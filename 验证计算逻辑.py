"""验证当前代码与历史报告的计算逻辑一致性"""
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. 读取历史报告
print("=" * 80)
print("【步骤1】读取历史科学分析报告 (2025-11-17 22:01)")
print("=" * 80)
df_history = pd.read_excel('门店数据/科学分析报告_20251117_220136.xlsx', sheet_name='科学方法分析')
print(f"商品总数: {len(df_history)}")
print(f"\n前3个商品的关键数据:")
print(df_history[['商品名称', '营销占比', '毛利率', '售罄率', '象限编号', '象限名称']].head(3))

print(f"\n统计信息:")
print(f"营销占比范围: {df_history['营销占比'].min():.6f} ~ {df_history['营销占比'].max():.6f}")
print(f"毛利率范围: {df_history['毛利率'].min():.6f} ~ {df_history['毛利率'].max():.6f}")
print(f"售罄率范围: {df_history['售罄率'].min():.6f} ~ {df_history['售罄率'].max():.6f}")

print(f"\n阈值信息 (全局固定阈值):")
print(f"营销阈值: {df_history['营销阈值'].iloc[0]:.6f}")
print(f"毛利阈值: {df_history['毛利阈值'].iloc[0]:.6f}")
print(f"售罄率阈值: {df_history['售罄率阈值'].iloc[0]:.6f}")

# 2. 加载原始数据并用当前代码计算
print("\n" + "=" * 80)
print("【步骤2】用当前代码重新计算")
print("=" * 80)

# 从数据库加载祥和路店的数据
from database.data_source_manager import DataSourceManager
data_manager = DataSourceManager()

print("正在从数据库加载祥和路店数据...")
df_raw = data_manager.load_from_database(
    store_name='惠宜选超市（徐州祥和路店）',
    start_date=None,
    end_date=None
)

print(f"原始数据量: {len(df_raw)} 行")
print(f"日期范围: {df_raw['日期'].min()} ~ {df_raw['日期'].max()}")

# 使用当前的科学八象限分析器
from 科学八象限分析器 import ScientificQuadrantAnalyzer

analyzer = ScientificQuadrantAnalyzer(df_raw, use_category_threshold=True)  # ✅ 使用品类动态阈值（与历史报告一致）
df_result = analyzer.analyze_with_confidence()

print(f"\n计算结果: {len(df_result)} 个商品")
print(f"\n前3个商品的关键数据:")
print(df_result[['商品名称', '营销占比', '毛利率', '动销率', '象限编号', '象限名称']].head(3))

print(f"\n统计信息:")
print(f"营销占比范围: {df_result['营销占比'].min():.6f} ~ {df_result['营销占比'].max():.6f}")
print(f"毛利率范围: {df_result['毛利率'].min():.6f} ~ {df_result['毛利率'].max():.6f}")
print(f"动销率范围: {df_result['动销率'].min():.6f} ~ {df_result['动销率'].max():.6f}")

# 3. 对比关键商品的计算结果
print("\n" + "=" * 80)
print("【步骤3】对比具体商品的计算数值")
print("=" * 80)

# 选择同一个商品对比
test_product = df_history['商品名称'].iloc[0]
print(f"测试商品: {test_product}")

hist_row = df_history[df_history['商品名称'] == test_product].iloc[0]
curr_row = df_result[df_result['商品名称'] == test_product].iloc[0] if test_product in df_result['商品名称'].values else None

if curr_row is not None:
    print(f"\n【历史报告】:")
    print(f"  营销占比: {hist_row['营销占比']:.6f}")
    print(f"  毛利率: {hist_row['毛利率']:.6f}")
    print(f"  售罄率: {hist_row['售罄率']:.6f}")
    print(f"  象限: {hist_row['象限编号']} {hist_row['象限名称']}")
    print(f"  利润额: {hist_row['利润额']:.2f}")
    print(f"  实收价格: {hist_row['实收价格']:.2f}")
    
    print(f"\n【当前计算】:")
    print(f"  营销占比: {curr_row['营销占比']:.6f}")
    print(f"  毛利率: {curr_row['毛利率']:.6f}")
    print(f"  动销率: {curr_row['动销率']:.6f}")
    print(f"  象限: {curr_row['象限编号']} {curr_row['象限名称']}")
    print(f"  利润额: {curr_row['利润额']:.2f}")
    print(f"  实收价格: {curr_row['实收价格']:.2f}")
    
    print(f"\n【差异分析】:")
    print(f"  营销占比差异: {abs(hist_row['营销占比'] - curr_row['营销占比']):.6f}")
    print(f"  毛利率差异: {abs(hist_row['毛利率'] - curr_row['毛利率']):.6f}")
    print(f"  利润额差异: {abs(hist_row['利润额'] - curr_row['利润额']):.2f}")
    print(f"  实收价格差异: {abs(hist_row['实收价格'] - curr_row['实收价格']):.2f}")
else:
    print(f"⚠️ 当前计算结果中未找到该商品")

# 4. 检查计算公式
print("\n" + "=" * 80)
print("【步骤4】验证计算公式")
print("=" * 80)

if curr_row is not None:
    # 从原始数据中找到该商品的明细
    product_details = df_raw[df_raw['商品名称'] == test_product]
    
    print(f"该商品的原始订单明细: {len(product_details)} 条")
    total_revenue = product_details['实收价格'].sum()
    total_profit = product_details['利润额'].sum()
    total_sales = product_details['月售'].sum()
    order_count = product_details['订单ID'].nunique()
    
    print(f"\n【聚合计算】:")
    print(f"  实收价格总和: {total_revenue:.2f}")
    print(f"  利润额总和: {total_profit:.2f}")
    print(f"  销量总和: {total_sales}")
    print(f"  订单数: {order_count}")
    
    # 计算毛利率
    calculated_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
    print(f"\n【毛利率验证】:")
    print(f"  历史报告毛利率: {hist_row['毛利率']:.4f}%")
    print(f"  当前计算毛利率: {curr_row['毛利率']:.4f}%")
    print(f"  手动计算毛利率: (利润额 {total_profit:.2f} / 实收价格 {total_revenue:.2f}) × 100 = {calculated_margin:.4f}%")
    print(f"  ✅ 公式一致" if abs(curr_row['毛利率'] - calculated_margin) < 0.01 else "❌ 公式不一致")

print("\n" + "=" * 80)
print("【总结】")
print("=" * 80)
print("如果营销占比、毛利率、利润额、实收价格的数值完全一致或差异极小(<0.01),")
print("说明计算逻辑正确。如果差异较大,需要检查数据源或聚合方式。")
