param(
    [switch]$Force
)
$ErrorActionPreference = "Stop"
$folders = @(
    (Join-Path $env:APPDATA "Rahmi Apps\LocalVoice"),
    (Join-Path $env:LOCALAPPDATA "Rahmi Apps\LocalVoice"),
    (Join-Path $env:APPDATA "LocalVoice"),
    (Join-Path $env:LOCALAPPDATA "LocalVoice")
) | Select-Object -Unique

if (-not $Force) {
    Write-Host "WARNUNG: Dies löscht Einstellungen, Verlauf, Wörterbuch, Profile, Modelle, Audio und Cache von LocalVoice." -ForegroundColor Yellow
    $answer = Read-Host "Zum vollständigen Zurücksetzen RESET eingeben"
    if ($answer -cne "RESET") {
        Write-Host "Abgebrochen."
        exit 0
    }
}

Get-Process LocalVoice -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 700
foreach ($folder in $folders) {
    if (Test-Path -LiteralPath $folder) {
        Remove-Item -LiteralPath $folder -Recurse -Force
        Write-Host "Gelöscht: $folder"
    }
}
Write-Host "LocalVoice-Benutzerdaten wurden vollständig zurückgesetzt." -ForegroundColor Green
