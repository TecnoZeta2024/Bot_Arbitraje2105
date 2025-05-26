from datetime import datetime
from decimal import Decimal, getcontext
from typing import Any, Dict, List, Optional

from src.domain.data_models import MarketDataUnified

# Configurar el contexto decimal global para asegurar la precisión
# Se elige una precisión de 18 decimales, común en finanzas para evitar errores de coma flotante.
getcontext().prec = 28

class BinanceTransformer:
    """
    Transformador para convertir datos crudos de Binance al esquema MarketDataUnified.
    Asegura la precisión Decimal en todas las operaciones numéricas.
    """

    @staticmethod
    def transform_ticker_24hr(data: Dict[str, Any]) -> MarketDataUnified:
        """
        Transforma los datos del endpoint /api/v3/ticker/24hr de Binance
        al esquema MarketDataUnified, aplicando precisión Decimal.
        """
        try:
            close_time_str = data.get('closeTime')
            timestamp = datetime.fromtimestamp(int(close_time_str) / 1000) if close_time_str else datetime.now()

            def to_decimal(value: Any) -> Decimal:
                # Convertir a Decimal y aplicar el contexto de precisión.
                # Si el valor es None o una cadena vacía, retorna Decimal('0').
                return Decimal(str(value)) if value is not None and str(value).strip() != '' else Decimal('0')

            def to_int(value: Any) -> Optional[int]:
                return int(value) if value is not None and str(value).strip() != '' else None

            return MarketDataUnified(
                symbol=data.get('symbol', ''),
                timestamp=timestamp,
                price=to_decimal(data.get('lastPrice')),
                volume=to_decimal(data.get('volume')),
                quote_volume=to_decimal(data.get('quoteVolume')),
                high_price=to_decimal(data.get('highPrice')),
                low_price=to_decimal(data.get('lowPrice')),
                open_price=to_decimal(data.get('openPrice')),
                close_price=to_decimal(data.get('lastPrice')), # lastPrice es el precio de cierre
                bid_price=to_decimal(data.get('bidPrice')),
                bid_qty=to_decimal(data.get('bidQty')),
                ask_price=to_decimal(data.get('askPrice')),
                ask_qty=to_decimal(data.get('askQty')),
                source="Binance",
                price_change_24h=to_decimal(data.get('priceChange')),
                price_change_percentage_24h=to_decimal(data.get('priceChangePercent')),
                market_cap=None, # No disponible en Binance ticker 24hr
                rank=None,       # No disponible en Binance ticker 24hr
                number_of_trades=to_int(data.get('count'))
            )
        except Exception as e:
            raise ValueError(f"Error al transformar datos de Binance ticker 24hr: {e} - Datos: {data}")

    @staticmethod
    def transform_depth(symbol: str, data: Dict[str, Any]) -> Dict[str, Decimal]:
        """
        Transforma los datos de profundidad de mercado (order book) de Binance,
        asegurando la precisión Decimal.
        Retorna los mejores bid/ask y sus cantidades.
        """
        bids = data.get('bids', [])
        asks = data.get('asks', [])

        # Asegurar que los valores se conviertan a Decimal con el contexto de precisión
        best_bid_price = Decimal(str(bids[0][0])) if bids else Decimal('0')
        best_bid_qty = Decimal(str(bids[0][1])) if bids else Decimal('0')
        best_ask_price = Decimal(str(asks[0][0])) if asks else Decimal('0')
        best_ask_qty = Decimal(str(asks[0][1])) if asks else Decimal('0')

        return {
            "bid_price": best_bid_price,
            "bid_qty": best_bid_qty,
            "ask_price": best_ask_price,
            "ask_qty": best_ask_qty,
        }

    @staticmethod
    def combine_market_data(ticker_data: Dict[str, Any], depth_data: Dict[str, Decimal]) -> MarketDataUnified:
        """
        Combina datos de ticker 24hr y profundidad de mercado para crear un MarketDataUnified.
        """
        transformed_ticker = BinanceTransformer.transform_ticker_24hr(ticker_data)
        
        # Actualizar los campos de bid/ask con los datos de profundidad si son más precisos o están disponibles
        # Los datos de ticker 24hr pueden no tener los mejores bid/ask actualizados
        # Asegurar que las actualizaciones también respeten la precisión Decimal
        transformed_ticker.bid_price = depth_data.get("bid_price", transformed_ticker.bid_price)
        transformed_ticker.bid_qty = depth_data.get("bid_qty", transformed_ticker.bid_qty)
        transformed_ticker.ask_price = depth_data.get("ask_price", transformed_ticker.ask_price)
        transformed_ticker.ask_qty = depth_data.get("ask_qty", transformed_ticker.ask_qty)
        
        return transformed_ticker

    @staticmethod
    def transform_simple_ticker(symbol: str, price: Any) -> Optional[MarketDataUnified]:
        """
        Transforma un símbolo y precio simple al esquema MarketDataUnified,
        asegurando la precisión Decimal.
        Útil cuando solo se dispone de precio y símbolo, rellenando otros campos con valores por defecto.
        """
        try:
            # Asegurar que el precio sea un Decimal y mayor que 0, aplicando el contexto de precisión
            decimal_price = Decimal(str(price))
            if decimal_price <= 0:
                return None # No transformar si el precio no es válido

            return MarketDataUnified(
                symbol=symbol,
                price=decimal_price,
                timestamp=datetime.now(),
                source="Binance",
                # Rellenar otros campos con valores por defecto o None si no están disponibles
                volume=Decimal('0'),
                quote_volume=Decimal('0'),
                high_price=Decimal('0'),
                low_price=Decimal('0'),
                open_price=Decimal('0'),
                close_price=decimal_price,
                bid_price=decimal_price, # Usar el precio como bid/ask si no hay más info
                bid_qty=Decimal('0'),
                ask_price=decimal_price,
                ask_qty=Decimal('0'),
                price_change_24h=None,
                price_change_percentage_24h=None,
                market_cap=None,
                rank=None,
                number_of_trades=None
            )
        except Exception as e:
            # Log the error but don't re-raise, allowing other tickers to be processed
            print(f"Error al transformar ticker simple de Binance ({symbol}, {price}): {e}")
            return None
