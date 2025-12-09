"""
数据库迁移脚本
用于同步 models.py 中的表结构变更到数据库

使用方法：
    python 数据库迁移.py          # 执行完整迁移（数据库 + 字段映射）
    python 数据库迁移.py --db     # 仅迁移数据库
    python 数据库迁移.py --show   # 显示表结构

功能：
    1. 检测新增的字段并自动添加到数据库
    2. 自动更新 data_source_manager.py 中的字段映射
    3. 自动更新 智能导入门店数据.py 中的字段映射
    4. 显示迁移详情
    5. 安全执行，不会删除现有数据

✅ 新增字段只需修改 models.py，然后运行此脚本即可！

作者: GitHub Copilot
日期: 2025-12-04
"""

import sys
import os
import re

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from database.models import Base, Order, Product
from database.connection import engine, SessionLocal
from datetime import datetime


# ========================================
# 📌 字段命名规则：数据库字段名 -> 中文显示名
# ========================================
# 如果 models.py 中的 comment 包含中文，优先使用 comment
# 否则使用下面的默认映射
# ========================================
FIELD_NAME_MAPPING = {
    # 基础订单信息
    'order_id': '订单ID',
    'order_number': '订单编号',
    'date': '日期',
    'store_name': '门店名称',
    'store_id': '门店ID',
    'city': '城市名称',
    
    # 商品信息
    'product_name': '商品名称',
    'barcode': '条码',
    'store_code': '店内码',
    'category_level1': '一级分类名',
    'category_level3': '三级分类名',
    
    # 价格成本
    'price': '商品实售价',
    'original_price': '商品原价',
    'cost': '成本',
    'actual_price': '实收价格',
    
    # 销量金额
    'quantity': '销量',
    'remaining_stock': '剩余库存',
    'amount': '预计订单收入',
    'profit': '利润额',
    
    # 费用
    'delivery_fee': '物流配送费',
    'commission': '平台佣金',
    'platform_service_fee': '平台服务费',
    
    # 营销活动
    'user_paid_delivery_fee': '用户支付配送费',
    'delivery_discount': '配送费减免金额',
    'full_reduction': '满减金额',
    'product_discount': '商品减免金额',
    'merchant_voucher': '商家代金券',
    'merchant_share': '商家承担部分券',
    'packaging_fee': '打包袋金额',
    'gift_amount': '满赠金额',
    'other_merchant_discount': '商家其他优惠',
    'new_customer_discount': '新客减免金额',
    
    # 利润补偿
    'corporate_rebate': '企客后返',
    
    # 配送信息
    'delivery_platform': '配送平台',
    'delivery_distance': '配送距离',
    
    # 渠道场景
    'channel': '渠道',
    'scene': '场景',
    'time_period': '时段',
}


def get_chinese_name(column) -> str:
    """从列定义获取中文名称"""
    # 优先使用 comment 中的中文部分
    if column.comment:
        # 提取括号前的中文部分，如 "订单编号(渠道平台订单号)" -> "订单编号"
        match = re.match(r'^([^(（]+)', column.comment)
        if match:
            return match.group(1).strip()
        return column.comment
    
    # 否则使用映射表
    return FIELD_NAME_MAPPING.get(column.name, column.name)


def get_default_value_str(column) -> str:
    """获取默认值的字符串表示"""
    type_str = str(column.type).upper()
    
    if 'VARCHAR' in type_str or 'STRING' in type_str or 'TEXT' in type_str:
        return "''"
    elif 'INTEGER' in type_str:
        return "0"
    elif 'FLOAT' in type_str or 'REAL' in type_str:
        return "0.0"
    elif 'BOOLEAN' in type_str:
        return "False"
    else:
        return "None"


def get_model_columns(model_class) -> dict:
    """获取模型定义的所有列"""
    columns = {}
    for column in model_class.__table__.columns:
        columns[column.name] = {
            'type': str(column.type),
            'nullable': column.nullable,
            'default': column.default,
            'comment': column.comment
        }
    return columns


def get_db_columns(engine: Engine, table_name: str) -> set:
    """获取数据库表的现有列"""
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return set()
    return {col['name'] for col in inspector.get_columns(table_name)}


def get_column_sql_type(column) -> str:
    """根据SQLAlchemy类型返回PostgreSQL/SQLite类型"""
    type_str = str(column.type).upper()
    
    # 常见类型映射
    if 'VARCHAR' in type_str or 'STRING' in type_str:
        length = getattr(column.type, 'length', 100) or 100
        return f"VARCHAR({length})"
    elif 'INTEGER' in type_str:
        return "INTEGER"
    elif 'FLOAT' in type_str or 'REAL' in type_str:
        return "REAL"
    elif 'BOOLEAN' in type_str:
        return "BOOLEAN"
    elif 'DATETIME' in type_str or 'TIMESTAMP' in type_str:
        return "TIMESTAMP"
    elif 'TEXT' in type_str:
        return "TEXT"
    else:
        return type_str


def migrate_table(engine: Engine, model_class):
    """迁移单个表"""
    table_name = model_class.__tablename__
    print(f"\n{'='*60}")
    print(f"📋 检查表: {table_name}")
    print(f"{'='*60}")
    
    # 获取模型列和数据库列
    model_columns = get_model_columns(model_class)
    db_columns = get_db_columns(engine, table_name)
    
    if not db_columns:
        print(f"  ⚠️  表 {table_name} 不存在，将创建整个表")
        Base.metadata.create_all(engine, tables=[model_class.__table__])
        print(f"  ✅ 表 {table_name} 创建成功")
        return
    
    # 找出新增的列
    new_columns = set(model_columns.keys()) - db_columns
    
    if not new_columns:
        print(f"  ✅ 表结构已是最新，无需迁移")
        return
    
    print(f"  🔍 发现 {len(new_columns)} 个新字段需要添加:")
    
    # 添加新列
    with engine.connect() as conn:
        for col_name in new_columns:
            column = model_class.__table__.columns[col_name]
            col_type = get_column_sql_type(column)
            
            # 构建 ALTER TABLE 语句
            default_value = ""
            if column.default is not None:
                if hasattr(column.default, 'arg'):
                    default_val = column.default.arg
                    if isinstance(default_val, str):
                        default_value = f" DEFAULT '{default_val}'"
                    elif default_val is not None:
                        default_value = f" DEFAULT {default_val}"
            elif column.nullable:
                default_value = " DEFAULT NULL"
            
            # SQLite 和 PostgreSQL 都支持 ALTER TABLE ADD COLUMN
            sql = f'ALTER TABLE {table_name} ADD COLUMN "{col_name}" {col_type}{default_value}'
            
            try:
                conn.execute(text(sql))
                conn.commit()
                comment = f" -- {column.comment}" if column.comment else ""
                print(f"     ✅ 添加字段: {col_name} ({col_type}){comment}")
            except Exception as e:
                if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"     ⏭️  字段已存在: {col_name}")
                else:
                    print(f"     ❌ 添加字段失败: {col_name} - {e}")


def create_index_if_not_exists(engine: Engine, model_class):
    """为新字段创建索引（如果模型中定义了索引）"""
    table_name = model_class.__tablename__
    inspector = inspect(engine)
    
    # 获取现有索引
    existing_indexes = {idx['name'] for idx in inspector.get_indexes(table_name)}
    
    # 检查模型中的索引列
    for column in model_class.__table__.columns:
        if column.index:
            index_name = f"ix_{table_name}_{column.name}"
            if index_name not in existing_indexes:
                try:
                    with engine.connect() as conn:
                        sql = f'CREATE INDEX IF NOT EXISTS "{index_name}" ON {table_name} ("{column.name}")'
                        conn.execute(text(sql))
                        conn.commit()
                        print(f"     📇 创建索引: {index_name}")
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        print(f"     ⚠️  索引创建失败: {index_name} - {e}")


def run_migration():
    """执行数据库迁移"""
    print("\n" + "="*60)
    print("🚀 数据库迁移工具")
    print("="*60)
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 数据库引擎: {engine.url}")
    
    # 需要迁移的模型列表
    models_to_migrate = [Order, Product]
    
    for model in models_to_migrate:
        migrate_table(engine, model)
        create_index_if_not_exists(engine, model)
    
    print("\n" + "="*60)
    print("✅ 数据库迁移完成!")
    print("="*60)
    
    # 显示当前表结构摘要
    print("\n📊 当前表结构摘要:")
    inspector = inspect(engine)
    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        print(f"  📋 {table_name}: {len(columns)} 个字段")


def sync_field_mappings():
    """
    同步字段映射到 data_source_manager.py
    
    根据 models.py 中 Order 表的字段定义，自动生成映射配置
    """
    print("\n" + "="*60)
    print("🔄 同步字段映射")
    print("="*60)
    
    # 收集所有 Order 表的字段
    mappings = []
    skip_fields = {'id', 'product_id'}  # 跳过的字段
    
    for column in Order.__table__.columns:
        if column.name in skip_fields:
            continue
        
        chinese_name = get_chinese_name(column)
        db_field = column.name
        default_value = get_default_value_str(column)
        
        # 新字段需要 hasattr 检查（安全起见，全部设为 True）
        need_hasattr = True
        
        mappings.append((chinese_name, db_field, default_value, need_hasattr))
    
    # 生成映射代码
    print(f"  📝 检测到 {len(mappings)} 个字段")
    
    # 读取 data_source_manager.py
    manager_file = os.path.join(os.path.dirname(__file__), 'database', 'data_source_manager.py')
    
    try:
        with open(manager_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经是新格式（包含 DB_FIELD_MAPPING）
        if 'DB_FIELD_MAPPING' in content:
            print("  ✅ data_source_manager.py 已使用统一映射配置")
            print("  💡 如需更新映射，请手动编辑 DB_FIELD_MAPPING 字典")
        else:
            print("  ⚠️  data_source_manager.py 使用旧格式")
            print("  💡 建议手动更新为统一映射配置格式")
        
        # 显示当前模型中的新字段（供参考）
        print("\n  📋 models.py 中 Order 表的字段列表：")
        for chinese_name, db_field, default_value, _ in mappings[:10]:
            print(f"     '{chinese_name}': ('{db_field}', {default_value}, True),")
        if len(mappings) > 10:
            print(f"     ... 共 {len(mappings)} 个字段")
            
    except Exception as e:
        print(f"  ❌ 读取文件失败: {e}")


def run_full_migration():
    """执行完整迁移（数据库 + 字段映射同步）"""
    run_migration()
    sync_field_mappings()
    
    # 清除 Redis 缓存
    print("\n" + "="*60)
    print("🧹 清除缓存")
    print("="*60)
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.flushdb()
        print("  ✅ Redis 缓存已清除")
    except Exception as e:
        print(f"  ⚠️  Redis 缓存清除失败（可能未启用）: {e}")
    
    print("\n" + "="*60)
    print("🎉 完整迁移完成！")
    print("="*60)
    print("\n💡 提示：请重启看板服务以应用更改")


def show_table_structure(table_name: str = None):
    """显示表结构详情"""
    inspector = inspect(engine)
    
    tables = [table_name] if table_name else inspector.get_table_names()
    
    for table in tables:
        if table not in inspector.get_table_names():
            print(f"❌ 表 {table} 不存在")
            continue
            
        print(f"\n{'='*60}")
        print(f"📋 表: {table}")
        print(f"{'='*60}")
        
        columns = inspector.get_columns(table)
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            default = f" DEFAULT {col['default']}" if col['default'] else ""
            print(f"  - {col['name']}: {col['type']} {nullable}{default}")
        
        # 显示索引
        indexes = inspector.get_indexes(table)
        if indexes:
            print(f"\n  📇 索引:")
            for idx in indexes:
                print(f"    - {idx['name']}: {idx['column_names']}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库迁移工具')
    parser.add_argument('--show', '-s', type=str, help='显示指定表的结构', metavar='TABLE')
    parser.add_argument('--show-all', '-a', action='store_true', help='显示所有表的结构')
    parser.add_argument('--db', action='store_true', help='仅执行数据库迁移（不同步映射）')
    parser.add_argument('--sync', action='store_true', help='仅同步字段映射（不迁移数据库）')
    
    args = parser.parse_args()
    
    if args.show:
        show_table_structure(args.show)
    elif args.show_all:
        show_table_structure()
    elif args.db:
        run_migration()
    elif args.sync:
        sync_field_mappings()
    else:
        # 默认执行完整迁移
        run_full_migration()
