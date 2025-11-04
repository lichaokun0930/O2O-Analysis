"""测试价格范围分布"""
import pandas as pd
import sys

# 加载数据
excel_file = "实际数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"
df = pd.read_excel(excel_file)

# 标准化字段
df['日期'] = pd.to_datetime(df['下单时间'])

# 过滤耗材
df = df[df['一级分类名'] != '耗材']

# 过滤咖啡渠道
if '渠道' in df.columns:
    coffee_channels = ['饿了么咖啡', '美团咖啡']
    df = df[~df['渠道'].isin(coffee_channels)]

print(f"数据行数: {len(df)}")

# 检查价格分布
if '商品实售价' in df.columns:
    # 转换为数值
    df['商品实售价'] = pd.to_numeric(df['商品实售价'], errors='coerce')
    
    print(f"\n价格统计:")
    print(f"最小价格: {df['商品实售价'].min():.2f}元")
    print(f"最大价格: {df['商品实售价'].max():.2f}元")
    print(f"平均价格: {df['商品实售价'].mean():.2f}元")
    print(f"中位数: {df['商品实售价'].median():.2f}元")
    
    # 价格区间分布
    print(f"\n价格区间分布:")
    print(f"0-10元: {len(df[df['商品实售价'] <= 10])} 个")
    print(f"10-30元: {len(df[(df['商品实售价'] > 10) & (df['商品实售价'] <= 30)])} 个")
    print(f"30-50元: {len(df[(df['商品实售价'] > 30) & (df['商品实售价'] <= 50)])} 个")
    print(f"50-100元: {len(df[(df['商品实售价'] > 50) & (df['商品实售价'] <= 100)])} 个")
    print(f"100元以上: {len(df[df['商品实售价'] > 100])} 个")
    
    # 检查价格>100的占比
    over_100 = len(df[df['商品实售价'] > 100])
    total = len(df)
    pct = over_100 / total * 100
    print(f"\n💡 价格超过100元的商品: {over_100}个 ({pct:.2f}%)")
    print(f"   如果价格筛选设为 [0, 100]，这些商品会被过滤掉！")
else:
    print("未找到'商品实售价'字段")
