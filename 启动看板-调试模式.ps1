Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "智能门店经营看板 - 调试模式" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "检测已有看板进程..." -ForegroundColor Gray
$existingProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*订单数据看板*" }

if ($existingProcess) {
    Write-Host "发现正在运行的看板实例, 正在停止..." -ForegroundColor Yellow
    Stop-Process -Id $existingProcess.Id -Force
    Write-Host "已停止现有实例" -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "未发现正在运行的看板实例" -ForegroundColor Gray
}

Write-Host ""
Write-Host "启动调试模式..." -ForegroundColor Yellow
Write-Host "访问地址: http://localhost:8050" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Gray
Write-Host ""

$env:DASH_DEBUG = "true"
& .\.venv\Scripts\python.exe 智能门店看板_Dash版.py
Remove-Item Env:DASH_DEBUG -ErrorAction SilentlyContinue
