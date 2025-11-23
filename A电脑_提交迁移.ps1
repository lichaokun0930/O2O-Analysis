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

# 首先添加迁移文件
git add $filepath
git add database\models.py

# 检查是否有其他修改的文件
$status = git status --short
if ($status) {
    Write-Host "`n当前工作区状态:" -ForegroundColor Yellow
    Write-Host $status
    Write-Host ""
    
    # 询问是否提交所有修改
    $choice = Read-Host "提交选项: [1]仅迁移相关 [2]所有修改 (默认1)"
    
    if ($choice -eq '2') {
        Write-Host "`n将提交所有修改文件..." -ForegroundColor Cyan
        git add -A
        
        # 再次显示将要提交的内容
        Write-Host "`n将要提交的文件:" -ForegroundColor Green
        git status --short
        
        $confirm = Read-Host "`n确认提交这些文件? (y/n)"
        if ($confirm -ne 'y') {
            Write-Host "`n✗ 已取消" -ForegroundColor Yellow
            exit 0
        }
    } else {
        Write-Host "`n仅提交迁移相关文件" -ForegroundColor Cyan
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
