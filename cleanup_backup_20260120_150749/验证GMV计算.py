# -*- coding: utf-8 -*-
"""
验证GMV计算逻辑

用户提供的验证数据：
- 门店: 惠宜选超市（昆山淀山湖镇店）
- 日期: 2026-01-18
- 预期GMV: 8440.66
- 预期营销成本: 1122
- 预期营销成本率: ~13.30%

GMV计算公式：
GMV = Σ(商品原价 × 销量) + Σ(打包袋金额) + Σ(用户支付配送费)

数据清洗规则：
1. 商品原价是商品级字段，需要乘以销量
2. 打包袋金额是订单级字段，用first聚合
3. 用户支付配送费是订单级字段，用first聚合
4. 剔除商品原价 < 0 的数据
"""

import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

from database.connection import SessionLocal
from database.models import Order
import pandas as pd

# 测试参数
STORE_NAME = "惠宜选超市（昆山淀山湖镇店）"
TEST_DATE = "2026-01-18"

def verify_gmv_calculation():
    """验证GMV计算"""
    session = SessionLocal()
    
    try:
        # 查询指定门店和日期的数据
        from sqlalchemy import func, cast, Date
        from datetime import datetime
        
        test_date = datetime.strptime(TEST_DATE, "%Y-%m-%d").date()
        
        orders = session.query(Order).filter(
            Order.store_name == STORE_NAME,
            cast(Order.date, Date) == test_date
        ).all()
        
        if not orders:
            print(f"❌ 未找到数据: {STORE_NAME} {TEST_DATE}")
            return
        
        print(f"=" * 70)
        print(f"验证GMV计算 - {STORE_NAME}")
        print(f"日期: {TEST_DATE}")
        print(f"=" * 70)
        print(f"\n原始记录数: {len(orders)}")
        
        # 转换为DataFrame
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '商品名称': order.product_name,
                '商品原价': float(order.original_price or 0),
                '月售': order.quantity if order.quantity is not None else 1,
                '打包袋金额': float(order.packaging_fee or 0),
                '用户支付配送费': float(order.user_paid_delivery_fee or 0),
                '实收价格': float(order.actual_price or 0),
                # 营销成本字段
                '满减金额': float(order.full_reduction or 0),
                '商品减免金额': float(order.product_discount or 0),
                '商家代金券': float(order.merchant_voucher or 0),
                '商家承担部分券': float(order.merchant_share or 0),
                '满赠金额': float(order.gift_amount or 0),
                '商家其他优惠': float(order.other_merchant_discount or 0),
                '新客减免金额': float(order.new_customer_discount or 0),
            })
        
        df = pd.DataFrame(data)
        
        # 统计订单数
        unique_orders = df['订单ID'].nunique()
        print(f"唯一订单数: {unique_orders}")
        
        # ==================== GMV计算 ====================
        print(f"\n" + "=" * 70)
        print("GMV计算过程:")
        print("=" * 70)
        
        # 关键理解：剔除商品原价<=0的整行数据
        # 意思是：这一行的商品原价、打包袋金额、用户支付配送费都不计入GMV
        # 即使同一订单有其他商品原价>0的行，商品原价<=0的那一行的打包袋和配送费也要剔除
        
        # 1. 先统计商品原价<=0的行的打包袋和配送费（需要从GMV中剔除）
        zero_price_rows = df[df['商品原价'] <= 0]
        removed_count = len(zero_price_rows)
        
        # 这些行的打包袋和配送费需要剔除（每行都有，因为是订单级字段重复展示）
        removed_packaging = zero_price_rows['打包袋金额'].sum() / zero_price_rows.groupby('订单ID').ngroups if removed_count > 0 else 0
        removed_delivery = zero_price_rows['用户支付配送费'].sum() / zero_price_rows.groupby('订单ID').ngroups if removed_count > 0 else 0
        
        # 实际上每个商品原价=0的行就是一行，打包袋和配送费就是那一行的值
        # 但因为同一订单可能有多个商品原价=0的行，需要按行来算
        removed_packaging_total = 0
        removed_delivery_total = 0
        for _, row in zero_price_rows.iterrows():
            removed_packaging_total += row['打包袋金额']
            removed_delivery_total += row['用户支付配送费']
        
        # 但是！打包袋和配送费是订单级的，同一订单的多行值相同
        # 所以需要按订单去重后再求和
        zero_price_order_level = zero_price_rows.groupby('订单ID').agg({
            '打包袋金额': 'first',
            '用户支付配送费': 'first'
        })
        removed_packaging = zero_price_order_level['打包袋金额'].sum()
        removed_delivery = zero_price_order_level['用户支付配送费'].sum()
        
        print(f"\n1. 商品原价<=0的行数: {removed_count} 条")
        print(f"   涉及唯一订单数: {len(zero_price_order_level)} 个")
        print(f"   这些行的打包袋金额合计（去重后）: ¥{removed_packaging:,.2f}")
        print(f"   这些行的用户支付配送费合计（去重后）: ¥{removed_delivery:,.2f}")
        
        # 2. 剔除商品原价<=0的行后计算
        df_clean = df[df['商品原价'] > 0].copy()
        print(f"   剩余记录数: {len(df_clean)}")
        
        # 2. 计算商品原价销售额 = Σ(商品原价 × 销量)
        df_clean['原价销售额'] = df_clean['商品原价'] * df_clean['月售']
        original_price_sales = df_clean['原价销售额'].sum()
        print(f"\n2. 商品原价销售额 = Σ(商品原价 × 销量)")
        print(f"   = ¥{original_price_sales:,.2f}")
        
        # 3. 订单级字段聚合
        order_level_agg = df_clean.groupby('订单ID').agg({
            '打包袋金额': 'first',
            '用户支付配送费': 'first',
            # 营销成本字段
            '满减金额': 'first',
            '商品减免金额': 'first',
            '商家代金券': 'first',
            '商家承担部分券': 'first',
            '满赠金额': 'first',
            '商家其他优惠': 'first',
            '新客减免金额': 'first',
        }).reset_index()
        
        packaging_fee = order_level_agg['打包袋金额'].sum()
        user_delivery_fee = order_level_agg['用户支付配送费'].sum()
        
        print(f"\n3. 订单级字段（用first聚合避免重复）:")
        print(f"   打包袋金额 = ¥{packaging_fee:,.2f}")
        print(f"   用户支付配送费 = ¥{user_delivery_fee:,.2f}")
        
        # 4. 计算GMV
        gmv = original_price_sales + packaging_fee + user_delivery_fee
        print(f"\n4. GMV = 商品原价销售额 + 打包袋金额 + 用户支付配送费")
        print(f"   = ¥{original_price_sales:,.2f} + ¥{packaging_fee:,.2f} + ¥{user_delivery_fee:,.2f}")
        print(f"   = ¥{gmv:,.2f}")
        
        # ==================== 营销成本计算 ====================
        print(f"\n" + "=" * 70)
        print("营销成本计算（7字段）:")
        print("=" * 70)
        
        marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', '满赠金额', '商家其他优惠', '新客减免金额']
        marketing_cost = 0
        
        print(f"\n各字段明细:")
        for field in marketing_fields:
            value = order_level_agg[field].sum()
            marketing_cost += value
            print(f"   {field}: ¥{value:,.2f}")
        
        print(f"\n   营销成本合计: ¥{marketing_cost:,.2f}")
        
        # ==================== 营销成本率计算 ====================
        print(f"\n" + "=" * 70)
        print("营销成本率计算:")
        print("=" * 70)
        
        marketing_cost_rate = (marketing_cost / gmv * 100) if gmv > 0 else 0
        
        print(f"\n营销成本率 = 营销成本 / GMV × 100%")
        print(f"           = ¥{marketing_cost:,.2f} / ¥{gmv:,.2f} × 100%")
        print(f"           = {marketing_cost_rate:.2f}%")
        
        # ==================== 与预期值对比 ====================
        print(f"\n" + "=" * 70)
        print("与用户预期值对比:")
        print("=" * 70)
        
        expected_gmv = 8440.66
        expected_marketing_cost = 1122
        expected_rate = 13.30
        
        print(f"\n| 指标 | 计算值 | 预期值 | 差异 |")
        print(f"|------|--------|--------|------|")
        print(f"| GMV | ¥{gmv:,.2f} | ¥{expected_gmv:,.2f} | {gmv - expected_gmv:+.2f} |")
        print(f"| 营销成本 | ¥{marketing_cost:,.2f} | ¥{expected_marketing_cost:,.2f} | {marketing_cost - expected_marketing_cost:+.2f} |")
        print(f"| 营销成本率 | {marketing_cost_rate:.2f}% | {expected_rate:.2f}% | {marketing_cost_rate - expected_rate:+.2f}pp |")
        
        # 判断是否匹配
        gmv_match = abs(gmv - expected_gmv) < 1
        marketing_match = abs(marketing_cost - expected_marketing_cost) < 1
        rate_match = abs(marketing_cost_rate - expected_rate) < 0.5
        
        print(f"\n验证结果:")
        print(f"   GMV匹配: {'✅' if gmv_match else '❌'}")
        print(f"   营销成本匹配: {'✅' if marketing_match else '❌'}")
        print(f"   营销成本率匹配: {'✅' if rate_match else '❌'}")
        
        if gmv_match and marketing_match and rate_match:
            print(f"\n🎉 所有指标验证通过！")
        else:
            print(f"\n⚠️ 部分指标存在差异，请检查数据")
        
    finally:
        session.close()


if __name__ == "__main__":
    verify_gmv_calculation()
