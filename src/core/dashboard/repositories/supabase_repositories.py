"""
Implementaciones concretas de repositorios utilizando Supabase.
"""

import json
import logging
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, Generic, List, Optional, TypeVar, cast

from supabase import Client, create_client

from src.core.dashboard.models.config_model import SystemConfig
from src.core.dashboard.models.operation_model import ArbitrageOperation
from src.core.dashboard.models.token_model import Token
from src.core.dashboard.repositories.repository_interface import Repository
from src.core.dashboard.repositories.specific_repositories import (
    ConfigRepository,
    OperationRepository,
    TokenRepository,
)

# Configurar logging
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Obtiene un cliente de Supabase singleton
    
    Returns:
        Client: Cliente de Supabase
    """
    import os
    supabase_url = os.getenv("SUPABASE_URL", "https://almhlhmijfkcvmdbidvw.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFsbWhsaG1pamZrY3ZtZGJpZHZ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY4NDUyMjksImV4cCI6MjA2MjQyMTIyOX0.-Jma387OwDcnOnoiR0g8KJT6QussDmxj4ot363SuKbk")
    return create_client(supabase_url, supabase_key)

# Implementación genérica base
T = TypeVar('T')

class SupabaseRepository(Repository[T], Generic[T]):
    """Implementación base de repositorio con Supabase"""
    
    def __init__(self, table_name: str, model_class):
        """
        Inicializa el repositorio
        
        Args:
            table_name: Nombre de la tabla en Supabase
            model_class: Clase del modelo que maneja este repositorio
        """
        self.table_name = table_name
        self.model_class = model_class
        self.supabase = get_supabase_client()
    
    def get_by_id(self, id: Any) -> Optional[T]:
        """
        Obtiene una entidad por su ID
        
        Args:
            id: ID de la entidad
            
        Returns:
            Optional[T]: Entidad encontrada o None si no existe
        """
        try:
            response = self.supabase.table(self.table_name).select("*").eq("id", id).execute()
            if response.data and len(response.data) > 0:
                return self.model_class.from_dict(response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error al obtener entidad por ID: {str(e)}")
            return None
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Obtiene todas las entidades
        
        Args:
            limit: Número máximo de entidades a obtener
            offset: Índice desde el cual comenzar
            
        Returns:
            List[T]: Lista de entidades
        """
        try:
            response = self.supabase.table(self.table_name).select("*").range(offset, offset + limit - 1).execute()
            if response.data:
                return [self.model_class.from_dict(item) for item in response.data]
            return []
        except Exception as e:
            logger.error(f"Error al obtener todas las entidades: {str(e)}")
            return []
    
    def create(self, entity: T) -> T:
        """
        Crea una nueva entidad
        
        Args:
            entity: Entidad a crear
            
        Returns:
            T: Entidad creada
        """
        try:
            data = entity.to_dict()
            if "id" in data:
                del data["id"]  # Supabase se encarga de generar el ID
                
            response = self.supabase.table(self.table_name).insert(data).execute()
            if response.data and len(response.data) > 0:
                return self.model_class.from_dict(response.data[0])
            return entity
        except Exception as e:
            logger.error(f"Error al crear entidad: {str(e)}")
            return entity
    
    def update(self, entity: T) -> T:
        """
        Actualiza una entidad existente
        
        Args:
            entity: Entidad a actualizar
            
        Returns:
            T: Entidad actualizada
        """
        try:
            data = entity.to_dict()
            entity_id = data.get("id")
            
            if not entity_id:
                logger.error("No se puede actualizar una entidad sin ID")
                return entity
                
            response = self.supabase.table(self.table_name).update(data).eq("id", entity_id).execute()
            if response.data and len(response.data) > 0:
                return self.model_class.from_dict(response.data[0])
            return entity
        except Exception as e:
            logger.error(f"Error al actualizar entidad: {str(e)}")
            return entity
    
    def delete(self, id: Any) -> bool:
        """
        Elimina una entidad por su ID
        
        Args:
            id: ID de la entidad a eliminar
            
        Returns:
            bool: True si la eliminación fue exitosa, False en caso contrario
        """
        try:
            response = self.supabase.table(self.table_name).delete().eq("id", id).execute()
            return True if response.data else False
        except Exception as e:
            logger.error(f"Error al eliminar entidad: {str(e)}")
            return False

class SupabaseTokenRepository(SupabaseRepository[Token], TokenRepository):
    """Implementación de repositorio de tokens con Supabase"""
    
    def __init__(self):
        """Inicializa el repositorio de tokens"""
        super().__init__("token_candidatos", Token)
    
    def get_by_symbol(self, symbol: str) -> Optional[Token]:
        """
        Obtiene un token por su símbolo
        
        Args:
            symbol: Símbolo del token
            
        Returns:
            Optional[Token]: Token encontrado o None si no existe
        """
        try:
            response = self.supabase.table(self.table_name).select("*").eq("simbolo", symbol.upper()).execute()
            if response.data and len(response.data) > 0:
                return Token.from_dict(response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error al obtener token por símbolo: {str(e)}")
            return None
    
    def search_by_symbol(self, query: str, limit: int = 20) -> List[Token]:
        """
        Busca tokens por coincidencia parcial en el símbolo
        
        Args:
            query: Texto a buscar
            limit: Número máximo de resultados
            
        Returns:
            List[Token]: Lista de tokens que coinciden con la búsqueda
        """
        try:
            response = self.supabase.table(self.table_name).select("*").ilike("simbolo", f"%{query}%").limit(limit).execute()
            if response.data:
                return [Token.from_dict(item) for item in response.data]
            return []
        except Exception as e:
            logger.error(f"Error al buscar tokens por símbolo: {str(e)}")
            return []
    
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
        try:
            query = self.supabase.table(self.table_name).select("*")
            
            if min_market_cap > 0:
                query = query.gte("market_cap", min_market_cap)
            
            if min_volume > 0:
                query = query.gte("volumen_binance_24h", min_volume)
            
            response = query.limit(limit).execute()
            
            if response.data:
                return [Token.from_dict(item) for item in response.data]
            return []
        except Exception as e:
            logger.error(f"Error al obtener tokens por criterios: {str(e)}")
            return []
    
    def update_multiple(self, tokens: List[Token]) -> bool:
        """
        Actualiza múltiples tokens a la vez
        
        Args:
            tokens: Lista de tokens a actualizar
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario
        """
        try:
            # Convertir tokens a diccionarios
            token_dicts = [token.to_dict() for token in tokens]
            
            # Supabase tiene un límite de registros por operación, usar lotes de 100
            batch_size = 100
            for i in range(0, len(token_dicts), batch_size):
                batch = token_dicts[i:i+batch_size]
                # Utilizamos upsert para actualizar si existe o insertar si no existe
                self.supabase.table(self.table_name).upsert(batch, on_conflict="simbolo").execute()
            
            return True
        except Exception as e:
            logger.error(f"Error al actualizar múltiples tokens: {str(e)}")
            return False

class SupabaseOperationRepository(SupabaseRepository[ArbitrageOperation], OperationRepository):
    """Implementación de repositorio de operaciones de arbitraje con Supabase"""
    
    def __init__(self):
        """Inicializa el repositorio de operaciones"""
        super().__init__("arbitraje_operaciones", ArbitrageOperation)
    
    def get_by_operation_id(self, operation_id: str) -> Optional[ArbitrageOperation]:
        """
        Obtiene una operación por su ID de operación
        
        Args:
            operation_id: ID único de la operación
            
        Returns:
            Optional[ArbitrageOperation]: Operación encontrada o None si no existe
        """
        try:
            response = self.supabase.table(self.table_name).select("*").eq("operacion_id", operation_id).execute()
            if response.data and len(response.data) > 0:
                return ArbitrageOperation.from_dict(response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error al obtener operación por ID: {str(e)}")
            return None
    
    def get_by_status(self, status: str, limit: int = 100) -> List[ArbitrageOperation]:
        """
        Obtiene operaciones según su estado
        
        Args:
            status: Estado de las operaciones a buscar
            limit: Número máximo de resultados
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones con el estado especificado
        """
        try:
            response = self.supabase.table(self.table_name).select("*").eq("estado", status).limit(limit).execute()
            if response.data:
                return [ArbitrageOperation.from_dict(item) for item in response.data]
            return []
        except Exception as e:
            logger.error(f"Error al obtener operaciones por estado: {str(e)}")
            return []
    
    def get_recent_operations(self, limit: int = 10) -> List[ArbitrageOperation]:
        """
        Obtiene las operaciones más recientes
        
        Args:
            limit: Número máximo de resultados
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones recientes
        """
        try:
            response = self.supabase.table(self.table_name).select("*").order("fecha_inicio_ejecucion", desc=True).limit(limit).execute()
            if response.data:
                return [ArbitrageOperation.from_dict(item) for item in response.data]
            return []
        except Exception as e:
            logger.error(f"Error al obtener operaciones recientes: {str(e)}")
            return []
    
    def get_operations_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ArbitrageOperation]:
        """
        Obtiene operaciones en un rango de fechas
        
        Args:
            start_date: Fecha de inicio del rango
            end_date: Fecha de fin del rango
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones en el rango de fechas
        """
        try:
            # Convertir fechas a formato ISO
            start_iso = start_date.isoformat()
            end_iso = end_date.isoformat()
            
            response = self.supabase.table(self.table_name).select("*") \
                .gte("fecha_inicio_ejecucion", start_iso) \
                .lte("fecha_inicio_ejecucion", end_iso) \
                .order("fecha_inicio_ejecucion") \
                .execute()
                
            if response.data:
                return [ArbitrageOperation.from_dict(item) for item in response.data]
            return []
        except Exception as e:
            logger.error(f"Error al obtener operaciones por rango de fechas: {str(e)}")
            return []

class SupabaseConfigRepository(SupabaseRepository[SystemConfig], ConfigRepository):
    """Implementación de repositorio de configuración del sistema con Supabase"""
    
    def __init__(self):
        """Inicializa el repositorio de configuración"""
        super().__init__("configuracion_sistema", SystemConfig)
        self._config_history_table = "configuracion_historial"  # Tabla para historial de configuración
    
    def get_current_config(self) -> Optional[SystemConfig]:
        """
        Obtiene la configuración actual del sistema
        
        Returns:
            Optional[SystemConfig]: Configuración actual o None si no existe
        """
        try:
            response = self.supabase.table(self.table_name).select("*").limit(1).execute()
            if response.data and len(response.data) > 0:
                return SystemConfig.from_dict(response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error al obtener configuración actual: {str(e)}")
            return None
    
    def save_config(self, config: SystemConfig) -> bool:
        """
        Guarda la configuración del sistema
        
        Args:
            config: Configuración a guardar
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario
        """
        try:
            data = config.to_dict()
            
            # Verificar si hay configuración existente
            current_config = self.get_current_config()
            
            if current_config:
                # Actualizar configuración existente
                config_id = current_config.id or 1
                response = self.supabase.table(self.table_name).update(data).eq("id", config_id).execute()
                
                # Guardar en historial si la tabla existe
                self._save_to_history(current_config.to_dict())
                
                return True if response.data else False
            else:
                # Crear nueva configuración
                response = self.supabase.table(self.table_name).insert(data).execute()
                return True if response.data else False
        except Exception as e:
            logger.error(f"Error al guardar configuración: {str(e)}")
            return False
    
    def get_config_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de cambios en la configuración
        
        Args:
            limit: Número máximo de registros a obtener
            
        Returns:
            List[Dict[str, Any]]: Historial de cambios en la configuración
        """
        try:
            # Verificar si la tabla de historial existe
            response = self.supabase.table(self._config_history_table).select("*").limit(limit).order("timestamp", desc=True).execute()
            if response.data:
                return response.data
            return []
        except Exception as e:
            logger.error(f"Error al obtener historial de configuración: {str(e)}")
            return []
    
    def _save_to_history(self, config_data: Dict[str, Any]) -> bool:
        """
        Guarda una configuración en el historial
        
        Args:
            config_data: Datos de configuración a guardar
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario
        """
        try:
            # Añadir timestamp
            history_entry = {
                "configuracion": json.dumps(config_data),
                "timestamp": datetime.now().isoformat(),
                "user_id": config_data.get("last_updated_by", "system")
            }
            
            response = self.supabase.table(self._config_history_table).insert(history_entry).execute()
            return True if response.data else False
        except Exception as e:
            logger.warning(f"No se pudo guardar en historial de configuración: {str(e)}")
            return False
