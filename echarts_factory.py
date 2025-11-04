#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECharts 图表工厂函数库
提供统一的 ECharts 图表创建接口，替代 Plotly 图表
"""

try:
    from dash_echarts import DashECharts
    ECHARTS_AVAILABLE = True
except ImportError:
    ECHARTS_AVAILABLE = False


# ==================== 数值格式化工具 ====================

def format_number(value):
    """
    智能数值格式化：整数显示整数，有小数则保留一位
    
    Args:
        value: 数值
    
    Returns:
        格式化后的数值（整数或保留一位小数）
    """
    if value == int(value):
        return int(value)
    else:
        return round(value, 1)


# ==================== 通用配置 ====================

COMMON_COLORS = {
    'blue': ['#4A90E2', '#2E5C8A', '#1A3A5C'],
    'red': ['#FF6B6B', '#E74C3C', '#C0392B'],
    'green': ['#2ECC71', '#27AE60', '#229954'],
    'orange': ['#FF7F0E', '#E67E22', '#D35400'],
    'purple': ['#9B59B6', '#8E44AD', '#7D3C98'],
    'yellow': ['#F39C12', '#E67E22', '#D35400']
}

COMMON_ANIMATION = {
    'animationEasing': 'elasticOut',
    'animationDuration': 1000
}

COMMON_TOOLTIP = {
    'trigger': 'axis',
    'backgroundColor': 'rgba(255,255,255,0.95)',
    'borderColor': '#ccc',
    'borderWidth': 1,
    'textStyle': {'color': '#333', 'fontSize': 12}
}


# ==================== 柱状图工厂 ====================

def create_bar_chart(
    data,
    x_field,
    y_field,
    title='柱状图',
    color_scheme='blue',
    orientation='vertical',
    show_label=True,
    height='400px'
):
    """
    创建柱状图
    
    Args:
        data: pandas DataFrame 或 dict
        x_field: X轴字段名
        y_field: Y轴字段名（可以是列表，支持多系列）
        title: 图表标题
        color_scheme: 配色方案 ('blue', 'red', 'green', etc.)
        orientation: 'vertical' 或 'horizontal'
        show_label: 是否显示数据标签
        height: 图表高度
    """
    if not ECHARTS_AVAILABLE:
        return None
    
    # 数据处理
    if hasattr(data, 'to_dict'):  # pandas DataFrame
        x_data = data[x_field].tolist()
        if isinstance(y_field, list):
            y_data = [[format_number(v) for v in data[f].tolist()] for f in y_field]
        else:
            y_data = [format_number(v) for v in data[y_field].tolist()]
    else:  # dict
        x_data = data[x_field]
        if isinstance(y_field, list):
            y_data = [[format_number(v) for v in data[f]] for f in y_field]
        else:
            y_data = [format_number(v) for v in data[y_field]]
    
    # 单系列还是多系列
    is_multi = isinstance(y_field, list)
    
    if orientation == 'horizontal':
        # 横向柱状图
        option = {
            'title': {'text': title, 'left': 'center', 'top': '3%', 
                     'textStyle': {'fontSize': 18, 'fontWeight': 'bold', 'color': '#1a1a1a'}},
            'tooltip': dict(COMMON_TOOLTIP, trigger='axis', axisPointer={'type': 'shadow'}),
            'grid': {'left': '15%', 'right': '8%', 'top': '15%', 'bottom': '10%', 'containLabel': True},
            'xAxis': {'type': 'value', 'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}}},
            'yAxis': {'type': 'category', 'data': x_data, 'axisLabel': {'fontSize': 10}},
            'series': [{
                'name': y_field if not is_multi else y_field[i],
                'type': 'bar',
                'data': y_data if not is_multi else y_data[i],
                'barWidth': '60%',
                'itemStyle': {
                    'color': {
                        'type': 'linear', 'x': 0, 'y': 0, 'x2': 1, 'y2': 0,
                        'colorStops': [
                            {'offset': 0, 'color': COMMON_COLORS[color_scheme][0]},
                            {'offset': 1, 'color': COMMON_COLORS[color_scheme][1]}
                        ]
                    },
                    'borderRadius': [0, 8, 8, 0],
                    'shadowColor': f'rgba{tuple(list(int(COMMON_COLORS[color_scheme][0][i:i+2], 16) for i in (1, 3, 5)) + [0.3])}',
                    'shadowBlur': 10
                },
                'label': {'show': show_label, 'position': 'right', 'fontSize': 10, 'fontWeight': 'bold'},
                'animationDelay': '{dataIndex} * 80'
            } for i in range(len(y_field) if is_multi else 1)]
        }
    else:
        # 纵向柱状图
        option = {
            'title': {'text': title, 'left': 'center', 'top': '3%',
                     'textStyle': {'fontSize': 18, 'fontWeight': 'bold', 'color': '#1a1a1a'}},
            'tooltip': dict(COMMON_TOOLTIP, trigger='axis', axisPointer={'type': 'shadow'}),
            'grid': {'left': '8%', 'right': '8%', 'top': '20%', 'bottom': '15%', 'containLabel': True},
            'xAxis': {'type': 'category', 'data': x_data, 'axisLabel': {'rotate': 30, 'fontSize': 10}},
            'yAxis': {'type': 'value', 'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}}},
            'series': [{
                'name': y_field if not is_multi else y_field[i],
                'type': 'bar',
                'data': y_data if not is_multi else y_data[i],
                'barWidth': '50%',
                'itemStyle': {
                    'color': {
                        'type': 'linear', 'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': COMMON_COLORS[color_scheme][0]},
                            {'offset': 0.5, 'color': COMMON_COLORS[color_scheme][1]},
                            {'offset': 1, 'color': COMMON_COLORS[color_scheme][2]}
                        ]
                    },
                    'borderRadius': [8, 8, 0, 0],
                    'shadowColor': 'rgba(0,0,0,0.2)',
                    'shadowBlur': 10
                },
                'label': {'show': show_label, 'position': 'top', 'fontSize': 10, 'fontWeight': 'bold'},
                'animationDelay': '{dataIndex} * 50'
            } for i in range(len(y_field) if is_multi else 1)]
        }
    
    option.update(COMMON_ANIMATION)
    
    return DashECharts(option=option, style={'height': height, 'width': '100%'})


# ==================== 折线图工厂 ====================

def create_line_chart(
    data,
    x_field,
    y_fields,
    title='折线图',
    color_schemes=None,
    smooth=True,
    show_area=True,
    height='400px'
):
    """
    创建折线图（支持多系列）
    
    Args:
        data: pandas DataFrame 或 dict
        x_field: X轴字段名
        y_fields: Y轴字段名（可以是列表，支持多系列）
        title: 图表标题
        color_schemes: 颜色方案列表（与y_fields对应）
        smooth: 是否平滑曲线
        show_area: 是否显示区域填充
        height: 图表高度
    """
    if not ECHARTS_AVAILABLE:
        return None
    
    # 数据处理
    if hasattr(data, 'to_dict'):
        x_data = data[x_field].tolist()
        if not isinstance(y_fields, list):
            y_fields = [y_fields]
        y_data_list = [[format_number(v) for v in data[f].tolist()] for f in y_fields]
    else:
        x_data = data[x_field]
        if not isinstance(y_fields, list):
            y_fields = [y_fields]
        y_data_list = [[format_number(v) for v in data[f]] for f in y_fields]
    
    if color_schemes is None:
        color_schemes = ['blue', 'orange', 'green', 'red', 'purple'][:len(y_fields)]
    
    series = []
    for i, (field, y_data, color_scheme) in enumerate(zip(y_fields, y_data_list, color_schemes)):
        series_config = {
            'name': field,
            'type': 'line',
            'data': y_data,
            'smooth': smooth,
            'symbol': ['circle', 'diamond', 'triangle'][i % 3],
            'symbolSize': 8,
            'lineStyle': {'width': 3, 'color': COMMON_COLORS[color_scheme][0]},
            'itemStyle': {'color': COMMON_COLORS[color_scheme][0], 'borderWidth': 2, 'borderColor': '#fff'}
        }
        
        if show_area:
            series_config['areaStyle'] = {
                'color': {
                    'type': 'linear', 'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                    'colorStops': [
                        {'offset': 0, 'color': f'rgba{tuple(list(int(COMMON_COLORS[color_scheme][0][i:i+2], 16) for i in (1, 3, 5)) + [0.3])}'},
                        {'offset': 1, 'color': f'rgba{tuple(list(int(COMMON_COLORS[color_scheme][0][i:i+2], 16) for i in (1, 3, 5)) + [0.05])}'}
                    ]
                }
            }
        
        series.append(series_config)
    
    option = {
        'title': {'text': title, 'left': 'center', 'top': '3%',
                 'textStyle': {'fontSize': 18, 'fontWeight': 'bold', 'color': '#1a1a1a'}},
        'tooltip': dict(COMMON_TOOLTIP, trigger='axis'),
        'legend': {'data': y_fields, 'top': '8%'},
        'grid': {'left': '8%', 'right': '8%', 'top': '20%', 'bottom': '15%', 'containLabel': True},
        'xAxis': {'type': 'category', 'data': x_data, 'axisLabel': {'rotate': 30, 'fontSize': 10}},
        'yAxis': {'type': 'value', 'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}}},
        'series': series
    }
    
    option.update(COMMON_ANIMATION)
    
    return DashECharts(option=option, style={'height': height, 'width': '100%'})


# ==================== 饼图工厂 ====================

def create_pie_chart(
    data,
    name_field,
    value_field,
    title='饼图',
    ring=True,
    height='400px'
):
    """
    创建饼图/环形图
    
    Args:
        data: pandas DataFrame 或 dict
        name_field: 名称字段
        value_field: 数值字段
        title: 图表标题
        ring: 是否为环形图
        height: 图表高度
    """
    if not ECHARTS_AVAILABLE:
        return None
    
    # 数据处理
    if hasattr(data, 'to_dict'):
        pie_data = [{'name': n, 'value': format_number(v)} for n, v in zip(data[name_field], data[value_field])]
    else:
        pie_data = [{'name': data[name_field][i], 'value': format_number(data[value_field][i])} for i in range(len(data[name_field]))]
    
    option = {
        'title': {'text': title, 'left': 'center', 'top': '3%',
                 'textStyle': {'fontSize': 18, 'fontWeight': 'bold', 'color': '#1a1a1a'}},
        'tooltip': {'trigger': 'item', 'formatter': '{b}: {c} ({d}%)'},
        'legend': {'orient': 'vertical', 'left': '5%', 'top': '15%', 'textStyle': {'fontSize': 11}},
        'series': [{
            'name': value_field,
            'type': 'pie',
            'radius': ['40%', '70%'] if ring else '70%',
            'center': ['60%', '55%'],
            'data': pie_data,
            'itemStyle': {
                'borderRadius': 10,
                'borderColor': '#fff',
                'borderWidth': 2
            },
            'label': {'show': True, 'formatter': '{b}\n{d}%', 'fontSize': 11, 'fontWeight': 'bold'},
            'emphasis': {
                'itemStyle': {'shadowBlur': 20, 'shadowColor': 'rgba(0, 0, 0, 0.5)'},
                'label': {'show': True, 'fontSize': 14, 'fontWeight': 'bold'}
            },
            'animationType': 'scale',
            'animationEasing': 'elasticOut',
            'animationDelay': '{dataIndex} * 50'
        }]
    }
    
    return DashECharts(option=option, style={'height': height, 'width': '100%'})


# ==================== 箱线图工厂 ====================

def create_box_chart(
    data,
    categories,
    values,
    title='箱线图',
    height='400px'
):
    """
    创建箱线图
    
    Args:
        data: pandas DataFrame
        categories: 分类字段
        values: 数值字段
        title: 图表标题
        height: 图表高度
    """
    if not ECHARTS_AVAILABLE:
        return None
    
    # 准备箱线图数据
    box_data = []
    cat_names = data[categories].unique()
    
    for cat in cat_names:
        cat_values = data[data[categories] == cat][values].tolist()
        if cat_values:
            box_data.append([
                min(cat_values),
                sorted(cat_values)[len(cat_values)//4],
                sorted(cat_values)[len(cat_values)//2],
                sorted(cat_values)[len(cat_values)*3//4],
                max(cat_values)
            ])
    
    option = {
        'title': {'text': title, 'left': 'center', 'top': '3%',
                 'textStyle': {'fontSize': 18, 'fontWeight': 'bold', 'color': '#1a1a1a'}},
        'tooltip': {'trigger': 'item'},
        'grid': {'left': '8%', 'right': '8%', 'top': '15%', 'bottom': '15%', 'containLabel': True},
        'xAxis': {'type': 'category', 'data': cat_names.tolist(), 'axisLabel': {'fontSize': 10}},
        'yAxis': {'type': 'value', 'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}}},
        'series': [{
            'name': 'boxplot',
            'type': 'boxplot',
            'data': box_data,
            'itemStyle': {
                'color': COMMON_COLORS['blue'][0],
                'borderColor': COMMON_COLORS['blue'][2]
            }
        }]
    }
    
    option.update(COMMON_ANIMATION)
    
    return DashECharts(option=option, style={'height': height, 'width': '100%'})


# ==================== 散点图工厂 ====================

def create_scatter_chart(
    data,
    x_field,
    y_field,
    title='散点图',
    color_scheme='blue',
    height='400px'
):
    """
    创建散点图
    
    Args:
        data: pandas DataFrame
        x_field: X轴字段
        y_field: Y轴字段
        title: 图表标题
        color_scheme: 配色方案
        height: 图表高度
    """
    if not ECHARTS_AVAILABLE:
        return None
    
    scatter_data = [[x, y] for x, y in zip(data[x_field], data[y_field])]
    
    option = {
        'title': {'text': title, 'left': 'center', 'top': '3%',
                 'textStyle': {'fontSize': 18, 'fontWeight': 'bold', 'color': '#1a1a1a'}},
        'tooltip': {'trigger': 'item', 'formatter': '{c}'},
        'grid': {'left': '8%', 'right': '8%', 'top': '15%', 'bottom': '15%', 'containLabel': True},
        'xAxis': {'type': 'value', 'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}}},
        'yAxis': {'type': 'value', 'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}}},
        'series': [{
            'type': 'scatter',
            'data': scatter_data,
            'symbolSize': 10,
            'itemStyle': {'color': COMMON_COLORS[color_scheme][0], 'opacity': 0.7}
        }]
    }
    
    option.update(COMMON_ANIMATION)
    
    return DashECharts(option=option, style={'height': height, 'width': '100%'})
