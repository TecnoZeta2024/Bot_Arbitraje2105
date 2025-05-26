import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ILLMProvider(Protocol):
    """
    Interfaz común para interactuar con diferentes Large Language Models (LLMs).
    """
    @abstractmethod
    async def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        """
        Genera texto basado en un prompt y una configuración específica.
        """
        pass

class GeminiProvider(ILLMProvider):
    """
    Implementación para interactuar con la API de Google Gemini.
    """
    def __init__(self):
        # Importar aquí para evitar dependencias si Gemini no se usa
        try:
            from google.generativeai.generative_models import GenerativeModel
            self.GenerativeModel = GenerativeModel
            self.api_key = os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno.")
            self.model = self.GenerativeModel('gemini-2.5-slash-preview-05-20')
            logger.info("GeminiProvider inicializado correctamente.")
        except ImportError:
            logger.error("La librería 'google-generativeai' no está instalada. Por favor, instálela para usar GeminiProvider.")
            self.GenerativeModel = None
            self.configure = None
            self.model = None
        except Exception as e:
            logger.error(f"Error al inicializar GeminiProvider: {e}")
            self.model = None

    async def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        if not self.model:
            logger.error("GeminiProvider no está disponible o no se inicializó correctamente.")
            raise RuntimeError("GeminiProvider no está disponible.")
        try:
            generation_config = config.get("generation_config", {})
            safety_settings = config.get("safety_settings", [])
            
            response = await self.model.generate_content_async(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            return response.text
        except Exception as e:
            logger.error(f"Error al generar texto con Gemini: {e}")
            raise

class OpenAIProvider(ILLMProvider):
    """
    Implementación para interactuar con la API de OpenAI.
    """
    def __init__(self):
        # Importar aquí para evitar dependencias si OpenAI no se usa
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            if not self.client.api_key:
                raise ValueError("OPENAI_API_KEY no está configurada en las variables de entorno.")
            logger.info("OpenAIProvider inicializado correctamente.")
        except ImportError:
            logger.error("La librería 'openai' no está instalada. Por favor, instálela para usar OpenAIProvider.")
            self.client = None
        except Exception as e:
            logger.error(f"Error al inicializar OpenAIProvider: {e}")
            self.client = None

    async def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        if not self.client:
            logger.error("OpenAIProvider no está disponible o no se inicializó correctamente.")
            raise RuntimeError("OpenAIProvider no está disponible.")
        try:
            model = config.get("model", "gpt-3.5-turbo")
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens", 150)
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content
            if content is None:
                raise RuntimeError("La respuesta de OpenAI no contiene texto.")
            return content
        except Exception as e:
            logger.error(f"Error al generar texto con OpenAI: {e}")
            raise

class LLMCache:
    """
    Sistema de caché simple para respuestas de LLMs.
    Podría ser reemplazado por un sistema de caché más robusto (Redis, etc.).
    """
    def __init__(self):
        self.cache = {}
        logger.info("LLMCache inicializado.")

    def get(self, key: str) -> Optional[str]:
        return self.cache.get(key)

    def set(self, key: str, value: str):
        self.cache[key] = value
        logger.info(f"Caché actualizada para la clave: {key[:50]}...") # Log de los primeros 50 caracteres de la clave

class LLMAbstraction:
    """
    Capa de abstracción principal para interactuar con LLMs, incluyendo fallback y caché.
    """
    def __init__(self, primary_provider: Optional[ILLMProvider], fallback_provider: Optional[ILLMProvider] = None):
        if not primary_provider:
            raise ValueError("Se debe proporcionar un proveedor primario para LLMAbstraction.")
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.cache = LLMCache()
        logger.info("LLMAbstraction inicializada.")

    async def generate_text(self, prompt: str, config: Dict[str, Any], use_cache: bool = True) -> str:
        cache_key = f"{prompt}-{hash(frozenset(config.items()))}" # Generar clave de caché única
        
        if use_cache:
            cached_response = self.cache.get(cache_key)
            if cached_response:
                logger.info(f"Respuesta obtenida de la caché para el prompt: {prompt[:50]}...")
                return cached_response

        try:
            logger.info(f"Intentando con el proveedor primario para el prompt: {prompt[:50]}...")
            response = await self.primary_provider.generate_text(prompt, config)
            if use_cache:
                self.cache.set(cache_key, response)
            return response
        except Exception as e:
            logger.warning(f"El proveedor primario falló ({e}). Intentando con el proveedor de fallback (si existe).")
            if self.fallback_provider:
                try:
                    logger.info(f"Intentando con el proveedor de fallback para el prompt: {prompt[:50]}...")
                    response = await self.fallback_provider.generate_text(prompt, config)
                    if use_cache:
                        self.cache.set(cache_key, response)
                    return response
                except Exception as fallback_e:
                    logger.error(f"Ambos proveedores (primario y fallback) fallaron para el prompt: {prompt[:50]}... - Primario: {e}, Fallback: {fallback_e}")
                    raise RuntimeError(f"Fallo en ambos proveedores de LLM: {e}, {fallback_e}")
            else:
                logger.error(f"El proveedor primario falló y no hay proveedor de fallback configurado para el prompt: {prompt[:50]}... - Error: {e}")
                raise RuntimeError(f"Fallo en el proveedor primario de LLM: {e}")
