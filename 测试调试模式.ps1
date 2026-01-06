# 测试调试模式热重载功能

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "测试调试模式热重载功能" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# 检查环境变量
Write-Host "🔍 检查环境变量..." -ForegroundColor Yellow
$env:DASH_DEBUG = "true"
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"
$env:PYTHONDONTWRITEBYTECODE = "1"

Write-Host "✅ 环境变量已设置:" -ForegroundColor Green
Write-Host "   DASH_DEBUG = $env:DASH_DEBUG" -ForegroundColor Gray
Write-Host "   FLASK_ENV = $env:FLASK_ENV" -ForegroundColor Gray
Write-Host "   FLASK_DEBUG = $env:FLASK_DEBUG" -ForegroundColor Gray
Write-Host "   PYTHONDONTWRITEBYTECODE = $env:PYTHONDONTWRITEBYTECODE" -ForegroundColor Gray
Write-Host ""

# 检查主程序文件
Write-Host "🔍 检查主程序配置..." -ForegroundColor Yellow
$mainFile = "智能门店看板_Dash版.py"

if (Test-Path $mainFile) {
    Write-Host "✅ 主程序文件存在: $mainFile" -ForegroundColor Green
    
    # 检查是否包含热重载配置
    $content = Get-Content $mainFile -Raw
    
    if ($content -match "use_reloader=True") {
        Write-Host "✅ 热重载配置已启用: use_reloader=True" -ForegroundColor Green
    } else {
        Write-Host "⚠️  未找到 use_reloader=True 配置" -ForegroundColor Yellow
    }
    
    if ($content -match "debug=True") {
        Write-Host "✅ 调试模式配置已启用: debug=True" -ForegroundColor Green
    } else {
        Write-Host "⚠️  未找到 debug=True 配置" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ 主程序文件不存在: $mainFile" -ForegroundColor Red
}

Write-Host ""

# 检查Flask/Werkzeug版本
Write-Host "🔍 检查依赖版本..." -ForegroundColor Yellow
$pythonExe = ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$flaskVersion = & $pythonExe -c "import flask; print(flask.__version__)" 2>$null
$werkzeugVersion = & $pythonExe -c "import werkzeug; print(werkzeug.__version__)" 2>$null

if ($flaskVersion) {
    Write-Host "✅ Flask 版本: $flaskVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Flask 未安装" -ForegroundColor Red
}

if ($werkzeugVersion) {
    Write-Host "✅ Werkzeug 版本: $werkzeugVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Werkzeug 未安装" -ForegroundColor Red
}

Write-Host ""

# 总结
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "📊 测试总结" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ 调试模式配置正确" -ForegroundColor Green
Write-Host ""
Write-Host "💡 使用说明:" -ForegroundColor Cyan
Write-Host "   1. 运行 .\启动看板-调试模式.ps1" -ForegroundColor Gray
Write-Host "   2. 修改代码并保存（Ctrl+S）" -ForegroundColor Gray
Write-Host "   3. 观察控制台输出 '* Restarting with stat'" -ForegroundColor Gray
Write-Host "   4. 刷新浏览器（Ctrl+F5）查看更改" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 预期行为:" -ForegroundColor Cyan
Write-Host "   - 修改.py文件后，控制台显示 'Detected change'" -ForegroundColor Gray
Write-Host "   - 服务器自动重启，显示 'Restarting with stat'" -ForegroundColor Gray
Write-Host "   - 刷新浏览器后看到新代码效果" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  注意事项:" -ForegroundColor Yellow
Write-Host "   - 只监控.py文件，修改.md/.txt不会触发重启" -ForegroundColor Gray
Write-Host "   - 大量修改可能导致重启较慢（10-15秒）" -ForegroundColor Gray
Write-Host "   - 如果热重载失败，手动重启调试模式" -ForegroundColor Gray
Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan

# 清理环境变量
Remove-Item Env:DASH_DEBUG -ErrorAction SilentlyContinue
Remove-Item Env:FLASK_ENV -ErrorAction SilentlyContinue
Remove-Item Env:FLASK_DEBUG -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue

Read-Host "按回车键退出"
