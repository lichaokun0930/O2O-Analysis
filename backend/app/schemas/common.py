# -*- coding: utf-8 -*-
"""
通用数据模型
"""

from typing import Optional, List, Any, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import date, datetime

T = TypeVar('T')


class ResponseBase(BaseModel):
    """API响应基类"""
    success: bool = True
    message: str = "操作成功"
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    detail: Optional[Any] = None


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=50, ge=1, le=500, description="每页数量")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class DateRangeParams(BaseModel):
    """日期范围参数"""
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")


class PaginatedResponse(ResponseBase, Generic[T]):
    """分页响应"""
    data: List[T]
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")
    
    @classmethod
    def create(cls, data: List[T], total: int, page: int, page_size: int):
        total_pages = (total + page_size - 1) // page_size
        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


class SummaryItem(BaseModel):
    """摘要项"""
    label: str
    value: Any
    unit: Optional[str] = None
    trend: Optional[float] = None  # 环比变化
    trend_direction: Optional[str] = None  # up/down/stable


class ChartDataPoint(BaseModel):
    """图表数据点"""
    x: Any  # X轴值
    y: Any  # Y轴值
    category: Optional[str] = None
    label: Optional[str] = None


class FilterOption(BaseModel):
    """筛选选项"""
    value: str
    label: str
    count: Optional[int] = None

