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

# ========== 自动检查并启动 PostgreSQL 数据库 ==========
Write-Host ""
Write-Host "🔍 检查 PostgreSQL 数据库..." -ForegroundColor Yellow

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

# 检查数据库连接
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
    Write-Host "⚠️  PostgreSQL 数据库未连接，正在尝试自动启动..." -ForegroundColor Yellow
    
    # 调用自动启动脚本
    try {
        . "$scriptDir\自动启动PostgreSQL.ps1"
        $startResult = Start-PostgreSQLAuto -Silent
        
        if ($startResult) {
            # 等待数据库完全启动（重试3次）
            $connected = $false
            for ($i = 1; $i -le 3; $i++) {
                Start-Sleep -Seconds 2
                $pgResult2 = & $pythonExe -c $pgCheckScript 2>&1
                if ($pgResult2 -eq "OK") {
                    Write-Host "✅ PostgreSQL 已成功启动并连接" -ForegroundColor Green
                    $connected = $true
                    break
                }
                if ($i -lt 3) {
                    Write-Host "   等待数据库就绪... (尝试 $i/3)" -ForegroundColor Cyan
                }
            }
            
            if (-not $connected) {
                Write-Host "⚠️  PostgreSQL 已启动，但连接仍失败" -ForegroundColor Yellow
                Write-Host "   提示: 数据库可能还在启动中，看板将继续启动" -ForegroundColor Gray
            }
        } else {
            Write-Host "❌ PostgreSQL 自动启动失败" -ForegroundColor Red
            Write-Host "   提示: 请手动运行 .\启动数据库.ps1" -ForegroundColor Gray
        }
    } catch {
        Write-Host "❌ 自动启动脚本执行失败: $_" -ForegroundColor Red
        Write-Host "   提示: 请手动运行 .\启动数据库.ps1" -ForegroundColor Gray
    }
} else {
    Write-Host "⚠️  PostgreSQL 数据库状态未知" -ForegroundColor Yellow
}

Write-Host ""

# ========== V8.9: 启动自检（可选，如遇到问题可注释掉）==========
# Write-Host "🔍 运行系统自检..." -ForegroundColor Yellow
# Write-Host ""
# & $pythonExe "简易启动自检.py"
# $checkExitCode = $LASTEXITCODE
# Write-Host ""
# if ($checkExitCode -eq 0) {
#     Write-Host "✅ 系统自检通过" -ForegroundColor Green
# } else {
#     Write-Host "⚠️  系统自检发现问题" -ForegroundColor Yellow
# }
# Write-Host ""
Write-Host "💡 提示: 如需查看详细调试日志，请使用:" -ForegroundColor Gray
Write-Host "   .\启动看板-调试模式.ps1" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔍 检测已有看板进程..." -ForegroundColor Yellow
# 查找所有Python进程(包括python.exe, python3.exe, python3.11.exe等)
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
    Write-Host "⚠️  发现 $($dashboardProcs.Count) 个运行中的看板实例,正在清理..." -ForegroundColor Yellow
    foreach ($proc in $dashboardProcs) {
        Write-Host "   停止进程 PID=$($proc.Id) (内存: $([math]::Round($proc.WS/1MB,2))MB)" -ForegroundColor DarkYellow
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
    Write-Host "✅ 旧进程已清理" -ForegroundColor Green
} else {
    Write-Host "✅ 未发现运行中的看板实例" -ForegroundColor Green
}

Write-Host ""
Write-Host "🚀 正在启动应用..." -ForegroundColor Yellow
Write-Host "📍 访问地址: http://localhost:8051" -ForegroundColor Green
Write-Host "🌐 局域网访问: http://192.168.1.213:8051" -ForegroundColor Green
Write-Host "⚠️  按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

# 启动应用 (添加错误处理)
try {
    # 添加 -u 参数强制无缓冲输出，确保日志实时显示
    & $pythonExe -u "智能门店看板_Dash版.py"
} catch {
    Write-Host ""
    Write-Host "❌ 启动失败: $_" -ForegroundColor Red
    Write-Host "   提示: 使用 .\生产环境启动.ps1 获取详细检查" -ForegroundColor Gray
    Read-Host "按回车键退出"
    exit 1
}
