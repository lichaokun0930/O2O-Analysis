"""
测试上周同期功能
验证calculate_week_on_week_comparison函数是否正常工作
"""
import sys
sys.path.insert(0, '.')

from database.data_source_manager import DataSourceManager
from datetime import datetime, timedelta
import pandas as pd

print("=" * 60)
print("测试上周同期功能")
print("=" * 60)

# 加载数据
print("\n1. 加载数据库数据...")
manager = DataSourceManager()
data_dict = manager.load_from_database()
df = data_dict['full']  # 使用完整数据（含耗材）
print(f"   ✓ 已加载 {len(df)} 条数据")

# 确保有日期字段
if '日期' not in df.columns and '下单时间' in df.columns:
    df['日期'] = df['下单时间']

df['日期'] = pd.to_datetime(df['日期'])

# 获取数据的日期范围
print(f"\n2. 数据日期范围:")
print(f"   最早: {df['日期'].min().date()}")
print(f"   最晚: {df['日期'].max().date()}")

# 检查是否有上周同期数据（7天前）
latest_date = df['日期'].max()
one_week_ago = latest_date - timedelta(days=7)
last_week_data_count = len(df[df['日期'] <= one_week_ago])

print(f"\n3. 上周同期数据检查:")
print(f"   当前最新日期: {latest_date.date()}")
print(f"   上周同期日期: {one_week_ago.date()}")
print(f"   上周及之前的数据: {last_week_data_count} 条")

if last_week_data_count > 0:
    print(f"   ✓ 有上周同期数据，可以计算对比")
    
    # 导入上周同期计算函数
    print(f"\n4. 测试上周同期计算...")
    from 智能门店看板_Dash版 import calculate_week_on_week_comparison
    
    # 使用最近3天与上周同期对比
    end_date = df['日期'].max()
    start_date = end_date - timedelta(days=2)  # 最近3天
    
    print(f"   本周期: {start_date.date()} ~ {end_date.date()}")
    print(f"   上周同期(7天前): {(start_date - timedelta(days=7)).date()} ~ {(end_date - timedelta(days=7)).date()}")
    
    wow_data = calculate_week_on_week_comparison(df, start_date, end_date)
    
    if wow_data:
        print(f"\n5. 上周同期计算结果:")
        print(f"=" * 60)
        
        for metric_name, metric_data in wow_data.items():
            current = metric_data.get('current', 0)
            previous = metric_data.get('previous', 0)
            change_rate = metric_data.get('change_rate', 0)
            
            icon = "📈" if change_rate > 0 else "📉"
            
            print(f"\n{icon} {metric_name}:")
            print(f"   本周期: {current:,.2f}")
            print(f"   上周同期(7天前): {previous:,.2f}")
            print(f"   变化: {change_rate:+.1f}%")
        
        print(f"\n" + "=" * 60)
        print(f"✓ 上周同期功能测试成功！")
    else:
        print(f"\n   ⚠️ 上周同期计算返回空结果")
else:
    print(f"   ⚠️ 没有上周同期数据，无法计算对比")
    print(f"   建议: 导入更多历史数据（至少需要7天以上的数据）")

print(f"\n" + "=" * 60)
print(f"测试完成")
print(f"=" * 60)
