"""
检查枫瑞店Excel源数据的详细信息
"""
import pandas as pd

file_path = '实际数据/枫瑞.xlsx'

# 检查Excel文件的所有sheet
xl_file = pd.ExcelFile(file_path)
print("=" * 80)
print(f"📂 文件: {file_path}")
print("=" * 80)
print(f"\nSheet列表: {xl_file.sheet_names}")

# 读取第一个sheet
df = pd.read_excel(file_path)
print(f"\n原始数据:")
print(f"  总行数: {len(df)}")
print(f"  总列数: {len(df.columns)}")

# 检查渠道字段
if '渠道' in df.columns:
    print(f"\n渠道分布(未剔除耗材):")
    channel_dist = df['渠道'].value_counts()
    for ch, cnt in channel_dist.items():
        channel_data = df[df['渠道'] == ch]
        profit = channel_data['利润额'].sum()
        orders = channel_data['订单ID'].nunique()
        print(f"  {ch}: {cnt}行, {orders}单, 利润额={profit:.2f}")

# 剔除耗材后
if '一级分类名' in df.columns:
    df_clean = df[df['一级分类名'] != '耗材'].copy()
    print(f"\n剔除耗材后:")
    print(f"  总行数: {len(df_clean)}")
    
    if '渠道' in df_clean.columns:
        print(f"\n渠道分布(剔除耗材后):")
        channel_dist = df_clean['渠道'].value_counts()
        for ch, cnt in channel_dist.items():
            channel_data = df_clean[df_clean['渠道'] == ch]
            profit = channel_data['利润额'].sum()
            orders = channel_data['订单ID'].nunique()
            print(f"  {ch}: {cnt}行, {orders}单, 利润额={profit:.2f}")

# 专门检查美团共橙
mt_data = df_clean[df_clean['渠道'] == '美团共橙'].copy()
print(f"\n🎯 美团共橙详细数据:")
print(f"  数据行数: {len(mt_data)}")
print(f"  订单数: {mt_data['订单ID'].nunique()}")
print(f"  利润额(直接sum): {mt_data['利润额'].sum():.2f}")

# 按订单聚合检查
order_profit = mt_data.groupby('订单ID')['利润额'].sum()
print(f"  利润额(聚合后): {order_profit.sum():.2f}")

# 检查你说的31176
print(f"\n💡 数据对比:")
print(f"  你说的利润额: 31,176")
print(f"  我计算的利润额: {order_profit.sum():.2f}")
print(f"  差异: {abs(31176 - order_profit.sum()):.2f}")

# 检查是否有特殊字符或空格
print(f"\n🔍 检查渠道字段是否有特殊字符:")
unique_channels = df['渠道'].unique()
for ch in unique_channels:
    print(f"  '{ch}' (长度={len(str(ch))})")

# 你能否告诉我你是怎么筛选的?
print(f"\n❓ 请确认:")
print(f"  1. 你用的Excel文件是 '实际数据/枫瑞.xlsx' 吗?")
print(f"  2. 你筛选的条件是: 渠道='美团共橙' + 剔除耗材 吗?")
print(f"  3. 你的利润额31,176是哪个字段的sum?")
