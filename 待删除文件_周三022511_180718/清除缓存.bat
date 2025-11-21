@echo off
echo ================================
echo 清除看板缓存并重启
echo ================================

REM 删除缓存文件
if exist "学习数据仓库\processed_data\*.pkl.gz" (
    echo 正在删除processed_data缓存...
    del /q "学习数据仓库\processed_data\*.pkl.gz"
    echo ✓ 已删除processed_data缓存
)

if exist "学习数据仓库\cache\*.*" (
    echo 正在删除cache目录...
    del /q "学习数据仓库\cache\*.*"
    echo ✓ 已删除cache缓存
)

if exist "__pycache__" (
    echo 正在删除__pycache__...
    rmdir /s /q "__pycache__"
    echo ✓ 已删除__pycache__
)

echo.
echo ================================
echo 缓存清理完成!
echo ================================
echo.
echo 现在可以重新启动看板,将使用最新计算逻辑
pause
