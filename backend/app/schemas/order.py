# -*- coding: utf-8 -*-
"""
订单相关数据模型
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import date, datetime
from .common import ResponseBase, PaginatedResponse


class OrderKPI(BaseModel):
    """订单KPI指标"""
    total_orders: int = Field(description="总订单数")
    total_amount: float = Field(description="总销售额")
    total_profit: float = Field(description="总利润")
    avg_order_value: float = Field(description="平均客单价")
    avg_profit_rate: float = Field(description="平均利润率(%)")
    order_count_trend: float = Field(default=0, description="订单数环比(%)")
    amount_trend: float = Field(default=0, description="销售额环比(%)")
    profit_trend: float = Field(default=0, description="利润环比(%)")


class OrderKPIResponse(ResponseBase):
    """订单KPI响应"""
    data: OrderKPI


class TrendDataPoint(BaseModel):
    """趋势数据点"""
    date: str
    order_count: int
    amount: float
    profit: float
    avg_value: float


class OrderTrendResponse(ResponseBase):
    """订单趋势响应"""
    data: List[TrendDataPoint]
    period_days: int


class ChannelStats(BaseModel):
    """渠道统计"""
    channel: str
    order_count: int
    amount: float
    profit: float
    order_ratio: float = Field(description="订单占比(%)")
    amount_ratio: float = Field(description="销售额占比(%)")
    avg_value: float = Field(description="平均客单价")
    profit_rate: float = Field(description="利润率(%)")


class OrderChannelResponse(ResponseBase):
    """订单渠道分析响应"""
    data: List[ChannelStats]


class OrderItem(BaseModel):
    """订单项"""
    order_id: str = Field(alias="订单ID")
    date: Optional[str] = None
    product_name: Optional[str] = Field(None, alias="商品名称")
    amount: Optional[float] = Field(None, alias="实收价格")
    profit: Optional[float] = Field(None, alias="订单实际利润")
    delivery_fee: Optional[float] = Field(None, alias="物流配送费")
    channel: Optional[str] = None
    
    class Config:
        populate_by_name = True


class OrderListResponse(ResponseBase):
    """订单列表响应"""
    data: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class StoreInfo(BaseModel):
    """门店信息"""
    name: str
    order_count: int = 0
    total_amount: float = 0


class StoreListResponse(ResponseBase):
    """门店列表响应"""
    data: List[str]


class ChannelListResponse(ResponseBase):
    """渠道列表响应"""
    data: List[str]

