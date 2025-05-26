import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QAction, QMenu, QMenuBar, QToolBar, QDockWidget, QTextEdit, QHBoxLayout, QLineEdit, QComboBox
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon # Descomentado para usar íconos
import resources.resources_rc as resources_rc # Importar el archivo de recursos compilado de forma absoluta
from .widgets.chart_widget import ChartWidget # Importar ChartWidget
from .widgets.opportunities_table import OpportunitiesTableView # Importar OpportunitiesTableView
from .widgets.strategy_control_panel import StrategyControlPanel # Importar StrategyControlPanel
from .widgets.notification_widget import NotificationWidget # Importar NotificationWidget
from .widgets.notification_center import NotificationCenter # Importar NotificationCenter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aplicación de Trading de Criptomonedas")
        self.setGeometry(100, 100, 1200, 800)

        self.notification_widget = NotificationWidget("", parent=self) # Instanciar el widget de notificación
        self.notification_center = NotificationCenter(self) # Instanciar el centro de notificaciones
        self._create_actions()
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_dock_widgets()

    def _create_actions(self):
        # Acciones de Archivo
        self.new_action = QAction(QIcon(":/icons/icon_home.png"), "&Nuevo", self) # Usando QIcon desde recursos
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.setStatusTip("Crear un nuevo archivo")
        self.new_action.triggered.connect(self.new_file)

        self.open_action = QAction("&Abrir...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.setStatusTip("Abrir un archivo existente")
        self.open_action.triggered.connect(self.open_file)

        self.save_action = QAction("&Guardar", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.setStatusTip("Guardar el archivo actual")
        self.save_action.triggered.connect(self.save_file)

        self.exit_action = QAction("&Salir", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.setStatusTip("Salir de la aplicación")
        self.exit_action.triggered.connect(self._exit_app)

        # Acciones de Editar
        self.cut_action = QAction("Cor&tar", self)
        self.cut_action.setShortcut("Ctrl+X")
        self.cut_action.setStatusTip("Cortar el texto seleccionado")

        self.copy_action = QAction("&Copiar", self)
        self.copy_action.setShortcut("Ctrl+C")
        self.copy_action.setStatusTip("Copiar el texto seleccionado")

        self.paste_action = QAction("&Pegar", self)
        self.paste_action.setShortcut("Ctrl+V")
        self.paste_action.setStatusTip("Pegar el texto desde el portapapeles")

        # Acciones de Ver
        self.zoom_in_action = QAction("Acercar", self)
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_in_action.setStatusTip("Acercar la vista")

        self.zoom_out_action = QAction("Alejar", self)
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_out_action.setStatusTip("Alejar la vista")

        # Acciones de Ayuda
        self.about_action = QAction("&Acerca de...", self)
        self.about_action.setStatusTip("Mostrar información acerca de la aplicación")
        self.about_action.triggered.connect(self.about_dialog)

        # Acción para abrir el centro de notificaciones
        self.show_notification_center_action = QAction("Centro de &Notificaciones", self)
        self.show_notification_center_action.setStatusTip("Mostrar el historial de notificaciones")
        self.show_notification_center_action.triggered.connect(self.notification_center.show_center)

    def _create_menu_bar(self):
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        # Menú Archivo
        self.file_menu: QMenu = self.menu_bar.addMenu("&Archivo")
        self.file_menu.addAction(self.new_action)
        self.file_menu.addAction(self.open_action)
        self.file_menu.addAction(self.save_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

        # Menú Editar
        self.edit_menu: QMenu = self.menu_bar.addMenu("&Editar")
        self.edit_menu.addAction(self.cut_action)
        self.edit_menu.addAction(self.copy_action)
        self.edit_menu.addAction(self.paste_action)

        # Menú Ver
        self.view_menu: QMenu = self.menu_bar.addMenu("&Ver")
        self.view_menu.addAction(self.zoom_in_action)
        self.view_menu.addAction(self.zoom_out_action)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.show_notification_center_action) # Añadir acción al menú Ver

        # Menú Ayuda
        self.help_menu: QMenu = self.menu_bar.addMenu("&Ayuda")
        self.help_menu.addAction(self.about_action)

    def _create_tool_bar(self):
        self.tool_bar: QToolBar = self.addToolBar("Barra de Herramientas Principal")
        self.tool_bar.addAction(self.new_action)
        self.tool_bar.addAction(self.open_action)
        self.tool_bar.addAction(self.save_action)
        self.tool_bar.addSeparator()
        self.tool_bar.addAction(self.cut_action)
        self.tool_bar.addAction(self.copy_action)
        self.tool_bar.addAction(self.paste_action)

    def _create_dock_widgets(self):
        # Panel de Gráficos
        self.chart_dock = QDockWidget("Gráficos", self)
        self.chart_widget = ChartWidget(self) # Instanciar ChartWidget
        self.chart_dock.setWidget(self.chart_widget) # Establecer ChartWidget como contenido
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.chart_dock)

        # Panel de Oportunidades (Tabla)
        self.opportunities_dock = QDockWidget("Oportunidades", self)
        
        # Contenedor principal para la tabla y los controles de filtro/ordenamiento
        opportunities_container = QWidget()
        opportunities_layout = QVBoxLayout(opportunities_container)

        self.opportunities_table = OpportunitiesTableView(self) # Instanciar OpportunitiesTableView
        opportunities_layout.addWidget(self.opportunities_table) # Añadir tabla al layout

        # Controles de filtrado
        filter_layout = QHBoxLayout()
        self.filter_label = QLabel("Filtrar por:")
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Escriba para filtrar...")
        self.filter_input.textChanged.connect(self.opportunities_table.set_filter_text)

        self.filter_column_combo = QComboBox()
        self.filter_column_combo.addItems(self.opportunities_table._model._headers) # Usar los encabezados del modelo
        self.filter_column_combo.currentIndexChanged.connect(self.opportunities_table.set_filter_column)

        filter_layout.addWidget(self.filter_label)
        filter_layout.addWidget(self.filter_input)
        filter_layout.addWidget(self.filter_column_combo)
        
        opportunities_layout.addLayout(filter_layout) # Añadir layout de filtro al layout principal

        self.opportunities_dock.setWidget(opportunities_container) # Establecer el contenedor como contenido del dock
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.opportunities_dock)

        # Panel de Estrategias
        self.strategies_dock = QDockWidget("Estrategias", self)
        self.strategies_content = StrategyControlPanel(self) # Instanciar el panel de control de estrategias
        self.strategies_dock.setWidget(self.strategies_content)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self.strategies_dock)

        # Configurar áreas de docking permitidas
        self.chart_dock.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.opportunities_dock.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)
        self.strategies_dock.setAllowedAreas(QtCore.Qt.DockWidgetArea.AllDockWidgetAreas)

    def show_notification(self, message, level='info', timeout=3000, persistent=False):
        # Mostrar notificación flotante
        self.notification_widget.label.setText(message)
        self.notification_widget.timeout = timeout
        self.notification_widget.persistent = persistent # Establecer la persistencia
        self.notification_widget.set_level_style(level) # Establecer el estilo de la notificación
        self.notification_widget.show_notification()

        # Añadir notificación al centro de notificaciones
        self.notification_center.add_notification(message, level)

    # Métodos de ejemplo para las acciones
    def new_file(self):
        print("Acción: Nuevo archivo")
        self.show_notification("¡Nuevo archivo creado!", timeout=2000)

    def open_file(self):
        print("Acción: Abrir archivo")
        self.show_notification("Abriendo archivo...", timeout=2000)

    def save_file(self):
        print("Acción: Guardar archivo")
        self.show_notification("Archivo guardado exitosamente.", timeout=2000)

    def about_dialog(self):
        # self.label.setText("Acción: Acerca de la aplicación")
        print("Acción: Acerca de la aplicación")

    def _exit_app(self):
        self.close()
