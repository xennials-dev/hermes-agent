@echo off
REM Windows CMD launcher for Hermes Agent
setlocal
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -m hermes_cli.main %*
) else if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" -m hermes_cli.main %*
) else (
    python "%~dp0hermes" %*
)
endlocal
