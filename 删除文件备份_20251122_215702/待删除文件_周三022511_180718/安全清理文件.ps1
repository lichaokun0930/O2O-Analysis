# 安全清理临时文件脚本
# 创建时间: 2025-11-18

$ErrorActionPreference = "Stop"
$BaseDir = $PSScriptRoot
$BackupDir = Join-Path $BaseDir "已删除文件备份_$(Get-Date -Format 'yyyyMMdd_HHmmss')"

Write-Host "======================================================================"
Write-Host "                  安全清理临时文件工具" -ForegroundColor Cyan
Write-Host "======================================================================"
Write-Host ""

# 创建备份目录
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
Write-Host "备份目录: $BackupDir" -ForegroundColor Green
Write-Host ""

# 定义要删除的文件列表
$filesToDelete = @(
    # test_*.py
    "test_cache_logic.py", "test_category_analysis.py", "test_channel_comparison.py",
    "test_comparison.py", "test_comparison_simple.py", "test_dashboard_integration.py",
    "test_dropdown_simple.py", "test_echarts.py", "test_filter_fix.py", "test_fixes.py",
    "test_preload.py", "test_real_data_structure.py", "test_real_scenario.py",
    "test_store_dropdown.py",
    
    # 测试*.py
    "测试Tab1订单导出.py", "测试TAB1实收价格修复.py", "测试Tab7_ECharts图表.py",
    "测试Tab7分析器.py", "测试Tab7回调.py", "测试八象限分析.py", "测试错误修复.py",
    "测试导入.py", "测试分类导出功能.py", "测试看板实际函数.py", "测试看板数据.py",
    "测试科学八象限对比.py", "测试客单价明细导出.py", "测试客单价增强导出.py",
    "测试空序列修复.py", "测试库存逻辑.py", "测试配送净成本.py", "测试趋势分析导出.py",
    "测试渠道修复.py", "测试三方对比.py", "测试删除门店功能.py", "测试数据库加载库存.py",
    "测试数据库利润.py", "测试系统函数输出.py", "测试祥和路店完整数据.py",
    "测试销售趋势优化.py", "测试新利润公式.py", "测试修复后的analyzer.py",
    "测试修复后的订单级处理.py", "测试营销成本计算.py", "测试营销分析.py",
    "测试营销分析完整导出.py", "测试营销分析修复.py", "测试营销占比筛选.py",
    "测试字段导入.py", "测试字段兼容性修复.py",
    
    # 验证*.py
    "验证Excel原始数据.py", "验证None值处理修复.py", "验证Tab6.py", "验证Tab7升级.py",
    "验证Tab7数据结构.py", "验证贝特幂案例.py", "验证成本字段是总成本.py",
    "验证动销逻辑修复.py", "验证分类趋势渠道筛选.py", "验证环比调试日志.py",
    "验证集成状态.py", "验证聚合后字段含义.py", "验证看板显示.py",
    "验证客单价渠道筛选.py", "验证利润额公式.py", "验证利润公式统一性.py",
    "验证利润计算逻辑.py", "验证利润率计算.py", "验证门店列表刷新和空间回收.py",
    "验证门店总利润差异.py", "验证配送平台利润计算.py", "验证配送平台字段.py",
    "验证企客后返聚合逻辑.py", "验证渠道环比修复.py", "验证渠道修复.py",
    "验证渠道字段修复.py", "验证渠道字段重复修复.py", "验证全部修复.py",
    "验证三个问题修复.py", "验证三维度利润计算.py", "验证商品实收额.py",
    "验证售罄率和库存.py", "验证数据库amount聚合.py", "验证数据库加载完整性.py",
    "验证象限分类逻辑.py", "验证销售趋势差异.py", "验证新利润额公式.py",
    "验证新字段计算逻辑.py", "验证修复后的计算.py", "验证修复后的聚合逻辑.py",
    "验证修复结果.py", "验证修改完成.py", "验证营销成本计算.py",
    "验证预计订单收入字段性质.py", "验证预计零售额.py", "验证主流区修复.py",
    "验证总利润计算.py", "验证总利润卡片.py",
    
    # 检查*.py
    "检查Excel利润额.py", "检查Excel利润字段.py", "检查Excel预计订单收入.py",
    "检查标准化字段.py", "检查产品表库存.py", "检查订单ID.py", "检查订单过滤.py",
    "检查库存数据.py", "检查利润额差异.py", "检查配送费逻辑.py", "检查渠道利润差异.py",
    "检查渠道数据.py", "检查闪购小程序费用.py", "检查数据差异原因.py",
    "检查数据库amount字段.py", "检查数据库表结构.py", "检查数据库分类统计.py",
    "检查数据库企客后返.py", "检查数据库数据.py", "检查数据库预计订单收入.py",
    "检查数据库重复.py", "检查数据库字段.py", "检查剔除耗材后数据.py",
    "检查祥和路店利润.py", "检查销售额计算.py", "检查预计订单收入.py", "检查字段名称.py",
    
    # 诊断、分析、对比、调试
    "诊断看板数据加载.py", "诊断利润额差异.py", "诊断利润计算.py", "诊断三个问题.py",
    "诊断上传问题.py", "诊断数据库问题.py", "诊断预计订单收入.py", "诊断总利润.py",
    "分析Excel利润额.py", "分析Excel利润字段.py", "分析差异来源.py", "分析郭庄路店数据.py",
    "分析金寨店利润.py", "分析数据缺失.py", "分析条码6949352201748.py", "分析销售额字段.py",
    "对比Excel和数据库.py", "对比数据库与Excel.py", "对比祥和路利润计算.py",
    "对比新旧公式.py", "对比营销分摊方式.py",
    "调试订单ID差异.py", "调试分类趋势.py", "调试分类趋势_简洁版.py",
    
    # 临时文件
    "temp_compare_fields.py", "temp_compute_platform_fee_totals.py", "temp_platform_breakdown.py",
    
    # 其他临时脚本
    "analyze_db_problem.py", "analyze_formula.py", "analyze_git_diff.py",
    "calculate_channel_profit_correct.py", "check_cached_data.py", "check_file.py",
    "check_order_ids.py", "check_platform_fee.py", "clear_cache.py",
    "compare_calculations.py", "compare_profit.py", "create_database.py",
    "dashboard_integrated.py", "dashboard_with_source_switch.py",
    "DATABASE_FIRST_STANDARD.py", "debug_xianghe_store.py",
    "diagnose_comparison.py", "diagnose_database.py", "diagnose_fee_problem.py",
    "diagnose_profit_diff.py", "diagnose_single_day.py",
    "fix_xianghe_dates.py", "main_simplified.py", "monitor_logs.py",
    "query_channel_profit.py", "reimport_xianghe_store.py", "replace_main.py",
    "reverse_engineer.py", "simple_query.py", "simulate_dashboard.py",
    "tab7_callbacks.py", "waterfall_chart.py", "fix_syntax.py", "clean_old_upload_code.py",
    "mqpd.py", "gemini_ai_助手.py",
    
    # 中文临时脚本
    "品类阈值诊断.py", "查看优化成果.py", "查看字段结构.py", "查看数据库状态.py",
    "穷举所有可能公式.py", "空值为0全公式测试.py", "精确反推.py", "系统性匹配手算公式.py",
    "系统验证字段逻辑.py", "紧急排查预计订单收入.py", "终极测试利润公式.py",
    "核查看板利润差异.py", "深度分析利润额.py", "深度对比分析.py", "深度诊断利润.py",
    "清理并重新导入数据.py", "清理重复数据.py", "清空并重新导入.py",
    "定位TAB1实收价格问题.py", "逐日分析.py", "演示营销占比筛选.py",
    "用您的公式计算.py", "用最初公式计算祥和路.py", "直接分析祥和路Excel.py",
    "直接测试分析器.py", "简单测试营销成本.py", "详细分析高利润率原因.py",
    "详细利润分解.py", "详细对比手算差异.py", "调研营销数据.py",
    "计算新数据文件.py", "计算配送成本对比.py", "订单概览计算公式详解.py",
    "评分模型分析器.py", "反推Excel利润公式.py", "反推Excel利润额公式.py",
    "反推手算公式.py", "同步Product表库存.py", "完全复制看板逻辑.py",
    "完整检查数据库amount.py", "完整模拟看板流程.py", "完整流程测试.py",
    "完整测试Tab7组件.py", "最终确认利润额公式.py", "最终验证.py",
    "最终验证看板逻辑.py", "全面诊断数据问题.py", "删除旧数据.py",
    "自动删除旧数据.py", "自定义导入示例.py", "重新导入数据库.py",
    "销量下滑诊断_增强版.py", "问题分析报告.py", "客单价与商品角色相关性分析.py",
    "多商品订单引导分析看板.py", "订单分析增强模块.py", "营销异常分析器.py",
    "科学八象限分析器.py",
    
    # 备份文件
    "智能门店看板_Dash版_备份_20251111_180602.py",
    
    # 日志和结果文件
    "dash_stderr.log", "dash_stdout.log", "debug_log.txt", "debug_result.txt",
    "test_result.txt", "problems.txt", "调研结果.txt", "深度对比结果.txt",
    "完整模拟结果.txt", "营销分析结果.txt", "最终验证结果.txt",
    
    # Excel文件
    "八象限分析结果.xlsx", "测试_Tab1订单导出_模拟数据.xlsx",
    "测试_客单价区间商品明细.xlsx", "测试_营销分析修复验证.xlsx",
    "客单价趋势分析_测试_20251114_193622.xlsx", "美团闪购逐日利润明细.xlsx",
    "如东门店_10月31日_客单价小于10元_20251110_194900.xlsx", "售罄率验证报告.xlsx",
    "祥和路店_营销分析报告_全部渠道_20251101-20251105_20251114_161902.xlsx",
    
    # HTML文件
    "分类销售看板布局demo.html",
    
    # Markdown文档
    "Tab7_ECharts修复报告.md", "Tab7系统排查报告.md", "八象限分析结果总结.md",
    "科学八象限分析测试总结.md", "空序列错误修复报告.md", "验证修复.md",
    "三个问题修复说明.md", "Tab1详细分析看板_计算公式修改总结.md",
    "客单价深度分析_计算公式修改总结.md", "渠道对比计算公式修改总结.md",
    "销售趋势分析_计算公式修改总结.md", "分类销售额计算逻辑修复说明.md",
    "企客后返聚合逻辑修复总结.md", "配送平台字段集成报告.md",
    "配送平台物流配送费优化报告.md", "数据库库存字段修复说明.md",
    "售罄率和库存逻辑修改总结.md", "滞销品和库存周转显示问题修复说明.md",
    "问题总结_滞销品和库存周转显示异常.md", "字段兼容性说明.md",
    "字段依赖关系确认.md", "商品分类销售占比图表优化完成报告.md",
    "一级分类销售趋势图表修改完成报告.md", "新增字段优化说明.md",
    "动销率移除说明.md", "README_Dash版.md", "README_可视化看板.md",
    "README_文档索引.md", "README_性能优化.md", "Dash看板统一计算标准.md",
    "统一计算标准.md", "TAB1利润计算逻辑汇总.md", "利润计算逻辑说明.md",
    "利润额公式更新总结.md", "利润额字段说明文档.md",
    "销售额和利润计算公式确认.md", "业务逻辑核心知识库.md",
    "订单数据业务逻辑确认.md", "原始数据业务逻辑确认.md", "给同事的说明.md",
    "可删除文件清单_20251110.md", "导入脚本使用指南.md",
    "客单价深度分析修复报告.md", "营销分析导出字段更新说明.md",
    "系统修改日志.md", "版本更新日志.md", "TAB删除操作记录.md",
    "项目完成总结.md", "BI平台迁移指南.md", "专业BI升级方案.md",
    "DEVELOPMENT_ROADMAP.md", "临时分析库优化完整方案.md",
    "性能优化方案_20251108.md", "性能优化建议清单.md", "性能优化总览.md",
    "客单价分析功能说明.md", "营销分析方法对比.md", "营销成本计算说明.md"
)

# 处理文件
$backedUp = 0
$deleted = 0
$notFound = 0

Write-Host "开始处理文件..." -ForegroundColor Yellow
Write-Host ""

foreach ($file in $filesToDelete) {
    $filePath = Join-Path $BaseDir $file
    
    if (Test-Path $filePath) {
        # 备份
        $backupPath = Join-Path $BackupDir $file
        Copy-Item $filePath $backupPath -Force
        $backedUp++
        
        # 删除
        Remove-Item $filePath -Force
        $deleted++
        
        if ($deleted % 50 -eq 0) {
            Write-Host "已处理 $deleted 个文件..." -ForegroundColor Cyan
        }
    } else {
        $notFound++
    }
}

Write-Host ""
Write-Host "======================================================================"
Write-Host "处理完成!" -ForegroundColor Green
Write-Host "======================================================================"
Write-Host ""
Write-Host "备份: $backedUp 个" -ForegroundColor Green
Write-Host "删除: $deleted 个" -ForegroundColor Green
Write-Host "未找到: $notFound 个" -ForegroundColor Yellow
Write-Host ""
Write-Host "备份目录: $BackupDir" -ForegroundColor Cyan
Write-Host ""

# 生成删除报告
$reportContent = "文件清理报告`n"
$reportContent += "生成时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n`n"
$reportContent += "备份目录: $BackupDir`n`n"
$reportContent += "统计:`n"
$reportContent += "- 备份文件: $backedUp 个`n"
$reportContent += "- 删除文件: $deleted 个`n"
$reportContent += "- 未找到: $notFound 个`n`n"
$reportContent += "保留的文件:`n"
$reportContent += "- 用户复购分析看板demo.html`n"
$reportContent += "- ai_pandasai_integration.py`n"
$reportContent += "- ai_rag_knowledge_base.py`n"
$reportContent += "- redis_cache_manager.py`n"
$reportContent += "- 智能门店看板_Dash版_删除前备份_20251115_145753.py`n`n"
$reportContent += "如需恢复，请从备份目录复制文件回工作目录。`n"

$reportPath = Join-Path $BackupDir "删除报告.txt"
$reportContent | Out-File $reportPath -Encoding UTF8

Write-Host "删除报告已生成" -ForegroundColor Green
Write-Host ""
