@echo off
title Click-Free Touchpad Diagnostic
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Run start.bat first (it sets up the environment).
    pause
    exit /b 1
)

"venv\Scripts\python.exe" -m tools.touchpad_diagnostic
if errorlevel 1 (
    echo.
    echo Touchpad diagnostic failed to start.
    pause
    exit /b 1
)
