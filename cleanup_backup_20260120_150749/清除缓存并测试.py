# -*- coding: utf-8 -*-
"""
清除所有缓存并测试渠道筛选
"""

import requests

API_BASE = "http://localhost:8080/api/v1"

def clear_all_caches():
    """清除所有缓存"""
    print("="*80)
    print("清除所有缓存")
    print("="*80)
    
    endpoints = [
        "/orders/clear-cache",
        "/stores/comparison/clear-cache"
    ]
    
    for endpoint in endpoints:
        try:
            res = requests.post(f"{API_BASE}{endpoint}", timeout=5)
            data = res.json()
            if data.get('success'):
                print(f"✓ {endpoint}: {data.get('message', '成功')}")
            else:
                print(f"✗ {endpoint}: 失败")
        except Exception as e:
            print(f"✗ {endpoint}: {e}")


def test_channel_filtering():
    """测试渠道筛选"""
    print("\n" + "="*80)
    print("测试渠道筛选（清除缓存后）")
    print("="*80)
    
    test_cases = [
        {"channel": "饿了么", "expected_marketing": 5.58, "expected_delivery": 4.94},
        {"channel": "美团共橙", "expected_marketing": 5.19, "expected_delivery": 4.14},
    ]
    
    for test in test_cases:
        channel = test["channel"]
        params = {
            "end_date": "2026-01-18",
            "previous_start": "2026-01-05",
            "previous_end": "2026-01-11",
            "channel": channel
        }
        
        print(f"\n测试渠道: {channel}")
        print(f"预期: 单均营销 ¥{test['expected_marketing']:.2f}, 单均配送 ¥{test['expected_delivery']:.2f}")
        
        try:
            res = requests.get(
                f"{API_BASE}/stores/comparison/week-over-week",
                params=params,
                timeout=30
            )
            data = res.json()
            
            if data.get('success'):
                stores = data.get('data', {}).get('stores', [])
                
                # 查找泰州泰兴店
                target = None
                for store in stores:
                    if '泰州泰兴' in store.get('store_name', ''):
                        target = store
                        break
                
                if target:
                    current = target['current']
                    actual_marketing = current['avg_marketing_cost']
                    actual_delivery = current['avg_delivery_fee']
                    
                    print(f"实际: 单均营销 ¥{actual_marketing:.2f}, 单均配送 ¥{actual_delivery:.2f}")
                    
                    # 检查是否匹配
                    marketing_match = abs(actual_marketing - test['expected_marketing']) < 0.1
                    delivery_match = abs(actual_delivery - test['expected_delivery']) < 0.5
                    
                    if marketing_match and delivery_match:
                        print("✓ 数据匹配！")
                    else:
                        print("✗ 数据不匹配！")
                        if not marketing_match:
                            print(f"  单均营销差异: {actual_marketing - test['expected_marketing']:.2f}")
                        if not delivery_match:
                            print(f"  单均配送差异: {actual_delivery - test['expected_delivery']:.2f}")
                else:
                    print("✗ 未找到泰州泰兴店")
            else:
                print(f"✗ API失败: {data}")
        except requests.Timeout:
            print("✗ 请求超时（30秒）")
        except Exception as e:
            print(f"✗ 请求异常: {e}")


if __name__ == "__main__":
    print("\n清除缓存并测试渠道筛选\n")
    
    # 步骤1：清除缓存
    clear_all_caches()
    
    # 步骤2：测试渠道筛选
    test_channel_filtering()
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)
    print("\n如果数据仍然不匹配，请检查：")
    print("1. 后端服务是否已重启")
    print("2. 后端日志中是否有'渠道筛选'的输出")
    print("3. 前端是否正确传递了channel参数")
