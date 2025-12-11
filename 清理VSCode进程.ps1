# ============================================
# VS Code 进程清理和优化脚本 V1.0
# 功能: 清理僵尸进程、释放内存、清除缓存
# ============================================

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   VS Code 进程清理和优化工具 V1.0" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ========================================
# 步骤1: 检查当前状态
# ========================================
Write-Host "🔍 检查VS Code进程状态..." -ForegroundColor Yellow
Write-Host ""

$codeProcesses = Get-Process Code* -ErrorAction SilentlyContinue

if (-not $codeProcesses) {
    Write-Host "   ✅ 没有运行中的VS Code进程" -ForegroundColor Green
    Write-Host ""
    Read-Host "按回车键退出"
    exit 0
}

# 统计信息
$processCount = $codeProcesses.Count
$totalMemoryMB = [math]::Round(($codeProcesses | Measure-Object WorkingSet -Sum).Sum / 1MB, 2)
$totalMemoryGB = [math]::Round($totalMemoryMB / 1024, 2)

Write-Host "📊 当前状态:" -ForegroundColor Cyan
Write-Host "   进程数量: $processCount" -ForegroundColor White
Write-Host "   总内存使用: $totalMemoryMB MB ($totalMemoryGB GB)" -ForegroundColor White
Write-Host ""

# 显示进程详情
Write-Host "📋 进程列表 (内存占用TOP 10):" -ForegroundColor Cyan
$codeProcesses | 
    Sort-Object WorkingSet -Descending | 
    Select-Object -First 10 Name, Id, 
        @{Name='内存(MB)';Expression={[math]::Round($_.WorkingSet/1MB,2)}},
        @{Name='启动时间';Expression={$_.StartTime.ToString('HH:mm:ss')}} |
    Format-Table -AutoSize

# 内存使用评估
Write-Host "💡 评估结果:" -ForegroundColor Yellow
if ($totalMemoryGB -gt 5) {
    Write-Host "   ⚠️  内存占用过高 (>5GB)，强烈建议清理" -ForegroundColor Red
    $recommendation = "建议立即清理"
} elseif ($totalMemoryGB -gt 3) {
    Write-Host "   ⚠️  内存占用较高 (>3GB)，建议清理" -ForegroundColor Yellow
    $recommendation = "建议清理"
} elseif ($processCount -gt 20) {
    Write-Host "   ⚠️  进程数量过多 (>20个)，建议清理" -ForegroundColor Yellow
    $recommendation = "建议清理进程"
} else {
    Write-Host "   ✅ 资源使用正常" -ForegroundColor Green
    $recommendation = "可选清理"
}

Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# ========================================
# 步骤2: 用户确认
# ========================================
Write-Host "🚨 警告: 此操作将关闭所有VS Code窗口!" -ForegroundColor Red
Write-Host "请确保已保存所有未保存的工作。" -ForegroundColor Yellow
Write-Host ""
Write-Host "清理选项:" -ForegroundColor Cyan
Write-Host "  1. 🔴 强制关闭所有VS Code进程 (快速)" -ForegroundColor White
Write-Host "  2. 🟡 优雅关闭 + 清理缓存 (推荐)" -ForegroundColor White
Write-Host "  3. 🟢 仅清理缓存和临时文件" -ForegroundColor White
Write-Host "  4. 📊 查看详细进程信息" -ForegroundColor White
Write-Host "  5. ❌ 取消操作" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请选择操作 (1-5)"

switch ($choice) {
    "1" {
        # 强制关闭所有进程
        Write-Host ""
        Write-Host "🔴 强制关闭所有VS Code进程..." -ForegroundColor Red
        Write-Host ""
        
        try {
            Get-Process Code* -ErrorAction SilentlyContinue | Stop-Process -Force
            Start-Sleep -Seconds 2
            
            # 验证
            $remaining = Get-Process Code* -ErrorAction SilentlyContinue
            if ($remaining) {
                Write-Host "   ⚠️  部分进程仍在运行，再次尝试..." -ForegroundColor Yellow
                Get-Process Code* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 1
            }
            
            Write-Host "   ✅ 所有进程已关闭" -ForegroundColor Green
            Write-Host "   💾 释放内存: $totalMemoryGB GB" -ForegroundColor Cyan
        } catch {
            Write-Host "   ❌ 关闭失败: $_" -ForegroundColor Red
        }
    }
    
    "2" {
        # 优雅关闭 + 清理缓存
        Write-Host ""
        Write-Host "🟡 优雅关闭VS Code..." -ForegroundColor Yellow
        Write-Host ""
        
        # 先尝试正常关闭
        Write-Host "   ⏳ 尝试正常关闭..." -ForegroundColor Gray
        $mainProcesses = Get-Process Code -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -ne ""}
        foreach ($proc in $mainProcesses) {
            $proc.CloseMainWindow() | Out-Null
        }
        
        Start-Sleep -Seconds 5
        
        # 检查是否还有进程
        $remaining = Get-Process Code* -ErrorAction SilentlyContinue
        if ($remaining) {
            Write-Host "   ⏳ 部分进程未响应，强制关闭..." -ForegroundColor Yellow
            Get-Process Code* -ErrorAction SilentlyContinue | Stop-Process -Force
            Start-Sleep -Seconds 2
        }
        
        Write-Host "   ✅ 所有进程已关闭" -ForegroundColor Green
        
        # 清理缓存
        Write-Host ""
        Write-Host "🧹 清理VS Code缓存..." -ForegroundColor Yellow
        
        $cachePaths = @(
            "$env:APPDATA\Code\Cache",
            "$env:APPDATA\Code\CachedData",
            "$env:APPDATA\Code\Code Cache",
            "$env:APPDATA\Code\GPUCache",
            "$env:APPDATA\Code\logs",
            "$env:APPDATA\Code - Insiders\Cache",
            "$env:APPDATA\Code - Insiders\CachedData",
            "$env:TEMP\vscode-*"
        )
        
        $totalCleared = 0
        foreach ($path in $cachePaths) {
            if (Test-Path $path) {
                try {
                    $size = (Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue | 
                             Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
                    $sizeMB = [math]::Round($size / 1MB, 2)
                    
                    Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue
                    Write-Host "   ✅ 清理: $(Split-Path $path -Leaf) ($sizeMB MB)" -ForegroundColor Green
                    $totalCleared += $sizeMB
                } catch {
                    Write-Host "   ⚠️  跳过: $(Split-Path $path -Leaf)" -ForegroundColor Yellow
                }
            }
        }
        
        Write-Host ""
        Write-Host "   💾 释放内存: $totalMemoryGB GB" -ForegroundColor Cyan
        Write-Host "   🗑️  清理缓存: $totalCleared MB" -ForegroundColor Cyan
    }
    
    "3" {
        # 仅清理缓存
        Write-Host ""
        Write-Host "🟢 清理VS Code缓存和临时文件..." -ForegroundColor Green
        Write-Host ""
        
        $cachePaths = @(
            "$env:APPDATA\Code\Cache",
            "$env:APPDATA\Code\CachedData",
            "$env:APPDATA\Code\Code Cache",
            "$env:APPDATA\Code\GPUCache",
            "$env:APPDATA\Code\logs",
            "$env:APPDATA\Code - Insiders\Cache",
            "$env:APPDATA\Code - Insiders\CachedData",
            "$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe.local",
            "$env:TEMP\vscode-*"
        )
        
        $totalCleared = 0
        foreach ($path in $cachePaths) {
            if (Test-Path $path) {
                try {
                    $size = (Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue | 
                             Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
                    $sizeMB = [math]::Round($size / 1MB, 2)
                    
                    Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue
                    Write-Host "   ✅ 清理: $(Split-Path $path -Leaf) ($sizeMB MB)" -ForegroundColor Green
                    $totalCleared += $sizeMB
                } catch {
                    Write-Host "   ⚠️  部分文件被占用: $(Split-Path $path -Leaf)" -ForegroundColor Yellow
                }
            } else {
                Write-Host "   ⏭️  跳过: $(Split-Path $path -Leaf) (不存在)" -ForegroundColor Gray
            }
        }
        
        Write-Host ""
        Write-Host "   🗑️  总清理: $totalCleared MB" -ForegroundColor Cyan
        Write-Host "   💡 建议重启VS Code以释放更多内存" -ForegroundColor Yellow
    }
    
    "4" {
        # 显示详细信息
        Write-Host ""
        Write-Host "📊 详细进程信息:" -ForegroundColor Cyan
        Write-Host ""
        
        Get-Process Code* -ErrorAction SilentlyContinue | 
            Select-Object Name, Id, 
                @{Name='内存(MB)';Expression={[math]::Round($_.WorkingSet/1MB,2)}},
                @{Name='CPU(s)';Expression={[math]::Round($_.CPU,2)}},
                @{Name='句柄数';Expression={$_.HandleCount}},
                @{Name='启动时间';Expression={$_.StartTime.ToString('yyyy-MM-dd HH:mm:ss')}},
                @{Name='窗口标题';Expression={$_.MainWindowTitle}} |
            Format-Table -AutoSize
        
        Write-Host ""
        Write-Host "💡 如需清理，请重新运行本脚本" -ForegroundColor Yellow
    }
    
    "5" {
        Write-Host ""
        Write-Host "❌ 操作已取消" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "按回车键退出"
        exit 0
    }
    
    default {
        Write-Host ""
        Write-Host "❌ 无效选项" -ForegroundColor Red
        Write-Host ""
        Read-Host "按回车键退出"
        exit 1
    }
}

# ========================================
# 步骤3: 最终验证
# ========================================
Write-Host ""
Write-Host "🔍 最终验证..." -ForegroundColor Yellow

$finalCheck = Get-Process Code* -ErrorAction SilentlyContinue
if ($finalCheck) {
    Write-Host "   ⚠️  仍有 $($finalCheck.Count) 个进程在运行" -ForegroundColor Yellow
    Write-Host "   可能需要手动关闭或重启系统" -ForegroundColor Yellow
} else {
    Write-Host "   ✅ 所有VS Code进程已关闭" -ForegroundColor Green
}

# 系统内存状态
$sysMem = Get-CimInstance Win32_OperatingSystem
$freeMemGB = [math]::Round($sysMem.FreePhysicalMemory/1MB, 2)
Write-Host "   💾 当前可用内存: $freeMemGB GB" -ForegroundColor Cyan

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "✅ 清理完成!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 优化建议:" -ForegroundColor Yellow
Write-Host "   1. 定期清理VS Code缓存（每周一次）" -ForegroundColor White
Write-Host "   2. 及时关闭不用的编辑器窗口" -ForegroundColor White
Write-Host "   3. 检查并禁用不必要的扩展" -ForegroundColor White
Write-Host "   4. 增大VS Code内存限制（settings.json）" -ForegroundColor White
Write-Host ""

Read-Host "按回车键退出"
