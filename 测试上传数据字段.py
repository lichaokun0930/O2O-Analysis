import pandas as pd
from 真实数据处理器 import RealDataProcessor

# 模拟上传数据处理流程
print("="*80)
print("🔍 测试上传数据处理流程")
print("="*80)

# 1. 加载原始Excel文件
file_path = r"门店数据\2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"
df = pd.read_excel(file_path)

print(f"\n📊 步骤1：原始Excel数据")
print(f"   数据量: {len(df)} 行 × {len(df.columns)} 列")
print(f"   字段: {df.columns.tolist()[:10]}...")

# 2. 使用RealDataProcessor标准化
processor = RealDataProcessor()
processed_df = processor.standardize_sales_data(df)

print(f"\n📊 步骤2：标准化后的数据")
print(f"   数据量: {len(processed_df)} 行 × {len(processed_df.columns)} 列")
print(f"   字段: {processed_df.columns.tolist()}")

# 3. 检查关键字段
key_fields = ['商品采购成本', '月售', '库存', '单品毛利']
print(f"\n🔍 检查关键字段:")
for field in key_fields:
    if field in processed_df.columns:
        print(f"   ✅ '{field}' 存在")
    else:
        print(f"   ❌ '{field}' 不存在")

# 4. 剔除耗材和咖啡
original_rows = len(processed_df)

# 剔除耗材
if '一级分类名' in processed_df.columns:
    processed_df = processed_df[processed_df['一级分类名'] != '耗材'].copy()
    print(f"\n🔴 已剔除耗材: {original_rows - len(processed_df)} 行")

# 剔除咖啡
if '渠道' in processed_df.columns:
    before = len(processed_df)
    processed_df = processed_df[~processed_df['渠道'].isin(['饿了么咖啡', '美团咖啡'])].copy()
    print(f"☕ 已剔除咖啡: {before - len(processed_df)} 行")

print(f"\n📊 最终数据量: {len(processed_df)} 行")

# 5. 再次检查关键字段
print(f"\n🔍 再次检查关键字段:")
for field in key_fields:
    if field in processed_df.columns:
        print(f"   ✅ '{field}' 存在")
        if pd.api.types.is_numeric_dtype(processed_df[field]):
            print(f"      总和: ¥{processed_df[field].sum():,.2f}")
    else:
        print(f"   ❌ '{field}' 不存在")

# 6. 测试订单聚合
print(f"\n📊 测试订单聚合:")
try:
    order_agg = processed_df.groupby('订单ID').agg({
        '商品实售价': 'sum',
        '商品采购成本': 'sum',
        '月售': 'sum',
    }).reset_index()
    print(f"   ✅ 聚合成功！订单数: {len(order_agg)}")
    print(f"   商品销售额: ¥{order_agg['商品实售价'].sum():,.2f}")
    print(f"   商品采购成本: ¥{order_agg['商品采购成本'].sum():,.2f}")
except Exception as e:
    print(f"   ❌ 聚合失败: {str(e)}")

print("\n" + "="*80)
