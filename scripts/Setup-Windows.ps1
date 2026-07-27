$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Get-LocalVoicePython {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($Version in @("3.12", "3.11")) {
            & py "-$Version" -c "import sys; assert sys.version_info[:2] == tuple(map(int, '$Version'.split('.')))" 2>$null
            if ($LASTEXITCODE -eq 0) { return @("py", "-$Version") }
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python -c "import sys; raise SystemExit(0 if sys.version_info[:2] in [(3,11),(3,12)] else 1)"
        if ($LASTEXITCODE -eq 0) { return @("python") }
    }
    throw "LocalVoice requires Python 3.11 or 3.12. Install one of these versions from python.org and enable 'Add Python to PATH'."
}

$PythonCommand = Get-LocalVoicePython
if (-not (Test-Path ".venv-windows\Scripts\python.exe")) {
    Remove-Item -Recurse -Force ".venv-windows" -ErrorAction SilentlyContinue
    if ($PythonCommand.Count -eq 2) {
        & $PythonCommand[0] $PythonCommand[1] -m venv .venv-windows
    } else {
        & $PythonCommand[0] -m venv .venv-windows
    }
}
& .\.venv-windows\Scripts\python.exe -m pip install --upgrade pip wheel setuptools
& .\.venv-windows\Scripts\python.exe -m pip install -r requirements.txt
Write-Host "LocalVoice is ready. Start it with scripts\Start-Windows.ps1" -ForegroundColor Green
