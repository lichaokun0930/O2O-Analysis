# Safe Repository Cleanup Script
# Date: 2025-11-18

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveDir = "Archived_Files_$timestamp"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Repository Cleanup Script" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Create archive directory
New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
Write-Host "[OK] Archive directory created: $archiveDir" -ForegroundColor Green
Write-Host ""

# Files to delete
$filesToDelete = @(
    "智能门店看板_Dash版_删除前备份_20251115_145753.py",
    "智能门店看板_Dash版_备份_20251111_180602.py",
    "智能门店经营看板_可视化.py",
    "智能门店经营看板_使用指南.md",
    "智能门店看板_简化版.py",
    "完整模拟结果.txt",
    "调研结果.txt",
    "最终验证结果.txt",
    "深度对比结果.txt",
    "营销分析结果.txt",
    "deleted_files.txt",
    "verify_channel_profit.py",
    "verify_meituan_sales.py",
    "verify_order_fields.py",
    "verify_revenue_calculation.py",
    "验证计算逻辑.py",
    "查看优化成果.py",
    "查看字段结构.py",
    "查看数据库状态.py",
    "fix_syntax.py",
    "clean_old_upload_code.py",
    "针对性修复.py",
    "修复界面兼容性.py",
    "完整修复兼容性.py",
    "订单数据理解验证.py",
    "订单数据业务逻辑确认.md",
    "启动智能看板.ps1",
    "快速启动看板.py",
    "启动P1_P2_P3.ps1",
    "打包核心文件.py",
    "打包纯代码文件.py",
    "打包给同事.ps1",
    "colleague_package.zip",
    "系统功能测试.py",
    "系统完整测试.py",
    "测试自适应学习系统.py",
    "快速测试.py",
    "逐表分析模板.md",
    "数据提交模板.md",
    "数据需求清单.md",
    "新需求融合协作流程.md",
    "清理过时文件_安全版.ps1",
    "安全清理文件.ps1",
    "安全清理仓库文件.ps1"
)

# Directories to delete
$dirsToDelete = @(
    "历史文档归档_2025-11-06",
    "temp_restore",
    "宸插垹闄ゆ枃浠跺浠絖20251118_145452"
)

# Counters
$movedFiles = 0
$movedDirs = 0
$failedItems = @()

# Move files
Write-Host "Moving files..." -ForegroundColor Yellow
foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        try {
            Move-Item -Path $file -Destination $archiveDir -Force
            Write-Host "  [OK] $file" -ForegroundColor Gray
            $movedFiles++
        }
        catch {
            Write-Host "  [FAIL] $file" -ForegroundColor Red
            $failedItems += $file
        }
    }
}

# Move directories
Write-Host ""
Write-Host "Moving directories..." -ForegroundColor Yellow
foreach ($dir in $dirsToDelete) {
    if (Test-Path $dir) {
        try {
            Move-Item -Path $dir -Destination $archiveDir -Force
            Write-Host "  [OK] $dir\" -ForegroundColor Gray
            $movedDirs++
        }
        catch {
            Write-Host "  [FAIL] $dir\" -ForegroundColor Red
            $failedItems += $dir
        }
    }
}

# Report
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Cleanup Summary" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Files moved: $movedFiles" -ForegroundColor Green
Write-Host "Directories moved: $movedDirs" -ForegroundColor Green

if ($failedItems.Count -gt 0) {
    Write-Host "Failed items: $($failedItems.Count)" -ForegroundColor Red
}

# Calculate archive size
$archiveSize = (Get-ChildItem $archiveDir -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Archive size: $([math]::Round($archiveSize, 2)) MB" -ForegroundColor Cyan
Write-Host "Archive location: .\$archiveDir" -ForegroundColor Cyan

# Save report
$reportPath = Join-Path $archiveDir "cleanup_report.txt"
$reportContent = "Repository Cleanup Report`n"
$reportContent += "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"
$reportContent += "Files moved: $movedFiles`n"
$reportContent += "Directories moved: $movedDirs`n"
$reportContent += "Failed: $($failedItems.Count)`n"
$reportContent += "Archive size: $([math]::Round($archiveSize, 2)) MB`n"

$reportContent | Out-File -FilePath $reportPath -Encoding UTF8

Write-Host ""
Write-Host "[OK] Cleanup completed!" -ForegroundColor Green
Write-Host "Report saved: $reportPath" -ForegroundColor Cyan
Write-Host ""
