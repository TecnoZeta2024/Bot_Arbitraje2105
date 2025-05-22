"""
Modelos de datos para la configuración del sistema.
Implementa patrones basados en SOLID para mantener la responsabilidad única y extensibilidad.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class WebhookConfig(BaseModel):
    """Configuración de webhooks del sistema"""
    opportunity_webhook: str = Field(default="", description="URL del webhook para enviar oportunidades detectadas")
    result_webhook: str = Field(default="", description="URL del webhook para enviar resultados de ejecución")
    decision_webhook: str = Field(default="", description="URL del webhook para recibir decisiones del usuario")
    
class ApiServerConfig(BaseModel):
    """Configuración del servidor API"""
    host: str = Field(default="localhost", description="Host del servidor API")
    port: int = Field(default=8000, description="Puerto del servidor API")
    base_url: str = Field(default="", description="URL base del servidor API")
    
class NotificationConfig(BaseModel):
    """Configuración de notificaciones"""
    notify_opportunity: bool = Field(default=True, description="Notificar oportunidades detectadas")
    notify_execution: bool = Field(default=True, description="Notificar ejecución de operaciones")
    notify_result: bool = Field(default=True, description="Notificar resultados de operaciones")
    notify_errors: bool = Field(default=True, description="Notificar errores")
    notify_min_priority: str = Field(default="Media", description="Nivel mínimo de prioridad para notificaciones")
    
class ReportConfig(BaseModel):
    """Configuración de informes periódicos"""
    enable_reports: bool = Field(default=True, description="Habilitar informes periódicos")
    report_frequency: str = Field(default="Diario", description="Frecuencia de informes")
    report_time: str = Field(default="20:00", description="Hora del informe")
    include_profit_metrics: bool = Field(default=True, description="Incluir métricas de rentabilidad")
    include_route_analysis: bool = Field(default=True, description="Incluir análisis de rutas")
    include_token_metrics: bool = Field(default=True, description="Incluir métricas de tokens")
    include_recommendations: bool = Field(default=True, description="Incluir recomendaciones")
    
class AlertConfig(BaseModel):
    """Configuración de alertas del sistema"""
    enable_status_alerts: bool = Field(default=True, description="Habilitar alertas de estado")
    cpu_threshold: int = Field(default=80, description="Umbral de uso de CPU (%)")
    memory_threshold: int = Field(default=85, description="Umbral de uso de memoria (%)")
    disk_threshold: int = Field(default=90, description="Umbral de uso de disco (%)")
    check_interval: int = Field(default=15, description="Intervalo de verificación (minutos)")
    alert_on_downtime: bool = Field(default=True, description="Alertar en caso de caída")
    
class TokenFilterConfig(BaseModel):
    """Configuración de filtros de tokens"""
    min_market_cap: int = Field(default=10000000, description="Market cap mínimo (USD)")
    min_binance_volume: int = Field(default=1000000, description="Volumen mínimo en Binance (USD/24h)")
    max_volatility_1h: float = Field(default=5.0, description="Volatilidad máxima 1h (%)")
    max_volatility_24h: float = Field(default=15.0, description="Volatilidad máxima 24h (%)")
    max_tokens: int = Field(default=100, description="Número máximo de tokens")
    blacklisted_tokens: List[str] = Field(default=[], description="Tokens en lista negra")
    
class OperationConfig(BaseModel):
    """Configuración de operaciones"""
    operation_mode: str = Field(default="testnet", description="Modo de operación")
    default_capital: float = Field(default=100.0, description="Capital por defecto (USDT)")
    max_capital: float = Field(default=1000.0, description="Capital máximo (USDT)")
    min_opportunity_roi: float = Field(default=0.2, description="Rentabilidad mínima (%)")
    max_slippage: float = Field(default=0.5, description="Slippage máximo aceptable (%)")
    detection_interval: int = Field(default=300, description="Intervalo de detección (segundos)")
    execution_timeout: int = Field(default=30, description="Timeout de ejecución (segundos)")
    auto_approve: bool = Field(default=False, description="Aprobar automáticamente oportunidades")
    auto_approve_threshold: int = Field(default=90, description="Umbral de confianza para aprobación automática (%)")
    
class SystemOperationConfig(BaseModel):
    """Configuración de funcionamiento del sistema"""
    log_level: str = Field(default="INFO", description="Nivel de detalle para los registros del sistema")
    max_operations_history: int = Field(default=1000, description="Número máximo de operaciones a mantener en historial")
    active_hours_start: str = Field(default="00:00", description="Hora de inicio de operaciones (UTC)")
    active_hours_end: str = Field(default="23:59", description="Hora de fin de operaciones (UTC)")
    # active_days: List[str] = Field(default=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"], description="Días de la semana en que el sistema operará") # Removed as column does not exist in DB
    
class SystemConfig(BaseModel):
    """Configuración completa del sistema"""
    id: Optional[str] = Field(default=None, description="ID del registro de configuración (UUID)") # Changed to Optional[str]
    operation: OperationConfig = Field(default_factory=OperationConfig, description="Configuración de operaciones")
    system: SystemOperationConfig = Field(default_factory=SystemOperationConfig, description="Configuración de funcionamiento del sistema")
    token_filters: TokenFilterConfig = Field(default_factory=TokenFilterConfig, description="Configuración de filtros de tokens")
    webhooks: WebhookConfig = Field(default_factory=WebhookConfig, description="Configuración de webhooks")
    api_server: ApiServerConfig = Field(default_factory=ApiServerConfig, description="Configuración del servidor API")
    notifications: NotificationConfig = Field(default_factory=NotificationConfig, description="Configuración de notificaciones")
    reports: ReportConfig = Field(default_factory=ReportConfig, description="Configuración de informes periódicos")
    alerts: AlertConfig = Field(default_factory=AlertConfig, description="Configuración de alertas del sistema")
    last_updated: Optional[datetime] = Field(default=None, description="Fecha y hora de la última actualización")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemConfig':
        """
        Crea una instancia de SystemConfig a partir de un diccionario
        
        Args:
            data: Diccionario con datos de configuración
            
        Returns:
            Instancia de SystemConfig
        """
        if not data:
            return cls()
            
        # Extraer configuraciones específicas de los datos generales
        operation_config = OperationConfig(
            operation_mode=data.get("operation_mode", "testnet"),
            default_capital=data.get("default_capital", 100.0),
            max_capital=data.get("max_capital", 1000.0),
            min_opportunity_roi=data.get("min_opportunity_roi", 0.2),
            max_slippage=data.get("max_slippage", 0.5),
            detection_interval=data.get("detection_interval", 300),
            execution_timeout=data.get("execution_timeout", 30),
            auto_approve=data.get("auto_approve", False),
            auto_approve_threshold=data.get("auto_approve_threshold", 90)
        )
        
        system_config = SystemOperationConfig(
            log_level=data.get("log_level", "INFO"),
            max_operations_history=data.get("max_operations_history", 1000),
            active_hours_start=data.get("active_hours_start", "00:00"),
            active_hours_end=data.get("active_hours_end", "23:59"),
            # active_days=data.get("active_days", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]) # Removed
        )
        
        token_filters = TokenFilterConfig(
            min_market_cap=data.get("min_market_cap", 10000000),
            min_binance_volume=data.get("min_binance_volume", 1000000),
            max_volatility_1h=data.get("max_volatility_1h", 5.0),
            max_volatility_24h=data.get("max_volatility_24h", 15.0),
            max_tokens=data.get("max_tokens", 100),
            blacklisted_tokens=data.get("blacklisted_tokens", [])
        )
        
        webhooks = WebhookConfig(
            opportunity_webhook=data.get("n8n_webhook_oportunidad", ""),
            result_webhook=data.get("n8n_webhook_resultado", ""),
            decision_webhook=data.get("n8n_webhook_decision", "")
        )
        
        api_server = ApiServerConfig(
            host=data.get("api_host", "localhost"),
            port=data.get("api_port", 8000),
            base_url=data.get("api_base_url", "")
        )
        
        notifications = NotificationConfig(
            notify_opportunity=data.get("notify_opportunity", True),
            notify_execution=data.get("notify_execution", True),
            notify_result=data.get("notify_result", True),
            notify_errors=data.get("notify_errors", True),
            notify_min_priority=data.get("notify_min_priority", "Media")
        )
        
        reports = ReportConfig(
            enable_reports=data.get("enable_reports", True),
            report_frequency=data.get("report_frequency", "Diario"),
            report_time=data.get("report_time", "20:00"),
            include_profit_metrics=data.get("include_profit_metrics", True),
            include_route_analysis=data.get("include_route_analysis", True),
            include_token_metrics=data.get("include_token_metrics", True),
            include_recommendations=data.get("include_recommendations", True)
        )
        
        alerts = AlertConfig(
            enable_status_alerts=data.get("enable_status_alerts", True),
            cpu_threshold=data.get("cpu_threshold", 80),
            memory_threshold=data.get("memory_threshold", 85),
            disk_threshold=data.get("disk_threshold", 90),
            check_interval=data.get("check_interval", 15),
            alert_on_downtime=data.get("alert_on_downtime", True)
        )
        
        # Crear instancia
        return cls(
            id=data.get("id"),
            operation=operation_config,
            system=system_config,
            token_filters=token_filters,
            webhooks=webhooks,
            api_server=api_server,
            notifications=notifications,
            reports=reports,
            alerts=alerts,
            last_updated=data.get("last_updated")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la configuración a un diccionario plano
        
        Returns:
            Dict[str, Any]: Diccionario con la configuración
        """
        # Extraer atributos de cada sección y aplanarlos
        operation_dict = self.operation.dict()
        system_dict = self.system.dict()
        # Remove active_days from system_dict if it exists (shouldn't after model change, but for safety)
        system_dict.pop('active_days', None)
        token_filters_dict = self.token_filters.dict()
        webhooks_dict = {
            "n8n_webhook_oportunidad": self.webhooks.opportunity_webhook,
            "n8n_webhook_resultado": self.webhooks.result_webhook,
            "n8n_webhook_decision": self.webhooks.decision_webhook
        }
        api_server_dict = {
            "api_host": self.api_server.host,
            "api_port": self.api_server.port,
            "api_base_url": self.api_server.base_url
        }
        notifications_dict = self.notifications.dict()
        reports_dict = self.reports.dict()
        alerts_dict = self.alerts.dict()
        
        # Combinar todos los diccionarios en uno solo
        result = {
            **operation_dict,
            **system_dict,
            **token_filters_dict,
            **webhooks_dict,
            **api_server_dict,
            **notifications_dict,
            **reports_dict,
            **alerts_dict,
            "last_updated": datetime.now().isoformat() if not self.last_updated else self.last_updated
        }
        
        if self.id:
            result["id"] = self.id
            
        return result
