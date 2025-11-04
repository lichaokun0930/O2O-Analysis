#!/usr/bin/env pwsh
# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    Clean up outdated files in the calculation model directory
.DESCRIPTION
    Batch delete temporary test files, diagnostic scripts, backup files, etc.
    Keep: sales_decline_diagnosis_enhanced.py, smart_store_dashboard_visual.py
.NOTES
    Lists all files to be deleted before execution, requires confirmation
#>

# Set console encoding to UTF-8 with BOM for Chinese character support
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Smart Store Dashboard - File Cleanup Tool (Safe)    " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# ==================== File List ====================

# Category 1: Test Files (10 files) - Keep sales_decline_diagnosis_enhanced.py
$testFiles = @(
    "测试AI业务上下文集成.py",
    "测试AI分析器.py",
    "测试Tab2_AI按钮.py",
    "测试Tab5扩展集成.py",
    "测试gemini模型.py",
    "测试利润品占比.py",
    "测试商品智能打标.py",
    "测试场景洞察结构.py",
    "测试场景画像修复.py",
    "测试成本优化Tab.py"
)

# Category 2: Quick Test Scripts (4 files)
$quickTestFiles = @(
    "快速测试场景洞察.py",
    "快速验证AI配置.py",
    "完整测试智谱API.py",
    "最小化测试API.py"
)

# Category 3: Diagnosis Scripts (4 files)
$diagnosisFiles = @(
    "诊断场景营销Tab.py",
    "诊断成本字段.py",
    "最终诊断利润.py",
    "检查热力图逻辑.py"
)

# Category 4: Backup Files (1 file)
$backupFiles = @(
    "智能门店看板_Dash版_备份_20251026_004413.py"
)

# Category 5: Old Version Files (7 files) - Keep smart_store_dashboard_visual.py
$oldVersionFiles = @(
    "智能门店看板_简化版.py",
    "智能门店经营看板系统.py",
    "场景营销看板.py",
    "多商品订单引导分析看板.py",
    "销量下滑诊断_简化版.py"
)

# Category 6: Analysis Scripts (5 files)
$analysisFiles = @(
    "商品分类结构分析.py",
    "客单价与商品角色相关性分析.py",
    "订单数据理解验证.py",
    "验证时段场景匹配逻辑.py",
    "分析打标结果.py"
)

# Category 7: Duplicate Startup Scripts (8 files)
$startupFiles = @(
    "启动Dash看板_新.ps1",
    "启动看板_新.ps1",
    "启动看板_简易版.ps1",
    "启动多商品分析看板.ps1",
    "启动智能看板.ps1",
    "启动看板.bat",
    "启动看板-后台模式.bat",
    "启动AI看板.bat"
)

# Category 8: Excel Reports (4 files)
$reportFiles = @(
    "问题诊断报告_20251014_181413.xlsx",
    "问题诊断报告_20251016_164453.xlsx",
    "测试_商品场景画像.xlsx",
    "测试_商品智能打标结果_订单数据.xlsx"
)

# Merge all files to delete
$allFilesToDelete = $testFiles + $quickTestFiles + $diagnosisFiles + $backupFiles + 
                    $oldVersionFiles + $analysisFiles + $startupFiles + $reportFiles

# ==================== Display Files to Delete ====================
Write-Host "=== Files to Delete - Total: $($allFilesToDelete.Count) ===" -ForegroundColor Yellow
Write-Host ""

$categoryNames = @{
    0 = "* Test Files"
    1 = "* Quick Test Scripts"
    2 = "* Diagnosis Scripts"
    3 = "* Backup Files"
    4 = "* Old Version Files"
    5 = "* Analysis Scripts"
    6 = "* Duplicate Startup Scripts"
    7 = "* Excel Reports"
}

$categories = @(
    $testFiles,
    $quickTestFiles,
    $diagnosisFiles,
    $backupFiles,
    $oldVersionFiles,
    $analysisFiles,
    $startupFiles,
    $reportFiles
)

$existingCount = 0
$missingCount = 0

for ($i = 0; $i -lt $categories.Count; $i++) {
    Write-Host $categoryNames[$i] -ForegroundColor Cyan
    foreach ($file in $categories[$i]) {
        if (Test-Path $file) {
            $fileSize = (Get-Item $file).Length / 1KB
            $sizeStr = "$([math]::Round($fileSize, 2)) KB"
            Write-Host "  + $file ($sizeStr)" -ForegroundColor Green
            $existingCount++
        } else {
            Write-Host "  - $file (Not Found)" -ForegroundColor DarkGray
            $missingCount++
        }
    }
    Write-Host ""
}

# ==================== Files to Keep ====================
Write-Host "=== Files to Keep ===" -ForegroundColor Green
Write-Host "  * 销量下滑诊断_增强版.py (User Required)" -ForegroundColor Green
Write-Host "  * 智能门店经营看板_可视化.py (User Required)" -ForegroundColor Green
Write-Host ""

# ==================== Statistics ====================
Write-Host "=== Statistics ===" -ForegroundColor Yellow
Write-Host "  Total Files: $($allFilesToDelete.Count)" -ForegroundColor White
Write-Host "  Existing: $existingCount" -ForegroundColor Green
Write-Host "  Not Found: $missingCount" -ForegroundColor DarkGray
Write-Host ""

if ($existingCount -eq 0) {
    Write-Host "INFO: All files already deleted, nothing to do!" -ForegroundColor Green
    exit 0
}

# ==================== User Confirmation ====================
Write-Host "WARNING: This will permanently delete $existingCount files!" -ForegroundColor Red
Write-Host ""
$confirmation = Read-Host "Confirm deletion? Type YES to continue, any other key to cancel"

if ($confirmation -ne 'YES') {
    Write-Host ""
    Write-Host "CANCELLED: Operation cancelled by user" -ForegroundColor Yellow
    exit 0
}

# ==================== Execute Deletion ====================
Write-Host ""
Write-Host "=== DELETING: Starting file deletion ===" -ForegroundColor Cyan
Write-Host ""

$deletedCount = 0
$failedCount = 0
$deletedFiles = @()
$failedFiles = @()

foreach ($file in $allFilesToDelete) {
    if (Test-Path $file) {
        try {
            Remove-Item $file -Force -ErrorAction Stop
            Write-Host "  + Deleted: $file" -ForegroundColor Green
            $deletedCount++
            $deletedFiles += $file
        } catch {
            Write-Host "  x Failed: $file" -ForegroundColor Red
            Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
            $failedCount++
            $failedFiles += $file
        }
    }
}

# ==================== Completion Summary ====================
Write-Host ""
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "              Cleanup Completed                         " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "SUCCESS: Deleted $deletedCount files" -ForegroundColor Green
if ($failedCount -gt 0) {
    Write-Host "FAILED: $failedCount files failed to delete" -ForegroundColor Red
}
Write-Host ""

# Generate deletion log
$logFile = "cleanup_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
$logContent = @"
Smart Store Dashboard - File Cleanup Log
Execution Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

================================================================================
Statistics
================================================================================
Total Files: $($allFilesToDelete.Count)
Deleted: $deletedCount
Failed: $failedCount

================================================================================
Deleted Files
================================================================================
$($deletedFiles -join "`n")

================================================================================
Failed Files
================================================================================
$($failedFiles -join "`n")

================================================================================
Preserved Files
================================================================================
* 销量下滑诊断_增强版.py (User Required)
* 智能门店经营看板_可视化.py (User Required)

================================================================================
Category Details
================================================================================
* Test Files: $($testFiles.Count)
* Quick Test Scripts: $($quickTestFiles.Count)
* Diagnosis Scripts: $($diagnosisFiles.Count)
* Backup Files: $($backupFiles.Count)
* Old Version Files: $($oldVersionFiles.Count)
* Analysis Scripts: $($analysisFiles.Count)
* Duplicate Startup Scripts: $($startupFiles.Count)
* Excel Reports: $($reportFiles.Count)

================================================================================
"@

$logContent | Out-File -FilePath $logFile -Encoding UTF8
Write-Host "Cleanup log saved to $logFile" -ForegroundColor Cyan
Write-Host ""
Write-Host "Cleanup completed successfully" -ForegroundColor Green
Write-Host ""

# Pause to review results
Write-Host "Press any key to exit" -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
