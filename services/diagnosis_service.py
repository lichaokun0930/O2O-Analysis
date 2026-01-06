# -*- coding: utf-8 -*-
"""
诊断分析服务（今日必做核心模块）

提供经营诊断相关的分析功能：
- 穿底订单分析（订单实际利润 < 0）
- 高配送费预警（配送费 > 6元 且 利润 < 配送费）
- 热销缺货分析
- 滞销商品分析（按状态变化点）
- 趋势分析

业务逻辑来源: components/today_must_do/diagnosis_analysis.py

两层架构:
🔴 紧急处理（今日必须完成）
  - 穿底止血：订单实际利润 < 0
  - 高配送费预警：配送费 > 6元 且 利润 < 配送费
  - 热销缺货：昨日热销品今日零销量

🟡 关注观察（本周内处理）
  - 流量异常：销量环比下跌 >30%
  - 滞销预警：按状态变化点提醒

核心公式（与主看板统一）:
  订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返

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


# 配送费阈值
DELIVERY_FEE_THRESHOLD = 6.0

# 滞销天数阈值
SLOW_MOVING_DAYS = {
    '新增滞销': 3,    # 刚满3天无销量
    '持续滞销': 7,    # 刚满7天无销量
    '严重滞销': 15,   # 刚满15天无销量
}


@dataclass
class DiagnosisSummary:
    """诊断汇总数据类"""
    overflow_orders: int        # 穿底订单数
    overflow_amount: float      # 穿底金额
    high_delivery_orders: int   # 高配送费订单数
    stockout_products: int      # 缺货商品数
    slow_moving_products: int   # 滞销商品数
    traffic_drop_products: int  # 流量下滑商品数


class DiagnosisService(BaseService):
    """
    诊断分析服务
    
    今日必做模块核心业务逻辑
    """
    
    def __init__(self, data_loader=None, cache_manager=None):
        super().__init__(cache_manager)
        self.data_loader = data_loader
        self.delivery_fee_threshold = DELIVERY_FEE_THRESHOLD
    
    # ==================== 诊断汇总 ====================
    
    def get_diagnosis_summary(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取诊断汇总数据
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店筛选
        
        Returns:
            诊断汇总数据
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
            
            # 筛选昨日数据
            date_col = self.get_date_column(data)
            data[date_col] = pd.to_datetime(data[date_col])
            yesterday_data = data[data[date_col].dt.normalize() == yesterday]
            
            # 聚合到订单级
            order_agg = self.aggregate_to_order_level(yesterday_data)
            
            # 1. 穿底订单统计
            if '订单实际利润' in order_agg.columns:
                overflow_mask = order_agg['订单实际利润'] < 0
                overflow_count = overflow_mask.sum()
                overflow_amount = abs(order_agg.loc[overflow_mask, '订单实际利润'].sum())
            else:
                overflow_count = 0
                overflow_amount = 0
            
            # 2. 高配送费订单统计
            if '物流配送费' in order_agg.columns and '订单实际利润' in order_agg.columns:
                high_delivery_mask = (
                    (order_agg['物流配送费'] > self.delivery_fee_threshold) & 
                    (order_agg['订单实际利润'] < order_agg['物流配送费'])
                )
                high_delivery_count = high_delivery_mask.sum()
            else:
                high_delivery_count = 0
            
            # 3. 其他统计（需要更多数据）
            
            summary = {
                '紧急处理': {
                    '穿底订单': {
                        'count': int(overflow_count),
                        'amount': round(float(overflow_amount), 2),
                        'icon': '🔴'
                    },
                    '高配送费': {
                        'count': int(high_delivery_count),
                        'threshold': self.delivery_fee_threshold,
                        'icon': '🔴'
                    }
                },
                '关注观察': {
                    '流量异常': {'count': 0, 'icon': '🟡'},
                    '滞销预警': {'count': 0, 'icon': '🟡'}
                }
            }
            
            return {
                'success': True,
                'data': summary,
                'date': str(yesterday.date())
            }
            
        except Exception as e:
            return self.handle_error(e, "获取诊断汇总失败")
    
    # ==================== 穿底订单分析 ====================
    
    def get_overflow_orders(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None,
        yesterday_only: bool = True
    ) -> Dict[str, Any]:
        """
        获取穿底订单列表
        
        定义：订单实际利润 < 0
        公式：订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店筛选
            yesterday_only: 是否只分析昨日数据
        
        Returns:
            穿底订单数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            date_col = self.get_date_column(data)
            if date_col:
                data[date_col] = pd.to_datetime(data[date_col])
                
                if yesterday_only:
                    yesterday = data[date_col].max().normalize()
                    data = data[data[date_col].dt.normalize() == yesterday]
            
            # 聚合到订单级
            order_agg = self.aggregate_to_order_level(data)
            
            if '订单实际利润' not in order_agg.columns:
                return {'error': '无法计算订单实际利润'}
            
            # 筛选穿底订单
            overflow_orders = order_agg[order_agg['订单实际利润'] < 0].copy()
            
            # 计算亏损金额
            overflow_orders['亏损金额'] = abs(overflow_orders['订单实际利润'])
            
            # 按亏损金额排序
            overflow_orders = overflow_orders.sort_values('亏损金额', ascending=False)
            
            # 渠道分布
            channel_dist = self.get_channel_distribution(overflow_orders)
            
            # 亏损原因分析
            reason_analysis = self._analyze_overflow_reasons(overflow_orders)
            
            return {
                'success': True,
                'data': self.clean_for_json(overflow_orders.head(100).to_dict('records')),
                'summary': {
                    'total_count': len(overflow_orders),
                    'total_loss': round(float(overflow_orders['亏损金额'].sum()), 2),
                    'avg_loss': round(float(overflow_orders['亏损金额'].mean()), 2) if len(overflow_orders) > 0 else 0,
                    'channel_distribution': channel_dist,
                    'reason_analysis': reason_analysis
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "获取穿底订单失败")
    
    def _analyze_overflow_reasons(self, overflow_orders: pd.DataFrame) -> Dict[str, int]:
        """分析穿底原因"""
        reasons = {
            '高配送费': 0,
            '高平台服务费': 0,
            '低毛利': 0,
            '活动补贴过大': 0,
        }
        
        if overflow_orders.empty:
            return reasons
        
        for _, order in overflow_orders.iterrows():
            delivery_fee = order.get('物流配送费', 0) or 0
            service_fee = order.get('平台服务费', 0) or 0
            profit = order.get('利润额', 0) or 0
            
            # 判断主要原因
            if delivery_fee > self.delivery_fee_threshold:
                reasons['高配送费'] += 1
            if service_fee > profit * 0.3:  # 服务费占毛利30%以上
                reasons['高平台服务费'] += 1
            if profit < 0:
                reasons['低毛利'] += 1
        
        return reasons
    
    # ==================== 高配送费预警 ====================
    
    def get_high_delivery_orders(
        self,
        df: pd.DataFrame,
        threshold: float = DELIVERY_FEE_THRESHOLD,
        store_name: Optional[str] = None,
        yesterday_only: bool = True
    ) -> Dict[str, Any]:
        """
        获取高配送费订单
        
        定义：配送费 > threshold 且 订单毛利 < 配送费
        
        Args:
            df: 订单数据DataFrame
            threshold: 配送费阈值（默认6元）
            store_name: 门店筛选
            yesterday_only: 是否只分析昨日数据
        
        Returns:
            高配送费订单数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            date_col = self.get_date_column(data)
            if date_col:
                data[date_col] = pd.to_datetime(data[date_col])
                
                if yesterday_only:
                    yesterday = data[date_col].max().normalize()
                    data = data[data[date_col].dt.normalize() == yesterday]
            
            # 聚合到订单级
            order_agg = self.aggregate_to_order_level(data)
            
            if '物流配送费' not in order_agg.columns:
                return {'error': '缺少配送费字段'}
            
            # 筛选高配送费订单
            # 条件：配送费 > threshold 且 利润 < 配送费（无法覆盖配送成本）
            profit_col = '订单实际利润' if '订单实际利润' in order_agg.columns else '利润额'
            
            if profit_col not in order_agg.columns:
                return {'error': '缺少利润字段'}
            
            high_delivery = order_agg[
                (order_agg['物流配送费'] > threshold) & 
                (order_agg[profit_col] < order_agg['物流配送费'])
            ].copy()
            
            # 计算配送费占比
            if '实收价格' in high_delivery.columns:
                high_delivery['配送费占比'] = (high_delivery['物流配送费'] / high_delivery['实收价格'] * 100).round(2)
            
            # 按配送费排序
            high_delivery = high_delivery.sort_values('物流配送费', ascending=False)
            
            return {
                'success': True,
                'data': self.clean_for_json(high_delivery.head(100).to_dict('records')),
                'summary': {
                    'total_count': len(high_delivery),
                    'total_delivery_fee': round(float(high_delivery['物流配送费'].sum()), 2),
                    'avg_delivery_fee': round(float(high_delivery['物流配送费'].mean()), 2) if len(high_delivery) > 0 else 0,
                    'threshold': threshold
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "获取高配送费订单失败")
    
    # ==================== 滞销商品分析 ====================
    
    def get_slow_moving_products(
        self,
        df: pd.DataFrame,
        days: int = 7,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取滞销商品
        
        定义：有库存但连续N天无销量
        注意：只在状态变化点提醒，避免每天重复
        
        Args:
            df: 订单数据DataFrame
            days: 滞销天数阈值
            store_name: 门店筛选
        
        Returns:
            滞销商品数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            date_col = self.get_date_column(data)
            if date_col is None:
                return {'error': '缺少日期字段'}
            
            data[date_col] = pd.to_datetime(data[date_col])
            yesterday = data[date_col].max().normalize()
            
            # 获取商品列表
            group_key = self.get_product_group_key(data)
            sales_col = self.get_sales_column(data)
            
            # 计算每个商品的最后销售日期
            product_last_sale = data.groupby(group_key).agg({
                '商品名称': 'first',
                date_col: 'max',
                sales_col: 'sum' if sales_col in data.columns else lambda x: 0,
            }).reset_index()
            
            product_last_sale.columns = [group_key, '商品名称', '最后销售日期', '总销量'][:len(product_last_sale.columns)]
            
            # 计算无销量天数
            product_last_sale['无销量天数'] = (yesterday - product_last_sale['最后销售日期']).dt.days
            
            # 分类滞销级别
            def classify_slow_moving(days_no_sale):
                if days_no_sale >= SLOW_MOVING_DAYS['严重滞销']:
                    return '严重滞销'
                elif days_no_sale >= SLOW_MOVING_DAYS['持续滞销']:
                    return '持续滞销'
                elif days_no_sale >= SLOW_MOVING_DAYS['新增滞销']:
                    return '新增滞销'
                else:
                    return '正常'
            
            product_last_sale['滞销级别'] = product_last_sale['无销量天数'].apply(classify_slow_moving)
            
            # 筛选滞销商品
            slow_moving = product_last_sale[product_last_sale['滞销级别'] != '正常'].copy()
            slow_moving = slow_moving.sort_values('无销量天数', ascending=False)
            
            # 按级别统计
            level_counts = slow_moving['滞销级别'].value_counts().to_dict()
            
            return {
                'success': True,
                'data': self.clean_for_json(slow_moving.to_dict('records')),
                'summary': {
                    'total_count': len(slow_moving),
                    'level_counts': level_counts,
                    'thresholds': SLOW_MOVING_DAYS
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "获取滞销商品失败")
    
    # ==================== 趋势分析辅助方法 ====================
    
    def calculate_trend_indicator(
        self,
        yesterday_value: float,
        avg_3d_value: float
    ) -> Dict[str, Any]:
        """
        计算趋势指示器（昨日 vs 3日均值）
        
        Args:
            yesterday_value: 昨日值
            avg_3d_value: 3日均值
        
        Returns:
            趋势指标字典
        """
        result = {
            'trend': 'stable',
            'icon': '→',
            'label': '持平',
            'color': 'gray',
            'change_pct': 0,
            'avg_3d': round(avg_3d_value, 1),
            'description': ''
        }
        
        if avg_3d_value <= 0:
            if yesterday_value > 0:
                result['trend'] = 'up'
                result['icon'] = '⚠️'
                result['label'] = '新增'
                result['color'] = 'orange'
                result['description'] = f'近3日均0，昨日新增{yesterday_value:.0f}'
            return result
        
        change_pct = (yesterday_value - avg_3d_value) / avg_3d_value * 100
        result['change_pct'] = round(change_pct, 1)
        
        # 判断趋势（对于负面指标：增加=恶化，减少=好转）
        if change_pct > 30:
            result['trend'] = 'up'
            result['icon'] = '↑'
            result['label'] = '恶化'
            result['color'] = 'red'
            result['description'] = f'较3日均({avg_3d_value:.0f})↑{change_pct:.0f}%'
        elif change_pct < -30:
            result['trend'] = 'down'
            result['icon'] = '↓'
            result['label'] = '好转'
            result['color'] = 'green'
            result['description'] = f'较3日均({avg_3d_value:.0f})↓{abs(change_pct):.0f}%'
        else:
            result['trend'] = 'stable'
            result['icon'] = '→'
            result['label'] = '持平'
            result['color'] = 'gray'
            result['description'] = f'与3日均({avg_3d_value:.0f})持平'
        
        return result
    
    # ==================== 批量趋势计算（性能优化）====================
    
    def calculate_daily_overflow_batch(
        self,
        df: pd.DataFrame,
        days: int = 3
    ) -> Dict[str, int]:
        """
        批量计算多天的穿底订单数（性能优化版）
        
        优化前：循环3次，每次筛选和聚合，耗时20-30秒
        优化后：一次性筛选和分组聚合，耗时2-3秒
        
        Args:
            df: 原始数据
            days: 查询天数（默认3天）
        
        Returns:
            {date: overflow_count} 每天的穿底订单数
        """
        if '订单ID' not in df.columns:
            return {}
        
        date_col = self.get_date_column(df)
        if date_col is None:
            return {}
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        yesterday = df[date_col].max().normalize()
        
        # 一次性筛选前N天的数据
        start_date = yesterday - timedelta(days=days)
        recent_df = df[df[date_col].dt.normalize() >= start_date].copy()
        
        if recent_df.empty:
            return {}
        
        # 准备聚合字段
        sales_field = self.get_sales_column(recent_df)
        if '实收价格' in recent_df.columns and sales_field in recent_df.columns:
            recent_df['_实收价格_销量'] = recent_df['实收价格'].fillna(0) * recent_df[sales_field].fillna(1)
        
        # 构建聚合字典
        agg_dict = {'日期': (date_col, 'first')}
        
        for field in self.ITEM_LEVEL_FIELDS:
            if field in recent_df.columns:
                agg_dict[field] = (field, 'sum')
        
        for field in self.ORDER_LEVEL_FIELDS:
            if field in recent_df.columns and field not in agg_dict:
                agg_dict[field] = (field, 'first')
        
        # 一次性聚合所有订单
        order_agg = recent_df.groupby('订单ID').agg(**agg_dict).reset_index()
        
        # 计算订单实际利润
        order_agg['订单实际利润'] = self.calculate_order_profit(order_agg)
        
        # 按日期分组统计穿底订单
        order_agg['日期'] = pd.to_datetime(order_agg['日期']).dt.normalize()
        order_agg['是否穿底'] = order_agg['订单实际利润'] < 0
        
        daily_overflow = order_agg.groupby('日期')['是否穿底'].sum().to_dict()
        
        return {str(k.date()): int(v) for k, v in daily_overflow.items()}

