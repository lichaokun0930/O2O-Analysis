"""
测试V7.2动态门槛的效果
对比固定门槛（V7.1）和动态门槛（V7.2）的差异
"""

import pandas as pd
import numpy as np
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
    order_id
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
    'order_id': 'nunique',
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

# 计算动销指数
min_sales = product_agg['销量'].min()
max_sales = product_agg['销量'].max()
sales_range = max_sales - min_sales if max_sales > min_sales else 1
product_agg['标准化销量'] = (product_agg['销量'] - min_sales) / sales_range

min_orders = product_agg['订单数'].min()
max_orders = product_agg['订单数'].max()
orders_range = max_orders - min_orders if max_orders > min_orders else 1
product_agg['标准化订单数'] = (product_agg['订单数'] - min_orders) / orders_range

product_agg['动销指数'] = 0.6 * product_agg['标准化销量'] + 0.4 * product_agg['标准化订单数']

print(f"✅ 聚合完成，共 {len(product_agg)} 个商品")

# ========== V7.1 固定门槛 ==========
print("\n" + "="*60)
print("📊 V7.1 固定门槛测试")
print("="*60)

V71_SALES_MIN = 20
V71_ORDERS_MIN = 5

sales_threshold = product_agg['动销指数'].median()
profit_threshold = product_agg['利润率'].median()

# V7.1判定
def is_high_sales_v71(row):
    return (row['动销指数'] > sales_threshold and 
            row['销量'] >= V71_SALES_MIN and 
            row['订单数'] >= V71_ORDERS_MIN)

product_agg['高动销_V71'] = product_agg.apply(is_high_sales_v71, axis=1)
product_agg['高利润'] = product_agg['利润率'] > profit_threshold

# 统计明星商品（高利润+高动销）
star_v71 = product_agg[product_agg['高利润'] & product_agg['高动销_V71']]

print(f"\n固定门槛: 销量≥{V71_SALES_MIN}件, 订单≥{V71_ORDERS_MIN}单")
print(f"高动销商品: {product_agg['高动销_V71'].sum()}个 ({product_agg['高动销_V71'].sum()/len(product_agg)*100:.1f}%)")
print(f"明星商品（高利润+高动销）: {len(star_v71)}个 ({len(star_v71)/len(product_agg)*100:.1f}%)")

# ========== V7.2 动态门槛 ==========
print("\n" + "="*60)
print("📊 V7.2 动态门槛测试")
print("="*60)

V72_SALES_MIN = max(product_agg['销量'].quantile(0.7), 5)
V72_ORDERS_MIN = max(product_agg['订单数'].quantile(0.7), 2)

# V7.2判定
def is_high_sales_v72(row):
    return (row['动销指数'] > sales_threshold and 
            row['销量'] >= V72_SALES_MIN and 
            row['订单数'] >= V72_ORDERS_MIN)

product_agg['高动销_V72'] = product_agg.apply(is_high_sales_v72, axis=1)

# 统计明星商品（高利润+高动销）
star_v72 = product_agg[product_agg['高利润'] & product_agg['高动销_V72']]

print(f"\n动态门槛: 销量≥{V72_SALES_MIN:.0f}件（70分位数）, 订单≥{V72_ORDERS_MIN:.0f}单（70分位数）")
print(f"高动销商品: {product_agg['高动销_V72'].sum()}个 ({product_agg['高动销_V72'].sum()/len(product_agg)*100:.1f}%)")
print(f"明星商品（高利润+高动销）: {len(star_v72)}个 ({len(star_v72)/len(product_agg)*100:.1f}%)")

# ========== 对比分析 ==========
print("\n" + "="*60)
print("📊 V7.1 vs V7.2 对比")
print("="*60)

print(f"\n高动销商品数量:")
print(f"  V7.1: {product_agg['高动销_V71'].sum()}个 ({product_agg['高动销_V71'].sum()/len(product_agg)*100:.1f}%)")
print(f"  V7.2: {product_agg['高动销_V72'].sum()}个 ({product_agg['高动销_V72'].sum()/len(product_agg)*100:.1f}%)")
print(f"  差异: {product_agg['高动销_V72'].sum() - product_agg['高动销_V71'].sum():+d}个")

print(f"\n明星商品数量:")
print(f"  V7.1: {len(star_v71)}个 ({len(star_v71)/len(product_agg)*100:.1f}%)")
print(f"  V7.2: {len(star_v72)}个 ({len(star_v72)/len(product_agg)*100:.1f}%)")
print(f"  差异: {len(star_v72) - len(star_v71):+d}个")

# 分析变化的商品
v71_only = product_agg[product_agg['高动销_V71'] & ~product_agg['高动销_V72']]
v72_only = product_agg[~product_agg['高动销_V71'] & product_agg['高动销_V72']]

print(f"\n变化分析:")
print(f"  V7.1有但V7.2没有: {len(v71_only)}个（门槛降低后不再满足）")
print(f"  V7.2有但V7.1没有: {len(v72_only)}个（门槛降低后新增）")

if len(v72_only) > 0:
    print(f"\n新增的高动销商品示例（前5个）:")
    for idx, row in v72_only.head(5).iterrows():
        print(f"  - {row['商品名称']}: 销量{row['销量']:.0f}件, 订单{row['订单数']:.0f}单, 动销指数{row['动销指数']:.3f}")

# ========== 建议 ==========
print("\n" + "="*60)
print("💡 结论")
print("="*60)

high_sales_pct_v72 = product_agg['高动销_V72'].sum() / len(product_agg) * 100
star_pct_v72 = len(star_v72) / len(product_agg) * 100

if 25 <= high_sales_pct_v72 <= 35:
    print(f"\n✅ V7.2动态门槛效果良好！")
    print(f"   - 高动销商品占比 {high_sales_pct_v72:.1f}%（目标25-35%）")
    print(f"   - 明星商品占比 {star_pct_v72:.1f}%")
    print(f"   - 建议采用V7.2动态门槛")
elif high_sales_pct_v72 < 25:
    print(f"\n⚠️ V7.2动态门槛可能仍然偏高")
    print(f"   - 高动销商品占比 {high_sales_pct_v72:.1f}%（低于目标25%）")
    print(f"   - 建议考虑使用60分位数或更低")
else:
    print(f"\n⚠️ V7.2动态门槛可能偏低")
    print(f"   - 高动销商品占比 {high_sales_pct_v72:.1f}%（高于目标35%）")
    print(f"   - 建议考虑使用80分位数")

print("\n" + "="*60)
print("测试完成！")
print("="*60)
