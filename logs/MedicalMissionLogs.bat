@echo off
REM ───────────────────────────────────────────
REM  Medical Mission Logs — Windows Launcher
REM  Double-click this file to start the app.
REM ───────────────────────────────────────────

cd /d "%~dp0"

echo.
echo   ================================================
echo    Medical Mission Logs
echo   ================================================
echo.

REM Check for Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo   Python is not installed.
    echo   Please install it from https://www.python.org/downloads/
    echo   IMPORTANT: Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Install dependencies if needed
python -c "import flask" 2>nul
if %ERRORLEVEL% neq 0 (
    echo   Installing required packages...
    python -m pip install -r requirements.txt
    echo.
)

REM Start the app (opens browser automatically)
python start.py

pause
