#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据生命周期管理器
- 历史数据清理
- 空间优化
- 性能监控
"""

import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text, func
from database.connection import SessionLocal, engine
from database.models import Order


class DataLifecycleManager:
    """数据生命周期管理器"""
    
    def __init__(self):
        self.session = SessionLocal()
    
    def get_database_stats(self):
        """获取数据库统计信息"""
        print("\n" + "="*70)
        print("📊 数据库统计信息")
        print("="*70)
        
        stats = {}
        
        try:
            # 1. 总订单数
            total_orders = self.session.query(Order).count()
            stats['total_orders'] = total_orders
            print(f"📦 总订单数: {total_orders:,}")
            
            # 2. 门店数量
            stores = self.session.query(Order.store_name).distinct().all()
            store_list = [s[0] for s in stores if s[0]]
            stats['store_count'] = len(store_list)
            print(f"🏪 门店数量: {len(store_list)}")
            
            # 3. 每个门店的数据量
            print(f"\n门店数据分布:")
            for store in store_list:
                count = self.session.query(Order).filter(
                    Order.store_name == store
                ).count()
                print(f"  • {store}: {count:,} 条")
                stats[f'store_{store}'] = count
            
            # 4. 日期范围
            min_date = self.session.query(func.min(Order.date)).scalar()
            max_date = self.session.query(func.max(Order.date)).scalar()
            stats['min_date'] = min_date
            stats['max_date'] = max_date
            print(f"\n📅 数据范围: {min_date} ~ {max_date}")
            
            # 5. 数据库大小
            size_query = text("""
                SELECT pg_size_pretty(pg_database_size('o2o_dashboard')) as size
            """)
            db_size = self.session.execute(size_query).scalar()
            stats['db_size'] = db_size
            print(f"💾 数据库大小: {db_size}")
            
            # 6. 表大小
            table_size_query = text("""
                SELECT pg_size_pretty(pg_total_relation_size('orders')) as size
            """)
            table_size = self.session.execute(table_size_query).scalar()
            stats['table_size'] = table_size
            print(f"📋 订单表大小: {table_size}")
            
            print("="*70 + "\n")
            return stats
            
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return stats
    
    def clean_old_data(self, days=90, store_name=None, dry_run=True):
        """
        清理历史数据
        
        参数:
            days: 保留最近N天的数据
            store_name: 指定门店（None=全部门店）
            dry_run: True=仅预览，False=真实删除
        """
        print("\n" + "="*70)
        print(f"🗑️  数据清理{'预览' if dry_run else '执行'}")
        print("="*70)
        
        cutoff_date = datetime.now() - timedelta(days=days)
        print(f"📅 保留数据: {cutoff_date.strftime('%Y-%m-%d')} 之后")
        print(f"🗑️  删除数据: {cutoff_date.strftime('%Y-%m-%d')} 之前")
        
        try:
            # 构建查询
            query = self.session.query(Order).filter(Order.date < cutoff_date)
            
            if store_name:
                query = query.filter(Order.store_name == store_name)
                print(f"🏪 门店: {store_name}")
            else:
                print(f"🏪 门店: 全部")
            
            # 统计将要删除的数据
            to_delete = query.count()
            
            if to_delete == 0:
                print(f"\n✅ 没有需要清理的数据")
                return {'deleted': 0, 'dry_run': dry_run}
            
            print(f"\n📊 将删除 {to_delete:,} 条数据")
            
            # 分门店统计
            if not store_name:
                print(f"\n各门店清理统计:")
                stores = self.session.query(Order.store_name).distinct().all()
                for store in stores:
                    if store[0]:
                        count = self.session.query(Order).filter(
                            Order.store_name == store[0],
                            Order.date < cutoff_date
                        ).count()
                        if count > 0:
                            print(f"  • {store[0]}: {count:,} 条")
            
            if dry_run:
                print(f"\n⚠️  这是预览模式，数据未实际删除")
                print(f"   使用 dry_run=False 执行真实删除")
                return {'deleted': 0, 'preview': to_delete, 'dry_run': True}
            
            # 真实删除
            print(f"\n开始删除...")
            deleted = query.delete(synchronize_session=False)
            self.session.commit()
            
            print(f"✅ 成功删除 {deleted:,} 条数据")
            
            # 🔄 VACUUM清理空间 - 必须在自动提交模式下执行
            print(f"\n🧹 正在优化数据库空间...")
            try:
                connection = self.session.connection().connection
                old_isolation_level = connection.isolation_level
                connection.set_isolation_level(0)  # 自动提交模式
                cursor = connection.cursor()
                cursor.execute("VACUUM ANALYZE orders")
                cursor.close()
                connection.set_isolation_level(old_isolation_level)
                print(f"✅ 空间优化完成")
            except Exception as vacuum_error:
                print(f"⚠️ VACUUM执行失败(不影响删除结果): {vacuum_error}")
            
            return {'deleted': deleted, 'dry_run': False}
            
        except Exception as e:
            self.session.rollback()
            print(f"❌ 删除失败: {e}")
            return {'deleted': 0, 'error': str(e)}
    
    def clean_by_date_range(self, start_date, end_date, store_name=None, dry_run=True):
        """
        按日期范围清理数据
        
        参数:
            start_date: 开始日期
            end_date: 结束日期
            store_name: 指定门店
            dry_run: 预览模式
        """
        print("\n" + "="*70)
        print(f"🗑️  按日期范围清理数据{'预览' if dry_run else '执行'}")
        print("="*70)
        
        print(f"📅 清理范围: {start_date} ~ {end_date}")
        
        try:
            query = self.session.query(Order).filter(
                Order.date >= pd.to_datetime(start_date),
                Order.date <= pd.to_datetime(end_date)
            )
            
            if store_name:
                query = query.filter(Order.store_name == store_name)
                print(f"🏪 门店: {store_name}")
            else:
                print(f"🏪 门店: 全部")
            
            to_delete = query.count()
            
            if to_delete == 0:
                print(f"\n✅ 没有符合条件的数据")
                return {'deleted': 0}
            
            print(f"\n📊 将删除 {to_delete:,} 条数据")
            
            if dry_run:
                print(f"\n⚠️  预览模式，数据未实际删除")
                return {'deleted': 0, 'preview': to_delete, 'dry_run': True}
            
            # 真实删除
            deleted = query.delete(synchronize_session=False)
            self.session.commit()
            
            print(f"✅ 成功删除 {deleted:,} 条数据")
            
            # 🔄 优化空间
            try:
                connection = self.session.connection().connection
                old_isolation_level = connection.isolation_level
                connection.set_isolation_level(0)
                cursor = connection.cursor()
                cursor.execute("VACUUM ANALYZE orders")
                cursor.close()
                connection.set_isolation_level(old_isolation_level)
                print("✅ 数据库空间优化完成")
            except Exception as vacuum_error:
                print(f"⚠️ VACUUM执行失败: {vacuum_error}")
            
            return {'deleted': deleted, 'dry_run': False}
            
        except Exception as e:
            self.session.rollback()
            print(f"❌ 删除失败: {e}")
            return {'error': str(e)}
    
    def clean_store_data(self, store_name, dry_run=True, auto_confirm=False):
        """
        清理指定门店的所有数据
        
        参数:
            store_name: 门店名称
            dry_run: 预览模式
            auto_confirm: 自动确认（用于Web界面，跳过交互式确认）
        """
        print("\n" + "="*70)
        print(f"🗑️  清理门店数据{'预览' if dry_run else '执行'}")
        print("="*70)
        
        print(f"🏪 门店: {store_name}")
        
        try:
            to_delete = self.session.query(Order).filter(
                Order.store_name == store_name
            ).count()
            
            if to_delete == 0:
                print(f"\n✅ 门店无数据")
                return {'deleted': 0}
            
            print(f"📊 将删除 {to_delete:,} 条数据")
            
            if dry_run:
                print(f"\n⚠️  预览模式，数据未实际删除")
                return {'deleted': 0, 'preview': to_delete, 'dry_run': True}
            
            # 确认删除（跳过交互式确认如果 auto_confirm=True）
            if not auto_confirm:
                confirm = input(f"\n⚠️  确认删除门店 '{store_name}' 的所有数据? (yes/no): ")
                if confirm.lower() != 'yes':
                    print("操作已取消")
                    return {'deleted': 0, 'cancelled': True}
            else:
                print(f"✅ 自动确认删除（Web界面模式）")
            
            # 真实删除
            deleted = self.session.query(Order).filter(
                Order.store_name == store_name
            ).delete(synchronize_session=False)
            self.session.commit()
            
            print(f"✅ 成功删除 {deleted:,} 条数据")
            
            # 🔄 优化空间 - VACUUM必须在自动提交模式下执行
            try:
                # 关闭当前事务,使用自动提交连接执行VACUUM
                connection = self.session.connection().connection
                old_isolation_level = connection.isolation_level
                connection.set_isolation_level(0)  # 自动提交模式
                cursor = connection.cursor()
                cursor.execute("VACUUM ANALYZE orders")
                cursor.close()
                connection.set_isolation_level(old_isolation_level)  # 恢复原始隔离级别
                print("✅ 数据库空间优化完成")
            except Exception as vacuum_error:
                print(f"⚠️ VACUUM执行失败(不影响删除结果): {vacuum_error}")
            
            return {'deleted': deleted, 'dry_run': False}
            
        except Exception as e:
            self.session.rollback()
            print(f"❌ 删除失败: {e}")
            return {'error': str(e)}
    
    def archive_old_data(self, days=90, archive_path='archived_data'):
        """
        归档历史数据（导出后删除）
        
        参数:
            days: 归档N天前的数据
            archive_path: 归档文件保存路径
        """
        print("\n" + "="*70)
        print(f"📦 归档历史数据")
        print("="*70)
        
        import os
        cutoff_date = datetime.now() - timedelta(days=days)
        
        print(f"📅 归档数据: {cutoff_date.strftime('%Y-%m-%d')} 之前")
        
        try:
            # 查询要归档的数据
            query = self.session.query(Order).filter(Order.date < cutoff_date)
            to_archive = query.count()
            
            if to_archive == 0:
                print(f"✅ 没有需要归档的数据")
                return {'archived': 0}
            
            print(f"📊 将归档 {to_archive:,} 条数据")
            
            # 导出数据
            os.makedirs(archive_path, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 分门店导出
            stores = self.session.query(Order.store_name).distinct().all()
            archived_files = []
            
            for store in stores:
                if not store[0]:
                    continue
                
                store_data = query.filter(Order.store_name == store[0]).all()
                if not store_data:
                    continue
                
                # 转为DataFrame
                data_list = []
                for order in store_data:
                    data_list.append({
                        '订单ID': order.order_id,
                        '日期': order.date,
                        '门店名称': order.store_name,
                        '商品名称': order.product_name,
                        '价格': order.price,
                        '数量': order.quantity,
                        '成本': order.cost,
                        '利润': order.profit,
                        # 更多字段...
                    })
                
                df = pd.DataFrame(data_list)
                filename = f"{archive_path}/归档_{store[0]}_{timestamp}.xlsx"
                df.to_excel(filename, index=False)
                archived_files.append(filename)
                
                print(f"  ✅ {store[0]}: {len(store_data):,} 条 → {filename}")
            
            # 删除已归档数据
            print(f"\n🗑️  删除已归档数据...")
            deleted = query.delete(synchronize_session=False)
            self.session.commit()
            
            print(f"✅ 归档完成: {deleted:,} 条数据")
            print(f"📁 归档文件: {len(archived_files)} 个")
            
            # 🔄 优化空间
            try:
                connection = self.session.connection().connection
                old_isolation_level = connection.isolation_level
                connection.set_isolation_level(0)
                cursor = connection.cursor()
                cursor.execute("VACUUM ANALYZE orders")
                cursor.close()
                connection.set_isolation_level(old_isolation_level)
                print("✅ 数据库空间优化完成")
            except Exception as vacuum_error:
                print(f"⚠️ VACUUM执行失败: {vacuum_error}")
            
            return {
                'archived': deleted,
                'files': archived_files
            }
            
        except Exception as e:
            self.session.rollback()
            print(f"❌ 归档失败: {e}")
            return {'error': str(e)}
    
    def get_data_age_distribution(self):
        """获取数据年龄分布"""
        print("\n" + "="*70)
        print("📅 数据年龄分布")
        print("="*70)
        
        try:
            # 按月统计
            query = text("""
                SELECT 
                    TO_CHAR(date, 'YYYY-MM') as month,
                    COUNT(*) as count
                FROM orders
                WHERE date IS NOT NULL
                GROUP BY TO_CHAR(date, 'YYYY-MM')
                ORDER BY month DESC
                LIMIT 12
            """)
            
            results = self.session.execute(query).fetchall()
            
            print(f"\n最近12个月数据量:")
            total = 0
            for month, count in results:
                print(f"  {month}: {count:,} 条")
                total += count
            
            print(f"\n总计: {total:,} 条")
            
            return results
            
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            return []
    
    def optimize_database(self):
        """优化数据库性能"""
        print("\n" + "="*70)
        print("🔧 优化数据库")
        print("="*70)
        
        try:
            # 🔄 获取原始连接,切换到自动提交模式
            connection = self.session.connection().connection
            old_isolation_level = connection.isolation_level
            connection.set_isolation_level(0)  # 自动提交模式
            cursor = connection.cursor()
            
            # 1. VACUUM FULL（完整清理）
            print("\n1️⃣ 执行 VACUUM FULL（这可能需要几分钟）...")
            cursor.execute("VACUUM FULL orders")
            print("   ✅ VACUUM FULL 完成")
            
            # 2. REINDEX（重建索引）
            print("\n2️⃣ 重建索引...")
            cursor.execute("REINDEX TABLE orders")
            print("   ✅ 索引重建完成")
            
            # 3. ANALYZE（更新统计信息）
            print("\n3️⃣ 更新统计信息...")
            cursor.execute("ANALYZE orders")
            print("   ✅ 统计信息更新完成")
            
            cursor.close()
            connection.set_isolation_level(old_isolation_level)  # 恢复原始隔离级别
            
            print("\n✅ 数据库优化完成！")
            
        except Exception as e:
            print(f"❌ 优化失败: {e}")
    
    def close(self):
        """关闭连接"""
        self.session.close()


def main():
    """主菜单"""
    manager = DataLifecycleManager()
    
    try:
        while True:
            print("\n" + "="*70)
            print("🛠️  数据生命周期管理工具")
            print("="*70)
            print("\n请选择操作:")
            print("  1. 查看数据库统计")
            print("  2. 查看数据年龄分布")
            print("  3. 清理历史数据（保留最近N天）")
            print("  4. 按日期范围清理")
            print("  5. 清理指定门店数据")
            print("  6. 归档历史数据")
            print("  7. 优化数据库")
            print("  0. 退出")
            
            choice = input("\n请输入选项 (0-7): ").strip()
            
            if choice == '1':
                manager.get_database_stats()
                
            elif choice == '2':
                manager.get_data_age_distribution()
                
            elif choice == '3':
                days = input("保留最近多少天的数据? (默认90天): ").strip()
                days = int(days) if days else 90
                
                # 先预览
                manager.clean_old_data(days=days, dry_run=True)
                
                confirm = input("\n确认执行删除? (yes/no): ").strip()
                if confirm.lower() == 'yes':
                    manager.clean_old_data(days=days, dry_run=False)
                
            elif choice == '4':
                start = input("开始日期 (YYYY-MM-DD): ").strip()
                end = input("结束日期 (YYYY-MM-DD): ").strip()
                
                # 先预览
                manager.clean_by_date_range(start, end, dry_run=True)
                
                confirm = input("\n确认执行删除? (yes/no): ").strip()
                if confirm.lower() == 'yes':
                    manager.clean_by_date_range(start, end, dry_run=False)
                
            elif choice == '5':
                stats = manager.get_database_stats()
                store = input("\n输入门店名称: ").strip()
                
                manager.clean_store_data(store, dry_run=False)
                
            elif choice == '6':
                days = input("归档多少天前的数据? (默认90天): ").strip()
                days = int(days) if days else 90
                
                manager.archive_old_data(days=days)
                
            elif choice == '7':
                confirm = input("⚠️  优化可能需要几分钟，继续? (yes/no): ").strip()
                if confirm.lower() == 'yes':
                    manager.optimize_database()
                
            elif choice == '0':
                print("\n👋 再见！")
                break
            
            else:
                print("❌ 无效选项")
            
            input("\n按回车键继续...")
    
    finally:
        manager.close()


if __name__ == "__main__":
    main()
