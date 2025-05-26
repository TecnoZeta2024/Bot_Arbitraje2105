from PyQt5.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QRect,
    QSize,
    QSortFilterProxyModel,
    Qt,
    QVariant,
    pyqtSignal,
)
from PyQt5.QtGui import QColor, QMouseEvent, QPainter
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionButton,
    QStyleOptionViewItem,
    QTableView,
    QVBoxLayout,
    QWidget,
)


class OpportunitiesTableModel(QAbstractTableModel):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self._data = data
        self._headers = ["ID", "Par", "Exchange", "Rentabilidad (%)", "Riesgo", "Fecha", "Acciones"]
        self._expanded_rows = set() # Almacena los índices de las filas expandidas

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        # Si una fila está expandida, añade una fila extra para el detalle
        return len(self._data) + len(self._expanded_rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        # Determinar la fila real de datos, ajustando por filas expandidas
        row = index.row()
        for expanded_row_idx in sorted(list(self._expanded_rows)):
            if row > expanded_row_idx:
                row -= 1
            else:
                break

        if row >= len(self._data): # Esto es una fila de detalle
            return QVariant() # Las filas de detalle no tienen datos de celda normales

        # Si es una fila de detalle (expandida), y la columna no es la primera, no mostrar nada
        if index.row() in self._expanded_rows and index.column() > 0:
            return QVariant()
        
        # Si es la columna de acciones, no mostrar nada, el delegado se encargará
        if index.column() == self.columnCount() - 1 and index.row() not in self._expanded_rows:
            return QVariant()

        if role == Qt.DisplayRole:
            if index.row() in self._expanded_rows: # Es una fila de detalle
                if index.column() == 0: # Solo la primera columna de la fila de detalle
                    # Aquí puedes devolver un identificador para el delegado
                    return "DETALLE_OPORTUNIDAD"
                return QVariant()
            return str(self._data[row][index.column()])
        elif role == Qt.EditRole: # Para permitir la edición si es necesario
            return self._data[row][index.column()]
        elif role == Qt.UserRole: # Para datos subyacentes para ordenamiento/filtrado
            return self._data[row][index.column()]
        elif role == Qt.BackgroundRole:
            if index.row() in self._expanded_rows: # Fila de detalle
                return QColor(240, 240, 240) # Un color de fondo diferente para el detalle
            # Aplicar alertas visuales basadas en la rentabilidad
            if index.column() == 3: # Columna "Rentabilidad (%)"
                try:
                    profitability = float(self._data[row][index.column()])
                    if profitability >= 1.0: # Alta rentabilidad
                        return QColor(144, 238, 144) # Verde claro
                    elif profitability <= 0.4: # Riesgo elevado / Baja rentabilidad
                        return QColor(255, 182, 193) # Rojo claro
                except ValueError:
                    pass # Ignorar si no es un número
            return QVariant()
        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
            elif orientation == Qt.Vertical:
                # Ajustar el número de fila si es una fila de detalle
                row_idx = section
                for expanded_row_idx in sorted(list(self._expanded_rows)):
                    if section > expanded_row_idx:
                        row_idx -= 1
                    else:
                        break
                if section in self._expanded_rows:
                    return "" # No mostrar número para filas de detalle
                return str(row_idx + 1)
        return QVariant()

    def toggle_expansion(self, row_index):
        # Ajustar el row_index para que apunte a la fila de datos original
        original_row_index = row_index
        for expanded_row_idx in sorted(list(self._expanded_rows)):
            if row_index > expanded_row_idx:
                original_row_index -= 1
            else:
                break

        # Calcular el índice de la fila de detalle
        detail_row_index = original_row_index + 1
        for expanded_row_idx in sorted(list(self._expanded_rows)):
            if expanded_row_idx < original_row_index:
                detail_row_index += 1

        if detail_row_index in self._expanded_rows:
            self.beginRemoveRows(QModelIndex(), detail_row_index, detail_row_index)
            self._expanded_rows.remove(detail_row_index)
            self.endRemoveRows()
        else:
            self.beginInsertRows(QModelIndex(), detail_row_index, detail_row_index)
            self._expanded_rows.add(detail_row_index)
            self.endInsertRows()
        return detail_row_index in self._expanded_rows # Retorna el nuevo estado de expansión

    def is_detail_row(self, row_index):
        return row_index in self._expanded_rows

    def get_opportunity_data(self, row_index):
        # Ajustar el row_index para que apunte a la fila de datos original
        original_row_index = row_index
        for expanded_row_idx in sorted(list(self._expanded_rows)):
            if row_index > expanded_row_idx:
                original_row_index -= 1
            else:
                break
        if original_row_index < len(self._data):
            return self._data[original_row_index]
        return None

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        # Asegurarse de que la columna de acciones no se intente ordenar por su contenido
        if column == self.columnCount() - 1:
            return # No ordenar por la columna de acciones

        # Limpiar el estado de expansión antes de ordenar
        self._expanded_rows.clear()

        self._data = sorted(self._data, key=lambda x: x[column], reverse=(order == Qt.DescendingOrder))
        self.layoutChanged.emit()

class ButtonDelegate(QStyledItemDelegate):
    execute_clicked = pyqtSignal(str)
    analyze_clicked = pyqtSignal(str)

    def paint(self, painter, option, index):
        # Obtener el estilo del widget o de la aplicación
        style = option.widget.style() if option.widget else QApplication.style()

        if index.column() == index.model().columnCount() - 1:
            # Dibuja el fondo de la celda
            style.drawControl(QStyle.CE_ItemViewItem, option, painter, option.widget)

            # Calcula el tamaño y la posición de los botones
            button_width = option.rect.width() // 2 - 2 # Dividir el espacio para dos botones con un pequeño margen
            button_height = option.rect.height() - 4 # Pequeño margen vertical
            
            execute_rect = QRect(option.rect.x() + 2, option.rect.y() + 2, button_width, button_height)
            analyze_rect = QRect(option.rect.x() + button_width + 4, option.rect.y() + 2, button_width, button_height)

            # Dibuja el botón "Ejecutar"
            execute_option = QStyleOptionButton()
            execute_option.rect = execute_rect
            execute_option.text = "Ejecutar"
            execute_option.state = QStyle.State_Enabled | QStyle.State_Active # Asegura que el botón se vea habilitado y activo
            style.drawControl(QStyle.CE_PushButton, execute_option, painter, option.widget)

            # Dibuja el botón "Analizar"
            analyze_option = QStyleOptionButton()
            analyze_option.rect = analyze_rect
            analyze_option.text = "Analizar"
            analyze_option.state = QStyle.State_Enabled | QStyle.State_Active # Asegura que el botón se vea habilitado y activo
            style.drawControl(QStyle.CE_PushButton, analyze_option, painter, option.widget)
        else:
            super().paint(painter, option, index)

    def editorEvent(self, event, model, option, index):
        # Asegurarse de que el modelo sea el modelo de datos real (OpportunitiesTableModel)
        source_model = model.sourceModel() if isinstance(model, QSortFilterProxyModel) else model

        if event.type() == QMouseEvent.MouseButtonRelease and index.column() == source_model.columnCount() - 1:
            opportunity_id = source_model.data(index.sibling(index.row(), 0), Qt.DisplayRole)
            
            button_width = option.rect.width() // 2 - 2
            execute_rect = QRect(option.rect.x() + 2, option.rect.y() + 2, button_width, option.rect.height() - 4)
            analyze_rect = QRect(option.rect.x() + button_width + 4, option.rect.y() + 2, button_width, option.rect.height() - 4)

            # Asegurarse de que el evento sea QMouseEvent para acceder a pos()
            if isinstance(event, QMouseEvent):
                if execute_rect.contains(event.pos()):
                    self.execute_clicked.emit(opportunity_id)
                    return True
                elif analyze_rect.contains(event.pos()):
                    self.analyze_clicked.emit(opportunity_id)
                    return True
        return super().editorEvent(event, model, option, index)

class ExpandableDelegate(QStyledItemDelegate):
    toggle_expansion_signal = pyqtSignal(int) # Emite el índice de la fila de datos original

    def paint(self, painter, option, index):
        # Asegurarse de que el modelo sea el modelo de datos real (OpportunitiesTableModel)
        source_model = index.model().sourceModel() if isinstance(index.model(), QSortFilterProxyModel) else index.model()

        if source_model.is_detail_row(index.row()):
            # Es una fila de detalle, dibujar el contenido expandido
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)

            # Dibujar el fondo de la fila de detalle
            painter.fillRect(option.rect, QColor(240, 240, 240)) # Color de fondo para el detalle

            # Obtener los datos de la oportunidad de la fila principal
            # El índice de la fila en el modelo proxy es diferente al del modelo fuente
            # Necesitamos el índice de la fila de datos original en el modelo fuente
            original_row_index = index.row()
            # Ajustar el original_row_index para que apunte a la fila de datos original
            # Esto es necesario porque _expanded_rows se basa en los índices del modelo fuente
            # y el index.row() que recibe el delegado es del proxy model.
            # La lógica de ajuste ya está en el modelo, así que la reutilizamos.
            opportunity_data = source_model.get_opportunity_data(original_row_index)
            
            if opportunity_data:
                detail_text = f"Detalles de Oportunidad:\n" \
                              f"ID: {opportunity_data[0]}\n" \
                              f"Par: {opportunity_data[1]}\n" \
                              f"Exchange: {opportunity_data[2]}\n" \
                              f"Rentabilidad: {opportunity_data[3]}%\n" \
                              f"Riesgo: {opportunity_data[4]}\n" \
                              f"Fecha: {opportunity_data[5]}\n" \
                              f"Información Adicional: Esta es una oportunidad de arbitraje triangular con un potencial de {opportunity_data[3]}% de ganancia."
                
                # Dibujar el texto de detalle
                text_rect = option.rect.adjusted(10, 5, -10, -5) # Margen interno
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, detail_text)

            painter.restore()
        else:
            # Es una fila normal, usar el delegado base para dibujar
            super().paint(painter, option, index)

    def sizeHint(self, option, index):
        # Asegurarse de que el modelo sea el modelo de datos real (OpportunitiesTableModel)
        source_model = index.model().sourceModel() if isinstance(index.model(), QSortFilterProxyModel) else index.model()

        if source_model.is_detail_row(index.row()):
            # Altura mayor para la fila de detalle
            return QSize(option.rect.width(), 120) # Altura fija para el detalle
        return super().sizeHint(option, index)

    def editorEvent(self, event, model, option, index):
        # Asegurarse de que el modelo sea el modelo de datos real (OpportunitiesTableModel)
        source_model = model.sourceModel() if isinstance(model, QSortFilterProxyModel) else model

        if event.type() == QMouseEvent.MouseButtonRelease and index.column() == 0: # Clic en la primera columna para expandir/contraer
            if not source_model.is_detail_row(index.row()): # Solo si no es una fila de detalle
                # Mapear el índice de la fila del proxy al índice del modelo original
                source_index = model.mapToSource(index)
                self.toggle_expansion_signal.emit(source_index.row())
                return True
        return super().editorEvent(event, model, option, index)

class OpportunitiesTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)

        # Datos de ejemplo
        example_data = [
            ["OPP001", "BTC/USDT", "Binance", 0.5, "Bajo", "2025-05-25"],
            ["OPP002", "ETH/USDT", "Kraken", 1.2, "Medio", "2025-05-25"],
            ["OPP003", "ADA/BTC", "Coinbase", 0.8, "Bajo", "2025-05-24"],
            ["OPP004", "XRP/USDT", "Binance", 0.3, "Alto", "2025-05-24"],
            ["OPP005", "LTC/EUR", "Coinbase", 1.5, "Bajo", "2025-05-25"], # Debería ser verde claro
            ["OPP006", "DOGE/USD", "Binance", 0.2, "Muy Alto", "2025-05-25"], # Debería ser rojo claro
            ["OPP007", "SOL/USDT", "Kraken", 0.9, "Medio", "2025-05-24"], # Sin color especial
        ]
        
        # Crear e instanciar el modelo base
        self._model = OpportunitiesTableModel(example_data)
        
        # Crear e instanciar el modelo proxy para filtrado y ordenamiento
        self._proxy_model = QSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive) # Filtrado no sensible a mayúsculas/minúsculas
        
        self.setModel(self._proxy_model)

        # Configurar el delegado para la columna de acciones
        self.action_delegate = ButtonDelegate(self)
        self.action_delegate.execute_clicked.connect(self.on_execute_opportunity)
        self.action_delegate.analyze_clicked.connect(self.on_analyze_opportunity)
        self.setItemDelegateForColumn(self._model.columnCount() - 1, self.action_delegate)

        # Configurar el delegado expandible para la primera columna
        self.expandable_delegate = ExpandableDelegate(self)
        self.expandable_delegate.toggle_expansion_signal.connect(self.toggle_row_expansion)
        self.setItemDelegateForColumn(0, self.expandable_delegate) # Aplicar a la primera columna

        self.resizeColumnsToContents()
        header = self.horizontalHeader()
        if header: # Verificar que el header no sea None
            header.setStretchLastSection(True)

    def toggle_row_expansion(self, row_index):
        # Mapear el índice de la fila del proxy al índice del modelo original
        source_index = self._proxy_model.mapToSource(self._proxy_model.index(row_index, 0))
        if source_index.isValid():
            is_expanded = self._model.toggle_expansion(source_index.row())
            # Actualizar la vista para reflejar el cambio de altura
            self.updateGeometries()
            self.resizeRowsToContents() # Ajustar la altura de las filas
            if is_expanded:
                # Asegurarse de que la fila expandida sea visible
                self.scrollTo(self._proxy_model.index(row_index + 1, 0), QTableView.EnsureVisible)


    def set_filter_text(self, text):
        self._proxy_model.setFilterRegExp(text)

    def set_filter_column(self, column_index):
        self._proxy_model.setFilterKeyColumn(column_index)

    def sort_by_column(self, column_index, order):
        self._proxy_model.sort(column_index, order)

    def on_execute_opportunity(self, opportunity_id):
        print(f"Ejecutar oportunidad: {opportunity_id}")
        # Aquí se integraría la lógica para iniciar el trading
        pass

    def on_analyze_opportunity(self, opportunity_id):
        print(f"Analizar oportunidad: {opportunity_id}")
        # Aquí se integraría la lógica para abrir el análisis detallado
        pass
