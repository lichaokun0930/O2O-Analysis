# -*- coding: utf-8 -*-
"""
测试 DuckDB 查询性能

对比 v1 (PostgreSQL预聚合表) 和 v2 (DuckDB+Parquet) 的查询性能
"""
import sys
from pathlib import Path
import time

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from datetime import date


def test_duckdb_queries():
    """测试DuckDB查询"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           🦆 DuckDB 查询性能测试
╠══════════════════════════════════════════════════════════════════╣
║  测试从 Parquet 文件查询数据的性能
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    from backend.app.services import duckdb_service
    
    # 检查状态
    status = duckdb_service.get_status()
    print(f"📊 DuckDB服务状态:")
    print(f"   - 原始Parquet文件: {status['raw_parquet_count']} 个")
    print(f"   - 原始数据大小: {status['raw_parquet_size_mb']} MB")
    print(f"   - 聚合Parquet文件: {status['aggregated_parquet_count']} 个")
    print(f"   - 有数据: {status['has_data']}")
    
    if not status['has_data']:
        print("\n❌ 无Parquet数据，请先运行迁移脚本")
        return False
    
    print("\n" + "="*60)
    print("📈 测试 KPI 查询")
    print("="*60)
    
    # 测试1: 全量KPI查询
    start = time.time()
    kpi = duckdb_service.query_kpi()
    elapsed = (time.time() - start) * 1000
    print(f"\n1. 全量KPI查询: {elapsed:.2f}ms")
    print(f"   - 订单数: {kpi['total_orders']:,}")
    print(f"   - 销售额: ¥{kpi['total_actual_sales']:,.2f}")
    print(f"   - 利润: ¥{kpi['total_profit']:,.2f}")
    print(f"   - 客单价: ¥{kpi['avg_order_value']:.2f}")
    print(f"   - 利润率: {kpi['profit_rate']:.2f}%")
    
    # 测试2: 按门店查询
    start = time.time()
    kpi_store = duckdb_service.query_kpi(store_name="惠宜选-泰州泰兴店")
    elapsed = (time.time() - start) * 1000
    print(f"\n2. 单门店KPI查询: {elapsed:.2f}ms")
    print(f"   - 订单数: {kpi_store['total_orders']:,}")
    print(f"   - 销售额: ¥{kpi_store['total_actual_sales']:,.2f}")
    
    # 测试3: 按日期范围查询
    start = time.time()
    kpi_range = duckdb_service.query_kpi(
        start_date=date(2026, 1, 10),
        end_date=date(2026, 1, 18)
    )
    elapsed = (time.time() - start) * 1000
    print(f"\n3. 日期范围KPI查询: {elapsed:.2f}ms")
    print(f"   - 订单数: {kpi_range['total_orders']:,}")
    
    print("\n" + "="*60)
    print("📈 测试趋势查询")
    print("="*60)
    
    # 测试4: 趋势查询
    start = time.time()
    trend = duckdb_service.query_trend(days=30)
    elapsed = (time.time() - start) * 1000
    print(f"\n4. 30天趋势查询: {elapsed:.2f}ms")
    print(f"   - 数据点数: {len(trend['dates'])}")
    if trend['dates']:
        print(f"   - 日期范围: {trend['dates'][0]} ~ {trend['dates'][-1]}")
        print(f"   - 总订单数: {sum(trend['order_counts']):,}")
    
    print("\n" + "="*60)
    print("📈 测试渠道查询")
    print("="*60)
    
    # 测试5: 渠道查询
    start = time.time()
    channels = duckdb_service.query_channels()
    elapsed = (time.time() - start) * 1000
    print(f"\n5. 渠道分析查询: {elapsed:.2f}ms")
    print(f"   - 渠道数: {len(channels)}")
    for ch in channels[:3]:
        print(f"   - {ch['channel']}: {ch['order_count']:,}单, ¥{ch['amount']:,.2f}")
    
    print("\n" + "="*60)
    print("📈 测试品类查询")
    print("="*60)
    
    # 测试6: 品类查询
    start = time.time()
    categories = duckdb_service.query_categories(top_n=5)
    elapsed = (time.time() - start) * 1000
    print(f"\n6. 品类分析查询: {elapsed:.2f}ms")
    print(f"   - 品类数: {len(categories)}")
    for cat in categories[:3]:
        print(f"   - {cat['category']}: ¥{cat['amount']:,.2f}")
    
    print("\n" + "="*60)
    print("✅ 所有测试完成！")
    print("="*60)
    
    return True


if __name__ == "__main__":
    success = test_duckdb_queries()
    sys.exit(0 if success else 1)
