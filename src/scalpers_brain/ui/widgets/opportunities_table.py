"""
Tabla de oportunidades de trading para Scalper's Brain
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, QSortFilterProxyModel, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QMenu, QAction
from PyQt5.QtGui import QColor

logger = logging.getLogger(__name__)

class OpportunitiesModel(QAbstractTableModel):
    """Modelo de datos para la tabla de oportunidades"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.headers = ["ID", "Símbolo", "Tipo", "Precio", "Confianza", "Estrategia", "Hora"]
        self.opportunities: List[Dict[str, Any]] = []
        
        # Cargar algunos datos de ejemplo
        self._load_sample_data()
        
    def _load_sample_data(self):
        """Carga datos de ejemplo para la tabla"""
        self.opportunities = [
            {
                'id': '001',
                'symbol': 'BTCUSDT',
                'type': 'COMPRA',
                'price': 50240.50,
                'confidence': 85.3,
                'strategy': 'Scalping',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            },
            {
                'id': '002',
                'symbol': 'ETHUSDT',
                'type': 'COMPRA',
                'price': 2940.75,
                'confidence': 72.8,
                'strategy': 'Tendencia',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            },
            {
                'id': '003',
                'symbol': 'BNBUSDT',
                'type': 'VENTA',
                'price': 580.25,
                'confidence': 68.5,
                'strategy': 'Momentum',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
        ]
        
    def rowCount(self, parent=QModelIndex()):
        """Retorna el número de filas"""
        return len(self.opportunities)
        
    def columnCount(self, parent=QModelIndex()):
        """Retorna el número de columnas"""
        return len(self.headers)
        
    def data(self, index, role=Qt.DisplayRole):
        """Retorna los datos para el rol especificado"""
        if not index.isValid() or index.row() >= len(self.opportunities):
            return QVariant()
            
        opportunity = self.opportunities[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            if column == 0:
                return opportunity['id']
            elif column == 1:
                return opportunity['symbol']
            elif column == 2:
                return opportunity['type']
            elif column == 3:
                return f"{opportunity['price']:.2f}"
            elif column == 4:
                return f"{opportunity['confidence']:.1f}%"
            elif column == 5:
                return opportunity['strategy']
            elif column == 6:
                return opportunity['timestamp']
                
        elif role == Qt.TextAlignmentRole:
            if column in [3, 4]:  # Precio, Confianza
                return Qt.AlignRight | Qt.AlignVCenter
            else:
                return Qt.AlignLeft | Qt.AlignVCenter
                
        elif role == Qt.ForegroundRole:
            if column == 2:  # Tipo
                if opportunity['type'] == 'COMPRA':
                    return QColor('#77DD77')  # Verde para compra
                else:
                    return QColor('#FF6B6B')  # Rojo para venta
            elif column == 4:  # Confianza
                confidence = opportunity['confidence']
                if confidence >= 80:
                    return QColor('#77DD77')  # Verde para alta confianza
                elif confidence >= 60:
                    return QColor('#FFD700')  # Amarillo para confianza media
                else:
                    return QColor('#FF6B6B')  # Rojo para baja confianza
                    
        return QVariant()
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Retorna los datos de cabecera"""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
            
        return QVariant()
        
    def add_opportunity(self, opportunity: Dict[str, Any]):
        """Añade una nueva oportunidad a la tabla"""
        self.beginInsertRows(QModelIndex(), len(self.opportunities), len(self.opportunities))
        self.opportunities.append(opportunity)
        self.endInsertRows()
        
    def remove_opportunity(self, row: int):
        """Elimina una oportunidad de la tabla"""
        if 0 <= row < len(self.opportunities):
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.opportunities[row]
            self.endRemoveRows()
            
    def clear(self):
        """Elimina todas las oportunidades"""
        self.beginResetModel()
        self.opportunities.clear()
        self.endResetModel()
        
    def get_opportunity(self, row: int) -> Optional[Dict[str, Any]]:
        """Retorna la oportunidad en la fila especificada"""
        if 0 <= row < len(self.opportunities):
            return self.opportunities[row]
        return None

class OpportunitiesTable(QWidget):
    """Widget de tabla de oportunidades"""
    
    # Señales
    opportunity_selected = pyqtSignal(dict)
    opportunity_executed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Modelos
        self.model = OpportunitiesModel(self)
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        
        # UI
        self.init_ui()
        
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabla
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSortingEnabled(True)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.SingleSelection)
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        self.table_view.doubleClicked.connect(self.on_double_click)
        
        # Configurar cabeceras
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Hora
        
        # Ordenar por confianza descendente por defecto
        self.table_view.sortByColumn(4, Qt.DescendingOrder)
        
        # Añadir tabla al layout
        layout.addWidget(self.table_view)
        
        # Aplicar layout
        self.setLayout(layout)
        
    def set_filter(self, text: str):
        """Establece el filtro de búsqueda"""
        self.proxy_model.setFilterFixedString(text)
        
    def show_context_menu(self, position):
        """Muestra el menú contextual"""
        indexes = self.table_view.selectedIndexes()
        if not indexes:
            return
            
        # Obtener fila seleccionada
        row = self.proxy_model.mapToSource(indexes[0]).row()
        opportunity = self.model.get_opportunity(row)
        
        if not opportunity:
            return
            
        # Crear menú
        menu = QMenu()
        
        # Acciones
        execute_action = QAction(f"Ejecutar {opportunity['type']} {opportunity['symbol']}", self)
        execute_action.triggered.connect(lambda: self.execute_opportunity(row))
        
        analyze_action = QAction(f"Analizar {opportunity['symbol']}", self)
        analyze_action.triggered.connect(lambda: self.analyze_opportunity(row))
        
        # Añadir acciones al menú
        menu.addAction(execute_action)
        menu.addAction(analyze_action)
        
        # Mostrar menú
        menu.exec_(self.table_view.viewport().mapToGlobal(position))
        
    def on_double_click(self, index):
        """Maneja el doble clic en una fila"""
        # Mapear índice al modelo fuente
        source_index = self.proxy_model.mapToSource(index)
        row = source_index.row()
        
        # Obtener oportunidad
        opportunity = self.model.get_opportunity(row)
        
        if opportunity:
            # Emitir señal
            self.opportunity_selected.emit(opportunity)
            
            # Notificar al usuario
            if self.parent:
                self.parent.show_notification(f"Seleccionada oportunidad {opportunity['symbol']} ({opportunity['type']})")
        
    def execute_opportunity(self, row: int):
        """Ejecuta la oportunidad seleccionada"""
        opportunity = self.model.get_opportunity(row)
        
        if opportunity:
            # Emitir señal
            self.opportunity_executed.emit(opportunity)
            
            # Notificar al usuario
            if self.parent:
                self.parent.show_notification(
                    f"Ejecutando {opportunity['type']} de {opportunity['symbol']} a {opportunity['price']:.2f}",
                    level='warning'
                )
                
            # Eliminar de la lista (opcional)
            # self.model.remove_opportunity(row)
        
    def analyze_opportunity(self, row: int):
        """Analiza la oportunidad seleccionada"""
        opportunity = self.model.get_opportunity(row)
        
        if opportunity and self.parent:
            self.parent.show_notification(
                f"Analizando {opportunity['symbol']} - Estrategia: {opportunity['strategy']}",
                level='info'
            )
            
    def add_opportunity(self, opportunity: Dict[str, Any]):
        """Añade una nueva oportunidad"""
        self.model.add_opportunity(opportunity)
