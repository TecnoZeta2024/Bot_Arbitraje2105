import streamlit as st
import pandas as pd

def orderbook_table(title, data, is_bids=True):
    st.subheader(title)
    if data.empty:
        st.write("No hay datos disponibles.")
        return

    # Asegurarse de que las columnas 'price' y 'amount' existan
    if 'price' not in data.columns or 'amount' not in data.columns:
        st.error("Los datos de la tabla deben contener las columnas 'price' y 'amount'.")
        return

    # Ordenar los bids de mayor a menor precio, y los asks de menor a mayor precio
    if is_bids:
        data = data.sort_values(by='price', ascending=False)
    else:
        data = data.sort_values(by='price', ascending=True)

    st.dataframe(data, use_container_width=True, hide_index=True)

if __name__ == '__main__':
    st.title("Ejemplo de Orderbook Table")

    # Datos de prueba para Bids
    bids_data = pd.DataFrame({
        'price': [100.1, 100.0, 99.9],
        'amount': [0.5, 1.2, 0.8],
        'exchange': ['Binance', 'Mobula', 'Binance']
    })
    orderbook_table("Bids de Prueba", bids_data, is_bids=True)

    st.markdown("---")

    # Datos de prueba para Asks
    asks_data = pd.DataFrame({
        'price': [100.2, 100.3, 100.4],
        'amount': [0.7, 1.0, 0.3],
        'exchange': ['Mobula', 'Binance', 'Mobula']
    })
    orderbook_table("Asks de Prueba", asks_data, is_bids=False)
