from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
import uuid

from pydantic import BaseModel, Field

class OpportunityUnified(BaseModel):
    """
    Esquema unificado para oportunidades de arbitraje.
    Utiliza Decimal para asegurar la precisión en valores monetarios y porcentajes.
    """
    opportunity_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID único de la oportunidad")
    symbol: str = Field(..., description="Símbolo del par de trading principal de la oportunidad (ej. BTCUSDT)")
    base_asset: str = Field(..., description="Activo base de la oportunidad (ej. BTC)")
    quote_asset: str = Field(..., description="Activo de cotización de la oportunidad (ej. USDT)")
    profit_percentage: Decimal = Field(..., description="Porcentaje de ganancia esperado de la oportunidad")
    expected_profit_usd: Decimal = Field(..., description="Ganancia esperada en USD de la oportunidad")
    path: List[str] = Field(..., description="Lista de pares de trading que forman la ruta de arbitraje (ej. ['BTC/USDT', 'ETH/BTC', 'ETH/USDT'])")
    timestamp: datetime = Field(..., description="Marca de tiempo de detección de la oportunidad")
    expiration_time: Optional[datetime] = Field(None, description="Tiempo de expiración de la oportunidad, si aplica")
    status: str = Field("detected", description="Estado actual de la oportunidad (ej. 'detected', 'executed', 'failed')")
    source: str = Field(..., description="Fuente de la oportunidad (ej. 'Binance', 'Mobula', 'Combined')")
    details: Dict[str, Any] = Field({}, description="Diccionario para detalles adicionales específicos de la oportunidad")

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }
        arbitrary_types_allowed = True
