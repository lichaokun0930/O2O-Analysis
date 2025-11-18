# -*- coding: utf-8 -*-
import pandas as pd
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, '.')

# 模拟看板的数据加载流程
print("=" * 80)
print("模拟看板数据加载和计算流程")
print("=" * 80)

# Step 1: 加载原始数据
df = pd.read_excel('实际数据/金寨.xlsx')
print(f"\n1. 原始数据: {len(df)} 行")

# Step 2: 检查是否剔除耗材和咖啡
耗材数据 = df[df['一级分类名'] == '耗材']
print(f"2. 耗材数据: {len(耗材数据)} 行")

咖啡渠道 = ['饿了么咖啡', '美团咖啡']
咖啡数据 = df[df['渠道'].isin(咖啡渠道)]
print(f"3. 咖啡渠道数据: {len(咖啡数据)} 行")

# Step 3: 剔除后的数据
df_filtered = df[
    (df['一级分类名'] != '耗材') & 
    (~df['渠道'].isin(咖啡渠道))
].copy()
print(f"4. 剔除后数据: {len(df_filtered)} 行")

# Step 4: 检查美团闪购数据
df_meituan = df_filtered[df_filtered['渠道'] == '美团闪购'].copy()
print(f"5. 美团闪购数据: {len(df_meituan)} 行, {df_meituan['订单ID'].nunique()} 单")

# Step 5: 导入calculate_order_metrics函数
print("\n" + "=" * 80)
print("调用 calculate_order_metrics() 计算")
print("=" * 80)

# 手动实现calculate_order_metrics的逻辑
df_meituan['物流配送费'] = df_meituan['物流配送费'].fillna(0)
df_meituan['配送费减免金额'] = df_meituan['配送费减免金额'].fillna(0)
df_meituan['用户支付配送费'] = df_meituan['用户支付配送费'].fillna(0)

agg_dict = {
    '商品实售价': 'sum',
    '预计订单收入': 'sum',
    '用户支付配送费': 'first',
    '配送费减免金额': 'first',
    '物流配送费': 'first',
    '平台佣金': 'first',
    '成本': 'sum',
}

# 可选字段
for field in ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', '打包袋金额',
              '满赠金额', '商家其他优惠', '新客减免金额']:
    if field in df_meituan.columns:
        agg_dict[field] = 'first'

if '企客后返' in df_meituan.columns:
    agg_dict['企客后返'] = 'sum'

order_agg = df_meituan.groupby('订单ID').agg(agg_dict).reset_index()

# 计算配送净成本
order_agg['配送净成本'] = (
    order_agg['物流配送费'] - 
    order_agg['配送费减免金额'] + 
    order_agg['用户支付配送费']
)

# 计算利润额
order_agg['利润额'] = (
    order_agg['预计订单收入'] - 
    order_agg['成本'] - 
    order_agg['平台佣金'] - 
    order_agg['物流配送费'] - 
    order_agg['配送费减免金额'] + 
    order_agg['用户支付配送费']
)

# 计算商家活动成本
order_agg['商家活动成本'] = (
    order_agg.get('满减金额', 0) + 
    order_agg.get('商品减免金额', 0) + 
    order_agg.get('商家代金券', 0) +
    order_agg.get('商家承担部分券', 0) +
    order_agg.get('满赠金额', 0) +
    order_agg.get('商家其他优惠', 0)
)

# 计算订单实际利润
order_agg['订单实际利润'] = (
    order_agg['利润额'] -
    order_agg.get('新客减免金额', 0) +
    order_agg.get('企客后返', 0)
)

print(f"\n订单聚合完成: {len(order_agg)} 单")

# Step 6: 按渠道聚合（模拟看板逻辑）
print("\n" + "=" * 80)
print("按渠道聚合（模拟看板显示）")
print("=" * 80)

total_profit = order_agg['订单实际利润'].sum()
total_revenue = order_agg['预计订单收入'].sum()
total_orders = len(order_agg)

print(f"\n美团闪购渠道:")
print(f"  订单数: {total_orders:,} 单")
print(f"  预计订单收入: ¥{total_revenue:,.2f}")
print(f"  订单实际利润: ¥{total_profit:,.2f}")
print(f"  利润率: {(total_profit/total_revenue*100):.2f}%")

print(f"\n与看板显示(¥17,600)的差异: ¥{abs(total_profit - 17600):,.2f}")

# 检查数据来源差异
print("\n" + "=" * 80)
print("可能的差异原因")
print("=" * 80)
print("1. 检查看板加载的是否是同一个文件")
print("2. 检查数据筛选条件（耗材、咖啡渠道等）")
print("3. 检查时间范围筛选")
print("4. 检查是否有其他数据预处理步骤")
