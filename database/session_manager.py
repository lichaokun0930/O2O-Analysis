#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库会话管理器 - 企业级优化
用途: 统一管理数据库会话，防止连接泄漏
"""

from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy.orm import Session
from database.connection import SessionLocal, engine
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """
    数据库会话管理器
    提供统一的会话管理接口，确保会话正确关闭
    """
    
    @staticmethod
    @contextmanager
    def get_session() -> Generator[Session, None, None]:
        """
        获取数据库会话（上下文管理器）
        
        使用示例:
            with SessionManager.get_session() as session:
                orders = session.query(Order).all()
                return orders
        
        特性:
            - 自动提交成功的事务
            - 自动回滚失败的事务
            - 自动关闭会话
            - 防止连接泄漏
        """
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            session.close()
    
    @staticmethod
    @contextmanager
    def get_readonly_session() -> Generator[Session, None, None]:
        """
        获取只读会话（不自动提交）
        
        使用示例:
            with SessionManager.get_readonly_session() as session:
                orders = session.query(Order).all()
                return orders
        
        特性:
            - 不自动提交（只读操作）
            - 自动回滚（如果有未提交的更改）
            - 自动关闭会话
            - 性能更好（无提交开销）
        """
        session = SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"数据库会话错误: {e}")
            raise
        finally:
            session.close()
    
    @staticmethod
    def execute_query(query_func, readonly=True):
        """
        执行查询函数
        
        Args:
            query_func: 查询函数，接收session参数
            readonly: 是否只读（默认True）
        
        使用示例:
            def get_orders(session):
                return session.query(Order).all()
            
            orders = SessionManager.execute_query(get_orders)
        
        Returns:
            查询结果
        """
        session_context = (
            SessionManager.get_readonly_session() 
            if readonly 
            else SessionManager.get_session()
        )
        
        with session_context as session:
            return query_func(session)
    
    @staticmethod
    def get_connection_pool_status():
        """
        获取连接池状态
        
        Returns:
            dict: 连接池状态信息
        """
        pool = engine.pool
        return {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'total': pool.size() + pool.overflow()
        }


# 便捷函数
def get_db_session():
    """获取数据库会话（便捷函数）"""
    return SessionManager.get_session()


def get_readonly_session():
    """获取只读会话（便捷函数）"""
    return SessionManager.get_readonly_session()


# 使用示例
if __name__ == '__main__':
    from database.models import Order
    
    # 示例1: 只读查询
    print("示例1: 只读查询")
    with get_readonly_session() as session:
        count = session.query(Order).count()
        print(f"订单总数: {count}")
    
    # 示例2: 写入操作
    print("\n示例2: 写入操作")
    with get_db_session() as session:
        # 这里可以进行增删改操作
        # session.add(new_order)
        # session.delete(old_order)
        pass
    
    # 示例3: 使用execute_query
    print("\n示例3: 使用execute_query")
    def get_store_count(session):
        from sqlalchemy import func
        return session.query(func.count(func.distinct(Order.store_name))).scalar()
    
    store_count = SessionManager.execute_query(get_store_count)
    print(f"门店数量: {store_count}")
    
    # 示例4: 查看连接池状态
    print("\n示例4: 连接池状态")
    status = SessionManager.get_connection_pool_status()
    print(f"连接池大小: {status['size']}")
    print(f"已签入: {status['checked_in']}")
    print(f"已签出: {status['checked_out']}")
    print(f"溢出: {status['overflow']}")
    print(f"总计: {status['total']}")
