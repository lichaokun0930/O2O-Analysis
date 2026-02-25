# -*- coding: utf-8 -*-
"""
对比经营总览TAB和全量门店对比TAB的数据差异

测试条件：
- 门店：惠宜选-泰州兴化店
- 日期：2026-01-16 ~ 2026-01-22
- 经营总览显示：3555.5
- 全量门店对比显示：3335.61
- 差异：219.89
"""

import requests
import json

API_BASE = "http://localhost:8000/api/v1"
STORE_NAME = "惠宜选-泰州兴化店"
START_DATE = "2026-01-16"
END_DATE = "2026-01-22"

def test_overview_api():
    """测试经营总览API（/orders/overview）"""
    print("\n" + "=" * 60)
    print("【经营总览TAB】/orders/overview API")
    print("=" * 60)
    
    params = {
        "store_name": STORE_NAME,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "use_aggregation": False
    }
    
    try:
        resp = requests.get(f"{API_BASE}/orders/overview", params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                result = data["data"]
                print(f"订单数: {result.get('total_orders')}")
                print(f"销售额: ¥{result.get('total_actual_sales'):,.2f}")
                print(f"总利润: ¥{result.get('total_profit'):,.2f}")
                print(f"利润率: {result.get('profit_rate'):.2f}%")
                return result
        else:
            print(f"❌ 请求失败: {resp.status_code}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    return None


def test_comparison_api():
    """测试全量门店对比API（/stores/comparison）"""
    print("\n" + "=" * 60)
    print("【全量门店对比TAB】/stores/comparison API")
    print("=" * 60)
    
    params = {
        "start_date": START_DATE,
        "end_date": END_DATE,
        "use_aggregation": False
    }
    
    try:
        resp = requests.get(f"{API_BASE}/stores/comparison", params=params, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                stores = data["data"]["stores"]
                # 找到目标门店
                target = None
                for store in stores:
                    if store["store_name"] == STORE_NAME:
                        target = store
                        break
                
                if target:
                    print(f"订单数: {target.get('order_count')}")
                    print(f"销售额: ¥{target.get('total_revenue'):,.2f}")
                    print(f"总利润: ¥{target.get('total_profit'):,.2f}")
                    print(f"利润率: {target.get('profit_margin'):.2f}%")
                    return target
                else:
                    print(f"❌ 未找到门店: {STORE_NAME}")
        else:
            print(f"❌ 请求失败: {resp.status_code}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    return None


def compare_results():
    """对比两个API的结果"""
    overview = test_overview_api()
    comparison = test_comparison_api()
    
    if overview and comparison:
        print("\n" + "=" * 60)
        print("【差异分析】")
        print("=" * 60)
        
        profit_diff = overview.get('total_profit', 0) - comparison.get('total_profit', 0)
        sales_diff = overview.get('total_actual_sales', 0) - comparison.get('total_revenue', 0)
        orders_diff = overview.get('total_orders', 0) - comparison.get('order_count', 0)
        
        print(f"利润差异: ¥{profit_diff:,.2f}")
        print(f"销售额差异: ¥{sales_diff:,.2f}")
        print(f"订单数差异: {orders_diff}")
        
        if profit_diff != 0:
            print(f"\n⚠️ 两个TAB的利润计算不一致！")
            print(f"   经营总览: ¥{overview.get('total_profit'):,.2f}")
            print(f"   门店对比: ¥{comparison.get('total_profit'):,.2f}")


if __name__ == "__main__":
    compare_results()
