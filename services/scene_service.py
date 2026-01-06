# -*- coding: utf-8 -*-
"""
场景分析服务

提供场景相关的分析功能：
- 场景分布分析
- 时段分析
- 场景×渠道交叉分析
- 场景趋势分析

版本: v1.0
创建日期: 2026-01-05
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta

from .base_service import BaseService
from .cache.cache_keys import CacheKeys


# 场景时段定义
SCENE_PERIODS = {
    '早餐': (6, 9),     # 06:00-08:59
    '午餐': (11, 14),   # 11:00-13:59
    '下午茶': (14, 17), # 14:00-16:59
    '晚餐': (17, 21),   # 17:00-20:59
    '夜宵': (21, 24),   # 21:00-23:59
}
SCENE_ORDER = ['早餐', '午餐', '下午茶', '晚餐', '夜宵']


class SceneService(BaseService):
    """
    场景分析服务
    
    提供场景和时段分析功能
    """
    
    def __init__(self, data_loader=None, cache_manager=None):
        super().__init__(cache_manager)
        self.data_loader = data_loader
        self.scene_periods = SCENE_PERIODS
        self.scene_order = SCENE_ORDER
    
    # ==================== 工具方法 ====================
    
    def get_scene_from_hour(self, hour: int) -> str:
        """根据小时获取场景"""
        if hour < 0:
            return '未知'
        
        for scene, (start, end) in self.scene_periods.items():
            if start < end:
                if start <= hour < end:
                    return scene
            else:
                if hour >= start or hour < end:
                    return scene
        
        return '其他'
    
    def add_scene_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """为DataFrame添加场景列"""
        data = df.copy()
        
        date_col = self.get_date_column(data)
        if date_col is None:
            data['场景'] = '未知'
            return data
        
        data[date_col] = pd.to_datetime(data[date_col])
        data['小时'] = data[date_col].dt.hour
        data['场景'] = data['小时'].apply(self.get_scene_from_hour)
        
        return data
    
    # ==================== 场景分布分析 ====================
    
    def get_scene_distribution(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取场景分布
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店筛选
        
        Returns:
            场景分布数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 聚合到订单级
            if '订单ID' in data.columns and len(data) > data['订单ID'].nunique():
                data = self.aggregate_to_order_level(data)
            
            # 添加场景列
            data = self.add_scene_column(data)
            
            # 获取利润字段
            profit_col = '订单实际利润' if '订单实际利润' in data.columns else '利润额'
            
            # 按场景统计
            scene_stats = []
            total_orders = len(data)
            
            for scene in self.scene_order:
                segment = data[data['场景'] == scene]
                
                if len(segment) == 0:
                    continue
                
                stats = {
                    '场景': scene,
                    '订单数': len(segment),
                    '订单占比': round(len(segment) / total_orders * 100, 1) if total_orders > 0 else 0
                }
                
                if '实收价格' in segment.columns:
                    stats['销售额'] = round(float(segment['实收价格'].sum()), 2)
                    stats['平均客单价'] = round(float(segment['实收价格'].mean()), 2)
                
                if profit_col in segment.columns:
                    stats['利润额'] = round(float(segment[profit_col].sum()), 2)
                    stats['平均利润'] = round(float(segment[profit_col].mean()), 2)
                    stats['利润率'] = round(
                        float(segment[profit_col].sum() / segment['实收价格'].sum() * 100), 2
                    ) if '实收价格' in segment.columns and segment['实收价格'].sum() > 0 else 0
                
                if '物流配送费' in segment.columns:
                    stats['平均配送费'] = round(float(segment['物流配送费'].mean()), 2)
                
                scene_stats.append(stats)
            
            return {
                'success': True,
                'data': scene_stats,
                'config': {
                    'scene_periods': self.scene_periods,
                    'scene_order': self.scene_order
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "获取场景分布失败")
    
    # ==================== 时段分析 ====================
    
    def get_hourly_analysis(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        按小时分析
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店筛选
        
        Returns:
            小时分析数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 聚合到订单级
            if '订单ID' in data.columns and len(data) > data['订单ID'].nunique():
                data = self.aggregate_to_order_level(data)
            
            # 获取小时
            date_col = self.get_date_column(data)
            if date_col is None:
                return {'error': '缺少日期字段'}
            
            data[date_col] = pd.to_datetime(data[date_col])
            data['小时'] = data[date_col].dt.hour
            
            # 按小时统计
            hourly_stats = data.groupby('小时').agg({
                '订单ID': 'count' if '订单ID' in data.columns else lambda x: len(x),
                '实收价格': 'sum' if '实收价格' in data.columns else lambda x: 0,
            }).reset_index()
            hourly_stats.columns = ['小时', '订单数', '销售额']
            
            # 补全24小时
            all_hours = pd.DataFrame({'小时': range(24)})
            hourly_stats = all_hours.merge(hourly_stats, on='小时', how='left')
            hourly_stats = hourly_stats.fillna(0)
            
            # 添加场景标签
            hourly_stats['场景'] = hourly_stats['小时'].apply(self.get_scene_from_hour)
            
            return {
                'success': True,
                'data': self.clean_for_json(hourly_stats.to_dict('records'))
            }
            
        except Exception as e:
            return self.handle_error(e, "小时分析失败")
    
    # ==================== 场景×渠道交叉分析 ====================
    
    def get_scene_channel_cross(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        场景×渠道交叉分析
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店筛选
        
        Returns:
            交叉分析数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 聚合到订单级
            if '订单ID' in data.columns and len(data) > data['订单ID'].nunique():
                data = self.aggregate_to_order_level(data)
            
            # 添加场景列
            data = self.add_scene_column(data)
            
            # 获取渠道列
            channel_col = next(
                (c for c in ['平台', '渠道', 'platform', 'channel'] if c in data.columns),
                None
            )
            
            if channel_col is None:
                return {'error': '缺少渠道字段'}
            
            # 交叉统计
            cross_stats = data.groupby(['场景', channel_col]).agg({
                '订单ID': 'count' if '订单ID' in data.columns else lambda x: len(x),
                '实收价格': 'sum' if '实收价格' in data.columns else lambda x: 0,
            }).reset_index()
            cross_stats.columns = ['场景', '渠道', '订单数', '销售额']
            
            # 转换为热力图格式
            heatmap_data = []
            channels = data[channel_col].unique().tolist()
            
            for scene in self.scene_order:
                for channel in channels:
                    row = cross_stats[(cross_stats['场景'] == scene) & (cross_stats['渠道'] == channel)]
                    order_count = int(row['订单数'].values[0]) if len(row) > 0 else 0
                    sales_amount = float(row['销售额'].values[0]) if len(row) > 0 else 0
                    
                    heatmap_data.append({
                        '场景': scene,
                        '渠道': channel,
                        '订单数': order_count,
                        '销售额': round(sales_amount, 2)
                    })
            
            return {
                'success': True,
                'data': heatmap_data,
                'config': {
                    'scenes': self.scene_order,
                    'channels': channels
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "场景渠道交叉分析失败")
    
    # ==================== 场景趋势分析 ====================
    
    def get_scene_trend(
        self,
        df: pd.DataFrame,
        days: int = 7,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        场景趋势分析
        
        Args:
            df: 订单数据DataFrame
            days: 分析天数
            store_name: 门店筛选
        
        Returns:
            场景趋势数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 聚合到订单级
            if '订单ID' in data.columns and len(data) > data['订单ID'].nunique():
                data = self.aggregate_to_order_level(data)
            
            # 添加场景列
            data = self.add_scene_column(data)
            
            # 获取日期
            date_col = self.get_date_column(data)
            if date_col is None:
                return {'error': '缺少日期字段'}
            
            data[date_col] = pd.to_datetime(data[date_col])
            data['日期'] = data[date_col].dt.date
            
            # 筛选最近N天
            max_date = data['日期'].max()
            min_date = max_date - timedelta(days=days-1)
            data = data[data['日期'] >= min_date]
            
            # 按日期和场景统计
            trend_data = data.groupby(['日期', '场景']).agg({
                '订单ID': 'count' if '订单ID' in data.columns else lambda x: len(x),
                '实收价格': 'sum' if '实收价格' in data.columns else lambda x: 0,
            }).reset_index()
            trend_data.columns = ['日期', '场景', '订单数', '销售额']
            trend_data['日期'] = trend_data['日期'].astype(str)
            
            # 按场景分组
            by_scene = {}
            for scene in self.scene_order:
                scene_data = trend_data[trend_data['场景'] == scene].copy()
                by_scene[scene] = self.clean_for_json(scene_data.to_dict('records'))
            
            return {
                'success': True,
                'data': by_scene,
                'config': {
                    'days': days,
                    'scene_order': self.scene_order
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "场景趋势分析失败")
    
    # ==================== 场景商品分析 ====================
    
    def get_scene_products(
        self,
        df: pd.DataFrame,
        scene: str,
        top_n: int = 10,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取指定场景的热销商品
        
        Args:
            df: 订单数据DataFrame（商品级）
            scene: 场景名称
            top_n: Top N
            store_name: 门店筛选
        
        Returns:
            场景商品数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 添加场景列
            data = self.add_scene_column(data)
            
            # 筛选指定场景
            if scene not in self.scene_order:
                return {'error': f'无效场景: {scene}'}
            
            scene_data = data[data['场景'] == scene]
            
            if scene_data.empty:
                return {'error': f'{scene}场景无数据'}
            
            # 商品聚合
            if '商品名称' not in scene_data.columns:
                return {'error': '缺少商品名称字段'}
            
            sales_col = self.get_sales_column(scene_data)
            
            product_stats = scene_data.groupby('商品名称').agg({
                sales_col: 'sum' if sales_col in scene_data.columns else lambda x: 0,
                '实收价格': 'sum' if '实收价格' in scene_data.columns else lambda x: 0,
                '利润额': 'sum' if '利润额' in scene_data.columns else lambda x: 0,
            }).reset_index()
            
            product_stats.columns = ['商品名称', '销量', '销售额', '利润额']
            product_stats = product_stats.sort_values('销量', ascending=False).head(top_n)
            
            return {
                'success': True,
                'data': self.clean_for_json(product_stats.to_dict('records')),
                'scene': scene
            }
            
        except Exception as e:
            return self.handle_error(e, f"获取{scene}场景商品失败")

