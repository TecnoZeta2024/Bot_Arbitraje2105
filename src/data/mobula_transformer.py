from datetime import datetime
from decimal import Decimal, getcontext
from typing import Dict, Any, Optional, List

from src.domain.data_models import MarketDataUnified, OpportunityUnified

# Configurar el contexto decimal global para asegurar la precisión
# Se elige una precisión de 18 decimales, común en finanzas para evitar errores de coma flotante.
getcontext().prec = 28

class MobulaTransformer:
    """
    Transformador para convertir datos crudos de Mobula al esquema MarketDataUnified.
    Asegura la precisión Decimal en todas las operaciones numéricas.
    Mobula no proporciona un endpoint directo para oportunidades, estas se construyen
    a partir de la lógica de detección de arbitraje.
    """

    @staticmethod
    def to_decimal(value: Any) -> Decimal:
        """
        Helper para convertir a Decimal, manejando None o cadenas vacías.
        Siempre retorna un Decimal, usando Decimal('0') como valor por defecto.
        """
        return Decimal(str(value)) if value is not None and str(value).strip() != '' else Decimal('0')

    @staticmethod
    def to_int(value: Any) -> Optional[int]:
        """Helper para convertir a int, manejando None o cadenas vacías."""
        return int(value) if value is not None and str(value).strip() != '' else None

    @staticmethod
    def transform_market_data(data: Dict[str, Any]) -> MarketDataUnified:
        """
        Transforma los datos de mercado de Mobula (endpoint /api/1/market/multi-data)
        al esquema MarketDataUnified, aplicando precisión Decimal.
        """
        try:
            last_updated_timestamp = data.get('last_updated')
            timestamp = datetime.fromtimestamp(last_updated_timestamp / 1000) if last_updated_timestamp is not None else datetime.now()

            return MarketDataUnified(
                symbol=data.get('symbol', ''),
                timestamp=timestamp,
                price=MobulaTransformer.to_decimal(data.get('price')),
                volume=MobulaTransformer.to_decimal(data.get('volume')),
                quote_volume=Decimal('0'), # No disponible directamente en Mobula, usar 0
                high_price=Decimal('0'),   # No disponible directamente en Mobula, usar 0
                low_price=Decimal('0'),    # No disponible directamente en Mobula, usar 0
                open_price=Decimal('0'),   # No disponible directamente en Mobula, usar 0
                close_price=MobulaTransformer.to_decimal(data.get('price')), # Usar precio actual como cierre
                bid_price=Decimal('0'),    # No disponible directamente en Mobula, usar 0
                bid_qty=Decimal('0'),      # No disponible directamente en Mobula, usar 0
                ask_price=Decimal('0'),    # No disponible directamente en Mobula, usar 0
                ask_qty=Decimal('0'),      # No disponible directamente en Mobula, usar 0
                source="Mobula",
                price_change_24h=MobulaTransformer.to_decimal(data.get('price_change_24h')),
                price_change_percentage_24h=MobulaTransformer.to_decimal(data.get('price_change_percentage_24h')),
                market_cap=MobulaTransformer.to_decimal(data.get('market_cap')),
                rank=MobulaTransformer.to_int(data.get('rank')),
                number_of_trades=None # No disponible directamente en Mobula
            )
        except Exception as e:
            raise ValueError(f"Error al transformar datos de Mobula market data: {e} - Datos: {data}")
