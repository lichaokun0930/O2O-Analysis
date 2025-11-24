# 综合清理脚本 - 清理临时文件、测试脚本、冗余文档
# 创建时间: 2025-11-22
# 说明: 删除调试过程中产生的临时文件和已完成项目的报告文档

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "🧹 项目文件综合清理" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# 创建备份目录
$backupDir = "删除文件备份_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
Write-Host "📦 创建备份目录: $backupDir" -ForegroundColor Cyan
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Write-Host ""

# Python测试脚本
$pyFilesToDelete = @(
    "add_remaining_stock_column.py",
    "check_product_sku.py",
    "check_stock.py",
    "verify_stock.py",
    "test_stock_loading.py",
    "verify_calculation_logic.py",
    "test.py",
    "检查数据库成本.py",
    "检查祥和路成本.py",
    "检查Excel成本.py",
    "检查Order表cost字段.py",
    "验证祥和路成本.py",
    "直接计算祥和路成本.py",
    "检查重复订单.py"
)

# 批处理脚本
$batFilesToDelete = @(
    "导入数据.bat",
    "补充清理.bat",
    "执行清理_安全版.bat",
    "推送前检查.bat",
    "推送到Github.bat",
    "推送营销分析文件.bat"
)

# PowerShell脚本
$ps1FilesToDelete = @(
    "git_clone_fresh.ps1",
    "初始化Git仓库.ps1",
    "检查Memurai安装.ps1",
    "检查营销分析文件.ps1"
)

# Markdown文档 (保留: 待升级_Waitress生产服务器.md, 后续优化计划.md)
$mdFilesToDelete = @(
    "Redis缓存集成完成报告.md",
    "UI_UX优化完成报告.md",
    "启动脚本测试报告.md",
    "导入脚本业务逻辑修复报告.md",
    "文件清理分析报告.md",
    "清理完成报告.md",
    "新电脑配置状态报告.md",
    "requirements追踪系统测试报告.md",
    "快速开始指南.md",
    "README_Dash版使用指南.md",
    "智能门店经营看板_使用指南.md",
    "数据库配置快速指南.md",
    "requirements追踪-快速开始.md",
    "时段与场景自动生成快速参考.md",
    "B电脑克隆清单.md",
    "Github推送文件清单.md",
    "完整推送确认清单.md",
    "数据量评估报告.md"
)

# 其他文件
$otherFilesToDelete = @(
    "成本验证结果.txt",
    "result.txt"
)

# 文件夹
$foldersToDelete = @(
    "待删除文件_20251119_175725",
    "待删除文件_周三022511_180718"
)

Write-Host "📋 将删除的内容:" -ForegroundColor Yellow
Write-Host ""
Write-Host "🐍 Python测试脚本 ($($pyFilesToDelete.Count)个):" -ForegroundColor Cyan
$pyFilesToDelete | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "📜 批处理脚本 ($($batFilesToDelete.Count)个):" -ForegroundColor Cyan
$batFilesToDelete | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "⚡ PowerShell脚本 ($($ps1FilesToDelete.Count)个):" -ForegroundColor Cyan
$ps1FilesToDelete | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "📄 Markdown文档 ($($mdFilesToDelete.Count)个):" -ForegroundColor Cyan
$mdFilesToDelete | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "📑 其他文件 ($($otherFilesToDelete.Count)个):" -ForegroundColor Cyan
$otherFilesToDelete | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "📁 文件夹 ($($foldersToDelete.Count)个):" -ForegroundColor Cyan
$foldersToDelete | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "总计: $($pyFilesToDelete.Count + $batFilesToDelete.Count + $ps1FilesToDelete.Count + $mdFilesToDelete.Count + $otherFilesToDelete.Count) 个文件 + $($foldersToDelete.Count) 个文件夹" -ForegroundColor Yellow
Write-Host ""

$confirmation = Read-Host "确认删除? (yes/no)"

if ($confirmation -eq "yes") {
    $totalDeleted = 0
    $totalNotFound = 0
    $totalBackedUp = 0
    
    Write-Host ""
    Write-Host "开始备份并删除文件..." -ForegroundColor Cyan
    Write-Host ""
    
    # 删除Python文件
    Write-Host "正在处理Python文件..." -ForegroundColor Yellow
    foreach ($file in $pyFilesToDelete) {
        if (Test-Path $file) {
            Copy-Item $file -Destination $backupDir -Force
            $totalBackedUp++
            Remove-Item $file -Force
            Write-Host "✅ $file (已备份)" -ForegroundColor Green
            $totalDeleted++
        } else {
            $totalNotFound++
        }
    }
    
    # 删除批处理文件
    Write-Host ""
    Write-Host "正在处理批处理文件..." -ForegroundColor Yellow
    foreach ($file in $batFilesToDelete) {
        if (Test-Path $file) {
            Copy-Item $file -Destination $backupDir -Force
            $totalBackedUp++
            Remove-Item $file -Force
            Write-Host "✅ $file (已备份)" -ForegroundColor Green
            $totalDeleted++
        } else {
            $totalNotFound++
        }
    }
    
    # 删除PowerShell文件
    Write-Host ""
    Write-Host "正在处理PowerShell脚本..." -ForegroundColor Yellow
    foreach ($file in $ps1FilesToDelete) {
        if (Test-Path $file) {
            Copy-Item $file -Destination $backupDir -Force
            $totalBackedUp++
            Remove-Item $file -Force
            Write-Host "✅ $file (已备份)" -ForegroundColor Green
            $totalDeleted++
        } else {
            $totalNotFound++
        }
    }
    
    # 删除Markdown文件
    Write-Host ""
    Write-Host "正在处理Markdown文档..." -ForegroundColor Yellow
    foreach ($file in $mdFilesToDelete) {
        if (Test-Path $file) {
            Copy-Item $file -Destination $backupDir -Force
            $totalBackedUp++
            Remove-Item $file -Force
            Write-Host "✅ $file (已备份)" -ForegroundColor Green
            $totalDeleted++
        } else {
            $totalNotFound++
        }
    }
    
    # 删除其他文件
    Write-Host ""
    Write-Host "正在处理其他文件..." -ForegroundColor Yellow
    foreach ($file in $otherFilesToDelete) {
        if (Test-Path $file) {
            Copy-Item $file -Destination $backupDir -Force
            $totalBackedUp++
            Remove-Item $file -Force
            Write-Host "✅ $file (已备份)" -ForegroundColor Green
            $totalDeleted++
        } else {
            $totalNotFound++
        }
    }
    
    # 删除文件夹
    Write-Host ""
    Write-Host "正在处理文件夹..." -ForegroundColor Yellow
    foreach ($folder in $foldersToDelete) {
        if (Test-Path $folder) {
            $folderBackup = Join-Path $backupDir $folder
            Copy-Item $folder -Destination $folderBackup -Recurse -Force
            $totalBackedUp++
            Remove-Item $folder -Recurse -Force
            Write-Host "✅ $folder\ (已备份)" -ForegroundColor Green
            $totalDeleted++
        } else {
            $totalNotFound++
        }
    }
    
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host "✨ 清理完成!" -ForegroundColor Green
    Write-Host "已备份: $totalBackedUp 项 -> $backupDir\" -ForegroundColor Cyan
    Write-Host "已删除: $totalDeleted 项" -ForegroundColor Green
    if ($totalNotFound -gt 0) {
        Write-Host "未找到: $totalNotFound 项" -ForegroundColor Yellow
    }
    Write-Host "===========================================" -ForegroundColor Cyan
    
} else {
    Write-Host ""
    Write-Host "❌ 已取消清理操作" -ForegroundColor Red
}

Write-Host ""
Write-Host "💡 已保留的重要文档:" -ForegroundColor Cyan
Write-Host "   ✅ README.md (项目主文档)" -ForegroundColor Gray
Write-Host "   ✅ 【权威】业务逻辑与数据字典完整手册.md" -ForegroundColor Gray
Write-Host "   ✅ 智能门店看板_Dash版使用指南.md" -ForegroundColor Gray
Write-Host "   ✅ 新电脑完整配置指南.md" -ForegroundColor Gray
Write-Host "   ✅ PostgreSQL环境配置完整指南.md" -ForegroundColor Gray
Write-Host "   ✅ Redis安装配置指南.md" -ForegroundColor Gray
Write-Host "   ✅ Git使用指南.md" -ForegroundColor Gray
Write-Host "   ✅ 待升级_Waitress生产服务器.md (保留)" -ForegroundColor Cyan
Write-Host "   ✅ 后续优化计划.md (保留)" -ForegroundColor Cyan
Write-Host ""
Write-Host "💾 备份位置: $backupDir\" -ForegroundColor Yellow
Write-Host "   如需恢复,可从此目录复制文件" -ForegroundColor Gray
Write-Host ""
