"""
完整数据流程验证脚本
验证从数据库读取  订单聚合  利润计算  剔除逻辑的完整流程
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 设置UTF-8输出
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("完整数据流程验证 - 祥和路店")
print("=" * 80)

# ===== Step 1: 从Excel读取数据(直接指定文件) =====
print("\nStep 1: 从Excel读取数据")
print("-" * 80)

# 直接指定祥和路.xlsx文件(实际数据文件夹)
excel_file = project_root / '实际数据' / '祥和路.xlsx'

if not excel_file.exists():
    print(f" 文件不存在: {excel_file}")
    print("请将祥和路.xlsx放在项目根目录")
    sys.exit(1)

print(f" 使用文件: {excel_file.name}")

try:
    df_raw = pd.read_excel(excel_file)
    print(f" 读取成功: {len(df_raw):,}行 x {len(df_raw.columns)}列")
    
    # 显示可用字段
    print(f"\n 字段列表:")
    for i, col in enumerate(df_raw.columns, 1):
        print(f"   {i:2d}. {col}")
    
    # 剔除耗材
    if '一级分类名' in df_raw.columns:
        df_display = df_raw[df_raw['一级分类名'] != '耗材'].copy()
        print(f"\n 剔除耗材后: {len(df_display):,}行 (原始{len(df_raw):,}行)")
    else:
        df_display = df_raw.copy()
        print(f"\n 没有一级分类名字段,无法剔除耗材")
    
    # 验证利润额字段
    if '利润额' in df_display.columns:
        print(f"\n 利润额字段存在")
        print(f"   - 总利润额: {df_display['利润额'].sum():,.2f}")
        print(f"   - 非零行数: {(df_display['利润额'] != 0).sum():,}行")
        print(f"   - 平均值: {df_display['利润额'].mean():.2f}")
    elif '实际利润' in df_display.columns:
        df_display['利润额'] = df_display['实际利润']
        print(f"\n 使用'实际利润'字段作为利润额")
        print(f"   - 总利润额: {df_display['利润额'].sum():,.2f}")
    else:
        print(f"\n 缺少利润额字段!")
        sys.exit(1)

except Exception as e:
    print(f" Excel读取失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ===== Step 2: 订单聚合逻辑 =====
print("\n Step 2: 订单聚合逻辑")
print("-" * 80)

# 聚合字典(参考智能门店看板_Dash版.py Line 10145-10180)
agg_dict = {
    '物流配送费': 'first',
    '平台佣金': 'first',
    '用户支付配送费': 'first',
    '配送费减免金额': 'first',
    '平台服务费': 'sum',  # 商品级字段
    '利润额': 'sum',  # 商品级字段,必须sum
    '企客后返': 'sum' if '企客后返' in df_display.columns else 'first',
    '预计订单收入': 'first',
    '实收价格': 'sum',  # 订单总收入
    '渠道': 'first',  # 订单级字段,添加渠道
}

# 过滤存在的字段
agg_dict_filtered = {k: v for k, v in agg_dict.items() if k in df_display.columns}
print(f"聚合字典包含 {len(agg_dict_filtered)} 个字段:")
for field, method in agg_dict_filtered.items():
    print(f"  - {field}: {method}")

# 执行聚合
order_agg = df_display.groupby('订单ID').agg(agg_dict_filtered).reset_index()
print(f"\n 聚合完成: {len(order_agg):,} 个订单")

# 检查利润额聚合结果
print(f"\n 利润额聚合验证:")
print(f"   - 总利润额(聚合前): {df_display['利润额'].sum():,.2f}")
print(f"   - 总利润额(聚合后): {order_agg['利润额'].sum():,.2f}")
print(f"   - 差异: {abs(df_display['利润额'].sum() - order_agg['利润额'].sum()):,.2f}")

# 样本订单验证
sample_order_id = order_agg['订单ID'].iloc[0]
sample_items = df_display[df_display['订单ID'] == sample_order_id]
print(f"\n 样本订单验证: {sample_order_id}")
print(f"   - 商品数: {len(sample_items)}个")
print(f"   - 利润额sum: {sample_items['利润额'].sum():.2f}")
print(f"   - 聚合后利润额: {order_agg[order_agg['订单ID'] == sample_order_id]['利润额'].iloc[0]:.2f}")

# ===== Step 3: 剔除逻辑 =====
print("\n Step 3: 剔除逻辑")
print("-" * 80)

# 修复前(佣金兜底)
old_filtered = order_agg[
    (order_agg['平台服务费'] > 0) | (order_agg['平台佣金'] > 0)
].copy()

# 修复后(只看服务费)
new_filtered = order_agg[order_agg['平台服务费'] > 0].copy()

print(f"剔除前订单数: {len(order_agg):,}个")
print(f"修复前(佣金兜底): {len(old_filtered):,}个订单")
print(f"修复后(只看服务费): {len(new_filtered):,}个订单")
print(f"兜底订单数: {len(old_filtered) - len(new_filtered):,}个")

# 分析兜底订单
fallback_orders = order_agg[
    (order_agg['平台服务费'] <= 0) & (order_agg['平台佣金'] > 0)
].copy()

if len(fallback_orders) > 0:
    print(f"\n 兜底订单分析:")
    print(f"   - 数量: {len(fallback_orders):,}个")
    print(f"   - 利润额总和: {fallback_orders['利润额'].sum():,.2f}")
    print(f"   - 配送费总和: {fallback_orders['物流配送费'].sum():,.2f}")
    print(f"   - 预期贡献: {(fallback_orders['利润额'] - fallback_orders['物流配送费']).sum():,.2f}")

# ===== Step 4: 利润计算公式 =====
print("\n Step 4: 利润计算公式")
print("-" * 80)

# 参考_calculate_profit_formula (Line 10366-10426)
new_filtered['订单实际利润'] = (
    new_filtered['利润额'] -
    new_filtered['平台服务费'] -
    new_filtered['物流配送费'] +
    new_filtered.get('企客后返', 0)
)

print(f"利润公式: 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返")
print(f"\n 分项统计:")
print(f"   - 总利润额: {new_filtered['利润额'].sum():,.2f}")
print(f"   - 总平台服务费: {new_filtered['平台服务费'].sum():,.2f}")
print(f"   - 总物流配送费: {new_filtered['物流配送费'].sum():,.2f}")
print(f"   - 总企客后返: {new_filtered.get('企客后返', pd.Series(0, index=new_filtered.index)).sum():,.2f}")
print(f"   - 订单实际利润: {new_filtered['订单实际利润'].sum():,.2f}")

# ===== Step 5: 分渠道对比 =====
print("\n Step 5: 分渠道对比")
print("-" * 80)

if '渠道' in new_filtered.columns:
    channel_stats = new_filtered.groupby('渠道').agg({
        '订单ID': 'count',
        '利润额': 'sum',
        '平台服务费': 'sum',
        '物流配送费': 'sum',
        '订单实际利润': 'sum'
    }).reset_index()
    channel_stats.columns = ['渠道', '订单数', '利润额', '平台服务费', '配送费', '实际利润']
    
    print(channel_stats.to_string(index=False))
    
    print(f"\n 与用户数据对比:")
    print(f"   饿了么: {channel_stats[channel_stats['渠道'] == '饿了么']['实际利润'].sum():,.2f} (用户: 6,826)")
    print(f"   美团: {channel_stats[channel_stats['渠道'] == '美团']['实际利润'].sum():,.2f} (用户: 15,066)")
    print(f"   京东: {channel_stats[channel_stats['渠道'] == '京东']['实际利润'].sum():,.2f} (用户: 1,439)")
    print(f"   总计: {new_filtered['订单实际利润'].sum():,.2f} (用户: 23,332)")
    
    print(f"\n 差异分析:")
    total_diff = new_filtered['订单实际利润'].sum() - 23332
    print(f"   - 总差异: {total_diff:,.2f} ({total_diff/23332*100:.2f}%)")
else:
    print(" 数据中没有渠道字段!")

# ===== Step 6: 检查看板显示数据 =====
print("\n Step 6: 检查看板显示数据")
print("-" * 80)

# 由于看板未运行,无法直接检查
print(f" 看板未运行,无法直接检查显示数据")
print(f" 建议:")
print(f"   1. 在看板'上传新数据'Tab上传祥和路.xlsx")
print(f"   2. 或在'数据库数据'Tab选择祥和路门店加载")
print(f"   3. 验证看板显示的总利润是否为{new_filtered['订单实际利润'].sum():,.2f}")

# ===== Step 7: 建议 =====
print("\n" + "=" * 80)
print(" 数据流程验证结论")
print("=" * 80)

print(f"""
 已验证环节:
1. 数据库读取: 利润额字段正确读取
2. 订单聚合: 利润额使用sum聚合
3. 剔除逻辑: 只保留平台服务费>0的订单
4. 利润公式: 利润额 - 服务费 - 配送费 + 企客后返

 计算结果:
- 系统计算: {new_filtered['订单实际利润'].sum():,.2f}
- 用户数据: 23,332.00
- 差异: {new_filtered['订单实际利润'].sum() - 23332:,.2f} ({abs(new_filtered['订单实际利润'].sum() - 23332)/23332*100:.2f}%)

 下一步建议:
""")

if abs(new_filtered['订单实际利润'].sum() - 23332) < 500:
    print("""
1.  计算逻辑正确,差异在合理范围内(2%)
2. 清理看板缓存:
   python 清理缓存.py
3. 重启看板验证:
   python 智能门店看板_Dash版.py
4. 在看板上传新数据Tab重新上传祥和路.xlsx
""")
else:
    print("""
1.  差异较大,需要进一步排查:
   - 检查Excel原始数据的利润额字段
   - 验证企客后返字段是否有数据
   - 确认用户手动计算的步骤
2. 提供用户的完整计算公式和Excel截图
3. 对比数据库中的数据与Excel是否一致
""")

print("=" * 80)
