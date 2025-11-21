"""为orders表补齐 platform_service_fee 字段的工具脚本。"""
from pathlib import Path
import sys

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import engine, check_connection


def ensure_platform_service_fee_column() -> bool:
    """检查 orders 表是否存在 platform_service_fee 字段，缺失则自动添加。"""
    print("=" * 80)
    print("🔧 检查并补齐 orders.platform_service_fee 字段")
    print("=" * 80)

    if not check_connection():
        print("❌ 数据库连接失败，无法检查表结构。")
        return False

    try:
        with engine.connect() as conn:
            check_sql = text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'orders'
                  AND column_name = 'platform_service_fee'
                LIMIT 1
                """
            )
            exists = conn.execute(check_sql).fetchone() is not None
            if exists:
                print("✅ 字段已存在，无需修改。")
                return True

            print("⚠️  检测到缺失字段，正在添加 platform_service_fee ...")
            alter_sql = text(
                """
                ALTER TABLE orders
                ADD COLUMN platform_service_fee DOUBLE PRECISION DEFAULT 0
                """
            )
            conn.execute(alter_sql)

            comment_sql = text(
                """
                COMMENT ON COLUMN orders.platform_service_fee IS '平台服务费'
                """
            )
            conn.execute(comment_sql)
            
            # ⚠️ 必须提交事务，否则DDL不生效
            conn.commit()

            print("✅ 已成功补齐 platform_service_fee 字段，默认值 0。")
            return True
    except Exception as exc:  # pragma: no cover - 命令行工具
        print(f"❌ 操作失败: {exc}")
        return False


if __name__ == "__main__":
    ensure_platform_service_fee_column()
