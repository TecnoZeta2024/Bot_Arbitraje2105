"""
Modelos de datos para los tokens criptográficos.
Implementa patrones basados en SOLID para mantener la responsabilidad única y extensibilidad.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Modelo para token criptográfico"""
    id: Optional[int] = Field(default=None, description="ID del token en la base de datos")
    symbol: str = Field(..., description="Símbolo del token (e.j., BTC, ETH)")
    name: Optional[str] = Field(default=None, description="Nombre del token")
    market_cap: Optional[float] = Field(default=None, description="Capitalización de mercado")
    binance_volume_24h: Optional[float] = Field(default=None, description="Volumen en Binance en 24 horas")
    change_24h: Optional[float] = Field(default=None, description="Cambio porcentual en 24 horas")
    change_7d: Optional[float] = Field(default=None, description="Cambio porcentual en 7 días")
    change_1h: Optional[float] = Field(default=None, description="Cambio porcentual en 1 hora")
    updated_at: Optional[datetime] = Field(default=None, description="Fecha y hora de última actualización")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Token':
        """
        Crea una instancia de Token a partir de un diccionario
        
        Args:
            data: Diccionario con datos del token
            
        Returns:
            Instancia de Token
        """
        return cls(
            id=data.get("id"),
            symbol=data.get("simbolo"),
            name=data.get("nombre"),
            market_cap=data.get("market_cap"),
            binance_volume_24h=data.get("volumen_binance_24h"),
            change_24h=data.get("rendimiento_24h"),
            change_7d=data.get("rendimiento_7d"),
            change_1h=data.get("rendimiento_1h"),
            updated_at=data.get("fecha_actualizacion")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el token a un diccionario para almacenamiento en la base de datos
        
        Returns:
            Dict[str, Any]: Diccionario con datos del token
        """
        result = {
            "simbolo": self.symbol,
            "nombre": self.name,
            "market_cap": self.market_cap,
            "volumen_binance_24h": self.binance_volume_24h,
            "rendimiento_24h": self.change_24h,
            "rendimiento_7d": self.change_7d,
            "rendimiento_1h": self.change_1h,
            "fecha_actualizacion": datetime.now().isoformat() if not self.updated_at else self.updated_at
        }
        
        if self.id is not None:
            result["id"] = self.id
            
        return result
