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

# 直接使用祥和路店Excel文件
excel_file = Path('实际数据/祥和路.xlsx')

if not excel_file.exists():
    print(f"\n❌ 文件不存在: {excel_file}")
    sys.exit(1)

print(f"\n📂 找到文件: {excel_file}")

# 读取Excel
df = pd.read_excel(excel_file)
print(f"📊 数据行数: {len(df):,}")
print(f"📋 字段列表: {df.columns.tolist()[:10]}...")

# 检查关键字段
required_fields = ['订单ID', '利润额', '平台服务费']
missing = [f for f in required_fields if f not in df.columns]
if missing:
    print(f"\n❌ 缺少字段: {missing}")
    print(f"可用字段: {df.columns.tolist()}")
    sys.exit(1)

print("\n" + "="*80)
print("📊 利润额计算验证")
print("="*80)

# 方法1: 直接sum所有行的利润额
profit_all_rows = df['利润额'].sum()
print(f"\n方法1 - 直接sum所有行:")
print(f"   利润额: ¥{profit_all_rows:,.2f}")
print(f"   总行数: {len(df):,}")

# 方法2: 按订单ID聚合后sum (避免重复计算)
profit_by_order = df.groupby('订单ID')['利润额'].first().sum()
order_count = df['订单ID'].nunique()
print(f"\n方法2 - 按订单ID聚合:")
print(f"   利润额: ¥{profit_by_order:,.2f}")
print(f"   订单数: {order_count:,}")

# 方法3: 剔除平台服务费=0的订单 (只看平台服务费,不看平台佣金)
df_with_fee = df[df['平台服务费'] != 0].copy()
profit_no_zero_fee_rows = df_with_fee['利润额'].sum()
profit_no_zero_fee_orders = df_with_fee.groupby('订单ID')['利润额'].first().sum()

print(f"\n方法3 - 剔除平台服务费=0的订单 (用户逻辑):")
print(f"   保留订单数: {df_with_fee['订单ID'].nunique():,} / {order_count:,}")
print(f"   剔除订单数: {order_count - df_with_fee['订单ID'].nunique():,}")
print(f"   利润额(按行): ¥{profit_no_zero_fee_rows:,.2f}")
print(f"   利润额(按订单): ¥{profit_no_zero_fee_orders:,.2f}")

# 方法4: 系统逻辑 (平台服务费>0 或 平台佣金>0)
if '平台佣金' in df.columns:
    df_system_logic = df[(df['平台服务费'] > 0) | (df['平台佣金'] > 0)].copy()
    profit_system_orders = df_system_logic.groupby('订单ID')['利润额'].first().sum()
    
    print(f"\n方法4 - 系统逻辑 (平台服务费>0 或 平台佣金>0):")
    print(f"   保留订单数: {df_system_logic['订单ID'].nunique():,} / {order_count:,}")
    print(f"   利润额(按订单): ¥{profit_system_orders:,.2f}")
    print(f"   与用户逻辑差异: ¥{profit_system_orders - profit_no_zero_fee_orders:,.2f}")
else:
    print(f"\n⚠️ Excel中没有'平台佣金'字段,无法测试系统逻辑")

# 检查平台服务费=0的订单
zero_fee_orders = df[df['平台服务费'] == 0]['订单ID'].unique()
print(f"\n平台服务费=0的订单:")
print(f"   订单数: {len(zero_fee_orders):,}")
if len(zero_fee_orders) > 0:
    zero_fee_profit = df[df['订单ID'].isin(zero_fee_orders)].groupby('订单ID')['利润额'].first().sum()
    print(f"   利润额: ¥{zero_fee_profit:,.2f}")
    print(f"   (负值表示退款订单)")

print("\n" + "="*80)
print("📋 用户提供的数据对比")
print("="*80)
print(f"用户数据 - 不剔除平台服务费=0: ¥56,341")
print(f"用户数据 - 剔除平台服务费=0:    ¥55,921")
print(f"差异(退款订单负利润):           ¥{56341 - 55921:,}")

print(f"\n系统计算 - 方法1(所有行):      ¥{profit_all_rows:,.2f}")
print(f"系统计算 - 方法2(按订单):      ¥{profit_by_order:,.2f}")
print(f"系统计算 - 方法3(剔除后按订单): ¥{profit_no_zero_fee_orders:,.2f}")

print("\n" + "="*80)
print("💡 差异分析与系统逻辑验证")
print("="*80)

# 验证系统逻辑
print("\n系统计算逻辑模拟:")
print("1. 从Excel读取 -> 所有订单利润额(按订单聚合)")
print(f"   结果: ¥{profit_by_order:,.2f}")
print(f"   目标: ¥56,341")
print(f"   差异: ¥{profit_by_order - 56341:,.2f}")

print("\n2. 剔除平台服务费=0的订单 -> 真实利润")
print(f"   结果: ¥{profit_no_zero_fee_orders:,.2f}")
print(f"   目标: ¥55,921")
print(f"   差异: ¥{profit_no_zero_fee_orders - 55921:,.2f}")

if abs(profit_by_order - 56341) < 10:
    print("\n✅ 步骤1验证通过: 系统正确读取了Excel所有订单利润")
elif abs(profit_no_zero_fee_orders - 55921) < 10:
    print("\n✅ 步骤2验证通过: 系统正确剔除了退货单")
else:
    print("\n❌ 系统计算与Excel数据不一致")
    print("\n可能原因:")
    print("   1. 订单ID字段在导入时被修改(导致聚合错误)")
    print("   2. 利润额字段在导入时被重新计算(而非直接使用Excel值)")
    print("   3. 平台服务费字段映射错误")
    
print("\n" + "="*80)
print("🔍 下一步: 检查数据库中的数据")
print("="*80)
print("建议: 上传祥和路Excel后,从数据库读取验证:")
print("1. 订单数是否匹配")
print("2. 利润额字段是否与Excel一致")  
print("3. 平台服务费=0的订单数是否匹配")
print("="*80)
