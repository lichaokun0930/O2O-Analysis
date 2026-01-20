# -*- coding: utf-8 -*-
"""
验证后端是否加载了修改后的代码

通过检查 API 返回的数据来判断是否使用了配送净成本
"""

import requests

BASE_URL = "http://localhost:8080/api/v1"

def test_delivery_cost_calculation():
    print("="*80)
    print("验证后端代码版本 - 检查单均配送费计算")
    print("="*80)
    
    # 测试美团渠道
    print("\n📊 测试美团渠道 (最近7天):")
    print("-"*60)
    
    try:
        resp = requests.get(
            f"{BASE_URL}/stores/comparison",
            params={
                "start_date": "2026-01-12",
                "end_date": "2026-01-18",
                "channel": "美团"
            },
            timeout=120
        )
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                stores = data.get("data", {}).get("stores", [])
                target = next((s for s in stores if "泰州泰兴" in s.get("store_name", "")), None)
                if target:
                    print(f"  门店: {target.get('store_name')}")
                    print(f"  订单数: {target.get('order_count')}")
                    print(f"  单均配送费: ¥{target.get('avg_delivery_fee', 0):.2f}")
                    print(f"  单均营销费: ¥{target.get('avg_marketing_cost', 0):.2f}")
                    
                    # 判断是否使用了配送净成本
                    avg_delivery = target.get('avg_delivery_fee', 0)
                    if 3.5 <= avg_delivery <= 4.5:
                        print(f"\n  ✅ 单均配送费接近 Dash 版本 (¥3.89)，代码已更新")
                    else:
                        print(f"\n  ⚠️ 单均配送费与 Dash 版本差异较大，可能需要重启后端")
                else:
                    print("  未找到泰州泰兴店")
            else:
                print(f"  API 返回失败: {data}")
        else:
            print(f"  API 错误: {resp.status_code}")
    except Exception as e:
        print(f"  错误: {e}")
    
    # 测试饿了么渠道
    print("\n📊 测试饿了么渠道 (最近7天):")
    print("-"*60)
    
    try:
        resp = requests.get(
            f"{BASE_URL}/stores/comparison",
            params={
                "start_date": "2026-01-12",
                "end_date": "2026-01-18",
                "channel": "饿了么"
            },
            timeout=120
        )
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                stores = data.get("data", {}).get("stores", [])
                target = next((s for s in stores if "泰州泰兴" in s.get("store_name", "")), None)
                if target:
                    print(f"  门店: {target.get('store_name')}")
                    print(f"  订单数: {target.get('order_count')}")
                    print(f"  单均配送费: ¥{target.get('avg_delivery_fee', 0):.2f}")
                    print(f"  单均营销费: ¥{target.get('avg_marketing_cost', 0):.2f}")
                    
                    # 判断是否使用了配送净成本
                    avg_delivery = target.get('avg_delivery_fee', 0)
                    if 1.0 <= avg_delivery <= 2.0:
                        print(f"\n  ✅ 单均配送费接近 Dash 版本 (¥1.61)，代码已更新")
                    else:
                        print(f"\n  ⚠️ 单均配送费与 Dash 版本差异较大，可能需要重启后端")
                else:
                    print("  未找到泰州泰兴店")
            else:
                print(f"  API 返回失败: {data}")
        else:
            print(f"  API 错误: {resp.status_code}")
    except Exception as e:
        print(f"  错误: {e}")
    
    print("\n" + "="*80)
    print("📋 Dash 版本参考值:")
    print("  美团渠道: 单均配送 ¥3.89")
    print("  饿了么渠道: 单均配送 ¥1.61")
    print("="*80)
    
    print("\n💡 如果数据不正确，请重启后端服务:")
    print("   cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload")


if __name__ == "__main__":
    test_delivery_cost_calculation()
