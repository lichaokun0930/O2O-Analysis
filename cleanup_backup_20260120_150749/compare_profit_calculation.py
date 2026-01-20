# -*- coding: utf-8 -*-
"""
对比Dash版本和后端API的利润计算
找出差异原因
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "backend" / "app"))

import pandas as pd
from database.connection import SessionLocal
from database.models import Order

def compare_profit():
    print("=" * 80)
    print("🔍 对比Dash版本和后端API的利润计算")
    print("=" * 80)
    
    # 1. 从数据库加载原始数据
    session = SessionLocal()
    try:
        orders = session.query(Order).all()
        data = []
        for o in orders:
            data.append({
                '订单ID': o.order_id,
                '利润额': float(o.profit or 0),
                '平台服务费': float(o.platform_service_fee or 0),
                '物流配送费': float(o.delivery_fee or 0),
                '企客后返': float(o.corporate_rebate or 0),
                '渠道': o.channel,
                '配送距离': float(o.delivery_distance or 0),
            })
        df = pd.DataFrame(data)
    finally:
        session.close()
    
    print(f"\n原始数据行数: {len(df)}")
    print(f"唯一订单ID数: {df['订单ID'].nunique()}")
    
    # 2. 按订单ID聚合（模拟Dash逻辑）
    df['订单ID'] = df['订单ID'].astype(str)
    
    agg_dict = {
        '利润额': 'sum',           # 商品级字段，sum
        '平台服务费': 'sum',       # 商品级字段，sum
        '物流配送费': 'first',     # 订单级字段，first
        '企客后返': 'sum',         # 商品级字段，sum
        '渠道': 'first',
        '配送距离': 'first',
    }
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    print(f"\n聚合后订单数: {len(order_agg)}")
    
    # 3. 计算订单实际利润（Dash公式）
    # 公式: 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
    order_agg['订单实际利润'] = (
        order_agg['利润额'] -
        order_agg['平台服务费'] -
        order_agg['物流配送费'] +
        order_agg['企客后返']
    )
    
    print(f"\n📊 利润计算详情（全部订单）:")
    print(f"  利润额总和: ¥{order_agg['利润额'].sum():,.2f}")
    print(f"  平台服务费总和: ¥{order_agg['平台服务费'].sum():,.2f}")
    print(f"  物流配送费总和: ¥{order_agg['物流配送费'].sum():,.2f}")
    print(f"  企客后返总和: ¥{order_agg['企客后返'].sum():,.2f}")
    print(f"  订单实际利润总和: ¥{order_agg['订单实际利润'].sum():,.2f}")
    
    # 4. 过滤异常订单（收费渠道中平台服务费=0的订单）
    PLATFORM_FEE_CHANNELS = [
        '饿了么', '京东到家', '美团共橙', '美团闪购', '抖音',
        '抖音直播', '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店'
    ]
    
    is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    
    print(f"\n过滤异常订单:")
    print(f"  收费渠道订单数: {is_fee_channel.sum()}")
    print(f"  平台服务费=0的订单数: {is_zero_fee.sum()}")
    print(f"  异常订单数（收费渠道且服务费=0）: {invalid_orders.sum()}")
    
    order_agg_filtered = order_agg[~invalid_orders].copy()
    print(f"  过滤后订单数: {len(order_agg_filtered)}")
    
    # 5. 按距离区间统计
    order_agg_filtered['配送距离_km'] = order_agg_filtered['配送距离'] / 1000
    
    def get_band(d):
        if d < 1: return "0-1km"
        elif d < 2: return "1-2km"
        elif d < 3: return "2-3km"
        elif d < 4: return "3-4km"
        elif d < 5: return "4-5km"
        elif d < 6: return "5-6km"
        else: return "6km+"
    
    order_agg_filtered['距离区间'] = order_agg_filtered['配送距离_km'].apply(get_band)
    
    print(f"\n📊 按距离区间统计（过滤后）:")
    for band in ["0-1km", "1-2km", "2-3km", "3-4km", "4-5km", "5-6km", "6km+"]:
        band_df = order_agg_filtered[order_agg_filtered['距离区间'] == band]
        order_count = len(band_df)
        profit = band_df['订单实际利润'].sum()
        print(f"  {band}: 订单数={order_count}, 利润=¥{profit:,.2f}")
    
    # 6. 对比API返回
    print(f"\n📊 对比API返回:")
    import requests
    try:
        resp = requests.get("http://localhost:8080/api/v1/orders/distance-analysis", timeout=30)
        api_data = resp.json()
        if api_data.get('success'):
            for band in api_data['data']['distance_bands']:
                print(f"  {band['band_label']}: 订单数={band['order_count']}, 利润=¥{band['profit']:,.2f}")
    except Exception as e:
        print(f"  API调用失败: {e}")

if __name__ == "__main__":
    compare_profit()
