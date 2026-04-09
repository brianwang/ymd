param()

$scriptPath = Join-Path $PSScriptRoot "scripts\dev-start.ps1"
& pwsh -NoProfile -ExecutionPolicy Bypass -File $scriptPath

