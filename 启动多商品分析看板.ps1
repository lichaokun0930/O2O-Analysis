# 启动多商品订单引导分析看板（含商品分类分析）
# 使用说明: 在PowerShell中运行此脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "启动多商品订单引导分析看板" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "✨ 新功能: 已集成商品分类结构竞争力分析!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 核心模块:" -ForegroundColor Yellow
Write-Host "  1️⃣  多商品订单引导分析" -ForegroundColor White
Write-Host "  2️⃣  商品分类结构竞争力分析 (NEW!)" -ForegroundColor Green
Write-Host "  3️⃣  满减策略优化" -ForegroundColor White
Write-Host ""

# 启动看板
streamlit run "多商品订单引导分析看板.py" --server.port 8503
