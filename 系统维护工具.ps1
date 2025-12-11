# ============================================
# 系统维护工具菜单 V1.0
# 集成: 数据库管理、进程清理、看板启动
# ============================================

function Show-Menu {
    Clear-Host
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "     系统维护工具菜单 V1.0" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📊 数据库管理:" -ForegroundColor Yellow
    Write-Host "  1. 启动PostgreSQL数据库" -ForegroundColor White
    Write-Host "  2. 停止PostgreSQL数据库" -ForegroundColor White
    Write-Host "  3. 重启PostgreSQL数据库" -ForegroundColor White
    Write-Host "  4. 查看PostgreSQL状态" -ForegroundColor White
    Write-Host ""
    Write-Host "🧹 进程清理:" -ForegroundColor Yellow
    Write-Host "  5. 清理VS Code进程" -ForegroundColor White
    Write-Host "  6. 清理Python进程" -ForegroundColor White
    Write-Host "  7. 清理所有开发进程" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 看板管理:" -ForegroundColor Yellow
    Write-Host "  8. 启动看板（生产环境）" -ForegroundColor White
    Write-Host "  9. 启动看板（调试模式）" -ForegroundColor White
    Write-Host "  10. 停止看板" -ForegroundColor White
    Write-Host ""
    Write-Host "🛠️  数据工具:" -ForegroundColor Yellow
    Write-Host "  11. 导出数据库表结构" -ForegroundColor White
    Write-Host "  12. 启动Redis缓存" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 系统信息:" -ForegroundColor Yellow
    Write-Host "  13. 查看系统资源使用" -ForegroundColor White
    Write-Host "  14. 查看端口占用情况" -ForegroundColor White
    Write-Host ""
    Write-Host "  0. 退出" -ForegroundColor Red
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
}

function Start-PostgreSQL {
    Write-Host "`n🚀 启动PostgreSQL..." -ForegroundColor Yellow
    & ".\启动数据库.ps1"
}

function Stop-PostgreSQL {
    Write-Host "`n🛑 停止PostgreSQL..." -ForegroundColor Yellow
    
    $pgProcesses = Get-Process postgres -ErrorAction SilentlyContinue
    if ($pgProcesses) {
        Write-Host "   发现 $($pgProcesses.Count) 个postgres进程" -ForegroundColor Cyan
        $confirm = Read-Host "   确认停止? (y/n)"
        if ($confirm -eq 'y') {
            Get-Process postgres | Stop-Process -Force
            Start-Sleep -Seconds 2
            Write-Host "   ✅ PostgreSQL已停止" -ForegroundColor Green
        }
    } else {
        Write-Host "   ✅ PostgreSQL未在运行" -ForegroundColor Green
    }
    
    Read-Host "`n按回车键返回主菜单"
}

function Restart-PostgreSQL {
    Write-Host "`n🔄 重启PostgreSQL..." -ForegroundColor Yellow
    
    Write-Host "   1️⃣ 停止服务..." -ForegroundColor Cyan
    Get-Process postgres -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-Host "   ✅ 已停止" -ForegroundColor Green
    
    Write-Host "`n   2️⃣ 启动服务..." -ForegroundColor Cyan
    & ".\启动数据库.ps1"
}

function Show-PostgreSQLStatus {
    Write-Host "`n📊 PostgreSQL状态检查..." -ForegroundColor Yellow
    Write-Host ""
    
    # 检查进程
    $pgProcesses = Get-Process postgres -ErrorAction SilentlyContinue
    if ($pgProcesses) {
        Write-Host "✅ 进程状态: 运行中" -ForegroundColor Green
        Write-Host "   进程数量: $($pgProcesses.Count)" -ForegroundColor White
        Write-Host "   启动时间: $($pgProcesses[0].StartTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White
        $memoryMB = [math]::Round(($pgProcesses | Measure-Object WorkingSet -Sum).Sum / 1MB, 2)
        Write-Host "   内存使用: $memoryMB MB" -ForegroundColor White
    } else {
        Write-Host "❌ 进程状态: 未运行" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # 检查端口
    $portCheck = netstat -ano | Select-String ":5432" | Select-String "LISTENING"
    if ($portCheck) {
        Write-Host "✅ 端口状态: 5432正在监听" -ForegroundColor Green
    } else {
        Write-Host "❌ 端口状态: 5432未监听" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # 测试连接 - 查找psql路径
    Write-Host "⏳ 测试数据库连接..." -ForegroundColor Yellow
    
    # 尝试查找psql
    $psqlPaths = @(
        "D:\PostgreSQL\bin\psql.exe",
        "C:\Program Files\PostgreSQL\18\bin\psql.exe",
        "C:\Program Files\PostgreSQL\16\bin\psql.exe",
        "C:\Program Files\PostgreSQL\15\bin\psql.exe",
        "C:\PostgreSQL\bin\psql.exe"
    )
    
    $psqlExe = $null
    foreach ($path in $psqlPaths) {
        if (Test-Path $path) {
            $psqlExe = $path
            break
        }
    }
    
    if ($psqlExe) {
        try {
            $env:PGPASSWORD = "308352588"  # 临时设置密码环境变量
            $testResult = & $psqlExe -U postgres -d o2o_dashboard -c "SELECT 'Orders表: ' || COUNT(*) || ' 行' FROM orders;" -t 2>&1
            $env:PGPASSWORD = $null  # 清除密码
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ 数据库连接: 正常" -ForegroundColor Green
                Write-Host "   $($testResult.Trim())" -ForegroundColor Cyan
                
                # 额外查询数据库版本
                $env:PGPASSWORD = "308352588"
                $versionResult = & $psqlExe -U postgres -d o2o_dashboard -c "SELECT version();" -t 2>&1
                $env:PGPASSWORD = $null
                
                if ($LASTEXITCODE -eq 0) {
                    $version = ($versionResult -split ',')[0].Trim()
                    Write-Host "   $version" -ForegroundColor Gray
                }
            } else {
                Write-Host "⚠️  数据库连接失败" -ForegroundColor Yellow
                Write-Host "   错误: $testResult" -ForegroundColor Gray
            }
        } catch {
            Write-Host "⚠️  连接测试失败: $_" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  psql命令不可用（未找到psql.exe）" -ForegroundColor Yellow
        Write-Host "   💡 PostgreSQL进程和端口正常，数据库应该可以正常使用" -ForegroundColor Cyan
    }
    
    Read-Host "`n按回车键返回主菜单"
}

function Clear-VSCodeProcesses {
    Write-Host "`n🧹 清理VS Code进程..." -ForegroundColor Yellow
    & ".\清理VSCode进程.ps1"
}

function Clear-PythonProcesses {
    Write-Host "`n🧹 清理Python进程..." -ForegroundColor Yellow
    
    $pythonProcesses = Get-Process python* -ErrorAction SilentlyContinue
    if ($pythonProcesses) {
        Write-Host "   发现 $($pythonProcesses.Count) 个Python进程" -ForegroundColor Cyan
        $memoryMB = [math]::Round(($pythonProcesses | Measure-Object WorkingSet -Sum).Sum / 1MB, 2)
        Write-Host "   内存使用: $memoryMB MB" -ForegroundColor White
        Write-Host ""
        
        $confirm = Read-Host "   确认清理? (y/n)"
        if ($confirm -eq 'y') {
            Get-Process python* | Stop-Process -Force
            Start-Sleep -Seconds 2
            Write-Host "   ✅ Python进程已清理" -ForegroundColor Green
        }
    } else {
        Write-Host "   ✅ 没有运行中的Python进程" -ForegroundColor Green
    }
    
    Read-Host "`n按回车键返回主菜单"
}

function Clear-AllDevProcesses {
    Write-Host "`n🧹 清理所有开发进程..." -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "将清理以下进程:" -ForegroundColor Cyan
    Write-Host "  - VS Code (Code*)" -ForegroundColor White
    Write-Host "  - Python (python*)" -ForegroundColor White
    Write-Host "  - Node.js (node*)" -ForegroundColor White
    Write-Host ""
    
    $confirm = Read-Host "确认清理所有开发进程? (y/n)"
    if ($confirm -eq 'y') {
        Write-Host ""
        
        # VS Code
        $codeCount = (Get-Process Code* -ErrorAction SilentlyContinue).Count
        if ($codeCount -gt 0) {
            Get-Process Code* | Stop-Process -Force -ErrorAction SilentlyContinue
            Write-Host "   ✅ 清理 $codeCount 个VS Code进程" -ForegroundColor Green
        }
        
        # Python
        $pythonCount = (Get-Process python* -ErrorAction SilentlyContinue).Count
        if ($pythonCount -gt 0) {
            Get-Process python* | Stop-Process -Force -ErrorAction SilentlyContinue
            Write-Host "   ✅ 清理 $pythonCount 个Python进程" -ForegroundColor Green
        }
        
        # Node.js
        $nodeCount = (Get-Process node* -ErrorAction SilentlyContinue).Count
        if ($nodeCount -gt 0) {
            Get-Process node* | Stop-Process -Force -ErrorAction SilentlyContinue
            Write-Host "   ✅ 清理 $nodeCount 个Node.js进程" -ForegroundColor Green
        }
        
        Start-Sleep -Seconds 2
        Write-Host ""
        Write-Host "   ✅ 所有开发进程已清理" -ForegroundColor Green
    }
    
    Read-Host "`n按回车键返回主菜单"
}

function Start-Dashboard {
    Write-Host "`n🚀 启动看板（生产环境）..." -ForegroundColor Yellow
    & ".\生产环境启动.ps1"
}

function Start-DashboardDebug {
    Write-Host "`n🐛 启动看板（调试模式）..." -ForegroundColor Yellow
    & ".\启动看板.ps1"
}

function Stop-Dashboard {
    Write-Host "`n🛑 停止看板..." -ForegroundColor Yellow
    
    Write-Host "   正在停止Python进程..." -ForegroundColor Cyan
    Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-Host "   ✅ 看板已停止" -ForegroundColor Green
    
    Read-Host "`n按回车键返回主菜单"
}

function Export-DatabaseSchema {
    Write-Host "`n📤 导出数据库表结构..." -ForegroundColor Yellow
    python "导出数据库表结构.py"
    Read-Host "`n按回车键返回主菜单"
}

function Start-Redis {
    Write-Host "`n🚀 启动Redis..." -ForegroundColor Yellow
    & ".\启动Redis.ps1"
}

function Show-SystemResources {
    Write-Host "`n📊 系统资源使用情况..." -ForegroundColor Yellow
    Write-Host ""
    
    # 内存
    $sysMem = Get-CimInstance Win32_OperatingSystem
    $totalMemGB = [math]::Round($sysMem.TotalVisibleMemorySize/1MB, 2)
    $freeMemGB = [math]::Round($sysMem.FreePhysicalMemory/1MB, 2)
    $usedMemGB = [math]::Round(($sysMem.TotalVisibleMemorySize - $sysMem.FreePhysicalMemory)/1MB, 2)
    $memUsagePercent = [math]::Round(($usedMemGB / $totalMemGB) * 100, 1)
    
    Write-Host "💾 内存:" -ForegroundColor Cyan
    Write-Host "   总容量: $totalMemGB GB" -ForegroundColor White
    Write-Host "   已使用: $usedMemGB GB ($memUsagePercent%)" -ForegroundColor White
    Write-Host "   可用: $freeMemGB GB" -ForegroundColor White
    Write-Host ""
    
    # CPU
    $cpu = Get-CimInstance Win32_Processor
    Write-Host "🖥️  CPU:" -ForegroundColor Cyan
    Write-Host "   名称: $($cpu.Name)" -ForegroundColor White
    Write-Host "   核心数: $($cpu.NumberOfCores)" -ForegroundColor White
    Write-Host "   逻辑处理器: $($cpu.NumberOfLogicalProcessors)" -ForegroundColor White
    Write-Host ""
    
    # 进程TOP 10
    Write-Host "📋 内存占用TOP 10:" -ForegroundColor Cyan
    Get-Process | 
        Sort-Object WorkingSet -Descending | 
        Select-Object -First 10 Name, 
            @{Name='内存(MB)';Expression={[math]::Round($_.WorkingSet/1MB,2)}} |
        Format-Table -AutoSize
    
    Read-Host "按回车键返回主菜单"
}

function Show-PortUsage {
    Write-Host "`n🔌 端口占用情况..." -ForegroundColor Yellow
    Write-Host ""
    
    $commonPorts = @{
        5432 = "PostgreSQL"
        6379 = "Redis"
        8050 = "Dash看板"
        8051 = "Dash看板(备用)"
        3000 = "Node.js/React"
        8000 = "FastAPI/Django"
    }
    
    foreach ($port in $commonPorts.Keys | Sort-Object) {
        $name = $commonPorts[$port]
        $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        
        if ($connection) {
            Write-Host "✅ 端口 $port ($name): " -NoNewline -ForegroundColor Green
            $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "$($process.ProcessName) (PID: $($connection.OwningProcess))" -ForegroundColor White
            } else {
                Write-Host "PID: $($connection.OwningProcess)" -ForegroundColor White
            }
        } else {
            Write-Host "⚪ 端口 $port ($name): 空闲" -ForegroundColor Gray
        }
    }
    
    Read-Host "`n按回车键返回主菜单"
}

# 主循环
while ($true) {
    Show-Menu
    $choice = Read-Host "请选择操作 (0-14)"
    
    switch ($choice) {
        "1" { Start-PostgreSQL }
        "2" { Stop-PostgreSQL }
        "3" { Restart-PostgreSQL }
        "4" { Show-PostgreSQLStatus }
        "5" { Clear-VSCodeProcesses }
        "6" { Clear-PythonProcesses }
        "7" { Clear-AllDevProcesses }
        "8" { Start-Dashboard }
        "9" { Start-DashboardDebug }
        "10" { Stop-Dashboard }
        "11" { Export-DatabaseSchema }
        "12" { Start-Redis }
        "13" { Show-SystemResources }
        "14" { Show-PortUsage }
        "0" {
            Write-Host "`n👋 再见!" -ForegroundColor Green
            exit 0
        }
        default {
            Write-Host "`n❌ 无效选项，请重新选择" -ForegroundColor Red
            Start-Sleep -Seconds 2
        }
    }
}
