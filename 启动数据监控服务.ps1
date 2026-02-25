# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    启动热文件夹监控服务

.DESCRIPTION
    监控 data/inbox 目录，新文件自动导入数据库
    - 导入成功 → 移动到 data/processed
    - 导入失败 → 移动到 data/failed

.EXAMPLE
    .\启动数据监控服务.ps1
#>

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 颜色输出函数
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# 显示横幅
Write-ColorOutput "`n========================================" "Cyan"
Write-ColorOutput "   📂 热文件夹监控服务" "Cyan"
Write-ColorOutput "========================================`n" "Cyan"

# 切换到项目目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 创建必要的目录
$inboxDir = ".\data\inbox"
$processedDir = ".\data\processed"
$failedDir = ".\data\failed"

if (-not (Test-Path $inboxDir)) {
    New-Item -ItemType Directory -Path $inboxDir -Force | Out-Null
    Write-ColorOutput "📁 创建目录: $inboxDir" "Green"
}
if (-not (Test-Path $processedDir)) {
    New-Item -ItemType Directory -Path $processedDir -Force | Out-Null
    Write-ColorOutput "📁 创建目录: $processedDir" "Green"
}
if (-not (Test-Path $failedDir)) {
    New-Item -ItemType Directory -Path $failedDir -Force | Out-Null
    Write-ColorOutput "📁 创建目录: $failedDir" "Green"
}

Write-ColorOutput "" "White"
Write-ColorOutput "📂 监控目录: $(Resolve-Path $inboxDir)" "Yellow"
Write-ColorOutput "✅ 成功目录: $(Resolve-Path $processedDir)" "Green"
Write-ColorOutput "❌ 失败目录: $(Resolve-Path $failedDir)" "Red"
Write-ColorOutput "" "White"
Write-ColorOutput "💡 使用方法:" "Cyan"
Write-ColorOutput "   将 Excel 文件放入 data\inbox 目录即可自动导入" "White"
Write-ColorOutput "" "White"

# 激活虚拟环境
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    . .\.venv\Scripts\Activate.ps1
    Write-ColorOutput "🔧 已激活虚拟环境" "Green"
} else {
    Write-ColorOutput "⚠️ 未找到虚拟环境，使用系统 Python" "Yellow"
}

# 检查 watchdog 是否安装
$watchdogInstalled = python -c "import watchdog" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-ColorOutput "" "White"
    Write-ColorOutput "⚠️ watchdog 未安装，将使用轮询模式" "Yellow"
    Write-ColorOutput "   如需实时监控，请运行: pip install watchdog" "Gray"
    Write-ColorOutput "" "White"
}

Write-ColorOutput "🚀 启动监控服务...`n" "Cyan"

# 启动监控服务
python -m services.data_watcher_service

Write-ColorOutput "`n监控服务已停止" "Yellow"
Read-Host "按回车键退出"
