#Bot Arbitraje - Dashboard de Trading con Streamlit
#UI moderna y simple sin complicaciones de WebSocket
#                         price = data["data"]["price"]
#                         logger.info(f"📈 Datos de mercado recibidos: {symbol} - ${price}")
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
import requests # Importar la librería requests

# Importar SystemMonitor
from src.infrastructure.monitoring.system_monitor import SystemMonitor, HealthStatus, AlertSeverity
# Importar AdvancedRiskManager y RiskParameters
from src.domain.risk_management.advanced_risk_manager import AdvancedRiskManager, RiskParameters
# Importar SupabaseClient y OperationRepositoryImpl
from src.infrastructure.external_apis.supabase_client import SupabaseClient
from src.infrastructure.database.operation_repository_impl import OperationRepositoryImpl
from src.utils.performance_calculator import calcular_metricas_rendimiento # Importar la función de cálculo de métricas

# Configuración de la página
st.set_page_config(
    page_title="Bot Arbitraje - Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'market_data' not in st.session_state:
    st.session_state.market_data = {}
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {
        'totalValue': 10000,
        'totalPnL': 0,
        'totalPnLPercent': 0,
        'availableBalance': 10000,
        'dailyPnL': 0
    }
if 'signals' not in st.session_state:
    st.session_state.signals = deque(maxlen=50)
if 'trades' not in st.session_state:
    st.session_state.trades = deque(maxlen=100)
if 'price_history' not in st.session_state:
    st.session_state.price_history = {
        'BTCUSDT': deque(maxlen=100),
        'ETHUSDT': deque(maxlen=100)
    }
if 'ws_connected' not in st.session_state:
    st.session_state.ws_connected = False
if 'message_queue' not in st.session_state:
    st.session_state.message_queue = queue.Queue()
if 'system_status_backend' not in st.session_state: # Nuevo estado para datos del backend
    st.session_state.system_status_backend = {
        'overall_health': 'UNKNOWN',
        'active_alerts_count': 0,
        'monitoring_status': 'stopped',
        'timestamp': datetime.now().isoformat()
    }
if 'risk_metrics_backend' not in st.session_state: # Nuevo estado para datos de riesgo del backend
    st.session_state.risk_metrics_backend = {
        'current_capital': 0.0,
        'available_capital': 0.0,
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

# Inicializar SystemMonitor (se mantendrá para la estructura, pero los datos vendrán del backend)
if 'system_monitor' not in st.session_state:
    st.session_state.system_monitor = SystemMonitor()

# Inicializar AdvancedRiskManager (se mantendrá para la estructura, pero los datos vendrán del backend)
if 'risk_manager' not in st.session_state:
    st.session_state.risk_manager = AdvancedRiskManager()

# Inicializar SupabaseClient y OperationRepositoryImpl
if 'supabase_client' not in st.session_state:
    st.session_state.supabase_client = SupabaseClient()
if 'operation_repository' not in st.session_state:
    st.session_state.operation_repository = OperationRepositoryImpl(st.session_state.supabase_client)

# WebSocket handler en thread separado
class WebSocketClient:
    def __init__(self, message_queue):
        self.message_queue = message_queue
        self.running = False
        
    async def connect(self):
        uri = "ws://localhost:8001/ws"
        try:
            async with websockets.connect(uri) as websocket:
                st.session_state.ws_connected = True
                
                # Subscribe to channels
                await websocket.send(json.dumps({
                    "type": "subscribe",
                    "channels": ["market_data", "trading_signals", "portfolio_updates"]
                }))
                
                while self.running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        self.message_queue.put(data)
                        
                        # Respond to heartbeat
                        if data.get('type') == 'heartbeat':
                            await websocket.send(json.dumps({
                                'type': 'heartbeat_ack',
                                'timestamp': time.time()
                            }))
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        print(f"Error: {e}")
                        
        except Exception as e:
            print(f"Connection error: {e}")
            st.session_state.ws_connected = False
            
    def start(self):
        self.running = True
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.connect())
        
    def stop(self):
        self.running = False

# Procesar mensajes del WebSocket
def process_websocket_messages():
    while not st.session_state.message_queue.empty():
        try:
            message = st.session_state.message_queue.get_nowait()
            msg_type = message.get('type')
            
            if msg_type == 'market_data':
                data = message['data']
                st.session_state.market_data[data['symbol']] = data
                
                # Actualizar historial de precios
                if data['symbol'] in st.session_state.price_history:
                    st.session_state.price_history[data['symbol']].append({
                        'time': datetime.now(),
                        'price': data['price']
                    })
                    
            elif msg_type == 'portfolio_update':
                st.session_state.portfolio = message['data']
                
            elif msg_type == 'trading_signal':
                st.session_state.signals.append(message['data'])
                
            elif msg_type == 'trade_executed':
                st.session_state.trades.append(message['data'])
            
            elif msg_type == 'system_metrics': # Manejar mensajes de system_metrics
                system_monitor_data = message['data'].get('system_monitor_status', {})
                st.session_state.system_status_backend = system_monitor_data
                
                # Extraer las métricas de riesgo si están en el mismo mensaje
                st.session_state.risk_metrics_backend = {
                    'current_capital': message['data'].get('portfolio_value', 0.0),
                    'available_capital': message['data'].get('available_balance', 0.0),
                    'daily_pnl': message['data'].get('daily_pnl', 0.0),
                    'total_pnl': message['data'].get('total_pnl', 0.0),
                    'open_positions': message['data'].get('open_positions', 0),
                    'total_exposure': message['data'].get('total_exposure', 0.0),
                    'exposure_percentage': message['data'].get('exposure_percentage', 0.0),
                    'unrealized_pnl': message['data'].get('unrealized_pnl', 0.0),
                    'daily_trades': message['data'].get('trades_count', 0),
                    'risk_events_today': message['data'].get('risk_events_today', 0),
                    'max_drawdown': message['data'].get('max_drawdown', 0.0)
                }
            
            # Añadir manejo para alertas generales del sistema
            else:
                # Asumir que cualquier otro tipo de mensaje es una alerta del sistema
                # O que el backend enviará mensajes con 'type': 'system_alert' o 'error_alert'
                alert_level = message.get('level', 'INFO').upper()
                alert_message = message.get('message', str(message))
                alert_component = message.get('component', 'WebSocket')
                alert_timestamp = message.get('timestamp', datetime.now().isoformat())

                st.session_state.system_alerts.append({
                    'level': alert_level,
                    'message': alert_message,
                    'component': alert_component,
                    'timestamp': alert_timestamp
                })
                
        except queue.Empty:
            break

# Header
st.title("🚀 Bot Arbitraje - Trading Dashboard")
st.markdown("### Sistema de Trading Automatizado con IA")

# Barra lateral
with st.sidebar:
    st.title("Menú del Dashboard")
    st.markdown("---")
    st.write("Estado de Conexión:")
    if st.session_state.ws_connected:
        st.success("🟢 Conectado")
    else:
        st.error("🔴 Desconectado")
        if st.button("🔄 Reconectar"):
            st.rerun()
    st.markdown("---")
    st.write("Navegación:")

# Procesar mensajes antes de mostrar
process_websocket_messages()

# Definir las pestañas principales
tab_titles = ["Inicio", "Estrategias", "Riesgos", "Alertas", "Métricas", "Configuración"]
tabs = st.tabs(tab_titles)

# --- Pestaña: Inicio ---
with tabs[0]:
    st.header("Estado General del Sistema")
    st.markdown("---")

    # Mostrar estado del sistema (ahora desde el backend)
    system_status_from_backend = st.session_state.system_status_backend
    st.subheader("Estado del Monitoreo")
    col_health, col_alerts, col_monitor = st.columns(3)
    with col_health:
        st.metric("Salud General", system_status_from_backend['overall_health'].upper())
    with col_alerts:
        st.metric("Alertas Activas", system_status_from_backend['active_alerts_count'])
    with col_monitor:
        st.metric("Estado Monitoreo", system_status_from_backend['monitoring_status'].capitalize())
    st.caption(f"Última actualización: {datetime.fromisoformat(system_status_from_backend['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
    st.markdown("---")

    st.subheader("💼 Trades Ejecutados Recientes")
    if st.session_state.trades:
        trades_df = pd.DataFrame(list(st.session_state.trades))
        display_df = trades_df[['symbol', 'side', 'price', 'quantity', 'pnl']].copy()
        display_df['pnl'] = display_df['pnl'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay trades ejecutados aún")

# --- Pestaña: Estrategias ---
with tabs[1]:
    st.header("Gestión de Estrategias")
    st.markdown("### Activación, Configuración y Resultados")
    
    # Controles de Trading (existente, movido aquí)
    # Función para enviar comandos al backend
    def send_trading_command(action: str):
        backend_url = "http://localhost:8001/api/trading/control"
        try:
            response = requests.post(backend_url, json={"action": action})
            if response.status_code == 200:
                st.success(f"Comando '{action}' enviado. Estado: {response.json().get('state')}")
            else:
                st.error(f"Error al enviar comando '{action}': {response.status_code} - {response.text}")
        except requests.exceptions.ConnectionError:
            st.error("No se pudo conectar al servidor de backend. Asegúrate de que esté corriendo.")
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

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
    st.subheader("Estrategias Disponibles")
    
    # Lista de estrategias (obtenidas de src/domain/strategies/)
    # En un entorno real, esto podría ser dinámico desde el backend
    available_strategies = [
        {"id": "scalping", "name": "Estrategia de Scalping", "description": "Operaciones rápidas para pequeñas ganancias."},
        {"id": "day_trading", "name": "Estrategia de Day Trading", "description": "Operaciones intradía basadas en tendencias."},
        {"id": "simple_arbitrage", "name": "Estrategia de Arbitraje Simple", "description": "Detección de diferencias de precio entre dos pares."},
        {"id": "triangular_arbitrage", "name": "Estrategia de Arbitraje Triangular", "description": "Detección de oportunidades en ciclos de tres pares."}
    ]

    if 'active_strategies' not in st.session_state:
        st.session_state.active_strategies = {s['id']: False for s in available_strategies}

    for strategy in available_strategies:
        col1, col2 = st.columns([0.7, 0.3])
        with col1:
            st.markdown(f"**{strategy['name']}**")
            st.caption(strategy['description'])
        with col2:
            is_active = st.checkbox("Activar", value=st.session_state.active_strategies[strategy['id']], key=f"strategy_{strategy['id']}_active")
            st.session_state.active_strategies[strategy['id']] = is_active
        
        st.write(f"Estado: {'🟢 Activa' if st.session_state.active_strategies[strategy['id']] else '🔴 Inactiva'}")
        st.markdown("---")

    st.info("El estado de activación de las estrategias se gestiona localmente en la interfaz. Para que el backend las utilice, la configuración debe ser cargada al iniciar el motor de trading.")

    st.markdown("---")
    st.subheader("🎯 Señales de Trading Recientes (Relacionadas con Estrategias)")
    if st.session_state.signals:
        signals_df = pd.DataFrame(list(st.session_state.signals))
        for _, signal in signals_df.iterrows():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                if signal.get('action') == 'BUY':
                    st.markdown(f"🟢 **COMPRA** {signal.get('symbol', 'N/A')}")
                else:
                    st.markdown(f"🔴 **VENTA** {signal.get('symbol', 'N/A')}")
            with col2:
                st.write(f"${signal.get('price', 0):,.2f}")
            with col3:
                confidence = signal.get('confidence', 0)
                st.write(f"{confidence}% conf")
            with col4:
                st.caption(signal.get('strategy', ''))
    else:
        st.info("No hay señales de trading aún.")
    
    st.markdown("---")
    st.subheader("💼 Trades Ejecutados Recientes (Relacionados con Estrategias)")
    if st.session_state.trades:
        trades_df = pd.DataFrame(list(st.session_state.trades))
        display_df = trades_df[['symbol', 'side', 'price', 'quantity', 'pnl']].copy()
        display_df['pnl'] = display_df['pnl'].apply(lambda x: f"${x:,.2f}")
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay trades ejecutados aún.")

# --- Pestaña: Riesgos ---
with tabs[2]:
    st.header("Gestión de Riesgos")
    st.markdown("### Parámetros Activos y Configuración")
    
    risk_params = st.session_state.risk_manager.risk_params # Obtener los parámetros actuales

    st.subheader("Parámetros de Capital y Exposición")
    col_loss, col_pos_size, col_total_exp = st.columns(3)
    with col_loss:
        new_max_daily_loss = st.number_input(
            "Pérdida Diaria Máx. (%)",
            min_value=0.0,
            max_value=100.0,
            value=risk_params.max_daily_loss * 100,
            step=0.1,
            format="%.1f",
            key="max_daily_loss_input"
        ) / 100
        # Actualizar el objeto risk_params en la sesión (no persistente en backend)
        risk_params.max_daily_loss = new_max_daily_loss
    with col_pos_size:
        new_max_position_size = st.number_input(
            "Tamaño Máx. Posición (%)",
            min_value=0.0,
            max_value=100.0,
            value=risk_params.max_position_size * 100,
            step=0.1,
            format="%.1f",
            key="max_position_size_input"
        ) / 100
        risk_params.max_position_size = new_max_position_size
    with col_total_exp:
        new_max_total_exposure = st.number_input(
            "Exposición Total Máx. (%)",
            min_value=0.0,
            max_value=100.0,
            value=risk_params.max_total_exposure * 100,
            step=0.1,
            format="%.1f",
            key="max_total_exposure_input"
        ) / 100
        risk_params.max_total_exposure = new_max_total_exposure

    st.markdown("---")
    st.subheader("Límites de Posición y Multiplicadores")
    col_sl_mult, col_tp_mult, col_conc_pos = st.columns(3)
    with col_sl_mult:
        new_stop_loss_multiplier = st.number_input(
            "Multiplicador Stop Loss (ATR)",
            min_value=0.1,
            max_value=10.0,
            value=risk_params.stop_loss_multiplier,
            step=0.1,
            format="%.1f",
            key="stop_loss_multiplier_input"
        )
        risk_params.stop_loss_multiplier = new_stop_loss_multiplier
    with col_tp_mult:
        new_profit_target_multiplier = st.number_input(
            "Multiplicador Take Profit (R/R)",
            min_value=0.1,
            max_value=10.0,
            value=risk_params.profit_target_multiplier,
            step=0.1,
            format="%.1f",
            key="profit_target_multiplier_input"
        )
        risk_params.profit_target_multiplier = new_profit_target_multiplier
    with col_conc_pos:
        new_max_concurrent_positions = st.number_input(
            "Posiciones Concurrentes Máx.",
            min_value=1,
            max_value=100,
            value=risk_params.max_concurrent_positions,
            step=1,
            key="max_concurrent_positions_input"
        )
        risk_params.max_concurrent_positions = new_max_concurrent_positions

    st.markdown("---")
    st.subheader("Métricas de Riesgo Actuales")
    risk_metrics_from_backend = st.session_state.risk_metrics_backend # Usar métricas del backend
    col_cap, col_avail_cap, col_daily_pnl, col_total_pnl = st.columns(4)
    with col_cap:
        st.metric("Capital Actual", f"${risk_metrics_from_backend['current_capital']:,.2f}")
    with col_avail_cap:
        st.metric("Capital Disponible", f"${risk_metrics_from_backend['available_capital']:,.2f}")
    with col_daily_pnl:
        st.metric("P&L Diario", f"${risk_metrics_from_backend['daily_pnl']:,.2f}")
    with col_total_pnl:
        st.metric("P&L Total", f"${risk_metrics_from_backend['total_pnl']:,.2f}")
    
    col_open_pos, col_exposure, col_unrealized, col_daily_trades = st.columns(4)
    with col_open_pos:
        st.metric("Posiciones Abiertas", risk_metrics_from_backend['open_positions'])
    with col_exposure:
        st.metric("Exposición Total (%)", f"{risk_metrics_from_backend['exposure_percentage'] * 100:,.2f}%")
    with col_unrealized:
        st.metric("P&L No Realizado", f"${risk_metrics_from_backend['unrealized_pnl']:,.2f}")
    with col_daily_trades:
        st.metric("Trades Diarios", risk_metrics_from_backend['daily_trades'])

    st.markdown("---")
    st.info("Los parámetros de riesgo configurados aquí son solo para visualización y simulación en el dashboard. Para que los cambios sean efectivos en el motor de trading, deben ser persistidos en el backend y el sistema debe ser reiniciado. La persistencia de estos valores en el backend no es parte de esta tarea.")

# --- Pestaña: Alertas ---
with tabs[3]:
    st.header("Alertas y Eventos Críticos")
    st.markdown("### Log de Alertas del Sistema")
    
    st.subheader("🎯 Señales de Trading Recientes")
    if st.session_state.signals:
        signals_df = pd.DataFrame(list(st.session_state.signals))
        for _, signal in signals_df.iterrows():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                if signal.get('action') == 'BUY':
                    st.markdown(f"🟢 **COMPRA** {signal.get('symbol', 'N/A')}")
                else:
                    st.markdown(f"🔴 **VENTA** {signal.get('symbol', 'N/A')}")
            with col2:
                st.write(f"${signal.get('price', 0):,.2f}")
            with col3:
                confidence = signal.get('confidence', 0)
                st.write(f"{confidence}% conf")
            with col4:
                st.caption(signal.get('strategy', ''))
    else:
        st.info("No hay señales de trading aún")
    
    st.markdown("---")
    st.subheader("Log General de Alertas")
    
    if 'system_alerts' not in st.session_state:
        st.session_state.system_alerts = deque(maxlen=100) # Para almacenar alertas generales del sistema

    # Asumir que los mensajes de tipo 'system_alert' o 'error_alert' se añadirán a esta cola
    # Esto requeriría que el WebSocketClient y process_websocket_messages se adapten para manejar estos tipos
    
    if st.session_state.system_alerts:
        for alert in st.session_state.system_alerts:
            if alert.get('level') == 'ERROR':
                st.error(f"[{alert.get('timestamp', 'N/A')}] {alert.get('message', 'N/A')} - Componente: {alert.get('component', 'N/A')}")
            elif alert.get('level') == 'WARNING':
                st.warning(f"[{alert.get('timestamp', 'N/A')}] {alert.get('message', 'N/A')} - Componente: {alert.get('component', 'N/A')}")
            else:
                st.info(f"[{alert.get('timestamp', 'N/A')}] {alert.get('message', 'N/A')}")
    else:
        st.info("No hay alertas generales del sistema aún.")
    
    st.caption("Las alertas del sistema (errores, estado) se mostrarán aquí si son enviadas por el backend a través del WebSocket.")

# --- Pestaña: Métricas ---
with tabs[4]:
    st.header("Métricas de Rendimiento")
    st.markdown("### Visualización de KPIs Clave")
    
    st.subheader("📊 Datos de Mercado en Tiempo Real")
    if st.session_state.market_data:
        market_cols = st.columns(len(st.session_state.market_data))
        for idx, (symbol, data) in enumerate(st.session_state.market_data.items()):
            with market_cols[idx]:
                change = data.get('changePercent24h', 0)
                price = data.get('price', 0)
                volume = data.get('volume24h', 0)
                st.markdown(f"### {symbol}")
                st.metric(
                    "Precio",
                    f"${price:,.2f}",
                    f"{change:.2f}%",
                    delta_color="normal" if change >= 0 else "inverse"
                )
                st.caption(f"Vol 24h: ${volume:,.0f}")
    else:
        st.info("Cargando datos de mercado...")

    st.markdown("---")
    st.subheader("📈 Gráficos de Precios")
    col1, col2 = st.columns(2)
    for idx, (symbol, history) in enumerate(st.session_state.price_history.items()):
        if history and len(history) > 1:
            df = pd.DataFrame(list(history))
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['time'],
                y=df['price'],
                mode='lines',
                name=symbol,
                line=dict(color='#00ff88' if idx == 0 else '#ff3366', width=2)
            ))
            fig.update_layout(
                title=f"{symbol} - Precio en Tiempo Real",
                xaxis_title="Tiempo",
                yaxis_title="Precio ($)",
                template="plotly_dark",
                height=400
            )
            if idx == 0:
                col1.plotly_chart(fig, use_container_width=True)
            else:
                col2.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📊 Métricas de Rendimiento de Operaciones")

    # Obtener operaciones completadas para calcular métricas
    # Para simplificar, obtendremos todas las operaciones completadas sin filtro de fecha por ahora
    # En un entorno real, se podría añadir un selector de rango de fechas
    try:
        # Usar asyncio.run para llamar a la función asíncrona en un contexto síncrono de Streamlit
        # Esto es una solución temporal para Streamlit. En una aplicación más compleja,
        # se usaría un bucle de eventos o un hilo para manejar las llamadas asíncronas.
        completed_operations = asyncio.run(st.session_state.operation_repository.get_completed_operations())
        
        # Convertir las operaciones a un formato que performance_calculator pueda usar
        # performance_calculator espera 'price' y 'timestamp'.
        # Aquí, usaremos 'actual_profit_percentage' como un proxy para el rendimiento diario
        # y 'completed_at' como timestamp. Esto no es ideal para volatilidad, pero es un inicio.
        
        # Para un cálculo más preciso de Sharpe Ratio y Drawdown, necesitaríamos una serie de tiempo de P&L del portafolio.
        # Por ahora, usaremos los datos de operaciones individuales.
        
        # Datos para calcular métricas de rendimiento (simplificado para el ejemplo)
        # performance_calculator.py espera 'price' y 'timestamp'.
        # Para P&L, win rate, sharpe ratio, drawdown, necesitamos un enfoque diferente.
        # AdvancedRiskManager.get_risk_metrics() ya nos da algunos P&L.
        # Vamos a calcular win rate, sharpe ratio y drawdown aquí directamente.

        total_profit = sum(float(op.actual_profit) for op in completed_operations if op.actual_profit is not None)
        total_trades = len(completed_operations)
        profitable_trades = sum(1 for op in completed_operations if op.is_profitable())
        
        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0

        # Para Sharpe Ratio y Drawdown, necesitamos una serie de retornos.
        # Simplificaremos usando los porcentajes de profit de cada operación.
        returns = [float(op.actual_profit_percentage) for op in completed_operations if op.actual_profit_percentage is not None]
        
        sharpe_ratio = 0.0
        if len(returns) > 1:
            # Usar la función calculate_sharpe_ratio del repositorio si está disponible y es adecuada
            # O calcularlo aquí si los datos son simples
            try:
                # Asumiendo que calculate_sharpe_ratio es un método del repo y es asíncrono
                sharpe_ratio = asyncio.run(st.session_state.operation_repository.calculate_sharpe_ratio(
                    start_date=datetime.min, end_date=datetime.max # Rango completo
                ))
            except Exception as e:
                st.warning(f"No se pudo calcular Sharpe Ratio: {e}")
                sharpe_ratio = 0.0

        # Cálculo de Drawdown (simplificado)
        # Necesitaríamos una serie de valores de capital a lo largo del tiempo para un drawdown preciso.
        # Por ahora, podemos mostrar el max_drawdown del RiskManager si está disponible.
        risk_metrics_for_drawdown = st.session_state.risk_manager.get_risk_metrics()
        max_drawdown = risk_metrics_for_drawdown.get('max_drawdown', 0.0)

        col_pnl, col_win_rate, col_sharpe, col_drawdown = st.columns(4)
        with col_pnl:
            st.metric("P&L Total", f"${total_profit:,.2f}")
        with col_win_rate:
            st.metric("Win Rate", f"{win_rate:,.2f}%")
        with col_sharpe:
            st.metric("Sharpe Ratio", f"{sharpe_ratio:,.2f}")
        with col_drawdown:
            st.metric("Max Drawdown", f"{max_drawdown * 100:,.2f}%") # Asumiendo que max_drawdown es un porcentaje

    except Exception as e:
        st.error(f"Error al cargar o calcular métricas de operaciones: {e}")
        st.info("Asegúrate de que el backend esté enviando datos de operaciones a Supabase y que la conexión sea correcta.")
    
    st.caption("Las métricas de rendimiento se basan en las operaciones completadas registradas en la base de datos.")

# --- Pestaña: Configuración ---
with tabs[5]:
    st.header("Configuración del Sistema")
    st.markdown("### Variables de Entorno, API Keys y Modo de Operación")
    
    from src.utils.config import settings, load_config, save_config # Importar el módulo de configuración

    current_config = load_config() # Cargar la configuración actual

    st.subheader("Variables de Entorno Clave")
    st.write(f"**API Host:** `{current_config.get('API_HOST', 'N/A')}`")
    st.write(f"**API Port:** `{current_config.get('API_PORT', 'N/A')}`")
    st.write(f"**Capital Inicial:** `{current_config.get('CAPITAL_INICIAL', 'N/A'):,.2f}`")
    st.write(f"**Umbral de Rentabilidad:** `{current_config.get('UMBRAL_RENTABILIDAD', 'N/A')}%`")
    st.write(f"**Binance API Key (parcial):** `{current_config.get('BINANCE_API_KEY', 'N/A')[:4]}...`")
    st.write(f"**Mobula API Key (parcial):** `{current_config.get('MOBULA_API_KEY', 'N/A')[:4]}...`")
    st.write(f"**Telegram Bot Token (parcial):** `{current_config.get('TELEGRAM_BOT_TOKEN', 'N/A')[:4]}...`")

    st.markdown("---")
    st.subheader("Modo de Operación")
    
    # Determinar el modo actual basado en BINANCE_TESTNET
    is_testnet = current_config.get('BINANCE_TESTNET', False)
    mode_options = ["Paper Trading (Testnet)", "Live Trading (Mainnet)"]
    current_mode_index = 0 if is_testnet else 1
    
    selected_mode = st.radio(
        "Seleccionar Modo de Operación:",
        options=mode_options,
        index=current_mode_index,
        key="operation_mode_radio"
    )

    # Actualizar la configuración si el modo cambia
    new_is_testnet = (selected_mode == "Paper Trading (Testnet)")
    if new_is_testnet != is_testnet:
        # Esto requeriría una forma de guardar la configuración de vuelta al .env o Supabase
        # Dado que no se debe modificar el backend, solo se mostrará la intención
        st.warning("El cambio de modo de operación requiere reiniciar el sistema para aplicar la nueva configuración.")
        # Aquí se podría llamar a una función de backend para guardar la configuración si existiera
        # Por ahora, solo se actualiza el estado visual o se informa al usuario.
        # Para una persistencia real, se necesitaría un mecanismo de guardado en config.py que afecte el .env o Supabase.
        # current_config['BINANCE_TESTNET'] = new_is_testnet
        # save_config(current_config) # Esto modificaría el backend, lo cual está prohibido.
        # Por lo tanto, solo se muestra el estado y la advertencia.
    
    st.info("El cambio de modo de operación (Paper/Live) se refleja en la interfaz. Para que sea efectivo en el backend, la variable de entorno BINANCE_TESTNET debe ser ajustada y el sistema reiniciado.")

# Footer con información
st.markdown("---")
st.caption("Bot Arbitraje v3.0 - Trading Automatizado con IA | Actualización automática cada 1 segundo")

# Auto-refresh
if st.session_state.ws_connected:
    time.sleep(1)
    st.rerun()

# Iniciar WebSocket client si no está corriendo
if 'ws_client' not in st.session_state:
    ws_client = WebSocketClient(st.session_state.message_queue)
    thread = threading.Thread(target=ws_client.start, daemon=True)
    thread.start()
    st.session_state.ws_client = ws_client
