@echo off
chcp 65001 >nul
echo =====================================
echo 检查 PostgreSQL 状态
echo =====================================
echo.

echo [1] 检查服务...
sc query | findstr /i "postgres" >nul
if %errorlevel%==0 (
    echo ✓ 找到 PostgreSQL 服务
    sc query postgresql-x64-15
    echo.
    sc query postgresql-x64-16
) else (
    echo ✗ 未找到 PostgreSQL 服务
)

echo.
echo [2] 检查端口 5432...
netstat -ano | findstr ":5432" >nul
if %errorlevel%==0 (
    echo ✓ 端口 5432 正在监听
    netstat -ano | findstr ":5432"
) else (
    echo ✗ 端口 5432 未监听
)

echo.
echo [3] 尝试连接数据库...
psql -U postgres -d o2o_analysis -c "SELECT version();" 2>nul
if %errorlevel%==0 (
    echo ✓ 数据库连接成功
) else (
    echo ✗ 数据库连接失败
)

echo.
pause
