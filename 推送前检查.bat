@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ================================================================
echo 推送前完整文件检查
echo ================================================================
echo.

set "allOk=1"

echo 【1】检查营销分析模型文件
echo ----------------------------------------
call :CheckFile "科学八象限分析器.py"
call :CheckFile "评分模型分析器.py"
call :CheckFile "verify_check\octant_analyzer.py"
call :CheckFile "verify_check\scoring_analyzer.py"
echo.

echo 【2】检查管理工具脚本
echo ----------------------------------------
call :CheckFile "启动_门店加盟类型字段迁移.ps1"
call :CheckFile "启动_Requirements追踪系统.ps1"
call :CheckFile "tools\track_requirements_changes.py"
echo.

echo 【3】检查文档文件
echo ----------------------------------------
call :CheckFile "Tab7八象限分析使用指南.md"
call :CheckFile "营销分析功能说明.md"
call :CheckFile "门店加盟类型字段使用指南.md"
call :CheckFile "门店加盟类型字段部署清单.md"
call :CheckFile "requirements变更追踪使用指南.md"
call :CheckFile "requirements追踪-快速开始.md"
call :CheckFile "requirements追踪系统测试报告.md"
call :CheckFile "requirements_changelog.md"
echo.

echo 【4】检查推送脚本
echo ----------------------------------------
call :CheckFile "B电脑克隆清单.md"
call :CheckFile "Github推送文件清单.md"
call :CheckFile "推送到Github.bat"
call :CheckFile "推送到Github.ps1"
call :CheckFile "推送营销分析文件.bat"
call :CheckFile "检查营销分析文件.ps1"
echo.

echo ================================================================
if "%allOk%"=="1" (
    echo ✅ 检查完成! 所有文件都存在
    echo ================================================================
    echo.
    echo 文件统计:
    echo   - 营销分析模型: 4个文件
    echo   - 管理工具: 3个文件
    echo   - 文档: 8个文件
    echo   - 推送脚本: 6个文件
    echo   总计: 21个关键文件
    echo.
    echo 可以安全推送到Github!
    echo.
    choice /C YN /M "是否立即推送"
    if errorlevel 2 goto :EOF
    if errorlevel 1 (
        echo.
        echo 开始推送...
        call "推送营销分析文件.bat"
    )
) else (
    echo ❌ 检查失败! 有文件缺失
    echo ================================================================
    echo.
    echo 请先创建缺失的文件再推送!
)

echo.
pause
goto :EOF

:CheckFile
if exist "%~1" (
    echo   ✓ %~1
) else (
    echo   ✗ %~1 [缺失]
    set "allOk=0"
)
goto :EOF
