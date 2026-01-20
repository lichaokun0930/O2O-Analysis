# -*- coding: utf-8 -*-
"""
修复预聚合表 - 完全对齐原始计算逻辑

问题：
1. 没有应用渠道过滤逻辑（剔除收费渠道且平台服务费=0的异常订单）
2. 利润计算公式不对：应该是 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
3. 动销商品数计算不对：按订单聚合后再SUM会重复计算

修复方案：
1. 在订单级聚合时应用渠道过滤逻辑
2. 使用正确的利润计算公式
3. 动销商品数按门店+日期去重统计
"""

import sys
from pathlib import Path
import time

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text
from database.connection import SessionLocal

# 收费渠道列表（与老版本一致）
PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购',
    '抖音', '抖音直播', '淘鲜达', '京东秒送',
    '美团咖啡店', '饿了么咖啡店'
]

def fix_store_daily_summary():
    """修复门店日汇总表"""
    print("="*60)
    print("修复 store_daily_summary 预聚合表")
    print("="*60)
    
    session = SessionLocal()
    try:
        # 1. 删除旧表
        print("\n1. 删除旧表...")
        session.execute(text("DROP TABLE IF EXISTS store_daily_summary CASCADE"))
        session.commit()
        print("   ✅ 旧表已删除")
        
        # 2. 创建新表（增加GMV字段）
        print("\n2. 创建新表结构...")
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
        
        # 3. 填充数据（完全对齐原始计算逻辑）
        print("\n3. 填充数据（对齐原始计算逻辑）...")
        
        # 核心修复点：
        # - 应用渠道过滤逻辑：剔除收费渠道且平台服务费=0的异常订单（仅用于订单数、利润等）
        # - 使用正确的利润公式：订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
        # - 动销商品数：按门店+日期去重统计
        # - GMV计算：剔除商品原价<=0的行后计算，但不应用渠道过滤
        
        insert_sql = """
        WITH order_level AS (
            -- 第一步：订单级聚合（商品级字段用SUM，订单级字段用MAX）
            -- 注意：这里不剔除original_price<=0的行，保证订单完整性
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
                -- 营销成本（7字段，不含配送费减免）- 也从这里计算，不受渠道过滤影响
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
            SUM(f.order_actual_profit) as total_profit,  -- 使用正确的利润公式
            SUM(f.order_delivery_fee) as total_delivery_fee,
            SUM(f.order_user_paid_delivery) as total_user_paid_delivery,
            SUM(f.order_delivery_discount) as total_delivery_discount,
            SUM(f.order_corporate_rebate) as total_corporate_rebate,
            COALESCE(g.daily_marketing_cost, 0) as total_marketing_cost,  -- 营销成本从gmv_daily获取（不受渠道过滤影响）
            SUM(f.order_platform_fee) as total_platform_fee,
            COALESCE(dp.active_products, 0) as active_products,
            COALESCE(g.daily_gmv, 0) as gmv  -- GMV从gmv_daily获取（不受渠道过滤影响）
        FROM filtered_orders f
        LEFT JOIN daily_products dp ON f.store_name = dp.store_name AND f.order_date = dp.order_date
        LEFT JOIN gmv_daily g ON f.store_name = g.store_name AND f.order_date = g.order_date AND f.channel = g.channel
        GROUP BY f.store_name, f.order_date, f.channel, dp.active_products, g.daily_gmv, g.daily_marketing_cost
        """
        
        start = time.time()
        session.execute(text(insert_sql))
        session.commit()
        elapsed = time.time() - start
        
        # 4. 更新派生字段
        print("\n4. 更新派生字段...")
        session.execute(text("""
            UPDATE store_daily_summary SET
                avg_order_value = CASE WHEN order_count > 0 THEN total_revenue / order_count ELSE 0 END,
                profit_margin = CASE WHEN total_revenue > 0 THEN total_profit / total_revenue * 100 ELSE 0 END,
                delivery_net_cost = total_delivery_fee - total_user_paid_delivery + total_delivery_discount - total_corporate_rebate
        """))
        session.commit()
        
        # 5. 统计结果
        count = session.execute(text("SELECT COUNT(*) FROM store_daily_summary")).scalar()
        print(f"\n   ✅ 数据填充完成: {count} 条汇总记录, 耗时 {elapsed:.2f}秒")
        
        # 6. 验证数据
        print("\n" + "="*60)
        print("验证修复结果（惠宜选超市昆山淀山湖镇店）")
        print("="*60)
        
        verify_sql = """
        SELECT 
            SUM(order_count) as total_orders,
            SUM(total_revenue) as total_revenue,
            SUM(total_profit) as total_profit,
            SUM(gmv) as total_gmv,
            SUM(total_marketing_cost) as total_marketing_cost
        FROM store_daily_summary
        WHERE store_name = '惠宜选超市（昆山淀山湖镇店）'
        """
        result = session.execute(text(verify_sql)).fetchone()
        
        print(f"\n预聚合表汇总:")
        print(f"  订单总数: {result[0]}")
        print(f"  商品实收额: {result[1]:.2f}")
        print(f"  总利润: {result[2]:.2f}")
        print(f"  GMV: {result[3]:.2f}")
        print(f"  营销成本: {result[4]:.2f}")
        
        # 对比原始计算
        print(f"\n期望值（use_aggregation=false）:")
        print(f"  订单总数: 2813")
        print(f"  商品实收额: 96524.10")
        print(f"  总利润: 13470.53")
        print(f"  GMV: 120860.06")
        print(f"  营销成本: 15949.11")
        
        # 检查差异
        diff_orders = int(result[0]) - 2813
        diff_profit = float(result[2]) - 13470.53
        diff_gmv = float(result[3]) - 120860.06
        diff_marketing = float(result[4]) - 15949.11
        
        print(f"\n差异分析:")
        print(f"  订单数差异: {diff_orders}")
        print(f"  利润差异: {diff_profit:.2f}")
        print(f"  GMV差异: {diff_gmv:.2f}")
        print(f"  营销成本差异: {diff_marketing:.2f}")
        
        if abs(diff_orders) < 5 and abs(diff_profit) < 100:
            print(f"\n✅ 修复成功！数据已对齐")
        else:
            print(f"\n⚠️ 仍有差异，需要进一步检查")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    fix_store_daily_summary()
