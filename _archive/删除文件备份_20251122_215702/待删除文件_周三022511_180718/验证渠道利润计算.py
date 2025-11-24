"""
验证不同渠道的利润额计算
对比修复前后的差异
"""
import pandas as pd
import numpy as np

print("=" * 80)
print("渠道利润额计算验证")
print("=" * 80)

# 读取数据
try:
    df = pd.read_excel('实际数据/枫瑞.xlsx')
    print(f"\n✅ 成功读取数据: {len(df)} 行")
    print(f"列名: {df.columns.tolist()[:20]}...")  # 只显示前20个
except Exception as e:
    print(f"❌ 读取数据失败: {e}")
    exit(1)

# 检查必需字段
required_fields = ['订单ID', '渠道', '利润额', '平台服务费', '物流配送费']
missing_fields = [f for f in required_fields if f not in df.columns]
if missing_fields:
    print(f"\n❌ 缺少必需字段: {missing_fields}")
    print(f"可用字段: {df.columns.tolist()}")
    exit(1)

print("\n" + "=" * 80)
print("第一步: 查看原始数据统计")
print("=" * 80)

print(f"\n总订单数: {df['订单ID'].nunique()}")
print(f"总行数(包含商品明细): {len(df)}")
print(f"\n渠道分布:")
channel_dist = df.groupby('渠道')['订单ID'].nunique()
for ch, cnt in channel_dist.items():
    print(f"  {ch}: {cnt} 订单")

print("\n" + "=" * 80)
print("第二步: 按订单聚合(模拟calculate_order_metrics)")
print("=" * 80)

# 确保订单ID唯一性
df['订单ID'] = df['订单ID'].astype(str)

# 检查企客后返字段
if '企客后返' in df.columns:
    has_rebate = True
    print("✅ 找到'企客后返'字段")
else:
    has_rebate = False
    print("⚠️ 未找到'企客后返'字段,将设为0")
    df['企客后返'] = 0

# 按订单聚合
agg_dict = {
    '渠道': 'first',
    '利润额': 'sum',
    '平台服务费': 'sum',
    '物流配送费': 'sum',
    '企客后返': 'sum'
}

# 添加平台佣金(如果存在)
if '平台佣金' in df.columns:
    agg_dict['平台佣金'] = 'sum'
    has_commission = True
    print("✅ 找到'平台佣金'字段")
else:
    has_commission = False
    print("⚠️ 未找到'平台佣金'字段")

# 添加实收价格(用于计算利润率)
if '实收价格' in df.columns:
    agg_dict['实收价格'] = 'sum'
    has_actual_price = True
elif '预计订单收入' in df.columns:
    agg_dict['预计订单收入'] = 'sum'
    has_actual_price = True
else:
    has_actual_price = False

order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()

print(f"\n聚合后订单数: {len(order_agg)}")
print(f"\n订单聚合样本数据(前3行):")
print(order_agg[['订单ID', '渠道', '利润额', '平台服务费', '物流配送费', '企客后返']].head(3))

print("\n" + "=" * 80)
print("第三步: 计算订单实际利润(修复前 - 未过滤)")
print("=" * 80)

# 修复前的逻辑: 直接计算,不过滤
order_agg_old = order_agg.copy()
order_agg_old['订单实际利润_旧'] = (
    order_agg_old['利润额'] - 
    order_agg_old['平台服务费'] - 
    order_agg_old['物流配送费'] + 
    order_agg_old['企客后返']
)

# 按渠道统计(修复前)
channel_old = order_agg_old.groupby('渠道').agg({
    '订单ID': 'count',
    '订单实际利润_旧': 'sum'
}).reset_index()
channel_old.columns = ['渠道', '订单数_旧', '总利润_旧']

print("\n【修复前】各渠道利润统计(未过滤平台服务费=0的订单):")
print(channel_old.to_string(index=False))

print("\n" + "=" * 80)
print("第四步: 计算订单实际利润(修复后 - 已过滤)")
print("=" * 80)

# 修复后的逻辑: all_with_fallback模式
order_agg_new = order_agg.copy()

# 1. 计算有效平台费用(带fallback)
if has_commission:
    order_agg_new['有效平台费用'] = order_agg_new['平台服务费']
    fallback_mask = order_agg_new['平台服务费'] <= 0
    order_agg_new.loc[fallback_mask, '有效平台费用'] = order_agg_new.loc[fallback_mask, '平台佣金']
else:
    order_agg_new['有效平台费用'] = order_agg_new['平台服务费']

# 2. 过滤: 只保留有效平台费用>0的订单
print(f"\n过滤前订单数: {len(order_agg_new)}")
order_agg_filtered = order_agg_new[order_agg_new['有效平台费用'] > 0].copy()
print(f"过滤后订单数: {len(order_agg_filtered)}")
print(f"被过滤订单数: {len(order_agg_new) - len(order_agg_filtered)}")

# 查看被过滤的订单
filtered_out = order_agg_new[order_agg_new['有效平台费用'] <= 0]
if len(filtered_out) > 0:
    print(f"\n被过滤订单渠道分布:")
    filtered_channels = filtered_out.groupby('渠道')['订单ID'].count()
    for ch, cnt in filtered_channels.items():
        print(f"  {ch}: {cnt} 订单")
    print(f"\n被过滤订单样本(前5行):")
    sample_cols = ['订单ID', '渠道', '平台服务费']
    if has_commission:
        sample_cols.append('平台佣金')
    sample_cols.append('有效平台费用')
    print(filtered_out[sample_cols].head())

# 3. 计算订单实际利润
order_agg_filtered['订单实际利润'] = (
    order_agg_filtered['利润额'] - 
    order_agg_filtered['平台服务费'] - 
    order_agg_filtered['物流配送费'] + 
    order_agg_filtered['企客后返']
)

# 按渠道统计(修复后)
channel_new = order_agg_filtered.groupby('渠道').agg({
    '订单ID': 'count',
    '订单实际利润': 'sum'
}).reset_index()
channel_new.columns = ['渠道', '订单数_新', '总利润_新']

print("\n【修复后】各渠道利润统计(已过滤平台服务费=0的订单):")
print(channel_new.to_string(index=False))

print("\n" + "=" * 80)
print("第五步: 对比修复前后的差异")
print("=" * 80)

# 合并对比
comparison = channel_old.merge(channel_new, on='渠道', how='outer').fillna(0)
comparison['订单数差异'] = comparison['订单数_新'] - comparison['订单数_旧']
comparison['利润差异'] = comparison['总利润_新'] - comparison['总利润_旧']
comparison['利润差异率%'] = (comparison['利润差异'] / comparison['总利润_旧'].replace(0, np.nan) * 100).fillna(0).round(2)

print("\n修复前后对比:")
print(comparison[['渠道', '订单数_旧', '订单数_新', '订单数差异', '总利润_旧', '总利润_新', '利润差异', '利润差异率%']].to_string(index=False))

# 计算利润率(如果有实收价格)
if has_actual_price:
    print("\n" + "=" * 80)
    print("第六步: 计算利润率")
    print("=" * 80)
    
    sales_field = '实收价格' if '实收价格' in order_agg_filtered.columns else '预计订单收入'
    
    # 修复后: 按渠道计算利润率
    channel_with_rate = order_agg_filtered.groupby('渠道').agg({
        '订单ID': 'count',
        '订单实际利润': 'sum',
        sales_field: 'sum'
    }).reset_index()
    
    channel_with_rate.columns = ['渠道', '订单数', '总利润', '销售额']
    channel_with_rate['利润率%'] = (
        channel_with_rate['总利润'] / channel_with_rate['销售额'].replace(0, np.nan) * 100
    ).fillna(0).round(2)
    
    print("\n各渠道利润率统计(修复后):")
    print(channel_with_rate.to_string(index=False))

print("\n" + "=" * 80)
print("验证完成!")
print("=" * 80)
