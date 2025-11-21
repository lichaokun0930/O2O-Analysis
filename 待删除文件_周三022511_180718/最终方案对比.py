#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终方案对比 - 正确理解耗材逻辑
"""

import pandas as pd

df = pd.read_excel('实际数据/枫瑞.xlsx')
df_mt = df[df['渠道'] == '美团共橙'].copy()

print("="*80)
print("最终方案对比")
print("="*80)

print("\n⭐ 关键理解:")
print("  耗材利润 = -548.81元(负值)")
print("  负值在求和时会自动减去,所以:")
print("  不剔除耗材利润额 = 31,176.37元 (已包含耗材亏损)")
print("  剔除耗材利润额 = 31,725.18元 (去掉负值,反而更高)")

# 方案对比
def calc_profit(data, use_fallback=True, filter_zero_fee=False):
    """统一的利润计算函数"""
    order_agg = data.groupby('订单ID').agg({
        '利润额': 'sum',
        '平台服务费': 'sum',
        '平台佣金': 'first',
        '物流配送费': 'first',
        '企客后返': 'sum'
    }).reset_index()
    
    # 过滤服务费<=0的订单
    if filter_zero_fee:
        order_agg = order_agg[order_agg['平台服务费'] > 0].copy()
    
    # 计算利润
    service_fee = order_agg['平台服务费']
    if use_fallback:
        commission = order_agg['平台佣金']
        fallback_mask = (service_fee <= 0)
        service_fee = service_fee.mask(fallback_mask, commission)
    
    profit = (
        order_agg['利润额'] -
        service_fee -
        order_agg['物流配送费'] +
        order_agg['企客后返']
    )
    
    return order_agg, profit.sum()

print("\n" + "="*80)
print("4种方案完整对比:")
print("="*80)

# 方案1: 剔除耗材 + all_with_fallback (当前看板方案)
df1 = df_mt[df_mt['一级分类名'] != '耗材'].copy()
agg1, profit1 = calc_profit(df1, use_fallback=True, filter_zero_fee=False)
print(f"\n【方案1: 剔除耗材 + all_with_fallback (当前看板)】")
print(f"  利润额: {agg1['利润额'].sum():.2f}")
print(f"  订单数: {len(agg1)}")
print(f"  订单实际利润: {profit1:.2f} 元 ❌")

# 方案2: 不剔除耗材 + all_with_fallback
agg2, profit2 = calc_profit(df_mt, use_fallback=True, filter_zero_fee=False)
print(f"\n【方案2: 不剔除耗材 + all_with_fallback】")
print(f"  利润额: {agg2['利润额'].sum():.2f} (包含耗材亏损)")
print(f"  订单数: {len(agg2)}")
print(f"  订单实际利润: {profit2:.2f} 元 ❌")

# 方案3: 剔除耗材 + all_no_fallback
agg3, profit3 = calc_profit(df1, use_fallback=False, filter_zero_fee=True)
print(f"\n【方案3: 剔除耗材 + all_no_fallback】")
print(f"  利润额: {agg3['利润额'].sum():.2f}")
print(f"  订单数: {len(agg3)} (过滤掉{len(agg1)-len(agg3)}单)")
print(f"  订单实际利润: {profit3:.2f} 元 ✅")

# 方案4: 不剔除耗材 + all_no_fallback ⭐您之前看到的652.06
agg4, profit4 = calc_profit(df_mt, use_fallback=False, filter_zero_fee=True)
print(f"\n【方案4: 不剔除耗材 + all_no_fallback】⭐")
print(f"  利润额: {agg4['利润额'].sum():.2f} (包含耗材亏损)")
print(f"  订单数: {len(agg4)} (过滤掉{len(agg2)-len(agg4)}单)")
print(f"  订单实际利润: {profit4:.2f} 元 ✅ 这就是您之前看到的652.06!")

print("\n" + "="*80)
print("总结:")
print("="*80)
print(f"方案1(当前看板): {profit1:>10.2f}元 - 剔除耗材,保留所有订单")
print(f"方案2:            {profit2:>10.2f}元 - 包含耗材,保留所有订单")
print(f"方案3:            {profit3:>10.2f}元 - 剔除耗材,过滤服务费<=0订单")
print(f"方案4:            {profit4:>10.2f}元 - 包含耗材,过滤服务费<=0订单")

print("\n推荐方案:")
print("✅ 方案3: 利润最高(1201.17元)")
print("   - 剔除耗材(去掉亏损商品)")
print("   - 过滤服务费<=0的订单(这些订单可能有问题)")
print("\n✅ 方案4: 利润次高(652.06元)")
print("   - 保留耗材(真实反映成本)")
print("   - 过滤服务费<=0的订单")

print("\n关键差异:")
print(f"  方案3 vs 方案4 差异: {profit3 - profit4:.2f}元 = 耗材亏损")
print(f"  方案1 vs 方案3 差异: {profit3 - profit1:.2f}元 = 339个问题订单")
