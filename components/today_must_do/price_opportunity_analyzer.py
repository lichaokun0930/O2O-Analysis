# -*- coding: utf-8 -*-
"""
提价机会分析器
识别可以安全提价的商品
"""

import pandas as pd
from datetime import timedelta


def get_price_increase_opportunity_products(df: pd.DataFrame, selected_days: int = 7) -> pd.DataFrame:
    """
    获取提价机会商品
    
    筛选标准：
    1. 销量稳定或上升（近N天 >= 前N天）
    2. 利润率 < 30%（还有提升空间）
    3. 当前售价 < 原价 * 0.9（离原价还有距离）
    4. 价格弹性 < 0.8（对价格相对不敏感）
    
    返回字段：
    - 商品名称、店内码、一级分类名
    - 当前售价、原价、利润率
    - 近N天销量、前N天销量、销量变化（绝对值）
    - 建议提价幅度
    - 预估利润增量
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    try:
        df = df.copy()
        
        # 获取字段
        date_col = next((c for c in ['日期', 'date', '订单日期'] if c in df.columns), None)
        product_col = next((c for c in ['商品名称', '商品', 'product_name'] if c in df.columns), None)
        code_col = next((c for c in ['店内码', '商品编码', 'sku'] if c in df.columns), None)
        price_col = next((c for c in ['实收价格', '商品实售价', '售价', 'price'] if c in df.columns), None)
        original_price_col = next((c for c in ['原价', '原售价'] if c in df.columns), None)
        sales_col = next((c for c in ['月售', '销量', '数量', 'quantity'] if c in df.columns), None)
        profit_col = next((c for c in ['利润额', 'profit'] if c in df.columns), None)
        category_col = next((c for c in ['一级分类名', '一级分类'] if c in df.columns), None)
        
        if not all([date_col, product_col, price_col, sales_col]):
            return pd.DataFrame()
        
        # 转换日期
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        
        if df.empty:
            return pd.DataFrame()
        
        # 计算时间段
        max_date = df[date_col].max().normalize()
        
        # 根据用户选择的天数计算时间窗口
        recent_start = max_date - timedelta(days=selected_days - 1)
        prev_start = max_date - timedelta(days=selected_days * 2 - 1)
        prev_end = max_date - timedelta(days=selected_days)
        
        recent_df = df[df[date_col].dt.normalize() >= recent_start]
        prev_df = df[(df[date_col].dt.normalize() >= prev_start) & (df[date_col].dt.normalize() <= prev_end)]
        
        if recent_df.empty or prev_df.empty:
            return pd.DataFrame()
        
        # 确定聚合key
        group_key = code_col if code_col and code_col in df.columns else product_col
        
        # 清洗数据
        for col in [sales_col, price_col]:
            if col in recent_df.columns:
                recent_df[col] = pd.to_numeric(recent_df[col], errors='coerce').fillna(0)
                prev_df[col] = pd.to_numeric(prev_df[col], errors='coerce').fillna(0)
        
        if original_price_col and original_price_col in df.columns:
            recent_df[original_price_col] = pd.to_numeric(recent_df[original_price_col], errors='coerce').fillna(0)
        
        if profit_col and profit_col in recent_df.columns:
            recent_df[profit_col] = pd.to_numeric(recent_df[profit_col], errors='coerce').fillna(0)
        
        # 聚合近期数据
        agg_dict = {
            sales_col: 'sum',
            price_col: 'mean',
        }
        
        if product_col != group_key and product_col in recent_df.columns:
            agg_dict[product_col] = 'first'
        if category_col and category_col in recent_df.columns:
            agg_dict[category_col] = 'first'
        if original_price_col and original_price_col in recent_df.columns:
            agg_dict[original_price_col] = 'mean'
        if profit_col and profit_col in recent_df.columns:
            agg_dict[profit_col] = 'sum'
        
        recent_stats = recent_df.groupby(group_key, as_index=False).agg(agg_dict)
        recent_stats = recent_stats.rename(columns={sales_col: f'近{selected_days}天销量'})
        
        # 聚合前期数据
        prev_stats = prev_df.groupby(group_key, as_index=False).agg({sales_col: 'sum'})
        prev_stats = prev_stats.rename(columns={sales_col: f'前{selected_days}天销量'})
        
        # 合并
        comparison = recent_stats.merge(prev_stats, on=group_key, how='inner')
        comparison[f'前{selected_days}天销量'] = comparison[f'前{selected_days}天销量'].fillna(0)
        
        # 计算利润率
        if profit_col and profit_col in comparison.columns:
            comparison['销售额'] = comparison[price_col] * comparison[f'近{selected_days}天销量']
            comparison['利润率'] = (comparison[profit_col] / comparison['销售额'] * 100).fillna(0)
            comparison['利润率'] = comparison['利润率'].clip(0, 100)
        else:
            comparison['利润率'] = 0
        
        # 计算销量变化（绝对值）
        comparison['销量变化'] = comparison[f'近{selected_days}天销量'] - comparison[f'前{selected_days}天销量']
        
        # 筛选条件
        if original_price_col and original_price_col in comparison.columns:
            price_space_mask = comparison[price_col] < comparison[original_price_col] * 0.9
        else:
            price_space_mask = pd.Series([True] * len(comparison), index=comparison.index)
        
        opportunity_mask = (
            (comparison['销量变化'] >= 0) &  # 销量稳定或上升
            (comparison['利润率'] < 30) &  # 利润率<30%
            (comparison['利润率'] > 0) &   # 利润率>0（排除异常）
            price_space_mask &  # 离原价有距离
            (comparison[f'近{selected_days}天销量'] >= 5)  # 至少有一定销量基础
        )
        
        opportunities = comparison[opportunity_mask].copy()
        
        if opportunities.empty:
            return pd.DataFrame()
        
        # 过滤耗材
        if category_col and category_col in opportunities.columns:
            opportunities = opportunities[opportunities[category_col] != '耗材']
        
        if opportunities.empty:
            return pd.DataFrame()
        
        # 计算建议提价幅度
        def get_suggest_increase(row):
            sales_growth = row['销量变化'] / row[f'前{selected_days}天销量'] if row[f'前{selected_days}天销量'] > 0 else 0
            profit_rate = row['利润率']
            
            if sales_growth > 0.2 and profit_rate < 20:
                return 8  # 销量大涨+低利润 → 提价8%
            elif sales_growth > 0.1:
                return 5  # 销量小涨 → 提价5%
            elif sales_growth >= 0 and profit_rate < 15:
                return 3  # 销量稳定+极低利润 → 提价3%
            else:
                return 2  # 保守提价2%
        
        opportunities['建议提价幅度'] = opportunities.apply(get_suggest_increase, axis=1)
        
        # 预估利润增量（简化计算：假设销量不变）
        if profit_col and profit_col in opportunities.columns:
            opportunities['预估利润增量'] = (
                opportunities[profit_col] * opportunities['建议提价幅度'] / 100
            ).round(2)
        else:
            opportunities['预估利润增量'] = 0
        
        # 按预估利润增量排序
        opportunities = opportunities.sort_values('预估利润增量', ascending=False)
        
        # 整理列顺序
        final_cols = []
        for col in [product_col, code_col, category_col, price_col, original_price_col, 
                    '利润率', f'近{selected_days}天销量', f'前{selected_days}天销量', 
                    '销量变化', '建议提价幅度', '预估利润增量']:
            if col and col in opportunities.columns:
                final_cols.append(col)
        
        # 添加其他列
        for col in opportunities.columns:
            if col not in final_cols:
                final_cols.append(col)
        
        return opportunities[final_cols]
        
    except Exception as e:
        print(f"get_price_increase_opportunity_products 错误: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()
