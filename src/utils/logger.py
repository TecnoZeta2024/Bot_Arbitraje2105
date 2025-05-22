"""
Módulo de logging para el Bot de Arbitraje Triangular.
Proporciona funciones para el registro de eventos y errores.
"""

import logging
import os
import sys
import io
from datetime import datetime
from typing import Optional

# Configuración básica de logging
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
LOG_DIR = 'logs'

# Asegurar que el directorio de logs existe
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Fecha para el nombre del archivo
date_str = datetime.now().strftime('%Y-%m-%d')

class UTF8StreamHandler(logging.StreamHandler):
    """
    Personalización de StreamHandler para asegurar 
    que se use codificación UTF-8 en la salida a consola
    """
    def __init__(self):
        # Usar una clase BytesIO para manejar la salida
        buffer = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        super().__init__(buffer)
        
class BotLogger:
    """
    Clase para gestionar logs del sistema.
    Permite crear diferentes loggers para distintos componentes del bot.
    """
    
    def __init__(self, name: str, level: int = LOG_LEVEL):
        """
        Inicializa un nuevo logger.
        
        Args:
            name: Nombre del componente (ej: 'filtrado', 'deteccion', 'ejecucion').
            level: Nivel de logging (default: logging.INFO).
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Evitar duplicación de handlers si el logger ya existe
        if not self.logger.handlers:
            self._setup_handlers(name)
    
    def _setup_handlers(self, name: str):
        """Configura los handlers para el logger."""
        # Handler para la consola con soporte UTF-8
        console_handler = UTF8StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        console_handler.setLevel(self.logger.level)
        self.logger.addHandler(console_handler)
        
        # Handler para archivo
        file_handler = logging.FileHandler(
            os.path.join(LOG_DIR, f'{name}_{date_str}.log'),
            encoding='utf-8'  # Especificar codificación UTF-8 para el archivo
        )
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        file_handler.setLevel(self.logger.level)
        self.logger.addHandler(file_handler)
    
    def debug(self, msg: str):
        """Registra un mensaje de nivel DEBUG."""
        self.logger.debug(msg)
    
    def info(self, msg: str):
        """Registra un mensaje de nivel INFO."""
        self.logger.info(msg)
    
    def warning(self, msg: str):
        """Registra un mensaje de nivel WARNING."""
        self.logger.warning(msg)
    
    def error(self, msg: str, exc_info: Optional[Exception] = None):
        """
        Registra un mensaje de nivel ERROR.
        
        Args:
            msg: Mensaje de error.
            exc_info: Excepción para incluir el traceback (opcional).
        """
        self.logger.error(msg, exc_info=exc_info)
    
    def critical(self, msg: str, exc_info: Optional[Exception] = None):
        """
        Registra un mensaje de nivel CRITICAL.
        
        Args:
            msg: Mensaje crítico.
            exc_info: Excepción para incluir el traceback (opcional).
        """
        self.logger.critical(msg, exc_info=exc_info)

# Función de ayuda para obtener un logger específico
def get_logger(name: str) -> BotLogger:
    """
    Obtiene un logger para un componente específico.
    
    Args:
        name: Nombre del componente.
        
    Returns:
        Un logger configurado.
    """
    return BotLogger(name)

# Setup básico para el logging
def setup_logger(name: str, log_level: int = LOG_LEVEL, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configura un logger con formato estándar
    
    Args:
        name: Nombre para el logger
        log_level: Nivel de logging (default: logging.INFO)
        log_file: Ruta al archivo de log (opcional)
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Evitar duplicar handlers
    if not logger.handlers:
        # Configurar handler de consola
        console_handler = UTF8StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)
        
        # Configurar handler de archivo si se especifica
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
            logger.addHandler(file_handler)
    
    return logger

# Loggers predefinidos para componentes principales
filtrado_logger = get_logger('filtrado')
deteccion_logger = get_logger('deteccion')
ejecucion_logger = get_logger('ejecucion')
api_logger = get_logger('api')
