"""
数据库结构自动同步脚本
一键添加所有缺失字段,确保models.py与数据库结构完全一致
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db
from sqlalchemy import text

def sync_database_structure():
    """同步数据库结构,添加所有缺失字段"""
    
    print("="*60)
    print("数据库结构自动同步")
    print("="*60)
    
    # 定义所有需要同步的字段
    fields_to_add = [
        {
            'name': 'stock',
            'type': 'INTEGER',
            'default': '0',
            'comment': '库存'
        },
        {
            'name': 'remaining_stock',
            'type': 'FLOAT',
            'default': '0',
            'comment': '剩余库存'
        },
        {
            'name': 'delivery_distance',
            'type': 'FLOAT',
            'default': '0',
            'comment': '配送距离(公里)'
        },
        {
            'name': 'store_id',
            'type': 'VARCHAR(100)',
            'default': 'NULL',
            'comment': '门店ID'
        },
        {
            'name': 'city',
            'type': 'VARCHAR(100)',
            'default': 'NULL',
            'comment': '城市'
        }
    ]
    
    db = next(get_db())
    added_fields = []
    existing_fields = []
    
    try:
        for field in fields_to_add:
            print(f"\n检查字段: {field['name']}")
            
            # 检查字段是否已存在
            check_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'orders' 
                AND column_name = :field_name
            """)
            
            result = db.execute(check_sql, {'field_name': field['name']})
            exists = result.fetchone() is not None
            
            if exists:
                print(f"  ✓ 字段已存在: {field['name']}")
                existing_fields.append(field['name'])
            else:
                # 添加字段
                default_clause = f"DEFAULT {field['default']}" if field['default'] != 'NULL' else ''
                
                add_sql = text(f"""
                    ALTER TABLE orders 
                    ADD COLUMN {field['name']} {field['type']} {default_clause}
                """)
                
                db.execute(add_sql)
                
                # 添加注释
                comment_sql = text(f"""
                    COMMENT ON COLUMN orders.{field['name']} IS '{field['comment']}'
                """)
                db.execute(comment_sql)
                
                print(f"  + 已添加字段: {field['name']} ({field['type']})")
                added_fields.append(field['name'])
        
        db.commit()
        
        # 验证结果
        print("\n" + "="*60)
        print("同步结果")
        print("="*60)
        print(f"已存在字段: {len(existing_fields)} 个")
        if existing_fields:
            for f in existing_fields:
                print(f"  - {f}")
        
        print(f"\n新增字段: {len(added_fields)} 个")
        if added_fields:
            for f in added_fields:
                print(f"  + {f}")
        
        # 查询最终字段列表
        result = db.execute(text("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'orders'
            ORDER BY ordinal_position
        """))
        
        print(f"\n当前orders表共有 {result.rowcount} 个字段")
        
        print("\n" + "="*60)
        print("✓ 数据库结构同步完成!")
        print("="*60)
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ 同步失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()


if __name__ == "__main__":
    print("\n此脚本将自动同步数据库结构,添加所有缺失字段")
    print("适用场景: 从B电脑克隆代码后同步数据库")
    print("\n开始同步...")
    
    success = sync_database_structure()
    
    if success:
        print("\n下一步: 重启看板验证功能")
        print("  .\\启动看板.ps1")
    else:
        print("\n请检查数据库连接和权限")
