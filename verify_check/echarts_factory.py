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

# 导入必要的组件
try:
    import dash_bootstrap_components as dbc
    from dash import html
    DBC_AVAILABLE = True
except ImportError:
    DBC_AVAILABLE = False
    html = None


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


# ==================== 统一主题配置 ====================

# 🎨 标准化颜色系统 - 每个颜色方案提供5级梯度
COMMON_COLORS = {
    'blue': ['#4A90E2', '#357ABD', '#2E5C8A', '#1F4468', '#1A3A5C'],
    'red': ['#FF6B6B', '#F25757', '#E74C3C', '#D63031', '#C0392B'],
    'green': ['#2ECC71', '#28B463', '#27AE60', '#1E8449', '#229954'],
    'orange': ['#FF7F0E', '#F39C12', '#E67E22', '#D35400', '#BA4A00'],
    'purple': ['#9B59B6', '#8E44AD', '#7D3C98', '#6C3483', '#5B2C6F'],
    'yellow': ['#F1C40F', '#F39C12', '#E67E22', '#D68910', '#CA6F1E'],
    'teal': ['#1ABC9C', '#16A085', '#138D75', '#117A65', '#0E6655'],
    'pink': ['#FD79A8', '#E84393', '#D63384', '#C2185B', '#AD1457']
}

# 🎬 标准化动画配置
COMMON_ANIMATION = {
    'animationEasing': 'cubicOut',  # 更平滑的缓动函数
    'animationDuration': 1200,       # 稍长的动画时长
    'animationDelay': 0
}

# 💬 标准化Tooltip样式
COMMON_TOOLTIP = {
    'trigger': 'axis',
    'backgroundColor': 'rgba(255, 255, 255, 0.96)',
    'borderColor': '#e0e0e0',
    'borderWidth': 1,
    'padding': [10, 15],
    'textStyle': {
        'color': '#333',
        'fontSize': 13,
        'fontFamily': 'Microsoft YaHei, Arial, sans-serif'
    },
    'shadowBlur': 10,
    'shadowColor': 'rgba(0, 0, 0, 0.1)',
    'shadowOffsetX': 0,
    'shadowOffsetY': 2
}

# 📊 标准化Legend样式
COMMON_LEGEND = {
    'top': '8%',
    'left': 'center',
    'icon': 'roundRect',
    'itemWidth': 18,
    'itemHeight': 12,
    'itemGap': 15,
    'textStyle': {
        'fontSize': 12,
        'color': '#666',
        'fontFamily': 'Microsoft YaHei, Arial, sans-serif'
    }
}

# 📐 标准化Grid布局
COMMON_GRID = {
    'left': '8%',
    'right': '8%',
    'top': '20%',
    'bottom': '15%',
    'containLabel': True
}

# 🎨 标准化Title样式
COMMON_TITLE = {
    'left': 'center',
    'top': '3%',
    'textStyle': {
        'fontSize': 18,
        'fontWeight': 'bold',
        'color': '#1a1a1a',
        'fontFamily': 'Microsoft YaHei, Arial, sans-serif'
    }
}

# 📏 标准化坐标轴样式
COMMON_AXIS_LABEL = {
    'fontSize': 11,
    'color': '#666',
    'fontFamily': 'Microsoft YaHei, Arial, sans-serif'
}

COMMON_SPLIT_LINE = {
    'lineStyle': {
        'type': 'dashed',
        'color': 'rgba(0, 0, 0, 0.08)',
        'width': 1
    }
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
            'title': dict(COMMON_TITLE, text=title),
            'tooltip': dict(COMMON_TOOLTIP, trigger='axis', axisPointer={'type': 'shadow'}),
            'grid': dict(COMMON_GRID, left='15%', top='15%', bottom='10%'),
            'xAxis': {'type': 'value', 'splitLine': COMMON_SPLIT_LINE, 'axisLabel': COMMON_AXIS_LABEL},
            'yAxis': {'type': 'category', 'data': x_data, 'axisLabel': dict(COMMON_AXIS_LABEL, fontSize=10)},
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
            'title': dict(COMMON_TITLE, text=title),
            'tooltip': dict(COMMON_TOOLTIP, trigger='axis', axisPointer={'type': 'shadow'}),
            'grid': COMMON_GRID,
            'xAxis': {'type': 'category', 'data': x_data, 'axisLabel': dict(COMMON_AXIS_LABEL, rotate=30, fontSize=10)},
            'yAxis': {'type': 'value', 'splitLine': COMMON_SPLIT_LINE, 'axisLabel': COMMON_AXIS_LABEL},
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
        'title': dict(COMMON_TITLE, text=title),
        'tooltip': dict(COMMON_TOOLTIP, trigger='axis'),
        'legend': dict(COMMON_LEGEND, data=y_fields),
        'grid': COMMON_GRID,
        'xAxis': {'type': 'category', 'data': x_data, 'axisLabel': dict(COMMON_AXIS_LABEL, rotate=30, fontSize=10)},
        'yAxis': {'type': 'value', 'splitLine': COMMON_SPLIT_LINE, 'axisLabel': COMMON_AXIS_LABEL},
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
        'title': dict(COMMON_TITLE, text=title),
        'tooltip': {'trigger': 'item', 'formatter': '{b}: {c} ({d}%)', **COMMON_TOOLTIP},
        'legend': dict(COMMON_LEGEND, orient='vertical', left='5%', top='15%'),
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
            'animationEasing': 'cubicOut',
            'animationDelay': '{dataIndex} * 80'
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
        'title': dict(COMMON_TITLE, text=title),
        'tooltip': {'trigger': 'item', **COMMON_TOOLTIP},
        'grid': COMMON_GRID,
        'xAxis': {'type': 'category', 'data': cat_names.tolist(), 'axisLabel': COMMON_AXIS_LABEL},
        'yAxis': {'type': 'value', 'splitLine': COMMON_SPLIT_LINE, 'axisLabel': COMMON_AXIS_LABEL},
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
        'title': dict(COMMON_TITLE, text=title),
        'tooltip': {'trigger': 'item', 'formatter': '{c}', **COMMON_TOOLTIP},
        'grid': COMMON_GRID,
        'xAxis': {'type': 'value', 'splitLine': COMMON_SPLIT_LINE, 'axisLabel': COMMON_AXIS_LABEL},
        'yAxis': {'type': 'value', 'splitLine': COMMON_SPLIT_LINE, 'axisLabel': COMMON_AXIS_LABEL},
        'series': [{
            'type': 'scatter',
            'data': scatter_data,
            'symbolSize': 10,
            'itemStyle': {'color': COMMON_COLORS[color_scheme][0], 'opacity': 0.7}
        }]
    }
    
    option.update(COMMON_ANIMATION)
    
    return DashECharts(option=option, style={'height': height, 'width': '100%'})


# ==================== 卡片式ECharts工厂（方案四专用）====================

def create_metric_bar_card(value, label, profit_rate, color_scheme='blue', height='140px'):
    """
    创建带利润率的指标柱状图卡片（客单价分布专用）
    
    Args:
        value: 订单数量
        label: 价格区间标签
        profit_rate: 利润率
        color_scheme: 配色方案
        height: 卡片高度
    
    Returns:
        完整的Card组件（HTML标题 + ECharts图表）
    """
    if not ECHARTS_AVAILABLE or not DBC_AVAILABLE:
        return None
    
    from dash import html
    
    option = {
        'grid': {'top': 10, 'bottom': 10, 'left': 10, 'right': 10},
        'xAxis': {'type': 'category', 'show': False, 'data': ['']},
        'yAxis': {'type': 'value', 'show': False},
        'series': [{
            'type': 'bar',
            'data': [value],
            'barWidth': '60%',
            'itemStyle': {
                'color': {
                    'type': 'linear',
                    'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                    'colorStops': [
                        {'offset': 0, 'color': COMMON_COLORS[color_scheme][0]},
                        {'offset': 1, 'color': COMMON_COLORS[color_scheme][3]}
                    ]
                },
                'borderRadius': [6, 6, 0, 0]
            },
            'label': {
                'show': True,
                'position': 'top',
                'formatter': f'{int(value)}单',
                'fontSize': 16,
                'fontWeight': 'bold',
                'color': COMMON_COLORS[color_scheme][2]
            }
        }],
        **COMMON_ANIMATION
    }
    
    # 返回Card + HTML标题 + ECharts图表
    profit_color = '#28a745' if profit_rate > 15 else '#fd7e14'
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.H6(label, className="text-muted mb-2 text-center", style={'fontSize': '0.9rem'}),
                html.Div([
                    html.Span(f"利润率 ", className="small text-muted"),
                    html.Span(f"{profit_rate:.1f}%", 
                             className="badge", 
                             style={'backgroundColor': profit_color, 'fontSize': '0.75rem'})
                ], className="text-center mb-2"),
                DashECharts(option=option, style={'height': '80px', 'width': '100%'})
            ])
        ], style={'padding': '0.75rem'})
    ], className="shadow-sm h-100")


def create_gauge_card(value, max_value, title, unit='¥', color_scheme='blue', height='200px'):
    """
    创建仪表盘卡片（用于成本结构等指标）
    
    Args:
        value: 当前值
        max_value: 最大值
        title: 标题
        unit: 单位
        color_scheme: 配色方案
        height: 卡片高度
    
    Returns:
        完整的Card组件
    """
    if not ECHARTS_AVAILABLE or not DBC_AVAILABLE:
        return None
    
    percentage = (value / max_value * 100) if max_value > 0 else 0
    
    option = {
        'series': [{
            'type': 'gauge',
            'startAngle': 180,
            'endAngle': 0,
            'min': 0,
            'max': 100,
            'radius': '90%',
            'center': ['50%', '75%'],
            'progress': {
                'show': True,
                'width': 12,
                'itemStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 1, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': COMMON_COLORS[color_scheme][1]},
                            {'offset': 1, 'color': COMMON_COLORS[color_scheme][3]}
                        ]
                    }
                }
            },
            'axisLine': {
                'lineStyle': {
                    'width': 12,
                    'color': [[1, 'rgba(0,0,0,0.1)']]
                }
            },
            'axisTick': {'show': False},
            'splitLine': {'show': False},
            'axisLabel': {'show': False},
            'anchor': {'show': False},
            'pointer': {'show': False},
            'title': {'show': False},  # 改用HTML标题
            'detail': {
                'valueAnimation': True,
                'formatter': f'{unit}{{value}}',
                'fontSize': 20,
                'fontWeight': 'bold',
                'color': COMMON_COLORS[color_scheme][2],
                'offsetCenter': [0, '5%']
            },
            'data': [{
                'value': round(percentage, 1),
                'name': title,
                'detail': {'formatter': f'{unit}{value:,.2f}\n{percentage:.1f}%'}
            }]
        }],
        **COMMON_ANIMATION
    }
    
    # 返回完整的Card组件（HTML标题+纯图表）
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.H6(title, className="text-muted mb-2 text-center", style={'fontSize': '0.9rem'}),
                DashECharts(option=option, style={'height': '110px', 'width': '100%'})
            ])
        ], style={'padding': '0.75rem'})
    ], className="shadow-sm h-100")
