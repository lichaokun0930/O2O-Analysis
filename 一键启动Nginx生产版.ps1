<# 
订单数据看板 - Nginx 生产版一键启动
同时启动：Nginx (前端) + Hypercorn (后端)
#>

$ErrorActionPreference = "SilentlyContinue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

# 配置
$BACKEND_PORT = 8080

# 自动查找 Nginx 目录
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

Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "      订单数据看板 - Nginx 生产版一键启动" -ForegroundColor White
Write-Host "      Frontend: Nginx    Backend: Hypercorn" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""

# ==========================================
# 检查 Nginx 是否已部署
# ==========================================
if (-not $NGINX_DIR) {
    Write-Host "(!) Nginx 未找到，请先运行 部署Nginx服务器.ps1" -ForegroundColor Yellow
    Write-Host ""
    $deploy = Read-Host "是否现在部署? (Y/N)"
    if ($deploy -eq "Y" -or $deploy -eq "y") {
        & "$scriptDir\部署Nginx服务器.ps1"
    }
    exit
}

# ==========================================
# 检查服务
# ==========================================
Write-Host "(*) 检查服务状态 ..." -ForegroundColor Cyan

# Redis/Memurai
$memuraiService = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue
if ($memuraiService -and $memuraiService.Status -ne "Running") {
    Start-Service -Name "Memurai" -ErrorAction SilentlyContinue
}
Write-Host "(OK) Redis 缓存" -ForegroundColor Green

# PostgreSQL
$pgServices = @('postgresql-x64-16', 'postgresql-x64-15', 'postgresql-x64-14', 'postgresql')
foreach ($svc in $pgServices) {
    $pgService = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($pgService) {
        if ($pgService.Status -ne "Running") {
            Start-Service -Name $svc -ErrorAction SilentlyContinue
        }
        break
    }
}
Write-Host "(OK) PostgreSQL 数据库" -ForegroundColor Green
Write-Host ""

# ==========================================
# 停止旧进程
# ==========================================
Write-Host "(*) 清理旧进程 ..." -ForegroundColor Cyan

# 停止 Nginx
Stop-Process -Name "nginx" -Force -ErrorAction SilentlyContinue

# 停止后端
$backendPort = netstat -ano | Select-String ":$BACKEND_PORT " | Select-String "LISTENING"
if ($backendPort) {
    $backendPort | ForEach-Object {
        if ($_.Line -match "\s+(\d+)$") {
            Stop-Process -Id $matches[1] -Force -ErrorAction SilentlyContinue
        }
    }
}

Start-Sleep -Seconds 2
Write-Host "(OK) 旧进程已清理" -ForegroundColor Green
Write-Host ""

# ==========================================
# 查找 Python
# ==========================================
$parentDir = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $parentDir ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"
}
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

# 虚拟环境激活脚本
$venvActivate = Join-Path $parentDir ".venv\Scripts\Activate.ps1"
if (-not (Test-Path $venvActivate)) {
    $venvActivate = Join-Path $scriptDir ".venv\Scripts\Activate.ps1"
}

# ==========================================
# 启动后端
# ==========================================
Write-Host "(*) 启动后端服务 (Hypercorn) ..." -ForegroundColor Cyan

$workers = [Math]::Min([Environment]::ProcessorCount, 16)

$backendScript = @"
Write-Host '============================================================' -ForegroundColor Magenta
Write-Host '  Backend API Server - Production Mode (Hypercorn)' -ForegroundColor Green
Write-Host '  Port: $BACKEND_PORT | Workers: $workers' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Magenta
Write-Host ''
if (Test-Path '$venvActivate') {
    & '$venvActivate'
}
Set-Location '$scriptDir\backend'
`$env:ENVIRONMENT = 'production'
`$env:DEBUG = 'false'
`$env:PYTHONPATH = '$scriptDir;$scriptDir\backend\app'
python -m hypercorn app.main:app --bind 0.0.0.0:$BACKEND_PORT --workers $workers --access-log -
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript

# 等待后端启动
Write-Host "(*) 等待后端服务就绪 ..." -ForegroundColor Cyan
$timeout = 30
$elapsed = 0
while ($elapsed -lt $timeout) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$BACKEND_PORT/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "(OK) 后端服务已就绪" -ForegroundColor Green
            break
        }
    } catch { }
    Start-Sleep -Seconds 2
    $elapsed += 2
}

if ($elapsed -ge $timeout) {
    Write-Host "(!) 后端启动超时，继续启动 Nginx" -ForegroundColor Yellow
} else {
    # 显示智能路由状态
    Write-Host ""
    Write-Host "(*) 获取智能查询路由状态 ..." -ForegroundColor Cyan
    try {
        $routerResponse = Invoke-WebRequest -Uri "http://127.0.0.1:$BACKEND_PORT/api/v1/observability/query-router/status" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        $routerData = $routerResponse.Content | ConvertFrom-Json
        
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Magenta
        Write-Host "  智能查询路由引擎" -ForegroundColor White
        Write-Host "============================================================" -ForegroundColor Magenta
        Write-Host ""
        Write-Host "  数据量: $($routerData.record_count.ToString('N0')) 条 ($($routerData.data_level_desc)数据)" -ForegroundColor Cyan
        Write-Host "  切换阈值: $($routerData.switch_threshold.ToString('N0')) 条" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  查询引擎状态:" -ForegroundColor White
        
        if ($routerData.engines.postgresql) {
            Write-Host "    (OK) PostgreSQL: 可用" -ForegroundColor Green
        } else {
            Write-Host "    (X) PostgreSQL: 不可用" -ForegroundColor Red
        }
        
        if ($routerData.engines.duckdb) {
            Write-Host "    (OK) DuckDB: 可用" -ForegroundColor Green
        } else {
            Write-Host "    (!) DuckDB: 未就绪" -ForegroundColor Yellow
        }
        
        Write-Host ""
        $currentEngine = $routerData.current_engine.ToUpper()
        Write-Host "  当前引擎: $currentEngine" -ForegroundColor Green
        
        if ($routerData.record_count -lt $routerData.switch_threshold) {
            $remaining = $routerData.switch_threshold - $routerData.record_count
            Write-Host "  智能切换: 数据量达到 $($routerData.switch_threshold.ToString('N0')) 条后自动切换到 DuckDB" -ForegroundColor Yellow
            Write-Host "            (还需 $($remaining.ToString('N0')) 条)" -ForegroundColor Gray
        } else {
            if ($routerData.engines.duckdb) {
                Write-Host "  智能切换: 已启用 DuckDB 加速" -ForegroundColor Green
            } else {
                Write-Host "  智能切换: 数据量已达标，但 DuckDB 未就绪" -ForegroundColor Yellow
            }
        }
        Write-Host ""
    } catch {
        Write-Host "(!) 无法获取路由状态: $_" -ForegroundColor Yellow
    }
}
Write-Host ""

# ==========================================
# 启动 Nginx
# ==========================================
Write-Host "(*) 启动 Nginx 服务 ..." -ForegroundColor Cyan

Set-Location $NGINX_DIR
Start-Process -FilePath ".\nginx.exe" -WindowStyle Hidden
Set-Location $scriptDir

Start-Sleep -Seconds 2

$nginxRunning = Get-Process -Name "nginx" -ErrorAction SilentlyContinue
if ($nginxRunning) {
    Write-Host "(OK) Nginx 已启动" -ForegroundColor Green
} else {
    Write-Host "(X) Nginx 启动失败" -ForegroundColor Red
}
Write-Host ""

# ==========================================
# 完成
# ==========================================
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.*" 
} | Select-Object -First 1).IPAddress

Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  (OK) 生产环境已启动！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "  访问地址:" -ForegroundColor White
Write-Host "    本机: http://localhost" -ForegroundColor Cyan
if ($localIP) {
    Write-Host "    局域网: http://$localIP" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "  后端 API: http://localhost:$BACKEND_PORT/docs" -ForegroundColor Gray
Write-Host "  监控后台: http://localhost:$BACKEND_PORT/api/v1/observability/dashboard" -ForegroundColor Cyan
Write-Host ""
Write-Host "  性能配置:" -ForegroundColor White
Write-Host "    Nginx: 静态资源 + API 代理" -ForegroundColor Gray
Write-Host "    Hypercorn: $workers workers" -ForegroundColor Gray
Write-Host "    Redis: 4GB 缓存" -ForegroundColor Gray
Write-Host ""
Write-Host "  停止服务:" -ForegroundColor White
Write-Host "    .\停止Nginx服务.ps1" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""

Read-Host "按回车键退出（服务会继续运行）"
