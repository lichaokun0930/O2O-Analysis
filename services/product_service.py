# -*- coding: utf-8 -*-
"""
商品分析服务

提供商品相关的分析功能：
- 商品排行榜
- 分类分析
- 库存分析
- 热销商品
- 高利润商品

业务逻辑来源: 
- components/today_must_do/product_analysis.py
- 智能门店看板_Dash版.py 中的 Tab 3 回调

版本: v1.0
创建日期: 2026-01-05
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass

from .base_service import BaseService
from .cache.cache_keys import CacheKeys


@dataclass
class ProductMetrics:
    """商品指标数据类"""
    product_name: str
    store_code: Optional[str]
    sales_quantity: int
    sales_amount: float
    profit: float
    profit_rate: float
    cost: float


class ProductService(BaseService):
    """
    商品分析服务
    
    提供商品数据分析功能
    """
    
    def __init__(self, data_loader=None, cache_manager=None):
        super().__init__(cache_manager)
        self.data_loader = data_loader
    
    # ==================== 商品日指标 ====================
    
    def get_product_daily_metrics(
        self, 
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
        """
        date_col = self.get_date_column(df)
        sales_col = self.get_sales_column(df)
        
        if date_col is None:
            return pd.DataFrame()
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 筛选指定日期
        day_data = df[df[date_col].dt.normalize() == target_date]
        
        if len(day_data) == 0:
            return pd.DataFrame()
        
        # 使用店内码聚合，避免同名不同规格商品混淆
        group_key = self.get_product_group_key(day_data)
        
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
        if '销售额' in result.columns:
            sales_safe = result['销售额'].replace(0, np.nan)
            
            if '成本' in result.columns:
                result['毛利率'] = ((result['销售额'] - result['成本']) / sales_safe * 100).round(2)
            elif '利润额' in result.columns:
                result['毛利率'] = (result['利润额'] / sales_safe * 100).round(2)
            else:
                result['毛利率'] = np.nan
            
            result['毛利率'] = result['毛利率'].replace([np.inf, -np.inf], np.nan)
        else:
            result['毛利率'] = np.nan
        
        return result
    
    # ==================== 商品排行 ====================
    
    def get_ranking(
        self,
        df: pd.DataFrame,
        sort_by: str = 'sales',  # sales/profit/quantity
        top_n: int = 20,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取商品排行榜
        
        Args:
            df: 订单数据DataFrame
            sort_by: 排序依据 (sales/profit/quantity)
            top_n: Top N
            store_name: 门店筛选
        
        Returns:
            排行榜数据字典
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            # 门店筛选
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 获取昨日日期
            yesterday = self.get_base_date(data)
            if yesterday is None:
                return {'error': '无法获取日期信息'}
            
            # 获取昨日商品指标
            metrics = self.get_product_daily_metrics(data, yesterday)
            if metrics.empty:
                return {'error': '昨日无销售数据'}
            
            # 排序
            sort_col_map = {
                'sales': '销售额',
                'profit': '利润额',
                'quantity': '销量'
            }
            sort_col = sort_col_map.get(sort_by, '销售额')
            
            if sort_col not in metrics.columns:
                return {'error': f'缺少排序字段: {sort_col}'}
            
            ranking = metrics.sort_values(sort_col, ascending=False).head(top_n).copy()
            
            # 计算单均指标
            if '销量' in ranking.columns and ranking['销量'].sum() > 0:
                if '利润额' in ranking.columns:
                    ranking['单均利润'] = (ranking['利润额'] / ranking['销量']).round(2)
                if '销售额' in ranking.columns:
                    ranking['单均价格'] = (ranking['销售额'] / ranking['销量']).round(2)
            
            return {
                'success': True,
                'data': self.clean_for_json(ranking.to_dict('records')),
                'summary': {
                    'total_count': len(ranking),
                    'total_sales': round(float(ranking['销售额'].sum()), 2) if '销售额' in ranking.columns else 0,
                    'total_profit': round(float(ranking['利润额'].sum()), 2) if '利润额' in ranking.columns else 0,
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "获取商品排行失败")
    
    # ==================== 热销商品 ====================
    
    def get_hot_products(
        self,
        df: pd.DataFrame,
        top_n: int = 10,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取热销商品TOP N
        
        Args:
            df: 订单数据DataFrame
            top_n: Top N
            store_name: 门店筛选
        
        Returns:
            热销商品数据
        """
        return self.get_ranking(df, sort_by='quantity', top_n=top_n, store_name=store_name)
    
    # ==================== 高利润商品 ====================
    
    def get_high_profit_products(
        self,
        df: pd.DataFrame,
        top_n: int = 20,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取高利润商品TOP N
        
        定义: 昨日给门店赚钱最多的商品（现金牛）
        
        Args:
            df: 订单数据DataFrame
            top_n: Top N
            store_name: 门店筛选
        
        Returns:
            高利润商品数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            yesterday = self.get_base_date(data)
            if yesterday is None:
                return {'error': '无法获取日期信息'}
            
            day_before = yesterday - timedelta(days=1)
            
            # 获取昨日数据
            metrics = self.get_product_daily_metrics(data, yesterday)
            if metrics.empty:
                return {'error': '昨日无销售数据'}
            
            # 筛选利润>0并排序
            if '利润额' not in metrics.columns:
                return {'error': '缺少利润额字段'}
            
            top_profit = metrics[metrics['利润额'] > 0].sort_values('利润额', ascending=False).head(top_n).copy()
            
            # 计算单均利润
            if '销量' in top_profit.columns:
                top_profit['单均利润额'] = (top_profit['利润额'] / top_profit['销量']).round(2)
            
            # 检查前日销量以标记"昨日首销"
            day_before_metrics = self.get_product_daily_metrics(data, day_before)
            if not day_before_metrics.empty and '商品名称' in day_before_metrics.columns:
                day_before_sales = day_before_metrics[['商品名称', '销量']].rename(columns={'销量': '前日销量'})
                top_profit = top_profit.merge(day_before_sales, on='商品名称', how='left')
                top_profit['前日销量'] = top_profit['前日销量'].fillna(0)
                top_profit['是否新增'] = top_profit['前日销量'] == 0
            else:
                top_profit['前日销量'] = 0
                top_profit['是否新增'] = False
            
            return {
                'success': True,
                'data': self.clean_for_json(top_profit.to_dict('records')),
                'summary': {
                    'total_profit': round(float(top_profit['利润额'].sum()), 2),
                    'count': len(top_profit)
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "获取高利润商品失败")
    
    # ==================== 分类分析 ====================
    
    def get_category_analysis(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取分类分析数据
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店筛选
        
        Returns:
            分类分析数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 查找分类列
            category_col = None
            for col in ['一级分类名', '一级分类', 'category_level1', 'category']:
                if col in data.columns:
                    category_col = col
                    break
            
            if category_col is None:
                return {'error': '缺少分类字段'}
            
            sales_col = self.get_sales_column(data)
            
            # 按分类聚合
            agg_dict = {
                '商品数': ('商品名称', 'nunique') if '商品名称' in data.columns else (category_col, 'count'),
            }
            
            if sales_col in data.columns:
                agg_dict['销量'] = (sales_col, 'sum')
            
            if '实收价格' in data.columns:
                agg_dict['销售额'] = ('实收价格', 'sum')
            
            if '利润额' in data.columns:
                agg_dict['利润额'] = ('利润额', 'sum')
            
            category_stats = data.groupby(category_col).agg(**agg_dict).reset_index()
            category_stats.columns = ['分类', '商品数', '销量', '销售额', '利润额'][:len(category_stats.columns)]
            
            # 计算占比
            if '销售额' in category_stats.columns:
                total_amount = category_stats['销售额'].sum()
                category_stats['销售额占比'] = (category_stats['销售额'] / total_amount * 100).round(2) if total_amount > 0 else 0
            
            if '利润额' in category_stats.columns and '销售额' in category_stats.columns:
                category_stats['利润率'] = (category_stats['利润额'] / category_stats['销售额'] * 100).round(2)
                category_stats['利润率'] = category_stats['利润率'].replace([np.inf, -np.inf], 0)
            
            # 按销售额排序
            category_stats = category_stats.sort_values('销售额' if '销售额' in category_stats.columns else '商品数', ascending=False)
            
            return {
                'success': True,
                'data': self.clean_for_json(category_stats.to_dict('records'))
            }
            
        except Exception as e:
            return self.handle_error(e, "获取分类分析失败")
    
    # ==================== 库存分析 ====================
    
    def get_inventory_analysis(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取库存分析数据
        
        Args:
            df: 订单数据DataFrame（需包含库存字段）
            store_name: 门店筛选
        
        Returns:
            库存分析数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 查找库存列
            stock_col = None
            for col in ['库存', '剩余库存', 'stock', 'inventory']:
                if col in data.columns:
                    stock_col = col
                    break
            
            if stock_col is None:
                return {'error': '缺少库存字段', 'data': []}
            
            # 按商品聚合（取最新库存）
            group_key = self.get_product_group_key(data)
            
            product_stock = data.groupby(group_key).agg({
                '商品名称': 'first' if group_key != '商品名称' else 'first',
                stock_col: 'last',  # 取最新库存
                self.get_sales_column(data): 'sum' if self.get_sales_column(data) in data.columns else lambda x: 0,
            }).reset_index()
            
            product_stock.columns = [group_key, '商品名称', '库存', '销量'][:len(product_stock.columns)]
            
            # 库存状态分类
            def classify_stock(row):
                stock = row.get('库存', 0)
                sales = row.get('销量', 0)
                
                if stock <= 0:
                    return '售罄'
                elif stock <= 5:
                    return '紧张'
                elif sales > 0 and stock < sales * 3:  # 库存不足3天销量
                    return '预警'
                else:
                    return '充足'
            
            product_stock['库存状态'] = product_stock.apply(classify_stock, axis=1)
            
            # 统计各状态数量
            status_counts = product_stock['库存状态'].value_counts().to_dict()
            
            # 低库存商品列表
            low_stock = product_stock[product_stock['库存状态'].isin(['售罄', '紧张', '预警'])].copy()
            low_stock = low_stock.sort_values('库存')
            
            return {
                'success': True,
                'data': self.clean_for_json(low_stock.to_dict('records')),
                'summary': {
                    'total_products': len(product_stock),
                    'status_counts': status_counts,
                    'low_stock_count': len(low_stock)
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "获取库存分析失败")
    
    # ==================== 流量下滑商品 ====================
    
    def get_traffic_drop_products(
        self,
        df: pd.DataFrame,
        top_n: int = 20,
        drop_threshold: float = 0.5,
        min_sales: int = 3,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取流量下滑商品
        
        定义: 以前卖得好，昨天突然卖不动了
        筛选: 前日销量 >= min_sales 且 昨日销量环比下跌 > drop_threshold
        
        Args:
            df: 订单数据DataFrame
            top_n: Top N
            drop_threshold: 下跌阈值（50%）
            min_sales: 最小前日销量
            store_name: 门店筛选
        
        Returns:
            流量下滑商品数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            yesterday = self.get_base_date(data)
            if yesterday is None:
                return {'error': '无法获取日期信息'}
            
            day_before = yesterday - timedelta(days=1)
            
            # 获取两日数据
            yesterday_metrics = self.get_product_daily_metrics(data, yesterday)
            day_before_metrics = self.get_product_daily_metrics(data, day_before)
            
            if yesterday_metrics.empty or day_before_metrics.empty:
                return {'error': '数据不足，无法进行对比'}
            
            # 合并对比
            comparison = day_before_metrics[['商品名称', '销量']].rename(columns={'销量': '前日销量'})
            comparison = comparison.merge(
                yesterday_metrics[['商品名称', '销量']].rename(columns={'销量': '昨日销量'}),
                on='商品名称',
                how='left'
            )
            comparison['昨日销量'] = comparison['昨日销量'].fillna(0)
            
            # 筛选：前日销量>=min_sales 且 下跌>threshold
            comparison['下跌幅度'] = (comparison['前日销量'] - comparison['昨日销量']) / comparison['前日销量']
            
            drop_products = comparison[
                (comparison['前日销量'] >= min_sales) & 
                (comparison['下跌幅度'] >= drop_threshold)
            ].copy()
            
            drop_products = drop_products.sort_values('下跌幅度', ascending=False).head(top_n)
            drop_products['下跌幅度'] = (drop_products['下跌幅度'] * 100).round(1)
            
            return {
                'success': True,
                'data': self.clean_for_json(drop_products.to_dict('records')),
                'summary': {
                    'count': len(drop_products),
                    'zero_sales_count': int((drop_products['昨日销量'] == 0).sum())
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "获取流量下滑商品失败")

