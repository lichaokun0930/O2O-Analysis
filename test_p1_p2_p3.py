"""
P1/P2/P3 综合测试脚本
验证所有功能模块是否正常工作
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_p1_batch_import():
    """测试P1: 批量导入功能"""
    print("\n" + "="*60)
    print("测试 P1: 批量数据导入功能")
    print("="*60)
    
    try:
        from database.batch_import import BatchDataImporter
        
        # 创建导入器（不实际执行导入）
        importer = BatchDataImporter("实际数据")
        
        # 查找文件
        files = importer.find_excel_files()
        
        print(f"✅ 模块导入成功")
        print(f"   发现 {len(files)} 个Excel文件")
        
        if files:
            print(f"   示例文件:")
            for f in files[:3]:
                print(f"     - {Path(f).name}")
        
        return True
        
    except Exception as e:
        print(f"❌ P1测试失败: {str(e)}")
        return False


def test_p2_data_source_manager():
    """测试P2: 数据源管理器"""
    print("\n" + "="*60)
    print("测试 P2: 数据源管理器")
    print("="*60)
    
    try:
        from database.data_source_manager import DataSourceManager
        
        manager = DataSourceManager()
        
        # 测试数据库加载
        print("1. 测试数据库加载...")
        df_db = manager.load_from_database()
        print(f"   ✅ 数据库数据: {len(df_db):,} 行")
        
        # 测试统计功能
        print("2. 测试数据库统计...")
        stats = manager.get_database_stats()
        print(f"   ✅ 商品: {stats.get('products', 0):,}")
        print(f"   ✅ 订单: {stats.get('orders', 0):,}")
        print(f"   ✅ 门店: {stats.get('stores', 0):,}")
        
        # 测试门店列表
        print("3. 测试门店列表...")
        stores = manager.get_available_stores()
        print(f"   ✅ 可用门店: {len(stores)}")
        for store in stores[:3]:
            print(f"      - {store}")
        
        # 测试日期范围
        print("4. 测试日期范围...")
        date_range = manager.get_date_range()
        if date_range[0]:
            print(f"   ✅ 日期: {date_range[0]} ~ {date_range[1]}")
        
        return True
        
    except Exception as e:
        print(f"❌ P2测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_p3_api_integration():
    """测试P3: API集成"""
    print("\n" + "="*60)
    print("测试 P3: 前后端API集成")
    print("="*60)
    
    try:
        import requests
        
        api_base = "http://localhost:8000"
        
        # 测试健康检查
        print("1. 测试健康检查...")
        response = requests.get(f"{api_base}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 后端状态: {data.get('status')}")
            print(f"   ✅ 数据库: {data.get('database')}")
        else:
            print(f"   ❌ 健康检查失败: HTTP {response.status_code}")
            return False
        
        # 测试统计API
        print("2. 测试统计API...")
        response = requests.get(f"{api_base}/api/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            products = stats.get('products', {}).get('total', 0)
            orders = stats.get('orders', {}).get('total', 0)
            print(f"   ✅ 商品: {products:,}")
            print(f"   ✅ 订单: {orders:,}")
        
        # 测试订单API
        print("3. 测试订单API...")
        response = requests.get(f"{api_base}/api/orders?limit=5", timeout=5)
        if response.status_code == 200:
            orders = response.json()
            print(f"   ✅ 返回订单数: {len(orders)}")
        
        # 测试商品API
        print("4. 测试商品API...")
        response = requests.get(f"{api_base}/api/products?limit=5", timeout=5)
        if response.status_code == 200:
            products = response.json()
            print(f"   ✅ 返回商品数: {len(products)}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("   ⚠️  后端服务未启动")
        print("   提示: 运行 python -m uvicorn backend.main:app --port 8000")
        return False
        
    except Exception as e:
        print(f"❌ P3测试失败: {str(e)}")
        return False


def test_database_connection():
    """测试数据库连接"""
    print("\n" + "="*60)
    print("测试 数据库连接")
    print("="*60)
    
    try:
        from database.connection import get_db
        from database.models import Order, Product
        
        db = next(get_db())
        
        # 查询统计
        product_count = db.query(Product).count()
        order_count = db.query(Order).count()
        
        print(f"✅ 数据库连接成功")
        print(f"   商品表: {product_count:,} 条记录")
        print(f"   订单表: {order_count:,} 条记录")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("P1/P2/P3 功能综合测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # 1. 数据库连接测试
    results['数据库连接'] = test_database_connection()
    
    # 2. P1测试
    results['P1-批量导入'] = test_p1_batch_import()
    
    # 3. P2测试
    results['P2-数据源管理'] = test_p2_data_source_manager()
    
    # 4. P3测试
    results['P3-API集成'] = test_p3_api_integration()
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:20s} {status}")
    
    # 总体评估
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！P1/P2/P3功能正常")
    elif passed >= total * 0.75:
        print("\n⚠️  大部分测试通过，但有些功能需要检查")
    else:
        print("\n❌ 多项测试失败，请检查系统配置")
    
    print("\n" + "="*60)
    print("详细说明:")
    print("  - P1: 批量导入工具准备就绪")
    print("  - P2: 数据源管理器可正常使用")
    print("  - P3: 需要后端服务运行才能测试")
    print("="*60)


if __name__ == "__main__":
    main()
