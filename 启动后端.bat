@echo off
chcp 65001 >nul
title 订单数据看板 - 后端API服务
setlocal enabledelayedexpansion

:: 端口配置
set API_PORT=8080

echo(
echo(============================================
echo(      订单数据看板 - FastAPI 后端服务
echo(============================================
echo(

cd /d "%~dp0backend"

:: 检测旧进程
echo([*] 检测旧进程...
set PID_OLD=
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":%API_PORT% " ^| findstr "LISTENING"') do (
    set PID_OLD=%%a
)

if defined PID_OLD (
    for /f "tokens=1" %%n in ('tasklist /FI "PID eq !PID_OLD!" /FO CSV /NH 2^>nul') do set PROC_NAME=%%~n
    echo([WARN] Port %API_PORT% 被占用
    echo(    进程: !PROC_NAME! - PID: !PID_OLD!
    echo(
    set /p clean="是否清理旧进程? [y/n]: "
    if /i "!clean!"=="y" (
        taskkill /PID !PID_OLD! /F >nul 2>&1
        echo([OK] 旧进程已清理
        timeout /t 1 /nobreak >nul
    )
)
echo(

:: 尝试激活虚拟环境
if exist "..\..\.venv\Scripts\activate.bat" (
    call "..\..\.venv\Scripts\activate.bat"
    echo([INFO] 已激活虚拟环境
) else if exist "..\.venv\Scripts\activate.bat" (
    call "..\.venv\Scripts\activate.bat"
    echo([INFO] 已激活虚拟环境
) else if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
    echo([INFO] 已激活虚拟环境
)

:: 检查依赖
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo([*] 正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo([ERROR] 依赖安装失败！
        pause
        exit /b 1
    )
)
echo(

:menu
echo(--------------------------------------------
echo(  请选择启动模式:
echo(
echo(    1. 开发模式 - 热重载 - Port %API_PORT%
echo(    2. 生产模式 - 多进程 - Port %API_PORT%
echo(    0. 退出
echo(--------------------------------------------
echo(
set /p choice="请输入选项 [1/2/0]: "

if "%choice%"=="1" goto dev
if "%choice%"=="2" goto prod
if "%choice%"=="0" goto end
echo([WARN] 无效选项，请重新选择
echo(
goto menu

:dev
echo(
set ENVIRONMENT=development
set DEBUG=true
set LOG_LEVEL=DEBUG
echo([MODE] 开发模式
echo([URL] http://localhost:%API_PORT%
echo([DOCS] http://localhost:%API_PORT%/api/docs
echo([TIP] 修改代码后自动重启，按 Ctrl+C 停止
echo(
python -m uvicorn app.main:app --host 0.0.0.0 --port %API_PORT% --reload --reload-dir app --log-level debug
goto end

:prod
echo(
set ENVIRONMENT=production
set DEBUG=false
set LOG_LEVEL=INFO

:: 计算Worker数
for /f "tokens=2 delims==" %%a in ('wmic cpu get NumberOfCores /value 2^>nul') do set CORES=%%a
if "%CORES%"=="" set CORES=2
set /a WORKERS=%CORES%*2+1
if %WORKERS% GTR 8 set WORKERS=8

echo([MODE] 生产模式
echo([WORKERS] %WORKERS% workers
echo([URL] http://localhost:%API_PORT%
echo([TIP] 按 Ctrl+C 停止
echo(
python -m uvicorn app.main:app --host 0.0.0.0 --port %API_PORT% --workers %WORKERS% --log-level info
goto end

:end
pause
