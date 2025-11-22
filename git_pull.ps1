# GitHub Pull Script - Daily Code Pull
# Author: Auto-generated
# Usage: .\git_pull.ps1

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  GitHub Pull Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "ERROR: Not a git repository!" -ForegroundColor Red
    Write-Host "Please run this script from the repository root." -ForegroundColor Yellow
    exit 1
}

# Show current branch
Write-Host "[Step 1] Current repository info:" -ForegroundColor Yellow
$branch = git branch --show-current
Write-Host "  Branch: $branch" -ForegroundColor Cyan
Write-Host "  Remote: $(git remote get-url origin)" -ForegroundColor Cyan
Write-Host ""

# Check for local changes
Write-Host "[Step 2] Checking for local changes..." -ForegroundColor Yellow
$hasChanges = git status --porcelain

if ($hasChanges) {
    Write-Host "  WARNING: You have uncommitted changes!" -ForegroundColor Yellow
    Write-Host ""
    git status --short
    Write-Host ""
    
    $response = Read-Host "  Do you want to stash these changes? (y/n)"
    if ($response -eq 'y') {
        Write-Host "  Stashing local changes..." -ForegroundColor Cyan
        git stash push -m "Auto-stash before pull $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        Write-Host "  OK: Changes stashed" -ForegroundColor Green
        Write-Host "  Use 'git stash pop' to restore them later" -ForegroundColor Yellow
    } else {
        Write-Host "  WARNING: Proceeding without stashing" -ForegroundColor Yellow
        Write-Host "  This may cause merge conflicts" -ForegroundColor Red
    }
} else {
    Write-Host "  OK: No local changes" -ForegroundColor Green
}
Write-Host ""

# Fetch latest changes
Write-Host "[Step 3] Fetching latest changes from GitHub..." -ForegroundColor Yellow
git fetch origin

$fetchStatus = $LASTEXITCODE
if ($fetchStatus -eq 0) {
    Write-Host "  OK: Fetch completed" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Fetch failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check for updates
Write-Host "[Step 4] Checking for updates..." -ForegroundColor Yellow
$localCommit = git rev-parse HEAD
$remoteCommit = git rev-parse origin/$branch

if ($localCommit -eq $remoteCommit) {
    Write-Host "  INFO: Already up to date" -ForegroundColor Cyan
    Write-Host "  No new changes to pull" -ForegroundColor Gray
} else {
    Write-Host "  New changes available:" -ForegroundColor Green
    git log HEAD..origin/$branch --oneline
    Write-Host ""
    
    # Pull changes
    Write-Host "[Step 5] Pulling changes..." -ForegroundColor Yellow
    git pull origin $branch
    
    $pullStatus = $LASTEXITCODE
    if ($pullStatus -eq 0) {
        Write-Host "  OK: Pull completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "  ERROR: Pull failed!" -ForegroundColor Red
        Write-Host "  You may have merge conflicts" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host ""

# Show latest commits
Write-Host "[Step 6] Latest commits:" -ForegroundColor Yellow
git log --oneline -5
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Pull completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Show summary
Write-Host "Summary:" -ForegroundColor Green
Write-Host "  Repository: $(git remote get-url origin)" -ForegroundColor Gray
Write-Host "  Branch: $branch" -ForegroundColor Gray
Write-Host "  Updated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""
