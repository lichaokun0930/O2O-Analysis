"""检查数据库索引"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import engine
from sqlalchemy import text

print("="*80)
print("📊 检查Orders表索引")
print("="*80)

with engine.connect() as conn:
    # 检查现有索引
    result = conn.execute(text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename='orders' 
        ORDER BY indexname
    """))
    
    indexes = result.fetchall()
    print(f"\n✅ 当前索引数量: {len(indexes)}")
    for idx_name, idx_def in indexes:
        print(f"\n  📌 {idx_name}")
        print(f"     {idx_def}")
    
    # 检查表大小
    result = conn.execute(text("""
        SELECT 
            pg_size_pretty(pg_total_relation_size('orders')) as total_size,
            pg_size_pretty(pg_relation_size('orders')) as table_size,
            pg_size_pretty(pg_indexes_size('orders')) as indexes_size
    """))
    
    sizes = result.fetchone()
    print(f"\n📦 存储统计:")
    print(f"  总大小: {sizes[0]}")
    print(f"  表大小: {sizes[1]}")
    print(f"  索引大小: {sizes[2]}")
    
    # 检查记录数
    result = conn.execute(text("SELECT COUNT(*) FROM orders"))
    count = result.fetchone()[0]
    print(f"\n📊 记录数: {count:,}")

print("\n" + "="*80)
