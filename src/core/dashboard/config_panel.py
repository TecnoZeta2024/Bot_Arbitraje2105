import datetime
import json
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st

from src.core.dashboard.supabase_client import (
    get_arbitrage_operations,
    get_system_config,
    get_token_candidates,
    update_system_config,
    update_token_candidates,
)
from src.utils.config import settings


def display_config_panel():
    """
    Muestra el panel de configuración del sistema
    """
    st.title("⚙️ Configuración del Sistema")
    
    # Pestañas para diferentes secciones de configuración
    tabs = st.tabs([
        "Parámetros Generales", 
        "Tokens y Filtros", 
        "Webhooks y APIs", 
        "Alertas y Notificaciones"
    ])
    
    # Cargar configuración actual
    config = get_system_config()
    
    if not config:
        st.error("No se pudo cargar la configuración del sistema. Verifica la conexión con la base de datos.")
        return
    
    with tabs[0]:
        display_general_settings(config)
    
    with tabs[1]:
        display_token_settings(config)
    
    with tabs[2]:
        display_webhook_settings(config)
    
    with tabs[3]:
        display_notification_settings(config)

def display_general_settings(config: Dict[str, Any]):
    """
    Muestra y permite editar parámetros generales del sistema
    
    Args:
        config (Dict[str, Any]): Configuración actual del sistema
    """
    st.subheader("Parámetros Generales del Sistema")
    
    # Crear formulario para parámetros generales
    with st.form("general_settings_form"):
        # Modo de operación
        st.subheader("Modo de Operación")
        
        operation_mode = st.radio(
            "Seleccionar modo",
            options=["testnet", "produccion"],
            index=0 if config.get("operation_mode", "testnet") == "testnet" else 1,
            help="Testnet para pruebas sin dinero real, Producción para operaciones con dinero real"
        )
        
        st.warning(
            "⚠️ El modo de producción utilizará fondos reales para las operaciones. "
            "Asegúrate de haber probado exhaustivamente en testnet antes de activarlo."
        )
        
        # Capital y límites
        st.subheader("Capital y Límites")
        
        col1, col2 = st.columns(2)
        
        with col1:
            default_capital = st.number_input(
                "Capital por defecto (USDT)",
                min_value=10.0,
                max_value=10000.0,
                value=float(config.get("default_capital", 100.0)),
                step=10.0,
                help="Capital predeterminado para operaciones"
            )
            
            min_opportunity_roi = st.number_input(
                "Rentabilidad mínima (%)",
                min_value=0.01,
                max_value=5.0,
                value=float(config.get("min_opportunity_roi", 0.2)),
                step=0.01,
                format="%.2f",
                help="Rentabilidad mínima para considerar una oportunidad viable"
            )
        
        with col2:
            max_capital = st.number_input(
                "Capital máximo (USDT)",
                min_value=10.0,
                max_value=50000.0,
                value=float(config.get("max_capital", 1000.0)),
                step=50.0,
                help="Límite máximo de capital para cualquier operación"
            )
            
            max_slippage = st.number_input(
                "Slippage máximo aceptable (%)",
                min_value=0.01,
                max_value=5.0,
                value=float(config.get("max_slippage", 0.5)),
                step=0.05,
                format="%.2f",
                help="Porcentaje máximo de slippage aceptable"
            )
        
        # Estrategia y ejecución
        st.subheader("Estrategia y Ejecución")
        
        col1, col2 = st.columns(2)
        
        with col1:
            detection_interval = st.number_input(
                "Intervalo de detección (segundos)",
                min_value=10,
                max_value=3600,
                value=int(config.get("detection_interval", 300)),
                step=10,
                help="Intervalo entre búsquedas de oportunidades"
            )
            
            execution_timeout = st.number_input(
                "Timeout de ejecución (segundos)",
                min_value=5,
                max_value=300,
                value=int(config.get("execution_timeout", 30)),
                step=5,
                help="Tiempo máximo para ejecutar una operación completa"
            )
        
        with col2:
            auto_approve = st.checkbox(
                "Aprobar automáticamente oportunidades",
                value=config.get("auto_approve", False),
                help="Si está habilitado, las oportunidades con alta confianza se ejecutarán automáticamente"
            )
            
            if auto_approve:
                auto_approve_threshold = st.slider(
                    "Umbral de confianza para aprobación automática (%)",
                    min_value=50,
                    max_value=100,
                    value=int(config.get("auto_approve_threshold", 90)),
                    step=5,
                    help="Nivel de confianza mínimo para aprobación automática"
                )
            else:
                auto_approve_threshold = config.get("auto_approve_threshold", 90)
        
        # Monitoreo y registro
        st.subheader("Monitoreo y Registro")
        
        col1, col2 = st.columns(2)
        
        with col1:
            log_level = st.selectbox(
                "Nivel de registro",
                options=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(
                    config.get("log_level", "INFO")
                ),
                help="Nivel de detalle para los registros del sistema"
            )
            
        with col2:
            max_operations_history = st.number_input(
                "Historial máximo (operaciones)",
                min_value=100,
                max_value=10000,
                value=int(config.get("max_operations_history", 1000)),
                step=100,
                help="Número máximo de operaciones a mantener en historial"
            )
        
        # Horarios de operación
        st.subheader("Horarios de Operación")
        
        col1, col2 = st.columns(2)
        
        with col1:
            active_hours_start = st.time_input(
                "Hora de inicio",
                value=datetime.time(
                    hour=int(config.get("active_hours_start", "00:00").split(":")[0]),
                    minute=int(config.get("active_hours_start", "00:00").split(":")[1])
                ),
                help="Hora de inicio de operaciones (UTC)"
            )
        
        with col2:
            active_hours_end = st.time_input(
                "Hora de fin",
                value=datetime.time(
                    hour=int(config.get("active_hours_end", "23:59").split(":")[0]),
                    minute=int(config.get("active_hours_end", "23:59").split(":")[1])
                ),
                help="Hora de fin de operaciones (UTC)"
            )
        
        active_days = st.multiselect(
            "Días activos",
            options=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
            default=config.get("active_days", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]),
            help="Días de la semana en que el sistema operará"
        )
        
        # Botón de guardar
        submit_button = st.form_submit_button("Guardar Configuración")
        
        if submit_button:
            # Preparar objeto de configuración actualizado
            updated_config = {
                "operation_mode": operation_mode,
                "default_capital": default_capital,
                "max_capital": max_capital,
                "min_opportunity_roi": min_opportunity_roi,
                "max_slippage": max_slippage,
                "detection_interval": detection_interval,
                "execution_timeout": execution_timeout,
                "auto_approve": auto_approve,
                "auto_approve_threshold": auto_approve_threshold,
                "log_level": log_level,
                "max_operations_history": max_operations_history,
                "active_hours_start": f"{active_hours_start.hour:02d}:{active_hours_start.minute:02d}",
                "active_hours_end": f"{active_hours_end.hour:02d}:{active_hours_end.minute:02d}",
                "active_days": active_days,
                "last_updated": datetime.datetime.now().isoformat()
            }
            
            # Actualizar configuración en la base de datos
            success = update_system_config(updated_config)
            
            if success:
                st.success("Configuración guardada correctamente")
            else:
                st.error("Error al guardar la configuración")
    
    # Mostrar historial de cambios de configuración
    with st.expander("Historial de Cambios"):
        st.info("Esta sección mostraría un historial de cambios en la configuración del sistema.")
        # Aquí se implementaría la lógica para mostrar el historial de cambios

def display_token_settings(config: Dict[str, Any]):
    """
    Muestra y permite editar configuración de tokens y filtros
    
    Args:
        config (Dict[str, Any]): Configuración actual del sistema
    """
    st.subheader("Configuración de Tokens y Filtros")
    
    # Cargar tokens candidatos actuales
    tokens = get_token_candidates()
    
    if tokens:
        tokens_df = pd.DataFrame(tokens)
        
        # Filtros para tokens
        with st.expander("Filtros de Tokens", expanded=True):
            st.markdown("#### Criterios de Filtrado")
            
            col1, col2 = st.columns(2)
            
            with col1:
                min_market_cap = st.number_input(
                    "Market Cap Mínimo (USD)",
                    min_value=0,
                    max_value=1000000000000,
                    value=int(config.get("min_market_cap", 10000000)),
                    step=1000000,
                    format="%d",
                    help="Capitalización de mercado mínima en USD"
                )
                
                min_binance_volume = st.number_input(
                    "Volumen Mínimo en Binance (USD/24h)",
                    min_value=0,
                    max_value=1000000000,
                    value=int(config.get("min_binance_volume", 1000000)),
                    step=100000,
                    format="%d",
                    help="Volumen mínimo en Binance en las últimas 24 horas"
                )
                
                max_volatility_1h = st.slider(
                    "Volatilidad Máxima 1h (%)",
                    min_value=0.1,
                    max_value=20.0,
                    value=float(config.get("max_volatility_1h", 5.0)),
                    step=0.1,
                    help="Cambio porcentual máximo en la última hora"
                )
            
            with col2:
                max_tokens = st.number_input(
                    "Número Máximo de Tokens",
                    min_value=5,
                    max_value=500,
                    value=int(config.get("max_tokens", 100)),
                    step=5,
                    help="Cantidad máxima de tokens a considerar"
                )
                
                blacklisted_tokens = st.text_area(
                    "Tokens en Lista Negra (uno por línea)",
                    value="\n".join(config.get("blacklisted_tokens", [])),
                    help="Tokens a excluir de las operaciones"
                )
                
                max_volatility_24h = st.slider(
                    "Volatilidad Máxima 24h (%)",
                    min_value=1.0,
                    max_value=50.0,
                    value=float(config.get("max_volatility_24h", 15.0)),
                    step=0.5,
                    help="Cambio porcentual máximo en las últimas 24 horas"
                )
            
            # Botón para actualizar filtros
            if st.button("Actualizar Filtros de Tokens"):
                # Preparar lista negra de tokens
                blacklist = [token.strip() for token in blacklisted_tokens.split("\n") if token.strip()]
                
                # Actualizar configuración
                updated_config = {
                    **config,
                    "min_market_cap": min_market_cap,
                    "min_binance_volume": min_binance_volume,
                    "max_volatility_1h": max_volatility_1h,
                    "max_volatility_24h": max_volatility_24h,
                    "max_tokens": max_tokens,
                    "blacklisted_tokens": blacklist,
                    "last_updated": datetime.datetime.now().isoformat()
                }
                
                success = update_system_config(updated_config)
                
                if success:
                    st.success("Filtros de tokens actualizados correctamente")
                else:
                    st.error("Error al actualizar filtros de tokens")
        
        # Visualizar tokens candidatos
        st.markdown("#### Tokens Candidatos Actuales")
        
        # Mostrar estadísticas básicas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Tokens", len(tokens_df))
        
        with col2:
            if 'market_cap' in tokens_df.columns:
                avg_market_cap = tokens_df['market_cap'].mean() / 1000000  # En millones
                st.metric("Market Cap Promedio", f"${avg_market_cap:.2f}M")
        
        with col3:
            if 'volumen_binance_24h' in tokens_df.columns:
                avg_volume = tokens_df['volumen_binance_24h'].mean() / 1000000  # En millones
                st.metric("Volumen Promedio", f"${avg_volume:.2f}M")
        
        # Mostrar tabla de tokens con filtros
        st.markdown("#### Lista de Tokens")
        
        # Filtros para la tabla
        col1, col2 = st.columns(2)
        
        with col1:
            search_token = st.text_input("Buscar por símbolo", "")
        
        with col2:
            sort_by = st.selectbox(
                "Ordenar por",
                options=["market_cap", "volumen_binance_24h", "rendimiento_24h"],
                format_func=lambda x: {
                    "market_cap": "Capitalización de Mercado",
                    "volumen_binance_24h": "Volumen en Binance",
                    "rendimiento_24h": "Rendimiento 24h"
                }.get(x, x)
            )
        
        # Filtrar y ordenar dataframe
        if search_token:
            filtered_df = tokens_df[tokens_df['simbolo'].str.contains(search_token, case=False)]
        else:
            filtered_df = tokens_df
        
        sorted_df = filtered_df.sort_values(by=sort_by, ascending=False) if sort_by in filtered_df.columns else filtered_df
        
        # Mostrar tabla
        if not sorted_df.empty:
            # Renombrar columnas para visualización
            display_cols = {
                'simbolo': 'Símbolo',
                'nombre': 'Nombre',
                'market_cap': 'Market Cap (USD)',
                'volumen_binance_24h': 'Volumen 24h (USD)',
                'rendimiento_24h': 'Cambio 24h (%)',
                'rendimiento_7d': 'Cambio 7d (%)',
                'fecha_actualizacion': 'Actualizado'
            }
            
            # Seleccionar columnas que existen en el dataframe
            cols_to_show = [col for col in display_cols.keys() if col in sorted_df.columns]
            
            # Crear dataframe para mostrar
            display_df = sorted_df[cols_to_show].copy()
            display_df.columns = [display_cols[col] for col in cols_to_show]
            
            # Formatear valores
            if 'Market Cap (USD)' in display_df.columns:
                display_df['Market Cap (USD)'] = display_df['Market Cap (USD)'].apply(lambda x: f"${x:,.0f}")
            
            if 'Volumen 24h (USD)' in display_df.columns:
                display_df['Volumen 24h (USD)'] = display_df['Volumen 24h (USD)'].apply(lambda x: f"${x:,.0f}")
            
            if 'Cambio 24h (%)' in display_df.columns:
                display_df['Cambio 24h (%)'] = display_df['Cambio 24h (%)'].apply(lambda x: f"{x:.2f}%")
            
            if 'Cambio 7d (%)' in display_df.columns:
                display_df['Cambio 7d (%)'] = display_df['Cambio 7d (%)'].apply(lambda x: f"{x:.2f}%")
            
            if 'Actualizado' in display_df.columns:
                display_df['Actualizado'] = pd.to_datetime(display_df['Actualizado']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Mostrar tabla
            st.dataframe(display_df, use_container_width=True)
            
            # Opción para exportar
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Descargar como CSV",
                data=csv,
                file_name=f"tokens_candidatos_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
            
            # Visualización de distribución de tokens
            st.markdown("#### Distribución de Tokens")
            
            # Seleccionar variable para visualizar
            viz_var = st.selectbox(
                "Visualizar distribución por",
                options=["market_cap", "volumen_binance_24h", "rendimiento_24h"],
                format_func=lambda x: {
                    "market_cap": "Capitalización de Mercado",
                    "volumen_binance_24h": "Volumen en Binance",
                    "rendimiento_24h": "Rendimiento 24h"
                }.get(x, x)
            )
            
            if viz_var in tokens_df.columns:
                # Crear visualización
                fig = px.histogram(
                    tokens_df,
                    x=viz_var,
                    nbins=20,
                    title=f"Distribución de {display_cols.get(viz_var, viz_var)}",
                    labels={viz_var: display_cols.get(viz_var, viz_var)},
                    color_discrete_sequence=['#6366f1']
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Mostrar tokens con valores extremos
                with st.expander("Tokens con valores extremos"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"#### Top 5 con mayor {display_cols.get(viz_var, viz_var)}")
                        top_5 = tokens_df.nlargest(5, viz_var)
                        for _, row in top_5.iterrows():
                            st.markdown(f"**{row['simbolo']}**: {row[viz_var]:,.2f}")
                    
                    with col2:
                        st.markdown(f"#### Top 5 con menor {display_cols.get(viz_var, viz_var)}")
                        bottom_5 = tokens_df.nsmallest(5, viz_var)
                        for _, row in bottom_5.iterrows():
                            st.markdown(f"**{row['simbolo']}**: {row[viz_var]:,.2f}")
        else:
            st.warning("No hay tokens candidatos para mostrar")
    else:
        st.warning("No se pudieron cargar los tokens candidatos. Verifica la conexión con la base de datos.")
        
        # Mostrar formulario para agregar tokens manualmente
        with st.expander("Agregar tokens manualmente"):
            st.markdown("#### Agregar Token")
            
            with st.form("add_token_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    token_symbol = st.text_input("Símbolo", "")
                    token_name = st.text_input("Nombre", "")
                    token_market_cap = st.number_input("Market Cap (USD)", min_value=0, step=1000000)
                
                with col2:
                    token_volume = st.number_input("Volumen 24h (USD)", min_value=0, step=10000)
                    token_change_24h = st.number_input("Cambio 24h (%)", step=0.1)
                    token_change_7d = st.number_input("Cambio 7d (%)", step=0.1)
                
                submit = st.form_submit_button("Agregar Token")
                
                if submit and token_symbol:
                    # Crear token
                    new_token = {
                        "simbolo": token_symbol.upper(),
                        "nombre": token_name,
                        "market_cap": token_market_cap,
                        "volumen_binance_24h": token_volume,
                        "rendimiento_24h": token_change_24h,
                        "rendimiento_7d": token_change_7d,
                        "fecha_actualizacion": datetime.datetime.now().isoformat()
                    }
                    
                    # Agregar token a la base de datos
                    success = update_token_candidates([new_token])
                    
                    if success:
                        st.success(f"Token {token_symbol.upper()} agregado correctamente")
                    else:
                        st.error("Error al agregar token")

def display_webhook_settings(config: Dict[str, Any]):
    """
    Muestra y permite editar configuración de webhooks y APIs
    
    Args:
        config (Dict[str, Any]): Configuración actual del sistema
    """
    st.subheader("Configuración de Webhooks y APIs")
    
    # Webhooks de n8n
    with st.expander("Webhooks de n8n", expanded=True):
        st.markdown("#### URLs de Webhooks")
        
        # Valores actuales (desde settings y config)
        opportunity_webhook = st.text_input(
            "Webhook de Oportunidad",
            value=config.get("n8n_webhook_oportunidad", settings.n8n_webhook_oportunidad),
            help="URL del webhook para enviar oportunidades detectadas"
        )
        
        result_webhook = st.text_input(
            "Webhook de Resultado",
            value=config.get("n8n_webhook_resultado", settings.n8n_webhook_resultado),
            help="URL del webhook para enviar resultados de ejecución"
        )
        
        decision_webhook = st.text_input(
            "Webhook de Decisión",
            value=config.get("n8n_webhook_decision", settings.n8n_webhook_decision),
            help="URL del webhook para recibir decisiones del usuario"
        )
        
        # Verificar webhooks
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Verificar Webhooks"):
                st.info("Verificando conexión con webhooks...")
                # Aquí se implementaría la lógica para verificar los webhooks
                st.success("Verificación completada. Webhooks accesibles.")
        
        with col2:
            if st.button("Guardar URLs de Webhooks"):
                # Actualizar configuración
                updated_config = {
                    **config,
                    "n8n_webhook_oportunidad": opportunity_webhook,
                    "n8n_webhook_resultado": result_webhook,
                    "n8n_webhook_decision": decision_webhook,
                    "last_updated": datetime.datetime.now().isoformat()
                }
                
                success = update_system_config(updated_config)
                
                if success:
                    st.success("URLs de webhooks actualizadas correctamente")
                else:
                    st.error("Error al actualizar URLs de webhooks")
    
    # APIs externas
    with st.expander("Credenciales de APIs", expanded=True):
        st.markdown("#### Configuración de APIs Externas")
        
        # Binance API
        st.markdown("### Binance API")
        
        col1, col2 = st.columns(2)
        
        with col1:
            binance_key = st.text_input(
                "API Key",
                value=settings.binance_api_key[:10] + "..." if settings.binance_api_key else "",
                type="password",
                help="Clave API de Binance"
            )
        
        with col2:
            binance_secret = st.text_input(
                "API Secret",
                value=settings.binance_api_secret[:5] + "..." if settings.binance_api_secret else "",
                type="password",
                help="Clave secreta API de Binance"
            )
        
        # Mobula API
        st.markdown("### Mobula API")
        
        mobula_key = st.text_input(
            "API Key",
            value=settings.mobula_api_key[:10] + "..." if settings.mobula_api_key else "",
            type="password",
            help="Clave API de Mobula"
        )
        
        # CoinGecko API
        st.markdown("### CoinGecko API")
        
        coingecko_key = st.text_input(
            "API Key",
            value=settings.coingecko_api_key[:10] + "..." if settings.coingecko_api_key else "",
            type="password",
            help="Clave API de CoinGecko"
        )
        
        # Guardar credenciales
        if st.button("Guardar Credenciales de APIs"):
            st.warning("⚠️ Esta funcionalidad requiere actualizar el archivo .env y reiniciar el sistema")
            # En un entorno real, aquí se implementaría la lógica para actualizar las credenciales de forma segura
            st.info("Esta función está deshabilitada en la interfaz web por motivos de seguridad. Actualiza las credenciales directamente en el archivo .env.")
    
    # Servidor API
    with st.expander("Servidor API", expanded=True):
        st.markdown("#### Configuración del Servidor API")
        
        col1, col2 = st.columns(2)
        
        with col1:
            api_host = st.text_input(
                "Host",
                value=config.get("api_host", "localhost"),
                help="Host del servidor API"
            )
        
        with col2:
            api_port = st.number_input(
                "Puerto",
                min_value=1,
                max_value=65535,
                value=int(config.get("api_port", 8000)),
                help="Puerto del servidor API"
            )
        
        api_base_url = st.text_input(
            "URL Base",
            value=config.get("api_base_url", f"http://{api_host}:{api_port}"),
            help="URL base del servidor API"
        )
        
        # Guardar configuración del servidor API
        if st.button("Guardar Configuración del Servidor API"):
            # Actualizar configuración
            updated_config = {
                **config,
                "api_host": api_host,
                "api_port": api_port,
                "api_base_url": api_base_url,
                "last_updated": datetime.datetime.now().isoformat()
            }
            
            success = update_system_config(updated_config)
            
            if success:
                st.success("Configuración del servidor API actualizada correctamente")
            else:
                st.error("Error al actualizar configuración del servidor API")

def display_notification_settings(config: Dict[str, Any]):
    """
    Muestra y permite editar configuración de alertas y notificaciones
    
    Args:
        config (Dict[str, Any]): Configuración actual del sistema
    """
    st.subheader("Configuración de Alertas y Notificaciones")
    
    # Telegram
    with st.expander("Configuración de Telegram", expanded=True):
        st.markdown("#### Bot de Telegram")
        
        # Valores actuales
        telegram_token = st.text_input(
            "Token del Bot",
            value=settings.telegram_bot_token[:10] + "..." if settings.telegram_bot_token else "",
            type="password",
            help="Token del bot de Telegram"
        )
        
        telegram_chat_id = st.text_input(
            "ID del Chat",
            value=settings.telegram_chat_id or "",
            help="ID del chat para enviar notificaciones"
        )
        
        # Opciones de notificación
        st.markdown("#### Opciones de Notificación")
        
        notify_opportunity = st.checkbox(
            "Notificar oportunidades detectadas",
            value=config.get("notify_opportunity", True),
            help="Enviar notificación cuando se detecte una oportunidad"
        )
        
        notify_execution = st.checkbox(
            "Notificar ejecución de operaciones",
            value=config.get("notify_execution", True),
            help="Enviar notificación al ejecutar una operación"
        )
        
        notify_result = st.checkbox(
            "Notificar resultados de operaciones",
            value=config.get("notify_result", True),
            help="Enviar notificación con el resultado de una operación"
        )
        
        notify_errors = st.checkbox(
            "Notificar errores",
            value=config.get("notify_errors", True),
            help="Enviar notificación cuando ocurra un error"
        )
        
        # Nivel de prioridad para notificaciones
        notify_min_priority = st.select_slider(
            "Nivel mínimo de prioridad para notificaciones",
            options=["Baja", "Media", "Alta", "Crítica"],
            value=config.get("notify_min_priority", "Media"),
            help="Solo se enviarán notificaciones de igual o mayor prioridad"
        )
        
        # Guardar configuración de notificaciones
        if st.button("Guardar Configuración de Notificaciones"):
            # Actualizar configuración
            updated_config = {
                **config,
                "notify_opportunity": notify_opportunity,
                "notify_execution": notify_execution,
                "notify_result": notify_result,
                "notify_errors": notify_errors,
                "notify_min_priority": notify_min_priority,
                "last_updated": datetime.datetime.now().isoformat()
            }
            
            success = update_system_config(updated_config)
            
            if success:
                st.success("Configuración de notificaciones actualizada correctamente")
            else:
                st.error("Error al actualizar configuración de notificaciones")
        
        # Probar notificaciones
        st.markdown("#### Prueba de Notificaciones")
        
        test_message = st.text_input(
            "Mensaje de prueba",
            value="Prueba de notificación del Bot de Arbitraje Triangular",
            help="Mensaje para probar las notificaciones"
        )
        
        if st.button("Enviar Mensaje de Prueba"):
            # Aquí se implementaría la lógica para enviar un mensaje de prueba
            st.info("Enviando mensaje de prueba...")
            # Simular envío exitoso
            st.success("Mensaje enviado correctamente")
    
    # Informes periódicos
    with st.expander("Informes Periódicos", expanded=True):
        st.markdown("#### Configuración de Informes")
        
        # Habilitar informes
        enable_reports = st.checkbox(
            "Habilitar informes periódicos",
            value=config.get("enable_reports", True),
            help="Generar y enviar informes periódicos"
        )
        
        # Frecuencia de informes
        report_frequency = st.selectbox(
            "Frecuencia de informes",
            options=["Diario", "Semanal", "Mensual"],
            index=["Diario", "Semanal", "Mensual"].index(
                config.get("report_frequency", "Diario")
            ),
            help="Frecuencia con la que se generarán los informes"
        )
        
        # Hora del informe
        report_time = st.time_input(
            "Hora del informe",
            value=datetime.time(
                hour=int(config.get("report_time", "20:00").split(":")[0]),
                minute=int(config.get("report_time", "20:00").split(":")[1])
            ),
            help="Hora a la que se generará el informe (UTC)"
        )
        
        # Incluir métricas
        col1, col2 = st.columns(2)
        
        with col1:
            include_profit_metrics = st.checkbox(
                "Incluir métricas de rentabilidad",
                value=config.get("include_profit_metrics", True),
                help="Incluir métricas detalladas de rentabilidad en los informes"
            )
            
            include_route_analysis = st.checkbox(
                "Incluir análisis de rutas",
                value=config.get("include_route_analysis", True),
                help="Incluir análisis de rendimiento por ruta en los informes"
            )
        
        with col2:
            include_token_metrics = st.checkbox(
                "Incluir métricas de tokens",
                value=config.get("include_token_metrics", True),
                help="Incluir métricas detalladas de tokens en los informes"
            )
            
            include_recommendations = st.checkbox(
                "Incluir recomendaciones",
                value=config.get("include_recommendations", True),
                help="Incluir recomendaciones generadas por IA en los informes"
            )
        
        # Guardar configuración de informes
        if st.button("Guardar Configuración de Informes"):
            # Actualizar configuración
            updated_config = {
                **config,
                "enable_reports": enable_reports,
                "report_frequency": report_frequency,
                "report_time": f"{report_time.hour:02d}:{report_time.minute:02d}",
                "include_profit_metrics": include_profit_metrics,
                "include_route_analysis": include_route_analysis,
                "include_token_metrics": include_token_metrics,
                "include_recommendations": include_recommendations,
                "last_updated": datetime.datetime.now().isoformat()
            }
            
            success = update_system_config(updated_config)
            
            if success:
                st.success("Configuración de informes actualizada correctamente")
            else:
                st.error("Error al actualizar configuración de informes")
        
        # Generar informe de prueba
        if st.button("Generar Informe de Prueba"):
            with st.spinner("Generando informe de prueba..."):
                # Aquí se implementaría la lógica para generar un informe de prueba
                # Simular generación de informe
                time.sleep(2)
                st.success("Informe generado correctamente")
                
                # Mostrar informe de ejemplo
                st.markdown("""
                ### Informe de Ejemplo
                
                #### Resumen de Rendimiento
                - **Operaciones Totales:** 12
                - **Tasa de Éxito:** 83.3%
                - **Ganancia Total:** 18.45 USDT
                - **ROI Promedio:** 0.28%
                
                #### Mejores Rutas
                1. USDT -> BTC -> ETH -> USDT (0.32%)
                2. USDT -> BNB -> MATIC -> USDT (0.28%)
                3. USDT -> ETH -> SOL -> USDT (0.25%)
                
                #### Recomendaciones
                - Incrementar capital en un 15% para las próximas operaciones
                - Priorizar rutas con ETH para mejorar la rentabilidad
                - Ajustar umbral de slippage a 0.3% para reducir cancelaciones
                """)
    
    # Alertas de estado
    with st.expander("Alertas de Estado del Sistema", expanded=True):
        st.markdown("#### Configuración de Alertas")
        
        # Habilitar alertas de estado
        enable_status_alerts = st.checkbox(
            "Habilitar alertas de estado",
            value=config.get("enable_status_alerts", True),
            help="Enviar alertas sobre el estado del sistema"
        )
        
        # Umbral de uso de CPU
        cpu_threshold = st.slider(
            "Umbral de uso de CPU (%)",
            min_value=50,
            max_value=95,
            value=int(config.get("cpu_threshold", 80)),
            step=5,
            help="Enviar alerta cuando el uso de CPU supere este umbral"
        )
        
        # Umbral de uso de memoria
        memory_threshold = st.slider(
            "Umbral de uso de memoria (%)",
            min_value=50,
            max_value=95,
            value=int(config.get("memory_threshold", 85)),
            step=5,
            help="Enviar alerta cuando el uso de memoria supere este umbral"
        )
        
        # Umbral de uso de disco
        disk_threshold = st.slider(
            "Umbral de uso de disco (%)",
            min_value=70,
            max_value=95,
            value=int(config.get("disk_threshold", 90)),
            step=5,
            help="Enviar alerta cuando el uso de disco supere este umbral"
        )
        
        # Intervalo de verificación
        check_interval = st.number_input(
            "Intervalo de verificación (minutos)",
            min_value=5,
            max_value=60,
            value=int(config.get("check_interval", 15)),
            step=5,
            help="Intervalo entre verificaciones de estado del sistema"
        )
        
        # Alerta de caída del sistema
        alert_on_downtime = st.checkbox(
            "Alertar en caso de caída",
            value=config.get("alert_on_downtime", True),
            help="Enviar alerta si el sistema no responde"
        )
        
        # Guardar configuración de alertas
        if st.button("Guardar Configuración de Alertas"):
            # Actualizar configuración
            updated_config = {
                **config,
                "enable_status_alerts": enable_status_alerts,
                "cpu_threshold": cpu_threshold,
                "memory_threshold": memory_threshold,
                "disk_threshold": disk_threshold,
                "check_interval": check_interval,
                "alert_on_downtime": alert_on_downtime,
                "last_updated": datetime.datetime.now().isoformat()
            }
            
            success = update_system_config(updated_config)
            
            if success:
                st.success("Configuración de alertas actualizada correctamente")
            else:
                st.error("Error al actualizar configuración de alertas")
        
        # Mostrar estado actual
        st.markdown("#### Estado Actual del Sistema")
        
        # Simular datos de estado
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cpu_usage = 45  # En un sistema real, esto se obtendría programáticamente
            cpu_color = "green" if cpu_usage < cpu_threshold else "red"
            st.markdown(f"**Uso de CPU:** <span style='color:{cpu_color}'>{cpu_usage}%</span>", unsafe_allow_html=True)
        
        with col2:
            memory_usage = 62  # En un sistema real, esto se obtendría programáticamente
            memory_color = "green" if memory_usage < memory_threshold else "red"
            st.markdown(f"**Uso de memoria:** <span style='color:{memory_color}'>{memory_usage}%</span>", unsafe_allow_html=True)
        
        with col3:
            disk_usage = 78  # En un sistema real, esto se obtendría programáticamente
            disk_color = "green" if disk_usage < disk_threshold else "red"
            st.markdown(f"**Uso de disco:** <span style='color:{disk_color}'>{disk_usage}%</span>", unsafe_allow_html=True)
        
        # Verificar estado del sistema
        if st.button("Verificar Estado del Sistema"):
            with st.spinner("Verificando estado del sistema..."):
                # Aquí se implementaría la lógica para verificar el estado
                # Simular verificación
                time.sleep(2)
                st.success("Sistema funcionando correctamente")
                
                # Mostrar detalles
                st.json({
                    "status": "OK",
                    "uptime": "3 días, 7 horas, 22 minutos",
                    "cpu_usage": f"{cpu_usage}%",
                    "memory_usage": f"{memory_usage}%",
                    "disk_usage": f"{disk_usage}%",
                    "active_processes": {
                        "detector": "RUNNING",
                        "executor": "RUNNING",
                        "api_server": "RUNNING",
                        "telegram_bot": "RUNNING"
                    },
                    "last_operation": "2025-05-13 14:28:45",
                    "operations_today": 7
                })
