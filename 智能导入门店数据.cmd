@echo off
chcp 65001 >nul
cd /d "%~dp0"
REM 尝试使用上级目录的虚拟环境
if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" "智能导入门店数据.py" %*
) else (
    REM 如果上级目录没有，尝试当前目录
    if exist ".\.venv\Scripts\python.exe" (
        ".\.venv\Scripts\python.exe" "智能导入门店数据.py" %*
    ) else (
        echo ❌ 未找到虚拟环境，请检查 .venv 文件夹是否存在
        pause
        exit /b
    )
)
pause
