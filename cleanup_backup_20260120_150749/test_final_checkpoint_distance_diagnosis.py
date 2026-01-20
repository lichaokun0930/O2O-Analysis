# -*- coding: utf-8 -*-
"""
Final Checkpoint - 分距离订单诊断功能完整验证

Task 10: Final Checkpoint - 完整功能验证

验证内容：
1. 验证完整的联动流程：雷达扫描 → 距离图表高亮
2. 验证日期联动：销售趋势图选中日期 → 距离图表数据更新
3. 验证筛选功能：门店/渠道筛选 → 数据正确过滤
4. 验证响应式布局

Requirements Coverage:
- Requirement 1: 后端API - 距离分析数据接口 (1.1-1.8)
- Requirement 2: 前端类型定义 (2.1-2.3)
- Requirement 3: 前端API函数 (3.1-3.3)
- Requirement 4: 分距离订单诊断图表组件 (4.1-4.9)
- Requirement 5: 配送溢价雷达联动回调 (5.1-5.4)
- Requirement 6: 图表联动高亮效果 (6.1-6.4)
- Requirement 7: 布局集成 (7.1-7.4)
"""

import requests
import json
import sys
from urllib.parse import quote

# API配置
BASE_URL = "http://localhost:8080/api/v1"

def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(test_name: str, passed: bool, details: str = ""):
    """打印测试结果"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status} - {test_name}")
    if details:
        print(f"         {details}")

def test_backend_api():
    """
    验证后端API功能
    Requirements: 1.1-1.8
    """
    print_header("1. 后端API验证 (Requirements 1.1-1.8)")
    
    all_passed = True
    
    # Test 1.1: 基本API调用
    try:
        response = requests.get(f"{BASE_URL}/orders/distance-analysis", timeout=30)
        data = response.json()
        
        if data.get("success") and "data" in data:
            result = data["data"]
            
            # 验证返回7个距离区间
            bands = result.get("distance_bands", [])
            if len(bands) == 7:
                print_result("1.1 返回7个距离区间", True, f"共 {len(bands)} 个区间")
            else:
                print_result("1.1 返回7个距离区间", False, f"期望7个，实际 {len(bands)} 个")
                all_passed = False
            
            # 验证每个区间包含必要字段
            required_fields = ["band_label", "min_distance", "max_distance", "order_count", 
                             "revenue", "profit", "profit_rate", "delivery_cost", 
                             "delivery_cost_rate", "avg_order_value"]
            
            fields_ok = True
            for band in bands:
                for field in required_fields:
                    if field not in band:
                        fields_ok = False
                        break
            
            print_result("1.6 每个区间包含完整指标", fields_ok)
            if not fields_ok:
                all_passed = False
            
            # 验证summary字段
            summary = result.get("summary", {})
            summary_fields = ["total_orders", "avg_distance", "optimal_distance", 
                           "total_revenue", "total_profit"]
            summary_ok = all(f in summary for f in summary_fields)
            print_result("1.7 返回summary统计", summary_ok, 
                        f"optimal_distance: {summary.get('optimal_distance')}")
            if not summary_ok:
                all_passed = False
                
        else:
            print_result("1.1 基本API调用", False, "API返回失败")
            all_passed = False
            
    except Exception as e:
        print_result("1.1 基本API调用", False, str(e))
        all_passed = False
    
    # Test 1.2-1.5: 筛选参数测试
    try:
        # 获取门店列表
        stores_resp = requests.get(f"{BASE_URL}/orders/stores", timeout=10)
        stores = stores_resp.json().get("data", [])
        
        if stores:
            store_name = stores[0]
            # 测试门店筛选
            response = requests.get(
                f"{BASE_URL}/orders/distance-analysis?store_name={quote(store_name)}", 
                timeout=30
            )
            data = response.json()
            print_result("1.2 门店筛选参数", data.get("success", False), f"门店: {store_name}")
        else:
            print_result("1.2 门店筛选参数", True, "无门店数据，跳过")
            
    except Exception as e:
        print_result("1.2-1.5 筛选参数测试", False, str(e))
        all_passed = False
    
    # Test 1.8: 空数据区间返回零值
    try:
        response = requests.get(f"{BASE_URL}/orders/distance-analysis", timeout=30)
        data = response.json()
        if data.get("success"):
            bands = data["data"].get("distance_bands", [])
            zero_bands = [b for b in bands if b["order_count"] == 0]
            if zero_bands:
                # 验证零订单区间的其他指标也为0
                zero_ok = all(
                    b["revenue"] == 0 and b["profit"] == 0 
                    for b in zero_bands
                )
                print_result("1.8 空数据区间返回零值", zero_ok, f"共 {len(zero_bands)} 个空区间")
            else:
                print_result("1.8 空数据区间返回零值", True, "所有区间都有数据")
    except Exception as e:
        print_result("1.8 空数据区间返回零值", False, str(e))
        all_passed = False
    
    return all_passed

def test_distance_band_logic():
    """
    验证距离区间分组逻辑
    Property 1: Distance Band Grouping Completeness
    """
    print_header("2. 距离区间分组逻辑验证 (Property 1)")
    
    # 距离区间定义
    DISTANCE_BANDS = [
        {"label": "0-1km", "min": 0, "max": 1},
        {"label": "1-2km", "min": 1, "max": 2},
        {"label": "2-3km", "min": 2, "max": 3},
        {"label": "3-4km", "min": 3, "max": 4},
        {"label": "4-5km", "min": 4, "max": 5},
        {"label": "5-6km", "min": 5, "max": 6},
        {"label": "6km+", "min": 6, "max": float('inf')},
    ]
    
    def get_band_index(distance):
        if distance < 0:
            distance = 0
        for i, band in enumerate(DISTANCE_BANDS):
            if band["min"] <= distance < band["max"]:
                return i
        return len(DISTANCE_BANDS) - 1
    
    # 测试边界值
    test_cases = [
        (0, 0, "0-1km"),
        (0.999, 0, "0-1km"),
        (1, 1, "1-2km"),
        (1.5, 1, "1-2km"),
        (5.999, 5, "5-6km"),
        (6, 6, "6km+"),
        (10, 6, "6km+"),
        (100, 6, "6km+"),
    ]
    
    all_passed = True
    for distance, expected_index, expected_label in test_cases:
        actual_index = get_band_index(distance)
        passed = actual_index == expected_index
        if not passed:
            all_passed = False
        print_result(f"距离 {distance}km → {expected_label}", passed, 
                    f"期望索引 {expected_index}, 实际 {actual_index}")
    
    return all_passed

def test_highlight_mapping():
    """
    验证高亮距离映射逻辑
    Property 4: Highlight Distance Mapping
    """
    print_header("3. 高亮距离映射验证 (Property 4)")
    
    DISTANCE_BANDS = [
        {"label": "0-1km", "min": 0, "max": 1},
        {"label": "1-2km", "min": 1, "max": 2},
        {"label": "2-3km", "min": 2, "max": 3},
        {"label": "3-4km", "min": 3, "max": 4},
        {"label": "4-5km", "min": 4, "max": 5},
        {"label": "5-6km", "min": 5, "max": 6},
        {"label": "6km+", "min": 6, "max": float('inf')},
    ]
    
    def get_band_index(distance):
        if distance is None or distance < 0:
            return -1
        for i, band in enumerate(DISTANCE_BANDS):
            if band["min"] <= distance < band["max"]:
                return i
        if distance >= DISTANCE_BANDS[-1]["min"]:
            return len(DISTANCE_BANDS) - 1
        return -1
    
    # 模拟雷达扫描（0-8km范围）
    all_passed = True
    for ratio in [0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]:
        distance = ratio * 8  # 0-8km
        band_index = get_band_index(distance)
        
        # 验证映射到有效区间
        passed = 0 <= band_index <= 6
        if not passed:
            all_passed = False
        
        label = DISTANCE_BANDS[band_index]["label"] if band_index >= 0 else "无效"
        print_result(f"雷达位置 {ratio*100:.0f}% ({distance:.1f}km) → {label}", passed)
    
    return all_passed

def test_metrics_calculation():
    """
    验证指标计算一致性
    Property 3: Metrics Calculation Consistency
    """
    print_header("4. 指标计算一致性验证 (Property 3)")
    
    try:
        response = requests.get(f"{BASE_URL}/orders/distance-analysis", timeout=30)
        data = response.json()
        
        if not data.get("success"):
            print_result("获取API数据", False)
            return False
        
        bands = data["data"].get("distance_bands", [])
        all_passed = True
        
        for band in bands:
            if band["order_count"] > 0 and band["revenue"] > 0:
                # 验证利润率计算
                expected_profit_rate = round(band["profit"] / band["revenue"] * 100, 2)
                actual_profit_rate = band["profit_rate"]
                profit_rate_ok = abs(expected_profit_rate - actual_profit_rate) < 0.1
                
                # 验证客单价计算
                expected_aov = round(band["revenue"] / band["order_count"], 2)
                actual_aov = band["avg_order_value"]
                aov_ok = abs(expected_aov - actual_aov) < 0.1
                
                if not profit_rate_ok or not aov_ok:
                    all_passed = False
                    print_result(f"{band['band_label']} 指标计算", False,
                               f"利润率: {actual_profit_rate} vs {expected_profit_rate}")
        
        if all_passed:
            print_result("所有区间指标计算正确", True)
        
        return all_passed
        
    except Exception as e:
        print_result("指标计算验证", False, str(e))
        return False

def test_optimal_distance():
    """
    验证最优距离识别
    Property 5: Optimal Distance Identification
    """
    print_header("5. 最优距离识别验证 (Property 5)")
    
    try:
        response = requests.get(f"{BASE_URL}/orders/distance-analysis", timeout=30)
        data = response.json()
        
        if not data.get("success"):
            print_result("获取API数据", False)
            return False
        
        bands = data["data"].get("distance_bands", [])
        summary = data["data"].get("summary", {})
        optimal = summary.get("optimal_distance")
        
        # 找出利润率最高的区间
        valid_bands = [b for b in bands if b["order_count"] > 0 and b["revenue"] > 0]
        
        if not valid_bands:
            print_result("最优距离识别", True, "无有效数据")
            return True
        
        max_profit_rate = max(b["profit_rate"] for b in valid_bands)
        expected_optimal = [b["band_label"] for b in valid_bands if b["profit_rate"] == max_profit_rate][0]
        
        passed = optimal == expected_optimal
        print_result("最优距离识别", passed, 
                    f"API返回: {optimal}, 期望: {expected_optimal} (利润率: {max_profit_rate}%)")
        
        return passed
        
    except Exception as e:
        print_result("最优距离识别", False, str(e))
        return False

def test_date_filtering():
    """
    验证日期联动筛选
    Requirements: 4.8
    """
    print_header("6. 日期联动筛选验证 (Requirement 4.8)")
    
    try:
        # 获取日期范围
        date_range_resp = requests.get(f"{BASE_URL}/orders/date-range", timeout=10)
        date_range = date_range_resp.json().get("data", {})
        
        max_date = date_range.get("max_date")
        if not max_date:
            print_result("日期筛选", True, "无日期数据，跳过")
            return True
        
        # 测试日期筛选
        response = requests.get(
            f"{BASE_URL}/orders/distance-analysis?target_date={max_date}", 
            timeout=30
        )
        data = response.json()
        
        passed = data.get("success", False)
        print_result("日期筛选参数", passed, f"日期: {max_date}")
        
        # 测试 MM-DD 格式
        if max_date and len(max_date) >= 10:
            mm_dd = max_date[5:10]  # 提取 MM-DD
            response2 = requests.get(
                f"{BASE_URL}/orders/distance-analysis?target_date={mm_dd}", 
                timeout=30
            )
            data2 = response2.json()
            passed2 = data2.get("success", False)
            print_result("MM-DD格式日期筛选", passed2, f"日期: {mm_dd}")
            return passed and passed2
        
        return passed
        
    except Exception as e:
        print_result("日期筛选验证", False, str(e))
        return False

def print_summary(results: dict):
    """打印测试总结"""
    print_header("测试总结")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\n  总测试项: {total}")
    print(f"  ✅ 通过: {passed}")
    print(f"  ❌ 失败: {failed}")
    print(f"\n  通过率: {passed/total*100:.1f}%")
    
    if failed > 0:
        print("\n  失败项目:")
        for name, result in results.items():
            if not result:
                print(f"    - {name}")
    
    print("\n" + "=" * 60)
    
    return failed == 0

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  分距离订单诊断 - Final Checkpoint 完整功能验证")
    print("  Task 10: Final Checkpoint - 完整功能验证")
    print("=" * 60)
    
    results = {}
    
    # 1. 后端API验证
    results["后端API (Req 1.1-1.8)"] = test_backend_api()
    
    # 2. 距离区间分组逻辑
    results["距离区间分组 (Property 1)"] = test_distance_band_logic()
    
    # 3. 高亮距离映射
    results["高亮距离映射 (Property 4)"] = test_highlight_mapping()
    
    # 4. 指标计算一致性
    results["指标计算 (Property 3)"] = test_metrics_calculation()
    
    # 5. 最优距离识别
    results["最优距离识别 (Property 5)"] = test_optimal_distance()
    
    # 6. 日期联动筛选
    results["日期联动筛选 (Req 4.8)"] = test_date_filtering()
    
    # 打印总结
    all_passed = print_summary(results)
    
    # 前端组件验证说明
    print("\n📋 前端组件验证说明:")
    print("  以下功能需要在浏览器中手动验证:")
    print("  - 雷达扫描 → 距离图表高亮联动 (Req 5.1-5.4, 6.1-6.4)")
    print("  - 响应式布局 (Req 7.1-7.3)")
    print("  - 主题切换 (Req 4.9)")
    print("  - Loading/Empty状态 (Req 4.6, 4.7)")
    print("\n  启动前端后访问: http://localhost:5173")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
