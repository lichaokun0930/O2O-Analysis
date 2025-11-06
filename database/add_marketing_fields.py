"""
添加营销活动字段到Order表
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import engine
from sqlalchemy import text


def add_marketing_fields():
    """添加营销活动相关字段到orders表"""
    
    fields = [
        "user_paid_delivery_fee FLOAT DEFAULT 0",
        "delivery_discount FLOAT DEFAULT 0",
        "full_reduction FLOAT DEFAULT 0",
        "product_discount FLOAT DEFAULT 0",
        "merchant_voucher FLOAT DEFAULT 0",
        "merchant_share FLOAT DEFAULT 0",
        "packaging_fee FLOAT DEFAULT 0",
    ]
    
    comments = {
        'user_paid_delivery_fee': '用户支付配送费',
        'delivery_discount': '配送费减免金额',
        'full_reduction': '满减金额',
        'product_discount': '商品减免金额',
        'merchant_voucher': '商家代金券',
        'merchant_share': '商家承担部分券',
        'packaging_fee': '打包袋金额',
    }
    
    with engine.connect() as conn:
        for field_def in fields:
            field_name = field_def.split()[0]
            
            # 检查字段是否已存在
            check_sql = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='orders' AND column_name=:field_name
            """)
            
            result = conn.execute(check_sql, {"field_name": field_name})
            exists = result.fetchone() is not None
            
            if exists:
                print(f"✅ 字段 {field_name} 已存在,跳过")
                continue
            
            # 添加字段
            try:
                alter_sql = text(f"ALTER TABLE orders ADD COLUMN {field_def}")
                conn.execute(alter_sql)
                conn.commit()
                print(f"✅ 成功添加字段: {field_name}")
                
                # 添加注释
                comment_sql = text(f"""
                    COMMENT ON COLUMN orders.{field_name} IS '{comments[field_name]}'
                """)
                conn.execute(comment_sql)
                conn.commit()
                print(f"   注释: {comments[field_name]}")
                
            except Exception as e:
                print(f"❌ 添加字段 {field_name} 失败: {e}")
                conn.rollback()
    
    print("\n✅ 营销活动字段迁移完成!")


if __name__ == "__main__":
    print("开始添加营销活动字段...\n")
    add_marketing_fields()
