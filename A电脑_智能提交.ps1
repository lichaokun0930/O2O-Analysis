# A电脑智能提交 - 自动检测数据库修改并一键推送
# 自动识别: models.py修改 -> 创建迁移 -> 应用 -> 提交所有到GitHub

param(
    [Parameter(Mandatory=$true)]
    [string]$message
)

Write-Host "=" * 60
Write-Host "A电脑: 智能提交到GitHub"
Write-Host "=" * 60

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 检查是否有修改
$allChanges = git status --short
if (-not $allChanges) {
    Write-Host "`n没有待提交的修改" -ForegroundColor Green
    exit 0
}

Write-Host "`n当前修改的文件:" -ForegroundColor Yellow
Write-Host $allChanges

# 关键: 检测是否修改了models.py
$modelsChanged = $allChanges | Where-Object { $_ -match "models\.py" }

if ($modelsChanged) {
    Write-Host "`n检测到database/models.py已修改!" -ForegroundColor Magenta
    Write-Host "=" * 60
    
    # 询问迁移描述
    Write-Host "`n需要创建数据库迁移" -ForegroundColor Yellow
    $description = Read-Host "请输入迁移描述(如: add_delivery_person)"
    
    if (-not $description) {
        Write-Host "`n未输入描述,跳过迁移创建" -ForegroundColor Yellow
        $skipMigration = $true
    } else {
        $skipMigration = $false
        
        # 生成迁移文件名
        $existing = Get-ChildItem "database\migrations\v*.sql" -Name | ForEach-Object {
            if ($_ -match "^v(\d+)_") {
                [int]$matches[1]
            }
        } | Sort-Object -Descending | Select-Object -First 1
        
        $version = if ($existing) { $existing + 1 } else { 2 }
        $filename = "v$version" + "_$description.sql"
        $filepath = "database\migrations\$filename"
        
        # 复制模板
        Write-Host "`n[1/5] 创建迁移文件: $filename" -ForegroundColor Cyan
        Copy-Item "database\migrations\migration_template.sql" $filepath
        
        # 替换占位符
        $content = Get-Content $filepath -Raw -Encoding UTF8
        $dateStr = Get-Date -Format "yyyy-MM-dd"
        $content = $content -replace "YYYY-MM-DD", $dateStr
        $content = $content -replace "描述这次迁移的目的", $message
        $content = $content -replace "new_field", $description
        Set-Content $filepath $content -Encoding UTF8
        
        # 打开编辑器
        Write-Host "请编辑迁移文件,添加ALTER TABLE语句..." -ForegroundColor Yellow
        notepad $filepath
        
        Write-Host "`n编辑完成后,按Enter键继续..." -ForegroundColor Yellow
        Read-Host
        
        # 应用迁移
        Write-Host "`n[2/5] 应用迁移到A电脑数据库..." -ForegroundColor Cyan
        python database\migrations\apply_migration.py $filename
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n迁移应用失败!" -ForegroundColor Red
            Write-Host "请检查SQL语法,修复后重新运行此脚本" -ForegroundColor Yellow
            exit 1
        }
        
        # 验证
        Write-Host "`n[3/5] 验证数据库结构..." -ForegroundColor Cyan
        python database\migrations\check_structure.py
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n数据库结构验证失败!" -ForegroundColor Red
            $continueAnyway = Read-Host "是否继续提交? (y/n)"
            if ($continueAnyway -ne 'y') {
                exit 1
            }
        }
        
        Write-Host "`n迁移创建和应用完成!" -ForegroundColor Green
    }
} else {
    Write-Host "`n未检测到models.py修改,跳过迁移步骤" -ForegroundColor Cyan
    $skipMigration = $true
}

# 提交所有修改到Git
Write-Host "`n" + "=" * 60
Write-Host "准备提交所有修改到GitHub"
Write-Host "=" * 60

# 显示最终要提交的内容
Write-Host "`n最终修改列表:" -ForegroundColor Cyan
$finalChanges = git status --short
Write-Host $finalChanges

# 确认
Write-Host ""
$confirm = Read-Host "确认提交以上所有修改到GitHub? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "`n已取消" -ForegroundColor Yellow
    exit 0
}

# 提交流程
$step = if ($skipMigration) { 1 } else { 4 }
$totalSteps = if ($skipMigration) { 3 } else { 5 }

Write-Host "`n[$step/$totalSteps] 添加所有文件到Git..." -ForegroundColor Cyan
git add -A

$step++
Write-Host "`n[$step/$totalSteps] 提交到本地仓库..." -ForegroundColor Cyan
git commit -m $message

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n提交失败!" -ForegroundColor Red
    exit 1
}

$step++
Write-Host "`n[$step/$totalSteps] 推送到GitHub..." -ForegroundColor Cyan
git push

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n推送失败!" -ForegroundColor Red
    Write-Host "请检查网络连接或手动运行: git push" -ForegroundColor Yellow
    exit 1
}

# 成功
Write-Host "`n" + "=" * 60
Write-Host "成功推送到GitHub!" -ForegroundColor Green
Write-Host "=" * 60

$lastCommit = git log -1 --oneline
Write-Host "`n最新提交: $lastCommit" -ForegroundColor Cyan

if (-not $skipMigration) {
    Write-Host "`n包含数据库迁移: $filename" -ForegroundColor Magenta
}

Write-Host "`n现在B电脑可以运行:" -ForegroundColor Yellow
Write-Host "  .\B电脑_拉取代码.ps1" -ForegroundColor White
Write-Host "`n来同步这些修改`n" -ForegroundColor Yellow
