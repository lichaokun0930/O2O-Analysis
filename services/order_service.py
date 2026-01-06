# -*- coding: utf-8 -*-
"""
订单分析服务

提供订单相关的分析功能：
- KPI指标计算
- 订单趋势分析
- 渠道分析
- 订单列表查询

业务逻辑来源: 智能门店看板_Dash版.py 中的 Tab 1 回调

版本: v1.0
创建日期: 2026-01-05
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass

from .base_service import BaseService, cache_result
from .cache.cache_keys import CacheKeys


@dataclass
class OrderKPI:
    """订单KPI数据类"""
    total_orders: int           # 总订单数
    total_amount: float         # 总销售额
    total_profit: float         # 总利润
    avg_order_value: float      # 平均客单价
    avg_profit_rate: float      # 平均利润率
    order_count_trend: float    # 订单数环比
    amount_trend: float         # 销售额环比
    profit_trend: float         # 利润环比


@dataclass 
class OrderTrendData:
    """订单趋势数据类"""
    dates: List[str]            # 日期列表
    order_counts: List[int]     # 订单数列表
    amounts: List[float]        # 销售额列表
    profits: List[float]        # 利润列表
    avg_values: List[float]     # 客单价列表


class OrderService(BaseService):
    """
    订单分析服务
    
    提供订单数据分析功能，从Dash回调中抽取的业务逻辑
    """
    
    def __init__(self, data_loader=None, cache_manager=None):
        """
        初始化订单服务
        
        Args:
            data_loader: 数据加载器（可选）
            cache_manager: 缓存管理器（可选）
        """
        super().__init__(cache_manager)
        self.data_loader = data_loader
    
    # ==================== KPI计算 ====================
    
    def get_kpi(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取订单KPI指标
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店名称筛选
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            KPI指标字典
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            # 复制数据避免修改原始数据
            data = df.copy()
            
            # 门店筛选
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 日期筛选
            date_col = self.get_date_column(data)
            if date_col and start_date:
                data[date_col] = pd.to_datetime(data[date_col])
                data = data[data[date_col].dt.date >= start_date]
            if date_col and end_date:
                data = data[data[date_col].dt.date <= end_date]
            
            if data.empty:
                return {'error': '筛选后无数据'}
            
            # 聚合到订单级
            order_agg = self.aggregate_to_order_level(data)
            
            # 计算KPI
            sales_col = self.get_sales_column(data)
            
            total_orders = len(order_agg)
            total_amount = order_agg['实收价格'].sum() if '实收价格' in order_agg.columns else 0
            total_profit = order_agg['订单实际利润'].sum() if '订单实际利润' in order_agg.columns else 0
            
            avg_order_value = total_amount / total_orders if total_orders > 0 else 0
            avg_profit_rate = (total_profit / total_amount * 100) if total_amount > 0 else 0
            
            # 计算环比（与前一周期对比）
            trends = self._calculate_trends(data, date_col)
            
            return {
                'success': True,
                'data': {
                    'total_orders': int(total_orders),
                    'total_amount': round(float(total_amount), 2),
                    'total_profit': round(float(total_profit), 2),
                    'avg_order_value': round(float(avg_order_value), 2),
                    'avg_profit_rate': round(float(avg_profit_rate), 2),
                    'order_count_trend': trends.get('order_count_trend', 0),
                    'amount_trend': trends.get('amount_trend', 0),
                    'profit_trend': trends.get('profit_trend', 0),
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "计算KPI失败")
    
    def _calculate_trends(self, df: pd.DataFrame, date_col: str) -> Dict[str, float]:
        """计算环比趋势"""
        if date_col is None:
            return {}
        
        try:
            df = df.copy()
            df[date_col] = pd.to_datetime(df[date_col])
            yesterday = df[date_col].max().normalize()
            day_before = yesterday - timedelta(days=1)
            
            # 昨日数据
            yesterday_data = df[df[date_col].dt.normalize() == yesterday]
            day_before_data = df[df[date_col].dt.normalize() == day_before]
            
            # 聚合
            yesterday_orders = yesterday_data['订单ID'].nunique() if '订单ID' in yesterday_data.columns else len(yesterday_data)
            day_before_orders = day_before_data['订单ID'].nunique() if '订单ID' in day_before_data.columns else len(day_before_data)
            
            # 计算环比
            order_trend = 0
            if day_before_orders > 0:
                order_trend = (yesterday_orders - day_before_orders) / day_before_orders * 100
            
            return {
                'order_count_trend': round(order_trend, 1)
            }
        except:
            return {}
    
    # ==================== 趋势分析 ====================
    
    def get_trend(
        self,
        df: pd.DataFrame,
        days: int = 30,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取订单趋势数据
        
        Args:
            df: 订单数据DataFrame
            days: 统计天数
            store_name: 门店名称筛选
        
        Returns:
            趋势数据字典
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            # 门店筛选
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            date_col = self.get_date_column(data)
            if date_col is None:
                return {'error': '缺少日期字段'}
            
            data[date_col] = pd.to_datetime(data[date_col])
            
            # 筛选最近N天
            max_date = data[date_col].max()
            min_date = max_date - timedelta(days=days)
            data = data[data[date_col] >= min_date]
            
            # 按日期聚合
            daily = data.groupby(data[date_col].dt.date).agg({
                '订单ID': 'nunique' if '订单ID' in data.columns else 'count',
                '实收价格': 'sum' if '实收价格' in data.columns else lambda x: 0,
                '利润额': 'sum' if '利润额' in data.columns else lambda x: 0,
            }).reset_index()
            
            daily.columns = ['date', 'order_count', 'amount', 'profit']
            daily = daily.sort_values('date')
            
            # 计算客单价
            daily['avg_value'] = daily.apply(
                lambda r: r['amount'] / r['order_count'] if r['order_count'] > 0 else 0,
                axis=1
            )
            
            return {
                'success': True,
                'data': {
                    'dates': [str(d) for d in daily['date'].tolist()],
                    'order_counts': daily['order_count'].tolist(),
                    'amounts': [round(x, 2) for x in daily['amount'].tolist()],
                    'profits': [round(x, 2) for x in daily['profit'].tolist()],
                    'avg_values': [round(x, 2) for x in daily['avg_value'].tolist()],
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "获取趋势数据失败")
    
    # ==================== 渠道分析 ====================
    
    def get_by_channel(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取渠道分析数据
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店名称筛选
        
        Returns:
            渠道分析数据字典
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            # 门店筛选
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 获取渠道列
            channel_col = next(
                (c for c in ['平台', '渠道', 'platform', 'channel'] if c in data.columns),
                None
            )
            
            if channel_col is None:
                return {'error': '缺少渠道字段'}
            
            # 按渠道聚合
            channel_stats = data.groupby(channel_col).agg({
                '订单ID': 'nunique' if '订单ID' in data.columns else 'count',
                '实收价格': 'sum' if '实收价格' in data.columns else lambda x: 0,
                '利润额': 'sum' if '利润额' in data.columns else lambda x: 0,
            }).reset_index()
            
            channel_stats.columns = ['channel', 'order_count', 'amount', 'profit']
            
            # 计算占比
            total_orders = channel_stats['order_count'].sum()
            total_amount = channel_stats['amount'].sum()
            
            channel_stats['order_ratio'] = channel_stats['order_count'] / total_orders * 100 if total_orders > 0 else 0
            channel_stats['amount_ratio'] = channel_stats['amount'] / total_amount * 100 if total_amount > 0 else 0
            channel_stats['avg_value'] = channel_stats.apply(
                lambda r: r['amount'] / r['order_count'] if r['order_count'] > 0 else 0,
                axis=1
            )
            channel_stats['profit_rate'] = channel_stats.apply(
                lambda r: r['profit'] / r['amount'] * 100 if r['amount'] > 0 else 0,
                axis=1
            )
            
            # 按订单数排序
            channel_stats = channel_stats.sort_values('order_count', ascending=False)
            
            return {
                'success': True,
                'data': self.clean_for_json(channel_stats.to_dict('records'))
            }
            
        except Exception as e:
            return self.handle_error(e, "获取渠道分析失败")
    
    # ==================== 订单列表 ====================
    
    def get_order_list(
        self,
        df: pd.DataFrame,
        page: int = 1,
        page_size: int = 50,
        store_name: Optional[str] = None,
        channel: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_by: str = 'date',
        sort_order: str = 'desc'
    ) -> Dict[str, Any]:
        """
        获取订单列表（支持分页和筛选）
        
        Args:
            df: 订单数据DataFrame
            page: 页码
            page_size: 每页数量
            store_name: 门店筛选
            channel: 渠道筛选
            start_date: 开始日期
            end_date: 结束日期
            sort_by: 排序字段
            sort_order: 排序方向
        
        Returns:
            订单列表数据字典
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据', 'data': [], 'total': 0}
            
            data = df.copy()
            
            # 应用筛选
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            channel_col = next(
                (c for c in ['平台', '渠道'] if c in data.columns), None
            )
            if channel and channel_col:
                data = data[data[channel_col] == channel]
            
            date_col = self.get_date_column(data)
            if date_col:
                data[date_col] = pd.to_datetime(data[date_col])
                if start_date:
                    data = data[data[date_col].dt.date >= start_date]
                if end_date:
                    data = data[data[date_col].dt.date <= end_date]
            
            # 聚合到订单级
            order_agg = self.aggregate_to_order_level(data)
            
            # 排序
            sort_col_map = {
                'date': date_col or '订单ID',
                'amount': '实收价格',
                'profit': '订单实际利润',
            }
            sort_col = sort_col_map.get(sort_by, '订单ID')
            if sort_col in order_agg.columns:
                order_agg = order_agg.sort_values(
                    sort_col, 
                    ascending=(sort_order == 'asc')
                )
            
            # 分页
            total = len(order_agg)
            start = (page - 1) * page_size
            end = start + page_size
            page_data = order_agg.iloc[start:end]
            
            # 选择展示字段
            display_cols = ['订单ID']
            if date_col and date_col in page_data.columns:
                display_cols.append(date_col)
            for col in ['商品名称', '实收价格', '订单实际利润', '物流配送费']:
                if col in page_data.columns:
                    display_cols.append(col)
            if channel_col and channel_col in page_data.columns:
                display_cols.append(channel_col)
            
            result_data = page_data[display_cols].copy()
            
            # 格式化日期
            if date_col in result_data.columns:
                result_data[date_col] = result_data[date_col].dt.strftime('%Y-%m-%d %H:%M')
            
            return {
                'success': True,
                'data': self.clean_for_json(result_data.to_dict('records')),
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
            
        except Exception as e:
            return self.handle_error(e, "获取订单列表失败")
    
    # ==================== 门店列表 ====================
    
    def get_store_list(self, df: pd.DataFrame) -> List[str]:
        """获取门店列表"""
        if df is None or df.empty:
            return []
        
        if '门店名称' in df.columns:
            return sorted(df['门店名称'].dropna().unique().tolist())
        return []
    
    # ==================== 渠道列表 ====================
    
    def get_channel_list(self, df: pd.DataFrame) -> List[str]:
        """获取渠道列表"""
        if df is None or df.empty:
            return []
        
        channel_col = next(
            (c for c in ['平台', '渠道', 'platform', 'channel'] if c in df.columns),
            None
        )
        
        if channel_col:
            return sorted(df[channel_col].dropna().unique().tolist())
        return []

