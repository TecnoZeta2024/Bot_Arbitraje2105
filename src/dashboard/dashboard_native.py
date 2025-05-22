"""
Dashboard para Bot de Arbitraje Triangular - Versión con Streamlit Nativo

Esta versión utiliza solo componentes nativos de Streamlit en lugar de MagicUI,
para asegurar compatibilidad y un despliegue más sencillo.
"""

import streamlit as st

# Configuración de la página - DEBE SER LA PRIMERA LLAMADA A STREAMLIT
st.set_page_config(
    page_title="Dashboard | Bot de Arbitraje Triangular",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import time

# Importación de utilidades y clientes de datos
from src.dashboard.supabase_client import (
    get_arbitrage_operations,
    get_performance_metrics,
    get_realtime_opportunities,
    get_system_config,
    update_system_config
)
from src.utils.config import load_config # Import load_config to get default interval

# Aplicar estilos personalizados
def apply_custom_styles():
    st.markdown("""
    <style>
    /* Estilos generales */
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Estilo para tarjetas */
    .card {
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        padding: 1.5rem;
        background-color: #ffffff;
        margin-bottom: 1rem;
    }
    
    /* Modo oscuro */
    @media (prefers-color-scheme: dark) {
        .card {
            background-color: #1E1E1E;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }
    }
    
    /* Badges y etiquetas */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: 500;
    }
    
    .badge-success {
        background-color: #4CAF50;
        color: white;
    }
    
    .badge-warning {
        background-color: #FF9800;
        color: white;
    }
    
    .badge-error {
        background-color: #F44336;
        color: white;
    }
    
    .badge-info {
        background-color: #2196F3;
        color: white;
    }
    
    /* Indicadores de estado */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 6px;
    }
    
    .status-active {
        background-color: #4CAF50;
        box-shadow: 0 0 5px #4CAF50;
    }
    
    .status-warning {
        background-color: #FF9800;
        box-shadow: 0 0 5px #FF9800;
    }
    
    .status-error {
        background-color: #F44336;
        box-shadow: 0 0 5px #F44336;
    }
    </style>
    """, unsafe_allow_html=True)

# Helpers para crear elementos visuales
def create_badge(text, badge_type):
    """Crear un badge HTML con estilo específico"""
    return f'<span class="badge badge-{badge_type}">{text}</span>'

def create_status_indicator(status_type, text=""):
    """Crear un indicador de estado circular con texto opcional"""
    return f'<span class="status-indicator status-{status_type}"></span>{text}'

def create_card(title, content, color=None):
    """Crear un contenedor tipo tarjeta con título y contenido"""
    card_style = f'border-left: 5px solid {color};' if color else ''
    
    return f"""
    <div class="card" style="{card_style}">
        <h3>{title}</h3>
        <div>{content}</div>
    </div>
    """

# Load initial configuration to get default refresh interval
initial_config = load_config()
default_refresh_interval = initial_config.get('INTERVALO_DETECCION', 300) # Use INTERVALO_DETECCION from config

# Variables de sesión para controlar el estado
if 'use_mock_data' not in st.session_state:
    st.session_state.use_mock_data = False

if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = default_refresh_interval # Use default from config

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

if 'operation_details' not in st.session_state:
    st.session_state.operation_details = None

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True

# Función para actualizar datos
def refresh_data():
    st.session_state.last_refresh = datetime.now()
    st.rerun()

# Visualizador de Fecha/Hora de última actualización
def show_last_refresh():
    col1, col2 = st.sidebar.columns([3, 1])
    col1.write(f"Última actualización: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    col2.button("🔄", on_click=refresh_data, help="Actualizar datos")

# Función para activar/desactivar datos simulados
def toggle_mock_data():
    st.session_state.use_mock_data = not st.session_state.use_mock_data
    st.rerun()

# Función para cambiar intervalo de actualización
def set_refresh_interval(seconds):
    st.session_state.refresh_interval = seconds

# Sección de Sidebar para configuración
def render_sidebar():
    with st.sidebar:
        st.title("Bot de Arbitraje Triangular")
        st.markdown("---")
        
        # Navegación
        st.subheader("Navegación")
        selected_tab = st.radio(
            "Sección:",
            ["📊 Monitoreo en Tiempo Real", 
             "📜 Operaciones Históricas", 
             "📈 Análisis de Rendimiento", 
             "⚙️ Configuración"]
        )
        
        st.markdown("---")
        
        # Opciones de datos
        st.subheader("Opciones de Datos")
        mock_status = "✅ Usar Datos Simulados" if st.session_state.use_mock_data else "❌ Usar Datos Reales"
        st.button(mock_status, on_click=toggle_mock_data)
        
        # Intervalo de actualización
        st.subheader("Intervalo de Actualización")
        st.radio(
            "Actualizar cada:",
            [15, 30, 60, 300],
            format_func=lambda x: f"{x} segundos",
            index=2,  # Default 60 seconds
            on_change=lambda: set_refresh_interval(st.session_state.refresh_interval),
            key="refresh_interval_radio"
        )
        
        show_last_refresh()
        
        st.markdown("---")
        
        # Estado del sistema
        st.subheader("Estado del Sistema")
        
        # Crear contenedor para estado del servicio
        with st.container():
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("#### Estado del servicio")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"{create_status_indicator('active')} Detección", unsafe_allow_html=True)
                st.markdown(f"{create_status_indicator('active')} n8n", unsafe_allow_html=True)
                st.markdown(f"{create_status_indicator('active')} Binance", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"{create_status_indicator('active')} Telegram", unsafe_allow_html=True)
                
                if st.session_state.use_mock_data:
                    st.markdown(f"{create_status_indicator('warning')} Supabase (simulado)", unsafe_allow_html=True)
                else:
                    st.markdown(f"{create_status_indicator('active')} Supabase", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.caption("© 2025 Bot de Arbitraje Triangular")
        
        return selected_tab

# Sección de Monitoreo en Tiempo Real
def render_realtime_monitoring():
    st.header("📊 Monitoreo en Tiempo Real")
    
    # Obtener datos
    opportunities = get_realtime_opportunities(use_mock=st.session_state.use_mock_data)
    operations = get_arbitrage_operations(limit=5, use_mock=st.session_state.use_mock_data)
    metrics = get_performance_metrics(use_mock=st.session_state.use_mock_data)
    
    # Tarjetas de métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Tarjeta para Ganancia Total
        with st.container():
            st.markdown(create_card(
                "💵 Ganancia Total", 
                f"<h2>${metrics['ganancia_total']:.2f} USDT</h2><p>En {metrics['operaciones_totales']} operaciones</p>",
                color="#4CAF50"
            ), unsafe_allow_html=True)
    
    with col2:
        # Tarjeta para Rentabilidad
        with st.container():
            st.markdown(create_card(
                "📈 Rentabilidad Prom.", 
                f"<h2>{metrics['rentabilidad_promedio']:.2f}%</h2><p>Éxito: {metrics['tasa_exito']*100:.1f}%</p>",
                color="#1E88E5"
            ), unsafe_allow_html=True)
    
    with col3:
        # Tarjeta para Tiempo Promedio
        with st.container():
            st.markdown(create_card(
                "⏱️ Tiempo Prom.", 
                f"<h2>{metrics['tiempo_promedio']:.1f}s</h2><p>{metrics['operaciones_por_dia']:.1f} ops/día</p>",
                color="#FF9800"
            ), unsafe_allow_html=True)
    
    with col4:
        # Tarjeta para Comisiones
        with st.container():
            st.markdown(create_card(
                "💸 Comisiones", 
                f"<h2>${metrics['comisiones_totales']:.2f} USDT</h2><p>Total pagado</p>",
                color="#F44336"
            ), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Oportunidades en tiempo real y operaciones recientes
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Oportunidades Detectadas")
        
        # Contenedor para oportunidades
        with st.container():
            if not opportunities:
                st.info("No hay oportunidades detectadas recientemente.")
            else:
                for opp in opportunities:
                    # Color según recomendación
                    recomendacion = opp.get('analisis_ia', {}).get('recomendacion', 'PENDIENTE')
                    color = {
                        'PROCEDER': '#4CAF50',
                        'PRECAUCION': '#FF9800',
                        'DESCARTAR': '#F44336',
                        'PENDIENTE': '#2196F3'
                    }.get(recomendacion, '#2196F3')
                    
                    # Crear tarjeta para la oportunidad
                    with st.expander(f"Oportunidad {opp['id']} - {opp['ruta']}"):
                        cols = st.columns([3, 1])
                        
                        with cols[0]:
                            st.markdown(f"**Ruta:** {opp['ruta']}")
                            st.markdown(f"**Rentabilidad:** {opp['rentabilidad_teorica']:.2f}%")
                            
                            # Recomendación IA con badge
                            st.markdown(
                                f"**IA:** {create_badge(recomendacion, 'success' if recomendacion == 'PROCEDER' else 'warning' if recomendacion == 'PRECAUCION' else 'error' if recomendacion == 'DESCARTAR' else 'info')} "
                                f"(Confianza: {opp.get('analisis_ia', {}).get('confianza', 0)}%)",
                                unsafe_allow_html=True
                            )
                            
                            # Mostrar riesgos
                            if opp.get('analisis_ia', {}).get('riesgos_identificados'):
                                st.markdown("**Riesgos:**")
                                for riesgo in opp.get('analisis_ia', {}).get('riesgos_identificados', []):
                                    st.markdown(f"• {riesgo}")
                        
                        with cols[1]:
                            st.button("Detalles", key=f"details_{opp['id']}")
                            if recomendacion in ['PROCEDER', 'PRECAUCION']:
                                st.button("Ejecutar", key=f"execute_{opp['id']}", type="primary")
    
    with col2:
        st.subheader("Operaciones Recientes")
        
        # Contenedor para operaciones recientes
        with st.container():
            if not operations:
                st.info("No hay operaciones recientes.")
            else:
                for op in operations:
                    # Color según estado
                    estado = op.get('estado', 'PENDIENTE')
                    color = {
                        'COMPLETADO': '#4CAF50',
                        'PENDIENTE': '#2196F3',
                        'EJECUTANDO': '#FF9800',
                        'FALLIDO': '#F44336',
                        'CANCELADO': '#9E9E9E'
                    }.get(estado, '#2196F3')
                    
                    # Crear tarjeta para la operación
                    with st.expander(f"Operación {op['operacion_id']} - {estado}"):
                        cols = st.columns([3, 2])
                        
                        with cols[0]:
                            st.markdown(f"**Ruta:** {op['ruta_arbitraje']}")
                            st.markdown(
                                f"**Estado:** {create_badge(estado, 'success' if estado == 'COMPLETADO' else 'warning' if estado == 'EJECUTANDO' else 'error' if estado == 'FALLIDO' else 'info')}",
                                unsafe_allow_html=True
                            )
                            
                            # Mostrar fecha
                            try:
                                fecha = datetime.fromisoformat(op['fecha_inicio_ejecucion'])
                                st.caption(f"Iniciada: {fecha.strftime('%d/%m/%Y %H:%M:%S')}")
                            except:
                                st.caption("Fecha: N/A")
                        
                        with cols[1]:
                            if estado == 'COMPLETADO':
                                ganancia = op.get('ganancia_neta', 0)
                                ganancia_color = "green" if ganancia > 0 else "red"
                                st.markdown(f"**Ganancia:** <span style='color:{ganancia_color}'>${ganancia:.2f} USDT</span>", unsafe_allow_html=True)
                                st.markdown(f"**Rentab:** {op.get('rentabilidad_real', 0):.2f}%")
                            elif estado == 'EJECUTANDO':
                                st.markdown("⏳ **En proceso...**")
                            elif estado == 'FALLIDO':
                                st.markdown("❌ **Error en ejecución**")
                            elif estado == 'CANCELADO':
                                st.markdown("🚫 **Cancelada por usuario**")
                            else:
                                st.markdown("⏳ **Esperando confirmación**")
                                
                            if st.button("Ver detalles", key=f"view_{op['operacion_id']}"):
                                st.session_state.operation_details = op
    
    st.markdown("---")
    
    # Gráfico de actividad reciente (últimas 24h)
    st.subheader("Actividad Reciente (24h)")
    
    # Simular datos de actividad por hora
    hours = list(range(24))
    now = datetime.now()
    hour_labels = [(now - timedelta(hours=h)).strftime("%H:00") for h in hours]
    hour_labels.reverse()  # Más reciente a la derecha
    
    # Generar datos simulados de actividad
    np.random.seed(42)  # Para reproducibilidad
    detections = np.random.randint(5, 15, size=24).tolist()
    executions = np.random.randint(0, 5, size=24).tolist()
    successes = [min(x, e) for e, x in zip(executions, np.random.randint(0, 5, size=24).tolist())]
    
    # Invertir para que más reciente esté a la derecha
    detections.reverse()
    executions.reverse()
    successes.reverse()
    
    # Crear dataframe
    df_activity = pd.DataFrame({
        'hora': hour_labels,
        'Oportunidades Detectadas': detections,
        'Operaciones Ejecutadas': executions,
        'Operaciones Exitosas': successes
    })
    
    # Gráfico con Plotly
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_activity['hora'], y=df_activity['Oportunidades Detectadas'],
        mode='lines+markers', name='Oportunidades', line=dict(color='#4B91F7', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df_activity['hora'], y=df_activity['Operaciones Ejecutadas'],
        mode='lines+markers', name='Ejecutadas', line=dict(color='#FF9800', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df_activity['hora'], y=df_activity['Operaciones Exitosas'],
        mode='lines+markers', name='Exitosas', line=dict(color='#4CAF50', width=2)
    ))
    
    fig.update_layout(
        title='Actividad por Hora',
        xaxis_title='Hora',
        yaxis_title='Cantidad',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400,
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode="x unified",
        template="plotly_dark" if st.session_state.dark_mode else "plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("Los datos de actividad se actualizan automáticamente. Última actualización: " + 
              st.session_state.last_refresh.strftime("%H:%M:%S"))

# Sección de Operaciones Históricas
def render_historical_operations():
    st.header("📜 Operaciones Históricas")
    
    # Filtros
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        estado_filter = st.multiselect(
            "Estado",
            ["COMPLETADO", "FALLIDO", "CANCELADO", "PENDIENTE", "EJECUTANDO"],
            default=["COMPLETADO", "FALLIDO", "CANCELADO"]
        )
    
    with col2:
        date_range = st.date_input(
            "Rango de fechas",
            value=(datetime.now() - timedelta(days=30), datetime.now()),
            max_value=datetime.now()
        )
    
    with col3:
        min_rentabilidad = st.number_input("Rentabilidad mín.", value=0.0, step=0.1)
    
    with col4:
        records_limit = st.selectbox("Mostrar", [10, 25, 50, 100, 200], index=1)
    
    # Obtener datos
    operations = get_arbitrage_operations(limit=records_limit, use_mock=st.session_state.use_mock_data)
    
    # Filtrar datos según selecciones
    filtered_operations = []
    for op in operations:
        # Filtro de estado
        if op.get('estado') not in estado_filter:
            continue
        
        # Filtro de fecha
        try:
            fecha = datetime.fromisoformat(op.get('fecha_inicio_ejecucion', ''))
            if fecha.date() < date_range[0] or fecha.date() > date_range[1]:
                continue
        except:
            # Si hay error con la fecha, incluirlo de todos modos
            pass
        
        # Filtro de rentabilidad
        if op.get('estado') == 'COMPLETADO' and op.get('rentabilidad_real', 0) < min_rentabilidad:
            continue
        
        filtered_operations.append(op)
    
    # Contenedor para resultados
    with st.container():
        if not filtered_operations:
            st.info("No se encontraron operaciones que coincidan con los filtros.")
        else:
            st.write(f"Mostrando {len(filtered_operations)} de {len(operations)} operaciones.")
            
            # Crear una tabla con los datos
            table_data = []
            for op in filtered_operations:
                estado = op.get('estado', 'DESCONOCIDO')
                
                # Formatear fecha
                try:
                    fecha = datetime.fromisoformat(op.get('fecha_inicio_ejecucion', ''))
                    fecha_str = fecha.strftime('%d/%m/%Y %H:%M:%S')
                except:
                    fecha_str = 'N/A'
                
                # Preparar ganancia con color según resultado
                ganancia = op.get('ganancia_neta', 0)
                ganancia_color = "green" if ganancia > 0 else "red" if ganancia < 0 else "gray"
                
                # Añadir a la tabla
                table_data.append({
                    "ID": op.get('operacion_id', 'N/A'),
                    "Fecha": fecha_str,
                    "Ruta": op.get('ruta_arbitraje', 'N/A'),
                    "Estado": estado,
                    "Capital": f"${op.get('capital_inicial', 0):.2f}",
                    "Ganancia": f"${ganancia:.2f}",
                    "Rentabilidad": f"{op.get('rentabilidad_real', 0):.2f}%",
                    "Comisiones": f"${op.get('comisiones_totales', 0):.2f}"
                })
            
            # Mostrar tabla
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, 
                         column_config={
                             "ID": st.column_config.TextColumn("ID"),
                             "Estado": st.column_config.TextColumn("Estado", width="medium"),
                             "Ganancia": st.column_config.TextColumn("Ganancia", width="medium"),
                         })
            
            # Botones de acción para cada operación
            col1, col2, col3 = st.columns(3)
            with col1:
                op_id = st.selectbox("Seleccionar operación para ver detalles", 
                                    options=[op.get('operacion_id', 'N/A') for op in filtered_operations])
            
            with col2:
                if st.button("Ver detalles", key="ver_detalles"):
                    # Buscar la operación seleccionada
                    for op in filtered_operations:
                        if op.get('operacion_id') == op_id:
                            st.session_state.operation_details = op
                            break
    
    st.markdown("---")
    
    # Mostrar detalles de operación si se seleccionó
    if st.session_state.operation_details:
        op = st.session_state.operation_details
        
        with st.container():
            st.subheader(f"Detalles de Operación: {op['operacion_id']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Información General")
                st.markdown(f"**Estado:** {op.get('estado', 'N/A')}")
                st.markdown(f"**Ruta:** {op.get('ruta_arbitraje', 'N/A')}")
                st.markdown(f"**Capital inicial:** ${op.get('capital_inicial', 0):.2f} USDT")
                st.markdown(f"**Fecha inicio:** {op.get('fecha_inicio_ejecucion', 'N/A')}")
                
                if op.get('fecha_completado'):
                    st.markdown(f"**Fecha completado:** {op.get('fecha_completado', 'N/A')}")
                    
                    # Calcular duración
                    try:
                        inicio = datetime.fromisoformat(op.get('fecha_inicio_ejecucion', ''))
                        fin = datetime.fromisoformat(op.get('fecha_completado', ''))
                        duracion = (fin - inicio).total_seconds()
                        st.markdown(f"**Duración:** {duracion:.2f} segundos")
                    except:
                        st.markdown("**Duración:** N/A")
            
            with col2:
                st.markdown("### Resultados")
                if op.get('estado') == 'COMPLETADO':
                    ganancia = op.get('ganancia_neta', 0)
                    rentabilidad = op.get('rentabilidad_real', 0)
                    
                    # Color según resultado
                    ganancia_color = "green" if ganancia > 0 else "red"
                    st.markdown(f"**Ganancia:** <span style='color:{ganancia_color}'>${ganancia:.2f} USDT</span>", unsafe_allow_html=True)
                    st.markdown(f"**Rentab:** {rentabilidad:.2f}%")
                    st.markdown(f"**Comisiones:** ${op.get('comisiones_totales', 0):.2f} USDT")
                    st.markdown(f"**Slippage real:** {op.get('slippage_real', 0):.2f}%")
                elif op.get('estado') == 'FALLIDO':
                    st.error("La operación falló durante la ejecución")
                    st.markdown("**Causa posible:** Slippage excesivo o error de conexión")
                elif op.get('estado') == 'CANCELADO':
                    st.warning("La operación fue cancelada por el usuario")
                else:
                    st.info("La operación está pendiente o en ejecución")
            
            # Pares ejecutados
            st.markdown("### Pares Ejecutados")
            if op.get('pares_ejecutados'):
                # Crear dataframe para pares
                pares_data = []
                for par in op.get('pares_ejecutados', []):
                    pares_data.append({
                        "Paso": par.get('step', 'N/A'),
                        "Símbolo": par.get('symbol', 'N/A'),
                        "Precio": f"${par.get('price', 0):.4f}",
                        "Cantidad": f"{par.get('quantity', 0):.6f}"
                    })
                
                df_pares = pd.DataFrame(pares_data)
                st.dataframe(df_pares, use_container_width=True)
            else:
                st.info("No hay información detallada sobre los pares ejecutados")
            
            # Análisis IA
            if op.get('analisis_ia'):
                st.markdown("### Análisis IA")
                ai_analysis = op.get('analisis_ia', {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    recomendacion = ai_analysis.get('recomendacion', 'N/A')
                    st.markdown(f"**Recomendación:** {recomendacion}")
                    st.markdown(f"**Confianza:** {ai_analysis.get('confianza', 0)}%")
                    st.markdown(f"**Rentabilidad estimada:** {ai_analysis.get('rentabilidad_neta_estimada', 0):.2f}%")
                
                with col2:
                    st.markdown("**Riesgos Identificados**")
                    if ai_analysis.get('riesgos_identificados'):
                        for riesgo in ai_analysis.get('riesgos_identificados', []):
                            st.markdown(f"• {riesgo}")
                    else:
                        st.info("No se identificaron riesgos específicos")
                
                if ai_analysis.get('explicacion'):
                    with st.expander("Ver explicación completa del análisis"):
                        st.write(ai_analysis.get('explicacion', ''))
            
            # Botones de acción
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("Exportar a JSON", key=f"export_{op.get('operacion_id', '')}"):
                    # Convertir a JSON para exportar
                    op_json = json.dumps(op, indent=2)
                    st.download_button(
                        label="Descargar JSON",
                        data=op_json,
                        file_name=f"operacion_{op.get('operacion_id', 'unknown')}.json",
                        mime="application/json"
                    )
            with col2:
                if st.button("Volver a lista", key="back_to_list"):
                    st.session_state.operation_details = None
                    st.rerun()

# Sección de Análisis de Rendimiento
def render_performance_analysis():
    st.header("📈 Análisis de Rendimiento")
    
    # Obtener datos
    operations = get_arbitrage_operations(limit=1000, use_mock=st.session_state.use_mock_data)
    metrics = get_performance_metrics(use_mock=st.session_state.use_mock_data)
    
    # Filtrar operaciones completadas para análisis
    completed_ops = [op for op in operations if op.get('estado') == 'COMPLETADO']
    
    # Periodo de análisis
    col1, col2 = st.columns(2)
    
    with col1:
        period = st.selectbox(
            "Periodo de análisis",
            ["Últimos 7 días", "Últimos 30 días", "Todo el historial"],
            index=1
        )
    
    with col2:
        group_by = st.selectbox(
            "Agrupar por",
            ["Día", "Semana", "Mes", "Ruta"],
            index=0
        )
    
    # Filtrar por periodo seleccionado
    now = datetime.now()
    if period == "Últimos 7 días":
        filter_date = now - timedelta(days=7)
    elif period == "Últimos 30 días":
        filter_date = now - timedelta(days=30)
    else:
        filter_date = now - timedelta(days=365)  # Todo el historial (1 año atrás como máximo)
    
    # Filtrar operaciones por fecha
    filtered_ops = []
    for op in completed_ops:
        try:
            fecha = datetime.fromisoformat(op.get('fecha_inicio_ejecucion', ''))
            if fecha >= filter_date:
                filtered_ops.append(op)
        except:
            # Si hay error con la fecha, incluirlo de todos modos
            pass
    
    # Tarjetas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Tarjeta de operaciones
        with st.container():
            st.markdown(create_card(
                "💰 Operaciones",
                f"<h2>{len(filtered_ops)}</h2><p>{len(filtered_ops)/len(completed_ops)*100:.1f}% del total</p>",
                color="#1E88E5"
            ), unsafe_allow_html=True)
    
    with col2:
        # Tarjeta de ganancia
        ganancia_total = sum(op.get('ganancia_neta', 0) for op in filtered_ops)
        exitosas = len([op for op in filtered_ops if op.get('ganancia_neta', 0) > 0])
        
        with st.container():
            st.markdown(create_card(
                "💵 Ganancia",
                f"<h2>${ganancia_total:.2f}</h2><p>{exitosas}/{len(filtered_ops)} exitosas</p>",
                color="#4CAF50"
            ), unsafe_allow_html=True)
    
    with col3:
        # Tarjeta de rentabilidad
        rentabilidades = [op.get('rentabilidad_real', 0) for op in filtered_ops if op.get('rentabilidad_real') is not None]
        rentabilidad_promedio = sum(rentabilidades) / len(rentabilidades) if rentabilidades else 0
        
        with st.container():
            st.markdown(create_card(
                "📊 Rentabilidad",
                f"<h2>{rentabilidad_promedio:.2f}%</h2><p>Promedio</p>",
                color="#9C27B0"
            ), unsafe_allow_html=True)
    
    with col4:
        # Tarjeta de comisiones
        comisiones_total = sum(op.get('comisiones_totales', 0) for op in filtered_ops)
        porcentaje_ganancia = (comisiones_total / ganancia_total * 100) if ganancia_total > 0 else 0
        
        with st.container():
            st.markdown(create_card(
                "💸 Comisiones",
                f"<h2>${comisiones_total:.2f}</h2><p>{porcentaje_ganancia:.1f}% de ganancia</p>",
                color="#FF9800"
            ), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Crear dataframe para análisis
    df_ops = []
    for op in filtered_ops:
        try:
            fecha = datetime.fromisoformat(op.get('fecha_inicio_ejecucion', ''))
            df_ops.append({
                'fecha': fecha,
                'dia': fecha.strftime('%Y-%m-%d'),
                'semana': fecha.strftime('%Y-%U'),
                'mes': fecha.strftime('%Y-%m'),
                'ruta': op.get('ruta_arbitraje', 'N/A'),
                'ganancia': op.get('ganancia_neta', 0),
                'rentabilidad': op.get('rentabilidad_real', 0),
                'comisiones': op.get('comisiones_totales', 0),
                'slippage': op.get('slippage_real', 0),
                'capital': op.get('capital_inicial', 0),
            })
        except:
            # Ignorar operaciones con problemas de fecha
            pass
    
    df = pd.DataFrame(df_ops)
    
    if df.empty:
        st.warning("No hay suficientes datos para el análisis en el periodo seleccionado.")
    else:
        # Agrupar datos según selección
        if group_by == "Día":
            df_grouped = df.groupby('dia').agg({
                'ganancia': 'sum',
                'rentabilidad': 'mean',
                'comisiones': 'sum',
                'slippage': 'mean',
                'capital': 'mean',
                'fecha': 'count'
            }).reset_index()
            df_grouped = df_grouped.rename(columns={'fecha': 'operaciones'})
            df_grouped['periodo'] = df_grouped['dia']
        elif group_by == "Semana":
            df_grouped = df.groupby('semana').agg({
                'ganancia': 'sum',
                'rentabilidad': 'mean',
                'comisiones': 'sum',
                'slippage': 'mean',
                'capital': 'mean',
                'fecha': 'count'
            }).reset_index()
            df_grouped = df_grouped.rename(columns={'fecha': 'operaciones'})
            df_grouped['periodo'] = df_grouped['semana'].apply(lambda x: f"Semana {x.split('-')[1]}")
        elif group_by == "Mes":
            df_grouped = df.groupby('mes').agg({
                'ganancia': 'sum',
                'rentabilidad': 'mean',
                'comisiones': 'sum',
                'slippage': 'mean',
                'capital': 'mean',
                'fecha': 'count'
            }).reset_index()
            df_grouped = df_grouped.rename(columns={'fecha': 'operaciones'})
            df_grouped['periodo'] = df_grouped['mes'].apply(lambda x: f"{x}")
        else:  # Ruta
            df_grouped = df.groupby('ruta').agg({
                'ganancia': 'sum',
                'rentabilidad': 'mean',
                'comisiones': 'sum',
                'slippage': 'mean',
                'capital': 'mean',
                'fecha': 'count'
            }).reset_index()
            df_grouped = df_grouped.rename(columns={'fecha': 'operaciones', 'ruta': 'periodo'})
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Ganancia por " + group_by.lower())
            
            # Gráfico de barras para ganancia
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=df_grouped['periodo'],
                y=df_grouped['ganancia'],
                marker_color=['green' if x > 0 else 'red' for x in df_grouped['ganancia']],
                text=df_grouped['ganancia'].apply(lambda x: f"${x:.2f}"),
                textposition='auto'
            ))
            
            fig.update_layout(
                title=f'Ganancia Total por {group_by.lower()}',
                xaxis_title=group_by,
                yaxis_title='Ganancia (USDT)',
                height=400,
                margin=dict(l=40, r=40, t=60, b=40),
                hovermode="x unified",
                template="plotly_dark" if st.session_state.dark_mode else "plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Operaciones y Rentabilidad")
            
            # Gráfico combinado de barras y líneas
            fig = go.Figure()
            
            # Barras para número de operaciones
            fig.add_trace(go.Bar(
                x=df_grouped['periodo'],
                y=df_grouped['operaciones'],
                name='Operaciones',
                marker_color='rgba(58, 71, 80, 0.6)',
                yaxis='y'
            ))
            
            # Línea para rentabilidad
            fig.add_trace(go.Scatter(
                x=df_grouped['periodo'],
                y=df_grouped['rentabilidad'],
                name='Rentabilidad',
                marker=dict(color='rgb(255, 165, 0)'),
                mode='lines+markers',
                yaxis='y2'
            ))
            
            # Configurar ejes
            fig.update_layout(
                title=f'Operaciones y Rentabilidad por {group_by.lower()}',
                xaxis_title=group_by,
                yaxis=dict(
                    title='Operaciones',
                    titlefont=dict(color='rgb(58, 71, 80)'),
                    tickfont=dict(color='rgb(58, 71, 80)')
                ),
                yaxis2=dict(
                    title='Rentabilidad (%)',
                    titlefont=dict(color='rgb(255, 165, 0)'),
                    tickfont=dict(color='rgb(255, 165, 0)'),
                    anchor='x',
                    overlaying='y',
                    side='right'
                ),
                height=400,
                margin=dict(l=40, r=40, t=60, b=40),
                hovermode="x unified",
                template="plotly_dark" if st.session_state.dark_mode else "plotly_white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Análisis adicional
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Mejor Desempeño")
            
            # Análisis por ruta
            if group_by != "Ruta":
                st.subheader("Rendimiento por Ruta")
                df_routes = df.groupby('ruta').agg({
                    'ganancia': 'sum',
                    'rentabilidad': 'mean',
                    'comisiones': 'sum',
                    'fecha': 'count'
                }).reset_index()
                df_routes = df_routes.rename(columns={'fecha': 'operaciones'})
                
                # Filtrar por al menos 5 operaciones
                df_routes = df_routes[df_routes['operaciones'] >= 1]
                
                if not df_routes.empty:
                    df_routes = df_routes.sort_values('rentabilidad', ascending=False)
                    
                    # Gráfico de barras para rentabilidad por ruta
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        y=df_routes['ruta'],
                        x=df_routes['rentabilidad'],
                        orientation='h',
                        marker_color='rgba(50, 171, 96, 0.7)',
                        text=df_routes['rentabilidad'].apply(lambda x: f"{x:.2f}%"),
                        textposition='auto'
                    ))
                    
                    fig.update_layout(
                        title='Rentabilidad Promedio por Ruta',
                        xaxis_title='Rentabilidad (%)',
                        yaxis_title='Ruta',
                        height=400,
                        margin=dict(l=40, r=40, t=60, b=40),
                        template="plotly_dark" if st.session_state.dark_mode else "plotly_white"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay suficientes datos para analizar por ruta")
            else:
                # Análisis por hora del día
                st.subheader("Rendimiento por Hora del Día")
                # Extraer hora del día
                df['hora'] = df['fecha'].apply(lambda x: x.hour)
                
                df_hour = df.groupby('hora').agg({
                    'ganancia': 'sum',
                    'rentabilidad': 'mean',
                    'fecha': 'count'
                }).reset_index()
                df_hour = df_hour.rename(columns={'fecha': 'operaciones'})
                
                # Gráfico de barras para rentabilidad por hora
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=df_hour['hora'],
                    y=df_hour['rentabilidad'],
                    marker_color='rgba(50, 171, 96, 0.7)',
                    text=df_hour['rentabilidad'].apply(lambda x: f"{x:.2f}%"),
                    textposition='auto'
                ))
                
                fig.update_layout(
                    title='Rentabilidad Promedio por Hora del Día',
                    xaxis_title='Hora',
                    yaxis_title='Rentabilidad (%)',
                    height=400,
                    margin=dict(l=40, r=40, t=60, b=40),
                    template="plotly_dark" if st.session_state.dark_mode else "plotly_white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Distribución de Resultados")
            
            # Histograma de rentabilidad
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=df['rentabilidad'],
                marker_color='rgba(73, 150, 220, 0.7)',
                nbinsx=20
            ))
            
            fig.update_layout(
                title='Distribución de Rentabilidad',
                xaxis_title='Rentabilidad (%)',
                yaxis_title='Frecuencia',
                height=400,
                margin=dict(l=40, r=40, t=60, b=40),
                template="plotly_dark" if st.session_state.dark_mode else "plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabla resumen
        st.markdown("---")
        
        st.subheader("Resumen Detallado")
        
        # Calcular estadísticas
        stats = {
            "Métrica": ["Operaciones Totales", "Operaciones Exitosas", "Tasa de Éxito", 
                        "Ganancia Total", "Ganancia Promedio", "Rentabilidad Promedio",
                        "Comisiones Totales", "Comisiones Promedio", "Slippage Promedio"],
            "Valor": [
                len(filtered_ops),
                len([op for op in filtered_ops if op.get('ganancia_neta', 0) > 0]),
                f"{len([op for op in filtered_ops if op.get('ganancia_neta', 0) > 0]) / len(filtered_ops) * 100:.1f}%" if filtered_ops else "N/A",
                f"${sum(op.get('ganancia_neta', 0) for op in filtered_ops):.2f}",
                f"${sum(op.get('ganancia_neta', 0) for op in filtered_ops) / len(filtered_ops):.2f}" if filtered_ops else "N/A",
                f"{sum(op.get('rentabilidad_real', 0) for op in filtered_ops) / len(filtered_ops):.2f}%" if filtered_ops else "N/A",
                f"${sum(op.get('comisiones_totales', 0) for op in filtered_ops):.2f}",
                f"${sum(op.get('comisiones_totales', 0) for op in filtered_ops) / len(filtered_ops):.2f}" if filtered_ops else "N/A",
                f"{sum(op.get('slippage_real', 0) for op in filtered_ops) / len(filtered_ops):.2f}%" if filtered_ops else "N/A"
            ]
        }
        
        # Mostrar tabla de estadísticas
        df_stats = pd.DataFrame(stats)
        st.table(df_stats)
        
        # Análisis de Slippage vs Rentabilidad
        st.markdown("---")
        
        st.subheader("Análisis de Slippage vs Rentabilidad")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['slippage'],
            y=df['rentabilidad'],
            mode='markers',
            marker=dict(
                size=8,
                color=df['ganancia'],
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Ganancia")
            ),
            text=df['ruta'],
            hovertemplate='Slippage: %{x:.2f}%<br>Rentabilidad: %{y:.2f}%<br>Ruta: %{text}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Relación entre Slippage y Rentabilidad',
            xaxis_title='Slippage (%)',
            yaxis_title='Rentabilidad (%)',
            height=500,
            margin=dict(l=40, r=40, t=60, b=40),
            template="plotly_dark" if st.session_state.dark_mode else "plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Agregar línea de regresión
        if len(df) > 5:  # Solo si hay suficientes datos
            try:
                z = np.polyfit(df['slippage'], df['rentabilidad'], 1)
                p = np.poly1d(z)
                
                # Crear un nuevo gráfico con la línea de regresión
                fig = go.Figure()
                
                # Datos originales
                fig.add_trace(go.Scatter(
                    x=df['slippage'],
                    y=df['rentabilidad'],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color=df['ganancia'],
                        colorscale='RdYlGn',
                        showscale=True,
                        colorbar=dict(title="Ganancia")
                    ),
                    text=df['ruta'],
                    hovertemplate='Slippage: %{x:.2f}%<br>Rentabilidad: %{y:.2f}%<br>Ruta: %{text}<extra></extra>',
                    name='Operaciones'
                ))
                
                # Línea de regresión
                fig.add_trace(go.Scatter(
                    x=[min(df['slippage']), max(df['slippage'])],
                    y=p([min(df['slippage']), max(df['slippage'])]),
                    mode='lines',
                    line=dict(color='white', width=2, dash='dash'),
                    name='Tendencia',
                    hoverinfo='skip'
                ))
                
                fig.update_layout(
                    title='Relación entre Slippage y Rentabilidad',
                    xaxis_title='Slippage (%)',
                    yaxis_title='Rentabilidad (%)',
                    height=500,
                    margin=dict(l=40, r=40, t=60, b=40),
                    template="plotly_dark" if st.session_state.dark_mode else "plotly_white"
                )
                
                # Actualizar gráfico
                st.plotly_chart(fig, use_container_width=True)
                
                # Mostrar coeficiente de correlación
                corr = df['slippage'].corr(df['rentabilidad'])
                st.write(f"Correlación entre Slippage y Rentabilidad: {corr:.3f}")
                if corr < -0.5:
                    st.success("Hay una fuerte correlación negativa: menor slippage suele resultar en mayor rentabilidad")
                elif corr > 0.5:
                    st.warning("Hay una correlación positiva: mayor slippage se asocia con mayor rentabilidad, posiblemente debido a oportunidades con mayor potencial")
                else:
                    st.info("No hay una correlación fuerte entre slippage y rentabilidad")
            except:
                st.warning("No hay suficientes datos para análisis estadístico")

# Aplicación principal
def main():
    # Aplicar estilos personalizados
    apply_custom_styles()
    
    # Verificar si hay auto-refresh
    if 'last_refresh' in st.session_state:
        time_since_refresh = (datetime.now() - st.session_state.last_refresh).total_seconds()
        if time_since_refresh > st.session_state.refresh_interval:
            refresh_data()
    
    # Renderizar sidebar y obtener pestaña seleccionada
    selected_tab = render_sidebar()
    
    # Renderizar sección correspondiente
    if selected_tab == "📊 Monitoreo en Tiempo Real":
        render_realtime_monitoring()
    elif selected_tab == "📜 Operaciones Históricas":
        render_historical_operations()
    elif selected_tab == "📈 Análisis de Rendimiento":
        render_performance_analysis()
    elif selected_tab == "⚙️ Configuración":
        render_configuration()

if __name__ == "__main__":
    main()
