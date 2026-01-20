# PostgreSQL 修复和启动脚本

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "PostgreSQL 数据库修复和启动" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan

$pgBin = "D:\PostgreSQL\bin"
$pgData = "D:\PostgreSQL\data"

# 1. 检查PostgreSQL是否已安装
if (-not (Test-Path "$pgBin\postgres.exe")) {
    Write-Host "❌ PostgreSQL未安装在 D:\PostgreSQL" -ForegroundColor Red
    Write-Host "请先运行安装脚本或手动安装PostgreSQL" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n✅ PostgreSQL已安装" -ForegroundColor Green

# 2. 停止所有PostgreSQL进程
Write-Host "`n🔍 检查现有PostgreSQL进程..." -ForegroundColor Yellow
$pgProcesses = Get-Process | Where-Object {$_.ProcessName -match "postgres"}
if ($pgProcesses) {
    Write-Host "发现 $($pgProcesses.Count) 个PostgreSQL进程，正在停止..." -ForegroundColor Yellow
    $pgProcesses | ForEach-Object {
        Write-Host "  停止进程: PID $($_.Id)" -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 3
    Write-Host "✅ 进程已停止" -ForegroundColor Green
} else {
    Write-Host "✅ 没有运行中的PostgreSQL进程" -ForegroundColor Green
}

# 3. 清理锁文件
Write-Host "`n🔧 清理锁文件..." -ForegroundColor Yellow
$lockFiles = @(
    "$pgData\postmaster.pid",
    "$pgData\postmaster.opts"
)

foreach ($lockFile in $lockFiles) {
    if (Test-Path $lockFile) {
        try {
            Remove-Item $lockFile -Force -ErrorAction Stop
            Write-Host "  ✓ 删除: $(Split-Path $lockFile -Leaf)" -ForegroundColor Gray
        } catch {
            Write-Host "  ✗ 无法删除: $(Split-Path $lockFile -Leaf) - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# 4. 检查端口占用
Write-Host "`n🔍 检查端口5432..." -ForegroundColor Yellow
$port5432 = netstat -ano | Select-String ":5432"
if ($port5432) {
    Write-Host "⚠️  端口5432被占用:" -ForegroundColor Yellow
    $port5432 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    
    # 尝试找到占用进程
    $pidMatch = $port5432 | Select-String "LISTENING\s+(\d+)" -AllMatches
    if ($pidMatch) {
        $pid = $pidMatch.Matches[0].Groups[1].Value
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  占用进程: $($process.ProcessName) (PID: $pid)" -ForegroundColor Red
            $response = Read-Host "是否终止该进程? (y/n)"
            if ($response -eq 'y') {
                Stop-Process -Id $pid -Force
                Start-Sleep -Seconds 2
                Write-Host "  ✓ 进程已终止" -ForegroundColor Green
            }
        }
    }
} else {
    Write-Host "✅ 端口5432未被占用" -ForegroundColor Green
}

# 5. 检查数据目录
Write-Host "`n🔍 检查数据目录..." -ForegroundColor Yellow
if (-not (Test-Path $pgData)) {
    Write-Host "❌ 数据目录不存在: $pgData" -ForegroundColor Red
    Write-Host "正在初始化数据库..." -ForegroundColor Yellow
    
    # 初始化数据库
    & "$pgBin\initdb.exe" -D $pgData -U postgres -E UTF8 --locale=C
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 数据库初始化成功" -ForegroundColor Green
    } else {
        Write-Host "❌ 数据库初始化失败" -ForegroundColor Red
        exit 1
    }
} else {
    # 检查关键文件
    $requiredFiles = @("postgresql.conf", "pg_hba.conf", "PG_VERSION")
    $missing = @()
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path "$pgData\$file")) {
            $missing += $file
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-Host "⚠️  缺少关键文件: $($missing -join ', ')" -ForegroundColor Yellow
        Write-Host "建议重新初始化数据库" -ForegroundColor Yellow
    } else {
        Write-Host "✅ 数据目录完整" -ForegroundColor Green
    }
}

# 6. 启动PostgreSQL
Write-Host "`n🚀 正在启动PostgreSQL..." -ForegroundColor Cyan
Write-Host "   命令: pg_ctl start -D `"$pgData`" -l `"$pgData\logfile.log`"" -ForegroundColor Gray

try {
    & "$pgBin\pg_ctl.exe" start -D $pgData -l "$pgData\logfile.log" -w -t 10
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ PostgreSQL启动成功!" -ForegroundColor Green
        Write-Host "   监听端口: 5432" -ForegroundColor Gray
        Write-Host "   数据目录: $pgData" -ForegroundColor Gray
        
        # 测试连接
        Start-Sleep -Seconds 2
        Write-Host "`n🔍 测试数据库连接..." -ForegroundColor Yellow
        & "$pgBin\psql.exe" -U postgres -c "SELECT version();" 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 数据库连接正常" -ForegroundColor Green
        } else {
            Write-Host "⚠️  数据库连接测试失败" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n❌ PostgreSQL启动失败!" -ForegroundColor Red
        Write-Host "`n查看日志:" -ForegroundColor Yellow
        if (Test-Path "$pgData\logfile.log") {
            Get-Content "$pgData\logfile.log" -Tail 20 -ErrorAction SilentlyContinue
        }
        
        # 查看log目录中的最新日志
        $logDir = "$pgData\log"
        if (Test-Path $logDir) {
            $latestLog = Get-ChildItem $logDir | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            if ($latestLog) {
                Write-Host "`n最新日志 ($($latestLog.Name)):" -ForegroundColor Yellow
                Get-Content $latestLog.FullName -Tail 20 -ErrorAction SilentlyContinue
            }
        }
    }
} catch {
    Write-Host "`n❌ 启动过程出错: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n===========================================" -ForegroundColor Cyan
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
