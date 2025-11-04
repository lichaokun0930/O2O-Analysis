import pandas as pd
import sys

# 加载数据
file_path = r"门店数据\2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"
df = pd.read_excel(file_path)

print("=" * 80)
print("📊 数据列名：")
print(df.columns.tolist())
print("\n" + "=" * 80)

# 查找成本相关字段
cost_columns = [col for col in df.columns if '成本' in col or '采购' in col]
print(f"💰 成本相关字段：{cost_columns}")

# 检查"成本"字段
if '成本' in df.columns:
    print("\n✅ 找到'成本'字段")
    print(f"   数据类型: {df['成本'].dtype}")
    print(f"   非空值数量: {df['成本'].notna().sum()} / {len(df)}")
    print(f"   总和: ¥{df['成本'].sum():,.2f}")
    print(f"   平均值: ¥{df['成本'].mean():.2f}")
    print(f"\n   样本数据（前10行）:")
    print(df[['商品名称', '成本', '商品实售价']].head(10).to_string())
    
    # 检查有多少行成本为0或NaN
    zero_cost = (df['成本'] == 0).sum()
    nan_cost = df['成本'].isna().sum()
    print(f"\n   ⚠️ 成本为0的行数: {zero_cost}")
    print(f"   ⚠️ 成本为NaN的行数: {nan_cost}")
else:
    print("\n❌ 未找到'成本'字段")

# 检查"商品采购成本"字段
if '商品采购成本' in df.columns:
    print("\n✅ 找到'商品采购成本'字段")
    print(f"   数据类型: {df['商品采购成本'].dtype}")
    print(f"   非空值数量: {df['商品采购成本'].notna().sum()} / {len(df)}")
    print(f"   总和: ¥{df['商品采购成本'].sum():,.2f}")
else:
    print("\n❌ 未找到'商品采购成本'字段")

print("\n" + "=" * 80)
