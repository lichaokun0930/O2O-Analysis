# PostgreSQL Complete Fix and Start Script
# Must run as Administrator

param([switch]$Force)

# Self-elevate to Administrator
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Yellow
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    if ($Force) { $arguments += " -Force" }
    Start-Process powershell.exe -ArgumentList $arguments -Verb RunAs
    exit
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  PostgreSQL Complete Repair & Start" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$dataPath = "D:\postgresql"
$lockFile = "$dataPath\postmaster.pid"
$serviceName = "postgresql-x64-18"

# Step 1: Stop any running PostgreSQL processes
Write-Host "[1/5] Checking for running PostgreSQL processes..." -ForegroundColor Yellow
$pgProcesses = Get-Process -Name postgres,pg_ctl -ErrorAction SilentlyContinue

if ($pgProcesses) {
    Write-Host "      Found $($pgProcesses.Count) process(es)" -ForegroundColor Red
    foreach ($proc in $pgProcesses) {
        Write-Host "      Stopping PID $($proc.Id) - $($proc.Name)" -ForegroundColor Gray
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    Write-Host "      All processes stopped" -ForegroundColor Green
} else {
    Write-Host "      No processes found" -ForegroundColor Green
}

# Step 2: Remove lock file
Write-Host ""
Write-Host "[2/5] Removing lock file..." -ForegroundColor Yellow
if (Test-Path $lockFile) {
    Remove-Item $lockFile -Force -ErrorAction SilentlyContinue
    Write-Host "      Lock file removed: $lockFile" -ForegroundColor Green
} else {
    Write-Host "      No lock file found" -ForegroundColor Green
}

# Step 3: Check port availability
Write-Host ""
Write-Host "[3/5] Checking port 8000..." -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($port8000) {
    Write-Host "      Port 8000 is occupied!" -ForegroundColor Red
    foreach ($conn in $port8000) {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "      Process: $($proc.Name) (PID: $($proc.Id))" -ForegroundColor Gray
            if ($Force -or $proc.Name -like "*postgres*") {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                Write-Host "      Killed PID $($proc.Id)" -ForegroundColor Green
            }
        }
    }
    Start-Sleep -Seconds 2
} else {
    Write-Host "      Port 8000 is available" -ForegroundColor Green
}

# Step 4: Stop service if running
Write-Host ""
Write-Host "[4/5] Ensuring service is stopped..." -ForegroundColor Yellow
$service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if ($service) {
    if ($service.Status -ne 'Stopped') {
        Stop-Service -Name $serviceName -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        Write-Host "      Service stopped" -ForegroundColor Green
    } else {
        Write-Host "      Service already stopped" -ForegroundColor Green
    }
} else {
    Write-Host "      Service not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 5: Start service
Write-Host ""
Write-Host "[5/5] Starting PostgreSQL service..." -ForegroundColor Yellow

try {
    Start-Service -Name $serviceName -ErrorAction Stop
    Start-Sleep -Seconds 5
    
    $service.Refresh()
    
    if ($service.Status -eq 'Running') {
        Write-Host ""
        Write-Host "============================================" -ForegroundColor Green
        Write-Host "  SUCCESS!" -ForegroundColor Green
        Write-Host "============================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "  PostgreSQL is now running" -ForegroundColor Cyan
        Write-Host "  Port: 8000" -ForegroundColor Cyan
        Write-Host "  Status: $($service.Status)" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "  Service started but status is: $($service.Status)" -ForegroundColor Yellow
        Write-Host "  Waiting 5 more seconds..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
        $service.Refresh()
        Write-Host "  Final status: $($service.Status)" -ForegroundColor Cyan
    }
    
} catch {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "  FAILED TO START" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Checking recent logs..." -ForegroundColor Yellow
    
    # Try to read log
    $logPath = "$dataPath\log"
    if (Test-Path $logPath) {
        $latestLog = Get-ChildItem -Path $logPath -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($latestLog) {
            Write-Host ""
            Write-Host "Last 20 lines from $($latestLog.Name):" -ForegroundColor Cyan
            Get-Content $latestLog.FullName -Tail 20 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        }
    }
    
    Write-Host ""
    Write-Host "Possible solutions:" -ForegroundColor Yellow
    Write-Host "  1. Check data directory: $dataPath" -ForegroundColor White
    Write-Host "  2. Verify postgresql.conf settings" -ForegroundColor White
    Write-Host "  3. Check Windows Event Viewer" -ForegroundColor White
    Write-Host "  4. Try manual start:" -ForegroundColor White
    Write-Host "     cd C:\Program Files\PostgreSQL\18\bin" -ForegroundColor Gray
    Write-Host "     .\pg_ctl.exe start -D $dataPath" -ForegroundColor Gray
}

Write-Host ""
Read-Host "Press Enter to exit"
