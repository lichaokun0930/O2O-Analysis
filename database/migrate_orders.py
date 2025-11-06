"""
P0 高优任务：修复订单导入重复ID问题
使用 PostgreSQL UPSERT 语法实现增量更新

问题：order_id 存在重复，导致 UniqueViolation 错误
解决方案：ON CONFLICT DO UPDATE - 遇到重复则更新现有记录
"""

import sys
from pathlib import Path
import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
import glob

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db, engine
from database.models import Order, Product
from 真实数据处理器 import RealDataProcessor


def upsert_orders(df: pd.DataFrame, batch_size: int = 1000):
    """
    使用 UPSERT 批量导入订单数据
    
    Args:
        df: 订单数据 DataFrame
        batch_size: 每批次数量
    
    Returns:
        导入统计信息
    """
    db = next(get_db())
    stats = {
        'total': len(df),
        'inserted': 0,
        'updated': 0,
        'errors': 0,
        'error_details': []
    }
    
    try:
        print(f"\n[开始导入] 总记录数: {len(df):,}")
        print(f"[批次设置] 每批 {batch_size} 条")
        print("="*60)
        
        # 按批次处理
        for batch_idx, start_idx in enumerate(range(0, len(df), batch_size), 1):
            end_idx = min(start_idx + batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx]
            
            print(f"\n[BATCH {batch_idx}] 处理 {start_idx+1} - {end_idx} 行...", end=" ")
            
            # 准备批量插入数据
            orders_data = []
            for _, row in batch_df.iterrows():
                try:
                    # 日期字段处理(兼容"日期"和"下单时间")
                    date_value = row.get('日期') or row.get('下单时间')
                    order_date = pd.to_datetime(date_value) if pd.notna(date_value) else None
                    
                    order_data = {
                        # 基础订单信息
                        'order_id': str(row.get('订单ID', '')),
                        'date': order_date,
                        'store_name': str(row.get('门店名称', 'UNKNOWN')),
                        'store_id': str(row.get('门店ID', '')) if pd.notna(row.get('门店ID')) else None,
                        'address': str(row.get('收货地址', '')) if pd.notna(row.get('收货地址')) else None,
                        'city': str(row.get('城市名称', '')) if pd.notna(row.get('城市名称')) else None,
                        
                        # 商品信息
                        'product_id': None,  # ✨ 明确设置为NULL (外键字段,允许为空,后续可通过条码关联)
                        'product_name': str(row.get('商品名称', '')),
                        'barcode': str(row.get('条码', '')) or str(row.get('商品条形码', '')),
                        'category_level1': str(row.get('一级分类名', '')),
                        'category_level3': str(row.get('三级分类名', '')),
                        
                        # 价格和数量
                        'price': float(row.get('商品实售价', 0)) if pd.notna(row.get('商品实售价')) else 0,
                        'original_price': float(row.get('商品原价', 0)) if pd.notna(row.get('商品原价')) else None,
                        'actual_price': float(row.get('实收价格', 0)) if pd.notna(row.get('实收价格')) else None,
                        'cost': float(row.get('成本', 0)) if pd.notna(row.get('成本')) else 0,
                        'quantity': int(row.get('销量', 1)) if pd.notna(row.get('销量')) else 1,
                        'amount': float(row.get('实收金额', 0)) if pd.notna(row.get('实收金额')) else 0,
                        
                        # ✨ 库存信息 (标准化后字段名为"库存",原始Excel为"剩余库存")
                        'stock': int(row.get('库存', 0)) if pd.notna(row.get('库存')) else 0,
                        
                        # ✨ 利润 (Excel中有这个字段!)
                        'profit': float(row.get('利润额', 0)) if pd.notna(row.get('利润额')) else 0,
                        'profit_margin': None,  # ✨ 明确设置为NULL (计算字段,可后续通过触发器或程序计算)
                        
                        # 费用
                        'delivery_fee': float(row.get('物流配送费', 0)) if pd.notna(row.get('物流配送费')) else 0,
                        'commission': float(row.get('平台佣金', 0)) if pd.notna(row.get('平台佣金')) else 0,
                        
                        # ✨ 营销活动字段 (Excel中都有!)
                        'user_paid_delivery_fee': float(row.get('用户支付配送费', 0)) if pd.notna(row.get('用户支付配送费')) else 0,
                        'delivery_discount': float(row.get('配送费减免金额', 0)) if pd.notna(row.get('配送费减免金额')) else 0,
                        'full_reduction': float(row.get('满减金额', 0)) if pd.notna(row.get('满减金额')) else 0,
                        'product_discount': float(row.get('商品减免金额', 0)) if pd.notna(row.get('商品减免金额')) else 0,
                        'merchant_voucher': float(row.get('商家代金券', 0)) if pd.notna(row.get('商家代金券')) else 0,
                        'merchant_share': float(row.get('商家承担部分券', 0)) if pd.notna(row.get('商家承担部分券')) else 0,
                        'packaging_fee': float(row.get('打包袋金额', 0)) if pd.notna(row.get('打包袋金额')) else 0,
                        
                        # ✨ 配送信息
                        'delivery_distance': float(row.get('配送距离', 0)) if pd.notna(row.get('配送距离')) else 0,
                        
                        # 渠道场景
                        'channel': str(row.get('渠道', '')),
                        'scene': str(row.get('场景', '')),
                        'time_period': str(row.get('时段', '')),
                    }
                    orders_data.append(order_data)
                    
                except Exception as e:
                    stats['errors'] += 1
                    stats['error_details'].append({
                        'row': start_idx + len(orders_data),
                        'error': str(e),
                        'data': row.to_dict()
                    })
            
            if not orders_data:
                print("[WARN] 无有效数据")
                continue
            
            # ✨ 直接批量插入 (允许订单ID重复,因为一个订单包含多个商品明细)
            try:
                db.bulk_insert_mappings(Order, orders_data)
                db.commit()
                
                # 统计插入数量
                batch_count = len(orders_data)
                stats['inserted'] += batch_count
                
                print(f"[OK] 成功插入 {batch_count} 条")
                
            except Exception as e:
                db.rollback()
                print(f"[ERROR] 批次失败: {e}")
                stats['errors'] += len(orders_data)
                stats['error_details'].append({
                    'batch': batch_idx,
                    'error': str(e)
                })
        
        print("\n" + "="*60)
        print("[COMPLETE] 导入完成")
        print(f"   总记录: {stats['total']:,}")
        print(f"   成功: {stats['inserted']:,}")
        print(f"   失败: {stats['errors']:,}")
        
        if stats['error_details']:
            print(f"\n[WARN] 错误详情（前5条）:")
            for err in stats['error_details'][:5]:
                print(f"   {err}")
        
        return stats
        
    finally:
        db.close()


def main():
    """主函数：加载并导入订单数据"""
    
    print("\n" + "="*60)
    print("[MIGRATE] 订单数据导入工具 (UPSERT版本)")
    print("="*60)
    
    # 1. 查找数据文件
    data_dir = r"D:\Python1\O2O_Analysis\O2O数据分析\测算模型\实际数据"
    excel_files = glob.glob(f"{data_dir}\\*.xlsx")
    
    if not excel_files:
        print(f"[ERROR] 未找到Excel文件: {data_dir}")
        return
    
    excel_file = excel_files[0]
    print(f"\n[FILE] 数据文件: {Path(excel_file).name}")
    
    # 2. 加载数据
    print(f"\n[STEP 1] 加载Excel数据...")
    df = pd.read_excel(excel_file)
    print(f"[OK] 已加载: {len(df):,} 行 × {len(df.columns)} 列")
    
    # 3. 标准化数据
    print(f"\n[STEP 2] 标准化字段...")
    processor = RealDataProcessor()
    df_standardized = processor.standardize_sales_data(df)
    print(f"[OK] 标准化完成: {len(df_standardized):,} 行")
    
    # 4. 业务规则过滤
    print(f"\n[STEP 3] 应用业务规则...")
    
    # 过滤耗材
    if '一级分类名' in df_standardized.columns:
        before = len(df_standardized)
        df_standardized = df_standardized[df_standardized['一级分类名'] != '耗材'].copy()
        removed = before - len(df_standardized)
        if removed > 0:
            print(f"   [FILTER] 剔除耗材: {removed:,} 行")
    
    # 过滤咖啡渠道
    if '渠道' in df_standardized.columns:
        before = len(df_standardized)
        df_standardized = df_standardized[~df_standardized['渠道'].str.contains('咖啡', na=False)].copy()
        removed = before - len(df_standardized)
        if removed > 0:
            print(f"   [FILTER] 剔除咖啡渠道: {removed:,} 行")
    
    print(f"[OK] 最终数据量: {len(df_standardized):,} 行")
    
    # 5. 导入数据库
    print(f"\n[STEP 4] 导入数据库...")
    stats = upsert_orders(df_standardized, batch_size=1000)
    
    # 6. 验证结果
    print(f"\n[STEP 5] 验证导入结果...")
    db = next(get_db())
    try:
        order_count = db.query(Order).count()
        product_count = db.query(Product).count()
        
        print(f"\n[STATS] 数据库统计:")
        print(f"   订单总数: {order_count:,}")
        print(f"   商品总数: {product_count:,}")
        
        # 查询最新订单
        latest_orders = db.query(Order).order_by(Order.date.desc()).limit(5).all()
        if latest_orders:
            print(f"\n[LATEST] 最新订单（前5条）:")
            for order in latest_orders:
                print(f"   {order.date} | {order.product_name} | ¥{order.price}")
    
    finally:
        db.close()
    
    print("\n" + "="*60)
    print("[SUCCESS] 订单导入完成！")
    print("="*60)


if __name__ == "__main__":
    # 导入前提醒
    from DATABASE_FIRST_STANDARD import remind_database_first
    remind_database_first()
    
    main()
