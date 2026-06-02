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

start "Work Agent Web Server" cmd /k "cd /d %~dp0 && node dist\index.js"
powershell -NoProfile -Command "Start-Sleep -Seconds 3; Start-Process 'http://localhost:3000'"

echo [Work Agent Web] Browser should open at http://localhost:3000
exit /b 0
