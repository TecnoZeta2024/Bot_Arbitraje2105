"""
Módulo para la inicialización de componentes y servicios del dashboard.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from src.core.dashboard.dependency_injection import (
    get_service_registry,
    initialize_service_registry,
)
from src.core.dashboard.repositories import (
    SupabaseTokenRepository,  # Import SupabaseTokenRepository
)
from src.core.dashboard.repositories import (
    FileSystemLogRepository,
    SupabaseConfigRepository,
    SupabaseOperationRepository,
)
from src.core.dashboard.services import (
    DefaultTokenService,  # Import DefaultTokenService implementation
)
from src.core.dashboard.services import TokenService  # Import TokenService interface
from src.core.dashboard.services import (
    AuthService,
    ConfigService,
    DefaultConfigService,
    DefaultNotificationService,
    DefaultOperationService,
    DefaultSystemMonitorService,
    NotificationService,
    OperationService,
    SupabaseAuthService,
    SystemMonitorService,
)
from src.utils.config import settings

# Configurar logger
logger = logging.getLogger(__name__)

def initialize_dashboard():
    """
    Inicializa todos los componentes necesarios para el dashboard
    """
    logger.info("Inicializando dashboard...")
    
    # Cargar variables de entorno si no se han cargado
    load_dotenv()
    
    # Inicializar registro de servicios
    initialize_service_registry()
    
    # Registrar repositorios
    register_repositories()
    
    # Registrar servicios
    register_services()
    
    logger.info("Dashboard inicializado correctamente")

def register_repositories():
    """
    Registra los repositorios necesarios
    """
    logger.info("Registrando repositorios...")
    
    # Crear instancias de repositorios
    operation_repo = SupabaseOperationRepository()
    config_repo = SupabaseConfigRepository()
    log_repo = FileSystemLogRepository(log_dir=get_log_directory())
    token_repo = SupabaseTokenRepository() # Create TokenRepository instance
    
    # Registrar repositorios en el registro de servicios
    registry = get_service_registry()
    registry.register("operation_repository", operation_repo)
    registry.register("config_repository", config_repo)
    registry.register("log_repository", log_repo)
    registry.register("token_repository", token_repo) # Register TokenRepository
    
    logger.info("Repositorios registrados correctamente")

def register_services():
    """
    Registra los servicios necesarios
    """
    logger.info("Registrando servicios...")
    
    # Obtener repositorios
    registry = get_service_registry()
    operation_repo = registry.get("operation_repository")
    config_repo = registry.get("config_repository")
    log_repo = registry.get("log_repository")
    token_repo = registry.get("token_repository") # Get TokenRepository

    # Crear servicios con implementaciones concretas
    auth_service = SupabaseAuthService()
    operation_service = DefaultOperationService(operation_repo)
    config_service = DefaultConfigService(config_repo)
    system_monitor_service = DefaultSystemMonitorService()
    notification_service = DefaultNotificationService(config_service)
    token_service = DefaultTokenService(token_repo) # Create TokenService instance

    # Registrar servicios
    registry.register(AuthService, auth_service)
    registry.register(OperationService, operation_service)
    registry.register(ConfigService, config_service)
    registry.register(SystemMonitorService, system_monitor_service)
    registry.register(NotificationService, notification_service)
    registry.register(TokenService, token_service) # Register TokenService
    
    logger.info("Servicios registrados correctamente")

def get_log_directory() -> Path:
    """
    Obtiene el directorio de logs
    
    Returns:
        Path: Ruta al directorio de logs
    """
    # Obtener directorio base
    base_dir = Path(os.path.abspath(os.path.dirname(__file__))).parent.parent.parent
    log_dir = base_dir / "logs"
    
    # Crear directorio si no existe
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directorio de logs creado: {log_dir}")
    
    return log_dir
