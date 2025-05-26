import sys
import random # Para simular datos
import sys
import random # Para simular datos
import numpy as np # Para simular datos de rendimiento
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QScrollArea,
    QListWidget, QListWidgetItem, QDialog, QFormLayout, QLineEdit, QPushButton,
    QDialogButtonBox, QStackedWidget, QTextEdit # Importar QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, QDateTime # Importar QDateTime para timestamps
from .chart_widget import ChartWidget # Importar ChartWidget

class StrategyControlPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Control de Estrategias")
        self.strategies_data = self.load_strategies_data() # Cargar datos de estrategias
        self.chart_widgets = {} # Diccionario para almacenar los ChartWidget por estrategia
        self.log_widgets = {} # Diccionario para almacenar los QTextEdit por estrategia
        self.init_ui()
        self.init_metrics_timer() # Inicializar el temporizador de métricas
        self.init_performance_timer() # Inicializar el temporizador de rendimiento

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Layout superior para la lista de estrategias y métricas
        top_layout = QHBoxLayout()

        # Lista de estrategias
        strategy_list_container = QVBoxLayout()
        strategy_list_container.addWidget(QLabel("<h3>Estrategias</h3>"))
        self.strategy_list_widget = QListWidget(self)
        self.strategy_list_widget.itemClicked.connect(self.on_strategy_selected)
        strategy_list_container.addWidget(self.strategy_list_widget)
        top_layout.addLayout(strategy_list_container)

        # Sección para mostrar métricas en tiempo real
        metrics_group_layout = QVBoxLayout()
        metrics_group_layout.addWidget(QLabel("<h3>Métricas en Tiempo Real</h3>"))

        self.pnl_label = QLabel("PnL: $0.00")
        self.operations_label = QLabel("Operaciones: 0")
        self.drawdown_label = QLabel("Drawdown: 0.00%")

        metrics_group_layout.addWidget(self.pnl_label)
        metrics_group_layout.addWidget(self.operations_label)
        metrics_group_layout.addWidget(self.drawdown_label)
        top_layout.addLayout(metrics_group_layout)

        main_layout.addLayout(top_layout)

        # Sección para gráficos de rendimiento
        main_layout.addWidget(QLabel("<h3>Gráficos de Rendimiento</h3>"))
        self.performance_chart_stacked_widget = QStackedWidget(self)
        main_layout.addWidget(self.performance_chart_stacked_widget)

        # Sección para logs por estrategia
        main_layout.addWidget(QLabel("<h3>Logs por Estrategia</h3>"))
        self.strategy_logs_stacked_widget = QStackedWidget(self)
        main_layout.addWidget(self.strategy_logs_stacked_widget)

        self.populate_strategy_list()
        self.create_performance_charts() # Crear los gráficos de rendimiento
        self.create_strategy_log_widgets() # Crear los widgets de log

    def load_strategies_data(self):
        # Ejemplo de datos de estrategias con parámetros
        return {
            "Estrategia de Arbitraje Triangular": {
                "active": True,
                "params": {
                    "Umbral de Oportunidad": "0.001",
                    "Volumen Mínimo": "100",
                    "Exchange Principal": "Binance"
                },
                "performance_data": [], # Inicializar datos de rendimiento
                "logs": [] # Inicializar lista de logs
            },
            "Estrategia de Scalping de Volumen": {
                "active": False,
                "params": {
                    "Volumen Mínimo": "500",
                    "Intervalo de Tiempo": "1m",
                    "Take Profit %": "0.0005"
                },
                "performance_data": [],
                "logs": []
            },
            "Estrategia de Day Trading Simple": {
                "active": True,
                "params": {
                    "Capital por Operación": "1000",
                    "Stop Loss %": "0.01",
                    "Indicador Principal": "RSI"
                },
                "performance_data": [],
                "logs": []
            },
            "Estrategia de Reversión a la Media": {
                "active": False,
                "params": {
                    "Ventana Media": "20",
                    "Desviación Estándar": "2",
                    "Activo Base": "BTC"
                },
                "performance_data": [],
                "logs": []
            },
            "Estrategia de Seguimiento de Tendencia": {
                "active": True,
                "params": {
                    "Periodo EMA": "50",
                    "Periodo MACD": "12,26,9",
                    "Confirmación": "ADX"
                },
                "performance_data": [],
                "logs": []
            },
        }

    def populate_strategy_list(self):
        self.strategy_list_widget.clear()
        for name, data in self.strategies_data.items():
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if data["active"] else Qt.CheckState.Unchecked)
            self.strategy_list_widget.addItem(item)

    def create_performance_charts(self):
        for name in self.strategies_data.keys():
            chart_widget = ChartWidget(self)
            self.chart_widgets[name] = chart_widget
            self.performance_chart_stacked_widget.addWidget(chart_widget)
            # Inicializar con datos de ejemplo para que el gráfico se muestre
            self.update_performance_chart(name)

    def create_strategy_log_widgets(self):
        for name in self.strategies_data.keys():
            log_text_edit = QTextEdit(self)
            log_text_edit.setReadOnly(True) # Hacer el QTextEdit de solo lectura
            self.log_widgets[name] = log_text_edit
            self.strategy_logs_stacked_widget.addWidget(log_text_edit)

    def add_log_message(self, strategy_name, message):
        if strategy_name in self.log_widgets:
            timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
            log_entry = f"[{timestamp}] {message}"
            self.strategies_data[strategy_name]["logs"].append(log_entry)
            # Limitar el número de logs para evitar sobrecarga
            if len(self.strategies_data[strategy_name]["logs"]) > 100:
                self.strategies_data[strategy_name]["logs"] = self.strategies_data[strategy_name]["logs"][-100:]
            
            # Actualizar el QTextEdit si es la estrategia actualmente visible
            if self.strategy_logs_stacked_widget.currentWidget() == self.log_widgets[strategy_name]:
                self.log_widgets[strategy_name].append(log_entry)

    def on_strategy_selected(self, item):
        strategy_name = item.text()
        # Manejar el cambio de estado del checkbox
        new_state = item.checkState() == Qt.CheckState.Checked
        self.strategies_data[strategy_name]["active"] = new_state
        self.add_log_message(strategy_name, f"Estrategia {'activada' if new_state else 'desactivada'}")

        # Mostrar el gráfico de rendimiento de la estrategia seleccionada
        if strategy_name in self.chart_widgets:
            index = self.performance_chart_stacked_widget.indexOf(self.chart_widgets[strategy_name])
            self.performance_chart_stacked_widget.setCurrentIndex(index)
            self.add_log_message(strategy_name, f"Mostrando gráfico para: {strategy_name}")

        # Mostrar los logs de la estrategia seleccionada
        if strategy_name in self.log_widgets:
            index = self.strategy_logs_stacked_widget.indexOf(self.log_widgets[strategy_name])
            self.strategy_logs_stacked_widget.setCurrentIndex(index)
            # Cargar logs existentes al seleccionar la estrategia
            self.log_widgets[strategy_name].clear()
            for log_entry in self.strategies_data[strategy_name]["logs"]:
                self.log_widgets[strategy_name].append(log_entry)
            self.add_log_message(strategy_name, f"Mostrando logs para: {strategy_name}")

        # Abrir diálogo de configuración al hacer clic en el nombre de la estrategia
        self.show_strategy_config_dialog(strategy_name)

    def show_strategy_config_dialog(self, strategy_name):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Configuración de {strategy_name}")
        
        layout = QFormLayout(dialog)
        
        strategy_params = self.strategies_data[strategy_name]["params"]
        
        # Diccionario para almacenar los QLineEdit para fácil acceso
        self.param_editors = {} 
        
        for param_name, param_value in strategy_params.items():
            label = QLabel(param_name + ":")
            editor = QLineEdit(str(param_value))
            layout.addRow(label, editor)
            self.param_editors[param_name] = editor # Guardar referencia al editor
            
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_strategy_config(strategy_name, dialog))
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(button_box)
        
        dialog.exec_()

    def save_strategy_config(self, strategy_name, dialog):
        # Guardar los valores editados de los parámetros
        for param_name, editor in self.param_editors.items():
            self.strategies_data[strategy_name]["params"][param_name] = editor.text()
        
        self.add_log_message(strategy_name, f"Configuración guardada:")
        for param_name, value in self.strategies_data[strategy_name]["params"].items():
            self.add_log_message(strategy_name, f"  {param_name}: {value}")
        
        dialog.accept()

    def init_metrics_timer(self):
        self.metrics_timer = QTimer(self)
        self.metrics_timer.setInterval(2000)  # Actualizar cada 2 segundos
        self.metrics_timer.timeout.connect(self.update_realtime_metrics)
        self.metrics_timer.start()

    def update_realtime_metrics(self):
        # Simular datos en tiempo real
        pnl = random.uniform(-100.0, 500.0)
        operations = random.randint(0, 100)
        drawdown = random.uniform(0.0, 10.0)

        self.pnl_label.setText(f"PnL: ${pnl:.2f}")
        self.operations_label.setText(f"Operaciones: {operations}")
        self.drawdown_label.setText(f"Drawdown: {drawdown:.2f}%")
        
        # Añadir un log de métricas para la estrategia activa (si hay alguna seleccionada)
        current_strategy_item = self.strategy_list_widget.currentItem()
        if current_strategy_item:
            strategy_name = current_strategy_item.text()
            self.add_log_message(strategy_name, f"Métricas actualizadas: PnL=${pnl:.2f}, Operaciones={operations}")

    def init_performance_timer(self):
        self.performance_timer = QTimer(self)
        self.performance_timer.setInterval(5000) # Actualizar gráficos cada 5 segundos
        self.performance_timer.timeout.connect(self.update_all_performance_charts)
        self.performance_timer.start()

    def update_all_performance_charts(self):
        for strategy_name in self.strategies_data.keys():
            self.update_performance_chart(strategy_name)

    def update_performance_chart(self, strategy_name):
        if strategy_name not in self.chart_widgets:
            return

        # Simular la evolución del capital/PnL
        current_data = self.strategies_data[strategy_name]["performance_data"]
        if not current_data:
            # Empezar con un capital inicial
            current_data.append((0, 1000.0))
        else:
            last_time, last_value = current_data[-1]
            new_time = last_time + 1
            # Simular un cambio aleatorio en el valor
            change = random.uniform(-10.0, 15.0)
            new_value = max(0, last_value + change) # Asegurar que el valor no sea negativo
            current_data.append((new_time, new_value))
        
        # Mantener solo los últimos 50 puntos de datos para no sobrecargar el gráfico
        if len(current_data) > 50:
            current_data = current_data[-50:]
        
        self.strategies_data[strategy_name]["performance_data"] = current_data

        times = [d[0] for d in current_data]
        values = [d[1] for d in current_data]

        self.chart_widgets[strategy_name].plot_performance_data(times, values, name=f"Rendimiento {strategy_name}")
        self.add_log_message(strategy_name, f"Gráfico de rendimiento actualizado. Último valor: {values[-1]:.2f}")

    def on_strategy_toggle(self, strategy_name, state): # Esta función ya no es necesaria con el nuevo enfoque de QListWidget
        pass # La lógica de toggle ahora está en on_strategy_selected

if __name__ == '__main__':
    app = QApplication(sys.argv)
    panel = StrategyControlPanel()
    panel.show()
    sys.exit(app.exec_())
