import mplfinance as mpf
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QWidget


class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111) # Initialize with a single subplot

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.mc = mpf.make_addplot([], panel=0) # Placeholder for main chart
        self.volume_plot = mpf.make_addplot([], panel=1, type='bar', color='gray') # Placeholder for volume

        self.figure.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)

        self.press = None
        self.xlim = None
        self.ylim = None

    def update_chart(self, data, indicators=None, signals=None):
        self.figure.clear()
        gs = self.figure.add_gridspec(3, 1, height_ratios=[3, 1, 1]) # 3 rows, 1 column, ratios for main, volume, and empty space
        self.ax = self.figure.add_subplot(gs[0, 0]) # Main chart on first row
        self.volume_ax = self.figure.add_subplot(gs[1, 0], sharex=self.ax) # Volume chart on second row, sharing x-axis with main chart
        self.figure.tight_layout() # Adjust layout to prevent overlap

        addplots = []
        if indicators:
            for indicator_data in indicators:
                addplots.append(mpf.make_addplot(indicator_data['data'], ax=self.ax, panel=indicator_data.get('panel', 0), color=indicator_data.get('color', 'blue'), linestyle=indicator_data.get('linestyle', '-')))

        if signals:
            for signal_data in signals:
                addplots.append(mpf.make_addplot(signal_data['data'], type='scatter', ax=self.ax, marker=signal_data.get('marker', '^'), color=signal_data.get('color', 'green'), markersize=signal_data.get('markersize', 100), panel=signal_data.get('panel', 0)))

        mpf.plot(data, type='candle', ax=self.ax, volume=self.volume_ax, addplot=addplots, style='yahoo',
                 panel_ratios=(3,1), figscale=1.0, figratio=(10,7),
                 returnfig=True,
                 axtitle='Gráfico de Velas',
                 ylabel='Precio',
                 ylabel_lower='Volumen')
        
        # Hide x-axis ticks and labels for the main chart to prevent overlap with volume chart
        self.ax.xaxis.set_visible(False)

        self.canvas.draw()

    def on_scroll(self, event):
        xlim = self.ax.get_xlim()
        xdata = event.xdata
        if xdata is None:
            return

        scale_factor = 1.5 if event.button == 'up' else 1/1.5
        new_width = (xlim[1] - xlim[0]) * scale_factor
        rel_x = (xdata - xlim[0]) / (xlim[1] - xlim[0])
        new_xlim = (xdata - rel_x * new_width, xdata + (1 - rel_x) * new_width)

        self.ax.set_xlim(new_xlim)
        self.canvas.draw_idle()

    def on_press(self, event):
        if event.inaxes != self.ax: return
        self.press = event.xdata, event.ydata
        self.xlim = self.ax.get_xlim()
        self.ylim = self.ax.get_ylim()

    def on_motion(self, event):
        if self.press is None or event.inaxes != self.ax: return
        if self.xlim is None or self.ylim is None: return # Add this check
        
        xpress, ypress = self.press
        dx = event.xdata - xpress
        dy = event.ydata - ypress

        self.ax.set_xlim(self.xlim[0] - dx, self.xlim[1] - dx)
        self.ax.set_ylim(self.ylim[0] - dy, self.ylim[1] - dy)
        self.canvas.draw_idle()

    def on_release(self, event):
        self.press = None
        self.xlim = None
        self.ylim = None
