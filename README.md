# 🚀 Advanced Personal Trading Platform v2.0

**Bot_Arbitraje2105** - Sistema de trading personal de clase institucional con IA, análisis en tiempo real y gestión avanzada de riesgos.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Instalación Rápida](#-instalación-rápida)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Estrategias de Trading](#-estrategias-de-trading)
- [Arquitectura](#-arquitectura)
- [Monitoreo y Alertas](#-monitoreo-y-alertas)
- [Desarrollo](#-desarrollo)
- [FAQ](#-faq)
- [Soporte](#-soporte)

## ✨ Características

### 🎯 **Estrategias de Trading Múltiples**
- **Scalping**: 50-200 trades/día, 0.01-0.1% ganancia por trade
- **Day Trading**: 5-20 trades/día, 0.5-2% ganancia por trade
- **Arbitraje Triangular**: Aprovechamiento de diferencias de precios
- **Swing Trading**: Posiciones de mediano plazo (próximamente)

### 🤖 **IA Avanzada**
- Integración completa con **Google Gemini AI**
- Análisis de sentiment en tiempo real
- Detección de patrones complejos
- Evaluación inteligente de riesgos
- Predicciones de precio a corto plazo

### 📊 **Datos en Tiempo Real**
- WebSockets de múltiples exchanges
- Procesamiento de datos ultra-rápido (<50ms latencia)
- Agregación inteligente de datos
- Historial de precios y volúmenes

### 🛡️ **Gestión de Riesgos Institucional**
- Stop-loss dinámico basado en volatilidad ATR
- Position sizing inteligente
- Límites diarios y por operación
- Monitoreo en tiempo real de drawdown
- Sistema de circuit breakers

### 📈 **Monitoreo y Alertas**
- Métricas de rendimiento en tiempo real
- Alertas por Telegram y Email
- Health checks automáticos
- Reportes de P&L
- Dashboard web (Streamlit)

### 🏗️ **Arquitectura Limpia**
- Principios SOLID y Clean Architecture
- Inyección de dependencias
- Separación clara de responsabilidades
- Código testeable y mantenible
- Patrones de diseño profesionales

## 🚀 Instalación Rápida

### Prerrequisitos
- Python 3.9 o superior
- 8GB RAM recomendados
- 5GB espacio en disco
- Conexión a internet estable

### 1. Clonar el Repositorio
```bash
git clone https://github.com/tu-usuario/Bot_Arbitraje2105.git
cd Bot_Arbitraje2105
```

### 2. Ejecutar Setup Automático
```bash
python setup.py
```

### 3. Configurar Variables de Entorno
```bash
cp .env.example .env
# Editar .env con tus API keys
```

### 4. Probar la Instalación
```bash
python test_setup.py
```

### 5. Iniciar la Plataforma
```bash
# Iniciar el servidor de producción
cd src
python main_advanced.py

# Iniciar el dashboard de Streamlit (en una nueva terminal)
streamlit run streamlit_dashboash.py
```

## ⚙️ Configuración

### Variables de Entorno Críticas

```bash
# API de IA (REQUERIDO)
GEMINI_API_KEY=tu_clave_de_gemini

# Capital inicial
INITIAL_CAPITAL=10000.00

# Símbolos a tradear
TRADING_SYMBOLS=BTCUSDT,ETHUSDT,ADAUSDT

# Estrategias habilitadas
ENABLED_STRATEGIES=scalping,day_trading

# Gestión de riesgos
MAX_DAILY_LOSS_PCT=2.0
MAX_POSITION_SIZE_PCT=10.0

# Notificaciones (OPCIONAL)
TELEGRAM_BOT_TOKEN=tu_token_de_telegram
TELEGRAM_CHAT_ID=tu_chat_id
```

### Configuración de Trading

#### Modo Paper Trading (Recomendado para Inicio)
```bash
PAPER_TRADING=true
```

#### Modo Live Trading
```bash
PAPER_TRADING=false
BINANCE_API_KEY=tu_api_key
BINANCE_SECRET_KEY=tu_secret_key
```

## 🎮 Uso

### Inicio Básico
```bash
cd src
python main_advanced.py
```

### Opciones de Línea de Comandos
```bash
# Modo verbose
python main_advanced.py --verbose

# Configuración específica
python main_advanced.py --config custom.env

# Solo una estrategia
python main_advanced.py --strategy scalping
```

### Detener la Aplicación
- **Ctrl+C**: Cierre graceful
- **Ctrl+Z**: Pausa (no recomendado)

## 📈 Estrategias de Trading

### 🏃‍♂️ Scalping Strategy

**Objetivo**: Ganancias pequeñas y frecuentes

**Parámetros**:
- Timeframe: 1 minuto
- Profit target: 0.01% - 0.1%
- Stop loss: 0.05%
- Max holding time: 30 minutos

**Indicadores**:
- RSI (7 períodos)
- MACD ultrarrápido
- Volume spike detection
- Bollinger Bands squeeze

### 📊 Day Trading Strategy

**Objetivo**: Ganancias moderadas intraday

**Parámetros**:
- Timeframes: 5m, 15m, 1h
- Profit targets: 0.5% - 3%
- Stop loss: 1%
- Max holding time: 8 horas

**Análisis**:
- Multi-timeframe consensus
- Market regime detection
- Support/resistance levels
- Trend strength analysis

### 🔄 Arbitrage Strategy

**Objetivo**: Aprovechar diferencias de precio

**Parámetros**:
- Min profit: 0.1%
- Max execution time: 30 segundos
- Fee consideration: 0.05%

## 🏗️ Arquitectura

### Capas de la Aplicación

```
📁 src/
├── 🎯 domain/              # Lógica de negocio
│   ├── entities/           # Entidades del dominio
│   ├── strategies/         # Estrategias de trading
│   ├── risk_management/    # Gestión de riesgos
│   └── trading_signals/    # Señales de trading
├── 🏗️ infrastructure/      # Infraestructura externa
│   ├── websockets/         # Conexiones WebSocket
│   ├── ai_analysis/        # Integración con IA
│   ├── real_time_data/     # Procesamiento de datos
│   ├── monitoring/         # Monitoreo del sistema
│   ├── messaging/          # Notificaciones
│   └── container/          # Inyección de dependencias
├── 🚀 application/         # Casos de uso
│   └── services/           # Servicios de aplicación
└── 📄 main_advanced.py     # Punto de entrada
```

### Principios de Diseño

- **SOLID**: Single Responsibility, Open/Closed, etc.
- **Clean Architecture**: Separación clara de capas
- **DRY**: Don't Repeat Yourself
- **KISS**: Keep It Simple, Stupid
- **Dependency Injection**: Bajo acoplamiento

## 📊 Monitoreo y Alertas

### Métricas de Rendimiento

```python
# Métricas clave monitoreadas
- P&L diario y total
- Win rate (tasa de éxito)
- Sharpe ratio
- Maximum drawdown
- Número de trades
- Latencia de ejecución
- Uso de recursos del sistema
```

### Tipos de Alertas

1. **🔴 CRÍTICAS**
   - Pérdidas excesivas
   - Fallos del sistema
   - Desconexiones prolongadas

2. **🟡 WARNING**
   - Bajo rendimiento
   - Alta latencia
   - Uso excesivo de recursos

3. **🟢 INFO**
   - Trades ejecutados
   - Reportes de rendimiento
   - Estado del sistema

### Canales de Notificación

- **Telegram**: Alertas instantáneas
- **Email**: Reportes detallados
- **Console**: Logs en tiempo real
- **Dashboard**: Visualización web

## 🛠️ Desarrollo

### Estructura del Proyecto

```bash
Bot_Arbitraje2105/
├── 📁 src/                 # Código fuente
├── 📁 tests/               # Tests automatizados
├── 📁 logs/                # Archivos de log
├── 📁 data/                # Datos y cache
├── 📁 docs/                # Documentación
├── 📄 requirements.txt     # Dependencias
├── 📄 .env.example         # Configuración ejemplo
├── 📄 setup.py             # Script de instalación
└── 📄 README.md            # Este archivo
```

### Ejecutar Tests

```bash
# Tests unitarios
pytest tests/unit/

# Tests de integración
pytest tests/integration/

# Tests con coverage
pytest --cov=src tests/

# Tests específicos
pytest tests/test_trading_engine.py -v
```

### Contribuir

1. Fork el repositorio
2. Crear una rama de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit los cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear un Pull Request

### Código de Calidad

```bash
# Formateo de código
black src/ --line-length 100
isort src/ --profile black

# Linting
pylint src/
flake8 src/

# Type checking
mypy src/

# Security check
bandit -r src/
```

## 📋 FAQ

### ❓ ¿Es seguro usar este bot?

**R**: El bot incluye múltiples capas de protección:
- Modo paper trading por defecto
- Límites estrictos de pérdidas
- Stop-loss automático
- Monitoreo continuo

### ❓ ¿Qué exchanges soporta?

**R**: Actualmente:
- ✅ Binance (completo)
- 🔄 Coinbase Pro (en desarrollo)
- 🔄 Kraken (planificado)

### ❓ ¿Cuánto capital necesito?

**R**: Recomendaciones:
- **Mínimo**: $1,000 USD
- **Recomendado**: $10,000 USD
- **Óptimo**: $50,000+ USD

### ❓ ¿Funciona 24/7?

**R**: Sí, está diseñado para:
- Operación continua
- Auto-reconexión
- Manejo de errores
- Alertas automáticas

### ❓ ¿Qué rendimientos puedo esperar?

**R**: Objetivos conservadores:
- **Daily P&L**: 0.5% - 2%
- **Monthly**: 10% - 20%
- **Win Rate**: >65%
- **Sharpe Ratio**: >1.5

**⚠️ Disclaimer**: El trading conlleva riesgos. Rendimientos pasados no garantizan resultados futuros.

## 🆘 Soporte

### Problemas Comunes

#### Error: "ModuleNotFoundError"
```bash
# Verificar virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Reinstalar dependencias
pip install -r requirements.txt
```

#### Error: "GEMINI_API_KEY not found"
```bash
# Verificar archivo .env
cat .env | grep GEMINI_API_KEY

# Obtener API key desde:
# https://aistudio.google.com/app/apikey
```

#### Error: WebSocket connection failed
```bash
# Verificar conectividad
ping api.binance.com

# Verificar configuración de proxy/firewall
```

### Logs y Debugging

```bash
# Logs detallados
LOG_LEVEL=DEBUG python main_advanced.py

# Logs específicos
tail -f logs/trading_$(date +%Y%m%d).log

# Verificar sistema
python test_setup.py
```

### Contacto y Soporte

- **📧 Email**: soporte@bot-arbitraje.com
- **💬 Telegram**: @BotArbitrajeSupport
- **🐛 Issues**: [GitHub Issues](https://github.com/tu-usuario/Bot_Arbitraje2105/issues)
- **📚 Docs**: [Documentación completa](https://docs.bot-arbitraje.com)

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## ⚠️ Disclaimer

**AVISO IMPORTANTE**: El trading de criptomonedas conlleva riesgos significativos de pérdida de capital. Este software se proporciona "tal como está" sin garantías de ningún tipo. Los desarrolladores no se hacen responsables de las pérdidas financieras que puedan resultar del uso de este software.

**Recomendaciones**:
- Comience con el modo paper trading
- Use solo capital que pueda permitirse perder
- Pruebe exhaustivamente antes del trading en vivo
- Monitoree constantemente el rendimiento
- Considere consultar con un asesor financiero

---

**🎉 ¡Feliz Trading!** 

*Desarrollado con ❤️ por el equipo de Bot_Arbitraje2105*
