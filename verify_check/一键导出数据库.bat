@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║           🗄️  PostgreSQL 数据库一键导出                         ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

REM 激活虚拟环境
if exist .venv\Scripts\activate.bat (
    echo ✅ 激活虚拟环境...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  未找到虚拟环境，使用系统 Python
)

echo.
echo 📤 开始导出数据库...
echo.

REM 导出所有格式（完整、仅结构、仅数据）
python 导出数据库.py --all

echo.
echo ✅ 导出完成！
echo.
echo 📁 导出文件位置: 数据库导出\
echo 📋 导入指南: 数据库导出\导入指南.txt
echo.
pause
