@echo off
chcp 65001 >nul
title 订单数据看板 - React 前端服务
setlocal enabledelayedexpansion

:: 端口配置
set DEV_PORT=3001
set PROD_PORT=4001

echo(
echo(============================================
echo(       订单数据看板 - React 前端服务
echo(============================================
echo(

cd /d "%~dp0frontend-react"

:: 检测旧进程
echo([*] 检测旧进程...
set OLD_FOUND=0
set PID_DEV=
set PID_PROD=

for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":%DEV_PORT% " ^| findstr "LISTENING"') do (
    set PID_DEV=%%a
    set OLD_FOUND=1
)

for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":%PROD_PORT% " ^| findstr "LISTENING"') do (
    set PID_PROD=%%a
    set OLD_FOUND=1
)

if "%OLD_FOUND%"=="1" (
    echo([WARN] 旧进程占用端口
    if defined PID_DEV echo(    Port %DEV_PORT%: PID !PID_DEV!
    if defined PID_PROD echo(    Port %PROD_PORT%: PID !PID_PROD!
    echo(
    set /p clean="是否清理旧进程? [y/n]: "
    if /i "!clean!"=="y" (
        if defined PID_DEV taskkill /PID !PID_DEV! /F >nul 2>&1
        if defined PID_PROD taskkill /PID !PID_PROD! /F >nul 2>&1
        echo([OK] 旧进程已清理
        timeout /t 1 /nobreak >nul
    )
)
echo(

:: 检查依赖
if not exist "node_modules" (
    echo([*] 首次运行，正在安装依赖...
    call npm install
    if errorlevel 1 (
        echo([ERROR] 依赖安装失败！
        pause
        exit /b 1
    )
    echo(
)

:menu
echo(--------------------------------------------
echo(  请选择启动模式:
echo(
echo(    1. 开发模式 - 热重载 - Port %DEV_PORT%
echo(    2. 生产模式 - 构建并预览 - Port %PROD_PORT%
echo(    3. 仅构建 - 不启动服务
echo(    0. 退出
echo(--------------------------------------------
echo(
set /p choice="请输入选项 [1/2/3/0]: "

if "%choice%"=="1" goto dev
if "%choice%"=="2" goto prod
if "%choice%"=="3" goto build
if "%choice%"=="0" goto end
echo([WARN] 无效选项，请重新选择
echo(
goto menu

:dev
echo(
echo([*] 启动开发模式 - 热重载已启用
echo([*] http://localhost:%DEV_PORT%
echo([TIP] 修改代码后自动刷新，按 Ctrl+C 停止
echo(
call npm run dev
goto end

:prod
echo(
echo([*] 正在构建生产版本...
call npm run build
if errorlevel 1 (
    echo([ERROR] 构建失败！
    pause
    goto menu
)
echo([OK] 构建完成！
echo(
echo([*] 启动预览服务器
echo([*] http://localhost:%PROD_PORT%
echo(
call npm run preview -- --port %PROD_PORT%
goto end

:build
echo(
echo([*] 正在构建生产版本...
call npm run build
if errorlevel 1 (
    echo([ERROR] 构建失败！
) else (
    echo([OK] 构建完成！产物位于 dist/ 目录
)
echo(
pause
goto menu

:end
pause
