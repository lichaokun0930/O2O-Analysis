"""
测试策略引流动态门槛的效果
对比固定门槛和动态门槛的差异
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

print(f"✅ 聚合完成，共 {len(product_agg)} 个商品")

# ========== 识别潜在的策略引流商品 ==========
print("\n" + "="*60)
print("📊 潜在策略引流商品分析")
print("="*60)

# 识别极端价格商品
extreme_price = product_agg[product_agg['商品实售价'] <= 0.01]
loss_attraction = product_agg[product_agg['利润率'] < -50]
low_price = product_agg[
    (product_agg['商品实售价'] <= 2) & 
    (product_agg['单品成本'] > 0) & 
    (product_agg['商品实售价'] < product_agg['单品成本'] * 0.5)
]
free_gift = product_agg[product_agg['商品实售价'] == 0]

print(f"\n潜在策略引流商品类型:")
print(f"  秒杀/满赠（≤0.01元）: {len(extreme_price)}个")
print(f"  亏损引流（利润率<-50%）: {len(loss_attraction)}个")
print(f"  低价引流（≤2元且<成本一半）: {len(low_price)}个")
print(f"  赠品（价格=0）: {len(free_gift)}个")

# 合并所有潜在策略引流商品
potential_strategy = pd.concat([extreme_price, loss_attraction, low_price, free_gift]).drop_duplicates()
print(f"\n总计潜在策略引流商品: {len(potential_strategy)}个")

# ========== 固定门槛测试 ==========
print("\n" + "="*60)
print("📊 固定门槛测试（销量≥20件）")
print("="*60)

FIXED_THRESHOLD = 20

strategy_fixed = potential_strategy[potential_strategy['销量'] >= FIXED_THRESHOLD]
print(f"\n满足固定门槛的策略引流商品: {len(strategy_fixed)}个 ({len(strategy_fixed)/len(potential_strategy)*100:.1f}%)")

if len(strategy_fixed) > 0:
    print(f"\n示例（前5个）:")
    for idx, row in strategy_fixed.head(5).iterrows():
        print(f"  - {row['商品名称'][:30]}: 价格{row['商品实售价']:.2f}元, 销量{row['销量']:.0f}件, 利润率{row['利润率']:.1f}%")

# ========== 动态门槛测试 ==========
print("\n" + "="*60)
print("📊 动态门槛测试（销量≥50分位数）")
print("="*60)

DYNAMIC_THRESHOLD = max(product_agg['销量'].quantile(0.5), 3)
print(f"\n动态门槛: 销量≥{DYNAMIC_THRESHOLD:.0f}件（50分位数，保底3件）")

strategy_dynamic = potential_strategy[potential_strategy['销量'] >= DYNAMIC_THRESHOLD]
print(f"满足动态门槛的策略引流商品: {len(strategy_dynamic)}个 ({len(strategy_dynamic)/len(potential_strategy)*100:.1f}%)")

if len(strategy_dynamic) > 0:
    print(f"\n示例（前5个）:")
    for idx, row in strategy_dynamic.head(5).iterrows():
        print(f"  - {row['商品名称'][:30]}: 价格{row['商品实售价']:.2f}元, 销量{row['销量']:.0f}件, 利润率{row['利润率']:.1f}%")

# ========== 对比分析 ==========
print("\n" + "="*60)
print("📊 固定门槛 vs 动态门槛对比")
print("="*60)

print(f"\n策略引流商品数量:")
print(f"  固定门槛（≥20件）: {len(strategy_fixed)}个 ({len(strategy_fixed)/len(potential_strategy)*100:.1f}%)")
print(f"  动态门槛（≥{DYNAMIC_THRESHOLD:.0f}件）: {len(strategy_dynamic)}个 ({len(strategy_dynamic)/len(potential_strategy)*100:.1f}%)")
print(f"  差异: {len(strategy_dynamic) - len(strategy_fixed):+d}个")

# 分析新增的商品
new_strategy = strategy_dynamic[~strategy_dynamic['商品名称'].isin(strategy_fixed['商品名称'])]
if len(new_strategy) > 0:
    print(f"\n动态门槛新增的策略引流商品: {len(new_strategy)}个")
    print(f"示例（前5个）:")
    for idx, row in new_strategy.head(5).iterrows():
        print(f"  - {row['商品名称'][:30]}: 价格{row['商品实售价']:.2f}元, 销量{row['销量']:.0f}件")

# ========== 建议 ==========
print("\n" + "="*60)
print("💡 结论")
print("="*60)

if len(potential_strategy) == 0:
    print("\n✅ 当前没有潜在的策略引流商品")
    print("   这是正常的，说明门店没有极端价格的引流活动")
else:
    strategy_pct_dynamic = len(strategy_dynamic) / len(potential_strategy) * 100
    
    if strategy_pct_dynamic >= 50:
        print(f"\n✅ 动态门槛效果良好！")
        print(f"   - {strategy_pct_dynamic:.1f}%的潜在引流商品被识别")
        print(f"   - 动态门槛（{DYNAMIC_THRESHOLD:.0f}件）比固定门槛（20件）更合理")
        print(f"   - 建议采用动态门槛")
    else:
        print(f"\n⚠️ 动态门槛可能仍然偏高")
        print(f"   - 只有{strategy_pct_dynamic:.1f}%的潜在引流商品被识别")
        print(f"   - 建议考虑使用更低的分位数（如30分位数）")

print("\n" + "="*60)
print("测试完成！")
print("="*60)
