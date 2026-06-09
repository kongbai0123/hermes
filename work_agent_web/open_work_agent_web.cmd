@echo off
setlocal
cd /d "%~dp0"

if not exist "dist\index.js" (
  echo [Work Agent Web] Build output not found. Running build first...
  call npm run build
  if errorlevel 1 (
    echo [Work Agent Web] Build failed.
    pause
    exit /b 1
  )
)

start /b powershell -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process 'http://localhost:3000'"
node dist\index.js
exit /b 0
