@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo 检查并推送营销分析模型文件到Github
echo ========================================
echo.

echo ✅ 确认文件存在:
if exist "科学八象限分析器.py" (
    echo   ✓ 科学八象限分析器.py
) else (
    echo   ✗ 科学八象限分析器.py [缺失]
)

if exist "评分模型分析器.py" (
    echo   ✓ 评分模型分析器.py
) else (
    echo   ✗ 评分模型分析器.py [缺失]
)
echo.

echo 📦 添加营销分析文件到Git...
git add "科学八象限分析器.py"
git add "评分模型分析器.py"
git add "verify_check\octant_analyzer.py"
git add "verify_check\scoring_analyzer.py"
git add "Tab7八象限分析使用指南.md"
git add "营销分析功能说明.md"

echo 📦 添加启动脚本和工具...
git add "启动_门店加盟类型字段迁移.ps1"
git add "启动_Requirements追踪系统.ps1"
git add "tools\track_requirements_changes.py"
git add "门店加盟类型字段使用指南.md"
git add "门店加盟类型字段部署清单.md"
git add "requirements变更追踪使用指南.md"
git add "requirements追踪-快速开始.md"
git add "requirements追踪系统测试报告.md"
git add "requirements_changelog.md"

echo 📦 添加推送和检查脚本...
git add "B电脑克隆清单.md"
git add "Github推送文件清单.md"
git add "推送到Github.bat"
git add "推送到Github.ps1"
git add "推送营销分析文件.bat"
git add "检查营销分析文件.ps1"
git add "推送前检查.bat"
git add "完整推送确认清单.md"

echo 📦 添加数据库相关文件...
git add "migrations\*.sql"
git add "verify_check\数据库导出\*.sql"
git add "database\*.py"
echo.

echo 📝 检查哪些文件将被提交...
git status --short
echo.

echo 💾 提交更改...
git commit -m "feat: 添加营销分析模型+管理工具+推送脚本

主要内容:
【营销分析模型】
+ 科学八象限分析器.py (品类动态阈值+置信度评估)
+ 评分模型分析器.py (多维度评分+权重计算)
+ Tab7八象限分析使用指南.md
+ 营销分析功能说明.md

【管理工具】
+ 启动_门店加盟类型字段迁移.ps1 (数据库字段迁移)
+ 启动_Requirements追踪系统.ps1 (依赖变更追踪)
+ tools/track_requirements_changes.py (依赖追踪核心)
+ 门店加盟类型字段使用指南.md
+ requirements变更追踪使用指南.md
+ requirements_changelog.md (变更日志)

【推送和部署】
+ B电脑克隆清单.md (完整部署指南)
+ Github推送文件清单.md (文件清单)
+ 推送脚本 (bat+ps1)

【数据库文件】
+ migrations/pg_ddl_*.sql (数据库表结构)
+ verify_check/数据库导出/o2o_dashboard_full_*.sql (完整数据备份)
+ database模块 (数据库连接和管理)

【verify_check目录】
+ octant_analyzer.py (英文版八象限分析器)
+ scoring_analyzer.py (英文版评分分析器)

完整功能,开箱即用!"
echo.

echo 🚀 推送到Github...
git push origin master
echo.

if %errorlevel%==0 (
    echo ========================================
    echo ✅ 推送成功!
    echo ========================================
    echo.
    echo 已推送的文件类别:
    echo.
    echo 【营销分析模型】
    echo   ✓ 科学八象限分析器.py
    echo   ✓ 评分模型分析器.py
    echo   ✓ verify_check\octant_analyzer.py
    echo   ✓ verify_check\scoring_analyzer.py
    echo   ✓ Tab7八象限分析使用指南.md
    echo   ✓ 营销分析功能说明.md
    echo.
    echo 【管理工具】
    echo   ✓ 启动_门店加盟类型字段迁移.ps1
    echo   ✓ 启动_Requirements追踪系统.ps1
    echo   ✓ tools\track_requirements_changes.py
    echo   ✓ 门店加盟类型字段使用指南.md
    echo   ✓ requirements变更追踪使用指南.md
    echo.
    echo 【推送和部署】
    echo   ✓ B电脑克隆清单.md
    echo   ✓ Github推送文件清单.md
    echo   ✓ 推送脚本 (bat+ps1^)
    echo.
    echo 【数据库文件】
    echo   ✓ migrations/pg_ddl_*.sql
    echo   ✓ verify_check/数据库导出/o2o_dashboard_full_*.sql
    echo   ✓ database模块
    echo.
    echo 🎉 B电脑克隆后即可使用:
    echo      Tab7营销分析功能
    echo      数据库字段迁移工具
    echo      Requirements依赖追踪系统
    echo      完整数据库备份恢复
) else (
    echo ========================================
    echo ❌ 推送失败!
    echo ========================================
)

echo.
pause
