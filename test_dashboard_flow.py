"""
模拟看板完整流程测试
从数据库加载 -> 聚合计算 -> 显示结果
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.data_source_manager import DataSourceManager
import pandas as pd

def test_dashboard_flow():
    """模拟看板完整流程"""
    print("="*80)
    print("🎯 模拟看板完整流程测试")
    print("="*80)
    
    manager = DataSourceManager()
    
    # ========== 步骤1: 从数据库加载数据（模拟load_from_database回调）==========
    print("\n【步骤1】从数据库加载数据...")
    GLOBAL_DATA = manager.load_from_database(store_name='共橙超市-徐州新沂2店')
    print(f"✅ 加载数据量: {len(GLOBAL_DATA)} 行")
    
    # ========== 步骤2: 检查关键字段 ==========
    print("\n【步骤2】检查关键字段...")
    key_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', 
                  '物流配送费', '平台佣金', '商品采购成本', '利润额']
    
    for field in key_fields:
        if field in GLOBAL_DATA.columns:
            total = GLOBAL_DATA[field].fillna(0).sum()
            print(f"   ✅ {field}: ¥{total:,.2f}")
        else:
            print(f"   ❌ {field}: 缺失")
    
    # ========== 步骤3: 订单级聚合（模拟show_tab1_detail_analysis）==========
    print("\n【步骤3】订单级聚合...")
    order_agg = GLOBAL_DATA.groupby('订单ID').agg({
        '商品实售价': 'sum',
        '商品采购成本': 'sum',
        '利润额': 'sum',
        '月售': 'sum',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '物流配送费': 'first',
        '满减金额': 'first',
        '商品减免金额': 'first',
        '商家代金券': 'first',
        '商家承担部分券': 'first',
        '平台佣金': 'first',
        '打包袋金额': 'first'
    }).reset_index()
    
    print(f"   订单数: {len(order_agg)}")
    
    # ========== 步骤4: 计算商家活动成本 ==========
    print("\n【步骤4】计算商家活动成本...")
    order_agg['商家活动成本'] = (
        order_agg['满减金额'] + 
        order_agg['商品减免金额'] + 
        order_agg['商家代金券'] +
        order_agg['商家承担部分券']
    )
    
    marketing_cost = order_agg['商家活动成本'].sum()
    print(f"   商家活动成本: ¥{marketing_cost:,.2f}")
    
    # ========== 步骤5: 成本结构分析（模拟Tab1显示）==========
    print("\n【步骤5】成本结构分析...")
    product_cost = order_agg['商品采购成本'].sum()
    delivery_cost = order_agg['物流配送费'].sum()
    commission = order_agg['平台佣金'].sum()
    
    print(f"\n📦 商品成本: ¥{product_cost:,.2f}")
    print(f"🚚 物流配送费: ¥{delivery_cost:,.2f}")
    print(f"🎁 商家活动: ¥{marketing_cost:,.2f}")
    print(f"   ├─ 满减金额: ¥{order_agg['满减金额'].sum():,.2f}")
    print(f"   ├─ 商品减免金额: ¥{order_agg['商品减免金额'].sum():,.2f}")
    print(f"   ├─ 商家代金券: ¥{order_agg['商家代金券'].sum():,.2f}")
    print(f"   └─ 商家承担部分券: ¥{order_agg['商家承担部分券'].sum():,.2f}")
    print(f"💳 平台佣金: ¥{commission:,.2f}")
    
    total_cost = product_cost + delivery_cost + marketing_cost + commission
    print(f"\n💰 总成本: ¥{total_cost:,.2f}")
    
    # ========== 步骤6: 验证 ==========
    print("\n【步骤6】验证...")
    if marketing_cost > 0:
        print(f"   ✅ 商家活动成本正常: ¥{marketing_cost:,.2f}")
    else:
        print(f"   ❌ 商家活动成本为0!")
        
        # 检查原始数据
        print(f"\n   🔍 原始数据检查:")
        for field in ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券']:
            count = (GLOBAL_DATA[field] > 0).sum()
            total = GLOBAL_DATA[field].sum()
            print(f"      {field}: {count}条记录, 总额=¥{total:,.2f}")
        
        # 检查聚合后数据
        print(f"\n   🔍 聚合后数据检查:")
        for field in ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券']:
            count = (order_agg[field] > 0).sum()
            total = order_agg[field].sum()
            print(f"      {field}: {count}条记录, 总额=¥{total:,.2f}")
    
    print("\n" + "="*80)
    print("✅ 流程测试完成")
    print("="*80)

if __name__ == "__main__":
    test_dashboard_flow()
