"""
Página de monitoreo en tiempo real.
"""

import subprocess  # Import subprocess
import sys  # Import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.apis.binance_client import BinanceClient  # Import BinanceClient
from src.core.dashboard.dependency_injection import get_service_registry
from src.core.dashboard.services import (
    ConfigService,
    OperationService,
    SystemMonitorService,
)
from src.utils.ui_components import (
    create_data_table,
    create_performance_chart,
    create_status_dashboard,
    display_metric_card,
    display_status_indicator,
)


def display_monitoring_page():
    """
    Muestra la página de monitoreo en tiempo real
    """
    st.title("📈 Monitoreo en Tiempo Real")
    
    # Obtener servicios
    service_registry = get_service_registry()
    operation_service = service_registry.get(OperationService)
    config_service = service_registry.get(ConfigService)
    system_monitor_service = service_registry.get(SystemMonitorService)
    binance_client = service_registry.get(BinanceClient) # Get BinanceClient instance
    
    # Obtener configuración
    config = config_service.get_system_config()
    
    # Pestañas
    tabs = st.tabs([
        "Rendimiento General",
        "Operaciones Activas",
        "Estado del Sistema",
        "Saldos de Cuenta" # New tab for balances
    ])
    
    # Pestaña de rendimiento general
    with tabs[0]:
        display_performance_overview(operation_service)
    
    # Pestaña de operaciones activas
    with tabs[1]:
        display_active_operations(operation_service)
    
    # Pestaña de estado del sistema
    with tabs[2]:
        display_system_status(system_monitor_service, config)

    # Pestaña de saldos de cuenta
    with tabs[3]:
        display_account_balances(binance_client) # New function call
    
    # Actualización automática
    auto_refresh = st.sidebar.checkbox("Actualización automática", value=False)
    refresh_interval = st.sidebar.slider("Intervalo (segundos)", 5, 60, 10)
    
    if auto_refresh:
        st.sidebar.warning(f"Actualizando cada {refresh_interval} segundos")
        time.sleep(refresh_interval)
        st.rerun()

def display_performance_overview(operation_service: OperationService):
    """
    Muestra una vista general del rendimiento
    
    Args:
        operation_service: Servicio de operaciones
    """
    st.subheader("Resumen de Rendimiento")
    
    # Métricas de último día
    st.markdown("#### Últimas 24 Horas")
    
    # Obtener operaciones de las últimas 24 horas
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)
    daily_operations = operation_service.get_operations_by_date_range(start_date, end_date)
    
    # Calcular métricas
    daily_metrics = operation_service.calculate_performance_metrics(daily_operations)
    
    # Mostrar métricas en columnas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        display_metric_card(
            "Operaciones",
            daily_metrics["total_operations"],
            help_text="Número total de operaciones en las últimas 24 horas"
        )
    
    with col2:
        display_metric_card(
            "Ganancia Total",
            daily_metrics["total_profit"],
            prefix="$",
            precision=3,
            help_text="Ganancia neta total en las últimas 24 horas"
        )
    
    with col3:
        display_metric_card(
            "Tasa de Éxito",
            daily_metrics["success_rate"] * 100,
            suffix="%",
            help_text="Porcentaje de operaciones exitosas"
        )
    
    with col4:
        display_metric_card(
            "ROI Promedio",
            daily_metrics["average_roi"],
            suffix="%",
            help_text="Rentabilidad promedio por operación"
        )
    
    # Gráfico de rendimiento de los últimos 7 días
    st.markdown("#### Tendencia de los Últimos 7 Días")
    
    # Obtener historial de operaciones
    history = operation_service.get_operation_history_by_day(days=7)
    
    # Crear gráfico
    fig = create_performance_chart(
        history,
        title="Rendimiento de los Últimos 7 Días"
    )
    
    # Mostrar gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Mejores rutas
    st.markdown("#### Mejores Rutas")
    best_routes = operation_service.get_best_routes(limit=5)
    
    if best_routes:
        # Crear DataFrame
        routes_df = pd.DataFrame(best_routes)
        
        # Formatear columnas
        routes_df["average_roi"] = routes_df["average_roi"].apply(lambda x: f"{x:.3f}%")
        routes_df["total_profit"] = routes_df["total_profit"].apply(lambda x: f"${x:.3f}")
        
        # Renombrar columnas
        routes_df.columns = [
            "Ruta",
            "Ganancia Total",
            "ROI Promedio",
            "Volumen Total",
            "Operaciones Exitosas"
        ]
        
        # Mostrar tabla
        st.dataframe(routes_df, use_container_width=True)
    else:
        st.info("No hay datos suficientes para mostrar las mejores rutas")

def display_active_operations(operation_service: OperationService):
    """
    Muestra las operaciones activas
    
    Args:
        operation_service: Servicio de operaciones
    """
    st.subheader("Operaciones Activas")
    
    # Obtener operaciones en ejecución
    executing_operations = operation_service.get_operations_by_status("EJECUTANDO")
    
    if executing_operations:
        st.markdown(f"**{len(executing_operations)} operaciones en ejecución**")
        
        # Crear DataFrame
        operations_data = []
        for op in executing_operations:
            operations_data.append({
                "ID": op.operation_id,
                "Ruta": op.route.route,
                "Capital": op.initial_capital,
                "Inicio": op.execution_start_time.strftime("%H:%M:%S") if op.execution_start_time else "",
                "Tiempo": (datetime.now() - op.execution_start_time).seconds if op.execution_start_time else 0,
                "Estado": "En Ejecución"
            })
        
        operations_df = pd.DataFrame(operations_data)
        
        # Formatear columnas
        operations_df["Capital"] = operations_df["Capital"].apply(lambda x: f"${x:.2f}")
        operations_df["Tiempo"] = operations_df["Tiempo"].apply(lambda x: f"{x} seg")
        
        # Mostrar tabla
        st.dataframe(operations_df, use_container_width=True)
    else:
        st.info("No hay operaciones en ejecución actualmente")
    
    # Operaciones pendientes
    pending_operations = operation_service.get_operations_by_status("PENDIENTE")
    
    if pending_operations:
        st.markdown(f"**{len(pending_operations)} operaciones pendientes**")
        
        # Crear DataFrame
        operations_data = []
        for op in pending_operations:
            operations_data.append({
                "ID": op.operation_id,
                "Ruta": op.route.route,
                "Capital": op.initial_capital,
                "Análisis IA": op.ai_analysis.recommendation if op.ai_analysis else "N/A",
                "Confianza": op.ai_analysis.confidence if op.ai_analysis else 0,
                "ROI Estimado": op.ai_analysis.estimated_roi if op.ai_analysis else 0
            })
        
        operations_df = pd.DataFrame(operations_data)
        
        # Formatear columnas
        operations_df["Capital"] = operations_df["Capital"].apply(lambda x: f"${x:.2f}")
        operations_df["Confianza"] = operations_df["Confianza"].apply(lambda x: f"{x}%")
        operations_df["ROI Estimado"] = operations_df["ROI Estimado"].apply(lambda x: f"{x}%")
        
        # Mostrar tabla
        st.dataframe(operations_df, use_container_width=True)
    else:
        st.info("No hay operaciones pendientes")
    
    # Operaciones recientes
    st.subheader("Operaciones Recientes")
    recent_operations = operation_service.get_recent_operations(limit=10)
    
    if recent_operations:
        # Crear DataFrame
        operations_data = []
        for op in recent_operations:
            operations_data.append({
                "ID": op.operation_id,
                "Ruta": op.route.route,
                "Capital": op.initial_capital,
                "Ganancia": op.net_profit,
                "ROI": op.real_roi,
                "Estado": op.status,
                "Finalización": op.completion_time.strftime("%H:%M:%S") if op.completion_time else ""
            })
        
        operations_df = pd.DataFrame(operations_data)
        
        # Formatear columnas
        operations_df["Capital"] = operations_df["Capital"].apply(lambda x: f"${x:.2f}")
        operations_df["Ganancia"] = operations_df["Ganancia"].apply(lambda x: f"${x:.3f}" if x is not None else "")
        operations_df["ROI"] = operations_df["ROI"].apply(lambda x: f"{x:.3f}%" if x is not None else "")
        
        # Colorear estados
        operations_df["Estado"] = operations_df["Estado"].apply(
            lambda x: f"<span style='color: {'green' if x == 'COMPLETADO' else 'red' if x == 'FALLIDO' else 'blue' if x == 'EJECUTANDO' else 'gray'};'>{x}</span>"
        )
        
        # Mostrar tabla con formato HTML
        st.markdown(operations_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.info("No hay operaciones recientes")

def display_system_status(system_monitor_service: SystemMonitorService, config):
    """
    Muestra el estado del sistema
    
    Args:
        system_monitor_service: Servicio de monitoreo del sistema
        config: Configuración del sistema
    """
    st.subheader("Estado del Sistema")
    
    # Obtener estado del sistema
    system_status = system_monitor_service.get_system_status()
    
    # Obtener estado de los procesos
    processes = system_monitor_service.check_processes()
    
    # Combinar datos
    status_data = {
        **system_status,
        "active_processes": processes
    }
    
    # Definir umbrales (using thresholds from config object attributes)
    cpu_threshold = getattr(config, "cpu_threshold", 80)
    memory_threshold = getattr(config, "memory_threshold", 85)
    disk_threshold = getattr(config, "disk_threshold", 90)

    thresholds = {
        "cpu_usage": {
            "low": (0, "green"),
            "medium": (cpu_threshold - 20, "yellow"),
            "high": (cpu_threshold, "red")
        },
        "memory_usage": {
            "low": (0, "green"),
            "medium": (memory_threshold - 20, "yellow"),
            "high": (memory_threshold, "red")
        },
        "disk_usage": {
            "low": (0, "green"),
            "medium": (disk_threshold - 20, "yellow"),
            "high": (disk_threshold, "red")
        }
    }
    
    # Mostrar dashboard de estado con visual alerts
    st.markdown("#### Métricas del Sistema")
    col1, col2, col3 = st.columns(3)

    # Display CPU Usage with color indicator
    cpu_usage = status_data.get("cpu_usage", 0)
    cpu_color = "green"
    if cpu_usage >= thresholds["cpu_usage"]["high"][0]:
        cpu_color = "red"
    elif cpu_usage >= thresholds["cpu_usage"]["medium"][0]:
        cpu_color = "yellow"
    with col1:
        st.markdown(f"**Uso de CPU:** <span style='color:{cpu_color}'>{cpu_usage}%</span>", unsafe_allow_html=True)

    # Display Memory Usage with color indicator
    memory_usage = status_data.get("memory_usage", 0)
    memory_color = "green"
    if memory_usage >= thresholds["memory_usage"]["high"][0]:
        memory_color = "red"
    elif memory_usage >= thresholds["memory_usage"]["medium"][0]:
        memory_color = "yellow"
    with col2:
        st.markdown(f"**Uso de memoria:** <span style='color:{memory_color}'>{memory_usage}%</span>", unsafe_allow_html=True)

    # Display Disk Usage with color indicator
    disk_usage = status_data.get("disk_usage", 0)
    disk_color = "green"
    if disk_usage >= thresholds["disk_usage"]["high"][0]:
        disk_color = "red"
    elif disk_usage >= thresholds["disk_usage"]["medium"][0]:
        disk_color = "yellow"
    with col3:
        st.markdown(f"**Uso de disco:** <span style='color:{disk_color}'>{disk_usage}%</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Control de Scripts")

    # Buttons for bot control
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Iniciar Detección"):
            st.info("Iniciando script de detección...")
            # TODO: Implement logic to start the detection script process
            st.success("Script de detección iniciado (simulado).")

    with col2:
        if st.button("Detener Detección"):
            st.info("Deteniendo script de detección...")
            # TODO: Implement logic to stop the detection script process
            st.warning("Script de detección detenido (simulado).")

    with col3:
        if st.button("Reiniciar Detección"):
            st.info("Reiniciando script de detección...")
            # TODO: Implement logic to restart the detection script process
            st.success("Script de detección reiniciado (simulado).")

    with col4:
        if st.button("Detener Todo"):
            st.info("Deteniendo todos los scripts...")
            # TODO: Implement logic to stop all bot processes
            st.warning("Todos los scripts detenidos (simulado).")


    st.markdown("---")
    # Logs del sistema
    st.subheader("Logs del Sistema")
    
    # Selector de componente
    component = st.selectbox(
        "Seleccionar componente",
        ["system", "detector", "executor", "api_server", "telegram_bot", "dashboard"]
    )
    
    # Número de líneas
    num_lines = st.slider("Número de líneas", 10, 200, 50)
    
    # Obtener logs
    logs = system_monitor_service.get_logs(component, lines=num_lines)
    
    # Palabras clave para resaltar
    highlight_keywords = {
        "ERROR": "red",
        "WARNING": "orange",
        "CRITICAL": "purple",
        "EXCEPTION": "red",
        "FAILED": "red",
        "SUCCESS": "green",
        "COMPLETED": "green"
    }
    
    # Mostrar logs
    if logs:
        log_text = "\n".join(logs)
        st.text_area("Logs", log_text, height=400)
    else:
        st.info(f"No hay logs disponibles para {component}")

def display_account_balances(binance_client: BinanceClient):
    """
    Muestra los saldos de la cuenta de Binance.

    Args:
        binance_client: Instancia del cliente de Binance.
    """
    st.subheader("Saldos de Cuenta de Binance")

    try:
        balances = binance_client.get_balances()

        if balances:
            # Filter out zero balances for cleaner display
            non_zero_balances = [b for b in balances if float(b.get("free", 0)) > 0 or float(b.get("locked", 0)) > 0]

            if non_zero_balances:
                # Convert to DataFrame for display
                balances_df = pd.DataFrame(non_zero_balances)

                # Rename columns for clarity
                balances_df.columns = ["Activo", "Libre", "Bloqueado"]

                # Format numeric columns
                balances_df["Libre"] = balances_df["Libre"].apply(lambda x: f"{float(x):.8f}")
                balances_df["Bloqueado"] = balances_df["Bloqueado"].apply(lambda x: f"{float(x):.8f}")

                st.dataframe(balances_df, use_container_width=True)
            else:
                st.info("No hay saldos distintos de cero en la cuenta de Binance.")
        else:
            st.warning("No se pudieron obtener los saldos de la cuenta de Binance.")
    except Exception as e:
        st.error(f"Error al obtener saldos de Binance: {e}")
        st.info("Asegúrate de que las credenciales de Binance estén configuradas correctamente y la API sea accesible.")
