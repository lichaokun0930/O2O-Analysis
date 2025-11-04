# 智能门店经营看板 - 启动脚本 (PowerShell)
# 使用方法：右键 -> "使用PowerShell运行"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           🏪 智能门店经营看板 - 启动程序                      ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 设置编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# 切换到项目目录
$ProjectDir = "d:\Python1\O2O_Analysis\O2O数据分析\测算模型"
Write-Host "📂 切换到项目目录: $ProjectDir" -ForegroundColor Yellow
Set-Location $ProjectDir

# 检查Python是否可用
Write-Host "🔍 检查Python环境..." -ForegroundColor Yellow
$PythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python已安装: $PythonVersion" -ForegroundColor Green
} else {
    Write-Host "❌ 错误: 未找到Python，请先安装Python" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}

# 检查端口8050是否被占用
Write-Host "🔍 检查端口8050..." -ForegroundColor Yellow
$PortCheck = netstat -ano | findstr :8050
if ($PortCheck) {
    Write-Host "⚠️  警告: 端口8050已被占用，尝试继续..." -ForegroundColor Yellow
    Write-Host "   如果启动失败，请先关闭占用端口的程序" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🚀 正在启动智能门店经营看板..." -ForegroundColor Green
Write-Host "   请等待启动完成，然后在浏览器中访问:" -ForegroundColor Cyan
Write-Host "   http://localhost:8050" -ForegroundColor Cyan
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""

# 启动应用
python "智能门店看板_Dash版.py"

# 应用退出后
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host "⚠️  应用服务器已停止" -ForegroundColor Yellow
Write-Host ""
Read-Host "按Enter键关闭此窗口"
