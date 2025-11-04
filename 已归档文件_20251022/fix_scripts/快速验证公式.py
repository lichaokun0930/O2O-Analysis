"""快速验证配送成本公式"""
import sys
sys.path.insert(0, r'd:\Python1\O2O_Analysis\O2O数据分析')

# 强制重新加载模块
if 'standard_business_config' in sys.modules:
    del sys.modules['standard_business_config']

from standard_business_config import StandardBusinessLogic
import pandas as pd

print("="*80)
print(" " * 25 + "配送成本公式验证")
print("="*80)

# 创建测试订单（模拟您提供的数据）
test_data = {
    '订单ID': 'TEST001',
    '配送费减免金额': 10.0,   # 假设值
    '物流配送费': 5.0,         # 假设值
    '用户支付配送费': 3.0      # 假设值
}

test_order = pd.Series(test_data)

print(f"\n📦 测试数据:")
print(f"   配送费减免金额: ¥{test_order['配送费减免金额']:.2f}")
print(f"   物流配送费: ¥{test_order['物流配送费']:.2f}")
print(f"   用户支付配送费: ¥{test_order['用户支付配送费']:.2f}")

# 调用 StandardBusinessLogic 计算配送成本
delivery_cost = StandardBusinessLogic.calculate_delivery_cost(test_order)

print(f"\n🔧 StandardBusinessLogic.calculate_delivery_cost() 返回:")
print(f"   配送成本 = ¥{delivery_cost:.2f}")

# 手动计算两种公式
新公式结果 = test_order['配送费减免金额'] + test_order['物流配送费']
旧公式结果 = test_order['用户支付配送费'] - test_order['配送费减免金额'] - test_order['物流配送费']

print(f"\n📐 公式对比:")
print(f"\n   ✅ 新公式(正确): 配送费减免 + 物流配送费")
print(f"      = {test_order['配送费减免金额']:.2f} + {test_order['物流配送费']:.2f}")
print(f"      = ¥{新公式结果:.2f}")

print(f"\n   ❌ 旧公式(错误): 用户支付 - 配送费减免 - 物流配送费")
print(f"      = {test_order['用户支付配送费']:.2f} - {test_order['配送费减免金额']:.2f} - {test_order['物流配送费']:.2f}")
print(f"      = ¥{旧公式结果:.2f}")

print(f"\n" + "="*80)
print(f"🔍 判断结果:")
print(f"="*80)

if abs(delivery_cost - 新公式结果) < 0.01:
    print(f"\n✅ StandardBusinessLogic 使用的是 【新公式(正确)】")
    print(f"   配送成本 = 配送费减免 + 物流配送费")
    print(f"   这是商家在配送环节的实际支出")
elif abs(delivery_cost - 旧公式结果) < 0.01:
    print(f"\n❌ StandardBusinessLogic 使用的是 【旧公式(错误)】")
    print(f"   配送成本 = 用户支付 - 配送费减免 - 物流配送费")
    print(f"   这会导致利润计算错误！")
else:
    print(f"\n⚠️ StandardBusinessLogic 使用的是 【未知公式】")
    print(f"   返回值: {delivery_cost:.2f}")
    print(f"   与新公式差异: {abs(delivery_cost - 新公式结果):.2f}")
    print(f"   与旧公式差异: {abs(delivery_cost - 旧公式结果):.2f}")

# 测试利润计算
print(f"\n" + "="*80)
print(f"💰 利润计算测试")
print(f"="*80)

# 添加更多测试数据
test_order['商品实售价总和'] = 100.0
test_order['打包费'] = 1.0
test_order['成本'] = 60.0
test_order['活动营销成本'] = 5.0
test_order['商品折扣成本'] = 3.0
test_order['平台佣金'] = 8.0

# 计算订单总收入
revenue = StandardBusinessLogic.calculate_estimated_order_revenue(test_order)
print(f"\n订单总收入:")
print(f"   = 商品实售价 + 打包费 + 用户支付配送费")
print(f"   = {test_order['商品实售价总和']:.2f} + {test_order['打包费']:.2f} + {test_order['用户支付配送费']:.2f}")
print(f"   = ¥{revenue:.2f}")

# 计算各项成本
print(f"\n各项成本:")
print(f"   商品成本: ¥{test_order['成本']:.2f}")
print(f"   配送成本: ¥{delivery_cost:.2f}")
print(f"   活动营销成本: ¥{test_order['活动营销成本']:.2f}")
print(f"   商品折扣成本: ¥{test_order['商品折扣成本']:.2f}")
print(f"   平台佣金: ¥{test_order['平台佣金']:.2f}")

total_cost = (test_order['成本'] + delivery_cost + test_order['活动营销成本'] + 
              test_order['商品折扣成本'] + test_order['平台佣金'])
print(f"   总成本: ¥{total_cost:.2f}")

# 计算利润
profit = StandardBusinessLogic.calculate_actual_order_profit(test_order)
manual_profit = revenue - total_cost

print(f"\n利润计算:")
print(f"   StandardBusinessLogic: ¥{profit:.2f}")
print(f"   手动计算: ¥{manual_profit:.2f}")
print(f"   差异: ¥{abs(profit - manual_profit):.2f}")

if abs(profit - manual_profit) < 0.01:
    print(f"\n✅ 利润计算正确")
else:
    print(f"\n❌ 利润计算有误")

print(f"\n" + "="*80)
print(f"✅ 验证完成")
print(f"="*80)

print(f"\n📋 结论:")
print(f"   如果上述显示使用的是【新公式(正确)】，")
print(f"   说明 standard_business_config.py 的配送成本公式已正确修复。")
print(f"   ")
print(f"   如果看板显示的利润仍然不对，可能的原因:")
print(f"   1. 浏览器缓存：请按 Ctrl+Shift+R 强制刷新")
print(f"   2. Streamlit 缓存：请重新上传数据文件")
print(f"   3. 数据文件列名不匹配：请检查 Excel 文件的列名")
