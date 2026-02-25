# -*- coding: utf-8 -*-
"""Extract analysis functions from orders.py into orders_analysis.py"""

import os

orders_path = r'd:\Python\订单数据看板（老版本）\订单数据看板\订单数据看板\O2O-Analysis\backend\app\api\v1\orders.py'
output_path = r'd:\Python\订单数据看板（老版本）\订单数据看板\订单数据看板\O2O-Analysis\backend\app\api\v1\orders_analysis.py'

with open(orders_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Function blocks to extract (1-indexed line numbers)
ranges = [
    (1411, 1467),   # get_profit_distribution
    (1470, 1568),   # get_price_distribution
    (1571, 1580),   # get_price_range_color
    (1583, 1662),   # get_category_trend
    (2091, 2202),   # get_anomaly_detection
    (2377, 2624),   # get_category_hourly_trend
    (2627, 2818),   # get_top_products_by_date
]

header = """# -*- coding: utf-8 -*-
\"\"\"
品类分析 + 异常检测 + 图表联动 API

从 orders.py 拆分出的分析相关接口：
- 利润区间分布
- 客单价区间分布
- 一级分类销售趋势
- 异常诊断
- 分时品类走势
- 商品销量排行
\"\"\"

from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import pandas as pd
import numpy as np

# 从主模块导入公共函数
from .orders import get_order_data, calculate_order_metrics

router = APIRouter()


"""

content = header
for start, end in ranges:
    block = ''.join(lines[start-1:end])
    content += block + '\n\n'

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'✅ orders_analysis.py created: {len(content)} chars')
for line in content.split('\n'):
    if 'async def ' in line or ('def get_price_range' in line):
        print(f'  {line.strip()[:70]}')
