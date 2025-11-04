"""
问题诊断引擎 - 自动识别运营问题并生成诊断报告

核心功能：
1. 销量下滑诊断
2. 客单价归因分析
3. 负毛利商品预警
4. 高配送费订单优化
5. 流量品&利润品失衡预警
6. 异常波动预警
7. 一键生成综合问题报告（Excel导出）

作者：AI Assistant
日期：2025-01-14
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')


class ProblemDiagnosticEngine:
    """问题诊断引擎"""
    
    def __init__(self, df: pd.DataFrame):
        """
        初始化诊断引擎
        
        Parameters:
        -----------
        df : pd.DataFrame
            包含订单数据的DataFrame，需包含以下列：
            - 订单ID, 三级分类名, 商品实售价, 时段, 场景（可选）
            - 日期, 周, 配送距离, 物流配送费, 平台佣金
            - 商品角色（流量品/利润品/凑单品）
            - 价格带（可选）
        """
        self.df = df.copy()
        self._prepare_data()
    
    def _prepare_data(self):
        """
        预处理数据
        
        ⚠️ 重要: 统一计算口径，与Tab 1/2保持一致
        - 收入字段: 优先使用'预计订单收入'，不存在则用'商品实售价'
        - 利润字段: 优先使用'实际利润'，不存在则计算
        - 毛利率: 基于商品实售价计算
        """
        # 确保日期列存在
        if '日期' in self.df.columns:
            self.df['日期'] = pd.to_datetime(self.df['日期'])
        
        # 🔧 统一收入字段：优先使用'预计订单收入'
        if '预计订单收入' not in self.df.columns:
            if '商品实售价' in self.df.columns:
                self.df['预计订单收入'] = self.df['商品实售价']
                print("⚠️ 诊断引擎: '预计订单收入'字段不存在，使用'商品实售价'代替")
            else:
                print("❌ 诊断引擎: 缺少收入字段('预计订单收入'或'商品实售价')")
        
        # 使用统一的收入字段
        revenue_col = '预计订单收入'
        
        # 计算单品毛利和毛利率（如果成本列存在）
        if '商品采购成本' in self.df.columns:
            # 使用'商品实售价'计算毛利（不是预计订单收入），与Tab 1/2一致
            price_col = '商品实售价' if '商品实售价' in self.df.columns else revenue_col
            self.df['单品毛利'] = self.df[price_col] - self.df['商品采购成本']
            self.df['单品毛利率'] = (self.df['单品毛利'] / self.df[price_col] * 100).fillna(0)
        
        # 🔧 计算实际利润（如果不存在）
        if '实际利润' not in self.df.columns:
            total_cost = pd.Series(0, index=self.df.index)
            
            if '商品采购成本' in self.df.columns:
                total_cost += self.df['商品采购成本'].fillna(0)
            if '物流配送费' in self.df.columns:
                total_cost += self.df['物流配送费'].fillna(0)
            if '平台佣金' in self.df.columns:
                total_cost += self.df['平台佣金'].fillna(0)
            
            self.df['实际利润'] = self.df[revenue_col] - total_cost
        
        # 计算配送费占比（使用预计订单收入）
        if '物流配送费' in self.df.columns and '订单ID' in self.df.columns:
            order_sales = self.df.groupby('订单ID')[revenue_col].sum()
            order_delivery = self.df.groupby('订单ID')['物流配送费'].first()
            delivery_ratio = (order_delivery / order_sales * 100).fillna(0)
            self.df['配送费占比'] = self.df['订单ID'].map(delivery_ratio)
    
    def get_available_periods(self, time_period: str = 'week') -> List[Dict[str, Any]]:
        """
        获取可用的时间周期列表（用于UI选择器）
        
        Parameters:
        -----------
        time_period : str
            周期类型 ('day', 'week', 'month')
        
        Returns:
        --------
        List[Dict]: 周期列表，每个元素包含 {index, label, date_range}
        """
        if '日期' not in self.df.columns:
            return []
        
        max_date = self.df['日期'].max()
        min_date = self.df['日期'].min()
        
        # 根据周期类型设置参数
        if time_period == 'day':
            period_days = 1
            total_days = (max_date - min_date).days
            max_periods = min(total_days + 1, 30)  # 最多显示30天
        elif time_period == 'week':
            period_days = 7
            total_days = (max_date - min_date).days
            max_periods = min(total_days // period_days, 12)  # 最多显示12周
        else:  # month
            period_days = 30
            total_days = (max_date - min_date).days
            max_periods = min(total_days // period_days, 12)  # 最多显示12个月
        
        periods = []
        for i in range(max_periods):
            if time_period == 'day':
                # 按日：每个index对应一天
                date = max_date - timedelta(days=i)
                label = f'{date.month}月{date.day}日 ({date.year}年)'
                periods.append({
                    'index': i,
                    'label': label,
                    'date_range': f'{date:%Y-%m-%d}',
                    'start_date': date,
                    'end_date': date
                })
            elif time_period == 'week':
                start = max_date - timedelta(days=(i + 1) * period_days - 1)
                end = max_date - timedelta(days=i * period_days)
                week_num = end.isocalendar()[1]
                year = end.year
                label = f'第{week_num}周 ({year}年)'
                periods.append({
                    'index': i,
                    'label': label,
                    'date_range': f'{start:%Y-%m-%d} ~ {end:%Y-%m-%d}',
                    'start_date': start,
                    'end_date': end
                })
            else:  # month
                start = max_date - timedelta(days=(i + 1) * period_days - 1)
                end = max_date - timedelta(days=i * period_days)
                label = f'{start.year}年{start.month}月'
                periods.append({
                    'index': i,
                    'label': label,
                    'date_range': f'{start:%Y-%m-%d} ~ {end:%Y-%m-%d}',
                    'start_date': start,
                    'end_date': end
                })
        
        return periods
    
    def get_available_price_periods(self, time_period: str = 'week') -> List[Dict]:
        """
        🆕 P2优化: 获取可用的客单价对比周期列表（参考销量下滑诊断）
        
        Parameters:
        -----------
        time_period : str
            周期类型 ('week', 'daily')
        
        Returns:
        --------
        List[Dict]
            可用周期列表，每个元素包含 index, label, date_range
        """
        if '日期' not in self.df.columns:
            return []
        
        max_date = self.df['日期'].max()
        min_date = self.df['日期'].min()
        
        if time_period == 'week':
            period_days = 7
        else:  # daily
            period_days = 1
        
        # 计算可用周期数
        total_days = (max_date - min_date).days
        max_periods = min(total_days // period_days, 12) if period_days > 1 else min(total_days, 30)
        
        periods = []
        for i in range(max_periods):
            if time_period == 'week':
                start = max_date - timedelta(days=(i + 1) * period_days - 1)
                end = max_date - timedelta(days=i * period_days)
                week_num = end.isocalendar()[1]
                year = end.year
                label = f'第{week_num}周 ({year}年)'
            else:  # daily
                start = max_date - timedelta(days=i)
                end = start
                label = start.strftime('%Y年%m月%d日')
            
            periods.append({
                'index': i,
                'label': label,
                'date_range': f'{start:%Y-%m-%d} ~ {end:%Y-%m-%d}' if time_period == 'week' else f'{start:%Y-%m-%d}',
                'start_date': start,
                'end_date': end
            })
        
        return periods

    
    def diagnose_sales_decline(self, 
                              time_period: str = 'week',
                              threshold: float = -20.0,
                              scene_filter: Optional[List[str]] = None,
                              time_slot_filter: Optional[List[str]] = None,
                              current_period_index: Optional[int] = None,
                              compare_period_index: Optional[int] = None) -> pd.DataFrame:
        """
        诊断销量下滑商品
        
        Parameters:
        -----------
        time_period : str
            对比周期 ('week', 'month')
        threshold : float
            下滑阈值（百分比，负数表示下降）
        scene_filter : List[str], optional
            场景筛选列表
        time_slot_filter : List[str], optional
            时段筛选列表
        current_period_index : int, optional
            当前周期索引（0=最新周，1=上一周，以此类推），默认None=最新周
        compare_period_index : int, optional
            对比周期索引（默认None=current_period_index+1）
        
        Returns:
        --------
        pd.DataFrame
            下滑商品诊断表（包含具体周期信息）
        """
        if '日期' not in self.df.columns or '三级分类名' not in self.df.columns:
            return pd.DataFrame()
        
        # 筛选数据
        df_filtered = self.df.copy()
        
        if scene_filter and '场景' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['场景'].isin(scene_filter)]
        if time_slot_filter and '时段' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['时段'].isin(time_slot_filter)]
        
        # 🆕 灵活的周期对比逻辑
        # 获取最大日期，并检查是否为NaT
        max_date = df_filtered['日期'].max()
        
        # 如果max_date是NaT或None，返回空DataFrame
        if pd.isna(max_date):
            return pd.DataFrame()
        
        # 设置默认值
        if current_period_index is None:
            current_period_index = 0  # 默认最新周期
        if compare_period_index is None:
            compare_period_index = current_period_index + 1  # 默认对比上一周期
        
        # 计算周期范围
        if time_period == 'day':
            period_days = 1
            # 当前周期（某一天）
            current_start = max_date - timedelta(days=current_period_index)
            current_end = current_start
            # 对比周期（另一天）
            compare_start = max_date - timedelta(days=compare_period_index)
            compare_end = compare_start
            
            current_label = f'{current_start.month}月{current_start.day}日'
            compare_label = f'{compare_start.month}月{compare_start.day}日'
            period_type = '日'
        elif time_period == 'week':
            period_days = 7
            # 当前周期
            current_start = max_date - timedelta(days=(current_period_index + 1) * period_days - 1)
            current_end = max_date - timedelta(days=current_period_index * period_days)
            # 对比周期
            compare_start = max_date - timedelta(days=(compare_period_index + 1) * period_days - 1)
            compare_end = max_date - timedelta(days=compare_period_index * period_days)
            
            # 计算周数（ISO标准）
            current_week = current_end.isocalendar()[1]
            compare_week = compare_end.isocalendar()[1]
            current_label = f'第{current_week}周'
            compare_label = f'第{compare_week}周'
            period_type = '周'
        else:  # month
            period_days = 30
            # 当前周期
            current_start = max_date - timedelta(days=(current_period_index + 1) * period_days - 1)
            current_end = max_date - timedelta(days=current_period_index * period_days)
            # 对比周期
            compare_start = max_date - timedelta(days=(compare_period_index + 1) * period_days - 1)
            compare_end = max_date - timedelta(days=compare_period_index * period_days)
            
            current_label = f'{current_start.month}月'
            compare_label = f'{compare_start.month}月'
            period_type = '月'
        
        # 提取周期数据
        # 注意：current_期表示当前分析的周期，compare_期表示用于对比的周期
        current_data = df_filtered[
            (df_filtered['日期'] >= current_start) & 
            (df_filtered['日期'] <= current_end)
        ]
        compare_data = df_filtered[
            (df_filtered['日期'] >= compare_start) & 
            (df_filtered['日期'] <= compare_end)
        ]
        
        # 修改：按商品名称统计销量（而不是只按三级分类）
        current_sales = current_data.groupby('商品名称').size()
        compare_sales = compare_data.groupby('商品名称').size()
        
        # 🆕 需求1: 统计预计收入和利润额（按商品名称聚合）
        current_revenue = pd.Series(dtype=float)
        compare_revenue = pd.Series(dtype=float)
        current_profit = pd.Series(dtype=float)
        compare_profit = pd.Series(dtype=float)
        
        if '预计订单收入' in current_data.columns:
            current_revenue = current_data.groupby('商品名称')['预计订单收入'].sum()
        elif '预估订单收入' in current_data.columns:
            current_revenue = current_data.groupby('商品名称')['预估订单收入'].sum()
        
        if '预计订单收入' in compare_data.columns:
            compare_revenue = compare_data.groupby('商品名称')['预计订单收入'].sum()
        elif '预估订单收入' in compare_data.columns:
            compare_revenue = compare_data.groupby('商品名称')['预估订单收入'].sum()
        
        # 🆕 直接使用利润额字段
        if '利润额' in current_data.columns:
            current_profit = current_data.groupby('商品名称')['利润额'].sum()
        
        if '利润额' in compare_data.columns:
            compare_profit = compare_data.groupby('商品名称')['利润额'].sum()
        
        # 🆕 动态表头 - 显示具体周期信息
        comparison = pd.DataFrame({
            f'{current_label}销量': current_sales,
            f'{compare_label}销量': compare_sales
        }).fillna(0)
        
        # 添加收入列（如果有数据）
        if not current_revenue.empty:
            comparison[f'{current_label}预计收入'] = current_revenue.fillna(0)
        if not compare_revenue.empty:
            comparison[f'{compare_label}预计收入'] = compare_revenue.fillna(0)
        
        # 添加利润列（如果有数据）
        if not current_profit.empty:
            comparison[f'{current_label}利润'] = current_profit.fillna(0)
        if not compare_profit.empty:
            comparison[f'{compare_label}利润'] = compare_profit.fillna(0)
        
        comparison['销量变化'] = comparison[f'{current_label}销量'] - comparison[f'{compare_label}销量']
        comparison['变化幅度%'] = (
            (comparison['销量变化'] / comparison[f'{compare_label}销量'].replace(0, 1)) * 100
        ).round(2)
        
        # 筛选下滑商品 - 只要变化幅度小于0就显示（移除threshold限制）
        declined = comparison[comparison['变化幅度%'] < 0].copy()
        
        if len(declined) == 0:
            return pd.DataFrame()
        
        # 🔧 关键修复：从两个周期的合并数据中获取商品信息（避免None值）
        # 合并当前期和对比期数据,确保所有下滑商品都能找到分类信息
        all_period_data = pd.concat([current_data, compare_data], ignore_index=True)
        
        # 补充商品信息 - 动态构建聚合字典（按商品名称聚合，同时获取分类信息）
        agg_dict = {
            '商品实售价': 'mean'
        }
        
        # 关键修改：添加分类信息到聚合字典
        if '一级分类名' in all_period_data.columns:
            agg_dict['一级分类名'] = 'first'
        
        if '三级分类名' in all_period_data.columns:
            agg_dict['三级分类名'] = 'first'
        
        # 可选列：只有存在时才添加
        if '商品角色' in all_period_data.columns:
            agg_dict['商品角色'] = lambda x: x.mode()[0] if len(x.mode()) > 0 else '未知'
        
        if '价格带' in all_period_data.columns:
            agg_dict['价格带'] = lambda x: x.mode()[0] if len(x.mode()) > 0 else '未知'
        
        # 🆕 需求2: 添加店内码和渠道字段
        if '店内码' in all_period_data.columns:
            agg_dict['店内码'] = 'first'  # 取第一个值（店内码应该是固定的）
        
        if '渠道' in all_period_data.columns:
            agg_dict['渠道'] = 'first'  # 取第一个值（渠道应该是固定的）
        
        # 🆕 添加时段和场景字段（用于可视化分析）
        if '时段' in all_period_data.columns:
            agg_dict['时段'] = lambda x: ', '.join(x.value_counts().head(3).index.tolist()) if len(x.value_counts()) > 0 else '无'
        
        if '场景' in all_period_data.columns:
            agg_dict['场景'] = lambda x: ', '.join(x.value_counts().head(2).index.tolist()) if len(x.value_counts()) > 0 else '无'

        
        # 修改：按商品名称聚合（使用合并后的数据）
        product_info = all_period_data.groupby('商品名称').agg(agg_dict)
        
        # 计算平均毛利率
        if '单品毛利率' in all_period_data.columns:
            product_margin = all_period_data.groupby('商品名称')['单品毛利率'].mean()
            product_info['平均毛利率%'] = product_margin.round(2)
        
        # 合并结果
        result = declined.merge(product_info, left_index=True, right_index=True, how='left')
        
        # 🆕 计算收入变化和利润变化（在格式化之前！使用真实利润额）
        current_revenue_col = f'{current_label}预计收入'
        compare_revenue_col = f'{compare_label}预计收入'
        current_profit_col = f'{current_label}利润'
        compare_profit_col = f'{compare_label}利润'
        
        if current_revenue_col in result.columns and compare_revenue_col in result.columns:
            # 此时收入列还是数值，可以直接计算
            result['收入变化'] = result[current_revenue_col].fillna(0) - result[compare_revenue_col].fillna(0)
        else:
            result['收入变化'] = 0.0
        
        # 🆕 使用真实利润额计算利润变化（不再估算）
        if current_profit_col in result.columns and compare_profit_col in result.columns:
            result['利润变化'] = result[current_profit_col].fillna(0) - result[compare_profit_col].fillna(0)
        else:
            # 如果没有利润数据，设为0
            result['利润变化'] = 0.0
        
        # 添加问题诊断
        result['问题等级'] = result['变化幅度%'].apply(
            lambda x: '严重' if x <= -50 else ('警告' if x <= -30 else '关注')
        )
        
        result['建议操作'] = result.apply(self._generate_decline_suggestion, axis=1)
        
        # 🎨 格式化数值显示（所有格式化操作放在最后）
        # 销量相关 - 显示整数（动态列名）
        sales_columns = [col for col in result.columns if '销量' in col and col != '销量变化']
        for col in sales_columns + ['销量变化']:
            if col in result.columns:
                result[col] = result[col].fillna(0).astype(int)
        
        # 🆕 需求1: 格式化预计收入列
        revenue_columns = [col for col in result.columns if '预计收入' in col]
        for col in revenue_columns:
            if col in result.columns:
                result[col] = result[col].apply(lambda x: f"¥{x:.1f}" if pd.notna(x) and x > 0 else "¥0.0")
        
        # 🆕 格式化利润列
        profit_columns = [col for col in result.columns if '利润' in col and col != '利润变化']
        for col in profit_columns:
            if col in result.columns:
                result[col] = result[col].apply(lambda x: f"¥{x:.1f}" if pd.notna(x) and x > 0 else "¥0.0")
        
        # 百分比 - 保留1位小数并添加%符号
        if '变化幅度%' in result.columns:
            result['变化幅度%'] = result['变化幅度%'].apply(lambda x: f"{x:.1f}%")
        
        if '平均毛利率%' in result.columns:
            result['平均毛利率%'] = result['平均毛利率%'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
        
        # 价格 - 保留1位小数
        if '商品实售价' in result.columns:
            result['商品实售价'] = result['商品实售价'].apply(lambda x: f"¥{x:.1f}" if pd.notna(x) else "N/A")
        
        # 分类信息 - 填充缺失值
        if '一级分类名' in result.columns:
            result['一级分类名'] = result['一级分类名'].fillna('未分类')
        
        if '三级分类名' in result.columns:
            result['三级分类名'] = result['三级分类名'].fillna('未分类')
        
        # 🔧 重要：将商品名称从索引移到列
        result = result.reset_index()
        
        return result
    
    def diagnose_customer_price_decline(self, 
                                       time_period: str = 'week',
                                       threshold: float = -5.0,
                                       current_period_index: Optional[int] = None,
                                       compare_period_index: Optional[int] = None) -> pd.DataFrame:
        """
        诊断客单价下滑并归因到具体商品
        
        Parameters:
        -----------
        time_period : str
            分析粒度 ('daily', 'week')
        threshold : float
            客单价下滑阈值（百分比）
        current_period_index : int, optional
            当前周期索引（0=最新周，1=上一周，以此类推），默认None=最新周
        compare_period_index : int, optional
            对比周期索引（默认None=current_period_index+1）
            
        Returns:
        --------
        pd.DataFrame
            客单价下滑归因表
            
        Note:
        -----
        如果current_period_index和compare_period_index都为None，则返回所有下滑周期的批量分析
        如果指定了具体周期索引，则返回该周期的详细分析
        """
        if '订单ID' not in self.df.columns or '日期' not in self.df.columns:
            return pd.DataFrame()
        
        max_date = self.df['日期'].max()
        min_date = self.df['日期'].min()
        
        # 检查日期是否有效
        if pd.isna(max_date) or pd.isna(min_date):
            return pd.DataFrame()
        
        # 🔄 批量分析模式：遍历所有周期找出下滑的
        if current_period_index is None and compare_period_index is None:
            return self._batch_analyze_customer_price(time_period, threshold, max_date, min_date)
        
        # 🎯 单次对比模式：分析指定两个周期
        return self._compare_two_periods_customer_price(
            time_period, threshold, max_date,
            current_period_index or 0,
            compare_period_index or 1
        )
    
    def diagnose_customer_price_decline_by_sheets(self, 
                                                   time_period: str = 'week',
                                                   threshold: float = -5.0,
                                                   current_period_index: Optional[int] = None,
                                                   compare_period_index: Optional[int] = None) -> dict:
        """
        诊断客单价下滑并返回分sheet的数据字典
        
        Parameters:
        -----------
        time_period : str
            分析粒度 ('daily', 'week')
        threshold : float
            客单价下滑阈值（百分比）
        current_period_index : int, optional
            当前周期索引
        compare_period_index : int, optional
            对比周期索引
            
        Returns:
        --------
        dict
            包含三个DataFrame的字典:
            {
                '客单价变化': DataFrame,  # 客单价汇总数据
                '下滑商品分析': DataFrame,  # 只包含下滑商品的TOP5
                '上涨商品分析': DataFrame   # 只包含上涨商品的TOP5
            }
        """
        # 获取完整数据
        full_result = self.diagnose_customer_price_decline(
            time_period=time_period,
            threshold=threshold,
            current_period_index=current_period_index,
            compare_period_index=compare_period_index
        )
        
        if len(full_result) == 0:
            return {
                '客单价变化': pd.DataFrame(),
                '下滑商品分析': pd.DataFrame(),
                '上涨商品分析': pd.DataFrame()
            }
        
        # 提取基础字段（客单价变化部分）
        base_cols = ['对比周期', '之前客单价', '当前客单价', '客单价变化', '变化幅度%', 
                     '商品角色分布', '问题等级', '建议操作']
        price_change_df = full_result[[col for col in base_cols if col in full_result.columns]].copy()
        
        # 提取下滑商品字段
        declining_cols = ['对比周期']
        for i in range(1, 6):
            prefix = f'TOP{i}下滑商品'
            for field in ['商品名称', '分类', '当前单价', '之前单价', '单价变化', '销量变化', '问题原因']:
                col_name = f'{prefix}-{field}'
                if col_name in full_result.columns:
                    declining_cols.append(col_name)
        
        declining_df = full_result[[col for col in declining_cols if col in full_result.columns]].copy()
        
        # 提取上涨商品字段
        rising_cols = ['对比周期']
        for i in range(1, 6):
            prefix = f'TOP{i}上涨商品'
            for field in ['商品名称', '分类', '当前单价', '之前单价', '单价变化', '销量变化', '增长原因']:
                col_name = f'{prefix}-{field}'
                if col_name in full_result.columns:
                    rising_cols.append(col_name)
        
        rising_df = full_result[[col for col in rising_cols if col in full_result.columns]].copy()
        
        return {
            '客单价变化': price_change_df,
            '下滑商品分析': declining_df,
            '上涨商品分析': rising_df
        }
    
    def _batch_analyze_customer_price(self, time_period: str, threshold: float, 
                                       max_date, min_date) -> pd.DataFrame:
        """批量分析所有周期的客单价变化"""
        if time_period == 'week':
            period_days = 7
        else:
            period_days = 1
        
        total_days = (max_date - min_date).days
        # 修复：按日分析时也应该根据实际天数计算max_periods
        if period_days > 1:
            max_periods = min(total_days // period_days, 12)
        else:
            max_periods = min(total_days, 30)
        
        results = []
        for i in range(max_periods - 1):  # 需要前后对比，所以-1
            current_idx = i
            compare_idx = i + 1
            
            # 计算周期范围
            if time_period == 'daily':
                # 按日分析：每个周期就是一天（需要包含整天的数据）
                # 使用日期的开始和结束时间，而不是具体的时间戳
                current_date = (max_date - timedelta(days=current_idx)).date()
                current_start = pd.Timestamp(current_date)  # 当天00:00:00
                current_end = current_start + timedelta(days=1) - timedelta(microseconds=1)  # 当天23:59:59
                
                compare_date = (max_date - timedelta(days=compare_idx)).date()
                compare_start = pd.Timestamp(compare_date)
                compare_end = compare_start + timedelta(days=1) - timedelta(microseconds=1)
            else:
                # 按周分析：每个周期是7天
                current_start = max_date - timedelta(days=(current_idx + 1) * period_days - 1)
                current_end = max_date - timedelta(days=current_idx * period_days)
                compare_start = max_date - timedelta(days=(compare_idx + 1) * period_days - 1)
                compare_end = max_date - timedelta(days=compare_idx * period_days)
            
            # 筛选数据
            # 🔍 DEBUG: 检查日期列类型和数据分布
            if i == 0:  # 只在第一次打印
                print(f"[DEBUG] 日期列类型: {self.df['日期'].dtype}")
                print(f"[DEBUG] 日期列样本: {self.df['日期'].head(3).tolist()}")
                print(f"[DEBUG] current_start类型: {type(current_start)}, 值: {current_start}")
                print(f"[DEBUG] 数据中的唯一日期数: {self.df['日期'].dt.date.nunique()}")
                
            current_data = self.df[(self.df['日期'] >= current_start) & (self.df['日期'] <= current_end)]
            compare_data = self.df[(self.df['日期'] >= compare_start) & (self.df['日期'] <= compare_end)]
            
            # 🔍 DEBUG: 打印数据量
            print(f"[DEBUG] Period {i}: current={len(current_data)}, compare={len(compare_data)}, range=({current_start.date()} to {current_end.date()}) vs ({compare_start.date()} to {compare_end.date()})")
            
            if len(current_data) == 0 or len(compare_data) == 0:
                continue
            
            # 计算客单价
            def calc_price(data):
                if '订单ID' not in data.columns:
                    print(f"[DEBUG] Missing 订单ID column!")
                    return None
                orders = data.groupby('订单ID')['商品实售价'].sum()
                avg_price = orders.mean() if len(orders) > 0 else None
                print(f"[DEBUG] Orders={len(orders)}, AvgPrice={avg_price}")
                return avg_price
            
            current_price = calc_price(current_data)
            compare_price = calc_price(compare_data)
            
            # 跳过无效数据
            if current_price is None or compare_price is None or current_price == 0 or compare_price == 0:
                continue
            
            price_change = current_price - compare_price
            change_pct = (price_change / compare_price * 100)
            
            # 只保留下滑的周期
            if change_pct <= threshold:
                # 计算周期标签
                if time_period == 'week':
                    current_week = current_end.isocalendar()[1]
                    compare_week = compare_end.isocalendar()[1]
                    period_label = f'第{compare_week}周 vs 第{current_week}周'
                    current_col = f'第{current_week}周客单价'
                    compare_col = f'第{compare_week}周客单价'
                else:
                    # 按日分析：使用end日期（实际上start和end是同一天）
                    period_label = f'{compare_end:%m-%d} vs {current_end:%m-%d}'
                    current_col = f'{current_end:%m-%d}客单价'
                    compare_col = f'{compare_end:%m-%d}客单价'
                
                # 分析TOP5商品（已区分下滑和上涨）
                top_products_dict = self._get_top_declining_products_with_reason(
                    current_data=current_data, 
                    compare_data=compare_data, 
                    top_n=5
                )
                
                # 商品角色分布
                if '商品角色' in current_data.columns:
                    role_dist = current_data['商品角色'].value_counts()
                    role_str = ' | '.join([f"{k}:{v}单" for k, v in role_dist.items()])
                else:
                    role_str = '未知'
                    role_dist = pd.Series()
                
                results.append({
                    '对比周期': period_label,
                    '之前客单价': compare_price,  # 更直观：时间上更早的周期
                    '当前客单价': current_price,  # 更直观：时间上更新的周期
                    '客单价变化': price_change,
                    '变化幅度%': change_pct,
                    
                    # === 下滑商品TOP5 ===
                    # TOP1下滑商品
                    'TOP1下滑商品-商品名称': top_products_dict['下滑商品-商品名称'][0],
                    'TOP1下滑商品-分类': top_products_dict['下滑商品-分类'][0],
                    'TOP1下滑商品-当前单价': top_products_dict['下滑商品-当前单价'][0],
                    'TOP1下滑商品-之前单价': top_products_dict['下滑商品-之前单价'][0],
                    'TOP1下滑商品-单价变化': top_products_dict['下滑商品-单价变化'][0],
                    'TOP1下滑商品-销量变化': top_products_dict['下滑商品-销量变化'][0],
                    'TOP1下滑商品-问题原因': top_products_dict['下滑商品-问题原因'][0],
                    # TOP2下滑商品
                    'TOP2下滑商品-商品名称': top_products_dict['下滑商品-商品名称'][1],
                    'TOP2下滑商品-分类': top_products_dict['下滑商品-分类'][1],
                    'TOP2下滑商品-当前单价': top_products_dict['下滑商品-当前单价'][1],
                    'TOP2下滑商品-之前单价': top_products_dict['下滑商品-之前单价'][1],
                    'TOP2下滑商品-单价变化': top_products_dict['下滑商品-单价变化'][1],
                    'TOP2下滑商品-销量变化': top_products_dict['下滑商品-销量变化'][1],
                    'TOP2下滑商品-问题原因': top_products_dict['下滑商品-问题原因'][1],
                    # TOP3下滑商品
                    'TOP3下滑商品-商品名称': top_products_dict['下滑商品-商品名称'][2],
                    'TOP3下滑商品-分类': top_products_dict['下滑商品-分类'][2],
                    'TOP3下滑商品-当前单价': top_products_dict['下滑商品-当前单价'][2],
                    'TOP3下滑商品-之前单价': top_products_dict['下滑商品-之前单价'][2],
                    'TOP3下滑商品-单价变化': top_products_dict['下滑商品-单价变化'][2],
                    'TOP3下滑商品-销量变化': top_products_dict['下滑商品-销量变化'][2],
                    'TOP3下滑商品-问题原因': top_products_dict['下滑商品-问题原因'][2],
                    # TOP4下滑商品
                    'TOP4下滑商品-商品名称': top_products_dict['下滑商品-商品名称'][3],
                    'TOP4下滑商品-分类': top_products_dict['下滑商品-分类'][3],
                    'TOP4下滑商品-当前单价': top_products_dict['下滑商品-当前单价'][3],
                    'TOP4下滑商品-之前单价': top_products_dict['下滑商品-之前单价'][3],
                    'TOP4下滑商品-单价变化': top_products_dict['下滑商品-单价变化'][3],
                    'TOP4下滑商品-销量变化': top_products_dict['下滑商品-销量变化'][3],
                    'TOP4下滑商品-问题原因': top_products_dict['下滑商品-问题原因'][3],
                    # TOP5商品信息
                    # TOP5下滑商品
                    'TOP5下滑商品-商品名称': top_products_dict['下滑商品-商品名称'][4],
                    'TOP5下滑商品-分类': top_products_dict['下滑商品-分类'][4],
                    'TOP5下滑商品-当前单价': top_products_dict['下滑商品-当前单价'][4],
                    'TOP5下滑商品-之前单价': top_products_dict['下滑商品-之前单价'][4],
                    'TOP5下滑商品-单价变化': top_products_dict['下滑商品-单价变化'][4],
                    'TOP5下滑商品-销量变化': top_products_dict['下滑商品-销量变化'][4],
                    'TOP5下滑商品-问题原因': top_products_dict['下滑商品-问题原因'][4],
                    
                    # === 上涨商品TOP5 ===
                    # TOP1上涨商品
                    'TOP1上涨商品-商品名称': top_products_dict['上涨商品-商品名称'][0],
                    'TOP1上涨商品-分类': top_products_dict['上涨商品-分类'][0],
                    'TOP1上涨商品-当前单价': top_products_dict['上涨商品-当前单价'][0],
                    'TOP1上涨商品-之前单价': top_products_dict['上涨商品-之前单价'][0],
                    'TOP1上涨商品-单价变化': top_products_dict['上涨商品-单价变化'][0],
                    'TOP1上涨商品-销量变化': top_products_dict['上涨商品-销量变化'][0],
                    'TOP1上涨商品-增长原因': top_products_dict['上涨商品-增长原因'][0],
                    # TOP2上涨商品
                    'TOP2上涨商品-商品名称': top_products_dict['上涨商品-商品名称'][1],
                    'TOP2上涨商品-分类': top_products_dict['上涨商品-分类'][1],
                    'TOP2上涨商品-当前单价': top_products_dict['上涨商品-当前单价'][1],
                    'TOP2上涨商品-之前单价': top_products_dict['上涨商品-之前单价'][1],
                    'TOP2上涨商品-单价变化': top_products_dict['上涨商品-单价变化'][1],
                    'TOP2上涨商品-销量变化': top_products_dict['上涨商品-销量变化'][1],
                    'TOP2上涨商品-增长原因': top_products_dict['上涨商品-增长原因'][1],
                    # TOP3上涨商品
                    'TOP3上涨商品-商品名称': top_products_dict['上涨商品-商品名称'][2],
                    'TOP3上涨商品-分类': top_products_dict['上涨商品-分类'][2],
                    'TOP3上涨商品-当前单价': top_products_dict['上涨商品-当前单价'][2],
                    'TOP3上涨商品-之前单价': top_products_dict['上涨商品-之前单价'][2],
                    'TOP3上涨商品-单价变化': top_products_dict['上涨商品-单价变化'][2],
                    'TOP3上涨商品-销量变化': top_products_dict['上涨商品-销量变化'][2],
                    'TOP3上涨商品-增长原因': top_products_dict['上涨商品-增长原因'][2],
                    # TOP4上涨商品
                    'TOP4上涨商品-商品名称': top_products_dict['上涨商品-商品名称'][3],
                    'TOP4上涨商品-分类': top_products_dict['上涨商品-分类'][3],
                    'TOP4上涨商品-当前单价': top_products_dict['上涨商品-当前单价'][3],
                    'TOP4上涨商品-之前单价': top_products_dict['上涨商品-之前单价'][3],
                    'TOP4上涨商品-单价变化': top_products_dict['上涨商品-单价变化'][3],
                    'TOP4上涨商品-销量变化': top_products_dict['上涨商品-销量变化'][3],
                    'TOP4上涨商品-增长原因': top_products_dict['上涨商品-增长原因'][3],
                    # TOP5上涨商品
                    'TOP5上涨商品-商品名称': top_products_dict['上涨商品-商品名称'][4],
                    'TOP5上涨商品-分类': top_products_dict['上涨商品-分类'][4],
                    'TOP5上涨商品-当前单价': top_products_dict['上涨商品-当前单价'][4],
                    'TOP5上涨商品-之前单价': top_products_dict['上涨商品-之前单价'][4],
                    'TOP5上涨商品-单价变化': top_products_dict['上涨商品-单价变化'][4],
                    'TOP5上涨商品-销量变化': top_products_dict['上涨商品-销量变化'][4],
                    'TOP5上涨商品-增长原因': top_products_dict['上涨商品-增长原因'][4],
                    
                    # 其他信息
                    '商品角色分布': role_str,
                    '问题等级': '🔴 严重' if change_pct <= -10 else '🟠 警告',
                    '建议操作': self._generate_price_suggestion(change_pct, role_dist)
                })
        
        if len(results) == 0:
            return pd.DataFrame()
        
        result = pd.DataFrame(results)
        
        # 🔍 DEBUG: 查看格式化前的数据
        print(f"\n[DEBUG] 格式化前的DataFrame:")
        print(f"  列名: {result.columns.tolist()}")
        if len(result) > 0:
            first_row = result.iloc[0]
            print(f"  之前客单价: {first_row.get('之前客单价', 'N/A')}")
            print(f"  当前客单价: {first_row.get('当前客单价', 'N/A')}")
        
        # 数值格式化
        if '之前客单价' in result.columns:
            result['之前客单价'] = result['之前客单价'].apply(lambda x: f"¥{x:.1f}")
        
        if '当前客单价' in result.columns:
            result['当前客单价'] = result['当前客单价'].apply(lambda x: f"¥{x:.1f}")
        
        if '客单价变化' in result.columns:
            result['客单价变化'] = result['客单价变化'].apply(lambda x: f"¥{x:.1f}")
        
        if '变化幅度%' in result.columns:
            result['变化幅度%'] = result['变化幅度%'].apply(lambda x: f"{x:.1f}%")
        
        # 格式化下滑商品的价格字段
        for i in range(1, 6):
            prefix = f'TOP{i}下滑商品'
            if f'{prefix}-当前单价' in result.columns:
                result[f'{prefix}-当前单价'] = result[f'{prefix}-当前单价'].apply(
                    lambda x: f"¥{x:.1f}" if x > 0 else ''
                )
            if f'{prefix}-之前单价' in result.columns:
                result[f'{prefix}-之前单价'] = result[f'{prefix}-之前单价'].apply(
                    lambda x: f"¥{x:.1f}" if x > 0 else ''
                )
            if f'{prefix}-单价变化' in result.columns:
                result[f'{prefix}-单价变化'] = result[f'{prefix}-单价变化'].apply(
                    lambda x: f"¥{x:+.1f}" if x != 0 else ''
                )
            if f'{prefix}-销量变化' in result.columns:
                result[f'{prefix}-销量变化'] = result[f'{prefix}-销量变化'].apply(
                    lambda x: f"{x:+.0f}件" if x != 0 else ''
                )
        
        # 格式化上涨商品的价格字段
        for i in range(1, 6):
            prefix = f'TOP{i}上涨商品'
            if f'{prefix}-当前单价' in result.columns:
                result[f'{prefix}-当前单价'] = result[f'{prefix}-当前单价'].apply(
                    lambda x: f"¥{x:.1f}" if x > 0 else ''
                )
            if f'{prefix}-之前单价' in result.columns:
                result[f'{prefix}-之前单价'] = result[f'{prefix}-之前单价'].apply(
                    lambda x: f"¥{x:.1f}" if x > 0 else ''
                )
            if f'{prefix}-单价变化' in result.columns:
                result[f'{prefix}-单价变化'] = result[f'{prefix}-单价变化'].apply(
                    lambda x: f"¥{x:+.1f}" if x != 0 else ''
                )
            if f'{prefix}-销量变化' in result.columns:
                result[f'{prefix}-销量变化'] = result[f'{prefix}-销量变化'].apply(
                    lambda x: f"{x:+.0f}件" if x != 0 else ''
                )
        
        return result
    
    def _compare_two_periods_customer_price(self, time_period: str, threshold: float,
                                            max_date, current_idx: int, compare_idx: int) -> pd.DataFrame:
        """对比两个指定周期的客单价"""
        if time_period == 'week':
            period_days = 7
        else:
            period_days = 1
        
        # 计算周期范围
        current_start = max_date - timedelta(days=(current_idx + 1) * period_days - 1)
        current_end = max_date - timedelta(days=current_idx * period_days)
        compare_start = max_date - timedelta(days=(compare_idx + 1) * period_days - 1)
        compare_end = max_date - timedelta(days=compare_idx * period_days)
        
        # 计算标签
        if time_period == 'week':
            current_week = current_end.isocalendar()[1]
            compare_week = compare_end.isocalendar()[1]
            current_label = f'第{current_week}周'
            compare_label = f'第{compare_week}周'
        else:
            current_label = current_start.strftime('%Y-%m-%d')
            compare_label = compare_start.strftime('%Y-%m-%d')
        
        # 筛选两个周期的数据
        current_data = self.df[(self.df['日期'] >= current_start) & (self.df['日期'] <= current_end)]
        compare_data = self.df[(self.df['日期'] >= compare_start) & (self.df['日期'] <= compare_end)]
        
        if len(current_data) == 0 or len(compare_data) == 0:
            return pd.DataFrame()
        
        # 计算客单价
        def calc_price(data):
            if '订单ID' not in data.columns:
                return None
            orders = data.groupby('订单ID')['商品实售价'].sum()
            return orders.mean() if len(orders) > 0 else None
        
        current_price = calc_price(current_data)
        compare_price = calc_price(compare_data)
        
        # 检查数据有效性
        if current_price is None or compare_price is None or current_price == 0 or compare_price == 0:
            return pd.DataFrame()
        
        price_change = current_price - compare_price
        change_pct = (price_change / compare_price * 100)
        
        # 分析TOP5商品（带原因分析）
        top_products_dict = self._get_top_declining_products_with_reason(
            current_data=current_data,
            compare_data=compare_data,
            top_n=5
        )
        
        # 商品角色分布
        if '商品角色' in current_data.columns:
            role_dist = current_data['商品角色'].value_counts()
            role_str = ' | '.join([f"{k}:{v}单" for k, v in role_dist.items()])
        else:
            role_str = '未知'
            role_dist = pd.Series()
        
        # 组装结果
        result = pd.DataFrame([{
            '对比周期': f'{compare_label} vs {current_label}',
            '之前客单价': compare_price,
            '当前客单价': current_price,
            '客单价变化': price_change,
            '变化幅度%': change_pct,
            
            # === 下滑商品TOP5 ===
            # TOP1下滑商品
            'TOP1下滑商品-商品名称': top_products_dict['下滑商品-商品名称'][0],
            'TOP1下滑商品-分类': top_products_dict['下滑商品-分类'][0],
            'TOP1下滑商品-当前单价': top_products_dict['下滑商品-当前单价'][0],
            'TOP1下滑商品-之前单价': top_products_dict['下滑商品-之前单价'][0],
            'TOP1下滑商品-单价变化': top_products_dict['下滑商品-单价变化'][0],
            'TOP1下滑商品-销量变化': top_products_dict['下滑商品-销量变化'][0],
            'TOP1下滑商品-问题原因': top_products_dict['下滑商品-问题原因'][0],
            # TOP2下滑商品
            'TOP2下滑商品-商品名称': top_products_dict['下滑商品-商品名称'][1],
            'TOP2下滑商品-分类': top_products_dict['下滑商品-分类'][1],
            'TOP2下滑商品-当前单价': top_products_dict['下滑商品-当前单价'][1],
            'TOP2下滑商品-之前单价': top_products_dict['下滑商品-之前单价'][1],
            'TOP2下滑商品-单价变化': top_products_dict['下滑商品-单价变化'][1],
            'TOP2下滑商品-销量变化': top_products_dict['下滑商品-销量变化'][1],
            'TOP2下滑商品-问题原因': top_products_dict['下滑商品-问题原因'][1],
            # TOP3下滑商品
            'TOP3下滑商品-商品名称': top_products_dict['下滑商品-商品名称'][2],
            'TOP3下滑商品-分类': top_products_dict['下滑商品-分类'][2],
            'TOP3下滑商品-当前单价': top_products_dict['下滑商品-当前单价'][2],
            'TOP3下滑商品-之前单价': top_products_dict['下滑商品-之前单价'][2],
            'TOP3下滑商品-单价变化': top_products_dict['下滑商品-单价变化'][2],
            'TOP3下滑商品-销量变化': top_products_dict['下滑商品-销量变化'][2],
            'TOP3下滑商品-问题原因': top_products_dict['下滑商品-问题原因'][2],
            # TOP4下滑商品
            'TOP4下滑商品-商品名称': top_products_dict['下滑商品-商品名称'][3],
            'TOP4下滑商品-分类': top_products_dict['下滑商品-分类'][3],
            'TOP4下滑商品-当前单价': top_products_dict['下滑商品-当前单价'][3],
            'TOP4下滑商品-之前单价': top_products_dict['下滑商品-之前单价'][3],
            'TOP4下滑商品-单价变化': top_products_dict['下滑商品-单价变化'][3],
            'TOP4下滑商品-销量变化': top_products_dict['下滑商品-销量变化'][3],
            'TOP4下滑商品-问题原因': top_products_dict['下滑商品-问题原因'][3],
            # TOP5下滑商品
            'TOP5下滑商品-商品名称': top_products_dict['下滑商品-商品名称'][4],
            'TOP5下滑商品-分类': top_products_dict['下滑商品-分类'][4],
            'TOP5下滑商品-当前单价': top_products_dict['下滑商品-当前单价'][4],
            'TOP5下滑商品-之前单价': top_products_dict['下滑商品-之前单价'][4],
            'TOP5下滑商品-单价变化': top_products_dict['下滑商品-单价变化'][4],
            'TOP5下滑商品-销量变化': top_products_dict['下滑商品-销量变化'][4],
            'TOP5下滑商品-问题原因': top_products_dict['下滑商品-问题原因'][4],
            
            # === 上涨商品TOP5 ===
            # TOP1上涨商品
            'TOP1上涨商品-商品名称': top_products_dict['上涨商品-商品名称'][0],
            'TOP1上涨商品-分类': top_products_dict['上涨商品-分类'][0],
            'TOP1上涨商品-当前单价': top_products_dict['上涨商品-当前单价'][0],
            'TOP1上涨商品-之前单价': top_products_dict['上涨商品-之前单价'][0],
            'TOP1上涨商品-单价变化': top_products_dict['上涨商品-单价变化'][0],
            'TOP1上涨商品-销量变化': top_products_dict['上涨商品-销量变化'][0],
            'TOP1上涨商品-增长原因': top_products_dict['上涨商品-增长原因'][0],
            # TOP2上涨商品
            'TOP2上涨商品-商品名称': top_products_dict['上涨商品-商品名称'][1],
            'TOP2上涨商品-分类': top_products_dict['上涨商品-分类'][1],
            'TOP2上涨商品-当前单价': top_products_dict['上涨商品-当前单价'][1],
            'TOP2上涨商品-之前单价': top_products_dict['上涨商品-之前单价'][1],
            'TOP2上涨商品-单价变化': top_products_dict['上涨商品-单价变化'][1],
            'TOP2上涨商品-销量变化': top_products_dict['上涨商品-销量变化'][1],
            'TOP2上涨商品-增长原因': top_products_dict['上涨商品-增长原因'][1],
            # TOP3上涨商品
            'TOP3上涨商品-商品名称': top_products_dict['上涨商品-商品名称'][2],
            'TOP3上涨商品-分类': top_products_dict['上涨商品-分类'][2],
            'TOP3上涨商品-当前单价': top_products_dict['上涨商品-当前单价'][2],
            'TOP3上涨商品-之前单价': top_products_dict['上涨商品-之前单价'][2],
            'TOP3上涨商品-单价变化': top_products_dict['上涨商品-单价变化'][2],
            'TOP3上涨商品-销量变化': top_products_dict['上涨商品-销量变化'][2],
            'TOP3上涨商品-增长原因': top_products_dict['上涨商品-增长原因'][2],
            # TOP4上涨商品
            'TOP4上涨商品-商品名称': top_products_dict['上涨商品-商品名称'][3],
            'TOP4上涨商品-分类': top_products_dict['上涨商品-分类'][3],
            'TOP4上涨商品-当前单价': top_products_dict['上涨商品-当前单价'][3],
            'TOP4上涨商品-之前单价': top_products_dict['上涨商品-之前单价'][3],
            'TOP4上涨商品-单价变化': top_products_dict['上涨商品-单价变化'][3],
            'TOP4上涨商品-销量变化': top_products_dict['上涨商品-销量变化'][3],
            'TOP4上涨商品-增长原因': top_products_dict['上涨商品-增长原因'][3],
            # TOP5上涨商品
            'TOP5上涨商品-商品名称': top_products_dict['上涨商品-商品名称'][4],
            'TOP5上涨商品-分类': top_products_dict['上涨商品-分类'][4],
            'TOP5上涨商品-当前单价': top_products_dict['上涨商品-当前单价'][4],
            'TOP5上涨商品-之前单价': top_products_dict['上涨商品-之前单价'][4],
            'TOP5上涨商品-单价变化': top_products_dict['上涨商品-单价变化'][4],
            'TOP5上涨商品-销量变化': top_products_dict['上涨商品-销量变化'][4],
            'TOP5上涨商品-增长原因': top_products_dict['上涨商品-增长原因'][4],
            
            # 其他信息
            '商品角色分布': role_str,
            '问题等级': '🔴 严重' if change_pct <= -10 else '🟠 警告',
            '建议操作': self._generate_price_suggestion(change_pct, role_dist)
        }])
        
        # 数值格式化
        if '之前客单价' in result.columns:
            result['之前客单价'] = result['之前客单价'].apply(lambda x: f"¥{x:.1f}")
        
        if '当前客单价' in result.columns:
            result['当前客单价'] = result['当前客单价'].apply(lambda x: f"¥{x:.1f}")
        
        if '客单价变化' in result.columns:
            result['客单价变化'] = result['客单价变化'].apply(lambda x: f"¥{x:.1f}")
        
        if '变化幅度%' in result.columns:
            result['变化幅度%'] = result['变化幅度%'].apply(lambda x: f"{x:.1f}%")
        
        # 格式化下滑商品的价格字段
        for i in range(1, 6):
            prefix = f'TOP{i}下滑商品'
            if f'{prefix}-当前单价' in result.columns:
                result[f'{prefix}-当前单价'] = result[f'{prefix}-当前单价'].apply(
                    lambda x: f"¥{x:.1f}" if x > 0 else ''
                )
            if f'{prefix}-之前单价' in result.columns:
                result[f'{prefix}-之前单价'] = result[f'{prefix}-之前单价'].apply(
                    lambda x: f"¥{x:.1f}" if x > 0 else ''
                )
            if f'{prefix}-单价变化' in result.columns:
                result[f'{prefix}-单价变化'] = result[f'{prefix}-单价变化'].apply(
                    lambda x: f"¥{x:+.1f}" if x != 0 else ''
                )
            if f'{prefix}-销量变化' in result.columns:
                result[f'{prefix}-销量变化'] = result[f'{prefix}-销量变化'].apply(
                    lambda x: f"{x:+.0f}件" if x != 0 else ''
                )
        
        # 格式化上涨商品的价格字段
        for i in range(1, 6):
            prefix = f'TOP{i}上涨商品'
            if f'{prefix}-当前单价' in result.columns:
                result[f'{prefix}-当前单价'] = result[f'{prefix}-当前单价'].apply(
                    lambda x: f"¥{x:.1f}" if x > 0 else ''
                )
            if f'{prefix}-之前单价' in result.columns:
                result[f'{prefix}-之前单价'] = result[f'{prefix}-之前单价'].apply(
                    lambda x: f"¥{x:.1f}" if x > 0 else ''
                )
            if f'{prefix}-单价变化' in result.columns:
                result[f'{prefix}-单价变化'] = result[f'{prefix}-单价变化'].apply(
                    lambda x: f"¥{x:+.1f}" if x != 0 else ''
                )
            if f'{prefix}-销量变化' in result.columns:
                result[f'{prefix}-销量变化'] = result[f'{prefix}-销量变化'].apply(
                    lambda x: f"{x:+.0f}件" if x != 0 else ''
                )
        
        return result
    
    def _get_top_declining_products_with_reason(
        self, 
        current_data: pd.DataFrame, 
        compare_data: pd.DataFrame,
        top_n: int = 5
    ) -> dict:
        """
        获取TOP下滑商品详细信息,包含下滑原因分析
        
        Parameters:
        -----------
        current_data : pd.DataFrame
            当前周期数据
        compare_data : pd.DataFrame
            对比周期数据
        top_n : int
            返回TOP N个商品
            
        Returns:
        --------
        dict
            包含各列数据的字典:
            {
                '商品名称': [商品1, 商品2, ...],
                '分类': [分类1, 分类2, ...],
                '当前单价': [价格1, 价格2, ...],
                '之前单价': [价格1, 价格2, ...],
                '单价变化': [变化1, 变化2, ...],
                '销量变化': [变化1, 变化2, ...],
                '下滑原因': [原因1, 原因2, ...]
            }
        """
        # 统计当前期商品情况
        agg_dict_current = {
            '商品实售价': ['mean', 'sum', 'count'],
            '三级分类名': 'first' if '三级分类名' in current_data.columns else lambda x: '未知'
        }
        # 增加库存字段（如果存在）
        if '剩余库存' in current_data.columns:
            agg_dict_current['剩余库存'] = 'max'  # 取最大库存值（代表当天的库存状态）
        
        current_agg = current_data.groupby('商品名称').agg(agg_dict_current)
        
        if '剩余库存' in current_data.columns:
            current_agg.columns = ['当前单价', '当前销售额', '当前销量', '分类', '当前库存']
        else:
            current_agg.columns = ['当前单价', '当前销售额', '当前销量', '分类']
        
        # 统计对比期商品情况
        agg_dict_compare = {
            '商品实售价': ['mean', 'sum', 'count']
        }
        # 增加库存字段（如果存在）
        if '剩余库存' in compare_data.columns:
            agg_dict_compare['剩余库存'] = 'max'
        
        compare_agg = compare_data.groupby('商品名称').agg(agg_dict_compare)
        
        if '剩余库存' in compare_data.columns:
            compare_agg.columns = ['之前单价', '之前销售额', '之前销量', '之前库存']
        else:
            compare_agg.columns = ['之前单价', '之前销售额', '之前销量']
        
        # 合并数据
        merged = current_agg.join(compare_agg, how='outer').fillna(0)
        
        # 计算变化
        merged['销售额变化'] = merged['当前销售额'] - merged['之前销售额']
        merged['销量变化'] = merged['当前销量'] - merged['之前销量']
        merged['单价变化'] = merged['当前单价'] - merged['之前单价']
        merged['单价变化率'] = ((merged['当前单价'] - merged['之前单价']) / merged['之前单价'] * 100).fillna(0)
        
        # 分析下滑原因
        def analyze_reason(row):
            """
            分析商品变化原因，返回(诊断结果, 变化类型)
            
            变化类型:
            - '下滑': 需要关注的问题商品
            - '上涨': 表现良好的商品
            - '正常': 无明显变化
            - '状态': 特殊状态说明
            """
            # 优先级1: 使用库存判定售罄（如果有库存字段）
            if '当前库存' in row.index and '之前库存' in row.index:
                # 标准售罄判定
                if row['当前库存'] == 0 and row['之前库存'] > 0:
                    return "🔴售罄", "下滑"
                
                # 🆕 特殊情况: 低频商品售罄
                # 场景: 之前无订单记录(销量0库存0)，但当前有销售且库存变0
                # 例如: 28寸行李箱整月只卖1件，之前无订单记录，卖出后库存为0
                elif (row['当前库存'] == 0 and 
                      row['之前库存'] == 0 and 
                      row['当前销量'] > 0 and 
                      row['之前销量'] == 0):
                    return "🔴售罄", "下滑"  # 低频商品售罄
                
                # 真正的已下架: 连续无库存无销量
                elif row['当前库存'] == 0:
                    return "⚪已下架", "状态"
                
                # 滞销预警：有库存但连续无销量
                elif row['当前库存'] > 0 and row['当前销量'] == 0 and row['之前销量'] == 0:
                    return "⚠️滞销预警", "下滑"
                # 库存不足预警：库存很少且销量下降
                elif row['当前库存'] > 0 and row['当前库存'] < 5 and row['销量变化'] < 0:
                    return "⚠️库存不足", "下滑"
            else:
                # 如果没有库存字段，降级使用销量判定（不理想但可用）
                if row['当前销量'] == 0 and row['之前销量'] > 0:
                    return "🔴疑似售罄(无库存数据)", "下滑"
                elif row['当前销量'] == 0:
                    return "⚪新品或下架", "状态"
            
            # 优先级2: 涨价相关
            if row['单价变化率'] > 5:
                if row['销量变化'] < 0:
                    return "💰涨价导致销量降", "下滑"
                else:
                    return "💰涨价(销量增)", "上涨"  # 表现良好
            # 优先级3: 降价相关
            elif row['单价变化率'] < -5:
                if row['销量变化'] < 0:
                    return "💸降价仍降量", "下滑"
                else:
                    return "💸降价促销成功", "上涨"  # 表现良好
            # 优先级4: 销量大幅下滑
            elif row['销量变化'] < -row['之前销量'] * 0.3:  # 销量下降>30%
                return "📉销量大幅下滑", "下滑"
            # 优先级5: 销量小幅下滑
            elif row['销量变化'] < 0:
                return "📉销量小幅下滑", "下滑"
            # 优先级6: 销量增长
            elif row['销量变化'] > 0:
                return "📈销量增长", "上涨"  # 表现良好
            else:
                return "✅正常", "正常"
        
        # 应用分析函数，拆分结果和分类
        analysis_results = merged.apply(analyze_reason, axis=1)
        merged['诊断结果'] = analysis_results.apply(lambda x: x[0])
        merged['变化类型'] = analysis_results.apply(lambda x: x[1])
        
        # 分别获取下滑商品和上涨商品
        declining_products = merged[
            (merged['变化类型'] == '下滑') & (merged['当前销售额'] > 0)
        ].sort_values('销售额变化', ascending=True).head(top_n)  # 按下滑幅度排序
        
        rising_products = merged[
            (merged['变化类型'] == '上涨') & (merged['当前销售额'] > 0)
        ].sort_values('销售额变化', ascending=False).head(top_n)  # 按增长幅度排序
        
        # 构造结果字典 - 包含下滑和上涨两部分
        result_dict = {
            # 下滑商品部分
            '下滑商品-商品名称': [],
            '下滑商品-分类': [],
            '下滑商品-当前单价': [],
            '下滑商品-之前单价': [],
            '下滑商品-单价变化': [],
            '下滑商品-销量变化': [],
            '下滑商品-问题原因': [],
            # 上涨商品部分
            '上涨商品-商品名称': [],
            '上涨商品-分类': [],
            '上涨商品-当前单价': [],
            '上涨商品-之前单价': [],
            '上涨商品-单价变化': [],
            '上涨商品-销量变化': [],
            '上涨商品-增长原因': []
        }
        
        # 填充下滑商品数据
        for prod_name, row in declining_products.iterrows():
            result_dict['下滑商品-商品名称'].append(prod_name)
            result_dict['下滑商品-分类'].append(row['分类'] if row['分类'] != '未知' else '')
            result_dict['下滑商品-当前单价'].append(row['当前单价'])
            result_dict['下滑商品-之前单价'].append(row['之前单价'])
            result_dict['下滑商品-单价变化'].append(row['单价变化'])
            result_dict['下滑商品-销量变化'].append(row['销量变化'])
            result_dict['下滑商品-问题原因'].append(row['诊断结果'])
        
        # 补齐下滑商品到top_n个
        while len(result_dict['下滑商品-商品名称']) < top_n:
            result_dict['下滑商品-商品名称'].append('')
            result_dict['下滑商品-分类'].append('')
            result_dict['下滑商品-当前单价'].append(0)
            result_dict['下滑商品-之前单价'].append(0)
            result_dict['下滑商品-单价变化'].append(0)
            result_dict['下滑商品-销量变化'].append(0)
            result_dict['下滑商品-问题原因'].append('')
        
        # 填充上涨商品数据
        for prod_name, row in rising_products.iterrows():
            result_dict['上涨商品-商品名称'].append(prod_name)
            result_dict['上涨商品-分类'].append(row['分类'] if row['分类'] != '未知' else '')
            result_dict['上涨商品-当前单价'].append(row['当前单价'])
            result_dict['上涨商品-之前单价'].append(row['之前单价'])
            result_dict['上涨商品-单价变化'].append(row['单价变化'])
            result_dict['上涨商品-销量变化'].append(row['销量变化'])
            result_dict['上涨商品-增长原因'].append(row['诊断结果'])
        
        # 补齐上涨商品到top_n个
        while len(result_dict['上涨商品-商品名称']) < top_n:
            result_dict['上涨商品-商品名称'].append('')
            result_dict['上涨商品-分类'].append('')
            result_dict['上涨商品-当前单价'].append(0)
            result_dict['上涨商品-之前单价'].append(0)
            result_dict['上涨商品-单价变化'].append(0)
            result_dict['上涨商品-销量变化'].append(0)
            result_dict['上涨商品-增长原因'].append('')
        
        return result_dict
    
    def _get_top_declining_products(self, data: pd.DataFrame, top_n: int = 5) -> list:
        """获取TOP商品列表（返回列表便于展示）- 保留向后兼容"""
        # 统计商品购买情况
        agg_dict = {'商品实售价': ['mean', 'sum', 'count']}
        
        # 动态添加字段
        if '一级分类名' in data.columns:
            agg_dict['一级分类名'] = 'first'
        if '三级分类名' in data.columns:
            agg_dict['三级分类名'] = 'first'
        if '店内码' in data.columns:
            agg_dict['店内码'] = 'first'
        if '渠道' in data.columns:
            agg_dict['渠道'] = 'first'
        if '商品角色' in data.columns:
            agg_dict['商品角色'] = lambda x: x.mode()[0] if len(x.mode()) > 0 else '未知'
        
        products = data.groupby('商品名称').agg(agg_dict)
        
        # 设置列名
        base_cols = ['平均单价', '总销售额', '销量']
        extra_cols = []
        if '一级分类名' in data.columns:
            extra_cols.append('一级分类名')
        if '三级分类名' in data.columns:
            extra_cols.append('三级分类名')
        if '店内码' in data.columns:
            extra_cols.append('店内码')
        if '渠道' in data.columns:
            extra_cols.append('渠道')
        if '商品角色' in data.columns:
            extra_cols.append('商品角色')
        
        products.columns = base_cols + extra_cols
        products = products.sort_values('总销售额', ascending=False).head(top_n)
        
        # 生成列表（每个商品一个字符串）
        result_list = []
        for prod_name, row in products.iterrows():
            # 格式：【分类】商品名(¥单价)
            category = f"【{row.get('一级分类名', '未知')}】" if '一级分类名' in row else ""
            prod_str = f"{category}{prod_name}(¥{row['平均单价']:.1f})"
            result_list.append(prod_str)
        
        # 补齐到top_n个，不足的填空字符串
        while len(result_list) < top_n:
            result_list.append('')
        
        return result_list[:top_n]
    
    def diagnose_negative_margin_products(self) -> pd.DataFrame:
        """
        诊断负毛利商品
        
        Returns:
        --------
        pd.DataFrame
            负毛利商品预警表
        """
        if '单品毛利率' not in self.df.columns:
            return pd.DataFrame()
        
        # 筛选负毛利商品
        negative = self.df[self.df['单品毛利率'] < 0].copy()
        
        if len(negative) == 0:
            return pd.DataFrame()
        
        # 按商品聚合 - 动态构建聚合字典
        agg_dict_negative = {
            '商品实售价': 'mean',
            '单品毛利率': 'mean',
            '单品毛利': 'sum',
            '订单ID': 'count'
        }
        
        # 添加分类信息
        if '一级分类名' in negative.columns:
            agg_dict_negative['一级分类名'] = 'first'
        
        if '三级分类名' in negative.columns:
            agg_dict_negative['三级分类名'] = 'first'
        
        # 可选列
        if '商品角色' in negative.columns:
            agg_dict_negative['商品角色'] = lambda x: x.mode()[0] if len(x.mode()) > 0 else '未知'
        
        if '时段' in negative.columns:
            agg_dict_negative['时段'] = lambda x: ', '.join(x.value_counts().head(2).index.tolist())
        
        if '场景' in negative.columns:
            agg_dict_negative['场景'] = lambda x: ', '.join(x.value_counts().head(2).index.tolist())
        
        # 修改：按商品名称分组
        # 修改：按商品名称分组
        result = negative.groupby('商品名称').agg(agg_dict_negative).reset_index()
        
        # 动态设置列名 - 保留商品名称，并添加分类信息
        columns = ['商品名称', '平均售价', '平均毛利率%', '累计亏损额', '亏损订单数']
        if '一级分类名' in negative.columns:
            columns.append('一级分类名')
        if '三级分类名' in negative.columns:
            columns.append('三级分类名')
        if '商品角色' in negative.columns:
            columns.append('商品角色')
        if '时段' in negative.columns:
            columns.append('主要时段')
        if '场景' in negative.columns:
            columns.append('主要场景')
        
        result.columns = columns
        
        result = result.sort_values('累计亏损额')
        
        # 添加问题诊断
        result['问题等级'] = result['累计亏损额'].apply(
            lambda x: '🔴 严重' if x <= -100 else ('🟠 警告' if x <= -50 else '🟡 关注')
        )
        
        result['建议操作'] = result.apply(
            lambda row: f"立即调价或下架（已亏损¥{abs(row['累计亏损额']):.1f}）" 
            if row['累计亏损额'] <= -100 
            else "检查成本核算，考虑涨价",
            axis=1
        )
        
        # 🎨 格式化数值显示
        # 价格 - 保留1位小数
        if '平均售价' in result.columns:
            result['平均售价'] = result['平均售价'].apply(lambda x: f"¥{x:.1f}" if pd.notna(x) else "N/A")
        
        # 百分比 - 保留1位小数并添加%符号
        if '平均毛利率%' in result.columns:
            result['平均毛利率%'] = result['平均毛利率%'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
        
        # 金额 - 保留1位小数
        if '累计亏损额' in result.columns:
            result['累计亏损额'] = result['累计亏损额'].apply(lambda x: f"¥{x:.1f}" if pd.notna(x) else "N/A")
        
        # 订单数 - 整数
        if '亏损订单数' in result.columns:
            result['亏损订单数'] = result['亏损订单数'].fillna(0).astype(int)
        
        # 分类信息 - 填充缺失值
        if '一级分类名' in result.columns:
            result['一级分类名'] = result['一级分类名'].fillna('未分类')
        
        if '三级分类名' in result.columns:
            result['三级分类名'] = result['三级分类名'].fillna('未分类')
        
        return result
    
    def diagnose_high_delivery_fee_orders(self, threshold: float = 20.0) -> pd.DataFrame:
        """
        诊断高配送费订单
        
        Parameters:
        -----------
        threshold : float
            配送费占比阈值（百分比）
        
        Returns:
        --------
        pd.DataFrame
            高配送费订单分析表
        """
        if '配送费占比' not in self.df.columns or '收货地址' not in self.df.columns:
            return pd.DataFrame()
        
        # 筛选高配送费订单
        high_fee = self.df[self.df['配送费占比'] >= threshold].copy()
        
        if len(high_fee) == 0:
            return pd.DataFrame()
        
        # 按地址聚合（去重）
        result = high_fee.groupby('收货地址').agg({
            '订单ID': 'nunique',
            '商品实售价': 'sum',
            '物流配送费': 'mean',
            '配送费占比': 'mean',
            '配送距离': 'mean',
            '三级分类名': lambda x: ', '.join(x.value_counts().head(3).index.tolist())
        }).reset_index()
        
        result.columns = ['收货地址', '订单次数', '累计销售额', '平均配送费', 
                         '平均配送费占比%', '平均配送距离', '主要商品']
        
        result = result.sort_values('订单次数', ascending=False)
        
        # 添加优化建议
        result['建议操作'] = result.apply(
            lambda row: f"引导满减凑单（当前¥{row['累计销售额']/row['订单次数']:.1f}/单）" 
            if row['累计销售额']/row['订单次数'] < 30 
            else "推荐大件组合，提升客单价",
            axis=1
        )
        
        return result
    
    def diagnose_product_role_imbalance(self) -> pd.DataFrame:
        """
        诊断流量品&利润品失衡
        
        Returns:
        --------
        pd.DataFrame
            商品角色失衡诊断表
        """
        if '商品角色' not in self.df.columns:
            return pd.DataFrame()
        
        # 按场景（或时段）统计商品角色分布
        group_col = '场景' if '场景' in self.df.columns else '时段'
        
        if group_col not in self.df.columns:
            return pd.DataFrame()
        
        # 统计各场景的商品角色分布
        role_dist = self.df.groupby([group_col, '商品角色']).size().unstack(fill_value=0)
        role_dist['总订单数'] = role_dist.sum(axis=1)
        
        # 计算占比
        for col in role_dist.columns:
            if col != '总订单数':
                role_dist[f'{col}占比%'] = (role_dist[col] / role_dist['总订单数'] * 100).round(2)
        
        # 识别失衡场景（流量品占比>70%或利润品占比<15%）
        imbalanced = []
        for scene in role_dist.index:
            traffic_ratio = role_dist.loc[scene, '流量品占比%'] if '流量品占比%' in role_dist.columns else 0
            profit_ratio = role_dist.loc[scene, '利润品占比%'] if '利润品占比%' in role_dist.columns else 0
            
            if traffic_ratio > 70:
                imbalanced.append({
                    '场景/时段': scene,
                    '流量品占比%': traffic_ratio,
                    '利润品占比%': profit_ratio,
                    '总订单数': role_dist.loc[scene, '总订单数'],
                    '问题类型': '流量品过多',
                    '问题等级': '🟠 警告',
                    '建议操作': '增加利润品推荐，优化商品组合'
                })
            elif profit_ratio < 15 and role_dist.loc[scene, '总订单数'] > 50:
                imbalanced.append({
                    '场景/时段': scene,
                    '流量品占比%': traffic_ratio,
                    '利润品占比%': profit_ratio,
                    '总订单数': role_dist.loc[scene, '总订单数'],
                    '问题类型': '利润品不足',
                    '问题等级': '🟡 关注',
                    '建议操作': '在流量品页面关联推荐利润品'
                })
        
        return pd.DataFrame(imbalanced)
    
    def diagnose_abnormal_fluctuation(self, threshold: float = 50.0) -> pd.DataFrame:
        """
        诊断异常波动商品（爆单或滞销）
        
        Parameters:
        -----------
        threshold : float
            波动阈值（环比变化百分比）
        
        Returns:
        --------
        pd.DataFrame
            异常波动商品表
        """
        if '周' not in self.df.columns or '三级分类名' not in self.df.columns:
            return pd.DataFrame()
        
        # 按周统计商品销量
        weekly_sales = self.df.groupby(['周', '三级分类名']).size().unstack(fill_value=0)
        
        # 计算环比变化
        pct_change = weekly_sales.pct_change(axis=0) * 100
        
        # 识别最近一周的异常商品
        if len(pct_change) < 2:
            return pd.DataFrame()
        
        latest_week = pct_change.index[-1]
        latest_changes = pct_change.loc[latest_week]
        
        # 筛选异常商品
        abnormal = latest_changes[(latest_changes >= threshold) | (latest_changes <= -threshold)]
        
        if len(abnormal) == 0:
            return pd.DataFrame()
        
        result = pd.DataFrame({
            '商品名称': abnormal.index,
            '环比变化%': abnormal.values,
            '上周销量': weekly_sales.loc[weekly_sales.index[-2], abnormal.index].values,
            '本周销量': weekly_sales.loc[latest_week, abnormal.index].values
        })
        
        result['异常类型'] = result['环比变化%'].apply(
            lambda x: '📈 爆单' if x > 0 else '📉 滞销'
        )
        
        result['问题等级'] = result['环比变化%'].apply(
            lambda x: '🔴 严重' if abs(x) >= 80 else '🟠 警告'
        )
        
        result['建议操作'] = result.apply(
            lambda row: "增加库存备货，避免缺货" if row['环比变化%'] > 0 
            else "检查原因：价格/库存/竞品？考虑促销",
            axis=1
        )
        
        return result.sort_values('环比变化%', key=abs, ascending=False)
    
    def generate_comprehensive_report(self, output_path: Optional[str] = None) -> Dict:
        """
        生成综合问题诊断报告（Excel格式）
        
        Parameters:
        -----------
        output_path : str, optional
            输出文件路径，不指定则返回字典
        
        Returns:
        --------
        Dict
            包含所有诊断结果的字典
        """
        print("🔍 开始生成综合问题诊断报告...")
        
        report = {
            '销量下滑商品': self.diagnose_sales_decline(),
            '客单价下滑归因': self.diagnose_customer_price_decline(),
            '负毛利商品预警': self.diagnose_negative_margin_products(),
            '高配送费订单': self.diagnose_high_delivery_fee_orders(),
            '商品角色失衡': self.diagnose_product_role_imbalance(),
            '异常波动商品': self.diagnose_abnormal_fluctuation()
        }
        
        # 生成摘要
        summary = self._generate_summary(report)
        report['诊断摘要'] = summary
        
        # 导出Excel
        if output_path:
            self._export_to_excel(report, output_path)
            print(f"✅ 报告已导出: {output_path}")
        
        return report
    
    def _generate_summary(self, report: Dict) -> pd.DataFrame:
        """生成诊断摘要"""
        summary_data = []
        
        for sheet_name, df in report.items():
            if isinstance(df, pd.DataFrame) and len(df) > 0:
                problem_count = len(df)
                severity = df['问题等级'].value_counts().to_dict() if '问题等级' in df.columns else {}
                
                summary_data.append({
                    '问题类别': sheet_name,
                    '问题数量': problem_count,
                    '严重': severity.get('🔴 严重', 0),
                    '警告': severity.get('🟠 警告', 0),
                    '关注': severity.get('🟡 关注', 0),
                    '状态': '🔴 需立即处理' if severity.get('🔴 严重', 0) > 0 else '🟠 建议优化'
                })
        
        return pd.DataFrame(summary_data)
    
    def _export_to_excel(self, report: Dict, output_path: str):
        """导出Excel报告"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 先写摘要
            if '诊断摘要' in report:
                report['诊断摘要'].to_excel(writer, sheet_name='诊断摘要', index=False)
            
            # 写入各诊断表
            for sheet_name, df in report.items():
                if sheet_name != '诊断摘要' and isinstance(df, pd.DataFrame) and len(df) > 0:
                    df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    
    def _generate_decline_suggestion(self, row) -> str:
        """生成销量下滑建议（安全访问可选字段）"""
        # 安全获取商品角色字段
        product_role = row.get('商品角色', '未知')
        
        if product_role == '流量品':
            return "流量品下滑！检查库存&价格，考虑促销活动"
        elif product_role == '利润品':
            return "利润品下滑！分析竞品，优化推荐位置"
        else:
            return "分析原因：季节性？竞品？库存？"
    
    def _generate_price_suggestion(self, change_pct: float, role_dist: pd.Series) -> str:
        """生成客单价下滑建议"""
        if '流量品' in role_dist.index and role_dist['流量品'] / role_dist.sum() > 0.7:
            return "流量品占比过高，增加利润品推荐"
        elif change_pct <= -10:
            return "客单价大幅下滑，推出满减活动引导凑单"
        else:
            return "优化商品组合，推荐高价值商品"


# 测试代码
if __name__ == "__main__":
    # 示例：加载数据并运行诊断
    print("问题诊断引擎加载成功！")
    print("可用诊断功能：")
    print("  1. diagnose_sales_decline() - 销量下滑诊断")
    print("  2. diagnose_customer_price_decline() - 客单价归因分析")
    print("  3. diagnose_negative_margin_products() - 负毛利预警")
    print("  4. diagnose_high_delivery_fee_orders() - 高配送费诊断")
    print("  5. diagnose_product_role_imbalance() - 商品角色失衡")
    print("  6. diagnose_abnormal_fluctuation() - 异常波动预警")
    print("  7. generate_comprehensive_report() - 生成综合报告")
