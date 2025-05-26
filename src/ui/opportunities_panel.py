from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class OpportunitiesTableModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []
        self._headers = ["ID", "Par", "Exchange", "Tipo", "Profit %", "Volumen", "Confianza IA", "Acciones"]

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self._headers)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._data[index.row()][index.column()])
        return QVariant()

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
            else:
                return str(section + 1)
        return QVariant()

    def update_data(self, new_data):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()

class OpportunitiesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.opportunities_data = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Filter and Sort Controls
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Filtrar por Par:"))
        self.filter_pair_input = QLineEdit()
        controls_layout.addWidget(self.filter_pair_input)
        controls_layout.addWidget(QLabel("Ordenar por:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["ID", "Par", "Profit %", "Confianza IA"])
        controls_layout.addWidget(self.sort_combo)
        self.sort_order_button = QPushButton("Asc/Desc")
        controls_layout.addWidget(self.sort_order_button)
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)

        # Table View
        self.table_view = QTableView()
        self.model = OpportunitiesTableModel(self.opportunities_data)
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.table_view)

        # Quick Actions (Example buttons)
        actions_layout = QHBoxLayout()
        self.execute_button = QPushButton("Ejecutar Oportunidad")
        self.analyze_button = QPushButton("Analizar Detalle")
        actions_layout.addWidget(self.execute_button)
        actions_layout.addWidget(self.analyze_button)
        actions_layout.addStretch()
        main_layout.addLayout(actions_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("Panel de Oportunidades")

        # Connect signals
        self.filter_pair_input.textChanged.connect(self.apply_filters_and_sort)
        self.sort_combo.currentIndexChanged.connect(self.apply_filters_and_sort)
        self.sort_order_button.clicked.connect(self.toggle_sort_order)

    def update_opportunities(self, new_opportunities_data):
        self.opportunities_data = new_opportunities_data
        self.apply_filters_and_sort()

    def apply_filters_and_sort(self):
        filtered_data = self.opportunities_data

        # Apply filter
        filter_text = self.filter_pair_input.text().lower()
        if filter_text:
            filtered_data = [
                row for row in filtered_data if filter_text in str(row[1]).lower() # Assuming 'Par' is at index 1
            ]

        # Apply sort
        sort_column_name = self.sort_combo.currentText()
        sort_column_index = self.model._headers.index(sort_column_name)
        
        # Determine sort order (ascending by default, toggle with button)
        # For simplicity, let's assume a simple toggle for now.
        # In a real app, you'd store the state.
        is_ascending = True # Placeholder, will be managed by toggle_sort_order

        # Sort logic (example, needs refinement for different data types)
        if sort_column_name == "Profit %" or sort_column_name == "Confianza IA":
            filtered_data.sort(key=lambda x: float(x[sort_column_index]) if isinstance(x[sort_column_index], (int, float)) or (isinstance(x[sort_column_index], str) and x[sort_column_index].replace('.', '', 1).isdigit()) else -float('inf'), reverse=not is_ascending)
        else:
            filtered_data.sort(key=lambda x: str(x[sort_column_index]), reverse=not is_ascending)

        self.model.update_data(filtered_data)

    def toggle_sort_order(self):
        # This method should toggle an internal state for sorting order
        # and then call apply_filters_and_sort again.
        # For now, it's a placeholder.
        print("Toggle sort order clicked!")
        self.apply_filters_and_sort() # Re-apply sort with toggled order (needs state)

    def highlight_alerts(self):
        # This method would apply visual alerts based on opportunity data
        # e.g., change row/cell background color based on profit % or confidence
        pass

if __name__ == '__main__':
    import sys

    from PyQt5.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    main_win = QMainWindow()
    panel = OpportunitiesPanel()
    main_win.setCentralWidget(panel)
    main_win.resize(800, 600)
    main_win.show()

    # Example data update
    example_data = [
        [1, "BTC/USDT", "Binance", "Triangular", "0.5", "1000", "95%", "Acción 1"],
        [2, "ETH/USDT", "Coinbase", "Cross-Exchange", "1.2", "500", "88%", "Acción 2"],
        [3, "ADA/BTC", "Kraken", "Triangular", "0.3", "2000", "70%", "Acción 3"],
        [4, "XRP/USDT", "Binance", "Cross-Exchange", "0.8", "750", "92%", "Acción 4"],
    ]
    panel.update_opportunities(example_data)

    sys.exit(app.exec_())
