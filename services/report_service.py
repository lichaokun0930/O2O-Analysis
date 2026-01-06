# -*- coding: utf-8 -*-
"""
报表导出服务

提供报表导出相关的功能：
- Excel导出
- CSV导出
- PDF报告生成
- 定时报表

版本: v1.0
创建日期: 2026-01-05
"""

import os
import io
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, date, timedelta

from .base_service import BaseService
from .cache.cache_keys import CacheKeys


class ReportService(BaseService):
    """
    报表导出服务
    
    提供各种格式的报表导出功能
    """
    
    def __init__(self, data_loader=None, cache_manager=None, output_dir: str = './reports'):
        super().__init__(cache_manager)
        self.data_loader = data_loader
        self.output_dir = output_dir
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
    
    # ==================== Excel导出 ====================
    
    def export_to_excel(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        filename: str = None,
        sheet_name: str = 'Sheet1',
        return_buffer: bool = False
    ) -> Dict[str, Any]:
        """
        导出数据到Excel
        
        Args:
            data: DataFrame或{sheet_name: DataFrame}字典
            filename: 文件名（不含路径）
            sheet_name: 单DataFrame时的工作表名
            return_buffer: 是否返回内存缓冲区（用于Web下载）
        
        Returns:
            导出结果
        """
        try:
            if filename is None:
                filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # 创建Excel写入器
            buffer = io.BytesIO() if return_buffer else None
            output = buffer if return_buffer else filepath
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if isinstance(data, pd.DataFrame):
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
                elif isinstance(data, dict):
                    for name, df in data.items():
                        if isinstance(df, pd.DataFrame):
                            df.to_excel(writer, sheet_name=name[:31], index=False)  # Excel限制31字符
                else:
                    return {'error': '不支持的数据类型'}
            
            if return_buffer:
                buffer.seek(0)
                return {
                    'success': True,
                    'buffer': buffer,
                    'filename': filename,
                    'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                }
            else:
                return {
                    'success': True,
                    'filepath': filepath,
                    'filename': filename
                }
                
        except Exception as e:
            return self.handle_error(e, "Excel导出失败")
    
    # ==================== CSV导出 ====================
    
    def export_to_csv(
        self,
        data: pd.DataFrame,
        filename: str = None,
        encoding: str = 'utf-8-sig',  # 支持中文的UTF-8
        return_buffer: bool = False
    ) -> Dict[str, Any]:
        """
        导出数据到CSV
        
        Args:
            data: DataFrame
            filename: 文件名
            encoding: 编码
            return_buffer: 是否返回内存缓冲区
        
        Returns:
            导出结果
        """
        try:
            if not isinstance(data, pd.DataFrame):
                return {'error': '数据必须是DataFrame'}
            
            if filename is None:
                filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            if return_buffer:
                buffer = io.StringIO()
                data.to_csv(buffer, index=False, encoding=encoding)
                buffer.seek(0)
                
                return {
                    'success': True,
                    'buffer': buffer,
                    'filename': filename,
                    'content_type': 'text/csv'
                }
            else:
                filepath = os.path.join(self.output_dir, filename)
                data.to_csv(filepath, index=False, encoding=encoding)
                
                return {
                    'success': True,
                    'filepath': filepath,
                    'filename': filename
                }
                
        except Exception as e:
            return self.handle_error(e, "CSV导出失败")
    
    # ==================== 订单报表 ====================
    
    def generate_order_report(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        format: str = 'excel'
    ) -> Dict[str, Any]:
        """
        生成订单报表
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店筛选
            start_date: 开始日期
            end_date: 结束日期
            format: 导出格式（excel/csv）
        
        Returns:
            报表导出结果
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            # 应用筛选
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            date_col = self.get_date_column(data)
            if date_col:
                data[date_col] = pd.to_datetime(data[date_col])
                if start_date:
                    data = data[data[date_col].dt.date >= start_date]
                if end_date:
                    data = data[data[date_col].dt.date <= end_date]
            
            # 聚合到订单级
            order_data = self.aggregate_to_order_level(data)
            
            # 选择导出字段
            export_columns = ['订单ID']
            if date_col and date_col in order_data.columns:
                export_columns.append(date_col)
            for col in ['门店名称', '商品名称', '实收价格', '订单实际利润', '物流配送费', '平台', '渠道']:
                if col in order_data.columns:
                    export_columns.append(col)
            
            export_data = order_data[export_columns].copy()
            
            # 格式化日期
            if date_col in export_data.columns:
                export_data[date_col] = export_data[date_col].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 生成文件名
            date_range = ''
            if start_date and end_date:
                date_range = f"_{start_date}_{end_date}"
            elif start_date:
                date_range = f"_from_{start_date}"
            
            filename = f"订单报表{date_range}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if format == 'csv':
                return self.export_to_csv(export_data, filename=f"{filename}.csv")
            else:
                return self.export_to_excel(export_data, filename=f"{filename}.xlsx", sheet_name='订单明细')
                
        except Exception as e:
            return self.handle_error(e, "生成订单报表失败")
    
    # ==================== 诊断报表 ====================
    
    def generate_diagnosis_report(
        self,
        df: pd.DataFrame,
        diagnosis_service=None,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成诊断报表
        
        包含：穿底订单、高配送费订单、滞销商品等
        
        Args:
            df: 订单数据DataFrame
            diagnosis_service: 诊断服务实例
            store_name: 门店筛选
        
        Returns:
            报表导出结果
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            sheets = {}
            
            # 聚合到订单级
            order_data = self.aggregate_to_order_level(df)
            
            # 1. 穿底订单
            if '订单实际利润' in order_data.columns:
                overflow = order_data[order_data['订单实际利润'] < 0].copy()
                overflow['亏损金额'] = abs(overflow['订单实际利润'])
                overflow = overflow.sort_values('亏损金额', ascending=False)
                sheets['穿底订单'] = overflow.head(100)
            
            # 2. 高配送费订单
            if '物流配送费' in order_data.columns:
                high_delivery = order_data[order_data['物流配送费'] > 6].copy()
                high_delivery = high_delivery.sort_values('物流配送费', ascending=False)
                sheets['高配送费订单'] = high_delivery.head(100)
            
            # 3. 汇总统计
            summary_data = {
                '指标': ['总订单数', '穿底订单数', '高配送费订单数', '总销售额', '总利润'],
                '数值': [
                    len(order_data),
                    len(sheets.get('穿底订单', pd.DataFrame())),
                    len(sheets.get('高配送费订单', pd.DataFrame())),
                    round(order_data['实收价格'].sum(), 2) if '实收价格' in order_data.columns else 0,
                    round(order_data['订单实际利润'].sum(), 2) if '订单实际利润' in order_data.columns else 0,
                ]
            }
            sheets['汇总统计'] = pd.DataFrame(summary_data)
            
            filename = f"诊断报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            return self.export_to_excel(sheets, filename=filename)
            
        except Exception as e:
            return self.handle_error(e, "生成诊断报表失败")
    
    # ==================== 商品报表 ====================
    
    def generate_product_report(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None,
        top_n: int = 100
    ) -> Dict[str, Any]:
        """
        生成商品报表
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店筛选
            top_n: 商品数量
        
        Returns:
            报表导出结果
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            # 商品聚合
            group_key = self.get_product_group_key(data)
            sales_col = self.get_sales_column(data)
            
            agg_dict = {}
            if group_key != '商品名称':
                agg_dict['商品名称'] = ('商品名称', 'first')
            agg_dict['销量'] = (sales_col, 'sum') if sales_col in data.columns else ('订单ID', 'count')
            
            if '实收价格' in data.columns:
                agg_dict['销售额'] = ('实收价格', 'sum')
            if '利润额' in data.columns:
                agg_dict['利润额'] = ('利润额', 'sum')
            if '商品采购成本' in data.columns:
                agg_dict['成本'] = ('商品采购成本', 'sum')
            
            product_stats = data.groupby(group_key).agg(**agg_dict).reset_index()
            
            # 计算毛利率
            if '销售额' in product_stats.columns:
                if '成本' in product_stats.columns:
                    product_stats['毛利率'] = (
                        (product_stats['销售额'] - product_stats['成本']) / product_stats['销售额'] * 100
                    ).round(2)
                elif '利润额' in product_stats.columns:
                    product_stats['毛利率'] = (
                        product_stats['利润额'] / product_stats['销售额'] * 100
                    ).round(2)
            
            # 排序
            product_stats = product_stats.sort_values('销量', ascending=False).head(top_n)
            
            filename = f"商品报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            return self.export_to_excel(product_stats, filename=filename, sheet_name='商品统计')
            
        except Exception as e:
            return self.handle_error(e, "生成商品报表失败")
    
    # ==================== 综合报表 ====================
    
    def generate_comprehensive_report(
        self,
        df: pd.DataFrame,
        store_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成综合报表
        
        包含：KPI汇总、订单明细、商品排行、诊断数据等多个工作表
        
        Args:
            df: 订单数据DataFrame
            store_name: 门店筛选
        
        Returns:
            报表导出结果
        """
        try:
            if df is None or df.empty:
                return {'error': '无数据'}
            
            data = df.copy()
            
            if store_name and '门店名称' in data.columns:
                data = data[data['门店名称'] == store_name]
            
            sheets = {}
            
            # 1. KPI汇总
            order_data = self.aggregate_to_order_level(data)
            kpi_data = {
                '指标': [
                    '总订单数',
                    '总销售额',
                    '总利润',
                    '平均客单价',
                    '平均利润率',
                    '穿底订单数',
                    '穿底率',
                    '高配送费订单数'
                ],
                '数值': [
                    len(order_data),
                    round(order_data['实收价格'].sum(), 2) if '实收价格' in order_data.columns else 0,
                    round(order_data['订单实际利润'].sum(), 2) if '订单实际利润' in order_data.columns else 0,
                    round(order_data['实收价格'].mean(), 2) if '实收价格' in order_data.columns else 0,
                    round(order_data['订单实际利润'].sum() / order_data['实收价格'].sum() * 100, 2) if '实收价格' in order_data.columns and order_data['实收价格'].sum() > 0 else 0,
                    int((order_data['订单实际利润'] < 0).sum()) if '订单实际利润' in order_data.columns else 0,
                    round((order_data['订单实际利润'] < 0).mean() * 100, 2) if '订单实际利润' in order_data.columns else 0,
                    int((order_data['物流配送费'] > 6).sum()) if '物流配送费' in order_data.columns else 0
                ]
            }
            sheets['KPI汇总'] = pd.DataFrame(kpi_data)
            
            # 2. 订单明细（限制条数）
            sheets['订单明细'] = order_data.head(1000)
            
            # 3. 商品排行
            group_key = self.get_product_group_key(data)
            sales_col = self.get_sales_column(data)
            
            if sales_col in data.columns:
                product_stats = data.groupby(group_key).agg({
                    sales_col: 'sum',
                    '利润额': 'sum' if '利润额' in data.columns else lambda x: 0,
                }).reset_index()
                product_stats.columns = [group_key, '销量', '利润额']
                product_stats = product_stats.sort_values('销量', ascending=False).head(50)
                sheets['商品排行TOP50'] = product_stats
            
            # 4. 渠道分析
            channel_col = next((c for c in ['平台', '渠道'] if c in order_data.columns), None)
            if channel_col:
                channel_stats = order_data.groupby(channel_col).agg({
                    '订单ID': 'count',
                    '实收价格': 'sum' if '实收价格' in order_data.columns else lambda x: 0,
                }).reset_index()
                channel_stats.columns = [channel_col, '订单数', '销售额']
                sheets['渠道分析'] = channel_stats
            
            filename = f"综合报表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            return self.export_to_excel(sheets, filename=filename)
            
        except Exception as e:
            return self.handle_error(e, "生成综合报表失败")

