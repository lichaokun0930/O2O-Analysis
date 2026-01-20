# -*- coding: utf-8 -*-
"""
检查六象限重复数据问题
"""
import pandas as pd
import sys

print("="*80)
print("检查六象限重复数据")
print("="*80)

# 从主模块导入
sys.path.insert(0, '.')

try:
    # 导入数据加载函数
    from database.connection import engine
    
    print("\n1. 加载数据...")
    with engine.connect() as conn:
        df = pd.read_sql('SELECT * FROM orders ORDER BY order_date DESC LIMIT 10000', conn)
    
    print(f"   数据加载成功: {len(df)} 条记录")
    
    # 字段映射
    field_mapping = {
        'order_date': '日期',
        'product_name': '商品名称',
        'store_code': '店内码',
        'platform': '渠道',
        'quantity': '月售',
        'category_level1': '一级分类名',
        'actual_price': '实收价格',
        'product_cost': '商品采购成本',
        'profit': '利润额',
        'order_id': '订单ID'
    }
    
    rename_dict = {k: v for k, v in field_mapping.items() if k in df.columns}
    df = df.rename(columns=rename_dict)
    
    print(f"\n2. 检查商品分组情况...")
    
    # 检查店内码的有效性
    if '店内码' in df.columns:
        valid_ratio = df['店内码'].notna().sum() / len(df)
        print(f"   店内码有效率: {valid_ratio:.1%}")
        
        # 检查同一商品名称是否有多个店内码
        if '商品名称' in df.columns:
            name_code_map = df[df['店内码'].notna()].groupby('商品名称')['店内码'].nunique()
            multi_code_products = name_code_map[name_code_map > 1]
            if len(multi_code_products) > 0:
                print(f"\n   ⚠️ 发现 {len(multi_code_products)} 个商品有多个店内码:")
                for product, count in multi_code_products.head(5).items():
                    codes = df[df['商品名称'] == product]['店内码'].unique()
                    print(f"      - {product}: {count}个店内码 {codes[:3]}")
    
    # 检查渠道情况
    if '渠道' in df.columns:
        unique_channels = df['渠道'].nunique()
        print(f"\n   渠道数量: {unique_channels}")
        print(f"   渠道列表: {df['渠道'].unique()[:10].tolist()}")
        
        # 检查同一商品在不同渠道的价格差异
        if '商品名称' in df.columns and '实收价格' in df.columns:
            price_by_channel = df.groupby(['商品名称', '渠道'])['实收价格'].mean().reset_index()
            price_variance = price_by_channel.groupby('商品名称')['实收价格'].std().fillna(0)
            has_diff = price_variance[price_variance > 0.1]
            
            if len(has_diff) > 0:
                print(f"\n   ⚠️ 发现 {len(has_diff)} 个商品在不同渠道价格不同:")
                for product in has_diff.head(5).index:
                    prices = price_by_channel[price_by_channel['商品名称'] == product]
                    print(f"      - {product}:")
                    for _, row in prices.iterrows():
                        print(f"        {row['渠道']}: ¥{row['实收价格']:.2f}")
    
    # 模拟商品聚合
    print(f"\n3. 模拟商品聚合...")
    
    sales_col = '月售' if '月售' in df.columns else '销量'
    
    # 方案1：只按商品名称分组
    if '商品名称' in df.columns and sales_col in df.columns:
        group1 = df.groupby('商品名称')[sales_col].sum().reset_index()
        print(f"   方案1（按商品名称）: {len(group1)} 个商品")
    
    # 方案2：按店内码+商品名称分组
    if '店内码' in df.columns and '商品名称' in df.columns and sales_col in df.columns:
        df_with_code = df[df['店内码'].notna()]
        group2 = df_with_code.groupby(['店内码', '商品名称'])[sales_col].sum().reset_index()
        print(f"   方案2（按店内码+商品名称）: {len(group2)} 个商品")
    
    # 方案3：按店内码+商品名称+渠道分组
    if '店内码' in df.columns and '商品名称' in df.columns and '渠道' in df.columns and sales_col in df.columns:
        df_with_code = df[df['店内码'].notna()]
        group3 = df_with_code.groupby(['店内码', '商品名称', '渠道'])[sales_col].sum().reset_index()
        print(f"   方案3（按店内码+商品名称+渠道）: {len(group3)} 个商品")
        
        # 检查是否有重复的商品名称
        name_counts = group3['商品名称'].value_counts()
        duplicates = name_counts[name_counts > 1]
        if len(duplicates) > 0:
            print(f"\n   ⚠️ 方案3中有 {len(duplicates)} 个商品名称出现多次:")
            for product, count in duplicates.head(10).items():
                print(f"      - {product}: 出现{count}次")
                details = group3[group3['商品名称'] == product]
                for _, row in details.iterrows():
                    print(f"        店内码:{row.get('店内码', 'N/A')}, 渠道:{row.get('渠道', 'N/A')}, 销量:{row[sales_col]}")
    
    print(f"\n4. 结论:")
    print(f"   如果方案3的商品数量明显多于方案1，说明同一商品因为:")
    print(f"   - 不同店内码（同名不同规格）")
    print(f"   - 不同渠道（跨渠道价格差异）")
    print(f"   被分成了多行，这可能导致六象限表格中出现重复的商品名称")

except Exception as e:
    print(f"\n错误: {str(e)}")
    import traceback
    traceback.print_exc()
