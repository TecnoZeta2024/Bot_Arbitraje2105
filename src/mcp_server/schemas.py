from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from enum import Enum

# Definición de la versión del protocolo
PROTOCOL_VERSION = "1.0.0"

class MessageType(str, Enum):
    """Define los tipos de mensajes para el protocolo MCP."""
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    EVENT = "event"
    ACK = "acknowledgment"

class BaseMessage(BaseModel):
    """Esquema base para todos los mensajes del protocolo MCP."""
    protocol_version: str = Field(PROTOCOL_VERSION, description="Versión del protocolo MCP.")
    message_id: str = Field(..., description="Identificador único del mensaje.")
    timestamp: float = Field(..., description="Marca de tiempo de creación del mensaje (Unix timestamp).")
    message_type: MessageType = Field(..., description="Tipo de mensaje (request, response, error, event, ack).")
    sender_id: str = Field(..., description="Identificador del remitente del mensaje.")
    recipient_id: Optional[str] = Field(None, description="Identificador del destinatario del mensaje (opcional).")

class RequestPayload(BaseModel):
    """Esquema para el payload de una solicitud."""
    tool_name: str = Field(..., description="Nombre de la herramienta o función a invocar.")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Argumentos para la herramienta o función.")

class RequestMessage(BaseMessage):
    """Esquema para un mensaje de solicitud (REQUEST)."""
    message_type: MessageType = MessageType.REQUEST
    payload: RequestPayload = Field(..., description="Contenido de la solicitud.")

class ResponsePayload(BaseModel):
    """Esquema para el payload de una respuesta."""
    result: Any = Field(..., description="Resultado de la operación solicitada.")
    status: str = Field(..., description="Estado de la respuesta (ej. 'success', 'failure').")

class ResponseMessage(BaseMessage):
    """Esquema para un mensaje de respuesta (RESPONSE)."""
    message_type: MessageType = MessageType.RESPONSE
    payload: ResponsePayload = Field(..., description="Contenido de la respuesta.")
    in_reply_to: str = Field(..., description="ID del mensaje de solicitud al que responde.")

class ErrorDetails(BaseModel):
    """Esquema para los detalles de un error."""
    code: str = Field(..., description="Código de error estandarizado.")
    message: str = Field(..., description="Mensaje de error descriptivo.")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales del error.")

class ErrorMessage(BaseMessage):
    """Esquema para un mensaje de error (ERROR)."""
    message_type: MessageType = MessageType.ERROR
    payload: ErrorDetails = Field(..., description="Detalles del error.")
    in_reply_to: Optional[str] = Field(None, description="ID del mensaje al que se refiere el error (opcional).")

class EventPayload(BaseModel):
    """Esquema para el payload de un evento."""
    event_name: str = Field(..., description="Nombre del evento.")
    data: Dict[str, Any] = Field(default_factory=dict, description="Datos asociados al evento.")

class EventMessage(BaseMessage):
    """Esquema para un mensaje de evento (EVENT)."""
    message_type: MessageType = MessageType.EVENT
    payload: EventPayload = Field(..., description="Contenido del evento.")

class AcknowledgmentPayload(BaseModel):
    """Esquema para el payload de un acuse de recibo."""
    status: str = Field(..., description="Estado del acuse de recibo (ej. 'received', 'processed').")
    message: Optional[str] = Field(None, description="Mensaje adicional del acuse de recibo.")

class AcknowledgmentMessage(BaseMessage):
    """Esquema para un mensaje de acuse de recibo (ACK)."""
    message_type: MessageType = MessageType.ACK
    payload: AcknowledgmentPayload = Field(..., description="Contenido del acuse de recibo.")
    in_reply_to: str = Field(..., description="ID del mensaje al que se acusa recibo.")

class MCPRegistration(BaseModel):
    """Esquema para el registro de un nuevo MCP."""
    mcp_id: str = Field(..., description="Identificador único del MCP.")
    address: str = Field(..., description="Dirección de red del MCP (ej. URL de la API).")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos detallados del MCP (versiones, etc.).")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="Capacidades del MCP (herramientas, recursos, etc.).")

class ToolParameter(BaseModel):
    """Define un parámetro para una herramienta MCP."""
    name: str = Field(..., description="Nombre del parámetro.")
    type: str = Field(..., description="Tipo de dato del parámetro (ej. 'string', 'integer', 'boolean').")
    description: str = Field(..., description="Descripción del parámetro.")
    optional: bool = Field(False, description="Indica si el parámetro es opcional.")

class Tool(BaseModel):
    """Esquema para la definición de una herramienta MCP."""
    name: str = Field(..., description="Nombre de la herramienta.")
    description: str = Field(..., description="Descripción de la herramienta.")
    parameters: List[ToolParameter] = Field(default_factory=list, description="Lista de parámetros de entrada para la herramienta.")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Esquema JSON para el resultado de salida de la herramienta (opcional).")

class ResourceSchema(BaseModel):
    """Esquema genérico para la estructura de un recurso."""
    type: str = Field(..., description="Tipo de esquema (ej. 'object', 'array', 'string', 'integer').")
    properties: Optional[Dict[str, Any]] = Field(None, description="Propiedades si el tipo es 'object'.")
    items: Optional[Dict[str, Any]] = Field(None, description="Esquema de los ítems si el tipo es 'array'.")
    description: Optional[str] = Field(None, description="Descripción del esquema.")

class Resource(BaseModel):
    """Esquema para la definición de un recurso MCP."""
    uri: str = Field(..., description="URI del recurso.")
    description: str = Field(..., description="Descripción del recurso.")
    schema: ResourceSchema = Field(..., description="Esquema JSON para la estructura del recurso.")

class CryptoSentimentRequest(BaseModel):
    """Esquema para la solicitud de sentimiento criptográfico."""
    symbol: str = Field(..., description="Símbolo de la criptomoneda (ej. 'BTC', 'ETH').")
    
class CryptoSentimentResponse(BaseModel):
    """Esquema para la respuesta de sentimiento criptográfico."""
    symbol: str = Field(..., description="Símbolo de la criptomoneda.")
    sentiment_score: float = Field(..., description="Puntuación de sentimiento (ej. 0.0 a 1.0).")
    sentiment_label: str = Field(..., description="Etiqueta de sentimiento (ej. 'positive', 'negative', 'neutral').")
    source: str = Field(..., description="Fuente del análisis de sentimiento.")

class MCPInfo(BaseModel):
    """Esquema para la información de un MCP disponible para el despachador."""
    mcp_id: str = Field(..., description="Identificador único del MCP.")
    base_url: str = Field(..., description="URL base del MCP para el despacho de solicitudes.")
    status: str = Field(..., description="Estado actual del MCP (ej. 'active', 'inactive').")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="Capacidades del MCP (herramientas, recursos, etc.).")

# Esquemas específicos para Freqtrade
class FreqtradeCommand(BaseModel):
    """Esquema base para comandos enviados a Freqtrade."""
    command: str = Field(..., description="Nombre del comando de Freqtrade a ejecutar.")
    args: Optional[List[str]] = Field(None, description="Argumentos opcionales para el comando.")
    kwargs: Optional[Dict[str, Any]] = Field(None, description="Argumentos de palabra clave opcionales para el comando.")

class FreqtradeStartBotCommand(FreqtradeCommand):
    """Comando para iniciar el bot de Freqtrade."""
    command: str = "start"
    strategy: str = Field(..., description="Nombre de la estrategia a usar.")
    dry_run: Optional[bool] = Field(True, description="Indica si se ejecuta en modo dry-run.")

class FreqtradeStopBotCommand(FreqtradeCommand):
    """Comando para detener el bot de Freqtrade."""
    command: str = "stop"

class FreqtradeForceBuyCommand(FreqtradeCommand):
    """Comando para forzar una compra en Freqtrade."""
    command: str = "forcebuy"
    pair: str = Field(..., description="Par de trading (ej. 'BTC/USDT').")
    price: Optional[float] = Field(None, description="Precio de compra (opcional).")
    amount: Optional[float] = Field(None, description="Cantidad a comprar (opcional).")

class FreqtradeForceSellCommand(FreqtradeCommand):
    """Comando para forzar una venta en Freqtrade."""
    command: str = "forcesell"
    trade_id: Optional[str] = Field(None, description="ID de la operación a vender (opcional).")
    pair: Optional[str] = Field(None, description="Par de trading (opcional, si no se usa trade_id).")
    price: Optional[float] = Field(None, description="Precio de venta (opcional).")
    amount: Optional[float] = Field(None, description="Cantidad a vender (opcional).")

class FreqtradeStatusCommand(FreqtradeCommand):
    """Comando para obtener el estado del bot de Freqtrade."""
    command: str = "status"

class FreqtradeDailyProfitCommand(FreqtradeCommand):
    """Comando para obtener el beneficio diario de Freqtrade."""
    command: str = "daily_profit"

class FreqtradeTradeData(BaseModel):
    """Esquema para una operación de trading de Freqtrade."""
    trade_id: str = Field(..., description="ID único de la operación.")
    pair: str = Field(..., description="Par de trading (ej. 'BTC/USDT').")
    strategy: str = Field(..., description="Estrategia utilizada para la operación.")
    open_date: str = Field(..., description="Fecha y hora de apertura de la operación.")
    close_date: Optional[str] = Field(None, description="Fecha y hora de cierre de la operación (si está cerrada).")
    open_rate: float = Field(..., description="Tasa de apertura.")
    close_rate: Optional[float] = Field(None, description="Tasa de cierre (si está cerrada).")
    amount: float = Field(..., description="Cantidad de la criptomoneda base.")
    profit_abs: float = Field(..., description="Beneficio absoluto en la moneda de cotización.")
    profit_pct: float = Field(..., description="Beneficio porcentual.")
    status: str = Field(..., description="Estado de la operación (ej. 'open', 'closed').")

class FreqtradePositionData(BaseModel):
    """Esquema para una posición abierta en Freqtrade."""
    pair: str = Field(..., description="Par de trading.")
    amount: float = Field(..., description="Cantidad de la criptomoneda base en la posición.")
    entry_price: float = Field(..., description="Precio de entrada promedio.")
    current_price: float = Field(..., description="Precio actual del par.")
    profit_pct: float = Field(..., description="Beneficio porcentual actual de la posición.")
    profit_abs: float = Field(..., description="Beneficio absoluto actual de la posición.")

class FreqtradeMetricData(BaseModel):
    """Esquema para métricas de rendimiento de Freqtrade."""
    key: str = Field(..., description="Nombre de la métrica (ej. 'total_trades', 'avg_profit').")
    value: Any = Field(..., description="Valor de la métrica.")
    timestamp: float = Field(..., description="Marca de tiempo de la métrica.")

class FreqtradeBalanceData(BaseModel):
    """Esquema para información de balance de la cuenta en Freqtrade."""
    currency: str = Field(..., description="Moneda (ej. 'USDT', 'BTC').")
    total: float = Field(..., description="Cantidad total de la moneda.")
    available: float = Field(..., description="Cantidad disponible de la moneda.")
    used: float = Field(..., description="Cantidad usada de la moneda.")

# Unión de todos los tipos de mensajes para validación general
MCPMessage = RequestMessage | ResponseMessage | ErrorMessage | EventMessage | AcknowledgmentMessage
