# -*- coding: utf-8 -*-
"""
历史数据迁移脚本

将 PostgreSQL 中的历史订单数据迁移到 Parquet 文件
支持增量迁移和全量迁移
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, date
import pandas as pd

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import func, distinct


def get_date_range():
    """获取数据库中的日期范围"""
    session = SessionLocal()
    try:
        from sqlalchemy import cast, Date
        min_date = session.query(func.min(cast(Order.date, Date))).scalar()
        max_date = session.query(func.max(cast(Order.date, Date))).scalar()
        return min_date, max_date
    finally:
        session.close()


def get_orders_by_date(target_date: date) -> pd.DataFrame:
    """获取指定日期的订单数据"""
    session = SessionLocal()
    try:
        from sqlalchemy import cast, Date
        
        # 使用cast将datetime转换为date进行比较
        orders = session.query(Order).filter(
            cast(Order.date, Date) == target_date
        ).all()
        
        if not orders:
            return pd.DataFrame()
        
        data = []
        for o in orders:
            data.append({
                '订单ID': o.order_id,
                '门店名称': o.store_name,
                '日期': o.date,
                '渠道': o.channel,
                '商品名称': o.product_name,
                '一级分类名': o.category_level1,
                '三级分类名': o.category_level3,
                '月售': o.quantity if o.quantity is not None else 1,
                '实收价格': float(o.actual_price or 0),
                '商品实售价': float(o.price or 0),
                '商品原价': float(o.original_price or 0),
                '商品采购成本': float(o.cost or 0),
                '利润额': float(o.profit or 0),
                '物流配送费': float(o.delivery_fee or 0),
                '平台服务费': float(o.platform_service_fee or 0),
                '平台佣金': float(o.commission or 0),
                '预计订单收入': float(o.amount or 0),
                '企客后返': float(o.corporate_rebate or 0),
                '用户支付配送费': float(o.user_paid_delivery_fee or 0),
                '配送费减免金额': float(o.delivery_discount or 0),
                '满减金额': float(o.full_reduction or 0),
                '商品减免金额': float(o.product_discount or 0),
                '新客减免金额': float(o.new_customer_discount or 0),
                '商家代金券': float(o.merchant_voucher or 0),
                '商家承担部分券': float(o.merchant_share or 0),
                '满赠金额': float(o.gift_amount or 0),
                '商家其他优惠': float(o.other_merchant_discount or 0),
                '打包袋金额': float(o.packaging_fee or 0),
                '库存': o.stock,
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()


def migrate_all_data():
    """迁移全部历史数据"""
    from backend.app.services import parquet_sync_service
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           📦 历史数据迁移到 Parquet
╠══════════════════════════════════════════════════════════════════╣
║  将 PostgreSQL 订单数据按日期分区存储为 Parquet 文件
║  同时生成日聚合数据（KPI、渠道、品类）
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # 获取日期范围
    min_date, max_date = get_date_range()
    
    if not min_date or not max_date:
        print("❌ 数据库中没有订单数据")
        return False
    
    print(f"📅 数据日期范围: {min_date} ~ {max_date}")
    
    # 计算总天数
    total_days = (max_date - min_date).days + 1
    print(f"📊 共需迁移 {total_days} 天的数据\n")
    
    # 统计
    total_records = 0
    success_days = 0
    failed_days = 0
    
    # 按日期迁移
    current_date = min_date
    while current_date <= max_date:
        try:
            # 获取当日数据
            df = get_orders_by_date(current_date)
            
            if df.empty:
                print(f"  ⚪ {current_date}: 无数据")
            else:
                # 同步原始数据
                parquet_sync_service.sync_raw_data(current_date, df)
                
                # 生成聚合数据
                parquet_sync_service.generate_daily_aggregations(current_date)
                
                total_records += len(df)
                success_days += 1
                print(f"  ✅ {current_date}: {len(df):,} 条记录")
        
        except Exception as e:
            failed_days += 1
            print(f"  ❌ {current_date}: 迁移失败 - {e}")
        
        current_date += timedelta(days=1)
    
    # 汇总
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                      📋 迁移完成
╠══════════════════════════════════════════════════════════════════╣
║  总记录数: {total_records:,}
║  成功天数: {success_days}
║  失败天数: {failed_days}
║  存储位置: {parquet_sync_service.data_dir}
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # 显示存储状态
    status = parquet_sync_service.get_status()
    print(f"📁 原始Parquet文件: {status['raw_files_count']} 个")
    print(f"📁 聚合Parquet文件: {status['aggregated_files_count']} 个")
    
    return failed_days == 0


if __name__ == "__main__":
    success = migrate_all_data()
    sys.exit(0 if success else 1)
