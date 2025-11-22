# Daily Workflow Script - Start your day or end your day
# Author: Auto-generated
# Usage: .\daily_workflow.ps1 [start|end]

param(
    [string]$action = "start"
)

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Daily Workflow - $(if($action -eq 'start'){'Start Day'}else{'End Day'})" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($action -eq "start") {
    # ============================================================
    # START DAY WORKFLOW
    # ============================================================
    
    Write-Host "===== Morning Routine =====" -ForegroundColor Magenta
    Write-Host ""
    
    # Step 1: Pull latest code
    Write-Host "[1/5] Pulling latest code from GitHub..." -ForegroundColor Yellow
    .\git_pull.ps1
    Write-Host ""
    
    # Step 2: Check dependencies
    Write-Host "[2/5] Checking Python dependencies..." -ForegroundColor Yellow
    if (Test-Path ".venv\Scripts\python.exe") {
        & .\.venv\Scripts\python.exe -c "import dash, pandas, sqlalchemy; print('  OK: Core packages available')"
    } else {
        Write-Host "  WARNING: Virtual environment not found" -ForegroundColor Yellow
        Write-Host "  Run: .\setup_new_pc.ps1" -ForegroundColor Cyan
    }
    Write-Host ""
    
    # Step 3: Start services
    Write-Host "[3/5] Starting backend services..." -ForegroundColor Yellow
    
    # Check PostgreSQL
    $pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
    if ($pgService) {
        if ($pgService.Status -ne "Running") {
            Start-Service $pgService.Name -ErrorAction SilentlyContinue
            Write-Host "  OK: PostgreSQL started" -ForegroundColor Green
        } else {
            Write-Host "  OK: PostgreSQL already running" -ForegroundColor Green
        }
    } else {
        Write-Host "  WARNING: PostgreSQL not found" -ForegroundColor Yellow
    }
    
    # Check Redis
    $redisService = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue
    if ($redisService) {
        if ($redisService.Status -ne "Running") {
            Start-Service Memurai -ErrorAction SilentlyContinue
            Write-Host "  OK: Redis started" -ForegroundColor Green
        } else {
            Write-Host "  OK: Redis already running" -ForegroundColor Green
        }
    } else {
        Write-Host "  WARNING: Redis not found" -ForegroundColor Yellow
    }
    Write-Host ""
    
    # Step 4: Check database
    Write-Host "[4/5] Checking database status..." -ForegroundColor Yellow
    if (Test-Path "查看数据库状态.py") {
        & .\.venv\Scripts\python.exe 查看数据库状态.py 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK: Database accessible" -ForegroundColor Green
        } else {
            Write-Host "  WARNING: Database check failed" -ForegroundColor Yellow
        }
    }
    Write-Host ""
    
    # Step 5: Ready to work
    Write-Host "[5/5] Environment ready!" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Good morning! Ready to work!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Quick commands:" -ForegroundColor Green
    Write-Host "  Start dashboard: .\启动看板.ps1" -ForegroundColor Cyan
    Write-Host "  View logs: Get-Content logs\*.log -Tail 20" -ForegroundColor Cyan
    Write-Host "  Test connection: python 测试Redis连接.py" -ForegroundColor Cyan
    Write-Host ""
    
} else {
    # ============================================================
    # END DAY WORKFLOW
    # ============================================================
    
    Write-Host "===== Evening Routine =====" -ForegroundColor Magenta
    Write-Host ""
    
    # Step 1: Stop dashboard
    Write-Host "[1/4] Stopping dashboard..." -ForegroundColor Yellow
    $dashProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -match "看板"}
    if ($dashProcess) {
        Stop-Process -Id $dashProcess.Id -Force
        Write-Host "  OK: Dashboard stopped" -ForegroundColor Green
    } else {
        Write-Host "  INFO: Dashboard not running" -ForegroundColor Cyan
    }
    Write-Host ""
    
    # Step 2: Backup database
    Write-Host "[2/4] Backup database?" -ForegroundColor Yellow
    $backup = Read-Host "  Create database backup? (y/n)"
    if ($backup -eq 'y') {
        if (Test-Path "一键导出数据库.bat") {
            Write-Host "  Creating backup..." -ForegroundColor Cyan
            & .\一键导出数据库.bat
            Write-Host "  OK: Backup completed" -ForegroundColor Green
        }
    } else {
        Write-Host "  Skipped" -ForegroundColor Gray
    }
    Write-Host ""
    
    # Step 3: Commit and push changes
    Write-Host "[3/4] Committing today's work..." -ForegroundColor Yellow
    
    # Check for changes
    $hasChanges = git status --porcelain
    if ($hasChanges) {
        Write-Host "  You have uncommitted changes:" -ForegroundColor Yellow
        git status --short
        Write-Host ""
        
        $commitMsg = Read-Host "  Enter commit message (or press Enter for default)"
        if ([string]::IsNullOrWhiteSpace($commitMsg)) {
            $commitMsg = "End of day commit - $(Get-Date -Format 'yyyy-MM-dd')"
        }
        
        Write-Host "  Pushing to GitHub..." -ForegroundColor Cyan
        .\git_push.ps1 "$commitMsg"
        Write-Host "  OK: Changes pushed" -ForegroundColor Green
    } else {
        Write-Host "  INFO: No changes to commit" -ForegroundColor Cyan
    }
    Write-Host ""
    
    # Step 4: Stop services (optional)
    Write-Host "[4/4] Stop backend services?" -ForegroundColor Yellow
    $stopServices = Read-Host "  Stop PostgreSQL and Redis? (y/n)"
    if ($stopServices -eq 'y') {
        Stop-Service postgresql* -ErrorAction SilentlyContinue
        Stop-Service Memurai -ErrorAction SilentlyContinue
        Write-Host "  OK: Services stopped" -ForegroundColor Green
    } else {
        Write-Host "  Services will keep running" -ForegroundColor Cyan
    }
    Write-Host ""
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Good evening! See you tomorrow!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Summary:" -ForegroundColor Green
    Write-Host "  Code: Pushed to GitHub" -ForegroundColor Gray
    Write-Host "  Database: $(if($backup -eq 'y'){'Backed up'}else{'Not backed up'})" -ForegroundColor Gray
    Write-Host "  Services: $(if($stopServices -eq 'y'){'Stopped'}else{'Running'})" -ForegroundColor Gray
    Write-Host "  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host ""
}
