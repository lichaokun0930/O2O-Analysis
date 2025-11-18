"""验证订单级字段是否重复"""
from database.connection import SessionLocal
from database.models import Order

session = SessionLocal()

# 查找有多个商品的订单
orders = session.query(Order).filter(Order.order_id == '2214490659').all()

print(f'订单 2214490659 包含 {len(orders)} 个商品:')
print(f"{'商品名称':<30} {'配送费':>10} {'佣金':>10} {'利润额':>10}")
print('-'*70)

for o in orders[:10]:
    print(f"{o.product_name:<30} {o.delivery_fee:>10.2f} {o.commission:>10.2f} {o.profit:>10.2f}")

# 统计这个订单的总值
total_delivery = sum([o.delivery_fee for o in orders])
total_commission = sum([o.commission for o in orders])
total_profit = sum([o.profit for o in orders])

print('\n如果直接SUM汇总:')
print(f"总配送费: {total_delivery:.2f} 元（{len(orders)} 个商品 × {orders[0].delivery_fee:.2f}）")
print(f"总佣金: {total_commission:.2f} 元（{len(orders)} 个商品 × {orders[0].commission:.2f}）")
print(f"总利润: {total_profit:.2f} 元")

print('\n✅ 正确做法（按订单聚合后取first）:')
print(f"订单配送费: {orders[0].delivery_fee:.2f} 元（取first，不重复）")
print(f"订单佣金: {orders[0].commission:.2f} 元（取first，不重复）")
print(f"订单利润: {total_profit:.2f} 元（商品级，应该sum）")

session.close()
