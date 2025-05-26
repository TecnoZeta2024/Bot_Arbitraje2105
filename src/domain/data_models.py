from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MarketDataUnified(BaseModel):
    """
    Esquema unificado para datos de mercado de diferentes fuentes (Binance, Mobula).
    Utiliza Decimal para asegurar la precisión en valores monetarios y de cantidad.
    """
    symbol: str = Field(..., description="Símbolo del par de trading (ej. BTCUSDT)")
    timestamp: datetime = Field(..., description="Marca de tiempo del dato de mercado")
    price: Decimal = Field(..., description="Precio actual del activo")
    volume: Decimal = Field(..., description="Volumen de trading en las últimas 24h en la moneda base")
    quote_volume: Decimal = Field(..., description="Volumen de trading en las últimas 24h en la moneda de cotización")
    high_price: Decimal = Field(..., description="Precio más alto en las últimas 24h")
    low_price: Decimal = Field(..., description="Precio más bajo en las últimas 24h")
    open_price: Decimal = Field(..., description="Precio de apertura en las últimas 24h")
    close_price: Decimal = Field(..., description="Precio de cierre en las últimas 24h")
    bid_price: Decimal = Field(..., description="Mejor precio de compra (bid)")
    bid_qty: Decimal = Field(..., description="Cantidad disponible al mejor precio de compra (bid)")
    ask_price: Decimal = Field(..., description="Mejor precio de venta (ask)")
    ask_qty: Decimal = Field(..., description="Cantidad disponible al mejor precio de venta (ask)")
    source: str = Field(..., description="Fuente del dato de mercado (ej. 'Binance', 'Mobula')")
    
    # Campos opcionales que pueden no estar presentes en todas las fuentes
    price_change_24h: Optional[Decimal] = Field(None, description="Cambio de precio en las últimas 24h")
    price_change_percentage_24h: Optional[Decimal] = Field(None, description="Cambio porcentual de precio en las últimas 24h")
    market_cap: Optional[Decimal] = Field(None, description="Capitalización de mercado del activo")
    rank: Optional[int] = Field(None, description="Ranking del activo por capitalización de mercado")
    number_of_trades: Optional[int] = Field(None, description="Número de operaciones en las últimas 24h")

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }
        arbitrary_types_allowed = True

class OpportunityStep(BaseModel):
    """
    Esquema para un paso individual dentro de una oportunidad de arbitraje.
    """
    order: int = Field(..., description="Orden del paso en el ciclo de arbitraje")
    from_coin: str = Field(..., description="Moneda de origen para este paso")
    to_coin: str = Field(..., description="Moneda de destino para este paso")
    pair: str = Field(..., description="Par de trading utilizado en este paso (ej. BTCUSDT)")
    amount_in: Decimal = Field(..., gt=0, description="Cantidad de moneda de origen a operar en este paso")

class OpportunityUnified(BaseModel):
    """
    Esquema unificado para oportunidades de arbitraje triangular.
    """
    opportunity_id: str = Field(..., description="ID único de la oportunidad")
    cycle: str = Field(..., description="Ciclo de arbitraje (ej. BTC -> ETH -> USDT -> BTC)")
    profit_percentage_gross: Decimal = Field(..., description="Rentabilidad bruta estimada en porcentaje")
    profit_percentage_net: Decimal = Field(..., description="Rentabilidad neta estimada en porcentaje, después de comisiones")
    steps: List[OpportunityStep] = Field(..., description="Pasos detallados de la operación de arbitraje")
    capital_inicial: Decimal = Field(..., gt=0, description="Capital inicial sugerido para la operación")
    capital_sugerido: Decimal = Field(..., gt=0, description="Capital sugerido para la operación, ajustado por el sistema")
    timestamp_detected: datetime = Field(default_factory=datetime.now, description="Marca de tiempo de la detección de la oportunidad")
