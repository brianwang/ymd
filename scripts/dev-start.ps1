param(
  [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"

function Get-FreePort {
  $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
  $listener.Start()
  $port = ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
  $listener.Stop()
  return $port
}

function Require-Command {
  param([string]$Name)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Missing required command: $Name"
  }
}

Require-Command "pwsh"
Require-Command "python"
Require-Command "npm"
Require-Command "node"

$root = Split-Path -Parent $PSScriptRoot
$apiPort = Get-FreePort
$adminPort = Get-FreePort
$h5Port = Get-FreePort

$apiBase = "http://localhost:$apiPort/api/v1"
Write-Host "Starting dev stack..."
Write-Host "API base: $apiBase"

$ymdAppEnvLocal = Join-Path $root "ymd-app\.env.local"
Set-Content -Path $ymdAppEnvLocal -Value "VITE_API_BASE_URL=$apiBase" -Encoding UTF8 -NoNewline

try {
  python -c "import uvicorn" | Out-Null
} catch {
  throw "Backend dependency missing: uvicorn. Install ymd-server requirements first."
}

$apiCmd = @"
$env:PYTHONDONTWRITEBYTECODE='1';
$env:PYTHONUNBUFFERED='1';
Set-Location '$root\ymd-server';
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $apiPort 2>&1
"@

$apiJob = Start-Job -Name "ymd-api" -ScriptBlock {
  param($cmd)
  pwsh -NoProfile -Command $cmd
} -ArgumentList $apiCmd

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$healthUrl = "http://localhost:$apiPort/"
while ((Get-Date) -lt $deadline) {
  try {
    Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 2 | Out-Null
    break
  } catch {
    Start-Sleep -Milliseconds 400
  }
}

try {
  Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 2 | Out-Null
} catch {
  $state = (Get-Job -Id $apiJob.Id -ErrorAction SilentlyContinue)?.State
  Write-Host ""
  Write-Host "Backend job state: $state"
  try {
    $tail = Receive-Job -Id $apiJob.Id -Keep -ErrorAction SilentlyContinue | Select-Object -Last 40
    if ($tail) {
      Write-Host "Backend job output (tail):"
      $tail | ForEach-Object { Write-Host $_ }
    }
  } catch {
  }
  Write-Host "Warning: Backend healthcheck did not pass within $TimeoutSeconds seconds: $healthUrl"
}

$adminCmd = @"
$env:VITE_API_BASE_URL='$apiBase';
Set-Location '$root\ymd-admin';
npm run dev -- --port $adminPort --strictPort 2>&1
"@

$adminJob = Start-Job -Name "ymd-admin" -ScriptBlock {
  param($cmd)
  pwsh -NoProfile -Command $cmd
} -ArgumentList $adminCmd

$h5Cmd = @"
$env:VITE_API_BASE_URL='$apiBase';
Set-Location '$root\ymd-app';
npm run dev:h5 -- --port $h5Port --strictPort 2>&1
"@

$h5Job = Start-Job -Name "ymd-h5" -ScriptBlock {
  param($cmd)
  pwsh -NoProfile -Command $cmd
} -ArgumentList $h5Cmd

Write-Host ""
Write-Host "API:    $apiBase (health: $healthUrl)"
Write-Host "Admin:  http://localhost:$adminPort/"
Write-Host "H5:     http://localhost:$h5Port/"
Write-Host ""
Write-Host "Jobs:   api=$($apiJob.Id) admin=$($adminJob.Id) h5=$($h5Job.Id)"
Write-Host "Logs:   Receive-Job -Id <id> -Keep"
Write-Host "Stop:   Stop-Job -Id <id>; Remove-Job -Id <id>"

try {
  Write-Host ""
  Write-Host "Running... Press Ctrl+C to stop."
  while ($true) {
    Start-Sleep -Seconds 2
  }
} finally {
  Get-Job | Stop-Job -ErrorAction SilentlyContinue
  Get-Job | Remove-Job -Force -ErrorAction SilentlyContinue
}
