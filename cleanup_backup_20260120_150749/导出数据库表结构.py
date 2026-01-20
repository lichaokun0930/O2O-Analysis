"""
智能数据库表结构导出工具 V1.0

功能:
1. 从PostgreSQL数据库读取完整表结构
2. 生成多种格式的建表语句(PostgreSQL/MySQL/SQLite/SQL Server)
3. 导出数据字典(Excel格式)
4. 生成Markdown文档
5. 包含示例数据和部署指南

作者: AI Assistant
日期: 2025-12-09
"""

import os
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

# 检查依赖
try:
    from sqlalchemy import create_engine, inspect, text, MetaData
    from sqlalchemy.schema import CreateTable
    import openpyxl
    # 检查psycopg2
    try:
        import psycopg2
        DRIVER = 'psycopg2'
    except ImportError:
        try:
            import pg8000
            DRIVER = 'pg8000'
        except ImportError:
            print("❌ 缺少PostgreSQL驱动!")
            print("请运行以下命令之一:")
            print("  pip install psycopg2-binary")
            print("  或")
            print("  pip install pg8000")
            sys.exit(1)
except ImportError as e:
    print(f"❌ 缺少依赖: {e}")
    print("请运行: pip install sqlalchemy openpyxl")
    sys.exit(1)

# 数据库连接配置
# 💡 提示: 这些配置应该与.env文件中的DATABASE_URL保持一致
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'o2o_dashboard',
    'user': 'postgres',
    'password': '308352588'  # ✅ 与.env中的实际密码一致
}

# 导出配置
OUTPUT_DIR = Path("数据库表结构导出")
TABLES_TO_EXPORT = ['orders', 'products', 'stores']  # 可以指定要导出的表,或留空导出全部


class DatabaseSchemaExporter:
    """数据库表结构导出器"""
    
    def __init__(self, db_config):
        """初始化"""
        self.config = db_config
        self.engine = None
        self.inspector = None
        self.metadata = MetaData()
        
    def connect(self):
        """连接数据库"""
        import warnings
        warnings.filterwarnings('ignore')
        
        try:
            # 根据可用驱动构建连接字符串
            if DRIVER == 'psycopg2':
                conn_str = f"postgresql+psycopg2://{self.config['user']}:{self.config['password']}@{self.config['host']}:{self.config['port']}/{self.config['database']}?client_encoding=utf8"
                connect_args = {'options': '-c client_encoding=UTF8'}
            else:  # pg8000
                # pg8000在Windows上需要特殊处理
                import pg8000.native
                # 直接使用pg8000原生连接测试
                try:
                    conn = pg8000.native.Connection(
                        user=self.config['user'],
                        password=self.config['password'],
                        host=self.config['host'],
                        port=self.config['port'],
                        database=self.config['database']
                    )
                    conn.close()
                except Exception as e:
                    # 捕获并忽略编码错误
                    if 'utf-8' not in str(e).lower():
                        raise
                
                conn_str = f"postgresql+pg8000://{self.config['user']}:{self.config['password']}@{self.config['host']}:{self.config['port']}/{self.config['database']}"
                connect_args = {}
            
            self.engine = create_engine(
                conn_str,
                connect_args=connect_args,
                pool_pre_ping=True,
                echo=False  # 关闭SQL日志避免编码问题
            )
            self.inspector = inspect(self.engine)
            
            # 测试连接
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.scalar()
                print(f"✅ 数据库连接成功 (驱动: {DRIVER})")
            
            return True
        except Exception as e:
            # 处理各种错误
            error_msg = str(e)
            
            # 如果是UTF-8解码错误,尝试用GBK解码
            if 'utf-8' in error_msg.lower() and 'decode' in error_msg.lower():
                try:
                    if hasattr(e, 'args') and e.args:
                        for arg in e.args:
                            if isinstance(arg, bytes):
                                error_msg = arg.decode('gbk', errors='replace')
                                break
                except:
                    error_msg = "编码错误 (可能PostgreSQL未启动或配置错误)"
            
            print(f"❌ 数据库连接失败: {error_msg}")
            print(f"   错误类型: {type(e).__name__}")
            
            # 提供更详细的诊断
            if 'Connection refused' in error_msg or 'could not connect' in error_msg.lower():
                print("   💡 PostgreSQL服务可能未启动")
            elif 'authentication' in error_msg.lower() or 'password' in error_msg.lower():
                print("   💡 用户名或密码可能不正确")
            elif 'database' in error_msg.lower() and 'does not exist' in error_msg.lower():
                print("   💡 数据库不存在")
            
            return False
    
    def get_all_tables(self):
        """获取所有表名"""
        return self.inspector.get_table_names()
    
    def get_table_info(self, table_name):
        """获取表的完整信息"""
        info = {
            'name': table_name,
            'columns': [],
            'primary_keys': [],
            'foreign_keys': [],
            'indexes': [],
            'row_count': 0,
            'sample_data': None
        }
        
        try:
            # 获取列信息
            columns = self.inspector.get_columns(table_name)
            for col in columns:
                col_info = {
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col['nullable'],
                    'default': col.get('default'),
                    'comment': col.get('comment', '')
                }
                info['columns'].append(col_info)
            
            # 获取主键
            pk = self.inspector.get_pk_constraint(table_name)
            info['primary_keys'] = pk.get('constrained_columns', [])
            
            # 获取外键
            fks = self.inspector.get_foreign_keys(table_name)
            for fk in fks:
                fk_info = {
                    'columns': fk['constrained_columns'],
                    'ref_table': fk['referred_table'],
                    'ref_columns': fk['referred_columns']
                }
                info['foreign_keys'].append(fk_info)
            
            # 获取索引
            indexes = self.inspector.get_indexes(table_name)
            for idx in indexes:
                idx_info = {
                    'name': idx['name'],
                    'columns': idx['column_names'],
                    'unique': idx['unique']
                }
                info['indexes'].append(idx_info)
            
            # 获取行数
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                info['row_count'] = result.scalar()
                
                # 获取示例数据(前5行)
                result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
                info['sample_data'] = result.fetchall()
            
        except Exception as e:
            print(f"⚠️ 获取表 {table_name} 信息时出错: {e}")
        
        return info
    
    def generate_postgresql_ddl(self, table_info):
        """生成PostgreSQL建表语句"""
        lines = []
        lines.append(f"-- ============================================")
        lines.append(f"-- 表名: {table_info['name']}")
        lines.append(f"-- 行数: {table_info['row_count']:,}")
        lines.append(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"-- ============================================")
        lines.append("")
        lines.append(f"CREATE TABLE IF NOT EXISTS {table_info['name']} (")
        
        # 列定义
        col_lines = []
        for col in table_info['columns']:
            col_def = f"    {col['name']} {col['type']}"
            if not col['nullable']:
                col_def += " NOT NULL"
            if col['default']:
                col_def += f" DEFAULT {col['default']}"
            col_lines.append(col_def)
        
        # 主键
        if table_info['primary_keys']:
            pk_cols = ', '.join(table_info['primary_keys'])
            col_lines.append(f"    PRIMARY KEY ({pk_cols})")
        
        lines.append(',\n'.join(col_lines))
        lines.append(");")
        lines.append("")
        
        # 外键
        for fk in table_info['foreign_keys']:
            fk_cols = ', '.join(fk['columns'])
            ref_cols = ', '.join(fk['ref_columns'])
            lines.append(f"ALTER TABLE {table_info['name']} ADD FOREIGN KEY ({fk_cols}) REFERENCES {fk['ref_table']}({ref_cols});")
        
        # 索引
        for idx in table_info['indexes']:
            if idx['name'].startswith('pk_'):  # 跳过主键索引
                continue
            idx_cols = ', '.join(idx['columns'])
            unique = "UNIQUE " if idx['unique'] else ""
            lines.append(f"CREATE {unique}INDEX {idx['name']} ON {table_info['name']} ({idx_cols});")
        
        # 注释
        if any(col['comment'] for col in table_info['columns']):
            lines.append("")
            lines.append("-- 列注释")
            for col in table_info['columns']:
                if col['comment']:
                    lines.append(f"COMMENT ON COLUMN {table_info['name']}.{col['name']} IS '{col['comment']}';")
        
        return '\n'.join(lines)
    
    def generate_mysql_ddl(self, table_info):
        """生成MySQL建表语句"""
        lines = []
        lines.append(f"-- ============================================")
        lines.append(f"-- 表名: {table_info['name']}")
        lines.append(f"-- 行数: {table_info['row_count']:,}")
        lines.append(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"-- ============================================")
        lines.append("")
        lines.append(f"CREATE TABLE IF NOT EXISTS `{table_info['name']}` (")
        
        # 列定义
        col_lines = []
        for col in table_info['columns']:
            # 类型转换
            mysql_type = self._convert_to_mysql_type(col['type'])
            col_def = f"    `{col['name']}` {mysql_type}"
            if not col['nullable']:
                col_def += " NOT NULL"
            if col['default']:
                col_def += f" DEFAULT {col['default']}"
            if col['comment']:
                col_def += f" COMMENT '{col['comment']}'"
            col_lines.append(col_def)
        
        # 主键
        if table_info['primary_keys']:
            pk_cols = ', '.join([f"`{pk}`" for pk in table_info['primary_keys']])
            col_lines.append(f"    PRIMARY KEY ({pk_cols})")
        
        lines.append(',\n'.join(col_lines))
        lines.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;")
        lines.append("")
        
        # 索引
        for idx in table_info['indexes']:
            if idx['name'].startswith('pk_'):
                continue
            idx_cols = ', '.join([f"`{col}`" for col in idx['columns']])
            unique = "UNIQUE " if idx['unique'] else ""
            lines.append(f"CREATE {unique}INDEX `{idx['name']}` ON `{table_info['name']}` ({idx_cols});")
        
        return '\n'.join(lines)
    
    def generate_sqlite_ddl(self, table_info):
        """生成SQLite建表语句"""
        lines = []
        lines.append(f"-- ============================================")
        lines.append(f"-- 表名: {table_info['name']}")
        lines.append(f"-- 行数: {table_info['row_count']:,}")
        lines.append(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"-- ============================================")
        lines.append("")
        lines.append(f"CREATE TABLE IF NOT EXISTS {table_info['name']} (")
        
        # 列定义
        col_lines = []
        for col in table_info['columns']:
            # 类型转换
            sqlite_type = self._convert_to_sqlite_type(col['type'])
            col_def = f"    {col['name']} {sqlite_type}"
            if not col['nullable']:
                col_def += " NOT NULL"
            if col['default']:
                col_def += f" DEFAULT {col['default']}"
            col_lines.append(col_def)
        
        # 主键
        if table_info['primary_keys']:
            pk_cols = ', '.join(table_info['primary_keys'])
            col_lines.append(f"    PRIMARY KEY ({pk_cols})")
        
        lines.append(',\n'.join(col_lines))
        lines.append(");")
        lines.append("")
        
        # 索引
        for idx in table_info['indexes']:
            if idx['name'].startswith('pk_'):
                continue
            idx_cols = ', '.join(idx['columns'])
            unique = "UNIQUE " if idx['unique'] else ""
            lines.append(f"CREATE {unique}INDEX {idx['name']} ON {table_info['name']} ({idx_cols});")
        
        return '\n'.join(lines)
    
    def _convert_to_mysql_type(self, pg_type):
        """PostgreSQL类型转MySQL类型"""
        type_map = {
            'INTEGER': 'INT',
            'BIGINT': 'BIGINT',
            'VARCHAR': 'VARCHAR',
            'TEXT': 'TEXT',
            'TIMESTAMP': 'DATETIME',
            'BOOLEAN': 'TINYINT(1)',
            'NUMERIC': 'DECIMAL',
            'REAL': 'FLOAT',
            'DOUBLE PRECISION': 'DOUBLE',
            'DATE': 'DATE',
            'TIME': 'TIME',
            'JSON': 'JSON',
            'JSONB': 'JSON'
        }
        
        pg_type_upper = pg_type.upper()
        for pg, mysql in type_map.items():
            if pg_type_upper.startswith(pg):
                # 保留长度信息
                if '(' in pg_type:
                    length = pg_type[pg_type.index('('):]
                    return mysql + length
                return mysql
        return pg_type  # 无法转换则保持原样
    
    def _convert_to_sqlite_type(self, pg_type):
        """PostgreSQL类型转SQLite类型"""
        type_map = {
            'INTEGER': 'INTEGER',
            'BIGINT': 'INTEGER',
            'VARCHAR': 'TEXT',
            'TEXT': 'TEXT',
            'TIMESTAMP': 'TEXT',
            'BOOLEAN': 'INTEGER',
            'NUMERIC': 'REAL',
            'REAL': 'REAL',
            'DOUBLE PRECISION': 'REAL',
            'DATE': 'TEXT',
            'TIME': 'TEXT',
            'JSON': 'TEXT',
            'JSONB': 'TEXT'
        }
        
        pg_type_upper = pg_type.upper()
        for pg, sqlite in type_map.items():
            if pg_type_upper.startswith(pg):
                return sqlite
        return 'TEXT'  # 默认TEXT
    
    def generate_markdown_doc(self, table_info):
        """生成Markdown文档"""
        lines = []
        lines.append(f"# 表: {table_info['name']}")
        lines.append("")
        lines.append(f"**数据行数**: {table_info['row_count']:,} 行")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 列信息表格
        lines.append("## 列定义")
        lines.append("")
        lines.append("| 列名 | 类型 | 允许NULL | 默认值 | 说明 |")
        lines.append("|------|------|----------|--------|------|")
        for col in table_info['columns']:
            nullable = '✅' if col['nullable'] else '❌'
            default = col['default'] or '-'
            comment = col['comment'] or '-'
            lines.append(f"| {col['name']} | {col['type']} | {nullable} | {default} | {comment} |")
        lines.append("")
        
        # 主键
        if table_info['primary_keys']:
            lines.append("## 主键")
            lines.append("")
            lines.append(f"- `{', '.join(table_info['primary_keys'])}`")
            lines.append("")
        
        # 外键
        if table_info['foreign_keys']:
            lines.append("## 外键")
            lines.append("")
            for fk in table_info['foreign_keys']:
                fk_cols = ', '.join(fk['columns'])
                ref_cols = ', '.join(fk['ref_columns'])
                lines.append(f"- `{fk_cols}` → `{fk['ref_table']}({ref_cols})`")
            lines.append("")
        
        # 索引
        if table_info['indexes']:
            lines.append("## 索引")
            lines.append("")
            lines.append("| 索引名 | 列 | 唯一 |")
            lines.append("|--------|----|----|")
            for idx in table_info['indexes']:
                unique = '✅' if idx['unique'] else '❌'
                cols = ', '.join(idx['columns'])
                lines.append(f"| {idx['name']} | {cols} | {unique} |")
            lines.append("")
        
        return '\n'.join(lines)
    
    def export_to_excel(self, all_tables_info, output_file):
        """导出到Excel数据字典"""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # 表清单
            tables_summary = []
            for table_info in all_tables_info:
                tables_summary.append({
                    '表名': table_info['name'],
                    '列数': len(table_info['columns']),
                    '行数': table_info['row_count'],
                    '主键': ', '.join(table_info['primary_keys']) if table_info['primary_keys'] else '-',
                    '外键数': len(table_info['foreign_keys']),
                    '索引数': len(table_info['indexes'])
                })
            df_summary = pd.DataFrame(tables_summary)
            df_summary.to_excel(writer, sheet_name='表清单', index=False)
            
            # 每个表的详细信息
            for table_info in all_tables_info:
                # 列信息
                columns_data = []
                for col in table_info['columns']:
                    columns_data.append({
                        '列名': col['name'],
                        '数据类型': col['type'],
                        '允许NULL': '是' if col['nullable'] else '否',
                        '默认值': col['default'] or '',
                        '说明': col['comment'] or '',
                        '是否主键': '✓' if col['name'] in table_info['primary_keys'] else ''
                    })
                df_cols = pd.DataFrame(columns_data)
                
                # 限制sheet名称长度
                sheet_name = table_info['name'][:31]
                df_cols.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"✅ Excel数据字典已生成: {output_file}")
    
    def export_all(self, tables=None):
        """导出所有表结构"""
        # 创建输出目录
        OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 获取要导出的表
        if tables:
            table_names = [t for t in tables if t in self.get_all_tables()]
        else:
            table_names = self.get_all_tables()
        
        if not table_names:
            print("❌ 没有找到要导出的表")
            return
        
        print(f"📋 准备导出 {len(table_names)} 个表...")
        print(f"   {', '.join(table_names)}")
        print("")
        
        # 收集所有表信息
        all_tables_info = []
        for table_name in table_names:
            print(f"🔍 分析表: {table_name}...", end=' ')
            table_info = self.get_table_info(table_name)
            all_tables_info.append(table_info)
            print(f"✅ ({table_info['row_count']:,} 行, {len(table_info['columns'])} 列)")
        
        print("")
        
        # 生成各种格式的DDL
        for table_info in all_tables_info:
            table_name = table_info['name']
            
            # PostgreSQL
            pg_file = OUTPUT_DIR / f"{table_name}_postgresql.sql"
            with open(pg_file, 'w', encoding='utf-8') as f:
                f.write(self.generate_postgresql_ddl(table_info))
            print(f"✅ PostgreSQL: {pg_file.name}")
            
            # MySQL
            mysql_file = OUTPUT_DIR / f"{table_name}_mysql.sql"
            with open(mysql_file, 'w', encoding='utf-8') as f:
                f.write(self.generate_mysql_ddl(table_info))
            print(f"✅ MySQL: {mysql_file.name}")
            
            # SQLite
            sqlite_file = OUTPUT_DIR / f"{table_name}_sqlite.sql"
            with open(sqlite_file, 'w', encoding='utf-8') as f:
                f.write(self.generate_sqlite_ddl(table_info))
            print(f"✅ SQLite: {sqlite_file.name}")
            
            # Markdown
            md_file = OUTPUT_DIR / f"{table_name}_文档.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(self.generate_markdown_doc(table_info))
            print(f"✅ 文档: {md_file.name}")
            print("")
        
        # 生成完整的SQL脚本(所有表)
        for db_type in ['postgresql', 'mysql', 'sqlite']:
            full_file = OUTPUT_DIR / f"完整数据库结构_{db_type}.sql"
            with open(full_file, 'w', encoding='utf-8') as f:
                f.write(f"-- ============================================\n")
                f.write(f"-- 完整数据库结构 ({db_type.upper()})\n")
                f.write(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- 包含表: {', '.join(table_names)}\n")
                f.write(f"-- ============================================\n\n")
                
                for table_info in all_tables_info:
                    if db_type == 'postgresql':
                        f.write(self.generate_postgresql_ddl(table_info))
                    elif db_type == 'mysql':
                        f.write(self.generate_mysql_ddl(table_info))
                    else:
                        f.write(self.generate_sqlite_ddl(table_info))
                    f.write("\n\n")
            print(f"✅ 完整脚本: {full_file.name}")
        
        # 生成Excel数据字典
        excel_file = OUTPUT_DIR / f"数据字典_{timestamp}.xlsx"
        self.export_to_excel(all_tables_info, excel_file)
        
        # 生成部署指南
        guide_file = OUTPUT_DIR / "部署指南.md"
        self._generate_deployment_guide(guide_file, all_tables_info)
        
        print("")
        print("="*60)
        print(f"🎉 导出完成! 文件保存在: {OUTPUT_DIR.absolute()}")
        print("="*60)
    
    def _generate_deployment_guide(self, output_file, all_tables_info):
        """生成部署指南"""
        lines = []
        lines.append("# 数据库部署指南")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**表数量**: {len(all_tables_info)} 个")
        lines.append("")
        
        lines.append("## 文件说明")
        lines.append("")
        lines.append("本次导出包含以下文件:")
        lines.append("")
        lines.append("### SQL脚本")
        lines.append("- `*_postgresql.sql` - PostgreSQL建表语句")
        lines.append("- `*_mysql.sql` - MySQL建表语句")
        lines.append("- `*_sqlite.sql` - SQLite建表语句")
        lines.append("- `完整数据库结构_*.sql` - 包含所有表的完整脚本")
        lines.append("")
        
        lines.append("### 文档")
        lines.append("- `*_文档.md` - 每个表的详细文档")
        lines.append("- `数据字典_*.xlsx` - Excel格式的完整数据字典")
        lines.append("- `部署指南.md` - 本文档")
        lines.append("")
        
        lines.append("## 部署步骤")
        lines.append("")
        
        # PostgreSQL
        lines.append("### PostgreSQL")
        lines.append("```bash")
        lines.append("# 连接数据库")
        lines.append("psql -U postgres -d your_database")
        lines.append("")
        lines.append("# 执行脚本")
        lines.append("\\i 完整数据库结构_postgresql.sql")
        lines.append("```")
        lines.append("")
        
        # MySQL
        lines.append("### MySQL")
        lines.append("```bash")
        lines.append("# 连接数据库")
        lines.append("mysql -u root -p your_database")
        lines.append("")
        lines.append("# 执行脚本")
        lines.append("source 完整数据库结构_mysql.sql;")
        lines.append("```")
        lines.append("")
        
        # SQLite
        lines.append("### SQLite")
        lines.append("```bash")
        lines.append("# 创建并执行")
        lines.append("sqlite3 your_database.db < 完整数据库结构_sqlite.sql")
        lines.append("```")
        lines.append("")
        
        lines.append("## 表清单")
        lines.append("")
        for table_info in all_tables_info:
            lines.append(f"### {table_info['name']}")
            lines.append(f"- **数据行数**: {table_info['row_count']:,} 行")
            lines.append(f"- **列数**: {len(table_info['columns'])} 列")
            if table_info['primary_keys']:
                lines.append(f"- **主键**: `{', '.join(table_info['primary_keys'])}`")
            lines.append("")
        
        lines.append("## 注意事项")
        lines.append("")
        lines.append("1. **类型兼容性**: 不同数据库的数据类型可能有差异,请根据实际情况调整")
        lines.append("2. **字符编码**: 建议使用UTF-8编码")
        lines.append("3. **权限设置**: 确保有CREATE TABLE权限")
        lines.append("4. **索引优化**: 大数据量时建议先导入数据再创建索引")
        lines.append("5. **外键约束**: 注意表创建顺序,先创建被引用的表")
        lines.append("")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ 部署指南: {output_file.name}")


def main():
    """主函数"""
    print("="*60)
    print("     智能数据库表结构导出工具 V1.0")
    print("="*60)
    print("")
    
    # 创建导出器
    exporter = DatabaseSchemaExporter(DATABASE_CONFIG)
    
    # 连接数据库
    print("🔌 正在连接数据库...")
    if not exporter.connect():
        print("")
        print("💡 提示:")
        print("   1. 请确认PostgreSQL服务已启动")
        print("   2. 检查数据库配置是否正确(DATABASE_CONFIG)")
        print("   3. 确认用户名和密码")
        return
    
    print("")
    
    # 显示可用的表
    all_tables = exporter.get_all_tables()
    print(f"📋 发现 {len(all_tables)} 个表:")
    for i, table in enumerate(all_tables, 1):
        print(f"   {i}. {table}")
    print("")
    
    # 选择要导出的表
    if TABLES_TO_EXPORT:
        print(f"📌 将导出指定的表: {', '.join(TABLES_TO_EXPORT)}")
        tables_to_export = TABLES_TO_EXPORT
    else:
        print("📌 将导出所有表")
        tables_to_export = None
    
    print("")
    input("按回车键开始导出...")
    print("")
    
    # 执行导出
    exporter.export_all(tables_to_export)
    
    print("")
    print("✨ 导出完成!你可以将导出的文件发送给同事。")
    print("")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\n按回车键退出...")
