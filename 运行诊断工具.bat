@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo =========================================
echo 诊断工具菜单
echo =========================================
echo.
echo 请选择要运行的诊断工具:
echo.
echo   1. 启动自检（完整报告）
echo   2. 今日必做性能诊断
echo   3. Redis缓存诊断
echo   4. 数据库连接诊断
echo   5. 退出
echo.

set /p choice=请输入选项 (1-5): 

if "%choice%"=="1" (
    echo.
    echo 运行启动自检...
    python 启动自检.py
    goto end
)

if "%choice%"=="2" (
    echo.
    echo 运行今日必做性能诊断...
    python 诊断今日必做性能.py
    goto end
)

if "%choice%"=="3" (
    echo.
    echo 运行Redis缓存诊断...
    python 通用模块诊断工具.py --example redis
    goto end
)

if "%choice%"=="4" (
    echo.
    echo 运行数据库连接诊断...
    python 通用模块诊断工具.py --example database
    goto end
)

if "%choice%"=="5" (
    echo.
    echo 退出
    exit /b
)

echo.
echo 无效选项，请重新运行脚本

:end
echo.
pause
