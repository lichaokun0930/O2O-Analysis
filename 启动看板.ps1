# 智能门店经营看板 - 启动脚本

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "智能门店经营看板 - 生产模式" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# ========== 自动检查并启动 Memurai Redis 服务 ==========
Write-Host "🔍 检查 Memurai Redis 服务..." -ForegroundColor Yellow
$memuraiService = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue

if ($memuraiService) {
    if ($memuraiService.Status -ne "Running") {
        Write-Host "⚠️  Memurai 服务未运行，正在启动..." -ForegroundColor Yellow
        try {
            # 尝试普通启动
            Start-Service -Name "Memurai" -ErrorAction Stop
            Start-Sleep -Seconds 2
            Write-Host "✅ Memurai Redis 服务已启动" -ForegroundColor Green
        } catch {
            # 需要管理员权限
            Write-Host "🔐 需要管理员权限，正在请求..." -ForegroundColor Cyan
            Start-Process powershell -ArgumentList "-Command", "Start-Service -Name 'Memurai'" -Verb RunAs -Wait
            Start-Sleep -Seconds 2
            
            # 验证启动结果
            $memuraiService = Get-Service -Name "Memurai"
            if ($memuraiService.Status -eq "Running") {
                Write-Host "✅ Memurai Redis 服务已启动" -ForegroundColor Green
            } else {
                Write-Host "❌ Memurai 启动失败，请手动检查" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "✅ Memurai Redis 服务正在运行" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  未检测到 Memurai 服务，Redis 缓存将不可用" -ForegroundColor Yellow
    Write-Host "   提示: 运行 .\安装Memurai_Redis.ps1 安装 Redis" -ForegroundColor Gray
}

# ========== 检查 PostgreSQL 数据库连接 ==========
Write-Host ""
Write-Host "🔍 检查 PostgreSQL 数据库连接..." -ForegroundColor Yellow

# 虚拟环境在父目录
$parentDir = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $parentDir ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    # 备选：当前目录的.venv
    $pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"
}
if (-not (Test-Path $pythonExe)) {
    Write-Warning "未找到虚拟环境，将使用系统 python。"
    $pythonExe = "python"
} else {
    Write-Host "✅ 使用虚拟环境: $pythonExe" -ForegroundColor Green
}

$pgCheckScript = @"
import sys
try:
    from database.connection import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1')).fetchone()
        if result:
            print('OK')
        else:
            print('FAIL')
except Exception as e:
    print(f'ERROR:{e}')
"@

$pgResult = & $pythonExe -c $pgCheckScript 2>&1
if ($pgResult -eq "OK") {
    Write-Host "✅ PostgreSQL 数据库连接正常" -ForegroundColor Green
} elseif ($pgResult -like "ERROR:*") {
    $errorMsg = $pgResult -replace "ERROR:", ""
    Write-Host "❌ PostgreSQL 数据库连接失败: $errorMsg" -ForegroundColor Red
    Write-Host "   提示: 请检查数据库服务是否运行，或运行 .\启动数据库.ps1" -ForegroundColor Gray
} else {
    Write-Host "⚠️  PostgreSQL 数据库状态未知" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "💡 提示: 如需查看详细调试日志，请使用:" -ForegroundColor Gray
Write-Host "   .\启动看板-调试模式.ps1" -ForegroundColor Cyan
Write-Host ""

Write-Host "检测已有看板进程..." -ForegroundColor Yellow
$running = Get-CimInstance Win32_Process -Filter "name='python.exe'" -ErrorAction SilentlyContinue |
	Where-Object { $_.CommandLine -match "智能门店看板_Dash版\.py" }

if ($running) {
	$running | ForEach-Object {
		Write-Host "停止PID $($_.ProcessId) -> $($_.CommandLine)" -ForegroundColor DarkYellow
		Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
	}
	Start-Sleep -Seconds 1
} else {
	Write-Host "未发现正在运行的看板实例。" -ForegroundColor DarkGreen
}

Write-Host "正在启动应用..." -ForegroundColor Yellow
Write-Host "访问地址: http://localhost:8050" -ForegroundColor Green
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

& $pythonExe "智能门店看板_Dash版.py"
