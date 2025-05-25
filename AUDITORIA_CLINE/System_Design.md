# Diseño del Sistema - Bot_Arbitraje2105

## 1. Visión General del Sistema

El Bot_Arbitraje2105 es una plataforma de trading personal avanzada diseñada para operar con criptomonedas, enfocándose en estrategias de scalping, day trading y arbitraje. El sistema está construido para ser robusto, escalable y observador, integrando datos en tiempo real, análisis impulsado por IA y gestión de riesgos.

## 2. Componentes Principales

El sistema se compone de varios módulos y servicios interconectados, que pueden ser conceptualizados como un **Monolito Modular** o una colección de **Microservicios** que interactúan a través de APIs REST y WebSockets.

### 2.1. Servidores API y WebSocket
Existen varias iteraciones de servidores, lo que indica una evolución en el diseño:
*   **`basic_server.py`**: Un servidor inicial simple con FastAPI y WebSockets para simulación de datos de mercado y trading básico.
*   **`enhanced_api_server.py`**: Una versión mejorada que integra datos reales de Binance y una gestión de estado más sofisticada para el paper trading y la generación de señales.
*   **`production_server.py` / `enhanced_production_server.py`**: Las versiones de producción, que incorporan:
    *   Descubrimiento dinámico de puertos.
    *   Logging avanzado con rotación de archivos y envío de logs vía WebSocket.
    *   Un `ConnectionManager` robusto para WebSockets con heartbeats.
    *   Un `TradingEngine` centralizado para gestionar el estado del trading, portfolio, posiciones y trades.
    *   Integración con `SystemMonitor` para monitoreo de salud y métricas.
    *   Integración con `AdvancedRiskManager` para la gestión de riesgos.
    *   Manejo de datos de Binance en tiempo real con lógica de reconexión.

### 2.2. Motor de Trading Principal (`main.py`)
El archivo `main.py` actúa como el orquestador principal de la aplicación. Se encarga de:
*   Configuración de logging avanzado.
*   Validación de la configuración del entorno (variables de entorno).
*   Realización de health checks de inicio (conectividad a internet, API de Gemini).
*   Configuración de un contenedor de Inyección de Dependencias (`DIContainer`).
*   Inicialización del `AdvancedTradingEngine`, que encapsula la lógica de trading, estrategias y gestión de riesgos.
*   Configuración de manejadores de señales para un cierre elegante del sistema.

### 2.3. Cliente WebSocket de Binance (`binance_websocket.py`)
Este módulo es responsable de:
*   Conectarse a los streams de datos de Binance en tiempo real (tickers, klines, orderbook).
*   Manejar la reconexión robusta con backoff exponencial.
*   Procesar los datos recibidos y enviarlos a un callback (usado por los servidores API para broadcast a los clientes frontend).
*   Proporciona funciones de utilidad para análisis técnico básico (`calculate_rsi`, `is_bullish_signal`, `is_bearish_signal`).

## 3. Flujo de Datos General

1.  **Datos de Mercado**: `binance_websocket.py` se conecta a Binance, recibe datos en tiempo real.
2.  **Procesamiento de Datos**: Los datos de Binance son procesados por el `BinanceDataFeeder` (dentro de los servidores API/producción) y actualizan el `TradingEngine`.
3.  **Generación de Señales**: El `TradingEngine` (o `AdvancedTradingEngine` en `main.py`) utiliza los datos de mercado y la lógica de las estrategias (potencialmente impulsadas por IA como Google Gemini) para generar señales de trading.
4.  **Gestión de Riesgos**: Las señales y las órdenes son validadas por el `AdvancedRiskManager`.
5.  **Ejecución de Órdenes**: El `TradingEngine` simula la ejecución de órdenes (paper trading) y actualiza el estado del portfolio.
6.  **Comunicación Frontend**: Los servidores API/producción utilizan el `ConnectionManager` para transmitir datos de mercado, señales, actualizaciones de portfolio y logs del sistema a los clientes WebSocket (frontends).

## 4. Consideraciones de Diseño

*   **Modularidad**: El uso de directorios como `application/`, `domain/`, `infrastructure/` sugiere una clara separación de responsabilidades.
*   **Asincronía**: Amplio uso de `asyncio` para manejar operaciones concurrentes y no bloqueantes, esencial para el trading en tiempo real.
*   **Observabilidad**: Logging detallado y monitoreo del sistema (`SystemMonitor`) para visibilidad del estado operativo.
*   **Resiliencia**: Mecanismos de reconexión y reintentos para servicios externos (Binance) y reinicio del servidor.
*   **Inyección de Dependencias**: El `DIContainer` en `main.py` indica un diseño que facilita la prueba y el mantenimiento.

## Problema: Duplicidad de Servidores
Se observan múltiples archivos de servidor (`basic_server.py`, `enhanced_api_server.py`, `production_server.py`, `enhanced_production_server.py`). Si bien esto muestra una evolución, en un entorno de producción final, solo debería haber una implementación activa del servidor principal.
#Solución: Consolidación de Servidores
Identificar la versión final y más robusta (aparentemente `enhanced_production_server.py`) y eliminar o archivar las versiones anteriores para evitar confusiones y mantener una única fuente de verdad para el servidor de producción. Asegurarse de que `launch_production.py` apunte a la versión correcta.
