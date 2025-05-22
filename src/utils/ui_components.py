"""
Componentes UI reutilizables para el dashboard.

Este módulo implementa componentes UI siguiendo el principio SRP (Single Responsibility Principle)
donde cada componente tiene una única responsabilidad y abstrae detalles de implementación.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta

def display_metric_card(title: str, value: Union[float, int], 
                      delta: Optional[float] = None, 
                      prefix: str = "", suffix: str = "",
                      precision: int = 2,
                      help_text: Optional[str] = None) -> None:
    """
    Muestra una tarjeta de métrica con formato.
    
    Args:
        title: Título de la métrica
        value: Valor de la métrica
        delta: Cambio en la métrica (opcional)
        prefix: Prefijo para el valor (ej: "$")
        suffix: Sufijo para el valor (ej: "%")
        precision: Número de decimales a mostrar
        help_text: Texto de ayuda (tooltip)
    """
    # Formatear valor
    if isinstance(value, (int, float)):
        formatted_value = f"{prefix}{value:.{precision}f}{suffix}"
    else:
        formatted_value = f"{prefix}{value}{suffix}"
    
    # Crear métrica con delta si existe
    if delta is not None:
        formatted_delta = f"{delta:.{precision}f}{suffix}"
        st.metric(
            label=title, 
            value=formatted_value,
            delta=formatted_delta,
            help=help_text
        )
    else:
        st.metric(
            label=title, 
            value=formatted_value,
            help=help_text
        )

def create_data_table(data: pd.DataFrame, 
                     height: Optional[int] = None,
                     highlight_cols: Optional[Dict[str, str]] = None) -> None:
    """
    Crea una tabla de datos con opciones de formato.
    
    Args:
        data: DataFrame con los datos
        height: Altura de la tabla
        highlight_cols: Diccionario de columnas a resaltar con colores
    """
    # Aplicar formato condicional
    if highlight_cols:
        # Copiar dataframe para no modificar el original
        styled_df = data.copy()
        
        # Aplicar estilos a columnas específicas
        for col, color in highlight_cols.items():
            if col in styled_df.columns:
                styled_df[col] = styled_df[col].apply(
                    lambda x: f"<span style='color: {color};'>{x}</span>"
                )
        
        # Mostrar tabla con formato HTML
        html_table = styled_df.to_html(escape=False, index=False)
        
        if height:
            html_table = f"<div style='height: {height}px; overflow-y: auto;'>{html_table}</div>"
        
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        # Mostrar tabla normal
        st.dataframe(data, height=height, use_container_width=True)

def display_status_indicator(status: str, 
                           status_map: Optional[Dict[str, Tuple[str, str]]] = None) -> None:
    """
    Muestra un indicador de estado con código de colores.
    
    Args:
        status: Estado a mostrar
        status_map: Mapeo de estados a (color, descripción)
    """
    # Mapeo predeterminado de estados
    default_map = {
        "OK": ("green", "✅ Operativo"),
        "RUNNING": ("green", "✅ En ejecución"),
        "WARNING": ("orange", "⚠️ Atención requerida"),
        "ERROR": ("red", "❌ Error"),
        "OFFLINE": ("gray", "⭘ Desconectado"),
        "UNKNOWN": ("gray", "❓ Desconocido")
    }
    
    # Usar mapeo personalizado o predeterminado
    status_dict = status_map or default_map
    
    # Obtener color y descripción
    color, description = status_dict.get(
        status.upper(), 
        status_dict.get("UNKNOWN", ("gray", "❓ Desconocido"))
    )
    
    # Mostrar indicador
    st.markdown(
        f"<span style='color: {color}; font-weight: bold;'>{description}</span>",
        unsafe_allow_html=True
    )

def create_performance_chart(data: Dict[str, Any], 
                           title: str = "Rendimiento",
                           show_volume: bool = True) -> go.Figure:
    """
    Crea un gráfico de rendimiento con varias métricas.
    
    Args:
        data: Diccionario con datos de rendimiento
        title: Título del gráfico
        show_volume: Mostrar datos de volumen
        
    Returns:
        go.Figure: Objeto de figura Plotly
    """
    # Verificar datos necesarios
    required_keys = ["dates", "profits", "cumulative_profit"]
    if not all(key in data for key in required_keys):
        # Crear figura vacía si faltan datos
        fig = go.Figure()
        fig.update_layout(
            title=title,
            annotations=[{
                "text": "Datos insuficientes para generar el gráfico",
                "showarrow": False,
                "font": {"size": 14}
            }]
        )
        return fig
    
    # Crear figura base
    fig = go.Figure()
    
    # Añadir gráfico de ganancias diarias
    fig.add_trace(
        go.Bar(
            x=data["dates"],
            y=data["profits"],
            name="Ganancia diaria",
            marker_color="rgba(55, 83, 109, 0.7)",
            hovertemplate="Fecha: %{x}<br>Ganancia: $%{y:.3f}<extra></extra>"
        )
    )
    
    # Añadir gráfico de ganancia acumulada
    fig.add_trace(
        go.Scatter(
            x=data["dates"],
            y=data["cumulative_profit"],
            mode="lines+markers",
            name="Ganancia acumulada",
            marker=dict(size=8, color="green"),
            line=dict(width=2, color="green"),
            hovertemplate="Fecha: %{x}<br>Ganancia acumulada: $%{y:.3f}<extra></extra>",
            yaxis="y2"
        )
    )
    
    # Añadir volumen si está disponible y se solicita
    if "volumes" in data and show_volume:
        fig.add_trace(
            go.Scatter(
                x=data["dates"],
                y=data["volumes"],
                mode="lines",
                name="Volumen operado",
                line=dict(width=1, color="rgba(156, 39, 176, 0.7)"),
                hovertemplate="Fecha: %{x}<br>Volumen: $%{y:.2f}<extra></extra>",
                yaxis="y3"
            )
        )
    
    # Configurar layout
    fig.update_layout(
        title=title,
        xaxis=dict(
            title="Fecha",
            rangeslider=dict(visible=True),
            type="category"
        ),
        yaxis=dict(
            title="Ganancia diaria ($)",
            titlefont=dict(color="rgba(55, 83, 109, 1)"),
            tickfont=dict(color="rgba(55, 83, 109, 1)")
        ),
        yaxis2=dict(
            title="Ganancia acumulada ($)",
            titlefont=dict(color="green"),
            tickfont=dict(color="green"),
            anchor="x",
            overlaying="y",
            side="right"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified"
    )
    
    # Añadir tercer eje y si se muestra volumen
    if "volumes" in data and show_volume:
        fig.update_layout(
            yaxis3=dict(
                title="Volumen ($)",
                titlefont=dict(color="rgba(156, 39, 176, 1)"),
                tickfont=dict(color="rgba(156, 39, 176, 1)"),
                anchor="free",
                overlaying="y",
                side="right",
                position=0.95
            )
        )
    
    return fig

def create_status_dashboard(status_data: Dict[str, Any], 
                          thresholds: Optional[Dict[str, Dict[str, Tuple[float, str]]]] = None) -> None:
    """
    Crea un dashboard de estado del sistema.
    
    Args:
        status_data: Datos de estado del sistema
        thresholds: Umbrales para indicadores
    """
    # Verificar estado general
    general_status = status_data.get("status", "UNKNOWN")
    
    # Mostrar estado general
    st.markdown("#### Estado General del Sistema")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if general_status == "OK":
            st.markdown(
                "<span style='color: green; font-size: 3rem;'>✅</span>",
                unsafe_allow_html=True
            )
        elif general_status == "ERROR":
            st.markdown(
                "<span style='color: red; font-size: 3rem;'>❌</span>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                "<span style='color: orange; font-size: 3rem;'>⚠️</span>",
                unsafe_allow_html=True
            )
    
    with col2:
        st.markdown(f"**Estado:** {general_status}")
        st.markdown(f"**Última actualización:** {status_data.get('timestamp', 'Desconocido')}")
        st.markdown(f"**Uptime:** {status_data.get('uptime', 'Desconocido')}")
    
    # Mostrar métricas de recursos
    st.markdown("#### Uso de Recursos")
    
    col1, col2, col3 = st.columns(3)
    
    # CPU Usage
    with col1:
        cpu_usage = status_data.get("cpu_usage", 0)
        cpu_threshold = thresholds.get("cpu_usage", {}) if thresholds else {}
        
        # Determinar color según umbrales
        color = "green"
        for level, (threshold, level_color) in sorted(cpu_threshold.items(), key=lambda x: x[1][0]):
            if cpu_usage >= threshold:
                color = level_color
        
        # Crear gráfico de gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=cpu_usage,
            title={"text": "CPU"},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, cpu_threshold.get("medium", (70, ""))[0]], "color": "lightgray"},
                    {"range": [cpu_threshold.get("medium", (70, ""))[0], 
                              cpu_threshold.get("high", (90, ""))[0]], "color": "yellow"},
                    {"range": [cpu_threshold.get("high", (90, ""))[0], 100], "color": "red"}
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": cpu_threshold.get("high", (90, ""))[0]
                }
            }
        ))
        
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Memory Usage
    with col2:
        memory_usage = status_data.get("memory_usage", 0)
        memory_threshold = thresholds.get("memory_usage", {}) if thresholds else {}
        
        # Determinar color según umbrales
        color = "green"
        for level, (threshold, level_color) in sorted(memory_threshold.items(), key=lambda x: x[1][0]):
            if memory_usage >= threshold:
                color = level_color
        
        # Crear gráfico de gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=memory_usage,
            title={"text": "RAM"},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, memory_threshold.get("medium", (70, ""))[0]], "color": "lightgray"},
                    {"range": [memory_threshold.get("medium", (70, ""))[0], 
                              memory_threshold.get("high", (90, ""))[0]], "color": "yellow"},
                    {"range": [memory_threshold.get("high", (90, ""))[0], 100], "color": "red"}
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": memory_threshold.get("high", (90, ""))[0]
                }
            }
        ))
        
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Disk Usage
    with col3:
        disk_usage = status_data.get("disk_usage", 0)
        disk_threshold = thresholds.get("disk_usage", {}) if thresholds else {}
        
        # Determinar color según umbrales
        color = "green"
        for level, (threshold, level_color) in sorted(disk_threshold.items(), key=lambda x: x[1][0]):
            if disk_usage >= threshold:
                color = level_color
        
        # Crear gráfico de gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=disk_usage,
            title={"text": "Disco"},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, disk_threshold.get("medium", (70, ""))[0]], "color": "lightgray"},
                    {"range": [disk_threshold.get("medium", (70, ""))[0], 
                              disk_threshold.get("high", (90, ""))[0]], "color": "yellow"},
                    {"range": [disk_threshold.get("high", (90, ""))[0], 100], "color": "red"}
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": disk_threshold.get("high", (90, ""))[0]
                }
            }
        ))
        
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar estado de procesos
    st.markdown("#### Procesos del Sistema")
    
    active_processes = status_data.get("active_processes", {})
    
    # Crear dataframe para mostrar
    processes_data = []
    for process_name, status in active_processes.items():
        processes_data.append({
            "Proceso": process_name.capitalize(),
            "Estado": status,
            "Acción": ""
        })
    
    if processes_data:
        processes_df = pd.DataFrame(processes_data)
        
        # Crear tabla
        col1, col2, col3 = st.columns([3, 2, 2])
        
        for i, row in enumerate(processes_data):
            with col1:
                st.write(f"**{row['Proceso']}**")
            
            with col2:
                if row["Estado"] == "RUNNING":
                    st.markdown("<span style='color: green;'>✅ En ejecución</span>", unsafe_allow_html=True)
                elif row["Estado"] == "DESCONOCIDO":
                    st.markdown("<span style='color: gray;'>❓ Desconocido</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color: red;'>❌ Detenido</span>", unsafe_allow_html=True)
            
            with col3:
                # Botón para reiniciar proceso
                if st.button(f"Reiniciar {row['Proceso']}", key=f"restart_{i}"):
                    st.success(f"Solicitud de reinicio de {row['Proceso']} enviada")
    else:
        st.info("No hay información disponible sobre los procesos")
