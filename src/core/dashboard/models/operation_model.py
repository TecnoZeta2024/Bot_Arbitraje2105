"""
Modelos de datos para las operaciones de arbitraje.
Implementa patrones basados en SOLID para mantener la responsabilidad única y extensibilidad.
"""

import json
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class OperationStatus(str, Enum):
    """Enum para estados de operación"""
    PENDIENTE = "PENDIENTE"
    EJECUTANDO = "EJECUTANDO"
    COMPLETADO = "COMPLETADO"
    FALLIDO = "FALLIDO"
    CANCELADO = "CANCELADO"

class ArbitrageRoute(BaseModel):
    """Modelo para una ruta de arbitraje"""
    route: str = Field(..., description="Representación textual de la ruta (ej: USDT->BTC->ETH->USDT)")
    pairs: List[Dict[str, Any]] = Field(default_factory=list, description="Pares de trading en la ruta")
    
class ArbitrageAnalysis(BaseModel):
    """Modelo para el análisis de una oportunidad de arbitraje por IA"""
    recommendation: str = Field(..., description="Recomendación (PROCEDER, PRECAUCION, DESCARTAR)")
    confidence: float = Field(..., description="Nivel de confianza (0-100)")
    estimated_roi: float = Field(..., description="Rentabilidad neta estimada (%)")
    identified_risks: List[str] = Field(default_factory=list, description="Riesgos identificados")
    explanation: str = Field(..., description="Explicación del análisis")
    
class ArbitrageOperation(BaseModel):
    """Modelo para una operación de arbitraje completa"""
    id: Optional[int] = Field(default=None, description="ID de la operación en la base de datos")
    operation_id: str = Field(..., description="ID único de la operación")
    opportunity_id: Optional[int] = Field(default=None, description="ID de la oportunidad detectada")
    route: ArbitrageRoute = Field(..., description="Ruta de arbitraje")
    initial_capital: float = Field(..., description="Capital inicial utilizado (USDT)")
    ai_analysis: Optional[ArbitrageAnalysis] = Field(default=None, description="Análisis de IA")
    user_decision: Optional[str] = Field(default=None, description="Decisión del usuario (Si/No)")
    decision_time: Optional[datetime] = Field(default=None, description="Timestamp de decisión del usuario")
    status: str = Field(default="PENDIENTE", description="Estado de la operación")
    executed_pairs: Optional[List[Dict[str, Any]]] = Field(default=None, description="Detalles de pares ejecutados")
    real_prices: Optional[Dict[str, float]] = Field(default=None, description="Precios reales de ejecución")
    gross_result: Optional[float] = Field(default=None, description="Resultado bruto (USDT)")
    total_fees: Optional[float] = Field(default=None, description="Comisiones totales (USDT)")
    real_slippage: Optional[float] = Field(default=None, description="Slippage real experimentado (%)")
    net_profit: Optional[float] = Field(default=None, description="Ganancia o pérdida neta (USDT)")
    real_roi: Optional[float] = Field(default=None, description="Rentabilidad neta real (%)")
    execution_start_time: Optional[datetime] = Field(default=None, description="Timestamp de inicio de ejecución")
    completion_time: Optional[datetime] = Field(default=None, description="Timestamp de finalización")
    execution_log: Optional[str] = Field(default=None, description="Log detallado de la ejecución")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArbitrageOperation':
        """
        Crea una instancia de ArbitrageOperation a partir de un diccionario
        
        Args:
            data: Diccionario con datos de la operación
            
        Returns:
            Instancia de ArbitrageOperation
        """
        # Procesar ruta
        route_data = data.get("ruta_arbitraje", "")
        pairs_data = data.get("pares_ejecutados")
        
        if isinstance(pairs_data, str):
            try:
                pairs = json.loads(pairs_data)
            except:
                pairs = []
        elif isinstance(pairs_data, list):
            pairs = pairs_data
        else:
            pairs = []
            
        route = ArbitrageRoute(
            route=route_data,
            pairs=pairs
        )
        
        # Procesar análisis de IA
        ai_analysis_data = data.get("analisis_ia")
        ai_analysis = None
        
        if ai_analysis_data:
            if isinstance(ai_analysis_data, str):
                try:
                    ai_analysis_dict = json.loads(ai_analysis_data)
                except:
                    ai_analysis_dict = {}
            elif isinstance(ai_analysis_data, dict):
                ai_analysis_dict = ai_analysis_data
            else:
                ai_analysis_dict = {}
                
            if ai_analysis_dict:
                ai_analysis = ArbitrageAnalysis(
                    recommendation=ai_analysis_dict.get("recomendacion", ""),
                    confidence=ai_analysis_dict.get("confianza", 0),
                    estimated_roi=ai_analysis_dict.get("rentabilidad_neta_estimada", 0),
                    identified_risks=ai_analysis_dict.get("riesgos_identificados", []),
                    explanation=ai_analysis_dict.get("explicacion", "")
                )
        
        # Procesar precios reales
        real_prices_data = data.get("precios_reales")
        real_prices = None
        
        if real_prices_data:
            if isinstance(real_prices_data, str):
                try:
                    real_prices = json.loads(real_prices_data)
                except:
                    real_prices = {}
            elif isinstance(real_prices_data, dict):
                real_prices = real_prices_data
        
        # Crear instancia
        return cls(
            id=data.get("id"),
            operation_id=data.get("operacion_id", ""),
            opportunity_id=data.get("oportunidad_detectada_id"),
            route=route,
            initial_capital=data.get("capital_inicial", 0),
            ai_analysis=ai_analysis,
            user_decision=data.get("decision_usuario"),
            decision_time=data.get("fecha_decision"),
            status=data.get("estado", "PENDIENTE"),
            executed_pairs=pairs if pairs else None,
            real_prices=real_prices,
            gross_result=data.get("resultado_bruto"),
            total_fees=data.get("comisiones_totales"),
            real_slippage=data.get("slippage_real"),
            net_profit=data.get("ganancia_neta"),
            real_roi=data.get("rentabilidad_real"),
            execution_start_time=data.get("fecha_inicio_ejecucion"),
            completion_time=data.get("fecha_completado"),
            execution_log=data.get("log_ejecucion")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la operación a un diccionario para almacenamiento en la base de datos
        
        Returns:
            Dict[str, Any]: Diccionario con datos de la operación
        """
        result = {
            "operacion_id": self.operation_id,
            "oportunidad_detectada_id": self.opportunity_id,
            "ruta_arbitraje": self.route.route,
            "capital_inicial": self.initial_capital,
            "decision_usuario": self.user_decision,
            "fecha_decision": self.decision_time.isoformat() if self.decision_time else None,
            "estado": self.status
        }
        
        # Agregar datos de análisis de IA si está disponible
        if self.ai_analysis:
            result["analisis_ia"] = json.dumps({
                "recomendacion": self.ai_analysis.recommendation,
                "confianza": self.ai_analysis.confidence,
                "rentabilidad_neta_estimada": self.ai_analysis.estimated_roi,
                "riesgos_identificados": self.ai_analysis.identified_risks,
                "explicacion": self.ai_analysis.explanation
            })
        
        # Agregar datos de ejecución si están disponibles
        if self.executed_pairs:
            result["pares_ejecutados"] = json.dumps(self.executed_pairs)
            
        if self.real_prices:
            result["precios_reales"] = json.dumps(self.real_prices)
            
        if self.gross_result is not None:
            result["resultado_bruto"] = self.gross_result
            
        if self.total_fees is not None:
            result["comisiones_totales"] = self.total_fees
            
        if self.real_slippage is not None:
            result["slippage_real"] = self.real_slippage
            
        if self.net_profit is not None:
            result["ganancia_neta"] = self.net_profit
            
        if self.real_roi is not None:
            result["rentabilidad_real"] = self.real_roi
            
        if self.execution_start_time:
            result["fecha_inicio_ejecucion"] = self.execution_start_time.isoformat()
            
        if self.completion_time:
            result["fecha_completado"] = self.completion_time.isoformat()
            
        if self.execution_log:
            result["log_ejecucion"] = self.execution_log
            
        if self.id:
            result["id"] = self.id
            
        return result
