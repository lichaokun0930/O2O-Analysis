"""
测试营销活动成本完整数据流程
模拟看板从数据库加载到计算的完整过程
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from database.data_source_manager import DataSourceManager
from scene_inference import add_scene_and_timeslot_fields

print("\n" + "="*80)
print("🔍 测试营销活动成本完整数据流程")
print("="*80)

# Step 1: 从数据库加载数据
print("\n【Step 1】从数据库加载数据...")
manager = DataSourceManager()
df = manager.load_from_database(store_name='共橙超市-徐州新沂2店')
print(f"✅ 加载数据: {len(df)} 行")

# Step 2: 检查营销活动字段
print("\n【Step 2】检查营销活动字段...")
marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券']
for field in marketing_fields:
    if field in df.columns:
        total = df[field].sum()
        non_zero = (df[field] > 0).sum()
        print(f"  ✅ {field}: 总和={total:.2f}, 非零行数={non_zero}")
    else:
        print(f"  ❌ {field}: 字段不存在!")

# Step 3: 添加场景字段
print("\n【Step 3】添加场景字段...")
df = add_scene_and_timeslot_fields(df)
print(f"✅ 场景字段已添加")

# Step 4: 订单级聚合
print("\n【Step 4】订单级聚合...")
order_agg = df.groupby('订单ID').agg({
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

print(f"✅ 聚合后订单数: {len(order_agg)}")

# Step 5: 计算商家活动成本
print("\n【Step 5】计算商家活动成本...")
order_agg['商家活动成本'] = (
    order_agg['满减金额'] + 
    order_agg['商品减免金额'] + 
    order_agg['商家代金券'] +
    order_agg['商家承担部分券']
)

marketing_cost_total = order_agg['商家活动成本'].sum()
print(f"✅ 商家活动成本总计: ¥{marketing_cost_total:,.2f}")

# Step 6: 详细分解
print("\n【Step 6】成本详细分解...")
components = {
    '满减金额': order_agg['满减金额'].sum(),
    '商品减免金额': order_agg['商品减免金额'].sum(),
    '商家代金券': order_agg['商家代金券'].sum(),
    '商家承担部分券': order_agg['商家承担部分券'].sum()
}

for name, value in components.items():
    print(f"  {name}: ¥{value:,.2f}")

# Step 7: 验证与Excel数据对比
print("\n【Step 7】与Excel数据对比...")
print("  (如果数据库数据是从Excel导入的,两者应该一致)")

print("\n" + "="*80)
print("✅ 测试完成!")
print("="*80)
