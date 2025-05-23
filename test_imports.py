#!/usr/bin/env python3
"""
Script de prueba para identificar problemas específicos en dashboard_production.py
Líneas problemáticas: 118, 133, 296
"""

import sys
import traceback

print("=== ANALISIS DE PROBLEMAS EN DASHBOARD_PRODUCTION.PY ===")
print(f"Python version: {sys.version}")
print()

# Test 1: Importaciones básicas
print("1. Testing basic imports...")
try:
    import streamlit as st
    print("   [OK] streamlit: OK")
except ImportError as e:
    print(f"   [ERROR] streamlit: {e}")

try:
    import pandas as pd
    print("   [OK] pandas: OK")
except ImportError as e:
    print(f"   [ERROR] pandas: {e}")

try:
    import plotly.graph_objects as go
    print("   [OK] plotly: OK")
except ImportError as e:
    print(f"   [ERROR] plotly: {e}")

try:
    import asyncio
    import websockets
    print("   [OK] websockets: OK")
except ImportError as e:
    print(f"   [ERROR] websockets: {e}")

print()

# Test 2: Importaciones específicas del proyecto - Línea 118 aprox
print("2. Testing SystemMonitor import (linea ~118)...")
try:
    from src.infrastructure.monitoring.system_monitor import SystemMonitor, HealthStatus, AlertSeverity
    print("   [OK] SystemMonitor: Importado correctamente")
except ImportError as e:
    print(f"   [ERROR] SystemMonitor: {e}")
    print(f"   Stack trace: {traceback.format_exc()}")

print()

# Test 3: Importaciones de AdvancedRiskManager
print("3. Testing AdvancedRiskManager import...")
try:
    from src.domain.risk_management.advanced_risk_manager import AdvancedRiskManager, RiskParameters
    print("   [OK] AdvancedRiskManager: Importado correctamente")
except ImportError as e:
    print(f"   [ERROR] AdvancedRiskManager: {e}")

print()

# Test 4: Importaciones de SupabaseClient - Línea 133 aprox
print("4. Testing SupabaseClient import (linea ~133)...")
try:
    from src.infrastructure.external_apis.supabase_client import SupabaseClient
    print("   [OK] SupabaseClient: Importado correctamente")
except ImportError as e:
    print(f"   [ERROR] SupabaseClient: {e}")
    print(f"   Stack trace: {traceback.format_exc()}")

print()

# Test 5: Otras importaciones del proyecto
print("5. Testing other project imports...")
try:
    from src.infrastructure.database.operation_repository_impl import OperationRepositoryImpl
    print("   [OK] OperationRepositoryImpl: OK")
except ImportError as e:
    print(f"   [ERROR] OperationRepositoryImpl: {e}")

try:
    from src.utils.performance_calculator import calcular_metricas_rendimiento
    print("   [OK] Performance Calculator: OK")
except ImportError as e:
    print(f"   [ERROR] Performance Calculator: {e}")

try:
    from src.utils.config import settings, load_config, save_config
    print("   [OK] Config utils: OK")
except ImportError as e:
    print(f"   [ERROR] Config utils: {e}")

print()

# Test 6: Test async function similar a línea 296
print("6. Testing async functionality (relacionado a linea ~296)...")
try:
    import queue
    import threading
    import json
    
    async def test_async_function():
        """Test similar a process_websocket_messages"""
        message_queue = queue.Queue()
        
        # Simular procesamiento de mensajes
        while not message_queue.empty():
            try:
                message = message_queue.get_nowait()
                msg_type = message.get('type')
                print(f"   Procesando mensaje tipo: {msg_type}")
            except queue.Empty:
                break
        
        return True
    
    # Ejecutar test async
    result = asyncio.run(test_async_function())
    print("   [OK] Async functionality: OK")
    
except Exception as e:
    print(f"   [ERROR] Async functionality: {e}")
    print(f"   Stack trace: {traceback.format_exc()}")

print()

# Test 7: Verificar estructura de directorios
print("7. Testing directory structure...")
import os

required_paths = [
    "src",
    "src/infrastructure",
    "src/infrastructure/monitoring",
    "src/infrastructure/external_apis",
    "src/domain",
    "src/domain/risk_management",
    "src/utils"
]

for path in required_paths:
    if os.path.exists(path):
        print(f"   [OK] Directory exists: {path}")
    else:
        print(f"   [ERROR] Missing directory: {path}")

print()
print("=== ANALISIS COMPLETO ===")
