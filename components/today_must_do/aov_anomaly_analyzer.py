"""
客单价异常分析器 - 订单金额分布分析
功能: 诊断客单价下降的根本原因
- 订单分布维度: 分析各价格带订单数量变化，找出下滑区间
- 商品拖累维度: 识别拖累客单价的商品和机会商品

🎯 核心逻辑:
  客单价 = 实收价格总和 / 订单总数
  (与Tab1"订单数据概览"保持完全一致，使用order_agg['实收价格'])
  
  📌 字段说明:
    - 实收价格: 消费者实际支付金额（平台补贴后），反映真实购买力 ✅
    - 商品实售价: 商品折扣价（不含平台补贴），反映商家定价策略
  
  通过分析不同价格带的订单数量变化，找出客单价下降的具体原因
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional


def analyze_category_contribution(
    df: pd.DataFrame,
    order_agg: pd.DataFrame,
    period_days: int = 30
) -> Dict:
    """
    分析分类对客单价的贡献变化
    
    核心逻辑:
    - 贡献度 = (分类销量 / 总订单数) × 分类平均单价
    - 对比历史期vs近期，找出贡献度变化最大的分类
    - 识别哪些分类导致了客单价下降
    
    参数:
        df: 原始订单数据（必须包含：日期、一级分类名、实收价格、订单ID）
        order_agg: 订单聚合数据
        period_days: 分析周期
    
    返回:
        {
            'category_changes': [...],  # 分类贡献度变化列表
            'top_decline': [...],        # TOP5贡献度下降分类
            'top_growth': [...],         # TOP5贡献度增长分类
            'summary': {...}             # 汇总统计
        }
    """
    
    print(f"🔍 [分类贡献度分析] 开始分析")
    
    # 检查必需字段
    if '一级分类名' not in df.columns:
        print(f"  ❌ 缺少'一级分类名'字段")
        return _empty_category_result()
    
    if '实收价格' not in df.columns:
        print(f"  ❌ 缺少'实收价格'字段")
        return _empty_category_result()
    
    if '日期' not in df.columns:
        print(f"  ❌ 缺少'日期'字段")
        return _empty_category_result()
    
    # 确保日期格式
    df['日期'] = pd.to_datetime(df['日期'])
    
    # 智能日期范围计算
    max_date = df['日期'].max()
    min_date = df['日期'].min()
    data_days = (max_date - min_date).days + 1
    
    original_period = period_days
    data_warning = None
    
    if data_days < period_days * 2:
        if data_days >= 14:
            period_days = 7
            data_warning = f"数据仅{data_days}天，已自动切换为7天对比周期"
        else:
            print(f"  ❌ 数据仅{data_days}天，至少需要14天数据")
            return _empty_category_result()
        print(f"  ⚠️ {data_warning}")
    
    recent_start = max_date - timedelta(days=period_days)
    history_start = max_date - timedelta(days=period_days * 2)
    
    # 筛选数据
    history_df = df[(df['日期'] >= history_start) & (df['日期'] < recent_start)].copy()
    recent_df = df[df['日期'] >= recent_start].copy()
    
    if len(history_df) == 0 or len(recent_df) == 0:
        print(f"  ❌ 数据不足")
        return _empty_category_result()
    
    # 二次验证
    history_order_count_pre = history_df['订单ID'].nunique()
    recent_order_count_pre = recent_df['订单ID'].nunique()
    
    if history_order_count_pre < recent_order_count_pre * 0.3:
        if data_warning is None:
            data_warning = f"历史期数据较少，对比结果仅供参考"
        print(f"  ⚠️ 历史期订单数{history_order_count_pre}，近期{recent_order_count_pre}")
    
    # 统计订单数
    history_order_count = history_df['订单ID'].nunique()
    recent_order_count = recent_df['订单ID'].nunique()
    
    print(f"  📊 历史期订单数: {history_order_count}")
    print(f"  📊 近期订单数: {recent_order_count}")
    
    # 按分类统计
    def calc_category_stats(data, order_count):
        """计算分类统计指标"""
        stats = data.groupby('一级分类名').agg({
            '订单ID': 'nunique',
            '实收价格': 'sum'
        }).reset_index()
        stats.columns = ['分类', '订单数', '销售额']
        stats['平均单价'] = stats['销售额'] / stats['订单数']
        stats['销量占比'] = (stats['订单数'] / order_count * 100).round(2)
        stats['贡献度'] = (stats['订单数'] / order_count) * stats['平均单价']
        return stats
    
    history_stats = calc_category_stats(history_df, history_order_count)
    recent_stats = calc_category_stats(recent_df, recent_order_count)
    
    # 合并对比
    comparison = history_stats.merge(
        recent_stats,
        on='分类',
        how='outer',
        suffixes=('_历史', '_近期')
    ).fillna(0)
    
    # 计算变化
    comparison['贡献度变化'] = comparison['贡献度_近期'] - comparison['贡献度_历史']
    comparison['销量占比变化'] = comparison['销量占比_近期'] - comparison['销量占比_历史']
    comparison['平均单价变化'] = comparison['平均单价_近期'] - comparison['平均单价_历史']
    
    # 排序
    comparison = comparison.sort_values('贡献度变化')
    
    # 提取TOP榜单
    top_decline = comparison.head(5).to_dict('records')  # 贡献度下降TOP5
    top_growth = comparison.tail(5).iloc[::-1].to_dict('records')  # 贡献度增长TOP5
    
    # 统计
    decline_categories = comparison[comparison['贡献度变化'] < 0]
    total_decline_contribution = decline_categories['贡献度变化'].sum()
    
    summary = {
        'history_start': history_start.strftime('%Y-%m-%d'),
        'history_end': recent_start.strftime('%Y-%m-%d'),
        'recent_start': recent_start.strftime('%Y-%m-%d'),
        'recent_end': max_date.strftime('%Y-%m-%d'),
        'total_categories': len(comparison),
        'decline_categories': len(decline_categories),
        'total_decline_contribution': total_decline_contribution,
        'period_days': period_days,
        'original_period': original_period,
        'data_warning': data_warning
    }
    
    print(f"✅ [分类贡献度分析] 完成")
    
    return {
        'category_changes': comparison.to_dict('records'),
        'top_decline': top_decline,
        'top_growth': top_growth,
        'summary': summary
    }


def _empty_category_result() -> Dict:
    """返回空的分类分析结果"""
    return {
        'category_changes': [],
        'top_decline': [],
        'top_growth': [],
        'summary': {
            'total_categories': 0,
            'decline_categories': 0,
            'total_decline_contribution': 0
        }
    }


def analyze_channel_comparison(
    df: pd.DataFrame,
    order_agg: pd.DataFrame,
    period_days: int = 30
) -> Dict:
    """
    分析各渠道客单价对比
    
    返回:
        {
            'channel_stats': [...],  # 各渠道统计数据
            'abnormal_channels': [...],  # 异常渠道（变化>10%）
            'summary': {...}
        }
    """
    
    print(f"🔍 [渠道对比分析] 开始分析")
    
    if '渠道' not in df.columns:
        print(f"  ❌ 缺少'渠道'字段")
        return {'channel_stats': [], 'abnormal_channels': [], 'summary': {}}
    
    if '日期' not in df.columns:
        print(f"  ❌ 缺少'日期'字段")
        return {'channel_stats': [], 'abnormal_channels': [], 'summary': {}}
    
    # 确保日期格式
    df['日期'] = pd.to_datetime(df['日期'])
    
    # 计算日期范围
    max_date = df['日期'].max()
    recent_start = max_date - timedelta(days=period_days)
    history_start = max_date - timedelta(days=period_days * 2)
    
    # 筛选数据
    history_df = df[(df['日期'] >= history_start) & (df['日期'] < recent_start)].copy()
    recent_df = df[df['日期'] >= recent_start].copy()
    
    if len(history_df) == 0 or len(recent_df) == 0:
        print(f"  ❌ 数据不足")
        return {'channel_stats': [], 'abnormal_channels': [], 'summary': {}}
    
    # 按渠道统计
    def calc_channel_stats(data):
        """计算渠道统计指标"""
        stats = data.groupby('渠道').agg({
            '订单ID': 'nunique',
            '实收价格': 'sum'
        }).reset_index()
        stats.columns = ['渠道', '订单数', '销售额']
        stats['客单价'] = (stats['销售额'] / stats['订单数']).round(2)
        return stats
    
    history_stats = calc_channel_stats(history_df)
    recent_stats = calc_channel_stats(recent_df)
    
    # 合并对比
    comparison = history_stats.merge(
        recent_stats,
        on='渠道',
        how='outer',
        suffixes=('_历史', '_近期')
    ).fillna(0)
    
    # 计算变化
    comparison['客单价变化'] = comparison['客单价_近期'] - comparison['客单价_历史']
    comparison['变化率'] = ((comparison['客单价变化'] / comparison['客单价_历史']) * 100).round(1)
    comparison['订单数变化'] = comparison['订单数_近期'] - comparison['订单数_历史']
    
    # 识别异常渠道（变化率>10%或<-10%）
    abnormal = comparison[abs(comparison['变化率']) > 10].to_dict('records')
    
    # 排序（按订单数_近期降序）
    comparison = comparison.sort_values('订单数_近期', ascending=False)
    
    summary = {
        'total_channels': len(comparison),
        'abnormal_count': len(abnormal)
    }
    
    print(f"✅ [渠道对比分析] 完成，共{len(comparison)}个渠道，{len(abnormal)}个异常")
    
    return {
        'channel_stats': comparison.to_dict('records'),
        'abnormal_channels': abnormal,
        'summary': summary
    }


def analyze_customer_downgrade(
    df: pd.DataFrame,
    order_agg: pd.DataFrame,
    period_days: int = 30
) -> Dict:
    """
    分析订单金额分布变化（订单维度，非客户维度）
    
    ⚠️ 业务场景：O2O外卖场景，客户识别度低，不适合客户级别分析
    ✅ 新方案：分析订单金额分布变化，找出问题价格带
    
    核心逻辑:
    1. 将订单按金额分档（¥0-10, ¥10-20, ¥20-30, ..., ¥100+）
    2. 对比历史期vs近期，各价格带的订单数量变化
    3. 标注下滑最严重的价格带（绝对数量下降）
    4. 给出可能原因和优化建议
    
    参数:
        df: 原始订单数据
        order_agg: 订单聚合数据（必须包含'商品实售价'字段）
        period_days: 分析周期(7/15/30天)
    
    返回:
        {
            'severe': [...],      # 订单数下降>30%的价格带
            'moderate': [...],    # 订单数下降15-30%的价格带
            'mild': [...],        # 订单数下降<15%的价格带
            'trend': {...},       # 趋势数据
            'summary': {...}      # 汇总统计
        }
    """
    
    print(f"🔍 [订单分布分析] 开始分析客单价异常")
    print(f"  df.shape = {df.shape}")
    print(f"  order_agg.shape = {order_agg.shape}")
    
    # ========== 1. 检查必需字段 ==========
    
    # 检查日期字段
    date_col = None
    if '日期' in order_agg.columns:
        date_col = '日期'
    elif '下单时间' in order_agg.columns:
        date_col = '下单时间'
        order_agg['日期'] = order_agg['下单时间']
        date_col = '日期'
    elif '日期' in df.columns or '下单时间' in df.columns:
        # 从df中补充日期
        df_date_col = '日期' if '日期' in df.columns else '下单时间'
        if '订单ID' in df.columns and '订单ID' in order_agg.columns:
            print(f"  🔧 从df中提取日期字段: {df_date_col}")
            df[df_date_col] = pd.to_datetime(df[df_date_col])
            order_date_map = df.groupby('订单ID')[df_date_col].first().reset_index()
            order_date_map.columns = ['订单ID', '日期']
            order_date_map['订单ID'] = order_date_map['订单ID'].astype(str)
            order_agg['订单ID'] = order_agg['订单ID'].astype(str)
            order_agg = order_agg.merge(order_date_map, on='订单ID', how='left')
            date_col = '日期'
            print(f"  ✅ 日期字段已添加")
    
    if date_col is None:
        print(f"  ❌ 缺少日期字段")
        return _empty_distribution_result()
    
    # 检查客单价字段（必须使用'实收价格'，与Tab1订单数据概览一致）
    if '实收价格' not in order_agg.columns:
        print(f"  ❌ 缺少'实收价格'字段，无法计算客单价")
        print(f"  📌 提示: 客单价 = 实收价格总和 / 订单数（消费者实际支付金额）")
        print(f"  📌 实收价格 = 平台补贴后价格（反映真实购买力）")
        return _empty_distribution_result()
    
    # 确保日期格式
    order_agg['日期'] = pd.to_datetime(order_agg['日期'])
    
    # ========== 2. 智能日期范围计算（自动降级）==========
    max_date = order_agg['日期'].max()
    min_date = order_agg['日期'].min()
    data_days = (max_date - min_date).days + 1
    
    # 智能降级逻辑
    original_period = period_days
    data_warning = None
    
    if data_days < period_days * 2:
        # 数据不足，自动降级
        if data_days >= 14:
            period_days = 7
            data_warning = f"数据仅{data_days}天，已自动切换为7天对比周期"
        else:
            # 数据太少，无法分析
            print(f"  ❌ 数据仅{data_days}天，至少需要14天数据")
            return _empty_distribution_result()
        
        print(f"  ⚠️ {data_warning}")
    
    recent_start = max_date - timedelta(days=period_days)
    history_start = max_date - timedelta(days=period_days * 2)
    
    print(f"  📅 分析周期: {period_days}天 {'（已自动降级）' if original_period != period_days else ''}")
    print(f"      历史期: {history_start.date()} ~ {recent_start.date()}")
    print(f"      近期: {recent_start.date()} ~ {max_date.date()}")
    print(f"      数据覆盖: {data_days}天")
    
    # 筛选数据
    history_orders = order_agg[
        (order_agg['日期'] >= history_start) & 
        (order_agg['日期'] < recent_start)
    ].copy()
    
    recent_orders = order_agg[
        order_agg['日期'] >= recent_start
    ].copy()
    
    print(f"  📊 历史期订单数: {len(history_orders)}")
    print(f"  📊 近期订单数: {len(recent_orders)}")
    
    # 二次验证：历史期数据不足30%时警告
    if len(history_orders) < len(recent_orders) * 0.3:
        if data_warning is None:
            data_warning = f"历史期数据较少（{len(history_orders)}单），对比结果仅供参考"
        print(f"  ⚠️ {data_warning}")
    
    if len(history_orders) == 0 or len(recent_orders) == 0:
        print(f"  ❌ 数据不足，无法对比")
        return _empty_distribution_result()
    
    # ========== 3. 计算整体客单价（与订单数据概览保持一致）==========
    history_total_sales = history_orders['实收价格'].sum()
    history_order_count = len(history_orders)
    history_aov = history_total_sales / history_order_count if history_order_count > 0 else 0
    
    recent_total_sales = recent_orders['实收价格'].sum()
    recent_order_count = len(recent_orders)
    recent_aov = recent_total_sales / recent_order_count if recent_order_count > 0 else 0
    
    aov_change = recent_aov - history_aov
    aov_change_rate = (aov_change / history_aov * 100) if history_aov > 0 else 0
    
    print(f"  💰 整体客单价对比:")
    print(f"      历史期: ¥{history_aov:.2f}")
    print(f"      近期: ¥{recent_aov:.2f}")
    print(f"      变化: ¥{aov_change:+.2f} ({aov_change_rate:+.1f}%)")
    
    # ========== 4. 订单金额分布分析 ==========
    
    # 定义价格带（与Tab1的客单价分析保持一致）
    bins = [0, 10, 20, 30, 40, 50, 100, 200, float('inf')]
    labels = ['¥0-10', '¥10-20', '¥20-30', '¥30-40', '¥40-50', '¥50-100', '¥100-200', '¥200+']
    
    # 为订单分配价格带
    history_orders['价格带'] = pd.cut(history_orders['实收价格'], bins=bins, labels=labels, right=False)
    recent_orders['价格带'] = pd.cut(recent_orders['实收价格'], bins=bins, labels=labels, right=False)
    
    # 统计各价格带订单数
    history_dist = history_orders['价格带'].value_counts().to_dict()
    recent_dist = recent_orders['价格带'].value_counts().to_dict()
    
    print(f"\n  📈 订单金额分布对比:")
    
    # 计算每个价格带的变化
    distribution_changes = []
    for label in labels:
        history_count = history_dist.get(label, 0)
        recent_count = recent_dist.get(label, 0)
        change_count = recent_count - history_count
        change_rate = (change_count / history_count * 100) if history_count > 0 else 0
        
        distribution_changes.append({
            '价格带': label,
            '历史期订单数': history_count,
            '近期订单数': recent_count,
            '变化数量': change_count,
            '变化率': change_rate,
            '历史期占比': (history_count / history_order_count * 100) if history_order_count > 0 else 0,
            '近期占比': (recent_count / recent_order_count * 100) if recent_order_count > 0 else 0
        })
        
        print(f"      {label:10s}: {history_count:4d} → {recent_count:4d} ({change_count:+4d}, {change_rate:+6.1f}%)")
    
    # ========== 5. 按严重程度分级 ==========
    
    # 只关注订单数下降的价格带
    declining_segments = [seg for seg in distribution_changes if seg['变化数量'] < 0]
    
    severe_list = []   # 订单数下降>30%
    moderate_list = [] # 订单数下降15-30%
    mild_list = []     # 订单数下降<15%
    
    for seg in declining_segments:
        if seg['变化率'] < -30:
            severe_list.append(seg)
        elif seg['变化率'] < -15:
            moderate_list.append(seg)
        else:
            mild_list.append(seg)
    
    print(f"\n  🔴 重度下滑: {len(severe_list)}个价格带 (订单数下降>30%)")
    print(f"  🟡 中度下滑: {len(moderate_list)}个价格带 (订单数下降15-30%)")
    print(f"  🟢 轻度下滑: {len(mild_list)}个价格带 (订单数下降<15%)")
    
    # ========== 6. 生成诊断建议 ==========
    
    # 找出下降最严重的价格带
    if severe_list:
        worst_segment = min(severe_list, key=lambda x: x['变化率'])
    elif moderate_list:
        worst_segment = min(moderate_list, key=lambda x: x['变化率'])
    elif mild_list:
        worst_segment = min(mild_list, key=lambda x: x['变化率'])
    else:
        worst_segment = None
    
    # 生成建议
    suggestions = []
    if worst_segment:
        suggestions.append({
            '问题': f"{worst_segment['价格带']}订单大幅下降",
            '具体': f"订单数从{worst_segment['历史期订单数']}降至{worst_segment['近期订单数']}（下降{abs(worst_segment['变化率']):.1f}%）",
            '建议': f"检查该价格带商品供应、优惠活动、竞品情况"
        })
    
    # 检查低价订单占比是否上升
    low_price_history = sum([seg['历史期订单数'] for seg in distribution_changes if seg['价格带'] in ['¥0-10', '¥10-20']])
    low_price_recent = sum([seg['近期订单数'] for seg in distribution_changes if seg['价格带'] in ['¥0-10', '¥10-20']])
    low_price_history_rate = (low_price_history / history_order_count * 100) if history_order_count > 0 else 0
    low_price_recent_rate = (low_price_recent / recent_order_count * 100) if recent_order_count > 0 else 0
    
    if low_price_recent_rate > low_price_history_rate + 5:
        suggestions.append({
            '问题': '低价订单占比上升',
            '具体': f"¥0-20订单占比从{low_price_history_rate:.1f}%升至{low_price_recent_rate:.1f}%",
            '建议': '考虑推广中高价商品、设置满减门槛'
        })
    
    # ========== 7. 生成趋势数据（按天统计）==========
    
    # 计算每天的客单价、订单数、订单均销量
    trend_data = {
        'dates': [],
        'aov_values': [],          # 客单价趋势
        'order_counts': [],        # 订单数趋势
        'avg_quantity': [],        # 订单均销量趋势
        'severe_count': [],
        'moderate_count': [],
        'mild_count': [],
        'total_count': [],
        'distribution': distribution_changes  # 完整的分布数据
    }
    
    # 合并历史期和近期数据用于趋势计算
    all_orders = pd.concat([history_orders, recent_orders])
    all_orders = all_orders.sort_values('日期')
    
    # 按天聚合
    daily_stats = all_orders.groupby(all_orders['日期'].dt.date).agg({
        '实收价格': 'sum',
        '订单ID': 'count'
    }).reset_index()
    daily_stats.columns = ['日期', '销售额', '订单数']
    daily_stats['客单价'] = daily_stats['销售额'] / daily_stats['订单数']
    
    # 计算单均件数（如果有销量字段）
    if '月售' in all_orders.columns:
        daily_quantity = all_orders.groupby(all_orders['日期'].dt.date)['月售'].sum().reset_index()
        daily_quantity.columns = ['日期', '总销量']
        daily_stats = daily_stats.merge(daily_quantity, on='日期', how='left')
        daily_stats['单均件数'] = daily_stats['总销量'] / daily_stats['订单数']
    else:
        daily_stats['单均件数'] = 0
    
    # 填充趋势数据
    for _, row in daily_stats.iterrows():
        trend_data['dates'].append(row['日期'].strftime('%m-%d'))
        trend_data['aov_values'].append(round(row['客单价'], 2))
        trend_data['order_counts'].append(int(row['订单数']))
        trend_data['avg_quantity'].append(round(row['单均件数'], 2) if row['单均件数'] > 0 else 0)
    
    # 价格带下滑数量（简化：使用整体统计）
    for i in range(len(daily_stats)):
        trend_data['severe_count'].append(len(severe_list))
        trend_data['moderate_count'].append(len(moderate_list))
        trend_data['mild_count'].append(len(mild_list))
        trend_data['total_count'].append(len(declining_segments))
    
    # ========== 8. 汇总统计 ==========
    
    summary = {
        'total_downgrade': len(declining_segments),
        'total_changes': len(declining_segments),
        'severe_count': len(severe_list),
        'moderate_count': len(moderate_list),
        'mild_count': len(mild_list),
        'avg_aov': recent_aov,
        'history_avg_aov': history_aov,
        'aov_change_amount': aov_change,
        'aov_change_rate': aov_change_rate,
        'avg_decline': abs(aov_change),
        'max_decline': max([abs(seg['变化率']) for seg in declining_segments]) if declining_segments else 0,
        'period_days': period_days,
        'original_period': original_period,  # 新增：原始请求周期
        'distribution': distribution_changes,
        'suggestions': suggestions,
        # 新增：日期范围信息
        'history_start': history_start.strftime('%Y-%m-%d'),
        'history_end': recent_start.strftime('%Y-%m-%d'),
        'recent_start': recent_start.strftime('%Y-%m-%d'),
        'recent_end': max_date.strftime('%Y-%m-%d'),
        'history_order_count': history_order_count,
        'recent_order_count': recent_order_count,
        'data_warning': data_warning  # 新增：数据不足警告
    }
    
    print(f"✅ [订单分布分析] 完成")
    
    return {
        'severe': severe_list,
        'moderate': moderate_list,
        'mild': mild_list,
        'trend': trend_data,
        'summary': summary
    }


def _analyze_downgrade_reasons(
    customers_df: pd.DataFrame,
    df: pd.DataFrame,
    order_agg: pd.DataFrame,
    recent_start: pd.Timestamp,
    history_start: pd.Timestamp
) -> List[Dict]:
    """分析每个降级客户的原因"""
    
    results = []
    
    for idx, row in customers_df.head(20).iterrows():  # 限制分析前20个
        customer = row['客户地址']
        
        # 获取该客户的历史和近期商品
        history_products = df[
            (df['客户地址'] == customer) & 
            (df['日期'] >= history_start) & 
            (df['日期'] < recent_start)
        ]['商品名称'].value_counts().head(3).index.tolist()
        
        recent_products = df[
            (df['客户地址'] == customer) & 
            (df['日期'] >= recent_start)
        ]['商品名称'].value_counts().head(3).index.tolist()
        
        # 判断原因
        reason, detail = _identify_downgrade_reason(
            customer, history_products, recent_products, df, recent_start
        )
        
        # 生成建议
        suggestion = _generate_suggestion(reason, history_products, row['下降幅度'])
        
        results.append({
            'customer': customer,
            'old_aov': round(row['历史客单价'], 2),
            'new_aov': round(row['近期客单价'], 2),
            'decline_rate': round(row['下降幅度'], 1),
            'reason': reason,
            'detail': detail,
            'old_products': history_products[:2],  # 最多2个
            'new_products': recent_products[:2],
            'suggestion': suggestion
        })
    
    return results


def _identify_downgrade_reason(
    customer: str,
    history_products: List[str],
    recent_products: List[str],
    df: pd.DataFrame,
    recent_start: pd.Timestamp
) -> Tuple[str, str]:
    """识别降级原因"""
    
    # 检查常购商品是否缺货
    if len(history_products) > 0:
        main_product = history_products[0]
        
        # 检查该商品在近期的库存情况
        recent_stock = df[
            (df['商品名称'] == main_product) & 
            (df['日期'] >= recent_start)
        ]
        
        # 如果近期没有该商品的记录,可能缺货
        if len(recent_stock) == 0:
            return '被迫降级', f'{main_product}(缺货)'
        
        # 检查是否涨价(简化判断)
        if '商品实售价' in df.columns:
            history_price = df[
                (df['商品名称'] == main_product) & 
                (df['日期'] < recent_start)
            ]['商品实售价'].mean()
            
            recent_price = recent_stock['商品实售价'].mean()
            
            if recent_price > history_price * 1.2:  # 涨价超过20%
                return '被迫降级', f'{main_product}(涨价{((recent_price/history_price-1)*100):.0f}%)'
    
    # 检查品类是否变化
    if len(history_products) > 0 and len(recent_products) > 0:
        if '一级分类名' in df.columns:
            history_categories = df[
                df['商品名称'].isin(history_products)
            ]['一级分类名'].unique()
            
            recent_categories = df[
                df['商品名称'].isin(recent_products)
            ]['一级分类名'].unique()
            
            # 品类完全不重叠
            if len(set(history_categories) & set(recent_categories)) == 0:
                return '品类转移', f'{history_categories[0]}→{recent_categories[0]}'
    
    # 默认为频次变化
    return '购买习惯变化', '从大单变小单'


def _generate_suggestion(
    reason: str,
    history_products: List[str],
    decline_rate: float
) -> str:
    """生成召回建议"""
    
    if reason == '被迫降级':
        if len(history_products) > 0:
            return f"补货通知+¥{min(abs(int(decline_rate)), 50)}券"
        return "商品补货提醒"
    
    elif reason == '品类转移':
        if len(history_products) > 0:
            # 提取品类(简化)
            return "原品类专区9折券"
        return "品类优惠券"
    
    else:
        # 购买习惯变化
        coupon_amount = max(10, min(abs(int(decline_rate)) // 2, 30))
        return f"满减券¥{coupon_amount}"


def _calculate_downgrade_trend(
    downgrade_customers: pd.DataFrame,
    order_agg: pd.DataFrame,
    max_date: pd.Timestamp,
    period_days: int
) -> Dict:
    """计算降级趋势数据(按天统计)"""
    
    # 生成日期序列
    date_range = pd.date_range(
        end=max_date,
        periods=period_days,
        freq='D'
    )
    
    # 为每个日期计算当天的降级客户数(滚动窗口)
    trend_data = {
        'dates': [d.strftime('%m-%d') for d in date_range],
        'severe_count': [],
        'moderate_count': [],
        'mild_count': [],
        'total_count': []
    }
    
    # 简化版本: 使用最终结果的平均值模拟趋势
    # (完整版本需要对每个日期点重新计算,性能开销大)
    # 🔧 更新阈值匹配主函数: 重度>30%, 中度15-30%, 轻度5-15%
    severe_base = len(downgrade_customers[downgrade_customers['下降幅度'] <= -30])
    moderate_base = len(downgrade_customers[
        (downgrade_customers['下降幅度'] > -30) & 
        (downgrade_customers['下降幅度'] <= -15)
    ])
    mild_base = len(downgrade_customers[downgrade_customers['下降幅度'] > -15])
    
    for i in range(period_days):
        # 添加随机波动模拟真实趋势
        noise = np.random.uniform(0.8, 1.2)
        trend_data['severe_count'].append(int(severe_base * noise))
        trend_data['moderate_count'].append(int(moderate_base * noise))
        trend_data['mild_count'].append(int(mild_base * noise))
        trend_data['total_count'].append(
            trend_data['severe_count'][-1] + 
            trend_data['moderate_count'][-1] + 
            trend_data['mild_count'][-1]
        )
    
    return trend_data


def analyze_product_drag(
    df: pd.DataFrame,
    order_agg: pd.DataFrame,
    period_days: int = 30
) -> Dict:
    """
    分析商品对客单价的影响
    
    参数:
        df: 原始订单数据（必须包含：日期、商品名称、实收价格、订单ID）
        order_agg: 订单聚合数据（必须包含：日期、实收价格）
        period_days: 分析周期(7/15/30天)
    
    返回:
        {
            'low_price_trend': {...},         # 低价商品趋势
            'structure_change': {...},        # 客单价结构变化
            'drag_products': [...],           # TOP5拖累商品
            'opportunity_products': [...],    # TOP5机会商品
            'summary': {...}                  # 汇总统计
        }
    """
    
    print(f"🔍 [商品拖累分析] 开始分析")
    print(f"  df.shape = {df.shape}")
    print(f"  df.columns = {df.columns.tolist()[:20]}...")  # 显示前20个字段
    print(f"  order_agg.shape = {order_agg.shape}")
    print(f"  order_agg.columns = {order_agg.columns.tolist()[:15]}...")  # 显示前15个字段
    
    # ========== 1. 检查order_agg必需字段 ==========
    if '日期' not in order_agg.columns:
        print(f"  ❌ order_agg缺少'日期'字段")
        return _empty_product_result()
    
    if '实收价格' not in order_agg.columns:
        print(f"  ❌ order_agg缺少'实收价格'字段")
        return _empty_product_result()
    
    # ========== 2. 检查df必需字段（商品分析关键）==========
    required_fields_df = ['日期', '商品名称', '订单ID']
    missing_fields = [f for f in required_fields_df if f not in df.columns]
    if missing_fields:
        print(f"  ❌ df缺少必需字段: {missing_fields}")
        return _empty_product_result()
    
    # 检查价格字段（优先使用实收价格）
    price_field = None
    if '实收价格' in df.columns:
        price_field = '实收价格'
        print(f"  ✅ 使用'实收价格'字段进行商品分析")
    elif '商品实售价' in df.columns:
        price_field = '商品实售价'
        print(f"  ⚠️ 使用'商品实售价'字段（建议使用'实收价格'）")
    else:
        print(f"  ❌ df缺少价格字段（'实收价格'或'商品实售价'）")
        return _empty_product_result()
    
    print(f"  ✅ 字段检查通过，开始分析")
    
    # 确保日期格式
    if not pd.api.types.is_datetime64_any_dtype(df['日期']):
        df = df.copy()
        df['日期'] = pd.to_datetime(df['日期'])
    
    if not pd.api.types.is_datetime64_any_dtype(order_agg['日期']):
        order_agg = order_agg.copy()
        order_agg['日期'] = pd.to_datetime(order_agg['日期'])
    
    
    # 计算日期范围
    max_date = order_agg['日期'].max()
    start_date = max_date - timedelta(days=period_days)
    
    # 筛选周期内订单
    period_orders = order_agg[order_agg['日期'] >= start_date].copy()
    
    print(f"  📅 分析周期: {period_days}天 ({start_date.date()} ~ {max_date.date()})")
    print(f"  📊 周期内订单数: {len(period_orders)}")
    
    if len(period_orders) == 0:
        print(f"  ❌ 周期内无订单数据")
        return _empty_product_result()
    
    # 1. 低价商品趋势
    print(f"  🔄 计算低价商品趋势...")
    low_price_trend = _calculate_low_price_trend(period_orders, period_days, max_date)
    
    # 2. 客单价结构变化
    print(f"  🔄 计算客单价结构变化...")
    structure_change = _calculate_structure_change(period_orders, period_days, max_date)
    
    # 3. 识别拖累商品（四层分析）
    print(f"  🔄 识别拖累商品（四层分析）...")
    product_analysis = _identify_drag_products(df, order_agg, start_date, max_date, price_field)
    
    # 4. 识别机会商品
    print(f"  🔄 识别机会商品...")
    opportunity_products = _identify_opportunity_products(df, order_agg, start_date, max_date, price_field)
    
    # 汇总统计
    summary = {
        'period_days': period_days,
        'total_orders': len(period_orders),
        'avg_aov': round(period_orders['实收价格'].mean(), 2),
        'low_price_ratio': low_price_trend['current_ratio'],
        'drag_product_count': len(product_analysis.get('core_drag', [])),
        'high_price_star_count': len(product_analysis.get('high_price', {}).get('star', []))
    }
    
    return {
        'low_price_trend': low_price_trend,
        'structure_change': structure_change,
        'product_analysis': product_analysis,  # 新结构：包含四层分析
        'opportunity_products': opportunity_products,
        'summary': summary
    }


def _calculate_low_price_trend(
    period_orders: pd.DataFrame,
    period_days: int,
    max_date: pd.Timestamp
) -> Dict:
    """计算低价商品占比趋势"""
    
    LOW_PRICE_THRESHOLD = 25  # 低价阈值
    
    # 生成日期序列
    date_range = pd.date_range(
        end=max_date,
        periods=period_days,
        freq='D'
    )
    
    dates_str = [d.strftime('%m-%d') for d in date_range]
    ratios = []
    
    for date in date_range:
        day_orders = period_orders[period_orders['日期'] == date]
        if len(day_orders) > 0:
            low_price_count = len(day_orders[day_orders['实收价格'] < LOW_PRICE_THRESHOLD])
            ratio = (low_price_count / len(day_orders) * 100)
            ratios.append(round(ratio, 1))
        else:
            ratios.append(0)
    
    return {
        'dates': dates_str,
        'ratios': ratios,
        'threshold': LOW_PRICE_THRESHOLD,
        'current_ratio': ratios[-1] if ratios else 0,
        'avg_ratio': round(np.mean(ratios), 1) if ratios else 0,
        'peak_date': dates_str[ratios.index(max(ratios))] if ratios else None,
        'peak_ratio': max(ratios) if ratios else 0
    }


def _calculate_structure_change(
    period_orders: pd.DataFrame,
    period_days: int,
    max_date: pd.Timestamp
) -> Dict:
    """计算客单价结构分布变化"""
    
    # 生成日期序列
    date_range = pd.date_range(
        end=max_date,
        periods=period_days,
        freq='D'
    )
    
    dates_str = [d.strftime('%m-%d') for d in date_range]
    low_ratios = []    # <25元
    mid_ratios = []    # 25-50元
    high_ratios = []   # >50元
    
    for date in date_range:
        day_orders = period_orders[period_orders['日期'] == date]
        if len(day_orders) > 0:
            low = len(day_orders[day_orders['实收价格'] < 25]) / len(day_orders) * 100
            mid = len(day_orders[
                (day_orders['实收价格'] >= 25) & 
                (day_orders['实收价格'] < 50)
            ]) / len(day_orders) * 100
            high = len(day_orders[day_orders['实收价格'] >= 50]) / len(day_orders) * 100
            
            low_ratios.append(round(low, 1))
            mid_ratios.append(round(mid, 1))
            high_ratios.append(round(high, 1))
        else:
            low_ratios.append(0)
            mid_ratios.append(0)
            high_ratios.append(0)
    
    # 计算变化(最近7天 vs 之前7天)
    if len(low_ratios) >= 14:
        recent_low = np.mean(low_ratios[-7:])
        prev_low = np.mean(low_ratios[-14:-7])
        low_change = round(recent_low - prev_low, 1)
        
        recent_mid = np.mean(mid_ratios[-7:])
        prev_mid = np.mean(mid_ratios[-14:-7])
        mid_change = round(recent_mid - prev_mid, 1)
        
        recent_high = np.mean(high_ratios[-7:])
        prev_high = np.mean(high_ratios[-14:-7])
        high_change = round(recent_high - prev_high, 1)
    else:
        low_change = mid_change = high_change = 0
    
    return {
        'dates': dates_str,
        'low': low_ratios,      # <25元
        'mid': mid_ratios,      # 25-50元
        'high': high_ratios,    # >50元
        'current': {
            'low': low_ratios[-1] if low_ratios else 0,
            'mid': mid_ratios[-1] if mid_ratios else 0,
            'high': high_ratios[-1] if high_ratios else 0
        },
        'change': {
            'low': low_change,
            'mid': mid_change,
            'high': high_change
        }
    }


def _diagnose_product_issue(
    product_name: str,
    avg_price: float,
    order_count: int,
    order_ratio: float,
    df: pd.DataFrame,
    start_date: pd.Timestamp,
    max_date: pd.Timestamp
) -> Tuple[str, str, str]:
    """
    诊断商品问题，返回(标签, 原因, 建议)
    
    诊断逻辑（5种标签）:
    1. 🔥 促销引流品：销量暴增>50% + 价格<5元
    2. 📉 降价促销：价格降幅>10%
    3. 🚫 售罄缺货：销量暴跌>60% + 库存=0
    4. 📦 滞销风险：价格不变 + 销量下降>50%
    5. 💰 低价拖累：默认标签（兜底）
    
    注：已在数据层剔除耗材，此处不再判断
    """
    
    # 获取该商品的历史数据
    product_df = df[df['商品名称'] == product_name].copy()
    
    # 计算历史期和近期的销量变化
    mid_date = start_date + (max_date - start_date) / 2
    history_sales = product_df[product_df['日期'] < mid_date]['订单ID'].nunique()
    recent_sales = product_df[product_df['日期'] >= mid_date]['订单ID'].nunique()
    
    if history_sales > 0:
        sales_change_rate = ((recent_sales - history_sales) / history_sales * 100)
    else:
        sales_change_rate = 0
    
    # 判断1: 促销引流品（低价+销量暴增）
    if avg_price < 5 and sales_change_rate > 50:
        return '🔥 促销引流品', f'销量暴增{sales_change_rate:.0f}%，价格¥{avg_price:.2f}', '建议：检查是否亏损，考虑涨价或限购'
    
    # 判断2: 售罄缺货（销量暴跌+库存为0）
    if '库存' in product_df.columns or '剩余库存' in product_df.columns:
        stock_col = '库存' if '库存' in product_df.columns else '剩余库存'
        current_stock = product_df[stock_col].iloc[-1] if len(product_df) > 0 else 999
        if current_stock <= 0 and sales_change_rate < -60:
            return '🚫 售罄缺货', f'库存为0，销量暴跌{abs(sales_change_rate):.0f}%', '建议：及时补货，避免缺货影响销售'
    
    # 计算价格变化
    if '实收价格' in product_df.columns:
        history_price = product_df[product_df['日期'] < mid_date]['实收价格'].mean()
        recent_price = product_df[product_df['日期'] >= mid_date]['实收价格'].mean()
        
        if history_price > 0:
            price_change_rate = ((recent_price - history_price) / history_price * 100)
        else:
            price_change_rate = 0
        
        # 判断3: 降价促销/临期
        if price_change_rate < -10:
            return '📉 降价促销', f'价格下降{abs(price_change_rate):.1f}%（¥{history_price:.2f}→¥{recent_price:.2f}）', '建议：临期清仓或供应商促销，属正常波动'
    else:
        price_change_rate = 0
    
    # 判断4: 滞销风险（价格不变+销量暴跌）
    if abs(price_change_rate) < 5 and sales_change_rate < -50:
        return '📦 滞销风险', f'价格不变，销量暴跌{abs(sales_change_rate):.0f}%', '建议：考虑促销活动或优化商品详情页'
    
    # 判断5: 低价拖累（默认兜底）
    return '💰 低价拖累', f'价格¥{avg_price:.2f}低于整体均价，占比{order_ratio:.1f}%', '建议：优化商品组合，引导购买高价商品'


def _identify_drag_products(
    df: pd.DataFrame,
    order_agg: pd.DataFrame,
    start_date: pd.Timestamp,
    max_date: pd.Timestamp,
    price_field: str = '实收价格'
) -> Dict:
    """
    四层商品分析（重构版）
    
    返回结构:
    {
        'core_drag': [],      # 第一层：核心拖累TOP10
        'abnormal': [],       # 第二层：异常变化TOP10
        'new_low': [],        # 第三层：新增低价TOP5
        'high_price': {       # 第四层：高价带机会（价格>30元）
            'star': [],       # 高价爆品
            'stable': [],     # 高价稳定
            'decline': []     # 高价滞销
        },
        'summary': {}         # 汇总信息
    }
    """
    
    result = {
        'core_drag': [],
        'abnormal': [],
        'new_low': [],
        'high_price': {'star': [], 'stable': [], 'decline': []},
        'summary': {}
    }
    
    # 筛选周期内数据
    period_df = df[df['日期'] >= start_date].copy()
    period_orders = order_agg[order_agg['日期'] >= start_date].copy()
    
    if len(period_df) == 0:
        print(f"    ⚠️ 周期内无商品明细数据")
        return result
    
    # 计算平均客单价
    avg_aov = period_orders['实收价格'].mean()
    print(f"    📊 平均客单价: ¥{avg_aov:.2f}")
    
    # ✅ 剔除耗材分类
    if '一级分类名' in period_df.columns:
        before_count = len(period_df)
        period_df = period_df[period_df['一级分类名'] != '耗材'].copy()
        after_count = len(period_df)
        if before_count > after_count:
            print(f"    ✂️ 已剔除耗材分类: {before_count - after_count} 条记录")
    
    # 分为历史期和近期
    mid_date = start_date + (max_date - start_date) / 2
    history_df = period_df[period_df['日期'] < mid_date].copy()
    recent_df = period_df[period_df['日期'] >= mid_date].copy()
    
    # 统计每个商品在历史期和近期的数据
    history_stats = history_df.groupby('商品名称').agg({
        '订单ID': 'nunique',
        price_field: 'mean'
    }).reset_index()
    history_stats.columns = ['商品名称', '历史订单数', '历史价格']
    
    recent_stats = recent_df.groupby('商品名称').agg({
        '订单ID': 'nunique',
        price_field: 'mean'
    }).reset_index()
    recent_stats.columns = ['商品名称', '近期订单数', '近期价格']
    
    # 合并数据
    product_stats = recent_stats.merge(history_stats, on='商品名称', how='outer').fillna(0)
    
    # 计算总订单数和占比
    total_orders = len(period_orders)
    product_stats['订单总数'] = product_stats['历史订单数'] + product_stats['近期订单数']
    product_stats['订单占比'] = (product_stats['近期订单数'] / total_orders * 100).round(1)
    
    # 计算变化率
    product_stats['销量变化率'] = product_stats.apply(
        lambda r: ((r['近期订单数'] - r['历史订单数']) / r['历史订单数'] * 100) if r['历史订单数'] > 0 else 0,
        axis=1
    ).round(1)
    
    product_stats['价格变化率'] = product_stats.apply(
        lambda r: ((r['近期价格'] - r['历史价格']) / r['历史价格'] * 100) if r['历史价格'] > 0 else 0,
        axis=1
    ).round(1)
    
    # 使用近期价格作为商品价格
    product_stats['平均价格'] = product_stats['近期价格']
    
    # 计算拉低金额
    product_stats['拉低金额'] = (
        (avg_aov - product_stats['平均价格']) * 
        product_stats['近期订单数']
    ).round(2)
    
    print(f"    📦 分析商品数: {len(product_stats)}")
    
    # ============ 第一层：核心拖累TOP10 ============
    core_drag_df = product_stats[
        (product_stats['平均价格'] < avg_aov * 0.85) &
        (product_stats['拉低金额'] > 0)
    ].sort_values('拉低金额', ascending=False).head(10)
    
    for _, row in core_drag_df.iterrows():
        label, reason, suggestion = _diagnose_product_issue(
            row['商品名称'], row['平均价格'], int(row['近期订单数']),
            row['订单占比'], df, start_date, max_date
        )
        result['core_drag'].append({
            'product': row['商品名称'],
            'avg_price': round(row['平均价格'], 2),
            'order_count': int(row['近期订单数']),
            'order_ratio': row['订单占比'],
            'drag_amount': row['拉低金额'],
            'sales_change': row['销量变化率'],
            'diagnosis_label': label,
            'diagnosis_reason': reason,
            'suggestion': suggestion
        })
    
    print(f"    🔴 核心拖累: {len(result['core_drag'])} 个")
    
    # ============ 第二层：异常变化TOP10 ============
    abnormal_df = product_stats[
        (product_stats['历史订单数'] >= 5) &
        ((product_stats['销量变化率'] > 100) | (product_stats['销量变化率'] < -30)) &
        (product_stats['平均价格'] < avg_aov)
    ].copy()
    abnormal_df['变化幅度'] = abs(abnormal_df['销量变化率'])
    abnormal_df = abnormal_df.sort_values('变化幅度', ascending=False).head(10)
    
    for _, row in abnormal_df.iterrows():
        result['abnormal'].append({
            'product': row['商品名称'],
            'avg_price': round(row['平均价格'], 2),
            'history_orders': int(row['历史订单数']),
            'recent_orders': int(row['近期订单数']),
            'sales_change': row['销量变化率'],
            'price_change': row['价格变化率']
        })
    
    print(f"    🟡 异常变化: {len(result['abnormal'])} 个")
    
    # ============ 第三层：新增低价TOP5 ============
    new_low_df = product_stats[
        (product_stats['历史订单数'] == 0) &
        (product_stats['近期订单数'] >= 3) &
        (product_stats['平均价格'] < avg_aov * 0.7)
    ].sort_values('近期订单数', ascending=False).head(5)
    
    for _, row in new_low_df.iterrows():
        result['new_low'].append({
            'product': row['商品名称'],
            'avg_price': round(row['平均价格'], 2),
            'order_count': int(row['近期订单数']),
            'order_ratio': row['订单占比']
        })
    
    print(f"    🆕 新增低价: {len(result['new_low'])} 个")
    
    # ============ 第四层：高价带机会（价格>30元）============
    HIGH_PRICE_THRESHOLD = 30  # 用户指定：单价30元以上
    
    high_price_df = product_stats[
        (product_stats['平均价格'] > HIGH_PRICE_THRESHOLD) &
        (product_stats['近期订单数'] >= 3)
    ].copy()
    
    # 计算拉升潜力 = (商品价格 - 平均客单价) × 近期订单数
    high_price_df['拉升潜力'] = (
        (high_price_df['平均价格'] - avg_aov) * 
        high_price_df['近期订单数']
    ).round(2)
    
    # 分类
    star_df = high_price_df[high_price_df['销量变化率'] > 50].sort_values('拉升潜力', ascending=False).head(5)
    stable_df = high_price_df[
        (high_price_df['销量变化率'] >= -20) & 
        (high_price_df['销量变化率'] <= 50)
    ].sort_values('拉升潜力', ascending=False).head(8)
    decline_df = high_price_df[high_price_df['销量变化率'] < -20].sort_values('销量变化率', ascending=True).head(3)
    
    for _, row in star_df.iterrows():
        result['high_price']['star'].append({
            'product': row['商品名称'],
            'avg_price': round(row['平均价格'], 2),
            'history_orders': int(row['历史订单数']),
            'recent_orders': int(row['近期订单数']),
            'sales_change': row['销量变化率'],
            'lift_potential': row['拉升潜力']
        })
    
    for _, row in stable_df.iterrows():
        result['high_price']['stable'].append({
            'product': row['商品名称'],
            'avg_price': round(row['平均价格'], 2),
            'recent_orders': int(row['近期订单数']),
            'sales_change': row['销量变化率'],
            'lift_potential': row['拉升潜力']
        })
    
    for _, row in decline_df.iterrows():
        result['high_price']['decline'].append({
            'product': row['商品名称'],
            'avg_price': round(row['平均价格'], 2),
            'history_orders': int(row['历史订单数']),
            'recent_orders': int(row['近期订单数']),
            'sales_change': row['销量变化率']
        })
    
    print(f"    🚀 高价带: 爆品{len(result['high_price']['star'])} 稳定{len(result['high_price']['stable'])} 滞销{len(result['high_price']['decline'])}")
    
    # 汇总信息
    result['summary'] = {
        'avg_aov': round(avg_aov, 2),
        'high_price_threshold': HIGH_PRICE_THRESHOLD,
        'total_products': len(product_stats),
        'core_drag_count': len(result['core_drag']),
        'abnormal_count': len(result['abnormal']),
        'new_low_count': len(result['new_low']),
        'high_price_star_count': len(result['high_price']['star']),
        'high_price_stable_count': len(result['high_price']['stable']),
        'high_price_decline_count': len(result['high_price']['decline'])
    }
    
    return result


def _identify_opportunity_products(
    df: pd.DataFrame,
    order_agg: pd.DataFrame,
    start_date: pd.Timestamp,
    max_date: pd.Timestamp,
    price_field: str = '实收价格'
) -> List[Dict]:
    """识别TOP5机会商品(高价值但销量下降)
    
    Args:
        price_field: 价格字段名，默认'实收价格'（优先），备选'商品实售价'
    """
    
    # 分为两个周期
    mid_date = start_date + (max_date - start_date) / 2
    
    period1_df = df[(df['日期'] >= start_date) & (df['日期'] < mid_date)].copy()
    period2_df = df[df['日期'] >= mid_date].copy()
    
    if len(period1_df) == 0 or len(period2_df) == 0:
        return []
    
    # 计算每个商品在两个周期的销量
    sales1 = period1_df.groupby('商品名称')['订单ID'].nunique()
    sales2 = period2_df.groupby('商品名称')['订单ID'].nunique()
    
    # 计算平均价格（使用动态价格字段）
    avg_prices = df[df['日期'] >= start_date].groupby('商品名称')[price_field].mean()
    
    # 合并
    comparison = pd.DataFrame({
        '前期销量': sales1,
        '后期销量': sales2,
        '平均价格': avg_prices
    }).fillna(0)
    
    # 计算销量变化率
    comparison['销量变化率'] = (
        (comparison['后期销量'] - comparison['前期销量']) / 
        comparison['前期销量'].replace(0, np.nan) * 100
    ).fillna(0).round(1)
    
    # 筛选机会商品(价格>40元 且 销量下降>10%)
    opportunity_df = comparison[
        (comparison['平均价格'] > 40) & 
        (comparison['销量变化率'] < -10) &
        (comparison['前期销量'] >= 3)  # 前期至少有3单
    ].copy()
    
    # 按销量变化率排序(降幅最大的)
    opportunity_df = opportunity_df.sort_values('销量变化率').head(5)
    
    results = []
    for product, row in opportunity_df.iterrows():
        results.append({
            'product': product,
            'avg_price': round(row['平均价格'], 2),
            'sales_change': row['销量变化率'],
            'prev_sales': int(row['前期销量']),
            'current_sales': int(row['后期销量'])
        })
    
    return results



def _empty_distribution_result() -> Dict:
    """返回空的订单分布分析结果"""
    return {
        'severe': [],
        'moderate': [],
        'mild': [],
        'trend': {
            'dates': [],
            'severe_count': [],
            'moderate_count': [],
            'mild_count': [],
            'total_count': [],
            'distribution': []
        },
        'summary': {
            'total_downgrade': 0,
            'total_changes': 0,
            'severe_count': 0,
            'moderate_count': 0,
            'mild_count': 0,
            'avg_aov': 0,
            'history_avg_aov': 0,
            'aov_change_amount': 0,
            'aov_change_rate': 0,
            'avg_decline': 0,
            'max_decline': 0,
            'period_days': 30,
            'distribution': [],
            'suggestions': []
        }
    }


def _empty_customer_result() -> Dict:
    """返回空的客户分析结果"""
    return {
        'severe': [],
        'moderate': [],
        'mild': [],
        'trend': {
            'dates': [],
            'severe_count': [],
            'moderate_count': [],
            'mild_count': [],
            'total_count': []
        },
        'summary': {
            'total_downgrade': 0,
            'total_changes': 0,
            'severe_count': 0,
            'moderate_count': 0,
            'mild_count': 0,
            'avg_aov': 0,
            'aov_change_amount': 0,
            'history_avg_aov': 0,
            'avg_decline': 0,
            'max_decline': 0,
            'period_days': 30
        }
    }


def _empty_product_result() -> Dict:
    """返回空的商品分析结果"""
    return {
        'low_price_trend': {
            'dates': [],
            'ratios': [],
            'threshold': 25,
            'current_ratio': 0,
            'avg_ratio': 0,
            'peak_date': None,
            'peak_ratio': 0
        },
        'structure_change': {
            'dates': [],
            'low': [],
            'mid': [],
            'high': [],
            'current': {'low': 0, 'mid': 0, 'high': 0},
            'change': {'low': 0, 'mid': 0, 'high': 0}
        },
        'drag_products': [],
        'opportunity_products': [],
        'summary': {
            'period_days': 30,
            'total_orders': 0,
            'avg_aov': 0,
            'low_price_ratio': 0,
            'drag_product_count': 0
        }
    }
