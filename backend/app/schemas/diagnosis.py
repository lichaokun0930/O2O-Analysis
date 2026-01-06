# -*- coding: utf-8 -*-
"""
诊断分析相关数据模型（今日必做核心）
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from .common import ResponseBase


class UrgentIssue(BaseModel):
    """紧急问题"""
    issue_type: str = Field(description="问题类型")
    count: int = Field(description="数量")
    amount: Optional[float] = Field(None, description="金额")
    icon: str = Field(default="🔴")


class WatchIssue(BaseModel):
    """关注问题"""
    issue_type: str
    count: int
    icon: str = Field(default="🟡")


class DiagnosisSummary(BaseModel):
    """诊断汇总"""
    urgent: Dict[str, UrgentIssue] = Field(description="紧急处理")
    watch: Dict[str, WatchIssue] = Field(description="关注观察")
    date: str = Field(description="数据日期")


class DiagnosisSummaryResponse(ResponseBase):
    """诊断汇总响应"""
    data: Dict[str, Any]
    date: Optional[str] = None


class OverflowOrderItem(BaseModel):
    """穿底订单项"""
    order_id: str
    date: Optional[str] = None
    product_name: Optional[str] = None
    amount: float = Field(description="订单金额")
    profit: float = Field(description="订单利润")
    loss_amount: float = Field(description="亏损金额")
    delivery_fee: Optional[float] = None
    channel: Optional[str] = None


class OverflowSummary(BaseModel):
    """穿底汇总"""
    total_count: int
    total_loss: float
    avg_loss: float
    channel_distribution: Dict[str, int] = {}
    reason_analysis: Dict[str, int] = {}


class OverflowOrdersResponse(ResponseBase):
    """穿底订单响应"""
    data: List[Dict[str, Any]]
    summary: OverflowSummary


class HighDeliverySummary(BaseModel):
    """高配送费汇总"""
    total_count: int
    total_delivery_fee: float
    avg_delivery_fee: float
    threshold: float


class HighDeliveryResponse(ResponseBase):
    """高配送费订单响应"""
    data: List[Dict[str, Any]]
    summary: HighDeliverySummary


class SlowMovingProduct(BaseModel):
    """滞销商品"""
    product_name: str
    days_no_sale: int
    level: str = Field(description="滞销级别")
    last_sale_date: Optional[str] = None


class SlowMovingSummary(BaseModel):
    """滞销汇总"""
    total_count: int
    level_counts: Dict[str, int]
    thresholds: Dict[str, int]


class SlowMovingResponse(ResponseBase):
    """滞销商品响应"""
    data: List[Dict[str, Any]]
    summary: SlowMovingSummary


class TrafficDropProduct(BaseModel):
    """流量下滑商品"""
    product_name: str
    yesterday_sales: int
    day_before_sales: int
    drop_rate: float = Field(description="下滑幅度(%)")


class TrafficDropSummary(BaseModel):
    """流量下滑汇总"""
    count: int
    zero_sales_count: int


class TrafficDropResponse(ResponseBase):
    """流量下滑响应"""
    data: List[Dict[str, Any]]
    summary: TrafficDropSummary


class ChurnCustomer(BaseModel):
    """流失客户"""
    customer_id: str
    last_order_date: str
    days_since_last: int
    order_count: int
    total_amount: float
    risk_level: str


class ChurnSummary(BaseModel):
    """流失汇总"""
    total_customers: int
    churn_count: int
    churn_rate: float
    risk_counts: Dict[str, int]
    total_ltv_at_risk: float


class CustomerChurnResponse(ResponseBase):
    """客户流失响应"""
    data: List[Dict[str, Any]]
    summary: ChurnSummary


class AOVAnomalySummary(BaseModel):
    """客单价异常汇总"""
    overall_aov: float
    upper_threshold: float
    lower_threshold: float
    total_orders: int
    abnormal_count: int
    abnormal_rate: float


class AOVAnomalyResponse(ResponseBase):
    """客单价异常响应"""
    data: Dict[str, Any]
    summary: AOVAnomalySummary

