# 智能门店看板 - 全栈服务一键启动脚本

Write-Host @"
╔══════════════════════════════════════════════════════════╗
║       🚀 智能门店经营看板 - 全栈服务启动器                ║
╚══════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# 检查虚拟环境
$venvPython = ".\.venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "✅ 使用虚拟环境: .venv" -ForegroundColor Green
    $pythonCmd = $venvPython
    $pipCmd = ".\.venv\Scripts\pip.exe"
} else {
    Write-Host "⚠️ 虚拟环境未找到，使用系统Python" -ForegroundColor Yellow
    $pythonCmd = "python"
    $pipCmd = "pip"
}

# 检查Python环境
Write-Host "`n[1/4] 检查Python环境..." -ForegroundColor Yellow
& $pythonCmd --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python未安装或未添加到PATH" -ForegroundColor Red
    exit 1
}

# 检查依赖
Write-Host "`n[2/4] 检查依赖包..." -ForegroundColor Yellow
$packages = @("fastapi", "uvicorn", "sqlalchemy", "psycopg2", "dash")
foreach ($pkg in $packages) {
    & $pythonCmd -c "import $pkg" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️  缺少依赖: $pkg，正在安装..." -ForegroundColor Yellow
        & $pipCmd install $pkg
    }
}
Write-Host "✅ 依赖检查完成" -ForegroundColor Green

# 检查数据库连接
Write-Host "`n[3/4] 检查数据库连接..." -ForegroundColor Yellow
& $pythonCmd -c "from database.connection import check_connection; check_connection()"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 数据库连接失败，请检查配置" -ForegroundColor Red
    Write-Host "   1. 确认PostgreSQL已安装并运行" -ForegroundColor Yellow
    Write-Host "   2. 检查.env文件中的数据库密码" -ForegroundColor Yellow
    Write-Host "   3. 确认数据库'o2o_dashboard'已创建" -ForegroundColor Yellow
    exit 1
}

# 启动服务
Write-Host "`n[4/4] 启动服务..." -ForegroundColor Yellow

Write-Host @"
╔══════════════════════════════════════════════════════════╗
║  🎯 启动模式选择                                           ║
╠══════════════════════════════════════════════════════════╣
║  1. 仅启动后端 API (端口 8000)                              ║
║  2. 仅启动前端看板 (端口 8050)                              ║
║  3. 同时启动前后端 (推荐)                                   ║
║  4. 退出                                                   ║
╚══════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

$choice = Read-Host "`n请选择 (1-4)"

switch ($choice) {
    "1" {
        Write-Host "`n🚀 启动后端API服务..." -ForegroundColor Green
        Write-Host "📍 API地址: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "📖 API文档: http://localhost:8000/api/docs`n" -ForegroundColor Cyan
        & $pythonCmd backend/main.py
    }
    "2" {
        Write-Host "`n🚀 启动前端看板服务..." -ForegroundColor Green
        Write-Host "📍 看板地址: http://localhost:8050`n" -ForegroundColor Cyan
        & $pythonCmd 智能门店看板_Dash版.py
    }
    "3" {
        Write-Host "`n🚀 同时启动前后端服务..." -ForegroundColor Green
        Write-Host "📍 后端API: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "📍 前端看板: http://localhost:8050`n" -ForegroundColor Cyan
        
        # 启动后端（后台运行）
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '$pythonCmd' backend/main.py" -WindowStyle Normal
        
        # 等待2秒
        Start-Sleep -Seconds 2
        
        # 启动前端（当前窗口）
        & $pythonCmd 智能门店看板_Dash版.py
    }
    "4" {
        Write-Host "`n👋 再见！" -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "`n❌ 无效选择" -ForegroundColor Red
        exit 1
    }
}
