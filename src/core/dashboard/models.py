"""
Modelos de datos para el dashboard.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class OperationStatus(Enum):
    """Estados posibles de una operación"""
    PENDIENTE = "PENDIENTE"
    EJECUTANDO = "EJECUTANDO"
    COMPLETADO = "COMPLETADO"
    FALLIDO = "FALLIDO"
    CANCELADO = "CANCELADO"

@dataclass
class ArbitrageRoute:
    """Modelo de ruta de arbitraje"""
    route: str
    pairs: List[str] = field(default_factory=list)
    tokens: List[str] = field(default_factory=list)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ArbitrageRoute":
        """
        Crea una instancia de ArbitrageRoute a partir de un diccionario
        
        Args:
            data: Diccionario con datos de ruta
            
        Returns:
            ArbitrageRoute: Instancia creada
        """
        return ArbitrageRoute(
            route=data.get("route", ""),
            pairs=data.get("pairs", []),
            tokens=data.get("tokens", [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la instancia a diccionario
        
        Returns:
            Dict[str, Any]: Diccionario con datos de ruta
        """
        return {
            "route": self.route,
            "pairs": self.pairs,
            "tokens": self.tokens
        }

@dataclass
class AIAnalysis:
    """Modelo de análisis de IA"""
    recommendation: str
    confidence: float
    estimated_roi: float
    identified_risks: List[str] = field(default_factory=list)
    explanation: str = ""
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AIAnalysis":
        """
        Crea una instancia de AIAnalysis a partir de un diccionario
        
        Args:
            data: Diccionario con datos de análisis
            
        Returns:
            AIAnalysis: Instancia creada
        """
        return AIAnalysis(
            recommendation=data.get("recomendacion", ""),
            confidence=data.get("confianza", 0.0),
            estimated_roi=data.get("rentabilidad_neta_estimada", 0.0),
            identified_risks=data.get("riesgos_identificados", []),
            explanation=data.get("explicacion", "")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la instancia a diccionario
        
        Returns:
            Dict[str, Any]: Diccionario con datos de análisis
        """
        return {
            "recomendacion": self.recommendation,
            "confianza": self.confidence,
            "rentabilidad_neta_estimada": self.estimated_roi,
            "riesgos_identificados": self.identified_risks,
            "explicacion": self.explanation
        }

@dataclass
class ExecutedPair:
    """Modelo de par ejecutado"""
    symbol: str
    order_type: str
    price: float
    quantity: float
    total_value: float
    commission: float
    timestamp: datetime
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ExecutedPair":
        """
        Crea una instancia de ExecutedPair a partir de un diccionario
        
        Args:
            data: Diccionario con datos de par ejecutado
            
        Returns:
            ExecutedPair: Instancia creada
        """
        # Convertir timestamp si es string
        timestamp = data.get("timestamp", None)
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif timestamp is None:
            timestamp = datetime.now()
        
        return ExecutedPair(
            symbol=data.get("symbol", ""),
            order_type=data.get("order_type", ""),
            price=data.get("price", 0.0),
            quantity=data.get("quantity", 0.0),
            total_value=data.get("total_value", 0.0),
            commission=data.get("commission", 0.0),
            timestamp=timestamp
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la instancia a diccionario
        
        Returns:
            Dict[str, Any]: Diccionario con datos de par ejecutado
        """
        return {
            "symbol": self.symbol,
            "order_type": self.order_type,
            "price": self.price,
            "quantity": self.quantity,
            "total_value": self.total_value,
            "commission": self.commission,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass
class ArbitrageOperation:
    """Modelo de operación de arbitraje"""
    operation_id: str
    route: Optional[ArbitrageRoute] = None
    status: str = OperationStatus.PENDIENTE.value
    initial_capital: float = 0.0
    ai_analysis: Optional[AIAnalysis] = None
    user_decision: Optional[str] = None
    executed_pairs: List[ExecutedPair] = field(default_factory=list)
    slippage: Optional[float] = None
    total_commissions: Optional[float] = None
    net_profit: Optional[float] = None
    real_roi: Optional[float] = None
    execution_start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    execution_log: str = ""
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ArbitrageOperation":
        """
        Crea una instancia de ArbitrageOperation a partir de un diccionario
        
        Args:
            data: Diccionario con datos de operación
            
        Returns:
            ArbitrageOperation: Instancia creada
        """
        # Parsear tiempos
        start_time = data.get("fecha_inicio_ejecucion")
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        
        completion_time = data.get("fecha_completado")
        if isinstance(completion_time, str):
            completion_time = datetime.fromisoformat(completion_time.replace("Z", "+00:00"))
        
        # Construir ruta de arbitraje
        route_data = data.get("ruta_arbitraje")
        route = None
        if route_data:
            if isinstance(route_data, dict):
                route = ArbitrageRoute.from_dict(route_data)
            elif isinstance(route_data, str):
                route = ArbitrageRoute(route=route_data)
        
        # Construir análisis de IA
        ai_analysis_data = data.get("analisis_ia")
        ai_analysis = None
        if ai_analysis_data and isinstance(ai_analysis_data, dict):
            ai_analysis = AIAnalysis.from_dict(ai_analysis_data)
        
        # Construir pares ejecutados
        executed_pairs = []
        pairs_data = data.get("pares_ejecutados", [])
        if pairs_data and isinstance(pairs_data, list):
            executed_pairs = [ExecutedPair.from_dict(pair_data) for pair_data in pairs_data]
        
        return ArbitrageOperation(
            operation_id=data.get("operacion_id", ""),
            route=route,
            status=data.get("estado", OperationStatus.PENDIENTE.value),
            initial_capital=data.get("capital_inicial", 0.0),
            ai_analysis=ai_analysis,
            user_decision=data.get("decision_usuario"),
            executed_pairs=executed_pairs,
            slippage=data.get("slippage_real"),
            total_commissions=data.get("comisiones_totales"),
            net_profit=data.get("ganancia_neta"),
            real_roi=data.get("rentabilidad_real"),
            execution_start_time=start_time,
            completion_time=completion_time,
            execution_log=data.get("log_ejecucion", "")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la instancia a diccionario
        
        Returns:
            Dict[str, Any]: Diccionario con datos de operación
        """
        result = {
            "operacion_id": self.operation_id,
            "estado": self.status,
            "capital_inicial": self.initial_capital,
            "slippage_real": self.slippage,
            "comisiones_totales": self.total_commissions,
            "ganancia_neta": self.net_profit,
            "rentabilidad_real": self.real_roi,
            "log_ejecucion": self.execution_log
        }
        
        # Añadir ruta si existe
        if self.route:
            result["ruta_arbitraje"] = self.route.to_dict()
        
        # Añadir análisis de IA si existe
        if self.ai_analysis:
            result["analisis_ia"] = self.ai_analysis.to_dict()
        
        # Añadir decisión de usuario si existe
        if self.user_decision:
            result["decision_usuario"] = self.user_decision
        
        # Añadir pares ejecutados si existen
        if self.executed_pairs:
            result["pares_ejecutados"] = [pair.to_dict() for pair in self.executed_pairs]
        
        # Añadir tiempos si existen
        if self.execution_start_time:
            result["fecha_inicio_ejecucion"] = self.execution_start_time.isoformat()
        
        if self.completion_time:
            result["fecha_completado"] = self.completion_time.isoformat()
        
        return result

@dataclass
class SystemConfig:
    """Modelo de configuración del sistema"""
    id: int = 1
    operation_mode: str = "testnet"
    default_capital: float = 100.0
    max_capital: float = 1000.0
    min_opportunity_roi: float = 0.2
    max_slippage: float = 0.5
    detection_interval: int = 300
    execution_timeout: int = 30
    auto_approve: bool = False
    auto_approve_threshold: int = 90
    log_level: str = "INFO"
    max_operations_history: int = 1000
    active_hours_start: str = "00:00"
    active_hours_end: str = "23:59"
    active_days: List[str] = field(default_factory=lambda: ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
    alerts: Dict[str, Any] = field(default_factory=lambda: {
        "cpu_threshold": 80,
        "memory_threshold": 85,
        "disk_threshold": 90,
        "check_interval": 15,
        "alert_on_downtime": True
    })
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SystemConfig":
        """
        Crea una instancia de SystemConfig a partir de un diccionario
        
        Args:
            data: Diccionario con datos de configuración
            
        Returns:
            SystemConfig: Instancia creada
        """
        # Extraer configuración de alertas
        alerts = {
            "cpu_threshold": data.get("cpu_threshold", 80),
            "memory_threshold": data.get("memory_threshold", 85),
            "disk_threshold": data.get("disk_threshold", 90),
            "check_interval": data.get("check_interval", 15),
            "alert_on_downtime": data.get("alert_on_downtime", True)
        }
        
        return SystemConfig(
            id=data.get("id", 1),
            operation_mode=data.get("operation_mode", "testnet"),
            default_capital=float(data.get("default_capital", 100.0)),
            max_capital=float(data.get("max_capital", 1000.0)),
            min_opportunity_roi=float(data.get("min_opportunity_roi", 0.2)),
            max_slippage=float(data.get("max_slippage", 0.5)),
            detection_interval=int(data.get("detection_interval", 300)),
            execution_timeout=int(data.get("execution_timeout", 30)),
            auto_approve=bool(data.get("auto_approve", False)),
            auto_approve_threshold=int(data.get("auto_approve_threshold", 90)),
            log_level=data.get("log_level", "INFO"),
            max_operations_history=int(data.get("max_operations_history", 1000)),
            active_hours_start=data.get("active_hours_start", "00:00"),
            active_hours_end=data.get("active_hours_end", "23:59"),
            active_days=data.get("active_days", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]),
            alerts=alerts
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la instancia a diccionario
        
        Returns:
            Dict[str, Any]: Diccionario con datos de configuración
        """
        return {
            "id": self.id,
            "operation_mode": self.operation_mode,
            "default_capital": self.default_capital,
            "max_capital": self.max_capital,
            "min_opportunity_roi": self.min_opportunity_roi,
            "max_slippage": self.max_slippage,
            "detection_interval": self.detection_interval,
            "execution_timeout": self.execution_timeout,
            "auto_approve": self.auto_approve,
            "auto_approve_threshold": self.auto_approve_threshold,
            "log_level": self.log_level,
            "max_operations_history": self.max_operations_history,
            "active_hours_start": self.active_hours_start,
            "active_hours_end": self.active_hours_end,
            "active_days": self.active_days,
            "cpu_threshold": self.alerts.get("cpu_threshold", 80),
            "memory_threshold": self.alerts.get("memory_threshold", 85),
            "disk_threshold": self.alerts.get("disk_threshold", 90),
            "check_interval": self.alerts.get("check_interval", 15),
            "alert_on_downtime": self.alerts.get("alert_on_downtime", True)
        }

@dataclass
class UserCredentials:
    """Modelo de credenciales de usuario"""
    email: str
    password: str

@dataclass
class User:
    """Modelo de usuario"""
    id: str
    email: str
    role: str = "user"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la instancia a diccionario
        
        Returns:
            Dict[str, Any]: Diccionario con datos de usuario
        """
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role
        }