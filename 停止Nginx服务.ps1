<# 
停止 Nginx 和后端服务
#>

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$BACKEND_PORT = 8080

# 自动查找 Nginx 目录
$NGINX_DIR = $null
$searchPaths = @(
    "$scriptDir\nginx-server\nginx.exe",
    "$scriptDir\nginx-server\nginx-*\nginx.exe"
)

foreach ($pattern in $searchPaths) {
    $found = Get-Item $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        $NGINX_DIR = Split-Path -Parent $found.FullName
        break
    }
}

Write-Host ""
Write-Host "(*) 停止服务 ..." -ForegroundColor Cyan

# 停止 Nginx
if ($NGINX_DIR -and (Test-Path "$NGINX_DIR\nginx.exe")) {
    Set-Location $NGINX_DIR
    & .\nginx.exe -s stop 2>$null
    Set-Location $scriptDir
}
Stop-Process -Name "nginx" -Force -ErrorAction SilentlyContinue
Write-Host "(OK) Nginx 已停止" -ForegroundColor Green

# 停止后端
$backendPort = netstat -ano | Select-String ":$BACKEND_PORT " | Select-String "LISTENING"
if ($backendPort) {
    $backendPort | ForEach-Object {
        if ($_.Line -match "\s+(\d+)$") {
            Stop-Process -Id $matches[1] -Force -ErrorAction SilentlyContinue
        }
    }
}
Write-Host "(OK) 后端服务已停止" -ForegroundColor Green

Write-Host ""
Write-Host "(OK) 所有服务已停止" -ForegroundColor Green
Write-Host ""
