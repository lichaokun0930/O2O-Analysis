import pandas as pd

# 读取祥和路源数据
df = pd.read_excel(r'd:\Python1\O2O_Analysis\O2O数据分析\测算模型\实际数据\祥和路.xlsx')

print(f"="*80)
print(f"📊 祥和路源数据分析")
print(f"="*80)
print(f"\n数据行数: {len(df):,}")
print(f"\n字段列表 ({len(df.columns)} 个):")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. {col}")

# 检查成本字段
if '商品采购成本' in df.columns:
    total_cost = df['商品采购成本'].sum()
    print(f"\n💰 商品采购成本统计:")
    print(f"   总和: ¥{total_cost:,.2f}")
    print(f"   均值: ¥{df['商品采购成本'].mean():,.2f}")
    print(f"   最大值: ¥{df['商品采购成本'].max():,.2f}")
    print(f"   最小值: ¥{df['商品采购成本'].min():,.2f}")
    print(f"   缺失值: {df['商品采购成本'].isna().sum()}")
else:
    print(f"\n❌ 未找到'商品采购成本'字段")

# 检查一级分类
if '一级分类名' in df.columns:
    print(f"\n📋 一级分类统计:")
    category_cost = df.groupby('一级分类名')['商品采购成本'].sum()
    for category, cost in category_cost.items():
        count = len(df[df['一级分类名'] == category])
        print(f"   {category}: {count:,} 行, 成本: ¥{cost:,.2f}")
    
    # 检查耗材成本
    if '耗材' in df['一级分类名'].values:
        consumable_cost = df[df['一级分类名'] == '耗材']['商品采购成本'].sum()
        consumable_rows = len(df[df['一级分类名'] == '耗材'])
        print(f"\n🔍 耗材成本详细:")
        print(f"   耗材行数: {consumable_rows:,}")
        print(f"   耗材成本: ¥{consumable_cost:,.2f}")
        
        non_consumable_cost = df[df['一级分类名'] != '耗材']['商品采购成本'].sum()
        print(f"   非耗材成本: ¥{non_consumable_cost:,.2f}")
        print(f"   验证: {consumable_cost:.2f} + {non_consumable_cost:.2f} = {consumable_cost + non_consumable_cost:.2f}")

# 检查订单ID
if '订单ID' in df.columns:
    print(f"\n📦 订单统计:")
    print(f"   唯一订单数: {df['订单ID'].nunique():,}")
    print(f"   订单ID类型: {df['订单ID'].dtype}")
    
    # 按订单聚合成本
    order_cost = df.groupby('订单ID')['商品采购成本'].sum()
    print(f"   订单级成本总和: ¥{order_cost.sum():,.2f}")
    print(f"   商品级成本总和: ¥{df['商品采购成本'].sum():,.2f}")
    print(f"   差异: ¥{abs(order_cost.sum() - df['商品采购成本'].sum()):,.2f}")

print(f"\n前5行数据预览:")
print(df.head())

print(f"\n="*80)
