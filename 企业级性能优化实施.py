# -*- coding: utf-8 -*-
"""
企业级性能优化实施脚本

三层优化方案：
1. 数据库层：添加/验证索引
2. 查询层：创建预聚合视图/物化表
3. 缓存层：优化 Redis 缓存策略

执行后自动验证优化效果

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
from sqlalchemy import text, inspect
import pandas as pd


def print_section(title):
    """打印分节标题"""
    print("\n" + "="*80)
    print(f"🔧 {title}")
    print("="*80)


# ==================== 第一层：数据库索引优化 ====================

def optimize_database_indexes():
    """优化数据库索引"""
    print_section("第一层：数据库索引优化")
    
    # 需要创建的索引（PostgreSQL 语法）
    indexes_to_create = [
        # 核心查询索引
        ("idx_perf_store_date", "orders", ["store_name", "date"]),
        ("idx_perf_date", "orders", ["date"]),
        ("idx_perf_order_number", "orders", ["order_number"]),
        # 聚合查询索引
        ("idx_perf_store_channel_date", "orders", ["store_name", "channel", "date"]),
        # 分类查询索引
        ("idx_perf_category_store_date", "orders", ["category_level1", "store_name", "date"]),
    ]
    
    session = SessionLocal()
    try:
        # 检查现有索引
        result = session.execute(text("""
            SELECT indexname FROM pg_indexes WHERE tablename = 'orders'
        """))
        existing_indexes = {row[0] for row in result.fetchall()}
        print(f"\n现有索引: {len(existing_indexes)} 个")
        for idx in sorted(existing_indexes)[:10]:
            print(f"   ✓ {idx}")
        if len(existing_indexes) > 10:
            print(f"   ... 还有 {len(existing_indexes) - 10} 个")
        
        # 创建缺失的索引
        created = 0
        for idx_name, table, columns in indexes_to_create:
            if idx_name not in existing_indexes:
                try:
                    cols = ", ".join(columns)
                    sql = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({cols})"
                    session.execute(text(sql))
                    session.commit()
                    print(f"\n   ✅ 创建索引: {idx_name} ON ({cols})")
                    created += 1
                except Exception as e:
                    print(f"\n   ⚠️ 索引 {idx_name} 创建失败: {e}")
                    session.rollback()
            else:
                print(f"\n   ✓ 索引已存在: {idx_name}")
        
        # 分析表以更新统计信息（PostgreSQL）
        try:
            session.execute(text("ANALYZE orders"))
            session.commit()
            print(f"\n   ✅ 已更新表统计信息 (ANALYZE)")
        except Exception as e:
            print(f"\n   ⚠️ ANALYZE 失败: {e}")
        
        print(f"\n📊 索引优化完成: 新建 {created} 个索引")
        return True
    except Exception as e:
        print(f"\n❌ 索引优化失败: {e}")
        return False
    finally:
        session.close()


# ==================== 第二层：预聚合表优化 ====================

def create_aggregation_tables():
    """创建预聚合表（PostgreSQL 版本）"""
    print_section("第二层：预聚合表优化")
    
    session = SessionLocal()
    try:
        # 创建门店日汇总表（PostgreSQL 语法）
        print("\n1. 创建门店日汇总表 (store_daily_summary)...")
        
        # 删除旧表
        session.execute(text("DROP TABLE IF EXISTS store_daily_summary CASCADE"))
        session.commit()
        
        # 创建新表（PostgreSQL 语法）
        create_table_sql = """
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(store_name, summary_date, channel)
        )
        """
        session.execute(text(create_table_sql))
        session.commit()
        print("   ✅ 表结构创建成功")
        
        # 创建索引
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_summary_store_date ON store_daily_summary(store_name, summary_date)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_summary_date ON store_daily_summary(summary_date)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_summary_channel ON store_daily_summary(channel)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_summary_store_channel ON store_daily_summary(store_name, channel)"))
        session.commit()
        print("   ✅ 索引创建成功")
        
        # 填充数据（PostgreSQL 语法）
        print("\n2. 填充预聚合数据...")
        
        # ✅ 使用订单编号前缀识别渠道（与 Dash 版本一致）
        # SG → 美团, ELE → 饿了么, JD → 京东
        # ⚠️ 重要：先按订单聚合，再按门店+日期+渠道聚合
        # 因为一个订单可能有多个商品行，配送费等字段不能重复计算
        # ⚠️ 营销字段（满减金额等）是订单级别字段，使用MAX而非SUM
        insert_sql = """
        WITH order_level AS (
            -- 第一步：按订单聚合（避免配送费等字段重复计算）
            SELECT 
                store_name,
                DATE(date) as order_date,
                order_id,
                order_number,
                CASE 
                    WHEN order_number LIKE 'SG%' THEN '美团'
                    WHEN order_number LIKE 'ELE%' THEN '饿了么'
                    WHEN order_number LIKE 'JD%' THEN '京东'
                    ELSE '其他'
                END as channel,
                SUM(COALESCE(actual_price, 0) * COALESCE(quantity, 1)) as order_revenue,
                SUM(COALESCE(profit, 0)) as order_profit,
                -- 配送费等字段取MAX（同一订单的所有商品行值相同）
                MAX(COALESCE(delivery_fee, 0)) as order_delivery_fee,
                MAX(COALESCE(user_paid_delivery_fee, 0)) as order_user_paid_delivery,
                MAX(COALESCE(delivery_discount, 0)) as order_delivery_discount,
                MAX(COALESCE(corporate_rebate, 0)) as order_corporate_rebate,
                MAX(COALESCE(platform_service_fee, 0)) as order_platform_fee,
                -- ✅ 营销费用也是订单级别字段，使用MAX（与Dash版本一致）
                MAX(COALESCE(full_reduction, 0)) + 
                MAX(COALESCE(product_discount, 0)) + 
                MAX(COALESCE(merchant_voucher, 0)) + 
                MAX(COALESCE(merchant_share, 0)) + 
                MAX(COALESCE(gift_amount, 0)) + 
                MAX(COALESCE(other_merchant_discount, 0)) + 
                MAX(COALESCE(new_customer_discount, 0)) as order_marketing_cost
            FROM orders
            GROUP BY store_name, DATE(date), order_id, order_number
        )
        -- 第二步：按门店+日期+渠道聚合
        INSERT INTO store_daily_summary (
            store_name, summary_date, channel, order_count, 
            total_revenue, total_profit, total_delivery_fee,
            total_user_paid_delivery, total_delivery_discount,
            total_corporate_rebate, total_marketing_cost, total_platform_fee
        )
        SELECT 
            store_name,
            order_date as summary_date,
            channel,
            COUNT(DISTINCT order_id) as order_count,
            SUM(order_revenue) as total_revenue,
            SUM(order_profit) as total_profit,
            SUM(order_delivery_fee) as total_delivery_fee,
            SUM(order_user_paid_delivery) as total_user_paid_delivery,
            SUM(order_delivery_discount) as total_delivery_discount,
            SUM(order_corporate_rebate) as total_corporate_rebate,
            SUM(order_marketing_cost) as total_marketing_cost,
            SUM(order_platform_fee) as total_platform_fee
        FROM order_level
        GROUP BY store_name, order_date, channel
        """
        
        start = time.time()
        session.execute(text(insert_sql))
        session.commit()
        elapsed = time.time() - start
        
        # 统计结果
        count = session.execute(text("SELECT COUNT(*) FROM store_daily_summary")).scalar()
        print(f"   ✅ 数据填充完成: {count} 条汇总记录, 耗时 {elapsed:.2f}秒")
        
        # 更新派生字段
        print("\n3. 更新派生指标...")
        update_sql = """
        UPDATE store_daily_summary SET
            avg_order_value = CASE WHEN order_count > 0 THEN total_revenue / order_count ELSE 0 END,
            profit_margin = CASE WHEN total_revenue > 0 THEN total_profit / total_revenue * 100 ELSE 0 END,
            delivery_net_cost = total_delivery_fee - total_user_paid_delivery + total_delivery_discount - total_corporate_rebate
        """
        session.execute(text(update_sql))
        session.commit()
        print("   ✅ 派生指标更新完成")
        
        return True
    except Exception as e:
        print(f"\n❌ 预聚合表创建失败: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return False
    finally:
        session.close()


# ==================== 第三层：缓存优化 ====================

def optimize_cache_strategy():
    """优化缓存策略"""
    print_section("第三层：缓存策略优化")
    
    # 检查 Redis 连接
    try:
        import redis
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_client.ping()
        print("\n✅ Redis 连接成功")
        
        # 清除旧缓存
        keys = redis_client.keys("order_data*") + redis_client.keys("store_comparison*")
        if keys:
            redis_client.delete(*keys)
            print(f"   清除旧缓存: {len(keys)} 个键")
        
        # 预热缓存：将预聚合数据加载到 Redis
        print("\n预热缓存...")
        
        session = SessionLocal()
        try:
            # 获取最近7天的汇总数据
            result = session.execute(text("""
                SELECT store_name, summary_date, channel,
                       order_count, total_revenue, total_profit,
                       total_delivery_fee, total_user_paid_delivery,
                       total_delivery_discount, total_corporate_rebate,
                       total_marketing_cost, avg_order_value, profit_margin,
                       delivery_net_cost
                FROM store_daily_summary
                WHERE summary_date >= CURRENT_DATE - INTERVAL '7 days'
            """))
            
            rows = result.fetchall()
            print(f"   加载 {len(rows)} 条汇总记录到 Redis")
            
            # 按门店+日期缓存
            import json
            for row in rows:
                cache_key = f"store_daily:{row[0]}:{row[1]}:{row[2] or 'all'}"
                cache_data = {
                    'order_count': int(row[3]) if row[3] else 0,
                    'total_revenue': float(row[4]) if row[4] else 0,
                    'total_profit': float(row[5]) if row[5] else 0,
                    'total_delivery_fee': float(row[6]) if row[6] else 0,
                    'total_user_paid_delivery': float(row[7]) if row[7] else 0,
                    'total_delivery_discount': float(row[8]) if row[8] else 0,
                    'total_corporate_rebate': float(row[9]) if row[9] else 0,
                    'total_marketing_cost': float(row[10]) if row[10] else 0,
                    'avg_order_value': float(row[11]) if row[11] else 0,
                    'profit_margin': float(row[12]) if row[12] else 0,
                    'delivery_net_cost': float(row[13]) if row[13] else 0
                }
                redis_client.setex(cache_key, 300, json.dumps(cache_data))  # 5分钟过期
            
            print(f"   ✅ 缓存预热完成")
        finally:
            session.close()
        
        return True
    except ImportError:
        print("\n⚠️ Redis 模块未安装，跳过缓存优化")
        return False
    except Exception as e:
        print(f"\n⚠️ Redis 缓存预热失败: {e}")
        print("   缓存优化跳过，系统将使用内存缓存")
        return False


# ==================== 验证优化效果 ====================

def verify_optimization():
    """验证优化效果"""
    print_section("验证优化效果")
    
    session = SessionLocal()
    results = {}
    
    try:
        # 测试1: 使用预聚合表查询
        print("\n1. 预聚合表查询性能:")
        start = time.time()
        result = session.execute(text("""
            SELECT store_name, 
                   SUM(order_count) as orders,
                   SUM(total_revenue) as revenue,
                   SUM(total_profit) as profit,
                   SUM(delivery_net_cost) as delivery_cost,
                   SUM(total_marketing_cost) as marketing_cost
            FROM store_daily_summary
            WHERE summary_date BETWEEN '2026-01-12' AND '2026-01-18'
            GROUP BY store_name
        """))
        rows = result.fetchall()
        agg_time = time.time() - start
        print(f"   预聚合表查询: {agg_time*1000:.1f}ms ({len(rows)} 门店)")
        results['aggregation_query'] = agg_time
        
        # 测试2: 原始表查询（对比）
        print("\n2. 原始表查询性能（对比）:")
        start = time.time()
        result = session.execute(text("""
            SELECT store_name, COUNT(DISTINCT order_id) as orders
            FROM orders
            WHERE date BETWEEN '2026-01-12' AND '2026-01-18'
            GROUP BY store_name
        """))
        rows = result.fetchall()
        raw_time = time.time() - start
        print(f"   原始表查询: {raw_time*1000:.1f}ms ({len(rows)} 门店)")
        results['raw_query'] = raw_time
        
        # 测试3: 索引效果验证
        print("\n3. 索引效果验证:")
        start = time.time()
        result = session.execute(text("""
            SELECT COUNT(*) FROM orders
            WHERE store_name = '惠宜选-泰州泰兴店'
            AND date BETWEEN '2026-01-12' AND '2026-01-18'
        """))
        count = result.scalar()
        index_time = time.time() - start
        print(f"   索引查询: {index_time*1000:.1f}ms ({count} 条)")
        results['index_query'] = index_time
        
        # 计算提升比例
        print("\n" + "="*80)
        print("📊 优化效果总结")
        print("="*80)
        
        if raw_time > 0:
            improvement = (raw_time - agg_time) / raw_time * 100
            print(f"\n预聚合表 vs 原始表: 提升 {improvement:.1f}%")
            print(f"   原始表: {raw_time*1000:.1f}ms")
            print(f"   预聚合: {agg_time*1000:.1f}ms")
        
        if agg_time < 0.1:
            print(f"\n✅ 优化成功！查询时间 < 100ms")
        elif agg_time < 0.5:
            print(f"\n✅ 优化成功！查询时间 < 500ms")
        else:
            print(f"\n⚠️ 查询时间仍较长，可能需要进一步优化")
        
        return results
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        return {}
    finally:
        session.close()


def verify_data_accuracy():
    """验证数据准确性"""
    print_section("验证数据准确性")
    
    session = SessionLocal()
    try:
        # 对比预聚合表和原始计算的结果
        print("\n对比惠宜选-泰州泰兴店 (2026-01-12 ~ 2026-01-18):")
        
        # 从预聚合表获取
        result = session.execute(text("""
            SELECT 
                SUM(order_count) as orders,
                SUM(total_revenue) as revenue,
                SUM(delivery_net_cost) as delivery_cost,
                SUM(total_marketing_cost) as marketing_cost
            FROM store_daily_summary
            WHERE store_name = '惠宜选-泰州泰兴店'
            AND summary_date BETWEEN '2026-01-12' AND '2026-01-18'
        """))
        agg_row = result.fetchone()
        
        print(f"\n预聚合表结果:")
        print(f"   订单数: {agg_row[0]}")
        print(f"   销售额: ¥{float(agg_row[1] or 0):,.2f}")
        print(f"   配送净成本: ¥{float(agg_row[2] or 0):,.2f}")
        print(f"   营销成本: ¥{float(agg_row[3] or 0):,.2f}")
        
        if agg_row[0] and agg_row[0] > 0:
            print(f"   单均配送费: ¥{float(agg_row[2] or 0)/agg_row[0]:.2f}")
            print(f"   单均营销费: ¥{float(agg_row[3] or 0)/agg_row[0]:.2f}")
        
        # 分渠道验证（使用订单编号前缀识别渠道）
        print("\n分渠道验证 (基于订单编号前缀):")
        result = session.execute(text("""
            SELECT 
                channel,
                SUM(order_count) as orders,
                SUM(delivery_net_cost) as delivery_cost,
                SUM(total_marketing_cost) as marketing_cost
            FROM store_daily_summary
            WHERE store_name = '惠宜选-泰州泰兴店'
            AND summary_date BETWEEN '2026-01-12' AND '2026-01-18'
            AND channel IN ('美团', '饿了么', '京东')
            GROUP BY channel
            ORDER BY orders DESC
        """))
        
        for row in result.fetchall():
            channel = row[0] or '未知'
            orders = row[1] or 0
            delivery = float(row[2] or 0)
            marketing = float(row[3] or 0)
            
            if orders > 0:
                print(f"\n   {channel}:")
                print(f"      订单数: {orders}")
                print(f"      单均配送费: ¥{delivery/orders:.2f}")
                print(f"      单均营销费: ¥{marketing/orders:.2f}")
        
        print("\n📋 Dash 版本参考值:")
        print("   美团共橙: 单均配送 ¥3.89, 单均营销 ¥5.19")
        print("   饿了么: 单均配送 ¥1.61, 单均营销 ¥5.58")
        
        return True
    except Exception as e:
        print(f"\n❌ 数据验证失败: {e}")
        return False
    finally:
        session.close()


def main():
    """主函数"""
    print("\n" + "🚀"*40)
    print("         企业级性能优化实施")
    print("🚀"*40)
    
    start_time = time.time()
    
    # 第一层：数据库索引优化
    optimize_database_indexes()
    
    # 第二层：预聚合表优化
    create_aggregation_tables()
    
    # 第三层：缓存优化
    optimize_cache_strategy()
    
    # 验证优化效果
    verify_optimization()
    
    # 验证数据准确性
    verify_data_accuracy()
    
    total_time = time.time() - start_time
    print(f"\n\n{'='*80}")
    print(f"✅ 优化实施完成！总耗时: {total_time:.1f}秒")
    print(f"{'='*80}")
    
    print("""
📋 后续步骤:
1. 重启后端服务以加载新的优化代码
2. 刷新前端页面验证效果
3. 如需进一步优化，可以考虑:
   - 添加定时任务自动更新预聚合表
   - 实现增量更新机制
   - 使用物化视图自动刷新
""")


if __name__ == "__main__":
    main()
