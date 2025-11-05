"""
静默版订单导入 - 减少输出，便于后台运行
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import glob

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db
from database.models import Order
from 真实数据处理器 import RealDataProcessor


def import_orders_quiet(df: pd.DataFrame):
    """静默导入订单"""
    db = next(get_db())
    stats = {'total': len(df), 'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
    
    try:
        print(f"开始导入 {len(df):,} 条记录...")
        
        for idx, row in df.iterrows():
            try:
                order_id = str(row.get('订单ID', ''))
                if not order_id or order_id == 'nan':
                    stats['skipped'] += 1
                    continue
                
                existing = db.query(Order).filter(Order.order_id == order_id).first()
                
                order_data = {
                    'order_id': order_id,
                    'date': pd.to_datetime(row['日期']) if pd.notna(row.get('日期')) else None,
                    'store_name': str(row.get('门店名称', 'UNKNOWN')),
                    'product_name': str(row.get('商品名称', '')),
                    'barcode': str(row.get('商品条形码', '')) if pd.notna(row.get('商品条形码')) else None,
                    'category_level1': str(row.get('一级分类名', '')) if pd.notna(row.get('一级分类名')) else None,
                    'category_level3': str(row.get('三级分类名', '')) if pd.notna(row.get('三级分类名')) else None,
                    'price': float(row.get('商品实售价', 0)) if pd.notna(row.get('商品实售价')) else 0,
                    'cost': float(row.get('商品采购成本', 0)) if pd.notna(row.get('商品采购成本')) else None,
                    'quantity': int(row.get('销售数量', 1)) if pd.notna(row.get('销售数量')) else 1,
                    'amount': float(row.get('实收金额', 0)) if pd.notna(row.get('实收金额')) else 0,
                    'channel': str(row.get('渠道', '')) if pd.notna(row.get('渠道')) else None,
                }
                
                if existing:
                    for key, value in order_data.items():
                        if key != 'order_id':
                            setattr(existing, key, value)
                    existing.updated_at = datetime.now()
                    stats['updated'] += 1
                else:
                    db.add(Order(**order_data))
                    stats['inserted'] += 1
                
                db.commit()
                
                # 每1000条显示一次进度
                if (idx + 1) % 1000 == 0:
                    print(f"进度: {idx+1:,}/{len(df):,} ({((idx+1)/len(df)*100):.1f}%)")
                    
            except Exception as e:
                db.rollback()
                stats['errors'] += 1
                continue
        
        print(f"\n完成! 总:{stats['total']:,} | 新增:{stats['inserted']:,} | 更新:{stats['updated']:,} | 错误:{stats['errors']:,}")
        return stats
        
    finally:
        db.close()


# 主程序
data_dir = r"D:\Python1\O2O_Analysis\O2O数据分析\测算模型\实际数据"
excel_files = glob.glob(f"{data_dir}\\*.xlsx")

if excel_files:
    print("加载数据...")
    df = pd.read_excel(excel_files[0])
    
    print("标准化...")
    processor = RealDataProcessor()
    df = processor.standardize_sales_data(df)
    
    print("过滤...")
    df = df[df.get('一级分类名', '') != '耗材'].copy()
    df = df[~df.get('渠道', '').str.contains('咖啡', na=False)].copy()
    
    print(f"最终数据: {len(df):,} 行\n")
    import_orders_quiet(df)
    
    # 验证
    db = next(get_db())
    count = db.query(Order).count()
    db.close()
    print(f"\n数据库订单总数: {count:,}")
