"""
完整模拟真实看板场景测试
验证动销率、滞销品、库存周转等功能
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

print("=" * 80)
print("🧪 完整模拟真实看板场景测试")
print("=" * 80)

# 模拟真实数据结构
np.random.seed(42)
dates = pd.date_range(end=datetime.now(), periods=31, freq='D')
categories = ['饮品', '休闲食品', '酒类', '个人洗护', '连食/罐头']

# 创建订单数据
orders = []
order_id = 1

# 为每个分类创建商品和订单
all_products_info = []

for cat in categories:
    # 每个分类20个商品
    for i in range(1, 21):
        product_name = f"{cat}_商品{i}"
        all_products_info.append({
            '商品名称': product_name,
            '一级分类名': cat,
            '库存': np.random.randint(0, 150)
        })
        
        # 只有前15个商品有销售(后5个商品无销售,用于测试动销率)
        if i <= 15:
            # 每个商品随机生成5-15个订单
            num_orders = np.random.randint(5, 15)
            for _ in range(num_orders):
                date = np.random.choice(dates)
                orders.append({
                    '订单ID': f'ORD_{order_id:06d}',
                    '商品名称': product_name,
                    '一级分类名': cat,
                    '商品实售价': np.random.uniform(10, 200),
                    '月售': np.random.randint(1, 20),
                    '库存': np.random.randint(0, 150),
                    '日期': date,
                    '下单时间': date,
                    '利润额': np.random.uniform(2, 50),
                    '物流配送费': np.random.uniform(0, 5),
                    '平台佣金': np.random.uniform(0, 10)
                })
                order_id += 1

df = pd.DataFrame(orders)

# 创建订单聚合数据
order_agg = df.groupby('订单ID').agg({
    '利润额': 'first',
    '物流配送费': 'first',
    '平台佣金': 'first'
}).reset_index()
order_agg['订单实际利润'] = order_agg['利润额'] - order_agg['物流配送费'] - order_agg['平台佣金']

print(f"\n📊 模拟数据统计:")
print(f"   总订单数: {len(df)}")
print(f"   订单数: {df['订单ID'].nunique()}")
print(f"   有销售的商品数: {df['商品名称'].nunique()}")
print(f"   总商品数(包含无销售): {len(all_products_info)}")
print(f"   分类数: {df['一级分类名'].nunique()}")

print(f"\n📋 各分类商品统计:")
for cat in categories:
    total = len([p for p in all_products_info if p['一级分类名'] == cat])
    with_sales = df[df['一级分类名'] == cat]['商品名称'].nunique()
    print(f"   {cat}: 总商品{total}个, 有销售{with_sales}个")

# 现在测试函数逻辑
print("\n" + "=" * 80)
print("🔍 测试动销率计算逻辑")
print("=" * 80)

# 模拟函数中的逻辑
last_date = df['日期'].max()

# 方法1: 当前代码逻辑(基于销售数据)
print("\n方法1: 基于销售数据统计 (当前代码)")
products_with_sales_method1 = df.groupby('一级分类名')['商品名称'].nunique().reset_index()
products_with_sales_method1.columns = ['分类', '有销量商品数']

for idx, row in products_with_sales_method1.iterrows():
    cat = row['分类']
    with_sales = row['有销量商品数']
    total = with_sales  # 问题: 总商品数也是基于销售数据
    rate = 100.0 if total > 0 else 0
    print(f"   {cat}: 有销量{with_sales}个 / 总商品{total}个 = {rate:.1f}% ❌ (错误!)")

# 方法2: 正确逻辑(需要获取所有商品库存信息)
print("\n方法2: 基于库存数据统计 (修复后)")

# 问题: 销售数据df中没有包含无销售的商品!
# 需要从其他数据源(如商品库存表)获取所有商品
print("   ⚠️ 关键问题: df中只有有销售的商品,缺少无销售商品的库存记录!")

# 如果有完整的商品库存数据
all_products_df = pd.DataFrame(all_products_info)
print(f"\n   假设有完整商品库存表: {len(all_products_df)}个商品")

for cat in categories:
    total = all_products_df[all_products_df['一级分类名'] == cat]['商品名称'].nunique()
    with_sales = df[df['一级分类名'] == cat]['商品名称'].nunique()
    rate = (with_sales / total * 100) if total > 0 else 0
    print(f"   {cat}: 有销量{with_sales}个 / 总商品{total}个 = {rate:.1f}% ✅ (正确!)")

# 关键发现
print("\n" + "=" * 80)
print("💡 关键发现")
print("=" * 80)
print("""
问题根源:
1. df (订单数据) 中只包含有销售记录的商品
2. 无销售的商品不会出现在订单数据中
3. 因此无法从df中获取完整的商品列表

当前数据源分析:
- 订单表: 只有发生销售的商品 ❌
- 商品表: 包含所有商品(有无销售都有) ✅

解决方案:
需要检查你的数据来源:
1. 是否有独立的商品库存表?
2. 还是所有商品都必须有销售记录才会出现?

如果是祥和路店数据,让我检查一下实际数据结构...
""")

# 检查真实数据
print("\n" + "=" * 80)
print("🔎 检查真实数据文件")
print("=" * 80)

import os
data_file = r"d:\Python1\O2O_Analysis\O2O数据分析\测算模型\门店数据\比价看板模块\订单数据-本店.xlsx"

if os.path.exists(data_file):
    print(f"✅ 找到数据文件: {data_file}")
    try:
        # 读取前100行看结构
        real_df = pd.read_excel(data_file, nrows=100)
        print(f"\n📋 数据列名:")
        for col in real_df.columns:
            print(f"   - {col}")
        
        print(f"\n📊 数据行数(前100): {len(real_df)}")
        print(f"   商品数: {real_df['商品名称'].nunique() if '商品名称' in real_df.columns else '列名不存在'}")
        
        # 检查是否有商品在某些日期没有销售
        if '商品名称' in real_df.columns and '日期' in real_df.columns:
            print(f"\n   每个商品的出现次数:")
            product_counts = real_df['商品名称'].value_counts().head(10)
            for product, count in product_counts.items():
                print(f"      {product}: {count}次")
                
    except Exception as e:
        print(f"❌ 读取失败: {e}")
else:
    print(f"❌ 文件不存在: {data_file}")

print("\n" + "=" * 80)
print("📝 结论")
print("=" * 80)
print("""
如果你看到的动销率是100%,可能的原因:

原因1: 数据结构问题
- 订单数据中确实所有商品都有销售
- 没有独立的商品库存表
- 无法区分"有商品但无销售"的情况

原因2: 数据筛选问题
- 选择的日期范围内,所有商品都有销售
- 可以尝试选择更长的日期范围

原因3: 代码逻辑确实需要调整
- 需要从其他数据源获取完整商品列表
- 或者基于库存字段推断商品存在

建议:
1. 检查是否有商品库存表或商品主数据表
2. 确认数据源中是否包含"有商品但无销售"的记录
3. 如果确实所有商品都有销售,那100%就是正确的
""")
