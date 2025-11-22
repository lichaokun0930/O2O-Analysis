import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database.db_manager import DatabaseManager
import pandas as pd

# 初始化数据库
db = DatabaseManager()

print("="*80)
print("🔍 检查数据库中祥和路店的利润数据")
print("="*80)

# 查询祥和路店的订单数据
query = """
SELECT 
    o.order_id,
    o.channel,
    o.profit_amount,
    o.logistics_cost,
    o.platform_service_fee,
    o.commission,
    o.kickback,
    o.created_at
FROM orders o
JOIN stores s ON o.store_id = s.id
WHERE s.name = '祥和路'
ORDER BY o.created_at DESC
LIMIT 10
"""

try:
    result = db.execute_query(query)
    
    if result and len(result) > 0:
        print(f"\n✅ 找到祥和路店的订单数据: {len(result)}条(显示前10条)")
        print("\n样本数据:")
        
        df = pd.DataFrame(result, columns=[
            '订单ID', '渠道', '利润额', '物流配送费', '平台服务费', '平台佣金', '企客后返', '创建时间'
        ])
        
        print(df.to_string(index=False))
        
        # 统计总数
        count_query = """
        SELECT COUNT(*) as total
        FROM orders o
        JOIN stores s ON o.store_id = s.id
        WHERE s.name = '祥和路'
        """
        count_result = db.execute_query(count_query)
        total_orders = count_result[0][0] if count_result else 0
        
        print(f"\n📊 祥和路店总订单数: {total_orders}")
        
        # 计算利润汇总
        summary_query = """
        SELECT 
            COUNT(DISTINCT o.order_id) as order_count,
            SUM(o.profit_amount) as total_profit,
            SUM(o.logistics_cost) as total_logistics,
            SUM(o.platform_service_fee) as total_service_fee,
            SUM(o.kickback) as total_kickback
        FROM orders o
        JOIN stores s ON o.store_id = s.id
        WHERE s.name = '祥和路'
        AND o.platform_service_fee > 0
        """
        
        summary_result = db.execute_query(summary_query)
        if summary_result and len(summary_result) > 0:
            order_count, total_profit, total_logistics, total_service_fee, total_kickback = summary_result[0]
            
            # 计算实际利润
            actual_profit = (total_profit or 0) - (total_service_fee or 0) - (total_logistics or 0) + (total_kickback or 0)
            
            print(f"\n💰 利润汇总(剔除平台服务费=0后):")
            print(f"   订单数:        {order_count:>10,}")
            print(f"   利润额:        ¥{total_profit or 0:>15,.2f}")
            print(f"   物流配送费:    ¥{total_logistics or 0:>15,.2f}")
            print(f"   平台服务费:    ¥{total_service_fee or 0:>15,.2f}")
            print(f"   企客后返:      ¥{total_kickback or 0:>15,.2f}")
            print(f"   " + "-"*50)
            print(f"   实际利润:      ¥{actual_profit:>15,.2f}")
        
        # 检查平台服务费=0的订单
        zero_fee_query = """
        SELECT COUNT(*) as zero_fee_count
        FROM orders o
        JOIN stores s ON o.store_id = s.id
        WHERE s.name = '祥和路'
        AND o.platform_service_fee = 0
        """
        
        zero_fee_result = db.execute_query(zero_fee_query)
        zero_fee_count = zero_fee_result[0][0] if zero_fee_result else 0
        
        print(f"\n⚠️ 平台服务费=0的订单: {zero_fee_count}个(应被剔除)")
        
        # 分渠道统计
        channel_query = """
        SELECT 
            o.channel,
            COUNT(DISTINCT o.order_id) as order_count,
            SUM(o.profit_amount) as total_profit,
            SUM(o.logistics_cost) as total_logistics,
            SUM(o.platform_service_fee) as total_service_fee,
            SUM(o.kickback) as total_kickback
        FROM orders o
        JOIN stores s ON o.store_id = s.id
        WHERE s.name = '祥和路'
        AND o.platform_service_fee > 0
        GROUP BY o.channel
        """
        
        channel_result = db.execute_query(channel_query)
        if channel_result and len(channel_result) > 0:
            print(f"\n📊 分渠道实际利润:")
            print("="*80)
            
            for row in channel_result:
                channel, order_count, profit, logistics, service_fee, kickback = row
                actual = (profit or 0) - (service_fee or 0) - (logistics or 0) + (kickback or 0)
                
                print(f"\n{channel}:")
                print(f"   订单数:      {order_count:>10,}")
                print(f"   利润额:      ¥{profit or 0:>15,.2f}")
                print(f"   物流配送费:  ¥{logistics or 0:>15,.2f}")
                print(f"   平台服务费:  ¥{service_fee or 0:>15,.2f}")
                print(f"   企客后返:    ¥{kickback or 0:>15,.2f}")
                print(f"   实际利润:    ¥{actual:>15,.2f}")
        
    else:
        print("\n❌ 数据库中没有祥和路店的数据!")
        print("\n💡 可能原因:")
        print("   1. 数据还没有上传到数据库")
        print("   2. 门店名称不匹配")
        
        # 列出所有门店
        stores_query = "SELECT id, name FROM stores"
        stores = db.execute_query(stores_query)
        if stores:
            print("\n📋 数据库中的门店列表:")
            for store_id, store_name in stores:
                print(f"   - {store_name} (ID: {store_id})")

except Exception as e:
    print(f"\n❌ 查询出错: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()

print("\n" + "="*80)
print("✅ 检查完成")
print("="*80)
