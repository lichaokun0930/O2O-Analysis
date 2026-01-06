# -*- coding: utf-8 -*-
"""
安全模块 - JWT认证

提供:
- JWT Token生成和验证
- 密码哈希和验证
- 依赖注入获取当前用户
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import sys
from pathlib import Path

# 添加父目录到路径
APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import settings

# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer Token模式
security = HTTPBearer(auto_error=False)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问Token
    
    Args:
        data: Token负载数据
        expires_delta: 过期时间增量
    
    Returns:
        JWT Token字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建刷新Token
    
    Args:
        data: Token负载数据
        expires_delta: 过期时间增量
    
    Returns:
        JWT Token字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证Token
    
    Args:
        token: JWT Token字符串
    
    Returns:
        解码后的负载数据，验证失败返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    获取当前用户（依赖注入）
    
    Args:
        credentials: HTTP Authorization头中的凭证
    
    Returns:
        用户信息字典
    
    Raises:
        HTTPException: Token无效或过期
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查Token类型
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token类型错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


async def get_current_user_required(
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取当前用户（必须认证）
    
    与get_current_user不同，此函数要求必须提供有效Token
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# 简化的用户数据（实际项目应该从数据库读取）
# 延迟加载避免模块导入时调用bcrypt
_DEMO_USERS = None

def get_demo_users():
    """延迟加载用户数据"""
    global _DEMO_USERS
    if _DEMO_USERS is None:
        _DEMO_USERS = {
            "admin": {
                "username": "admin",
                "password_hash": get_password_hash("admin123"),
                "role": "admin",
                "name": "管理员"
            },
            "user": {
                "username": "user",
                "password_hash": get_password_hash("user123"),
                "role": "user",
                "name": "普通用户"
            }
        }
    return _DEMO_USERS


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    验证用户登录
    
    Args:
        username: 用户名
        password: 密码
    
    Returns:
        用户信息，验证失败返回None
    """
    users = get_demo_users()
    user = users.get(username)
    if not user:
        return None
    
    if not verify_password(password, user["password_hash"]):
        return None
    
    return {
        "username": user["username"],
        "role": user["role"],
        "name": user["name"]
    }

