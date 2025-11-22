# A电脑提交所有修改到Git
# 用于提交非迁移相关的代码修改(看板、分析引擎、工具脚本等)

param(
    [Parameter(Mandatory=$true)]
    [string]$message
)

Write-Host "=" * 60
Write-Host "A电脑: 提交所有修改到Git"
Write-Host "=" * 60

# 检查是否有修改
$status = git status --short
if (-not $status) {
    Write-Host "`n✓ 没有待提交的修改" -ForegroundColor Green
    exit 0
}

Write-Host "`n当前修改的文件:" -ForegroundColor Yellow
Write-Host $status

# 分类显示
Write-Host "`n文件分类:" -ForegroundColor Cyan
$modified = git diff --name-only
$untracked = git ls-files --others --exclude-standard

if ($modified) {
    Write-Host "`n已修改文件:" -ForegroundColor Yellow
    $modified | ForEach-Object { Write-Host "  M  $_" }
}

if ($untracked) {
    Write-Host "`n新增文件:" -ForegroundColor Green
    $untracked | ForEach-Object { Write-Host "  A  $_" }
}

# 确认提交
Write-Host ""
$confirm = Read-Host "是否提交以上所有修改? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "`n✗ 已取消" -ForegroundColor Yellow
    Write-Host "`n如需选择性提交,请使用:" -ForegroundColor Cyan
    Write-Host "  git add <文件路径>" -ForegroundColor White
    Write-Host "  git commit -m `"提交信息`"" -ForegroundColor White
    Write-Host "  git push" -ForegroundColor White
    exit 0
}

Write-Host "`n[1/3] 添加所有文件到Git..." -ForegroundColor Cyan
git add -A

Write-Host "`n[2/3] 提交到本地仓库..." -ForegroundColor Cyan
git commit -m $message

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n✗ 提交失败!" -ForegroundColor Red
    exit 1
}

Write-Host "`n[3/3] 推送到远程仓库..." -ForegroundColor Cyan
git push

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n✗ 推送失败!" -ForegroundColor Red
    Write-Host "请检查网络连接或手动运行: git push" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n验证推送结果..." -ForegroundColor Cyan
$lastCommit = git log -1 --oneline
Write-Host "最新提交: $lastCommit" -ForegroundColor Green

Write-Host "`n" "=" * 60
Write-Host "✓ 所有修改已成功提交到GitHub!" -ForegroundColor Green
Write-Host "=" * 60

Write-Host "`n现在B电脑可以运行:" -ForegroundColor Yellow
Write-Host "  git pull" -ForegroundColor White
Write-Host "  .\B电脑_同步数据库.ps1  # 如果包含数据库修改" -ForegroundColor White
Write-Host "`n来同步这些修改`n" -ForegroundColor Yellow
