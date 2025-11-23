"""
检查数据库结构是否与models.py一致
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db
from database.models import Order
from sqlalchemy import text, inspect

def check_structure():
    """检查数据库结构与models.py是否一致"""
    
    print("="*60)
    print("数据库结构一致性检查")
    print("="*60)
    
    db = next(get_db())
    
    try:
        # 1. 获取数据库字段
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'orders'
            ORDER BY ordinal_position
        """))
        
        db_columns = {row[0]: {
            'type': row[1],
            'nullable': row[2] == 'YES',
            'default': row[3]
        } for row in result}
        
        print(f"\n数据库字段数: {len(db_columns)}")
        
        # 2. 获取models.py字段
        inspector = inspect(Order)
        model_columns = {col.name: col for col in inspector.columns}
        
        print(f"models.py字段数: {len(model_columns)}")
        
        # 3. 对比差异
        db_only = set(db_columns.keys()) - set(model_columns.keys())
        model_only = set(model_columns.keys()) - set(db_columns.keys())
        common = set(db_columns.keys()) & set(model_columns.keys())
        
        print(f"\n{'='*60}")
        print("对比结果")
        print(f"{'='*60}")
        
        # 数据库独有字段
        if db_only:
            print(f"\n⚠ 数据库独有字段 ({len(db_only)} 个):")
            for field in sorted(db_only):
                print(f"  - {field} ({db_columns[field]['type']})")
        
        # models.py独有字段
        if model_only:
            print(f"\n⚠ models.py独有字段 ({len(model_only)} 个):")
            for field in sorted(model_only):
                print(f"  - {field}")
        
        # 共有字段
        print(f"\n✓ 共有字段 ({len(common)} 个)")
        
        # 4. 判断是否一致
        if db_only or model_only:
            print(f"\n{'='*60}")
            print("✗ 数据库结构不一致!")
            print(f"{'='*60}")
            
            if model_only:
                print("\n建议操作:")
                print("1. 创建迁移脚本添加缺失字段")
                print("2. 或运行: python 同步数据库结构.py")
            
            return False
        else:
            print(f"\n{'='*60}")
            print("✓ 数据库结构完全一致!")
            print(f"{'='*60}")
            return True
        
    except Exception as e:
        print(f"\n✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = check_structure()
    sys.exit(0 if success else 1)
