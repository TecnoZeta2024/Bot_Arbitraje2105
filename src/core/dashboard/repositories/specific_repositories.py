"""
Interfaces específicas para repositorios de tokens, operaciones y configuración.
"""

from abc import abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.dashboard.models.config_model import SystemConfig
from src.core.dashboard.models.operation_model import ArbitrageOperation
from src.core.dashboard.models.token_model import Token
from src.core.dashboard.repositories.repository_interface import Repository


class TokenRepository(Repository[Token]):
    """Interfaz para repositorio de tokens"""
    
    @abstractmethod
    def get_by_symbol(self, symbol: str) -> Optional[Token]:
        """
        Obtiene un token por su símbolo
        
        Args:
            symbol: Símbolo del token
            
        Returns:
            Optional[Token]: Token encontrado o None si no existe
        """
        pass
    
    @abstractmethod
    def search_by_symbol(self, query: str, limit: int = 20) -> List[Token]:
        """
        Busca tokens por coincidencia parcial en el símbolo
        
        Args:
            query: Texto a buscar
            limit: Número máximo de resultados
            
        Returns:
            List[Token]: Lista de tokens que coinciden con la búsqueda
        """
        pass
    
    @abstractmethod
    def get_tokens_by_criteria(self, min_market_cap: float = 0, min_volume: float = 0, limit: int = 100) -> List[Token]:
        """
        Obtiene tokens según criterios específicos
        
        Args:
            min_market_cap: Capitalización de mercado mínima
            min_volume: Volumen mínimo en 24h
            limit: Número máximo de resultados
            
        Returns:
            List[Token]: Lista de tokens que cumplen los criterios
        """
        pass
    
    @abstractmethod
    def update_multiple(self, tokens: List[Token]) -> bool:
        """
        Actualiza múltiples tokens a la vez
        
        Args:
            tokens: Lista de tokens a actualizar
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario
        """
        pass

class OperationRepository(Repository[ArbitrageOperation]):
    """Interfaz para repositorio de operaciones de arbitraje"""
    
    @abstractmethod
    def get_by_operation_id(self, operation_id: str) -> Optional[ArbitrageOperation]:
        """
        Obtiene una operación por su ID de operación
        
        Args:
            operation_id: ID único de la operación
            
        Returns:
            Optional[ArbitrageOperation]: Operación encontrada o None si no existe
        """
        pass
    
    @abstractmethod
    def get_by_status(self, status: str, limit: int = 100) -> List[ArbitrageOperation]:
        """
        Obtiene operaciones según su estado
        
        Args:
            status: Estado de las operaciones a buscar
            limit: Número máximo de resultados
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones con el estado especificado
        """
        pass
    
    @abstractmethod
    def get_recent_operations(self, limit: int = 10) -> List[ArbitrageOperation]:
        """
        Obtiene las operaciones más recientes
        
        Args:
            limit: Número máximo de resultados
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones recientes
        """
        pass
    
    @abstractmethod
    def get_operations_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ArbitrageOperation]:
        """
        Obtiene operaciones en un rango de fechas
        
        Args:
            start_date: Fecha de inicio del rango
            end_date: Fecha de fin del rango
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones en el rango de fechas
        """
        pass

class ConfigRepository(Repository[SystemConfig]):
    """Interfaz para repositorio de configuración del sistema"""
    
    @abstractmethod
    def get_current_config(self) -> Optional[SystemConfig]:
        """
        Obtiene la configuración actual del sistema
        
        Returns:
            Optional[SystemConfig]: Configuración actual o None si no existe
        """
        pass
    
    @abstractmethod
    def save_config(self, config: SystemConfig) -> bool:
        """
        Guarda la configuración del sistema
        
        Args:
            config: Configuración a guardar
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario
        """
        pass
    
    @abstractmethod
    def get_config_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de cambios en la configuración
        
        Args:
            limit: Número máximo de registros a obtener
            
        Returns:
            List[Dict[str, Any]]: Historial de cambios en la configuración
        """
        pass
