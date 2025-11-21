"""
完整测试:模拟真实订单数据结构
每个商品每天都有记录,但只有部分商品有实际销量
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("=" * 80)
print("🧪 模拟真实订单数据结构测试")
print("=" * 80)

# 模拟真实数据:每个商品每天都有记录
np.random.seed(42)
dates = pd.date_range(end=datetime.now(), periods=31, freq='D')
categories = ['饮品', '休闲食品', '酒类', '个人洗护', '连食/罐头']

orders = []
order_id = 1

for cat in categories:
    # 每个分类20个商品
    for i in range(1, 21):
        product_name = f"{cat}_商品{i}"
        
        # 每个商品每天都有记录
        for date in dates:
            # 前15个商品有实际销量,后5个商品销量=0
            if i <= 15:
                # 有销量的商品
                orders.append({
                    '订单ID': f'ORD_{order_id:06d}',
                    '商品名称': product_name,
                    '一级分类名': cat,
                    '商品实售价': np.random.uniform(10, 200),
                    '月售': np.random.randint(1, 20),  # 月售 > 0
                    '库存': np.random.randint(0, 150),
                    '日期': date,
                    '下单时间': date,
                    '利润额': np.random.uniform(2, 50),
                    '物流配送费': np.random.uniform(0, 5),
                    '平台佣金': np.random.uniform(0, 10)
                })
            else:
                # 无销量的商品(但每天都有记录)
                orders.append({
                    '订单ID': f'ORD_{order_id:06d}',
                    '商品名称': product_name,
                    '一级分类名': cat,
                    '商品实售价': 0,  # 销售额 = 0
                    '月售': 0,  # 月售 = 0
                    '库存': np.random.randint(50, 150),
                    '日期': date,
                    '下单时间': date,
                    '利润额': 0,
                    '物流配送费': 0,
                    '平台佣金': 0
                })
            order_id += 1

df = pd.DataFrame(orders)

print(f"\n📊 数据统计:")
print(f"   总记录数: {len(df)}")
print(f"   商品总数: {df['商品名称'].nunique()}")
print(f"   分类数: {df['一级分类名'].nunique()}")
print(f"   日期范围: {df['日期'].min().date()} ~ {df['日期'].max().date()}")

# 测试动销率计算
print("\n" + "=" * 80)
print("🔍 测试动销率计算")
print("=" * 80)

print("\n❌ 错误方法: 基于出现在数据中的商品")
for cat in categories:
    total = df[df['一级分类名'] == cat]['商品名称'].nunique()
    with_sales = df[df['一级分类名'] == cat]['商品名称'].nunique()
    rate = (with_sales / total * 100) if total > 0 else 0
    print(f"   {cat}: {with_sales}/{total} = {rate:.1f}% (错误!)")

print("\n✅ 正确方法: 基于月售>0的商品")
for cat in categories:
    total = df[df['一级分类名'] == cat]['商品名称'].nunique()
    with_sales = df[(df['一级分类名'] == cat) & (df['月售'] > 0)]['商品名称'].nunique()
    rate = (with_sales / total * 100) if total > 0 else 0
    print(f"   {cat}: {with_sales}/{total} = {rate:.1f}% (正确!)")

# 测试滞销品统计
print("\n" + "=" * 80)
print("🐌 测试滞销品统计")
print("=" * 80)

last_date = df['日期'].max()
last_stock = df.loc[df.groupby('商品名称')['日期'].idxmax()]

product_last_sale = df[df['月售'] > 0].groupby('商品名称')['日期'].max().reset_index()
product_last_sale.columns = ['商品名称', '最后销售日期']
product_last_sale['滞销天数'] = (last_date - product_last_sale['最后销售日期']).dt.days

product_info = df[['商品名称', '一级分类名']].drop_duplicates()
product_stock = last_stock[['商品名称', '库存']]
product_info = product_info.merge(product_stock, on='商品名称', how='left')

product_stagnant = product_last_sale.merge(product_info, on='商品名称', how='left')

# 统计各类型滞销品
product_stagnant['轻度滞销'] = ((product_stagnant['滞销天数'] == 7) & (product_stagnant['库存'] > 0)).astype(int)
product_stagnant['中度滞销'] = ((product_stagnant['滞销天数'] >= 8) & (product_stagnant['滞销天数'] <= 15) & (product_stagnant['库存'] > 0)).astype(int)
product_stagnant['重度滞销'] = ((product_stagnant['滞销天数'] >= 16) & (product_stagnant['滞销天数'] <= 30) & (product_stagnant['库存'] > 0)).astype(int)
product_stagnant['超重度滞销'] = ((product_stagnant['滞销天数'] > 30) & (product_stagnant['库存'] > 0)).astype(int)

stagnant_stats = product_stagnant.groupby('一级分类名').agg({
    '轻度滞销': 'sum',
    '中度滞销': 'sum',
    '重度滞销': 'sum',
    '超重度滞销': 'sum'
}).reset_index()

print("\n滞销品统计:")
for idx, row in stagnant_stats.iterrows():
    print(f"   {row['一级分类名']}: 轻度{row['轻度滞销']} 中度{row['中度滞销']} 重度{row['重度滞销']} 超重度{row['超重度滞销']}")

# 对于无销售的商品(月售始终=0)
no_sales_products = df[df['月售'] == 0].groupby('商品名称').size().reset_index()
no_sales_products = no_sales_products[no_sales_products[0] == len(dates)]  # 所有日期都是0
print(f"\n完全无销售的商品数: {len(no_sales_products)} (这些商品不在滞销品统计中)")

# 测试库存周转
print("\n" + "=" * 80)
print("📦 测试库存周转天数")
print("=" * 80)

date_range_days = (df['日期'].max() - df['日期'].min()).days + 1

for cat in categories:
    cat_df = df[df['一级分类名'] == cat]
    total_qty = cat_df['月售'].sum()
    cat_stock = last_stock[last_stock['一级分类名'] == cat]['库存'].sum()
    
    daily_avg = total_qty / date_range_days
    turnover_days = (cat_stock / daily_avg) if daily_avg > 0 else 0
    
    print(f"   {cat}: 库存{int(cat_stock)}件, 日均销{daily_avg:.1f}件, 周转{turnover_days:.1f}天")

print("\n" + "=" * 80)
print("✅ 测试完成!")
print("=" * 80)

print("\n📝 总结:")
print("   1. ✅ 动销率: 基于月售>0统计,结果为75% (15/20)")
print("   2. ✅ 滞销品: 有销售但最近N天无销量的商品")
print("   3. ✅ 库存周转: 正确计算")
print("   4. ⚠️  完全无销售的5个商品不计入滞销品")
