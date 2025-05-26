import streamlit as st
import pandas as pd
from src.dashboard.components.orderbook_table import orderbook_table

def show_aggregated_orderbooks_page():
    st.title("Agregador de Orderbooks y Detección de Arbitraje")

    st.markdown("""
        Esta página muestra orderbooks agregados de múltiples exchanges en tiempo real,
        calcula los mejores precios y liquidez, y detecta oportunidades de arbitraje cross-exchange.
    """)

    st.header("Orderbooks Agregados")

    # Datos de prueba estáticos para orderbooks
    bids_data = pd.DataFrame({
        'price': [100.15, 100.10, 100.05],
        'amount': [0.8, 1.5, 0.7],
        'exchange': ['Binance', 'Mobula', 'Binance']
    })

    asks_data = pd.DataFrame({
        'price': [100.20, 100.25, 100.30],
        'amount': [1.0, 0.9, 1.2],
        'exchange': ['Mobula', 'Binance', 'Mobula']
    })

    col1, col2 = st.columns(2)
    with col1:
        orderbook_table("Bids Agregados", bids_data, is_bids=True)
    with col2:
        orderbook_table("Asks Agregados", asks_data, is_bids=False)

    st.header("Métricas Agregadas")
    st.markdown("---")

    col3, col4, col5 = st.columns(3)
    with col3:
        st.subheader("Mejor Precio de Compra (Bid)")
        st.metric(label="Precio", value="100.15 USD")
        st.metric(label="Exchange", value="Binance")
    with col4:
        st.subheader("Mejor Precio de Venta (Ask)")
        st.metric(label="Precio", value="100.20 USD")
        st.metric(label="Exchange", value="Mobula")
    with col5:
        st.subheader("Liquidez Total (Ejemplo)")
        st.metric(label="Bids (Cantidad)", value="3.0 BTC")
        st.metric(label="Asks (Cantidad)", value="3.1 BTC")

    st.header("Oportunidades de Arbitraje Detectadas")
    st.markdown("---")

    # Placeholder para oportunidades de arbitraje
    st.info("Aquí se mostrarán las oportunidades de arbitraje cross-exchange en tiempo real.")
    arbitrage_opportunities = pd.DataFrame({
        'Par': ['BTC/USD'],
        'Exchange Compra': ['Binance'],
        'Precio Compra': [100.15],
        'Exchange Venta': ['Mobula'],
        'Precio Venta': [100.20],
        'Beneficio Potencial (%)': [0.05],
        'Estado': ['Activo']
    })
    if not arbitrage_opportunities.empty:
        st.dataframe(arbitrage_opportunities, use_container_width=True, hide_index=True)
    else:
        st.write("No se han detectado oportunidades de arbitraje en este momento.")

if __name__ == '__main__':
    show_aggregated_orderbooks_page()
