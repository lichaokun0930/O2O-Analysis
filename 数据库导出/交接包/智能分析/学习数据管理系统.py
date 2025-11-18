#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习数据管理系统 - 智能数据质量评估与异常检测
负责学习数据的收集、验证、存储和版本管理
"""

import os
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import pickle
import gzip
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

class LearningDataManager:
    """学习数据管理器"""
    
    def __init__(self, data_dir: str = "学习数据仓库"):
        """
        初始化学习数据管理器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.ensure_data_directory()
        
        # 数据库文件路径
        self.db_path = os.path.join(data_dir, "learning_data.db")
        self.init_database()
        
        # 数据质量评估配置
        self.quality_config = {
            'completeness_threshold': 0.8,  # 完整性阈值
            'consistency_threshold': 0.9,   # 一致性阈值
            'accuracy_threshold': 0.85,     # 准确性阈值
            'freshness_days': 30,           # 数据新鲜度（天）
            'duplicate_threshold': 0.95,    # 重复数据相似度阈值
            'outlier_contamination': 0.05   # 异常数据污染率
        }
        
        # 异常检测器
        self.anomaly_detector = IsolationForest(
            contamination=self.quality_config['outlier_contamination'],
            random_state=42
        )
        
        # 数据标准化器
        self.data_scaler = StandardScaler()
        
        # 缓存管理
        self.cache_size_limit = 1000  # 最大缓存样本数
        self.cached_data = {}
        
        logger.info("学习数据管理系统初始化完成")
    
    def ensure_data_directory(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # 创建子目录
        subdirs = ['raw_data', 'processed_data', 'quality_reports', 'backups', 'cache']
        for subdir in subdirs:
            path = os.path.join(self.data_dir, subdir)
            if not os.path.exists(path):
                os.makedirs(path)
    
    def init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建数据集表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT UNIQUE,
                    name TEXT,
                    description TEXT,
                    created_time TEXT,
                    updated_time TEXT,
                    data_type TEXT,
                    sample_count INTEGER,
                    feature_count INTEGER,
                    quality_score REAL,
                    file_path TEXT,
                    file_size INTEGER,
                    checksum TEXT,
                    version INTEGER DEFAULT 1
                )
            ''')
            
            # 创建数据质量评估表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quality_assessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT,
                    assessment_time TEXT,
                    completeness_score REAL,
                    consistency_score REAL,
                    accuracy_score REAL,
                    freshness_score REAL,
                    overall_score REAL,
                    anomalies_detected INTEGER,
                    quality_report TEXT,
                    FOREIGN KEY (dataset_id) REFERENCES datasets (dataset_id)
                )
            ''')
            
            # 创建学习历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT,
                    model_name TEXT,
                    training_time TEXT,
                    sample_count INTEGER,
                    performance_metrics TEXT,
                    feature_importance TEXT,
                    training_duration REAL,
                    FOREIGN KEY (dataset_id) REFERENCES datasets (dataset_id)
                )
            ''')
            
            # 创建异常数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS anomaly_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT,
                    detection_time TEXT,
                    anomaly_type TEXT,
                    severity TEXT,
                    sample_indices TEXT,
                    description TEXT,
                    resolution_status TEXT DEFAULT 'pending',
                    FOREIGN KEY (dataset_id) REFERENCES datasets (dataset_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("数据库初始化完成")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
    
    def generate_dataset_id(self, data: Any, name: str = "") -> str:
        """生成数据集ID"""
        try:
            # 使用数据的哈希值和时间戳生成ID
            if isinstance(data, pd.DataFrame):
                data_hash = hashlib.md5(data.to_string().encode()).hexdigest()[:8]
            else:
                data_hash = hashlib.md5(str(data).encode()).hexdigest()[:8]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_part = name.replace(" ", "_") if name else "dataset"
            
            return f"{name_part}_{data_hash}_{timestamp}"
        
        except Exception as e:
            logger.error(f"生成数据集ID失败: {str(e)}")
            return f"dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def calculate_file_checksum(self, file_path: str) -> str:
        """计算文件校验和"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"计算文件校验和失败: {str(e)}")
            return ""
    
    def save_dataset(self, data: pd.DataFrame, name: str = "", description: str = "", data_type: str = "training") -> str:
        """
        保存数据集
        
        Args:
            data: 要保存的数据
            name: 数据集名称
            description: 数据集描述
            data_type: 数据类型
            
        Returns:
            数据集ID
        """
        try:
            dataset_id = self.generate_dataset_id(data, name)
            
            # 保存数据文件
            file_name = f"{dataset_id}.pkl.gz"
            file_path = os.path.join(self.data_dir, 'processed_data', file_name)
            
            with gzip.open(file_path, 'wb') as f:
                pickle.dump(data, f)
            
            # 获取文件信息
            file_size = os.path.getsize(file_path)
            checksum = self.calculate_file_checksum(file_path)
            
            # 评估数据质量
            quality_assessment = self.assess_data_quality(data, dataset_id)
            
            # 保存到数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_time = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO datasets 
                (dataset_id, name, description, created_time, updated_time, data_type, 
                 sample_count, feature_count, quality_score, file_path, file_size, checksum)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dataset_id, name, description, current_time, current_time, data_type,
                len(data), len(data.columns), quality_assessment['overall_score'],
                file_path, file_size, checksum
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"数据集保存成功: {dataset_id}, 样本数: {len(data)}, 质量评分: {quality_assessment['overall_score']:.3f}")
            
            return dataset_id
            
        except Exception as e:
            logger.error(f"保存数据集失败: {str(e)}")
            return ""
    
    def load_dataset(self, dataset_id: str) -> Optional[pd.DataFrame]:
        """
        加载数据集
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            数据集DataFrame
        """
        try:
            # 先检查缓存
            if dataset_id in self.cached_data:
                logger.info(f"从缓存加载数据集: {dataset_id}")
                return self.cached_data[dataset_id]
            
            # 从数据库获取文件路径
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT file_path, checksum FROM datasets WHERE dataset_id = ?', (dataset_id,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                logger.warning(f"数据集不存在: {dataset_id}")
                return None
            
            file_path, expected_checksum = result
            
            # 验证文件完整性
            if expected_checksum:
                actual_checksum = self.calculate_file_checksum(file_path)
                if actual_checksum != expected_checksum:
                    logger.error(f"数据集文件已损坏: {dataset_id}")
                    return None
            
            # 加载数据
            with gzip.open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            # 缓存管理
            if len(self.cached_data) >= self.cache_size_limit:
                # 移除最旧的缓存项
                oldest_key = next(iter(self.cached_data))
                del self.cached_data[oldest_key]
            
            self.cached_data[dataset_id] = data
            
            logger.info(f"数据集加载成功: {dataset_id}, 样本数: {len(data)}")
            return data
            
        except Exception as e:
            logger.error(f"加载数据集失败: {str(e)}")
            return None
    
    def assess_data_quality(self, data: pd.DataFrame, dataset_id: str) -> Dict[str, Any]:
        """
        评估数据质量
        
        Args:
            data: 要评估的数据
            dataset_id: 数据集ID
            
        Returns:
            质量评估结果
        """
        try:
            assessment = {
                'completeness_score': 0.0,
                'consistency_score': 0.0,
                'accuracy_score': 0.0,
                'freshness_score': 0.0,
                'overall_score': 0.0,
                'anomalies_detected': 0,
                'quality_issues': [],
                'recommendations': []
            }
            
            # 1. 完整性评估
            total_cells = data.size
            missing_cells = data.isnull().sum().sum()
            completeness = 1 - (missing_cells / total_cells) if total_cells > 0 else 0
            assessment['completeness_score'] = completeness
            
            if completeness < self.quality_config['completeness_threshold']:
                assessment['quality_issues'].append(f"数据完整性较低: {completeness:.2%}")
                assessment['recommendations'].append("建议补充缺失数据或使用插值方法")
            
            # 2. 一致性评估
            consistency_score = 1.0  # 默认一致性良好
            
            # 检查数据类型一致性
            for column in data.columns:
                if data[column].dtype == 'object':
                    # 检查字符串列的格式一致性
                    unique_formats = data[column].dropna().apply(lambda x: type(x).__name__).unique()
                    if len(unique_formats) > 1:
                        consistency_score -= 0.1
                        assessment['quality_issues'].append(f"列 {column} 数据类型不一致")
            
            assessment['consistency_score'] = max(0, consistency_score)
            
            # 3. 准确性评估（基于统计异常检测）
            numeric_columns = data.select_dtypes(include=[np.number]).columns
            accuracy_score = 1.0
            total_anomalies = 0
            
            if len(numeric_columns) > 0:
                # 数值列异常检测
                numeric_data = data[numeric_columns].fillna(data[numeric_columns].mean())
                
                if len(numeric_data) > 10:  # 需要足够的样本进行异常检测
                    try:
                        anomaly_labels = self.anomaly_detector.fit_predict(numeric_data)
                        anomaly_count = np.sum(anomaly_labels == -1)
                        total_anomalies = anomaly_count
                        
                        anomaly_rate = anomaly_count / len(numeric_data)
                        accuracy_score = max(0, 1 - anomaly_rate * 2)  # 异常率影响准确性
                        
                        if anomaly_rate > self.quality_config['outlier_contamination']:
                            assessment['quality_issues'].append(f"检测到 {anomaly_count} 个异常样本 ({anomaly_rate:.1%})")
                            assessment['recommendations'].append("建议审查异常数据并考虑清理")
                    
                    except Exception as e:
                        logger.warning(f"异常检测失败: {str(e)}")
            
            assessment['accuracy_score'] = accuracy_score
            assessment['anomalies_detected'] = total_anomalies
            
            # 4. 新鲜度评估
            freshness_score = 1.0  # 新数据默认新鲜度满分
            
            # 如果数据包含时间戳，检查数据的新鲜度
            time_columns = []
            for col in data.columns:
                if 'time' in col.lower() or 'date' in col.lower() or '时间' in col:
                    time_columns.append(col)
            
            if time_columns:
                try:
                    latest_time_col = time_columns[0]
                    if data[latest_time_col].dtype == 'object':
                        latest_date = pd.to_datetime(data[latest_time_col]).max()
                    else:
                        latest_date = data[latest_time_col].max()
                    
                    if pd.isna(latest_date):
                        freshness_score = 0.5
                    else:
                        days_old = (datetime.now() - pd.to_datetime(latest_date)).days
                        freshness_score = max(0, 1 - days_old / self.quality_config['freshness_days'])
                        
                        if days_old > self.quality_config['freshness_days']:
                            assessment['quality_issues'].append(f"数据较旧，最新数据距今 {days_old} 天")
                            assessment['recommendations'].append("建议更新数据或收集更新的数据")
                
                except Exception as e:
                    logger.warning(f"新鲜度评估失败: {str(e)}")
            
            assessment['freshness_score'] = freshness_score
            
            # 5. 计算综合评分
            weights = {
                'completeness': 0.3,
                'consistency': 0.2,
                'accuracy': 0.3,
                'freshness': 0.2
            }
            
            overall_score = (
                assessment['completeness_score'] * weights['completeness'] +
                assessment['consistency_score'] * weights['consistency'] +
                assessment['accuracy_score'] * weights['accuracy'] +
                assessment['freshness_score'] * weights['freshness']
            )
            
            assessment['overall_score'] = overall_score
            
            # 保存质量评估结果到数据库
            self.save_quality_assessment(dataset_id, assessment)
            
            logger.info(f"数据质量评估完成: {dataset_id}, 综合评分: {overall_score:.3f}")
            
            return assessment
            
        except Exception as e:
            logger.error(f"数据质量评估失败: {str(e)}")
            return {
                'completeness_score': 0.0,
                'consistency_score': 0.0,
                'accuracy_score': 0.0,
                'freshness_score': 0.0,
                'overall_score': 0.0,
                'anomalies_detected': 0,
                'quality_issues': ['质量评估系统故障'],
                'recommendations': ['请检查数据质量评估系统']
            }
    
    def save_quality_assessment(self, dataset_id: str, assessment: Dict[str, Any]):
        """保存质量评估结果"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO quality_assessments 
                (dataset_id, assessment_time, completeness_score, consistency_score, 
                 accuracy_score, freshness_score, overall_score, anomalies_detected, quality_report)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dataset_id,
                datetime.now().isoformat(),
                assessment['completeness_score'],
                assessment['consistency_score'],
                assessment['accuracy_score'],
                assessment['freshness_score'],
                assessment['overall_score'],
                assessment['anomalies_detected'],
                json.dumps(assessment, ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存质量评估失败: {str(e)}")
    
    def detect_duplicate_datasets(self, similarity_threshold: float = None) -> List[Tuple[str, str, float]]:
        """
        检测重复数据集
        
        Args:
            similarity_threshold: 相似度阈值
            
        Returns:
            重复数据集对列表 [(dataset_id1, dataset_id2, similarity), ...]
        """
        try:
            if similarity_threshold is None:
                similarity_threshold = self.quality_config['duplicate_threshold']
            
            # 获取所有数据集
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT dataset_id, sample_count, feature_count FROM datasets')
            datasets_info = cursor.fetchall()
            conn.close()
            
            duplicates = []
            
            # 比较数据集相似度
            for i, (id1, count1, features1) in enumerate(datasets_info):
                for j, (id2, count2, features2) in enumerate(datasets_info[i+1:], i+1):
                    try:
                        # 加载数据集进行比较
                        data1 = self.load_dataset(id1)
                        data2 = self.load_dataset(id2)
                        
                        if data1 is not None and data2 is not None:
                            # 计算结构相似度
                            structure_similarity = self.calculate_structure_similarity(data1, data2)
                            
                            if structure_similarity > similarity_threshold:
                                # 计算内容相似度
                                content_similarity = self.calculate_content_similarity(data1, data2)
                                overall_similarity = (structure_similarity + content_similarity) / 2
                                
                                if overall_similarity > similarity_threshold:
                                    duplicates.append((id1, id2, overall_similarity))
                                    
                    except Exception as e:
                        logger.warning(f"比较数据集失败 {id1} vs {id2}: {str(e)}")
            
            if duplicates:
                logger.info(f"检测到 {len(duplicates)} 对重复数据集")
            
            return duplicates
            
        except Exception as e:
            logger.error(f"检测重复数据集失败: {str(e)}")
            return []
    
    def calculate_structure_similarity(self, data1: pd.DataFrame, data2: pd.DataFrame) -> float:
        """计算数据集结构相似度"""
        try:
            # 比较列名
            cols1 = set(data1.columns)
            cols2 = set(data2.columns)
            
            common_cols = cols1.intersection(cols2)
            all_cols = cols1.union(cols2)
            
            column_similarity = len(common_cols) / len(all_cols) if all_cols else 0
            
            # 比较数据类型
            dtype_similarity = 1.0
            for col in common_cols:
                if data1[col].dtype != data2[col].dtype:
                    dtype_similarity -= 0.1
            
            dtype_similarity = max(0, dtype_similarity)
            
            # 比较形状相似度
            shape_similarity = 1 - abs(len(data1) - len(data2)) / max(len(data1), len(data2))
            
            # 综合结构相似度
            structure_similarity = (column_similarity * 0.5 + dtype_similarity * 0.3 + shape_similarity * 0.2)
            
            return structure_similarity
            
        except Exception as e:
            logger.error(f"计算结构相似度失败: {str(e)}")
            return 0.0
    
    def calculate_content_similarity(self, data1: pd.DataFrame, data2: pd.DataFrame) -> float:
        """计算数据集内容相似度"""
        try:
            # 找到共同的数值列
            numeric_cols1 = set(data1.select_dtypes(include=[np.number]).columns)
            numeric_cols2 = set(data2.select_dtypes(include=[np.number]).columns)
            common_numeric_cols = list(numeric_cols1.intersection(numeric_cols2))
            
            if not common_numeric_cols:
                return 0.0
            
            # 计算统计特征相似度
            similarities = []
            
            for col in common_numeric_cols:
                try:
                    # 基本统计量
                    stats1 = data1[col].describe()
                    stats2 = data2[col].describe()
                    
                    # 计算统计量相似度
                    stat_names = ['mean', 'std', 'min', 'max']
                    stat_similarities = []
                    
                    for stat in stat_names:
                        if stat in stats1 and stat in stats2:
                            val1, val2 = stats1[stat], stats2[stat]
                            if val1 != 0 or val2 != 0:
                                stat_sim = 1 - abs(val1 - val2) / (abs(val1) + abs(val2))
                                stat_similarities.append(stat_sim)
                    
                    if stat_similarities:
                        similarities.append(np.mean(stat_similarities))
                
                except Exception as e:
                    logger.warning(f"计算列 {col} 相似度失败: {str(e)}")
            
            if similarities:
                return np.mean(similarities)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"计算内容相似度失败: {str(e)}")
            return 0.0
    
    def cleanup_old_data(self, days_threshold: int = 90):
        """
        清理过期数据
        
        Args:
            days_threshold: 保留天数阈值
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_threshold)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取过期数据集
            cursor.execute('''
                SELECT dataset_id, file_path FROM datasets 
                WHERE created_time < ?
            ''', (cutoff_date.isoformat(),))
            
            old_datasets = cursor.fetchall()
            
            cleaned_count = 0
            for dataset_id, file_path in old_datasets:
                try:
                    # 删除文件
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                    # 删除数据库记录
                    cursor.execute('DELETE FROM datasets WHERE dataset_id = ?', (dataset_id,))
                    cursor.execute('DELETE FROM quality_assessments WHERE dataset_id = ?', (dataset_id,))
                    cursor.execute('DELETE FROM learning_history WHERE dataset_id = ?', (dataset_id,))
                    cursor.execute('DELETE FROM anomaly_data WHERE dataset_id = ?', (dataset_id,))
                    
                    # 清理缓存
                    if dataset_id in self.cached_data:
                        del self.cached_data[dataset_id]
                    
                    cleaned_count += 1
                    
                except Exception as e:
                    logger.error(f"清理数据集失败 {dataset_id}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"数据清理完成，清理了 {cleaned_count} 个过期数据集")
            
        except Exception as e:
            logger.error(f"数据清理失败: {str(e)}")
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 基础统计
            cursor.execute('SELECT COUNT(*) FROM datasets')
            total_datasets = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(sample_count) FROM datasets')
            total_samples = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT AVG(quality_score) FROM datasets')
            avg_quality = cursor.fetchone()[0] or 0
            
            # 数据类型分布
            cursor.execute('SELECT data_type, COUNT(*) FROM datasets GROUP BY data_type')
            type_distribution = dict(cursor.fetchall())
            
            # 质量分布
            cursor.execute('''
                SELECT 
                    CASE 
                        WHEN quality_score >= 0.8 THEN 'excellent'
                        WHEN quality_score >= 0.6 THEN 'good'
                        WHEN quality_score >= 0.4 THEN 'fair'
                        ELSE 'poor'
                    END as quality_level,
                    COUNT(*) as count
                FROM datasets 
                GROUP BY quality_level
            ''')
            quality_distribution = dict(cursor.fetchall())
            
            # 最近活动
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute('SELECT COUNT(*) FROM datasets WHERE created_time > ?', (week_ago,))
            recent_datasets = cursor.fetchone()[0]
            
            conn.close()
            
            statistics = {
                'total_datasets': total_datasets,
                'total_samples': total_samples,
                'average_quality_score': round(avg_quality, 3),
                'data_type_distribution': type_distribution,
                'quality_distribution': quality_distribution,
                'recent_datasets_7days': recent_datasets,
                'cache_size': len(self.cached_data),
                'storage_directory': self.data_dir
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"获取数据统计失败: {str(e)}")
            return {}
    
    def export_data_report(self) -> str:
        """导出数据管理报告"""
        try:
            stats = self.get_data_statistics()
            
            report = f"""
# 学习数据管理报告

## 数据概览
- 数据集总数: {stats.get('total_datasets', 0)}
- 样本总数: {stats.get('total_samples', 0):,}
- 平均质量评分: {stats.get('average_quality_score', 0):.3f}/1.0
- 近7天新增数据集: {stats.get('recent_datasets_7days', 0)}

## 数据类型分布
"""
            
            for data_type, count in stats.get('data_type_distribution', {}).items():
                report += f"- {data_type}: {count} 个数据集\n"
            
            report += f"""
## 数据质量分布
"""
            
            for quality_level, count in stats.get('quality_distribution', {}).items():
                report += f"- {quality_level}: {count} 个数据集\n"
            
            report += f"""
## 存储信息
- 存储目录: {stats.get('storage_directory', 'N/A')}
- 缓存数据集: {stats.get('cache_size', 0)} 个

## 数据质量建议
"""
            
            # 基于统计信息生成建议
            avg_quality = stats.get('average_quality_score', 0)
            if avg_quality < 0.6:
                report += "- ⚠️ 整体数据质量偏低，建议加强数据清理和验证\n"
            elif avg_quality < 0.8:
                report += "- 💡 数据质量中等，可以进一步优化数据收集流程\n"
            else:
                report += "- ✅ 数据质量良好，继续保持当前标准\n"
            
            poor_count = stats.get('quality_distribution', {}).get('poor', 0)
            if poor_count > 0:
                report += f"- 🔧 发现 {poor_count} 个低质量数据集，建议优先处理\n"
            
            report += f"""
报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            # 保存报告
            report_path = os.path.join(self.data_dir, 'quality_reports', 
                                     f"data_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"数据管理报告已保存: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"导出数据报告失败: {str(e)}")
            return ""


def main():
    """测试学习数据管理系统"""
    # 创建数据管理器
    manager = LearningDataManager()
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'feature1': np.random.normal(0, 1, 100),
        'feature2': np.random.normal(5, 2, 100),
        'feature3': ['A'] * 50 + ['B'] * 50,
        'target': np.random.random(100),
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='D')
    })
    
    # 添加一些缺失值和异常值
    test_data.loc[10:15, 'feature1'] = np.nan
    test_data.loc[95:99, 'feature2'] = 100  # 异常值
    
    # 保存数据集
    print("保存测试数据集...")
    dataset_id = manager.save_dataset(test_data, "测试数据集", "用于测试数据管理系统", "training")
    print(f"数据集ID: {dataset_id}")
    
    # 加载数据集
    print("加载数据集...")
    loaded_data = manager.load_dataset(dataset_id)
    print(f"加载成功，样本数: {len(loaded_data) if loaded_data is not None else 0}")
    
    # 获取统计信息
    print("获取数据统计...")
    stats = manager.get_data_statistics()
    print("统计信息:", json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 导出报告
    print("导出数据报告...")
    report_path = manager.export_data_report()
    print(f"报告路径: {report_path}")


if __name__ == "__main__":
    main()