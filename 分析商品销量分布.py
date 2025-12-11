"""
快速分析门店商品的销量和订单数分布
用于评估"销量≥20件 + 订单≥5单"的门槛是否合理
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime, timedelta

# 数据库连接
try:
    from database.connection import engine
    print("✅ 数据库连接成功")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    exit(1)

# 获取最近30天的订单数据
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

print(f"\n📅 分析周期: {start_date.date()} 至 {end_date.date()} (30天)")

# 读取订单数据
query = f"""
SELECT 
    product_name,
    price,
    cost,
    quantity,
    order_id,
    date
FROM orders
WHERE date >= '{start_date.date()}'
  AND date <= '{end_date.date()}'
"""

print("\n🔄 正在读取订单数据...")
try:
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    print(f"✅ 读取成功，共 {len(df)} 条订单记录")
except Exception as e:
    print(f"❌ 读取失败: {e}")
    exit(1)

# 按商品聚合
print("\n🔄 正在聚合商品数据...")
product_agg = df.groupby('product_name').agg({
    'quantity': 'sum',
    'order_id': 'nunique',  # 订单数（去重）
    'price': lambda x: (x * df.loc[x.index, 'quantity']).sum() / df.loc[x.index, 'quantity'].sum() if df.loc[x.index, 'quantity'].sum() > 0 else 0,
    'cost': lambda x: (x * df.loc[x.index, 'quantity']).sum() / df.loc[x.index, 'quantity'].sum() if df.loc[x.index, 'quantity'].sum() > 0 else 0,
}).reset_index()

product_agg.columns = ['商品名称', '销量', '订单数', '商品实售价', '单品成本']

# 计算利润率
product_agg['利润率'] = np.where(
    product_agg['商品实售价'] > 0,
    (product_agg['商品实售价'] - product_agg['单品成本']) / product_agg['商品实售价'] * 100,
    0
)

print(f"✅ 聚合完成，共 {len(product_agg)} 个商品")

# ========== 分析销量分布 ==========
print("\n" + "="*60)
print("📊 销量分布分析")
print("="*60)

sales_stats = product_agg['销量'].describe()
print(f"\n销量统计:")
print(f"  最小值: {sales_stats['min']:.0f} 件")
print(f"  25分位数: {sales_stats['25%']:.0f} 件")
print(f"  中位数: {sales_stats['50%']:.0f} 件")
print(f"  75分位数: {sales_stats['75%']:.0f} 件")
print(f"  最大值: {sales_stats['max']:.0f} 件")
print(f"  平均值: {sales_stats['mean']:.1f} 件")

# 销量分段统计
print(f"\n销量分段统计:")
sales_ranges = [
    (0, 5, "≤5件（极低）"),
    (5, 10, "5-10件（很低）"),
    (10, 20, "10-20件（低）"),
    (20, 50, "20-50件（中等）"),
    (50, 100, "50-100件（高）"),
    (100, float('inf'), "≥100件（很高）")
]

for min_val, max_val, label in sales_ranges:
    count = len(product_agg[(product_agg['销量'] > min_val) & (product_agg['销量'] <= max_val)])
    pct = count / len(product_agg) * 100
    print(f"  {label}: {count}个 ({pct:.1f}%)")

# 关键门槛
sales_20_count = len(product_agg[product_agg['销量'] >= 20])
sales_20_pct = sales_20_count / len(product_agg) * 100
print(f"\n🎯 销量≥20件的商品: {sales_20_count}个 ({sales_20_pct:.1f}%)")

# ========== 分析订单数分布 ==========
print("\n" + "="*60)
print("📊 订单数分布分析")
print("="*60)

orders_stats = product_agg['订单数'].describe()
print(f"\n订单数统计:")
print(f"  最小值: {orders_stats['min']:.0f} 单")
print(f"  25分位数: {orders_stats['25%']:.0f} 单")
print(f"  中位数: {orders_stats['50%']:.0f} 单")
print(f"  75分位数: {orders_stats['75%']:.0f} 单")
print(f"  最大值: {orders_stats['max']:.0f} 单")
print(f"  平均值: {orders_stats['mean']:.1f} 单")

# 订单数分段统计
print(f"\n订单数分段统计:")
orders_ranges = [
    (0, 2, "≤2单（极低）"),
    (2, 5, "2-5单（低）"),
    (5, 10, "5-10单（中等）"),
    (10, 20, "10-20单（高）"),
    (20, float('inf'), "≥20单（很高）")
]

for min_val, max_val, label in orders_ranges:
    count = len(product_agg[(product_agg['订单数'] > min_val) & (product_agg['订单数'] <= max_val)])
    pct = count / len(product_agg) * 100
    print(f"  {label}: {count}个 ({pct:.1f}%)")

# 关键门槛
orders_5_count = len(product_agg[product_agg['订单数'] >= 5])
orders_5_pct = orders_5_count / len(product_agg) * 100
print(f"\n🎯 订单数≥5单的商品: {orders_5_count}个 ({orders_5_pct:.1f}%)")

# ========== 分析组合门槛 ==========
print("\n" + "="*60)
print("📊 组合门槛分析")
print("="*60)

# 当前门槛：销量≥20 + 订单≥5
current_threshold = len(product_agg[(product_agg['销量'] >= 20) & (product_agg['订单数'] >= 5)])
current_pct = current_threshold / len(product_agg) * 100
print(f"\n当前门槛（销量≥20 + 订单≥5）:")
print(f"  满足条件的商品: {current_threshold}个 ({current_pct:.1f}%)")

# 建议的门槛方案
print(f"\n建议的门槛方案对比:")
thresholds = [
    (10, 3, "宽松"),
    (15, 4, "适中"),
    (20, 5, "当前"),
    (30, 6, "严格"),
]

for sales_min, orders_min, label in thresholds:
    count = len(product_agg[(product_agg['销量'] >= sales_min) & (product_agg['订单数'] >= orders_min)])
    pct = count / len(product_agg) * 100
    print(f"  {label}（销量≥{sales_min} + 订单≥{orders_min}）: {count}个 ({pct:.1f}%)")

# ========== 分析高利润商品 ==========
print("\n" + "="*60)
print("📊 高利润商品分析")
print("="*60)

profit_median = product_agg['利润率'].median()
high_profit = product_agg[product_agg['利润率'] > profit_median]
print(f"\n利润率中位数: {profit_median:.1f}%")
print(f"高利润商品（利润率>中位数）: {len(high_profit)}个 ({len(high_profit)/len(product_agg)*100:.1f}%)")

# 高利润商品中，有多少满足不同的动销门槛
print(f"\n高利润商品中，满足不同动销门槛的数量:")
for sales_min, orders_min, label in thresholds:
    count = len(high_profit[(high_profit['销量'] >= sales_min) & (high_profit['订单数'] >= orders_min)])
    pct = count / len(high_profit) * 100
    print(f"  {label}（销量≥{sales_min} + 订单≥{orders_min}）: {count}个 ({pct:.1f}%)")

# ========== 建议 ==========
print("\n" + "="*60)
print("💡 建议")
print("="*60)

if current_pct < 20:
    print(f"\n⚠️ 当前门槛（销量≥20 + 订单≥5）只有 {current_pct:.1f}% 的商品满足")
    print(f"   这个门槛可能偏高，建议考虑降低")
    print(f"\n推荐方案:")
    
    # 找到接近30%的门槛
    for sales_min, orders_min, label in thresholds:
        count = len(product_agg[(product_agg['销量'] >= sales_min) & (product_agg['订单数'] >= orders_min)])
        pct = count / len(product_agg) * 100
        if 25 <= pct <= 35:
            print(f"  ✅ {label}方案（销量≥{sales_min} + 订单≥{orders_min}）: {pct:.1f}% 的商品满足")
            print(f"     这样可以让约30%的商品有机会成为'高动销'")
            break
elif current_pct > 40:
    print(f"\n✅ 当前门槛（销量≥20 + 订单≥5）有 {current_pct:.1f}% 的商品满足")
    print(f"   这个门槛可能偏低，建议考虑提高")
else:
    print(f"\n✅ 当前门槛（销量≥20 + 订单≥5）有 {current_pct:.1f}% 的商品满足")
    print(f"   这个门槛比较合理")

print("\n" + "="*60)
print("分析完成！")
print("="*60)
