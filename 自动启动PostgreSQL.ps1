# PostgreSQL 自动启动脚本
# 用于在启动看板前自动启动数据库

param(
    [switch]$Silent = $false  # 静默模式，不显示详细信息
)

function Start-PostgreSQLAuto {
    if (-not $Silent) {
        Write-Host "🔍 检查 PostgreSQL 状态..." -ForegroundColor Yellow
    }
    
    # 检查PostgreSQL进程是否已运行
    $pgProcesses = Get-Process postgres -ErrorAction SilentlyContinue
    if ($pgProcesses) {
        if (-not $Silent) {
            Write-Host "✅ PostgreSQL 已在运行 ($($pgProcesses.Count) 个进程)" -ForegroundColor Green
        }
        return $true
    }
    
    # 查找PostgreSQL安装路径
    $pgPaths = @(
        "D:\PostgreSQL\bin",
        "C:\Program Files\PostgreSQL\18\bin",
        "C:\Program Files\PostgreSQL\16\bin",
        "C:\Program Files\PostgreSQL\15\bin",
        "C:\Program Files\PostgreSQL\14\bin",
        "C:\Program Files\PostgreSQL\13\bin"
    )
    
    $pgCtl = $null
    $pgBinDir = $null
    foreach ($path in $pgPaths) {
        if (Test-Path "$path\pg_ctl.exe") {
            $pgCtl = "$path\pg_ctl.exe"
            $pgBinDir = $path
            break
        }
    }
    
    if (-not $pgCtl) {
        if (-not $Silent) {
            Write-Host "❌ 未找到 PostgreSQL 安装" -ForegroundColor Red
        }
        return $false
    }
    
    # 查找数据目录
    $dataDirs = @(
        "D:\PostgreSQL\data",
        "C:\Program Files\PostgreSQL\18\data",
        "C:\Program Files\PostgreSQL\16\data",
        "C:\Program Files\PostgreSQL\15\data",
        "C:\Program Files\PostgreSQL\14\data",
        "C:\Program Files\PostgreSQL\13\data"
    )
    
    $dataDir = $null
    foreach ($dir in $dataDirs) {
        if (Test-Path "$dir\postgresql.conf") {
            $dataDir = $dir
            break
        }
    }
    
    if (-not $dataDir) {
        if (-not $Silent) {
            Write-Host "❌ 未找到 PostgreSQL 数据目录" -ForegroundColor Red
        }
        return $false
    }
    
    # 启动PostgreSQL
    if (-not $Silent) {
        Write-Host "🚀 正在启动 PostgreSQL..." -ForegroundColor Yellow
        Write-Host "   安装路径: $pgBinDir" -ForegroundColor Cyan
        Write-Host "   数据目录: $dataDir" -ForegroundColor Cyan
    }
    
    try {
        # 设置环境变量
        $env:PATH = "$pgBinDir;$env:PATH"
        
        # 启动数据库（使用Start-Process避免阻塞）
        $startInfo = New-Object System.Diagnostics.ProcessStartInfo
        $startInfo.FileName = $pgCtl
        $startInfo.Arguments = "start -D `"$dataDir`" -l `"$dataDir\logfile`""
        $startInfo.UseShellExecute = $false
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $startInfo.CreateNoWindow = $true
        
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $startInfo
        $process.Start() | Out-Null
        
        # 等待进程完成（最多5秒）
        $process.WaitForExit(5000) | Out-Null
        
        # 等待PostgreSQL启动
        Start-Sleep -Seconds 3
        
        # 验证启动
        $pgProcesses = Get-Process postgres -ErrorAction SilentlyContinue
        if ($pgProcesses) {
            if (-not $Silent) {
                Write-Host "✅ PostgreSQL 启动成功 ($($pgProcesses.Count) 个进程)" -ForegroundColor Green
            }
            return $true
        } else {
            if (-not $Silent) {
                Write-Host "❌ PostgreSQL 启动失败" -ForegroundColor Red
                $stdout = $process.StandardOutput.ReadToEnd()
                $stderr = $process.StandardError.ReadToEnd()
                if ($stdout) { Write-Host "   输出: $stdout" -ForegroundColor Gray }
                if ($stderr) { Write-Host "   错误: $stderr" -ForegroundColor Gray }
            }
            return $false
        }
    } catch {
        if (-not $Silent) {
            Write-Host "❌ 启动失败: $_" -ForegroundColor Red
        }
        return $false
    }
}

# 如果直接运行此脚本
if ($MyInvocation.InvocationName -ne '.') {
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host "PostgreSQL 自动启动脚本" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host ""
    
    $result = Start-PostgreSQLAuto
    
    Write-Host ""
    if ($result) {
        Write-Host "✅ PostgreSQL 已就绪" -ForegroundColor Green
    } else {
        Write-Host "❌ PostgreSQL 启动失败" -ForegroundColor Red
        Write-Host ""
        Write-Host "请尝试手动启动:" -ForegroundColor Yellow
        Write-Host "   .\启动数据库.ps1" -ForegroundColor Cyan
    }
    Write-Host ""
    
    if (-not $Silent) {
        Read-Host "按回车键退出"
    }
}
