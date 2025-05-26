from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
import pyqtgraph as pg
import numpy as np
import pandas as pd
from collections import OrderedDict

class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.indicators = OrderedDict() # Para almacenar los indicadores activos
        self.signals = [] # Para almacenar las señales de trading
        self.data = None # Para almacenar los datos OHLC
        self.candle_plot_widget = pg.PlotWidget()
        self.volume_plot_widget = pg.PlotWidget()
        self.performance_plot_widget = pg.PlotWidget() # Nuevo PlotWidget para rendimiento
        self.init_ui()
        # self.plot_data_example() # Comentar o eliminar esta línea si no se necesitan datos de ejemplo al inicio

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Configurar el PlotWidget principal para las velas (opcional, se puede ocultar si solo es rendimiento)
        self.candle_plot_widget.setMouseEnabled(x=True, y=True)
        self.candle_plot_widget.showGrid(x=True, y=True)
        self.candle_plot_widget.addLegend()
        self.candle_plot_widget.setLabel('left', 'Precio')
        self.candle_plot_widget.setLabel('bottom', 'Tiempo')
        self.candle_plot_widget.hide() # Ocultar por defecto si el enfoque es rendimiento

        # Configurar el PlotWidget para el volumen (opcional, se puede ocultar)
        self.volume_plot_widget.setMouseEnabled(x=True, y=True)
        self.volume_plot_widget.showGrid(x=True, y=True)
        self.volume_plot_widget.setLabel('left', 'Volumen')
        self.volume_plot_widget.setLabel('bottom', 'Tiempo')
        self.volume_plot_widget.setMaximumHeight(200)
        self.volume_plot_widget.hide() # Ocultar por defecto

        # Sincronizar los ejes X
        self.volume_plot_widget.setXLink(self.candle_plot_widget)

        # Configurar el nuevo PlotWidget para gráficos de rendimiento
        self.performance_plot_widget.setMouseEnabled(x=True, y=True)
        self.performance_plot_widget.showGrid(x=True, y=True)
        self.performance_plot_widget.addLegend()
        self.performance_plot_widget.setLabel('left', 'Valor')
        self.performance_plot_widget.setLabel('bottom', 'Tiempo')
        
        main_layout.addWidget(self.candle_plot_widget)
        main_layout.addWidget(self.volume_plot_widget)
        main_layout.addWidget(self.performance_plot_widget) # Añadir el widget de rendimiento
        self.setLayout(main_layout)

    def plot_ohlc_data(self, data, volume_data):
        """
        Dibuja datos OHLC (velas) y volumen.
        :param data: Array numpy con datos OHLC (time, open, close, high, low).
        :param volume_data: Array numpy con datos de volumen (time, volume).
        """
        self.candle_plot_widget.show()
        self.volume_plot_widget.show()
        self.performance_plot_widget.hide() # Ocultar el de rendimiento si se muestran OHLC

        self.candle_plot_widget.clear()
        self.volume_plot_widget.clear()

        times = data['time']
        opens = data['open']
        closes = data['close']
        highs = data['high']
        lows = data['low']

        self.candle_plot_widget.addItem(pg.PlotDataItem(x=times, open=opens, close=closes, high=highs, low=lows, brush='g', pen='w', name='Velas'))

        volume_times = volume_data[:, 0]
        volumes = volume_data[:, 1]

        volume_colors = []
        for i in range(len(data)):
            if data['close'][i] > data['open'][i]:
                volume_colors.append('g')
            else:
                volume_colors.append('r')
        
        self.volume_plot_widget.addItem(pg.BarGraphItem(x=volume_times, height=volumes, width=0.8, brushes=volume_colors))

        self.data = pd.DataFrame({
            'time': data['time'],
            'open': data['open'],
            'high': data['high'],
            'low': data['low'],
            'close': data['close'],
            'volume': volumes
        })
        self.update_indicators()
        self.update_signals()

    def plot_performance_data(self, times, values, name="Rendimiento", color='c'):
        """
        Dibuja un gráfico de línea para datos de rendimiento (ej. PnL, capital).
        :param times: Lista o array de valores para el eje X (tiempo).
        :param values: Lista o array de valores para el eje Y (rendimiento).
        :param name: Nombre de la curva para la leyenda.
        :param color: Color de la línea.
        """
        self.candle_plot_widget.hide()
        self.volume_plot_widget.hide()
        self.performance_plot_widget.show() # Mostrar el de rendimiento

        self.performance_plot_widget.clear()
        self.performance_plot_widget.plot(times, values, pen=pg.mkPen(color, width=2), name=name)
        print(f"Gráfico de rendimiento '{name}' actualizado.")

    def plot_data_example(self):
        # Datos de ejemplo para velas (OHLC) y volumen
        data = np.array([
            (1, 10, 12, 13, 9),
            (2, 12, 11, 12.5, 10.5),
            (3, 11, 13, 14, 10),
            (4, 13, 12.5, 13.5, 11.5),
            (5, 12.5, 14, 14.5, 12),
            (6, 14, 13.5, 14, 13),
            (7, 13.5, 15, 15.5, 13),
            (8, 15, 14.5, 15, 14),
            (9, 14.5, 16, 16.5, 14),
            (10, 16, 15.5, 16, 15)
        ], dtype=[('time', float), ('open', float), ('close', float), ('high', float), ('low', float)])
        
        volume_data = np.array([
            (1, 100), (2, 120), (3, 90), (4, 150), (5, 110),
            (6, 130), (7, 80), (8, 160), (9, 100), (10, 140)
        ])
        self.plot_ohlc_data(data, volume_data)

        # Añadir señales de ejemplo para verificación
        self.clear_signals()
        self.add_signal(time=2, value=10.5, signal_type='buy', color='g', symbol='t', size=15)
        self.add_signal(time=5, value=14.5, signal_type='sell', color='r', symbol='t1', size=15)
        self.add_signal(time=8, value=14.0, signal_type='info', color='y', symbol='s', size=12)
        self.update_signals()

        # Ejemplo de datos de rendimiento
        perf_times = np.arange(1, 11)
        perf_values = np.array([1000, 1010, 1005, 1020, 1015, 1030, 1025, 1040, 1035, 1050])
        self.plot_performance_data(perf_times, perf_values, name="Capital Total", color='c')


    def add_signal(self, time, value, signal_type='buy', color='g', symbol='o', size=10):
        """
        Añade una señal al gráfico.
        :param time: El tiempo (índice X) de la señal.
        :param value: El valor (índice Y) de la señal.
        :param signal_type: Tipo de señal (ej. 'buy', 'sell', 'info').
        :param color: Color de la señal (ej. 'g' para verde, 'r' para rojo).
        :param symbol: Símbolo a usar para la señal (ej. 'o' para círculo, 't' para triángulo).
        :param size: Tamaño del símbolo.
        """
        self.signals.append({
            'time': time,
            'value': value,
            'type': signal_type,
            'color': color,
            'symbol': symbol,
            'size': size
        })
        # No llamar update_signals aquí, se llamará una vez después de añadir todas las señales

    def clear_signals(self):
        """Limpia todas las señales del gráfico."""
        self.signals = []
        # No llamar update_signals aquí, se llamará una vez después de limpiar

    def update_signals(self):
        """Dibuja o actualiza las señales en el gráfico."""
        # Limpiar señales existentes antes de redibujar
        for item in self.candle_plot_widget.items():
            if isinstance(item, pg.ScatterPlotItem) and item.name() == 'Signals':
                self.candle_plot_widget.removeItem(item)

        if not self.signals:
            return

        times = [s['time'] for s in self.signals]
        values = [s['value'] for s in self.signals]
        colors = [s['color'] for s in self.signals]
        symbols = [s['symbol'] for s in self.signals]
        sizes = [s['size'] for s in self.signals]

        scatter = pg.ScatterPlotItem(
            x=times, y=values,
            pen=pg.mkPen(None),
            brush=[pg.mkBrush(c) for c in colors],
            symbol=symbols,
            size=sizes,
            name='Signals'
        )
        self.candle_plot_widget.addItem(scatter)
        print(f"Señales actualizadas: {len(self.signals)} señales mostradas.")

    def add_indicator(self, name, indicator_type, params=None, plot_item=None):
        if plot_item is None:
            plot_item = self.candle_plot_widget

        if params is None:
            params = {}

        if indicator_type == 'SMA':
            period = params.get('period', 10)
            if self.data is not None and not self.data.empty:
                sma_values = self.data['close'].rolling(window=period).mean()
                curve = plot_item.plot(self.data['time'].values, sma_values.values, pen=pg.mkPen('blue', width=2), name=f'SMA-{period}')
                self.indicators[name] = {'type': indicator_type, 'params': params, 'curve': curve, 'plot_item': plot_item}
                print(f"Indicador {name} (SMA-{period}) añadido.")
            else:
                print("No hay datos para calcular SMA.")
        # Aquí se pueden añadir más tipos de indicadores (EMA, RSI, MACD, etc.)
        else:
            print(f"Tipo de indicador '{indicator_type}' no soportado.")

    def remove_indicator(self, name):
        if name in self.indicators:
            indicator_info = self.indicators.pop(name)
            indicator_info['plot_item'].removeItem(indicator_info['curve'])
            print(f"Indicador {name} removido.")
        else:
            print(f"Indicador {name} no encontrado.")

    def update_indicators(self):
        # Limpiar indicadores existentes antes de redibujar
        for name in list(self.indicators.keys()):
            self.remove_indicator(name)

        # Añadir indicadores de ejemplo
        # self.add_indicator('SMA_10', 'SMA', {'period': 10}) # Comentar o eliminar si no se necesitan indicadores de ejemplo
        # self.add_indicator('SMA_20', 'SMA', {'period': 20}, plot_item=self.candle_plot_widget) # Comentar o eliminar
