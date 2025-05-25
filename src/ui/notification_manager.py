from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QCoreApplication
from PyQt5.QtGui import QColor, QPalette, QFontMetrics

class NotificationManager(QObject):
    notification_signal = pyqtSignal(str, str, str) # type, message, details

    def __init__(self, parent=None):
        super().__init__(parent)
        self.notifications = []
        self.notification_signal.connect(self._show_notification)

    def show_notification(self, type, message, details=""):
        self.notification_signal.emit(type, message, details)

    def _show_notification(self, type, message, details=""):
        notification_widget = FloatingNotification(type, message, details)
        notification_widget.show()
        self.notifications.append(notification_widget)
        # Clean up closed notifications
        self.notifications = [n for n in self.notifications if n.isVisible()]

class FloatingNotification(QWidget):
    def __init__(self, type, message, details="", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.label_message = QLabel(message)
        self.label_details = QLabel(details)
        self.label_details.setWordWrap(True)

        font_metrics = QFontMetrics(self.label_message.font())
        text_width = font_metrics.width(message)
        self.setFixedWidth(max(300, text_width + 50)) # Adjust width based on message length

        main_layout.addWidget(self.label_message)
        if details:
            main_layout.addWidget(self.label_details)

        self.setup_style(type)

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.fade_out)
        self.fade_alpha = 1.0
        self.fade_step = 0.05

        self.initial_pos_set = False
        self.timer = QTimer(self)
        self.timer.singleShot(5000, self.start_fade_out) # Notification visible for 5 seconds

    def setup_style(self, type):
        palette = self.palette()
        if type == "info":
            self.setStyleSheet("background-color: rgba(0, 123, 255, 200); border: 1px solid rgba(0, 123, 255, 255); border-radius: 5px; color: white;")
            palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        elif type == "warning":
            self.setStyleSheet("background-color: rgba(255, 193, 7, 200); border: 1px solid rgba(255, 193, 7, 255); border-radius: 5px; color: black;")
            palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
        elif type == "error":
            self.setStyleSheet("background-color: rgba(220, 53, 69, 200); border: 1px solid rgba(220, 53, 69, 255); border-radius: 5px; color: white;")
            palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        elif type == "success":
            self.setStyleSheet("background-color: rgba(40, 167, 69, 200); border: 1px solid rgba(40, 167, 69, 255); border-radius: 5px; color: white;")
            palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        else: # Default to info
            self.setStyleSheet("background-color: rgba(0, 123, 255, 200); border: 1px solid rgba(0, 123, 255, 255); border-radius: 5px; color: white;")
            palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        self.setPalette(palette)

    def showEvent(self, event):
        if not self.initial_pos_set:
            self.initial_pos_set = True
            self.adjust_position()
        super().showEvent(event)

    def adjust_position(self):
        screen_rect = QApplication.primaryScreen().availableGeometry()
        x = screen_rect.width() - self.width() - 20
        y = screen_rect.height() - self.height() - 20 # Start from bottom right
        
        # Adjust position to stack notifications
        # This part needs a more robust way to get all active FloatingNotification instances
        # For now, we'll assume they are managed by the NotificationManager
        # and adjust based on the last one added or a simple stacking logic.
        # A more complex solution would involve a global notification stack manager.
        
        # Simple stacking: find the highest Y position of existing notifications
        highest_y = screen_rect.height() - self.height() - 20 # Default if no others
        for widget in QApplication.instance().topLevelWidgets():
            if isinstance(widget, FloatingNotification) and widget != self and widget.isVisible():
                # Check if the new notification would overlap
                if widget.x() == x and widget.y() < y: # If it's in the same column and above
                    y = widget.y() - self.height() - 10 # Stack above it
        
        self.move(x, y)

    def start_fade_out(self):
        self.animation_timer.start(50) # Fade out over 2.5 seconds (50ms * 50 steps)

    def fade_out(self):
        self.fade_alpha -= self.fade_step
        if self.fade_alpha <= 0:
            self.close()
        else:
            self.setWindowOpacity(self.fade_alpha)

    def mousePressEvent(self, event):
        self.close() # Close on click
