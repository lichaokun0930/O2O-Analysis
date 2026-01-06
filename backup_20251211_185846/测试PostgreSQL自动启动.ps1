# 测试PostgreSQL自动启动功能

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "PostgreSQL 自动启动功能测试" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# 步骤1: 确保PostgreSQL已停止
Write-Host "[1/4] 停止现有PostgreSQL进程..." -ForegroundColor Yellow
$existingProcs = Get-Process postgres -ErrorAction SilentlyContinue
if ($existingProcs) {
    Write-Host "   发现 $($existingProcs.Count) 个进程，正在停止..." -ForegroundColor Cyan
    $existingProcs | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-Host "   ✅ 已停止" -ForegroundColor Green
} else {
    Write-Host "   ✅ 没有运行中的进程" -ForegroundColor Green
}

Write-Host ""

# 步骤2: 测试自动启动脚本
Write-Host "[2/4] 测试自动启动脚本..." -ForegroundColor Yellow

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
. "$scriptDir\自动启动PostgreSQL.ps1"

$startResult = Start-PostgreSQLAuto

if ($startResult) {
    Write-Host "   ✅ 自动启动成功" -ForegroundColor Green
} else {
    Write-Host "   ❌ 自动启动失败" -ForegroundColor Red
    Read-Host "`n按回车键退出"
    exit 1
}

Write-Host ""

# 步骤3: 验证进程
Write-Host "[3/4] 验证PostgreSQL进程..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
$pgProcs = Get-Process postgres -ErrorAction SilentlyContinue
if ($pgProcs) {
    Write-Host "   ✅ 发现 $($pgProcs.Count) 个进程" -ForegroundColor Green
    $pgProcs | Select-Object Id, ProcessName, StartTime | Format-Table -AutoSize
} else {
    Write-Host "   ❌ 未发现进程" -ForegroundColor Red
    Read-Host "`n按回车键退出"
    exit 1
}

Write-Host ""

# 步骤4: 测试数据库连接（带重试）
Write-Host "[4/4] 测试数据库连接..." -ForegroundColor Yellow

$parentDir = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $parentDir ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"
}
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
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

# 重试最多3次
$maxRetries = 3
$pgResult = $null
for ($i = 1; $i -le $maxRetries; $i++) {
    if ($i -gt 1) {
        Write-Host "   等待数据库就绪... (尝试 $i/$maxRetries)" -ForegroundColor Cyan
        Start-Sleep -Seconds 3
    }
    
    $pgResult = & $pythonExe -c $pgCheckScript 2>&1
    if ($pgResult -eq "OK") {
        Write-Host "   ✅ 数据库连接成功" -ForegroundColor Green
        break
    }
}

if ($pgResult -ne "OK") {
    Write-Host "   ⚠️  数据库连接失败（已重试$maxRetries次）" -ForegroundColor Yellow
    Write-Host "   提示: 数据库可能还在启动中，请稍后再试" -ForegroundColor Gray
}

Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

if ($pgResult -eq "OK") {
    Write-Host "✅ PostgreSQL 自动启动功能正常工作！" -ForegroundColor Green
} else {
    Write-Host "⚠️  PostgreSQL 已启动，但数据库连接失败" -ForegroundColor Yellow
    Write-Host "   可能需要检查数据库配置" -ForegroundColor Gray
}

Write-Host ""
Read-Host "按回车键退出"
