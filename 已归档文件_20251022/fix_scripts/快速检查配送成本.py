import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

# 加载数据
print("加载数据...")
df = pd.read_excel("测算模型/实际数据/W36-W37订单数据.xlsx")
print(f"数据行数: {len(df)}")

# 检查配送相关列是否存在
delivery_cols = ['配送费减免金额', '物流配送费', '用户支付配送费', '订单ID']
print("\n检查配送相关列:")
for col in delivery_cols:
    exists = "✓" if col in df.columns else "✗"
    print(f"  {exists} {col}")

if all(col in df.columns for col in delivery_cols):
    # 按订单聚合
    print("\n按订单聚合...")
    order_agg = df.groupby('订单ID').agg({
        '配送费减免金额': 'first',
        '物流配送费': 'first',
        '用户支付配送费': 'first'
    }).reset_index()
    
    # 计算两种配送成本
    order_agg['配送成本_新'] = order_agg['配送费减免金额'] + order_agg['物流配送费']
    order_agg['配送成本_旧'] = order_agg['用户支付配送费'] - order_agg['配送费减免金额'] - order_agg['物流配送费']
    
    print(f"\n📊 配送成本对比:")
    print(f"  新公式(正确): 配送费减免 + 物流配送费 = ¥{order_agg['配送成本_新'].sum():,.2f}")
    print(f"  旧公式(错误): 用户支付 - 配送费减免 - 物流配送费 = ¥{order_agg['配送成本_旧'].sum():,.2f}")
    print(f"  差异: ¥{abs(order_agg['配送成本_新'].sum() - order_agg['配送成本_旧'].sum()):,.2f}")
    
    # 验证 StandardBusinessLogic
    from standard_business_config import StandardBusinessLogic
    
    order_agg['配送成本_SBL'] = order_agg.apply(StandardBusinessLogic.calculate_delivery_cost, axis=1)
    print(f"\n  StandardBusinessLogic: ¥{order_agg['配送成本_SBL'].sum():,.2f}")
    
    if abs(order_agg['配送成本_SBL'].sum() - order_agg['配送成本_新'].sum()) < 0.01:
        print("  ✅ StandardBusinessLogic 使用的是新公式(正确)")
    else:
        print("  ❌ StandardBusinessLogic 使用的是旧公式(错误)")
else:
    print("\n❌ 数据文件缺少必需列")
    print(f"\n可用列: {df.columns.tolist()}")
