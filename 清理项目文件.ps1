# 安全清理项目冗余文件

Write-Host "=" * 70
Write-Host "项目文件清理工具"
Write-Host "=" * 70

Write-Host "`n正在分析可删除的文件..." -ForegroundColor Cyan

# 定义要删除的文件和文件夹
$itemsToDelete = @(
    # 备份文件夹
    "删除文件备份_20251122_215702",
    "宸插垹闄ゆ枃浠跺浠絖20251118_145452",
    
    # 测试脚本
    "测试Redis连接.py",
    "测试Redis性能.py",
    "测试导入脚本修复.py",
    
    # 过时文档
    "导入脚本修复说明.md",
    "导入脚本库存字段修复说明.md",
    "字段兼容性修复完成报告.md",
    "models字段同步修复说明.md",
    
    # 临时脚本
    "示例_WebWorker后台计算.py",
    "price_comparison_dashboard.py",
    "同步数据库结构.py",
    
    # 旧版Git脚本
    "git_pull.ps1",
    "git_push.ps1",
    "git_sync.ps1",
    "推送到Github.ps1",
    
    # 多余启动脚本
    "清理临时文件-综合版_backup.ps1",
    "重启看板.ps1",
    
    # 旧版安装脚本
    "安装demo依赖.ps1",
    "安装GLM优化依赖.ps1",
    "安装Redis_WSL.ps1",
    
    # 过时配置
    "requirements_utf8.txt"
)

# 可选删除项(仅未被引用的AI高级模块)

$optionalItems = @(
    "ai_pandasai_integration.py",      # PandasAI对话(try-import,可选)
    "增量学习优化器.py",               # 未被引用 - 自动优化
    "自适应学习引擎.py"                # 未被引用 - 自适应学习
)

# 统计
$totalSize = 0
$existingItems = @()

foreach ($item in $itemsToDelete) {
    if (Test-Path $item) {
        $size = (Get-ChildItem $item -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        $totalSize += $size
        $existingItems += $item
        
        $sizeKB = [math]::Round($size / 1KB, 2)
        Write-Host "  [✓] $item ($sizeKB KB)" -ForegroundColor Yellow
    }
}

$totalMB = [math]::Round($totalSize / 1MB, 2)

Write-Host "`n找到 $($existingItems.Count) 个可删除项,共 $totalMB MB" -ForegroundColor Cyan

# 显示可选删除项
Write-Host "`n可选删除(AI高级功能):" -ForegroundColor Magenta
foreach ($item in $optionalItems) {
    if (Test-Path $item) {
        Write-Host "  [?] $item" -ForegroundColor Gray
    }
}

Write-Host "`n" + "=" * 70
$confirm = Read-Host "确认删除以上文件? (y/n)"

if ($confirm -ne 'y') {
    Write-Host "`n已取消" -ForegroundColor Yellow
    exit 0
}

# 询问是否删除可选项
Write-Host ""
$deleteOptional = Read-Host "是否同时删除AI高级功能模块? (y/n,默认n)"

# 执行删除
Write-Host "`n开始清理..." -ForegroundColor Cyan
$deletedCount = 0

foreach ($item in $existingItems) {
    try {
        Remove-Item $item -Recurse -Force -ErrorAction Stop
        Write-Host "  [✓] 已删除: $item" -ForegroundColor Green
        $deletedCount++
    } catch {
        Write-Host "  [✗] 删除失败: $item - $_" -ForegroundColor Red
    }
}

if ($deleteOptional -eq 'y') {
    foreach ($item in $optionalItems) {
        if (Test-Path $item) {
            try {
                Remove-Item $item -Force -ErrorAction Stop
                Write-Host "  [✓] 已删除: $item" -ForegroundColor Green
                $deletedCount++
            } catch {
                Write-Host "  [✗] 删除失败: $item - $_" -ForegroundColor Red
            }
        }
    }
}

Write-Host "`n" + "=" * 70
Write-Host "清理完成!" -ForegroundColor Green
Write-Host "=" * 70

Write-Host "`n已删除 $deletedCount 个项目,释放约 $totalMB MB 空间" -ForegroundColor Cyan

Write-Host "`n查看详细清理方案: 项目清理方案.md" -ForegroundColor Yellow
Write-Host ""
