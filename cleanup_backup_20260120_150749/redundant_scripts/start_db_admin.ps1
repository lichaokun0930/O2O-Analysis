# Start PostgreSQL with Administrator privileges

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Restarting as Administrator..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PostgreSQL Database Startup (Admin)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start PostgreSQL service
$service = Get-Service -Name "postgresql-x64-18" -ErrorAction SilentlyContinue

if ($service) {
    Write-Host "Service: $($service.DisplayName)" -ForegroundColor Cyan
    Write-Host "Status: $($service.Status)" -ForegroundColor Yellow
    Write-Host ""
    
    if ($service.Status -ne 'Running') {
        Write-Host "Starting PostgreSQL..." -ForegroundColor Yellow
        try {
            Start-Service -Name $service.Name
            Start-Sleep -Seconds 3
            
            $service.Refresh()
            if ($service.Status -eq 'Running') {
                Write-Host ""
                Write-Host "========================================" -ForegroundColor Green
                Write-Host "PostgreSQL Started Successfully!" -ForegroundColor Green
                Write-Host "========================================" -ForegroundColor Green
                Write-Host ""
                Write-Host "Database is now running on port 8000" -ForegroundColor Cyan
            } else {
                Write-Host "Failed to start. Status: $($service.Status)" -ForegroundColor Red
            }
        } catch {
            Write-Host "Error: $_" -ForegroundColor Red
            Write-Host ""
            Write-Host "Check the PostgreSQL log file:" -ForegroundColor Yellow
            Write-Host "C:\Program Files\PostgreSQL\18\data\log\" -ForegroundColor White
        }
    } else {
        Write-Host "PostgreSQL is already running!" -ForegroundColor Green
        Write-Host "Port: 8000" -ForegroundColor Cyan
    }
} else {
    Write-Host "PostgreSQL service not found!" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"
