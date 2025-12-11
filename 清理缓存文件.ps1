# 清理 Python 缓存文件，释放空间并解决 VS Code 崩溃问题

Write-Host "开始清理 Python 缓存文件..." -ForegroundColor Green

# 清理 __pycache__ 目录
$pycacheDirs = Get-ChildItem -Path "." -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
$count = ($pycacheDirs | Measure-Object).Count
Write-Host "找到 $count 个 __pycache__ 目录" -ForegroundColor Yellow

foreach ($dir in $pycacheDirs) {
    Remove-Item -Path $dir.FullName -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "已删除: $($dir.FullName)" -ForegroundColor Gray
}

# 清理 .pyc 文件
$pycFiles = Get-ChildItem -Path "." -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue
$pycCount = ($pycFiles | Measure-Object).Count
Write-Host "找到 $pycCount 个 .pyc 文件" -ForegroundColor Yellow

foreach ($file in $pycFiles) {
    Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
}

# 清理 .pyo 文件
$pyoFiles = Get-ChildItem -Path "." -Recurse -Filter "*.pyo" -ErrorAction SilentlyContinue
$pyoCount = ($pyoFiles | Measure-Object).Count
Write-Host "找到 $pyoCount 个 .pyo 文件" -ForegroundColor Yellow

foreach ($file in $pyoFiles) {
    Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
}

Write-Host "`n清理完成！" -ForegroundColor Green
Write-Host "已删除 $count 个缓存目录和 $($pycCount + $pyoCount) 个缓存文件" -ForegroundColor Cyan
Write-Host "`n现在可以重新打开 VS Code 了" -ForegroundColor Green
