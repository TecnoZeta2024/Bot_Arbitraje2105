"""
Inicialización del paquete de servicios.
"""

from src.core.dashboard.services.service_interfaces import (
    AuthService,
    ConfigService,
    TokenService,
    OperationService,
    NotificationService,
    SystemMonitorService
)

from src.core.dashboard.services.service_implementations import (
    SupabaseAuthService,
    DefaultConfigService,
    DefaultTokenService,
    DefaultOperationService,
    DefaultNotificationService,
    DefaultSystemMonitorService
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
