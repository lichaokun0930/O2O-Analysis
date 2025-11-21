@echo off
chcp 65001 >nul
echo.
echo =====================================================================
echo                     安全清理冗余文件
echo =====================================================================
echo.
echo 准备将冗余文件移动到备份文件夹...
echo.
pause

:: 创建备份文件夹
set "timestamp=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "timestamp=%timestamp: =0%"
set "backupFolder=待删除文件_%timestamp%"

echo.
echo 创建备份文件夹: %backupFolder%
mkdir "%backupFolder%" 2>nul

:: 移动文件
echo.
echo 正在移动文件...
echo.

set count=0

:: 测试文件
call :MoveFile "测试requirements追踪.py"
call :MoveFile "测试启动脚本.ps1"
call :MoveFile "测试成本字段.py"
call :MoveFile "测试数据字段.py"
call :MoveFile "测试标准化字段.py"
call :MoveFile "测试看板数据加载.py"
call :MoveFile "测试门店加盟类型字段.py"

:: 检查文件
call :MoveFile "检查Excel与看板差异.py"
call :MoveFile "检查Excel数据.py"
call :MoveFile "检查PowerShell版本_兼容版.ps1"
call :MoveFile "检查佣金兜底订单.py"
call :MoveFile "检查利润额来源.py"
call :MoveFile "检查同事环境.ps1"
call :MoveFile "检查当前看板数据.py"
call :MoveFile "检查数据库利润数据.py"
call :MoveFile "检查数据库表.py"
call :MoveFile "检查数据库门店.py"
call :MoveFile "检查枫瑞美团共橙数据.py"
call :MoveFile "检查渠道过滤.py"
call :MoveFile "检查源数据.py"
call :MoveFile "检查物流费.py"
call :MoveFile "检查物流费差异.py"
call :MoveFile "检查看板数据文件.py"
call :MoveFile "检查耗材利润.py"
call :MoveFile "检查耗材订单结构.py"
call :MoveFile "检查订单结构.py"
call :MoveFile "检查门店数据文件夹.py"
call :MoveFile "快速检查耗材.py"
call :MoveFile "快速检查耗材数据.py"

:: 验证文件
call :MoveFile "验证all_no_fallback结果.py"
call :MoveFile "验证Line1016影响.py"
call :MoveFile "验证保留剔除耗材.py"
call :MoveFile "验证修复后的利润计算.py"
call :MoveFile "验证兜底逻辑.py"
call :MoveFile "验证商品级剔除.py"
call :MoveFile "验证实际利润公式.py"
call :MoveFile "验证数据分离.py"
call :MoveFile "验证数据库数据.py"
call :MoveFile "验证最终修改结果.py"
call :MoveFile "验证渠道利润计算.py"
call :MoveFile "验证物流配送费聚合.py"
call :MoveFile "验证用户计算.py"
call :MoveFile "验证祥和路利润.py"
call :MoveFile "验证祥和路店利润.py"
call :MoveFile "验证过滤影响.py"
call :MoveFile "快速验证利润.py"
call :MoveFile "完整数据流程验证.py"
call :MoveFile "完整数据流程验证_clean.py"
call :MoveFile "完整自检.py"
call :MoveFile "完整验证数据分离.py"

:: 诊断文件
call :MoveFile "诊断利润异常.py"
call :MoveFile "诊断美团共橙负利润.py"

:: 对比文件
call :MoveFile "对比三种计算方案.py"
call :MoveFile "对比剔除前后数据.py"
call :MoveFile "对比订单ID和利润额.py"
call :MoveFile "深度对比结果.txt"
call :MoveFile "最终方案对比.py"
call :MoveFile "完整模拟结果.txt"

:: 分析追踪文件
call :MoveFile "分析利润差异.py"
call :MoveFile "逐步追踪利润额.py"
call :MoveFile "反推看板数据.py"
call :MoveFile "商品分类结构分析.py"
call :MoveFile "分析冗余文件.py"
call :MoveFile "理解剔除负值逻辑.py"
call :MoveFile "理解耗材逻辑.py"
call :MoveFile "用核心代码计算美团共橙.py"
call :MoveFile "直接调用看板函数验证.py"
call :MoveFile "精确计算枫瑞店利润.py"
call :MoveFile "计算美团共橙利润_不剔除耗材.py"
call :MoveFile "重新理解耗材逻辑.py"
call :MoveFile "最终完整计算.py"
call :MoveFile "最终验证.py"

:: 演示Demo
call :MoveFile "demo_price_data.json"
call :MoveFile "分类销售看板布局demo.html"
call :MoveFile "用户复购分析看板demo.html"
call :MoveFile "演示requirements追踪.py"

:: 清理脚本
call :MoveFile "清理缓存.py"
call :MoveFile "清理过时文件_安全版.ps1"
call :MoveFile "清除缓存.bat"
call :MoveFile "清空数据库.py"
call :MoveFile "安全清理仓库文件.ps1"
call :MoveFile "安全清理文件.ps1"
call :MoveFile "执行清理.ps1"

:: 旧版脚本
call :MoveFile "启动P1_P2_P3.ps1"
call :MoveFile "启动全栈服务.ps1"
call :MoveFile "启动全栈服务_自动.py"
call :MoveFile "快速启动看板.py"
call :MoveFile "快速启动数据库.ps1"
call :MoveFile "定位PowerShell7.ps1"
call :MoveFile "设置PowerShell7为默认.ps1"
call :MoveFile "智能门店看板_简化版.py"
call :MoveFile "智能门店经营看板_可视化.py"

:: 临时文件
call :MoveFile "调研结果.txt"
call :MoveFile "营销分析结果.txt"
call :MoveFile "批量替换calc_mode.py"
call :MoveFile "重新导入数据.py"
call :MoveFile "重新导入铜山万达.ps1"
call :MoveFile "已禁用TAB功能归档.py"
call :MoveFile "添加PowerShell7到右键菜单.ps1"

echo.
echo =====================================================================
echo.
echo 清理完成!
echo.
echo 已移动 %count% 个文件到: %backupFolder%
echo.
echo 提示:
echo   1. 测试您的应用是否正常运行
echo   2. 确认无问题后,可以删除备份文件夹
echo   3. 如有问题,可以从备份文件夹恢复文件
echo.
echo =====================================================================
echo.
pause
goto :eof

:MoveFile
if exist %1 (
    move %1 "%backupFolder%\" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] %~1
        set /a count+=1
    ) else (
        echo [Error] %~1
    )
) else (
    echo [Not Found] %~1
)
goto :eof
