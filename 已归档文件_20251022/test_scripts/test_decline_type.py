"""测试变化幅度%字段的数据类型"""
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

# 执行诊断
result = engine.diagnose_sales_decline(
    threshold=-100,
    time_period='week',
    current_period_index=0,
    compare_period_index=1
)

print(f"\n诊断结果: {len(result)} 个下滑商品")

if len(result) > 0:
    # 检查变化幅度%的数据类型
    print(f"\n变化幅度%字段类型: {result['变化幅度%'].dtype}")
    print(f"前5个值:")
    for i, val in enumerate(result['变化幅度%'].head(5)):
        print(f"  [{i}] {val} (type: {type(val).__name__})")
    
    # 测试数值比较
    print(f"\n测试数值比较:")
    decline_range = [-100, 0]
    print(f"decline_range = {decline_range}")
    
    # 尝试筛选
    try:
        filtered = result[
            (result['变化幅度%'] >= decline_range[0]) &
            (result['变化幅度%'] <= decline_range[1])
        ]
        print(f"✅ 筛选成功! 结果: {len(filtered)} 个商品")
    except Exception as e:
        print(f"❌ 筛选失败: {e}")
    
    # 如果是字符串，尝试转换
    if result['变化幅度%'].dtype == 'object':
        print(f"\n⚠️  检测到变化幅度%是对象类型，尝试转换为数值:")
        try:
            result['变化幅度%_numeric'] = pd.to_numeric(
                result['变化幅度%'].astype(str).str.replace('%', ''), 
                errors='coerce'
            )
            print(f"转换后类型: {result['变化幅度%_numeric'].dtype}")
            print(f"前5个值: {list(result['变化幅度%_numeric'].head())}")
            
            # 再次测试筛选
            filtered2 = result[
                (result['变化幅度%_numeric'] >= decline_range[0]) &
                (result['变化幅度%_numeric'] <= decline_range[1])
            ]
            print(f"✅ 转换后筛选成功! 结果: {len(filtered2)} 个商品")
        except Exception as e:
            print(f"❌ 转换失败: {e}")

else:
    print("❌ 没有找到下滑商品")
