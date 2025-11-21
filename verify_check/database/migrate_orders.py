"""
P0 高优任务：修复订单导入重复ID问题
使用 PostgreSQL UPSERT 语法实现增量更新

问题：order_id 存在重复，导致 UniqueViolation 错误
解决方案：ON CONFLICT DO UPDATE - 遇到重复则更新现有记录
"""

import sys
import os
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
                        
                        # ✨ 利润 (Excel中有这个字段!)
                        'profit': float(row.get('利润额', 0)) if pd.notna(row.get('利润额')) else 0,
                        'profit_margin': None,  # ✨ 明确设置为NULL (计算字段,可后续通过触发器或程序计算)
                        
                        # 费用
                        'delivery_fee': float(row.get('物流配送费', 0)) if pd.notna(row.get('物流配送费')) else 0,
                        'commission': float(row.get('平台佣金', 0)) if pd.notna(row.get('平台佣金')) else 0,
                        'platform_service_fee': float(row.get('平台服务费', 0)) if pd.notna(row.get('平台服务费')) else 0,  # 修复:正确映射平台服务费字段
                        
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
        
        # ✅ 5. 更新Product表(同步库存和成本信息)
        print(f"\n[STEP 5] 更新Product表...")
        try:
            from database.models import Product
            
            # ✅ 使用传入的df参数(已经标准化)
            # 获取每个商品的最新库存和成本(按商品名称+条码分组,取最后一条记录)
            if '库存' in df.columns and '条码' in df.columns:
                # 按商品聚合,获取最新数据
                product_data = df.groupby('条码').agg({
                    '商品名称': 'first',
                    '一级分类名': 'first',
                    '三级分类名': 'first',
                    '库存': 'last',  # 取最后一条记录的库存
                    '商品采购成本': 'last',      # 取最后一条记录的成本
                    '商品实售价': 'last' # 取最后一条记录的售价
                }).reset_index()
                
                # 过滤有效数据
                product_data = product_data[product_data['条码'].notna()]
                
                updated_count = 0
                created_count = 0
                
                for _, row in product_data.iterrows():
                    barcode = str(row['条码'])
                    stock = int(row['库存']) if pd.notna(row['库存']) else 0
                    cost = float(row['商品采购成本']) if pd.notna(row['商品采购成本']) else 0
                    price = float(row['商品实售价']) if pd.notna(row['商品实售价']) else 0
                    
                    # 查找或创建Product记录
                    product = db.query(Product).filter(Product.barcode == barcode).first()
                    
                    if product:
                        # 更新现有商品
                        product.stock = stock
                        product.current_cost = cost
                        product.current_price = price
                        product.category_level1 = str(row['一级分类名']) if pd.notna(row['一级分类名']) else None
                        product.category_level3 = str(row['三级分类名']) if pd.notna(row['三级分类名']) else None
                        updated_count += 1
                    else:
                        # 创建新商品
                        new_product = Product(
                            barcode=barcode,
                            product_name=str(row['商品名称']),
                            stock=stock,
                            current_cost=cost,
                            current_price=price,
                            category_level1=str(row['一级分类名']) if pd.notna(row['一级分类名']) else None,
                            category_level3=str(row['三级分类名']) if pd.notna(row['三级分类名']) else None
                        )
                        db.add(new_product)
                        created_count += 1
                
                db.commit()
                print(f"[OK] Product表更新完成")
                print(f"   新增商品: {created_count:,}")
                print(f"   更新商品: {updated_count:,}")
            else:
                print(f"[WARN] 缺少'库存'或'条码'字段,跳过Product表更新")
                print(f"   可用字段: {df_standardized.columns.tolist()}")
                
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Product表更新失败: {e}")
            import traceback
            traceback.print_exc()
        
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
    
    # ✅ 2025-11-18: 指定枫瑞店数据文件
    excel_file = os.path.join(data_dir, "枫瑞.xlsx")
    
    if not os.path.exists(excel_file):
        print(f"[ERROR] 未找到文件: {excel_file}")
        return
    
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
    
    # ❌ 2025-11-18: 禁用耗材剔除,保留真实成本数据
    # 原因: 耗材(购物袋)是订单成本的一部分,剔除会导致利润虚高
    # if '一级分类名' in df_standardized.columns:
    #     before = len(df_standardized)
    #     df_standardized = df_standardized[df_standardized['一级分类名'] != '耗材'].copy()
    #     removed = before - len(df_standardized)
    #     if removed > 0:
    #         print(f"   [FILTER] 剔除耗材: {removed:,} 行")
    print(f"   [OK] 保留耗材数据 (包含购物袋等成本)")
    
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
    # from DATABASE_FIRST_STANDARD import remind_database_first
    # remind_database_first()
    
    main()
