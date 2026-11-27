@echo off
title Japanese Handwriting Practice
cd /d "%~dp0"

echo ==========================================
echo Kanji Writer
echo ==========================================

rem ---- Setup: runs only when the environment is missing or incomplete ----
if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" -c "import PySide6" 2>nul
    if not errorlevel 1 goto run
)

echo.
echo First-time setup (needs internet)...
echo.
echo [1/3] Checking Python 3.11 or newer...

py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.11 or newer is required.
    pause
    exit /b 1
)

echo [2/3] Creating virtual environment if needed...

if not exist "venv\Scripts\python.exe" (
    py -3 -m venv venv
    if errorlevel 1 goto setup_error
)

echo [3/3] Installing dependencies...

"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto setup_error

"venv\Scripts\python.exe" -c "import PySide6; print('PySide6:', PySide6.__version__)"
if errorlevel 1 goto setup_error

echo.
echo Setup complete.

:run
echo.
echo Starting application...
echo.

"venv\Scripts\python.exe" main.py

if errorlevel 1 (
    echo.
    echo ==========================================
    echo APPLICATION ERROR
    echo ==========================================
    echo Please check the error message above.
    pause
    exit /b 1
)
exit /b 0

:setup_error
echo.
echo ==========================================
echo SETUP FAILED
echo ==========================================
echo Check your Python version and internet connection.
pause
exit /b 1
