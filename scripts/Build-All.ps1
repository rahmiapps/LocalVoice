$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location (Split-Path $PSScriptRoot -Parent)
& "$PSScriptRoot\Build-Windows.ps1"
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw "WSL is not installed. Install WSL/Ubuntu or run scripts/Build-Linux.sh on a Linux computer."
}
$LinuxPath = (& wsl.exe wslpath -a -- (Get-Location).Path).Trim()
if (-not $LinuxPath) { throw "The project path could not be converted for WSL." }
& wsl.exe --cd $LinuxPath bash -lc "chmod +x scripts/*.sh installer/linux/*.sh installer/linux/AppRun && ./scripts/Build-Linux.sh"
if ($LASTEXITCODE -ne 0) { throw "The Linux build failed." }
