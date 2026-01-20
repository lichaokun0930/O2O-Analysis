"""
检查实际数据中的利润率计算

从看板的全局数据中随机抽取几个商品，验证利润率计算是否正确
"""

import sys
import os
import pandas as pd
import numpy as np

# 直接加载数据文件，不启动看板
data_file = r"d:\Python\订单数据看板\O2O-Analysis\实际数据\2025-11-04 00_00_00至2025-12-03 23_59_59订单明细数据导出汇总.xlsx"

print(f"正在加载数据文件: {data_file}")
GLOBAL_DATA = pd.read_excel(data_file)

if GLOBAL_DATA is None or GLOBAL_DATA.empty:
    print("⚠️ 全局数据未加载，请先启动看板")
    sys.exit(1)

print("=" * 100)
print("检查订单数据中的利润额字段")
print("=" * 100)

# 查看原始数据的字段
print(f"\n数据行数: {len(GLOBAL_DATA)}")
print(f"\n数据列: {', '.join(GLOBAL_DATA.columns.tolist())}")

# 检查是否有利润额字段
if '利润额' in GLOBAL_DATA.columns:
    print(f"\n✅ 发现'利润额'字段")
    print(f"   数值范围: {GLOBAL_DATA['利润额'].min():.2f} ~ {GLOBAL_DATA['利润额'].max():.2f}")
    print(f"   平均值: {GLOBAL_DATA['利润额'].mean():.2f}")
    print(f"   非空行数: {GLOBAL_DATA['利润额'].notna().sum()} / {len(GLOBAL_DATA)}")
else:
    print(f"\n❌ 未发现'利润额'字段")

# 检查相关字段
profit_related_cols = ['利润额', '实际利润', '毛利润', '商品实售价', '实收价格', '单品成本', '成本', '商品采购成本']
available_cols = [col for col in profit_related_cols if col in GLOBAL_DATA.columns]

print(f"\n可用的利润相关字段: {', '.join(available_cols)}")

# 随机抽取5个订单查看详情
sample_df = GLOBAL_DATA.sample(min(5, len(GLOBAL_DATA)), random_state=42)

print("\n" + "=" * 100)
print("随机抽取5个订单的详细信息")
print("=" * 100)

display_cols = ['订单ID', '商品名称', '销量', '实收价格', '单品成本', '利润额']
display_cols = [col for col in display_cols if col in sample_df.columns]

for idx, row in sample_df.iterrows():
    print(f"\n订单 #{idx}")
    for col in display_cols:
        print(f"  {col}: {row[col]}")
    
    # 尝试手动计算利润额
    if all(col in row.index for col in ['实收价格', '单品成本', '销量']):
        calculated_profit = (row['实收价格'] - row['单品成本']) * row['销量']
        actual_profit = row.get('利润额', 0)
        print(f"  ")
        print(f"  📊 手动计算利润额 = (实收价格 - 单品成本) × 销量")
        print(f"                   = ({row['实收价格']:.2f} - {row['单品成本']:.2f}) × {row['销量']}")
        print(f"                   = {calculated_profit:.2f}")
        print(f"  📊 数据中的利润额 = {actual_profit:.2f}")
        
        if abs(calculated_profit - actual_profit) < 0.01:
            print(f"  ✅ 验证通过：手动计算 = 数据字段")
        else:
            print(f"  ⚠️ 验证失败：手动计算({calculated_profit:.2f}) ≠ 数据字段({actual_profit:.2f})")
            print(f"     差异: {abs(calculated_profit - actual_profit):.2f}元")

print("\n" + "=" * 100)
print("检查聚合后的商品利润率")
print("=" * 100)

# 模拟商品健康分析的聚合逻辑
sales_col = '月售' if '月售' in GLOBAL_DATA.columns else '销量'
cost_col = '商品采购成本' if '商品采购成本' in GLOBAL_DATA.columns else '成本'

# 计算订单总收入
df_test = GLOBAL_DATA.copy()
if '实收价格' in df_test.columns and sales_col in df_test.columns:
    df_test['订单总收入'] = df_test['实收价格'].fillna(0) * df_test[sales_col].fillna(1)
else:
    df_test['订单总收入'] = df_test.get('商品实售价', 0)

# 聚合到商品级别
group_cols = ['商品名称']
agg_dict = {
    '订单总收入': 'sum',
    '利润额': 'sum',
    sales_col: 'sum',
}

if '商品原价' in df_test.columns:
    agg_dict['商品原价'] = 'max'
if '单品成本' in df_test.columns:
    agg_dict['单品成本'] = 'first'

product_data = df_test.groupby(group_cols).agg(agg_dict).reset_index()

# 计算综合利润率
product_data['综合利润率'] = np.where(
    product_data['订单总收入'] > 0,
    (product_data['利润额'] / product_data['订单总收入'] * 100),
    0
)

# 计算定价利润率
if '商品原价' in product_data.columns and '单品成本' in product_data.columns:
    product_data['定价利润率'] = np.where(
        product_data['商品原价'] > 0,
        ((product_data['商品原价'] - product_data['单品成本']) / product_data['商品原价'] * 100),
        0
    )

# 随机抽取3个商品
sample_products = product_data.sample(min(3, len(product_data)), random_state=42)

print(f"\n随机抽取3个商品的聚合结果:")
for idx, row in sample_products.iterrows():
    print(f"\n【{row['商品名称']}】")
    print(f"  销售额(订单总收入): ¥{row['订单总收入']:.2f}")
    print(f"  利润额: ¥{row['利润额']:.2f}")
    print(f"  销量: {row[sales_col]}件")
    print(f"  综合利润率: {row['综合利润率']:.2f}%")
    
    if '定价利润率' in row:
        print(f"  商品原价: ¥{row['商品原价']:.2f}")
        print(f"  单品成本: ¥{row['单品成本']:.2f}")
        print(f"  定价利润率: {row['定价利润率']:.2f}%")

print("\n" + "=" * 100)
print("结论")
print("=" * 100)
print("""
请检查以上输出，确认：
1. ✅ '利润额'字段在原始数据中存在且有合理的数值范围
2. ✅ 手动计算的利润额与数据字段一致
3. ✅ 聚合后的综合利润率计算正确
4. ✅ 定价利润率基于商品原价和单品成本计算正确

如果发现异常，可能的原因：
- 原始数据中'利润额'字段本身有误
- '实收价格'或'单品成本'字段缺失或错误
- 聚合逻辑有问题（如重复计算）
""")
