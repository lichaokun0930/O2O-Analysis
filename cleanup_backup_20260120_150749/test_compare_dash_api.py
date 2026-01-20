# -*- coding: utf-8 -*-
"""
对比Dash版本和API版本的订单聚合逻辑
验证订单数是否一致
"""
import sys
from pathlib import Path

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(APP_DIR / "backend" / "app"))

import pandas as pd
import numpy as np

def test_dash_vs_api():
    """对比Dash版本和API版本的订单聚合"""
    print("=" * 80)
    print("🔍 对比Dash版本和API版本的订单聚合逻辑")
    print("=" * 80)
    
    # ========== 1. 从数据库加载原始数据 ==========
    print("\n1️⃣ 从数据库加载原始数据...")
    from database.connection import SessionLocal
    from database.models import Order
    
    session = SessionLocal()
    try:
        orders = session.query(Order).all()
        
        # 转换为DataFrame
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '门店名称': order.store_name,
                '日期': order.date,
                '渠道': order.channel,
                '商品名称': order.product_name,
                '一级分类名': order.category_level1,
                '月售': order.quantity if order.quantity is not None else 1,
                '实收价格': float(order.actual_price or 0),
                '商品实售价': float(order.price or 0),
                '商品采购成本': float(order.cost or 0),
                '利润额': float(order.profit or 0),
                '物流配送费': float(order.delivery_fee or 0),
                '平台服务费': float(order.platform_service_fee or 0),
                '平台佣金': float(order.commission or 0),
                '预计订单收入': float(order.amount or 0),
                '企客后返': float(order.corporate_rebate or 0),
                '用户支付配送费': float(order.user_paid_delivery_fee or 0),
                '配送费减免金额': float(order.delivery_discount or 0),
                '满减金额': float(order.full_reduction or 0),
                '商品减免金额': float(order.product_discount or 0),
                '新客减免金额': float(order.new_customer_discount or 0),
                '配送距离': float(order.delivery_distance or 0),
            })
        
        df = pd.DataFrame(data)
        print(f"   原始数据行数: {len(df)}")
        print(f"   唯一订单ID数: {df['订单ID'].nunique()}")
        
    finally:
        session.close()
    
    # ========== 2. 使用API版本的calculate_order_metrics ==========
    print("\n2️⃣ 使用API版本的calculate_order_metrics...")
    from api.v1.orders import calculate_order_metrics as api_calculate
    
    api_order_agg = api_calculate(df.copy())
    print(f"   API聚合后订单数: {len(api_order_agg)}")
    
    # ========== 3. 手动实现Dash版本的聚合逻辑 ==========
    print("\n3️⃣ 手动实现Dash版本的聚合逻辑...")
    
    df_dash = df.copy()
    df_dash['订单ID'] = df_dash['订单ID'].astype(str)
    
    # 空值填充
    df_dash['物流配送费'] = df_dash['物流配送费'].fillna(0)
    df_dash['配送费减免金额'] = df_dash['配送费减免金额'].fillna(0)
    df_dash['用户支付配送费'] = df_dash['用户支付配送费'].fillna(0)
    
    # 计算订单总收入
    df_dash['订单总收入'] = df_dash['实收价格'] * df_dash['月售']
    
    # 订单级聚合
    agg_dict = {
        '商品实售价': 'sum',
        '预计订单收入': 'sum',
        '用户支付配送费': 'first',
        '配送费减免金额': 'first',
        '物流配送费': 'first',
        '平台佣金': 'first',
        '月售': 'sum',
        '平台服务费': 'sum',
        '订单总收入': 'sum',
        '利润额': 'sum',
        '企客后返': 'sum',
        '商品采购成本': 'sum',
        '满减金额': 'first',
        '商品减免金额': 'first',
        '新客减免金额': 'first',
        '渠道': 'first',
        '门店名称': 'first',
        '日期': 'first',
        '配送距离': 'first',  # 配送距离是订单级字段，用first
    }
    
    dash_order_agg = df_dash.groupby('订单ID').agg(agg_dict).reset_index()
    
    # 计算订单实际利润
    dash_order_agg['实收价格'] = dash_order_agg['订单总收入']
    dash_order_agg['平台服务费'] = dash_order_agg['平台服务费'].fillna(0)
    dash_order_agg['企客后返'] = dash_order_agg['企客后返'].fillna(0)
    dash_order_agg['利润额'] = dash_order_agg['利润额'].fillna(0)
    
    # 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
    dash_order_agg['订单实际利润'] = (
        dash_order_agg['利润额'] -
        dash_order_agg['平台服务费'] -
        dash_order_agg['物流配送费'] +
        dash_order_agg['企客后返']
    )
    
    # 过滤收费渠道中平台服务费=0的异常订单
    PLATFORM_FEE_CHANNELS = [
        '饿了么', '京东到家', '美团共橙', '美团闪购', '抖音',
        '抖音直播', '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店'
    ]
    
    is_fee_channel = dash_order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = dash_order_agg['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    
    print(f"   Dash聚合后订单数（过滤前）: {len(dash_order_agg)}")
    print(f"   异常订单数（收费渠道平台服务费=0）: {invalid_orders.sum()}")
    
    dash_order_agg_filtered = dash_order_agg[~invalid_orders].copy()
    print(f"   Dash聚合后订单数（过滤后）: {len(dash_order_agg_filtered)}")
    
    # ========== 4. 按距离区间统计 ==========
    print("\n4️⃣ 按距离区间统计（使用Dash聚合数据）...")
    
    # 转换距离单位（米->公里）
    dash_order_agg_filtered['配送距离_km'] = dash_order_agg_filtered['配送距离'] / 1000
    
    def get_band(distance):
        if distance < 1:
            return "0-1km"
        elif distance < 2:
            return "1-2km"
        elif distance < 3:
            return "2-3km"
        elif distance < 4:
            return "3-4km"
        elif distance < 5:
            return "4-5km"
        elif distance < 6:
            return "5-6km"
        else:
            return "6km+"
    
    dash_order_agg_filtered['距离区间'] = dash_order_agg_filtered['配送距离_km'].apply(get_band)
    
    print("\n   距离区间分布（Dash版本逻辑）:")
    for band in ["0-1km", "1-2km", "2-3km", "3-4km", "4-5km", "5-6km", "6km+"]:
        band_df = dash_order_agg_filtered[dash_order_agg_filtered['距离区间'] == band]
        order_count = len(band_df)
        revenue = band_df['实收价格'].sum()
        profit = band_df['订单实际利润'].sum()
        profit_rate = round(profit / revenue * 100, 2) if revenue > 0 else 0
        print(f"   {band}: 订单数={order_count}, 销售额={revenue:.2f}, 利润率={profit_rate}%")
    
    # ========== 5. 对比API返回结果 ==========
    print("\n5️⃣ 对比API返回结果...")
    import requests
    
    try:
        response = requests.get("http://localhost:8080/api/v1/orders/distance-analysis", timeout=30)
        api_data = response.json()
        
        if api_data.get('success'):
            print("\n   API返回的距离区间分布:")
            for band in api_data['data']['distance_bands']:
                print(f"   {band['band_label']}: 订单数={band['order_count']}, "
                      f"销售额={band['revenue']:.2f}, 利润率={band['profit_rate']}%")
            
            print(f"\n   API总订单数: {api_data['data']['summary']['total_orders']}")
            print(f"   Dash总订单数: {len(dash_order_agg_filtered)}")
            
            if api_data['data']['summary']['total_orders'] == len(dash_order_agg_filtered):
                print("\n   ✅ 订单数一致！")
            else:
                print(f"\n   ❌ 订单数不一致！差异: {api_data['data']['summary']['total_orders'] - len(dash_order_agg_filtered)}")
        else:
            print(f"   ❌ API返回失败: {api_data}")
            
    except Exception as e:
        print(f"   ❌ API调用失败: {e}")
    
    print("\n" + "=" * 80)
    print("✅ 对比完成")
    print("=" * 80)


if __name__ == "__main__":
    test_dash_vs_api()
