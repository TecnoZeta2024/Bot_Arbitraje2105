# Flujo de Datos - Scalper's Brain - Edición Personal

## Visión General del Flujo de Datos

Scalper's Brain implementa un flujo de datos complejo y optimizado que procesa información de múltiples exchanges, la enriquece con análisis de IA a través de MCPs, y la presenta en una interfaz PyQt5 de alta performance. El sistema está diseñado para latencia ultra-baja y procesamiento paralelo masivo.

## Diagrama de Flujo de Datos Principal

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Exchanges    │     │    WebSocket    │     │   Normalizer    │     │   Aggregator    │
│ Binance/Coinbase│────▶│    Streams      │────▶│   Unificado     │────▶│  Multi-Exchange │
│   EOD/Polygon   │     │                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │                         │
                                                          ▼                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Cache L1      │◀────│  Enrichment     │◀────│     MCPs        │◀────│   Dispatcher    │
│   (Memory)      │     │    Engine       │     │  Orquestador    │     │   Inteligente   │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                         │                         │
         ▼                       ▼                         ▼                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Cache L2      │     │   Multi-IA      │     │   Strategy      │     │   Execution     │
│    (Redis)      │────▶│   Analysis      │────▶│    Engine       │────▶│    Engine       │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                         │                         │
         ▼                       ▼                         ▼                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Cache L3      │     │   PyQt5 UI      │     │  Notification   │     │   Performance   │
│  (PostgreSQL)   │◀────│   Real-time     │◀────│    System       │◀────│    Tracker      │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Flujos de Datos Principales

### 1. Flujo de Datos de Mercado Multi-Exchange

**Origen → Destino:** Múltiples Exchanges → Sistema Unificado → UI/Trading

**Etapas:**

#### 1.1 Ingesta Paralela
```python
# Implementación conceptual
class UnifiedMarketDataIngester:
    def __init__(self):
        self.adapters = {
            'binance': BinanceAdapter(),
            'coinbase': CoinbaseAdapter(),
            'eod': EODHistoricalAdapter(),
            'polygon': PolygonAdapter()
        }
        self.normalizer = DataNormalizer()
        self.aggregator = OrderbookAggregator()
    
    async def ingest_all(self):
        tasks = []
        for exchange, adapter in self.adapters.items():
            tasks.append(self._ingest_exchange(exchange, adapter))
        
        async for normalized_data in self._process_streams(tasks):
            yield normalized_data
```

#### 1.2 Normalización Universal
- **Timestamp unification**: Conversión a UTC nanosegundos
- **Decimal precision**: Manejo consistente con Decimal para evitar float errors
- **Symbol mapping**: Traducción entre nomenclaturas de exchanges
- **Order type standardization**: Unificación de tipos de órdenes
- **Fee structure normalization**: Cálculo unificado de comisiones

#### 1.3 Agregación Inteligente
- **Best bid/ask calculation**: Mejor precio disponible cross-exchange
- **Liquidity depth analysis**: Profundidad agregada del orderbook
- **Arbitrage detection**: Identificación instantánea de discrepancias
- **Volume weighted prices**: VWAP en tiempo real
- **Market microstructure**: Análisis de spread y volatilidad

### 2. Flujo de Enriquecimiento con MCPs

**Origen → Destino:** Datos Normalizados → MCPs → Datos Enriquecidos

**Pipeline de MCPs:**

```yaml
mcp_pipeline:
  - stage_1_technical:
      - crypto-indicators-mcp:
          indicators: [RSI, MACD, BB, ATR, EMA]
          timeframes: [1m, 5m, 15m, 1h]
      - custom-patterns-mcp:
          patterns: [triangles, flags, channels]
  
  - stage_2_fundamental:
      - coinmarketcap-mcp:
          data: [mcap, volume, dominance]
      - on_chain-mcp:
          metrics: [whale_movements, exchange_flows]
  
  - stage_3_sentiment:
      - crypto-sentiment-mcp:
          sources: [twitter, reddit, telegram]
      - cryptopanic-mcp:
          filter: [high_impact, verified]
  
  - stage_4_execution:
      - freqtrade-mcp: # Premium only
          mode: [dry_run, live]
```

### 3. Flujo de Análisis Multi-IA

**Origen → Destino:** Datos Enriquecidos → LLMs → Decisiones de Trading

**Arquitectura de Consenso:**

```python
class MultiAIConsensusEngine:
    def __init__(self):
        self.providers = {
            'gemini': GeminiProvider(model='gemini-1.5-flash'),  # Free
            'gpt4o_mini': GPT4MiniProvider(),  # Premium
            'claude': ClaudeProvider(),  # Premium
            'local': LocalLLMProvider()  # Open source
        }
        self.voting_weights = {
            'gemini': 0.3,
            'gpt4o_mini': 0.35,
            'claude': 0.25,
            'local': 0.1
        }
    
    async def analyze(self, market_context: Dict) -> TradingDecision:
        # Parallel analysis
        analyses = await asyncio.gather(*[
            provider.analyze(market_context) 
            for provider in self.providers.values()
        ])
        
        # Weighted consensus
        return self._calculate_consensus(analyses)
```

### 4. Flujo de Visualización en PyQt5

**Origen → Destino:** Todos los Componentes → UI Thread-Safe → Widgets

**Sistema de Actualización:**

```python
class RealTimeUIUpdater:
    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.update_queue = asyncio.Queue()
        self.update_signals = {
            'market_data': pyqtSignal(dict),
            'portfolio': pyqtSignal(dict),
            'signals': pyqtSignal(list),
            'alerts': pyqtSignal(dict)
        }
    
    async def update_loop(self):
        while True:
            update = await self.update_queue.get()
            
            # Thread-safe UI update
            QMetaObject.invokeMethod(
                self.main_window,
                self._apply_update,
                Qt.QueuedConnection,
                Q_ARG(dict, update)
            )
```

### 5. Flujo de Ejecución Inteligente

**Origen → Destino:** Señales de Trading → Smart Router → Exchanges

**Smart Order Routing (SOR):**

```python
class SmartOrderRouter:
    def __init__(self):
        self.execution_algos = {
            'iceberg': IcebergAlgorithm(),
            'twap': TWAPAlgorithm(),
            'sniper': SniperAlgorithm(),
            'adaptive': AdaptiveAlgorithm()
        }
    
    async def route_order(self, order: Order) -> ExecutionResult:
        # Analyze order characteristics
        order_profile = self._profile_order(order)
        
        # Select best execution venue
        best_venue = self._select_venue(order_profile)
        
        # Choose execution algorithm
        algo = self._select_algorithm(order_profile)
        
        # Execute with monitoring
        return await algo.execute(order, best_venue)
```

## Optimizaciones de Performance

### 1. Zero-Copy Data Passing
- Uso de memoria compartida para datos grandes
- Referencias inmutables entre componentes
- Buffers reutilizables para WebSocket

### 2. Procesamiento por Lotes Inteligente
```python
class BatchProcessor:
    def __init__(self, batch_size=1000, max_latency_ms=10):
        self.batch_size = batch_size
        self.max_latency_ms = max_latency_ms
        self.buffer = []
        self.last_flush = time.time()
    
    async def process(self, item):
        self.buffer.append(item)
        
        if len(self.buffer) >= self.batch_size or \
           (time.time() - self.last_flush) * 1000 > self.max_latency_ms:
            await self._flush()
```

### 3. Caché Predictivo
- Pre-fetching basado en patrones de uso
- Invalidación inteligente con TTL dinámico
- Compresión automática de datos históricos

### 4. Paralelización Masiva
- Thread pools para cálculos CPU-intensive
- AsyncIO para I/O operations
- Multiprocessing para backtesting

## Manejo de Datos Críticos

### 1. Datos de Orderbook
- **Formato**: Estructura columnar optimizada
- **Updates**: Incremental con checksums
- **Snapshot**: Cada 1000 updates o 30 segundos
- **Compresión**: zstd para históricos

### 2. Datos de Trading
- **Journaling**: Write-ahead logging
- **Replication**: Master-slave con failover
- **Encryption**: AES-256 para datos sensibles
- **Audit trail**: Inmutable con hashes

### 3. Datos de Configuración
- **Hot reload**: Sin reiniciar sistema
- **Versioning**: Git-like para rollback
- **Validation**: Schema enforcement
- **Distribution**: Pub-sub para cambios

## Flujos de Emergencia

### 1. Circuit Breakers
```python
class DataFlowCircuitBreaker:
    def __init__(self, failure_threshold=5, timeout_seconds=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
```

### 2. Fallback Mechanisms
- Exchange failover automático
- Caché como fuente temporal
- Modo degradado con funcionalidad limitada
- Alertas multi-canal

### 3. Data Recovery
- Replay desde último checkpoint
- Reconciliación automática
- Gap filling desde fuentes alternativas

## Métricas de Flujo de Datos

### 1. Latencia End-to-End
- **Target**: < 10ms (percentil 99)
- **Medición**: Desde recepción hasta UI
- **Breakdown**: Por componente

### 2. Throughput
- **Capacity**: 1M mensajes/segundo
- **Sustained**: 100K mensajes/segundo
- **Burst handling**: 10x capacity por 10 segundos

### 3. Data Quality
- **Completeness**: 99.99%
- **Accuracy**: Validación cruzada
- **Freshness**: Age tracking por dato

## Integración con Modelo Gratuito vs Premium

### Modelo Gratuito
- **Exchanges**: Binance, Coinbase (WebSocket público)
- **Rate limits**: 100 requests/min
- **Históricos**: Últimas 24 horas
- **MCPs**: Básicos sin límites estrictos

### Modelo Premium
- **Exchanges**: +EOD, Polygon, APIs privadas
- **Rate limits**: Ilimitado con pooling
- **Históricos**: 5+ años tick-by-tick
- **MCPs**: Todos incluyendo freqtrade
- **Priority queues**: Para ejecución

---

*Este diseño de flujo de datos representa un salto cuántico respecto al sistema original, manteniendo la robustez pero agregando capacidades de procesamiento paralelo masivo, integración multi-fuente y optimizaciones de latencia ultra-baja necesarias para competir en mercados modernos.*
