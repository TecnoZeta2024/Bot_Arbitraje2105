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
                
        except queue.Empty:
            break

# Header
st.title("🚀 Bot Arbitraje - Trading Dashboard")
st.markdown("### Sistema de Trading Automatizado con IA")

# Conexión status
col1, col2, col3 = st.columns([1, 1, 3])
with col1:
    if st.session_state.ws_connected:
        st.success("🟢 Conectado")
    else:
        st.error("🔴 Desconectado")
        
with col2:
    if st.button("🔄 Reconectar"):
        # Reintentar conexión
        st.rerun()

# Portfolio Summary
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "💰 Valor Total",
        f"${st.session_state.portfolio['totalValue']:,.2f}",
        f"{st.session_state.portfolio['totalPnLPercent']:.2f}%"
    )

with col2:
    pnl = st.session_state.portfolio['totalPnL']
    st.metric(
        "📊 P&L Total",
        f"${abs(pnl):,.2f}",
        f"{'↑' if pnl >= 0 else '↓'} {abs(pnl):.2f}",
        delta_color="normal" if pnl >= 0 else "inverse"
    )

with col3:
    daily_pnl = st.session_state.portfolio['dailyPnL']
    st.metric(
        "📈 P&L Diario",
        f"${abs(daily_pnl):,.2f}",
        f"{'↑' if daily_pnl >= 0 else '↓'} {abs(daily_pnl):.2f}",
        delta_color="normal" if daily_pnl >= 0 else "inverse"
    )

with col4:
    st.metric(
        "💸 Balance Disponible",
        f"${st.session_state.portfolio['availableBalance']:,.2f}"
    )

with col5:
    total_trades = len(list(st.session_state.trades))
    st.metric(
        "🔄 Trades Totales",
        total_trades
    )

# Market Data y Gráficos
st.markdown("---")
st.markdown("### 📊 Datos de Mercado en Tiempo Real")

# Procesar mensajes antes de mostrar
process_websocket_messages()

# Tabs para diferentes vistas
tab1, tab2, tab3, tab4 = st.tabs(["📈 Precios", "📊 Gráficos", "🎯 Señales", "💼 Trades"])

with tab1:
    # Mostrar datos de mercado
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

with tab2:
    # Gráficos de precios
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

with tab3:
    # Señales de Trading
    st.markdown("### 🎯 Señales de Trading Recientes")
    
    if st.session_state.signals:
        signals_df = pd.DataFrame(list(st.session_state.signals))
        
        # Mostrar señales con colores
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

with tab4:
    # Trades ejecutados
    st.markdown("### 💼 Trades Ejecutados")
    
    if st.session_state.trades:
        trades_df = pd.DataFrame(list(st.session_state.trades))
        
        # Tabla de trades
        display_df = trades_df[['symbol', 'side', 'price', 'quantity', 'pnl']].copy()
        display_df['pnl'] = display_df['pnl'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay trades ejecutados aún")

# Controles de Trading
st.markdown("---")
st.markdown("### 🎮 Controles de Trading")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("▶️ Iniciar Trading", type="primary", use_container_width=True):
        # Enviar comando al backend
        st.success("Trading iniciado")

with col2:
    if st.button("⏸️ Pausar Trading", use_container_width=True):
        st.warning("Trading pausado")

with col3:
    if st.button("⏹️ Detener Trading", use_container_width=True):
        st.info("Trading detenido")

with col4:
    if st.button("🔄 Actualizar", use_container_width=True):
        st.rerun()

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
