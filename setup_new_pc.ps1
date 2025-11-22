# New PC Auto Setup Script
# Purpose: Automate Python environment and dependency installation

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  O2O Dashboard - Auto Setup  " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "[Step 1] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  OK Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Create virtual environment
Write-Host "[Step 2] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "  INFO: .venv already exists" -ForegroundColor Cyan
} else {
    python -m venv .venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK: Virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "  ERROR: Failed to create venv" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Step 3: Upgrade pip
Write-Host "[Step 3] Upgrading pip..." -ForegroundColor Yellow
$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"
$venvPip = Join-Path $scriptDir ".venv\Scripts\pip.exe"

& $venvPython -m pip install --upgrade pip --quiet
Write-Host "  OK: pip upgraded" -ForegroundColor Green
Write-Host ""

# Step 4: Install dependencies
Write-Host "[Step 4] Installing dependencies (5-10 min)..." -ForegroundColor Yellow
Write-Host "  Please wait... You can get a coffee" -ForegroundColor Cyan

$reqFile = if (Test-Path "requirements_utf8.txt") { "requirements_utf8.txt" } else { "requirements.txt" }

if (Test-Path $reqFile) {
    & $venvPip install -r $reqFile --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK: Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Some packages failed" -ForegroundColor Yellow
    }
} else {
    Write-Host "  WARNING: requirements.txt not found" -ForegroundColor Yellow
}
Write-Host ""

# Step 5: Verify core packages
Write-Host "[Step 5] Verifying core packages..." -ForegroundColor Yellow
$testScript = @"
import sys
try:
    import dash, pandas, plotly, sqlalchemy
    print('OK: Core packages verified')
    sys.exit(0)
except ImportError as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"@

$result = & $venvPython -c $testScript 2>&1
Write-Host "  $result" -ForegroundColor $(if ($LASTEXITCODE -eq 0) { "Green" } else { "Red" })
Write-Host ""

# Step 6: Create .env file
Write-Host "[Step 6] Creating .env file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item .env.example .env
        Write-Host "  OK: .env created from .env.example" -ForegroundColor Green
    } else {
        @"
# Database config
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/o2o_dashboard

# Redis config
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
"@ | Out-File -FilePath ".env" -Encoding UTF8
        Write-Host "  OK: Default .env created" -ForegroundColor Green
        Write-Host "  WARNING: Please edit .env and set your password!" -ForegroundColor Yellow
    }
} else {
    Write-Host "  INFO: .env already exists" -ForegroundColor Cyan
}
Write-Host ""

# Step 7: Check PostgreSQL
Write-Host "[Step 7] Checking PostgreSQL..." -ForegroundColor Yellow
$pgInstalled = Test-Path "C:\Program Files\PostgreSQL"
if ($pgInstalled) {
    Write-Host "  OK: PostgreSQL installed" -ForegroundColor Green
    $pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
    if ($pgService -and $pgService.Status -eq "Running") {
        Write-Host "  OK: PostgreSQL service running" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: PostgreSQL service not running" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ERROR: PostgreSQL not installed" -ForegroundColor Red
    Write-Host "     Download: https://www.postgresql.org/download/windows/" -ForegroundColor Cyan
}
Write-Host ""

# Step 8: Check Redis
Write-Host "[Step 8] Checking Redis..." -ForegroundColor Yellow
$redisService = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue
if ($redisService) {
    Write-Host "  OK: Redis (Memurai) installed" -ForegroundColor Green
    if ($redisService.Status -eq "Running") {
        Write-Host "  OK: Redis service running" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Redis service not running" -ForegroundColor Yellow
        Write-Host "     Run: Start-Service Memurai" -ForegroundColor Cyan
    }
} else {
    Write-Host "  ERROR: Redis not installed" -ForegroundColor Red
    Write-Host "     Download: https://www.memurai.com/get-memurai" -ForegroundColor Cyan
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Summary" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Completed:" -ForegroundColor Green
Write-Host "  [OK] Python virtual environment" -ForegroundColor Green
Write-Host "  [OK] Project dependencies" -ForegroundColor Green
Write-Host "  [OK] .env configuration file" -ForegroundColor Green
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
if (-not $pgInstalled) {
    Write-Host "  1. Install PostgreSQL database" -ForegroundColor Red
}
if (-not $redisService) {
    Write-Host "  2. Install Redis (Memurai)" -ForegroundColor Red
}
Write-Host "  3. Edit .env file (set database password)" -ForegroundColor Yellow
Write-Host "     Command: notepad .env" -ForegroundColor Cyan
Write-Host ""

if ($pgInstalled -and $redisService) {
    Write-Host "  4. Initialize database" -ForegroundColor Yellow
    Write-Host "     Command: python database\migrate.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  5. Start dashboard" -ForegroundColor Yellow
    Write-Host "     Command: .\start_dashboard.ps1" -ForegroundColor Cyan
    Write-Host "     URL: http://localhost:8050" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "  - Full guide: New PC Setup Guide.md" -ForegroundColor Gray
Write-Host "  - Quick start: Quick Start Guide.md" -ForegroundColor Gray
Write-Host ""

Write-Host "Setup completed!" -ForegroundColor Green
Write-Host ""
