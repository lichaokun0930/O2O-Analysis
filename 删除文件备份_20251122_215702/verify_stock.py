from database.connection import SessionLocal
from database.models import Order

session = SessionLocal()

total = session.query(Order).count()
with_stock = session.query(Order).filter(Order.remaining_stock > 0).count()

print(f"Order表记录数: {total:,}")
print(f"有库存的记录数: {with_stock:,} ({with_stock/total*100:.1f}%)")

if with_stock > 0:
    sample = session.query(Order).filter(Order.remaining_stock > 0).first()
    print(f"\n✅ 示例记录:")
    print(f"  商品: {sample.product_name}")
    print(f"  剩余库存: {sample.remaining_stock}")
    print(f"  销量: {sample.quantity}")
else:
    print("\n❌ 所有记录的剩余库存都为0!")

session.close()
