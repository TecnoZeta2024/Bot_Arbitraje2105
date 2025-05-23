#!/bin/bash
# Bot Arbitraje - Dashboard Production Startup Script
# Uso: ./start_dashboard_production.sh

echo "🚀 Iniciando Bot Arbitraje Dashboard - Production Mode"
echo "======================================================"

# Verificar dependencias
echo "🔍 Verificando dependencias..."

# Verificar Python
if ! command -v python &> /dev/null; then
    echo "❌ Python no está instalado"
    exit 1
fi

# Verificar pip
if ! command -v pip &> /dev/null; then
    echo "❌ pip no está instalado"
    exit 1
fi

echo "✅ Python y pip encontrados"

# Verificar archivo .env
if [ ! -f ".env" ]; then
    echo "❌ Archivo .env no encontrado"
    echo "Por favor copia .env.example a .env y configura las variables"
    exit 1
fi

echo "✅ Archivo .env encontrado"

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "🔧 Activando entorno virtual..."
    source venv/bin/activate || source venv/Scripts/activate
    echo "✅ Entorno virtual activado"
elif [ -d ".venv" ]; then
    echo "🔧 Activando entorno virtual..."
    source .venv/bin/activate || source .venv/Scripts/activate
    echo "✅ Entorno virtual activado"
else
    echo "⚠️ No se encontró entorno virtual, usando Python global"
fi

# Instalar/actualizar dependencias
echo "📦 Verificando dependencias..."
pip install -r requirements.txt --quiet

# Verificar que Streamlit esté instalado
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit no está instalado"
    echo "Instalando Streamlit..."
    pip install streamlit
fi

echo "✅ Dependencias verificadas"

# Verificar estructura de directorios
echo "📁 Verificando estructura de directorios..."

# Crear directorios necesarios si no existen
mkdir -p logs
mkdir -p data
mkdir -p cache
mkdir -p reports

echo "✅ Estructura de directorios verificada"

# Verificar configuración crítica
echo "🔧 Verificando configuración..."

# Verificar variables de entorno críticas
if grep -q "SUPABASE_URL=" .env && grep -q "SUPABASE_KEY=" .env; then
    echo "✅ Configuración de Supabase encontrada"
else
    echo "⚠️ Configuración de Supabase incompleta"
fi

if grep -q "BINANCE_API_KEY=" .env; then
    echo "✅ Configuración de Binance encontrada"
else
    echo "⚠️ Configuración de Binance no encontrada"
fi

# Verificar puerto disponible
PORT=8501
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️ Puerto $PORT está ocupado"
    echo "Buscando puerto alternativo..."
    for port in {8502..8510}; do
        if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            PORT=$port
            break
        fi
    done
    echo "✅ Usando puerto alternativo: $PORT"
else
    echo "✅ Puerto $PORT disponible"
fi

# Crear log del inicio
echo "📝 Creando log de inicio..."
LOG_FILE="logs/dashboard_startup_$(date +%Y%m%d_%H%M%S).log"
echo "Inicio del dashboard: $(date)" > "$LOG_FILE"

# Mensaje de inicio
echo ""
echo "🎉 ¡Todo listo para iniciar el dashboard!"
echo "======================================"
echo ""
echo "🌐 El dashboard se abrirá en: http://localhost:$PORT"
echo "📝 Logs disponibles en: $LOG_FILE"
echo "🛑 Para detener: Ctrl+C"
echo ""
echo "⚡ Iniciando Streamlit Dashboard..."
echo ""

# Iniciar Streamlit con configuración de producción
streamlit run dashboard_production.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.runOnSave=false \
    --server.fileWatcherType=none \
    --browser.gatherUsageStats=false \
    --logger.level=info \
    2>&1 | tee -a "$LOG_FILE"
