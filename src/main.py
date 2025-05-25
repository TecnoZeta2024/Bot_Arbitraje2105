import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent))

def run_ui():
    """Punto de entrada para ejecutar la aplicación PyQt5."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_ui()
