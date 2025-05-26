"""
Centro de notificaciones para Scalper's Brain
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

class NotificationCenter(QDialog):
    """Centro para mostrar historial de notificaciones"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Configuración de la ventana
        self.setWindowTitle("Centro de Notificaciones")
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.resize(500, 400)
        
        # Datos
        self.notifications: List[Dict] = []
        
        # UI
        self.init_ui()
        
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Lista de notificaciones
        self.notification_list = QListWidget()
        self.notification_list.setAlternatingRowColors(True)
        
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.notification_list)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Limpiar Todo")
        self.clear_button.clicked.connect(self.clear_notifications)
        
        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.close)
        
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_button)
        
        # Añadir widgets al layout principal
        layout.addWidget(QLabel("<b>Historial de Notificaciones</b>"))
        layout.addWidget(scroll_area)
        layout.addLayout(buttons_layout)
        
        # Aplicar layout
        self.setLayout(layout)
        
    def add_notification(self, message: str, level: str = 'info'):
        """Añade una notificación al historial"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        notification = {
            'message': message,
            'level': level,
            'timestamp': timestamp
        }
        
        # Añadir a la lista de datos
        self.notifications.append(notification)
        
        # Limitar a 100 notificaciones
        if len(self.notifications) > 100:
            self.notifications = self.notifications[-100:]
        
        # Actualizar UI si está visible
        if self.isVisible():
            self.update_notification_list()
            
        logger.debug(f"Notificación añadida: [{level}] {message}")
        
    def update_notification_list(self):
        """Actualiza la lista visual de notificaciones"""
        self.notification_list.clear()
        
        for notification in reversed(self.notifications):
            item = QListWidgetItem()
            
            # Crear widget para la notificación
            widget = QWidget()
            layout = QHBoxLayout(widget)
            
            # Etiqueta de tiempo
            time_label = QLabel(notification['timestamp'])
            time_label.setFixedWidth(60)
            
            # Etiqueta de nivel
            level_label = QLabel(notification['level'].upper())
            level_label.setFixedWidth(60)
            
            # Establecer color según nivel
            if notification['level'] == 'info':
                level_label.setStyleSheet("color: #29B6F6;")
            elif notification['level'] == 'success':
                level_label.setStyleSheet("color: #66BB6A;")
            elif notification['level'] == 'warning':
                level_label.setStyleSheet("color: #FFA726;")
            elif notification['level'] == 'error':
                level_label.setStyleSheet("color: #EF5350;")
            
            # Etiqueta de mensaje
            message_label = QLabel(notification['message'])
            message_label.setWordWrap(True)
            
            # Añadir widgets al layout
            layout.addWidget(time_label)
            layout.addWidget(level_label)
            layout.addWidget(message_label, 1)
            layout.setContentsMargins(5, 5, 5, 5)
            
            # Configurar widget
            widget.setLayout(layout)
            
            # Configurar item
            item.setSizeHint(QSize(self.notification_list.width(), 50))
            
            # Añadir a la lista
            self.notification_list.addItem(item)
            self.notification_list.setItemWidget(item, widget)
    
    def clear_notifications(self):
        """Elimina todas las notificaciones"""
        self.notifications.clear()
        self.notification_list.clear()
        logger.debug("Notificaciones eliminadas")
        
    def show(self):
        """Muestra el centro de notificaciones"""
        self.update_notification_list()
        super().show()
