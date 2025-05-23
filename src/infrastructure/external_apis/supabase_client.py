"""
Cliente para interactuar con la base de datos Supabase.
"""

import json
from typing import Any, Dict, List, Optional, Union

from supabase import Client, create_client

from ...utils.config import get_config_value  # Import get_config_value desde src.utils
from ...utils.logger import get_logger

# Obtener logger específico
logger = get_logger("supabase_client")

class SupabaseClient:
    """
    Cliente para interactuar con Supabase.
    Proporciona métodos para realizar operaciones CRUD en las tablas del proyecto.
    """
    
    def __init__(self):
        """Inicializa el cliente de Supabase con la configuración global."""
        supabase_url = get_config_value("SUPABASE_URL")
        supabase_key = get_config_value("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
             logger.critical("Supabase URL or Key not configured.")
             # Depending on desired behavior, could raise an error or return None/False
             # For now, raise an error to halt if essential config is missing
             raise ValueError("Supabase URL and Key must be configured.")

        try:
            self.client: Client = create_client(
                supabase_url,
                supabase_key
            )
            logger.info("Cliente Supabase inicializado correctamente")
        except Exception as e:
            logger.critical(f"Error al inicializar cliente Supabase: {str(e)}", exc_info=e)
            raise
    
    def check_connection(self) -> bool:
        """
        Verifica que la conexión con Supabase esté funcionando correctamente.
        
        Returns:
            bool: True si la conexión es exitosa, False en caso contrario.
        """
        try:
            # Intentar una consulta simple para verificar la conexión
            response = self.client.table("arbitraje_operaciones").select("count").execute()
            return True
        except Exception as e:
            logger.error(f"Error al verificar conexión con Supabase: {str(e)}", exc_info=e)
            return False
    
    # Operaciones para token_candidatos
    
    def insertar_token(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserta un nuevo token candidato.
        
        Args:
            token_data: Datos del token a insertar.
            
        Returns:
            Datos del token insertado.
        """
        try:
            response = self.client.table("token_candidatos").insert(token_data).execute()
            logger.info(f"Token insertado: {token_data.get('simbolo')}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error al insertar token {token_data.get('simbolo')}: {str(e)}", exc_info=e)
            raise
    
    def insertar_tokens(self, tokens_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Inserta múltiples tokens candidatos.
        
        Args:
            tokens_data: Lista de datos de tokens a insertar.
            
        Returns:
            Lista de tokens insertados.
        """
        try:
            response = self.client.table("token_candidatos").insert(tokens_data).execute()
            logger.info(f"Insertados {len(tokens_data)} tokens")
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error al insertar múltiples tokens: {str(e)}", exc_info=e)
            raise
    
    def obtener_tokens(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de tokens candidatos.
        
        Args:
            limit: Límite de resultados (default: 50).
            
        Returns:
            Lista de tokens candidatos.
        """
        try:
            response = self.client.table("token_candidatos").select("*").limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error al obtener tokens: {str(e)}", exc_info=e)
            return []
    
    def obtener_token_por_simbolo(self, simbolo: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un token por su símbolo.
        
        Args:
            simbolo: Símbolo del token a buscar.
            
        Returns:
            Datos del token o None si no existe.
        """
        try:
            response = self.client.table("token_candidatos").select("*").eq("simbolo", simbolo).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error al obtener token {simbolo}: {str(e)}", exc_info=e)
            return None
            
    def actualizar_token(self, simbolo: str, actualizacion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza los datos de un token candidato existente por su símbolo.
        
        Args:
            simbolo: Símbolo del token a actualizar.
            actualizacion_data: Datos a actualizar.
            
        Returns:
            Datos del token actualizado.
        """
        try:
            response = self.client.table("token_candidatos").update(actualizacion_data).eq("simbolo", simbolo).execute()
            logger.info(f"Token actualizado: {simbolo}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error al actualizar token {simbolo}: {str(e)}", exc_info=e)
            raise

    def eliminar_token(self, simbolo: str) -> Dict[str, Any]:
        """
        Elimina un token candidato por su símbolo.
        
        Args:
            simbolo: Símbolo del token a eliminar.
            
        Returns:
            Datos del token eliminado.
        """
        try:
            response = self.client.table("token_candidatos").delete().eq("simbolo", simbolo).execute()
            logger.info(f"Token eliminado: {simbolo}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error al eliminar token {simbolo}: {str(e)}", exc_info=e)
            raise
    
    # Operaciones para oportunidades_detectadas
    
    def insertar_oportunidad(self, oportunidad_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserta una nueva oportunidad de arbitraje detectada.
        
        Args:
            oportunidad_data: Datos de la oportunidad a insertar.
            
        Returns:
            Datos de la oportunidad insertada.
        """
        try:
            # Manejar campos JSON si existen
            if "pares_comercio" in oportunidad_data and not isinstance(oportunidad_data["pares_comercio"], str):
                oportunidad_data["pares_comercio"] = json.dumps(oportunidad_data["pares_comercio"])
                
            response = self.client.table("oportunidades_detectadas").insert(oportunidad_data).execute()
            logger.info(f"Oportunidad insertada: {oportunidad_data.get('ruta')}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error al insertar oportunidad: {str(e)}", exc_info=e)
            raise
    
    def obtener_oportunidades(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de oportunidades detectadas recientes.
        
        Args:
            limit: Límite de resultados (default: 20).
            
        Returns:
            Lista de oportunidades detectadas.
        """
        try:
            response = self.client.table("oportunidades_detectadas").select("*").order("fecha_deteccion", desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error al obtener oportunidades: {str(e)}", exc_info=e)
            return []
            
    def actualizar_oportunidad(self, oportunidad_id: str, actualizacion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza los datos de una oportunidad de arbitraje existente por su ID.
        
        Args:
            oportunidad_id: ID único de la oportunidad.
            actualizacion_data: Datos a actualizar.
            
        Returns:
            Datos de la oportunidad actualizada.
        """
        try:
            # Manejar campos JSON si existen
            if "pares_comercio" in actualizacion_data and not isinstance(actualizacion_data["pares_comercio"], str):
                actualizacion_data["pares_comercio"] = json.dumps(actualizacion_data["pares_comercio"])
                
            response = self.client.table("oportunidades_detectadas").update(actualizacion_data).eq("id", oportunidad_id).execute()
            logger.info(f"Oportunidad actualizada: {oportunidad_id}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error al actualizar oportunidad {oportunidad_id}: {str(e)}", exc_info=e)
            raise

    def eliminar_oportunidad(self, oportunidad_id: str) -> Dict[str, Any]:
        """
        Elimina una oportunidad de arbitraje por su ID.
        
        Args:
            oportunidad_id: ID único de la oportunidad.
            
        Returns:
            Datos de la oportunidad eliminada.
        """
        try:
            response = self.client.table("oportunidades_detectadas").delete().eq("id", oportunidad_id).execute()
            logger.info(f"Oportunidad eliminada: {oportunidad_id}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error al eliminar oportunidad {oportunidad_id}: {str(e)}", exc_info=e)
            raise
    
    # Operaciones para arbitraje_operaciones
    
    def insertar_operacion(self, operacion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserta una nueva operación de arbitraje.
        
        Args:
            operacion_data: Datos de la operación a insertar.
            
        Returns:
            Datos de la operación insertada.
        """
        try:
            # Manejar campos JSON si existen
            for campo in ["analisis_ia", "pares_ejecutados", "precios_reales"]:
                if campo in operacion_data and not isinstance(operacion_data[campo], str):
                    operacion_data[campo] = json.dumps(operacion_data[campo])
                    
            response = self.client.table("arbitraje_operaciones").insert(operacion_data).execute()
            logger.info(f"Operación insertada: {operacion_data.get('operacion_id')}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error al insertar operación: {str(e)}", exc_info=e)
            raise
    
    def actualizar_operacion(self, operacion_id: str, actualizacion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza los datos de una operación existente.
        
        Args:
            operacion_id: ID único de la operación.
            actualizacion_data: Datos a actualizar.
            
        Returns:
            Datos de la operación actualizada.
        """
        try:
            # Manejar campos JSON si existen
            for campo in ["analisis_ia", "pares_ejecutados", "precios_reales"]:
                if campo in actualizacion_data and not isinstance(actualizacion_data[campo], str):
                    actualizacion_data[campo] = json.dumps(actualizacion_data[campo])
                    
            response = self.client.table("arbitraje_operaciones").update(actualizacion_data).eq("operacion_id", operacion_id).execute()
            logger.info(f"Operación actualizada: {operacion_id}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error al actualizar operación {operacion_id}: {str(e)}", exc_info=e)
            raise
    
    def obtener_operacion(self, operacion_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos de una operación por su ID.
        
        Args:
            operacion_id: ID único de la operación.
            
        Returns:
            Datos de la operación o None si no existe.
        """
        try:
            response = self.client.table("arbitraje_operaciones").select("*").eq("operacion_id", operacion_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error al obtener operación {operacion_id}: {str(e)}", exc_info=e)
            return None
    
    def obtener_operaciones_recientes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de operaciones recientes.
        
        Args:
            limit: Límite de resultados (default: 10).
            
        Returns:
            Lista de operaciones.
        """
        try:
            response = self.client.table("arbitraje_operaciones").select("*").order("fecha_completado", desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error al obtener operaciones recientes: {str(e)}", exc_info=e)
            return []
            
    def eliminar_operacion(self, operacion_id: str) -> Dict[str, Any]:
        """
        Elimina una operación de arbitraje por su ID.
        
        Args:
            operacion_id: ID único de la operación.
            
        Returns:
            Datos de la operación eliminada.
        """
        try:
            response = self.client.table("arbitraje_operaciones").delete().eq("operacion_id", operacion_id).execute()
            logger.info(f"Operación eliminada: {operacion_id}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error al eliminar operación {operacion_id}: {str(e)}", exc_info=e)
            raise

    # Operaciones para configuración_sistema

    def obtener_configuracion(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene la configuración del sistema.
        
        Returns:
            Datos de la configuración o None si no existe.
        """
        try:
            # Asumiendo que solo hay una fila de configuración
            response = self.client.table("configuracion_sistema").select("*").limit(1).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error al obtener configuración del sistema: {str(e)}", exc_info=e)
            return None

    def actualizar_configuracion(self, actualizacion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza la configuración del sistema.
        
        Args:
            actualizacion_data: Datos a actualizar.
            
        Returns:
            Datos de la configuración actualizada.
        """
        try:
            # Asumiendo que solo hay una fila de configuración y la actualizamos por un ID conocido o un filtro
            # Aquí asumimos que hay una columna 'id' o similar para identificar la única fila
            # Si no hay una columna 'id', necesitaríamos otro criterio o asumir que siempre actualizamos la primera/única fila
            # Para simplificar, asumimos una columna 'id' con un valor fijo o conocido, o actualizamos la primera fila encontrada
            
            # Opción 1: Actualizar por un ID conocido (si existe)
            # response = self.client.table("configuracion_sistema").update(actualizacion_data).eq("id", "conocido").execute()
            
            # Opción 2: Actualizar la primera fila encontrada (menos robusto si hay múltiples filas)
            # Primero obtenemos la fila para obtener su ID si es necesario, o simplemente actualizamos sin filtro si la tabla solo tiene una fila
            
            # Si la tabla 'configuracion_sistema' solo tiene una fila por diseño, podemos intentar actualizar sin un filtro específico,
            # aunque Supabase generalmente requiere un filtro para actualizaciones.
            # Una forma más segura es obtener la fila primero.
            
            current_config = self.obtener_configuracion()
            if current_config and 'id' in current_config: # Asumiendo que la tabla tiene una columna 'id'
                 response = self.client.table("configuracion_sistema").update(actualizacion_data).eq("id", current_config['id']).execute()
            else:
                 # Si no hay configuración o no tiene ID, podríamos intentar insertar si la tabla lo permite,
                 # o lanzar un error si se espera que la configuración ya exista.
                 # Para este caso, asumimos que la configuración debe existir para ser actualizada.
                 logger.error("No se encontró configuración existente para actualizar o falta columna 'id'.")
                 return {} # O lanzar una excepción
                 
            logger.info("Configuración del sistema actualizada")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error al actualizar configuración del sistema: {str(e)}", exc_info=e)
            raise

    # Operaciones para metricas_rendimiento

    def insertar_metrica(self, metrica_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserta una nueva métrica de rendimiento.
        
        Args:
            metrica_data: Datos de la métrica a insertar.
            
        Returns:
            Datos de la métrica insertada.
        """
        try:
            response = self.client.table("metricas_rendimiento").insert(metrica_data).execute()
            logger.info("Métrica de rendimiento insertada")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error al insertar métrica de rendimiento: {str(e)}", exc_info=e)
            raise

    def obtener_metricas(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtiene las métricas de rendimiento recientes.
        
        Args:
            limit: Límite de resultados (default: 50).
            
        Returns:
            Lista de métricas de rendimiento.
        """
        try:
            response = self.client.table("metricas_rendimiento").select("*").order("fecha", desc=True).limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error al obtener métricas de rendimiento: {str(e)}", exc_info=e)
            return []
            
    def eliminar_metrica(self, metrica_id: str) -> Dict[str, Any]:
        """
        Elimina una métrica de rendimiento por su ID.
        
        Args:
            metrica_id: ID único de la métrica.
            
        Returns:
            Datos de la métrica eliminada.
        """
        try:
            response = self.client.table("metricas_rendimiento").delete().eq("id", metrica_id).execute()
            logger.info(f"Métrica de rendimiento eliminada: {metrica_id}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error al eliminar métrica de rendimiento {metrica_id}: {str(e)}", exc_info=e)
            raise
            
    def actualizar_metrica(self, metrica_id: str, actualizacion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza los datos de una métrica de rendimiento existente por su ID.
        
        Args:
            metrica_id: ID único de la métrica.
            actualizacion_data: Datos a actualizar.
            
        Returns:
            Datos de la métrica actualizada.
        """
        try:
            response = self.client.table("metricas_rendimiento").update(actualizacion_data).eq("id", metrica_id).execute()
            logger.info(f"Métrica de rendimiento actualizada: {metrica_id}")
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error al actualizar métrica de rendimiento {metrica_id}: {str(e)}", exc_info=e)
            raise

    # Queries para estadísticas y reportes

    def obtener_historial_operaciones(self, limit: int = 100, order_by: str = "fecha_completado", ascending: bool = False) -> List[Dict[str, Any]]:
        """
        Obtiene el historial de operaciones de arbitraje.

        Args:
            limit: Límite de resultados (default: 100).
            order_by: Columna para ordenar los resultados (default: "fecha_completado").
            ascending: Si True, ordena ascendente; si False, descendente (default: False).

        Returns:
            Lista de operaciones históricas.
        """
        try:
            query = self.client.table("arbitraje_operaciones").select("*")
            if order_by:
                query = query.order(order_by, desc=not ascending)
            response = query.limit(limit).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error al obtener historial de operaciones: {str(e)}", exc_info=e)
            return []


# Instancia global
supabase_client = SupabaseClient()
