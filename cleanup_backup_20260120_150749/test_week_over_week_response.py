#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试环比数据API响应结构
验证 aov, avg_delivery_fee, avg_marketing_cost 是否正确返回
"""

import requests
import json
from datetime import date, timedelta

# API配置
BASE_URL = "http://localhost:8080/api/v1/stores"

def test_week_over_week_api():
    """测试环比数据API"""
    print("=" * 80)
    print("测试环比数据API响应结构")
    print("=" * 80)
    
    # 计算日期范围
    end_date = date(2026, 1, 15)  # 数据库最大日期
    current_start = end_date - timedelta(days=6)  # 最近7天
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=6)
    
    print(f"\n📅 本期: {current_start} ~ {end_date}")
    print(f"📅 上期: {previous_start} ~ {previous_end}")
    
    # 调用API
    url = f"{BASE_URL}/comparison/week-over-week"
    params = {
        "end_date": str(end_date),
        "previous_start": str(previous_start),
        "previous_end": str(previous_end)
    }
    
    print(f"\n🔍 请求URL: {url}")
    print(f"🔍 请求参数: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("success"):
            print(f"\n❌ API返回失败: {data}")
            return
        
        stores = data.get("data", {}).get("stores", [])
        
        if not stores:
            print("\n⚠️ 没有返回门店数据")
            return
        
        print(f"\n✅ 返回 {len(stores)} 个门店的环比数据")
        
        # 检查第一个门店的数据结构
        first_store = stores[0]
        print(f"\n📊 第一个门店: {first_store['store_name']}")
        print("\n当前值 (current):")
        print(json.dumps(first_store.get("current", {}), indent=2, ensure_ascii=False))
        
        print("\n环比变化 (changes):")
        changes = first_store.get("changes", {})
        print(json.dumps(changes, indent=2, ensure_ascii=False))
        
        # 验证关键字段
        print("\n🔍 验证关键字段:")
        required_fields = [
            "order_count", "revenue", "profit", "profit_margin",
            "aov", "avg_delivery_fee", "avg_marketing_cost",
            "delivery_cost_rate", "marketing_cost_rate"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field in changes:
                print(f"  ✅ {field}: {changes[field]}")
            else:
                print(f"  ❌ {field}: 缺失")
                missing_fields.append(field)
        
        if missing_fields:
            print(f"\n❌ 缺失字段: {missing_fields}")
        else:
            print(f"\n✅ 所有字段都存在！")
        
        # 检查所有门店
        print(f"\n📊 检查所有 {len(stores)} 个门店...")
        all_have_fields = True
        for store in stores:
            changes = store.get("changes", {})
            for field in ["aov", "avg_delivery_fee", "avg_marketing_cost"]:
                if field not in changes:
                    print(f"  ⚠️ {store['store_name']} 缺少 {field}")
                    all_have_fields = False
        
        if all_have_fields:
            print("  ✅ 所有门店都包含 aov, avg_delivery_fee, avg_marketing_cost")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务器")
        print("   请确保后端服务器正在运行: python backend/main.py")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_week_over_week_api()
