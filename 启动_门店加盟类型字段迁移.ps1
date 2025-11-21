#!/usr/bin/env powershell
# =============================================================================
# 门店加盟类型字段 - 数据库迁移启动脚本
# =============================================================================
# 功能: 一键执行数据库迁移,添加store_franchise_type字段
# 作者: AI助手
# 创建日期: 2025-11-19
# =============================================================================

# 设置错误处理
$ErrorActionPreference = "Stop"

# 显示标题
Write-Host ""
Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host "🏪 门店加盟类型字段 - 数据库迁移工具" -ForegroundColor Cyan
Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host ""

# 显示编码规则
Write-Host "📋 字段规格:" -ForegroundColor Yellow
Write-Host "   字段名: store_franchise_type (SMALLINT)" -ForegroundColor White
Write-Host "   编码规则:" -ForegroundColor White
Write-Host "     1 = 直营店" -ForegroundColor Green
Write-Host "     2 = 加盟店" -ForegroundColor Green
Write-Host "     3 = 托管店" -ForegroundColor Green
Write-Host "     4 = 买断" -ForegroundColor Green
Write-Host "     NULL = 未分类" -ForegroundColor Gray
Write-Host ""

# 显示菜单
Write-Host "请选择操作:" -ForegroundColor Yellow
Write-Host "  [1] 执行Python迁移脚本 (推荐开发环境)" -ForegroundColor White
Write-Host "  [2] 查看生产SQL脚本" -ForegroundColor White
Write-Host "  [3] 测试字段功能" -ForegroundColor White
Write-Host "  [4] 查看使用文档" -ForegroundColor White
Write-Host "  [5] 查看部署清单" -ForegroundColor White
Write-Host "  [Q] 退出" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选项 [1-5/Q]"

switch ($choice.ToUpper()) {
    "1" {
        Write-Host ""
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host "🔧 执行Python迁移脚本" -ForegroundColor Cyan
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host ""
        
        Write-Host "⚠️  即将修改数据库结构,是否继续? (yes/no): " -ForegroundColor Yellow -NoNewline
        $confirm = Read-Host
        
        if ($confirm -eq "yes" -or $confirm -eq "y") {
            Write-Host ""
            Write-Host "🚀 开始执行迁移..." -ForegroundColor Green
            Write-Host ""
            
            python database\add_store_franchise_type_field.py
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "=============================================================================" -ForegroundColor Green
                Write-Host "✅ 迁移执行成功!" -ForegroundColor Green
                Write-Host "=============================================================================" -ForegroundColor Green
                Write-Host ""
                Write-Host "📝 后续操作:" -ForegroundColor Yellow
                Write-Host "   1. 查看使用文档: 门店加盟类型字段使用指南.md" -ForegroundColor White
                Write-Host "   2. 更新Excel数据: 添加'门店加盟类型'列(1-4)" -ForegroundColor White
                Write-Host "   3. 导入新数据: 系统将自动识别并填充字段" -ForegroundColor White
                Write-Host ""
            } else {
                Write-Host ""
                Write-Host "❌ 迁移执行失败,请查看错误信息" -ForegroundColor Red
                Write-Host ""
            }
        } else {
            Write-Host ""
            Write-Host "❌ 操作已取消" -ForegroundColor Yellow
            Write-Host ""
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host "📄 生产SQL脚本" -ForegroundColor Cyan
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host ""
        
        $sqlFile = "database\migrations\pg_ddl_20251119.sql"
        
        if (Test-Path $sqlFile) {
            Write-Host "📁 脚本位置: $sqlFile" -ForegroundColor Green
            Write-Host ""
            Write-Host "📋 脚本内容预览:" -ForegroundColor Yellow
            Write-Host ""
            Get-Content $sqlFile -TotalCount 30
            Write-Host ""
            Write-Host "... (更多内容请查看完整文件)" -ForegroundColor Gray
            Write-Host ""
            Write-Host "💡 使用方式:" -ForegroundColor Yellow
            Write-Host "   psql -h [数据库地址] -U [用户名] -d o2o_dashboard -f $sqlFile" -ForegroundColor White
            Write-Host ""
        } else {
            Write-Host "❌ SQL脚本未找到: $sqlFile" -ForegroundColor Red
            Write-Host "💡 提示: 先运行选项1执行Python脚本,会自动生成SQL脚本" -ForegroundColor Yellow
            Write-Host ""
        }
    }
    
    "3" {
        Write-Host ""
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host "🧪 测试字段功能" -ForegroundColor Cyan
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host ""
        
        $testFile = "测试门店加盟类型字段.py"
        
        if (Test-Path $testFile) {
            Write-Host "🚀 开始执行测试..." -ForegroundColor Green
            Write-Host ""
            
            python $testFile
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "✅ 测试完成" -ForegroundColor Green
                Write-Host ""
            } else {
                Write-Host ""
                Write-Host "⚠️  测试未完全通过,请查看错误信息" -ForegroundColor Yellow
                Write-Host ""
            }
        } else {
            Write-Host "❌ 测试脚本未找到: $testFile" -ForegroundColor Red
            Write-Host ""
        }
    }
    
    "4" {
        Write-Host ""
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host "📚 使用文档" -ForegroundColor Cyan
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host ""
        
        $docFile = "门店加盟类型字段使用指南.md"
        
        if (Test-Path $docFile) {
            Write-Host "📁 文档位置: $docFile" -ForegroundColor Green
            Write-Host ""
            Write-Host "🔍 使用默认编辑器打开文档..." -ForegroundColor Yellow
            Start-Process $docFile
            Write-Host ""
        } else {
            Write-Host "❌ 文档未找到: $docFile" -ForegroundColor Red
            Write-Host ""
        }
    }
    
    "5" {
        Write-Host ""
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host "📋 部署清单" -ForegroundColor Cyan
        Write-Host "=============================================================================" -ForegroundColor Cyan
        Write-Host ""
        
        $checklistFile = "门店加盟类型字段部署清单.md"
        
        if (Test-Path $checklistFile) {
            Write-Host "📁 清单位置: $checklistFile" -ForegroundColor Green
            Write-Host ""
            Write-Host "🔍 使用默认编辑器打开清单..." -ForegroundColor Yellow
            Start-Process $checklistFile
            Write-Host ""
        } else {
            Write-Host "❌ 清单未找到: $checklistFile" -ForegroundColor Red
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
        Write-Host "❌ 无效选项,请重新运行脚本" -ForegroundColor Red
        Write-Host ""
        exit 1
    }
}

# 暂停等待用户确认
Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
