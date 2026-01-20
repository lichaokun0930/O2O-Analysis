# -*- coding: utf-8 -*-
"""
订单数据概览 - 新旧版本数据对比测试

对比项目：
1. 六大核心卡片指标
2. 渠道表现数据
3. 计算逻辑一致性
"""
import requests
import pandas as pd
from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import func

# 收费渠道列表
PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购',
    '抖音', '抖音直播', '淘鲜达', '京东秒送',
    '美团咖啡店', '饿了么咖啡店'
]

def get_old_version_metrics():
    """老版本计算逻辑（直接查询数据库，模拟Dash计算）"""
    session = SessionLocal()
    try:
        orders = session.query(Order).all()
        if not orders:
            return {}
        
        # 转换为DataFrame
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '门店名称': order.store_name,
                '日期': order.date,
                '渠道': order.channel,
                '商品名称': order.product_name,
                '月售': order.quantity,
                '实收价格': float(order.actual_price or 0),
                '商品实售价': float(order.price or 0),
                '商品采购成本': float(order.cost or 0),
                '利润额': float(order.profit or 0),
                '物流配送费': float(order.delivery_fee or 0),
                '平台服务费': float(order.platform_service_fee or 0),
                '平台佣金': float(order.commission or 0),
                '预计订单收入': float(order.amount or 0),
                '企客后返': float(order.corporate_rebate or 0),
                '用户支付配送费': float(order.user_paid_delivery_fee or 0),
                '配送费减免金额': float(order.delivery_discount or 0),
            })
        
        df = pd.DataFrame(data)
        df['订单ID'] = df['订单ID'].astype(str)
        
        # 空值填充
        df['物流配送费'] = df['物流配送费'].fillna(0)
        df['配送费减免金额'] = df['配送费减免金额'].fillna(0)
        df['用户支付配送费'] = df['用户支付配送费'].fillna(0)
        
        # 计算订单总收入
        df['订单总收入'] = df['实收价格'] * df['月售']
        
        # 订单级聚合
        agg_dict = {
            '商品实售价': 'sum',
            '预计订单收入': 'sum',
            '用户支付配送费': 'first',
            '配送费减免金额': 'first',
            '物流配送费': 'first',
            '平台佣金': 'first',
            '月售': 'sum',
            '平台服务费': 'sum',
            '订单总收入': 'sum',
            '利润额': 'sum',
            '企客后返': 'sum',
            '商品采购成本': 'sum',
            '渠道': 'first',
            '门店名称': 'first',
            '日期': 'first',
        }
        
        order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
        order_agg['实收价格'] = order_agg['订单总收入']
        
        # 关键字段兜底
        order_agg['平台服务费'] = order_agg['平台服务费'].fillna(0)
        order_agg['企客后返'] = order_agg['企客后返'].fillna(0)
        order_agg['平台佣金'] = order_agg['平台佣金'].fillna(0)
        order_agg['利润额'] = order_agg['利润额'].fillna(0)
        
        # 计算订单实际利润（核心公式）
        order_agg['订单实际利润'] = (
            order_agg['利润额'] -
            order_agg['平台服务费'] -
            order_agg['物流配送费'] +
            order_agg['企客后返']
        )
        
        # 按渠道类型过滤异常订单
        if '渠道' in order_agg.columns:
            is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
            is_zero_fee = order_agg['平台服务费'] <= 0
            invalid_orders = is_fee_channel & is_zero_fee
            order_agg = order_agg[~invalid_orders].copy()
        
        # 六大核心卡片
        total_orders = len(order_agg)
        total_actual_sales = order_agg['实收价格'].sum()
        total_profit = order_agg['订单实际利润'].sum()
        avg_order_value = total_actual_sales / total_orders if total_orders > 0 else 0
        profit_rate = (total_profit / total_actual_sales * 100) if total_actual_sales > 0 else 0
        
        # 动销商品数
        active_products = df[df['月售'] > 0]['商品名称'].nunique()
        
        return {
            'total_orders': int(total_orders),
            'total_actual_sales': round(float(total_actual_sales), 2),
            'total_profit': round(float(total_profit), 2),
            'avg_order_value': round(float(avg_order_value), 2),
            'profit_rate': round(float(profit_rate), 2),
            'active_products': int(active_products),
        }
    finally:
        session.close()


def get_new_version_metrics():
    """新版本API获取的指标"""
    response = requests.get("http://localhost:8080/api/v1/orders/overview")
    data = response.json()
    return data.get('data', {})


def compare_metrics():
    """Compare old vs new version metrics"""
    print("=" * 70)
    print("Order Overview - Old vs New Version Comparison Test")
    print("=" * 70)
    
    old = get_old_version_metrics()
    new = get_new_version_metrics()
    
    print("\n[6 Core KPI Cards Comparison]")
    print("-" * 70)
    print(f"{'Metric':<20} {'Old':>15} {'New':>15} {'Diff':>15} {'Status':>10}")
    print("-" * 70)
    
    metrics = [
        ('Total Orders', 'total_orders'),
        ('Actual Sales', 'total_actual_sales'),
        ('Total Profit', 'total_profit'),
        ('Avg Order Value', 'avg_order_value'),
        ('Profit Rate(%)', 'profit_rate'),
        ('Active Products', 'active_products'),
    ]
    
    all_match = True
    for label, key in metrics:
        old_val = old.get(key, 0)
        new_val = new.get(key, 0)
        diff = new_val - old_val
        
        # 判断是否一致（允许小数误差）
        if isinstance(old_val, float):
            match = abs(diff) < 0.01
        else:
            match = diff == 0
        
        status = "OK" if match else "DIFF"
        if not match:
            all_match = False
        
        print(f"{label:<20} {old_val:>15,.2f} {new_val:>15,.2f} {diff:>+15,.2f} {status:>10}")
    
    print("-" * 70)
    print()
    
    if all_match:
        print("=" * 70)
        print("RESULT: ALL METRICS MATCHED! New version equals Old version.")
        print("=" * 70)
    else:
        print("=" * 70)
        print("RESULT: MISMATCH FOUND! Please check calculation logic.")
        print("=" * 70)
    
    return all_match


def compare_channel_stats():
    """Compare channel statistics"""
    print("\n" + "=" * 70)
    print("Channel Performance Comparison")
    print("=" * 70)
    
    # Get new version channel data
    response = requests.get("http://localhost:8080/api/v1/orders/channels")
    new_data = response.json().get('data', [])
    
    if not new_data:
        print("No channel data available")
        return
    
    print(f"\n{'Channel':<15} {'Orders':>10} {'Amount':>15} {'Profit':>15} {'Rate':>10}")
    print("-" * 70)
    
    for ch in new_data:
        channel_name = ch['channel'][:12] if ch['channel'] else 'Unknown'
        print(f"{channel_name:<15} {ch['order_count']:>10,} {ch['amount']:>15,.2f} {ch['profit']:>15,.2f} {ch['profit_rate']:>10.2f}%")
    
    print("-" * 70)


if __name__ == "__main__":
    compare_metrics()
    compare_channel_stats()

