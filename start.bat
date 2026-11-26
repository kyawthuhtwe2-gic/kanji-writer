
@echo off
title Japanese Handwriting Practice - Trackpad Only
cd /d "%~dp0"

echo ==========================================
echo Japanese Handwriting Practice
echo ==========================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found.
    echo Please run install.bat first.
    pause
    exit /b 1
)

echo Checking PySide6 installation...

"venv\Scripts\python.exe" -c "import PySide6" 2>nul

if errorlevel 1 (
    echo.
    echo ERROR: Required packages are missing.
    echo Please run install.bat first.
    pause
    exit /b 1
)

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

echo.
echo Application closed successfully.
pause
