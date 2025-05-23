# Plan de Acción para "Producción Local" (Enfoque Frontend Primero) - Bot_Arbitraje2105

## 1. Objetivo Principal

Asegurar que la aplicación "Bot_Arbitraje2105", ejecutándose localmente, sea robusta, segura para operar con capital real y eficiente para el uso personal intensivo. La **máxima prioridad** es que cada avance en el desarrollo sea visible e interactuable a través del frontend de manera incremental y lo más pronto posible.

## 2. Estrategia Interna de Programación: "Frontend-First Visibility"

Esta estrategia guiará todo el desarrollo de nuevas funcionalidades y mejoras:

*   **Definición de la Interfaz (API y WebSockets) Impulsada por el Frontend**:
    *   Antes de implementar cualquier lógica de backend compleja, se definirá qué información necesita consumir el frontend y qué acciones debe poder iniciar el usuario desde la interfaz.
    *   Esto dictará el diseño de los *endpoints* de la API REST (ej. en `core/api_server.py`) y los mensajes/canales WebSocket.
*   **Desarrollo Iterativo Backend-Frontend (Ciclo de Visibilidad)**:
    1.  **Paso 1 (Frontend - Mockup/Estructura Inicial)**: Crear los componentes de UI básicos en React para la nueva funcionalidad. Se pueden usar datos simulados (`mock data`) o placeholders inicialmente para definir la estructura y el flujo visual.
    2.  **Paso 2 (Backend - Implementación Mínima Viable)**: Desarrollar la lógica mínima indispensable en el backend para servir los datos requeridos por el frontend o para manejar las acciones básicas definidas. El objetivo es tener algo funcional rápidamente.
    3.  **Paso 3 (Integración y Visualización Temprana)**: Conectar el frontend con esta implementación mínima del backend. **Este es el punto de control crucial para la visibilidad**. El usuario debe poder ver la nueva funcionalidad, aunque sea en una forma básica, interactuando con datos reales o ejecutando acciones reales.
    4.  **Paso 4 (Backend - Refinamiento y Lógica Completa)**: Una vez validada la visualización básica, completar y robustecer la lógica del backend. Esto incluye optimizaciones, manejo de casos borde, seguridad adicional, y toda la funcionalidad avanzada.
    5.  **Paso 5 (Frontend - Refinamiento y Experiencia de Usuario Completa)**: Mejorar los componentes del frontend para reflejar la funcionalidad completa del backend. Esto incluye una mejor presentación de datos, manejo de estados de carga/error, interactividad avanzada, y una experiencia de usuario pulida.
*   **Comunicación Continua y Reactiva (WebSockets)**:
    *   Utilizar WebSockets no solo para datos de mercado, sino también para enviar actualizaciones de estado en tiempo real desde el backend al frontend (ej. progreso de una operación, resultados de un análisis, errores, confirmaciones). Esto refuerza la percepción de una herramienta viva y en evolución.
*   **Modularidad en el Frontend**:
    *   Construir componentes de React bien encapsulados, reutilizables y enfocados en una sola responsabilidad. Esto facilita la adición, modificación y prueba incremental de la interfaz.

## 3. Plan de Tareas Detallado

### Fase 0: Establecimiento de la Base para "Frontend-First Visibility"

*   **Tarea 1: Revisión y Optimización de la Comunicación Backend-Frontend Actual**
    *   **Subtarea**: Auditar los *endpoints* API y los canales WebSocket existentes. Asegurar que sean claros, eficientes, bien documentados (al menos internamente) y fáciles de consumir por el frontend.
    *   **Subtarea**: Revisar y optimizar `frontend/src/hooks/useWebSocket.ts` y la gestión de estado global (ej. Zustand en `frontend/src/store/`) para un manejo reactivo y eficiente de los datos provenientes del backend.
    *   **Subtarea**: Implementar o mejorar un sistema de notificaciones visuales en el frontend (ej. "toasts" o alertas no intrusivas) para comunicar estados importantes, éxitos, advertencias o errores provenientes del backend.
*   **Tarea 2: Preparación del Entorno de Desarrollo Local Enfocado al Frontend**
    *   **Subtarea**: Asegurar un flujo de trabajo de desarrollo local eficiente que permita ejecutar simultáneamente el backend Python y el servidor de desarrollo del frontend (ej. Vite con Hot Module Replacement - HMR) con facilidad.
    *   **Subtarea**: Configurar y utilizar activamente herramientas de desarrollo de navegador (React DevTools, y Redux/Zustand DevTools si aplica) para inspeccionar el estado, los componentes y el flujo de datos del frontend.

### Fase 1: Desarrollo Incremental de Funcionalidades (Ciclo Continuo Frontend-Backend)

Esta fase es el núcleo del trabajo y se aplicará de forma continua para cada nueva característica o mejora significativa que se decida implementar.

*   **Proceso General para Cada Nueva Funcionalidad:**
    1.  **Planificación Detallada**:
        *   Definir claramente qué se quiere lograr con la nueva funcionalidad.
        *   Especificar qué información necesitará el frontend y qué interacciones del usuario se habilitarán.
        *   Diseñar (aunque sea a grandes rasgos) cómo se verá y se sentirá en la UI.
    2.  **Implementación Siguiendo el Ciclo de Visibilidad**:
        *   Aplicar los 5 pasos del "Desarrollo Iterativo Backend-Frontend" descritos en la Sección 2.
        *   **Priorizar siempre alcanzar el Paso 3 (Integración y Visualización Temprana) lo antes posible.**

*   **Ejemplo de Flujo para una Nueva Funcionalidad: "Dashboard de Resumen de Rendimiento Diario"**
    1.  *Planificación*: El frontend necesita mostrar P&L diario, número de trades, win rate del día. El usuario podrá seleccionar la fecha.
    2.  *Frontend - Mockup*: Crear componentes React para mostrar estas métricas y un selector de fecha. Usar datos simulados.
    3.  *Backend - Mínimo*: Crear un endpoint API que devuelva el P&L y número de trades para una fecha dada (cálculo simple inicial).
    4.  *Integración y Visualización*: Conectar el frontend al nuevo endpoint. El usuario ya puede ver P&L y trades del día actual (o seleccionado) en la UI.
    5.  *Backend - Completo*: Optimizar el cálculo, añadir win rate, persistir datos si es necesario, manejar errores.
    6.  *Frontend - Refinamiento*: Mejorar gráficos, añadir tooltips, manejo de estados de carga, formato de números.

### Fase 2: Robustecimiento del Sistema Local (Paralelo y Continuo)

Estas tareas se realizan de forma continua, asegurando que cualquier cambio mantenga o mejore la visibilidad y funcionalidad del frontend.

*   **Tarea 3: Seguridad de Claves API y Secretos (Local)**
    *   **Subtarea**: Mantener el archivo `.env` fuera del control de versiones (en `.gitignore`).
    *   **Subtarea**: Revisar periódicamente que no haya secretos expuestos accidentalmente en logs o en el código.
*   **Tarea 4: Fortalecimiento del Manejo de Errores y Excepciones (Backend y Frontend)**
    *   **Subtarea (Backend)**: Implementar manejo robusto de excepciones en toda la lógica de negocio, APIs y WebSockets. Usar reintentos con backoff (`tenacity`) para llamadas a servicios externos. Mejorar la reconexión de WebSockets.
    *   **Subtarea (Frontend)**: Asegurar que el frontend capture errores de la API o WebSockets y los presente de forma clara al usuario, evitando que la aplicación se bloquee. Mostrar indicadores de estado de conexión.
*   **Tarea 5: Idempotencia en Operaciones Críticas (Backend)**
    *   **Subtarea**: Revisar y asegurar que las operaciones que modifican estado o ejecutan trades sean idempotentes.
*   **Tarea 6: Logging Efectivo para Diagnóstico (Backend y Frontend)**
    *   **Subtarea (Backend)**: Configurar logs detallados con rotación de archivos para facilitar el diagnóstico de problemas sin saturar el disco.
    *   **Subtarea (Frontend)**: Utilizar `console.log/warn/error` de forma estratégica durante el desarrollo. Para producción local, asegurar que los errores importantes se puedan reportar o sean visibles para el usuario si impiden la funcionalidad.
*   **Tarea 7: Pruebas de Estabilidad Local (Continuas)**
    *   **Subtarea**: Dejar la aplicación (backend y frontend) corriendo por períodos extendidos en el entorno local para identificar fugas de memoria, degradación del rendimiento o problemas de conexión a largo plazo. Monitorear el uso de CPU y memoria.

### Fase 3: Mantenimiento y Operación Local Eficiente (Continuo)

*   **Tarea 8: Scripts de Inicio/Parada Simplificados**
    *   **Subtarea**: Crear o mejorar scripts (`.bat`, `.sh`) para iniciar/detener fácilmente todos los componentes de la aplicación (backend, frontend).
*   **Tarea 9: Gestión de Datos y Backups (Supabase y Cache Local)**
    *   **Subtarea**: Familiarizarse con las opciones de backup de Supabase (incluso en el plan gratuito) y realizar backups manuales periódicos de datos críticos.
    *   **Subtarea**: Implementar una política o script para limpiar el directorio `cache/` si los datos cacheados tienden a ocupar mucho espacio.
*   **Tarea 10: Actualización de Dependencias**
    *   **Subtarea**: Revisar y actualizar dependencias (Python: `pip list --outdated`; Node.js: `npm outdated`) regularmente para aplicar parches de seguridad y obtener mejoras. Realizar esto en una rama separada y probar antes de integrar.

## 4. Sobre los Tests (Enfoque Pragmático con Prioridad Frontend)

Aunque la visibilidad en el frontend es clave, los tests son importantes para la fiabilidad, especialmente al manejar capital.

*   **Backend**:
    *   **Tests Unitarios y de Integración**: Priorizar para lógica de cálculo de oportunidades, ejecución de trades, gestión de capital, y la correcta implementación de los *endpoints* API y mensajes WebSocket que consume el frontend.
*   **Frontend**:
    *   **Tests de Componentes (Recomendado)**: Utilizar React Testing Library para verificar que los componentes individuales renderizan la información correcta y responden a interacciones básicas. Esto asegura que lo que *ves* y con lo que *interactúas* funciona como se espera.
    *   **Tests Unitarios (Opcional)**: Para lógica compleja dentro de componentes, hooks personalizados o funciones de utilidad del frontend.
    *   **Tests End-to-End (E2E) (Menor prioridad para uso local personal)**: Herramientas como Cypress o Playwright son potentes pero pueden ser un esfuerzo considerable. Considerar solo para los flujos de usuario más críticos si el tiempo lo permite.

## 5. Próximos Pasos Inmediatos

1.  **Revisar y Validar este Plan**: Asegúrate de que este plan revisado se alinea completamente con tu visión.
2.  **Priorizar la Primera Funcionalidad/Mejora**: Identifica la primera pieza de trabajo (una nueva funcionalidad, o una mejora a algo existente) que deseas abordar siguiendo la "Estrategia Frontend-First Visibility".
3.  **Comenzar con la Fase 0**: Iniciar las tareas de la "Fase 0: Establecimiento de la Base para Frontend-First Visibility" para asegurar que la comunicación y el entorno de desarrollo estén óptimos para este enfoque.

Este plan busca un equilibrio entre tu necesidad de ver la evolución constante en el frontend y la necesidad de construir una aplicación local robusta y fiable.
