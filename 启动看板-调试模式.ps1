# 智能门店经营看板 - 调试模式启动脚本

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "智能门店经营看板 - 调试模式" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# ========== 检查并启动 Memurai Redis 服务 ==========
Write-Host "🔍 检查 Memurai Redis 服务..." -ForegroundColor Yellow
$memuraiService = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue

if ($memuraiService) {
    if ($memuraiService.Status -ne "Running") {
        Write-Host "⚠️  Memurai 服务未运行，正在启动..." -ForegroundColor Yellow
        try {
            Start-Service -Name "Memurai" -ErrorAction Stop
            Start-Sleep -Seconds 2
            Write-Host "✅ Memurai Redis 服务已启动" -ForegroundColor Green
        } catch {
            Write-Host "🔐 需要管理员权限，正在请求..." -ForegroundColor Cyan
            Start-Process powershell -ArgumentList "-Command", "Start-Service -Name 'Memurai'" -Verb RunAs -Wait
            Start-Sleep -Seconds 2
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

# ========== 检查并停止已有看板进程 ==========
Write-Host "🔍 检测已有看板进程..." -ForegroundColor Yellow
$allPythonProcs = Get-Process python* -ErrorAction SilentlyContinue
$dashboardProcs = @()

foreach ($proc in $allPythonProcs) {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.Id)").CommandLine
        if ($cmdLine -match "智能门店看板_Dash版\.py") {
            $dashboardProcs += $proc
        }
    } catch { }
}

if ($dashboardProcs.Count -gt 0) {
    Write-Host "   发现 $($dashboardProcs.Count) 个旧进程，正在清理..." -ForegroundColor Yellow
    foreach ($proc in $dashboardProcs) {
        Write-Host "   停止进程 PID=$($proc.Id)" -ForegroundColor DarkYellow
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    Write-Host "   ✅ 旧进程已清理" -ForegroundColor Green
} else {
    Write-Host "   ✅ 无需清理" -ForegroundColor Green
}

Write-Host ""
Write-Host "🐛 启动调试模式..." -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "📍 本机访问: http://localhost:8051" -ForegroundColor Green
Write-Host "🌐 局域网访问: http://192.168.1.213:8051" -ForegroundColor Green
Write-Host ""
Write-Host "💡 特性:" -ForegroundColor Cyan
Write-Host "   - 自动重载: 代码修改后自动重启" -ForegroundColor Gray
Write-Host "   - 详细日志: 显示所有调试信息" -ForegroundColor Gray
Write-Host "   - 错误追踪: 完整的堆栈跟踪" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

try {
    $env:DASH_DEBUG = "true"
    & $pythonExe "智能门店看板_Dash版.py"
} catch {
    Write-Host ""
    Write-Host "❌ 调试模式启动失败: $_" -ForegroundColor Red
    Read-Host "按回车键退出"
} finally {
    Remove-Item Env:DASH_DEBUG -ErrorAction SilentlyContinue
}
