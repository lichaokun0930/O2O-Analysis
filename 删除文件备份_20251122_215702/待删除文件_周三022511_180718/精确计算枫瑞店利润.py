"""
精确计算枫瑞店总利润
"""
import pandas as pd
import numpy as np

print("=" * 80)
print("枫瑞店总利润精确计算")
print("=" * 80)

# 读取数据
df = pd.read_excel('实际数据/枫瑞.xlsx')
print(f"\n✅ 数据行数: {len(df)}")
print(f"✅ 订单数: {df['订单ID'].nunique()}")

# 显示所有可能的利润相关字段
print(f"\n📋 利润相关字段:")
profit_related = [col for col in df.columns if '利润' in col or '收入' in col or '成本' in col]
for col in profit_related:
    print(f"  - {col}")

print("\n" + "=" * 80)
print("方法1: 直接汇总利润额字段")
print("=" * 80)

if '利润额' in df.columns:
    total_profit_raw = df['利润额'].sum()
    print(f"\n利润额字段直接求和: {total_profit_raw:,.2f}")
    
    # 按订单汇总后再求和
    order_profit = df.groupby('订单ID')['利润额'].sum()
    total_profit_by_order = order_profit.sum()
    print(f"按订单汇总后求和: {total_profit_by_order:,.2f}")
    
    print(f"\n两种方法结果{'一致 ✅' if abs(total_profit_raw - total_profit_by_order) < 0.01 else '不一致 ❌'}")

print("\n" + "=" * 80)
print("方法2: 手动计算 (售价 - 成本) × 销量")
print("=" * 80)

if '商品实售价' in df.columns and '成本' in df.columns and '销量' in df.columns:
    # 计算每行的毛利
    df_calc = df.copy()
    df_calc['单行毛利'] = (df_calc['商品实售价'] - df_calc['成本']) * df_calc['销量']
    total_margin = df_calc['单行毛利'].sum()
    print(f"\n手动计算毛利: {total_margin:,.2f}")
    
    # 对比利润额字段
    if '利润额' in df.columns:
        diff = total_margin - df['利润额'].sum()
        print(f"与利润额字段差异: {diff:,.2f}")

print("\n" + "=" * 80)
print("方法3: 检查是否有其他利润字段")
print("=" * 80)

# 检查预计订单收入等字段
if '预计订单收入' in df.columns:
    # 按订单汇总预计订单收入
    order_revenue = df.groupby('订单ID')['预计订单收入'].first().sum()
    print(f"\n预计订单收入总和: {order_revenue:,.2f}")

if '实收价格' in df.columns:
    order_actual = df.groupby('订单ID')['实收价格'].first().sum()
    print(f"实收价格总和: {order_actual:,.2f}")

print("\n" + "=" * 80)
print("方法4: 完整的订单实际利润计算")
print("=" * 80)

# 按订单聚合
order_agg = df.groupby('订单ID').agg({
    '利润额': 'sum',
    '平台服务费': 'sum',
    '物流配送费': 'sum',
    '企客后返': 'sum'
}).reset_index()

print(f"\n各项汇总:")
print(f"  利润额总和: {order_agg['利润额'].sum():,.2f}")
print(f"  平台服务费总和: {order_agg['平台服务费'].sum():,.2f}")
print(f"  物流配送费总和: {order_agg['物流配送费'].sum():,.2f}")
print(f"  企客后返总和: {order_agg['企客后返'].sum():,.2f}")

# 计算订单实际利润(未过滤)
order_agg['订单实际利润_未过滤'] = (
    order_agg['利润额'] - 
    order_agg['平台服务费'] - 
    order_agg['物流配送费'] + 
    order_agg['企客后返']
)

total_actual_profit_unfiltered = order_agg['订单实际利润_未过滤'].sum()
print(f"\n订单实际利润(未过滤): {total_actual_profit_unfiltered:,.2f}")
print(f"  = 利润额 - 平台服务费 - 物流配送费 + 企客后返")
print(f"  = {order_agg['利润额'].sum():,.2f} - {order_agg['平台服务费'].sum():,.2f} - {order_agg['物流配送费'].sum():,.2f} + {order_agg['企客后返'].sum():,.2f}")

print("\n" + "=" * 80)
print("关键问题: 您说的总利润62372是指哪个数值?")
print("=" * 80)

print(f"""
请确认您说的"总利润62372"是指以下哪个数值:

A. 利润额字段直接求和 = {df['利润额'].sum() if '利润额' in df.columns else 'N/A':,.2f}
B. 订单实际利润(利润额-平台费-物流费+后返) = {total_actual_profit_unfiltered:,.2f}
C. 其他计算方式?

如果是 {df['利润额'].sum() if '利润额' in df.columns else 0:,.2f}，那确实接近您说的62372!
""")

print("=" * 80)
