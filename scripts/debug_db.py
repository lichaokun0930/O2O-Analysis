
import sys
import os
from pathlib import Path

# Setup paths
# scripts/debug_db.py -> parent -> O2O-Analysis
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    
print(f"Added to path: {PROJECT_ROOT}")

try:
    # Try importing from 'database' directly (O2O-Analysis/database)
    from database.connection import SessionLocal
    from database.models import Order
    
    session = SessionLocal()
    # Query last 10 orders
    orders = session.query(Order).order_by(Order.date.desc()).limit(10).all()
    
    print(f"Found {len(orders)} orders.")
    for o in orders:
        print(f"Order: {o.order_id}, Date: {o.date} (Hour: {o.date.hour})")
        
    session.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
