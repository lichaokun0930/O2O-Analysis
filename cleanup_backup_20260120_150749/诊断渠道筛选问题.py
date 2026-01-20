# -*- coding: utf-8 -*-
"""
诊断渠道筛选问题

对比：
1. 直接测试逻辑（已验证正确）
2. API测试（疑似有问题）
"""

import requests
import sys
from pathlib import Path
from datetime import date

# 添加路径
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.api.v1.store_comparison import get_all_stores_data, calculate_store_metrics

API_BASE = "http://localhost:8080/api/v1/stores"

def test_direct_logic():
    """直接测试逻辑（已知正确）"""
    print("="*80)
    print("1. 直接测试逻辑（DataFrame筛选）")
    print("="*80)
    
    start_date = date(2026, 1, 12)
    end_date = date(2026, 1, 18)
    
    df = get_all_stores_data(start_date, end_date)
    
    # 测试饿了么
    df_elm = df[df['渠道'] == '饿了么']
    stats_elm = calculate_store_metrics(df_elm)
    target_elm = stats_elm[stats_elm['store_name'].str.contains('泰州泰兴', na=False)]
    
    if not target_elm.empty:
        row = target_elm.iloc[0]
        print(f"\n饿了么:")
        print(f"  订单数: {row['order_count']}")
        print(f"  单均配送费: ¥{row['avg_delivery_fee']:.2f}")
        print(f"  单均营销费: ¥{row['avg_marketing_cost']:.2f}")
    
    # 测试美团共橙
    df_mt = df[df['渠道'] == '美团共橙']
    stats_mt = calculate_store_metrics(df_mt)
    target_mt = stats_mt[stats_mt['store_name'].str.contains('泰州泰兴', na=False)]
    
    if not target_mt.empty:
        row = target_mt.iloc[0]
        print(f"\n美团共橙:")
        print(f"  订单数: {row['order_count']}")
        print(f"  单均配送费: ¥{row['avg_delivery_fee']:.2f}")
        print(f"  单均营销费: ¥{row['avg_marketing_cost']:.2f}")


def test_api():
    """测试API（疑似有问题）"""
    print("\n" + "="*80)
    print("2. 测试API（week-over-week端点）")
    print("="*80)
    
    channels = ['饿了么', '美团共橙']
    
    for channel in channels:
        params = {
            "end_date": "2026-01-18",
            "previous_start": "2026-01-05",
            "previous_end": "2026-01-11",
            "channel": channel
        }
        
        print(f"\n请求参数: {params}")
        
        try:
            res = requests.get(f"{API_BASE}/comparison/week-over-week", params=params, timeout=10)
            data = res.json()
            
            if data.get('success'):
                stores = data.get('data', {}).get('stores', [])
                print(f"返回门店数: {len(stores)}")
                
                # 查找泰州泰兴店
                target = None
                for store in stores:
                    if '泰州泰兴' in store.get('store_name', ''):
                        target = store
                        break
                
                if target:
                    current = target['current']
                    print(f"\n{channel}:")
                    print(f"  订单数: {current['order_count']}")
                    print(f"  单均配送费: ¥{current['avg_delivery_fee']:.2f}")
                    print(f"  单均营销费: ¥{current['avg_marketing_cost']:.2f}")
                else:
                    print(f"  未找到泰州泰兴店")
            else:
                print(f"  API失败: {data}")
        except Exception as e:
            print(f"  请求异常: {e}")


def compare_results():
    """对比结果"""
    print("\n" + "="*80)
    print("3. 结果对比")
    print("="*80)
    
    print("\n预期结果（直接测试）:")
    print("  饿了么: 单均营销 ¥5.58, 单均配送 ¥4.94")
    print("  美团共橙: 单均营销 ¥5.19, 单均配送 ¥4.14")
    
    print("\n实际结果（API）:")
    print("  如果两个渠道数据完全一样，说明渠道筛选未生效")
    print("  如果数据与预期一致，说明渠道筛选正常")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("诊断渠道筛选问题")
    print("="*80)
    
    test_direct_logic()
    test_api()
    compare_results()
    
    print("\n" + "="*80)
    print("诊断完成")
    print("="*80)
