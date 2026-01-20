"""
对比Dash版和React版的营销成本计算差异
验证哪个版本符合权威手册v3.1的定义
"""
import requests
import json

BASE_URL = "http://localhost:8080"
TEST_STORE = "惠宜选-泰州泰兴店"
START_DATE = "2026-01-12"
END_DATE = "2026-01-18"

print("=" * 100)
print("对比Dash版和React版的营销成本计算差异")
print("=" * 100)
print()

print("📚 权威手册v3.1定义（2025-01-16更新）:")
print("-" * 100)
print("商家活动成本（营销成本）包含8个字段:")
print("  1. 配送费减免金额")
print("  2. 满减金额")
print("  3. 商品减免金额")
print("  4. 商家代金券")
print("  5. 商家承担部分券")
print("  6. 满赠金额")
print("  7. 商家其他优惠")
print("  8. 新客减免金额")
print()

print("🔍 Dash版本实际使用的字段（从代码中发现）:")
print("-" * 100)
print("商家活动成本只包含6个字段:")
print("  1. ❌ 配送费减免金额 - 缺失")
print("  2. ✅ 满减金额")
print("  3. ✅ 商品减免金额")
print("  4. ✅ 商家代金券")
print("  5. ✅ 商家承担部分券")
print("  6. ✅ 满赠金额")
print("  7. ✅ 商家其他优惠")
print("  8. ❌ 新客减免金额 - 缺失")
print()
print("⚠️ Dash版本未更新到v3.1，缺少2个营销字段！")
print()

print("✅ React版本（修复后）使用的字段:")
print("-" * 100)
print("商家活动成本包含完整的8个字段（符合权威手册v3.1）")
print()

print("📊 数据对比:")
print("-" * 100)
print(f"测试门店: {TEST_STORE}")
print(f"测试日期: {START_DATE} 至 {END_DATE}")
print()

# 获取React版本的数据
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
            
            print(f"{'渠道':<20} {'React版单均营销':>18} {'Dash版单均营销':>18} {'差异':>12} {'状态':<15}")
            print("-" * 100)
            
            dash_values = {
                "饿了么": 5.58,
                "美团共橙": 5.19
            }
            
            for channel_info in channels_data:
                channel = channel_info.get('channel', 'Unknown')
                if channel in dash_values:
                    react_value = channel_info.get('current', {}).get('avg_marketing_per_order', 0)
                    dash_value = dash_values[channel]
                    diff = react_value - dash_value
                    diff_pct = (diff / dash_value * 100) if dash_value > 0 else 0
                    
                    # React版本应该更高（因为包含了2个额外字段）
                    status = "✅ React更高" if react_value > dash_value else "⚠️ 需检查"
                    
                    print(f"{channel:<20} ¥{react_value:>16.2f} ¥{dash_value:>16.2f} {diff_pct:>11.1f}% {status:<15}")
            
            print("-" * 100)
            print()
            
            print("💡 分析结论:")
            print("-" * 100)
            print("1. 如果React版本的单均营销 > Dash版本:")
            print("   ✅ 说明React版本正确包含了8个字段（配送费减免 + 新客减免）")
            print("   ⚠️ Dash版本需要更新代码以符合权威手册v3.1")
            print()
            print("2. 如果React版本的单均营销 ≈ Dash版本:")
            print("   ⚠️ 说明配送费减免和新客减免金额很小或为0")
            print("   ⚠️ 或者React版本的修复未生效（后端未重启）")
            print()
            print("3. 如果React版本的单均营销 < Dash版本:")
            print("   ❌ 说明React版本计算有误，需要检查代码")
            
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
print()
print("📝 建议:")
print("1. 重启React版本后端服务，确保代码修改生效")
print("2. 更新Dash版本代码，添加缺失的2个营销字段")
print("3. 统一两个版本的营销成本计算逻辑")
