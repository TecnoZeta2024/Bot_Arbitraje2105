from typing import Any, Dict

import google.generativeai as genai

from src.utils.config import settings
from src.utils.logger import get_logger

gemini_logger = get_logger("gemini_client")

class GeminiClient:
    """
    Cliente para interactuar con la API de Google Gemini.
    """
    def __init__(self):
        self.api_key = settings.gemini_api_key
        if not self.api_key:
            gemini_logger.error("GEMINI_API_KEY no está configurada en las variables de entorno.")
            raise ValueError("GEMINI_API_KEY no configurada.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        gemini_logger.info("Cliente Gemini inicializado.")

    async def generate_content(self, prompt: str) -> Dict[str, Any]:
        """
        Genera contenido utilizando el modelo Gemini.

        Args:
            prompt (str): El prompt de texto para generar contenido.

        Returns:
            Dict[str, Any]: La respuesta de la API de Gemini.
        """
        try:
            gemini_logger.info(f"Enviando prompt a Gemini: {prompt[:100]}...") # Log first 100 chars
            response = await self.model.generate_content(prompt)
            gemini_logger.info("Respuesta de Gemini recibida.")
            
            # Acceder al texto generado y parsear la respuesta completa
            parsed_response = self.parse_gemini_response(response)
            
            return {
                "success": parsed_response.get("success", True), # Propagate success from parsing, default to True
                "text": parsed_response.get("text"),
                "parsed_response": parsed_response, # Include the full parsed data
                "raw_response": response # Keep raw response for debugging if needed
            }
        except Exception as e:
            gemini_logger.error(f"Error al generar o parsear contenido con Gemini: {str(e)}", exc_info=e)
            return {
                "success": False,
                "error": str(e)
            }

    def parse_gemini_response(self, response: Any) -> Dict[str, Any]:
        """
        Parsea la respuesta cruda de la API de Gemini.

        Args:
            response (Any): El objeto de respuesta cruda de Gemini.

        Returns:
            Dict[str, Any]: Un diccionario con la información parseada.
        """
        parsed_data = {
            "text": None,
            "blocked": False,
            "safety_ratings": [],
            "finish_reason": None,
            "prompt_feedback": None
        }

        try:
            if response.parts:
                parsed_data["text"] = response.text
            
            if response.prompt_feedback:
                parsed_data["prompt_feedback"] = response.prompt_feedback.to_dict()
                if response.prompt_feedback.block_reason:
                    parsed_data["blocked"] = True
                    gemini_logger.warning(f"Respuesta de Gemini bloqueada por: {response.prompt_feedback.block_reason}")

            if response.candidates:
                candidate = response.candidates[0] # Assuming we care about the first candidate
                if candidate.finish_reason:
                    parsed_data["finish_reason"] = candidate.finish_reason.name
                if candidate.safety_ratings:
                    parsed_data["safety_ratings"] = [sr.to_dict() for sr in candidate.safety_ratings]
                    for sr in candidate.safety_ratings:
                        if sr.blocked:
                            parsed_data["blocked"] = True
                            gemini_logger.warning(f"Contenido bloqueado por Safety Rating: {sr.category.name} - {sr.threshold.name}")
            
            gemini_logger.info("Respuesta de Gemini parseada exitosamente.")
        except Exception as e:
            gemini_logger.error(f"Error al parsear la respuesta de Gemini: {str(e)}", exc_info=e)
            parsed_data["error"] = str(e)
            parsed_data["success"] = False # Indicate parsing failure

        return parsed_data

# Instancia global del cliente Gemini
gemini_client = GeminiClient()
