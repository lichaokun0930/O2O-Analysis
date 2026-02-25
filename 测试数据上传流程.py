# -*- coding: utf-8 -*-
"""
数据上传流程完整测试

测试内容：
1. 单门店上传逻辑
2. 多门店聚合表上传逻辑
3. 上传后系统抓取逻辑（门店列表、数据查询）
4. 删除门店后的清理逻辑

使用方式：
    python 测试数据上传流程.py
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text, func
from database.connection import SessionLocal, init_database
from database.models import Order

# 测试数据配置
TEST_STORES = ["测试门店A", "测试门店B", "测试门店C"]
TEST_PRODUCTS = ["测试商品1", "测试商品2", "测试商品3"]


def create_test_data(stores: list, rows_per_store: int = 100) -> pd.DataFrame:
    """创建测试数据"""
    data = []
    base_date = datetime.now() - timedelta(days=30)
    
    for store in stores:
        for i in range(rows_per_store):
            order_id = f"TEST_{store}_{i:05d}"
            data.append({
                '订单ID': order_id,
                '订单编号': f"ORD{order_id}",
                '门店名称': store,
                '商品名称': np.random.choice(TEST_PRODUCTS),
                '下单时间': base_date + timedelta(days=np.random.randint(0, 30)),
                '商品实售价': round(np.random.uniform(10, 100), 2),
                '商品原价': round(np.random.uniform(15, 120), 2),
                '销量': np.random.randint(1, 10),
                '一级分类名': '测试分类',
                '渠道': '美团',
            })
    
    return pd.DataFrame(data)


def save_test_excel(df: pd.DataFrame, filename: str) -> str:
    """保存测试数据到临时Excel文件"""
    temp_dir = tempfile.mkdtemp()
    filepath = os.path.join(temp_dir, filename)
    df.to_excel(filepath, index=False)
    return filepath


def cleanup_test_data():
    """清理测试数据"""
    session = SessionLocal()
    try:
        for store in TEST_STORES:
            deleted = session.query(Order).filter(Order.store_name == store).delete()
            if deleted > 0:
                print(f"   🗑️ 清理 {store}: {deleted} 条")
        session.commit()
    finally:
        session.close()


def test_1_single_store_upload():
    """测试1: 单门店上传"""
    print("\n" + "="*60)
    print("📋 测试1: 单门店上传")
    print("="*60)
    
    try:
        # 创建单门店测试数据
        df = create_test_data([TEST_STORES[0]], rows_per_store=50)
        print(f"   📊 创建测试数据: {len(df)} 行, 门店: {TEST_STORES[0]}")
        
        # 保存到临时文件
        filepath = save_test_excel(df, "单门店测试.xlsx")
        print(f"   📁 保存到: {filepath}")
        
        # 使用批量导入器导入
        from database.batch_import_enhanced import BatchDataImporterEnhanced
        importer = BatchDataImporterEnhanced(
            data_dir=os.path.dirname(filepath),
            mode="replace"
        )
        
        # 导入单个文件
        success = importer.import_file(filepath)
        
        if not success:
            print("   ❌ 导入失败")
            return False
        
        # 验证数据库
        session = SessionLocal()
        try:
            count = session.query(Order).filter(Order.store_name == TEST_STORES[0]).count()
            print(f"   📊 数据库验证: {count} 条")
            
            if count > 0:
                print("   ✅ 测试1通过: 单门店上传成功")
                return True
            else:
                print("   ❌ 测试1失败: 数据未导入")
                return False
        finally:
            session.close()
            
    except Exception as e:
        print(f"   ❌ 测试1异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_2_multi_store_upload():
    """测试2: 多门店聚合表上传"""
    print("\n" + "="*60)
    print("📋 测试2: 多门店聚合表上传")
    print("="*60)
    
    try:
        # 创建多门店测试数据
        df = create_test_data(TEST_STORES, rows_per_store=30)
        print(f"   📊 创建测试数据: {len(df)} 行, 门店: {len(TEST_STORES)} 个")
        
        # 检查门店分布
        store_counts = df['门店名称'].value_counts()
        print(f"   📊 门店分布:")
        for store, count in store_counts.items():
            print(f"      • {store}: {count} 条")
        
        # 保存到临时文件
        filepath = save_test_excel(df, "多门店聚合测试.xlsx")
        print(f"   📁 保存到: {filepath}")
        
        # 使用批量导入器导入
        from database.batch_import_enhanced import BatchDataImporterEnhanced
        importer = BatchDataImporterEnhanced(
            data_dir=os.path.dirname(filepath),
            mode="replace"
        )
        
        # 导入单个文件
        success = importer.import_file(filepath)
        
        if not success:
            print("   ❌ 导入失败")
            return False
        
        # 验证数据库
        session = SessionLocal()
        try:
            print(f"   📊 数据库验证:")
            all_ok = True
            for store in TEST_STORES:
                count = session.query(Order).filter(Order.store_name == store).count()
                status = "✅" if count > 0 else "❌"
                print(f"      {status} {store}: {count} 条")
                if count == 0:
                    all_ok = False
            
            if all_ok:
                print("   ✅ 测试2通过: 多门店聚合表上传成功")
                return True
            else:
                print("   ❌ 测试2失败: 部分门店数据未导入")
                return False
        finally:
            session.close()
            
    except Exception as e:
        print(f"   ❌ 测试2异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_3_store_list_query():
    """测试3: 门店列表查询"""
    print("\n" + "="*60)
    print("📋 测试3: 门店列表查询")
    print("="*60)
    
    try:
        session = SessionLocal()
        try:
            # 查询门店列表
            stores = session.query(Order.store_name).distinct().all()
            store_list = [s[0] for s in stores if s[0]]
            
            print(f"   📊 查询到 {len(store_list)} 个门店:")
            for store in store_list:
                count = session.query(Order).filter(Order.store_name == store).count()
                print(f"      • {store}: {count} 条")
            
            # 验证测试门店是否都在列表中
            test_stores_found = [s for s in TEST_STORES if s in store_list]
            
            if len(test_stores_found) == len(TEST_STORES):
                print("   ✅ 测试3通过: 所有测试门店都能查询到")
                return True
            else:
                print(f"   ❌ 测试3失败: 只找到 {len(test_stores_found)}/{len(TEST_STORES)} 个测试门店")
                return False
        finally:
            session.close()
            
    except Exception as e:
        print(f"   ❌ 测试3异常: {e}")
        return False


def test_4_data_query_by_store():
    """测试4: 按门店查询数据"""
    print("\n" + "="*60)
    print("📋 测试4: 按门店查询数据")
    print("="*60)
    
    try:
        session = SessionLocal()
        try:
            all_ok = True
            
            for store in TEST_STORES:
                # 查询门店数据
                orders = session.query(Order).filter(Order.store_name == store).limit(5).all()
                
                if orders:
                    print(f"   ✅ {store}: 查询成功, 示例订单ID: {orders[0].order_id}")
                else:
                    print(f"   ❌ {store}: 查询失败, 无数据")
                    all_ok = False
            
            if all_ok:
                print("   ✅ 测试4通过: 按门店查询数据正常")
                return True
            else:
                print("   ❌ 测试4失败: 部分门店查询失败")
                return False
        finally:
            session.close()
            
    except Exception as e:
        print(f"   ❌ 测试4异常: {e}")
        return False


def test_5_delete_store():
    """测试5: 删除门店数据"""
    print("\n" + "="*60)
    print("📋 测试5: 删除门店数据")
    print("="*60)
    
    try:
        from database.data_lifecycle_manager import DataLifecycleManager
        
        manager = DataLifecycleManager()
        
        # 删除第一个测试门店
        store_to_delete = TEST_STORES[0]
        print(f"   🗑️ 删除门店: {store_to_delete}")
        
        result = manager.clean_store_data(store_to_delete, dry_run=False, auto_confirm=True)
        manager.close()
        
        deleted = result.get('deleted', 0)
        print(f"   📊 删除结果: {deleted} 条")
        
        # 验证删除
        session = SessionLocal()
        try:
            remaining = session.query(Order).filter(Order.store_name == store_to_delete).count()
            
            if remaining == 0:
                print(f"   ✅ 测试5通过: 门店数据已彻底删除")
                return True
            else:
                print(f"   ❌ 测试5失败: 还有 {remaining} 条数据残留")
                return False
        finally:
            session.close()
            
    except Exception as e:
        print(f"   ❌ 测试5异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_6_replace_mode():
    """测试6: 替换模式（重复上传）"""
    print("\n" + "="*60)
    print("📋 测试6: 替换模式（重复上传）")
    print("="*60)
    
    try:
        # 先上传一批数据
        df1 = create_test_data([TEST_STORES[1]], rows_per_store=50)
        filepath1 = save_test_excel(df1, "替换测试_第一次.xlsx")
        
        from database.batch_import_enhanced import BatchDataImporterEnhanced
        importer1 = BatchDataImporterEnhanced(
            data_dir=os.path.dirname(filepath1),
            mode="replace"
        )
        importer1.import_file(filepath1)
        
        # 查询第一次上传后的数量
        session = SessionLocal()
        count1 = session.query(Order).filter(Order.store_name == TEST_STORES[1]).count()
        print(f"   📊 第一次上传后: {count1} 条")
        session.close()
        
        # 再上传一批不同数量的数据（替换模式）
        df2 = create_test_data([TEST_STORES[1]], rows_per_store=30)
        filepath2 = save_test_excel(df2, "替换测试_第二次.xlsx")
        
        importer2 = BatchDataImporterEnhanced(
            data_dir=os.path.dirname(filepath2),
            mode="replace"
        )
        importer2.import_file(filepath2)
        
        # 查询第二次上传后的数量
        session = SessionLocal()
        count2 = session.query(Order).filter(Order.store_name == TEST_STORES[1]).count()
        print(f"   📊 第二次上传后: {count2} 条")
        session.close()
        
        # 验证：第二次应该是30条左右，而不是50+30=80条
        if count2 < count1:
            print(f"   ✅ 测试6通过: 替换模式正常工作 ({count1} → {count2})")
            return True
        else:
            print(f"   ❌ 测试6失败: 替换模式未生效，数据累加了")
            return False
            
    except Exception as e:
        print(f"   ❌ 测试6异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("🧪 数据上传流程完整测试")
    print("="*60)
    
    # 初始化数据库
    init_database()
    
    # 先清理测试数据
    print("\n🧹 清理旧测试数据...")
    cleanup_test_data()
    
    # 运行测试
    results = {}
    
    results['test_1'] = test_1_single_store_upload()
    results['test_2'] = test_2_multi_store_upload()
    results['test_3'] = test_3_store_list_query()
    results['test_4'] = test_4_data_query_by_store()
    results['test_5'] = test_5_delete_store()
    results['test_6'] = test_6_replace_mode()
    
    # 清理测试数据
    print("\n🧹 清理测试数据...")
    cleanup_test_data()
    
    # 汇总结果
    print("\n" + "="*60)
    print("📋 测试结果汇总")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查上述错误")
        return 1


if __name__ == "__main__":
    exit(main())
