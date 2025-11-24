"""
从数据库直接读取数据验证美团闪购利润
"""
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from database.connection import get_db_connection
from database.models import Order
from 智能门店看板_Dash版 import calculate_order_metrics, CHANNELS_TO_REMOVE

print("="*80)
print("🔍 美团闪购利润验证(从数据库)")
print("="*80)

# 1. 从数据库读取数据
end_date = datetime.now().date()
start_date = end_date - timedelta(days=7)

print(f"\n📅 查询时间范围: {start_date} 至 {end_date}")

with get_db_connection() as session:
    orders = session.query(Order).filter(
        Order.date >= start_date,
        Order.date <= end_date
    ).all()
    
    df = pd.DataFrame([{
        '订单ID': o.order_id,
        '渠道': o.channel,
        '门店': o.store_name,
        '商品实售价': o.product_selling_price or 0,
        '实收价格': o.actual_payment or 0,
        '利润额': o.profit or 0,
        '平台服务费': o.platform_service_fee or 0,
        '物流配送费': o.delivery_fee or 0,
        '企客后返': o.enterprise_rebate or 0,
        '订单实际利润': o.actual_profit or 0
    } for o in orders])

print(f"✅ 从数据库读取: {len(df):,} 行, {df['订单ID'].nunique():,} 订单")

# 2. 主看板计算流程
print(f"\n{'='*80}")
print("📊 方法1: 主看板计算流程")
print("="*80)

print(f"Step 1: 全局订单聚合...")
order_agg = calculate_order_metrics(df, calc_mode='all_no_fallback')
print(f"✅ order_agg: {len(order_agg):,} 订单")

# 确保渠道字段
if '渠道' not in order_agg.columns:
    order_channel = df.groupby('订单ID')['渠道'].first().reset_index()
    order_channel['订单ID'] = order_channel['订单ID'].astype(str)
    order_agg['订单ID'] = order_agg['订单ID'].astype(str)
    order_agg = order_agg.merge(order_channel, on='订单ID', how='left')

print(f"\nStep 2: 过滤排除渠道...")
excluded_channels = ['收银机订单', '闪购小程序'] + CHANNELS_TO_REMOVE
print(f"排除: {excluded_channels}")
order_agg_filtered = order_agg[~order_agg['渠道'].isin(excluded_channels)].copy()
print(f"✅ 过滤后: {len(order_agg_filtered):,} 订单")

print(f"\nStep 3: 按渠道聚合...")
channel_stats = order_agg_filtered.groupby('渠道').agg({
    '订单ID': 'count',
    '实收价格': 'sum' if '实收价格' in order_agg_filtered.columns else lambda x: 0,
    '订单实际利润': 'sum'
}).reset_index()
channel_stats.columns = ['渠道', '订单数', '销售额', '总利润']

print(f"\n✅ 主看板渠道统计:")
print(channel_stats.to_string(index=False))

# 3. 下钻页面计算流程
print(f"\n{'='*80}")
print("📊 方法2: 下钻页面计算流程")
print("="*80)

channel_name = "美团闪购"
channel_order_agg = order_agg_filtered[order_agg_filtered['渠道'] == channel_name].copy()
print(f"提取{channel_name}数据: {len(channel_order_agg):,} 订单")

if len(channel_order_agg) > 0:
    total_sales = channel_order_agg['实收价格'].sum() if '实收价格' in channel_order_agg.columns else channel_order_agg['商品实售价'].sum()
    total_profit = channel_order_agg['订单实际利润'].sum()
    
    print(f"\n✅ 下钻页面统计:")
    print(f"   订单数: {len(channel_order_agg):,}")
    print(f"   销售额: ¥{total_sales:,.2f}")
    print(f"   总利润: ¥{total_profit:,.2f}")
else:
    print(f"❌ 没有找到{channel_name}数据!")

# 4. 对比
print(f"\n{'='*80}")
print("🔍 结果对比")
print("="*80)

mt_stats = channel_stats[channel_stats['渠道'] == channel_name]
if len(mt_stats) > 0:
    main_profit = mt_stats['总利润'].iloc[0]
    drill_profit = total_profit
    
    print(f"主看板利润: ¥{main_profit:,.2f}")
    print(f"下钻利润: ¥{drill_profit:,.2f}")
    
    if abs(main_profit - drill_profit) < 0.01:
        print(f"\n✅ 计算一致!")
    else:
        print(f"\n❌ 差异: ¥{abs(main_profit - drill_profit):,.2f}")
else:
    print(f"❌ 主看板没有{channel_name}数据!")

print(f"\n{'='*80}")
