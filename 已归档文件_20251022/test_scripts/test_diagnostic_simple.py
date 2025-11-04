"""
简化版诊断测试 - 直接读取主应用的 GLOBAL_DATA
"""
import sys
import os
import io

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("测试开始: 简化版诊断测试")
print("=" * 80)

# 1. 导入主应用模块
print("\n[步骤 1] 导入主应用...")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入需要的函数
exec(open('智能门店看板_Dash版.py', encoding='utf-8').read().split('app.layout =')[0])

print("   => 导入完成")

# 2. 加载数据
print("\n[步骤 2] 加载数据...")
df = load_real_business_data()
print(f"   => 数据加载: {len(df)} 行")
print(f"   => 字段: {df.columns.tolist()[:15]}")

# 3. 检查关键字段
print("\n[步骤 3] 检查关键字段...")
print(f"   '月售' 在数据中: {'月售' in df.columns}")
print(f"   '销量' 在数据中: {'销量' in df.columns}")
print(f"   '利润额' 在数据中: {'利润额' in df.columns}")
print(f"   '利润' 在数据中: {'利润' in df.columns}")

# 4. 执行字段映射（模拟回调中的逻辑）
print("\n[步骤 4] 执行字段映射...")
if '月售' in df.columns and '销量' not in df.columns:
    df['销量'] = df['月售']
    print("   => 映射: '月售' -> '销量'")
else:
    print(f"   => 不需要映射销量字段 (月售存在:{'月售' in df.columns}, 销量存在:{'销量' in df.columns})")

if '利润额' in df.columns and '利润' not in df.columns:
    df['利润'] = df['利润额']
    print("   => 映射: '利润额' -> '利润'")
else:
    print(f"   => 不需要映射利润字段 (利润额存在:{'利润额' in df.columns}, 利润存在:{'利润' in df.columns})")

# 5. 使用诊断引擎
print("\n[步骤 5] 初始化诊断引擎...")
from 自适应学习引擎 import ProblemDiagnosticEngine

engine = ProblemDiagnosticEngine(df)
print("   => 引擎初始化完成")

# 6. 执行诊断
print("\n[步骤 6] 执行诊断...")
print("   配置: 时间周期=week, 阈值=-20%")

result = engine.diagnose_sales_decline(time_period='week', threshold=-20.0)

print(f"\n[步骤 7] 诊断结果...")
print(f"   结果行数: {len(result)}")

if len(result) > 0:
    print(f"   => 成功找到下滑商品!")
    print(f"\n   前10条结果:")
    display_cols = ['商品名称', '销量变化率', '销量', '预计订单收入', '利润']
    available_cols = [col for col in display_cols if col in result.columns]
    print(result[available_cols].head(10).to_string())
    
    # 统计信息
    print(f"\n   统计信息:")
    print(f"      - 唯一商品数: {result['商品名称'].nunique()}")
    print(f"      - 平均下滑率: {result['销量变化率'].mean():.2f}%")
    print(f"      - 最大下滑率: {result['销量变化率'].min():.2f}%")
else:
    print(f"   => 诊断引擎返回空结果")
    print(f"   请检查:")
    print(f"      1. 数据中是否有多个周的数据")
    print(f"      2. 字段映射是否正确")
    print(f"      3. 阈值设置是否合理")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
