from PyQt5.QtCore import QDateTime, Qt
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class NotificationCenterPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Centro de Notificaciones")
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)
        
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Align content to the top
        self.scroll_area.setWidget(self.scroll_content)
        
        main_layout.addWidget(self.scroll_area)
        
        self.notifications = [] # Store persistent notifications

    def add_notification(self, type, message, details=""):
        timestamp = QDateTime.currentDateTime().toString(Qt.DateFormat.DefaultLocaleLongDate)
        notification_item = NotificationItem(type, message, details, timestamp)
        self.scroll_layout.insertWidget(0, notification_item) # Add to top
        self.notifications.append({"type": type, "message": message, "details": details, "timestamp": timestamp})
        # Optional: Limit number of stored notifications
        if len(self.notifications) > 100:
            self.notifications.pop(0) # Remove oldest

class NotificationItem(QFrame):
    def __init__(self, type, message, details, timestamp, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        item_layout = QVBoxLayout(self)
        self.setLayout(item_layout)
        
        self.label_timestamp = QLabel(timestamp)
        self.label_timestamp.setStyleSheet("font-size: 10px; color: gray;")
        
        self.label_message = QLabel(message)
        self.label_message.setWordWrap(True)
        self.label_message.setStyleSheet("font-weight: bold;")
        
        self.label_details = QLabel(details)
        self.label_details.setWordWrap(True)
        self.label_details.setStyleSheet("font-size: 12px;")
        
        item_layout.addWidget(self.label_timestamp)
        item_layout.addWidget(self.label_message)
        if details:
            item_layout.addWidget(self.label_details)
        
        self.setup_style(type)
        self.setContentsMargins(10, 10, 10, 10) # Add some padding

    def setup_style(self, type):
        if type == "info":
            self.setStyleSheet("background-color: #e0f7fa; border: 1px solid #00bcd4; border-radius: 5px;")
        elif type == "warning":
            self.setStyleSheet("background-color: #fffde7; border: 1px solid #ffeb3b; border-radius: 5px;")
        elif type == "error":
            self.setStyleSheet("background-color: #ffebee; border: 1px solid #f44336; border-radius: 5px;")
        elif type == "success":
            self.setStyleSheet("background-color: #e8f5e9; border: 1px solid #4CAF50; border-radius: 5px;")
        else: # Default to info
            self.setStyleSheet("background-color: #e0f7fa; border: 1px solid #00bcd4; border-radius: 5px;")
