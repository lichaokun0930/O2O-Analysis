"""
数据分析 API
提供四象限、趋势等分析接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict

from database.connection import get_db
from database.models import Product, Order

router = APIRouter()


@router.get("/quadrant")
async def get_quadrant_analysis(db: Session = Depends(get_db)):
    """
    四象限分析
    返回商品的利润率 × 动销指数分布
    """
    # 这里简化版本，实际应该从缓存表读取
    # 或者调用现有的分析函数
    
    products = db.query(Product).filter(
        Product.total_sales > 0
    ).all()
    
    result = {
        "high_profit_high_sales": [],
        "high_profit_low_sales": [],
        "low_profit_high_sales": [],
        "low_profit_low_sales": [],
    }
    
    # 简单分类（实际应该用更复杂的算法）
    for p in products:
        if not p.avg_profit_margin:
            continue
            
        item = {
            "id": p.id,
            "name": p.product_name,
            "profit_margin": p.avg_profit_margin,
            "sales": p.total_sales,
            "category": p.category_level1,
        }
        
        if p.avg_profit_margin > 30:
            if p.total_sales > 1000:
                result["high_profit_high_sales"].append(item)
            else:
                result["high_profit_low_sales"].append(item)
        else:
            if p.total_sales > 1000:
                result["low_profit_high_sales"].append(item)
            else:
                result["low_profit_low_sales"].append(item)
    
    return result


@router.get("/trend")
async def get_trend_analysis(
    period: str = "day",  # day, week, month
    db: Session = Depends(get_db)
):
    """
    趋势分析
    """
    # 按日期分组统计
    if period == "day":
        date_trunc = func.date(Order.date)
    elif period == "week":
        date_trunc = func.date_trunc('week', Order.date)
    else:
        date_trunc = func.date_trunc('month', Order.date)
    
    trend_data = db.query(
        date_trunc.label('period'),
        func.sum(Order.amount).label('total_amount'),
        func.sum(Order.profit).label('total_profit'),
        func.count(Order.id).label('order_count')
    ).group_by('period').order_by('period').all()
    
    return [
        {
            "period": str(row.period),
            "amount": float(row.total_amount or 0),
            "profit": float(row.total_profit or 0),
            "orders": row.order_count,
        }
        for row in trend_data
    ]


@router.get("/category-analysis")
async def get_category_analysis(db: Session = Depends(get_db)):
    """
    分类分析
    """
    category_data = db.query(
        Product.category_level1,
        func.count(Product.id).label('product_count'),
        func.sum(Product.total_sales).label('total_sales'),
        func.avg(Product.avg_profit_margin).label('avg_margin')
    ).group_by(Product.category_level1).all()
    
    return [
        {
            "category": row.category_level1,
            "product_count": row.product_count,
            "total_sales": float(row.total_sales or 0),
            "avg_margin": float(row.avg_margin or 0),
        }
        for row in category_data
        if row.category_level1
    ]
