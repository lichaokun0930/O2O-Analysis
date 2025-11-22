#!/usr/bin/env powershell
# =============================================================================
# 启动脚本测试工具
# =============================================================================
# 功能: 验证所有启动脚本的语法和结构
# =============================================================================

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                        启动脚本测试工具                                    ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 定义要测试的脚本
$scriptsToTest = @(
    "主菜单.ps1",
    "启动_门店加盟类型字段迁移.ps1",
    "启动_Requirements追踪系统.ps1"
)

$passCount = 0
$failCount = 0

foreach ($script in $scriptsToTest) {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host "测试脚本: $script" -ForegroundColor Yellow
    Write-Host ""
    
    # 检查文件是否存在
    if (-not (Test-Path $script)) {
        Write-Host "  ❌ 文件不存在" -ForegroundColor Red
        Write-Host ""
        $failCount++
        continue
    }
    
    Write-Host "  ✅ 文件存在" -ForegroundColor Green
    
    # 获取文件信息
    $fileInfo = Get-Item $script
    Write-Host "  📄 文件大小: $($fileInfo.Length) 字节" -ForegroundColor Gray
    Write-Host "  📅 最后修改: $($fileInfo.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
    
    # 读取文件内容
    try {
        $content = Get-Content $script -Raw -ErrorAction Stop
        Write-Host "  ✅ 文件可读取" -ForegroundColor Green
        
        # 检查PowerShell语法
        $errors = $null
        $null = [System.Management.Automation.PSParser]::Tokenize($content, [ref]$errors)
        
        if ($errors -and $errors.Count -gt 0) {
            Write-Host "  ❌ PowerShell语法错误:" -ForegroundColor Red
            foreach ($error in $errors) {
                Write-Host "     行 $($error.Token.StartLine): $($error.Message)" -ForegroundColor Red
            }
            $failCount++
        } else {
            Write-Host "  ✅ PowerShell语法正确" -ForegroundColor Green
            
            # 检查关键结构
            $checks = @{
                "错误处理" = '$ErrorActionPreference'
                "函数定义" = 'function '
                "用户输入" = 'Read-Host'
                "条件判断" = 'if \('
                "循环结构" = '(do|while|foreach)'
            }
            
            $structureOK = $true
            foreach ($check in $checks.GetEnumerator()) {
                if ($content -match $check.Value) {
                    Write-Host "  ✅ 包含$($check.Key)" -ForegroundColor Green
                } else {
                    Write-Host "  ⚠️  未找到$($check.Key)" -ForegroundColor Yellow
                }
            }
            
            # 特定脚本的特殊检查
            switch -Wildcard ($script) {
                "主菜单.ps1" {
                    if ($content -match 'Show-MainMenu') {
                        Write-Host "  ✅ 包含菜单显示函数" -ForegroundColor Green
                    }
                    if ($content -match 'Start-FranchiseTypeMigration') {
                        Write-Host "  ✅ 包含字段迁移调用" -ForegroundColor Green
                    }
                    if ($content -match 'Start-RequirementsTracker') {
                        Write-Host "  ✅ 包含追踪系统调用" -ForegroundColor Green
                    }
                }
                "*门店加盟类型*" {
                    if ($content -match 'store_franchise_type') {
                        Write-Host "  ✅ 包含字段名称" -ForegroundColor Green
                    }
                    if ($content -match '直营店.*加盟店.*托管店.*买断') {
                        Write-Host "  ✅ 包含编码规则说明" -ForegroundColor Green
                    }
                }
                "*Requirements*" {
                    if ($content -match 'track_requirements_changes.py') {
                        Write-Host "  ✅ 包含追踪脚本调用" -ForegroundColor Green
                    }
                    if ($content -match '.requirements_snapshots') {
                        Write-Host "  ✅ 包含快照目录检查" -ForegroundColor Green
                    }
                }
            }
            
            $passCount++
        }
        
    } catch {
        Write-Host "  ❌ 读取文件失败: $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
    
    Write-Host ""
}

# 显示测试总结
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""
Write-Host "📊 测试总结" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  总计测试: $($scriptsToTest.Count) 个脚本" -ForegroundColor White
Write-Host "  ✅ 通过: $passCount" -ForegroundColor Green
Write-Host "  ❌ 失败: $failCount" -ForegroundColor Red
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "🎉 所有启动脚本测试通过!" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 建议:" -ForegroundColor Yellow
    Write-Host "   1. 运行 .\主菜单.ps1 启动主菜单" -ForegroundColor White
    Write-Host "   2. 运行 .\启动_门店加盟类型字段迁移.ps1 测试数据库迁移" -ForegroundColor White
    Write-Host "   3. 运行 .\启动_Requirements追踪系统.ps1 测试追踪系统" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "⚠️  部分脚本存在问题,请检查上述错误信息" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
Write-Host ""
