from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


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
    async def get_ticker(self, symbol: str) -> Ticker:
        """
        Obtiene la información del ticker para un símbolo dado.
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
    Adaptador para interactuar con la API de Binance.
    """
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
        # Aquí se inicializaría el cliente de Binance real
        print("BinanceAdapter inicializado.")

    async def get_ticker(self, symbol: str) -> Ticker:
        # Implementación real para obtener el ticker de Binance
        print(f"Obteniendo ticker para {symbol} desde Binance.")
        return Ticker(symbol=symbol, bid=0.0, ask=0.0, last=0.0, timestamp=0)

    async def place_order(self, order: Order) -> OrderResult:
        # Implementación real para colocar una orden en Binance
        print(f"Colocando orden en Binance: {order}")
        return OrderResult(order_id="binance_order_123", symbol=order.symbol,
                           status="FILLED", amount=order.amount, price=order.price or 0.0,
                           timestamp=0)

    async def get_balance(self, asset: str) -> float:
        # Implementación real para obtener el balance de Binance
        print(f"Obteniendo balance de {asset} desde Binance.")
        return 0.0

class CoinbaseAdapter(IExchangeAdapter):
    """
    Adaptador para interactuar con la API de Coinbase.
    """
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
        # Aquí se inicializaría el cliente de Coinbase real
        print("CoinbaseAdapter inicializado.")

    async def get_ticker(self, symbol: str) -> Ticker:
        # Implementación real para obtener el ticker de Coinbase
        print(f"Obteniendo ticker para {symbol} desde Coinbase.")
        return Ticker(symbol=symbol, bid=0.0, ask=0.0, last=0.0, timestamp=0)

    async def place_order(self, order: Order) -> OrderResult:
        # Implementación real para colocar una orden en Coinbase
        print(f"Colocando orden en Coinbase: {order}")
        return OrderResult(order_id="coinbase_order_456", symbol=order.symbol,
                           status="FILLED", amount=order.amount, price=order.price or 0.0,
                           timestamp=0)

    async def get_balance(self, asset: str) -> float:
        # Implementación real para obtener el balance de Coinbase
        print(f"Obteniendo balance de {asset} desde Coinbase.")
        return 0.0
