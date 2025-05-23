@echo off
title Bot Arbitraje 2105 - Production Server
echo ========================================
echo   BOT ARBITRAJE 2105 - PRODUCTION START
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9+ from python.org
    pause
    exit /b 1
)

echo [1/4] Checking dependencies...
python diagnose_dependencies.py >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Some dependencies may be missing
    echo Run update_dependencies.bat to fix
    pause
)

echo [2/4] Starting Production Server...
cd /d "%~dp0"
start "Bot Arbitraje - Production Server" cmd /k "python src\launch_production_clean.py"

echo [3/4] Waiting for server to initialize...
timeout /t 5 /nobreak > nul

echo [4/4] Starting Frontend...
if exist frontend\package.json (
    start "Bot Arbitraje - Frontend" cmd /k "cd frontend && npm run dev"
) else (
    echo [WARNING] Frontend directory not found
    echo Server will run without frontend
)

echo.
echo ========================================
echo   SYSTEM STARTED SUCCESSFULLY!
echo ========================================
echo.
echo Production Server: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo WebSocket: ws://localhost:8000/ws
echo.
if exist frontend\package.json (
    echo Frontend: http://localhost:5173
    echo.
    echo Press any key to open the dashboard...
    pause > nul
    start http://localhost:5173
) else (
    echo API Health Check: http://localhost:8000/api/health
    echo.
    echo Press any key to open API docs...
    pause > nul
    start http://localhost:8000/docs
)
