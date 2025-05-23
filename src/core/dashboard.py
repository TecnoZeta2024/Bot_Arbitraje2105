import os
import sys
from pathlib import Path

import streamlit as st

# Asegurar que el módulo pueda ser importado correctamente
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.append(str(project_root))

# Importar los módulos del dashboard
from src.core.dashboard.auth import authenticate_user, login_page
from src.core.dashboard.config_panel import display_config_panel
from src.core.dashboard.historical_ops import display_historical_operations
from src.core.dashboard.monitoring import display_monitoring_page
from src.core.dashboard.performance import display_performance_charts
from src.utils.config import load_config
from src.utils.ui_components import setup_page_config


def main():
    """
    Función principal del dashboard de Arbitraje Triangular
    """
    # Configuración de la página
    setup_page_config("Bot de Arbitraje Triangular - Dashboard", "📊")
    
    # Cargar configuración
    config = load_config()
    
    # Autenticación
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        
    if not st.session_state.authenticated:
        login_page()
        return
        
    # Barra lateral con navegación
    st.sidebar.title("Arbitraje Triangular")
    st.sidebar.image("assets/logo.png", width=100)
    
    # Menú de navegación
    menu_options = [
        "📈 Monitoreo en Tiempo Real",
        "📋 Operaciones Históricas",
        "📊 Análisis de Rendimiento",
        "⚙️ Configuración"
    ]
    
    selection = st.sidebar.radio("Navegación", menu_options)
    
    # Mostrar página según selección
    if selection == menu_options[0]:
        display_monitoring_page()
    elif selection == menu_options[1]:
        display_historical_operations()
    elif selection == menu_options[2]:
        display_performance_charts()
    elif selection == menu_options[3]:
        display_config_panel()
    
    # Footer con información del sistema
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Versión: 1.0.0")
    
    # Botón de logout
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.experimental_rerun()

if __name__ == "__main__":
    main()
