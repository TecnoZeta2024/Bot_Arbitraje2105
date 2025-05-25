# Diseño de API - Bot_Arbitraje2105

## Visión General de la API

El Bot_Arbitraje2105 implementa una API moderna y bien estructurada que sigue principios de diseño REST combinados con capacidades WebSocket para comunicación en tiempo real. La API está diseñada para proporcionar acceso a todas las funcionalidades del sistema de trading, desde la obtención de datos de mercado hasta la ejecución de operaciones y la gestión de estrategias.

## Principios de Diseño de API

### 1. Arquitectura REST

La API sigue los principios de Representational State Transfer (REST):
- Recursos identificados por URLs
- Operaciones CRUD mapeadas a métodos HTTP estándar
- Uso de códigos de estado HTTP apropiados
- Formato JSON para intercambio de datos
- Diseño sin estado (stateless)

### 2. Comunicación en Tiempo Real

Para datos que requieren actualización inmediata, la API implementa:
- WebSockets para comunicación bidireccional
- Patrón de publicación-suscripción para datos de mercado
- Canales temáticos para diferentes tipos de actualización

### 3. Seguridad y Autenticación

La API implementa mecanismos de seguridad robustos:
- Autenticación basada en JWT (JSON Web Tokens)
- Control de acceso basado en roles (RBAC)
- HTTPS para comunicación cifrada
- Validación y sanitización de datos de entrada

## Especificación OpenAPI

La API está documentada utilizando la especificación OpenAPI (anteriormente Swagger), proporcionando:
- Documentación interactiva
- Esquemas de solicitud y respuesta
- Ejemplos de uso
- Descripción de errores

### Ejemplo de Definición OpenAPI (Inferido)

```yaml
openapi: 3.0.0
info:
  title: Bot de Arbitraje Triangular API
  description: API para el sistema de trading Bot_Arbitraje2105
  version: 2.0.0
servers:
  - url: http://localhost:8000
    description: Servidor de desarrollo
  - url: https://api.tradingbot.example.com
    description: Servidor de producción
tags:
  - name: auth
    description: Autenticación y gestión de usuarios
  - name: trading
    description: Operaciones de trading
  - name: market
    description: Datos de mercado
  - name: system
    description: Gestión y configuración del sistema
paths:
  /api/auth/login:
    post:
      tags:
        - auth
      summary: Iniciar sesión de usuario
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  format: password
      responses:
        '200':
          description: Login exitoso
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token:
                    type: string
                  refresh_token:
                    type: string
                  token_type:
                    type: string
                    example: bearer
        '401':
          description: Credenciales inválidas
  
  /api/opportunities:
    get:
      tags:
        - trading
      summary: Obtener oportunidades de arbitraje
      security:
        - bearerAuth: []
      parameters:
        - in: query
          name: status
          schema:
            type: string
            enum: [DETECTED, APPROVED, PENDING, EXECUTING, COMPLETED]
        - in: query
          name: min_profit
          schema:
            type: number
            format: float
        - in: query
          name: limit
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: Lista de oportunidades
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Opportunity'
        '401':
          description: No autenticado
```

## Recursos de API y Endpoints

### 1. Autenticación y Usuarios

| Endpoint | Método | Descripción | Request Body | Response |
|----------|--------|-------------|--------------|----------|
| `/api/auth/register` | POST | Registro de usuario | `{email, password, name}` | `{user_id, email, role}` |
| `/api/auth/login` | POST | Inicio de sesión | `{email, password}` | `{access_token, refresh_token}` |
| `/api/auth/refresh` | POST | Renovar token | `{refresh_token}` | `{access_token}` |
| `/api/auth/me` | GET | Info de usuario actual | - | `{user_id, email, role, ...}` |

### 2. Oportunidades de Arbitraje

| Endpoint | Método | Descripción | Request Body/Params | Response |
|----------|--------|-------------|---------------------|----------|
| `/api/opportunities` | GET | Listar oportunidades | Query params: status, limit | Array de oportunidades |
| `/api/opportunities/{id}` | GET | Detalle de oportunidad | Path param: id | Detalles completos |
| `/api/opportunities/{id}/approve` | POST | Aprobar oportunidad | Path param: id | Resultado de aprobación |
| `/api/opportunities/{id}/execute` | POST | Ejecutar oportunidad | Path param: id | Resultado de ejecución |

### 3. Operaciones de Trading

| Endpoint | Método | Descripción | Request Body/Params | Response |
|----------|--------|-------------|---------------------|----------|
| `/api/trades` | GET | Historial de operaciones | Query params: symbol, limit | Array de operaciones |
| `/api/trades` | POST | Crear operación manual | `{symbol, side, quantity, ...}` | Detalles de operación |
| `/api/trades/{id}` | GET | Detalle de operación | Path param: id | Detalles completos |
| `/api/trades/{id}/cancel` | POST | Cancelar operación | Path param: id | Resultado de cancelación |

### 4. Datos de Mercado

| Endpoint | Método | Descripción | Request Body/Params | Response |
|----------|--------|-------------|---------------------|----------|
| `/api/market/pairs` | GET | Pares disponibles | Query params: exchange | Array de pares |
| `/api/market/data/{symbol}` | GET | Datos de símbolo | Path param: symbol | Datos actuales |
| `/api/market/history/{symbol}` | GET | Datos históricos | Path: symbol, Query: interval, limit | Serie temporal |
| `/api/market/orderbook/{symbol}` | GET | Orderbook | Path param: symbol | Órdenes actuales |

### 5. Estrategias y Configuración

| Endpoint | Método | Descripción | Request Body/Params | Response |
|----------|--------|-------------|---------------------|----------|
| `/api/strategies` | GET | Listar estrategias | Query: active | Array de estrategias |
| `/api/strategies` | POST | Crear estrategia | `{name, type, params, ...}` | Estrategia creada |
| `/api/strategies/{id}` | PUT | Actualizar estrategia | `{params, active, ...}` | Estrategia actualizada |
| `/api/config` | GET | Configuración del sistema | - | Configuración actual |
| `/api/config` | PUT | Actualizar configuración | `{key: value, ...}` | Configuración actualizada |

### 6. Análisis y Reportes

| Endpoint | Método | Descripción | Request Body/Params | Response |
|----------|--------|-------------|---------------------|----------|
| `/api/portfolio` | GET | Resumen de cartera | - | Estado actual de la cartera |
| `/api/analysis/performance` | GET | Métricas de rendimiento | Query: period | Métricas calculadas |
| `/api/analysis/risk` | GET | Análisis de riesgo | Query: period | Métricas de riesgo |
| `/api/reports` | POST | Generar reporte | `{type, params, ...}` | Reporte generado |

## API WebSocket

La API WebSocket permite comunicación bidireccional en tiempo real para datos que requieren actualizaciones frecuentes.

### Endpoint Principal

```
ws://hostname:port/ws
```

### Protocolo de Comunicación

#### Conexión Inicial

Al establecer la conexión, el cliente recibe un mensaje de confirmación:

```json
{
  "type": "connection_ack",
  "message": "Connected to enhanced trading server",
  "timestamp": 1681569012.456,
  "features": ["real_binance_data", "ai_signals", "trading_controls"]
}
```

#### Suscripción a Canales

El cliente puede suscribirse a canales específicos:

```json
// Cliente -> Servidor
{
  "type": "subscribe",
  "channels": ["market_data", "trading_signal", "portfolio_update"]
}

// Servidor -> Cliente (confirmación)
{
  "type": "subscription_ack",
  "status": "Subscribed",
  "channels": ["market_data", "trading_signal", "portfolio_update"]
}
```

#### Tipos de Mensajes

**Datos de Mercado:**
```json
{
  "type": "market_data",
  "data": {
    "symbol": "BTCUSDT",
    "price": 29876.45,
    "volume24h": 1254.78,
    "changePercent24h": 2.34,
    "high24h": 30245.67,
    "low24h": 29456.78,
    "timestamp": 1681569045.789
  }
}
```

**Señales de Trading:**
```json
{
  "type": "trading_signal",
  "data": {
    "id": "signal_1681569078",
    "symbol": "ETHUSDT",
    "action": "BUY",
    "price": 1876.23,
    "strategy": "BullishMomentum",
    "confidence": 75.5,
    "reasoning": "Strong upward momentum with high volume",
    "timestamp": 1681569078.123
  }
}
```

**Actualización de Cartera:**
```json
{
  "type": "portfolio_update",
  "data": {
    "totalValue": 12567.89,
    "dailyPnL": 234.56,
    "totalPnL": 876.54,
    "totalPnLPercent": 7.45,
    "availableBalance": 5432.10,
    "positions": [...],
    "totalTrades": 124,
    "winRate": 68.5
  }
}
```

## Modelos de Datos

La API utiliza modelos de datos consistentes para solicitudes y respuestas, definidos utilizando Pydantic para validación y serialización.

### Ejemplos de Modelos Principales

#### Modelo de Oportunidad

```python
class OpportunityResponse(BaseModel):
    opportunity_id: str
    base_currency: str
    intermediate_currency: str
    quote_currency: str
    estimated_profit_percentage: float
    required_capital: float
    expected_profit: float
    detection_timestamp: datetime
    status: str
    expiry_timestamp: Optional[datetime] = None
    confidence_score: Optional[float] = None
    risk_score: Optional[float] = None
    
    class Config:
        schema_extra = {
            "example": {
                "opportunity_id": "opp_16815690123",
                "base_currency": "BTC",
                "intermediate_currency": "ETH",
                "quote_currency": "USDT",
                "estimated_profit_percentage": 0.45,
                "required_capital": 1000.00,
                "expected_profit": 4.50,
                "detection_timestamp": "2023-04-15T12:30:45Z",
                "status": "DETECTED",
                "expiry_timestamp": "2023-04-15T12:31:45Z",
                "confidence_score": 0.85,
                "risk_score": 0.25
            }
        }
```

#### Modelo de Operación

```python
class TradeResponse(BaseModel):
    id: str
    symbol: str
    side: str  # BUY, SELL
    quantity: float
    price: float
    pnl: Optional[float] = None
    strategy: str
    timestamp: datetime
    status: str
    
    class Config:
        schema_extra = {
            "example": {
                "id": "trade_16815695678",
                "symbol": "BTCUSDT",
                "side": "BUY",
                "quantity": 0.05,
                "price": 29876.45,
                "pnl": 45.67,
                "strategy": "Manual",
                "timestamp": "2023-04-15T12:45:30Z",
                "status": "COMPLETED"
            }
        }
```

## Autenticación y Seguridad

### Autenticación JWT

La API utiliza JWT (JSON Web Tokens) para autenticación:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Control de Acceso por Roles

Se implementa RBAC (Role-Based Access Control) para diferentes niveles de acceso:

| Rol | Permisos |
|-----|----------|
| ADMIN | Acceso completo a todas las funcionalidades |
| TRADER | Ejecución de operaciones, gestión de estrategias, lectura de datos |
| ANALYST | Lectura de datos, generación de reportes, sin ejecución |
| VIEWER | Solo lectura de datos básicos y dashboards |

### Rate Limiting

Se implementa limitación de tasas para prevenir abusos:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1681570000
```

## Gestión de Errores

La API proporciona respuestas de error consistentes y descriptivas:

```json
{
  "status": "error",
  "code": "INSUFFICIENT_BALANCE",
  "message": "Insufficient balance to execute this operation",
  "details": {
    "required": 1000.0,
    "available": 876.54
  },
  "timestamp": "2023-04-15T14:25:30.123Z"
}
```

### Códigos de Estado HTTP

| Código | Significado | Uso |
|--------|-------------|-----|
| 200 | OK | Solicitud exitosa |
| 201 | Created | Recurso creado exitosamente |
| 400 | Bad Request | Parámetros inválidos o faltantes |
| 401 | Unauthorized | Autenticación faltante o inválida |
| 403 | Forbidden | Sin permisos para el recurso |
| 404 | Not Found | Recurso no encontrado |
| 409 | Conflict | Conflicto con el estado actual |
| 429 | Too Many Requests | Excedido límite de solicitudes |
| 500 | Internal Server Error | Error interno del servidor |

## Versionado de API

El sistema no implementa versionado explícito en la URL, pero está preparado para evolucionar mediante:

- Headers de aceptación (`Accept: application/json; version=2.0`)
- Potencial para agregar prefijos de versión en el futuro (`/api/v2/...`)

## Problemas y Recomendaciones

## Problema: Falta de versionado explícito en la API, origen: análisis de estructura de rutas ##
#Solución: Implementar versionado explícito en la URL (ej. /api/v1/) para facilitar la evolución de la API sin romper compatibilidad con clientes existentes #

## Problema: Documentación incompleta de la API, origen: ausencia de especificación OpenAPI completa ##
#Solución: Generar y mantener una especificación OpenAPI completa que documente todos los endpoints, parámetros, modelos y ejemplos, facilitando la integración con clientes #

## Problema: Inconsistencia en formatos de respuesta, origen: análisis de código ##
#Solución: Estandarizar los formatos de respuesta en toda la API, utilizando estructuras consistentes para éxito y error, con campos obligatorios como "status" y tipos de datos uniformes #

## Problema: Ausencia de paginación estandarizada, origen: implementación de endpoints de listado ##
#Solución: Implementar una estrategia de paginación consistente para todos los endpoints que devuelven colecciones, incluyendo metadatos de paginación (total, página actual, páginas totales) #
