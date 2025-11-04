"""测试诊断引擎"""
import pandas as pd
import sys
sys.path.insert(0, r"D:\Python1\O2O_Analysis\O2O数据分析\测算模型")

from 真实数据处理器 import RealDataProcessor
from 问题诊断引擎 import ProblemDiagnosticEngine

# 加载数据
print("📂 加载数据...")
processor = RealDataProcessor()

# 使用最新的缓存数据
import gzip
import pickle
cache_file = r"学习数据仓库\uploaded_data\2025-09-01 00_00_00至2025-09-30 01_08_49订单明细数据导出汇总 (1)_ef875e4d_20251020_111132.pkl.gz"

with gzip.open(cache_file, 'rb') as f:
    cached = pickle.load(f)
    df = cached['data']

print(f"✅ 数据加载完成: {len(df)} 行")

# 标准化
df = processor.standardize_sales_data(df)
print(f"✅ 标准化完成: {len(df)} 行")
print(f"📋 字段: {list(df.columns)[:20]}")

# 检查场景和时段字段
if '场景' in df.columns:
    print(f"✅ 场景字段存在，唯一值: {df['场景'].unique().tolist()}")
else:
    print("❌ 缺少场景字段")

if '时段' in df.columns:
    print(f"✅ 时段字段存在，唯一值: {df['时段'].unique().tolist()}")
else:
    print("❌ 缺少时段字段")

# 初始化诊断引擎
print("\n🔧 初始化诊断引擎...")
engine = ProblemDiagnosticEngine(df)

# 运行诊断
print("\n🔍 开始诊断（周度对比）...")
try:
    result = engine.diagnose_sales_decline(
        time_period='week',
        threshold=-5.0,
        scene_filter=None,
        time_slot_filter=None,
        current_period_index=0,
        compare_period_index=1
    )
    
    print(f"\n📊 诊断结果:")
    print(f"   - 数据行数: {len(result)}")
    print(f"   - 字段数量: {len(result.columns)}")
    print(f"   - 字段列表:")
    for i, col in enumerate(result.columns, 1):
        print(f"     {i:2d}. {col}")
    
    # 检查关键字段
    print(f"\n🔍 关键字段检查:")
    for field in ['商品名称', '场景', '时段', '销量变化', '收入变化', '利润变化']:
        exists = field in result.columns
        print(f"   - '{field}': {'✅' if exists else '❌'}")
        if exists and len(result) > 0:
            print(f"      样本: {result[field].head(3).tolist()}")

except Exception as e:
    print(f"❌ 诊断失败: {e}")
    import traceback
    traceback.print_exc()
