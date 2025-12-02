#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化的八象限分析器 - 科学版
整合品类动态阈值、趋势分析、置信度评估
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional


class ScientificQuadrantAnalyzer:
    """
    科学的八象限分析器
    
    改进点:
    1. 支持品类动态阈值(不同品类不同标准)
    2. 增加置信度评估(边界商品标记)
    3. 支持趋势分析(30天数据可分析趋势)
    4. 增加利润贡献度权重
    """
    
    def __init__(self, data: pd.DataFrame, use_category_threshold: bool = True):
        """
        初始化分析器
        
        Args:
            data: 订单数据DataFrame
            use_category_threshold: 是否使用品类动态阈值
        """
        self.data = data.copy()
        self.use_category_threshold = use_category_threshold
        self.category_col = self._detect_category_field()
        self._map_fields()  # 字段映射
    
    def _map_fields(self):
        """智能字段映射"""
        # 月售字段
        if '月售' not in self.data.columns and '销量' in self.data.columns:
            self.data['月售'] = self.data['销量']
        
        # 营销总成本字段 (修正: 优先使用营销活动补贴，而非平台佣金)
        # 营销活动字段列表
        marketing_cols = ['满减金额', '新客减免金额', '配送费减免金额', '商家代金券', 
                         '商家承担部分券', '满赠金额', '商家其他优惠', '商品减免金额']
        
        # 检查是否存在营销字段
        available_marketing_cols = [col for col in marketing_cols if col in self.data.columns]
        
        if available_marketing_cols:
            # 如果有营销字段，计算总营销成本
            # 注意: 这些通常是订单级字段，如果数据是商品级明细，直接相加会重复计算
            # 这里假设输入数据是商品级明细(每行一个商品)，且订单级字段在同一订单的所有行中重复
            
            # 策略: 暂时先不在此处计算，而在 _aggregate_to_product_level 中通过分摊逻辑计算
            pass
        elif '营销总成本' not in self.data.columns:
            # 降级方案: 如果没有营销活动字段，才使用平台服务费/佣金
            if '平台服务费' in self.data.columns:
                self.data['营销总成本'] = self.data['平台服务费'].fillna(0)
            elif '平台佣金' in self.data.columns:
                self.data['营销总成本'] = self.data['平台佣金'].fillna(0)
    
    def _detect_category_field(self) -> Optional[str]:
        """检测品类字段"""
        for col in ['一级分类名', '美团一级分类', '一级分类']:
            if col in self.data.columns:
                return col
        return None
    
    def calculate_category_thresholds(self) -> Dict[str, Dict[str, float]]:
        """
        计算品类动态阈值
        
        Returns:
            {
                '饮料': {'营销占比': 0.45, '毛利率': 0.25, '售罄率': 0.55},
                '休闲食品': {'营销占比': 0.52, '毛利率': 0.32, '售罄率': 0.48},
                ...
            }
        """
        if not self.category_col or not self.use_category_threshold:
            return {}
        
        # 聚合到商品级别
        product_data = self._aggregate_to_product_level()
        
        thresholds = {}
        for category in product_data[self.category_col].unique():
            cat_data = product_data[product_data[self.category_col] == category]
            
            # 品类商品数太少,不使用动态阈值
            if len(cat_data) < 10:
                continue
            
            thresholds[category] = {
                # 营销占比: 使用60分位数(高于60%的商品算高营销)
                '营销占比': cat_data['营销占比'].quantile(0.6),
                # 毛利率: 使用40分位数(低于40%的商品算低毛利)
                '毛利率': cat_data['毛利率'].quantile(0.4),
                # 售罄率: 使用50分位数 + 30分位数月售
                '售罄率': cat_data['售罄率'].quantile(0.5) if '售罄率' in cat_data.columns else 0,
                '月售': cat_data['月售'].quantile(0.3),
            }
        
        return thresholds
    
    def _aggregate_to_product_level(self) -> pd.DataFrame:
        """聚合到商品级别"""
        # 先计算每条记录的订单总收入（实收价格是单价，需要乘以销量）
        self.data['订单总收入'] = self.data['实收价格'] * self.data['月售']
        
        # === 核心修正: 营销成本分摊逻辑 ===
        # 营销活动字段列表
        marketing_cols = ['满减金额', '新客减免金额', '配送费减免金额', '商家代金券', 
                         '商家承担部分券', '满赠金额', '商家其他优惠', '商品减免金额']
        available_marketing_cols = [col for col in marketing_cols if col in self.data.columns]
        
        if available_marketing_cols and '订单ID' in self.data.columns:
            # 1. 计算每个订单的总营销成本 (取first避免重复)
            order_marketing = self.data.groupby('订单ID')[available_marketing_cols].first().sum(axis=1).reset_index(name='订单营销总额')
            
            # 2. 计算每个订单的总GMV (用于分摊)
            order_gmv = self.data.groupby('订单ID')['订单总收入'].sum().reset_index(name='订单GMV')
            
            # 3. 合并回原数据
            temp_df = self.data.merge(order_marketing, on='订单ID', how='left').merge(order_gmv, on='订单ID', how='left')
            
            # 4. 按金额占比分摊营销成本
            # 分摊公式: 商品营销成本 = 订单营销总额 * (商品收入 / 订单GMV)
            # 处理除零错误
            temp_df['分摊营销成本'] = np.where(
                temp_df['订单GMV'] > 0,
                temp_df['订单营销总额'] * (temp_df['订单总收入'] / temp_df['订单GMV']),
                0
            )
            
            # 更新到self.data (为了后续聚合)
            self.data['分摊营销成本'] = temp_df['分摊营销成本']
            marketing_agg_col = '分摊营销成本'
        else:
            # 降级: 使用预先存在的营销总成本(可能是佣金)
            marketing_agg_col = '营销总成本' if '营销总成本' in self.data.columns else None

        agg_dict = {
            '订单总收入': 'sum',      # 实收价格×销量的总和
            '利润额': 'sum',          # 已是总额，直接sum
            '月售': 'sum'
        }
        
        if marketing_agg_col:
            agg_dict[marketing_agg_col] = 'sum'
        
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
        
        # 统一营销成本字段名
        if marketing_agg_col == '分摊营销成本':
            product_data.rename(columns={'分摊营销成本': '营销总成本'}, inplace=True)
        elif marketing_agg_col is None:
            product_data['营销总成本'] = 0
            
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
        
        # 计算指标
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
    
    def analyze_with_confidence(self,
                                marketing_threshold: float = 0.15,
                                margin_threshold: float = 0.3,
                                turnover_rate_threshold: float = 0.5) -> pd.DataFrame:
        """
        八象限分析 + 置信度评估
        
        Args:
            marketing_threshold: 全局营销占比阈值(品类阈值优先)
            margin_threshold: 全局毛利率阈值(品类阈值优先)
            turnover_rate_threshold: 售罄率阈值
        
        Returns:
            包含象限、置信度、建议的DataFrame
        """
        product_data = self._aggregate_to_product_level()
        
        # 获取品类阈值
        category_thresholds = self.calculate_category_thresholds()
        
        # 为每个商品确定阈值
        def get_threshold(row, metric):
            """获取商品的阈值(品类或全局)"""
            if self.category_col and row[self.category_col] in category_thresholds:
                return category_thresholds[row[self.category_col]][metric]
            else:
                # 使用全局阈值
                if metric == '营销占比':
                    return marketing_threshold
                elif metric == '毛利率':
                    return margin_threshold
                elif metric == '售罄率':
                    return turnover_rate_threshold
                elif metric == '月售':
                    return product_data['月售'].quantile(0.3)
        
        # 判断等级
        product_data['营销阈值'] = product_data.apply(lambda row: get_threshold(row, '营销占比'), axis=1)
        product_data['毛利阈值'] = product_data.apply(lambda row: get_threshold(row, '毛利率'), axis=1)
        product_data['售罄率阈值'] = product_data.apply(lambda row: get_threshold(row, '售罄率'), axis=1)
        product_data['月售阈值'] = product_data.apply(lambda row: get_threshold(row, '月售'), axis=1)
        
        # 分类
        product_data['营销等级'] = np.where(
            product_data['营销占比'] >= product_data['营销阈值'], '高营销', '低营销'
        )
        product_data['毛利等级'] = np.where(
            product_data['毛利率'] >= product_data['毛利阈值'], '高毛利', '低毛利'
        )
        
        # 动销等级(双重判断:售罄率+月售)
        if '售罄率' in product_data.columns:
            product_data['动销等级'] = np.where(
                (product_data['售罄率'] >= product_data['售罄率阈值']) &
                (product_data['月售'] >= product_data['月售阈值']),
                '高动销',
                '低动销'
            )
        else:
            product_data['动销等级'] = np.where(
                product_data['月售'] >= product_data['月售阈值'], '高动销', '低动销'
            )
        
        # 🆕 置信度评估(边界商品标记)
        boundary_range = 0.1  # ±10%为边界
        
        product_data['营销置信度'] = product_data.apply(
            lambda row: self._calculate_confidence(
                row['营销占比'], row['营销阈值'], boundary_range
            ), axis=1
        )
        product_data['毛利置信度'] = product_data.apply(
            lambda row: self._calculate_confidence(
                row['毛利率'], row['毛利阈值'], boundary_range
            ), axis=1
        )
        product_data['动销置信度'] = product_data.apply(
            lambda row: self._calculate_confidence(
                row.get('售罄率', row['月售']/row['月售阈值']), 
                row['售罄率阈值'], 
                boundary_range
            ), axis=1
        )
        
        # 综合置信度(取最低)
        product_data['分类置信度'] = product_data[[
            '营销置信度', '毛利置信度', '动销置信度'
        ]].min(axis=1)
        
        # 象限映射
        quadrant_map = {
            ('高营销', '高毛利', '高动销'): ('Q1', '💰金牛过度', 'P1', '降低营销投入,测试价格弹性'),
            ('高营销', '高毛利', '低动销'): ('Q2', '⚠️高成本蓄客', 'P2', '优化营销策略或考虑退出'),
            ('高营销', '低毛利', '高动销'): ('Q3', '🔴引流亏损', 'P1', '提价或减少营销,警惕亏损'),
            ('高营销', '低毛利', '低动销'): ('Q4', '❌双输商品', 'P0', '立即停止营销或下架'),
            ('低营销', '高毛利', '高动销'): ('Q5', '⭐黄金商品', 'OK', '保持策略,可适度加大营销'),
            ('低营销', '高毛利', '低动销'): ('Q6', '💎潜力商品', 'P3', '增加营销投入,提升曝光'),
            ('低营销', '低毛利', '高动销'): ('Q7', '🎯引流爆款', 'OK', '维持现状,搭配高毛利商品'),
            ('低营销', '低毛利', '低动销'): ('Q8', '🗑️淘汰区', 'P4', '考虑清仓或下架')
        }
        
        product_data['象限组合'] = list(zip(
            product_data['营销等级'],
            product_data['毛利等级'],
            product_data['动销等级']
        ))
        
        quadrant_info = product_data['象限组合'].map(
            lambda x: quadrant_map.get(x, ('Q0', '未分类', 'P5', '需人工判断'))
        )
        product_data[['象限编号', '象限名称', '优先级', '优化建议']] = pd.DataFrame(
            quadrant_info.tolist(),
            index=product_data.index
        )
        
        # 🆕 置信度标签
        product_data['置信度标签'] = product_data['分类置信度'].apply(
            lambda x: '高置信' if x > 0.7 else ('中置信' if x > 0.4 else '低置信')
        )
        
        # 🆕 增强建议(结合置信度)
        product_data['增强建议'] = product_data.apply(
            lambda row: self._generate_enhanced_advice(row), axis=1
        )
        
        # 清理临时列
        product_data = product_data.drop(columns=['象限组合'])
        
        # 排序
        priority_order = ['P0', 'P1', 'P2', 'P3', 'P4', 'OK', 'P5']
        product_data['优先级排序'] = product_data['优先级'].map(
            {p: i for i, p in enumerate(priority_order)}
        )
        product_data = product_data.sort_values(
            ['优先级排序', '利润额'],
            ascending=[True, False]
        ).drop(columns=['优先级排序'])
        
        return product_data
    
    def _calculate_confidence(self, value: float, threshold: float, boundary_range: float) -> float:
        """
        计算分类置信度
        
        Args:
            value: 实际值
            threshold: 阈值
            boundary_range: 边界范围
        
        Returns:
            置信度 (0-1),越接近阈值置信度越低
        """
        distance = abs(value - threshold)
        if distance > boundary_range:
            return 1.0  # 高置信
        else:
            # 线性衰减: distance=0 → confidence=0, distance=boundary_range → confidence=1
            return distance / boundary_range
    
    def _generate_enhanced_advice(self, row: pd.Series) -> str:
        """生成增强建议"""
        base_advice = row['优化建议']
        confidence = row['置信度标签']
        
        if confidence == '低置信':
            return f"{base_advice} (⚠️边界商品,建议人工复核)"
        elif confidence == '中置信':
            return f"{base_advice} (ℹ️接近阈值,密切关注)"
        else:
            return base_advice
    
    def calculate_trend(self, days_split: int = 15) -> pd.DataFrame:
        """
        计算趋势(需要有日期字段)
        
        Args:
            days_split: 数据分割点(默认15天,前后各15天)
        
        Returns:
            包含趋势标签的DataFrame
        """
        if '日期' not in self.data.columns:
            print("⚠️ 数据中缺少日期字段,无法计算趋势")
            return self._aggregate_to_product_level()
        
        self.data['日期'] = pd.to_datetime(self.data['日期'])
        max_date = self.data['日期'].max()
        min_date = self.data['日期'].min()
        split_date = max_date - pd.Timedelta(days=days_split)
        
        if split_date <= min_date:
            print(f"⚠️ 数据跨度不足{days_split*2}天,无法计算趋势")
            return self._aggregate_to_product_level()
        
        # 前期和后期数据
        early_data = self.data[self.data['日期'] < split_date]
        recent_data = self.data[self.data['日期'] >= split_date]
        
        # 聚合
        def aggregate_period(df):
            return df.groupby('商品名称').agg({
                '月售': 'sum',
                '利润额': 'sum',
                '实收价格': 'sum'
            }).add_suffix('_period')
        
        early_agg = aggregate_period(early_data)
        recent_agg = aggregate_period(recent_data)
        
        # 合并
        trend_data = early_agg.merge(recent_agg, left_index=True, right_index=True, how='outer').fillna(0)
        
        # 计算变化率
        trend_data['销量变化率'] = np.where(
            trend_data['月售_period_x'] > 0,
            (trend_data['月售_period_y'] - trend_data['月售_period_x']) / trend_data['月售_period_x'],
            0
        )
        trend_data['利润变化率'] = np.where(
            trend_data['利润额_period_x'] > 0,
            (trend_data['利润额_period_y'] - trend_data['利润额_period_x']) / trend_data['利润额_period_x'],
            0
        )
        
        # 趋势标签
        trend_data['销量趋势'] = trend_data['销量变化率'].apply(
            lambda x: '上升⬆️' if x > 0.1 else ('下降⬇️' if x < -0.1 else '平稳→')
        )
        trend_data['利润趋势'] = trend_data['利润变化率'].apply(
            lambda x: '上升⬆️' if x > 0.1 else ('下降⬇️' if x < -0.1 else '平稳→')
        )
        
        return trend_data.reset_index()
    
    def generate_diagnostic_report(self, product_name: str) -> str:
        """
        生成单品诊断报告
        
        Args:
            product_name: 商品名称
        
        Returns:
            诊断报告文本
        """
        product_data = self.analyze_with_confidence()
        
        if product_name not in product_data['商品名称'].values:
            return f"❌ 未找到商品: {product_name}"
        
        product = product_data[product_data['商品名称'] == product_name].iloc[0]
        
        report = f"""
╔════════════════════════════════════════════════════════════════╗
║  📦 {product_name} - 深度诊断报告
╚════════════════════════════════════════════════════════════════╝

【基础信息】
  象限: {product['象限名称']} ({product['象限编号']})
  优先级: {product['优先级']}
  置信度: {product['置信度标签']} ({product['分类置信度']:.1%})

【核心指标】
  💰 利润贡献: ¥{product['利润额']:.2f} (毛利率: {product['毛利率']:.1%})
  📊 销量: {product['月售']:.0f}件
  💸 营销占比: {product['营销占比']:.1%} (阈值: {product['营销阈值']:.1%})
  🔄 动销率: {product.get('动销率', 0):.1%} (阈值: {product['动销率阈值']:.1%})

【相对位置】
  营销等级: {product['营销等级']} (置信度: {product['营销置信度']:.1%})
  毛利等级: {product['毛利等级']} (置信度: {product['毛利置信度']:.1%})
  动销等级: {product['动销等级']} (置信度: {product['动销置信度']:.1%})

【优化建议】
  {product['增强建议']}

【阈值说明】
  {'✅ 使用品类动态阈值' if self.use_category_threshold and self.category_col else '⚠️ 使用全局固定阈值'}
  {'(品类: ' + str(product.get(self.category_col, '')) + ')' if self.category_col else ''}
"""
        return report


# ==================== 使用示例 ====================
if __name__ == '__main__':
    print("=" * 80)
    print("🔬 科学的八象限分析器 - 使用指南")
    print("=" * 80)
    print()
    print("核心改进:")
    print("  1. ✅ 品类动态阈值 - 不同品类不同标准")
    print("  2. ✅ 置信度评估 - 标记边界商品")
    print("  3. ✅ 趋势分析 - 利用30天数据分析趋势")
    print("  4. ✅ 增强建议 - 结合置信度给出建议")
    print()
    print("使用方法:")
    print("```python")
    print("# 初始化分析器")
    print("analyzer = ScientificQuadrantAnalyzer(df, use_category_threshold=True)")
    print()
    print("# 获取品类阈值")
    print("thresholds = analyzer.calculate_category_thresholds()")
    print("print(thresholds)")
    print()
    print("# 执行分析")
    print("result = analyzer.analyze_with_confidence()")
    print()
    print("# 查看低置信度商品(需要人工复核)")
    print("low_confidence = result[result['置信度标签'] == '低置信']")
    print()
    print("# 生成单品诊断")
    print("report = analyzer.generate_diagnostic_report('贝特幂啤酒')")
    print("print(report)")
    print()
    print("# 计算趋势")
    print("trend_data = analyzer.calculate_trend(days_split=15)")
    print("```")
    print()
    print("💡 建议:")
    print("  - 先运行品类阈值诊断工具,了解各品类差异")
    print("  - 如果品类差异大(>30%),使用品类动态阈值")
    print("  - 低置信度商品需要人工复核,不要盲目执行建议")
    print("  - 结合趋势分析,预判商品未来走向")
