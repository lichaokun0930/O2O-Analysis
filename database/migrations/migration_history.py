"""
迁移历史记录表
用于跟踪哪些迁移已经执行过
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db
from sqlalchemy import text

def create_migration_history_table():
    """创建迁移历史记录表"""
    
    db = next(get_db())
    
    try:
        # 创建迁移历史表
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS migration_history (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT NOW(),
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT
            )
        """))
        
        db.commit()
        print("✓ 迁移历史表已创建")
        
    except Exception as e:
        db.rollback()
        print(f"✗ 创建迁移历史表失败: {e}")
        
    finally:
        db.close()


def get_applied_migrations():
    """获取已应用的迁移列表"""
    
    db = next(get_db())
    
    try:
        result = db.execute(text("""
            SELECT migration_name, applied_at 
            FROM migration_history 
            WHERE success = TRUE
            ORDER BY applied_at
        """))
        
        migrations = [(row[0], row[1]) for row in result]
        return migrations
        
    except Exception as e:
        print(f"获取迁移历史失败: {e}")
        return []
        
    finally:
        db.close()


def record_migration(migration_name: str, success: bool = True, error_message: str = None):
    """记录迁移执行历史"""
    
    db = next(get_db())
    
    try:
        db.execute(text("""
            INSERT INTO migration_history (migration_name, success, error_message)
            VALUES (:name, :success, :error)
            ON CONFLICT (migration_name) DO UPDATE
            SET applied_at = NOW(),
                success = :success,
                error_message = :error
        """), {
            'name': migration_name,
            'success': success,
            'error': error_message
        })
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"记录迁移历史失败: {e}")
        
    finally:
        db.close()


if __name__ == "__main__":
    # 创建迁移历史表
    create_migration_history_table()
    
    # 显示已应用的迁移
    migrations = get_applied_migrations()
    
    if migrations:
        print(f"\n已应用的迁移 ({len(migrations)} 个):")
        for name, applied_at in migrations:
            print(f"  ✓ {name} - {applied_at}")
    else:
        print("\n还没有应用任何迁移")
