#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实端到端性能测试

测试场景:
1. 启动看板服务器
2. 等待服务器就绪
3. 模拟浏览器访问"今日必做"Tab
4. 测量从点击到数据完全加载的时间

作者: AI Assistant
版本: V8.2
日期: 2025-12-11
"""

import sys
from pathlib import Path
import time
import requests
import json
from datetime import datetime

# 添加项目路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))


def print_section(title, char='='):
    """打印章节标题"""
    print(f"\n{char*80}")
    print(f"{title}")
    print(f"{char*80}\n")


def wait_for_server(url="http://localhost:8051", timeout=60):
    """等待服务器启动"""
    print(f"等待服务器启动: {url}")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                elapsed = time.time() - start_time
                print(f"✅ 服务器已就绪，耗时: {elapsed:.2f}秒")
                return True
        except:
            pass
        
        time.sleep(1)
        elapsed = time.time() - start_time
        print(f"   等待中... ({elapsed:.0f}/{timeout}秒)", end='\r')
    
    print(f"\n❌ 服务器启动超时")
    return False


def test_diagnosis_callback():
    """
    测试"今日必做"Tab的诊断数据加载
    
    模拟用户点击Tab后的回调请求
    """
    print_section("测试: 今日必做Tab - 诊断数据加载")
    
    # Dash回调的URL格式
    callback_url = "http://localhost:8051/_dash-update-component"
    
    # 模拟点击"今日必做"Tab的回调请求
    # 这是Dash的内部回调格式
    payload = {
        "output": "diagnosis-cards-container.children",
        "outputs": {
            "id": "diagnosis-cards-container",
            "property": "children"
        },
        "inputs": [
            {
                "id": "current-data-store",
                "property": "data",
                "value": None  # 首次加载，无缓存数据
            }
        ],
        "changedPropIds": ["current-data-store.data"],
        "state": []
    }
    
    print("📊 模拟用户点击'今日必做'Tab...")
    print(f"   请求URL: {callback_url}")
    print(f"   回调: diagnosis-cards-container.children")
    
    try:
        # 测试1: 首次加载（无缓存）
        print("\n[测试1] 首次加载（无缓存）")
        print("-" * 80)
        
        start_time = time.time()
        
        response = requests.post(
            callback_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2分钟超时
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ 请求成功")
            print(f"⏱️  加载时间: {elapsed:.2f}秒")
            print(f"📦 响应大小: {len(response.content)} 字节")
            
            # 尝试解析响应
            try:
                data = response.json()
                if 'response' in data:
                    print(f"✅ 数据已返回")
                else:
                    print(f"⚠️  响应格式异常")
            except:
                print(f"⚠️  无法解析JSON响应")
            
            return elapsed
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"   响应: {response.text[:200]}")
            return None
            
    except requests.Timeout:
        print(f"❌ 请求超时（>120秒）")
        return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_with_cache():
    """测试缓存命中的情况"""
    print_section("测试: 缓存命中情况")
    
    callback_url = "http://localhost:8051/_dash-update-component"
    
    payload = {
        "output": "diagnosis-cards-container.children",
        "outputs": {
            "id": "diagnosis-cards-container",
            "property": "children"
        },
        "inputs": [
            {
                "id": "current-data-store",
                "property": "data",
                "value": None
            }
        ],
        "changedPropIds": ["current-data-store.data"],
        "state": []
    }
    
    print("📊 测试缓存命中...")
    print("   提示: 如果后台任务已预热缓存，这次应该很快")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            callback_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ 请求成功")
            print(f"⏱️  加载时间: {elapsed:.2f}秒")
            
            if elapsed < 2:
                print(f"🚀 缓存命中! 加载速度极快")
            elif elapsed < 10:
                print(f"⚡ 加载较快，可能使用了缓存")
            else:
                print(f"⚠️  加载较慢，可能未命中缓存")
            
            return elapsed
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def check_redis_cache():
    """检查Redis缓存状态"""
    print_section("检查Redis缓存状态")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # 检查诊断缓存
        cache_key = 'diagnosis:latest'
        
        if r.exists(cache_key):
            ttl = r.ttl(cache_key)
            print(f"✅ 缓存存在: {cache_key}")
            print(f"   剩余时间: {ttl}秒 ({ttl//60}分钟)")
            return True
        else:
            print(f"❌ 缓存不存在: {cache_key}")
            print(f"   提示: 后台任务可能还未完成预热")
            return False
            
    except Exception as e:
        print(f"❌ 无法连接Redis: {e}")
        return False


def main():
    """主测试流程"""
    print("\n" + "="*80)
    print("真实端到端性能测试")
    print("="*80)
    print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n⚠️  重要提示:")
    print("1. 请先启动看板: python -u 智能门店看板_Dash版.py")
    print("2. 或使用启动脚本: .\\启动看板-调试模式.ps1")
    print("3. 等待服务器完全启动后，按回车继续...")
    
    input("\n按回车键开始测试...")
    
    # 步骤1: 检查服务器
    print_section("步骤1: 检查服务器状态")
    
    if not wait_for_server():
        print("\n❌ 服务器未启动，请先启动看板")
        print("\n启动命令:")
        print("   python -u 智能门店看板_Dash版.py")
        print("   或")
        print("   .\\启动看板-调试模式.ps1")
        return
    
    # 步骤2: 检查Redis缓存
    has_cache = check_redis_cache()
    
    # 步骤3: 测试首次加载
    first_load_time = test_diagnosis_callback()
    
    if first_load_time is None:
        print("\n❌ 测试失败，无法获取加载时间")
        return
    
    # 步骤4: 等待一下，再测试缓存命中
    print("\n等待3秒后测试缓存命中...")
    time.sleep(3)
    
    second_load_time = test_with_cache()
    
    # 汇总结果
    print_section("测试结果汇总")
    
    print(f"📊 测试数据:")
    print(f"   - 服务器地址: http://localhost:8051")
    print(f"   - 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   - Redis缓存: {'✅ 存在' if has_cache else '❌ 不存在'}")
    
    print(f"\n⏱️  加载时间:")
    print(f"   - 首次加载: {first_load_time:.2f}秒")
    if second_load_time:
        print(f"   - 第二次加载: {second_load_time:.2f}秒")
        
        if second_load_time < first_load_time:
            improvement = (first_load_time - second_load_time) / first_load_time * 100
            print(f"   - 性能提升: {improvement:.1f}%")
    
    print(f"\n📈 性能评估:")
    
    if first_load_time < 2:
        print(f"   ✅ 首次加载极快（<2秒）- 缓存已预热")
    elif first_load_time < 10:
        print(f"   ✅ 首次加载较快（<10秒）- 计算优化生效")
    elif first_load_time < 30:
        print(f"   ⚠️  首次加载中等（<30秒）- 可能需要进一步优化")
    else:
        print(f"   ❌ 首次加载较慢（>{first_load_time:.0f}秒）- 需要检查问题")
    
    if second_load_time:
        if second_load_time < 2:
            print(f"   ✅ 缓存命中极快（<2秒）- 缓存优化生效")
        elif second_load_time < 5:
            print(f"   ⚡ 缓存命中较快（<5秒）- 部分优化生效")
        else:
            print(f"   ⚠️  缓存命中较慢（>{second_load_time:.0f}秒）- 缓存可能未生效")
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)
    
    print("\n💡 说明:")
    print("1. 首次加载时间包括:")
    print("   - 数据查询")
    print("   - 诊断计算")
    print("   - 渲染组件")
    print("   - 网络传输")
    
    print("\n2. 如果首次加载很快（<2秒），说明:")
    print("   - 后台任务已预热缓存")
    print("   - 直接从Redis读取")
    print("   - 优化完全生效")
    
    print("\n3. 如果首次加载较慢（>10秒），可能是:")
    print("   - 后台任务还未完成预热")
    print("   - Redis缓存未启用")
    print("   - 需要等待5分钟让后台任务运行")
    
    print("\n4. 建议:")
    print("   - 启动看板后等待1-2分钟")
    print("   - 让后台任务完成首次缓存预热")
    print("   - 然后再访问'今日必做'Tab")
    
    print("="*80)


if __name__ == "__main__":
    main()
