param([Parameter(Mandatory=$true)][string]$message)
Write-Host "=" * 60
Write-Host "A电脑: 智能提交到GitHub"
Write-Host "=" * 60
.\.venv\Scripts\Activate.ps1
$allChanges = git status --short
if (-not $allChanges) { Write-Host "没有待提交的修改" -ForegroundColor Green; exit 0 }
Write-Host "`n当前修改的文件:" -ForegroundColor Yellow
Write-Host $allChanges
$modelsChanged = $allChanges | Where-Object { $_ -match "models\.py" }
if ($modelsChanged) {
    Write-Host "`n检测到database/models.py已修改!" -ForegroundColor Magenta
    Write-Host "=" * 60
    Write-Host "`n需要创建数据库迁移" -ForegroundColor Yellow
    $description = Read-Host "请输入迁移描述(如: add_delivery_person)"
    if (-not $description) { Write-Host "未输入描述,跳过迁移创建" -ForegroundColor Yellow; $skipMigration = $true }
    else {
        $skipMigration = $false
        $existing = Get-ChildItem "database\migrations\v*.sql" -Name | ForEach-Object { if ($_ -match "^v(\d+)_") { [int]$matches[1] } } | Sort-Object -Descending | Select-Object -First 1
        $version = if ($existing) { $existing + 1 } else { 2 }
        $filename = "v$version" + "_$description.sql"
        $filepath = "database\migrations\$filename"
        Write-Host "`n[1/5] 创建迁移文件: $filename" -ForegroundColor Cyan
        Copy-Item "database\migrations\migration_template.sql" $filepath
        $content = Get-Content $filepath -Raw -Encoding UTF8
        $dateStr = Get-Date -Format "yyyy-MM-dd"
        $content = $content.Replace("YYYY-MM-DD", $dateStr).Replace("描述这次迁移的目的", $message).Replace("new_field", $description)
        Set-Content $filepath $content -Encoding UTF8
        Write-Host "请编辑迁移文件,添加ALTER TABLE语句..." -ForegroundColor Yellow
        notepad $filepath
        Write-Host "`n编辑完成后,按Enter键继续..." -ForegroundColor Yellow
        Read-Host
        Write-Host "`n[2/5] 应用迁移到A电脑数据库..." -ForegroundColor Cyan
        python database\migrations\apply_migration.py $filename
        if ($LASTEXITCODE -ne 0) { Write-Host "迁移应用失败!" -ForegroundColor Red; exit 1 }
        Write-Host "`n[3/5] 验证数据库结构..." -ForegroundColor Cyan
        python database\migrations\check_structure.py
        if ($LASTEXITCODE -ne 0) { $continueAnyway = Read-Host "是否继续提交? (y/n)"; if ($continueAnyway -ne 'y') { exit 1 } }
        Write-Host "迁移创建和应用完成!" -ForegroundColor Green
    }
} else { Write-Host "`n未检测到models.py修改,跳过迁移步骤" -ForegroundColor Cyan; $skipMigration = $true }
Write-Host "`n" + "=" * 60
Write-Host "准备提交所有修改到GitHub"
Write-Host "=" * 60
Write-Host "`n最终修改列表:" -ForegroundColor Cyan
$finalChanges = git status --short
Write-Host $finalChanges
Write-Host ""
$confirm = Read-Host "确认提交以上所有修改到GitHub? (y/n)"
if ($confirm -ne 'y') { Write-Host "已取消" -ForegroundColor Yellow; exit 0 }
$step = if ($skipMigration) { 1 } else { 4 }
$totalSteps = if ($skipMigration) { 3 } else { 5 }
Write-Host "`n[$step/$totalSteps] 添加所有文件到Git..." -ForegroundColor Cyan
git add -A
$step++
Write-Host "`n[$step/$totalSteps] 提交到本地仓库..." -ForegroundColor Cyan
git commit -m $message
if ($LASTEXITCODE -ne 0) { Write-Host "提交失败!" -ForegroundColor Red; exit 1 }
$step++
Write-Host "`n[$step/$totalSteps] 推送到GitHub..." -ForegroundColor Cyan
git push
if ($LASTEXITCODE -ne 0) { Write-Host "推送失败!" -ForegroundColor Red; exit 1 }
Write-Host "`n" + "=" * 60
Write-Host "成功推送到GitHub!" -ForegroundColor Green
Write-Host "=" * 60
$lastCommit = git log -1 --oneline
Write-Host "`n最新提交: $lastCommit" -ForegroundColor Cyan
if (-not $skipMigration) { Write-Host "`n包含数据库迁移: $filename" -ForegroundColor Magenta }
Write-Host "`n现在B电脑可以运行:" -ForegroundColor Yellow
Write-Host "  .\B电脑_拉取代码.ps1" -ForegroundColor White
Write-Host ""