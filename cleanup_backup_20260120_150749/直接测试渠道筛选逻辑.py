# -*- coding: utf-8 -*-
"""
直接测试渠道筛选逻辑（不通过API）

验证DataFrame筛选是否正常工作
"""

import sys
from pathlib import Path
from datetime import date

# 添加路径
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.api.v1.store_comparison import get_all_stores_data, calculate_store_metrics

def test_channel_filtering_logic():
    """测试渠道筛选逻辑"""
    print("="*80)
    print("直接测试渠道筛选逻辑")
    print("="*80)
    
    # 加载数据
    start_date = date(2026, 1, 12)
    end_date = date(2026, 1, 18)
    
    print(f"\n加载数据: {start_date} ~ {end_date}")
    df = get_all_stores_data(start_date, end_date)
    
    if df.empty:
        print("数据为空！")
        return
    
    print(f"总数据行数: {len(df)}")
    print(f"渠道列: {'渠道' in df.columns}")
    
    if '渠道' in df.columns:
        print(f"\n渠道分布:")
        channel_counts = df['渠道'].value_counts()
        for ch, count in channel_counts.items():
            print(f"  {ch}: {count} 行")
        
        # 测试筛选饿了么
        print(f"\n测试筛选: 饿了么")
        df_elm = df[df['渠道'] == '饿了么']
        print(f"筛选后行数: {len(df_elm)}")
        
        if not df_elm.empty:
            # 计算指标
            stats = calculate_store_metrics(df_elm)
            print(f"门店数: {len(stats)}")
            
            # 查找泰州泰兴店
            target = stats[stats['store_name'].str.contains('泰州泰兴', na=False)]
            if not target.empty:
                row = target.iloc[0]
                print(f"\n泰州泰兴店 (饿了么):")
                print(f"  订单数: {row['order_count']}")
                print(f"  销售额: {row['total_revenue']:.2f}")
                print(f"  单均配送费: {row['avg_delivery_fee']:.2f}")
                print(f"  单均营销费: {row['avg_marketing_cost']:.2f}")
        
        # 测试筛选美团共橙
        print(f"\n测试筛选: 美团共橙")
        df_mt = df[df['渠道'] == '美团共橙']
        print(f"筛选后行数: {len(df_mt)}")
        
        if not df_mt.empty:
            # 计算指标
            stats = calculate_store_metrics(df_mt)
            print(f"门店数: {len(stats)}")
            
            # 查找泰州泰兴店
            target = stats[stats['store_name'].str.contains('泰州泰兴', na=False)]
            if not target.empty:
                row = target.iloc[0]
                print(f"\n泰州泰兴店 (美团共橙):")
                print(f"  订单数: {row['order_count']}")
                print(f"  销售额: {row['total_revenue']:.2f}")
                print(f"  单均配送费: {row['avg_delivery_fee']:.2f}")
                print(f"  单均营销费: {row['avg_marketing_cost']:.2f}")
        
        # 测试全部渠道
        print(f"\n测试: 全部渠道")
        stats_all = calculate_store_metrics(df)
        print(f"门店数: {len(stats_all)}")
        
        target = stats_all[stats_all['store_name'].str.contains('泰州泰兴', na=False)]
        if not target.empty:
            row = target.iloc[0]
            print(f"\n泰州泰兴店 (全部渠道):")
            print(f"  订单数: {row['order_count']}")
            print(f"  销售额: {row['total_revenue']:.2f}")
            print(f"  单均配送费: {row['avg_delivery_fee']:.2f}")
            print(f"  单均营销费: {row['avg_marketing_cost']:.2f}")


if __name__ == "__main__":
    test_channel_filtering_logic()
