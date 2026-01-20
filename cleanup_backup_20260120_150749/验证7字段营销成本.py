"""
验证React版本对齐Dash版本后的营销成本计算
使用7个营销字段（剔除配送费减免金额）
"""
import requests
import json

BASE_URL = "http://localhost:8080"
TEST_STORE = "惠宜选-泰州泰兴店"
START_DATE = "2026-01-12"
END_DATE = "2026-01-18"

print("=" * 100)
print("验证React版本对齐Dash版本后的营销成本计算")
print("=" * 100)
print()

print("📋 营销成本字段（7个，对齐Dash版本）:")
print("-" * 100)
print("  1. 满减金额")
print("  2. 商品减免金额")
print("  3. 商家代金券")
print("  4. 商家承担部分券")
print("  5. 满赠金额")
print("  6. 商家其他优惠")
print("  7. 新客减免金额")
print()
print("  ❌ 配送费减免金额 - 已剔除（属于配送成本，不属于营销成本）")
print()

print(f"测试门店: {TEST_STORE}")
print(f"测试日期: {START_DATE} 至 {END_DATE}")
print()

# 1. 清除缓存
print("步骤1: 清除缓存...")
try:
    response = requests.post(f"{BASE_URL}/api/v1/orders/clear-cache")
    if response.status_code == 200:
        print("✅ 缓存清除成功")
    else:
        print(f"⚠️ 缓存清除失败: {response.status_code}")
except Exception as e:
    print(f"⚠️ 缓存清除异常: {e}")
print()

# 2. 测试渠道对比API
print("步骤2: 测试渠道对比API...")
try:
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
            
            print("✅ API响应成功")
            print()
            
            # Dash版本的预期值
            dash_values = {
                "饿了么": {"avg_marketing": 5.58, "avg_delivery": 1.61},
                "美团共橙": {"avg_marketing": 5.19, "avg_delivery": 3.89}
            }
            
            print(f"{'渠道':<20} {'订单数':>10} {'React单均营销':>15} {'Dash单均营销':>15} {'差异%':>10} {'状态':<10}")
            print("-" * 100)
            
            all_passed = True
            for channel_info in channels_data:
                channel = channel_info.get('channel', 'Unknown')
                if channel in dash_values:
                    current = channel_info.get('current', {})
                    order_count = current.get('order_count', 0)
                    react_marketing = current.get('avg_marketing_per_order', 0)
                    dash_marketing = dash_values[channel]['avg_marketing']
                    
                    diff_pct = ((react_marketing - dash_marketing) / dash_marketing * 100) if dash_marketing > 0 else 0
                    
                    # 允许5%的误差
                    passed = abs(diff_pct) <= 5
                    status = "✅ 通过" if passed else "❌ 失败"
                    
                    print(f"{channel:<20} {order_count:>10} ¥{react_marketing:>13.2f} ¥{dash_marketing:>13.2f} {diff_pct:>9.1f}% {status:<10}")
                    
                    if not passed:
                        all_passed = False
            
            print("-" * 100)
            print()
            
            if all_passed:
                print("🎉 所有测试通过！React版本已成功对齐Dash版本！")
                print()
                print("✅ 营销成本计算一致性验证通过")
                print("✅ 两个版本使用相同的7个营销字段")
            else:
                print("⚠️ 部分测试失败")
                print()
                print("可能的原因:")
                print("1. 后端服务未重启，仍在使用旧代码")
                print("2. 缓存未完全清除")
                print("3. 数据源不一致")
                print()
                print("建议操作:")
                print("1. 重启后端服务")
                print("2. 再次运行此测试脚本")
            
        else:
            print("❌ API返回数据格式错误")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"❌ API请求失败: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ 测试异常: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 100)
print("测试完成")
print("=" * 100)
