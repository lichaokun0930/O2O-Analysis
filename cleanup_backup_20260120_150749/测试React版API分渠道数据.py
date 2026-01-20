#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试React版API返回的分渠道数据

直接调用React版本的API，查看返回的单均营销和单均配送数据
"""

import requests
import json
from datetime import date

# API基础URL
BASE_URL = "http://localhost:8080/api/v1"

def test_store_comparison_api():
    """测试全量门店对比API"""
    print("="*80)
    print("🔍 测试React版全量门店对比API")
    print("="*80)
    
    # 调用全量门店对比API
    url = f"{BASE_URL}/store-comparison/week-over-week"
    
    print(f"\n请求URL: {url}")
    print("请求参数: 无（默认使用最近一周数据）")
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"\n❌ API请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return
        
        data = response.json()
        
        if not data.get('success'):
            print(f"\n❌ API返回失败: {data.get('message')}")
            return
        
        stores_data = data.get('data', [])
        print(f"\n✅ API请求成功")
        print(f"返回门店数: {len(stores_data)}")
        
        # 查找泰州泰兴店
        target_store = None
        for store in stores_data:
            if '泰兴' in store.get('store_name', ''):
                target_store = store
                break
        
        if not target_store:
            print("\n⚠️ 未找到泰州泰兴店，显示前3个门店的数据：")
            for i, store in enumerate(stores_data[:3]):
                print(f"\n门店{i+1}: {store.get('store_name')}")
                print(f"  单均营销: ¥{store.get('current', {}).get('avg_marketing_cost', 0):.2f}")
                print(f"  单均配送: ¥{store.get('current', {}).get('avg_delivery_fee', 0):.2f}")
            return
        
        # 显示泰州泰兴店的数据
        print(f"\n找到门店: {target_store.get('store_name')}")
        print("="*80)
        
        current = target_store.get('current', {})
        print(f"\n当前周期数据:")
        print(f"  订单数: {current.get('order_count', 0)}")
        print(f"  销售额: ¥{current.get('total_revenue', 0):,.2f}")
        print(f"  利润: ¥{current.get('total_profit', 0):,.2f}")
        print(f"  利润率: {current.get('profit_margin', 0):.2f}%")
        print(f"  客单价: ¥{current.get('aov', 0):.2f}")
        print(f"  单均配送费: ¥{current.get('avg_delivery_fee', 0):.2f}")
        print(f"  单均营销费: ¥{current.get('avg_marketing_cost', 0):.2f}")
        print(f"  配送成本率: {current.get('delivery_cost_rate', 0):.2f}%")
        print(f"  营销成本率: {current.get('marketing_cost_rate', 0):.2f}%")
        
        changes = target_store.get('changes', {})
        if changes:
            print(f"\n环比变化:")
            print(f"  订单数: {changes.get('order_count', 0):+.2f}%")
            print(f"  销售额: {changes.get('total_revenue', 0):+.2f}%")
            print(f"  利润: {changes.get('total_profit', 0):+.2f}%")
            print(f"  客单价: {changes.get('aov', 0):+.2f}%")
            print(f"  单均配送费: {changes.get('avg_delivery_fee', 0):+.2f}%")
            print(f"  单均营销费: {changes.get('avg_marketing_cost', 0):+.2f}%")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到API服务器")
        print("请确保后端服务已启动:")
        print("  cd backend")
        print("  python -m app.main")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

def test_orders_channels_api():
    """测试订单概览-渠道统计API"""
    print("\n" + "="*80)
    print("🔍 测试React版订单概览-渠道统计API")
    print("="*80)
    
    # 调用渠道统计API
    url = f"{BASE_URL}/orders/channels"
    
    # 添加门店筛选
    params = {
        'store_name': '惠宜选-泰州泰兴店',
        'start_date': '2026-01-12',
        'end_date': '2026-01-18'
    }
    
    print(f"\n请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"\n❌ API请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return
        
        data = response.json()
        
        if not data.get('success'):
            print(f"\n❌ API返回失败: {data.get('message')}")
            return
        
        channels_data = data.get('data', [])
        print(f"\n✅ API请求成功")
        print(f"返回渠道数: {len(channels_data)}")
        
        # 显示各渠道数据
        print("\n" + "="*80)
        print("各渠道数据:")
        print("="*80)
        
        for channel in channels_data:
            print(f"\n{channel.get('channel')}:")
            print(f"  订单数: {channel.get('order_count', 0)}")
            print(f"  销售额: ¥{channel.get('amount', 0):,.2f}")
            print(f"  利润: ¥{channel.get('profit', 0):,.2f}")
            print(f"  客单价: ¥{channel.get('avg_value', 0):.2f}")
            print(f"  利润率: {channel.get('profit_rate', 0):.2f}%")
            print(f"  订单占比: {channel.get('order_ratio', 0):.2f}%")
            print(f"  销售额占比: {channel.get('amount_ratio', 0):.2f}%")
            
            # 注意：这个API可能没有返回单均营销和单均配送
            if 'avg_marketing_cost' in channel:
                print(f"  单均营销: ¥{channel.get('avg_marketing_cost', 0):.2f}")
            if 'avg_delivery_fee' in channel:
                print(f"  单均配送: ¥{channel.get('avg_delivery_fee', 0):.2f}")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到API服务器")
        print("请确保后端服务已启动:")
        print("  cd backend")
        print("  python -m app.main")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

def test_channel_comparison_api():
    """测试渠道环比对比API"""
    print("\n" + "="*80)
    print("🔍 测试React版渠道环比对比API")
    print("="*80)
    
    # 调用渠道环比对比API
    url = f"{BASE_URL}/orders/channel-comparison"
    
    # 添加门店筛选
    params = {
        'store_name': '惠宜选-泰州泰兴店',
        'start_date': '2026-01-12',
        'end_date': '2026-01-18'
    }
    
    print(f"\n请求URL: {url}")
    print(f"请求参数: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"\n❌ API请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return
        
        data = response.json()
        
        if not data.get('success'):
            print(f"\n❌ API返回失败: {data.get('message')}")
            return
        
        channels_data = data.get('data', [])
        print(f"\n✅ API请求成功")
        print(f"返回渠道数: {len(channels_data)}")
        
        # 显示各渠道数据（包含成本结构）
        print("\n" + "="*80)
        print("各渠道详细数据（包含单均营销和单均配送）:")
        print("="*80)
        
        for channel in channels_data:
            current = channel.get('current', {})
            changes = channel.get('changes', {})
            
            print(f"\n{channel.get('channel')}:")
            print(f"  订单数: {current.get('order_count', 0)}")
            print(f"  销售额: ¥{current.get('amount', 0):,.2f}")
            print(f"  利润: ¥{current.get('profit', 0):,.2f}")
            print(f"  客单价: ¥{current.get('avg_value', 0):.2f}")
            print(f"  利润率: {current.get('profit_rate', 0):.2f}%")
            
            # 重点：单均营销和单均配送
            print(f"  单均利润: ¥{current.get('avg_profit_per_order', 0):.2f}")
            print(f"  单均营销: ¥{current.get('avg_marketing_per_order', 0):.2f}")
            print(f"  单均配送: ¥{current.get('avg_delivery_per_order', 0):.2f}")
            
            if changes:
                print(f"  环比变化:")
                print(f"    单均营销: {changes.get('avg_marketing_per_order', 0):+.2f}%")
                print(f"    单均配送: {changes.get('avg_delivery_per_order', 0):+.2f}%")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到API服务器")
        print("请确保后端服务已启动:")
        print("  cd backend")
        print("  python -m app.main")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")

def main():
    """主函数"""
    print("="*80)
    print("🔍 测试React版API分渠道数据")
    print("="*80)
    print("\n测试目标：")
    print("  1. 全量门店对比API - 查看泰州泰兴店的单均营销和单均配送")
    print("  2. 订单概览-渠道统计API - 查看各渠道的数据")
    print("  3. 渠道环比对比API - 查看各渠道的单均营销和单均配送")
    
    # 测试1：全量门店对比
    test_store_comparison_api()
    
    # 测试2：订单概览-渠道统计
    test_orders_channels_api()
    
    # 测试3：渠道环比对比（包含单均营销和单均配送）
    test_channel_comparison_api()
    
    print("\n" + "="*80)
    print("✅ 测试完成")
    print("="*80)
    print("\n💡 对比说明：")
    print("  - 全量门店对比显示的是全渠道合计数据")
    print("  - 渠道环比对比显示的是各渠道分别的数据")
    print("  - 如果两者的计算逻辑一致，分渠道数据的加权平均应该等于全渠道合计")

if __name__ == "__main__":
    main()
