"""
Interfaces para repositorios de datos.
Siguiendo el principio de inversión de dependencias (DIP), definimos interfaces
para los repositorios que utilizarán los servicios.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

# Tipo genérico para modelos
T = TypeVar('T')

class Repository(Generic[T], ABC):
    """Interfaz base para repositorios"""
    
    @abstractmethod
    def get_by_id(self, id: Any) -> Optional[T]:
        """
        Obtiene una entidad por su ID
        
        Args:
            id: ID de la entidad
            
        Returns:
            Optional[T]: Entidad encontrada o None si no existe
        """
        pass
    
    @abstractmethod
    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Obtiene todas las entidades
        
        Args:
            limit: Número máximo de entidades a obtener
            offset: Índice desde el cual comenzar
            
        Returns:
            List[T]: Lista de entidades
        """
        pass
    
    @abstractmethod
    def create(self, entity: T) -> T:
        """
        Crea una nueva entidad
        
        Args:
            entity: Entidad a crear
            
        Returns:
            T: Entidad creada
        """
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """
        Actualiza una entidad existente
        
        Args:
            entity: Entidad a actualizar
            
        Returns:
            T: Entidad actualizada
        """
        pass
    
    @abstractmethod
    def delete(self, id: Any) -> bool:
        """
        Elimina una entidad por su ID
        
        Args:
            id: ID de la entidad a eliminar
            
        Returns:
            bool: True si la eliminación fue exitosa, False en caso contrario
        """
        pass
