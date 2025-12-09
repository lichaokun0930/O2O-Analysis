# -*- coding: utf-8 -*-
"""
智能调价计算器 - 定价引擎

核心功能：
1. 价格弹性系数计算
2. 销量/利润预测
3. 智能定价建议
4. 调价方案生成与导出
5. 弹性系数学习机制（从实际调价效果反推）

Author: AI Assistant
Date: 2025-11-28
Updated: 2025-12-04 - 添加弹性系数学习机制
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import io
import json
import os

# ==================== 弹性系数学习存储 ====================
# 存储学习到的弹性系数，格式：{店内码: {渠道: {'elasticity': float, 'samples': int, 'last_update': str}}}
LEARNED_ELASTICITY_FILE = os.path.join(os.path.dirname(__file__), 'learned_elasticity.json')
LEARNED_ELASTICITY: Dict[str, Dict[str, dict]] = {}

def load_learned_elasticity():
    """加载已学习的弹性系数"""
    global LEARNED_ELASTICITY
    try:
        if os.path.exists(LEARNED_ELASTICITY_FILE):
            with open(LEARNED_ELASTICITY_FILE, 'r', encoding='utf-8') as f:
                LEARNED_ELASTICITY = json.load(f)
                print(f"✅ 已加载 {sum(len(v) for v in LEARNED_ELASTICITY.values())} 条学习弹性系数")
    except Exception as e:
        print(f"⚠️ 加载弹性系数失败: {e}")
        LEARNED_ELASTICITY = {}

def save_learned_elasticity():
    """保存学习到的弹性系数"""
    try:
        with open(LEARNED_ELASTICITY_FILE, 'w', encoding='utf-8') as f:
            json.dump(LEARNED_ELASTICITY, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存弹性系数失败: {e}")

def learn_elasticity_from_price_change(
    product_code: str,
    channel: str,
    old_price: float,
    new_price: float,
    old_daily_sales: float,
    new_daily_sales: float,
    days_after_change: int = 7
) -> Optional[float]:
    """
    从实际调价效果学习弹性系数
    
    公式：弹性系数 = (销量变化率) / (价格变化率)
    
    Args:
        product_code: 店内码
        channel: 渠道
        old_price: 调价前价格
        new_price: 调价后价格
        old_daily_sales: 调价前日均销量
        new_daily_sales: 调价后日均销量
        days_after_change: 调价后观察天数（用于判断数据可靠性）
    
    Returns:
        计算得到的弹性系数，无效时返回None
    """
    global LEARNED_ELASTICITY
    
    # 数据有效性检查
    if old_price <= 0 or new_price <= 0:
        return None
    if old_daily_sales <= 0:  # 调价前必须有销量
        return None
    if abs(new_price - old_price) / old_price < 0.02:  # 价格变化太小（<2%），不可靠
        return None
    
    # 计算弹性系数
    price_change_rate = (new_price - old_price) / old_price
    sales_change_rate = (new_daily_sales - old_daily_sales) / old_daily_sales if old_daily_sales > 0 else 0
    
    # 弹性 = 销量变化率 / 价格变化率
    if abs(price_change_rate) < 0.01:
        return None
    
    elasticity = sales_change_rate / price_change_rate
    
    # 合理性检查：
    # - 正常弹性为负数（涨价→销量降，降价→销量涨）
    # - 刚需品可能有小的正弹性（涨价销量基本不变或微涨）
    # - 异常情况：弹性绝对值过大（>5），可能有其他因素影响
    if elasticity > 1.0:  # 涨价反而大幅增销量，可能有其他因素（如促销活动）
        return None
    if elasticity < -5:  # 弹性过大，不可靠
        return None
    
    # 存储学习结果（使用加权平均）
    if product_code not in LEARNED_ELASTICITY:
        LEARNED_ELASTICITY[product_code] = {}
    
    if channel not in LEARNED_ELASTICITY[product_code]:
        LEARNED_ELASTICITY[product_code][channel] = {
            'elasticity': elasticity,
            'samples': 1,
            'last_update': datetime.now().strftime('%Y-%m-%d')
        }
    else:
        # 加权平均：新样本权重 = 1 / (samples + 1)
        old_data = LEARNED_ELASTICITY[product_code][channel]
        old_elasticity = old_data['elasticity']
        samples = old_data['samples']
        
        # 新弹性 = (旧弹性 × 旧样本数 + 新弹性) / (旧样本数 + 1)
        new_elasticity = (old_elasticity * samples + elasticity) / (samples + 1)
        
        LEARNED_ELASTICITY[product_code][channel] = {
            'elasticity': round(new_elasticity, 3),
            'samples': samples + 1,
            'last_update': datetime.now().strftime('%Y-%m-%d')
        }
    
    # 保存到文件
    save_learned_elasticity()
    
    return elasticity

def get_learned_elasticity(product_code: str, channel: str) -> Optional[Tuple[float, int]]:
    """
    获取学习到的弹性系数
    
    Returns:
        (弹性系数, 样本数) 或 None
    """
    if product_code in LEARNED_ELASTICITY:
        if channel in LEARNED_ELASTICITY[product_code]:
            data = LEARNED_ELASTICITY[product_code][channel]
            return (data['elasticity'], data['samples'])
        # 尝试其他渠道的数据
        for ch, data in LEARNED_ELASTICITY[product_code].items():
            if data['samples'] >= 2:  # 至少2个样本才使用跨渠道数据
                return (data['elasticity'], data['samples'])
    return None

# 初始化时加载已学习的弹性系数
load_learned_elasticity()

# ==================== 品类默认弹性系数 ====================

CATEGORY_ELASTICITY = {
    # 一级分类 → 默认弹性系数（负数表示涨价导致销量下降）
    '饮料': -1.2,       # 较敏感，可替代性强
    '酒水': -0.8,       # 品牌忠诚度高
    '零食': -1.0,       # 中等敏感
    '休闲食品': -1.0,   # 中等敏感
    '生鲜': -1.5,       # 高敏感，时效性强
    '水果': -1.4,       # 高敏感
    '蔬菜': -1.3,       # 高敏感
    '日用品': -0.6,     # 刚需，敏感度低
    '日化': -0.6,       # 刚需
    '粮油调味': -0.5,   # 刚需，敏感度最低
    '粮油': -0.5,
    '调味品': -0.5,
    '乳品烘焙': -0.9,   # 中等偏低
    '乳制品': -0.9,
    '烘焙': -0.9,
    '个护清洁': -0.7,   # 品牌忠诚度较高
    '个人护理': -0.7,
    '清洁用品': -0.7,
    '母婴': -0.4,       # 刚需，品牌忠诚度极高
    '宠物': -0.5,       # 刚需
    '冷冻冷藏': -1.1,   # 较敏感
    '速食': -0.9,       # 中等
    '方便食品': -0.9,
    '耗材': -0.3,       # 必需品，极低敏感
}

# 默认弹性系数（当无法匹配分类时使用）
DEFAULT_ELASTICITY = -1.0

# 渠道敏感度修正系数
CHANNEL_SENSITIVITY = {
    '美团闪购': 1.1,     # 用户对价格较敏感
    '美团': 1.1,
    '饿了么': 1.0,       # 中等
    '京东到家': 0.9,     # 用户对价格敏感度略低
    '京东': 0.9,
    '闪购小程序': 0.8,   # 私域流量，敏感度低
    '小程序': 0.8,
}


# ==================== 弹性系数计算 ====================

def get_product_elasticity(
    product_code: str,
    channel: str,
    category: str,
    price_changes_df: pd.DataFrame = None
) -> Tuple[float, str]:
    """
    获取商品的价格弹性系数
    
    优先级：
    1. 该商品在该渠道的历史弹性（需至少3次有效调价）
    2. 该商品跨渠道平均弹性
    3. 同一级分类默认弹性
    4. 全局默认值
    
    Args:
        product_code: 店内码
        channel: 渠道
        category: 一级分类
        price_changes_df: 价格变动历史数据
    
    Returns:
        (弹性系数, 来源说明)
    """
    
    # 0. 【优先】尝试从学习数据获取该商品弹性
    learned = get_learned_elasticity(product_code, channel)
    if learned is not None:
        elasticity, samples = learned
        if samples >= 2:  # 至少2次调价样本
            return (elasticity, f"学习数据（{samples}次调价）")
    
    # 1. 尝试从历史数据获取该商品弹性
    if price_changes_df is not None and not price_changes_df.empty:
        # 该商品+该渠道的调价记录
        product_channel_data = price_changes_df[
            (price_changes_df['店内码'] == product_code) & 
            (price_changes_df['渠道'] == channel)
        ]
        
        if len(product_channel_data) >= 3:
            # 有足够数据，计算历史弹性均值
            valid_data = product_channel_data[product_channel_data['弹性'].notna()]
            if len(valid_data) >= 3:
                elasticity = valid_data['弹性'].mean()
                return (round(elasticity, 2), f"历史数据（{len(valid_data)}次调价）")
        
        # 2. 该商品跨渠道
        product_data = price_changes_df[price_changes_df['店内码'] == product_code]
        if len(product_data) >= 3:
            valid_data = product_data[product_data['弹性'].notna()]
            if len(valid_data) >= 3:
                elasticity = valid_data['弹性'].mean()
                return (round(elasticity, 2), f"跨渠道历史（{len(valid_data)}次）")
    
    # 3. 品类默认弹性
    if category:
        # 尝试精确匹配
        if category in CATEGORY_ELASTICITY:
            elasticity = CATEGORY_ELASTICITY[category]
            return (elasticity, f"品类默认（{category}）⚠️")
        
        # 尝试模糊匹配
        for cat_name, cat_elasticity in CATEGORY_ELASTICITY.items():
            if cat_name in category or category in cat_name:
                return (cat_elasticity, f"品类参考（{cat_name}）⚠️")
    
    # 4. 全局默认
    return (DEFAULT_ELASTICITY, "默认值⚠️")


def get_channel_factor(channel: str) -> float:
    """获取渠道敏感度修正系数"""
    if channel:
        for ch_name, factor in CHANNEL_SENSITIVITY.items():
            if ch_name in channel or channel in ch_name:
                return factor
    return 1.0


# ==================== 销量/利润预测 ====================

def predict_sales_change(
    current_price: float,
    new_price: float,
    elasticity: float,
    channel: str = None,
    inventory_days: float = None
) -> Dict[str, float]:
    """
    预测调价后的销量变化
    
    公式：销量变化率 = 价格变化率 × 弹性系数 × 渠道修正 × 库存修正
    
    Args:
        current_price: 当前价格
        new_price: 新价格
        elasticity: 弹性系数
        channel: 渠道（用于修正）
        inventory_days: 库存可售天数（用于修正）
    
    Returns:
        {
            'price_change_rate': 价格变化率%,
            'qty_change_rate': 销量变化率%,
            'channel_factor': 渠道修正系数,
            'inventory_factor': 库存修正系数
        }
    """
    if current_price <= 0:
        return {'price_change_rate': 0, 'qty_change_rate': 0, 'channel_factor': 1, 'inventory_factor': 1}
    
    # 价格变化率
    price_change_rate = (new_price - current_price) / current_price * 100
    
    # 渠道修正
    channel_factor = get_channel_factor(channel) if channel else 1.0
    
    # 库存修正（库存积压时降价效果更好，涨价风险更大）
    inventory_factor = 1.0
    if inventory_days is not None:
        if inventory_days > 30:  # 库存积压
            if price_change_rate < 0:  # 降价
                inventory_factor = 1.1  # 降价效果增强
            else:  # 涨价
                inventory_factor = 1.2  # 涨价风险增大
        elif inventory_days < 7:  # 库存紧张
            if price_change_rate > 0:  # 涨价
                inventory_factor = 0.8  # 涨价风险降低（供不应求）
    
    # 最终销量变化预测
    qty_change_rate = price_change_rate * elasticity * channel_factor * inventory_factor / 100 * 100
    
    return {
        'price_change_rate': round(price_change_rate, 1),
        'qty_change_rate': round(qty_change_rate, 1),
        'channel_factor': channel_factor,
        'inventory_factor': inventory_factor
    }


def predict_profit_change(
    current_price: float,
    new_price: float,
    cost: float,
    current_qty: float,
    elasticity: float,
    channel: str = None
) -> Dict[str, Any]:
    """
    预测调价后的利润变化
    
    Args:
        current_price: 当前价格
        new_price: 新价格
        cost: 成本
        current_qty: 当前日均销量
        elasticity: 弹性系数
        channel: 渠道
    
    Returns:
        完整的预测结果
    """
    if current_price <= 0 or cost <= 0:
        return None
    
    # 获取销量变化预测
    sales_prediction = predict_sales_change(current_price, new_price, elasticity, channel)
    qty_change_rate = sales_prediction['qty_change_rate'] / 100
    
    # 预测新销量
    new_qty = current_qty * (1 + qty_change_rate)
    new_qty = max(0, new_qty)  # 销量不能为负
    
    # 当前指标
    current_revenue = current_price * current_qty
    current_profit = (current_price - cost) * current_qty
    current_margin = (current_price - cost) / current_price * 100 if current_price > 0 else 0
    
    # 预测指标
    new_revenue = new_price * new_qty
    new_profit = (new_price - cost) * new_qty
    new_margin = (new_price - cost) / new_price * 100 if new_price > 0 else 0
    
    # 变化率
    revenue_change = (new_revenue - current_revenue) / current_revenue * 100 if current_revenue > 0 else 0
    profit_change = (new_profit - current_profit) / abs(current_profit) * 100 if current_profit != 0 else (100 if new_profit > 0 else 0)
    margin_change = new_margin - current_margin  # 百分点变化
    
    return {
        # 当前状态
        'current_price': round(current_price, 2),
        'current_qty': round(current_qty, 1),
        'current_revenue': round(current_revenue, 2),
        'current_profit': round(current_profit, 2),
        'current_margin': round(current_margin, 1),
        
        # 新状态预测
        'new_price': round(new_price, 2),
        'new_qty': round(new_qty, 1),
        'new_revenue': round(new_revenue, 2),
        'new_profit': round(new_profit, 2),
        'new_margin': round(new_margin, 1),
        
        # 变化
        'price_change_rate': sales_prediction['price_change_rate'],
        'qty_change_rate': round(qty_change_rate * 100, 1),
        'revenue_change_rate': round(revenue_change, 1),
        'profit_change_rate': round(profit_change, 1),
        'margin_change': round(margin_change, 1),
        
        # 弹性信息
        'elasticity': elasticity,
    }


# ==================== 智能定价建议 ====================

def find_optimal_price(
    current_price: float,
    cost: float,
    current_qty: float,
    elasticity: float,
    channel: str = None,
    max_price_increase: float = 0.30,  # 最大涨价幅度30%
    step: float = 0.01  # 步进1%
) -> Dict[str, Any]:
    """
    寻找利润最大化的最优价格点
    
    原理：遍历不同涨价幅度，找到 (价格-成本) × 预估销量 最大的点
    
    Args:
        current_price: 当前价格
        cost: 成本
        current_qty: 当前日均销量
        elasticity: 弹性系数
        channel: 渠道
        max_price_increase: 最大涨价幅度（默认30%）
        step: 步进幅度（默认1%）
    
    Returns:
        {
            'optimal_price': 最优价格,
            'optimal_increase': 最优涨价幅度,
            'max_profit': 最大预估利润,
            'profit_curve': 利润曲线数据,
            'warning_threshold': 警告阈值（超过此涨幅可能亏损）
        }
    """
    if current_price <= 0 or cost <= 0 or current_qty <= 0:
        return None
    
    current_profit = (current_price - cost) * current_qty
    
    # 利润曲线数据
    profit_curve = []
    max_profit = current_profit
    optimal_price = current_price
    optimal_increase = 0
    warning_threshold = None  # 超过此涨幅利润开始下降
    
    # 从0%到最大涨幅遍历
    increases = [i * step for i in range(0, int(max_price_increase / step) + 1)]
    
    prev_profit = current_profit
    profit_declining = False
    
    for increase in increases:
        new_price = current_price * (1 + increase)
        
        # 预测销量变化
        price_change_rate = increase * 100
        qty_change_rate = price_change_rate * elasticity / 100  # 弹性是负数
        new_qty = current_qty * (1 + qty_change_rate)
        new_qty = max(0, new_qty)
        
        # 计算利润
        new_profit = (new_price - cost) * new_qty
        
        profit_curve.append({
            'increase': round(increase * 100, 1),
            'price': round(new_price, 2),
            'qty_change': round(qty_change_rate * 100, 1),
            'profit': round(new_profit, 2),
            'profit_change': round((new_profit - current_profit) / abs(current_profit) * 100 if current_profit != 0 else 0, 1)
        })
        
        # 更新最优点
        if new_profit > max_profit:
            max_profit = new_profit
            optimal_price = new_price
            optimal_increase = increase
        
        # 检测利润开始下降的拐点
        if not profit_declining and new_profit < prev_profit and increase > 0:
            profit_declining = True
            warning_threshold = increase
        
        # 检测亏损点
        if new_profit < current_profit and warning_threshold is None:
            warning_threshold = increase
        
        prev_profit = new_profit
    
    return {
        'optimal_price': round(optimal_price, 2),
        'optimal_increase': round(optimal_increase * 100, 1),
        'current_profit': round(current_profit, 2),
        'max_profit': round(max_profit, 2),
        'profit_increase': round((max_profit - current_profit) / abs(current_profit) * 100 if current_profit != 0 else 0, 1),
        'warning_threshold': round(warning_threshold * 100, 1) if warning_threshold else None,
        'profit_curve': profit_curve
    }


def get_pricing_decision(
    current_price: float,
    cost: float,
    current_qty: float,
    elasticity: float,
    channel: str = None,
    category: str = None
) -> Dict[str, Any]:
    """
    智能定价决策树 - 核心函数
    
    决策逻辑：
    1️⃣ 判断是否需要调价
       - 利润率 < 0 (穿底) → 必须调价 ⚠️
       - 利润率 < 10% (低利润) → 建议调价
       - 利润率 ≥ 10% → 可选调价
    
    2️⃣ 计算最优调价幅度（基于弹性）
       - 目标：利润最大化
       - 公式：找到 (价格-成本) × 预估销量 最大的点
    
    3️⃣ 给出建议和风险提示
       - 🟢 推荐：利润最优点
       - 🟡 保守：较安全的涨幅
       - 🔴 警告：超过此涨幅可能导致利润下降
    
    Returns:
        {
            'urgency': 调价紧迫度 (critical/recommended/optional),
            'urgency_icon': 紧迫度图标,
            'urgency_text': 紧迫度描述,
            'current_margin': 当前利润率,
            'recommendations': [
                {'level': 'optimal', 'icon': '🟢', 'price': x, 'increase': y, 'profit_change': z, 'reason': ...},
                {'level': 'conservative', 'icon': '🟡', ...},
            ],
            'warning': 警告信息,
            'optimal_analysis': 最优点分析结果
        }
    """
    if current_price <= 0 or cost <= 0:
        return None
    
    # 1️⃣ 计算当前利润率，判断调价紧迫度
    current_margin = (current_price - cost) / current_price * 100
    current_profit = (current_price - cost) * current_qty
    
    if current_margin < 0:
        urgency = 'critical'
        urgency_icon = '🚨'
        urgency_text = f'穿底商品！利润率 {current_margin:.1f}%，必须调价止损'
    elif current_margin < 10:
        urgency = 'recommended'
        urgency_icon = '⚠️'
        urgency_text = f'低利润商品，利润率 {current_margin:.1f}%，建议提价'
    elif current_margin < 20:
        urgency = 'suggested'
        urgency_icon = '💡'
        urgency_text = f'利润率 {current_margin:.1f}%，可考虑优化'
    else:
        urgency = 'optional'
        urgency_icon = '✅'
        urgency_text = f'利润率 {current_margin:.1f}%，可维持或微调'
    
    # 2️⃣ 计算最优价格点
    optimal = find_optimal_price(
        current_price, cost, current_qty, elasticity, channel
    )
    
    if not optimal:
        return {
            'urgency': urgency,
            'urgency_icon': urgency_icon,
            'urgency_text': urgency_text,
            'current_margin': round(current_margin, 1),
            'recommendations': [],
            'warning': '无法计算最优价格',
            'optimal_analysis': None
        }
    
    # 3️⃣ 生成三档建议
    recommendations = []
    
    # 🟢 推荐方案（利润最优点）
    if optimal['optimal_increase'] > 0:
        opt_price = optimal['optimal_price']
        opt_prediction = predict_profit_change(
            current_price, opt_price, cost, current_qty, elasticity, channel
        )
        
        recommendations.append({
            'level': 'optimal',
            'icon': '🟢',
            'label': '推荐',
            'price': opt_price,
            'increase': optimal['optimal_increase'],
            'qty_change': opt_prediction['qty_change_rate'] if opt_prediction else 0,
            'profit_change': optimal['profit_increase'],
            'new_margin': opt_prediction['new_margin'] if opt_prediction else 0,
            'reason': f"利润最大化点，预估利润+{optimal['profit_increase']:.1f}%"
        })
    
    # 🟡 保守方案（约为最优点的一半）
    conservative_increase = optimal['optimal_increase'] / 2 if optimal['optimal_increase'] > 2 else 1
    if conservative_increase >= 0.5:
        cons_price = round(current_price * (1 + conservative_increase / 100), 2)
        cons_prediction = predict_profit_change(
            current_price, cons_price, cost, current_qty, elasticity, channel
        )
        
        if cons_prediction:
            recommendations.append({
                'level': 'conservative',
                'icon': '🟡',
                'label': '保守',
                'price': cons_price,
                'increase': conservative_increase,
                'qty_change': cons_prediction['qty_change_rate'],
                'profit_change': cons_prediction['profit_change_rate'],
                'new_margin': cons_prediction['new_margin'],
                'reason': '风险较低的稳妥方案'
            })
    
    # 🔴 激进方案（警告线附近）
    if optimal['warning_threshold'] and optimal['warning_threshold'] > optimal['optimal_increase']:
        aggressive_increase = (optimal['optimal_increase'] + optimal['warning_threshold']) / 2
        if aggressive_increase > optimal['optimal_increase'] + 2:
            aggr_price = round(current_price * (1 + aggressive_increase / 100), 2)
            aggr_prediction = predict_profit_change(
                current_price, aggr_price, cost, current_qty, elasticity, channel
            )
            
            if aggr_prediction:
                recommendations.append({
                    'level': 'aggressive',
                    'icon': '🔴',
                    'label': '激进',
                    'price': aggr_price,
                    'increase': round(aggressive_increase, 1),
                    'qty_change': aggr_prediction['qty_change_rate'],
                    'profit_change': aggr_prediction['profit_change_rate'],
                    'new_margin': aggr_prediction['new_margin'],
                    'reason': '高风险高回报，谨慎使用'
                })
    
    # 生成警告信息
    warning = None
    if optimal['warning_threshold']:
        warning = f"⚠️ 涨价超过 {optimal['warning_threshold']:.1f}% 可能导致利润下降"
    
    # 弹性风险提示
    elasticity_warning = None
    if abs(elasticity) >= 1.5:
        elasticity_warning = f"该商品弹性系数 {elasticity:.1f}，价格敏感度高，建议小幅调整"
    elif abs(elasticity) <= 0.5:
        elasticity_warning = f"该商品弹性系数 {elasticity:.1f}，价格敏感度低，有较大涨价空间"
    
    return {
        'urgency': urgency,
        'urgency_icon': urgency_icon,
        'urgency_text': urgency_text,
        'current_margin': round(current_margin, 1),
        'current_profit': round(current_profit, 2),
        'elasticity': elasticity,
        'elasticity_warning': elasticity_warning,
        'recommendations': recommendations,
        'warning': warning,
        'optimal_analysis': optimal
    }


def generate_pricing_suggestions(
    current_price: float,
    cost: float,
    current_qty: float,
    elasticity: float,
    channel: str = None,
    target_margin: float = None
) -> List[Dict[str, Any]]:
    """
    生成智能定价建议（保守/推荐/激进三档）
    
    Args:
        current_price: 当前价格
        cost: 成本
        current_qty: 当前日均销量
        elasticity: 弹性系数
        channel: 渠道
        target_margin: 目标利润率（可选）
    
    Returns:
        三档建议方案列表
    """
    suggestions = []
    
    current_margin = (current_price - cost) / current_price * 100 if current_price > 0 else 0
    
    # 根据当前利润率确定调价策略
    if current_margin < 5:
        # 严重亏损，需要大幅涨价
        adjustments = [0.08, 0.15, 0.25]  # 保守8%，推荐15%，激进25%
        labels = ['🟢 保守', '🟡 推荐', '🔴 激进']
    elif current_margin < 15:
        # 低利润，适度涨价
        adjustments = [0.05, 0.10, 0.18]
        labels = ['🟢 保守', '🟡 推荐', '🔴 激进']
    elif current_margin < 25:
        # 正常利润，微调
        adjustments = [0.03, 0.06, 0.10]
        labels = ['🟢 微调', '🟡 适度', '🔴 进取']
    else:
        # 利润较好，可以维持或小幅调整
        adjustments = [0, 0.03, 0.06]
        labels = ['🟢 维持', '🟡 微涨', '🔴 试探']
    
    for i, (adj, label) in enumerate(zip(adjustments, labels)):
        new_price = current_price * (1 + adj)
        new_price = round(new_price, 1)  # 保留1位小数，便于定价
        
        prediction = predict_profit_change(
            current_price, new_price, cost, current_qty, elasticity, channel
        )
        
        if prediction:
            suggestions.append({
                'label': label,
                'new_price': new_price,
                'price_change': f"+{adj*100:.0f}%" if adj > 0 else "维持",
                'qty_change': f"{prediction['qty_change_rate']:+.0f}%",
                'profit_change': f"{prediction['profit_change_rate']:+.0f}%",
                'new_margin': f"{prediction['new_margin']:.1f}%",
                'prediction': prediction
            })
    
    # 如果有目标利润率，计算目标价格
    if target_margin is not None and target_margin > current_margin:
        target_price = cost / (1 - target_margin / 100)
        target_price = round(target_price, 1)
        
        prediction = predict_profit_change(
            current_price, target_price, cost, current_qty, elasticity, channel
        )
        
        if prediction:
            suggestions.append({
                'label': f'🎯 目标{target_margin:.0f}%',
                'new_price': target_price,
                'price_change': f"+{prediction['price_change_rate']:.0f}%",
                'qty_change': f"{prediction['qty_change_rate']:+.0f}%",
                'profit_change': f"{prediction['profit_change_rate']:+.0f}%",
                'new_margin': f"{prediction['new_margin']:.1f}%",
                'prediction': prediction
            })
    
    return suggestions


def get_risk_assessment(
    price_change_rate: float,
    qty_change_rate: float,
    elasticity: float,
    category: str = None
) -> Dict[str, Any]:
    """
    评估调价风险
    
    Returns:
        {
            'level': 'low'/'medium'/'high',
            'icon': 风险图标,
            'notes': 风险提示列表
        }
    """
    notes = []
    risk_score = 0
    
    # 涨价幅度风险
    if abs(price_change_rate) > 20:
        notes.append("调价幅度较大（>20%），建议分步调整")
        risk_score += 2
    elif abs(price_change_rate) > 10:
        notes.append("调价幅度中等（10-20%）")
        risk_score += 1
    
    # 销量影响风险
    if qty_change_rate < -30:
        notes.append("预计销量大幅下降（>30%），需谨慎评估")
        risk_score += 2
    elif qty_change_rate < -15:
        notes.append("预计销量有所下降（15-30%）")
        risk_score += 1
    
    # 高敏感商品
    if abs(elasticity) > 1.3:
        notes.append("该商品价格敏感度较高，用户对价格变化反应强烈")
        risk_score += 1
    
    # 敏感品类
    sensitive_categories = ['生鲜', '水果', '蔬菜', '饮料']
    if category and any(cat in category for cat in sensitive_categories):
        notes.append(f"{category}类商品通常对价格敏感")
    
    # 确定风险等级
    if risk_score >= 4:
        level = 'high'
        icon = '🔴'
    elif risk_score >= 2:
        level = 'medium'
        icon = '🟡'
    else:
        level = 'low'
        icon = '🟢'
    
    if not notes:
        notes.append("调价风险可控")
    
    return {
        'level': level,
        'icon': icon,
        'score': risk_score,
        'notes': notes
    }


# ==================== 批量调价处理 ====================

def calculate_batch_pricing(
    products_df: pd.DataFrame,
    adjustment_type: str = 'percentage',
    adjustment_value: float = 0.1,
    target_margin: float = None,
    price_changes_df: pd.DataFrame = None
) -> pd.DataFrame:
    """
    批量计算调价方案
    
    Args:
        products_df: 商品DataFrame，需包含：店内码、商品名称、渠道、当前价格、成本、日均销量、一级分类
        adjustment_type: 调整类型 - 'percentage'(按比例) / 'target_margin'(目标利润率) / 'manual'(手动)
        adjustment_value: 调整值（比例或目标利润率）
        target_margin: 目标利润率（当type='target_margin'时使用）
        price_changes_df: 历史价格变动数据（用于获取弹性）
    
    Returns:
        包含调价方案和预测结果的DataFrame
    """
    results = []
    
    # 识别字段
    code_col = next((c for c in ['店内码', '商品编码', 'SKU'] if c in products_df.columns), '店内码')
    name_col = '商品名称'
    channel_col = next((c for c in ['渠道', '平台'] if c in products_df.columns), None)
    price_col = next((c for c in ['实收价格', '当前价格', '售价'] if c in products_df.columns), None)
    cost_col = next((c for c in ['单品成本', '商品采购成本', '成本'] if c in products_df.columns), None)
    qty_col = next((c for c in ['日均销量', '销量', '月售'] if c in products_df.columns), None)
    category_col = next((c for c in ['一级分类名', '一级分类'] if c in products_df.columns), None)
    
    if not price_col or not cost_col:
        print("批量调价：缺少价格或成本字段")
        return pd.DataFrame()
    
    for _, row in products_df.iterrows():
        product_code = row.get(code_col, '')
        product_name = row.get(name_col, '')
        channel = row.get(channel_col, '') if channel_col else ''
        current_price = float(row.get(price_col, 0))
        cost = float(row.get(cost_col, 0))
        current_qty = float(row.get(qty_col, 1)) if qty_col else 1
        category = row.get(category_col, '') if category_col else ''
        
        if current_price <= 0 or cost <= 0:
            continue
        
        # 获取弹性系数
        elasticity, elasticity_source = get_product_elasticity(
            product_code, channel, category, price_changes_df
        )
        
        # 计算新价格
        if adjustment_type == 'percentage':
            new_price = current_price * (1 + adjustment_value)
        elif adjustment_type == 'target_margin':
            tm = target_margin if target_margin else adjustment_value
            new_price = cost / (1 - tm / 100) if tm < 100 else cost * 2
        else:
            new_price = current_price  # manual需要单独设置
        
        new_price = round(new_price, 2)
        
        # 预测效果
        prediction = predict_profit_change(
            current_price, new_price, cost, current_qty, elasticity, channel
        )
        
        if not prediction:
            continue
        
        # 风险评估
        risk = get_risk_assessment(
            prediction['price_change_rate'],
            prediction['qty_change_rate'],
            elasticity,
            category
        )
        
        results.append({
            '店内码': product_code,
            '商品名称': product_name,
            '渠道': channel,
            '一级分类': category,
            '当前价格': current_price,
            '成本': cost,
            '新价格': new_price,
            '调价幅度': f"{prediction['price_change_rate']:+.1f}%",
            '当前利润率': f"{prediction['current_margin']:.1f}%",
            '新利润率': f"{prediction['new_margin']:.1f}%",
            '弹性系数': elasticity,
            '弹性来源': elasticity_source,
            '预估销量变化': f"{prediction['qty_change_rate']:+.1f}%",
            '预估利润变化': f"{prediction['profit_change_rate']:+.1f}%",
            '风险等级': risk['icon'],
            '风险提示': '; '.join(risk['notes']),
            # 原始数值（用于排序和计算）
            '_price_change': prediction['price_change_rate'],
            '_qty_change': prediction['qty_change_rate'],
            '_profit_change': prediction['profit_change_rate'],
            '_new_margin': prediction['new_margin'],
            '_current_profit': prediction['current_profit'],
            '_new_profit': prediction['new_profit'],
        })
    
    return pd.DataFrame(results)


# ==================== 导出功能 ====================

def export_pricing_plan_to_excel(
    pricing_df: pd.DataFrame,
    summary: Dict[str, Any] = None
) -> bytes:
    """
    导出调价方案到Excel
    
    Args:
        pricing_df: 调价方案DataFrame
        summary: 汇总统计
    
    Returns:
        Excel文件的bytes
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet1: 调价清单
        export_cols = [
            '店内码', '商品名称', '渠道', '一级分类',
            '当前价格', '成本', '新价格', '调价幅度',
            '当前利润率', '新利润率',
            '预估销量变化', '预估利润变化',
            '风险等级', '风险提示'
        ]
        export_df = pricing_df[[c for c in export_cols if c in pricing_df.columns]]
        export_df.to_excel(writer, sheet_name='调价清单', index=False)
        
        # Sheet2: 效果预估汇总
        if not pricing_df.empty:
            summary_data = {
                '指标': [
                    '调整商品数',
                    '平均调价幅度',
                    '平均利润率提升',
                    '预估总利润变化',
                    '高风险商品数',
                    '中风险商品数',
                    '低风险商品数',
                ],
                '数值': [
                    len(pricing_df),
                    f"{pricing_df['_price_change'].mean():.1f}%",
                    f"{(pricing_df['_new_margin'] - pricing_df['当前价格'].apply(lambda x: 0)).mean():.1f}%",
                    f"{(pricing_df['_new_profit'].sum() - pricing_df['_current_profit'].sum()):.2f}元/天",
                    len(pricing_df[pricing_df['风险等级'] == '🔴']),
                    len(pricing_df[pricing_df['风险等级'] == '🟡']),
                    len(pricing_df[pricing_df['风险等级'] == '🟢']),
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='效果预估', index=False)
        
        # Sheet3: 弹性分析
        elasticity_cols = ['店内码', '商品名称', '渠道', '弹性系数', '弹性来源']
        elasticity_df = pricing_df[[c for c in elasticity_cols if c in pricing_df.columns]]
        elasticity_df.to_excel(writer, sheet_name='弹性分析', index=False)
    
    output.seek(0)
    return output.getvalue()


# ==================== 辅助函数 ====================

def calculate_target_price(cost: float, target_margin: float, current_price: float = None) -> float:
    """
    根据成本和目标利润率计算售价
    
    Args:
        cost: 成本价
        target_margin: 目标利润率（0-1之间的小数，如0.2表示20%）
        current_price: 当前价格（可选，用于价格合理性检查）
    
    Returns:
        计算出的目标售价
    """
    if cost <= 0:
        return current_price or 0
    
    # 如果目标利润率超过100%，限制为100%
    if target_margin >= 1:
        target_margin = 0.99
    
    # 计算目标价格: 价格 = 成本 / (1 - 利润率)
    target_price = cost / (1 - target_margin)
    
    # 价格合理性检查
    if current_price and target_price > current_price * 2:
        # 涨幅超过100%，限制最大涨幅
        target_price = current_price * 2
    
    return round(target_price, 2)


def get_pricing_summary(pricing_df: pd.DataFrame) -> Dict[str, Any]:
    """获取调价方案汇总统计"""
    if pricing_df.empty:
        return {
            'total_products': 0,
            'avg_price_change': 0,
            'avg_margin_change': 0,
            'total_profit_change': 0,
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0,
        }
    
    return {
        'total_products': len(pricing_df),
        'avg_price_change': round(pricing_df['_price_change'].mean(), 1),
        'avg_margin_change': round(pricing_df['_new_margin'].mean() - 
                                   (pricing_df['当前价格'] - pricing_df['成本']) / pricing_df['当前价格'] * 100, 1).mean() 
                                   if '当前价格' in pricing_df.columns else 0,
        'total_profit_change': round(pricing_df['_new_profit'].sum() - pricing_df['_current_profit'].sum(), 2),
        'high_risk_count': len(pricing_df[pricing_df['风险等级'] == '🔴']),
        'medium_risk_count': len(pricing_df[pricing_df['风险等级'] == '🟡']),
        'low_risk_count': len(pricing_df[pricing_df['风险等级'] == '🟢']),
    }


# ==================== 滞销品降价策略 ====================

# 滞销等级定义
STAGNANT_LEVELS = {
    'light': {'days_min': 7, 'days_max': 7, 'discount_min': 0.05, 'discount_max': 0.10, 'label': '🟡 轻度滞销'},
    'medium': {'days_min': 8, 'days_max': 15, 'discount_min': 0.10, 'discount_max': 0.15, 'label': '🟠 中度滞销'},
    'heavy': {'days_min': 16, 'days_max': 30, 'discount_min': 0.15, 'discount_max': 0.20, 'label': '🔴 重度滞销'},
    'severe': {'days_min': 31, 'days_max': 9999, 'discount_min': 0.20, 'discount_max': 0.30, 'label': '⚫ 超重度滞销'},
}

# 销量下滑降价策略
SALES_DECLINE_STRATEGY = {
    'mild': {'decline_min': 0.10, 'decline_max': 0.30, 'discount_min': 0.03, 'discount_max': 0.05},
    'moderate': {'decline_min': 0.30, 'decline_max': 0.50, 'discount_min': 0.05, 'discount_max': 0.10},
    'severe': {'decline_min': 0.50, 'decline_max': 1.0, 'discount_min': 0.10, 'discount_max': 0.15},
}


def get_stagnant_products(df: pd.DataFrame, store: str = None, level: str = 'all') -> pd.DataFrame:
    """
    获取滞销商品列表 - 基于销售流水数据
    
    滞销定义：数据周期内，商品最后一次销售距今超过N天
    - 轻度滞销：最后销售=7天前
    - 中度滞销：最后销售在8-15天前
    - 重度滞销：最后销售在16-30天前  
    - 超重度滞销：最后销售>30天前
    
    Args:
        df: 原始销售数据DataFrame
        store: 门店名称
        level: 滞销等级 - 'light'/'medium'/'heavy'/'severe'/'all'
    
    Returns:
        滞销商品DataFrame
    """
    if df is None or df.empty:
        print("[滞销品] 数据为空")
        return pd.DataFrame()
    
    # 检测必需字段
    date_col = next((c for c in ['日期', '下单时间'] if c in df.columns), None)
    stock_col = next((c for c in ['剩余库存', '库存', '库存数量', 'stock'] if c in df.columns), None)
    name_col = '商品名称' if '商品名称' in df.columns else None
    store_col = next((c for c in ['门店名称', '门店'] if c in df.columns), None)
    code_col = next((c for c in ['店内码', '商品编码', 'sku'] if c in df.columns), None)
    category_col = next((c for c in ['一级分类名', '一级分类'] if c in df.columns), None)
    price_col = next((c for c in ['商品实售价', '实收价格', '售价'] if c in df.columns), None)
    cost_col = next((c for c in ['商品采购成本', '单品成本', '成本'] if c in df.columns), None)
    qty_col = next((c for c in ['月售', '销量'] if c in df.columns), None)
    
    print(f"[滞销品] 检测字段: date={date_col}, stock={stock_col}, name={name_col}, qty={qty_col}")
    print(f"[滞销品] 数据行数: {len(df)}, level={level}")
    
    if not date_col or not name_col:
        print("[滞销品] 缺少日期或商品名称字段")
        return pd.DataFrame()
    
    try:
        df_copy = df.copy()
        
        # 门店筛选
        if store and store_col:
            df_copy = df_copy[df_copy[store_col] == store]
            print(f"[滞销品] 门店筛选后: {len(df_copy)} 行")
        
        if df_copy.empty:
            print("[滞销品] 门店筛选后数据为空")
            return pd.DataFrame()
        
        # 确保日期格式
        df_copy[date_col] = pd.to_datetime(df_copy[date_col])
        last_date = df_copy[date_col].max()
        print(f"[滞销品] 数据最后日期: {last_date}")
        
        # 计算每个商品的最后销售日期和销量
        agg_dict = {date_col: 'max'}
        if qty_col:
            agg_dict[qty_col] = 'sum'
        
        product_stats = df_copy.groupby(name_col).agg(agg_dict).reset_index()
        product_stats.columns = ['商品名称', '最后销售日期'] + (['总销量'] if qty_col else [])
        product_stats['滞销天数'] = (last_date - product_stats['最后销售日期']).dt.days
        
        # 重命名为兼容后续代码
        product_last_sale = product_stats[['商品名称', '最后销售日期', '滞销天数']].copy()
        print(f"[滞销品] 商品数: {len(product_last_sale)}, 滞销天数分布: {product_last_sale['滞销天数'].value_counts().head(5).to_dict()}")
        
        # 🔧 先计算单品成本（关键！原始数据中 商品采购成本 = 单品成本 × 销量）
        if cost_col and qty_col:
            df_copy['_销量'] = pd.to_numeric(df_copy[qty_col], errors='coerce').fillna(1).replace(0, 1)
            df_copy['_单品成本'] = df_copy[cost_col].fillna(0) / df_copy['_销量']
        elif cost_col:
            df_copy['_单品成本'] = df_copy[cost_col].fillna(0)
        else:
            df_copy['_单品成本'] = 0
        
        # 获取商品信息（使用正确的单品成本）
        agg_dict = {}
        if code_col:
            agg_dict[code_col] = 'first'
        if category_col:
            agg_dict[category_col] = 'first'
        if price_col:
            agg_dict[price_col] = 'mean'
        # 使用计算后的单品成本
        agg_dict['_单品成本'] = 'mean'
        
        if agg_dict:
            product_info = df_copy.groupby(name_col).agg(agg_dict).reset_index()
        else:
            product_info = df_copy[[name_col]].drop_duplicates()
        
        # 🔧 获取库存信息 - 采用订单数据概览的双重判断逻辑
        if stock_col:
            # 步骤1: 获取最后一天有销售的商品库存
            last_day_data = df_copy[df_copy[date_col] == last_date]
            if len(last_day_data) > 0:
                last_day_stock_map = last_day_data.groupby(name_col)[stock_col].last().to_dict()
            else:
                last_day_stock_map = {}
            
            # 步骤2: 获取每个商品最后一次售卖记录的库存（关键！）
            last_sale_stock = df_copy.sort_values(date_col).groupby(name_col).agg({
                stock_col: 'last'
            })
            last_sale_stock_map = last_sale_stock[stock_col].to_dict()
            
            # 步骤3: 双重判断 - 优先使用最后一天的库存，否则使用最后售卖时的库存
            def get_final_stock(product_name):
                if product_name in last_day_stock_map:
                    return last_day_stock_map[product_name]
                elif product_name in last_sale_stock_map:
                    return last_sale_stock_map[product_name]
                else:
                    return 0
            
            # 为每个商品获取库存
            all_products = product_info[name_col].unique()
            stock_df = pd.DataFrame({
                '商品名称': all_products,
                '库存': [get_final_stock(p) for p in all_products]
            })
            product_info = product_info.merge(stock_df, left_on=name_col, right_on='商品名称', how='left')
            if name_col != '商品名称':
                product_info = product_info.drop(columns=['商品名称'])
            product_info['库存'] = product_info['库存'].fillna(0)
            print(f"[滞销品] 库存获取完成: 最后一天{len(last_day_stock_map)}个, 最后售卖{len(last_sale_stock_map)}个")
        else:
            product_info['库存'] = 1  # 无库存字段时假设有库存
        
        # 合并数据
        result = product_last_sale.merge(product_info, on='商品名称', how='left')
        
        # 筛选有库存的商品（如果有库存字段）
        if stock_col and '库存' in result.columns:
            before_filter = len(result)
            result = result[result['库存'] > 0]
            print(f"[滞销品] 库存>0筛选: {before_filter} -> {len(result)}")
        else:
            print(f"[滞销品] 无库存字段，跳过库存筛选，保留全部 {len(result)} 个商品")
        
        # 根据滞销等级筛选
        before_level_filter = len(result)
        if level == 'all':
            # 所有滞销品（>=7天）
            result = result[result['滞销天数'] >= 7]
        elif level in STAGNANT_LEVELS:
            lvl = STAGNANT_LEVELS[level]
            result = result[
                (result['滞销天数'] >= lvl['days_min']) & 
                (result['滞销天数'] <= lvl['days_max'])
            ]
        print(f"[滞销品] 等级筛选({level}): {before_level_filter} -> {len(result)}")
        
        # 添加滞销等级标签
        def get_stagnant_label(days):
            if days == 7:
                return '🟡 轻度'
            elif 8 <= days <= 15:
                return '🟠 中度'
            elif 16 <= days <= 30:
                return '🔴 重度'
            elif days > 30:
                return '⚫ 超重度'
            return '--'
        
        result['滞销等级'] = result['滞销天数'].apply(get_stagnant_label)
        
        # 重命名列
        rename_map = {}
        if code_col and code_col in result.columns:
            rename_map[code_col] = '店内码'
        if category_col and category_col in result.columns:
            rename_map[category_col] = '一级分类'
        if price_col and price_col in result.columns:
            rename_map[price_col] = '实收价格'
        # 🔧 使用计算后的单品成本字段
        if '_单品成本' in result.columns:
            rename_map['_单品成本'] = '单品成本'
        
        if rename_map:
            result = result.rename(columns=rename_map)
        
        # 按滞销天数降序排序
        result = result.sort_values('滞销天数', ascending=False)
        
        print(f"[滞销品] 获取到 {len(result)} 个滞销商品 (等级={level})")
        return result
        
    except Exception as e:
        print(f"[滞销品] 获取滞销商品失败: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def get_markdown_price_decision(
    current_price: float,
    cost: float,
    stagnant_days: int = None,
    sales_decline_rate: float = None,
    source_type: str = 'stagnant'
) -> Dict[str, Any]:
    """
    获取降价决策（保本底线）
    
    Args:
        current_price: 当前价格
        cost: 成本
        stagnant_days: 滞销天数（用于滞销品）
        sales_decline_rate: 销量下滑比例（用于销量下滑商品）
        source_type: 来源类型 - 'stagnant'/'sales_decline'
    
    Returns:
        降价决策结果
    """
    if current_price <= 0 or cost <= 0:
        return None
    
    current_margin = (current_price - cost) / current_price * 100
    floor_price = cost  # 保本底线
    
    # 确定降价比例
    discount_rate = 0
    discount_reason = ""
    
    if source_type == 'stagnant' and stagnant_days:
        # 根据滞销天数确定降价策略
        if stagnant_days == 7:
            discount_rate = 0.08  # 轻度：降8%
            discount_reason = "轻度滞销(7天)"
        elif 8 <= stagnant_days <= 15:
            discount_rate = 0.12  # 中度：降12%
            discount_reason = "中度滞销(8-15天)"
        elif 16 <= stagnant_days <= 30:
            discount_rate = 0.18  # 重度：降18%
            discount_reason = "重度滞销(16-30天)"
        elif stagnant_days > 30:
            discount_rate = 0.25  # 超重度：降25%
            discount_reason = "超重度滞销(>30天)"
    
    elif source_type == 'sales_decline' and sales_decline_rate:
        # 根据销量下滑比例确定降价策略
        if 0.10 <= sales_decline_rate < 0.30:
            discount_rate = 0.04  # 轻度下滑：降4%
            discount_reason = "销量下滑10-30%"
        elif 0.30 <= sales_decline_rate < 0.50:
            discount_rate = 0.08  # 中度下滑：降8%
            discount_reason = "销量下滑30-50%"
        elif sales_decline_rate >= 0.50:
            discount_rate = 0.12  # 重度下滑：降12%
            discount_reason = "销量下滑>50%"
    
    # 计算建议价格（不低于成本）
    suggested_price = current_price * (1 - discount_rate)
    suggested_price = max(suggested_price, floor_price)
    suggested_price = round(suggested_price, 2)
    
    # 实际降价幅度
    actual_discount = (current_price - suggested_price) / current_price if current_price > 0 else 0
    
    # 是否触及保本底线
    hit_floor = suggested_price <= floor_price * 1.01  # 允许1%误差
    
    # 新利润率
    new_margin = (suggested_price - cost) / suggested_price * 100 if suggested_price > 0 else 0
    
    return {
        'current_price': round(current_price, 2),
        'cost': round(cost, 2),
        'floor_price': round(floor_price, 2),
        'current_margin': round(current_margin, 1),
        'suggested_price': suggested_price,
        'suggested_discount': round(discount_rate * 100, 1),
        'actual_discount': round(actual_discount * 100, 1),
        'new_margin': round(new_margin, 1),
        'hit_floor': hit_floor,
        'reason': discount_reason,
        'warning': f"⚠️ 已触及保本底线¥{floor_price:.2f}" if hit_floor else None
    }


def get_sales_decline_products(df: pd.DataFrame, store: str = None) -> pd.DataFrame:
    """
    获取销量下滑商品
    
    从诊断模块获取销量下滑的商品列表
    """
    # 这里复用诊断模块的逻辑，在callbacks.py中直接调用诊断模块
    # 此函数作为占位，实际逻辑在回调中实现
    return pd.DataFrame()


def get_profit_decline_products(df: pd.DataFrame, store: str = None) -> pd.DataFrame:
    """
    获取利润率下滑商品
    
    从诊断模块获取利润率下滑的商品列表
    """
    # 同上，实际逻辑在回调中复用诊断模块
    return pd.DataFrame()


# 判断商品来源的调价方向
SOURCE_DIRECTION = {
    # 提价类
    'overflow': 'up',           # 穿底止血
    'price_abnormal': 'up',     # 价格异常
    'profit_decline': 'up',     # 利润率下滑
    'low_profit': 'up',         # 低利润（兼容旧选项）
    
    # 降价类
    'sales_decline': 'down',    # 销量下滑
    'stagnant_light': 'down',   # 轻度滞销
    'stagnant_medium': 'down',  # 中度滞销
    'stagnant_heavy': 'down',   # 重度滞销
    'stagnant_severe': 'down',  # 超重度滞销
    'stagnant_all': 'down',     # 全部滞销
}


def get_source_direction(source: str) -> str:
    """
    根据商品来源获取默认调价方向
    
    Returns:
        'up': 提价
        'down': 降价
    """
    return SOURCE_DIRECTION.get(source, None)

