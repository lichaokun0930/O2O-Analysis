# -*- coding: utf-8 -*-
"""
测试GMV API - 强制使用原始查询
"""

import requests

BASE_URL = "http://localhost:8080/api/v1"
STORE_NAME = "惠宜选超市（昆山淀山湖镇店）"
START_DATE = "2026-01-18"
END_DATE = "2026-01-18"

def test_overview_api():
    """测试overview API是否返回GMV和营销成本率"""
    print("=" * 70)
    print("测试 /orders/overview API (强制使用原始查询)")
    print("=" * 70)
    
    params = {
        "store_name": STORE_NAME,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "use_aggregation": False  # 强制使用原始查询
    }
    
    try:
        response = requests.get(f"{BASE_URL}/orders/overview", params=params)
        
        print(f"\n请求URL: {response.url}")
        print(f"HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n完整响应:")
            import json
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get("success"):
                result = data.get("data", {})
                print(f"\n" + "=" * 70)
                print("解析结果:")
                print("=" * 70)
                print(f"  订单总数: {result.get('total_orders')}")
                print(f"  商品实收额: ¥{result.get('total_actual_sales', 0):,.2f}")
                print(f"  总利润: ¥{result.get('total_profit', 0):,.2f}")
                print(f"  平均客单价: ¥{result.get('avg_order_value', 0):.2f}")
                print(f"  总利润率: {result.get('profit_rate', 0):.2f}%")
                print(f"  动销商品数: {result.get('active_products')}")
                
                gmv = result.get('gmv')
                marketing_cost = result.get('marketing_cost')
                marketing_cost_rate = result.get('marketing_cost_rate')
                
                print(f"\n  🆕 GMV(营业额): {'¥' + str(gmv) if gmv is not None else 'N/A'}")
                print(f"  🆕 营销成本: {'¥' + str(marketing_cost) if marketing_cost is not None else 'N/A'}")
                print(f"  🆕 营销成本率: {str(marketing_cost_rate) + '%' if marketing_cost_rate is not None else 'N/A'}")
                
                # 验证新字段是否存在
                if gmv is not None and marketing_cost_rate is not None:
                    print(f"\n✅ GMV和营销成本率字段已正确返回")
                else:
                    print(f"\n❌ 缺少GMV或营销成本率字段")
                    print(f"   gmv: {gmv}")
                    print(f"   marketing_cost: {marketing_cost}")
                    print(f"   marketing_cost_rate: {marketing_cost_rate}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(response.text)
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到后端服务 ({BASE_URL})")
        print("请确保后端服务已启动")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_overview_api()
