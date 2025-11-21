"""
完整验证数据分离方案
验证所有数据加载路径的数据分离正确性
"""
import sys
from pathlib import Path

# 添加项目路径
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

import pandas as pd
from database.data_source_manager import DataSourceManager

print("="*80)
print("📊 完整验证数据分离方案")
print("="*80)

# 初始化数据源管理器
manager = DataSourceManager()

# ========== 验证0: 查询可用门店 ==========
print("\n【验证0】查询可用门店")
print("-"*80)
try:
    stores = manager.get_available_stores()
    print(f"✅ 可用门店: {stores}")
    
    if stores:
        selected_store = stores[0]
        print(f"✅ 使用门店: {selected_store}")
    else:
        print("❌ 没有可用门店")
        sys.exit(1)
except Exception as e:
    print(f"❌ 查询门店失败: {e}")
    sys.exit(1)

# ========== 验证1: 数据库加载返回dict结构 ==========
print("\n【验证1】数据库加载返回dict结构")
print("-"*80)
try:
    loaded_data = manager.load_from_database(store_name=selected_store)
    
    if isinstance(loaded_data, dict):
        print("✅ 返回dict结构")
        print(f"   包含键: {list(loaded_data.keys())}")
        
        df_full = loaded_data['full']
        df_display = loaded_data['display']
        
        print(f"✅ 完整数据: {len(df_full):,}行")
        print(f"✅ 展示数据: {len(df_display):,}行")
        print(f"✅ 耗材数据: {len(df_full) - len(df_display):,}行")
    else:
        print("❌ 返回DataFrame,未分离")
except Exception as e:
    print(f"❌ 数据库加载失败: {e}")

# ========== 验证2: 展示数据不含耗材 ==========
print("\n【验证2】展示数据不含耗材")
print("-"*80)
if isinstance(loaded_data, dict):
    df_display = loaded_data['display']
    if '一级分类名' in df_display.columns:
        consumable_count = (df_display['一级分类名'] == '耗材').sum()
        if consumable_count == 0:
            print("✅ 展示数据不含耗材")
        else:
            print(f"❌ 展示数据仍包含{consumable_count}行耗材")
    else:
        print("⚠️ 展示数据缺少'一级分类名'字段")

# ========== 验证3: 完整数据含耗材 ==========
print("\n【验证3】完整数据含耗材")
print("-"*80)
if isinstance(loaded_data, dict):
    df_full = loaded_data['full']
    if '一级分类名' in df_full.columns:
        consumable_count = (df_full['一级分类名'] == '耗材').sum()
        print(f"✅ 完整数据包含{consumable_count:,}行耗材")
        
        # 验证耗材利润
        consumable_data = df_full[df_full['一级分类名'] == '耗材']
        if not consumable_data.empty and '利润额' in consumable_data.columns:
            consumable_profit = consumable_data['利润额'].sum()
            print(f"   耗材总利润: {consumable_profit:,.2f}元")
            
            if consumable_profit < 0:
                print(f"   ✅ 耗材利润为负值,符合预期")
    else:
        print("⚠️ 完整数据缺少'一级分类名'字段")

# ========== 验证4: 利润计算差异 ==========
print("\n【验证4】利润计算差异")
print("-"*80)
if isinstance(loaded_data, dict):
    df_full = loaded_data['full']
    df_display = loaded_data['display']
    
    # 需要的字段
    profit_fields = ['利润额', '平台服务费', '物流配送费', '企客后返']
    
    # 检查字段存在性
    missing_full = [f for f in profit_fields if f not in df_full.columns]
    missing_display = [f for f in profit_fields if f not in df_display.columns]
    
    if not missing_full and not missing_display:
        # 计算完整数据利润
        df_full_filtered = df_full[df_full['平台服务费'] > 0].copy()
        full_profit_base = df_full_filtered['利润额'].sum()
        full_service_fee = df_full_filtered['平台服务费'].sum()
        full_delivery_fee = df_full_filtered['物流配送费'].sum()
        full_rebate = df_full_filtered['企客后返'].sum()
        full_profit = full_profit_base - full_service_fee - full_delivery_fee + full_rebate
        
        # 计算展示数据利润
        df_display_filtered = df_display[df_display['平台服务费'] > 0].copy()
        display_profit_base = df_display_filtered['利润额'].sum()
        display_service_fee = df_display_filtered['平台服务费'].sum()
        display_delivery_fee = df_display_filtered['物流配送费'].sum()
        display_rebate = df_display_filtered['企客后返'].sum()
        display_profit = display_profit_base - display_service_fee - display_delivery_fee + display_rebate
        
        print(f"完整数据利润(含耗材): {full_profit:,.2f}元")
        print(f"展示数据利润(不含耗材): {display_profit:,.2f}元")
        print(f"差异: {display_profit - full_profit:,.2f}元")
        
        if display_profit > full_profit:
            print("✅ 展示数据利润更高(剔除负利润耗材后)")
        else:
            print("⚠️ 异常:展示数据利润应该更高")
    else:
        print(f"⚠️ 字段缺失")
        if missing_full:
            print(f"   完整数据缺少: {missing_full}")
        if missing_display:
            print(f"   展示数据缺少: {missing_display}")

# ========== 验证5: 数据结构一致性 ==========
print("\n【验证5】数据结构一致性")
print("-"*80)
if isinstance(loaded_data, dict):
    df_full = loaded_data['full']
    df_display = loaded_data['display']
    
    full_cols = set(df_full.columns)
    display_cols = set(df_display.columns)
    
    if full_cols == display_cols:
        print("✅ 完整数据和展示数据字段一致")
        print(f"   共{len(full_cols)}个字段")
    else:
        print("⚠️ 字段不一致")
        missing_in_display = full_cols - display_cols
        extra_in_display = display_cols - full_cols
        if missing_in_display:
            print(f"   展示数据缺少: {missing_in_display}")
        if extra_in_display:
            print(f"   展示数据多出: {extra_in_display}")

print("\n" + "="*80)
print("✅ 验证完成")
print("="*80)
