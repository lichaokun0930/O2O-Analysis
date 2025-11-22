# B电脑一键同步数据库结构

Write-Host "=" * 60
Write-Host "B电脑: 同步数据库结构"
Write-Host "=" * 60

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 1. 拉取代码
Write-Host "`n[1/4] 拉取最新代码..."
git pull

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Git拉取失败" -ForegroundColor Red
    exit 1
}

# 2. 同步迁移
Write-Host "`n[2/4] 同步数据库迁移..."
python database\migrations\sync_migrations.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 迁移同步失败" -ForegroundColor Red
    exit 1
}

# 3. 验证结构
Write-Host "`n[3/4] 验证数据库结构..."
python database\migrations\check_structure.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ 数据库结构可能不一致" -ForegroundColor Yellow
}

# 4. 清理缓存
Write-Host "`n[4/4] 清理Redis缓存..."
python 清理Redis缓存.py

Write-Host "`n" + "=" * 60
Write-Host "✓ 同步完成!" -ForegroundColor Green
Write-Host "=" * 60

Write-Host "`n下一步: 重启看板验证功能"
Write-Host "  .\启动看板.ps1" -ForegroundColor Cyan
