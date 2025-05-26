"""
Widget de gráficos financieros para Scalper's Brain
Implementa visualización avanzada de gráficos con mplfinance
"""

import logging
import numpy as np
import pandas as pd
import mplfinance as mpf
from datetime import datetime, timedelta

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel
from PyQt5.QtCore import Qt, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)

class ChartWidget(QWidget):
    """Widget para visualización de gráficos financieros"""
    
    # Señales
    symbol_changed = pyqtSignal(str)
    timeframe_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Datos del gráfico
        self.symbol = "BTCUSDT"
        self.timeframe = "1m"
        self.chart_data = None
        
        # Configuración
        self.chart_style = 'nightclouds'  # Tema oscuro profesional
        self.volume = True
        
        # UI
        self.init_ui()
        
        # Cargar datos de ejemplo para prueba
        self.load_sample_data()
        
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Layout principal
        self.layout = QVBoxLayout(self)
        
        # Controles superiores
        controls_layout = QHBoxLayout()
        
        # Selector de símbolo
        self.symbol_label = QLabel("Símbolo:")
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT"])
        self.symbol_combo.setCurrentText(self.symbol)
        self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
        
        # Selector de timeframe
        self.timeframe_label = QLabel("Timeframe:")
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1m", "5m", "15m", "1h", "4h", "1d"])
        self.timeframe_combo.setCurrentText(self.timeframe)
        self.timeframe_combo.currentTextChanged.connect(self.on_timeframe_changed)
        
        # Botones de indicadores
        self.add_indicator_btn = QPushButton("+ Indicador")
        self.add_indicator_btn.clicked.connect(self.on_add_indicator)
        
        # Añadir widgets al layout de controles
        controls_layout.addWidget(self.symbol_label)
        controls_layout.addWidget(self.symbol_combo)
        controls_layout.addWidget(self.timeframe_label)
        controls_layout.addWidget(self.timeframe_combo)
        controls_layout.addStretch()
        controls_layout.addWidget(self.add_indicator_btn)
        
        # Añadir layout de controles al layout principal
        self.layout.addLayout(controls_layout)
        
        # Crear widget de gráfico
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        
        # Añadir canvas al layout
        self.layout.addWidget(self.canvas)
        
        # Aplicar layout
        self.setLayout(self.layout)
        
    def load_sample_data(self):
        """Carga datos de ejemplo para mostrar un gráfico inicial"""
        # Crear datos de ejemplo
        np.random.seed(42)
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=500, freq='1min')
        
        # Simular precios con una tendencia y volatilidad
        price = 50000
        prices = []
        volumes = []
        
        for _ in range(len(dates)):
            change = np.random.normal(0, 1) * 50  # Cambio aleatorio con volatilidad
            price += change
            prices.append(price)
            volumes.append(np.random.randint(10000, 1000000))
        
        # Crear OHLC a partir de precios
        opens = prices.copy()
        closes = prices.copy()
        highs = [p * (1 + np.random.uniform(0, 0.01)) for p in prices]
        lows = [p * (1 - np.random.uniform(0, 0.01)) for p in prices]
        
        # Crear DataFrame
        self.chart_data = pd.DataFrame({
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes,
            'Volume': volumes
        }, index=dates)
        
        # Visualizar datos
        self.update_chart()
        
    def update_chart(self):
        """Actualiza el gráfico con los datos actuales"""
        if self.chart_data is None:
            logger.warning("No hay datos para mostrar en el gráfico")
            return
        
        # Limpiar figura
        self.figure.clear()
        
        # Configurar mplfinance
        kwargs = {
            'type': 'candle',
            'style': self.chart_style,
            'figsize': (10, 6),
            'volume': self.volume,
            'panel_ratios': (4, 1) if self.volume else None,
            'tight_layout': True,
            'title': f'{self.symbol} - {self.timeframe}',
            'returnfig': True
        }
        
        # Crear gráfico
        fig, axes = mpf.plot(
            self.chart_data,
            **kwargs,
            fig=self.figure
        )
        
        # Actualizar canvas
        self.canvas.draw()
        
    def on_symbol_changed(self, symbol):
        """Maneja el cambio de símbolo"""
        if symbol == self.symbol:
            return
            
        self.symbol = symbol
        logger.info(f"Símbolo cambiado a {symbol}")
        self.symbol_changed.emit(symbol)
        
        # En un sistema real, esto cargaría nuevos datos
        # Por ahora, regeneramos datos de muestra
        self.load_sample_data()
        
    def on_timeframe_changed(self, timeframe):
        """Maneja el cambio de timeframe"""
        if timeframe == self.timeframe:
            return
            
        self.timeframe = timeframe
        logger.info(f"Timeframe cambiado a {timeframe}")
        self.timeframe_changed.emit(timeframe)
        
        # En un sistema real, esto cargaría nuevos datos con el timeframe correcto
        # Por ahora, regeneramos datos de muestra
        self.load_sample_data()
        
    def on_add_indicator(self):
        """Abre diálogo para agregar un indicador"""
        if self.parent:
            self.parent.show_notification("Funcionalidad de indicadores en desarrollo", level="info")
        
    def set_data(self, data, symbol=None, timeframe=None):
        """Establece nuevos datos para el gráfico"""
        self.chart_data = data
        
        if symbol:
            self.symbol = symbol
            self.symbol_combo.setCurrentText(symbol)
            
        if timeframe:
            self.timeframe = timeframe
            self.timeframe_combo.setCurrentText(timeframe)
            
        self.update_chart()
