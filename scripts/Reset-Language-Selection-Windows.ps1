$ErrorActionPreference = 'Stop'
Get-Process LocalVoice -ErrorAction SilentlyContinue | Stop-Process -Force
$configDir = Join-Path $env:APPDATA 'Rahmi Apps\LocalVoice'
$localePath = Join-Path $configDir 'ui-locale.json'
if (Test-Path $localePath) { Remove-Item $localePath -Force }
Write-Host 'Die bestätigte Sprache wurde zurückgesetzt. Beim nächsten Start erscheint die Sprachauswahl.' -ForegroundColor Green
