@echo off
chcp 65001 >nul
set PGPASSWORD=308352588

echo =====================================
echo 查询最新导入的数据
echo =====================================
echo.

echo [1] 查询总记录数...
psql -U postgres -d o2o_dashboard -c "SELECT COUNT(*) FROM orders;"

echo.
echo [2] 查询门店分布...
psql -U postgres -d o2o_dashboard -c "SELECT store_name, COUNT(*) as count FROM orders GROUP BY store_name ORDER BY count DESC;"

echo.
echo [3] 查询最新5条记录...
psql -U postgres -d o2o_dashboard -c "SELECT id, order_id, store_name, date, channel, price FROM orders ORDER BY id DESC LIMIT 5;"

echo.
echo [4] 检查store_name为空的记录...
psql -U postgres -d o2o_dashboard -c "SELECT COUNT(*) as null_store_count FROM orders WHERE store_name IS NULL OR store_name = '';"

echo.
pause
