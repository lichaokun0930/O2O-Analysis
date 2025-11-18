@echo off
chcp 65001 >nul
title 智能门店经营看板 - 启动程序
color 0A

echo.
echo ================================================================
echo             智能门店经营看板 - 启动程序
echo ================================================================
echo.

echo [1/3] 切换到项目目录...
cd /d "d:\Python1\O2O_Analysis\O2O数据分析\测算模型"

echo [2/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] 未找到Python，请先安装Python
    pause
    exit /b 1
)
echo [OK] Python环境检测通过

REM 设置环境变量（禁用缓冲，确保日志实时显示）
set PYTHONUNBUFFERED=1
set PYTHONIOENCODING=utf-8
echo [OK] 已启用实时日志显示

echo.
echo [3/3] 正在启动智能门店经营看板...
echo.
echo       请等待启动完成（约10-15秒）
echo       然后在浏览器中访问: http://localhost:8050
echo.
echo ----------------------------------------------------------------
echo.

python "智能门店看板_Dash版.py"

echo.
echo ----------------------------------------------------------------
echo [INFO] 应用服务器已停止
echo.
pause
