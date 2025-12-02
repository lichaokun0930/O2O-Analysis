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
    
    # 🔧 智能识别新增字段及其类型
    $modelsDiff = git diff database/models.py
    $newFields = @()
    $fieldDetails = @{}  # 存储字段名 -> 类型映射
    
    foreach ($line in $modelsDiff -split "`n") {
        # 匹配新增的 Column 定义行，提取字段名和类型
        # 例如: +    store_code = Column(String(100), index=True, comment='店内码')
        if ($line -match '^\+\s+(\w+)\s*=\s*Column\((\w+)(\((\d+)\))?') {
            $fieldName = $matches[1]
            $fieldType = $matches[2]
            $fieldLength = $matches[4]
            
            # 排除非字段的行
            if ($fieldName -and $fieldName -notmatch '^#|^_') {
                $newFields += $fieldName
                
                # 转换Python类型到SQL类型
                $sqlType = switch ($fieldType) {
                    'String' { if ($fieldLength) { "VARCHAR($fieldLength)" } else { "VARCHAR(255)" } }
                    'Integer' { "INTEGER" }
                    'Float' { "REAL" }
                    'Boolean' { "BOOLEAN" }
                    'Text' { "TEXT" }
                    'DateTime' { "TIMESTAMP" }
                    'Date' { "DATE" }
                    'Numeric' { "NUMERIC" }
                    default { "VARCHAR(255)" }
                }
                $fieldDetails[$fieldName] = $sqlType
            }
        }
    }
    
    if ($newFields.Count -gt 0) {
        # 自动生成迁移描述
        $autoDescription = "add_" + ($newFields -join "_")
        Write-Host "`n🔍 智能识别到新增字段: $($newFields -join ', ')" -ForegroundColor Green
        Write-Host "   建议迁移描述: $autoDescription" -ForegroundColor Cyan
        $useAuto = Read-Host "使用此描述? (Y=使用 / N=手动输入 / S=跳过迁移)"
        
        if ($useAuto -eq 'S' -or $useAuto -eq 's') {
            Write-Host "跳过迁移创建" -ForegroundColor Yellow
            $skipMigration = $true
            $description = $null
        } elseif ($useAuto -eq 'N' -or $useAuto -eq 'n') {
            $description = Read-Host "请输入迁移描述"
            if (-not $description) { $skipMigration = $true } else { $skipMigration = $false }
        } else {
            # 默认使用自动识别的描述
            $description = $autoDescription
            $skipMigration = $false
            Write-Host "使用自动识别的描述: $description" -ForegroundColor Green
        }
    } else {
        # 无法自动识别，回退到手动输入
        Write-Host "`n未能自动识别新增字段，请手动输入" -ForegroundColor Yellow
        $description = Read-Host "请输入迁移描述(如: add_delivery_person)，留空跳过"
        if (-not $description) { $skipMigration = $true } else { $skipMigration = $false }
    }
    
    if (-not $skipMigration -and $description) {
        $existing = Get-ChildItem "database\migrations\v*.sql" -Name | ForEach-Object { if ($_ -match "^v(\d+)_") { [int]$matches[1] } } | Sort-Object -Descending | Select-Object -First 1
        $version = if ($existing) { $existing + 1 } else { 2 }
        $filename = "v$version" + "_$description.sql"
        $filepath = Join-Path $PSScriptRoot "database\migrations\$filename"
        Write-Host "`n[1/5] 创建迁移文件: $filename" -ForegroundColor Cyan
        
        # 🔧 自动生成SQL语句
        $dateStr = Get-Date -Format "yyyy-MM-dd"
        $sqlStatements = @()
        $sqlStatements += "-- 迁移: $description"
        $sqlStatements += "-- 日期: $dateStr"
        $sqlStatements += "-- 描述: $message"
        $sqlStatements += ""
        
        foreach ($field in $newFields) {
            $sqlType = $fieldDetails[$field]
            if (-not $sqlType) { $sqlType = "VARCHAR(255)" }
            $sqlStatements += "-- 添加 $field 字段"
            $sqlStatements += "ALTER TABLE orders ADD COLUMN IF NOT EXISTS $field $sqlType;"
            # 如果原始代码包含 index=True，添加索引
            $indexMatch = $modelsDiff | Select-String -Pattern "\+\s+$field\s*=.*index\s*=\s*True"
            if ($indexMatch) {
                $sqlStatements += "CREATE INDEX IF NOT EXISTS idx_orders_$field ON orders($field);"
            }
            $sqlStatements += ""
        }
        
        # 写入文件（使用无BOM的UTF-8编码）
        $sqlContent = $sqlStatements -join "`n"
        [System.IO.File]::WriteAllText($filepath, $sqlContent, [System.Text.UTF8Encoding]::new($false))
        
        Write-Host "`n📝 自动生成的SQL语句:" -ForegroundColor Green
        Write-Host $sqlContent -ForegroundColor Gray
        Write-Host ""
        
        $editSql = Read-Host "是否需要手动编辑? (Y=编辑 / Enter=直接使用)"
        if ($editSql -eq 'Y' -or $editSql -eq 'y') {
            notepad $filepath
            Write-Host "`n编辑完成后,按Enter键继续..." -ForegroundColor Yellow
            Read-Host
        }
        
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
git push origin master
if ($LASTEXITCODE -ne 0) { 
    Write-Host "推送失败! 尝试设置上游分支后重试..." -ForegroundColor Yellow
    git push -u origin master
    if ($LASTEXITCODE -ne 0) { Write-Host "推送失败! 请检查网络连接或GitHub权限" -ForegroundColor Red; exit 1 }
}
Write-Host "`n" + "=" * 60
Write-Host "成功推送到GitHub!" -ForegroundColor Green
Write-Host "=" * 60
$lastCommit = git log -1 --oneline
Write-Host "`n最新提交: $lastCommit" -ForegroundColor Cyan
if (-not $skipMigration) { Write-Host "`n包含数据库迁移: $filename" -ForegroundColor Magenta }
Write-Host "`n现在B电脑可以运行:" -ForegroundColor Yellow
Write-Host "  .\B电脑_拉取代码.ps1" -ForegroundColor White
Write-Host ""