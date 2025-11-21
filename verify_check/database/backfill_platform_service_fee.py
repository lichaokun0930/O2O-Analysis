#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回填历史数据的platform_service_fee字段
将Excel中的'平台服务费'数据正确导入到数据库

⚠️ 可选执行: 
   - 如果只是想让现有数据可用,不需要执行此脚本(过滤逻辑已修复)
   - 如果想让历史数据的platform_service_fee字段准确,可以执行此脚本
"""

import pandas as pd
from database.connection import get_db_context
from database.models import Order
from sqlalchemy import update
from datetime import datetime

def backfill_from_excel(excel_file: str):
    """从Excel重新读取平台服务费数据并回填到数据库"""
    
    print(f"\n{'='*80}")
    print("🔧 回填历史数据 - platform_service_fee 字段")
    print(f"{'='*80}\n")
    
    # 1. 读取Excel
    print(f"1️⃣ 读取Excel: {excel_file}")
    df = pd.read_excel(excel_file)
    print(f"   总行数: {len(df)}")
    
    # 检查是否有必要的列
    if '订单ID' not in df.columns or '平台服务费' not in df.columns:
        print(f"   ❌ Excel缺少必要的列: '订单ID' 或 '平台服务费'")
        return
    
    # 2. 准备更新数据
    print(f"\n2️⃣ 准备更新数据...")
    df_update = df[['订单ID', '平台服务费']].copy()
    df_update = df_update[pd.notna(df_update['平台服务费'])]  # 过滤掉空值
    df_update = df_update[df_update['平台服务费'] != 0]  # 过滤掉0值
    
    print(f"   需要更新的订单数: {len(df_update)} (平台服务费>0)")
    
    if len(df_update) == 0:
        print(f"   ⚠️  没有需要更新的数据")
        return
    
    # 3. 批量更新数据库
    print(f"\n3️⃣ 开始批量更新数据库...")
    with get_db_context() as session:
        updated_count = 0
        not_found_count = 0
        
        for idx, row in df_update.iterrows():
            order_id = str(row['订单ID'])
            service_fee = float(row['平台服务费'])
            
            # 查找订单
            order = session.query(Order).filter(Order.order_id == order_id).first()
            if order:
                order.platform_service_fee = service_fee
                updated_count += 1
                
                if updated_count % 1000 == 0:
                    session.commit()
                    print(f"   进度: {updated_count}/{len(df_update)}")
            else:
                not_found_count += 1
        
        # 最后提交
        session.commit()
        
        print(f"\n4️⃣ 更新完成:")
        print(f"   ✅ 成功更新: {updated_count} 笔订单")
        print(f"   ⚠️  未找到: {not_found_count} 笔订单")
    
    # 5. 验证结果
    print(f"\n5️⃣ 验证更新结果...")
    with get_db_context() as session:
        from sqlalchemy import func
        
        total = session.query(func.count(Order.id)).scalar()
        zero_fee = session.query(func.count(Order.id)).filter(Order.platform_service_fee == 0).scalar()
        non_zero_fee = session.query(func.count(Order.id)).filter(Order.platform_service_fee > 0).scalar()
        
        print(f"   总订单: {total}")
        print(f"   平台服务费=0: {zero_fee} ({zero_fee/total*100:.1f}%)")
        print(f"   平台服务费>0: {non_zero_fee} ({non_zero_fee/total*100:.1f}%)")
    
    print(f"\n✅ 回填完成!")

def main():
    """主函数"""
    # 你的Excel文件路径
    excel_file = r"实际数据\2025-10-16 00_00_00至2025-11-14 23_59_59订单明细数据导出汇总.xlsx"
    
    print("⚠️  注意:")
    print("   - 此脚本将从Excel重新读取'平台服务费'数据并更新到数据库")
    print("   - 不会影响其他字段")
    print("   - 已有的platform_service_fee值会被覆盖")
    print()
    
    choice = input("是否继续? (y/n): ").strip().lower()
    if choice == 'y':
        backfill_from_excel(excel_file)
    else:
        print("已取消")

if __name__ == '__main__':
    main()
