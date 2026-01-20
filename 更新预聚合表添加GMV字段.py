# -*- coding: utf-8 -*-
"""
更新预聚合表添加GMV字段

GMV计算公式：
GMV = Σ(商品原价 × 销量) + Σ(打包袋金额) + Σ(用户支付配送费)

数据清洗规则：
- 剔除商品原价 <= 0 的整行数据

营销成本率 = 营销成本(7字段) / GMV × 100%
"""

import time
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from database.connection import SessionLocal
from sqlalchemy import text


def add_gmv_columns():
    """添加GMV相关字段到store_daily_summary表"""
    print("=" * 60)
    print("步骤1: 添加GMV相关字段")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        # 检查并添加所有需要的字段
        fields_to_add = [
            ('gmv', 'NUMERIC(15,2)', '0'),
            ('gmv_original_price_sales', 'NUMERIC(15,2)', '0'),
            ('gmv_packaging_fee', 'NUMERIC(15,2)', '0'),
            ('gmv_user_delivery_fee', 'NUMERIC(15,2)', '0'),
            ('marketing_cost_rate', 'NUMERIC(10,4)', '0'),
        ]
        
        for field_name, field_type, default_val in fields_to_add:
            # 检查字段是否存在
            result = session.execute(text(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'store_daily_summary' AND column_name = '{field_name}'
            """))
            if result.fetchone():
                print(f"  ✓ {field_name} 字段已存在")
            else:
                # 添加字段
                session.execute(text(f"""
                    ALTER TABLE store_daily_summary 
                    ADD COLUMN {field_name} {field_type} DEFAULT {default_val}
                """))
                session.commit()
                print(f"  ✅ {field_name} 字段添加成功")
        
        print("✅ 所有GMV字段检查完成")
        return True
    except Exception as e:
        print(f"❌ 添加字段失败: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def update_gmv_data():
    """更新GMV数据（使用正确的计算逻辑）"""
    print("\n" + "=" * 60)
    print("步骤2: 计算并更新GMV数据")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        start = time.time()
        
        # 使用CTE计算GMV（剔除商品原价<=0的行）
        # 注意：这个SQL需要从原始订单表重新计算
        update_sql = """
        WITH gmv_calc AS (
            SELECT 
                store_name,
                DATE(date) as summary_date,
                CASE 
                    WHEN order_number LIKE 'SG%%' THEN '美团'
                    WHEN order_number LIKE 'ELE%%' THEN '饿了么'
                    WHEN order_number LIKE 'JD%%' THEN '京东'
                    ELSE '其他'
                END as channel,
                -- 商品原价销售额（只计算原价>0的行）
                SUM(CASE WHEN COALESCE(original_price, 0) > 0 
                    THEN COALESCE(original_price, 0) * COALESCE(quantity, 1) 
                    ELSE 0 END) as original_price_sales,
                -- 打包袋金额（订单级，需要去重）
                -- 只计算有效订单（至少有一个商品原价>0）
                0 as packaging_fee_placeholder,
                -- 用户支付配送费（订单级，需要去重）
                0 as user_delivery_fee_placeholder
            FROM orders
            GROUP BY store_name, DATE(date), 
                CASE 
                    WHEN order_number LIKE 'SG%%' THEN '美团'
                    WHEN order_number LIKE 'ELE%%' THEN '饿了么'
                    WHEN order_number LIKE 'JD%%' THEN '京东'
                    ELSE '其他'
                END
        ),
        -- 订单级字段需要单独计算（只计算有效订单）
        order_level_gmv AS (
            SELECT 
                store_name,
                DATE(date) as summary_date,
                CASE 
                    WHEN order_number LIKE 'SG%%' THEN '美团'
                    WHEN order_number LIKE 'ELE%%' THEN '饿了么'
                    WHEN order_number LIKE 'JD%%' THEN '京东'
                    ELSE '其他'
                END as channel,
                order_id,
                -- 检查该订单是否有有效商品（原价>0）
                MAX(CASE WHEN COALESCE(original_price, 0) > 0 THEN 1 ELSE 0 END) as has_valid_product,
                MAX(COALESCE(packaging_fee, 0)) as packaging_fee,
                MAX(COALESCE(user_paid_delivery_fee, 0)) as user_delivery_fee
            FROM orders
            GROUP BY store_name, DATE(date), order_id, order_number
        ),
        order_level_agg AS (
            SELECT 
                store_name,
                summary_date,
                channel,
                SUM(CASE WHEN has_valid_product = 1 THEN packaging_fee ELSE 0 END) as total_packaging_fee,
                SUM(CASE WHEN has_valid_product = 1 THEN user_delivery_fee ELSE 0 END) as total_user_delivery_fee
            FROM order_level_gmv
            GROUP BY store_name, summary_date, channel
        ),
        final_gmv AS (
            SELECT 
                g.store_name,
                g.summary_date,
                g.channel,
                g.original_price_sales,
                COALESCE(o.total_packaging_fee, 0) as packaging_fee,
                COALESCE(o.total_user_delivery_fee, 0) as user_delivery_fee,
                g.original_price_sales + COALESCE(o.total_packaging_fee, 0) + COALESCE(o.total_user_delivery_fee, 0) as gmv
            FROM gmv_calc g
            LEFT JOIN order_level_agg o 
                ON g.store_name = o.store_name 
                AND g.summary_date = o.summary_date 
                AND g.channel = o.channel
        )
        UPDATE store_daily_summary s
        SET 
            gmv = f.gmv,
            gmv_original_price_sales = f.original_price_sales,
            gmv_packaging_fee = f.packaging_fee,
            gmv_user_delivery_fee = f.user_delivery_fee,
            marketing_cost_rate = CASE WHEN f.gmv > 0 THEN s.total_marketing_cost / f.gmv * 100 ELSE 0 END
        FROM final_gmv f
        WHERE s.store_name = f.store_name 
            AND s.summary_date = f.summary_date 
            AND COALESCE(s.channel, '其他') = f.channel
        """
        
        session.execute(text(update_sql))
        session.commit()
        
        elapsed = time.time() - start
        print(f"✅ GMV数据更新完成，耗时 {elapsed:.2f}秒")
        
        return True
    except Exception as e:
        print(f"❌ 更新GMV数据失败: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def verify_gmv_calculation():
    """验证GMV计算结果"""
    print("\n" + "=" * 60)
    print("步骤3: 验证GMV计算结果")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        # 验证惠宜选超市昆山淀山湖镇店 2026-01-18 的数据
        result = session.execute(text("""
            SELECT 
                store_name,
                summary_date,
                channel,
                gmv,
                gmv_original_price_sales,
                gmv_packaging_fee,
                gmv_user_delivery_fee,
                total_marketing_cost,
                marketing_cost_rate
            FROM store_daily_summary
            WHERE store_name LIKE '%%昆山淀山湖%%'
            AND summary_date = '2026-01-18'
        """))
        
        rows = result.fetchall()
        if rows:
            print("\n惠宜选超市昆山淀山湖镇店 2026-01-18 数据:")
            print("-" * 60)
            
            total_gmv = 0
            total_marketing = 0
            
            for row in rows:
                print(f"渠道: {row[2]}")
                print(f"  GMV: ¥{row[3]:,.2f}")
                print(f"    - 商品原价销售额: ¥{row[4]:,.2f}")
                print(f"    - 打包袋金额: ¥{row[5]:,.2f}")
                print(f"    - 用户支付配送费: ¥{row[6]:,.2f}")
                print(f"  营销成本: ¥{row[7]:,.2f}")
                print(f"  营销成本率: {row[8]:.2f}%")
                print()
                
                total_gmv += float(row[3]) if row[3] else 0
                total_marketing += float(row[7]) if row[7] else 0
            
            print("-" * 60)
            print(f"合计 GMV: ¥{total_gmv:,.2f}")
            print(f"合计营销成本: ¥{total_marketing:,.2f}")
            print(f"合计营销成本率: {total_marketing/total_gmv*100:.2f}%" if total_gmv > 0 else "N/A")
            
            # 与预期值对比
            print("\n" + "-" * 60)
            print("与预期值对比:")
            print(f"  预期GMV: ¥8,440.66")
            print(f"  实际GMV: ¥{total_gmv:,.2f}")
            print(f"  差异: ¥{total_gmv - 8440.66:,.2f}")
            
            if abs(total_gmv - 8440.66) < 1:
                print("\n✅ GMV计算正确！")
            else:
                print("\n⚠️ GMV计算有差异，请检查")
        else:
            print("⚠️ 未找到测试数据")
        
        return True
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        session.close()


def main():
    """主函数"""
    print("=" * 60)
    print("更新预聚合表添加GMV字段")
    print("=" * 60)
    
    # 步骤1: 添加字段
    if not add_gmv_columns():
        return
    
    # 步骤2: 更新数据
    if not update_gmv_data():
        return
    
    # 步骤3: 验证结果
    verify_gmv_calculation()
    
    print("\n" + "=" * 60)
    print("✅ 预聚合表GMV字段更新完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
