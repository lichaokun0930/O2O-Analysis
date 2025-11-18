# -*- coding: utf-8 -*-
import pandas as pd
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

df = pd.read_excel('实际数据/金寨.xlsx')

print("=" * 80)
print("详细对比分析 - 美团闪购渠道利润计算")
print("=" * 80)

# 筛选美团闪购数据
df_mt = df[df['渠道'] == '美团闪购'].copy()
print(f"\n美团闪购数据: {len(df_mt)} 行")
print(f"订单数: {df_mt['订单ID'].nunique()} 单")

# 查看原始数据中的"利润额"字段
if '利润额' in df_mt.columns:
    original_profit = df_mt['利润额'].sum()
    print(f"\n原始数据中的'利润额'字段总和: ¥{original_profit:,.2f}")
    print("(这是Excel中计算好的利润额)")

# 按订单聚合
print("\n" + "=" * 80)
print("按订单聚合各项金额")
print("=" * 80)

# 填充空值
df_mt['物流配送费'] = df_mt['物流配送费'].fillna(0)
df_mt['配送费减免金额'] = df_mt['配送费减免金额'].fillna(0)
df_mt['用户支付配送费'] = df_mt['用户支付配送费'].fillna(0)

# 订单级聚合
agg_dict = {
    '预计订单收入': 'sum',          # 商品级，sum
    '成本': 'sum',                   # 商品级，sum
    '平台佣金': 'first',             # 订单级，first
    '物流配送费': 'first',           # 订单级，first
    '配送费减免金额': 'first',       # 订单级，first
    '用户支付配送费': 'first',       # 订单级，first
    '新客减免金额': 'first' if '新客减免金额' in df_mt.columns else lambda x: 0,
    '企客后返': 'sum' if '企客后返' in df_mt.columns else lambda x: 0,
}

if '利润额' in df_mt.columns:
    agg_dict['利润额'] = 'sum'  # 商品级，sum

order_agg = df_mt.groupby('订单ID').agg(agg_dict).reset_index()

print(f"\n聚合后订单数: {len(order_agg)}")

# 显示聚合后的总金额
print("\n聚合后各字段总和:")
print(f"  预计订单收入: ¥{order_agg['预计订单收入'].sum():,.2f}")
print(f"  成本:         ¥{order_agg['成本'].sum():,.2f}")
print(f"  平台佣金:     ¥{order_agg['平台佣金'].sum():,.2f}")
print(f"  物流配送费:   ¥{order_agg['物流配送费'].sum():,.2f}")
print(f"  配送费减免:   ¥{order_agg['配送费减免金额'].sum():,.2f}")
print(f"  用户支付配送: ¥{order_agg['用户支付配送费'].sum():,.2f}")
print(f"  新客减免:     ¥{order_agg['新客减免金额'].sum():,.2f}")
print(f"  企客后返:     ¥{order_agg['企客后返'].sum():,.2f}")

if '利润额' in order_agg.columns:
    print(f"  利润额(原始): ¥{order_agg['利润额'].sum():,.2f}")

# 方法1: 使用原始"利润额"字段
print("\n" + "=" * 80)
print("方法1: 使用原始数据中的'利润额'字段")
print("=" * 80)

if '利润额' in order_agg.columns:
    profit_method1 = order_agg['利润额'].sum()
    profit_method1_final = profit_method1 - order_agg['新客减免金额'].sum() + order_agg['企客后返'].sum()
    
    print(f"\n利润额(原始):       ¥{profit_method1:,.2f}")
    print(f"  - 新客减免金额:   ¥{order_agg['新客减免金额'].sum():,.2f}")
    print(f"  + 企客后返:       ¥{order_agg['企客后返'].sum():,.2f}")
    print(f"= 订单实际利润:     ¥{profit_method1_final:,.2f}")

# 方法2: 重新计算利润额
print("\n" + "=" * 80)
print("方法2: 按新公式重新计算利润额")
print("=" * 80)

order_agg['利润额_新'] = (
    order_agg['预计订单收入'] - 
    order_agg['成本'] - 
    order_agg['平台佣金'] - 
    order_agg['物流配送费'] - 
    order_agg['配送费减免金额'] + 
    order_agg['用户支付配送费']
)

order_agg['订单实际利润_新'] = (
    order_agg['利润额_新'] - 
    order_agg['新客减免金额'] + 
    order_agg['企客后返']
)

profit_method2_base = order_agg['利润额_新'].sum()
profit_method2 = order_agg['订单实际利润_新'].sum()

print(f"\n利润额(重新计算):   ¥{profit_method2_base:,.2f}")
print(f"  - 新客减免金额:   ¥{order_agg['新客减免金额'].sum():,.2f}")
print(f"  + 企客后返:       ¥{order_agg['企客后返'].sum():,.2f}")
print(f"= 订单实际利润:     ¥{profit_method2:,.2f}")

# 对比差异
print("\n" + "=" * 80)
print("差异分析")
print("=" * 80)

if '利润额' in order_agg.columns:
    diff_base = profit_method1 - profit_method2_base
    diff_final = profit_method1_final - profit_method2
    
    print(f"\n利润额差异:         ¥{diff_base:,.2f}")
    print(f"订单实际利润差异:   ¥{diff_final:,.2f}")
    
    print("\n可能原因:")
    print("1. 原始'利润额'字段的计算公式可能不同")
    print("2. 聚合方式可能有差异（sum vs first）")
    
    # 分析原始利润额字段的计算逻辑
    print("\n" + "=" * 80)
    print("尝试反推原始'利润额'字段的计算公式")
    print("=" * 80)
    
    # 选取前几条订单详细分析
    sample_orders = df_mt['订单ID'].unique()[:5]
    
    for order_id in sample_orders:
        order_data = df_mt[df_mt['订单ID'] == order_id]
        order_summary = order_agg[order_agg['订单ID'] == order_id].iloc[0]
        
        print(f"\n订单 {order_id}:")
        print(f"  商品行数: {len(order_data)}")
        print(f"  原始利润额(每行): {order_data['利润额'].values}")
        print(f"  原始利润额总和: ¥{order_data['利润额'].sum():.2f}")
        print(f"  聚合后利润额: ¥{order_summary['利润额']:.2f}")
        print(f"  重新计算利润额: ¥{order_summary['利润额_新']:.2f}")
        
        # 查看配送相关字段
        print(f"  物流配送费(每行): {order_data['物流配送费'].values}")
        print(f"  配送费减免(每行): {order_data['配送费减免金额'].values}")
        print(f"  用户支付配送(每行): {order_data['用户支付配送费'].values}")

print("\n" + "=" * 80)
print("分析完成")
print("=" * 80)

# 总结您的数据和我的数据
print("\n总结:")
print(f"您计算的利润: ¥14,247.00")
print(f"我方法1计算:  ¥{profit_method1_final if '利润额' in order_agg.columns else 0:,.2f} (使用原始利润额字段)")
print(f"我方法2计算:  ¥{profit_method2:,.2f} (重新计算)")
print(f"\n差异(您-方法1): ¥{14247 - (profit_method1_final if '利润额' in order_agg.columns else 0):,.2f}")
print(f"差异(您-方法2): ¥{14247 - profit_method2:,.2f}")
