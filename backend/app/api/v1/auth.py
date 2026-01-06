# -*- coding: utf-8 -*-
"""
认证 API

提供:
- 用户登录
- Token刷新
- 当前用户信息
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta

import sys
from pathlib import Path
APP_DIR = Path(__file__).resolve().parent.parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user_required,
    authenticate_user,
)
from schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserInfo,
    CurrentUserResponse,
)
from config import settings

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    用户登录
    
    默认账号：
    - admin / admin123 (管理员)
    - user / user123 (普通用户)
    """
    user = authenticate_user(request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成Token
    token_data = {
        "sub": user["username"],
        "role": user["role"],
        "name": user["name"]
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserInfo(
            username=user["username"],
            role=user["role"],
            name=user["name"]
        )
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(request: TokenRefreshRequest):
    """刷新Token"""
    payload = verify_token(request.refresh_token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新Token"
        )
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token类型错误"
        )
    
    # 生成新的访问Token
    token_data = {
        "sub": payload.get("sub"),
        "role": payload.get("role"),
        "name": payload.get("name")
    }
    
    new_access_token = create_access_token(token_data)
    
    return TokenRefreshResponse(
        access_token=new_access_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(user: dict = Depends(get_current_user_required)):
    """获取当前用户信息"""
    return CurrentUserResponse(
        user=UserInfo(
            username=user.get("sub"),
            role=user.get("role"),
            name=user.get("name")
        )
    )


@router.post("/logout")
async def logout():
    """
    登出
    
    客户端应删除本地存储的Token
    """
    return {"success": True, "message": "已登出"}

