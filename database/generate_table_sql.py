# -*- coding: utf-8 -*-
"""
根据 aggregation_config.py 自动生成建表 SQL

用法：
    python database/generate_table_sql.py [表名]
    
    不指定表名则生成所有表的 SQL
"""

import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from services.aggregation_config import AGGREGATION_CONFIGS, AggregationConfig


def generate_create_table_sql(config: AggregationConfig) -> str:
    """根据配置生成 CREATE TABLE SQL"""
    
    lines = []
    lines.append(f"-- {config.description}")
    lines.append(f"CREATE TABLE IF NOT EXISTS {config.table_name} (")
    lines.append("    id SERIAL PRIMARY KEY,")
    
    # 从 group_by 提取字段
    for g in config.group_by:
        if " as " in g.lower():
            # 有别名，如 "DATE(date) as summary_date"
            field_name = g.lower().split(" as ")[1].strip()
            # 推断类型
            if "date" in field_name.lower():
                field_type = "DATE"
            elif "hour" in field_name.lower():
                field_type = "INTEGER"
            else:
                field_type = "VARCHAR(100)"
            lines.append(f"    {field_name} {field_type},")
        elif g == "store_name":
            lines.append("    store_name VARCHAR(100) NOT NULL,")
        elif g == "channel":
            lines.append("    channel VARCHAR(50),")
        elif g == "category_level1":
            lines.append("    category_level1 VARCHAR(100),")
        elif g == "category_level3":
            lines.append("    category_level3 VARCHAR(100),")
        elif g == "product_name":
            lines.append("    product_name VARCHAR(200),")
        elif "distance_band" in g.lower():
            lines.append("    distance_band VARCHAR(20),")
        else:
            lines.append(f"    {g} VARCHAR(100),")
    
    # 从 fields 提取字段
    for f in config.fields:
        if "count" in f.name.lower():
            field_type = "INTEGER DEFAULT 0"
        else:
            field_type = "DECIMAL(12,2) DEFAULT 0"
        lines.append(f"    {f.name} {field_type},")
    
    # 从 derived_fields 提取字段
    for df in config.derived_fields:
        if "count" in df.name.lower():
            field_type = "INTEGER DEFAULT 0"
        else:
            field_type = "DECIMAL(12,2) DEFAULT 0"
        lines.append(f"    {df.name} {field_type},")
    
    # 时间戳
    lines.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
    lines.append("    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    lines.append(");")
    
    # 索引
    lines.append("")
    lines.append(f"-- 索引")
    lines.append(f"CREATE INDEX IF NOT EXISTS idx_{config.table_name}_store ON {config.table_name}(store_name);")
    
    # 日期索引
    for g in config.group_by:
        if " as " in g.lower():
            field_name = g.lower().split(" as ")[1].strip()
            if "date" in field_name.lower() or "week" in field_name.lower():
                lines.append(f"CREATE INDEX IF NOT EXISTS idx_{config.table_name}_{field_name} ON {config.table_name}({field_name});")
    
    # 复合索引
    date_field = None
    for g in config.group_by:
        if " as " in g.lower():
            field_name = g.lower().split(" as ")[1].strip()
            if "date" in field_name.lower():
                date_field = field_name
                break
    
    if date_field:
        lines.append(f"CREATE INDEX IF NOT EXISTS idx_{config.table_name}_store_{date_field} ON {config.table_name}(store_name, {date_field});")
    
    return "\n".join(lines)


def main():
    if len(sys.argv) > 1:
        # 生成指定表的 SQL
        table_name = sys.argv[1]
        if table_name in AGGREGATION_CONFIGS:
            config = AGGREGATION_CONFIGS[table_name]
            print(generate_create_table_sql(config))
        else:
            print(f"错误：未找到表配置 '{table_name}'")
            print(f"可用的表：{list(AGGREGATION_CONFIGS.keys())}")
            sys.exit(1)
    else:
        # 生成所有表的 SQL
        print("-- ============================================")
        print("-- 预聚合表建表 SQL（自动生成）")
        print("-- ============================================")
        print()
        
        for table_name, config in AGGREGATION_CONFIGS.items():
            print(generate_create_table_sql(config))
            print()
            print()


if __name__ == "__main__":
    main()
