# -*- coding: utf-8 -*-
"""
验证沛县店营销成本率计算

用户预期：2025-01-12 ~ 2025-01-18，营销成本率约 12.1%
需要验证：
1. API返回的营销成本率是多少
2. 原始数据计算的营销成本率是多少
3. 差异原因分析
"""

import requests
import pandas as pd
from datetime import date
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import and_

API_BASE = "http://localhost:8080/api/v1"
STORE_NAME = "惠宜选-徐州沛县店"

def test_api_response():
    """测试API返回的营销成本率"""
    print("=" * 60)
    print("1. 测试API返回值")
    print("=" * 60)
    
    params = {
        "start_date": "2026-01-12",
        "end_date": "2026-01-18",
        "sort_by": "revenue",
        "sort_order": "desc"
    }
    
    try:
        res = requests.get(f"{API_BASE}/store-comparison/comparison", params=params)
        data = res.json()
        
        if data.get("success") and data.get("data", {}).get("stores"):
            stores = data["data"]["stores"]
            
            # 查找沛县店
            peixian_store = None
            for store in stores:
                if store["store_name"] == STORE_NAME:
                    peixian_store = store
                    break
            
            if peixian_store:
                print(f"\n门店名称: {peixian_store['store_name']}")
                print(f"订单数: {peixian_store['order_count']}")
                print(f"销售额: ¥{peixian_store['total_revenue']:,.2f}")
                print(f"总利润: ¥{peixian_store['total_profit']:,.2f}")
                print(f"利润率: {peixian_store['profit_margin']:.2f}%")
                print(f"总营销成本: ¥{peixian_store.get('total_marketing_cost', 'N/A')}")
                print(f"单均营销费: ¥{peixian_store['avg_marketing_cost']:.2f}")
                print(f"营销成本率: {peixian_store['marketing_cost_rate']:.2f}%")
                print(f"配送成本率: {peixian_store['delivery_cost_rate']:.2f}%")
                
                return peixian_store
            else:
                print("❌ 未找到沛县店")
                print("可用门店:", [s["store_name"] for s in stores[:5]])
        else:
            print("❌ API返回失败:", data)
    except Exception as e:
        print(f"❌ API请求失败: {e}")
    
    return None


def calculate_from_raw_data():
    """从原始数据计算营销成本率"""
    print("\n" + "=" * 60)
    print("2. 从原始数据计算")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        # 查询沛县店数据
        from datetime import datetime
        start_date = datetime(2026, 1, 12)
        end_date = datetime(2026, 1, 18, 23, 59, 59)
        
        orders = session.query(Order).filter(
            and_(
                Order.store_name == STORE_NAME,
                Order.date >= start_date,
                Order.date <= end_date
            )
        ).all()
        
        if not orders:
            print("❌ 未找到沛县店数据")
            return None
        
        print(f"\n门店名称: {orders[0].store_name}")
        print(f"原始记录数: {len(orders)}")
        
        # 转换为DataFrame
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '实收价格': float(order.actual_price or 0),
                '月售': order.quantity if order.quantity is not None else 1,
                '满减金额': float(order.full_reduction or 0),
                '商品减免金额': float(order.product_discount or 0),
                '商家代金券': float(order.merchant_voucher or 0),
                '商家承担部分券': float(order.merchant_share or 0),
                '满赠金额': float(order.gift_amount or 0),
                '商家其他优惠': float(order.other_merchant_discount or 0),
                '新客减免金额': float(order.new_customer_discount or 0),
                '配送费减免金额': float(order.delivery_discount or 0),
            })
        
        df = pd.DataFrame(data)
        
        # 计算订单总收入
        df['订单总收入'] = df['实收价格'] * df['月售']
        
        # 按订单聚合
        order_agg = df.groupby('订单ID').agg({
            '订单总收入': 'sum',
            '满减金额': 'first',
            '商品减免金额': 'first',
            '商家代金券': 'first',
            '商家承担部分券': 'first',
            '满赠金额': 'first',
            '商家其他优惠': 'first',
            '新客减免金额': 'first',
            '配送费减免金额': 'first',
        }).reset_index()
        
        # 计算营销成本（7字段，不含配送费减免）
        marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', 
                          '满赠金额', '商家其他优惠', '新客减免金额']
        order_agg['营销成本'] = sum(order_agg[f].fillna(0) for f in marketing_fields)
        
        # 计算营销成本（8字段，含配送费减免）
        marketing_fields_8 = marketing_fields + ['配送费减免金额']
        order_agg['营销成本_含配送减免'] = sum(order_agg[f].fillna(0) for f in marketing_fields_8)
        
        # 汇总
        total_orders = len(order_agg)
        total_revenue = order_agg['订单总收入'].sum()
        total_marketing_7 = order_agg['营销成本'].sum()
        total_marketing_8 = order_agg['营销成本_含配送减免'].sum()
        
        marketing_rate_7 = (total_marketing_7 / total_revenue * 100) if total_revenue > 0 else 0
        marketing_rate_8 = (total_marketing_8 / total_revenue * 100) if total_revenue > 0 else 0
        
        print(f"\n订单数: {total_orders}")
        print(f"销售额: ¥{total_revenue:,.2f}")
        print(f"\n--- 营销成本计算 ---")
        print(f"7字段营销成本: ¥{total_marketing_7:,.2f}")
        print(f"7字段营销成本率: {marketing_rate_7:.2f}%")
        print(f"\n8字段营销成本(含配送减免): ¥{total_marketing_8:,.2f}")
        print(f"8字段营销成本率: {marketing_rate_8:.2f}%")
        
        # 各字段明细
        print(f"\n--- 各字段明细 ---")
        for field in marketing_fields_8:
            total = order_agg[field].sum()
            print(f"{field}: ¥{total:,.2f}")
        
        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "marketing_cost_7": total_marketing_7,
            "marketing_rate_7": marketing_rate_7,
            "marketing_cost_8": total_marketing_8,
            "marketing_rate_8": marketing_rate_8,
        }
        
    finally:
        session.close()


def check_aggregation_table():
    """检查预聚合表中的数据"""
    print("\n" + "=" * 60)
    print("3. 检查预聚合表数据")
    print("=" * 60)
    
    session = SessionLocal()
    try:
        from sqlalchemy import text
        
        sql = f"""
            SELECT 
                store_name,
                SUM(order_count) as order_count,
                SUM(total_revenue) as total_revenue,
                SUM(total_marketing_cost) as total_marketing_cost
            FROM store_daily_summary
            WHERE store_name = '{STORE_NAME}'
              AND summary_date >= '2026-01-12'
              AND summary_date <= '2026-01-18'
            GROUP BY store_name
        """
        
        result = session.execute(text(sql))
        row = result.fetchone()
        
        if row:
            store_name, order_count, total_revenue, total_marketing_cost = row
            marketing_rate = (total_marketing_cost / total_revenue * 100) if total_revenue > 0 else 0
            
            print(f"\n门店名称: {store_name}")
            print(f"订单数: {order_count}")
            print(f"销售额: ¥{total_revenue:,.2f}")
            print(f"营销成本: ¥{total_marketing_cost:,.2f}")
            print(f"营销成本率: {marketing_rate:.2f}%")
            
            return {
                "order_count": order_count,
                "total_revenue": total_revenue,
                "total_marketing_cost": total_marketing_cost,
                "marketing_rate": marketing_rate
            }
        else:
            print("❌ 预聚合表中未找到沛县店数据")
            
    except Exception as e:
        print(f"❌ 查询预聚合表失败: {e}")
    finally:
        session.close()
    
    return None


if __name__ == "__main__":
    print("验证沛县店营销成本率")
    print("日期范围: 2026-01-12 ~ 2026-01-18")
    print("用户预期: 约 12.1%")
    print()
    
    # 1. API返回值
    api_result = test_api_response()
    
    # 2. 原始数据计算
    raw_result = calculate_from_raw_data()
    
    # 3. 预聚合表数据
    agg_result = check_aggregation_table()
    
    # 4. 对比分析
    print("\n" + "=" * 60)
    print("4. 对比分析")
    print("=" * 60)
    
    print("\n| 来源 | 营销成本率 |")
    print("|------|-----------|")
    print(f"| 用户预期 | 12.1% |")
    if api_result:
        print(f"| API返回 | {api_result['marketing_cost_rate']:.2f}% |")
    if raw_result:
        print(f"| 原始数据(7字段) | {raw_result['marketing_rate_7']:.2f}% |")
        print(f"| 原始数据(8字段) | {raw_result['marketing_rate_8']:.2f}% |")
    if agg_result:
        print(f"| 预聚合表 | {agg_result['marketing_rate']:.2f}% |")
