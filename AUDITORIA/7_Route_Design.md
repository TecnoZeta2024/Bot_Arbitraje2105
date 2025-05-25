# Diseño de Rutas - Bot_Arbitraje2105

## Visión General

El Bot_Arbitraje2105 implementa un sistema de enrutamiento organizado que sigue principios RESTful, combinado con endpoints WebSocket para comunicación en tiempo real. La estructura de rutas está diseñada para proporcionar una interfaz clara y consistente para diferentes funcionalidades del sistema, con una separación lógica basada en dominios y recursos.

## Estructura de Rutas

### Rutas HTTP Principales

#### Rutas Públicas

| Método | Ruta | Descripción | Componente |
|--------|------|-------------|------------|
| `GET` | `/` | Página de inicio/estado del sistema | `enhanced_api_server.py` |
| `GET` | `/api/health` | Verificación de estado del sistema | `enhanced_api_server.py` |
| `GET` | `/docs` | Documentación interactiva de la API (Swagger) | FastAPI automático |
| `GET` | `/redoc` | Documentación alternativa (ReDoc) | FastAPI automático |

#### Rutas de Autenticación

| Método | Ruta | Descripción | Componente |
|--------|------|-------------|------------|
| `POST` | `/api/auth/register` | Registro de nuevo usuario | (inferido) |
| `POST` | `/api/auth/login` | Inicio de sesión de usuario | (inferido) |
| `POST` | `/api/auth/refresh` | Renovación de token | (inferido) |
| `POST` | `/api/auth/logout` | Cierre de sesión | (inferido) |
| `GET` | `/api/auth/me` | Información del usuario actual | (inferido) |

#### Rutas de Trading y Operaciones

| Método | Ruta | Descripción | Componente |
|--------|------|-------------|------------|
| `GET` | `/api/portfolio` | Obtener resumen de cartera | `enhanced_api_server.py` |
| `GET` | `/api/trades` | Obtener historial de operaciones | `enhanced_api_server.py` |
| `POST` | `/api/trades` | Crear nueva operación | (inferido) |
| `GET` | `/api/trades/{id}` | Obtener detalles de operación específica | (inferido) |
| `DELETE` | `/api/trades/{id}` | Cancelar operación | (inferido) |
| `GET` | `/api/opportunities` | Listar oportunidades de arbitraje | (inferido) |
| `GET` | `/api/opportunities/{id}` | Detalles de oportunidad específica | (inferido) |
| `POST` | `/api/opportunities/{id}/execute` | Ejecutar oportunidad de arbitraje | (inferido) |

#### Rutas de Datos de Mercado

| Método | Ruta | Descripción | Componente |
|--------|------|-------------|------------|
| `GET` | `/api/market/pairs` | Listar pares de trading disponibles | (inferido) |
| `GET` | `/api/market/data/{symbol}` | Obtener datos de mercado para un símbolo | (inferido) |
| `GET` | `/api/market/orderbook/{symbol}` | Obtener orderbook de un símbolo | (inferido) |
| `GET` | `/api/market/history/{symbol}` | Obtener datos históricos de un símbolo | (inferido) |

#### Rutas de Configuración y Sistema

| Método | Ruta | Descripción | Componente |
|--------|------|-------------|------------|
| `GET` | `/api/config` | Obtener configuración actual del sistema | (inferido) |
| `PUT` | `/api/config` | Actualizar configuración del sistema | (inferido) |
| `GET` | `/api/system/status` | Estado detallado del sistema | (inferido) |
| `POST` | `/api/system/restart` | Reiniciar componentes del sistema | (inferido) |
| `GET` | `/api/logs` | Obtener logs del sistema | (inferido) |

#### Rutas de Estrategias

| Método | Ruta | Descripción | Componente |
|--------|------|-------------|------------|
| `GET` | `/api/strategies` | Listar estrategias disponibles | (inferido) |
| `POST` | `/api/strategies` | Crear nueva estrategia | (inferido) |
| `GET` | `/api/strategies/{id}` | Obtener detalles de estrategia | (inferido) |
| `PUT` | `/api/strategies/{id}` | Actualizar estrategia | (inferido) |
| `DELETE` | `/api/strategies/{id}` | Eliminar estrategia | (inferido) |
| `POST` | `/api/strategies/{id}/activate` | Activar estrategia | (inferido) |
| `POST` | `/api/strategies/{id}/deactivate` | Desactivar estrategia | (inferido) |

#### Rutas de Análisis y Reportes

| Método | Ruta | Descripción | Componente |
|--------|------|-------------|------------|
| `GET` | `/api/analysis/performance` | Obtener métricas de rendimiento | (inferido) |
| `GET` | `/api/analysis/risk` | Obtener métricas de riesgo | (inferido) |
| `GET` | `/api/reports` | Listar reportes disponibles | (inferido) |
| `GET` | `/api/reports/{id}` | Obtener reporte específico | (inferido) |
| `POST` | `/api/reports/generate` | Generar nuevo reporte | (inferido) |

### Endpoints WebSocket

| Ruta | Descripción | Componente |
|------|-------------|------------|
| `/ws` | Conexión WebSocket principal | `enhanced_api_server.py` |

### Canales WebSocket

Basado en el análisis del código, el sistema implementa un sistema de canales para WebSockets que permite a los clientes suscribirse a tipos específicos de actualizaciones:

| Canal | Descripción | Tipo de Datos |
|-------|-------------|---------------|
| `market_data` | Actualizaciones de datos de mercado | Precios, volúmenes, cambios |
| `trading_signal` | Señales de trading generadas | Recomendaciones de compra/venta |
| `portfolio_update` | Actualizaciones de cartera | Valor, P&L, posiciones |
| `trade_executed` | Notificaciones de operaciones ejecutadas | Detalles de trades |
| `system_metrics` | Métricas del sistema | Estadísticas de rendimiento |
| `orderbook_data` | Actualizaciones de orderbook | Órdenes de compra/venta |
| `kline_data` | Datos de velas (OHLC) | Datos para gráficos |

## Implementación de Rutas

### Router de FastAPI

El sistema utiliza FastAPI para la definición y gestión de rutas, que proporciona:
- Validación automática de parámetros
- Documentación interactiva (Swagger/OpenAPI)
- Tipado estático con Pydantic
- Soporte nativo para operaciones asíncronas

**Ejemplo de implementación (inferido):**

```python
# Configuración de router para rutas de trading
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import List, Optional

from ..dependencies import get_current_user, get_trading_service
from ..models import Trade, TradeCreate, TradeResponse

router = APIRouter(prefix="/api/trades", tags=["trades"])

@router.get("/", response_model=List[TradeResponse])
async def get_trades(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    symbol: Optional[str] = None,
    current_user = Depends(get_current_user),
    trading_service = Depends(get_trading_service)
):
    """Obtiene historial de operaciones con filtros opcionales"""
    return await trading_service.get_trades(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        symbol=symbol
    )

@router.post("/", response_model=TradeResponse, status_code=201)
async def create_trade(
    trade_data: TradeCreate,
    current_user = Depends(get_current_user),
    trading_service = Depends(get_trading_service)
):
    """Crea una nueva operación de trading"""
    return await trading_service.create_trade(
        user_id=current_user.id,
        trade_data=trade_data
    )

@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: str = Path(..., title="ID de la operación"),
    current_user = Depends(get_current_user),
    trading_service = Depends(get_trading_service)
):
    """Obtiene detalles de una operación específica"""
    trade = await trading_service.get_trade_by_id(trade_id)
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    # Verificar propiedad o permisos administrativos
    if trade.user_id != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized to access this trade")
    
    return trade
```

### Gestor de WebSockets

El sistema implementa un gestor de conexiones WebSocket para manejar la comunicación en tiempo real:

```python
# En enhanced_api_server.py
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connection established. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed. Total: {len(self.active_connections)}")

    async def broadcast_json(self, data: dict):
        if self.active_connections:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(data)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.disconnect(connection)
```

## Patrones de Diseño de Rutas

### 1. Patrón RESTful

El diseño de rutas sigue principios RESTful:
- Uso de sustantivos en plural para recursos (`/trades`, `/opportunities`)
- Operaciones CRUD mapeadas a métodos HTTP (GET, POST, PUT, DELETE)
- Uso de códigos de estado HTTP apropiados
- Jerarquía de recursos con IDs (`/strategies/{id}`)

### 2. Patrón de Versionado

Aunque no se implementa explícitamente, se infiere la posibilidad de versionado de API:
- Potencial para prefijos de versión (`/api/v1/...`)
- Estructura preparada para evolución

### 3. Patrón de Middleware

El sistema utiliza middlewares para funcionalidades transversales:
- Autenticación y autorización
- Logging y monitoreo
- Manejo de errores
- Rate limiting

### 4. Patrón de WebSockets para Tiempo Real

Implementación de patrón de publicación-suscripción para datos en tiempo real:
- Conexiones persistentes
- Canales temáticos
- Broadcast selectivo

## Estrategias de Seguridad en Rutas

### 1. Protección de Rutas

- Middleware de autenticación para rutas protegidas
- Verificación de permisos basada en roles
- Validación de tokens JWT

### 2. Validación de Entrada

- Esquemas Pydantic para validación de datos
- Sanitización de parámetros
- Límites en tamaño de solicitudes

### 3. Rate Limiting

- Limitación de solicitudes por IP/usuario
- Prevención de ataques de fuerza bruta
- Throttling para APIs intensivas

## Gestión de Errores

El sistema implementa una gestión de errores consistente:

- Códigos de estado HTTP adecuados
- Mensajes de error estructurados
- Manejo centralizado de excepciones

**Ejemplo de estructura de error (inferido):**
```json
{
  "status": "error",
  "code": "INVALID_TRADE_PARAMS",
  "message": "Invalid trading parameters provided",
  "details": {
    "symbol": "Symbol BTCUSD is not supported",
    "quantity": "Quantity must be greater than minimum order size (0.001)"
  },
  "timestamp": "2023-04-15T14:25:30.123Z"
}
```

## Documentación de API

El sistema aprovecha las capacidades de documentación automática de FastAPI:

- Documentación OpenAPI/Swagger en `/docs`
- Documentación ReDoc en `/redoc`
- Anotaciones de tipo para parámetros y respuestas
- Ejemplos y descripciones de endpoints

## Problemas y Recomendaciones

## Problema: Inconsistencia en la estructura de rutas, origen: comparación entre enhanced_api_server.py y la estructura inferida ##
#Solución: Estandarizar la estructura de rutas siguiendo una convención clara y consistente, organizando los endpoints por dominio y recurso con una jerarquía coherente #

## Problema: Falta de versionado explícito de API, origen: análisis de código ##
#Solución: Implementar versionado explícito de API (ej. /api/v1/) para permitir evolución sin romper compatibilidad, facilitando la transición para los clientes durante actualizaciones #

## Problema: Potencial exposición de endpoints sensibles sin autenticación, origen: enhanced_api_server.py ##
#Solución: Revisar todos los endpoints y aplicar middleware de autenticación a rutas sensibles, asegurando que solo los usuarios autorizados puedan acceder a funcionalidades críticas #

## Problema: Manejo inconsistente de WebSockets, origen: implementación actual en enhanced_api_server.py ##
#Solución: Refactorizar el sistema de WebSockets para utilizar un diseño más modular con manejadores específicos por tipo de mensaje y mejor gestión de suscripciones #
