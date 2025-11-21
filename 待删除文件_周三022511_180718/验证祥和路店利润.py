#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证祥和路店利润额计算"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path.cwd()))

print("="*80)
print("🔍 验证祥和路店利润额计算")
print("="*80)

# 查找祥和路店的Excel文件
data_dir = Path('实际数据')
if not data_dir.exists():
    print(f"❌ 数据目录不存在: {data_dir}")
    sys.exit(1)

# 列出所有Excel文件
excel_files = list(data_dir.glob('*.xlsx')) + list(data_dir.glob('*.xls'))
print(f"\n📂 找到 {len(excel_files)} 个Excel文件:")
for i, f in enumerate(excel_files, 1):
    print(f"   {i}. {f.name}")

# 尝试找到祥和路店的文件
xianghe_file = None
for f in excel_files:
    if '祥和' in f.name:
        xianghe_file = f
        break

if not xianghe_file:
    print("\n⚠️ 未找到包含'祥和'的文件,尝试加载第一个文件...")
    if excel_files:
        xianghe_file = excel_files[0]
    else:
        print("❌ 没有可用的Excel文件")
        sys.exit(1)

print(f"\n📊 加载文件: {xianghe_file.name}")
df = pd.read_excel(xianghe_file)

print(f"✅ 数据加载成功: {len(df):,} 行")
print(f"📋 字段: {df.columns.tolist()}")

# 检查关键字段
required_fields = ['利润额', '平台服务费', '订单ID']
missing = [f for f in required_fields if f not in df.columns]
if missing:
    print(f"\n❌ 缺少字段: {missing}")
    print(f"可用字段: {df.columns.tolist()}")
    sys.exit(1)

print("\n" + "="*80)
print("📊 利润额统计")
print("="*80)

# 1. 不剔除平台服务费=0的订单
profit_all = df['利润额'].sum()
print(f"\n【方法1: 直接sum所有行的利润额】")
print(f"   总利润: ¥{profit_all:,.2f}")

# 2. 按订单聚合(避免重复计算)
order_profit = df.groupby('订单ID')['利润额'].first().sum()
print(f"\n【方法2: 按订单ID聚合后sum】")
print(f"   总利润: ¥{order_profit:,.2f}")
print(f"   订单数: {df['订单ID'].nunique():,}")

# 3. 剔除平台服务费=0的订单
df_no_zero = df[df['平台服务费'] != 0].copy()
profit_no_zero_direct = df_no_zero['利润额'].sum()
profit_no_zero_grouped = df_no_zero.groupby('订单ID')['利润额'].first().sum()

print(f"\n【方法3: 剔除平台服务费=0后直接sum】")
print(f"   总利润: ¥{profit_no_zero_direct:,.2f}")
print(f"   剔除行数: {len(df) - len(df_no_zero):,}")

print(f"\n【方法4: 剔除平台服务费=0后按订单聚合】")
print(f"   总利润: ¥{profit_no_zero_grouped:,.2f}")
print(f"   剔除订单数: {df['订单ID'].nunique() - df_no_zero['订单ID'].nunique():,}")

# 4. 分析平台服务费=0的订单
zero_fee_df = df[df['平台服务费'] == 0].copy()
if not zero_fee_df.empty:
    zero_fee_profit = zero_fee_df['利润额'].sum()
    zero_fee_profit_grouped = zero_fee_df.groupby('订单ID')['利润额'].first().sum()
    
    print(f"\n【平台服务费=0的订单(退货单)】")
    print(f"   订单数: {zero_fee_df['订单ID'].nunique():,}")
    print(f"   数据行数: {len(zero_fee_df):,}")
    print(f"   直接sum利润: ¥{zero_fee_profit:,.2f}")
    print(f"   按订单聚合利润: ¥{zero_fee_profit_grouped:,.2f}")
    
    # 显示几个退货单示例
    print(f"\n   退货单示例(前3个订单):")
    for order_id in zero_fee_df['订单ID'].unique()[:3]:
        order_data = zero_fee_df[zero_fee_df['订单ID'] == order_id]
        order_profit = order_data['利润额'].iloc[0] if len(order_data) > 0 else 0
        print(f"      订单 {order_id}: 利润={order_profit:.2f}, 商品数={len(order_data)}")

print("\n" + "="*80)
print("📋 与用户数据对比")
print("="*80)

print(f"\n【用户提供数据】")
print(f"   不剔除平台服务费=0: ¥56,341")
print(f"   剔除平台服务费=0: ¥55,921")
print(f"   差异: ¥420 (退货单负利润)")

print(f"\n【系统计算数据(按订单聚合)】")
print(f"   不剔除平台服务费=0: ¥{order_profit:,.2f}")
print(f"   剔除平台服务费=0: ¥{profit_no_zero_grouped:,.2f}")
if not zero_fee_df.empty:
    print(f"   差异: ¥{zero_fee_profit_grouped:,.2f}")

print(f"\n【差异分析】")
diff_all = 56341 - order_profit
diff_no_zero = 55921 - profit_no_zero_grouped
print(f"   不剔除时差异: ¥{diff_all:,.2f}")
print(f"   剔除后差异: ¥{diff_no_zero:,.2f}")

if abs(diff_all) < 0.01 and abs(diff_no_zero) < 0.01:
    print(f"\n✅ 数据完全一致!")
elif abs(diff_all) < 100:
    print(f"\n✅ 数据基本一致(差异<¥100)")
else:
    print(f"\n❌ 数据存在较大差异,需要进一步检查")

print("\n" + "="*80)
