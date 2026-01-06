# 验证生产服务器升级脚本
# 用途: 检查Waitress配置是否已升级到阶段2（16线程，支持100-200人）

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " 验证生产服务器升级 - V8.10.1" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# 检查主程序文件
$mainFile = ".\智能门店看板_Dash版.py"

if (-not (Test-Path $mainFile)) {
    Write-Host "❌ 错误: 找不到主程序文件" -ForegroundColor Red
    Write-Host "   文件: $mainFile" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ 找到主程序文件" -ForegroundColor Green
Write-Host ""

# 读取文件内容
$content = Get-Content $mainFile -Raw -Encoding UTF8

# 检查关键配置
Write-Host "🔍 检查Waitress配置..." -ForegroundColor Cyan
Write-Host ""

# 检查线程数
if ($content -match "threads=16") {
    Write-Host "✅ 线程数: 16 (阶段2配置)" -ForegroundColor Green
    $threadsOK = $true
} elseif ($content -match "threads=8") {
    Write-Host "❌ 线程数: 8 (阶段1配置，需要升级)" -ForegroundColor Red
    $threadsOK = $false
} else {
    Write-Host "⚠️ 线程数: 未找到配置" -ForegroundColor Yellow
    $threadsOK = $false
}

# 检查连接数
if ($content -match "connection_limit=200") {
    Write-Host "✅ 连接数: 200 (阶段2配置)" -ForegroundColor Green
    $connectionsOK = $true
} elseif ($content -match "connection_limit=100") {
    Write-Host "❌ 连接数: 100 (阶段1配置，需要升级)" -ForegroundColor Red
    $connectionsOK = $false
} else {
    Write-Host "⚠️ 连接数: 未找到配置" -ForegroundColor Yellow
    $connectionsOK = $false
}

# 检查超时时间
if ($content -match "channel_timeout=180") {
    Write-Host "✅ 超时时间: 180秒/3分钟 (阶段2配置)" -ForegroundColor Green
    $timeoutOK = $true
} elseif ($content -match "channel_timeout=120") {
    Write-Host "❌ 超时时间: 120秒/2分钟 (阶段1配置，需要升级)" -ForegroundColor Red
    $timeoutOK = $false
} else {
    Write-Host "⚠️ 超时时间: 未找到配置" -ForegroundColor Yellow
    $timeoutOK = $false
}

# 检查启动日志
if ($content -match "100-200人并发") {
    Write-Host "✅ 启动日志: 显示'100-200人并发'" -ForegroundColor Green
    $logOK = $true
} elseif ($content -match "30-50人并发") {
    Write-Host "❌ 启动日志: 显示'30-50人并发' (需要更新)" -ForegroundColor Red
    $logOK = $false
} else {
    Write-Host "⚠️ 启动日志: 未找到并发人数说明" -ForegroundColor Yellow
    $logOK = $false
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " 验证结果" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# 汇总结果
$allOK = $threadsOK -and $connectionsOK -and $timeoutOK -and $logOK

if ($allOK) {
    Write-Host "🎉 验证通过！" -ForegroundColor Green
    Write-Host ""
    Write-Host "配置状态:" -ForegroundColor Cyan
    Write-Host "  • 线程数: 16 ✅" -ForegroundColor Green
    Write-Host "  • 连接数: 200 ✅" -ForegroundColor Green
    Write-Host "  • 超时: 3分钟 ✅" -ForegroundColor Green
    Write-Host "  • 并发支持: 100-200人 ✅" -ForegroundColor Green
    Write-Host ""
    Write-Host "当前配置: 阶段2 (企业级)" -ForegroundColor Green
    Write-Host "适用场景: 100-200人并发访问" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步:" -ForegroundColor Cyan
    Write-Host "  1. 重启看板验证: .\启动看板.ps1" -ForegroundColor White
    Write-Host "  2. 检查启动日志确认配置" -ForegroundColor White
    Write-Host "  3. 可选: 运行压力测试 python 压力测试_30人.py 100" -ForegroundColor White
} else {
    Write-Host "❌ 验证失败！" -ForegroundColor Red
    Write-Host ""
    Write-Host "配置状态:" -ForegroundColor Cyan
    if ($threadsOK) {
        Write-Host "  • 线程数: 16 ✅" -ForegroundColor Green
    } else {
        Write-Host "  • 线程数: 需要升级 ❌" -ForegroundColor Red
    }
    if ($connectionsOK) {
        Write-Host "  • 连接数: 200 ✅" -ForegroundColor Green
    } else {
        Write-Host "  • 连接数: 需要升级 ❌" -ForegroundColor Red
    }
    if ($timeoutOK) {
        Write-Host "  • 超时: 3分钟 ✅" -ForegroundColor Green
    } else {
        Write-Host "  • 超时: 需要升级 ❌" -ForegroundColor Red
    }
    if ($logOK) {
        Write-Host "  • 并发支持: 100-200人 ✅" -ForegroundColor Green
    } else {
        Write-Host "  • 并发支持: 需要更新 ❌" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "当前配置: 阶段1 (基础级)" -ForegroundColor Yellow
    Write-Host "适用场景: 30-50人并发访问" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "解决方案:" -ForegroundColor Cyan
    Write-Host "  请查看文档: V8.10.1_生产服务器升级报告.md" -ForegroundColor White
    Write-Host "  或手动修改配置文件" -ForegroundColor White
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# 返回状态码
if ($allOK) {
    exit 0
} else {
    exit 1
}
