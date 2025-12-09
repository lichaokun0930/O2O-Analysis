"""
P2任务：数据源管理器
支持从Excel或数据库加载数据

✅ 2025-12-04: 统一字段映射配置
- 所有数据库字段到中文显示名的映射统一在此文件维护
- 新增字段时只需在 DB_FIELD_MAPPING 中添加映射即可
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


# ========================================
# 📌 统一字段映射配置表
# ========================================
# 格式: '中文显示名': ('数据库字段名', 默认值, 是否必须hasattr检查)
# 新增字段时只需在这里添加一行即可，无需修改其他代码
# ========================================
DB_FIELD_MAPPING = {
    # ===== 基础订单信息 =====
    '订单ID': ('order_id', '', False),
    '订单编号': ('order_number', '', True),  # ✅ 新增字段示例
    '下单时间': ('date', None, False),
    '日期': ('date', None, False),  # 兼容字段
    '门店名称': ('store_name', '', False),
    '门店ID': ('store_id', '', True),
    '城市名称': ('city', '', True),
    
    # ===== 商品信息 =====
    '商品名称': ('product_name', '', False),
    '商品条形码': ('barcode', '', False),
    '条码': ('barcode', '', False),  # 兼容字段
    '店内码': ('store_code', '', True),  # 特殊处理，见下方
    '一级分类名': ('category_level1', '', False),
    '三级分类名': ('category_level3', '', False),
    
    # ===== 价格成本 =====
    '商品实售价': ('price', 0.0, False),
    '商品原价': ('original_price', None, False),  # 特殊处理：fallback到price
    '商品采购成本': ('cost', 0.0, False),
    '成本': ('cost', 0.0, False),  # 兼容字段
    '实收价格': ('actual_price', None, False),  # 特殊处理：fallback到price
    
    # ===== 销量金额 =====
    '销量': ('quantity', 1, False),
    '销售数量': ('quantity', 1, False),  # 兼容字段
    '月售': ('quantity', 1, False),  # 兼容字段
    '库存': ('remaining_stock', 0, False),
    '剩余库存': ('remaining_stock', 0, False),
    '预计订单收入': ('amount', None, False),  # 特殊处理
    '利润额': ('profit', 0.0, False),
    
    # ===== 费用 =====
    '物流配送费': ('delivery_fee', 0.0, False),
    '平台佣金': ('commission', 0.0, False),
    '平台服务费': ('platform_service_fee', 0.0, False),
    
    # ===== 营销活动字段 =====
    '用户支付配送费': ('user_paid_delivery_fee', 0.0, False),
    '配送费减免金额': ('delivery_discount', 0.0, False),
    '满减金额': ('full_reduction', 0.0, False),
    '商品减免金额': ('product_discount', 0.0, False),
    '商家代金券': ('merchant_voucher', 0.0, False),
    '商家承担部分券': ('merchant_share', 0.0, False),
    '打包袋金额': ('packaging_fee', 0.0, False),
    '满赠金额': ('gift_amount', 0.0, True),
    '商家其他优惠': ('other_merchant_discount', 0.0, True),
    '新客减免金额': ('new_customer_discount', 0.0, True),
    
    # ===== 利润维度字段 =====
    '企客后返': ('corporate_rebate', 0.0, True),
    
    # ===== 配送信息 =====
    '配送平台': ('delivery_platform', '', True),
    '配送距离': ('delivery_distance', 0.0, True),
    '收货地址': ('address', '', False),  # ✅ 新增：客户地址字段
    
    # ===== 渠道场景 =====
    '渠道': ('channel', '', False),
    '场景': ('scene', '', False),
    '时段': ('time_period', '', False),
}


def get_field_value(order, field_name: str, default_value, need_hasattr: bool):
    """
    安全获取字段值
    
    Args:
        order: Order对象
        field_name: 数据库字段名
        default_value: 默认值
        need_hasattr: 是否需要检查hasattr
    """
    if need_hasattr:
        if hasattr(order, field_name):
            val = getattr(order, field_name)
            return val if val is not None else default_value
        return default_value
    else:
        val = getattr(order, field_name, default_value)
        return val if val is not None else default_value


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
            # 构建查询 - JOIN Product表获取店内码(不再JOIN成本和库存,Order表已有)
            from database.models import Product
            query = db.query(
                Order, 
                Product.store_code
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
                # ✅ 修复：先转换类型，再设置时间为当天结束
                from datetime import datetime, timedelta
                
                # 第一步：统一转换为datetime对象
                if isinstance(end_date, str):
                    end_date = datetime.fromisoformat(end_date)
                elif not isinstance(end_date, datetime):
                    # 如果是date对象，转换为datetime
                    end_date = datetime.combine(end_date, datetime.min.time())
                
                # 第二步：设置时间为当天23:59:59
                end_date = datetime.combine(end_date.date(), datetime.max.time())
                
                print(f"[Database] 应用结束日期过滤: {end_date.date()} 23:59:59 (包含当天)", flush=True)
                query = query.filter(Order.date <= end_date)
            
            # 执行查询
            print(f"[Database] 执行查询...")
            results = query.all()
            print(f"[Database] 查询到 {len(results)} 条记录")
            
            # 🔍 调试: 检查前5条记录的订单ID
            if results:
                print(f"[Database] 前5条记录的订单ID:")
                for i, (order, store_code) in enumerate(results[:5]):
                    print(f"   {i+1}. order_id='{order.order_id}' (type={type(order.order_id).__name__})")
            
            # 转换为DataFrame - 使用统一的字段映射
            data = []
            for order, store_code in results:
                row = {}
                
                # 自动从映射表读取字段
                for chinese_name, (db_field, default_val, need_hasattr) in DB_FIELD_MAPPING.items():
                    row[chinese_name] = get_field_value(order, db_field, default_val, need_hasattr)
                
                # ===== 特殊处理的字段 =====
                # 店内码: 优先使用Order表，fallback到Product表
                if not row.get('店内码'):
                    row['店内码'] = store_code if store_code else ''
                
                # 商品原价: fallback到实售价
                if row.get('商品原价') is None:
                    row['商品原价'] = row.get('商品实售价', 0)
                
                # 实收价格: fallback到实售价
                if row.get('实收价格') is None:
                    row['实收价格'] = row.get('商品实售价', 0)
                
                # 预计订单收入: fallback到计算值
                if row.get('预计订单收入') is None:
                    row['预计订单收入'] = row.get('商品实售价', 0) * row.get('销量', 1)
                
                # ===== 计算字段 =====
                price = row.get('商品实售价', 0) or 0
                quantity = row.get('销量', 1) or 1
                actual_price = row.get('实收价格', 0) or price
                
                row['订单零售额'] = price * quantity
                row['实收金额'] = actual_price * quantity
                row['用户支付金额'] = actual_price * quantity
                
                # ===== 兼容字段处理已通过字段映射自动完成 =====
                # row['收货地址'] 已通过 DB_FIELD_MAPPING 自动映射
                
                data.append(row)
            
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
