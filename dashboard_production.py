#Bot Arbitraje - Dashboard de Trading con Streamlit
#UI moderna y simple sin complicaciones de WebSocket
#Dashboard Production-Ready con manejo robusto de importaciones y errores

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import asyncio
import json
import websockets
import threading
import queue
import time
from collections import deque
import requests
import sys
import traceback

# Configuración de la página ANTES de cualquier otra cosa
st.set_page_config(
    page_title="Bot Arbitraje - Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === SISTEMA DE IMPORTACIONES ROBUSTO ===
# Importar componentes del sistema con manejo de errores
IMPORTS_SUCCESS = True
import_errors = []

try:
    from src.infrastructure.monitoring.system_monitor import SystemMonitor, HealthStatus, AlertSeverity
    st.success("✅ SystemMonitor importado correctamente")
except ImportError as e:
    import_errors.append(f"SystemMonitor: {e}")
    IMPORTS_SUCCESS = False
    # Mock SystemMonitor
    class MockSystemMonitor:
        def get_system_status(self):
            return {
                "overall_health": "unknown",
                "active_alerts_count": 0,
                "monitoring_status": "error",
                "timestamp": datetime.now().isoformat()
            }
    SystemMonitor = MockSystemMonitor

try:
    from src.domain.risk_management.advanced_risk_manager import AdvancedRiskManager, RiskParameters
    st.success("✅ AdvancedRiskManager importado correctamente")
except ImportError as e:
    import_errors.append(f"AdvancedRiskManager: {e}")
    IMPORTS_SUCCESS = False
    # Mock AdvancedRiskManager
    class MockRiskParameters:
        def __init__(self):
            self.max_daily_loss = 0.02
            self.max_position_size = 0.05
            self.max_total_exposure = 0.8
            self.stop_loss_multiplier = 1.5
            self.profit_target_multiplier = 2.0
            self.max_concurrent_positions = 10

    class MockRiskManager:
        def __init__(self):
            self.risk_params = MockRiskParameters()
        
        def get_risk_metrics(self):
            return {
                'current_capital': 10000.0,
                'available_capital': 10000.0,
                'daily_pnl': 0.0,
                'total_pnl': 0.0,
                'open_positions': 0,
                'total_exposure': 0.0,
                'exposure_percentage': 0.0,
                'unrealized_pnl': 0.0,
                'daily_trades': 0,
                'risk_events_today': 0,
                'max_drawdown': 0.0
            }
    AdvancedRiskManager = MockRiskManager
    RiskParameters = MockRiskParameters

try:
    from src.infrastructure.external_apis.supabase_client import SupabaseClient
    st.success("✅ SupabaseClient importado correctamente")
except ImportError as e:
    import_errors.append(f"SupabaseClient: {e}")
    IMPORTS_SUCCESS = False
    # Mock SupabaseClient
    class MockSupabaseClient:
        def check_connection(self):
            return False
    SupabaseClient = MockSupabaseClient

try:
    from src.infrastructure.database.operation_repository_impl import OperationRepositoryImpl
    st.success("✅ OperationRepositoryImpl importado correctamente")
except ImportError as e:
    import_errors.append(f"OperationRepositoryImpl: {e}")
    IMPORTS_SUCCESS = False
    # Mock OperationRepositoryImpl
    class MockOperationRepository:
        def __init__(self, client):
            self.client = client
        
        async def get_completed_operations(self):
            return []
        
        async def calculate_sharpe_ratio(self, start_date, end_date):
            return 0.0
    OperationRepositoryImpl = MockOperationRepository

try:
    from src.utils.performance_calculator import calcular_metricas_rendimiento
    st.success("✅ Performance Calculator importado correctamente")
except ImportError as e:
    import_errors.append(f"Performance Calculator: {e}")
    IMPORTS_SUCCESS = False
    # Mock performance calculator
    def calcular_metricas_rendimiento(datos):
        return {
            "rendimiento_1h": 0.0,
            "rendimiento_24h": 0.0,
            "rendimiento_7d": 0.0,
            "volatilidad": 0.0
        }

try:
    from src.utils.config import settings, load_config, save_config
    st.success("✅ Config utils importado correctamente")
except ImportError as e:
    import_errors.append(f"Config utils: {e}")
    IMPORTS_SUCCESS = False
    # Mock config functions
    def load_config():
        return {
            'API_HOST': 'localhost',
            'API_PORT': 8001,
            'CAPITAL_INICIAL': 10000.0,
            'UMBRAL_RENTABILIDAD': 0.5,
            'BINANCE_API_KEY': 'mock_key',
            'MOBULA_API_KEY': 'mock_key',
            'TELEGRAM_BOT_TOKEN': 'mock_token',
            'BINANCE_TESTNET': True
        }
    
    def save_config(config):
        return True
    
    class MockSettings:
        pass
    settings = MockSettings()

# Mostrar estado de importaciones
if not IMPORTS_SUCCESS:
    st.error("⚠️ Algunos módulos no se pudieron importar:")
    for error in import_errors:
        st.error(f"  • {error}")
    st.warning("El dashboard funcionará en modo limitado usando objetos mock.")
    st.info("Para resolución de problemas de librerías, usar context7 según protocolo mandatorio.")
else:
    st.success("🎉 Todos los módulos importados correctamente")

# CSS personalizado para mejor apariencia
st.markdown("""
<style>
    .stApp {
        background-color: #0f0f0f;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #333;
    }
    .positive {
        color: #00ff88;
    }
    .negative {
        color: #ff3366;
    }
    div[data-testid="metric-container"] {
        background-color: rgba(28, 28, 28, 0.8);
        border: 1px solid #333;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-healthy { background-color: #00ff88; }
    .status-warning { background-color: #ffaa00; }
    .status-error { background-color: #ff3366; }
    .status-unknown { background-color: #666; }
</style>
""", unsafe_allow_html=True)

# === INICIALIZACIÓN DE SESSION STATE ===
# Initialize session state
session_defaults = {
    'market_data': {},
    'portfolio': {
        'totalValue': 10000,
        'totalPnL': 0,
        'totalPnLPercent': 0,
        'availableBalance': 10000,
        'dailyPnL': 0
    },
    'signals': deque(maxlen=50),
    'trades': deque(maxlen=100),
    'price_history': {
        'BTCUSDT': deque(maxlen=100),
        'ETHUSDT': deque(maxlen=100)
    },
    'ws_connected': False,
    'ws_connection_attempts': 0,
    'ws_last_attempt': None,
    'message_queue': queue.Queue(),
    'system_status_backend': {
        'overall_health': 'UNKNOWN',
        'active_alerts_count': 0,
        'monitoring_status': 'stopped',
        'timestamp': datetime.now().isoformat()
    },
    'risk_metrics_backend': {
        'current_capital': 10000.0,
        'available_capital': 10000.0,
        'daily_pnl': 0.0,
        'total_pnl': 0.0,
        'open_positions': 0,
        'total_exposure': 0.0,
        'exposure_percentage': 0.0,
        'unrealized_pnl': 0.0,
        'daily_trades': 0,
        'risk_events_today': 0,
        'max_drawdown': 0.0
    },
    'system_alerts': deque(maxlen=100),
    'backend_status': {
        'api_responsive': False,
        'last_check': None,
        'error_count': 0
    },
    'active_strategies': {
        'scalping': False,
        'day_trading': False,
        'simple_arbitrage': True,
        'triangular_arbitrage': False
    }
}

for key, default_value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

# === INICIALIZACIÓN DE COMPONENTES ===
# Inicializar componentes principales con manejo de errores
try:
    if 'system_monitor' not in st.session_state:
        st.session_state.system_monitor = SystemMonitor()
except Exception as e:
    st.error(f"Error inicializando SystemMonitor: {e}")
    st.session_state.system_monitor = MockSystemMonitor()

try:
    if 'risk_manager' not in st.session_state:
        st.session_state.risk_manager = AdvancedRiskManager()
except Exception as e:
    st.error(f"Error inicializando AdvancedRiskManager: {e}")
    st.session_state.risk_manager = MockRiskManager()

try:
    if 'supabase_client' not in st.session_state:
        st.session_state.supabase_client = SupabaseClient()
        # Verificar conexión
        connection_status = st.session_state.supabase_client.check_connection()
        if connection_status:
            st.success("✅ Conexión con Supabase establecida")
        else:
            st.warning("⚠️ No se pudo conectar con Supabase")
except Exception as e:
    st.error(f"Error inicializando SupabaseClient: {e}")
    st.session_state.supabase_client = MockSupabaseClient()

try:
    if 'operation_repository' not in st.session_state:
        st.session_state.operation_repository = OperationRepositoryImpl(st.session_state.supabase_client)
except Exception as e:
    st.error(f"Error inicializando OperationRepository: {e}")
    st.session_state.operation_repository = MockOperationRepository(st.session_state.supabase_client)

# === WEBSOCKET CLIENT MEJORADO ===
class EnhancedWebSocketClient:
    def __init__(self, message_queue):
        self.message_queue = message_queue
        self.running = False
        self.reconnect_delay = 1  # seconds
        self.max_reconnect_delay = 30
        self.connection_attempts = 0
        
    async def connect_with_retry(self):
        """Conectar con reintentos automáticos"""
        uri = "ws://localhost:8001/ws"
        
        while self.running:
            try:
                st.session_state.ws_connection_attempts += 1
                st.session_state.ws_last_attempt = datetime.now()
                
                async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as websocket:
                    st.session_state.ws_connected = True
                    self.connection_attempts = 0
                    self.reconnect_delay = 1
                    
                    # Subscribe to channels
                    await websocket.send(json.dumps({
                        "type": "subscribe",
                        "channels": ["market_data", "trading_signals", "portfolio_updates", "system_metrics"]
                    }))
                    
                    # Listen for messages
                    while self.running:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                            data = json.loads(message)
                            self.message_queue.put(data)
                            
                            # Respond to heartbeat
                            if data.get('type') == 'heartbeat':
                                await websocket.send(json.dumps({
                                    'type': 'heartbeat_ack',
                                    'timestamp': time.time()
                                }))
                                
                        except asyncio.TimeoutError:
                            # Timeout is normal, continue
                            continue
                        except websockets.exceptions.ConnectionClosed:
                            # Connection closed, will retry
                            break
                        except Exception as e:
                            print(f"Message processing error: {e}")
                            
            except Exception as e:
                st.session_state.ws_connected = False
                self.connection_attempts += 1
                print(f"WebSocket connection failed (attempt {self.connection_attempts}): {e}")
                
                if self.running:
                    await asyncio.sleep(self.reconnect_delay)
                    self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
                    
    def start(self):
        self.running = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect_with_retry())
        
    def stop(self):
        self.running = False

# === FUNCIONES DE PROCESAMIENTO ===
def process_websocket_messages():
    """Procesar mensajes del WebSocket con manejo de errores"""
    while not st.session_state.message_queue.empty():
        try:
            message = st.session_state.message_queue.get_nowait()
            msg_type = message.get('type')
            
            if msg_type == 'market_data':
                data = message.get('data', {})
                symbol = data.get('symbol')
                if symbol:
                    st.session_state.market_data[symbol] = data
                    
                    # Actualizar historial de precios
                    if symbol in st.session_state.price_history:
                        st.session_state.price_history[symbol].append({
                            'time': datetime.now(),
                            'price': data.get('price', 0)
                        })
                        
            elif msg_type == 'portfolio_update':
                st.session_state.portfolio.update(message.get('data', {}))
                
            elif msg_type == 'trading_signal':
                st.session_state.signals.append(message.get('data', {}))
                
            elif msg_type == 'trade_executed':
                st.session_state.trades.append(message.get('data', {}))
            
            elif msg_type == 'system_metrics':
                # Actualizar métricas del sistema
                data = message.get('data', {})
                st.session_state.system_status_backend.update(
                    data.get('system_monitor_status', {})
                )
                
                # Actualizar métricas de riesgo
                st.session_state.risk_metrics_backend.update({
                    'current_capital': data.get('portfolio_value', 0.0),
                    'available_capital': data.get('available_balance', 0.0),
                    'daily_pnl': data.get('daily_pnl', 0.0),
                    'total_pnl': data.get('total_pnl', 0.0),
                    'open_positions': data.get('open_positions', 0),
                    'total_exposure': data.get('total_exposure', 0.0),
                    'exposure_percentage': data.get('exposure_percentage', 0.0),
                    'unrealized_pnl': data.get('unrealized_pnl', 0.0),
                    'daily_trades': data.get('trades_count', 0),
                    'risk_events_today': data.get('risk_events_today', 0),
                    'max_drawdown': data.get('max_drawdown', 0.0)
                })
            
            elif msg_type in ['system_alert', 'error_alert', 'warning']:
                # Manejar alertas del sistema
                alert = {
                    'level': message.get('level', 'INFO').upper(),
                    'message': message.get('message', str(message)),
                    'component': message.get('component', 'WebSocket'),
                    'timestamp': message.get('timestamp', datetime.now().isoformat())
                }
                st.session_state.system_alerts.append(alert)
                
        except queue.Empty:
            break
        except Exception as e:
            st.error(f"Error procesando mensaje WebSocket: {e}")

def check_backend_status():
    """Verificar estado del backend API"""
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            st.session_state.backend_status['api_responsive'] = True
            st.session_state.backend_status['error_count'] = 0
        else:
            st.session_state.backend_status['api_responsive'] = False
            st.session_state.backend_status['error_count'] += 1
    except Exception as e:
        st.session_state.backend_status['api_responsive'] = False
        st.session_state.backend_status['error_count'] += 1
    
    st.session_state.backend_status['last_check'] = datetime.now()

def send_trading_command(action: str):
    """Enviar comandos al backend con manejo de errores"""
    backend_url = "http://localhost:8001/api/trading/control"
    try:
        response = requests.post(backend_url, json={"action": action}, timeout=10)
        if response.status_code == 200:
            result = response.json()
            st.success(f"✅ Comando '{action}' enviado exitosamente. Estado: {result.get('state', 'N/A')}")
            return True
        else:
            st.error(f"❌ Error al enviar comando '{action}': {response.status_code} - {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        st.error("🔌 No se pudo conectar al servidor de backend. Verificar que esté corriendo en puerto 8001.")
        return False
    except requests.exceptions.Timeout:
        st.error("⏰ Timeout al enviar comando. El backend puede estar sobrecargado.")
        return False
    except Exception as e:
        st.error(f"💥 Error inesperado: {e}")
        return False

# === HEADER Y SIDEBAR ===
st.title("🚀 Bot Arbitraje - Trading Dashboard v3.0")
st.markdown("### Sistema de Trading Automatizado con IA - Production Ready")

# Verificar estado del backend
check_backend_status()

# Sidebar con información de estado
with st.sidebar:
    st.title("🎛️ Panel de Control")
    st.markdown("---")
    
    # Estado de conexiones
    st.subheader("🔗 Estado de Conexiones")
    
    # WebSocket Status
    ws_status_color = "🟢" if st.session_state.ws_connected else "🔴"
    ws_status_text = "Conectado" if st.session_state.ws_connected else "Desconectado"
    st.write(f"**WebSocket:** {ws_status_color} {ws_status_text}")
    
    if st.session_state.ws_last_attempt:
        st.caption(f"Último intento: {st.session_state.ws_last_attempt.strftime('%H:%M:%S')}")
    
    # Backend API Status
    api_status_color = "🟢" if st.session_state.backend_status['api_responsive'] else "🔴"
    api_status_text = "Responsivo" if st.session_state.backend_status['api_responsive'] else "No disponible"
    st.write(f"**Backend API:** {api_status_color} {api_status_text}")
    
    if st.session_state.backend_status['error_count'] > 0:
        st.caption(f"Errores: {st.session_state.backend_status['error_count']}")
    
    # Supabase Status
    if hasattr(st.session_state.supabase_client, 'check_connection'):
        supabase_ok = st.session_state.supabase_client.check_connection()
        supabase_color = "🟢" if supabase_ok else "🔴"
        supabase_text = "Conectado" if supabase_ok else "Desconectado"
    else:
        supabase_color = "🟡"
        supabase_text = "Mock (modo desarrollo)"
    st.write(f"**Supabase:** {supabase_color} {supabase_text}")
    
    st.markdown("---")
    
    # Controles rápidos
    st.subheader("⚡ Controles Rápidos")
    if st.button("🔄 Reconectar WebSocket", use_container_width=True):
        # Reiniciar WebSocket
        if 'ws_client' in st.session_state:
            st.session_state.ws_client.stop()
            del st.session_state.ws_client
        st.rerun()
    
    if st.button("🔍 Verificar Backend", use_container_width=True):
        check_backend_status()
        st.rerun()
    
    st.markdown("---")
    
    # Información del sistema
    st.subheader("📊 Info del Sistema")
    st.write(f"**Módulos:** {'✅ OK' if IMPORTS_SUCCESS else '⚠️ Parcial'}")
    st.write(f"**Mensajes WS:** {st.session_state.message_queue.qsize()}")
    st.write(f"**Señales:** {len(st.session_state.signals)}")
    st.write(f"**Trades:** {len(st.session_state.trades)}")

# Procesar mensajes antes de mostrar contenido
process_websocket_messages()

# === PESTAÑAS PRINCIPALES ===
tab_titles = ["🏠 Inicio", "📈 Estrategias", "⚠️ Riesgos", "🚨 Alertas", "📊 Métricas", "⚙️ Configuración"]
tabs = st.tabs(tab_titles)

# --- PESTAÑA: INICIO ---
with tabs[0]:
    st.header("🏠 Estado General del Sistema")
    
    # Indicadores de estado principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = st.session_state.system_status_backend.get('overall_health', 'UNKNOWN').upper()
        status_emoji = {
            'HEALTHY': '🟢', 'DEGRADED': '🟡', 'UNHEALTHY': '🔴', 'CRITICAL': '🚨'
        }.get(status, '⚫')
        st.metric("Estado General", f"{status_emoji} {status}")
    
    with col2:
        alerts_count = st.session_state.system_status_backend.get('active_alerts_count', 0)
        st.metric("Alertas Activas", alerts_count)
    
    with col3:
        monitoring_status = st.session_state.system_status_backend.get('monitoring_status', 'stopped')
        monitor_emoji = '🟢' if monitoring_status == 'running' else '🔴'
        st.metric("Monitoreo", f"{monitor_emoji} {monitoring_status.title()}")
    
    with col4:
        portfolio_value = st.session_state.portfolio.get('totalValue', 0)
        st.metric("Valor Portfolio", f"${portfolio_value:,.2f}")
    
    st.markdown("---")
    
    # Resumen de trading
    st.subheader("📊 Resumen de Trading")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Portfolio")
        portfolio = st.session_state.portfolio
        daily_pnl = portfolio.get('dailyPnL', 0)
        total_pnl = portfolio.get('totalPnL', 0)
        
        pnl_color = 'positive' if daily_pnl >= 0 else 'negative'
        st.markdown(f"**P&L Diario:** <span class='{pnl_color}'>${daily_pnl:,.2f}</span>", unsafe_allow_html=True)
        
        pnl_color = 'positive' if total_pnl >= 0 else 'negative'
        st.markdown(f"**P&L Total:** <span class='{pnl_color}'>${total_pnl:,.2f}</span>", unsafe_allow_html=True)
        
        available = portfolio.get('availableBalance', 0)
        st.markdown(f"**Balance Disponible:** ${available:,.2f}")
    
    with col2:
        st.markdown("#### 🎯 Actividad Reciente")
        if st.session_state.trades:
            recent_trades = list(st.session_state.trades)[-5:]  # Últimos 5 trades
            for trade in recent_trades:
                symbol = trade.get('symbol', 'N/A')
                side = trade.get('side', 'N/A')
                price = trade.get('price', 0)
                pnl = trade.get('pnl', 0)
                
                side_emoji = '🟢' if side == 'BUY' else '🔴'
                pnl_color = 'positive' if pnl >= 0 else 'negative'
                
                st.markdown(f"{side_emoji} {symbol} @ ${price:,.2f} | <span class='{pnl_color}'>${pnl:,.2f}</span>", 
                           unsafe_allow_html=True)
        else:
            st.info("No hay trades recientes")
    
    st.markdown("---")
    
    # Métricas de mercado
    st.subheader("💹 Datos de Mercado")
    if st.session_state.market_data:
        market_cols = st.columns(len(st.session_state.market_data))
        for idx, (symbol, data) in enumerate(st.session_state.market_data.items()):
            with market_cols[idx]:
                price = data.get('price', 0)
                change_24h = data.get('changePercent24h', 0)
                volume = data.get('volume24h', 0)
                
                change_color = 'positive' if change_24h >= 0 else 'negative'
                change_arrow = '↗️' if change_24h >= 0 else '↘️'
                
                st.markdown(f"#### {symbol}")
                st.markdown(f"**${price:,.4f}**")
                st.markdown(f"<span class='{change_color}'>{change_arrow} {change_24h:+.2f}%</span>", 
                           unsafe_allow_html=True)
                st.caption(f"Vol: ${volume:,.0f}")
    else:
        st.info("🔄 Cargando datos de mercado...")

# --- PESTAÑA: ESTRATEGIAS ---
with tabs[1]:
    st.header("📈 Gestión de Estrategias")
    
    # Controles de trading
    st.subheader("🎮 Controles de Trading")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("▶️ Iniciar Trading", type="primary", use_container_width=True):
            send_trading_command("start")
    
    with col2:
        if st.button("⏸️ Pausar Trading", use_container_width=True):
            send_trading_command("pause")
    
    with col3:
        if st.button("⏹️ Detener Trading", use_container_width=True):
            send_trading_command("stop")
    
    with col4:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Estrategias disponibles
    st.subheader("⚙️ Configuración de Estrategias")
    
    strategies_config = [
        {
            "id": "scalping",
            "name": "🏃‍♂️ Scalping",
            "description": "Operaciones ultrarrápidas aprovechando micro-movimientos",
            "risk": "Alto",
            "timeframe": "1-5 min"
        },
        {
            "id": "day_trading", 
            "name": "📅 Day Trading",
            "description": "Operaciones intradía siguiendo tendencias de corto plazo",
            "risk": "Medio",
            "timeframe": "15m-4h"
        },
        {
            "id": "simple_arbitrage",
            "name": "🔄 Arbitraje Simple", 
            "description": "Diferencias de precio entre exchanges",
            "risk": "Bajo",
            "timeframe": "Instantáneo"
        },
        {
            "id": "triangular_arbitrage",
            "name": "🔺 Arbitraje Triangular",
            "description": "Ciclos de 3 pares para aprovechar ineficiencias",
            "risk": "Medio",
            "timeframe": "1-3 min"
        }
    ]
    
    for strategy in strategies_config:
        with st.expander(f"**{strategy['name']}** - {strategy['description']}", 
                        expanded=st.session_state.active_strategies.get(strategy['id'], False)):
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Descripción:** {strategy['description']}")
                st.markdown(f"**Nivel de Riesgo:** {strategy['risk']}")
                st.markdown(f"**Timeframe:** {strategy['timeframe']}")
            
            with col2:
                is_active = st.checkbox(
                    "Activar", 
                    value=st.session_state.active_strategies.get(strategy['id'], False),
                    key=f"strategy_{strategy['id']}"
                )
                st.session_state.active_strategies[strategy['id']] = is_active
                
                status_text = "🟢 Activa" if is_active else "🔴 Inactiva"
                st.markdown(f"**Estado:** {status_text}")
    
    st.markdown("---")
    
    # Señales recientes
    st.subheader("🎯 Señales de Trading Recientes")
    if st.session_state.signals:
        signals_df = pd.DataFrame(list(st.session_state.signals))
        
        # Mostrar las últimas 10 señales
        for _, signal in signals_df.tail(10).iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                
                with col1:
                    action = signal.get('action', 'N/A')
                    symbol = signal.get('symbol', 'N/A')
                    action_emoji = '🟢' if action == 'BUY' else '🔴'
                    st.markdown(f"{action_emoji} **{action}** {symbol}")
                
                with col2:
                    price = signal.get('price', 0)
                    st.markdown(f"${price:,.4f}")
                
                with col3:
                    confidence = signal.get('confidence', 0)
                    conf_color = 'positive' if confidence > 80 else 'negative' if confidence < 50 else ''
                    st.markdown(f"<span class='{conf_color}'>{confidence}%</span>", unsafe_allow_html=True)
                
                with col4:
                    strategy = signal.get('strategy', 'N/A')
                    st.caption(strategy)
                
                with col5:
                    timestamp = signal.get('timestamp', datetime.now().isoformat())
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        st.caption(dt.strftime('%H:%M:%S'))
                    except:
                        st.caption('N/A')
    else:
        st.info("📭 No hay señales de trading disponibles")

# --- PESTAÑA: RIESGOS ---
with tabs[2]:
    st.header("⚠️ Gestión de Riesgos")
    
    # Métricas actuales de riesgo
    risk_metrics = st.session_state.risk_metrics_backend
    
    st.subheader("📊 Métricas Actuales de Riesgo")
    
    # Row 1: Capital metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        current_capital = risk_metrics.get('current_capital', 0)
        st.metric("Capital Actual", f"${current_capital:,.2f}")
    
    with col2:
        available_capital = risk_metrics.get('available_capital', 0)
        st.metric("Capital Disponible", f"${available_capital:,.2f}")
    
    with col3:
        daily_pnl = risk_metrics.get('daily_pnl', 0)
        pnl_delta = f"{daily_pnl:+.2f}" if daily_pnl != 0 else None
        st.metric("P&L Diario", f"${daily_pnl:,.2f}", delta=pnl_delta)
    
    with col4:
        total_pnl = risk_metrics.get('total_pnl', 0)
        st.metric("P&L Total", f"${total_pnl:,.2f}")
    
    # Row 2: Position metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        open_positions = risk_metrics.get('open_positions', 0)
        st.metric("Posiciones Abiertas", open_positions)
    
    with col2:
        exposure_pct = risk_metrics.get('exposure_percentage', 0) * 100
        exposure_color = "🟢" if exposure_pct < 50 else "🟡" if exposure_pct < 80 else "🔴"
        st.metric("Exposición Total", f"{exposure_color} {exposure_pct:.1f}%")
    
    with col3:
        unrealized_pnl = risk_metrics.get('unrealized_pnl', 0)
        st.metric("P&L No Realizado", f"${unrealized_pnl:,.2f}")
    
    with col4:
        max_drawdown = risk_metrics.get('max_drawdown', 0) * 100
        dd_color = "🟢" if max_drawdown < 5 else "🟡" if max_drawdown < 10 else "🔴"
        st.metric("Max Drawdown", f"{dd_color} {max_drawdown:.1f}%")
    
    st.markdown("---")
    
    # Configuración de parámetros de riesgo
    st.subheader("⚙️ Configuración de Parámetros")
    
    risk_params = st.session_state.risk_manager.risk_params
    
    with st.expander("📐 Límites de Capital y Posición", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_daily_loss = st.slider(
                "Pérdida Diaria Máxima (%)",
                0.0, 10.0, 
                risk_params.max_daily_loss * 100,
                0.1,
                help="Porcentaje máximo de pérdida diaria permitida"
            )
            risk_params.max_daily_loss = max_daily_loss / 100
        
        with col2:
            max_position_size = st.slider(
                "Tamaño Máximo por Posición (%)",
                0.0, 20.0,
                risk_params.max_position_size * 100,
                0.1,
                help="Porcentaje máximo del capital por posición"
            )
            risk_params.max_position_size = max_position_size / 100
        
        with col3:
            max_exposure = st.slider(
                "Exposición Total Máxima (%)",
                0.0, 100.0,
                risk_params.max_total_exposure * 100,
                1.0,
                help="Porcentaje máximo del capital en posiciones abiertas"
            )
            risk_params.max_total_exposure = max_exposure / 100
    
    with st.expander("🎯 Configuración de Stop Loss y Take Profit"):
        col1, col2 = st.columns(2)
        
        with col1:
            sl_multiplier = st.slider(
                "Multiplicador Stop Loss (ATR)",
                0.5, 5.0,
                risk_params.stop_loss_multiplier,
                0.1,
                help="Multiplicador del ATR para calcular stop loss"
            )
            risk_params.stop_loss_multiplier = sl_multiplier
        
        with col2:
            tp_multiplier = st.slider(
                "Ratio Riesgo/Recompensa",
                1.0, 5.0,
                risk_params.profit_target_multiplier,
                0.1,
                help="Ratio para calcular take profit basado en stop loss"
            )
            risk_params.profit_target_multiplier = tp_multiplier
    
    # Alertas de riesgo
    st.subheader("🚨 Alertas de Riesgo")
    risk_events_today = risk_metrics.get('risk_events_today', 0)
    
    if risk_events_today > 0:
        st.warning(f"⚠️ {risk_events_today} eventos de riesgo detectados hoy")
    else:
        st.success("✅ No hay eventos de riesgo activos")
    
    # Indicadores de riesgo visual
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Semáforo de exposición
        if exposure_pct < 50:
            st.success("🟢 Exposición: BAJA")
        elif exposure_pct < 80:
            st.warning("🟡 Exposición: MEDIA")
        else:
            st.error("🔴 Exposición: ALTA")
    
    with col2:
        # Semáforo de drawdown
        if max_drawdown < 5:
            st.success("🟢 Drawdown: BAJO")
        elif max_drawdown < 10:
            st.warning("🟡 Drawdown: MEDIO")
        else:
            st.error("🔴 Drawdown: ALTO")
    
    with col3:
        # Estado general de riesgo
        overall_risk = "BAJO" if exposure_pct < 50 and max_drawdown < 5 else "ALTO"
        risk_color = "success" if overall_risk == "BAJO" else "error"
        getattr(st, risk_color)(f"{'🟢' if overall_risk == 'BAJO' else '🔴'} Riesgo General: {overall_risk}")

# --- PESTAÑA: ALERTAS ---
with tabs[3]:
    st.header("🚨 Alertas y Eventos del Sistema")
    
    # Resumen de alertas
    alerts = list(st.session_state.system_alerts)
    
    if alerts:
        # Contar alertas por tipo
        error_count = sum(1 for alert in alerts if alert.get('level') == 'ERROR')
        warning_count = sum(1 for alert in alerts if alert.get('level') == 'WARNING')
        info_count = sum(1 for alert in alerts if alert.get('level') == 'INFO')
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔴 Errores", error_count)
        with col2:
            st.metric("🟡 Advertencias", warning_count)
        with col3:
            st.metric("🔵 Información", info_count)
        with col4:
            st.metric("📊 Total", len(alerts))
        
        st.markdown("---")
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            level_filter = st.selectbox(
                "Filtrar por nivel:",
                ["Todos", "ERROR", "WARNING", "INFO"],
                key="alert_level_filter"
            )
        
        with col2:
            show_count = st.slider("Mostrar últimas:", 10, 100, 50, 10)
        
        # Mostrar alertas filtradas
        filtered_alerts = alerts
        if level_filter != "Todos":
            filtered_alerts = [a for a in alerts if a.get('level') == level_filter]
        
        # Mostrar las más recientes primero
        filtered_alerts = filtered_alerts[-show_count:]
        filtered_alerts.reverse()
        
        for alert in filtered_alerts:
            level = alert.get('level', 'INFO')
            message = alert.get('message', 'N/A')
            component = alert.get('component', 'N/A')
            timestamp = alert.get('timestamp', 'N/A')
            
            # Formatear timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                time_str = timestamp
            
            # Mostrar alerta según nivel
            if level == 'ERROR':
                st.error(f"🔴 **[{time_str}]** {message} | Componente: {component}")
            elif level == 'WARNING':
                st.warning(f"🟡 **[{time_str}]** {message} | Componente: {component}")
            else:
                st.info(f"🔵 **[{time_str}]** {message} | Componente: {component}")
    
    else:
        st.success("✅ No hay alertas en el sistema")
        st.info("Las alertas aparecerán aquí cuando el backend detecte eventos importantes")
    
    st.markdown("---")
    
    # Señales como alertas de trading
    st.subheader("📈 Señales de Trading (Últimas 24h)")
    
    if st.session_state.signals:
        signals_today = list(st.session_state.signals)[-20:]  # Últimas 20
        
        for signal in reversed(signals_today):
            action = signal.get('action', 'N/A')
            symbol = signal.get('symbol', 'N/A')
            price = signal.get('price', 0)
            confidence = signal.get('confidence', 0)
            strategy = signal.get('strategy', 'N/A')
            
            action_emoji = '🟢' if action == 'BUY' else '🔴'
            conf_level = "Alta" if confidence > 80 else "Media" if confidence > 60 else "Baja"
            
            st.info(f"{action_emoji} **{action}** {symbol} @ ${price:,.4f} | "
                   f"Confianza: {confidence}% ({conf_level}) | Estrategia: {strategy}")
    else:
        st.info("📭 No hay señales de trading recientes")

# --- PESTAÑA: MÉTRICAS ---
with tabs[4]:
    st.header("📊 Métricas y Análisis de Rendimiento")
    
    # Datos de mercado en tiempo real
    st.subheader("💹 Datos de Mercado en Tiempo Real")
    
    if st.session_state.market_data:
        for symbol, data in st.session_state.market_data.items():
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Métricas del símbolo
                price = data.get('price', 0)
                change_24h = data.get('changePercent24h', 0)
                volume = data.get('volume24h', 0)
                
                st.markdown(f"### {symbol}")
                st.metric("Precio", f"${price:,.4f}", f"{change_24h:+.2f}%")
                st.metric("Volumen 24h", f"${volume:,.0f}")
            
            with col2:
                # Gráfico de precio
                price_history = st.session_state.price_history.get(symbol, [])
                if price_history and len(price_history) > 1:
                    df = pd.DataFrame(list(price_history))
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df['time'],
                        y=df['price'],
                        mode='lines',
                        name=symbol,
                        line=dict(color='#00ff88', width=2)
                    ))
                    
                    fig.update_layout(
                        title=f"{symbol} - Evolución del Precio",
                        xaxis_title="Tiempo",
                        yaxis_title="Precio ($)",
                        template="plotly_dark",
                        height=300,
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Esperando datos históricos...")
            
            st.markdown("---")
    else:
        st.info("🔄 Cargando datos de mercado desde WebSocket...")
    
    # Métricas de trading
    st.subheader("📈 Métricas de Trading")
    
    try:
        # Intentar obtener operaciones de Supabase
        if hasattr(st.session_state.operation_repository, 'get_completed_operations'):
            completed_operations = asyncio.run(
                st.session_state.operation_repository.get_completed_operations()
            )
            
            if completed_operations:
                # Calcular métricas
                total_operations = len(completed_operations)
                profitable_ops = [op for op in completed_operations if hasattr(op, 'is_profitable') and op.is_profitable()]
                
                total_profit = sum(
                    float(op.actual_profit) for op in completed_operations 
                    if hasattr(op, 'actual_profit') and op.actual_profit is not None
                )
                
                win_rate = (len(profitable_ops) / total_operations * 100) if total_operations > 0 else 0
                
                # Mostrar métricas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Operaciones", total_operations)
                
                with col2:
                    st.metric("Operaciones Rentables", len(profitable_ops))
                
                with col3:
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                
                with col4:
                    st.metric("Profit Total", f"${total_profit:,.2f}")
                
                # Gráfico de rendimiento
                if len(completed_operations) > 1:
                    profits = []
                    dates = []
                    
                    for op in completed_operations:
                        if hasattr(op, 'actual_profit') and op.actual_profit is not None:
                            profits.append(float(op.actual_profit))
                            if hasattr(op, 'completed_at') and op.completed_at:
                                dates.append(op.completed_at)
                            else:
                                dates.append(datetime.now())
                    
                    if profits and dates:
                        fig = go.Figure()
                        
                        # Profit acumulativo
                        cumulative_profit = [sum(profits[:i+1]) for i in range(len(profits))]
                        
                        fig.add_trace(go.Scatter(
                            x=dates,
                            y=cumulative_profit,
                            mode='lines+markers',
                            name='Profit Acumulativo',
                            line=dict(color='#00ff88', width=2)
                        ))
                        
                        fig.update_layout(
                            title="Evolución del Profit Acumulativo",
                            xaxis_title="Fecha",
                            yaxis_title="Profit ($)",
                            template="plotly_dark",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
            
            else:
                st.info("📊 No hay operaciones completadas para mostrar métricas")
        
        else:
            st.warning("⚠️ Repository mock activo - datos de ejemplo")
            
            # Mostrar métricas mock
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Operaciones", "0")
            with col2:
                st.metric("Win Rate", "0%")
            with col3:
                st.metric("Profit Total", "$0.00")
            with col4:
                st.metric("Sharpe Ratio", "0.00")
    
    except Exception as e:
        st.error(f"Error al cargar métricas de trading: {e}")
        st.info("Verificar conexión con Supabase y estado del backend")

# --- PESTAÑA: CONFIGURACIÓN ---
with tabs[5]:
    st.header("⚙️ Configuración del Sistema")
    
    # Cargar configuración actual
    try:
        current_config = load_config()
        config_loaded = True
    except Exception as e:
        st.error(f"Error cargando configuración: {e}")
        current_config = {}
        config_loaded = False
    
    # Estado de la configuración
    st.subheader("📋 Variables de Entorno")
    
    config_items = [
        ("API_HOST", "Host del Backend API"),
        ("API_PORT", "Puerto del Backend API"),
        ("CAPITAL_INICIAL", "Capital Inicial de Trading"),
        ("UMBRAL_RENTABILIDAD", "Umbral de Rentabilidad (%)"),
        ("BINANCE_API_KEY", "Binance API Key"),
        ("MOBULA_API_KEY", "Mobula API Key"),
        ("TELEGRAM_BOT_TOKEN", "Telegram Bot Token"),
        ("BINANCE_TESTNET", "Modo Testnet")
    ]
    
    for key, description in config_items:
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.markdown(f"**{description}:**")
        
        with col2:
            value = current_config.get(key, 'N/A')
            
            # Ocultar claves sensibles
            if 'KEY' in key or 'TOKEN' in key:
                if isinstance(value, str) and len(value) > 4:
                    display_value = f"{value[:4]}..." + "*" * (len(value) - 4)
                else:
                    display_value = "***"
            else:
                display_value = str(value)
            
            # Color según estado
            if value != 'N/A' and value != '':
                st.success(f"✅ {display_value}")
            else:
                st.error(f"❌ No configurado")
    
    st.markdown("---")
    
    # Modo de operación
    st.subheader("🎛️ Modo de Operación")
    
    current_testnet = current_config.get('BINANCE_TESTNET', True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        mode_options = ["🧪 Paper Trading (Testnet)", "💰 Live Trading (Mainnet)"]
        current_mode = 0 if current_testnet else 1
        
        selected_mode = st.radio(
            "Seleccionar modo:",
            mode_options,
            index=current_mode
        )
        
        new_testnet = (selected_mode == mode_options[0])
        
        if new_testnet != current_testnet:
            st.warning("⚠️ Cambio detectado - Se requiere reinicio del sistema")
    
    with col2:
        # Estado actual
        current_mode_text = "Paper Trading (Testnet)" if current_testnet else "Live Trading (Mainnet)"
        mode_color = "🧪" if current_testnet else "💰"
        
        st.info(f"**Modo Actual:** {mode_color} {current_mode_text}")
        
        if current_testnet:
            st.success("✅ Operando en modo seguro (Testnet)")
        else:
            st.error("⚠️ ¡ATENCIÓN! Operando con dinero real")
    
    st.markdown("---")
    
    # Herramientas de configuración
    st.subheader("🔧 Herramientas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Recargar Configuración", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("🧪 Probar Conexiones", use_container_width=True):
            with st.spinner("Probando conexiones..."):
                # Probar backend
                backend_ok = st.session_state.backend_status['api_responsive']
                
                # Probar Supabase
                supabase_ok = False
                if hasattr(st.session_state.supabase_client, 'check_connection'):
                    supabase_ok = st.session_state.supabase_client.check_connection()
                
                # Mostrar resultados
                st.success(f"Backend API: {'✅' if backend_ok else '❌'}")
                st.success(f"Supabase: {'✅' if supabase_ok else '❌'}")
                st.success(f"WebSocket: {'✅' if st.session_state.ws_connected else '❌'}")
    
    with col3:
        if st.button("📊 Estado del Sistema", use_container_width=True):
            st.json({
                "imports_success": IMPORTS_SUCCESS,
                "websocket_connected": st.session_state.ws_connected,
                "backend_responsive": st.session_state.backend_status['api_responsive'],
                "active_strategies": sum(st.session_state.active_strategies.values()),
                "signals_count": len(st.session_state.signals),
                "trades_count": len(st.session_state.trades)
            })

# === FOOTER Y AUTO-REFRESH ===
st.markdown("---")

# Footer con información del sistema
col1, col2, col3 = st.columns(3)

with col1:
    st.caption("🚀 **Bot Arbitraje v3.0** - Trading Automatizado con IA")

with col2:
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.caption(f"🕒 Última actualización: {last_update}")

with col3:
    status_emoji = "🟢" if st.session_state.ws_connected and IMPORTS_SUCCESS else "🟡"
    status_text = "Operativo" if st.session_state.ws_connected and IMPORTS_SUCCESS else "Limitado"
    st.caption(f"{status_emoji} Estado: {status_text}")

# Auto-refresh mejorado
if st.session_state.ws_connected:
    # Actualizar cada 2 segundos si hay conexión WebSocket
    time.sleep(2)
    st.rerun()
else:
    # Actualizar cada 5 segundos si no hay conexión para intentar reconectar
    time.sleep(5)
    st.rerun()

# === INICIALIZACIÓN DE WEBSOCKET ===
# Iniciar WebSocket client si no está corriendo
if 'ws_client' not in st.session_state and st.session_state.backend_status['api_responsive']:
    try:
        ws_client = EnhancedWebSocketClient(st.session_state.message_queue)
        thread = threading.Thread(target=ws_client.start, daemon=True)
        thread.start()
        st.session_state.ws_client = ws_client
    except Exception as e:
        st.error(f"Error iniciando WebSocket client: {e}")
