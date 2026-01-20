"""
验证单均营销修复效果
测试React版API是否正确计算单均营销（包含8个营销字段）
"""
import requests
import json
from datetime import datetime

# API配置
BASE_URL = "http://localhost:8080"
TEST_STORE = "惠宜选-泰州泰兴店"
START_DATE = "2026-01-12"
END_DATE = "2026-01-18"

print("=" * 80)
print("验证单均营销修复效果")
print("=" * 80)
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

# 2. 测试渠道环比对比API
print("步骤2: 测试渠道环比对比API...")
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
        print(f"✅ API响应成功")
        print(f"返回数据条数: {len(data)}")
        print()
        
        # 显示各渠道的单均营销和单均配送
        print("各渠道数据对比:")
        print("-" * 80)
        print(f"{'渠道':<20} {'订单数':>10} {'单均营销':>12} {'单均配送':>12}")
        print("-" * 80)
        
        for channel_data in data:
            channel = channel_data.get('channel', 'Unknown')
            current = channel_data.get('current', {})
            
            order_count = current.get('order_count', 0)
            avg_marketing = current.get('avg_marketing_cost', 0)
            avg_delivery = current.get('avg_delivery_fee', 0)
            
            print(f"{channel:<20} {order_count:>10} {avg_marketing:>12.2f} {avg_delivery:>12.2f}")
        
        print("-" * 80)
        print()
        
        # 3. 与预期值对比
        print("步骤3: 与Dash版本对比...")
        print("-" * 80)
        
        expected_values = {
            "饿了么": {"avg_marketing": 7.87, "avg_delivery": 1.61},
            "美团共橙": {"avg_marketing": 10.17, "avg_delivery": 3.89}
        }
        
        print(f"{'渠道':<20} {'指标':<15} {'React版':>12} {'Dash版':>12} {'差异':>12} {'状态':<10}")
        print("-" * 80)
        
        all_passed = True
        for channel_data in data:
            channel = channel_data.get('channel', 'Unknown')
            if channel in expected_values:
                current = channel_data.get('current', {})
                
                # 检查单均营销
                actual_marketing = current.get('avg_marketing_cost', 0)
                expected_marketing = expected_values[channel]['avg_marketing']
                diff_marketing = actual_marketing - expected_marketing
                diff_pct_marketing = (diff_marketing / expected_marketing * 100) if expected_marketing > 0 else 0
                
                # 允许5%的误差
                marketing_passed = abs(diff_pct_marketing) <= 5
                status_marketing = "✅ 通过" if marketing_passed else "❌ 失败"
                
                print(f"{channel:<20} {'单均营销':<15} {actual_marketing:>12.2f} {expected_marketing:>12.2f} {diff_pct_marketing:>11.1f}% {status_marketing:<10}")
                
                # 检查单均配送
                actual_delivery = current.get('avg_delivery_fee', 0)
                expected_delivery = expected_values[channel]['avg_delivery']
                diff_delivery = actual_delivery - expected_delivery
                diff_pct_delivery = (diff_delivery / expected_delivery * 100) if expected_delivery > 0 else 0
                
                delivery_passed = abs(diff_pct_delivery) <= 5
                status_delivery = "✅ 通过" if delivery_passed else "❌ 失败"
                
                print(f"{channel:<20} {'单均配送':<15} {actual_delivery:>12.2f} {expected_delivery:>12.2f} {diff_pct_delivery:>11.1f}% {status_delivery:<10}")
                
                if not (marketing_passed and delivery_passed):
                    all_passed = False
        
        print("-" * 80)
        print()
        
        if all_passed:
            print("🎉 所有测试通过！单均营销修复成功！")
        else:
            print("⚠️ 部分测试失败，需要进一步检查")
            print()
            print("可能的原因:")
            print("1. 后端服务未重启，仍在使用旧代码")
            print("2. 缓存未完全清除")
            print("3. 数据库中的原始数据有问题")
            print()
            print("建议操作:")
            print("1. 重启后端服务: python backend/app/main.py")
            print("2. 再次运行此测试脚本")
        
    else:
        print(f"❌ API请求失败: {response.status_code}")
        print(f"错误信息: {response.text}")
        
except Exception as e:
    print(f"❌ 测试异常: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("测试完成")
print("=" * 80)
