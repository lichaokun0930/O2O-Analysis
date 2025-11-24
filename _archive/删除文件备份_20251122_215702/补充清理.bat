@echo off
chcp 65001 >nul
echo.
echo ===================================================================
echo            继续清理剩余文件
echo ===================================================================
echo.

set BACKUP=待删除文件_20251119_175725

echo 正在移动剩余文件到: %BACKUP%
echo.

if exist "检查Excel与看板差异.py" (
    move /Y "检查Excel与看板差异.py" "%BACKUP%\" >nul 2>&1
    echo [OK] 检查Excel与看板差异.py
) else (
    echo [Skip] 检查Excel与看板差异.py
)

if exist "完整性检查报告.py" (
    move /Y "完整性检查报告.py" "%BACKUP%\" >nul 2>&1
    echo [OK] 完整性检查报告.py
) else (
    echo [Skip] 完整性检查报告.py
)

if exist "查看优化成果.py" (
    move /Y "查看优化成果.py" "%BACKUP%\" >nul 2>&1
    echo [OK] 查看优化成果.py
) else (
    echo [Skip] 查看优化成果.py
)

if exist "查看字段结构.py" (
    move /Y "查看字段结构.py" "%BACKUP%\" >nul 2>&1
    echo [OK] 查看字段结构.py
) else (
    echo [Skip] 查看字段结构.py
)

echo.
echo ===================================================================
echo 清理完成! 保留 "查看数据库状态.py" 用于日常维护
echo ===================================================================
echo.
pause
