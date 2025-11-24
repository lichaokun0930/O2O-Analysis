# 重新导入铜山万达数据 - 包含新字段
Write-Host "================================" -ForegroundColor Cyan
Write-Host "  重新导入铜山万达数据" -ForegroundColor Yellow
Write-Host "  包含新增的4个字段" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 运行导入脚本
python 智能导入门店数据.py

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
