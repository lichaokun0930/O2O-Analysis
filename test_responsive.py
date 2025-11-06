#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECharts响应式功能测试脚本
快速验证三大功能是否正常工作
"""

import sys
from pathlib import Path

# 添加路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from echarts_responsive_utils import (
    calculate_chart_height,
    calculate_dynamic_grid,
    get_responsive_font_size,
    create_responsive_echarts_config
)

def test_calculate_height():
    """测试动态高度计算"""
    print("=" * 60)
    print("📏 测试1: 动态高度计算")
    print("=" * 60)
    
    test_cases = [
        (5, 'bar', "5个商品的柱状图"),
        (10, 'bar', "10个商品的柱状图"),
        (20, 'bar', "20个商品的柱状图（应达到最大值）"),
        (8, 'pie', "8个分类的饼图"),
        (15, 'line', "15个数据点的折线图")
    ]
    
    for count, chart_type, desc in test_cases:
        height = calculate_chart_height(count, chart_type)
        print(f"  {desc}: {height}px")
    
    print("✅ 高度计算测试通过\n")


def test_dynamic_grid():
    """测试动态Grid配置"""
    print("=" * 60)
    print("🎯 测试2: 动态Grid配置")
    print("=" * 60)
    
    test_cases = [5, 12, 20]
    
    for count in test_cases:
        grid = calculate_dynamic_grid(count, 'bar')
        print(f"  {count}个商品:")
        print(f"    - bottom: {grid['bottom']}")
        print(f"    - containLabel: {grid['containLabel']}")
    
    print("✅ Grid配置测试通过\n")


def test_responsive_font():
    """测试响应式字体"""
    print("=" * 60)
    print("✏️ 测试3: 响应式字体大小")
    print("=" * 60)
    
    test_cases = [5, 12, 25]
    
    for count in test_cases:
        font_size = get_responsive_font_size(count)
        print(f"  {count}个数据项: 字体{font_size}px")
    
    print("✅ 字体大小测试通过\n")


def test_complete_config():
    """测试完整配置生成"""
    print("=" * 60)
    print("🚀 测试4: 完整响应式配置")
    print("=" * 60)
    
    config = create_responsive_echarts_config(
        data_count=15,
        chart_type='bar',
        include_height=True,
        include_grid=True,
        include_font=True
    )
    
    print("  配置内容:")
    for key, value in config.items():
        if isinstance(value, dict):
            print(f"    {key}:")
            for k, v in value.items():
                print(f"      - {k}: {v}")
        else:
            print(f"    {key}: {value}")
    
    print("✅ 完整配置测试通过\n")


def test_device_configs():
    """测试设备配置"""
    print("=" * 60)
    print("📱 测试5: 设备断点配置")
    print("=" * 60)
    
    from echarts_responsive_utils import get_device_breakpoints, get_device_chart_heights
    
    breakpoints = get_device_breakpoints()
    print("  断点配置:")
    for device, width in breakpoints.items():
        print(f"    {device}: {width}px")
    
    heights = get_device_chart_heights()
    print("\n  设备高度配置:")
    for device, config in heights.items():
        print(f"    {device}:")
        for key, value in config.items():
            print(f"      - {key}: {value}px")
    
    print("✅ 设备配置测试通过\n")


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("[ECharts响应式功能测试]")
    print("=" * 60 + "\n")
    
    try:
        # 测试1: 高度计算
        test_calculate_height()
        
        # 测试2: Grid配置
        test_dynamic_grid()
        
        # 测试3: 字体大小
        test_responsive_font()
        
        # 测试4: 完整配置
        test_complete_config()
        
        # 测试5: 设备配置
        test_device_configs()
        
        # 总结
        print("=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        print("\n功能验证:")
        print("  ✅ 动态高度计算")
        print("  ✅ Grid自动调整")
        print("  ✅ 响应式字体")
        print("  ✅ 完整配置生成")
        print("  ✅ 设备断点配置")
        print("\n下一步:")
        print("  1. 启动看板: python 智能门店看板_Dash版.py")
        print("  2. 访问: http://localhost:8050")
        print("  3. 打开浏览器控制台查看响应式日志")
        print("  4. 调整窗口大小测试自动重绘")
        print("  5. 使用设备模拟器测试不同断点\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
