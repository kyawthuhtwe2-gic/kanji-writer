@echo off
title Build Kanji Writer Installer
cd /d "%~dp0"

echo ==========================================
echo Build Kanji Writer (exe + installer)
echo ==========================================

if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3 -m venv venv
    if errorlevel 1 goto build_error
)

echo [1/4] Installing dependencies...
"venv\Scripts\python.exe" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto build_error

echo [2/4] Building executable...
"venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name KanjiWriter ^
    --add-data "practice\strokes;practice\strokes" ^
    main.py
if errorlevel 1 goto build_error

if exist "release" rmdir /s /q "release"
mkdir "release"

echo [3/4] Locating Inno Setup...
set "ISCC="
for %%P in (
    "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    "%ProgramFiles%\Inno Setup 6\ISCC.exe"
    "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
) do if exist %%P set "ISCC=%%~P"

if not defined ISCC (
    echo Inno Setup not found. Installing with winget...
    winget install --id JRSoftware.InnoSetup -e --silent --accept-package-agreements --accept-source-agreements
    for %%P in (
        "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
        "%ProgramFiles%\Inno Setup 6\ISCC.exe"
        "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
    ) do if exist %%P set "ISCC=%%~P"
)

if not defined ISCC (
    echo.
    echo Inno Setup missing. Install from https://jrsoftware.org/isdl.php then rerun.
    pause
    exit /b 1
)

echo [4/4] Creating installer...
"%ISCC%" installer.iss
if errorlevel 1 goto build_error

echo.
echo Done.
echo Installer: release\KanjiWriter-Setup.exe
start "" "release"
pause
exit /b 0

:build_error
echo.
echo ==========================================
echo BUILD FAILED
echo ==========================================
pause
exit /b 1
