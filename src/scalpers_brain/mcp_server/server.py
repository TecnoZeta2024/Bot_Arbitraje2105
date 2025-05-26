"""
Servidor MCP (Model Context Protocol) para Scalper's Brain
Implementa un servidor FastAPI para exponer MCPs a modelos de IA
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Modelos de datos
class MCPRequest(BaseModel):
    mcp_id: str
    action: str
    parameters: Dict[str, Any] = {}
    context: Dict[str, Any] = {}

class MCPResponse(BaseModel):
    mcp_id: str
    action: str
    status: str
    data: Any = None
    error: Optional[str] = None
    timestamp: float = time.time()

class RegisterMCPRequest(BaseModel):
    mcp_id: str
    name: str
    description: str
    version: str
    capabilities: List[str]
    actions: List[Dict[str, Any]]
    metadata: Dict[str, Any] = {}

# Clase principal del servidor MCP
class MCPServer:
    """
    Servidor para la gestión de MCPs (Model Context Protocols)
    Permite a los modelos de IA interactuar con funcionalidades del sistema
    """
    
    def __init__(self):
        self.app = FastAPI(
            title="Scalper's Brain MCP Server",
            description="Servidor de Model Context Protocols para interacción con IA",
            version="1.0.0"
        )
        
        # Registro de MCPs
        self.mcps: Dict[str, Dict[str, Any]] = {}
        
        # Cliente WebSocket activos
        self.active_connections: List[WebSocket] = []
        
        # Configurar rutas
        self._setup_routes()
        
        logger.info("Servidor MCP inicializado")
    
    def _setup_routes(self):
        """Configura las rutas del servidor FastAPI"""
        
        @self.app.get("/")
        async def root():
            return {
                "name": "Scalper's Brain MCP Server",
                "version": "1.0.0",
                "status": "active",
                "mcps_count": len(self.mcps),
                "connections": len(self.active_connections)
            }
        
        @self.app.get("/mcps")
        async def list_mcps():
            """Lista todos los MCPs registrados"""
            return {
                "mcps": [
                    {
                        "id": mcp_id,
                        "name": mcp_data["name"],
                        "description": mcp_data["description"],
                        "version": mcp_data["version"],
                        "capabilities": mcp_data["capabilities"]
                    }
                    for mcp_id, mcp_data in self.mcps.items()
                ]
            }
        
        @self.app.get("/mcps/{mcp_id}")
        async def get_mcp(mcp_id: str):
            """Obtiene información detallada de un MCP"""
            if mcp_id not in self.mcps:
                raise HTTPException(status_code=404, detail=f"MCP {mcp_id} not found")
            
            return self.mcps[mcp_id]
        
        @self.app.post("/mcps/register", response_model=dict)
        async def register_mcp(request: RegisterMCPRequest):
            """Registra un nuevo MCP"""
            mcp_id = request.mcp_id
            
            # Validar que no exista ya
            if mcp_id in self.mcps:
                # Actualizar si ya existe
                self.mcps[mcp_id].update(request.dict())
                logger.info(f"MCP actualizado: {mcp_id}")
                return {"status": "updated", "mcp_id": mcp_id}
            
            # Registrar nuevo MCP
            self.mcps[mcp_id] = request.dict()
            logger.info(f"MCP registrado: {mcp_id}")
            
            return {"status": "registered", "mcp_id": mcp_id}
        
        @self.app.post("/mcps/{mcp_id}/execute", response_model=MCPResponse)
        async def execute_mcp(mcp_id: str, request: MCPRequest):
            """Ejecuta una acción en un MCP"""
            if mcp_id not in self.mcps:
                raise HTTPException(status_code=404, detail=f"MCP {mcp_id} not found")
            
            # Validar acción
            action = request.action
            mcp_actions = [a["id"] for a in self.mcps[mcp_id]["actions"]]
            if action not in mcp_actions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Action {action} not available for MCP {mcp_id}"
                )
            
            try:
                # Aquí implementaríamos la lógica para ejecutar la acción
                # Por ahora, devolvemos una respuesta simulada
                return MCPResponse(
                    mcp_id=mcp_id,
                    action=action,
                    status="success",
                    data={"message": f"Action {action} executed successfully", "parameters": request.parameters},
                    timestamp=time.time()
                )
            except Exception as e:
                logger.error(f"Error executing MCP {mcp_id} action {action}: {e}")
                return MCPResponse(
                    mcp_id=mcp_id,
                    action=action,
                    status="error",
                    error=str(e),
                    timestamp=time.time()
                )
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """Endpoint WebSocket para comunicación en tiempo real"""
            await self._handle_websocket_connection(websocket)
    
    async def _handle_websocket_connection(self, websocket: WebSocket):
        """Maneja una conexión WebSocket"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Nueva conexión WebSocket. Total: {len(self.active_connections)}")
        
        try:
            # Enviar confirmación de conexión
            await websocket.send_json({
                "type": "connection_established",
                "message": "Connected to Scalper's Brain MCP Server",
                "mcps_count": len(self.mcps),
                "timestamp": time.time()
            })
            
            # Bucle de recepción de mensajes
            while True:
                data = await websocket.receive_text()
                await self._process_websocket_message(websocket, data)
                
        except WebSocketDisconnect:
            logger.info("WebSocket desconectado")
        except Exception as e:
            logger.error(f"Error en WebSocket: {e}")
        finally:
            # Limpiar conexión
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
            logger.info(f"Conexión cerrada. Total: {len(self.active_connections)}")
    
    async def _process_websocket_message(self, websocket: WebSocket, message: str):
        """Procesa un mensaje recibido por WebSocket"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                # Responder al ping para mantener conexión
                await websocket.send_json({"type": "pong", "timestamp": time.time()})
            
            elif message_type == "execute_mcp":
                # Ejecutar MCP
                mcp_id = data.get("mcp_id")
                action = data.get("action")
                parameters = data.get("parameters", {})
                
                if not mcp_id or not action:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Missing mcp_id or action",
                        "timestamp": time.time()
                    })
                    return
                
                # Validar MCP
                if mcp_id not in self.mcps:
                    await websocket.send_json({
                        "type": "error",
                        "error": f"MCP {mcp_id} not found",
                        "timestamp": time.time()
                    })
                    return
                
                # Validar acción
                mcp_actions = [a["id"] for a in self.mcps[mcp_id]["actions"]]
                if action not in mcp_actions:
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Action {action} not available for MCP {mcp_id}",
                        "timestamp": time.time()
                    })
                    return
                
                # Respuesta simulada
                await websocket.send_json({
                    "type": "mcp_result",
                    "mcp_id": mcp_id,
                    "action": action,
                    "status": "success",
                    "data": {"message": f"Action {action} executed successfully"},
                    "timestamp": time.time()
                })
            
            elif message_type == "list_mcps":
                # Enviar lista de MCPs
                await websocket.send_json({
                    "type": "mcps_list",
                    "mcps": [
                        {
                            "id": mcp_id,
                            "name": mcp_data["name"],
                            "description": mcp_data["description"],
                            "version": mcp_data["version"],
                            "capabilities": mcp_data["capabilities"]
                        }
                        for mcp_id, mcp_data in self.mcps.items()
                    ],
                    "timestamp": time.time()
                })
            
            else:
                # Tipo de mensaje no reconocido
                await websocket.send_json({
                    "type": "error",
                    "error": f"Unknown message type: {message_type}",
                    "timestamp": time.time()
                })
                
        except json.JSONDecodeError:
            await websocket.send_json({
                "type": "error",
                "error": "Invalid JSON",
                "timestamp": time.time()
            })
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            await websocket.send_json({
                "type": "error",
                "error": f"Internal error: {str(e)}",
                "timestamp": time.time()
            })
    
    def start(self, host: str = "127.0.0.1", port: int = 8080):
        """Inicia el servidor MCP"""
        import uvicorn
        logger.info(f"Iniciando servidor MCP en http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port)

# Función para crear y configurar el servidor
def create_mcp_server():
    """Crea una instancia del servidor MCP"""
    return MCPServer()

# Punto de entrada para ejecución directa
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = create_mcp_server()
    server.start()
