from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import func

session = SessionLocal()

# 检查字段
sample = session.query(Order).first()
print("Order表库存字段检查:")
print(f"  stock: {sample.stock}")
print(f"  remaining_stock: {sample.remaining_stock}")

# 统计有库存的数据
stock_count = session.query(Order).filter(Order.remaining_stock.isnot(None), Order.remaining_stock > 0).count()
print(f"\n库存 > 0 的记录数: {stock_count:,} / 22,780")

# 查看有库存的示例
if stock_count > 0:
    orders = session.query(Order).filter(Order.remaining_stock > 0).limit(5).all()
    print("\n有库存的商品示例:")
    for o in orders:
        print(f"  {o.product_name}: 剩余库存={o.remaining_stock}")
else:
    print("\n⚠️ 所有记录的剩余库存字段都为0或NULL!")

session.close()
