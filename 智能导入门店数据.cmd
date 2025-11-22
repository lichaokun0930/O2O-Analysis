@echo off
chcp 65001 >nul
cd /d "%~dp0"
.\.venv\Scripts\python.exe "智能导入门店数据.py" %*
pause
