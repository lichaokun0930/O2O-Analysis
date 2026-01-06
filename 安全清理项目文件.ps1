# 项目文件安全清理脚本
# 包含交互式确认和备份功能

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "项目文件安全清理工具" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# 统计信息
$stats = @{
    '旧版本文档' = 46
    '测试脚本' = 21
    '诊断工具' = 7
    'A/B电脑脚本' = 5
    '临时文件' = 2
    '冗余安装脚本' = 4
    '冗余Git脚本' = 1
}

$totalFiles = ($stats.Values | Measure-Object -Sum).Sum

Write-Host "📊 清理统计:" -ForegroundColor Yellow
foreach ($category in $stats.Keys) {
    Write-Host "   - $category : $($stats[$category]) 个" -ForegroundColor Gray
}
Write-Host "   总计: $totalFiles 个文件" -ForegroundColor White
Write-Host ""

Write-Host "⚠️  注意事项:" -ForegroundColor Yellow
Write-Host "   1. 清理前会自动创建备份" -ForegroundColor Gray
Write-Host "   2. 只删除已确认的旧文件" -ForegroundColor Gray
Write-Host "   3. 核心运行文件不会被删除" -ForegroundColor Gray
Write-Host "   4. 可以随时从备份恢复" -ForegroundColor Gray
Write-Host ""

# 询问用户
$confirm = Read-Host "是否继续清理? (Y/N)"
if ($confirm -ne 'Y' -and $confirm -ne 'y') {
    Write-Host "已取消清理" -ForegroundColor Yellow
    exit
}

Write-Host ""
Write-Host "🔄 开始清理..." -ForegroundColor Cyan
Write-Host ""

# 创建备份目录
$backupDir = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Write-Host "✅ 已创建备份目录: $backupDir" -ForegroundColor Green

# 备份函数
function Backup-And-Remove {
    param($filePath)
    
    if (Test-Path $filePath) {
        $fileName = Split-Path $filePath -Leaf
        $backupPath = Join-Path $backupDir $fileName
        
        try {
            Copy-Item $filePath $backupPath -ErrorAction Stop
            Remove-Item $filePath -ErrorAction Stop
            return $true
        } catch {
            Write-Host "   ⚠️  处理失败: $fileName - $_" -ForegroundColor Red
            return $false
        }
    }
    return $false
}

$deletedCount = 0

# 1. 清理旧版本文档
Write-Host "`n📄 清理旧版本文档 (V7.x, V8.0-V8.8)..." -ForegroundColor Yellow
$oldVersionDocs = @(
    "V7.4.2字段引用错误修复.md",
    "V7.4快速验证指南.md",
    "V7.4评分体系删除说明.md",
    "V7.4语法错误修复说明.md",
    "V7.5.1性能优化加强版.md",
    "V7.5.2异步加载BUG修复.md",
    "V7.5性能优化实施说明.md",
    "V7.6性能优化进展.md",
    "V7.6紧急性能优化方案.md",
    "V7.6缓存配置修复说明.md",
    "V8.0快速测试指南.md",
    "V8.0方案D实施完成报告.md",
    "V8.0最终实施报告.md",
    "V8.1完整使用指南.md",
    "V8.1方案A实施完成报告.md",
    "V8.2启动脚本更新说明.md",
    "V8.2完整使用指南.md",
    "V8.2实施完成报告.md",
    "V8.2最终交付说明.md",
    "V8.2最终验证报告.md",
    "V8.3_vs_V8.4_对比分析.md",
    "V8.3完整性能优化方案.md",
    "V8.3实施完成报告.md",
    "V8.4_README.md",
    "V8.4交付总结.md",
    "V8.4交付清单.md",
    "V8.4企业级缓存实施报告.md",
    "V8.4实施清单.md",
    "V8.4实际数据规模评估.md",
    "V8.4快速上手指南.md",
    "V8.4快速启动指南.md",
    "V8.4最终确认.md",
    "V8.4最终验证报告.md",
    "V8.4生产级升级完成报告.md",
    "V8.5企业级优化规划.md",
    "V8.5基础设施优化完成报告.md",
    "V8.5快速启动指南.md",
    "V8.6-V8.7完整优化实施报告.md",
    "V8.6.2商品健康分析性能优化方案.md",
    "V8.6今日必做性能优化完成报告.md",
    "V8.6今日必做性能优化方案.md",
    "V8.8-V8.9_README.md",
    "V8.8-V8.9完整优化实施报告.md",
    "V8.8-V8.9完整优化方案.md",
    "V8.8-V8.9快速启动指南.md",
    "V8.8-V8.9最终验证报告.md"
)

foreach ($file in $oldVersionDocs) {
    if (Backup-And-Remove $file) {
        $deletedCount++
        Write-Host "   ✓ $file" -ForegroundColor DarkGray
    }
}

# 2. 清理测试脚本
Write-Host "`n🧪 清理测试脚本..." -ForegroundColor Yellow
$testScripts = @(
    "测试html_Style修复.py",
    "测试Redis自动启动.py",
    "测试V8.0启动.py",
    "测试V8.1后台任务.py",
    "测试V8.3智能缓存.py",
    "测试V8.4分层缓存.py",
    "测试V8.6今日必做性能优化.py",
    "测试V8.6完整优化.py",
    "测试V8.8-V8.9优化.py",
    "测试今日必做完整流程.py",
    "测试今日必做实际性能.py",
    "测试全部数据模式.py",
    "测试利润率计算.py",
    "测试动态门槛效果.py",
    "测试启动日志输出.py",
    "测试监控面板.py",
    "测试策略引流动态门槛.py",
    "测试PostgreSQL自动启动.ps1",
    "测试启动脚本日志.ps1",
    "验证V7.4评分删除.py",
    "验证V8.4集成.py",
    "验证利润额公式.py",
    "验证基础设施优化.py",
    "验证修复效果.md",
    "验证V7.3优化效果.md"
)

foreach ($file in $testScripts) {
    if (Backup-And-Remove $file) {
        $deletedCount++
        Write-Host "   ✓ $file" -ForegroundColor DarkGray
    }
}

# 3. 清理诊断工具（保留通用诊断框架）
Write-Host "`n🔍 清理诊断工具..." -ForegroundColor Yellow
$diagnosticTools = @(
    "诊断V8.0加载流程.md",
    "诊断今日必做性能.py",
    "诊断内存问题.py",
    "诊断导出数据不匹配.py",
    "诊断局域网访问.bat",
    "诊断工具使用指南.md",
    "诊断工具快速参考.md"
)
# 保留: 通用模块诊断工具.py, 运行诊断工具.ps1/bat (通用诊断框架)
# 可选保留: 诊断局域网访问.ps1 (如需网络诊断)

foreach ($file in $diagnosticTools) {
    if (Backup-And-Remove $file) {
        $deletedCount++
        Write-Host "   ✓ $file" -ForegroundColor DarkGray
    }
}

# 4. 清理A/B电脑脚本（保留实用工具）
Write-Host "`n💻 清理A/B电脑协作脚本..." -ForegroundColor Yellow
$abScripts = @(
    "AB电脑操作快速参考.md",
    "A电脑_创建迁移.ps1",
    "A电脑_提交所有修改.ps1",
    "A电脑_提交迁移.ps1",
    "A电脑操作指南.md"
)
# 保留: A电脑_智能提交.ps1, B电脑_拉取代码.ps1, B电脑_同步数据库.ps1

foreach ($file in $abScripts) {
    if (Backup-And-Remove $file) {
        $deletedCount++
        Write-Host "   ✓ $file" -ForegroundColor DarkGray
    }
}

# 5. 清理临时文件
Write-Host "`n🗑️  清理临时文件..." -ForegroundColor Yellow
$tempFiles = @(
    "debug_output.txt",
    ".env.template"
)

foreach ($file in $tempFiles) {
    if (Backup-And-Remove $file) {
        $deletedCount++
        Write-Host "   ✓ $file" -ForegroundColor DarkGray
    }
}

# 6. 清理冗余安装脚本（可选）
Write-Host "`n📦 清理冗余安装脚本..." -ForegroundColor Yellow
$installScripts = @(
    "安装GLM优化依赖.ps1",
    "安装Memurai_Redis.ps1",
    "安装Redis_WSL.ps1",
    "安装demo依赖.ps1"
)

foreach ($file in $installScripts) {
    if (Backup-And-Remove $file) {
        $deletedCount++
        Write-Host "   ✓ $file" -ForegroundColor DarkGray
    }
}

# 7. 清理冗余Git脚本（可选）
Write-Host "`n🔀 清理冗余Git脚本..." -ForegroundColor Yellow
$gitScripts = @(
    "推送到Github.ps1"
)

foreach ($file in $gitScripts) {
    if (Backup-And-Remove $file) {
        $deletedCount++
        Write-Host "   ✓ $file" -ForegroundColor DarkGray
    }
}

# 清理根目录的临时文件
Write-Host "`n🧹 清理根目录临时文件..." -ForegroundColor Yellow
$rootTempFile = "..\debug_output.txt"
if (Test-Path $rootTempFile) {
    if (Backup-And-Remove $rootTempFile) {
        $deletedCount++
        Write-Host "   ✓ debug_output.txt (根目录)" -ForegroundColor DarkGray
    }
}

# 完成
Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "✅ 清理完成!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 清理统计:" -ForegroundColor Yellow
Write-Host "   已删除文件: $deletedCount 个" -ForegroundColor White
Write-Host "   备份位置: $backupDir" -ForegroundColor White
Write-Host ""
Write-Host "💡 提示:" -ForegroundColor Cyan
Write-Host "   - 如需恢复文件，请从备份目录复制" -ForegroundColor Gray
Write-Host "   - 建议运行 .\启动看板.ps1 测试程序是否正常" -ForegroundColor Gray
Write-Host "   - 确认无误后可删除备份目录" -ForegroundColor Gray
Write-Host ""

# 询问是否测试启动
$testRun = Read-Host "是否立即测试启动看板? (Y/N)"
if ($testRun -eq 'Y' -or $testRun -eq 'y') {
    Write-Host ""
    Write-Host "🚀 启动看板..." -ForegroundColor Cyan
    & ".\启动看板.ps1"
}
