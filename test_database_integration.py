"""
测试数据库集成功能
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_database_connection():
    """测试数据库连接"""
    print("=== 测试1: 数据库连接 ===")
    try:
        from database.connection import test_connection
        test_connection()
        print("✅ 数据库连接成功\n")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}\n")
        return False


def test_data_source_manager():
    """测试数据源管理器"""
    print("=== 测试2: 数据源管理器 ===")
    try:
        from database.data_source_manager import DataSourceManager
        
        manager = DataSourceManager()
        print("✅ 数据源管理器初始化成功")
        
        # 获取统计信息
        stats = manager.get_database_stats()
        print(f"\n📊 数据库统计:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")
        
        # 获取门店列表
        stores = manager.get_available_stores()
        print(f"\n🏪 可用门店 ({len(stores)}个):")
        for store in stores[:5]:
            print(f"  - {store}")
        if len(stores) > 5:
            print(f"  ... 还有 {len(stores) - 5} 个门店")
        
        print("\n✅ 数据源管理器测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 数据源管理器测试失败: {e}\n")
        return False


def test_load_from_database():
    """测试从数据库加载数据"""
    print("=== 测试3: 从数据库加载数据 ===")
    try:
        from database.data_source_manager import DataSourceManager
        
        manager = DataSourceManager()
        
        # 加载数据
        df = manager.load_from_database()
        
        print(f"✅ 成功加载 {len(df):,} 条数据")
        print(f"📋 字段数: {len(df.columns)}")
        print(f"📅 日期范围: {df['日期'].min()} ~ {df['日期'].max()}")
        
        # 显示前几行
        print("\n📊 数据预览:")
        print(df.head(3).to_string())
        
        print("\n✅ 数据加载测试通过\n")
        return True
        
    except Exception as e:
        print(f"❌ 数据加载测试失败: {e}\n")
        return False


def main():
    """主测试流程"""
    print("=" * 70)
    print("🧪 智能门店看板 - 数据库集成测试")
    print("=" * 70 + "\n")
    
    results = []
    
    # 测试1: 数据库连接
    results.append(("数据库连接", test_database_connection()))
    
    # 如果数据库连接成功，继续后续测试
    if results[0][1]:
        results.append(("数据源管理器", test_data_source_manager()))
        results.append(("数据加载", test_load_from_database()))
    
    # 总结
    print("=" * 70)
    print("📊 测试结果汇总:")
    print("=" * 70)
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！数据库功能可以正常使用。")
    else:
        print("\n⚠️ 部分测试失败，请检查:")
        print("  1. PostgreSQL 是否正在运行？")
        print("  2. .env 文件中的数据库配置是否正确？")
        print("  3. 数据库中是否有数据？")
        print("\n提示: 运行 'python database/batch_import.py' 导入数据")


if __name__ == "__main__":
    main()
