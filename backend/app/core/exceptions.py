# -*- coding: utf-8 -*-
"""
异常处理模块

定义API异常类和全局异常处理器
"""

from typing import Optional, Any, Dict
from fastapi import HTTPException, status


class APIException(HTTPException):
    """API基础异常"""
    
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "服务器内部错误",
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundException(APIException):
    """资源未找到异常"""
    
    def __init__(self, detail: str = "资源未找到"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class UnauthorizedException(APIException):
    """未授权异常"""
    
    def __init__(self, detail: str = "未授权访问"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenException(APIException):
    """禁止访问异常"""
    
    def __init__(self, detail: str = "禁止访问"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ValidationException(APIException):
    """验证异常"""
    
    def __init__(self, detail: str = "数据验证失败"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class ServiceException(APIException):
    """服务异常"""
    
    def __init__(self, detail: str = "服务处理失败"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class DatabaseException(APIException):
    """数据库异常"""
    
    def __init__(self, detail: str = "数据库操作失败"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class CacheException(APIException):
    """缓存异常"""
    
    def __init__(self, detail: str = "缓存操作失败"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

