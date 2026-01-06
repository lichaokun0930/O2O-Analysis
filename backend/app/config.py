# -*- coding: utf-8 -*-
"""
应用配置

支持从环境变量和.env文件加载配置
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用信息
    APP_NAME: str = "订单数据看板 API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["*"]
    
    # JWT配置
    JWT_SECRET_KEY: str = "order-dashboard-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "o2o_dashboard"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1  # 使用DB 1，与O2O比价看板(DB 0)隔离
    REDIS_PASSWORD: Optional[str] = None
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 500
    
    # 缓存配置
    CACHE_TTL_SHORT: int = 300      # 5分钟
    CACHE_TTL_MEDIUM: int = 1800    # 30分钟
    CACHE_TTL_LONG: int = 3600      # 1小时
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略 .env 中多余的变量


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的配置实例"""
    return Settings()


# 全局配置实例
settings = get_settings()

