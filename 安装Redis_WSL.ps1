# ================================================================
#          WSL Redis 一键安装脚本
# ================================================================

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "          WSL Redis 一键安装和启动" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

# 检查WSL状态
Write-Host "📋 检查WSL状态..." -ForegroundColor Yellow
$wslCheck = wsl --status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ WSL未正确配置" -ForegroundColor Red
    Write-Host "请先运行: wsl --install" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ WSL已就绪`n" -ForegroundColor Green

# 在WSL中安装Redis
Write-Host "📦 在WSL中安装Redis..." -ForegroundColor Yellow
Write-Host "执行命令: sudo apt update && sudo apt install -y redis-server`n" -ForegroundColor Gray

wsl bash -c @"
echo '正在更新包列表...'
sudo apt update -qq
echo '正在安装Redis...'
sudo apt install -y redis-server
echo '✅ Redis安装完成'
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Redis安装失败" -ForegroundColor Red
    exit 1
}

# 启动Redis服务
Write-Host "`n🚀 启动Redis服务..." -ForegroundColor Yellow
wsl bash -c "sudo service redis-server start"

# 等待启动
Start-Sleep -Seconds 2

# 测试连接
Write-Host "`n🧪 测试Redis连接..." -ForegroundColor Yellow
$testResult = wsl bash -c "redis-cli ping"
if ($testResult -match "PONG") {
    Write-Host "✅ Redis运行正常!`n" -ForegroundColor Green
} else {
    Write-Host "⚠️  Redis可能未正常启动" -ForegroundColor Yellow
}

# 显示信息
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "          Redis 服务信息" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  连接地址: localhost:6379" -ForegroundColor White
Write-Host "  状态: 运行中" -ForegroundColor Green
Write-Host "`n  常用命令:" -ForegroundColor Yellow
Write-Host "    停止: wsl sudo service redis-server stop" -ForegroundColor Gray
Write-Host "    重启: wsl sudo service redis-server restart" -ForegroundColor Gray
Write-Host "    状态: wsl sudo service redis-server status" -ForegroundColor Gray
Write-Host "    测试: wsl redis-cli ping" -ForegroundColor Gray
Write-Host "================================================================`n" -ForegroundColor Cyan
