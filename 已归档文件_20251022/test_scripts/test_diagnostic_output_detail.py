"""测试诊断引擎输出的详细字段信息"""
import pandas as pd
from pathlib import Path

# 加载数据
data_file = Path("门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx")
if not data_file.exists():
    print(f"❌ 文件不存在: {data_file}")
    exit(1)

print(f"📂 加载数据: {data_file.name}")
df = pd.read_excel(data_file)
print(f"✅ 数据加载: {len(df)} 行")

# 标准化
from 真实数据处理器 import RealDataProcessor
processor = RealDataProcessor()
df = processor.standardize_sales_data(df)
print(f"✅ 标准化完成: {len(df)} 行")

# 初始化诊断引擎
from 问题诊断引擎 import ProblemDiagnosticEngine
engine = ProblemDiagnosticEngine(df)

# 运行诊断
print(f"\n🔍 开始诊断...")
result = engine.diagnose_sales_decline(
    compare_period='week',
    threshold=-5.0
)

if result is not None:
    print(f"\n📊 诊断结果:")
    print(f"   - 数据行数: {len(result)}")
    print(f"   - 数据列数: {len(result.columns)}")
    print(f"\n📋 所有字段列表:")
    for i, col in enumerate(result.columns, 1):
        print(f"   {i:2d}. {col}")
    
    # 检查销量字段
    sales_cols = [col for col in result.columns if '销量' in col]
    print(f"\n💡 销量相关字段: {sales_cols}")
    
    # 检查前3行数据
    print(f"\n🔍 前3行数据样本:")
    print(result.head(3).to_string())
    
    # 检查数据类型
    print(f"\n📝 数据类型:")
    for col in sales_cols:
        print(f"   - {col}: {result[col].dtype}")
        print(f"     样本值: {result[col].head(3).tolist()}")
else:
    print("❌ 诊断失败")
