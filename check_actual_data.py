# -*- coding: utf-8 -*-
"""
检查实际数据 - 简化版
"""
import pandas as pd
import sys

# 设置输出编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    print("="*80)
    print("检查实际数据")
    print("="*80)
    
    try:
        # 从主模块加载数据
        print("\n正在加载数据...")
        from 智能门店看板_Dash版 import load_data_from_db
        
        df = load_data_from_db()
        
        if df is None or df.empty:
            print("错误: 数据为空")
            return
        
        print(f"数据加载成功: {len(df)} 条记录")
        print(f"日期范围: {df['日期'].min()} ~ {df['日期'].max()}")
        
        # 检查关键字段
        print("\n检查关键字段:")
        key_fields = ['商品名称', '日期', '月售', '销量', '剩余库存', '实收价格', '商品采购成本']
        for field in key_fields:
            if field in df.columns:
                non_null = df[field].notna().sum()
                print(f"  {field}: {non_null}/{len(df)} 非空")
            else:
                print(f"  {field}: 字段不存在")
        
        # 测试诊断函数
        print("\n测试诊断函数...")
        from components.today_must_do.diagnosis_analysis import analyze_urgent_issues
        
        result = analyze_urgent_issues(df)
        
        print("\n诊断结果:")
        print(f"  热销缺货: {result['stockout']['count']} 个")
        print(f"  价格异常: {result['price_abnormal']['count']} 个")
        
        if result['stockout'].get('error'):
            print(f"  热销缺货错误: {result['stockout']['error']}")
        if result['price_abnormal'].get('error'):
            print(f"  价格异常错误: {result['price_abnormal']['error']}")
        
        # 如果为0，检查原因
        if result['stockout']['count'] == 0:
            print("\n分析热销缺货为0的原因:")
            df_copy = df.copy()
            df_copy['日期'] = pd.to_datetime(df_copy['日期'])
            yesterday = df_copy['日期'].max().normalize()
            yesterday_df = df_copy[df_copy['日期'].dt.normalize() == yesterday]
            
            print(f"  昨日订单数: {len(yesterday_df)}")
            
            if '剩余库存' in yesterday_df.columns:
                stock_zero = yesterday_df[yesterday_df['剩余库存'] == 0]
                print(f"  昨日库存为0的订单行: {len(stock_zero)}")
                print(f"  昨日库存为0的商品数: {stock_zero['商品名称'].nunique()}")
            else:
                print("  数据中没有'剩余库存'字段")
        
        if result['price_abnormal']['count'] == 0:
            print("\n分析价格异常为0的原因:")
            df_copy = df.copy()
            df_copy['日期'] = pd.to_datetime(df_copy['日期'])
            yesterday = df_copy['日期'].max().normalize()
            yesterday_df = df_copy[df_copy['日期'].dt.normalize() == yesterday]
            
            print(f"  昨日订单数: {len(yesterday_df)}")
            
            if '实收价格' in yesterday_df.columns and '商品采购成本' in yesterday_df.columns:
                sales_field = '月售' if '月售' in yesterday_df.columns else '销量'
                price_df = yesterday_df[['商品名称', '实收价格', '商品采购成本', sales_field]].copy()
                price_df = price_df.dropna(subset=['实收价格', '商品采购成本'])
                
                if len(price_df) > 0:
                    price_df[sales_field] = pd.to_numeric(price_df[sales_field], errors='coerce').fillna(1)
                    price_df[sales_field] = price_df[sales_field].replace(0, 1)
                    price_df['单品成本'] = price_df['商品采购成本'] / price_df[sales_field]
                    
                    abnormal = price_df[price_df['实收价格'] < price_df['单品成本']]
                    print(f"  有效价格数据: {len(price_df)} 条")
                    print(f"  价格异常订单行: {len(abnormal)}")
                    
                    if len(abnormal) == 0:
                        # 显示价格分布
                        print(f"  实收价格范围: {price_df['实收价格'].min():.2f} ~ {price_df['实收价格'].max():.2f}")
                        print(f"  单品成本范围: {price_df['单品成本'].min():.2f} ~ {price_df['单品成本'].max():.2f}")
                else:
                    print("  没有有效的价格数据")
            else:
                print("  数据中缺少'实收价格'或'商品采购成本'字段")
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
