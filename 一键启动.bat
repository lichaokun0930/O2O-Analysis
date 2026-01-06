@echo off
chcp 65001 > nul
cd /d "%~dp0"

:: 查找虚拟环境 Python 并运行启动脚本
if exist "..\..\.venv\Scripts\python.exe" (
    call "..\..\.venv\Scripts\python.exe" "%~dp0一键启动.py" %*
) else if exist "..\.venv\Scripts\python.exe" (
    call "..\.venv\Scripts\python.exe" "%~dp0一键启动.py" %*
) else if exist ".venv\Scripts\python.exe" (
    call ".venv\Scripts\python.exe" "%~dp0一键启动.py" %*
) else (
    call python "%~dp0一键启动.py" %*
)

if errorlevel 1 pause
