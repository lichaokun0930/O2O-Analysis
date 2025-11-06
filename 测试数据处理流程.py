import pandas as pd
import sys
sys.path.append('.')
from 真实数据处理器 import RealDataProcessor

# 初始化处理器
processor = RealDataProcessor(data_dir='门店数据')

# 加载数据
file_path = r"门店数据\2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"
df = pd.read_excel(file_path)

print("=" * 80)
print("🔹 步骤1：原始数据")
print(f"   数据量: {len(df)} 行")
if '成本' in df.columns:
    print(f"   '成本'字段总和: ¥{df['成本'].sum():,.2f}")
    print(f"   '成本'字段非零数量: {(df['成本'] > 0).sum()}")

# 标准化数据
print("\n" + "=" * 80)
print("🔹 步骤2：标准化数据")
standardized_df = processor.standardize_sales_data(df)

print(f"   数据量: {len(standardized_df)} 行")
print(f"   字段: {standardized_df.columns.tolist()}")

if '商品采购成本' in standardized_df.columns:
    print(f"\n   ✅ '商品采购成本'字段存在")
    print(f"   数据类型: {standardized_df['商品采购成本'].dtype}")
    print(f"   总和: ¥{standardized_df['商品采购成本'].sum():,.2f}")
    print(f"   非零数量: {(standardized_df['商品采购成本'] > 0).sum()}")
    print(f"   NaN数量: {standardized_df['商品采购成本'].isna().sum()}")
    print(f"\n   样本数据（前10行）:")
    print(standardized_df[['商品名称', '商品采购成本', '商品实售价']].head(10).to_string())
else:
    print(f"   ❌ '商品采购成本'字段不存在")

# 剔除耗材和咖啡
print("\n" + "=" * 80)
print("🔹 步骤3：剔除耗材")
consumable_mask = standardized_df['一级分类名'] == '耗材'
consumable_count = consumable_mask.sum()
print(f"   耗材数量: {consumable_count} 行")

df_no_consumable = standardized_df[~consumable_mask].copy()
print(f"   剔除后数据量: {len(df_no_consumable)} 行")

if '商品采购成本' in df_no_consumable.columns:
    print(f"   '商品采购成本'总和: ¥{df_no_consumable['商品采购成本'].sum():,.2f}")

print("\n" + "=" * 80)
print("🔹 步骤4：剔除咖啡渠道")
coffee_channels = ['饿了么咖啡', '美团咖啡']
coffee_mask = df_no_consumable['渠道'].isin(coffee_channels)
coffee_count = coffee_mask.sum()
print(f"   咖啡数量: {coffee_count} 行")

df_final = df_no_consumable[~coffee_mask].copy()
print(f"   最终数据量: {len(df_final)} 行")

if '商品采购成本' in df_final.columns:
    print(f"   '商品采购成本'总和: ¥{df_final['商品采购成本'].sum():,.2f}")
    print(f"   '商品采购成本'非零数量: {(df_final['商品采购成本'] > 0).sum()}")
    print(f"   '商品采购成本'NaN数量: {df_final['商品采购成本'].isna().sum()}")

# 测试订单聚合
print("\n" + "=" * 80)
print("🔹 步骤5：订单聚合测试")
order_agg = df_final.groupby('订单ID').agg({
    '商品实售价': 'sum',
    '商品采购成本': 'sum',
}).reset_index()

print(f"   订单数: {len(order_agg)}")
print(f"   商品销售额总和: ¥{order_agg['商品实售价'].sum():,.2f}")
print(f"   商品采购成本总和: ¥{order_agg['商品采购成本'].sum():,.2f}")

print("\n" + "=" * 80)
