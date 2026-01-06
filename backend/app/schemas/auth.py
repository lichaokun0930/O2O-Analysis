# -*- coding: utf-8 -*-
"""
认证相关数据模型
"""

from typing import Optional
from pydantic import BaseModel, Field
from .common import ResponseBase


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=4, max_length=100, description="密码")


class UserInfo(BaseModel):
    """用户信息"""
    username: str
    name: str
    role: str


class LoginResponse(ResponseBase):
    """登录响应"""
    access_token: str = Field(description="访问Token")
    refresh_token: str = Field(description="刷新Token")
    token_type: str = Field(default="bearer", description="Token类型")
    expires_in: int = Field(description="过期时间（秒）")
    user: UserInfo = Field(description="用户信息")


class TokenRefreshRequest(BaseModel):
    """Token刷新请求"""
    refresh_token: str = Field(..., description="刷新Token")


class TokenRefreshResponse(ResponseBase):
    """Token刷新响应"""
    access_token: str = Field(description="新的访问Token")
    expires_in: int = Field(description="过期时间（秒）")


class CurrentUserResponse(ResponseBase):
    """当前用户响应"""
    user: UserInfo

