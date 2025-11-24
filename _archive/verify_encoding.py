from database.connection import get_db_context
from database.models import Order
import sys

# 设置控制台输出编码为utf-8
sys.stdout.reconfigure(encoding='utf-8')

print("="*50)
print("🔍 验证数据库编码和数据导入情况")
print("="*50)

try:
    with get_db_context() as db:
        # 1. 检查所有门店名称
        print("\n1. 检查门店名称列表:")
        stores = db.query(Order.store_name).distinct().all()
        store_names = [s[0] for s in stores]
        
        for name in store_names:
            print(f"   - {name}")
            
        # 2. 检查祥和路店数据
        target = "惠宜选超市（徐州祥和路店）"
        print(f"\n2. 检查目标门店: {target}")
        
        if target in store_names:
            count = db.query(Order).filter(Order.store_name == target).count()
            print(f"   ✅ 找到门店数据! 订单行数: {count}")
            
            # 3. 检查利润额 (深入分析)
            print(f"\n3. 利润额分析:")
            
            # 方式1: 直接累加 (假设是商品级利润)
            profit_rows = db.query(Order.profit).filter(Order.store_name == target).all()
            total_profit_sum = sum(p[0] or 0 for p in profit_rows)
            print(f"   💰 方式1 [直接累加所有行]: {total_profit_sum:,.2f} (当前结果)")
            
            # 方式2: 按订单去重 (假设是订单级利润，每行重复)
            orders = db.query(Order.order_id, Order.profit).filter(Order.store_name == target).all()
            unique_profits = {}
            for oid, p in orders:
                # 记录每个订单的利润（假设同一订单的利润值在每行都一样，取最后一个覆盖即可）
                unique_profits[oid] = p or 0
            
            total_profit_dedup = sum(unique_profits.values())
            print(f"   💰 方式2 [按订单ID去重]:   {total_profit_dedup:,.2f} (推测真实值)")
            
            print(f"\n   📊 差异分析:")
            print(f"      订单数: {len(unique_profits)}")
            print(f"      总行数: {len(profit_rows)}")
            print(f"      平均每单行数: {len(profit_rows)/len(unique_profits):.1f}")
            if total_profit_dedup > 0:
                print(f"      倍数关系: {total_profit_sum/total_profit_dedup:.1f}倍")
        else:
            print(f"   ❌ 未找到该门店! 当前存在的门店: {store_names}")

except Exception as e:
    print(f"\n❌ 验证过程出错: {e}")
