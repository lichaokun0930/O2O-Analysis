# -*- coding: utf-8 -*-
"""测试环比计算逻辑 - 独立版本"""
import pandas as pd
from datetime import datetime, date, timedelta
from database.models import Order
from database.connection import get_db
from sqlalchemy import cast, Date, func

# 获取数据库连接
db = next(get_db())

store_name = '共橙超市-南通海安店'
target_date = date(2025, 10, 31)

print(f"\n{'='*60}")
print(f"测试门店: {store_name}")
print(f"目标日期: {target_date}")
print(f"{'='*60}\n")

# 查询完整数据
orders = db.query(Order).filter(Order.store_name == store_name).all()

# 转换为DataFrame
data = []
for order in orders:
    data.append({
        '订单ID': order.order_id,
        '日期': order.date,
        '下单时间': order.date,
        '商品名称': order.product_name or '',
        '商品实售价': order.amount or 0,
        '利润额': order.profit or 0,
        '物流配送费': order.delivery_fee or 0,
        '平台佣金': order.commission or 0,
        '新客减免金额': order.new_customer_discount or 0,
        '企客后返': order.corporate_rebate or 0,
        '预计订单收入': order.amount or 0,
        '配送费减免金额': order.delivery_discount or 0,
        '用户支付配送费': order.user_paid_delivery_fee or 0,
        '月售': 0,
    })

df = pd.DataFrame(data)
print(f"总数据量: {len(df)} 条")
print(f"日期范围: {df['日期'].min()} 到 {df['日期'].max()}")

# 确保日期字段为datetime类型
df['日期'] = pd.to_datetime(df['日期'])
df['下单时间'] = pd.to_datetime(df['下单时间'])

# 设置日期范围
start_date = datetime(2025, 10, 31, 0, 0, 0)
end_date = datetime(2025, 10, 31, 23, 59, 59)
period_days = 1

# 计算上一周期
prev_end_date = start_date - timedelta(days=1)
prev_start_date = prev_end_date - timedelta(days=period_days - 1)

print(f"\n当前周期: {start_date.date()} ~ {end_date.date()}")
print(f"上期周期: {prev_start_date.date()} ~ {prev_end_date.date()}")

# 筛选当前周期数据
current_data = df[
    (df['日期'].dt.date >= start_date.date()) & 
    (df['日期'].dt.date <= end_date.date())
].copy()

# 筛选上一周期数据
prev_data = df[
    (df['日期'].dt.date >= prev_start_date.date()) & 
    (df['日期'].dt.date <= prev_end_date.date())
].copy()

print(f"\n当前周期数据: {len(current_data)} 条")
print(f"上期周期数据: {len(prev_data)} 条")

if len(prev_data) == 0:
    print("\n❌ 上一周期无数据，无法计算环比")
    db.close()
    exit(1)

# 计算指标函数
def calc_metrics(data):
    """计算指标"""
    if len(data) == 0:
        return {
            'order_count': 0,
            'total_sales': 0,
            'total_profit': 0,
        }
    
    # 聚合订单数据 - 使用新公式
    agg_dict = {
        '商品实售价': 'sum',
        '利润额': 'sum',
        '物流配送费': 'first',
        '平台佣金': 'first',
        '新客减免金额': 'first',
        '企客后返': 'sum',
    }
    
    order_metrics = data.groupby('订单ID').agg(agg_dict).reset_index()
    
    # 使用新公式计算订单实际利润
    order_metrics['订单实际利润'] = (
        order_metrics['利润额'] - 
        order_metrics['物流配送费'] - 
        order_metrics['平台佣金'] - 
        order_metrics['新客减免金额'] + 
        order_metrics['企客后返']
    )
    
    order_count = len(order_metrics)
    total_sales = order_metrics['商品实售价'].sum()
    total_profit = order_metrics['订单实际利润'].sum()
    
    return {
        'order_count': order_count,
        'total_sales': total_sales,
        'total_profit': total_profit,
    }

current_metrics = calc_metrics(current_data)
prev_metrics = calc_metrics(prev_data)

print(f"\n{'='*60}")
print(f"当前周期 ({start_date.date()}):")
print(f"  订单数: {current_metrics['order_count']}")
print(f"  销售额: ¥{current_metrics['total_sales']:,.2f}")
print(f"  总利润: ¥{current_metrics['total_profit']:,.2f}")

print(f"\n上期周期 ({prev_start_date.date()}):")
print(f"  订单数: {prev_metrics['order_count']}")
print(f"  销售额: ¥{prev_metrics['total_sales']:,.2f}")
print(f"  总利润: ¥{prev_metrics['total_profit']:,.2f}")

# 计算环比
def calc_change_rate(current, prev):
    if prev == 0:
        return 999.9 if current > 0 else 0
    return ((current - prev) / prev) * 100

order_change = calc_change_rate(current_metrics['order_count'], prev_metrics['order_count'])
sales_change = calc_change_rate(current_metrics['total_sales'], prev_metrics['total_sales'])
profit_change = calc_change_rate(current_metrics['total_profit'], prev_metrics['total_profit'])

print(f"\n{'='*60}")
print(f"环比变化:")
print(f"  订单数: {order_change:+.1f}%")
print(f"  销售额: {sales_change:+.1f}%")
print(f"  总利润: {profit_change:+.1f}%")
print(f"{'='*60}\n")

db.close()
