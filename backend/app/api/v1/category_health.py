# -*- coding: utf-8 -*-
"""
品类健康度分析 API

提供:
- 品类销售额、环比增长、波动系数、平均折扣、利润率
- 支持周期切换（7/14/30天）
- 支持下钻到三级分类
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import numpy as np

import sys
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = APP_DIR.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 尝试导入数据库
DATABASE_AVAILABLE = False
try:
    from database.connection import SessionLocal
    from database.models import Order
    from sqlalchemy import func, case, and_
    DATABASE_AVAILABLE = True
except ImportError:
    print("⚠️ 数据库模块未找到")

router = APIRouter()


class CategoryHealthItem(BaseModel):
    """品类健康度数据项"""
    name: str                    # 品类名称
    level: int                   # 分类级别 (1=一级, 3=三级)
    parent: Optional[str]        # 父级分类（三级分类时有值）
    current_revenue: float       # 本期销售额
    previous_revenue: float      # 上期销售额
    growth_rate: float           # 环比增长率 (%)
    current_quantity: int        # 本期销量
    previous_quantity: int       # 上期销量
    quantity_growth_rate: float  # 销量环比增长率 (%)
    volatility: float            # 波动系数 (CV)
    volatility_level: str        # 波动等级 (低/中/高)
    avg_discount: float          # 本期平均折扣 (如 8.5 表示 8.5折)
    prev_discount: float         # 上期平均折扣
    discount_change: float       # 折扣变化 (本期 - 上期，正数表示折扣力度减小)
    profit_margin: float         # 利润率 (%)
    daily_revenue: List[float]   # 每日销售额（用于 sparkline）


class CategoryHealthResponse(BaseModel):
    """品类健康度响应"""
    success: bool
    data: List[CategoryHealthItem]
    period: dict                 # { start, end, days }
    summary: dict                # 汇总信息


def calculate_cv(values: List[float]) -> float:
    """计算变异系数 (Coefficient of Variation)"""
    if not values or len(values) < 2:
        return 0.0
    arr = np.array(values)
    mean = np.mean(arr)
    if mean == 0:
        return 0.0
    std = np.std(arr, ddof=1)
    return round((std / mean) * 100, 1)


def get_volatility_level(cv: float) -> str:
    """根据CV值判断波动等级"""
    if cv < 20:
        return "低"
    elif cv < 40:
        return "中"
    else:
        return "高"


@router.get("/health", response_model=CategoryHealthResponse)
async def get_category_health(
    store_name: Optional[str] = Query(None, description="门店名称"),
    channel: Optional[str] = Query(None, description="渠道名称"),
    period: Optional[int] = Query(None, description="周期天数(7/14/30)，与start_date/end_date二选一"),
    start_date: Optional[str] = Query(None, description="开始日期(YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期(YYYY-MM-DD)"),
    level: int = Query(1, description="分类级别(1=一级, 3=三级)"),
    parent_category: Optional[str] = Query(None, description="父级分类（下钻时使用）")
):
    """
    获取品类健康度分析数据
    
    日期参数说明:
    - 方式1: 使用 period 参数（7/14/30天），自动计算日期范围
    - 方式2: 使用 start_date + end_date 自定义日期范围
    
    指标说明:
    - 环比增长: (本期 - 上期) / 上期 × 100%
    - 波动系数: 标准差 / 均值 × 100%
    - 平均折扣: 实售总额 / 原价总额 × 10 (如 8.5折)
    - 利润率: 利润 / 销售额 × 100%
    """
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="数据库不可用")
    
    session = SessionLocal()
    try:
        # 获取数据库中最新日期
        max_date_result = session.query(func.max(Order.date)).scalar()
        if not max_date_result:
            return CategoryHealthResponse(
                success=True,
                data=[],
                period={"start": None, "end": None, "days": 0},
                summary={"total_categories": 0, "total_revenue": 0}
            )
        
        # 处理日期类型
        if hasattr(max_date_result, 'date'):
            db_max_date = max_date_result.date()
        else:
            db_max_date = max_date_result
        
        # 计算日期范围
        if start_date and end_date:
            # 自定义日期范围
            try:
                query_start = datetime.strptime(start_date, "%Y-%m-%d").date()
                query_end = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD")
            
            period_days = (query_end - query_start).days + 1
        else:
            # 使用 period 参数
            if period not in [7, 14, 30]:
                period = 7
            period_days = period
            query_end = db_max_date
            query_start = query_end - timedelta(days=period_days - 1)
        
        # 计算上期日期范围（用于环比）
        prev_end = query_start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=period_days - 1)
        
        # 确定分类字段
        if level == 1:
            category_col = Order.category_level1
        else:
            category_col = Order.category_level3
        
        # 构建基础查询条件
        base_filters = []
        if store_name:
            base_filters.append(Order.store_name == store_name)
        if channel:
            base_filters.append(Order.channel == channel)
        if level == 3 and parent_category:
            base_filters.append(Order.category_level1 == parent_category)
        
        # 🆕 排除"耗材"分类
        excluded_categories = ['耗材']
        if level == 1:
            base_filters.append(~Order.category_level1.in_(excluded_categories))
        
        # 查询本期数据（按日期分组，用于计算波动）
        # 🔴 关键修复：actual_price是单价，必须乘以quantity才是销售额
        current_daily = session.query(
            category_col.label('category'),
            func.date(Order.date).label('day'),
            func.sum(Order.actual_price * Order.quantity).label('revenue'),  # 实收价格×销量=销售额
            func.sum(Order.original_price * Order.quantity).label('original_revenue'),
            func.sum(Order.profit).label('profit'),
            func.sum(Order.quantity).label('quantity')  # 销量
        ).filter(
            and_(
                func.date(Order.date) >= query_start,
                func.date(Order.date) <= query_end,
                category_col.isnot(None),
                category_col != '',
                *base_filters
            )
        ).group_by(category_col, func.date(Order.date)).all()
        
        # 查询上期汇总数据（包含原价用于计算折扣）
        # 🔴 关键修复：actual_price是单价，必须乘以quantity才是销售额
        previous_data = session.query(
            category_col.label('category'),
            func.sum(Order.actual_price * Order.quantity).label('revenue'),  # 实收价格×销量=销售额
            func.sum(Order.original_price * Order.quantity).label('original_revenue'),  # 原价
            func.sum(Order.quantity).label('quantity')  # 销量
        ).filter(
            and_(
                func.date(Order.date) >= prev_start,
                func.date(Order.date) <= prev_end,
                category_col.isnot(None),
                category_col != '',
                *base_filters
            )
        ).group_by(category_col).all()
        
        # 转换上期数据为字典
        prev_revenue_map = {row.category: row.revenue or 0 for row in previous_data}
        prev_original_map = {row.category: row.original_revenue or 0 for row in previous_data}
        prev_quantity_map = {row.category: row.quantity or 0 for row in previous_data}
        
        # 按品类聚合本期数据
        category_data = {}
        for row in current_daily:
            cat = row.category
            if cat not in category_data:
                category_data[cat] = {
                    'daily_revenue': [],
                    'total_revenue': 0,
                    'total_original': 0,
                    'total_profit': 0,
                    'total_quantity': 0
                }
            category_data[cat]['daily_revenue'].append(row.revenue or 0)
            category_data[cat]['total_revenue'] += row.revenue or 0
            category_data[cat]['total_original'] += row.original_revenue or 0
            category_data[cat]['total_profit'] += row.profit or 0
            category_data[cat]['total_quantity'] += row.quantity or 0
        
        # 构建结果
        results = []
        for cat, data in category_data.items():
            current_rev = data['total_revenue']
            prev_rev = prev_revenue_map.get(cat, 0)
            current_qty = data['total_quantity']
            prev_qty = prev_quantity_map.get(cat, 0)
            
            # 销售额环比增长率
            if prev_rev > 0:
                growth = round((current_rev - prev_rev) / prev_rev * 100, 1)
            else:
                growth = 100.0 if current_rev > 0 else 0.0
            
            # 销量环比增长率
            if prev_qty > 0:
                qty_growth = round((current_qty - prev_qty) / prev_qty * 100, 1)
            else:
                qty_growth = 100.0 if current_qty > 0 else 0.0
            
            # 波动系数
            cv = calculate_cv(data['daily_revenue'])
            
            # 本期平均折扣：实收价格 / 原价 × 10
            if data['total_original'] > 0:
                discount = round(data['total_revenue'] / data['total_original'] * 10, 1)
            else:
                discount = 10.0  # 无原价数据时默认原价
            
            # 上期平均折扣
            prev_original = prev_original_map.get(cat, 0)
            if prev_original > 0:
                prev_discount = round(prev_rev / prev_original * 10, 1)
            else:
                prev_discount = 10.0
            
            # 折扣变化（正数表示折扣力度减小，如从8.3变成8.5）
            discount_change = round(discount - prev_discount, 1)
            
            # 利润率：利润 / 实收价格 × 100
            if current_rev > 0:
                profit_margin = round(data['total_profit'] / current_rev * 100, 1)
            else:
                profit_margin = 0.0
            
            results.append(CategoryHealthItem(
                name=cat,
                level=level,
                parent=parent_category if level == 3 else None,
                current_revenue=round(current_rev, 2),
                previous_revenue=round(prev_rev, 2),
                growth_rate=growth,
                current_quantity=current_qty,
                previous_quantity=prev_qty,
                quantity_growth_rate=qty_growth,
                volatility=cv,
                volatility_level=get_volatility_level(cv),
                avg_discount=discount,
                prev_discount=prev_discount,
                discount_change=discount_change,
                profit_margin=profit_margin,
                daily_revenue=[round(v, 2) for v in data['daily_revenue']]
            ))
        
        # 按销售额降序排序
        results.sort(key=lambda x: x.current_revenue, reverse=True)
        
        return CategoryHealthResponse(
            success=True,
            data=results,
            period={
                "start": query_start.strftime("%Y-%m-%d"),
                "end": query_end.strftime("%Y-%m-%d"),
                "days": period_days
            },
            summary={
                "total_categories": len(results),
                "total_revenue": round(sum(r.current_revenue for r in results), 2)
            }
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
