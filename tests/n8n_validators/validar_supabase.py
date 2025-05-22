"""
Validador para los nodos de Supabase en n8n.
Este script genera y verifica la configuración de las tablas en Supabase,
y la correcta integración con los nodos de n8n.
"""

import sys
import os
import json
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime

# Agregar directorio raíz al path para importar modules del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils.logger import get_logger
from src.apis.supabase_client import supabase_client

# Configurar logger
logger = get_logger("n8n_validador_supabase")

def verificar_tabla_existe(nombre_tabla: str) -> bool:
    """
    Verifica si una tabla existe en Supabase.
    
    Args:
        nombre_tabla: Nombre de la tabla a verificar.
        
    Returns:
        True si la tabla existe, False en caso contrario.
    """
    try:
        # Intentar una consulta simple para verificar si la tabla existe
        response = supabase_client.supabase.table(nombre_tabla).select("*").limit(1).execute()
        return True
    except Exception as e:
        logger.error(f"Error al verificar tabla {nombre_tabla}: {str(e)}", exc_info=e)
        return False

def crear_tabla_token_candidatos() -> bool:
    """
    Crea la tabla token_candidatos si no existe.
    
    Returns:
        True si la operación fue exitosa, False en caso contrario.
    """
    try:
        # Consulta SQL para crear la tabla
        sql = """
        CREATE TABLE IF NOT EXISTS token_candidatos (
            id SERIAL PRIMARY KEY,
            simbolo VARCHAR(20) UNIQUE,
            nombre VARCHAR(50),
            market_cap NUMERIC,
            rendimiento_7d NUMERIC,
            rendimiento_24h NUMERIC,
            rendimiento_1h NUMERIC,
            volumen_binance_24h NUMERIC,
            fecha_actualizacion TIMESTAMP DEFAULT NOW()
        );
        """
        
        # Ejecutar la consulta SQL
        supabase_client.supabase.rpc('exec_sql', {'query': sql}).execute()
        
        logger.info("Tabla token_candidatos creada correctamente")
        return True
    except Exception as e:
        logger.error(f"Error al crear tabla token_candidatos: {str(e)}", exc_info=e)
        return False

def crear_tabla_oportunidades_detectadas() -> bool:
    """
    Crea la tabla oportunidades_detectadas si no existe.
    
    Returns:
        True si la operación fue exitosa, False en caso contrario.
    """
    try:
        # Consulta SQL para crear la tabla
        sql = """
        CREATE TABLE IF NOT EXISTS oportunidades_detectadas (
            id SERIAL PRIMARY KEY,
            ruta TEXT,
            pares_comercio JSONB,
            rentabilidad_teorica NUMERIC,
            capital_inicial NUMERIC,
            fecha_deteccion TIMESTAMP DEFAULT NOW()
        );
        """
        
        # Ejecutar la consulta SQL
        supabase_client.supabase.rpc('exec_sql', {'query': sql}).execute()
        
        logger.info("Tabla oportunidades_detectadas creada correctamente")
        return True
    except Exception as e:
        logger.error(f"Error al crear tabla oportunidades_detectadas: {str(e)}", exc_info=e)
        return False

def crear_tabla_arbitraje_operaciones() -> bool:
    """
    Crea la tabla arbitraje_operaciones si no existe.
    
    Returns:
        True si la operación fue exitosa, False en caso contrario.
    """
    try:
        # Consulta SQL para crear la tabla
        sql = """
        CREATE TABLE IF NOT EXISTS arbitraje_operaciones (
            id SERIAL PRIMARY KEY,
            operacion_id VARCHAR(255) UNIQUE,
            oportunidad_detectada_id INTEGER,
            ruta_arbitraje TEXT,
            capital_inicial NUMERIC,
            analisis_ia JSONB,
            decision_usuario VARCHAR(20),
            fecha_decision TIMESTAMP,
            estado VARCHAR(50),
            pares_ejecutados JSONB,
            precios_reales JSONB,
            resultado_bruto NUMERIC,
            comisiones_totales NUMERIC,
            slippage_real NUMERIC,
            ganancia_neta NUMERIC,
            rentabilidad_real NUMERIC,
            fecha_inicio_ejecucion TIMESTAMP,
            fecha_completado TIMESTAMP,
            log_ejecucion TEXT
        );
        """
        
        # Ejecutar la consulta SQL
        supabase_client.supabase.rpc('exec_sql', {'query': sql}).execute()
        
        logger.info("Tabla arbitraje_operaciones creada correctamente")
        return True
    except Exception as e:
        logger.error(f"Error al crear tabla arbitraje_operaciones: {str(e)}", exc_info=e)
        return False

def crear_tabla_configuracion_sistema() -> bool:
    """
    Crea la tabla configuracion_sistema si no existe.
    
    Returns:
        True si la operación fue exitosa, False en caso contrario.
    """
    try:
        # Consulta SQL para crear la tabla
        sql = """
        CREATE TABLE IF NOT EXISTS configuracion_sistema (
            id SERIAL PRIMARY KEY,
            clave VARCHAR(50) UNIQUE,
            valor TEXT,
            tipo VARCHAR(20),
            descripcion TEXT,
            actualizado_por VARCHAR(50),
            fecha_actualizacion TIMESTAMP DEFAULT NOW()
        );
        """
        
        # Ejecutar la consulta SQL
        supabase_client.supabase.rpc('exec_sql', {'query': sql}).execute()
        
        logger.info("Tabla configuracion_sistema creada correctamente")
        return True
    except Exception as e:
        logger.error(f"Error al crear tabla configuracion_sistema: {str(e)}", exc_info=e)
        return False

def crear_tabla_metricas_rendimiento() -> bool:
    """
    Crea la tabla metricas_rendimiento si no existe.
    
    Returns:
        True si la operación fue exitosa, False en caso contrario.
    """
    try:
        # Consulta SQL para crear la tabla
        sql = """
        CREATE TABLE IF NOT EXISTS metricas_rendimiento (
            id SERIAL PRIMARY KEY,
            fecha DATE UNIQUE,
            operaciones_totales INTEGER,
            operaciones_exitosas INTEGER,
            operaciones_fallidas INTEGER,
            ganancia_total NUMERIC,
            perdida_total NUMERIC,
            balance_neto NUMERIC,
            rentabilidad_promedio NUMERIC,
            comisiones_totales NUMERIC,
            mejor_ruta TEXT,
            mejor_rentabilidad NUMERIC,
            tiempo_ejecucion_promedio NUMERIC
        );
        """
        
        # Ejecutar la consulta SQL
        supabase_client.supabase.rpc('exec_sql', {'query': sql}).execute()
        
        logger.info("Tabla metricas_rendimiento creada correctamente")
        return True
    except Exception as e:
        logger.error(f"Error al crear tabla metricas_rendimiento: {str(e)}", exc_info=e)
        return False

def insertar_datos_prueba() -> bool:
    """
    Inserta datos de prueba en las tablas para verificar la integración con n8n.
    
    Returns:
        True si la operación fue exitosa, False en caso contrario.
    """
    try:
        # Insertar token de prueba
        token_data = {
            "simbolo": "TEST",
            "nombre": "Token de Prueba",
            "market_cap": 1000000.0,
            "rendimiento_7d": 5.2,
            "rendimiento_24h": 2.1,
            "rendimiento_1h": 0.5,
            "volumen_binance_24h": 5000000.0,
            "fecha_actualizacion": datetime.now().isoformat()
        }
        supabase_client.insertar_token(token_data)
        
        # Insertar oportunidad de prueba
        oportunidad_data = {
            "ruta": "USDT -> TEST -> BTC -> USDT",
            "pares_comercio": json.dumps([
                {"symbol": "TESTUSDT", "step": 1},
                {"symbol": "TESTBTC", "step": 2},
                {"symbol": "BTCUSDT", "step": 3}
            ]),
            "rentabilidad_teorica": 1.5,
            "capital_inicial": 100.0,
            "fecha_deteccion": datetime.now().isoformat()
        }
        result_oportunidad = supabase_client.insertar_oportunidad(oportunidad_data)
        
        # Insertar operación de prueba
        operacion_data = {
            "operacion_id": f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "oportunidad_detectada_id": result_oportunidad.get("id", 0),
            "ruta_arbitraje": "USDT -> TEST -> BTC -> USDT",
            "capital_inicial": 100.0,
            "analisis_ia": json.dumps({
                "recomendacion": "PROCEDER",
                "confianza": 85,
                "rentabilidad_neta_estimada": 1.2,
                "riesgos_identificados": ["Riesgo de prueba 1", "Riesgo de prueba 2"],
                "explicacion": "Explicación de prueba"
            }),
            "decision_usuario": "Si",
            "fecha_decision": datetime.now().isoformat(),
            "estado": "COMPLETADO",
            "pares_ejecutados": json.dumps([
                {"symbol": "TESTUSDT", "precio": 1.05, "cantidad": 95.0},
                {"symbol": "TESTBTC", "precio": 0.00004, "cantidad": 2500.0},
                {"symbol": "BTCUSDT", "precio": 40000.0, "cantidad": 0.1}
            ]),
            "resultado_bruto": 101.2,
            "comisiones_totales": 0.3,
            "slippage_real": 0.1,
            "ganancia_neta": 0.9,
            "rentabilidad_real": 0.9,
            "fecha_inicio_ejecucion": (datetime.now()).isoformat(),
            "fecha_completado": datetime.now().isoformat()
        }
        supabase_client.insertar_operacion(operacion_data)
        
        logger.info("Datos de prueba insertados correctamente")
        return True
    except Exception as e:
        logger.error(f"Error al insertar datos de prueba: {str(e)}", exc_info=e)
        return False

def validar_tablas_supabase():
    """
    Valida la existencia y estructura de las tablas en Supabase.
    Crea las tablas si no existen y opcionalmente inserta datos de prueba.
    """
    print(f"\n{'='*50}")
    print("VALIDACIÓN DE TABLAS SUPABASE")
    print(f"{'='*50}")
    
    # Lista de tablas a verificar
    tablas = [
        "token_candidatos",
        "oportunidades_detectadas",
        "arbitraje_operaciones",
        "configuracion_sistema",
        "metricas_rendimiento"
    ]
    
    # Verificar existencia de tablas
    for tabla in tablas:
        existe = verificar_tabla_existe(tabla)
        print(f"Tabla {tabla}: {'EXISTE' if existe else 'NO EXISTE'}")
    
    print(f"{'='*50}")
    
    # Preguntar si desea crear las tablas que no existen
    crear_tablas = input("¿Desea crear las tablas que no existen? (s/n): ").lower() == 's'
    
    if crear_tablas:
        # Crear tablas
        creacion_exitosa = True
        
        if not verificar_tabla_existe("token_candidatos"):
            creacion_exitosa = crear_tabla_token_candidatos() and creacion_exitosa
        
        if not verificar_tabla_existe("oportunidades_detectadas"):
            creacion_exitosa = crear_tabla_oportunidades_detectadas() and creacion_exitosa
        
        if not verificar_tabla_existe("arbitraje_operaciones"):
            creacion_exitosa = crear_tabla_arbitraje_operaciones() and creacion_exitosa
        
        if not verificar_tabla_existe("configuracion_sistema"):
            creacion_exitosa = crear_tabla_configuracion_sistema() and creacion_exitosa
        
        if not verificar_tabla_existe("metricas_rendimiento"):
            creacion_exitosa = crear_tabla_metricas_rendimiento() and creacion_exitosa
        
        print(f"{'='*50}")
        print(f"Creación de tablas: {'EXITOSA' if creacion_exitosa else 'CON ERRORES'}")
        
        # Preguntar si desea insertar datos de prueba
        if creacion_exitosa:
            insertar_datos = input("¿Desea insertar datos de prueba? (s/n): ").lower() == 's'
            
            if insertar_datos:
                insercion_exitosa = insertar_datos_prueba()
                print(f"{'='*50}")
                print(f"Inserción de datos de prueba: {'EXITOSA' if insercion_exitosa else 'CON ERRORES'}")
    
    print(f"{'='*50}\n")

if __name__ == "__main__":
    validar_tablas_supabase()
