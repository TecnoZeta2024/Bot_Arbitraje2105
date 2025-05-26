from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol, List
from decimal import Decimal

from src.infrastructure.external_apis.binance_client import BinanceClient
from src.infrastructure.external_apis.mobula_client import MobulaAPIClient
from src.data.binance_transformer import BinanceTransformer
from src.data.mobula_transformer import MobulaTransformer
from src.domain.data_models import MarketDataUnified

@dataclass
class Ticker:
    symbol: str
    bid: float
    ask: float
    last: float
    timestamp: int

@dataclass
class Order:
    symbol: str
    type: str
    side: str
    amount: float
    price: Optional[float] = None

@dataclass
class OrderResult:
    order_id: str
    symbol: str
    status: str
    amount: float
    price: Optional[float]
    timestamp: int

class IExchangeAdapter(Protocol):
    """
    Interfaz unificada para interactuar con diferentes exchanges de criptomonedas.
    """
    async def get_ticker(self, symbol: str) -> MarketDataUnified:
        """
        Obtiene la información del ticker para un símbolo dado, ya transformada.
        """
        ...

    async def place_order(self, order: Order) -> OrderResult:
        """
        Coloca una orden en el exchange.
        """
        ...

    async def get_balance(self, asset: str) -> float:
        """
        Obtiene el balance de un activo específico.
        """
        ...

class BinanceAdapter(IExchangeAdapter):
    """
    Adaptador para interactuar con la API de Binance, integrando transformadores.
    """
    def __init__(self, trading: bool = False):
        self.binance_client = BinanceClient(trading=trading)
        self.transformer = BinanceTransformer()
        print(f"BinanceAdapter inicializado (trading: {trading}).")

    async def get_ticker(self, symbol: str) -> MarketDataUnified:
        """
        Obtiene la información del ticker para un símbolo dado de Binance
        y la transforma a MarketDataUnified.
        """
        ticker_data = self.binance_client.get_ticker(symbol)
        if ticker_data:
            return self.transformer.transform_ticker_24hr(ticker_data)
        raise ValueError(f"No se pudieron obtener datos del ticker para {symbol} desde Binance.")

    async def place_order(self, order: Order) -> OrderResult:
        # Implementación real para colocar una orden en Binance
        # Asumiendo que el cliente de Binance tiene un método para esto
        result = self.binance_client.crear_orden_mercado(order.symbol, order.side, order.amount)
        if result:
            order_id = str(result.get("orderId", ""))
            symbol = result.get("symbol", "")
            status = result.get("status", "UNKNOWN")
            amount = float(result.get("executedQty", 0.0))
            price = float(result.get("price", order.price or 0.0))
            timestamp = int(result.get("transactTime", 0))
            return OrderResult(order_id=order_id, symbol=symbol,
                               status=status, amount=amount, price=price,
                               timestamp=timestamp)
        raise ValueError("No se pudo crear la orden de mercado en Binance.")

    async def get_balance(self, asset: str) -> float:
        # Implementación real para obtener el balance de Binance
        balance = self.binance_client.obtener_saldo(asset)
        return balance if balance is not None else 0.0

class MobulaAdapter(IExchangeAdapter):
    """
    Adaptador para interactuar con la API de Mobula, integrando transformadores.
    """
    def __init__(self):
        self.mobula_client = MobulaAPIClient()
        self.transformer = MobulaTransformer()
        print("MobulaAdapter inicializado.")

    async def get_raw_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la información del ticker para un símbolo dado de Mobula en formato bruto.
        """
        market_data_raw = await self.mobula_client.get_market_data(assets=[symbol])
        if market_data_raw and symbol.upper() in market_data_raw:
            return market_data_raw[symbol.upper()]
        return None

    async def get_ticker(self, symbol: str) -> MarketDataUnified:
        """
        Obtiene la información de mercado para un símbolo dado de Mobula
        y la transforma a MarketDataUnified.
        """
        raw_data = await self.get_raw_ticker(symbol)
        if raw_data:
            return self.transformer.transform_market_data(raw_data)
        raise ValueError(f"No se pudieron obtener datos del ticker para {symbol} desde Mobula.")

    async def place_order(self, order: Order) -> OrderResult:
        # Mobula no es un exchange de trading, por lo que este método no aplica.
        # Podríamos levantar una excepción o devolver un resultado de error.
        raise NotImplementedError("Mobula API no soporta la colocación de órdenes.")

    async def get_balance(self, asset: str) -> float:
        # Mobula no es un exchange de trading, por lo que este método no aplica.
        raise NotImplementedError("Mobula API no soporta la obtención de balances.")

# No instanciar adaptadores globales aquí, deben ser instanciados donde se necesiten
# para permitir la inyección de dependencias y configuración flexible.
