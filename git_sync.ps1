# GitHub Sync Script - Pull then Push
# Author: Auto-generated
# Usage: .\git_sync.ps1 "commit message"

param(
    [string]$message = "Daily sync $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GitHub Sync Script (Pull + Push)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Pull latest changes
Write-Host "===== STEP 1: Pull Latest Changes =====" -ForegroundColor Magenta
Write-Host ""

.\git_pull.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Pull failed! Please resolve issues before pushing." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "===== STEP 2: Push Local Changes =====" -ForegroundColor Magenta
Write-Host ""

# Wait a moment
Start-Sleep -Seconds 1

# Step 2: Push changes
.\git_push.ps1 "$message"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Push failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sync completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
