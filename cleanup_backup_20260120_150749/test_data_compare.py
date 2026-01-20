# -*- coding: utf-8 -*-
"""
数据对比测试：新版本 vs 老版本
"""
import requests
from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import func

print("=" * 70)
print("Data Comparison Test: Old Version (DB) vs New Version (API)")
print("=" * 70)

# 1. 老版本 - 直接查询数据库
session = SessionLocal()
old_orders = session.query(func.count(Order.id)).scalar()
old_stores = session.query(func.count(func.distinct(Order.store_name))).scalar()
old_products = session.query(func.count(func.distinct(Order.product_name))).scalar()

old_store_counts = dict(
    session.query(Order.store_name, func.count(Order.id))
    .group_by(Order.store_name)
    .all()
)
session.close()

# 2. 新版本 - 通过API获取
stats = requests.get("http://localhost:8080/api/v1/data/stats").json()
stores_resp = requests.get("http://localhost:8080/api/v1/data/stores").json()
new_store_counts = {s["value"]: s["order_count"] for s in stores_resp["data"]}

# 3. 对比结果
print()
print("[Statistics Comparison]")
diff1 = old_orders - stats["total_orders"]
diff2 = old_stores - stats["total_stores"]
diff3 = old_products - stats["total_products"]

print(f"  Total Orders:   Old={old_orders:>10,} | New={stats['total_orders']:>10,} | Diff={diff1}")
print(f"  Total Stores:   Old={old_stores:>10} | New={stats['total_stores']:>10} | Diff={diff2}")
print(f"  Total Products: Old={old_products:>10,} | New={stats['total_products']:>10,} | Diff={diff3}")

print()
print("[Store Order Counts]")
all_match = True
for store, old_cnt in sorted(old_store_counts.items()):
    new_cnt = new_store_counts.get(store, 0)
    match = "OK" if old_cnt == new_cnt else "DIFF"
    if old_cnt != new_cnt:
        all_match = False
    short_name = store[:35] + "..." if len(store) > 35 else store
    print(f"  [{match:4}] {short_name}: Old={old_cnt:,} | New={new_cnt:,}")

print()
print("=" * 70)
if all_match and diff1 == 0 and diff2 == 0 and diff3 == 0:
    print("RESULT: ALL DATA MATCHED! New version equals Old version.")
else:
    print("RESULT: DATA MISMATCH! Please check.")
print("=" * 70)

