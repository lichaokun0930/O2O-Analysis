"""
检查数据库中的门店和渠道数据
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database.connection import get_db_connection
from database.models import Order
from sqlalchemy import func
from datetime import datetime, timedelta

print("="*80)
print("🔍 检查数据库中的门店数据")
print("="*80)

with get_db_connection() as session:
    # 1. 总体统计
    total_orders = session.query(func.count(Order.id)).scalar()
    print(f"\n📊 总订单数: {total_orders:,}")
    
    # 2. 按门店统计
    print(f"\n📍 按门店统计:")
    store_stats = session.query(
        Order.store_name,
        func.count(Order.id).label('订单数'),
        func.sum(Order.actual_profit).label('总利润')
    ).group_by(Order.store_name).all()
    
    if store_stats:
        for store, count, profit in store_stats:
            profit_val = profit or 0
            print(f"   {store}: {count:,} 订单, 利润 ¥{profit_val:,.2f}")
    else:
        print("   ❌ 没有门店数据!")
    
    # 3. 按渠道统计
    print(f"\n📱 按渠道统计:")
    channel_stats = session.query(
        Order.channel,
        func.count(Order.id).label('订单数'),
        func.sum(Order.actual_profit).label('总利润')
    ).group_by(Order.channel).all()
    
    if channel_stats:
        for channel, count, profit in channel_stats:
            profit_val = profit or 0
            print(f"   {channel}: {count:,} 订单, 利润 ¥{profit_val:,.2f}")
    else:
        print("   ❌ 没有渠道数据!")
    
    # 4. 祥和路店详细统计
    print(f"\n🏪 祥和路店详细统计:")
    xianghelu_orders = session.query(Order).filter(
        Order.store_name.like('%祥和路%')
    ).all()
    
    if xianghelu_orders:
        print(f"   订单行数: {len(xianghelu_orders):,}")
        
        # 按渠道分组
        from collections import defaultdict
        channel_data = defaultdict(lambda: {'count': 0, 'profit': 0})
        
        for order in xianghelu_orders:
            channel_data[order.channel]['count'] += 1
            channel_data[order.channel]['profit'] += (order.actual_profit or 0)
        
        for channel, data in channel_data.items():
            print(f"   {channel}: {data['count']:,} 订单, 利润 ¥{data['profit']:,.2f}")
    else:
        print("   ❌ 没有找到祥和路店数据!")
        
        # 模糊搜索其他可能的名称
        print(f"\n🔍 搜索包含'祥和'或'路'的门店:")
        similar_stores = session.query(Order.store_name).filter(
            (Order.store_name.like('%祥和%')) | (Order.store_name.like('%路店%'))
        ).distinct().all()
        
        if similar_stores:
            for (store,) in similar_stores:
                print(f"      {store}")
        else:
            print("      ❌ 没有找到相关门店")
    
    # 5. 时间范围
    print(f"\n📅 数据时间范围:")
    date_range = session.query(
        func.min(Order.date).label('最早'),
        func.max(Order.date).label('最晚')
    ).first()
    
    if date_range and date_range[0]:
        print(f"   {date_range[0]} 至 {date_range[1]}")
    else:
        print("   ❌ 没有日期数据!")

print(f"\n{'='*80}")
