# B电脑拉取所有代码更新
# 用于同步A电脑的非数据库代码修改(看板、分析引擎、工具脚本等)

$separator = "=" * 60
Write-Host $separator
Write-Host "B电脑: 拉取所有代码更新"
Write-Host $separator

# 检查当前状态
Write-Host "`n检查本地修改..." -ForegroundColor Cyan
$localChanges = git status --short

if ($localChanges) {
    Write-Host "`n警告: 本地有未提交的修改" -ForegroundColor Yellow
    Write-Host $localChanges
    Write-Host ""
    $action = Read-Host "操作选项: [1]暂存本地修改 [2]放弃本地修改 [3]取消 (默认3)"
    
    switch ($action) {
        '1' {
            Write-Host "`n暂存本地修改..." -ForegroundColor Cyan
            git stash save "B电脑本地修改-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            Write-Host "本地修改已暂存,拉取完成后可运行: git stash pop" -ForegroundColor Green
        }
        '2' {
            Write-Host "`n放弃本地修改..." -ForegroundColor Cyan
            $confirm = Read-Host "确认放弃所有本地修改? (yes/no)"
            if ($confirm -eq 'yes') {
                git reset --hard HEAD
                git clean -fd
                Write-Host "本地修改已清除" -ForegroundColor Green
            } else {
                Write-Host "已取消" -ForegroundColor Yellow
                exit 0
            }
        }
        default {
            Write-Host "`n已取消" -ForegroundColor Yellow
            Write-Host "请先提交或暂存本地修改" -ForegroundColor Cyan
            exit 0
        }
    }
}

# 拉取代码
Write-Host "`n[1/3] 拉取最新代码..." -ForegroundColor Cyan

# 记录拉取前的提交哈希，用于后续对比
$beforePull = git rev-parse HEAD 2>$null

git pull origin master

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n拉取失败! 尝试设置上游分支后重试..." -ForegroundColor Yellow
    git pull -u origin master
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n拉取失败!" -ForegroundColor Red
        Write-Host "可能原因:" -ForegroundColor Yellow
        Write-Host "  1. 网络问题" -ForegroundColor White
        Write-Host "  2. 本地和远程有冲突" -ForegroundColor White
        Write-Host "  3. 分支配置问题" -ForegroundColor White
        exit 1
    }
}

# 显示更新内容
Write-Host "`n[2/3] 查看更新内容..." -ForegroundColor Cyan
$lastCommit = git log -1 --oneline

# 安全获取变更文件列表
$afterPull = git rev-parse HEAD
if ($beforePull -and $beforePull -ne $afterPull) {
    $changedFiles = git diff --name-only $beforePull $afterPull
} else {
    $changedFiles = $null
    Write-Host "已是最新版本，无需更新" -ForegroundColor Green
}

Write-Host "最新提交: $lastCommit" -ForegroundColor Green

if ($changedFiles) {
    Write-Host "`n更新的文件:" -ForegroundColor Yellow
    $changedFiles | ForEach-Object { 
        if ($_ -match "\.py$") {
            Write-Host "  Python  $_" -ForegroundColor Cyan
        } elseif ($_ -match "\.md$") {
            Write-Host "  文档    $_" -ForegroundColor Gray
        } elseif ($_ -match "migrations") {
            Write-Host "  迁移    $_" -ForegroundColor Magenta
        } elseif ($_ -match "\.ps1$") {
            Write-Host "  脚本    $_" -ForegroundColor Green
        } else {
            Write-Host "  其他    $_" -ForegroundColor White
        }
    }
}

# 检查是否需要同步数据库
$hasMigrations = $changedFiles | Where-Object { $_ -match "migrations|models.py" }

if ($hasMigrations) {
    Write-Host "`n[3/3] 检测到数据库相关修改..." -ForegroundColor Yellow
    $syncDb = Read-Host "是否同步数据库结构? (y/n)"
    
    if ($syncDb -eq 'y') {
        Write-Host "`n运行数据库同步..." -ForegroundColor Cyan
        .\B电脑_同步数据库.ps1
    } else {
        Write-Host "`n稍后手动运行: .\B电脑_同步数据库.ps1" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n[3/3] 无数据库相关修改" -ForegroundColor Cyan
    Write-Host "如需清理缓存，可手动重启看板" -ForegroundColor Gray
}

Write-Host "`n$separator"
Write-Host "代码更新完成!" -ForegroundColor Green
Write-Host $separator

Write-Host "`n下一步: 重启看板验证功能" -ForegroundColor Yellow
Write-Host "  .\启动看板.ps1" -ForegroundColor Cyan
Write-Host ""
