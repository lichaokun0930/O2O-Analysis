#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试raw_data的日期范围"""

import pandas as pd
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from 智能门店经营看板_可视化 import load_real_business_data

# 加载数据
data, msgs = load_real_business_data()

if data:
    raw = data['raw_data']
    print(f"✅ Raw data行数: {len(raw)}")
    print(f"   日期列是否存在: {'日期' in raw.columns}")
    print(f"   下单时间列是否存在: {'下单时间' in raw.columns}")
    
    if '下单时间' in raw.columns:
        dates = pd.to_datetime(raw['下单时间'], errors='coerce')
        valid_dates = dates.dropna()
        print(f"   日期范围: {valid_dates.min()} 至 {valid_dates.max()}")
        print(f"   唯一日期数: {valid_dates.dt.date.nunique()}")
        
        # 按日期统计数据量
        date_counts = valid_dates.dt.date.value_counts().sort_index()
        print(f"\n📊 每日数据量（前10天）:")
        for date, count in date_counts.head(10).items():
            print(f"   {date}: {count}条")
else:
    print("❌ 未能加载数据")
