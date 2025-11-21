"""
简化版订单导入 - 使用逐行INSERT处理重复
避免复杂的UPSERT语句
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import glob

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db
from database.models import Order
from 真实数据处理器 import RealDataProcessor


def import_orders_simple(df: pd.DataFrame, batch_size: int = 500):
    """
    简单方式导入订单：逐条检查是否存在，存在则更新，不存在则插入
    
    Args:
        df: 订单数据
        batch_size: 每批提交数量
    """
    db = next(get_db())
    stats = {
        'total': len(df),
        'inserted': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    
    try:
        print(f"\n[START] 总记录数: {len(df):,}")
        print("="*60)
        
        batch_count = 0
        for idx, row in df.iterrows():
            try:
                # 提取数据
                order_id = str(row.get('订单ID', ''))
                if not order_id or order_id == 'nan':
                    stats['skipped'] += 1
                    continue
                
                # 检查是否已存在
                existing = db.query(Order).filter(Order.order_id == order_id).first()
                
                # 准备数据
                order_data = {
                    'order_id': order_id,
                    'date': pd.to_datetime(row['日期']) if pd.notna(row.get('日期')) else None,
                    'store_name': str(row.get('门店名称', 'UNKNOWN')),
                    'product_name': str(row.get('商品名称', '')),
                    'barcode': str(row.get('商品条形码', '')) if pd.notna(row.get('商品条形码')) else None,
                    'category_level1': str(row.get('一级分类名', '')) if pd.notna(row.get('一级分类名')) else None,
                    'category_level3': str(row.get('三级分类名', '')) if pd.notna(row.get('三级分类名')) else None,
                    'price': float(row.get('商品实售价', 0)) if pd.notna(row.get('商品实售价')) else 0,
                    'original_price': float(row.get('商品原价', 0)) if pd.notna(row.get('商品原价')) else None,
                    'cost': float(row.get('商品采购成本', 0)) if pd.notna(row.get('商品采购成本')) else None,
                    'actual_price': float(row.get('实收价格', 0)) if pd.notna(row.get('实收价格')) else None,
                    'quantity': int(row.get('销售数量', 1)) if pd.notna(row.get('销售数量')) else 1,
                    'amount': float(row.get('实收金额', 0)) if pd.notna(row.get('实收金额')) else 0,
                    'delivery_fee': float(row.get('物流配送费', 0)) if pd.notna(row.get('物流配送费')) else 0,
                    'commission': float(row.get('平台佣金', 0)) if pd.notna(row.get('平台佣金')) else 0,
                    'platform_service_fee': float(row.get('平台服务费', 0)) if pd.notna(row.get('平台服务费')) else 0,  # 修复:正确映射平台服务费字段
                    'channel': str(row.get('渠道', '')) if pd.notna(row.get('渠道')) else None,
                    'scene': str(row.get('场景', '')) if pd.notna(row.get('场景')) else None,
                    'time_period': str(row.get('时段', '')) if pd.notna(row.get('时段')) else None,
                    'address': str(row.get('收货地址', ''))[:500] if pd.notna(row.get('收货地址')) else None,  # 限制长度
                }
                
                if existing:
                    # 更新现有记录
                    for key, value in order_data.items():
                        if key != 'order_id':  # 不更新主键
                            setattr(existing, key, value)
                    existing.updated_at = datetime.now()
                    stats['updated'] += 1
                else:
                    # 插入新记录
                    new_order = Order(**order_data)
                    db.add(new_order)
                    stats['inserted'] += 1
                
                # 立即提交每一条（避免同批次内的重复ID冲突）
                try:
                    db.commit()
                except Exception as commit_error:
                    db.rollback()
                    stats['errors'] += 1
                    if stats['errors'] <= 10:
                        print(f"[ERROR] 提交失败 {order_id}: {str(commit_error)[:60]}")
                
                batch_count += 1
                
                # 每批显示进度
                if batch_count >= batch_size:
                    print(f"[PROGRESS] {idx+1:,}/{len(df):,} | 插入:{stats['inserted']} 更新:{stats['updated']}")
                    batch_count = 0
                    
            except Exception as e:
                stats['errors'] += 1
                if stats['errors'] <= 10:  # 打印前10个错误
                    print(f"[ERROR] 行 {idx}: {str(e)[:80]}")
                continue
        
        # 最后检查（不需要再提交了，每条都已提交）
        print(f"\n[PROGRESS] 处理完成")
        
        print("\n" + "="*60)
        print("[COMPLETE] 导入统计:")
        print(f"   总记录: {stats['total']:,}")
        print(f"   新插入: {stats['inserted']:,}")
        print(f"   已更新: {stats['updated']:,}")
        print(f"   跳过: {stats['skipped']:,}")
        print(f"   错误: {stats['errors']:,}")
        print("="*60)
        
        return stats
        
    except Exception as e:
        db.rollback()
        print(f"\n[FATAL ERROR] {e}")
        raise
    finally:
        db.close()


def main():
    """主函数"""
    
    print("\n" + "="*60)
    print("[SIMPLE ORDER IMPORT] 简化版订单导入工具")
    print("="*60)
    
    # 1. 查找数据文件
    data_dir = r"D:\Python1\O2O_Analysis\O2O数据分析\测算模型\实际数据"
    excel_files = glob.glob(f"{data_dir}\\*.xlsx")
    
    if not excel_files:
        print(f"[ERROR] 未找到Excel文件: {data_dir}")
        return
    
    excel_file = excel_files[0]
    print(f"\n[FILE] {Path(excel_file).name}")
    
    # 2. 加载数据
    print(f"\n[STEP 1/5] 加载Excel...")
    df = pd.read_excel(excel_file)
    print(f"[OK] {len(df):,} 行 × {len(df.columns)} 列")
    
    # 3. 标准化
    print(f"\n[STEP 2/5] 标准化字段...")
    processor = RealDataProcessor()
    df = processor.standardize_sales_data(df)
    print(f"[OK] {len(df):,} 行")
    
    # 4. 过滤
    print(f"\n[STEP 3/5] 业务规则过滤...")
    
    # 过滤耗材
    if '一级分类名' in df.columns:
        before = len(df)
        df = df[df['一级分类名'] != '耗材'].copy()
        if before > len(df):
            print(f"   [FILTER] 耗材: -{before - len(df):,} 行")
    
    # 过滤咖啡渠道
    if '渠道' in df.columns:
        before = len(df)
        df = df[~df['渠道'].str.contains('咖啡', na=False)].copy()
        if before > len(df):
            print(f"   [FILTER] 咖啡渠道: -{before - len(df):,} 行")
    
    print(f"[OK] 最终: {len(df):,} 行")
    
    # 5. 导入
    print(f"\n[STEP 4/5] 导入数据库...")
    stats = import_orders_simple(df, batch_size=500)
    
    # 6. 验证
    print(f"\n[STEP 5/5] 验证结果...")
    db = next(get_db())
    try:
        order_count = db.query(Order).count()
        print(f"\n[DATABASE] 订单总数: {order_count:,}")
        
        # 查询最新订单
        latest = db.query(Order).order_by(Order.date.desc()).limit(3).all()
        if latest:
            print(f"\n[LATEST] 最新3条订单:")
            for o in latest:
                print(f"   {o.date} | {o.product_name[:30]} | ¥{o.price}")
    finally:
        db.close()
    
    print("\n" + "="*60)
    print("[SUCCESS] 订单导入完成!")
    print("="*60)


if __name__ == "__main__":
    main()
