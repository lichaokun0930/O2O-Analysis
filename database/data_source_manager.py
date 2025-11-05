"""
P2任务：数据源管理器
支持从Excel或数据库加载数据
"""

import sys
from pathlib import Path
import pandas as pd
from typing import Literal
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.connection import get_db
from database.models import Order, Product
from 真实数据处理器 import RealDataProcessor


class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self):
        self.processor = RealDataProcessor()
        self.current_source = 'excel'  # 默认Excel
    
    def load_from_excel(self, file_path: str = None) -> pd.DataFrame:
        """从Excel加载数据"""
        if file_path is None:
            file_path = r"门店数据\比价看板模块\订单数据-本店.xlsx"
        
        print(f"[Excel] 加载数据: {file_path}")
        
        try:
            # 加载
            df = pd.read_excel(file_path)
            print(f"[Excel] 原始数据: {len(df):,} 行")
            
            # 标准化
            df = self.processor.standardize_sales_data(df)
            
            # 业务过滤
            if '一级分类名' in df.columns:
                df = df[df['一级分类名'] != '耗材'].copy()
            if '渠道' in df.columns:
                df = df[~df['渠道'].str.contains('咖啡', na=False)].copy()
            
            print(f"[Excel] 过滤后: {len(df):,} 行")
            
            self.current_source = 'excel'
            return df
            
        except Exception as e:
            print(f"[Excel] 加载失败: {str(e)}")
            return pd.DataFrame()
    
    def load_from_database(self, 
                          store_name: str = None,
                          start_date: datetime = None,
                          end_date: datetime = None) -> pd.DataFrame:
        """从数据库加载数据"""
        print(f"[Database] 加载数据...")
        
        db = next(get_db())
        
        try:
            # 构建查询
            query = db.query(Order)
            
            # 过滤条件
            if store_name:
                query = query.filter(Order.store_name == store_name)
            if start_date:
                query = query.filter(Order.date >= start_date)
            if end_date:
                query = query.filter(Order.date <= end_date)
            
            # 执行查询
            orders = query.all()
            
            # 转换为DataFrame
            data = []
            for order in orders:
                data.append({
                    '订单ID': order.order_id,
                    '日期': order.date,
                    '门店名称': order.store_name,
                    '商品名称': order.product_name,
                    '商品条形码': order.barcode,
                    '一级分类名': order.category_level1,
                    '三级分类名': order.category_level3,
                    '商品实售价': order.price,
                    '商品采购成本': order.cost,
                    '销售数量': order.quantity,
                    '实收金额': order.amount,
                    '渠道': order.channel,
                    '场景': order.scene,
                    '时段': order.time_period,
                })
            
            df = pd.DataFrame(data)
            
            print(f"[Database] 查询结果: {len(df):,} 行")
            
            self.current_source = 'database'
            return df
            
        except Exception as e:
            print(f"[Database] 加载失败: {str(e)}")
            return pd.DataFrame()
        finally:
            db.close()
    
    def load_data(self, 
                  source: Literal['excel', 'database'] = 'excel',
                  **kwargs) -> pd.DataFrame:
        """
        统一数据加载接口
        
        Args:
            source: 数据源类型 ('excel' 或 'database')
            **kwargs: 
                - file_path: Excel文件路径（source='excel'时）
                - store_name: 门店名称（source='database'时）
                - start_date: 起始日期（source='database'时）
                - end_date: 结束日期（source='database'时）
        """
        if source == 'excel':
            file_path = kwargs.get('file_path')
            return self.load_from_excel(file_path)
        
        elif source == 'database':
            store_name = kwargs.get('store_name')
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            return self.load_from_database(store_name, start_date, end_date)
        
        else:
            raise ValueError(f"不支持的数据源: {source}")
    
    def get_available_stores(self) -> list:
        """获取数据库中的门店列表"""
        db = next(get_db())
        try:
            stores = db.query(Order.store_name).distinct().all()
            return [s[0] for s in stores if s[0]]
        finally:
            db.close()
    
    def get_date_range(self) -> tuple:
        """获取数据库中的日期范围"""
        db = next(get_db())
        try:
            from sqlalchemy import func
            result = db.query(
                func.min(Order.date),
                func.max(Order.date)
            ).first()
            return result
        finally:
            db.close()
    
    def get_database_stats(self) -> dict:
        """获取数据库统计信息"""
        db = next(get_db())
        try:
            stats = {
                'products': db.query(Product).count(),
                'orders': db.query(Order).count(),
                'stores': db.query(Order.store_name).distinct().count(),
            }
            
            date_range = self.get_date_range()
            if date_range[0]:
                stats['start_date'] = date_range[0].strftime('%Y-%m-%d')
                stats['end_date'] = date_range[1].strftime('%Y-%m-%d')
            
            return stats
        finally:
            db.close()


# 测试代码
if __name__ == "__main__":
    manager = DataSourceManager()
    
    print("\n=== 测试Excel数据源 ===")
    df_excel = manager.load_data(source='excel')
    print(f"Excel数据: {len(df_excel)} 行")
    if not df_excel.empty:
        print(df_excel.head(3))
    
    print("\n=== 测试数据库数据源 ===")
    df_db = manager.load_data(source='database')
    print(f"数据库数据: {len(df_db)} 行")
    if not df_db.empty:
        print(df_db.head(3))
    
    print("\n=== 数据库统计 ===")
    stats = manager.get_database_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n=== 可用门店 ===")
    stores = manager.get_available_stores()
    for store in stores[:5]:
        print(f"  - {store}")
