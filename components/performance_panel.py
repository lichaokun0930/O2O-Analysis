"""
性能监控面板组件 (V8.10.3)

功能：
1. 在看板界面显示性能监控数据
2. 实时更新各模块耗时
3. 可视化性能瓶颈

使用方法：
    from components.performance_panel import create_performance_panel
    
    # 在layout中添加
    layout = html.Div([
        create_performance_panel(),
        # 其他组件...
    ])
"""

from dash import html, dcc
import dash_mantine_components as dmc
from dash.dependencies import Input, Output, State
from typing import Dict, Optional


def create_performance_panel(panel_id: str = 'performance-panel') -> html.Div:
    """
    创建性能监控面板
    
    Args:
        panel_id: 面板ID
    
    Returns:
        Dash组件
    """
    return html.Div([
        # 性能监控开关（紧凑按钮）
        html.Div([
            html.Div([
                dmc.Switch(
                    id=f'{panel_id}-toggle',
                    label='性能',  # 缩短标签文字
                    checked=False,
                    size='sm',
                    color='blue',
                ),
            ], style={
                'width': '80px',  # 强制宽度80px
                'overflow': 'hidden'  # 超出部分隐藏
            }),
        ], style={
            'marginBottom': '10px',
        }),
        
        # 性能数据显示区域（默认隐藏）
        html.Div(
            id=f'{panel_id}-content',
            style={'display': 'none'},
            children=[
                # 总耗时卡片
                dmc.Card([
                    dmc.CardSection([
                        html.H4('⏱️ 总耗时', style={'margin': '0'}),
                    ], withBorder=True, inheritPadding=True, py='xs'),
                    dmc.CardSection([
                        html.Div(id=f'{panel_id}-total-time', children='--秒'),
                    ], inheritPadding=True, py='md'),
                ], withBorder=True, shadow='sm', radius='md', style={'marginBottom': '10px'}),
                
                # 各模块耗时列表
                dmc.Card([
                    dmc.CardSection([
                        html.H4('📊 模块耗时', style={'margin': '0'}),
                    ], withBorder=True, inheritPadding=True, py='xs'),
                    dmc.CardSection([
                        html.Div(id=f'{panel_id}-module-times'),
                    ], inheritPadding=True, py='md'),
                ], withBorder=True, shadow='sm', radius='md'),
            ]
        ),
        
        # 隐藏的数据存储
        dcc.Store(id=f'{panel_id}-data'),
        dcc.Store(id=f'{panel_id}-show-all', data=False),  # 存储展开/折叠状态
    ], style={
        'position': 'fixed',
        'top': '80px',
        'right': '20px',
        'width': '300px',  # 保持原始宽度
        'zIndex': 1000,
        'backgroundColor': 'white',
        'padding': '15px',  # 保持原始内边距
        'borderRadius': '8px',
        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
        'maxHeight': '80vh',
        'overflowY': 'auto'
    })


def format_performance_data(performance_data: Optional[Dict], top_n: int = 5, show_all: bool = False) -> tuple:
    """
    格式化性能数据为显示组件（支持TOP展示）
    
    Args:
        performance_data: 性能数据字典
        top_n: 显示TOP N个最慢的模块（默认5个）
        show_all: 是否显示全部模块（默认False）
    
    Returns:
        (total_time_component, module_times_component)
    """
    if not performance_data or 'measurements' not in performance_data:
        return (
            html.Div('暂无数据', style={'color': '#999'}),
            html.Div('暂无数据', style={'color': '#999'})
        )
    
    # 总耗时
    total_time = performance_data.get('total_time', 0)
    total_time_component = html.Div([
        html.Span(f'{total_time:.2f}', style={
            'fontSize': '32px',
            'fontWeight': 'bold',
            'color': '#1890ff' if total_time < 5 else ('#faad14' if total_time < 10 else '#ff4d4f')
        }),
        html.Span('秒', style={'fontSize': '16px', 'marginLeft': '5px'})
    ])
    
    # 各模块耗时
    measurements = performance_data.get('measurements', {})
    
    # 按耗时排序（降序）
    sorted_items = sorted(
        measurements.items(),
        key=lambda x: x[1].get('current', 0),
        reverse=True
    )
    
    # 决定显示哪些模块
    total_modules = len(sorted_items)
    if show_all or total_modules <= top_n:
        display_items = sorted_items
        show_expand_button = False
    else:
        display_items = sorted_items[:top_n]
        show_expand_button = True
    
    module_items = []
    for idx, (name, stats) in enumerate(display_items):
        current_time = stats.get('current', 0)
        avg_time = stats.get('avg', 0)
        
        # 计算百分比
        percentage = (current_time / total_time * 100) if total_time > 0 else 0
        
        # 颜色编码
        if current_time < 0.5:
            color = '#52c41a'  # 绿色
            emoji = '🟢'
        elif current_time < 2:
            color = '#1890ff'  # 蓝色
            emoji = '🔵'
        elif current_time < 5:
            color = '#faad14'  # 黄色
            emoji = '🟡'
        else:
            color = '#ff4d4f'  # 红色
            emoji = '🔴'
        
        # 添加排名标识（TOP 3）
        rank_badge = ''
        if idx == 0:
            rank_badge = '🥇 '
        elif idx == 1:
            rank_badge = '🥈 '
        elif idx == 2:
            rank_badge = '🥉 '
        
        module_items.append(
            html.Div([
                # 模块名称（带排名）
                html.Div([
                    html.Span(rank_badge, style={'marginRight': '5px'}),
                    html.Span(name, style={
                        'fontSize': '12px',
                        'fontWeight': '600' if idx < 3 else '500',
                    }),
                    html.Span(f' {emoji}', style={'marginLeft': '5px'})
                ], style={'marginBottom': '5px'}),
                
                # 进度条
                html.Div([
                    html.Div(style={
                        'width': f'{min(percentage, 100)}%',
                        'height': '6px',
                        'backgroundColor': color,
                        'borderRadius': '3px',
                        'transition': 'width 0.3s',
                        'boxShadow': '0 1px 3px rgba(0,0,0,0.1)' if idx < 3 else 'none'
                    })
                ], style={
                    'width': '100%',
                    'height': '6px',
                    'backgroundColor': '#f0f0f0',
                    'borderRadius': '3px',
                    'marginBottom': '5px'
                }),
                
                # 时间信息
                html.Div([
                    html.Span(f'{current_time:.2f}秒', style={
                        'fontSize': '11px',
                        'color': color,
                        'fontWeight': 'bold'
                    }),
                    html.Span(f' ({percentage:.1f}%)', style={
                        'fontSize': '10px',
                        'color': '#999',
                        'marginLeft': '5px'
                    }),
                    html.Span(f' 平均: {avg_time:.2f}秒', style={
                        'fontSize': '10px',
                        'color': '#999',
                        'marginLeft': '10px'
                    }),
                ]),
            ], style={
                'marginBottom': '15px',
                'paddingBottom': '15px',
                'borderBottom': '1px solid #f0f0f0',
                'backgroundColor': '#fffbe6' if idx < 3 else 'transparent',
                'padding': '10px' if idx < 3 else '0',
                'borderRadius': '4px' if idx < 3 else '0'
            })
        )
    
    # 添加展开/折叠按钮
    if show_expand_button:
        hidden_count = total_modules - top_n
        module_items.append(
            html.Div([
                html.Button(
                    f'查看全部 {total_modules} 个模块 ({hidden_count} 个已隐藏) ▼',
                    id='performance-expand-btn',
                    n_clicks=0,
                    style={
                        'width': '100%',
                        'padding': '8px',
                        'backgroundColor': '#f0f0f0',
                        'border': '1px solid #d9d9d9',
                        'borderRadius': '4px',
                        'cursor': 'pointer',
                        'fontSize': '11px',
                        'color': '#666',
                        'transition': 'all 0.2s'
                    }
                )
            ], style={'marginTop': '10px'})
        )
    
    module_times_component = html.Div(module_items)
    
    return (total_time_component, module_times_component)


def register_performance_panel_callbacks(app, panel_id: str = 'performance-panel', top_n: int = 5):
    """
    注册性能监控面板的回调函数
    
    Args:
        app: Dash app实例
        panel_id: 面板ID
        top_n: 默认显示TOP N个最慢的模块
    """
    
    # 切换面板显示/隐藏
    @app.callback(
        Output(f'{panel_id}-content', 'style'),
        Input(f'{panel_id}-toggle', 'checked')
    )
    def toggle_panel(checked):
        if checked:
            return {'display': 'block'}
        else:
            return {'display': 'none'}
    
    # 更新性能数据显示（支持TOP展示）
    @app.callback(
        [
            Output(f'{panel_id}-total-time', 'children'),
            Output(f'{panel_id}-module-times', 'children'),
        ],
        [
            Input(f'{panel_id}-data', 'data'),
            Input(f'{panel_id}-show-all', 'data')
        ]
    )
    def update_performance_display(performance_data, show_all):
        return format_performance_data(performance_data, top_n=top_n, show_all=show_all)
    
    # 展开/折叠按钮回调
    @app.callback(
        Output(f'{panel_id}-show-all', 'data'),
        Input('performance-expand-btn', 'n_clicks'),
        State(f'{panel_id}-show-all', 'data'),
        prevent_initial_call=True
    )
    def toggle_expand(n_clicks, current_show_all):
        if n_clicks:
            return not current_show_all
        return current_show_all


# 简化版：创建性能监控Badge（用于Tab标题）
def create_performance_badge(time_seconds: float) -> dmc.Badge:
    """
    创建性能监控徽章
    
    Args:
        time_seconds: 耗时（秒）
    
    Returns:
        Badge组件
    """
    if time_seconds < 2:
        color = 'green'
        icon = '⚡'
    elif time_seconds < 5:
        color = 'blue'
        icon = '⏱️'
    elif time_seconds < 10:
        color = 'yellow'
        icon = '⚠️'
    else:
        color = 'red'
        icon = '🐌'
    
    return dmc.Badge(
        f'{icon} {time_seconds:.1f}s',
        color=color,
        variant='filled',
        size='sm'
    )


# 测试代码
if __name__ == '__main__':
    # 测试性能数据格式化
    test_data = {
        'total_time': 5.234,
        'measurements': {
            '1.订单聚合': {'current': 2.1, 'avg': 2.0, 'min': 1.9, 'max': 2.3, 'count': 5},
            '2.紧急问题分析': {'current': 1.5, 'avg': 1.4, 'min': 1.3, 'max': 1.6, 'count': 5},
            '3.正向激励分析': {'current': 0.8, 'avg': 0.7, 'min': 0.6, 'max': 0.9, 'count': 5},
            '4.关注问题分析': {'current': 0.834, 'avg': 0.8, 'min': 0.7, 'max': 0.9, 'count': 5},
        },
        'timestamp': '2025-12-11T10:30:00'
    }
    
    total, modules = format_performance_data(test_data)
    print("Total time component:", total)
    print("Modules component:", modules)
