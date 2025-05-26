from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.mcp_server.schemas import Resource, Tool  # Importar Tool y Resource


class BaseMCPAdapter(ABC):
    """
    Clase base abstracta para adaptadores MCP.
    Define la interfaz común que todos los adaptadores deben implementar.
    """

    def __init__(self, server_name: Optional[str] = None, description: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.server_name = server_name if server_name is not None else self.__class__.__name__.lower()
        self.description = description if description is not None else f"Adapter for {self.server_name}"
        self.config = config if config is not None else {}

    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """
        Retorna una lista de objetos Tool que este adaptador expone.
        """
        pass

    @abstractmethod
    def get_resources(self) -> List[Resource]:
        """
        Retorna una lista de objetos Resource que este adaptador expone.
        """
        pass

    @abstractmethod
    async def handle_tool_request(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja una solicitud para ejecutar una herramienta específica proporcionada por este adaptador.
        """
        pass

    @abstractmethod
    async def handle_resource_request(self, uri: str, query_params: Dict[str, Any]) -> Any:
        """
        Maneja una solicitud para acceder a un recurso específico proporcionado por este adaptador.
        """
        pass

    def to_registry_format(self) -> Dict[str, Any]:
        """
        Convierte la información del adaptador a un formato adecuado para el registro.
        """
        return {
            "server_name": self.server_name,
            "description": self.description,
            "tools": [tool.dict() for tool in self.get_tools()],
            "resources": [resource.dict() for resource in self.get_resources()]
        }
