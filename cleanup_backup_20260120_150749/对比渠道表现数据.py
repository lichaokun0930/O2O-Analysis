# -*- coding: utf-8 -*-
"""
对比渠道表现数据 - Vue版本 vs Dash版本

验证灵璧县门店的渠道表现对比数据是否一致
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "app"))

# 数据库连接
from database.connection import SessionLocal
from database.models import Order

# 收费渠道列表（与老版本一致）
PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购',
    '抖音', '抖音直播', '淘鲜达', '京东秒送',
    '美团咖啡店', '饿了么咖啡店'
]

# 咖啡渠道（在渠道对比中隐藏）
CHANNELS_TO_REMOVE = ['美团咖啡店', '饿了么咖啡店']


def load_store_data(store_name: str) -> pd.DataFrame:
    """从数据库加载指定门店数据"""
    session = SessionLocal()
    try:
        orders = session.query(Order).filter(Order.store_name == store_name).all()
        if not orders:
            return pd.DataFrame()
        
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '门店名称': order.store_name,
                '日期': order.date,
                '渠道': order.channel,
                '商品名称': order.product_name,
                '一级分类名': order.category_level1,
                '月售': order.quantity,
                '实收价格': float(order.actual_price or 0),
                '商品实售价': float(order.price or 0),
                '商品采购成本': float(order.cost or 0),
                '利润额': float(order.profit or 0),
                '物流配送费': float(order.delivery_fee or 0),
                '平台服务费': float(order.platform_service_fee or 0),
                '企客后返': float(order.corporate_rebate or 0),
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()


def calculate_order_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    统一的订单指标计算函数（与老版本完全一致）
    """
    if df.empty or '订单ID' not in df.columns:
        return pd.DataFrame()
    
    df = df.copy()
    df['订单ID'] = df['订单ID'].astype(str)
    
    # 空值填充
    df['物流配送费'] = df['物流配送费'].fillna(0)
    df['平台服务费'] = df['平台服务费'].fillna(0)
    df['企客后返'] = df['企客后返'].fillna(0)
    df['利润额'] = df['利润额'].fillna(0)
    
    # 计算订单总收入（实收价格 × 销量）
    sales_field = '月售' if '月售' in df.columns else '销量'
    if '实收价格' in df.columns and sales_field in df.columns:
        df['订单总收入'] = df['实收价格'] * df[sales_field]
    
    # 订单级聚合
    agg_dict = {
        '物流配送费': 'first',
    }
    
    if '商品实售价' in df.columns:
        agg_dict['商品实售价'] = 'sum'
    
    if sales_field in df.columns:
        agg_dict[sales_field] = 'sum'
    if '平台服务费' in df.columns:
        agg_dict['平台服务费'] = 'sum'
    if '订单总收入' in df.columns:
        agg_dict['订单总收入'] = 'sum'
    if '利润额' in df.columns:
        agg_dict['利润额'] = 'sum'
    if '企客后返' in df.columns:
        agg_dict['企客后返'] = 'sum'
    if '商品采购成本' in df.columns:
        agg_dict['商品采购成本'] = 'sum'
    
    # 订单级字段用first
    for field in ['渠道', '门店名称', '日期']:
        if field in df.columns:
            agg_dict[field] = 'first'
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    
    # 将订单总收入重命名为实收价格
    if '订单总收入' in order_agg.columns:
        order_agg['实收价格'] = order_agg['订单总收入']
    
    # 关键字段兜底
    for col in ['平台服务费', '企客后返', '利润额', '物流配送费']:
        if col not in order_agg.columns:
            order_agg[col] = 0
        order_agg[col] = order_agg[col].fillna(0)
    
    # 计算订单实际利润（核心公式）
    order_agg['订单实际利润'] = (
        order_agg['利润额'] -
        order_agg['平台服务费'] -
        order_agg['物流配送费'] +
        order_agg['企客后返']
    )
    
    # 按渠道类型过滤异常订单
    if '渠道' in order_agg.columns:
        is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
        is_zero_fee = order_agg['平台服务费'] <= 0
        invalid_orders = is_fee_channel & is_zero_fee
        order_agg = order_agg[~invalid_orders].copy()
    
    return order_agg


def calculate_channel_stats(order_agg: pd.DataFrame, exclude_coffee: bool = True) -> pd.DataFrame:
    """
    计算渠道统计数据
    
    Args:
        order_agg: 订单聚合数据
        exclude_coffee: 是否排除咖啡渠道
    """
    if order_agg.empty or '渠道' not in order_agg.columns:
        return pd.DataFrame()
    
    df = order_agg.copy()
    
    # 排除咖啡渠道
    if exclude_coffee:
        df = df[~df['渠道'].isin(CHANNELS_TO_REMOVE)]
    
    # 按渠道聚合
    channel_stats = df.groupby('渠道').agg({
        '订单ID': 'count',
        '实收价格': 'sum',
        '订单实际利润': 'sum',
    }).reset_index()
    
    channel_stats.columns = ['渠道', '订单数', '销售额', '利润']
    
    # 计算派生指标
    total_orders = channel_stats['订单数'].sum()
    total_amount = channel_stats['销售额'].sum()
    
    channel_stats['订单占比'] = (channel_stats['订单数'] / total_orders * 100) if total_orders > 0 else 0
    channel_stats['销售额占比'] = (channel_stats['销售额'] / total_amount * 100) if total_amount > 0 else 0
    channel_stats['客单价'] = channel_stats.apply(
        lambda r: r['销售额'] / r['订单数'] if r['订单数'] > 0 else 0, axis=1
    )
    channel_stats['利润率'] = channel_stats.apply(
        lambda r: r['利润'] / r['销售额'] * 100 if r['销售额'] > 0 else 0, axis=1
    )
    
    # 按订单数排序
    channel_stats = channel_stats.sort_values('订单数', ascending=False)
    
    return channel_stats


def main():
    store_name = "共橙一站式超市（灵璧县新河路店）"
    
    print("=" * 80)
    print(f" 渠道表现对比数据验证 - {store_name}")
    print("=" * 80)
    
    # 1. 加载数据
    print(f"\n📦 加载 {store_name} 门店数据...")
    df = load_store_data(store_name)
    
    if df.empty:
        print(f"❌ 未找到 {store_name} 的数据")
        return
    
    print(f"   原始数据: {len(df)} 条记录")
    
    # 2. 数据日期范围
    df['日期'] = pd.to_datetime(df['日期'])
    min_date = df['日期'].min()
    max_date = df['日期'].max()
    print(f"   日期范围: {min_date.date()} ~ {max_date.date()}")
    
    # 3. 渠道分布（原始数据）
    print(f"\n📊 原始数据渠道分布:")
    channel_counts = df.groupby('渠道')['订单ID'].nunique().sort_values(ascending=False)
    for ch, cnt in channel_counts.items():
        print(f"   {ch}: {cnt} 笔订单")
    
    # 4. 计算订单级指标
    print(f"\n🔄 计算订单级指标...")
    order_agg = calculate_order_metrics(df)
    print(f"   有效订单数: {len(order_agg)}")
    
    # 5. 计算渠道统计（排除咖啡渠道）
    print(f"\n📈 渠道表现统计（排除咖啡渠道）:")
    channel_stats = calculate_channel_stats(order_agg, exclude_coffee=True)
    
    print(f"\n{'渠道':<15} {'订单数':>8} {'销售额':>12} {'利润':>12} {'客单价':>10} {'利润率':>8}")
    print("-" * 70)
    
    for _, row in channel_stats.iterrows():
        print(f"{row['渠道']:<15} {int(row['订单数']):>8} {row['销售额']:>12,.2f} {row['利润']:>12,.2f} {row['客单价']:>10,.2f} {row['利润率']:>7.2f}%")
    
    # 6. 汇总
    print("-" * 70)
    total_orders = channel_stats['订单数'].sum()
    total_sales = channel_stats['销售额'].sum()
    total_profit = channel_stats['利润'].sum()
    avg_value = total_sales / total_orders if total_orders > 0 else 0
    profit_rate = total_profit / total_sales * 100 if total_sales > 0 else 0
    
    print(f"{'合计':<15} {int(total_orders):>8} {total_sales:>12,.2f} {total_profit:>12,.2f} {avg_value:>10,.2f} {profit_rate:>7.2f}%")
    
    # 7. 与Vue API对比
    print(f"\n" + "=" * 80)
    print(" 与Vue API对比")
    print("=" * 80)
    
    print("""
请在浏览器中访问Vue版本，选择灵璧县门店，对比以下数据:

1. 渠道表现对比卡片中的数据是否一致
2. 各渠道的订单数、销售额、利润、客单价、利润率

如果数据不一致，请提供Vue版本显示的数据，我来分析差异原因。
""")
    
    # 8. 输出JSON格式（方便对比）
    print(f"\n📋 JSON格式数据（用于对比）:")
    result = []
    for _, row in channel_stats.iterrows():
        result.append({
            "channel": row['渠道'],
            "order_count": int(row['订单数']),
            "amount": round(float(row['销售额']), 2),
            "profit": round(float(row['利润']), 2),
            "avg_value": round(float(row['客单价']), 2),
            "profit_rate": round(float(row['利润率']), 2),
        })
    
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
