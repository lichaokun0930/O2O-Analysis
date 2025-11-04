"""诊断看板实际显示的利润值"""
import sys
import os
sys.path.insert(0, r'd:\Python1\O2O_Analysis\O2O数据分析')

import pandas as pd
from standard_business_config import StandardBusinessLogic, StandardBusinessConfig, create_order_level_summary, apply_standard_business_logic

# 加载实际数据
data_file = r"d:\Python1\O2O_Analysis\O2O数据分析\测算模型\实际数据\W36-W37订单数据.xlsx"
print(f"📂 加载数据: {data_file}")
df = pd.read_excel(data_file)
print(f"   原始数据行数: {len(df)}")

# 剔除耗材数据（模拟看板的处理）
if '三级分类名' in df.columns:
    consumables_mask = df['三级分类名'].str.contains('购物袋', na=False)
    before = len(df)
    df = df[~consumables_mask]
    after = len(df)
    if before != after:
        print(f"   ✅ 已剔除 {before - after} 行耗材数据，从 {before} 行减少到 {after} 行")

# 创建订单级汇总
print("\n📊 创建订单级汇总...")
order_agg = create_order_level_summary(df, StandardBusinessConfig)
print(f"   订单数: {len(order_agg)}")

# 应用标准业务逻辑计算
print("\n🔧 应用标准业务逻辑...")
order_agg = apply_standard_business_logic(order_agg)

# 检查计算结果
print("\n" + "="*80)
print("📊 看板显示的关键指标")
print("="*80)

# 商品销售额（商品实售价总和）
if '商品实售价总和' in order_agg.columns:
    total_sales = order_agg['商品实售价总和'].sum()
    print(f"\n商品销售额: ¥{total_sales:,.2f}")
else:
    print(f"\n⚠️ 缺少'商品实售价总和'列")

# 订单总收入
if '预估订单收入' in order_agg.columns:
    total_revenue = order_agg['预估订单收入'].sum()
    print(f"订单总收入: ¥{total_revenue:,.2f}")
else:
    print(f"⚠️ 缺少'预估订单收入'列")

# 总配送成本
if '配送成本' in order_agg.columns:
    total_delivery_cost = order_agg['配送成本'].sum()
    avg_delivery_cost = order_agg['配送成本'].mean()
    print(f"总配送成本: ¥{total_delivery_cost:,.2f} (平均: ¥{avg_delivery_cost:.2f}/单)")
    
    # 验证配送成本公式
    print(f"\n🔍 配送成本公式验证:")
    if '配送费减免金额' in order_agg.columns and '物流配送费' in order_agg.columns:
        manual_delivery = (order_agg['配送费减免金额'] + order_agg['物流配送费']).sum()
        print(f"   手动计算 (配送费减免 + 物流配送费): ¥{manual_delivery:,.2f}")
        if abs(total_delivery_cost - manual_delivery) < 0.01:
            print(f"   ✅ 配送成本使用的是新公式(正确)")
        else:
            print(f"   ❌ 配送成本计算有误")
            print(f"   差异: ¥{abs(total_delivery_cost - manual_delivery):,.2f}")
else:
    print(f"⚠️ 缺少'配送成本'列")

# 活动营销成本
if '活动营销成本' in order_agg.columns:
    total_activity_marketing = order_agg['活动营销成本'].sum()
    print(f"\n活动营销成本: ¥{total_activity_marketing:,.2f}")
else:
    print(f"\n⚠️ 缺少'活动营销成本'列")

# 商品折扣成本
if '商品折扣成本' in order_agg.columns:
    total_product_discount = order_agg['商品折扣成本'].sum()
    print(f"商品折扣成本: ¥{total_product_discount:,.2f}")
else:
    print(f"⚠️ 缺少'商品折扣成本'列")

# 商品成本
if '成本' in order_agg.columns:
    total_product_cost = order_agg['成本'].sum()
    print(f"总商品成本: ¥{total_product_cost:,.2f}")
else:
    print(f"⚠️ 缺少'成本'列")

# 平台佣金
if '平台佣金' in order_agg.columns:
    total_commission = order_agg['平台佣金'].sum()
    print(f"总平台佣金: ¥{total_commission:,.2f}")
else:
    print(f"⚠️ 缺少'平台佣金'列")

# 订单实际利润
if '订单实际利润额' in order_agg.columns:
    total_profit = order_agg['订单实际利润额'].sum()
    avg_profit = order_agg['订单实际利润额'].mean()
    profitable_orders = (order_agg['订单实际利润额'] > 0).sum()
    profit_rate = profitable_orders / len(order_agg)
    
    print(f"\n" + "="*80)
    print(f"💰 总利润额: ¥{total_profit:,.2f}")
    print(f"="*80)
    print(f"   平均订单利润: ¥{avg_profit:.2f}")
    print(f"   盈利订单数: {profitable_orders} / {len(order_agg)} ({profit_rate:.1%})")
    
    # 手动验证利润计算
    print(f"\n🔍 利润计算验证:")
    if all(col in order_agg.columns for col in ['预估订单收入', '成本', '配送成本', '活动营销成本', '商品折扣成本', '平台佣金']):
        manual_profit = (
            order_agg['预估订单收入'].sum() -
            order_agg['成本'].sum() -
            order_agg['配送成本'].sum() -
            order_agg['活动营销成本'].sum() -
            order_agg['商品折扣成本'].sum() -
            order_agg['平台佣金'].sum()
        )
        print(f"   手动计算: ¥{manual_profit:,.2f}")
        if abs(total_profit - manual_profit) < 0.01:
            print(f"   ✅ 利润计算正确")
        else:
            print(f"   ❌ 利润计算有误")
            print(f"   差异: ¥{abs(total_profit - manual_profit):,.2f}")
else:
    print(f"\n⚠️ 缺少'订单实际利润额'列")

# 详细的利润构成分析
print(f"\n" + "="*80)
print(f"📊 利润构成详细分析")
print(f"="*80)

if all(col in order_agg.columns for col in ['预估订单收入', '成本', '配送成本', '活动营销成本', '商品折扣成本', '平台佣金']):
    revenue = order_agg['预估订单收入'].sum()
    costs = {
        '商品成本': order_agg['成本'].sum(),
        '配送成本': order_agg['配送成本'].sum(),
        '活动营销成本': order_agg['活动营销成本'].sum(),
        '商品折扣成本': order_agg['商品折扣成本'].sum(),
        '平台佣金': order_agg['平台佣金'].sum()
    }
    
    print(f"\n收入:")
    print(f"   订单总收入: ¥{revenue:,.2f}")
    
    print(f"\n成本明细:")
    total_costs = 0
    for cost_name, cost_value in costs.items():
        print(f"   {cost_name}: ¥{cost_value:,.2f}")
        total_costs += cost_value
    
    print(f"\n   总成本: ¥{total_costs:,.2f}")
    print(f"\n最终利润:")
    print(f"   = 订单总收入 - 总成本")
    print(f"   = ¥{revenue:,.2f} - ¥{total_costs:,.2f}")
    print(f"   = ¥{revenue - total_costs:,.2f}")

print(f"\n" + "="*80)
print(f"✅ 诊断完成")
print(f"="*80)
