@echo off
chcp 65001 >nul
title 一键配置局域网访问
color 0B

echo.
echo ================================================================
echo          智能门店看板 - 一键配置局域网访问
echo ================================================================
echo.
echo 此脚本将自动完成以下操作：
echo   1. 检查网络连接
echo   2. 配置Windows防火墙（开放8050端口）
echo   3. 显示局域网访问地址
echo.
echo 注意：需要管理员权限才能配置防火墙
echo.
pause

echo.
echo [1/3] 正在检查管理员权限...

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] 已获得管理员权限
) else (
    echo [ERROR] 需要管理员权限！
    echo.
    echo 请按照以下步骤操作：
    echo   1. 关闭此窗口
    echo   2. 右键点击此脚本
    echo   3. 选择"以管理员身份运行"
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] 正在配置防火墙规则...
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { try { $rule = Get-NetFirewallRule -DisplayName '智能门店看板' -ErrorAction SilentlyContinue; if ($rule) { Write-Host '[INFO] 检测到已存在的防火墙规则，正在更新...' -ForegroundColor Yellow; Remove-NetFirewallRule -DisplayName '智能门店看板' -ErrorAction SilentlyContinue } New-NetFirewallRule -DisplayName '智能门店看板' -Description '允许智能门店经营看板的局域网访问（端口8051）' -Direction Inbound -Protocol TCP -LocalPort 8051 -Action Allow -Enabled True -Profile Domain,Private,Public -ErrorAction Stop | Out-Null; Write-Host '[OK] 防火墙规则配置成功！' -ForegroundColor Green } catch { Write-Host '[ERROR] 配置失败: $($_.Exception.Message)' -ForegroundColor Red; exit 1 } }"

if %errorlevel% neq 0 (
    echo [ERROR] 防火墙配置失败
    pause
    exit /b 1
)

echo.
echo [3/3] 获取局域网IP地址...
REM 优先获取192.168或10.开头的真实局域网IP（排除虚拟适配器）
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

echo.
echo ================================================================
echo                    配置完成！
echo ================================================================
echo.
echo ✅ 防火墙规则已配置
echo ✅ 8050端口已开放
echo.
echo 📍 本机访问地址：
echo    http://localhost:8050
echo.
echo 🌐 局域网访问地址：
echo    http://%IP%:8050
echo.
echo ================================================================
echo.
echo 💡 使用提示：
echo    1. 确保看板程序已启动（双击"启动看板.bat"）
echo    2. 确保其他设备连接到同一WiFi
echo    3. 在其他设备浏览器中输入上述局域网地址
echo.
echo 🔍 如果仍然无法访问，请运行：诊断局域网访问.ps1
echo.
pause
