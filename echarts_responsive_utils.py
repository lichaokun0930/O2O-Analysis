#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECharts 响应式工具函数
提供动态高度计算、设备检测等功能
"""

def calculate_chart_height(data_count, chart_type='bar', min_height=300, max_height=800, item_height=40):
    """
    根据数据量动态计算图表高度
    
    参数:
        data_count (int): 数据项数量
        chart_type (str): 图表类型 ('bar', 'pie', 'line', 'scatter')
        min_height (int): 最小高度（px）
        max_height (int): 最大高度（px）
        item_height (int): 每个数据项的高度（px）
    
    返回:
        int: 计算后的高度（px）
    
    示例:
        >>> calculate_chart_height(5, 'bar')
        400
        >>> calculate_chart_height(20, 'bar', item_height=30)
        800  # 达到最大值
    """
    # 不同图表类型的基础高度
    base_heights = {
        'bar': 250,      # 柱状图：基础250px
        'pie': 350,      # 饼图：基础350px（需要图例空间）
        'line': 300,     # 折线图：基础300px
        'scatter': 350,  # 散点图：基础350px
        'heatmap': 400,  # 热力图：基础400px
        'box': 350,      # 箱线图：基础350px
    }
    
    base_height = base_heights.get(chart_type, 300)
    
    # 计算动态高度
    if chart_type == 'bar':
        # 柱状图：横向排列，数据越多需要越高
        calculated_height = base_height + (data_count * item_height)
    elif chart_type == 'pie':
        # 饼图：主要看图例数量
        legend_height = (data_count // 5) * 25  # 每行5个图例
        calculated_height = base_height + legend_height
    else:
        # 其他图表类型：适当增加
        calculated_height = base_height + (data_count * 10)
    
    # 限制在最小和最大值之间
    return max(min_height, min(max_height, calculated_height))


def calculate_dynamic_grid(data_count, chart_type='bar', container_height=None):
    """
    根据数据量动态计算图表内边距（grid配置）
    
    参数:
        data_count (int): 数据项数量
        chart_type (str): 图表类型
        container_height (int, optional): 容器高度，用于计算百分比
    
    返回:
        dict: ECharts grid配置
    
    示例:
        >>> calculate_dynamic_grid(10, 'bar')
        {'left': '5%', 'right': '5%', 'top': '80px', 'bottom': '10%', 'containLabel': True}
    """
    # 基础配置
    grid = {
        'containLabel': True
    }
    
    if chart_type == 'bar':
        # 柱状图：数据多时增加底部空间（显示X轴标签）
        if data_count > 15:
            grid.update({
                'left': '3%',
                'right': '4%',
                'top': '80px',
                'bottom': '25%'  # 更多空间给X轴标签
            })
        elif data_count > 10:
            grid.update({
                'left': '4%',
                'right': '5%',
                'top': '80px',
                'bottom': '20%'
            })
        else:
            grid.update({
                'left': '5%',
                'right': '5%',
                'top': '80px',
                'bottom': '10%'
            })
    
    elif chart_type == 'pie':
        # 饼图：中心定位
        grid.update({
            'left': '5%',
            'right': '5%',
            'top': '60px',
            'bottom': '5%'
        })
    
    else:
        # 默认配置
        grid.update({
            'left': '5%',
            'right': '5%',
            'top': '80px',
            'bottom': '12%'
        })
    
    return grid


def get_responsive_font_size(data_count, base_size=12, min_size=10, max_size=14):
    """
    根据数据量动态调整字体大小
    
    参数:
        data_count (int): 数据项数量
        base_size (int): 基础字体大小
        min_size (int): 最小字体大小
        max_size (int): 最大字体大小
    
    返回:
        int: 字体大小（px）
    
    示例:
        >>> get_responsive_font_size(5)
        12
        >>> get_responsive_font_size(20)
        10
    """
    # 数据越多，字体越小（避免拥挤）
    if data_count > 20:
        return min_size
    elif data_count > 10:
        return min_size + 1
    else:
        return min(max_size, base_size)


def create_responsive_echarts_config(data_count, chart_type='bar', 
                                     include_height=True,
                                     include_grid=True,
                                     include_font=True):
    """
    创建完整的响应式ECharts配置
    
    参数:
        data_count (int): 数据项数量
        chart_type (str): 图表类型
        include_height (bool): 是否包含高度计算
        include_grid (bool): 是否包含grid配置
        include_font (bool): 是否包含字体配置
    
    返回:
        dict: 包含height, grid, fontSize等配置的字典
    
    示例:
        >>> config = create_responsive_echarts_config(10, 'bar')
        >>> config['height']
        650
        >>> config['grid']['bottom']
        '10%'
    """
    config = {}
    
    if include_height:
        config['height'] = calculate_chart_height(data_count, chart_type)
    
    if include_grid:
        config['grid'] = calculate_dynamic_grid(data_count, chart_type)
    
    if include_font:
        config['fontSize'] = get_responsive_font_size(data_count)
        config['labelFontSize'] = config['fontSize'] - 1  # 标签字体略小
        config['titleFontSize'] = config['fontSize'] + 4   # 标题字体略大
    
    return config


# ==================== 设备检测相关 ====================

def get_device_breakpoints():
    """
    获取响应式断点配置
    
    返回:
        dict: 断点配置
    """
    return {
        'mobile': 576,    # < 576px
        'tablet': 992,    # 576px - 991px
        'desktop': 992    # >= 992px
    }


def get_device_chart_heights():
    """
    获取不同设备的图表高度配置
    
    返回:
        dict: 设备高度配置
    """
    return {
        'mobile': {
            'default': 300,
            'max': 400
        },
        'tablet': {
            'default': 400,
            'max': 500
        },
        'desktop': {
            'default': 450,
            'max': 800
        }
    }


# ==================== 使用示例 ====================

if __name__ == '__main__':
    # 示例1: 计算柱状图高度（10个商品）
    height = calculate_chart_height(10, 'bar')
    print(f"柱状图高度（10商品）: {height}px")
    
    # 示例2: 计算饼图高度（8个分类）
    height = calculate_chart_height(8, 'pie')
    print(f"饼图高度（8分类）: {height}px")
    
    # 示例3: 获取完整配置
    config = create_responsive_echarts_config(15, 'bar')
    print(f"完整配置: {config}")
    
    # 示例4: 动态grid配置
    grid = calculate_dynamic_grid(20, 'bar')
    print(f"Grid配置（20商品）: {grid}")
