@echo off
chcp 65001 >nul
title 诊断局域网访问
color 0E

echo.
echo ================================================================
echo          智能门店看板 - 局域网访问诊断工具
echo ================================================================
echo.

echo [1/5] 检查管理员权限...
net session >nul 2>&1
if %errorlevel% == 0 (
    echo   [OK] 已以管理员身份运行
) else (
    echo   [WARN] 未以管理员身份运行，某些检查可能受限
)

echo.
echo [2/5] 获取本机IP地址...
REM 优先获取192.168或10.开头的局域网IP（排除虚拟适配器如26.x.x.x）
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4" ^| findstr "192.168 10."') do (
    set IP=%%a
    goto :found_ip
)
REM 如果没找到，尝试获取任意IPv4
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4"') do (
    set IP=%%a
    goto :found_ip
)
:found_ip
set IP=%IP:~1%
if defined IP (
    echo   [OK] 本机局域网IP: %IP%
) else (
    echo   [ERROR] 未检测到有效的局域网IP地址
    echo         请检查网络连接是否正常
)

echo.
echo [3/5] 检查防火墙规则...
powershell -NoProfile -Command "if (Get-NetFirewallRule -DisplayName '智能门店看板' -ErrorAction SilentlyContinue) { Write-Host '  [OK] 防火墙规则已存在且已启用' -ForegroundColor Green } else { Write-Host '  [ERROR] 未找到防火墙规则' -ForegroundColor Red; Write-Host '         局域网访问将被Windows防火墙阻止！' -ForegroundColor Yellow }"

echo.
echo [4/5] 检查8050端口状态...
netstat -an | findstr ":8050" >nul 2>&1
if %errorlevel% == 0 (
    echo   [OK] 端口8050正在被使用 ^(看板可能正在运行^)
) else (
    echo   [WARN] 端口8050未被占用 ^(看板未启动^)
)

echo.
echo [5/5] 检查网络类型...
powershell -NoProfile -Command "$profile = Get-NetConnectionProfile -ErrorAction SilentlyContinue; if ($profile) { Write-Host \"  网络名称: $($profile.Name)\" -ForegroundColor White; Write-Host \"  网络类型: $($profile.NetworkCategory)\" -ForegroundColor White; if ($profile.NetworkCategory -eq 'Public') { Write-Host '  [WARN] 网络类型为公用，可能影响局域网访问' -ForegroundColor Yellow } else { Write-Host '  [OK] 网络类型合适' -ForegroundColor Green } } else { Write-Host '  [WARN] 无法获取网络配置信息' -ForegroundColor Yellow }"

echo.
echo ================================================================
echo                     诊断总结
echo ================================================================
echo.

REM 检查是否有防火墙问题
powershell -NoProfile -Command "if (-not (Get-NetFirewallRule -DisplayName '智能门店看板' -ErrorAction SilentlyContinue)) { Write-Host '[ERROR] 问题: 防火墙未配置 (最常见问题)' -ForegroundColor Red; Write-Host '        解决方案: 以管理员身份运行 一键配置局域网访问.bat' -ForegroundColor Yellow; exit 1 } else { Write-Host '[OK] 未发现明显问题' -ForegroundColor Green }"

echo.
echo ================================================================
echo                    访问地址
echo ================================================================
echo.
echo   本机访问:
echo      http://localhost:8050
echo.
if defined IP (
    echo   局域网访问 ^(其他设备^):
    echo      http://%IP%:8050
    echo.
    echo   使用步骤:
    echo      1. 确保看板程序已启动 ^(双击 启动看板.bat^)
    echo      2. 确保其他设备连接到同一WiFi
    echo      3. 在其他设备浏览器中输入上述地址
)
echo.

echo ================================================================
echo           如果仍然无法访问，请尝试以下步骤
echo ================================================================
echo.
echo   1. 关闭防火墙测试
echo      临时关闭Windows防火墙，测试是否能访问
echo      如果可以，说明是防火墙配置问题
echo.
echo   2. 检查杀毒软件
echo      某些杀毒软件可能阻止端口访问
echo      尝试暂时禁用杀毒软件测试
echo.
echo   3. 检查路由器设置
echo      确认路由器未开启AP隔离功能
echo      AP隔离会阻止设备间互相访问
echo.
echo   4. Ping测试连通性
if defined IP (
    echo      在其他设备上执行: ping %IP%
)
echo      如果ping不通，说明网络层不通
echo.
echo   5. 查看详细日志
echo      启动看板时，注意控制台输出的IP地址
echo      确认是否正确绑定到 0.0.0.0:8050
echo.
echo ================================================================
echo.
pause
