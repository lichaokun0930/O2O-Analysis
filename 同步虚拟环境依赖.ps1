# ========================================
# 同步虚拟环境依赖
# 确保父目录和当前目录的虚拟环境都有必要的依赖
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  同步虚拟环境依赖" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

# 检测虚拟环境
$parentVenv = Join-Path (Split-Path -Parent $scriptDir) ".venv\Scripts\pip.exe"
$currentVenv = Join-Path $scriptDir ".venv\Scripts\pip.exe"

$venvs = @()

if (Test-Path $parentVenv) {
    $venvs += @{
        Name = "父目录虚拟环境"
        Path = $parentVenv
        PythonPath = Join-Path (Split-Path -Parent $scriptDir) ".venv\Scripts\python.exe"
    }
}

if (Test-Path $currentVenv) {
    $venvs += @{
        Name = "当前目录虚拟环境"
        Path = $currentVenv
        PythonPath = Join-Path $scriptDir ".venv\Scripts\python.exe"
    }
}

if ($venvs.Count -eq 0) {
    Write-Host "❌ 未找到任何虚拟环境" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "🔍 发现 $($venvs.Count) 个虚拟环境" -ForegroundColor Yellow
Write-Host ""

# V8.4 生产级必需依赖
$requiredPackages = @(
    "waitress",
    "psutil"
)

foreach ($venv in $venvs) {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  $($venv.Name)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($package in $requiredPackages) {
        Write-Host "📦 检查 $package..." -ForegroundColor Yellow
        
        # 检查是否已安装
        $checkResult = & $venv.PythonPath -c "import $package; print('installed')" 2>&1
        
        if ($checkResult -eq "installed") {
            Write-Host "   ✅ 已安装" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️ 未安装，正在安装..." -ForegroundColor Yellow
            & $venv.Path install $package --quiet
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✅ 安装成功" -ForegroundColor Green
            } else {
                Write-Host "   ❌ 安装失败" -ForegroundColor Red
            }
        }
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  同步完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ 所有虚拟环境已同步" -ForegroundColor Green
Write-Host ""
Write-Host "📋 下一步:" -ForegroundColor Cyan
Write-Host "   1. 运行: .\\启动看板-调试模式.ps1" -ForegroundColor White
Write-Host "   2. 访问: http://localhost:8051" -ForegroundColor White
Write-Host "   3. 查看页面顶部的监控面板" -ForegroundColor White
Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
