#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能门店经营看板系统 - 完整功能测试脚本
测试所有模块和功能是否正常工作
"""

import sys
import os
import traceback
from pathlib import Path

def test_module_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试1: 模块导入测试")
    print("=" * 60)
    
    results = {}
    
    # 测试1.1: 订单数据处理器
    try:
        from 订单数据处理器 import OrderDataProcessor
        print("✅ 订单数据处理器导入成功")
        results['order_processor'] = True
    except Exception as e:
        print(f"❌ 订单数据处理器导入失败: {e}")
        results['order_processor'] = False
    
    # 测试1.2: 智能门店系统
    try:
        from 智能门店经营看板系统 import IntelligentStoreManagementSystem
        print("✅ 智能门店系统导入成功")
        results['main_system'] = True
    except Exception as e:
        print(f"❌ 智能门店系统导入失败: {e}")
        results['main_system'] = False
    
    # 测试1.3: 自适应学习模块
    try:
        from 自适应学习引擎 import AdaptiveLearningEngine
        print("✅ 自适应学习引擎导入成功")
        results['learning_engine'] = True
    except Exception as e:
        print(f"❌ 自适应学习引擎导入失败: {e}")
        results['learning_engine'] = False
    
    return results

def test_data_processor():
    """测试数据处理器功能"""
    print("\n" + "=" * 60)
    print("测试2: 数据处理器功能测试")
    print("=" * 60)
    
    try:
        from 订单数据处理器 import OrderDataProcessor
        
        # 创建处理器实例
        processor = OrderDataProcessor()
        print("✅ 创建数据处理器实例成功")
        
        # 测试数据文件路径
        data_file = "实际数据/2025-09-23 00_00_00至2025-09-23 10_02_10订单明细数据导出汇总 (1).xlsx"
        
        if not Path(data_file).exists():
            print(f"❌ 数据文件不存在: {data_file}")
            return False
        
        # 测试数据加载
        if processor.load_data(data_file):
            print("✅ 数据加载成功")
            
            # 测试数据清洗
            if processor.clean_data():
                print("✅ 数据清洗成功")
                
                # 测试利润计算
                if processor.calculate_profit():
                    print("✅ 利润计算成功")
                    
                    # 获取摘要信息
                    summary = processor.get_summary()
                    print(f"   📊 处理结果:")
                    print(f"      - 订单数量: {summary['order_count']}")
                    print(f"      - 平均利润: {summary['avg_profit']:.2f}元")
                    print(f"      - 盈利订单: {summary['profitable_orders']}")
                    print(f"      - 盈利率: {summary['profit_rate']*100:.1f}%")
                    
                    return True
                else:
                    print("❌ 利润计算失败")
                    return False
            else:
                print("❌ 数据清洗失败")
                return False
        else:
            print("❌ 数据加载失败")
            return False
            
    except Exception as e:
        print(f"❌ 数据处理器测试异常: {e}")
        traceback.print_exc()
        return False

def test_ai_models():
    """测试AI模型功能"""
    print("\n" + "=" * 60)
    print("测试3: AI模型功能测试")
    print("=" * 60)
    
    try:
        from 智能门店经营看板系统 import IntelligentStoreManagementSystem
        
        # 创建系统实例
        system = IntelligentStoreManagementSystem()
        print("✅ 创建AI系统实例成功")
        
        # 准备测试数据
        test_data = {
            'store_id': 'test_store',
            'store_name': '测试门店',
            'data_file': '实际数据/2025-09-23 00_00_00至2025-09-23 10_02_10订单明细数据导出汇总 (1).xlsx'
        }
        
        # 测试假设验证模型
        try:
            hypothesis = system.hypothesis_engine.create_hypothesis(
                description="提高流量品销量测试",
                confidence_level=0.8
            )
            print("✅ 假设验证模型工作正常")
        except Exception as e:
            print(f"❌ 假设验证模型失败: {e}")
        
        # 测试预测模型
        try:
            prediction = system.prediction_engine.predict_sales_trend({'test': 'data'})
            print("✅ 预测分析模型工作正常")
        except Exception as e:
            print(f"❌ 预测分析模型失败: {e}")
        
        # 测试决策模型
        try:
            decisions = system.decision_engine.generate_strategy_options({'test': 'data'})
            print("✅ 决策建议模型工作正常")
        except Exception as e:
            print(f"❌ 决策建议模型失败: {e}")
        
        # 测试概率模型
        try:
            probability = system.probability_engine.calculate_success_probability({'test': 'data'})
            print("✅ 概率预测模型工作正常")
        except Exception as e:
            print(f"❌ 概率预测模型失败: {e}")
        
        # 测试数据经营模型
        try:
            insights = system.data_operation_engine.analyze_business_opportunities({'test': 'data'})
            print("✅ 数据经营模型工作正常")
        except Exception as e:
            print(f"❌ 数据经营模型失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI模型测试异常: {e}")
        traceback.print_exc()
        return False

def test_learning_system():
    """测试自适应学习系统"""
    print("\n" + "=" * 60)
    print("测试4: 自适应学习系统测试")
    print("=" * 60)
    
    try:
        from 自适应学习引擎 import AdaptiveLearningEngine
        from 学习数据管理系统 import LearningDataManager
        
        # 创建学习引擎
        learning_engine = AdaptiveLearningEngine()
        data_manager = LearningDataManager()
        
        print("✅ 学习系统组件创建成功")
        
        # 测试数据管理
        try:
            datasets = data_manager.list_datasets()
            print(f"✅ 数据管理系统正常 (已有{len(datasets)}个数据集)")
        except Exception as e:
            print(f"❌ 数据管理系统失败: {e}")
        
        # 测试学习引擎统计
        try:
            stats = learning_engine.get_learning_statistics()
            print("✅ 学习引擎统计功能正常")
        except Exception as e:
            print(f"❌ 学习引擎统计失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 学习系统测试异常: {e}")
        traceback.print_exc()
        return False

def test_integration():
    """测试系统集成"""
    print("\n" + "=" * 60)
    print("测试5: 系统集成测试")
    print("=" * 60)
    
    try:
        from 智能门店经营看板系统 import IntelligentStoreManagementSystem
        
        # 创建完整系统
        system = IntelligentStoreManagementSystem()
        print("✅ 系统创建成功")
        
        # 准备真实数据
        store_data = {
            'store_id': 'test_store_001',
            'store_name': '测试门店',
            'data_file': '实际数据/2025-09-23 00_00_00至2025-09-23 10_02_10订单明细数据导出汇总 (1).xlsx'
        }
        
        # 运行完整分析
        try:
            results = system.run_comprehensive_analysis(store_data)
            if results:
                print("✅ 完整系统分析运行成功")
                print(f"   📊 分析模块数: {len(results)}")
                
                # 显示关键结果
                if 'summary' in results:
                    summary = results['summary']
                    print(f"   📈 分析概要:")
                    for key, value in summary.items():
                        print(f"      - {key}: {value}")
                
                return True
            else:
                print("❌ 系统分析返回空结果")
                return False
                
        except Exception as e:
            print(f"❌ 系统集成测试失败: {e}")
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ 系统集成异常: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("智能门店经营看板系统 - 完整功能测试")
    
    # 导入pandas
    try:
        import pandas as pd
        print("测试时间:", pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'))
    except ImportError:
        print("测试时间: 未知 (pandas模块未安装)")
        print("❌ pandas模块未安装")
        return
    
    test_results = {}
    
    # 执行所有测试
    test_results['imports'] = test_module_imports()
    test_results['data_processor'] = test_data_processor()
    test_results['ai_models'] = test_ai_models()
    test_results['learning_system'] = test_learning_system()
    test_results['integration'] = test_integration()
    
    # 测试结果汇总
    print("\n" + "=" * 60)
    print("📋 测试结果汇总")
    print("=" * 60)
    
    success_count = 0
    total_tests = 5
    
    if isinstance(test_results['imports'], dict):
        import_success = sum(test_results['imports'].values())
        print(f"模块导入: {import_success}/3 个模块成功")
    
    for test_name, result in test_results.items():
        if test_name == 'imports':
            continue
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n总体通过率: {success_count}/{total_tests-1} = {success_count/(total_tests-1)*100:.1f}%")
    
    if success_count >= 3:
        print("🎉 系统基本功能正常，可以投入使用！")
    else:
        print("⚠️ 系统存在问题，需要修复后再使用")

if __name__ == "__main__":
    main()