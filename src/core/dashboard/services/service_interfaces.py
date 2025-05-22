"""
Interface para servicios.
Siguiendo el principio de inversión de dependencias (DIP), definimos interfaces
para los servicios que utilizará el dashboard.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Generic, TypeVar
from datetime import datetime

from src.core.dashboard.models.token_model import Token
from src.core.dashboard.models.operation_model import ArbitrageOperation
from src.core.dashboard.models.config_model import SystemConfig
from src.core.dashboard.models.user_model import User, UserCredentials

class AuthService(ABC):
    """Interfaz para servicio de autenticación"""
    
    @abstractmethod
    def login(self, credentials: UserCredentials) -> Optional[User]:
        """
        Autentica un usuario
        
        Args:
            credentials: Credenciales del usuario
            
        Returns:
            Optional[User]: Usuario autenticado o None si la autenticación falló
        """
        pass
    
    @abstractmethod
    def logout(self, user_id: str) -> bool:
        """
        Cierra la sesión de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            bool: True si el cierre de sesión fue exitoso, False en caso contrario
        """
        pass
    
    @abstractmethod
    def get_current_user(self) -> Optional[User]:
        """
        Obtiene el usuario actualmente autenticado
        
        Returns:
            Optional[User]: Usuario actual o None si no hay sesión activa
        """
        pass
    
    @abstractmethod
    def check_permission(self, user_id: str, required_role: str) -> bool:
        """
        Verifica si un usuario tiene el rol requerido
        
        Args:
            user_id: ID del usuario
            required_role: Rol requerido
            
        Returns:
            bool: True si el usuario tiene el rol requerido, False en caso contrario
        """
        pass

class ConfigService(ABC):
    """Interfaz para servicio de configuración"""
    
    @abstractmethod
    def get_system_config(self) -> SystemConfig:
        """
        Obtiene la configuración actual del sistema
        
        Returns:
            SystemConfig: Configuración actual del sistema
        """
        pass
    
    @abstractmethod
    def update_system_config(self, config: SystemConfig) -> bool:
        """
        Actualiza la configuración del sistema
        
        Args:
            config: Nueva configuración
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        pass
    
    @abstractmethod
    def get_config_section(self, section_name: str) -> Dict[str, Any]:
        """
        Obtiene una sección específica de la configuración
        
        Args:
            section_name: Nombre de la sección
            
        Returns:
            Dict[str, Any]: Datos de la sección de configuración
        """
        pass
    
    @abstractmethod
    def update_config_section(self, section_name: str, section_data: Dict[str, Any]) -> bool:
        """
        Actualiza una sección específica de la configuración
        
        Args:
            section_name: Nombre de la sección
            section_data: Nuevos datos para la sección
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        pass
    
    @abstractmethod
    def validate_webhooks(self) -> Dict[str, bool]:
        """
        Valida la conexión con los webhooks configurados
        
        Returns:
            Dict[str, bool]: Estado de validación de cada webhook
        """
        pass
    
    @abstractmethod
    def reload_config(self) -> bool:
        """
        Recarga la configuración del sistema desde la base de datos
        
        Returns:
            bool: True si la recarga fue exitosa, False en caso contrario
        """
        pass

class TokenService(ABC):
    """Interfaz para servicio de tokens"""
    
    @abstractmethod
    def get_all_tokens(self, limit: int = 100) -> List[Token]:
        """
        Obtiene todos los tokens
        
        Args:
            limit: Número máximo de tokens a obtener
            
        Returns:
            List[Token]: Lista de tokens
        """
        pass
    
    @abstractmethod
    def search_tokens(self, query: str, limit: int = 20) -> List[Token]:
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
    def get_token_by_symbol(self, symbol: str) -> Optional[Token]:
        """
        Obtiene un token por su símbolo
        
        Args:
            symbol: Símbolo del token
            
        Returns:
            Optional[Token]: Token encontrado o None si no existe
        """
        pass
    
    @abstractmethod
    def update_tokens(self, tokens: List[Token]) -> bool:
        """
        Actualiza múltiples tokens
        
        Args:
            tokens: Lista de tokens a actualizar
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        pass
    
    @abstractmethod
    def filter_tokens(self, min_market_cap: float = 0, min_volume: float = 0, max_tokens: int = 100) -> List[Token]:
        """
        Filtra tokens según criterios
        
        Args:
            min_market_cap: Capitalización de mercado mínima
            min_volume: Volumen mínimo en 24h
            max_tokens: Número máximo de tokens a retornar
            
        Returns:
            List[Token]: Lista de tokens filtrados
        """
        pass
    
    @abstractmethod
    def get_token_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de los tokens
        
        Returns:
            Dict[str, Any]: Estadísticas de tokens (total, promedio de market cap, etc.)
        """
        pass

class OperationService(ABC):
    """Interfaz para servicio de operaciones"""
    
    @abstractmethod
    def get_recent_operations(self, limit: int = 10) -> List[ArbitrageOperation]:
        """
        Obtiene las operaciones más recientes
        
        Args:
            limit: Número máximo de operaciones
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones recientes
        """
        pass
    
    @abstractmethod
    def get_operation_by_id(self, operation_id: str) -> Optional[ArbitrageOperation]:
        """
        Obtiene una operación por su ID
        
        Args:
            operation_id: ID de la operación
            
        Returns:
            Optional[ArbitrageOperation]: Operación encontrada o None si no existe
        """
        pass
    
    @abstractmethod
    def get_operations_by_status(self, status: str, limit: int = 100) -> List[ArbitrageOperation]:
        """
        Obtiene operaciones según su estado
        
        Args:
            status: Estado de las operaciones
            limit: Número máximo de operaciones
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones con el estado especificado
        """
        pass
    
    @abstractmethod
    def get_operations_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ArbitrageOperation]:
        """
        Obtiene operaciones en un rango de fechas
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones en el rango de fechas
        """
        pass
    
    @abstractmethod
    def calculate_performance_metrics(self, operations: Optional[List[ArbitrageOperation]] = None) -> Dict[str, Any]:
        """
        Calcula métricas de rendimiento
        
        Args:
            operations: Lista de operaciones (si None, se utilizan todas las operaciones)
            
        Returns:
            Dict[str, Any]: Métricas de rendimiento
        """
        pass
    
    @abstractmethod
    def get_best_routes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Obtiene las mejores rutas según rentabilidad
        
        Args:
            limit: Número máximo de rutas
            
        Returns:
            List[Dict[str, Any]]: Lista de mejores rutas con métricas
        """
        pass
    
    @abstractmethod
    def get_operation_history_by_day(self, days: int = 30) -> Dict[str, Any]:
        """
        Obtiene el historial de operaciones agrupado por día
        
        Args:
            days: Número de días a considerar
            
        Returns:
            Dict[str, Any]: Historial de operaciones
        """
        pass

class NotificationService(ABC):
    """Interfaz para servicio de notificaciones"""
    
    @abstractmethod
    def send_telegram_message(self, message: str) -> bool:
        """
        Envía un mensaje por Telegram
        
        Args:
            message: Mensaje a enviar
            
        Returns:
            bool: True si el envío fue exitoso, False en caso contrario
        """
        pass
    
    @abstractmethod
    def send_test_notification(self, channel: str, message: str) -> bool:
        """
        Envía una notificación de prueba
        
        Args:
            channel: Canal de notificación (telegram, email, etc.)
            message: Mensaje a enviar
            
        Returns:
            bool: True si el envío fue exitoso, False en caso contrario
        """
        pass
    
    @abstractmethod
    def get_notification_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado de las notificaciones
        
        Returns:
            Dict[str, Any]: Estado de cada canal de notificación
        """
        pass

class SystemMonitorService(ABC):
    """Interfaz para servicio de monitoreo del sistema"""
    
    @abstractmethod
    def get_system_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del sistema
        
        Returns:
            Dict[str, Any]: Estado del sistema (CPU, memoria, etc.)
        """
        pass
    
    @abstractmethod
    def check_processes(self) -> Dict[str, str]:
        """
        Verifica el estado de los procesos del sistema
        
        Returns:
            Dict[str, str]: Estado de cada proceso
        """
        pass
    
    @abstractmethod
    def restart_process(self, process_name: str) -> bool:
        """
        Reinicia un proceso específico
        
        Args:
            process_name: Nombre del proceso
            
        Returns:
            bool: True si el reinicio fue exitoso, False en caso contrario
        """
        pass
    
    @abstractmethod
    def get_logs(self, component: str, lines: int = 100) -> List[str]:
        """
        Obtiene los logs de un componente específico
        
        Args:
            component: Nombre del componente
            lines: Número máximo de líneas
            
        Returns:
            List[str]: Lista de líneas de log
        """
        pass
