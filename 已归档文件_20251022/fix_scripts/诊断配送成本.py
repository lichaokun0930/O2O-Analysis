"""诊断配送成本计算问题"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from standard_business_config import StandardBusinessLogic, apply_standard_business_logic

# 加载数据
data_file = "测算模型/实际数据/W36-W37订单数据.xlsx"
print(f"📂 加载数据: {data_file}")
df = pd.read_excel(data_file)
print(f"   ✓ 数据行数: {len(df)}")

# 检查必需列
required_cols = ['配送费减免金额', '物流配送费', '用户支付配送费', '订单ID']
missing = [col for col in required_cols if col not in df.columns]
if missing:
    print(f"❌ 缺少必需列: {missing}")
    print(f"   可用列: {df.columns.tolist()}")
    sys.exit(1)

print("\n" + "="*80)
print("📊 配送成本相关字段统计")
print("="*80)

# 统计配送相关字段
print("\n1️⃣ 配送费减免金额:")
print(f"   总计: ¥{df['配送费减免金额'].sum():,.2f}")
print(f"   均值: ¥{df['配送费减免金额'].mean():.2f}")
print(f"   非零行数: {(df['配送费减免金额'] != 0).sum()}")

print("\n2️⃣ 物流配送费:")
print(f"   总计: ¥{df['物流配送费'].sum():,.2f}")
print(f"   均值: ¥{df['物流配送费'].mean():.2f}")
print(f"   非零行数: {(df['物流配送费'] != 0).sum()}")

print("\n3️⃣ 用户支付配送费:")
print(f"   总计: ¥{df['用户支付配送费'].sum():,.2f}")
print(f"   均值: ¥{df['用户支付配送费'].mean():.2f}")
print(f"   非零行数: {(df['用户支付配送费'] != 0).sum()}")

# 按订单聚合计算配送成本
print("\n" + "="*80)
print("📊 按订单聚合后的配送成本")
print("="*80)

# 订单级别聚合
order_agg = df.groupby('订单ID').agg({
    '配送费减免金额': 'first',
    '物流配送费': 'first', 
    '用户支付配送费': 'first',
    '商品实售价': 'sum',
    '打包费': 'first'
}).reset_index()

print(f"\n订单数: {len(order_agg)}")

# 手动计算两种配送成本
order_agg['配送成本_新公式'] = order_agg['配送费减免金额'] + order_agg['物流配送费']
order_agg['配送成本_旧公式'] = order_agg['用户支付配送费'] - order_agg['配送费减免金额'] - order_agg['物流配送费']

print("\n🔹 新公式（正确）: 配送成本 = 配送费减免 + 物流配送费")
print(f"   总配送成本: ¥{order_agg['配送成本_新公式'].sum():,.2f}")
print(f"   平均配送成本: ¥{order_agg['配送成本_新公式'].mean():.2f}")

print("\n🔹 旧公式（错误）: 配送成本 = 用户支付 - 配送费减免 - 物流配送费")
print(f"   总配送成本: ¥{order_agg['配送成本_旧公式'].sum():,.2f}")
print(f"   平均配送成本: ¥{order_agg['配送成本_旧公式'].mean():.2f}")

# 使用标准业务逻辑计算
print("\n" + "="*80)
print("📊 使用 StandardBusinessLogic 计算配送成本")
print("="*80)

order_agg['配送成本'] = order_agg.apply(StandardBusinessLogic.calculate_delivery_cost, axis=1)

print(f"\n标准业务逻辑计算结果:")
print(f"   总配送成本: ¥{order_agg['配送成本'].sum():,.2f}")
print(f"   平均配送成本: ¥{order_agg['配送成本'].mean():.2f}")

# 比较
print("\n" + "="*80)
print("📊 三种计算方式对比")
print("="*80)

comparison = pd.DataFrame({
    '计算方式': ['新公式（正确）', '旧公式（错误）', 'StandardBusinessLogic'],
    '总配送成本': [
        order_agg['配送成本_新公式'].sum(),
        order_agg['配送成本_旧公式'].sum(),
        order_agg['配送成本'].sum()
    ]
})

print(comparison.to_string(index=False))

# 检查是否一致
if abs(order_agg['配送成本'].sum() - order_agg['配送成本_新公式'].sum()) < 0.01:
    print("\n✅ StandardBusinessLogic 使用的是新公式（正确）")
else:
    print("\n❌ StandardBusinessLogic 计算结果与新公式不一致")

# 计算利润影响
print("\n" + "="*80)
print("📊 配送成本对利润的影响")
print("="*80)

# 计算订单总收入
order_agg['订单总收入'] = order_agg['商品实售价'] + order_agg['打包费'] + order_agg['用户支付配送费']

# 假设其他成本
print("\n假设其他成本为0，仅看配送成本对利润的影响:")
print(f"\n订单总收入: ¥{order_agg['订单总收入'].sum():,.2f}")
print(f"\n使用新公式配送成本，利润 = {order_agg['订单总收入'].sum():,.2f} - {order_agg['配送成本_新公式'].sum():,.2f} = ¥{order_agg['订单总收入'].sum() - order_agg['配送成本_新公式'].sum():,.2f}")
print(f"使用旧公式配送成本，利润 = {order_agg['订单总收入'].sum():,.2f} - {order_agg['配送成本_旧公式'].sum():,.2f} = ¥{order_agg['订单总收入'].sum() - order_agg['配送成本_旧公式'].sum():,.2f}")

profit_diff = (order_agg['订单总收入'].sum() - order_agg['配送成本_旧公式'].sum()) - (order_agg['订单总收入'].sum() - order_agg['配送成本_新公式'].sum())
print(f"\n❌ 旧公式导致利润虚高: ¥{profit_diff:,.2f}")

print("\n" + "="*80)
print("✅ 诊断完成")
print("="*80)
