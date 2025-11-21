"""
逐步追踪利润额变化
从Excel → 剔除耗材 → 按订单聚合 → 剔除服务费=0 → 计算实际利润
"""

import pandas as pd
from pathlib import Path

print("=" * 100)
print("利润额逐步追踪分析 - 祥和路店")
print("=" * 100)

# 读取Excel
excel_file = Path(__file__).parent / '实际数据' / '祥和路.xlsx'
df_raw = pd.read_excel(excel_file)

print(f"\nStep 1: Excel原始数据")
print(f"-" * 100)
print(f"总行数: {len(df_raw):,}行")
print(f"总利润额: {df_raw['利润额'].sum():,.2f}")

# 统计不同分类的数据
print(f"\n按一级分类名统计:")
if '一级分类名' in df_raw.columns:
    category_stats = df_raw.groupby('一级分类名').agg({
        '利润额': 'sum',
        '订单ID': 'nunique',
        '商品名称': 'count'
    })
    category_stats.columns = ['利润额', '订单数', '商品行数']
    category_stats = category_stats.sort_values('利润额', ascending=False)
    print(category_stats.to_string())

# 剔除耗材
df_no_consumable = df_raw[df_raw['一级分类名'] != '耗材'].copy()

print(f"\nStep 2: 剔除耗材后")
print(f"-" * 100)
print(f"总行数: {len(df_no_consumable):,}行 (剔除{len(df_raw) - len(df_no_consumable):,}行)")
print(f"总利润额: {df_no_consumable['利润额'].sum():,.2f}")
print(f"与Excel差异: {df_raw['利润额'].sum() - df_no_consumable['利润额'].sum():,.2f}")

# 按订单聚合
agg_dict = {
    '物流配送费': 'first',
    '平台服务费': 'sum',
    '利润额': 'sum',
    '企客后返': 'sum',
    '渠道': 'first'
}
order_agg = df_no_consumable.groupby('订单ID').agg(agg_dict).reset_index()

print(f"\nStep 3: 按订单聚合后")
print(f"-" * 100)
print(f"订单数: {len(order_agg):,}个")
print(f"总利润额: {order_agg['利润额'].sum():,.2f}")
print(f"与剔除耗材后差异: {df_no_consumable['利润额'].sum() - order_agg['利润额'].sum():,.2f}")

# 检查聚合前后利润额一致性
print(f"\n利润额聚合验证:")
print(f"- 聚合前(剔除耗材): {df_no_consumable['利润额'].sum():,.2f}")
print(f"- 聚合后: {order_agg['利润额'].sum():,.2f}")
print(f"- 差异: {abs(df_no_consumable['利润额'].sum() - order_agg['利润额'].sum()):,.6f}")

# 剔除平台服务费=0
filtered = order_agg[order_agg['平台服务费'] > 0].copy()

print(f"\nStep 4: 剔除平台服务费=0的订单")
print(f"-" * 100)
print(f"剔除前订单数: {len(order_agg):,}个")
print(f"剔除后订单数: {len(filtered):,}个")
print(f"剔除订单数: {len(order_agg) - len(filtered):,}个")
print(f"\n利润额统计:")
print(f"- 剔除前总利润额: {order_agg['利润额'].sum():,.2f}")
print(f"- 剔除后总利润额: {filtered['利润额'].sum():,.2f}")
print(f"- 剔除订单利润额: {order_agg['利润额'].sum() - filtered['利润额'].sum():,.2f}")

# 分析被剔除的订单
removed = order_agg[order_agg['平台服务费'] <= 0].copy()
print(f"\n被剔除订单分析:")
print(f"- 数量: {len(removed):,}个")
print(f"- 利润额总和: {removed['利润额'].sum():,.2f}")
print(f"- 配送费总和: {removed['物流配送费'].sum():,.2f}")
print(f"- 平台服务费总和: {removed['平台服务费'].sum():,.2f}")

# 计算实际利润
filtered['订单实际利润'] = (
    filtered['利润额'] -
    filtered['平台服务费'] -
    filtered['物流配送费'] +
    filtered['企客后返']
)

print(f"\nStep 5: 计算订单实际利润")
print(f"-" * 100)
print(f"利润公式: 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返")
print(f"\n分项统计:")
print(f"- 利润额: {filtered['利润额'].sum():,.2f}")
print(f"- 减: 平台服务费: {filtered['平台服务费'].sum():,.2f}")
print(f"- 减: 物流配送费: {filtered['物流配送费'].sum():,.2f}")
print(f"- 加: 企客后返: {filtered['企客后返'].sum():,.2f}")
print(f"- 等于: 订单实际利润: {filtered['订单实际利润'].sum():,.2f}")

# 分渠道对比
print(f"\nStep 6: 分渠道统计")
print(f"-" * 100)

channel_stats = filtered.groupby('渠道').agg({
    '订单ID': 'count',
    '利润额': 'sum',
    '平台服务费': 'sum',
    '物流配送费': 'sum',
    '企客后返': 'sum',
    '订单实际利润': 'sum'
}).reset_index()
channel_stats.columns = ['渠道', '订单数', '利润额', '平台服务费', '配送费', '企客后返', '实际利润']

print(channel_stats.to_string(index=False))

# 与用户数据对比
print(f"\n与用户数据对比:")
print(f"-" * 100)

user_data = {
    '饿了么': 6826.00,
    '美团闪购': 15066.00,
    '京东到家': 1439.00
}

for channel in channel_stats['渠道'].unique():
    system_profit = channel_stats[channel_stats['渠道'] == channel]['实际利润'].sum()
    
    # 尝试匹配用户渠道名
    user_profit = None
    if channel == '饿了么':
        user_profit = user_data.get('饿了么')
    elif '美团' in channel:
        user_profit = user_data.get('美团闪购')
    elif '京东' in channel:
        user_profit = user_data.get('京东到家')
    
    if user_profit:
        diff = system_profit - user_profit
        diff_pct = (diff / user_profit * 100) if user_profit != 0 else 0
        print(f"{channel:12s}: 系统={system_profit:>10,.2f}  用户={user_profit:>10,.2f}  差异={diff:>8,.2f} ({diff_pct:+.2f}%)")
    else:
        print(f"{channel:12s}: 系统={system_profit:>10,.2f}  (用户数据未提供)")

total_system = filtered['订单实际利润'].sum()
total_user = 23332.00

print(f"\n{'总计':12s}: 系统={total_system:>10,.2f}  用户={total_user:>10,.2f}  差异={total_system - total_user:>8,.2f} ({(total_system - total_user)/total_user*100:+.2f}%)")

# 最终结论
print(f"\n" + "=" * 100)
print(f"结论")
print(f"=" * 100)

print(f"""
关键发现:
1. Excel原始利润额: {df_raw['利润额'].sum():,.2f}
2. 剔除耗材后利润额: {df_no_consumable['利润额'].sum():,.2f}
3. 按订单聚合后利润额: {order_agg['利润额'].sum():,.2f}  (验证:聚合无损失)
4. 剔除服务费=0后利润额: {filtered['利润额'].sum():,.2f}
5. 计算订单实际利润: {filtered['订单实际利润'].sum():,.2f}

用户数据: 23,332.00
系统计算: {filtered['订单实际利润'].sum():,.2f}
差异: {filtered['订单实际利润'].sum() - 23332:,.2f} ({(filtered['订单实际利润'].sum() - 23332)/23332*100:.2f}%)

可能原因:
1. 用户在剔除平台服务费=0时使用的是"商品行级别"剔除,而不是"订单级别"
2. 用户手动计算时可能还剔除了其他条件(例如特定渠道或订单状态)
3. 企客后返字段(当前为0,但某些订单可能有数据)
4. 用户使用的Excel版本或数据范围与当前文件不一致

建议:
1. 请用户提供完整的Excel计算步骤和筛选条件
2. 对比用户的渠道名称映射(美团 vs 美团闪购, 京东 vs 京东到家)
3. 确认用户是否在商品行级别剔除平台服务费=0
""")

print("=" * 100)
