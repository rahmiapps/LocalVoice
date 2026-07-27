$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path ".venv-windows\Scripts\pythonw.exe")) { & "$PSScriptRoot\Setup-Windows.ps1" }
Start-Process -FilePath ".\.venv-windows\Scripts\pythonw.exe" -ArgumentList "run_localvoice.py" -WorkingDirectory (Get-Location)
