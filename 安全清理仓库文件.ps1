# 安全清理仓库文件脚本
# 日期: 2025-11-18
# 功能: 备份后删除过时/临时文件

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveDir = "已清理文件归档_$timestamp"

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "🗑️  安全清理仓库文件" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# 创建归档目录
New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
Write-Host "✅ 创建归档目录: $archiveDir" -ForegroundColor Green
Write-Host ""

# 定义要删除的文件列表
$filesToDelete = @(
    # 1. 旧版本备份文件
    "智能门店看板_Dash版_删除前备份_20251115_145753.py",
    "智能门店看板_Dash版_备份_20251111_180602.py",
    "智能门店经营看板_可视化.py",
    "智能门店经营看板_使用指南.md",
    "智能门店看板_简化版.py",
    
    # 2. 临时/测试文件
    "完整模拟结果.txt",
    "调研结果.txt",
    "最终验证结果.txt",
    "深度对比结果.txt",
    "营销分析结果.txt",
    "deleted_files.txt",
    
    # 3. 验证/测试脚本
    "verify_channel_profit.py",
    "verify_meituan_sales.py",
    "verify_order_fields.py",
    "verify_revenue_calculation.py",
    "验证计算逻辑.py",
    "查看优化成果.py",
    "查看字段结构.py",
    "查看数据库状态.py",
    
    # 4. 旧的修复脚本
    "fix_syntax.py",
    "clean_old_upload_code.py",
    "针对性修复.py",
    "修复界面兼容性.py",
    "完整修复兼容性.py",
    "订单数据理解验证.py",
    "订单数据业务逻辑确认.md",
    
    # 5. 重复/过时的启动脚本
    "启动智能看板.ps1",
    "快速启动看板.py",
    "启动P1_P2_P3.ps1",
    
    # 6. 打包脚本
    "打包核心文件.py",
    "打包纯代码文件.py",
    "打包给同事.ps1",
    "colleague_package.zip",
    
    # 7. 测试系统文件
    "系统功能测试.py",
    "系统完整测试.py",
    "测试自适应学习系统.py",
    "快速测试.py",
    
    # 8. 旧的或重复的文档
    "逐表分析模板.md",
    "数据提交模板.md",
    "数据需求清单.md",
    "新需求融合协作流程.md",
    
    # 9. 旧的清理脚本
    "清理过时文件_安全版.ps1",
    "安全清理文件.ps1"
)

# 定义要删除的目录列表
$dirsToDelete = @(
    "历史文档归档_2025-11-06",
    "temp_restore",
    "宸插垹闄ゆ枃浠跺浠絖20251118_145452"
)

# 统计
$movedFiles = 0
$movedDirs = 0
$failedFiles = @()

# 移动文件到归档目录
Write-Host "📦 开始备份文件..." -ForegroundColor Yellow
foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        try {
            Move-Item -Path $file -Destination $archiveDir -Force
            Write-Host "  ✓ 已备份: $file" -ForegroundColor Gray
            $movedFiles++
        }
        catch {
            Write-Host "  ✗ 失败: $file - $($_.Exception.Message)" -ForegroundColor Red
            $failedFiles += $file
        }
    }
    else {
        Write-Host "  - 不存在: $file" -ForegroundColor DarkGray
    }
}

# 移动目录到归档目录
Write-Host ""
Write-Host "📁 开始备份目录..." -ForegroundColor Yellow
foreach ($dir in $dirsToDelete) {
    if (Test-Path $dir) {
        try {
            Move-Item -Path $dir -Destination $archiveDir -Force
            Write-Host "  ✓ 已备份: $dir\" -ForegroundColor Gray
            $movedDirs++
        }
        catch {
            Write-Host "  ✗ 失败: $dir - $($_.Exception.Message)" -ForegroundColor Red
            $failedFiles += $dir
        }
    }
    else {
        Write-Host "  - 不存在: $dir\" -ForegroundColor DarkGray
    }
}

# 生成清理报告
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "📊 清理报告" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ 成功备份文件: $movedFiles 个" -ForegroundColor Green
Write-Host "✅ 成功备份目录: $movedDirs 个" -ForegroundColor Green

if ($failedFiles.Count -gt 0) {
    Write-Host "❌ 失败项: $($failedFiles.Count) 个" -ForegroundColor Red
    Write-Host ""
    Write-Host "失败列表:" -ForegroundColor Yellow
    foreach ($failed in $failedFiles) {
        Write-Host "  - $failed" -ForegroundColor Red
    }
}

# 计算归档目录大小
$archiveSize = (Get-ChildItem $archiveDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host ""
Write-Host "💾 归档目录大小: $([math]::Round($archiveSize, 2)) MB" -ForegroundColor Cyan
Write-Host "📂 归档位置: .\$archiveDir" -ForegroundColor Cyan

# 保存清理报告
$reportPath = Join-Path $archiveDir "清理报告.txt"
# 生成简化的清理报告
$reportLines = @(
    "Cleanup Report",
    "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "=" * 60,
    "",
    "Files moved: $movedFiles",
    "Directories moved: $movedDirs",
    "Failed: $($failedFiles.Count)",
    "Archive size: $([math]::Round($archiveSize, 2)) MB",
    "",
    "Files:",
    $($filesToDelete -join "`n"),
    "",
    "Directories:",
    $($dirsToDelete -join "`n")
)

$reportLines -join "`n" | Out-File -FilePath $reportPath -Encoding UTF8
Write-Host ""
Write-Host "📄 清理报告已保存: $reportPath" -ForegroundColor Green

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "✅ 清理完成！仓库已优化" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 提示:" -ForegroundColor Yellow
Write-Host "  - 所有文件已安全备份到 $archiveDir" -ForegroundColor White
Write-Host "  - 如需恢复，从归档目录移回即可" -ForegroundColor White
Write-Host "  - 建议保留归档目录30天后再删除" -ForegroundColor White
Write-Host ""
