"""
测试距离分析API的门店筛选功能
验证：
1. 不传store_name时返回全部门店数据
2. 传store_name时只返回该门店数据
3. 厉臣便利（镇江平昌路店）应该只有约7936个订单
"""
import requests
import urllib.parse

BASE_URL = "http://localhost:8080/api/v1"

def test_distance_analysis_store_filter():
    """测试门店筛选"""
    
    # 测试1: 不传门店参数（应返回全部门店数据）
    print("=" * 60)
    print("测试1: 不传门店参数")
    print("=" * 60)
    
    resp = requests.get(f"{BASE_URL}/orders/distance-analysis")
    if resp.status_code == 200:
        data = resp.json()
        if data.get("success"):
            summary = data["data"]["summary"]
            bands = data["data"]["distance_bands"]
            total_orders = summary["total_orders"]
            print(f"✅ 全部门店订单数: {total_orders}")
            print(f"   各距离区间订单数:")
            for band in bands:
                print(f"   - {band['band_label']}: {band['order_count']} 订单, 利润 ¥{band['profit']:.2f}")
        else:
            print(f"❌ API返回失败: {data}")
    else:
        print(f"❌ HTTP错误: {resp.status_code}")
    
    # 测试2: 传门店参数（厉臣便利（镇江平昌路店））
    print("\n" + "=" * 60)
    print("测试2: 传门店参数 - 厉臣便利（镇江平昌路店）")
    print("=" * 60)
    
    store_name = "厉臣便利（镇江平昌路店）"
    encoded_store = urllib.parse.quote(store_name)
    
    resp = requests.get(f"{BASE_URL}/orders/distance-analysis?store_name={encoded_store}")
    if resp.status_code == 200:
        data = resp.json()
        if data.get("success"):
            summary = data["data"]["summary"]
            bands = data["data"]["distance_bands"]
            total_orders = summary["total_orders"]
            print(f"✅ 门店订单数: {total_orders}")
            print(f"   期望订单数: ~7936 (去重后)")
            print(f"   各距离区间订单数:")
            for band in bands:
                print(f"   - {band['band_label']}: {band['order_count']} 订单, 利润 ¥{band['profit']:.2f}")
            
            # 验证订单数是否合理
            if total_orders > 10000:
                print(f"\n⚠️ 警告: 订单数 {total_orders} 远超预期 7936，门店筛选可能未生效!")
            elif total_orders < 7000:
                print(f"\n⚠️ 警告: 订单数 {total_orders} 低于预期 7936，可能有数据问题!")
            else:
                print(f"\n✅ 订单数 {total_orders} 在合理范围内 (7000-8000)")
        else:
            print(f"❌ API返回失败: {data}")
    else:
        print(f"❌ HTTP错误: {resp.status_code}")
    
    # 测试3: 直接查询数据库验证订单数
    print("\n" + "=" * 60)
    print("测试3: 直接查询数据库验证")
    print("=" * 60)
    
    try:
        import sys
        sys.path.insert(0, '订单数据看板/订单数据看板/O2O-Analysis')
        from database.connection import SessionLocal
        from database.models import Order
        from sqlalchemy import func
        
        session = SessionLocal()
        try:
            # 查询该门店的唯一订单数
            unique_orders = session.query(func.count(func.distinct(Order.order_id))).filter(
                Order.store_name == store_name
            ).scalar()
            
            # 查询该门店的总行数
            total_rows = session.query(func.count(Order.id)).filter(
                Order.store_name == store_name
            ).scalar()
            
            print(f"✅ 数据库验证:")
            print(f"   门店: {store_name}")
            print(f"   唯一订单数: {unique_orders}")
            print(f"   总行数(含商品): {total_rows}")
            
        finally:
            session.close()
    except Exception as e:
        print(f"⚠️ 数据库查询失败: {e}")

if __name__ == "__main__":
    test_distance_analysis_store_filter()
