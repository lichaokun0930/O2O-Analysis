# -*- coding: utf-8 -*-
"""Extract delivery functions from orders.py into orders_delivery.py"""

import os

orders_path = r'd:\Python\订单数据看板（老版本）\订单数据看板\订单数据看板\O2O-Analysis\backend\app\api\v1\orders.py'
output_path = r'd:\Python\订单数据看板（老版本）\订单数据看板\订单数据看板\O2O-Analysis\backend\app\api\v1\orders_delivery.py'

with open(orders_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Ranges identified from view_file_outline after Phase 2 deletions (1-indexed)
ranges = [
    (2032, 2102),   # identify_peak_periods
    (2105, 2455),   # get_hourly_profit
    (2460, 2636),   # get_cost_structure
    (2637, 2652),   # DISTANCE_BANDS
    (2653, 2671),   # get_distance_band
    (2674, 2691),   # get_distance_band_index
    (2694, 3110),   # get_distance_analysis
    (3115, 3307),   # get_delivery_radar_data
]

header = """# -*- coding: utf-8 -*-
\"\"\"
配送分析 + 成本结构 API

从 orders.py 拆分出的配送相关接口：
- 分时利润分析（含高峰识别）
- 成本结构分析（桑基图）
- 分距离订单诊断
- 配送溢价雷达
\"\"\"

from fastapi import APIRouter, Query, Depends
from typing import Optional, List, Dict, Any
from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np
from database.connection import SessionLocal

# 从主模块导入公共函数
from .orders import get_order_data, calculate_order_metrics

router = APIRouter()

"""

content = header
for start, end in ranges:
    block = "".join(lines[start-1:end])
    content += block + "\n\n"

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ orders_delivery.py created: {len(content)} chars")
