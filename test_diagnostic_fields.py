"""测试诊断引擎输出字段"""
import sys
import pandas as pd

# 防止导入智能看板启动服务器
sys.modules['智能门店看板_Dash版'] = None

from 订单数据处理器 import 订单数据处理器
from 问题诊断引擎 import 问题诊断引擎

# 初始化数据处理器
processor = 订单数据处理器("实际数据")

# 加载数据
file_path = "门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx"
print(f"📂 加载数据: {file_path}")
df = processor.load_data(file_path)
print(f"✅ 数据加载完成: {len(df)} 行")

# 标准化数据
df = processor.standardize_sales_data(df)
print(f"✅ 数据标准化完成: {len(df)} 行")

# 初始化诊断引擎
engine = 问题诊断引擎(df)
print(f"✅ 诊断引擎初始化完成")

# 运行诊断
print(f"\n🔍 开始诊断...")
result = engine.diagnose_sales_decline(
    compare_period='day',
    threshold=-5.0,
    scene_filter=None,
    time_slot_filter=None
)

if result is not None:
    print(f"\n📊 诊断结果:")
    print(f"   - 数据行数: {len(result)}")
    print(f"   - 字段列表:")
    for col in result.columns:
        print(f"     • {col}")
    
    # 检查关键字段
    print(f"\n🔍 关键字段检查:")
    print(f"   - '商品名称' 存在: {'商品名称' in result.columns}")
    print(f"   - '收入变化' 存在: {'收入变化' in result.columns}")
    print(f"   - '利润变化' 存在: {'利润变化' in result.columns}")
    
    if '收入变化' in result.columns:
        print(f"\n💰 收入变化字段信息:")
        print(f"   - 数据类型: {result['收入变化'].dtype}")
        print(f"   - 样本值:")
        print(result[['商品名称', '收入变化']].head())
else:
    print("❌ 诊断失败，没有返回结果")
