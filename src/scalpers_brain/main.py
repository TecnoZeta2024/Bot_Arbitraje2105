#!/usr/bin/env python3
"""
Scalper's Brain - Edición Personal
Plataforma avanzada de trading personal con arquitectura modular y análisis potenciado por IA.
"""

import asyncio
import os
import sys
import platform
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join('logs', f'scalpers_brain_{os.getpid()}.log'))
    ]
)

logger = logging.getLogger("ScalpersBrain")

# Asegurar que la carpeta logs exista
os.makedirs('logs', exist_ok=True)

async def initialize_backend(app_context):
    """Inicializa los servicios backend de manera asíncrona"""
    from scalpers_brain.infrastructure.container.di_container import DIContainer, ServiceLocator
    from scalpers_brain.core.backend_service import UIBackendService
    
    logger.info("Inicializando servicios backend...")
    
    # Crear y configurar el contenedor DI
    container = DIContainer()
    ServiceLocator.set_container(container)
    
    # Registrar servicios
    await register_services(container)
    
    # Obtener servicio de backend para UI
    backend_service = container.resolve(UIBackendService)
    app_context['backend'] = backend_service
    
    logger.info("Servicios backend inicializados exitosamente")
    
    return backend_service

async def register_services(container):
    """Registra todos los servicios en el contenedor DI"""
    from scalpers_brain.core.backend_service import UIBackendService
    from scalpers_brain.infrastructure.market_data.binance_adapter import BinanceAdapter
    
    # Registrar adaptadores de exchange
    container.register_singleton(BinanceAdapter)
    
    # Registrar servicios principales
    container.register_singleton(UIBackendService)
    
    # Cargar adaptadores adicionales según configuración
    
    logger.info("Servicios registrados en el contenedor DI")

def run():
    """Función principal que inicia la aplicación"""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QIcon
    from scalpers_brain.ui.main_window import MainWindow
    
    logger.info(f"Iniciando Scalper's Brain en {platform.system()} {platform.release()}")
    
    # Crear aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Scalper's Brain")
    
    # Configuración específica por sistema operativo
    if platform.system() == "Windows":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ScalpersBrain")
        
    # Cargar estilos
    style_path = os.path.join(os.path.dirname(__file__), 'ui', 'style.qss')
    if os.path.exists(style_path):
        with open(style_path, 'r') as f:
            app.setStyleSheet(f.read())
    else:
        logger.warning(f"No se encontró el archivo de estilo en {style_path}")
    
    # Inicializar la ventana principal (Frontend First)
    app_context = {}
    main_window = MainWindow(app_context)
    main_window.show()
    
    # Iniciar la inicialización del backend de forma asíncrona
    loop = asyncio.get_event_loop()
    loop.create_task(initialize_backend(app_context))
    
    # Iniciar bucle de eventos
    sys.exit(app.exec_())

if __name__ == "__main__":
    run()
