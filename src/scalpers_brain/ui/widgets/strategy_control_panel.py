"""
Panel de control de estrategias para Scalper's Brain
"""

import logging
from typing import Dict, List, Any, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSlider, QCheckBox, QGroupBox, QScrollArea, QSizePolicy,
    QComboBox, QSpinBox, QDoubleSpinBox, QFormLayout
)

logger = logging.getLogger(__name__)

class StrategyWidget(QWidget):
    """Widget para controlar una estrategia individual"""
    
    # Señales
    enabled_changed = pyqtSignal(str, bool)
    settings_changed = pyqtSignal(str, dict)
    
    def __init__(self, strategy_id: str, strategy_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        
        # Datos
        self.strategy_id = strategy_id
        self.strategy_data = strategy_data
        self.is_enabled = strategy_data.get('enabled', False)
        self.settings = strategy_data.get('settings', {})
        
        # UI
        self.init_ui()
        
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Título y switch
        header_layout = QHBoxLayout()
        
        # Nombre de la estrategia
        title = QLabel(f"<b>{self.strategy_data['name']}</b>")
        title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Checkbox para activar/desactivar
        self.enabled_checkbox = QCheckBox("Activar")
        self.enabled_checkbox.setChecked(self.is_enabled)
        self.enabled_checkbox.stateChanged.connect(self.on_enabled_changed)
        
        header_layout.addWidget(title)
        header_layout.addWidget(self.enabled_checkbox)
        
        # Añadir cabecera al layout principal
        layout.addLayout(header_layout)
        
        # Descripción
        if 'description' in self.strategy_data:
            description = QLabel(self.strategy_data['description'])
            description.setWordWrap(True)
            description.setStyleSheet("color: #AAAAAA; font-size: 11px;")
            layout.addWidget(description)
        
        # Grupo de configuraciones
        settings_group = QGroupBox("Configuración")
        settings_layout = QFormLayout(settings_group)
        
        # Procesar configuraciones según su tipo
        for key, setting in self.settings.items():
            setting_type = setting.get('type', 'string')
            label = QLabel(setting.get('label', key))
            
            if setting_type == 'boolean':
                control = QCheckBox()
                control.setChecked(setting.get('value', False))
                control.stateChanged.connect(lambda state, k=key: self.on_setting_changed(k, state == Qt.Checked))
            
            elif setting_type == 'integer':
                control = QSpinBox()
                control.setMinimum(setting.get('min', 0))
                control.setMaximum(setting.get('max', 100))
                control.setValue(setting.get('value', 0))
                control.valueChanged.connect(lambda value, k=key: self.on_setting_changed(k, value))
            
            elif setting_type == 'float':
                control = QDoubleSpinBox()
                control.setMinimum(setting.get('min', 0.0))
                control.setMaximum(setting.get('max', 100.0))
                control.setSingleStep(setting.get('step', 0.1))
                control.setDecimals(setting.get('decimals', 2))
                control.setValue(setting.get('value', 0.0))
                control.valueChanged.connect(lambda value, k=key: self.on_setting_changed(k, value))
            
            elif setting_type == 'select':
                control = QComboBox()
                control.addItems(setting.get('options', []))
                value = setting.get('value', '')
                if value in setting.get('options', []):
                    control.setCurrentText(value)
                control.currentTextChanged.connect(lambda value, k=key: self.on_setting_changed(k, value))
            
            elif setting_type == 'slider':
                control = QSlider(Qt.Horizontal)
                control.setMinimum(setting.get('min', 0))
                control.setMaximum(setting.get('max', 100))
                control.setValue(setting.get('value', 0))
                control.valueChanged.connect(lambda value, k=key: self.on_setting_changed(k, value))
            
            else:  # string o tipo por defecto
                control = QComboBox()
                control.setEditable(True)
                if 'value' in setting:
                    control.setCurrentText(str(setting['value']))
                control.currentTextChanged.connect(lambda value, k=key: self.on_setting_changed(k, value))
            
            settings_layout.addRow(label, control)
        
        # Añadir grupo de configuraciones
        layout.addWidget(settings_group)
        
        # Añadir espacio
        layout.addStretch()
        
        # Aplicar layout
        self.setLayout(layout)
        
        # Estilo
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3E3E42;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
            }
        """)
        
    def on_enabled_changed(self, state):
        """Maneja el cambio de estado de activación"""
        self.is_enabled = state == Qt.Checked
        self.enabled_changed.emit(self.strategy_id, self.is_enabled)
        logger.info(f"Estrategia {self.strategy_data['name']} {'activada' if self.is_enabled else 'desactivada'}")
        
    def on_setting_changed(self, key, value):
        """Maneja el cambio de un ajuste"""
        if key in self.settings:
            self.settings[key]['value'] = value
            self.settings_changed.emit(self.strategy_id, self.settings)
            logger.debug(f"Configuración '{key}' de {self.strategy_data['name']} cambiada a {value}")

class StrategyControlPanel(QWidget):
    """Panel de control de estrategias"""
    
    # Señales
    strategy_enabled = pyqtSignal(str, bool)
    strategy_settings_changed = pyqtSignal(str, dict)
    start_all = pyqtSignal()
    stop_all = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # Datos
        self.strategies: Dict[str, StrategyWidget] = {}
        
        # UI
        self.init_ui()
        
        # Cargar estrategias de ejemplo
        self._load_sample_strategies()
        
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Controles generales
        controls_layout = QHBoxLayout()
        
        # Botón de iniciar todas las estrategias
        self.start_all_button = QPushButton("Iniciar Todas")
        self.start_all_button.clicked.connect(self.on_start_all)
        
        # Botón de detener todas las estrategias
        self.stop_all_button = QPushButton("Detener Todas")
        self.stop_all_button.clicked.connect(self.on_stop_all)
        
        # Añadir botones al layout de controles
        controls_layout.addWidget(self.start_all_button)
        controls_layout.addWidget(self.stop_all_button)
        controls_layout.addStretch()
        
        # Añadir layout de controles al layout principal
        layout.addLayout(controls_layout)
        
        # Contenedor de estrategias con scroll
        self.strategies_container = QWidget()
        self.strategies_layout = QHBoxLayout(self.strategies_container)
        self.strategies_layout.setContentsMargins(0, 0, 0, 0)
        self.strategies_layout.setSpacing(10)
        
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.strategies_container)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Añadir scroll area al layout principal
        layout.addWidget(scroll_area, 1)
        
        # Aplicar layout
        self.setLayout(layout)
        
    def _load_sample_strategies(self):
        """Carga estrategias de ejemplo"""
        sample_strategies = {
            'scalping': {
                'name': 'Scalping',
                'description': 'Estrategia de scalping para movimientos rápidos de precio con bajo riesgo',
                'enabled': True,
                'settings': {
                    'min_profit': {
                        'label': 'Beneficio mínimo (%)',
                        'type': 'float',
                        'min': 0.1,
                        'max': 5.0,
                        'step': 0.1,
                        'decimals': 1,
                        'value': 0.5
                    },
                    'stop_loss': {
                        'label': 'Stop Loss (%)',
                        'type': 'float',
                        'min': 0.1,
                        'max': 2.0,
                        'step': 0.1,
                        'decimals': 1,
                        'value': 0.3
                    },
                    'max_hold_time': {
                        'label': 'Tiempo máximo (min)',
                        'type': 'integer',
                        'min': 1,
                        'max': 60,
                        'value': 15
                    },
                    'use_ai': {
                        'label': 'Usar IA para señales',
                        'type': 'boolean',
                        'value': True
                    }
                }
            },
            'day_trading': {
                'name': 'Day Trading',
                'description': 'Estrategia de day trading para capturar movimientos intradía con análisis técnico',
                'enabled': False,
                'settings': {
                    'profit_target': {
                        'label': 'Objetivo de beneficio (%)',
                        'type': 'float',
                        'min': 0.5,
                        'max': 10.0,
                        'step': 0.5,
                        'decimals': 1,
                        'value': 2.0
                    },
                    'risk_level': {
                        'label': 'Nivel de riesgo',
                        'type': 'select',
                        'options': ['Conservador', 'Moderado', 'Agresivo'],
                        'value': 'Moderado'
                    },
                    'indicators': {
                        'label': 'Indicadores',
                        'type': 'select',
                        'options': ['RSI+MACD', 'Bollinger+ADX', 'EMA Cruce', 'Todos'],
                        'value': 'RSI+MACD'
                    }
                }
            },
            'arbitrage': {
                'name': 'Arbitraje',
                'description': 'Estrategia de arbitraje triangular para aprovechar diferencias de precio entre pares',
                'enabled': False,
                'settings': {
                    'min_profit': {
                        'label': 'Beneficio mínimo (%)',
                        'type': 'float',
                        'min': 0.1,
                        'max': 5.0,
                        'step': 0.1,
                        'decimals': 2,
                        'value': 0.15
                    },
                    'execution_speed': {
                        'label': 'Velocidad de ejecución',
                        'type': 'slider',
                        'min': 1,
                        'max': 10,
                        'value': 7
                    },
                    'exchanges': {
                        'label': 'Exchanges',
                        'type': 'select',
                        'options': ['Binance', 'Binance+Coinbase', 'Todos (Premium)'],
                        'value': 'Binance'
                    }
                }
            }
        }
        
        # Añadir estrategias a la interfaz
        for strategy_id, strategy_data in sample_strategies.items():
            self.add_strategy(strategy_id, strategy_data)
        
    def add_strategy(self, strategy_id: str, strategy_data: Dict[str, Any]):
        """Añade una estrategia al panel"""
        # Crear widget
        strategy_widget = StrategyWidget(strategy_id, strategy_data, self)
        
        # Conectar señales
        strategy_widget.enabled_changed.connect(self.on_strategy_enabled)
        strategy_widget.settings_changed.connect(self.on_strategy_settings_changed)
        
        # Añadir al layout
        self.strategies_layout.addWidget(strategy_widget)
        
        # Almacenar referencia
        self.strategies[strategy_id] = strategy_widget
        
        logger.info(f"Estrategia {strategy_data['name']} añadida al panel")
        
    def remove_strategy(self, strategy_id: str):
        """Elimina una estrategia del panel"""
        if strategy_id in self.strategies:
            # Eliminar widget
            strategy_widget = self.strategies[strategy_id]
            self.strategies_layout.removeWidget(strategy_widget)
            strategy_widget.deleteLater()
            
            # Eliminar referencia
            del self.strategies[strategy_id]
            
            logger.info(f"Estrategia {strategy_id} eliminada del panel")
        
    def on_strategy_enabled(self, strategy_id: str, enabled: bool):
        """Maneja el cambio de estado de una estrategia"""
        # Emitir señal
        self.strategy_enabled.emit(strategy_id, enabled)
        
        # Notificar al usuario
        if self.parent:
            strategy_name = self.strategies[strategy_id].strategy_data['name']
            self.parent.show_notification(
                f"Estrategia {strategy_name} {'activada' if enabled else 'desactivada'}",
                level='info' if enabled else 'warning'
            )
        
    def on_strategy_settings_changed(self, strategy_id: str, settings: Dict):
        """Maneja el cambio de configuración de una estrategia"""
        # Emitir señal
        self.strategy_settings_changed.emit(strategy_id, settings)
        
    def on_start_all(self):
        """Inicia todas las estrategias"""
        # Activar todas las estrategias
        for strategy_id, strategy_widget in self.strategies.items():
            strategy_widget.enabled_checkbox.setChecked(True)
        
        # Emitir señal
        self.start_all.emit()
        
        # Notificar al usuario
        if self.parent:
            self.parent.show_notification("Todas las estrategias activadas", level='warning')
        
    def on_stop_all(self):
        """Detiene todas las estrategias"""
        # Desactivar todas las estrategias
        for strategy_id, strategy_widget in self.strategies.items():
            strategy_widget.enabled_checkbox.setChecked(False)
        
        # Emitir señal
        self.stop_all.emit()
        
        # Notificar al usuario
        if self.parent:
            self.parent.show_notification("Todas las estrategias desactivadas", level='warning')
