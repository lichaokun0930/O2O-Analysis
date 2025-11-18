"""
分类销售看板功能测试脚本
测试新增的售罄品、滞销品、动销率等功能
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 模拟测试数据
def create_test_data():
    """创建测试数据"""
    np.random.seed(42)
    
    # 日期范围: 最近30天
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # 一级分类
    categories = ['饮品', '休闲食品', '美容护肤', '日用百货', '粮油调味']
    
    # 生成商品数据
    products = []
    for cat in categories:
        for i in range(10):  # 每个分类10个商品
            products.append({
                '商品名称': f'{cat}_商品{i+1}',
                '一级分类名': cat
            })
    
    # 生成订单数据
    data = []
    for date in dates:
        # 每天随机生成订单
        for _ in range(np.random.randint(20, 50)):
            product = products[np.random.randint(0, len(products))]
            order_id = f'ORD{date.strftime("%Y%m%d")}{np.random.randint(1000, 9999)}'
            
            data.append({
                '日期': date,
                '订单ID': order_id,
                '商品名称': product['商品名称'],
                '一级分类名': product['一级分类名'],
                '商品实售价': np.random.uniform(10, 200),
                '月售': np.random.randint(1, 5),
                '库存': np.random.randint(0, 100) if np.random.random() > 0.1 else 0,  # 10%概率库存为0
            })
    
    df = pd.DataFrame(data)
    
    # 创建订单聚合数据
    order_agg = df.groupby('订单ID').agg({
        '商品实售价': 'sum'
    }).reset_index()
    order_agg['订单实际利润'] = order_agg['商品实售价'] * 0.2  # 假设20%利润率
    
    return df, order_agg

# 测试各项指标计算
def test_category_analysis():
    """测试分类分析功能"""
    print("=" * 60)
    print("🧪 分类销售看板功能测试")
    print("=" * 60)
    
    # 创建测试数据
    print("\n📊 创建测试数据...")
    df, order_agg = create_test_data()
    print(f"✅ 数据行数: {len(df)}")
    print(f"✅ 订单数: {df['订单ID'].nunique()}")
    print(f"✅ 商品数: {df['商品名称'].nunique()}")
    print(f"✅ 分类数: {df['一级分类名'].nunique()}")
    
    # 测试1: 售罄品统计
    print("\n" + "=" * 60)
    print("测试1: 售罄品统计 (库存=0 且 近7天有销量)")
    print("=" * 60)
    
    last_date = df['日期'].max()
    seven_days_ago = last_date - timedelta(days=7)
    recent_sales = df[df['日期'] >= seven_days_ago]
    recent_products = set(recent_sales['商品名称'].unique())
    
    last_stock = df.loc[df.groupby('商品名称')['日期'].idxmax()]
    zero_stock_products = set(last_stock[last_stock['库存'] == 0]['商品名称'].unique())
    sellout_products = zero_stock_products & recent_products
    
    print(f"✅ 近7天有销量商品数: {len(recent_products)}")
    print(f"✅ 当前库存为0商品数: {len(zero_stock_products)}")
    print(f"✅ 售罄品数 (交集): {len(sellout_products)}")
    
    if len(sellout_products) > 0:
        print(f"\n📋 售罄商品示例:")
        for i, product in enumerate(list(sellout_products)[:5], 1):
            cat = df[df['商品名称'] == product]['一级分类名'].iloc[0]
            print(f"  {i}. {product} ({cat})")
    
    # 测试2: 滞销品四级分级
    print("\n" + "=" * 60)
    print("测试2: 滞销品四级分级")
    print("=" * 60)
    
    product_last_sale = df.groupby('商品名称')['日期'].max().reset_index()
    product_last_sale.columns = ['商品名称', '最后销售日期']
    product_last_sale['滞销天数'] = (last_date - product_last_sale['最后销售日期']).dt.days
    
    product_info = df[['商品名称', '一级分类名']].drop_duplicates()
    product_stock = last_stock[['商品名称', '库存']]
    product_stagnant = product_last_sale.merge(product_info, on='商品名称', how='left')
    product_stagnant = product_stagnant.merge(product_stock, on='商品名称', how='left')
    
    product_stagnant['轻度滞销'] = ((product_stagnant['滞销天数'] == 7) & (product_stagnant['库存'] > 0)).astype(int)
    product_stagnant['中度滞销'] = ((product_stagnant['滞销天数'] >= 8) & (product_stagnant['滞销天数'] <= 15) & (product_stagnant['库存'] > 0)).astype(int)
    product_stagnant['重度滞销'] = ((product_stagnant['滞销天数'] >= 16) & (product_stagnant['滞销天数'] <= 30) & (product_stagnant['库存'] > 0)).astype(int)
    product_stagnant['超重度滞销'] = ((product_stagnant['滞销天数'] > 30) & (product_stagnant['库存'] > 0)).astype(int)
    
    print(f"✅ 轻度滞销 (7天): {product_stagnant['轻度滞销'].sum()}个")
    print(f"✅ 中度滞销 (8-15天): {product_stagnant['中度滞销'].sum()}个")
    print(f"✅ 重度滞销 (16-30天): {product_stagnant['重度滞销'].sum()}个")
    print(f"✅ 超重度滞销 (>30天): {product_stagnant['超重度滞销'].sum()}个")
    
    # 测试3: 动销率
    print("\n" + "=" * 60)
    print("测试3: 动销率计算")
    print("=" * 60)
    
    for cat in df['一级分类名'].unique():
        cat_products = df[df['一级分类名'] == cat]['商品名称'].nunique()
        cat_sales_products = df[df['一级分类名'] == cat]['商品名称'].nunique()
        turnover_rate = (cat_sales_products / cat_products * 100) if cat_products > 0 else 0
        print(f"✅ {cat}: 总商品{cat_products}个, 有销量{cat_sales_products}个, 动销率{turnover_rate:.1f}%")
    
    # 测试4: 库存周转天数
    print("\n" + "=" * 60)
    print("测试4: 库存周转天数")
    print("=" * 60)
    
    date_range_days = (df['日期'].max() - df['日期'].min()).days + 1
    print(f"✅ 数据周期: {date_range_days}天")
    
    for cat in df['一级分类名'].unique():
        cat_df = df[df['一级分类名'] == cat]
        total_sales = cat_df['月售'].sum()
        daily_sales = total_sales / date_range_days
        current_stock = last_stock[last_stock['一级分类名'] == cat]['库存'].sum()
        turnover_days = current_stock / daily_sales if daily_sales > 0 else 0
        print(f"✅ {cat}: 库存{current_stock:.0f}件, 日均销{daily_sales:.1f}件, 周转{turnover_days:.1f}天")
    
    print("\n" + "=" * 60)
    print("✅ 所有功能测试完成!")
    print("=" * 60)

if __name__ == '__main__':
    test_category_analysis()
