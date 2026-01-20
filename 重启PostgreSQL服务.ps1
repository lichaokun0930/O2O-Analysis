# PostgreSQL 服务重启脚本
# 需要以管理员权限运行

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  重启 PostgreSQL 服务以应用新配置" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否以管理员权限运行
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️ 需要管理员权限，正在请求提升..." -ForegroundColor Yellow
    Start-Process powershell -Verb RunAs -ArgumentList "-NoExit -File `"$PSCommandPath`""
    exit
}

Write-Host "✅ 已获得管理员权限" -ForegroundColor Green
Write-Host ""

# 查找 PostgreSQL 服务
$pgService = Get-Service -Name "postgresql*" | Select-Object -First 1

if ($pgService) {
    Write-Host "📌 找到服务: $($pgService.Name)" -ForegroundColor Cyan
    Write-Host "📌 当前状态: $($pgService.Status)" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "🔄 正在重启服务..." -ForegroundColor Yellow
    Restart-Service -Name $pgService.Name -Force
    Start-Sleep -Seconds 5
    
    $pgService = Get-Service -Name $pgService.Name
    if ($pgService.Status -eq "Running") {
        Write-Host "✅ PostgreSQL 服务已成功重启！" -ForegroundColor Green
    } else {
        Write-Host "❌ 服务重启失败，状态: $($pgService.Status)" -ForegroundColor Red
    }
} else {
    Write-Host "❌ 未找到 PostgreSQL 服务" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan

# 验证新配置
Write-Host ""
Write-Host "📊 验证新配置..." -ForegroundColor Cyan
Write-Host ""

# 等待服务完全启动
Start-Sleep -Seconds 3

# 使用 Python 验证
$pythonScript = @"
from database.connection import engine
from sqlalchemy import text

print('当前 PostgreSQL 配置:')
print('-' * 40)
with engine.connect() as conn:
    for param in ['max_connections', 'shared_buffers', 'work_mem', 'effective_cache_size']:
        result = conn.execute(text(f'SHOW {param}')).scalar()
        print(f'  {param}: {result}')
"@

Set-Location $PSScriptRoot
python -c $pythonScript

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
