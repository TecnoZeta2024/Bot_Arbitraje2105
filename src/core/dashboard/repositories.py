"""
Repositorios para acceso a datos del dashboard.
Implementan el patrón Repository para abstraer el acceso a datos.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import re

from supabase import create_client

from src.core.dashboard.models import (
    ArbitrageOperation,
    SystemConfig,
    OperationStatus
)

# Configurar logger
logger = logging.getLogger(__name__)

class SupabaseOperationRepository:
    """
    Repositorio para acceder a datos de operaciones en Supabase
    """
    
    def __init__(self):
        """Inicializa el repositorio"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.client = create_client(self.supabase_url, self.supabase_key)
        self.table_name = "arbitraje_operaciones"
    
    def get_recent_operations(self, limit: int = 10) -> List[ArbitrageOperation]:
        """
        Obtiene las operaciones más recientes
        
        Args:
            limit: Número máximo de operaciones a obtener
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones
        """
        try:
            response = self.client.table(self.table_name) \
                .select("*") \
                .order("fecha_inicio_ejecucion", desc=True) \
                .limit(limit) \
                .execute()
                
            if hasattr(response, 'data'):
                return [ArbitrageOperation.from_dict(item) for item in response.data]
            return []
        except Exception as e:
            logger.error(f"Error al obtener operaciones recientes: {str(e)}")
            return []
    
    def get_operations_by_status(self, status: str) -> List[ArbitrageOperation]:
        """
        Obtiene operaciones filtradas por estado
        
        Args:
            status: Estado a filtrar
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones
        """
        try:
            response = self.client.table(self.table_name) \
                .select("*") \
                .eq("estado", status) \
                .order("fecha_inicio_ejecucion", desc=True) \
                .execute()
                
            if hasattr(response, 'data'):
                return [ArbitrageOperation.from_dict(item) for item in response.data]
            return []
        except Exception as e:
            logger.error(f"Error al obtener operaciones por estado: {str(e)}")
            return []
    
    def get_operations_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[ArbitrageOperation]:
        """
        Obtiene operaciones en un rango de fechas
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones
        """
        try:
            # Formatear fechas como ISO strings
            start_iso = start_date.isoformat()
            end_iso = end_date.isoformat()
            
            response = self.client.table(self.table_name) \
                .select("*") \
                .gte("fecha_inicio_ejecucion", start_iso) \
                .lte("fecha_inicio_ejecucion", end_iso) \
                .order("fecha_inicio_ejecucion", desc=True) \
                .execute()
                
            if hasattr(response, 'data'):
                return [ArbitrageOperation.from_dict(item) for item in response.data]
            return []
        except Exception as e:
            logger.error(f"Error al obtener operaciones por rango de fechas: {str(e)}")
            return []
    
    def get_filtered_operations(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        statuses: Optional[List[str]] = None,
        min_capital: Optional[float] = None,
        min_roi: Optional[float] = None,
        sort_by: str = "fecha_inicio_ejecucion",
        ascending: bool = False
    ) -> List[ArbitrageOperation]:
        """
        Obtiene operaciones con filtros aplicados
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            statuses: Lista de estados
            min_capital: Capital mínimo
            min_roi: ROI mínimo
            sort_by: Campo para ordenar
            ascending: Orden ascendente o descendente
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones filtradas
        """
        try:
            # Iniciar consulta
            query = self.client.table(self.table_name).select("*")
            
            # Aplicar filtros
            if start_date:
                query = query.gte("fecha_inicio_ejecucion", start_date.isoformat())
            
            if end_date:
                query = query.lte("fecha_inicio_ejecucion", end_date.isoformat())
            
            if statuses:
                query = query.in_("estado", statuses)
            
            if min_capital is not None and min_capital > 0:
                query = query.gte("capital_inicial", min_capital)
            
            if min_roi is not None:
                query = query.gte("rentabilidad_real", min_roi)
            
            # Aplicar orden
            query = query.order(sort_by, desc=not ascending)
            
            # Ejecutar consulta
            response = query.execute()
            
            if hasattr(response, 'data'):
                return [ArbitrageOperation.from_dict(item) for item in response.data]
            return []
        except Exception as e:
            logger.error(f"Error al obtener operaciones filtradas: {str(e)}")
            return []
    
    def get_operation_by_id(self, operation_id: str) -> Optional[ArbitrageOperation]:
        """
        Obtiene una operación por su ID
        
        Args:
            operation_id: ID de la operación
            
        Returns:
            Optional[ArbitrageOperation]: Operación o None si no se encuentra
        """
        try:
            response = self.client.table(self.table_name) \
                .select("*") \
                .eq("operacion_id", operation_id) \
                .execute()
                
            if hasattr(response, 'data') and response.data:
                return ArbitrageOperation.from_dict(response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error al obtener operación por ID: {str(e)}")
            return None

class SupabaseConfigRepository:
    """
    Repositorio para acceder a datos de configuración en Supabase
    """
    
    def __init__(self):
        """Inicializa el repositorio"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.client = create_client(self.supabase_url, self.supabase_key)
        self.table_name = "configuracion_sistema"
    
    def get_system_config(self) -> SystemConfig:
        """
        Obtiene la configuración del sistema
        
        Returns:
            SystemConfig: Configuración del sistema
        """
        try:
            response = self.client.table(self.table_name) \
                .select("*") \
                .eq("id", 1) \
                .execute()
                
            if hasattr(response, 'data') and response.data:
                return SystemConfig.from_dict(response.data[0])
            
            # Si no hay configuración, crear una por defecto
            default_config = SystemConfig()
            self.update_system_config(default_config)
            return default_config
        except Exception as e:
            logger.error(f"Error al obtener configuración del sistema: {str(e)}")
            return SystemConfig()
    
    def update_system_config(self, config: SystemConfig) -> bool:
        """
        Actualiza la configuración del sistema
        
        Args:
            config: Nueva configuración
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            config_dict = config.to_dict()
            
            # Añadir timestamp de actualización
            config_dict["last_updated"] = datetime.now().isoformat()
            
            response = self.client.table(self.table_name) \
                .upsert(config_dict) \
                .execute()
                
            return hasattr(response, 'data') and len(response.data) > 0
        except Exception as e:
            logger.error(f"Error al actualizar configuración del sistema: {str(e)}")
            return False
    
    def get_token_candidates(self, limit: int = 100) -> List[Dict]:
        """
        Obtiene tokens candidatos para arbitraje
        
        Args:
            limit: Número máximo de tokens a obtener
            
        Returns:
            List[Dict]: Lista de tokens candidatos
        """
        try:
            response = self.client.table("token_candidatos") \
                .select("*") \
                .order("market_cap", desc=True) \
                .limit(limit) \
                .execute()
                
            if hasattr(response, 'data'):
                return response.data
            return []
        except Exception as e:
            logger.error(f"Error al obtener tokens candidatos: {str(e)}")
            return []
    
    def update_token_candidates(self, tokens: List[Dict]) -> bool:
        """
        Actualiza la lista de tokens candidatos
        
        Args:
            tokens: Lista de tokens a actualizar
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            # Añadir timestamp de actualización a cada token
            for token in tokens:
                token["fecha_actualizacion"] = datetime.now().isoformat()
            
            response = self.client.table("token_candidatos") \
                .upsert(tokens) \
                .execute()
                
            return hasattr(response, 'data') and len(response.data) > 0
        except Exception as e:
            logger.error(f"Error al actualizar tokens candidatos: {str(e)}")
            return False

class FileSystemLogRepository:
    """
    Repositorio para acceder a logs del sistema almacenados en archivos
    """
    
    def __init__(self, log_dir: Path):
        """
        Inicializa el repositorio
        
        Args:
            log_dir: Directorio de logs
        """
        self.log_dir = log_dir
    
    def get_logs(self, component: str, lines: int = 50) -> List[str]:
        """
        Obtiene las últimas líneas de log de un componente
        
        Args:
            component: Nombre del componente
            lines: Número de líneas a obtener
            
        Returns:
            List[str]: Líneas de log
        """
        try:
            # Obtener ruta del archivo de log
            log_file = self._get_log_file_path(component)
            
            if not log_file.exists():
                logger.warning(f"Archivo de log no encontrado: {log_file}")
                return []
            
            # Leer las últimas líneas del archivo
            return self._read_last_lines(log_file, lines)
        except Exception as e:
            logger.error(f"Error al obtener logs: {str(e)}")
            return []
    
    def _get_log_file_path(self, component: str) -> Path:
        """
        Obtiene la ruta del archivo de log de un componente
        
        Args:
            component: Nombre del componente
            
        Returns:
            Path: Ruta del archivo de log
        """
        # Mapeo de componentes a archivos de log
        component_logs = {
            "system": "system.log",
            "detector": "detector.log",
            "executor": "executor.log",
            "api_server": "api_server.log",
            "telegram_bot": "telegram_bot.log",
            "dashboard": "dashboard.log"
        }
        
        log_file = component_logs.get(component, f"{component}.log")
        return self.log_dir / log_file
    
    def _read_last_lines(self, file_path: Path, lines: int) -> List[str]:
        """
        Lee las últimas líneas de un archivo
        
        Args:
            file_path: Ruta del archivo
            lines: Número de líneas a leer
            
        Returns:
            List[str]: Líneas leídas
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Leer todo el archivo y dividir en líneas
                all_lines = file.readlines()
                
                # Devolver las últimas 'lines' líneas
                return [line.rstrip() for line in all_lines[-lines:]]
        except Exception as e:
            logger.error(f"Error al leer archivo {file_path}: {str(e)}")
            return []
    
    def search_logs(self, component: str, pattern: str, days: int = 7) -> List[str]:
        """
        Busca líneas en los logs que coincidan con un patrón
        
        Args:
            component: Nombre del componente
            pattern: Patrón de búsqueda (regex)
            days: Días atrás para buscar
            
        Returns:
            List[str]: Líneas que coinciden con el patrón
        """
        try:
            # Obtener ruta del archivo de log
            log_file = self._get_log_file_path(component)
            
            if not log_file.exists():
                logger.warning(f"Archivo de log no encontrado: {log_file}")
                return []
            
            # Compilar patrón regex
            regex = re.compile(pattern)
            
            # Calcular fecha límite
            limit_date = datetime.now() - timedelta(days=days)
            limit_date_str = limit_date.strftime("%Y-%m-%d")
            
            # Buscar en el archivo
            matching_lines = []
            
            with open(log_file, 'r', encoding='utf-8') as file:
                for line in file:
                    # Verificar si la línea contiene la fecha límite o posterior
                    if limit_date_str in line:
                        # Si llegamos a la fecha límite, comenzar a buscar el patrón
                        break
                
                # Continuar leyendo y buscar el patrón
                for line in file:
                    if regex.search(line):
                        matching_lines.append(line.rstrip())
            
            return matching_lines
        except Exception as e:
            logger.error(f"Error al buscar en logs: {str(e)}")
            return []