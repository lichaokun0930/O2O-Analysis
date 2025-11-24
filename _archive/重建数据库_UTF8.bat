@echo off
chcp 65001 >nul
set PGPASSWORD=308352588

echo =====================================
echo 重建数据库为UTF8编码
echo =====================================
echo.

echo 警告: 即将删除并重建 o2o_dashboard 数据库!
echo 所有数据将丢失!
echo.
pause

echo.
echo [1] 断开所有连接...
psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='o2o_dashboard';"

echo.
echo [2] 删除旧数据库...
psql -U postgres -c "DROP DATABASE IF EXISTS o2o_dashboard;"

echo.
echo [3] 创建UTF8编码数据库...
psql -U postgres -c "CREATE DATABASE o2o_dashboard ENCODING 'UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0;"

echo.
echo [4] 验证数据库编码...
psql -U postgres -c "\l o2o_dashboard"

echo.
echo ✓ 数据库已重建,请重新运行导入脚本
pause
