"""
数据库模型定义
定义订单、商品、分析结果等表结构
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Order(Base):
    """订单表 - 存储所有订单数据"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(100), nullable=False, unique=True, index=True, comment='订单ID')
    date = Column(DateTime, nullable=False, index=True, comment='下单时间')
    store_name = Column(String(200), comment='门店名称')
    
    # 商品信息
    product_id = Column(Integer, ForeignKey('products.id'), index=True, comment='商品ID')
    product_name = Column(String(500), nullable=False, comment='商品名称')
    barcode = Column(String(100), index=True, comment='条码')
    
    # 分类
    category_level1 = Column(String(100), index=True, comment='一级分类')
    category_level3 = Column(String(100), index=True, comment='三级分类')
    
    # 价格和成本
    price = Column(Float, nullable=False, comment='商品实售价')
    original_price = Column(Float, comment='商品原价')
    cost = Column(Float, comment='商品采购成本')
    actual_price = Column(Float, comment='实收价格')
    
    # 销量和金额
    quantity = Column(Integer, default=1, comment='销量')
    amount = Column(Float, comment='销售额')
    profit = Column(Float, comment='利润')
    profit_margin = Column(Float, comment='利润率')
    
    # 费用
    delivery_fee = Column(Float, default=0, comment='物流配送费')
    commission = Column(Float, default=0, comment='平台佣金')
    platform_service_fee = Column(Float, default=0, comment='平台服务费')
    
    # 营销活动费用
    user_paid_delivery_fee = Column(Float, default=0, comment='用户支付配送费')
    delivery_discount = Column(Float, default=0, comment='配送费减免金额')
    full_reduction = Column(Float, default=0, comment='满减金额')
    product_discount = Column(Float, default=0, comment='商品减免金额')
    merchant_voucher = Column(Float, default=0, comment='商家代金券')
    merchant_share = Column(Float, default=0, comment='商家承担部分券')
    packaging_fee = Column(Float, default=0, comment='打包袋金额')
    gift_amount = Column(Float, default=0, comment='满赠金额')
    other_merchant_discount = Column(Float, default=0, comment='商家其他优惠')
    new_customer_discount = Column(Float, default=0, comment='新客减免金额')
    
    # 利润补偿项
    corporate_rebate = Column(Float, default=0, comment='企客后返')
    
    # ✅ 配送信息
    delivery_platform = Column(String(100), index=True, comment='配送平台')
    
    # ✅ 门店信息
    store_franchise_type = Column(Integer, index=True, comment='门店加盟类型(1=直营店,2=加盟店,3=托管店,4=买断,NULL=未分类)')
    
    # 场景和时段
    scene = Column(String(50), index=True, comment='消费场景')
    time_period = Column(String(50), index=True, comment='时段')
    
    # 其他
    address = Column(Text, comment='收货地址')
    channel = Column(String(100), index=True, comment='渠道')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关系
    product = relationship("Product", back_populates="orders")
    
    # 索引
    __table_args__ = (
        Index('idx_date_store', 'date', 'store_name'),
        Index('idx_product_date', 'product_id', 'date'),
        Index('idx_scene_time', 'scene', 'time_period'),
    )


class Product(Base):
    """商品表 - 存储商品主数据"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(500), nullable=False, index=True, comment='商品名称')
    barcode = Column(String(100), unique=True, index=True, comment='条码')
    store_code = Column(String(100), comment='店内码')
    
    # 分类
    category_level1 = Column(String(100), index=True, comment='一级分类')
    category_level3 = Column(String(100), index=True, comment='三级分类')
    
    # 当前价格和成本
    current_price = Column(Float, comment='当前售价')
    current_cost = Column(Float, comment='当前成本')
    
    # 库存
    stock = Column(Integer, default=0, comment='当前库存')
    stock_status = Column(String(20), comment='库存状态：充足/紧张/售罄')
    
    # 商品标签
    product_role = Column(String(20), index=True, comment='商品角色：流量品/利润品/形象品')
    lifecycle_stage = Column(String(20), comment='生命周期：明星/金牛/引流/淘汰')
    
    # 统计数据（缓存）
    total_sales = Column(Float, default=0, comment='总销售额')
    total_orders = Column(Integer, default=0, comment='总订单数')
    total_quantity = Column(Integer, default=0, comment='总销量')
    avg_profit_margin = Column(Float, comment='平均利润率')
    
    # 元数据
    is_active = Column(Boolean, default=True, comment='是否在售')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    last_sale_date = Column(DateTime, comment='最后销售日期')
    
    # 关系
    orders = relationship("Order", back_populates="product")
    scene_tags = relationship("SceneTag", back_populates="product")


class SceneTag(Base):
    """场景打标结果表 - 存储智能打标结果"""
    __tablename__ = 'scene_tags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    
    # 场景标签
    base_scene = Column(String(50), comment='基础场景')
    seasonal_scene = Column(String(50), comment='季节场景')
    holiday_scene = Column(String(50), comment='节假日场景')
    purchase_driver = Column(String(50), comment='购买驱动')
    
    # 置信度
    confidence = Column(Float, comment='置信度分数')
    
    # 元数据
    tagged_at = Column(DateTime, default=datetime.now, comment='打标时间')
    algorithm_version = Column(String(20), comment='算法版本')
    
    # 关系
    product = relationship("Product", back_populates="scene_tags")
    
    # 索引
    __table_args__ = (
        Index('idx_product_scene', 'product_id', 'base_scene'),
    )


class AnalysisCache(Base):
    """分析结果缓存表 - 存储计算结果避免重复计算"""
    __tablename__ = 'analysis_cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(200), unique=True, nullable=False, index=True, comment='缓存键')
    cache_type = Column(String(50), index=True, comment='缓存类型：quadrant/trend/scene等')
    
    # 缓存数据
    result_data = Column(Text, comment='结果JSON数据')
    
    # 参数记录
    params = Column(Text, comment='计算参数JSON')
    data_hash = Column(String(64), comment='数据MD5哈希，用于判断数据是否变化')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    expire_at = Column(DateTime, comment='过期时间')
    hit_count = Column(Integer, default=0, comment='命中次数')
    
    # 索引
    __table_args__ = (
        Index('idx_type_key', 'cache_type', 'cache_key'),
    )


class AIAnalysisLog(Base):
    """AI分析日志表 - 记录AI分析请求和结果"""
    __tablename__ = 'ai_analysis_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_type = Column(String(50), index=True, comment='分析类型')
    prompt = Column(Text, comment='用户提示词')
    response = Column(Text, comment='AI响应')
    
    # AI模型信息
    model_name = Column(String(100), comment='模型名称：GLM-4/通义千问/Gemini')
    tokens_used = Column(Integer, comment='消耗Token数')
    
    # 性能指标
    response_time = Column(Float, comment='响应时间（秒）')
    success = Column(Boolean, default=True, comment='是否成功')
    error_message = Column(Text, comment='错误信息')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    user_id = Column(String(100), comment='用户ID（预留）')
    
    # 索引
    __table_args__ = (
        Index('idx_created_at', 'created_at'),
    )


class DataUploadHistory(Base):
    """数据上传历史表 - 记录每次数据导入"""
    __tablename__ = 'data_upload_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(500), nullable=False, comment='文件名')
    file_size = Column(Integer, comment='文件大小（字节）')
    file_hash = Column(String(64), comment='文件MD5哈希')
    
    # 导入结果
    rows_imported = Column(Integer, comment='导入行数')
    rows_failed = Column(Integer, default=0, comment='失败行数')
    success = Column(Boolean, default=True, comment='是否成功')
    error_log = Column(Text, comment='错误日志')
    
    # 元数据
    uploaded_at = Column(DateTime, default=datetime.now, comment='上传时间')
    uploaded_by = Column(String(100), comment='上传人（预留）')
    
    # 索引
    __table_args__ = (
        Index('idx_uploaded_at', 'uploaded_at'),
    )


# 导出所有模型
__all__ = [
    'Base',
    'Order',
    'Product',
    'SceneTag',
    'AnalysisCache',
    'AIAnalysisLog',
    'DataUploadHistory',
]
