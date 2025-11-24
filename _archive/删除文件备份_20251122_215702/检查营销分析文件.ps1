Write-Host "================================" -ForegroundColor Cyan
Write-Host "检查营销分析模型文件" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

Write-Host "`n1️⃣ 检查文件是否存在..." -ForegroundColor Yellow

$files = @(
    "科学八象限分析器.py",
    "评分模型分析器.py",
    "verify_check\octant_analyzer.py",
    "verify_check\scoring_analyzer.py"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file (不存在)" -ForegroundColor Red
    }
}

Write-Host "`n2️⃣ 检查Git跟踪状态..." -ForegroundColor Yellow
Write-Host "已跟踪的营销分析文件:" -ForegroundColor White
git ls-files | Select-String "八象限|评分|octant|scoring"

Write-Host "`n3️⃣ 检查Git暂存状态..." -ForegroundColor Yellow
Write-Host "未暂存的营销分析文件:" -ForegroundColor White
git status --porcelain | Select-String "八象限|评分|octant|scoring"

Write-Host "`n4️⃣ 添加营销分析文件到Git..." -ForegroundColor Yellow
git add "科学八象限分析器.py" "评分模型分析器.py"

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ 文件已添加到暂存区" -ForegroundColor Green
} else {
    Write-Host "  ❌ 添加失败" -ForegroundColor Red
}

Write-Host "`n5️⃣ 最终状态检查..." -ForegroundColor Yellow
git status --short | Select-String "八象限|评分"

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "检查完成!" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

Write-Host "`n按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
