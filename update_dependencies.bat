@echo off
echo ========================================
echo   BOT ARBITRAJE 2105 - DEPENDENCY UPDATE
echo ========================================
echo.

echo [1/5] Creating backup of current requirements...
copy requirements.txt requirements_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.txt

echo.
echo [2/5] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [3/5] Installing optimized dependencies...
python -m pip install -r requirements_optimized.txt --upgrade

echo.
echo [4/5] Verifying installation...
python diagnose_dependencies.py

echo.
echo [5/5] Installation complete!
echo.
echo ========================================
echo   Next steps:
echo   1. Run: python src\launch_production.py
echo   2. Or use: start_production_optimized.bat
echo ========================================
pause
