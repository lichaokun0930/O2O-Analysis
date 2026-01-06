# ================================================================
#          Memurai (Windows Redis) 安装和配置
# ================================================================

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "          Memurai Redis 安装向导" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

Write-Host "📋 Memurai 简介:" -ForegroundColor Yellow
Write-Host "  • Windows原生Redis替代品" -ForegroundColor White
Write-Host "  • 兼容Redis 7.x协议" -ForegroundColor White
Write-Host "  • 开发者版永久免费" -ForegroundColor Green
Write-Host "  • 无需WSL或虚拟化`n" -ForegroundColor White

# 检查是否已安装
$memuraiPath = "C:\Program Files\Memurai\memurai.exe"
$memuraiService = Get-Service -Name "Memurai" -ErrorAction SilentlyContinue

if (Test-Path $memuraiPath) {
    Write-Host "✅ Memurai已安装`n" -ForegroundColor Green
    
    # 检查服务状态
    if ($memuraiService) {
        if ($memuraiService.Status -eq "Running") {
            Write-Host "✅ Memurai服务正在运行`n" -ForegroundColor Green
        } else {
            Write-Host "⚠️  Memurai服务未运行,正在启动..." -ForegroundColor Yellow
            Start-Service -Name "Memurai"
            Start-Sleep -Seconds 2
            Write-Host "✅ Memurai服务已启动`n" -ForegroundColor Green
        }
    }
    
    # 测试连接
    Write-Host "🧪 测试Redis连接..." -ForegroundColor Yellow
    try {
        $testScript = @"
import redis
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    result = r.ping()
    if result:
        print('✅ Redis连接成功! PONG')
        info = r.info('server')
        print(f'Redis版本: {info.get(\"redis_version\", \"未知\")}')
    else:
        print('❌ 连接失败')
except Exception as e:
    print(f'❌ 连接错误: {e}')
"@
        python -c $testScript
    } catch {
        Write-Host "⚠️  Python测试失败,请确保已安装redis包" -ForegroundColor Yellow
    }
    
} else {
    Write-Host "❌ Memurai未安装`n" -ForegroundColor Red
    Write-Host "📥 请按照以下步骤安装:" -ForegroundColor Yellow
    Write-Host "`n步骤 1: 下载Memurai" -ForegroundColor Cyan
    Write-Host "  访问: https://www.memurai.com/get-memurai" -ForegroundColor White
    Write-Host "  选择: Memurai Developer (免费版)" -ForegroundColor Green
    Write-Host "  点击: Download for Windows`n" -ForegroundColor White
    
    Write-Host "步骤 2: 安装Memurai" -ForegroundColor Cyan
    Write-Host "  1. 运行下载的 .msi 安装包" -ForegroundColor White
    Write-Host "  2. 按默认选项安装(Next -> Next -> Install)" -ForegroundColor White
    Write-Host "  3. 安装完成后会自动启动服务`n" -ForegroundColor White
    
    Write-Host "步骤 3: 再次运行此脚本验证" -ForegroundColor Cyan
    Write-Host "  .\安装Memurai_Redis.ps1`n" -ForegroundColor White
    
    Write-Host "是否现在打开下载页面? (Y/N): " -ForegroundColor Yellow -NoNewline
    $response = Read-Host
    if ($response -eq 'Y' -or $response -eq 'y') {
        Start-Process "https://www.memurai.com/get-memurai"
    }
}

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "          连接信息" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  主机: localhost" -ForegroundColor White
Write-Host "  端口: 6379" -ForegroundColor White
Write-Host "  密码: (无)" -ForegroundColor Gray
Write-Host "`n  Python连接示例:" -ForegroundColor Yellow
Write-Host "    import redis" -ForegroundColor Gray
Write-Host "    r = redis.Redis(host='localhost', port=6379)" -ForegroundColor Gray
Write-Host "    r.ping()  # 返回True表示连接成功" -ForegroundColor Gray
Write-Host "================================================================`n" -ForegroundColor Cyan
