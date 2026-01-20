# -*- coding: utf-8 -*-
"""
测试全看板性能优化效果

验证所有模块的预聚合表查询性能
"""

import requests
import time
import json

API_BASE = "http://localhost:8080/api/v1"

def test_overview():
    """测试经营总览API"""
    print("\n1. 经营总览 (orders/overview)")
    print("-" * 40)
    
    params = {
        "store_name": "惠宜选-泰州泰兴店",
        "start_date": "2026-01-12",
        "end_date": "2026-01-18"
    }
    
    # 使用预聚合表
    start = time.time()
    try:
        resp = requests.get(f"{API_BASE}/orders/overview", params={**params, "use_aggregation": "true"}, timeout=30)
        t1 = time.time() - start
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            print(f"   预聚合表: {t1*1000:.0f}ms")
            print(f"   订单数: {data.get('total_orders')}, 销售额: ¥{data.get('total_actual_sales'):,.0f}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 不使用预聚合表
    start = time.time()
    try:
        resp = requests.get(f"{API_BASE}/orders/overview", params={**params, "use_aggregation": "false"}, timeout=60)
        t2 = time.time() - start
        if resp.status_code == 200:
            print(f"   原始查询: {t2*1000:.0f}ms")
            if t1 > 0:
                print(f"   提升: {(t2-t1)/t2*100:.0f}%")
    except Exception as e:
        print(f"   ❌ 原始查询错误: {e}")


def test_store_comparison():
    """测试全量门店对比API"""
    print("\n2. 全量门店对比 (stores/comparison)")
    print("-" * 40)
    
    params = {
        "start_date": "2026-01-12",
        "end_date": "2026-01-18"
    }
    
    start = time.time()
    try:
        resp = requests.get(f"{API_BASE}/stores/comparison", params={**params, "use_aggregation": "true"}, timeout=30)
        t1 = time.time() - start
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            stores = data.get("stores", [])
            print(f"   预聚合表: {t1*1000:.0f}ms ({len(stores)} 门店)")
    except Exception as e:
        print(f"   ❌ 错误: {e}")


def test_daily_trend():
    """测试日趋势API"""
    print("\n3. 日趋势图 (orders/trend)")
    print("-" * 40)
    
    params = {
        "store_name": "惠宜选-泰州泰兴店",
        "days": 30
    }
    
    start = time.time()
    try:
        resp = requests.get(f"{API_BASE}/orders/trend", params=params, timeout=30)
        t1 = time.time() - start
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            print(f"   响应时间: {t1*1000:.0f}ms ({len(data)} 天)")
        else:
            print(f"   状态码: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")


def test_hourly_analysis():
    """测试分时段分析API"""
    print("\n4. 分时段分析 (orders/hourly-profit)")
    print("-" * 40)
    
    params = {
        "store_name": "惠宜选-泰州泰兴店",
        "start_date": "2026-01-12",
        "end_date": "2026-01-18"
    }
    
    start = time.time()
    try:
        resp = requests.get(f"{API_BASE}/orders/hourly-profit", params=params, timeout=30)
        t1 = time.time() - start
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            hours = data.get("hours", [])
            print(f"   响应时间: {t1*1000:.0f}ms ({len(hours)} 时段)")
        else:
            print(f"   状态码: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")


def test_category_health():
    """测试品类健康度API"""
    print("\n5. 品类健康度 (category-health/health)")
    print("-" * 40)
    
    params = {
        "store_name": "惠宜选-泰州泰兴店",
        "start_date": "2026-01-12",
        "end_date": "2026-01-18"
    }
    
    start = time.time()
    try:
        resp = requests.get(f"{API_BASE}/category-health/health", params=params, timeout=30)
        t1 = time.time() - start
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            print(f"   响应时间: {t1*1000:.0f}ms ({len(data)} 品类)")
        else:
            print(f"   状态码: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")


def test_top_products():
    """测试商品销量排行API"""
    print("\n6. 商品销量排行 (orders/top-products-by-date)")
    print("-" * 40)
    
    params = {
        "store_name": "惠宜选-泰州泰兴店",
        "date": "2026-01-18",
        "limit": 20
    }
    
    start = time.time()
    try:
        resp = requests.get(f"{API_BASE}/orders/top-products-by-date", params=params, timeout=30)
        t1 = time.time() - start
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            print(f"   响应时间: {t1*1000:.0f}ms (Top {len(data)} 商品)")
        else:
            print(f"   状态码: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")


def main():
    print("\n" + "🚀"*30)
    print("      全看板性能优化效果测试")
    print("🚀"*30)
    
    # 检查后端是否运行
    try:
        resp = requests.get(f"{API_BASE}/orders/stores", timeout=5)
        if resp.status_code != 200:
            print("\n❌ 后端服务未运行")
            return
    except:
        print("\n❌ 后端服务未运行，请先启动后端")
        print("   cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8080")
        return
    
    test_overview()
    test_store_comparison()
    test_daily_trend()
    test_hourly_analysis()
    test_category_health()
    test_top_products()
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)


if __name__ == "__main__":
    main()
