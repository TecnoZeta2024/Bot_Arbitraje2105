# Gestión de Estado - Scalper's Brain - Edición Personal

## Visión General de la Gestión de Estado

Scalper's Brain implementa un sistema de gestión de estado distribuido y reactivo, evolucionando significativamente del Bot_Arbitraje2105. El nuevo sistema maneja estado local (UI), estado compartido (entre componentes), estado distribuido (MCPs) y estado persistente (base de datos), todo coordinado mediante patrones reactivos y event-driven.

## Arquitectura de Estado Multi-Capa

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CAPA DE PRESENTACIÓN                            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  UI State      │  │  View Models   │  │  UI Cache      │            │
│  │  (PyQt5)       │  │  (Reactive)    │  │  (Temporal)    │            │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘            │
│           └───────────────────┴───────────────────┘                     │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       ESTADO DE APLICACIÓN                               │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  App State     │  │  Session State │  │  Strategy State│            │
│  │  Store         │  │  Manager       │  │  Machines      │            │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘            │
│           └───────────────────┴───────────────────┘                     │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ESTADO DISTRIBUIDO                               │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  MCP State     │  │  Exchange State│  │  Market State  │            │
│  │  Registry      │  │  Aggregator    │  │  Snapshot      │            │
│  └────────┬───────┘  └────────┬───────┘  └────────┬───────┘            │
│           └───────────────────┴───────────────────┘                     │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       ESTADO PERSISTENTE                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  Event Store   │  │  State Store   │  │  Time Series   │            │
│  │  (Immutable)   │  │  (Mutable)     │  │  Database      │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
```

## Patrones de Gestión de Estado

### 1. Redux-like State Management para UI

```python
from dataclasses import dataclass
from typing import Any, Dict, List, Callable
from enum import Enum

class ActionType(Enum):
    # Market Actions
    UPDATE_TICKER = "UPDATE_TICKER"
    UPDATE_ORDERBOOK = "UPDATE_ORDERBOOK"
    
    # Trading Actions
    PLACE_ORDER = "PLACE_ORDER"
    ORDER_FILLED = "ORDER_FILLED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    
    # Strategy Actions
    STRATEGY_ENABLED = "STRATEGY_ENABLED"
    STRATEGY_DISABLED = "STRATEGY_DISABLED"
    STRATEGY_SIGNAL = "STRATEGY_SIGNAL"

@dataclass
class Action:
    type: ActionType
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)

class StateStore:
    def __init__(self):
        self._state = {}
        self._subscribers: List[Callable] = []
        self._middleware: List[Callable] = []
        self._history: List[Action] = []
        
    def dispatch(self, action: Action):
        # Middleware pipeline
        for middleware in self._middleware:
            action = middleware(action, self._state)
            
        # Update state
        old_state = copy.deepcopy(self._state)
        self._state = self._reducer(self._state, action)
        
        # History tracking
        self._history.append(action)
        
        # Notify subscribers
        for subscriber in self._subscribers:
            subscriber(self._state, old_state, action)
    
    def subscribe(self, callback: Callable):
        self._subscribers.append(callback)
        return lambda: self._subscribers.remove(callback)
    
    def get_state(self) -> Dict[str, Any]:
        return copy.deepcopy(self._state)
```

### 2. View Models Reactivos (MVVM Pattern)

```python
from PyQt5.QtCore import QObject, pyqtSignal
import rx
from rx import operators as ops

class MarketDataViewModel(QObject):
    # Signals para UI binding
    ticker_updated = pyqtSignal(dict)
    orderbook_updated = pyqtSignal(dict)
    trade_executed = pyqtSignal(dict)
    
    def __init__(self, market_service: MarketDataService):
        super().__init__()
        self.market_service = market_service
        self._subscriptions = []
        
        # Reactive streams
        self.ticker_stream = rx.subject.BehaviorSubject({})
        self.orderbook_stream = rx.subject.BehaviorSubject({})
        
        self._setup_streams()
    
    def _setup_streams(self):
        # Ticker updates con throttling
        ticker_sub = self.market_service.ticker_updates.pipe(
            ops.throttle_first(0.1),  # Max 10 updates per second
            ops.distinct_until_changed()
        ).subscribe(
            on_next=lambda data: self.ticker_updated.emit(data),
            on_error=lambda e: self.handle_error(e)
        )
        self._subscriptions.append(ticker_sub)
        
        # Orderbook con debouncing
        orderbook_sub = self.market_service.orderbook_updates.pipe(
            ops.debounce(0.05),  # Wait 50ms after last update
            ops.map(lambda ob: self._aggregate_orderbook(ob))
        ).subscribe(
            on_next=lambda data: self.orderbook_updated.emit(data),
            on_error=lambda e: self.handle_error(e)
        )
        self._subscriptions.append(orderbook_sub)
```

### 3. State Machines para Estrategias

```python
from enum import Enum
from transitions import Machine

class StrategyState(Enum):
    IDLE = "idle"
    SCANNING = "scanning"
    SIGNAL_DETECTED = "signal_detected"
    EXECUTING = "executing"
    COOLDOWN = "cooldown"
    ERROR = "error"

class ScalpingStrategyStateMachine:
    def __init__(self):
        self.state = StrategyState.IDLE
        
        # State machine configuration
        self.machine = Machine(
            model=self,
            states=StrategyState,
            initial=StrategyState.IDLE,
            transitions=[
                # From IDLE
                {'trigger': 'start', 'source': StrategyState.IDLE, 'dest': StrategyState.SCANNING},
                
                # From SCANNING
                {'trigger': 'signal_found', 'source': StrategyState.SCANNING, 'dest': StrategyState.SIGNAL_DETECTED},
                {'trigger': 'stop', 'source': StrategyState.SCANNING, 'dest': StrategyState.IDLE},
                
                # From SIGNAL_DETECTED
                {'trigger': 'execute', 'source': StrategyState.SIGNAL_DETECTED, 'dest': StrategyState.EXECUTING},
                {'trigger': 'reject', 'source': StrategyState.SIGNAL_DETECTED, 'dest': StrategyState.SCANNING},
                
                # From EXECUTING
                {'trigger': 'complete', 'source': StrategyState.EXECUTING, 'dest': StrategyState.COOLDOWN},
                {'trigger': 'fail', 'source': StrategyState.EXECUTING, 'dest': StrategyState.ERROR},
                
                # From COOLDOWN
                {'trigger': 'resume', 'source': StrategyState.COOLDOWN, 'dest': StrategyState.SCANNING},
                
                # From ERROR
                {'trigger': 'recover', 'source': StrategyState.ERROR, 'dest': StrategyState.IDLE},
            ],
            before_state_change=self._before_state_change,
            after_state_change=self._after_state_change
        )
        
    def _before_state_change(self):
        logger.info(f"Strategy transitioning from {self.state}")
        
    def _after_state_change(self):
        logger.info(f"Strategy transitioned to {self.state}")
        # Emit state change event
        EventBus.emit(StrategyStateChanged(
            strategy_id=self.id,
            old_state=self.state,
            new_state=self.state
        ))
```

### 4. Event Store con Event Sourcing

```python
@dataclass
class DomainEvent:
    aggregate_id: str
    event_type: str
    event_data: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

class EventStore:
    def __init__(self, db_client: DatabaseClient):
        self.db_client = db_client
        self._projections: Dict[str, Projection] = {}
        
    async def append_event(self, event: DomainEvent):
        """Append event to store and update projections"""
        # Persist event
        await self.db_client.execute(
            """
            INSERT INTO events (event_id, aggregate_id, event_type, event_data, timestamp, version)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            event.event_id, event.aggregate_id, event.event_type,
            json.dumps(event.event_data), event.timestamp, event.version
        )
        
        # Update projections
        for projection in self._projections.values():
            await projection.handle(event)
            
        # Publish to event bus
        await EventBus.publish(event)
    
    async def get_events(self, aggregate_id: str, from_version: int = 0) -> List[DomainEvent]:
        """Get events for aggregate from specific version"""
        rows = await self.db_client.fetch(
            """
            SELECT * FROM events 
            WHERE aggregate_id = $1 AND version > $2
            ORDER BY version ASC
            """,
            aggregate_id, from_version
        )
        
        return [self._row_to_event(row) for row in rows]
    
    async def replay_events(self, aggregate_id: str) -> Any:
        """Replay events to rebuild aggregate state"""
        events = await self.get_events(aggregate_id)
        aggregate = self._create_aggregate(aggregate_id)
        
        for event in events:
            aggregate.apply_event(event)
            
        return aggregate
```

### 5. Caché Distribuido con Coherencia

```python
class DistributedCache:
    def __init__(self, redis_client: Redis, local_cache_size: int = 1000):
        self.redis = redis_client
        self.local_cache = LRUCache(maxsize=local_cache_size)
        self.subscriptions = {}
        
    async def get(self, key: str) -> Optional[Any]:
        # Check L1 cache
        value = self.local_cache.get(key)
        if value is not None:
            return value
            
        # Check L2 cache (Redis)
        value = await self.redis.get(key)
        if value is not None:
            # Update L1
            self.local_cache[key] = value
            return json.loads(value)
            
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        # Update both caches
        self.local_cache[key] = value
        await self.redis.setex(key, ttl, json.dumps(value))
        
        # Publish update event
        await self.redis.publish(f"cache:update:{key}", json.dumps({
            'key': key,
            'action': 'set',
            'timestamp': time.time()
        }))
    
    async def invalidate(self, key: str):
        # Remove from both caches
        self.local_cache.pop(key, None)
        await self.redis.delete(key)
        
        # Publish invalidation event
        await self.redis.publish(f"cache:update:{key}", json.dumps({
            'key': key,
            'action': 'invalidate',
            'timestamp': time.time()
        }))
```

### 6. Estado de MCPs con Registry Pattern

```python
class MCPStateRegistry:
    def __init__(self):
        self._mcps: Dict[str, MCPState] = {}
        self._health_checks: Dict[str, datetime] = {}
        self._metrics: Dict[str, MCPMetrics] = {}
        
    async def register_mcp(self, mcp_id: str, mcp_config: MCPConfig):
        """Register new MCP and initialize its state"""
        state = MCPState(
            id=mcp_id,
            config=mcp_config,
            status=MCPStatus.INITIALIZING,
            capabilities=await self._discover_capabilities(mcp_config)
        )
        
        self._mcps[mcp_id] = state
        self._health_checks[mcp_id] = datetime.utcnow()
        self._metrics[mcp_id] = MCPMetrics()
        
        # Start health monitoring
        asyncio.create_task(self._monitor_health(mcp_id))
        
    async def get_mcp_state(self, mcp_id: str) -> Optional[MCPState]:
        return self._mcps.get(mcp_id)
    
    async def update_mcp_status(self, mcp_id: str, status: MCPStatus):
        if mcp_id in self._mcps:
            old_status = self._mcps[mcp_id].status
            self._mcps[mcp_id].status = status
            
            # Emit status change event
            await EventBus.emit(MCPStatusChanged(
                mcp_id=mcp_id,
                old_status=old_status,
                new_status=status
            ))
```

### 7. Sincronización de Estado Multi-Exchange

```python
class ExchangeStateAggregator:
    def __init__(self):
        self._exchange_states: Dict[str, ExchangeState] = {}
        self._aggregated_state = AggregatedMarketState()
        self._lock = asyncio.Lock()
        
    async def update_exchange_state(self, exchange_id: str, state_update: StateUpdate):
        """Update individual exchange state and recalculate aggregated state"""
        async with self._lock:
            # Update individual exchange
            if exchange_id not in self._exchange_states:
                self._exchange_states[exchange_id] = ExchangeState(exchange_id)
                
            self._exchange_states[exchange_id].apply_update(state_update)
            
            # Recalculate aggregated state
            await self._recalculate_aggregated_state()
            
    async def _recalculate_aggregated_state(self):
        """Recalculate best prices across all exchanges"""
        all_bids = []
        all_asks = []
        
        for exchange_state in self._exchange_states.values():
            if exchange_state.is_healthy:
                all_bids.extend(exchange_state.orderbook.bids)
                all_asks.extend(exchange_state.orderbook.asks)
        
        # Sort and aggregate
        self._aggregated_state.best_bid = max(all_bids, key=lambda x: x.price) if all_bids else None
        self._aggregated_state.best_ask = min(all_asks, key=lambda x: x.price) if all_asks else None
        
        # Calculate spread and arbitrage opportunities
        if self._aggregated_state.best_bid and self._aggregated_state.best_ask:
            self._aggregated_state.spread = self._aggregated_state.best_ask.price - self._aggregated_state.best_bid.price
            self._check_arbitrage_opportunities()
```

## Flujo de Estado Reactivo

```
User Action → UI State → Command → Domain Event → State Update → Projection → UI Update
     ↑                                                                              ↓
     └──────────────────────── Reactive Feedback Loop ─────────────────────────────┘
```

## Estrategias de Persistencia

### 1. Write-Through para Estado Crítico
```python
async def update_position(self, position: Position):
    # Update in-memory state
    self._positions[position.id] = position
    
    # Write through to database
    await self._repository.save_position(position)
    
    # Update cache
    await self._cache.set(f"position:{position.id}", position)
    
    # Emit event
    await self._event_bus.emit(PositionUpdated(position))
```

### 2. Write-Behind para Estado de Alto Volumen
```python
class WriteBackBuffer:
    def __init__(self, flush_interval: float = 1.0):
        self._buffer: Dict[str, Any] = {}
        self._flush_task = None
        
    async def write(self, key: str, value: Any):
        self._buffer[key] = value
        
        if not self._flush_task:
            self._flush_task = asyncio.create_task(self._flush_loop())
            
    async def _flush_loop(self):
        while self._buffer:
            await asyncio.sleep(self._flush_interval)
            await self._flush()
            
    async def _flush(self):
        if not self._buffer:
            return
            
        # Batch write to database
        items = list(self._buffer.items())
        self._buffer.clear()
        
        await self._repository.batch_save(items)
```

## Manejo de Conflictos y Consistencia

### 1. Optimistic Locking
```python
class OptimisticLockingMixin:
    def __init__(self):
        self._version = 0
        
    def increment_version(self):
        self._version += 1
        
    async def save_with_version_check(self, repository):
        current_version = await repository.get_version(self.id)
        
        if current_version != self._version:
            raise ConcurrencyError(f"Version mismatch: expected {self._version}, got {current_version}")
            
        self.increment_version()
        await repository.save(self)
```

### 2. Conflict Resolution con CRDTs
```python
class CRDTCounter:
    """Conflict-free Replicated Data Type for distributed counting"""
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.counts: Dict[str, int] = {node_id: 0}
        
    def increment(self):
        self.counts[self.node_id] += 1
        
    def merge(self, other: 'CRDTCounter'):
        for node_id, count in other.counts.items():
            self.counts[node_id] = max(self.counts.get(node_id, 0), count)
            
    def value(self) -> int:
        return sum(self.counts.values())
```

## Monitoreo y Debugging de Estado

### 1. State Inspector
```python
class StateInspector:
    def __init__(self, state_store: StateStore):
        self.state_store = state_store
        self._snapshots: List[StateSnapshot] = []
        
    def take_snapshot(self, label: str = ""):
        snapshot = StateSnapshot(
            timestamp=datetime.utcnow(),
            label=label,
            state=copy.deepcopy(self.state_store.get_state()),
            stack_trace=traceback.format_stack()
        )
        self._snapshots.append(snapshot)
        
    def compare_snapshots(self, idx1: int, idx2: int) -> Dict[str, Any]:
        """Compare two state snapshots and return differences"""
        snapshot1 = self._snapshots[idx1]
        snapshot2 = self._snapshots[idx2]
        
        return DeepDiff(snapshot1.state, snapshot2.state)
```

### 2. Time-Travel Debugging
```python
class TimeTravelDebugger:
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        
    async def replay_to_timestamp(self, aggregate_id: str, target_time: datetime):
        """Replay events up to specific timestamp"""
        events = await self.event_store.get_events(aggregate_id)
        aggregate = self._create_aggregate(aggregate_id)
        
        for event in events:
            if event.timestamp <= target_time:
                aggregate.apply_event(event)
            else:
                break
                
        return aggregate
```

## Mejoras Respecto al Bot_Arbitraje2105

1. **Estado Reactivo**: Implementación completa de programación reactiva
2. **Multi-Fuente**: Gestión coherente de estado desde múltiples fuentes
3. **Event Sourcing**: Historial completo y reproducible
4. **State Machines**: Gestión formal de estados de estrategias
5. **Debugging Avanzado**: Time-travel y state inspection
6. **Caché Distribuido**: Coherencia entre múltiples nodos
7. **Conflict Resolution**: Manejo robusto de concurrencia

---

*Este sistema de gestión de estado proporciona la base sólida necesaria para una plataforma de trading compleja, manteniendo la coherencia y trazabilidad mientras permite la escala y el rendimiento requeridos.*
