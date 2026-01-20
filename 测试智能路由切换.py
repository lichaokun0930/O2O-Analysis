# -*- coding: utf-8 -*-
"""
智能查询路由切换测试脚本

测试内容：
1. 查看当前路由状态
2. 测试 PostgreSQL 查询
3. 测试 DuckDB 查询
4. 测试智能路由查询
5. 强制切换引擎并验证
6. 性能对比

使用方法：
    python 测试智能路由切换.py
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8080/api/v1"

def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_json(data: dict, indent: int = 2):
    print(json.dumps(data, ensure_ascii=False, indent=indent))

def test_router_status():
    """测试1: 查看路由状态"""
    print_header("1. 查看智能路由状态")
    
    try:
        resp = requests.get(f"{BASE_URL}/observability/query-router/status", timeout=10)
        data = resp.json()
        
        print(f"\n📊 数据量: {data.get('record_count', 0):,} 条")
        print(f"📈 切换阈值: {data.get('switch_threshold', 0):,} 条")
        print(f"🎯 当前引擎: {data.get('current_engine', 'unknown').upper()}")
        print(f"💡 推荐引擎: {data.get('recommended_engine', 'unknown').upper()}")
        print(f"📊 数据级别: {data.get('data_level_desc', '未知')}")
        
        engines = data.get('engines', {})
        print(f"\n🔧 引擎可用性:")
        print(f"   PostgreSQL: {'✅ 可用' if engines.get('postgresql') else '❌ 不可用'}")
        print(f"   DuckDB: {'✅ 可用' if engines.get('duckdb') else '❌ 不可用'}")
        
        stats = data.get('stats', {})
        print(f"\n📈 查询统计:")
        print(f"   PostgreSQL 查询次数: {stats.get('postgresql_queries', 0)}")
        print(f"   DuckDB 查询次数: {stats.get('duckdb_queries', 0)}")
        print(f"   自动切换次数: {stats.get('auto_switches', 0)}")
        
        return data
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_smart_routing_query():
    """测试2: 智能路由查询对比"""
    print_header("2. 智能路由查询对比测试")
    
    try:
        resp = requests.get(f"{BASE_URL}/observability/query-router/test", timeout=30)
        data = resp.json()
        
        # 智能路由结果
        smart = data.get('smart_routing', {})
        if smart.get('success'):
            print(f"\n🧠 智能路由查询:")
            print(f"   引擎: {smart.get('engine', 'unknown').upper()}")
            print(f"   来源: {smart.get('source', 'unknown')}")
            print(f"   耗时: {smart.get('query_time_ms', 0):.2f}ms")
        else:
            print(f"\n❌ 智能路由查询失败: {smart.get('error')}")
        
        # PostgreSQL 结果
        pg = data.get('postgresql', {})
        if pg.get('success'):
            print(f"\n🐘 PostgreSQL 直接查询:")
            print(f"   耗时: {pg.get('query_time_ms', 0):.2f}ms")
            pg_data = pg.get('data', {})
            print(f"   订单数: {pg_data.get('total_orders', 0):,}")
        else:
            print(f"\n❌ PostgreSQL 查询失败: {pg.get('error')}")
        
        # DuckDB 结果
        dk = data.get('duckdb', {})
        if dk.get('success'):
            print(f"\n🦆 DuckDB 直接查询:")
            print(f"   耗时: {dk.get('query_time_ms', 0):.2f}ms")
            dk_data = dk.get('data', {})
            print(f"   订单数: {dk_data.get('total_orders', 0):,}")
        else:
            print(f"\n❌ DuckDB 查询失败: {dk.get('error')}")
        
        # 性能对比
        comparison = data.get('comparison', {})
        if comparison:
            print(f"\n📊 性能对比:")
            print(f"   PostgreSQL: {comparison.get('postgresql_ms', 0):.2f}ms")
            print(f"   DuckDB: {comparison.get('duckdb_ms', 0):.2f}ms")
            print(f"   更快引擎: {comparison.get('faster_engine', 'unknown').upper()}")
            print(f"   加速比: {comparison.get('speedup', 0):.2f}x")
        
        return data
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_force_engine_switch():
    """测试3: 强制切换引擎"""
    print_header("3. 强制切换引擎测试")
    
    # 获取当前引擎
    status_resp = requests.get(f"{BASE_URL}/observability/query-router/status", timeout=10)
    current_engine = status_resp.json().get('current_engine', 'postgresql')
    print(f"\n当前引擎: {current_engine.upper()}")
    
    # 切换到另一个引擎
    target_engine = 'duckdb' if current_engine == 'postgresql' else 'postgresql'
    print(f"尝试切换到: {target_engine.upper()}")
    
    try:
        resp = requests.post(
            f"{BASE_URL}/observability/query-router/force-engine",
            params={"engine": target_engine},
            timeout=10
        )
        result = resp.json()
        
        if result.get('success'):
            print(f"✅ 切换成功: {result.get('message')}")
            
            # 验证切换后的查询
            print(f"\n验证切换后的查询...")
            test_resp = requests.get(f"{BASE_URL}/observability/query-router/test", timeout=30)
            test_data = test_resp.json()
            
            smart = test_data.get('smart_routing', {})
            if smart.get('success'):
                print(f"   智能路由使用引擎: {smart.get('engine', 'unknown').upper()}")
                print(f"   查询耗时: {smart.get('query_time_ms', 0):.2f}ms")
        else:
            print(f"❌ 切换失败: {result.get('message')}")
        
        # 切换回原来的引擎
        print(f"\n切换回原引擎: {current_engine.upper()}")
        requests.post(
            f"{BASE_URL}/observability/query-router/force-engine",
            params={"engine": current_engine},
            timeout=10
        )
        print("✅ 已恢复")
        
        return result
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_v2_api_direct():
    """测试4: 直接调用 v2 API (DuckDB)"""
    print_header("4. 直接调用 v2 API (DuckDB)")
    
    try:
        # 测试 overview
        print("\n📊 v2/orders/overview:")
        start = time.time()
        resp = requests.get("http://localhost:8080/api/v2/orders/overview", timeout=30)
        elapsed = (time.time() - start) * 1000
        data = resp.json()
        
        if data.get('success'):
            result = data.get('data', {})
            print(f"   订单数: {result.get('total_orders', 0):,}")
            print(f"   销售额: ¥{result.get('total_actual_sales', 0):,.2f}")
            print(f"   利润: ¥{result.get('total_profit', 0):,.2f}")
            print(f"   查询耗时: {data.get('query_time_ms', elapsed):.2f}ms")
            print(f"   数据来源: {data.get('source', 'unknown')}")
        else:
            print(f"   ❌ 查询失败")
        
        # 测试 trend
        print("\n📈 v2/orders/trend:")
        start = time.time()
        resp = requests.get("http://localhost:8080/api/v2/orders/trend?days=7", timeout=30)
        elapsed = (time.time() - start) * 1000
        data = resp.json()
        
        if data.get('success'):
            result = data.get('data', {})
            dates = result.get('dates', [])
            print(f"   数据天数: {len(dates)}")
            print(f"   查询耗时: {data.get('query_time_ms', elapsed):.2f}ms")
        else:
            print(f"   ❌ 查询失败")
        
        # 测试 channels
        print("\n📊 v2/orders/channels:")
        start = time.time()
        resp = requests.get("http://localhost:8080/api/v2/orders/channels", timeout=30)
        elapsed = (time.time() - start) * 1000
        data = resp.json()
        
        if data.get('success'):
            result = data.get('data', [])
            print(f"   渠道数: {len(result)}")
            print(f"   查询耗时: {data.get('query_time_ms', elapsed):.2f}ms")
        else:
            print(f"   ❌ 查询失败")
        
        # 测试 status
        print("\n🔧 v2/orders/status:")
        resp = requests.get("http://localhost:8080/api/v2/orders/status", timeout=10)
        data = resp.json()
        
        if data.get('success'):
            status = data.get('data', {})
            print(f"   DuckDB 启用: {status.get('enabled', False)}")
            print(f"   Parquet 文件数: {status.get('raw_parquet_count', 0)}")
            print(f"   Parquet 大小: {status.get('raw_parquet_size_mb', 0):.2f}MB")
        
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_performance_comparison():
    """测试5: 性能压力测试"""
    print_header("5. 性能压力测试 (10次查询)")
    
    iterations = 10
    pg_times = []
    dk_times = []
    
    print("\n正在进行压力测试...")
    
    for i in range(iterations):
        # PostgreSQL (v1 API)
        try:
            start = time.time()
            resp = requests.get(f"{BASE_URL}/orders/overview?use_aggregation=true", timeout=30)
            pg_times.append((time.time() - start) * 1000)
        except:
            pass
        
        # DuckDB (v2 API)
        try:
            start = time.time()
            resp = requests.get("http://localhost:8080/api/v2/orders/overview", timeout=30)
            dk_times.append((time.time() - start) * 1000)
        except:
            pass
        
        print(f"   完成 {i+1}/{iterations}")
    
    if pg_times:
        print(f"\n🐘 PostgreSQL (v1 API):")
        print(f"   平均耗时: {sum(pg_times)/len(pg_times):.2f}ms")
        print(f"   最快: {min(pg_times):.2f}ms")
        print(f"   最慢: {max(pg_times):.2f}ms")
    
    if dk_times:
        print(f"\n🦆 DuckDB (v2 API):")
        print(f"   平均耗时: {sum(dk_times)/len(dk_times):.2f}ms")
        print(f"   最快: {min(dk_times):.2f}ms")
        print(f"   最慢: {max(dk_times):.2f}ms")
    
    if pg_times and dk_times:
        pg_avg = sum(pg_times)/len(pg_times)
        dk_avg = sum(dk_times)/len(dk_times)
        
        print(f"\n📊 对比结论:")
        if dk_avg < pg_avg:
            speedup = pg_avg / dk_avg
            print(f"   DuckDB 更快，加速比: {speedup:.2f}x")
        else:
            speedup = dk_avg / pg_avg
            print(f"   PostgreSQL 更快，加速比: {speedup:.2f}x")

def main():
    print("\n" + "=" * 60)
    print("  🧠 智能查询路由切换测试")
    print("=" * 60)
    print(f"  测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  后端地址: {BASE_URL}")
    print("=" * 60)
    
    # 检查后端是否可用
    try:
        resp = requests.get("http://localhost:8080/api/health", timeout=5)
        if resp.status_code != 200:
            print("\n❌ 后端服务不可用，请先启动后端")
            return
    except:
        print("\n❌ 无法连接后端服务，请先启动后端")
        return
    
    print("\n✅ 后端服务已连接")
    
    # 运行测试
    test_router_status()
    test_smart_routing_query()
    test_force_engine_switch()
    test_v2_api_direct()
    test_performance_comparison()
    
    print_header("测试完成")
    print("\n✅ 所有测试已完成！")
    print("\n💡 提示:")
    print("   - 当前数据量 < 100万，默认使用 PostgreSQL")
    print("   - 数据量达到 100万后，将自动切换到 DuckDB")
    print("   - 可以使用 force-engine API 强制切换引擎进行测试")

if __name__ == "__main__":
    main()
