# Git推送脚本
Write-Host "================================" -ForegroundColor Cyan
Write-Host "开始推送代码到Github" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# 检查Git仓库
if (!(Test-Path ".git")) {
    Write-Host "❌ 错误:当前目录不是Git仓库!" -ForegroundColor Red
    exit 1
}

# 检查远程仓库
Write-Host "`n📍 检查远程仓库..." -ForegroundColor Yellow
git remote -v

# 检查当前分支
Write-Host "`n🌿 当前分支:" -ForegroundColor Yellow
git branch --show-current

# 查看修改的文件数量
Write-Host "`n📝 修改的文件:" -ForegroundColor Yellow
$changedFiles = git status --porcelain
$fileCount = ($changedFiles | Measure-Object).Count
Write-Host "共 $fileCount 个文件需要提交" -ForegroundColor White

# 显示核心文件状态
Write-Host "`n核心文件状态:" -ForegroundColor Cyan
git status --porcelain | Select-String "智能门店看板_Dash版.py|真实数据处理器.py|requirements.txt"

# 确认推送
Write-Host "`n⚠️  准备推送到Github,包含以下操作:" -ForegroundColor Yellow
Write-Host "  1. 添加所有修改的文件 (git add .)" -ForegroundColor White
Write-Host "  2. 提交更改 (git commit)" -ForegroundColor White
Write-Host "  3. 推送到远程仓库 (git push)" -ForegroundColor White

$confirm = Read-Host "`n是否继续? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "❌ 已取消推送" -ForegroundColor Red
    exit 0
}

# 添加所有文件
Write-Host "`n📦 添加文件..." -ForegroundColor Cyan
git add .

# 提交更改
Write-Host "`n💾 提交更改..." -ForegroundColor Cyan
$commitMessage = @"
feat: Toast队列管理系统+全局刷新按钮优化

主要更新:
- ✨ 实现Toast队列管理系统(去重+限制+堆叠+自动消失)
- ✨ 全局刷新按钮集成Toast提示
- 🐛 修复Dash布局缩进问题
- 🗑️ 删除冗余刷新按钮
- 🔧 平台服务费过滤逻辑优化

技术细节:
- Toast队列自动管理(最多5个,自动去重)
- 全局刷新按钮8步流程完整实施
- MANTINE和Bootstrap两个布局分支都已更新
- 收费渠道列表:10个渠道按类型过滤
"@

git commit -m $commitMessage

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 提交失败!" -ForegroundColor Red
    exit 1
}

# 推送到远程
Write-Host "`n🚀 推送到Github..." -ForegroundColor Cyan
git push origin master

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n================================" -ForegroundColor Green
    Write-Host "✅ 推送成功!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host "`n您现在可以在B电脑上执行:" -ForegroundColor Yellow
    Write-Host "  git clone https://github.com/lichaokun0930/O2O-Analysis.git" -ForegroundColor White
} else {
    Write-Host "`n❌ 推送失败!请检查:" -ForegroundColor Red
    Write-Host "  1. 网络连接是否正常" -ForegroundColor White
    Write-Host "  2. Github访问权限是否正确" -ForegroundColor White
    Write-Host "  3. 是否需要先拉取远程更新 (git pull)" -ForegroundColor White
}

Write-Host "`n按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
