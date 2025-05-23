@echo off
echo ========================================
echo   BOT ARBITRAJE 2105 - OPTIMIZED START
echo ========================================
echo.

echo [1/3] Starting Production Server...
cd /d "%~dp0"
start "Bot Arbitraje - Production Server" cmd /k "python src\launch_production.py"

echo [2/3] Waiting for server to initialize...
timeout /t 5 /nobreak > nul

echo [3/3] Starting Frontend...
start "Bot Arbitraje - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   SYSTEM STARTED SUCCESSFULLY!
echo ========================================
echo.
echo Production Server: http://localhost:8000
echo Frontend: http://localhost:5173
echo WebSocket: ws://localhost:8000/ws
echo.
echo If you encounter any issues:
echo 1. Run: python diagnose_dependencies.py
echo 2. Update deps: update_dependencies.bat
echo.
echo Press any key to open the dashboard in your browser...
pause > nul

start http://localhost:5173
