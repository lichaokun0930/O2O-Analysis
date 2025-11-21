# Redis 安装和启动指南

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "          Redis 快速安装和启动                                   " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# 检查Redis是否已安装
$redisInstalled = Get-Command redis-server -ErrorAction SilentlyContinue

if ($redisInstalled) {
    Write-Host "✅ Redis已安装" -ForegroundColor Green
    Write-Host "   路径: $($redisInstalled.Source)" -ForegroundColor Gray
} else {
    Write-Host "⚠️  Redis未安装" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "安装选项:" -ForegroundColor Cyan
    Write-Host "  1️⃣  使用winget安装（推荐）" -ForegroundColor White
    Write-Host "     命令: winget install Redis.Redis" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2️⃣  使用Chocolatey安装" -ForegroundColor White
    Write-Host "     命令: choco install redis-64" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3️⃣  手动下载" -ForegroundColor White
    Write-Host "     地址: https://github.com/microsoftarchive/redis/releases" -ForegroundColor Gray
    Write-Host ""
    
    $choice = Read-Host "是否现在使用winget安装? (y/n)"
    if ($choice -eq 'y' -or $choice -eq 'Y') {
        Write-Host ""
        Write-Host "开始安装Redis..." -ForegroundColor Cyan
        winget install Redis.Redis
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Redis安装成功!" -ForegroundColor Green
        } else {
            Write-Host "❌ 安装失败，请手动安装" -ForegroundColor Red
            exit
        }
    } else {
        Write-Host "请手动安装Redis后再运行此脚本" -ForegroundColor Yellow
        exit
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "          启动Redis服务                                          " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# 检查Redis是否正在运行
$redisProcess = Get-Process redis-server -ErrorAction SilentlyContinue

if ($redisProcess) {
    Write-Host "✅ Redis已在运行" -ForegroundColor Green
    Write-Host "   PID: $($redisProcess.Id)" -ForegroundColor Gray
    Write-Host "   内存: $([math]::Round($redisProcess.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor Gray
    Write-Host ""
    
    $restart = Read-Host "是否重启Redis? (y/n)"
    if ($restart -eq 'y' -or $restart -eq 'Y') {
        Write-Host "停止Redis..." -ForegroundColor Yellow
        Stop-Process -Id $redisProcess.Id -Force
        Start-Sleep -Seconds 2
    } else {
        Write-Host ""
        Write-Host "Redis服务地址: localhost:6379" -ForegroundColor Cyan
        Write-Host ""
        exit
    }
}

# 启动Redis
Write-Host "启动Redis服务..." -ForegroundColor Cyan

# 查找Redis配置文件
$redisConf = "redis.windows.conf"
if (Test-Path $redisConf) {
    Write-Host "使用配置文件: $redisConf" -ForegroundColor Gray
    Start-Process redis-server -ArgumentList $redisConf -WindowStyle Minimized
} else {
    # 使用默认配置
    Start-Process redis-server -WindowStyle Minimized
}

Start-Sleep -Seconds 3

# 验证启动
$redisProcess = Get-Process redis-server -ErrorAction SilentlyContinue

if ($redisProcess) {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host "          ✅ Redis启动成功!                                     " -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "服务信息:" -ForegroundColor Cyan
    Write-Host "  地址: localhost:6379" -ForegroundColor White
    Write-Host "  PID: $($redisProcess.Id)" -ForegroundColor White
    Write-Host "  内存: $([math]::Round($redisProcess.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor White
    Write-Host ""
    Write-Host "测试连接:" -ForegroundColor Cyan
    Write-Host "  python -c `"import redis; r=redis.Redis(); print('✅ 连接成功!' if r.ping() else '❌ 连接失败')`"" -ForegroundColor Gray
    Write-Host ""
    Write-Host "管理命令:" -ForegroundColor Cyan
    Write-Host "  redis-cli           # 进入Redis命令行" -ForegroundColor Gray
    Write-Host "  redis-cli ping      # 测试连接" -ForegroundColor Gray
    Write-Host "  redis-cli info      # 查看信息" -ForegroundColor Gray
    Write-Host "  redis-cli flushall  # 清空所有数据" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ Redis启动失败" -ForegroundColor Red
    Write-Host "   请检查是否已正确安装Redis" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
