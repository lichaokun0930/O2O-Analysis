# -*- coding: utf-8 -*-
import pandas as pd
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

df = pd.read_excel('实际数据/金寨.xlsx')
df_meituan = df[df['渠道'] == '美团闪购'].copy()

print("=" * 80)
print("深度分析：原始'利润额'字段的计算公式")
print("=" * 80)

# 随机抽取10个订单样本
sample_orders = df_meituan['订单ID'].unique()[:10]

print(f"\n分析 {len(sample_orders)} 个订单样本...\n")

for order_id in sample_orders:
    order_data = df_meituan[df_meituan['订单ID'] == order_id]
    
    # 获取各字段值
    预计订单收入 = order_data['预计订单收入'].sum()
    商品实售价 = order_data['商品实售价'].sum()
    成本 = order_data['成本'].sum()
    平台佣金 = order_data['平台佣金'].iloc[0]
    物流配送费 = order_data['物流配送费'].iloc[0]
    配送费减免 = order_data['配送费减免金额'].iloc[0]
    用户支付配送费 = order_data['用户支付配送费'].iloc[0]
    原始利润额_单个 = order_data['利润额'].iloc[0]
    原始利润额_总和 = order_data['利润额'].sum()
    
    # 尝试各种公式
    公式A = 商品实售价 - 成本  # 只算商品毛利
    公式B = 商品实售价 - 成本 - 平台佣金  # 商品毛利 - 佣金
    公式C = 预计订单收入 - 成本 - 平台佣金  # 订单收入 - 成本 - 佣金
    公式D = 预计订单收入 - 成本 - 平台佣金 - 物流配送费  # 不含配送费优化
    公式E = 预计订单收入 - 成本 - 平台佣金 + 用户支付配送费 - 物流配送费  # 部分新公式
    
    # 找到最接近的公式
    diffs = {
        'A(商品毛利)': abs(公式A - 原始利润额_单个),
        'B(毛利-佣金)': abs(公式B - 原始利润额_单个),
        'C(收入-成本-佣金)': abs(公式C - 原始利润额_单个),
        'D(C-配送费)': abs(公式D - 原始利润额_单个),
        'E(部分新公式)': abs(公式E - 原始利润额_单个),
    }
    
    best_match = min(diffs, key=diffs.get)
    
    if diffs[best_match] < 0.01:
        print(f"订单{order_id}: 原始利润额=¥{原始利润额_单个:.2f}, 匹配公式={best_match}")

print("\n" + "=" * 80)
print("按订单去重聚合分析")
print("=" * 80)

# 按订单聚合，取first()来去重
order_level = df_meituan.groupby('订单ID').agg({
    '利润额': 'first',  # 订单级字段，取第一个
    '预计订单收入': 'sum',  # 商品级字段，求和
    '商品实售价': 'sum',
    '成本': 'sum',
    '平台佣金': 'first',
    '物流配送费': 'first',
    '配送费减免金额': 'first',
    '用户支付配送费': 'first',
}).reset_index()

# 计算各种可能的公式
order_level['公式A'] = order_level['商品实售价'] - order_level['成本']
order_level['公式B'] = order_level['商品实售价'] - order_level['成本'] - order_level['平台佣金']
order_level['公式C'] = order_level['预计订单收入'] - order_level['成本'] - order_level['平台佣金']

# 统计匹配情况
匹配A = (abs(order_level['利润额'] - order_level['公式A']) < 0.01).sum()
匹配B = (abs(order_level['利润额'] - order_level['公式B']) < 0.01).sum()
匹配C = (abs(order_level['利润额'] - order_level['公式C']) < 0.01).sum()

print(f"\n总订单数: {len(order_level)}")
print(f"匹配公式A(商品毛利): {匹配A} 单 ({匹配A/len(order_level)*100:.1f}%)")
print(f"匹配公式B(毛利-佣金): {匹配B} 单 ({匹配B/len(order_level)*100:.1f}%)")
print(f"匹配公式C(收入-成本-佣金): {匹配C} 单 ({匹配C/len(order_level)*100:.1f}%)")

# 找出最匹配的公式
if 匹配A == len(order_level):
    print("\n✅ 原始'利润额' = 商品实售价 - 成本")
    correct_formula = '公式A'
elif 匹配B == len(order_level):
    print("\n✅ 原始'利润额' = 商品实售价 - 成本 - 平台佣金")
    correct_formula = '公式B'
elif 匹配C == len(order_level):
    print("\n✅ 原始'利润额' = 预计订单收入 - 成本 - 平台佣金")
    correct_formula = '公式C'
else:
    print("\n❓ 原始'利润额'使用了其他公式")
    correct_formula = None

# 如果找到了正确公式，计算看板应该显示的值
if correct_formula:
    看板使用的利润 = order_level['利润额'].sum()
    print(f"\n看板应该显示的利润额: ¥{看板使用的利润:,.2f}")
    print(f"与实际看板显示(¥17,600)的差异: ¥{abs(看板使用的利润 - 17600):,.2f}")
