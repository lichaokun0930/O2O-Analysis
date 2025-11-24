#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL 数据库导出工具
导出表结构和数据，用于数据库迁移和交接

功能：
1. 导出完整的数据库dump文件（表结构+数据）
2. 单独导出表结构（schema only）
3. 单独导出数据（data only）
4. 支持指定表导出

使用方法：
    # 导出完整数据库（表结构+数据）
    python 导出数据库.py
    
    # 只导出表结构
    python 导出数据库.py --schema-only
    
    # 只导出数据
    python 导出数据库.py --data-only
    
    # 导出指定表
    python 导出数据库.py --table orders --table products

生成文件：
    - o2o_dashboard_full_YYYYMMDD_HHMMSS.sql (完整备份)
    - o2o_dashboard_schema_YYYYMMDD_HHMMSS.sql (仅表结构)
    - o2o_dashboard_data_YYYYMMDD_HHMMSS.sql (仅数据)
"""

import os
import sys
import subprocess
from datetime import datetime
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


def check_pg_dump():
    """检查pg_dump是否可用"""
    try:
        result = subprocess.run(['pg_dump', '--version'], 
                              capture_output=True, 
                              text=True,
                              check=True)
        print(f"✅ 检测到 PostgreSQL 工具: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ 未找到 pg_dump 工具")
        print("📋 请安装 PostgreSQL 客户端工具：")
        print("   Windows: https://www.postgresql.org/download/windows/")
        print("   下载安装后，将 PostgreSQL 的 bin 目录添加到系统 PATH")
        print("   例如: C:\\Program Files\\PostgreSQL\\15\\bin")
        return False


def get_output_filename(export_type='full'):
    """生成输出文件名"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 创建导出目录
    export_dir = Path(__file__).parent / '数据库导出'
    export_dir.mkdir(exist_ok=True)
    
    filename_map = {
        'full': f'o2o_dashboard_full_{timestamp}.sql',
        'schema': f'o2o_dashboard_schema_{timestamp}.sql',
        'data': f'o2o_dashboard_data_{timestamp}.sql',
    }
    
    return export_dir / filename_map.get(export_type, f'o2o_dashboard_{timestamp}.sql')


def export_database(export_type='full', tables=None):
    """
    导出数据库
    
    Args:
        export_type: 导出类型 ('full', 'schema', 'data')
        tables: 要导出的表列表（None表示导出所有表）
    """
    if not check_pg_dump():
        return False
    
    output_file = get_output_filename(export_type)
    
    # 设置环境变量（用于密码认证）
    env = os.environ.copy()
    env['PGPASSWORD'] = DB_PASSWORD
    
    # 构建pg_dump命令
    cmd = [
        'pg_dump',
        '-h', DB_HOST,
        '-p', str(DB_PORT),
        '-U', DB_USER,
        '-d', DB_NAME,
        '--no-owner',  # 不包含所有者信息
        '--no-privileges',  # 不包含权限设置
        '-F', 'p',  # 纯文本格式
        '-f', str(output_file),
    ]
    
    # 添加导出类型参数
    if export_type == 'schema':
        cmd.append('--schema-only')
    elif export_type == 'data':
        cmd.append('--data-only')
    
    # 添加表过滤
    if tables:
        for table in tables:
            cmd.extend(['-t', table])
    
    print(f"\n{'='*70}")
    print(f"📤 开始导出数据库...")
    print(f"{'='*70}")
    print(f"数据库: {DB_NAME}")
    print(f"主机: {DB_HOST}:{DB_PORT}")
    print(f"用户: {DB_USER}")
    print(f"导出类型: {export_type}")
    if tables:
        print(f"导出表: {', '.join(tables)}")
    else:
        print(f"导出表: 全部")
    print(f"输出文件: {output_file}")
    print(f"{'='*70}\n")
    
    try:
        # 执行pg_dump
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        # 检查文件大小
        file_size = output_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"✅ 导出成功!")
        print(f"📁 文件: {output_file}")
        print(f"📊 大小: {file_size_mb:.2f} MB ({file_size:,} bytes)")
        
        # 显示SQL文件的前几行预览
        print(f"\n{'='*70}")
        print("📄 文件预览（前20行）:")
        print(f"{'='*70}")
        with open(output_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 20:
                    print("... (更多内容省略)")
                    break
                print(line.rstrip())
        print(f"{'='*70}\n")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 导出失败!")
        print(f"错误信息: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False


def export_all_formats():
    """导出所有格式（完整、仅结构、仅数据）"""
    print("\n" + "="*70)
    print("🎯 导出所有格式（完整、仅结构、仅数据）")
    print("="*70 + "\n")
    
    results = {}
    
    # 1. 导出完整备份
    print("📦 1/3 导出完整备份（表结构+数据）...")
    results['full'] = export_database('full')
    
    # 2. 导出表结构
    print("\n📋 2/3 导出表结构...")
    results['schema'] = export_database('schema')
    
    # 3. 导出数据
    print("\n💾 3/3 导出数据...")
    results['data'] = export_database('data')
    
    # 总结
    print("\n" + "="*70)
    print("📊 导出结果汇总")
    print("="*70)
    success_count = sum(results.values())
    total_count = len(results)
    
    for export_type, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        type_name = {'full': '完整备份', 'schema': '表结构', 'data': '数据'}[export_type]
        print(f"{type_name}: {status}")
    
    print(f"\n总计: {success_count}/{total_count} 个导出任务成功")
    print("="*70 + "\n")
    
    return success_count == total_count


def get_database_info():
    """获取数据库信息"""
    try:
        from database.connection import SessionLocal
        from database.models import Order, Product
        
        session = SessionLocal()
        
        # 获取表数据量
        order_count = session.query(Order).count()
        product_count = session.query(Product).count()
        
        # 获取门店列表
        stores = session.query(Order.store_name).distinct().all()
        store_names = [s[0] for s in stores if s[0]]
        
        # 获取日期范围
        from sqlalchemy import func
        date_range = session.query(
            func.min(Order.date).label('min_date'),
            func.max(Order.date).label('max_date')
        ).first()
        
        session.close()
        
        print("\n" + "="*70)
        print("📊 数据库信息")
        print("="*70)
        print(f"数据库名称: {DB_NAME}")
        print(f"主机: {DB_HOST}:{DB_PORT}")
        print(f"\n表统计:")
        print(f"  Orders 表: {order_count:,} 条记录")
        print(f"  Products 表: {product_count:,} 条记录")
        print(f"\n门店数量: {len(store_names)} 个")
        if store_names:
            print(f"门店列表:")
            for store in store_names[:10]:  # 最多显示10个
                print(f"  - {store}")
            if len(store_names) > 10:
                print(f"  ... 还有 {len(store_names) - 10} 个门店")
        
        if date_range.min_date and date_range.max_date:
            print(f"\n数据时间范围:")
            print(f"  最早: {date_range.min_date}")
            print(f"  最晚: {date_range.max_date}")
        
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"⚠️ 无法获取数据库详细信息: {e}")
        print("（这不影响数据导出）\n")


def create_import_guide():
    """创建导入指南文件"""
    guide_file = Path(__file__).parent / '数据库导出' / '导入指南.txt'
    
    guide_content = f"""
================================================================================
PostgreSQL 数据库导入指南
================================================================================

一、环境准备
------------
1. 安装 PostgreSQL 数据库（版本 12 或更高）
   - Windows: https://www.postgresql.org/download/windows/
   - Linux: apt-get install postgresql 或 yum install postgresql
   - macOS: brew install postgresql

2. 确保 PostgreSQL 服务正在运行
   - Windows: 打开"服务"，找到 PostgreSQL 服务
   - Linux: sudo systemctl status postgresql
   - macOS: brew services start postgresql


二、创建数据库
--------------
使用 psql 命令行工具或 pgAdmin 图形界面创建数据库：

方法1：使用 psql 命令行
------------------------
psql -U postgres
CREATE DATABASE o2o_dashboard;
\\q

方法2：使用 SQL 语句
-------------------
CREATE DATABASE o2o_dashboard
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'zh_CN.UTF-8'
    LC_CTYPE = 'zh_CN.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;


三、导入数据
------------

📦 方法1：导入完整备份（推荐）
-------------------------------
psql -U postgres -d o2o_dashboard -f o2o_dashboard_full_YYYYMMDD_HHMMSS.sql

这个命令会：
✅ 创建所有表结构
✅ 导入所有数据
✅ 创建索引


📋 方法2：先导入结构，再导入数据
--------------------------------
# 步骤1：导入表结构
psql -U postgres -d o2o_dashboard -f o2o_dashboard_schema_YYYYMMDD_HHMMSS.sql

# 步骤2：导入数据
psql -U postgres -d o2o_dashboard -f o2o_dashboard_data_YYYYMMDD_HHMMSS.sql


四、验证导入
------------
导入完成后，验证数据是否正确：

psql -U postgres -d o2o_dashboard

-- 查看所有表
\\dt

-- 查看 orders 表结构
\\d orders

-- 查看 orders 表数据量
SELECT COUNT(*) FROM orders;

-- 查看 products 表数据量
SELECT COUNT(*) FROM products;

-- 查看门店列表
SELECT DISTINCT store_name FROM orders;

-- 退出
\\q


五、配置应用连接
----------------
修改应用的 .env 文件或 database/config.py 文件：

DB_HOST=localhost
DB_PORT=5432
DB_NAME=o2o_dashboard
DB_USER=postgres
DB_PASSWORD=你的密码


六、常见问题
------------

问题1：导入时出现编码错误
解决：确保数据库创建时使用 UTF8 编码
      CREATE DATABASE o2o_dashboard ENCODING 'UTF8';

问题2：导入时出现权限错误
解决：使用超级用户导入，或授予相应权限
      GRANT ALL PRIVILEGES ON DATABASE o2o_dashboard TO your_user;

问题3：导入时间过长
解决：先导入结构，创建索引前导入数据，最后创建索引

问题4：表已存在错误
解决：删除现有数据库重新创建
      DROP DATABASE IF EXISTS o2o_dashboard;
      CREATE DATABASE o2o_dashboard;


七、数据库配置建议
------------------

1. 性能优化（修改 postgresql.conf）：
   shared_buffers = 256MB
   effective_cache_size = 1GB
   work_mem = 16MB
   maintenance_work_mem = 128MB

2. 连接数配置：
   max_connections = 100

3. 日志配置：
   logging_collector = on
   log_directory = 'pg_log'
   log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'


八、备份建议
------------

1. 定期备份（每天）：
   pg_dump -h localhost -U postgres -d o2o_dashboard -F c -f backup_$(date +%Y%m%d).dump

2. 自动备份脚本（Linux/macOS）：
   #!/bin/bash
   BACKUP_DIR="/path/to/backup"
   DATE=$(date +%Y%m%d_%H%M%S)
   pg_dump -h localhost -U postgres -d o2o_dashboard -F c -f ${{BACKUP_DIR}}/backup_${{DATE}}.dump
   
   # 保留最近7天的备份
   find ${{BACKUP_DIR}} -name "backup_*.dump" -mtime +7 -delete

3. Windows 计划任务：
   创建 .bat 文件，使用 Windows 任务计划程序定时执行


九、联系方式
------------
如有问题，请联系：
- 数据库管理员：[填写联系方式]
- 技术支持：[填写联系方式]


================================================================================
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
数据库版本: PostgreSQL 12+
导出工具: pg_dump
================================================================================
"""
    
    try:
        guide_file.parent.mkdir(exist_ok=True)
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        print(f"✅ 已生成导入指南: {guide_file}\n")
    except Exception as e:
        print(f"⚠️ 生成导入指南失败: {e}\n")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='PostgreSQL 数据库导出工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 导出完整数据库
  python 导出数据库.py
  
  # 导出所有格式（完整、仅结构、仅数据）
  python 导出数据库.py --all
  
  # 只导出表结构
  python 导出数据库.py --schema-only
  
  # 只导出数据
  python 导出数据库.py --data-only
  
  # 导出指定表
  python 导出数据库.py --table orders --table products
  
  # 查看数据库信息
  python 导出数据库.py --info
        """
    )
    
    parser.add_argument('--all', action='store_true',
                       help='导出所有格式（完整、仅结构、仅数据）')
    parser.add_argument('--schema-only', action='store_true',
                       help='只导出表结构')
    parser.add_argument('--data-only', action='store_true',
                       help='只导出数据')
    parser.add_argument('--table', '-t', action='append',
                       help='指定要导出的表（可多次使用）')
    parser.add_argument('--info', action='store_true',
                       help='只显示数据库信息，不导出')
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║           🗄️  PostgreSQL 数据库导出工具                         ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # 显示数据库信息
    get_database_info()
    
    # 如果只是查看信息，退出
    if args.info:
        return
    
    # 生成导入指南
    create_import_guide()
    
    # 根据参数决定导出方式
    if args.all:
        # 导出所有格式
        success = export_all_formats()
    elif args.schema_only:
        # 只导出表结构
        success = export_database('schema', args.table)
    elif args.data_only:
        # 只导出数据
        success = export_database('data', args.table)
    else:
        # 默认：导出完整备份
        success = export_database('full', args.table)
    
    if success:
        print("""
╔══════════════════════════════════════════════════════════════════╗
║  ✅ 导出完成！                                                    ║
║                                                                  ║
║  📁 导出文件位置: 数据库导出/                                      ║
║  📋 导入指南: 数据库导出/导入指南.txt                              ║
║                                                                  ║
║  💡 提示:                                                         ║
║  1. 将 .sql 文件发送给同事                                        ║
║  2. 同时发送"导入指南.txt"                                        ║
║  3. 按照指南中的步骤导入数据库                                     ║
╚══════════════════════════════════════════════════════════════════╝
        """)
    else:
        print("""
╔══════════════════════════════════════════════════════════════════╗
║  ❌ 导出失败！                                                    ║
║                                                                  ║
║  请检查:                                                          ║
║  1. PostgreSQL 工具是否已安装                                     ║
║  2. 数据库连接配置是否正确                                         ║
║  3. 数据库服务是否正在运行                                         ║
╚══════════════════════════════════════════════════════════════════╝
        """)
        sys.exit(1)


if __name__ == '__main__':
    main()
