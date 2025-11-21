"""
商品管理 API
提供商品数据的增删改查接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database.connection import get_db
from database.models import Product, Order

router = APIRouter()


# Pydantic模型（API响应格式）
class ProductResponse(BaseModel):
    id: int
    product_name: str
    barcode: Optional[str]
    category_level1: Optional[str]
    category_level3: Optional[str]
    current_price: Optional[float]
    current_cost: Optional[float]
    stock: int
    product_role: Optional[str]
    lifecycle_stage: Optional[str]
    total_sales: float
    total_orders: int
    avg_profit_margin: Optional[float]
    is_active: bool
    
    class Config:
        from_attributes = True


class ProductStats(BaseModel):
    """商品统计数据"""
    total_products: int
    active_products: int
    out_of_stock: int
    low_stock: int
    by_category: dict
    by_role: dict


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = Query(0, description="跳过记录数"),
    limit: int = Query(100, description="返回记录数", le=1000),
    category: Optional[str] = Query(None, description="分类筛选"),
    role: Optional[str] = Query(None, description="角色筛选：流量品/利润品/形象品"),
    search: Optional[str] = Query(None, description="商品名称搜索"),
    db: Session = Depends(get_db)
):
    """
    获取商品列表
    支持分页、筛选、搜索
    """
    query = db.query(Product)
    
    # 应用筛选条件
    if category:
        query = query.filter(Product.category_level1 == category)
    
    if role:
        query = query.filter(Product.product_role == role)
    
    if search:
        query = query.filter(Product.product_name.ilike(f"%{search}%"))
    
    # 分页
    products = query.offset(skip).limit(limit).all()
    
    return products


@router.get("/stats", response_model=ProductStats)
async def get_product_stats(db: Session = Depends(get_db)):
    """
    获取商品统计数据
    """
    total = db.query(Product).count()
    active = db.query(Product).filter(Product.is_active == True).count()
    out_of_stock = db.query(Product).filter(Product.stock == 0).count()
    low_stock = db.query(Product).filter(Product.stock > 0, Product.stock < 10).count()
    
    # 按分类统计
    by_category = dict(
        db.query(Product.category_level1, func.count(Product.id))
        .group_by(Product.category_level1)
        .all()
    )
    
    # 按角色统计
    by_role = dict(
        db.query(Product.product_role, func.count(Product.id))
        .filter(Product.product_role.isnot(None))
        .group_by(Product.product_role)
        .all()
    )
    
    return ProductStats(
        total_products=total,
        active_products=active,
        out_of_stock=out_of_stock,
        low_stock=low_stock,
        by_category=by_category,
        by_role=by_role
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    获取单个商品详情
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    return product


@router.get("/{product_id}/orders")
async def get_product_orders(
    product_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取商品的订单列表
    """
    # 检查商品是否存在
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 获取订单
    orders = db.query(Order).filter(
        Order.product_id == product_id
    ).order_by(desc(Order.date)).offset(skip).limit(limit).all()
    
    return {
        "product_id": product_id,
        "product_name": product.product_name,
        "total_orders": db.query(Order).filter(Order.product_id == product_id).count(),
        "orders": [
            {
                "order_id": o.order_id,
                "date": o.date.isoformat(),
                "quantity": o.quantity,
                "amount": o.amount,
                "profit": o.profit,
                "scene": o.scene,
            }
            for o in orders
        ]
    }


@router.get("/top/sales")
async def get_top_products_by_sales(
    limit: int = Query(20, description="返回数量", le=100),
    category: Optional[str] = Query(None, description="分类筛选"),
    db: Session = Depends(get_db)
):
    """
    销售额TOP商品
    """
    query = db.query(Product).filter(Product.total_sales > 0)
    
    if category:
        query = query.filter(Product.category_level1 == category)
    
    products = query.order_by(desc(Product.total_sales)).limit(limit).all()
    
    return [
        {
            "id": p.id,
            "name": p.product_name,
            "category": p.category_level1,
            "sales": p.total_sales,
            "orders": p.total_orders,
            "profit_margin": p.avg_profit_margin,
        }
        for p in products
    ]


@router.get("/top/profit")
async def get_top_products_by_profit(
    limit: int = Query(20, description="返回数量", le=100),
    db: Session = Depends(get_db)
):
    """
    利润率TOP商品
    """
    products = db.query(Product).filter(
        Product.avg_profit_margin.isnot(None),
        Product.avg_profit_margin > 0
    ).order_by(desc(Product.avg_profit_margin)).limit(limit).all()
    
    return [
        {
            "id": p.id,
            "name": p.product_name,
            "category": p.category_level1,
            "profit_margin": p.avg_profit_margin,
            "sales": p.total_sales,
        }
        for p in products
    ]


@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """
    获取所有分类列表
    """
    categories = db.query(
        Product.category_level1,
        func.count(Product.id).label('count')
    ).group_by(Product.category_level1).all()
    
    return [
        {"name": cat, "count": count}
        for cat, count in categories
        if cat
    ]
