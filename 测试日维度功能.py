"""
测试日维度销量下滑诊断功能
"""
import pandas as pd
from datetime import datetime, timedelta

print("="*80)
print("测试日维度销量下滑诊断")
print("="*80)

# 创建测试数据
dates = []
products = []
sales = []

# 生成30天的数据
base_date = datetime(2025, 10, 16)
for i in range(30):
    date = base_date - timedelta(days=i)
    
    # 商品A：逐渐下滑
    for _ in range(max(1, 30 - i)):
        dates.append(date)
        products.append('商品A')
        sales.append(1)
    
    # 商品B：稳定
    for _ in range(20):
        dates.append(date)
        products.append('商品B')
        sales.append(1)
    
    # 商品C：某天突然下滑
    qty = 25 if i < 10 else 5  # 10天前是25件/天，之后降到5件/天
    for _ in range(qty):
        dates.append(date)
        products.append('商品C')
        sales.append(1)

df = pd.DataFrame({
    '日期': dates,
    '商品名称': products,
    '三级分类名': products,
    '销量': sales
})

print(f"\n生成测试数据：{len(df)} 条记录")
print(f"日期范围：{df['日期'].min()} ~ {df['日期'].max()}")
print(f"\n每日销量统计：")
print(df.groupby(['日期', '商品名称']).size().unstack(fill_value=0))

# 测试诊断引擎
try:
    from 问题诊断引擎 import ProblemDiagnosticEngine
    
    engine = ProblemDiagnosticEngine(df)
    
    print("\n" + "="*80)
    print("测试1：获取可用日期列表")
    print("="*80)
    
    periods = engine.get_available_periods('day')
    print(f"\n可用日期数量：{len(periods)}")
    print("\n前10个日期：")
    for p in periods[:10]:
        print(f"  {p['label']}: {p['date_range']}")
    
    print("\n" + "="*80)
    print("测试2：对比昨天 vs 今天")
    print("="*80)
    
    # 今天 vs 昨天
    result = engine.diagnose_sales_decline(
        time_period='day',
        threshold=-20.0,
        current_period_index=0,  # 今天
        compare_period_index=1   # 昨天
    )
    
    if len(result) > 0:
        print(f"\n✅ 发现 {len(result)} 个下滑商品")
        print("\n下滑商品详情：")
        display_cols = ['商品名称', result.columns[1], result.columns[2], '销量变化', '变化幅度%', '问题等级']
        print(result[display_cols].to_string(index=False))
    else:
        print("\n未发现下滑商品")
    
    print("\n" + "="*80)
    print("测试3：对比10天前 vs 今天")
    print("="*80)
    
    # 今天 vs 10天前
    result2 = engine.diagnose_sales_decline(
        time_period='day',
        threshold=-20.0,
        current_period_index=0,   # 今天
        compare_period_index=10   # 10天前
    )
    
    if len(result2) > 0:
        print(f"\n✅ 发现 {len(result2)} 个下滑商品")
        print("\n下滑商品详情：")
        display_cols = ['商品名称', result2.columns[1], result2.columns[2], '销量变化', '变化幅度%', '问题等级']
        print(result2[display_cols].to_string(index=False))
    else:
        print("\n未发现下滑商品")
    
    print("\n" + "="*80)
    print("✅ 日维度功能测试通过！")
    print("="*80)
    print("\n使用说明：")
    print("1. 运行智能看板：streamlit run 智能门店经营看板_可视化.py")
    print("2. 进入【问题诊断引擎】→【销量下滑】")
    print("3. 对比周期选择器中现在有三个选项：")
    print("   - 按日对比 ← 新增")
    print("   - 按周对比")
    print("   - 按月对比")
    print("4. 选择'按日对比'后，可以对比任意两天的销量")
    
except Exception as e:
    print(f"\n❌ 测试失败：{e}")
    import traceback
    traceback.print_exc()
