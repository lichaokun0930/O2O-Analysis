# 开放看板端口 - 允许局域网访问
# 需要以管理员身份运行

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  智能门店看板 - 防火墙端口配置" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否以管理员身份运行
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ 错误：需要以管理员身份运行此脚本！" -ForegroundColor Red
    Write-Host ""
    Write-Host "请执行以下操作：" -ForegroundColor Yellow
    Write-Host "1. 右键点击PowerShell图标" -ForegroundColor White
    Write-Host "2. 选择'以管理员身份运行'" -ForegroundColor White
    Write-Host "3. 重新运行此脚本" -ForegroundColor White
    Write-Host ""
    pause
    exit
}

Write-Host "✅ 管理员权限确认" -ForegroundColor Green
Write-Host ""

# 检查规则是否已存在
$existingRule = Get-NetFirewallRule -DisplayName "智能门店看板" -ErrorAction SilentlyContinue

if ($existingRule) {
    Write-Host "⚠️  检测到已存在的防火墙规则" -ForegroundColor Yellow
    Write-Host ""
    $choice = Read-Host "是否删除旧规则并重新创建？(Y/N)"
    
    if ($choice -eq 'Y' -or $choice -eq 'y') {
        Remove-NetFirewallRule -DisplayName "智能门店看板" -ErrorAction SilentlyContinue
        Write-Host "✅ 已删除旧规则" -ForegroundColor Green
    } else {
        Write-Host "❌ 操作已取消" -ForegroundColor Red
        pause
        exit
    }
}

Write-Host "🔧 正在配置防火墙规则..." -ForegroundColor Cyan
Write-Host ""

try {
    # 创建入站规则，允许8050端口的TCP连接
    New-NetFirewallRule `
        -DisplayName "智能门店看板" `
        -Description "允许智能门店经营看板的局域网访问（端口8050）" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort 8050 `
        -Action Allow `
        -Enabled True `
        -Profile Domain,Private,Public `
        -ErrorAction Stop
    
    Write-Host "✅ 防火墙规则创建成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  配置详情" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  规则名称: 智能门店看板" -ForegroundColor White
    Write-Host "  端口: 8050 (TCP)" -ForegroundColor White
    Write-Host "  方向: 入站" -ForegroundColor White
    Write-Host "  操作: 允许连接" -ForegroundColor White
    Write-Host "  配置文件: 域/专用/公用 (全部)" -ForegroundColor White
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host ""
    
    # 获取本机IP
    Write-Host "📍 本机网络信息:" -ForegroundColor Cyan
    $localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*" }).IPAddress | Select-Object -First 1
    
    if ($localIP) {
        Write-Host "  本机IP: $localIP" -ForegroundColor Green
        Write-Host ""
        Write-Host "🌐 局域网访问地址:" -ForegroundColor Yellow
        Write-Host "  http://$localIP:8050" -ForegroundColor White
        Write-Host ""
    }
    
    Write-Host "✅ 现在其他设备可以通过局域网访问看板了！" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 使用提示:" -ForegroundColor Cyan
    Write-Host "  1. 确保其他设备连接到同一WiFi" -ForegroundColor White
    Write-Host "  2. 启动智能门店看板" -ForegroundColor White
    Write-Host "  3. 在其他设备浏览器中输入上述地址" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "❌ 配置失败：$($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 手动配置步骤:" -ForegroundColor Yellow
    Write-Host "  1. 打开'控制面板' → 'Windows Defender 防火墙'" -ForegroundColor White
    Write-Host "  2. 点击'高级设置' → '入站规则' → '新建规则'" -ForegroundColor White
    Write-Host "  3. 选择'端口' → TCP → 输入'8050'" -ForegroundColor White
    Write-Host "  4. 选择'允许连接' → 全选网络类型 → 完成" -ForegroundColor White
    Write-Host ""
}

Write-Host "按任意键退出..." -ForegroundColor Gray
pause
