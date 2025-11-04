"""
诊断利润计算差异
验证各项成本和收入的实际数值
"""
import pandas as pd
import sys
import os

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from standard_business_config import (
    StandardBusinessConfig,
    StandardBusinessLogic,
    create_order_level_summary,
    apply_standard_business_logic
)

# 从命令行参数获取数据文件路径
if len(sys.argv) > 1:
    data_file = sys.argv[1]
else:
    print("=" * 80)
    print("📊 利润计算差异诊断")
    print("=" * 80)
    print("\n❌ 请提供数据文件路径")
    print("用法: python 诊断利润差异.py <数据文件路径>")
    print("=" * 80)
    sys.exit(1)

print("=" * 80)
print("📊 利润计算差异详细诊断")
print("=" * 80)
print(f"📂 数据文件: {data_file}")

try:
    df = pd.read_excel(data_file)
    print(f"\n✅ 成功读取数据: {len(df)} 行")
    
    # 剔除耗材
    original_count = len(df)
    category_col = None
    for col in ['一级分类名', '美团一级分类', '一级分类']:
        if col in df.columns:
            category_col = col
            break
    
    if category_col:
        df_clean = df[~df[category_col].str.contains('耗材|购物袋', na=False, case=False)].copy()
        removed = original_count - len(df_clean)
        print(f"✅ 剔除 {removed} 行耗材数据，剩余 {len(df_clean)} 行")
        df = df_clean
    
    # 创建订单级汇总
    print("\n" + "=" * 80)
    print("1️⃣ 创建订单级汇总并应用业务逻辑")
    print("=" * 80)
    
    order_agg = create_order_level_summary(df, StandardBusinessConfig)
    order_agg = apply_standard_business_logic(order_agg)
    
    print(f"✅ 订单数: {len(order_agg)}")
    
    # 计算订单总收入
    print("\n" + "=" * 80)
    print("2️⃣ 订单总收入计算")
    print("=" * 80)
    
    if '预估订单收入' in order_agg.columns:
        total_revenue = order_agg['预估订单收入'].sum()
        print(f"订单总收入（系统计算）: ¥{total_revenue:,.2f}")
        
        # 手动验证
        sales = order_agg['商品实售价总和'].sum() if '商品实售价总和' in order_agg.columns else 0
        packing = order_agg['打包费'].sum() if '打包费' in order_agg.columns else 0
        user_delivery = order_agg['用户支付配送费'].sum() if '用户支付配送费' in order_agg.columns else 0
        
        print(f"\n手动验证:")
        print(f"  商品实售价: ¥{sales:,.2f}")
        print(f"  打包费: ¥{packing:,.2f}")
        print(f"  用户支付配送费: ¥{user_delivery:,.2f}")
        print(f"  ─────────────────────")
        manual_revenue = sales + packing + user_delivery
        print(f"  合计: ¥{manual_revenue:,.2f}")
        
        if abs(manual_revenue - total_revenue) < 1:
            print(f"  ✅ 一致")
        else:
            print(f"  ⚠️ 差异: ¥{abs(manual_revenue - total_revenue):,.2f}")
    
    # 计算各项成本
    print("\n" + "=" * 80)
    print("3️⃣ 成本明细计算")
    print("=" * 80)
    
    # 1. 商品成本
    product_cost = order_agg['成本'].sum() if '成本' in order_agg.columns else 0
    print(f"\n1. 总商品成本: ¥{product_cost:,.2f}")
    
    # 2. 配送成本
    print(f"\n2. 配送成本分析:")
    user_pay_delivery = order_agg['用户支付配送费'].sum() if '用户支付配送费' in order_agg.columns else 0
    delivery_discount = order_agg['配送费减免金额'].sum() if '配送费减免金额' in order_agg.columns else 0
    logistics_fee = order_agg['物流配送费'].sum() if '物流配送费' in order_agg.columns else 0
    
    print(f"  用户支付配送费: ¥{user_pay_delivery:,.2f}")
    print(f"  配送费减免: ¥{delivery_discount:,.2f}")
    print(f"  物流配送费: ¥{logistics_fee:,.2f}")
    
    # 配送成本（可能为负）
    delivery_cost_formula = user_pay_delivery - delivery_discount - logistics_fee
    print(f"  ─────────────────────")
    print(f"  配送成本（公式）= 用户支付 - 减免 - 物流费")
    print(f"  配送成本 = ¥{delivery_cost_formula:,.2f}")
    
    # 系统计算的配送成本
    if '配送成本' in order_agg.columns:
        system_delivery_cost = order_agg['配送成本'].sum()
        print(f"  系统计算配送成本: ¥{system_delivery_cost:,.2f}")
        if abs(system_delivery_cost - delivery_cost_formula) < 1:
            print(f"  ✅ 一致")
        else:
            print(f"  ⚠️ 差异: ¥{abs(system_delivery_cost - delivery_cost_formula):,.2f}")
    
    # 用户期望的配送成本
    print(f"\n  ⚠️ 注意：您提到的'总配送成本 = ¥21,936'")
    print(f"  可能指的是: 配送费减免(¥{delivery_discount:,.2f}) + 物流配送费(¥{logistics_fee:,.2f})")
    print(f"  = ¥{delivery_discount + logistics_fee:,.2f}")
    
    # 3. 活动营销成本
    activity_marketing = order_agg['活动营销成本'].sum() if '活动营销成本' in order_agg.columns else 0
    print(f"\n3. 活动营销成本: ¥{activity_marketing:,.2f}")
    
    # 4. 商品折扣成本
    product_discount = order_agg['商品折扣成本'].sum() if '商品折扣成本' in order_agg.columns else 0
    print(f"\n4. 商品折扣成本: ¥{product_discount:,.2f}")
    
    # 5. 平台佣金
    commission = order_agg['平台佣金'].sum() if '平台佣金' in order_agg.columns else 0
    print(f"\n5. 总平台佣金: ¥{commission:,.2f}")
    
    # 利润计算
    print("\n" + "=" * 80)
    print("4️⃣ 利润计算对比")
    print("=" * 80)
    
    # 系统计算的利润
    if '订单实际利润额' in order_agg.columns:
        system_profit = order_agg['订单实际利润额'].sum()
        print(f"\n系统计算的总利润额: ¥{system_profit:,.2f}")
    
    # 按当前公式计算
    print(f"\n按当前公式计算:")
    print(f"  订单总收入: ¥{total_revenue:,.2f}")
    print(f"  - 商品成本: ¥{product_cost:,.2f}")
    print(f"  - 配送成本: ¥{delivery_cost_formula:,.2f}")
    print(f"  - 活动营销: ¥{activity_marketing:,.2f}")
    print(f"  - 商品折扣: ¥{product_discount:,.2f}")
    print(f"  - 平台佣金: ¥{commission:,.2f}")
    print(f"  ─────────────────────")
    
    current_formula_profit = (total_revenue - product_cost - delivery_cost_formula - 
                             activity_marketing - product_discount - commission)
    print(f"  利润 = ¥{current_formula_profit:,.2f}")
    
    # 按用户理解计算
    print(f"\n按您的理解计算:")
    user_delivery_cost = delivery_discount + logistics_fee  # 您说的21,936
    print(f"  订单总收入: ¥{total_revenue:,.2f}")
    print(f"  - 商品成本: ¥{product_cost:,.2f}")
    print(f"  - 总配送成本(减免+物流): ¥{user_delivery_cost:,.2f}")
    print(f"  - 活动营销: ¥{activity_marketing:,.2f}")
    print(f"  - 商品折扣: ¥{product_discount:,.2f}")
    print(f"  - 平台佣金: ¥{commission:,.2f}")
    print(f"  ─────────────────────")
    
    user_formula_profit = (total_revenue - product_cost - user_delivery_cost - 
                          activity_marketing - product_discount - commission)
    print(f"  利润 = ¥{user_formula_profit:,.2f}")
    
    # 差异分析
    print("\n" + "=" * 80)
    print("5️⃣ 差异分析")
    print("=" * 80)
    
    print(f"\n系统计算利润: ¥{system_profit:,.2f}")
    print(f"您的期望利润: ¥42,805.00")
    print(f"差异: ¥{abs(system_profit - 42805):,.2f}")
    
    print(f"\n关键差异点：配送成本的定义")
    print(f"  当前公式: 配送成本 = 用户支付(¥{user_pay_delivery:,.2f}) - 减免(¥{delivery_discount:,.2f}) - 物流(¥{logistics_fee:,.2f}) = ¥{delivery_cost_formula:,.2f}")
    print(f"  您的理解: 配送成本 = 减免(¥{delivery_discount:,.2f}) + 物流(¥{logistics_fee:,.2f}) = ¥{user_delivery_cost:,.2f}")
    print(f"  两者差异: ¥{abs(delivery_cost_formula - user_delivery_cost):,.2f}")
    
    print("\n" + "=" * 80)
    print("✅ 诊断完成")
    print("=" * 80)
    
    print("\n💡 建议：")
    print("如果您认为配送成本应该是'配送费减免 + 物流配送费'，")
    print("那么需要修改配送成本的计算公式。")
    
except Exception as e:
    print(f"\n❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()
