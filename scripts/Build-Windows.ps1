param(
    [switch]$SkipDependencyAudit
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".venv-windows\Scripts\python.exe")) { & "$PSScriptRoot\Setup-Windows.ps1" }
$Python = Resolve-Path ".venv-windows\Scripts\python.exe"
& $Python -m pip install -r requirements-build.txt
& $Python -m pip check
& $Python scripts\Run-Checks.py
if (-not $SkipDependencyAudit) {
    & $Python -m pip_audit -r requirements.txt --progress-spinner off
}

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
& $Python -m PyInstaller --clean --noconfirm LocalVoice.spec
if (-not (Test-Path "dist\LocalVoice\LocalVoice.exe")) {
    throw "PyInstaller did not create dist\LocalVoice\LocalVoice.exe"
}
$OldQtPlatform = $env:QT_QPA_PLATFORM
$OldPynputBackend = $env:PYNPUT_BACKEND
try {
    $env:QT_QPA_PLATFORM = "offscreen"
    $env:PYNPUT_BACKEND = "dummy"
    & "dist\LocalVoice\LocalVoice.exe" --package-smoke-test
    if ($LASTEXITCODE -ne 0) { throw "The frozen Windows application failed its package smoke test." }
} finally {
    $env:QT_QPA_PLATFORM = $OldQtPlatform
    $env:PYNPUT_BACKEND = $OldPynputBackend
}

$Release = Join-Path (Get-Location) "release\windows"
Remove-Item -Recurse -Force $Release -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $Release -Force | Out-Null
Copy-Item -Recurse "dist\LocalVoice" "$Release\LocalVoice"
Compress-Archive -Path "$Release\LocalVoice\*" -DestinationPath "$Release\LocalVoice-Windows-x64-Portable.zip" -Force
Remove-Item -Recurse -Force "$Release\LocalVoice"

$InnoCandidates = @(
  "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
  "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
  "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)
$Inno = $InnoCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $Inno) {
    $Inno = Get-ChildItem "$env:LOCALAPPDATA\Programs", "${env:ProgramFiles(x86)}", "$env:ProgramFiles" `
      -Filter ISCC.exe -Recurse -ErrorAction SilentlyContinue |
      Select-Object -First 1 -ExpandProperty FullName
}
if (-not $Inno) {
    throw "Inno Setup 6 was not found. Install it, then run Build-Windows.ps1 again."
}
Write-Host "Using Inno Setup: $Inno" -ForegroundColor Cyan
& $Inno "installer\windows\LocalVoice.iss"
$Installer = "installer\windows\Output\LocalVoice-Setup-Windows-x64.exe"
if (-not (Test-Path $Installer)) { throw "The Windows installer was not created." }
Copy-Item $Installer $Release -Force

$SignTool = $env:SIGNTOOL_PATH
$Thumbprint = $env:WINDOWS_CERT_THUMBPRINT
if ($SignTool -and $Thumbprint) {
    & $SignTool sign /sha1 $Thumbprint /fd SHA256 /tr https://timestamp.digicert.com /td SHA256 (Join-Path $Release "LocalVoice-Setup-Windows-x64.exe")
} else {
    "UNSIGNED BUILD - configure SIGNTOOL_PATH and WINDOWS_CERT_THUMBPRINT for public distribution." | Set-Content (Join-Path $Release "SIGNING_STATUS.txt") -Encoding UTF8
}

& $Python -m pip freeze | Set-Content (Join-Path $Release "PYTHON-DEPENDENCIES.txt") -Encoding UTF8
Get-ChildItem $Release -File | Where-Object { $_.Name -ne "SHA256SUMS.txt" } | Sort-Object Name | ForEach-Object {
  $Hash = Get-FileHash $_.FullName -Algorithm SHA256
  "$($Hash.Hash.ToLower())  $($_.Name)"
} | Set-Content (Join-Path $Release "SHA256SUMS.txt") -Encoding ASCII
Write-Host "Windows release created in $Release" -ForegroundColor Green
