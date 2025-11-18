#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""分析数据库platform_service_fee的真实问题"""

from database.connection import get_db_context
from database.models import Order
from sqlalchemy import func

def main():
    print(f"\n{'='*70}")
    print("🔍 深度分析数据库 platform_service_fee 问题")
    print(f"{'='*70}\n")
    
    with get_db_context() as session:
        # 1. 查看所有store_name
        print("1️⃣ 数据库中的 store_name 列表:")
        stores = session.query(Order.store_name, func.count(Order.id)).group_by(Order.store_name).all()
        for store_name, count in stores:
            print(f"   - {store_name}: {count} 笔订单")
        
        # 2. 统计platform_service_fee
        print(f"\n2️⃣ platform_service_fee 分布:")
        total = session.query(func.count(Order.id)).scalar()
        zero_fee = session.query(func.count(Order.id)).filter(Order.platform_service_fee == 0).scalar()
        non_zero_fee = session.query(func.count(Order.id)).filter(Order.platform_service_fee > 0).scalar()
        null_fee = session.query(func.count(Order.id)).filter(Order.platform_service_fee.is_(None)).scalar()
        
        print(f"   总订单数: {total}")
        print(f"   平台服务费 = 0: {zero_fee} ({zero_fee/total*100:.1f}%)")
        print(f"   平台服务费 > 0: {non_zero_fee} ({non_zero_fee/total*100:.1f}%)")
        print(f"   平台服务费为空: {null_fee} ({null_fee/total*100:.1f}%)")
        
        # 3. 查看实际值的分布
        print(f"\n3️⃣ platform_service_fee 唯一值样本 (前20个):")
        samples = session.query(Order.platform_service_fee).distinct().limit(20).all()
        for (fee,) in samples:
            print(f"   - {fee}")
        
        # 4. 关键问题:为什么都是0?
        print(f"\n4️⃣ 【核心问题分析】")
        print(f"   ❓ 为什么 platform_service_fee 都是 0?")
        print(f"   ")
        
        # 检查原始Excel数据是否有这个字段
        print(f"   可能原因:")
        print(f"   1. ❌ 原始Excel没有'平台服务费'列")
        print(f"   2. ❌ 导入时字段映射错误")
        print(f"   3. ❌ 数据库默认值为0,但实际应该从其他字段计算")
        
        # 5. 检查platform_commission是否有值
        print(f"\n5️⃣ 对比检查 platform_commission (平台佣金):")
        zero_commission = session.query(func.count(Order.id)).filter(Order.platform_commission == 0).scalar()
        non_zero_commission = session.query(func.count(Order.id)).filter(Order.platform_commission > 0).scalar()
        
        print(f"   平台佣金 = 0: {zero_commission} ({zero_commission/total*100:.1f}%)")
        print(f"   平台佣金 > 0: {non_zero_commission} ({non_zero_commission/total*100:.1f}%)")
        
        if non_zero_commission > 0:
            print(f"\n   ✅ 发现 {non_zero_commission} 笔订单有平台佣金!")
            print(f"   💡 建议: 应该用 platform_commission 而非 platform_service_fee")
        
        # 6. 显示实际订单样例
        print(f"\n6️⃣ 订单数据样例 (前5笔):")
        orders = session.query(
            Order.order_id,
            Order.platform_service_fee,
            Order.platform_commission,
            Order.total_amount
        ).limit(5).all()
        
        for order in orders:
            print(f"   订单号: {order.order_id}")
            print(f"     - 平台服务费: {order.platform_service_fee}")
            print(f"     - 平台佣金: {order.platform_commission}")
            print(f"     - 订单金额: {order.total_amount}")

if __name__ == '__main__':
    main()
