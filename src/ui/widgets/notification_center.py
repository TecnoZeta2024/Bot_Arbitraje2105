from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QLabel, QWidget, QHBoxLayout, QPushButton
from PyQt5 import QtCore
from PyQt5.QtCore import QDateTime

class NotificationCenter(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Centro de Notificaciones")
        self.setGeometry(100, 100, 600, 400)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

        self.notifications = []

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        title_label = QLabel("Historial de Notificaciones")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        self.notification_list_widget = QListWidget()
        main_layout.addWidget(self.notification_list_widget)

        clear_button = QPushButton("Limpiar Notificaciones")
        clear_button.clicked.connect(self.clear_notifications)
        main_layout.addWidget(clear_button)

    def add_notification(self, message, type="info"):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        notification_entry = f"[{timestamp}] [{type.upper()}] {message}"
        self.notifications.append(notification_entry)
        self.notification_list_widget.addItem(notification_entry)
        self.notification_list_widget.scrollToBottom()

    def clear_notifications(self):
        self.notifications = []
        self.notification_list_widget.clear()

    def show_center(self):
        self.update_list_widget()
        self.exec_()

    def update_list_widget(self):
        self.notification_list_widget.clear()
        for notification in self.notifications:
            self.notification_list_widget.addItem(notification)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    center = NotificationCenter()
    center.add_notification("Esto es una notificación de prueba.", "info")
    center.add_notification("Error al conectar con la API.", "error")
    center.add_notification("Oportunidad detectada: BTC/USDT.", "success")
    center.show_center()
    sys.exit(app.exec_())
