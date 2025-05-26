# Estructuras de Datos de Fuentes Externas

Este documento detalla las estructuras de datos clave obtenidas de las APIs de Binance y Mobula, identificando los campos relevantes y sus tipos de datos para la normalización.

## 1. Binance API

Los datos de Binance a menudo se reciben como cadenas para valores numéricos, que luego son convertidos a `float` en el cliente. Para la normalización, se deben considerar estos campos como `Decimal` para mantener la precisión.

### 1.1. Ticker (24hr) - `get_ticker`, `get_tickers`
Endpoint: `/api/v3/ticker/24hr`
Ejemplo de campos clave:
- `symbol`: `str` (ej. "BTCUSDT")
- `priceChange`: `str` (convertir a `Decimal`)
- `priceChangePercent`: `str` (convertir a `Decimal`)
- `weightedAvgPrice`: `str` (convertir a `Decimal`)
- `lastPrice`: `str` (convertir a `Decimal`)
- `volume`: `str` (convertir a `Decimal`)
- `quoteVolume`: `str` (convertir a `Decimal`)
- `openTime`: `int` (timestamp en ms)
- `closeTime`: `int` (timestamp en ms)

### 1.2. Precios (último) - `obtener_precio_ticker`, `obtener_precios_todos`
Endpoint: `/api/v3/ticker/price`
Ejemplo de campos clave:
- `symbol`: `str`
- `price`: `str` (convertir a `Decimal`)

### 1.3. Profundidad de Mercado (Order Book) - `obtener_profundidad_mercado`
Endpoint: `/api/v3/depth`
Ejemplo de campos clave:
- `lastUpdateId`: `int`
- `bids`: `List[List[str, str]]` (lista de [precio, cantidad], ambos `str` a `Decimal`)
- `asks`: `List[List[str, str]]` (lista de [precio, cantidad], ambos `str` a `Decimal`)

### 1.4. Velas (Klines) - `obtener_klines`
Endpoint: `/api/v3/klines`
Ejemplo de estructura: `List[List[Any]]`
Cada vela: `[Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, Number of trades, Taker buy base asset volume, Taker buy quote asset volume, Ignore]`
- `Open time`: `int` (timestamp en ms)
- `Open`, `High`, `Low`, `Close`, `Volume`, `Quote asset volume`, `Taker buy base asset volume`, `Taker buy quote asset volume`: `str` (convertir a `Decimal`)

### 1.5. Información de Cuenta - `get_account_info`, `get_balances`
Endpoint: `/api/v3/account`
Ejemplo de campos clave:
- `balances`: `List[Dict]`
  - `asset`: `str`
  - `free`: `str` (convertir a `Decimal`)
  - `locked`: `str` (convertir a `Decimal`)

### 1.6. Información de Exchange - `obtener_info_exchange`, `obtener_reglas_simbolo`
Endpoint: `/api/v3/exchangeInfo`
Ejemplo de campos clave:
- `symbols`: `List[Dict]`
  - `symbol`: `str`
  - `status`: `str`
  - `baseAsset`: `str`
  - `quoteAsset`: `str`
  - `filters`: `List[Dict]` (ej. `LOT_SIZE` con `minQty`, `maxQty`, `stepSize` como `str` a `Decimal`)

## 2. Mobula API

Mobula ya realiza algunas conversiones a `Decimal` en su cliente, pero es importante verificar la consistencia y aplicar `Decimal` a todos los campos numéricos relevantes.

### 2.1. Datos de Mercado - `get_market_data`
Endpoint: `/api/1/market/multi-data`
Ejemplo de campos clave (dentro de `data` por activo):
- `symbol`: `str`
- `price`: `Decimal` (ya convertido en cliente)
- `price_change_24h`: `float`
- `price_change_percentage_24h`: `float`
- `market_cap`: `float`
- `volume_24h`: `float`
- `circulating_supply`: `float`
- `total_supply`: `float`
- `ath`: `float`
- `atl`: `float`
- `rank`: `int`
- `last_updated`: `datetime` (ya convertido en cliente)

### 2.2. Información de Token - `get_token_info`
Endpoint: `/api/1/metadata`
Ejemplo de campos clave (dentro de `data`):
- `name`: `str`
- `symbol`: `str`
- `description`: `str`
- `total_supply`: `float`
- `max_supply`: `float`
- `contracts`: `List[Dict]` (ej. `address`, `blockchain`)

### 2.3. Datos Históricos - `get_historical_data`
Endpoint: `/api/1/market/history`
Ejemplo de estructura (dentro de `data.price_history`): `List[List[int, float, float]]`
Cada punto: `[timestamp, price, market_cap]`
- `timestamp`: `datetime` (ya convertido en cliente)
- `price`: `Decimal` (ya convertido en cliente)
- `market_cap`: `float`

### 2.4. Métricas de Mercado - `get_market_metrics`
Endpoint: `/api/1/market/metrics`
Ejemplo de campos clave (dentro de `data`):
- `volatility_24h`: `float`
- `volatility_7d`: `float`
- `volume_to_market_cap`: `float`
- `liquidity_score`: `float`
- `holder_count`: `int`
- `social_score`: `float`
- `development_score`: `float`
- `community_score`: `float`

### 2.5. Top Ganadores/Perdedores - `get_top_gainers_losers`
Endpoint: `/api/1/market/data`
Ejemplo de estructura (dentro de `gainers` o `losers`): `List[Dict]`
Cada item:
- `symbol`: `str`
- `price`: `float`
- `change_24h`: `float`

### 2.6. Búsqueda de Tokens - `search_tokens`
Endpoint: `/api/1/search`
Ejemplo de estructura (dentro de `data`): `List[Dict]`
Cada item:
- `name`: `str`
- `symbol`: `str`
- `market_cap`: `float`
- `price`: `float`

### 2.7. Tokens en Tendencia - `get_trending_tokens`
Endpoint: `/api/1/market/trending`
Ejemplo de estructura (dentro de `data`): `List[Dict]`
Cada item:
- `symbol`: `str`
- `name`: `str`
- `price`: `float`
- `change_24h`: `float`
- `volume_24h`: `float`
- `market_cap`: `float`
- `trending_score`: `float`
