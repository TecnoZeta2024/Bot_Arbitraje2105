"""
Inicialización del paquete de modelos.
"""

from src.core.dashboard.models.config_model import *
from src.core.dashboard.models.operation_model import *
from src.core.dashboard.models.token_model import *
from src.core.dashboard.models.user_model import *

# Exportar todos los modelos
__all__ = [
    # Modelos de configuración
    'SystemConfig',
    'OperationConfig',
    'SystemOperationConfig',
    'TokenFilterConfig',
    'WebhookConfig',
    'ApiServerConfig',
    'NotificationConfig',
    'ReportConfig',
    'AlertConfig',
    
    # Modelos de tokens
    'Token',
    
    # Modelos de operaciones
    'ArbitrageOperation',
    'ArbitrageRoute',
    'ArbitrageAnalysis',
    'OperationStatus',
    
    # Modelos de usuarios
    'User',
    'UserCredentials'
]
