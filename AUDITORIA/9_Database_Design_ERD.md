# Diseño de Base de Datos (ERD) - Bot_Arbitraje2105

## Visión General

El Bot_Arbitraje2105 utiliza PostgreSQL a través de Supabase como su sistema principal de gestión de base de datos. La estructura de la base de datos está diseñada para soportar las operaciones de trading, análisis de oportunidades, gestión de usuarios y monitoreo del sistema.

Este diagrama entidad-relación (ERD) representa el modelo de datos subyacente del sistema, basado en el análisis del código y la estructura del proyecto.

## Diagrama Entidad-Relación (ERD)

```
┌────────────────────┐       ┌─────────────────────┐       ┌────────────────────┐
│     usuarios       │       │    oportunidades    │       │ arbitraje_operaciones │
├────────────────────┤       ├─────────────────────┤       ├────────────────────┤
│ id (PK)            │       │ opportunity_id (PK) │       │ id (PK)            │
│ email              │1      │ base_currency       │       │ signal_id (UQ)     │
│ password_hash      ├───┐   │ intermediate_currency│       │ strategy_name      │
│ role               │   │   │ quote_currency      │       │ symbol             │
│ created_at         │   │   │ estimated_profit_percentage│ │ action             │
│ last_login         │   │   │ required_capital    │       │ entry_price        │
│ is_active          │   │   │ expected_profit     │       │ exit_price         │
└────────────────────┘   │   │ detection_timestamp │       │ quantity           │
                         │   │ status              │       │ pnl                │
┌────────────────────┐   │   │ expiry_timestamp    │       │ commission         │
│   trading_pairs    │   │   │ confidence_score    │1      │ confidence         │
├────────────────────┤   │   │ risk_score          ├───┐   │ risk_level         │
│ symbol (PK)        │   │   │ created_by (FK)     │   │   │ entry_time         │
│ base_asset         │   └───┤                     │   │   │ exit_time          │
│ quote_asset        │       └─────────────────────┘   │   │ hold_duration_seconds│
│ price_precision    │                                 │   │ ai_analysis (JSONB)│
│ quantity_precision │       ┌─────────────────────┐   │   │ market_conditions (JSONB)│
│ min_quantity       │       │  execution_steps    │   │   │ created_at         │
│ max_quantity       │       ├─────────────────────┤   │   │ updated_at         │
│ status             │       │ id (PK)             │   │   │ operation_id (FK)  │
│ created_at         │       │ operation_id (FK)   │   └───┤ opportunity_id (FK)│
│ updated_at         │       │ step_number         │       └────────────────────┘
└────────────────────┘       │ pair_symbol         │               │
        │                    │ action              │               │
        │                    │ expected_quantity   │               │
        │                    │ executed_quantity   │               │
        │                    │ expected_price      │               │
        │                    │ executed_price      │               │
┌───────┴──────────┐         │ fee_amount          │       ┌───────┴──────────┐
│   market_data    │         │ slippage_percentage │       │   metricas_rendimiento   │
├─────────────────┤         │ status              │       ├─────────────────┤
│ id (PK)         │         │ execution_timestamp │       │ id (PK)         │
│ symbol (FK)     │         │ error_message       │       │ timestamp       │
│ timestamp       │         └─────────────────────┘       │ strategy_name   │
│ open            │                                       │ symbol          │
│ high            │         ┌─────────────────────┐       │ metric_name     │
│ low             │         │configuracion_sistema│       │ metric_value    │
│ close           │         ├─────────────────────┤       │ metric_data (JSONB)│
│ volume          │         │ id (PK)             │       │ period_start    │
│ quote_volume    │         │ config_key (UQ)     │       │ period_end      │
│ created_at      │         │ config_value (JSONB)│       │ created_at      │
└─────────────────┘         │ description         │       └─────────────────┘
                            │ category            │
┌─────────────────┐         │ is_active           │       ┌─────────────────┐
│   estrategias   │         │ created_at          │       │     alertas     │
├─────────────────┤         │ updated_at          │       ├─────────────────┤
│ id (PK)         │         └─────────────────────┘       │ id (PK)         │
│ name            │                                       │ type            │
│ type            │         ┌─────────────────────┐       │ severity        │
│ description     │         │   trade_signals     │       │ message         │
│ parameters (JSONB)│       ├─────────────────────┤       │ details (JSONB) │
│ is_active       │         │ signal_id (PK)      │       │ timestamp       │
│ created_by (FK) │         │ strategy_name       │       │ is_read         │
│ created_at      │         │ symbol              │       │ user_id (FK)    │
│ updated_at      │         │ action              │       │ created_at      │
└─────────────────┘         │ entry_price         │       └─────────────────┘
                            │ confidence          │
┌─────────────────┐         │ risk_level          │       ┌─────────────────┐
│  user_sessions  │         │ timestamp           │       │  system_logs    │
├─────────────────┤         │ ai_analysis (JSONB) │       ├─────────────────┤
│ id (PK)         │         │ market_conditions (JSONB)│  │ id (PK)         │
│ user_id (FK)    │         └─────────────────────┘       │ level           │
│ token_jti       │                                       │ component       │
│ ip_address      │                                       │ message         │
│ user_agent      │                                       │ details (JSONB) │
│ created_at      │                                       │ timestamp       │
│ expires_at      │                                       │ created_at      │
│ revoked         │                                       └─────────────────┘
└─────────────────┘
```

## Descripción de Tablas

### 1. usuarios

Almacena información de usuarios del sistema.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | UUID | Identificador único del usuario (PK) |
| email | VARCHAR | Correo electrónico (único) |
| password_hash | VARCHAR | Hash de contraseña (bcrypt) |
| role | VARCHAR | Rol del usuario (ADMIN, TRADER, ANALYST, VIEWER) |
| created_at | TIMESTAMP | Fecha de creación |
| last_login | TIMESTAMP | Último inicio de sesión |
| is_active | BOOLEAN | Estado activo del usuario |

### 2. oportunidades

Almacena oportunidades de arbitraje detectadas.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| opportunity_id | VARCHAR | Identificador único de la oportunidad (PK) |
| base_currency | VARCHAR | Moneda base del arbitraje triangular |
| intermediate_currency | VARCHAR | Moneda intermedia |
| quote_currency | VARCHAR | Moneda de cotización |
| estimated_profit_percentage | DECIMAL | Porcentaje de ganancia estimada |
| required_capital | DECIMAL | Capital requerido para la operación |
| expected_profit | DECIMAL | Ganancia esperada en términos absolutos |
| detection_timestamp | TIMESTAMP | Momento de detección |
| status | VARCHAR | Estado (DETECTED, PENDING, APPROVED, etc.) |
| expiry_timestamp | TIMESTAMP | Momento de expiración |
| confidence_score | DECIMAL | Puntuación de confianza (0-1) |
| risk_score | DECIMAL | Puntuación de riesgo (0-1) |
| created_by | UUID | Usuario que detectó/aprobó (FK -> usuarios.id) |

### 3. arbitraje_operaciones

Almacena operaciones de arbitraje ejecutadas.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL | Identificador único (PK) |
| signal_id | VARCHAR | ID de señal único (UQ) |
| strategy_name | VARCHAR | Nombre de la estrategia utilizada |
| symbol | VARCHAR | Símbolo/par de trading |
| action | VARCHAR | Acción (BUY, SELL) |
| entry_price | DECIMAL | Precio de entrada |
| exit_price | DECIMAL | Precio de salida |
| quantity | DECIMAL | Cantidad operada |
| pnl | DECIMAL | Ganancias/pérdidas |
| commission | DECIMAL | Comisiones pagadas |
| confidence | DECIMAL | Nivel de confianza (0-1) |
| risk_level | VARCHAR | Nivel de riesgo |
| entry_time | TIMESTAMP | Momento de entrada |
| exit_time | TIMESTAMP | Momento de salida |
| hold_duration_seconds | INTEGER | Duración de la operación en segundos |
| ai_analysis | JSONB | Análisis de IA (formato JSON) |
| market_conditions | JSONB | Condiciones de mercado (formato JSON) |
| created_at | TIMESTAMP | Fecha de creación |
| updated_at | TIMESTAMP | Fecha de actualización |
| operation_id | VARCHAR | ID de la operación (FK) |
| opportunity_id | VARCHAR | ID de la oportunidad (FK -> oportunidades.opportunity_id) |

### 4. execution_steps

Almacena pasos individuales de ejecución de operaciones de arbitraje.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL | Identificador único (PK) |
| operation_id | VARCHAR | ID de la operación (FK -> arbitraje_operaciones.operation_id) |
| step_number | INTEGER | Número secuencial del paso |
| pair_symbol | VARCHAR | Par de trading |
| action | VARCHAR | Acción (BUY, SELL) |
| expected_quantity | DECIMAL | Cantidad esperada |
| executed_quantity | DECIMAL | Cantidad ejecutada |
| expected_price | DECIMAL | Precio esperado |
| executed_price | DECIMAL | Precio real de ejecución |
| fee_amount | DECIMAL | Monto de comisión |
| slippage_percentage | DECIMAL | Porcentaje de deslizamiento |
| status | VARCHAR | Estado del paso |
| execution_timestamp | TIMESTAMP | Momento de ejecución |
| error_message | TEXT | Mensaje de error (si falló) |

### 5. trading_pairs

Almacena información sobre pares de trading disponibles.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| symbol | VARCHAR | Símbolo del par (PK) |
| base_asset | VARCHAR | Activo base |
| quote_asset | VARCHAR | Activo de cotización |
| price_precision | INTEGER | Precisión del precio |
| quantity_precision | INTEGER | Precisión de la cantidad |
| min_quantity | DECIMAL | Cantidad mínima de orden |
| max_quantity | DECIMAL | Cantidad máxima de orden |
| status | VARCHAR | Estado (ACTIVE, INACTIVE) |
| created_at | TIMESTAMP | Fecha de creación |
| updated_at | TIMESTAMP | Fecha de actualización |

### 6. market_data

Almacena datos históricos de mercado.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL | Identificador único (PK) |
| symbol | VARCHAR | Símbolo del par (FK -> trading_pairs.symbol) |
| timestamp | TIMESTAMP | Momento del dato |
| open | DECIMAL | Precio de apertura |
| high | DECIMAL | Precio más alto |
| low | DECIMAL | Precio más bajo |
| close | DECIMAL | Precio de cierre |
| volume | DECIMAL | Volumen de base |
| quote_volume | DECIMAL | Volumen de cotización |
| created_at | TIMESTAMP | Fecha de registro |

### 7. metricas_rendimiento

Almacena métricas de rendimiento del sistema.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL | Identificador único (PK) |
| timestamp | TIMESTAMP | Momento de la métrica |
| strategy_name | VARCHAR | Estrategia relacionada |
| symbol | VARCHAR | Símbolo relacionado |
| metric_name | VARCHAR | Nombre de la métrica |
| metric_value | DECIMAL | Valor numérico |
| metric_data | JSONB | Datos adicionales (JSON) |
| period_start | TIMESTAMP | Inicio del período |
| period_end | TIMESTAMP | Fin del período |
| created_at | TIMESTAMP | Fecha de creación |

### 8. configuracion_sistema

Almacena configuraciones del sistema.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL | Identificador único (PK) |
| config_key | VARCHAR | Clave de configuración (UQ) |
| config_value | JSONB | Valor de configuración (JSON) |
| description | TEXT | Descripción |
| category | VARCHAR | Categoría |
| is_active | BOOLEAN | Estado activo |
| created_at | TIMESTAMP | Fecha de creación |
| updated_at | TIMESTAMP | Fecha de actualización |

### 9. estrategias

Almacena definiciones de estrategias de trading.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL | Identificador único (PK) |
| name | VARCHAR | Nombre de la estrategia |
| type | VARCHAR | Tipo (ARBITRAGE, SCALPING, etc.) |
| description | TEXT | Descripción |
| parameters | JSONB | Parámetros de configuración (JSON) |
| is_active | BOOLEAN | Estado activo |
| created_by | UUID | Usuario creador (FK -> usuarios.id) |
| created_at | TIMESTAMP | Fecha de creación |
| updated_at | TIMESTAMP | Fecha de actualización |

### 10. trade_signals

Almacena señales de trading generadas.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| signal_id | VARCHAR | Identificador único (PK) |
| strategy_name | VARCHAR | Estrategia que generó la señal |
| symbol | VARCHAR | Símbolo/par |
| action | VARCHAR | Acción recomendada |
| entry_price | DECIMAL | Precio de entrada recomendado |
| confidence | DECIMAL | Nivel de confianza |
| risk_level | VARCHAR | Nivel de riesgo |
| timestamp | TIMESTAMP | Momento de generación |
| ai_analysis | JSONB | Análisis de IA (JSON) |
| market_conditions | JSONB | Condiciones de mercado (JSON) |

### 11. user_sessions

Almacena sesiones de usuario activas.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL | Identificador único (PK) |
| user_id | UUID | ID de usuario (FK -> usuarios.id) |
| token_jti | VARCHAR | JWT ID único |
| ip_address | VARCHAR | Dirección IP |
| user_agent | TEXT | Agente de usuario |
| created_at | TIMESTAMP | Inicio de sesión |
| expires_at | TIMESTAMP | Expiración |
| revoked | BOOLEAN | Indica si fue revocada |

### 12. alertas

Almacena alertas generadas por el sistema.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL | Identificador único (PK) |
| type | VARCHAR | Tipo de alerta |
| severity | VARCHAR | Severidad (INFO, WARNING, ERROR) |
| message | TEXT | Mensaje |
| details | JSONB | Detalles adicionales (JSON) |
| timestamp | TIMESTAMP | Momento de la alerta |
| is_read | BOOLEAN | Indica si fue leída |
| user_id | UUID | Usuario destinatario (FK -> usuarios.id) |
| created_at | TIMESTAMP | Fecha de creación |

### 13. system_logs

Almacena logs del sistema.

| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | SERIAL | Identificador único (PK) |
| level | VARCHAR | Nivel (INFO, WARNING, ERROR) |
| component | VARCHAR | Componente que generó el log |
| message | TEXT | Mensaje |
| details | JSONB | Detalles adicionales (JSON) |
| timestamp | TIMESTAMP | Momento del log |
| created_at | TIMESTAMP | Fecha de registro |

## Relaciones Principales

1. **usuarios → oportunidades**: Un usuario puede crear/aprobar múltiples oportunidades.

2. **oportunidades → arbitraje_operaciones**: Una oportunidad puede dar lugar a una operación de arbitraje.

3. **arbitraje_operaciones → execution_steps**: Una operación consiste en múltiples pasos de ejecución.

4. **trading_pairs → market_data**: Un par de trading tiene múltiples datos históricos de mercado.

5. **usuarios → estrategias**: Un usuario puede crear múltiples estrategias.

6. **usuarios → user_sessions**: Un usuario puede tener múltiples sesiones activas.

7. **usuarios → alertas**: Las alertas pueden estar dirigidas a usuarios específicos.

## Índices Importantes

Para optimizar el rendimiento, se han identificado los siguientes índices:

1. **arbitraje_operaciones**:
   - `idx_arbitraje_operaciones_strategy` (strategy_name)
   - `idx_arbitraje_operaciones_symbol` (symbol)
   - `idx_arbitraje_operaciones_entry_time` (entry_time)

2. **configuracion_sistema**:
   - `idx_configuracion_sistema_key` (config_key)
   - `idx_configuracion_sistema_category` (category)

3. **metricas_rendimiento**:
   - `idx_metricas_rendimiento_timestamp` (timestamp)
   - `idx_metricas_rendimiento_strategy` (strategy_name)
   - `idx_metricas_rendimiento_metric` (metric_name)

4. **market_data**:
   - `idx_market_data_symbol_timestamp` (symbol, timestamp)

## Consideraciones de Diseño

### 1. Uso de JSONB

El diseño hace uso extensivo del tipo JSONB de PostgreSQL para datos semi-estructurados como:
- Configuraciones
- Parámetros de estrategias
- Análisis de IA
- Condiciones de mercado
- Detalles de alertas y logs

Esta elección permite flexibilidad en el esquema mientras mantiene capacidades de indexación y consulta.

### 2. Particionado

Para tablas que acumulan grandes volúmenes de datos como `market_data` y `system_logs`, se recomienda implementar particionado por tiempo para optimizar el rendimiento:

```sql
CREATE TABLE market_data (
    id SERIAL,
    symbol VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE,
    -- otros campos
) PARTITION BY RANGE (timestamp);

CREATE TABLE market_data_current PARTITION OF market_data
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');

CREATE TABLE market_data_archive PARTITION OF market_data
    FOR VALUES FROM ('2022-01-01') TO ('2023-01-01');
```

### 3. Estrategia de Respaldo

Para tablas críticas como `arbitraje_operaciones` y `oportunidades`, se recomienda una estrategia de respaldo más frecuente que para tablas de logs o datos históricos.

## Problemas y Recomendaciones

## Problema: Ausencia de restricciones de integridad referencial explícitas, origen: definiciones de tablas en supabase_client.py ##
#Solución: Implementar restricciones FOREIGN KEY explícitas en todas las relaciones para garantizar la integridad referencial y prevenir inconsistencias en los datos #

## Problema: Falta de estrategia de archivo/purga para tablas que crecen rápidamente, origen: análisis de tablas market_data, system_logs ##
#Solución: Implementar una política de retención de datos con particionado por tiempo y procedimientos automatizados para archivar o purgar datos antiguos, especialmente para tablas de alta frecuencia #

## Problema: Uso extensivo de JSONB sin esquema definido, origen: campos ai_analysis, market_conditions, etc. ##
#Solución: Definir y documentar esquemas JSON para campos JSONB importantes, utilizando validación en la aplicación y posiblemente check constraints en la base de datos para garantizar la consistencia #

## Problema: Falta de índices para búsquedas frecuentes, origen: análisis de código ##
#Solución: Identificar patrones de consulta comunes en el código e implementar índices adicionales, especialmente para búsquedas por rangos de tiempo y combinaciones de campos frecuentemente consultados #
