"""验证配送成本公式是否生效"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 创建测试数据
import pandas as pd
from standard_business_config import StandardBusinessLogic, create_order_level_summary, apply_standard_business_logic, StandardBusinessConfig

# 测试单个订单的配送成本计算
test_order = pd.Series({
    '订单ID': 'TEST001',
    '配送费减免金额': 5.0,
    '物流配送费': 3.0,
    '用户支付配送费': 2.0,
    '商品实售价总和': 100.0,
    '打包费': 1.0,
    '成本': 50.0,
    '活动营销成本': 10.0,
    '商品折扣成本': 5.0,
    '平台佣金': 8.0
})

print("="*80)
print("测试配送成本计算公式")
print("="*80)

# 计算配送成本
delivery_cost = StandardBusinessLogic.calculate_delivery_cost(test_order)
print(f"\n📦 配送成本相关字段:")
print(f"  配送费减免金额: ¥{test_order['配送费减免金额']:.2f}")
print(f"  物流配送费: ¥{test_order['物流配送费']:.2f}")
print(f"  用户支付配送费: ¥{test_order['用户支付配送费']:.2f}")

print(f"\n🔹 StandardBusinessLogic.calculate_delivery_cost 计算结果:")
print(f"  配送成本 = ¥{delivery_cost:.2f}")

# 手动计算两种公式
new_formula = test_order['配送费减免金额'] + test_order['物流配送费']
old_formula = test_order['用户支付配送费'] - test_order['配送费减免金额'] - test_order['物流配送费']

print(f"\n🔹 新公式(正确): 配送费减免 + 物流配送费")
print(f"  = {test_order['配送费减免金额']:.2f} + {test_order['物流配送费']:.2f}")
print(f"  = ¥{new_formula:.2f}")

print(f"\n🔹 旧公式(错误): 用户支付 - 配送费减免 - 物流配送费")
print(f"  = {test_order['用户支付配送费']:.2f} - {test_order['配送费减免金额']:.2f} - {test_order['物流配送费']:.2f}")
print(f"  = ¥{old_formula:.2f}")

# 判断使用的哪个公式
if abs(delivery_cost - new_formula) < 0.01:
    print(f"\n✅ StandardBusinessLogic 使用的是 新公式(正确)")
elif abs(delivery_cost - old_formula) < 0.01:
    print(f"\n❌ StandardBusinessLogic 使用的是 旧公式(错误)")
else:
    print(f"\n⚠️ StandardBusinessLogic 使用的是 未知公式")

# 计算订单总收入和利润
revenue = StandardBusinessLogic.calculate_estimated_order_revenue(test_order)
profit = StandardBusinessLogic.calculate_actual_order_profit(test_order)

print(f"\n" + "="*80)
print("完整利润计算验证")
print("="*80)

print(f"\n📊 订单总收入:")
print(f"  = 商品实售价 + 打包费 + 用户支付配送费")
print(f"  = {test_order['商品实售价总和']:.2f} + {test_order['打包费']:.2f} + {test_order['用户支付配送费']:.2f}")
print(f"  = ¥{revenue:.2f}")

print(f"\n📊 各项成本:")
print(f"  商品成本: ¥{test_order['成本']:.2f}")
print(f"  配送成本: ¥{delivery_cost:.2f}")
print(f"  活动营销成本: ¥{test_order['活动营销成本']:.2f}")
print(f"  商品折扣成本: ¥{test_order['商品折扣成本']:.2f}")
print(f"  平台佣金: ¥{test_order['平台佣金']:.2f}")

total_cost = test_order['成本'] + delivery_cost + test_order['活动营销成本'] + test_order['商品折扣成本'] + test_order['平台佣金']
print(f"\n  总成本: ¥{total_cost:.2f}")

print(f"\n📊 利润计算:")
print(f"  = 订单总收入 - 总成本")
print(f"  = {revenue:.2f} - {total_cost:.2f}")
print(f"  = ¥{profit:.2f}")

# 验证与函数返回值是否一致
manual_profit = revenue - total_cost
if abs(profit - manual_profit) < 0.01:
    print(f"\n✅ 利润计算正确")
else:
    print(f"\n❌ 利润计算错误 (函数返回: {profit:.2f}, 手动计算: {manual_profit:.2f})")

# 比较使用新旧配送成本公式对利润的影响
profit_new = revenue - (test_order['成本'] + new_formula + test_order['活动营销成本'] + test_order['商品折扣成本'] + test_order['平台佣金'])
profit_old = revenue - (test_order['成本'] + old_formula + test_order['活动营销成本'] + test_order['商品折扣成本'] + test_order['平台佣金'])

print(f"\n" + "="*80)
print("配送成本公式对利润的影响")
print("="*80)
print(f"\n使用新公式，利润 = ¥{profit_new:.2f}")
print(f"使用旧公式，利润 = ¥{profit_old:.2f}")
print(f"差异 = ¥{abs(profit_new - profit_old):.2f}")

if abs(profit - profit_new) < 0.01:
    print(f"\n✅ 当前使用的是新公式(正确)")
elif abs(profit - profit_old) < 0.01:
    print(f"\n❌ 当前使用的是旧公式(错误)")

print(f"\n" + "="*80)
print("✅ 验证完成")
print("="*80)
