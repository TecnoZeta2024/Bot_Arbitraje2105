"""
Ventana principal de Scalper's Brain
Implementa la interfaz de usuario con paneles acoplables y diseño modular
"""

import logging
import sys
from typing import Dict, Any, Optional

from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QStatusBar,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from scalpers_brain.ui.widgets.chart_widget import ChartWidget
from scalpers_brain.ui.widgets.notification_center import NotificationCenter
from scalpers_brain.ui.widgets.notification_widget import NotificationWidget
from scalpers_brain.ui.widgets.opportunities_table import OpportunitiesTable
from scalpers_brain.ui.widgets.strategy_control_panel import StrategyControlPanel

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación Scalper's Brain"""
    
    def __init__(self, app_context: Dict[str, Any]):
        super().__init__()
        self.app_context = app_context
        
        # Registrar la ventana en el contexto para acceso desde otros componentes
        self.app_context['main_window'] = self
        
        # Configurar ventana
        self.setWindowTitle("Scalper's Brain - Edición Personal")
        self.setMinimumSize(1200, 800)
        
        # Inicializar componentes de UI
        self.notification_widget = NotificationWidget("", parent=self)
        self.notification_center = NotificationCenter(self)
        
        # Crear elementos de la interfaz
        self._create_actions()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_status_bar()
        self._create_dock_widgets()
        
        # Configurar layout central
        self._create_central_widget()
        
        logger.info("Ventana principal inicializada")
        
        # Mostrar mensaje de bienvenida
        self.show_notification("Bienvenido a Scalper's Brain - Edición Personal", level="info", timeout=5000)

    def _create_actions(self):
        """Crea las acciones para menús y barras de herramientas"""
        # Acciones de Archivo
        self.new_strategy_action = QAction("Nueva Estrategia", self)
        self.new_strategy_action.setShortcut("Ctrl+N")
        self.new_strategy_action.setStatusTip("Crear una nueva estrategia de trading")
        self.new_strategy_action.triggered.connect(self._new_strategy)

        self.open_action = QAction("Abrir Configuración...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.setStatusTip("Abrir un archivo de configuración existente")
        self.open_action.triggered.connect(self._open_config)

        self.save_action = QAction("Guardar Configuración", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.setStatusTip("Guardar la configuración actual")
        self.save_action.triggered.connect(self._save_config)

        self.exit_action = QAction("Salir", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.setStatusTip("Salir de la aplicación")
        self.exit_action.triggered.connect(self._exit_app)

        # Acciones de Trading
        self.start_trading_action = QAction("Iniciar Trading", self)
        self.start_trading_action.setStatusTip("Iniciar sistema de trading automático")
        self.start_trading_action.triggered.connect(self._start_trading)

        self.stop_trading_action = QAction("Detener Trading", self)
        self.stop_trading_action.setStatusTip("Detener sistema de trading automático")
        self.stop_trading_action.triggered.connect(self._stop_trading)
        
        self.paper_trading_action = QAction("Modo Paper Trading", self)
        self.paper_trading_action.setCheckable(True)
        self.paper_trading_action.setChecked(True)
        self.paper_trading_action.setStatusTip("Activar/desactivar modo paper trading")
        self.paper_trading_action.triggered.connect(self._toggle_paper_trading)

        # Acciones de Ver
        self.zoom_in_action = QAction("Acercar", self)
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_in_action.setStatusTip("Acercar la vista")
        self.zoom_in_action.triggered.connect(self._zoom_in)

        self.zoom_out_action = QAction("Alejar", self)
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_out_action.setStatusTip("Alejar la vista")
        self.zoom_out_action.triggered.connect(self._zoom_out)

        # Acción para abrir el centro de notificaciones
        self.show_notification_center_action = QAction("Centro de Notificaciones", self)
        self.show_notification_center_action.setStatusTip("Mostrar el historial de notificaciones")
        self.show_notification_center_action.triggered.connect(self.notification_center.show)

    def _create_menu_bar(self):
        """Crea la barra de menú principal"""
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        # Menú Archivo
        self.file_menu = self.menu_bar.addMenu("&Archivo")
        self.file_menu.addAction(self.new_strategy_action)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

        # Menú Trading
        self.trading_menu = self.menu_bar.addMenu("&Trading")
        self.trading_menu.addAction(self.start_trading_action)
        self.trading_menu.addAction(self.stop_trading_action)
        self.trading_menu.addSeparator()
        self.trading_menu.addAction(self.paper_trading_action)

        # Menú Ver
        self.view_menu = self.menu_bar.addMenu("&Ver")
        self.view_menu.addAction(self.zoom_in_action)
        self.view_menu.addAction(self.zoom_out_action)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.show_notification_center_action)

        # Menú Ayuda
        self.help_menu = self.menu_bar.addMenu("A&yuda")
        self.about_action = QAction("Acerca de...", self)
        self.about_action.triggered.connect(self._show_about)
        self.help_menu.addAction(self.about_action)

    def _create_tool_bar(self):
        """Crea la barra de herramientas principal"""
        self.tool_bar = self.addToolBar("Principal")
        self.tool_bar.setMovable(True)
        
        # Añadir acciones a la barra de herramientas
        self.tool_bar.addAction(self.new_strategy_action)
        self.tool_bar.addAction(self.open_action)
        self.tool_bar.addAction(self.save_action)
        self.tool_bar.addSeparator()
        
        # Acciones de trading
        self.tool_bar.addAction(self.start_trading_action)
        self.tool_bar.addAction(self.stop_trading_action)
        
        # Selector de exchange
        self.tool_bar.addSeparator()
        exchange_label = QLabel("Exchange:")
        self.tool_bar.addWidget(exchange_label)
        
        self.exchange_combo = QComboBox()
        self.exchange_combo.addItems(["Binance", "Coinbase", "EOD Historical (Premium)", "Polygon.io (Premium)"])
        self.exchange_combo.setCurrentIndex(0)
        self.exchange_combo.currentIndexChanged.connect(self._exchange_changed)
        self.tool_bar.addWidget(self.exchange_combo)

    def _create_status_bar(self):
        """Crea la barra de estado"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Información del estado del sistema
        self.status_connection = QLabel("No conectado")
        self.status_trading = QLabel("Trading: Inactivo")
        self.status_mode = QLabel("Modo: Paper Trading")
        
        self.status_bar.addPermanentWidget(self.status_connection)
        self.status_bar.addPermanentWidget(self.status_trading)
        self.status_bar.addPermanentWidget(self.status_mode)
        
        # Mensaje inicial
        self.status_bar.showMessage("Iniciando Scalper's Brain...", 5000)

    def _create_central_widget(self):
        """Crea el widget central"""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(self.central_widget)
        
        # Widget de bienvenida temporal (se reemplazará por el dashboard principal)
        welcome_widget = QLabel("Cargando Scalper's Brain...")
        welcome_widget.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(welcome_widget)
        
        # Aplicar layout
        self.central_widget.setLayout(main_layout)

    def _create_dock_widgets(self):
        """Crea los widgets acoplables"""
        # Panel de Gráficos
        self.chart_dock = QDockWidget("Gráficos", self)
        self.chart_widget = ChartWidget(self)
        self.chart_dock.setWidget(self.chart_widget)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.chart_dock)

        # Panel de Oportunidades
        self.opportunities_dock = QDockWidget("Oportunidades", self)
        opportunities_container = QWidget()
        opportunities_layout = QVBoxLayout(opportunities_container)

        # Crear tabla de oportunidades
        self.opportunities_table = OpportunitiesTable(self)
        opportunities_layout.addWidget(self.opportunities_table)

        # Controles de filtrado
        filter_layout = QHBoxLayout()
        self.filter_label = QLabel("Filtrar:")
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Escriba para filtrar...")
        self.filter_input.textChanged.connect(self.opportunities_table.set_filter)

        filter_layout.addWidget(self.filter_label)
        filter_layout.addWidget(self.filter_input)
        
        # Añadir filtros al layout de oportunidades
        opportunities_layout.addLayout(filter_layout)
        
        # Establecer el widget contenedor como contenido del dock
        self.opportunities_dock.setWidget(opportunities_container)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.opportunities_dock)

        # Panel de Estrategias
        self.strategies_dock = QDockWidget("Estrategias", self)
        self.strategies_panel = StrategyControlPanel(self)
        self.strategies_dock.setWidget(self.strategies_panel)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.strategies_dock)

        # Configurar áreas de docking permitidas
        self.chart_dock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.opportunities_dock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.strategies_dock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)

    def show_notification(self, message: str, level: str = 'info', timeout: int = 3000, persistent: bool = False):
        """Muestra una notificación flotante y la registra en el centro de notificaciones"""
        # Mostrar notificación flotante
        self.notification_widget.set_message(message)
        self.notification_widget.set_timeout(timeout)
        self.notification_widget.set_persistent(persistent)
        self.notification_widget.set_level(level)
        self.notification_widget.show()

        # Añadir notificación al centro de notificaciones
        self.notification_center.add_notification(message, level)
        
        # También mostrar en la barra de estado para mensajes importantes
        if level in ['warning', 'error']:
            self.status_bar.showMessage(message, timeout)

    def update_status(self, connection_status: str = None, trading_status: str = None, mode: str = None):
        """Actualiza la información de estado en la barra de estado"""
        if connection_status:
            self.status_connection.setText(connection_status)
        
        if trading_status:
            self.status_trading.setText(f"Trading: {trading_status}")
        
        if mode:
            self.status_mode.setText(f"Modo: {mode}")

    # Métodos para acciones del menú
    def _new_strategy(self):
        """Crear nueva estrategia"""
        self.show_notification("Creando nueva estrategia...", timeout=2000)
        # Implementar creación de estrategia

    def _open_config(self):
        """Abrir configuración"""
        self.show_notification("Abriendo configuración...", timeout=2000)
        # Implementar apertura de configuración

    def _save_config(self):
        """Guardar configuración"""
        self.show_notification("Configuración guardada", timeout=2000)
        # Implementar guardado de configuración

    def _exit_app(self):
        """Salir de la aplicación"""
        # Añadir lógica para guardar estado, cerrar conexiones, etc.
        self.close()

    def _start_trading(self):
        """Iniciar trading"""
        self.show_notification("Iniciando sistema de trading...", level="info")
        self.update_status(trading_status="Activo")
        # Implementar inicio de trading

    def _stop_trading(self):
        """Detener trading"""
        self.show_notification("Sistema de trading detenido", level="warning")
        self.update_status(trading_status="Inactivo")
        # Implementar detención de trading

    def _toggle_paper_trading(self, checked):
        """Activar/desactivar paper trading"""
        mode = "Paper Trading" if checked else "Trading Real"
        self.update_status(mode=mode)
        
        if not checked:
            self.show_notification("¡ATENCIÓN! Modo de trading real activado", level="warning", persistent=True)
        else:
            self.show_notification("Modo paper trading activado", level="info")

    def _exchange_changed(self, index):
        """Cambiar exchange seleccionado"""
        exchange = self.exchange_combo.currentText()
        self.show_notification(f"Exchange cambiado a {exchange}", level="info")
        
        # Verificar si es un exchange premium
        if "(Premium)" in exchange and self.app_context.get('is_premium', False) == False:
            self.show_notification("Esta funcionalidad requiere la versión Premium", level="warning")
            # Revertir a Binance (índice 0)
            self.exchange_combo.setCurrentIndex(0)

    def _zoom_in(self):
        """Acercar vista"""
        # Implementar zoom in en el widget activo

    def _zoom_out(self):
        """Alejar vista"""
        # Implementar zoom out en el widget activo

    def _show_about(self):
        """Mostrar diálogo 'Acerca de'"""
        self.show_notification("Scalper's Brain v1.0.0 - Edición Personal", level="info")
