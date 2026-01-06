# 测试启动脚本日志输出

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "测试启动脚本日志输出" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# 查找Python可执行文件
$parentDir = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $parentDir ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = Join-Path $scriptDir ".venv\Scripts\python.exe"
}
if (-not (Test-Path $pythonExe)) {
    Write-Warning "未找到虚拟环境，将使用系统 python。"
    $pythonExe = "python"
} else {
    Write-Host "✅ 使用虚拟环境: $pythonExe" -ForegroundColor Green
}

Write-Host ""
Write-Host "测试1: 检查Redis管理器是否可用" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Gray

$testScript1 = @"
import sys
sys.path.insert(0, '.')
try:
    from redis_manager import ensure_redis_running, redis_health_check
    print('✅ Redis管理器导入成功')
    
    # 测试Redis连接
    if ensure_redis_running():
        print('✅ Redis可用')
        health = redis_health_check()
        print(f'   - 运行状态: {health["running"]}')
        print(f'   - 内存使用: {health["memory"]}')
        print(f'   - 键数量: {health["keys"]}')
    else:
        print('❌ Redis不可用')
except Exception as e:
    print(f'❌ 错误: {e}')
    import traceback
    traceback.print_exc()
"@

& $pythonExe -c $testScript1

Write-Host ""
Write-Host "测试2: 检查后台任务是否可用" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Gray

$testScript2 = @"
import sys
sys.path.insert(0, '.')
try:
    from background_tasks import get_scheduler_status
    print('✅ 后台任务模块导入成功')
    
    # 注意：这里不启动调度器，只测试导入
    print('   提示: 后台任务会在主程序启动时自动启动')
except Exception as e:
    print(f'❌ 错误: {e}')
    import traceback
    traceback.print_exc()
"@

& $pythonExe -c $testScript2

Write-Host ""
Write-Host "测试3: 模拟主程序启动流程" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Gray

$testScript3 = @"
import sys
sys.path.insert(0, '.')

print('='*80)
print('模拟主程序启动流程')
print('='*80)

# 步骤1: Redis自动启动
print('\n[步骤1] Redis自动启动检查...')
try:
    from redis_manager import ensure_redis_running, redis_health_check
    
    if ensure_redis_running():
        health = redis_health_check()
        if health['running']:
            print(f'✅ Redis服务正常 - 内存: {health["memory"]}, 键数量: {health["keys"]}')
        else:
            print(f'⚠️ Redis健康检查失败: {health.get("error", "未知错误")}')
    else:
        print('⚠️ Redis启动失败，缓存功能将不可用')
except Exception as e:
    print(f'⚠️ Redis管理器异常: {e}')

# 步骤2: 后台任务启动（不实际启动，只显示日志）
print('\n[步骤2] 后台任务启动检查...')
try:
    from background_tasks import start_background_tasks
    print('✅ 后台任务模块已加载')
    print('   提示: 实际启动时会自动运行后台任务')
except Exception as e:
    print(f'⚠️ 后台任务启动失败: {e}')

print('\n' + '='*80)
print('测试完成')
print('='*80)
"@

& $pythonExe -c $testScript3

Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "如果上述测试都通过，说明功能正常。" -ForegroundColor Gray
Write-Host "如果启动看板时看不到这些日志，可能是因为：" -ForegroundColor Gray
Write-Host "1. Python输出被缓冲了（添加 -u 参数强制无缓冲）" -ForegroundColor Yellow
Write-Host "2. 日志被其他输出覆盖了" -ForegroundColor Yellow
Write-Host "3. 启动脚本重定向了输出" -ForegroundColor Yellow
Write-Host ""
Write-Host "建议修改启动脚本，添加 -u 参数：" -ForegroundColor Cyan
Write-Host '   & $pythonExe -u "智能门店看板_Dash版.py"' -ForegroundColor White
Write-Host ""

Read-Host "按回车键退出"
