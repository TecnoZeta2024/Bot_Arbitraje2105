# Patrón Arquitectónico - Scalper's Brain - Edición Personal

## Arquitectura General

Scalper's Brain implementa una **Arquitectura Limpia (Clean Architecture)** evolucionada, combinada con **Arquitectura Hexagonal (Ports and Adapters)** y **Arquitectura Basada en Eventos (Event-Driven Architecture)**. Adicionalmente, incorpora el patrón **MCP (Model Context Protocol)** para modularidad extrema, manteniendo los principios de **Domain-Driven Design (DDD)**.

## Evolución Arquitectónica

La arquitectura evoluciona del Bot_Arbitraje2105 añadiendo:
- **Capa de Presentación Rica**: UI PyQt5 con patrón MVP (Model-View-Presenter)
- **Orquestación de MCPs**: Nueva capa para gestión de Model Context Protocols
- **Multi-Provider Pattern**: Abstracción para múltiples exchanges y LLMs
- **Event Sourcing Parcial**: Para auditoría y reproducibilidad
- **CQRS Completo**: Separación total de lecturas y escrituras

## Diagrama de Capas Expandido

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CAPA DE PRESENTACIÓN                              │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │   PyQt5 UI   │  │  Streamlit   │  │   REST API   │  │  WebSocket  │ │
│  │   (Main)     │  │  Dashboard   │  │   Server     │  │   Server    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
│         │                  │                  │                 │        │
│         └──────────────────┴──────────────────┴─────────────────┘        │
│                                   │                                       │
│                            ┌──────▼────────┐                             │
│                            │   Presenter   │                             │
│                            │    Layer      │                             │
│                            └──────┬────────┘                             │
└────────────────────────────────────┼─────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      CAPA DE APLICACIÓN                                  │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Casos de    │  │  Servicios   │  │   Command    │  │   Query     │ │
│  │     Uso      │  │ Aplicación   │  │   Handlers   │  │  Handlers   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
│         │                  │                  │                 │        │
│         └──────────────────┴──────────────────┴─────────────────┘        │
│                                   │                                       │
│                            ┌──────▼────────┐                             │
│                            │ Event Bus &   │                             │
│                            │ Message Queue │                             │
│                            └──────┬────────┘                             │
└────────────────────────────────────┼─────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        CAPA DE DOMINIO                                   │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Entidades   │  │  Agregados   │  │   Servicios  │  │    Value    │ │
│  │              │  │              │  │   Dominio    │  │   Objects   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │    Eventos   │  │ Repositorios │  │   Políticas  │  │   Fábricas  │ │
│  │   Dominio    │  │ (Interfaces) │  │   Negocio    │  │             │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CAPA DE ORQUESTACIÓN MCP                             │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  MCP Router  │  │MCP Discovery │  │MCP Lifecycle │  │ MCP Health  │ │
│  │              │  │   Service    │  │   Manager    │  │   Monitor   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
│         │                  │                  │                 │        │
│         └──────────────────┴──────────────────┴─────────────────┘        │
│                                   │                                       │
│  ┌────────────────────────────────┼─────────────────────────────────┐   │
│  │                         MCP Adapters                              │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│  │  │Indicator│ │Sentiment│ │  News   │ │CoinMCap │ │FreqTrade│   │   │
│  │  │   MCP   │ │   MCP   │ │   MCP   │ │   MCP   │ │   MCP   │   │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │
│  └───────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   CAPA DE INFRAESTRUCTURA                               │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Repository  │  │   Exchange   │  │      LLM     │  │    Cache    │ │
│  │    Impls     │  │   Adapters   │  │   Providers  │  │   Layers    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  WebSocket   │  │   Database   │  │   Message    │  │  External   │ │
│  │  Managers    │  │  Connectors  │  │    Queue     │  │    APIs     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

## Patrones de Diseño Implementados

### 1. Model-View-Presenter (MVP) - NUEVO
Para la capa de presentación PyQt5:
- **Model**: Datos del dominio expuestos via ViewModels
- **View**: Widgets PyQt5 sin lógica de negocio
- **Presenter**: Coordinación entre View y Model

### 2. Adapter Pattern Extendido
Múltiples niveles de adaptadores:
- **Exchange Adapters**: Binance, Coinbase, EOD, Polygon
- **LLM Adapters**: Gemini, OpenAI, Claude
- **MCP Adapters**: Cada MCP con su adaptador específico

### 3. Strategy Pattern Mejorado
```python
class TradingStrategy(ABC):
    @abstractmethod
    async def analyze(self, market_data: MarketData) -> Signal:
        pass
    
    @abstractmethod
    async def execute(self, signal: Signal) -> ExecutionResult:
        pass

class ScalpingStrategy(TradingStrategy):
    def __init__(self, mcp_orchestrator: MCPOrchestrator):
        self.mcp_orchestrator = mcp_orchestrator
        
    async def analyze(self, market_data: MarketData) -> Signal:
        # Usar MCPs para análisis
        indicators = await self.mcp_orchestrator.call_mcp(
            "crypto-indicators", 
            market_data
        )
        sentiment = await self.mcp_orchestrator.call_mcp(
            "crypto-sentiment",
            market_data.symbol
        )
        return self._generate_signal(indicators, sentiment)
```

### 4. Chain of Responsibility para Validación
```python
class ValidationChain:
    def __init__(self):
        self.validators = [
            BalanceValidator(),
            RiskLimitValidator(),
            MarketConditionValidator(),
            ComplianceValidator()
        ]
    
    async def validate(self, order: Order) -> ValidationResult:
        for validator in self.validators:
            result = await validator.validate(order)
            if not result.is_valid:
                return result
        return ValidationResult(is_valid=True)
```

### 5. Event Sourcing Parcial
Para operaciones críticas:
```python
@dataclass
class TradingEvent:
    event_id: str
    event_type: str
    aggregate_id: str
    timestamp: datetime
    data: Dict[str, Any]
    
class EventStore:
    async def append(self, event: TradingEvent):
        # Persistir evento inmutable
        pass
    
    async def get_events(self, aggregate_id: str) -> List[TradingEvent]:
        # Recuperar historial de eventos
        pass
```

### 6. CQRS (Command Query Responsibility Segregation)
Separación completa de lecturas y escrituras:
```python
# Commands
class CreateOrderCommand:
    def __init__(self, order_data: OrderData):
        self.order_data = order_data

class CreateOrderHandler:
    async def handle(self, command: CreateOrderCommand):
        # Lógica de escritura
        pass

# Queries
class GetPortfolioQuery:
    def __init__(self, user_id: str):
        self.user_id = user_id

class GetPortfolioHandler:
    async def handle(self, query: GetPortfolioQuery):
        # Lógica optimizada de lectura
        pass
```

### 7. Saga Pattern para Transacciones Distribuidas
```python
class ArbitrageSaga:
    def __init__(self):
        self.steps = [
            BuyStep(),
            TransferStep(),
            SellStep()
        ]
        self.compensations = []
    
    async def execute(self):
        for step in self.steps:
            try:
                result = await step.execute()
                self.compensations.append(step.compensate)
            except Exception as e:
                await self._compensate()
                raise
```

### 8. Circuit Breaker para Servicios Externos
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError()
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
```

## Principios SOLID Reforzados

### 1. SRP - Responsabilidad Única
- Cada MCP tiene una responsabilidad específica
- Presenters separados por vista
- Handlers específicos por comando/query

### 2. OCP - Abierto/Cerrado
- Nuevos MCPs sin modificar el orquestador
- Nuevas estrategias sin tocar el motor
- Nuevos exchanges via adaptadores

### 3. LSP - Sustitución de Liskov
- Todos los exchanges implementan IExchangeAdapter
- Todos los LLMs implementan ILLMProvider
- Todos los MCPs implementan IMCPAdapter

### 4. ISP - Segregación de Interfaces
```python
# Interfaces específicas y enfocadas
class IMarketDataProvider(Protocol):
    async def get_ticker(self, symbol: str) -> Ticker: ...

class IOrderExecutor(Protocol):
    async def place_order(self, order: Order) -> OrderResult: ...

class IHistoricalDataProvider(Protocol):
    async def get_candles(self, symbol: str, interval: str) -> List[Candle]: ...
```

### 5. DIP - Inversión de Dependencias
- Dominio no conoce infraestructura
- Aplicación depende de abstracciones
- Infraestructura implementa contratos del dominio

## Patrones Adicionales para Escalabilidad

### 1. Bulkhead Pattern
Aislamiento de recursos para prevenir fallas en cascada:
```python
class ResourcePool:
    def __init__(self, name: str, size: int):
        self.name = name
        self.semaphore = asyncio.Semaphore(size)
    
    async def acquire(self):
        async with self.semaphore:
            yield
```

### 2. Retry Pattern con Backoff Exponencial
```python
class RetryPolicy:
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
    
    async def execute(self, func, *args, **kwargs):
        for attempt in range(self.max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_attempts - 1:
                    raise
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
```

### 3. Rate Limiter Pattern
```python
class RateLimiter:
    def __init__(self, rate: int, per: float):
        self.rate = rate
        self.per = per
        self.tokens = rate
        self.updated_at = time.time()
    
    async def acquire(self):
        while self.tokens <= 0:
            now = time.time()
            elapsed = now - self.updated_at
            self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.per))
            self.updated_at = now
            if self.tokens <= 0:
                await asyncio.sleep(0.1)
        
        self.tokens -= 1
```

## Evolución y Mejoras Clave

### Respecto al Bot_Arbitraje2105:
1. **Presentación Rica**: De API-only a UI completa
2. **Multi-Exchange**: De Binance-only a agregación
3. **Multi-Estrategia**: De arbitraje-only a completo
4. **Modularidad MCP**: Capacidades pluggables
5. **IA Avanzada**: De Gemini-only a multi-provider
6. **Observabilidad**: Métricas y trazabilidad completas

### Preparación para el Futuro:
1. **Cloud-Ready**: Diseño distribuible
2. **Multi-Tenant**: Bases para SaaS
3. **Plugin System**: Extensibilidad total
4. **API First**: Todo expuesto como API
5. **Event Streaming**: Preparado para Kafka/Pulsar

---

*Esta arquitectura representa una evolución natural que mantiene las fortalezas del diseño original mientras añade las capacidades necesarias para una plataforma de trading completa y profesional.*
