#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自适应学习引擎 - AI模型持续优化系统
支持在线学习、模型版本管理、性能监控和智能调参
"""

import os
import json
import pickle
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import SGDRegressor, PassiveAggressiveRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdaptiveLearningEngine:
    """自适应学习引擎"""
    
    def __init__(self, model_dir: str = "智能模型仓库"):
        """
        初始化自适应学习引擎
        
        Args:
            model_dir: 模型存储目录
        """
        self.model_dir = model_dir
        self.ensure_model_directory()
        
        # 学习历史存储
        self.learning_history_file = os.path.join(model_dir, "learning_history.json")
        self.model_performance_file = os.path.join(model_dir, "model_performance.json")
        self.feature_importance_file = os.path.join(model_dir, "feature_importance.json")
        
        # 初始化在线学习模型
        self.online_models = {
            'sales_predictor': SGDRegressor(learning_rate='adaptive', eta0=0.01, max_iter=1000),
            'profit_predictor': PassiveAggressiveRegressor(max_iter=1000, random_state=42),
            'demand_predictor': SGDRegressor(learning_rate='invscaling', eta0=0.1, max_iter=1000),
            'price_optimizer': SGDRegressor(learning_rate='constant', eta0=0.05, max_iter=1000)
        }
        
        # 批量学习模型
        self.batch_models = {
            'sales_predictor': RandomForestRegressor(n_estimators=100, random_state=42),
            'profit_predictor': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'demand_predictor': RandomForestRegressor(n_estimators=80, random_state=42),
            'price_optimizer': GradientBoostingRegressor(n_estimators=80, random_state=42)
        }
        
        # 特征预处理器
        self.scalers = {}
        self.label_encoders = {}
        
        # 学习参数
        self.learning_config = {
            'batch_size': 50,
            'learning_rate_decay': 0.95,
            'performance_threshold': 0.85,
            'retrain_threshold': 0.1,
            'max_memory_samples': 10000
        }
        
        # 加载已有模型和历史
        self.load_existing_models()
        self.learning_history = self.load_learning_history()
        self.model_performance = self.load_model_performance()
        
        logger.info("自适应学习引擎初始化完成")
    
    def ensure_model_directory(self):
        """确保模型目录存在"""
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
        
        # 创建子目录
        subdirs = ['online_models', 'batch_models', 'scalers', 'archives']
        for subdir in subdirs:
            path = os.path.join(self.model_dir, subdir)
            if not os.path.exists(path):
                os.makedirs(path)
    
    def load_existing_models(self):
        """加载已存在的模型"""
        try:
            # 加载在线模型
            online_models_dir = os.path.join(self.model_dir, 'online_models')
            for model_name in self.online_models.keys():
                model_path = os.path.join(online_models_dir, f'{model_name}.joblib')
                if os.path.exists(model_path):
                    self.online_models[model_name] = joblib.load(model_path)
                    logger.info(f"加载在线模型: {model_name}")
            
            # 加载批量模型
            batch_models_dir = os.path.join(self.model_dir, 'batch_models')
            for model_name in self.batch_models.keys():
                model_path = os.path.join(batch_models_dir, f'{model_name}.joblib')
                if os.path.exists(model_path):
                    self.batch_models[model_name] = joblib.load(model_path)
                    logger.info(f"加载批量模型: {model_name}")
            
            # 加载预处理器
            scalers_dir = os.path.join(self.model_dir, 'scalers')
            for file_name in os.listdir(scalers_dir):
                if file_name.endswith('.joblib'):
                    name = file_name.replace('.joblib', '')
                    if 'scaler' in name:
                        self.scalers[name] = joblib.load(os.path.join(scalers_dir, file_name))
                    elif 'encoder' in name:
                        self.label_encoders[name] = joblib.load(os.path.join(scalers_dir, file_name))
                        
        except Exception as e:
            logger.warning(f"加载已有模型时出错: {str(e)}")
    
    def save_models(self):
        """保存所有模型"""
        try:
            # 保存在线模型
            online_models_dir = os.path.join(self.model_dir, 'online_models')
            for model_name, model in self.online_models.items():
                model_path = os.path.join(online_models_dir, f'{model_name}.joblib')
                joblib.dump(model, model_path)
            
            # 保存批量模型
            batch_models_dir = os.path.join(self.model_dir, 'batch_models')
            for model_name, model in self.batch_models.items():
                model_path = os.path.join(batch_models_dir, f'{model_name}.joblib')
                joblib.dump(model, model_path)
            
            # 保存预处理器
            scalers_dir = os.path.join(self.model_dir, 'scalers')
            for name, scaler in self.scalers.items():
                scaler_path = os.path.join(scalers_dir, f'{name}.joblib')
                joblib.dump(scaler, scaler_path)
            
            for name, encoder in self.label_encoders.items():
                encoder_path = os.path.join(scalers_dir, f'{name}.joblib')
                joblib.dump(encoder, encoder_path)
                
            logger.info("模型保存完成")
                
        except Exception as e:
            logger.error(f"保存模型时出错: {str(e)}")
    
    def load_learning_history(self) -> List[Dict]:
        """加载学习历史"""
        try:
            if os.path.exists(self.learning_history_file):
                with open(self.learning_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"加载学习历史失败: {str(e)}")
        return []
    
    def save_learning_history(self):
        """保存学习历史"""
        try:
            with open(self.learning_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存学习历史失败: {str(e)}")
    
    def load_model_performance(self) -> Dict:
        """加载模型性能记录"""
        try:
            if os.path.exists(self.model_performance_file):
                with open(self.model_performance_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"加载性能记录失败: {str(e)}")
        return {}
    
    def save_model_performance(self):
        """保存模型性能记录"""
        try:
            with open(self.model_performance_file, 'w', encoding='utf-8') as f:
                json.dump(self.model_performance, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存性能记录失败: {str(e)}")
    
    def extract_learning_features(self, analysis_data: Dict) -> pd.DataFrame:
        """
        从分析数据中提取学习特征
        
        Args:
            analysis_data: 分析数据字典
            
        Returns:
            特征DataFrame
        """
        features_list = []
        
        try:
            # 从产品数据提取特征
            if 'product_data' in analysis_data and isinstance(analysis_data['product_data'], pd.DataFrame):
                product_df = analysis_data['product_data']
                
                for _, row in product_df.iterrows():
                    feature = {
                        'timestamp': datetime.now().isoformat(),
                        'product_name': str(row.get('商品名称', 'unknown')),
                        'price': float(row.get('售价', 0)),
                        'original_price': float(row.get('原价', 0)),
                        'monthly_sales': int(row.get('月售', 0)),
                        'stock': int(row.get('库存', 0)),
                        'category_l1': str(row.get('美团一级分类', 'unknown')),
                        'category_l3': str(row.get('美团三级分类', 'unknown')),
                        'discount_rate': 1 - (float(row.get('售价', 0)) / max(float(row.get('原价', 1)), 1)),
                        'stock_turnover': float(row.get('月售', 0)) / max(float(row.get('库存', 1)), 1)
                    }
                    features_list.append(feature)
            
            # 添加时间特征
            now = datetime.now()
            time_features = {
                'hour': now.hour,
                'day_of_week': now.weekday(),
                'day_of_month': now.day,
                'month': now.month,
                'is_weekend': 1 if now.weekday() >= 5 else 0,
                'is_peak_hour': 1 if now.hour in [11, 12, 18, 19, 20] else 0
            }
            
            # 为每个产品特征添加时间特征
            for feature in features_list:
                feature.update(time_features)
            
            df = pd.DataFrame(features_list)
            
            if len(df) > 0:
                logger.info(f"提取到 {len(df)} 条学习特征")
            
            return df
            
        except Exception as e:
            logger.error(f"特征提取失败: {str(e)}")
            return pd.DataFrame()
    
    def prepare_features_and_targets(self, features_df: pd.DataFrame) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """
        准备训练特征和目标变量
        
        Args:
            features_df: 特征DataFrame
            
        Returns:
            包含不同预测任务的特征和目标字典
        """
        if len(features_df) == 0:
            return {}
        
        try:
            # 处理分类特征
            categorical_columns = ['category_l1', 'category_l3']
            for col in categorical_columns:
                if col in features_df.columns:
                    encoder_name = f'{col}_encoder'
                    if encoder_name not in self.label_encoders:
                        self.label_encoders[encoder_name] = LabelEncoder()
                        features_df[col] = self.label_encoders[encoder_name].fit_transform(features_df[col].astype(str))
                    else:
                        # 处理新类别
                        known_classes = set(self.label_encoders[encoder_name].classes_)
                        new_values = []
                        for val in features_df[col].astype(str):
                            if val in known_classes:
                                new_values.append(val)
                            else:
                                new_values.append('unknown' if 'unknown' in known_classes else self.label_encoders[encoder_name].classes_[0])
                        features_df[col] = self.label_encoders[encoder_name].transform(new_values)
            
            # 选择数值特征
            numeric_features = [
                'price', 'original_price', 'discount_rate', 'stock_turnover',
                'hour', 'day_of_week', 'day_of_month', 'month', 'is_weekend', 'is_peak_hour',
                'category_l1', 'category_l3'
            ]
            
            available_features = [col for col in numeric_features if col in features_df.columns]
            
            if len(available_features) == 0:
                logger.warning("没有可用的数值特征")
                return {}
            
            X = features_df[available_features].fillna(0).values
            
            # 标准化特征
            scaler_name = 'main_scaler'
            if scaler_name not in self.scalers:
                self.scalers[scaler_name] = StandardScaler()
                X = self.scalers[scaler_name].fit_transform(X)
            else:
                X = self.scalers[scaler_name].transform(X)
            
            # 构建不同的目标变量
            targets = {}
            
            # 销量预测目标
            if 'monthly_sales' in features_df.columns:
                targets['sales_predictor'] = features_df['monthly_sales'].fillna(0).values
            
            # 利润预测目标（基于价格和销量）
            if 'price' in features_df.columns and 'monthly_sales' in features_df.columns:
                profit_estimate = features_df['price'] * features_df['monthly_sales'] * 0.3  # 假设30%毛利率
                targets['profit_predictor'] = profit_estimate.fillna(0).values
            
            # 需求预测目标（基于销量和库存周转）
            if 'stock_turnover' in features_df.columns:
                targets['demand_predictor'] = features_df['stock_turnover'].fillna(0).values
            
            # 价格优化目标（基于折扣率和销量的权衡）
            if 'discount_rate' in features_df.columns and 'monthly_sales' in features_df.columns:
                # 价格效率 = 销量 * (1 - 折扣率)
                price_efficiency = features_df['monthly_sales'] * (1 - features_df['discount_rate'])
                targets['price_optimizer'] = price_efficiency.fillna(0).values
            
            result = {}
            for target_name, y in targets.items():
                if len(y) > 0:
                    result[target_name] = (X, y)
            
            logger.info(f"准备了 {len(result)} 个预测任务的数据")
            return result
            
        except Exception as e:
            logger.error(f"准备训练数据失败: {str(e)}")
            return {}
    
    def online_learning_update(self, analysis_data: Dict, feedback_data: Optional[Dict] = None):
        """
        在线学习更新
        
        Args:
            analysis_data: 分析数据
            feedback_data: 反馈数据（实际结果）
        """
        try:
            # 提取特征
            features_df = self.extract_learning_features(analysis_data)
            
            if len(features_df) == 0:
                logger.warning("没有有效的特征数据进行学习")
                return
            
            # 准备训练数据
            training_data = self.prepare_features_and_targets(features_df)
            
            if not training_data:
                logger.warning("没有有效的训练数据")
                return
            
            # 在线更新每个模型
            for model_name, (X, y) in training_data.items():
                if model_name in self.online_models and len(X) > 0:
                    try:
                        # 对于在线学习，我们使用部分拟合
                        if hasattr(self.online_models[model_name], 'partial_fit'):
                            self.online_models[model_name].partial_fit(X, y)
                        else:
                            # 如果模型不支持partial_fit，使用增量训练
                            self.online_models[model_name].fit(X, y)
                        
                        logger.info(f"在线更新模型: {model_name}, 样本数: {len(X)}")
                        
                        # 记录学习历史
                        learning_record = {
                            'timestamp': datetime.now().isoformat(),
                            'model_name': model_name,
                            'learning_type': 'online',
                            'sample_count': len(X),
                            'feature_count': X.shape[1] if len(X.shape) > 1 else 0
                        }
                        
                        # 如果有反馈数据，计算性能
                        if feedback_data and model_name in feedback_data:
                            actual_values = feedback_data[model_name]
                            if len(actual_values) == len(y):
                                mae = mean_absolute_error(actual_values, y)
                                learning_record['mae'] = float(mae)
                                learning_record['performance_improvement'] = self.calculate_performance_improvement(model_name, mae)
                        
                        self.learning_history.append(learning_record)
                        
                    except Exception as e:
                        logger.error(f"在线学习更新失败 {model_name}: {str(e)}")
            
            # 保存更新的模型和历史
            self.save_models()
            self.save_learning_history()
            
            # 评估是否需要批量重训练
            self.evaluate_retrain_need()
            
            logger.info("在线学习更新完成")
            
        except Exception as e:
            logger.error(f"在线学习更新过程失败: {str(e)}")
    
    def batch_learning_update(self, analysis_data_list: List[Dict]):
        """
        批量学习更新
        
        Args:
            analysis_data_list: 分析数据列表
        """
        try:
            if not analysis_data_list:
                logger.warning("没有批量学习数据")
                return
            
            # 合并所有特征
            all_features = []
            for data in analysis_data_list:
                features_df = self.extract_learning_features(data)
                if len(features_df) > 0:
                    all_features.append(features_df)
            
            if not all_features:
                logger.warning("没有有效的批量特征数据")
                return
            
            combined_features = pd.concat(all_features, ignore_index=True)
            
            # 准备训练数据
            training_data = self.prepare_features_and_targets(combined_features)
            
            if not training_data:
                logger.warning("没有有效的批量训练数据")
                return
            
            # 批量训练每个模型
            for model_name, (X, y) in training_data.items():
                if model_name in self.batch_models and len(X) > 10:  # 需要足够的样本
                    try:
                        # 分割训练和验证数据
                        X_train, X_val, y_train, y_val = train_test_split(
                            X, y, test_size=0.2, random_state=42
                        )
                        
                        # 训练模型
                        self.batch_models[model_name].fit(X_train, y_train)
                        
                        # 计算性能指标
                        y_pred = self.batch_models[model_name].predict(X_val)
                        mae = mean_absolute_error(y_val, y_pred)
                        mse = mean_squared_error(y_val, y_pred)
                        r2 = r2_score(y_val, y_pred)
                        
                        # 更新性能记录
                        if model_name not in self.model_performance:
                            self.model_performance[model_name] = []
                        
                        performance_record = {
                            'timestamp': datetime.now().isoformat(),
                            'training_type': 'batch',
                            'sample_count': len(X_train),
                            'mae': float(mae),
                            'mse': float(mse),
                            'r2': float(r2),
                            'feature_count': X.shape[1]
                        }
                        
                        self.model_performance[model_name].append(performance_record)
                        
                        logger.info(f"批量训练完成: {model_name}, MAE: {mae:.4f}, R2: {r2:.4f}")
                        
                    except Exception as e:
                        logger.error(f"批量训练失败 {model_name}: {str(e)}")
            
            # 保存模型和性能记录
            self.save_models()
            self.save_model_performance()
            
            # 记录批量学习历史
            batch_record = {
                'timestamp': datetime.now().isoformat(),
                'learning_type': 'batch',
                'total_samples': len(combined_features),
                'models_updated': list(training_data.keys()),
                'data_sources': len(analysis_data_list)
            }
            self.learning_history.append(batch_record)
            self.save_learning_history()
            
            logger.info("批量学习更新完成")
            
        except Exception as e:
            logger.error(f"批量学习更新过程失败: {str(e)}")
    
    def predict_with_ensemble(self, analysis_data: Dict) -> Dict[str, Any]:
        """
        使用集成模型进行预测
        
        Args:
            analysis_data: 分析数据
            
        Returns:
            预测结果字典
        """
        try:
            # 提取特征
            features_df = self.extract_learning_features(analysis_data)
            
            if len(features_df) == 0:
                logger.warning("没有有效的特征数据进行预测")
                return {}
            
            # 准备预测数据
            training_data = self.prepare_features_and_targets(features_df)
            
            if not training_data:
                logger.warning("没有有效的预测数据")
                return {}
            
            predictions = {}
            
            for model_name, (X, _) in training_data.items():
                try:
                    # 在线模型预测
                    online_pred = None
                    if model_name in self.online_models:
                        if hasattr(self.online_models[model_name], 'predict'):
                            online_pred = self.online_models[model_name].predict(X)
                    
                    # 批量模型预测
                    batch_pred = None
                    if model_name in self.batch_models:
                        if hasattr(self.batch_models[model_name], 'predict'):
                            batch_pred = self.batch_models[model_name].predict(X)
                    
                    # 集成预测结果
                    if online_pred is not None and batch_pred is not None:
                        # 加权平均（在线模型权重较低，批量模型权重较高）
                        ensemble_pred = 0.3 * online_pred + 0.7 * batch_pred
                    elif online_pred is not None:
                        ensemble_pred = online_pred
                    elif batch_pred is not None:
                        ensemble_pred = batch_pred
                    else:
                        continue
                    
                    # 计算预测统计信息
                    pred_stats = {
                        'mean': float(np.mean(ensemble_pred)),
                        'std': float(np.std(ensemble_pred)),
                        'min': float(np.min(ensemble_pred)),
                        'max': float(np.max(ensemble_pred)),
                        'median': float(np.median(ensemble_pred)),
                        'predictions': ensemble_pred.tolist() if len(ensemble_pred) <= 100 else ensemble_pred[:100].tolist()
                    }
                    
                    predictions[model_name] = pred_stats
                    
                    logger.info(f"模型 {model_name} 预测完成，均值: {pred_stats['mean']:.4f}")
                    
                except Exception as e:
                    logger.error(f"模型 {model_name} 预测失败: {str(e)}")
            
            # 添加预测元信息
            predictions['meta'] = {
                'prediction_time': datetime.now().isoformat(),
                'feature_count': X.shape[1] if len(list(training_data.values())) > 0 else 0,
                'sample_count': len(features_df),
                'models_used': list(predictions.keys())
            }
            
            return predictions
            
        except Exception as e:
            logger.error(f"集成预测失败: {str(e)}")
            return {}
    
    def calculate_performance_improvement(self, model_name: str, current_mae: float) -> float:
        """计算性能改善程度"""
        try:
            if model_name in self.model_performance and self.model_performance[model_name]:
                recent_performances = [record['mae'] for record in self.model_performance[model_name][-5:]]
                if recent_performances:
                    avg_historical_mae = np.mean(recent_performances)
                    improvement = (avg_historical_mae - current_mae) / avg_historical_mae
                    return float(improvement)
        except Exception:
            pass
        return 0.0
    
    def evaluate_retrain_need(self) -> bool:
        """评估是否需要重新训练"""
        try:
            # 检查学习历史，判断是否需要批量重训练
            recent_online_updates = [
                record for record in self.learning_history[-50:] 
                if record.get('learning_type') == 'online'
            ]
            
            if len(recent_online_updates) >= self.learning_config['batch_size']:
                logger.info("检测到足够的在线更新，建议进行批量重训练")
                return True
            
            # 检查性能下降
            for model_name, performance_history in self.model_performance.items():
                if len(performance_history) >= 3:
                    recent_mae = [record['mae'] for record in performance_history[-3:]]
                    if len(recent_mae) >= 2:
                        performance_trend = (recent_mae[-1] - recent_mae[0]) / recent_mae[0]
                        if performance_trend > self.learning_config['retrain_threshold']:
                            logger.warning(f"模型 {model_name} 性能下降 {performance_trend:.2%}，建议重训练")
                            return True
            
        except Exception as e:
            logger.error(f"评估重训练需求失败: {str(e)}")
        
        return False
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """获取学习统计信息"""
        try:
            stats = {
                'total_learning_sessions': len(self.learning_history),
                'online_updates': len([r for r in self.learning_history if r.get('learning_type') == 'online']),
                'batch_updates': len([r for r in self.learning_history if r.get('learning_type') == 'batch']),
                'models_count': {
                    'online': len(self.online_models),
                    'batch': len(self.batch_models)
                },
                'learning_timeline': []
            }
            
            # 最近7天的学习活动
            week_ago = datetime.now() - timedelta(days=7)
            recent_activities = [
                record for record in self.learning_history
                if datetime.fromisoformat(record['timestamp']) > week_ago
            ]
            
            stats['recent_activity'] = {
                'total_sessions': len(recent_activities),
                'online_sessions': len([r for r in recent_activities if r.get('learning_type') == 'online']),
                'batch_sessions': len([r for r in recent_activities if r.get('learning_type') == 'batch'])
            }
            
            # 模型性能趋势
            performance_trends = {}
            for model_name, performance_history in self.model_performance.items():
                if performance_history:
                    recent_performance = performance_history[-5:] if len(performance_history) >= 5 else performance_history
                    mae_trend = [record['mae'] for record in recent_performance]
                    
                    if len(mae_trend) >= 2:
                        trend_direction = "improving" if mae_trend[-1] < mae_trend[0] else "declining"
                        trend_rate = abs((mae_trend[-1] - mae_trend[0]) / mae_trend[0])
                    else:
                        trend_direction = "stable"
                        trend_rate = 0.0
                    
                    performance_trends[model_name] = {
                        'direction': trend_direction,
                        'rate': float(trend_rate),
                        'current_mae': float(mae_trend[-1]) if mae_trend else 0.0,
                        'sample_count': len(performance_history)
                    }
            
            stats['performance_trends'] = performance_trends
            
            return stats
            
        except Exception as e:
            logger.error(f"获取学习统计信息失败: {str(e)}")
            return {}
    
    def export_learning_report(self) -> str:
        """导出学习报告"""
        try:
            stats = self.get_learning_statistics()
            
            report = f"""
# 智能模型学习报告

## 学习概况
- 总学习会话: {stats.get('total_learning_sessions', 0)} 次
- 在线更新: {stats.get('online_updates', 0)} 次
- 批量更新: {stats.get('batch_updates', 0)} 次
- 活跃模型数: 在线模型 {stats.get('models_count', {}).get('online', 0)} 个，批量模型 {stats.get('models_count', {}).get('batch', 0)} 个

## 近期学习活动（最近7天）
- 学习会话: {stats.get('recent_activity', {}).get('total_sessions', 0)} 次
- 在线学习: {stats.get('recent_activity', {}).get('online_sessions', 0)} 次
- 批量学习: {stats.get('recent_activity', {}).get('batch_sessions', 0)} 次

## 模型性能趋势
"""
            
            for model_name, trend_info in stats.get('performance_trends', {}).items():
                direction_emoji = "📈" if trend_info['direction'] == 'improving' else "📉" if trend_info['direction'] == 'declining' else "➡️"
                report += f"""
### {model_name}
- 趋势: {direction_emoji} {trend_info['direction']} ({trend_info['rate']:.2%})
- 当前误差: {trend_info['current_mae']:.4f}
- 训练样本: {trend_info['sample_count']} 批次
"""
            
            report += f"""
## 建议
- 学习引擎运行状态: {'🟢 良好' if stats.get('total_learning_sessions', 0) > 0 else '🟡 需要更多数据'}
- 重训练建议: {'🔄 建议重训练' if self.evaluate_retrain_need() else '✅ 当前模型性能良好'}

报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            # 保存报告
            report_path = os.path.join(self.model_dir, f"learning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"学习报告已保存: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"导出学习报告失败: {str(e)}")
            return ""


def main():
    """测试自适应学习引擎"""
    # 创建学习引擎
    engine = AdaptiveLearningEngine()
    
    # 模拟分析数据
    sample_data = {
        'product_data': pd.DataFrame({
            '商品名称': ['测试商品1', '测试商品2'],
            '售价': [10.0, 20.0],
            '原价': [15.0, 25.0],
            '月售': [100, 200],
            '库存': [50, 80],
            '美团一级分类': ['食品', '饮品'],
            '美团三级分类': ['零食', '茶饮料']
        })
    }
    
    # 在线学习更新
    print("执行在线学习更新...")
    engine.online_learning_update(sample_data)
    
    # 预测测试
    print("执行预测测试...")
    predictions = engine.predict_with_ensemble(sample_data)
    print("预测结果:", json.dumps(predictions, indent=2, ensure_ascii=False))
    
    # 获取学习统计
    print("获取学习统计...")
    stats = engine.get_learning_statistics()
    print("学习统计:", json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 导出报告
    print("导出学习报告...")
    report_path = engine.export_learning_report()
    print(f"报告路径: {report_path}")


if __name__ == "__main__":
    main()