#!/usr/bin/env pwsh
# 智能门店看板启动脚本 - Python 3.11 环境
# 用途：使用 Python 3.11 虚拟环境启动 Dash 看板，确保 PandasAI/RAG 依赖可用

$ErrorActionPreference = "Stop"

Write-Host "🚀 智能门店经营看板 - 启动中..." -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# 检查 Python 3.11 虚拟环境
$venvPath = Join-Path $PSScriptRoot ".venv311"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Host "❌ Python 3.11 虚拟环境未找到！" -ForegroundColor Red
    Write-Host "   请先运行以下命令创建虚拟环境：" -ForegroundColor Yellow
    Write-Host "   py -3.11 -m venv .venv311" -ForegroundColor Yellow
    Write-Host "   .\.venv311\Scripts\python.exe -m pip install pandasai chromadb sentence-transformers torch dash dash-bootstrap-components plotly" -ForegroundColor Yellow
    exit 1
}

# 显示 Python 版本
Write-Host "✅ Python 环境：" -ForegroundColor Green
& $pythonExe --version

# 检查关键依赖
Write-Host "`n📦 检查关键依赖..." -ForegroundColor Cyan
$dependencies = @("pandasai", "chromadb", "sentence_transformers", "torch", "dash")
$missingDeps = @()

foreach ($dep in $dependencies) {
    $result = & $pythonExe -c "import $dep; print('✓')" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $missingDeps += $dep
        Write-Host "   ❌ $dep 未安装" -ForegroundColor Red
    } else {
        Write-Host "   ✅ $dep" -ForegroundColor Green
    }
}

if ($missingDeps.Count -gt 0) {
    Write-Host "`n❌ 缺少以下依赖：$($missingDeps -join ', ')" -ForegroundColor Red
    Write-Host "   请运行以下命令安装：" -ForegroundColor Yellow
    Write-Host "   .\.venv311\Scripts\python.exe -m pip install $($missingDeps -join ' ')" -ForegroundColor Yellow
    exit 1
}

# 启动看板
Write-Host "`n🌐 启动智能门店看板..." -ForegroundColor Cyan
Write-Host "   访问地址: http://localhost:8050" -ForegroundColor Green
Write-Host "   按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host ""

# 切换到脚本目录并运行看板
Set-Location $PSScriptRoot
& $pythonExe "智能门店看板_Dash版.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ 看板启动失败，退出码: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
