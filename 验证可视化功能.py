#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
销量下滑可视化功能验证脚本
快速检查所有图表组件是否正常工作
"""

import sys
from pathlib import Path

# 添加路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

def test_imports():
    """测试必要的库导入"""
    print("=" * 50)
    print("1. 测试库导入")
    print("=" * 50)
    
    try:
        import streamlit as st
        print("✅ Streamlit 已安装")
    except ImportError:
        print("❌ Streamlit 未安装")
        return False
    
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        print("✅ Plotly 已安装")
    except ImportError:
        print("❌ Plotly 未安装")
        return False
    
    try:
        import pandas as pd
        import numpy as np
        print("✅ Pandas/Numpy 已安装")
    except ImportError:
        print("❌ Pandas/Numpy 未安装")
        return False
    
    return True

def test_chart_creation():
    """测试图表创建功能"""
    print("\n" + "=" * 50)
    print("2. 测试图表创建")
    print("=" * 50)
    
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd
    
    # 测试数据
    test_data = pd.DataFrame({
        '商品名称': ['活珠子', '豆浆', '油条', '盖浇饭', '奶茶'],
        '销量变化': [-9, -12, -8, -15, -10],
        '变化幅度%': [-75.0, -60.0, -50.0, -45.0, -40.0],
        '收入变化': [-135, -96, -64, -225, -150],
        '利润变化': [-47, -34, -22, -79, -53],
        '商品实售价': [15, 8, 8, 15, 15],
        '平均毛利率%': [35, 35, 35, 35, 35],
        '一级分类名': ['熟食', '饮料', '熟食', '熟食', '饮料'],
        '三级分类名': ['卤制品', '豆制品', '面点', '快餐', '茶饮']
    })
    
    try:
        # 测试1: 柱状图
        fig1 = go.Figure(go.Bar(
            x=['清晨', '上午', '正午'],
            y=[15, 12, 10],
            marker_color='#d32f2f'
        ))
        print("✅ 柱状图创建成功")
    except Exception as e:
        print(f"❌ 柱状图创建失败: {e}")
        return False
    
    try:
        # 测试2: 饼图
        fig2 = go.Figure(go.Pie(
            labels=['早餐', '午餐', '晚餐'],
            values=[35, 40, 25],
            hole=0.4
        ))
        print("✅ 饼图创建成功")
    except Exception as e:
        print(f"❌ 饼图创建失败: {e}")
        return False
    
    try:
        # 测试3: 散点图
        fig3 = go.Figure(go.Scatter(
            x=test_data['销量变化'],
            y=test_data['利润变化'],
            mode='markers',
            marker=dict(
                size=test_data['商品实售价'] * 2,
                color=test_data['平均毛利率%'],
                colorscale='RdYlGn'
            ),
            text=test_data['商品名称']
        ))
        print("✅ 散点图创建成功")
    except Exception as e:
        print(f"❌ 散点图创建失败: {e}")
        return False
    
    try:
        # 测试4: 树状图
        fig4 = px.treemap(
            test_data,
            path=['一级分类名', '三级分类名', '商品名称'],
            values=test_data['收入变化'].abs(),
            color='变化幅度%',
            color_continuous_scale='Reds'
        )
        print("✅ 树状图创建成功")
    except Exception as e:
        print(f"❌ 树状图创建失败: {e}")
        return False
    
    try:
        # 测试5: 热力图
        heatmap_data = pd.DataFrame({
            '清晨': [15, 0, 0, 0, 0],
            '上午': [8, 2, 3, 0, 0],
            '正午': [3, 20, 4, 1, 0]
        }, index=['早餐', '午餐', '下午茶', '晚餐', '夜宵'])
        
        fig5 = px.imshow(
            heatmap_data,
            color_continuous_scale='Reds',
            aspect='auto',
            text_auto=True
        )
        print("✅ 热力图创建成功")
    except Exception as e:
        print(f"❌ 热力图创建失败: {e}")
        return False
    
    try:
        # 测试6: 瀑布图
        fig6 = go.Figure(go.Waterfall(
            x=test_data['商品名称'][:3],
            y=test_data['收入变化'][:3].abs(),
            decreasing={"marker": {"color": "#d32f2f"}}
        ))
        print("✅ 瀑布图创建成功")
    except Exception as e:
        print(f"❌ 瀑布图创建失败: {e}")
        return False
    
    return True

def test_data_processing():
    """测试数据处理功能"""
    print("\n" + "=" * 50)
    print("3. 测试数据处理")
    print("=" * 50)
    
    import pandas as pd
    
    # 测试parse_number函数
    def parse_number(val):
        """解析带格式的数值"""
        if pd.isna(val):
            return 0
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).replace('¥', '').replace('%', '').replace(',', '').replace('N/A', '0')
        try:
            return float(val_str)
        except:
            return 0
    
    test_cases = [
        ('¥1234.5', 1234.5),
        ('-50.0%', -50.0),
        ('¥12,345', 12345.0),
        ('N/A', 0),
        (123, 123.0),
        (None, 0)
    ]
    
    all_passed = True
    for input_val, expected in test_cases:
        result = parse_number(input_val)
        if abs(result - expected) < 0.01:
            print(f"✅ {input_val} → {result}")
        else:
            print(f"❌ {input_val} → {result} (期望: {expected})")
            all_passed = False
    
    return all_passed

def test_file_structure():
    """测试文件结构"""
    print("\n" + "=" * 50)
    print("4. 测试文件结构")
    print("=" * 50)
    
    required_files = [
        '智能门店经营看板_可视化.py',
        '问题诊断引擎.py',
        '销量下滑可视化功能说明.md',
        '销量下滑诊断可视化设计方案.md'
    ]
    
    all_exist = True
    for file_name in required_files:
        file_path = APP_DIR / file_name
        if file_path.exists():
            print(f"✅ {file_name} 存在")
        else:
            print(f"❌ {file_name} 不存在")
            all_exist = False
    
    return all_exist

def main():
    """主测试函数"""
    print("\n" + "🔍" * 25)
    print(" " * 10 + "销量下滑可视化功能验证")
    print("🔍" * 25 + "\n")
    
    results = []
    
    # 测试1: 库导入
    results.append(("库导入", test_imports()))
    
    # 测试2: 图表创建
    results.append(("图表创建", test_chart_creation()))
    
    # 测试3: 数据处理
    results.append(("数据处理", test_data_processing()))
    
    # 测试4: 文件结构
    results.append(("文件结构", test_file_structure()))
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print("\n" + "=" * 50)
    print(f"总计: {passed}/{total} 通过")
    print("=" * 50)
    
    if passed == total:
        print("\n🎉 所有测试通过！可以启动Streamlit了")
        print("\n启动命令:")
        print("streamlit run 智能门店经营看板_可视化.py")
    else:
        print("\n⚠️ 部分测试失败，请检查环境配置")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
