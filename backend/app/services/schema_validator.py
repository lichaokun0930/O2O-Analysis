# -*- coding: utf-8 -*-
"""
预聚合表结构验证器

在应用启动和数据导入前自动检查表结构，确保与代码定义一致。
如果发现缺失字段，自动添加。

设计原则：
1. 启动时自动验证，不需要手动干预
2. 发现问题自动修复（添加缺失字段）
3. 记录所有修复操作，便于追踪
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from sqlalchemy import text

APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal


# 预聚合表的期望字段定义
EXPECTED_SCHEMA: Dict[str, Dict[str, str]] = {
    "store_daily_summary": {
        "id": "SERIAL PRIMARY KEY",
        "store_name": "VARCHAR(100) NOT NULL",
        "summary_date": "DATE",
        "channel": "VARCHAR(50)",
        "order_count": "INTEGER DEFAULT 0",
        "total_revenue": "DECIMAL(12,2) DEFAULT 0",
        "total_profit": "DECIMAL(12,2) DEFAULT 0",
        "total_delivery_fee": "DECIMAL(12,2) DEFAULT 0",
        "total_user_paid_delivery": "DECIMAL(12,2) DEFAULT 0",
        "total_delivery_discount": "DECIMAL(12,2) DEFAULT 0",
        "total_corporate_rebate": "DECIMAL(12,2) DEFAULT 0",
        "total_marketing_cost": "DECIMAL(12,2) DEFAULT 0",
        "total_platform_fee": "DECIMAL(12,2) DEFAULT 0",
        "active_products": "INTEGER DEFAULT 0",
        "gmv": "DECIMAL(12,2) DEFAULT 0",
        "avg_order_value": "DECIMAL(12,2) DEFAULT 0",
        "profit_margin": "DECIMAL(8,4) DEFAULT 0",
        "delivery_net_cost": "DECIMAL(12,2) DEFAULT 0",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    },
    "store_hourly_summary": {
        "id": "SERIAL PRIMARY KEY",
        "store_name": "VARCHAR(100) NOT NULL",
        "summary_date": "DATE",
        "hour_of_day": "INTEGER",
        "channel": "VARCHAR(50)",
        "order_count": "INTEGER DEFAULT 0",
        "total_revenue": "DECIMAL(12,2) DEFAULT 0",
        "total_profit": "DECIMAL(12,2) DEFAULT 0",
        "total_delivery_fee": "DECIMAL(12,2) DEFAULT 0",
        "delivery_net_cost": "DECIMAL(12,2) DEFAULT 0",
        "total_marketing_cost": "DECIMAL(12,2) DEFAULT 0",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    },
    "category_daily_summary": {
        "id": "SERIAL PRIMARY KEY",
        "store_name": "VARCHAR(100) NOT NULL",
        "summary_date": "DATE",
        "category_level1": "VARCHAR(100)",
        "category_level3": "VARCHAR(100)",
        "channel": "VARCHAR(50)",
        "order_count": "INTEGER DEFAULT 0",
        "product_count": "INTEGER DEFAULT 0",
        "total_quantity": "INTEGER DEFAULT 0",
        "total_revenue": "DECIMAL(12,2) DEFAULT 0",
        "total_original_price": "DECIMAL(12,2) DEFAULT 0",
        "total_cost": "DECIMAL(12,2) DEFAULT 0",
        "total_profit": "DECIMAL(12,2) DEFAULT 0",
        "avg_discount": "DECIMAL(8,4) DEFAULT 0",
        "profit_margin": "DECIMAL(8,4) DEFAULT 0",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    },
    "delivery_summary": {
        "id": "SERIAL PRIMARY KEY",
        "store_name": "VARCHAR(100) NOT NULL",
        "summary_date": "DATE",
        "hour_of_day": "INTEGER",
        "distance_band": "VARCHAR(20)",
        "channel": "VARCHAR(50)",
        "order_count": "INTEGER DEFAULT 0",
        "total_revenue": "DECIMAL(12,2) DEFAULT 0",
        "delivery_net_cost": "DECIMAL(12,2) DEFAULT 0",
        "high_delivery_count": "INTEGER DEFAULT 0",
        "avg_delivery_fee": "DECIMAL(12,2) DEFAULT 0",
        "distance_min": "DECIMAL(8,2) DEFAULT 0",
        "distance_max": "DECIMAL(8,2) DEFAULT 0",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    },
    "product_daily_summary": {
        "id": "SERIAL PRIMARY KEY",
        "store_name": "VARCHAR(100) NOT NULL",
        "summary_date": "DATE",
        "product_name": "VARCHAR(200)",
        "category_level1": "VARCHAR(100)",
        "channel": "VARCHAR(50)",
        "order_count": "INTEGER DEFAULT 0",
        "total_quantity": "INTEGER DEFAULT 0",
        "total_revenue": "DECIMAL(12,2) DEFAULT 0",
        "total_cost": "DECIMAL(12,2) DEFAULT 0",
        "total_profit": "DECIMAL(12,2) DEFAULT 0",
        "avg_price": "DECIMAL(12,2) DEFAULT 0",
        "profit_margin": "DECIMAL(8,4) DEFAULT 0",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
    },
}


class SchemaValidator:
    """预聚合表结构验证器"""
    
    @staticmethod
    def validate_and_fix_all() -> Tuple[bool, List[str]]:
        """
        验证并修复所有预聚合表结构
        
        Returns:
            (success, messages): 是否全部成功，操作日志
        """
        messages = []
        all_success = True
        
        session = SessionLocal()
        try:
            for table_name, expected_fields in EXPECTED_SCHEMA.items():
                success, table_messages = SchemaValidator._validate_table(
                    session, table_name, expected_fields
                )
                messages.extend(table_messages)
                if not success:
                    all_success = False
            
            session.commit()
            
        except Exception as e:
            messages.append(f"❌ 验证过程出错: {e}")
            session.rollback()
            all_success = False
        finally:
            session.close()
        
        return all_success, messages
    
    @staticmethod
    def _validate_table(session, table_name: str, expected_fields: Dict[str, str]) -> Tuple[bool, List[str]]:
        """验证单个表结构"""
        messages = []
        
        # 检查表是否存在
        try:
            result = session.execute(text(f"SELECT 1 FROM {table_name} LIMIT 1"))
            result.fetchone()
        except Exception:
            messages.append(f"⚠️ 表 {table_name} 不存在，将在首次同步时创建")
            return True, messages
        
        # 获取现有字段
        result = session.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
        """))
        existing_columns = {row[0].lower() for row in result.fetchall()}
        
        # 检查缺失字段
        missing_fields = []
        for field_name, field_def in expected_fields.items():
            if field_name.lower() not in existing_columns:
                missing_fields.append((field_name, field_def))
        
        if not missing_fields:
            return True, messages
        
        # 添加缺失字段
        for field_name, field_def in missing_fields:
            # 提取类型（去掉 PRIMARY KEY, NOT NULL 等约束）
            field_type = field_def.split()[0]
            if field_type == "SERIAL":
                # SERIAL 不能后加，跳过
                messages.append(f"⚠️ {table_name}.{field_name}: SERIAL 字段无法后加，请手动处理")
                continue
            
            # 提取默认值
            default_clause = ""
            if "DEFAULT" in field_def.upper():
                default_idx = field_def.upper().index("DEFAULT")
                default_clause = field_def[default_idx:]
            
            try:
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {field_name} {field_type} {default_clause}"
                session.execute(text(alter_sql))
                messages.append(f"✅ 已添加字段: {table_name}.{field_name}")
            except Exception as e:
                messages.append(f"❌ 添加字段失败: {table_name}.{field_name} - {e}")
                return False, messages
        
        return True, messages
    
    @staticmethod
    def get_missing_fields(table_name: str) -> List[str]:
        """获取表缺失的字段列表"""
        if table_name not in EXPECTED_SCHEMA:
            return []
        
        session = SessionLocal()
        try:
            result = session.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
            """))
            existing_columns = {row[0].lower() for row in result.fetchall()}
            
            expected_fields = EXPECTED_SCHEMA[table_name]
            missing = [f for f in expected_fields.keys() if f.lower() not in existing_columns]
            return missing
        except:
            return []
        finally:
            session.close()


def validate_schema_on_startup():
    """启动时验证表结构（供 main.py 调用）"""
    print("🔍 验证预聚合表结构...")
    success, messages = SchemaValidator.validate_and_fix_all()
    
    for msg in messages:
        print(f"   {msg}")
    
    if success:
        print("✅ 预聚合表结构验证通过")
    else:
        print("⚠️ 预聚合表结构存在问题，请检查日志")
    
    return success


# 单例
schema_validator = SchemaValidator()
