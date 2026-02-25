# -*- coding: utf-8 -*-
"""
清理导入历史记录

当你删除了订单数据但想重新导入同一个文件时，需要先清理导入历史记录。
批量导入工具通过文件哈希判断是否已导入，如果历史记录存在则会跳过该文件。

使用场景：
1. 删除了 orders 表数据后想重新导入
2. 修改了 Excel 文件内容后想重新导入（文件哈希会变化，通常不需要清理）
3. 想要全量重新导入所有数据

使用方式：
    python 清理导入历史记录.py           # 交互式清理
    python 清理导入历史记录.py --force   # 强制清理（不询问）
    python 清理导入历史记录.py --check   # 仅查看历史记录
"""

import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal, init_database
from database.models import DataUploadHistory, Order
from sqlalchemy import func


def show_history(session):
    """显示当前导入历史"""
    records = session.query(DataUploadHistory).order_by(DataUploadHistory.uploaded_at.desc()).all()
    
    if not records:
        print("📋 导入历史记录为空")
        return False
    
    print(f"\n{'='*70}")
    print(f"📋 当前导入历史记录 ({len(records)} 条)")
    print(f"{'='*70}")
    
    for r in records:
        status = "✅" if r.success else "❌"
        print(f"{status} {r.file_name}")
        print(f"   导入时间: {r.uploaded_at}")
        print(f"   导入行数: {r.rows_imported:,}")
        print(f"   文件哈希: {r.file_hash[:16]}..." if r.file_hash else "   文件哈希: 无")
        print()
    
    return True


def show_database_status(session):
    """显示数据库当前状态"""
    print(f"\n{'='*70}")
    print("📊 数据库当前状态")
    print(f"{'='*70}")
    
    # 订单数
    order_count = session.query(func.count(Order.id)).scalar() or 0
    unique_orders = session.query(func.count(func.distinct(Order.order_id))).scalar() or 0
    store_count = session.query(func.count(func.distinct(Order.store_name))).scalar() or 0
    
    print(f"   订单行数: {order_count:,}")
    print(f"   唯一订单: {unique_orders:,}")
    print(f"   门店数量: {store_count}")
    
    if order_count == 0:
        print("\n⚠️  数据库中没有订单数据，但导入历史记录可能还存在")
        print("   这会导致重新导入时提示'文件已导入过'")


def clear_history(session, force=False):
    """清理导入历史"""
    records = session.query(DataUploadHistory).all()
    
    if not records:
        print("📋 导入历史记录为空，无需清理")
        return
    
    if not force:
        confirm = input(f"\n是否清理所有 {len(records)} 条导入历史记录？(y/n): ").strip().lower()
        if confirm != 'y':
            print("⏭️ 已取消清理")
            return
    
    deleted = session.query(DataUploadHistory).delete()
    session.commit()
    
    print(f"\n✅ 已清理 {deleted} 条导入历史记录")
    print("💡 现在可以重新运行批量导入脚本了：")
    print("   .\\一键批量导入数据.ps1")


def main():
    parser = argparse.ArgumentParser(description='清理导入历史记录')
    parser.add_argument('--force', '-f', action='store_true', help='强制清理，不询问确认')
    parser.add_argument('--check', '-c', action='store_true', help='仅查看历史记录，不清理')
    args = parser.parse_args()
    
    init_database()
    session = SessionLocal()
    
    try:
        # 显示数据库状态
        show_database_status(session)
        
        # 显示历史记录
        has_history = show_history(session)
        
        # 如果只是查看，到此结束
        if args.check:
            return
        
        # 清理历史记录
        if has_history:
            clear_history(session, force=args.force)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    main()
