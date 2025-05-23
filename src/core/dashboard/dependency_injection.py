"""
Módulo para gestión de dependencias e inyección de dependencias.
Implementado siguiendo el patrón de Service Locator/Registry.
"""

import logging
from typing import Any, Dict, Generic, Optional, Type, TypeVar

# Import necessary services
from src.apis.binance_client import BinanceClient
from src.apis.mobula_client import MobulaClient
from src.apis.supabase_client import supabase_client  # Import the global instance
from src.core.dashboard.services.opportunity_detection_service import (
    OpportunityDetectionService,
)
from src.utils.config import settings

from .services.ai_report_service import AIReportService  # Import the new service

# Configurar logger
logger = logging.getLogger(__name__)

# Definir tipo genérico para servicios
T = TypeVar('T')

class ServiceRegistry:
    """
    Registro centralizado de servicios para inyección de dependencias
    """
    
    def __init__(self):
        """Inicializa un nuevo registro de servicios"""
        self._services: Dict[Any, Any] = {}
        logger.debug("Registro de servicios inicializado")
    
    def register(self, service_type: Any, instance: Any) -> None:
        """
        Registra una instancia de servicio con un tipo específico
        
        Args:
            service_type: Tipo o clave del servicio
            instance: Instancia del servicio
        """
        self._services[service_type] = instance
        logger.debug(f"Servicio registrado: {service_type}")
    
    def get(self, service_type: Any) -> Any:
        """
        Obtiene una instancia de servicio registrada
        
        Args:
            service_type: Tipo o clave del servicio
        
        Returns:
            Any: Instancia del servicio
        
        Raises:
            KeyError: Si el servicio no está registrado
        """
        if service_type not in self._services:
            logger.error(f"Servicio no encontrado: {service_type}")
            raise KeyError(f"Servicio no registrado: {service_type}")
        
        return self._services[service_type]
    
    def has(self, service_type: Any) -> bool:
        """
        Verifica si un servicio está registrado
        
        Args:
            service_type: Tipo o clave del servicio
        
        Returns:
            bool: True si el servicio está registrado, False en caso contrario
        """
        return service_type in self._services
    
    def clear(self) -> None:
        """Elimina todos los servicios registrados"""
        self._services.clear()
        logger.debug("Registro de servicios limpiado")

# Instancia global del registro de servicios
_service_registry: Optional[ServiceRegistry] = None

def initialize_service_registry() -> None:
    """
    Inicializa el registro global de servicios
    """
    global _service_registry
    _service_registry = ServiceRegistry()
    logger.info("Registro global de servicios inicializado")

    # Register core services
    _service_registry.register(BinanceClient, BinanceClient())
    _service_registry.register(MobulaClient, MobulaClient())
    _service_registry.register(settings, settings)

    # Register OpportunityDetectionService
    binance_client_instance = _service_registry.get(BinanceClient)
    mobula_client_instance = _service_registry.get(MobulaClient)
    settings_instance = _service_registry.get(settings)
    opportunity_detection_service_instance = OpportunityDetectionService(
        binance_client=binance_client_instance,
        mobula_client=mobula_client_instance,
        settings=settings_instance
    )
    _service_registry.register(OpportunityDetectionService, opportunity_detection_service_instance)
    logger.info("OpportunityDetectionService registrado")

    # Register AIReportService
    # Access the global supabase_client instance
    ai_report_service_instance = AIReportService(supabase_client=supabase_client)
    _service_registry.register(AIReportService, ai_report_service_instance)
    logger.info("AIReportService registrado")


def get_service_registry() -> ServiceRegistry:
    """
    Obtiene el registro global de servicios
    
    Returns:
        ServiceRegistry: Registro de servicios
    
    Raises:
        RuntimeError: Si el registro no ha sido inicializado
    """
    global _service_registry
    
    if _service_registry is None:
        logger.error("Registro de servicios no inicializado")
        raise RuntimeError("El registro de servicios no ha sido inicializado. Llama a initialize_service_registry() primero.")
    
    return _service_registry
