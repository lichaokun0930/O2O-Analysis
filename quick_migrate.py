"""
Simplified Migration Script - No Emoji
"""
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db_context, init_database, check_connection
from database.models import Order, Product

print("="*80)
print("Database Migration: Excel -> PostgreSQL")
print("="*80)

# Check database connection
if not check_connection():
    print("[ERROR] Database connection failed!")
    sys.exit(1)

# Initialize database tables
init_database()

# Load data
print("\n[Loading Excel data...]")
# 使用绝对路径
import glob
data_dir = r"D:\Python1\O2O_Analysis\O2O数据分析\测算模型\实际数据"
excel_files = glob.glob(f"{data_dir}\\*.xlsx")

if not excel_files:
    print(f"[ERROR] No Excel files found in: {data_dir}")
    sys.exit(1)

excel_file = excel_files[0]  # Use first Excel file found
print(f"[Loading] {Path(excel_file).name}")

df = pd.read_excel(excel_file)
print(f"[OK] Loaded {len(df)} rows")

# Import data
print("\n[Importing to database...]")

with get_db_context() as db:
    # Import products first
    print("  [1/2] Importing products...")
    products_dict = {}
    product_count = 0
    
    for product_name in df['商品名称'].unique():
        product_rows = df[df['商品名称'] == product_name].iloc[0]
        
        try:
            barcode = str(product_rows.get('条码', ''))
            
            # Check if exists
            product = db.query(Product).filter(Product.barcode == barcode).first()
            
            if not product:
                product = Product(
                    product_name=product_name,
                    barcode=barcode,
                    category_level1=product_rows.get('一级分类名', ''),
                    category_level3=product_rows.get('三级分类名', ''),
                    current_price=float(product_rows.get('商品实售价', 0)),
                    current_cost=float(product_rows.get('商品采购成本', 0)),
                )
                db.add(product)
                db.flush()
                product_count += 1
            
            products_dict[product_name] = product.id
            
        except Exception as e:
            print(f"    [WARNING] Product import error: {product_name} - {e}")
    
    db.commit()
    print(f"  [OK] Imported {product_count} products")
    
    # Import orders
    print("  [2/2] Importing orders...")
    order_count = 0
    
    for idx, row in df.iterrows():
        try:
            order = Order(
                order_id=str(row['订单ID']),
                date=pd.to_datetime(row.get('下单时间', datetime.now())),
                store_name=row.get('门店名称', ''),
                product_id=products_dict.get(row['商品名称']),
                product_name=row['商品名称'],
                barcode=str(row.get('条码', '')),
                category_level1=row.get('一级分类名', ''),
                category_level3=row.get('三级分类名', ''),
                price=float(row.get('商品实售价', 0)),
                original_price=float(row.get('商品原价', 0)),
                cost=float(row.get('商品采购成本', 0)),
                quantity=int(row.get('月售', 1)),
                amount=float(row.get('预计订单收入', 0)),
                profit=float(row.get('实际利润', 0)),
                delivery_fee=float(row.get('物流配送费', 0)),
                commission=float(row.get('平台佣金', 0)),
                channel=row.get('渠道', ''),
            )
            
            db.add(order)
            order_count += 1
            
            # Commit every 1000 records
            if order_count % 1000 == 0:
                db.commit()
                print(f"    Progress: {order_count}/{len(df)} orders")
                
        except Exception as e:
            print(f"    [WARNING] Order import error (row {idx}): {e}")
    
    db.commit()
    print(f"  [OK] Imported {order_count} orders")

print("\n" + "="*80)
print("[SUCCESS] Migration completed!")
print("="*80)
print(f"\nImported:")
print(f"  - Products: {len(products_dict)}")
print(f"  - Orders: {order_count}")
print("\nDatabase is ready! You can now:")
print("  1. Start backend: python backend/main.py")
print("  2. Start frontend: python 智能门店看板_Dash版.py")
print("="*80)
