"""
订单管理 API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime, timedelta

from database.connection import get_db
from database.models import Order

router = APIRouter()


@router.get("/")
async def get_orders(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    scene: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取订单列表"""
    query = db.query(Order)
    
    if start_date:
        query = query.filter(Order.date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Order.date <= datetime.fromisoformat(end_date))
    if scene:
        query = query.filter(Order.scene == scene)
    
    orders = query.order_by(desc(Order.date)).offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "total": total,
        "orders": [
            {
                "id": o.id,
                "order_id": o.order_id,
                "date": o.date.isoformat(),
                "product_name": o.product_name,
                "amount": o.amount,
                "profit": o.profit,
                "scene": o.scene,
            }
            for o in orders
        ]
    }


@router.get("/stats")
async def get_order_stats(
    days: int = Query(30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取订单统计"""
    start_date = datetime.now() - timedelta(days=days)
    
    total_orders = db.query(func.count(Order.id)).filter(Order.date >= start_date).scalar()
    total_amount = db.query(func.sum(Order.amount)).filter(Order.date >= start_date).scalar() or 0
    total_profit = db.query(func.sum(Order.profit)).filter(Order.date >= start_date).scalar() or 0
    
    return {
        "period_days": days,
        "total_orders": total_orders,
        "total_amount": float(total_amount),
        "total_profit": float(total_profit),
        "avg_order_value": float(total_amount / total_orders) if total_orders > 0 else 0,
    }
