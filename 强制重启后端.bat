@echo off
echo ================================================================================
echo 强制重启React版本后端服务
echo ================================================================================
echo.

echo 步骤1: 停止所有占用8080端口的进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do (
    echo 找到进程 PID: %%a
    taskkill /F /PID %%a 2>nul
    if errorlevel 1 (
        echo 进程 %%a 已停止或无法停止
    ) else (
        echo 成功停止进程 %%a
    )
)

echo.
echo 等待端口释放...
timeout /t 3 /nobreak >nul

echo.
echo 步骤2: 启动后端服务...
echo 提示: 请在新的终端窗口中手动运行以下命令:
echo.
echo    cd 订单数据看板\订单数据看板\O2O-Analysis
echo    .venv\Scripts\activate
echo    python backend/app/main.py
echo.
echo 或者直接运行: 启动后端.bat
echo.

pause
