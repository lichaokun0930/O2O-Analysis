"""
检查Excel文件的列名
"""
import pandas as pd
from pathlib import Path

excel_file = Path("实际数据/2025-10-25 00_00_00至2025-11-23 23_59_59订单明细数据导出汇总.xlsx")

if not excel_file.exists():
    print(f"❌ 文件不存在: {excel_file}")
    exit(1)

print("="*80)
print("🔍 检查Excel文件列名")
print("="*80)

df = pd.read_excel(excel_file)

print(f"\n📂 文件: {excel_file.name}")
print(f"📊 总行数: {len(df):,}")
print(f"📋 总列数: {len(df.columns)}")

print(f"\n📋 所有列名:")
for i, col in enumerate(df.columns, 1):
    print(f"   {i:2d}. {col}")

# 检查关键列
key_columns = ['门店名称', '门店', '渠道', '订单ID', '商品名称', '成本', '商品采购成本']
print(f"\n🔍 检查关键列:")
for col in key_columns:
    if col in df.columns:
        print(f"   ✅ {col}")
        # 显示前3个值
        sample = df[col].dropna().head(3).tolist()
        if sample:
            print(f"      示例: {sample}")
    else:
        print(f"   ❌ {col} (不存在)")

print(f"\n{'='*80}")
