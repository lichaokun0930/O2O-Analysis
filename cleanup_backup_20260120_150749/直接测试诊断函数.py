# -*- coding: utf-8 -*-
"""
直接测试诊断函数 - 使用看板的数据加载方式
"""
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*80)
print("直接测试诊断函数")
print("="*80)

# 导入诊断分析模块
from components.today_must_do.diagnosis_analysis import analyze_urgent_issues, get_diagnosis_summary

# 导入数据库连接
from database.connection import engine
import pandas as pd

print("\n1. 加载数据...")
try:
    with engine.connect() as conn:
        # 使用正确的SQL查询
        df = pd.read_sql('SELECT * FROM orders ORDER BY order_date DESC LIMIT 5000', conn)
    
    print(f"   数据加载成功: {len(df)} 条记录")
    
    # 检查字段映射
    print("\n2. 检查字段映射...")
    field_mapping = {
        'order_date': '日期',
        'product_name': '商品名称',
        'quantity': '月售',
        'remaining_stock': '剩余库存',
        'actual_price': '实收价格',
        'product_cost': '商品采购成本',
        'category_level1': '一级分类名',
        'platform': '平台',
        'store_name': '门店名称'
    }
    
    # 重命名字段
    rename_dict = {}
    for db_field, display_field in field_mapping.items():
        if db_field in df.columns:
            rename_dict[db_field] = display_field
            print(f"   {db_field} -> {display_field}")
    
    df = df.rename(columns=rename_dict)
    
    print(f"\n3. 数据概况:")
    print(f"   日期范围: {df['日期'].min()} ~ {df['日期'].max()}")
    print(f"   商品数: {df['商品名称'].nunique()}")
    print(f"   门店数: {df['门店名称'].nunique() if '门店名称' in df.columns else 'N/A'}")
    
    # 检查关键字段
    print(f"\n4. 关键字段检查:")
    key_fields = ['剩余库存', '实收价格', '商品采购成本', '月售']
    for field in key_fields:
        if field in df.columns:
            non_null = df[field].notna().sum()
            print(f"   {field}: {non_null}/{len(df)} 非空")
        else:
            print(f"   {field}: 不存在")
    
    # 执行诊断分析
    print(f"\n5. 执行诊断分析...")
    result = analyze_urgent_issues(df)
    
    print(f"\n" + "="*80)
    print("诊断结果:")
    print("="*80)
    print(f"热销缺货: {result['stockout']['count']} 个")
    print(f"价格异常: {result['price_abnormal']['count']} 个")
    
    if result['stockout'].get('error'):
        print(f"\n热销缺货错误: {result['stockout']['error']}")
    
    if result['price_abnormal'].get('error'):
        print(f"\n价格异常错误: {result['price_abnormal']['error']}")
    
    # 如果为0，详细分析原因
    if result['stockout']['count'] == 0:
        print(f"\n分析热销缺货为0的原因:")
        df_copy = df.copy()
        df_copy['日期'] = pd.to_datetime(df_copy['日期'])
        yesterday = df_copy['日期'].max().normalize()
        yesterday_df = df_copy[df_copy['日期'].dt.normalize() == yesterday]
        
        print(f"  昨日订单数: {len(yesterday_df)}")
        
        if '剩余库存' in yesterday_df.columns:
            stock_zero = yesterday_df[yesterday_df['剩余库存'] == 0]
            print(f"  昨日库存为0的订单行: {len(stock_zero)}")
            if len(stock_zero) > 0:
                print(f"  昨日库存为0的商品: {stock_zero['商品名称'].unique()[:5].tolist()}")
        else:
            print(f"  数据中没有'剩余库存'字段")
    
    if result['price_abnormal']['count'] == 0:
        print(f"\n分析价格异常为0的原因:")
        df_copy = df.copy()
        df_copy['日期'] = pd.to_datetime(df_copy['日期'])
        yesterday = df_copy['日期'].max().normalize()
        yesterday_df = df_copy[df_copy['日期'].dt.normalize() == yesterday]
        
        print(f"  昨日订单数: {len(yesterday_df)}")
        
        if '实收价格' in yesterday_df.columns and '商品采购成本' in yesterday_df.columns:
            sales_field = '月售' if '月售' in yesterday_df.columns else '销量'
            price_df = yesterday_df[['商品名称', '实收价格', '商品采购成本', sales_field]].dropna()
            
            if len(price_df) > 0:
                price_df[sales_field] = pd.to_numeric(price_df[sales_field], errors='coerce').fillna(1).replace(0, 1)
                price_df['单品成本'] = price_df['商品采购成本'] / price_df[sales_field]
                
                print(f"  有效价格数据: {len(price_df)} 条")
                print(f"  实收价格范围: {price_df['实收价格'].min():.2f} ~ {price_df['实收价格'].max():.2f}")
                print(f"  单品成本范围: {price_df['单品成本'].min():.2f} ~ {price_df['单品成本'].max():.2f}")
                
                # 检查是否有价格低于成本的
                abnormal = price_df[price_df['实收价格'] < price_df['单品成本']]
                print(f"  价格异常订单行: {len(abnormal)}")
                
                if len(abnormal) > 0:
                    print(f"  价格异常商品示例:")
                    for _, row in abnormal.head(3).iterrows():
                        print(f"    - {row['商品名称']}: 售价¥{row['实收价格']:.2f} < 成本¥{row['单品成本']:.2f}")

except Exception as e:
    print(f"\n错误: {str(e)}")
    import traceback
    traceback.print_exc()
