import logging
from typing import Dict, Any, List
from src.mcp_server.adapters.base_adapter import BaseMCPAdapter
from src.mcp_server.schemas import Tool, Resource, ToolParameter, ResourceSchema

logger = logging.getLogger(__name__)

class ExampleMCPAdapter(BaseMCPAdapter):
    """
    Adaptador de ejemplo para demostrar la implementación de BaseMCPAdapter.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__("example-server", "Adaptador de ejemplo para pruebas", config)

    def get_tools(self) -> List[Tool]:
        """
        Define las herramientas que expone este adaptador.
        """
        return [
            Tool(
                name="greet_user",
                description="Saluda a un usuario por su nombre.",
                parameters=[
                    ToolParameter(name="name", type="string", description="El nombre del usuario a saludar.", optional=True)
                ],
                output_schema={"type": "object", "properties": {"message": {"type": "string"}}}
            )
        ]

    def get_resources(self) -> List[Resource]:
        """
        Define los recursos que expone este adaptador.
        """
        return [
            Resource(
                uri="/example/status",
                description="Retorna el estado actual del servidor de ejemplo.",
                schema=ResourceSchema(
                    type="object",
                    properties={
                        "status": {"type": "string"},
                        "version": {"type": "string"}
                    },
                    description="Estado del servidor de ejemplo.",
                    items=None # Añadido items=None
                )
            )
        ]

    async def handle_tool_request(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja una solicitud para ejecutar una herramienta específica.
        """
        logger.info(f"Manejando solicitud de herramienta Example: {tool_name} con parámetros {parameters}")
        if tool_name == "greet_user":
            name = parameters.get("name", "Invitado")
            return {"message": f"¡Hola, {name} desde ExampleMCPAdapter!"}
        else:
            raise ValueError(f"Herramienta Example no soportada: {tool_name}")

    async def handle_resource_request(self, uri: str, query_params: Dict[str, Any]) -> Any:
        """
        Maneja una solicitud para acceder a un recurso específico.
        """
        logger.info(f"Manejando solicitud de recurso Example: {uri} con query_params {query_params}")
        if uri == "/example/status":
            return {"status": "activo", "version": "1.0.0"}
        else:
            raise ValueError(f"Recurso Example no soportado: {uri}")
