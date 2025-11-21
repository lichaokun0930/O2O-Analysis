"""
数据库表结构升级脚本
为Order表添加营销活动、配送距离、城市、门店ID等字段
优先级：P0 - 支持完整字段映射
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.connection import engine, check_connection

def upgrade_order_table():
    """升级Order表结构，添加新字段"""
    
    print("="*80)
    print("🔧 开始升级Order表结构")
    print("="*80)
    
    # 检查数据库连接
    if not check_connection():
        print("❌ 数据库连接失败，升级中止！")
        return False
    
    # 定义要添加的字段
    new_columns = [
        # 营销活动字段
        ("user_paid_delivery_fee", "FLOAT DEFAULT 0", "用户支付配送费"),
        ("delivery_discount", "FLOAT DEFAULT 0", "配送费减免金额"),
        ("full_reduction", "FLOAT DEFAULT 0", "满减金额"),
        ("product_discount", "FLOAT DEFAULT 0", "商品减免金额"),
        ("merchant_voucher", "FLOAT DEFAULT 0", "商家代金券"),
        ("merchant_share", "FLOAT DEFAULT 0", "商家承担部分券"),
        ("packaging_fee", "FLOAT DEFAULT 0", "打包袋金额"),
        
        # 配送和地理信息
        ("delivery_distance", "FLOAT DEFAULT 0", "配送距离(km)"),
        ("city", "VARCHAR(50)", "城市名称"),
        
        # 门店信息
        ("store_id", "VARCHAR(50)", "门店ID"),
    ]
    
    try:
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 检查每个字段是否存在，不存在则添加
                for col_name, col_type, col_comment in new_columns:
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
                        print(f"  ⏭️  字段 '{col_name}' 已存在，跳过")
                    else:
                        # 添加字段
                        alter_sql = text(f"""
                            ALTER TABLE orders 
                            ADD COLUMN {col_name} {col_type}
                        """)
                        conn.execute(alter_sql)
                        print(f"  ✅ 添加字段 '{col_name}' ({col_comment})")
                        
                        # 添加注释
                        comment_sql = text(f"""
                            COMMENT ON COLUMN orders.{col_name} IS '{col_comment}'
                        """)
                        conn.execute(comment_sql)
                
                # 添加索引
                indexes = [
                    ("idx_city", "city", "城市索引"),
                    ("idx_store_id", "store_id", "门店ID索引"),
                ]
                
                print("\n📊 添加索引...")
                for idx_name, idx_column, idx_comment in indexes:
                    # 检查索引是否存在
                    check_idx_sql = text("""
                        SELECT indexname 
                        FROM pg_indexes 
                        WHERE tablename = 'orders' 
                        AND indexname = :idx_name
                    """)
                    result = conn.execute(check_idx_sql, {"idx_name": idx_name})
                    exists = result.fetchone() is not None
                    
                    if exists:
                        print(f"  ⏭️  索引 '{idx_name}' 已存在，跳过")
                    else:
                        create_idx_sql = text(f"""
                            CREATE INDEX {idx_name} ON orders ({idx_column})
                        """)
                        conn.execute(create_idx_sql)
                        print(f"  ✅ 创建索引 '{idx_name}' ({idx_comment})")
                
                # 提交事务
                trans.commit()
                
                print("\n" + "="*80)
                print("✅ Order表结构升级成功！")
                print("="*80)
                
                # 显示升级后的字段统计
                count_sql = text("""
                    SELECT COUNT(*) as total_columns
                    FROM information_schema.columns 
                    WHERE table_name = 'orders'
                """)
                result = conn.execute(count_sql)
                total_cols = result.fetchone()[0]
                
                print(f"\n📊 升级后Order表总字段数: {total_cols}")
                print(f"   新增字段: {len([c for c in new_columns])}")
                print(f"   新增索引: {len(indexes)}")
                
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"\n❌ 升级失败，已回滚: {e}")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"\n❌ 数据库连接错误: {e}")
        return False


def verify_upgrade():
    """验证升级结果"""
    print("\n" + "="*80)
    print("🔍 验证升级结果")
    print("="*80)
    
    try:
        with engine.connect() as conn:
            # 查询所有字段
            sql = text("""
                SELECT column_name, data_type, column_default, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'orders'
                ORDER BY ordinal_position
            """)
            result = conn.execute(sql)
            columns = result.fetchall()
            
            print(f"\n✅ Order表当前字段列表（共{len(columns)}个）:")
            print("-" * 80)
            for i, (col_name, data_type, default, nullable) in enumerate(columns, 1):
                default_str = str(default)[:30] if default else 'NULL'
                print(f"{i:3d}. {col_name:30s} | {data_type:15s} | 默认值: {default_str}")
            
            # 统计新字段
            new_fields = [
                'user_paid_delivery_fee', 'delivery_discount', 'full_reduction',
                'product_discount', 'merchant_voucher', 'merchant_share',
                'packaging_fee', 'delivery_distance', 'city', 'store_id'
            ]
            
            existing_new_fields = [col[0] for col in columns if col[0] in new_fields]
            
            print(f"\n📊 新增字段验证: {len(existing_new_fields)}/{len(new_fields)} 个已添加")
            for field in new_fields:
                status = "✅" if field in existing_new_fields else "❌"
                print(f"  {status} {field}")
            
            return len(existing_new_fields) == len(new_fields)
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 Order表结构升级工具")
    print("="*80)
    print("目标: 添加营销活动、配送距离、城市、门店ID等10个字段")
    print("影响: 支持Excel数据的完整33个字段映射")
    print("="*80)
    
    confirm = input("\n⚠️  是否继续升级Order表结构？(yes/no): ")
    
    if confirm.lower() == 'yes':
        success = upgrade_order_table()
        
        if success:
            verify_upgrade()
            print("\n✅ 升级完成！现在可以重新导入Excel数据以映射所有字段。")
        else:
            print("\n❌ 升级失败！请检查错误信息。")
            sys.exit(1)
    else:
        print("\n❌ 升级已取消")
        sys.exit(0)
