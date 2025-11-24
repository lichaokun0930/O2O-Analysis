"""
验证用户提供的计算逻辑
"""
import pandas as pd

# 加载数据
df = pd.read_excel('实际数据/枫瑞.xlsx')
if '一级分类名' in df.columns:
    df = df[df['一级分类名'] != '耗材'].copy()

mt_data = df[df['渠道'] == '美团共橙'].copy()

# 手工聚合
order_agg = mt_data.groupby('订单ID').agg({
    '利润额': 'sum',
    '物流配送费': 'first',
    '平台服务费': 'sum',
    '企客后返': 'sum'
}).reset_index()

print("=" * 80)
print("验证用户的计算逻辑")
print("=" * 80)

# 过滤平台服务费>0
filtered = order_agg[order_agg['平台服务费'] > 0].copy()

print(f"\n过滤后(平台服务费>0):")
print(f"  订单数: {len(filtered)}")
print(f"  利润额: {filtered['利润额'].sum():.2f}")
print(f"  物流配送费: {filtered['物流配送费'].sum():.2f}")
print(f"  平台服务费: {filtered['平台服务费'].sum():.2f}")
print(f"  企客后返: {filtered['企客后返'].sum():.2f}")

result = (
    filtered['利润额'].sum() - 
    filtered['物流配送费'].sum() - 
    filtered['平台服务费'].sum() + 
    filtered['企客后返'].sum()
)

print(f"\n计算:")
print(f"  {filtered['利润额'].sum():.2f} - {filtered['物流配送费'].sum():.2f} - {filtered['平台服务费'].sum():.2f} + {filtered['企客后返'].sum():.2f}")
print(f"  = {result:.2f}")

print("\n" + "=" * 80)
