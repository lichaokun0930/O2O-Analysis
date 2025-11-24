@echo off
chcp 65001 >nul
set PGPASSWORD=308352588

echo =====================================
echo 清空数据库旧数据
echo =====================================
echo.

echo 警告: 即将删除 orders 表中的所有数据!
echo.
pause

echo 正在清空...
psql -U postgres -d o2o_dashboard -c "DELETE FROM orders;"

echo.
echo 验证...
psql -U postgres -d o2o_dashboard -c "SELECT COUNT(*) as remaining FROM orders;"

echo.
echo ✓ 数据已清空,可以重新导入
pause
