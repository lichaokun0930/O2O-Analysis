"""
数据库连接配置
管理数据库连接、会话和基础操作
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os
from dotenv import load_dotenv
from typing import Generator

# 加载环境变量
load_dotenv()

# 数据库URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/o2o_dashboard"
)

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,              # 连接池大小
    max_overflow=10,          # 最大溢出连接数
    pool_timeout=30,          # 连接超时
    pool_recycle=3600,        # 连接回收时间（秒）
    echo=False,               # 不打印SQL（生产环境关闭）
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    用于FastAPI依赖注入
    
    使用示例：
    @app.get("/api/products")
    def get_products(db: Session = Depends(get_db)):
        products = db.query(Product).all()
        return products
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    数据库上下文管理器
    用于普通Python代码
    
    使用示例：
    with get_db_context() as db:
        products = db.query(Product).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_database():
    """
    初始化数据库
    创建所有表
    """
    from database.models import Base
    
    print("[Creating database tables...]")
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created!")


def drop_all_tables():
    """
    删除所有表（危险操作！）
    仅用于开发环境重置数据库
    """
    from database.models import Base
    
    confirm = input("⚠️ 确认要删除所有数据表吗？(yes/no): ")
    if confirm.lower() == 'yes':
        print("🗑️ 正在删除所有表...")
        Base.metadata.drop_all(bind=engine)
        print("✅ 所有表已删除！")
    else:
        print("❌ 操作已取消")


def check_connection():
    """
    检查数据库连接是否正常
    """
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("[OK] Database connection successful!")
            return True
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # 测试数据库连接
    check_connection()
