"""
自动同步所有未应用的迁移
B电脑从Git拉取代码后执行此脚本
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from migration_history import create_migration_history_table, get_applied_migrations
from apply_migration import apply_migration

def sync_migrations():
    """自动应用所有未执行的迁移"""
    
    print("="*60)
    print("数据库迁移同步")
    print("="*60)
    
    # 确保迁移历史表存在
    create_migration_history_table()
    
    # 获取已应用的迁移
    applied = set(name for name, _ in get_applied_migrations())
    print(f"\n已应用的迁移: {len(applied)} 个")
    
    # 获取所有迁移文件
    migrations_dir = Path(__file__).parent
    migration_files = sorted([
        f.name for f in migrations_dir.glob('v*.sql')
    ])
    
    print(f"发现迁移文件: {len(migration_files)} 个")
    
    # 找出未应用的迁移
    pending = [f for f in migration_files if f not in applied]
    
    if not pending:
        print("\n✓ 所有迁移都已应用,无需同步")
        return True
    
    print(f"\n待应用的迁移: {len(pending)} 个")
    for f in pending:
        print(f"  - {f}")
    
    # 应用未执行的迁移
    print(f"\n{'='*60}")
    print("开始应用迁移...")
    print(f"{'='*60}")
    
    success_count = 0
    failed_count = 0
    
    for migration_file in pending:
        if apply_migration(migration_file):
            success_count += 1
        else:
            failed_count += 1
    
    # 汇总结果
    print(f"\n{'='*60}")
    print("同步结果")
    print(f"{'='*60}")
    print(f"成功: {success_count} 个")
    print(f"失败: {failed_count} 个")
    
    if failed_count == 0:
        print("\n✓ 数据库结构同步完成!")
        return True
    else:
        print(f"\n✗ 有 {failed_count} 个迁移失败,请检查错误信息")
        return False


if __name__ == "__main__":
    success = sync_migrations()
    
    if success:
        print("\n下一步: 验证数据库结构")
        print("  python database\\migrations\\check_structure.py")
    
    sys.exit(0 if success else 1)
