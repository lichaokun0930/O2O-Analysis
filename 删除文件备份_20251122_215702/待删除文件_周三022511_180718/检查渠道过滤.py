"""
检查是否有闪购小程序或其他渠道被混在美团共橙里
"""
import pandas as pd

df = pd.read_excel('实际数据/枫瑞.xlsx')
if '一级分类名' in df.columns:
    df = df[df['一级分类名'] != '耗材'].copy()

print("所有渠道分布:")
print(df['渠道'].value_counts())

# 检查美团共橙数据
mt_data = df[df['渠道'] == '美团共橙'].copy()

# 检查是否还有其他需要过滤的
print(f"\n美团共橙渠道检查:")
print(f"  总订单: {mt_data['订单ID'].nunique()}")
print(f"  总利润额: {mt_data['利润额'].sum():.2f}")

# 按订单聚合
order_agg = mt_data.groupby('订单ID').agg({
    '利润额': 'sum',
    '平台服务费': 'sum',
}).reset_index()

# 检查Tab1的过滤逻辑(剔除闪购小程序+饿了么)
excluded_channels = ['收银机订单', '闪购小程序']
print(f"\n如果按Tab1逻辑过滤(排除 {excluded_channels}):")
# 美团共橙不在排除列表,所以应该全部保留
print(f"  美团共橙本身就不在排除列表,应该保留全部")

# 检查利润额的分布
print(f"\n利润额分布:")
print(f"  利润额>0的订单: {(order_agg['利润额'] > 0).sum()}")
print(f"  利润额=0的订单: {(order_agg['利润额'] == 0).sum()}")
print(f"  利润额<0的订单: {(order_agg['利润额'] < 0).sum()}")
print(f"  利润额总和: {order_agg['利润额'].sum():.2f}")

# 你说的31176,差549.18
print(f"\n差异分析:")
print(f"  31725.18 - 31176 = {31725.18 - 31176:.2f}")
print(f"\n可能的原因:")
print(f"  1. 是否有部分订单在你那边被其他条件过滤了?")
print(f"  2. 数据文件版本是否一致?")
print(f"  3. 是否有日期范围过滤?")
