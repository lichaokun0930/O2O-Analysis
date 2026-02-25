# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    一键批量导入数据工具 v2.0

.DESCRIPTION
    交互式数据导入工具，支持：
    1. 增量导入 - 只导入新数据
    2. 全量重新导入 - 清空后重新导入（解决数据丢失问题）
    3. 仅清理数据 - 清空所有数据和历史记录

.EXAMPLE
    .\一键批量导入数据.ps1
#>

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'

# 颜色输出函数
function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

# 显示横幅
function Show-Banner {
    Clear-Host
    Write-ColorOutput "`n========================================" "Cyan"
    Write-ColorOutput "   📦 一键批量导入数据工具 v2.0" "Cyan"
    Write-ColorOutput "========================================`n" "Cyan"
}

# 显示菜单
function Show-Menu {
    Write-ColorOutput "请选择操作模式：`n" "White"
    Write-ColorOutput "  [1] 增量导入" "Green"
    Write-ColorOutput "      只导入新数据，跳过已导入的文件`n" "Gray"
    Write-ColorOutput "  [2] 全量重新导入 (推荐)" "Yellow"
    Write-ColorOutput "      清空所有数据后重新导入，解决数据丢失/金额不对问题`n" "Gray"
    Write-ColorOutput "  [3] 仅清理数据" "Red"
    Write-ColorOutput "      清空所有订单数据、导入历史、预聚合表`n" "Gray"
    Write-ColorOutput "  [4] 查看当前数据状态" "Cyan"
    Write-ColorOutput "      显示数据库中的数据统计`n" "Gray"
    Write-ColorOutput "  [0] 退出`n" "White"
}

# 切换到脚本目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 激活虚拟环境
function Activate-Venv {
    if (Test-Path ".\.venv\Scripts\Activate.ps1") {
        . .\.venv\Scripts\Activate.ps1
        return $true
    }
    Write-ColorOutput "⚠️ 未找到虚拟环境，使用系统 Python" "Yellow"
    return $false
}

# 查找 Excel 文件
function Get-ExcelFiles {
    param([string]$Path = ".\实际数据")
    
    if (-not (Test-Path $Path)) {
        return @()
    }
    
    return Get-ChildItem -Path $Path -Include "*.xlsx", "*.xls" -Recurse | 
        Where-Object { -not $_.Name.StartsWith("~$") }
}

# 显示文件列表
function Show-FileList {
    param([string]$Path = ".\实际数据")
    
    $files = Get-ExcelFiles -Path $Path
    
    if ($files.Count -eq 0) {
        Write-ColorOutput "❌ 未找到 Excel 文件: $Path" "Red"
        return $false
    }
    
    Write-ColorOutput "`n📂 数据目录: $Path" "White"
    Write-ColorOutput "📊 发现 $($files.Count) 个 Excel 文件:`n" "Green"
    
    $index = 1
    foreach ($file in $files) {
        $size = [math]::Round($file.Length / 1MB, 2)
        Write-ColorOutput "   $index. $($file.Name) ($size MB)" "White"
        $index++
    }
    Write-ColorOutput "" "White"
    return $true
}

# 查看数据状态
function Show-DataStatus {
    Write-ColorOutput "`n� 正在查询数据库状态..." "Cyan"
    
    $pythonCode = @"
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from database.connection import SessionLocal, init_database
from database.models import Order, DataUploadHistory
from sqlalchemy import func, text

init_database()
session = SessionLocal()

try:
    # 订单统计
    order_count = session.query(func.count(Order.id)).scalar() or 0
    unique_orders = session.query(func.count(func.distinct(Order.order_id))).scalar() or 0
    store_count = session.query(func.count(func.distinct(Order.store_name))).scalar() or 0
    history_count = session.query(func.count(DataUploadHistory.id)).scalar() or 0
    
    print(f'\n订单行数: {order_count:,}')
    print(f'唯一订单: {unique_orders:,}')
    print(f'门店数量: {store_count}')
    print(f'导入历史: {history_count} 条')
    
    if order_count > 0:
        # 金额统计
        result = session.execute(text('''
            SELECT 
                SUM(actual_price * quantity) as revenue,
                SUM(profit - platform_service_fee - delivery_fee + corporate_rebate) as profit
            FROM orders
        '''))
        row = result.fetchone()
        print(f'\n商品实收额: ¥{row[0]:,.2f}' if row[0] else '\n商品实收额: ¥0')
        print(f'总利润: ¥{row[1]:,.2f}' if row[1] else '总利润: ¥0')
        
        # 预聚合表
        print('\n预聚合表:')
        tables = ['store_daily_summary', 'store_hourly_summary', 'category_daily_summary', 'delivery_summary', 'product_daily_summary']
        for t in tables:
            try:
                r = session.execute(text(f'SELECT COUNT(*) FROM {t}'))
                c = r.scalar() or 0
                print(f'  {t}: {c:,} 条')
            except:
                print(f'  {t}: 表不存在')
finally:
    session.close()
"@
    
    python -c $pythonCode
    Write-ColorOutput "" "White"
}

# 清理所有数据
function Clear-AllData {
    Write-ColorOutput "`n🗑️ 正在清理所有数据..." "Yellow"
    
    $pythonCode = @"
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from database.connection import SessionLocal, init_database
from database.models import Order, DataUploadHistory
from sqlalchemy import text

init_database()
session = SessionLocal()

tables = ['store_daily_summary', 'store_hourly_summary', 'category_daily_summary', 'delivery_summary', 'product_daily_summary']

try:
    # 清理预聚合表
    for t in tables:
        try:
            r = session.execute(text(f'DELETE FROM {t}'))
            if r.rowcount > 0:
                print(f'  {t}: 删除 {r.rowcount:,} 条')
        except Exception as e:
            pass
    
    # 清理订单
    deleted = session.query(Order).delete()
    print(f'  orders: 删除 {deleted:,} 条')
    
    # 清理历史
    deleted = session.query(DataUploadHistory).delete()
    print(f'  data_upload_history: 删除 {deleted} 条')
    
    session.commit()
    print('\n✅ 所有数据已清理')
except Exception as e:
    print(f'❌ 清理失败: {e}')
    session.rollback()
finally:
    session.close()
"@
    
    python -c $pythonCode
}

# 执行导入
function Start-Import {
    param([string]$Mode = "incremental")
    
    Write-ColorOutput "`n🚀 开始导入数据...`n" "Cyan"
    
    python -c @"
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from database.batch_import_enhanced import BatchDataImporterEnhanced

importer = BatchDataImporterEnhanced(data_dir='./实际数据', mode='$Mode')
importer.run()
"@
}

# 显示导入结果
function Show-ImportResult {
    Write-ColorOutput "`n📊 导入后数据验证:" "Cyan"
    
    $pythonCode = @"
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '.')
from database.connection import SessionLocal, init_database
from database.models import Order
from sqlalchemy import func, text

init_database()
session = SessionLocal()

try:
    order_count = session.query(func.count(Order.id)).scalar() or 0
    unique_orders = session.query(func.count(func.distinct(Order.order_id))).scalar() or 0
    
    # 正确的利润计算：先按订单聚合，再计算利润
    # 利润公式：利润额 - 平台服务费 - 物流配送费 + 企客后返（每个订单只扣一次）
    result = session.execute(text('''
        WITH order_level AS (
            SELECT 
                order_id,
                SUM(COALESCE(actual_price, 0) * COALESCE(quantity, 1)) as order_revenue,
                SUM(COALESCE(profit, 0)) as order_profit,
                MAX(COALESCE(platform_service_fee, 0)) as order_platform_fee,
                MAX(COALESCE(delivery_fee, 0)) as order_delivery_fee,
                MAX(COALESCE(corporate_rebate, 0)) as order_corporate_rebate
            FROM orders
            GROUP BY order_id
        )
        SELECT 
            SUM(order_revenue) as total_revenue,
            SUM(order_profit - order_platform_fee - order_delivery_fee + order_corporate_rebate) as total_profit
        FROM order_level
    '''))
    row = result.fetchone()
    
    print(f'\n  订单行数: {order_count:,}')
    print(f'  唯一订单: {unique_orders:,}')
    print(f'  商品实收额: ¥{row[0]:,.2f}' if row[0] else '  商品实收额: ¥0')
    print(f'  总利润: ¥{row[1]:,.2f}' if row[1] else '  总利润: ¥0')
finally:
    session.close()
"@
    
    python -c $pythonCode
}

# 主程序
Show-Banner
Activate-Venv | Out-Null

while ($true) {
    Show-Menu
    $choice = Read-Host "请输入选项 [0-4]"
    
    switch ($choice) {
        "1" {
            # 增量导入
            Show-Banner
            Write-ColorOutput "📋 模式: 增量导入`n" "Green"
            
            if (-not (Show-FileList)) {
                Read-Host "`n按回车键返回菜单"
                Show-Banner
                continue
            }
            
            $confirm = Read-Host "确认开始增量导入？(y/n)"
            if ($confirm -eq "y" -or $confirm -eq "Y") {
                Start-Import -Mode "incremental"
                Show-ImportResult
            }
            
            Read-Host "`n按回车键返回菜单"
            Show-Banner
        }
        "2" {
            # 全量重新导入
            Show-Banner
            Write-ColorOutput "📋 模式: 全量重新导入`n" "Yellow"
            Write-ColorOutput "⚠️  此操作将清空所有现有数据后重新导入！`n" "Red"
            
            if (-not (Show-FileList)) {
                Read-Host "`n按回车键返回菜单"
                Show-Banner
                continue
            }
            
            $confirm = Read-Host "确认要清空数据并重新导入？(输入 yes 确认)"
            if ($confirm -eq "yes") {
                Clear-AllData
                Start-Import -Mode "incremental"
                Show-ImportResult
                Write-ColorOutput "`n✅ 全量重新导入完成！" "Green"
            } else {
                Write-ColorOutput "已取消操作" "Yellow"
            }
            
            Read-Host "`n按回车键返回菜单"
            Show-Banner
        }
        "3" {
            # 仅清理数据
            Show-Banner
            Write-ColorOutput "📋 模式: 仅清理数据`n" "Red"
            Write-ColorOutput "⚠️  此操作将删除所有订单数据、导入历史、预聚合表！`n" "Red"
            
            Show-DataStatus
            
            $confirm = Read-Host "`n确认要清空所有数据？(输入 yes 确认)"
            if ($confirm -eq "yes") {
                Clear-AllData
            } else {
                Write-ColorOutput "已取消操作" "Yellow"
            }
            
            Read-Host "`n按回车键返回菜单"
            Show-Banner
        }
        "4" {
            # 查看数据状态
            Show-Banner
            Show-DataStatus
            Read-Host "`n按回车键返回菜单"
            Show-Banner
        }
        "0" {
            Write-ColorOutput "`n👋 再见！`n" "Cyan"
            exit 0
        }
        default {
            Write-ColorOutput "`n❌ 无效选项，请重新选择`n" "Red"
            Start-Sleep -Seconds 1
            Show-Banner
        }
    }
}
