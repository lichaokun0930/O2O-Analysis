# -*- coding: utf-8 -*-
"""测试 Tab 4 诊断功能"""

import io
import pandas as pd
import sys
from pathlib import Path

# 解决 Windows 编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from 问题诊断引擎 import ProblemDiagnosticEngine
from 真实数据处理器 import RealDataProcessor

print("="*80)
print("测试 Tab 4 诊断功能")
print("="*80)

# 1. 加载数据
print("\n📂 步骤1: 加载数据...")
data_file = APP_DIR / "实际数据" / "2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"

if not data_file.exists():
    print(f"❌ 数据文件不存在: {data_file}")
    sys.exit(1)

# 读取Excel文件
raw_df = pd.read_excel(data_file)
print(f"📊 原始数据: {len(raw_df)} 行 × {len(raw_df.columns)} 列")

# 标准化数据
processor = RealDataProcessor("实际数据")
df = processor.standardize_sales_data(raw_df)

print(f"✅ 数据加载成功: {len(df)} 行")
print(f"📋 字段: {df.columns.tolist()[:10]}...")

# 2. 剔除耗材和咖啡
print("\n📂 步骤2: 剔除耗材和咖啡...")
before = len(df)
df = df[df['一级分类名'] != '耗材']
print(f"   🔴 剔除耗材: {before - len(df)} 行")

before = len(df)
df = df[~df['渠道'].isin(['饿了么咖啡', '美团咖啡'])]
print(f"   ☕ 剔除咖啡: {before - len(df)} 行")
print(f"✅ 最终数据: {len(df)} 行")

# 3. 检查必要字段
print("\n步骤3: 检查必要字段...")
required_fields = ['商品名称', '预计订单收入', '日期']
missing_fields = [f for f in required_fields if f not in df.columns]

if missing_fields:
    print(f"缺少字段: {missing_fields}")
    print(f"当前字段: {df.columns.tolist()}")
    sys.exit(1)

# 字段映射
if '月售' in df.columns:
    df['销量'] = df['月售']
    print("   将'月售'映射为'销量'")
else:
    print("   警告: 没有找到'月售'或'销量'字段")
    sys.exit(1)

if '利润额' in df.columns:
    df['利润'] = df['利润额']
    print("   将'利润额'映射为'利润'")
elif '利润' not in df.columns:
    print("   警告: 没有找到'利润额'或'利润'字段")
    sys.exit(1)

print("所有必要字段都存在")

# 4. 检查周数据
print("\n📂 步骤4: 检查周数据分布...")
df['日期'] = pd.to_datetime(df['日期'])
df['week'] = df['日期'].dt.isocalendar().week

week_counts = df.groupby('week').size().sort_index()
print(f"📊 数据覆盖的周:")
for week, count in week_counts.items():
    print(f"   第{week}周: {count} 条记录")

if len(week_counts) < 2:
    print("⚠️ 警告: 数据少于2周，无法进行周度对比！")
else:
    print(f"✅ 数据覆盖 {len(week_counts)} 周，可以进行周度对比")

# 5. 测试诊断引擎
print("\n📂 步骤5: 初始化诊断引擎...")
engine = ProblemDiagnosticEngine(df)
print("✅ 诊断引擎初始化完成")

# 6. 执行诊断 - 周度对比，阈值 -20%
print("\n📂 步骤6: 执行诊断（周度对比，阈值-20%）...")
try:
    result = engine.diagnose_sales_decline(
        time_period='week',
        threshold=-20.0,
        scene_filter=None,
        time_slot_filter=None,
        current_period_index=0,
        compare_period_index=1
    )
    
    print(f"✅ 诊断完成")
    print(f"📊 结果: {len(result)} 个下滑商品")
    
    if len(result) == 0:
        print("\n⚠️ 未找到符合条件的下滑商品")
        print("   可能原因:")
        print("   1. 阈值 -20% 太严格")
        print("   2. 数据时间跨度不足")
        print("   3. 商品周环比变化都在 -20% 以上")
        
        # 尝试降低阈值
        print("\n🔄 尝试降低阈值到 -5%...")
        result = engine.diagnose_sales_decline(
            time_period='week',
            threshold=-5.0,
            scene_filter=None,
            time_slot_filter=None,
            current_period_index=0,
            compare_period_index=1
        )
        print(f"📊 结果: {len(result)} 个下滑商品")
        
    if len(result) > 0:
        print(f"\n📋 结果字段: {result.columns.tolist()}")
        print("\n📊 前5个下滑商品:")
        print(result.head().to_string())
    
except Exception as e:
    print(f"❌ 诊断失败: {e}")
    import traceback
    traceback.print_exc()

# 7. 手动计算周环比（验证）
print("\n📂 步骤7: 手动计算周环比（验证）...")
weeks = sorted(df['week'].unique())
if len(weeks) >= 2:
    current_week = weeks[-1]  # 最近一周
    compare_week = weeks[-2]  # 前一周
    
    print(f"   当前周: 第{current_week}周")
    print(f"   对比周: 第{compare_week}周")
    
    current_data = df[df['week'] == current_week]
    compare_data = df[df['week'] == compare_week]
    
    print(f"   当前周数据: {len(current_data)} 条")
    print(f"   对比周数据: {len(compare_data)} 条")
    
    # 按商品汇总
    current_agg = current_data.groupby('商品名称')['销量'].sum()
    compare_agg = compare_data.groupby('商品名称')['销量'].sum()
    
    # 合并
    comparison = pd.DataFrame({
        '当前周销量': current_agg,
        '对比周销量': compare_agg
    }).dropna()
    
    comparison['变化量'] = comparison['当前周销量'] - comparison['对比周销量']
    comparison['变化幅度%'] = (comparison['变化量'] / comparison['对比周销量'] * 100).fillna(0)
    
    # 筛选下滑商品
    declined = comparison[comparison['变化幅度%'] <= -20].sort_values('变化幅度%')
    
    print(f"\n📊 手动计算结果: {len(declined)} 个下滑商品（阈值-20%）")
    
    if len(declined) > 0:
        print("\n前5个:")
        print(declined.head().to_string())
    else:
        print("\n⚠️ 没有商品下滑超过20%")
        
        # 显示变化幅度分布
        print("\n📊 变化幅度分布:")
        print(f"   最大下滑: {comparison['变化幅度%'].min():.2f}%")
        print(f"   最大上涨: {comparison['变化幅度%'].max():.2f}%")
        print(f"   平均变化: {comparison['变化幅度%'].mean():.2f}%")
        print(f"   中位数: {comparison['变化幅度%'].median():.2f}%")
        
        # 显示下滑商品数量（不同阈值）
        for threshold in [-5, -10, -15, -20]:
            count = len(comparison[comparison['变化幅度%'] <= threshold])
            print(f"   阈值{threshold}%: {count} 个商品")

print("\n" + "="*80)
print("✅ 测试完成")
print("="*80)
