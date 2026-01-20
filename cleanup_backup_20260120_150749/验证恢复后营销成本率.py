# -*- coding: utf-8 -*-
"""
验证恢复原始逻辑后的营销成本率计算
用户期望: 沛县店 2026-01-12 ~ 2026-01-18 营销成本率 = 12.1%
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import SessionLocal
from database.models import Order
from sqlalchemy import and_
from datetime import datetime
import pandas as pd

def verify_marketing_cost_rate():
    """验证营销成本率计算"""
    session = SessionLocal()
    
    try:
        # 查询沛县店数据
        start_date = datetime(2026, 1, 12)
        end_date = datetime(2026, 1, 18, 23, 59, 59)
        
        orders = session.query(Order).filter(
            and_(
                Order.store_name == '惠宜选-徐州沛县店',
                Order.date >= start_date,
                Order.date <= end_date
            )
        ).all()
        
        print(f"=" * 60)
        print(f"沛县店 2026-01-12 ~ 2026-01-18 营销成本率验证")
        print(f"=" * 60)
        print(f"订单数: {len(orders)}")
        
        # 计算各项指标
        total_revenue = 0  # 实收金额
        total_marketing_cost = 0  # 营销成本（7字段）
        
        # 7个营销字段
        marketing_fields = {
            '满减金额': 0,
            '商品减免金额': 0,
            '商家代金券': 0,
            '商家承担部分券': 0,
            '满赠金额': 0,
            '商家其他优惠': 0,
            '新客减免金额': 0
        }
        
        for order in orders:
            total_revenue += float(order.actual_price or 0)
            
            # 累加7个营销字段
            marketing_fields['满减金额'] += float(order.full_reduction or 0)
            marketing_fields['商品减免金额'] += float(order.product_discount or 0)
            marketing_fields['商家代金券'] += float(order.merchant_voucher or 0)
            marketing_fields['商家承担部分券'] += float(order.merchant_share or 0)
            marketing_fields['满赠金额'] += float(order.gift_amount or 0)
            marketing_fields['商家其他优惠'] += float(order.other_merchant_discount or 0)
            marketing_fields['新客减免金额'] += float(order.new_customer_discount or 0)
        
        # 计算总营销成本
        total_marketing_cost = sum(marketing_fields.values())
        
        # 计算营销成本率
        marketing_cost_rate = (total_marketing_cost / total_revenue * 100) if total_revenue > 0 else 0
        
        print(f"\n📊 计算结果:")
        print(f"  实收金额(total_revenue): ¥{total_revenue:,.2f}")
        print(f"  营销成本(7字段合计): ¥{total_marketing_cost:,.2f}")
        print(f"  营销成本率: {marketing_cost_rate:.2f}%")
        
        print(f"\n📋 营销成本明细(7字段):")
        for field, value in marketing_fields.items():
            print(f"  {field}: ¥{value:,.2f}")
        
        print(f"\n🎯 用户期望: 12.1%")
        print(f"📊 实际计算: {marketing_cost_rate:.2f}%")
        
        if abs(marketing_cost_rate - 12.1) < 0.5:
            print(f"✅ 计算结果与用户期望接近!")
        else:
            print(f"⚠️ 计算结果与用户期望有差异，需要进一步分析")
            
            # 分析可能的原因
            print(f"\n🔍 差异分析:")
            
            # 检查是否需要按订单聚合
            print(f"\n  尝试按订单聚合后计算...")
            
            # 转换为DataFrame进行订单级聚合
            data = []
            for order in orders:
                data.append({
                    '订单ID': order.order_id,
                    '实收价格': float(order.actual_price or 0),
                    '满减金额': float(order.full_reduction or 0),
                    '商品减免金额': float(order.product_discount or 0),
                    '商家代金券': float(order.merchant_voucher or 0),
                    '商家承担部分券': float(order.merchant_share or 0),
                    '满赠金额': float(order.gift_amount or 0),
                    '商家其他优惠': float(order.other_merchant_discount or 0),
                    '新客减免金额': float(order.new_customer_discount or 0),
                })
            
            df = pd.DataFrame(data)
            
            # 订单级聚合
            order_agg = df.groupby('订单ID').agg({
                '实收价格': 'sum',
                '满减金额': 'first',  # 订单级字段用first
                '商品减免金额': 'first',
                '商家代金券': 'first',
                '商家承担部分券': 'first',
                '满赠金额': 'first',
                '商家其他优惠': 'first',
                '新客减免金额': 'first',
            }).reset_index()
            
            # 计算营销成本
            order_agg['营销成本'] = (
                order_agg['满减金额'] + 
                order_agg['商品减免金额'] + 
                order_agg['商家代金券'] + 
                order_agg['商家承担部分券'] + 
                order_agg['满赠金额'] + 
                order_agg['商家其他优惠'] + 
                order_agg['新客减免金额']
            )
            
            agg_revenue = order_agg['实收价格'].sum()
            agg_marketing = order_agg['营销成本'].sum()
            agg_rate = (agg_marketing / agg_revenue * 100) if agg_revenue > 0 else 0
            
            print(f"  订单数(聚合后): {len(order_agg)}")
            print(f"  实收金额(聚合后): ¥{agg_revenue:,.2f}")
            print(f"  营销成本(聚合后): ¥{agg_marketing:,.2f}")
            print(f"  营销成本率(聚合后): {agg_rate:.2f}%")
        
    finally:
        session.close()

if __name__ == "__main__":
    verify_marketing_cost_rate()
