@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ================================
echo 开始推送代码到Github
echo ================================
echo.

echo 检查Git仓库...
if not exist ".git" (
    echo ❌ 错误:当前目录不是Git仓库!
    pause
    exit /b 1
)

echo.
echo 检查远程仓库...
git remote -v
echo.

echo 添加文件...
git add .
echo.

echo 提交更改...
git commit -m "feat: Toast队列管理系统+全局刷新按钮优化

主要更新:
- 实现Toast队列管理系统(去重+限制+堆叠+自动消失)
- 全局刷新按钮集成Toast提示
- 修复Dash布局缩进问题
- 删除冗余刷新按钮
- 平台服务费过滤逻辑优化
- 添加B电脑克隆清单和推送脚本"
echo.

echo 推送到Github...
git push origin master
echo.

if %errorlevel%==0 (
    echo ================================
    echo ✅ 推送成功!
    echo ================================
    echo.
    echo 您现在可以在B电脑上执行:
    echo   git clone https://github.com/lichaokun0930/O2O-Analysis.git
) else (
    echo ================================
    echo ❌ 推送失败!
    echo ================================
    echo.
    echo 请检查:
    echo   1. 网络连接是否正常
    echo   2. Github访问权限是否正确
    echo   3. 是否需要先拉取远程更新 (git pull)
)

echo.
pause
