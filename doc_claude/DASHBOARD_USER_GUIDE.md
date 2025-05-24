# 📊 Bot Arbitraje - Dashboard de Trading
## Guía de Usuario y Manual de Operación - Versión Production Ready

### 🎯 Visión General

El Dashboard de Trading del Bot Arbitraje es una interfaz web moderna y completa que permite monitorear, controlar y analizar todas las operaciones de trading automatizado. Desarrollado con Streamlit y siguiendo arquitectura Clean Architecture, el dashboard integra todos los componentes del sistema para una experiencia unificada.

---

## 🚀 Inicio Rápido

### Prerequisitos
- Python 3.8 o superior
- Conexión a internet estable
- Variables de entorno configuradas en `.env`
- Backend API corriendo (opcional para modo desarrollo)

### Inicio Automático

**Linux/Mac:**
```bash
chmod +x start_dashboard_production.sh
./start_dashboard_production.sh
```

**Windows:**
```cmd
start_dashboard_production.bat
```

**Manual:**
```bash
streamlit run dashboard_production.py
```

### URLs de Acceso
- **Local:** http://localhost:8501
- **Red local:** http://[TU_IP]:8501

---

## 🎛️ Características Principales

### ✅ **Sistema de Importaciones Robusto**
- Manejo automático de errores de importación
- Objetos mock para desarrollo sin dependencias
- Indicadores visuales de estado de módulos
- Continúa funcionando incluso con módulos faltantes

### ✅ **WebSocket en Tiempo Real**
- Reconexión automática con backoff exponencial
- Manejo robusto de desconexiones
- Indicadores de estado de conexión
- Buffer de mensajes inteligente

### ✅ **Monitoreo del Sistema**
- Health checks automáticos
- Métricas de rendimiento en tiempo real
- Sistema de alertas visual
- Estado de todos los componentes

### ✅ **Gestión de Riesgos Avanzada**
- Configuración interactiva de parámetros
- Semáforos visuales de riesgo
- Métricas de exposición y drawdown
- Alertas de eventos críticos

### ✅ **Integración con Base de Datos**
- Conexión automática con Supabase
- Datos históricos de operaciones
- Cálculo de métricas de rendimiento
- Persistencia de configuración

---

## 📋 Pestañas del Dashboard

### 🏠 **Inicio**
**Propósito:** Vista general del estado del sistema
- **Estado General:** Salud de todos los componentes
- **Portfolio:** Valor actual, P&L diario y total
- **Actividad Reciente:** Últimas operaciones ejecutadas
- **Datos de Mercado:** Precios y cambios en tiempo real

**Métricas Clave:**
- Estado general del sistema (🟢/🟡/🔴)
- Alertas activas
- Valor del portfolio
- P&L diario y acumulado

### 📈 **Estrategias**
**Propósito:** Control y configuración de estrategias de trading
- **Controles de Trading:** Iniciar/Pausar/Detener sistema
- **Configuración de Estrategias:** Activar/desactivar estrategias
- **Señales Recientes:** Últimas señales generadas
- **Estado de Ejecución:** Operaciones en curso

**Estrategias Disponibles:**
- 🏃‍♂️ **Scalping:** Operaciones ultrarrápidas (1-5 min)
- 📅 **Day Trading:** Operaciones intradía (15m-4h)
- 🔄 **Arbitraje Simple:** Diferencias entre exchanges
- 🔺 **Arbitraje Triangular:** Ciclos de 3 pares (1-3 min)

### ⚠️ **Riesgos**
**Propósito:** Monitoreo y control de riesgos de trading
- **Métricas Actuales:** Capital, exposición, P&L
- **Configuración de Límites:** Sliders interactivos
- **Semáforos de Riesgo:** Indicadores visuales
- **Alertas de Eventos:** Notificaciones críticas

**Parámetros Configurables:**
- Pérdida diaria máxima (%)
- Tamaño máximo por posición (%)
- Exposición total máxima (%)
- Multiplicadores de stop-loss y take-profit

### 🚨 **Alertas**
**Propósito:** Registro de eventos y alertas del sistema
- **Resumen de Alertas:** Conteo por nivel de severidad
- **Log General:** Historial completo de eventos
- **Señales de Trading:** Alertas de oportunidades
- **Filtros:** Por nivel, fecha, componente

**Tipos de Alertas:**
- 🔴 **Errores:** Fallos críticos del sistema
- 🟡 **Advertencias:** Situaciones que requieren atención
- 🔵 **Información:** Eventos informativos

### 📊 **Métricas**
**Propósito:** Análisis de rendimiento y datos de mercado
- **Datos de Mercado:** Precios en tiempo real
- **Gráficos de Precios:** Evolución temporal
- **Métricas de Trading:** Win rate, profit total
- **Análisis de Rendimiento:** Sharpe ratio, drawdown

**Visualizaciones:**
- Gráficos de líneas para precios
- Métricas de rendimiento calculadas
- Profit acumulativo en el tiempo
- Distribución de ganancias/pérdidas

### ⚙️ **Configuración**
**Propósito:** Configuración del sistema y variables
- **Variables de Entorno:** Estado de configuración
- **Modo de Operación:** Testnet vs Mainnet
- **Herramientas:** Pruebas de conexión
- **Estado del Sistema:** Información técnica

**Configuraciones Críticas:**
- API Keys (Binance, Mobula, etc.)
- URLs de servicios
- Parámetros de trading
- Modo de operación (seguridad)

---

## 🔧 Configuración Técnica

### Variables de Entorno Requeridas (.env)
```bash
# APIs de Trading
BINANCE_API_KEY=tu_api_key_aqui
BINANCE_SECRET_KEY=tu_secret_key_aqui
BINANCE_TESTNET=True  # False para trading real

# Base de Datos
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_anon_key_aqui

# APIs Externas
MOBULA_API_KEY=tu_mobula_key_aqui
COINGECKO_API_KEY=tu_coingecko_key_aqui

# Telegram (opcional)
TELEGRAM_BOT_TOKEN=tu_bot_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui

# Servidor
API_HOST=localhost
API_PORT=8001

# Trading
CAPITAL_INICIAL=10000.0
UMBRAL_RENTABILIDAD=0.5
```

### Dependencias del Sistema
```bash
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.0.0
websockets>=11.0
requests>=2.28.0
supabase>=1.0.0
python-dotenv>=1.0.0
asyncio
```

### Puertos Utilizados
- **Dashboard:** 8501 (predeterminado)
- **Backend API:** 8001
- **WebSocket:** 8001/ws

---

## 🔍 Resolución de Problemas

### Problemas Comunes

#### ❌ **Error de Importación de Módulos**
**Síntoma:** Mensajes de error rojos sobre módulos no encontrados
**Solución:**
1. Verificar que todas las dependencias estén instaladas
2. Activar entorno virtual si es necesario
3. El dashboard continuará funcionando en modo limitado

#### ❌ **WebSocket No Conecta**
**Síntoma:** Indicador rojo "Desconectado" en sidebar
**Solución:**
1. Verificar que el backend API esté corriendo en puerto 8001
2. Verificar firewall y permisos de red
3. El dashboard intentará reconectar automáticamente

#### ❌ **Supabase No Responde**
**Síntoma:** Advertencia de conexión con base de datos
**Solución:**
1. Verificar SUPABASE_URL y SUPABASE_KEY en .env
2. Verificar conectividad a internet
3. Comprobar estado del servicio Supabase

#### ❌ **Puerto Ocupado**
**Síntoma:** Error al iniciar sobre puerto en uso
**Solución:**
```bash
# Encontrar proceso usando el puerto
netstat -ano | findstr :8501  # Windows
lsof -i :8501  # Linux/Mac

# Terminar proceso o usar puerto alternativo
streamlit run dashboard_production.py --server.port=8502
```

### Logs y Debugging

**Ubicación de Logs:**
- `logs/dashboard_startup_[fecha].log` - Logs de inicio
- `logs/streamlit_[fecha].log` - Logs de Streamlit
- Console output en tiempo real

**Modo Debug:**
```bash
# Activar logging detallado
export STREAMLIT_LOGGER_LEVEL=debug
streamlit run dashboard_production.py --logger.level=debug
```

---

## 🛡️ Seguridad y Mejores Prácticas

### ✅ **Configuración Segura**
- Usar variables de entorno para credenciales
- Nunca hardcodear API keys en el código
- Mantener `.env` fuera del control de versiones
- Usar HTTPS en producción

### ✅ **Modo Testnet Recomendado**
- Comenzar siempre con `BINANCE_TESTNET=True`
- Probar todas las funcionalidades en testnet
- Solo cambiar a mainnet después de pruebas extensivas

### ✅ **Monitoreo Continuo**
- Revisar alertas regularmente
- Monitorear métricas de riesgo
- Verificar logs por errores
- Mantener backups de configuración

### ✅ **Límites de Riesgo**
- Configurar límites conservadores inicialmente
- Nunca arriesgar más del 2% del capital por operación
- Mantener exposición total bajo 80%
- Establecer límites de pérdida diaria

---

## 📈 Optimización de Rendimiento

### Configuraciones Recomendadas

**Para Trading de Alta Frecuencia:**
- Actualización cada 1 segundo
- Buffer WebSocket pequeño (50 mensajes)
- Límites de exposición más restrictivos

**Para Trading Conservador:**
- Actualización cada 5 segundos
- Buffer WebSocket mayor (200 mensajes)
- Límites de riesgo más amplios

**Para Desarrollo/Testing:**
- Modo mock activado
- Logging detallado
- Alertas de debugging habilitadas

---

## 🆘 Soporte y Contacto

### Recursos de Ayuda
- **Documentación técnica:** `/docs` directory
- **Logs del sistema:** `/logs` directory
- **Configuración:** `.env` y `config.toml`

### Comandos Útiles
```bash
# Reiniciar dashboard
pkill -f streamlit && ./start_dashboard_production.sh

# Verificar estado del sistema
curl http://localhost:8001/health

# Ver logs en tiempo real
tail -f logs/dashboard_startup_$(date +%Y%m%d)*.log

# Backup de configuración
cp .env .env.backup.$(date +%Y%m%d)
```

---

## 🔄 Actualizaciones y Mantenimiento

### Actualización del Dashboard
1. Detener el dashboard (Ctrl+C)
2. Actualizar código desde repositorio
3. Actualizar dependencias: `pip install -r requirements.txt`
4. Reiniciar con script de producción

### Mantenimiento Regular
- **Diario:** Revisar alertas y métricas de riesgo
- **Semanal:** Verificar logs por errores
- **Mensual:** Actualizar dependencias y configuración
- **Trimestral:** Backup completo del sistema

---

**✨ ¡El dashboard está listo para operación en producción!**

Para soporte adicional, consultar la documentación técnica en `/docs` o revisar los logs del sistema en `/logs`.
