import logging
import os
from typing import Any, Dict, List, Optional

import streamlit as st
from supabase import Client, create_client

from src.utils.mock_data import (
    generate_mock_config,
    generate_mock_operations,
    generate_mock_performance_metrics,
    generate_mock_realtime_opportunities,
)

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("dashboard.supabase")

def get_supabase_client() -> Client:
    """
    Obtiene un cliente de Supabase configurado
    
    Returns:
        Client: Cliente de Supabase
    """
    try:
        url = os.environ.get("SUPABASE_URL", "https://almhlhmijfkcvmdbidvw.supabase.co")
        key = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFsbWhsaG1pamZrY3ZtZGJpZHZ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY4NDUyMjksImV4cCI6MjA2MjQyMTIyOX0.-Jma387OwDcnOnoiR0g8KJT6QussDmxj4ot363SuKbk")
        
        client = create_client(url, key)
        return client
    except Exception as e:
        logger.error(f"Error al inicializar cliente Supabase: {str(e)}")
        return None

def get_arbitrage_operations(limit=100, order_by="fecha_inicio_ejecucion", ascending=False, use_mock=False) -> List[Dict[str, Any]]:
    """
    Obtiene las operaciones de arbitraje de Supabase o datos simulados
    
    Args:
        limit (int): Número máximo de operaciones a recuperar
        order_by (str): Campo por el que ordenar
        ascending (bool): Si es True, ordena ascendente, si es False, descendente
        use_mock (bool): Si es True, usa datos simulados independientemente del modo
        
    Returns:
        List[Dict]: Lista de operaciones
    """
    # Modo desarrollo o si falla conexión - usar datos simulados
    if use_mock or os.getenv("DASHBOARD_MODE", "").lower() == "dev":
        logger.info("Usando datos simulados para operaciones")
        return generate_mock_operations(limit)
    
    # Modo producción - conectar a Supabase
    try:
        supabase = get_supabase_client()
        if not supabase:
            logger.warning("No se pudo obtener cliente Supabase, usando datos simulados")
            return generate_mock_operations(limit)
            
        direction = "asc" if ascending else "desc"
        
        logger.info(f"Consultando operaciones en Supabase (limit={limit}, order={order_by} {direction})")
        response = supabase.table("arbitraje_operaciones") \
            .select("*") \
            .order(order_by, direction) \
            .limit(limit) \
            .execute()
            
        if hasattr(response, 'data'):
            logger.info(f"Operaciones recuperadas: {len(response.data)}")
            return response.data
        else:
            logger.error("Formato de respuesta Supabase inesperado")
            return generate_mock_operations(limit)
    except Exception as e:
        logger.error(f"Error al obtener operaciones: {str(e)}")
        # Fallback a datos simulados en caso de error
        return generate_mock_operations(limit)

def get_performance_metrics(use_mock=False) -> Dict[str, Any]:
    """
    Obtiene métricas de rendimiento del sistema
    
    Args:
        use_mock (bool): Si es True, usa datos simulados
        
    Returns:
        Dict: Métricas de rendimiento
    """
    if use_mock or os.getenv("DASHBOARD_MODE", "").lower() == "dev":
        logger.info("Usando datos simulados para métricas de rendimiento")
        return generate_mock_performance_metrics()
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            logger.warning("No se pudo obtener cliente Supabase, usando datos simulados")
            return generate_mock_performance_metrics()
        
        # En producción, realizar cálculos sobre datos reales
        # Ejemplo: Obtener operaciones y calcular estadísticas
        operations = get_arbitrage_operations(limit=1000, use_mock=False)
        
        if not operations:
            return generate_mock_performance_metrics()
        
        # Calcular métricas reales
        operaciones_totales = len(operations)
        operaciones_exitosas = sum(1 for op in operations if op.get('estado') == "COMPLETADO" and op.get('ganancia_neta', 0) > 0)
        tasa_exito = operaciones_exitosas / operaciones_totales if operaciones_totales > 0 else 0
        
        # Calcular ganancias
        ganancias = [op.get('ganancia_neta', 0) for op in operations if op.get('estado') == "COMPLETADO"]
        ganancia_total = sum(ganancias) if ganancias else 0
        
        # Calcular rentabilidades
        rentabilidades = [op.get('rentabilidad_real', 0) for op in operations if op.get('estado') == "COMPLETADO" and op.get('rentabilidad_real', 0) > 0]
        rentabilidad_promedio = sum(rentabilidades) / len(rentabilidades) if rentabilidades else 0
        
        # Encontrar mejor ruta
        rutas = {}
        for op in operations:
            if op.get('estado') == "COMPLETADO" and op.get('rentabilidad_real', 0) > 0:
                ruta = op.get('ruta_arbitraje', '')
                if ruta in rutas:
                    rutas[ruta]['count'] += 1
                    rutas[ruta]['total_rentabilidad'] += op.get('rentabilidad_real', 0)
                else:
                    rutas[ruta] = {
                        'count': 1,
                        'total_rentabilidad': op.get('rentabilidad_real', 0)
                    }
        
        mejor_ruta = max(rutas.items(), key=lambda x: x[1]['total_rentabilidad'] / x[1]['count'], default=(None, None))[0] if rutas else ""
        
        # Calcular otras métricas
        capitales = [op.get('capital_inicial', 0) for op in operations if op.get('estado') == "COMPLETADO"]
        capital_promedio = sum(capitales) / len(capitales) if capitales else 0
        
        # Calcular tiempos de ejecución
        tiempos = []
        for op in operations:
            if op.get('estado') == "COMPLETADO" and op.get('fecha_inicio_ejecucion') and op.get('fecha_completado'):
                try:
                    inicio = datetime.datetime.fromisoformat(op.get('fecha_inicio_ejecucion'))
                    fin = datetime.datetime.fromisoformat(op.get('fecha_completado'))
                    tiempos.append((fin - inicio).total_seconds())
                except:
                    pass
        
        tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else 0
        
        # Comisiones totales
        comisiones = [op.get('comisiones_totales', 0) for op in operations if op.get('estado') == "COMPLETADO"]
        comisiones_totales = sum(comisiones) if comisiones else 0
        
        # Operaciones por día (aproximado)
        dias_operacion = operaciones_totales / 30  # Asumiendo 30 días
        operaciones_por_dia = operaciones_totales / dias_operacion if dias_operacion > 0 else 0
        
        return {
            "operaciones_totales": operaciones_totales,
            "operaciones_exitosas": operaciones_exitosas,
            "tasa_exito": tasa_exito,
            "ganancia_total": ganancia_total,
            "rentabilidad_promedio": rentabilidad_promedio,
            "mejor_ruta": mejor_ruta,
            "capital_promedio": capital_promedio,
            "tiempo_promedio": tiempo_promedio,
            "comisiones_totales": comisiones_totales,
            "operaciones_por_dia": operaciones_por_dia
        }
        
    except Exception as e:
        logger.error(f"Error al calcular métricas de rendimiento: {str(e)}")
        return generate_mock_performance_metrics()

def get_realtime_opportunities(use_mock=False) -> List[Dict[str, Any]]:
    """
    Obtiene oportunidades de arbitraje en tiempo real
    
    Args:
        use_mock (bool): Si es True, usa datos simulados
        
    Returns:
        List[Dict]: Lista de oportunidades
    """
    if use_mock or os.getenv("DASHBOARD_MODE", "").lower() == "dev":
        logger.info("Usando datos simulados para oportunidades en tiempo real")
        return generate_mock_realtime_opportunities()
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            logger.warning("No se pudo obtener cliente Supabase, usando datos simulados")
            return generate_mock_realtime_opportunities()
        
        # Obtener oportunidades recientes
        response = supabase.table("oportunidades_detectadas") \
            .select("*") \
            .order("fecha_deteccion", 'desc') \
            .limit(10) \
            .execute()
            
        if hasattr(response, 'data') and response.data:
            # Transformar datos al formato esperado
            opportunities = []
            for opp in response.data:
                opportunity = {
                    "id": opp.get("id", f"OPP-{random.randint(100, 999)}"),
                    "ruta": opp.get("ruta", ""),
                    "rentabilidad_teorica": opp.get("rentabilidad_teorica", 0),
                    "capital_sugerido": opp.get("capital_inicial", 100),
                    "timestamp": opp.get("fecha_deteccion", ""),
                }
                
                # Buscar si hay análisis IA asociado
                try:
                    analysis_response = supabase.table("arbitraje_operaciones") \
                        .select("analisis_ia") \
                        .eq("oportunidad_detectada_id", opp.get("id")) \
                        .limit(1) \
                        .execute()
                    
                    if hasattr(analysis_response, 'data') and analysis_response.data:
                        opportunity["analisis_ia"] = analysis_response.data[0].get("analisis_ia", {})
                    else:
                        # Si no hay análisis IA, crear uno mock
                        opportunity["analisis_ia"] = {
                            "recomendacion": "PENDIENTE",
                            "confianza": 0,
                            "rentabilidad_neta_estimada": 0,
                            "riesgos_identificados": ["Análisis pendiente"]
                        }
                except:
                    opportunity["analisis_ia"] = {
                        "recomendacion": "ERROR",
                        "confianza": 0,
                        "rentabilidad_neta_estimada": 0,
                        "riesgos_identificados": ["Error al obtener análisis"]
                    }
                
                opportunities.append(opportunity)
            
            return opportunities
        else:
            logger.warning("No se encontraron oportunidades en tiempo real, usando simuladas")
            return generate_mock_realtime_opportunities()
    except Exception as e:
        logger.error(f"Error al obtener oportunidades en tiempo real: {str(e)}")
        return generate_mock_realtime_opportunities()

def get_system_config(use_mock=False) -> Dict[str, Any]:
    """
    Obtiene la configuración del sistema
    
    Args:
        use_mock (bool): Si es True, usa datos simulados
        
    Returns:
        Dict: Configuración del sistema
    """
    if use_mock or os.getenv("DASHBOARD_MODE", "").lower() == "dev":
        logger.info("Usando datos simulados para configuración del sistema")
        return generate_mock_config()
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            logger.warning("No se pudo obtener cliente Supabase, usando datos simulados")
            return generate_mock_config()
        
        # Obtener configuración
        response = supabase.table("configuracion_sistema") \
            .select("*") \
            .execute()
            
        if hasattr(response, 'data') and response.data:
            # Transformar a estructura esperada
            config = {}
            for item in response.data:
                category = item.get("categoria", "")
                key = item.get("clave", "")
                value = item.get("valor", "")
                
                if category not in config:
                    config[category] = {}
                
                try:
                    # Intentar convertir a número si es posible
                    if value.isdigit():
                        config[category][key] = int(value)
                    elif value.replace(".", "", 1).isdigit():
                        config[category][key] = float(value)
                    elif value.lower() == "true":
                        config[category][key] = True
                    elif value.lower() == "false":
                        config[category][key] = False
                    else:
                        config[category][key] = value
                except:
                    config[category][key] = value
            
            return config
        else:
            logger.warning("No se encontró configuración, usando simulada")
            return generate_mock_config()
    except Exception as e:
        logger.error(f"Error al obtener configuración: {str(e)}")
        return generate_mock_config()

def update_system_config(config: Dict[str, Any], use_mock=False) -> bool:
    """
    Actualiza la configuración del sistema
    
    Args:
        config (Dict): Nueva configuración
        use_mock (bool): Si es True, simula actualización exitosa
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario
    """
    if use_mock or os.getenv("DASHBOARD_MODE", "").lower() == "dev":
        logger.info("Simulando actualización de configuración exitosa")
        return True
    
    try:
        supabase = get_supabase_client()
        if not supabase:
            logger.warning("No se pudo obtener cliente Supabase")
            return False
        
        # Eliminar configuración actual
        supabase.table("configuracion_sistema").delete().execute()
        
        # Insertar nueva configuración
        rows = []
        for category, settings in config.items():
            for key, value in settings.items():
                rows.append({
                    "categoria": category,
                    "clave": key,
                    "valor": str(value)
                })
        
        response = supabase.table("configuracion_sistema").insert(rows).execute()
        
        return hasattr(response, 'data')
    except Exception as e:
        logger.error(f"Error al actualizar configuración: {str(e)}")
        return False
