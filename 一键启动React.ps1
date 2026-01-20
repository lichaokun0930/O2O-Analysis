<# 
订单数据看板 - React版一键启动脚本
支持开发模式和生产模式
#>

# ==========================================
# 配置
# ==========================================
$FRONTEND_DEV_PORT = 6001
$FRONTEND_PROD_PORT = 4001
$BACKEND_PORT = 8080

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

# ==========================================
# 检查后端是否就绪
# ==========================================
function Test-BackendReady {
    param(
        [int]$Port = $BACKEND_PORT,
        [int]$Timeout = 60
    )
    
    $startTime = Get-Date
    $elapsed = 0
    
    while ($elapsed -lt $Timeout) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                return $true
            }
        } catch {
            # 忽略错误，继续重试
        }
        
        Start-Sleep -Seconds 2
        $elapsed = (Get-Date) - $startTime
        $elapsed = $elapsed.TotalSeconds
    }
    
    return $false
}

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

# ==========================================
# 显示标题
# ==========================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "            订单数据看板 - React版一键启动" -ForegroundColor White
Write-Host "        Frontend: React 18   Backend: FastAPI" -ForegroundColor Magenta
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "    环境: Development" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""

# ==========================================
# 检查 Redis/Memurai
# ==========================================
Write-Host "(*) 检查 Redis 缓存服务 ..." -ForegroundColor Cyan
$memuraiService = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue

if ($memuraiService) {
    if ($memuraiService.Status -eq "Running") {
        Write-Host "(OK) Redis 已运行 (Memurai)" -ForegroundColor Green
    } else {
        Write-Host "(!) Memurai 未运行，正在启动..." -ForegroundColor Yellow
        try {
            Start-Service -Name "Memurai" -ErrorAction Stop
            Start-Sleep -Seconds 2
            Write-Host "(OK) Redis 已启动 (Memurai)" -ForegroundColor Green
        } catch {
            Write-Host "(!) Redis 启动失败，缓存功能不可用" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "(!) Memurai 服务未安装，缓存功能不可用" -ForegroundColor Yellow
}
Write-Host ""

# ==========================================
# 检查 PostgreSQL
# ==========================================
Write-Host "(*) 检查 PostgreSQL 数据库 ..." -ForegroundColor Cyan

$pgCheckScript = @"
import sys
try:
    from database.connection import engine, check_connection
    from sqlalchemy import text
    result = check_connection()
    if result['connected']:
        with engine.connect() as conn:
            count = conn.execute(text('SELECT COUNT(*) FROM orders')).scalar()
        print(f'OK|{count}')
    else:
        print('FAIL|' + result['message'])
except Exception as e:
    print('ERROR|' + str(e))
"@

$pgResult = & $pythonExe -c $pgCheckScript 2>&1
$pgParts = "$pgResult" -split '\|'

if ($pgParts[0] -eq "OK") {
    Write-Host "(OK) PostgreSQL 数据库已连接" -ForegroundColor Green
    if ($pgParts.Length -gt 1 -and $pgParts[1]) {
        Write-Host "     订单数据: $($pgParts[1]) 条" -ForegroundColor Cyan
    }
} else {
    Write-Host "(!) PostgreSQL 未连接，尝试启动..." -ForegroundColor Yellow
    
    $services = @('postgresql-x64-16', 'postgresql-x64-15', 'postgresql-x64-14', 'postgresql')
    $started = $false
    foreach ($svc in $services) {
        try {
            Start-Service -Name $svc -ErrorAction Stop
            Start-Sleep -Seconds 3
            Write-Host "(OK) PostgreSQL 已启动 ($svc)" -ForegroundColor Green
            $started = $true
            break
        } catch {
            continue
        }
    }
    
    if (-not $started) {
        Write-Host "(!) PostgreSQL 启动失败" -ForegroundColor Yellow
    }
}
Write-Host ""

# ==========================================
# 检查 Node.js
# ==========================================
$nodeVersion = & node -v 2>$null
if ($nodeVersion) {
    Write-Host "(OK) Node.js: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "(X) Node.js 未安装" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}
Write-Host ""

# ==========================================
# 检查旧进程
# ==========================================
Write-Host "(*) 检查旧进程 ..." -ForegroundColor Cyan

$frontendPort = netstat -ano | Select-String ":$FRONTEND_DEV_PORT " | Select-String "LISTENING"
$backendPort = netstat -ano | Select-String ":$BACKEND_PORT " | Select-String "LISTENING"

if ($frontendPort -or $backendPort) {
    Write-Host "(!) 发现旧进程，正在清理..." -ForegroundColor Yellow
    
    if ($frontendPort) {
        $frontendPort | ForEach-Object {
            if ($_.Line -match "\s+(\d+)$") {
                $processId = $matches[1]
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            }
        }
    }
    
    if ($backendPort) {
        $backendPort | ForEach-Object {
            if ($_.Line -match "\s+(\d+)$") {
                $processId = $matches[1]
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            }
        }
    }
    
    Start-Sleep -Seconds 2
    Write-Host "(OK) 旧进程已清理" -ForegroundColor Green
} else {
    Write-Host "(OK) 端口可用" -ForegroundColor Green
}
Write-Host ""

# ==========================================
# 菜单
# ==========================================
Write-Host "  ------------------------------------------" -ForegroundColor Gray
Write-Host "  1 - 开发模式 (前后端热重载)" -ForegroundColor White
Write-Host "  2 - 生产模式 (构建+多进程)" -ForegroundColor White
Write-Host "  3 - 仅启动后端" -ForegroundColor White
Write-Host "  4 - 仅启动前端 (React)" -ForegroundColor White
Write-Host "  0 - 退出" -ForegroundColor White
Write-Host "  ------------------------------------------" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "请选择 (0-4)"

switch ($choice) {
    "1" {
        # 开发模式
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Magenta
        Write-Host "  (Development) 开发模式 (支持热重载)" -ForegroundColor Green
        Write-Host "  (*) 代码修改后会自动刷新，无需手动重启" -ForegroundColor Cyan
        Write-Host ""
        
        # 安装前端依赖
        if (-not (Test-Path "$scriptDir\frontend-react\node_modules")) {
            Write-Host "(*) 安装 React 前端依赖 ..." -ForegroundColor Cyan
            Set-Location "$scriptDir\frontend-react"
            npm install
            Set-Location $scriptDir
        }
        
        # 检查后端依赖
        Write-Host "(*) 检查后端依赖 ..." -ForegroundColor Cyan
        $uvicornCheck = & $pythonExe -c "import uvicorn" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "(*) 安装后端依赖 ..." -ForegroundColor Yellow
            & $pythonExe -m pip install -r "$scriptDir\backend\requirements.txt"
        }
        Write-Host "(OK) 后端依赖已就绪" -ForegroundColor Green
        
        # 启动后端
        Write-Host "(*) 启动后端 API 服务器 ..." -ForegroundColor Cyan
        
        # 获取虚拟环境激活脚本路径
        $venvActivate = Join-Path $parentDir ".venv\Scripts\Activate.ps1"
        if (-not (Test-Path $venvActivate)) {
            $venvActivate = Join-Path $scriptDir ".venv\Scripts\Activate.ps1"
        }
        
        $backendScript = @"
Write-Host '============================================================' -ForegroundColor Magenta
Write-Host '  Backend API Server - Development Mode' -ForegroundColor Green
Write-Host '  Port: $BACKEND_PORT' -ForegroundColor Cyan
Write-Host '  Press Ctrl+C to stop' -ForegroundColor Yellow
Write-Host '============================================================' -ForegroundColor Magenta
Write-Host ''
# 激活虚拟环境
if (Test-Path '$venvActivate') {
    & '$venvActivate'
}
Set-Location '$scriptDir\backend'
`$env:ENVIRONMENT = 'development'
`$env:DEBUG = 'true'
`$env:PYTHONPATH = '$scriptDir;$scriptDir\backend\app'
python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload --reload-dir app --log-level debug
"@
        Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript
        
        # 等待后端完全启动
        Write-Host "(*) 等待后端服务启动 ..." -ForegroundColor Cyan
        if (Test-BackendReady -Port $BACKEND_PORT -Timeout 60) {
            Write-Host "(OK) 后端服务已就绪" -ForegroundColor Green
            
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
        } else {
            Write-Host "(!) 后端服务启动超时，但继续启动前端" -ForegroundColor Yellow
        }
        
        # 获取本机IP
        $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.*" } | Select-Object -First 1).IPAddress
        
        Write-Host ""
        Write-Host "    本机访问: http://localhost:$FRONTEND_DEV_PORT" -ForegroundColor Green
        if ($localIP) {
            Write-Host "    局域网访问: http://${localIP}:$FRONTEND_DEV_PORT" -ForegroundColor Green
        }
        Write-Host "    API 地址: http://localhost:$BACKEND_PORT" -ForegroundColor Green
        Write-Host "    API 文档: http://localhost:$BACKEND_PORT/docs" -ForegroundColor Green
        Write-Host "    监控后台: http://localhost:$BACKEND_PORT/api/v1/observability/dashboard" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "    按 Ctrl+C 停止服务" -ForegroundColor Yellow
        Write-Host "============================================================" -ForegroundColor Magenta
        Write-Host ""
        
        # 启动前端
        Set-Location "$scriptDir\frontend-react"
        npm run dev
    }
    "2" {
        # 生产模式
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Magenta
        Write-Host "  (Production) 生产模式" -ForegroundColor Green
        Write-Host ""
        
        # 检查后端依赖
        $uvicornCheck = & $pythonExe -c "import uvicorn" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "(*) 安装后端依赖 ..." -ForegroundColor Yellow
            & $pythonExe -m pip install -r "$scriptDir\backend\requirements.txt"
        }
        
        # 构建前端
        Write-Host "(*) 构建 React 前端生产版本 ..." -ForegroundColor Cyan
        Set-Location "$scriptDir\frontend-react"
        
        if (-not (Test-Path "node_modules")) {
            Write-Host "(*) 安装 React 前端依赖 ..." -ForegroundColor Cyan
            npm install
        }
        
        npm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Host "(X) 前端构建失败" -ForegroundColor Red
            Read-Host "按回车键退出"
            exit 1
        }
        Write-Host "(OK) 前端构建完成" -ForegroundColor Green
        
        # 计算 workers（根据 CPU 核心数优化）
        # 你的 Ryzen 9 有 16 核，可以跑更多 workers
        $workers = [Math]::Min([Environment]::ProcessorCount, 16)
        
        # 启动后端
        Write-Host "(*) 启动后端生产服务器 (Hypercorn, $workers workers) ..." -ForegroundColor Cyan
        
        # 获取虚拟环境激活脚本路径
        $venvActivate = Join-Path $parentDir ".venv\Scripts\Activate.ps1"
        if (-not (Test-Path $venvActivate)) {
            $venvActivate = Join-Path $scriptDir ".venv\Scripts\Activate.ps1"
        }
        
        # 检查并安装 hypercorn
        Write-Host "(*) 检查 Hypercorn ..." -ForegroundColor Cyan
        $hypercornCheck = & $pythonExe -c "import hypercorn" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "(*) 安装 Hypercorn ..." -ForegroundColor Yellow
            & $pythonExe -m pip install hypercorn>=0.16.0
        }
        
        $backendScript = @"
Write-Host '============================================================' -ForegroundColor Magenta
Write-Host '  Backend API Server - Production Mode (Hypercorn)' -ForegroundColor Green
Write-Host '  Port: $BACKEND_PORT | Workers: $workers' -ForegroundColor Cyan
Write-Host '  Hypercorn 支持 Windows 多进程，性能更稳定' -ForegroundColor Yellow
Write-Host '============================================================' -ForegroundColor Magenta
Write-Host ''
# 激活虚拟环境
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
        
        # 等待后端完全启动
        Write-Host "(*) 等待后端服务启动 ..." -ForegroundColor Cyan
        if (Test-BackendReady -Port $BACKEND_PORT -Timeout 60) {
            Write-Host "(OK) 后端服务已就绪" -ForegroundColor Green
            
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
                
                $currentEngine = $routerData.current_engine.ToUpper()
                Write-Host "  当前引擎: $currentEngine" -ForegroundColor Green
                
                if ($routerData.record_count -lt $routerData.switch_threshold) {
                    $remaining = $routerData.switch_threshold - $routerData.record_count
                    Write-Host "  智能切换: 数据量达到 $($routerData.switch_threshold.ToString('N0')) 条后自动切换到 DuckDB" -ForegroundColor Yellow
                } else {
                    if ($routerData.engines.duckdb) {
                        Write-Host "  智能切换: 已启用 DuckDB 加速" -ForegroundColor Green
                    }
                }
                Write-Host ""
            } catch {
                Write-Host "(!) 无法获取路由状态" -ForegroundColor Yellow
            }
        } else {
            Write-Host "(!) 后端服务启动超时，但继续启动前端" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "    前端: http://localhost:$FRONTEND_PROD_PORT" -ForegroundColor Green
        Write-Host "    后端: http://localhost:$BACKEND_PORT" -ForegroundColor Green
        Write-Host ""
        
        # 启动前端预览
        Set-Location "$scriptDir\frontend-react"
        npm run preview -- --port $FRONTEND_PROD_PORT
    }
    "3" {
        # 仅启动后端
        Write-Host ""
        Write-Host "(*) 检查后端依赖 ..." -ForegroundColor Cyan
        $uvicornCheck = & $pythonExe -c "import uvicorn" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "(*) 安装后端依赖 ..." -ForegroundColor Yellow
            & $pythonExe -m pip install -r "$scriptDir\backend\requirements.txt"
        }
        
        Write-Host "(*) 启动后端服务 ..." -ForegroundColor Cyan
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Magenta
        Write-Host "  Backend API Server - Development Mode" -ForegroundColor Green
        Write-Host "  Port: $BACKEND_PORT" -ForegroundColor Cyan
        Write-Host "  API Docs: http://localhost:$BACKEND_PORT/docs" -ForegroundColor Cyan
        Write-Host "============================================================" -ForegroundColor Magenta
        Write-Host ""
        
        Set-Location "$scriptDir\backend"
        $env:ENVIRONMENT = "development"
        $env:DEBUG = "true"
        $env:PYTHONPATH = "$scriptDir;$scriptDir\backend\app"
        & $pythonExe -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload --reload-dir app --log-level debug
    }
    "4" {
        # 仅启动前端
        Write-Host ""
        Write-Host "(*) 启动 React 前端服务 ..." -ForegroundColor Cyan
        
        if (-not (Test-Path "$scriptDir\frontend-react\node_modules")) {
            Write-Host "(*) 安装 React 前端依赖 ..." -ForegroundColor Cyan
            Set-Location "$scriptDir\frontend-react"
            npm install
        }
        
        Set-Location "$scriptDir\frontend-react"
        npm run dev
    }
    "0" {
        Write-Host "退出" -ForegroundColor Gray
        exit 0
    }
    default {
        Write-Host "(!) 无效选项" -ForegroundColor Yellow
    }
}
