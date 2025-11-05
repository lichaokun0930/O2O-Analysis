"""
系统完整性测试脚本
测试前端、后端、数据库的集成情况
"""

import requests
import json

print("="*60)
print("智能门店经营看板 - 系统测试")
print("="*60)

# 1. 测试后端健康检查
print("\n[1/5] 测试后端健康检查...")
try:
    response = requests.get("http://localhost:8000/api/health")
    data = response.json()
    print(f"   状态: {data['status']}")
    print(f"   数据库: {data['database']}")
    print(f"   商品数: {data['stats']['products']:,}")
    print(f"   订单数: {data['stats']['orders']:,}")
    print("   ✅ 健康检查通过")
except Exception as e:
    print(f"   ❌ 错误: {e}")

# 2. 测试数据统计API
print("\n[2/5] 测试数据统计API...")
try:
    response = requests.get("http://localhost:8000/api/stats")
    stats = response.json()
    print(f"   商品总数: {stats['products']['total']:,}")
    print(f"   订单总数: {stats['orders']['total']:,}")
    print(f"   场景数: {stats['scenes']['total']:,}")
    print(f"   缓存数: {stats['cache']['total']:,}")
    print("   ✅ 统计API正常")
except Exception as e:
    print(f"   ❌ 错误: {e}")

# 3. 测试商品列表API
print("\n[3/5] 测试商品列表API...")
try:
    response = requests.get("http://localhost:8000/api/products/", params={"limit": 5})
    products = response.json()
    print(f"   返回商品数: {len(products)}")
    if products:
        print(f"   示例商品: {products[0]['name'][:30]}")
        print(f"   商品分类: {products[0].get('category_level1', 'N/A')}")
    print("   ✅ 商品API正常")
except Exception as e:
    print(f"   ❌ 错误: {e}")

# 4. 测试订单列表API
print("\n[4/5] 测试订单列表API...")
try:
    response = requests.get("http://localhost:8000/api/orders/", params={"limit": 5})
    orders = response.json()
    print(f"   返回订单数: {len(orders)}")
    if orders:
        print(f"   示例订单ID: {orders[0]['order_id']}")
        print(f"   订单日期: {orders[0]['date'][:10]}")
        print(f"   订单金额: ¥{orders[0].get('amount', 0)}")
    print("   ✅ 订单API正常")
except Exception as e:
    print(f"   ❌ 错误: {e}")

# 5. 测试前端页面
print("\n[5/5] 测试Dash前端...")
try:
    response = requests.get("http://localhost:8050")
    if response.status_code == 200:
        print(f"   响应状态: {response.status_code}")
        print(f"   页面大小: {len(response.content):,} bytes")
        print("   ✅ 前端页面正常")
    else:
        print(f"   ❌ 响应状态异常: {response.status_code}")
except Exception as e:
    print(f"   ❌ 错误: {e}")

print("\n" + "="*60)
print("测试完成！")
print("="*60)

print("\n📊 访问地址:")
print("   前端看板: http://localhost:8050")
print("   后端API文档: http://localhost:8000/api/docs")
print("   健康检查: http://localhost:8000/api/health")

print("\n💡 下一步:")
print("   1. 打开浏览器访问 http://localhost:8050")
print("   2. 查看各个功能Tab（订单概览、商品分析、场景分析等）")
print("   3. 测试数据筛选和可视化功能")
print("   4. 如需API接口，访问 http://localhost:8000/api/docs")
