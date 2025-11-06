"""
测试诊断引擎与真实历史数据
"""
import sys
import os
import glob
import pickle
import gzip
import pandas as pd
from 问题诊断引擎 import ProblemDiagnosticEngine

print("="*70)
print("🔍 测试诊断引擎与真实历史数据")
print("="*70)

# 1. 加载最新历史数据
cache_dir = "学习数据仓库/uploaded_data"
cache_files = glob.glob(os.path.join(cache_dir, "*.pkl.gz"))
latest = max(cache_files, key=os.path.getmtime)

print(f"\n[1] 加载数据: {os.path.basename(latest)}")
with gzip.open(latest, 'rb') as f:
    data_dict = pickle.load(f)

df = data_dict['data']
print(f"    ✅ 加载成功: {len(df):,} 行 × {len(df.columns)} 列")

# 2. 检查字段
print("\n[2] 检查关键字段:")
required = ['日期', '商品名称', '三级分类名']
missing = [f for f in required if f not in df.columns]
if missing:
    print(f"    ❌ 缺少字段: {missing}")
    sys.exit(1)
else:
    print(f"    ✅ 所有必需字段都存在")

# 3. 检查日期范围
print("\n[3] 日期范围分析:")
df['日期'] = pd.to_datetime(df['日期'])
min_date = df['日期'].min()
max_date = df['日期'].max()
days = (max_date - min_date).days

print(f"    最小日期: {min_date}")
print(f"    最大日期: {max_date}")
print(f"    跨度: {days} 天 ({days/7:.1f} 周)")

if days < 14:
    print(f"    ⚠️  警告：跨度不足2周，周度对比可能失败")

# 4. 生成场景和时段（模拟Dash中的逻辑）
print("\n[4] 生成场景和时段字段...")
df['_hour'] = df['日期'].dt.hour

def get_time_slot(hour):
    if pd.isna(hour):
        return '未知时段'
    if 6 <= hour < 9:
        return '清晨(6-9点)'
    elif 9 <= hour < 12:
        return '上午(9-12点)'
    elif 12 <= hour < 14:
        return '正午(12-14点)'
    elif 14 <= hour < 18:
        return '下午(14-18点)'
    elif 18 <= hour < 21:
        return '傍晚(18-21点)'
    elif 21 <= hour < 24:
        return '晚间(21-24点)'
    elif 0 <= hour < 3:
        return '深夜(0-3点)'
    else:
        return '凌晨(3-6点)'

df['时段'] = df['_hour'].apply(get_time_slot)

# 简化的场景推断
def infer_scene(row):
    hour = row.get('_hour', -1)
    if 6 <= hour < 10:
        return '早餐'
    elif 10 <= hour < 14:
        return '日常购物'
    elif 14 <= hour < 17:
        return '下午茶'
    elif 17 <= hour < 21:
        return '晚餐'
    elif 21 <= hour <= 23:
        return '夜间社交'
    else:
        return '居家消费'

df['场景'] = df.apply(infer_scene, axis=1)
print(f"    ✅ 生成完成")
print(f"    场景: {df['场景'].unique().tolist()}")
print(f"    时段: {df['时段'].unique().tolist()}")

# 5. 创建诊断引擎并测试
print("\n[5] 创建诊断引擎...")
engine = ProblemDiagnosticEngine(df)
print(f"    ✅ 诊断引擎已创建")

# 6. 测试周度诊断
print("\n[6] 运行周度诊断...")
print(f"    参数: time_period='week', threshold=-5.0")

try:
    result = engine.diagnose_sales_decline(
        time_period='week',
        threshold=-5.0,
        scene_filter=None,
        time_slot_filter=None,
        current_period_index=0,
        compare_period_index=1
    )
    
    print(f"\n✅ 诊断完成！")
    print(f"   结果行数: {len(result)}")
    
    if result.empty:
        print(f"\n⚠️  诊断结果为空！")
        print(f"\n可能原因分析：")
        print(f"  1. 数据跨度({days}天)不足2周，无法进行周度对比")
        print(f"  2. 所有商品变化幅度都>-5%，没有符合阈值的下滑商品")
        print(f"  3. 数据字段不符合诊断引擎要求")
        
        # 尝试降低阈值
        print(f"\n尝试 threshold=0（显示所有变化）...")
        result2 = engine.diagnose_sales_decline(
            time_period='week',
            threshold=0,
            current_period_index=0,
            compare_period_index=1
        )
        print(f"   threshold=0 结果: {len(result2)} 行")
        
        if result2.empty:
            print(f"   ❌ 即使threshold=0也无结果，数据跨度可能不足")
        else:
            print(f"   ✅ 有{len(result2)}个商品有周度变化")
            if '变化幅度%' in result2.columns:
                print(f"   变化幅度范围: [{result2['变化幅度%'].min():.1f}%, {result2['变化幅度%'].max():.1f}%]")
    else:
        print(f"\n✅ 找到 {len(result)} 个下滑商品")
        print(f"\n字段列表:")
        for i, col in enumerate(result.columns, 1):
            print(f"   {i:2d}. {col}")
        
        # 检查商品名称
        if '商品名称' in result.columns:
            print(f"\n✅ '商品名称' 在列中")
        else:
            print(f"\n❌ '商品名称' 不在列中")
        
        # 显示前5个商品
        print(f"\n前5个下滑商品:")
        display_cols = ['商品名称', '销量变化', '收入变化', '变化幅度%']
        available = [c for c in display_cols if c in result.columns]
        print(result[available].head().to_string(index=False))
        
except Exception as e:
    print(f"\n❌ 诊断失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
