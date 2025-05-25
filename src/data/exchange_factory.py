from typing import Optional
from src.data.exchange_adapters import IExchangeAdapter, BinanceAdapter, CoinbaseAdapter, Order, OrderResult, Ticker

class ExchangeFactory:
    """
    Factory para crear instancias de adaptadores de exchanges.
    """
    def __init__(self, api_keys: dict):
        self.api_keys = api_keys
        self.adapters = {}

    def get_adapter(self, exchange_name: str) -> Optional[IExchangeAdapter]:
        """
        Devuelve la instancia de adaptador correcta para el exchange dado.
        """
        if exchange_name not in self.adapters:
            if exchange_name == "binance":
                keys = self.api_keys.get("binance", {})
                self.adapters[exchange_name] = BinanceAdapter(keys.get("api_key"), keys.get("secret_key"))
            elif exchange_name == "coinbase":
                keys = self.api_keys.get("coinbase", {})
                self.adapters[exchange_name] = CoinbaseAdapter(keys.get("api_key"), keys.get("secret_key"))
            else:
                print(f"Exchange {exchange_name} no soportado.")
                return None
        return self.adapters[exchange_name]

class MultiExchangeManager:
    """
    Gestiona múltiples exchanges con lógica de failover.
    """
    def __init__(self, exchange_factory: ExchangeFactory, primary_exchange: str, secondary_exchange: str):
        self.exchange_factory = exchange_factory
        self.primary_adapter = self.exchange_factory.get_adapter(primary_exchange)
        self.secondary_adapter = self.exchange_factory.get_adapter(secondary_exchange)
        self.current_adapter = self.primary_adapter
        self.primary_exchange_name = primary_exchange
        self.secondary_exchange_name = secondary_exchange

        if not self.primary_adapter:
            raise ValueError(f"No se pudo inicializar el adaptador para el exchange primario: {primary_exchange}")
        if not self.secondary_adapter:
            print(f"Advertencia: No se pudo inicializar el adaptador para el exchange secundario: {secondary_exchange}. El failover no estará disponible.")

    async def _execute_with_failover(self, method_name: str, *args, **kwargs):
        """
        Intenta ejecutar un método en el adaptador actual, con failover si falla.
        """
        try:
            if self.current_adapter:
                method = getattr(self.current_adapter, method_name)
                return await method(*args, **kwargs)
            else:
                raise ConnectionError("No hay adaptador de exchange disponible.")
        except Exception as e:
            print(f"Error en {self.current_adapter.__class__.__name__}.{method_name}: {e}")
            if self.secondary_adapter and self.current_adapter == self.primary_adapter:
                print(f"Cambiando a exchange secundario: {self.secondary_exchange_name}")
                self.current_adapter = self.secondary_adapter
                try:
                    method = getattr(self.current_adapter, method_name)
                    return await method(*args, **kwargs)
                except Exception as e_secondary:
                    print(f"Error en {self.current_adapter.__class__.__name__}.{method_name} (secundario): {e_secondary}")
                    raise ConnectionError("Ambos exchanges fallaron.")
            else:
                raise

    async def get_ticker(self, symbol: str) -> Ticker:
        return await self._execute_with_failover("get_ticker", symbol)

    async def place_order(self, order: Order) -> OrderResult:
        return await self._execute_with_failover("place_order", order)

    async def get_balance(self, asset: str) -> float:
        return await self._execute_with_failover("get_balance", asset)
