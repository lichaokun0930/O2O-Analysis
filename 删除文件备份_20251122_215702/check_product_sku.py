from database.connection import SessionLocal
from database.models import Product, SKU

session = SessionLocal()

print("=== Product表检查 ===")
prod_count = session.query(Product).count()
print(f"Product总数: {prod_count}")

if prod_count > 0:
    sample = session.query(Product).first()
    print(f"示例数据:")
    print(f"  barcode: {sample.barcode}")
    print(f"  product_name: {sample.product_name}")
    print(f"  stock: {sample.stock}")
    print(f"  store_code: {sample.store_code}")

print(f"\n=== SKU表检查 ===")
sku_count = session.query(SKU).count()
print(f"SKU总数: {sku_count}")

if sku_count > 0:
    sku_sample = session.query(SKU).first()
    print(f"示例数据:")
    print(f"  sku_id: {sku_sample.sku_id}")
    print(f"  product_name: {sku_sample.product_name}")
    print(f"  turnover_days: {sku_sample.turnover_days}")
    print(f"  is_slow_moving: {sku_sample.is_slow_moving}")

session.close()
