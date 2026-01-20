# -*- coding: utf-8 -*-
"""
测试企业级性能优化效果

验证：
1. 预聚合表查询性能
2. API响应时间
3. 数据准确性对比
"""

import requests
import time
import json

API_BASE = "http://localhost:8080/api/v1/stores"

def test_api_performance():
    """测试API性能"""
    print("\n" + "="*80)
    print("🚀 测试全量门店对比API性能")
    print("="*80)
    
    # 测试参数
    params = {
        "start_date": "2026-01-12",
        "end_date": "2026-01-18"
    }
    
    # 测试1: 使用预聚合表
    print("\n1. 使用预聚合表查询:")
    params_agg = {**params, "use_aggregation": "true"}
    start = time.time()
    try:
        resp = requests.get(f"{API_BASE}/comparison", params=params_agg, timeout=30)
        elapsed = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            stores = data.get("data", {}).get("stores", [])
            print(f"   ✅ 响应时间: {elapsed*1000:.1f}ms")
            print(f"   门店数量: {len(stores)}")
            
            # 显示惠宜选-泰州泰兴店的数据
            for store in stores:
                if store.get("store_name") == "惠宜选-泰州泰兴店":
                    print(f"\n   惠宜选-泰州泰兴店:")
                    print(f"      订单数: {store.get('order_count')}")
                    print(f"      销售额: ¥{store.get('total_revenue'):,.2f}")
                    print(f"      单均配送费: ¥{store.get('avg_delivery_fee'):.2f}")
                    print(f"      单均营销费: ¥{store.get('avg_marketing_cost'):.2f}")
                    break
        else:
            print(f"   ❌ 请求失败: {resp.status_code}")
            print(f"   {resp.text[:200]}")
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
    
    # 测试2: 不使用预聚合表（对比）
    print("\n2. 不使用预聚合表查询（对比）:")
    params_raw = {**params, "use_aggregation": "false"}
    start = time.time()
    try:
        resp = requests.get(f"{API_BASE}/comparison", params=params_raw, timeout=120)
        elapsed = time.time() - start
        
        if resp.status_code == 200:
            data = resp.json()
            stores = data.get("data", {}).get("stores", [])
            print(f"   ✅ 响应时间: {elapsed*1000:.1f}ms")
            print(f"   门店数量: {len(stores)}")
            
            # 显示惠宜选-泰州泰兴店的数据
            for store in stores:
                if store.get("store_name") == "惠宜选-泰州泰兴店":
                    print(f"\n   惠宜选-泰州泰兴店:")
                    print(f"      订单数: {store.get('order_count')}")
                    print(f"      销售额: ¥{store.get('total_revenue'):,.2f}")
                    print(f"      单均配送费: ¥{store.get('avg_delivery_fee'):.2f}")
                    print(f"      单均营销费: ¥{store.get('avg_marketing_cost'):.2f}")
                    break
        else:
            print(f"   ❌ 请求失败: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")


def test_channel_filter():
    """测试渠道筛选"""
    print("\n" + "="*80)
    print("🔍 测试渠道筛选功能")
    print("="*80)
    
    channels = ["美团", "饿了么", "京东"]
    
    for channel in channels:
        params = {
            "start_date": "2026-01-12",
            "end_date": "2026-01-18",
            "channel": channel,
            "use_aggregation": "true"
        }
        
        start = time.time()
        try:
            resp = requests.get(f"{API_BASE}/comparison", params=params, timeout=30)
            elapsed = time.time() - start
            
            if resp.status_code == 200:
                data = resp.json()
                stores = data.get("data", {}).get("stores", [])
                
                # 找惠宜选-泰州泰兴店
                for store in stores:
                    if store.get("store_name") == "惠宜选-泰州泰兴店":
                        print(f"\n{channel}渠道 (响应: {elapsed*1000:.1f}ms):")
                        print(f"   订单数: {store.get('order_count')}")
                        print(f"   单均配送费: ¥{store.get('avg_delivery_fee'):.2f}")
                        print(f"   单均营销费: ¥{store.get('avg_marketing_cost'):.2f}")
                        break
        except Exception as e:
            print(f"\n{channel}渠道: ❌ {e}")
    
    print("\n📋 Dash 版本参考值:")
    print("   美团共橙: 单均配送 ¥3.89, 单均营销 ¥5.19")
    print("   饿了么: 单均配送 ¥1.61, 单均营销 ¥5.58")


def main():
    print("\n" + "🚀"*40)
    print("         企业级性能优化效果测试")
    print("🚀"*40)
    
    # 检查后端是否运行
    try:
        resp = requests.get(f"{API_BASE}/comparison/available-channels", timeout=5)
        if resp.status_code != 200:
            print("\n❌ 后端服务未运行，请先启动后端服务")
            print("   cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8080")
            return
    except:
        print("\n❌ 后端服务未运行，请先启动后端服务")
        print("   cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8080")
        return
    
    test_api_performance()
    test_channel_filter()
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)


if __name__ == "__main__":
    main()
