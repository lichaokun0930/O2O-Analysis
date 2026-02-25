# -*- coding: utf-8 -*-
"""
预聚合表自动同步服务

当数据发生变更（上传/删除）时，自动增量更新预聚合表，
确保预聚合表与原始数据保持一致。

设计原则：
1. 增量更新：只更新受影响的门店和日期，而不是全量重建
2. 自动触发：数据变更后自动调用，无需手动干预
3. 异步执行：不阻塞主请求，后台完成更新
4. 配置驱动：表列表从配置文件读取，新增表只需添加配置
"""

import sys
from pathlib import Path
from typing import List, Optional, Set
from datetime import date, datetime
from sqlalchemy import text
import threading

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal

# 从配置文件读取预聚合表列表
try:
    from .aggregation_config import get_all_table_names
    AGGREGATION_TABLES = get_all_table_names()
except ImportError:
    # 兼容：如果配置文件不存在，使用硬编码列表
    AGGREGATION_TABLES = [
        'store_daily_summary',
        'store_hourly_summary',
        'category_daily_summary',
        'delivery_summary',
        'product_daily_summary'
    ]


class AggregationSyncService:
    """预聚合表自动同步服务"""
    
    @staticmethod
    def get_table_list() -> List[str]:
        """获取预聚合表列表（从配置读取）"""
        return AGGREGATION_TABLES
    
    @staticmethod
    def sync_store_data(store_names: List[str], async_mode: bool = True):
        """
        同步指定门店的预聚合数据
        
        Args:
            store_names: 需要同步的门店列表
            async_mode: 是否异步执行（默认True，不阻塞主请求）
        """
        if not store_names:
            return
        
        if async_mode:
            # 异步执行，不阻塞主请求
            thread = threading.Thread(
                target=AggregationSyncService._do_sync_store_data,
                args=(store_names,),
                daemon=True
            )
            thread.start()
            print(f"🔄 预聚合表异步更新已启动: {store_names}")
        else:
            # 同步执行
            AggregationSyncService._do_sync_store_data(store_names)
    
    @staticmethod
    def _do_sync_store_data(store_names: List[str]):
        """执行门店数据同步"""
        session = SessionLocal()
        sync_errors = []  # 收集同步错误
        
        try:
            # 0. 先验证并修复表结构
            try:
                from .schema_validator import SchemaValidator
                success, messages = SchemaValidator.validate_and_fix_all()
                for msg in messages:
                    print(f"   {msg}")
                if not success:
                    raise Exception("预聚合表结构验证失败，请检查日志")
            except ImportError:
                pass  # 验证器不存在时跳过
            
            print(f"\n{'='*60}")
            print(f"🔄 开始同步预聚合表: {store_names}")
            print(f"   📋 表列表: {AGGREGATION_TABLES}")
            print(f"{'='*60}")
            
            for store_name in store_names:
                # 1. 删除该门店的旧预聚合数据
                for table in AGGREGATION_TABLES:
                    try:
                        result = session.execute(
                            text(f"DELETE FROM {table} WHERE store_name = :store_name"),
                            {"store_name": store_name}
                        )
                        if result.rowcount > 0:
                            print(f"   🗑️ {table}: 删除 {result.rowcount} 条")
                    except Exception as e:
                        print(f"   ⚠️ {table}: {e}")
                
                session.commit()
            
            # 2. 重新生成这些门店的预聚合数据
            # 使用手写 SQL，同步失败时记录错误
            try:
                AggregationSyncService._rebuild_store_daily_summary(session, store_names)
            except Exception as e:
                sync_errors.append(f"store_daily_summary: {e}")
            
            try:
                AggregationSyncService._rebuild_store_hourly_summary(session, store_names)
            except Exception as e:
                sync_errors.append(f"store_hourly_summary: {e}")
            
            try:
                AggregationSyncService._rebuild_category_daily_summary(session, store_names)
            except Exception as e:
                sync_errors.append(f"category_daily_summary: {e}")
            
            try:
                AggregationSyncService._rebuild_delivery_summary(session, store_names)
            except Exception as e:
                sync_errors.append(f"delivery_summary: {e}")
            
            try:
                AggregationSyncService._rebuild_product_daily_summary(session, store_names)
            except Exception as e:
                sync_errors.append(f"product_daily_summary: {e}")
            
            # 检查是否有同步错误
            if sync_errors:
                print(f"\n❌ 预聚合表同步存在错误:")
                for err in sync_errors:
                    print(f"   - {err}")
                raise Exception(f"预聚合表同步失败: {len(sync_errors)} 个表出错")
            
            print(f"   ✅ 使用手写 SQL 同步")
            
            print(f"\n✅ 预聚合表同步完成: {store_names}")
            
            # 同步完成后，刷新预聚合表可用性状态
            try:
                from .aggregation_service import check_aggregation_tables
                check_aggregation_tables(force=True)
                print("   ✅ 预聚合表可用性状态已刷新")
            except Exception as e:
                print(f"   ⚠️ 刷新可用性状态失败: {e}")
            
            # 清除缓存，确保下次查询获取最新数据
            try:
                AggregationSyncService._clear_all_caches(store_names)
            except Exception as e:
                print(f"   ⚠️ 清除缓存失败: {e}")
            
        except Exception as e:
            print(f"❌ 预聚合表同步失败: {e}")
            session.rollback()
        finally:
            session.close()
    
    @staticmethod
    def _rebuild_store_daily_summary(session, store_names: List[str]):
        """重建门店日汇总表"""
        store_list = "', '".join(store_names)
        
        sql = f"""
        WITH order_level AS (
            SELECT 
                store_name,
                DATE(date) as order_date,
                order_id,
                channel,
                SUM(COALESCE(actual_price, 0) * COALESCE(quantity, 1)) as order_revenue,
                SUM(COALESCE(profit, 0)) as order_profit_raw,
                SUM(COALESCE(platform_service_fee, 0)) as order_platform_fee,
                SUM(COALESCE(corporate_rebate, 0)) as order_corporate_rebate,
                MAX(COALESCE(delivery_fee, 0)) as order_delivery_fee,
                MAX(COALESCE(user_paid_delivery_fee, 0)) as order_user_paid_delivery,
                MAX(COALESCE(delivery_discount, 0)) as order_delivery_discount,
                MAX(COALESCE(full_reduction, 0)) + MAX(COALESCE(product_discount, 0)) + 
                MAX(COALESCE(merchant_voucher, 0)) + MAX(COALESCE(merchant_share, 0)) + 
                MAX(COALESCE(gift_amount, 0)) + MAX(COALESCE(other_merchant_discount, 0)) + 
                MAX(COALESCE(new_customer_discount, 0)) as order_marketing_cost
            FROM orders
            WHERE store_name IN ('{store_list}')
            GROUP BY store_name, DATE(date), order_id, channel
        ),
        gmv_order_level AS (
            SELECT 
                store_name,
                DATE(date) as order_date,
                order_id,
                channel,
                SUM(COALESCE(original_price, 0) * COALESCE(quantity, 1)) as order_original_price_sales,
                MAX(COALESCE(packaging_fee, 0)) as order_packaging_fee,
                MAX(COALESCE(user_paid_delivery_fee, 0)) as order_user_paid_delivery_gmv,
                MAX(COALESCE(full_reduction, 0)) + MAX(COALESCE(product_discount, 0)) + 
                MAX(COALESCE(merchant_voucher, 0)) + MAX(COALESCE(merchant_share, 0)) + 
                MAX(COALESCE(gift_amount, 0)) + MAX(COALESCE(other_merchant_discount, 0)) + 
                MAX(COALESCE(new_customer_discount, 0)) as order_marketing_cost_gmv
            FROM orders
            WHERE store_name IN ('{store_list}') AND original_price > 0
            GROUP BY store_name, DATE(date), order_id, channel
        ),
        gmv_daily AS (
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
            SELECT 
                o.*,
                o.order_profit_raw - o.order_platform_fee - o.order_delivery_fee + o.order_corporate_rebate as order_actual_profit
            FROM order_level o
            WHERE NOT (
                o.channel IN ('饿了么', '京东到家', '美团共橙', '美团闪购', '抖音', '抖音直播', '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店')
                AND o.order_platform_fee <= 0
            )
        ),
        daily_products AS (
            SELECT 
                store_name,
                DATE(date) as order_date,
                COUNT(DISTINCT product_name) as active_products
            FROM orders
            WHERE store_name IN ('{store_list}') AND quantity > 0
            GROUP BY store_name, DATE(date)
        )
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
        
        try:
            session.execute(text(sql))
            
            # 更新派生字段
            session.execute(text(f"""
                UPDATE store_daily_summary SET
                    avg_order_value = CASE WHEN order_count > 0 THEN total_revenue / order_count ELSE 0 END,
                    profit_margin = CASE WHEN total_revenue > 0 THEN total_profit / total_revenue * 100 ELSE 0 END,
                    delivery_net_cost = total_delivery_fee - total_user_paid_delivery + total_delivery_discount - total_corporate_rebate
                WHERE store_name IN ('{store_list}')
            """))
            
            session.commit()
            
            result = session.execute(text(f"SELECT COUNT(*) FROM store_daily_summary WHERE store_name IN ('{store_list}')"))
            count = result.scalar()
            print(f"   ✅ store_daily_summary: {count} 条")
        except Exception as e:
            print(f"   ❌ store_daily_summary: {e}")
            session.rollback()
    
    @staticmethod
    def _rebuild_store_hourly_summary(session, store_names: List[str]):
        """重建门店小时汇总表"""
        store_list = "', '".join(store_names)
        
        sql = f"""
        WITH order_level AS (
            SELECT 
                store_name,
                DATE(date) as order_date,
                EXTRACT(HOUR FROM date)::INTEGER as hour_of_day,
                order_id,
                channel,
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
            WHERE store_name IN ('{store_list}')
            GROUP BY store_name, DATE(date), EXTRACT(HOUR FROM date), order_id, channel
        )
        INSERT INTO store_hourly_summary (
            store_name, summary_date, hour_of_day, channel,
            order_count, total_revenue, total_profit, total_delivery_fee,
            delivery_net_cost, total_marketing_cost
        )
        SELECT 
            store_name, 
            order_date, 
            hour_of_day,
            channel,
            COUNT(DISTINCT order_id) as order_count,
            SUM(order_revenue) as total_revenue,
            SUM(order_profit - order_delivery_fee + order_corporate_rebate) as total_profit,
            SUM(order_delivery_fee) as total_delivery_fee,
            SUM(order_delivery_fee - user_net_delivery - order_corporate_rebate) as delivery_net_cost,
            SUM(order_marketing_cost) as total_marketing_cost
        FROM order_level
        GROUP BY store_name, order_date, hour_of_day, channel
        """
        
        try:
            session.execute(text(sql))
            session.commit()
            
            result = session.execute(text(f"SELECT COUNT(*) FROM store_hourly_summary WHERE store_name IN ('{store_list}')"))
            count = result.scalar()
            print(f"   ✅ store_hourly_summary: {count} 条")
        except Exception as e:
            print(f"   ❌ store_hourly_summary: {e}")
            session.rollback()
    
    @staticmethod
    def _rebuild_category_daily_summary(session, store_names: List[str]):
        """重建品类日汇总表"""
        store_list = "', '".join(store_names)
        
        sql = f"""
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
            channel,
            COUNT(DISTINCT order_id) as order_count,
            COUNT(DISTINCT product_name) as product_count,
            SUM(COALESCE(quantity, 1)) as total_quantity,
            SUM(COALESCE(actual_price, 0) * COALESCE(quantity, 1)) as total_revenue,
            SUM(COALESCE(original_price, 0) * COALESCE(quantity, 1)) as total_original_price,
            SUM(COALESCE(cost, 0) * COALESCE(quantity, 1)) as total_cost,
            SUM(COALESCE(profit, 0)) as total_profit
        FROM orders
        WHERE store_name IN ('{store_list}')
        GROUP BY store_name, DATE(date), category_level1, category_level3, channel
        """
        
        try:
            session.execute(text(sql))
            
            # 更新派生字段
            session.execute(text(f"""
                UPDATE category_daily_summary SET
                    avg_discount = CASE WHEN total_original_price > 0 
                        THEN (1 - total_revenue / total_original_price) * 10 ELSE 0 END,
                    profit_margin = CASE WHEN total_revenue > 0 
                        THEN total_profit / total_revenue * 100 ELSE 0 END
                WHERE store_name IN ('{store_list}')
            """))
            
            session.commit()
            
            result = session.execute(text(f"SELECT COUNT(*) FROM category_daily_summary WHERE store_name IN ('{store_list}')"))
            count = result.scalar()
            print(f"   ✅ category_daily_summary: {count} 条")
        except Exception as e:
            print(f"   ❌ category_daily_summary: {e}")
            session.rollback()
    
    @staticmethod
    def _rebuild_delivery_summary(session, store_names: List[str]):
        """重建配送分析汇总表"""
        store_list = "', '".join(store_names)
        
        sql = f"""
        WITH order_level AS (
            SELECT 
                store_name,
                DATE(date) as order_date,
                EXTRACT(HOUR FROM date)::INTEGER as hour_of_day,
                order_id,
                channel,
                MAX(COALESCE(delivery_distance, 0)) as distance,
                SUM(COALESCE(actual_price, 0) * COALESCE(quantity, 1)) as order_revenue,
                MAX(COALESCE(delivery_fee, 0)) as delivery_fee,
                MAX(COALESCE(user_paid_delivery_fee, 0)) as user_paid,
                MAX(COALESCE(delivery_discount, 0)) as discount,
                MAX(COALESCE(corporate_rebate, 0)) as rebate
            FROM orders
            WHERE store_name IN ('{store_list}')
            GROUP BY store_name, DATE(date), EXTRACT(HOUR FROM date), order_id, channel
        )
        INSERT INTO delivery_summary (
            store_name, summary_date, hour_of_day, distance_band, channel,
            order_count, total_revenue, delivery_net_cost, high_delivery_count
        )
        SELECT 
            store_name,
            order_date,
            hour_of_day,
            CASE 
                WHEN distance < 1 THEN '0-1km'
                WHEN distance < 2 THEN '1-2km'
                WHEN distance < 3 THEN '2-3km'
                WHEN distance < 4 THEN '3-4km'
                WHEN distance < 5 THEN '4-5km'
                ELSE '5km+'
            END as distance_band,
            channel,
            COUNT(DISTINCT order_id) as order_count,
            SUM(order_revenue) as total_revenue,
            SUM(delivery_fee - user_paid + discount - rebate) as delivery_net_cost,
            SUM(CASE WHEN (delivery_fee - user_paid + discount - rebate) > 5 THEN 1 ELSE 0 END) as high_delivery_count
        FROM order_level
        GROUP BY store_name, order_date, hour_of_day, 
            CASE 
                WHEN distance < 1 THEN '0-1km'
                WHEN distance < 2 THEN '1-2km'
                WHEN distance < 3 THEN '2-3km'
                WHEN distance < 4 THEN '3-4km'
                WHEN distance < 5 THEN '4-5km'
                ELSE '5km+'
            END,
            channel
        """
        
        try:
            session.execute(text(sql))
            
            # 更新派生字段
            session.execute(text(f"""
                UPDATE delivery_summary SET
                    avg_delivery_fee = CASE WHEN order_count > 0 THEN delivery_net_cost / order_count ELSE 0 END,
                    distance_min = CASE distance_band
                        WHEN '0-1km' THEN 0 WHEN '1-2km' THEN 1 WHEN '2-3km' THEN 2
                        WHEN '3-4km' THEN 3 WHEN '4-5km' THEN 4 ELSE 5 END,
                    distance_max = CASE distance_band
                        WHEN '0-1km' THEN 1 WHEN '1-2km' THEN 2 WHEN '2-3km' THEN 3
                        WHEN '3-4km' THEN 4 WHEN '4-5km' THEN 5 ELSE 10 END
                WHERE store_name IN ('{store_list}')
            """))
            
            session.commit()
            
            result = session.execute(text(f"SELECT COUNT(*) FROM delivery_summary WHERE store_name IN ('{store_list}')"))
            count = result.scalar()
            print(f"   ✅ delivery_summary: {count} 条")
        except Exception as e:
            print(f"   ❌ delivery_summary: {e}")
            session.rollback()
    
    @staticmethod
    def _rebuild_product_daily_summary(session, store_names: List[str]):
        """重建商品日汇总表"""
        store_list = "', '".join(store_names)
        
        sql = f"""
        INSERT INTO product_daily_summary (
            store_name, summary_date, product_name, category_level1, channel,
            order_count, total_quantity, total_revenue, total_cost, total_profit
        )
        SELECT 
            store_name,
            DATE(date) as summary_date,
            product_name,
            category_level1,
            channel,
            COUNT(DISTINCT order_id) as order_count,
            SUM(COALESCE(quantity, 1)) as total_quantity,
            SUM(COALESCE(actual_price, 0) * COALESCE(quantity, 1)) as total_revenue,
            SUM(COALESCE(cost, 0) * COALESCE(quantity, 1)) as total_cost,
            SUM(COALESCE(profit, 0)) as total_profit
        FROM orders
        WHERE store_name IN ('{store_list}')
        GROUP BY store_name, DATE(date), product_name, category_level1, channel
        """
        
        try:
            session.execute(text(sql))
            
            # 更新派生字段
            session.execute(text(f"""
                UPDATE product_daily_summary SET
                    avg_price = CASE WHEN total_quantity > 0 THEN total_revenue / total_quantity ELSE 0 END,
                    profit_margin = CASE WHEN total_revenue > 0 THEN total_profit / total_revenue * 100 ELSE 0 END
                WHERE store_name IN ('{store_list}')
            """))
            
            session.commit()
            
            result = session.execute(text(f"SELECT COUNT(*) FROM product_daily_summary WHERE store_name IN ('{store_list}')"))
            count = result.scalar()
            print(f"   ✅ product_daily_summary: {count} 条")
        except Exception as e:
            print(f"   ❌ product_daily_summary: {e}")
            session.rollback()


    @staticmethod
    def _clear_all_caches(store_names: List[str]):
        """
        清除所有相关缓存
        
        包括：
        1. Redis 缓存（使用 FLUSHDB 清除当前数据库所有键）
        2. 内存缓存（如果有）
        
        设计原则：
        - 数据变更后清除所有缓存，确保不会遗漏
        - 新增功能无需手动添加缓存键模式
        """
        print(f"   🧹 开始清除缓存...")
        
        # 1. 清除 Redis 缓存（清除当前数据库所有键）
        try:
            import redis
            from app.config import settings
            
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            
            # 方案1：清除所有键（最彻底，推荐）
            # 使用 FLUSHDB 清除当前数据库，新增功能无需手动添加模式
            keys_before = redis_client.dbsize()
            if keys_before > 0:
                redis_client.flushdb()
                print(f"      ✅ Redis 缓存已清除: {keys_before} 个键 (FLUSHDB)")
            else:
                print(f"      ℹ️ Redis 无缓存需要清除")
                
        except ImportError:
            print(f"      ⚠️ Redis 未安装，跳过 Redis 缓存清除")
        except Exception as e:
            print(f"      ⚠️ Redis 缓存清除失败: {e}")
        
        # 2. 清除内存缓存（通过调用 cache_service）
        try:
            from .cache_service import cache_service
            
            # 清除所有内存缓存
            cache_service.clear_all()
            print(f"      ✅ 内存缓存已清除")
        except ImportError:
            # cache_service 可能不存在
            pass
        except Exception as e:
            print(f"      ⚠️ 内存缓存清除失败: {e}")
        
        # 3. 通知查询路由服务重新初始化
        try:
            from .query_router_service import query_router_service
            query_router_service.initialize()
            print(f"      ✅ 查询路由服务已重新初始化")
        except Exception as e:
            print(f"      ⚠️ 查询路由服务重新初始化失败: {e}")


# 创建单例实例
aggregation_sync_service = AggregationSyncService()
