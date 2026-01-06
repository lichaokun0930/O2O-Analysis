# 项目文件清理脚本
# 自动生成于: 2025-12-11 18:45:00

Write-Host '项目文件清理工具' -ForegroundColor Cyan
Write-Host '=' * 80 -ForegroundColor Cyan


# 可以删除的旧版本文档
Write-Host '\n清理: 可以删除的旧版本文档 (41 个)' -ForegroundColor Yellow
Remove-Item "V7.4.2字段引用错误修复.md" -ErrorAction SilentlyContinue
Remove-Item "V7.4快速验证指南.md" -ErrorAction SilentlyContinue
Remove-Item "V7.4评分体系删除说明.md" -ErrorAction SilentlyContinue
Remove-Item "V7.4语法错误修复说明.md" -ErrorAction SilentlyContinue
Remove-Item "V7.5.1性能优化加强版.md" -ErrorAction SilentlyContinue
Remove-Item "V7.5.2异步加载BUG修复.md" -ErrorAction SilentlyContinue
Remove-Item "V7.5性能优化实施说明.md" -ErrorAction SilentlyContinue
Remove-Item "V7.6性能优化进展.md" -ErrorAction SilentlyContinue
Remove-Item "V7.6紧急性能优化方案.md" -ErrorAction SilentlyContinue
Remove-Item "V7.6缓存配置修复说明.md" -ErrorAction SilentlyContinue
Remove-Item "V8.0快速测试指南.md" -ErrorAction SilentlyContinue
Remove-Item "V8.0方案D实施完成报告.md" -ErrorAction SilentlyContinue
Remove-Item "V8.0最终实施报告.md" -ErrorAction SilentlyContinue
Remove-Item "V8.1完整使用指南.md" -ErrorAction SilentlyContinue
Remove-Item "V8.1方案A实施完成报告.md" -ErrorAction SilentlyContinue
Remove-Item "V8.2启动脚本更新说明.md" -ErrorAction SilentlyContinue
Remove-Item "V8.2完整使用指南.md" -ErrorAction SilentlyContinue
Remove-Item "V8.2实施完成报告.md" -ErrorAction SilentlyContinue
Remove-Item "V8.2最终交付说明.md" -ErrorAction SilentlyContinue
Remove-Item "V8.2最终验证报告.md" -ErrorAction SilentlyContinue
Remove-Item "V8.3_vs_V8.4_对比分析.md" -ErrorAction SilentlyContinue
Remove-Item "V8.3完整性能优化方案.md" -ErrorAction SilentlyContinue
Remove-Item "V8.3实施完成报告.md" -ErrorAction SilentlyContinue
Remove-Item "V8.4_README.md" -ErrorAction SilentlyContinue
Remove-Item "V8.4交付总结.md" -ErrorAction SilentlyContinue
Remove-Item "V8.4交付清单.md" -ErrorAction SilentlyContinue
Remove-Item "V8.4企业级缓存实施报告.md" -ErrorAction SilentlyContinue
Remove-Item "V8.4实施清单.md" -ErrorAction SilentlyContinue
Remove-Item "V8.4实际数据规模评估.md" -ErrorAction SilentlyContinue
Remove-Item "V8.4快速上手指南.md" -ErrorAction SilentlyContinue
Remove-Item "V8.4快速启动指南.md" -ErrorAction SilentlyContinue
Remove-Item "V8.4最终确认.md" -ErrorAction SilentlyContinue
Remove-Item "V8.4最终验证报告.md" -ErrorAction SilentlyContinue
Remove-Item "V8.4生产级升级完成报告.md" -ErrorAction SilentlyContinue
Remove-Item "V8.5企业级优化规划.md" -ErrorAction SilentlyContinue
Remove-Item "V8.5基础设施优化完成报告.md" -ErrorAction SilentlyContinue
Remove-Item "V8.5快速启动指南.md" -ErrorAction SilentlyContinue
Remove-Item "V8.6-V8.7完整优化实施报告.md" -ErrorAction SilentlyContinue
Remove-Item "V8.6.2商品健康分析性能优化方案.md" -ErrorAction SilentlyContinue
Remove-Item "V8.6今日必做性能优化完成报告.md" -ErrorAction SilentlyContinue
Remove-Item "V8.6今日必做性能优化方案.md" -ErrorAction SilentlyContinue

# 可以删除的测试脚本
Write-Host '\n清理: 可以删除的测试脚本 (21 个)' -ForegroundColor Yellow
Remove-Item "测试html_Style修复.py" -ErrorAction SilentlyContinue
Remove-Item "测试Redis自动启动.py" -ErrorAction SilentlyContinue
Remove-Item "测试V8.0启动.py" -ErrorAction SilentlyContinue
Remove-Item "测试V8.1后台任务.py" -ErrorAction SilentlyContinue
Remove-Item "测试V8.3智能缓存.py" -ErrorAction SilentlyContinue
Remove-Item "测试V8.4分层缓存.py" -ErrorAction SilentlyContinue
Remove-Item "测试V8.6今日必做性能优化.py" -ErrorAction SilentlyContinue
Remove-Item "测试V8.6完整优化.py" -ErrorAction SilentlyContinue
Remove-Item "测试V8.8-V8.9优化.py" -ErrorAction SilentlyContinue
Remove-Item "测试今日必做完整流程.py" -ErrorAction SilentlyContinue
Remove-Item "测试今日必做实际性能.py" -ErrorAction SilentlyContinue
Remove-Item "测试全部数据模式.py" -ErrorAction SilentlyContinue
Remove-Item "测试利润率计算.py" -ErrorAction SilentlyContinue
Remove-Item "测试动态门槛效果.py" -ErrorAction SilentlyContinue
Remove-Item "测试启动日志输出.py" -ErrorAction SilentlyContinue
Remove-Item "测试监控面板.py" -ErrorAction SilentlyContinue
Remove-Item "测试策略引流动态门槛.py" -ErrorAction SilentlyContinue
Remove-Item "验证V7.4评分删除.py" -ErrorAction SilentlyContinue
Remove-Item "验证V8.4集成.py" -ErrorAction SilentlyContinue
Remove-Item "验证利润额公式.py" -ErrorAction SilentlyContinue
Remove-Item "验证基础设施优化.py" -ErrorAction SilentlyContinue

# 可以删除的临时文件
Write-Host '\n清理: 可以删除的临时文件 (2 个)' -ForegroundColor Yellow
Remove-Item ".env.template" -ErrorAction SilentlyContinue
Remove-Item "debug_output.txt" -ErrorAction SilentlyContinue

Write-Host '\n清理完成!' -ForegroundColor Green
