# -*- coding: utf-8 -*-
import pandas as pd
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

df = pd.read_excel('实际数据/金寨.xlsx')

print("=" * 80)
print("对比分析：看板显示¥17,600 vs 计算结果¥10,730.82")
print("=" * 80)

# 筛选美团闪购
df_meituan = df[df['渠道'] == '美团闪购'].copy()
print(f"\n美团闪购数据: {len(df_meituan)} 行, {df_meituan['订单ID'].nunique()} 单")

# 方法1: 直接从原始数据聚合（可能是看板的老方法）
print("\n" + "=" * 80)
print("方法1: 直接从原始数据聚合'利润额'字段")
print("=" * 80)

if '利润额' in df_meituan.columns:
    # 直接求和利润额字段
    method1_profit = df_meituan['利润额'].sum()
    print(f"利润额字段直接求和: ¥{method1_profit:,.2f}")
    
    # 按订单去重后求和
    order_profit = df_meituan.groupby('订单ID')['利润额'].first().sum()
    print(f"按订单去重后求和: ¥{order_profit:,.2f}")
else:
    print("数据中没有'利润额'字段")
    method1_profit = 0

# 方法2: 按新公式计算
print("\n" + "=" * 80)
print("方法2: 按新公式计算（订单级聚合）")
print("=" * 80)

# 订单级聚合
agg_dict = {
    '预计订单收入': 'sum',
    '成本': 'sum',
    '平台佣金': 'first',
    '物流配送费': 'first',
    '配送费减免金额': 'first',
    '用户支付配送费': 'first',
}

if '新客减免金额' in df_meituan.columns:
    agg_dict['新客减免金额'] = 'first'
if '企客后返' in df_meituan.columns:
    agg_dict['企客后返'] = 'sum'

order_agg = df_meituan.groupby('订单ID').agg(agg_dict).reset_index()

# 计算利润
order_agg['利润额_新'] = (
    order_agg['预计订单收入'] - 
    order_agg['成本'] - 
    order_agg['平台佣金'] - 
    order_agg['物流配送费'] - 
    order_agg['配送费减免金额'] + 
    order_agg['用户支付配送费']
)

order_agg['订单实际利润'] = (
    order_agg['利润额_新'] - 
    order_agg.get('新客减免金额', 0) + 
    order_agg.get('企客后返', 0)
)

method2_profit = order_agg['订单实际利润'].sum()
print(f"订单实际利润: ¥{method2_profit:,.2f}")

# 方法3: 检查原始数据中的"利润额"是如何计算的
print("\n" + "=" * 80)
print("方法3: 分析原始数据'利润额'字段的计算逻辑")
print("=" * 80)

if '利润额' in df_meituan.columns:
    # 取一个订单样本分析
    sample_order = df_meituan['订单ID'].iloc[0]
    sample_data = df_meituan[df_meituan['订单ID'] == sample_order]
    
    print(f"\n样本订单: {sample_order}")
    print(f"商品数: {len(sample_data)}")
    print("\n各字段值:")
    
    fields_to_check = ['预计订单收入', '成本', '平台佣金', '物流配送费', 
                       '配送费减免金额', '用户支付配送费', '利润额',
                       '新客减免金额', '企客后返']
    
    for field in fields_to_check:
        if field in sample_data.columns:
            values = sample_data[field].values
            print(f"  {field}: {values} (sum={values.sum():.2f})")
    
    # 验证原始利润额计算公式
    if '利润额' in sample_data.columns:
        原始利润额 = sample_data['利润额'].iloc[0]
        
        # 尝试反推公式
        预计订单收入 = sample_data['预计订单收入'].sum()
        成本 = sample_data['成本'].sum()
        平台佣金 = sample_data['平台佣金'].iloc[0]
        物流配送费 = sample_data['物流配送费'].iloc[0]
        配送费减免 = sample_data['配送费减免金额'].iloc[0]
        用户支付配送费 = sample_data['用户支付配送费'].iloc[0]
        
        # 可能的公式1: 预计订单收入 - 成本 - 平台佣金 - 物流配送费
        formula1 = 预计订单收入 - 成本 - 平台佣金 - 物流配送费
        
        # 可能的公式2: 预计订单收入 - 成本 - 平台佣金 - 物流配送费 + 用户支付配送费
        formula2 = 预计订单收入 - 成本 - 平台佣金 - 物流配送费 + 用户支付配送费
        
        # 可能的公式3: 包含配送费减免
        formula3 = 预计订单收入 - 成本 - 平台佣金 - 物流配送费 - 配送费减免 + 用户支付配送费
        
        print(f"\n原始'利润额'字段值: ¥{原始利润额:.2f}")
        print(f"公式1 (收入-成本-佣金-配送费): ¥{formula1:.2f} 【差异: ¥{abs(formula1-原始利润额):.2f}】")
        print(f"公式2 (公式1+用户配送费): ¥{formula2:.2f} 【差异: ¥{abs(formula2-原始利润额):.2f}】")
        print(f"公式3 (新公式): ¥{formula3:.2f} 【差异: ¥{abs(formula3-原始利润额):.2f}】")
        
        if abs(formula1 - 原始利润额) < 0.01:
            print("\n⚠️ 原始'利润额'使用公式1（老公式，不含配送费相关）")
        elif abs(formula2 - 原始利润额) < 0.01:
            print("\n⚠️ 原始'利润额'使用公式2（部分新公式，不含配送费减免）")
        elif abs(formula3 - 原始利润额) < 0.01:
            print("\n✅ 原始'利润额'使用公式3（新公式）")
        else:
            print("\n❓ 原始'利润额'使用未知公式")

# 汇总对比
print("\n" + "=" * 80)
print("汇总对比")
print("=" * 80)
print(f"\n看板显示:          ¥17,600.00")
print(f"方法1(原始字段):    ¥{method1_profit:,.2f}")
print(f"方法2(新公式):      ¥{method2_profit:,.2f}")
print(f"\n差异1(看板-原始):   ¥{17600 - method1_profit:,.2f}")
print(f"差异2(看板-新公式): ¥{17600 - method2_profit:,.2f}")
print(f"差异3(原始-新公式): ¥{method1_profit - method2_profit:,.2f}")

print("\n" + "=" * 80)
print("可能原因分析")
print("=" * 80)
print("1. 看板可能使用了原始数据的'利润额'字段，而不是按新公式计算")
print("2. 原始'利润额'字段可能不包含配送费减免、新客减免等调整项")
print("3. 新旧公式的差异导致了利润额的不同")
