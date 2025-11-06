# ==========================================
# 智能门店看板 - 简易启动脚本
# ==========================================

Write-Host "`n正在启动智能门店看板..." -ForegroundColor Cyan

# 停止旧进程
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# 设置环境变量并启动（一行命令）
$env:PYTHONUNBUFFERED="1"; $env:PYTHONIOENCODING="utf-8"; python "智能门店看板_Dash版.py"
