@echo off
title Hermes Agent OS Launcher
echo ==========================================
echo    Hermes Agent OS is starting...
echo ==========================================

:: 1. 檢查 Python 是否安裝
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [Error] Python is not installed or not in PATH.
    pause
    exit /b
)

:: 2. 在背景啟動伺服器
echo [*] Launching Backend Server...
start /b python start_hermes.py

:: 3. 等待一秒確保伺服器啟動
timeout /t 2 /nobreak >nul

:: 4. 自動開啟瀏覽器進入儀表板
echo [*] Opening Dashboard in Browser...
start http://localhost:8000/dashboard.html

echo ==========================================
echo    Hermes is now running in background.
echo    Close this window to stop the server.
echo ==========================================
pause
