# Patrón Arquitectónico - Scalper's Brain - Edición Personal

## Arquitectura General

Scalper's Brain evoluciona la arquitectura limpia original hacia una **Arquitectura Orientada a Eventos con Microservicios Opcionales**, manteniendo los principios de Domain-Driven Design (DDD) y agregando capacidades de procesamiento distribuido. La arquitectura permite comenzar como monolito modular y escalar a microservicios según necesidad.

## Diagrama de Arquitectura Evolutiva

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CAPA DE PRESENTACIÓN                              │
│                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   PyQt5     │  │   Web API   │  │  WebSocket  │  │   Mobile    │   │
│  │   Desktop   │  │  (FastAPI)  │  │   Server    │  │   (Future)  │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
└─────────┼────────────────┼────────────────┼────────────────┼───────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CAPA DE APLICACIÓN (Use Cases)                        │
│                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Trading    │  │  Analysis   │  │   Risk      │  │  Portfolio  │   │
│  │  Commands   │  │  Queries    │  │  Commands   │  │   Queries   │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
└─────────┼────────────────┼────────────────┼────────────────┼───────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EVENT BUS / MEDIATOR                             │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  Domain Events | Integration Events | Command Bus | Query Bus   │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      CAPA DE DOMINIO (Core)                              │
│                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Trading    │  │   Market    │  │    Risk     │  │     AI      │   │
│  │  Aggregate  │  │  Aggregate  │  │  Aggregate  │  │  Aggregate  │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   Domain    │  │   Domain    │  │   Value     │  │  Domain     │   │
│  │  Services   │  │   Events    │  │   Objects   │  │   Rules     │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CAPA DE INFRAESTRUCTURA                               │
│                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │  Exchange   │  │     MCP     │  │     AI      │  │  Database   │   │
│  │  Adapters   │  │ Orchestrator│  │  Providers  │  │  Adapters   │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   Message   │  │    Cache    │  │  Monitoring │  │   File      │   │
│  │    Queue    │  │   System    │  │   System    │  │   System    │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Principios Arquitectónicos Fundamentales

### 1. Event-Driven Architecture (EDA)

El sistema se basa en eventos para comunicación desacoplada:

```python
# Domain Event
@dataclass
class TradingSignalDetected(DomainEvent):
    signal_id: str
    symbol: str
    strategy: str
    action: TradingAction
    confidence: float
    timestamp: datetime
    metadata: Dict[str, Any]

# Event Handler
class TradingSignalHandler(IEventHandler[TradingSignalDetected]):
    def __init__(self, 
                 trading_service: ITradingService,
                 risk_manager: IRiskManager,
                 notification_service: INotificationService):
        self.trading_service = trading_service
        self.risk_manager = risk_manager
        self.notification_service = notification_service
    
    async def handle(self, event: TradingSignalDetected) -> None:
        # Validate with risk manager
        if await self.risk_manager.approve_signal(event):
            # Execute trade
            result = await self.trading_service.execute_signal(event)
            
            # Notify user
            await self.notification_service.notify_trade_execution(result)
```

### 2. CQRS (Command Query Responsibility Segregation)

Separación clara entre comandos y consultas:

```python
# Command
@dataclass
class ExecuteTradeCommand(Command):
    symbol: str
    side: TradeSide
    quantity: Decimal
    order_type: OrderType
    user_id: str

# Command Handler
class ExecuteTradeCommandHandler(ICommandHandler[ExecuteTradeCommand]):
    async def handle(self, command: ExecuteTradeCommand) -> TradeResult:
        # Business logic for trade execution
        ...

# Query
@dataclass
class GetPortfolioPerformanceQuery(Query):
    user_id: str
    start_date: datetime
    end_date: datetime

# Query Handler
class GetPortfolioPerformanceQueryHandler(IQueryHandler[GetPortfolioPerformanceQuery]):
    async def handle(self, query: GetPortfolioPerformanceQuery) -> PortfolioPerformance:
        # Optimized read model for performance data
        ...
```

### 3. Agregados Mejorados

Agregados con mejor encapsulación y event sourcing opcional:

```python
class TradingSession(AggregateRoot):
    """Agregado que representa una sesión de trading"""
    
    def __init__(self, session_id: str, user_id: str):
        super().__init__()
        self.session_id = session_id
        self.user_id = user_id
        self.status = SessionStatus.INACTIVE
        self.active_strategies: List[Strategy] = []
        self.performance_metrics = PerformanceMetrics()
        
    def start_session(self, strategies: List[Strategy]) -> None:
        """Inicia una sesión de trading"""
        if self.status != SessionStatus.INACTIVE:
            raise DomainError("Cannot start an active session")
        
        self.status = SessionStatus.ACTIVE
        self.active_strategies = strategies
        self.started_at = datetime.utcnow()
        
        # Emit domain event
        self.add_domain_event(
            TradingSessionStarted(
                session_id=self.session_id,
                user_id=self.user_id,
                strategies=[s.name for s in strategies],
                started_at=self.started_at
            )
        )
    
    def execute_trade(self, trade: Trade) -> None:
        """Ejecuta un trade dentro de la sesión"""
        if self.status != SessionStatus.ACTIVE:
            raise DomainError("Cannot execute trade in inactive session")
        
        # Validate trade against session rules
        self._validate_trade(trade)
        
        # Update metrics
        self.performance_metrics.add_trade(trade)
        
        # Emit event
        self.add_domain_event(
            TradeExecuted(
                session_id=self.session_id,
                trade_id=trade.id,
                symbol=trade.symbol,
                pnl=trade.calculate_pnl()
            )
        )
```

### 4. Bounded Contexts Definidos

El sistema se divide en contextos delimitados claros:

```yaml
bounded_contexts:
  trading:
    aggregates: [TradingSession, Order, Position]
    services: [ExecutionService, OrderManagementService]
    events: [OrderPlaced, OrderFilled, PositionOpened, PositionClosed]
    
  market_data:
    aggregates: [MarketDataFeed, PriceHistory]
    services: [DataNormalizationService, AggregationService]
    events: [PriceUpdated, VolumeSpike, MarketOpened]
    
  risk_management:
    aggregates: [RiskProfile, RiskLimit]
    services: [RiskCalculationService, ComplianceService]
    events: [RiskLimitBreached, DrawdownAlert]
    
  analytics:
    aggregates: [AnalysisReport, AIModel]
    services: [TechnicalAnalysisService, SentimentAnalysisService]
    events: [SignalGenerated, AnalysisCompleted]
    
  portfolio:
    aggregates: [Portfolio, Asset]
    services: [ValuationService, AllocationService]
    events: [PortfolioRebalanced, AssetAllocated]
```

### 5. Patrón Repository Mejorado

Repositorios con soporte para proyecciones y event sourcing:

```python
class TradingSessionRepository(IRepository[TradingSession]):
    """Repository con capacidades avanzadas"""
    
    def __init__(self, 
                 event_store: IEventStore,
                 snapshot_store: ISnapshotStore,
                 cache: ICache):
        self.event_store = event_store
        self.snapshot_store = snapshot_store
        self.cache = cache
    
    async def get_by_id(self, session_id: str) -> Optional[TradingSession]:
        # Try cache first
        cached = await self.cache.get(f"session:{session_id}")
        if cached:
            return cached
        
        # Try snapshot
        snapshot = await self.snapshot_store.get_latest(session_id)
        
        # Rebuild from events
        events = await self.event_store.get_events(
            aggregate_id=session_id,
            from_version=snapshot.version if snapshot else 0
        )
        
        session = self._rebuild_from_events(snapshot, events)
        
        # Cache for future requests
        await self.cache.set(f"session:{session_id}", session, ttl=300)
        
        return session
    
    async def save(self, session: TradingSession) -> None:
        # Save events
        if session.uncommitted_events:
            await self.event_store.save_events(
                aggregate_id=session.session_id,
                events=session.uncommitted_events,
                expected_version=session.version
            )
        
        # Update snapshot if needed
        if session.version % 10 == 0:  # Every 10 events
            await self.snapshot_store.save(session)
        
        # Update cache
        await self.cache.set(f"session:{session.session_id}", session)
        
        # Clear uncommitted events
        session.mark_events_as_committed()
```

### 6. Saga Pattern para Transacciones Distribuidas

Gestión de procesos de negocio complejos:

```python
class ArbitrageTradingSaga(ISaga):
    """Saga para ejecutar arbitraje triangular"""
    
    def __init__(self, 
                 command_bus: ICommandBus,
                 query_bus: IQueryBus):
        self.command_bus = command_bus
        self.query_bus = query_bus
        self.state = SagaState()
    
    async def handle(self, event: ArbitrageOpportunityDetected) -> None:
        try:
            # Step 1: Check available balance
            balance = await self.query_bus.query(
                GetAvailableBalanceQuery(event.base_currency)
            )
            
            if balance < event.required_amount:
                await self._compensate("Insufficient balance")
                return
            
            # Step 2: Place first order
            order1_result = await self.command_bus.send(
                PlaceOrderCommand(
                    symbol=event.pair1,
                    side=event.side1,
                    quantity=event.quantity1
                )
            )
            self.state.add_step("order1", order1_result)
            
            # Step 3: Place second order
            order2_result = await self.command_bus.send(
                PlaceOrderCommand(
                    symbol=event.pair2,
                    side=event.side2,
                    quantity=event.quantity2
                )
            )
            self.state.add_step("order2", order2_result)
            
            # Step 4: Place third order
            order3_result = await self.command_bus.send(
                PlaceOrderCommand(
                    symbol=event.pair3,
                    side=event.side3,
                    quantity=event.quantity3
                )
            )
            self.state.add_step("order3", order3_result)
            
            # Success - emit completion event
            await self._complete_saga(event)
            
        except Exception as e:
            # Compensate all completed steps
            await self._compensate(str(e))
```

## Patrones de Diseño Adicionales

### 1. Circuit Breaker Pattern

Protección contra fallos en servicios externos:

```python
class CircuitBreaker:
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Type[Exception] = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
```

### 2. Bulkhead Pattern

Aislamiento de recursos para prevenir fallos en cascada:

```python
class BulkheadExecutor:
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def execute(self, func: Callable, *args, **kwargs):
        async with self.semaphore:
            return await func(*args, **kwargs)
```

### 3. Strategy Pattern Mejorado

Estrategias de trading como plugins:

```python
class StrategyPlugin(ABC):
    """Base para todas las estrategias de trading"""
    
    @abstractmethod
    def get_metadata(self) -> StrategyMetadata:
        pass
    
    @abstractmethod
    async def analyze(self, market_data: MarketData) -> List[Signal]:
        pass
    
    @abstractmethod
    def get_required_indicators(self) -> List[str]:
        pass
    
    @abstractmethod
    def get_required_mcps(self) -> List[str]:
        pass
```

## Modelo de Deployment

### 1. Monolito Modular (Inicio)
```yaml
deployment:
  type: monolithic
  modules:
    - ui-module
    - trading-module
    - market-data-module
    - risk-module
    - analytics-module
```

### 2. Microservicios (Escalado)
```yaml
deployment:
  type: microservices
  services:
    - name: trading-service
      replicas: 3
      resources:
        cpu: 2
        memory: 4Gi
    
    - name: market-data-service
      replicas: 5
      resources:
        cpu: 4
        memory: 8Gi
```

## Principios SOLID Aplicados - Mejorados

### 1. Single Responsibility Principle (SRP)
- Cada agregado maneja su propio estado
- Servicios con responsabilidad única
- Handlers separados por tipo de operación

### 2. Open/Closed Principle (OCP)
- Estrategias como plugins
- MCPs como extensiones
- Proveedores de IA intercambiables

### 3. Liskov Substitution Principle (LSP)
- Todas las implementaciones respetan contratos
- Adapters transparentes para exchanges
- Providers de IA con interfaz común

### 4. Interface Segregation Principle (ISP)
- Interfaces específicas por contexto
- Separación read/write models
- APIs granulares

### 5. Dependency Inversion Principle (DIP)
- Dominio no depende de infraestructura
- Inyección de dependencias mejorada
- Abstracciones para todo servicio externo

---

*Esta arquitectura representa una evolución significativa que mantiene los principios sólidos del sistema original mientras agrega capacidades empresariales como event sourcing, CQRS, y la posibilidad de escalar a microservicios cuando sea necesario.*
