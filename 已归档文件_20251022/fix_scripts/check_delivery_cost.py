#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查配送成本计算逻辑"""

import pandas as pd
from pathlib import Path

# 查找实际数据目录中的Excel文件
data_dir = Path(r"实际数据")
excel_files = list(data_dir.glob("*.xlsx"))

if excel_files:
    # 读取第一个Excel文件
    file_path = excel_files[0]
    print(f"读取文件: {file_path.name}\n")
    
    df = pd.read_excel(file_path)
    
    # 显示配送相关字段的统计信息
    delivery_cols = ['物流配送费', '配送费减免金额', '用户支付配送费']
    
    print("=" * 60)
    print("【原始数据字段汇总（所有行）】")
    print("=" * 60)
    for col in delivery_cols:
        if col in df.columns:
            print(f"{col}: {df[col].sum():,.2f}")
    
    # 按订单聚合
    order_delivery = df.groupby('订单ID').agg({
        '物流配送费': 'first',
        '配送费减免金额': 'first', 
        '用户支付配送费': 'first'
    }).reset_index()
    
    print("\n" + "=" * 60)
    print("【按订单聚合后的总和】")
    print("=" * 60)
    for col in delivery_cols:
        print(f"{col}: {order_delivery[col].sum():,.2f}")
    
    # 尝试不同的配送成本计算方式
    print("\n" + "=" * 60)
    print("【不同的配送成本计算方式对比】")
    print("=" * 60)
    
    logistics = order_delivery['物流配送费'].sum()
    exemption = order_delivery['配送费减免金额'].sum()
    user_pay = order_delivery['用户支付配送费'].sum()
    
    print(f"物流配送费: {logistics:,.2f}")
    print(f"配送费减免: {exemption:,.2f}")
    print(f"用户支付配送费: {user_pay:,.2f}")
    print()
    
    # 方式1: 物流配送费 - 配送费减免
    calc1 = logistics - exemption
    print(f"方式1 (物流配送费 - 配送费减免)")
    print(f"  = {logistics:,.2f} - {exemption:,.2f}")
    print(f"  = {calc1:,.2f}")
    print()
    
    # 方式2: 配送费减免 + 物流配送费
    calc2 = exemption + logistics
    print(f"方式2 (配送费减免 + 物流配送费)")
    print(f"  = {exemption:,.2f} + {logistics:,.2f}")
    print(f"  = {calc2:,.2f}")
    print()
    
    # 方式3: 用户支付 - 配送费减免 - 物流配送费 (净成本)
    calc3 = user_pay - exemption - logistics
    print(f"方式3 (用户支付 - 配送费减免 - 物流配送费)")
    print(f"  = {user_pay:,.2f} - {exemption:,.2f} - {logistics:,.2f}")
    print(f"  = {calc3:,.2f}")
    print()
    
    # 检查哪个结果接近21,936
    print("=" * 60)
    print("【哪个计算结果接近 21,936？】")
    print("=" * 60)
    target = 21936
    results = {
        "方式1 (物流-减免)": calc1,
        "方式2 (减免+物流)": calc2,
        "方式3 (用户支付-减免-物流)": calc3
    }
    
    for name, value in results.items():
        diff = abs(value - target)
        print(f"{name}: {value:,.2f} (差异: {diff:,.2f})")
    
else:
    print("未找到Excel文件")
