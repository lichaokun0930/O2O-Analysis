# -*- coding: utf-8 -*-
"""
测试距离分析API
"""
import requests
import json

def test_distance_api():
    """测试距离分析API"""
    url = "http://localhost:8080/api/v1/orders/distance-analysis"
    
    try:
        response = requests.get(url, timeout=30)
        data = response.json()
        
        if data.get('success'):
            print("=" * 60)
            print("✅ 距离分析API测试结果")
            print("=" * 60)
            
            bands = data['data']['distance_bands']
            for band in bands:
                print(f"区间 {band['band_label']}: "
                      f"订单数={band['order_count']}, "
                      f"利润率={band['profit_rate']}%")
            
            summary = data['data']['summary']
            print(f"\n📊 汇总:")
            print(f"   总订单数: {summary['total_orders']}")
            print(f"   平均距离: {summary['avg_distance']}km")
            print(f"   最优距离: {summary['optimal_distance']}")
            print(f"   总销售额: {summary['total_revenue']}")
            print(f"   总利润: {summary['total_profit']}")
        else:
            print(f"❌ API返回失败: {data}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确保后端已启动")
        print("   启动命令: python backend/main.py")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_distance_api()
