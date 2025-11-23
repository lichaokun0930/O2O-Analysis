# B电脑同步数据库结构
# 仅同步数据库迁移,不拉取其他代码

Write-Host "=" * 60
Write-Host "B电脑: 同步数据库结构"
Write-Host "=" * 60

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 0. 检查是否需要先拉取代码
Write-Host "`n[0/4] 检查迁移文件..." -ForegroundColor Cyan
git fetch
$behind = git rev-list HEAD..origin/master --count

if ($behind -gt 0) {
    Write-Host "远程有 $behind 个新提交" -ForegroundColor Yellow
    $pullFirst = Read-Host "是否先拉取代码 (y/n 默认y)"
    
    if ($pullFirst -ne 'n') {
        Write-Host "`n拉取最新代码..." -ForegroundColor Cyan
        git pull
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Git拉取失败" -ForegroundColor Red
            exit 1
        }
    }
}

# 2. 同步迁移
Write-Host "`n[2/4] 同步数据库迁移..." -ForegroundColor Cyan
python database\migrations\sync_migrations.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "迁移同步失败" -ForegroundColor Red
    exit 1
}

# 3. 验证结构
Write-Host "`n[3/4] 验证数据库结构..." -ForegroundColor Cyan
python database\migrations\check_structure.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "数据库结构可能不一致" -ForegroundColor Yellow
}

# 4. 清理缓存
Write-Host "`n[4/4] 清理Redis缓存..." -ForegroundColor Cyan
python 清理Redis缓存.py

Write-Host "`n完成!" -ForegroundColor Green
Write-Host "=" * 60