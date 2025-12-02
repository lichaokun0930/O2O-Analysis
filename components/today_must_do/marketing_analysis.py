# -*- coding: utf-8 -*-
"""
今日必做 - 营销侧分析模块 (V2.0 完全重写)

严格按照「今日必做优化.md」设计文档实现:

核心判断标准:
  - 营销导致亏损订单:
    ├── 基础条件: 订单实际利润 < 0
    ├── 营销关联: 订单参与了满减/优惠券/商品减免等活动
    └── 分类标签: 标记该订单参与的所有活动类型

展示逻辑:
  - 活动类型分布（满减/商品减免/新客券等）
  - 活动叠加×高配送费交叉分析

⚠️ 时间基准: 数据最后一天 = "昨日"
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from typing import Dict, Tuple, Optional, Any, List

# 导入运力侧工具函数用于交叉分析
from .delivery_analysis import (
    SCENE_PERIODS, 
    get_hour_from_datetime, 
    get_scene_period, 
    prepare_order_data_with_distance
)

# 配送费阈值
DELIVERY_FEE_THRESHOLD = 6  # 元

# 活动类型字段映射
ACTIVITY_FIELDS = {
    '满减活动': '满减金额',
    '商品减免': '商品减免金额',
    '新客券': '新客减免金额',
    '商家代金券': '商家代金券',
    '商家承担券': '商家承担部分券',
    '满赠': '满赠金额',
    '其他优惠': '商家其他优惠'
}


def get_base_date(df: pd.DataFrame) -> Optional[pd.Timestamp]:
    """获取基准日期（昨日 = 数据最后一天）"""
    date_col = '日期' if '日期' in df.columns else '下单时间'
    if date_col not in df.columns:
        return None
    
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    return df[date_col].max().normalize()


def analyze_marketing_loss(
    order_agg: pd.DataFrame,
    yesterday_only: bool = True
) -> Dict[str, Any]:
    """
    营销导致亏损订单分析
    
    严格按照设计文档实现:
    - 基础条件: 订单实际利润 < 0
    - 营销关联: 参与了活动
    - 分类: 按活动类型统计
    
    Args:
        order_agg: 订单级聚合数据
        yesterday_only: 是否只分析昨日数据
    
    Returns:
        Dict: {
            'summary': {...},
            'by_activity_type': [...],
            'loss_orders': DataFrame,
            'error': str or None
        }
    """
    result = {
        'summary': {},
        'by_activity_type': [],
        'loss_orders': pd.DataFrame(),
        'error': None
    }
    
    try:
        if order_agg is None or len(order_agg) == 0:
            result['error'] = '无订单数据'
            return result
        
        df = order_agg.copy()
        
        # 获取利润字段
        profit_col = None
        for col in ['订单实际利润', '利润额']:
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
        
        # 计算商家活动成本
        df['商家活动成本'] = 0
        for activity_name, field_name in ACTIVITY_FIELDS.items():
            if field_name in df.columns:
                df['商家活动成本'] += df[field_name].fillna(0)
        
        # 标记参与活动的订单
        df['参与活动'] = df['商家活动成本'] > 0
        
        # 亏损订单：利润<0 且 参与了活动
        df['是否亏损'] = (df[profit_col] < 0) & df['参与活动']
        loss_orders = df[df['是否亏损']].copy()
        
        # 按活动类型统计
        by_activity_type = []
        for activity_name, field_name in ACTIVITY_FIELDS.items():
            if field_name in df.columns:
                # 参与该活动的亏损订单
                has_activity = df[field_name].fillna(0) > 0
                loss_with_activity = (df[profit_col] < 0) & has_activity
                
                if loss_with_activity.sum() > 0:
                    activity_loss_df = df[loss_with_activity]
                    by_activity_type.append({
                        '活动类型': activity_name,
                        '订单数': int(loss_with_activity.sum()),
                        '亏损金额': round(abs(activity_loss_df[profit_col].sum()), 2),
                        '单均亏损': round(abs(activity_loss_df[profit_col].mean()), 2)
                    })
        
        # 按亏损金额排序
        by_activity_type = sorted(by_activity_type, key=lambda x: x['亏损金额'], reverse=True)
        
        # 汇总统计
        total_orders = len(df)
        loss_count = len(loss_orders)
        
        result['summary'] = {
            'yesterday': get_base_date(order_agg).strftime('%Y-%m-%d') if get_base_date(order_agg) else None,
            'total_orders': total_orders,
            'loss_count': loss_count,
            'loss_rate': round(loss_count / total_orders * 100, 2) if total_orders > 0 else 0,
            'total_loss': round(abs(loss_orders[profit_col].sum()), 2) if len(loss_orders) > 0 else 0,
            'avg_loss': round(abs(loss_orders[profit_col].mean()), 2) if len(loss_orders) > 0 else 0,
            'activity_order_count': int(df['参与活动'].sum()),
            'activity_order_rate': round(df['参与活动'].mean() * 100, 2)
        }
        
        result['by_activity_type'] = by_activity_type
        result['loss_orders'] = loss_orders
        
        return result
        
    except Exception as e:
        result['error'] = f'分析营销亏损失败: {str(e)}'
        return result


def analyze_activity_overlap(
    order_agg: pd.DataFrame,
    raw_df: Optional[pd.DataFrame] = None,
    yesterday_only: bool = True
) -> Dict[str, Any]:
    """
    活动叠加×高配送费交叉分析
    
    严格按照设计文档实现:
    - 活动叠加(≥2个) + 配送费>6元 的订单
    - 分析平均亏损、时段分布、距离分布
    """
    result = {
        'summary': {},
        'overlap_orders': pd.DataFrame(),
        'by_period': {},
        'by_distance': {},
        'by_activity': {},
        'activity_combinations': [],
        'error': None
    }
    
    try:
        if order_agg is None or len(order_agg) == 0:
            result['error'] = '无订单数据'
            return result
        
        df = order_agg.copy()
        
        # 尝试添加配送距离信息
        df_with_dist, _ = prepare_order_data_with_distance(df, raw_df)
        if not df_with_dist.empty:
            df = df_with_dist
        
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
        
        # 统计每个订单参与的活动数量
        df['活动数量'] = 0
        df['活动类型列表'] = ''
        
        for activity_name, field_name in ACTIVITY_FIELDS.items():
            if field_name in df.columns:
                has_activity = df[field_name].fillna(0) > 0
                df.loc[has_activity, '活动数量'] += 1
                df.loc[has_activity, '活动类型列表'] += activity_name + '+'
        
        df['活动类型列表'] = df['活动类型列表'].str.rstrip('+')
        
        # 获取利润字段
        profit_col = None
        for col in ['订单实际利润', '利润额']:
            if col in df.columns:
                profit_col = col
                break
        
        # 条件：活动叠加(≥2个) + 配送费>6元
        overlap_condition = (df['活动数量'] >= 2) & (df['物流配送费'] > DELIVERY_FEE_THRESHOLD)
        overlap_orders = df[overlap_condition].copy()
        
        if len(overlap_orders) == 0:
            result['summary'] = {
                'overlap_count': 0,
                'message': '未发现活动叠加+高配送费的订单'
            }
            return result
        
        # 计算亏损
        if profit_col:
            avg_loss = abs(overlap_orders[profit_col].mean()) if (overlap_orders[profit_col] < 0).any() else 0
            # 与普通亏损单对比
            all_loss = df[(df[profit_col] < 0) & df['参与活动'] if '参与活动' in df.columns else (df[profit_col] < 0)]
            normal_avg_loss = abs(all_loss[profit_col].mean()) if len(all_loss) > 0 else 0
            loss_ratio = round(avg_loss / normal_avg_loss, 1) if normal_avg_loss > 0 else 1.0
        else:
            avg_loss = 0
            loss_ratio = 0
        
        # 汇总
        result['summary'] = {
            'overlap_count': len(overlap_orders),
            'avg_loss': round(avg_loss, 2),
            'loss_ratio': loss_ratio,
            'avg_activity_count': round(overlap_orders['活动数量'].mean(), 1),
            'avg_delivery_fee': round(overlap_orders['物流配送费'].mean(), 2)
        }
        
        # 1. 时段分布
        dt_col = '下单时间' if '下单时间' in overlap_orders.columns else '日期'
        if dt_col in overlap_orders.columns:
            overlap_orders['hour'] = overlap_orders[dt_col].apply(get_hour_from_datetime)
            overlap_orders['period'] = overlap_orders['hour'].apply(get_scene_period)
            top_period = overlap_orders['period'].value_counts().head(1)
            if not top_period.empty:
                result['by_period'] = {
                    'name': top_period.index[0],
                    'count': int(top_period.values[0]),
                    'rate': int(top_period.values[0] / len(overlap_orders) * 100)
                }
                
        # 2. 距离分布
        if '配送距离' in overlap_orders.columns:
            bins = [0, 3, 5, float('inf')]
            labels = ['0-3km', '3-5km', '5km+']
            overlap_orders['dist_range'] = pd.cut(overlap_orders['配送距离'], bins=bins, labels=labels)
            top_dist = overlap_orders['dist_range'].value_counts().head(1)
            if not top_dist.empty:
                result['by_distance'] = {
                    'name': top_dist.index[0],
                    'count': int(top_dist.values[0]),
                    'rate': int(top_dist.values[0] / len(overlap_orders) * 100)
                }
                
        # 3. 活动组合分布
        top_combo = overlap_orders['活动类型列表'].value_counts().head(1)
        if not top_combo.empty:
            result['by_activity'] = {
                'name': top_combo.index[0],
                'count': int(top_combo.values[0]),
                'rate': int(top_combo.values[0] / len(overlap_orders) * 100)
            }
        
        # 活动组合统计
        combo_counts = overlap_orders['活动类型列表'].value_counts().head(10)
        result['activity_combinations'] = [
            {'组合': combo, '订单数': int(count)}
            for combo, count in combo_counts.items()
        ]
        
        result['overlap_orders'] = overlap_orders
        
        return result
        
    except Exception as e:
        result['error'] = f'分析活动叠加失败: {str(e)}'
        return result


def create_marketing_delivery_matrix(
    order_agg: pd.DataFrame,
    yesterday_only: bool = True
) -> Tuple[Dict[str, Dict], Dict[str, Any]]:
    """
    创建活动叠加×高配送费交叉分析矩阵
    
    四象限:
        - 正常订单: 活动优惠 ≤ 毛利 且 配送费 ≤ 6元
        - 配送压力: 活动优惠 ≤ 毛利 且 配送费 > 6元
        - 营销穿底: 活动优惠 > 毛利 且 配送费 ≤ 6元
        - 双重亏损: 活动优惠 > 毛利 且 配送费 > 6元
    """
    try:
        if order_agg is None or len(order_agg) == 0:
            return {}, {'error': '无订单数据'}
        
        df = order_agg.copy()
        
        # 筛选昨日数据
        if yesterday_only:
            date_col = '日期' if '日期' in df.columns else '下单时间'
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col])
                yesterday = df[date_col].max().normalize()
                df = df[df[date_col].dt.normalize() == yesterday]
        
        if len(df) == 0:
            return {}, {'error': '昨日无订单数据'}
        
        # 计算商品毛利
        df['商品毛利'] = (
            df['利润额'] + 
            df['物流配送费'] + 
            df.get('平台服务费', 0)
        )
        
        # 计算商家活动成本
        df['活动优惠'] = 0
        for activity_name, field_name in ACTIVITY_FIELDS.items():
            if field_name in df.columns:
                df['活动优惠'] += df[field_name].fillna(0)
        
        # 分类标记
        df['营销穿底'] = df['活动优惠'] > df['商品毛利']
        df['高配送费'] = df['物流配送费'] > DELIVERY_FEE_THRESHOLD
        
        # 四象限分类
        normal = (~df['营销穿底']) & (~df['高配送费'])
        delivery_pressure = (~df['营销穿底']) & (df['高配送费'])
        marketing_overflow = (df['营销穿底']) & (~df['高配送费'])
        double_loss = (df['营销穿底']) & (df['高配送费'])
        
        total = len(df)
        
        matrix = {
            'normal': {
                'name': '✅ 正常订单',
                'count': int(normal.sum()),
                'rate': round(normal.sum() / total * 100, 2) if total > 0 else 0,
                'description': '活动优惠≤毛利 且 配送费≤6元'
            },
            'delivery_pressure': {
                'name': '⚠️ 配送压力',
                'count': int(delivery_pressure.sum()),
                'rate': round(delivery_pressure.sum() / total * 100, 2) if total > 0 else 0,
                'description': '活动优惠≤毛利 但 配送费>6元'
            },
            'marketing_overflow': {
                'name': '⚠️ 营销穿底',
                'count': int(marketing_overflow.sum()),
                'rate': round(marketing_overflow.sum() / total * 100, 2) if total > 0 else 0,
                'description': '活动优惠>毛利 但 配送费≤6元'
            },
            'double_loss': {
                'name': '🔴 双重亏损',
                'count': int(double_loss.sum()),
                'rate': round(double_loss.sum() / total * 100, 2) if total > 0 else 0,
                'description': '活动优惠>毛利 且 配送费>6元'
            }
        }
        
        summary = {
            'yesterday': get_base_date(order_agg).strftime('%Y-%m-%d') if get_base_date(order_agg) else None,
            'total_orders': total,
            'problem_orders': int(marketing_overflow.sum() + double_loss.sum()),
            'problem_rate': round((marketing_overflow.sum() + double_loss.sum()) / total * 100, 2) if total > 0 else 0,
            'error': None
        }
        
        return matrix, summary
        
    except Exception as e:
        return {}, {'error': f'创建交叉分析失败: {str(e)}'}


def get_discount_analysis_by_range(order_agg: pd.DataFrame) -> Dict[str, Any]:
    """按满减金额区间分析穿底情况"""
    try:
        if order_agg is None or len(order_agg) == 0:
            return {'error': '无订单数据'}
        
        if '满减金额' not in order_agg.columns:
            return {'error': '缺少满减金额字段'}
        
        df = order_agg[order_agg['满减金额'] > 0].copy()
        
        if len(df) == 0:
            return {'error': '无满减订单'}
        
        # 计算商品毛利
        df['商品毛利'] = (
            df['利润额'] + 
            df['物流配送费'] + 
            df.get('平台服务费', 0)
        )
        
        df['穿底'] = df['满减金额'] > df['商品毛利']
        
        bins = [0, 5, 10, 15, 20, 30, float('inf')]
        labels = ['0-5元', '5-10元', '10-15元', '15-20元', '20-30元', '30元+']
        df['满减区间'] = pd.cut(df['满减金额'], bins=bins, labels=labels, include_lowest=True)
        
        result = {}
        for label in labels:
            segment = df[df['满减区间'] == label]
            if len(segment) > 0:
                result[label] = {
                    'count': len(segment),
                    'overflow_count': int(segment['穿底'].sum()),
                    'overflow_rate': round(segment['穿底'].mean() * 100, 2),
                    'avg_discount': round(segment['满减金额'].mean(), 2),
                    'avg_margin': round(segment['商品毛利'].mean(), 2)
                }
            else:
                result[label] = {'count': 0, 'overflow_count': 0, 'overflow_rate': 0, 'avg_discount': 0, 'avg_margin': 0}
        
        return result
        
    except Exception as e:
        return {'error': str(e)}


# ============== 兼容旧API ==============

def identify_discount_overflow_orders(order_agg: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """兼容旧API的包装函数"""
    result = analyze_marketing_loss(order_agg, yesterday_only=False)
    summary = result['summary'].copy() if result['summary'] else {}
    summary['error'] = result['error']
    return result['loss_orders'], summary
