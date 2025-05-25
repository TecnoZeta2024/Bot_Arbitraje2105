# Diseño de Rutas (Route Design) - Bot_Arbitraje2105

El Bot_Arbitraje2105 expone sus funcionalidades a través de una combinación de endpoints RESTful y un único endpoint WebSocket, utilizando el framework FastAPI. El diseño de rutas ha evolucionado a lo largo de las diferentes versiones del servidor, añadiendo más granularidad y funcionalidades.

## 1. Convenciones Generales

*   **Prefijo `/api`**: La mayoría de los endpoints RESTful utilizan el prefijo `/api` para agrupar las funcionalidades de la API.
*   **Verbos HTTP**: Se utilizan los verbos HTTP estándar (GET, POST) para las operaciones REST.
*   **WebSocket Único**: Un único endpoint `/ws` se utiliza para toda la comunicación en tiempo real, multiplexando diferentes tipos de mensajes a través de este canal.

## 2. Rutas por Versión del Servidor

### 2.1. `basic_server.py` (Versión Básica)

Este servidor presenta las rutas más fundamentales:

*   **GET `/`**
    *   **Propósito**: Endpoint raíz para verificar que el servidor está en funcionamiento.
    *   **Respuesta**: Un mensaje simple de "Servidor Básico de Trading en funcionamiento".
*   **GET `/api/health`**
    *   **Propósito**: Proporciona un chequeo de salud básico del servidor.
    *   **Respuesta**: Estado "OK", versión, número de conexiones WebSocket activas, y estado de `trading_active` y `portfolio_value`.
*   **WebSocket `/ws`**
    *   **Propósito**: Canal de comunicación bidireccional en tiempo real.
    *   **Funcionalidad**: Maneja conexiones, desconexiones, broadcast de datos de mercado simulados, y recibe mensajes para control de trading (`trading_control`) y ejecución de órdenes simuladas (`execute_order`).

### 2.2. `enhanced_api_server.py` (Versión Mejorada)

Esta versión expande las rutas, añadiendo más funcionalidades de consulta y control:

*   **GET `/`**
    *   **Propósito**: Similar al básico, pero con un mensaje de bienvenida más descriptivo y listado de características.
*   **GET `/api/health`**
    *   **Propósito**: Chequeo de salud más detallado.
    *   **Respuesta**: Incluye estado de Binance y número de señales generadas, además de la información básica.
*   **GET `/api/portfolio`**
    *   **Propósito**: Obtener un resumen del estado actual del portfolio.
    *   **Respuesta**: Valor total, PnL diario, balance disponible, posiciones, etc.
*   **GET `/api/trades`**
    *   **Propósito**: Obtener una lista de los trades recientes.
    *   **Parámetros**: `limit` (opcional) para controlar el número de trades.
*   **WebSocket `/ws`**
    *   **Propósito**: Canal de comunicación en tiempo real mejorado.
    *   **Funcionalidad**: Similar al básico, pero con integración de datos reales de Binance, manejo de suscripciones (`subscribe`), y la capacidad de enviar datos de orderbook y klines.

### 2.3. `production_server.py` / `enhanced_production_server.py` (Versión de Producción Final)

Estas versiones representan el diseño de rutas más completo y robusto:

*   **GET `/`**
    *   **Propósito**: Endpoint raíz con información detallada del servidor, versión, estado y una lista exhaustiva de características y endpoints disponibles.
*   **GET `/api/health`**
    *   **Propósito**: Health check exhaustivo.
    *   **Respuesta**: Incluye métricas del servidor (uptime), estado del sistema de trading, conexiones, portfolio, trades, señales, y el estado de servicios como Binance y SystemMonitor.
*   **GET `/api/portfolio`**
    *   **Propósito**: Obtener el estado actual del portfolio.
    *   **Respuesta**: Objeto `Portfolio` completo.
*   **GET `/api/trades`**
    *   **Propósito**: Obtener una lista de los trades recientes.
    *   **Parámetros**: `limit` (opcional).
*   **GET `/api/signals`**
    *   **Propósito**: Obtener una lista de las señales de trading recientes generadas por el sistema.
    *   **Parámetros**: `limit` (opcional).
*   **POST `/api/trading/control`**
    *   **Propósito**: Controlar el estado operativo del motor de trading.
    *   **Parámetros**: `action` (string: "start", "pause", "stop", "reset").
    *   **Respuesta**: Estado de éxito y el nuevo estado del motor de trading.
*   **WebSocket `/ws`**
    *   **Propósito**: Canal de comunicación bidireccional en tiempo real con funcionalidades de producción.
    *   **Funcionalidad**: Manejo de `client_id` único, envío de mensajes de bienvenida y estado inicial, manejo de suscripciones (`subscribe`), ejecución de órdenes (`execute_order`), y confirmación de heartbeats (`heartbeat_ack`). Difunde datos de mercado, señales, actualizaciones de portfolio, métricas del sistema y alertas de riesgo.

## 3. Diagrama de Rutas (Conceptual)

```mermaid
graph TD
    subgraph REST API Endpoints
        A[GET /]
        B[GET /api/health]
        C[GET /api/portfolio]
        D[GET /api/trades]
        E[GET /api/signals]
        F[POST /api/trading/control]
    end

    subgraph WebSocket Endpoint
        G[WS /ws]
    end

    Client_Frontend --> A
    Client_Frontend --> B
    Client_Frontend --> C
    Client_Frontend --> D
    Client_Frontend --> E
    Client_Frontend --> F

    Client_Frontend --> G: Real-time Data & Control
    G --> Client_Frontend: Market Data, Signals, Portfolio, Logs, Metrics
```

## Problema: Consistencia en la documentación de rutas
Aunque FastAPI genera documentación automáticamente, la auditoría revela que las descripciones y ejemplos de las rutas no están completamente estandarizados o detallados en los comentarios de código para todas las versiones del servidor.
#Solución: Mejorar la Documentación de la API
Asegurar que todos los endpoints REST y los tipos de mensajes WebSocket estén completamente documentados utilizando docstrings y los parámetros de FastAPI (e.g., `description`, `summary`, `response_model`, `status_code`, `json_schema_extra` para ejemplos). Esto facilitará el uso y mantenimiento de la API para desarrolladores frontend y otros consumidores.
