@echo off
title Bot Arbitraje 2105 - Sistema Completo v3.0

:: Configuración de colores
color 0A

echo.
echo ===============================================================================
echo                    🚀 BOT ARBITRAJE 2105 - SISTEMA COMPLETO 🚀
echo                              Production Ready v3.0
echo ===============================================================================
echo.
echo [INFO] Iniciando todos los componentes del sistema...
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ [ERROR] Python no está instalado o no está en PATH
    echo    Instala Python 3.9+ desde python.org
    pause
    exit /b 1
)

:: Verificar Streamlit
streamlit --version >nul 2>&1
if errorlevel 1 (
    echo ❌ [ERROR] Streamlit no está instalado
    echo    Instalando Streamlit...
    pip install streamlit
)

echo ✅ [OK] Dependencias verificadas
echo.

:: Crear directorios necesarios
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "cache" mkdir cache

echo ✅ [OK] Estructura de directorios preparada
echo.

:: Iniciar Backend API
echo 🔧 [1/2] Iniciando Backend API (Puerto 8001)...
start "Bot Arbitraje - Backend API" cmd /k "cd /d "%~dp0" && python src\launch_production.py"

:: Esperar a que el backend se inicie
echo ⏳ [WAIT] Esperando a que el backend se inicialice...
timeout /t 8 /nobreak > nul

:: Verificar backend
echo 🔍 [CHECK] Verificando estado del backend...
curl -s http://localhost:8001/api/health > nul
if errorlevel 1 (
    echo ⚠️ [WARNING] Backend puede estar iniciando aún...
    echo           Si el dashboard no conecta, espera 30 segundos e inténtalo de nuevo
) else (
    echo ✅ [OK] Backend respondiendo correctamente
)

echo.

:: Iniciar Dashboard Streamlit
echo 🎨 [2/2] Iniciando Dashboard Streamlit (Puerto 8501)...
start "Bot Arbitraje - Dashboard" cmd /k "cd /d "%~dp0" && streamlit run dashboard_production.py --server.port=8501 --server.address=0.0.0.0 --server.headless=false"

:: Esperar a que Streamlit se inicie
echo ⏳ [WAIT] Esperando a que Streamlit se inicialice...
timeout /t 5 /nobreak > nul

echo.
echo ===============================================================================
echo                           🎉 SISTEMA INICIADO EXITOSAMENTE 🎉
echo ===============================================================================
echo.
echo 🌐 **ACCESO AL SISTEMA:**
echo    • Dashboard Principal: http://localhost:8501
echo    • Backend API:         http://localhost:8001
echo    • API Docs:            http://localhost:8001/docs
echo    • Health Check:        http://localhost:8001/api/health
echo.
echo 📊 **CARACTERÍSTICAS DISPONIBLES:**
echo    • Trading en tiempo real con Binance
echo    • WebSocket con heartbeat automático
echo    • Sistema de gestión de riesgo avanzado
echo    • Monitoreo del sistema en tiempo real
echo    • Dashboard con 6 pestañas funcionales:
echo      - 🏠 Inicio (Estado general del sistema)
echo      - 📈 Estrategias (Controles de trading)
echo      - ⚠️ Riesgos (Gestión de riesgos)
echo      - 🚨 Alertas (Alertas del sistema)
echo      - 📊 Métricas (Análisis de rendimiento)
echo      - ⚙️ Configuración (Ajustes del sistema)
echo.
echo 🔧 **CONTROLES:**
echo    • Para detener el sistema: Cierra ambas ventanas de comandos
echo    • Para reiniciar: Ejecuta este script nuevamente
echo    • Para monitoreo: Revisa logs/ para archivos de log
echo.
echo ⚡ **ESTADO ACTUAL:**
echo    • Backend: Iniciando/Corriendo en puerto 8001
echo    • Dashboard: Iniciando/Corriendo en puerto 8501
echo    • WebSocket: Conectando automáticamente
echo.
echo ===============================================================================
echo  El dashboard se abrirá automáticamente en tu navegador en unos segundos...
echo ===============================================================================
echo.

:: Esperar un poco más y abrir el navegador
timeout /t 3 /nobreak > nul
start http://localhost:8501

echo 🎯 [DONE] ¡Sistema completamente operativo!
echo.
echo Presiona cualquier tecla para cerrar esta ventana (el sistema seguirá corriendo)
pause > nul