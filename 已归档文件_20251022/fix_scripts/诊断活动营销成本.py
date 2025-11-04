"""
诊断活动营销成本计算
详细分析每个营销字段的贡献
"""
import pandas as pd
import sys
import os

# 添加父目录到路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from standard_business_config import (
    StandardBusinessConfig,
    StandardBusinessLogic,
    create_order_level_summary,
    apply_standard_business_logic
)

# 读取数据
# 从命令行参数获取数据文件路径
if len(sys.argv) > 1:
    data_file = sys.argv[1]
else:
    print("=" * 80)
    print("📊 活动营销成本详细诊断")
    print("=" * 80)
    print("\n❌ 请提供数据文件路径")
    print("用法: python 诊断活动营销成本.py <数据文件路径>")
    print("=" * 80)
    sys.exit(1)

print("=" * 80)
print("📊 活动营销成本详细诊断")
print("=" * 80)
print(f"📂 数据文件: {data_file}")

try:
    df = pd.read_excel(data_file)
    print(f"\n✅ 成功读取数据: {len(df)} 行")
    
    # 剔除耗材
    original_count = len(df)
    category_col = None
    for col in ['一级分类名', '美团一级分类', '一级分类']:
        if col in df.columns:
            category_col = col
            break
    
    if category_col:
        df_clean = df[~df[category_col].str.contains('耗材|购物袋', na=False, case=False)].copy()
        removed = original_count - len(df_clean)
        print(f"✅ 剔除 {removed} 行耗材数据，剩余 {len(df_clean)} 行")
        df = df_clean
    
    # 创建订单级汇总
    print("\n" + "=" * 80)
    print("1️⃣ 创建订单级汇总")
    print("=" * 80)
    
    order_agg = create_order_level_summary(df, StandardBusinessConfig)
    print(f"✅ 订单数: {len(order_agg)}")
    
    # 检查活动营销相关字段
    print("\n" + "=" * 80)
    print("2️⃣ 检查活动营销相关字段（订单级汇总后）")
    print("=" * 80)
    
    marketing_fields = [
        '满减金额',
        '商家代金券',
        '商家承担部分券',
        '满赠金额',
        '新客减免金额'
    ]
    
    print("⚠️ 注意：配送费减免金额已在配送成本中扣除，不计入活动营销成本")
    print("=" * 80)
    
    field_totals = {}
    for field in marketing_fields:
        if field in order_agg.columns:
            total = order_agg[field].sum()
            field_totals[field] = total
            non_zero_count = (order_agg[field] > 0).sum()
            print(f"✅ {field}:")
            print(f"   - 总额: ¥{total:,.2f}")
            print(f"   - 非零订单数: {non_zero_count}")
            print(f"   - 平均值: ¥{order_agg[field].mean():,.2f}")
        else:
            print(f"❌ {field}: 字段不存在")
            field_totals[field] = 0
    
    # 应用业务逻辑计算
    print("\n" + "=" * 80)
    print("3️⃣ 应用业务逻辑计算活动营销成本")
    print("=" * 80)
    
    order_agg = apply_standard_business_logic(order_agg)
    
    if '活动营销成本' in order_agg.columns:
        total_activity_marketing = order_agg['活动营销成本'].sum()
        print(f"\n✅ 总活动营销成本: ¥{total_activity_marketing:,.2f}")
        print(f"   - 平均每单: ¥{order_agg['活动营销成本'].mean():,.2f}")
        print(f"   - 非零订单数: {(order_agg['活动营销成本'] > 0).sum()}")
    
    # 验证计算
    print("\n" + "=" * 80)
    print("4️⃣ 验证计算（手动求和）")
    print("=" * 80)
    
    manual_total = sum(field_totals.values())
    print(f"\n手动求和所有字段:")
    for field, total in field_totals.items():
        print(f"  {field}: ¥{total:,.2f}")
    print(f"  {'=' * 40}")
    print(f"  手动总和: ¥{manual_total:,.2f}")
    
    if '活动营销成本' in order_agg.columns:
        system_total = order_agg['活动营销成本'].sum()
        print(f"  系统计算: ¥{system_total:,.2f}")
        
        if abs(manual_total - system_total) < 0.01:
            print(f"  ✅ 计算一致！")
        else:
            print(f"  ⚠️ 差异: ¥{abs(manual_total - system_total):,.2f}")
    
    # 检查原始数据中的字段（查看是否是订单级重复）
    print("\n" + "=" * 80)
    print("5️⃣ 检查原始数据字段特征（前10个订单）")
    print("=" * 80)
    
    sample_orders = df['订单ID'].unique()[:10]
    for order_id in sample_orders:
        order_rows = df[df['订单ID'] == order_id]
        print(f"\n订单ID: {order_id} ({len(order_rows)} 个商品)")
        
        for field in marketing_fields:
            if field in df.columns:
                values = order_rows[field].unique()
                if len(values) == 1:
                    print(f"  {field}: ¥{values[0]} (所有商品行相同 ✅)")
                else:
                    print(f"  {field}: {len(values)}个不同值 ⚠️ {values}")
    
    # 样本订单详细分析
    print("\n" + "=" * 80)
    print("6️⃣ 样本订单活动营销成本详细分析（前5个订单）")
    print("=" * 80)
    print("⚠️ 配送费减免已在配送成本中扣除，不计入活动营销成本")
    print("=" * 80)
    
    sample_order_agg = order_agg.head(5)
    for idx, row in sample_order_agg.iterrows():
        print(f"\n订单ID: {row['订单ID']}")
        print(f"  配送费减免: ¥{row.get('配送费减免金额', 0):,.2f} (已在配送成本扣除)")
        print(f"  满减金额: ¥{row.get('满减金额', 0):,.2f}")
        print(f"  商家代金券: ¥{row.get('商家代金券', 0):,.2f}")
        print(f"  商家承担部分券: ¥{row.get('商家承担部分券', 0):,.2f}")
        print(f"  满赠金额: ¥{row.get('满赠金额', 0):,.2f}")
        print(f"  新客减免: ¥{row.get('新客减免金额', 0):,.2f}")
        print(f"  ─────────────────────")
        print(f"  活动营销成本: ¥{row.get('活动营销成本', 0):,.2f}")
        
        # 手动验证（不含配送费减免）
        manual = (
            row.get('满减金额', 0) +
            row.get('商家代金券', 0) +
            row.get('商家承担部分券', 0) +
            row.get('满赠金额', 0) +
            row.get('新客减免金额', 0)
        )
        print(f"  手动计算: ¥{manual:,.2f}")
        if abs(manual - row.get('活动营销成本', 0)) < 0.01:
            print(f"  ✅ 一致")
        else:
            print(f"  ⚠️ 不一致")
    
    print("\n" + "=" * 80)
    print("✅ 诊断完成")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()
