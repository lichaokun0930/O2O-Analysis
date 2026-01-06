# ========================================
# 生产级依赖安装脚本 (V8.4)
# 用途: 安装Waitress生产服务器和系统监控依赖
# 适用: 30-200人并发场景
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  生产级依赖安装 (V8.4)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python环境
Write-Host "🔍 检查Python环境..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "❌ 未找到Python，请先安装Python 3.8+" -ForegroundColor Red
    pause
    exit 1
}

$pythonVersion = python --version
Write-Host "✅ Python版本: $pythonVersion" -ForegroundColor Green
Write-Host ""

# 检查虚拟环境
Write-Host "🔍 检查虚拟环境..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "✅ 虚拟环境已存在" -ForegroundColor Green
    Write-Host "🔄 激活虚拟环境..." -ForegroundColor Yellow
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠️ 虚拟环境不存在，将使用全局Python环境" -ForegroundColor Yellow
}
Write-Host ""

# 安装依赖
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  开始安装依赖" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Waitress生产服务器
Write-Host "📦 [1/2] 安装 Waitress 生产服务器..." -ForegroundColor Yellow
Write-Host "   用途: 支持30-200人并发访问" -ForegroundColor Gray
python -m pip install waitress --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Waitress 安装成功" -ForegroundColor Green
} else {
    Write-Host "   ❌ Waitress 安装失败" -ForegroundColor Red
}
Write-Host ""

# 2. psutil系统监控
Write-Host "📦 [2/2] 安装 psutil 系统监控库..." -ForegroundColor Yellow
Write-Host "   用途: 监控CPU、内存、Redis状态" -ForegroundColor Gray
python -m pip install psutil --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ psutil 安装成功" -ForegroundColor Green
} else {
    Write-Host "   ❌ psutil 安装失败" -ForegroundColor Red
}
Write-Host ""

# 验证安装
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  验证安装结果" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔍 检查已安装的包..." -ForegroundColor Yellow
$packages = @("waitress", "psutil")
$allInstalled = $true

foreach ($pkg in $packages) {
    $result = python -c "import $pkg; print($pkg.__version__)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ $pkg : $result" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $pkg : 未安装" -ForegroundColor Red
        $allInstalled = $false
    }
}
Write-Host ""

# 总结
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  安装完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($allInstalled) {
    Write-Host "✅ 所有依赖安装成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 下一步操作:" -ForegroundColor Cyan
    Write-Host "   1. 运行 .\启动看板-调试模式.ps1 启动看板" -ForegroundColor White
    Write-Host "   2. 访问 http://localhost:8051 查看监控面板" -ForegroundColor White
    Write-Host "   3. 运行 python 压力测试_30人.py 测试并发性能" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 生产模式特性:" -ForegroundColor Cyan
    Write-Host "   • Waitress服务器: 8线程, 100连接" -ForegroundColor White
    Write-Host "   • 系统监控面板: 实时显示Redis/CPU/内存状态" -ForegroundColor White
    Write-Host "   • 支持并发: 30-50人 (可扩展至100-200人)" -ForegroundColor White
} else {
    Write-Host "⚠️ 部分依赖安装失败，请检查错误信息" -ForegroundColor Yellow
    Write-Host "   提示: 可能需要管理员权限或网络连接" -ForegroundColor Gray
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
