import sys
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QPushButton, QHBoxLayout
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QTimer, QRect, QUrl, QCoreApplication # Añadir QCoreApplication para primaryScreen
from PyQt5.QtGui import QColor, QPalette, QIcon
from PyQt5.QtMultimedia import QSoundEffect

class NotificationWidget(QWidget):
    def __init__(self, message, level='info', parent=None, timeout=3000, persistent=False, enable_sound=True):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.NoDropShadowWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setFixedSize(300, 100) # Tamaño ajustado para el botón de cerrar

        self.enable_sound = enable_sound
        self.sound_effects = {}
        self._load_sounds()

        main_layout = QVBoxLayout(self)
        
        # Layout para el mensaje y el botón de cerrar
        header_layout = QHBoxLayout()
        self.label = QLabel(message)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet("color: white; font-weight: bold;")
        header_layout.addWidget(self.label)

        self.close_button = QPushButton("X")
        self.close_button.setFixedSize(20, 20)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 50);
                color: white;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 80);
            }
        """)
        self.close_button.clicked.connect(self.hide_notification)
        header_layout.addWidget(self.close_button)
        header_layout.setAlignment(self.close_button, QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)

        main_layout.addLayout(header_layout)
        self.setLayout(main_layout)

        self.persistent = persistent
        if not self.persistent:
            self.timeout_timer = QTimer(self)
            self.timeout_timer.setSingleShot(True)
            self.timeout_timer.timeout.connect(self.hide_notification)
            self.timeout = timeout
        else:
            self.timeout_timer = None # No hay temporizador si es persistente

        self.level = level
        self.set_level_style(level)

    def _load_sounds(self):
        """Carga los archivos de sonido para cada nivel de notificación."""
        sound_paths = {
            'info': 'src/resources/sounds/info.wav',
            'warning': 'src/resources/sounds/warning.wav',
            'error': 'src/resources/sounds/error.wav',
            'success': 'src/resources/sounds/success.wav'
        }
        for level, path in sound_paths.items():
            sound = QSoundEffect()
            sound.setSource(QUrl.fromLocalFile(path))
            self.sound_effects[level] = sound

    def play_sound(self, level):
        """Reproduce el sonido correspondiente al nivel de notificación."""
        if self.enable_sound and level in self.sound_effects and self.sound_effects[level].isLoaded():
            self.sound_effects[level].play()

    def set_level_style(self, level):
        """Aplica estilos visuales basados en el nivel de notificación."""
        self.setObjectName(f"NotificationWidget_{level}")
        self.setStyleSheet(f"""
            .NotificationWidget_{level} {{
                border-radius: 10px;
                padding: 10px;
            }}
            .NotificationWidget_{level} QLabel {{
                color: white;
                font-weight: bold;
            }}
            .NotificationWidget_info {{
                background-color: rgba(0, 123, 255, 180); /* Azul */
            }}
            .NotificationWidget_warning {{
                background-color: rgba(255, 193, 7, 180); /* Amarillo */
            }}
            .NotificationWidget_error {{
                background-color: rgba(220, 53, 69, 180); /* Rojo */
            }}
            .NotificationWidget_success {{
                background-color: rgba(40, 167, 69, 180); /* Verde */
            }}
            .NotificationWidget_default {{
                background-color: rgba(0, 0, 0, 180); /* Por defecto, negro */
            }}
        """)

    def show_notification(self):
        # Usar QGuiApplication.primaryScreen() para mayor robustez
        screen_rect = QApplication.primaryScreen().availableGeometry()
        x = screen_rect.width() - self.width() - 20
        y = screen_rect.height() - self.height() - 20
        self.move(x, y)
        self.show()
        if not self.persistent and self.timeout_timer:
            self.timeout_timer.start(self.timeout)
        self.play_sound(self.level) # Reproducir sonido al mostrar la notificación

    def hide_notification(self):
        self.hide()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Ejemplos de uso con diferentes niveles
    notification_info = NotificationWidget("¡Información importante!", level='info')
    notification_info.show_notification()

    notification_warning = NotificationWidget("Advertencia: Conexión inestable.", level='warning', persistent=True) # Notificación persistente
    screen_rect_warning = QApplication.primaryScreen().availableGeometry()
    notification_warning.move(screen_rect_warning.width() - notification_warning.width() - 20, screen_rect_warning.height() - notification_warning.height() - 120)
    notification_warning.show_notification()

    notification_error = NotificationWidget("Error: No se pudo completar la operación.", level='error')
    screen_rect_error = QApplication.primaryScreen().availableGeometry()
    notification_error.move(screen_rect_error.width() - notification_error.width() - 20, screen_rect_error.height() - notification_error.height() - 220)
    notification_error.show_notification()

    notification_success = NotificationWidget("¡Éxito! Transacción completada.", level='success', persistent=True) # Notificación persistente
    screen_rect_success = QApplication.primaryScreen().availableGeometry()
    notification_success.move(screen_rect_success.width() - notification_success.width() - 20, screen_rect_success.height() - notification_success.height() - 320)
    notification_success.show_notification()

    sys.exit(app.exec_())
