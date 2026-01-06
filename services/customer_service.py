# -*- coding: utf-8 -*-
"""
客户流失分析服务

提供客户流失相关的分析功能：
- 客户识别（基于收货地址）
- 流失状态判断（高危/预警）
- 流失原因分析（缺货/涨价/下架）
- 精准召回建议

业务逻辑来源: components/today_must_do/customer_churn_analyzer.py

定义:
- 流失客户 = 过去30天内下单≥2次，但7天未下单

性能优化:
- 支持Redis缓存
- 算法向量化优化

版本: v1.0
创建日期: 2026-01-05
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta

from .base_service import BaseService
from .cache.cache_keys import CacheKeys


class CustomerService(BaseService):
    """
    客户流失分析服务
    
    基于收货地址识别客户，分析流失风险
    """
    
    def __init__(self, data_loader=None, cache_manager=None):
        super().__init__(cache_manager)
        self.data_loader = data_loader
    
    # ==================== 地址标准化 ====================
    
    @staticmethod
    def standardize_address(addr: str) -> Optional[str]:
        """
        标准化收货地址
        
        处理逻辑:
        - 去除空格
        - 统一楼层格式（单元→-、栋→-）
        - 保留核心识别信息
        
        Args:
            addr: 原始收货地址
        
        Returns:
            标准化后的地址
        """
        if pd.isna(addr):
            return None
        
        addr = str(addr).replace(' ', '')
        addr = addr.replace('单元', '-').replace('栋', '-')
        
        return addr
    
    # ==================== 流失客户识别 ====================
    
    def identify_churn_customers(
        self,
        df: pd.DataFrame,
        today: Optional[datetime] = None,
        lookback_days: int = 30,
        min_orders: int = 2,
        no_order_days: int = 7
    ) -> Dict[str, Any]:
        """
        识别流失客户
        
        定义:
        - 流失客户 = 过去{lookback_days}天内下单≥{min_orders}次，但{no_order_days}天未下单
        
        Args:
            df: 订单DataFrame
            today: 当前日期（默认为数据最后日期）
            lookback_days: 回溯天数（默认30天）
            min_orders: 最小订单数（默认2次）
            no_order_days: 未下单天数阈值（默认7天）
        
        Returns:
            流失客户分析数据
        """
        try:
            if df is None or df.empty:
                return {'error': '无订单数据'}
            
            data = df.copy()
            
            # 获取日期列
            date_col = self.get_date_column(data)
            if date_col is None:
                return {'error': '缺少日期字段'}
            
            data[date_col] = pd.to_datetime(data[date_col])
            
            # 设置基准日期
            if today is None:
                today = data[date_col].max()
            
            # 获取地址列
            addr_col = None
            for col in ['收货地址', '地址', 'address', 'delivery_address']:
                if col in data.columns:
                    addr_col = col
                    break
            
            if addr_col is None:
                return {'error': '缺少收货地址字段'}
            
            # 标准化地址
            data['标准地址'] = data[addr_col].apply(self.standardize_address)
            data = data[data['标准地址'].notna()]
            
            if data.empty:
                return {'error': '有效地址数据为空'}
            
            # 筛选回溯期内的数据
            start_date = today - timedelta(days=lookback_days)
            lookback_data = data[data[date_col] >= start_date]
            
            # 按客户（地址）聚合
            customer_stats = lookback_data.groupby('标准地址').agg({
                '订单ID': 'nunique' if '订单ID' in lookback_data.columns else 'count',
                date_col: ['max', 'min'],
                '实收价格': 'sum' if '实收价格' in lookback_data.columns else lambda x: 0,
            }).reset_index()
            
            customer_stats.columns = ['customer_id', 'order_count', 'last_order_date', 'first_order_date', 'total_amount']
            
            # 计算距今天数
            customer_stats['days_since_last'] = (today - customer_stats['last_order_date']).dt.days
            
            # 计算平均客单价
            customer_stats['avg_order_value'] = (
                customer_stats['total_amount'] / customer_stats['order_count']
            ).round(2)
            
            # 识别流失客户
            churn_mask = (
                (customer_stats['order_count'] >= min_orders) &
                (customer_stats['days_since_last'] >= no_order_days)
            )
            churn_customers = customer_stats[churn_mask].copy()
            
            # 分类流失风险
            def classify_churn_risk(days):
                if days >= 14:
                    return '高危流失'
                elif days >= 7:
                    return '流失预警'
                else:
                    return '正常'
            
            churn_customers['风险等级'] = churn_customers['days_since_last'].apply(classify_churn_risk)
            
            # 按距今天数排序
            churn_customers = churn_customers.sort_values('days_since_last', ascending=False)
            
            # 风险等级统计
            risk_counts = churn_customers['风险等级'].value_counts().to_dict()
            
            return {
                'success': True,
                'data': self.clean_for_json(churn_customers.head(100).to_dict('records')),
                'summary': {
                    'total_customers': len(customer_stats),
                    'churn_count': len(churn_customers),
                    'churn_rate': round(len(churn_customers) / len(customer_stats) * 100, 1) if len(customer_stats) > 0 else 0,
                    'risk_counts': risk_counts,
                    'avg_days_since_last': round(float(churn_customers['days_since_last'].mean()), 1) if len(churn_customers) > 0 else 0,
                    'total_ltv_at_risk': round(float(churn_customers['total_amount'].sum()), 2),
                    'parameters': {
                        'lookback_days': lookback_days,
                        'min_orders': min_orders,
                        'no_order_days': no_order_days
                    }
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "客户流失分析失败")
    
    # ==================== 流失原因分析 ====================
    
    def analyze_churn_reasons(
        self,
        df: pd.DataFrame,
        churn_customers: pd.DataFrame,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析流失原因
        
        可能原因：
        - 缺货：常购商品近期无库存
        - 涨价：常购商品价格上涨
        - 下架：常购商品已下架
        
        Args:
            df: 订单数据DataFrame
            churn_customers: 流失客户DataFrame
            store_name: 门店筛选
        
        Returns:
            流失原因分析数据
        """
        try:
            if df is None or df.empty or churn_customers is None or churn_customers.empty:
                return {'error': '数据不足'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 获取日期和地址列
            date_col = self.get_date_column(data)
            if date_col is None:
                return {'error': '缺少日期字段'}
            
            data[date_col] = pd.to_datetime(data[date_col])
            
            # 标准化地址
            addr_col = None
            for col in ['收货地址', '地址', 'address']:
                if col in data.columns:
                    addr_col = col
                    break
            
            if addr_col is None:
                return {'error': '缺少地址字段'}
            
            data['标准地址'] = data[addr_col].apply(self.standardize_address)
            
            # 获取流失客户的历史购买记录
            churn_ids = set(churn_customers['customer_id'].tolist())
            churn_history = data[data['标准地址'].isin(churn_ids)]
            
            if churn_history.empty:
                return {'error': '无流失客户历史记录'}
            
            # 分析常购商品
            if '商品名称' not in churn_history.columns:
                return {'error': '缺少商品名称字段'}
            
            # 获取流失客户的TOP购买商品
            top_products = churn_history.groupby('商品名称').agg({
                '标准地址': 'nunique',  # 购买客户数
                '订单ID': 'count' if '订单ID' in churn_history.columns else lambda x: len(x),  # 购买次数
            }).reset_index()
            top_products.columns = ['商品名称', '购买客户数', '购买次数']
            top_products = top_products.sort_values('购买客户数', ascending=False).head(20)
            
            # TODO: 对接库存数据分析缺货原因
            # TODO: 对接价格数据分析涨价原因
            # TODO: 对接商品状态分析下架原因
            
            return {
                'success': True,
                'data': {
                    'top_products': self.clean_for_json(top_products.to_dict('records')),
                    # 占位：后续对接更多数据源
                    'stockout_products': [],
                    'price_increase_products': [],
                    'discontinued_products': []
                },
                'summary': {
                    'analyzed_customers': len(churn_ids),
                    'analyzed_orders': len(churn_history)
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "流失原因分析失败")
    
    # ==================== 召回建议 ====================
    
    def generate_recall_suggestions(
        self,
        churn_customers: pd.DataFrame,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        生成召回建议
        
        基于LTV和流失天数优先级排序
        
        Args:
            churn_customers: 流失客户DataFrame
            top_n: 优先召回数量
        
        Returns:
            召回建议数据
        """
        try:
            if churn_customers is None or churn_customers.empty:
                return {'error': '无流失客户数据'}
            
            customers = churn_customers.copy()
            
            # 计算召回优先级分数
            # 综合考虑：LTV高 + 流失天数短（刚流失更容易召回）
            if 'total_amount' in customers.columns and 'days_since_last' in customers.columns:
                # 标准化LTV（0-1）
                ltv_max = customers['total_amount'].max()
                ltv_min = customers['total_amount'].min()
                if ltv_max > ltv_min:
                    customers['ltv_score'] = (customers['total_amount'] - ltv_min) / (ltv_max - ltv_min)
                else:
                    customers['ltv_score'] = 1
                
                # 流失天数越短越好（反向）
                days_max = customers['days_since_last'].max()
                days_min = customers['days_since_last'].min()
                if days_max > days_min:
                    customers['recency_score'] = 1 - (customers['days_since_last'] - days_min) / (days_max - days_min)
                else:
                    customers['recency_score'] = 1
                
                # 综合分数（LTV权重60%，近期权重40%）
                customers['priority_score'] = (
                    customers['ltv_score'] * 0.6 +
                    customers['recency_score'] * 0.4
                ).round(2)
            else:
                customers['priority_score'] = 1
            
            # 按优先级排序
            priority_list = customers.sort_values('priority_score', ascending=False).head(top_n)
            
            # 生成召回建议
            suggestions = []
            for _, row in priority_list.iterrows():
                suggestion = {
                    'customer_id': row.get('customer_id', '未知'),
                    'priority_score': float(row.get('priority_score', 0)),
                    'days_since_last': int(row.get('days_since_last', 0)),
                    'total_amount': float(row.get('total_amount', 0)),
                    'order_count': int(row.get('order_count', 0)),
                    'risk_level': row.get('风险等级', '未知'),
                    'suggested_action': self._get_recall_action(row)
                }
                suggestions.append(suggestion)
            
            return {
                'success': True,
                'data': suggestions,
                'summary': {
                    'total_priority': len(priority_list),
                    'high_risk_count': int((priority_list.get('风险等级', pd.Series()) == '高危流失').sum()),
                    'total_ltv_at_risk': round(float(priority_list['total_amount'].sum()), 2) if 'total_amount' in priority_list.columns else 0
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "生成召回建议失败")
    
    def _get_recall_action(self, customer_row: pd.Series) -> str:
        """根据客户情况生成召回建议"""
        days = customer_row.get('days_since_last', 0)
        ltv = customer_row.get('total_amount', 0)
        
        if days >= 14 and ltv >= 500:
            return "高价值高风险客户，建议电话回访+专属优惠券"
        elif days >= 14:
            return "高风险客户，建议发送专属优惠券召回"
        elif days >= 7 and ltv >= 300:
            return "中价值预警客户，建议推送个性化推荐"
        else:
            return "建议发送关怀短信+小额优惠"
    
    # ==================== 客单价异常分析 ====================
    
    def analyze_aov_anomaly(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        客单价异常分析
        
        检测客单价异常波动
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店筛选
        
        Returns:
            客单价异常分析数据
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
            
            if '实收价格' not in data.columns:
                return {'error': '缺少实收价格字段'}
            
            # 获取日期
            date_col = self.get_date_column(data)
            if date_col:
                data[date_col] = pd.to_datetime(data[date_col])
            
            # 计算整体统计
            overall_aov = data['实收价格'].mean()
            overall_std = data['实收价格'].std()
            
            # 定义异常阈值（均值±2倍标准差）
            upper_threshold = overall_aov + 2 * overall_std
            lower_threshold = max(0, overall_aov - 2 * overall_std)
            
            # 标记异常订单
            data['客单价异常'] = (
                (data['实收价格'] > upper_threshold) |
                (data['实收价格'] < lower_threshold)
            )
            
            # 异常类型
            data.loc[data['实收价格'] > upper_threshold, '异常类型'] = '异常高'
            data.loc[data['实收价格'] < lower_threshold, '异常类型'] = '异常低'
            
            abnormal_orders = data[data['客单价异常']].copy()
            
            # 按日期统计异常趋势
            daily_anomaly = None
            if date_col:
                daily_anomaly = data.groupby(data[date_col].dt.date).agg({
                    '实收价格': 'mean',
                    '客单价异常': 'sum',
                    '订单ID': 'count' if '订单ID' in data.columns else lambda x: len(x)
                }).reset_index()
                daily_anomaly.columns = ['日期', '平均客单价', '异常订单数', '总订单数']
                daily_anomaly['异常率'] = (daily_anomaly['异常订单数'] / daily_anomaly['总订单数'] * 100).round(1)
            
            return {
                'success': True,
                'data': {
                    'abnormal_orders': self.clean_for_json(abnormal_orders.head(50).to_dict('records')),
                    'daily_trend': self.clean_for_json(daily_anomaly.to_dict('records')) if daily_anomaly is not None else []
                },
                'summary': {
                    'overall_aov': round(float(overall_aov), 2),
                    'overall_std': round(float(overall_std), 2),
                    'upper_threshold': round(float(upper_threshold), 2),
                    'lower_threshold': round(float(lower_threshold), 2),
                    'total_orders': len(data),
                    'abnormal_count': len(abnormal_orders),
                    'abnormal_rate': round(len(abnormal_orders) / len(data) * 100, 1) if len(data) > 0 else 0
                }
            }
            
        except Exception as e:
            return self.handle_error(e, "客单价异常分析失败")

