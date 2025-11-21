# PostgreSQL 数据库启动脚本
# 适用于端口 8000 的 PostgreSQL 服务

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "PostgreSQL 数据库启动脚本" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# 常见的 PostgreSQL 安装路径
$pgPaths = @(
    "C:\Program Files\PostgreSQL\16\bin",
    "C:\Program Files\PostgreSQL\15\bin",
    "C:\Program Files\PostgreSQL\14\bin",
    "C:\Program Files\PostgreSQL\13\bin",
    "C:\PostgreSQL\16\bin",
    "C:\PostgreSQL\15\bin",
    "D:\PostgreSQL\bin",
    "C:\Program Files (x86)\PostgreSQL\16\bin"
)

# 查找 pg_ctl 和 postgres
$pgCtl = $null
$postgres = $null

foreach ($path in $pgPaths) {
    if (Test-Path "$path\pg_ctl.exe") {
        $pgCtl = "$path\pg_ctl.exe"
        $postgres = "$path\postgres.exe"
        Write-Host "找到 PostgreSQL: $path" -ForegroundColor Green
        break
    }
}

if (-not $pgCtl) {
    Write-Host "未找到 PostgreSQL 安装路径" -ForegroundColor Yellow
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
                Write-Host "指定路径无效" -ForegroundColor Red
                exit 1
            }
        }
        "2" {
            Write-Host "`n检查 PostgreSQL 服务状态..." -ForegroundColor Yellow
            Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue | Format-Table -AutoSize
            Read-Host "`n按回车键退出"
            exit 0
        }
        "3" {
            Write-Host "`n尝试启动所有 PostgreSQL 服务..." -ForegroundColor Yellow
            $services = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
            
            if ($services) {
                foreach ($service in $services) {
                    Write-Host "启动服务: $($service.Name)" -ForegroundColor Cyan
                    try {
                        Start-Service -Name $service.Name -ErrorAction Stop
                        Write-Host "✓ 服务 $($service.Name) 已启动" -ForegroundColor Green
                    } catch {
                        Write-Host "✗ 启动失败: $_" -ForegroundColor Red
                    }
                }
                
                Write-Host "`n服务状态:" -ForegroundColor Yellow
                Get-Service -Name "postgresql*" | Format-Table -AutoSize
                Read-Host "`n按回车键退出"
                exit 0
            } else {
                Write-Host "未找到 PostgreSQL 服务" -ForegroundColor Red
                Read-Host "`n按回车键退出"
                exit 1
            }
        }
        default {
            Write-Host "无效选项" -ForegroundColor Red
            exit 1
        }
    }
}

# 常见的数据目录
$dataDirs = @(
    "C:\Program Files\PostgreSQL\16\data",
    "C:\Program Files\PostgreSQL\15\data",
    "C:\Program Files\PostgreSQL\14\data",
    "C:\PostgreSQL\data",
    "D:\PostgreSQL\data",
    "C:\ProgramData\PostgreSQL\data"
)

$dataDir = $null
foreach ($dir in $dataDirs) {
    if (Test-Path "$dir\postgresql.conf") {
        $dataDir = $dir
        Write-Host "找到数据目录: $dataDir" -ForegroundColor Green
        break
    }
}

if (-not $dataDir) {
    Write-Host "未找到数据目录，请手动指定" -ForegroundColor Yellow
    $dataDir = Read-Host "请输入 PostgreSQL 数据目录路径"
    
    if (-not (Test-Path "$dataDir\postgresql.conf")) {
        Write-Host "指定的数据目录无效" -ForegroundColor Red
        Read-Host "按回车键退出"
        exit 1
    }
}

Write-Host ""
Write-Host "配置信息:" -ForegroundColor Cyan
Write-Host "  PostgreSQL: $pgCtl" -ForegroundColor White
Write-Host "  数据目录: $dataDir" -ForegroundColor White
Write-Host ""

# 检查端口 8000 是否被占用
Write-Host "检查端口 8000..." -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($port8000) {
    Write-Host "端口 8000 已被占用" -ForegroundColor Yellow
    $port8000 | Format-Table -Property State, OwningProcess, RemoteAddress -AutoSize
    
    $kill = Read-Host "`n是否终止占用进程? (y/n)"
    if ($kill -eq "y") {
        foreach ($conn in $port8000) {
            try {
                Stop-Process -Id $conn.OwningProcess -Force
                Write-Host "✓ 已终止进程 $($conn.OwningProcess)" -ForegroundColor Green
            } catch {
                Write-Host "✗ 无法终止进程: $_" -ForegroundColor Red
            }
        }
        Start-Sleep -Seconds 2
    }
}

# 启动数据库
Write-Host ""
Write-Host "正在启动 PostgreSQL..." -ForegroundColor Yellow

try {
    # 使用 pg_ctl 启动
    $startArgs = "start -D `"$dataDir`" -l `"$dataDir\logfile.log`""
    
    Write-Host "执行命令: $pgCtl $startArgs" -ForegroundColor Gray
    
    Start-Process -FilePath $pgCtl -ArgumentList $startArgs -NoNewWindow -Wait
    
    Write-Host ""
    Write-Host "等待数据库启动..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    # 检查状态
    & $pgCtl status -D $dataDir
    
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host "✓ PostgreSQL 启动成功!" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "数据库信息:" -ForegroundColor Cyan
    Write-Host "  主机: localhost" -ForegroundColor White
    Write-Host "  端口: 8000 (如已配置)" -ForegroundColor White
    Write-Host "  日志: $dataDir\logfile.log" -ForegroundColor White
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
