#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证看板中所有指标的计算准确性"""

import pandas as pd
import sys
from pathlib import Path

# 添加上级目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from standard_business_config import StandardBusinessConfig, create_order_level_summary, apply_standard_business_logic

def verify_all_metrics():
    """验证所有指标计算"""
    
    # 查找数据文件
    data_dir = Path("实际数据")
    excel_files = list(data_dir.glob("*.xlsx"))
    
    if not excel_files:
        print("❌ 未找到数据文件")
        return
    
    print(f"📂 读取文件: {excel_files[0].name}\n")
    df = pd.read_excel(excel_files[0])
    
    # 剔除耗材数据
    original_count = len(df)
    df = df[~df['商品名称'].str.contains('购物袋|塑料袋', na=False)]
    print(f"✅ 已剔除 {original_count - len(df)} 行耗材数据\n")
    
    # 创建订单级汇总
    order_agg = create_order_level_summary(df, StandardBusinessConfig)
    order_agg = apply_standard_business_logic(order_agg)
    
    print("=" * 80)
    print("【核心指标验证】")
    print("=" * 80)
    
    # 1. 订单数量
    print(f"\n1️⃣ 订单总数: {len(order_agg):,}")
    print(f"   商品总数: {len(df):,}")
    print(f"   平均每单商品数: {len(df) / len(order_agg):.2f}")
    
    # 2. 销售额（商品实售价总和）
    total_sales = order_agg['商品实售价总和'].sum()
    avg_sales = total_sales / len(order_agg)
    median_sales = order_agg['商品实售价总和'].median()
    print(f"\n2️⃣ 总销售额（商品实售价）: ¥{total_sales:,.2f}")
    print(f"   平均客单价: ¥{avg_sales:,.2f}")
    print(f"   客单价中位数: ¥{median_sales:,.2f}")
    print(f"   ✅ 计算公式: sum(商品实售价总和)")
    
    # 3. 订单总收入（包含打包费和配送费）
    packing_fee = order_agg['打包袋金额'].sum() if '打包袋金额' in order_agg.columns else 0
    user_pay_delivery = order_agg['用户支付配送费'].sum()
    total_revenue = total_sales + packing_fee + user_pay_delivery
    print(f"\n3️⃣ 订单总收入: ¥{total_revenue:,.2f}")
    print(f"   = 商品实售价(¥{total_sales:,.2f}) + 打包费(¥{packing_fee:,.2f}) + 用户支付配送费(¥{user_pay_delivery:,.2f})")
    print(f"   ✅ 计算公式: 商品实售价总和 + 打包袋金额 + 用户支付配送费")
    
    # 4. 配送成本（净成本）
    delivery_cost = order_agg['配送成本'].sum()
    exemption = order_agg['配送费减免金额'].sum()
    logistics = order_agg['物流配送费'].sum()
    print(f"\n4️⃣ 配送成本（净成本）: ¥{delivery_cost:,.2f}")
    print(f"   = (配送费减免¥{exemption:,.2f} + 物流配送费¥{logistics:,.2f}) - 用户支付¥{user_pay_delivery:,.2f}")
    print(f"   = ¥{exemption + logistics - user_pay_delivery:,.2f}")
    print(f"   ✅ 计算公式: (配送费减免金额 + 物流配送费) - 用户支付配送费")
    
    # 5. 其他成本
    total_cost = order_agg['成本'].sum()
    activity_cost = order_agg['活动营销成本'].sum()
    discount_cost = order_agg['商品折扣成本'].sum()
    commission = order_agg['平台佣金'].sum()
    
    print(f"\n5️⃣ 其他成本:")
    print(f"   商品成本: ¥{total_cost:,.2f}")
    print(f"   活动营销成本: ¥{activity_cost:,.2f}")
    print(f"   商品折扣成本: ¥{discount_cost:,.2f}")
    print(f"   平台佣金: ¥{commission:,.2f}")
    
    # 6. 总利润
    total_profit = order_agg['订单实际利润额'].sum()
    expected_profit = total_revenue - total_cost - delivery_cost - activity_cost - discount_cost - commission
    
    print(f"\n6️⃣ 总利润额: ¥{total_profit:,.2f}")
    print(f"   验算: ¥{total_revenue:,.2f} - ¥{total_cost:,.2f} - ¥{delivery_cost:,.2f} - ¥{activity_cost:,.2f} - ¥{discount_cost:,.2f} - ¥{commission:,.2f}")
    print(f"   = ¥{expected_profit:,.2f}")
    print(f"   差异: ¥{abs(total_profit - expected_profit):,.2f}")
    if abs(total_profit - expected_profit) < 0.01:
        print(f"   ✅ 利润计算正确")
    else:
        print(f"   ❌ 利润计算有误差")
    
    # 7. 盈利订单比例
    profit_orders = (order_agg['订单实际利润额'] > 0).sum()
    profit_ratio = (order_agg['订单实际利润额'] > 0).mean()
    print(f"\n7️⃣ 盈利订单数: {profit_orders:,}")
    print(f"   盈利订单比例: {profit_ratio:.2%}")
    print(f"   ✅ 计算公式: (订单实际利润额 > 0的订单数) / 订单总数")
    
    # 8. 平均值
    avg_profit = order_agg['订单实际利润额'].mean()
    avg_delivery = order_agg['配送成本'].mean()
    
    print(f"\n8️⃣ 平均值:")
    print(f"   平均订单利润: ¥{avg_profit:,.2f}")
    print(f"   平均配送成本: ¥{avg_delivery:,.2f}")
    print(f"   平均活动营销成本: ¥{order_agg['活动营销成本'].mean():,.2f}")
    print(f"   平均商品折扣成本: ¥{order_agg['商品折扣成本'].mean():,.2f}")
    
    # 9. 毛利率和净利率计算验证
    print(f"\n9️⃣ 利润率指标:")
    # 毛利 = 销售额 - 商品成本
    gross_profit = total_sales - total_cost
    gross_margin = (gross_profit / total_sales * 100) if total_sales > 0 else 0
    print(f"   毛利润: ¥{gross_profit:,.2f}")
    print(f"   毛利率: {gross_margin:.2f}%")
    print(f"   ✅ 计算公式: (销售额 - 商品成本) / 销售额 × 100%")
    
    # 净利率 = 总利润 / 订单总收入
    net_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    print(f"   净利润: ¥{total_profit:,.2f}")
    print(f"   净利率: {net_margin:.2f}%")
    print(f"   ✅ 计算公式: 总利润 / 订单总收入 × 100%")
    
    # 10. 成本占比
    print(f"\n🔟 成本结构占比（占订单总收入）:")
    cost_items = {
        '商品成本': total_cost,
        '配送成本': delivery_cost,
        '活动营销成本': activity_cost,
        '商品折扣成本': discount_cost,
        '平台佣金': commission
    }
    
    for name, value in cost_items.items():
        ratio = (value / total_revenue * 100) if total_revenue > 0 else 0
        print(f"   {name}: ¥{value:,.2f} ({ratio:.2f}%)")
    
    total_costs = sum(cost_items.values())
    total_cost_ratio = (total_costs / total_revenue * 100) if total_revenue > 0 else 0
    print(f"   总成本: ¥{total_costs:,.2f} ({total_cost_ratio:.2f}%)")
    print(f"   利润占比: ¥{total_profit:,.2f} ({net_margin:.2f}%)")
    
    # 验证总和
    sum_check = total_costs + total_profit
    print(f"\n   验证: 总成本 + 利润 = ¥{sum_check:,.2f}")
    print(f"   订单总收入 = ¥{total_revenue:,.2f}")
    print(f"   差异: ¥{abs(sum_check - total_revenue):,.2f}")
    if abs(sum_check - total_revenue) < 0.01:
        print(f"   ✅ 成本结构验证正确")
    else:
        print(f"   ❌ 成本结构有误差")
    
    print("\n" + "=" * 80)
    print("【验证完成】")
    print("=" * 80)

if __name__ == "__main__":
    verify_all_metrics()
