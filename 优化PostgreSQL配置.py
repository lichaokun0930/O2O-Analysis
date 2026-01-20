"""
PostgreSQL 高并发配置优化脚本

针对 300-500 并发用户优化 PostgreSQL 配置
运行此脚本后需要重启 PostgreSQL 服务
"""

import subprocess
import sys

def get_pg_config_path():
    """获取 PostgreSQL 配置文件路径"""
    # Windows 常见路径
    possible_paths = [
        r"C:\Program Files\PostgreSQL\16\data\postgresql.conf",
        r"C:\Program Files\PostgreSQL\15\data\postgresql.conf",
        r"C:\Program Files\PostgreSQL\14\data\postgresql.conf",
        r"C:\Program Files\PostgreSQL\13\data\postgresql.conf",
    ]
    
    import os
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def check_current_settings():
    """检查当前 PostgreSQL 设置"""
    try:
        from database.connection import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # 获取关键配置
            settings = {}
            for param in ['max_connections', 'shared_buffers', 'work_mem', 
                         'maintenance_work_mem', 'effective_cache_size']:
                result = conn.execute(text(f"SHOW {param}")).scalar()
                settings[param] = result
            
            # 获取当前连接数
            current_conn = conn.execute(text(
                "SELECT count(*) FROM pg_stat_activity"
            )).scalar()
            settings['current_connections'] = current_conn
            
            return settings
    except Exception as e:
        print(f"❌ 无法连接数据库: {e}")
        return None


def print_recommendations():
    """打印优化建议"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║           PostgreSQL 高并发优化配置建议                           ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  针对你的配置（16核 62GB 内存，300-500并发）推荐：                 ║
║                                                                  ║
║  1. max_connections = 200        # 最大连接数（默认100太小）      ║
║  2. shared_buffers = 4GB         # 共享缓冲区（内存的6-8%）       ║
║  3. work_mem = 64MB              # 每个查询的工作内存             ║
║  4. maintenance_work_mem = 512MB # 维护操作内存                   ║
║  5. effective_cache_size = 48GB  # 预估可用缓存（内存的75%）      ║
║  6. random_page_cost = 1.1       # SSD优化                       ║
║  7. checkpoint_completion_target = 0.9                           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")


def generate_config_snippet():
    """生成配置片段"""
    config = """
# ============================================
# 高并发优化配置（300-500用户）
# 添加到 postgresql.conf 文件末尾
# ============================================

# 连接设置
max_connections = 200
superuser_reserved_connections = 3

# 内存设置（基于62GB内存）
shared_buffers = 4GB
work_mem = 64MB
maintenance_work_mem = 512MB
effective_cache_size = 48GB

# 磁盘设置（SSD优化）
random_page_cost = 1.1
effective_io_concurrency = 200

# WAL设置
wal_buffers = 64MB
checkpoint_completion_target = 0.9
max_wal_size = 2GB
min_wal_size = 1GB

# 查询优化
default_statistics_target = 100
"""
    return config


def main():
    print("=" * 60)
    print("  PostgreSQL 高并发配置检查与优化")
    print("=" * 60)
    print()
    
    # 检查当前设置
    print("📊 当前 PostgreSQL 配置：")
    print("-" * 40)
    
    settings = check_current_settings()
    if settings:
        for key, value in settings.items():
            status = "⚠️" if key == 'max_connections' and int(value) < 150 else "✅"
            print(f"  {status} {key}: {value}")
    
    print()
    print_recommendations()
    
    # 生成配置
    print("📝 推荐配置（复制到 postgresql.conf）：")
    print("-" * 40)
    print(generate_config_snippet())
    
    # 查找配置文件
    config_path = get_pg_config_path()
    if config_path:
        print(f"\n📁 配置文件位置: {config_path}")
    else:
        print("\n⚠️ 未找到 postgresql.conf，请手动查找")
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  操作步骤：                                                       ║
║  1. 用管理员权限打开 postgresql.conf                              ║
║  2. 将上面的配置添加到文件末尾                                     ║
║  3. 保存文件                                                      ║
║  4. 重启 PostgreSQL 服务：                                        ║
║     - 打开"服务"(services.msc)                                   ║
║     - 找到 postgresql-x64-16（或你的版本）                        ║
║     - 右键 → 重新启动                                             ║
╚══════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
