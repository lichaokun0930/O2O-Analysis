#!/usr/bin/env pwsh
# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    启动智能门店看板 - 调试模式

.DESCRIPTION
    以调试模式启动看板，显示详细的错误堆栈和调试日志
    适用场景：
    - 开发新功能
    - 排查错误
    - 查看详细日志

.NOTES
    Author: AI Assistant
    Version: 1.0
    调试模式特性：
    ✅ 详细的错误堆栈信息
    ✅ 实时显示所有回调日志
    ✅ 代码热重载（保存后自动刷新）
    ⚠️ 性能略低，不建议生产环境使用
#>

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "智能门店经营看板 - 调试模式" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# 检测已有看板进程
Write-Host "检测已有看板进程..." -ForegroundColor Gray
$existingProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*智能门店*" -or 
    (Get-NetTCPConnection -LocalPort 8050 -State Listen -ErrorAction SilentlyContinue).OwningProcess -contains $_.Id
}

if ($existingProcess) {
    Write-Host "⚠️  发现正在运行的看板实例 (PID: $($existingProcess.Id))" -ForegroundColor Yellow
    Write-Host "是否停止现有实例并启动调试模式? (Y/N): " -ForegroundColor Yellow -NoNewline
    $choice = Read-Host
    if ($choice -eq 'Y' -or $choice -eq 'y') {
        Stop-Process -Id $existingProcess.Id -Force
        Write-Host "✅ 已停止现有实例" -ForegroundColor Green
        Start-Sleep -Seconds 2
    } else {
        Write-Host "❌ 取消启动" -ForegroundColor Red
        exit 0
    }
} else {
    Write-Host "未发现正在运行的看板实例。" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🐛 启动调试模式..." -ForegroundColor Yellow
Write-Host "   ✓ 详细错误堆栈" -ForegroundColor Gray
Write-Host "   ✓ 回调函数日志" -ForegroundColor Gray
Write-Host "   ✓ 实时代码重载" -ForegroundColor Gray
Write-Host ""
Write-Host "访问地址: http://localhost:8050" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Gray
Write-Host ""

# 设置调试环境变量
$env:DASH_DEBUG = "true"

# 激活虚拟环境并启动
& .\.venv\Scripts\python.exe "智能门店看板_Dash版.py"

# 清理环境变量
Remove-Item Env:DASH_DEBUG -ErrorAction SilentlyContinue
