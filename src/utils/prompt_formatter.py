import json
from pathlib import Path
from typing import Any, Dict

from src.utils.logger import get_logger

prompt_logger = get_logger("prompt_formatter")

def load_and_format_gemini_prompt(opportunity_data: Dict[str, Any]) -> str:
    """
    Carga el template del prompt de Gemini y lo formatea con los datos de la oportunidad.

    Args:
        opportunity_data (Dict[str, Any]): Diccionario con los datos de la oportunidad.

    Returns:
        str: El prompt formateado listo para ser enviado a Gemini.
    """
    prompt_template_path = Path(__file__).parents[2] / "n8n_flows" / "prompts" / "gemini_prompt_template.txt"
    
    try:
        with open(prompt_template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # Convertir los datos de la oportunidad a una cadena JSON formateada
        opportunity_json_str = json.dumps(opportunity_data, indent=2)
        
        # Reemplazar el placeholder en el template
        # Asumiendo que el placeholder es exactamente "{{ $json.body.body.oportunidad }}"
        formatted_prompt = template.replace("{{ $json.body.body.oportunidad }}", opportunity_json_str)
        
        prompt_logger.info("Prompt de Gemini cargado y formateado exitosamente.")
        return formatted_prompt
        
    except FileNotFoundError:
        prompt_logger.error(f"Template de prompt de Gemini no encontrado en: {prompt_template_path}")
        raise FileNotFoundError(f"Template de prompt de Gemini no encontrado en: {prompt_template_path}")
    except Exception as e:
        prompt_logger.error(f"Error al cargar o formatear el prompt de Gemini: {str(e)}", exc_info=e)
        raise
