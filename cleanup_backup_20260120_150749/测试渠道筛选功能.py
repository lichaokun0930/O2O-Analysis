# -*- coding: utf-8 -*-
"""
测试全量门店对比的渠道筛选功能

验证：
1. 获取可用渠道列表（只显示有数据的渠道）
2. 渠道筛选后的环比数据是否正确
3. 对比不同渠道的单均营销和单均配送数据
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8080/api/v1/stores"

def test_available_channels():
    """测试获取可用渠道列表"""
    print("\n" + "="*80)
    print("测试1: 获取可用渠道列表")
    print("="*80)
    
    # 测试日期范围：2026-01-12 至 2026-01-18
    params = {
        "start_date": "2026-01-12",
        "end_date": "2026-01-18"
    }
    
    try:
        res = requests.get(f"{API_BASE}/comparison/available-channels", params=params)
        data = res.json()
        
        if data.get('success'):
            channels = data.get('data', [])
            print(f"✅ 获取到 {len(channels)} 个有数据的渠道:")
            for i, ch in enumerate(channels, 1):
                print(f"   {i}. {ch}")
        else:
            print(f"❌ 请求失败: {data}")
    except Exception as e:
        print(f"❌ 请求异常: {e}")


def test_channel_filtering():
    """测试渠道筛选功能"""
    print("\n" + "="*80)
    print("测试2: 渠道筛选功能")
    print("="*80)
    
    # 测试门店：惠宜选-泰州泰兴店
    # 测试日期：2026-01-12 至 2026-01-18
    
    test_channels = ['饿了么', '美团共橙', None]  # None 表示全部渠道
    
    for channel in test_channels:
        print(f"\n{'='*60}")
        print(f"📊 测试渠道: {channel or '全部渠道'}")
        print(f"{'='*60}")
        
        params = {
            "end_date": "2026-01-18",
            "previous_start": "2026-01-05",
            "previous_end": "2026-01-11"
        }
        
        if channel:
            params["channel"] = channel
        
        try:
            res = requests.get(f"{API_BASE}/comparison/week-over-week", params=params)
            data = res.json()
            
            if data.get('success'):
                stores = data.get('data', {}).get('stores', [])
                print(f"✅ 获取到 {len(stores)} 个门店的环比数据")
                
                # 查找泰州泰兴店
                target_store = None
                for store in stores:
                    if '泰州泰兴' in store.get('store_name', ''):
                        target_store = store
                        break
                
                if target_store:
                    store_name = target_store['store_name']
                    current = target_store['current']
                    
                    print(f"\n🏪 门店: {store_name}")
                    print(f"   订单数: {current['order_count']}")
                    print(f"   销售额: ¥{current['total_revenue']:,.2f}")
                    print(f"   利润: ¥{current['total_profit']:,.2f}")
                    print(f"   利润率: {current['profit_margin']:.2f}%")
                    print(f"   客单价: ¥{current['aov']:.2f}")
                    print(f"   单均配送费: ¥{current['avg_delivery_fee']:.2f}")
                    print(f"   单均营销费: ¥{current['avg_marketing_cost']:.2f}")
                else:
                    print(f"⚠️ 未找到泰州泰兴店数据")
            else:
                print(f"❌ 请求失败: {data}")
        except Exception as e:
            print(f"❌ 请求异常: {e}")


def test_comparison_with_dash():
    """对比React版本和Dash版本的数据"""
    print("\n" + "="*80)
    print("测试3: 对比React版本和Dash版本的数据")
    print("="*80)
    
    print("\n📋 Dash版本数据（参考）:")
    print("   泰州泰兴店 (2026-01-12 至 2026-01-18)")
    print("   - 饿了么: 单均营销 ¥5.58, 单均配送 ¥1.61")
    print("   - 美团共橙: 单均营销 ¥5.19, 单均配送 ¥3.89")
    
    print("\n📊 React版本数据:")
    
    channels = ['饿了么', '美团共橙']
    
    for channel in channels:
        params = {
            "end_date": "2026-01-18",
            "previous_start": "2026-01-05",
            "previous_end": "2026-01-11",
            "channel": channel
        }
        
        try:
            res = requests.get(f"{API_BASE}/comparison/week-over-week", params=params)
            data = res.json()
            
            if data.get('success'):
                stores = data.get('data', {}).get('stores', [])
                
                # 查找泰州泰兴店
                target_store = None
                for store in stores:
                    if '泰州泰兴' in store.get('store_name', ''):
                        target_store = store
                        break
                
                if target_store:
                    current = target_store['current']
                    print(f"   - {channel}: 单均营销 ¥{current['avg_marketing_cost']:.2f}, 单均配送 ¥{current['avg_delivery_fee']:.2f}")
                else:
                    print(f"   - {channel}: ⚠️ 未找到数据")
        except Exception as e:
            print(f"   - {channel}: ❌ 请求异常: {e}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("测试: 全量门店对比 - 渠道筛选功能")
    print("="*80)
    
    test_available_channels()
    test_channel_filtering()
    test_comparison_with_dash()
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)
