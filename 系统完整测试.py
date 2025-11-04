# -*- coding: utf-8 -*-
"""
智能门店经营看板系统 - 完整测试脚本
测试五大核心模型的集成效果和数据处理能力
"""

import os
import sys
import pandas as pd
import traceback
from datetime import datetime

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

def test_system_integration():
    """测试系统集成效果"""
    print("🚀 开始智能门店经营看板系统完整测试")
    print("=" * 60)
    
    test_results = {
        'data_loading': False,
        'core_logic': False,
        'five_models': False,
        'competitor_analysis': False,
        'report_generation': False
    }
    
    try:
        # 1. 测试数据加载
        print("\n📁 1. 测试数据文件加载...")
        data_file = "实际数据/测试数据-近30天数据.xlsx"
        
        if not os.path.exists(data_file):
            print(f"❌ 数据文件不存在: {data_file}")
            return test_results
        
        # 检查数据文件的sheets
        excel_file = pd.ExcelFile(data_file)
        required_sheets = ['门店订单数据', '竞对数据', '门店成本数据', '门店流量数据']
        
        print(f"📊 数据文件包含的sheets: {excel_file.sheet_names}")
        
        missing_sheets = [sheet for sheet in required_sheets if sheet not in excel_file.sheet_names]
        if missing_sheets:
            print(f"⚠️ 缺少必需的sheets: {missing_sheets}")
        else:
            print("✅ 所有必需的数据sheets都存在")
            test_results['data_loading'] = True
        
        # 检查数据量
        for sheet in required_sheets:
            if sheet in excel_file.sheet_names:
                df = pd.read_excel(data_file, sheet_name=sheet)
                print(f"  {sheet}: {len(df):,}条记录")
        
    except Exception as e:
        print(f"❌ 数据加载测试失败: {e}")
        return test_results
    
    try:
        # 2. 测试核心业务逻辑
        print("\n🔧 2. 测试核心业务逻辑集成...")
        
        try:
            from 核心业务逻辑 import process_order_data, CoreBusinessLogic
            print("✅ 核心业务逻辑模块导入成功")
            
            # 测试数据处理
            order_data = pd.read_excel(data_file, sheet_name='门店订单数据')
            cleaned_data, order_summary, business_metrics = process_order_data(order_data)
            
            print(f"✅ 数据处理成功:")
            print(f"  - 清洗后记录: {len(cleaned_data):,}条")
            print(f"  - 订单汇总: {len(order_summary):,}个订单")
            print(f"  - 业务指标: {len(business_metrics)}组")
            
            test_results['core_logic'] = True
            
        except Exception as e:
            print(f"❌ 核心业务逻辑测试失败: {e}")
            traceback.print_exc()
    
    except Exception as e:
        print(f"❌ 核心逻辑测试出错: {e}")
    
    try:
        # 3. 测试五大模型系统
        print("\n🧠 3. 测试五大模型系统集成...")
        
        try:
            from 智能门店经营看板系统 import SmartStoreDashboard
            print("✅ 智能门店经营看板系统导入成功")
            
            # 初始化系统
            dashboard = SmartStoreDashboard()
            print("✅ 智能看板系统初始化成功")
            
            # 准备测试数据
            store_data = {
                'store_id': 'TEST_STORE_001',
                'order_data': pd.read_excel(data_file, sheet_name='门店订单数据')
            }
            
            # 加载竞对数据
            competitor_data = pd.read_excel(data_file, sheet_name='竞对数据')
            
            # 执行综合分析
            print("🔄 开始执行综合分析...")
            analysis_result = dashboard.comprehensive_analysis(
                store_data=store_data,
                competitor_data=competitor_data
            )
            
            print("✅ 五大模型分析完成!")
            
            # 检查分析结果
            key_sections = [
                'analysis_timestamp', 'store_overview', 'data_quality',
                'hypothesis_analysis', 'trend_predictions', 'strategic_decisions',
                'risk_assessment', 'operation_insights'
            ]
            
            for section in key_sections:
                if section in analysis_result:
                    print(f"  ✅ {section}: 已生成")
                else:
                    print(f"  ⚠️ {section}: 缺失")
            
            test_results['five_models'] = True
            
        except Exception as e:
            print(f"❌ 五大模型系统测试失败: {e}")
            traceback.print_exc()
    
    except Exception as e:
        print(f"❌ 模型系统测试出错: {e}")
    
    try:
        # 4. 测试竞对分析
        print("\n🕵️ 4. 测试竞对倒推分析...")
        
        try:
            from 竞对商业情报倒推分析器 import CompetitorIntelligenceAnalyzer
            print("✅ 竞对分析器导入成功")
            
            analyzer = CompetitorIntelligenceAnalyzer()
            if analyzer.load_data(data_file):
                analyzer.process_order_data_with_core_logic()
                analyzer.analyze_our_cost_structure()
                analyzer.reverse_engineer_competitor_costs()
                
                print("✅ 竞对倒推分析完成")
                test_results['competitor_analysis'] = True
            else:
                print("❌ 竞对数据加载失败")
                
        except Exception as e:
            print(f"❌ 竞对分析测试失败: {e}")
            traceback.print_exc()
    
    except Exception as e:
        print(f"❌ 竞对分析测试出错: {e}")
    
    # 5. 测试报告生成
    print("\n📋 5. 测试报告生成...")
    try:
        # 创建测试报告
        report_dir = "测试报告"
        os.makedirs(report_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        test_report = os.path.join(report_dir, f"系统测试报告_{timestamp}.md")
        
        with open(test_report, 'w', encoding='utf-8') as f:
            f.write("# 智能门店经营看板系统测试报告\n\n")
            f.write(f"**测试时间**: {datetime.now()}\n\n")
            
            f.write("## 测试结果汇总\n\n")
            for test_name, result in test_results.items():
                status = "✅ 通过" if result else "❌ 失败"
                f.write(f"- {test_name}: {status}\n")
            
            f.write(f"\n## 总体评估\n\n")
            passed_tests = sum(test_results.values())
            total_tests = len(test_results)
            f.write(f"通过测试: {passed_tests}/{total_tests}\n")
            f.write(f"成功率: {passed_tests/total_tests*100:.1f}%\n")
        
        print(f"✅ 测试报告已生成: {test_report}")
        test_results['report_generation'] = True
        
    except Exception as e:
        print(f"❌ 报告生成失败: {e}")
    
    # 最终结果
    print("\n" + "="*60)
    print("🎯 系统测试完成汇总")
    print("="*60)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"\n📊 总体评估: {passed_tests}/{total_tests} 通过 ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("\n🎉 恭喜！所有测试都通过了，系统集成完成！")
    elif passed_tests >= total_tests * 0.8:
        print(f"\n✅ 系统基本可用，{total_tests - passed_tests}个功能需要优化")
    else:
        print(f"\n⚠️ 系统需要进一步完善，{total_tests - passed_tests}个核心功能有问题")
    
    return test_results

def test_visual_interface():
    """测试可视化界面"""
    print("\n🎨 测试可视化界面...")
    
    try:
        # 检查streamlit和相关依赖
        import streamlit
        import plotly
        print("✅ 可视化依赖包检查通过")
        
        # 检查可视化文件
        visual_file = "智能门店经营看板_可视化.py"
        if os.path.exists(visual_file):
            print("✅ 可视化界面文件存在")
            print("💡 可以运行: streamlit run 智能门店经营看板_可视化.py")
            return True
        else:
            print(f"❌ 可视化文件不存在: {visual_file}")
            return False
            
    except ImportError as e:
        print(f"❌ 可视化依赖缺失: {e}")
        print("💡 请运行: pip install streamlit plotly")
        return False

if __name__ == "__main__":
    # 执行完整系统测试
    test_results = test_system_integration()
    
    # 测试可视化界面
    test_visual_interface()
    
    print("\n" + "="*60)
    print("📝 测试建议:")
    print("1. 如果所有测试通过，可以启动可视化界面进行使用")
    print("2. 如果有测试失败，请查看错误信息进行修复")
    print("3. 可视化界面启动命令: streamlit run 智能门店经营看板_可视化.py")
    print("="*60)