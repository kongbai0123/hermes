$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

py -3.12 -m PyInstaller `
  --onefile `
  --name WorkAgent `
  --clean `
  --distpath "$Root\dist" `
  --workpath "$Root\build" `
  --specpath "$Root" `
  simple_agent_app.py

Write-Host "Built: $Root\dist\WorkAgent.exe"
