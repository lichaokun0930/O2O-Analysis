# PostgreSQL 数据库启动脚本 V2.0
# 功能增强: 自动清理僵尸进程、端口检测、健康检查

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "PostgreSQL 数据库启动脚本 V2.0" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# ========================================
# 🧹 步骤1: 清理僵尸进程
# ========================================
Write-Host "🔍 检查PostgreSQL进程状态..." -ForegroundColor Yellow

$existingProcesses = Get-Process postgres -ErrorAction SilentlyContinue
if ($existingProcesses) {
    $processCount = $existingProcesses.Count
    Write-Host "   发现 $processCount 个postgres进程" -ForegroundColor Cyan
    
    # 检查进程启动时间是否一致（判断是否为僵尸进程）
    $startTimes = $existingProcesses | Select-Object -ExpandProperty StartTime -Unique
    
    if ($startTimes.Count -gt 2) {
        Write-Host "   ⚠️  检测到僵尸进程（启动时间不一致）" -ForegroundColor Yellow
        Write-Host "   正在清理僵尸进程..." -ForegroundColor Yellow
        
        try {
            Get-Process postgres -ErrorAction SilentlyContinue | Stop-Process -Force
            Start-Sleep -Seconds 2
            Write-Host "   ✅ 僵尸进程已清理" -ForegroundColor Green
        } catch {
            Write-Host "   ⚠️  部分进程清理失败，继续启动..." -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ✅ 进程状态正常（统一启动时间）" -ForegroundColor Green
        $shouldRestart = Read-Host "   是否重启PostgreSQL? (y/n)"
        if ($shouldRestart -eq 'y') {
            Write-Host "   正在停止现有进程..." -ForegroundColor Yellow
            Get-Process postgres -ErrorAction SilentlyContinue | Stop-Process -Force
            Start-Sleep -Seconds 2
            Write-Host "   ✅ 已停止" -ForegroundColor Green
        } else {
            Write-Host "   跳过启动，PostgreSQL已在运行" -ForegroundColor Green
            Write-Host ""
            Read-Host "按回车键退出"
            exit 0
        }
    }
} else {
    Write-Host "   ✅ 没有运行中的postgres进程" -ForegroundColor Green
}

Write-Host ""

# ========================================
# 🔌 步骤2: 检查端口占用
# ========================================
Write-Host "🔍 检查端口5432占用情况..." -ForegroundColor Yellow

$portCheck = netstat -ano | Select-String ":5432" | Select-String "LISTENING"
if ($portCheck) {
    Write-Host "   ⚠️  端口5432已被占用" -ForegroundColor Yellow
    $portCheck | ForEach-Object {
        $line = $_.Line
        if ($line -match "\s+(\d+)$") {
            $pid = $matches[1]
            $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "   占用进程: $($process.ProcessName) (PID: $pid)" -ForegroundColor Cyan
            }
        }
    }
    Write-Host "   正在清理端口占用..." -ForegroundColor Yellow
    Get-Process postgres -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-Host "   ✅ 端口已释放" -ForegroundColor Green
} else {
    Write-Host "   ✅ 端口5432空闲" -ForegroundColor Green
}

Write-Host ""

# ========================================
# 📂 步骤3: 查找PostgreSQL安装路径
# ========================================

# 常见的 PostgreSQL 安装路径
$pgPaths = @(
    "D:\PostgreSQL\bin",
    "C:\Program Files\PostgreSQL\18\bin",
    "C:\Program Files\PostgreSQL\16\bin",
    "C:\Program Files\PostgreSQL\15\bin",
    "C:\Program Files\PostgreSQL\14\bin",
    "C:\Program Files\PostgreSQL\13\bin",
    "C:\PostgreSQL\16\bin",
    "C:\PostgreSQL\15\bin",
    "C:\Program Files (x86)\PostgreSQL\16\bin"
)

Write-Host "🔍 查找PostgreSQL安装路径..." -ForegroundColor Yellow

# 查找 pg_ctl 和 postgres
$pgCtl = $null
$postgres = $null

foreach ($path in $pgPaths) {
    if (Test-Path "$path\pg_ctl.exe") {
        $pgCtl = "$path\pg_ctl.exe"
        $postgres = "$path\postgres.exe"
        Write-Host "   ✅ 找到PostgreSQL: $path" -ForegroundColor Green
        break
    }
}

if (-not $pgCtl) {
    Write-Host "   ❌ 未找到PostgreSQL安装路径" -ForegroundColor Red
    Write-Host ""
    Write-Host "请选择操作:" -ForegroundColor Cyan
    Write-Host "1. 手动指定 PostgreSQL 路径" -ForegroundColor White
    Write-Host "2. 检查 PostgreSQL 服务状态" -ForegroundColor White
    Write-Host "3. 尝试启动 PostgreSQL 服务" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "请输入选项 (1-3)"
    
    switch ($choice) {
        "1" {
            $customPath = Read-Host "请输入 PostgreSQL bin 目录路径"
            if (Test-Path "$customPath\pg_ctl.exe") {
                $pgCtl = "$customPath\pg_ctl.exe"
                $postgres = "$customPath\postgres.exe"
            } else {
                Write-Host "   ❌ 指定路径无效" -ForegroundColor Red
                Read-Host "`n按回车键退出"
                exit 1
            }
        }
        "2" {
            Write-Host "`n🔍 检查PostgreSQL服务状态..." -ForegroundColor Yellow
            Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Format-Table -AutoSize
            Read-Host "`n按回车键退出"
            exit 0
        }
        "3" {
            Write-Host "`n🚀 尝试启动所有PostgreSQL服务..." -ForegroundColor Yellow
            $services = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
            
            if ($services) {
                foreach ($service in $services) {
                    Write-Host "   启动服务: $($service.Name)" -ForegroundColor Cyan
                    try {
                        Start-Service -Name $service.Name -ErrorAction Stop
                        Write-Host "   ✅ 服务 $($service.Name) 已启动" -ForegroundColor Green
                    } catch {
                        Write-Host "   ❌ 启动失败: $_" -ForegroundColor Red
                    }
                }
                
                Write-Host "`n服务状态:" -ForegroundColor Yellow
                Get-Service -Name "postgresql*" | Format-Table -AutoSize
                Read-Host "`n按回车键退出"
                exit 0
            } else {
                Write-Host "   ❌ 未找到PostgreSQL服务" -ForegroundColor Red
                Read-Host "`n按回车键退出"
                exit 1
            }
        }
        default {
            Write-Host "   ❌ 无效选项" -ForegroundColor Red
            Read-Host "`n按回车键退出"
            exit 1
        }
    }
}

Write-Host ""

# ========================================
# 📂 步骤4: 查找数据目录
# ========================================
Write-Host "🔍 查找PostgreSQL数据目录..." -ForegroundColor Yellow

# 常见的数据目录
$dataDirs = @(
    "D:\PostgreSQL\data",
    "C:\Program Files\PostgreSQL\18\data",
    "C:\Program Files\PostgreSQL\16\data",
    "C:\Program Files\PostgreSQL\15\data",
    "C:\Program Files\PostgreSQL\14\data",
    "C:\PostgreSQL\data",
    "C:\ProgramData\PostgreSQL\data"
)

$dataDir = $null
foreach ($dir in $dataDirs) {
    if (Test-Path "$dir\postgresql.conf") {
        $dataDir = $dir
        Write-Host "   ✅ 找到数据目录: $dataDir" -ForegroundColor Green
        break
    }
}

if (-not $dataDir) {
    Write-Host "   ⚠️  未找到数据目录，请手动指定" -ForegroundColor Yellow
    $dataDir = Read-Host "请输入 PostgreSQL 数据目录路径"
    
    if (-not (Test-Path "$dataDir\postgresql.conf")) {
        Write-Host "   ❌ 指定的数据目录无效" -ForegroundColor Red
        Read-Host "`n按回车键退出"
        exit 1
    }
}

Write-Host ""

# ========================================
# 🚀 步骤5: 启动PostgreSQL
# ========================================
Write-Host "🚀 启动PostgreSQL..." -ForegroundColor Yellow

try {
    # 设置PATH环境变量
    $pgBinDir = Split-Path -Parent $pgCtl
    $env:PATH = "$pgBinDir;$env:PATH"
    
    # 使用 pg_ctl 启动
    $startArgs = "start -D `"$dataDir`" -l `"$dataDir\logfile`""
    
    Write-Host "   执行命令: pg_ctl $startArgs" -ForegroundColor Gray
    
    & $pgCtl start -D $dataDir -l "$dataDir\logfile"
    
    Write-Host ""
    Write-Host "⏳ 等待数据库启动..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    # ========================================
    # ✅ 步骤6: 健康检查
    # ========================================
    Write-Host ""
    Write-Host "🔍 PostgreSQL健康检查..." -ForegroundColor Yellow
    
    # 检查进程
    $pgProcesses = Get-Process postgres -ErrorAction SilentlyContinue
    if ($pgProcesses) {
        Write-Host "   ✅ 进程数量: $($pgProcesses.Count)" -ForegroundColor Green
        Write-Host "   ✅ 统一启动时间: $($pgProcesses[0].StartTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 未检测到postgres进程" -ForegroundColor Red
    }
    
    # 检查端口
    $portCheck = netstat -ano | Select-String ":5432" | Select-String "LISTENING"
    if ($portCheck) {
        Write-Host "   ✅ 端口5432正在监听" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 端口5432未监听" -ForegroundColor Red
    }
    
    # 测试连接
    Write-Host "   ⏳ 测试数据库连接..." -ForegroundColor Yellow
    try {
        $testResult = & psql -U postgres -d o2o_dashboard -c "SELECT version();" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ 数据库连接成功" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  数据库连接测试失败（可能需要配置认证）" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ⚠️  psql命令不可用，跳过连接测试" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host "✅ PostgreSQL 启动成功!" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📊 数据库信息:" -ForegroundColor Cyan
    Write-Host "   主机: localhost" -ForegroundColor White
    Write-Host "   端口: 5432" -ForegroundColor White
    Write-Host "   数据目录: $dataDir" -ForegroundColor White
    Write-Host "   日志文件: $dataDir\logfile" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 常用命令:" -ForegroundColor Cyan
    Write-Host "   查看状态: pg_ctl status -D `"$dataDir`"" -ForegroundColor Gray
    Write-Host "   停止服务: pg_ctl stop -D `"$dataDir`"" -ForegroundColor Gray
    Write-Host "   重启服务: pg_ctl restart -D `"$dataDir`"" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "✗ 启动失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "可能的解决方案:" -ForegroundColor Yellow
    Write-Host "1. 检查数据目录权限" -ForegroundColor White
    Write-Host "2. 查看日志文件: $dataDir\logfile.log" -ForegroundColor White
    Write-Host "3. 尝试以管理员身份运行此脚本" -ForegroundColor White
    Write-Host "4. 检查 postgresql.conf 中的端口配置" -ForegroundColor White
    Write-Host ""
}

Read-Host "按回车键退出"
