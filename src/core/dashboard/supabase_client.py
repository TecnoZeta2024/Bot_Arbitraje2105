import os
from functools import lru_cache

import streamlit as st
from supabase import Client, create_client


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Crea un cliente de Supabase usando las credenciales del entorno
    
    Returns:
        Client: Cliente de Supabase
    """
    # Obtener las credenciales de Supabase del entorno
    supabase_url = os.getenv("SUPABASE_URL", "https://almhlhmijfkcvmdbidvw.supabase.co")
    supabase_key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFsbWhsaG1pamZrY3ZtZGJpZHZ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY4NDUyMjksImV4cCI6MjA2MjQyMTIyOX0.-Jma387OwDcnOnoiR0g8KJT6QussDmxj4ot363SuKbk")
    
    # Crear y retornar el cliente
    return create_client(supabase_url, supabase_key)

# Funciones para obtener datos específicos

def get_arbitrage_operations(limit=100, order_by="fecha_inicio_ejecucion", ascending=False):
    """
    Obtiene las operaciones de arbitraje de Supabase
    
    Args:
        limit (int): Número máximo de operaciones a obtener
        order_by (str): Campo por el cual ordenar
        ascending (bool): Orden ascendente (True) o descendente (False)
    
    Returns:
        list: Lista de operaciones
    """
    try:
        supabase = get_supabase_client()
        direction = "asc" if ascending else "desc"
        
        response = supabase.table("arbitraje_operaciones") \
            .select("*") \
            .order(order_by, direction) \
            .limit(limit) \
            .execute()
            
        return response.data
    except Exception as e:
        st.error(f"Error al obtener operaciones: {str(e)}")
        return []

def get_system_config():
    """
    Obtiene la configuración del sistema desde Supabase
    
    Returns:
        dict: Configuración del sistema
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table("configuracion_sistema") \
            .select("*") \
            .execute()
            
        if response.data:
            return response.data[0]
        return {}
    except Exception as e:
        st.error(f"Error al obtener configuración: {str(e)}")
        return {}

def update_system_config(config_data):
    """
    Actualiza la configuración del sistema en Supabase
    
    Args:
        config_data (dict): Datos de configuración a actualizar
    
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    try:
        supabase = get_supabase_client()
        
        # Asumimos que solo hay un registro de configuración con id=1
        response = supabase.table("configuracion_sistema") \
            .update(config_data) \
            .eq("id", 1) \
            .execute()
            
        return True
    except Exception as e:
        st.error(f"Error al actualizar configuración: {str(e)}")
        return False

def get_performance_metrics(days=30):
    """
    Obtiene métricas de rendimiento para el período especificado
    
    Args:
        days (int): Número de días para los cuales obtener métricas
    
    Returns:
        list: Lista de métricas de rendimiento
    """
    try:
        supabase = get_supabase_client()
        
        # Consulta para obtener métricas de rendimiento
        response = supabase.table("arbitraje_operaciones") \
            .select("*") \
            .gte("fecha_inicio_ejecucion", f"now()-interval '{days} days'") \
            .order("fecha_inicio_ejecucion", 'asc') \
            .execute()
            
        return response.data
    except Exception as e:
        st.error(f"Error al obtener métricas: {str(e)}")
        return []

def get_token_candidates(limit=200):
    """
    Obtiene la lista de tokens candidatos de Supabase
    
    Args:
        limit (int): Número máximo de tokens a obtener
    
    Returns:
        list: Lista de tokens candidatos
    """
    try:
        supabase = get_supabase_client()
        
        # Consulta para obtener tokens
        response = supabase.table("token_candidatos") \
            .select("*") \
            .order("rendimiento_24h", ascending=False) \
            .limit(10) \
            .execute()
            
        return response.data
    except Exception as e:
        st.error(f"Error al obtener tokens candidatos: {str(e)}")
        return []

def update_token_candidates(tokens):
    """
    Actualiza o crea tokens candidatos en Supabase
    
    Args:
        tokens (list): Lista de tokens a actualizar o crear
    
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        supabase = get_supabase_client()
        
        # Insertar o actualizar tokens
        for token in tokens:
            # Verificar si el token ya existe
            response = supabase.table("token_candidatos") \
                .select("simbolo") \
                .eq("simbolo", token["simbolo"]) \
                .execute()
                
            if response.data:
                # Actualizar token existente
                supabase.table("token_candidatos") \
                    .update(token) \
                    .eq("simbolo", token["simbolo"]) \
                    .execute()
            else:
                # Insertar nuevo token
                supabase.table("token_candidatos") \
                    .insert(token) \
                    .execute()
        
        return True
    except Exception as e:
        st.error(f"Error al actualizar tokens candidatos: {str(e)}")
        return False

def get_recent_operations(limit=5):
    """
    Obtiene las operaciones más recientes
    
    Args:
        limit (int): Número máximo de operaciones a obtener
    
    Returns:
        list: Lista de operaciones recientes
    """
    return get_arbitrage_operations(limit=limit)
