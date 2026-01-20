# -*- coding: utf-8 -*-
"""
添加GMV字段到预聚合表

GMV = 实收金额 + 全部折扣（商品原价/交易总额）
全部折扣 = 满减金额 + 商品减免金额 + 商家代金券 + 商家承担部分券 + 满赠金额 + 商家其他优惠 + 新客减免金额 + 配送费减免金额
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import text
import pandas as pd
from datetime import datetime

session = SessionLocal()
try:
    print("=" * 60)
    print("添加GMV字段到预聚合表")
    print("=" * 60)
    
    # 1. 添加GMV列（如果不存在）
    print("\n1. 检查并添加GMV列...")
    try:
        session.execute(text("ALTER TABLE store_daily_summary ADD COLUMN IF NOT EXISTS gmv NUMERIC DEFAULT 0"))
        session.commit()
        print("   ✅ GMV列已添加")
    except Exception as e:
        session.rollback()
        print(f"   ⚠️ 添加GMV列失败: {e}")
    
    # 2. 从原始订单表计算GMV并更新
    print("\n2. 计算并更新GMV数据...")
    
    # 获取所有门店和日期组合
    stores_dates = session.execute(text("""
        SELECT DISTINCT store_name, summary_date, channel 
        FROM store_daily_summary
        ORDER BY store_name, summary_date
    """)).fetchall()
    
    print(f"   需要更新 {len(stores_dates)} 条记录")
    
    updated = 0
    for store_name, summary_date, channel in stores_dates:
        # 从原始订单表计算GMV
        # 先获取该门店该日期该渠道的订单
        
        # 构建渠道筛选条件
        channel_filter = ""
        if channel == '美团':
            channel_filter = "AND order_number LIKE 'SG%'"
        elif channel == '饿了么':
            channel_filter = "AND order_number LIKE 'ELE%'"
        elif channel == '京东':
            channel_filter = "AND order_number LIKE 'JD%'"
        
        # 计算GMV = 实收金额 + 全部折扣
        sql = f"""
            WITH order_data AS (
                SELECT 
                    order_id,
                    SUM(COALESCE(actual_price, 0) * COALESCE(quantity, 1)) as revenue,
                    MAX(COALESCE(full_reduction, 0)) as full_reduction,
                    MAX(COALESCE(product_discount, 0)) as product_discount,
                    MAX(COALESCE(merchant_voucher, 0)) as merchant_voucher,
                    MAX(COALESCE(merchant_share, 0)) as merchant_share,
                    MAX(COALESCE(gift_amount, 0)) as gift_amount,
                    MAX(COALESCE(other_merchant_discount, 0)) as other_discount,
                    MAX(COALESCE(new_customer_discount, 0)) as new_customer_discount,
                    MAX(COALESCE(delivery_discount, 0)) as delivery_discount
                FROM orders
                WHERE store_name = :store_name
                  AND DATE(date) = :summary_date
                  {channel_filter}
                GROUP BY order_id
            )
            SELECT 
                SUM(revenue) as total_revenue,
                SUM(full_reduction + product_discount + merchant_voucher + merchant_share + 
                    gift_amount + other_discount + new_customer_discount + delivery_discount) as total_discount
            FROM order_data
        """
        
        result = session.execute(text(sql), {
            'store_name': store_name,
            'summary_date': summary_date
        }).fetchone()
        
        if result and result[0]:
            total_revenue = float(result[0]) if result[0] else 0
            total_discount = float(result[1]) if result[1] else 0
            gmv = total_revenue + total_discount
            
            # 更新预聚合表
            update_sql = """
                UPDATE store_daily_summary 
                SET gmv = :gmv
                WHERE store_name = :store_name 
                  AND summary_date = :summary_date
                  AND channel = :channel
            """
            session.execute(text(update_sql), {
                'gmv': gmv,
                'store_name': store_name,
                'summary_date': summary_date,
                'channel': channel
            })
            updated += 1
            
            if updated % 100 == 0:
                session.commit()
                print(f"   已更新 {updated} 条...")
    
    session.commit()
    print(f"\n   ✅ 完成！共更新 {updated} 条记录")
    
    # 3. 验证结果
    print("\n3. 验证结果...")
    verify_sql = """
        SELECT store_name, summary_date, channel, total_revenue, gmv,
               CASE WHEN gmv > 0 THEN total_marketing_cost / gmv * 100 ELSE 0 END as marketing_rate
        FROM store_daily_summary
        WHERE store_name = '惠宜选-徐州沛县店'
          AND summary_date >= '2026-01-12'
          AND summary_date <= '2026-01-18'
        ORDER BY summary_date
    """
    results = session.execute(text(verify_sql)).fetchall()
    
    print(f"\n   沛县店 2026-01-12 ~ 2026-01-18 数据:")
    print(f"   {'日期':<12} {'渠道':<8} {'实收':>12} {'GMV':>12} {'营销成本率':>10}")
    print("   " + "-" * 60)
    
    total_revenue = 0
    total_gmv = 0
    total_marketing = 0
    
    for row in results:
        print(f"   {str(row[1]):<12} {row[2] or '全部':<8} ¥{row[3]:>10,.2f} ¥{row[4]:>10,.2f} {row[5]:>8.2f}%")
        total_revenue += float(row[3]) if row[3] else 0
        total_gmv += float(row[4]) if row[4] else 0
    
    # 汇总
    summary_sql = """
        SELECT SUM(total_revenue), SUM(gmv), SUM(total_marketing_cost)
        FROM store_daily_summary
        WHERE store_name = '惠宜选-徐州沛县店'
          AND summary_date >= '2026-01-12'
          AND summary_date <= '2026-01-18'
    """
    summary = session.execute(text(summary_sql)).fetchone()
    
    if summary:
        total_revenue = float(summary[0]) if summary[0] else 0
        total_gmv = float(summary[1]) if summary[1] else 0
        total_marketing = float(summary[2]) if summary[2] else 0
        marketing_rate = (total_marketing / total_gmv * 100) if total_gmv > 0 else 0
        
        print("   " + "-" * 60)
        print(f"   {'汇总':<12} {'':<8} ¥{total_revenue:>10,.2f} ¥{total_gmv:>10,.2f} {marketing_rate:>8.2f}%")
        print(f"\n   ✅ 营销成本率(基于GMV): {marketing_rate:.2f}%")
        print(f"   📊 用户预期: 12.1%")

finally:
    session.close()
