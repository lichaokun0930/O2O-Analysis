@echo off
chcp 65001 >nul
title 智能门店经营看板 - 启动程序
color 0A

echo.
echo ================================================================
echo             智能门店经营看板 - 启动程序
echo ================================================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

echo [1/4] 检查 Memurai Redis 服务...
sc query Memurai >nul 2>&1
if errorlevel 1 (
    echo [WARN] 未检测到 Memurai 服务，Redis 缓存将不可用
    goto :check_python
)

REM 检查服务是否运行
for /f "tokens=3 delims=: " %%a in ('sc query Memurai ^| findstr "STATE"') do (
    if /i "%%a"=="RUNNING" (
        echo [OK] Memurai Redis 服务正在运行
    ) else (
        echo [INFO] 正在启动 Memurai Redis 服务...
        net start Memurai >nul 2>&1
        if errorlevel 1 (
            echo [WARN] 需要管理员权限，请在弹出窗口中确认...
            powershell -Command "Start-Process powershell -ArgumentList '-Command', 'Start-Service -Name Memurai' -Verb RunAs -Wait"
        )
        timeout /t 2 /nobreak >nul
        echo [OK] Memurai Redis 服务已启动
    )
)

:check_python
echo.
echo [2/4] 检查Python环境...
REM 虚拟环境在父目录
if exist "..\\.venv\\Scripts\\python.exe" (
    set PYTHON_EXE=..\.venv\Scripts\python.exe
    echo [OK] 使用虚拟环境 Python ^(父目录^)
) else if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
    echo [OK] 使用虚拟环境 Python ^(当前目录^)
) else (
    set PYTHON_EXE=python
    echo [OK] 使用系统 Python
)

echo.
echo [3/4] 检查并停止已运行的看板进程...
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /v ^| findstr "智能门店看板"') do (
    echo [INFO] 停止已运行的进程 PID: %%a
    taskkill /pid %%a /f >nul 2>&1
)

REM 设置环境变量（禁用缓冲，确保日志实时显示）
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8

echo.
echo [4/4] 检查防火墙配置...
powershell -Command "if (Get-NetFirewallRule -DisplayName '智能门店看板' -ErrorAction SilentlyContinue) { Write-Host '[OK] 防火墙规则已配置，支持局域网访问' } else { Write-Host '[WARN] 未配置防火墙，局域网访问可能被阻止' -ForegroundColor Yellow; Write-Host '      请以管理员身份运行: 配置防火墙.ps1' -ForegroundColor Yellow }"

echo.
echo [5/5] 正在启动智能门店经营看板...
echo.
echo       请等待启动完成（约10-15秒）
echo       本机访问: http://localhost:8051
echo.
echo       若需局域网访问，启动后查看控制台显示的局域网地址
echo       如无法访问，请运行: 诊断局域网访问.ps1
echo.
echo ----------------------------------------------------------------
echo.

%PYTHON_EXE% "智能门店看板_Dash版.py"

echo.
echo ----------------------------------------------------------------
echo [INFO] 应用服务器已停止
echo.
pause
