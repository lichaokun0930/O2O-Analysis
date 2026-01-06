#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
今日必做Tab性能诊断脚本

检查所有可能影响性能的因素
"""

import sys
import time
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

print("="*80)
print("今日必做Tab性能诊断")
print("="*80)
print()

# 1. 检查Redis连接
print("[1/6] 检查Redis缓存...")
try:
    import redis
    client = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=5)
    result = client.ping()
    print(f"   ✅ Redis连接: {'正常' if result else '失败'}")
    
    # 检查缓存管理器
    try:
        from redis_cache_manager import REDIS_CACHE_MANAGER
        if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
            print(f"   ✅ Redis缓存管理器: 已启用")
        else:
            print(f"   ❌ Redis缓存管理器: 未启用")
    except Exception as e:
        print(f"   ❌ Redis缓存管理器导入失败: {e}")
        
except Exception as e:
    print(f"   ❌ Redis连接失败: {e}")

print()

# 2. 检查数据库连接
print("[2/6] 检查PostgreSQL数据库...")
try:
    from database.connection import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1')).fetchone()
        print(f"   ✅ 数据库连接: 正常")
        
        # 检查索引
        index_query = text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'orders' 
            AND schemaname = 'public'
        """)
        indexes = conn.execute(index_query).fetchall()
        print(f"   ✅ orders表索引数量: {len(indexes)}个")
        if len(indexes) < 10:
            print(f"   ⚠️  索引数量偏少，建议运行: python database/create_indexes.py")
            
except Exception as e:
    print(f"   ❌ 数据库连接失败: {e}")

print()

# 3. 检查数据量
print("[3/6] 检查数据量...")
try:
    data_dir = APP_DIR / "实际数据"
    excel_files = list(data_dir.glob("*.xlsx"))
    if excel_files:
        latest_file = max(excel_files, key=lambda x: x.stat().st_mtime)
        print(f"   文件: {latest_file.name}")
        
        import pandas as pd
        df = pd.read_excel(latest_file)
        print(f"   ✅ 数据行数: {len(df):,}行")
        print(f"   ✅ 订单数: {df['订单ID'].nunique():,}单")
        print(f"   ✅ 商品数: {df['商品名称'].nunique():,}个")
        
        if len(df) > 50000:
            print(f"   ⚠️  数据量较大，建议启用V8.7数据采样优化")
    else:
        print(f"   ❌ 未找到数据文件")
except Exception as e:
    print(f"   ❌ 数据检查失败: {e}")

print()

# 4. 检查V8.6优化
print("[4/6] 检查V8.6订单聚合优化...")
try:
    from components.today_must_do.diagnosis_analysis import calculate_order_aggregation
    print(f"   ✅ calculate_order_aggregation函数: 已导入")
    
    # 测试性能
    if 'df' in locals():
        start = time.time()
        order_agg = calculate_order_aggregation(df)
        elapsed = time.time() - start
        print(f"   ✅ 订单聚合耗时: {elapsed:.2f}秒")
        if elapsed > 1:
            print(f"   ⚠️  聚合较慢，可能需要优化")
except Exception as e:
    print(f"   ❌ V8.6优化检查失败: {e}")

print()

# 5. 检查V8.8-V8.9优化
print("[5/6] 检查V8.8-V8.9优化...")
try:
    from components.today_must_do.debounce_utils import debounce
    print(f"   ✅ 防抖工具: 已导入")
except Exception as e:
    print(f"   ❌ 防抖工具导入失败: {e}")

try:
    from components.today_must_do.pagination_utils import get_pagination_config
    print(f"   ✅ 分页工具: 已导入")
    
    if 'df' in locals():
        config = get_pagination_config(len(df))
        print(f"   ✅ 分页策略: {config['mode']} (每页{config['page_size']}行)")
except Exception as e:
    print(f"   ❌ 分页工具导入失败: {e}")

print()

# 6. 性能建议
print("[6/6] 性能建议...")
print()

issues = []
recommendations = []

# Redis检查
try:
    from redis_cache_manager import REDIS_CACHE_MANAGER
    if not (REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled):
        issues.append("Redis缓存未启用")
        recommendations.append("1. 确保Memurai服务正在运行")
        recommendations.append("2. 检查看板启动日志中的Redis初始化信息")
        recommendations.append("3. 运行: Get-Service Memurai | Start-Service")
except:
    pass

# 数据库索引检查
try:
    if 'indexes' in locals() and len(indexes) < 10:
        issues.append("数据库索引不足")
        recommendations.append("4. 运行: python database/create_indexes.py")
except:
    pass

# 数据量检查
try:
    if 'df' in locals() and len(df) > 50000:
        issues.append("数据量较大")
        recommendations.append("5. V8.7数据采样优化应该会自动生效")
except:
    pass

if issues:
    print("⚠️  发现以下问题:")
    for issue in issues:
        print(f"   - {issue}")
    print()
    print("💡 建议:")
    for rec in recommendations:
        print(f"   {rec}")
else:
    print("✅ 所有检查通过，系统配置正常")
    print()
    print("如果今日必做Tab仍然很慢，可能的原因:")
    print("   1. 首次加载需要计算缓存（40秒左右）")
    print("   2. 二次加载应该<1秒（如果Redis正常）")
    print("   3. 检查浏览器控制台是否有错误")

print()
print("="*80)
print("诊断完成")
print("="*80)
