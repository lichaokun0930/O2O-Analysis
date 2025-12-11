"""
验证原始数据中的利润额计算公式

检查Excel中的利润额 = ? 
"""

import pandas as pd
import numpy as np

# 加载原始数据
data_file = r"d:\Python\订单数据看板\O2O-Analysis\实际数据\2025-11-04 00_00_00至2025-12-03 23_59_59订单明细数据导出汇总.xlsx"
df = pd.read_excel(data_file)

print("=" * 100)
print("验证原始数据中的利润额计算公式")
print("=" * 100)

# 随机抽取10个订单进行验证
sample = df.sample(min(10, len(df)), random_state=42)

print(f"\n可用字段: {', '.join(df.columns.tolist())}\n")

for idx, row in sample.iterrows():
    print(f"\n订单 #{idx} - {row['商品名称'][:30]}")
    print(f"  {'字段':<20} {'值':<15} {'说明'}")
    print(f"  {'-'*60}")
    
    # 基础数据
    print(f"  {'销量':<20} {row['销量']:<15.0f}")
    print(f"  {'实收价格':<20} ¥{row['实收价格']:<14.2f} (实际成交单价)")
    print(f"  {'成本':<20} ¥{row['成本']:<14.2f} (单品成本)")
    print(f"  {'商品实售价':<20} ¥{row['商品实售价']:<14.2f} (标价)")
    print(f"  {'':<20} {'':<15}")
    
    # 营销成本相关
    marketing_cols = ['满减金额', '新客减免金额', '配送费减免金额', '商家代金券', 
                      '商家承担部分券', '满赠金额', '商家其他优惠', '商品减免金额']
    total_marketing = 0
    for col in marketing_cols:
        if col in row.index:
            val = row[col] if pd.notna(row[col]) else 0
            if val != 0:
                print(f"  {col:<20} ¥{val:<14.2f}")
                total_marketing += val
    
    if total_marketing > 0:
        print(f"  {'营销成本合计':<20} ¥{total_marketing:<14.2f}")
        print(f"  {'':<20} {'':<15}")
    
    # 其他成本
    if '平台服务费' in row.index and pd.notna(row['平台服务费']):
        print(f"  {'平台服务费':<20} ¥{row['平台服务费']:<14.2f}")
    if '物流配送费' in row.index and pd.notna(row['物流配送费']):
        print(f"  {'物流配送费':<20} ¥{row['物流配送费']:<14.2f}")
    if '企客后返' in row.index and pd.notna(row['企客后返']):
        print(f"  {'企客后返':<20} ¥{row['企客后返']:<14.2f} (返利)")
    
    print(f"  {'':<20} {'':<15}")
    print(f"  {'利润额(数据)':<20} ¥{row['利润额']:<14.2f} ⭐")
    
    # 尝试反推利润额计算公式
    print(f"\n  📊 反推计算公式:")
    
    # 方案1：简单毛利 = (实收价格 - 成本) × 销量
    simple_profit = (row['实收价格'] - row['成本']) * row['销量']
    print(f"     方案1: (实收价格 - 成本) × 销量 = {simple_profit:.2f}")
    
    # 方案2：扣除营销成本后的利润
    profit_after_marketing = simple_profit - total_marketing
    print(f"     方案2: 简单毛利 - 营销成本 = {profit_after_marketing:.2f}")
    
    # 方案3：扣除所有平台费用
    platform_fee = row.get('平台服务费', 0) if pd.notna(row.get('平台服务费', 0)) else 0
    logistics_fee = row.get('物流配送费', 0) if pd.notna(row.get('物流配送费', 0)) else 0
    rebate = row.get('企客后返', 0) if pd.notna(row.get('企客后返', 0)) else 0
    profit_after_all = simple_profit - total_marketing - platform_fee - logistics_fee + rebate
    print(f"     方案3: 方案2 - 平台费 - 物流费 + 返利 = {profit_after_all:.2f}")
    
    # 对比实际值
    actual_profit = row['利润额']
    print(f"\n  ✅ 实际利润额: ¥{actual_profit:.2f}")
    
    # 判断最接近哪个方案
    diff1 = abs(simple_profit - actual_profit)
    diff2 = abs(profit_after_marketing - actual_profit)
    diff3 = abs(profit_after_all - actual_profit)
    
    if diff1 < 0.01:
        print(f"  🎯 匹配方案1：简单毛利")
    elif diff2 < 0.01:
        print(f"  🎯 匹配方案2：扣除营销成本")
    elif diff3 < 0.01:
        print(f"  🎯 匹配方案3：扣除所有费用")
    else:
        print(f"  ⚠️ 未匹配任何方案 (差异: 方案1={diff1:.2f}, 方案2={diff2:.2f}, 方案3={diff3:.2f})")

print("\n" + "=" * 100)
print("结论")
print("=" * 100)
print("""
通过对比可以判断出原始数据中的'利润额'计算口径：

📌 如果匹配方案1：利润额 = (实收价格 - 成本) × 销量
   → 只扣除了商品成本，未扣除营销成本
   → calculate_enhanced_product_scores需要重新计算营销成本分摊

📌 如果匹配方案2或方案3：利润额已经扣除了营销成本和平台费用
   → calculate_enhanced_product_scores中的营销成本计算是多余的
   → 会导致重复扣除，利润率偏低

建议：检查Excel源数据中的'利润额'列公式，确认计算口径
""")
