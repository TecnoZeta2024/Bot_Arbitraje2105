# **Arquitectura \- Bot de Arbitraje Triangular (v2)**

Este documento detalla la arquitectura del sistema para el bot de arbitraje triangular, integrando los flujos de trabajo de n8n y los scripts de Python.

## **🏛️ Diagrama de Flujo General**

graph TD  
    subgraph Python Scripts  
        A\[Filtrado de Tokens\] \--\> B\[Detección de Oportunidades\]  
        B \--\> C\[Ejecución de Arbitraje\]  
    end

    subgraph APIs Externas  
        Mobula(Mobula) \--\> A  
        BinanceAPI(Binance API) \--\> B  
        BinanceAPI \--\> C  
    end

    subgraph Base de Datos (Supabase)  
        DB\_Tokens\[token\_candidatos\] \--\> A  
        DB\_Oportunidades\[oportunidades\_detectadas\] \--\> B  
        DB\_Operaciones\[arbitraje\_operaciones\] \--\> C  
        DB\_Operaciones \--\> N8N\_Reporte\[Consulta Estadísticas\]  
    end

    subgraph n8n Workflows  
        N8N\_Webhook\_Oportunidad\[/arbitraje-oportunidad\<br\>Webhook Oportunidad\] \--\> N8N\_IA\[Agente IA \- Análisis\]  
        N8N\_IA \--\> N8N\_Switch\[Evaluar Recomendación\]  
        N8N\_Switch \-- PROCEDER/PRECAUCION \--\> N8N\_Telegram\_Notif\[Notificar por Telegram\]  
        N8N\_Switch \-- DESCARTAR \--\> N8N\_End\[Fin del Flujo\]  
        N8N\_Telegram\_Notif \--\> N8N\_Wait\[Esperar Confirmación Usuario\]  
        N8N\_Wait \--\> N8N\_Webhook\_Decision\[/webhook/decision\<br\>Webhook Decisión Usuario\]  
        N8N\_Webhook\_Decision \--\> N8N\_Switch\_Decision\[Procesar Decisión\]  
        N8N\_Switch\_Decision \-- Si \--\> N8N\_HTTP\_Ejecutar\[Enviar a Python\<br\>HTTP POST /api/ejecutar-arbitraje\]  
        N8N\_Switch\_Decision \-- No \--\> N8N\_End\_Cancel\[Fin \- Cancelado\]  
        C \--\> N8N\_Webhook\_Resultado\[/arbitraje-resultado\<br\>Webhook Resultado Ejecución\]  
        N8N\_Webhook\_Resultado \--\> N8N\_Supabase\_Update\[Actualizar Registro\<br\>Supabase\]  
        N8N\_Supabase\_Update \--\> N8N\_Telegram\_Resultado\[Notificar Resultado\<br\>Telegram\]

        N8N\_Trigger\_Reporte\[Trigger Manual/Programado\] \--\> N8N\_Reporte  
        N8N\_Reporte \--\> N8N\_IA\_Reporte\[Generar Informe con IA\]  
        N8N\_IA\_Reporte \--\> N8N\_Telegram\_Reporte\[Enviar Informe\<br\>Telegram\]  
    end

    PythonScripts \--\> N8N\_Webhook\_Oportunidad  
    N8N\_HTTP\_Ejecutar \--\> C  
    C \--\> DB\_Operaciones  
    N8N\_Supabase\_Update \--\> DB\_Operaciones

    TelegramBot(Telegram Bot) \--\> N8N\_Telegram\_Notif  
    TelegramBot \--\> N8N\_Telegram\_Resultado  
    TelegramBot \--\> N8N\_Telegram\_Reporte  
    TelegramBot \--\> N8N\_Webhook\_Decision

    Dashboard(Dashboard Streamlit) \--\> DB\_Operaciones  
    Dashboard \--\> N8N\_Reporte

*Nota: El diagrama anterior utiliza sintaxis Mermaid para una mejor visualización. La conexión del Webhook de Decisión del Usuario no está explícitamente visible en el JSON como un nodo receptor separado después del nodo 'Wait', pero se asume que el nodo 'Wait' espera una respuesta (probablemente a través de otro webhook de Telegram o similar) que alimenta el nodo 'Procesar Decisión Usuario'. Se ha añadido un nodo representativo para clarificar el flujo.*

## **🔗 Flujo de Datos Detallado**

El sistema se compone de varios flujos interconectados:

### **1\. Proceso de Filtrado de Tokens (Python)**

\# script: src/core/filtrar\_tokens.py  
1\. Consultar APIs externas (Mobula/CoinGecko/Binance) para obtener datos de tokens.  
2\. Aplicar filtros cuantitativos (ej: capitalización de mercado, volumen en Binance, listado en Binance).  
3\. Guardar la lista de tokens que cumplen los criterios en Supabase (tabla \`token\_candidatos\`).  
4\. Retornar la lista filtrada para el siguiente paso.

*Este proceso se ejecuta periódicamente (ej: diariamente).*

### **2\. Detección de Oportunidades (Python)**

\# script: src/core/detectar\_oportunidades.py  
1\. Leer los tokens candidatos desde Supabase (\`token\_candidatos\`).  
2\. Generar todas las combinaciones triangulares posibles con estos tokens en Binance.  
3\. Para cada combinación, calcular la rentabilidad teórica bruta utilizando los precios actuales de Binance.  
4\. Validar oportunidades (ej: rentabilidad \> umbral, pares disponibles en Binance).  
5\. Guardar las oportunidades detectadas (ruta, rentabilidad teórica) en Supabase (tabla \`oportunidades\_detectadas\`).  
6\. Enviar los detalles de cada oportunidad viable vía \*\*Webhook HTTP POST\*\* a n8n en el endpoint \`/arbitraje-oportunidad\`.

*Este proceso se ejecuta continuamente o a intervalos cortos (ej: cada 5-10 minutos).*

### **3\. Análisis y Notificación (n8n Workflow)**

// n8n workflow: Bot Arbitraje triangular.json  
1\. \*\*Recibir Oportunidad (Webhook /arbitraje-oportunidad):\*\* n8n recibe los datos de la oportunidad detectada desde el script de Python.  
2\. \*\*Análisis IA (Agente IA \- Análisis de Oportunidad):\*\* Utiliza un modelo de lenguaje (Google Gemini) para analizar la oportunidad. El prompt incluye la ruta, rentabilidad teórica y datos de los tokens, solicitando un análisis de viabilidad considerando slippage, volatilidad, spread y comisiones. La respuesta esperada es un JSON con \`recomendacion\` ('PROCEDER', 'PRECAUCION', 'DESCARTAR'), \`confianza\`, \`rentabilidad\_neta\_estimada\`, \`riesgos\_identificados\` y \`explicacion\`.  
3\. \*\*Evaluar Recomendación (Switch):\*\* Dirige el flujo basado en la \`recomendacion\` de la IA.  
4\. \*\*Notificar Usuario (Telegram):\*\* Si la recomendación es 'PROCEDER' o 'PRECAUCION', envía un mensaje detallado al usuario vía Telegram con la información de la oportunidad, el análisis de la IA y los riesgos. Incluye opciones interactivas ('/Si', '/No') para la confirmación.  
5\. \*\*Esperar Confirmación (Wait):\*\* Pausa el flujo esperando la respuesta del usuario (configurado para 300 segundos en el JSON). Se asume que la respuesta del usuario en Telegram activa otro webhook o mecanismo que reanuda este flujo con la decisión.  
6\. \*\*Procesar Decisión Usuario (Switch):\*\* Evalúa la respuesta del usuario ('Si' o 'No').  
7\. \*\*Enviar a Python para Ejecución (HTTP Request):\*\* Si el usuario confirma ('Si'), envía un \*\*HTTP POST request\*\* al script de ejecución de Python (ej: \`http://localhost:8000/api/ejecutar-arbitraje\`) con los detalles de la oportunidad y el análisis de la IA. Esto inicia la ejecución real de las órdenes en Binance.

### **4\. Ejecución y Registro de Resultados (Python \+ n8n)**

\# script: src/core/ejecutar\_ciclo.py  
1\. Recibir la solicitud de ejecución desde n8n (HTTP POST /api/ejecutar-arbitraje).  
2\. Conectarse a la API de Binance (Testnet o Producción).  
3\. Ejecutar la secuencia de órdenes de intercambio triangular en Binance.  
4\. Monitorear el estado y resultado de las órdenes.  
5\. Calcular el resultado neto, slippage real y comisiones totales.  
6\. Enviar el resultado de la ejecución (estado, ganancia neta, slippage, comisiones, pares ejecutados, etc.) vía \*\*Webhook HTTP POST\*\* de vuelta a n8n en el endpoint \`/arbitraje-resultado\`.  
\`\`\`javascript  
// n8n workflow (continuación del flujo principal)  
7\. \*\*Webhook Resultado Ejecución (/arbitraje-resultado):\*\* n8n recibe el resultado de la ejecución desde el script de Python.  
8\. \*\*Actualizar Registro (Supabase):\*\* Utiliza el nodo Supabase para actualizar el registro correspondiente en la tabla \`arbitraje\_operaciones\` con los resultados reales de la ejecución (estado, ganancia neta, rentabilidad real, comisiones, slippage real, pares ejecutados, fecha de completado).  
9\. \*\*Notificar Resultado (Telegram):\*\* Envía un mensaje final al usuario vía Telegram informando sobre el resultado de la operación (éxito/fallo, ganancia/pérdida, detalles).

### **5\. Informes Periódicos (n8n Workflow)**

// n8n workflow (flujo separado)  
1\. \*\*Trigger (Manual/Programado):\*\* El flujo se inicia manualmente (en el JSON) o se configuraría con un trigger de tiempo (ej: diario a las 20:00).  
2\. \*\*Consultar Estadísticas (Supabase):\*\* Consulta la base de datos Supabase (tabla \`arbitraje\_operaciones\`) para obtener los datos de las operaciones de un período (ej: última semana).  
3\. \*\*Generar Informe (Agente IA \- Information Extractor):\*\* Utiliza un modelo de lenguaje (Google Gemini) para analizar los datos de las operaciones y generar un resumen estructurado (total operaciones, ganancia total, rentabilidad promedio, mejor ruta, recomendaciones, patrones identificados).  
4\. \*\*Enviar Informe (Telegram):\*\* Envía el informe generado por la IA al usuario vía Telegram.

## **📁 Estructura de Archivos Detallada**

C:\\Users\\zamor\\Bot de Arbitraje Triangular\\  
│  
├── CLAUDE.md                    \# Memoria principal del asistente  
├── .env                         \# API keys y configuración (para Python y n8n)  
├── requirements.txt             \# Dependencias Python  
├── main.py                      \# Orquestador principal de scripts Python  
│  
├── src/  
│   ├── \_\_init\_\_.py  
│   ├── core/  
│   │   ├── \_\_init\_\_.py  
│   │   ├── filtrar\_tokens.py    \# Módulo de filtrado (Paso 1\)  
│   │   ├── detectar\_oportunidades.py  \# Detección de arbitraje (Paso 2\)  
│   │   ├── ejecutar\_ciclo.py    \# Ejecución en Binance (Paso 4\)  
│   │   └── dashboard.py         \# Interfaz web (Streamlit)  
│   │  
│   ├── apis/  
│   │   ├── \_\_init\_\_.py  
│   │   ├── mobula\_client.py     \# Cliente para Mobula API  
│   │   ├── coingecko\_client.py  \# Cliente para CoinGecko API  
│   │   ├── binance\_client.py    \# Cliente para Binance API  
│   │   └── supabase\_client.py   \# Cliente para Supabase API  
│   │  
│   └── utils/  
│       ├── \_\_init\_\_.py  
│       ├── logger.py            \# Utilidad de logging  
│       ├── calculator.py        \# Utilidades de cálculo (ej: rentabilidad)  
│       └── config.py            \# Carga de configuración desde .env  
│  
├── n8n\_flows/  
│   ├── Bot\_Arbitraje\_triangular.json \# Flujo principal de n8n (Análisis, Notificación, Ejecución, Reporte)  
│   └── prompts/  
│       └── gemini\_prompt\_template.txt \# Plantillas de prompts para IA (si se usan archivos externos)  
│  
├── tests/                       \# Pruebas unitarias e de integración  
│   ├── test\_filtrado.py  
│   ├── test\_deteccion.py  
│   └── test\_ejecucion.py  
│  
├── Contexto/                    \# Documentación del proyecto  
│   ├── \[archivos existentes\]  
│  
└── Seguimiento\_Control/         \# Archivos de control y seguimiento  
    ├── ESTADO\_PROYECTO.md  
    ├── RESUMEN\_ARQUITECTURA.md  \# Este documento  
    ├── LOG\_DECISIONES.md        \# Registro manual o automático de decisiones clave  
    └── BACKLOG\_TAREAS.md        \# Seguimiento de tareas pendientes

## **📊 Esquema de Base de Datos (Supabase)**

Basado en el uso observado en el flujo de n8n y la estructura proyectada:

\-- Tabla: token\_candidatos  
\-- Almacena tokens que cumplen los criterios iniciales de filtrado.  
CREATE TABLE token\_candidatos (  
    id SERIAL PRIMARY KEY,  
    simbolo VARCHAR(20) UNIQUE, \-- Símbolo del token (ej: BTC, ETH)  
    nombre VARCHAR(50),  
    market\_cap NUMERIC,         \-- Capitalización de mercado  
    rendimiento\_7d NUMERIC,     \-- Rendimiento en 7 días (%)  
    rendimiento\_24h NUMERIC,    \-- Rendimiento en 24 horas (%)  
    rendimiento\_1h NUMERIC,     \-- Rendimiento en 1 hora (%)  
    volumen\_binance\_24h NUMERIC,-- Volumen en Binance en 24 horas  
    fecha\_actualizacion TIMESTAMP DEFAULT NOW() \-- Marca de tiempo de la última actualización  
);

\-- Tabla: oportunidades\_detectadas  
\-- Almacena oportunidades de arbitraje triangular identificadas por los scripts de Python.  
CREATE TABLE oportunidades\_detectadas (  
    id SERIAL PRIMARY KEY,  
    ruta TEXT,          \-- Ruta del arbitraje (ej: "USDT \-\> BTC \-\> ETH \-\> USDT")  
    pares\_comercio JSONB, \-- Detalles de los pares de comercio (ej: \[{"symbol": "BTCUSDT", "step": 1}, ...\])  
    rentabilidad\_teorica NUMERIC, \-- Rentabilidad bruta calculada antes de comisiones/slippage  
    capital\_inicial NUMERIC,    \-- Capital con el que se detectó la oportunidad  
    fecha\_deteccion TIMESTAMP DEFAULT NOW() \-- Marca de tiempo de la detección  
);

\-- Tabla: arbitraje\_operaciones  
\-- \*\*Tabla central\*\* utilizada por n8n para registrar y actualizar el estado y resultado de las operaciones \*intentadas\*.  
CREATE TABLE arbitraje\_operaciones (  
    id SERIAL PRIMARY KEY,  
    operacion\_id VARCHAR(255) UNIQUE, \-- ID único de la operación (ej: combinado de workflow ID y timestamp)  
    oportunidad\_detectada\_id INTEGER REFERENCES oportunidades\_detectadas(id), \-- Oportunidad que originó esta operación  
    ruta\_arbitraje TEXT,        \-- Ruta de la operación (copia de oportunidad\_detectada)  
    capital\_inicial NUMERIC,    \-- Capital con el que se intentó operar  
    analisis\_ia JSONB,          \-- JSON completo del análisis de la IA para esta oportunidad  
    decision\_usuario VARCHAR(20), \-- Decisión del usuario ("Si", "No")  
    fecha\_decision TIMESTAMP,   \-- Marca de tiempo de la decisión del usuario  
    estado VARCHAR(50),         \-- Estado de la ejecución ("PENDIENTE", "EJECUTANDO", "COMPLETADO", "FALLIDO", "CANCELADO")  
    pares\_ejecutados JSONB,     \-- Detalles de los pares y órdenes ejecutadas  
    precios\_reales JSONB,       \-- Precios reales de ejecución  
    resultado\_bruto NUMERIC,    \-- Resultado antes de comisiones  
    comisiones\_totales NUMERIC, \-- Comisiones pagadas  
    slippage\_real NUMERIC,      \-- Slippage real experimentado (%)  
    ganancia\_neta NUMERIC,      \-- Ganancia o pérdida neta en USDT  
    rentabilidad\_real NUMERIC,  \-- Rentabilidad neta real (%)  
    fecha\_inicio\_ejecucion TIMESTAMP, \-- Marca de tiempo del inicio de ejecución  
    fecha\_completado TIMESTAMP, \-- Marca de tiempo de finalización de ejecución  
    log\_ejecucion TEXT          \-- Log detallado de la ejecución (opcional)  
);

\-- Nota: La tabla \`analisis\_oportunidades\` descrita en la v1 parece estar integrada  
\-- dentro de la tabla \`arbitraje\_operaciones\` en el campo \`analisis\_ia\`,  
\-- según el flujo de n8n que pasa el JSON completo del análisis de la IA  
\-- al script de ejecución, que luego lo incluye en el resultado enviado de vuelta a n8n  
\-- para la actualización final en \`arbitraje\_operaciones\`.

## **🔑 APIs y Configuraciones Clave**

### **Módulo Python: Filtrado y Detección**

\# Configuración de APIs externas  
MOBULA\_CONFIG \= {  
    "base\_url": "\[https://api.mobula.io/api/1/\](https://api.mobula.io/api/1/)",  
    "key": os.getenv("MOBULA\_API\_KEY"), \# Clave API cargada desde .env  
    "timeout": 10 \# Tiempo de espera para respuestas  
}

COINGECKO\_CONFIG \= {  
    "base\_url": "\[https://api.coingecko.com/api/v3/\](https://api.coingecko.com/api/v3/)",  
    "timeout": 10 \# Tiempo de espera para respuestas  
}

BINANCE\_CONFIG\_DATA \= { \# Configuración para obtener datos (precios, volumen)  
    "base\_url": "\[https://api.binance.com/api/v3/\](https://api.binance.com/api/v3/)", \# API de datos pública  
    "timeout": 10  
}

### **Módulo n8n y Gemini**

// Webhook endpoint en n8n para recibir oportunidades de Python  
// Utilizado por el nodo "Recibir Oportunidad de Python"  
/arbitraje-oportunidad

// Webhook endpoint implícito en n8n para recibir la decisión del usuario desde Telegram  
// Utilizado por el nodo "Esperar Confirmación Usuario" (asume una respuesta que reanuda el flujo)  
// La configuración exacta depende de cómo se gestione la respuesta de Telegram (ej: otro webhook de Telegram)  
// /webhook/decision (ejemplo de ruta si se usa un webhook dedicado)

// Endpoint HTTP en el script Python para iniciar la ejecución  
// Utilizado por el nodo "Enviar a Python para Ejecución"  
http://localhost:8000/api/ejecutar-arbitraje

// Webhook endpoint en n8n para recibir el resultado de la ejecución desde Python  
// Utilizado por el nodo "Webhook Resultado de Ejecución"  
/arbitraje-resultado

// Configuración del Agente IA (Google Gemini) en n8n  
// Prompt template utilizado en el nodo "Agente IA \- Análisis de Oportunidad":  
\`Eres un experto en arbitraje triangular de criptomonedas. Analiza la siguiente oportunidad considerando:

1\. Rentabilidad bruta teórica  
2\. Potencial de slippage según liquidez  
3\. Volatilidad reciente de los tokens  
4\. Spread bid-ask en Binance  
5\. Comisiones totales del ciclo  
6\. Riesgos específicos identificados

Estructura tu análisis en JSON con:  
\- recomendacion: 'PROCEDER' | 'PRECAUCION' | 'DESCARTAR'  
\- confianza: 0-100  
\- rentabilidad\_neta\_estimada: porcentaje  
\- riesgos\_identificados: \[lista\]  
\- explicacion: string

Datos de entrada: {{ $json }}\`

// Configuración del Agente IA (Google Gemini) en n8n para informes  
// Prompt template utilizado en el nodo "Generar Informe con IA":  
\`Analiza las siguientes operaciones de arbitraje de la última semana y genera un informe comprensivo:

{{ $json.map(op \=\> \\\`Operación ${op.operacion\_id}: ${op.ganancia\_neta} USDT, Rentabilidad: ${op.rentabilidad\_real}%, Ruta: ${op.ruta\_arbitraje}\\\`).join('\\\\n') }}\`  
// Se extraen atributos específicos (total\_operaciones, ganancia\_total, etc.)

### **Módulo Python: Ejecución en Binance**

\# Configuración para la ejecución de órdenes en Binance  
BINANCE\_CONFIG\_TRADE \= {  
    "api\_key": os.getenv("BINANCE\_API\_KEY"), \# Clave API cargada desde .env  
    "secret\_key": os.getenv("BINANCE\_SECRET\_KEY"), \# Secret Key cargada desde .env  
    "testnet": True,  \# \*\*IMPORTANTE\*\*: Cambiar a False para operar con dinero real  
    "base\_url": "\[https://testnet.binance.vision/api/v3/\](https://testnet.binance.vision/api/v3/)" \# URL para Testnet  
    \# Para producción, usar: "base\_url": "\[https://api.binance.com/api/v3/\](https://api.binance.com/api/v3/)"  
}

\# Endpoint en el script Python para recibir la solicitud de ejecución  
\# /api/ejecutar-arbitraje

## **🔄 Ciclo de Ejecución Típico**

1. **\[Programado/Diario\] Inicio del Ciclo de Detección:**  
   * El script Python filtrar\_tokens.py se ejecuta (ej: 08:00 AM).  
   * Consulta APIs externas, filtra tokens y actualiza token\_candidatos en Supabase.  
2. **\[Continuo\] Detección de Oportunidades:**  
   * El script Python detectar\_oportunidades.py se ejecuta continuamente o a intervalos cortos (ej: cada 5-10 minutos).  
   * Lee token\_candidatos, genera rutas, calcula rentabilidad teórica.  
   * Guarda oportunidades en oportunidades\_detectadas.  
   * Envía oportunidades viables a n8n vía Webhook /arbitraje-oportunidad.  
3. **\[Bajo Demanda \- Trigger por Webhook\] Análisis y Notificación:**  
   * n8n recibe la oportunidad (/arbitraje-oportunidad).  
   * El nodo "Agente IA \- Análisis de Oportunidad" analiza la oportunidad.  
   * El nodo "Evaluar Recomendación IA" dirige el flujo.  
   * Si la recomendación es 'PROCEDER' o 'PRECAUCION', n8n notifica al usuario por Telegram.  
   * El nodo "Esperar Confirmación Usuario" pausa el flujo.  
4. **\[Interacción Usuario\] Decisión y Reanudación:**  
   * El usuario recibe la notificación en Telegram.  
   * El usuario responde ('/Si' o '/No').  
   * La respuesta del usuario es capturada (probablemente por otro webhook de Telegram o mecanismo asociado al nodo 'Wait' de n8n) reanudando el flujo en n8n.  
5. **\[Bajo Demanda \- Trigger por Decisión\] Ejecución o Cancelación:**  
   * El nodo "Procesar Decisión Usuario" evalúa la respuesta.  
   * Si es 'Si', el nodo "Enviar a Python para Ejecución" envía un HTTP POST al script ejecutar\_ciclo.py (/api/ejecutar-arbitraje).  
   * Si es 'No', el flujo termina (operación cancelada).  
6. **\[Bajo Demanda \- Trigger por HTTP Request\] Ejecución en Binance:**  
   * El script Python ejecutar\_ciclo.py recibe la solicitud.  
   * Ejecuta las órdenes de arbitraje en Binance (Testnet/Producción).  
   * Calcula resultados reales (ganancia, slippage, comisiones).  
   * Envía el resultado a n8n vía Webhook /arbitraje-resultado.  
7. **\[Bajo Demanda \- Trigger por Webhook\] Registro y Notificación Final:**  
   * n8n recibe el resultado de la ejecución (/arbitraje-resultado).  
   * El nodo "Actualizar Registro en Supabase" actualiza el registro correspondiente en la tabla arbitraje\_operaciones.  
   * El nodo "Notificar Resultado por Telegram" informa al usuario el resultado final.  
8. **\[Programado/Diario\] Generación de Informe:**  
   * Un trigger (ej: diario a las 20:00) inicia el flujo de reporte en n8n.  
   * Consulta arbitraje\_operaciones en Supabase.  
   * El nodo "Generar Informe con IA" analiza los datos y crea un resumen.  
   * El nodo "Enviar Informe por Telegram" envía el informe al usuario.

*Documento generado por CodeCraft Assistant, basado en el análisis del flujo de n8n y la arquitectura proyectada.*