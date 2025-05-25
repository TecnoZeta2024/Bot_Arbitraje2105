# Diseño de API (API Design) - Bot_Arbitraje2105

El diseño de la API del Bot_Arbitraje2105 se basa en el framework FastAPI, que facilita la creación de endpoints RESTful y la gestión de comunicación WebSocket. La API está diseñada para ser intuitiva, tipada y auto-documentada, utilizando modelos Pydantic para la validación y serialización de datos.

## 1. Principios de Diseño

*   **RESTful para Consultas y Control**: Los endpoints HTTP (GET, POST) se utilizan para operaciones de consulta de estado (portfolio, trades, señales) y control del sistema (iniciar/detener trading).
*   **WebSocket para Tiempo Real**: Un único endpoint WebSocket (`/ws`) maneja toda la comunicación bidireccional en tiempo real, incluyendo datos de mercado, señales, actualizaciones de portfolio y logs.
*   **Modelos de Datos Fuertemente Tipados**: El uso extensivo de Pydantic asegura que los datos de entrada y salida se ajusten a esquemas predefinidos, proporcionando validación automática y mejorando la claridad de la API.
*   **Auto-documentación**: FastAPI genera automáticamente documentación interactiva (Swagger UI/ReDoc) a partir del código, lo que facilita la exploración y el uso de la API.

## 2. Modelos de Datos Clave (Pydantic)

Los siguientes modelos Pydantic definen la estructura de los datos intercambiados a través de la API y WebSockets:

*   **`MarketData`**: Representa los datos de mercado en tiempo real para un símbolo específico.
    ```python
    class MarketData(BaseModel):
        symbol: str
        price: float
        volume24h: float
        changePercent24h: float
        high24h: Optional[float] = None
        low24h: Optional[float] = None
        timestamp: float
    ```
*   **`TradingSignal`**: Representa una señal de trading generada por el sistema.
    ```python
    class TradingSignal(BaseModel):
        id: str
        symbol: str
        action: SignalAction # Enum: BUY, SELL, HOLD
        price: float
        quantity: Optional[float] = Field(default=0.001, gt=0)
        strategy: str
        confidence: float
        reasoning: str
        riskLevel: str = "MEDIUM"
        timestamp: float
    ```
*   **`Position`**: Representa una posición de trading abierta.
    ```python
    class Position(BaseModel):
        id: str
        symbol: str
        side: str # LONG, SHORT
        quantity: float
        entryPrice: float
        currentPrice: float
        unrealizedPnL: float
        unrealizedPnLPercent: float
        realizedPnL: float = 0
        stopLoss: Optional[float] = None
        takeProfit: Optional[float] = None
        status: str = "OPEN"
        timestamp: float
    ```
*   **`Trade`**: Representa un trade ejecutado.
    ```python
    class Trade(BaseModel):
        id: str
        symbol: str
        side: str # BUY, SELL
        quantity: float
        price: float
        fee: float
        pnl: float
        pnlPercent: float
        strategy: str
        timestamp: float
    ```
*   **`Portfolio`**: Representa el estado general del portfolio del usuario.
    ```python
    class Portfolio(BaseModel):
        totalValue: float
        totalPnL: float
        totalPnLPercent: float
        availableBalance: float
        dailyPnL: float
        positions: List[Position] = []
        winRate: float = 0
        totalTrades: int = 0
        timestamp: float
    ```
*   **`OrderBook`**: Representa los datos del libro de órdenes (bids y asks).
    ```python
    class OrderBook(BaseModel):
        symbol: str
        bids: List[List[float]] # [price, quantity]
        asks: List[List[float]] # [price, quantity]
        timestamp: float
    ```

## 3. Endpoints RESTful

Los endpoints RESTful proporcionan acceso síncrono a la información del sistema y control sobre el motor de trading.

*   **`GET /`**: Información general del servidor.
*   **`GET /api/health`**: Chequeo de salud detallado del sistema.
*   **`GET /api/portfolio`**: Recupera el objeto `Portfolio` actual.
*   **`GET /api/trades?limit={int}`**: Recupera una lista de los trades recientes.
*   **`GET /api/signals?limit={int}`**: Recupera una lista de las señales de trading recientes.
*   **`POST /api/trading/control`**:
    *   **Cuerpo de la Solicitud**: `{"action": "start" | "pause" | "stop" | "reset"}`
    *   **Respuesta**: `{"status": "success" | "error", "state": "IDLE" | "RUNNING" | ...}`

## 4. Diseño del Endpoint WebSocket (`/ws`)

El endpoint WebSocket es el canal principal para la comunicación en tiempo real y las interacciones dinámicas.

### 4.1. Mensajes del Cliente al Servidor (Entrantes)

Los clientes envían mensajes JSON con un campo `type` para indicar la acción:

*   **`{"type": "subscribe", "channels": ["market_data", "trading_signals"]}`**: Suscribe al cliente a streams de datos específicos.
*   **`{"type": "trading_control", "action": "start"}`**: Inicia, pausa o detiene el motor de trading.
*   **`{"type": "execute_order", "symbol": "BTCUSDT", "side": "BUY", "quantity": 0.001}`**: Simula la ejecución de una orden.
*   **`{"type": "heartbeat_ack", "timestamp": 1678886400.0}`**: Confirmación de recepción del heartbeat del servidor.

### 4.2. Mensajes del Servidor al Cliente (Salientes)

El servidor envía mensajes JSON con un campo `type` para indicar el tipo de actualización:

*   **`{"type": "connection_ack", ...}`**: Confirmación de conexión exitosa.
*   **`{"type": "portfolio_update", "data": {...}}`**: Actualizaciones del objeto `Portfolio`.
*   **`{"type": "market_data", "data": {...}}`**: Datos de mercado en tiempo real (`MarketData`).
*   **`{"type": "trading_status", "data": {"status": "ACTIVE", ...}}`**: Cambios en el estado del motor de trading.
*   **`{"type": "trade_executed", "data": {...}}`**: Detalles de un `Trade` ejecutado.
*   **`{"type": "trading_signal", "data": {...}}`**: Una nueva `TradingSignal` generada.
*   **`{"type": "system_metrics", "data": {...}}`**: Métricas de monitoreo del sistema.
*   **`{"type": "system_alert", "level": "WARNING", "message": "...", ...}`**: Logs y alertas del sistema.
*   **`{"type": "orderbook_update", "data": {...}}`**: Actualizaciones del libro de órdenes (`OrderBook`).
*   **`{"type": "kline_data", "data": {...}}`**: Datos de velas (candlesticks).
*   **`{"type": "heartbeat", "timestamp": 1678886400.0}`**: Mensaje de heartbeat para mantener la conexión activa.
*   **`{"type": "error", "message": "..."}`**: Mensajes de error específicos para el cliente.

## 5. Consideraciones de Diseño

*   **Coherencia de Datos**: El uso de Pydantic en ambos lados (solicitudes y respuestas, mensajes WebSocket) garantiza que la estructura de los datos sea consistente y validada.
*   **Extensibilidad**: El diseño permite añadir fácilmente nuevos endpoints REST o tipos de mensajes WebSocket para futuras funcionalidades.
*   **Eficiencia**: La comunicación en tiempo real a través de un único WebSocket reduce la sobrecarga de conexiones HTTP.

## Problema: Falta de versionado explícito en la API
Aunque el servidor tiene un campo `version` (e.g., "3.1.0"), no hay un versionado explícito en las rutas de la API (e.g., `/api/v1/health`). Esto puede dificultar la evolución de la API sin romper la compatibilidad con clientes existentes.
#Solución: Implementar Versionado de API
Se recomienda añadir un prefijo de versión a las rutas de la API (e.g., `/api/v1/health`, `/api/v2/portfolio`). Esto permite introducir cambios incompatibles en futuras versiones de la API sin afectar a los clientes que utilizan versiones anteriores. FastAPI soporta la creación de routers con prefijos, lo que facilita esta implementación.
