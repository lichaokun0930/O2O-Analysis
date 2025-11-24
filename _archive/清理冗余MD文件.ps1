# 清理冗余Markdown文件
# 创建时间: 2025-11-22
# 说明: 删除已完成的报告、重复的文档、未实施的计划

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "清理冗余Markdown文件" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

$filesToDelete = @(
    # 完成报告类
    "Redis缓存集成完成报告.md",
    "UI_UX优化完成报告.md",
    "启动脚本测试报告.md",
    "导入脚本业务逻辑修复报告.md",
    "文件清理分析报告.md",
    "清理完成报告.md",
    "新电脑配置状态报告.md",
    "requirements追踪系统测试报告.md",
    
    # 重复的使用指南
    "快速开始指南.md",
    "README_Dash版使用指南.md",
    "智能门店经营看板_使用指南.md",
    
    # 未实施计划
    "待升级_Waitress生产服务器.md",
    "后续优化计划.md",
    
    # 重复配置指南
    "数据库配置快速指南.md",
    "requirements追踪-快速开始.md",
    "时段与场景自动生成快速参考.md",
    
    # 临时文档
    "B电脑克隆清单.md",
    "Github推送文件清单.md",
    "完整推送确认清单.md",
    "数据量评估报告.md"
)

Write-Host "📋 将删除以下文件:" -ForegroundColor Yellow
$filesToDelete | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }
Write-Host ""

$confirmation = Read-Host "确认删除? (yes/no)"

if ($confirmation -eq "yes") {
    $deleted = 0
    $notFound = 0
    
    foreach ($file in $filesToDelete) {
        if (Test-Path $file) {
            Remove-Item $file -Force
            Write-Host "✅ 已删除: $file" -ForegroundColor Green
            $deleted++
        } else {
            Write-Host "⚠️  不存在: $file" -ForegroundColor DarkYellow
            $notFound++
        }
    }
    
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host "清理完成!" -ForegroundColor Green
    Write-Host "已删除: $deleted 个文件" -ForegroundColor Green
    Write-Host "未找到: $notFound 个文件" -ForegroundColor Yellow
    Write-Host "===========================================" -ForegroundColor Cyan
} else {
    Write-Host "❌ 已取消" -ForegroundColor Red
}

Write-Host ""
Write-Host "💡 提示: 保留的重要文档包括:" -ForegroundColor Cyan
Write-Host "   - README.md (项目主文档)" -ForegroundColor Gray
Write-Host "   - 【权威】业务逻辑与数据字典完整手册.md (核心业务)" -ForegroundColor Gray
Write-Host "   - 智能门店看板_Dash版使用指南.md (主要指南)" -ForegroundColor Gray
Write-Host "   - 新电脑完整配置指南.md (环境配置)" -ForegroundColor Gray
Write-Host ""
