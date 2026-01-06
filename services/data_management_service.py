# -*- coding: utf-8 -*-
"""
数据管理服务

提供数据管理相关的功能：
- 数据上传和导入
- 数据验证
- 数据清洗
- 数据备份和恢复

版本: v1.0
创建日期: 2026-01-05
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, date, timedelta
import hashlib

from .base_service import BaseService
from .cache.cache_keys import CacheKeys


# 支持的文件格式
SUPPORTED_FORMATS = ['.xlsx', '.xls', '.csv', '.parquet']

# 必需字段
REQUIRED_FIELDS = {
    '订单数据': ['订单ID', '商品名称'],
    '商品数据': ['商品名称', '条码'],
}

# 字段映射（常见别名 -> 标准名称）
FIELD_MAPPING = {
    # 订单ID
    '订单号': '订单ID',
    '订单编号': '订单ID',
    'order_id': '订单ID',
    'OrderID': '订单ID',
    
    # 商品名称
    '品名': '商品名称',
    '商品': '商品名称',
    'product_name': '商品名称',
    'ProductName': '商品名称',
    
    # 日期
    '下单日期': '下单时间',
    '订单时间': '下单时间',
    'order_time': '下单时间',
    'order_date': '下单时间',
    
    # 价格
    '实付金额': '实收价格',
    '实付': '实收价格',
    '付款金额': '实收价格',
    
    # 成本
    '采购成本': '商品采购成本',
    '进货价': '商品采购成本',
    
    # 配送费
    '配送费': '物流配送费',
    '运费': '物流配送费',
}


class DataManagementService(BaseService):
    """
    数据管理服务
    
    提供数据导入、验证、清洗等功能
    """
    
    def __init__(self, data_loader=None, cache_manager=None, data_dir: str = './data'):
        super().__init__(cache_manager)
        self.data_loader = data_loader
        self.data_dir = data_dir
        
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
    
    # ==================== 数据加载 ====================
    
    def load_file(
        self,
        filepath: str,
        sheet_name: Union[str, int] = 0,
        encoding: str = 'utf-8'
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        加载数据文件
        
        Args:
            filepath: 文件路径
            sheet_name: Excel工作表名/索引
            encoding: CSV编码
        
        Returns:
            (DataFrame, 错误信息)
        """
        try:
            if not os.path.exists(filepath):
                return None, f'文件不存在: {filepath}'
            
            ext = os.path.splitext(filepath)[1].lower()
            
            if ext not in SUPPORTED_FORMATS:
                return None, f'不支持的文件格式: {ext}'
            
            if ext in ['.xlsx', '.xls']:
                df = pd.read_excel(filepath, sheet_name=sheet_name)
            elif ext == '.csv':
                # 尝试多种编码
                for enc in [encoding, 'utf-8-sig', 'gbk', 'gb2312']:
                    try:
                        df = pd.read_csv(filepath, encoding=enc)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    return None, '无法识别文件编码'
            elif ext == '.parquet':
                df = pd.read_parquet(filepath)
            else:
                return None, f'不支持的文件格式: {ext}'
            
            return df, None
            
        except Exception as e:
            return None, str(e)
    
    # ==================== 字段映射 ====================
    
    def apply_field_mapping(
        self,
        df: pd.DataFrame,
        custom_mapping: Dict[str, str] = None
    ) -> pd.DataFrame:
        """
        应用字段映射，将常见别名转换为标准名称
        
        Args:
            df: DataFrame
            custom_mapping: 自定义映射
        
        Returns:
            映射后的DataFrame
        """
        data = df.copy()
        
        # 合并映射
        mapping = FIELD_MAPPING.copy()
        if custom_mapping:
            mapping.update(custom_mapping)
        
        # 应用映射
        rename_dict = {}
        for col in data.columns:
            if col in mapping:
                rename_dict[col] = mapping[col]
        
        if rename_dict:
            data = data.rename(columns=rename_dict)
        
        return data
    
    # ==================== 数据验证 ====================
    
    def validate_data(
        self,
        df: pd.DataFrame,
        data_type: str = '订单数据',
        strict: bool = False
    ) -> Dict[str, Any]:
        """
        验证数据质量
        
        Args:
            df: DataFrame
            data_type: 数据类型
            strict: 是否严格模式（缺少必需字段报错）
        
        Returns:
            验证结果
        """
        if df is None or df.empty:
            return {'valid': False, 'error': '数据为空'}
        
        result = {
            'valid': True,
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': df.columns.tolist(),
            'missing_required': [],
            'quality_issues': [],
            'data_types': {},
            'null_counts': {},
            'sample_values': {}
        }
        
        # 检查必需字段
        required = REQUIRED_FIELDS.get(data_type, [])
        for field in required:
            if field not in df.columns:
                result['missing_required'].append(field)
        
        if result['missing_required'] and strict:
            result['valid'] = False
            result['error'] = f"缺少必需字段: {', '.join(result['missing_required'])}"
            return result
        
        # 数据类型和空值统计
        for col in df.columns:
            result['data_types'][col] = str(df[col].dtype)
            result['null_counts'][col] = int(df[col].isna().sum())
            
            # 样例值（非空的前3个）
            non_null = df[col].dropna().head(3).tolist()
            result['sample_values'][col] = [str(v)[:50] for v in non_null]
        
        # 质量问题检测
        # 1. 高空值率字段
        for col, null_count in result['null_counts'].items():
            null_rate = null_count / len(df)
            if null_rate > 0.5:
                result['quality_issues'].append({
                    'type': '高空值率',
                    'column': col,
                    'detail': f'{null_rate*100:.1f}% 为空'
                })
        
        # 2. 订单ID重复（正常情况有多行）
        if '订单ID' in df.columns:
            order_count = df['订单ID'].nunique()
            row_count = len(df)
            avg_items = row_count / order_count if order_count > 0 else 0
            result['order_stats'] = {
                'unique_orders': int(order_count),
                'total_rows': row_count,
                'avg_items_per_order': round(avg_items, 2)
            }
        
        # 3. 日期范围
        date_col = self.get_date_column(df)
        if date_col:
            try:
                dates = pd.to_datetime(df[date_col], errors='coerce')
                valid_dates = dates.dropna()
                if len(valid_dates) > 0:
                    result['date_range'] = {
                        'min': str(valid_dates.min().date()),
                        'max': str(valid_dates.max().date()),
                        'days': (valid_dates.max() - valid_dates.min()).days
                    }
            except:
                pass
        
        return result
    
    # ==================== 数据清洗 ====================
    
    def clean_data(
        self,
        df: pd.DataFrame,
        remove_duplicates: bool = False,
        fill_missing: bool = False,
        convert_types: bool = True
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        清洗数据
        
        Args:
            df: DataFrame
            remove_duplicates: 是否去重
            fill_missing: 是否填充缺失值
            convert_types: 是否转换数据类型
        
        Returns:
            (清洗后的DataFrame, 清洗报告)
        """
        data = df.copy()
        report = {
            'original_rows': len(data),
            'actions': []
        }
        
        # 1. 字段映射
        data = self.apply_field_mapping(data)
        report['actions'].append('应用字段映射')
        
        # 2. 去除完全重复的行
        if remove_duplicates:
            before = len(data)
            data = data.drop_duplicates()
            removed = before - len(data)
            if removed > 0:
                report['actions'].append(f'去除重复行: {removed}')
        
        # 3. 数据类型转换
        if convert_types:
            # 日期字段
            date_cols = ['下单时间', '日期', 'date', 'order_date']
            for col in date_cols:
                if col in data.columns:
                    try:
                        data[col] = pd.to_datetime(data[col], errors='coerce')
                        report['actions'].append(f'转换日期字段: {col}')
                    except:
                        pass
            
            # 数值字段
            numeric_cols = [
                '实收价格', '商品实售价', '商品采购成本', '利润额',
                '物流配送费', '平台服务费', '月售', '销量', '库存'
            ]
            for col in numeric_cols:
                if col in data.columns:
                    try:
                        data[col] = pd.to_numeric(data[col], errors='coerce')
                        report['actions'].append(f'转换数值字段: {col}')
                    except:
                        pass
        
        # 4. 填充缺失值
        if fill_missing:
            # 数值字段填0
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                null_count = data[col].isna().sum()
                if null_count > 0:
                    data[col] = data[col].fillna(0)
                    report['actions'].append(f'填充空值: {col} ({null_count}个)')
        
        report['final_rows'] = len(data)
        report['columns'] = data.columns.tolist()
        
        return data, report
    
    # ==================== 数据合并 ====================
    
    def merge_data(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        on: Union[str, List[str]],
        how: str = 'left'
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        合并两个DataFrame
        
        Args:
            df1: 主数据
            df2: 关联数据
            on: 关联字段
            how: 合并方式
        
        Returns:
            (合并后的DataFrame, 合并报告)
        """
        try:
            merged = df1.merge(df2, on=on, how=how)
            
            report = {
                'df1_rows': len(df1),
                'df2_rows': len(df2),
                'merged_rows': len(merged),
                'on_columns': on if isinstance(on, list) else [on],
                'how': how
            }
            
            return merged, report
            
        except Exception as e:
            return df1, {'error': str(e)}
    
    # ==================== 数据导入 ====================
    
    def import_data(
        self,
        filepath: str,
        data_type: str = '订单数据',
        validate: bool = True,
        clean: bool = True
    ) -> Dict[str, Any]:
        """
        导入数据文件
        
        Args:
            filepath: 文件路径
            data_type: 数据类型
            validate: 是否验证
            clean: 是否清洗
        
        Returns:
            导入结果
        """
        try:
            # 1. 加载文件
            df, error = self.load_file(filepath)
            if error:
                return {'success': False, 'error': error}
            
            result = {
                'success': True,
                'filename': os.path.basename(filepath),
                'original_rows': len(df),
                'original_columns': len(df.columns)
            }
            
            # 2. 验证
            if validate:
                validation = self.validate_data(df, data_type)
                result['validation'] = validation
                
                if not validation.get('valid', True):
                    result['success'] = False
                    result['error'] = validation.get('error', '验证失败')
                    return result
            
            # 3. 清洗
            if clean:
                df, clean_report = self.clean_data(df)
                result['clean_report'] = clean_report
            
            result['data'] = df
            result['final_rows'] = len(df)
            result['final_columns'] = len(df.columns)
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ==================== 数据统计 ====================
    
    def get_data_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取数据统计信息
        
        Args:
            df: DataFrame
        
        Returns:
            统计信息
        """
        if df is None or df.empty:
            return {'error': '数据为空'}
        
        stats = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'memory_usage_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
        }
        
        # 数值字段统计
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            stats['numeric_summary'] = df[numeric_cols].describe().to_dict()
        
        # 日期范围
        date_col = self.get_date_column(df)
        if date_col:
            try:
                dates = pd.to_datetime(df[date_col], errors='coerce').dropna()
                if len(dates) > 0:
                    stats['date_range'] = {
                        'min': str(dates.min().date()),
                        'max': str(dates.max().date())
                    }
            except:
                pass
        
        # 订单统计
        if '订单ID' in df.columns:
            stats['order_count'] = int(df['订单ID'].nunique())
        
        # 门店统计
        if '门店名称' in df.columns:
            stores = df['门店名称'].unique().tolist()
            stats['store_count'] = len(stores)
            stats['stores'] = stores[:10]  # 最多显示10个
        
        return stats
    
    # ==================== 数据哈希 ====================
    
    def calculate_data_hash(self, df: pd.DataFrame) -> str:
        """
        计算数据哈希值（用于判断数据是否变化）
        
        Args:
            df: DataFrame
        
        Returns:
            哈希值
        """
        if df is None or df.empty:
            return ''
        
        # 使用pandas内置哈希
        hash_values = pd.util.hash_pandas_object(df)
        combined_hash = hashlib.md5(hash_values.values.tobytes()).hexdigest()
        
        return combined_hash
    
    # ==================== 缓存管理 ====================
    
    def clear_cache(self) -> Dict[str, Any]:
        """清空数据缓存"""
        if self.cache:
            success = self.cache.clear_all()
            return {'success': success, 'message': '缓存已清空'}
        return {'success': False, 'message': '缓存未启用'}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        if self.cache:
            return self.cache.get_stats()
        return {'enabled': False}

