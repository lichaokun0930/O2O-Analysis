# -*- coding: utf-8 -*-
import pandas as pd
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')
from 订单数据处理器 import OrderDataProcessor

print("=" * 80)
print("查询：惠宜选-六安市金寨店 - 美团闪购渠道利润额")
print("=" * 80)

# 加载数据
processor = OrderDataProcessor()
df = processor.standardize_sales_data()

print(f"\n总数据行数: {len(df)}")

# 查看门店名称
if '门店名称' in df.columns:
    stores = df['门店名称'].unique()
    print(f"\n数据中的门店: {stores.tolist()}")
    
    # 筛选目标门店
    target_stores = [s for s in stores if '金寨' in s or '六安' in s]
    if target_stores:
        print(f"包含'金寨'或'六安'的门店: {target_stores}")
    else:
        print("未找到包含'金寨'或'六安'的门店")
        print("使用所有数据继续分析...")
        target_stores = stores.tolist()
else:
    print("数据中没有'门店名称'字段，使用全部数据")
    target_stores = None

# 筛选门店数据
if target_stores:
    df_store = df[df['门店名称'].isin(target_stores)].copy()
    print(f"\n筛选后数据行数: {len(df_store)}")
else:
    df_store = df.copy()

# 查看渠道
if '渠道' in df_store.columns:
    channels = df_store['渠道'].unique()
    print(f"\n该门店的渠道: {channels.tolist()}")
    
    # 查找美团闪购渠道
    meituan_channels = [c for c in channels if '美团' in c and '闪购' in c]
    if meituan_channels:
        print(f"\n找到美团闪购渠道: {meituan_channels}")
        target_channel = meituan_channels[0]
    else:
        print("\n未找到包含'美团'和'闪购'的渠道")
        meituan_all = [c for c in channels if '美团' in c]
        print(f"所有美团相关渠道: {meituan_all}")
        if meituan_all:
            target_channel = meituan_all[0]
            print(f"使用第一个美团渠道: {target_channel}")
        else:
            print("没有任何美团渠道，退出")
            sys.exit(1)
else:
    print("数据中没有'渠道'字段")
    sys.exit(1)

# 筛选目标渠道数据
df_channel = df_store[df_store['渠道'] == target_channel].copy()
print(f"\n{target_channel} 渠道数据行数: {len(df_channel)}")

if len(df_channel) == 0:
    print("该渠道没有数据")
    sys.exit(1)

# 导入计算函数
from 智能门店看板_Dash版 import calculate_order_metrics

print("\n" + "=" * 80)
print("使用 calculate_order_metrics() 计算订单实际利润")
print("=" * 80)

# 计算订单指标
order_agg = calculate_order_metrics(df_channel)

print(f"\n订单数: {len(order_agg)}")
print(f"订单ID示例: {order_agg['订单ID'].head(3).tolist()}")

# 计算总利润
total_profit = order_agg['订单实际利润'].sum()
total_sales = order_agg['商品实售价'].sum()
total_revenue = order_agg['预计订单收入'].sum()

print("\n" + "=" * 80)
print("计算结果")
print("=" * 80)
print(f"\n渠道: {target_channel}")
print(f"订单数: {len(order_agg):,} 单")
print(f"商品销售额: ¥{total_sales:,.2f}")
print(f"预计订单收入: ¥{total_revenue:,.2f}")
print(f"订单实际利润: ¥{total_profit:,.2f}")
print(f"利润率: {(total_profit / total_revenue * 100):.2f}%")

# 显示利润构成明细
print("\n" + "=" * 80)
print("利润构成明细")
print("=" * 80)

total_cost = order_agg['商品采购成本'].sum() if '商品采购成本' in order_agg.columns else 0
total_commission = order_agg['平台佣金'].sum() if '平台佣金' in order_agg.columns else 0
total_delivery = order_agg['物流配送费'].sum() if '物流配送费' in order_agg.columns else 0
total_delivery_discount = order_agg['配送费减免金额'].sum() if '配送费减免金额' in order_agg.columns else 0
total_user_delivery = order_agg['用户支付配送费'].sum() if '用户支付配送费' in order_agg.columns else 0
total_new_customer = order_agg.get('新客减免金额', pd.Series([0])).sum()
total_enterprise = order_agg.get('企客后返', pd.Series([0])).sum()
total_profit_base = order_agg.get('利润额', pd.Series([0])).sum()

print(f"\n预计订单收入:      ¥{total_revenue:>12,.2f}")
print(f"  - 商品采购成本:   ¥{total_cost:>12,.2f}")
print(f"  - 平台佣金:       ¥{total_commission:>12,.2f}")
print(f"  - 物流配送费:     ¥{total_delivery:>12,.2f}")
print(f"  - 配送费减免:     ¥{total_delivery_discount:>12,.2f}")
print(f"  + 用户支付配送费: ¥{total_user_delivery:>12,.2f}")
print(f"{'─' * 50}")
print(f"= 利润额:           ¥{total_profit_base:>12,.2f}")
print(f"  - 新客减免金额:   ¥{total_new_customer:>12,.2f}")
print(f"  + 企客后返:       ¥{total_enterprise:>12,.2f}")
print(f"{'═' * 50}")
print(f"= 订单实际利润:     ¥{total_profit:>12,.2f}")

# 验证计算
calculated_profit_base = total_revenue - total_cost - total_commission - total_delivery - total_delivery_discount + total_user_delivery
calculated_profit = calculated_profit_base - total_new_customer + total_enterprise

print("\n" + "=" * 80)
print("计算验证")
print("=" * 80)
print(f"利润额（计算）:       ¥{calculated_profit_base:,.2f}")
print(f"利润额（数据库）:     ¥{total_profit_base:,.2f}")
print(f"差异:                 ¥{abs(calculated_profit_base - total_profit_base):,.2f}")

print(f"\n订单实际利润（计算）: ¥{calculated_profit:,.2f}")
print(f"订单实际利润（数据库）: ¥{total_profit:,.2f}")
print(f"差异:                 ¥{abs(calculated_profit - total_profit):,.2f}")

if abs(calculated_profit - total_profit) < 0.01:
    print("\n✅ 验证通过！计算公式正确")
else:
    print("\n⚠️ 验证失败！存在计算差异")

print("\n" + "=" * 80)
print("查询完成")
print("=" * 80)
