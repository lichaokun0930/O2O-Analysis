# A电脑创建迁移工作流

param(
    [Parameter(Mandatory=$true)]
    [string]$description
)

Write-Host "=" * 60
Write-Host "A电脑: 创建并应用迁移"
Write-Host "=" * 60

# 激活虚拟环境
.\.venv\Scripts\Activate.ps1

# 生成迁移文件名
$timestamp = Get-Date -Format "yyyyMMdd_HHmm"

# 获取下一个版本号
$existing = Get-ChildItem "database\migrations\v*.sql" -Name | ForEach-Object {
    if ($_ -match "^v(\d+)_") {
        [int]$matches[1]
    }
} | Sort-Object -Descending | Select-Object -First 1

$version = if ($existing) { $existing + 1 } else { 2 }

$filename = "v${version}_${description}.sql"
$filepath = "database\migrations\$filename"

# 检查文件是否已存在
if (Test-Path $filepath) {
    Write-Host "`n✗ 文件已存在: $filename" -ForegroundColor Red
    exit 1
}

# 复制模板
Copy-Item "database\migrations\migration_template.sql" $filepath
Write-Host "`n✓ 已创建迁移文件: $filename" -ForegroundColor Green

# 替换模板中的占位符
$content = Get-Content $filepath -Raw -Encoding UTF8
$content = $content -replace "YYYY-MM-DD", (Get-Date -Format "yyyy-MM-dd")
$content = $content -replace "描述这次迁移的目的", "添加 $description 相关字段"
$content = $content -replace "new_field", $description
Set-Content $filepath $content -Encoding UTF8

Write-Host "`n请编辑迁移文件,添加ALTER TABLE语句" -ForegroundColor Yellow
Write-Host "文件路径: $filepath`n" -ForegroundColor Cyan

# 打开编辑器
notepad $filepath

Write-Host "`n编辑完成后,按Enter键继续..." -ForegroundColor Yellow
Read-Host

# 显示文件内容预览
Write-Host "`n迁移文件预览:" -ForegroundColor Cyan
Write-Host "-" * 60
Get-Content $filepath | Select-Object -First 20
Write-Host "..." -ForegroundColor Gray
Write-Host "-" * 60

# 确认是否应用
$confirm = Read-Host "`n是否应用此迁移到A电脑数据库? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "`n✗ 已取消" -ForegroundColor Yellow
    exit 0
}

# 应用迁移
Write-Host "`n[1/3] 应用迁移到数据库..." -ForegroundColor Cyan
python database\migrations\apply_migration.py $filename

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n✗ 迁移应用失败!" -ForegroundColor Red
    Write-Host "请检查SQL语法并重新运行" -ForegroundColor Yellow
    exit 1
}

# 验证
Write-Host "`n[2/3] 验证数据库结构..." -ForegroundColor Cyan
python database\migrations\check_structure.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n⚠ 数据库结构可能不一致,请检查" -ForegroundColor Yellow
}

# 查看Git状态
Write-Host "`n[3/3] 准备提交..." -ForegroundColor Cyan
git status

Write-Host "`n" "=" * 60
Write-Host "✓ 迁移创建和应用完成!" -ForegroundColor Green
Write-Host "=" * 60

Write-Host "`n下一步: 提交到Git" -ForegroundColor Yellow
Write-Host "`n建议的提交命令:" -ForegroundColor Cyan
Write-Host "  git add database\migrations\$filename database\models.py" -ForegroundColor White
Write-Host "  git commit -m `"添加 $description 字段`"" -ForegroundColor White
Write-Host "  git push" -ForegroundColor White

Write-Host "`n或者运行:" -ForegroundColor Cyan
Write-Host "  .\A电脑_提交迁移.ps1 `"$filename`" `"添加 $description 字段`"" -ForegroundColor White
