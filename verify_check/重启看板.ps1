# 清除缓存并重启看板
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "清除缓存并重启看板" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan

# 1. 清除缓存
Write-Host "`n[1] 清除缓存..." -ForegroundColor Green
Remove-Item "学习数据仓库\cache\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "学习数据仓库\uploaded_data\*" -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "   ✅ 缓存已清除" -ForegroundColor Green

# 2. 停止旧进程
Write-Host "`n[2] 停止旧进程..." -ForegroundColor Green
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 3. 启动看板
Write-Host "`n[3] 启动看板..." -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "🔄 正在启动智能门店经营看板..." -ForegroundColor Green
python 智能门店看板_Dash版.py
