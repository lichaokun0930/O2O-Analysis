# 智能门店经营看板 - 启动脚本

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "智能门店经营看板 - 生产模式" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 提示: 如需查看详细调试日志，请使用:" -ForegroundColor Gray
Write-Host "   .\启动看板-调试模式.ps1" -ForegroundColor Cyan
Write-Host ""

$pythonExe = Join-Path $scriptDir ".venv\\Scripts\\python.exe"
if (-not (Test-Path $pythonExe)) {
	Write-Warning "未找到虚拟环境，将使用系统 python。"
	$pythonExe = "python"
}

Write-Host "检测已有看板进程..." -ForegroundColor Yellow
$running = Get-CimInstance Win32_Process -Filter "name='python.exe'" -ErrorAction SilentlyContinue |
	Where-Object { $_.CommandLine -match "智能门店看板_Dash版\.py" }

if ($running) {
	$running | ForEach-Object {
		Write-Host "停止PID $($_.ProcessId) -> $($_.CommandLine)" -ForegroundColor DarkYellow
		Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
	}
	Start-Sleep -Seconds 1
} else {
	Write-Host "未发现正在运行的看板实例。" -ForegroundColor DarkGreen
}

Write-Host "正在启动应用..." -ForegroundColor Yellow
Write-Host "访问地址: http://localhost:8050" -ForegroundColor Green
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

& $pythonExe "智能门店看板_Dash版.py"
