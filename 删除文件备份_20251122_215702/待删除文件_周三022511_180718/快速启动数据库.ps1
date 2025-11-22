# Quick Start PostgreSQL on Port 8000
# Run as Administrator

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$pgCtl = "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe"
$dataDir = "D:\postgresql"

Write-Host ""
Write-Host "Starting PostgreSQL on port 5432..." -ForegroundColor Cyan

# Check if already running
$running = & $pgCtl status -D $dataDir 2>&1
if ($running -match "server is running") {
    Write-Host "PostgreSQL is already running!" -ForegroundColor Green
    & $pgCtl status -D $dataDir
} else {
    # Start server
    & $pgCtl start -D $dataDir -w -t 30
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "SUCCESS - PostgreSQL started!" -ForegroundColor Green
        Write-Host "Port: 5432" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "Failed to start. Check logs:" -ForegroundColor Red
        Write-Host "  $dataDir\log\" -ForegroundColor Yellow
    }
}

Write-Host ""
Read-Host "Press Enter to exit"
