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
start "Bot Arbitraje - Production Server" cmd /k ".\.venv\Scripts\activate && python src\launch_production.py"

echo [3/4] Waiting for server to initialize...
timeout /t 5 /nobreak > nul

echo.
echo ========================================
echo   SYSTEM STARTED SUCCESSFULLY!
echo ========================================
echo.
echo Production Server: http://localhost:8001
echo API Documentation: http://localhost:8001/docs
echo WebSocket: ws://localhost:8001/ws
echo.
echo Press any key to open the Streamlit dashboard...
pause > nul
start http://localhost:8501
