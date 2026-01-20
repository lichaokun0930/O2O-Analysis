# -*- coding: utf-8 -*-
"""
性能诊断分析 - 找出系统瓶颈

作为企业级工程师，我们需要先量化问题：
1. 数据量有多大？
2. 每个 API 的耗时分布在哪里？
3. 瓶颈是 I/O、计算还是网络？
"""

import time
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import func, text
import pandas as pd

def diagnose_data_volume():
    """诊断数据量"""
    print("="*80)
    print("📊 数据量诊断")
    print("="*80)
    
    session = SessionLocal()
    try:
        # 总记录数
        total_records = session.query(func.count(Order.id)).scalar()
        print(f"\n总记录数: {total_records:,} 条")
        
        # 唯一订单数
        unique_orders = session.query(func.count(func.distinct(Order.order_id))).scalar()
        print(f"唯一订单数: {unique_orders:,} 单")
        
        # 门店数
        store_count = session.query(func.count(func.distinct(Order.store_name))).scalar()
        print(f"门店数: {store_count} 个")
        
        # 日期范围
        min_date = session.query(func.min(Order.date)).scalar()
        max_date = session.query(func.max(Order.date)).scalar()
        print(f"日期范围: {min_date} ~ {max_date}")
        
        # 每个门店的平均记录数
        avg_per_store = total_records / store_count if store_count > 0 else 0
        print(f"每门店平均记录: {avg_per_store:,.0f} 条")
        
        # 数据量评估
        print("\n📋 数据量评估:")
        if total_records < 100000:
            print(f"   ✅ 数据量较小 ({total_records:,} 条)，不应该有性能问题")
            print(f"   ⚠️ 如果有性能问题，说明代码实现有问题")
        elif total_records < 1000000:
            print(f"   ⚠️ 中等数据量 ({total_records:,} 条)，需要适当优化")
        else:
            print(f"   🔴 大数据量 ({total_records:,} 条)，需要企业级优化")
        
        return total_records, unique_orders, store_count
    finally:
        session.close()


def diagnose_query_performance():
    """诊断查询性能"""
    print("\n" + "="*80)
    print("⏱️ 查询性能诊断")
    print("="*80)
    
    session = SessionLocal()
    try:
        # 测试1: 简单计数查询
        start = time.time()
        session.query(func.count(Order.id)).scalar()
        count_time = time.time() - start
        print(f"\n1. 简单计数查询: {count_time*1000:.1f}ms")
        
        # 测试2: 全表扫描
        start = time.time()
        orders = session.query(Order).limit(10000).all()
        scan_time = time.time() - start
        print(f"2. 读取10000条记录: {scan_time*1000:.1f}ms")
        
        # 测试3: 按门店筛选
        start = time.time()
        orders = session.query(Order).filter(
            Order.store_name == "惠宜选-泰州泰兴店"
        ).all()
        filter_time = time.time() - start
        print(f"3. 按门店筛选: {filter_time*1000:.1f}ms ({len(orders)} 条)")
        
        # 测试4: 按日期范围筛选
        start = time.time()
        from datetime import datetime
        orders = session.query(Order).filter(
            Order.date >= datetime(2026, 1, 12),
            Order.date <= datetime(2026, 1, 18)
        ).all()
        date_filter_time = time.time() - start
        print(f"4. 按日期范围筛选: {date_filter_time*1000:.1f}ms ({len(orders)} 条)")
        
        # 测试5: 复合筛选
        start = time.time()
        orders = session.query(Order).filter(
            Order.store_name == "惠宜选-泰州泰兴店",
            Order.date >= datetime(2026, 1, 12),
            Order.date <= datetime(2026, 1, 18)
        ).all()
        compound_time = time.time() - start
        print(f"5. 复合筛选(门店+日期): {compound_time*1000:.1f}ms ({len(orders)} 条)")
        
        # 性能评估
        print("\n📋 查询性能评估:")
        if compound_time < 0.5:
            print(f"   ✅ 数据库查询性能良好 (<500ms)")
        elif compound_time < 2:
            print(f"   ⚠️ 数据库查询较慢 ({compound_time*1000:.0f}ms)，建议添加索引")
        else:
            print(f"   🔴 数据库查询很慢 ({compound_time*1000:.0f}ms)，需要优化")
        
        return count_time, scan_time, filter_time
    finally:
        session.close()


def diagnose_pandas_performance():
    """诊断 Pandas 计算性能"""
    print("\n" + "="*80)
    print("🐼 Pandas 计算性能诊断")
    print("="*80)
    
    session = SessionLocal()
    try:
        # 加载数据
        start = time.time()
        orders = session.query(Order).all()
        load_time = time.time() - start
        print(f"\n1. 从数据库加载全部数据: {load_time*1000:.1f}ms ({len(orders)} 条)")
        
        # 转换为 DataFrame
        start = time.time()
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '门店名称': order.store_name,
                '渠道': order.channel,
                '实收价格': float(order.actual_price or 0),
                '物流配送费': float(order.delivery_fee or 0),
                '平台服务费': float(order.platform_service_fee or 0),
            })
        df = pd.DataFrame(data)
        convert_time = time.time() - start
        print(f"2. 转换为 DataFrame: {convert_time*1000:.1f}ms")
        
        # GroupBy 聚合
        start = time.time()
        order_agg = df.groupby('订单ID').agg({
            '实收价格': 'sum',
            '物流配送费': 'first',
            '平台服务费': 'sum',
        }).reset_index()
        groupby_time = time.time() - start
        print(f"3. GroupBy 订单聚合: {groupby_time*1000:.1f}ms ({len(order_agg)} 订单)")
        
        # 按门店聚合
        start = time.time()
        # 先合并门店信息
        order_store = df.groupby('订单ID')['门店名称'].first().reset_index()
        order_agg = order_agg.merge(order_store, on='订单ID')
        store_agg = order_agg.groupby('门店名称').agg({
            '订单ID': 'count',
            '实收价格': 'sum',
        }).reset_index()
        store_agg_time = time.time() - start
        print(f"4. 按门店聚合: {store_agg_time*1000:.1f}ms ({len(store_agg)} 门店)")
        
        # 性能评估
        total_time = load_time + convert_time + groupby_time + store_agg_time
        print(f"\n📋 Pandas 计算性能评估:")
        print(f"   总耗时: {total_time*1000:.1f}ms")
        
        if total_time < 2:
            print(f"   ✅ 计算性能良好 (<2秒)")
        elif total_time < 5:
            print(f"   ⚠️ 计算较慢，建议优化数据结构")
        else:
            print(f"   🔴 计算很慢，需要重构")
        
        # 瓶颈分析
        print(f"\n📊 耗时分布:")
        print(f"   数据库加载: {load_time/total_time*100:.1f}%")
        print(f"   DataFrame转换: {convert_time/total_time*100:.1f}%")
        print(f"   订单聚合: {groupby_time/total_time*100:.1f}%")
        print(f"   门店聚合: {store_agg_time/total_time*100:.1f}%")
        
        return load_time, convert_time, groupby_time
    finally:
        session.close()


def diagnose_api_bottleneck():
    """诊断 API 瓶颈"""
    print("\n" + "="*80)
    print("🔍 API 瓶颈诊断")
    print("="*80)
    
    import requests
    
    apis = [
        ("/stores/comparison", {"start_date": "2026-01-12", "end_date": "2026-01-18"}),
        ("/stores/comparison/week-over-week", {"end_date": "2026-01-18"}),
        ("/orders/overview", {"store_name": "惠宜选-泰州泰兴店"}),
        ("/orders/channels", {"store_name": "惠宜选-泰州泰兴店"}),
    ]
    
    print("\n单独请求各 API:")
    for api, params in apis:
        try:
            start = time.time()
            resp = requests.get(f"http://localhost:8080/api/v1{api}", params=params, timeout=60)
            elapsed = time.time() - start
            status = "✅" if resp.status_code == 200 else "❌"
            print(f"   {status} {api}: {elapsed*1000:.0f}ms")
        except Exception as e:
            print(f"   ❌ {api}: {e}")
    
    # 并发请求测试
    print("\n并发请求测试 (模拟前端同时请求):")
    import concurrent.futures
    
    def make_request(api_info):
        api, params = api_info
        start = time.time()
        try:
            resp = requests.get(f"http://localhost:8080/api/v1{api}", params=params, timeout=60)
            return api, time.time() - start, resp.status_code
        except Exception as e:
            return api, time.time() - start, str(e)
    
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(make_request, apis))
    total_time = time.time() - start
    
    for api, elapsed, status in results:
        status_str = "✅" if status == 200 else f"❌ {status}"
        print(f"   {status_str} {api}: {elapsed*1000:.0f}ms")
    
    print(f"\n   并发总耗时: {total_time*1000:.0f}ms")
    
    if total_time < 10:
        print(f"   ✅ 并发性能良好")
    else:
        print(f"   ⚠️ 并发性能需要优化")


def main():
    print("\n" + "🔬"*40)
    print("         企业级性能诊断分析")
    print("🔬"*40)
    
    # 1. 数据量诊断
    total_records, unique_orders, store_count = diagnose_data_volume()
    
    # 2. 查询性能诊断
    diagnose_query_performance()
    
    # 3. Pandas 计算性能诊断
    diagnose_pandas_performance()
    
    # 4. API 瓶颈诊断
    diagnose_api_bottleneck()
    
    # 总结
    print("\n" + "="*80)
    print("📋 诊断总结与优化建议")
    print("="*80)
    
    print(f"""
数据规模: {total_records:,} 条记录, {unique_orders:,} 订单, {store_count} 门店

这个数据量级（约 {total_records//1000}K 条）对于现代系统来说是很小的，
不应该有任何性能问题。如果出现超时，问题一定在代码实现上。

🎯 可能的瓶颈点:
1. 【数据库】没有合适的索引
2. 【后端】每次请求都重新加载全部数据（没有缓存）
3. 【后端】Pandas 计算逻辑冗余（重复计算）
4. 【后端】ORM 对象转换开销大
5. 【前端】同时发起太多请求，后端串行处理
6. 【前端】没有请求去重/防抖

🚀 企业级优化方案:
1. 数据库层: 添加复合索引 (store_name, date)
2. 缓存层: Redis 缓存聚合结果（5分钟过期）
3. 计算层: 预计算门店日汇总表
4. API层: 异步处理 + 连接池
5. 前端层: 请求合并 + 骨架屏 + 渐进加载
""")


if __name__ == "__main__":
    main()
