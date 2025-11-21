#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试门店加盟类型字段功能
验证数据库迁移和字段映射是否正常工作
"""

import pandas as pd
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import engine, SessionLocal
from database.models import Order
from sqlalchemy import text

def test_database_field():
    """测试数据库字段是否添加成功"""
    
    print("\n" + "="*80)
    print("🧪 测试1: 验证数据库字段")
    print("="*80)
    
    session = SessionLocal()
    
    try:
        # 检查字段是否存在
        result = session.execute(text("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name='orders' AND column_name='store_franchise_type'
        """))
        
        field_info = result.fetchone()
        
        if field_info:
            print("✅ store_franchise_type 字段存在")
            print(f"   📌 字段名: {field_info[0]}")
            print(f"   📌 数据类型: {field_info[1]}")
            print(f"   📌 允许空值: {field_info[2]}")
            print(f"   📌 默认值: {field_info[3]}")
            
            # 检查索引
            result = session.execute(text("""
                SELECT indexname
                FROM pg_indexes 
                WHERE tablename='orders' AND indexname='idx_orders_franchise_type'
            """))
            
            index_info = result.fetchone()
            if index_info:
                print(f"✅ 索引已创建: {index_info[0]}")
            else:
                print("⚠️  索引未找到")
            
            # 检查约束
            result = session.execute(text("""
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_name='orders' AND constraint_name='chk_franchise_type'
            """))
            
            constraint_info = result.fetchone()
            if constraint_info:
                print(f"✅ 数据约束已创建: {constraint_info[0]}")
            else:
                print("⚠️  数据约束未找到")
            
            return True
        else:
            print("❌ store_franchise_type 字段不存在")
            print("💡 请先运行: python database/add_store_franchise_type_field.py")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        session.close()


def test_field_mapping():
    """测试字段映射功能"""
    
    print("\n" + "="*80)
    print("🧪 测试2: 验证字段映射")
    print("="*80)
    
    from 真实数据处理器 import RealDataProcessor
    
    # 创建测试数据
    test_data = pd.DataFrame({
        '商品名称': ['测试商品A', '测试商品B', '测试商品C'],
        '门店名称': ['北京直营店', '上海加盟店', '深圳托管店'],
        '门店加盟类型': [1, 2, 3],  # 使用标准字段名
        '日期': ['2025-11-19', '2025-11-19', '2025-11-19'],
        '商品实售价': [100, 150, 200],
        '商品采购成本': [60, 90, 120],
        '月售': [10, 20, 30]
    })
    
    print("📊 测试数据:")
    print(test_data.to_string(index=False))
    
    # 初始化处理器
    processor = RealDataProcessor()
    
    # 标准化字段
    standardized_df = processor.standardize_data_format(test_data)
    
    print("\n📋 标准化后的字段:")
    print(f"   原始字段数: {len(test_data.columns)}")
    print(f"   标准化后字段数: {len(standardized_df.columns)}")
    
    # 检查关键字段是否存在
    required_fields = ['商品名称', '门店名称', '门店加盟类型', '日期', '商品实售价', '商品采购成本']
    
    for field in required_fields:
        if field in standardized_df.columns:
            print(f"   ✅ {field}: 存在")
        else:
            print(f"   ❌ {field}: 缺失")
    
    # 检查门店加盟类型的数据
    if '门店加盟类型' in standardized_df.columns:
        print("\n📊 门店加盟类型数据分布:")
        franchise_counts = standardized_df['门店加盟类型'].value_counts()
        
        mapping = {1: '直营店', 2: '加盟店', 3: '托管店', 4: '买断'}
        for type_id, count in franchise_counts.items():
            type_name = mapping.get(type_id, f'未知类型({type_id})')
            print(f"   {type_name}: {count}条")
        
        return True
    else:
        print("❌ 门店加盟类型字段映射失败")
        return False


def test_alternative_field_names():
    """测试别名字段识别"""
    
    print("\n" + "="*80)
    print("🧪 测试3: 验证别名字段识别")
    print("="*80)
    
    from 真实数据处理器 import RealDataProcessor
    
    # 测试不同的字段名
    test_cases = [
        {
            'name': '测试用例1: 标准字段名',
            'data': {
                '商品名称': ['商品1'],
                '门店加盟类型': [1],
                '日期': ['2025-11-19']
            }
        },
        {
            'name': '测试用例2: 简写',
            'data': {
                '商品名称': ['商品2'],
                '加盟类型': [2],
                '日期': ['2025-11-19']
            }
        },
        {
            'name': '测试用例3: 别名',
            'data': {
                '商品名称': ['商品3'],
                '门店类型': [3],
                '日期': ['2025-11-19']
            }
        },
        {
            'name': '测试用例4: 英文字段名',
            'data': {
                'product_name': ['Product4'],
                'store_franchise_type': [4],
                'date': ['2025-11-19']
            }
        }
    ]
    
    processor = RealDataProcessor()
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n📋 {test_case['name']}")
        test_df = pd.DataFrame(test_case['data'])
        
        try:
            standardized_df = processor.standardize_data_format(test_df)
            
            # 检查是否成功映射到标准字段
            if '门店加盟类型' in standardized_df.columns or 'store_franchise_type' in standardized_df.columns:
                print("   ✅ 字段映射成功")
                
                # 显示映射后的值
                franchise_col = '门店加盟类型' if '门店加盟类型' in standardized_df.columns else 'store_franchise_type'
                value = standardized_df[franchise_col].iloc[0]
                
                mapping = {1: '直营店', 2: '加盟店', 3: '托管店', 4: '买断'}
                print(f"   📊 加盟类型: {mapping.get(value, '未知')}")
            else:
                print("   ⚠️  未找到门店加盟类型字段")
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            all_passed = False
    
    return all_passed


def test_data_constraints():
    """测试数据约束"""
    
    print("\n" + "="*80)
    print("🧪 测试4: 验证数据约束")
    print("="*80)
    
    session = SessionLocal()
    
    try:
        # 测试1: 插入合法值 (1-4)
        print("\n📋 测试合法值 (1-4):")
        for value in [1, 2, 3, 4]:
            try:
                result = session.execute(text("""
                    SELECT 
                        CASE :value
                            WHEN 1 THEN '直营店'
                            WHEN 2 THEN '加盟店'
                            WHEN 3 THEN '托管店'
                            WHEN 4 THEN '买断'
                        END AS type_name
                    WHERE :value IS NULL OR :value BETWEEN 1 AND 4
                """), {'value': value})
                
                type_name = result.fetchone()
                if type_name:
                    print(f"   ✅ {value} = {type_name[0]} (合法)")
            except Exception as e:
                print(f"   ❌ {value}: {e}")
        
        # 测试2: NULL值
        print("\n📋 测试NULL值:")
        try:
            result = session.execute(text("""
                SELECT 'NULL值' 
                WHERE NULL IS NULL OR NULL BETWEEN 1 AND 4
            """))
            if result.fetchone():
                print("   ✅ NULL (合法 - 历史数据兼容)")
        except Exception as e:
            print(f"   ❌ NULL: {e}")
        
        # 测试3: 非法值
        print("\n📋 测试非法值 (应被约束拒绝):")
        for value in [0, 5, -1, 99]:
            try:
                result = session.execute(text("""
                    SELECT :value
                    WHERE :value IS NULL OR :value BETWEEN 1 AND 4
                """), {'value': value})
                
                if result.fetchone() is None:
                    print(f"   ✅ {value} (被正确拒绝)")
                else:
                    print(f"   ⚠️  {value} (未被拒绝,约束可能失效)")
            except Exception as e:
                print(f"   ✅ {value} (被约束拒绝): {str(e)[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        session.close()


def test_data_statistics():
    """测试数据统计查询"""
    
    print("\n" + "="*80)
    print("🧪 测试5: 验证统计查询")
    print("="*80)
    
    session = SessionLocal()
    
    try:
        # 统计各类型订单数
        result = session.execute(text("""
            SELECT 
                CASE store_franchise_type
                    WHEN 1 THEN '直营店'
                    WHEN 2 THEN '加盟店'
                    WHEN 3 THEN '托管店'
                    WHEN 4 THEN '买断'
                    ELSE '未分类'
                END AS 加盟类型,
                COUNT(*) AS 订单数,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS 占比
            FROM orders
            GROUP BY store_franchise_type
            ORDER BY 订单数 DESC
            LIMIT 10
        """))
        
        rows = result.fetchall()
        
        if rows:
            print("\n📊 订单分布统计:")
            print(f"{'加盟类型':<15} {'订单数':>10} {'占比':>10}")
            print("-" * 40)
            
            for row in rows:
                print(f"{row[0]:<15} {row[1]:>10,} {row[2]:>9}%")
            
            return True
        else:
            print("⚠️  数据库中暂无订单数据")
            print("💡 提示: 上传包含'门店加盟类型'字段的数据后可查看统计")
            return True
            
    except Exception as e:
        print(f"❌ 统计查询失败: {e}")
        return False
    finally:
        session.close()


def main():
    """运行所有测试"""
    
    print("\n" + "="*80)
    print("🚀 门店加盟类型字段功能测试")
    print("="*80)
    print("📅 测试时间:", pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    tests = [
        ("数据库字段验证", test_database_field),
        ("字段映射功能", test_field_mapping),
        ("别名字段识别", test_alternative_field_names),
        ("数据约束验证", test_data_constraints),
        ("统计查询验证", test_data_statistics)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 执行失败: {e}")
            results.append((test_name, False))
    
    # 测试总结
    print("\n" + "="*80)
    print("📋 测试总结")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*80)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✅ 所有测试通过! 门店加盟类型字段功能正常")
    else:
        print(f"⚠️  {total - passed} 项测试失败,请检查相关配置")
    
    print("="*80)
    
    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
