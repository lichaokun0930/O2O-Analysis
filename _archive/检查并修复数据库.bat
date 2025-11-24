@echo off
chcp 65001 >nul
echo =====================================
echo 检查和修复数据库配置
echo =====================================

set PGPASSWORD=308352588

echo.
echo [1] 列出所有数据库...
psql -U postgres -c "\l" 2>nul

echo.
echo [2] 检查 o2o_dashboard 数据库...
psql -U postgres -d o2o_dashboard -c "SELECT COUNT(*) as order_count FROM orders;" 2>nul
if %errorlevel%==0 (
    echo ✓ o2o_dashboard 存在且有 orders 表
) else (
    echo ✗ o2o_dashboard 不存在或没有 orders 表
    echo.
    echo 尝试创建数据库...
    psql -U postgres -c "CREATE DATABASE o2o_dashboard;"
    if %errorlevel%==0 (
        echo ✓ 数据库创建成功
    ) else (
        echo ✗ 数据库创建失败
    )
)

echo.
echo [3] 检查 o2o_analysis 数据库...
psql -U postgres -d o2o_analysis -c "SELECT COUNT(*) as order_count FROM orders;" 2>nul
if %errorlevel%==0 (
    echo ✓ o2o_analysis 存在且有 orders 表
) else (
    echo ✗ o2o_analysis 不存在或没有 orders 表
)

echo.
pause
