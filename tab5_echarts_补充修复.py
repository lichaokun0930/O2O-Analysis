"""
Tab 5 ECharts 补充修复函数
========================
此文件包含剩余图表的ECharts版本,需要手动合并到tab5_extended_renders.py

使用方法:
1. 将以下函数复制到tab5_extended_renders.py的辅助函数区域(Line 28附近)
2. 修改原有图表调用为条件渲染
"""

# ==================== 3. 趋势双轴图 ====================

def render_trend_echarts(period_trend_df):
    """时段销量与销售额趋势 - ECharts双Y轴折线图"""
    option = {
        'title': {
            'text': '时段销量与销售额趋势',
            'left': 'center',
            'textStyle': {'fontSize': 16}
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'cross'}
        },
        'legend': {
            'data': ['订单量', '销售额'],
            'top': 35
        },
        'grid': {
            'left': '60px',
            'right': '60px',
            'bottom': '60px',
            'top': '80px'
        },
        'xAxis': {
            'type': 'category',
            'data': period_trend_df['时段'].tolist(),
            'axisLabel': {'rotate': 45}
        },
        'yAxis': [
            {
                'type': 'value',
                'name': '订单量',
                'position': 'left',
                'axisLabel': {'formatter': '{value}'}
            },
            {
                'type': 'value',
                'name': '销售额 (¥)',
                'position': 'right',
                'axisLabel': {'formatter': '¥{value}'}
            }
        ],
        'series': [
            {
                'name': '订单量',
                'type': 'line',
                'yAxisIndex': 0,
                'data': period_trend_df['订单量'].tolist(),
                'smooth': True,
                'lineStyle': {'width': 2, 'color': '#3b82f6'},
                'itemStyle': {'color': '#3b82f6'},
                'areaStyle': {'opacity': 0.1, 'color': '#3b82f6'}
            },
            {
                'name': '销售额',
                'type': 'line',
                'yAxisIndex': 1,
                'data': period_trend_df['销售额'].tolist(),
                'smooth': True,
                'lineStyle': {'width': 2, 'color': '#f59e0b', 'type': 'dashed'},
                'itemStyle': {'color': '#f59e0b'},
                'areaStyle': {'opacity': 0.1, 'color': '#f59e0b'}
            }
        ]
    }
    
    from dash_echarts import DashECharts
    return DashECharts(
        option=option,
        id='trend-chart',
        style={'height': '500px'}
    )


def render_trend_plotly(period_trend_df):
    """趋势图 - Plotly后备版本"""
    import plotly.graph_objs as go
    from dash import dcc
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=period_trend_df['时段'],
        y=period_trend_df['订单量'],
        name='订单量',
        yaxis='y',
        line=dict(color='#3b82f6', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=period_trend_df['时段'],
        y=period_trend_df['销售额'],
        name='销售额',
        yaxis='y2',
        line=dict(color='#f59e0b', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title='时段销量与销售额趋势',
        xaxis=dict(title='时段'),
        yaxis=dict(title='订单量', side='left'),
        yaxis2=dict(title='销售额 (¥)', side='right', overlaying='y'),
        height=500,
        font=dict(family="Microsoft YaHei", size=12)
    )
    return dcc.Graph(figure=fig)


# ==================== 4. 商品场景关联分组柱状图 ====================

def render_product_scene_network_echarts(top_products_scene_data):
    """商品场景关联 - ECharts分组柱状图"""
    
    # 提取场景列表(排除商品名和总销量列)
    scenes = [col for col in top_products_scene_data.columns 
              if col not in ['商品名', '总销量']]
    
    # 按总销量排序取Top10
    top10 = top_products_scene_data.nlargest(10, '总销量')
    
    # 构建系列数据
    series = []
    for scene in scenes:
        series.append({
            'name': scene,
            'type': 'bar',
            'data': top10[scene].tolist(),
            'emphasis': {'focus': 'series'},
            'label': {
                'show': False  # 柱子上不显示数值
            }
        })
    
    option = {
        'title': {
            'text': '商品场景关联分析 (Top10商品)',
            'left': 'center',
            'textStyle': {'fontSize': 16}
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'shadow'},
            'formatter': '{b}<br/>{a}: {c}单'
        },
        'legend': {
            'data': scenes,
            'top': 35,
            'type': 'scroll',  # 场景多时可滚动
            'width': '80%'
        },
        'grid': {
            'left': '60px',
            'right': '40px',
            'bottom': '120px',
            'top': '100px'
        },
        'xAxis': {
            'type': 'category',
            'data': top10['商品名'].tolist(),
            'axisLabel': {
                'rotate': 45,
                'interval': 0,
                'fontSize': 11
            }
        },
        'yAxis': {
            'type': 'value',
            'name': '订单量',
            'axisLabel': {'formatter': '{value}'}
        },
        'series': series,
        'dataZoom': [
            {
                'type': 'slider',
                'show': True,
                'xAxisIndex': 0,
                'bottom': 10,
                'height': 20,
                'startValue': 0,
                'endValue': min(9, len(top10) - 1)
            }
        ]
    }
    
    from dash_echarts import DashECharts
    return DashECharts(
        option=option,
        id='product-scene-network-chart',
        style={'height': '600px'}
    )


def render_product_scene_network_plotly(top_products_scene_data):
    """商品场景关联 - Plotly后备版本"""
    import plotly.graph_objs as go
    from dash import dcc
    
    scenes = [col for col in top_products_scene_data.columns 
              if col not in ['商品名', '总销量']]
    top10 = top_products_scene_data.nlargest(10, '总销量')
    
    fig = go.Figure()
    for scene in scenes:
        fig.add_trace(go.Bar(
            x=top10['商品名'],
            y=top10[scene],
            name=scene
        ))
    
    fig.update_layout(
        title='商品场景关联分析 (Top10商品)',
        barmode='group',
        xaxis=dict(title='商品', tickangle=-45),
        yaxis=dict(title='订单量'),
        height=600,
        font=dict(family="Microsoft YaHei", size=12),
        showlegend=True
    )
    return dcc.Graph(figure=fig)


# ==================== 5. 场景驱动因素雷达图 ====================

def render_driver_radar_echarts(driver_data):
    """场景驱动因素雷达图 - ECharts版本"""
    
    # 假设driver_data是DataFrame: 场景、订单占比、销售占比、利润占比、客单价指数、转化率
    indicators = [
        {'name': '订单占比', 'max': 100},
        {'name': '销售占比', 'max': 100},
        {'name': '利润占比', 'max': 100},
        {'name': '客单价指数', 'max': 150},
        {'name': '转化率', 'max': 100}
    ]
    
    series_data = []
    for idx, row in driver_data.iterrows():
        series_data.append({
            'value': [
                row.get('订单占比', 0),
                row.get('销售占比', 0),
                row.get('利润占比', 0),
                row.get('客单价指数', 0),
                row.get('转化率', 0)
            ],
            'name': row.get('场景', f'场景{idx+1}')
        })
    
    option = {
        'title': {
            'text': '场景驱动因素分析',
            'left': 'center'
        },
        'tooltip': {
            'trigger': 'item'
        },
        'legend': {
            'data': [item['name'] for item in series_data],
            'top': 35
        },
        'radar': {
            'indicator': indicators,
            'radius': '60%'
        },
        'series': [{
            'type': 'radar',
            'data': series_data,
            'areaStyle': {'opacity': 0.2}
        }]
    }
    
    from dash_echarts import DashECharts
    return DashECharts(
        option=option,
        id='driver-radar-chart',
        style={'height': '500px'}
    )


def render_driver_radar_plotly(driver_data):
    """雷达图 - Plotly后备版本"""
    import plotly.graph_objs as go
    from dash import dcc
    
    fig = go.Figure()
    
    for idx, row in driver_data.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=[
                row.get('订单占比', 0),
                row.get('销售占比', 0),
                row.get('利润占比', 0),
                row.get('客单价指数', 0),
                row.get('转化率', 0)
            ],
            theta=['订单占比', '销售占比', '利润占比', '客单价指数', '转化率'],
            fill='toself',
            name=row.get('场景', f'场景{idx+1}')
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title='场景驱动因素分析',
        height=500,
        font=dict(family="Microsoft YaHei", size=12)
    )
    return dcc.Graph(figure=fig)


# ==================== 修改调用示例 ====================

"""
在tab5_extended_renders.py的相应位置,将原有图表调用改为条件渲染:

# 趋势图 (约Line 450)
原代码:
    dcc.Graph(figure=trend_fig)
    
修改为:
    render_trend_echarts(period_trend_df) if ECHARTS_AVAILABLE
    else render_trend_plotly(period_trend_df)


# 商品场景关联图 (约Line 800)
原代码:
    dcc.Graph(figure=network_fig)
    
修改为:
    render_product_scene_network_echarts(top_products_scene_data) if ECHARTS_AVAILABLE
    else render_product_scene_network_plotly(top_products_scene_data)


# 雷达图 (约Line 900)
原代码:
    dcc.Graph(figure=driver_fig)
    
修改为:
    render_driver_radar_echarts(driver_data) if ECHARTS_AVAILABLE
    else render_driver_radar_plotly(driver_data)
"""

# ==================== 客单价图表说明 ====================

"""
客单价箱线图(price_fig)和柱状图(price_bar_fig):

建议保持使用Plotly,因为:
1. 箱线图在ECharts中配置复杂,需要手动计算四分位数
2. Plotly的箱线图交互性很好(显示异常值、中位数等)
3. 这两个图表不是核心展示图表

如果仍需ECharts版本,可使用:
- 箱线图: option = {'series': [{'type': 'boxplot', 'data': [...]}]}
- 柱状图: option = {'series': [{'type': 'bar', 'data': [...]}]}
"""
