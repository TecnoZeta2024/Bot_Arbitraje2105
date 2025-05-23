@echo off
REM Bot Arbitraje - Dashboard Production Startup Script for Windows
REM Uso: start_dashboard_production.bat

echo 🚀 Iniciando Bot Arbitraje Dashboard - Production Mode
echo ======================================================

REM Verificar dependencias
echo 🔍 Verificando dependencias...

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no está instalado o no está en PATH
    pause
    exit /b 1
)

REM Verificar pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip no está instalado
    pause
    exit /b 1
)

echo ✅ Python y pip encontrados

REM Verificar archivo .env
if not exist ".env" (
    echo ❌ Archivo .env no encontrado
    echo Por favor copia .env.example a .env y configura las variables
    pause
    exit /b 1
)

echo ✅ Archivo .env encontrado

REM Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    echo 🔧 Activando entorno virtual...
    call venv\Scripts\activate.bat
    echo ✅ Entorno virtual activado
) else if exist ".venv\Scripts\activate.bat" (
    echo 🔧 Activando entorno virtual...
    call .venv\Scripts\activate.bat
    echo ✅ Entorno virtual activado
) else (
    echo ⚠️ No se encontró entorno virtual, usando Python global
)

REM Instalar/actualizar dependencias
echo 📦 Verificando dependencias...
pip install -r requirements.txt --quiet

REM Verificar que Streamlit esté instalado
streamlit --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Streamlit no está instalado
    echo Instalando Streamlit...
    pip install streamlit
)

echo ✅ Dependencias verificadas

REM Verificar estructura de directorios
echo 📁 Verificando estructura de directorios...

REM Crear directorios necesarios si no existen
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "cache" mkdir cache
if not exist "reports" mkdir reports

echo ✅ Estructura de directorios verificada

REM Verificar configuración crítica
echo 🔧 Verificando configuración...

REM Verificar variables de entorno críticas usando findstr
findstr /c:"SUPABASE_URL=" .env >nul && findstr /c:"SUPABASE_KEY=" .env >nul
if errorlevel 1 (
    echo ⚠️ Configuración de Supabase incompleta
) else (
    echo ✅ Configuración de Supabase encontrada
)

findstr /c:"BINANCE_API_KEY=" .env >nul
if errorlevel 1 (
    echo ⚠️ Configuración de Binance no encontrada
) else (
    echo ✅ Configuración de Binance encontrada
)

REM Verificar puerto (simplificado para Windows)
set PORT=8501
echo ✅ Usando puerto: %PORT%

REM Crear log del inicio
echo 📝 Creando log de inicio...
set LOG_FILE=logs\dashboard_startup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
echo Inicio del dashboard: %date% %time% > "%LOG_FILE%"

REM Mensaje de inicio
echo.
echo 🎉 ¡Todo listo para iniciar el dashboard!
echo ======================================
echo.
echo 🌐 El dashboard se abrirá en: http://localhost:%PORT%
echo 📝 Logs disponibles en: %LOG_FILE%
echo 🛑 Para detener: Ctrl+C
echo.
echo ⚡ Iniciando Streamlit Dashboard...
echo.

REM Iniciar Streamlit con configuración de producción
streamlit run dashboard_production.py ^
    --server.port=%PORT% ^
    --server.address=0.0.0.0 ^
    --server.headless=true ^
    --server.runOnSave=false ^
    --server.fileWatcherType=none ^
    --browser.gatherUsageStats=false ^
    --logger.level=info

pause
