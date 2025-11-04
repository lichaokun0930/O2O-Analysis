#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景营销智能决策引擎 - 诊断脚本
快速检查模块是否正常加载
"""

import sys
print("=" * 60)
print("🔍 场景营销智能决策引擎诊断")
print("=" * 60)

# 1. 检查Python版本
print(f"\n1️⃣ Python版本: {sys.version}")

# 2. 检查依赖包
print("\n2️⃣ 检查依赖包...")
dependencies = {
    'mlxtend': 'mlxtend',
    'xgboost': 'xgboost',
    'sklearn': 'scikit-learn',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'plotly': 'plotly'
}

for module, package in dependencies.items():
    try:
        exec(f"import {module}")
        version = eval(f"{module}.__version__")
        print(f"   ✅ {package}: {version}")
    except ImportError as e:
        print(f"   ❌ {package}: 未安装 ({e})")
    except AttributeError:
        print(f"   ✅ {package}: 已安装（无版本信息）")

# 3. 检查场景营销智能决策引擎模块
print("\n3️⃣ 检查场景营销智能决策引擎...")
try:
    from 场景营销智能决策引擎 import (
        SceneMarketingIntelligence,
        ProductCombinationMiner,
        SceneRecognitionModel,
        RFMCustomerSegmentation,
        SceneDecisionTreeRules
    )
    print("   ✅ 场景营销智能决策引擎加载成功")
    
    # 检查各组件
    print("\n4️⃣ 检查各组件...")
    print(f"   ✅ ProductCombinationMiner: {ProductCombinationMiner}")
    print(f"   ✅ SceneRecognitionModel: {SceneRecognitionModel}")
    print(f"   ✅ RFMCustomerSegmentation: {RFMCustomerSegmentation}")
    print(f"   ✅ SceneDecisionTreeRules: {SceneDecisionTreeRules}")
    print(f"   ✅ SceneMarketingIntelligence: {SceneMarketingIntelligence}")
    
    # 5. 测试实例化
    print("\n5️⃣ 测试实例化...")
    try:
        miner = ProductCombinationMiner()
        print("   ✅ ProductCombinationMiner实例化成功")
    except Exception as e:
        print(f"   ❌ ProductCombinationMiner实例化失败: {e}")
    
    try:
        model = SceneRecognitionModel()
        print("   ✅ SceneRecognitionModel实例化成功")
    except Exception as e:
        print(f"   ❌ SceneRecognitionModel实例化失败: {e}")
    
    try:
        rfm = RFMCustomerSegmentation()
        print("   ✅ RFMCustomerSegmentation实例化成功")
    except Exception as e:
        print(f"   ❌ RFMCustomerSegmentation实例化失败: {e}")

except ImportError as e:
    print(f"   ❌ 场景营销智能决策引擎加载失败")
    print(f"   错误详情: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ 诊断完成")
print("=" * 60)
