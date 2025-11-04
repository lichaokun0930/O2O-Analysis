"""检查诊断结果中的价格字段"""
import pandas as pd
import sys
sys.path.append('.')
from 问题诊断引擎 import ProblemDiagnosticEngine

# 加载数据
excel_file = "实际数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"
df = pd.read_excel(excel_file)
df['日期'] = pd.to_datetime(df['下单时间'])
df = df[df['一级分类名'] != '耗材']
if '渠道' in df.columns:
    coffee_channels = ['饿了么咖啡', '美团咖啡']
    df = df[~df['渠道'].isin(coffee_channels)]

engine = ProblemDiagnosticEngine(df)
result = engine.diagnose_sales_decline(
    threshold=-100,
    time_period='week',
    current_period_index=0,
    compare_period_index=1
)

print(f"诊断结果: {len(result)} 个下滑商品")
print(f"\n诊断结果的列: {list(result.columns)}")

if '商品实售价' in result.columns:
    print(f"\n商品实售价字段:")
    print(f"  数据类型: {result['商品实售价'].dtype}")
    print(f"  前10个值:")
    for i, val in enumerate(result['商品实售价'].head(10)):
        print(f"    [{i}] {val} (type: {type(val).__name__})")
    
    print(f"\n  统计信息:")
    print(f"    NaN数量: {result['商品实售价'].isna().sum()}")
    print(f"    非NaN数量: {result['商品实售价'].notna().sum()}")
    
    # 尝试转换
    numeric_price = pd.to_numeric(result['商品实售价'], errors='coerce')
    print(f"\n  转换为数值后:")
    print(f"    类型: {numeric_price.dtype}")
    print(f"    NaN数量: {numeric_price.isna().sum()}")
    print(f"    有效数值: {numeric_price.notna().sum()}")
    print(f"    最小值: {numeric_price.min()}")
    print(f"    最大值: {numeric_price.max()}")
    print(f"    平均值: {numeric_price.mean():.2f}")
    
    # 检查价格分布
    print(f"\n  价格分布:")
    print(f"    0-10元: {(numeric_price <= 10).sum()}")
    print(f"    10-30元: {((numeric_price > 10) & (numeric_price <= 30)).sum()}")
    print(f"    30-50元: {((numeric_price > 30) & (numeric_price <= 50)).sum()}")
    print(f"    50-100元: {((numeric_price > 50) & (numeric_price <= 100)).sum()}")
    print(f"    >100元: {(numeric_price > 100).sum()}")
    print(f"    NaN: {numeric_price.isna().sum()}")
    
else:
    print("\n❌ 诊断结果中没有'商品实售价'字段！")
    print("可用字段:", list(result.columns))
