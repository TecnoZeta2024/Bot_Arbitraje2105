@echo off
title Bot Arbitraje 2105 - Detener Sistema

echo.
echo ===============================================================================
echo                       🛑 DETENIENDO BOT ARBITRAJE 2105 🛑
echo ===============================================================================
echo.

echo 🔍 Buscando procesos del Bot Arbitraje...

:: Detener procesos de Python relacionados con el bot
echo 🔧 Deteniendo Backend API...
taskkill /f /im python.exe /fi "WINDOWTITLE eq Bot Arbitraje - Backend API" 2>nul
if errorlevel 1 (
    echo ⚠️ No se encontró proceso del Backend API corriendo
) else (
    echo ✅ Backend API detenido
)

echo.
echo 🎨 Deteniendo Dashboard Streamlit...
taskkill /f /im python.exe /fi "WINDOWTITLE eq Bot Arbitraje - Dashboard" 2>nul
if errorlevel 1 (
    echo ⚠️ No se encontró proceso del Dashboard corriendo
) else (
    echo ✅ Dashboard Streamlit detenido
)

echo.
echo 🧹 Limpiando procesos residuales...

:: Buscar y detener procesos que usen los puertos específicos
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8001') do (
    taskkill /f /pid %%a 2>nul >nul
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8501') do (
    taskkill /f /pid %%a 2>nul >nul
)

echo ✅ Procesos residuales limpiados

echo.
echo ===============================================================================
echo                        ✅ SISTEMA COMPLETAMENTE DETENIDO ✅
echo ===============================================================================
echo.
echo 📊 **ESTADO ACTUAL:**
echo    • Backend API (Puerto 8001): DETENIDO
echo    • Dashboard Streamlit (Puerto 8501): DETENIDO
echo    • Procesos WebSocket: DETENIDOS
echo.
echo 🔧 **PARA REINICIAR EL SISTEMA:**
echo    Ejecuta: start_complete_system.bat
echo.
echo 📁 **LOGS CONSERVADOS:**
echo    Los archivos de log se mantienen en el directorio logs/
echo.

timeout /t 3 /nobreak > nul
echo Presiona cualquier tecla para cerrar...
pause > nul