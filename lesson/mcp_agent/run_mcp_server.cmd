@echo off
setlocal
set "ROOT=%~dp0.."
set "LOCAL_AGENT_TUTOR_ROOT=%ROOT%"
if exist "%ROOT%\dist\LocalAgentTutorMCP.exe" (
  "%ROOT%\dist\LocalAgentTutorMCP.exe"
) else (
  py -3.12 "%~dp0server.py"
)
