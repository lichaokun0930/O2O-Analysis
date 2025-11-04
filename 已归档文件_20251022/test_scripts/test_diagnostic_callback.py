"""
测试诊断回调逻辑
模拟用户点击"开始诊断"按钮后的完整流程
"""
import pandas as pd
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🧪 开始测试诊断回调逻辑")
print("=" * 80)

# 1. 加载数据
print("\n📂 步骤 1: 加载数据...")
from 真实数据处理器 import RealDataProcessor

processor = RealDataProcessor(data_dir='实际数据')
df = processor.load_and_process_data()

print(f"   ✅ 数据加载完成: {len(df)} 行")
print(f"   📋 字段列表: {df.columns.tolist()[:10]}...")

# 2. 检查关键字段
print("\n🔍 步骤 2: 检查关键字段...")
required_fields = ['商品名称', '日期', '销量', '利润', '预计订单收入']
missing_fields = [f for f in required_fields if f not in df.columns]

if missing_fields:
    print(f"   ❌ 缺失字段: {missing_fields}")
    
    # 尝试字段映射
    print("\n🔧 步骤 2.1: 尝试字段映射...")
    if '月售' in df.columns and '销量' not in df.columns:
        df['销量'] = df['月售']
        print(f"      ✅ 映射: '月售' -> '销量'")
    
    if '利润额' in df.columns and '利润' not in df.columns:
        df['利润'] = df['利润额']
        print(f"      ✅ 映射: '利润额' -> '利润'")
    
    # 重新检查
    missing_fields = [f for f in required_fields if f not in df.columns]
    if missing_fields:
        print(f"   ❌ 映射后仍缺失: {missing_fields}")
    else:
        print(f"   ✅ 所有必需字段已就绪")
else:
    print(f"   ✅ 所有必需字段已存在")

# 3. 检查数据类型和内容
print("\n📊 步骤 3: 检查数据详情...")
print(f"   '销量' 字段:")
print(f"      - 数据类型: {df['销量'].dtype}")
print(f"      - 总和: {df['销量'].sum():,.0f}")
print(f"      - 非零数量: {(df['销量'] > 0).sum()} / {len(df)}")
print(f"      - 示例: {df['销量'].head(3).tolist()}")

print(f"\n   '利润' 字段:")
print(f"      - 数据类型: {df['利润'].dtype}")
print(f"      - 总和: ¥{df['利润'].sum():,.2f}")
print(f"      - 非零数量: {(df['利润'] != 0).sum()} / {len(df)}")
print(f"      - 示例: {df['利润'].head(3).tolist()}")

# 4. 测试周度分组
print("\n📅 步骤 4: 测试周度分组...")
df['日期'] = pd.to_datetime(df['日期'])
df['周'] = df['日期'].dt.isocalendar().week

week_counts = df.groupby('周').size()
print(f"   周分布:")
for week, count in week_counts.items():
    print(f"      Week {week}: {count} 条记录")

# 5. 模拟诊断引擎逻辑
print("\n🔍 步骤 5: 模拟诊断引擎...")
time_period = 'week'
threshold = -20.0

print(f"   配置: 时间周期={time_period}, 阈值={threshold}%")

# 按周和商品聚合
print("\n   5.1 按周和商品聚合...")
weekly_agg = df.groupby(['周', '商品名称']).agg({
    '销量': 'sum',
    '预计订单收入': 'sum',
    '利润': 'sum'
}).reset_index()

print(f"      ✅ 聚合后: {len(weekly_agg)} 条记录")
print(f"      示例数据:")
print(weekly_agg.head(10).to_string())

# 计算周度变化
print("\n   5.2 计算周度销量变化...")
weekly_agg = weekly_agg.sort_values(['商品名称', '周'])
weekly_agg['上周销量'] = weekly_agg.groupby('商品名称')['销量'].shift(1)
weekly_agg['销量变化率'] = ((weekly_agg['销量'] - weekly_agg['上周销量']) / weekly_agg['上周销量'] * 100).round(2)

# 过滤下滑商品
declining = weekly_agg[
    (weekly_agg['销量变化率'] < threshold) & 
    (weekly_agg['上周销量'].notna())
].copy()

print(f"      ✅ 找到 {len(declining)} 条下滑记录")

if len(declining) > 0:
    print(f"      示例下滑商品:")
    print(declining.head(10)[['商品名称', '周', '销量', '上周销量', '销量变化率']].to_string())
    
    # 统计唯一商品数
    unique_products = declining['商品名称'].nunique()
    print(f"\n      📊 唯一下滑商品数: {unique_products}")
else:
    print(f"      ⚠️ 没有找到符合条件的下滑商品")

# 6. 测试完整诊断引擎
print("\n" + "=" * 80)
print("🔬 步骤 6: 使用真实诊断引擎测试...")
print("=" * 80)

from 自适应学习引擎 import ProblemDiagnosticEngine

engine = ProblemDiagnosticEngine(df)
result = engine.diagnose_sales_decline(time_period='week', threshold=-20.0)

print(f"\n✅ 诊断完成!")
print(f"   结果数据量: {len(result)} 行")

if len(result) > 0:
    print(f"\n   前10条结果:")
    display_cols = ['商品名称', '销量变化率', '销量', '预计订单收入', '利润']
    available_cols = [col for col in display_cols if col in result.columns]
    print(result[available_cols].head(10).to_string())
    
    print(f"\n   ✅ 测试成功! 诊断引擎工作正常")
else:
    print(f"\n   ⚠️ 诊断引擎返回空结果")
    print(f"   可能原因:")
    print(f"      1. 阈值 {threshold}% 设置过严格")
    print(f"      2. 数据中确实没有符合条件的下滑商品")
    print(f"      3. 字段映射问题")

print("\n" + "=" * 80)
print("🧪 测试完成")
print("=" * 80)
