import os
import sys

from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Cargar el archivo QSS para el tema oscuro
    qss_path = os.path.join(os.path.dirname(__file__), 'ui', 'style.qss')
    if os.path.exists(qss_path):
        with open(qss_path, 'r') as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Advertencia: No se encontró el archivo de estilo QSS en {qss_path}")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
