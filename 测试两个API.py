# -*- coding: utf-8 -*-
"""
测试两个API的实际返回值
"""

import requests

API_BASE = "http://localhost:8000/api/v1"
STORE_NAME = "惠宜选-泰州兴化店"
START_DATE = "2026-01-16"
END_DATE = "2026-01-22"

def test_overview_api():
    """测试经营总览API"""
    print("\n" + "=" * 60)
    print("【经营总览TAB】/orders/overview")
    print("=" * 60)
    
    params = {
        "store_name": STORE_NAME,
        "start_date": START_DATE,
        "end_date": END_DATE
    }
    
    try:
        resp = requests.get(f"{API_BASE}/orders/overview", params=params, timeout=30)
        print(f"状态码: {resp.status_code}")
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
                print(f"API返回失败: {data}")
        else:
            print(f"HTTP错误: {resp.text}")
    except Exception as e:
        print(f"请求异常: {e}")
    
    return None


def test_comparison_api():
    """测试全量门店对比API"""
    print("\n" + "=" * 60)
    print("【全量门店对比TAB】/stores/comparison")
    print("=" * 60)
    
    params = {
        "start_date": START_DATE,
        "end_date": END_DATE
    }
    
    try:
        resp = requests.get(f"{API_BASE}/stores/comparison", params=params, timeout=30)
        print(f"状态码: {resp.status_code}")
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
                    print(f"未找到门店: {STORE_NAME}")
                    print(f"可用门店: {[s['store_name'] for s in stores[:5]]}")
            else:
                print(f"API返回失败: {data}")
        else:
            print(f"HTTP错误: {resp.text}")
    except Exception as e:
        print(f"请求异常: {e}")
    
    return None


if __name__ == "__main__":
    print(f"测试参数: 门店={STORE_NAME}, 日期={START_DATE}~{END_DATE}")
    
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
