# 生产环境启动脚本 - 稳定版
# 适用于Windows生产环境，确保可靠启动

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "智能门店经营看板 - 生产环境启动" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# ========== 1. 清理旧进程 ==========
Write-Host "🔍 [步骤1/5] 清理旧的看板进程..." -ForegroundColor Yellow
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
        Write-Host "   停止进程 PID=$($proc.Id) (内存: $([math]::Round($proc.WS/1MB,2))MB)" -ForegroundColor DarkYellow
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    Write-Host "   ✅ 旧进程已清理" -ForegroundColor Green
} else {
    Write-Host "   ✅ 无需清理" -ForegroundColor Green
}

# ========== 2. 检查虚拟环境 ==========
Write-Host ""
Write-Host "🔍 [步骤2/5] 检查虚拟环境..." -ForegroundColor Yellow
$parentDir = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $parentDir ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    $pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"
}

if (-not (Test-Path $pythonExe)) {
    Write-Host "   ❌ 未找到虚拟环境" -ForegroundColor Red
    Write-Host "   请运行: python -m venv .venv" -ForegroundColor Gray
    Read-Host "按回车键退出"
    exit 1
}

Write-Host "   ✅ 虚拟环境: $pythonExe" -ForegroundColor Green

# ========== 3. 检查Redis服务 ==========
Write-Host ""
Write-Host "🔍 [步骤3/5] 检查 Redis 服务..." -ForegroundColor Yellow
$memuraiService = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue

if ($memuraiService) {
    if ($memuraiService.Status -ne "Running") {
        Write-Host "   启动 Memurai Redis..." -ForegroundColor Yellow
        try {
            Start-Service -Name "Memurai" -ErrorAction Stop
            Start-Sleep -Seconds 2
            Write-Host "   ✅ Redis 服务已启动" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  Redis 启动失败(需管理员权限)，缓存功能将降级" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ✅ Redis 服务正在运行" -ForegroundColor Green
    }
} else {
    Write-Host "   ⚠️  未检测到 Memurai，缓存功能将降级" -ForegroundColor Yellow
}

# ========== 4. 检查PostgreSQL数据库 ==========
Write-Host ""
Write-Host "🔍 [步骤4/5] 检查 PostgreSQL 数据库..." -ForegroundColor Yellow

$pgCheckScript = @'
import sys
try:
    from database.connection import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1')).fetchone()
        print('OK' if result else 'FAIL')
except Exception as e:
    print('ERROR:' + str(e))
'@

$pgResult = & $pythonExe -c $pgCheckScript 2>&1
if ($pgResult -eq "OK") {
    Write-Host "   ✅ PostgreSQL 连接正常" -ForegroundColor Green
} elseif ($pgResult -like "ERROR:*") {
    $errorMsg = $pgResult -replace "ERROR:", ""
    Write-Host "   ❌ PostgreSQL 连接失败: $errorMsg" -ForegroundColor Red
    Write-Host "   提示: 请运行 .\启动数据库.ps1 或检查数据库服务" -ForegroundColor Gray
    Write-Host ""
    $continue = Read-Host "是否继续启动? (Y/N)"
    if ($continue -ne "Y" -and $continue -ne "y") {
        exit 1
    }
} else {
    Write-Host "   ⚠️  数据库状态未知" -ForegroundColor Yellow
}

# ========== 5. 启动应用 ==========
Write-Host ""
Write-Host "🚀 [步骤5/5] 启动应用服务器..." -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 本机访问: http://localhost:8051" -ForegroundColor Green
Write-Host "🌐 局域网访问: http://192.168.1.213:8051" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# 启动应用
try {
    & $pythonExe "智能门店看板_Dash版.py"
} catch {
    Write-Host ""
    Write-Host "❌ 应用启动失败: $_" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}
