# -*- coding: utf-8 -*-
import pandas as pd
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

df = pd.read_excel('实际数据/金寨.xlsx')

print("=" * 80)
print("逐步分析：美团闪购利润计算")
print("=" * 80)
print("看板显示: ¥14,247")
print("您的计算: ¥13,716")
print("脚本计算: ¥10,730")
print("=" * 80)

# Step 1: 原始数据
df_meituan = df[df['渠道'] == '美团闪购'].copy()
print(f"\nStep 1: 原始美团闪购数据")
print(f"  数据行数: {len(df_meituan)}")
print(f"  订单数: {df_meituan['订单ID'].nunique()}")

# Step 2: 检查各关键字段的总和
print(f"\nStep 2: 关键字段直接求和（未聚合）")
print(f"  预计订单收入总和: ¥{df_meituan['预计订单收入'].sum():,.2f}")
print(f"  成本总和: ¥{df_meituan['成本'].sum():,.2f}")
print(f"  平台佣金总和: ¥{df_meituan['平台佣金'].sum():,.2f}")
print(f"  物流配送费总和: ¥{df_meituan['物流配送费'].sum():,.2f}")
print(f"  配送费减免总和: ¥{df_meituan['配送费减免金额'].sum():,.2f}")
print(f"  用户支付配送费总和: ¥{df_meituan['用户支付配送费'].sum():,.2f}")

# Step 3: 订单级聚合
print(f"\nStep 3: 订单级聚合")

df_meituan['物流配送费'] = df_meituan['物流配送费'].fillna(0)
df_meituan['配送费减免金额'] = df_meituan['配送费减免金额'].fillna(0)
df_meituan['用户支付配送费'] = df_meituan['用户支付配送费'].fillna(0)

order_agg = df_meituan.groupby('订单ID').agg({
    '预计订单收入': 'sum',  # 商品级，求和
    '成本': 'sum',           # 商品级，求和
    '平台佣金': 'first',     # 订单级，取第一个
    '物流配送费': 'first',   # 订单级，取第一个
    '配送费减免金额': 'first', # 订单级，取第一个
    '用户支付配送费': 'first', # 订单级，取第一个
    '新客减免金额': 'first' if '新客减免金额' in df_meituan.columns else lambda x: 0,
    '企客后返': 'sum' if '企客后返' in df_meituan.columns else lambda x: 0,
}).reset_index()

print(f"  订单数: {len(order_agg)}")
print(f"  预计订单收入: ¥{order_agg['预计订单收入'].sum():,.2f}")
print(f"  成本: ¥{order_agg['成本'].sum():,.2f}")
print(f"  平台佣金: ¥{order_agg['平台佣金'].sum():,.2f}")
print(f"  物流配送费: ¥{order_agg['物流配送费'].sum():,.2f}")
print(f"  配送费减免: ¥{order_agg['配送费减免金额'].sum():,.2f}")
print(f"  用户支付配送费: ¥{order_agg['用户支付配送费'].sum():,.2f}")

if '新客减免金额' in order_agg.columns:
    print(f"  新客减免金额: ¥{order_agg['新客减免金额'].sum():,.2f}")
if '企客后返' in order_agg.columns:
    print(f"  企客后返: ¥{order_agg['企客后返'].sum():,.2f}")

# Step 4: 计算利润（分步骤）
print(f"\nStep 4: 分步计算利润")

# 4.1 利润额
order_agg['利润额'] = (
    order_agg['预计订单收入'] - 
    order_agg['成本'] - 
    order_agg['平台佣金'] - 
    order_agg['物流配送费'] - 
    order_agg['配送费减免金额'] + 
    order_agg['用户支付配送费']
)

利润额总和 = order_agg['利润额'].sum()
print(f"  利润额 = 预计订单收入 - 成本 - 佣金 - 配送费 - 配送减免 + 用户付配送")
print(f"  利润额总和: ¥{利润额总和:,.2f}")

# 4.2 订单实际利润
新客减免 = order_agg.get('新客减免金额', pd.Series([0])).sum()
企客后返 = order_agg.get('企客后返', pd.Series([0])).sum()

order_agg['订单实际利润'] = (
    order_agg['利润额'] -
    order_agg.get('新客减免金额', 0) +
    order_agg.get('企客后返', 0)
)

订单实际利润 = order_agg['订单实际利润'].sum()

print(f"  新客减免金额: ¥{新客减免:,.2f}")
print(f"  企客后返: ¥{企客后返:,.2f}")
print(f"  订单实际利润 = 利润额 - 新客减免 + 企客后返")
print(f"  订单实际利润: ¥{订单实际利润:,.2f}")

# Step 5: 对比分析
print(f"\n" + "=" * 80)
print("对比分析")
print("=" * 80)
print(f"看板显示:   ¥14,247.00")
print(f"您的计算:   ¥13,716.00  (差异: ¥{14247 - 13716:,.2f})")
print(f"脚本计算:   ¥{订单实际利润:,.2f}  (差异: ¥{13716 - 订单实际利润:,.2f})")

# 可能的差异原因
print(f"\n" + "=" * 80)
print("差异原因分析")
print("=" * 80)

# 检查1: 订单级字段是否重复累加
平台佣金_错误求和 = df_meituan['平台佣金'].sum()
平台佣金_正确聚合 = order_agg['平台佣金'].sum()
if abs(平台佣金_错误求和 - 平台佣金_正确聚合) > 0.01:
    print(f"\n❌ 可能问题1: 订单级字段被重复累加")
    print(f"   平台佣金(错误-直接求和): ¥{平台佣金_错误求和:,.2f}")
    print(f"   平台佣金(正确-订单聚合): ¥{平台佣金_正确聚合:,.2f}")
    print(f"   差异: ¥{平台佣金_错误求和 - 平台佣金_正确聚合:,.2f}")

# 检查2: 计算公式差异
print(f"\n尝试不同公式:")

# 可能的公式1: 不包含配送费减免
公式1 = (
    order_agg['预计订单收入'].sum() -
    order_agg['成本'].sum() -
    order_agg['平台佣金'].sum() -
    order_agg['物流配送费'].sum() +
    order_agg['用户支付配送费'].sum() -
    新客减免 +
    企客后返
)
print(f"  公式1(不含配送减免): ¥{公式1:,.2f}  差异vs您: ¥{abs(公式1 - 13716):,.2f}")

# 可能的公式2: 使用配送净成本
配送净成本 = (
    order_agg['物流配送费'].sum() -
    order_agg['配送费减免金额'].sum() +
    order_agg['用户支付配送费'].sum()
)
公式2 = (
    order_agg['预计订单收入'].sum() -
    order_agg['成本'].sum() -
    order_agg['平台佣金'].sum() -
    配送净成本 -
    新客减免 +
    企客后返
)
print(f"  公式2(使用配送净成本): ¥{公式2:,.2f}  差异vs您: ¥{abs(公式2 - 13716):,.2f}")

# 可能的公式3: 不减配送费减免
公式3 = (
    order_agg['预计订单收入'].sum() -
    order_agg['成本'].sum() -
    order_agg['平台佣金'].sum() -
    order_agg['物流配送费'].sum() -
    新客减免 +
    企客后返
)
print(f"  公式3(不减配送减免): ¥{公式3:,.2f}  差异vs您: ¥{abs(公式3 - 13716):,.2f}")

print(f"\n最接近您计算结果的公式:")
diffs = {
    '公式1': abs(公式1 - 13716),
    '公式2': abs(公式2 - 13716),
    '公式3': abs(公式3 - 13716),
    '当前公式': abs(订单实际利润 - 13716)
}
best = min(diffs, key=diffs.get)
print(f"  {best}, 差异仅 ¥{diffs[best]:,.2f}")
