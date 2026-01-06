# -*- coding: utf-8 -*-
"""
营销分析服务

提供营销相关的分析功能：
- 营销导致亏损订单分析
- 活动类型分布
- 活动叠加分析
- 折扣分析

业务逻辑来源: components/today_must_do/marketing_analysis.py

核心判断标准:
  - 营销导致亏损订单:
    ├── 基础条件: 订单实际利润 < 0
    ├── 营销关联: 订单参与了满减/优惠券/商品减免等活动
    └── 分类标签: 标记该订单参与的所有活动类型

版本: v1.0
创建日期: 2026-01-05
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta

from .base_service import BaseService
from .cache.cache_keys import CacheKeys


# 配送费阈值
DELIVERY_FEE_THRESHOLD = 6.0

# 活动类型字段映射（全部是订单级字段）
ACTIVITY_FIELDS = {
    '满减活动': '满减金额',
    '商品减免': '商品减免金额',
    '新客券': '新客减免金额',
    '商家代金券': '商家代金券',
    '商家承担券': '商家承担部分券',
    '满赠': '满赠金额',
    '其他优惠': '商家其他优惠'
}


class MarketingService(BaseService):
    """
    营销分析服务
    
    提供营销数据分析功能
    """
    
    def __init__(self, data_loader=None, cache_manager=None):
        super().__init__(cache_manager)
        self.data_loader = data_loader
        self.activity_fields = ACTIVITY_FIELDS
    
    # ==================== 营销损失分析 ====================
    
    def analyze_marketing_loss(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None,
        yesterday_only: bool = True
    ) -> Dict[str, Any]:
        """
        营销导致亏损订单分析
        
        定义:
        - 基础条件: 订单实际利润 < 0
        - 营销关联: 参与了活动
        - 分类: 按活动类型统计
        
        Args:
            df: 订单数据DataFrame（需为订单级聚合后）
            store_name: 门店筛选
            yesterday_only: 是否只分析昨日数据
        
        Returns:
            营销损失分析数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无订单数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 聚合到订单级（如果还不是）
            if '订单ID' in data.columns and len(data) > data['订单ID'].nunique():
                data = self.aggregate_to_order_level(data)
            
            # 获取利润字段
            profit_col = None
            for col in ['订单实际利润', '利润额']:
                if col in data.columns:
                    profit_col = col
                    break
            
            if profit_col is None:
                return {'error': '缺少利润字段'}
            
            # 筛选昨日数据
            if yesterday_only:
                date_col = self.get_date_column(data)
                if date_col:
                    data[date_col] = pd.to_datetime(data[date_col])
                    yesterday = data[date_col].max().normalize()
                    data = data[data[date_col].dt.normalize() == yesterday]
            
            if data.empty:
                return {'error': '昨日无订单数据'}
            
            # 计算商家活动成本
            data['商家活动成本'] = 0
            for activity_name, field_name in self.activity_fields.items():
                if field_name in data.columns:
                    data['商家活动成本'] += data[field_name].fillna(0)
            
            # 标记参与活动的订单
            data['参与活动'] = data['商家活动成本'] > 0
            
            # 亏损订单：利润<0 且 参与了活动
            data['是否亏损'] = (data[profit_col] < 0) & data['参与活动']
            loss_orders = data[data['是否亏损']].copy()
            
            # 按活动类型统计
            by_activity_type = []
            for activity_name, field_name in self.activity_fields.items():
                if field_name in data.columns:
                    # 参与该活动的亏损订单
                    has_activity = data[field_name].fillna(0) > 0
                    loss_with_activity = (data[profit_col] < 0) & has_activity
                    
                    if loss_with_activity.sum() > 0:
                        activity_loss_df = data[loss_with_activity]
                        by_activity_type.append({
                            '活动类型': activity_name,
                            '订单数': int(loss_with_activity.sum()),
                            '亏损金额': round(abs(float(activity_loss_df[profit_col].sum())), 2),
                            '单均亏损': round(abs(float(activity_loss_df[profit_col].mean())), 2),
                            '活动补贴总额': round(float(activity_loss_df[field_name].sum()), 2)
                        })
            
            # 按亏损金额排序
            by_activity_type = sorted(by_activity_type, key=lambda x: x['亏损金额'], reverse=True)
            
            return {
                'success': True,
                'data': {
                    'by_activity_type': by_activity_type,
                    'loss_orders': self.clean_for_json(loss_orders.head(50).to_dict('records'))
                },
                'summary': {
                    'total_orders': len(data),
                    'activity_orders': int(data['参与活动'].sum()),
                    'loss_orders': int(data['是否亏损'].sum()),
                    'total_loss': round(abs(float(loss_orders[profit_col].sum())), 2) if len(loss_orders) > 0 else 0,
                    'total_activity_cost': round(float(data['商家活动成本'].sum()), 2)
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "营销损失分析失败")
    
    # ==================== 活动叠加分析 ====================
    
    def analyze_activity_overlap(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None,
        yesterday_only: bool = True
    ) -> Dict[str, Any]:
        """
        活动叠加分析
        
        分析同时参与多个活动的订单
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店筛选
            yesterday_only: 是否只分析昨日数据
        
        Returns:
            活动叠加分析数据
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
                return {'error': '无数据'}
            
            # 计算每个订单参与的活动数量
            data['活动数量'] = 0
            data['活动类型列表'] = ''
            
            for activity_name, field_name in self.activity_fields.items():
                if field_name in data.columns:
                    has_activity = data[field_name].fillna(0) > 0
                    data.loc[has_activity, '活动数量'] += 1
                    data.loc[has_activity, '活动类型列表'] += activity_name + ','
            
            # 去掉末尾逗号
            data['活动类型列表'] = data['活动类型列表'].str.rstrip(',')
            
            # 按活动数量分组统计
            overlap_stats = data.groupby('活动数量').agg({
                '订单ID': 'count',
                '实收价格': 'sum' if '实收价格' in data.columns else lambda x: 0,
            }).reset_index()
            overlap_stats.columns = ['活动数量', '订单数', '销售额']
            
            # 多活动叠加订单详情
            multi_activity = data[data['活动数量'] >= 2].copy()
            
            # 获取利润字段
            profit_col = '订单实际利润' if '订单实际利润' in multi_activity.columns else '利润额'
            
            multi_activity_summary = None
            if not multi_activity.empty and profit_col in multi_activity.columns:
                multi_activity_summary = {
                    'count': len(multi_activity),
                    'loss_count': int((multi_activity[profit_col] < 0).sum()),
                    'loss_rate': round((multi_activity[profit_col] < 0).mean() * 100, 1),
                    'avg_activity_count': round(float(multi_activity['活动数量'].mean()), 1)
                }
            
            return {
                'success': True,
                'data': {
                    'overlap_stats': self.clean_for_json(overlap_stats.to_dict('records')),
                    'multi_activity_orders': self.clean_for_json(multi_activity.head(30).to_dict('records'))
                },
                'summary': multi_activity_summary or {
                    'count': 0,
                    'loss_count': 0,
                    'loss_rate': 0,
                    'avg_activity_count': 0
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "活动叠加分析失败")
    
    # ==================== 高配送费×活动叠加交叉分析 ====================
    
    def analyze_delivery_activity_cross(
        self,
        df: pd.DataFrame,
        delivery_threshold: float = DELIVERY_FEE_THRESHOLD,
        store_name: Optional[str] = None,
        yesterday_only: bool = True
    ) -> Dict[str, Any]:
        """
        配送费×活动叠加交叉分析
        
        分析高配送费且参与活动的订单
        
        Args:
            df: 订单数据DataFrame
            delivery_threshold: 配送费阈值
            store_name: 门店筛选
            yesterday_only: 是否只分析昨日数据
        
        Returns:
            交叉分析数据
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
                return {'error': '无数据'}
            
            # 检查必要字段
            if '物流配送费' not in data.columns:
                return {'error': '缺少配送费字段'}
            
            # 计算活动成本
            data['商家活动成本'] = 0
            for activity_name, field_name in self.activity_fields.items():
                if field_name in data.columns:
                    data['商家活动成本'] += data[field_name].fillna(0)
            
            # 标记高配送费
            data['高配送费'] = data['物流配送费'] > delivery_threshold
            
            # 标记参与活动
            data['参与活动'] = data['商家活动成本'] > 0
            
            # 交叉分组
            cross_stats = data.groupby(['高配送费', '参与活动']).agg({
                '订单ID': 'count',
                '实收价格': 'sum' if '实收价格' in data.columns else lambda x: 0,
            }).reset_index()
            cross_stats.columns = ['高配送费', '参与活动', '订单数', '销售额']
            
            # 高配送费+活动叠加的订单（风险最高）
            high_risk = data[(data['高配送费']) & (data['参与活动'])].copy()
            
            profit_col = '订单实际利润' if '订单实际利润' in high_risk.columns else '利润额'
            
            high_risk_summary = None
            if not high_risk.empty and profit_col in high_risk.columns:
                high_risk_summary = {
                    'count': len(high_risk),
                    'loss_count': int((high_risk[profit_col] < 0).sum()),
                    'loss_rate': round((high_risk[profit_col] < 0).mean() * 100, 1),
                    'total_loss': round(abs(float(high_risk[high_risk[profit_col] < 0][profit_col].sum())), 2)
                }
            
            return {
                'success': True,
                'data': {
                    'cross_stats': self.clean_for_json(cross_stats.to_dict('records')),
                    'high_risk_orders': self.clean_for_json(high_risk.head(30).to_dict('records'))
                },
                'summary': high_risk_summary or {
                    'count': 0,
                    'loss_count': 0,
                    'loss_rate': 0,
                    'total_loss': 0
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "配送×活动交叉分析失败")
    
    # ==================== 折扣分析 ====================
    
    def analyze_discounts(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        折扣分析
        
        分析各类折扣的使用情况
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店筛选
        
        Returns:
            折扣分析数据
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
            
            # 统计各活动类型
            discount_stats = []
            total_discount = 0
            
            for activity_name, field_name in self.activity_fields.items():
                if field_name in data.columns:
                    field_total = data[field_name].fillna(0).sum()
                    field_count = (data[field_name].fillna(0) > 0).sum()
                    
                    if field_total > 0:
                        discount_stats.append({
                            '活动类型': activity_name,
                            '使用次数': int(field_count),
                            '补贴金额': round(float(field_total), 2),
                            '单均补贴': round(float(field_total / field_count), 2) if field_count > 0 else 0
                        })
                        total_discount += field_total
            
            # 按补贴金额排序
            discount_stats = sorted(discount_stats, key=lambda x: x['补贴金额'], reverse=True)
            
            # 计算占比
            for stat in discount_stats:
                stat['占比'] = round(stat['补贴金额'] / total_discount * 100, 1) if total_discount > 0 else 0
            
            return {
                'success': True,
                'data': discount_stats,
                'summary': {
                    'total_discount': round(float(total_discount), 2),
                    'total_orders': len(data),
                    'discount_orders': int(sum(s['使用次数'] for s in discount_stats)),
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "折扣分析失败")

