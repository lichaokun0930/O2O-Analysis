"""测试环比计算逻辑"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
from datetime import datetime, date
from database.models import Order
from database.connection import get_db
from sqlalchemy import cast, Date, func

# 获取数据库连接
db = next(get_db())

# 查询共橙超市10月31日的数据
target_date = date(2025, 10, 31)
store_name = '共橙超市-南通海安店'

print(f"\n{'='*60}")
print(f"测试门店: {store_name}")
print(f"目标日期: {target_date}")
print(f"{'='*60}\n")

# 1. 检查10月31日数据
oct31_count = db.query(Order).filter(
    Order.store_name == store_name,
    cast(Order.date, Date) == target_date
).count()
print(f"✓ 10月31日订单数: {oct31_count}")

# 2. 检查环比日期范围 (10月30日)
prev_date = date(2025, 10, 30)
oct30_count = db.query(Order).filter(
    Order.store_name == store_name,
    cast(Order.date, Date) == prev_date
).count()
print(f"✓ 10月30日订单数 (环比): {oct30_count}")

# 3. 查询所有日期的订单分布
print("\n近期订单日期分布:")
date_dist = db.query(
    cast(Order.date, Date).label('date'),
    func.count(Order.id).label('count')
).filter(
    Order.store_name == store_name,
    cast(Order.date, Date) >= date(2025, 10, 28),
    cast(Order.date, Date) <= date(2025, 11, 2)
).group_by(cast(Order.date, Date)).order_by(cast(Order.date, Date)).all()

from sqlalchemy import func
for d, count in date_dist:
    marker = " ← 目标" if d == target_date else " ← 环比" if d == prev_date else ""
    print(f"  {d}: {count:>4}单{marker}")

# 4. 测试环比计算函数
print(f"\n{'='*60}")
print("测试环比计算函数")
print(f"{'='*60}\n")

# 查询完整数据
from sqlalchemy.orm import Query
orders = db.query(Order).filter(Order.store_name == store_name).all()

# 转换为DataFrame
data = []
for order in orders:
    data.append({
        '订单ID': order.order_id,
        '日期': order.date,
        '下单时间': order.date,
        '商品实售价': order.amount or 0,
        '利润额': order.profit or 0,
        '物流配送费': order.delivery_fee or 0,
        '平台佣金': order.commission or 0,
        '新客减免金额': order.new_customer_discount or 0,
        '企客后返': order.corporate_rebate or 0,
        '预计订单收入': order.amount or 0,
        '配送费减免金额': order.delivery_discount or 0,
        '用户支付配送费': order.user_paid_delivery_fee or 0,
    })

df = pd.DataFrame(data)
print(f"✓ 总数据量: {len(df)} 条记录")
print(f"✓ 日期范围: {df['日期'].min()} 到 {df['日期'].max()}")

# 导入环比计算函数
import sys
sys.path.insert(0, '.')
from 智能门店看板_Dash版 import calculate_period_comparison

# 测试环比计算
start_date = datetime(2025, 10, 31, 0, 0, 0)
end_date = datetime(2025, 10, 31, 23, 59, 59)

print(f"\n当前周期: {start_date.date()} ~ {end_date.date()}")

comparison_result = calculate_period_comparison(
    df=df,
    start_date=start_date,
    end_date=end_date,
    store_name=store_name
)

print(f"\n环比计算结果:")
if comparison_result:
    for metric_name, metric_data in comparison_result.items():
        print(f"\n{metric_name}:")
        print(f"  当前值: {metric_data.get('current', 0):.2f}")
        print(f"  上期值: {metric_data.get('previous', 0):.2f}")
        print(f"  环比: {metric_data.get('change_rate', 0):+.1f}%")
else:
    print("  ❌ 环比计算返回空结果")

print(f"\n{'='*60}")
print("测试完成")
print(f"{'='*60}")

db.close()
