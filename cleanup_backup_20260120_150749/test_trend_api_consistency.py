# -*- coding: utf-8 -*-
"""
销售趋势分析API一致性测试

验证React版本的trend API返回数据与Dash版本完全一致
"""

import requests
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 后端API地址
API_BASE = "http://127.0.0.1:8080/api/v1"

def test_trend_api():
    """测试trend API返回数据"""
    print("=" * 60)
    print("📊 销售趋势分析API一致性测试")
    print("=" * 60)
    
    # 1. 获取门店列表
    print("\n1️⃣ 获取门店列表...")
    try:
        res = requests.get(f"{API_BASE}/orders/stores")
        stores = res.json().get('data', [])
        print(f"   ✅ 获取到 {len(stores)} 个门店")
        if stores:
            test_store = stores[0]
            print(f"   📍 测试门店: {test_store}")
    except Exception as e:
        print(f"   ❌ 获取门店列表失败: {e}")
        return
    
    # 2. 获取渠道列表
    print("\n2️⃣ 获取渠道列表...")
    try:
        res = requests.get(f"{API_BASE}/orders/channel-list")
        channels = res.json().get('data', [])
        print(f"   ✅ 获取到 {len(channels)} 个渠道: {channels}")
    except Exception as e:
        print(f"   ❌ 获取渠道列表失败: {e}")
        channels = []
    
    # 3. 测试全部渠道的趋势数据
    print("\n3️⃣ 测试全部渠道趋势数据...")
    try:
        res = requests.get(f"{API_BASE}/orders/trend", params={
            'store_name': test_store,
            'days': 30,
            'granularity': 'day'
        })
        data = res.json()
        if data.get('success'):
            trend = data['data']
            print(f"   ✅ 获取到 {len(trend['dates'])} 天数据")
            print(f"   📅 日期范围: {trend['dates'][0] if trend['dates'] else 'N/A'} ~ {trend['dates'][-1] if trend['dates'] else 'N/A'}")
            
            # 检查是否包含利润率
            if 'profit_rates' in trend:
                print(f"   ✅ 包含利润率数据")
                avg_profit_rate = np.mean(trend['profit_rates']) if trend['profit_rates'] else 0
                print(f"   📈 平均利润率: {avg_profit_rate:.2f}%")
            else:
                print(f"   ❌ 缺少利润率数据!")
            
            # 打印汇总
            total_orders = sum(trend['order_counts'])
            total_amount = sum(trend['amounts'])
            total_profit = sum(trend['profits'])
            overall_profit_rate = (total_profit / total_amount * 100) if total_amount > 0 else 0
            
            print(f"\n   📊 汇总统计:")
            print(f"      订单总数: {total_orders}")
            print(f"      销售总额: ¥{total_amount:,.2f}")
            print(f"      总利润: ¥{total_profit:,.2f}")
            print(f"      整体利润率: {overall_profit_rate:.2f}%")
        else:
            print(f"   ❌ API返回失败: {data}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    # 4. 测试按渠道筛选
    if channels:
        test_channel = channels[0]
        print(f"\n4️⃣ 测试渠道筛选 (渠道={test_channel})...")
        try:
            res = requests.get(f"{API_BASE}/orders/trend", params={
                'store_name': test_store,
                'channel': test_channel,
                'days': 30,
                'granularity': 'day'
            })
            data = res.json()
            if data.get('success'):
                trend = data['data']
                print(f"   ✅ 获取到 {len(trend['dates'])} 天数据")
                
                total_orders = sum(trend['order_counts'])
                total_amount = sum(trend['amounts'])
                total_profit = sum(trend['profits'])
                
                print(f"   📊 {test_channel} 渠道汇总:")
                print(f"      订单总数: {total_orders}")
                print(f"      销售总额: ¥{total_amount:,.2f}")
                print(f"      总利润: ¥{total_profit:,.2f}")
                
                if 'profit_rates' in trend and trend['profit_rates']:
                    avg_profit_rate = np.mean(trend['profit_rates'])
                    print(f"      平均利润率: {avg_profit_rate:.2f}%")
            else:
                print(f"   ❌ API返回失败: {data}")
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")
    
    # 5. 与Dash版本对比
    print("\n5️⃣ 与Dash版本数据对比...")
    try:
        # 导入Dash版本的计算函数
        from 智能门店看板_Dash版 import calculate_order_metrics, calculate_daily_sales_with_channel, get_global_data
        
        # 获取全局数据
        df = get_global_data()
        if df is not None and not df.empty:
            # 筛选门店
            store_df = df[df['门店名称'] == test_store].copy()
            if not store_df.empty:
                # 计算订单指标
                order_agg = calculate_order_metrics(store_df)
                
                # 计算日度数据
                daily_sales, _ = calculate_daily_sales_with_channel(store_df, order_agg, 'all')
                
                if not daily_sales.empty:
                    dash_total_orders = daily_sales['订单数'].sum()
                    dash_total_amount = daily_sales['销售额'].sum()
                    dash_total_profit = daily_sales['总利润'].sum()
                    dash_avg_profit_rate = daily_sales['利润率'].mean()
                    
                    print(f"   📊 Dash版本数据:")
                    print(f"      订单总数: {dash_total_orders}")
                    print(f"      销售总额: ¥{dash_total_amount:,.2f}")
                    print(f"      总利润: ¥{dash_total_profit:,.2f}")
                    print(f"      平均利润率: {dash_avg_profit_rate:.2f}%")
                    
                    # 对比
                    print(f"\n   🔍 数据对比:")
                    print(f"      订单数差异: {total_orders - dash_total_orders}")
                    print(f"      销售额差异: ¥{total_amount - dash_total_amount:,.2f}")
                    print(f"      利润差异: ¥{total_profit - dash_total_profit:,.2f}")
                else:
                    print(f"   ⚠️ Dash版本日度数据为空")
            else:
                print(f"   ⚠️ 门店 {test_store} 在Dash数据中不存在")
        else:
            print(f"   ⚠️ 无法获取Dash全局数据")
    except ImportError as e:
        print(f"   ⚠️ 无法导入Dash模块进行对比: {e}")
        print(f"   💡 请确保在O2O-Analysis目录下运行此脚本")
    except Exception as e:
        print(f"   ❌ 对比失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_trend_api()
