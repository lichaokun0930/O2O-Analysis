import pandas as pd
from 问题诊断引擎 import ProblemDiagnosticEngine

# 加载数据
df = pd.read_excel('实际数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx')
print(f'原始数据: {len(df)} 行')

# 标准化
df['日期'] = pd.to_datetime(df['下单时间'])
df = df[df['一级分类名'] != '耗材']
print(f'过滤后: {len(df)} 行')

# 创建诊断引擎
engine = ProblemDiagnosticEngine(df)

# 执行诊断
print('\n测试诊断引擎...')
result = engine.diagnose_sales_decline(
    threshold=-100,
    time_period='week',
    current_period_index=0,
    compare_period_index=1
)

print(f'\n诊断结果: {len(result)} 个下滑商品')

if not result.empty:
    print('\n前20个下滑商品:')
    print(result[['商品名称', '变化幅度%']].head(20))
    print(f'\n变化幅度范围: {result["变化幅度%"].min():.2f}% ~ {result["变化幅度%"].max():.2f}%')
else:
    print('\n未发现下滑商品')
    print('原因：第1周和第2周的商品销量可能都在上涨或持平')
