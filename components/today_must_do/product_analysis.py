# -*- coding: utf-8 -*-
"""
今日必做 - 商品侧分析模块 (V2.3 运营视角重构)

严格按照「商品侧运营重构方案」实现:

核心理念: 从"数据分析师视角"转变为"门店运营视角"
四大场景:
1. 🏆 高利润商品榜 (Top Profit): 谁在赚钱?
2. 📉 流量下跌/异常榜 (Traffic Drop): 谁突然卖不动了?
3. 🐌 新增滞销预警 (New Slow-Moving): 谁刚开始积压?
4. 🚀 潜力新品榜 (New Potential): 谁是明日之星?

⚠️ 时间基准: 数据最后一天 = "昨日"
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from typing import Dict, Tuple, Optional, Any, List


def get_base_dates(df: pd.DataFrame) -> Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
    """
    获取基准日期
    
    Returns:
        (昨日, 前日) - 昨日是数据最后一天
    """
    date_col = '日期' if '日期' in df.columns else '下单时间'
    if date_col not in df.columns:
        return None, None
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # 昨日 = 数据最后一天
    yesterday = df[date_col].max().normalize()
    # 前日 = 昨日 - 1天
    day_before = yesterday - timedelta(days=1)
    
    return yesterday, day_before


def get_product_daily_metrics(
    df: pd.DataFrame, 
    target_date: pd.Timestamp
) -> pd.DataFrame:
    """
    获取指定日期的商品级指标汇总
    
    Args:
        df: 原始数据（商品级明细）
        target_date: 目标日期
    
    Returns:
        DataFrame: 店内码 | 商品名称 | 销量 | 销售额 | 利润额 | 毛利率
    
    Note:
        ⚠️ 使用店内码（而非商品名称）区分商品，避免同名不同规格混淆
    """
    date_col = '日期' if '日期' in df.columns else '下单时间'
    sales_col = '月售' if '月售' in df.columns else '销量'
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # 筛选指定日期
    day_data = df[df[date_col].dt.normalize() == target_date]
    
    if len(day_data) == 0:
        return pd.DataFrame()
    
    # ⚠️ 优先使用店内码聚合，避免同名不同规格商品混淆
    group_key = '店内码' if '店内码' in day_data.columns else '商品名称'
    
    # 按商品聚合
    agg_dict = {}
    
    # 保留商品名称
    if group_key == '店内码':
        agg_dict['商品名称'] = ('商品名称', 'first')
    
    # 销量
    if sales_col in day_data.columns:
        agg_dict['销量'] = (sales_col, 'sum')
    
    # 销售额 = 实收价格 × 销量
    if '实收价格' in day_data.columns and sales_col in day_data.columns:
        day_data['_实收价格_销量'] = day_data['实收价格'].fillna(0) * day_data[sales_col].fillna(1)
        agg_dict['销售额'] = ('_实收价格_销量', 'sum')
    elif '商品实售价' in day_data.columns:
        # 备选：商品实售价已经是总价
        agg_dict['销售额'] = ('商品实售价', 'sum')
    
    # 利润额
    if '利润额' in day_data.columns:
        agg_dict['利润额'] = ('利润额', 'sum')
    
    # 成本
    cost_col = '商品采购成本' if '商品采购成本' in day_data.columns else '成本'
    if cost_col in day_data.columns:
        agg_dict['成本'] = (cost_col, 'sum')
    
    if not agg_dict:
        return pd.DataFrame()
    
    # 执行聚合
    result = day_data.groupby(group_key).agg(**agg_dict).reset_index()
    
    # 计算毛利率
    # 修正逻辑: 销售额为0时，毛利率应视为无效(NaN)，不参与"毛利率下滑"计算
    # 避免出现 0(无销量) vs 40%(有销量) 被误判为"毛利率暴跌"
    if '销售额' in result.columns:
        # 使用临时变量避免除以0
        sales_safe = result['销售额'].replace(0, np.nan)
        
        if '成本' in result.columns:
            result['毛利率'] = ((result['销售额'] - result['成本']) / sales_safe * 100).round(2)
        elif '利润额' in result.columns:
            result['毛利率'] = (result['利润额'] / sales_safe * 100).round(2)
        else:
            result['毛利率'] = np.nan
            
        # 清理 inf/-inf
        result['毛利率'] = result['毛利率'].replace([np.inf, -np.inf], np.nan)
    else:
        result['毛利率'] = np.nan
    
    return result


def analyze_top_profit_products(df: pd.DataFrame, top_n: int = 20) -> Dict[str, Any]:
    """
    场景A: 🏆 高利润商品榜 (Top Profit)
    定义: 昨日给门店赚钱最多的商品（现金牛）。
    """
    result = {'summary': {}, 'data': pd.DataFrame(), 'error': None}
    
    try:
        yesterday, day_before = get_base_dates(df)
        if yesterday is None:
            result['error'] = '无法获取日期信息'
            return result
            
        # 获取昨日数据
        metrics = get_product_daily_metrics(df, yesterday)
        if metrics.empty:
            result['error'] = '昨日无销售数据'
            return result
            
        # 筛选利润>0并排序
        if '利润额' not in metrics.columns:
            result['error'] = '缺少利润额字段'
            return result
            
        top_profit = metrics[metrics['利润额'] > 0].sort_values('利润额', ascending=False).head(top_n).copy()
        
        # 计算单均指标
        top_profit['单均利润额'] = (top_profit['利润额'] / top_profit['销量']).round(2)
        
        # 检查前日销量以标记"昨日首销"
        day_before_metrics = get_product_daily_metrics(df, day_before)
        if not day_before_metrics.empty:
            day_before_sales = day_before_metrics[['商品名称', '销量']].rename(columns={'销量': '前日销量'})
            top_profit = top_profit.merge(day_before_sales, on='商品名称', how='left')
            top_profit['前日销量'] = top_profit['前日销量'].fillna(0)
        else:
            top_profit['前日销量'] = 0
            
        result['data'] = top_profit
        result['summary'] = {
            'total_profit': top_profit['利润额'].sum(),
            'count': len(top_profit)
        }
        return result
        
    except Exception as e:
        result['error'] = f'分析高利润商品时出错: {str(e)}'
        return result


def analyze_traffic_drop_products(df: pd.DataFrame, top_n: int = 20) -> Dict[str, Any]:
    """
    场景B: 📉 流量下跌/异常榜 (Traffic Drop)
    定义: 以前卖得好，昨天突然卖不动了。
    筛选: 前日销量 >= 3 且 昨日销量环比下跌 > 50%（或者直接为0）。
    """
    result = {'summary': {}, 'data': pd.DataFrame(), 'error': None}
    
    try:
        yesterday, day_before = get_base_dates(df)
        if yesterday is None:
            result['error'] = '无法获取日期信息'
            return result
            
        date_col = '日期' if '日期' in df.columns else '下单时间'
        
        # 获取两日数据
        yesterday_metrics = get_product_daily_metrics(df, yesterday)
        day_before_metrics = get_product_daily_metrics(df, day_before)
        
        if day_before_metrics.empty:
            result['error'] = '前日无销售数据，无法计算下跌'
            return result
            
        # 合并数据
        comparison = day_before_metrics[['商品名称', '销量', '利润额']].merge(
            yesterday_metrics[['商品名称', '销量']], 
            on='商品名称', 
            how='left',
            suffixes=('_前日', '_昨日')
        )
        comparison['销量_昨日'] = comparison['销量_昨日'].fillna(0)
        
        # 计算单均利润（用前日数据估算）
        comparison['单均利润'] = (comparison['利润额'] / comparison['销量_前日']).replace([np.inf, -np.inf], 0).fillna(0)
        
        # 筛选条件: 前日销量>=3 且 (昨日销量=0 或 跌幅>50%)
        # 跌幅 = (前日-昨日)/前日
        comparison['跌幅'] = (comparison['销量_前日'] - comparison['销量_昨日']) / comparison['销量_前日']
        
        mask = (comparison['销量_前日'] >= 3) & (comparison['跌幅'] > 0.5)
        drops = comparison[mask].copy()
        
        # 获取昨日库存信息 (用于判断是否售罄)
        stock_col = next((c for c in ['剩余库存', '库存', 'stock'] if c in df.columns), None)
        if stock_col:
            # 创建副本并转换日期，避免修改原始数据
            df_stock = df[[date_col, '商品名称', stock_col]].copy()
            df_stock[date_col] = pd.to_datetime(df_stock[date_col])
            
            # 获取昨日最后一条记录的库存
            yesterday_data = df_stock[df_stock[date_col].dt.normalize() == yesterday]
            # 按时间排序取最后一条
            latest_stock = yesterday_data.sort_values(date_col).groupby('商品名称')[stock_col].last().reset_index()
            latest_stock.rename(columns={stock_col: '昨日库存'}, inplace=True)
            
            drops = drops.merge(latest_stock, on='商品名称', how='left')
            drops['昨日库存'] = drops['昨日库存'].fillna(0)
        else:
            drops['昨日库存'] = 0
            
        # 标记原因: 售罄 vs 流量下滑
        # 售罄逻辑: 昨日库存 <= 0
        drops['原因'] = drops.apply(
            lambda x: '🚫 售罄缺货' if x['昨日库存'] <= 0 else '📉 流量下滑', 
            axis=1
        )
        
        # 计算预估损失
        drops['流失利润估算'] = ((drops['销量_前日'] - drops['销量_昨日']) * drops['单均利润']).round(2)
        
        # 排序: 按流失利润倒序
        drops = drops.sort_values('流失利润估算', ascending=False).head(top_n)
        
        result['data'] = drops
        result['summary'] = {
            'count': len(drops),
            'total_loss': drops['流失利润估算'].sum(),
            'stockout_count': (drops['昨日库存'] <= 0).sum()
        }
        return result
        
    except Exception as e:
        result['error'] = f'分析流量下跌商品时出错: {str(e)}'
        return result


def analyze_new_slow_moving_products(df: pd.DataFrame) -> Dict[str, Any]:
    """
    场景C: 🐌 新增滞销预警 (New Slow-Moving)
    定义: 刚刚掉入滞销坑位的商品。
    筛选: 最后销售日期 距今 = 7天 (轻度) 或 30天 (重度)。
    """
    result = {'summary': {}, 'data': pd.DataFrame(), 'error': None}
    
    try:
        date_col = '日期' if '日期' in df.columns else '下单时间'
        if date_col not in df.columns:
            result['error'] = '缺少日期字段'
            return result
            
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        last_date = df[date_col].max().normalize()
        
        # 计算每个商品的最后销售日期
        last_sales = df.groupby('商品名称')[date_col].max().reset_index()
        last_sales['days_since'] = (last_date - last_sales[date_col].dt.normalize()).dt.days
        
        # 筛选刚好满7天或30天的
        # 考虑到数据可能不是每天都有，放宽一点范围: 7-8天, 30-31天
        new_light = last_sales[last_sales['days_since'].between(7, 8)].copy()
        new_severe = last_sales[last_sales['days_since'].between(30, 31)].copy()
        
        new_light['滞销等级'] = '🟡 轻度(7天)'
        new_severe['滞销等级'] = '🔴 重度(30天)'
        
        combined = pd.concat([new_severe, new_light])
        
        if combined.empty:
            return result
            
        # 获取库存和成本信息
        # 优先使用最后一天的库存快照，如果没有则用最后一次销售时的记录
        # 这里简化处理，尝试获取最新的库存记录
        stock_col = next((c for c in ['剩余库存', '库存', 'stock'] if c in df.columns), None)
        cost_col = next((c for c in ['商品采购成本', '成本', 'cost'] if c in df.columns), None)
        
        if stock_col and cost_col:
            # 获取每个商品的最新库存和成本
            # 注意: 这里的成本应该是单价
            latest_info = df.sort_values(date_col).groupby('商品名称')[[stock_col, cost_col]].last().reset_index()
            combined = combined.merge(latest_info, on='商品名称', how='left')
            combined['积压成本'] = (combined[stock_col] * combined[cost_col]).fillna(0).round(2)
        else:
            combined['库存'] = 0
            combined['积压成本'] = 0
            
        result['data'] = combined
        result['summary'] = {
            'count': len(combined),
            'total_cost': combined['积压成本'].sum()
        }
        return result
        
    except Exception as e:
        result['error'] = f'分析新增滞销商品时出错: {str(e)}'
        return result


def analyze_potential_new_products(df: pd.DataFrame, top_n: int = 20) -> Dict[str, Any]:
    """
    场景D: 🚀 潜力新品榜 (New Potential)
    定义: 近期首次动销且表现不错的商品。
    筛选: 过去7天无销量(除昨日外) 且 昨日销量>0。
    """
    result = {'summary': {}, 'data': pd.DataFrame(), 'error': None}
    
    try:
        yesterday, day_before = get_base_dates(df)
        if yesterday is None:
            result['error'] = '无法获取日期信息'
            return result
            
        date_col = '日期' if '日期' in df.columns else '下单时间'
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 获取昨日有销量的商品
        yesterday_sales = df[df[date_col].dt.normalize() == yesterday]['商品名称'].unique()
        
        # 检查这些商品在过去7天(不含昨日)是否有销量
        start_check_date = yesterday - timedelta(days=7)
        past_sales = df[
            (df[date_col].dt.normalize() >= start_check_date) & 
            (df[date_col].dt.normalize() < yesterday)
        ]
        past_sold_products = set(past_sales['商品名称'].unique())
        
        # 筛选出"昨日新增动销" (昨日卖了，但过去7天没卖)
        new_movers = [p for p in yesterday_sales if p not in past_sold_products]
        
        if not new_movers:
            return result
            
        # 获取这些商品的昨日指标
        metrics = get_product_daily_metrics(df, yesterday)
        potential = metrics[metrics['商品名称'].isin(new_movers)].copy()
        
        # 排序: 按销售额倒序
        potential = potential.sort_values('销售额', ascending=False).head(top_n)
        
        result['data'] = potential
        result['summary'] = {
            'count': len(potential),
            'total_sales': potential['销售额'].sum()
        }
        return result
        
    except Exception as e:
        result['error'] = f'分析潜力新品时出错: {str(e)}'
        return result


# 保留旧函数以兼容其他模块调用，但标记为Deprecated
def analyze_product_fluctuation(df: pd.DataFrame, top_n: int = 10) -> Dict[str, Any]:
    """
    [Deprecated] 旧版波动分析，保留兼容性
    """
    # ...existing code...
    result = {
        'summary': {},
        'top_declining': pd.DataFrame(),
        'all_declining': pd.DataFrame(),
        'error': None
    }
    
    try:
        # 获取基准日期
        yesterday, day_before = get_base_dates(df)
        if yesterday is None:
            result['error'] = '无法获取日期信息'
            return result
        
        # 获取昨日和前日的商品指标
        yesterday_metrics = get_product_daily_metrics(df, yesterday)
        day_before_metrics = get_product_daily_metrics(df, day_before)
        
        if len(yesterday_metrics) == 0:
            result['error'] = '昨日无销售数据'
            return result
        
        if len(day_before_metrics) == 0:
            result['error'] = '前日无销售数据，无法计算环比'
            return result
        
        # 合并对比
        comparison = yesterday_metrics.merge(
            day_before_metrics,
            on='商品名称',
            how='outer',
            suffixes=('_昨日', '_前日')
        ).fillna(0)
        
        # 计算环比变化
        if '利润额_昨日' in comparison.columns and '利润额_前日' in comparison.columns:
            comparison['利润额变化'] = comparison['利润额_昨日'] - comparison['利润额_前日']
            comparison['利润额环比'] = comparison.apply(
                lambda r: (r['利润额变化'] / r['利润额_前日'] * 100) 
                          if r['利润额_前日'] != 0 else (0 if r['利润额_昨日'] == 0 else -100),
                axis=1
            ).round(2)
        
        if '毛利率_昨日' in comparison.columns and '毛利率_前日' in comparison.columns:
            # 修正: 如果昨日销量为0 (毛利率为NaN)，则毛利率变化也应为NaN，不参与"毛利率下滑"统计
            comparison['毛利率变化'] = comparison['毛利率_昨日'] - comparison['毛利率_前日']
        
        if '销量_昨日' in comparison.columns and '销量_前日' in comparison.columns:
            comparison['销量变化'] = comparison['销量_昨日'] - comparison['销量_前日']
            comparison['销量环比'] = comparison.apply(
                lambda r: (r['销量变化'] / r['销量_前日'] * 100)
                          if r['销量_前日'] != 0 else (0 if r['销量_昨日'] == 0 else -100),
                axis=1
            ).round(2)
            
        # 添加下滑原因分析
        def analyze_decline_reason(row):
            reasons = []
            # 1. 突发停售: 前日有销量，昨日无销量
            if row.get('销量_前日', 0) > 0 and row.get('销量_昨日', 0) == 0:
                return '🛑 突发停售'
            
            # 2. 销量跳水: 销量下滑超过30%
            if row.get('销量环比', 0) < -30:
                reasons.append('📉 销量跳水')
            elif row.get('销量变化', 0) < 0:
                reasons.append('📉 销量微跌')
                
            # 3. 毛利恶化: 毛利率下滑超过5个百分点 (且昨日有销量)
            if pd.notna(row.get('毛利率变化')) and row.get('毛利率变化') < -5:
                reasons.append('💸 毛利恶化')
            elif pd.notna(row.get('毛利率变化')) and row.get('毛利率变化') < 0:
                reasons.append('💸 毛利微跌')
                
            if not reasons:
                return '⚠️ 利润下滑' # 兜底: 销量/毛利没大跌，但利润跌了
                
            return ' + '.join(reasons)

        comparison['下滑原因'] = comparison.apply(analyze_decline_reason, axis=1)
        
        # 判断是否下滑
        decline_conditions = []
        if '利润额变化' in comparison.columns:
            decline_conditions.append(comparison['利润额变化'] < 0)
        # 注意: 毛利率变化为NaN时 (即昨日无销量)，不应被视为"毛利率下滑"
        if '毛利率变化' in comparison.columns:
            decline_conditions.append(comparison['毛利率变化'] < 0)
        if '销量变化' in comparison.columns:
            decline_conditions.append(comparison['销量变化'] < 0)
        
        if not decline_conditions:
            result['error'] = '无法计算变化指标'
            return result
        
        is_declining = pd.concat(decline_conditions, axis=1).any(axis=1)
        declining_products = comparison[is_declining].copy()
        
        # 计算汇总统计
        summary = {
            'declining_count': len(declining_products),
            'yesterday': yesterday.strftime('%Y-%m-%d'),
            'day_before': day_before.strftime('%Y-%m-%d')
        }
        
        if '利润额变化' in declining_products.columns:
            profit_declining = declining_products[declining_products['利润额变化'] < 0]
            summary['profit_declining_count'] = len(profit_declining)
            summary['profit_loss_total'] = round(abs(profit_declining['利润额变化'].sum()), 2)
        
        if '毛利率变化' in declining_products.columns:
            # 修正: 排除NaN值
            margin_declining = declining_products[declining_products['毛利率变化'] < 0]
            summary['margin_declining_count'] = len(margin_declining)
            summary['margin_avg_drop'] = round(margin_declining['毛利率变化'].mean(), 2) if len(margin_declining) > 0 else 0
        
        if '销量变化' in declining_products.columns:
            sales_declining = declining_products[declining_products['销量变化'] < 0]
            summary['sales_declining_count'] = len(sales_declining)
        
        if '利润额变化' in declining_products.columns:
            declining_products = declining_products.sort_values('利润额变化', ascending=True)
        
        result['summary'] = summary
        result['all_declining'] = declining_products
        result['top_declining'] = declining_products.head(top_n)
        
        return result
        
    except Exception as e:
        result['error'] = f'分析商品波动时出错: {str(e)}'
        return result


def analyze_slow_moving_products(df: pd.DataFrame) -> Dict[str, Any]:
    """
    [Deprecated] 旧版滞销分析，保留兼容性
    """
    # ...existing code...
    result = {
        'summary': {},
        'severe': pd.DataFrame(),
        'medium': pd.DataFrame(),
        'light': pd.DataFrame(),
        'error': None
    }
    
    try:
        date_col = '日期' if '日期' in df.columns else '下单时间'
        sales_col = '月售' if '月售' in df.columns else '销量'
        
        if date_col not in df.columns:
            result['error'] = '缺少日期字段'
            return result
        
        if '商品名称' not in df.columns:
            result['error'] = '缺少商品名称字段'
            return result
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        max_date = df[date_col].max().normalize()
        min_date = df[date_col].min().normalize()
        data_range_days = (max_date - min_date).days + 1
        
        if sales_col in df.columns:
            sales_df = df[df[sales_col] > 0]
        else:
            sales_df = df
        
        category_col = '一级分类名' if '一级分类名' in df.columns else '一级分类'
        
        if len(sales_df) == 0:
            result['error'] = '无销售记录'
            return result
        
        last_sale = sales_df.groupby('商品名称').agg({date_col: 'max'}).reset_index()
        last_sale.columns = ['商品名称', '最后销售日']
        
        if category_col in df.columns:
            product_category = df.groupby('商品名称')[category_col].first().reset_index()
            last_sale = last_sale.merge(product_category, on='商品名称', how='left')
        
        last_sale['无销量天数'] = (max_date - pd.to_datetime(last_sale['最后销售日'])).dt.days
        
        severe = last_sale[last_sale['无销量天数'] >= 30].copy()
        medium = last_sale[(last_sale['无销量天数'] >= 15) & (last_sale['无销量天数'] < 30)].copy()
        light = last_sale[(last_sale['无销量天数'] >= 7) & (last_sale['无销量天数'] < 15)].copy()
        
        for df_temp in [severe, medium, light]:
            if len(df_temp) > 0:
                df_temp['最后销售日'] = pd.to_datetime(df_temp['最后销售日']).dt.strftime('%m月%d日')
        
        severe = severe.sort_values('无销量天数', ascending=False)
        medium = medium.sort_values('无销量天数', ascending=False)
        light = light.sort_values('无销量天数', ascending=False)
        
        result['summary'] = {
            'severe_count': len(severe),
            'medium_count': len(medium),
            'light_count': len(light),
            'data_range_days': data_range_days,
            'as_of_date': max_date.strftime('%Y-%m-%d')
        }
        result['severe'] = severe
        result['medium'] = medium
        result['light'] = light
        
        return result
        
    except Exception as e:
        result['error'] = f'分析滞销商品时出错: {str(e)}'
        return result


def get_product_insight(df: pd.DataFrame, product_name: str) -> Dict[str, Any]:
    """获取单品洞察（下钻分析）"""
    result = {
        'product_name': product_name,
        'trend_data': pd.DataFrame(),
        'price_change': {},
        'cost_change': {},
        'activity_change': {},
        'insight': '',
        'error': None
    }
    
    try:
        date_col = '日期' if '日期' in df.columns else '下单时间'
        sales_col = '月售' if '月售' in df.columns else '销量'
        
        product_df = df[df['商品名称'] == product_name].copy()
        
        if len(product_df) == 0:
            result['error'] = f'未找到商品: {product_name}'
            return result
        
        product_df[date_col] = pd.to_datetime(product_df[date_col])
        yesterday, day_before = get_base_dates(df)
        
        # 历史趋势
        agg_cols = {}
        if sales_col in product_df.columns:
            agg_cols[sales_col] = 'sum'
        if '利润额' in product_df.columns:
            agg_cols['利润额'] = 'sum'
        if '商品实售价' in product_df.columns:
            agg_cols['商品实售价'] = 'sum'
        
        if agg_cols:
            daily_agg = product_df.groupby(product_df[date_col].dt.date).agg(agg_cols).reset_index()
            # 统一日期列名为'日期'，方便前端绘图
            if date_col in daily_agg.columns and date_col != '日期':
                daily_agg.rename(columns={date_col: '日期'}, inplace=True)
            # 防止groupby后列名丢失
            if '日期' not in daily_agg.columns:
                daily_agg.rename(columns={daily_agg.columns[0]: '日期'}, inplace=True)
            
            # 统一销量列名为'销量'
            if sales_col != '销量' and sales_col in daily_agg.columns:
                daily_agg.rename(columns={sales_col: '销量'}, inplace=True)
                
            result['trend_data'] = daily_agg
        
        # 昨日vs前日对比
        if yesterday and day_before:
            yesterday_data = product_df[product_df[date_col].dt.normalize() == yesterday]
            day_before_data = product_df[product_df[date_col].dt.normalize() == day_before]
            
            if '实收价格' in product_df.columns and sales_col in product_df.columns:
                y_sales = yesterday_data[sales_col].sum()
                d_sales = day_before_data[sales_col].sum()
                y_avg_price = (yesterday_data['实收价格'] * yesterday_data[sales_col]).sum() / y_sales if y_sales > 0 else 0
                d_avg_price = (day_before_data['实收价格'] * day_before_data[sales_col]).sum() / d_sales if d_sales > 0 else 0
                result['price_change'] = {
                    '昨日均价': round(y_avg_price, 2),
                    '前日均价': round(d_avg_price, 2),
                    '变化率': round((y_avg_price - d_avg_price) / d_avg_price * 100, 2) if d_avg_price > 0 else 0
                }
            
            if '满减金额' in product_df.columns:
                y_activity = (yesterday_data['满减金额'] > 0).sum() / len(yesterday_data) * 100 if len(yesterday_data) > 0 else 0
                d_activity = (day_before_data['满减金额'] > 0).sum() / len(day_before_data) * 100 if len(day_before_data) > 0 else 0
                result['activity_change'] = {
                    '昨日满减占比': round(y_activity, 1),
                    '前日满减占比': round(d_activity, 1),
                    '变化': round(y_activity - d_activity, 1)
                }
        
        insights = []
        if result['price_change'] and result['price_change'].get('变化率', 0) < -5:
            insights.append(f"售价下降{abs(result['price_change']['变化率'])}%")
        if result['activity_change'] and result['activity_change'].get('变化', 0) > 10:
            insights.append(f"满减活动参与增加{result['activity_change']['变化']}个百分点")
        
        result['insight'] = '初步判断: ' + '，'.join(insights) if insights else '暂无明显异常原因'
        return result
        
    except Exception as e:
        result['error'] = f'获取商品洞察时出错: {str(e)}'
        return result


# ============== 兼容旧API ==============

def get_declining_products(df: pd.DataFrame, top_n: int = 10) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """兼容旧API的包装函数"""
    result = analyze_product_fluctuation(df, top_n)
    if result['error']:
        return None, result['error']
    return result['top_declining'], None


def identify_slow_moving_products(df: pd.DataFrame, as_of_date: Optional[pd.Timestamp] = None) -> Dict[str, pd.Series]:
    """兼容旧API的包装函数"""
    result = analyze_slow_moving_products(df)
    if result['error']:
        return {
            'light': pd.Series(dtype=float),
            'medium': pd.Series(dtype=float),
            'severe': pd.Series(dtype=float),
            'error': result['error']
        }
    
    def df_to_series(df_temp):
        if len(df_temp) == 0:
            return pd.Series(dtype=int)
        return df_temp.set_index('商品名称')['无销量天数']
    
    return {
        'light': df_to_series(result['light']),
        'medium': df_to_series(result['medium']),
        'severe': df_to_series(result['severe']),
        'error': None
    }


# ============== 增强版单品洞察 (V2.0) ==============

def get_product_insight_enhanced(df: pd.DataFrame, product_name: str) -> Dict[str, Any]:
    """
    增强版单品洞察 - 全面分析单个商品
    
    返回结构:
    {
        'product_name': str,           # 商品名称
        'summary': {                   # 汇总指标
            'total_sales': float,      # 总销售额
            'total_profit': float,     # 总利润
            'total_quantity': int,     # 总销量（订单数）
            'avg_price': float,        # 平均单价
            'avg_margin': float,       # 平均毛利率(%)
            'avg_profit_per_order': float,  # 平均订单利润
        },
        'daily_trend': pd.DataFrame,   # 按日趋势: 日期, 销量, 销售额, 利润, 实收利润率, 定价利润率
        'hourly_trend': pd.DataFrame,  # 按时段趋势: 小时, 销量, 销售额, 利润, 实收利润率, 定价利润率
        'partners': pd.DataFrame,      # 最佳拍档: 商品名称, 频次, 一级分类
        'role_daily': pd.DataFrame,    # 购买角色按日分布: 日期, 角色, 销量
        'price_sensitivity': {         # 价格敏感度分析
            'correlation': float,      # 价格-销量相关系数
            'level': str,              # 敏感度等级
            'color': str,              # 对应颜色
        },
        'recommendations': list,       # 推荐行动列表
        'error': str or None
    }
    """
    result = {
        'product_name': product_name,
        'summary': {},
        'daily_trend': pd.DataFrame(),
        'hourly_trend': pd.DataFrame(),
        'partners': pd.DataFrame(),
        'role_daily': pd.DataFrame(),
        'price_sensitivity': {},
        'recommendations': [],
        'error': None
    }
    
    try:
        # ========== 1. 基础数据准备 ==========
        date_col = '日期' if '日期' in df.columns else '下单时间'
        sales_col = '月售' if '月售' in df.columns else '销量'
        
        # 检测一级分类列
        category_col = None
        for col_name in ['一级分类名', '美团一级分类', '一级分类']:
            if col_name in df.columns:
                category_col = col_name
                break
        
        product_df = df[df['商品名称'] == product_name].copy()
        
        if len(product_df) == 0:
            result['error'] = f'未找到商品: {product_name}'
            return result
        
        # 确保日期格式正确
        product_df[date_col] = pd.to_datetime(product_df[date_col])
        product_df['_date'] = product_df[date_col].dt.date
        product_df['_hour'] = product_df[date_col].dt.hour
        
        # 确保数值列存在且正确
        numeric_cols = ['实收价格', '利润额', '商品采购成本', '满减金额', '商品原价']
        for col in numeric_cols:
            if col in product_df.columns:
                product_df[col] = pd.to_numeric(product_df[col], errors='coerce').fillna(0)
        
        # 销量字段
        sales_col = '月售' if '月售' in product_df.columns else '销量'
        if sales_col in product_df.columns:
            product_df[sales_col] = pd.to_numeric(product_df[sales_col], errors='coerce').fillna(1)
        else:
            product_df[sales_col] = 1
        
        # 如果没有利润额，计算它
        if '利润额' not in product_df.columns:
            if '商品采购成本' in product_df.columns:
                # 注意：商品采购成本已经是总成本(单品成本×月售)，利润额也应该是总利润
                product_df['利润额'] = product_df['实收价格'] * product_df[sales_col] - product_df['商品采购成本']
            else:
                product_df['利润额'] = 0
        
        # ⚠️ 计算实收金额 = 实收价格(单价) × 月售(销量)
        product_df['_实收金额'] = product_df['实收价格'] * product_df[sales_col]
        
        # ========== 2. 汇总指标 ==========
        # 销售额 = 实收价格 × 月售 (实收价格是单价，需乘以销量)
        total_sales = product_df['_实收金额'].sum()
        total_profit = product_df['利润额'].sum()
        total_quantity = product_df['订单ID'].nunique()
        avg_price = total_sales / total_quantity if total_quantity > 0 else 0
        avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
        avg_profit_per_order = total_profit / total_quantity if total_quantity > 0 else 0
        
        result['summary'] = {
            'total_sales': round(total_sales, 2),
            'total_profit': round(total_profit, 2),
            'total_quantity': total_quantity,
            'avg_price': round(avg_price, 2),
            'avg_margin': round(avg_margin, 1),
            'avg_profit_per_order': round(avg_profit_per_order, 2),
        }
        
        # ========== 3. 按日趋势（价格敏感度维度） ==========
        # 使用_实收金额(已乘以销量)作为销售额
        daily_agg = product_df.groupby('_date').agg({
            '订单ID': 'nunique',
            '_实收金额': 'sum',  # 实收价格×月售
            '利润额': 'sum',
        }).reset_index()
        daily_agg.columns = ['日期', '销量', '销售额', '利润额']
        
        # 计算平均单价
        daily_agg['平均单价'] = np.where(
            daily_agg['销量'] > 0,
            (daily_agg['销售额'] / daily_agg['销量']).round(2),
            0
        )
        
        # 计算实收利润率 = 利润额 / 销售额 * 100
        # 限制在合理范围内 (-100% ~ 100%)，避免极端值
        raw_margin = np.where(
            daily_agg['销售额'] > 0,
            (daily_agg['利润额'] / daily_agg['销售额']) * 100,
            0
        )
        daily_agg['实收利润率'] = np.clip(raw_margin, -100, 100).round(1)
        
        # 计算定价利润率（需要商品原价和成本）
        # 定价利润率 = (商品原价 - 商品采购成本) / 商品原价 × 100
        # 注意：商品原价为0或无效时，使用实收利润率代替
        if '商品原价' in product_df.columns and '商品采购成本' in product_df.columns:
            # 只统计有效的商品原价（>0）
            valid_pricing_data = product_df[product_df['商品原价'] > 0].copy()
            if not valid_pricing_data.empty:
                daily_cost = valid_pricing_data.groupby('_date').agg({
                    '商品原价': 'sum',
                    '商品采购成本': 'sum'
                }).reset_index()
                daily_cost.columns = ['日期', '_原价总额', '_成本总额']
                daily_agg = daily_agg.merge(daily_cost, on='日期', how='left')
                daily_agg['_原价总额'] = daily_agg['_原价总额'].fillna(0)
                daily_agg['_成本总额'] = daily_agg['_成本总额'].fillna(0)
                
                # 当原价总额有效时计算定价利润率，否则使用实收利润率
                raw_pricing_margin = np.where(
                    daily_agg['_原价总额'] > 0,
                    ((daily_agg['_原价总额'] - daily_agg['_成本总额']) / daily_agg['_原价总额']) * 100,
                    daily_agg['实收利润率']  # 无有效原价时用实收利润率代替
                )
                daily_agg['定价利润率'] = np.clip(raw_pricing_margin, -100, 100).round(1)
                daily_agg = daily_agg.drop(columns=['_原价总额', '_成本总额'])
            else:
                # 所有商品原价都为0或无效
                daily_agg['定价利润率'] = daily_agg['实收利润率']
        else:
            daily_agg['定价利润率'] = daily_agg['实收利润率']  # 无原价时等同实收利润率
        
        daily_agg = daily_agg.sort_values('日期')
        daily_agg['日期'] = pd.to_datetime(daily_agg['日期'])
        result['daily_trend'] = daily_agg
        
        # ========== 4. 按时段趋势（时段画像维度） ==========
        # 使用_实收金额(已乘以销量)作为销售额
        hourly_agg = product_df.groupby('_hour').agg({
            '订单ID': 'nunique',
            '_实收金额': 'sum',  # 实收价格×月售
            '利润额': 'sum',
        }).reset_index()
        hourly_agg.columns = ['小时', '销量', '销售额', '利润额']
        
        # 补全24小时
        full_hours = pd.DataFrame({'小时': range(24)})
        hourly_agg = full_hours.merge(hourly_agg, on='小时', how='left').fillna(0)
        
        # 计算时段指标
        hourly_agg['平均单价'] = np.where(
            hourly_agg['销量'] > 0,
            (hourly_agg['销售额'] / hourly_agg['销量']).round(2),
            0
        )
        # 利润率限制在合理范围内 (-100% ~ 100%)
        raw_hourly_margin = np.where(
            hourly_agg['销售额'] > 0,
            (hourly_agg['利润额'] / hourly_agg['销售额']) * 100,
            0
        )
        hourly_agg['实收利润率'] = np.clip(raw_hourly_margin, -100, 100).round(1)
        
        # 计算定价利润率（按时段）
        # 定价利润率 = (商品原价 - 商品采购成本) / 商品原价 × 100
        # 注意：商品原价为0或无效时，使用实收利润率代替
        if '商品原价' in product_df.columns and '商品采购成本' in product_df.columns:
            # 只统计有效的商品原价（>0）
            valid_pricing_data = product_df[product_df['商品原价'] > 0].copy()
            if not valid_pricing_data.empty:
                hourly_cost = valid_pricing_data.groupby('_hour').agg({
                    '商品原价': 'sum',
                    '商品采购成本': 'sum'
                }).reset_index()
                hourly_cost.columns = ['小时', '_原价总额', '_成本总额']
                hourly_agg = hourly_agg.merge(hourly_cost, on='小时', how='left')
                hourly_agg['_原价总额'] = hourly_agg['_原价总额'].fillna(0)
                hourly_agg['_成本总额'] = hourly_agg['_成本总额'].fillna(0)
                
                # 当原价总额有效时计算定价利润率，否则使用实收利润率
                raw_hourly_pricing = np.where(
                    hourly_agg['_原价总额'] > 0,
                    ((hourly_agg['_原价总额'] - hourly_agg['_成本总额']) / hourly_agg['_原价总额']) * 100,
                    hourly_agg['实收利润率']  # 无有效原价时用实收利润率代替
                )
                hourly_agg['定价利润率'] = np.clip(raw_hourly_pricing, -100, 100).round(1)
                hourly_agg = hourly_agg.drop(columns=['_原价总额', '_成本总额'])
            else:
                # 所有商品原价都为0或无效
                hourly_agg['定价利润率'] = hourly_agg['实收利润率']
        else:
            hourly_agg['定价利润率'] = hourly_agg['实收利润率']
        
        result['hourly_trend'] = hourly_agg
        
        # ========== 5. 最佳拍档（剔除耗材） ==========
        order_ids = product_df['订单ID'].unique()
        
        # 获取同单商品
        related_orders = df[df['订单ID'].isin(order_ids)].copy()
        partners = related_orders[related_orders['商品名称'] != product_name].copy()
        
        if not partners.empty and category_col:
            # 剔除耗材分类
            partners = partners[partners[category_col] != '耗材'].copy()
        
        if not partners.empty:
            # 统计频次并保留分类信息
            if category_col:
                partner_stats = partners.groupby('商品名称').agg({
                    '订单ID': 'nunique',
                    category_col: 'first'
                }).reset_index()
                partner_stats.columns = ['商品名称', '频次', '一级分类']
            else:
                partner_stats = partners.groupby('商品名称')['订单ID'].nunique().reset_index()
                partner_stats.columns = ['商品名称', '频次']
                partner_stats['一级分类'] = '-'
            
            partner_stats = partner_stats.sort_values('频次', ascending=False).head(10)
            result['partners'] = partner_stats
        
        # ========== 6. 购买角色分析（单品日记） ==========
        # 计算每个订单的总金额
        order_totals = related_orders.groupby('订单ID')['实收价格'].sum().to_dict()
        
        def get_role(row):
            if row['利润额'] < 0:
                return '亏损引流'
            total = order_totals.get(row['订单ID'], 0)
            if total == 0:
                return '核心需求'
            ratio = row['实收价格'] / total
            if ratio > 0.6:
                return '核心需求'  # 主买
            elif ratio < 0.3:
                return '凑单配角'  # 顺手买
            else:
                return '核心需求'
        
        product_df['_role'] = product_df.apply(get_role, axis=1)
        
        role_daily = product_df.groupby(['_date', '_role'])['订单ID'].nunique().reset_index()
        role_daily.columns = ['日期', '角色', '销量']
        role_daily['日期'] = pd.to_datetime(role_daily['日期'])
        result['role_daily'] = role_daily
        
        # ========== 7. 价格敏感度分析 ==========
        correlation = 0
        sensitivity_level = '数据不足'
        sensitivity_color = 'gray'
        
        if len(daily_agg) > 3:
            correlation = daily_agg['平均单价'].corr(daily_agg['销量'])
            
            if pd.isna(correlation):
                correlation = 0
            
            if correlation < -0.6:
                sensitivity_level = '高敏感'
                sensitivity_color = 'red'
            elif correlation < -0.3:
                sensitivity_level = '中等敏感'
                sensitivity_color = 'orange'
            elif correlation < 0:
                sensitivity_level = '低敏感'
                sensitivity_color = 'green'
            else:
                sensitivity_level = '不敏感'
                sensitivity_color = 'blue'
        
        result['price_sensitivity'] = {
            'correlation': round(correlation, 3),
            'level': sensitivity_level,
            'color': sensitivity_color,
        }
        
        # ========== 8. 智能建议 ==========
        recommendations = []
        avg_margin_val = result['summary']['avg_margin']
        
        # 规则1: 负毛利预警
        if avg_margin_val < 0:
            recommendations.append({
                'title': '🛑 止损建议',
                'desc': '当前商品处于亏损状态，建议立即检查成本配置或提高售价。',
                'type': 'danger'
            })
        
        # 规则2: 低毛利 + 低敏感 -> 涨价
        elif avg_margin_val < 15 and correlation > -0.3:
            recommendations.append({
                'title': '💰 涨价机会',
                'desc': '用户对价格不敏感且当前毛利较低，建议尝试提价以提升利润。',
                'type': 'success'
            })
        
        # 规则3: 高毛利 + 高敏感 -> 促销
        elif avg_margin_val > 40 and correlation < -0.6:
            recommendations.append({
                'title': '📢 以价换量',
                'desc': '用户对价格高度敏感且毛利空间充足，可尝试短期促销拉动销量。',
                'type': 'info'
            })
        
        # 规则4: 核心商品识别
        if len(result['role_daily']) > 0:
            core_ratio = result['role_daily'][result['role_daily']['角色'] == '核心需求']['销量'].sum()
            total_role = result['role_daily']['销量'].sum()
            if total_role > 0 and core_ratio / total_role > 0.7:
                recommendations.append({
                    'title': '⭐ 核心商品',
                    'desc': '该商品主要作为顾客的核心需求购买，是门店的引流商品。',
                    'type': 'primary'
                })
        
        if not recommendations:
            recommendations.append({
                'title': '✅ 维持现状',
                'desc': '当前商品表现平稳，建议继续保持当前策略。',
                'type': 'secondary'
            })
        
        result['recommendations'] = recommendations
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        result['error'] = f'获取商品洞察时出错: {str(e)}'
        return result
