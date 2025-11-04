"""测试诊断回调逻辑"""
import pandas as pd
import sys
sys.path.append('.')
from 问题诊断引擎 import ProblemDiagnosticEngine

# 加载数据
excel_file = "实际数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"
df = pd.read_excel(excel_file)

# 标准化字段
df['日期'] = pd.to_datetime(df['下单时间'])

# 过滤
df = df[df['一级分类名'] != '耗材']
if '渠道' in df.columns:
    coffee_channels = ['饿了么咖啡', '美团咖啡']
    df = df[~df['渠道'].isin(coffee_channels)]

print(f"过滤后数据: {len(df)} 行")

# 初始化引擎
engine = ProblemDiagnosticEngine(df)

# 模拟回调参数
time_period = 'week'
current_idx = 0
compare_idx = 1
category_filter = None
price_range = [0, 100]
decline_range = [-100, 0]

print(f"\n{'='*80}")
print(f"🔍 开始诊断...")
print(f"   时间粒度: {time_period}")
print(f"   当前周期: {current_idx}, 对比周期: {compare_idx}")

# 执行诊断
result = engine.diagnose_sales_decline(
    threshold=-100,
    time_period=time_period,
    current_period_index=current_idx if current_idx is not None else 0,
    compare_period_index=compare_idx if compare_idx is not None else 1
)

print(f"✅ 诊断完成，初始结果: {len(result)} 个下滑商品")
if len(result) > 0:
    print(f"   变化幅度%类型: {result['变化幅度%'].dtype}")
    print(f"   前3个值: {list(result['变化幅度%'].head(3))}")

# 应用高级筛选
if not result.empty:
    # 分类筛选
    if category_filter and '一级分类名' in result.columns:
        before_count = len(result)
        result = result[result['一级分类名'].isin(category_filter)]
        print(f"   分类筛选: {before_count} -> {len(result)} 个商品")
    
    # 价格筛选
    if price_range and '商品实售价' in result.columns:
        before_count = len(result)
        # 转换为数值类型，先去除¥符号
        result['商品实售价'] = pd.to_numeric(
            result['商品实售价'].astype(str).str.replace('¥', '').str.replace('￥', ''),
            errors='coerce'
        )
        result = result[
            (result['商品实售价'] >= price_range[0]) &
            (result['商品实售价'] <= price_range[1])
        ]
        print(f"   价格筛选 [{price_range[0]}-{price_range[1]}]: {before_count} -> {len(result)} 个商品")
    
    # 下滑幅度筛选
    if decline_range and '变化幅度%' in result.columns:
        before_count = len(result)
        print(f"   下滑幅度筛选前: {before_count} 个商品")
        print(f"   筛选范围: {decline_range}")
        
        # 转换字符串百分比为数值
        result['变化幅度%_numeric'] = pd.to_numeric(
            result['变化幅度%'].astype(str).str.replace('%', ''),
            errors='coerce'
        )
        print(f"   转换后类型: {result['变化幅度%_numeric'].dtype}")
        print(f"   转换后前3个值: {list(result['变化幅度%_numeric'].head(3))}")
        print(f"   转换后最小值: {result['变化幅度%_numeric'].min()}")
        print(f"   转换后最大值: {result['变化幅度%_numeric'].max()}")
        
        result = result[
            (result['变化幅度%_numeric'] >= decline_range[0]) &
            (result['变化幅度%_numeric'] <= decline_range[1])
        ]
        print(f"   下滑幅度筛选后: {len(result)} 个商品")
        
        result = result.drop('变化幅度%_numeric', axis=1)

print(f"📊 最终结果: {len(result)} 个下滑商品")
print(f"{'='*80}\n")

if len(result) > 0:
    print("前10个下滑商品:")
    print(result[['商品名称', '变化幅度%', '商品实售价']].head(10))
