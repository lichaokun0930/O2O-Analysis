"""
清空数据库中的旧数据，强制重新计算
"""

import sys
sys.path.insert(0, r'd:\Python1\O2O_Analysis\O2O数据分析\测算模型')

try:
    from database.data_source_manager import DataSourceManager
    
    manager = DataSourceManager()
    
    print("=" * 80)
    print("数据库清理工具")
    print("=" * 80)
    
    # 获取所有门店
    stores = manager.get_all_stores()
    print(f"\n当前数据库中的门店:")
    for i, store in enumerate(stores, 1):
        print(f"  {i}. {store['store_name']} - 数据量: {store['record_count']}行")
    
    print("\n" + "="*80)
    print("⚠️  警告：如果要使用新的利润公式，请:")
    print("   1. 直接使用'文件上传'Tab重新上传Excel")
    print("   2. 或者在下方输入门店名称来删除旧数据")
    print("="*80)
    
    # 可选：删除特定门店数据
    # store_to_delete = "惠宜选-六安市金寨店"
    # manager.delete_store_data(store_to_delete)
    # print(f"✅ 已删除 {store_to_delete} 的数据库记录")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
