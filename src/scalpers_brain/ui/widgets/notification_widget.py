"""
Widget de notificaciones para Scalper's Brain
"""

import logging
from typing import Optional

from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy

logger = logging.getLogger(__name__)

class NotificationWidget(QWidget):
    """Widget para mostrar notificaciones flotantes"""
    
    def __init__(self, message: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # Configuración
        self.message = message
        self.timeout = 3000  # ms
        self.persistent = False
        self.level = 'info'
        
        # Estado
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide_notification)
        
        # UI
        self.init_ui()
        
        # Estilos por defecto
        self.setStyleSheet("""
            QWidget { 
                background-color: #2D2D30;
                border: 1px solid #3E3E42;
                border-radius: 4px;
            }
            QLabel { 
                color: #FFFFFF;
                border: none;
                font-size: 12px;
                padding: 2px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #CCCCCC;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #FFFFFF;
            }
        """)
        
        # Ocultar inicialmente
        self.hide()
        
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Configurar widget
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(300)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        # Layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # Label para el mensaje
        self.label = QLabel(self.message)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        
        # Botón de cerrar
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(16, 16)
        self.close_button.clicked.connect(self.hide_notification)
        layout.addWidget(self.close_button)
        
        # Aplicar layout
        self.setLayout(layout)
        
    def set_message(self, message: str):
        """Establece el mensaje de la notificación"""
        self.message = message
        self.label.setText(message)
        self.adjustSize()
        
    def set_timeout(self, timeout: int):
        """Establece el tiempo de visibilidad en ms"""
        self.timeout = timeout
        
    def set_persistent(self, persistent: bool):
        """Establece si la notificación debe persistir hasta ser cerrada"""
        self.persistent = persistent
        
    def set_level(self, level: str):
        """Establece el nivel de la notificación y aplica el estilo correspondiente"""
        self.level = level
        self.set_level_style(level)
        
    def set_level_style(self, level: str):
        """Aplica el estilo correspondiente al nivel de la notificación"""
        base_style = """
            QWidget { 
                background-color: #2D2D30;
                border: 1px solid #3E3E42;
                border-radius: 4px;
            }
            QLabel { 
                color: #FFFFFF;
                border: none;
                font-size: 12px;
                padding: 2px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #CCCCCC;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #FFFFFF;
            }
        """
        
        if level == 'info':
            self.setStyleSheet(base_style + """
                QWidget { 
                    background-color: #2D2D30;
                    border: 1px solid #3E3E42;
                }
            """)
        elif level == 'success':
            self.setStyleSheet(base_style + """
                QWidget { 
                    background-color: #0D3B0D;
                    border: 1px solid #1E541E;
                }
            """)
        elif level == 'warning':
            self.setStyleSheet(base_style + """
                QWidget { 
                    background-color: #523D00;
                    border: 1px solid #6E5100;
                }
            """)
        elif level == 'error':
            self.setStyleSheet(base_style + """
                QWidget { 
                    background-color: #4A0000;
                    border: 1px solid #6E0000;
                }
            """)
        
    def show_notification(self):
        """Muestra la notificación con animación"""
        if not self.parent():
            logger.warning("No se puede mostrar la notificación sin un widget padre")
            return
            
        # Posicionar en la esquina superior derecha del padre
        parent_rect = self.parent().rect()
        self.adjustSize()
        width = self.width()
        x = parent_rect.width() - width - 20
        target_y = 20
        
        # Posición inicial (fuera de la pantalla)
        self.setGeometry(x, -self.height(), width, self.height())
        self.show()
        
        # Crear y configurar animación
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(QRect(x, -self.height(), width, self.height()))
        self.animation.setEndValue(QRect(x, target_y, width, self.height()))
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()
        
        # Iniciar temporizador si no es persistente
        if not self.persistent:
            self.timer.start(self.timeout)
        
    def hide_notification(self):
        """Oculta la notificación con animación"""
        if not self.isVisible():
            return
            
        # Detener el temporizador
        self.timer.stop()
        
        # Animación de salida
        geometry = self.geometry()
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setStartValue(geometry)
        self.animation.setEndValue(QRect(geometry.x(), -self.height(), geometry.width(), geometry.height()))
        self.animation.setEasingCurve(QEasingCurve.InCubic)
        self.animation.finished.connect(self.hide)
        self.animation.start()
