#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多维度评分模型分析器
将每个维度转换为0-100分,根据业务重要性加权求和
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional


class ScoringModelAnalyzer:
    """
    多维度评分模型分析器
    
    核心思路:
    1. 将每个指标转换为0-100分(连续评分,避免硬切)
    2. 根据业务重要性设置权重
    3. 计算综合得分,分档评级
    4. 保留象限概念,但基于得分而非阈值
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化分析器
        
        Args:
            data: 订单数据DataFrame
        """
        self.data = data.copy()
        self.category_col = self._detect_category_field()
        self._map_fields()
    
    def _detect_category_field(self) -> Optional[str]:
        """检测品类字段"""
        for col in ['一级分类名', '美团一级分类', '一级分类']:
            if col in self.data.columns:
                return col
        return None
    
    def _map_fields(self):
        """智能字段映射"""
        # 月售字段
        if '月售' not in self.data.columns and '销量' in self.data.columns:
            self.data['月售'] = self.data['销量']
        
        # 营销总成本字段（平台服务费和平台佣金是同一个东西，商品级用服务费，订单级用佣金）
        if '营销总成本' not in self.data.columns:
            if '平台服务费' in self.data.columns:
                self.data['营销总成本'] = self.data['平台服务费'].fillna(0)
            elif '平台佣金' in self.data.columns:
                self.data['营销总成本'] = self.data['平台佣金'].fillna(0)
    
    def _aggregate_to_product_level(self) -> pd.DataFrame:
        """聚合到商品级别"""
        # 先计算每条记录的订单总收入（实收价格是单价，需要乘以销量）
        self.data['订单总收入'] = self.data['实收价格'] * self.data['月售']
        
        agg_dict = {
            '营销总成本': 'sum',      # 已是总额，直接sum
            '订单总收入': 'sum',      # 实收价格×销量的总和
            '利润额': 'sum',          # 已是总额，直接sum
            '月售': 'sum'
        }
        
        # 添加店内码字段（如果存在）
        if '店内码' in self.data.columns:
            agg_dict['店内码'] = 'first'  # 取第一次出现的店内码
        
        # 分组字段
        group_fields = ['商品名称']
        if self.category_col:
            group_fields.append(self.category_col)
        
        product_data = self.data.groupby(group_fields).agg(agg_dict).reset_index()
        
        # 重命名回实收价格（现在是总收入）
        product_data.rename(columns={'订单总收入': '实收价格'}, inplace=True)
        
        # 获取期末库存(最后订单日的剩余库存)
        stock_col = self._detect_stock_field()
        if stock_col:
            last_stock = self._get_last_day_stock(stock_col)
            product_data = product_data.merge(
                last_stock.rename('实际剩余库存'),
                on='商品名称',
                how='left'
            )
            # 保留原始库存值,同时创建期末库存字段(用于计算)
            product_data['期末库存'] = product_data['实际剩余库存'].fillna(0)
        
        # 计算基础指标
        product_data['营销占比'] = np.where(
            product_data['实收价格'] > 0,
            product_data['营销总成本'] / product_data['实收价格'],
            0
        )
        product_data['毛利率'] = np.where(
            product_data['实收价格'] > 0,
            product_data['利润额'] / product_data['实收价格'],
            0
        )
        product_data['营销ROI'] = np.where(
            product_data['营销总成本'] > 0,
            product_data['利润额'] / product_data['营销总成本'],
            np.nan
        )
        
        if stock_col:
            # 售罄率 = 月售 / (月售 + 期末库存)
            product_data['售罄率'] = np.where(
                (product_data['月售'] + product_data['期末库存']) > 0,
                product_data['月售'] / (product_data['月售'] + product_data['期末库存']),
                0
            )
        
        return product_data
    
    def _detect_stock_field(self) -> Optional[str]:
        """检测库存字段"""
        for col in ['剩余库存', '库存', '期末库存']:
            if col in self.data.columns:
                return col
        return None
    
    def _get_last_day_stock(self, stock_col: str) -> pd.Series:
        """获取每个商品最后一次订单的剩余库存"""
        # 改为取每个商品最后一次出现时的库存,避免因max(日期)导致的数据缺失
        return self.data.groupby('商品名称')[stock_col].last()
    
    def calculate_marketing_score(self, df: pd.DataFrame) -> pd.Series:
        """
        营销效率分: 营销占比越低越好,ROI越高越好
        
        分数构成:
        - 营销ROI得分 (50分): ROI越高得分越高
        - 营销占比得分 (50分): 占比越低得分越高
        """
        # 营销ROI得分 (0-50分)
        # 将ROI标准化到0-50分,ROI>2认为是优秀(50分)
        roi_score = df['营销ROI'].fillna(0).clip(lower=0, upper=2) / 2 * 50
        
        # 营销占比得分 (0-50分)
        # 占比越低得分越高,0%=50分,100%=0分
        cost_ratio_score = (1 - df['营销占比'].clip(lower=0, upper=1)) * 50
        
        return roi_score + cost_ratio_score
    
    def calculate_profit_score(self, df: pd.DataFrame) -> pd.Series:
        """
        盈利能力分: 综合考虑毛利率和利润绝对值
        
        分数构成:
        - 毛利率得分 (40分): 毛利率越高得分越高
        - 利润绝对值得分 (60分): 利润额越高得分越高
        """
        # 毛利率得分 (0-40分)
        # 毛利率>80%认为是优秀(40分)
        margin_score = df['毛利率'].clip(lower=0, upper=0.8) / 0.8 * 40
        
        # 利润绝对值得分 (0-60分)
        # 使用90分位数作为优秀标准
        profit_90 = df['利润额'].quantile(0.9)
        if profit_90 > 0:
            profit_score = (df['利润额'].clip(lower=0, upper=profit_90) / profit_90) * 60
        else:
            profit_score = pd.Series(0, index=df.index)
        
        return margin_score + profit_score
    
    def calculate_turnover_score(self, df: pd.DataFrame) -> pd.Series:
        """
        动销健康分: 综合售罄率和销量
        
        分数构成:
        - 售罄率得分 (40分): 售罄率越高得分越高
        - 销量得分 (60分): 销量越高得分越高
        """
        # 售罄率得分 (0-40分)
        if '售罄率' in df.columns:
            # 售罄率>80%认为是优秀(40分)
            turnover_score = df['售罄率'].clip(lower=0, upper=0.8) / 0.8 * 40
        else:
            turnover_score = pd.Series(0, index=df.index)
        
        # 销量得分 (0-60分)
        # 使用90分位数作为优秀标准
        volume_90 = df['月售'].quantile(0.9)
        if volume_90 > 0:
            volume_score = (df['月售'].clip(lower=0, upper=volume_90) / volume_90) * 60
        else:
            volume_score = pd.Series(0, index=df.index)
        
        return turnover_score + volume_score
    
    def analyze_with_scoring(self, 
                            weights: Dict[str, float] = None) -> pd.DataFrame:
        """
        基于评分模型的分析
        
        Args:
            weights: 各维度权重,默认{'营销效率': 0.25, '盈利能力': 0.45, '动销健康': 0.3}
        
        Returns:
            包含评分和等级的DataFrame
        """
        if weights is None:
            weights = {
                '营销效率': 0.25,  # 营销成本控制
                '盈利能力': 0.45,  # 最重要:赚钱能力
                '动销健康': 0.3    # 销售活力
            }
        
        # 验证权重和为1
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            print(f"⚠️ 权重总和为{total_weight:.2f},已自动归一化")
            weights = {k: v/total_weight for k, v in weights.items()}
        
        print(f"📊 使用权重配置: 营销效率{weights['营销效率']:.0%}, 盈利能力{weights['盈利能力']:.0%}, 动销健康{weights['动销健康']:.0%}")
        
        # 聚合到商品级别
        product_data = self._aggregate_to_product_level()
        
        # 计算三大维度得分
        product_data['营销效率分'] = self.calculate_marketing_score(product_data)
        product_data['盈利能力分'] = self.calculate_profit_score(product_data)
        product_data['动销健康分'] = self.calculate_turnover_score(product_data)
        
        # 计算综合得分
        product_data['综合得分'] = (
            product_data['营销效率分'] * weights['营销效率'] +
            product_data['盈利能力分'] * weights['盈利能力'] +
            product_data['动销健康分'] * weights['动销健康']
        )
        
        # 基于综合得分分档
        product_data['评分等级'] = pd.cut(
            product_data['综合得分'],
            bins=[0, 40, 60, 80, 100],
            labels=['⚠️需优化', '📊待改进', '✅表现良好', '⭐优秀'],
            include_lowest=True
        )
        
        # 🆕 映射到八象限(保留象限概念,但基于得分判断)
        product_data = self._map_to_quadrants(product_data)
        
        # 🆕 单维度等级(用于详细分析)
        product_data['营销效率等级'] = pd.cut(
            product_data['营销效率分'],
            bins=[0, 40, 60, 80, 100],
            labels=['差', '中', '良', '优'],
            include_lowest=True
        )
        product_data['盈利能力等级'] = pd.cut(
            product_data['盈利能力分'],
            bins=[0, 40, 60, 80, 100],
            labels=['差', '中', '良', '优'],
            include_lowest=True
        )
        product_data['动销健康等级'] = pd.cut(
            product_data['动销健康分'],
            bins=[0, 40, 60, 80, 100],
            labels=['差', '中', '良', '优'],
            include_lowest=True
        )
        
        # 排序: 按综合得分降序
        product_data = product_data.sort_values('综合得分', ascending=False)
        
        return product_data
    
    def _map_to_quadrants(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        将评分映射到八象限
        
        逻辑:
        - 营销效率分>60: 低营销(好), ≤60: 高营销(需优化)
        - 盈利能力分>60: 高毛利(好), ≤60: 低毛利(需优化)
        - 动销健康分>60: 高动销(好), ≤60: 低动销(需优化)
        """
        # 基于得分判断等级
        df['营销等级'] = np.where(df['营销效率分'] > 60, '低营销', '高营销')
        df['毛利等级'] = np.where(df['盈利能力分'] > 60, '高毛利', '低毛利')
        df['动销等级'] = np.where(df['动销健康分'] > 60, '高动销', '低动销')
        
        # 象限映射
        quadrant_map = {
            ('高营销', '高毛利', '高动销'): ('Q1', '💰金牛过度', 'P1', '降低营销投入'),
            ('高营销', '高毛利', '低动销'): ('Q2', '⚠️高成本蓄客', 'P2', '优化营销策略'),
            ('高营销', '低毛利', '高动销'): ('Q3', '🔴引流亏损', 'P1', '提价或减少营销'),
            ('高营销', '低毛利', '低动销'): ('Q4', '❌双输商品', 'P0', '立即停止营销'),
            ('低营销', '高毛利', '高动销'): ('Q5', '⭐黄金商品', 'OK', '保持策略'),
            ('低营销', '高毛利', '低动销'): ('Q6', '💎潜力商品', 'P3', '增加营销投入'),
            ('低营销', '低毛利', '高动销'): ('Q7', '🎯引流爆款', 'OK', '维持现状'),
            ('低营销', '低毛利', '低动销'): ('Q8', '🗑️淘汰区', 'P4', '考虑清仓')
        }
        
        df['象限组合'] = list(zip(df['营销等级'], df['毛利等级'], df['动销等级']))
        
        quadrant_info = df['象限组合'].map(
            lambda x: quadrant_map.get(x, ('Q0', '未分类', 'P5', '需人工判断'))
        )
        df[['象限编号', '象限名称', '优先级', '优化建议']] = pd.DataFrame(
            quadrant_info.tolist(),
            index=df.index
        )
        
        df = df.drop(columns=['象限组合'])
        
        return df
    
    def generate_score_report(self, product_name: str, product_data: pd.DataFrame = None) -> str:
        """
        生成单品评分报告
        
        Args:
            product_name: 商品名称
            product_data: 分析结果(可选,如果没有则自动分析)
        
        Returns:
            评分报告文本
        """
        if product_data is None:
            product_data = self.analyze_with_scoring()
        
        if product_name not in product_data['商品名称'].values:
            return f"❌ 未找到商品: {product_name}"
        
        product = product_data[product_data['商品名称'] == product_name].iloc[0]
        
        # 排名
        rank = product_data[product_data['商品名称'] == product_name].index[0] + 1
        total = len(product_data)
        
        report = f"""
╔════════════════════════════════════════════════════════════════╗
║  📊 {product_name} - 评分报告
╚════════════════════════════════════════════════════════════════╝

【综合评价】
  🏆 综合得分: {product['综合得分']:.1f} 分
  📊 评分等级: {product['评分等级']}
  📈 排名: {rank}/{total} (前{rank/total*100:.1f}%)
  🎯 象限: {product['象限名称']} ({product['象限编号']})

【三大维度得分】
  💸 营销效率: {product['营销效率分']:.1f}分 ({product['营销效率等级']})
     ├─ 营销ROI: {product.get('营销ROI', 0):.2f}
     └─ 营销占比: {product['营销占比']:.1%}
  
  💰 盈利能力: {product['盈利能力分']:.1f}分 ({product['盈利能力等级']})
     ├─ 毛利率: {product['毛利率']:.1%}
     └─ 利润额: ¥{product['利润额']:.2f}
  
  🔄 动销健康: {product['动销健康分']:.1f}分 ({product['动销健康等级']})
     ├─ 动销率: {product.get('动销率', 0):.1%}
     └─ 月售: {product['月售']:.0f}件

【优化建议】
  {product['优化建议']}

【得分解读】
  90-100分: ⭐优秀 - 各项指标均衡优异
  80-90分:  ✅表现良好 - 大部分指标优秀
  60-80分:  📊待改进 - 部分指标需要优化
  0-60分:   ⚠️需优化 - 存在明显短板
"""
        return report


# ==================== 使用示例 ====================
if __name__ == '__main__':
    print("=" * 80)
    print("📊 多维度评分模型分析器 - 使用指南")
    print("=" * 80)
    print()
    print("核心特点:")
    print("  1. ✅ 连续评分 - 避免简单二分的硬切")
    print("  2. ✅ 权重可调 - 根据业务重点调整权重")
    print("  3. ✅ 易于理解 - 分数直观,类似学生成绩")
    print("  4. ✅ 保留象限 - 基于得分映射到八象限")
    print()
    print("使用方法:")
    print("```python")
    print("# 初始化分析器")
    print("analyzer = ScoringModelAnalyzer(df)")
    print()
    print("# 使用默认权重分析")
    print("result = analyzer.analyze_with_scoring()")
    print()
    print("# 自定义权重(如更重视盈利能力)")
    print("result = analyzer.analyze_with_scoring({")
    print("    '营销效率': 0.2,")
    print("    '盈利能力': 0.5,  # 提高盈利权重")
    print("    '动销健康': 0.3")
    print("})")
    print()
    print("# 生成单品报告")
    print("report = analyzer.generate_score_report('贝特幂啤酒', result)")
    print("print(report)")
    print("```")
    print()
    print("💡 优势:")
    print("  - 评分连续,避免了49%和51%被硬性分类的问题")
    print("  - 权重可调,适应不同业务场景")
    print("  - 综合得分可直接排序,找出TOP商品")
