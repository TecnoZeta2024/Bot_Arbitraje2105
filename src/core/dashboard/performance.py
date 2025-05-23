"""
Módulo para análisis y visualización del rendimiento del sistema de arbitraje.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.core.dashboard.dependency_injection import get_service_registry
from src.core.dashboard.models import OperationStatus
from src.core.dashboard.services import OperationService, TokenService
from src.utils.ui_components import create_performance_chart, display_metric_card


def display_performance_charts():
    """
    Muestra gráficos y análisis de rendimiento del sistema de arbitraje
    """
    st.title("📊 Análisis de Rendimiento")
    
    # Obtener servicios
    operation_service = get_service_registry().get(OperationService)
    token_service = get_service_registry().get(TokenService)
    
    # Filtros de análisis
    st.markdown("### Filtros de Análisis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        time_period = st.selectbox(
            "Período de Análisis",
            options=["7 días", "30 días", "90 días", "Año en curso", "Todo el historial"],
            index=1
        )
        
        # Calcular fechas según el período seleccionado
        end_date = datetime.now()
        
        if time_period == "7 días":
            start_date = end_date - timedelta(days=7)
        elif time_period == "30 días":
            start_date = end_date - timedelta(days=30)
        elif time_period == "90 días":
            start_date = end_date - timedelta(days=90)
        elif time_period == "Año en curso":
            start_date = datetime(end_date.year, 1, 1)
        else:  # Todo el historial
            start_date = datetime(2020, 1, 1)  # Fecha muy anterior
    
    with col2:
        min_capital = st.number_input(
            "Capital mínimo",
            min_value=0.0,
            value=0.0,
            step=10.0
        )
        
        min_operations = st.number_input(
            "Mínimo de operaciones",
            min_value=1,
            value=5,
            step=1
        )
    
    with col3:
        group_by = st.selectbox(
            "Agrupar por",
            options=["Día", "Semana", "Mes", "Ruta"],
            index=0
        )
        
        chart_type = st.selectbox(
            "Tipo de visualización",
            options=["Líneas", "Barras", "Área", "Mixto"],
            index=3
        )
    
    # Botón para aplicar filtros
    if st.button("Analizar Rendimiento"):
        # Obtener operaciones por rango de fechas
        operations = operation_service.get_operations_by_date_range(
            start_date=start_date,
            end_date=end_date
        )
        
        # Procesar y mostrar resultados
        display_performance_results(
            operations, 
            group_by, 
            chart_type,
            start_date,
            end_date,
            min_capital=min_capital,
            statuses=[OperationStatus.COMPLETADO.value]
        )
    else:
        # Mostrar datos recientes por defecto
        default_end = datetime.now()
        default_start = default_end - timedelta(days=30)
        
        operations = operation_service.get_operations_by_date_range(
            start_date=default_start,
            end_date=default_end
        )
        
        display_performance_results(
            operations, 
            "Día", 
            "Mixto",
            default_start,
            default_end,
            min_capital=0.0,
            statuses=[OperationStatus.COMPLETADO.value]
        )

def display_performance_results(
    operations: List[Any], 
    group_by: str, 
    chart_type: str,
    start_date: datetime,
    end_date: datetime,
    min_capital: float = 0.0,
    statuses: Optional[List[str]] = None
):
    """
    Muestra los resultados del análisis de rendimiento
    
    Args:
        operations: Lista de operaciones a analizar
        group_by: Criterio de agrupación
        chart_type: Tipo de gráfico a mostrar
        start_date: Fecha de inicio del análisis
        end_date: Fecha de fin del análisis
        min_capital: Capital mínimo a filtrar
        statuses: Lista de estados a filtrar
    """
    # Verificar si hay operaciones
    if not operations:
        st.info("No se encontraron operaciones con los filtros seleccionados")
        return
    
    # Calcular métricas generales
    total_operations = len(operations)
    total_profit = sum(op.net_profit for op in operations if op.net_profit is not None)
    avg_roi = sum(op.real_roi for op in operations if op.real_roi is not None) / sum(1 for op in operations if op.real_roi is not None) if operations else 0
    
    max_roi = max(op.real_roi for op in operations if op.real_roi is not None) if operations else 0
    min_roi = min(op.real_roi for op in operations if op.real_roi is not None) if operations else 0
    
    total_capital = sum(op.initial_capital for op in operations if op.initial_capital is not None)
    avg_duration = sum((op.completion_time - op.execution_start_time).total_seconds() 
                   for op in operations 
                   if op.completion_time and op.execution_start_time) / total_operations if total_operations else 0
    
    # Mostrar resumen de rendimiento
    st.markdown("## Resumen de Rendimiento")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        display_metric_card(
            "Operaciones Totales",
            total_operations,
            prefix="",
            suffix="",
            precision=0,
            help_text="Número total de operaciones en el período"
        )
    
    with col2:
        display_metric_card(
            "Ganancia Total",
            total_profit,
            prefix="$",
            precision=3,
            help_text="Ganancia neta total en el período"
        )
    
    with col3:
        display_metric_card(
            "ROI Promedio",
            avg_roi,
            suffix="%",
            precision=3,
            help_text="Rentabilidad promedio por operación"
        )
    
    with col4:
        display_metric_card(
            "Capital Total",
            total_capital,
            prefix="$",
            precision=2,
            help_text="Capital total utilizado en las operaciones"
        )
    
    # Segunda fila de métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        display_metric_card(
            "ROI Máximo",
            max_roi,
            suffix="%",
            precision=3,
            help_text="Rentabilidad máxima obtenida"
        )
    
    with col2:
        display_metric_card(
            "ROI Mínimo",
            min_roi,
            suffix="%",
            precision=3,
            help_text="Rentabilidad mínima obtenida"
        )
    
    with col3:
        display_metric_card(
            "Duración Promedio",
            avg_duration,
            suffix=" s",
            precision=1,
            help_text="Duración promedio de las operaciones"
        )
    
    with col4:
        display_metric_card(
            "Ganancia/Operación",
            total_profit / total_operations if total_operations else 0,
            prefix="$",
            precision=3,
            help_text="Ganancia promedio por operación"
        )
    
    # Convertir a DataFrame para análisis
    operations_data = []
    for op in operations:
        # Fecha formateada según agrupación
        if group_by == "Día":
            date_group = op.execution_start_time.date() if op.execution_start_time else None
        elif group_by == "Semana":
            date_group = op.execution_start_time.date() - timedelta(days=op.execution_start_time.weekday()) if op.execution_start_time else None
        elif group_by == "Mes":
            date_group = datetime(op.execution_start_time.year, op.execution_start_time.month, 1).date() if op.execution_start_time else None
        else:  # Ruta
            date_group = None
        
        # Crear diccionario con datos relevantes
        op_data = {
            "id": op.operation_id,
            "date": op.execution_start_time,
            "date_group": date_group,
            "route": op.route.route if op.route else "Desconocida",
            "initial_capital": op.initial_capital,
            "net_profit": op.net_profit,
            "real_roi": op.real_roi,
            "duration": (op.completion_time - op.execution_start_time).total_seconds() if op.completion_time and op.execution_start_time else None,
            "slippage": op.real_slippage,
            "fees": op.total_fees
        }
        
        operations_data.append(op_data)
    
    # Crear DataFrame
    df = pd.DataFrame(operations_data)
    
    # Verificar datos válidos
    if df.empty or df["date"].isna().all() or df["net_profit"].isna().all():
        st.warning("No hay datos suficientes para el análisis de rendimiento")
        return
    
    # Gráficos según tipo de análisis
    if group_by in ["Día", "Semana", "Mes"]:
        display_time_series_analysis(df, group_by, chart_type)
    else:  # Ruta
        display_route_analysis(df, chart_type)
    
    # Análisis de correlaciones
    display_correlation_analysis(df)
    
    # Análisis de distribución
    display_distribution_analysis(df)

def display_time_series_analysis(df: pd.DataFrame, group_by: str, chart_type: str):
    """
    Muestra análisis de series temporales para rendimiento
    
    Args:
        df: DataFrame con datos de operaciones
        group_by: Tipo de agrupación temporal
        chart_type: Tipo de gráfico a mostrar
    """
    st.markdown("## Análisis Temporal")
    
    # Verificar datos necesarios
    if "date_group" not in df.columns or df["date_group"].isna().all():
        st.warning("No hay datos de fechas disponibles para el análisis temporal")
        return
    
    # Agrupar por período
    grouped = df.groupby("date_group").agg({
        "net_profit": ["sum", "mean", "count"],
        "real_roi": ["mean", "max", "min"],
        "initial_capital": ["sum"],
        "duration": ["mean"],
        "slippage": ["mean"],
        "fees": ["sum"]
    }).reset_index()
    
    # Renombrar columnas
    grouped.columns = [
        "date", 
        "total_profit", 
        "avg_profit", 
        "operations", 
        "avg_roi", 
        "max_roi", 
        "min_roi", 
        "total_capital",
        "avg_duration",
        "avg_slippage",
        "total_fees"
    ]
    
    # Ordenar por fecha
    grouped = grouped.sort_values("date")
    
    # Calcular ganancia acumulada
    grouped["cumulative_profit"] = grouped["total_profit"].cumsum()
    
    # Formatear fechas para visualización
    if group_by == "Día":
        grouped["date_str"] = grouped["date"].apply(lambda x: x.strftime("%d/%m/%Y"))
    elif group_by == "Semana":
        grouped["date_str"] = grouped["date"].apply(lambda x: f"Semana {x.strftime('%U')} - {x.year}")
    else:  # Mes
        grouped["date_str"] = grouped["date"].apply(lambda x: x.strftime("%b %Y"))
    
    # Crear gráfico según tipo
    if chart_type == "Líneas":
        fig = px.line(
            grouped, 
            x="date", 
            y="total_profit",
            title=f"Ganancia por {group_by.lower()}",
            labels={"date": "Fecha", "total_profit": "Ganancia (USDT)"},
            markers=True
        )
    elif chart_type == "Barras":
        fig = px.bar(
            grouped, 
            x="date", 
            y="total_profit",
            title=f"Ganancia por {group_by.lower()}",
            labels={"date": "Fecha", "total_profit": "Ganancia (USDT)"},
            color="avg_roi",
            text="operations"
        )
    elif chart_type == "Área":
        fig = px.area(
            grouped, 
            x="date", 
            y="total_profit",
            title=f"Ganancia por {group_by.lower()}",
            labels={"date": "Fecha", "total_profit": "Ganancia (USDT)"},
            color_discrete_sequence=["rgba(0, 104, 201, 0.7)"]
        )
    else:  # Mixto
        # Crear figura base
        fig = go.Figure()
        
        # Añadir gráfico de barras para ganancia diaria
        fig.add_trace(
            go.Bar(
                x=grouped["date"],
                y=grouped["total_profit"],
                name="Ganancia por período",
                marker_color="rgba(55, 83, 109, 0.7)",
                hovertemplate="Fecha: %{x}<br>Ganancia: $%{y:.3f}<br>Operaciones: %{text}<extra></extra>",
                text=grouped["operations"]
            )
        )
        
        # Añadir gráfico de línea para ganancia acumulada
        fig.add_trace(
            go.Scatter(
                x=grouped["date"],
                y=grouped["cumulative_profit"],
                mode="lines+markers",
                name="Ganancia acumulada",
                marker=dict(size=8, color="green"),
                line=dict(width=2, color="green"),
                hovertemplate="Fecha: %{x}<br>Ganancia acumulada: $%{y:.3f}<extra></extra>",
                yaxis="y2"
            )
        )
        
        # Configurar layout con eje Y secundario
        fig.update_layout(
            title=f"Ganancia por {group_by.lower()} y acumulada",
            xaxis=dict(
                title="Fecha",
                tickformat="%d/%m/%Y" if group_by == "Día" else None,
                type="category" if group_by != "Día" else None
            ),
            yaxis=dict(
                title="Ganancia por período (USDT)",
                titlefont=dict(color="rgba(55, 83, 109, 1)"),
                tickfont=dict(color="rgba(55, 83, 109, 1)")
            ),
            yaxis2=dict(
                title="Ganancia acumulada (USDT)",
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
    
    # Mostrar gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico adicional para ROI
    fig2 = go.Figure()
    
    # Añadir línea de ROI promedio
    fig2.add_trace(
        go.Scatter(
            x=grouped["date"],
            y=grouped["avg_roi"],
            mode="lines+markers",
            name="ROI promedio",
            marker=dict(size=8, color="blue"),
            line=dict(width=2)
        )
    )
    
    # Añadir rangos de ROI (min-max)
    fig2.add_trace(
        go.Scatter(
            x=grouped["date"],
            y=grouped["max_roi"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip"
        )
    )
    
    fig2.add_trace(
        go.Scatter(
            x=grouped["date"],
            y=grouped["min_roi"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(0, 100, 80, 0.2)",
            name="Rango ROI"
        )
    )
    
    # Configurar layout
    fig2.update_layout(
        title=f"ROI promedio por {group_by.lower()}",
        xaxis_title="Fecha",
        yaxis_title="ROI (%)",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode="x unified"
    )
    
    # Mostrar gráfico
    st.plotly_chart(fig2, use_container_width=True)
    
    # Mostrar tabla de datos
    with st.expander("Ver datos detallados"):
        display_df = grouped.copy()
        
        # Formatear columnas para visualización
        display_df["total_profit"] = display_df["total_profit"].apply(lambda x: f"${x:.3f}")
        display_df["avg_profit"] = display_df["avg_profit"].apply(lambda x: f"${x:.3f}")
        display_df["avg_roi"] = display_df["avg_roi"].apply(lambda x: f"{x:.3f}%")
        display_df["max_roi"] = display_df["max_roi"].apply(lambda x: f"{x:.3f}%")
        display_df["min_roi"] = display_df["min_roi"].apply(lambda x: f"{x:.3f}%")
        display_df["total_capital"] = display_df["total_capital"].apply(lambda x: f"${x:.2f}")
        display_df["avg_duration"] = display_df["avg_duration"].apply(lambda x: f"{x:.1f} s")
        display_df["avg_slippage"] = display_df["avg_slippage"].apply(lambda x: f"{x:.3f}%" if x is not None else "N/A")
        display_df["total_fees"] = display_df["total_fees"].apply(lambda x: f"${x:.4f}" if x is not None else "N/A")
        display_df["cumulative_profit"] = display_df["cumulative_profit"].apply(lambda x: f"${x:.3f}")
        
        # Usar date_str como índice
        display_df.set_index("date_str", inplace=True)
        
        # Seleccionar y reordenar columnas
        display_df = display_df[[
            "operations", 
            "total_profit", 
            "avg_profit", 
            "cumulative_profit", 
            "avg_roi", 
            "total_capital",
            "avg_duration",
            "avg_slippage",
            "total_fees"
        ]]
        
        # Renombrar columnas
        display_df.columns = [
            "Operaciones", 
            "Ganancia Total", 
            "Ganancia Promedio", 
            "Ganancia Acumulada", 
            "ROI Promedio", 
            "Capital Total",
            "Duración Promedio",
            "Slippage Promedio",
            "Comisiones Totales"
        ]
        
        st.dataframe(display_df, use_container_width=True)

def display_route_analysis(df: pd.DataFrame, chart_type: str):
    """
    Muestra análisis de rendimiento por ruta
    
    Args:
        df: DataFrame con datos de operaciones
        chart_type: Tipo de gráfico a mostrar
    """
    st.markdown("## Análisis por Ruta")
    
    # Verificar datos necesarios
    if "route" not in df.columns or df["route"].isna().all():
        st.warning("No hay datos de rutas disponibles para el análisis")
        return
    
    # Agrupar por ruta
    grouped = df.groupby("route").agg({
        "net_profit": ["sum", "mean", "count"],
        "real_roi": ["mean", "max", "min", "std"],
        "initial_capital": ["sum", "mean"],
        "duration": ["mean"],
        "slippage": ["mean"],
        "fees": ["sum", "mean"]
    }).reset_index()
    
    # Renombrar columnas
    grouped.columns = [
        "route", 
        "total_profit", 
        "avg_profit", 
        "operations", 
        "avg_roi", 
        "max_roi", 
        "min_roi", 
        "std_roi",
        "total_capital",
        "avg_capital",
        "avg_duration",
        "avg_slippage",
        "total_fees",
        "avg_fees"
    ]
    
    # Ordenar por ganancia total
    grouped = grouped.sort_values("total_profit", ascending=False)
    
    # Limitar a top 15 rutas para visualización
    top_routes = grouped.head(15)
    
    # Crear gráfico según tipo
    if chart_type in ["Barras", "Mixto"]:
        fig = px.bar(
            top_routes, 
            x="route", 
            y="total_profit",
            title="Top 15 Rutas por Ganancia Total",
            labels={"route": "Ruta", "total_profit": "Ganancia (USDT)"},
            color="avg_roi",
            text="operations",
            color_continuous_scale=["red", "yellow", "green"]
        )
    elif chart_type == "Líneas":
        fig = px.line(
            top_routes, 
            x="route", 
            y="total_profit",
            title="Top 15 Rutas por Ganancia Total",
            labels={"route": "Ruta", "total_profit": "Ganancia (USDT)"},
            markers=True
        )
    else:  # Área
        fig = px.area(
            top_routes, 
            x="route", 
            y="total_profit",
            title="Top 15 Rutas por Ganancia Total",
            labels={"route": "Ruta", "total_profit": "Ganancia (USDT)"}
        )
    
    # Configurar layout
    fig.update_layout(
        xaxis_title="Ruta",
        yaxis_title="Ganancia Total (USDT)",
        height=500,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_tickangle=-45
    )
    
    # Mostrar gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico de distribución de ROI por ruta
    fig2 = px.box(
        df[df["route"].isin(top_routes["route"])],
        x="route",
        y="real_roi",
        title="Distribución de ROI por Ruta",
        labels={"route": "Ruta", "real_roi": "ROI (%)"},
        color="route"
    )
    
    # Configurar layout
    fig2.update_layout(
        xaxis_title="Ruta",
        yaxis_title="ROI (%)",
        height=500,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_tickangle=-45,
        showlegend=False
    )
    
    # Mostrar gráfico
    st.plotly_chart(fig2, use_container_width=True)
    
    # Mostrar tabla de datos
    with st.expander("Ver datos detallados de rutas"):
        display_df = grouped.copy()
        
        # Formatear columnas para visualización
        display_df["total_profit"] = display_df["total_profit"].apply(lambda x: f"${x:.3f}")
        display_df["avg_profit"] = display_df["avg_profit"].apply(lambda x: f"${x:.3f}")
        display_df["avg_roi"] = display_df["avg_roi"].apply(lambda x: f"{x:.3f}%")
        display_df["max_roi"] = display_df["max_roi"].apply(lambda x: f"{x:.3f}%")
        display_df["min_roi"] = display_df["min_roi"].apply(lambda x: f"{x:.3f}%")
        display_df["std_roi"] = display_df["std_roi"].apply(lambda x: f"{x:.3f}%")
        display_df["total_capital"] = display_df["total_capital"].apply(lambda x: f"${x:.2f}")
        display_df["avg_capital"] = display_df["avg_capital"].apply(lambda x: f"${x:.2f}")
        display_df["avg_duration"] = display_df["avg_duration"].apply(lambda x: f"{x:.1f} s" if x is not None else "N/A")
        display_df["avg_slippage"] = display_df["avg_slippage"].apply(lambda x: f"{x:.3f}%" if x is not None else "N/A")
        display_df["total_fees"] = display_df["total_fees"].apply(lambda x: f"${x:.4f}" if x is not None else "N/A")
        display_df["avg_fees"] = display_df["avg_fees"].apply(lambda x: f"${x:.4f}" if x is not None else "N/A")
        
        # Seleccionar y reordenar columnas
        display_df = display_df[[
            "route",
            "operations", 
            "total_profit", 
            "avg_profit", 
            "avg_roi", 
            "max_roi",
            "min_roi",
            "std_roi",
            "total_capital",
            "avg_duration",
            "avg_slippage",
            "total_fees"
        ]]
        
        # Renombrar columnas
        display_df.columns = [
            "Ruta",
            "Operaciones", 
            "Ganancia Total", 
            "Ganancia Promedio", 
            "ROI Promedio", 
            "ROI Máximo",
            "ROI Mínimo",
            "Desv. Estándar ROI",
            "Capital Total",
            "Duración Promedio",
            "Slippage Promedio",
            "Comisiones Totales"
        ]
        
        st.dataframe(display_df, use_container_width=True)

def display_correlation_analysis(df: pd.DataFrame):
    """
    Muestra análisis de correlaciones entre variables
    
    Args:
        df: DataFrame con datos de operaciones
    """
    st.markdown("## Análisis de Correlaciones")
    
    # Obtener columnas numéricas relevantes
    numeric_cols = [
        "initial_capital", 
        "net_profit", 
        "real_roi", 
        "duration", 
        "slippage", 
        "fees"
    ]
    
    # Verificar datos suficientes
    valid_df = df[numeric_cols].dropna()
    
    if len(valid_df) < 5:
        st.warning("No hay suficientes datos para el análisis de correlaciones")
        return
    
    # Calcular matriz de correlación
    corr_matrix = valid_df.corr()
    
    # Crear heatmap
    fig = px.imshow(
        corr_matrix,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        aspect="auto",
        title="Matriz de Correlación entre Variables"
    )
    
    # Mejorar layout
    fig.update_layout(
        height=500,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    # Mostrar heatmap
    st.plotly_chart(fig, use_container_width=True)
    
    # Gráficos de dispersión para correlaciones clave
    st.markdown("### Correlaciones Principales")
    
    col1, col2 = st.columns(2)
    
    # Correlación ROI vs Slippage
    with col1:
        if "real_roi" in df.columns and "slippage" in df.columns:
            valid_data = df[df["real_roi"].notna() & df["slippage"].notna()]
            
            if not valid_data.empty:
                fig = px.scatter(
                    valid_data,
                    x="slippage",
                    y="real_roi",
                    title="ROI vs Slippage",
                    labels={
                        "slippage": "Slippage (%)",
                        "real_roi": "ROI (%)"
                    },
                    color="real_roi",
                    size="initial_capital",
                    trendline="ols",
                    trendline_color_override="red",
                    color_continuous_scale=["red", "yellow", "green"],
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Calcular y mostrar correlación
                correlation = valid_data["slippage"].corr(valid_data["real_roi"])
                st.markdown(f"**Correlación Slippage-ROI:** {correlation:.3f}")
            else:
                st.info("Datos insuficientes para análisis ROI vs Slippage")
    
    # Correlación Capital vs Ganancia
    with col2:
        if "initial_capital" in df.columns and "net_profit" in df.columns:
            valid_data = df[df["initial_capital"].notna() & df["net_profit"].notna()]
            
            if not valid_data.empty:
                fig = px.scatter(
                    valid_data,
                    x="initial_capital",
                    y="net_profit",
                    title="Ganancia vs Capital Inicial",
                    labels={
                        "initial_capital": "Capital Inicial (USDT)",
                        "net_profit": "Ganancia (USDT)"
                    },
                    color="real_roi",
                    trendline="ols",
                    trendline_color_override="red",
                    color_continuous_scale=["red", "yellow", "green"],
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Calcular y mostrar correlación
                correlation = valid_data["initial_capital"].corr(valid_data["net_profit"])
                st.markdown(f"**Correlación Capital-Ganancia:** {correlation:.3f}")
            else:
                st.info("Datos insuficientes para análisis Capital vs Ganancia")

def display_distribution_analysis(df: pd.DataFrame):
    """
    Muestra análisis de distribuciones de variables clave
    
    Args:
        df: DataFrame con datos de operaciones
    """
    st.markdown("## Análisis de Distribuciones")
    
    col1, col2 = st.columns(2)
    
    # Distribución de ROI
    with col1:
        if "real_roi" in df.columns and not df["real_roi"].isna().all():
            fig = px.histogram(
                df,
                x="real_roi",
                nbins=20,
                title="Distribución de ROI",
                labels={"real_roi": "ROI (%)"},
                color_discrete_sequence=['#4f46e5'],
                marginal="box"
            )
            
            # Añadir líneas verticales para promedio y mediana
            fig.add_vline(
                x=df["real_roi"].mean(),
                line_dash="dash",
                line_color="red",
                annotation_text=f"Media: {df['real_roi'].mean():.3f}%",
                annotation_position="top right"
            )
            
            fig.add_vline(
                x=df["real_roi"].median(),
                line_dash="dash",
                line_color="green",
                annotation_text=f"Mediana: {df['real_roi'].median():.3f}%",
                annotation_position="top left"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Estadísticas descriptivas
            st.markdown("**Estadísticas de ROI:**")
            roi_stats = df["real_roi"].describe().reset_index()
            roi_stats.columns = ["Estadística", "Valor"]
            roi_stats["Valor"] = roi_stats["Valor"].apply(lambda x: f"{x:.3f}%")
            st.dataframe(roi_stats, use_container_width=True)
    
    # Distribución de Ganancia
    with col2:
        if "net_profit" in df.columns and not df["net_profit"].isna().all():
            fig = px.histogram(
                df,
                x="net_profit",
                nbins=20,
                title="Distribución de Ganancia",
                labels={"net_profit": "Ganancia (USDT)"},
                color_discrete_sequence=['#10b981'],
                marginal="box"
            )
            
            # Añadir líneas verticales para promedio y mediana
            fig.add_vline(
                x=df["net_profit"].mean(),
                line_dash="dash",
                line_color="red",
                annotation_text=f"Media: ${df['net_profit'].mean():.3f}",
                annotation_position="top right"
            )
            
            fig.add_vline(
                x=df["net_profit"].median(),
                line_dash="dash",
                line_color="green",
                annotation_text=f"Mediana: ${df['net_profit'].median():.3f}",
                annotation_position="top left"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Estadísticas descriptivas
            st.markdown("**Estadísticas de Ganancia:**")
            profit_stats = df["net_profit"].describe().reset_index()
            profit_stats.columns = ["Estadística", "Valor"]
            profit_stats["Valor"] = profit_stats["Valor"].apply(lambda x: f"${x:.3f}")
            st.dataframe(profit_stats, use_container_width=True)
    
    # Análisis de slippage y otros factores
    if "slippage" in df.columns and not df["slippage"].isna().all():
        st.markdown("### Análisis de Factores de Impacto")
        
        col1, col2 = st.columns(2)
        
        # Distribución de Slippage
        with col1:
            fig = px.histogram(
                df,
                x="slippage",
                nbins=20,
                title="Distribución de Slippage",
                labels={"slippage": "Slippage (%)"},
                color_discrete_sequence=['#f59e0b'],
                marginal="box"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Distribución de Duración
        with col2:
            if "duration" in df.columns and not df["duration"].isna().all():
                fig = px.histogram(
                    df,
                    x="duration",
                    nbins=20,
                    title="Distribución de Duración",
                    labels={"duration": "Duración (segundos)"},
                    color_discrete_sequence=['#3b82f6'],
                    marginal="box"
                )
                
                st.plotly_chart(fig, use_container_width=True)
