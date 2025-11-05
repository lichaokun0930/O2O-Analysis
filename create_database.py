"""
创建PostgreSQL数据库
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 数据库配置
DB_USER = "postgres"
DB_PASSWORD = "308352588"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "o2o_dashboard"

print("="*80)
print("  Creating PostgreSQL Database")
print("="*80)

try:
    # 连接到默认的postgres数据库
    print(f"\n[1/3] Connecting to PostgreSQL server...")
    conn = psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    print(f"✅ Connected successfully!")
    
    # 检查数据库是否已存在
    print(f"\n[2/3] Checking if database '{DB_NAME}' exists...")
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (DB_NAME,)
    )
    exists = cursor.fetchone()
    
    if exists:
        print(f"ℹ️  Database '{DB_NAME}' already exists")
    else:
        # 创建数据库
        print(f"[3/3] Creating database '{DB_NAME}'...")
        cursor.execute(f'CREATE DATABASE {DB_NAME}')
        print(f"✅ Database '{DB_NAME}' created successfully!")
    
    cursor.close()
    conn.close()
    
    # 验证数据库连接
    print(f"\n[Verification] Testing connection to '{DB_NAME}'...")
    test_conn = psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )
    test_conn.close()
    print(f"✅ Connection verified!")
    
    print("\n" + "="*80)
    print("  Database Setup Complete!")
    print("="*80)
    print(f"\nDatabase: {DB_NAME}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"User: {DB_USER}")
    print("\nNext steps:")
    print("  1. Initialize tables and import data:")
    print("     python database/migrate.py")
    print("  2. Start backend API:")
    print("     python backend/main.py")
    print("  3. Start frontend dashboard:")
    print("     python 智能门店看板_Dash版.py")
    print("\n" + "="*80)
    
except psycopg2.Error as e:
    print(f"\n❌ Database error: {e}")
    print("\nPlease check:")
    print("  1. PostgreSQL service is running")
    print("  2. Password is correct")
    print("  3. User 'postgres' has permission to create databases")
    exit(1)
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    exit(1)
