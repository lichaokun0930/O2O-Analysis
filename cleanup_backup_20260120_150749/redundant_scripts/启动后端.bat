@echo off
echo ================================================================================
echo 启动React版本后端服务
echo ================================================================================
echo.

cd /d "%~dp0"

echo 激活虚拟环境...
call .venv\Scripts\activate.bat

echo.
echo 启动后端服务（端口8080）...
echo 按 Ctrl+C 可停止服务
echo.

python backend/app/main.py

pause
