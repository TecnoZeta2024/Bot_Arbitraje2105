# Gestión de Estado - Scalper's Brain - Edición Personal

## Visión General de la Gestión de Estado

Scalper's Brain implementa un sistema de gestión de estado híbrido que combina Event Sourcing para datos críticos, CQRS para optimización de lecturas, y state machines para flujos complejos. El sistema garantiza consistencia eventual mientras mantiene performance de tiempo real para trading de alta frecuencia.

## Arquitectura de Estado Multi-Capa

```
┌─────────────────────────────────────────────────────────────────┐
│                    UI STATE (PyQt5)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Local State  │  │ Redux-like   │  │   Reactive   │         │
│  │  (Widgets)   │  │    Store     │  │  Bindings    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 APPLICATION STATE                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Command    │  │    Query     │  │    Event     │         │
│  │   Handlers   │  │   Handlers   │  │   Handlers   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DOMAIN STATE                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Aggregates  │  │    State     │  │   Event      │         │
│  │              │  │   Machines   │  │   Store      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              INFRASTRUCTURE STATE                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Write Models │  │ Read Models  │  │  Snapshots   │         │
│  │   (Events)   │  │(Projections) │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Patrones de Gestión de Estado

### 1. Event Sourcing para Datos Críticos

```python
@dataclass
class Event:
    """Base class for all domain events"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    aggregate_id: str
    event_type: str
    event_version: int = 1
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

class TradingSessionEventStore:
    """Event store for trading session aggregate"""
    
    async def save_events(self, 
                         aggregate_id: str, 
                         events: List[Event], 
                         expected_version: int) -> None:
        """Save events with optimistic concurrency control"""
        async with self.db.transaction() as tx:
            # Check current version
            current_version = await tx.fetchval(
                "SELECT MAX(version) FROM events WHERE aggregate_id = $1",
                aggregate_id
            )
            
            if current_version != expected_version:
                raise ConcurrencyError(
                    f"Expected version {expected_version}, got {current_version}"
                )
            
            # Save events
            for event in events:
                await tx.execute("""
                    INSERT INTO events 
                    (event_id, aggregate_id, event_type, event_data, 
                     version, occurred_at, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, event.event_id, aggregate_id, event.event_type,
                    json.dumps(asdict(event)), current_version + 1,
                    event.occurred_at, json.dumps(event.metadata))
                
                current_version += 1
                
            # Publish to event bus
            for event in events:
                await self.event_bus.publish(event)
```

### 2. State Machines para Flujos Complejos

```python
class OrderStateMachine:
    """State machine for order lifecycle"""
    
    states = {
        'CREATED': ['PENDING_SUBMIT'],
        'PENDING_SUBMIT': ['SUBMITTED', 'REJECTED'],
        'SUBMITTED': ['PARTIALLY_FILLED', 'FILLED', 'CANCELLED'],
        'PARTIALLY_FILLED': ['FILLED', 'CANCELLED'],
        'FILLED': ['SETTLED'],
        'CANCELLED': [],
        'REJECTED': [],
        'SETTLED': []
    }
    
    def __init__(self, order_id: str):
        self.order_id = order_id
        self.current_state = 'CREATED'
        self.state_history = [('CREATED', datetime.utcnow())]
        
    def can_transition_to(self, new_state: str) -> bool:
        """Check if transition is valid"""
        return new_state in self.states.get(self.current_state, [])
    
    def transition_to(self, new_state: str, metadata: Dict = None) -> None:
        """Execute state transition"""
        if not self.can_transition_to(new_state):
            raise InvalidStateTransition(
                f"Cannot transition from {self.current_state} to {new_state}"
            )
        
        old_state = self.current_state
        self.current_state = new_state
        self.state_history.append((new_state, datetime.utcnow(), metadata))
        
        # Emit state change event
        event = OrderStateChanged(
            order_id=self.order_id,
            from_state=old_state,
            to_state=new_state,
            metadata=metadata
        )
        
        return event
```

### 3. CQRS con Proyecciones Optimizadas

```python
class PortfolioProjection:
    """Read model optimized for portfolio queries"""
    
    def __init__(self, redis_client: Redis, db_client: AsyncPGPool):
        self.redis = redis_client
        self.db = db_client
        
    async def handle_position_opened(self, event: PositionOpened) -> None:
        """Update projection when position is opened"""
        # Update in-memory cache
        portfolio_key = f"portfolio:{event.user_id}"
        position_data = {
            'symbol': event.symbol,
            'quantity': str(event.quantity),
            'entry_price': str(event.entry_price),
            'opened_at': event.occurred_at.isoformat()
        }
        
        await self.redis.hset(
            portfolio_key,
            event.position_id,
            json.dumps(position_data)
        )
        
        # Update materialized view
        await self.db.execute("""
            INSERT INTO portfolio_positions 
            (user_id, position_id, symbol, quantity, entry_price, opened_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (position_id) DO UPDATE
            SET quantity = $4, updated_at = NOW()
        """, event.user_id, event.position_id, event.symbol,
            event.quantity, event.entry_price, event.occurred_at)
        
    async def get_portfolio_summary(self, user_id: str) -> PortfolioSummary:
        """Get optimized portfolio summary"""
        # Try cache first
        cached = await self.redis.get(f"portfolio_summary:{user_id}")
        if cached:
            return PortfolioSummary.from_json(cached)
        
        # Query materialized view
        result = await self.db.fetchrow("""
            SELECT 
                COUNT(*) as position_count,
                SUM(current_value) as total_value,
                SUM(unrealized_pnl) as total_unrealized_pnl,
                SUM(realized_pnl) as total_realized_pnl,
                MAX(updated_at) as last_update
            FROM portfolio_summary
            WHERE user_id = $1
        """, user_id)
        
        summary = PortfolioSummary(
            position_count=result['position_count'],
            total_value=result['total_value'],
            total_unrealized_pnl=result['total_unrealized_pnl'],
            total_realized_pnl=result['total_realized_pnl'],
            last_update=result['last_update']
        )
        
        # Cache for 60 seconds
        await self.redis.setex(
            f"portfolio_summary:{user_id}",
            60,
            summary.to_json()
        )
        
        return summary
```

### 4. UI State Management con Redux-like Store

```python
class TradingStore:
    """Centralized state store for PyQt5 UI"""
    
    def __init__(self):
        self._state = {
            'market_data': {},
            'portfolio': {},
            'active_orders': [],
            'signals': [],
            'ui_settings': {},
            'connection_status': {}
        }
        self._subscribers = []
        self._middleware = []
        self._reducer = self._create_reducer()
        
    def _create_reducer(self):
        """Create root reducer"""
        return combine_reducers({
            'market_data': market_data_reducer,
            'portfolio': portfolio_reducer,
            'active_orders': orders_reducer,
            'signals': signals_reducer,
            'ui_settings': settings_reducer,
            'connection_status': connection_reducer
        })
    
    def dispatch(self, action: Action) -> None:
        """Dispatch action through middleware chain"""
        # Apply middleware
        for middleware in self._middleware:
            action = middleware(self._state, action)
            if action is None:
                return
        
        # Update state
        old_state = self._state
        self._state = self._reducer(self._state, action)
        
        # Notify subscribers if state changed
        if self._state != old_state:
            for subscriber in self._subscribers:
                subscriber(self._state, action)
    
    def subscribe(self, callback: Callable) -> Callable:
        """Subscribe to state changes"""
        self._subscribers.append(callback)
        
        # Return unsubscribe function
        def unsubscribe():
            self._subscribers.remove(callback)
        
        return unsubscribe
    
    def get_state(self) -> Dict:
        """Get current state"""
        return deepcopy(self._state)
    
    def select(self, selector: Callable) -> Any:
        """Select derived state"""
        return selector(self._state)
```

### 5. Reactive Bindings para UI

```python
class ReactiveProperty(QObject):
    """Reactive property with Qt signal emission"""
    
    valueChanged = pyqtSignal(object)
    
    def __init__(self, initial_value=None):
        super().__init__()
        self._value = initial_value
        self._computed_properties = []
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, new_value):
        if self._value != new_value:
            old_value = self._value
            self._value = new_value
            self.valueChanged.emit(new_value)
            
            # Update computed properties
            for computed in self._computed_properties:
                computed.invalidate()
    
    def bind_to_widget(self, widget, property_name):
        """Bind to Qt widget property"""
        # Set initial value
        setattr(widget, property_name, self._value)
        
        # Connect to changes
        self.valueChanged.connect(
            lambda v: setattr(widget, property_name, v)
        )
    
    def computed(self, func):
        """Create computed property"""
        computed_prop = ComputedProperty(func, [self])
        self._computed_properties.append(computed_prop)
        return computed_prop
```

## Sincronización de Estado Multi-Fuente

### 1. Reconciliación de Estado

```python
class StateReconciler:
    """Reconcile state from multiple sources"""
    
    async def reconcile_orderbook(self, symbol: str) -> OrderBook:
        """Reconcile orderbook from multiple exchanges"""
        orderbooks = await asyncio.gather(
            self.binance_client.get_orderbook(symbol),
            self.coinbase_client.get_orderbook(symbol),
            self.polygon_client.get_orderbook(symbol),
            return_exceptions=True
        )
        
        # Filter out errors
        valid_orderbooks = [
            ob for ob in orderbooks 
            if not isinstance(ob, Exception)
        ]
        
        if not valid_orderbooks:
            raise NoDataAvailable(f"No orderbook data for {symbol}")
        
        # Merge orderbooks
        merged = self._merge_orderbooks(valid_orderbooks)
        
        # Validate consistency
        if not self._validate_orderbook_consistency(merged):
            # Log inconsistency and use best effort
            logger.warning(f"Orderbook inconsistency detected for {symbol}")
        
        return merged
```

### 2. Optimistic Updates

```python
class OptimisticUpdateManager:
    """Manage optimistic updates with rollback capability"""
    
    def __init__(self, store: TradingStore):
        self.store = store
        self.pending_updates = {}
        
    async def execute_with_optimistic_update(self,
                                            action: Action,
                                            remote_call: Callable) -> Any:
        """Execute with optimistic update and rollback on failure"""
        update_id = str(uuid.uuid4())
        
        # Save current state
        snapshot = self.store.get_state()
        
        # Apply optimistic update
        self.store.dispatch(action)
        self.pending_updates[update_id] = {
            'snapshot': snapshot,
            'action': action
        }
        
        try:
            # Execute remote call
            result = await remote_call()
            
            # Confirm update
            self.store.dispatch(Action(
                type='CONFIRM_OPTIMISTIC_UPDATE',
                payload={'update_id': update_id, 'result': result}
            ))
            
            del self.pending_updates[update_id]
            return result
            
        except Exception as e:
            # Rollback
            self.store.dispatch(Action(
                type='ROLLBACK_OPTIMISTIC_UPDATE',
                payload={'update_id': update_id, 'error': str(e)}
            ))
            
            # Restore snapshot
            self.store._state = snapshot
            del self.pending_updates[update_id]
            
            raise
```

## Persistencia y Recuperación de Estado

### 1. Snapshot Strategy

```python
class SnapshotManager:
    """Manage aggregate snapshots for performance"""
    
    async def should_snapshot(self, aggregate: AggregateRoot) -> bool:
        """Determine if snapshot is needed"""
        # Snapshot every 100 events or 1 hour
        events_since_snapshot = aggregate.version - aggregate.snapshot_version
        time_since_snapshot = datetime.utcnow() - aggregate.snapshot_timestamp
        
        return (events_since_snapshot >= 100 or 
                time_since_snapshot >= timedelta(hours=1))
    
    async def create_snapshot(self, aggregate: AggregateRoot) -> None:
        """Create and store snapshot"""
        snapshot_data = {
            'aggregate_id': aggregate.id,
            'aggregate_type': type(aggregate).__name__,
            'version': aggregate.version,
            'state': aggregate.to_dict(),
            'created_at': datetime.utcnow()
        }
        
        # Compress state
        compressed = zlib.compress(
            json.dumps(snapshot_data).encode('utf-8')
        )
        
        await self.db.execute("""
            INSERT INTO snapshots 
            (aggregate_id, version, data, created_at)
            VALUES ($1, $2, $3, $4)
        """, aggregate.id, aggregate.version, compressed, datetime.utcnow())
```

### 2. State Recovery

```python
class StateRecoveryService:
    """Service for recovering system state after crash"""
    
    async def recover_system_state(self) -> SystemState:
        """Recover complete system state"""
        logger.info("Starting state recovery...")
        
        # 1. Load latest system snapshot
        system_snapshot = await self.snapshot_store.get_latest_system_snapshot()
        
        # 2. Replay events since snapshot
        events = await self.event_store.get_events_since(
            system_snapshot.timestamp if system_snapshot else datetime.min
        )
        
        # 3. Rebuild state
        state = SystemState()
        if system_snapshot:
            state = SystemState.from_snapshot(system_snapshot)
        
        # 4. Apply events
        for event in events:
            await self.event_processor.process(event, state)
        
        # 5. Validate state consistency
        validation_result = await self.state_validator.validate(state)
        if not validation_result.is_valid:
            logger.error(f"State validation failed: {validation_result.errors}")
            # Attempt repair
            state = await self.state_repairer.repair(state, validation_result)
        
        logger.info("State recovery completed")
        return state
```

## Monitoreo y Métricas de Estado

### 1. State Health Metrics

```python
class StateHealthMonitor:
    """Monitor health of state management system"""
    
    def __init__(self):
        self.metrics = {
            'event_processing_lag': Gauge('event_processing_lag_seconds'),
            'snapshot_age': Gauge('snapshot_age_seconds'),
            'state_size': Gauge('state_size_bytes'),
            'reconciliation_conflicts': Counter('reconciliation_conflicts_total'),
            'optimistic_rollbacks': Counter('optimistic_rollbacks_total')
        }
    
    async def check_health(self) -> HealthStatus:
        """Comprehensive health check"""
        checks = {
            'event_store': await self._check_event_store(),
            'projections': await self._check_projections(),
            'cache_consistency': await self._check_cache_consistency(),
            'state_machines': await self._check_state_machines()
        }
        
        overall_health = all(check.is_healthy for check in checks.values())
        
        return HealthStatus(
            is_healthy=overall_health,
            checks=checks,
            timestamp=datetime.utcnow()
        )
```

---

*Este sistema de gestión de estado representa una evolución significativa, introduciendo patrones avanzados como Event Sourcing y CQRS mientras mantiene la simplicidad para casos de uso básicos. La arquitectura permite comenzar simple y escalar según las necesidades.*
