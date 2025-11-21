# -*- coding: utf-8 -*-
"""
重新导入祥和路店数据（清理旧数据并导入新数据）
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
from sqlalchemy import func

sys.path.insert(0, '.')

from database.connection import get_db
from database.models import Order, Product
from database.batch_import import BatchDataImporter

print("="*80)
print("🔄 祥和路店数据重新导入")
print("="*80)

store_name = "惠宜选超市（徐州祥和路店）"

# Step 1: 获取Excel文件路径
excel_file = input("\n📂 请输入祥和路店Excel文件的完整路径: ").strip().strip('"')

if not Path(excel_file).exists():
    print(f"❌ 文件不存在: {excel_file}")
    exit(1)

# Step 2: 预览Excel数据
print(f"\n📊 预览Excel数据...")
df = pd.read_excel(excel_file)
print(f"   总行数: {len(df):,}")
print(f"   列名: {list(df.columns)[:10]}...")

# 查找日期列
date_cols = [col for col in df.columns if any(kw in col for kw in ['日期', '时间', 'date', 'time'])]
print(f"\n📅 可能的日期列: {date_cols}")

if date_cols:
    date_col = date_cols[0]
    df_temp = df.copy()
    df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
    min_date = df_temp[date_col].min()
    max_date = df_temp[date_col].max()
    days = df_temp[date_col].dt.date.nunique()
    
    print(f"\n   使用列: {date_col}")
    print(f"   日期范围: {min_date} 至 {max_date}")
    print(f"   天数: {days} 天")

# Step 3: 确认删除旧数据
db = next(get_db())
old_count = db.query(Order).filter(Order.store_name == store_name).count()
print(f"\n⚠️  数据库中现有 {old_count:,} 条 '{store_name}' 的订单")

confirm = input(f"\n确认删除这些旧数据并重新导入? (yes/no): ")
if confirm.lower() != 'yes':
    print("❌ 已取消")
    db.close()
    exit(0)

# Step 4: 删除旧订单数据
print(f"\n🗑️  删除旧订单数据...")
try:
    deleted = db.query(Order).filter(Order.store_name == store_name).delete()
    db.commit()
    print(f"   ✅ 已删除 {deleted:,} 条订单")
except Exception as e:
    db.rollback()
    print(f"   ❌ 删除失败: {e}")
    db.close()
    exit(1)
finally:
    db.close()

# Step 5: 使用修复后的导入器重新导入
print(f"\n📥 开始重新导入...")
importer = BatchDataImporter(str(Path(excel_file).parent))

try:
    # 直接导入单个文件
    success = importer.import_file(excel_file)
    
    if success:
        print(f"\n✅ 导入成功!")
        
        # 验证新数据
        db = next(get_db())
        try:
            result = db.query(
                func.count(Order.id).label('count'),
                func.min(Order.date).label('min_date'),
                func.max(Order.date).label('max_date'),
                func.count(func.distinct(func.date(Order.date))).label('days')
            ).filter(Order.store_name == store_name).first()
            
            print(f"\n📊 新数据统计:")
            print(f"   订单数: {result.count:,}")
            print(f"   日期范围: {result.min_date} 至 {result.max_date}")
            print(f"   天数: {result.days} 天")
        finally:
            db.close()
    else:
        print(f"\n❌ 导入失败")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("完成")
print("="*80)
