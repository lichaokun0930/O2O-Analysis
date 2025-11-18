# -*- coding: utf-8 -*-
"""
祥和路店数据日期修复脚本
从原始Excel重新读取正确的日期并更新数据库
"""

import sys
import pandas as pd
from datetime import datetime
from pathlib import Path
from sqlalchemy import func

sys.path.insert(0, '.')

from database.connection import get_db
from database.models import Order

print("="*80)
print("📅 祥和路店数据日期修复")
print("="*80)

# 请替换为实际的Excel文件路径
excel_file = input("\n请输入祥和路店Excel文件的完整路径: ").strip().strip('"')

if not Path(excel_file).exists():
    print(f"❌ 文件不存在: {excel_file}")
    exit(1)

print(f"\n📂 读取Excel文件: {excel_file}")
df = pd.read_excel(excel_file)

print(f"✅ 加载了 {len(df):,} 行数据")
print(f"\n列名: {list(df.columns)}")

# 查找日期列
date_columns = [col for col in df.columns if any(keyword in col for keyword in ['日期', '时间', 'date', 'time'])]
print(f"\n可能的日期列: {date_columns}")

if not date_columns:
    print("❌ 未找到日期列，请手动指定")
    date_col = input("请输入日期列名: ").strip()
else:
    date_col = date_columns[0]
    print(f"✅ 使用日期列: {date_col}")

# 检查日期范围
df[date_col] = pd.to_datetime(df[date_col])
print(f"\n📅 日期范围: {df[date_col].min()} 至 {df[date_col].max()}")
print(f"📊 天数: {df[date_col].nunique()} 天")

# 确认
confirm = input(f"\n确认要更新数据库中'惠宜选超市（徐州祥和路店）'的订单日期吗? (yes/no): ")
if confirm.lower() != 'yes':
    print("❌ 已取消")
    exit(0)

# 更新数据库
db = next(get_db())

try:
    updated_count = 0
    error_count = 0
    
    print(f"\n🔄 开始更新...")
    
    for idx, row in df.iterrows():
        try:
            order_id = str(row['订单ID'])
            new_date = row[date_col]
            
            # 查找订单
            order = db.query(Order).filter(
                Order.order_id == order_id,
                Order.store_name == '惠宜选超市（徐州祥和路店）'
            ).first()
            
            if order:
                order.date = new_date
                updated_count += 1
                
                if updated_count % 1000 == 0:
                    db.commit()
                    print(f"   已更新 {updated_count:,} 条...")
            
        except Exception as e:
            error_count += 1
            if error_count <= 5:
                print(f"   ⚠️  订单 {order_id} 更新失败: {e}")
            continue
    
    db.commit()
    
    print(f"\n✅ 更新完成!")
    print(f"   成功: {updated_count:,} 条")
    print(f"   失败: {error_count:,} 条")
    
    # 验证
    print(f"\n🔍 验证更新结果...")
    result = db.query(
        func.min(Order.date).label('min_date'),
        func.max(Order.date).label('max_date'),
        func.count(func.distinct(func.date(Order.date))).label('days')
    ).filter(Order.store_name == '惠宜选超市（徐州祥和路店）').first()
    
    print(f"   新的日期范围: {result.min_date} 至 {result.max_date}")
    print(f"   天数: {result.days} 天")

except Exception as e:
    db.rollback()
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

print("\n" + "="*80)
