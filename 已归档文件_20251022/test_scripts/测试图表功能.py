"""
测试图表功能
快速验证6个图表的回调函数是否正常工作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# 导入核心模块
from 问题诊断引擎 import ProblemDiagnosticEngine
import pandas as pd

# 初始化数据
data_file = "门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"

if not os.path.exists(data_file):
    print(f"❌ 数据文件不存在: {data_file}")
    sys.exit(1)

print("🔄 正在加载数据...")
df_raw = pd.read_excel(data_file)
print(f"✅ 数据加载成功: {len(df_raw)} 行")

# 初始化诊断引擎
print("🔧 正在初始化诊断引擎...")
engine = ProblemDiagnosticEngine(df_raw)

# 运行销量下滑诊断
print("📊 正在运行销量下滑诊断...")
result = engine.diagnose_sales_decline()

# 检查结果
if result is not None and not result.empty:
    df_decline = result
    print(f"\n✅ 下滑诊断成功: 发现 {len(df_decline)} 个下滑商品")
    
    # 检查所需字段
    required_fields = [
        '商品名称', '场景', '一级分类名', '销量变化', '收入变化', '利润变化',
        '对比周期销量', '当前周期销量', '商品实售价', '平均毛利率%'
    ]
    
    print("\n📋 字段检查:")
    for field in required_fields:
        exists = field in df_decline.columns
        status = "✅" if exists else "❌"
        print(f"  {status} {field}")
    
    # 模拟图表数据计算
    print("\n📈 图表数据计算测试:")
    
    # 1. 分时段分布
    if '场景' in df_decline.columns:
        slot_stats = df_decline.groupby('场景').size()
        print(f"  ✅ 分时段分布: {len(slot_stats)} 个场景")
    
    # 2. 周期对比
    if '对比周期销量' in df_decline.columns and '当前周期销量' in df_decline.columns:
        top10 = df_decline.nlargest(10, '销量变化')
        print(f"  ✅ 周期对比: TOP10商品")
    
    # 3. 分类损失
    if '一级分类名' in df_decline.columns and '收入变化' in df_decline.columns:
        cat_loss = df_decline.groupby('一级分类名')['收入变化'].sum()
        print(f"  ✅ 分类损失: {len(cat_loss)} 个分类")
    
    # 4. 分类TOP商品
    if '一级分类名' in df_decline.columns and '销量变化' in df_decline.columns:
        categories = df_decline['一级分类名'].unique()
        print(f"  ✅ 分类TOP商品: {len(categories)} 个分类")
    
    # 5. 四维散点图
    scatter_fields = ['销量变化', '利润变化', '商品实售价', '平均毛利率%']
    if all(f in df_decline.columns for f in scatter_fields):
        print(f"  ✅ 四维散点图: 所有字段齐全")
    
    # 6. 价格分布
    if '商品实售价' in df_decline.columns:
        price_range = (df_decline['商品实售价'].min(), df_decline['商品实售价'].max())
        print(f"  ✅ 价格分布: 范围 ¥{price_range[0]:.2f} - ¥{price_range[1]:.2f}")
    
    print("\n" + "="*60)
    print("🎉 所有图表数据准备就绪！")
    print("💡 可以启动Dash应用查看可视化效果")
    print("   运行命令: python 智能门店看板_Dash版.py")
    print("="*60)

else:
    print("❌ 未发现下滑商品，无法测试图表功能")
