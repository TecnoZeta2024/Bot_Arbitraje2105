"""
Sistema de Monitoreo Integral - Métricas, Alertas y Health Checks
"""

import asyncio
import json
import logging
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AlertSeverity(Enum):
    """Niveles de severidad de alertas."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """Estados de salud del sistema."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alerta del sistema."""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    component: str
    tags: Dict[str, str] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class HealthCheck:
    """Resultado de un health check."""
    component: str
    status: HealthStatus
    message: str
    timestamp: datetime
    latency_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Metric:
    """Métrica del sistema."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


class MetricsCollector:
    """Recolector de métricas del sistema."""
    
    def __init__(self):
        self.logger = logging.getLogger("MetricsCollector")
        self.metrics_history = defaultdict(deque)
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Incrementa un contador."""
        key = self._make_key(name, tags or {})
        self.counters[key] += value
        
        metric = Metric(
            name=name,
            value=self.counters[key],
            timestamp=datetime.now(),
            tags=tags or {},
            unit="count"
        )
        
        self._store_metric(metric)
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Establece el valor de un gauge."""
        key = self._make_key(name, tags or {})
        self.gauges[key] = value
        
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        
        self._store_metric(metric)
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Registra un valor en un histograma."""
        key = self._make_key(name, tags or {})
        self.histograms[key].append(value)
        
        # Mantener solo los últimos 1000 valores
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
        
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        
        self._store_metric(metric)
    
    def _make_key(self, name: str, tags: Dict[str, str]) -> str:
        """Crea una clave única para la métrica."""
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}|{tag_str}" if tag_str else name
    
    def _store_metric(self, metric: Metric):
        """Almacena la métrica en el historial."""
        key = self._make_key(metric.name, metric.tags)
        self.metrics_history[key].append(metric)
        
        # Mantener solo las últimas 1000 métricas por tipo
        if len(self.metrics_history[key]) > 1000:
            self.metrics_history[key].popleft()
    
    def get_metric_stats(self, name: str, tags: Dict[str, str] = None) -> Dict[str, float]:
        """Obtiene estadísticas de una métrica."""
        key = self._make_key(name, tags or {})
        
        if name in [m.name for m in self.metrics_history.get(key, [])]:
            values = [m.value for m in self.metrics_history[key]]
            
            if values:
                return {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "p50": statistics.median(values),
                    "p95": statistics.quantiles(values, n=20)[18] if len(values) > 20 else max(values),
                    "p99": statistics.quantiles(values, n=100)[98] if len(values) > 100 else max(values)
                }
        
        return {}


class AlertManager:
    """Gestor de alertas del sistema."""
    
    def __init__(self):
        self.logger = logging.getLogger("AlertManager")
        self.alerts = {}
        self.alert_handlers = defaultdict(list)
        self.alert_history = deque(maxlen=1000)
        
    def register_alert_handler(self, severity: AlertSeverity, handler: Callable[[Alert], None]):
        """Registra un manejador de alertas."""
        self.alert_handlers[severity].append(handler)
        self.logger.info(f"Registered alert handler for {severity.value}")
    
    async def create_alert(
        self,
        alert_id: str,
        severity: AlertSeverity,
        title: str,
        message: str,
        component: str,
        tags: Dict[str, str] = None
    ) -> Alert:
        """Crea una nueva alerta."""
        alert = Alert(
            id=alert_id,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(),
            component=component,
            tags=tags or {}
        )
        
        self.alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Notificar a manejadores
        await self._notify_handlers(alert)
        
        self.logger.warning(
            f"Alert created - {severity.value.upper()}: {title} ({component})"
        )
        
        return alert
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resuelve una alerta."""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            
            self.logger.info(f"Alert resolved: {alert_id}")
            return True
        
        return False
    
    async def _notify_handlers(self, alert: Alert):
        """Notifica a los manejadores de alertas."""
        handlers = self.alert_handlers.get(alert.severity, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                self.logger.error(f"Error notifying alert handler: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Obtiene alertas activas."""
        return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Obtiene historial de alertas."""
        return list(self.alert_history)[-limit:]


class HealthChecker:
    """Sistema de health checks."""
    
    def __init__(self):
        self.logger = logging.getLogger("HealthChecker")
        self.health_checks = {}
        self.check_history = defaultdict(deque)
        
    def register_health_check(
        self,
        component: str,
        check_func: Callable[[], HealthCheck],
        interval_seconds: int = 60
    ):
        """Registra un health check."""
        self.health_checks[component] = {
            'func': check_func,
            'interval': interval_seconds,
            'last_check': None
        }
        
        self.logger.info(f"Registered health check for {component} (interval: {interval_seconds}s)")
    
    async def run_health_checks(self) -> Dict[str, HealthCheck]:
        """Ejecuta todos los health checks."""
        results = {}
        
        for component, check_config in self.health_checks.items():
            try:
                start_time = datetime.now()
                
                check_func = check_config['func']
                if asyncio.iscoroutinefunction(check_func):
                    health_check = await check_func()
                else:
                    health_check = check_func()
                
                # Calcular latencia
                latency = (datetime.now() - start_time).total_seconds() * 1000
                health_check.latency_ms = latency
                
                results[component] = health_check
                
                # Almacenar en historial
                self.check_history[component].append(health_check)
                if len(self.check_history[component]) > 100:
                    self.check_history[component].popleft()
                
                check_config['last_check'] = datetime.now()
                
            except Exception as e:
                self.logger.error(f"Error running health check for {component}: {e}")
                
                error_check = HealthCheck(
                    component=component,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {str(e)}",
                    timestamp=datetime.now()
                )
                
                results[component] = error_check
        
        return results
    
    def get_overall_health(self) -> HealthStatus:
        """Obtiene el estado general de salud del sistema."""
        if not self.check_history:
            return HealthStatus.UNHEALTHY
        
        latest_checks = {}
        for component, checks in self.check_history.items():
            if checks:
                latest_checks[component] = checks[-1]
        
        if not latest_checks:
            return HealthStatus.UNHEALTHY
        
        statuses = [check.status for check in latest_checks.values()]
        
        # Si hay algún estado crítico
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        
        # Si hay algún estado no saludable
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        
        # Si hay algún estado degradado
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY


class SystemMonitor:
    """Monitor principal del sistema."""
    
    def __init__(self):
        self.logger = logging.getLogger("SystemMonitor")
        
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.health_checker = HealthChecker()
        
        self.is_running = False
        self.monitoring_interval = 30  # segundos
        
        # Registrar health checks básicos
        self._register_default_health_checks()
        
        self.logger.info("SystemMonitor initialized")
    
    async def start(self):
        """Inicia el sistema de monitoreo."""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("Starting system monitoring")
        
        # Iniciar loops de monitoreo
        asyncio.create_task(self._monitoring_loop())
    
    async def stop(self):
        """Detiene el sistema de monitoreo."""
        self.is_running = False
        self.logger.info("Stopping system monitoring")
    
    async def _monitoring_loop(self):
        """Loop principal de monitoreo."""
        while self.is_running:
            try:
                # Ejecutar health checks
                health_results = await self.health_checker.run_health_checks()
                
                # Generar alertas basadas en health checks
                await self._process_health_results(health_results)
                
                # Reportar métricas de monitoreo
                self.metrics_collector.set_gauge(
                    "system.health_checks.total",
                    len(health_results)
                )
                
                healthy_count = sum(
                    1 for check in health_results.values()
                    if check.status == HealthStatus.HEALTHY
                )
                
                self.metrics_collector.set_gauge(
                    "system.health_checks.healthy",
                    healthy_count
                )
                
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _process_health_results(self, health_results: Dict[str, HealthCheck]):
        """Procesa resultados de health checks y genera alertas."""
        for component, health_check in health_results.items():
            if health_check.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                alert_id = f"health.{component}.{health_check.status.value}"
                
                severity = AlertSeverity.CRITICAL if health_check.status == HealthStatus.CRITICAL else AlertSeverity.ERROR
                
                await self.alert_manager.create_alert(
                    alert_id=alert_id,
                    severity=severity,
                    title=f"Health Check Failed: {component}",
                    message=health_check.message,
                    component=component,
                    tags={
                        "health_status": health_check.status.value,
                        "latency_ms": str(health_check.latency_ms)
                    }
                )
    
    def _register_default_health_checks(self):
        """Registra health checks por defecto."""
        
        def system_health_check() -> HealthCheck:
            """Health check básico del sistema."""
            try:
                # Verificar memoria, CPU, etc.
                import psutil
                
                memory_percent = psutil.virtual_memory().percent
                cpu_percent = psutil.cpu_percent(interval=1)
                
                if memory_percent > 90 or cpu_percent > 90:
                    return HealthCheck(
                        component="system",
                        status=HealthStatus.DEGRADED,
                        message=f"High resource usage - Memory: {memory_percent}%, CPU: {cpu_percent}%",
                        timestamp=datetime.now(),
                        details={
                            "memory_percent": memory_percent,
                            "cpu_percent": cpu_percent
                        }
                    )
                
                return HealthCheck(
                    component="system",
                    status=HealthStatus.HEALTHY,
                    message="System resources are healthy",
                    timestamp=datetime.now(),
                    details={
                        "memory_percent": memory_percent,
                        "cpu_percent": cpu_percent
                    }
                )
                
            except Exception as e:
                return HealthCheck(
                    component="system",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Unable to check system resources: {str(e)}",
                    timestamp=datetime.now()
                )
        
        self.health_checker.register_health_check("system", system_health_check, 60)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del sistema."""
        overall_health = self.health_checker.get_overall_health()
        active_alerts = self.alert_manager.get_active_alerts()
        
        return {
            "overall_health": overall_health.value,
            "active_alerts_count": len(active_alerts),
            "monitoring_status": "running" if self.is_running else "stopped",
            "timestamp": datetime.now().isoformat()
        }
