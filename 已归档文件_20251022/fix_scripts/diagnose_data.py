"""诊断数据和引擎问题"""
import pandas as pd
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

# 防止导入时启动应用
import os
os.environ['SKIP_APP_RUN'] = '1'

from 问题诊断引擎 import ProblemDiagnosticEngine
from 订单数据处理器 import OrderDataProcessor

print("="*80)
print("🔍 诊断分析：为什么诊断引擎返回空数据")
print("="*80)

# 加载数据
data_file = Path("门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx")

if not data_file.exists():
    print(f"❌ 数据文件不存在: {data_file}")
    sys.exit(1)

print(f"\n1️⃣ 加载数据文件: {data_file.name}")
df = pd.read_excel(data_file)
print(f"   ✅ 原始数据: {len(df)} 行 × {len(df.columns)} 列")
print(f"   📋 字段: {list(df.columns)[:10]}...")

# 标准化数据
print(f"\n2️⃣ 标准化数据...")
processor = OrderDataProcessor("实际数据")
df = processor.standardize_sales_data(df)
print(f"   ✅ 标准化完成: {len(df)} 行")
print(f"   📋 标准化后字段: {list(df.columns)[:15]}...")

# 检查关键字段
print(f"\n3️⃣ 检查关键字段:")
required_fields = ['商品名称', '日期', '月售']
for field in required_fields:
    exists = field in df.columns
    print(f"   {'✅' if exists else '❌'} {field}: {exists}")
    if exists:
        print(f"      - 非空数量: {df[field].notna().sum()}/{len(df)}")
        if field == '日期':
            print(f"      - 日期范围: {df[field].min()} 至 {df[field].max()}")
            print(f"      - 日期跨度: {(df[field].max() - df[field].min()).days} 天")

# 初始化诊断引擎
print(f"\n4️⃣ 初始化诊断引擎...")
engine = ProblemDiagnosticEngine(df)
print(f"   ✅ 引擎初始化完成")
print(f"   📊 引擎数据量: {len(engine.df)} 行")

# 测试周度诊断（最简单的参数）
print(f"\n5️⃣ 测试周度诊断（阈值=-20%）...")
try:
    result = engine.diagnose_sales_decline(
        time_period='week',
        threshold=-20.0,
        scene_filter=None,
        time_slot_filter=None,
        current_period_index=0,
        compare_period_index=1
    )
    
    print(f"   📊 诊断结果: {len(result)} 行")
    
    if len(result) == 0:
        print(f"   ⚠️ 返回空数据！")
        print(f"\n   🔍 可能原因分析:")
        
        # 检查周度数据分布
        if '日期' in df.columns:
            df['周'] = df['日期'].dt.isocalendar().week
            weekly_counts = df.groupby('周').size()
            print(f"   - 周度数据分布:")
            for week, count in weekly_counts.head(10).items():
                print(f"     第{week}周: {count} 条记录")
            
            unique_weeks = df['周'].nunique()
            print(f"   - 总共有 {unique_weeks} 个不同的周")
            
            if unique_weeks < 2:
                print(f"   ❌ 问题：数据只有 {unique_weeks} 周，无法进行周度对比！")
            else:
                print(f"   ✅ 有足够的周数进行对比")
                
                # 检查是否有下滑商品
                print(f"\n   🔍 手动计算周度对比:")
                # 获取最近两周
                weeks = sorted(df['周'].unique(), reverse=True)
                if len(weeks) >= 2:
                    week0 = weeks[0]
                    week1 = weeks[1]
                    print(f"   - 当前周: 第{week0}周")
                    print(f"   - 对比周: 第{week1}周")
                    
                    week0_data = df[df['周'] == week0]
                    week1_data = df[df['周'] == week1]
                    
                    print(f"   - 第{week0}周数据: {len(week0_data)} 行")
                    print(f"   - 第{week1}周数据: {len(week1_data)} 行")
                    
                    # 按商品统计销量
                    week0_sales = week0_data.groupby('商品名称')['月售'].sum()
                    week1_sales = week1_data.groupby('商品名称')['月售'].sum()
                    
                    print(f"   - 第{week0}周商品数: {len(week0_sales)}")
                    print(f"   - 第{week1}周商品数: {len(week1_sales)}")
                    
                    # 计算变化
                    comparison = pd.DataFrame({
                        '当前销量': week0_sales,
                        '对比销量': week1_sales
                    }).fillna(0)
                    
                    comparison['变化'] = comparison['当前销量'] - comparison['对比销量']
                    comparison['变化幅度%'] = (comparison['变化'] / comparison['对比销量'].replace(0, 1) * 100).round(2)
                    
                    declined = comparison[comparison['变化幅度%'] <= -20].sort_values('变化幅度%')
                    
                    print(f"\n   📉 变化幅度 ≤ -20% 的商品: {len(declined)} 个")
                    if len(declined) > 0:
                        print(f"   前5个下滑商品:")
                        for i, (name, row) in enumerate(declined.head(5).iterrows(), 1):
                            print(f"      {i}. {name}: {row['变化幅度%']:.1f}%")
                    else:
                        print(f"   ⚠️ 没有符合条件的下滑商品")
                        print(f"   提示：尝试降低阈值（如-5%）或检查数据质量")
    else:
        print(f"   ✅ 返回 {len(result)} 个下滑商品")
        print(f"   📋 结果字段: {list(result.columns)[:10]}...")
        if '变化幅度%' in result.columns:
            print(f"   📉 变化幅度范围: {result['变化幅度%'].min():.1f}% 至 {result['变化幅度%'].max():.1f}%")
        
except Exception as e:
    print(f"   ❌ 诊断失败: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print(f"诊断完成")
print(f"{'='*80}")
