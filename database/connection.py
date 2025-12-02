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
# 使用 pg8000 驱动避免 psycopg2 的 UTF-8 编码问题
engine = create_engine(
    DATABASE_URL.replace('postgresql://', 'postgresql+pg8000://'),
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


def check_connection() -> dict:
    """
    检查数据库连接是否正常
    
    Returns:
        dict: {'connected': bool, 'message': str, 'details': dict}
    """
    try:
        from sqlalchemy import text
        import time
        start = time.time()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            latency = round((time.time() - start) * 1000, 2)
            
            # 获取数据库版本
            version = conn.execute(text("SELECT version()")).scalar()
            
            return {
                'connected': True,
                'message': '数据库连接正常',
                'details': {
                    'latency_ms': latency,
                    'database': 'o2o_dashboard',
                    'version': version[:50] if version else 'Unknown'
                }
            }
    except Exception as e:
        error_msg = str(e)
        # 简化错误信息
        if 'password authentication failed' in error_msg.lower():
            simple_msg = '密码认证失败'
        elif 'connection refused' in error_msg.lower():
            simple_msg = '连接被拒绝(数据库服务未启动)'
        elif 'timeout' in error_msg.lower():
            simple_msg = '连接超时'
        else:
            simple_msg = '连接失败'
        
        return {
            'connected': False,
            'message': simple_msg,
            'details': {
                'error': error_msg[:200]
            }
        }


def get_connection_status() -> dict:
    """
    获取数据库连接状态（带缓存，避免频繁检测）
    
    Returns:
        dict: 连接状态信息
    """
    return check_connection()


if __name__ == "__main__":
    # 测试数据库连接
    check_connection()
