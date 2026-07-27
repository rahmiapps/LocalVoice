param(
    [ValidateSet('de','en','fr','it','es','zh')]
    [string]$Language = 'de'
)

$ErrorActionPreference = 'Stop'

Get-Process LocalVoice -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

$configDir = Join-Path $env:APPDATA 'Rahmi Apps\LocalVoice'
$settingsPath = Join-Path $configDir 'settings.json'
$localePath = Join-Path $configDir 'ui-locale.json'
New-Item -ItemType Directory -Path $configDir -Force | Out-Null

if (Test-Path $settingsPath) {
    try {
        $settings = Get-Content $settingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        $backup = "$settingsPath.broken-$(Get-Date -Format yyyyMMddHHmmss)"
        Move-Item $settingsPath $backup -Force
        $settings = [pscustomobject]@{}
    }
} else {
    $settings = [pscustomobject]@{}
}

function Set-JsonProperty {
    param([object]$Object, [string]$Name, [object]$Value)
    if ($null -eq $Object.PSObject.Properties[$Name]) {
        $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value
    } else {
        $Object.$Name = $Value
    }
}

Set-JsonProperty $settings 'settings_schema_version' 9
Set-JsonProperty $settings 'ui_language' $Language
Set-JsonProperty $settings 'ui_language_confirmed' $true

if ($null -eq $settings.PSObject.Properties['first_run_complete']) {
    Set-JsonProperty $settings 'first_run_complete' $false
}

$preferred = @()
if ($null -ne $settings.PSObject.Properties['preferred_languages'] -and $settings.preferred_languages) {
    $preferred = @($settings.preferred_languages | ForEach-Object { [string]$_ })
}
$preferred = @($Language) + @($preferred | Where-Object { $_ -ne $Language })
Set-JsonProperty $settings 'preferred_languages' @($preferred | Select-Object -Unique | Select-Object -First 12)

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$settingsJson = $settings | ConvertTo-Json -Depth 50
$settingsTmp = "$settingsPath.tmp"
[System.IO.File]::WriteAllText($settingsTmp, $settingsJson, $utf8NoBom)
Move-Item $settingsTmp $settingsPath -Force

$locale = [ordered]@{
    schema_version = 3
    confirmation_generation = 3
    confirmation_source = 'explicit-user-choice'
    ui_language = $Language
    confirmed = $true
}
$localeJson = $locale | ConvertTo-Json -Depth 10
$localeTmp = "$localePath.tmp"
[System.IO.File]::WriteAllText($localeTmp, $localeJson, $utf8NoBom)
Move-Item $localeTmp $localePath -Force

Write-Host "LocalVoice-Sprache wurde dauerhaft auf '$Language' gesetzt." -ForegroundColor Green
Write-Host "Einstellungen: $settingsPath"
Write-Host "Sprachbestätigung: $localePath"
