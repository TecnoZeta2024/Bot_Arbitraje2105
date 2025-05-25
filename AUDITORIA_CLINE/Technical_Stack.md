# Pila Tecnológica (Technical Stack) - Bot_Arbitraje2105

El Bot_Arbitraje2105 está construido sobre una pila tecnológica moderna y robusta, predominantemente basada en Python, diseñada para el desarrollo de aplicaciones asíncronas de alto rendimiento y en tiempo real.

## 1. Lenguaje de Programación

*   **Python 3.9+**: El lenguaje principal de desarrollo, elegido por su versatilidad, ecosistema de librerías y soporte para programación asíncrona.

## 2. Frameworks y Librerías Principales

### 2.1. Backend y API

*   **FastAPI**: Framework web de alto rendimiento para construir APIs REST y WebSockets. Proporciona tipado estático, validación de datos automática y documentación interactiva (Swagger UI/ReDoc).
*   **Uvicorn**: Servidor ASGI (Asynchronous Server Gateway Interface) que ejecuta la aplicación FastAPI.
*   **Pydantic**: Utilizado para la definición de modelos de datos y la validación de esquemas, asegurando la integridad de los datos que entran y salen de la API.

### 2.2. Comunicación en Tiempo Real

*   **`websockets`**: Librería Python para construir clientes y servidores WebSocket, utilizada para la conexión con Binance y la comunicación con los clientes frontend.
*   **`aiohttp`**: Librería HTTP asíncrona para Python, utilizada para realizar llamadas REST a la API de Binance (e.g., para obtener estadísticas de 24 horas).
*   **`asyncio`**: Módulo estándar de Python para escribir código concurrente utilizando la sintaxis `async/await`, fundamental para manejar múltiples conexiones y flujos de datos en tiempo real de manera eficiente.

### 2.3. Inteligencia Artificial y Análisis

*   **`google-generativeai`**: Librería para interactuar con la API de Google Gemini, utilizada para análisis impulsado por IA (mencionado en `main.py`).

### 2.4. Gestión de Configuración y Entorno

*   **`python-dotenv`**: Para cargar variables de entorno desde archivos `.env`, facilitando la gestión de configuraciones sensibles y específicas del entorno.

### 2.5. Logging y Monitoreo

*   **`logging` (Módulo estándar de Python)**: Utilizado para la configuración de un sistema de logging robusto con rotación de archivos y handlers personalizados (como `WebSocketLoggingHandler`).
*   **`SystemMonitor` (Interno)**: Componente para el monitoreo de la salud y métricas del sistema.
*   **`AdvancedRiskManager` (Interno)**: Componente para la gestión avanzada de riesgos.

### 2.6. Utilidades y Otros

*   **`json`**: Módulo estándar para la serialización y deserialización de datos JSON.
*   **`time` / `datetime`**: Módulos estándar para la gestión de tiempo y fechas.
*   **`random`**: Módulo estándar para la generación de números aleatorios (usado en simulaciones).
*   **`socket`**: Módulo estándar para operaciones de red (usado para encontrar puertos disponibles).
*   **`pathlib` / `os` / `sys`**: Módulos estándar para la manipulación de rutas de archivos y el entorno del sistema.
*   **`enum`**: Módulo estándar para definir conjuntos de constantes con nombres (e.g., `TradingState`, `SignalAction`).
*   **`uuid`**: Módulo estándar para la generación de IDs únicos (usado para `client_id` en WebSockets).

## 3. Herramientas y Conceptos Adicionales

*   **Inyección de Dependencias (DI)**: Implementado a través de un `DIContainer` para mejorar la modularidad y testabilidad.
*   **Contenedorización (Docker)**: La presencia de un `Dockerfile` sugiere que la aplicación está diseñada para ser desplegada en contenedores.
*   **Git**: Para control de versiones.

## Problema: Dependencia de `binance_websocket1` en `enhanced_api_server.py`
El archivo `src/enhanced_api_server.py` importa `src.binance_websocket1` en lugar de `src.binance_websocket`. Esto es un error tipográfico que probablemente causa un `ModuleNotFoundError` si `binance_websocket1.py` no existe.
#Solución: Corregir la Importación
Cambiar `from src.binance_websocket1 import ...` a `from src.binance_websocket import ...` en `src/enhanced_api_server.py`. Esto asegura que el servidor utilice el módulo correcto para la conexión con Binance.
