"""
Implementaciones de repositorios utilizando el sistema de archivos local.
Siguiendo el principio SRP: Cada repositorio tiene una única responsabilidad.
"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.dashboard.repositories.repository_interface import Repository

logger = logging.getLogger(__name__)

class FileSystemLogRepository(Repository):
    """
    Repositorio para acceder a logs almacenados en sistema de archivos.
    Aplica el principio SRP al tener la única responsabilidad de gestionar logs.
    """
    
    def __init__(self, log_dir: Path):
        """
        Inicializa el repositorio de logs.
        
        Args:
            log_dir (Path): Directorio donde se encuentran los archivos de log
        """
        self.log_dir = log_dir
        logger.info(f"FileSystemLogRepository inicializado con directorio: {log_dir}")
    
    def get_all(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los archivos de log y los datos básicos.
        
        Returns:
            List[Dict[str, Any]]: Lista de metadatos de logs
        """
        result = []
        
        try:
            if not self.log_dir.exists():
                logger.warning(f"El directorio de logs no existe: {self.log_dir}")
                return []
            
            for file in self.log_dir.glob("*.log"):
                stats = file.stat()
                result.append({
                    "filename": file.name,
                    "path": str(file),
                    "size": stats.st_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime),
                    "created": datetime.fromtimestamp(stats.st_ctime)
                })
            
            # Ordenar por fecha de modificación (más reciente primero)
            result.sort(key=lambda x: x["modified"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error al obtener los logs: {str(e)}")
        
        return result
    
    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el contenido de un archivo de log por su nombre.
        
        Args:
            id (str): Nombre del archivo de log
            
        Returns:
            Optional[Dict[str, Any]]: Datos del log o None si no existe
        """
        try:
            file_path = self.log_dir / id
            
            if not file_path.exists() or not file_path.is_file():
                logger.warning(f"Archivo de log no encontrado: {file_path}")
                return None
            
            stats = file_path.stat()
            content = file_path.read_text(encoding='utf-8')
            
            return {
                "filename": file_path.name,
                "path": str(file_path),
                "content": content,
                "size": stats.st_size,
                "modified": datetime.fromtimestamp(stats.st_mtime),
                "created": datetime.fromtimestamp(stats.st_ctime)
            }
            
        except Exception as e:
            logger.error(f"Error al leer el archivo de log {id}: {str(e)}")
            return None
    
    def get_recent_logs(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Obtiene los logs de los últimos X días.
        
        Args:
            days (int): Número de días a filtrar
            
        Returns:
            List[Dict[str, Any]]: Lista de metadatos de logs recientes
        """
        all_logs = self.get_all()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return [log for log in all_logs if log["modified"] >= cutoff_date]
    
    def get_log_content(self, filename: str, max_lines: int = 1000) -> List[str]:
        """
        Obtiene el contenido de un archivo de log limitado a un número de líneas.
        
        Args:
            filename (str): Nombre del archivo
            max_lines (int): Número máximo de líneas a devolver
            
        Returns:
            List[str]: Líneas del archivo de log
        """
        try:
            file_path = self.log_dir / filename
            
            if not file_path.exists() or not file_path.is_file():
                logger.warning(f"Archivo de log no encontrado: {file_path}")
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Si hay más líneas que el máximo, tomar las últimas (más recientes)
            if len(lines) > max_lines:
                lines = lines[-max_lines:]
            
            return lines
            
        except Exception as e:
            logger.error(f"Error al leer el contenido del log {filename}: {str(e)}")
            return []
    
    # Métodos necesarios para implementar la interfaz Repository pero que no aplicamos para logs
    def create(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        logger.warning("Método create no implementado para FileSystemLogRepository")
        return None
    
    def update(self, id: str, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        logger.warning("Método update no implementado para FileSystemLogRepository")
        return None
    
    def delete(self, id: str) -> bool:
        logger.warning("Método delete no implementado para FileSystemLogRepository")
        return False
