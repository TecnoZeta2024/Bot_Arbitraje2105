import heapq
from collections import defaultdict


class OrderbookAggregator:
    def __init__(self):
        self.exchange_orderbooks = {}  # {exchange_id: {"bids": {price: quantity}, "asks": {price: quantity}}}
        self.aggregated_bids = []  # Max-heap for bids (price, quantity)
        self.aggregated_asks = []  # Min-heap for asks (price, quantity)

    def update_orderbook(self, exchange_id, orderbook_data):
        """
        Actualiza el orderbook de un exchange específico y reconstruye el orderbook agregado.
        orderbook_data: {"bids": [[price, quantity], ...], "asks": [[price, quantity], ...]}
        """
        self.exchange_orderbooks[exchange_id] = {
            "bids": {float(p): float(q) for p, q in orderbook_data.get("bids", [])},
            "asks": {float(p): float(q) for p, q in orderbook_data.get("asks", [])}
        }
        self._rebuild_aggregated_orderbook()

    def _rebuild_aggregated_orderbook(self):
        """
        Reconstruye el orderbook agregado a partir de todos los orderbooks de los exchanges.
        """
        self.aggregated_bids = []
        self.aggregated_asks = []

        all_bids = defaultdict(float)
        all_asks = defaultdict(float)

        for exchange_id, ob in self.exchange_orderbooks.items():
            for price, quantity in ob["bids"].items():
                all_bids[price] += quantity
            for price, quantity in ob["asks"].items():
                all_asks[price] += quantity

        for price, quantity in all_bids.items():
            heapq.heappush(self.aggregated_bids, (-price, quantity))  # Max-heap for bids

        for price, quantity in all_asks.items():
            heapq.heappush(self.aggregated_asks, (price, quantity))  # Min-heap for asks

    def get_best_prices(self):
        """
        Retorna el mejor bid y ask del orderbook agregado.
        """
        best_bid = None
        best_ask = None

        if self.aggregated_bids:
            best_bid = -self.aggregated_bids[0][0]  # Top of max-heap
        if self.aggregated_asks:
            best_ask = self.aggregated_asks[0][0]  # Top of min-heap

        return {"best_bid": best_bid, "best_ask": best_ask}

    def get_liquidity_at_level(self, price, side, depth=1):
        """
        Estima la liquidez total en un nivel de precio dado o hasta una cierta profundidad.
        side: "bids" o "asks"
        depth: número de niveles de precio a considerar
        """
        total_liquidity = 0.0
        if side == "bids":
            current_heap = sorted(self.aggregated_bids, key=lambda x: -x[0]) # Sort by price descending
            for i in range(min(depth, len(current_heap))):
                p, q = -current_heap[i][0], current_heap[i][1]
                if p >= price:
                    total_liquidity += q
        elif side == "asks":
            current_heap = sorted(self.aggregated_asks, key=lambda x: x[0]) # Sort by price ascending
            for i in range(min(depth, len(current_heap))):
                p, q = current_heap[i][0], current_heap[i][1]
                if p <= price:
                    total_liquidity += q
        return total_liquidity

    def detect_arbitrage(self):
        """
        Detecta oportunidades de arbitraje cross-exchange.
        Retorna una lista de oportunidades: [{"buy_exchange": "...", "sell_exchange": "...", "profit": "..."}]
        """
        opportunities = []
        best_prices = self.get_best_prices()
        best_bid_global = best_prices["best_bid"]
        best_ask_global = best_prices["best_ask"]

        if best_bid_global is None or best_ask_global is None:
            return opportunities

        # Simple cross-exchange arbitrage: buy low on one exchange, sell high on another
        for buy_exchange_id, buy_ob in self.exchange_orderbooks.items():
            for sell_exchange_id, sell_ob in self.exchange_orderbooks.items():
                if buy_exchange_id == sell_exchange_id:
                    continue

                # Find best ask on buy_exchange
                buy_asks = sorted(buy_ob["asks"].items())
                if not buy_asks:
                    continue
                best_buy_ask_price = buy_asks[0][0]

                # Find best bid on sell_exchange
                sell_bids = sorted(sell_ob["bids"].items(), reverse=True)
                if not sell_bids:
                    continue
                best_sell_bid_price = sell_bids[0][0]

                if best_sell_bid_price > best_buy_ask_price:
                    profit = best_sell_bid_price - best_buy_ask_price
                    opportunities.append({
                        "buy_exchange": buy_exchange_id,
                        "sell_exchange": sell_exchange_id,
                        "buy_price": best_buy_ask_price,
                        "sell_price": best_sell_bid_price,
                        "profit": profit
                    })
        
        # Sort opportunities by profit in descending order
        opportunities.sort(key=lambda x: x["profit"], reverse=True)
        return opportunities
