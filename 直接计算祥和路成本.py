import pandas as pd
import sys

print("="*60, flush=True)
print("开始读取祥和路数据...", flush=True)

# 直接读取Excel
df = pd.read_excel("实际数据/祥和路.xlsx")
print(f"✅ 读取成功", flush=True)

print(f"\n总行数: {len(df)}", flush=True)
print(f"总字段数: {len(df.columns)}", flush=True)

if '成本' in df.columns:
    total_cost = df['成本'].sum()
    print(f"\n💰 '成本'字段总和: {total_cost:,.2f}", flush=True)
    print(f"   非空行数: {df['成本'].notna().sum()}", flush=True)
    print(f"   零值行数: {(df['成本'] == 0).sum()}", flush=True)
    
if '商品采购成本' in df.columns:
    total_cost2 = df['商品采购成本'].sum()
    print(f"\n💰 '商品采购成本'字段总和: {total_cost2:,.2f}", flush=True)

print("="*60, flush=True)
