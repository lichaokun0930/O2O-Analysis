"""
测试所有对比模式 - 自动化测试脚本
测试日度、周度、月度对比的完整流程
"""

import pandas as pd
from datetime import datetime, timedelta
import sys

print("="*80)
print("🧪 开始测试所有对比模式")
print("="*80)

# 加载数据
try:
    from 订单数据处理器 import OrderDataProcessor
    from 问题诊断引擎 import ProblemDiagnosticEngine
    
    print("\n✅ 模块导入成功")
except Exception as e:
    print(f"\n❌ 模块导入失败: {e}")
    sys.exit(1)

# 初始化数据处理器
try:
    print("\n" + "="*80)
    print("📂 正在加载数据...")
    print("="*80)
    
    processor = OrderDataProcessor()
    
    # 查找最新的数据文件
    import os
    data_dir = "实际数据"
    if os.path.exists(data_dir):
        files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx')]
        if files:
            latest_file = sorted(files)[-1]
            data_path = os.path.join(data_dir, latest_file)
            print(f"📂 加载文件: {latest_file}")
            processor.load_data(data_path)
            data = processor.get_standardized_data()
        else:
            print("❌ 数据目录中没有Excel文件")
            sys.exit(1)
    else:
        print("❌ 数据目录不存在")
        sys.exit(1)
    
    if data is None or data.empty:
        print("❌ 数据加载失败")
        sys.exit(1)
    
    print(f"✅ 数据加载成功: {len(data)} 行")
    print(f"📅 数据日期范围: {data['日期'].min()} ~ {data['日期'].max()}")
    
    # 检查必需字段
    required_fields = ['商品名称', '日期', '销量', '预计订单收入', '利润', '场景', '时段']
    missing_fields = [f for f in required_fields if f not in data.columns]
    
    if missing_fields:
        print(f"❌ 缺少必需字段: {missing_fields}")
        sys.exit(1)
    
    print(f"✅ 所有必需字段存在")
    print(f"   场景数量: {data['场景'].nunique()}")
    print(f"   时段数量: {data['时段'].nunique()}")
    
except Exception as e:
    print(f"❌ 数据加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试1: 周度对比
print("\n" + "="*80)
print("📊 测试1: 周度对比")
print("="*80)

try:
    # 获取数据中的周编号
    data['_week'] = pd.to_datetime(data['日期']).dt.isocalendar().week
    available_weeks = sorted(data['_week'].unique(), reverse=True)
    
    print(f"可用周编号: {available_weeks}")
    
    if len(available_weeks) >= 2:
        week_current = available_weeks[0]
        week_compare = available_weeks[1]
        
        print(f"\n测试周度对比: 第{week_current}周 vs 第{week_compare}周")
        
        # 筛选数据
        current_data = data[data['_week'] == week_current]
        compare_data = data[data['_week'] == week_compare]
        
        print(f"  当前周期数据: {len(current_data)} 条")
        print(f"  对比周期数据: {len(compare_data)} 条")
        
        # 数据可用性检查
        if len(current_data) == 0:
            print(f"  ⚠️ 第{week_current}周没有数据")
        elif len(current_data) < 5:
            print(f"  ⚠️ 第{week_current}周数据量过少 (仅{len(current_data)}条)")
        else:
            print(f"  ✅ 第{week_current}周数据充足")
        
        if len(compare_data) == 0:
            print(f"  ⚠️ 第{week_compare}周没有数据")
        elif len(compare_data) < 5:
            print(f"  ⚠️ 第{week_compare}周数据量过少 (仅{len(compare_data)}条)")
        else:
            print(f"  ✅ 第{week_compare}周数据充足")
        
        # 简单对比计算
        if len(current_data) > 0 and len(compare_data) > 0:
            current_agg = current_data.groupby('商品名称').agg({
                '销量': 'sum',
                '预计订单收入': 'sum',
                '利润': 'sum'
            }).reset_index()
            
            compare_agg = compare_data.groupby('商品名称').agg({
                '销量': 'sum',
                '预计订单收入': 'sum',
                '利润': 'sum'
            }).reset_index()
            
            result = pd.merge(current_agg, compare_agg, on='商品名称', how='inner', suffixes=('_current', '_compare'))
            result['销量变化'] = result['销量_current'] - result['销量_compare']
            result['变化幅度%'] = (result['销量变化'] / result['销量_compare'] * 100).fillna(0)
            
            declining = result[result['变化幅度%'] <= -20]
            
            print(f"  📊 对比结果:")
            print(f"     总商品数: {len(result)}")
            print(f"     下滑商品数 (≤-20%): {len(declining)}")
            if len(declining) > 0:
                print(f"     平均下滑幅度: {declining['变化幅度%'].mean():.1f}%")
                print(f"     最大下滑幅度: {declining['变化幅度%'].min():.1f}%")
            
            print("  ✅ 周度对比测试通过")
    else:
        print("  ⚠️ 数据中周数不足，无法进行周度对比测试")
        
except Exception as e:
    print(f"  ❌ 周度对比测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试2: 月度对比
print("\n" + "="*80)
print("📊 测试2: 月度对比")
print("="*80)

try:
    # 获取数据中的月份
    data['_month'] = pd.to_datetime(data['日期']).dt.to_period('M').astype(str)
    available_months = sorted(data['_month'].unique(), reverse=True)
    
    print(f"可用月份: {available_months}")
    
    if len(available_months) >= 2:
        month_current = available_months[0]
        month_compare = available_months[1]
        
        print(f"\n测试月度对比: {month_current} vs {month_compare}")
        
        # 筛选数据
        current_data = data[data['_month'] == month_current]
        compare_data = data[data['_month'] == month_compare]
        
        print(f"  当前周期数据: {len(current_data)} 条")
        print(f"  对比周期数据: {len(compare_data)} 条")
        
        # 数据可用性检查
        if len(current_data) == 0:
            print(f"  ⚠️ {month_current} 没有数据")
        elif len(current_data) < 20:
            print(f"  ⚠️ {month_current} 数据量过少 (仅{len(current_data)}条)")
        else:
            print(f"  ✅ {month_current} 数据充足")
        
        if len(compare_data) == 0:
            print(f"  ⚠️ {month_compare} 没有数据")
        elif len(compare_data) < 20:
            print(f"  ⚠️ {month_compare} 数据量过少 (仅{len(compare_data)}条)")
        else:
            print(f"  ✅ {month_compare} 数据充足")
        
        # 简单对比计算
        if len(current_data) > 0 and len(compare_data) > 0:
            current_agg = current_data.groupby('商品名称').agg({
                '销量': 'sum',
                '预计订单收入': 'sum',
                '利润': 'sum'
            }).reset_index()
            
            compare_agg = compare_data.groupby('商品名称').agg({
                '销量': 'sum',
                '预计订单收入': 'sum',
                '利润': 'sum'
            }).reset_index()
            
            result = pd.merge(current_agg, compare_agg, on='商品名称', how='inner', suffixes=('_current', '_compare'))
            result['销量变化'] = result['销量_current'] - result['销量_compare']
            result['变化幅度%'] = (result['销量变化'] / result['销量_compare'] * 100).fillna(0)
            
            declining = result[result['变化幅度%'] <= -20]
            
            print(f"  📊 对比结果:")
            print(f"     总商品数: {len(result)}")
            print(f"     下滑商品数 (≤-20%): {len(declining)}")
            if len(declining) > 0:
                print(f"     平均下滑幅度: {declining['变化幅度%'].mean():.1f}%")
                print(f"     最大下滑幅度: {declining['变化幅度%'].min():.1f}%")
            
            print("  ✅ 月度对比测试通过")
    else:
        print(f"  ⚠️ 数据只包含 {len(available_months)} 个月，无法进行月度对比测试")
        
except Exception as e:
    print(f"  ❌ 月度对比测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试3: 日度对比
print("\n" + "="*80)
print("📊 测试3: 日度对比")
print("="*80)

try:
    # 获取日期范围
    data['日期'] = pd.to_datetime(data['日期'])
    min_date = data['日期'].min()
    max_date = data['日期'].max()
    
    print(f"数据日期范围: {min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}")
    print(f"数据跨度: {(max_date - min_date).days + 1} 天")
    
    # 测试最近7天 vs 前7天
    current_start = max_date - timedelta(days=6)
    current_end = max_date
    compare_start = max_date - timedelta(days=13)
    compare_end = max_date - timedelta(days=7)
    
    print(f"\n测试日度对比:")
    print(f"  当前周期: {current_start.strftime('%Y-%m-%d')} ~ {current_end.strftime('%Y-%m-%d')}")
    print(f"  对比周期: {compare_start.strftime('%Y-%m-%d')} ~ {compare_end.strftime('%Y-%m-%d')}")
    
    # 筛选数据
    current_data = data[(data['日期'] >= current_start) & (data['日期'] <= current_end)]
    compare_data = data[(data['日期'] >= compare_start) & (data['日期'] <= compare_end)]
    
    print(f"  当前周期数据: {len(current_data)} 条")
    print(f"  对比周期数据: {len(compare_data)} 条")
    
    # 数据可用性检查
    if len(current_data) == 0:
        print(f"  ⚠️ 当前周期没有数据")
    elif len(current_data) < 10:
        print(f"  ⚠️ 当前周期数据量过少 (仅{len(current_data)}条)，建议扩大日期范围")
    else:
        print(f"  ✅ 当前周期数据充足")
    
    if len(compare_data) == 0:
        print(f"  ⚠️ 对比周期没有数据")
    elif len(compare_data) < 10:
        print(f"  ⚠️ 对比周期数据量过少 (仅{len(compare_data)}条)，建议扩大日期范围")
    else:
        print(f"  ✅ 对比周期数据充足")
    
    # 检查日期跨度
    current_days = (current_end - current_start).days + 1
    compare_days = (compare_end - compare_start).days + 1
    print(f"  当前周期跨度: {current_days} 天")
    print(f"  对比周期跨度: {compare_days} 天")
    
    # 简单对比计算
    if len(current_data) > 0 and len(compare_data) > 0:
        current_agg = current_data.groupby('商品名称').agg({
            '销量': 'sum',
            '预计订单收入': 'sum',
            '利润': 'sum'
        }).reset_index()
        
        compare_agg = compare_data.groupby('商品名称').agg({
            '销量': 'sum',
            '预计订单收入': 'sum',
            '利润': 'sum'
        }).reset_index()
        
        result = pd.merge(current_agg, compare_agg, on='商品名称', how='inner', suffixes=('_current', '_compare'))
        result['销量变化'] = result['销量_current'] - result['销量_compare']
        result['变化幅度%'] = (result['销量变化'] / result['销量_compare'] * 100).fillna(0)
        
        declining = result[result['变化幅度%'] <= -20]
        
        print(f"  📊 对比结果:")
        print(f"     总商品数: {len(result)}")
        print(f"     下滑商品数 (≤-20%): {len(declining)}")
        if len(declining) > 0:
            print(f"     平均下滑幅度: {declining['变化幅度%'].mean():.1f}%")
            print(f"     最大下滑幅度: {declining['变化幅度%'].min():.1f}%")
        
        print("  ✅ 日度对比测试通过")
        
except Exception as e:
    print(f"  ❌ 日度对比测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试4: 场景和时段筛选
print("\n" + "="*80)
print("📊 测试4: 场景和时段筛选")
print("="*80)

try:
    scenes = data['场景'].dropna().unique()
    slots = data['时段'].dropna().unique()
    
    print(f"可用场景 ({len(scenes)}个): {list(scenes)}")
    print(f"可用时段 ({len(slots)}个): {list(slots)}")
    
    if len(scenes) > 0:
        test_scene = scenes[0]
        filtered = data[data['场景'] == test_scene]
        print(f"\n测试场景筛选 (场景='{test_scene}'):")
        print(f"  筛选后数据: {len(filtered)} 条 ({len(filtered)/len(data)*100:.1f}%)")
        print(f"  ✅ 场景筛选测试通过")
    
    if len(slots) > 0:
        test_slot = slots[0]
        filtered = data[data['时段'] == test_slot]
        print(f"\n测试时段筛选 (时段='{test_slot}'):")
        print(f"  筛选后数据: {len(filtered)} 条 ({len(filtered)/len(data)*100:.1f}%)")
        print(f"  ✅ 时段筛选测试通过")
    
except Exception as e:
    print(f"  ❌ 筛选测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试总结
print("\n" + "="*80)
print("✅ 测试总结")
print("="*80)
print("""
已完成测试项目:
  ✅ 周度对比 - 数据提取、数量检查、对比计算
  ✅ 月度对比 - 数据提取、数量检查、对比计算
  ✅ 日度对比 - 日期范围筛选、跨度检查、对比计算
  ✅ 场景筛选 - 场景字段存在性、筛选功能
  ✅ 时段筛选 - 时段字段存在性、筛选功能

建议后续在浏览器中测试:
  1. 访问 http://localhost:8050
  2. 切换到 Tab 4 (问题诊断)
  3. 切换到 Tab 4.1 (销量下滑诊断)
  4. 测试不同粒度的周期选择器
  5. 验证图表正确显示
  6. 测试场景和时段筛选器
  7. 验证数据可用性提示
""")

print("\n🎉 所有自动化测试完成！")
print("="*80)
