"""
测试数据字段完整性
检查库存、月售、成本等字段是否存在
"""
import sys
from pathlib import Path

# 设置输出编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

import pandas as pd
from database.data_source_manager import DataSourceManager

print("="*80)
print("📊 测试数据字段完整性")
print("="*80)

# 初始化数据源管理器
manager = DataSourceManager()

# 获取可用门店
stores = manager.get_available_stores()
print(f"\n✅ 可用门店: {stores}")

if stores:
    store = stores[0]
    print(f"✅ 使用门店: {store}")
    
    # 加载数据
    loaded_data = manager.load_from_database(store_name=store)
    
    if isinstance(loaded_data, dict):
        df_full = loaded_data['full']
        df_display = loaded_data['display']
        
        print(f"\n📊 完整数据: {len(df_full):,}行")
        print(f"📊 展示数据: {len(df_display):,}行")
        
        # 检查关键字段
        critical_fields = {
            '库存相关': ['库存', '剩余库存'],
            '销量相关': ['月售', '销量'],
            '成本相关': ['商品采购成本', '利润额', '平台服务费', '物流配送费'],
            '分类相关': ['一级分类名', '三级分类名'],
            '时间相关': ['日期', '下单时间']
        }
        
        print("\n" + "="*80)
        print("字段存在性检查")
        print("="*80)
        
        for category, fields in critical_fields.items():
            print(f"\n【{category}】")
            for field in fields:
                if field in df_display.columns:
                    # 检查非空值数量
                    non_null_count = df_display[field].notna().sum()
                    non_zero_count = (df_display[field] != 0).sum() if pd.api.types.is_numeric_dtype(df_display[field]) else non_null_count
                    print(f"  ✅ {field}: {non_null_count:,}行非空, {non_zero_count:,}行非零")
                    
                    # 如果是数值字段,显示统计信息
                    if pd.api.types.is_numeric_dtype(df_display[field]):
                        print(f"     范围: {df_display[field].min():.2f} ~ {df_display[field].max():.2f}, 均值: {df_display[field].mean():.2f}")
                else:
                    print(f"  ❌ {field}: 不存在")
        
        # 检查耗材数据的成本
        if '一级分类名' in df_full.columns:
            consumable = df_full[df_full['一级分类名'] == '耗材']
            if len(consumable) > 0:
                print(f"\n" + "="*80)
                print(f"耗材数据检查 ({len(consumable):,}行)")
                print("="*80)
                
                if '商品采购成本' in consumable.columns:
                    cost = consumable['商品采购成本'].sum()
                    print(f"  商品采购成本总计: {cost:,.2f}元")
                
                if '利润额' in consumable.columns:
                    profit = consumable['利润额'].sum()
                    print(f"  利润额总计: {profit:,.2f}元")
        
        # 检查一级分类分布
        if '一级分类名' in df_display.columns:
            print(f"\n" + "="*80)
            print("一级分类分布")
            print("="*80)
            category_dist = df_display['一级分类名'].value_counts()
            for cat, count in category_dist.head(10).items():
                print(f"  {cat}: {count:,}行")

print("\n" + "="*80)
print("✅ 测试完成")
print("="*80)
