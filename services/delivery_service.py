# -*- coding: utf-8 -*-
"""
配送分析服务

提供配送相关的分析功能：
- 配送成本异常分析
- 距离×时段热力图
- 配送距离分析
- 异常高发区标记

业务逻辑来源: components/today_must_do/delivery_analysis.py

核心判断标准:
  - 异常订单定义:
    ├── 基础条件: 单均配送费 > 6元
    └── 排除条件: 订单毛利 > 单均配送费 (能背回成本的不算异常)
  - 最终异常订单 = 单均配送费 > 6元 AND 订单毛利 < 单均配送费

版本: v1.0
创建日期: 2026-01-05
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta

from .base_service import BaseService
from .cache.cache_keys import CacheKeys


# 距离分段定义
DISTANCE_BINS = [0, 2, 3, 4, 5, 6, 8, float('inf')]
DISTANCE_LABELS = ['0-2km', '2-3km', '3-4km', '4-5km', '5-6km', '6-8km', '8km+']

# 场景时段定义
SCENE_PERIODS = {
    '早餐': (6, 9),     # 06:00-08:59
    '午餐': (11, 14),   # 11:00-13:59
    '下午茶': (14, 17), # 14:00-16:59
    '晚餐': (17, 21),   # 17:00-20:59
    '夜宵': (21, 24),   # 21:00-23:59
}
SCENE_ORDER = ['早餐', '午餐', '下午茶', '晚餐', '夜宵']

# 配送费阈值
DELIVERY_FEE_THRESHOLD = 6.0


class DeliveryService(BaseService):
    """
    配送分析服务
    
    提供配送数据分析功能
    """
    
    def __init__(self, data_loader=None, cache_manager=None):
        super().__init__(cache_manager)
        self.data_loader = data_loader
        self.delivery_fee_threshold = DELIVERY_FEE_THRESHOLD
    
    # ==================== 工具方法 ====================
    
    @staticmethod
    def get_hour_from_datetime(dt) -> int:
        """从datetime提取小时"""
        if pd.isna(dt):
            return -1
        try:
            return pd.to_datetime(dt).hour
        except:
            return -1
    
    @staticmethod
    def get_scene_period(hour: int) -> str:
        """根据小时获取场景时段"""
        if hour < 0:
            return '未知'
        
        for scene, (start, end) in SCENE_PERIODS.items():
            if start < end:
                if start <= hour < end:
                    return scene
            else:  # 跨天情况
                if hour >= start or hour < end:
                    return scene
        
        return '其他'
    
    def prepare_order_data_with_distance(
        self,
        order_agg: pd.DataFrame,
        raw_df: Optional[pd.DataFrame] = None
    ) -> Tuple[pd.DataFrame, Optional[str]]:
        """
        准备包含配送距离的订单数据
        
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
        if distance_col is None and raw_df is not None and '订单ID' in raw_df.columns:
            for col in ['配送距离', '送达距离', 'distance', 'delivery_distance']:
                if col in raw_df.columns:
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
    
    # ==================== 配送异常分析 ====================
    
    def analyze_delivery_issues(
        self,
        df: pd.DataFrame,
        raw_df: Optional[pd.DataFrame] = None,
        store_name: Optional[str] = None,
        yesterday_only: bool = True
    ) -> Dict[str, Any]:
        """
        配送成本异常分析
        
        定义: 配送费>6元 且 订单毛利<配送费
        
        Args:
            df: 订单数据DataFrame（订单级聚合后）
            raw_df: 原始商品级数据（可选）
            store_name: 门店筛选
            yesterday_only: 是否只分析昨日数据
        
        Returns:
            配送异常分析数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无订单数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 聚合到订单级
            if '订单ID' in data.columns and len(data) > data['订单ID'].nunique():
                data = self.aggregate_to_order_level(data)
            
            # 日期筛选
            if yesterday_only:
                date_col = self.get_date_column(data)
                if date_col:
                    data[date_col] = pd.to_datetime(data[date_col])
                    yesterday = data[date_col].max().normalize()
                    data = data[data[date_col].dt.normalize() == yesterday]
            
            if data.empty:
                return {'error': '昨日无订单数据'}
            
            # 检查配送费字段
            if '物流配送费' not in data.columns:
                return {'error': '缺少配送费字段'}
            
            # 获取利润字段
            profit_col = '订单实际利润' if '订单实际利润' in data.columns else '利润额'
            if profit_col not in data.columns:
                return {'error': '缺少利润字段'}
            
            # 异常定义：配送费>阈值 且 利润<配送费
            data['配送费异常'] = (
                (data['物流配送费'] > self.delivery_fee_threshold) &
                (data[profit_col] < data['物流配送费'])
            )
            
            abnormal_orders = data[data['配送费异常']].copy()
            
            # 准备配送距离数据
            abnormal_with_distance, _ = self.prepare_order_data_with_distance(abnormal_orders, raw_df)
            
            # 按配送费排序
            abnormal_with_distance = abnormal_with_distance.sort_values('物流配送费', ascending=False)
            
            # 距离分布分析
            distance_dist = {}
            if '配送距离' in abnormal_with_distance.columns:
                abnormal_with_distance['距离分段'] = pd.cut(
                    abnormal_with_distance['配送距离'],
                    bins=DISTANCE_BINS,
                    labels=DISTANCE_LABELS,
                    include_lowest=True
                )
                distance_dist = abnormal_with_distance['距离分段'].value_counts().to_dict()
                distance_dist = {str(k): int(v) for k, v in distance_dist.items()}
            
            return {
                'success': True,
                'data': self.clean_for_json(abnormal_with_distance.head(100).to_dict('records')),
                'summary': {
                    'total_orders': len(data),
                    'abnormal_count': len(abnormal_orders),
                    'abnormal_rate': round(len(abnormal_orders) / len(data) * 100, 1) if len(data) > 0 else 0,
                    'total_delivery_fee': round(float(abnormal_orders['物流配送费'].sum()), 2),
                    'avg_delivery_fee': round(float(abnormal_orders['物流配送费'].mean()), 2) if len(abnormal_orders) > 0 else 0,
                    'threshold': self.delivery_fee_threshold,
                    'distance_distribution': distance_dist
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "配送异常分析失败")
    
    # ==================== 热力图分析 ====================
    
    def get_delivery_heatmap(
        self,
        df: pd.DataFrame,
        raw_df: Optional[pd.DataFrame] = None,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成距离×时段热力图数据
        
        Args:
            df: 订单数据DataFrame
            raw_df: 原始商品级数据（可选）
            store_name: 门店筛选
        
        Returns:
            热力图数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无订单数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 聚合到订单级
            if '订单ID' in data.columns and len(data) > data['订单ID'].nunique():
                data = self.aggregate_to_order_level(data)
            
            # 准备配送距离数据
            data, error = self.prepare_order_data_with_distance(data, raw_df)
            if '配送距离' not in data.columns:
                return {'error': error or '缺少配送距离'}
            
            # 获取时段
            date_col = self.get_date_column(data)
            if date_col:
                data['小时'] = data[date_col].apply(self.get_hour_from_datetime)
                data['时段'] = data['小时'].apply(self.get_scene_period)
            else:
                return {'error': '缺少时间字段'}
            
            # 距离分段
            data['距离分段'] = pd.cut(
                data['配送距离'],
                bins=DISTANCE_BINS,
                labels=DISTANCE_LABELS,
                include_lowest=True
            )
            
            # 获取利润字段
            profit_col = '订单实际利润' if '订单实际利润' in data.columns else '利润额'
            
            # 标记异常订单
            if '物流配送费' in data.columns and profit_col in data.columns:
                data['配送费异常'] = (
                    (data['物流配送费'] > self.delivery_fee_threshold) &
                    (data[profit_col] < data['物流配送费'])
                )
            else:
                data['配送费异常'] = False
            
            # 构建热力图数据
            heatmap_data = []
            
            for distance_label in DISTANCE_LABELS:
                for scene in SCENE_ORDER:
                    mask = (data['距离分段'] == distance_label) & (data['时段'] == scene)
                    total_count = mask.sum()
                    abnormal_count = (mask & data['配送费异常']).sum()
                    abnormal_rate = abnormal_count / total_count * 100 if total_count > 0 else 0
                    
                    heatmap_data.append({
                        '距离': distance_label,
                        '时段': scene,
                        '订单数': int(total_count),
                        '异常数': int(abnormal_count),
                        '异常率': round(abnormal_rate, 1),
                        '是否高发区': abnormal_rate > 15  # 占比>15%标记为高发区
                    })
            
            return {
                'success': True,
                'data': heatmap_data,
                'config': {
                    'distance_labels': DISTANCE_LABELS,
                    'scene_order': SCENE_ORDER,
                    'threshold': 15  # 高发区阈值
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "生成热力图失败")
    
    # ==================== 距离分析 ====================
    
    def analyze_by_distance(
        self,
        df: pd.DataFrame,
        raw_df: Optional[pd.DataFrame] = None,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        按配送距离分析
        
        Args:
            df: 订单数据DataFrame
            raw_df: 原始商品级数据（可选）
            store_name: 门店筛选
        
        Returns:
            距离分析数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无订单数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 聚合到订单级
            if '订单ID' in data.columns and len(data) > data['订单ID'].nunique():
                data = self.aggregate_to_order_level(data)
            
            # 准备配送距离数据
            data, error = self.prepare_order_data_with_distance(data, raw_df)
            if '配送距离' not in data.columns:
                return {'error': error or '缺少配送距离'}
            
            # 距离分段
            data['距离分段'] = pd.cut(
                data['配送距离'],
                bins=DISTANCE_BINS,
                labels=DISTANCE_LABELS,
                include_lowest=True
            )
            
            # 获取利润字段
            profit_col = '订单实际利润' if '订单实际利润' in data.columns else '利润额'
            
            # 按距离分段统计
            distance_stats = []
            
            for label in DISTANCE_LABELS:
                segment = data[data['距离分段'] == label]
                
                if len(segment) == 0:
                    continue
                
                stats = {
                    '距离': label,
                    '订单数': len(segment),
                    '订单占比': round(len(segment) / len(data) * 100, 1)
                }
                
                if '物流配送费' in segment.columns:
                    stats['平均配送费'] = round(float(segment['物流配送费'].mean()), 2)
                    stats['配送费总额'] = round(float(segment['物流配送费'].sum()), 2)
                
                if profit_col in segment.columns:
                    stats['平均利润'] = round(float(segment[profit_col].mean()), 2)
                    stats['亏损订单数'] = int((segment[profit_col] < 0).sum())
                    stats['亏损率'] = round((segment[profit_col] < 0).mean() * 100, 1)
                
                if '实收价格' in segment.columns:
                    stats['平均客单价'] = round(float(segment['实收价格'].mean()), 2)
                
                distance_stats.append(stats)
            
            return {
                'success': True,
                'data': distance_stats,
                'config': {
                    'distance_bins': DISTANCE_BINS,
                    'distance_labels': DISTANCE_LABELS
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "距离分析失败")
    
    # ==================== 时段分析 ====================
    
    def analyze_by_time_period(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        按时段分析配送
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店筛选
        
        Returns:
            时段分析数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无订单数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 聚合到订单级
            if '订单ID' in data.columns and len(data) > data['订单ID'].nunique():
                data = self.aggregate_to_order_level(data)
            
            # 获取时段
            date_col = self.get_date_column(data)
            if date_col:
                data['小时'] = data[date_col].apply(self.get_hour_from_datetime)
                data['时段'] = data['小时'].apply(self.get_scene_period)
            else:
                return {'error': '缺少时间字段'}
            
            # 获取利润字段
            profit_col = '订单实际利润' if '订单实际利润' in data.columns else '利润额'
            
            # 按时段统计
            period_stats = []
            
            for scene in SCENE_ORDER:
                segment = data[data['时段'] == scene]
                
                if len(segment) == 0:
                    continue
                
                stats = {
                    '时段': scene,
                    '订单数': len(segment),
                    '订单占比': round(len(segment) / len(data) * 100, 1)
                }
                
                if '物流配送费' in segment.columns:
                    stats['平均配送费'] = round(float(segment['物流配送费'].mean()), 2)
                    stats['高配送费订单数'] = int((segment['物流配送费'] > self.delivery_fee_threshold).sum())
                
                if profit_col in segment.columns:
                    stats['平均利润'] = round(float(segment[profit_col].mean()), 2)
                    stats['亏损订单数'] = int((segment[profit_col] < 0).sum())
                
                if '实收价格' in segment.columns:
                    stats['平均客单价'] = round(float(segment['实收价格'].mean()), 2)
                
                period_stats.append(stats)
            
            return {
                'success': True,
                'data': period_stats,
                'config': {
                    'scene_periods': SCENE_PERIODS,
                    'scene_order': SCENE_ORDER
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "时段分析失败")

