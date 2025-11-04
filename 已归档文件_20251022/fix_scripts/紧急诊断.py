"""紧急诊断配送成本计算"""
import sys
sys.path.insert(0, r'd:\Python1\O2O_Analysis\O2O数据分析')

# 强制重新加载
if 'standard_business_config' in sys.modules:
    del sys.modules['standard_business_config']

from standard_business_config import StandardBusinessLogic
import pandas as pd

# 测试数据
test = pd.Series({
    '配送费减免金额': 10.0,
    '物流配送费': 5.0,
    '用户支付配送费': 3.0
})

result = StandardBusinessLogic.calculate_delivery_cost(test)

print(f"配送费减免: {test['配送费减免金额']}")
print(f"物流配送费: {test['物流配送费']}")
print(f"用户支付配送费: {test['用户支付配送费']}")
print(f"\n计算结果: {result}")
print(f"期望结果: {test['配送费减免金额'] + test['物流配送费']}")

if abs(result - 15.0) < 0.01:
    print("\n✅ 配送成本公式正确")
else:
    print(f"\n❌ 配送成本公式错误，差异: {abs(result - 15.0)}")
