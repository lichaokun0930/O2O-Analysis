"""
快速诊断测试 - 验证诊断引擎是否能返回数据
"""
from 问题诊断引擎 import ProblemDiagnosticEngine
import pandas as pd

# 加载数据
print("🔄 正在加载数据...")
df = pd.read_excel("门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx")
print(f"✅ 数据加载成功: {len(df)} 行")

# 检查关键字段
print("\n📋 字段检查:")
required_fields = ['日期', '商品名称', '三级分类名']
for field in required_fields:
    exists = field in df.columns
    print(f"  - {field}: {'✅' if exists else '❌ 缺失'}")

# 检查日期范围
if '日期' in df.columns:
    print(f"\n📅 日期范围:")
    print(f"  - 最小日期: {df['日期'].min()}")
    print(f"  - 最大日期: {df['日期'].max()}")
    print(f"  - 日期类型: {df['日期'].dtype}")

# 初始化诊断引擎
print("\n🔧 正在初始化诊断引擎...")
engine = ProblemDiagnosticEngine(df)
print("✅ 初始化完成！")

# 测试不同阈值
print("\n" + "="*60)
print("测试1: threshold=0 (显示所有变化)")
print("="*60)
result1 = engine.diagnose_sales_decline(time_period='week', threshold=0)
print(f"结果行数: {len(result1)}")
if not result1.empty:
    print(f"字段数: {len(result1.columns)}")
    print(f"字段列表: {list(result1.columns)[:10]}")
    if '销量变化' in result1.columns:
        print(f"销量变化范围: [{result1['销量变化'].min():.2f}, {result1['销量变化'].max():.2f}]")
    print(f"\n前5条数据:")
    display_cols = ['商品名称', '场景', '销量变化', '收入变化'] if all(c in result1.columns for c in ['商品名称', '场景', '销量变化', '收入变化']) else result1.columns[:4]
    print(result1[display_cols].head())
else:
    print("❌ 返回空数据！")

print("\n" + "="*60)
print("测试2: threshold=-5 (下滑幅度>5%)")
print("="*60)
result2 = engine.diagnose_sales_decline(time_period='week', threshold=-5)
print(f"结果行数: {len(result2)}")

print("\n" + "="*60)
print("测试3: threshold=-10 (下滑幅度>10%)")
print("="*60)
result3 = engine.diagnose_sales_decline(time_period='week', threshold=-10)
print(f"结果行数: {len(result3)}")

print("\n" + "="*60)
print("测试4: 不使用任何筛选")
print("="*60)
result4 = engine.diagnose_sales_decline(
    time_period='week', 
    threshold=0,
    scene_filter=None,
    time_slot_filter=None
)
print(f"结果行数: {len(result4)}")
if not result4.empty:
    print(f"\n数据类型检查:")
    print(result4.dtypes)

print("\n" + "="*60)
print("📊 总结")
print("="*60)
print(f"threshold=0:   {len(result1)} 条")
print(f"threshold=-5:  {len(result2)} 条")
print(f"threshold=-10: {len(result3)} 条")
print(f"无筛选:        {len(result4)} 条")

if len(result1) == 0 and len(result4) == 0:
    print("\n⚠️ 警告：所有测试都返回空数据！")
    print("可能原因：")
    print("1. 诊断引擎内部逻辑问题")
    print("2. 数据时间范围不符合周期计算")
    print("3. 数据字段缺失")
