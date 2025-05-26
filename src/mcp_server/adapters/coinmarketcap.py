import asyncio  # Necesario para run_in_executor
import logging
import os
from typing import Any, Dict, List

import requests  # Mantener requests por ahora, pero idealmente usar aiohttp o httpx

from src.mcp_server.adapters.base_adapter import BaseMCPAdapter
from src.mcp_server.schemas import Resource, ResourceSchema, Tool, ToolParameter

logger = logging.getLogger(__name__)

class CoinMarketCapAdapter(BaseMCPAdapter):
    def __init__(self, config: Dict[str, Any]):
        super().__init__("coinmarketcap", "Adaptador para CoinMarketCap API", config)
        self.api_key = config.get("api_key") or os.getenv("COINMARKETCAP_API_KEY")
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        if not self.api_key:
            logger.error("COINMARKETCAP_API_KEY no está configurada en la configuración o variables de entorno.")
            raise ValueError("COINMARKETCAP_API_KEY no está configurada.")

    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="get_latest_listings",
                description="Obtiene las últimas listas de criptomonedas con datos de mercado.",
                parameters=[
                    ToolParameter(name="start", type="integer", description="Offset de inicio para la paginación (por defecto: 1).", optional=True),
                    ToolParameter(name="limit", type="integer", description="Número de resultados a devolver (por defecto: 100, máximo: 5000).", optional=True),
                    ToolParameter(name="convert", type="string", description="Moneda a la que convertir los datos (por defecto: USD).", optional=True)
                ],
                output_schema={"type": "object"} # Se puede definir un esquema de salida más específico si es necesario
            ),
            Tool(
                name="get_quotes",
                description="Obtiene datos de mercado para una o más criptomonedas por ID o símbolo.",
                parameters=[
                    ToolParameter(name="id", type="string", description="IDs de criptomonedas separadas por comas.", optional=True),
                    ToolParameter(name="symbol", type="string", description="Símbolos de criptomonedas separadas por comas.", optional=True),
                    ToolParameter(name="convert", type="string", description="Moneda a la que convertir los datos (por defecto: USD).", optional=True)
                ],
                output_schema={"type": "object"} # Se puede definir un esquema de salida más específico si es necesario
            )
        ]

    def get_resources(self) -> List[Resource]:
        return []

    async def handle_tool_request(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": self.api_key,
        }
        
        if tool_name == "get_latest_listings":
            endpoint = f"{self.base_url}/cryptocurrency/listings/latest"
            params = {
                "start": parameters.get("start", 1),
                "limit": parameters.get("limit", 100),
                "convert": parameters.get("convert", "USD")
            }
            return await self._make_request(endpoint, headers, params)
        
        elif tool_name == "get_quotes":
            endpoint = f"{self.base_url}/cryptocurrency/quotes/latest"
            params = {
                "id": parameters.get("id"),
                "symbol": parameters.get("symbol"),
                "convert": parameters.get("convert", "USD")
            }
            return await self._make_request(endpoint, headers, params)
        
        else:
            raise ValueError(f"Herramienta no soportada: {tool_name}")

    async def handle_resource_request(self, uri: str, query_params: Dict[str, Any]) -> Any:
        raise NotImplementedError("Este adaptador no proporciona recursos.")

    async def _make_request(self, url: str, headers: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        try:
            # Ejecutar la llamada síncrona en un thread pool para no bloquear el event loop
            response = await loop.run_in_executor(
                None, # Usar el ThreadPoolExecutor por defecto
                lambda: requests.get(url, headers=headers, params=params, timeout=10) # Añadir timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"Error HTTP al solicitar {url}: {http_err}")
            raise
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"Error de conexión al solicitar {url}: {conn_err}")
            raise
        except requests.exceptions.Timeout as timeout_err:
            logger.error(f"Tiempo de espera agotado al solicitar {url}: {timeout_err}")
            raise
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Error general de solicitud al solicitar {url}: {req_err}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al procesar la solicitud a {url}: {e}")
            raise
