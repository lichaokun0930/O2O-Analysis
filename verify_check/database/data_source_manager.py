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
                          end_date: datetime = None,
                          split_consumables: bool = True) -> dict:
        """
        从数据库加载数据
        
        Args:
            store_name: 门店名称
            start_date: 开始日期
            end_date: 结束日期
            split_consumables: 是否分离耗材数据
            
        Returns:
            如果split_consumables=True:
                {'full': 完整数据(含耗材), 'display': 展示数据(不含耗材)}
            如果split_consumables=False:
                {'full': 完整数据(含耗材)}
        """
        print(f"[Database] 加载数据...")
        print(f"[Database] 参数 - 门店: {store_name}, 开始日期: {start_date}, 结束日期: {end_date}")
        
        db = next(get_db())
        
        try:
            # 构建查询 - JOIN Product表获取店内码、库存和成本
            from database.models import Product
            query = db.query(
                Order, 
                Product.store_code,
                Product.stock,  # 🆕 获取库存
                Product.current_cost  # 🆕 获取成本
            ).outerjoin(
                Product, Order.barcode == Product.barcode
            )
            
            # 过滤条件
            if store_name:
                print(f"[Database] 应用门店过滤: {store_name}")
                query = query.filter(Order.store_name == store_name)
            
            # ✅ 修复单日查询：确保日期范围包含完整的一天
            if start_date:
                # 转换为datetime对象，设置为当天00:00:00
                from datetime import datetime, timedelta
                if isinstance(start_date, str):
                    start_date = datetime.fromisoformat(start_date)
                if not isinstance(start_date, datetime):
                    # 如果是date对象，转换为datetime
                    start_date = datetime.combine(start_date, datetime.min.time())
                
                print(f"[Database] 应用开始日期过滤: {start_date.date()} 00:00:00")
                query = query.filter(Order.date >= start_date)
            
            if end_date:
                # 转换为datetime对象，设置为当天23:59:59
                from datetime import datetime, timedelta
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date)
                if not isinstance(end_date, datetime):
                    # 如果是date对象，转换为datetime
                    end_date = datetime.combine(end_date, datetime.max.time())
                else:
                    # 如果已是datetime，设置时间为当天结束
                    end_date = datetime.combine(end_date.date(), datetime.max.time())
                
                print(f"[Database] 应用结束日期过滤: {end_date.date()} 23:59:59 (包含当天)")
                query = query.filter(Order.date <= end_date)
            
            # 执行查询
            print(f"[Database] 执行查询...")
            results = query.all()
            print(f"[Database] 查询到 {len(results)} 条记录")
            
            # 🔍 调试: 检查前5条记录的订单ID
            if results:
                print(f"[Database] 前5条记录的订单ID:")
                for i, (order, store_code, stock, cost) in enumerate(results[:5]):
                    print(f"   {i+1}. order_id='{order.order_id}' (type={type(order.order_id).__name__})")
            
            # 转换为DataFrame
            data = []
            for order, store_code, stock, cost in results:  # 🆕 解包时增加stock和cost
                data.append({
                    # 基础订单信息
                    '订单ID': order.order_id,
                    '下单时间': order.date,
                    '日期': order.date,  # 兼容字段
                    '门店名称': order.store_name,
                    '门店ID': order.store_name if order.store_name else '',  # 使用store_name替代不存在的store_id
                    '收货地址': order.address if hasattr(order, 'address') else '',
                    '城市名称': '',  # Order模型中没有city字段
                    
                    # 商品信息
                    '商品名称': order.product_name,
                    '商品条形码': order.barcode,
                    '条码': order.barcode,  # 兼容字段
                    '店内码': store_code if store_code else '',  # ✨ 从Product表JOIN获取
                    '一级分类名': order.category_level1,
                    '三级分类名': order.category_level3,
                    
                    # 价格成本
                    '商品实售价': order.price,
                    '商品原价': order.original_price if order.original_price else order.price,
                    '商品采购成本': cost if cost is not None else 0.0,  # 🆕 优先使用Product表的current_cost
                    '成本': cost if cost is not None else 0.0,  # 兼容字段
                    '实收价格': order.actual_price if order.actual_price else order.price,
                    
                    # 销量金额
                    '销量': order.quantity,
                    '销售数量': order.quantity,  # 兼容字段
                    '月售': order.quantity,  # 兼容字段
                    '库存': stock if stock is not None else 0,  # 🆕 从Product表获取实际库存
                    '剩余库存': stock if stock is not None else 0,  # 🆕 兼容字段,使用实际库存
                    '订单零售额': order.price * order.quantity,
                    '实收金额': (order.actual_price if order.actual_price else order.price) * order.quantity,
                    '用户支付金额': (order.actual_price if order.actual_price else order.price) * order.quantity,
                    # 🔄 从amount字段读取Excel的"预计订单收入"（不再用price*quantity计算）
                    '预计订单收入': order.amount if order.amount else (order.price * order.quantity),
                    # ✅ 从数据库读取Excel导入的"利润额"字段（存储在profit字段中）
                    '利润额': order.profit if order.profit else 0.0,
                    
                    # 费用
                    '物流配送费': order.delivery_fee if order.delivery_fee else 0.0,
                    '平台佣金': order.commission if order.commission else 0.0,
                    '平台服务费': order.platform_service_fee if order.platform_service_fee else 0.0,  # 修复:添加平台服务费映射
                    
                    # ✨ 营销活动字段
                    '用户支付配送费': order.user_paid_delivery_fee if order.user_paid_delivery_fee else 0.0,
                    '配送费减免金额': order.delivery_discount if order.delivery_discount else 0.0,
                    '满减金额': order.full_reduction if order.full_reduction else 0.0,
                    '商品减免金额': order.product_discount if order.product_discount else 0.0,
                    '商家代金券': order.merchant_voucher if order.merchant_voucher else 0.0,
                    '商家承担部分券': order.merchant_share if order.merchant_share else 0.0,
                    '打包袋金额': order.packaging_fee if order.packaging_fee else 0.0,
                    # ✅ 新增营销维度字段
                    '满赠金额': order.gift_amount if hasattr(order, 'gift_amount') and order.gift_amount else 0.0,
                    '商家其他优惠': order.other_merchant_discount if hasattr(order, 'other_merchant_discount') and order.other_merchant_discount else 0.0,
                    '新客减免金额': order.new_customer_discount if hasattr(order, 'new_customer_discount') and order.new_customer_discount else 0.0,
                    # ✅ 新增利润维度字段
                    '企客后返': order.corporate_rebate if hasattr(order, 'corporate_rebate') and order.corporate_rebate else 0.0,
                    # ✅ 新增配送平台字段
                    '配送平台': order.delivery_platform if hasattr(order, 'delivery_platform') and order.delivery_platform else '',
                    
                    # ✨ 配送信息（Order模型中没有此字段）
                    '配送距离': 0.0,
                    
                    # 渠道场景
                    '渠道': order.channel if order.channel else '',
                    '场景': order.scene if order.scene else '',
                    '时段': order.time_period if order.time_period else '',
                })
            
            df = pd.DataFrame(data)
            
            print(f"[Database] 查询结果: {len(df):,} 行")
            
            # 🔍 检查渠道分布
            if '渠道' in df.columns:
                channel_counts = df['渠道'].value_counts()
                print(f"[Database] 渠道分布:")
                for ch, cnt in channel_counts.items():
                    print(f"   {ch}: {cnt:,} 行")
                    
                # 🔍 特别检查闪购小程序
                xiaochengxu_count = (df['渠道'] == '闪购小程序').sum()
                print(f"[Database] 🔍 '闪购小程序'数据: {xiaochengxu_count} 行")
            
            # 🔄 2025-11-19: 数据分离策略
            # - df_full: 完整数据(含耗材) → 用于利润计算
            # - df_display: 展示数据(不含耗材) → 用于分析图表
            print(f"[Database] ✅ 保留耗材数据 (包含购物袋等成本)")
            
            df_full = df.copy()
            
            if split_consumables and '一级分类名' in df.columns:
                df_display = df[df['一级分类名'] != '耗材'].copy()
                consumable_count = len(df_full) - len(df_display)
                
                print(f"[Database] 📊 数据分离完成:")
                print(f"   - 完整数据(含耗材): {len(df_full):,} 行")
                print(f"   - 展示数据(不含耗材): {len(df_display):,} 行")
                print(f"   - 耗材数据: {consumable_count:,} 行")
                
                self.current_source = 'database'
                return {
                    'full': df_full,
                    'display': df_display
                }
            else:
                print(f"[Database] 📊 返回完整数据: {len(df_full):,} 行 (不分离)")
                self.current_source = 'database'
                return {
                    'full': df_full,
                    'display': df_full.copy()
                }
            
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
