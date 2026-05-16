@'
@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo ==========================================
echo   Hermes Agent OS
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python or add it to PATH.
    pause
    exit /b 1
)

echo [*] Starting Hermes server...
echo [*] Dashboard URL: http://localhost:8000/dashboard.html
echo.

start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8000/dashboard.html"

python start_hermes.py

echo.
echo [*] Hermes stopped.
pause
'@ | Set-Content -Path .\RUN_HERMES.bat -Encoding ASCII