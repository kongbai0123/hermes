$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

py -3.12 -m pip install pyinstaller
py -3.12 -m PyInstaller --clean --onefile --name LocalAgentTutor LocalAgentTutor.py
py -3.12 -m PyInstaller --clean --onefile --name LocalAgentTutorUI tutor_ui.py
py -3.12 -m PyInstaller --clean --onefile --name LocalAgentTutorMCP mcp_agent\server.py

Write-Host ""
Write-Host "Build complete:"
Write-Host "$root\dist\LocalAgentTutor.exe"
Write-Host "$root\dist\LocalAgentTutorUI.exe"
Write-Host "$root\dist\LocalAgentTutorMCP.exe"
