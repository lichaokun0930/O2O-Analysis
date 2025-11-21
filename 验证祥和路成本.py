import pandas as pd
import sys

print("="*60, flush=True)
print("🚀 开始验证祥和路成本数据", flush=True)
print("="*60, flush=True)

try:
    # 读取祥和路源数据
    file_path = r"实际数据\祥和路.xlsx"
    print(f"\n📂 读取文件: {file_path}", flush=True)
    df = pd.read_excel(file_path)
    print(f"✅ 文件读取成功", flush=True)

    print(f"\n📊 祥和路源数据")
    print(f"   总行数: {len(df):,}", flush=True)
except Exception as e:
    print(f"❌ 读取文件失败: {e}", flush=True)
    sys.exit(1)

try:
    # 计算商品采购成本总和
    if '商品采购成本' in df.columns:
        print(f"\n🔍 检查成本字段...", flush=True)
        total_cost = df['商品采购成本'].sum()
        print(f"\n💰 商品采购成本总和(直接求和): ¥{total_cost:,.2f}", flush=True)
        
        # 检查是否有耗材
        if '一级分类名' in df.columns:
            consumable_df = df[df['一级分类名'] == '耗材']
            consumable_cost = consumable_df['商品采购成本'].sum()
            non_consumable_cost = df[df['一级分类名'] != '耗材']['商品采购成本'].sum()
            
            print(f"\n📦 按分类统计:", flush=True)
            print(f"   耗材成本: ¥{consumable_cost:,.2f} ({len(consumable_df):,} 行)", flush=True)
            print(f"   非耗材成本: ¥{non_consumable_cost:,.2f}", flush=True)
            print(f"   差异(耗材成本): ¥{total_cost - non_consumable_cost:,.2f}", flush=True)
        
        # 检查订单维度聚合
        if '订单ID' in df.columns:
            print(f"\n📋 订单聚合测试:", flush=True)
            # 按订单聚合(含耗材)
            order_agg_full = df.groupby('订单ID').agg({
                '商品采购成本': 'sum'
            }).reset_index()
            cost_full = order_agg_full['商品采购成本'].sum()
            print(f"   含耗材订单聚合成本: ¥{cost_full:,.2f}", flush=True)
            
            # 按订单聚合(不含耗材)
            df_no_consumable = df[df['一级分类名'] != '耗材']
            order_agg_no_consumable = df_no_consumable.groupby('订单ID').agg({
                '商品采购成本': 'sum'
            }).reset_index()
            cost_no_consumable = order_agg_no_consumable['商品采购成本'].sum()
            print(f"   不含耗材订单聚合成本: ¥{cost_no_consumable:,.2f}", flush=True)
            print(f"   差异: ¥{cost_full - cost_no_consumable:,.2f}", flush=True)
    else:
        print(f"❌ 未找到'商品采购成本'字段", flush=True)

    print("\n" + "="*60, flush=True)
    print("✅ 验证完成", flush=True)
    
except Exception as e:
    print(f"\n❌ 计算过程出错: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
