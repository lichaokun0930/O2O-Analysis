# 诊断工具快捷启动脚本

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

# 虚拟环境在父目录
$parentDir = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $parentDir ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    # 备选：当前目录的.venv
    $pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"
}
if (-not (Test-Path $pythonExe)) {
    Write-Warning "未找到虚拟环境，将使用系统 python。"
    $pythonExe = "python"
}

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "诊断工具菜单" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "请选择要运行的诊断工具:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. 启动自检（完整报告）" -ForegroundColor White
Write-Host "  2. 今日必做性能诊断" -ForegroundColor White
Write-Host "  3. Redis缓存诊断" -ForegroundColor White
Write-Host "  4. 数据库连接诊断" -ForegroundColor White
Write-Host "  5. 退出" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选项 (1-5)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "运行启动自检..." -ForegroundColor Cyan
        & $pythonExe "启动自检.py"
    }
    "2" {
        Write-Host ""
        Write-Host "运行今日必做性能诊断..." -ForegroundColor Cyan
        & $pythonExe "诊断今日必做性能.py"
    }
    "3" {
        Write-Host ""
        Write-Host "运行Redis缓存诊断..." -ForegroundColor Cyan
        & $pythonExe "通用模块诊断工具.py" "--example" "redis"
    }
    "4" {
        Write-Host ""
        Write-Host "运行数据库连接诊断..." -ForegroundColor Cyan
        & $pythonExe "通用模块诊断工具.py" "--example" "database"
    }
    "5" {
        Write-Host ""
        Write-Host "退出" -ForegroundColor Gray
        exit
    }
    default {
        Write-Host ""
        Write-Host "无效选项，请重新运行脚本" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
