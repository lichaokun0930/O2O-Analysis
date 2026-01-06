# -*- coding: utf-8 -*-
"""
Pydantic 数据模型
"""

from .common import (
    ResponseBase,
    PaginatedResponse,
    PaginationParams,
    DateRangeParams,
    ErrorResponse,
)
from .auth import (
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserInfo,
)
from .order import (
    OrderKPIResponse,
    OrderTrendResponse,
    OrderListResponse,
    OrderChannelResponse,
    OrderItem,
)
from .diagnosis import (
    DiagnosisSummaryResponse,
    OverflowOrdersResponse,
    HighDeliveryResponse,
    SlowMovingResponse,
    TrafficDropResponse,
    CustomerChurnResponse,
)
from .product import (
    ProductRankingResponse,
    ProductCategoryResponse,
    HotProductsResponse,
    HighProfitProductsResponse,
)

__all__ = [
    # Common
    'ResponseBase',
    'PaginatedResponse',
    'PaginationParams',
    'DateRangeParams',
    'ErrorResponse',
    # Auth
    'LoginRequest',
    'LoginResponse',
    'TokenRefreshRequest',
    'TokenRefreshResponse',
    'UserInfo',
    # Order
    'OrderKPIResponse',
    'OrderTrendResponse',
    'OrderListResponse',
    'OrderChannelResponse',
    'OrderItem',
    # Diagnosis
    'DiagnosisSummaryResponse',
    'OverflowOrdersResponse',
    'HighDeliveryResponse',
    'SlowMovingResponse',
    'TrafficDropResponse',
    'CustomerChurnResponse',
    # Product
    'ProductRankingResponse',
    'ProductCategoryResponse',
    'HotProductsResponse',
    'HighProfitProductsResponse',
]

