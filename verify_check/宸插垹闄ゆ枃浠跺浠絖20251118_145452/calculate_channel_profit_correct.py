"""使用看板相同的计算逻辑验证分渠道利润"""
from database.connection import SessionLocal
from database.models import Order
import pandas as pd

session = SessionLocal()

# 查询铜山万达店所有数据
query = session.query(Order).filter(Order.store_name == '惠宜选-徐州铜山万达店')
orders_data = query.all()

# 转换为DataFrame
data = []
for o in orders_data:
    data.append({
        '订单ID': o.order_id,
        '渠道': o.channel,
        '商品实售价': o.price,
        '利润额': o.profit,
        '销量': o.quantity,
        '物流配送费': o.delivery_fee,
        '平台佣金': o.commission,
        '用户支付配送费': o.user_paid_delivery_fee,
        '配送费减免金额': o.delivery_discount,
        '满减金额': o.full_reduction,
        '商品减免金额': o.product_discount,
        '商家代金券': o.merchant_voucher,
        '商家承担部分券': o.merchant_share
    })

df = pd.DataFrame(data)

print(f"总记录数: {len(df):,}")
print(f"订单数: {df['订单ID'].nunique():,}")
print(f"渠道数: {df['渠道'].nunique()}")

# ===== 使用看板相同的计算逻辑 =====
print('\n' + '='*100)
print('使用看板 calculate_order_metrics 逻辑计算分渠道利润')
print('='*100)

# Step 1: 订单级聚合（订单级字段用first，商品级字段用sum）
agg_dict = {
    '商品实售价': 'sum',
    '利润额': 'sum',
    '销量': 'sum',
    '用户支付配送费': 'first',  # 订单级
    '配送费减免金额': 'first',
    '物流配送费': 'first',       # 订单级
    '满减金额': 'first',
    '商品减免金额': 'first',
    '商家代金券': 'first',
    '商家承担部分券': 'first',
    '平台佣金': 'first',         # 订单级
}

order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()

# 添加渠道信息
order_channel = df.groupby('订单ID')['渠道'].first()
order_agg = order_agg.merge(order_channel, on='订单ID', how='left')

# Step 2: 计算商家活动成本
order_agg['商家活动成本'] = (
    order_agg['满减金额'] + 
    order_agg['商品减免金额'] + 
    order_agg['商家代金券'] +
    order_agg['商家承担部分券']
)

# Step 3: 计算配送净成本
order_agg['配送净成本'] = (
    order_agg['物流配送费'] - 
    (order_agg['用户支付配送费'] - order_agg['配送费减免金额'])
)

# Step 4: 计算订单实际利润
order_agg['订单实际利润'] = (
    order_agg['利润额'] - 
    order_agg['配送净成本'] - 
    order_agg['平台佣金']
)

# 过滤掉不需要的渠道
excluded_channels = ['收银机订单', '闪购小程序']
order_agg_filtered = order_agg[~order_agg['渠道'].isin(excluded_channels)].copy()

# 按渠道聚合
channel_stats = order_agg_filtered.groupby('渠道').agg({
    '订单ID': 'count',
    '商品实售价': 'sum',
    '订单实际利润': 'sum',
    '商家活动成本': 'sum',
    '平台佣金': 'sum',
    '配送净成本': 'sum'
}).reset_index()

channel_stats.columns = ['渠道', '订单数', '销售额', '总利润', '营销成本', '平台佣金', '配送成本']

# 计算关键指标
channel_stats['客单价'] = channel_stats['销售额'] / channel_stats['订单数']
channel_stats['利润率'] = (channel_stats['总利润'] / channel_stats['销售额'] * 100).fillna(0)

# 排序
channel_stats = channel_stats.sort_values('销售额', ascending=False)

# 显示结果
print(f"\n{'渠道':<15} {'订单数':>8} {'销售额':>12} {'总利润':>12} {'利润率':>8} {'客单价':>10}")
print('-'*80)
for _, row in channel_stats.iterrows():
    print(f"{row['渠道']:<15} {int(row['订单数']):>8,} {row['销售额']:>12,.2f} {row['总利润']:>12,.2f} {row['利润率']:>7.1f}% {row['客单价']:>10,.2f}")

print('-'*80)
print(f"{'合计':<15} {channel_stats['订单数'].sum():>8,} {channel_stats['销售额'].sum():>12,.2f} {channel_stats['总利润'].sum():>12,.2f}")

print('\n💡 这是看板实际显示的数据（使用正确的订单级聚合）')

session.close()
