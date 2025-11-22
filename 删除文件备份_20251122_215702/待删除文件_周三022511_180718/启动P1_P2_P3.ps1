# P1/P2/P3 快速启动脚本集合

Write-Output ""
Write-Output "=========================================="
Write-Output "  智能门店经营看板 - P1/P2/P3 任务启动"
Write-Output "=========================================="
Write-Output ""

# 功能选择
Write-Output "请选择要启动的功能:"
Write-Output ""
Write-Output "  [1] P1 - 批量历史数据导入"
Write-Output "  [2] P2 - 数据源切换看板 (Excel/数据库)"
Write-Output "  [3] P3 - 前后端集成看板 (仅API)"
Write-Output "  [4] 测试数据源管理器"
Write-Output "  [5] 查看数据库统计"
Write-Output "  [0] 退出"
Write-Output ""

$choice = Read-Host "请输入选项 (0-5)"

switch ($choice) {
    "1" {
        Write-Output ""
        Write-Output "[P1] 启动批量历史数据导入..."
        Write-Output "=========================================="
        Write-Output ""
        
        # 询问数据目录
        Write-Output "默认数据目录: 实际数据\"
        $useDefault = Read-Host "使用默认目录? (Y/n)"
        
        if ($useDefault -eq "n" -or $useDefault -eq "N") {
            $dataDir = Read-Host "请输入数据目录路径"
            D:/办公/Python/python.exe database/batch_import.py $dataDir
        } else {
            D:/办公/Python/python.exe database/batch_import.py
        }
    }
    
    "2" {
        Write-Output ""
        Write-Output "[P2] 启动数据源切换看板..."
        Write-Output "=========================================="
        Write-Output "功能: Excel文件 + PostgreSQL数据库"
        Write-Output "端口: 8050"
        Write-Output "地址: http://localhost:8050"
        Write-Output "=========================================="
        Write-Output ""
        
        D:/办公/Python/python.exe dashboard_with_source_switch.py
    }
    
    "3" {
        Write-Output ""
        Write-Output "[P3] 启动前后端集成看板..."
        Write-Output "=========================================="
        Write-Output "架构: 前后端分离 (通过API通信)"
        Write-Output "端口: 8051"
        Write-Output "地址: http://localhost:8051"
        Write-Output "=========================================="
        Write-Output ""
        Write-Output "⚠️  请确保后端服务已启动!"
        Write-Output "后端启动命令: python -m uvicorn backend.main:app --port 8000"
        Write-Output ""
        
        $continue = Read-Host "后端已启动? (Y/n)"
        
        if ($continue -ne "n" -and $continue -ne "N") {
            D:/办公/Python/python.exe dashboard_integrated.py
        } else {
            Write-Output "已取消启动"
        }
    }
    
    "4" {
        Write-Output ""
        Write-Output "[测试] 数据源管理器测试..."
        Write-Output "=========================================="
        Write-Output ""
        
        D:/办公/Python/python.exe database/data_source_manager.py
    }
    
    "5" {
        Write-Output ""
        Write-Output "[统计] 数据库统计信息..."
        Write-Output "=========================================="
        Write-Output ""
        
        # 使用Python快速查询
        D:/办公/Python/python.exe -c @"
import sys
sys.path.insert(0, '.')
from database.data_source_manager import DataSourceManager

manager = DataSourceManager()
stats = manager.get_database_stats()

print('数据库统计信息:')
print('=' * 40)
print(f'商品总数: {stats.get(\"products\", 0):,}')
print(f'订单总数: {stats.get(\"orders\", 0):,}')
print(f'门店数量: {stats.get(\"stores\", 0):,}')

if stats.get('start_date'):
    print(f'日期范围: {stats[\"start_date\"]} ~ {stats[\"end_date\"]}')

print('')
print('可用门店:')
stores = manager.get_available_stores()
for i, store in enumerate(stores[:10], 1):
    print(f'  {i}. {store}')

if len(stores) > 10:
    print(f'  ... 还有 {len(stores)-10} 个门店')
"@
        
        Write-Output ""
        Read-Host "按回车键继续..."
    }
    
    "0" {
        Write-Output "退出"
        exit
    }
    
    default {
        Write-Output "无效选项: $choice"
    }
}

Write-Output ""
Write-Output "=========================================="
Write-Output "操作完成"
Write-Output "=========================================="
Write-Output ""
