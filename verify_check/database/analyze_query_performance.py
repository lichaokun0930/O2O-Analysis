"""分析数据库查询性能"""
import sys
from pathlib import Path
import time
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import engine
from sqlalchemy import text

print("="*80)
print("⚡ 数据库查询性能分析")
print("="*80)

# 测试查询
test_queries = [
    {
        "name": "查询1: 全表查询(不推荐)",
        "sql": "SELECT * FROM orders LIMIT 1000",
        "desc": "获取前1000条记录"
    },
    {
        "name": "查询2: 按日期范围查询",
        "sql": """
            SELECT * FROM orders 
            WHERE date >= '2025-10-01' AND date <= '2025-10-31'
        """,
        "desc": "查询2025年10月数据"
    },
    {
        "name": "查询3: 按门店名称查询",
        "sql": """
            SELECT * FROM orders 
            WHERE store_name = '新沂2店'
        """,
        "desc": "查询特定门店"
    },
    {
        "name": "查询4: 复合条件查询(日期+门店)",
        "sql": """
            SELECT * FROM orders 
            WHERE date >= '2025-10-01' 
            AND date <= '2025-10-31'
            AND store_name = '新沂2店'
        """,
        "desc": "查询特定门店的10月数据"
    },
    {
        "name": "查询5: JOIN查询(Orders+Products)",
        "sql": """
            SELECT o.*, p.store_code
            FROM orders o
            LEFT JOIN products p ON o.barcode = p.barcode
            WHERE o.date >= '2025-10-01' 
            AND o.date <= '2025-10-31'
            LIMIT 1000
        """,
        "desc": "JOIN查询商品信息"
    },
]

with engine.connect() as conn:
    # 测试每个查询
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"📊 {query['name']}")
        print(f"   {query['desc']}")
        print(f"{'='*80}")
        
        # 获取执行计划
        explain_sql = f"EXPLAIN ANALYZE {query['sql']}"
        
        start_time = time.time()
        result = conn.execute(text(explain_sql))
        explain_output = result.fetchall()
        elapsed = (time.time() - start_time) * 1000  # 转换为毫秒
        
        print(f"\n⏱️  执行时间: {elapsed:.2f}ms")
        print(f"\n📋 执行计划:")
        for line in explain_output:
            print(f"   {line[0]}")
        
        # 实际执行查询获取结果数
        result = conn.execute(text(query['sql']))
        rows = result.fetchall()
        print(f"\n✅ 返回记录数: {len(rows):,}")

print(f"\n{'='*80}")
print("🎯 性能分析建议")
print(f"{'='*80}")

# 检查慢查询
with engine.connect() as conn:
    # 检查是否有门店名称索引
    result = conn.execute(text("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename='orders' 
        AND indexname LIKE '%store%'
    """))
    store_indexes = result.fetchall()
    
    if not store_indexes:
        print("\n⚠️  未发现store_name索引,可能影响按门店查询性能")
        print("   建议: CREATE INDEX idx_store_name ON orders (store_name)")
    else:
        print(f"\n✅ 已有门店相关索引: {[idx[0] for idx in store_indexes]}")
    
    # 检查date索引
    result = conn.execute(text("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename='orders' 
        AND indexname LIKE '%date%'
    """))
    date_indexes = result.fetchall()
    print(f"✅ 已有日期相关索引: {[idx[0] for idx in date_indexes]}")

print(f"\n{'='*80}")
