#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景营销智能决策引擎 - 测试脚本
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("🧪 场景营销智能决策引擎 - 测试")
print("=" * 80)

# 测试导入
print("\n1️⃣ 测试模块导入...")
try:
    from 场景营销智能决策引擎 import (
        SceneMarketingIntelligence,
        ProductCombinationMiner,
        SceneRecognitionModel,
        RFMCustomerSegmentation,
        SceneDecisionTreeRules
    )
    print("✅ 所有模块导入成功！")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 生成测试数据
print("\n2️⃣ 生成测试订单数据...")
np.random.seed(42)

n_orders = 500
n_products = 20

# 商品库
products = [
    '可口可乐', '薯片', '矿泉水', '巧克力', '坚果', 
    '咖啡', '饼干', '牛奶', '酸奶', '果汁',
    '啤酒', '瓜子', '花生', '辣条', '面包',
    '纸巾', '垃圾袋', '洗洁精', '电池', '牙膏'
]

# 生成订单数据
orders = []
order_id = 1

for i in range(n_orders):
    # 随机日期
    days_ago = np.random.randint(0, 30)
    order_date = datetime.now() - timedelta(days=days_ago)
    
    # 随机时间
    hour = np.random.choice([9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23])
    
    # 随机购买1-5个商品
    n_items = np.random.randint(1, 6)
    selected_products = np.random.choice(products, n_items, replace=False)
    
    for product in selected_products:
        # 随机价格
        price = np.random.uniform(5, 50)
        
        # 随机配送距离
        distance = np.random.uniform(0.5, 5.0)
        
        # 配送费
        if distance < 1:
            delivery_fee = 0
        elif distance < 3:
            delivery_fee = 3
        else:
            delivery_fee = 5
        
        orders.append({
            '订单ID': f'ORD{order_id:06d}',
            '商品名称': product,
            '商品实售价': price,
            '配送距离': distance,
            '物流配送费': delivery_fee,
            '日期_datetime': order_date,
            '小时': hour,
            '三级分类名': '休闲食品' if product in ['可口可乐', '薯片', '巧克力', '坚果'] else '日用百货'
        })
    
    order_id += 1

test_df = pd.DataFrame(orders)
print(f"✅ 生成 {len(test_df)} 条订单明细，{test_df['订单ID'].nunique()} 个订单")
print(f"   商品种类: {test_df['商品名称'].nunique()}")
print(f"   时间跨度: {test_df['日期_datetime'].min()} ~ {test_df['日期_datetime'].max()}")

# 测试完整引擎
print("\n3️⃣ 运行完整智能分析...")
engine = SceneMarketingIntelligence()

try:
    results = engine.run_full_analysis(test_df)
    
    print("\n" + "=" * 80)
    print(engine.get_summary_report())
    print("=" * 80)
    
    print("\n✅ 所有测试通过！")
    print("\n💡 提示：可以在Streamlit看板中查看完整的可视化分析")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
