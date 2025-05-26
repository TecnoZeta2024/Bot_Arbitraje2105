# Documentación de Esquemas Unificados y Reglas de Mapeo

Este documento describe los esquemas de datos unificados `MarketDataUnified` y `OpportunityUnified`, así como las reglas de mapeo desde las fuentes de datos originales (Binance y Mobula) a estos esquemas.

## 1. Esquema `MarketDataUnified`

**Propósito:** Proporcionar una representación estandarizada de los datos de mercado de diversas fuentes, asegurando consistencia y precisión.

**Definición (Pydantic):**
```python
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

class MarketDataUnified(BaseModel):
    symbol: str = Field(..., description="Símbolo del par de trading (ej. BTCUSDT)")
    timestamp: datetime = Field(..., description="Marca de tiempo del dato de mercado")
    price: Decimal = Field(..., description="Precio actual del activo")
    volume: Decimal = Field(..., description="Volumen de trading en las últimas 24h en la moneda base")
    quote_volume: Decimal = Field(..., description="Volumen de trading en las últimas 24h en la moneda de cotización")
    high_price: Decimal = Field(..., description="Precio más alto en las últimas 24h")
    low_price: Decimal = Field(..., description="Precio más bajo en las últimas 24h")
    open_price: Decimal = Field(..., description="Precio de apertura en las últimas 24h")
    close_price: Decimal = Field(..., description="Precio de cierre en las últimas 24h")
    bid_price: Decimal = Field(..., description="Mejor precio de compra (bid)")
    bid_qty: Decimal = Field(..., description="Cantidad disponible al mejor precio de compra (bid)")
    ask_price: Decimal = Field(..., description="Mejor precio de venta (ask)")
    ask_qty: Decimal = Field(..., description="Cantidad disponible al mejor precio de venta (ask)")
    source: str = Field(..., description="Fuente del dato de mercado (ej. 'Binance', 'Mobula')")
    
    price_change_24h: Optional[Decimal] = Field(None, description="Cambio de precio en las últimas 24h")
    price_change_percentage_24h: Optional[Decimal] = Field(None, description="Cambio porcentual de precio en las últimas 24h")
    market_cap: Optional[Decimal] = Field(None, description="Capitalización de mercado del activo")
    rank: Optional[int] = Field(None, description="Ranking del activo por capitalización de mercado")
    number_of_trades: Optional[int] = Field(None, description="Número de operaciones en las últimas 24h")
```

**Validaciones Clave:**
*   Todos los campos numéricos (`price`, `volume`, etc.) deben ser convertidos a `Decimal` para asegurar precisión.
*   `timestamp` debe ser un objeto `datetime` válido.
*   `symbol` y `source` son campos obligatorios.

## 2. Esquema `OpportunityUnified`

**Propósito:** Estandarizar la representación de las oportunidades de arbitraje detectadas, facilitando su procesamiento y ejecución.

**Definición (Pydantic):**
```python
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
import uuid

from pydantic import BaseModel, Field

class OpportunityUnified(BaseModel):
    opportunity_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID único de la oportunidad")
    symbol: str = Field(..., description="Símbolo del par de trading principal de la oportunidad (ej. BTCUSDT)")
    base_asset: str = Field(..., description="Activo base de la oportunidad (ej. BTC)")
    quote_asset: str = Field(..., description="Activo de cotización de la oportunidad (ej. USDT)")
    profit_percentage: Decimal = Field(..., description="Porcentaje de ganancia esperado de la oportunidad")
    expected_profit_usd: Decimal = Field(..., description="Ganancia esperada en USD de la oportunidad")
    path: List[str] = Field(..., description="Lista de pares de trading que forman la ruta de arbitraje (ej. ['BTC/USDT', 'ETH/BTC', 'ETH/USDT'])")
    timestamp: datetime = Field(..., description="Marca de tiempo de detección de la oportunidad")
    expiration_time: Optional[datetime] = Field(None, description="Tiempo de expiración de la oportunidad, si aplica")
    status: str = Field("detected", description="Estado actual de la oportunidad (ej. 'detected', 'executed', 'failed')")
    source: str = Field(..., description="Fuente de la oportunidad (ej. 'Binance', 'Mobula', 'Combined')")
    details: Dict[str, Any] = Field({}, description="Diccionario para detalles adicionales específicos de la oportunidad")
```

**Validaciones Clave:**
*   `opportunity_id` se genera automáticamente.
*   `profit_percentage` y `expected_profit_usd` deben ser `Decimal`.
*   `path` debe ser una lista de cadenas.
*   `timestamp` debe ser un objeto `datetime` válido.
*   `symbol`, `base_asset`, `quote_asset`, `source` son campos obligatorios.

## 3. Reglas de Mapeo de Fuentes de Datos

### 3.1. Mapeo de Binance a `MarketDataUnified`

Los datos de Binance se obtienen principalmente del endpoint `/api/v3/ticker/24hr` y `/api/v3/depth`. Los valores numéricos se reciben como cadenas y deben ser convertidos a `Decimal`.

| Campo `MarketDataUnified` | Campo(s) Fuente Binance (Endpoint /api/v3/ticker/24hr) | Transformación |
| :------------------------ | :----------------------------------------------------- | :------------- |
| `symbol`                  | `symbol`                                               | Directo        |
| `timestamp`               | `closeTime`                                            | Convertir ms a `datetime` |
| `price`                   | `lastPrice`                                            | `str` a `Decimal` |
| `volume`                  | `volume`                                               | `str` a `Decimal` |
| `quote_volume`            | `quoteVolume`                                          | `str` a `Decimal` |
| `high_price`              | `highPrice`                                            | `str` a `Decimal` |
| `low_price`               | `lowPrice`                                             | `str` a `Decimal` |
| `open_price`              | `openPrice`                                            | `str` a `Decimal` |
| `close_price`             | `lastPrice` (o `closePrice` si disponible)             | `str` a `Decimal` |
| `bid_price`               | `bidPrice` (desde `/api/v3/depth` o ticker)            | `str` a `Decimal` |
| `bid_qty`                 | `bidQty` (desde `/api/v3/depth` o ticker)              | `str` a `Decimal` |
| `ask_price`               | `askPrice` (desde `/api/v3/depth` o ticker)            | `str` a `Decimal` |
| `ask_qty`                 | `askQty` (desde `/api/v3/depth` o ticker)              | `str` a `Decimal` |
| `source`                  | Fijo: "Binance"                                        | Directo        |
| `price_change_24h`        | `priceChange`                                          | `str` a `Decimal` |
| `price_change_percentage_24h` | `priceChangePercent`                               | `str` a `Decimal` |
| `number_of_trades`        | `count` (número de operaciones)                        | `int` directo  |
| `market_cap`              | N/A                                                    | No disponible |
| `rank`                    | N/A                                                    | No disponible |

### 3.2. Mapeo de Mobula a `MarketDataUnified` y `OpportunityUnified`

Los datos de Mobula se obtienen principalmente del endpoint `/api/1/market/multi-data`. Algunos campos numéricos ya pueden venir como `Decimal` o `float` desde el cliente de Mobula, pero se debe asegurar la conversión final a `Decimal` para consistencia.

#### 3.2.1. Mapeo a `MarketDataUnified`

| Campo `MarketDataUnified` | Campo(s) Fuente Mobula (Endpoint /api/1/market/multi-data) | Transformación |
| :------------------------ | :--------------------------------------------------------- | :------------- |
| `symbol`                  | `symbol`                                                   | Directo        |
| `timestamp`               | `last_updated`                                             | `datetime` directo |
| `price`                   | `price`                                                    | `Decimal` directo |
| `volume`                  | `volume_24h`                                               | `float` a `Decimal` |
| `quote_volume`            | N/A                                                        | No disponible |
| `high_price`              | N/A                                                        | No disponible |
| `low_price`               | N/A                                                        | No disponible |
| `open_price`              | N/A                                                        | No disponible |
| `close_price`             | `price` (último precio)                                    | `Decimal` directo |
| `bid_price`               | N/A                                                        | No disponible |
| `bid_qty`                 | N/A                                                        | No disponible |
| `ask_price`               | N/A                                                        | No disponible |
| `ask_qty`                 | N/A                                                        | No disponible |
| `source`                  | Fijo: "Mobula"                                             | Directo        |
| `price_change_24h`        | `price_change_24h`                                         | `float` a `Decimal` |
| `price_change_percentage_24h` | `price_change_percentage_24h`                          | `float` a `Decimal` |
| `market_cap`              | `market_cap`                                               | `float` a `Decimal` |
| `rank`                    | `rank`                                                     | `int` directo  |
| `number_of_trades`        | N/A                                                        | No disponible |

#### 3.2.2. Mapeo a `OpportunityUnified`

Las oportunidades de Mobula no se obtienen directamente de un endpoint específico de "oportunidades" como en Binance. En cambio, se construyen a partir de la lógica de detección de arbitraje que utiliza los datos de mercado de Mobula. Por lo tanto, los campos de `OpportunityUnified` se derivan de cálculos y combinaciones de datos, no de un mapeo directo de una única respuesta de API de Mobula.

| Campo `OpportunityUnified` | Origen (Derivado de Mobula Market Data) | Notas |
| :------------------------- | :-------------------------------------- | :---- |
| `opportunity_id`           | Generado por el sistema                 | `uuid.uuid4()` |
| `symbol`                   | Derivado de los pares de trading involucrados | Ej. "BTCUSDT" |
| `base_asset`               | Derivado del `symbol`                   | Ej. "BTC" |
| `quote_asset`              | Derivado del `symbol`                   | Ej. "USDT" |
| `profit_percentage`        | Calculado por la lógica de arbitraje    | Basado en precios de Mobula |
| `expected_profit_usd`      | Calculado por la lógica de arbitraje    | Basado en `profit_percentage` y monto de inversión |
| `path`                     | Definido por la ruta de arbitraje detectada | Lista de pares de trading |
| `timestamp`                | Marca de tiempo de detección            | `datetime.now()` |
| `expiration_time`          | Opcional, si la oportunidad tiene una vida útil limitada | |
| `status`                   | Inicialmente "detected"                 | Cambia según el ciclo de vida de la oportunidad |
| `source`                   | Fijo: "Mobula" o "Combined"             | Depende de si la oportunidad es puramente de Mobula o combinada con otras fuentes |
| `details`                  | Detalles adicionales de la oportunidad  | Puede incluir precios específicos de los exchanges, fees, etc. |

## 4. Campos Numéricos Críticos y Precisión Decimal

Los siguientes campos en los esquemas unificados requieren el uso del tipo `Decimal` de Python para asegurar la máxima precisión en cálculos financieros y de trading, evitando errores de punto flotante.

### 4.1. Campos en `MarketDataUnified`

| Campo                     | Tipo de Dato | Descripción                                       | Notas de Precisión |
| :------------------------ | :----------- | :------------------------------------------------ | :----------------- |
| `price`                   | `Decimal`    | Precio actual del activo                          | Alta precisión requerida para valores monetarios. |
| `volume`                  | `Decimal`    | Volumen de trading en la moneda base              | Alta precisión para cantidades. |
| `quote_volume`            | `Decimal`    | Volumen de trading en la moneda de cotización     | Alta precisión para cantidades. |
| `high_price`              | `Decimal`    | Precio más alto en las últimas 24h                | Alta precisión para valores monetarios. |
| `low_price`               | `Decimal`    | Precio más bajo en las últimas 24h                | Alta precisión para valores monetarios. |
| `open_price`              | `Decimal`    | Precio de apertura en las últimas 24h             | Alta precisión para valores monetarios. |
| `close_price`             | `Decimal`    | Precio de cierre en las últimas 24h               | Alta precisión para valores monetarios. |
| `bid_price`               | `Decimal`    | Mejor precio de compra (bid)                      | Alta precisión para valores monetarios. |
| `bid_qty`                 | `Decimal`    | Cantidad disponible al mejor precio de compra (bid) | Alta precisión para cantidades. |
| `ask_price`               | `Decimal`    | Mejor precio de venta (ask)                       | Alta precisión para valores monetarios. |
| `ask_qty`                 | `Decimal`    | Cantidad disponible al mejor precio de venta (ask) | Alta precisión para cantidades. |
| `price_change_24h`        | `Optional[Decimal]` | Cambio de precio en las últimas 24h           | Alta precisión para valores monetarios. |
| `price_change_percentage_24h` | `Optional[Decimal]` | Cambio porcentual de precio en las últimas 24h | Alta precisión para porcentajes. |
| `market_cap`              | `Optional[Decimal]` | Capitalización de mercado del activo          | Alta precisión para valores monetarios grandes. |

### 4.2. Campos en `OpportunityUnified`

| Campo                     | Tipo de Dato | Descripción                                       | Notas de Precisión |
| :------------------------ | :----------- | :------------------------------------------------ | :----------------- |
| `profit_percentage`       | `Decimal`    | Porcentaje de ganancia esperado de la oportunidad | Alta precisión para porcentajes. |
| `expected_profit_usd`     | `Decimal`    | Ganancia esperada en USD de la oportunidad        | Alta precisión para valores monetarios. |
