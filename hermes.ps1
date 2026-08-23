# PowerShell launcher for Hermes Agent in development checkout
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (Test-Path "$ScriptDir\.venv\Scripts\python.exe") {
    & "$ScriptDir\.venv\Scripts\python.exe" -m hermes_cli.main @args
} elseif (Test-Path "$ScriptDir\venv\Scripts\python.exe") {
    & "$ScriptDir\venv\Scripts\python.exe" -m hermes_cli.main @args
} else {
    python "$ScriptDir\hermes" @args
}
