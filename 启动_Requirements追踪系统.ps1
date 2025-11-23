# =============================================================================
# Requirements变更追踪系统 - 启动脚本
# =============================================================================
# 功能: 一键管理requirements.txt变更追踪
# 作者: AI助手
# 创建日期: 2025-11-19
# =============================================================================

# 设置错误处理
$ErrorActionPreference = "Stop"

# 切换到脚本所在目录
Set-Location $PSScriptRoot

# 显示标题
Write-Host ""
Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host "📦 Requirements变更追踪系统" -ForegroundColor Cyan
Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否存在快照
$snapshotDir = ".requirements_snapshots"
$hasSnapshot = $false

if (Test-Path $snapshotDir) {
    $snapshotFiles = Get-ChildItem $snapshotDir -Filter "requirements_*.json" -ErrorAction SilentlyContinue
    if ($snapshotFiles.Count -gt 0) {
        $hasSnapshot = $true
        $latestSnapshot = $snapshotFiles | Sort-Object Name -Descending | Select-Object -First 1
        Write-Host "📊 系统状态:" -ForegroundColor Yellow
        Write-Host "   ✅ 已初始化" -ForegroundColor Green
        Write-Host "   📁 快照数量: $($snapshotFiles.Count)" -ForegroundColor White
        Write-Host "   📅 最新快照: $($latestSnapshot.Name)" -ForegroundColor White
        Write-Host ""
    }
}

if (-not $hasSnapshot) {
    Write-Host "📊 系统状态:" -ForegroundColor Yellow
    Write-Host "   ⚠️  未初始化 (需要创建首次快照)" -ForegroundColor Yellow
    Write-Host ""
}

# 显示菜单
Write-Host "请选择操作:" -ForegroundColor Yellow
Write-Host "  [1] 追踪requirements.txt变更 (主要功能)" -ForegroundColor White
Write-Host "  [2] 显示当前所有依赖包" -ForegroundColor White
Write-Host "  [3] 清理旧快照" -ForegroundColor White
Write-Host "  [4] 运行演示脚本" -ForegroundColor White
Write-Host "  [5] 运行完整测试" -ForegroundColor White
Write-Host "  [6] 查看使用文档" -ForegroundColor White
Write-Host "  [7] 查看变更日志" -ForegroundColor White
Write-Host "  [Q] 退出" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选项 [1-7/Q]"

switch ($choice.ToUpper()) {
    "1" {
        Write-Host ""
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host "🔍 追踪requirements.txt变更" -ForegroundColor Cyan
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host ""
        
        # 询问变更原因
        Write-Host "💡 请输入变更原因 (可选,按Enter跳过): " -ForegroundColor Yellow -NoNewline
        $reason = Read-Host
        
        Write-Host ""
        Write-Host "🚀 开始追踪..." -ForegroundColor Green
        Write-Host ""
        
        if ($reason) {
            python tools\track_requirements_changes.py -r $reason
        } else {
            python tools\track_requirements_changes.py
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "=============================================================================" -ForegroundColor Green
            Write-Host "✅ 追踪完成!" -ForegroundColor Green
            Write-Host "=============================================================================" -ForegroundColor Green
            Write-Host ""
            
            # 检查是否生成了变更日志
            if (Test-Path "requirements_changelog.md") {
                Write-Host "📄 变更日志已更新: requirements_changelog.md" -ForegroundColor Green
                Write-Host ""
                Write-Host "💡 是否查看变更日志? (y/n): " -ForegroundColor Yellow -NoNewline
                $viewLog = Read-Host
                
                if ($viewLog -eq "y" -or $viewLog -eq "yes") {
                    Write-Host ""
                    Write-Host "📋 最新变更 (前30行):" -ForegroundColor Yellow
                    Write-Host ""
                    Get-Content "requirements_changelog.md" -TotalCount 30 -Encoding UTF8
                    Write-Host ""
                    Write-Host "... (完整内容请查看文件)" -ForegroundColor Gray
                    Write-Host ""
                }
            }
        } else {
            Write-Host ""
            Write-Host "❌ 追踪失败,请查看错误信息" -ForegroundColor Red
            Write-Host ""
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host "📦 显示当前所有依赖包" -ForegroundColor Cyan
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host ""
        
        python tools\track_requirements_changes.py --show
        
        Write-Host ""
    }
    
    "3" {
        Write-Host ""
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host "🗑️  清理旧快照" -ForegroundColor Cyan
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host ""
        
        if (Test-Path $snapshotDir) {
            $snapshotFiles = Get-ChildItem $snapshotDir -Filter "requirements_*.json" -ErrorAction SilentlyContinue
            Write-Host "📊 当前快照数量: $($snapshotFiles.Count)" -ForegroundColor Yellow
            Write-Host ""
        }
        
        Write-Host "💡 保留最新多少个快照? (默认10,按Enter使用默认值): " -ForegroundColor Yellow -NoNewline
        $keepCount = Read-Host
        
        if (-not $keepCount) {
            $keepCount = 10
        }
        
        Write-Host ""
        Write-Host "🚀 开始清理..." -ForegroundColor Green
        Write-Host ""
        
        python tools\track_requirements_changes.py --cleanup --keep $keepCount
        
        Write-Host ""
    }
    
    "4" {
        Write-Host ""
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host "🎬 运行演示脚本" -ForegroundColor Cyan
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host ""
        
        $demoFile = "演示requirements追踪.py"
        
        if (Test-Path $demoFile) {
            Write-Host "🚀 开始演示..." -ForegroundColor Green
            Write-Host ""
            
            python $demoFile
            
            Write-Host ""
        } else {
            Write-Host "❌ 演示脚本未找到: $demoFile" -ForegroundColor Red
            Write-Host ""
        }
    }
    
    "5" {
        Write-Host ""
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host "🧪 运行完整测试" -ForegroundColor Cyan
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host ""
        
        $testFile = "测试requirements追踪.py"
        
        if (Test-Path $testFile) {
            Write-Host "⚠️  测试将临时修改requirements.txt,完成后会自动恢复" -ForegroundColor Yellow
            Write-Host "💡 是否继续? (y/n): " -ForegroundColor Yellow -NoNewline
            $confirm = Read-Host
            
            if ($confirm -eq "y" -or $confirm -eq "yes") {
                Write-Host ""
                Write-Host "🚀 开始测试..." -ForegroundColor Green
                Write-Host ""
                
                python $testFile
                
                Write-Host ""
            } else {
                Write-Host ""
                Write-Host "❌ 测试已取消" -ForegroundColor Yellow
                Write-Host ""
            }
        } else {
            Write-Host "❌ 测试脚本未找到: $testFile" -ForegroundColor Red
            Write-Host ""
        }
    }
    
    "6" {
        Write-Host ""
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host "📚 使用文档" -ForegroundColor Cyan
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host ""
        
        Write-Host "📄 可用文档:" -ForegroundColor Yellow
        Write-Host "  [1] requirements变更追踪使用指南.md (完整文档)" -ForegroundColor White
        Write-Host "  [2] requirements追踪-快速开始.md (快速指南)" -ForegroundColor White
        Write-Host "  [3] requirements追踪系统测试报告.md (测试报告)" -ForegroundColor White
        Write-Host ""
        
        Write-Host "请选择要查看的文档 [1-3]: " -ForegroundColor Yellow -NoNewline
        $docChoice = Read-Host
        
        $docFiles = @(
            "requirements变更追踪使用指南.md",
            "requirements追踪-快速开始.md",
            "requirements追踪系统测试报告.md"
        )
        
        $docIndex = [int]$docChoice - 1
        
        if ($docIndex -ge 0 -and $docIndex -lt $docFiles.Count) {
            $docFile = $docFiles[$docIndex]
            
            if (Test-Path $docFile) {
                Write-Host ""
                Write-Host "🔍 使用默认编辑器打开文档..." -ForegroundColor Green
                Start-Process $docFile
                Write-Host ""
            } else {
                Write-Host ""
                Write-Host "❌ 文档未找到: $docFile" -ForegroundColor Red
                Write-Host ""
            }
        } else {
            Write-Host ""
            Write-Host "❌ 无效选项" -ForegroundColor Red
            Write-Host ""
        }
    }
    
    "7" {
        Write-Host ""
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host "📋 查看变更日志" -ForegroundColor Cyan
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host ""
        
        $changelogFile = "requirements_changelog.md"
        
        if (Test-Path $changelogFile) {
            Write-Host "📁 日志位置: $changelogFile" -ForegroundColor Green
            Write-Host ""
            Write-Host "📋 最新内容 (前50行):" -ForegroundColor Yellow
            Write-Host ""
            Get-Content $changelogFile -TotalCount 50 -Encoding UTF8
            Write-Host ""
            Write-Host "... (更多内容请查看完整文件)" -ForegroundColor Gray
            Write-Host ""
            Write-Host "💡 是否用编辑器打开完整文件? (y/n): " -ForegroundColor Yellow -NoNewline
            $openFile = Read-Host
            
            if ($openFile -eq "y" -or $openFile -eq "yes") {
                Start-Process $changelogFile
            }
            Write-Host ""
        } else {
            Write-Host "ℹ️  变更日志尚未生成" -ForegroundColor Yellow
            Write-Host "Tip: Run option 1 after modifying requirements.txt to generate changelog" -ForegroundColor White
            Write-Host ""
        }
    }
    
    "Q" {
        Write-Host ""
        Write-Host "👋 再见!" -ForegroundColor Cyan
        Write-Host ""
        exit 0
    }
    
    default {
        Write-Host ""
        Write-Host "Invalid option, please run the script again" -ForegroundColor Red
        Write-Host ""
        exit 1
    }
}

# 暂停等待用户确认
Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
