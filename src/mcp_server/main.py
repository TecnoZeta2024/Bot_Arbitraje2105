import logging
from datetime import datetime, timedelta
from typing import Dict, Optional  # Importar Optional

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.mcp_server.registry import MCPRegistry  # Importar el registro de MCPs

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Instancia global del registro de MCPs
mcp_registry = MCPRegistry()

app = FastAPI(
    title="MCPs HTTP/WebSocket Server",
    description="Servidor FastAPI para exponer Model Context Protocols (MCPs) a Large Language Models (LLMs) y comunicación en tiempo real via WebSockets.",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Autenticación (JWT simplificado para ejemplo)
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Usuarios de ejemplo (en un entorno real, esto vendría de una base de datos)
FAKE_USERS_DB = {
    "testuser": {
        "username": "testuser",
        "password": "testpassword" # En un entorno real, usar hashes de contraseñas
    }
}

def get_user(username: str):
    if username in FAKE_USERS_DB:
        return FAKE_USERS_DB[username]
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user or user["password"] != password:
        return False
    return user

# async def get_current_user(token: str = Depends(oauth2_scheme)):
#     # Aquí se debería decodificar y validar el token JWT
#     # Por simplicidad, solo verificamos si el token es "valid_token"
#     if token != "valid_token":
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Credenciales inválidas",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     return {"username": "authenticated_user"} # Retorna un usuario ficticio

# Rate Limiting (implementación básica en memoria)
# En un entorno de producción, usar Redis o similar
RATE_LIMIT_WINDOW = 60 # segundos
RATE_LIMIT_MAX_REQUESTS = 10 # solicitudes por ventana
request_counts: Dict[str, list[datetime]] = {}

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        current_time = datetime.now()

        if client_ip not in request_counts:
            request_counts[client_ip] = []

        # Limpiar solicitudes antiguas
        request_counts[client_ip] = [
            timestamp for timestamp in request_counts[client_ip]
            if current_time - timestamp <= timedelta(seconds=RATE_LIMIT_WINDOW)
        ]

        # Contar solicitudes en la ventana actual
        if client_ip != "unknown" and len(request_counts[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Demasiadas solicitudes. Por favor, inténtelo de nuevo más tarde."}
            )
        
        request_counts[client_ip].append(current_time)
        logger.info(f"Request from {client_ip} to {request.url.path}")
        response = await call_next(request)
        return response

app.add_middleware(RateLimitMiddleware)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up MCP server...")
    mcp_registry.start_health_checks(interval=10) # Iniciar health checks al inicio

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down MCP server...")
    mcp_registry.stop_health_checks() # Detener health checks al apagar

# Rutas HTTP
@app.get("/")
async def read_root():
    logger.info("Root endpoint accessed.")
    return {"message": "Servidor Base HTTP/WebSocket para MCPs. Registro de MCPs activo."}

@app.post("/register_mcp")
async def register_mcp(mcp_id: str, config: Dict, metadata: Optional[Dict] = None):
    """
    Endpoint para registrar un nuevo MCP o actualizar uno existente.
    """
    mcp_registry.register(mcp_id, config, metadata)
    return {"message": f"MCP {mcp_id} registrado/actualizado exitosamente."}

@app.get("/list_mcps")
async def list_mcps(status: Optional[str] = None):
    """
    Endpoint para listar los MCPs registrados, opcionalmente filtrados por estado.
    """
    return mcp_registry.list_mcps(status)

@app.get("/get_mcp/{mcp_id}")
async def get_mcp_info(mcp_id: str):
    """
    Endpoint para obtener la configuración de un MCP específico.
    """
    mcp_config = mcp_registry.get_mcp(mcp_id)
    if mcp_config:
        return {"mcp_id": mcp_id, "config": mcp_config}
    raise HTTPException(status_code=404, detail=f"MCP {mcp_id} no encontrado o inactivo.")

@app.post("/hot_reload_mcp_config")
async def hot_reload_mcp_config(mcp_id: str, new_config: Dict):
    """
    Endpoint para recargar la configuración de un MCP sin reiniciar el servidor.
    """
    mcp_registry.hot_reload_config(mcp_id, new_config)
    return {"message": f"Configuración de MCP {mcp_id} recargada exitosamente."}

@app.delete("/unregister_mcp/{mcp_id}")
async def unregister_mcp_endpoint(mcp_id: str):
    """
    Endpoint para desregistrar un MCP.
    """
    mcp_registry.unregister(mcp_id)
    return {"message": f"MCP {mcp_id} desregistrado exitosamente."}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None): # , current_user: dict = Depends(get_current_user)
    logger.info(f"Item {item_id} accessed.")
    return {"item_id": item_id, "q": q} # , "user": current_user

# Ruta WebSocket
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Extraer el token de los query parameters
    token: str = websocket.query_params.get("token", "") # Asegurar que token sea siempre una cadena

    if token != "valid_token": # Simplificar la condición ya que token nunca será None
        logger.warning(f"WebSocket connection attempt with invalid token: {token}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    logger.info(f"WebSocket connection established with token: {token}")
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")
            # Aquí se procesarían las solicitudes de MCPs
            await websocket.send_text(f"Message text was: {data}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("WebSocket connection closed.")

# Para servir una página HTML simple para probar el WebSocket
templates = Jinja2Templates(directory="templates")

@app.get("/websocket_test", response_class=HTMLResponse)
async def get_websocket_test_page(request: Request):
    return templates.TemplateResponse("websocket_test.html", {"request": request})
