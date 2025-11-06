# ==========================================
# Intelligent Store Dashboard Startup Script
# ==========================================

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "   Smart Store Dashboard - Startup" -ForegroundColor Yellow
Write-Host "================================================`n" -ForegroundColor Cyan

# 1. Check and stop existing Python processes
Write-Host "[1/3] Checking port 8050..." -ForegroundColor Green
$existingProcess = Get-NetTCPConnection -LocalPort 8050 -ErrorAction SilentlyContinue
if ($existingProcess) {
    Write-Host "      Port 8050 is occupied, stopping old process..." -ForegroundColor Yellow
    Stop-Process -Name python -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "      Old process stopped" -ForegroundColor Green
}

# 2. Configure Python environment (disable output buffering)
Write-Host "`n[2/3] Configuring Python environment..." -ForegroundColor Green
$env:PYTHONUNBUFFERED = "1"
$env:PYTHONIOENCODING = "utf-8"
Write-Host "      PYTHONUNBUFFERED = 1" -ForegroundColor Gray
Write-Host "      PYTHONIOENCODING = utf-8" -ForegroundColor Gray

# 2.5. Verify Python and file existence
Write-Host "`n[2.5/3] Verifying environment..." -ForegroundColor Green
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if ($pythonPath) {
    Write-Host "      Python found: $pythonPath" -ForegroundColor Gray
} else {
    Write-Host "      ERROR: Python not found in PATH!" -ForegroundColor Red
    exit 1
}

# Use current directory directly, avoid encoding issues
$currentDir = Get-Location
$scriptName = [System.Text.Encoding]::UTF8.GetString([System.Text.Encoding]::Default.GetBytes("智能门店看板_Dash版.py"))
$scriptPath = Join-Path $currentDir $scriptName

if (Test-Path "智能门店看板_Dash版.py") {
    Write-Host "      Script found in current directory" -ForegroundColor Gray
    $scriptPath = "智能门店看板_Dash版.py"
} else {
    Write-Host "      ERROR: Script not found in current directory" -ForegroundColor Red
    exit 1
}

# 3. Start Dash application
Write-Host "`n[3/3] Starting dashboard application..." -ForegroundColor Green
Write-Host "      Full logging enabled" -ForegroundColor Cyan
Write-Host "      Access URL: http://localhost:8050" -ForegroundColor Cyan
Write-Host "      Press Ctrl+C to stop`n" -ForegroundColor Yellow
Write-Host "================================================`n" -ForegroundColor Cyan

# Run Python application (use full path to avoid issues)
try {
    & python $scriptPath
}
catch {
    Write-Host "`nApplication startup failed: $_" -ForegroundColor Red
    Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nDashboard stopped" -ForegroundColor Green
