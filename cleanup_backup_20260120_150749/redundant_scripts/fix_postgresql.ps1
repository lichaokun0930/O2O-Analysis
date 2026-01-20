# PostgreSQL Diagnostic and Fix Script

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Restarting as Administrator..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PostgreSQL Diagnostic Tool" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Find PostgreSQL installation
$pgPath = "C:\Program Files\PostgreSQL\18"
$dataPath = "$pgPath\data"
$logPath = "$dataPath\log"

Write-Host "Checking installation..." -ForegroundColor Yellow
Write-Host "  Path: $pgPath" -ForegroundColor White
Write-Host "  Data: $dataPath" -ForegroundColor White
Write-Host "  Logs: $logPath" -ForegroundColor White
Write-Host ""

# Check if paths exist
if (-not (Test-Path $pgPath)) {
    Write-Host "PostgreSQL not found at $pgPath" -ForegroundColor Red
    $pgPath = Read-Host "Enter PostgreSQL installation path"
    $dataPath = "$pgPath\data"
    $logPath = "$dataPath\log"
}

# Check latest log file
Write-Host "Checking recent errors..." -ForegroundColor Yellow
if (Test-Path $logPath) {
    $latestLog = Get-ChildItem -Path $logPath -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    
    if ($latestLog) {
        Write-Host "Latest log: $($latestLog.Name)" -ForegroundColor Cyan
        Write-Host "Last modified: $($latestLog.LastWriteTime)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "--- Last 30 lines ---" -ForegroundColor Yellow
        Get-Content $latestLog.FullName -Tail 30 | Write-Host -ForegroundColor White
        Write-Host "--- End of log ---" -ForegroundColor Yellow
        Write-Host ""
    }
} else {
    Write-Host "Log directory not found: $logPath" -ForegroundColor Red
}

# Common fixes
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Common Solutions:" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Check port 8000 (or 5432)" -ForegroundColor Yellow

$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$port5432 = Get-NetTCPConnection -LocalPort 5432 -ErrorAction SilentlyContinue

if ($port8000) {
    Write-Host "   Port 8000 is in use:" -ForegroundColor Red
    $port8000 | ForEach-Object {
        $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "   Process: $($proc.Name) (PID: $($_.OwningProcess))" -ForegroundColor White
    }
    
    $kill = Read-Host "`n   Kill process on port 8000? (y/n)"
    if ($kill -eq 'y') {
        $port8000 | ForEach-Object {
            Stop-Process -Id $_.OwningProcess -Force
            Write-Host "   Killed PID $($_.OwningProcess)" -ForegroundColor Green
        }
    }
} else {
    Write-Host "   Port 8000 is free" -ForegroundColor Green
}

if ($port5432) {
    Write-Host "   Port 5432 is in use:" -ForegroundColor Yellow
    $port5432 | ForEach-Object {
        $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        Write-Host "   Process: $($proc.Name) (PID: $($_.OwningProcess))" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "2. Check data directory lock" -ForegroundColor Yellow

$lockFile = "$dataPath\postmaster.pid"
if (Test-Path $lockFile) {
    Write-Host "   Lock file exists: $lockFile" -ForegroundColor Red
    Write-Host "   Content:" -ForegroundColor Gray
    Get-Content $lockFile | Write-Host -ForegroundColor White
    
    $removeLock = Read-Host "`n   Remove lock file? (y/n)"
    if ($removeLock -eq 'y') {
        Remove-Item $lockFile -Force
        Write-Host "   Lock file removed" -ForegroundColor Green
    }
} else {
    Write-Host "   No lock file found (OK)" -ForegroundColor Green
}

Write-Host ""
Write-Host "3. Try to start service" -ForegroundColor Yellow

$service = Get-Service -Name "postgresql-x64-18" -ErrorAction SilentlyContinue

if ($service) {
    Write-Host "   Service status: $($service.Status)" -ForegroundColor Cyan
    
    if ($service.Status -eq 'Stopped') {
        $tryStart = Read-Host "`n   Try to start now? (y/n)"
        if ($tryStart -eq 'y') {
            try {
                Start-Service -Name $service.Name
                Start-Sleep -Seconds 3
                $service.Refresh()
                
                if ($service.Status -eq 'Running') {
                    Write-Host ""
                    Write-Host "   SUCCESS! PostgreSQL is now running" -ForegroundColor Green
                } else {
                    Write-Host "   Still stopped. Check logs above for errors." -ForegroundColor Red
                }
            } catch {
                Write-Host "   Error: $_" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "   Service is running!" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "4. Manual start option" -ForegroundColor Yellow
Write-Host "   If service won't start, try manual:" -ForegroundColor Gray
Write-Host "   cd `"$pgPath\bin`"" -ForegroundColor White
Write-Host "   .\pg_ctl.exe start -D `"$dataPath`"" -ForegroundColor White

Write-Host ""
$manual = Read-Host "Try manual start now? (y/n)"

if ($manual -eq 'y') {
    $pgCtl = "$pgPath\bin\pg_ctl.exe"
    
    if (Test-Path $pgCtl) {
        Write-Host ""
        Write-Host "Starting PostgreSQL manually..." -ForegroundColor Yellow
        & $pgCtl start -D $dataPath
        
        Start-Sleep -Seconds 3
        Write-Host ""
        & $pgCtl status -D $dataPath
    } else {
        Write-Host "pg_ctl.exe not found at $pgCtl" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
