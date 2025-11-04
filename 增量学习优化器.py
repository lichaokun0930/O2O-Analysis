#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量学习优化器 - 智能参数调优和性能监控
支持动态学习率调整、特征重要性分析、模型集成优化
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import json
import os
from datetime import datetime, timedelta
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import IsolationForest
import logging

logger = logging.getLogger(__name__)

class IncrementalLearningOptimizer:
    """增量学习优化器"""
    
    def __init__(self, learning_engine):
        """
        初始化增量学习优化器
        
        Args:
            learning_engine: 自适应学习引擎实例
        """
        self.learning_engine = learning_engine
        
        # 优化配置
        self.optimization_config = {
            'learning_rate_min': 0.001,
            'learning_rate_max': 0.1,
            'learning_rate_decay': 0.95,
            'performance_window': 10,
            'improvement_threshold': 0.05,
            'feature_importance_threshold': 0.01,
            'outlier_contamination': 0.1,
            'cross_validation_folds': 3
        }
        
        # 性能追踪
        self.performance_history = {}
        self.feature_importance_history = {}
        self.learning_curve_data = {}
        
        # 动态参数
        self.dynamic_params = {}
        
        # 异常检测器
        self.outlier_detectors = {}
        
        logger.info("增量学习优化器初始化完成")
    
    def adaptive_learning_rate_adjustment(self, model_name: str, current_performance: float) -> float:
        """
        自适应学习率调整
        
        Args:
            model_name: 模型名称
            current_performance: 当前性能指标
            
        Returns:
            调整后的学习率
        """
        try:
            if model_name not in self.performance_history:
                self.performance_history[model_name] = []
            
            self.performance_history[model_name].append({
                'timestamp': datetime.now().isoformat(),
                'performance': current_performance
            })
            
            # 保持历史记录在合理范围内
            if len(self.performance_history[model_name]) > self.optimization_config['performance_window']:
                self.performance_history[model_name] = self.performance_history[model_name][-self.optimization_config['performance_window']:]
            
            # 初始学习率
            if model_name not in self.dynamic_params:
                self.dynamic_params[model_name] = {
                    'learning_rate': 0.01,
                    'momentum': 0.9,
                    'adjustment_count': 0
                }
            
            current_lr = self.dynamic_params[model_name]['learning_rate']
            
            # 如果有足够的历史数据，分析性能趋势
            if len(self.performance_history[model_name]) >= 3:
                recent_performances = [record['performance'] for record in self.performance_history[model_name][-3:]]
                
                # 计算性能趋势
                performance_trend = (recent_performances[-1] - recent_performances[0]) / recent_performances[0]
                
                if performance_trend < -self.optimization_config['improvement_threshold']:
                    # 性能在改善，稍微增加学习率
                    new_lr = min(current_lr * 1.05, self.optimization_config['learning_rate_max'])
                    adjustment_reason = "性能改善，增加学习率"
                elif performance_trend > self.optimization_config['improvement_threshold']:
                    # 性能在恶化，减少学习率
                    new_lr = max(current_lr * self.optimization_config['learning_rate_decay'], 
                                self.optimization_config['learning_rate_min'])
                    adjustment_reason = "性能恶化，减少学习率"
                else:
                    # 性能稳定，保持当前学习率
                    new_lr = current_lr
                    adjustment_reason = "性能稳定，保持学习率"
                
                self.dynamic_params[model_name]['learning_rate'] = new_lr
                self.dynamic_params[model_name]['adjustment_count'] += 1
                
                logger.info(f"模型 {model_name} 学习率调整: {current_lr:.6f} -> {new_lr:.6f} ({adjustment_reason})")
                
                return new_lr
            
            return current_lr
            
        except Exception as e:
            logger.error(f"自适应学习率调整失败: {str(e)}")
            return 0.01  # 返回默认学习率
    
    def feature_importance_analysis(self, model_name: str, X: np.ndarray, y: np.ndarray, feature_names: List[str] = None) -> Dict[str, float]:
        """
        特征重要性分析
        
        Args:
            model_name: 模型名称
            X: 特征数据
            y: 目标数据
            feature_names: 特征名称列表
            
        Returns:
            特征重要性字典
        """
        try:
            if feature_names is None:
                feature_names = [f'feature_{i}' for i in range(X.shape[1])]
            
            # 获取模型的特征重要性
            model = None
            if model_name in self.learning_engine.batch_models:
                model = self.learning_engine.batch_models[model_name]
            elif model_name in self.learning_engine.online_models:
                model = self.learning_engine.online_models[model_name]
            
            if model is None or not hasattr(model, 'feature_importances_'):
                logger.warning(f"模型 {model_name} 不支持特征重要性分析")
                return {}
            
            # 获取特征重要性
            importances = model.feature_importances_
            
            # 创建特征重要性字典
            importance_dict = {}
            for i, importance in enumerate(importances):
                if i < len(feature_names):
                    importance_dict[feature_names[i]] = float(importance)
            
            # 记录特征重要性历史
            if model_name not in self.feature_importance_history:
                self.feature_importance_history[model_name] = []
            
            importance_record = {
                'timestamp': datetime.now().isoformat(),
                'importances': importance_dict,
                'top_features': sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:5]
            }
            
            self.feature_importance_history[model_name].append(importance_record)
            
            # 保持历史记录在合理范围内
            if len(self.feature_importance_history[model_name]) > 20:
                self.feature_importance_history[model_name] = self.feature_importance_history[model_name][-20:]
            
            logger.info(f"模型 {model_name} 特征重要性分析完成")
            
            return importance_dict
            
        except Exception as e:
            logger.error(f"特征重要性分析失败: {str(e)}")
            return {}
    
    def dynamic_feature_selection(self, model_name: str, X: np.ndarray, y: np.ndarray, feature_names: List[str] = None) -> Tuple[np.ndarray, List[str]]:
        """
        动态特征选择
        
        Args:
            model_name: 模型名称
            X: 原始特征数据
            y: 目标数据
            feature_names: 特征名称列表
            
        Returns:
            筛选后的特征数据和特征名称
        """
        try:
            if feature_names is None:
                feature_names = [f'feature_{i}' for i in range(X.shape[1])]
            
            # 分析特征重要性
            importance_dict = self.feature_importance_analysis(model_name, X, y, feature_names)
            
            if not importance_dict:
                return X, feature_names
            
            # 筛选重要特征
            threshold = self.optimization_config['feature_importance_threshold']
            important_features = [name for name, importance in importance_dict.items() 
                                if importance >= threshold]
            
            if len(important_features) == 0:
                # 如果没有特征达到阈值，选择前50%的特征
                sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
                important_features = [name for name, _ in sorted_features[:max(1, len(sorted_features)//2)]]
            
            # 筛选特征数据
            important_indices = [i for i, name in enumerate(feature_names) if name in important_features]
            selected_X = X[:, important_indices]
            selected_feature_names = [feature_names[i] for i in important_indices]
            
            logger.info(f"模型 {model_name} 特征选择: {len(feature_names)} -> {len(selected_feature_names)} 特征")
            
            return selected_X, selected_feature_names
            
        except Exception as e:
            logger.error(f"动态特征选择失败: {str(e)}")
            return X, feature_names
    
    def outlier_detection_and_filtering(self, X: np.ndarray, y: np.ndarray, model_name: str = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        异常检测和过滤
        
        Args:
            X: 特征数据
            y: 目标数据
            model_name: 模型名称（用于缓存检测器）
            
        Returns:
            过滤后的特征和目标数据
        """
        try:
            if len(X) < 10:  # 数据量太少，不进行异常检测
                return X, y
            
            # 获取或创建异常检测器
            detector_key = model_name or 'default'
            
            if detector_key not in self.outlier_detectors:
                self.outlier_detectors[detector_key] = IsolationForest(
                    contamination=self.optimization_config['outlier_contamination'],
                    random_state=42
                )
            
            detector = self.outlier_detectors[detector_key]
            
            # 检测异常
            outlier_labels = detector.fit_predict(X)
            
            # 过滤异常值
            normal_mask = outlier_labels == 1
            filtered_X = X[normal_mask]
            filtered_y = y[normal_mask]
            
            outlier_count = np.sum(outlier_labels == -1)
            logger.info(f"异常检测完成: 原始样本 {len(X)}, 异常样本 {outlier_count}, 保留样本 {len(filtered_X)}")
            
            return filtered_X, filtered_y
            
        except Exception as e:
            logger.error(f"异常检测失败: {str(e)}")
            return X, y
    
    def cross_validation_performance_check(self, model, X: np.ndarray, y: np.ndarray, model_name: str) -> Dict[str, float]:
        """
        交叉验证性能检查
        
        Args:
            model: 模型实例
            X: 特征数据
            y: 目标数据
            model_name: 模型名称
            
        Returns:
            交叉验证性能指标
        """
        try:
            if len(X) < self.optimization_config['cross_validation_folds']:
                logger.warning(f"样本数量不足进行交叉验证: {len(X)}")
                return {}
            
            # 交叉验证评分
            cv_scores = cross_val_score(
                model, X, y, 
                cv=self.optimization_config['cross_validation_folds'], 
                scoring='neg_mean_absolute_error'
            )
            
            cv_performance = {
                'cv_mean_mae': float(-cv_scores.mean()),
                'cv_std_mae': float(cv_scores.std()),
                'cv_best_mae': float(-cv_scores.max()),
                'cv_worst_mae': float(-cv_scores.min())
            }
            
            # 记录学习曲线数据
            if model_name not in self.learning_curve_data:
                self.learning_curve_data[model_name] = []
            
            curve_point = {
                'timestamp': datetime.now().isoformat(),
                'sample_size': len(X),
                'cv_performance': cv_performance
            }
            
            self.learning_curve_data[model_name].append(curve_point)
            
            logger.info(f"模型 {model_name} 交叉验证: MAE {cv_performance['cv_mean_mae']:.4f} ± {cv_performance['cv_std_mae']:.4f}")
            
            return cv_performance
            
        except Exception as e:
            logger.error(f"交叉验证性能检查失败: {str(e)}")
            return {}
    
    def model_ensemble_optimization(self, predictions_dict: Dict[str, np.ndarray], y_true: np.ndarray) -> Dict[str, float]:
        """
        模型集成优化
        
        Args:
            predictions_dict: 各模型预测结果字典
            y_true: 真实值
            
        Returns:
            优化的集成权重
        """
        try:
            if not predictions_dict or len(predictions_dict) < 2:
                return {}
            
            # 计算各模型的单独性能
            model_performances = {}
            for model_name, predictions in predictions_dict.items():
                if len(predictions) == len(y_true):
                    mae = mean_absolute_error(y_true, predictions)
                    model_performances[model_name] = mae
            
            if not model_performances:
                return {}
            
            # 基于性能的权重计算（性能越好权重越高）
            # 使用倒数权重：权重 = 1/MAE
            inverse_maes = {name: 1/mae if mae > 0 else 1.0 for name, mae in model_performances.items()}
            total_inverse_mae = sum(inverse_maes.values())
            
            # 标准化权重
            ensemble_weights = {
                name: inverse_mae / total_inverse_mae 
                for name, inverse_mae in inverse_maes.items()
            }
            
            # 验证集成效果
            ensemble_prediction = np.zeros_like(y_true, dtype=float)
            for model_name, weight in ensemble_weights.items():
                if model_name in predictions_dict:
                    ensemble_prediction += weight * predictions_dict[model_name]
            
            ensemble_mae = mean_absolute_error(y_true, ensemble_prediction)
            
            # 检查集成是否优于最佳单个模型
            best_single_mae = min(model_performances.values())
            improvement = (best_single_mae - ensemble_mae) / best_single_mae
            
            logger.info(f"集成优化结果: 最佳单模型MAE {best_single_mae:.4f}, 集成MAE {ensemble_mae:.4f}, 改善 {improvement:.2%}")
            
            # 只有在集成有显著改善时才返回权重
            if improvement > 0.01:  # 至少1%的改善
                return ensemble_weights
            else:
                # 返回均等权重
                equal_weight = 1.0 / len(predictions_dict)
                return {name: equal_weight for name in predictions_dict.keys()}
            
        except Exception as e:
            logger.error(f"模型集成优化失败: {str(e)}")
            return {}
    
    def smart_retraining_decision(self, model_name: str) -> Dict[str, Any]:
        """
        智能重训练决策
        
        Args:
            model_name: 模型名称
            
        Returns:
            重训练决策信息
        """
        try:
            decision = {
                'should_retrain': False,
                'confidence': 0.0,
                'reasons': [],
                'recommended_action': 'continue',
                'priority': 'low'
            }
            
            # 检查性能趋势
            if model_name in self.performance_history:
                performance_records = self.performance_history[model_name]
                
                if len(performance_records) >= 5:
                    recent_performances = [record['performance'] for record in performance_records[-5:]]
                    
                    # 计算性能趋势
                    trend_slope = np.polyfit(range(len(recent_performances)), recent_performances, 1)[0]
                    
                    if trend_slope > 0.05:  # 性能恶化趋势
                        decision['should_retrain'] = True
                        decision['confidence'] += 0.3
                        decision['reasons'].append("性能持续恶化")
                        decision['priority'] = 'high'
                    
                    # 检查性能波动
                    performance_std = np.std(recent_performances)
                    performance_mean = np.mean(recent_performances)
                    cv = performance_std / performance_mean if performance_mean > 0 else 0
                    
                    if cv > 0.2:  # 高变异系数表示不稳定
                        decision['should_retrain'] = True
                        decision['confidence'] += 0.2
                        decision['reasons'].append("性能不稳定")
            
            # 检查学习曲线
            if model_name in self.learning_curve_data:
                curve_data = self.learning_curve_data[model_name]
                
                if len(curve_data) >= 3:
                    recent_cv_scores = [record['cv_performance']['cv_mean_mae'] for record in curve_data[-3:] 
                                      if 'cv_performance' in record and 'cv_mean_mae' in record['cv_performance']]
                    
                    if len(recent_cv_scores) >= 2:
                        cv_trend = (recent_cv_scores[-1] - recent_cv_scores[0]) / recent_cv_scores[0]
                        
                        if cv_trend > 0.1:  # 交叉验证性能恶化
                            decision['should_retrain'] = True
                            decision['confidence'] += 0.3
                            decision['reasons'].append("交叉验证性能下降")
            
            # 检查数据新鲜度
            if model_name in self.learning_engine.model_performance:
                last_update_records = self.learning_engine.model_performance[model_name]
                
                if last_update_records:
                    last_update_time = datetime.fromisoformat(last_update_records[-1]['timestamp'])
                    days_since_update = (datetime.now() - last_update_time).days
                    
                    if days_since_update > 7:  # 超过7天未更新
                        decision['should_retrain'] = True
                        decision['confidence'] += 0.2
                        decision['reasons'].append(f"模型已{days_since_update}天未更新")
            
            # 设置推荐行动
            if decision['confidence'] >= 0.5:
                decision['recommended_action'] = 'retrain_immediately'
                decision['priority'] = 'high'
            elif decision['confidence'] >= 0.3:
                decision['recommended_action'] = 'schedule_retrain'
                decision['priority'] = 'medium'
            else:
                decision['recommended_action'] = 'monitor'
                decision['priority'] = 'low'
            
            logger.info(f"模型 {model_name} 重训练决策: {decision['recommended_action']} (置信度: {decision['confidence']:.2f})")
            
            return decision
            
        except Exception as e:
            logger.error(f"智能重训练决策失败: {str(e)}")
            return {
                'should_retrain': False,
                'confidence': 0.0,
                'reasons': ['决策系统故障'],
                'recommended_action': 'manual_check',
                'priority': 'medium'
            }
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """生成优化报告"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'models_monitored': len(self.performance_history),
                'optimization_summary': {},
                'performance_trends': {},
                'feature_importance_analysis': {},
                'retraining_recommendations': {},
                'learning_statistics': {}
            }
            
            # 性能趋势分析
            for model_name, history in self.performance_history.items():
                if len(history) >= 2:
                    performances = [record['performance'] for record in history]
                    
                    report['performance_trends'][model_name] = {
                        'current_performance': performances[-1],
                        'best_performance': min(performances),
                        'worst_performance': max(performances),
                        'trend_direction': 'improving' if performances[-1] < performances[0] else 'declining',
                        'stability': float(np.std(performances[-5:])) if len(performances) >= 5 else 0.0
                    }
            
            # 特征重要性分析
            for model_name, importance_history in self.feature_importance_history.items():
                if importance_history:
                    latest_importance = importance_history[-1]['importances']
                    top_features = sorted(latest_importance.items(), key=lambda x: x[1], reverse=True)[:3]
                    
                    report['feature_importance_analysis'][model_name] = {
                        'top_features': [{'feature': name, 'importance': importance} 
                                       for name, importance in top_features],
                        'feature_count': len(latest_importance)
                    }
            
            # 重训练推荐
            for model_name in self.learning_engine.online_models.keys():
                decision = self.smart_retraining_decision(model_name)
                report['retraining_recommendations'][model_name] = decision
            
            # 学习统计
            total_adjustments = sum(params.get('adjustment_count', 0) 
                                  for params in self.dynamic_params.values())
            
            report['learning_statistics'] = {
                'total_learning_rate_adjustments': total_adjustments,
                'active_models': len(self.dynamic_params),
                'outlier_detectors': len(self.outlier_detectors),
                'feature_selections_performed': len(self.feature_importance_history)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成优化报告失败: {str(e)}")
            return {'error': str(e)}
    
    def save_optimization_state(self, file_path: str = None):
        """保存优化状态"""
        try:
            if file_path is None:
                file_path = os.path.join(self.learning_engine.model_dir, 'optimization_state.json')
            
            state = {
                'performance_history': self.performance_history,
                'feature_importance_history': self.feature_importance_history,
                'learning_curve_data': self.learning_curve_data,
                'dynamic_params': self.dynamic_params,
                'optimization_config': self.optimization_config
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            logger.info(f"优化状态已保存: {file_path}")
            
        except Exception as e:
            logger.error(f"保存优化状态失败: {str(e)}")
    
    def load_optimization_state(self, file_path: str = None):
        """加载优化状态"""
        try:
            if file_path is None:
                file_path = os.path.join(self.learning_engine.model_dir, 'optimization_state.json')
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                self.performance_history = state.get('performance_history', {})
                self.feature_importance_history = state.get('feature_importance_history', {})
                self.learning_curve_data = state.get('learning_curve_data', {})
                self.dynamic_params = state.get('dynamic_params', {})
                
                # 合并配置（保留用户自定义的配置）
                loaded_config = state.get('optimization_config', {})
                self.optimization_config.update(loaded_config)
                
                logger.info(f"优化状态已加载: {file_path}")
            
        except Exception as e:
            logger.error(f"加载优化状态失败: {str(e)}")


def main():
    """测试增量学习优化器"""
    from 自适应学习引擎 import AdaptiveLearningEngine
    
    # 创建学习引擎和优化器
    engine = AdaptiveLearningEngine()
    optimizer = IncrementalLearningOptimizer(engine)
    
    # 模拟优化过程
    print("测试增量学习优化器...")
    
    # 模拟性能数据
    for i in range(10):
        model_name = 'test_model'
        # 模拟性能逐渐改善的场景
        performance = 1.0 - i * 0.05 + np.random.normal(0, 0.02)
        
        # 调整学习率
        new_lr = optimizer.adaptive_learning_rate_adjustment(model_name, performance)
        print(f"迭代 {i+1}: 性能 {performance:.4f}, 学习率 {new_lr:.6f}")
    
    # 生成优化报告
    report = optimizer.generate_optimization_report()
    print("\n优化报告:", json.dumps(report, indent=2, ensure_ascii=False))
    
    # 测试重训练决策
    decision = optimizer.smart_retraining_decision('test_model')
    print("\n重训练决策:", json.dumps(decision, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()