"""
场景分析 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.connection import get_db
from database.models import Order, SceneTag

router = APIRouter()


@router.get("/distribution")
async def get_scene_distribution(db: Session = Depends(get_db)):
    """
    场景分布统计
    """
    scene_data = db.query(
        Order.scene,
        func.count(Order.id).label('order_count'),
        func.sum(Order.amount).label('total_amount'),
        func.sum(Order.profit).label('total_profit')
    ).filter(
        Order.scene.isnot(None)
    ).group_by(Order.scene).all()
    
    return [
        {
            "scene": row.scene,
            "orders": row.order_count,
            "amount": float(row.total_amount or 0),
            "profit": float(row.total_profit or 0),
        }
        for row in scene_data
    ]


@router.get("/time-period")
async def get_time_period_analysis(db: Session = Depends(get_db)):
    """
    时段分析
    """
    period_data = db.query(
        Order.time_period,
        func.count(Order.id).label('order_count'),
        func.sum(Order.amount).label('total_amount')
    ).filter(
        Order.time_period.isnot(None)
    ).group_by(Order.time_period).all()
    
    return [
        {
            "period": row.time_period,
            "orders": row.order_count,
            "amount": float(row.total_amount or 0),
        }
        for row in period_data
    ]
