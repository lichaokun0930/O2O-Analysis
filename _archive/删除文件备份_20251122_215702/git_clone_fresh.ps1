# GitHub Fresh Clone Script - Clone repository to new location
# Author: Auto-generated
# Usage: .\git_clone_fresh.ps1

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GitHub Fresh Clone Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get repository URL
Write-Host "[Step 1] Getting repository URL..." -ForegroundColor Yellow

if (Test-Path ".git") {
    $repoUrl = git remote get-url origin
    Write-Host "  Repository: $repoUrl" -ForegroundColor Cyan
} else {
    Write-Host "  ERROR: Not in a git repository!" -ForegroundColor Red
    $repoUrl = Read-Host "  Please enter repository URL"
}
Write-Host ""

# Ask for clone location
Write-Host "[Step 2] Choose clone location..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$defaultPath = "D:\Python\订单数据看板\O2O-Analysis_clone_$timestamp"
$clonePath = Read-Host "  Enter path (press Enter for: $defaultPath)"

if ([string]::IsNullOrWhiteSpace($clonePath)) {
    $clonePath = $defaultPath
}

Write-Host "  Clone to: $clonePath" -ForegroundColor Cyan
Write-Host ""

# Check if path exists
if (Test-Path $clonePath) {
    Write-Host "  WARNING: Path already exists!" -ForegroundColor Yellow
    $response = Read-Host "  Delete and recreate? (y/n)"
    if ($response -eq 'y') {
        Remove-Item -Path $clonePath -Recurse -Force
        Write-Host "  Old directory removed" -ForegroundColor Green
    } else {
        Write-Host "  Aborted" -ForegroundColor Red
        exit 1
    }
}
Write-Host ""

# Clone repository
Write-Host "[Step 3] Cloning repository..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Cyan
Write-Host ""

git clone $repoUrl $clonePath

$cloneStatus = $LASTEXITCODE
if ($cloneStatus -eq 0) {
    Write-Host ""
    Write-Host "  OK: Clone completed successfully!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  ERROR: Clone failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Show clone info
Write-Host "[Step 4] Clone information:" -ForegroundColor Yellow
Set-Location $clonePath
Write-Host "  Location: $clonePath" -ForegroundColor Cyan
Write-Host "  Branch: $(git branch --show-current)" -ForegroundColor Cyan
Write-Host "  Latest commit:" -ForegroundColor Cyan
git log --oneline -1
Write-Host ""

# Offer to create virtual environment
Write-Host "[Step 5] Setup Python environment?" -ForegroundColor Yellow
$setupEnv = Read-Host "  Create virtual environment and install dependencies? (y/n)"

if ($setupEnv -eq 'y') {
    Write-Host ""
    Write-Host "  Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
    
    Write-Host "  Installing dependencies..." -ForegroundColor Cyan
    & .\.venv\Scripts\pip.exe install --upgrade pip --quiet
    & .\.venv\Scripts\pip.exe install -r requirements.txt --quiet
    
    Write-Host "  OK: Environment setup completed" -ForegroundColor Green
    Write-Host ""
    Write-Host "  To activate: .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Clone completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Green
Write-Host "  1. cd `"$clonePath`"" -ForegroundColor Cyan
Write-Host "  2. .\.venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "  3. Install PostgreSQL and Redis" -ForegroundColor Cyan
Write-Host "  4. Configure .env file" -ForegroundColor Cyan
Write-Host "  5. Run: python database\migrate.py" -ForegroundColor Cyan
Write-Host "  6. Start: .\start_dashboard.ps1" -ForegroundColor Cyan
Write-Host ""
