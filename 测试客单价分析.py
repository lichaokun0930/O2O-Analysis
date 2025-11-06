"""测试客单价分析功能"""
import pandas as pd
import sys
sys.path.append('.')

# 直接加载数据
df = pd.read_excel('门店数据/2025-09-01 00_00_00至2025-09-30 12_42_28订单明细数据导出汇总 (2).xlsx')

# 基础数据处理
df['日期'] = pd.to_datetime(df['日期'])
df = df[df['商品实售价'] > 0]  # 过滤无效数据

print(f"✅ 数据加载完成，共 {len(df)} 行")
print(f"📅 日期范围: {df['日期'].min()} ~ {df['日期'].max()}")
print(f"🔑 关键字段: {df.columns.tolist()[:10]}")

# 检查订单ID
if '订单ID' in df.columns:
    print(f"📦 订单数量: {df['订单ID'].nunique()}")
    sample_orders = df.groupby('订单ID')['商品实售价'].sum().head()
    print(f"\n📊 样本订单金额:")
    for oid, total in sample_orders.items():
        print(f"  {oid}: ¥{total:.2f}")
else:
    print("❌ 缺少'订单ID'字段！")
    sys.exit(1)

# 简单测试：手动计算客单价
print("\n" + "="*60)
print("手动计算测试")
print("="*60)

# 按周分组计算
df['周'] = df['日期'].dt.isocalendar().week
weekly_prices = df.groupby(['周', '订单ID'])['商品实售价'].sum().groupby('周').mean()
print(f"\n📊 每周平均客单价:")
for week, price in weekly_prices.items():
    print(f"  第{week}周: ¥{price:.2f}")

# 检查数据量
weekly_counts = df.groupby('周')['订单ID'].nunique()
print(f"\n📦 每周订单数:")
for week, count in weekly_counts.items():
    print(f"  第{week}周: {count}单")
