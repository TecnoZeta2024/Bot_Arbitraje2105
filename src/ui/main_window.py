import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QDockWidget, QAction, QMenuBar, QToolBar
from PyQt5.QtCore import Qt, QSize, QCoreApplication
from PyQt5.QtGui import QIcon, QPalette, QColor
from src.ui.chart_widget import ChartWidget # Importar ChartWidget
from src.ui.opportunities_panel import OpportunitiesPanel # Importar OpportunitiesPanel
from src.ui.strategy_control_panel import StrategyControlPanel # Importar StrategyControlPanel
from src.ui.notification_manager import NotificationManager # Importar NotificationManager
from src.ui.notification_center_panel import NotificationCenterPanel # Importar NotificationCenterPanel
import pandas as pd # Necesario para los datos de mplfinance
import numpy as np # Necesario para generar datos de prueba

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scalper's Brain")
        self.setGeometry(100, 100, 1200, 800)
        
        # Instanciar el gestor de notificaciones
        self.notification_manager = NotificationManager(self)
        
        # Instanciar el centro de notificaciones
        self.notification_center_panel = NotificationCenterPanel(self)
        
        # Conectar la señal del gestor de notificaciones al centro de notificaciones
        self.notification_manager.notification_signal.connect(self.notification_center_panel.add_notification)

        self._setup_ui()

    def _setup_ui(self):
        # Configurar tema oscuro
        self.set_dark_theme()

        # Widget central
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(0, 0, 0, 0)

        # Configurar menús
        self._setup_menus()

        # Configurar toolbar
        self._setup_toolbar()

        # Configurar sistema de docking (ejemplo de paneles)
        self._setup_dock_widgets()

    def set_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        self.setPalette(palette)

    def _setup_menus(self):
        menubar = self.menuBar()

        self.file_menu = menubar.addMenu('&Archivo')
        new_action = QAction('&Nuevo', self)
        self.file_menu.addAction(new_action)
        self.file_menu.addSeparator()
        exit_action = QAction('&Salir', self)
        exit_action.triggered.connect(QCoreApplication.instance().quit)
        self.file_menu.addAction(exit_action)

        self.view_menu = menubar.addMenu('&Vista')
        # Aquí se añadirán acciones para mostrar/ocultar paneles
        show_notifications_action = QAction('Mostrar Centro de Notificaciones', self)
        show_notifications_action.triggered.connect(self._toggle_notification_center)
        self.view_menu.addAction(show_notifications_action)
        
        self.tools_menu = menubar.addMenu('&Herramientas')
        # Acciones para herramientas de trading, backtesting, etc.
        test_notification_action = QAction('Enviar Notificación de Prueba', self)
        test_notification_action.triggered.connect(self._send_test_notification)
        self.tools_menu.addAction(test_notification_action)

        self.help_menu = menubar.addMenu('&Ayuda')
        about_action = QAction('&Acerca de', self)
        self.help_menu.addAction(about_action)

    def _setup_toolbar(self):
        self.toolbar = self.addToolBar('Principal')
        self.toolbar.setIconSize(QSize(24, 24))

        open_action = QAction(QIcon.fromTheme('document-open'), 'Abrir', self)
        self.toolbar.addAction(open_action)

        save_action = QAction(QIcon.fromTheme('document-save'), 'Guardar', self)
        self.toolbar.addAction(save_action)

        self.toolbar.addSeparator()

        play_action = QAction(QIcon.fromTheme('media-playback-start'), 'Iniciar Estrategia', self)
        self.toolbar.addAction(play_action)

        stop_action = QAction(QIcon.fromTheme('media-playback-stop'), 'Detener Estrategia', self)
        self.toolbar.addAction(stop_action)

    def _setup_dock_widgets(self):
        # Ejemplo de un panel acoplable
        self.opportunities_panel = OpportunitiesPanel()
        dock1 = QDockWidget("Panel de Oportunidades", self)
        dock1.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        dock1.setWidget(self.opportunities_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock1)

        dock2 = QDockWidget("Panel de Gráficos", self)
        dock2.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.chart_widget = ChartWidget() # Instanciar ChartWidget
        dock2.setWidget(self.chart_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock2)

        self.strategy_control_panel = StrategyControlPanel()
        dock3 = QDockWidget("Panel de Control de Estrategias", self)
        dock3.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        dock3.setWidget(self.strategy_control_panel)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock3)

        # Panel de Centro de Notificaciones
        dock_notifications = QDockWidget("Centro de Notificaciones", self)
        dock_notifications.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        dock_notifications.setWidget(self.notification_center_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_notifications)

        # Ejemplo de datos para el panel de oportunidades
        example_opportunities_data = [
            [1, "BTC/USDT", "Binance", "Triangular", "0.5", "1000", "95%", "Ejecutar"],
            [2, "ETH/USDT", "Coinbase", "Cross-Exchange", "1.2", "500", "88%", "Analizar"],
            [3, "ADA/BTC", "Kraken", "Triangular", "0.3", "2000", "70%", "Ejecutar"],
            [4, "XRP/USDT", "Binance", "Cross-Exchange", "0.8", "750", "92%", "Analizar"],
            [5, "LTC/EUR", "Bitstamp", "Triangular", "0.6", "1200", "80%", "Ejecutar"],
            [6, "BCH/USD", "Gemini", "Cross-Exchange", "1.0", "600", "90%", "Analizar"],
            [7, "DOT/USDT", "KuCoin", "Triangular", "0.4", "1500", "78%", "Ejecutar"],
            [8, "SOL/USDT", "FTX", "Cross-Exchange", "1.5", "300", "98%", "Analizar"],
        ]
        self.opportunities_panel.update_opportunities(example_opportunities_data)

        # Generar datos de prueba y actualizar el gráfico
        self._load_and_display_sample_chart_data()

        # Puedes añadir más paneles y configurarlos según sea necesario

    def _load_and_display_sample_chart_data(self):
        # Generar datos de velas de ejemplo
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        open_prices = np.random.uniform(100, 110, 100)
        high_prices = open_prices + np.random.uniform(1, 5, 100)
        low_prices = open_prices - np.random.uniform(1, 5, 100)
        close_prices = np.random.uniform(low_prices, high_prices, 100)
        volume = np.random.uniform(1000, 5000, 100)

        data = pd.DataFrame({
            'Open': open_prices,
            'High': high_prices,
            'Low': low_prices,
            'Close': close_prices,
            'Volume': volume
        }, index=dates)

        # Generar indicadores de ejemplo (SMA 10 y SMA 20)
        sma_10 = data['Close'].rolling(window=10).mean()
        sma_20 = data['Close'].rolling(window=20).mean()
        
        indicators = [
            {'data': sma_10, 'color': 'blue', 'linestyle': '-', 'panel': 0},
            {'data': sma_20, 'color': 'red', 'linestyle': '-', 'panel': 0}
        ]

        # Generar señales de trading de ejemplo (compra/venta aleatorias)
        signals = []
        for i in range(len(data)):
            if np.random.rand() < 0.05: # 5% de probabilidad de señal
                if np.random.rand() < 0.5: # 50% de probabilidad de compra
                    signals.append({'data': [data['Low'].iloc[i] * 0.98 if i == j else np.nan for j in range(len(data))], 'marker': '^', 'color': 'green', 'markersize': 100, 'panel': 0})
                else: # 50% de probabilidad de venta
                    signals.append({'data': [data['High'].iloc[i] * 1.02 if i == j else np.nan for j in range(len(data))], 'marker': 'v', 'color': 'red', 'markersize': 100, 'panel': 0})

        self.chart_widget.update_chart(data, indicators, signals)

    def _send_test_notification(self):
        self.notification_manager.show_notification("info", "Notificación de Prueba", "Esta es una notificación de información de prueba.")
        self.notification_manager.show_notification("warning", "Advertencia de Prueba", "Algo importante que debes saber.")
        self.notification_manager.show_notification("error", "Error de Prueba", "Ha ocurrido un error crítico.")
        self.notification_manager.show_notification("success", "Éxito de Prueba", "La operación se completó con éxito.")

    def _toggle_notification_center(self):
        if self.notification_center_panel.isVisible():
            self.notification_center_panel.hide()
        else:
            self.notification_center_panel.show()
