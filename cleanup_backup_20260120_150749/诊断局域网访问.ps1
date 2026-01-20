# 诊断智能门店看板局域网访问问题
# 自动检测并修复常见问题

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   智能门店看板 - 局域网访问诊断工具 V1.0" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 检查1: 是否以管理员身份运行
Write-Host "[检查 1/5] 检查管理员权限..." -ForegroundColor Cyan
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    Write-Host "  ✅ 已以管理员身份运行" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  未以管理员身份运行，某些检查可能受限" -ForegroundColor Yellow
}
Write-Host ""

# 检查2: 获取本机IP地址
Write-Host "[检查 2/5] 获取本机IP地址..." -ForegroundColor Cyan
$localIPs = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.IPAddress -notlike "127.*" -and 
    $_.IPAddress -notlike "169.*" -and
    $_.PrefixOrigin -eq "Dhcp" -or $_.PrefixOrigin -eq "Manual"
}

if ($localIPs) {
    foreach ($ip in $localIPs) {
        Write-Host "  ✅ 本机IP: $($ip.IPAddress)" -ForegroundColor Green
    }
    $primaryIP = $localIPs[0].IPAddress
} else {
    Write-Host "  ❌ 未检测到有效的局域网IP地址" -ForegroundColor Red
    Write-Host "     请检查网络连接是否正常" -ForegroundColor Yellow
    $primaryIP = $null
}
Write-Host ""

# 检查3: 防火墙规则
Write-Host "[检查 3/5] 检查防火墙规则..." -ForegroundColor Cyan
$firewallRule = Get-NetFirewallRule -DisplayName "智能门店看板" -ErrorAction SilentlyContinue

if ($firewallRule) {
    if ($firewallRule.Enabled -eq "True") {
        Write-Host "  ✅ 防火墙规则已存在且已启用" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  防火墙规则存在但未启用" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ 未找到防火墙规则" -ForegroundColor Red
    Write-Host "     局域网访问将被Windows防火墙阻止！" -ForegroundColor Yellow
}
Write-Host ""

# 检查4: 8050端口是否被占用
Write-Host "[检查 4/5] 检查8050端口状态..." -ForegroundColor Cyan
$portInUse = Get-NetTCPConnection -LocalPort 8050 -ErrorAction SilentlyContinue

if ($portInUse) {
    Write-Host "  ✅ 端口8050正在被使用（看板可能正在运行）" -ForegroundColor Green
    $process = Get-Process -Id $portInUse[0].OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "     进程: $($process.ProcessName) (PID: $($process.Id))" -ForegroundColor White
    }
} else {
    Write-Host "  ⚠️  端口8050未被占用（看板未启动）" -ForegroundColor Yellow
}
Write-Host ""

# 检查5: 网络配置文件
Write-Host "[检查 5/5] 检查网络配置文件..." -ForegroundColor Cyan
$networkProfile = Get-NetConnectionProfile -ErrorAction SilentlyContinue
if ($networkProfile) {
    Write-Host "  网络名称: $($networkProfile.Name)" -ForegroundColor White
    Write-Host "  网络类型: $($networkProfile.NetworkCategory)" -ForegroundColor White
    
    if ($networkProfile.NetworkCategory -eq "Public") {
        Write-Host "  ⚠️  网络类型为'公用'，可能影响局域网访问" -ForegroundColor Yellow
        Write-Host "     建议将网络类型改为'专用'" -ForegroundColor Yellow
    } else {
        Write-Host "  ✅ 网络类型合适" -ForegroundColor Green
    }
} else {
    Write-Host "  ⚠️  无法获取网络配置信息" -ForegroundColor Yellow
}
Write-Host ""

# ==================== 诊断总结 ====================
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   诊断总结" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$hasIssues = $false

if (-not $primaryIP) {
    Write-Host "❌ 问题1: 未检测到有效的局域网IP" -ForegroundColor Red
    Write-Host "   解决方案: 检查网络连接，确保已连接到WiFi或有线网络" -ForegroundColor Yellow
    Write-Host ""
    $hasIssues = $true
}

if (-not $firewallRule) {
    Write-Host "❌ 问题2: 防火墙未配置 (最常见问题)" -ForegroundColor Red
    Write-Host "   解决方案: 运行'配置防火墙.ps1'脚本配置防火墙规则" -ForegroundColor Yellow
    Write-Host ""
    $hasIssues = $true
    
    if ($isAdmin) {
        Write-Host "💡 是否立即配置防火墙？" -ForegroundColor Cyan
        $choice = Read-Host "   输入 Y 自动配置，输入 N 跳过 (Y/N)"
        
        if ($choice -eq 'Y' -or $choice -eq 'y') {
            Write-Host ""
            Write-Host "🔧 正在配置防火墙..." -ForegroundColor Cyan
            try {
                New-NetFirewallRule `
                    -DisplayName "智能门店看板" `
                    -Description "允许智能门店经营看板的局域网访问（端口8050）" `
                    -Direction Inbound `
                    -Protocol TCP `
                    -LocalPort 8050 `
                    -Action Allow `
                    -Enabled True `
                    -Profile Domain,Private,Public `
                    -ErrorAction Stop | Out-Null
                
                Write-Host "  ✅ 防火墙规则创建成功！" -ForegroundColor Green
                Write-Host ""
            } catch {
                Write-Host "  ❌ 配置失败: $($_.Exception.Message)" -ForegroundColor Red
                Write-Host ""
            }
        }
    }
}

if (-not $portInUse) {
    Write-Host "⚠️  提醒: 看板程序未启动" -ForegroundColor Yellow
    Write-Host "   请双击'启动看板.bat'启动程序" -ForegroundColor Yellow
    Write-Host ""
}

if (-not $hasIssues -and $portInUse) {
    Write-Host "✅ 未发现明显问题，局域网访问应该正常！" -ForegroundColor Green
    Write-Host ""
}

# ==================== 访问信息 ====================
if ($primaryIP) {
    Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "   访问地址" -ForegroundColor Yellow
    Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  📍 本机访问:" -ForegroundColor Cyan
    Write-Host "     http://localhost:8050" -ForegroundColor White
    Write-Host ""
    Write-Host "  🌐 局域网访问 (其他设备):" -ForegroundColor Cyan
    Write-Host "     http://$primaryIP:8050" -ForegroundColor Green
    Write-Host ""
    Write-Host "  💡 使用步骤:" -ForegroundColor Cyan
    Write-Host "     1. 确保看板程序已启动（双击'启动看板.bat'）" -ForegroundColor White
    Write-Host "     2. 确保其他设备连接到同一WiFi" -ForegroundColor White
    Write-Host "     3. 在其他设备浏览器中输入上述地址" -ForegroundColor White
    Write-Host ""
}

# ==================== 故障排查建议 ====================
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   如果仍然无法访问，请尝试以下步骤" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  1️⃣  关闭防火墙测试" -ForegroundColor Cyan
Write-Host "     临时关闭Windows防火墙，测试是否能访问" -ForegroundColor White
Write-Host "     如果可以，说明是防火墙配置问题" -ForegroundColor White
Write-Host ""
Write-Host "  2️⃣  检查杀毒软件" -ForegroundColor Cyan
Write-Host "     某些杀毒软件可能阻止端口访问" -ForegroundColor White
Write-Host "     尝试暂时禁用杀毒软件测试" -ForegroundColor White
Write-Host ""
Write-Host "  3️⃣  检查路由器设置" -ForegroundColor Cyan
Write-Host "     确认路由器未开启AP隔离功能" -ForegroundColor White
Write-Host "     AP隔离会阻止设备间互相访问" -ForegroundColor White
Write-Host ""
Write-Host "  4️⃣  Ping测试连通性" -ForegroundColor Cyan
Write-Host "     在其他设备上ping本机IP: ping $primaryIP" -ForegroundColor White
Write-Host "     如果ping不通，说明网络层不通" -ForegroundColor White
Write-Host ""
Write-Host "  5️⃣  查看详细日志" -ForegroundColor Cyan
Write-Host "     启动看板时，注意控制台输出的IP地址" -ForegroundColor White
Write-Host "     确认是否正确绑定到0.0.0.0:8050" -ForegroundColor White
Write-Host ""

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
