"""
详细查看API返回的数据，特别是营销成本相关字段
"""
import requests
import json

BASE_URL = "http://localhost:8080"
TEST_STORE = "惠宜选-泰州泰兴店"
START_DATE = "2026-01-12"
END_DATE = "2026-01-18"

print("=" * 100)
print("详细查看API返回数据")
print("=" * 100)
print()

# 清除缓存
print("清除缓存...")
requests.post(f"{BASE_URL}/api/v1/orders/clear-cache")
print()

# 测试渠道对比API
params = {
    "store_name": TEST_STORE,
    "start_date": START_DATE,
    "end_date": END_DATE
}

response = requests.get(
    f"{BASE_URL}/api/v1/orders/channel-comparison",
    params=params
)

if response.status_code == 200:
    data = response.json()
    
    if data.get('success') and data.get('data'):
        channels_data = data['data']
        
        for channel_info in channels_data:
            channel = channel_info.get('channel', 'Unknown')
            
            if channel in ['饿了么', '美团共橙']:
                print(f"{'=' * 100}")
                print(f"渠道: {channel}")
                print(f"{'=' * 100}")
                
                current = channel_info.get('current', {})
                
                print(f"\n基础指标:")
                print(f"  订单数: {current.get('order_count', 0)}")
                print(f"  销售额: ¥{current.get('amount', 0):.2f}")
                print(f"  利润: ¥{current.get('profit', 0):.2f}")
                print(f"  客单价: ¥{current.get('avg_value', 0):.2f}")
                print(f"  利润率: {current.get('profit_rate', 0):.2f}%")
                
                print(f"\n成本结构:")
                print(f"  商品成本: ¥{current.get('product_cost', 0):.2f} ({current.get('product_cost_rate', 0):.2f}%)")
                print(f"  耗材成本: ¥{current.get('consumable_cost', 0):.2f} ({current.get('consumable_cost_rate', 0):.2f}%)")
                print(f"  商品减免: ¥{current.get('product_discount', 0):.2f} ({current.get('product_discount_rate', 0):.2f}%)")
                print(f"  活动补贴: ¥{current.get('activity_subsidy', 0):.2f} ({current.get('activity_subsidy_rate', 0):.2f}%)")
                print(f"  配送成本: ¥{current.get('delivery_cost', 0):.2f} ({current.get('delivery_cost_rate', 0):.2f}%)")
                print(f"  平台服务费: ¥{current.get('platform_fee', 0):.2f} ({current.get('platform_fee_rate', 0):.2f}%)")
                print(f"  总成本率: {current.get('total_cost_rate', 0):.2f}%")
                
                print(f"\n单均经济:")
                print(f"  单均利润: ¥{current.get('avg_profit_per_order', 0):.2f}")
                print(f"  单均营销: ¥{current.get('avg_marketing_per_order', 0):.2f}")  # 关键指标
                print(f"  单均配送: ¥{current.get('avg_delivery_per_order', 0):.2f}")
                
                print()
        
        print("=" * 100)
        print("对比Dash版本预期值:")
        print("=" * 100)
        print(f"饿了么: 单均营销 ¥5.58, 单均配送 ¥1.61")
        print(f"美团共橙: 单均营销 ¥5.19, 单均配送 ¥3.89")
        
    else:
        print("❌ API返回数据格式错误")
        print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print(f"❌ API请求失败: {response.status_code}")
    print(response.text)

print()
print("=" * 100)
