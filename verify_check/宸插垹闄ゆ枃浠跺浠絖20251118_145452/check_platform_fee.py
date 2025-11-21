#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查数据库中platform_service_fee的分布"""

import sys
sys.path.append('.')

from database.data_source_manager import DataSourceManager
import pandas as pd

def main():
    ds = DataSourceManager()
    df = ds.load_from_database('REAL_STORE_DATA')
    
    print(f"\n{'='*60}")
    print("📊 数据库中 platform_service_fee 字段分析")
    print(f"{'='*60}\n")
    
    print(f"总订单数: {len(df)}")
    print(f"平台服务费 > 0 的订单: {(df['platform_service_fee'] > 0).sum()}")
    print(f"平台服务费 = 0 的订单: {(df['platform_service_fee'] == 0).sum()}")
    print(f"平台服务费为空的订单: {df['platform_service_fee'].isna().sum()}")
    
    print(f"\n平台服务费统计分布:")
    print(df['platform_service_fee'].describe())
    
    print(f"\n平台服务费唯一值:")
    print(df['platform_service_fee'].unique()[:20])  # 前20个唯一值
    
    # 检查是否所有值都是0
    all_zero = (df['platform_service_fee'] == 0).all()
    print(f"\n❗ 所有平台服务费都是0: {all_zero}")
    
    # 如果有非0值,显示样例
    if not all_zero:
        non_zero = df[df['platform_service_fee'] > 0]
        print(f"\n✅ 找到 {len(non_zero)} 笔有平台服务费的订单")
        print(non_zero[['order_id', 'platform_service_fee']].head(10))

if __name__ == '__main__':
    main()
