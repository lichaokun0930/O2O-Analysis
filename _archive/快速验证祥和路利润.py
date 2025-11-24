"""
快速验证祥和路店(美团闪购)的利润计算
"""
import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from 智能门店看板_Dash版 import calculate_order_metrics, CHANNELS_TO_REMOVE, GLOBAL_DATA

print("="*80)
print("🔍 祥和路店(美团闪购)利润验证")
print("="*80)

if GLOBAL_DATA is None or GLOBAL_DATA.empty:
    print("❌ GLOBAL_DATA为空,请先启动看板")
    sys.exit(1)

df = GLOBAL_DATA.copy()
channel_name = "美团闪购"

print(f"\n1️⃣ 全局数据统计:")
print(f"   总行数: {len(df):,}")
print(f"   总订单数: {df['订单ID'].nunique():,}")

print(f"\n2️⃣ 主看板计算流程:")
print(f"   Step 1: 全局订单聚合...")
order_agg = calculate_order_metrics(df, calc_mode='all_no_fallback')
print(f"   ✅ order_agg: {len(order_agg):,} 订单")

# 确保渠道字段
if '渠道' not in order_agg.columns:
    order_channel = df.groupby('订单ID')['渠道'].first().reset_index()
    order_channel['订单ID'] = order_channel['订单ID'].astype(str)
    order_agg['订单ID'] = order_agg['订单ID'].astype(str)
    order_agg = order_agg.merge(order_channel, on='订单ID', how='left')

print(f"\n   Step 2: 过滤排除渠道...")
excluded_channels = ['收银机订单', '闪购小程序'] + CHANNELS_TO_REMOVE
print(f"   排除: {excluded_channels}")
order_agg_filtered = order_agg[~order_agg['渠道'].isin(excluded_channels)].copy()
print(f"   ✅ 过滤后: {len(order_agg_filtered):,} 订单")

print(f"\n   Step 3: 按渠道聚合...")
channel_stats = order_agg_filtered.groupby('渠道').agg({
    '订单ID': 'count',
    '实收价格': 'sum' if '实收价格' in order_agg_filtered.columns else lambda x: 0,
    '订单实际利润': 'sum'
}).reset_index()
channel_stats.columns = ['渠道', '订单数', '销售额', '利润额']

print(f"\n📊 主看板渠道统计:")
print(channel_stats[channel_stats['渠道'] == channel_name].to_string(index=False))

print(f"\n3️⃣ 下钻页面计算流程:")
print(f"   Step 1-3: 复用主看板的order_agg和过滤逻辑...")
print(f"   Step 4: 提取{channel_name}数据...")
channel_order_agg = order_agg_filtered[order_agg_filtered['渠道'] == channel_name].copy()
print(f"   ✅ {channel_name}订单数: {len(channel_order_agg):,}")

if '实收价格' in channel_order_agg.columns:
    total_sales = channel_order_agg['实收价格'].sum()
else:
    total_sales = channel_order_agg['商品实售价'].sum()

total_profit = channel_order_agg['订单实际利润'].sum()
total_orders = len(channel_order_agg)

print(f"\n📊 下钻页面统计:")
print(f"   订单数: {total_orders:,}")
print(f"   销售额: ¥{total_sales:,.2f}")
print(f"   利润额: ¥{total_profit:,.2f}")

print(f"\n4️⃣ 一致性验证:")
main_profit = channel_stats[channel_stats['渠道'] == channel_name]['利润额'].iloc[0]
drill_profit = total_profit

if abs(main_profit - drill_profit) < 0.01:
    print(f"   ✅ 利润额一致: 主看板={main_profit:.2f}, 下钻={drill_profit:.2f}")
else:
    print(f"   ❌ 利润额不一致:")
    print(f"      主看板: ¥{main_profit:,.2f}")
    print(f"      下钻页面: ¥{drill_profit:,.2f}")
    print(f"      差异: ¥{abs(main_profit - drill_profit):,.2f}")

print(f"\n{'='*80}")
