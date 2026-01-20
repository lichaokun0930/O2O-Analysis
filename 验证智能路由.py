# -*- coding: utf-8 -*-
"""
验证智能路由功能（本地测试，不需要后端运行）

直接调用服务层验证智能路由逻辑
"""

import sys
from pathlib import Path

# 添加路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend" / "app"))

def main():
    print("\n" + "=" * 60)
    print("  🧠 智能查询路由验证")
    print("=" * 60)
    
    # 1. 初始化路由服务
    print("\n1. 初始化路由服务...")
    from backend.app.services.query_router_service import query_router_service
    
    report = query_router_service.initialize()
    
    print(f"\n📊 数据量: {report['record_count']:,} 条")
    print(f"📈 切换阈值: {report['switch_threshold']:,} 条")
    print(f"🎯 当前引擎: {report['current_engine'].upper()}")
    print(f"💡 推荐引擎: {report['recommended_engine'].upper()}")
    print(f"📊 数据级别: {report['data_level_desc']}")
    
    pg_status = report['engines']['postgresql']
    dk_status = report['engines']['duckdb']
    
    print(f"\n🔧 引擎可用性:")
    print(f"   PostgreSQL: {'✅ ' + pg_status['reason'] if pg_status['available'] else '❌ ' + pg_status['reason']}")
    print(f"   DuckDB: {'✅ ' + dk_status['reason'] if dk_status['available'] else '⚠️ ' + dk_status['reason']}")
    
    # 2. 测试智能路由查询
    print("\n" + "=" * 60)
    print("2. 测试智能路由查询...")
    
    try:
        result = query_router_service.query_overview()
        print(f"\n✅ 查询成功!")
        print(f"   引擎: {result.engine.value.upper()}")
        print(f"   来源: {result.source}")
        print(f"   耗时: {result.query_time_ms:.2f}ms")
        
        if result.data:
            print(f"\n📊 查询结果:")
            print(f"   订单数: {result.data.get('total_orders', 0):,}")
            print(f"   销售额: ¥{result.data.get('total_actual_sales', 0):,.2f}")
            print(f"   利润: ¥{result.data.get('total_profit', 0):,.2f}")
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    
    # 3. 测试强制切换
    print("\n" + "=" * 60)
    print("3. 测试强制切换引擎...")
    
    current = report['current_engine']
    target = 'duckdb' if current == 'postgresql' else 'postgresql'
    
    print(f"\n当前引擎: {current.upper()}")
    print(f"尝试切换到: {target.upper()}")
    
    switch_result = query_router_service.force_engine(target)
    
    if switch_result['success']:
        print(f"✅ {switch_result['message']}")
        
        # 验证切换后的查询
        print("\n验证切换后的查询...")
        result = query_router_service.query_overview()
        print(f"   使用引擎: {result.engine.value.upper()}")
        print(f"   查询耗时: {result.query_time_ms:.2f}ms")
        
        # 切换回原引擎
        query_router_service.force_engine(current)
        print(f"\n✅ 已恢复到 {current.upper()}")
    else:
        print(f"❌ {switch_result['message']}")
    
    # 4. 性能对比
    print("\n" + "=" * 60)
    print("4. 性能对比测试...")
    
    import time
    
    # PostgreSQL
    query_router_service.force_engine('postgresql')
    pg_times = []
    for _ in range(5):
        result = query_router_service.query_overview()
        pg_times.append(result.query_time_ms)
    
    # DuckDB
    switch_result = query_router_service.force_engine('duckdb')
    dk_times = []
    if switch_result['success']:
        for _ in range(5):
            result = query_router_service.query_overview()
            dk_times.append(result.query_time_ms)
    
    # 恢复
    query_router_service.force_engine(current)
    
    print(f"\n🐘 PostgreSQL (5次查询):")
    print(f"   平均耗时: {sum(pg_times)/len(pg_times):.2f}ms")
    print(f"   最快: {min(pg_times):.2f}ms")
    print(f"   最慢: {max(pg_times):.2f}ms")
    
    if dk_times:
        print(f"\n🦆 DuckDB (5次查询):")
        print(f"   平均耗时: {sum(dk_times)/len(dk_times):.2f}ms")
        print(f"   最快: {min(dk_times):.2f}ms")
        print(f"   最慢: {max(dk_times):.2f}ms")
        
        pg_avg = sum(pg_times)/len(pg_times)
        dk_avg = sum(dk_times)/len(dk_times)
        
        print(f"\n📊 对比结论:")
        if dk_avg < pg_avg:
            print(f"   DuckDB 更快，加速比: {pg_avg/dk_avg:.2f}x")
        else:
            print(f"   PostgreSQL 更快，加速比: {dk_avg/pg_avg:.2f}x")
    else:
        print(f"\n⚠️ DuckDB 不可用，无法对比")
    
    # 5. 查询统计
    print("\n" + "=" * 60)
    print("5. 查询统计...")
    
    status = query_router_service.get_status()
    stats = status['stats']
    
    print(f"\n📈 查询统计:")
    print(f"   PostgreSQL 查询次数: {stats['postgresql_queries']}")
    print(f"   DuckDB 查询次数: {stats['duckdb_queries']}")
    print(f"   引擎切换次数: {stats['auto_switches']}")
    
    print("\n" + "=" * 60)
    print("✅ 验证完成!")
    print("=" * 60)
    
    print("\n💡 说明:")
    print(f"   - 当前数据量: {report['record_count']:,} 条")
    print(f"   - 切换阈值: {report['switch_threshold']:,} 条")
    remaining = report['switch_threshold'] - report['record_count']
    if remaining > 0:
        print(f"   - 还需 {remaining:,} 条数据才会自动切换到 DuckDB")
    else:
        print(f"   - 数据量已达标，系统会自动使用 DuckDB")

if __name__ == "__main__":
    main()
