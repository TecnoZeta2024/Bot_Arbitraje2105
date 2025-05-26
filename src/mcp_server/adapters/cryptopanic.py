import os
import httpx
import logging
from typing import List, Dict, Any, Optional
from src.mcp_server.adapters.base_adapter import BaseMCPAdapter
from src.mcp_server.schemas import Tool, Resource, ToolParameter, ResourceSchema

logger = logging.getLogger(__name__)

class CryptoPanicAdapter(BaseMCPAdapter):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("cryptopanic", "Adaptador para CryptoPanic API", config)
        self.api_key = config.get("api_key") or os.getenv("CRYPTOPANIC_API_KEY")
        self.base_url = "https://cryptopanic.com/api/v1"
        self.client = httpx.AsyncClient() # Usar AsyncClient para compatibilidad con async/await

        if not self.api_key:
            logger.error("CRYPTOPANIC_API_KEY no está configurada en la configuración o variables de entorno.")
            raise ValueError("CRYPTOPANIC_API_KEY no está configurada.")

    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="get_news",
                description="Obtiene las últimas noticias y eventos del mercado criptográfico de CryptoPanic.",
                parameters=[
                    ToolParameter(name="filter", type="string", description="Filtro para las noticias (e.g., 'rising', 'hot', 'bullish', 'bearish', 'important', 'saved', 'lol').", optional=True),
                    ToolParameter(name="currencies", type="string", description="Lista de símbolos de monedas separados por coma (e.g., 'BTC,ETH').", optional=True),
                    ToolParameter(name="regions", type="string", description="Lista de regiones separadas por coma (e.g., 'en', 'de', 'es').", optional=True),
                    ToolParameter(name="kind", type="string", description="Tipo de contenido (e.g., 'news', 'media').", optional=True)
                ],
                output_schema={
                    "type": "object",
                    "properties": {
                        "posts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "kind": {"type": "string"},
                                    "domain": {"type": "string"},
                                    "source": {"type": "object", "properties": {"title": {"type": "string"}, "region": {"type": "string"}}},
                                    "title": {"type": "string"},
                                    "published_at": {"type": "string", "format": "date-time"},
                                    "url": {"type": "string", "format": "uri"},
                                    "votes": {"type": "object", "properties": {"positive": {"type": "integer"}, "negative": {"type": "integer"}, "important": {"type": "integer"}, "liked": {"type": "integer"}, "disliked": {"type": "integer"}, "lol": {"type": "integer"}, "toxic": {"type": "integer"}, "saved": {"type": "integer"}}},
                                    "currencies": {"type": "array", "items": {"type": "object", "properties": {"code": {"type": "string"}, "title": {"type": "string"}, "slug": {"type": "string"}}}},
                                    "id": {"type": "integer"}
                                }
                            }
                        }
                    }
                }
            )
        ]

    def get_resources(self) -> List[Resource]:
        return []

    async def handle_tool_request(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Manejando solicitud de herramienta CryptoPanic: {tool_name} con parámetros {parameters}")
        if tool_name == "get_news":
            return await self._get_news_from_api(**parameters)
        else:
            raise ValueError(f"Herramienta CryptoPanic no soportada: {tool_name}")

    async def handle_resource_request(self, uri: str, query_params: Dict[str, Any]) -> Any:
        raise NotImplementedError("Este adaptador no proporciona recursos.")

    async def _get_news_from_api(self, filter: Optional[str] = None, currencies: Optional[str] = None, regions: Optional[str] = None, kind: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "CRYPTOPANIC_API_KEY no está configurada en las variables de entorno."}

        endpoint = f"{self.base_url}/posts/"
        params = {
            "auth_token": self.api_key,
            "public": "true"
        }

        # Filtrar parámetros opcionales que no son None
        optional_params = {
            "filter": filter,
            "currencies": currencies,
            "regions": regions,
            "kind": kind
        }
        params.update({k: v for k, v in optional_params.items() if v is not None})

        try:
            response = await self.client.get(endpoint, params=params) # Usar await con AsyncClient
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP: {e.response.status_code} - {e.response.text}")
            return {"error": f"Error HTTP: {e.response.status_code} - {e.response.text}"}
        except httpx.RequestError as e:
            logger.error(f"Error de solicitud: {e}")
            return {"error": f"Error de solicitud: {e}"}
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return {"error": f"Error inesperado: {e}"}
