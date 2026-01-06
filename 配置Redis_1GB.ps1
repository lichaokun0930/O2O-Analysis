# 配置Redis为1GB内存（适合100家门店）

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host " 配置Redis内存限制为1GB" -ForegroundColor Yellow
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# 检查Redis是否运行
Write-Host "🔍 检查Redis服务..." -ForegroundColor Yellow
$redisRunning = $false

# 检查Memurai服务
$memuraiService = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue
if ($memuraiService -and $memuraiService.Status -eq "Running") {
    Write-Host "✅ Memurai服务正在运行" -ForegroundColor Green
    $redisRunning = $true
} else {
    Write-Host "⚠️ Memurai服务未运行，尝试启动..." -ForegroundColor Yellow
    try {
        Start-Service -Name "Memurai" -ErrorAction Stop
        Start-Sleep -Seconds 2
        Write-Host "✅ Memurai服务已启动" -ForegroundColor Green
        $redisRunning = $true
    } catch {
        Write-Host "❌ 无法启动Memurai服务" -ForegroundColor Red
        Write-Host "   请手动启动Redis或运行: .\启动Redis.ps1" -ForegroundColor Gray
        Read-Host "按回车键退出"
        exit 1
    }
}

if (-not $redisRunning) {
    Write-Host "❌ Redis未运行，无法配置" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "⚙️ 配置Redis参数..." -ForegroundColor Yellow

# 使用redis-cli配置
try {
    # 检查redis-cli是否可用
    $redisCli = "redis-cli"
    $testResult = & $redisCli ping 2>&1
    
    if ($testResult -ne "PONG") {
        Write-Host "❌ redis-cli不可用或Redis连接失败" -ForegroundColor Red
        Write-Host "   请确保Redis正在运行且redis-cli在PATH中" -ForegroundColor Gray
        Read-Host "按回车键退出"
        exit 1
    }
    
    Write-Host "✅ Redis连接成功" -ForegroundColor Green
    Write-Host ""
    
    # 获取当前配置
    Write-Host "📊 当前配置:" -ForegroundColor Cyan
    $currentMaxmemory = & $redisCli CONFIG GET maxmemory
    $currentPolicy = & $redisCli CONFIG GET maxmemory-policy
    
    if ($currentMaxmemory[1] -eq "0") {
        Write-Host "   内存限制: 无限制" -ForegroundColor Gray
    } else {
        $currentMB = [math]::Round($currentMaxmemory[1] / 1024 / 1024, 0)
        Write-Host "   内存限制: ${currentMB}MB" -ForegroundColor Gray
    }
    Write-Host "   淘汰策略: $($currentPolicy[1])" -ForegroundColor Gray
    Write-Host ""
    
    # 设置新配置
    Write-Host "🔧 设置新配置..." -ForegroundColor Yellow
    
    # 设置内存限制为1GB
    $result1 = & $redisCli CONFIG SET maxmemory 1gb 2>&1
    if ($result1 -eq "OK") {
        Write-Host "   ✅ 内存限制已设置为1GB" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 设置内存限制失败: $result1" -ForegroundColor Red
    }
    
    # 设置淘汰策略为allkeys-lru
    $result2 = & $redisCli CONFIG SET maxmemory-policy allkeys-lru 2>&1
    if ($result2 -eq "OK") {
        Write-Host "   ✅ 淘汰策略已设置为allkeys-lru" -ForegroundColor Green
    } else {
        Write-Host "   ❌ 设置淘汰策略失败: $result2" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # 验证新配置
    Write-Host "✔️ 验证新配置:" -ForegroundColor Cyan
    $newMaxmemory = & $redisCli CONFIG GET maxmemory
    $newPolicy = & $redisCli CONFIG GET maxmemory-policy
    
    $newMB = [math]::Round($newMaxmemory[1] / 1024 / 1024, 0)
    Write-Host "   内存限制: ${newMB}MB" -ForegroundColor Green
    Write-Host "   淘汰策略: $($newPolicy[1])" -ForegroundColor Green
    Write-Host ""
    
    # 尝试持久化配置
    Write-Host "💾 尝试持久化配置..." -ForegroundColor Yellow
    $rewriteResult = & $redisCli CONFIG REWRITE 2>&1
    if ($rewriteResult -eq "OK") {
        Write-Host "   ✅ 配置已保存到配置文件" -ForegroundColor Green
        Write-Host "   （重启Redis后配置仍然有效）" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠️ 无法保存到配置文件: $rewriteResult" -ForegroundColor Yellow
        Write-Host "   （配置仅在当前会话有效，重启后需重新配置）" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "=" * 70 -ForegroundColor Cyan
    Write-Host " ✅ Redis配置完成" -ForegroundColor Green
    Write-Host "=" * 70 -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 配置摘要:" -ForegroundColor Cyan
    Write-Host "   - 内存限制: 1GB" -ForegroundColor White
    Write-Host "   - 淘汰策略: allkeys-lru（自动淘汰最少使用的键）" -ForegroundColor White
    Write-Host "   - 适用场景: 100家门店，300万行数据" -ForegroundColor White
    Write-Host "   - 预期使用率: 40%（健康范围）" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 下一步:" -ForegroundColor Cyan
    Write-Host "   1. 运行测试: python 测试V8.4分层缓存.py" -ForegroundColor Gray
    Write-Host "   2. 启动看板: .\启动看板-调试模式.ps1" -ForegroundColor Gray
    Write-Host "   3. 监控内存: redis-cli INFO memory" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host "❌ 配置失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 手动配置方法:" -ForegroundColor Cyan
    Write-Host "   1. 打开命令行: redis-cli" -ForegroundColor Gray
    Write-Host "   2. 执行命令: CONFIG SET maxmemory 1gb" -ForegroundColor Gray
    Write-Host "   3. 执行命令: CONFIG SET maxmemory-policy allkeys-lru" -ForegroundColor Gray
    Write-Host "   4. 保存配置: CONFIG REWRITE" -ForegroundColor Gray
    Write-Host ""
}

Read-Host "按回车键退出"
