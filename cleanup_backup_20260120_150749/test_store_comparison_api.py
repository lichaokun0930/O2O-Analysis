#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试全量门店对比API
"""

import requests
import json
from datetime import date, timedelta

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def test_store_comparison():
    """测试门店对比API"""
    print("=" * 60)
    print("测试全量门店对比API")
    print("=" * 60)
    
    # 1. 测试获取门店对比数据
    print("\n1. 测试 GET /stores/comparison")
    print("-" * 60)
    
    # 计算日期范围（最近7天）
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
    
    params = {
        'start_date': str(start_date),
        'end_date': str(end_date),
        'sort_by': 'revenue',
        'sort_order': 'desc'
    }
    
    print(f"请求参数: {json.dumps(params, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.get(f"{BASE_URL}/stores/comparison", params=params)
        print(f"\n状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n响应数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get('success'):
                stores = data.get('data', {}).get('stores', [])
                print(f"\n✅ 成功获取 {len(stores)} 个门店数据")
                
                if stores:
                    print(f"\n前3个门店:")
                    for i, store in enumerate(stores[:3], 1):
                        print(f"  {i}. {store.get('store_name')}: "
                              f"订单{store.get('order_count')}单, "
                              f"销售额¥{store.get('total_revenue'):.2f}")
                else:
                    print("\n⚠️ 没有门店数据")
            else:
                print(f"\n❌ API返回失败: {data.get('message')}")
        else:
            print(f"\n❌ 请求失败: {response.text}")
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
    
    # 2. 测试数据库中是否有数据
    print("\n\n2. 检查数据库中的门店数据")
    print("-" * 60)
    
    try:
        # 直接查询数据库
        import sys
        from pathlib import Path
        
        # 添加项目路径
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        from database.connection import SessionLocal
        from database.models import Order
        
        session = SessionLocal()
        
        # 查询门店列表
        stores = session.query(Order.store_name).distinct().all()
        print(f"数据库中的门店数量: {len(stores)}")
        
        if stores:
            print(f"\n门店列表:")
            for i, (store_name,) in enumerate(stores[:10], 1):
                # 查询该门店的订单数
                count = session.query(Order).filter(Order.store_name == store_name).count()
                print(f"  {i}. {store_name}: {count} 条订单")
            
            if len(stores) > 10:
                print(f"  ... 还有 {len(stores) - 10} 个门店")
        else:
            print("\n⚠️ 数据库中没有门店数据")
        
        # 查询日期范围
        min_date = session.query(Order.date).order_by(Order.date.asc()).first()
        max_date = session.query(Order.date).order_by(Order.date.desc()).first()
        
        if min_date and max_date:
            print(f"\n数据日期范围: {min_date[0].date()} ~ {max_date[0].date()}")
        
        session.close()
        
    except Exception as e:
        print(f"\n❌ 数据库查询异常: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_store_comparison()
