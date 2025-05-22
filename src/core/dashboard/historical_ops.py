"""
Módulo para visualización del historial de operaciones.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, Any, List, Optional

from src.core.dashboard.dependency_injection import get_service_registry
from src.core.dashboard.services import OperationService, ConfigService
from src.core.dashboard.models import ArbitrageOperation, OperationStatus

def display_historical_operations():
    """
    Muestra el historial de operaciones del sistema
    """
    st.title("📜 Historial de Operaciones")
    
    # Obtener servicios
    operation_service = get_service_registry().get(OperationService)
    config_service = get_service_registry().get(ConfigService)
    
    # Filtros para historial
    st.markdown("### Filtros de Búsqueda")
    col1, col2, col3 = st.columns(3)
    
    # Rango de fechas
    with col1:
        end_date = st.date_input(
            "Hasta",
            value=datetime.now().date(),
            max_value=datetime.now().date()
        )
        
        days_range = st.slider(
            "Período (días)",
            min_value=1,
            max_value=90,
            value=30
        )
        
        start_date = end_date - timedelta(days=days_range)
    
    # Filtros de estado y ruta
    with col2:
        status_filter = st.multiselect(
            "Estado",
            options=[s.value for s in OperationStatus],
            default=["COMPLETADO", "FALLIDO"]
        )
        
        min_capital = st.number_input(
            "Capital mínimo",
            min_value=0.0,
            value=0.0,
            step=10.0
        )
    
    with col3:
        min_roi = st.number_input(
            "ROI mínimo (%)",
            min_value=-100.0,
            max_value=100.0,
            value=0.0,
            step=0.1
        )
        
        sort_by = st.selectbox(
            "Ordenar por",
            options=[
                "fecha_inicio_ejecucion", 
                "fecha_completado", 
                "real_roi", 
                "net_profit", 
                "initial_capital"
            ],
            format_func=lambda x: {
                "fecha_inicio_ejecucion": "Fecha de inicio",
                "fecha_completado": "Fecha de finalización",
                "real_roi": "Rentabilidad",
                "net_profit": "Ganancia",
                "initial_capital": "Capital"
            }.get(x, x)
        )
        
        ascending = st.checkbox("Orden ascendente", value=False)
    
    # Botón para filtrar
    if st.button("Aplicar Filtros"):
        # Convertir fechas a datetime
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Obtener operaciones por rango de fechas
        operations = operation_service.get_operations_by_date_range(
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        # Procesar y mostrar resultados
        display_operations_results(operations, status_filter, min_capital, min_roi / 100, sort_by, ascending)
    else:
        # Mostrar datos recientes por defecto (últimos 30 días)
        default_end = datetime.now()
        default_start = default_end - timedelta(days=30)
        
        operations = operation_service.get_operations_by_date_range(
            start_date=default_start,
            end_date=default_end
        )
        
        # Aplicar filtros y ordenamiento por defecto
        display_operations_results(operations, ["COMPLETADO", "FALLIDO"], 0.0, 0.0, "fecha_inicio_ejecucion", False)

def display_operations_results(operations: List[ArbitrageOperation], statuses: List[str], min_capital: float, min_roi: float, sort_by: str, ascending: bool):
    """
    Muestra los resultados de operaciones filtradas y ordenadas
    
    Args:
        operations: Lista de operaciones a mostrar (sin filtrar/ordenar inicialmente)
        statuses: Lista de estados a filtrar
        min_capital: Capital mínimo a filtrar
        min_roi: ROI mínimo a filtrar (en decimal)
        sort_by: Campo por el cual ordenar
        ascending: Orden ascendente o descendente
    """
    # Verificar si hay operaciones antes de procesar
    if not operations:
        st.info("No se encontraron operaciones con los filtros seleccionados")
        return
    
    # Preparar datos para visualización
    operations_data = []
    for op in operations:
        # Crear diccionario base con los campos principales
        op_data = {
            "operation_id": op.operation_id,
            "route": op.route.route if op.route else "N/A",
            "initial_capital": op.initial_capital,
            "status": op.status,
            "execution_start_time": op.execution_start_time,
            "completion_time": op.completion_time,
            "net_profit": op.net_profit,
            "real_roi": op.real_roi,
            "execution_duration": (op.completion_time - op.execution_start_time).total_seconds() if op.completion_time and op.execution_start_time else None,
            "slippage": op.slippage,
            "total_commissions": op.total_commissions
        }
        
        # Añadir a la lista
        operations_data.append(op_data)
    
    # Crear DataFrame
    df = pd.DataFrame(operations_data)

    # Aplicar filtros
    if statuses:
        df = df[df['status'].isin(statuses)]
    if min_capital > 0:
        df = df[df['initial_capital'] >= min_capital]
    if min_roi is not None:
         # Ensure 'real_roi' is not None before comparison
        df = df[df['real_roi'].apply(lambda x: x is not None and x >= min_roi)]

    # Aplicar ordenamiento
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=ascending)
    
    # Mostrar resumen (usando el DataFrame filtrado)
    st.markdown("## Resultados")
    st.markdown(f"**{len(df)} operaciones encontradas**")
    
    # Calcular métricas generales (usando el DataFrame filtrado)
    completed_ops_df = df[df["status"] == OperationStatus.COMPLETADO.value]
    total_profit = completed_ops_df["net_profit"].sum() if not completed_ops_df.empty else 0
    avg_roi = completed_ops_df["real_roi"].mean() if not completed_ops_df.empty else 0
    success_operations = len(completed_ops_df)
    success_rate = success_operations / len(df) if not df.empty else 0
    
    # Mostrar métricas en columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Operaciones",
            f"{len(df)}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Ganancia Total",
            f"${total_profit:.3f}",
            delta=None
        )
    
    with col3:
        st.metric(
            "ROI Promedio",
            f"{avg_roi:.3f}%",
            delta=None
        )
    
    with col4:
        st.metric(
            "Tasa de Éxito",
            f"{success_rate * 100:.2f}%",
            delta=None
        )
    
    # Pestañas para diferentes vistas
    tabs = st.tabs([
        "Tabla de Operaciones", 
        "Gráfico de Tendencias", 
        "Distribución de Resultados", 
        "Análisis de Rutas",
        "Informes IA"
    ])
    
    # Pestaña 1: Tabla de Operaciones
    with tabs[0]:
        st.markdown("### Tabla Detallada de Operaciones")
        
        # Formatear dataframe para visualización
        display_df = df.copy()
        
        # Renombrar columnas
        display_df.columns = [
            "ID Operación",
            "Ruta",
            "Capital Inicial",
            "Estado",
            "Inicio",
            "Finalización",
            "Ganancia Neta",
            "ROI (%)",
            "Duración (s)",
            "Slippage (%)",
            "Comisiones"
        ]
        
        # Formatear valores
        display_df["Capital Inicial"] = display_df["Capital Inicial"].apply(lambda x: f"${x:.2f}" if x is not None else "N/A")
        display_df["Ganancia Neta"] = display_df["Ganancia Neta"].apply(lambda x: f"${x:.3f}" if x is not None else "N/A")
        display_df["ROI (%)"] = display_df["ROI (%)"].apply(lambda x: f"{x:.3f}%" if x is not None else "N/A")
        display_df["Slippage (%)"] = display_df["Slippage (%)"].apply(lambda x: f"{x:.3f}%" if x is not None else "N/A")
        display_df["Comisiones"] = display_df["Comisiones"].apply(lambda x: f"${x:.4f}" if x is not None else "N/A")
        
        # Formatear fechas
        display_df["Inicio"] = display_df["Inicio"].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if x is not None else "N/A")
        display_df["Finalización"] = display_df["Finalización"].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if x is not None else "N/A")
        
        # Mostrar tabla con estilo
        st.dataframe(
            display_df,
            use_container_width=True,
            height=500
        )
        
        # Exportar a CSV
        st.download_button(
            label="Descargar como CSV",
            data=display_df.to_csv(index=False).encode('utf-8'),
            file_name=f'operaciones_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mime='text/csv'
        )
    
    # Pestaña 2: Gráfico de Tendencias
    with tabs[1]:
        st.markdown("### Tendencias de Rentabilidad")
        
        # Preparar datos para gráfico
        trend_df = df.copy()
        trend_df = trend_df.sort_values(by="execution_start_time")
        
        # Filtrar operaciones completadas con datos válidos
        trend_df = trend_df[
            (trend_df["status"] == OperationStatus.COMPLETADO.value) & 
            (trend_df["real_roi"].notna()) & 
            (trend_df["execution_start_time"].notna())
        ]
        
        if not trend_df.empty:
            # Crear gráfico de líneas para ROI
            fig = px.line(
                trend_df,
                x="execution_start_time",
                y="real_roi",
                title="Tendencia de ROI en el Tiempo",
                labels={
                    "execution_start_time": "Fecha",
                    "real_roi": "ROI (%)"
                },
                color_discrete_sequence=['#4f46e5']
            )
            
            # Añadir línea de promedio
            fig.add_hline(
                y=trend_df["real_roi"].mean(),
                line_dash="dash",
                line_color="red",
                annotation_text=f"Promedio: {trend_df['real_roi'].mean():.3f}%",
                annotation_position="bottom right"
            )
            
            # Mejorar layout
            fig.update_layout(
                xaxis_title="Fecha de Operación",
                yaxis_title="ROI (%)",
                height=500,
                margin=dict(l=20, r=20, t=40, b=20),
                hovermode="x unified"
            )
            
            # Mostrar gráfico
            st.plotly_chart(fig, use_container_width=True)
            
            # Crear gráfico de barras para ganancias acumuladas
            trend_df["cumulative_profit"] = trend_df["net_profit"].cumsum()
            
            fig2 = px.bar(
                trend_df,
                x="execution_start_time",
                y="net_profit",
                title="Ganancias por Operación y Acumuladas",
                labels={
                    "execution_start_time": "Fecha",
                    "net_profit": "Ganancia (USDT)"
                },
                color="net_profit",
                color_continuous_scale=["red", "yellow", "green"],
                range_color=[-trend_df["net_profit"].abs().max(), trend_df["net_profit"].abs().max()]
            )
            
            # Añadir línea de ganancia acumulada
            fig2.add_trace(
                go.Scatter(
                    x=trend_df["execution_start_time"],
                    y="cumulative_profit",
                    mode='lines',
                    name='Ganancia Acumulada',
                    line=dict(color='navy', width=3)
                )
            )
            
            # Mejorar layout
            fig2.update_layout(
                xaxis_title="Fecha de Operación",
                yaxis_title="Ganancia (USDT)",
                height=500,
                margin=dict(l=20, r=20, t=40, b=20),
                hovermode="x unified"
            )
            
            # Mostrar gráfico
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No hay suficientes datos para mostrar tendencias")
    
    # Pestaña 3: Distribución de Resultados
    with tabs[2]:
        st.markdown("### Distribución de Resultados")
        
        # Filtrar operaciones completadas
        completed_df = df[df["status"] == OperationStatus.COMPLETADO.value].copy()
        
        if not completed_df.empty:
            # Crear pestañas para diferentes distribuciones
            dist_tabs = st.tabs([
                "Distribución de ROI", 
                "Distribución por Estado", 
                "Correlación ROI vs Slippage"
            ])
            
            # Sub-pestaña 1: Distribución de ROI
            with dist_tabs[0]:
                # Histograma de ROI
                fig = px.histogram(
                    completed_df,
                    x="real_roi",
                    nbins=20,
                    title="Distribución de ROI",
                    labels={"real_roi": "ROI (%)"},
                    color_discrete_sequence=['#4f46e5']
                )
                
                # Añadir líneas verticales para promedio y mediana
                fig.add_vline(
                    x=completed_df["real_roi"].mean(),
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Media: {completed_df['real_roi'].mean():.3f}%",
                    annotation_position="top right"
                )
                
                fig.add_vline(
                    x=completed_df["real_roi"].median(),
                    line_dash="dash",
                    line_color="green",
                    annotation_text=f"Mediana: {completed_df['real_roi'].median():.3f}%",
                    annotation_position="top left"
                )
                
                # Mejorar layout
                fig.update_layout(
                    xaxis_title="ROI (%)",
                    yaxis_title="Número de Operaciones",
                    height=500,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                
                # Mostrar gráfico
                st.plotly_chart(fig, use_container_width=True)
                
                # Estadísticas adicionales
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "ROI Promedio",
                        f"{completed_df['real_roi'].mean():.3f}%",
                        delta=None
                    )
                
                with col2:
                    st.metric(
                        "ROI Mediana",
                        f"{completed_df['real_roi'].median():.3f}%",
                        delta=None
                    )
                
                with col3:
                    st.metric(
                        "Desviación Estándar",
                        f"{completed_df['real_roi'].std():.3f}%",
                        delta=None
                    )
            
            # Sub-pestaña 2: Distribución por Estado
            with dist_tabs[1]:
                # Contar operaciones por estado
                status_counts = df["status"].value_counts().reset_index()
                status_counts.columns = ["Estado", "Cantidad"]
                
                # Gráfico de pastel
                fig = px.pie(
                    status_counts,
                    values="Cantidad",
                    names="Estado",
                    title="Distribución de Operaciones por Estado",
                    color="Estado",
                    color_discrete_map={
                        "COMPLETADO": "#10b981",
                        "FALLIDO": "#ef4444",
                        "CANCELADO": "#64748b",
                        "EJECUTANDO": "#3b82f6",
                        "PENDIENTE": "#f59e0b"
                    }
                )
                
                # Mejorar layout
                fig.update_layout(
                    height=500,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                
                # Mostrar gráfico
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabla de resumen
                st.markdown("#### Resumen por Estado")
                st.dataframe(status_counts, use_container_width=True)
            
            # Sub-pestaña 3: Correlación ROI vs Slippage
            with dist_tabs[2]:
                # Verificar si hay datos válidos
                valid_data = completed_df[
                    completed_df["real_roi"].notna() & 
                    completed_df["slippage"].notna()
                ].copy()
                
                if not valid_data.empty:
                    # Gráfico de dispersión
                    fig = px.scatter(
                        valid_data,
                        x="slippage",
                        y="real_roi",
                        title="Correlación entre Slippage y ROI",
                        labels={
                            "slippage": "Slippage (%)",
                            "real_roi": "ROI (%)"
                        },
                        color="real_roi",
                        size="initial_capital",
                        hover_data=["route", "initial_capital", "net_profit"],
                        color_continuous_scale=["red", "yellow", "green"]
                    )
                    
                    # Añadir línea de tendencia
                    fig.update_layout(
                        height=600,
                        margin=dict(l=20, r=20, t=40, b=20)
                    )
                    
                    # Calcular y mostrar correlación
                    correlation = valid_data["slippage"].corr(valid_data["real_roi"])
                    st.markdown(f"**Correlación Slippage-ROI:** {correlation:.3f}")
                    
                    # Descripción de la correlación
                    if correlation < -0.5:
                        st.info("Existe una fuerte correlación negativa: mayor slippage tiende a resultar en menor ROI")
                    elif correlation < -0.2:
                        st.info("Existe una correlación negativa moderada entre slippage y ROI")
                    elif correlation < 0.2:
                        st.info("No existe una correlación clara entre slippage y ROI")
                    elif correlation < 0.5:
                        st.info("Existe una correlación positiva moderada entre slippage y ROI")
                    else:
                        st.info("Existe una fuerte correlación positiva: mayor slippage tiende a resultar en mayor ROI")
                else:
                    st.info("No hay suficientes datos para analizar la correlación")
        else:
            st.info("No hay operaciones completadas para analizar distribuciones")
    
    # Pestaña 4: Análisis de Rutas
    with tabs[3]:
        st.markdown("### Análisis de Rutas")
        
        # Agrupar operaciones por ruta
        if not df.empty and "route" in df.columns:
            # Filtrar operaciones completadas
            completed_df = df[df["status"] == OperationStatus.COMPLETADO.value].copy()
            
            if not completed_df.empty:
                # Agrupar por ruta
                route_analysis = completed_df.groupby("route").agg({
                    "net_profit": ["sum", "mean", "count"],
                    "real_roi": ["mean", "max", "min", "std"],
                    "initial_capital": ["mean", "sum"],
                    "slippage": ["mean"],
                    "total_commissions": ["sum", "mean"]
                }).reset_index()
                
                # Formatear nombres de columnas
                route_analysis.columns = [
                    "Ruta",
                    "Ganancia Total",
                    "Ganancia Promedio",
                    "Operaciones",
                    "ROI Promedio",
                    "ROI Máximo",
                    "ROI Mínimo",
                    "ROI Desviación",
                    "Capital Promedio",
                    "Capital Total",
                    "Slippage Promedio",
                    "Comisiones Totales",
                    "Comisiones Promedio"
                ]
                
                # Ordenar por ganancia total
                route_analysis = route_analysis.sort_values(by="Ganancia Total", ascending=False)
                
                # Mostrar tabla
                st.dataframe(route_analysis, use_container_width=True)
                
                # Gráfico de barras para comparación de rutas
                top_routes = route_analysis.head(10)
                
                fig = px.bar(
                    top_routes,
                    x="Ruta",
                    y="Ganancia Total",
                    title="Top 10 Rutas por Ganancia Total",
                    color="ROI Promedio",
                    text="Operaciones",
                    color_continuous_scale=["red", "yellow", "green"]
                )
                
                # Mejorar layout
                fig.update_layout(
                    xaxis_title="Ruta",
                    yaxis_title="Ganancia Total (USDT)",
                    height=500,
                    margin=dict(l=20, r=20, t=40, b=20),
                    xaxis_tickangle=-45
                )
                
                # Mostrar gráfico
                st.plotly_chart(fig, use_container_width=True)
                
                # Distribución de ROI por ruta
                top_routes_list = top_routes["Ruta"].tolist()
                top_routes_df = completed_df[completed_df["route"].isin(top_routes_list)].copy()
                
                if not top_routes_df.empty:
                    fig = px.box(
                        top_routes_df,
                        x="route",
                        y="real_roi",
                        title="Distribución de ROI por Ruta",
                        labels={
                            "route": "Ruta",
                            "real_roi": "ROI (%)"
                        },
                        color="route"
                    )
                    
                    # Mejorar layout
                    fig.update_layout(
                        xaxis_title="Ruta",
                        yaxis_title="ROI (%)",
                        height=500,
                        margin=dict(l=20, r=20, t=40, b=20),
                        xaxis_tickangle=-45
                    )
                    
                    # Mostrar gráfico
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay operaciones completadas para analizar rutas")
        else:
            st.info("No hay datos de rutas disponibles")

    # Pestaña 5: Informes IA
    with tabs[4]:
        display_ai_reports()


def display_operation_detail(operation: ArbitrageOperation):
    """
    Muestra los detalles de una operación específica
    
    Args:
        operation: Operación a mostrar en detalle
    """
    st.subheader(f"Detalles de Operación {operation.operation_id}")
    
    # Crear pestañas para diferentes secciones
    tabs = st.tabs([
        "Información General", 
        "Detalles de Ejecución", 
        "Análisis IA"
    ])
    
    # Pestaña 1: Información General
    with tabs[0]:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Datos Básicos")
            st.markdown(f"**ID:** {operation.operation_id}")
            st.markdown(f"**Ruta:** {operation.route.route if operation.route else 'N/A'}")
            st.markdown(f"**Estado:** {operation.status}")
            st.markdown(f"**Capital Inicial:** ${operation.initial_capital:.2f}")
            st.markdown(f"**Ganancia Neta:** ${operation.net_profit:.4f}" if operation.net_profit is not None else "**Ganancia Neta:** N/A")
            st.markdown(f"**ROI:** {operation.real_roi:.3f}%" if operation.real_roi is not None else "**ROI:** N/A")
        
        with col2:
            st.markdown("#### Tiempos y Métricas")
            st.markdown(f"**Inicio:** {operation.execution_start_time.strftime('%Y-%m-%d %H:%M:%S')}" if operation.execution_start_time else "**Inicio:** N/A")
            st.markdown(f"**Finalización:** {operation.completion_time.strftime('%Y-%m-%d %H:%M:%S')}" if operation.completion_time else "**Finalización:** N/A")
            
            if operation.execution_start_time and operation.completion_time:
                duration = (operation.completion_time - operation.execution_start_time).total_seconds()
                st.markdown(f"**Duración:** {duration:.2f} segundos")
            else:
                st.markdown("**Duración:** N/A")
            
            st.markdown(f"**Slippage:** {operation.slippage:.3f}%" if operation.slippage is not None else "**Slippage:** N/A")
            st.markdown(f"**Comisiones:** ${operation.total_commissions:.4f}" if operation.total_commissions is not None else "**Comisiones:** N/A")
    
    # Pestaña 2: Detalles de Ejecución
    with tabs[1]:
        st.markdown("#### Detalles de Ejecución")
        
        # Mostrar pares ejecutados
        if operation.executed_pairs:
            st.markdown("##### Pares Ejecutados")
            
            # Convertir a DataFrame para mejor visualización
            pairs_data = []
            for pair in operation.executed_pairs:
                pairs_data.append({
                    "Símbolo": pair.symbol,
                    "Orden": pair.order_type,
                    "Precio": pair.price,
                    "Cantidad": pair.quantity,
                    "Valor Total": pair.total_value,
                    "Comisión": pair.commission,
                    "Timestamp": pair.timestamp
                })
            
            pairs_df = pd.DataFrame(pairs_data)
            st.dataframe(pairs_df, use_container_width=True)
            
            # Mostrar gráfico de secuencia de ejecución
            if len(pairs_data) > 1:
                fig = px.line(
                    pairs_df,
                    x="Timestamp",
                    y="Valor Total",
                    title="Secuencia de Ejecución",
                    markers=True,
                    text="Símbolo"
                )
                
                fig.update_traces(textposition="top center")
                
                # Mejorar layout
                fig.update_layout(
                    xaxis_title="Tiempo",
                    yaxis_title="Valor (USDT)",
                    height=400,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay detalles de ejecución disponibles")
    
    # Pestaña 3: Análisis IA
    with tabs[2]:
        st.markdown("#### Análisis de IA")
        
        if operation.ai_analysis:
            # Mostrar análisis de IA
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Recomendación:** {operation.ai_analysis.recommendation}")
                st.markdown(f"**Confianza:** {operation.ai_analysis.confidence}%")
                st.markdown(f"**ROI Estimado:** {operation.ai_analysis.estimated_roi}%")
            
            with col2:
                st.markdown("**Riesgos Identificados:**")
                for risk in operation.ai_analysis.identified_risks:
                    st.markdown(f"- {risk}")
            
            st.markdown("**Explicación:**")
            st.markdown(operation.ai_analysis.explanation)
            
            # Comparar estimación vs resultados reales si está completada
            if operation.status == OperationStatus.COMPLETADO.value and operation.real_roi is not None:
                st.markdown("#### Comparación Estimación vs Realidad")
                
                # Diferencia entre ROI estimado y real
                roi_diff = operation.real_roi - operation.ai_analysis.estimated_roi
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "ROI Estimado",
                        f"{operation.ai_analysis.estimated_roi}%",
                        delta=None
                    )
                
                with col2:
                    st.metric(
                        "ROI Real",
                        f"{operation.real_roi:.3f}%",
                        delta=None
                    )
                
                with col3:
                    st.metric(
                        "Diferencia",
                        f"{roi_diff:.3f}%",
                        delta=roi_diff,
                        delta_color="inverse"
                    )
                
                # Gráfico comparativo
                comparison_data = {
                    "Tipo": ["Estimado", "Real"],
                    "ROI": [operation.ai_analysis.estimated_roi, operation.real_roi]
                }
                
                fig = px.bar(
                    comparison_data,
                    x="Tipo",
                    y="ROI",
                    title="Comparación ROI Estimado vs Real",
                    color="Tipo",
                    text="ROI"
                )
                
                # Mejorar layout
                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="ROI (%)",
                    height=400,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Evaluar precisión de la IA
                precision = (1 - abs(roi_diff / operation.ai_analysis.estimated_roi)) * 100 if operation.ai_analysis.estimated_roi != 0 else 0
                
                if precision > 90:
                    st.success(f"La IA fue muy precisa en esta operación ({precision:.1f}% de precisión)")
                elif precision > 70:
                    st.info(f"La IA fue moderadamente precisa en esta operación ({precision:.1f}% de precisión)")
                else:
                    st.warning(f"La IA tuvo baja precisión en esta operación ({precision:.1f}% de precisión)")
        else:
            st.info("No hay análisis de IA disponible para esta operación")

def display_ai_reports():
    """
    Muestra los informes de IA generados
    """
    st.subheader("Informes de Análisis de IA")

    # Obtener servicio de informes IA (assuming AIReportService exists)
    try:
        ai_report_service = get_service_registry().get("AIReportService") # Use string key for now
    except Exception as e:
        st.error(f"Error al obtener servicio de informes IA: {e}")
        st.info("Asegúrate de que 'AIReportService' esté registrado en el contenedor de servicios.")
        return

    # Obtener informes de IA desde Supabase
    try:
        reports = ai_report_service.get_ai_reports() # Assuming this method exists
    except Exception as e:
        st.error(f"Error al obtener informes de IA: {e}")
        st.info("Asegúrate de que la tabla 'informes_ia' exista y el servicio pueda acceder a ella.")
        return

    if not reports:
        st.info("No se encontraron informes de IA.")
        return

    # Mostrar informes
    st.markdown(f"**{len(reports)} informes encontrados**")

    # Convertir a DataFrame para visualización
    reports_data = []
    for report in reports:
        report_content = report.get("report_data", {})
        # Assuming report_data is a JSON string or dict
        if isinstance(report_content, str):
            try:
                report_content = json.loads(report_content)
            except json.JSONDecodeError:
                st.warning(f"Error al decodificar el contenido JSON del informe {report.get('id', 'N/A')}")
                report_content = {"error": "Contenido JSON inválido"}

        reports_data.append({
            "ID Informe": report.get("id", "N/A"),
            "Fecha Generación": report.get("generated_at", "N/A"),
            "Total Operaciones": report_content.get("total_operaciones", "N/A"),
            "Ganancia Total": report_content.get("ganancia_total", "N/A"),
            "ROI Promedio": report_content.get("rentabilidad_promedio", "N/A"),
            "Mejor Ruta": report_content.get("mejor_ruta", "N/A"),
            "Recomendaciones": report_content.get("recomendaciones", "N/A"),
            "Patrones Identificados": report_content.get("patrones_identificados", "N/A"),
            "Contenido Completo": report_content # Keep full content for expander
        })

    reports_df = pd.DataFrame(reports_data)

    # Mostrar tabla de informes
    st.dataframe(reports_df[[
        "ID Informe",
        "Fecha Generación",
        "Total Operaciones",
        "Ganancia Total",
        "ROI Promedio",
        "Mejor Ruta"
    ]], use_container_width=True)

    # Mostrar detalles completos en un expander
    with st.expander("Ver detalles completos de los informes"):
        for index, row in reports_df.iterrows():
            st.markdown(f"#### Informe ID: {row['ID Informe']}")
            st.markdown(f"**Fecha Generación:** {row['Fecha Generación']}")
            st.markdown("**Contenido Completo:**")
            st.json(row["Contenido Completo"])
            st.markdown("---")
