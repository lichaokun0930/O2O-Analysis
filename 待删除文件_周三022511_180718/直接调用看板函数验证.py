"""
快速验证: 直接调用看板的calculate_order_metrics函数
模拟看板处理祥和路数据的完整流程
"""
import pandas as pd
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入看板的核心函数
from 智能门店看板_Dash版 import calculate_order_metrics

print("="*80)
print("直接调用看板核心函数验证")
print("="*80)

# 读取Excel
excel_file = Path(__file__).parent / '实际数据' / '祥和路.xlsx'
df = pd.read_excel(excel_file)

print(f"\n1. Excel原始数据:")
print(f"   - 总行数: {len(df):,}行")
print(f"   - 利润额总和: ¥{df['利润额'].sum():,.2f}")

# 剔除耗材(模拟看板逻辑)
df_display = df[df['一级分类名'] != '耗材'].copy()

print(f"\n2. 剔除耗材后:")
print(f"   - 总行数: {len(df_display):,}行")
print(f"   - 利润额总和: ¥{df_display['利润额'].sum():,.2f}")

# 调用看板的calculate_order_metrics函数
print(f"\n3. 调用看板calculate_order_metrics函数...")
print(f"   (会打印看板内部的调试信息)")
print("-"*80)

order_metrics = calculate_order_metrics(df_display)

print("-"*80)
print(f"\n4. 函数返回结果:")
print(f"   - 订单数: {len(order_metrics):,}个")
if '订单实际利润' in order_metrics.columns:
    print(f"   - 订单实际利润总和: ¥{order_metrics['订单实际利润'].sum():,.2f}")
    
    # 分渠道
    if '渠道' in order_metrics.columns:
        print(f"\n5. 分渠道统计:")
        channel_stats = order_metrics.groupby('渠道')['订单实际利润'].sum()
        for channel, profit in channel_stats.items():
            print(f"   - {channel}: ¥{profit:,.2f}")
else:
    print(f"   ⚠️ 返回数据中没有'订单实际利润'字段")
    print(f"   可用字段: {order_metrics.columns.tolist()}")

print(f"\n" + "="*80)
print(f"验证结论:")
print(f"="*80)

if '订单实际利润' in order_metrics.columns:
    system_total = order_metrics['订单实际利润'].sum()
    user_total = 23332.00
    diff = system_total - user_total
    
    print(f"看板核心函数计算: ¥{system_total:,.2f}")
    print(f"用户手动计算: ¥{user_total:,.2f}")
    print(f"差异: ¥{diff:,.2f} ({diff/user_total*100:.2f}%)")
    
    if abs(diff) < 100:
        print(f"\n✅ 看板计算正确!差异在合理范围内!")
    elif abs(diff) < 500:
        print(f"\n✅ 看板计算基本正确,差异可能来自企客后返或四舍五入")
    else:
        print(f"\n⚠️ 差异较大,需要对比用户的剔除条件")
else:
    print(f"❌ 函数返回数据异常,请检查calculate_order_metrics")
