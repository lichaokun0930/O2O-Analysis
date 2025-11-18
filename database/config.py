"""
数据库配置文件
集中管理数据库连接参数和系统配置

📋 快速开始:
1. 复制 .env.example 为 .env
2. 修改 .env 中的 DATABASE_URL (改成你的数据库密码)
3. 导入使用: from database.config import DATABASE_URL, POOL_CONFIG

💡 使用示例:
    from database.config import DATABASE_CONFIG, POOL_CONFIG
    
    # 获取数据库URL
    from database.config import get_database_url
    url = get_database_url()
    
    # 查看当前配置
    from database.config import print_config
    print_config()

🔧 配置说明:
- 所有配置都可以通过 .env 文件设置
- 如果 .env 中没有设置,会使用下面的默认值
- 生产环境务必修改数据库密码和 SECRET_KEY
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== 数据库连接配置 ====================

# 数据库主机地址
DB_HOST = os.getenv('DB_HOST', 'localhost')

# 数据库端口
DB_PORT = int(os.getenv('DB_PORT', 5432))

# 数据库名称
DB_NAME = os.getenv('DB_NAME', 'o2o_dashboard')

# 数据库用户名
DB_USER = os.getenv('DB_USER', 'postgres')

# 数据库密码
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

# 数据库驱动
DB_DRIVER = os.getenv('DB_DRIVER', 'pg8000')  # 使用pg8000避免UTF-8编码问题

# 完整数据库URL
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)

# 带驱动的数据库URL（用于SQLAlchemy）
DATABASE_URL_WITH_DRIVER = DATABASE_URL.replace('postgresql://', f'postgresql+{DB_DRIVER}://')


# ==================== 连接池配置 ====================

# 连接池大小（同时保持的连接数）
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', 5))

# 最大溢出连接数（超过pool_size后允许的额外连接）
MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', 10))

# 连接超时时间（秒）
POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', 30))

# 连接回收时间（秒，防止连接过期）
POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', 3600))

# 是否在控制台打印SQL语句（开发环境可设为True）
ECHO_SQL = os.getenv('DB_ECHO_SQL', 'false').lower() == 'true'


# ==================== 查询优化配置 ====================

# 批量插入大小
BATCH_SIZE = int(os.getenv('DB_BATCH_SIZE', 1000))

# 查询超时时间（秒）
QUERY_TIMEOUT = int(os.getenv('DB_QUERY_TIMEOUT', 60))

# 是否启用查询缓存
ENABLE_QUERY_CACHE = os.getenv('ENABLE_QUERY_CACHE', 'true').lower() == 'true'


# ==================== 数据生命周期配置 ====================

# 数据保留天数（超过此天数的数据会被归档或清理）
DATA_RETENTION_DAYS = int(os.getenv('DATA_RETENTION_DAYS', 365))

# 是否启用自动归档
ENABLE_AUTO_ARCHIVE = os.getenv('ENABLE_AUTO_ARCHIVE', 'true').lower() == 'true'

# 归档检查频率（天）
ARCHIVE_CHECK_INTERVAL_DAYS = int(os.getenv('ARCHIVE_CHECK_INTERVAL_DAYS', 7))


# ==================== 配置字典（供其他模块导入使用） ====================

DATABASE_CONFIG = {
    'host': DB_HOST,
    'port': DB_PORT,
    'database': DB_NAME,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'driver': DB_DRIVER,
}

POOL_CONFIG = {
    'pool_size': POOL_SIZE,
    'max_overflow': MAX_OVERFLOW,
    'pool_timeout': POOL_TIMEOUT,
    'pool_recycle': POOL_RECYCLE,
    'echo': ECHO_SQL,
}

PERFORMANCE_CONFIG = {
    'batch_size': BATCH_SIZE,
    'query_timeout': QUERY_TIMEOUT,
    'enable_cache': ENABLE_QUERY_CACHE,
}

LIFECYCLE_CONFIG = {
    'retention_days': DATA_RETENTION_DAYS,
    'enable_auto_archive': ENABLE_AUTO_ARCHIVE,
    'archive_interval_days': ARCHIVE_CHECK_INTERVAL_DAYS,
}


# ==================== 辅助函数 ====================

def get_database_url(with_driver: bool = True) -> str:
    """
    获取数据库连接URL
    
    Args:
        with_driver: 是否包含驱动名称（默认True，用于SQLAlchemy）
    
    Returns:
        数据库连接URL字符串
    """
    return DATABASE_URL_WITH_DRIVER if with_driver else DATABASE_URL


def print_config():
    """
    打印当前数据库配置（隐藏密码）
    用于调试和验证配置
    """
    print("=" * 60)
    print("数据库配置信息")
    print("=" * 60)
    print(f"主机地址: {DB_HOST}")
    print(f"端口: {DB_PORT}")
    print(f"数据库名: {DB_NAME}")
    print(f"用户名: {DB_USER}")
    print(f"密码: {'*' * len(DB_PASSWORD)}")
    print(f"驱动: {DB_DRIVER}")
    print(f"\n连接池配置:")
    print(f"  连接池大小: {POOL_SIZE}")
    print(f"  最大溢出: {MAX_OVERFLOW}")
    print(f"  连接超时: {POOL_TIMEOUT}秒")
    print(f"  连接回收: {POOL_RECYCLE}秒")
    print(f"  打印SQL: {ECHO_SQL}")
    print(f"\n性能配置:")
    print(f"  批量大小: {BATCH_SIZE}")
    print(f"  查询超时: {QUERY_TIMEOUT}秒")
    print(f"  查询缓存: {ENABLE_QUERY_CACHE}")
    print(f"\n数据生命周期:")
    print(f"  保留天数: {DATA_RETENTION_DAYS}天")
    print(f"  自动归档: {ENABLE_AUTO_ARCHIVE}")
    print(f"  归档间隔: {ARCHIVE_CHECK_INTERVAL_DAYS}天")
    print("=" * 60)


if __name__ == '__main__':
    # 运行此文件可查看当前配置
    print_config()
