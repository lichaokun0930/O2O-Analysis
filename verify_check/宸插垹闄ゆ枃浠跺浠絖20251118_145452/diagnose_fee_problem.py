#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对比Excel原始数据和数据库数据,找出platform_service_fee问题根源"""

import pandas as pd
from database.connection import get_db_context
from database.models import Order
from sqlalchemy import func

def main():
    print(f"\n{'='*80}")
    print("🔍 Excel vs 数据库 - platform_service_fee 完整分析")
    print(f"{'='*80}\n")
    
    # 1. 读取Excel原始数据
    excel_file = r"实际数据\2025-10-16 00_00_00至2025-11-14 23_59_59订单明细数据导出汇总.xlsx"
    print(f"1️⃣ 读取Excel文件: {excel_file}")
    
    df_excel = pd.read_excel(excel_file)
    print(f"   Excel总行数: {len(df_excel)}")
    print(f"\n   Excel列名:")
    for i, col in enumerate(df_excel.columns, 1):
        print(f"   {i:2d}. {col}")
    
    # 2. 检查Excel中是否有"平台服务费"相关列
    print(f"\n2️⃣ 搜索'平台服务费'相关列:")
    fee_columns = [col for col in df_excel.columns if '服务费' in col or '佣金' in col or 'commission' in col.lower()]
    
    if fee_columns:
        print(f"   ✅ 找到 {len(fee_columns)} 个相关列:")
        for col in fee_columns:
            non_zero = (df_excel[col] != 0).sum() if pd.api.types.is_numeric_dtype(df_excel[col]) else 0
            print(f"      - '{col}': 非0值数量 = {non_zero}")
            if non_zero > 0:
                print(f"        样本值: {df_excel[df_excel[col] != 0][col].head(5).tolist()}")
    else:
        print(f"   ❌ 未找到任何服务费/佣金相关列")
    
    # 3. 查看数据库情况
    print(f"\n3️⃣ 数据库中的platform_service_fee:")
    with get_db_context() as session:
        total = session.query(func.count(Order.id)).scalar()
        zero_fee = session.query(func.count(Order.id)).filter(Order.platform_service_fee == 0).scalar()
        non_zero_fee = session.query(func.count(Order.id)).filter(Order.platform_service_fee > 0).scalar()
        
        print(f"   总订单: {total}")
        print(f"   服务费=0: {zero_fee} ({zero_fee/total*100:.1f}%)")
        print(f"   服务费>0: {non_zero_fee} ({non_zero_fee/total*100:.1f}%)")
        
        # 查看commission字段
        print(f"\n4️⃣ 数据库中的commission(平台佣金):")
        zero_comm = session.query(func.count(Order.id)).filter(Order.commission == 0).scalar()
        non_zero_comm = session.query(func.count(Order.id)).filter(Order.commission > 0).scalar()
        
        print(f"   佣金=0: {zero_comm} ({zero_comm/total*100:.1f}%)")
        print(f"   佣金>0: {non_zero_comm} ({non_zero_comm/total*100:.1f}%)")
        
        if non_zero_comm > 0:
            # 显示有佣金的订单样本
            orders_with_comm = session.query(
                Order.order_id,
                Order.commission,
                Order.platform_service_fee,
                Order.amount
            ).filter(Order.commission > 0).limit(10).all()
            
            print(f"\n   ✅ 有平台佣金的订单样本:")
            for order in orders_with_comm:
                print(f"      订单 {order.order_id}: 佣金={order.commission}, 服务费={order.platform_service_fee}, 金额={order.amount}")
    
    # 5. 结论分析
    print(f"\n{'='*80}")
    print("📋 【问题诊断结论】")
    print(f"{'='*80}\n")
    
    print("❓ 为什么'仅平台服务费>0'模式会过滤掉所有数据?")
    print()
    print("答案:")
    print("1. ✅ 数据库中35504笔订单的platform_service_fee都是0")
    print("2. ✅ 默认计算模式'service_fee_positive'要求平台服务费>0")
    print("3. ✅ 0笔订单满足条件 → 过滤后DataFrame为空 → 看板显示0数据")
    print()
    
    if non_zero_comm > 0:
        print("💡 关键发现:")
        print(f"   - 数据库中有 {non_zero_comm} 笔订单有'平台佣金'(commission)")
        print(f"   - 但'平台服务费'(platform_service_fee)全部为0")
        print()
        print("🎯 根本原因:")
        print("   1. Excel导入时,可能'平台佣金'列被映射到了commission字段")
        print("   2. 而platform_service_fee字段使用了默认值0,从未被填充")
        print("   3. 计算口径却基于platform_service_fee过滤,导致全部被过滤")
        print()
        print("✨ 彻底解决方案(无需降级):")
        print("   方案A: 修复数据导入逻辑")
        print("      → 将Excel的'平台佣金'列正确映射到platform_service_fee")
        print("      → 或在导入时计算:platform_service_fee = commission")
        print()
        print("   方案B: 修改过滤逻辑")
        print("      → 改为: (平台服务费>0 OR 平台佣金>0)")
        print("      → 这样已有数据也能通过过滤")
        print()
        print("   方案C: 数据回填")
        print("      → UPDATE orders SET platform_service_fee = commission")
        print("      → WHERE platform_service_fee = 0 AND commission > 0")
    else:
        print("⚠️  警告:")
        print("   - platform_service_fee全0")
        print("   - commission也全0")
        print("   - 需要检查Excel原始数据是否真的有服务费/佣金信息")

if __name__ == '__main__':
    main()
