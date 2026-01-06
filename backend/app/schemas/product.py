# -*- coding: utf-8 -*-
"""
商品相关数据模型
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from .common import ResponseBase


class ProductItem(BaseModel):
    """商品项"""
    product_name: str
    store_code: Optional[str] = None
    sales_quantity: int = Field(alias="销量")
    sales_amount: float = Field(alias="销售额")
    profit: float = Field(alias="利润额")
    profit_rate: Optional[float] = Field(None, alias="毛利率")
    
    class Config:
        populate_by_name = True


class ProductRankingSummary(BaseModel):
    """商品排行汇总"""
    total_count: int
    total_sales: float
    total_profit: float


class ProductRankingResponse(ResponseBase):
    """商品排行响应"""
    data: List[Dict[str, Any]]
    summary: ProductRankingSummary


class CategoryStats(BaseModel):
    """分类统计"""
    category: str = Field(alias="分类")
    product_count: int = Field(alias="商品数")
    sales_quantity: int = Field(alias="销量")
    sales_amount: float = Field(alias="销售额")
    profit: float = Field(alias="利润额")
    amount_ratio: float = Field(alias="销售额占比")
    profit_rate: float = Field(alias="利润率")
    
    class Config:
        populate_by_name = True


class ProductCategoryResponse(ResponseBase):
    """分类分析响应"""
    data: List[Dict[str, Any]]


class HotProduct(BaseModel):
    """热销商品"""
    product_name: str
    sales_quantity: int
    sales_amount: float
    profit: float
    rank: int


class HotProductsResponse(ResponseBase):
    """热销商品响应"""
    data: List[Dict[str, Any]]
    summary: ProductRankingSummary


class HighProfitProduct(BaseModel):
    """高利润商品"""
    product_name: str
    profit: float
    profit_per_unit: float
    sales_quantity: int
    is_new: bool = Field(default=False, description="是否新增")


class HighProfitSummary(BaseModel):
    """高利润汇总"""
    total_profit: float
    count: int


class HighProfitProductsResponse(ResponseBase):
    """高利润商品响应"""
    data: List[Dict[str, Any]]
    summary: HighProfitSummary


class InventoryItem(BaseModel):
    """库存项"""
    product_name: str
    stock: int
    sales_quantity: int
    status: str = Field(description="库存状态")


class InventorySummary(BaseModel):
    """库存汇总"""
    total_products: int
    status_counts: Dict[str, int]
    low_stock_count: int


class InventoryResponse(ResponseBase):
    """库存分析响应"""
    data: List[Dict[str, Any]]
    summary: InventorySummary

