# -*- coding: utf-8 -*-
"""
调试诊断数据 - 检查实际数据中的热销缺货和价格异常
"""
import pandas as pd
import sys
from datetime import datetime, timedelta

def debug_diagnosis():
    """调试诊断数据"""
    print("="*80)
    print("🔍 调试热销缺货和价格异常数据")
    print("="*80)
    
    try:
        # 连接数据库
        from database.connection import engine
        
        print("\n📊 正在加载数据...")
        with engine.connect() as conn:
            # 先查看表结构
            tables = pd.read_sql("SELECT table_name FROM information_schema.tables WHERE table_schema='public'", conn)
            print(f"   可用表: {tables['table_name'].tolist()}")
            
            # 查看orders表的列
            columns = pd.read_sql("SELECT column_name FROM information_schema.columns WHERE table_name='orders'", conn)
            print(f"   orders表字段: {columns['column_name'].tolist()[:20]}")
            
            # 加载订单数据（使用正确的字段名）
            df = pd.read_sql('SELECT * FROM orders ORDER BY "order_date" DESC LIMIT 10000', conn)
        
        print(f"✅ 数据加载成功: {len(df)} 条记录")
        print(f"   - 日期范围: {df['日期'].min()} ~ {df['日期'].max()}")
        print(f"   - 商品数: {df['商品名称'].nunique()}")
        
        # 检查关键字段
        print("\n🔍 检查关键字段:")
        key_fields = ['商品名称', '日期', '月售', '销量', '剩余库存', '实收价格', '商品采购成本', '一级分类名']
        for field in key_fields:
            if field in df.columns:
                non_null = df[field].notna().sum()
                print(f"   ✅ {field}: {non_null}/{len(df)} 非空")
            else:
                print(f"   ❌ {field}: 字段不存在")
        
        # 获取昨日日期
        df['日期'] = pd.to_datetime(df['日期'])
        yesterday = df['日期'].max().normalize()
        print(f"\n📅 昨日日期: {yesterday}")
        
        # 检查热销缺货
        print("\n" + "="*80)
        print("🔴 检查热销缺货数据")
        print("="*80)
        
        if '剩余库存' in df.columns:
            yesterday_df = df[df['日期'].dt.normalize() == yesterday]
            print(f"   - 昨日订单数: {len(yesterday_df)}")
            
            # 统计昨日库存为0的商品
            if len(yesterday_df) > 0:
                stock_zero = yesterday_df[yesterday_df['剩余库存'] == 0]
                print(f"   - 昨日库存为0的订单行: {len(stock_zero)}")
                print(f"   - 昨日库存为0的商品数: {stock_zero['商品名称'].nunique()}")
                
                if len(stock_zero) > 0:
                    print(f"\n   📋 库存为0的商品示例:")
                    for product in stock_zero['商品名称'].unique()[:5]:
                        print(f"      - {product}")
                
                # 检查这些商品在前7天是否有销量
                start_date = yesterday - timedelta(days=6)
                period_df = df[(df['日期'].dt.normalize() >= start_date) & (df['日期'].dt.normalize() <= yesterday)]
                
                sales_col = '月售' if '月售' in df.columns else '销量'
                if sales_col in period_df.columns:
                    period_sales = period_df.groupby('商品名称')[sales_col].sum()
                    
                    # 找出有销量且昨日库存为0的商品
                    stockout_products = []
                    for product in stock_zero['商品名称'].unique():
                        if product in period_sales.index and period_sales[product] > 0:
                            stockout_products.append(product)
                    
                    print(f"\n   🎯 符合热销缺货条件的商品数: {len(stockout_products)}")
                    if len(stockout_products) > 0:
                        print(f"   📋 热销缺货商品:")
                        for product in stockout_products[:5]:
                            sales = period_sales[product]
                            print(f"      - {product} (7天销量: {sales})")
                    else:
                        print(f"   ⚠️ 没有商品同时满足：前7天有销量 且 昨日库存为0")
            else:
                print(f"   ⚠️ 昨日没有订单数据")
        else:
            print(f"   ❌ 数据中没有'剩余库存'字段")
        
        # 检查价格异常
        print("\n" + "="*80)
        print("🟠 检查价格异常数据")
        print("="*80)
        
        if '实收价格' in df.columns and '商品采购成本' in df.columns:
            yesterday_df = df[df['日期'].dt.normalize() == yesterday]
            print(f"   - 昨日订单数: {len(yesterday_df)}")
            
            if len(yesterday_df) > 0:
                sales_field = '月售' if '月售' in yesterday_df.columns else '销量'
                
                # 计算单品成本
                price_df = yesterday_df[['商品名称', '实收价格', '商品采购成本', sales_field]].copy()
                price_df = price_df.dropna(subset=['实收价格', '商品采购成本'])
                
                if len(price_df) > 0:
                    price_df[sales_field] = pd.to_numeric(price_df[sales_field], errors='coerce').fillna(1)
                    price_df[sales_field] = price_df[sales_field].replace(0, 1)
                    price_df['单品成本'] = price_df['商品采购成本'] / price_df[sales_field]
                    
                    # 筛选售价低于成本的
                    abnormal = price_df[price_df['实收价格'] < price_df['单品成本']]
                    
                    print(f"   - 有效价格数据: {len(price_df)} 条")
                    print(f"   - 价格异常订单行: {len(abnormal)}")
                    print(f"   - 价格异常商品数: {abnormal['商品名称'].nunique()}")
                    
                    if len(abnormal) > 0:
                        print(f"\n   📋 价格异常商品示例:")
                        for _, row in abnormal.head(5).iterrows():
                            print(f"      - {row['商品名称']}: 售价¥{row['实收价格']:.2f} < 成本¥{row['单品成本']:.2f}")
                    else:
                        print(f"   ✅ 所有商品售价均高于成本")
                else:
                    print(f"   ⚠️ 没有有效的价格数据")
            else:
                print(f"   ⚠️ 昨日没有订单数据")
        else:
            missing = []
            if '实收价格' not in df.columns:
                missing.append('实收价格')
            if '商品采购成本' not in df.columns:
                missing.append('商品采购成本')
            print(f"   ❌ 数据中缺少字段: {', '.join(missing)}")
        
        # 测试诊断函数
        print("\n" + "="*80)
        print("🧪 测试诊断函数")
        print("="*80)
        
        from components.today_must_do.diagnosis_analysis import analyze_urgent_issues
        
        print("   正在执行 analyze_urgent_issues...")
        result = analyze_urgent_issues(df)
        
        print(f"\n   📊 函数返回结果:")
        print(f"   - 热销缺货: {result['stockout']['count']} 个")
        print(f"   - 价格异常: {result['price_abnormal']['count']} 个")
        
        if result['stockout'].get('error'):
            print(f"   ⚠️ 热销缺货错误: {result['stockout']['error']}")
        if result['price_abnormal'].get('error'):
            print(f"   ⚠️ 价格异常错误: {result['price_abnormal']['error']}")
        
    except Exception as e:
        print(f"\n❌ 调试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_diagnosis()
