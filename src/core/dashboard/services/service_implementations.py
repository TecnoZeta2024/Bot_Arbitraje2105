"""
Implementaciones concretas de servicios.
"""

import os
import json
import logging
import psutil
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
import streamlit as st

from src.core.dashboard.services.service_interfaces import (
    AuthService,
    ConfigService,
    TokenService,
    OperationService,
    NotificationService,
    SystemMonitorService
)

from src.core.dashboard.repositories import (
    TokenRepository,
    OperationRepository,
    ConfigRepository,
    SupabaseTokenRepository,
    SupabaseOperationRepository,
    SupabaseConfigRepository
)

from src.core.dashboard.models import (
    Token,
    ArbitrageOperation,
    SystemConfig,
    User,
    UserCredentials
)

from src.utils.config import settings

# Configurar logging
logger = logging.getLogger(__name__)

class SupabaseAuthService(AuthService):
    """Implementación de servicio de autenticación utilizando Supabase"""
    
    def login(self, credentials: UserCredentials) -> Optional[User]:
        """
        Autentica un usuario
        
        Args:
            credentials: Credenciales del usuario
            
        Returns:
            Optional[User]: Usuario autenticado o None si la autenticación falló
        """
        try:
            # Obtener cliente de Supabase
            from src.core.dashboard.repositories.supabase_repositories import get_supabase_client
            supabase = get_supabase_client()
            
            # Autenticar usuario
            response = supabase.auth.sign_in_with_password({
                "email": credentials.email,
                "password": credentials.password
            })
            
            if response.user:
                # Crear objeto de usuario
                user = User(
                    id=response.user.id,
                    email=response.user.email,
                    role="admin" if credentials.email.endswith("@admin.com") else "user",
                    name=response.user.user_metadata.get("name") if hasattr(response.user, "user_metadata") else None,
                    created_at=datetime.fromisoformat(response.user.created_at) if hasattr(response.user, "created_at") else None
                )
                
                # Guardar en sesión de Streamlit
                if "user" not in st.session_state:
                    st.session_state.user = user.to_dict()
                
                return user
            
            return None
        except Exception as e:
            logger.error(f"Error de autenticación: {str(e)}")
            return None
    
    def logout(self, user_id: str) -> bool:
        """
        Cierra la sesión de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            bool: True si el cierre de sesión fue exitoso, False en caso contrario
        """
        try:
            # Obtener cliente de Supabase
            from src.core.dashboard.repositories.supabase_repositories import get_supabase_client
            supabase = get_supabase_client()
            
            # Cerrar sesión
            supabase.auth.sign_out()
            
            # Limpiar sesión de Streamlit
            if "user" in st.session_state:
                del st.session_state.user
            
            if "authenticated" in st.session_state:
                st.session_state.authenticated = False
            
            return True
        except Exception as e:
            logger.error(f"Error al cerrar sesión: {str(e)}")
            return False
    
    def get_current_user(self) -> Optional[User]:
        """
        Obtiene el usuario actualmente autenticado
        
        Returns:
            Optional[User]: Usuario actual o None si no hay sesión activa
        """
        try:
            if "user" in st.session_state:
                user_data = st.session_state.user
                if isinstance(user_data, dict):
                    return User.from_dict(user_data)
            
            # Si no hay usuario en la sesión, intentar obtenerlo de Supabase
            from src.core.dashboard.repositories.supabase_repositories import get_supabase_client
            supabase = get_supabase_client()
            
            response = supabase.auth.get_user()
            if response.user:
                user = User(
                    id=response.user.id,
                    email=response.user.email,
                    role="admin" if response.user.email.endswith("@admin.com") else "user",
                    name=response.user.user_metadata.get("name") if hasattr(response.user, "user_metadata") else None,
                    created_at=datetime.fromisoformat(response.user.created_at) if hasattr(response.user, "created_at") else None
                )
                
                # Actualizar sesión
                st.session_state.user = user.to_dict()
                st.session_state.authenticated = True
                
                return user
            
            return None
        except Exception as e:
            logger.error(f"Error al obtener usuario actual: {str(e)}")
            return None
    
    def check_permission(self, user_id: str, required_role: str) -> bool:
        """
        Verifica si un usuario tiene el rol requerido
        
        Args:
            user_id: ID del usuario
            required_role: Rol requerido
            
        Returns:
            bool: True si el usuario tiene el rol requerido, False en caso contrario
        """
        try:
            user = self.get_current_user()
            if not user:
                return False
            
            # Verificar si el ID coincide
            if user.id != user_id:
                return False
            
            return user.has_permission(required_role)
        except Exception as e:
            logger.error(f"Error al verificar permisos: {str(e)}")
            return False

class DefaultConfigService(ConfigService):
    """Implementación predeterminada del servicio de configuración"""
    
    def __init__(self, repository: Optional[ConfigRepository] = None):
        """
        Inicializa el servicio
        
        Args:
            repository: Repositorio de configuración
        """
        self.repository = repository or SupabaseConfigRepository()
        self._config_cache = None
    
    def get_system_config(self) -> SystemConfig:
        """
        Obtiene la configuración actual del sistema
        
        Returns:
            SystemConfig: Configuración actual del sistema
        """
        if self._config_cache is None:
            config = self.repository.get_current_config()
            if not config:
                # Si no hay configuración, crear una por defecto
                config = SystemConfig()
                
                # Inicializar con valores de settings
                config.webhooks.opportunity_webhook = settings.n8n_webhook_oportunidad
                config.webhooks.result_webhook = settings.n8n_webhook_resultado
                config.webhooks.decision_webhook = settings.n8n_webhook_decision
                
                # Guardar configuración por defecto
                self.repository.save_config(config)
            
            self._config_cache = config
        
        return self._config_cache
    
    def update_system_config(self, config: SystemConfig) -> bool:
        """
        Actualiza la configuración del sistema
        
        Args:
            config: Nueva configuración
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        result = self.repository.save_config(config)
        if result:
            # Actualizar caché
            self._config_cache = config
        return result
    
    def get_config_section(self, section_name: str) -> Dict[str, Any]:
        """
        Obtiene una sección específica de la configuración
        
        Args:
            section_name: Nombre de la sección
            
        Returns:
            Dict[str, Any]: Datos de la sección de configuración
        """
        config = self.get_system_config()
        
        # Obtener la sección
        section = getattr(config, section_name, None)
        if section:
            return section.dict()
        
        return {}
    
    def update_config_section(self, section_name: str, section_data: Dict[str, Any]) -> bool:
        """
        Actualiza una sección específica de la configuración
        
        Args:
            section_name: Nombre de la sección
            section_data: Nuevos datos para la sección
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        config = self.get_system_config()
        
        # Obtener la sección
        section = getattr(config, section_name, None)
        if not section:
            return False
        
        # Actualizar la sección
        for key, value in section_data.items():
            if hasattr(section, key):
                setattr(section, key, value)
        
        # Guardar la configuración
        return self.update_system_config(config)
    
    def validate_webhooks(self) -> Dict[str, bool]:
        """
        Valida la conexión con los webhooks configurados
        
        Returns:
            Dict[str, bool]: Estado de validación de cada webhook
        """
        config = self.get_system_config()
        results = {}
        
        # Verificar webhook de oportunidad
        opportunity_webhook = config.webhooks.opportunity_webhook
        if opportunity_webhook:
            try:
                # Hacer una solicitud HEAD para verificar que el endpoint existe
                response = requests.head(opportunity_webhook, timeout=5)
                results["opportunity_webhook"] = response.status_code < 400
            except Exception:
                results["opportunity_webhook"] = False
        else:
            results["opportunity_webhook"] = False
        
        # Verificar webhook de resultado
        result_webhook = config.webhooks.result_webhook
        if result_webhook:
            try:
                response = requests.head(result_webhook, timeout=5)
                results["result_webhook"] = response.status_code < 400
            except Exception:
                results["result_webhook"] = False
        else:
            results["result_webhook"] = False
        
        # Verificar webhook de decisión
        decision_webhook = config.webhooks.decision_webhook
        if decision_webhook:
            try:
                response = requests.head(decision_webhook, timeout=5)
                results["decision_webhook"] = response.status_code < 400
            except Exception:
                results["decision_webhook"] = False
        else:
            results["decision_webhook"] = False
        
        return results
    
    def reload_config(self) -> bool:
        """
        Recarga la configuración del sistema desde la base de datos
        
        Returns:
            bool: True si la recarga fue exitosa, False en caso contrario
        """
        try:
            # Limpiar caché
            self._config_cache = None
            
            # Obtener configuración nuevamente
            self.get_system_config()
            
            return True
        except Exception as e:
            logger.error(f"Error al recargar configuración: {str(e)}")
            return False

class DefaultTokenService(TokenService):
    """Implementación predeterminada del servicio de tokens"""
    
    def __init__(self, repository: Optional[TokenRepository] = None):
        """
        Inicializa el servicio
        
        Args:
            repository: Repositorio de tokens
        """
        self.repository = repository or SupabaseTokenRepository()
    
    def get_all_tokens(self, limit: int = 100) -> List[Token]:
        """
        Obtiene todos los tokens
        
        Args:
            limit: Número máximo de tokens a obtener
            
        Returns:
            List[Token]: Lista de tokens
        """
        return self.repository.get_all(limit=limit)
    
    def search_tokens(self, query: str, limit: int = 20) -> List[Token]:
        """
        Busca tokens por coincidencia parcial en el símbolo
        
        Args:
            query: Texto a buscar
            limit: Número máximo de resultados
            
        Returns:
            List[Token]: Lista de tokens que coinciden con la búsqueda
        """
        return self.repository.search_by_symbol(query, limit=limit)
    
    def get_token_by_symbol(self, symbol: str) -> Optional[Token]:
        """
        Obtiene un token por su símbolo
        
        Args:
            symbol: Símbolo del token
            
        Returns:
            Optional[Token]: Token encontrado o None si no existe
        """
        return self.repository.get_by_symbol(symbol)
    
    def update_tokens(self, tokens: List[Token]) -> bool:
        """
        Actualiza múltiples tokens
        
        Args:
            tokens: Lista de tokens a actualizar
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        return self.repository.update_multiple(tokens)
    
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
        return self.repository.get_tokens_by_criteria(
            min_market_cap=min_market_cap, 
            min_volume=min_volume,
            limit=max_tokens
        )
    
    def get_token_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de los tokens
        
        Returns:
            Dict[str, Any]: Estadísticas de tokens (total, promedio de market cap, etc.)
        """
        tokens = self.get_all_tokens(limit=1000)
        
        if not tokens:
            return {
                "total": 0,
                "avg_market_cap": 0,
                "avg_volume": 0,
                "max_market_cap": 0,
                "min_market_cap": 0,
                "top_volume_tokens": [],
                "top_market_cap_tokens": []
            }
        
        # Convertir a DataFrame para análisis
        tokens_data = [token.to_dict() for token in tokens]
        df = pd.DataFrame(tokens_data)
        
        # Calcular estadísticas
        stats = {
            "total": len(tokens),
            "avg_market_cap": df.get("market_cap", pd.Series()).mean() if "market_cap" in df else 0,
            "avg_volume": df.get("volumen_binance_24h", pd.Series()).mean() if "volumen_binance_24h" in df else 0,
            "max_market_cap": df.get("market_cap", pd.Series()).max() if "market_cap" in df else 0,
            "min_market_cap": df.get("market_cap", pd.Series()).min() if "market_cap" in df else 0,
        }
        
        # Top tokens por volumen
        if "volumen_binance_24h" in df and "simbolo" in df:
            top_volume = df.nlargest(5, "volumen_binance_24h")[["simbolo", "volumen_binance_24h"]]
            stats["top_volume_tokens"] = top_volume.to_dict("records")
        else:
            stats["top_volume_tokens"] = []
        
        # Top tokens por market cap
        if "market_cap" in df and "simbolo" in df:
            top_market_cap = df.nlargest(5, "market_cap")[["simbolo", "market_cap"]]
            stats["top_market_cap_tokens"] = top_market_cap.to_dict("records")
        else:
            stats["top_market_cap_tokens"] = []
        
        return stats

class DefaultOperationService(OperationService):
    """Implementación predeterminada del servicio de operaciones"""
    
    def __init__(self, repository: Optional[OperationRepository] = None):
        """
        Inicializa el servicio
        
        Args:
            repository: Repositorio de operaciones
        """
        self.repository = repository or SupabaseOperationRepository()
    
    def get_recent_operations(self, limit: int = 10) -> List[ArbitrageOperation]:
        """
        Obtiene las operaciones más recientes
        
        Args:
            limit: Número máximo de operaciones
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones recientes
        """
        return self.repository.get_recent_operations(limit=limit)
    
    def get_operation_by_id(self, operation_id: str) -> Optional[ArbitrageOperation]:
        """
        Obtiene una operación por su ID
        
        Args:
            operation_id: ID de la operación
            
        Returns:
            Optional[ArbitrageOperation]: Operación encontrada o None si no existe
        """
        return self.repository.get_by_operation_id(operation_id)
    
    def get_operations_by_status(self, status: str, limit: int = 100) -> List[ArbitrageOperation]:
        """
        Obtiene operaciones según su estado
        
        Args:
            status: Estado de las operaciones
            limit: Número máximo de operaciones
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones con el estado especificado
        """
        return self.repository.get_by_status(status, limit=limit)
    
    def get_operations_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ArbitrageOperation]:
        """
        Obtiene operaciones en un rango de fechas
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            List[ArbitrageOperation]: Lista de operaciones en el rango de fechas
        """
        return self.repository.get_operations_by_date_range(start_date, end_date)
    
    def calculate_performance_metrics(self, operations: Optional[List[ArbitrageOperation]] = None) -> Dict[str, Any]:
        """
        Calcula métricas de rendimiento
        
        Args:
            operations: Lista de operaciones (si None, se utilizan las operaciones de los últimos 30 días)
            
        Returns:
            Dict[str, Any]: Métricas de rendimiento
        """
        if operations is None:
            # Obtener operaciones de los últimos 30 días
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            operations = self.get_operations_by_date_range(start_date, end_date)
        
        if not operations:
            return {
                "total_operations": 0,
                "successful_operations": 0,
                "failed_operations": 0,
                "success_rate": 0,
                "total_profit": 0,
                "average_roi": 0,
                "best_roi": 0,
                "worst_roi": 0,
                "total_fees": 0,
                "average_slippage": 0,
                "total_volume": 0
            }
        
        # Filtrar operaciones completadas
        completed_operations = [op for op in operations if op.status == "COMPLETADO"]
        failed_operations = [op for op in operations if op.status == "FALLIDO"]
        
        # Calcular métricas
        metrics = {
            "total_operations": len(operations),
            "successful_operations": len(completed_operations),
            "failed_operations": len(failed_operations),
            "success_rate": len(completed_operations) / len(operations) if operations else 0,
        }
        
        # Métricas de rentabilidad
        if completed_operations:
            metrics["total_profit"] = sum(op.net_profit or 0 for op in completed_operations)
            metrics["average_roi"] = sum(op.real_roi or 0 for op in completed_operations) / len(completed_operations)
            metrics["best_roi"] = max((op.real_roi or 0) for op in completed_operations)
            metrics["worst_roi"] = min((op.real_roi or 0) for op in completed_operations)
            metrics["total_fees"] = sum(op.total_fees or 0 for op in completed_operations)
            metrics["average_slippage"] = sum(op.real_slippage or 0 for op in completed_operations) / len(completed_operations)
            metrics["total_volume"] = sum(op.initial_capital or 0 for op in completed_operations)
        else:
            metrics.update({
                "total_profit": 0,
                "average_roi": 0,
                "best_roi": 0,
                "worst_roi": 0,
                "total_fees": 0,
                "average_slippage": 0,
                "total_volume": 0
            })
        
        return metrics
    
    def get_best_routes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Obtiene las mejores rutas según rentabilidad
        
        Args:
            limit: Número máximo de rutas
            
        Returns:
            List[Dict[str, Any]]: Lista de mejores rutas con métricas
        """
        # Obtener todas las operaciones completadas
        operations = self.repository.get_by_status("COMPLETADO", limit=1000)
        
        if not operations:
            return []
        
        # Agrupar por ruta
        routes = {}
        for op in operations:
            route_str = op.route.route
            if route_str not in routes:
                routes[route_str] = {
                    "route": route_str,
                    "operations": [],
                    "total_profit": 0,
                    "average_roi": 0,
                    "total_volume": 0,
                    "success_count": 0
                }
            
            # Añadir operación a la ruta
            routes[route_str]["operations"].append(op)
            routes[route_str]["total_profit"] += op.net_profit or 0
            routes[route_str]["total_volume"] += op.initial_capital or 0
            routes[route_str]["success_count"] += 1
        
        # Calcular métricas promedio
        for route in routes.values():
            if route["operations"]:
                route["average_roi"] = sum(op.real_roi or 0 for op in route["operations"]) / len(route["operations"])
        
        # Ordenar por rentabilidad promedio
        best_routes = sorted(
            routes.values(), 
            key=lambda x: x["average_roi"], 
            reverse=True
        )[:limit]
        
        # Limpiar para devolver
        for route in best_routes:
            del route["operations"]
        
        return best_routes
    
    def get_operation_history_by_day(self, days: int = 30) -> Dict[str, Any]:
        """
        Obtiene el historial de operaciones agrupado por día
        
        Args:
            days: Número de días a considerar
            
        Returns:
            Dict[str, Any]: Historial de operaciones
        """
        # Obtener operaciones en el rango de fechas
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        operations = self.get_operations_by_date_range(start_date, end_date)
        
        if not operations:
            return {
                "dates": [],
                "profits": [],
                "volumes": [],
                "counts": [],
                "cumulative_profit": []
            }
        
        # Preparar DataFrame para análisis
        data = []
        for op in operations:
            if op.execution_start_time and op.status == "COMPLETADO":
                data.append({
                    "date": op.execution_start_time.date(),
                    "profit": op.net_profit or 0,
                    "volume": op.initial_capital or 0,
                    "status": op.status
                })
        
        if not data:
            return {
                "dates": [],
                "profits": [],
                "volumes": [],
                "counts": [],
                "cumulative_profit": []
            }
        
        df = pd.DataFrame(data)
        
        # Agrupar por día
        daily = df.groupby("date").agg({
            "profit": "sum",
            "volume": "sum",
            "status": "count"
        }).reset_index()
        
        # Calcular beneficio acumulado
        daily["cumulative_profit"] = daily["profit"].cumsum()
        
        # Convertir a listas para la respuesta
        result = {
            "dates": [d.strftime("%Y-%m-%d") for d in daily["date"]],
            "profits": daily["profit"].tolist(),
            "volumes": daily["volume"].tolist(),
            "counts": daily["status"].tolist(),
            "cumulative_profit": daily["cumulative_profit"].tolist()
        }
        
        return result

class DefaultNotificationService(NotificationService):
    """Implementación predeterminada del servicio de notificaciones"""
    
    def __init__(self, config_service: Optional[ConfigService] = None):
        """
        Inicializa el servicio
        
        Args:
            config_service: Servicio de configuración
        """
        self.config_service = config_service or DefaultConfigService()
    
    def send_telegram_message(self, message: str) -> bool:
        """
        Envía un mensaje por Telegram
        
        Args:
            message: Mensaje a enviar
            
        Returns:
            bool: True si el envío fue exitoso, False en caso contrario
        """
        try:
            # Obtener token y chat_id de las configuraciones
            token = settings.telegram_bot_token
            chat_id = settings.telegram_chat_id
            
            if not token or not chat_id:
                logger.error("No se encontraron credenciales de Telegram")
                return False
            
            # Construir URL de la API de Telegram
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            
            # Enviar mensaje
            response = requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
            
            # Verificar respuesta
            response.raise_for_status()
            result = response.json()
            
            return result.get("ok", False)
        except Exception as e:
            logger.error(f"Error al enviar mensaje de Telegram: {str(e)}")
            return False
    
    def send_test_notification(self, channel: str, message: str) -> bool:
        """
        Envía una notificación de prueba
        
        Args:
            channel: Canal de notificación (telegram, email, etc.)
            message: Mensaje a enviar
            
        Returns:
            bool: True si el envío fue exitoso, False en caso contrario
        """
        if channel == "telegram":
            return self.send_telegram_message(message)
        
        # Otros canales no implementados
        logger.warning(f"Canal de notificación no implementado: {channel}")
        return False
    
    def get_notification_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado de las notificaciones
        
        Returns:
            Dict[str, Any]: Estado de cada canal de notificación
        """
        # Obtener configuración
        config = self.config_service.get_system_config()
        
        # Verificar configuración de Telegram
        telegram_status = {
            "configured": bool(settings.telegram_bot_token and settings.telegram_chat_id),
            "enabled": config.notifications.notify_opportunity or 
                      config.notifications.notify_execution or 
                      config.notifications.notify_result or 
                      config.notifications.notify_errors
        }
        
        # Verificar si se puede enviar mensaje de prueba
        if telegram_status["configured"] and telegram_status["enabled"]:
            try:
                # Enviar ping (mensaje vacío)
                url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/getMe"
                response = requests.get(url, timeout=5)
                telegram_status["available"] = response.status_code == 200
            except Exception:
                telegram_status["available"] = False
        else:
            telegram_status["available"] = False
        
        return {
            "telegram": telegram_status,
            # Otros canales futuros
        }

class DefaultSystemMonitorService(SystemMonitorService):
    """Implementación predeterminada del servicio de monitoreo del sistema"""
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del sistema
        
        Returns:
            Dict[str, Any]: Estado del sistema (CPU, memoria, etc.)
        """
        try:
            # Obtener métricas de CPU
            cpu_percent = psutil.cpu_percent(interval=0.5)
            
            # Obtener métricas de memoria
            memory = psutil.virtual_memory()
            memory_used_percent = memory.percent
            
            # Obtener métricas de disco
            disk = psutil.disk_usage("/")
            disk_used_percent = disk.percent
            
            # Obtener uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            uptime_str = f"{uptime.days} días, {uptime.seconds // 3600} horas, {(uptime.seconds // 60) % 60} minutos"
            
            return {
                "status": "OK",
                "cpu_usage": cpu_percent,
                "memory_usage": memory_used_percent,
                "disk_usage": disk_used_percent,
                "uptime": uptime_str,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error al obtener estado del sistema: {str(e)}")
            return {
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def check_processes(self) -> Dict[str, str]:
        """
        Verifica el estado de los procesos del sistema
        
        Returns:
            Dict[str, str]: Estado de cada proceso
        """
        processes = {
            "detector": "DESCONOCIDO",
            "executor": "DESCONOCIDO",
            "api_server": "DESCONOCIDO",
            "telegram_bot": "DESCONOCIDO"
        }
        
        try:
            # Buscar procesos relacionados
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    
                    # Detector de oportunidades
                    if 'python' in proc.info['name'].lower() and 'detectar_oportunidades.py' in cmdline:
                        processes['detector'] = "RUNNING"
                    
                    # Ejecutor de operaciones
                    elif 'python' in proc.info['name'].lower() and 'ejecutar_ciclo.py' in cmdline:
                        processes['executor'] = "RUNNING"
                    
                    # Servidor API
                    elif 'python' in proc.info['name'].lower() and 'api_server.py' in cmdline:
                        processes['api_server'] = "RUNNING"
                    
                    # Bot de Telegram
                    elif 'python' in proc.info['name'].lower() and 'telegram_handler.py' in cmdline:
                        processes['telegram_bot'] = "RUNNING"
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception as e:
            logger.error(f"Error al verificar procesos: {str(e)}")
        
        return processes
    
    def restart_process(self, process_name: str) -> bool:
        """
        Reinicia un proceso específico
        
        Args:
            process_name: Nombre del proceso
            
        Returns:
            bool: True si el reinicio fue exitoso, False en caso contrario
        """
        try:
            # Mapeo de nombres de procesos a scripts
            process_map = {
                "detector": "detectar_oportunidades.py",
                "executor": "ejecutar_ciclo.py",
                "api_server": "api_server.py",
                "telegram_bot": "telegram_handler.py"
            }
            
            if process_name not in process_map:
                logger.error(f"Proceso desconocido: {process_name}")
                return False
            
            script_name = process_map[process_name]
            
            # Buscar el proceso
            target_pid = None
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'python' in proc.info['name'].lower() and script_name in cmdline:
                        target_pid = proc.info['pid']
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            if target_pid:
                # Intentar terminar el proceso
                p = psutil.Process(target_pid)
                p.terminate()
                
                # Esperar a que finalice
                gone, still_alive = psutil.wait_procs([p], timeout=5)
                if still_alive:
                    # Forzar terminación
                    p.kill()
            
            # Iniciar nuevo proceso
            script_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src", "core", script_name)
            if not os.path.exists(script_path):
                logger.error(f"No se encontró el script: {script_path}")
                return False
            
            # Iniciar en segundo plano
            import subprocess
            subprocess.Popen(["python", script_path], shell=True)
            
            return True
        except Exception as e:
            logger.error(f"Error al reiniciar proceso: {str(e)}")
            return False
    
    def get_logs(self, component: str, lines: int = 100) -> List[str]:
        """
        Obtiene los logs de un componente específico
        
        Args:
            component: Nombre del componente
            lines: Número máximo de líneas
            
        Returns:
            List[str]: Lista de líneas de log
        """
        try:
            # Mapeo de componentes a archivos de log
            log_files = {
                "detector": "detector.log",
                "executor": "executor.log",
                "api_server": "api_server.log",
                "telegram_bot": "telegram_bot.log",
                "dashboard": "dashboard.log",
                "system": "system.log"
            }
            
            if component not in log_files:
                logger.error(f"Componente desconocido: {component}")
                return [f"Componente desconocido: {component}"]
            
            log_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "logs", log_files[component])
            
            if not os.path.exists(log_path):
                return [f"No se encontró el archivo de log: {log_files[component]}"]
            
            # Leer últimas líneas
            with open(log_path, 'r', encoding='utf-8') as f:
                # Leer todas las líneas y tomar las últimas 'lines'
                all_lines = f.readlines()
                return all_lines[-lines:]
        except Exception as e:
            logger.error(f"Error al obtener logs: {str(e)}")
            return [f"Error al obtener logs: {str(e)}"]
