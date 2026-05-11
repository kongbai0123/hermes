@echo off
title Hermes Git Push Tool
echo ========================================
echo   HERMES AGENT OS - GIT DEPLOY
echo ========================================
echo.
echo [*] Checking local changes...
git status -s
echo.
echo [?] Enter commit message (or press Enter for 'Update Hermes'):
set /p msg=Message: 
if "%msg%"=="" set msg=Update Hermes %date%
echo.
echo [*] Preparing to push...
echo [*] Message: %msg%
echo.
echo [+] Git Add...
git add .
echo [+] Git Commit...
git commit -m "%msg%"
echo [+] Git Push...
git push origin main
if %errorlevel% equ 0 (
echo.
echo ========================================
echo   SUCCESS: GITHUB UPDATED!
echo ========================================
) else (
echo.
echo ========================================
echo   ERROR: FAILED TO PUSH.
echo ========================================
)
echo.
pause
