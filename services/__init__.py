# -*- coding: utf-8 -*-
"""
订单数据看板 - Service层
业务逻辑服务模块

从Dash回调中抽取的业务逻辑，提供：
- 订单分析服务 (OrderService)
- 商品分析服务 (ProductService)  
- 诊断分析服务 (DiagnosisService)
- 营销分析服务 (MarketingService)
- 配送分析服务 (DeliveryService)
- 客户流失分析服务 (CustomerService)
- 场景分析服务 (SceneService)
- 报表导出服务 (ReportService)
- 数据管理服务 (DataManagementService)

版本: v1.0
创建日期: 2026-01-05
"""

from .base_service import BaseService
from .order_service import OrderService
from .product_service import ProductService
from .diagnosis_service import DiagnosisService
from .marketing_service import MarketingService
from .delivery_service import DeliveryService
from .customer_service import CustomerService
from .scene_service import SceneService
from .report_service import ReportService
from .data_management_service import DataManagementService

__all__ = [
    'BaseService',
    'OrderService',
    'ProductService',
    'DiagnosisService',
    'MarketingService',
    'DeliveryService',
    'CustomerService',
    'SceneService',
    'ReportService',
    'DataManagementService',
]

__version__ = '1.0.0'

