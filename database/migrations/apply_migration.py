"""
应用单个迁移脚本
"""

import sys
from pathlib import Path
import argparse

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db
from sqlalchemy import text
from migration_history import record_migration, get_applied_migrations

def apply_migration(migration_file: str):
    """
    应用迁移脚本
    
    Args:
        migration_file: 迁移文件名(如 v1_add_stock_fields.sql)
    """
    
    migration_path = Path(__file__).parent / migration_file
    
    if not migration_path.exists():
        print(f"✗ 迁移文件不存在: {migration_file}")
        return False
    
    # 检查是否已应用
    applied = [name for name, _ in get_applied_migrations()]
    if migration_file in applied:
        print(f"⊙ 迁移已应用过: {migration_file}")
        return True
    
    print(f"\n{'='*60}")
    print(f"应用迁移: {migration_file}")
    print(f"{'='*60}")
    
    # 读取SQL
    with open(migration_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # 执行迁移
    db = next(get_db())
    
    try:
        # 执行SQL
        db.execute(text(sql))
        db.commit()
        
        # 记录成功
        record_migration(migration_file, success=True)
        
        print(f"\n✓ 迁移应用成功: {migration_file}")
        return True
        
    except Exception as e:
        db.rollback()
        
        # 记录失败
        error_msg = str(e)
        record_migration(migration_file, success=False, error_message=error_msg)
        
        print(f"\n✗ 迁移应用失败: {migration_file}")
        print(f"错误: {error_msg}")
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='应用数据库迁移')
    parser.add_argument('migration', help='迁移文件名(如 v1_add_stock_fields.sql)')
    
    args = parser.parse_args()
    
    success = apply_migration(args.migration)
    sys.exit(0 if success else 1)
