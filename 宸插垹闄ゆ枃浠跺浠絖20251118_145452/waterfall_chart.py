#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
瀑布图工厂函数 - 补充到 echarts_factory.py
"""

def format_number(value):
    """智能数值格式化"""
    if value == int(value):
        return int(value)
    else:
        return round(value, 1)

COMMON_COLORS = {
    'red': ['#FF6B6B', '#E74C3C', '#C0392B'],
}

COMMON_ANIMATION = {
    'animationEasing': 'elasticOut',
    'animationDuration': 1000
}

def create_waterfall_chart(
    data,
    name_field,
    value_field,
    title='瀑布图',
    color_scheme='red',
    height='400px'
):
    """
    创建横向柱状图（用于展示收入损失TOP10，商品名称水平显示更清晰）
    
    Args:
        data: pandas DataFrame 或 dict
        name_field: 名称字段（Y轴）
        value_field: 数值字段（负值表示损失）
        title: 图表标题
        color_scheme: 配色方案
        height: 图表高度
    """
    try:
        from dash_echarts import DashECharts
    except ImportError:
        return None
    
    # 数据处理 - 反转顺序，让损失最大的在顶部
    if hasattr(data, 'to_dict'):
        names = data[name_field].tolist()[::-1]  # 反转
        values = [format_number(abs(v)) for v in data[value_field].tolist()][::-1]
    else:
        names = data[name_field][::-1]
        values = [format_number(abs(v)) for v in data[value_field]][::-1]
    
    option = {
        'title': {
            'text': title,
            'left': 'center',
            'top': '2%',
            'textStyle': {'fontSize': 18, 'fontWeight': 'bold', 'color': '#1a1a1a'}
        },
        'tooltip': {
            'trigger': 'axis',
            'formatter': '{b}<br/>¥{c}',
            'axisPointer': {'type': 'shadow'}
        },
        'grid': {
            'left': '5%',  # 减少左侧空白，让图表更靠左
            'right': '8%',
            'top': '12%',
            'bottom': '8%',
            'containLabel': True  # 自动计算包含标签的空间
        },
        'xAxis': {
            'type': 'value',
            'name': '金额（元）',
            'axisLabel': {'formatter': '¥{value}'},
            'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}}
        },
        'yAxis': {
            'type': 'category',
            'data': names,
            'axisLabel': {
                'fontSize': 11,
                'overflow': 'truncate',
                'width': 100,  # 商品名称最大宽度
                'interval': 0  # 显示所有标签
            },
            'axisTick': {'alignWithLabel': True}
        },
        'series': [{
            'name': '收入损失',
            'type': 'bar',
            'data': values,
            'itemStyle': {
                'color': COMMON_COLORS[color_scheme][0],
                'borderRadius': [0, 4, 4, 0]  # 横向柱状图圆角
            },
            'label': {
                'show': True,
                'position': 'right',  # 标签显示在右侧
                'formatter': '¥{c}',
                'fontSize': 10,
                'fontWeight': 'bold',
                'color': '#333'
            },
            'emphasis': {
                'itemStyle': {
                    'color': COMMON_COLORS[color_scheme][1],
                    'shadowBlur': 10,
                    'shadowColor': 'rgba(0,0,0,0.3)'
                }
            },
            'barWidth': '50%'
        }]
    }
    
    option.update(COMMON_ANIMATION)
    
    return DashECharts(option=option, style={'height': height, 'width': '100%'})
