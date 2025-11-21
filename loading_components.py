"""
加载进度组件库
功能: 提供统一的Loading和骨架屏组件,改善用户体验
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_loading_progress(progress=0, message="正在加载数据..."):
    """
    创建带进度条的Loading组件
    
    Args:
        progress: 进度百分比 (0-100)
        message: 显示消息
    """
    return html.Div([
        html.Div([
            # 进度条
            html.Div(
                html.Div(
                    className="loading-progress-fill",
                    style={'width': f'{progress}%'}
                ),
                className="loading-progress-bar"
            ),
            # 提示文本
            html.Div([
                html.I(className="bi bi-arrow-repeat loading-progress-icon"),
                html.Span(message)
            ], className="loading-progress-text")
        ], className="loading-progress-container")
    ])


def create_skeleton_card(title=True, metrics=3, chart=False, height='auto'):
    """
    创建骨架屏卡片
    
    Args:
        title: 是否显示标题骨架
        metrics: 显示几个指标骨架 (0-5)
        chart: 是否显示图表骨架
        height: 卡片高度 (默认auto,可设置如'80px')
    """
    children = []
    
    # 标题骨架
    if title:
        children.append(
            html.Div(className="skeleton-box skeleton-title")
        )
    
    # 指标骨架
    for i in range(metrics):
        children.append(
            html.Div(className="skeleton-box skeleton-metric")
        )
    
    # 图表骨架
    if chart:
        children.append(
            html.Div(className="skeleton-box skeleton-chart")
        )
    
    # 全局信息卡片特殊处理: 显示单个矩形骨架屏
    if not title and metrics == 0 and not chart:
        return html.Div([
            html.Div(className="skeleton-box", style={
                'width': '100%',
                'height': height if height != 'auto' else '80px',
                'borderRadius': '8px'
            })
        ], className="skeleton-card mb-3")
    
    return html.Div(children, className="skeleton-card", style={'height': height} if height != 'auto' else {})


def create_enhanced_loading(component_id, loading_type="circle", children=None):
    """
    创建增强的Loading组件
    
    Args:
        component_id: 组件ID
        loading_type: 加载动画类型 ("circle", "default", "dot", "cube", "graph")
        children: 子组件
    """
    return dcc.Loading(
        id=f"loading-{component_id}",
        type=loading_type,
        color="#667eea",
        children=children if children else html.Div(id=component_id),
        className="loading-wrapper",
        style={'minHeight': '200px'}
    )


def create_tab_skeleton():
    """创建Tab页面的骨架屏"""
    return dbc.Container([
        dbc.Row([
            # 左侧指标卡片
            dbc.Col([
                create_skeleton_card(title=True, metrics=2, chart=False)
            ], md=3),
            dbc.Col([
                create_skeleton_card(title=True, metrics=2, chart=False)
            ], md=3),
            dbc.Col([
                create_skeleton_card(title=True, metrics=2, chart=False)
            ], md=3),
            dbc.Col([
                create_skeleton_card(title=True, metrics=2, chart=False)
            ], md=3),
        ], className="mb-4"),
        
        # 图表区域
        dbc.Row([
            dbc.Col([
                create_skeleton_card(title=True, metrics=0, chart=True)
            ], md=6),
            dbc.Col([
                create_skeleton_card(title=True, metrics=0, chart=True)
            ], md=6),
        ])
    ], fluid=True)


def create_data_loading_indicator(stage="init"):
    """
    创建数据加载阶段指示器
    
    Args:
        stage: 加载阶段
            - init: 初始化
            - loading: 加载中
            - processing: 处理中
            - complete: 完成
    """
    stage_config = {
        'init': {
            'icon': 'bi-hourglass-split',
            'text': '准备加载数据...',
            'color': '#17a2b8',
            'progress': 10
        },
        'loading': {
            'icon': 'bi-download',
            'text': '正在从数据库读取数据...',
            'color': '#667eea',
            'progress': 40
        },
        'processing': {
            'icon': 'bi-gear-fill',
            'text': '正在处理和分析数据...',
            'color': '#ffc107',
            'progress': 70
        },
        'complete': {
            'icon': 'bi-check-circle-fill',
            'text': '数据加载完成!',
            'color': '#28a745',
            'progress': 100
        }
    }
    
    config = stage_config.get(stage, stage_config['init'])
    
    return html.Div([
        html.Div([
            html.I(className=f"bi {config['icon']}", style={
                'fontSize': '2rem',
                'color': config['color'],
                'marginBottom': '12px'
            }),
            html.H5(config['text'], className="mb-3"),
            dbc.Progress(
                value=config['progress'],
                color="primary",
                animated=stage != 'complete',
                style={'height': '8px'}
            )
        ], style={
            'textAlign': 'center',
            'padding': '40px 20px',
            'background': 'white',
            'borderRadius': '12px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.08)'
        })
    ])


def create_mini_loading(text="加载中..."):
    """创建小型加载指示器"""
    return html.Div([
        dbc.Spinner(size="sm", color="primary", spinner_style={'marginRight': '8px'}),
        html.Span(text, className="text-muted small")
    ], className="d-flex align-items-center")


def create_lazy_load_container(component_id, placeholder_text="点击加载此内容"):
    """
    创建懒加载容器
    
    Args:
        component_id: 组件ID
        placeholder_text: 占位文本
    """
    return html.Div([
        html.Div([
            html.I(className="bi bi-eye", style={'fontSize': '2rem', 'color': '#dee2e6'}),
            html.P(placeholder_text, className="mt-2 text-muted"),
            dbc.Button("立即加载", id=f"trigger-{component_id}", size="sm", color="primary")
        ], className="empty-state"),
        html.Div(id=component_id, style={'display': 'none'})
    ])


def create_dashboard_skeleton():
    """创建完整的看板骨架屏(覆盖顶部控制面板+内容区)"""
    return dbc.Container([
        # 头部骨架
        html.Div([
            html.Div(className="skeleton-box", style={
                'width': '300px',
                'height': '40px',
                'marginBottom': '20px'
            })
        ]),
        
        # 数据源选择卡片骨架
        html.Div([
            html.Div(className="skeleton-box", style={
                'width': '100%',
                'height': '120px',
                'marginBottom': '20px'
            })
        ]),
        
        # Tab导航骨架
        html.Div([
            html.Div(className="skeleton-box", style={
                'width': '100%',
                'height': '50px',
                'marginBottom': '20px'
            })
        ]),
        
        # Tab内容骨架
        create_tab_skeleton()
    ], fluid=True, style={'padding': '20px'})


def create_page_loading_overlay():
    """创建全页面加载遮罩"""
    return html.Div([
        html.Div([
            dbc.Spinner(color="light", style={'width': '3rem', 'height': '3rem'}),
            html.H4("加载中...", className="mt-3", style={'color': 'white'})
        ], style={
            'position': 'fixed',
            'top': '50%',
            'left': '50%',
            'transform': 'translate(-50%, -50%)',
            'textAlign': 'center',
            'zIndex': 9999
        })
    ], id="page-loading-overlay", style={
        'position': 'fixed',
        'top': 0,
        'left': 0,
        'width': '100%',
        'height': '100%',
        'background': 'rgba(0, 0, 0, 0.7)',
        'zIndex': 9998,
        'display': 'none'  # 默认隐藏
    })


# ==================== 预定义常用Loading配置 ====================

LOADING_CONFIG = {
    'default': {
        'type': 'circle',
        'color': '#667eea'
    },
    'graph': {
        'type': 'graph',
        'color': '#667eea'
    },
    'cube': {
        'type': 'cube',
        'color': '#667eea'
    },
    'dot': {
        'type': 'dot',
        'color': '#667eea'
    }
}


def wrap_with_loading(children, config_type='default', component_id=None):
    """
    快速包装组件为Loading
    
    Args:
        children: 要包装的子组件
        config_type: Loading配置类型
        component_id: 组件ID (可选)
    """
    config = LOADING_CONFIG.get(config_type, LOADING_CONFIG['default'])
    
    return dcc.Loading(
        id=f"loading-{component_id}" if component_id else None,
        type=config['type'],
        color=config['color'],
        children=children
    )
