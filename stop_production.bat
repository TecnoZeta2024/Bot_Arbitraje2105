@echo off
echo ========================================
echo   BOT ARBITRAJE 2105 - STOPPING SYSTEM
echo ========================================
echo.

echo Stopping all processes...

taskkill /F /FI "WindowTitle eq Bot Arbitraje - Production Server*" 2>nul
taskkill /F /FI "WindowTitle eq Bot Arbitraje - Frontend*" 2>nul

echo.
echo System stopped successfully.
echo.
pause
