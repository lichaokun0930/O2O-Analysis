# ============================================
# 项目文件清理脚本
# 清理临时测试文件、调试脚本、旧版本报告
# ============================================

$ErrorActionPreference = "Stop"
$basePath = $PSScriptRoot

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  项目文件清理工具" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ==========================================
# 第一步：创建备份
# ==========================================
$backupName = "cleanup_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
$backupPath = Join-Path $basePath $backupName

Write-Host "📦 第一步：创建备份目录 $backupName" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupPath -Force | Out-Null

# ==========================================
# 定义要清理的文件列表
# ==========================================

# 1. 测试/验证/诊断脚本（一次性使用，已完成任务）
$testScripts = @(
    # test_ 开头的测试脚本
    "test_api_call.py",
    "test_api_marketing.py",
    "test_compare_dash_api.py",
    "test_data_compare.py",
    "test_diagnosis_fix.py",
    "test_distance_analysis_properties.py",
    "test_distance_api_debug.py",
    "test_distance_data_distribution.py",
    "test_distance_highlight_mapping.py",
    "test_distance_store_filter.py",
    "test_field_removal.py",
    "test_final_checkpoint_distance_diagnosis.py",
    "test_inventory_trend_api.py",
    "test_marketing_structure_properties.py",
    "test_marketing_trend_properties.py",
    "test_order_api_cache.py",
    "test_order_overview_compare.py",
    "test_store_comparison_api.py",
    "test_store_distance.py",
    "test_trend_api_consistency.py",
    "test_trend_calculation_consistency.py",
    "test_upload_fix_verification.py",
    "test_upload.csv",
    "test_week_over_week_response.py",
    
    # debug_ 开头的调试脚本
    "debug_diagnosis_data.py",
    "debug_marketing.py",
    "debug_order_agg.py",
    "debug_week_over_week.py",
    
    # 中文命名的测试/验证/诊断脚本
    "测试Dash优化.py",
    "测试GMV_API_v2.py",
    "测试GMV_API.py",
    "测试React版API分渠道数据.py",
    "测试V8.10.1修复.py",
    "测试全看板性能优化.py",
    "测试后端API.py",
    "测试商品健康分析表格.py",
    "测试客户流失分析向量化优化.py",
    "测试客户流失分析缓存.py",
    "测试性能优化效果.py",
    "测试性能监控数据累积.py",
    "测试性能监控系统.py",
    "测试数据量保护.py",
    "测试方案B_TOP展示.py",
    "测试流式查询和智能加载.py",
    "测试渠道筛选功能.py",
    "测试调试模式.ps1",
    
    "验证7字段营销成本.py",
    "验证API修复效果.py",
    "验证Dash版Tab1渠道数据.py",
    "验证GMV计算.py",
    "验证V8.10.2部署.py",
    "验证单均营销修复.py",
    "验证单均配送费修复_v2.py",
    "验证单均配送费修复.py",
    "验证后端代码版本.py",
    "验证商品数据一致性.py",
    "验证客户流失分析缓存.ps1",
    "验证恢复后营销成本率.py",
    "验证成本结构数据一致性_v2.py",
    "验证成本结构数据一致性.py",
    "验证日期范围影响.py",
    "验证正确营销成本率公式.py",
    "验证沛县店营销成本率.py",
    "验证渠道字段差异.py",
    "验证生产服务器升级.ps1",
    "验证预聚合表一致性.py",
    "验证原价计算营销成本率.py",
    
    "诊断Vue订单数据问题_v2.py",
    "诊断Vue订单数据问题_v3.py",
    "诊断Vue订单数据问题_v4.py",
    "诊断Vue订单数据问题.py",
    "诊断利润率差异.py",
    "诊断商品健康分析表格.py",
    "诊断局域网访问.ps1",
    "诊断查询性能.py",
    "诊断渠道筛选问题.py",
    
    "检查六象限重复数据.py",
    "检查其他渠道数据.py",
    "检查实际利润率.py",
    "检查渠道混合问题.py",
    "检查特定订单.py",
    "检查虚拟环境依赖.py",
    "检查预聚合表结构.py",
    
    "调试营销成本计算.py",
    "深入分析GMV差异.py",
    "深入分析营销成本率.py",
    "深度分析营销成本率差异.py",
    "详细分析GMV差异.py",
    "详细查看API数据.py",
    "详细检查GMV差异.py",
    "多维度营销成本率分析.py",
    "对比Dash和React单均营销计算.py",
    "对比Dash和React营销字段差异.py",
    "对比核心指标计算.py",
    "对比渠道表现数据.py",
    "直接测试渠道筛选逻辑.py",
    "直接测试营销计算逻辑.py",
    "直接测试诊断函数.py",
    "用商品原价计算营销成本率.py",
    "查看API返回格式.py",
    "查看数据日期范围.py",
    "查看门店列表.py"
)

# 2. 旧版本报告文件（V8.x 系列，已过时）
$oldVersionDocs = @(
    "V8.10.1_BUG修复开发文档.md",
    "V8.10.1_BUG修复报告.md",
    "V8.10.1_修复与优化总结.md",
    "V8.10.1_修复总结.md",
    "V8.10.1_商品健康分析表格修复说明.md",
    "V8.10.1_客户流失分析缓存优化.md",
    "V8.10.1_快速验证指南.md",
    "V8.10.1_性能瓶颈分析.md",
    "V8.10.1_按钮缺失批量修复说明.md",
    "V8.10.1_生产服务器升级报告.md",
    "V8.10.2_今日工作总结.md",
    "V8.10.2_向量化优化实施报告.md",
    "V8.10.2_客户流失分析算法优化计划.md",
    "V8.10.2_算法优化实施方案.md",
    "V8.10.2_部署完成报告.md",
    "V8.10.3_README.md",
    "V8.10.3_今日工作总结_性能监控修复.md",
    "V8.10.3_今日工作总结.md",
    "V8.10.3_商品健康分析字段优化.md",
    "V8.10.3_快速验证指南_性能监控修复.md",
    "V8.10.3_快速验证指南.md",
    "V8.10.3_性能监控扩展方案.md",
    "V8.10.3_性能监控数据累积修复报告.md",
    "V8.10.3_性能监控系统实施报告.md",
    "V8.10.3_性能监控面板极简优化.md",
    "V8.10.3_性能监控面板样式优化.md",
    "V8.10.3_数据加载监控已添加.md",
    "V8.10.3_方案B实施完成报告.md",
    "V8.10.3_热销缺货和价格异常修复报告.md",
    "V8.10.3_诊断分析现状评估.md",
    "V8.10.3_部署清单.md",
    "V8.10千万级数据处理实施报告.md",
    "V8.8-V8.9文档清理说明.md",
    "V8.9_README.md",
    "V8.9_Redis缓存修复报告.md",
    "V8.9.1_Dash3兼容性修复报告.md",
    "V8.9.1一页纸总结.md",
    "V8.9.1快速验证指南.md",
    "V8.9.1最终修复说明.md",
    "V8.9.1验证通过报告.md",
    "V8.9.2修正说明.md",
    "V8.9.2千万级数据保护.md",
    "V8.9一页纸总结.md",
    "V8.9完整交付清单.md",
    "V8.9快速验证指南.md",
    "V8.9最终交付说明.md",
    "V8.9最终验证通过报告.md"
)

# 3. 临时/过时的文档
$tempDocs = @(
    "测试当前数据的诊断结果.md",
    "调试模式使用指南.md",
    "调试模式修复说明.md",
    "验证前端编译.md",
    "查看诊断调试输出.md",
    "清理对比表.md",
    "清理建议-最终版.md",
    "清理总结.md",
    "最终清理方案.md",
    "文件清理建议报告.md",
    "项目清理完整指南.md",
    "项目清理方案.md",
    "README_清理说明.md",
    "快速验证_热销缺货和价格异常修复.md"
)

# 4. 一次性工具脚本（已完成任务）
$oneTimeScripts = @(
    "分析可删除文件.py",
    "分析商品原价0的订单.py",
    "分析商品销量分布.py",
    "字段对比分析.py",
    "字段检测工具.py",
    "扫描今日变动.py",
    "清理工作区.py",
    "清除Redis缓存.py",
    "清除缓存并测试.py",
    "任务管理器对比测试.py",
    "内存优化测试工具.py",
    "实时内存监控.py",
    "完整端到端测试.py",
    "快速测试V8.6优化.py",
    "快速验证V8.2.py",
    "性能诊断分析.py",
    "真实端到端性能测试.py",
    "压力测试_30人.py",
    "通用模块诊断工具.py",
    "导出数据库表结构.py",
    "数据库迁移.py",
    "deploy_v8.10.2.py",
    "compare_profit_calculation.py",
    "check_actual_data.py",
    "check_all_stores_distance.py",
    "check_excel_distance.py",
    "check_store_data_source.py",
    "analyze_churn_reasons_v2.py",
    "analyze_churn_reasons_v8.10.2_final.py"
)

# 5. 日志文件
$logFiles = @(
    "启动日志_完整.txt"
)

# ==========================================
# 第二步：备份文件
# ==========================================
Write-Host ""
Write-Host "📦 第二步：备份待删除文件..." -ForegroundColor Yellow

$allFilesToDelete = $testScripts + $oldVersionDocs + $tempDocs + $oneTimeScripts + $logFiles
$backedUp = 0
$notFound = 0

foreach ($file in $allFilesToDelete) {
    $filePath = Join-Path $basePath $file
    if (Test-Path $filePath) {
        Copy-Item $filePath -Destination $backupPath -Force
        $backedUp++
    } else {
        $notFound++
    }
}

Write-Host "  ✅ 已备份 $backedUp 个文件到 $backupName" -ForegroundColor Green
Write-Host "  ℹ️ $notFound 个文件不存在（可能已删除）" -ForegroundColor Gray

# ==========================================
# 第三步：显示清理计划
# ==========================================
Write-Host ""
Write-Host "📋 第三步：清理计划" -ForegroundColor Yellow
Write-Host ""
Write-Host "  将删除以下类型的文件：" -ForegroundColor White
Write-Host "  1. 测试/验证/诊断脚本: $($testScripts.Count) 个" -ForegroundColor Cyan
Write-Host "  2. 旧版本报告 (V8.x): $($oldVersionDocs.Count) 个" -ForegroundColor Cyan
Write-Host "  3. 临时文档: $($tempDocs.Count) 个" -ForegroundColor Cyan
Write-Host "  4. 一次性工具脚本: $($oneTimeScripts.Count) 个" -ForegroundColor Cyan
Write-Host "  5. 日志文件: $($logFiles.Count) 个" -ForegroundColor Cyan
Write-Host ""
Write-Host "  总计: $($allFilesToDelete.Count) 个文件" -ForegroundColor Yellow
Write-Host ""

# ==========================================
# 第四步：确认删除
# ==========================================
$confirm = Read-Host "确认删除这些文件吗？(yes/no)"

if ($confirm -eq "yes") {
    Write-Host ""
    Write-Host "🗑️ 第四步：删除文件..." -ForegroundColor Yellow
    
    $deleted = 0
    foreach ($file in $allFilesToDelete) {
        $filePath = Join-Path $basePath $file
        if (Test-Path $filePath) {
            Remove-Item $filePath -Force
            $deleted++
        }
    }
    
    Write-Host "  ✅ 已删除 $deleted 个文件" -ForegroundColor Green
    
    # 删除旧备份目录
    Write-Host ""
    Write-Host "🗑️ 清理旧备份目录..." -ForegroundColor Yellow
    Get-ChildItem -Path $basePath -Directory | Where-Object { $_.Name -match "^backup_2025" } | ForEach-Object {
        Write-Host "  删除: $($_.Name)" -ForegroundColor Gray
        Remove-Item $_.FullName -Recurse -Force
    }
    
    # 清理缓存目录
    Write-Host ""
    Write-Host "🗑️ 清理缓存目录..." -ForegroundColor Yellow
    $cacheDirs = @("__pycache__", ".pytest_cache", "data_cache")
    foreach ($dir in $cacheDirs) {
        $dirPath = Join-Path $basePath $dir
        if (Test-Path $dirPath) {
            Remove-Item $dirPath -Recurse -Force
            Write-Host "  删除: $dir" -ForegroundColor Gray
        }
    }
    
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  ✅ 清理完成！" -ForegroundColor Green
    Write-Host "  备份位置: $backupPath" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ 已取消清理操作" -ForegroundColor Yellow
    Write-Host "  备份目录已创建: $backupPath" -ForegroundColor Gray
    
    # 删除空备份目录
    if ((Get-ChildItem $backupPath | Measure-Object).Count -eq 0) {
        Remove-Item $backupPath -Force
    }
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
