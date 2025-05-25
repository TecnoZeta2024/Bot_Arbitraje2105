import logging
from datetime import datetime
from decimal import Decimal, getcontext

# Configurar la precisión decimal para evitar errores de punto flotante
getcontext().prec = 10

class VirtualPortfolio:
    def __init__(self, initial_balance_usd=Decimal('10000.00')):
        self.balances = {'USD': initial_balance_usd}
        self.positions = {}  # {symbol: {amount: Decimal, avg_price: Decimal}}
        self.trade_history = []
        self.pnl_history = []
        logging.info(f"Cartera virtual inicializada con USD: {self.balances['USD']}")

    def update_balance(self, currency, amount):
        self.balances[currency] = self.balances.get(currency, Decimal('0.00')) + amount
        logging.debug(f"Balance actualizado: {currency} {amount}. Nuevo balance: {self.balances[currency]}")

    def add_position(self, symbol, amount, price):
        if symbol not in self.positions:
            self.positions[symbol] = {'amount': Decimal('0.00'), 'avg_price': Decimal('0.00')}
        
        current_total = self.positions[symbol]['amount'] * self.positions[symbol]['avg_price']
        new_total = amount * price
        total_amount = self.positions[symbol]['amount'] + amount
        
        if total_amount == Decimal('0.00'):
            self.positions[symbol]['avg_price'] = Decimal('0.00')
        else:
            self.positions[symbol]['avg_price'] = (current_total + new_total) / total_amount
        
        self.positions[symbol]['amount'] = total_amount
        logging.debug(f"Posición añadida: {symbol} {amount} a {price}. Nueva posición: {self.positions[symbol]}")

    def record_trade(self, trade_type, symbol, amount, price, fee, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()
        trade = {
            'timestamp': timestamp,
            'type': trade_type,
            'symbol': symbol,
            'amount': amount,
            'price': price,
            'fee': fee,
            'balance_usd_after': self.balances.get('USD', Decimal('0.00'))
        }
        self.trade_history.append(trade)
        logging.info(f"Trade registrado: {trade_type} {symbol} {amount} a {price}")

    def calculate_current_pnl(self, current_prices):
        total_pnl = Decimal('0.00')
        for symbol, position in self.positions.items():
            if position['amount'] > Decimal('0.00') and symbol in current_prices:
                current_value = position['amount'] * current_prices[symbol]
                cost_basis = position['amount'] * position['avg_price']
                pnl = current_value - cost_basis
                total_pnl += pnl
        return total_pnl

    def record_pnl(self, current_prices, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()
        current_pnl = self.calculate_current_pnl(current_prices)
        self.pnl_history.append({'timestamp': timestamp, 'pnl': current_pnl})
        logging.debug(f"PNL registrado: {current_pnl}")

class PaperTradingSystem:
    def __init__(self, market_data_provider):
        self.virtual_portfolio = VirtualPortfolio()
        self.market_data = market_data_provider
        self.logger = logging.getLogger("PaperTradingSystem")
        self.logger.setLevel(logging.INFO)

    async def execute_paper_order(self, order):
        """
        Simula la ejecución de una orden y actualiza la cartera virtual.
        order: {
            'symbol': 'BTC/USD',
            'type': 'LIMIT' or 'MARKET',
            'side': 'BUY' or 'SELL',
            'amount': Decimal,
            'price': Decimal (for LIMIT orders)
        }
        """
        symbol = order['symbol']
        order_type = order['type']
        side = order['side']
        amount = Decimal(str(order['amount'])) # Asegurar Decimal
        
        current_price = await self.market_data.get_current_price(symbol)
        if not current_price:
            self.logger.warning(f"No se pudo obtener el precio actual para {symbol}. Orden no ejecutada.")
            return False

        current_price = Decimal(str(current_price)) # Asegurar Decimal

        execution_price = current_price
        if order_type == 'LIMIT' and 'price' in order:
            limit_price = Decimal(str(order['price'])) # Asegurar Decimal
            if (side == 'BUY' and limit_price < current_price) or \
               (side == 'SELL' and limit_price > current_price):
                execution_price = limit_price
            else:
                self.logger.info(f"Orden límite {side} {symbol} a {limit_price} no ejecutada al precio actual {current_price}.")
                return False

        # Simular comisiones (ej. 0.1%)
        fee_rate = Decimal('0.001')
        
        if side == 'BUY':
            cost = amount * execution_price
            fee = cost * fee_rate
            total_cost = cost + fee
            
            if self.virtual_portfolio.balances.get('USD', Decimal('0.00')) >= total_cost:
                self.virtual_portfolio.update_balance('USD', -total_cost)
                self.virtual_portfolio.add_position(symbol, amount, execution_price)
                self.virtual_portfolio.record_trade('BUY', symbol, amount, execution_price, fee)
                self.logger.info(f"Orden de compra simulada ejecutada: {symbol} {amount} a {execution_price}")
                return True
            else:
                self.logger.warning(f"Fondos insuficientes para comprar {amount} de {symbol}. Necesario: {total_cost}, Disponible: {self.virtual_portfolio.balances.get('USD', Decimal('0.00'))}")
                return False
        
        elif side == 'SELL':
            if self.virtual_portfolio.positions.get(symbol, {'amount': Decimal('0.00')})['amount'] >= amount:
                revenue = amount * execution_price
                fee = revenue * fee_rate
                net_revenue = revenue - fee
                
                self.virtual_portfolio.update_balance('USD', net_revenue)
                self.virtual_portfolio.add_position(symbol, -amount, execution_price) # Restar de la posición
                self.virtual_portfolio.record_trade('SELL', symbol, amount, execution_price, fee)
                self.logger.info(f"Orden de venta simulada ejecutada: {symbol} {amount} a {execution_price}")
                return True
            else:
                self.logger.warning(f"Posición insuficiente para vender {amount} de {symbol}. Disponible: {self.virtual_portfolio.positions.get(symbol, {'amount': Decimal('0.00')})['amount']}")
                return False
        return False

    def get_performance(self, current_prices):
        """
        Retorna métricas de rendimiento para la cartera virtual.
        """
        current_pnl = self.virtual_portfolio.calculate_current_pnl(current_prices)
        total_balance_usd = self.virtual_portfolio.balances.get('USD', Decimal('0.00'))
        
        # Calcular el valor total de las posiciones abiertas en USD
        open_positions_value_usd = Decimal('0.00')
        for symbol, position in self.virtual_portfolio.positions.items():
            if position['amount'] > Decimal('0.00') and symbol in current_prices:
                open_positions_value_usd += position['amount'] * current_prices[symbol]
        
        total_equity = total_balance_usd + open_positions_value_usd
        
        return {
            'current_pnl': current_pnl,
            'total_balance_usd': total_balance_usd,
            'total_equity_usd': total_equity,
            'trade_history': self.virtual_portfolio.trade_history,
            'pnl_history': self.virtual_portfolio.pnl_history,
            'positions': self.virtual_portfolio.positions
        }

    async def update_pnl_history(self):
        """
        Actualiza el historial de PNL con los precios actuales del mercado.
        """
        current_prices = {}
        for symbol in self.virtual_portfolio.positions.keys():
            price = await self.market_data.get_current_price(symbol)
            if price:
                current_prices[symbol] = Decimal(str(price))
        
        if current_prices:
            self.virtual_portfolio.record_pnl(current_prices)

# Ejemplo de uso (requiere un market_data_provider real o mock)
# class MockMarketDataProvider:
#     async def get_current_price(self, symbol):
#         if symbol == 'BTC/USD':
#             return Decimal('30000.00')
#         elif symbol == 'ETH/USD':
#             return Decimal('2000.00')
#         return None

# async def main():
#     logging.basicConfig(level=logging.INFO)
#     mock_market_data = MockMarketDataProvider()
#     paper_trading = PaperTradingSystem(mock_market_data)

#     # Simular una compra
#     order_buy = {
#         'symbol': 'BTC/USD',
#         'type': 'MARKET',
#         'side': 'BUY',
#         'amount': Decimal('0.01')
#     }
#     await paper_trading.execute_paper_order(order_buy)

#     # Simular una venta
#     order_sell = {
#         'symbol': 'BTC/USD',
#         'type': 'MARKET',
#         'side': 'SELL',
#         'amount': Decimal('0.005')
#     }
#     await paper_trading.execute_paper_order(order_sell)

#     # Obtener y mostrar rendimiento
#     current_prices = {'BTC/USD': Decimal('30500.00'), 'ETH/USD': Decimal('2050.00')}
#     performance = paper_trading.get_performance(current_prices)
#     print("\n--- Rendimiento de Paper Trading ---")
#     print(f"Balance USD: {performance['total_balance_usd']}")
#     print(f"Equidad Total USD: {performance['total_equity_usd']}")
#     print(f"PNL Actual: {performance['current_pnl']}")
#     print("Posiciones:", performance['positions'])
#     print("Historial de Trades:", performance['trade_history'])
#     print("Historial de PNL:", performance['pnl_history'])

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())
