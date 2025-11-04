"""测试默认数据的诊断"""
import pandas as pd
import sys
import io

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, r"D:\Python1\O2O_Analysis\O2O数据分析\测算模型")

from 真实数据处理器 import RealDataProcessor  
from 问题诊断引擎 import ProblemDiagnosticEngine
from pathlib import Path

# 加载默认数据
print("[INFO] 加载默认数据...")
data_file = Path("门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx")

df = pd.read_excel(data_file)
print(f"✅ 数据加载完成: {len(df)} 行")

# 标准化
processor = RealDataProcessor()
df = processor.standardize_sales_data(df)
print(f"✅ 标准化完成: {len(df)} 行")

# 剔除耗材和咖啡
df = df[df['一级分类名'] != '耗材'].copy()
df = df[~df['渠道'].isin(['饿了么咖啡', '美团咖啡'])].copy()
print(f"✅ 剔除后: {len(df)} 行")

# 检查场景和时段字段
print(f"\n📋 字段检查:")
print(f"   - 场景字段: {'✅' if '场景' in df.columns else '❌'}")
print(f"   - 时段字段: {'✅' if '时段' in df.columns else '❌'}")
print(f"   - 商品名称: {'✅' if '商品名称' in df.columns else '❌'}")

# 初始化诊断引擎
print("\n🔧 初始化诊断引擎...")
engine = ProblemDiagnosticEngine(df)

# 运行诊断
print("\n🔍 开始诊断（周度对比，阈值-5%）...")
try:
    result = engine.diagnose_sales_decline(
        time_period='week',
        threshold=-5.0,
        scene_filter=None,
        time_slot_filter=None,
        current_period_index=0,
        compare_period_index=1
    )
    
    if result is None or result.empty:
        print("❌ 诊断引擎返回空结果！")
    else:
        print(f"\n📊 诊断成功！")
        print(f"   - 下滑商品数: {len(result)}")
        print(f"   - 字段数量: {len(result.columns)}")
        print(f"\n   - 前10个字段:")
        for i, col in enumerate(list(result.columns)[:10], 1):
            print(f"     {i:2d}. {col}")
        
        # 检查关键字段
        print(f"\n🔍 关键字段检查:")
        for field in ['商品名称', '场景', '时段', '销量变化', '收入变化']:
            exists = field in result.columns
            status = '✅' if exists else '❌'
            print(f"   {status} '{field}'", end='')
            if exists and len(result) > 0:
                sample = result[field].head(2).tolist()
                print(f"  样本: {sample}")
            else:
                print()
        
        # 显示前3行数据
        print(f"\n📄 前3行数据:")
        print(result[['商品名称', '销量变化', '变化幅度%']].head(3) if '商品名称' in result.columns else result.head(3))

except Exception as e:
    print(f"\n❌ 诊断失败: {e}")
    import traceback
    traceback.print_exc()
