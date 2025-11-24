from database.connection import get_db_context
from database.models import Order
from sqlalchemy import func
import pandas as pd

def diagnose_issues():
    store_name = "惠宜选-徐州铜山万达店"  # 假设这是数据库中的标准名称，需要确认
    
    print(f"[INFO] 诊断门店: {store_name}")
    
    with get_db_context() as db:
        # 1. 确认门店名称是否正确
        exists = db.query(Order).filter(Order.store_name == store_name).first()
        if not exists:
            print(f"[ERROR] 未找到门店 '{store_name}'")
            # 列出所有门店供参考
            all_stores = db.query(Order.store_name).distinct().all()
            print(f"   可用门店: {[s[0] for s in all_stores]}")
            return

        # 2. 诊断问题1: 渠道列表
        print("\n[INFO] 渠道分布情况:")
        channels = db.query(Order.channel, func.count(Order.id)).filter(
            Order.store_name == store_name
        ).group_by(Order.channel).all()
        
        for channel, count in channels:
            print(f"   - {channel}: {count} 行数据")
            
        # 3. 诊断问题2: 饿了么利润额差异
        target_channel = "饿了么"
        print(f"\n[INFO] {target_channel} 利润分析:")
        
        # 获取该门店、该渠道的所有订单数据
        orders = db.query(Order.order_id, Order.profit, Order.date).filter(
            Order.store_name == store_name,
            Order.channel == target_channel
        ).all()
        
        if not orders:
            print(f"   [ERROR] 未找到 {target_channel} 的数据")
            return

        df = pd.DataFrame(orders, columns=['order_id', 'profit', 'date'])
        
        # 方式A: 直接累加 (Sum of all rows)
        total_sum = df['profit'].sum()
        print(f"   方式A (直接累加所有行): {total_sum:.2f}")
        
        # 方式B: 按订单ID去重后累加 (Sum of unique orders)
        # 假设同一订单的多行数据中，profit字段是重复的订单级利润
        df_unique = df.drop_duplicates(subset=['order_id'])
        unique_sum = df_unique['profit'].sum()
        print(f"   方式B (按订单ID去重后累加): {unique_sum:.2f}")
        
        # 方式C: 假设profit是商品级利润，直接累加就是对的
        # 但如果存在重复导入，或者逻辑错误，可能会导致差异
        
        print(f"\n   用户反馈: 看板显示 6069 vs 下钻显示 6255")
        print(f"   差异值: {abs(6069 - 6255)}")
        
        # 检查是否有时间范围的影响 (比如最近30天)
        max_date = df['date'].max()
        min_date = df['date'].min()
        print(f"   数据时间范围: {min_date} 至 {max_date}")

if __name__ == "__main__":
    diagnose_issues()
