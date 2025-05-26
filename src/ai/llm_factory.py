import logging
import os
from typing import Optional

from src.ai.llm_providers import (
    GeminiProvider,
    ILLMProvider,
    LLMAbstraction,
    OpenAIProvider,
)

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMFactory:
    """
    Factory para crear instancias de proveedores de LLMs y la abstracción principal.
    """
    @staticmethod
    def get_provider(provider_name: str) -> Optional[ILLMProvider]:
        """
        Devuelve una instancia del proveedor de LLM especificado.
        """
        if provider_name.lower() == "gemini":
            try:
                return GeminiProvider()
            except Exception as e:
                logger.error(f"No se pudo inicializar GeminiProvider: {e}")
                return None
        elif provider_name.lower() == "openai":
            try:
                return OpenAIProvider()
            except Exception as e:
                logger.error(f"No se pudo inicializar OpenAIProvider: {e}")
                return None
        else:
            logger.warning(f"Proveedor de LLM desconocido: {provider_name}")
            return None

    @staticmethod
    def get_llm_abstraction(
        primary_llm: str,
        fallback_llm: Optional[str] = None
    ) -> LLMAbstraction:
        """
        Crea y devuelve una instancia de LLMAbstraction con los proveedores especificados.
        """
        primary_provider = LLMFactory.get_provider(primary_llm)
        if not primary_provider:
            raise ValueError(f"No se pudo obtener el proveedor primario: {primary_llm}")

        fallback_provider = None
        if fallback_llm:
            fallback_provider = LLMFactory.get_provider(fallback_llm)
            if not fallback_provider:
                logger.warning(f"No se pudo obtener el proveedor de fallback: {fallback_llm}. Se procederá sin fallback.")

        return LLMAbstraction(primary_provider=primary_provider, fallback_provider=fallback_provider)
