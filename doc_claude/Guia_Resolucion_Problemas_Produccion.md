# Guía de Resolución de Problemas y Puesta en Producción - Bot Arbitraje 2105

## Índice
1.  Introducción
2.  Principios Fundamentales de Ingeniería de Software
3.  Metodología de Depuración
4.  Gestión de Dependencias y Librerías
5.  Pruebas y Observabilidad
6.  Puesta en Producción y Enfoque 'Frontend First'
7.  Troubleshooting Común
8.  Conclusión

## 1. Introducción
Este documento sirve como una guía integral para la resolución de problemas (debugging) y la implementación de mejores prácticas para la puesta en producción de la aplicación Bot Arbitraje 2105. Dada la complejidad del sistema, que abarca trading, inteligencia artificial, bases de datos y un dashboard interactivo, es crucial adoptar un enfoque metódico y proactivo para asegurar la robustez, eficiencia y fiabilidad del software. Se enfatizará la estrategia de 'Frontend First Visibility' para una detección temprana de problemas y una gestión eficiente de las dependencias de librerías, incluyendo el uso mandatorio de la herramienta 'context7'.

## 2. Principios Fundamentales de Ingeniería de Software
La arquitectura y el desarrollo del Bot Arbitraje 2105 se adhieren a principios de ingeniería de software probados para garantizar un código limpio, mantenible y escalable.

### 2.1. Separación de Responsabilidades (Separation of Concerns)
El sistema está diseñado con módulos y capas bien definidas, cada una con una responsabilidad única. Por ejemplo, la lógica de dominio (`src/domain/`), la infraestructura (`src/infrastructure/`) y la aplicación (`src/application/`) están claramente separadas, lo que facilita la comprensión, el desarrollo y la depuración.

### 2.2. Principio de Responsabilidad Única (Single Responsibility Principle - SRP)
Cada clase o módulo tiene una única razón para cambiar. Esto se observa en la granularidad de los servicios y entidades, como `domain/entities/arbitrage_operation.py` o `application/services/opportunity_service.py`, que se centran en una tarea específica.

### 2.3. Principio Abierto/Cerrado (Open/Closed Principle - OCP)
El diseño favorece la extensión sin necesidad de modificar el código existente. Esto se logra mediante el uso de abstracciones e interfaces, permitiendo añadir nuevas estrategias de trading (`domain/strategies/`) o adaptadores de intercambio (`data/exchange_adapters.py`) sin alterar el código base.

### 2.4. No te Repitas (Don't Repeat Yourself - DRY)
Se evita la duplicación de código extrayendo funcionalidades comunes en módulos reutilizables. Ejemplos incluyen utilidades (`src/utils/`) o servicios compartidos.

### 2.5. Manténlo Simple, Estúpido (Keep It Simple, Stupid - KISS) y No lo Necesitarás (You Ain't Gonna Need It - YAGNI)
Las soluciones se mantienen lo más simples posible, y la funcionalidad solo se implementa cuando es estrictamente necesaria, evitando la complejidad prematura.

### 2.6. Principio de Inversión de Dependencias (Dependency Inversion Principle - DIP)
Los módulos de alto nivel dependen de abstracciones, no de implementaciones concretas. Esto se ve en el uso de interfaces de repositorio (`domain/repositories/`) que son implementadas por la capa de infraestructura (`infrastructure/database/`).

## 3. Metodología de Depuración
La depuración es un proceso metódico esencial para identificar y resolver problemas en el software. Un enfoque estructurado minimiza el tiempo de inactividad y mejora la calidad del código.

### 3.1. Identificación y Reproducción de Bugs
El primer paso es comprender y reproducir consistentemente el bug.
*   **Recopilación de Información:** Obtener detalles del error (mensajes de error, pasos para reproducir, entorno, datos de entrada).
*   **Aislamiento:** Intentar reproducir el bug en el entorno más simple posible (ej., un test unitario o un script mínimo).
*   **Confirmación:** Asegurarse de que el bug es reproducible y entender las condiciones bajo las cuales ocurre.

### 3.2. Recopilación de Logs y Trazas
Los logs son una fuente invaluable de información durante la depuración.
*   **Sistema de Logging:** El proyecto utiliza `structlog` para un logging estructurado y eficiente. Los logs se encuentran en el directorio `logs/` (ej., `logs/production_server.log`, `logs/api_2025-05-21.log`).
*   **Configuración del Logger:** La configuración del logger se gestiona en `utils/logger.py`, permitiendo ajustar el nivel de detalle según sea necesario.
*   **Análisis de Trazas:** Examinar las trazas de pila (stack traces) en los logs para identificar el punto exacto donde ocurre el error.

### 3.3. Formulación y Prueba de Hipótesis
Una vez que el bug es reproducible y se tiene información de los logs, se formula una hipótesis sobre la causa raíz.
*   **Hipótesis:** Basado en la información, proponer una posible causa del bug (ej., un valor nulo inesperado, un error de lógica, un problema de concurrencia).
*   **Prueba:** Modificar el código (temporalmente) o añadir puntos de interrupción (breakpoints) para validar la hipótesis. Esto puede implicar el uso de un depurador interactivo.
*   **Iteración:** Si la hipótesis es incorrecta, formular una nueva y repetir el proceso.

### 3.4. Uso de Herramientas de Diagnóstico
El proyecto incluye herramientas específicas para facilitar la depuración.
*   **`diagnose_dependencies.py`:** Este script es crucial para identificar problemas relacionados con las dependencias de Python, como versiones incompatibles o paquetes faltantes. Se recomienda ejecutarlo cuando se sospeche de problemas en el entorno o las librerías.
*   **Herramientas de Desarrollo del Navegador:** Para problemas de frontend (dashboard de Streamlit o cualquier UI basada en web), las herramientas de desarrollo del navegador (consola, inspector de elementos, red) son indispensables para depurar JavaScript, CSS y el flujo de datos.
*   **Monitoreo del Sistema:** Herramientas como `psutil` (utilizado en el proyecto) pueden ayudar a monitorear el uso de recursos (CPU, memoria) y detectar fugas o cuellos de botella que podrían manifestarse como bugs.

## 4. Gestión de Dependencias y Librerías
La gestión adecuada de las dependencias es fundamental para la estabilidad y seguridad del proyecto.

### 4.1. `requirements.txt` y `package-lock.json`
*   **`requirements.txt`:** Este archivo lista las dependencias de Python del proyecto con sus versiones específicas. Es crucial para asegurar que el entorno de desarrollo y producción sea consistente.
*   **`package-lock.json`:** Si el proyecto incluye componentes de frontend basados en Node.js (como React o Streamlit con dependencias de npm), `package-lock.json` (o `yarn.lock`) asegura que las versiones exactas de todas las dependencias (incluyendo las transitivas) estén bloqueadas, garantizando builds reproducibles.

### 4.2. Proceso de Actualización de Dependencias
La actualización regular de dependencias es importante para obtener parches de seguridad y mejoras de rendimiento, pero debe hacerse con precaución.
*   **Revisión Periódica:** Utilizar herramientas como `pip list --outdated` (para Python) o `npm outdated` (para Node.js) para identificar dependencias desactualizadas.
*   **Actualización Controlada:** Realizar actualizaciones en una rama separada, probando exhaustivamente para detectar regresiones o incompatibilidades.
*   **Bloqueo de Versiones:** Una vez que las nuevas versiones son validadas, actualizar `requirements.txt` y `package-lock.json` para reflejar los cambios.

### 4.3. Resolución de Problemas de Compatibilidad con `context7` (MANDATORIO)
Los problemas de compatibilidad entre librerías son una fuente común de errores (`AttributeError`, `ImportError`, etc.). Para abordar esto, el uso de la herramienta `context7` es **MANDATORIO**.
*   **Propósito de `context7`:** `context7` es una herramienta diseñada para diagnosticar y proponer soluciones a problemas de compatibilidad de librerías y conflictos de versiones. Contiene un vasto conocimiento sobre librerías y sus interacciones.
*   **Cuándo Usar `context7`:** Ante cualquier error que sugiera un problema de librería (ej., un `ImportError` después de una actualización, un `AttributeError` en una función de una librería que antes funcionaba, o un comportamiento inesperado que apunte a una incompatibilidad).
*   **Cómo Usar `context7`:**
    1.  **Identificar la Librería:** Determinar qué librería o conjunto de librerías parece estar causando el problema.
    2.  **Resolver ID de Librería:** Utilizar `context7.resolve-library-id` con el nombre de la librería para obtener su ID compatible con Context7 (ej., `/org/project`).
    3.  **Obtener Documentación/Soluciones:** Una vez que se tiene el ID, usar `context7.get-library-docs` con el ID y una descripción del problema (`userQuery`) para obtener información relevante, soluciones conocidas o versiones compatibles.
*   **PROHIBICIÓN ESTRICTA:** **NUNCA** intentar solucionar problemas de compatibilidad de librerías mediante la instalación indiscriminada o secuencial de múltiples versiones. `context7` es la **ÚNICA HERRAMIENTA** autorizada para diagnosticar y proponer soluciones a estos problemas específicos.

## 5. Pruebas y Observabilidad
Las pruebas y la observabilidad son pilares fundamentales para asegurar la calidad, fiabilidad y rendimiento de la aplicación en producción.

### 5.1. Estrategia de Pruebas
El proyecto Bot Arbitraje 2105 debe seguir una estrategia de pruebas robusta, priorizando la fiabilidad de las operaciones críticas.
*   **Pirámide de Tests:**
    *   **Tests Unitarios:** Enfocados en la lógica de negocio individual (ej., funciones de cálculo de oportunidades, algoritmos de trading, validadores de datos). Se encuentran en `tests/` (ej., `tests/test_detectar_oportunidades.py`).
    *   **Tests de Integración:** Verifican la interacción entre diferentes módulos o servicios (ej., comunicación entre el backend y la base de datos, integración con APIs externas como Binance).
    *   **Tests End-to-End (E2E):** Simulan flujos de usuario completos, especialmente importantes para el dashboard y la interacción con el bot. Aunque de menor prioridad para uso local personal, son cruciales para la confianza en producción.
*   **Aplicación en el Proyecto:** El directorio `tests/` contiene la suite de pruebas, utilizando `pytest` y `pytest-asyncio` para las pruebas de Python. Se recomienda expandir la cobertura de pruebas, especialmente para la lógica de trading y los componentes críticos del dashboard.

### 5.2. Observabilidad del Sistema
La observabilidad permite entender el estado interno del sistema a partir de sus salidas externas (logs, métricas, trazas).
*   **Logging Efectivo:**
    *   El proyecto utiliza `structlog` para un logging estructurado y detallado. Los logs se almacenan en el directorio `logs/` (ej., `logs/api_2025-05-21.log`, `logs/deteccion_2025-05-21.log`).
    *   Es vital configurar los niveles de logging adecuadamente (DEBUG, INFO, WARNING, ERROR, CRITICAL) para obtener la información necesaria sin saturar los archivos. La configuración se gestiona en `utils/logger.py`.
    *   Los logs deben ser lo suficientemente descriptivos para diagnosticar problemas sin necesidad de acceder al código fuente.
*   **Métricas y Monitoreo:**
    *   La librería `psutil` se utiliza para monitorear el uso de recursos del sistema (CPU, memoria, disco, red). Esto es crucial para identificar cuellos de botella de rendimiento, fugas de memoria o comportamientos anómalos.
    *   Se deben establecer métricas clave de negocio (ej., número de oportunidades detectadas, trades ejecutados, P&L diario) y métricas operacionales (latencia de API, errores de WebSocket).
    *   La visualización de estas métricas en el dashboard (ej., `core/dashboard/monitoring.py`, `core/dashboard/performance.py`) es fundamental para una supervisión proactiva.
*   **Alertas:**
    *   Configurar alertas automáticas (ej., a través de Telegram usando `python-telegram-bot` y `infrastructure/messaging/telegram_notifier.py`) para notificar sobre eventos críticos como errores de API, fallos en la ejecución de trades, o umbrales de rendimiento excedidos.

## 6. Puesta en Producción y Enfoque 'Frontend First'
La puesta en producción es la fase crítica donde la aplicación se expone a un entorno real. Un enfoque 'Frontend First' asegura que la visibilidad y la experiencia del usuario sean prioritarias desde el inicio.

### 6.1. Estrategia 'Frontend First Visibility'
Esta estrategia, detallada en `doc_claude/PLAN_PRODUCCION_LOCAL_FRONTEND_FOCUS.md`, guía el desarrollo para que cada avance sea visible e interactuable a través del frontend lo antes posible.
*   **Definición de la Interfaz Impulsada por el Frontend:** El diseño de la API y WebSockets se define por lo que el frontend necesita consumir y las acciones que el usuario debe iniciar.
*   **Ciclo de Desarrollo Iterativo Backend-Frontend (5 Pasos):**
    1.  **Frontend - Mockup/Estructura Inicial:** Componentes UI básicos con datos simulados.
    2.  **Backend - Implementación Mínima Viable:** Lógica mínima para servir datos o manejar acciones básicas.
    3.  **Integración y Visualización Temprana:** Conexión frontend-backend para visibilidad temprana de la funcionalidad. **Punto de control crucial.**
    4.  **Backend - Refinamiento y Lógica Completa:** Optimización, manejo de casos borde, seguridad.
    5.  **Frontend - Refinamiento y Experiencia de Usuario Completa:** Mejora de componentes, manejo de estados de carga/error, interactividad.

### 6.2. Seguridad de Claves API y Secretos
*   **Gestión de `.env`:** Mantener el archivo `.env` (que contiene credenciales sensibles) fuera del control de versiones (`.gitignore`).
*   **Revisión Periódica:** Auditar regularmente para asegurar que no haya secretos expuestos accidentalmente en logs o código.

### 6.3. Fortalecimiento del Manejo de Errores y Excepciones
*   **Backend:** Implementar manejo robusto de excepciones en toda la lógica de negocio, APIs y WebSockets. Utilizar reintentos con backoff (ej., con `tenacity`) para llamadas a servicios externos y mejorar la reconexión de WebSockets.
*   **Frontend:** Asegurar que el frontend capture errores de la API o WebSockets y los presente de forma clara al usuario, evitando bloqueos de la aplicación. Mostrar indicadores de estado de conexión.

### 6.4. Idempotencia en Operaciones Críticas
*   Asegurar que las operaciones que modifican el estado o ejecutan trades sean idempotentes. Esto significa que ejecutar la misma operación múltiples veces produce el mismo resultado que ejecutarla una sola vez, lo cual es vital para la fiabilidad en entornos distribuidos o con reintentos.

### 6.5. Scripts de Inicio/Parada Simplificados
*   Crear o mejorar scripts (`.bat`, `.sh` como `start_production.bat`, `stop_production.bat`) para iniciar y detener fácilmente todos los componentes de la aplicación (backend, frontend, etc.). Esto simplifica la operación y el mantenimiento.

### 6.6. Gestión de Datos y Backups
*   **Supabase y Cache Local:** Familiarizarse con las opciones de backup de la base de datos (ej., Supabase) y realizar backups manuales periódicos de datos críticos.
*   **Limpieza de Cache:** Implementar una política o script para limpiar el directorio `cache/` si los datos cacheados tienden a ocupar mucho espacio.

### 6.7. Monitoreo de Estabilidad Local
*   Realizar pruebas de estabilidad dejando la aplicación (backend y frontend) corriendo por períodos extendidos en el entorno local. Monitorear el uso de CPU y memoria para identificar fugas de memoria, degradación del rendimiento o problemas de conexión a largo plazo.

## 7. Troubleshooting Común
Esta sección generaliza problemas comunes que pueden surgir durante el desarrollo y la operación del Bot Arbitraje 2105, basándose en experiencias previas documentadas en `SOLUCION_PROBLEMAS.md`.

### 7.1. Errores de Conexión o "Too Many Requests"
*   **Problema:** Fallos al conectar con APIs externas (ej., Binance) o recibir errores de "Too many requests".
*   **Causa Común:** Exceso de solicitudes, límites de tasa excedidos, o problemas de red/firewall.
*   **Solución:**
    *   Implementar y ajustar el rate limiting en las llamadas a la API.
    *   Reducir el número de suscripciones simultáneas (ej., en `src/binance_websocket.py`).
    *   Verificar la conectividad de red y la configuración del firewall.
    *   Implementar reintentos con backoff exponencial.

### 7.2. Problemas de Importación de Módulos o Librerías
*   **Problema:** Errores como `ImportError: No module named 'xyz'` o `AttributeError` en librerías.
*   **Causa Común:** Entorno virtual incorrecto, dependencias no instaladas, versiones incompatibles de librerías, o paths de importación incorrectos.
*   **Solución:**
    *   Asegurarse de que el entorno virtual esté activado y que todas las dependencias de `requirements.txt` estén instaladas.
    *   Utilizar `diagnose_dependencies.py` para identificar problemas de dependencias.
    *   **Para problemas de compatibilidad de versiones de librerías, el uso de `context7` es MANDATORIO.** Consultar la sección 4.3 para su uso.
    *   Verificar que los scripts de inicio (`start_production_final.bat`) utilicen los paths de importación correctos.

### 7.3. Problemas con Caracteres Unicode
*   **Problema:** Errores relacionados con la codificación de caracteres, especialmente en entornos Windows.
*   **Causa Común:** Archivos guardados con codificaciones incompatibles o manejo incorrecto de cadenas Unicode.
*   **Solución:**
    *   Asegurarse de que los archivos de código fuente estén guardados con codificación UTF-8.
    *   Utilizar versiones "limpias" de scripts o módulos que manejen la codificación correctamente (ej., `src/production_server_clean.py` si aplica).

### 7.4. Comportamiento Inesperado del Dashboard o UI
*   **Problema:** El dashboard no se actualiza, componentes no se renderizan, o interacciones no responden.
*   **Causa Común:** Problemas de conexión con el backend, errores de JavaScript en el navegador, problemas de estado en el frontend.
*   **Solución:**
    *   Verificar la conexión del frontend con el backend (API y WebSockets).
    *   Usar las herramientas de desarrollo del navegador (consola, red, componentes) para inspeccionar errores de JavaScript, llamadas de red fallidas o estados de componentes.
    *   Asegurar que el ciclo de visibilidad 'Frontend First' se haya seguido correctamente.

## 8. Conclusión
La implementación y el mantenimiento del Bot Arbitraje 2105 requieren un compromiso continuo con las mejores prácticas de ingeniería de software. Al adherirse a los principios de diseño, adoptar una metodología de depuración estructurada, gestionar proactivamente las dependencias (con el apoyo crucial de `context7`), implementar pruebas rigurosas y mantener una observabilidad constante, se puede asegurar la robustez, fiabilidad y eficiencia del sistema. El enfoque 'Frontend First Visibility' no solo acelera el desarrollo, sino que también facilita la detección temprana de problemas, contribuyendo a un ciclo de vida del software más saludable y a una operación más segura en producción. Este documento sirve como una referencia viva para guiar estos esfuerzos y fomentar una cultura de mejora continua.
