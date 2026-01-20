# 验证客户流失分析缓存优化
# V8.10.1 性能优化验证脚本

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🧪 V8.10.1 客户流失分析缓存优化验证" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 设置UTF-8编码
$env:PYTHONIOENCODING = 'utf-8'

Write-Host "📋 验证内容:" -ForegroundColor Yellow
Write-Host "   1. Redis缓存功能正常" -ForegroundColor White
Write-Host "   2. 首次调用正常计算并缓存" -ForegroundColor White
Write-Host "   3. 二次调用命中缓存，性能提升" -ForegroundColor White
Write-Host "   4. 缓存数据一致性验证" -ForegroundColor White
Write-Host ""

Write-Host "🚀 开始测试..." -ForegroundColor Green
Write-Host ""

# 运行测试脚本
python 测试客户流失分析缓存.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ 验证完成" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "💡 下一步:" -ForegroundColor Yellow
Write-Host "   1. 启动看板（调试模式）: .\启动看板-调试模式.ps1" -ForegroundColor White
Write-Host "   2. 选择门店，进入'今日必做'Tab" -ForegroundColor White
Write-Host "   3. 查看'经营诊断'，记录首次加载时间" -ForegroundColor White
Write-Host "   4. 刷新页面，再次查看，验证缓存命中" -ForegroundColor White
Write-Host "   5. 查看日志中的'缓存命中'/'缓存未命中'信息" -ForegroundColor White
Write-Host ""

Write-Host "📊 预期效果:" -ForegroundColor Yellow
Write-Host "   首次加载: ~85秒（缓存未命中）" -ForegroundColor White
Write-Host "   再次加载: <3秒（缓存命中）" -ForegroundColor White
Write-Host "   性能提升: 96.5%" -ForegroundColor Green
Write-Host ""

Read-Host "按Enter键退出"
