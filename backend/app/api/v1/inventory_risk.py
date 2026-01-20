# -*- coding: utf-8 -*-
"""
库存风险分析 API

与 Dash 版本完全一致的计算逻辑：
- 售罄品: 库存=0 且 近7天有销量
- 滞销品分级（🆕 优化版：以商品首次出现日期为基准）:
  - 关注: 3天无销量 且 库存 > 0
  - 轻度滞销: 7天无销量 且 库存 > 0
  - 中度滞销: 15天无销量 且 库存 > 0
  - 重度滞销: 30天无销量 且 库存 > 0
- 库存周转天数: 当前库存 / 日均销量

🆕 2025-01-16 优化：
滞销天数计算逻辑改为"以商品首次出现日期为观察起点"
- 商品A在1日有销售 → 从1日开始计算无销售天数
- 商品B在5日首次出现 → 从5日开始计算无销售天数
- 解决了数据窗口边界导致的滞销判断失真问题

业务逻辑来源: 智能门店看板_Dash版.py 第11333-11430行
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List
from datetime import timedelta
import pandas as pd
import numpy as np

import sys
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from .orders import get_order_data

router = APIRouter()


def get_product_latest_stock(df: pd.DataFrame, stock_col: str, date_col: str) -> Dict[str, float]:
    """
    获取每个商品的最新库存（与Dash版本一致）
    
    逻辑：按日期排序，取每个商品最后一条记录的库存值
    """
    if stock_col not in df.columns or date_col not in df.columns:
        return {}
    
    df_sorted = df.sort_values(date_col)
    latest = df_sorted.groupby('商品名称')[stock_col].last()
    return latest.to_dict()


def calculate_inventory_risk_dash_style(df: pd.DataFrame, store_name: str = None) -> Dict[str, Any]:
    """
    计算库存风险统计（与Dash版本完全一致）
    
    来源: 智能门店看板_Dash版.py 第11333-11430行
    """
    result = {
        "sold_out": {"total": 0, "products": [], "by_category": {}},
        "slow_moving": {
            "total": 0, 
            "by_severity": {"light": 0, "medium": 0, "heavy": 0, "critical": 0},
            "products": [],
            "by_category": {}
        },
        "by_category": [],
        "turnover": {}
    }
    
    if df.empty:
        return result
    
    # ==================== 1. 检查必需字段 ====================
    date_col = None
    for col in ['日期', '下单时间']:
        if col in df.columns:
            date_col = col
            break
    
    stock_col = None
    for col in ['库存', '剩余库存', 'stock', 'remaining_stock']:
        if col in df.columns:
            stock_col = col
            break
    
    sales_col = '月售' if '月售' in df.columns else '销量' if '销量' in df.columns else None
    category_col = '一级分类名' if '一级分类名' in df.columns else '一级分类'
    
    if not date_col:
        print("⚠️ 缺少日期字段，无法计算库存风险")
        return result
    
    # ==================== 2. 准备数据 ====================
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    
    if df.empty:
        return result
    
    last_date = df[date_col].max()
    seven_days_ago = last_date - timedelta(days=7)
    
    # ==================== 3. 获取商品最新库存状态 ====================
    if stock_col:
        stock_map = get_product_latest_stock(df, stock_col=stock_col, date_col=date_col)
        
        all_products = df['商品名称'].unique()
        last_stock = pd.DataFrame({
            '商品名称': all_products,
            '库存': [stock_map.get(p, 0) for p in all_products]
        })
        
        # 添加分类信息
        product_category_map = df.groupby('商品名称')[category_col].first().to_dict()
        last_stock['分类'] = last_stock['商品名称'].map(product_category_map)
    else:
        print("⚠️ 缺少库存字段，无法计算库存风险")
        return result
    
    # ==================== 4. 售罄品统计 (库存=0且近7天有销量) ====================
    # 筛选近7天有销量的数据
    recent_sales = df[df[date_col] >= seven_days_ago]
    recent_products = set(recent_sales['商品名称'].unique())
    
    # 获取当前库存=0的商品
    zero_stock_products = set(last_stock[last_stock['库存'] == 0]['商品名称'].unique())
    
    # 售罄品 = 库存0 且 近7天有销量
    sellout_products = zero_stock_products & recent_products
    
    result["sold_out"]["total"] = len(sellout_products)
    
    # 按分类统计售罄品
    if len(sellout_products) > 0:
        sellout_df = df[df['商品名称'].isin(sellout_products)][[category_col, '商品名称']].drop_duplicates()
        sellout_by_cat = sellout_df.groupby(category_col).size().to_dict()
        result["sold_out"]["by_category"] = sellout_by_cat
        
        # 生成售罄品详情列表
        for product in sellout_products:
            product_data = recent_sales[recent_sales['商品名称'] == product]
            category = product_category_map.get(product, '未知')
            
            # 计算影响金额（近7天销售额）
            impact = product_data['实收价格'].sum() if '实收价格' in product_data.columns else 0
            
            result["sold_out"]["products"].append({
                "id": f"oos-{hash(product) % 10000}",
                "skuName": product,
                "spec": "",
                "issueType": "OUT_OF_STOCK",
                "reason": "库存为0但近7天有销量",
                "impactValue": round(float(impact), 2),
                "duration": "7天内",
                "action": "立即补货",
                "category": category
            })
    
    # ==================== 5. 滞销品四级分级统计（🆕 优化版：以首次出现日期为基准） ====================
    # 🆕 计算每个商品的首次出现日期和最后销售日期
    product_first_sale = df.groupby('商品名称')[date_col].min().reset_index()
    product_first_sale.columns = ['商品名称', '首次出现日期']
    
    product_last_sale = df.groupby('商品名称')[date_col].max().reset_index()
    product_last_sale.columns = ['商品名称', '最后销售日期']
    
    # 合并首次和最后销售日期
    product_sales_info = product_first_sale.merge(product_last_sale, on='商品名称')
    
    # 🆕 计算滞销天数（新逻辑）
    # 如果最后销售日期 == 首次出现日期，说明只卖过一次，从首次出现日期开始计算
    # 否则从最后销售日期开始计算
    def calc_days_no_sale(row):
        if row['最后销售日期'] == row['首次出现日期']:
            # 只在首次出现时卖过一次，从首次出现日期开始计算
            return (last_date - row['首次出现日期']).days
        else:
            # 有多次销售，从最后销售日期开始计算
            return (last_date - row['最后销售日期']).days
    
    product_sales_info['滞销天数'] = product_sales_info.apply(calc_days_no_sale, axis=1)
    
    # 合并库存信息
    product_stagnant = product_sales_info.merge(
        last_stock[['商品名称', '库存', '分类']], 
        on='商品名称', 
        how='left'
    )
    product_stagnant['库存'] = product_stagnant['库存'].fillna(0)
    
    # 🆕 滞销品分级（4级：关注/轻度/中度/重度，互斥分级）
    product_stagnant['关注'] = ((product_stagnant['滞销天数'] >= 3) & (product_stagnant['滞销天数'] < 7) & (product_stagnant['库存'] > 0)).astype(int)
    product_stagnant['轻度滞销'] = ((product_stagnant['滞销天数'] >= 7) & (product_stagnant['滞销天数'] < 15) & (product_stagnant['库存'] > 0)).astype(int)
    product_stagnant['中度滞销'] = ((product_stagnant['滞销天数'] >= 15) & (product_stagnant['滞销天数'] < 30) & (product_stagnant['库存'] > 0)).astype(int)
    product_stagnant['重度滞销'] = ((product_stagnant['滞销天数'] >= 30) & (product_stagnant['库存'] > 0)).astype(int)
    
    # 汇总滞销品数量
    result["slow_moving"]["by_severity"] = {
        "watch": int(product_stagnant['关注'].sum()),
        "light": int(product_stagnant['轻度滞销'].sum()),
        "medium": int(product_stagnant['中度滞销'].sum()),
        "heavy": int(product_stagnant['重度滞销'].sum()),
        "critical": 0  # 不再使用超重度，统一归入重度
    }
    result["slow_moving"]["total"] = sum(result["slow_moving"]["by_severity"].values())
    
    # 按分类汇总滞销品
    stagnant_by_cat = product_stagnant.groupby('分类').agg({
        '关注': 'sum',
        '轻度滞销': 'sum',
        '中度滞销': 'sum',
        '重度滞销': 'sum'
    }).to_dict('index')
    
    for cat, counts in stagnant_by_cat.items():
        total = sum(counts.values())
        if total > 0:
            result["slow_moving"]["by_category"][cat] = {
                "watch": int(counts['关注']),
                "light": int(counts['轻度滞销']),
                "medium": int(counts['中度滞销']),
                "heavy": int(counts['重度滞销']),
                "critical": 0,
                "total": int(total)
            }
    
    # 生成滞销品详情列表
    slow_products = product_stagnant[
        (product_stagnant['关注'] == 1) |
        (product_stagnant['轻度滞销'] == 1) | 
        (product_stagnant['中度滞销'] == 1) | 
        (product_stagnant['重度滞销'] == 1)
    ]
    
    # 🔧 性能优化：预计算每个商品的平均单价，避免循环内过滤
    avg_price_map = {}
    if '实收价格' in df.columns:
        avg_price_map = df.groupby('商品名称')['实收价格'].mean().to_dict()
    
    for _, row in slow_products.iterrows():
        # 🆕 确定滞销等级（4级：关注/轻度/中度/重度）
        if row['重度滞销'] == 1:
            severity = 'heavy'
            action = '降价清仓'
        elif row['中度滞销'] == 1:
            severity = 'medium'
            action = '促销推荐'
        elif row['轻度滞销'] == 1:
            severity = 'light'
            action = '关注观察'
        else:  # 关注
            severity = 'watch'
            action = '持续关注'
        
        # 🔧 优化：使用预计算的平均单价
        avg_price = avg_price_map.get(row['商品名称'], 0)
        impact = row['库存'] * avg_price
        
        result["slow_moving"]["products"].append({
            "id": f"slow-{hash(row['商品名称']) % 10000}",
            "skuName": row['商品名称'],
            "spec": "",
            "issueType": "SLOW_MOVING",
            "reason": f"{int(row['滞销天数'])}天无销量",
            "impactValue": round(float(impact), 2),
            "duration": f"{int(row['滞销天数'])}天",
            "action": action,
            "severity": severity,
            "category": row['分类'] if pd.notna(row['分类']) else '未知'
        })
    
    # ==================== 6. 库存周转天数计算 ====================
    if sales_col:
        date_range_days = (df[date_col].max() - df[date_col].min()).days + 1
        if date_range_days <= 0:
            date_range_days = 1
        
        # 按分类统计
        category_stats = df.groupby(category_col).agg({
            sales_col: 'sum'
        }).reset_index()
        category_stats.columns = ['分类', '总销量']
        
        # 按分类统计当前库存
        category_stock = last_stock.groupby('分类')['库存'].sum().reset_index()
        category_stock.columns = ['分类', '当前库存']
        
        category_stats = category_stats.merge(category_stock, on='分类', how='left')
        category_stats['当前库存'] = category_stats['当前库存'].fillna(0)
        
        # 计算日均销量和库存周转天数
        category_stats['日均销量'] = (category_stats['总销量'] / date_range_days).round(2)
        category_stats['库存周转天数'] = category_stats.apply(
            lambda r: round(r['当前库存'] / r['日均销量'], 1) if r['日均销量'] > 0 else 0,
            axis=1
        )
        
        result["turnover"] = category_stats.set_index('分类')['库存周转天数'].to_dict()
    
    # ==================== 7. 按分类汇总 ====================
    categories = df[category_col].unique()
    for cat in categories:
        sold_out_count = result["sold_out"]["by_category"].get(cat, 0)
        slow_moving_data = result["slow_moving"]["by_category"].get(cat, {})
        slow_moving_count = slow_moving_data.get("total", 0) if isinstance(slow_moving_data, dict) else 0
        turnover = result["turnover"].get(cat, 0)
        
        result["by_category"].append({
            "category": cat,
            "soldOutCount": int(sold_out_count),
            "slowMovingCount": int(slow_moving_count),
            "inventoryTurnover": float(turnover),
            "slowMovingDetail": slow_moving_data if isinstance(slow_moving_data, dict) else {}
        })
    
    # 按售罄+滞销总数排序
    result["by_category"].sort(key=lambda x: x["soldOutCount"] + x["slowMovingCount"], reverse=True)
    
    return result


@router.get("/summary")
async def get_inventory_risk_summary(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    category: Optional[str] = Query(None, description="分类筛选")
) -> Dict[str, Any]:
    """
    获取库存风险汇总（与Dash版本一致）
    """
    df = get_order_data(store_name)
    if df.empty:
        return {
            "success": True,
            "data": {
                "sold_out": {"total": 0, "products": [], "by_category": {}},
                "slow_moving": {"total": 0, "by_severity": {}, "products": [], "by_category": {}},
                "by_category": [],
                "turnover": {}
            }
        }
    
    # 分类筛选
    if category:
        category_col = '一级分类名' if '一级分类名' in df.columns else '一级分类'
        if category_col in df.columns:
            df = df[df[category_col] == category]
    
    result = calculate_inventory_risk_dash_style(df, store_name)
    
    return {"success": True, "data": result}


@router.get("/sold-out")
async def get_sold_out_products(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """
    获取售罄品列表（与Dash版本一致）
    
    售罄品定义: 库存=0 且 近7天有销量
    """
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": [], "total": 0}
    
    result = calculate_inventory_risk_dash_style(df, store_name)
    products = result["sold_out"]["products"]
    
    # 分类筛选
    if category:
        products = [p for p in products if p.get("category") == category]
    
    # 分页
    total = len(products)
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "success": True,
        "data": products[start:end],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/slow-moving")
async def get_slow_moving_products(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    severity: Optional[str] = Query(None, description="滞销等级: light/medium/heavy/critical"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
) -> Dict[str, Any]:
    """
    获取滞销品列表（与Dash版本一致）
    
    滞销品分级:
    - light: 滞销天数 == 7
    - medium: 滞销天数 8-15
    - heavy: 滞销天数 16-30
    - critical: 滞销天数 > 30
    """
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": [], "total": 0, "by_severity": {}}
    
    result = calculate_inventory_risk_dash_style(df, store_name)
    products = result["slow_moving"]["products"]
    
    # 分类筛选
    if category:
        products = [p for p in products if p.get("category") == category]
    
    # 等级筛选
    if severity:
        products = [p for p in products if p.get("severity") == severity]
    
    # 分页
    total = len(products)
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "success": True,
        "data": products[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "by_severity": result["slow_moving"]["by_severity"]
    }


@router.get("/category-risk")
async def get_category_risk_stats(
    store_name: Optional[str] = Query(None, description="门店名称筛选")
) -> Dict[str, Any]:
    """
    获取按分类的库存风险统计（与Dash版本一致）
    
    用于品类效益矩阵中显示每个分类的售罄品和滞销品数量
    """
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": []}
    
    result = calculate_inventory_risk_dash_style(df, store_name)
    
    return {"success": True, "data": result["by_category"]}


@router.get("/trend")
async def get_inventory_risk_trend(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    days: int = Query(30, ge=7, le=90, description="趋势天数")
) -> Dict[str, Any]:
    """
    获取库存风险趋势数据（售罄率趋势 + 滞销率趋势）
    
    🆕 重构版本 - 解决数据窗口问题：
    
    滞销分级定义（简化为3级）：
    - 轻度(light): 7天无销量，需要 >= 8天数据
    - 中度(medium): 15天无销量，需要 >= 16天数据
    - 重度(heavy): 30天无销量，需要 >= 31天数据
    
    自适应逻辑：
    - 根据数据量自动决定可展示的等级
    - 趋势起始日 = 数据起始日 + 最高可用等级的回溯天数
    - 避免数据不足导致的虚假递增趋势
    
    返回：
    - 每日售罄率、滞销率（百分比）
    - 可用的滞销等级列表
    - 趋势有效起始日期
    """
    df = get_order_data(store_name)
    if df.empty:
        return {"success": True, "data": [], "message": "无数据", "availableLevels": []}
    
    # 检查必需字段
    date_col = None
    for col in ['日期', '下单时间']:
        if col in df.columns:
            date_col = col
            break
    
    stock_col = None
    for col in ['库存', '剩余库存', 'stock', 'remaining_stock']:
        if col in df.columns:
            stock_col = col
            break
    
    if not date_col or not stock_col:
        return {"success": True, "data": [], "message": f"缺少必需字段: date={date_col}, stock={stock_col}", "availableLevels": []}
    
    # 准备数据
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    
    if df.empty:
        return {"success": True, "data": [], "message": "日期解析后无有效数据", "availableLevels": []}
    
    # 🆕 分类筛选（支持一级分类和三级分类）
    category_col = '一级分类名' if '一级分类名' in df.columns else '一级分类'
    l3_col = '三级分类名' if '三级分类名' in df.columns else '三级分类'
    
    if category and category_col in df.columns:
        if '|' in category:
            # 三级分类格式：一级分类|三级分类
            parts = category.split('|')
            l1_cat = parts[0]
            l3_cat = parts[1] if len(parts) > 1 else None
            
            df = df[df[category_col] == l1_cat]
            if l3_cat and l3_col in df.columns:
                df = df[df[l3_col] == l3_cat]
        else:
            # 一级分类
            df = df[df[category_col] == category]
        
        if df.empty:
            return {"success": True, "data": [], "message": f"分类 {category} 无数据", "availableLevels": []}
    
    # 确定日期范围
    max_date = df[date_col].max()
    min_date = df[date_col].min()
    total_data_days = (max_date - min_date).days + 1
    
    # ==================== 🆕 滞销分级定义（4级：关注/轻度/中度/重度） ====================
    SLOW_MOVING_LEVELS = [
        {"key": "watch", "label": "关注", "days": 3, "min_data_days": 4},
        {"key": "light", "label": "轻度", "days": 7, "min_data_days": 8},
        {"key": "medium", "label": "中度", "days": 15, "min_data_days": 16},
        {"key": "heavy", "label": "重度", "days": 30, "min_data_days": 31},
    ]
    
    # 根据数据量确定可用等级
    available_levels = []
    max_lookback_days = 0
    for level in SLOW_MOVING_LEVELS:
        if total_data_days >= level["min_data_days"]:
            available_levels.append(level["key"])
            max_lookback_days = level["days"]
    
    if not available_levels:
        return {
            "success": True, 
            "data": [], 
            "message": f"数据量不足（{total_data_days}天），至少需要8天数据才能计算滞销趋势",
            "availableLevels": [],
            "totalDataDays": total_data_days
        }
    
    # ==================== 🆕 计算趋势有效起始日 ====================
    # 趋势起始日 = 数据起始日 + 最高可用等级的回溯天数
    trend_start_date = min_date + timedelta(days=max_lookback_days)
    
    # 确保趋势起始日不超过最大日期
    if trend_start_date > max_date:
        trend_start_date = max_date
    
    # 生成趋势日期序列
    date_range = pd.date_range(start=trend_start_date, end=max_date, freq='D')
    
    if len(date_range) == 0:
        return {
            "success": True,
            "data": [],
            "message": "趋势日期范围为空",
            "availableLevels": available_levels,
            "totalDataDays": total_data_days
        }
    
    trend_data = []
    
    # ==================== 🚀 性能优化：预计算所有数据 ====================
    df_sorted = df.sort_values(date_col)
    
    # 1. 预计算每个商品每天的最新库存（累积到当天）
    # 使用 pivot 创建 商品×日期 的库存矩阵
    all_products = df['商品名称'].unique()
    all_dates = pd.date_range(start=min_date, end=max_date, freq='D')
    
    # 按日期和商品分组，取每天每个商品的最后库存
    daily_stock_df = df_sorted.groupby([df_sorted[date_col].dt.date, '商品名称'])[stock_col].last().unstack(fill_value=np.nan)
    
    # 前向填充：如果某天没有数据，使用前一天的库存
    daily_stock_df = daily_stock_df.ffill()
    
    # 2. 🆕 预计算每个商品的首次出现日期（作为滞销计算的基准点）
    # 商品首次出现日期 = 该商品在数据中第一次有销售记录的日期
    product_first_appearance = df_sorted.groupby('商品名称')[date_col].min()
    print(f"[inventory_risk] 商品首次出现日期示例: {dict(list(product_first_appearance.items())[:3])}")
    
    # 3. 预计算每个商品每天的最后销售日期（用于判断是否有新销售）
    daily_last_sale = df_sorted.groupby([df_sorted[date_col].dt.date, '商品名称'])[date_col].max().unstack()
    daily_last_sale = daily_last_sale.ffill()  # 前向填充
    
    # 4. 预计算每个商品在每个7天窗口内是否有销量
    # 创建一个标记：每天每个商品是否有销售记录
    daily_has_sale = df_sorted.groupby([df_sorted[date_col].dt.date, '商品名称']).size().unstack(fill_value=0)
    daily_has_sale = (daily_has_sale > 0).astype(int)
    
    # 计算7天滚动窗口内是否有销量
    rolling_7d_sales = daily_has_sale.rolling(window=7, min_periods=1).sum()
    
    # ==================== 遍历日期计算趋势 ====================
    for current_date in date_range:
        current_date_key = current_date.date()
        current_date_ts = pd.Timestamp(current_date)
        
        # 获取当天的库存状态
        if current_date_key not in daily_stock_df.index:
            # 找最近的前一天
            valid_dates = [d for d in daily_stock_df.index if d <= current_date_key]
            if not valid_dates:
                continue
            current_date_key = max(valid_dates)
        
        stock_series = daily_stock_df.loc[current_date_key].dropna()
        if stock_series.empty:
            continue
        
        total_sku = len(stock_series)
        total_sku_with_stock = int((stock_series > 0).sum())
        
        # ==================== 售罄计算 ====================
        # 库存=0 的商品
        zero_stock_products = set(stock_series[stock_series == 0].index)
        
        # 近7天有销量的商品
        if current_date_key in rolling_7d_sales.index:
            recent_sales_mask = rolling_7d_sales.loc[current_date_key] > 0
            recent_products = set(recent_sales_mask[recent_sales_mask].index)
        else:
            recent_products = set()
        
        sold_out_count = len(zero_stock_products & recent_products)
        sold_out_rate = round(sold_out_count / total_sku * 100, 2) if total_sku > 0 else 0
        
        # ==================== 滞销计算（🆕 优化版：以首次出现日期为基准） ====================
        slow_moving_counts = {"watch": 0, "light": 0, "medium": 0, "heavy": 0}
        
        # 🆕 新逻辑：滞销天数 = 当前日期 - 商品首次出现日期（如果首次出现后一直没有再销售）
        # 或者 = 当前日期 - 最后销售日期（如果首次出现后有过销售）
        
        # 只统计有库存的商品
        products_with_stock = stock_series[stock_series > 0].index.tolist()
        
        if products_with_stock:
            days_no_sale_list = []
            
            for product in products_with_stock:
                # 获取商品首次出现日期
                first_date = product_first_appearance.get(product)
                if first_date is None:
                    continue
                
                # 获取商品最后销售日期（截至当前日期）
                last_sale_date = None
                if current_date_key in daily_last_sale.index and product in daily_last_sale.columns:
                    last_sale_val = daily_last_sale.loc[current_date_key, product]
                    if pd.notna(last_sale_val):
                        last_sale_date = pd.Timestamp(last_sale_val)
                
                # 🆕 计算无销售天数
                # 如果最后销售日期 == 首次出现日期，说明只在首次出现时卖过一次
                # 滞销天数 = 当前日期 - 首次出现日期
                if last_sale_date is None or last_sale_date == first_date:
                    # 从首次出现日期开始计算
                    days_no_sale = (current_date_ts - pd.Timestamp(first_date)).days
                else:
                    # 从最后销售日期开始计算
                    days_no_sale = (current_date_ts - last_sale_date).days
                
                days_no_sale_list.append((product, days_no_sale))
            
            # 转换为 Series 便于统计
            if days_no_sale_list:
                days_no_sale_series = pd.Series(
                    {p: d for p, d in days_no_sale_list}
                )
                
                # 统计各等级（互斥分级）
                if "heavy" in available_levels:
                    slow_moving_counts["heavy"] = int((days_no_sale_series >= 30).sum())
                if "medium" in available_levels:
                    slow_moving_counts["medium"] = int(((days_no_sale_series >= 15) & (days_no_sale_series < 30)).sum())
                if "light" in available_levels:
                    slow_moving_counts["light"] = int(((days_no_sale_series >= 7) & (days_no_sale_series < 15)).sum())
                if "watch" in available_levels:
                    slow_moving_counts["watch"] = int(((days_no_sale_series >= 3) & (days_no_sale_series < 7)).sum())
        
        # 计算各等级滞销率
        slow_moving_rates = {}
        for level_key in available_levels:
            slow_moving_rates[level_key] = round(
                slow_moving_counts[level_key] / total_sku_with_stock * 100, 2
            ) if total_sku_with_stock > 0 else 0
        
        total_slow_moving = sum(slow_moving_counts[k] for k in available_levels)
        total_slow_moving_rate = round(
            total_slow_moving / total_sku_with_stock * 100, 2
        ) if total_sku_with_stock > 0 else 0
        
        trend_data.append({
            "date": current_date.strftime('%Y-%m-%d'),
            # 售罄
            "soldOutCount": sold_out_count,
            "soldOutRate": sold_out_rate,
            # 滞销（总计）
            "slowMovingCount": total_slow_moving,
            "slowMovingRate": total_slow_moving_rate,
            # 滞销（分级）
            "slowMovingByLevel": {k: slow_moving_counts[k] for k in available_levels},
            "slowMovingRateByLevel": {k: slow_moving_rates[k] for k in available_levels},
            # 基数
            "totalSku": total_sku,
            "totalSkuWithStock": total_sku_with_stock
        })
    
    # 计算趋势变化（首日 vs 末日）
    first_day = trend_data[0] if trend_data else None
    last_day = trend_data[-1] if trend_data else None
    
    change_summary = None
    if first_day and last_day and len(trend_data) > 1:
        change_summary = {
            "soldOutRateChange": round(last_day["soldOutRate"] - first_day["soldOutRate"], 2),
            "slowMovingRateChange": round(last_day["slowMovingRate"] - first_day["slowMovingRate"], 2),
            "periodDays": len(trend_data)
        }
    
    return {
        "success": True,
        "data": trend_data,
        "availableLevels": available_levels,
        "trendStartDate": trend_start_date.strftime('%Y-%m-%d'),
        "dateRange": {
            "start": min_date.strftime('%Y-%m-%d'),
            "end": max_date.strftime('%Y-%m-%d')
        },
        "totalDataDays": total_data_days,
        "changeSummary": change_summary,
        # 🆕 售罄定义说明
        "soldOutDefinition": "库存=0 且 近7天有销量",
        "levelDefinitions": {
            "watch": "3天无销量",
            "light": "7天无销量",
            "medium": "15天无销量", 
            "heavy": "30天无销量"
        }
    }

@router.get("/sold-out-analysis")
async def get_sold_out_analysis(
    store_name: Optional[str] = Query(None, description="门店名称筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    days: int = Query(30, ge=7, le=90, description="分析天数")
) -> Dict[str, Any]:
    """
    获取售罄深度分析数据
    
    包含：
    - 当前售罄品数量
    - 售罄损失金额（基于日均销售额估算）
    - 售罄品类分布
    - 高频售罄品（近N天售罄>=2次）
    - 平均恢复时间
    """
    df = get_order_data(store_name)
    if df.empty:
        return {
            "success": True,
            "data": {
                "soldOutCount": 0,
                "estimatedLoss": 0,
                "byCategory": [],
                "frequentSoldOut": [],
                "avgRecoveryDays": 0
            }
        }
    
    # 检查必需字段
    date_col = None
    for col in ['日期', '下单时间']:
        if col in df.columns:
            date_col = col
            break
    
    stock_col = None
    for col in ['库存', '剩余库存', 'stock', 'remaining_stock']:
        if col in df.columns:
            stock_col = col
            break
    
    category_col = '一级分类名' if '一级分类名' in df.columns else '一级分类'
    price_col = '实收价格' if '实收价格' in df.columns else None
    
    if not date_col or not stock_col:
        return {
            "success": True,
            "data": {
                "soldOutCount": 0,
                "estimatedLoss": 0,
                "byCategory": [],
                "frequentSoldOut": [],
                "avgRecoveryDays": 0
            },
            "message": f"缺少必需字段: date={date_col}, stock={stock_col}"
        }
    
    # 准备数据
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    
    if df.empty:
        return {
            "success": True,
            "data": {
                "soldOutCount": 0,
                "estimatedLoss": 0,
                "byCategory": [],
                "frequentSoldOut": [],
                "avgRecoveryDays": 0
            }
        }
    
    # 🆕 分类筛选（支持一级分类和三级分类）
    l3_col = '三级分类名' if '三级分类名' in df.columns else '三级分类'
    
    if category and category_col in df.columns:
        if '|' in category:
            # 三级分类格式：一级分类|三级分类
            parts = category.split('|')
            l1_cat = parts[0]
            l3_cat = parts[1] if len(parts) > 1 else None
            
            df = df[df[category_col] == l1_cat]
            if l3_cat and l3_col in df.columns:
                df = df[df[l3_col] == l3_cat]
        else:
            # 一级分类
            df = df[df[category_col] == category]
        
        if df.empty:
            return {
                "success": True,
                "data": {
                    "soldOutCount": 0,
                    "estimatedLoss": 0,
                    "byCategory": [],
                    "frequentSoldOut": [],
                    "avgRecoveryDays": 0
                },
                "message": f"分类 {category} 无数据"
            }
    
    max_date = df[date_col].max()
    min_date = max_date - timedelta(days=days)
    seven_days_ago = max_date - timedelta(days=7)
    
    # 筛选分析周期内的数据
    df_period = df[df[date_col] >= min_date].copy()
    
    # ==================== 1. 当前售罄品 ====================
    # 获取每个商品的最新库存
    df_sorted = df.sort_values(date_col)
    latest_stock = df_sorted.groupby('商品名称')[stock_col].last()
    
    # 近7天有销量的商品
    recent_sales = df[df[date_col] >= seven_days_ago]
    recent_products = set(recent_sales['商品名称'].unique())
    
    # 售罄品 = 库存0 且 近7天有销量
    zero_stock_products = set(latest_stock[latest_stock == 0].index)
    sold_out_products = zero_stock_products & recent_products
    sold_out_count = len(sold_out_products)
    
    # ==================== 2. 售罄损失金额 ====================
    estimated_loss = 0
    if price_col and len(sold_out_products) > 0:
        # 计算每个售罄品的日均销售额
        sold_out_df = recent_sales[recent_sales['商品名称'].isin(sold_out_products)]
        if not sold_out_df.empty:
            # 按商品分组计算近7天总销售额
            product_sales = sold_out_df.groupby('商品名称')[price_col].sum()
            # 日均销售额
            daily_avg_sales = product_sales / 7
            # 估算损失 = 日均销售额 × 假设售罄1天
            estimated_loss = float(daily_avg_sales.sum())
    
    # ==================== 3. 售罄品类分布 ====================
    by_category = []
    if len(sold_out_products) > 0 and category_col in df.columns:
        # 获取售罄品的分类
        product_category = df[df['商品名称'].isin(sold_out_products)].groupby('商品名称')[category_col].first()
        
        # 按分类统计
        category_counts = product_category.value_counts()
        
        # 计算每个分类的损失
        for cat, count in category_counts.items():
            cat_products = product_category[product_category == cat].index
            cat_loss = 0
            if price_col:
                cat_sales = recent_sales[recent_sales['商品名称'].isin(cat_products)]
                if not cat_sales.empty:
                    cat_loss = float(cat_sales[price_col].sum() / 7)
            
            by_category.append({
                "category": cat,
                "count": int(count),
                "loss": round(cat_loss, 2)
            })
        
        # 按数量排序
        by_category.sort(key=lambda x: x["count"], reverse=True)
    
    # ==================== 4. 高频售罄品（优化版） ====================
    frequent_sold_out = []
    product_sold_out_days = {}
    product_recovery_days = {}
    
    # 🚀 优化：预计算所有数据，避免双重循环
    df_period_sorted = df_period.sort_values(date_col)
    
    # 预计算每个商品每天的库存
    daily_stock_pivot = df_period_sorted.groupby([df_period_sorted[date_col].dt.date, '商品名称'])[stock_col].last().unstack(fill_value=np.nan)
    daily_stock_pivot = daily_stock_pivot.ffill()
    
    # 预计算每个商品每天是否有销售
    daily_has_sale = df_period_sorted.groupby([df_period_sorted[date_col].dt.date, '商品名称']).size().unstack(fill_value=0)
    daily_has_sale = (daily_has_sale > 0).astype(int)
    
    # 计算7天滚动窗口内是否有销量
    rolling_7d = daily_has_sale.rolling(window=7, min_periods=1).sum()
    
    # 计算每天每个商品是否售罄（库存=0 且 近7天有销量）
    is_sold_out_matrix = (daily_stock_pivot == 0) & (rolling_7d > 0)
    
    # 统计每个商品的售罄次数（连续售罄只算一次）
    for product in is_sold_out_matrix.columns:
        sold_out_series = is_sold_out_matrix[product].dropna()
        if sold_out_series.empty:
            continue
        
        # 找出售罄开始的日期（从非售罄变为售罄）
        sold_out_starts = sold_out_series & (~sold_out_series.shift(1, fill_value=False))
        sold_out_dates = sold_out_starts[sold_out_starts].index.tolist()
        
        # 找出恢复的日期（从售罄变为非售罄）
        recovery_starts = (~sold_out_series) & sold_out_series.shift(1, fill_value=False)
        recovery_dates = recovery_starts[recovery_starts].index.tolist()
        
        # 计算恢复时间
        recovery_times = []
        for i, start_date in enumerate(sold_out_dates):
            # 找到对应的恢复日期
            recovery_after = [d for d in recovery_dates if d > start_date]
            if recovery_after:
                recovery_time = (recovery_after[0] - start_date).days
                if recovery_time > 0:
                    recovery_times.append(recovery_time)
        
        if len(sold_out_dates) >= 2:  # 至少售罄2次才算高频
            product_sold_out_days[product] = sold_out_dates
            product_recovery_days[product] = recovery_times
    
    # 生成高频售罄品列表
    product_category_map = df.groupby('商品名称')[category_col].first().to_dict() if category_col in df.columns else {}
    
    for product, dates_list in product_sold_out_days.items():
        times = len(dates_list)
        recovery_list = product_recovery_days.get(product, [])
        avg_recovery = round(sum(recovery_list) / len(recovery_list), 1) if recovery_list else 0
        
        # 获取分类
        cat = product_category_map.get(product, '未知')
        
        frequent_sold_out.append({
            "name": product,
            "times": times,
            "avgRecoveryDays": avg_recovery,
            "category": cat
        })
    
    # 按售罄次数排序，取前10
    frequent_sold_out.sort(key=lambda x: x["times"], reverse=True)
    frequent_sold_out = frequent_sold_out[:10]
    
    # ==================== 5. 平均恢复时间 ====================
    all_recovery_times = []
    for times in product_recovery_days.values():
        all_recovery_times.extend(times)
    
    avg_recovery_days = round(sum(all_recovery_times) / len(all_recovery_times), 1) if all_recovery_times else 0
    
    return {
        "success": True,
        "data": {
            "soldOutCount": sold_out_count,
            "estimatedLoss": round(estimated_loss, 2),
            "byCategory": by_category,
            "frequentSoldOut": frequent_sold_out,
            "avgRecoveryDays": avg_recovery_days
        },
        "period": {
            "start": min_date.strftime('%Y-%m-%d'),
            "end": max_date.strftime('%Y-%m-%d'),
            "days": days
        }
    }
