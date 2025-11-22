# GitHub Push Script - Daily Code Push
# Author: Auto-generated
# Usage: .\git_push.ps1 "commit message"

param(
    [string]$message = "Daily update $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GitHub Push Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "ERROR: Not a git repository!" -ForegroundColor Red
    Write-Host "Please run this script from the repository root." -ForegroundColor Yellow
    exit 1
}

# Show current status
Write-Host "[Step 1] Checking repository status..." -ForegroundColor Yellow
git status --short
Write-Host ""

# Add all changes
Write-Host "[Step 2] Adding changes..." -ForegroundColor Yellow
git add .

$addStatus = $LASTEXITCODE
if ($addStatus -eq 0) {
    Write-Host "  OK: Changes added" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Some files may not be added" -ForegroundColor Yellow
}
Write-Host ""

# Show what will be committed
Write-Host "[Step 3] Files to be committed:" -ForegroundColor Yellow
git status --short
Write-Host ""

# Commit changes
Write-Host "[Step 4] Committing changes..." -ForegroundColor Yellow
Write-Host "  Message: $message" -ForegroundColor Cyan

git commit -m "$message"

$commitStatus = $LASTEXITCODE
if ($commitStatus -eq 0) {
    Write-Host "  OK: Changes committed" -ForegroundColor Green
} else {
    Write-Host "  INFO: No changes to commit or commit failed" -ForegroundColor Cyan
}
Write-Host ""

# Push to remote
Write-Host "[Step 5] Pushing to GitHub..." -ForegroundColor Yellow

$branch = git branch --show-current
Write-Host "  Branch: $branch" -ForegroundColor Cyan

git push origin $branch

$pushStatus = $LASTEXITCODE
if ($pushStatus -eq 0) {
    Write-Host "  OK: Successfully pushed to GitHub!" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Push failed!" -ForegroundColor Red
    Write-Host "  Please check your network connection and authentication." -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Show remote status
Write-Host "[Step 6] Remote repository status:" -ForegroundColor Yellow
git log --oneline -5
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Push completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Show summary
Write-Host "Summary:" -ForegroundColor Green
Write-Host "  Repository: $(git remote get-url origin)" -ForegroundColor Gray
Write-Host "  Branch: $branch" -ForegroundColor Gray
Write-Host "  Commit: $message" -ForegroundColor Gray
Write-Host "  Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""
