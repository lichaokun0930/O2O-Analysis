# A电脑提交迁移到Git

param(
    [Parameter(Mandatory=$true)]
    [string]$filename,
    
    [Parameter(Mandatory=$true)]
    [string]$message
)

Write-Host "=" * 60
Write-Host "A电脑: 提交迁移到Git"
Write-Host "=" * 60

# 验证迁移文件存在
$filepath = "database\migrations\$filename"
if (-not (Test-Path $filepath)) {
    Write-Host "`n✗ 迁移文件不存在: $filename" -ForegroundColor Red
    exit 1
}

Write-Host "`n[1/4] 添加文件到Git..." -ForegroundColor Cyan
git add $filepath
git add database\models.py

# 检查是否有其他相关文件修改
$status = git status --short
if ($status) {
    Write-Host "`n当前修改的文件:" -ForegroundColor Yellow
    Write-Host $status
    
    $addMore = Read-Host "`n是否添加其他文件? (y/n,默认n)"
    if ($addMore -eq 'y') {
        Write-Host "请手动运行: git add <文件路径>" -ForegroundColor Cyan
        Write-Host "然后重新运行此脚本`n" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "`n[2/4] 提交到本地仓库..." -ForegroundColor Cyan
git commit -m $message

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n✗ 提交失败!" -ForegroundColor Red
    exit 1
}

Write-Host "`n[3/4] 推送到远程仓库..." -ForegroundColor Cyan
git push

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n✗ 推送失败!" -ForegroundColor Red
    Write-Host "请检查网络连接或手动运行: git push" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n[4/4] 验证推送结果..." -ForegroundColor Cyan
$lastCommit = git log -1 --oneline
Write-Host "最新提交: $lastCommit" -ForegroundColor Green

Write-Host "`n" "=" * 60
Write-Host "✓ 迁移已成功提交到GitHub!" -ForegroundColor Green
Write-Host "=" * 60

Write-Host "`n现在B电脑可以运行:" -ForegroundColor Yellow
Write-Host "  .\B电脑_同步数据库.ps1" -ForegroundColor White
Write-Host "`n来同步这个迁移`n" -ForegroundColor Yellow
