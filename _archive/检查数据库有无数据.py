"""
检查数据库里是否有订单数据
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import get_db_connection
from database.models import Order
from sqlalchemy import func

print("="*80)
print("🔍 检查数据库订单数据")
print("="*80)

try:
    with get_db_connection() as session:
        # 统计总订单数
        total_count = session.query(func.count(Order.id)).scalar()
        print(f"\n📊 数据库总记录数: {total_count:,}")
        
        if total_count > 0:
            # 统计门店
            stores = session.query(
                Order.store_name,
                func.count(Order.id).label('count')
            ).group_by(Order.store_name).all()
            
            print(f"\n📍 门店列表:")
            for store, count in stores:
                print(f"   {store}: {count:,} 条记录")
            
            # 统计渠道
            channels = session.query(
                Order.channel,
                func.count(Order.id).label('count')
            ).group_by(Order.channel).all()
            
            print(f"\n📱 渠道列表:")
            for channel, count in channels:
                print(f"   {channel}: {count:,} 条记录")
            
            # 查看最新5条数据
            latest = session.query(Order).order_by(Order.date.desc()).limit(5).all()
            print(f"\n📅 最新5条记录:")
            for order in latest:
                print(f"   {order.date} | {order.store_name} | {order.channel} | 订单{order.order_id}")
        else:
            print("\n❌ 数据库是空的!")
            
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
