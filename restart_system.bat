@echo off
echo ===================================================
echo Bot Arbitraje - Reinicio Rapido del Sistema
echo ===================================================

echo.
echo [1] Deteniendo servicios existentes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [2] Limpiando logs anteriores...
if exist logs\production_server.log (
    move /Y logs\production_server.log logs\production_server_old.log 2>nul
)

echo.
echo [3] Iniciando Backend (Puerto 8001)...
cd /d "C:\Users\zamor\Bot_Arbitraje2105"
start "Bot Arbitraje - Backend" cmd /k ".\.venv\Scripts\activate && python src\launch_production.py"

echo.
echo [4] Esperando que el backend se inicie...
timeout /t 5 /nobreak >nul

echo.
echo [5] Iniciando Frontend (Puerto 5173)...
cd /d "C:\Users\zamor\Bot_Arbitraje2105\frontend"
start "Bot Arbitraje - Frontend" cmd /k "npm run dev"

echo.
echo ===================================================
echo Sistema iniciado exitosamente!
echo.
echo Backend:  http://localhost:8001
echo Frontend: http://localhost:5173
echo.
echo Verifica la consola del navegador (F12) para ver
echo si los WebSockets se conectan correctamente.
echo ===================================================
echo.
pause
