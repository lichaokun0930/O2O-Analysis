#!/usr/bin/env powershell
# =============================================================================
# O2O智能看板系统 - 主启动菜单
# =============================================================================
# 功能: 统一入口,快速访问所有工具和功能
# 作者: AI助手
# 创建日期: 2025-11-19
# =============================================================================

# 设置错误处理
$ErrorActionPreference = "Stop"

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 显示标题
Clear-Host
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    O2O智能看板系统 - 主启动菜单                          ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 显示系统信息
Write-Host "📍 当前目录: $(Get-Location)" -ForegroundColor Gray
Write-Host "📅 系统日期: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# 主菜单
function Show-MainMenu {
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    Write-Host "                              🎯 核心功能                                   " -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  [1] 🚀 启动智能看板 (Dash版)" -ForegroundColor White
    Write-Host "  [2] 🗄️  启动数据库服务" -ForegroundColor White
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    Write-Host "                           📦 新功能 (2025-11-19)                          " -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  [3] 🏪 门店加盟类型字段迁移" -ForegroundColor Green
    Write-Host "      └─ 数据库添加store_franchise_type字段 (1=直营,2=加盟,3=托管,4=买断)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  [4] 📊 Requirements变更追踪系统" -ForegroundColor Green
    Write-Host "      └─ 自动追踪requirements.txt变更,生成变更日志" -ForegroundColor Gray
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    Write-Host "                              🛠️  工具集                                    " -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  [5] 📥 智能导入门店数据" -ForegroundColor White
    Write-Host "  [6] 🔧 检查数据库状态" -ForegroundColor White
    Write-Host "  [7] 🧹 清理缓存" -ForegroundColor White
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    Write-Host "                              📚 文档中心                                   " -ForegroundColor Yellow
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  [8] 📖 查看使用指南" -ForegroundColor White
    Write-Host "  [9] 📋 查看部署清单" -ForegroundColor White
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  [Q] 🚪 退出" -ForegroundColor White
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════════" -ForegroundColor DarkGray
    Write-Host ""
}

# 启动智能看板
function Start-Dashboard {
    Write-Host ""
    Write-Host "🚀 启动智能看板..." -ForegroundColor Green
    Write-Host ""
    
    if (Test-Path "启动看板.ps1") {
        & .\启动看板.ps1
    } elseif (Test-Path "智能门店看板_Dash版.py") {
        python 智能门店看板_Dash版.py
    } else {
        Write-Host "❌ 找不到看板启动文件" -ForegroundColor Red
        Write-Host ""
    }
}

# 启动数据库
function Start-Database {
    Write-Host ""
    Write-Host "🗄️  启动数据库服务..." -ForegroundColor Green
    Write-Host ""
    
    if (Test-Path "启动数据库.ps1") {
        & .\启动数据库.ps1
    } elseif (Test-Path "start_database.ps1") {
        & .\start_database.ps1
    } else {
        Write-Host "❌ 找不到数据库启动文件" -ForegroundColor Red
        Write-Host ""
    }
}

# 门店加盟类型字段迁移
function Start-FranchiseTypeMigration {
    Write-Host ""
    Write-Host "🏪 启动门店加盟类型字段迁移工具..." -ForegroundColor Green
    Write-Host ""
    
    if (Test-Path "启动_门店加盟类型字段迁移.ps1") {
        & .\启动_门店加盟类型字段迁移.ps1
    } else {
        Write-Host "❌ 找不到迁移启动文件" -ForegroundColor Red
        Write-Host ""
    }
}

# Requirements追踪系统
function Start-RequirementsTracker {
    Write-Host ""
    Write-Host "📊 启动Requirements变更追踪系统..." -ForegroundColor Green
    Write-Host ""
    
    if (Test-Path "启动_Requirements追踪系统.ps1") {
        & .\启动_Requirements追踪系统.ps1
    } else {
        Write-Host "❌ 找不到追踪系统启动文件" -ForegroundColor Red
        Write-Host ""
    }
}

# 智能导入数据
function Import-StoreData {
    Write-Host ""
    Write-Host "📥 启动智能导入工具..." -ForegroundColor Green
    Write-Host ""
    
    if (Test-Path "智能导入门店数据.py") {
        python 智能导入门店数据.py
    } else {
        Write-Host "❌ 找不到导入工具" -ForegroundColor Red
        Write-Host ""
    }
}

# 检查数据库状态
function Check-DatabaseStatus {
    Write-Host ""
    Write-Host "🔧 检查数据库状态..." -ForegroundColor Green
    Write-Host ""
    
    if (Test-Path "检查数据库状态.py") {
        python 检查数据库状态.py
    } else {
        Write-Host "❌ 找不到检查脚本" -ForegroundColor Red
        Write-Host ""
    }
}

# 清理缓存
function Clear-Cache {
    Write-Host ""
    Write-Host "🧹 清理缓存..." -ForegroundColor Green
    Write-Host ""
    
    if (Test-Path "清理缓存.py") {
        python 清理缓存.py
    } elseif (Test-Path "清除缓存.bat") {
        & .\清除缓存.bat
    } else {
        Write-Host "❌ 找不到清理脚本" -ForegroundColor Red
        Write-Host ""
    }
}

# 查看文档
function Show-Documentation {
    Write-Host ""
    Write-Host "📖 可用文档列表:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  [1] README_Dash版使用指南.md" -ForegroundColor White
    Write-Host "  [2] 快速启动指南.md" -ForegroundColor White
    Write-Host "  [3] 门店加盟类型字段使用指南.md" -ForegroundColor White
    Write-Host "  [4] requirements变更追踪使用指南.md" -ForegroundColor White
    Write-Host "  [5] 业务逻辑与数据字典完整手册.md" -ForegroundColor White
    Write-Host ""
    Write-Host "请选择要查看的文档 [1-5]: " -ForegroundColor Yellow -NoNewline
    $docChoice = Read-Host
    
    $docs = @(
        "README_Dash版使用指南.md",
        "快速启动指南.md",
        "门店加盟类型字段使用指南.md",
        "requirements变更追踪使用指南.md",
        "【权威】业务逻辑与数据字典完整手册.md"
    )
    
    $docIndex = [int]$docChoice - 1
    
    if ($docIndex -ge 0 -and $docIndex -lt $docs.Count) {
        $docFile = $docs[$docIndex]
        if (Test-Path $docFile) {
            Write-Host ""
            Write-Host "🔍 打开文档: $docFile" -ForegroundColor Green
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

# 查看部署清单
function Show-DeploymentChecklist {
    Write-Host ""
    Write-Host "📋 可用清单列表:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  [1] 部署清单.md" -ForegroundColor White
    Write-Host "  [2] 门店加盟类型字段部署清单.md" -ForegroundColor White
    Write-Host "  [3] 交付清单.md" -ForegroundColor White
    Write-Host ""
    Write-Host "请选择要查看的清单 [1-3]: " -ForegroundColor Yellow -NoNewline
    $checklistChoice = Read-Host
    
    $checklists = @(
        "部署清单.md",
        "门店加盟类型字段部署清单.md",
        "交付清单.md"
    )
    
    $checklistIndex = [int]$checklistChoice - 1
    
    if ($checklistIndex -ge 0 -and $checklistIndex -lt $checklists.Count) {
        $checklistFile = $checklists[$checklistIndex]
        if (Test-Path $checklistFile) {
            Write-Host ""
            Write-Host "🔍 打开清单: $checklistFile" -ForegroundColor Green
            Start-Process $checklistFile
            Write-Host ""
        } else {
            Write-Host ""
            Write-Host "❌ 清单未找到: $checklistFile" -ForegroundColor Red
            Write-Host ""
        }
    } else {
        Write-Host ""
        Write-Host "❌ 无效选项" -ForegroundColor Red
        Write-Host ""
    }
}

# 主循环
do {
    Show-MainMenu
    
    Write-Host "请输入选项 [1-9/Q]: " -ForegroundColor Cyan -NoNewline
    $choice = Read-Host
    
    switch ($choice.ToUpper()) {
        "1" { Start-Dashboard }
        "2" { Start-Database }
        "3" { Start-FranchiseTypeMigration }
        "4" { Start-RequirementsTracker }
        "5" { Import-StoreData }
        "6" { Check-DatabaseStatus }
        "7" { Clear-Cache }
        "8" { Show-Documentation }
        "9" { Show-DeploymentChecklist }
        "Q" { 
            Write-Host ""
            Write-Host "👋 感谢使用O2O智能看板系统!" -ForegroundColor Cyan
            Write-Host ""
            exit 0
        }
        default { 
            Write-Host ""
            Write-Host "❌ 无效选项,请重新选择" -ForegroundColor Red
            Write-Host ""
            Start-Sleep -Seconds 2
            Clear-Host
        }
    }
    
    if ($choice.ToUpper() -ne "Q") {
        Write-Host ""
        Write-Host "按任意键返回主菜单..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        Clear-Host
    }
    
} while ($true)
