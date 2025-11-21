"""调试祥和路店数据问题"""
import pandas as pd
import numpy as np
from 订单数据处理器 import OrderDataProcessor

# 初始化处理器
processor = OrderDataProcessor()

# 加载祥和路店数据
try:
    df = processor.读取订单数据(门店名称='祥和路店')
    
    print("=" * 80)
    print("祥和路店数据加载成功")
    print("=" * 80)
    print(f"\n数据形状: {df.shape}")
    print(f"\n所有列名:\n{df.columns.tolist()}")
    
    # 检查关键字段
    print("\n" + "=" * 80)
    print("关键字段检查:")
    print("=" * 80)
    
    critical_fields = ['商品名称', '一级分类名', '库存', '日期', '月售']
    for field in critical_fields:
        if field in df.columns:
            print(f"✅ {field} 存在")
            print(f"   - 数据类型: {df[field].dtype}")
            print(f"   - 非空数量: {df[field].notna().sum()}/{len(df)}")
            if field == '库存':
                print(f"   - 库存统计: 最小={df[field].min()}, 最大={df[field].max()}, 平均={df[field].mean():.2f}")
                print(f"   - 库存>0的商品数: {(df[field] > 0).sum()}")
                print(f"   - 库存=0的商品数: {(df[field] == 0).sum()}")
            elif field == '月售':
                print(f"   - 月售统计: 最小={df[field].min()}, 最大={df[field].max()}, 总和={df[field].sum()}")
                print(f"   - 月售>0的记录数: {(df[field] > 0).sum()}/{len(df)}")
        else:
            print(f"❌ {field} 不存在")
    
    # 检查日期字段
    print("\n" + "=" * 80)
    print("日期字段详细检查:")
    print("=" * 80)
    
    date_fields = ['日期', '下单时间', '创建时间']
    for field in date_fields:
        if field in df.columns:
            print(f"\n{field}:")
            print(f"  - 数据类型: {df[field].dtype}")
            print(f"  - 样例: {df[field].head(3).tolist()}")
            if pd.api.types.is_datetime64_any_dtype(df[field]):
                print(f"  - 日期范围: {df[field].min()} 到 {df[field].max()}")
            
    # 检查分类数据
    print("\n" + "=" * 80)
    print("分类统计:")
    print("=" * 80)
    if '一级分类名' in df.columns:
        print(f"\n一级分类数量: {df['一级分类名'].nunique()}")
        print(f"分类列表:\n{df['一级分类名'].value_counts()}")
    
    # 检查每个分类的库存情况
    if '库存' in df.columns and '一级分类名' in df.columns:
        print("\n" + "=" * 80)
        print("各分类库存情况:")
        print("=" * 80)
        
        # 获取最后一天的数据
        last_date = df['日期'].max() if '日期' in df.columns else df['下单时间'].max()
        last_day_data = df[df['日期'] == last_date] if '日期' in df.columns else df[df['下单时间'] == last_date]
        
        category_stock = last_day_data.groupby('一级分类名').agg({
            '库存': ['sum', 'mean', 'count'],
            '商品名称': 'nunique'
        })
        print("\n各分类库存汇总:")
        print(category_stock)
        
    # 模拟滞销品计算
    print("\n" + "=" * 80)
    print("滞销品计算测试:")
    print("=" * 80)
    
    if '日期' in df.columns and '商品名称' in df.columns:
        last_date = df['日期'].max()
        print(f"\n数据最后日期: {last_date}")
        
        # 计算每个商品的最后销售日期
        product_last_sale = df.groupby('商品名称')['日期'].max().reset_index()
        product_last_sale.columns = ['商品名称', '最后销售日期']
        product_last_sale['滞销天数'] = (last_date - product_last_sale['最后销售日期']).dt.days
        
        print(f"\n商品总数: {len(product_last_sale)}")
        print(f"滞销天数分布:")
        print(f"  - 0天(当天有销售): {(product_last_sale['滞销天数'] == 0).sum()}")
        print(f"  - 1-6天: {((product_last_sale['滞销天数'] >= 1) & (product_last_sale['滞销天数'] <= 6)).sum()}")
        print(f"  - 7天(轻度): {(product_last_sale['滞销天数'] == 7).sum()}")
        print(f"  - 8-15天(中度): {((product_last_sale['滞销天数'] >= 8) & (product_last_sale['滞销天数'] <= 15)).sum()}")
        print(f"  - 16-30天(重度): {((product_last_sale['滞销天数'] >= 16) & (product_last_sale['滞销天数'] <= 30)).sum()}")
        print(f"  - >30天(超重度): {(product_last_sale['滞销天数'] > 30).sum()}")
        
        # 获取商品库存信息
        if '库存' in df.columns:
            last_stock = df[df['日期'] == last_date][['商品名称', '一级分类名', '库存']].drop_duplicates('商品名称')
            product_info = product_last_sale.merge(last_stock, on='商品名称', how='left')
            product_info['库存'] = product_info['库存'].fillna(0)
            
            print(f"\n库存>0的滞销品统计:")
            stagnant = product_info[product_info['库存'] > 0]
            print(f"  - 轻度滞销(7天): {((stagnant['滞销天数'] == 7)).sum()}")
            print(f"  - 中度滞销(8-15天): {((stagnant['滞销天数'] >= 8) & (stagnant['滞销天数'] <= 15)).sum()}")
            print(f"  - 重度滞销(16-30天): {((stagnant['滞销天数'] >= 16) & (stagnant['滞销天数'] <= 30)).sum()}")
            print(f"  - 超重度滞销(>30天): {((stagnant['滞销天数'] > 30)).sum()}")
            
            # 按分类统计
            if '一级分类名' in product_info.columns:
                print("\n" + "=" * 80)
                print("各分类滞销品统计(库存>0):")
                print("=" * 80)
                
                product_info['轻度滞销'] = ((product_info['滞销天数'] == 7) & (product_info['库存'] > 0)).astype(int)
                product_info['中度滞销'] = ((product_info['滞销天数'] >= 8) & (product_info['滞销天数'] <= 15) & (product_info['库存'] > 0)).astype(int)
                product_info['重度滞销'] = ((product_info['滞销天数'] >= 16) & (product_info['滞销天数'] <= 30) & (product_info['库存'] > 0)).astype(int)
                product_info['超重度滞销'] = ((product_info['滞销天数'] > 30) & (product_info['库存'] > 0)).astype(int)
                
                stagnant_by_cat = product_info.groupby('一级分类名').agg({
                    '轻度滞销': 'sum',
                    '中度滞销': 'sum',
                    '重度滞销': 'sum',
                    '超重度滞销': 'sum'
                })
                stagnant_by_cat['总计'] = stagnant_by_cat.sum(axis=1)
                print(stagnant_by_cat[stagnant_by_cat['总计'] > 0])
    
    print("\n" + "=" * 80)
    print("调试完成")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
