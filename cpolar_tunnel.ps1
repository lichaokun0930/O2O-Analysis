<# 
cpolar - Smart Reconnect Mode
Auto reconnect on disconnect
#>

param(
    [string]$TunnelUrl = "https://O2O-Analysis.vip.cpolar.cn",
    [string]$CpolarPath = "C:\Program Files\cpolar\cpolar.exe",
    [string]$Subdomain = "O2O-Analysis",
    [string]$Region = "cn_vip",
    [int]$Port = 80
)

$Host.UI.RawUI.WindowTitle = "cpolar Tunnel - O2O Analysis"
$maxRetries = 999
$retryDelay = 5

function Show-Banner {
    Clear-Host
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host "  cpolar - Smart Reconnect Mode" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  URL: $TunnelUrl" -ForegroundColor Yellow
    Write-Host "  Port: $Port (Nginx)" -ForegroundColor Cyan
    Write-Host "  cpolar: $CpolarPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Auto reconnect on disconnect" -ForegroundColor Gray
    Write-Host "  Press Ctrl+C to stop" -ForegroundColor Gray
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host ""
}

# Check cpolar exists
if (-not (Test-Path $CpolarPath)) {
    Write-Host "(X) cpolar not found: $CpolarPath" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

$retryCount = 0
while ($retryCount -lt $maxRetries) {
    Show-Banner
    
    if ($retryCount -gt 0) {
        Write-Host "(!) Retry $retryCount ..." -ForegroundColor Yellow
    }
    
    Write-Host "(*) Connecting to cpolar server..." -ForegroundColor Cyan
    Write-Host ""
    
    # Start cpolar using Start-Process to handle spaces in path
    $process = Start-Process -FilePath $CpolarPath -ArgumentList "http","-subdomain=$Subdomain","-region=$Region",$Port -NoNewWindow -Wait -PassThru
    
    $exitCode = $process.ExitCode
    
    Write-Host ""
    if ($exitCode -eq 0) {
        Write-Host "(*) cpolar exited normally" -ForegroundColor Green
        break
    } else {
        Write-Host "(!) cpolar disconnected (code: $exitCode)" -ForegroundColor Red
        Write-Host "(*) Reconnecting in $retryDelay seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds $retryDelay
        $retryCount++
    }
}

if ($retryCount -ge $maxRetries) {
    Write-Host "(X) Max retries reached" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to close"
