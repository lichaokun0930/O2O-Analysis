"""
验证美团闪购利润计算差异
对比主看板和下钻页面的计算逻辑
"""
import pandas as pd
from pathlib import Path

# 加载数据
data_file = Path("订单数据_2024-11-01至2024-11-07.xlsx")
if not data_file.exists():
    print("❌ 数据文件不存在,请确保'订单数据_2024-11-01至2024-11-07.xlsx'在当前目录")
    exit(1)

print("="*80)
print("🔍 验证美团闪购利润计算")
print("="*80)

# 读取数据
df = pd.read_excel(data_file)
print(f"\n📊 原始数据: {len(df):,} 行")

# 只看美团闪购渠道
df_mt = df[df['渠道'] == '美团闪购'].copy()
print(f"📊 美团闪购数据: {len(df_mt):,} 行")
print(f"📊 订单数: {df_mt['订单ID'].nunique():,}")

# 方法1: 简单聚合(可能错误)
print(f"\n{'='*80}")
print("方法1: 简单聚合(直接sum商品级字段)")
print("="*80)

simple_profit = df_mt['利润额'].sum()
simple_service_fee = df_mt['平台服务费'].sum()
simple_delivery = df_mt['物流配送费'].sum()
simple_enterprise = df_mt['企客后返'].sum() if '企客后返' in df_mt.columns else 0

simple_actual_profit = simple_profit - simple_service_fee - simple_delivery + simple_enterprise

print(f"利润额: ¥{simple_profit:,.2f}")
print(f"平台服务费: ¥{simple_service_fee:,.2f}")
print(f"物流配送费: ¥{simple_delivery:,.2f}")
print(f"企客后返: ¥{simple_enterprise:,.2f}")
print(f"订单实际利润 = {simple_profit:.2f} - {simple_service_fee:.2f} - {simple_delivery:.2f} + {simple_enterprise:.2f}")
print(f"             = ¥{simple_actual_profit:,.2f}")

# 方法2: 订单级聚合(正确方法)
print(f"\n{'='*80}")
print("方法2: 订单级聚合(先按订单ID聚合,再计算)")
print("="*80)

# 转换订单ID为字符串
df_mt['订单ID'] = df_mt['订单ID'].astype(str)

# 按订单聚合
order_agg = df_mt.groupby('订单ID').agg({
    '利润额': 'sum',
    '平台服务费': 'sum',
    '物流配送费': 'first',  # 订单级字段用first
    '企客后返': 'first' if '企客后返' in df_mt.columns else lambda x: 0
}).reset_index()

print(f"聚合后订单数: {len(order_agg):,}")

# 计算订单实际利润
order_agg['订单实际利润'] = (
    order_agg['利润额'] 
    - order_agg['平台服务费'] 
    - order_agg['物流配送费'] 
    + order_agg['企客后返']
)

order_profit_sum = order_agg['利润额'].sum()
order_service_fee_sum = order_agg['平台服务费'].sum()
order_delivery_sum = order_agg['物流配送费'].sum()
order_enterprise_sum = order_agg['企客后返'].sum()
order_actual_profit_sum = order_agg['订单实际利润'].sum()

print(f"利润额: ¥{order_profit_sum:,.2f}")
print(f"平台服务费: ¥{order_service_fee_sum:,.2f}")
print(f"物流配送费: ¥{order_delivery_sum:,.2f}")
print(f"企客后返: ¥{order_enterprise_sum:,.2f}")
print(f"订单实际利润 = {order_profit_sum:.2f} - {order_service_fee_sum:.2f} - {order_delivery_sum:.2f} + {order_enterprise_sum:.2f}")
print(f"             = ¥{order_actual_profit_sum:,.2f}")

# 方法3: 检查是否有服务费=0的订单需要剔除
print(f"\n{'='*80}")
print("方法3: 应用渠道过滤(剔除收费渠道且服务费=0的订单)")
print("="*80)

# 美团闪购是收费渠道
is_fee_channel = True
zero_fee_orders = order_agg[order_agg['平台服务费'] <= 0]

print(f"总订单数: {len(order_agg):,}")
print(f"服务费=0的订单: {len(zero_fee_orders):,}")

if len(zero_fee_orders) > 0:
    print(f"\n⚠️ 发现 {len(zero_fee_orders)} 个服务费=0的订单,需要剔除!")
    print(f"   这些订单的利润额: ¥{zero_fee_orders['利润额'].sum():,.2f}")
    print(f"   这些订单的实际利润: ¥{zero_fee_orders['订单实际利润'].sum():,.2f}")
    
    # 剔除后的结果
    order_agg_filtered = order_agg[order_agg['平台服务费'] > 0].copy()
    filtered_actual_profit = order_agg_filtered['订单实际利润'].sum()
    
    print(f"\n✅ 剔除后:")
    print(f"   订单数: {len(order_agg_filtered):,}")
    print(f"   订单实际利润: ¥{filtered_actual_profit:,.2f}")
else:
    print(f"✅ 没有需要剔除的订单")
    filtered_actual_profit = order_actual_profit_sum

# 总结
print(f"\n{'='*80}")
print("📊 计算结果对比")
print("="*80)
print(f"方法1(简单聚合): ¥{simple_actual_profit:,.2f}")
print(f"方法2(订单聚合): ¥{order_actual_profit_sum:,.2f}")
print(f"方法3(过滤后): ¥{filtered_actual_profit:,.2f}")

print(f"\n💡 结论:")
if abs(simple_actual_profit - order_actual_profit_sum) > 0.01:
    print(f"   ⚠️ 方法1和方法2差异: ¥{abs(simple_actual_profit - order_actual_profit_sum):,.2f}")
    print(f"   原因: 商品级字段(平台服务费)需要先sum再聚合到订单级")

if abs(order_actual_profit_sum - filtered_actual_profit) > 0.01:
    print(f"   ⚠️ 方法2和方法3差异: ¥{abs(order_actual_profit_sum - filtered_actual_profit):,.2f}")
    print(f"   原因: 需要剔除服务费=0的异常订单")

print(f"\n✅ 最终正确答案应该是: ¥{filtered_actual_profit:,.2f}")
print(f"="*80)
