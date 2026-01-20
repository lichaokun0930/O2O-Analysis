# -*- coding: utf-8 -*-
"""
对比Dash版本和Vue版本的核心经营指标计算

针对灵璧县门店，计算六大核心卡片：
1. 订单总数
2. 商品实收额
3. 总利润
4. 平均客单价
5. 总利润率
6. 动销商品数
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

# ==================== 收费渠道列表 ====================
PLATFORM_FEE_CHANNELS = [
    '饿了么', '京东到家', '美团共橙', '美团闪购',
    '抖音', '抖音直播', '淘鲜达', '京东秒送',
    '美团咖啡店', '饿了么咖啡店'
]


def load_database_data(store_filter='灵璧'):
    """从数据库加载数据"""
    try:
        from database.connection import SessionLocal
        from database.models import Order
    except ImportError as e:
        print(f"❌ 无法导入数据库模块: {e}")
        return None
    
    session = SessionLocal()
    try:
        query = session.query(Order)
        if store_filter:
            query = query.filter(Order.store_name.like(f'%{store_filter}%'))
        
        orders = query.all()
        
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '门店名称': order.store_name,
                '渠道': order.channel,
                '平台服务费': float(order.platform_service_fee or 0),
                '平台佣金': float(order.commission or 0),
                '商品名称': order.product_name,
                '一级分类名': order.category_level1,
                '日期': order.date,
                '利润额': float(order.profit or 0),
                '物流配送费': float(order.delivery_fee or 0),
                '企客后返': float(order.corporate_rebate or 0),
                '实收价格': float(order.actual_price or 0),
                '商品实售价': float(order.price or 0),
                '月售': order.quantity or 1,
                '预计订单收入': float(order.amount or 0),
                '用户支付配送费': float(order.user_paid_delivery_fee or 0),
                '配送费减免金额': float(order.delivery_discount or 0),
            })
        
        return pd.DataFrame(data)
    finally:
        session.close()


# ==================== Dash版本计算逻辑 ====================
def calculate_dash_style(df):
    """
    完全模拟Dash版本的calculate_order_metrics函数
    """
    print("\n" + "="*60)
    print("📊 Dash版本计算逻辑")
    print("="*60)
    
    if df.empty or '订单ID' not in df.columns:
        return None
    
    df = df.copy()
    
    # 统一订单ID类型为字符串
    df['订单ID'] = df['订单ID'].astype(str)
    
    # 兼容字段名
    sales_field = '月售' if '月售' in df.columns else '销量'
    
    # 空值填充
    df['物流配送费'] = df['物流配送费'].fillna(0)
    df['配送费减免金额'] = df['配送费减免金额'].fillna(0)
    df['用户支付配送费'] = df['用户支付配送费'].fillna(0)
    df['平台服务费'] = df['平台服务费'].fillna(0)
    df['企客后返'] = df['企客后返'].fillna(0)
    df['利润额'] = df['利润额'].fillna(0)
    
    # 计算订单总收入 = 实收价格 × 销量
    if '实收价格' in df.columns and sales_field in df.columns:
        df['订单总收入'] = df['实收价格'] * df[sales_field]
    
    # 订单级聚合
    agg_dict = {
        '商品实售价': 'sum',
        '预计订单收入': 'sum',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '物流配送费': 'first',
        '平台佣金': 'first',
        '渠道': 'first',
        '门店名称': 'first',
        '日期': 'first',
    }
    
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
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    
    # 重命名订单总收入为实收价格
    if '订单总收入' in order_agg.columns:
        order_agg['实收价格'] = order_agg['订单总收入']
    
    # 关键字段兜底
    order_agg['平台服务费'] = order_agg['平台服务费'].fillna(0)
    order_agg['企客后返'] = order_agg['企客后返'].fillna(0)
    order_agg['平台佣金'] = order_agg['平台佣金'].fillna(0)
    order_agg['利润额'] = order_agg['利润额'].fillna(0)
    
    # 计算订单实际利润（核心公式）
    # 公式: 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
    order_agg['订单实际利润'] = (
        order_agg['利润额'] -
        order_agg['平台服务费'] -
        order_agg['物流配送费'] +
        order_agg['企客后返']
    )
    
    print(f"   聚合后订单数: {len(order_agg):,}")
    
    # 按渠道类型过滤异常订单
    if '渠道' in order_agg.columns:
        is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
        is_zero_fee = order_agg['平台服务费'] <= 0
        invalid_orders = is_fee_channel & is_zero_fee
        
        print(f"   收费渠道订单: {is_fee_channel.sum():,}")
        print(f"   平台服务费=0: {is_zero_fee.sum():,}")
        print(f"   剔除订单数: {invalid_orders.sum():,}")
        
        filtered = order_agg[~invalid_orders].copy()
    else:
        filtered = order_agg.copy()
    
    print(f"   过滤后订单数: {len(filtered):,}")
    
    # 计算六大核心指标
    total_orders = len(filtered)
    total_actual_sales = filtered['实收价格'].sum() if '实收价格' in filtered.columns else 0
    total_profit = filtered['订单实际利润'].sum()
    avg_order_value = total_actual_sales / total_orders if total_orders > 0 else 0
    profit_rate = (total_profit / total_actual_sales * 100) if total_actual_sales > 0 else 0
    
    # 动销商品数（有销量的SKU）
    if '商品名称' in df.columns and sales_field in df.columns:
        active_products = df[df[sales_field] > 0]['商品名称'].nunique()
    else:
        active_products = df['商品名称'].nunique() if '商品名称' in df.columns else 0
    
    return {
        '订单总数': total_orders,
        '商品实收额': total_actual_sales,
        '总利润': total_profit,
        '平均客单价': avg_order_value,
        '总利润率': profit_rate,
        '动销商品数': active_products,
    }


# ==================== Vue版本计算逻辑 ====================
def calculate_vue_style(df):
    """
    模拟Vue版本的calculate_order_metrics函数
    （从backend/app/api/v1/orders.py提取）
    """
    print("\n" + "="*60)
    print("📊 Vue版本计算逻辑")
    print("="*60)
    
    if df.empty or '订单ID' not in df.columns:
        return None
    
    df = df.copy()
    
    # 统一订单ID类型为字符串
    df['订单ID'] = df['订单ID'].astype(str)
    
    # 兼容字段名
    sales_field = '月售' if '月售' in df.columns else '销量'
    
    # 空值填充
    df['物流配送费'] = df['物流配送费'].fillna(0)
    df['配送费减免金额'] = df['配送费减免金额'].fillna(0)
    df['用户支付配送费'] = df['用户支付配送费'].fillna(0)
    
    # 计算订单总收入（实收价格 × 销量）
    if '实收价格' in df.columns and sales_field in df.columns:
        df['订单总收入'] = df['实收价格'] * df[sales_field]
    
    # 订单级聚合
    agg_dict = {
        '商品实售价': 'sum',
        '预计订单收入': 'sum',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '物流配送费': 'first',
        '平台佣金': 'first',
    }
    
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
    
    # 订单级字段用first
    for field in ['渠道', '门店名称', '日期']:
        if field in df.columns:
            agg_dict[field] = 'first'
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    
    # 将订单总收入重命名为实收价格
    if '订单总收入' in order_agg.columns:
        order_agg['实收价格'] = order_agg['订单总收入']
    
    # 关键字段兜底
    if '平台服务费' not in order_agg.columns:
        order_agg['平台服务费'] = 0
    order_agg['平台服务费'] = order_agg['平台服务费'].fillna(0)
    
    if '企客后返' not in order_agg.columns:
        order_agg['企客后返'] = 0
    order_agg['企客后返'] = order_agg['企客后返'].fillna(0)
    
    if '平台佣金' not in order_agg.columns:
        order_agg['平台佣金'] = order_agg['平台服务费']
    order_agg['平台佣金'] = order_agg['平台佣金'].fillna(0)
    
    if '利润额' not in order_agg.columns:
        order_agg['利润额'] = 0
    order_agg['利润额'] = order_agg['利润额'].fillna(0)
    
    # 计算订单实际利润（核心公式）
    order_agg['订单实际利润'] = (
        order_agg['利润额'] -
        order_agg['平台服务费'] -
        order_agg['物流配送费'] +
        order_agg['企客后返']
    )
    
    print(f"   聚合后订单数: {len(order_agg):,}")
    
    # 按渠道类型过滤异常订单
    if '渠道' in order_agg.columns:
        is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
        is_zero_fee = order_agg['平台服务费'] <= 0
        invalid_orders = is_fee_channel & is_zero_fee
        
        print(f"   收费渠道订单: {is_fee_channel.sum():,}")
        print(f"   平台服务费=0: {is_zero_fee.sum():,}")
        print(f"   剔除订单数: {invalid_orders.sum():,}")
        
        order_agg = order_agg[~invalid_orders].copy()
    
    print(f"   过滤后订单数: {len(order_agg):,}")
    
    # 六大核心卡片
    total_orders = len(order_agg)
    total_actual_sales = order_agg['实收价格'].sum() if '实收价格' in order_agg.columns else 0
    total_profit = order_agg['订单实际利润'].sum() if '订单实际利润' in order_agg.columns else 0
    avg_order_value = total_actual_sales / total_orders if total_orders > 0 else 0
    profit_rate = (total_profit / total_actual_sales * 100) if total_actual_sales > 0 else 0
    
    # 动销商品数
    if '商品名称' in df.columns and sales_field in df.columns:
        active_products = df[df[sales_field] > 0]['商品名称'].nunique()
    else:
        active_products = df['商品名称'].nunique() if '商品名称' in df.columns else 0
    
    return {
        '订单总数': total_orders,
        '商品实收额': total_actual_sales,
        '总利润': total_profit,
        '平均客单价': avg_order_value,
        '总利润率': profit_rate,
        '动销商品数': active_products,
    }


def main():
    print("="*70)
    print("🔍 灵璧县门店 - 核心经营指标对比")
    print("="*70)
    
    # 加载数据
    print("\n📦 加载数据库数据...")
    df = load_database_data('灵璧')
    
    if df is None or df.empty:
        print("❌ 数据加载失败")
        return
    
    print(f"   原始记录数: {len(df):,}")
    print(f"   唯一订单数: {df['订单ID'].nunique():,}")
    
    # Dash版本计算
    dash_result = calculate_dash_style(df)
    
    # Vue版本计算
    vue_result = calculate_vue_style(df)
    
    # 对比结果
    print("\n" + "="*70)
    print("📊 核心经营指标对比结果")
    print("="*70)
    
    print(f"\n{'指标':<15} {'Dash版本':<20} {'Vue版本':<20} {'差异':<15}")
    print("-"*70)
    
    for key in dash_result.keys():
        dash_val = dash_result[key]
        vue_val = vue_result[key]
        
        if isinstance(dash_val, float):
            if key == '总利润率':
                dash_str = f"{dash_val:.2f}%"
                vue_str = f"{vue_val:.2f}%"
                diff = vue_val - dash_val
                diff_str = f"{diff:+.2f}%"
            else:
                dash_str = f"¥{dash_val:,.2f}"
                vue_str = f"¥{vue_val:,.2f}"
                diff = vue_val - dash_val
                diff_str = f"¥{diff:+,.2f}"
        else:
            dash_str = f"{dash_val:,}"
            vue_str = f"{vue_val:,}"
            diff = vue_val - dash_val
            diff_str = f"{diff:+,}"
        
        match = "✅" if abs(diff) < 0.01 else "❌"
        print(f"{key:<15} {dash_str:<20} {vue_str:<20} {diff_str:<15} {match}")
    
    print("\n" + "="*70)
    print("🎯 结论")
    print("="*70)
    
    all_match = all(
        abs(dash_result[k] - vue_result[k]) < 0.01 
        for k in dash_result.keys()
    )
    
    if all_match:
        print("\n✅ 两个版本的计算逻辑完全一致！")
        print("   如果实际显示不一致，问题可能在于：")
        print("   1. 数据源不同（数据库 vs Excel）")
        print("   2. 日期筛选范围不同")
        print("   3. 门店筛选条件不同")
    else:
        print("\n❌ 两个版本的计算逻辑存在差异！")
        print("   需要检查具体的计算公式差异")


if __name__ == "__main__":
    main()
