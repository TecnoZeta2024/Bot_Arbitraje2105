import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import dotenv
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from supabase.client import Client, create_client

# Cargar variables de entorno desde .env
env_file = Path(__file__).parents[2] / ".env"
load_dotenv(dotenv_path=env_file)

# Clase para acceder a las configuraciones del sistema
class Settings:
    def __init__(self):
        # Ruta al archivo .env
        self.env_file = str(env_file)
        
        # APIs externas
        self.binance_api_key = os.getenv("BINANCE_API_KEY", "")
        self.binance_api_secret = os.getenv("BINANCE_SECRET_KEY", "")
        self.binance_testnet = os.getenv("BINANCE_TESTNET", "True").lower() == "true"
        self.mobula_api_key = os.getenv("MOBULA_API_KEY", "")
        self.coingecko_api_key = os.getenv("COINGECKO_API_KEY", "")
        
        # Telegram
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        
        # Webhooks n8n
        self.n8n_webhook_oportunidad = os.getenv("N8N_WEBHOOK_OPORTUNIDAD", "")
        self.n8n_webhook_resultado = os.getenv("N8N_WEBHOOK_RESULTADO", "")
        self.n8n_webhook_decision = os.getenv("N8N_WEBHOOK_DECISION", "")
        
        # API Server
        self.api_host = os.getenv("API_HOST", "localhost")
        self.api_port = int(os.getenv("API_PORT", 8001))
        self.api_server_url = os.getenv("API_SERVER_URL", f"http://{self.api_host}:{self.api_port}")
        
        # Parámetros del bot
        self.capital_inicial = float(os.getenv("CAPITAL_INICIAL", 100))
        self.umbral_rentabilidad = float(os.getenv("UMBRAL_RENTABILIDAD", 0.5))
        self.intervalo_deteccion = int(os.getenv("INTERVALO_DETECCION", 300))
        self.max_tokens_considerados = int(os.getenv("MAX_TOKENS_CONSIDERADOS", 50))

# Instancia global para acceso a la configuración
settings = Settings()

# Configuración de logging (asegurarse de que logger esté definido)
import logging

logger = logging.getLogger(__name__)

def get_supabase_client() -> Optional[Client]:
    """
    Obtiene un cliente de Supabase configurado
    
    Returns:
        Client: Cliente de Supabase
    """
    try:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        
        if not url or not key:
            logger.warning("SUPABASE_URL o SUPABASE_KEY no están configurados en las variables de entorno.")
            return None

        client = create_client(url, key)
        return client
    except Exception as e:
        logger.error(f"Error al inicializar cliente Supabase: {str(e)}")
        return None

def load_config_from_supabase() -> Dict[str, Any]:
    """
    Carga la configuración del sistema desde la tabla 'configuracion_sistema' en Supabase.
    
    Returns:
        Dict: Configuración del sistema cargada desde Supabase.
    """
    config = {}
    try:
        supabase = get_supabase_client()
        if not supabase:
            logger.warning("No se pudo obtener cliente Supabase para cargar configuración.")
            return config

        response = supabase.table("configuracion_sistema") \
            .select("*") \
            .limit(1) \
            .execute()

        if hasattr(response, 'data') and response.data:
            # Asumimos que solo hay una fila de configuración global
            db_config = response.data[0]
            for key, value in db_config.items():
                # Excluir la columna 'id' si existe y no es necesaria en la configuración
                if key == "id":
                    continue
                config[key] = value
        else:
            logger.info("No se encontró configuración en la tabla 'configuracion_sistema' de Supabase.")

    except Exception as e:
        logger.error(f"Error al cargar configuración desde Supabase: {str(e)}")

    return config

def save_config_to_supabase(config: Dict[str, Any]) -> bool:
    """
    Guarda la configuración del sistema en la tabla 'configuracion_sistema' en Supabase.
    Elimina la configuración existente antes de insertar la nueva.
    
    Args:
        config (Dict): Configuración del sistema a guardar.
        
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario.
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            logger.warning("No se pudo obtener cliente Supabase para guardar configuración.")
            return False

        # Eliminar configuración actual
        delete_response = supabase.table("configuracion_sistema").delete().neq("clave", "non_existent_key").execute()
        if hasattr(delete_response, 'error') and delete_response.error:
             logger.error(f"Error al eliminar configuración existente en Supabase: {delete_response.error}")
             # Continuar intentando insertar, podría ser un error menor
        else:
             logger.info("Configuración existente eliminada de Supabase.")


        # Preparar datos para insertar
        rows = []
        for category, settings in config.items():
            for key, value in settings.items():
                rows.append({
                    "categoria": category,
                    "clave": key,
                    "valor": str(value) # Guardar como string en la base de datos
                })

        if not rows:
            logger.warning("No hay datos de configuración para guardar en Supabase.")
            return True # Considerar exitoso si no hay nada que guardar

        insert_response = supabase.table("configuracion_sistema").insert(rows).execute()

        if hasattr(insert_response, 'data'):
            logger.info(f"Configuración guardada exitosamente en Supabase. Filas insertadas: {len(insert_response.data)}")
            return True
        else:
            logger.error(f"Error al guardar configuración en Supabase: {insert_response}")
            return False

    except Exception as e:
        logger.error(f"Error inesperado al guardar configuración en Supabase: {str(e)}")
        return False


# --- Funciones existentes (adaptadas o mantenidas) ---

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Carga la configuración del sistema. Prioriza Supabase, luego .env, luego config.json.
    
    Args:
        config_path (str, optional): Ruta al archivo de configuración JSON (fallback).
        
    Returns:
        Dict: Configuración del sistema.
    """
    config = {}

    # 1. Cargar desde Supabase
    supabase_config = load_config_from_supabase()
    config.update(supabase_config)
    logger.info(f"Configuración cargada desde Supabase: {supabase_config}")

    # 2. Cargar desde .env (sobrescribe si hay duplicados)
    env_config = {
        "BINANCE_API_KEY": os.getenv("BINANCE_API_KEY", ""),
        "BINANCE_API_SECRET": os.getenv("BINANCE_SECRET_KEY", ""),
        "MOBULA_API_KEY": os.getenv("MOBULA_API_KEY", ""),
        "COINGECKO_API_KEY": os.getenv("COINGECKO_API_KEY", ""),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
        "SUPABASE_URL": os.getenv("SUPABASE_URL", "https://almhlhmijfkcvmdbidvw.supabase.co"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFsbWhsaG1pamZrY3ZtZGJpZHZ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY4NDUyMjksImV4cCI6MjA2MjQyMTIyOX0.-Jma387OwDcnOnoiR0g8KJT6QussDmxj4ot363SuKbk"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        "API_HOST": os.getenv("API_HOST", "localhost"),
        "API_PORT": int(os.getenv("API_PORT", 8001)),
        "CAPITAL_INICIAL": float(os.getenv("CAPITAL_INICIAL", 100.0)),
        "UMBRAL_RENTABILIDAD": float(os.getenv("UMBRAL_RENTABILIDAD", 0.5)),
        "INTERVALO_DETECCION": int(os.getenv("INTERVALO_DETECCION", 300)),
        "MAX_TOKENS_CONSIDERADOS": int(os.getenv("MAX_TOKENS_CONSIDERADOS", 50)),
        "BINANCE_TESTNET": os.getenv("BINANCE_TESTNET", "False").lower() == "true", # Añadir BINANCE_TESTNET
        "N8N_WEBHOOK_OPORTUNIDAD": os.getenv("N8N_WEBHOOK_OPORTUNIDAD", "https://d261-177-222-98-63.ngrok-free.app/webhook-test/arbitraje-oportunidad"), # Añadir webhook URLs
        "N8N_WEBHOOK_RESULTADO": os.getenv("N8N_WEBHOOK_RESULTADO", "http://localhost:5678/webhook/e5b3189c-352e-4506-8306-22a40360c7e2/arbitraje-resultado")
    }
    # Integrar env_config, manejando categorías si es necesario.
    # Por simplicidad, asumimos que las variables de entorno son de nivel superior o mapean a categorías específicas.
    # Si se necesita una estructura más compleja, se requeriría un mapeo explícito.
    # Por ahora, las agregamos directamente, sobrescribiendo si existen.
    config.update(env_config)
    logger.info(f"Configuración cargada desde .env: {env_config}")


    # 3. Cargar desde archivo JSON (fallback, sobrescribe si hay duplicados)
    if config_path:
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    json_config = json.load(f)
                    # Integrar json_config, manejando categorías si es necesario.
                    # Similar al .env, agregamos directamente.
                    config.update(json_config)
                logger.info(f"Configuración cargada desde {config_path}: {json_config}")
            else:
                 logger.warning(f"Archivo de configuración no encontrado en {config_path}")
        except Exception as e:
            logger.error(f"Error al cargar configuración desde {config_path}: {str(e)}")

    # Convertir valores a tipos correctos después de cargar de todas las fuentes
    # Esto es crucial ya que Supabase y JSON guardan como strings
    final_config = {}
    for key, value in config.items():
        if isinstance(value, dict):
            final_config[key] = {}
            for sub_key, sub_value in value.items():
                 try:
                    if isinstance(sub_value, str):
                        if sub_value.lower() == "true":
                            final_config[key][sub_key] = True
                        elif sub_value.lower() == "false":
                            final_config[key][sub_key] = False
                        elif sub_value.replace(".", "", 1).isdigit():
                            if "." in sub_value:
                                final_config[key][sub_key] = float(sub_value)
                            else:
                                final_config[key][sub_key] = int(sub_value)
                        else:
                            final_config[key][sub_key] = sub_value
                    else:
                         final_config[key][sub_key] = sub_value # Mantener tipos si no son strings
                 except ValueError:
                    final_config[key][sub_key] = sub_value # Fallback a valor original si la conversión falla
        else:
            try:
                if isinstance(value, str):
                    if value.lower() == "true":
                        final_config[key] = True
                    elif value.lower() == "false":
                        final_config[key] = False
                    elif value.replace(".", "", 1).isdigit():
                        if "." in value:
                            final_config[key] = float(value)
                        else:
                            final_config[key] = int(value)
                    else:
                        final_config[key] = value
                else:
                    final_config[key] = value # Mantener tipos si no son strings
            except ValueError:
                final_config[key] = value # Fallback a valor original si la conversión falla

    # Retornar el diccionario de configuración final
    return final_config


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
    """
    Guarda la configuración. Prioriza guardar en Supabase si es posible,
    de lo contrario, guarda en un archivo JSON si se proporciona config_path.
    
    Args:
        config (Dict): Configuración a guardar.
        config_path (str, optional): Ruta del archivo de configuración JSON (fallback).
        
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario.
    """
    # Intentar guardar en Supabase primero
    if save_config_to_supabase(config):
        logger.info("Configuración guardada exitosamente en Supabase.")
        return True
    else:
        logger.warning("No se pudo guardar configuración en Supabase.")
        # Si falla Supabase y se proporciona un path, intentar guardar en JSON
        if config_path:
            try:
                # Asegurarse de que el directorio existe
                config_file = Path(config_path)
                config_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Guardar configuración
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=4)
                
                logger.info(f"Configuración guardada exitosamente en archivo JSON: {config_path}")
                return True
            except Exception as e:
                logger.error(f"Error al guardar configuración en {config_path}: {str(e)}")
                return False
        else:
            logger.warning("No se proporcionó ruta de archivo JSON para guardar la configuración localmente.")
            return False

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Obtiene un valor específico de la configuración cargada.
    
    Args:
        key (str): Clave de configuración a obtener (puede ser 'categoria.clave').
        default (Any, optional): Valor por defecto si la clave no existe.
        
    Returns:
        Any: Valor de la configuración.
    """
    config = load_config()
    
    # Manejar claves anidadas (categoria.clave)
    keys = key.split('.')
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default # Clave no encontrada
    
    return value

def get_supabase_config() -> Dict[str, str]:
    """
    Obtiene la configuración de Supabase
    
    Returns:
        Dict: Configuración de Supabase (url, key)
    """
    return {
        "url": os.getenv("SUPABASE_URL", "https://almhlhmijfkcvmdbidvw.supabase.co"),
        "key": os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFsbWhsaG1pamZrY3ZtZGJpZHZ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDY4NDUyMjksImV4cCI6MjA2MjQyMTIyOX0.-Jma387OwDcnOnoiR0g8KJT6QussDmxj4ot363SuKbk")
    }
