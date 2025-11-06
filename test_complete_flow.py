"""
完整数据流程测试
测试从数据库加载数据后,是否能正确计算商家活动成本
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database.data_source_manager import DataSourceManager
import pandas as pd

def test_complete_flow():
    """测试完整流程"""
    print("="*80)
    print("📊 完整数据流程测试")
    print("="*80)
    
    manager = DataSourceManager()
    
    # 1. 从数据库加载数据
    print("\n1️⃣ 从数据库加载数据...")
    df = manager.load_from_database(store_name='共橙超市-徐州新沂2店')
    print(f"   加载数据量: {len(df)} 行")
    
    # 2. 检查基础营销字段
    print("\n2️⃣ 检查基础营销字段...")
    marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券']
    for field in marketing_fields:
        if field in df.columns:
            total = df[field].fillna(0).sum()
            count = (df[field] > 0).sum()
            print(f"   ✅ {field}: 总额=¥{total:,.2f}, 非零记录={count}")
        else:
            print(f"   ❌ {field}: 字段缺失")
    
    # 3. 按订单聚合
    print("\n3️⃣ 按订单聚合...")
    order_agg = df.groupby('订单ID').agg({
        '商品实售价': 'sum',
        '商品采购成本': 'sum',
        '利润额': 'sum',
        '月售': 'sum',
        '用户支付配送费': 'sum',
        '配送费减免金额': 'sum',
        '物流配送费': 'sum',
        '满减金额': 'sum',
        '商品减免金额': 'sum',
        '商家代金券': 'sum',
        '商家承担部分券': 'sum',
        '平台佣金': 'sum',
        '打包袋金额': 'sum'
    }).reset_index()
    
    print(f"   订单数: {len(order_agg)}")
    
    # 4. 计算商家活动成本(模拟运营核心代码逻辑)
    print("\n4️⃣ 计算商家活动成本...")
    order_agg['商家活动成本'] = (
        order_agg['满减金额'] + 
        order_agg['商品减免金额'] + 
        order_agg['商家代金券'] +
        order_agg['商家承担部分券']
    )
    
    marketing_cost = order_agg['商家活动成本'].sum()
    print(f"   商家活动成本总额: ¥{marketing_cost:,.2f}")
    
    # 5. 详细分解
    print("\n5️⃣ 成本详细分解:")
    print(f"   满减金额: ¥{order_agg['满减金额'].sum():,.2f}")
    print(f"   商品减免金额: ¥{order_agg['商品减免金额'].sum():,.2f}")
    print(f"   商家代金券: ¥{order_agg['商家代金券'].sum():,.2f}")
    print(f"   商家承担部分券: ¥{order_agg['商家承担部分券'].sum():,.2f}")
    print(f"   -------------------------")
    print(f"   商家活动成本合计: ¥{marketing_cost:,.2f}")
    
    # 6. 样本数据
    print("\n6️⃣ 样本订单(前5个有活动成本的):")
    sample = order_agg[order_agg['商家活动成本'] > 0].head(5)
    if len(sample) > 0:
        print(sample[['订单ID', '满减金额', '商品减免金额', '商家代金券', '商家承担部分券', '商家活动成本']])
    else:
        print("   ⚠️ 没有找到有活动成本的订单")
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)

if __name__ == "__main__":
    test_complete_flow()
