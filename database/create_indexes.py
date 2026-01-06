#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库索引创建脚本 - 企业级优化
用途: 为常用查询创建索引，提升查询性能10-100倍
"""

import sys
import io
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text, inspect
from database.connection import engine

# 解决Windows PowerShell下emoji输出乱码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 定义需要创建的索引
INDEXES = [
    # 复合索引 - 最常用的查询组合
    {
        'name': 'idx_orders_store_date',
        'table': 'orders',
        'columns': ['store_name', 'date'],
        'description': '门店+日期复合索引 (最常用查询)'
    },
    {
        'name': 'idx_orders_store_channel',
        'table': 'orders',
        'columns': ['store_name', 'channel'],
        'description': '门店+渠道复合索引'
    },
    {
        'name': 'idx_orders_store_product',
        'table': 'orders',
        'columns': ['store_name', 'product_name'],
        'description': '门店+商品复合索引'
    },
    {
        'name': 'idx_orders_date_channel',
        'table': 'orders',
        'columns': ['date', 'channel'],
        'description': '日期+渠道复合索引'
    },
    
    # 单列索引 - 已存在的索引不会重复创建
    {
        'name': 'idx_orders_store_name',
        'table': 'orders',
        'columns': ['store_name'],
        'description': '门店名称索引'
    },
    {
        'name': 'idx_orders_product_name',
        'table': 'orders',
        'columns': ['product_name'],
        'description': '商品名称索引'
    },
    {
        'name': 'idx_orders_channel',
        'table': 'orders',
        'columns': ['channel'],
        'description': '渠道索引'
    },
    {
        'name': 'idx_orders_category_l1',
        'table': 'orders',
        'columns': ['category_level1'],
        'description': '一级分类索引'
    },
    {
        'name': 'idx_orders_scene',
        'table': 'orders',
        'columns': ['scene'],
        'description': '消费场景索引'
    },
    {
        'name': 'idx_orders_time_period',
        'table': 'orders',
        'columns': ['time_period'],
        'description': '时段索引'
    },
    
    # 性能优化索引
    {
        'name': 'idx_orders_date_desc',
        'table': 'orders',
        'columns': ['date DESC'],
        'description': '日期降序索引 (最新订单查询)'
    },
    
    # Product 表索引（用于 JOIN 优化）
    {
        'name': 'idx_product_barcode',
        'table': 'products',
        'columns': ['barcode'],
        'description': 'Product 表条码索引 (JOIN 优化)'
    },
    {
        'name': 'idx_product_name',
        'table': 'products',
        'columns': ['product_name'],
        'description': 'Product 表商品名称索引'
    },
]


def check_index_exists(index_name):
    """检查索引是否已存在"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM pg_indexes 
                    WHERE indexname = :index_name
                )
            """), {'index_name': index_name})
            return result.scalar()
    except Exception as e:
        print(f"   ⚠️ 检查索引失败: {e}")
        return False


def create_index(index_info):
    """创建单个索引"""
    name = index_info['name']
    table = index_info['table']
    columns = ', '.join(index_info['columns'])
    description = index_info['description']
    
    # 检查索引是否已存在
    if check_index_exists(name):
        print(f"   ⏭️ {name}: 已存在，跳过")
        return True
    
    try:
        sql = f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({columns})"
        
        with engine.connect() as conn:
            print(f"   🔨 创建索引: {name}")
            print(f"      表: {table}")
            print(f"      列: {columns}")
            print(f"      说明: {description}")
            
            conn.execute(text(sql))
            conn.commit()
            
            print(f"   ✅ 创建成功")
            return True
            
    except Exception as e:
        print(f"   ❌ 创建失败: {e}")
        return False


def analyze_table(table_name):
    """分析表以更新统计信息"""
    try:
        with engine.connect() as conn:
            conn.execute(text(f"ANALYZE {table_name}"))
            conn.commit()
        return True
    except Exception as e:
        print(f"   ⚠️ 分析表失败: {e}")
        return False


def get_table_stats(table_name):
    """获取表统计信息"""
    try:
        with engine.connect() as conn:
            # 获取行数
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            row_count = result.scalar()
            
            # 获取表大小
            result = conn.execute(text("""
                SELECT pg_size_pretty(pg_total_relation_size(:table_name))
            """), {'table_name': table_name})
            table_size = result.scalar()
            
            return {
                'rows': row_count,
                'size': table_size
            }
    except Exception as e:
        return {
            'rows': 'unknown',
            'size': 'unknown'
        }


def main():
    """主函数"""
    print("="*70)
    print("  数据库索引创建 - 企业级优化")
    print("="*70)
    print()
    
    # 检查数据库连接
    print("🔍 [1/4] 检查数据库连接...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("   ✅ 数据库连接正常")
    except Exception as e:
        print(f"   ❌ 数据库连接失败: {e}")
        print("   提示: 请确保PostgreSQL服务正在运行")
        return
    
    print()
    
    # 获取表统计信息
    print("📊 [2/4] 获取表统计信息...")
    stats = get_table_stats('orders')
    print(f"   表: orders")
    print(f"   行数: {stats['rows']}")
    print(f"   大小: {stats['size']}")
    print()
    
    # 创建索引
    print("🔨 [3/4] 创建索引...")
    print(f"   计划创建 {len(INDEXES)} 个索引")
    print()
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, index_info in enumerate(INDEXES, 1):
        print(f"📦 [{i}/{len(INDEXES)}] {index_info['name']}")
        
        if check_index_exists(index_info['name']):
            print(f"   ⏭️ 已存在，跳过")
            skip_count += 1
        else:
            if create_index(index_info):
                success_count += 1
            else:
                fail_count += 1
        
        print()
    
    # 分析表
    print("📈 [4/4] 分析表以更新统计信息...")
    if analyze_table('orders'):
        print("   ✅ 表分析完成")
    print()
    
    # 总结
    print("="*70)
    print("  索引创建完成")
    print("="*70)
    print()
    print(f"📊 总计: {len(INDEXES)} 个索引")
    print(f"   ✅ 新创建: {success_count}")
    print(f"   ⏭️ 已存在: {skip_count}")
    print(f"   ❌ 失败: {fail_count}")
    print()
    
    if success_count > 0:
        print("🎉 索引创建成功！")
        print()
        print("📋 预期收益:")
        print("   • 查询速度: 提升10-100倍")
        print("   • 数据库负载: 降低80%")
        print("   • 响应时间: 大幅降低")
        print()
        print("💡 建议:")
        print("   • 重启看板以应用优化")
        print("   • 运行压力测试验证性能提升")
    elif skip_count == len(INDEXES):
        print("ℹ️ 所有索引已存在，无需创建")
    else:
        print("⚠️ 部分索引创建失败，请检查错误信息")
    
    print()
    print("="*70)


if __name__ == '__main__':
    main()
