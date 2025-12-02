# -*- coding: utf-8 -*-
"""
今日必做 - 运力侧分析模块 (V2.0 完全重写)

严格按照「今日必做优化.md」设计文档实现:

核心判断标准:
  - 异常订单定义:
    ├── 基础条件: 单均配送费 > 6元
    └── 排除条件: 订单毛利 > 单均配送费 (能背回成本的不算异常)
  - 最终异常订单 = 单均配送费 > 6元 AND 订单毛利 < 单均配送费

展示逻辑:
  - 热力图: 距离×时段交叉分析
  - 异常高发区标记: 占比>15%

⚠️ 时间基准: 数据最后一天 = "昨日"
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from typing import Dict, Tuple, Optional, Any


# 距离分段定义
DISTANCE_BINS = [0, 2, 3, 4, 5, 6, 8, float('inf')]
DISTANCE_LABELS = ['0-2km', '2-3km', '3-4km', '4-5km', '5-6km', '6-8km', '8km+']

# 场景时段定义（按设计文档）
SCENE_PERIODS = {
    '早餐': (6, 9),     # 06:00-08:59
    '午餐': (11, 14),   # 11:00-13:59
    '下午茶': (14, 17), # 14:00-16:59
    '晚餐': (17, 21),   # 17:00-20:59
    '夜宵': (21, 24),   # 21:00-23:59
}
SCENE_ORDER = ['早餐', '午餐', '下午茶', '晚餐', '夜宵']

# 配送费阈值
DELIVERY_FEE_THRESHOLD = 6  # 元


def get_hour_from_datetime(dt) -> int:
    """从datetime提取小时"""
    if pd.isna(dt):
        return -1
    try:
        return pd.to_datetime(dt).hour
    except:
        return -1


def get_scene_period(hour: int) -> str:
    """根据小时获取场景时段"""
    if hour < 0:
        return '未知'
    
    for scene, (start, end) in SCENE_PERIODS.items():
        if start < end:
            if start <= hour < end:
                return scene
        else:  # 跨天情况（夜宵: 21-6）
            if hour >= start or hour < end:
                return scene
    
    return '其他'


def get_base_date(df: pd.DataFrame) -> Optional[pd.Timestamp]:
    """获取基准日期（昨日 = 数据最后一天）"""
    date_col = '日期' if '日期' in df.columns else '下单时间'
    if date_col not in df.columns:
        return None
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    return df[date_col].max().normalize()


def prepare_order_data_with_distance(
    order_agg: pd.DataFrame,
    raw_df: Optional[pd.DataFrame] = None
) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    准备包含配送距离的订单数据
    
    问题: calculate_order_metrics 默认不聚合配送距离
    解决: 从原始数据手动添加配送距离
    
    Args:
        order_agg: 订单级聚合数据
        raw_df: 原始商品级数据（可选，用于获取配送距离）
    
    Returns:
        (prepared_df, error_msg)
    """
    if order_agg is None or len(order_agg) == 0:
        return pd.DataFrame(), '无订单数据'
    
    df = order_agg.copy()
    
    # 检查是否已有配送距离
    distance_col = None
    for col in ['配送距离', '送达距离', 'distance', 'delivery_distance']:
        if col in df.columns:
            distance_col = col
            break
    
    # 如果没有配送距离，尝试从原始数据获取
    if distance_col is None and raw_df is not None:
        for col in ['配送距离', '送达距离', 'distance', 'delivery_distance']:
            if col in raw_df.columns:
                # 从原始数据聚合配送距离（按订单ID取first）
                distance_map = raw_df.groupby('订单ID')[col].first()
                df['配送距离'] = df['订单ID'].map(distance_map)
                distance_col = '配送距离'
                break
    
    if distance_col is None:
        return df, '缺少配送距离字段'
    
    # 统一字段名
    if distance_col != '配送距离':
        df['配送距离'] = df[distance_col]
    
    # 数值转换
    df['配送距离'] = pd.to_numeric(df['配送距离'], errors='coerce').fillna(0)
    
    # 检查单位（如果值很大，可能是米，需要转换为公里）
    if df['配送距离'].mean() > 100:
        df['配送距离'] = df['配送距离'] / 1000
    
    return df, None


def analyze_delivery_issues(
    order_agg: pd.DataFrame,
    raw_df: Optional[pd.DataFrame] = None,
    yesterday_only: bool = True
) -> Dict[str, Any]:
    """
    配送成本异常分析
    
    严格按照设计文档实现:
    - 异常定义: 配送费>6元 且 订单毛利<配送费
    - 统计: 异常订单数、占比、累计损失
    
    Args:
        order_agg: 订单级聚合数据
        raw_df: 原始商品级数据（用于获取配送距离）
        yesterday_only: 是否只分析昨日数据
    
    Returns:
        Dict: {
            'summary': {...},
            'problem_orders': DataFrame,
            'by_distance': {...},
            'by_period': {...},
            'error': str or None
        }
    """
    result = {
        'summary': {},
        'problem_orders': pd.DataFrame(),
        'by_distance': {},
        'by_period': {},
        'error': None
    }
    
    try:
        if order_agg is None or len(order_agg) == 0:
            result['error'] = '无订单数据'
            return result
        
        # 准备数据
        df, error = prepare_order_data_with_distance(order_agg, raw_df)
        if len(df) == 0:
            result['error'] = error or '数据准备失败'
            return result
        
        # 检查必要字段
        required_fields = ['物流配送费']
        missing = [f for f in required_fields if f not in df.columns]
        if missing:
            result['error'] = f'缺少必要字段: {missing}'
            return result
        
        # 获取利润字段
        profit_col = None
        for col in ['订单实际利润', '利润额', 'profit']:
            if col in df.columns:
                profit_col = col
                break
        
        if profit_col is None:
            result['error'] = '缺少利润字段'
            return result
        
        # 筛选昨日数据
        if yesterday_only:
            date_col = '日期' if '日期' in df.columns else '下单时间'
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col])
                yesterday = df[date_col].max().normalize()
                df = df[df[date_col].dt.normalize() == yesterday]
        
        if len(df) == 0:
            result['error'] = '昨日无订单数据'
            return result
        
        # 标记异常订单
        # 条件1: 配送费超阈值
        high_delivery = df['物流配送费'] > DELIVERY_FEE_THRESHOLD
        
        # 条件2: 利润无法覆盖配送费
        unprofitable = df[profit_col] < df['物流配送费']
        
        # 异常订单
        df['是否异常'] = high_delivery & unprofitable
        problem_orders = df[df['是否异常']].copy()
        
        if len(problem_orders) > 0:
            problem_orders['配送亏损'] = problem_orders['物流配送费'] - problem_orders[profit_col]
        
        # 汇总统计
        total_orders = len(df)
        problem_count = len(problem_orders)
        
        result['summary'] = {
            'yesterday': get_base_date(order_agg).strftime('%Y-%m-%d') if get_base_date(order_agg) else None,
            'total_orders': total_orders,
            'problem_count': problem_count,
            'problem_rate': round(problem_count / total_orders * 100, 2) if total_orders > 0 else 0,
            'total_loss': round(problem_orders['配送亏损'].sum(), 2) if len(problem_orders) > 0 else 0,
            'avg_loss': round(problem_orders['配送亏损'].mean(), 2) if len(problem_orders) > 0 else 0,
            'high_delivery_count': int(high_delivery.sum()),
        }
        
        result['problem_orders'] = problem_orders
        
        # 按距离分段统计
        if '配送距离' in df.columns and df['配送距离'].sum() > 0:
            df['距离分段'] = pd.cut(
                df['配送距离'], 
                bins=DISTANCE_BINS, 
                labels=DISTANCE_LABELS,
                include_lowest=True
            )
            
            by_distance = {}
            for label in DISTANCE_LABELS:
                segment = df[df['距离分段'] == label]
                if len(segment) > 0:
                    by_distance[label] = {
                        'order_count': len(segment),
                        'problem_count': int(segment['是否异常'].sum()),
                        'problem_rate': round(segment['是否异常'].mean() * 100, 2),
                        'avg_fee': round(segment['物流配送费'].mean(), 2)
                    }
            result['by_distance'] = by_distance
        
        # 按时段统计
        time_col = '日期' if '日期' in df.columns else '下单时间'
        if time_col in df.columns:
            df['小时'] = df[time_col].apply(get_hour_from_datetime)
            df['时段'] = df['小时'].apply(get_scene_period)
            
            by_period = {}
            for scene in SCENE_ORDER:
                segment = df[df['时段'] == scene]
                if len(segment) > 0:
                    by_period[scene] = {
                        'order_count': len(segment),
                        'problem_count': int(segment['是否异常'].sum()),
                        'problem_rate': round(segment['是否异常'].mean() * 100, 2),
                        'avg_fee': round(segment['物流配送费'].mean(), 2)
                    }
            result['by_period'] = by_period
        
        return result
        
    except Exception as e:
        result['error'] = f'分析配送异常失败: {str(e)}'
        return result


def create_delivery_heatmap_data(
    order_agg: pd.DataFrame, 
    raw_df: Optional[pd.DataFrame] = None,
    time_dimension: str = 'scene',
    show_problem_only: bool = False
) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """
    创建距离×时段交叉分析热力图数据
    
    严格按照设计文档实现:
    - 行: 距离分段 (0-2km, 2-3km, ...)
    - 列: 时段 (早餐, 午餐, ...)
    - 值: 异常订单数 或 单均配送费
    
    Returns:
        (heatmap_df, summary)
        heatmap_df: pivot table格式
    """
    try:
        if order_agg is None or len(order_agg) == 0:
            return None, {'error': '无订单数据'}
        
        # 准备数据
        df, error = prepare_order_data_with_distance(order_agg, raw_df)
        if '配送距离' not in df.columns or df['配送距离'].sum() == 0:
            return None, {'error': error or '缺少配送距离数据'}
        
        # 获取利润字段
        profit_col = None
        for col in ['订单实际利润', '利润额', 'profit']:
            if col in df.columns:
                profit_col = col
                break
        
        # 距离分段
        df['距离分段'] = pd.cut(
            df['配送距离'], 
            bins=DISTANCE_BINS, 
            labels=DISTANCE_LABELS,
            include_lowest=True
        )
        
        # 时段处理
        time_col = '日期' if '日期' in df.columns else '下单时间'
        if time_col in df.columns:
            df['小时'] = df[time_col].apply(get_hour_from_datetime)
            df['时段'] = df['小时'].apply(get_scene_period)
        else:
            return None, {'error': '缺少时间字段'}
        
        # 标记异常订单
        if profit_col and '物流配送费' in df.columns:
            df['是否异常'] = (df['物流配送费'] > DELIVERY_FEE_THRESHOLD) & (df[profit_col] < df['物流配送费'])
        else:
            df['是否异常'] = df['物流配送费'] > DELIVERY_FEE_THRESHOLD
        
        # 过滤无效数据
        df = df[(df['距离分段'].notna()) & (df['时段'].isin(SCENE_ORDER))]
        
        if len(df) == 0:
            return None, {'error': '过滤后无有效数据'}
        
        # 创建透视表
        if show_problem_only:
            # 异常订单数热力图
            heatmap_data = df.pivot_table(
                values='是否异常',
                index='距离分段',
                columns='时段',
                aggfunc='sum'
            ).fillna(0).astype(int)
        else:
            # 单均配送费热力图
            heatmap_data = df.pivot_table(
                values='物流配送费',
                index='距离分段',
                columns='时段',
                aggfunc='mean'
            ).round(2)
        
        # 确保列顺序
        existing_cols = [c for c in SCENE_ORDER if c in heatmap_data.columns]
        heatmap_data = heatmap_data[existing_cols]
        
        # 确保行顺序
        heatmap_data = heatmap_data.reindex([l for l in DISTANCE_LABELS if l in heatmap_data.index])
        
        # 订单数统计
        order_count_data = df.pivot_table(
            values='订单ID' if '订单ID' in df.columns else '物流配送费',
            index='距离分段',
            columns='时段',
            aggfunc='count'
        ).fillna(0).astype(int)
        
        # 计算异常集中区域（占比>15%）
        problem_count = df.pivot_table(
            values='是否异常',
            index='距离分段',
            columns='时段',
            aggfunc='sum'
        ).fillna(0)
        
        problem_rate = (problem_count / order_count_data * 100).fillna(0)
        hot_zones = []
        for dist in problem_rate.index:
            for period in problem_rate.columns:
                if problem_rate.loc[dist, period] > 15:
                    hot_zones.append({
                        '距离': dist,
                        '时段': period,
                        '异常占比': round(problem_rate.loc[dist, period], 1),
                        '异常订单': int(problem_count.loc[dist, period])
                    })
        
        summary = {
            'total_orders': len(df),
            'problem_orders': int(df['是否异常'].sum()),
            'problem_rate': round(df['是否异常'].mean() * 100, 2),
            'avg_delivery_fee': round(df['物流配送费'].mean(), 2),
            'hot_zones': hot_zones,
            'order_counts': order_count_data.to_dict(),
            'error': None
        }
        
        return heatmap_data, summary
        
    except Exception as e:
        return None, {'error': f'创建热力图数据失败: {str(e)}'}


def get_delivery_summary_by_distance(
    order_agg: pd.DataFrame,
    raw_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """按距离分段汇总配送数据"""
    try:
        df, error = prepare_order_data_with_distance(order_agg, raw_df)
        if '配送距离' not in df.columns:
            return {'error': error or '缺少配送距离字段'}
        
        profit_col = None
        for col in ['订单实际利润', '利润额']:
            if col in df.columns:
                profit_col = col
                break
        
        df['距离分段'] = pd.cut(
            df['配送距离'], 
            bins=DISTANCE_BINS, 
            labels=DISTANCE_LABELS,
            include_lowest=True
        )
        
        if profit_col and '物流配送费' in df.columns:
            df['是否问题订单'] = (df['物流配送费'] > DELIVERY_FEE_THRESHOLD) & (df[profit_col] < df['物流配送费'])
        else:
            df['是否问题订单'] = df['物流配送费'] > DELIVERY_FEE_THRESHOLD
        
        result = {}
        for label in DISTANCE_LABELS:
            segment_df = df[df['距离分段'] == label]
            if len(segment_df) > 0:
                result[label] = {
                    'order_count': len(segment_df),
                    'avg_fee': round(segment_df['物流配送费'].mean(), 2),
                    'max_fee': round(segment_df['物流配送费'].max(), 2),
                    'problem_count': int(segment_df['是否问题订单'].sum()),
                    'problem_rate': round(segment_df['是否问题订单'].mean() * 100, 2)
                }
            else:
                result[label] = {'order_count': 0, 'avg_fee': 0, 'max_fee': 0, 'problem_count': 0, 'problem_rate': 0}
        
        return result
        
    except Exception as e:
        return {'error': str(e)}


# ============== 兼容旧API ==============

def identify_delivery_issues(order_agg: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """兼容旧API的包装函数"""
    result = analyze_delivery_issues(order_agg, yesterday_only=False)
    return result['problem_orders'], result['summary']
