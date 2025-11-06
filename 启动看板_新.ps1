# -*- coding: utf-8 -*-
# 启动智能门店经营看板 (Dash版)

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "智能门店经营看板 - Dash版" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python环境
Write-Host "正在检查Python环境..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "未找到Python，请先安装Python 3.8+" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "正在启动Dash应用..." -ForegroundColor Yellow
Write-Host "   访问地址: http://localhost:8050" -ForegroundColor Green
Write-Host "   按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""

# 先停止旧进程
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

# 启动应用
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$appFile = Join-Path $scriptPath "智能门店看板_Dash版.py"

if (Test-Path $appFile) {
    python -u $appFile
} else {
    Write-Host "错误: 找不到应用文件 $appFile" -ForegroundColor Red
    Read-Host "按回车键退出"
}
