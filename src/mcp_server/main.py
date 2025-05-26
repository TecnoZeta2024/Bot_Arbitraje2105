import json
import logging
import os
import time
import uuid
from datetime import timedelta
from typing import Any, Dict, Optional

import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from prometheus_client import Counter, Gauge, generate_latest
from pydantic import BaseModel, TypeAdapter, ValidationError
from starlette.middleware.gzip import GZipMiddleware  # Importar GZipMiddleware
from starlette.responses import JSONResponse, PlainTextResponse

from src.mcp_server.auth import authenticate_user, create_access_token, get_current_user
from src.mcp_server.dispatcher import MCPDispatcher  # Importar MCPDispatcher
from src.mcp_server.logging_config import setup_logging
from src.mcp_server.registry import MCPRegistry  # Importar MCPRegistry
from src.mcp_server.schemas import (
    MCPRegistration,  # Importar el nuevo esquema MCPRegistration
)
from src.mcp_server.schemas import (
    PROTOCOL_VERSION,
    AcknowledgmentMessage,
    AcknowledgmentPayload,
    ErrorDetails,
    ErrorMessage,
    MCPMessage,
    MessageType,
    RequestMessage,
    RequestPayload,
    ResponseMessage,
    ResponsePayload,
)

# Configurar el logger para este módulo
logger = logging.getLogger("mcp_server.main")

app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000) # Añadir el middleware de Gzip

# Instanciar el registro de MCPs
mcp_registry = MCPRegistry()

# Instanciar el despachador de MCPs
mcp_dispatcher = MCPDispatcher(mcp_registry)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Manejador global para HTTPException."""
    error_response = _create_error_message(
        code=f"HTTP_{exc.status_code}",
        message=exc.detail,
        details=exc.headers if exc.headers else None
    )
    logger.error(f"HTTPException capturada: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Manejador global para excepciones no controladas."""
    logger.critical(f"Excepción no controlada: {exc}", exc_info=True)
    error_response = _create_error_message(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal server error occurred.",
        details={"error_type": type(exc).__name__, "error_message": str(exc)}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )

def _create_error_message(
    code: str,
    message: str,
    in_reply_to: Optional[str] = None,
    recipient_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> ErrorMessage:
    """Crea un mensaje de error estandarizado."""
    return ErrorMessage(
        protocol_version=PROTOCOL_VERSION,
        message_id=str(uuid.uuid4()),
        timestamp=time.time(),
        sender_id="mcp_server",
        payload=ErrorDetails(
            code=code,
            message=message,
            details=details
        ),
        in_reply_to=in_reply_to,
        recipient_id=recipient_id
    )

@app.get("/protocol-version")
async def get_protocol_version():
    """
    Endpoint para obtener la versión actual del protocolo MCP soportada por el servidor.
    """
    logger.info(f"Solicitud recibida para el endpoint /protocol-version. Versión actual: {PROTOCOL_VERSION}")
    return {"protocol_version": PROTOCOL_VERSION}

# Métricas de Prometheus
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint"]
)
REQUEST_DURATION_SECONDS = Gauge(
    "http_request_duration_seconds", "HTTP request duration in seconds", ["method", "endpoint"]
)
WEBSOCKET_CONNECTIONS = Gauge(
    "websocket_connections", "Number of active WebSocket connections"
)
WEBSOCKET_MESSAGES_RECEIVED = Counter(
    "websocket_messages_received_total", "Total WebSocket messages received"
)
WEBSOCKET_MESSAGES_SENT = Counter(
    "websocket_messages_sent_total", "Total WebSocket messages sent"
)
HTTP_ERRORS_TOTAL = Counter(
    "http_errors_total", "Total HTTP errors", ["method", "endpoint", "status_code"]
)
WEBSOCKET_ERRORS_TOTAL = Counter(
    "websocket_errors_total", "Total WebSocket errors"
)

@app.get("/metrics")
async def metrics():
    """
    Endpoint para exponer métricas de Prometheus.
    """
    logger.debug("Solicitud recibida para el endpoint /metrics.")
    return PlainTextResponse(generate_latest().decode("utf-8"))

@app.get("/health")
async def health_check():
    """
    Endpoint para verificar el estado de salud del servidor MCP.
    """
    logger.debug("Solicitud recibida para el endpoint /health.")
    return {"status": "ok", "timestamp": time.time()}

@app.on_event("startup")
async def startup():
    setup_logging()
    logger.info("Iniciando la aplicación FastAPI.")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    r = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(r)
    logger.info("FastAPILimiter inicializado.")
    
    # Iniciar health checks del registro de MCPs
    mcp_registry.start_health_checks(interval=10) # Intervalo configurable
    logger.info("Health checks del registro de MCPs iniciados.")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Deteniendo la aplicación FastAPI.")
    # Detener health checks del registro de MCPs
    mcp_registry.stop_health_checks()
    logger.info("Health checks del registro de MCPs detenidos.")

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    method = request.method
    endpoint = request.url.path
    status_code = response.status_code

    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint).set(process_time)

    if status_code >= 400:
        HTTP_ERRORS_TOTAL.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        logger.error(f"Error HTTP {status_code} en {method} {endpoint}")
    else:
        logger.info(f"Solicitud HTTP {method} {endpoint} procesada en {process_time:.4f} segundos con estado {status_code}")

    return response

# Endpoint para obtener el token de autenticación
@app.post("/token", dependencies=[Depends(RateLimiter(times=2, seconds=60))])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            logger.warning(f"Intento de inicio de sesión fallido para el usuario: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=30) # Usar la constante definida en auth.py si se importa
        access_token = create_access_token(
            data={"sub": user["username"]}, expires_delta=access_token_expires
        )
        logger.info(f"Inicio de sesión exitoso para el usuario: {user['username']}")
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        logger.error(f"Error de autenticación: {e.detail}")
        raise
    except Exception as e:
        logger.critical(f"Error crítico en login_for_access_token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication",
        )

@app.get("/", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def read_root(current_user: str = Depends(get_current_user)):
    logger.info(f"Acceso a la ruta raíz por el usuario: {current_user}")
    return {"message": f"MCP Server Running for user: {current_user}"}

# Endpoints para el registro y discovery de MCPs
@app.post("/register-mcp", status_code=status.HTTP_201_CREATED)
async def register_mcp(
    registration_data: MCPRegistration, # Usar el esquema MCPRegistration directamente
    current_user: str = Depends(get_current_user) # Requiere autenticación
):
    logger.info(f"Solicitud de registro de MCP recibida de {current_user} para MCP ID: {registration_data.mcp_id}")
    mcp_registry.register(registration_data) # Pasar el objeto MCPRegistration directamente
    return {"message": f"MCP {registration_data.mcp_id} registrado/actualizado exitosamente."}

@app.delete("/unregister-mcp", status_code=status.HTTP_200_OK)
async def unregister_mcp(
    mcp_id: str,
    current_user: str = Depends(get_current_user) # Requiere autenticación
):
    logger.info(f"Solicitud de desregistro de MCP recibida de {current_user} para MCP ID: {mcp_id}")
    mcp_registry.unregister(mcp_id)
    return {"message": f"MCP {mcp_id} desregistrado exitosamente."}

@app.get("/list-mcps", status_code=status.HTTP_200_OK)
async def list_mcps(
    status_filter: Optional[str] = None,
    current_user: str = Depends(get_current_user) # Requiere autenticación
):
    logger.info(f"Solicitud de listado de MCPs recibida de {current_user}. Filtro de estado: {status_filter}")
    # status_filter ya es Optional[str], la firma en registry.py lo acepta
    mcps = mcp_registry.list_mcps(status=status_filter)
    # mcps ya es una lista de diccionarios, no necesita conversión adicional para JSON
    return mcps

@app.get("/get-mcp/{mcp_id}", status_code=status.HTTP_200_OK)
async def get_mcp_config(
    mcp_id: str,
    current_user: str = Depends(get_current_user) # Requiere autenticación
):
    logger.info(f"Solicitud de obtención de MCP recibida de {current_user} para MCP ID: {mcp_id}")
    mcp_config = mcp_registry.get_mcp(mcp_id)
    if mcp_config:
        return mcp_config
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"MCP {mcp_id} no encontrado o inactivo."
    )

@app.post("/hot-reload-mcp", status_code=status.HTTP_200_OK)
async def hot_reload_mcp_config(
    registration_data: MCPRegistration, # Usar el esquema MCPRegistration directamente
    current_user: str = Depends(get_current_user) # Requiere autenticación
):
    logger.info(f"Solicitud de hot-reload de MCP recibida de {current_user} para MCP ID: {registration_data.mcp_id}")
    mcp_registry.hot_reload_config(registration_data) # Pasar el objeto MCPRegistration directamente
    return {"message": f"Configuración para MCP {registration_data.mcp_id} recargada exitosamente."}

@app.api_route("/dispatch/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def dispatch_mcp_request(
    path: str,
    request: Request,
    current_user: str = Depends(get_current_user) # Requiere autenticación
):
    logger.info(f"Solicitud de despacho recibida de {current_user} para ruta: /{path} con método: {request.method}")
    
    # Leer el cuerpo de la solicitud si no es GET o DELETE
    body = None
    if request.method in ["POST", "PUT"]:
        body = await request.body()

    try:
        response = await mcp_dispatcher.dispatch(
            path=path,
            method=request.method,
            headers=dict(request.headers), # Pasar todos los headers
            body=body
        )
        # Reenviar la respuesta del MCP al cliente
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=response.headers
        )
    except HTTPException as e:
        logger.error(f"Error al despachar solicitud HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.critical(f"Error inesperado al despachar solicitud HTTP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor al despachar la solicitud.")

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    current_user: str = Depends(get_current_user),
):
    await websocket.accept()
    WEBSOCKET_CONNECTIONS.inc()
    logger.info(f"Conexión WebSocket establecida para el usuario: {current_user}. Conexiones activas: {WEBSOCKET_CONNECTIONS._value}")

    message_count = 0
    last_message_time = 0
    RATE_LIMIT_WS_MESSAGES = 5
    RATE_LIMIT_WS_SECONDS = 60

    try:
        while True:
            try:
                data = await websocket.receive_text()
                WEBSOCKET_MESSAGES_RECEIVED.inc()
                logger.debug(f"Mensaje WebSocket recibido de {current_user}: {data}")

                current_time = time.time()
                if current_time - last_message_time > RATE_LIMIT_WS_SECONDS:
                    message_count = 0
                    last_message_time = current_time

                message_count += 1

                if message_count > RATE_LIMIT_WS_MESSAGES:
                    logger.warning(f"Límite de tasa excedido para el usuario WebSocket {current_user}. Cerrando conexión.")
                    error_msg = _create_error_message(
                        code="RATE_LIMIT_EXCEEDED",
                        message="Too many messages. Rate limit exceeded."
                    )
                    await websocket.send_json(error_msg.model_dump_json())
                    WEBSOCKET_MESSAGES_SENT.inc()
                    await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER)
                    break

                message_dict = {}
                try:
                    message_dict = json.loads(data)
                    mcp_message = TypeAdapter(MCPMessage).validate_python(message_dict)
                    logger.info(f"Mensaje MCP válido recibido: {mcp_message.message_type}")

                    # Lógica de versionado: Verificar la versión del protocolo del mensaje entrante
                    if mcp_message.protocol_version != PROTOCOL_VERSION:
                        logger.warning(
                            f"Mensaje recibido con versión de protocolo diferente. "
                            f"Esperado: {PROTOCOL_VERSION}, Recibido: {mcp_message.protocol_version}. "
                            f"ID del mensaje: {mcp_message.message_id}"
                        )
                        # Aquí se podría implementar lógica para manejar versiones antiguas/nuevas
                        # Por ejemplo, transformar el mensaje, enrutar a un manejador específico,
                        # o enviar un error si la versión no es compatible.
                        # Por ahora, solo se registra una advertencia y se procesa con la lógica actual.

                    if mcp_message.message_type == MessageType.REQUEST:
                        try:
                            # Preparar el cuerpo para el despacho (serializar argumentos a JSON y luego a bytes)
                            # Asumimos que el path para el dispatch de WebSocket es el tool_name
                            dispatch_path = mcp_message.payload.tool_name
                            dispatch_body = json.dumps(mcp_message.payload.arguments).encode('utf-8')
                            
                            # Despachar la solicitud a través del MCPDispatcher
                            # Para WebSocket, el método es conceptualmente POST ya que se envía un payload
                            dispatcher_response = await mcp_dispatcher.dispatch(
                                path=dispatch_path,
                                method="POST", # O el método adecuado según la convención de tu MCP
                                headers={"Content-Type": "application/json"},
                                body=dispatch_body
                            )

                            # Construir la respuesta MCP a partir de la respuesta del despachador
                            response_payload_instance = ResponsePayload(
                                result=dispatcher_response.json(), # Asumimos que la respuesta es JSON
                                status="success" if dispatcher_response.is_success else "failure"
                            )
                            response_msg = ResponseMessage(
                                protocol_version=PROTOCOL_VERSION,
                                message_id=str(uuid.uuid4()),
                                timestamp=time.time(),
                                sender_id="mcp_server",
                                recipient_id=mcp_message.sender_id,
                                in_reply_to=mcp_message.message_id,
                                payload=response_payload_instance
                            )
                            await websocket.send_json(response_msg.model_dump_json())
                            WEBSOCKET_MESSAGES_SENT.inc()
                            logger.debug(f"Respuesta MCP despachada y enviada a {current_user}: {response_msg.message_id}")

                        except HTTPException as e:
                            logger.error(f"Error al despachar solicitud WebSocket a MCP: {e.detail}")
                            error_msg = _create_error_message(
                                code=f"DISPATCH_ERROR_{e.status_code}",
                                message=f"Failed to dispatch request to MCP: {e.detail}",
                                in_reply_to=mcp_message.message_id,
                                recipient_id=mcp_message.sender_id
                            )
                            await websocket.send_json(error_msg.model_dump_json())
                            WEBSOCKET_MESSAGES_SENT.inc()
                        except Exception as e:
                            logger.critical(f"Error inesperado durante el despacho WebSocket: {e}", exc_info=True)
                            error_msg = _create_error_message(
                                code="INTERNAL_DISPATCH_ERROR",
                                message="An unexpected error occurred during MCP dispatch.",
                                in_reply_to=mcp_message.message_id,
                                recipient_id=mcp_message.sender_id
                            )
                            await websocket.send_json(error_msg.model_dump_json())
                            WEBSOCKET_MESSAGES_SENT.inc()
                    elif mcp_message.message_type == MessageType.ACK:
                        logger.info(f"ACK recibido para mensaje {mcp_message.in_reply_to}")
                    else:
                        ack_payload_instance = AcknowledgmentPayload(
                            status="received",
                            message=f"Message of type {mcp_message.message_type} received."
                        )
                        ack_msg = AcknowledgmentMessage(
                            protocol_version=PROTOCOL_VERSION,
                            message_id=str(uuid.uuid4()),
                            timestamp=time.time(),
                            sender_id="mcp_server",
                            recipient_id=mcp_message.sender_id,
                            in_reply_to=mcp_message.message_id,
                            payload=ack_payload_instance
                        )
                        await websocket.send_json(ack_msg.model_dump_json())
                        WEBSOCKET_MESSAGES_SENT.inc()
                        logger.debug(f"ACK MCP enviado a {current_user}: {ack_msg.message_id}")

                except json.JSONDecodeError:
                    logger.error(f"Mensaje WebSocket no es JSON válido de {current_user}: {data}")
                    error_msg = _create_error_message(
                        code="INVALID_JSON",
                        message="Message is not a valid JSON format.",
                        in_reply_to=None, # No hay message_id válido para responder
                        recipient_id=None # No hay sender_id válido
                    )
                    await websocket.send_json(error_msg.model_dump_json())
                    WEBSOCKET_MESSAGES_SENT.inc()
                except ValidationError as e:
                    logger.error(f"Error de validación Pydantic en mensaje WebSocket de {current_user}: {e.errors()}")
                    error_msg = _create_error_message(
                        code="VALIDATION_ERROR",
                        message="Message does not conform to MCP protocol schema.",
                        details={"errors": e.errors()},
                        in_reply_to=message_dict.get("message_id") if isinstance(message_dict, dict) else None,
                        recipient_id=message_dict.get("sender_id") if isinstance(message_dict, dict) else None
                    )
                    await websocket.send_json(error_msg.model_dump_json())
                    WEBSOCKET_MESSAGES_SENT.inc()
                except Exception as e:
                    logger.critical(f"Error inesperado al procesar mensaje WebSocket de {current_user}: {e}", exc_info=True)
                    error_msg = _create_error_message(
                        code="INTERNAL_SERVER_ERROR",
                        message="An unexpected error occurred while processing your message.",
                        in_reply_to=message_dict.get("message_id") if isinstance(message_dict, dict) else None,
                        recipient_id=message_dict.get("sender_id") if isinstance(message_dict, dict) else None
                    )
                    await websocket.send_json(error_msg.model_dump_json())
                    WEBSOCKET_MESSAGES_SENT.inc()

            except Exception as e:
                WEBSOCKET_ERRORS_TOTAL.inc()
                logger.error(f"Error general en WebSocket para el usuario {current_user}: {e}", exc_info=True)
                try:
                    error_msg = _create_error_message(
                        code="CONNECTION_ERROR",
                        message="An error occurred with the WebSocket connection."
                    )
                    await websocket.send_json(error_msg.model_dump_json())
                    WEBSOCKET_MESSAGES_SENT.inc()
                except Exception as send_e:
                    logger.error(f"No se pudo enviar el mensaje de error antes de cerrar la conexión: {send_e}")
                finally:
                    await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
                break
    finally:
        WEBSOCKET_CONNECTIONS.dec()
        logger.info(f"Conexión WebSocket cerrada para el usuario: {current_user}. Conexiones activas: {WEBSOCKET_CONNECTIONS._value}")
