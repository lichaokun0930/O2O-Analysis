@echo off
chcp 65001 > nul
echo ================================
echo   重新导入门店数据
echo   包含新增的4个字段
echo ================================
echo.

REM 使用虚拟环境的Python
if exist ".venv\Scripts\python.exe" (
    echo 使用虚拟环境Python...
    .venv\Scripts\python.exe 智能导入门店数据.py
) else (
    echo 虚拟环境不存在，使用系统Python...
    python 智能导入门店数据.py
)

echo.
pause
