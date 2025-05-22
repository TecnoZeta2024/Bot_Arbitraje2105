import streamlit as st
import pandas as pd
import numpy as np
import json
import time
from typing import List, Dict, Any
from datetime import datetime

# Import necessary functions from detectar_oportunidades.py
from src.core.detectar_oportunidades import send_opportunities_to_webhook
from src.utils.config import settings

# Import dependency injection
from src.core.dashboard.dependency_injection import get_service_registry
from src.core.dashboard.services.opportunity_detection_service import OpportunityDetectionService

def display_detection_page():
    """
    Displays an optimized triangular arbitrage opportunity detection page in the dashboard.
    Implements a simplified, integrated workflow with advanced detection parameters.
    """
    # Get the OpportunityDetectionService from the dependency injection container
    registry = get_service_registry()
    opportunity_service = registry.get(OpportunityDetectionService)
    
    # Initialize session state for tracking workflow
    if 'workflow_stage' not in st.session_state:
        st.session_state['workflow_stage'] = 'config'  # Stages: config, data_fetch, detection, results
    
    if 'detection_history' not in st.session_state:
        st.session_state['detection_history'] = []
        
    # Main header
    st.title("🔍 Sistema de Detección de Arbitraje Triangular")
    
    # Sidebar for configuration and workflow control
    with st.sidebar:
        st.header("Flujo de Trabajo")
        
        # Workflow steps indicator
        steps = {
            'config': {"title": "1. Configuración", "icon": "⚙️", "active": st.session_state['workflow_stage'] == 'config'},
            'data_fetch': {"title": "2. Datos de Mercado", "icon": "📊", "active": st.session_state['workflow_stage'] == 'data_fetch'},
            'detection': {"title": "3. Detección", "icon": "🔎", "active": st.session_state['workflow_stage'] == 'detection'},
            'results': {"title": "4. Resultados", "icon": "💰", "active": st.session_state['workflow_stage'] == 'results'}
        }
        
        for step_id, step in steps.items():
            if step["active"]:
                st.markdown(f"**{step['icon']} {step['title']} ← ACTUAL**")
            else:
                st.markdown(f"{step['icon']} {step['title']}")
        
        st.divider()
        
        # Quick navigation
        st.subheader("Navegación Rápida")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⬅️ Anterior", disabled=st.session_state['workflow_stage'] == 'config'):
                # Move to previous stage
                workflow_stages = list(steps.keys())
                current_index = workflow_stages.index(st.session_state['workflow_stage'])
                if current_index > 0:
                    st.session_state['workflow_stage'] = workflow_stages[current_index - 1]
                    st.rerun()
        
        with col2:
            if st.button("Siguiente ➡️", disabled=st.session_state['workflow_stage'] == 'results'):
                # Move to next stage
                workflow_stages = list(steps.keys())
                current_index = workflow_stages.index(st.session_state['workflow_stage'])
                if current_index < len(workflow_stages) - 1:
                    st.session_state['workflow_stage'] = workflow_stages[current_index + 1]
                    st.rerun()
        
        # Reset workflow button
        if st.button("🔄 Reiniciar Flujo"):
            st.session_state['workflow_stage'] = 'config'
            if 'market_data_fetched' in st.session_state:
                del st.session_state['market_data_fetched']
            if 'opportunities' in st.session_state:
                del st.session_state['opportunities']
            st.rerun()
            
        # Stats
        if 'symbols' in st.session_state and 'tickers' in st.session_state:
            st.divider()
            st.subheader("Estadísticas")
            st.metric("Símbolos Cargados", len(st.session_state['symbols']))
            st.metric("Tickers Disponibles", len(st.session_state['tickers']))
            
            if 'opportunities' in st.session_state and st.session_state['opportunities']:
                st.metric("Oportunidades Encontradas", len(st.session_state['opportunities']))
                
                # Get best opportunity
                best_opp = max(st.session_state['opportunities'], key=lambda x: x.get('profit_percentage_net', 0))
                st.metric("Mejor Rentabilidad", f"{best_opp.get('profit_percentage_net', 0):.4f}%")
    
    # Main content area based on workflow stage
    if st.session_state['workflow_stage'] == 'config':
        display_configuration_stage(opportunity_service)
    elif st.session_state['workflow_stage'] == 'data_fetch':
        display_data_fetch_stage(opportunity_service)
    elif st.session_state['workflow_stage'] == 'detection':
        display_detection_stage(opportunity_service)
    elif st.session_state['workflow_stage'] == 'results':
        display_results_stage(opportunity_service)

def display_configuration_stage(opportunity_service):
    """Configure parameters for market data fetch and opportunity detection."""
    st.header("1. Configuración de Parámetros")
    st.write("Configure los parámetros para la obtención de datos y detección de oportunidades.")
    
    # Create tabs for different configuration categories
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Datos de Mercado", 
        "🔎 Detección de Oportunidades", 
        "💲 Configuración Financiera",
        "🛠️ Opciones Avanzadas"
    ])
    
    with tab1:
        st.subheader("Configuración de Datos de Mercado")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Token search parameters
            token_search_limit = st.number_input(
                "Límite de Búsqueda de Tokens",
                min_value=10,
                max_value=2000,
                value=settings.token_search_limit if hasattr(settings, 'token_search_limit') else 400,
                step=10,
                help="Número máximo de tokens a obtener de las APIs."
            )
            
            api_rate_limit = st.number_input(
                "Límite de Parámetros por Llamada API",
                min_value=100,
                max_value=1000,
                value=400,
                step=50,
                help="Límite de symbols/tickers/parámetros por llamada API (Binance limita a 400)."
            )
        
        with col2:
            # Data source configuration
            data_source_priority = st.selectbox(
                "Prioridad de Fuente de Datos",
                options=["Mobula → Binance", "Binance → Mobula", "Solo Mobula", "Solo Binance"],
                index=0,
                help="Orden de prioridad para obtener datos de mercado."
            )
            
            market_fetch_timeout = st.number_input(
                "Timeout para Obtención de Datos (segundos)",
                min_value=5,
                max_value=300,
                value=30,
                step=5,
                help="Tiempo máximo de espera para obtener datos de mercado."
            )
        
        # Exchange selection (new)
        st.subheader("Configuración de Exchange")
        exchange_options = ["Binance", "KuCoin", "Gate.io", "OKX", "Huobi"]
        selected_exchanges = st.multiselect(
            "Exchanges a Consultar",
            options=exchange_options,
            default=["Binance"],
            help="Seleccione los exchanges de los que obtener datos. Nota: Actualmente solo Binance está completamente implementado."
        )
        
        if len(selected_exchanges) > 1:
            st.info("⚠️ Configuración multi-exchange: Esto puede aumentar los tiempos de procesamiento.")
    
    with tab2:
        st.subheader("Parámetros de Detección de Oportunidades")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Profitability thresholds
            umbral_rentabilidad = st.number_input(
                "Umbral de Rentabilidad Mínima (%)",
                min_value=0.0,
                max_value=200.0,
                value=settings.umbral_rentabilidad,
                step=0.1,
                format="%.2f",
                help="Porcentaje mínimo de rentabilidad bruta para considerar una oportunidad."
            )
            
            min_net_profit = st.number_input(
                "Rentabilidad Neta Mínima (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.5,
                step=0.1,
                format="%.2f",
                help="Porcentaje mínimo de rentabilidad neta (después de comisiones) para considerar una oportunidad."
            )
        
        with col2:
            # Token filtering criteria
            min_token_age = st.slider(
                "Edad Mínima del Token (días)",
                min_value=0,
                max_value=365,
                value=30,
                help="Edad mínima del token para ser considerado en la detección (reduce riesgos con tokens nuevos)."
            )
            
            # Risk level selector (new)
            risk_level = st.select_slider(
                "Nivel de Riesgo",
                options=["Muy Bajo", "Bajo", "Moderado", "Alto", "Muy Alto"],
                value="Moderado",
                help="Nivel de riesgo aceptable para las oportunidades detectadas."
            )
        
        # Token parameter criteria
        st.subheader("Criterios de Filtrado de Tokens")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_marketcap = st.number_input(
                "Capitalización Mínima (USD)",
                min_value=0,
                max_value=10000000000,
                value=500000,
                step=100000,
                format="%d",
                help="Capitalización de mercado mínima para considerar un token."
            )
        
        with col2:
            min_volume = st.number_input(
                "Volumen 24h Mínimo (USD)",
                min_value=0,
                max_value=100000000,
                value=50000,
                step=10000,
                format="%d",
                help="Volumen mínimo de las últimas 24 horas para considerar un token."
            )
            
        with col3:
            min_liquidity = st.number_input(
                "Liquidez Mínima (USD)",
                min_value=0,
                max_value=10000000,
                value=10000,
                step=1000,
                format="%d",
                help="Liquidez mínima para considerar un token."
            )
            
        # Advanced token filtering (new)
        st.subheader("Filtrado Avanzado de Tokens")
        col1, col2 = st.columns(2)
        
        with col1:
            exclude_stablecoins = st.checkbox(
                "Excluir Stablecoins",
                value=False,
                help="Excluir stablecoins conocidas de la detección de oportunidades."
            )
            
            exclude_leveraged = st.checkbox(
                "Excluir Tokens Apalancados",
                value=True,
                help="Excluir tokens con apalancamiento (ej. 3x BTC) de la detección."
            )
            
        with col2:
            exclude_meme_tokens = st.checkbox(
                "Excluir Meme Tokens",
                value=False,
                help="Intentar excluir tokens de memes conocidos de la detección."
            )
            
            check_token_security = st.checkbox(
                "Verificar Seguridad del Token",
                value=True,
                help="Verificar auditorías y vulnerabilidades conocidas de los tokens."
            )
    
    with tab3:
        st.subheader("Configuración Financiera")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Capital configuration
            capital_inicial = st.number_input(
                "Capital Inicial Sugerido",
                min_value=10.0,
                max_value=100000.0,
                value=settings.capital_inicial,
                step=10.0,
                format="%.2f",
                help="Capital inicial sugerido para calcular los montos de los pasos de la operación."
            )
            
            max_capital_per_trade = st.number_input(
                "Capital Máximo por Operación",
                min_value=10.0,
                max_value=100000.0,
                value=settings.capital_inicial * 2 if hasattr(settings, 'capital_inicial') else 1000.0,
                step=100.0,
                format="%.2f",
                help="Capital máximo a utilizar en una sola operación de arbitraje."
            )
        
        with col2:
            # Risk management
            max_capital_exposure = st.slider(
                "Exposición Máxima del Capital (%)",
                min_value=1,
                max_value=100,
                value=25,
                help="Porcentaje máximo del capital total a exponer en operaciones simultáneas."
            )
            
            stop_loss_percentage = st.slider(
                "Stop Loss Porcentual (%)",
                min_value=0.1,
                max_value=10.0,
                value=2.0,
                step=0.1,
                help="Porcentaje de pérdida máxima permitida antes de cerrar la posición."
            )
        
        # Fee configuration section
        st.subheader("Configuración de Comisiones")
        
        fee_type = st.radio(
            "Tipo de Comisión",
            options=["Taker (market order)", "Maker (limit order)", "Personalizado"],
            index=0,
            help="Tipo de comisión a aplicar en los cálculos."
        )
        
        if fee_type == "Personalizado":
            # Custom fees for each step
            col_fee1, col_fee2, col_fee3 = st.columns(3)
            with col_fee1:
                fee_step1 = st.number_input(
                    "Comisión Paso 1 (%)",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.1,
                    step=0.01,
                    format="%.3f"
                )
            with col_fee2:
                fee_step2 = st.number_input(
                    "Comisión Paso 2 (%)",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.1,
                    step=0.01,
                    format="%.3f"
                )
            with col_fee3:
                fee_step3 = st.number_input(
                    "Comisión Paso 3 (%)",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.1,
                    step=0.01,
                    format="%.3f"
                )
            fees_percentage = [fee_step1, fee_step2, fee_step3]
        else:
            # Standard fee
            fee_value = st.number_input(
                f"Fee {fee_type} (%)",
                min_value=0.0,
                max_value=2.0,
                value=0.1 if fee_type == "Taker (market order)" else 0.075,
                step=0.01,
                format="%.3f",
                help=f"Porcentaje de la tarifa {fee_type.lower()}."
            )
            fees_percentage = [fee_value, fee_value, fee_value]
            
        # Additional fee considerations (new)
        st.subheader("Consideraciones Adicionales de Comisiones")
        col1, col2 = st.columns(2)
        
        with col1:
            use_bnb_discount = st.checkbox(
                "Aplicar Descuento BNB",
                value=True,
                help="Aplicar descuento por pagar comisiones con BNB en Binance."
            )
            
        with col2:
            vip_level = st.selectbox(
                "Nivel VIP en Exchange",
                options=["Ninguno", "VIP 1", "VIP 2", "VIP 3", "VIP 4", "VIP 5+"],
                index=0,
                help="Nivel VIP en el exchange para aplicar descuentos correspondientes."
            )
    
    with tab4:
        st.subheader("Opciones Avanzadas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Processing parameters
            max_pairs = st.number_input(
                "Máximo de Combinaciones a Verificar",
                min_value=1000,
                max_value=10000000,
                value=100000,
                step=10000,
                format="%d",
                help="Limita el número de combinaciones de pares a verificar para prevenir timeouts."
            )
            
            parallel_processing = st.checkbox(
                "Procesamiento Paralelo",
                value=True,
                help="Utilizar procesamiento paralelo para acelerar la detección (consume más CPU)."
            )
            
            if parallel_processing:
                n_workers = st.slider(
                    "Número de Workers",
                    min_value=2,
                    max_value=16,
                    value=4,
                    help="Número de procesos paralelos para la detección."
                )
        
        with col2:
            # Results configuration
            limit_results = st.checkbox(
                "Limitar Resultados",
                value=True
            )
            
            if limit_results:
                top_results = st.number_input(
                    "Mostrar Top N Oportunidades",
                    min_value=1,
                    max_value=100,
                    value=10,
                    step=1,
                    help="Número máximo de oportunidades a mostrar, ordenadas por rentabilidad."
                )
                
            sort_by = st.selectbox(
                "Ordenar Resultados Por",
                options=[
                    "Rentabilidad Neta (desc)", 
                    "Rentabilidad Bruta (desc)", 
                    "Volumen (desc)",
                    "Riesgo (asc)",
                    "Complejidad (asc)"
                ],
                index=0,
                help="Criterio para ordenar las oportunidades encontradas."
            )
        
        # Base tokens configuration
        st.subheader("Configuración de Tokens Base")
        
        # Add option to filter by specific base/quote coins
        include_base_coins = st.multiselect(
            "Incluir Monedas Base",
            options=["BTC", "ETH", "BNB", "USDT", "BUSD", "USDC", "XRP", "ADA", "DOGE", "SOL", "AVAX", "MATIC", "DOT", "TRX"],
            default=["BTC", "ETH", "BNB", "USDT"],
            help="Solo incluir pares con estas monedas base."
        )
        
        # Excluded tokens
        excluded_tokens = st.text_area(
            "Tokens a Excluir (uno por línea)",
            value="BOME\nSAFEMOON\nSQUID\nWORTHLESS",
            help="Lista de tokens específicos a excluir de la detección."
        )
        
        # Advanced execution options (new)
        st.subheader("Opciones de Ejecución Avanzadas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            execution_mode = st.selectbox(
                "Modo de Ejecución",
                options=["Simulación", "Testnet", "Producción"],
                index=0,
                help="Modo de ejecución de las operaciones detectadas."
            )
            
            if execution_mode == "Producción":
                st.warning("⚠️ Modo de producción: Se ejecutarán operaciones con capital real!")
                confirm_production = st.checkbox("Confirmo que quiero operar con capital real")
        
        with col2:
            execution_strategy = st.selectbox(
                "Estrategia de Ejecución",
                options=["Secuencial", "Paralela", "Híbrida"],
                index=0,
                help="Estrategia para ejecutar las transacciones de arbitraje."
            )
            
            retry_failed = st.checkbox(
                "Reintentar Operaciones Fallidas",
                value=True,
                help="Reintentar operaciones que fallaron (hasta 3 veces)."
            )
    
    # Store all parameters in session state
    st.session_state['detection_params'] = {
        # Market data parameters
        'token_search_limit': token_search_limit,
        'api_rate_limit': api_rate_limit,
        'data_source_priority': data_source_priority,
        'market_fetch_timeout': market_fetch_timeout,
        'selected_exchanges': selected_exchanges,
        
        # Opportunity detection parameters
        'umbral_rentabilidad': umbral_rentabilidad,
        'min_net_profit': min_net_profit,
        'min_token_age': min_token_age,
        'risk_level': risk_level,
        
        # Token filtering
        'min_marketcap': min_marketcap,
        'min_volume': min_volume,
        'min_liquidity': min_liquidity,
        'exclude_stablecoins': exclude_stablecoins,
        'exclude_leveraged': exclude_leveraged,
        'exclude_meme_tokens': exclude_meme_tokens,
        'check_token_security': check_token_security,
        
        # Financial parameters
        'capital_inicial': capital_inicial,
        'max_capital_per_trade': max_capital_per_trade,
        'max_capital_exposure': max_capital_exposure,
        'stop_loss_percentage': stop_loss_percentage,
        'fees_percentage': fees_percentage,
        'use_bnb_discount': use_bnb_discount,
        'vip_level': vip_level,
        
        # Advanced options
        'max_pairs': max_pairs,
        'parallel_processing': parallel_processing,
        'n_workers': n_workers if parallel_processing else 1,
        'limit_results': limit_results,
        'top_results': top_results if limit_results else None,
        'sort_by': sort_by,
        'include_base_coins': include_base_coins,
        'excluded_tokens': [t.strip() for t in excluded_tokens.split('\n') if t.strip()],
        'execution_mode': execution_mode,
        'execution_strategy': execution_strategy,
        'retry_failed': retry_failed
    }
    
    # Add preset configurations
    st.subheader("Presets de Configuración")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💼 Conservador", use_container_width=True):
            # Conservative preset - prioritizes safety over profit
            st.session_state['detection_params'].update({
                'umbral_rentabilidad': 1.0,
                'min_net_profit': 0.75,
                'min_marketcap': 5000000,
                'min_volume': 500000,
                'min_token_age': 180,
                'risk_level': "Bajo",
                'max_capital_exposure': 15,
                'stop_loss_percentage': 1.0,
                'check_token_security': True,
                'execution_mode': "Simulación"
            })
            st.rerun()
    
    with col2:
        if st.button("⚖️ Balanceado", use_container_width=True):
            # Balanced preset - middle ground
            st.session_state['detection_params'].update({
                'umbral_rentabilidad': 0.5,
                'min_net_profit': 0.2,
                'min_marketcap': 1000000,
                'min_volume': 100000,
                'min_token_age': 60,
                'risk_level': "Moderado",
                'max_capital_exposure': 25,
                'stop_loss_percentage': 2.0,
                'check_token_security': True,
                'execution_mode': "Testnet"
            })
            st.rerun()
    
    with col3:
        if st.button("🚀 Agresivo", use_container_width=True):
            # Aggressive preset - prioritizes profit potential
            st.session_state['detection_params'].update({
                'umbral_rentabilidad': 0.1,
                'min_net_profit': 0.05,
                'min_marketcap': 100000,
                'min_volume': 10000,
                'min_token_age': 14,
                'risk_level': "Alto",
                'max_capital_exposure': 50,
                'stop_loss_percentage': 5.0,
                'check_token_security': False,
                'execution_mode': "Testnet"
            })
            st.rerun()
    
    with col4:
        if st.button("🔬 Investigación", use_container_width=True):
            # Research preset - maximum data collection
            st.session_state['detection_params'].update({
                'token_search_limit': 1000,
                'umbral_rentabilidad': 0.01,
                'min_net_profit': 0.0,
                'min_marketcap': 0,
                'min_volume': 0,
                'min_token_age': 0,
                'min_liquidity': 0,
                'risk_level': "Muy Alto",
                'exclude_stablecoins': False,
                'exclude_leveraged': False,
                'exclude_meme_tokens': False,
                'check_token_security': False,
                'limit_results': False,
                'execution_mode': "Simulación"
            })
            st.rerun()
    
    # Navigation buttons
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col3:
        if st.button("Continuar a Obtención de Datos", type="primary", use_container_width=True):
            st.session_state['workflow_stage'] = 'data_fetch'
            st.rerun()

def display_data_fetch_stage(opportunity_service):
    """Fetch and display market data from exchanges."""
    st.header("2. Obtención de Datos de Mercado")
    st.write("Obtenga los símbolos y precios de los pares de trading disponibles en los exchanges configurados.")
    
    # Get parameters from session state
    params = st.session_state.get('detection_params', {})
    token_search_limit = params.get('token_search_limit', 400)
    market_fetch_timeout = params.get('market_fetch_timeout', 30)
    selected_exchanges = params.get('selected_exchanges', ["Binance"])
    
    # Display current configuration
    with st.expander("Configuración Actual", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Límite de Tokens", token_search_limit)
        
        with col2:
            st.metric("Timeout de Fetch (s)", market_fetch_timeout)
        
        with col3:
            st.metric("Exchanges", ", ".join(selected_exchanges))
    
    # Current market status
    st.subheader("Estado del Mercado")
    
    # Mock-up market indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        btc_price = 55000 + np.random.normal(0, 200)
        btc_change = np.random.normal(0, 1.5)
        st.metric("Bitcoin (BTC)", f"${btc_price:.2f}", f"{btc_change:.2f}%")
    
    with col2:
        eth_price = 3200 + np.random.normal(0, 50)
        eth_change = np.random.normal(0, 2)
        st.metric("Ethereum (ETH)", f"${eth_price:.2f}", f"{eth_change:.2f}%")
    
    with col3:
        # Calculate market volatility index (mock)
        volatility = np.random.uniform(10, 40)
        vol_change = np.random.normal(0, 3)
        vol_label = "Baja" if volatility < 20 else "Media" if volatility < 30 else "Alta"
        st.metric(f"Volatilidad ({vol_label})", f"{volatility:.1f}", f"{vol_change:.1f}%")
    
    with col4:
        # Calculate arbitrage opportunities estimate (mock)
        arb_estimate = np.random.randint(5, 50)
        st.metric("Est. Oportunidades", arb_estimate)
    
    # Fetch data button
    fetch_button = st.button(
        "Obtener Datos de Mercado", 
        type="primary",
        key="fetch_data_btn",
        help="Inicia la obtención de datos de mercado desde los exchanges configurados."
    )
    
    if fetch_button:
        with st.spinner(f"Obteniendo datos de mercado desde {', '.join(selected_exchanges)}..."):
            # Mock progress bar to simulate real fetching
            progress_bar = st.progress(0)
            
            # Create tabs for each exchange
            exchange_tabs = st.tabs(selected_exchanges)
            
            # Simulate fetching data from each exchange
            for i, (exchange, tab) in enumerate(zip(selected_exchanges, exchange_tabs)):
                with tab:
                    st.write(f"Conectando a {exchange}...")
                    placeholder = st.empty()
                    
                    # Simulate API calls
                    for j in range(5):
                        time.sleep(0.5)  # Simulate network delay
                        placeholder.write(f"Obteniendo datos de mercado ({j+1}/5)...")
                        progress_value = (i * 5 + j + 1) / (len(selected_exchanges) * 5)
                        progress_bar.progress(progress_value)
            
            # Actually fetch data
            success = opportunity_service.fetch_and_store_market_data(token_search_limit)
            
            if success:
                st.session_state['market_data_fetched'] = True
                st.success(f"✅ Datos de mercado obtenidos correctamente de {', '.join(selected_exchanges)}")
                
                # Show data statistics
                if 'symbols' in st.session_state and 'tickers' in st.session_state:
                    st.subheader("Resumen de Datos Obtenidos")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Total de Símbolos", len(st.session_state['symbols']))
                        
                        if len(st.session_state['symbols']) > 0:
                            st.write("Muestra de Símbolos:")
                            st.code("\n".join(st.session_state['symbols'][:10]))
                    
                    with col2:
                        st.metric("Total de Tickers", len(st.session_state['tickers']))
                        
                        if len(st.session_state['tickers']) > 0:
                            st.write("Muestra de Tickers:")
                            sample_tickers = dict(list(st.session_state['tickers'].items())[:5])
                            st.json(sample_tickers)
                
                # Visualization of symbols by base currency
                if 'symbols' in st.session_state and len(st.session_state['symbols']) > 0:
                    st.subheader("Distribución de Símbolos por Moneda Base")
                    
                    # Count symbols by common base currencies
                    common_bases = ["BTC", "ETH", "USDT", "BNB", "BUSD"]
                    base_counts = {}
                    
                    for base in common_bases:
                        base_counts[base] = len([s for s in st.session_state['symbols'] if s.endswith(base)])
                    
                    # Other category
                    others_count = len(st.session_state['symbols']) - sum(base_counts.values())
                    if others_count > 0:
                        base_counts["Otros"] = others_count
                    
                    # Create dataframe for chart
                    base_df = pd.DataFrame({
                        "Base": list(base_counts.keys()),
                        "Count": list(base_counts.values())
                    })
                    
                    # Display bar chart
                    st.bar_chart(base_df.set_index("Base"))
            else:
                st.error("❌ Error al obtener datos de mercado. Por favor, verifica la conexión a los exchanges.")
    else:
        if st.session_state.get('market_data_fetched', False):
            st.success("✅ Datos de mercado ya obtenidos. Puede proceder a la detección de oportunidades.")
        else:
            st.info("ℹ️ Presione el botón 'Obtener Datos de Mercado' para comenzar.")
    
    # Navigation buttons
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⬅️ Volver a Configuración", use_container_width=True):
            st.session_state['workflow_stage'] = 'config'
            st.rerun()
    
    with col3:
        continue_button = st.button(
            "Continuar a Detección ➡️", 
            type="primary", 
            use_container_width=True,
            disabled=not st.session_state.get('market_data_fetched', False)
        )
        
        if continue_button:
            st.session_state['workflow_stage'] = 'detection'
            st.rerun()

def display_detection_stage(opportunity_service):
    """Run detection and display initial results."""
    st.header("3. Detección de Oportunidades de Arbitraje")
    
    if not st.session_state.get('market_data_fetched', False):
        st.warning("⚠️ No se han obtenido datos de mercado. Por favor, vuelva al paso anterior.")
        
        if st.button("Volver a Obtención de Datos"):
            st.session_state['workflow_stage'] = 'data_fetch'
            st.rerun()
        
        return
    
    # Get parameters from session state
    params = st.session_state.get('detection_params', {})
    
    # Display current configuration for detection
    with st.expander("Configuración de Detección", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Umbral Rentabilidad", f"{params.get('umbral_rentabilidad', 0.5)}%")
        
        with col2:
            st.metric("Capital Inicial", f"${params.get('capital_inicial', 100)}")
        
        with col3:
            st.metric("Fee Promedio", f"{sum(params.get('fees_percentage', [0.1, 0.1, 0.1]))/3:.3f}%")
        
        with col4:
            st.metric("Nivel de Riesgo", params.get('risk_level', 'Moderado'))
    
    # Detection options
    st.subheader("Opciones de Ejecución")
    
    detection_mode = st.radio(
        "Modo de Detección",
        options=["Estándar", "Profunda", "Rápida"],
        horizontal=True,
        help="""
        - Estándar: Equilibrio entre velocidad y exhaustividad
        - Profunda: Más exhaustiva, pero más lenta
        - Rápida: Más rápida, pero menos exhaustiva
        """
    )
    
    # Adjust detection parameters based on mode
    if detection_mode == "Profunda":
        st.info("ℹ️ Modo Profundo: Análisis más exhaustivo, mayor tiempo de procesamiento.")
        depth_factor = 2.0
    elif detection_mode == "Rápida":
        st.warning("⚠️ Modo Rápido: Análisis más ligero, menor tiempo de procesamiento.")
        depth_factor = 0.5
    else:
        depth_factor = 1.0
    
    # Filter visualizations
    st.subheader("Filtros Activos")
    
    filt1, filt2 = st.columns(2)
    
    with filt1:
        active_filters = {
            "Rentabilidad Mínima": f"{params.get('umbral_rentabilidad', 0.5)}%",
            "Market Cap Mínimo": f"${params.get('min_marketcap', 500000):,}",
            "Volumen Mínimo": f"${params.get('min_volume', 50000):,}",
            "Edad Mínima Token": f"{params.get('min_token_age', 30)} días"
        }
        
        # Convert to dataframe for display
        filter_df = pd.DataFrame({"Filtro": list(active_filters.keys()), "Valor": list(active_filters.values())})
        st.dataframe(filter_df, use_container_width=True, hide_index=True)
    
    with filt2:
        # Token exclusions
        excluded = []
        
        if params.get('exclude_stablecoins', False):
            excluded.append("Stablecoins")
        
        if params.get('exclude_leveraged', False):
            excluded.append("Tokens Apalancados")
        
        if params.get('exclude_meme_tokens', False):
            excluded.append("Meme Tokens")
        
        excluded.extend(params.get('excluded_tokens', [])[:5])
        
        if excluded:
            st.write("Exclusiones:")
            for ex in excluded:
                st.caption(f"• {ex}")
        else:
            st.write("Sin exclusiones activas")
    
    # Detection button
    detect_button = st.button(
        "Iniciar Detección de Oportunidades", 
        type="primary",
        key="detect_btn"
    )
    
    if detect_button:
        # Retrieve parameters from session state
        fees = params.get('fees_percentage', [0.1, 0.1, 0.1])
        
        # Run detection with progress indication
        st.subheader("Progreso de la Detección")
        
        with st.status("Proceso de detección en curso...") as status:
            st.write("Inicializando detección de oportunidades...")
            
            # Create progress bar to visualize the detection process
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate multi-phase detection process
            phases = [
                "Filtrado preliminar de tokens",
                "Construcción de grafo de trading",
                "Búsqueda de ciclos triangulares",
                "Cálculo de rentabilidades",
                "Validación de oportunidades",
                "Verificación de liquidez",
                "Clasificación final"
            ]
            
            for i, phase in enumerate(phases):
                progress_value = i / len(phases)
                progress_bar.progress(progress_value)
                status_text.write(f"Fase {i+1}/{len(phases)}: {phase}")
                
                # Simulate work being done
                time.sleep(0.5)
            
            # Perform actual detection
            with st.spinner("Ejecutando detección final..."):
                # Verificar si se debe usar un archivo de caché específico
                use_cache = False
                cache_filepath = None
                
                if st.session_state.get('use_selected_cache', False) and 'selected_cache_filepath' in st.session_state:
                    cache_filepath = st.session_state['selected_cache_filepath']
                    st.info(f"Usando datos de caché: {cache_filepath}")
                    # Resetear el flag para no usar siempre este caché
                    st.session_state['use_selected_cache'] = False
                
                # Llamar al servicio con la opción de caché apropiada
                opportunities = opportunity_service.find_and_store_opportunities(
                    params.get('umbral_rentabilidad', settings.umbral_rentabilidad),
                    params.get('capital_inicial', settings.capital_inicial),
                    fees,
                    use_cache=use_cache,
                    cache_filepath=cache_filepath
                )
                
                # Store opportunities in session state for later use
                st.session_state['opportunities'] = opportunities
                
                # Record detection in history
                detection_record = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "mode": detection_mode,
                    "opportunities_count": len(opportunities) if opportunities else 0,
                    "parameters": {
                        "umbral_rentabilidad": params.get('umbral_rentabilidad'),
                        "min_marketcap": params.get('min_marketcap'),
                        "risk_level": params.get('risk_level')
                    }
                }
                
                if 'detection_history' not in st.session_state:
                    st.session_state['detection_history'] = []
                
                st.session_state['detection_history'].append(detection_record)
            
            # Complete the progress bar
            progress_bar.progress(1.0)
            
            # Update status based on results
            if opportunities and len(opportunities) > 0:
                status.update(label="✅ Detección completada con éxito", state="complete")
                st.success(f"Se encontraron {len(opportunities)} oportunidades de arbitraje triangular.")
            else:
                status.update(label="ℹ️ Detección completada sin resultados", state="complete")
                st.info("No se encontraron oportunidades con los parámetros especificados.")
        
        # Display initial results summary
        if opportunities and len(opportunities) > 0:
            st.subheader("Resumen de Resultados")
            
            # Calculate some statistics
            best_profit = max([opp.get('profit_percentage_net', 0) for opp in opportunities])
            avg_profit = sum([opp.get('profit_percentage_net', 0) for opp in opportunities]) / len(opportunities)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Oportunidades Encontradas", len(opportunities))
            
            with col2:
                st.metric("Mejor Rentabilidad", f"{best_profit:.4f}%")
            
            with col3:
                st.metric("Rentabilidad Media", f"{avg_profit:.4f}%")
            
            # Comprobar si hay oportunidades con rentabilidad positiva
            positive_opps = [opp for opp in opportunities if opp.get('profit_percentage_net', 0) > 0]
            
            if positive_opps:
                # Top 3 opportunities preview
                st.subheader("Top 3 Oportunidades")
                
                # Sort by net profitability and take top 3
                top_opps = sorted(
                    positive_opps, 
                    key=lambda x: x.get('profit_percentage_net', 0), 
                    reverse=True
                )[:3]
                
                top_data = []
                for idx, opp in enumerate(top_opps):
                    top_data.append({
                        "Ranking": idx + 1,
                        "Ciclo": opp.get("cycle", "N/A"),
                        "Rentabilidad": f"{opp.get('profit_percentage_net', 0):.4f}%",
                        "Capital": f"${opp.get('capital_sugerido', 0):.2f}"
                    })
                
                top_df = pd.DataFrame(top_data)
                st.dataframe(top_df, use_container_width=True, hide_index=True)
                
                # Encourage navigation to detailed results
                st.success("Detección completada. ¡Vea los resultados detallados en la siguiente página!")
                
                if st.button("Ver Resultados Detallados", type="primary"):
                    st.session_state['workflow_stage'] = 'results'
                    st.rerun()
            else:
                st.warning("Se encontraron oportunidades, pero ninguna con rentabilidad positiva.")
                
                # Opciones para el usuario cuando no hay resultados positivos
                st.subheader("Opciones Disponibles")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Crear Nueva Detección de Símbolos", use_container_width=True):
                        if 'opportunities' in st.session_state:
                            del st.session_state['opportunities']
                        if 'market_data_fetched' in st.session_state:
                            del st.session_state['market_data_fetched']
                        st.session_state['workflow_stage'] = 'data_fetch'
                        st.rerun()
                
                with col2:
                    # Buscar archivos de caché disponibles
                    from src.core.detectar_oportunidades import list_available_cache_files
                    cache_files = list_available_cache_files()
                    
                    if cache_files:
                        cache_options = {f"{cf['formatted_time']} ({cf['symbols_count']} símbolos)": cf['filepath'] 
                                         for cf in cache_files}
                        
                        selected_cache = st.selectbox(
                            "Seleccionar Log Previo", 
                            options=list(cache_options.keys()),
                            key="cache_selection"
                        )
                        
                        if st.button("📂 Usar Log Previo", use_container_width=True):
                            st.session_state['selected_cache_filepath'] = cache_options[selected_cache]
                            # Reiniciar la detección con el archivo de caché seleccionado
                            if 'opportunities' in st.session_state:
                                del st.session_state['opportunities']
                            st.session_state['use_selected_cache'] = True
                            st.rerun()
                    else:
                        st.info("No hay logs previos disponibles.")
                        if st.button("📂 Verificar Logs", use_container_width=True):
                            st.info("Buscando logs disponibles...")
                            st.rerun()
        else:
            st.warning("No se encontraron oportunidades con los parámetros actuales.")
            
            suggestions = [
                "Reducir el umbral de rentabilidad mínima",
                "Disminuir los requisitos de capitalización de mercado y volumen",
                "Incluir más monedas base en la búsqueda",
                "Desactivar algunas exclusiones de tokens",
                "Aumentar el límite de búsqueda de tokens"
            ]
            
            st.write("Sugerencias para encontrar más oportunidades:")
            for sugg in suggestions:
                st.markdown(f"• {sugg}")
            
            if st.button("Volver a Configuración"):
                st.session_state['workflow_stage'] = 'config'
                st.rerun()
    
    # Show detection history
    if 'detection_history' in st.session_state and st.session_state['detection_history']:
        with st.expander("Historial de Detecciones"):
            history_data = []
            
            for idx, record in enumerate(st.session_state['detection_history']):
                history_data.append({
                    "ID": idx + 1,
                    "Fecha": record["timestamp"],
                    "Modo": record["mode"],
                    "Oportunidades": record["opportunities_count"],
                    "Umbral": f"{record['parameters']['umbral_rentabilidad']}%",
                    "Riesgo": record['parameters']['risk_level']
                })
            
            history_df = pd.DataFrame(history_data)
            st.dataframe(history_df, use_container_width=True, hide_index=True)
    
    # Navigation buttons
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⬅️ Volver a Datos", use_container_width=True):
            st.session_state['workflow_stage'] = 'data_fetch'
            st.rerun()
    
    with col3:
        results_button = st.button(
            "Continuar a Resultados ➡️", 
            type="primary", 
            use_container_width=True,
            disabled=not st.session_state.get('opportunities', [])
        )
        
        if results_button:
            st.session_state['workflow_stage'] = 'results'
            st.rerun()

def display_results_stage(opportunity_service):
    """Display detailed results and options for action."""
    st.header("4. Resultados y Análisis")
    
    if not st.session_state.get('opportunities', []):
        st.warning("⚠️ No se han detectado oportunidades. Por favor, vuelva al paso anterior.")
        
        if st.button("Volver a Detección"):
            st.session_state['workflow_stage'] = 'detection'
            st.rerun()
        
        return
    
    # Get parameters and opportunities
    params = st.session_state.get('detection_params', {})
    opportunities = st.session_state.get('opportunities', [])
    
    # Opportunity filtering and sorting options
    st.subheader("Filtrar y Ordenar Resultados")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_profit_filter = st.slider(
            "Rentabilidad Mínima (%)",
            min_value=0.0,
            max_value=max([opp.get('profit_percentage_net', 0) for opp in opportunities]) + 0.5,
            value=0.0,
            step=0.05
        )
    
    with col2:
        sort_options = [
            "Rentabilidad Neta (desc)",
            "Rentabilidad Bruta (desc)",
            "Capital Sugerido (asc)",
            "Complejidad (asc)"
        ]
        
        sort_by = st.selectbox(
            "Ordenar Por",
            options=sort_options,
            index=0
        )
    
    with col3:
        show_top_n = st.number_input(
            "Mostrar Top",
            min_value=1,
            max_value=len(opportunities),
            value=min(10, len(opportunities)),
            step=1
        )
    
    # Apply filters
    filtered_opps = [opp for opp in opportunities if opp.get('profit_percentage_net', 0) >= min_profit_filter]
    
    # Apply sorting
    if sort_by == "Rentabilidad Neta (desc)":
        filtered_opps = sorted(filtered_opps, key=lambda x: x.get('profit_percentage_net', 0), reverse=True)
    elif sort_by == "Rentabilidad Bruta (desc)":
        filtered_opps = sorted(filtered_opps, key=lambda x: x.get('profit_percentage_gross', 0), reverse=True)
    elif sort_by == "Capital Sugerido (asc)":
        filtered_opps = sorted(filtered_opps, key=lambda x: x.get('capital_sugerido', 0))
    elif sort_by == "Complejidad (asc)":
        # Complexity is determined by number of steps and involved tokens
        filtered_opps = sorted(filtered_opps, key=lambda x: len(x.get('steps', [])))
    
    # Take top N
    filtered_opps = filtered_opps[:show_top_n]
    
    # Results summary metrics
    if filtered_opps:
        st.subheader("Resumen de Oportunidades")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Oportunidades", len(filtered_opps))
        
        with col2:
            best_profit = max([opp.get('profit_percentage_net', 0) for opp in filtered_opps])
            st.metric("Mejor Rentabilidad", f"{best_profit:.4f}%")
        
        with col3:
            avg_profit = sum([opp.get('profit_percentage_net', 0) for opp in filtered_opps]) / len(filtered_opps)
            st.metric("Rentabilidad Media", f"{avg_profit:.4f}%")
        
        with col4:
            total_capital = sum([opp.get('capital_sugerido', 0) for opp in filtered_opps])
            st.metric("Capital Total Sugerido", f"${total_capital:.2f}")
        
        # Detailed results table
        st.subheader("Tabla de Oportunidades")
        
        opportunity_data = []
        for idx, opp in enumerate(filtered_opps):
            opportunity_data.append({
                "ID": opp.get("opportunity_id", f"OPP-{idx+1}"),
                "Ciclo": opp.get("cycle", "N/A"),
                "Rentabilidad Bruta (%)": opp.get("profit_percentage_gross", 0.0),
                "Rentabilidad Neta (%)": opp.get("profit_percentage_net", 0.0),
                "Capital Sugerido": opp.get("capital_sugerido", 0.0),
                "Pasos": len(opp.get("steps", [])),
                "Detalle": opp  # Full data for expander
            })
        
        # Create dataframe for display
        df_opportunities = pd.DataFrame(opportunity_data)
        
        # Display interactive dataframe
        st.dataframe(
            df_opportunities[[
                'ID', 
                'Ciclo', 
                'Rentabilidad Bruta (%)', 
                'Rentabilidad Neta (%)', 
                'Capital Sugerido',
                'Pasos'
            ]],
            use_container_width=True,
            column_config={
                "Rentabilidad Bruta (%)": st.column_config.NumberColumn(
                    format="%.4f %%"
                ),
                "Rentabilidad Neta (%)": st.column_config.NumberColumn(
                    format="%.4f %%"
                ),
                "Capital Sugerido": st.column_config.NumberColumn(
                    format="$%.2f"
                )
            },
            hide_index=True
        )
        
        # Opportunity details in expandable sections
        st.subheader("Detalles de Oportunidades")
        
        for i, opp in enumerate(filtered_opps):
            with st.expander(f"Oportunidad {i+1}: {opp.get('cycle', 'N/A')} • Rentabilidad: {opp.get('profit_percentage_net', 0):.4f}%"):
                # Two columns: left for details, right for visualization
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    # Opportunity metadata
                    st.write("**Información General:**")
                    st.write(f"• **ID:** {opp.get('opportunity_id', 'N/A')}")
                    st.write(f"• **Ciclo:** {opp.get('cycle', 'N/A')}")
                    st.write(f"• **Rentabilidad Bruta:** {opp.get('profit_percentage_gross', 0):.4f}%")
                    st.write(f"• **Rentabilidad Neta:** {opp.get('profit_percentage_net', 0):.4f}%")
                    st.write(f"• **Capital Sugerido:** ${opp.get('capital_sugerido', 0):.2f}")
                    
                    # Display steps in a more readable format
                    steps = opp.get("steps", [])
                    
                    if steps:
                        st.write("**Pasos de Ejecución:**")
                        steps_df = pd.DataFrame(steps)
                        st.dataframe(
                            steps_df,
                            use_container_width=True,
                            hide_index=True
                        )
                
                with col2:
                    # Simple cycle visualization
                    st.write("**Visualización del Ciclo:**")
                    
                    # Draw a simple cycle diagram
                    if 'steps' in opp and opp['steps']:
                        steps = opp['steps']
                        coins = []
                        for step in steps:
                            if 'from_coin' in step:
                                coins.append(step['from_coin'])
                        
                        # Add the last coin to close the cycle
                        if steps and 'to_coin' in steps[-1]:
                            coins.append(steps[-1]['to_coin'])
                        
                        # Visualization placeholder
                        st.code(f"{' -> '.join(coins)}")
                
                # Action buttons for this opportunity
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"Enviar a Webhook", key=f"send_webhook_{i}"):
                        success = send_opportunities_to_webhook([opp], settings.n8n_webhook_oportunidad)
                        if success:
                            st.success(f"Oportunidad enviada a webhook correctamente")
                        else:
                            st.error(f"Error al enviar oportunidad a webhook")
                
                with col2:
                    if st.button(f"Simular Ejecución", key=f"simulate_{i}"):
                        st.info("Simulación iniciada... Esta función no está implementada completamente.")
                
                # Full JSON data - CAMBIADO: Usando pestañas para evitar expanders anidados
                json_tab, _ = st.tabs(["Datos JSON", " "])
                with json_tab:
                    st.json(opp)
        
        # Webhook section
        st.subheader("Enviar a Webhook n8n")
        
        # CAMBIADO: Usando st.container en lugar de st.expander
        webhook_container = st.container()
        webhook_container.write("**Configuración de Webhook:**")
        
        col1, col2 = webhook_container.columns(2)
        
        with col1:
            col1.write(f"**URL:** {settings.n8n_webhook_oportunidad if settings.n8n_webhook_oportunidad else 'No configurado'}")
            col1.write(f"**ID Webhook:** 5b4db952-98a4-4d44-838b-a2df8762eb1c")
        
        with col2:
            col2.write("Para configurar el webhook, edite la variable `N8N_WEBHOOK_OPORTUNIDAD` en el archivo `.env`")
        
        # Button to send all opportunities to webhook
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("Enviar Todas las Oportunidades Filtradas a n8n", type="primary", use_container_width=True):
                with st.spinner("Enviando oportunidades al webhook..."):
                    # Send only filtered opportunities
                    success = send_opportunities_to_webhook(filtered_opps, settings.n8n_webhook_oportunidad)
                    
                    if success:
                        st.success(f"✅ {len(filtered_opps)} oportunidades enviadas correctamente al webhook")
                    else:
                        st.error("❌ Error al enviar las oportunidades al webhook")
        
        # Export options
        st.subheader("Exportar Resultados")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Exportar como JSON", use_container_width=True):
                # Convert to JSON
                json_data = json.dumps([opp for opp in filtered_opps], indent=2)
                
                # Display downloading instructions
                st.code(json_data)
                st.caption("Copie y guarde el JSON anterior para uso futuro.")
        
        with col2:
            if st.button("Exportar como CSV", use_container_width=True):
                # Create a simplified dataframe for export
                export_data = []
                
                for opp in filtered_opps:
                    export_data.append({
                        "ID": opp.get("opportunity_id", ""),
                        "Cycle": opp.get("cycle", ""),
                        "Profit_Gross_Pct": opp.get("profit_percentage_gross", 0),
                        "Profit_Net_Pct": opp.get("profit_percentage_net", 0),
                        "Suggested_Capital": opp.get("capital_sugerido", 0),
                        "Steps_Count": len(opp.get("steps", [])),
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                
                export_df = pd.DataFrame(export_data)
                
                # Display CSV
                csv = export_df.to_csv(index=False)
                st.code(csv)
                st.caption("Copie y guarde el CSV anterior para uso futuro.")
        
        with col3:
            if st.button("Generar Informe", use_container_width=True):
                st.info("Esta función generará un informe detallado con análisis usando Google Gemini. No implementada completamente.")
    else:
        st.warning("No se encontraron oportunidades que cumplan con los filtros especificados.")
    
    # Analytics and insights
    if len(filtered_opps) > 3:
        st.subheader("Análisis e Insights")
        
        # Distribute opportunities by profit range
        profit_ranges = {
            "0-0.1%": 0,
            "0.1-0.25%": 0,
            "0.25-0.5%": 0,
            "0.5-1.0%": 0,
            "1.0-2.0%": 0,
            ">2.0%": 0
        }
        
        for opp in filtered_opps:
            profit = opp.get('profit_percentage_net', 0)
            
            if profit < 0.1:
                profit_ranges["0-0.1%"] += 1
            elif profit < 0.25:
                profit_ranges["0.1-0.25%"] += 1
            elif profit < 0.5:
                profit_ranges["0.25-0.5%"] += 1
            elif profit < 1.0:
                profit_ranges["0.5-1.0%"] += 1
            elif profit < 2.0:
                profit_ranges["1.0-2.0%"] += 1
            else:
                profit_ranges[">2.0%"] += 1
        
        # Create dataframe for visualization
        profit_dist_df = pd.DataFrame({
            "Rango": list(profit_ranges.keys()),
            "Cantidad": list(profit_ranges.values())
        })
        
        # Display as chart
        st.write("**Distribución de Oportunidades por Rango de Rentabilidad**")
        st.bar_chart(profit_dist_df.set_index("Rango"))
        
        # Identify most common base coins
        coin_frequency = {}
        
        for opp in filtered_opps:
            cycle = opp.get("cycle", "")
            
            if cycle:
                coins = [c.strip() for c in cycle.replace("->", "").split() if c.strip()]
                
                for coin in coins:
                    if coin not in coin_frequency:
                        coin_frequency[coin] = 0
                    
                    coin_frequency[coin] += 1
        
        # Get top 5 most frequent coins
        top_coins = sorted(coin_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Create dataframe for visualization
        coin_freq_df = pd.DataFrame({
            "Moneda": [c[0] for c in top_coins],
            "Frecuencia": [c[1] for c in top_coins]
        })
        
        # Display as chart
        st.write("**Monedas Más Frecuentes en las Oportunidades**")
        st.bar_chart(coin_freq_df.set_index("Moneda"))
        
        # Key insights
        st.write("**Insights Clave:**")
        
        # Calculate some metrics
        avg_profit = sum([opp.get('profit_percentage_net', 0) for opp in filtered_opps]) / len(filtered_opps)
        best_base = max(coin_frequency.items(), key=lambda x: x[1])[0] if coin_frequency else "N/A"
        
        st.markdown(f"""
        • La rentabilidad media de las oportunidades encontradas es de **{avg_profit:.4f}%**
        • La moneda más frecuente en las oportunidades es **{best_base}**
        • El **{(profit_ranges[">2.0%"] / len(filtered_opps) * 100):.1f}%** de las oportunidades tiene una rentabilidad superior al 2%
        • El rango de rentabilidad con más oportunidades es **{max(profit_ranges.items(), key=lambda x: x[1])[0]}**
        """)
    
    # Navigation buttons
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⬅️ Volver a Detección", use_container_width=True):
            st.session_state['workflow_stage'] = 'detection'
            st.rerun()
    
    with col3:
        if st.button("Iniciar Nuevo Análisis 🔄", use_container_width=True):
            st.session_state['workflow_stage'] = 'config'
            # Keep history but reset current opportunities
            if 'opportunities' in st.session_state:
                del st.session_state['opportunities']
            if 'market_data_fetched' in st.session_state:
                del st.session_state['market_data_fetched']
            st.rerun()
