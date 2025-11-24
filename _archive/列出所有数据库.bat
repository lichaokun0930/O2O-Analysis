@echo off
chcp 65001 >nul
echo =====================================
echo 列出所有数据库
echo =====================================
echo.

echo 密码: 308352588
echo.

psql -U postgres -c "\l" 2>nul

if %errorlevel% neq 0 (
    echo.
    echo 使用密码连接...
    echo 308352588| psql -U postgres -c "\l"
)

echo.
pause
