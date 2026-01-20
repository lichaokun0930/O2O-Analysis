# PostgreSQL Database Startup Script
# For port 8000

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PostgreSQL Database Startup" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check PostgreSQL service
Write-Host "Checking PostgreSQL services..." -ForegroundColor Yellow
$services = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue

if ($services) {
    Write-Host "`nFound PostgreSQL services:" -ForegroundColor Green
    $services | Format-Table Name, Status, DisplayName -AutoSize
    
    Write-Host "`nStarting services..." -ForegroundColor Yellow
    foreach ($service in $services) {
        if ($service.Status -ne 'Running') {
            try {
                Write-Host "Starting $($service.Name)..." -ForegroundColor Cyan
                Start-Service -Name $service.Name -ErrorAction Stop
                Write-Host "  OK - Service started" -ForegroundColor Green
            } catch {
                Write-Host "  ERROR: $_" -ForegroundColor Red
            }
        } else {
            Write-Host "$($service.Name) is already running" -ForegroundColor Green
        }
    }
    
    Write-Host "`nCurrent status:" -ForegroundColor Yellow
    Get-Service -Name "postgresql*" | Format-Table Name, Status -AutoSize
    
} else {
    Write-Host "No PostgreSQL service found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Alternative: Try using pg_ctl" -ForegroundColor Yellow
    Write-Host ""
    
    # Common PostgreSQL paths
    $pgPaths = @(
        "C:\Program Files\PostgreSQL\16\bin\pg_ctl.exe",
        "C:\Program Files\PostgreSQL\15\bin\pg_ctl.exe",
        "C:\Program Files\PostgreSQL\14\bin\pg_ctl.exe",
        "C:\PostgreSQL\bin\pg_ctl.exe",
        "D:\PostgreSQL\bin\pg_ctl.exe"
    )
    
    $pgCtl = $null
    foreach ($path in $pgPaths) {
        if (Test-Path $path) {
            $pgCtl = $path
            Write-Host "Found pg_ctl: $path" -ForegroundColor Green
            break
        }
    }
    
    if ($pgCtl) {
        $dataPath = Split-Path (Split-Path $pgCtl) | Join-Path -ChildPath "data"
        
        if (Test-Path $dataPath) {
            Write-Host "Data directory: $dataPath" -ForegroundColor Green
            Write-Host ""
            Write-Host "Starting PostgreSQL..." -ForegroundColor Yellow
            
            & $pgCtl start -D $dataPath
            
            Start-Sleep -Seconds 2
            Write-Host ""
            & $pgCtl status -D $dataPath
        } else {
            Write-Host "Data directory not found: $dataPath" -ForegroundColor Red
        }
    } else {
        Write-Host "pg_ctl not found in common locations" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please check:" -ForegroundColor Yellow
        Write-Host "1. Is PostgreSQL installed?" -ForegroundColor White
        Write-Host "2. Installation path" -ForegroundColor White
        Write-Host "3. Run as Administrator" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
