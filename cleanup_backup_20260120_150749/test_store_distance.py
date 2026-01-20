# -*- coding: utf-8 -*-
"""
测试指定门店的距离分析
门店：厉臣便利（镇江平昌路店）
"""
import sys
from pathlib import Path
import requests

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(APP_DIR / "backend" / "app"))

import pandas as pd
from urllib.parse import quote

STORE_NAME = "惠宜选超市（合肥繁华大道店）"

def test_store_distance():
    print("=" * 80)
    print(f"🏪 测试门店: {STORE_NAME}")
    print("=" * 80)
    
    # 1. 直接从数据库查询该门店数据
    print("\n1️⃣ 从数据库查询该门店原始数据...")
    from database.connection import SessionLocal
    from database.models import Order
    
    session = SessionLocal()
    try:
        # 查询该门店所有订单
        orders = session.query(Order).filter(Order.store_name == STORE_NAME).all()
        
        data = []
        for order in orders:
            data.append({
                '订单ID': order.order_id,
                '渠道': order.channel,
                '配送距离': float(order.delivery_distance or 0),
                '平台服务费': float(order.platform_service_fee or 0),
                '利润额': float(order.profit or 0),
                '物流配送费': float(order.delivery_fee or 0),
                '企客后返': float(order.corporate_rebate or 0),
                '实收价格': float(order.actual_price or 0),
                '月售': order.quantity if order.quantity is not None else 1,
            })
        
        df = pd.DataFrame(data)
        print(f"   原始数据行数: {len(df)}")
        print(f"   唯一订单ID数: {df['订单ID'].nunique()}")
        
        # 检查配送距离
        print(f"\n   配送距离统计（原始值，单位：米）:")
        print(f"   - 非零值: {(df['配送距离'] > 0).sum()}")
        print(f"   - 零值: {(df['配送距离'] == 0).sum()}")
        print(f"   - 平均值: {df['配送距离'].mean():.2f}")
        print(f"   - 最大值: {df['配送距离'].max():.2f}")
        
    finally:
        session.close()
    
    # 2. 手动聚合（模拟Dash逻辑）
    print("\n2️⃣ 手动聚合（Dash逻辑）...")
    
    df['订单ID'] = df['订单ID'].astype(str)
    df['订单总收入'] = df['实收价格'] * df['月售']
    
    # 按订单ID聚合
    agg_dict = {
        '渠道': 'first',
        '配送距离': 'first',
        '平台服务费': 'sum',
        '利润额': 'sum',
        '物流配送费': 'first',
        '企客后返': 'sum',
        '订单总收入': 'sum',
    }
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    order_agg['实收价格'] = order_agg['订单总收入']
    
    # 计算订单实际利润
    order_agg['订单实际利润'] = (
        order_agg['利润额'] -
        order_agg['平台服务费'] -
        order_agg['物流配送费'] +
        order_agg['企客后返']
    )
    
    # 过滤异常订单
    PLATFORM_FEE_CHANNELS = [
        '饿了么', '京东到家', '美团共橙', '美团闪购', '抖音',
        '抖音直播', '淘鲜达', '京东秒送', '美团咖啡店', '饿了么咖啡店'
    ]
    
    is_fee_channel = order_agg['渠道'].isin(PLATFORM_FEE_CHANNELS)
    is_zero_fee = order_agg['平台服务费'] <= 0
    invalid_orders = is_fee_channel & is_zero_fee
    
    print(f"   聚合后订单数（过滤前）: {len(order_agg)}")
    print(f"   异常订单数: {invalid_orders.sum()}")
    
    order_agg_filtered = order_agg[~invalid_orders].copy()
    print(f"   聚合后订单数（过滤后）: {len(order_agg_filtered)}")
    
    # 转换距离单位
    order_agg_filtered['配送距离_km'] = order_agg_filtered['配送距离'] / 1000
    
    # 按距离区间统计
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
    
    order_agg_filtered['距离区间'] = order_agg_filtered['配送距离_km'].apply(get_band)
    
    print(f"\n   📊 Dash版本距离区间分布:")
    total_orders = 0
    for band in ["0-1km", "1-2km", "2-3km", "3-4km", "4-5km", "5-6km", "6km+"]:
        band_df = order_agg_filtered[order_agg_filtered['距离区间'] == band]
        order_count = len(band_df)
        total_orders += order_count
        revenue = band_df['实收价格'].sum()
        profit = band_df['订单实际利润'].sum()
        profit_rate = round(profit / revenue * 100, 2) if revenue > 0 else 0
        print(f"   {band}: 订单数={order_count}, 销售额=¥{revenue:.2f}, 利润率={profit_rate}%")
    
    print(f"\n   Dash版本总订单数: {total_orders}")
    
    # 3. 调用API
    print("\n3️⃣ 调用API...")
    try:
        url = f"http://localhost:8080/api/v1/orders/distance-analysis?store_name={quote(STORE_NAME)}"
        response = requests.get(url, timeout=30)
        api_data = response.json()
        
        if api_data.get('success'):
            print(f"\n   📊 API返回距离区间分布:")
            api_total = 0
            for band in api_data['data']['distance_bands']:
                api_total += band['order_count']
                print(f"   {band['band_label']}: 订单数={band['order_count']}, "
                      f"销售额=¥{band['revenue']:.2f}, 利润率={band['profit_rate']}%")
            
            print(f"\n   API总订单数: {api_data['data']['summary']['total_orders']}")
            print(f"   API平均距离: {api_data['data']['summary']['avg_distance']}km")
            
            # 对比
            print(f"\n4️⃣ 对比结果:")
            if api_data['data']['summary']['total_orders'] == total_orders:
                print(f"   ✅ 订单数一致: {total_orders}")
            else:
                print(f"   ❌ 订单数不一致!")
                print(f"      Dash: {total_orders}")
                print(f"      API:  {api_data['data']['summary']['total_orders']}")
        else:
            print(f"   ❌ API返回失败: {api_data}")
            
    except Exception as e:
        print(f"   ❌ API调用失败: {e}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_store_distance()
