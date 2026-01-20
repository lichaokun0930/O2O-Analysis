# -*- coding: utf-8 -*-
"""
数据同步定时任务

使用 APScheduler 实现：
1. 每天凌晨2:00同步昨日数据到Parquet
2. 每小时刷新预聚合缓存
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, date
import pandas as pd
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from database.models import Order
from app.services import parquet_sync_service

# 全局调度器
scheduler = BackgroundScheduler()


def sync_yesterday_data():
    """
    同步昨日数据（每天凌晨 2:00 执行）
    """
    yesterday = datetime.now().date() - timedelta(days=1)
    print(f"🔄 [{datetime.now()}] 开始同步 {yesterday} 的数据...")
    
    session = SessionLocal()
    try:
        orders = session.query(Order).filter(Order.date == yesterday).all()
        
        if not orders:
            print(f"⚠️ {yesterday} 无数据")
            return
        
        # 转换为 DataFrame
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
            })
        
        df = pd.DataFrame(data)
        
        # 同步原始数据
        parquet_sync_service.sync_raw_data(yesterday, df)
        
        # 生成聚合数据
        parquet_sync_service.generate_daily_aggregations(yesterday)
        
        print(f"✅ [{datetime.now()}] {yesterday} 数据同步完成: {len(df)} 条")
        
    except Exception as e:
        print(f"❌ [{datetime.now()}] 同步失败: {e}")
    finally:
        session.close()


def sync_today_data():
    """
    同步今日数据（每小时执行，用于实时更新）
    """
    today = datetime.now().date()
    print(f"🔄 [{datetime.now()}] 刷新今日 {today} 的数据...")
    
    session = SessionLocal()
    try:
        orders = session.query(Order).filter(Order.date == today).all()
        
        if not orders:
            print(f"⚠️ 今日暂无数据")
            return
        
        # 转换为 DataFrame
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
            })
        
        df = pd.DataFrame(data)
        
        # 同步原始数据（覆盖今日文件）
        parquet_sync_service.sync_raw_data(today, df)
        
        # 生成聚合数据
        parquet_sync_service.generate_daily_aggregations(today)
        
        print(f"✅ [{datetime.now()}] 今日数据刷新完成: {len(df)} 条")
        
    except Exception as e:
        print(f"❌ [{datetime.now()}] 刷新失败: {e}")
    finally:
        session.close()


def init_scheduler():
    """初始化定时任务调度器"""
    # 每天凌晨 2:00 同步昨日数据
    scheduler.add_job(
        sync_yesterday_data,
        CronTrigger(hour=2, minute=0),
        id='sync_yesterday',
        name='同步昨日数据到Parquet',
        replace_existing=True
    )
    
    # 每小时整点刷新今日数据
    scheduler.add_job(
        sync_today_data,
        CronTrigger(minute=0),
        id='sync_today',
        name='刷新今日数据',
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ 定时任务调度器已启动")
    print("   - 每天 02:00: 同步昨日数据")
    print("   - 每小时整点: 刷新今日数据")


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        print("⚠️ 定时任务调度器已关闭")


# 手动触发函数（用于测试）
def manual_sync(target_date: date = None):
    """手动触发同步"""
    if target_date is None:
        target_date = datetime.now().date()
    
    print(f"🔄 手动同步 {target_date} 的数据...")
    
    session = SessionLocal()
    try:
        orders = session.query(Order).filter(Order.date == target_date).all()
        
        if not orders:
            print(f"⚠️ {target_date} 无数据")
            return False
        
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
            })
        
        df = pd.DataFrame(data)
        parquet_sync_service.sync_raw_data(target_date, df)
        parquet_sync_service.generate_daily_aggregations(target_date)
        
        print(f"✅ 手动同步完成: {len(df)} 条")
        return True
        
    except Exception as e:
        print(f"❌ 手动同步失败: {e}")
        return False
    finally:
        session.close()
