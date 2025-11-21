@echo off
chcp 65001 >nul
title 智能门店经营看板 - 启动程序

echo.
echo ================================================================
echo             智能门店经营看板 - 后台启动
echo ================================================================
echo.

cd /d "d:\Python1\O2O_Analysis\O2O数据分析\测算模型"

echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到Python，请先安装Python
    pause
    exit /b 1
)
echo [OK] Python已安装

echo [2/4] 检查端口8050...
netstat -ano | findstr :8050 >nul
if not errorlevel 1 (
    echo [WARNING] 端口8050已被占用，应用可能已在运行
    echo           请先访问 http://localhost:8050 查看
    echo           如需重启，请先关闭占用端口的进程
    pause
    exit /b 0
)
echo [OK] 端口8050可用

echo [3/4] 启动应用服务器（后台模式）...
start "智能门店看板-服务器" /MIN python "智能门店看板_Dash版.py"

echo [4/4] 等待服务器启动...
timeout /t 10 /nobreak >nul

echo.
echo ----------------------------------------------------------------
echo [SUCCESS] 应用已启动！
echo.
echo 访问地址: http://localhost:8050
echo.
echo 提示：
echo   - 服务器在后台运行，不会阻塞此窗口
echo   - 关闭此窗口不会停止服务器
echo   - 要停止服务器，请关闭"智能门店看板-服务器"窗口
echo   - 或使用 taskkill 命令结束Python进程
echo.
echo ----------------------------------------------------------------
echo.

:: 自动打开浏览器
echo 正在打开浏览器...
start http://localhost:8050

echo.
echo 完成！您可以关闭此窗口，服务器将继续运行。
echo.
pause
