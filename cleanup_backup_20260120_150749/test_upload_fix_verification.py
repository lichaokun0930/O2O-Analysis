# -*- coding: utf-8 -*-
"""
验证数据上传BUG修复
测试配送距离字段是否正确映射
"""
import pandas as pd
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_excel_fields():
    """测试Excel文件中的字段"""
    print("=" * 60)
    print("测试1: 验证Excel文件字段")
    print("=" * 60)
    
    file_path = PROJECT_ROOT / '实际数据' / '2025-12-13 00_00_00至2026-01-11 23_59_59订单明细数据导出汇总.xlsx'
    df = pd.read_excel(file_path, nrows=10)
    
    # 检查关键字段
    key_fields = ['配送距离', '配送平台', '门店ID', '城市名称', '打包袋金额', '剩余库存']
    
    print("\n关键字段检查:")
    for field in key_fields:
        if field in df.columns:
            sample = df[field].head(3).tolist()
            print(f"  ✅ {field}: {sample}")
        else:
            print(f"  ❌ {field}: 字段不存在")
    
    return True


def test_store_distance_data():
    """测试厉臣便利的配送距离数据"""
    print("\n" + "=" * 60)
    print("测试2: 厉臣便利（镇江平昌路店）配送距离数据")
    print("=" * 60)
    
    file_path = PROJECT_ROOT / '实际数据' / '2025-12-13 00_00_00至2026-01-11 23_59_59订单明细数据导出汇总.xlsx'
    df = pd.read_excel(file_path)
    
    store_df = df[df['门店名称'] == '厉臣便利（镇江平昌路店）']
    
    print(f"\n总行数: {len(store_df):,}")
    print(f"唯一订单数: {store_df['订单ID'].nunique():,}")
    print(f"\n配送距离统计:")
    print(f"  - 配送距离>0的行数: {(store_df['配送距离'] > 0).sum():,}")
    print(f"  - 配送距离=0的行数: {(store_df['配送距离'] == 0).sum():,}")
    print(f"  - 配送距离为空的行数: {store_df['配送距离'].isna().sum():,}")
    
    # 配送距离分布
    print(f"\n配送距离分布（米）:")
    distance_stats = store_df['配送距离'].describe()
    print(f"  - 最小值: {distance_stats['min']:.0f}")
    print(f"  - 最大值: {distance_stats['max']:.0f}")
    print(f"  - 平均值: {distance_stats['mean']:.0f}")
    print(f"  - 中位数: {distance_stats['50%']:.0f}")
    
    return True


def test_database_current_state():
    """测试数据库当前状态"""
    print("\n" + "=" * 60)
    print("测试3: 数据库当前状态（修复前）")
    print("=" * 60)
    
    try:
        from database.connection import SessionLocal
        from database.models import Order
        from sqlalchemy import func
        
        session = SessionLocal()
        
        # 厉臣便利的配送距离统计
        store_name = '厉臣便利（镇江平昌路店）'
        
        total = session.query(func.count(Order.id)).filter(
            Order.store_name == store_name
        ).scalar()
        
        non_zero_distance = session.query(func.count(Order.id)).filter(
            Order.store_name == store_name,
            Order.delivery_distance > 0
        ).scalar()
        
        zero_distance = session.query(func.count(Order.id)).filter(
            Order.store_name == store_name,
            Order.delivery_distance == 0
        ).scalar()
        
        print(f"\n{store_name}:")
        print(f"  - 总记录数: {total:,}")
        print(f"  - 配送距离>0: {non_zero_distance:,}")
        print(f"  - 配送距离=0: {zero_distance:,}")
        
        if non_zero_distance == 0:
            print(f"\n⚠️  警告: 数据库中该门店所有订单的配送距离都是0！")
            print(f"   这证实了上传逻辑BUG - 配送距离字段未被正确导入")
            print(f"\n✅ 修复方案: 已在 data_management.py 中添加 delivery_distance 字段映射")
            print(f"   请重新上传数据以修复此问题")
        else:
            print(f"\n✅ 数据库中已有配送距离数据")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"\n❌ 数据库连接失败: {e}")
        return False


def test_upload_logic_fields():
    """测试上传逻辑中的字段映射"""
    print("\n" + "=" * 60)
    print("测试4: 验证上传逻辑字段映射")
    print("=" * 60)
    
    upload_file = PROJECT_ROOT / 'backend' / 'app' / 'api' / 'v1' / 'data_management.py'
    
    with open(upload_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键字段是否在上传逻辑中
    key_mappings = [
        ("delivery_distance", "配送距离"),
        ("delivery_platform", "配送平台"),
        ("store_id", "门店ID"),
        ("city", "城市名称"),
        ("packaging_fee", "打包袋金额"),
        ("remaining_stock", "剩余库存"),
        ("address", "收货地址"),
        ("store_franchise_type", "门店加盟类型"),
    ]
    
    print("\n字段映射检查:")
    all_found = True
    for db_field, excel_field in key_mappings:
        if db_field in content and excel_field in content:
            print(f"  ✅ {db_field} <- {excel_field}")
        else:
            print(f"  ❌ {db_field} <- {excel_field} (缺失)")
            all_found = False
    
    if all_found:
        print(f"\n✅ 所有关键字段映射已添加！")
    else:
        print(f"\n⚠️  部分字段映射缺失")
    
    return all_found


if __name__ == "__main__":
    print("=" * 60)
    print("数据上传BUG修复验证")
    print("=" * 60)
    
    test_excel_fields()
    test_store_distance_data()
    test_database_current_state()
    test_upload_logic_fields()
    
    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)
    print("\n下一步操作:")
    print("1. 重启后端服务")
    print("2. 在React前端的数据管理页面重新上传厉臣便利的数据")
    print("3. 验证配送距离数据是否正确导入")
