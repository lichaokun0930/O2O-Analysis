@echo off
chcp 65001 >nul
title 停止智能门店经营看板

echo.
echo ================================================================
echo             停止智能门店经营看板服务器
echo ================================================================
echo.

echo [1/2] 查找运行中的Python进程（端口8050）...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8050 ^| findstr LISTENING') do (
    set PID=%%a
    goto :found
)

echo [INFO] 未找到运行在8050端口的进程
echo        应用可能已经停止
pause
exit /b 0

:found
echo [OK] 找到进程 PID: %PID%

echo [2/2] 停止服务器...
taskkill /F /PID %PID% >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 停止失败，可能需要管理员权限
    pause
    exit /b 1
)

echo.
echo ----------------------------------------------------------------
echo [SUCCESS] 服务器已停止！
echo ----------------------------------------------------------------
echo.
pause
