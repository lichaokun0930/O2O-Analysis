"""
数据库表结构自动升级脚本（无需确认）
为Order表添加营销活动、配送距离、城市、门店ID等字段
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.connection import engine, check_connection

def auto_upgrade():
    """自动升级Order表结构"""
    
    print("="*80)
    print("🔧 自动升级Order表结构")
    print("="*80)
    
    if not check_connection():
        print("❌ 数据库连接失败！")
        return False
    
    new_columns = [
        ("user_paid_delivery_fee", "FLOAT DEFAULT 0"),
        ("delivery_discount", "FLOAT DEFAULT 0"),
        ("full_reduction", "FLOAT DEFAULT 0"),
        ("product_discount", "FLOAT DEFAULT 0"),
        ("merchant_voucher", "FLOAT DEFAULT 0"),
        ("merchant_share", "FLOAT DEFAULT 0"),
        ("packaging_fee", "FLOAT DEFAULT 0"),
        ("delivery_distance", "FLOAT DEFAULT 0"),
        ("city", "VARCHAR(50)"),
        ("store_id", "VARCHAR(50)"),
    ]
    
    added = 0
    skipped = 0
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                for col_name, col_type in new_columns:
                    # 检查字段是否存在
                    check_sql = text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'orders' 
                        AND column_name = :col_name
                    """)
                    result = conn.execute(check_sql, {"col_name": col_name})
                    exists = result.fetchone() is not None
                    
                    if exists:
                        print(f"  ⏭️  {col_name:30s} - 已存在")
                        skipped += 1
                    else:
                        alter_sql = text(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}")
                        conn.execute(alter_sql)
                        print(f"  ✅ {col_name:30s} - 已添加")
                        added += 1
                
                # 添加索引
                try:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_city ON orders (city)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_store_id ON orders (store_id)"))
                    print(f"\n  ✅ 索引已创建")
                except:
                    pass
                
                trans.commit()
                
                print("\n" + "="*80)
                print(f"✅ 升级完成！新增 {added} 个字段，跳过 {skipped} 个已存在字段")
                print("="*80)
                
                # 验证结果
                count_sql = text("SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'orders'")
                result = conn.execute(count_sql)
                total = result.fetchone()[0]
                print(f"\n📊 Order表当前总字段数: {total}")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"\n❌ 升级失败: {e}")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"\n❌ 连接错误: {e}")
        return False

if __name__ == "__main__":
    auto_upgrade()
