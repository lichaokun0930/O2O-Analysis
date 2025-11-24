@echo off
chcp 65001 >nul
set PGPASSWORD=308352588

echo =====================================
echo 查询数据库订单数量
echo =====================================
echo.

psql -U postgres -d o2o_dashboard -c "SELECT COUNT(*) as total FROM orders;"
echo.

echo 查询门店列表...
psql -U postgres -d o2o_dashboard -c "SELECT store_name, COUNT(*) as count FROM orders GROUP BY store_name;"
echo.

pause
