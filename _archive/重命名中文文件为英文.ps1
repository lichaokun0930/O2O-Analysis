# 批量重命名中文文件为英文 - 避免编码问题
# 针对核心文件进行重命名

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "          中文文件名重命名工具 - 避免编码问题                    " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# 定义重命名映射表
$renameMap = @{
    # 核心Python文件
    "智能门店看板_Dash版.py" = "dashboard_main.py"
    "订单数据处理器.py" = "order_processor.py"
    "真实数据处理器.py" = "real_data_processor.py"
    "场景营销智能决策引擎.py" = "scenario_decision_engine.py"
    "商品场景智能打标引擎.py" = "product_tagging_engine.py"
    "科学八象限分析器.py" = "octant_analyzer.py"
    "评分模型分析器.py" = "scoring_analyzer.py"
    "自适应学习引擎.py" = "adaptive_learning_engine.py"
    "学习数据管理系统.py" = "learning_data_manager.py"
    "增量学习优化器.py" = "incremental_optimizer.py"
    "智能导入门店数据.py" = "smart_data_import.py"
    "查看数据库状态.py" = "check_db_status.py"
    "导出数据库.py" = "export_database.py"
    "打包核心文件.py" = "package_core_files.py"
    "打包纯代码文件.py" = "package_code_only.py"
    "gemini_ai_助手.py" = "gemini_ai_assistant.py"
    
    # 启动脚本
    "启动看板.ps1" = "start_dashboard.ps1"
    "启动看板.bat" = "start_dashboard.bat"
    "启动智能看板.ps1" = "start_smart_dashboard.ps1"
    "启动数据库.ps1" = "start_database.ps1"
    "启动看板_简易版.ps1" = "start_dashboard_simple.ps1"
    "启动看板_显示日志.ps1" = "start_dashboard_verbose.ps1"
    "启动看板-后台模式.bat" = "start_dashboard_background.bat"
    "启动多商品分析看板.ps1" = "start_multi_product_dashboard.ps1"
    "启动Dash看板.ps1" = "start_dash_dashboard.ps1"
    
    # 工具脚本
    "主菜单.ps1" = "main_menu.ps1"
    "安装依赖.ps1" = "install_dependencies.ps1"
    "打包给同事.ps1" = "package_for_colleague.ps1"
    "打包完整目录.ps1" = "package_full_directory.ps1"
    "重命名中文文件为英文.ps1" = "rename_chinese_to_english.ps1"
    
    # Markdown文档（保留中文，但创建英文副本）
    # 这些会在打包时创建英文README
}

Write-Host "📋 重命名计划:" -ForegroundColor Yellow
Write-Host ""

$renamed = 0
$skipped = 0
$failed = 0

foreach ($item in $renameMap.GetEnumerator()) {
    $oldName = $item.Key
    $newName = $item.Value
    
    if (Test-Path $oldName) {
        if (Test-Path $newName) {
            Write-Host "  ⚠️  跳过: $oldName → $newName (目标已存在)" -ForegroundColor Yellow
            $skipped++
        } else {
            try {
                Rename-Item -Path $oldName -NewName $newName -ErrorAction Stop
                Write-Host "  ✅ $oldName → $newName" -ForegroundColor Green
                $renamed++
            } catch {
                Write-Host "  ❌ 失败: $oldName → $newName ($_)" -ForegroundColor Red
                $failed++
            }
        }
    } else {
        Write-Host "  ⏭️  不存在: $oldName" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                    重命名完成统计                              " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ 成功重命名: $renamed 个" -ForegroundColor Green
Write-Host "⚠️  跳过: $skipped 个" -ForegroundColor Yellow
Write-Host "❌ 失败: $failed 个" -ForegroundColor Red
Write-Host ""

if ($renamed -gt 0) {
    Write-Host "📌 重要提示:" -ForegroundColor Yellow
    Write-Host "  1. 启动脚本已重命名,请使用新名称:" -ForegroundColor White
    Write-Host "     .\start_dashboard.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  2. 主程序已重命名:" -ForegroundColor White
    Write-Host "     python dashboard_main.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  3. 需要更新引用这些文件的代码" -ForegroundColor White
    Write-Host "     建议运行: .\update_imports.ps1" -ForegroundColor Cyan
    Write-Host ""
}
