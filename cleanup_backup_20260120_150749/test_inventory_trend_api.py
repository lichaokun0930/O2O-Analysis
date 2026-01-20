# -*- coding: utf-8 -*-
"""
测试库存风险趋势API和品类效益矩阵API
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_apis():
    """测试相关API"""
    
    # 1. 先获取可用的门店列表
    print("=" * 60)
    print("1. 获取门店列表...")
    try:
        res = requests.get(f"{BASE_URL}/orders/stores")
        stores = res.json()
        print(f"   可用门店: {stores}")
        store_name = stores[0] if stores else None
    except Exception as e:
        print(f"   获取门店失败: {e}")
        store_name = None
    
    # 2. 测试品类效益矩阵API（不带门店参数）
    print("\n" + "=" * 60)
    print("2. 测试品类效益矩阵API（不带门店参数）...")
    
    try:
        res = requests.get(f"{BASE_URL}/category-matrix/with-risk")
        data = res.json()
        print(f"   响应状态: {res.status_code}")
        print(f"   success: {data.get('success')}")
        print(f"   数据条数: {len(data.get('data', []))}")
        print(f"   level: {data.get('level')}")
        if data.get('data') and len(data['data']) > 0:
            print(f"   第一条数据:")
            print(json.dumps(data['data'][0], ensure_ascii=False, indent=4))
        if data.get('error'):
            print(f"   错误: {data.get('error')}")
    except Exception as e:
        print(f"   请求失败: {e}")
    
    # 3. 测试品类效益矩阵API（带门店参数）
    if store_name:
        print("\n" + "=" * 60)
        print(f"3. 测试品类效益矩阵API（门店: {store_name}）...")
        
        try:
            res = requests.get(f"{BASE_URL}/category-matrix/with-risk", params={'store_name': store_name})
            data = res.json()
            print(f"   响应状态: {res.status_code}")
            print(f"   success: {data.get('success')}")
            print(f"   数据条数: {len(data.get('data', []))}")
            if data.get('data') and len(data['data']) > 0:
                print(f"   第一条数据:")
                print(json.dumps(data['data'][0], ensure_ascii=False, indent=4))
                # 检查revenue是否为0
                total_revenue = sum(item.get('revenue', 0) for item in data['data'])
                print(f"\n   总revenue: {total_revenue}")
                if total_revenue == 0:
                    print("   ⚠️ 警告: 所有品类的revenue都是0！")
        except Exception as e:
            print(f"   请求失败: {e}")
    
    # 4. 测试库存风险趋势API
    print("\n" + "=" * 60)
    print("4. 测试库存风险趋势API...")
    
    params = {'store_name': store_name} if store_name else {}
    try:
        res = requests.get(f"{BASE_URL}/inventory-risk/trend", params=params)
        data = res.json()
        print(f"   响应状态: {res.status_code}")
        print(f"   success: {data.get('success')}")
        print(f"   数据条数: {len(data.get('data', []))}")
        print(f"   message: {data.get('message')}")
        if data.get('data') and len(data['data']) > 0:
            print(f"   第一条: {data['data'][0]}")
            print(f"   最后一条: {data['data'][-1]}")
    except Exception as e:
        print(f"   请求失败: {e}")

if __name__ == "__main__":
    test_apis()
