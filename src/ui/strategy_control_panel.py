from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QGroupBox
from PyQt5.QtCore import Qt

class StrategyControlPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Panel de Control de Estrategias")
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)
        self.strategies = {} # Dictionary to hold strategy widgets

        self.setup_ui()

    def setup_ui(self):
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<h2>Estrategias Activas</h2>"))
        header_layout.addStretch()
        self.main_layout.addLayout(header_layout)

        # Scroll Area for Strategies
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.strategies_container = QWidget()
        self.strategies_layout = QVBoxLayout(self.strategies_container)
        self.strategies_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.strategies_container)
        self.main_layout.addWidget(self.scroll_area)

        # Example: Add a dummy strategy for now
        self.add_strategy_widget("Estrategia de Arbitraje Triangular", "arbitraje_triangular_v1")
        self.add_strategy_widget("Estrategia de Scalping", "scalping_v2")

    def add_strategy_widget(self, name, strategy_id):
        strategy_group = QGroupBox(name)
        strategy_layout = QVBoxLayout(strategy_group)

        # Status and Switch (Placeholder for QSwitchButton)
        status_layout = QHBoxLayout()
        status_label = QLabel("Estado: Inactivo")
        status_layout.addWidget(status_label)
        # Placeholder for a real switch button
        toggle_button = QPushButton("Activar/Desactivar")
        toggle_button.clicked.connect(lambda: self.toggle_strategy(strategy_id, status_label))
        status_layout.addWidget(toggle_button)
        strategy_layout.addLayout(status_layout)

        # Configuration Button
        config_button = QPushButton("Configurar")
        config_button.clicked.connect(lambda: self.open_config_dialog(strategy_id))
        strategy_layout.addWidget(config_button)

        # Metrics (Placeholder)
        metrics_label = QLabel("Métricas: P&L: N/A, Drawdown: N/A")
        strategy_layout.addWidget(metrics_label)

        # Chart (Placeholder for ChartWidget)
        chart_label = QLabel("Gráfico de Rendimiento (Placeholder)")
        strategy_layout.addWidget(chart_label)

        # Logs (Placeholder)
        logs_label = QLabel("Logs: No hay logs recientes.")
        strategy_layout.addWidget(logs_label)

        strategy_group.setLayout(strategy_layout)
        self.strategies_layout.addWidget(strategy_group)
        self.strategies[strategy_id] = {
            "group": strategy_group,
            "status_label": status_label,
            "metrics_label": metrics_label,
            "logs_label": logs_label,
            "is_active": False
        }

    def toggle_strategy(self, strategy_id, status_label):
        strategy_info = self.strategies.get(strategy_id)
        if strategy_info:
            strategy_info["is_active"] = not strategy_info["is_active"]
            status_label.setText(f"Estado: {'Activo' if strategy_info['is_active'] else 'Inactivo'}")
            print(f"Estrategia {strategy_id} {'activada' if strategy_info['is_active'] else 'desactivada'}")
            # Here you would call a backend service to actually activate/deactivate the strategy

    def open_config_dialog(self, strategy_id):
        print(f"Abriendo diálogo de configuración para la estrategia: {strategy_id}")
        # Implement a QDialog for strategy specific configuration

    def update_strategy_status(self, strategy_id, status, metrics, logs):
        strategy_info = self.strategies.get(strategy_id)
        if strategy_info:
            strategy_info["status_label"].setText(f"Estado: {status}")
            strategy_info["metrics_label"].setText(f"Métricas: P&L: {metrics.get('pnl', 'N/A')}, Drawdown: {metrics.get('drawdown', 'N/A')}")
            strategy_info["logs_label"].setText(f"Logs: {logs}")
            # Update chart if a ChartWidget is integrated

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    panel = StrategyControlPanel()
    panel.show()
    sys.exit(app.exec_())
