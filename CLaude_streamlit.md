Tienes razón, entiendo tu frustración. Los errores de WebSocket con React/Vite pueden ser muy complicados. Te propongo una solución **mucho más simple y elegante** usando **Streamlit**, que es perfecto para dashboards de trading.

## 🚀 Solución con Streamlit - Sin complicaciones

Streamlit es un framework Python que:
- ✅ **No requiere Node.js ni npm**
- ✅ **WebSockets automáticos**
- ✅ **UI moderna y bonita por defecto**
- ✅ **Actualización en tiempo real**
- ✅ **Se integra perfectamente con tu código Python existente**

Vamos a crear un dashboard funcional en minutos:## 🎯 Solución Simple: Dashboard con Streamlit

Entiendo perfectamente tu frustración. Te propongo **Streamlit**, una alternativa MUCHO más simple que React/Vite:

### ✨ Ventajas de Streamlit:
- ✅ **Sin Node.js, npm, ni WebSockets manuales**
- ✅ **Python puro** (ya lo tienes instalado)
- ✅ **Actualización automática en tiempo real**
- ✅ **UI moderna y bonita por defecto**
- ✅ **Se instala en 30 segundos**

### 📦 Instalación (1 comando):
```bash
pip install streamlit plotly pandas
```

### 📝 Crea el archivo `streamlit_dashboard.py`:

```python
"""
Bot Arbitraje - Dashboard Simple con Streamlit
Interfaz moderna sin complicaciones de WebSocket
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Bot Arbitraje Dashboard",
    page_icon="📈",
    layout="wide"
)

# Título
st.title("🚀 Bot Arbitraje - Trading Dashboard")

# Funciones para obtener datos
@st.cache_data(ttl=1)  # Cache por 1 segundo
def get_portfolio():
    try:
        response = requests.get('http://localhost:8001/api/portfolio')
        return response.json()
    except:
        return None

@st.cache_data(ttl=1)
def get_trades():
    try:
        response = requests.get('http://localhost:8001/api/trades?limit=10')
        return response.json()
    except:
        return []

# Portfolio
portfolio = get_portfolio()
if portfolio:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Valor Total", f"${portfolio['totalValue']:,.2f}")
    
    with col2:
        pnl = portfolio['totalPnL']
        st.metric("📊 P&L Total", f"${pnl:,.2f}", 
                 f"{portfolio['totalPnLPercent']:.2f}%")
    
    with col3:
        st.metric("📈 P&L Diario", f"${portfolio['dailyPnL']:,.2f}")
    
    with col4:
        st.metric("💸 Balance", f"${portfolio['availableBalance']:,.2f}")

# Trades recientes
st.subheader("📊 Trades Recientes")
trades = get_trades()

if trades:
    df = pd.DataFrame(trades)
    st.dataframe(df[['symbol', 'side', 'price', 'quantity', 'pnl']], 
                 use_container_width=True)

# Controles
st.subheader("🎮 Controles")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("▶️ Iniciar Trading", type="primary"):
        requests.post('http://localhost:8001/api/trading/control', 
                     params={'action': 'start'})
        st.success("Trading iniciado!")

with col2:
    if st.button("⏸️ Pausar"):
        requests.post('http://localhost:8001/api/trading/control', 
                     params={'action': 'pause'})
        st.warning("Trading pausado")

with col3:
    if st.button("🔄 Actualizar"):
        st.rerun()

# Auto-actualización
st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
time.sleep(2)
st.rerun()
```

### 🚀 Para ejecutar:

```bash
# En la carpeta del proyecto
cd C:\Users\zamor\Bot_Arbitraje2105

# Ejecutar Streamlit
streamlit run src/streamlit_dashboard.py
```

## 🎨 Alternativas Aún Más Simples:

### 1. **Gradio** (Similar a Streamlit):
```python
import gradio as gr
import requests

def get_portfolio_info():
    response = requests.get('http://localhost:8001/api/portfolio')
    data = response.json()
    return f"Valor: ${data['totalValue']:,.2f} | P&L: ${data['totalPnL']:,.2f}"

interface = gr.Interface(
    fn=get_portfolio_info,
    inputs=None,
    outputs="text",
    title="Bot Arbitraje Dashboard"
)

interface.launch()
```

### 2. **Panel HTML Simple** (Sin frameworks):
```html
<!DOCTYPE html>
<html>
<head>
    <title>Bot Arbitraje</title>
    <style>
        body { 
            background: #1a1a1a; 
            color: white; 
            font-family: Arial;
            padding: 20px;
        }
        .metric { 
            background: #2a2a2a; 
            padding: 20px; 
            margin: 10px;
            border-radius: 10px;
            display: inline-block;
        }
    </style>
</head>
<body>
    <h1>📈 Bot Arbitraje Dashboard</h1>
    <div id="portfolio"></div>
    
    <script>
        async function updateData() {
            const response = await fetch('http://localhost:8001/api/portfolio');
            const data = await response.json();
            
            document.getElementById('portfolio').innerHTML = `
                <div class="metric">
                    <h3>Valor Total</h3>
                    <h2>$${data.totalValue.toFixed(2)}</h2>
                </div>
                <div class="metric">
                    <h3>P&L</h3>
                    <h2>$${data.totalPnL.toFixed(2)}</h2>
                </div>
            `;
        }
        
        setInterval(updateData, 1000);
        updateData();
    </script>
</body>
</html>
```

## 🔧 Script de Inicio Rápido para Streamlit:

```batch
@echo off
echo Iniciando Bot Arbitraje con Streamlit...

REM Instalar dependencias si no existen
pip install streamlit plotly pandas requests

REM Iniciar backend
start cmd /k "cd /d C:\Users\zamor\Bot_Arbitraje2105 && python src\production_server.py"

REM Esperar 3 segundos
timeout /t 3

REM Iniciar Streamlit
cd /d C:\Users\zamor\Bot_Arbitraje2105
streamlit run src\streamlit_dashboard.py

pause
```

### 💡 ¿Por qué Streamlit es mejor para tu caso?

1. **Sin WebSockets manuales** - Se encarga automáticamente
2. **Sin npm/node** - Solo Python
3. **UI bonita por defecto** - No necesitas CSS
4. **Actualización automática** - Con `st.rerun()`
5. **Gráficos incluidos** - Con Plotly integrado

¿Quieres que te ayude a implementar el dashboard con Streamlit? Es literalmente copiar el código y ejecutar. ¡Sin complicaciones! 🚀