# -*- coding: utf-8 -*-
"""
测试后端 API 是否正常工作
"""

import requests
import time

BASE_URL = "http://localhost:8080/api/v1"

def test_api():
    print("="*80)
    print("测试后端 API")
    print("="*80)
    
    # 测试1: 健康检查
    print("\n1. 测试健康检查...")
    try:
        resp = requests.get(f"{BASE_URL.replace('/api/v1', '')}/", timeout=5)
        print(f"   状态码: {resp.status_code}")
        if resp.status_code == 200:
            print("   ✅ 后端服务正常运行")
        else:
            print("   ❌ 后端服务异常")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ 无法连接到后端服务，请确保后端已启动")
        print("   启动命令: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8080")
        return
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return
    
    # 测试2: 门店对比 API
    print("\n2. 测试门店对比 API...")
    try:
        start_time = time.time()
        resp = requests.get(
            f"{BASE_URL}/stores/comparison",
            params={
                "start_date": "2026-01-12",
                "end_date": "2026-01-18",
                "sort_by": "revenue",
                "sort_order": "desc"
            },
            timeout=120
        )
        elapsed = time.time() - start_time
        print(f"   状态码: {resp.status_code}")
        print(f"   耗时: {elapsed:.2f}秒")
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                stores = data.get("data", {}).get("stores", [])
                print(f"   ✅ 返回 {len(stores)} 个门店")
                
                # 查找泰州泰兴店
                target = next((s for s in stores if "泰州泰兴" in s.get("store_name", "")), None)
                if target:
                    print(f"\n   📊 惠宜选-泰州泰兴店:")
                    print(f"      订单数: {target.get('order_count')}")
                    print(f"      单均配送费: ¥{target.get('avg_delivery_fee', 0):.2f}")
                    print(f"      单均营销费: ¥{target.get('avg_marketing_cost', 0):.2f}")
            else:
                print(f"   ❌ API 返回失败: {data}")
        else:
            print(f"   ❌ API 错误: {resp.text[:200]}")
    except requests.exceptions.Timeout:
        print("   ❌ 请求超时（120秒）")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 测试3: 环比数据 API
    print("\n3. 测试环比数据 API...")
    try:
        start_time = time.time()
        resp = requests.get(
            f"{BASE_URL}/stores/comparison/week-over-week",
            params={
                "end_date": "2026-01-18",
                "previous_start": "2026-01-05",
                "previous_end": "2026-01-11"
            },
            timeout=120
        )
        elapsed = time.time() - start_time
        print(f"   状态码: {resp.status_code}")
        print(f"   耗时: {elapsed:.2f}秒")
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                stores = data.get("data", {}).get("stores", [])
                print(f"   ✅ 返回 {len(stores)} 个门店")
            else:
                print(f"   ❌ API 返回失败: {data}")
        else:
            print(f"   ❌ API 错误: {resp.text[:200]}")
    except requests.exceptions.Timeout:
        print("   ❌ 请求超时（120秒）")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    print("\n" + "="*80)
    print("📋 Dash 版本参考值:")
    print("   美团渠道: 单均配送 ¥3.89")
    print("   饿了么渠道: 单均配送 ¥1.61")
    print("="*80)


if __name__ == "__main__":
    test_api()
