
@echo off
title Japanese Handwriting Practice - Installer
cd /d "%~dp0"

echo ==========================================
echo Japanese Handwriting Practice - Installation
echo ==========================================

echo.
echo [1/4] Checking Python 3.11 or newer...

py -3 --version
if errorlevel 1 (
    echo ERROR: Python 3.11 or newer is required.
    pause
    exit /b 1
)

py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.11 or newer is required.
    pause
    exit /b 1
)

echo.
echo [2/4] Creating virtual environment if needed...

if not exist "venv\Scripts\python.exe" (
    py -3 -m venv venv
    if errorlevel 1 goto error
)

echo.
echo [3/4] Installing dependencies...

venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error

echo.
echo [4/4] Testing installed packages...

venv\Scripts\python.exe -c "import PySide6; print('PySide6:', PySide6.__version__)"
if errorlevel 1 goto error

echo.
echo ==========================================
echo INSTALLATION SUCCESSFUL!
echo ==========================================
echo Run start.bat to launch the touchpad-only application.
pause
exit /b 0

:error
echo.
echo ==========================================
echo INSTALLATION FAILED!
echo ==========================================
echo Check your Python version and internet connection.
pause
exit /b 1
