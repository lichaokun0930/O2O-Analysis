# -*- coding: utf-8 -*-
import pandas as pd
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 直接加载Excel文件
file_path = "实际数据/金寨.xlsx"

print("=" * 80)
print("查询：惠宜选-六安市金寨店 - 美团闪购渠道利润额")
print("=" * 80)

df = pd.read_excel(file_path)
print(f"\n总数据行数: {len(df)}")
print(f"字段: {df.columns.tolist()}")

# 查看门店和渠道
if '门店名称' in df.columns:
    print(f"\n门店: {df['门店名称'].unique().tolist()}")
if '渠道' in df.columns:
    print(f"渠道: {df['渠道'].unique().tolist()}")

# 筛选美团闪购数据
if '渠道' in df.columns:
    df_meituan = df[df['渠道'].str.contains('美团.*闪购', na=False, regex=True)].copy()
    
    if len(df_meituan) == 0:
        # 尝试只包含"美团"
        df_meituan = df[df['渠道'].str.contains('美团', na=False)].copy()
        print(f"\n未找到'美团闪购'，使用所有美团渠道，共{len(df_meituan)}行")
    else:
        print(f"\n美团闪购数据: {len(df_meituan)}行")
    
    if len(df_meituan) > 0:
        channel_name = df_meituan['渠道'].iloc[0]
        print(f"渠道名称: {channel_name}")
        
        # 关键字段
        revenue_field = '预计订单收入' if '预计订单收入' in df_meituan.columns else '商品实售价'
        cost_field = '商品采购成本' if '商品采购成本' in df_meituan.columns else '成本'
        
        print(f"\n使用字段:")
        print(f"  收入字段: {revenue_field}")
        print(f"  成本字段: {cost_field}")
        
        # 按订单聚合
        print("\n按订单聚合计算...")
        
        # 订单级聚合字典
        agg_dict = {
            revenue_field: 'sum',
            cost_field: 'sum',
            '平台佣金': 'first' if '平台佣金' in df_meituan.columns else lambda x: 0,
            '物流配送费': 'first' if '物流配送费' in df_meituan.columns else lambda x: 0,
            '配送费减免金额': 'first' if '配送费减免金额' in df_meituan.columns else lambda x: 0,
            '用户支付配送费': 'first' if '用户支付配送费' in df_meituan.columns else lambda x: 0,
        }
        
        # 可选字段
        if '新客减免金额' in df_meituan.columns:
            agg_dict['新客减免金额'] = 'first'
        if '企客后返' in df_meituan.columns:
            agg_dict['企客后返'] = 'sum'
        
        order_agg = df_meituan.groupby('订单ID').agg(agg_dict).reset_index()
        
        # 计算利润
        order_agg['利润额'] = (
            order_agg[revenue_field] - 
            order_agg[cost_field] - 
            order_agg['平台佣金'] - 
            order_agg['物流配送费'] - 
            order_agg['配送费减免金额'] + 
            order_agg['用户支付配送费']
        )
        
        order_agg['订单实际利润'] = (
            order_agg['利润额'] - 
            order_agg.get('新客减免金额', 0) + 
            order_agg.get('企客后返', 0)
        )
        
        # 汇总
        total_orders = len(order_agg)
        total_revenue = order_agg[revenue_field].sum()
        total_cost = order_agg[cost_field].sum()
        total_commission = order_agg['平台佣金'].sum()
        total_delivery = order_agg['物流配送费'].sum()
        total_delivery_discount = order_agg['配送费减免金额'].sum()
        total_user_delivery = order_agg['用户支付配送费'].sum()
        total_new_customer = order_agg.get('新客减免金额', pd.Series([0])).sum()
        total_enterprise = order_agg.get('企客后返', pd.Series([0])).sum()
        total_profit_base = order_agg['利润额'].sum()
        total_profit = order_agg['订单实际利润'].sum()
        
        print("\n" + "=" * 80)
        print(f"【{channel_name}】 利润计算结果")
        print("=" * 80)
        print(f"\n订单数: {total_orders:,} 单")
        print(f"\n{revenue_field}:      ¥{total_revenue:>15,.2f}")
        print(f"  - {cost_field}:   ¥{total_cost:>15,.2f}")
        print(f"  - 平台佣金:       ¥{total_commission:>15,.2f}")
        print(f"  - 物流配送费:     ¥{total_delivery:>15,.2f}")
        print(f"  - 配送费减免:     ¥{total_delivery_discount:>15,.2f}")
        print(f"  + 用户支付配送费: ¥{total_user_delivery:>15,.2f}")
        print(f"{'─' * 80}")
        print(f"= 利润额:           ¥{total_profit_base:>15,.2f}")
        print(f"  - 新客减免金额:   ¥{total_new_customer:>15,.2f}")
        print(f"  + 企客后返:       ¥{total_enterprise:>15,.2f}")
        print(f"{'═' * 80}")
        print(f"= 订单实际利润:     ¥{total_profit:>15,.2f}")
        print(f"\n利润率: {(total_profit / total_revenue * 100):.2f}%")
        
    else:
        print("\n未找到美团相关数据")
else:
    print("\n数据中没有'渠道'字段")

print("\n" + "=" * 80)
print("查询完成")
print("=" * 80)
