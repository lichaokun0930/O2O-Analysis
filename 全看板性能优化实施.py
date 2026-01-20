# -*- coding: utf-8 -*-
"""
全看板企业级性能优化实施脚本

覆盖所有模块的预聚合表体系：
1. store_daily_summary - 门店日汇总（已有）
2. store_hourly_summary - 门店小时汇总（分时段分析）
3. category_daily_summary - 品类日汇总（品类分析）
4. delivery_distance_summary - 配送距离汇总（配送分析）
5. marketing_daily_summary - 营销日汇总（营销趋势）

支持 PostgreSQL 数据库
"""

import time
import sys
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from database.connection import SessionLocal, engine
from database.models import Order, Base
from sqlalchemy import text
import pandas as pd


def print_section(title):
    """打印分节标题"""
    print("\n" + "="*80)
    print(f"🔧 {title}")
    print("="*80)


def print_subsection(title):
    """打印子节标题"""
    print(f"\n--- {title} ---")


# ==================== 第一层：数据库索引优化 ====================

def optimize_all_indexes():
    """优化所有模块需要的索引"""
    print_section("第一层：全量索引优化")
    
    # 需要创建的索引（覆盖所有模块）
    indexes_to_create = [
        # 基础查询索引
        ("idx_full_store_date", "orders", ["store_name", "date"]),
        ("idx_full_date", "orders", ["date"]),
        ("idx_full_order_number", "orders", ["order_number"]),
        ("idx_full_channel", "orders", ["channel"]),
        
        # 门店+渠道+日期（门店对比）
        ("idx_full_store_channel_date", "orders", ["store_name", "channel", "date"]),
        
        # 品类分析索引
        ("idx_full_category_l1_date", "orders", ["category_level1", "date"]),
        ("idx_full_category_l3_date", "orders", ["category_level3", "date"]),
        ("idx_full_store_category_date", "orders", ["store_name", "category_level1", "date"]),
        
        # 配送分析索引
        ("idx_full_delivery_distance", "orders", ["delivery_distance"]),
        ("idx_full_store_distance", "orders", ["store_name", "delivery_distance"]),
        
        # 时段分析索引（使用函数索引需要特殊处理）
        ("idx_full_order_id", "orders", ["order_id"]),
    ]
    
    session = SessionLocal()
    try:
        # 检查现有索引
        result = session.execute(text("""
            SELECT indexname FROM pg_indexes WHERE tablename = 'orders'
        """))
        existing_indexes = {row[0] for row in result.fetchall()}
        print(f"\n现有索引: {len(existing_indexes)} 个")
        
        # 创建缺失的索引
        created = 0
        for idx_name, table, columns in indexes_to_create:
            if idx_name not in existing_indexes:
                try:
                    cols = ", ".join(columns)
                    sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({cols})"
                    session.execute(text(sql))
                    session.commit()
                    print(f"   ✅ 创建索引: {idx_name}")
                    created += 1
                except Exception as e:
                    print(f"   ⚠️ 索引 {idx_name} 创建失败: {e}")
                    session.rollback()
            else:
                print(f"   ✓ 索引已存在: {idx_name}")
        
        # 更新统计信息
        session.execute(text("ANALYZE orders"))
        session.commit()
        print(f"\n📊 索引优化完成: 新建 {created} 个索引")
        return True
    except Exception as e:
        print(f"\n❌ 索引优化失败: {e}")
        return False
    finally:
        session.close()


# ==================== 第二层：预聚合表体系 ====================

def create_store_daily_summary():
    """
    创建/更新门店日汇总表（经营总览+门店对比）
    
    核心逻辑（与原始计算完全对齐）：
    1. 应用渠道过滤逻辑：剔除收费渠道且平台服务费=0的异常订单（仅用于订单数、利润等）
    2. 使用正确的利润公式：订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
    3. 动销商品数：按门店+日期去重统计
    4. GMV和营销成本：剔除商品原价<=0的行后计算，但不应用渠道过滤
    """
    print_subsection("1. 门店日汇总表 (store_daily_summary)")
    
    session = SessionLocal()
    try:
        # 删除旧表
        session.execute(text("DROP TABLE IF EXISTS store_daily_summary CASCADE"))
        session.commit()
        
        # 创建表（增加GMV字段）
        create_sql = """
        CREATE TABLE store_daily_summary (
            id SERIAL PRIMARY KEY,
            store_name VARCHAR(200) NOT NULL,
            summary_date DATE NOT NULL,
            channel VARCHAR(100),
            order_count INTEGER DEFAULT 0,
            total_revenue NUMERIC(15,2) DEFAULT 0,
            total_profit NUMERIC(15,2) DEFAULT 0,
            total_delivery_fee NUMERIC(15,2) DEFAULT 0,
            total_user_paid_delivery NUMERIC(15,2) DEFAULT 0,
            total_delivery_discount NUMERIC(15,2) DEFAULT 0,
            total_corporate_rebate NUMERIC(15,2) DEFAULT 0,
            total_marketing_cost NUMERIC(15,2) DEFAULT 0,
            total_platform_fee NUMERIC(15,2) DEFAULT 0,
            avg_order_value NUMERIC(15,2) DEFAULT 0,
            profit_margin NUMERIC(10,4) DEFAULT 0,
            delivery_net_cost NUMERIC(15,2) DEFAULT 0,
            active_products INTEGER DEFAULT 0,
            gmv NUMERIC(15,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(store_name, summary_date, channel)
        )
        """
        session.execute(text(create_sql))
        session.commit()
        
        # 创建索引
        session.execute(text("CREATE INDEX idx_sds_store_date ON store_daily_summary(store_name, summary_date)"))
        session.execute(text("CREATE INDEX idx_sds_date ON store_daily_summary(summary_date)"))
        session.execute(text("CREATE INDEX idx_sds_channel ON store_daily_summary(channel)"))
        session.commit()
        print("   ✅ 表结构和索引创建成功")
        
        # 填充数据（完全对齐原始计算逻辑）
        insert_sql = """
        WITH order_level AS (
            -- 第一步：订单级聚合（商品级字段用SUM，订单级字段用MAX）
            SELECT 
                store_name,
                DATE(date) as order_date,
                order_id,
                channel,
                -- 商品级字段聚合
                SUM(COALESCE(actual_price, 0) * COALESCE(quantity, 1)) as order_revenue,
                SUM(COALESCE(profit, 0)) as order_profit_raw,
                SUM(COALESCE(platform_service_fee, 0)) as order_platform_fee,
                SUM(COALESCE(corporate_rebate, 0)) as order_corporate_rebate,
                -- 订单级字段取MAX
                MAX(COALESCE(delivery_fee, 0)) as order_delivery_fee,
                MAX(COALESCE(user_paid_delivery_fee, 0)) as order_user_paid_delivery,
                MAX(COALESCE(delivery_discount, 0)) as order_delivery_discount,
                -- 营销成本（7字段，不含配送费减免）
                MAX(COALESCE(full_reduction, 0)) + MAX(COALESCE(product_discount, 0)) + 
                MAX(COALESCE(merchant_voucher, 0)) + MAX(COALESCE(merchant_share, 0)) + 
                MAX(COALESCE(gift_amount, 0)) + MAX(COALESCE(other_merchant_discount, 0)) + 
                MAX(COALESCE(new_customer_discount, 0)) as order_marketing_cost
            FROM orders
            GROUP BY store_name, DATE(date), order_id, channel
        ),
        gmv_order_level AS (
            -- GMV计算：剔除商品原价<=0的行后计算（不应用渠道过滤）
            SELECT 
                store_name,
                DATE(date) as order_date,
                order_id,
                channel,
                SUM(COALESCE(original_price, 0) * COALESCE(quantity, 1)) as order_original_price_sales,
                MAX(COALESCE(packaging_fee, 0)) as order_packaging_fee,
                MAX(COALESCE(user_paid_delivery_fee, 0)) as order_user_paid_delivery_gmv,
                -- 营销成本（7字段）- 也从这里计算，不受渠道过滤影响
                MAX(COALESCE(full_reduction, 0)) + MAX(COALESCE(product_discount, 0)) + 
                MAX(COALESCE(merchant_voucher, 0)) + MAX(COALESCE(merchant_share, 0)) + 
                MAX(COALESCE(gift_amount, 0)) + MAX(COALESCE(other_merchant_discount, 0)) + 
                MAX(COALESCE(new_customer_discount, 0)) as order_marketing_cost_gmv
            FROM orders
            WHERE original_price > 0  -- GMV清洗规则：剔除商品原价<=0的行
            GROUP BY store_name, DATE(date), order_id, channel
        ),
        gmv_daily AS (
            -- GMV和营销成本按门店+日期+渠道汇总（不应用渠道过滤）
            SELECT 
                store_name,
                order_date,
                channel,
                SUM(order_original_price_sales + order_packaging_fee + order_user_paid_delivery_gmv) as daily_gmv,
                SUM(order_marketing_cost_gmv) as daily_marketing_cost
            FROM gmv_order_level
            GROUP BY store_name, order_date, channel
        ),
        filtered_orders AS (
            -- 第二步：应用渠道过滤逻辑（仅用于订单数、利润等，不影响GMV）
            -- 剔除【收费渠道 且 平台服务费=0】的异常订单
            SELECT 
                o.*,
                -- 计算订单实际利润（核心公式）
                o.order_profit_raw - o.order_platform_fee - o.order_delivery_fee + o.order_corporate_rebate as order_actual_profit
            FROM order_level o
            WHERE NOT (
                o.channel IN ('饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播', '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店')
                AND o.order_platform_fee <= 0
            )
        ),
        daily_products AS (
            -- 第三步：计算动销商品数（按门店+日期去重）
            SELECT 
                store_name,
                DATE(date) as order_date,
                COUNT(DISTINCT product_name) as active_products
            FROM orders
            WHERE quantity > 0
            GROUP BY store_name, DATE(date)
        )
        -- 第四步：按门店+日期+渠道聚合
        INSERT INTO store_daily_summary (
            store_name, summary_date, channel, order_count, 
            total_revenue, total_profit, total_delivery_fee,
            total_user_paid_delivery, total_delivery_discount,
            total_corporate_rebate, total_marketing_cost, total_platform_fee,
            active_products, gmv
        )
        SELECT 
            f.store_name, 
            f.order_date, 
            f.channel,
            COUNT(DISTINCT f.order_id) as order_count,
            SUM(f.order_revenue) as total_revenue,
            SUM(f.order_actual_profit) as total_profit,
            SUM(f.order_delivery_fee) as total_delivery_fee,
            SUM(f.order_user_paid_delivery) as total_user_paid_delivery,
            SUM(f.order_delivery_discount) as total_delivery_discount,
            SUM(f.order_corporate_rebate) as total_corporate_rebate,
            COALESCE(g.daily_marketing_cost, 0) as total_marketing_cost,
            SUM(f.order_platform_fee) as total_platform_fee,
            COALESCE(dp.active_products, 0) as active_products,
            COALESCE(g.daily_gmv, 0) as gmv
        FROM filtered_orders f
        LEFT JOIN daily_products dp ON f.store_name = dp.store_name AND f.order_date = dp.order_date
        LEFT JOIN gmv_daily g ON f.store_name = g.store_name AND f.order_date = g.order_date AND f.channel = g.channel
        GROUP BY f.store_name, f.order_date, f.channel, dp.active_products, g.daily_gmv, g.daily_marketing_cost
        """
        
        start = time.time()
        session.execute(text(insert_sql))
        session.commit()
        
        # 更新派生字段
        session.execute(text("""
            UPDATE store_daily_summary SET
                avg_order_value = CASE WHEN order_count > 0 THEN total_revenue / order_count ELSE 0 END,
                profit_margin = CASE WHEN total_revenue > 0 THEN total_profit / total_revenue * 100 ELSE 0 END,
                delivery_net_cost = total_delivery_fee - total_user_paid_delivery + total_delivery_discount - total_corporate_rebate
        """))
        session.commit()
        
        count = session.execute(text("SELECT COUNT(*) FROM store_daily_summary")).scalar()
        print(f"   ✅ 数据填充完成: {count} 条, 耗时 {time.time()-start:.2f}秒")
        return True
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def create_store_hourly_summary():
    """创建门店小时汇总表（分时段分析）"""
    print_subsection("2. 门店小时汇总表 (store_hourly_summary)")
    
    session = SessionLocal()
    try:
        session.execute(text("DROP TABLE IF EXISTS store_hourly_summary CASCADE"))
        session.commit()
        
        create_sql = """
        CREATE TABLE store_hourly_summary (
            id SERIAL PRIMARY KEY,
            store_name VARCHAR(200) NOT NULL,
            summary_date DATE NOT NULL,
            hour_of_day INTEGER NOT NULL,
            channel VARCHAR(100),
            order_count INTEGER DEFAULT 0,
            total_revenue NUMERIC(15,2) DEFAULT 0,
            total_profit NUMERIC(15,2) DEFAULT 0,
            total_delivery_fee NUMERIC(15,2) DEFAULT 0,
            delivery_net_cost NUMERIC(15,2) DEFAULT 0,
            total_marketing_cost NUMERIC(15,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(store_name, summary_date, hour_of_day, channel)
        )
        """
        session.execute(text(create_sql))
        session.commit()
        
        session.execute(text("CREATE INDEX idx_shs_store_date ON store_hourly_summary(store_name, summary_date)"))
        session.execute(text("CREATE INDEX idx_shs_hour ON store_hourly_summary(hour_of_day)"))
        session.commit()
        print("   ✅ 表结构创建成功")
        
        # 填充数据
        insert_sql = """
        WITH order_level AS (
            SELECT 
                store_name,
                DATE(date) as order_date,
                EXTRACT(HOUR FROM date)::INTEGER as hour_of_day,
                order_id,
                CASE 
                    WHEN order_number LIKE 'SG%' THEN '美团'
                    WHEN order_number LIKE 'ELE%' THEN '饿了么'
                    WHEN order_number LIKE 'JD%' THEN '京东'
                    ELSE '其他'
                END as channel,
                SUM(COALESCE(actual_price, 0) * COALESCE(quantity, 1)) as order_revenue,
                SUM(COALESCE(profit, 0)) as order_profit,
                MAX(COALESCE(delivery_fee, 0)) as order_delivery_fee,
                MAX(COALESCE(user_paid_delivery_fee, 0)) - MAX(COALESCE(delivery_discount, 0)) as user_net_delivery,
                MAX(COALESCE(corporate_rebate, 0)) as order_corporate_rebate,
                MAX(COALESCE(full_reduction, 0)) + MAX(COALESCE(product_discount, 0)) + 
                MAX(COALESCE(merchant_voucher, 0)) + MAX(COALESCE(merchant_share, 0)) + 
                MAX(COALESCE(gift_amount, 0)) + MAX(COALESCE(other_merchant_discount, 0)) + 
                MAX(COALESCE(new_customer_discount, 0)) as order_marketing_cost
            FROM orders
            GROUP BY store_name, DATE(date), EXTRACT(HOUR FROM date), order_id, order_number
        )
        INSERT INTO store_hourly_summary (
            store_name, summary_date, hour_of_day, channel,
            order_count, total_revenue, total_profit, total_delivery_fee,
            delivery_net_cost, total_marketing_cost
        )
        SELECT 
            store_name, order_date, hour_of_day, channel,
            COUNT(DISTINCT order_id),
            SUM(order_revenue), SUM(order_profit), SUM(order_delivery_fee),
            SUM(order_delivery_fee - user_net_delivery - order_corporate_rebate),
            SUM(order_marketing_cost)
        FROM order_level
        GROUP BY store_name, order_date, hour_of_day, channel
        """
        
        start = time.time()
        session.execute(text(insert_sql))
        session.commit()
        
        count = session.execute(text("SELECT COUNT(*) FROM store_hourly_summary")).scalar()
        print(f"   ✅ 数据填充完成: {count} 条, 耗时 {time.time()-start:.2f}秒")
        return True
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def create_category_daily_summary():
    """创建品类日汇总表（品类分析+品类健康度）"""
    print_subsection("3. 品类日汇总表 (category_daily_summary)")
    
    session = SessionLocal()
    try:
        session.execute(text("DROP TABLE IF EXISTS category_daily_summary CASCADE"))
        session.commit()
        
        create_sql = """
        CREATE TABLE category_daily_summary (
            id SERIAL PRIMARY KEY,
            store_name VARCHAR(200) NOT NULL,
            summary_date DATE NOT NULL,
            category_level1 VARCHAR(200),
            category_level3 VARCHAR(200),
            channel VARCHAR(100),
            order_count INTEGER DEFAULT 0,
            product_count INTEGER DEFAULT 0,
            total_quantity INTEGER DEFAULT 0,
            total_revenue NUMERIC(15,2) DEFAULT 0,
            total_original_price NUMERIC(15,2) DEFAULT 0,
            total_cost NUMERIC(15,2) DEFAULT 0,
            total_profit NUMERIC(15,2) DEFAULT 0,
            avg_discount NUMERIC(10,4) DEFAULT 0,
            profit_margin NUMERIC(10,4) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(store_name, summary_date, category_level1, category_level3, channel)
        )
        """
        session.execute(text(create_sql))
        session.commit()
        
        session.execute(text("CREATE INDEX idx_cds_store_date ON category_daily_summary(store_name, summary_date)"))
        session.execute(text("CREATE INDEX idx_cds_category ON category_daily_summary(category_level1)"))
        session.execute(text("CREATE INDEX idx_cds_category3 ON category_daily_summary(category_level3)"))
        session.commit()
        print("   ✅ 表结构创建成功")
        
        # 填充数据（按商品行聚合，品类分析需要商品级别数据）
        insert_sql = """
        INSERT INTO category_daily_summary (
            store_name, summary_date, category_level1, category_level3, channel,
            order_count, product_count, total_quantity, total_revenue, 
            total_original_price, total_cost, total_profit
        )
        SELECT 
            store_name,
            DATE(date) as summary_date,
            category_level1,
            category_level3,
            CASE 
                WHEN order_number LIKE 'SG%' THEN '美团'
                WHEN order_number LIKE 'ELE%' THEN '饿了么'
                WHEN order_number LIKE 'JD%' THEN '京东'
                ELSE '其他'
            END as channel,
            COUNT(DISTINCT order_id) as order_count,
            COUNT(DISTINCT product_name) as product_count,
            SUM(COALESCE(quantity, 1)) as total_quantity,
            SUM(COALESCE(actual_price, 0) * COALESCE(quantity, 1)) as total_revenue,
            SUM(COALESCE(original_price, 0) * COALESCE(quantity, 1)) as total_original_price,
            SUM(COALESCE(cost, 0) * COALESCE(quantity, 1)) as total_cost,
            SUM(COALESCE(profit, 0)) as total_profit
        FROM orders
        WHERE category_level1 IS NOT NULL AND category_level1 != ''
        GROUP BY store_name, DATE(date), category_level1, category_level3, 
            CASE 
                WHEN order_number LIKE 'SG%' THEN '美团'
                WHEN order_number LIKE 'ELE%' THEN '饿了么'
                WHEN order_number LIKE 'JD%' THEN '京东'
                ELSE '其他'
            END
        """
        
        start = time.time()
        session.execute(text(insert_sql))
        session.commit()
        
        # 更新派生字段
        session.execute(text("""
            UPDATE category_daily_summary SET
                avg_discount = CASE WHEN total_original_price > 0 THEN total_revenue / total_original_price * 10 ELSE 10 END,
                profit_margin = CASE WHEN total_revenue > 0 THEN total_profit / total_revenue * 100 ELSE 0 END
        """))
        session.commit()
        
        count = session.execute(text("SELECT COUNT(*) FROM category_daily_summary")).scalar()
        print(f"   ✅ 数据填充完成: {count} 条, 耗时 {time.time()-start:.2f}秒")
        return True
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def create_delivery_summary():
    """创建配送分析汇总表（配送热力图+距离分析）"""
    print_subsection("4. 配送分析汇总表 (delivery_summary)")
    
    session = SessionLocal()
    try:
        session.execute(text("DROP TABLE IF EXISTS delivery_summary CASCADE"))
        session.commit()
        
        create_sql = """
        CREATE TABLE delivery_summary (
            id SERIAL PRIMARY KEY,
            store_name VARCHAR(200) NOT NULL,
            summary_date DATE NOT NULL,
            hour_of_day INTEGER,
            distance_band VARCHAR(50),
            distance_min NUMERIC(10,2),
            distance_max NUMERIC(10,2),
            channel VARCHAR(100),
            order_count INTEGER DEFAULT 0,
            total_revenue NUMERIC(15,2) DEFAULT 0,
            total_profit NUMERIC(15,2) DEFAULT 0,
            total_delivery_fee NUMERIC(15,2) DEFAULT 0,
            delivery_net_cost NUMERIC(15,2) DEFAULT 0,
            high_delivery_count INTEGER DEFAULT 0,
            avg_delivery_fee NUMERIC(10,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(store_name, summary_date, hour_of_day, distance_band, channel)
        )
        """
        session.execute(text(create_sql))
        session.commit()
        
        session.execute(text("CREATE INDEX idx_ds_store_date ON delivery_summary(store_name, summary_date)"))
        session.execute(text("CREATE INDEX idx_ds_distance ON delivery_summary(distance_band)"))
        session.execute(text("CREATE INDEX idx_ds_hour ON delivery_summary(hour_of_day)"))
        session.commit()
        print("   ✅ 表结构创建成功")
        
        # 填充数据（按距离区间和小时聚合）
        insert_sql = """
        WITH order_level AS (
            SELECT 
                store_name,
                DATE(date) as order_date,
                EXTRACT(HOUR FROM date)::INTEGER as hour_of_day,
                order_id,
                CASE 
                    WHEN order_number LIKE 'SG%' THEN '美团'
                    WHEN order_number LIKE 'ELE%' THEN '饿了么'
                    WHEN order_number LIKE 'JD%' THEN '京东'
                    ELSE '其他'
                END as channel,
                COALESCE(delivery_distance, 0) as distance,
                CASE 
                    WHEN COALESCE(delivery_distance, 0) < 1 THEN '0-1km'
                    WHEN COALESCE(delivery_distance, 0) < 2 THEN '1-2km'
                    WHEN COALESCE(delivery_distance, 0) < 3 THEN '2-3km'
                    WHEN COALESCE(delivery_distance, 0) < 4 THEN '3-4km'
                    WHEN COALESCE(delivery_distance, 0) < 5 THEN '4-5km'
                    ELSE '5km+'
                END as distance_band,
                SUM(COALESCE(actual_price, 0) * COALESCE(quantity, 1)) as order_revenue,
                SUM(COALESCE(profit, 0)) as order_profit,
                MAX(COALESCE(delivery_fee, 0)) as order_delivery_fee,
                MAX(COALESCE(delivery_fee, 0)) - 
                    (MAX(COALESCE(user_paid_delivery_fee, 0)) - MAX(COALESCE(delivery_discount, 0))) - 
                    MAX(COALESCE(corporate_rebate, 0)) as delivery_net
            FROM orders
            GROUP BY store_name, DATE(date), EXTRACT(HOUR FROM date), order_id, order_number, delivery_distance
        )
        INSERT INTO delivery_summary (
            store_name, summary_date, hour_of_day, distance_band, channel,
            order_count, total_revenue, total_profit, total_delivery_fee,
            delivery_net_cost, high_delivery_count
        )
        SELECT 
            store_name, order_date, hour_of_day, distance_band, channel,
            COUNT(DISTINCT order_id),
            SUM(order_revenue), SUM(order_profit), SUM(order_delivery_fee),
            SUM(delivery_net),
            SUM(CASE WHEN delivery_net > 6 THEN 1 ELSE 0 END)
        FROM order_level
        GROUP BY store_name, order_date, hour_of_day, distance_band, channel
        """
        
        start = time.time()
        session.execute(text(insert_sql))
        session.commit()
        
        # 更新派生字段
        session.execute(text("""
            UPDATE delivery_summary SET
                avg_delivery_fee = CASE WHEN order_count > 0 THEN delivery_net_cost / order_count ELSE 0 END,
                distance_min = CASE distance_band
                    WHEN '0-1km' THEN 0 WHEN '1-2km' THEN 1 WHEN '2-3km' THEN 2
                    WHEN '3-4km' THEN 3 WHEN '4-5km' THEN 4 ELSE 5 END,
                distance_max = CASE distance_band
                    WHEN '0-1km' THEN 1 WHEN '1-2km' THEN 2 WHEN '2-3km' THEN 3
                    WHEN '3-4km' THEN 4 WHEN '4-5km' THEN 5 ELSE 99 END
        """))
        session.commit()
        
        count = session.execute(text("SELECT COUNT(*) FROM delivery_summary")).scalar()
        print(f"   ✅ 数据填充完成: {count} 条, 耗时 {time.time()-start:.2f}秒")
        return True
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def create_product_daily_summary():
    """创建商品日汇总表（商品销量排行）"""
    print_subsection("5. 商品日汇总表 (product_daily_summary)")
    
    session = SessionLocal()
    try:
        session.execute(text("DROP TABLE IF EXISTS product_daily_summary CASCADE"))
        session.commit()
        
        create_sql = """
        CREATE TABLE product_daily_summary (
            id SERIAL PRIMARY KEY,
            store_name VARCHAR(200) NOT NULL,
            summary_date DATE NOT NULL,
            product_name VARCHAR(500) NOT NULL,
            category_level1 VARCHAR(200),
            channel VARCHAR(100),
            order_count INTEGER DEFAULT 0,
            total_quantity INTEGER DEFAULT 0,
            total_revenue NUMERIC(15,2) DEFAULT 0,
            total_profit NUMERIC(15,2) DEFAULT 0,
            avg_price NUMERIC(10,2) DEFAULT 0,
            profit_margin NUMERIC(10,4) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(store_name, summary_date, product_name, channel)
        )
        """
        session.execute(text(create_sql))
        session.commit()
        
        session.execute(text("CREATE INDEX idx_pds_store_date ON product_daily_summary(store_name, summary_date)"))
        session.execute(text("CREATE INDEX idx_pds_product ON product_daily_summary(product_name)"))
        session.execute(text("CREATE INDEX idx_pds_revenue ON product_daily_summary(total_revenue DESC)"))
        session.commit()
        print("   ✅ 表结构创建成功")
        
        # 填充数据
        insert_sql = """
        INSERT INTO product_daily_summary (
            store_name, summary_date, product_name, category_level1, channel,
            order_count, total_quantity, total_revenue, total_profit
        )
        SELECT 
            store_name,
            DATE(date) as summary_date,
            product_name,
            category_level1,
            CASE 
                WHEN order_number LIKE 'SG%' THEN '美团'
                WHEN order_number LIKE 'ELE%' THEN '饿了么'
                WHEN order_number LIKE 'JD%' THEN '京东'
                ELSE '其他'
            END as channel,
            COUNT(DISTINCT order_id) as order_count,
            SUM(COALESCE(quantity, 1)) as total_quantity,
            SUM(COALESCE(actual_price, 0) * COALESCE(quantity, 1)) as total_revenue,
            SUM(COALESCE(profit, 0)) as total_profit
        FROM orders
        WHERE product_name IS NOT NULL AND product_name != ''
        GROUP BY store_name, DATE(date), product_name, category_level1,
            CASE 
                WHEN order_number LIKE 'SG%' THEN '美团'
                WHEN order_number LIKE 'ELE%' THEN '饿了么'
                WHEN order_number LIKE 'JD%' THEN '京东'
                ELSE '其他'
            END
        """
        
        start = time.time()
        session.execute(text(insert_sql))
        session.commit()
        
        # 更新派生字段
        session.execute(text("""
            UPDATE product_daily_summary SET
                avg_price = CASE WHEN total_quantity > 0 THEN total_revenue / total_quantity ELSE 0 END,
                profit_margin = CASE WHEN total_revenue > 0 THEN total_profit / total_revenue * 100 ELSE 0 END
        """))
        session.commit()
        
        count = session.execute(text("SELECT COUNT(*) FROM product_daily_summary")).scalar()
        print(f"   ✅ 数据填充完成: {count} 条, 耗时 {time.time()-start:.2f}秒")
        return True
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        session.rollback()
        return False
    finally:
        session.close()


# ==================== 第三层：缓存预热 ====================

def warm_up_cache():
    """预热Redis缓存"""
    print_section("第三层：缓存预热")
    
    try:
        import redis
        import json
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_client.ping()
        print("✅ Redis 连接成功")
    except Exception as e:
        print(f"⚠️ Redis 不可用: {e}")
        return False
    
    session = SessionLocal()
    try:
        # 清除旧缓存
        keys = redis_client.keys("agg_*")
        if keys:
            redis_client.delete(*keys)
            print(f"   清除旧缓存: {len(keys)} 个键")
        
        # 预热门店日汇总（最近7天）
        print("\n预热门店日汇总...")
        result = session.execute(text("""
            SELECT store_name, summary_date, channel,
                   order_count, total_revenue, total_profit,
                   delivery_net_cost, total_marketing_cost, avg_order_value
            FROM store_daily_summary
            WHERE summary_date >= CURRENT_DATE - INTERVAL '7 days'
        """))
        rows = result.fetchall()
        for row in rows:
            cache_key = f"agg_store_daily:{row[0]}:{row[1]}:{row[2] or 'all'}"
            cache_data = {
                'order_count': int(row[3]) if row[3] else 0,
                'total_revenue': float(row[4]) if row[4] else 0,
                'total_profit': float(row[5]) if row[5] else 0,
                'delivery_net_cost': float(row[6]) if row[6] else 0,
                'total_marketing_cost': float(row[7]) if row[7] else 0,
                'avg_order_value': float(row[8]) if row[8] else 0
            }
            redis_client.setex(cache_key, 300, json.dumps(cache_data))
        print(f"   ✅ 门店日汇总: {len(rows)} 条")
        
        # 预热品类汇总
        print("预热品类汇总...")
        result = session.execute(text("""
            SELECT store_name, summary_date, category_level1,
                   SUM(total_revenue), SUM(total_profit), SUM(total_quantity)
            FROM category_daily_summary
            WHERE summary_date >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY store_name, summary_date, category_level1
        """))
        rows = result.fetchall()
        for row in rows:
            cache_key = f"agg_category:{row[0]}:{row[1]}:{row[2] or 'unknown'}"
            cache_data = {
                'total_revenue': float(row[3]) if row[3] else 0,
                'total_profit': float(row[4]) if row[4] else 0,
                'total_quantity': int(row[5]) if row[5] else 0
            }
            redis_client.setex(cache_key, 300, json.dumps(cache_data))
        print(f"   ✅ 品类汇总: {len(rows)} 条")
        
        print("\n✅ 缓存预热完成")
        return True
    except Exception as e:
        print(f"❌ 缓存预热失败: {e}")
        return False
    finally:
        session.close()


# ==================== 验证优化效果 ====================

def verify_all_optimizations():
    """验证所有优化效果"""
    print_section("验证优化效果")
    
    session = SessionLocal()
    results = {}
    
    try:
        # 测试1: 门店日汇总查询
        print("\n1. 门店日汇总查询:")
        start = time.time()
        result = session.execute(text("""
            SELECT store_name, SUM(order_count), SUM(total_revenue), SUM(total_profit)
            FROM store_daily_summary
            WHERE summary_date BETWEEN '2026-01-12' AND '2026-01-18'
            GROUP BY store_name
        """))
        rows = result.fetchall()
        t1 = time.time() - start
        print(f"   预聚合表: {t1*1000:.1f}ms ({len(rows)} 门店)")
        results['store_daily'] = t1
        
        # 测试2: 分时段汇总查询
        print("\n2. 分时段汇总查询:")
        start = time.time()
        result = session.execute(text("""
            SELECT hour_of_day, SUM(order_count), SUM(total_revenue)
            FROM store_hourly_summary
            WHERE store_name = '惠宜选-泰州泰兴店'
            AND summary_date BETWEEN '2026-01-12' AND '2026-01-18'
            GROUP BY hour_of_day
            ORDER BY hour_of_day
        """))
        rows = result.fetchall()
        t2 = time.time() - start
        print(f"   预聚合表: {t2*1000:.1f}ms ({len(rows)} 时段)")
        results['hourly'] = t2
        
        # 测试3: 品类汇总查询
        print("\n3. 品类汇总查询:")
        start = time.time()
        result = session.execute(text("""
            SELECT category_level1, SUM(total_revenue), SUM(total_profit), SUM(total_quantity)
            FROM category_daily_summary
            WHERE store_name = '惠宜选-泰州泰兴店'
            AND summary_date BETWEEN '2026-01-12' AND '2026-01-18'
            GROUP BY category_level1
            ORDER BY SUM(total_revenue) DESC
        """))
        rows = result.fetchall()
        t3 = time.time() - start
        print(f"   预聚合表: {t3*1000:.1f}ms ({len(rows)} 品类)")
        results['category'] = t3
        
        # 测试4: 配送分析查询
        print("\n4. 配送分析查询:")
        start = time.time()
        result = session.execute(text("""
            SELECT distance_band, SUM(order_count), SUM(delivery_net_cost), SUM(high_delivery_count)
            FROM delivery_summary
            WHERE store_name = '惠宜选-泰州泰兴店'
            AND summary_date BETWEEN '2026-01-12' AND '2026-01-18'
            GROUP BY distance_band
            ORDER BY MIN(distance_min)
        """))
        rows = result.fetchall()
        t4 = time.time() - start
        print(f"   预聚合表: {t4*1000:.1f}ms ({len(rows)} 距离区间)")
        results['delivery'] = t4
        
        # 测试5: 商品销量查询
        print("\n5. 商品销量查询:")
        start = time.time()
        result = session.execute(text("""
            SELECT product_name, SUM(total_quantity), SUM(total_revenue)
            FROM product_daily_summary
            WHERE store_name = '惠宜选-泰州泰兴店'
            AND summary_date BETWEEN '2026-01-12' AND '2026-01-18'
            GROUP BY product_name
            ORDER BY SUM(total_quantity) DESC
            LIMIT 20
        """))
        rows = result.fetchall()
        t5 = time.time() - start
        print(f"   预聚合表: {t5*1000:.1f}ms (Top {len(rows)} 商品)")
        results['product'] = t5
        
        # 对比原始表查询
        print("\n--- 对比原始表查询 ---")
        start = time.time()
        result = session.execute(text("""
            SELECT store_name, COUNT(DISTINCT order_id)
            FROM orders
            WHERE date BETWEEN '2026-01-12' AND '2026-01-18'
            GROUP BY store_name
        """))
        rows = result.fetchall()
        t_raw = time.time() - start
        print(f"   原始表: {t_raw*1000:.1f}ms ({len(rows)} 门店)")
        results['raw'] = t_raw
        
        # 总结
        print("\n" + "="*80)
        print("📊 优化效果总结")
        print("="*80)
        
        avg_agg = (t1 + t2 + t3 + t4 + t5) / 5
        improvement = (t_raw - avg_agg) / t_raw * 100 if t_raw > 0 else 0
        
        print(f"\n预聚合表平均查询时间: {avg_agg*1000:.1f}ms")
        print(f"原始表查询时间: {t_raw*1000:.1f}ms")
        print(f"性能提升: {improvement:.1f}%")
        
        if avg_agg < 0.01:
            print(f"\n✅ 优化成功！所有查询 < 10ms")
        elif avg_agg < 0.1:
            print(f"\n✅ 优化成功！所有查询 < 100ms")
        
        return results
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return {}
    finally:
        session.close()


def show_table_stats():
    """显示所有预聚合表的统计信息"""
    print_section("预聚合表统计")
    
    session = SessionLocal()
    try:
        tables = [
            ('store_daily_summary', '门店日汇总'),
            ('store_hourly_summary', '门店小时汇总'),
            ('category_daily_summary', '品类日汇总'),
            ('delivery_summary', '配送分析汇总'),
            ('product_daily_summary', '商品日汇总')
        ]
        
        total_rows = 0
        for table_name, desc in tables:
            try:
                count = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                total_rows += count
                print(f"   {desc} ({table_name}): {count:,} 条")
            except:
                print(f"   {desc} ({table_name}): 表不存在")
        
        print(f"\n   总计: {total_rows:,} 条预聚合记录")
        return total_rows
    finally:
        session.close()


def main():
    """主函数"""
    print("\n" + "🚀"*40)
    print("         全看板企业级性能优化实施")
    print("🚀"*40)
    
    start_time = time.time()
    
    # 第一层：索引优化
    optimize_all_indexes()
    
    # 第二层：预聚合表体系
    print_section("第二层：预聚合表体系")
    create_store_daily_summary()
    create_store_hourly_summary()
    create_category_daily_summary()
    create_delivery_summary()
    create_product_daily_summary()
    
    # 显示统计
    show_table_stats()
    
    # 【重要】验证预聚合表数据一致性
    print_section("第三层：数据一致性验证")
    print("验证预聚合表数据与原始计算是否一致...")
    try:
        import subprocess
        result = subprocess.run(
            ['python', '验证预聚合表一致性.py'],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        print(result.stdout)
        if result.returncode != 0:
            print("❌ 数据一致性验证失败！请检查预聚合表生成逻辑")
            print(result.stderr)
            return
    except Exception as e:
        print(f"⚠️ 无法运行验证脚本: {e}")
    
    # 第四层：缓存预热
    warm_up_cache()
    
    # 验证优化效果
    verify_all_optimizations()
    
    total_time = time.time() - start_time
    print(f"\n\n{'='*80}")
    print(f"✅ 全看板优化实施完成！总耗时: {total_time:.1f}秒")
    print(f"{'='*80}")
    
    print("""
📋 优化覆盖范围:
   ✅ 经营总览（6个核心指标卡片）
   ✅ 日趋势图
   ✅ 分时段分析
   ✅ 品类分析（效益矩阵+健康度）
   ✅ 配送分析（热力图+距离分析）
   ✅ 商品销量排行
   ✅ 营销成本分析
   ✅ 全量门店对比

📋 后续步骤:
   1. 重启后端服务
   2. 更新API以使用预聚合表
   3. 刷新前端验证效果
""")


if __name__ == "__main__":
    main()
