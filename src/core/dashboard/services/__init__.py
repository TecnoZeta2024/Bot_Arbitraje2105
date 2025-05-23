"""
Inicialización del paquete de servicios.
"""

from src.core.dashboard.services.service_implementations import (
    DefaultConfigService,
    DefaultNotificationService,
    DefaultOperationService,
    DefaultSystemMonitorService,
    DefaultTokenService,
    SupabaseAuthService,
)
from src.core.dashboard.services.service_interfaces import (
    AuthService,
    ConfigService,
    NotificationService,
    OperationService,
    SystemMonitorService,
    TokenService,
)
from src.core.dashboard.services.telegram_service import TelegramService

# Exportar todos los servicios
__all__ = [
    # Interfaces
    'AuthService',
    'ConfigService',
    'TokenService',
    'OperationService',
    'NotificationService',
    'SystemMonitorService',
    
    # Implementaciones concretas
    'SupabaseAuthService',
    'DefaultConfigService',
    'DefaultTokenService',
    'DefaultOperationService',
    'DefaultNotificationService',
    'DefaultSystemMonitorService',
    'TelegramService'
]
