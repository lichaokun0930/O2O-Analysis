<# 
订单数据看板 - Nginx 部署脚本
自动配置、启动 Nginx 服务器
#>

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

# 配置
$FRONTEND_PORT = 80
$BACKEND_PORT = 8080

# 自动查找 Nginx 目录（支持多层结构）
$NGINX_DIR = $null
$searchPaths = @(
    "$scriptDir\nginx-server\nginx.exe",
    "$scriptDir\nginx-server\nginx-*\nginx.exe",
    "$scriptDir\nginx\nginx.exe"
)

foreach ($pattern in $searchPaths) {
    $found = Get-Item $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        $NGINX_DIR = Split-Path -Parent $found.FullName
        break
    }
}

if (-not $NGINX_DIR) {
    Write-Host "(X) 未找到 Nginx，请确保已解压到 nginx-server 目录" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "        订单数据看板 - Nginx 生产服务器部署" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""

# ==========================================
# 步骤 1: 检查 Nginx
# ==========================================
Write-Host "(*) 步骤 1: 检查 Nginx ..." -ForegroundColor Cyan
Write-Host "(OK) Nginx 目录: $NGINX_DIR" -ForegroundColor Green
Write-Host ""

# ==========================================
# 步骤 2: 构建前端
# ==========================================
Write-Host "(*) 步骤 2: 构建 React 前端 ..." -ForegroundColor Cyan

$frontendDir = "$scriptDir\frontend-react"

if (-not (Test-Path "$frontendDir\node_modules")) {
    Write-Host "(*) 安装前端依赖 ..." -ForegroundColor Yellow
    Set-Location $frontendDir
    npm install
    Set-Location $scriptDir
}

Write-Host "(*) 执行生产构建 (npm run build) ..." -ForegroundColor Yellow
Set-Location $frontendDir
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "(X) 前端构建失败" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Set-Location $scriptDir
Write-Host "(OK) 前端构建完成" -ForegroundColor Green
Write-Host ""

# ==========================================
# 步骤 3: 复制文件到 Nginx
# ==========================================
Write-Host "(*) 步骤 3: 部署静态文件到 Nginx ..." -ForegroundColor Cyan

$nginxHtml = "$NGINX_DIR\html"

# 清空旧文件
if (Test-Path $nginxHtml) {
    Get-ChildItem $nginxHtml -Exclude "50x.html" | Remove-Item -Recurse -Force
}

# 复制构建产物
Copy-Item -Path "$frontendDir\dist\*" -Destination $nginxHtml -Recurse -Force

Write-Host "(OK) 静态文件已部署" -ForegroundColor Green
Write-Host ""

# ==========================================
# 步骤 4: 配置 Nginx
# ==========================================
Write-Host "(*) 步骤 4: 配置 Nginx ..." -ForegroundColor Cyan

$nginxConf = "$NGINX_DIR\conf\nginx.conf"
$customConf = "$scriptDir\nginx\nginx.conf"

if (Test-Path $customConf) {
    Copy-Item $customConf $nginxConf -Force
    Write-Host "(OK) 已应用自定义配置" -ForegroundColor Green
} else {
    Write-Host "(!) 使用默认配置" -ForegroundColor Yellow
}
Write-Host ""

# ==========================================
# 步骤 5: 停止旧进程
# ==========================================
Write-Host "(*) 步骤 5: 检查旧进程 ..." -ForegroundColor Cyan

$nginxProcess = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
if ($nginxProcess) {
    Write-Host "(*) 停止旧 Nginx 进程 ..." -ForegroundColor Yellow
    Stop-Process -Name "nginx" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# 检查端口 80
$port80 = netstat -ano | Select-String ":80 " | Select-String "LISTENING"
if ($port80) {
    Write-Host "(!) 端口 80 被占用，尝试释放 ..." -ForegroundColor Yellow
    $port80 | ForEach-Object {
        if ($_.Line -match "\s+(\d+)$") {
            $pid = $matches[1]
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc -and $proc.ProcessName -ne "System") {
                Write-Host "    停止进程: $($proc.ProcessName) (PID: $pid)" -ForegroundColor Gray
                Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            }
        }
    }
    Start-Sleep -Seconds 2
}

Write-Host "(OK) 端口已就绪" -ForegroundColor Green
Write-Host ""

# ==========================================
# 步骤 6: 启动 Nginx
# ==========================================
Write-Host "(*) 步骤 6: 启动 Nginx ..." -ForegroundColor Cyan

Set-Location $NGINX_DIR
Start-Process -FilePath ".\nginx.exe" -WindowStyle Hidden
Set-Location $scriptDir

Start-Sleep -Seconds 2

# 验证启动
$nginxRunning = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
if ($nginxRunning) {
    Write-Host "(OK) Nginx 已启动" -ForegroundColor Green
} else {
    Write-Host "(X) Nginx 启动失败，请检查日志: $NGINX_DIR\logs\error.log" -ForegroundColor Red
}
Write-Host ""

# ==========================================
# 完成
# ==========================================
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.*" 
} | Select-Object -First 1).IPAddress

Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  (OK) Nginx 部署完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "  访问地址:" -ForegroundColor White
Write-Host "    本机: http://localhost" -ForegroundColor Cyan
if ($localIP) {
    Write-Host "    局域网: http://$localIP" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "  后端 API: http://localhost:$BACKEND_PORT" -ForegroundColor White
Write-Host "  API 文档: http://localhost:$BACKEND_PORT/docs" -ForegroundColor White
Write-Host ""
Write-Host "  管理命令:" -ForegroundColor White
Write-Host "    停止: .\nginx-server\nginx.exe -s stop" -ForegroundColor Gray
Write-Host "    重载: .\nginx-server\nginx.exe -s reload" -ForegroundColor Gray
Write-Host "    日志: .\nginx-server\logs\" -ForegroundColor Gray
Write-Host ""
Write-Host "  注意: 请确保后端服务已启动 (端口 $BACKEND_PORT)" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""

Read-Host "按回车键退出"
