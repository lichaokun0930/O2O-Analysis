@echo off
chcp 65001 >nul
echo ==========================================
echo PostgreSQL 强制修复和启动
echo ==========================================
echo.

echo 正在终止所有PostgreSQL进程...
taskkill /F /IM postgres.exe >nul 2>&1
timeout /t 2 >nul

echo 正在清理锁文件...
del /F /Q "D:\PostgreSQL\data\postmaster.pid" >nul 2>&1
del /F /Q "D:\PostgreSQL\data\postmaster.opts" >nul 2>&1
del /F /Q "D:\PostgreSQL\data\logfile.log" >nul 2>&1

echo.
echo 正在启动PostgreSQL...
"D:\PostgreSQL\bin\pg_ctl.exe" start -D "D:\PostgreSQL\data"

echo.
echo ==========================================
timeout /t 3 >nul

echo.
echo 检查PostgreSQL状态...
"D:\PostgreSQL\bin\pg_ctl.exe" status -D "D:\PostgreSQL\data"

echo.
pause
