# -*- coding: utf-8 -*-
"""
今日必做 - 骨架屏组件 (Skeleton Screens)

用于优化首屏加载体验，在数据加载前显示占位内容

设计原则:
1. 视觉一致性 - 骨架屏布局与真实内容一致
2. 动画效果 - 使用脉冲动画表示加载中
3. 信息提示 - 显示"正在加载..."文字

作者: AI Assistant
版本: V1.0
日期: 2025-12-11
"""

from dash import html, dcc
import dash_bootstrap_components as dbc

# ============ 骨架屏样式 ============

SKELETON_STYLE = {
    'background': 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
    'backgroundSize': '200% 100%',
    'animation': 'skeleton-loading 1.5s ease-in-out infinite',
    'borderRadius': '4px'
}

# CSS动画定义（需要在主应用中注入）
SKELETON_CSS = """
@keyframes skeleton-loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}

.skeleton-pulse {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s ease-in-out infinite;
    border-radius: 4px;
}

.skeleton-text {
    height: 16px;
    margin-bottom: 8px;
}

.skeleton-title {
    height: 24px;
    margin-bottom: 12px;
    width: 60%;
}

.skeleton-card {
    padding: 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
"""


def create_diagnosis_card_skeleton():
    """
    创建诊断卡片骨架屏
    
    模拟3个诊断卡片的布局
    """
    skeleton_card = html.Div([
        # 标题骨架
        html.Div(className="skeleton-pulse skeleton-title"),
        # 主要数值骨架
        html.Div(className="skeleton-pulse", style={'height': '48px', 'width': '80%', 'marginBottom': '12px'}),
        # 副标题骨架
        html.Div(className="skeleton-pulse skeleton-text", style={'width': '70%'}),
        html.Div(className="skeleton-pulse skeleton-text", style={'width': '60%'}),
        # 按钮骨架
        html.Div(className="skeleton-pulse", style={'height': '32px', 'width': '100px', 'marginTop': '12px'}),
    ], className="skeleton-card")
    
    return dbc.Row([
        dbc.Col(skeleton_card, width=4),
        dbc.Col(skeleton_card, width=4),
        dbc.Col(skeleton_card, width=4),
    ], className="mb-4")


def create_product_health_skeleton():
    """
    创建商品健康分析骨架屏
    
    模拟表格布局
    """
    # 表头骨架
    table_header = html.Div([
        html.Div(className="skeleton-pulse", style={'height': '40px', 'marginBottom': '8px'})
    ])
    
    # 表格行骨架（5行）
    table_rows = []
    for i in range(5):
        row = html.Div([
            html.Div(className="skeleton-pulse skeleton-text", style={'width': '90%'})
        ], style={'marginBottom': '8px'})
        table_rows.append(row)
    
    return html.Div([
        html.Div([
            html.Div(className="skeleton-pulse skeleton-title", style={'width': '200px', 'marginBottom': '16px'}),
            table_header,
            html.Div(table_rows)
        ], className="skeleton-card")
    ])


def create_loading_spinner(text="正在加载数据..."):
    """
    创建加载动画组件
    
    Args:
        text: 加载提示文字
    """
    return html.Div([
        dbc.Spinner(
            color="primary",
            size="lg",
            spinner_style={"width": "3rem", "height": "3rem"}
        ),
        html.Div(text, className="mt-3 text-muted", style={'fontSize': '14px'})
    ], style={
        'textAlign': 'center',
        'padding': '40px 0'
    })


def create_today_must_do_skeleton():
    """
    创建今日必做Tab的完整骨架屏
    
    包含:
    - 诊断卡片骨架（3个）
    - 商品健康分析骨架
    - 加载动画
    """
    return html.Div([
        # 页面标题
        html.Div([
            html.H4("📋 今日必做", className="mb-3"),
            html.P("正在加载经营诊断数据，请稍候...", className="text-muted small")
        ]),
        
        # 加载动画
        create_loading_spinner("正在分析昨日经营数据..."),
        
        # 诊断卡片骨架
        html.Div([
            html.H5("🔴 紧急处理", className="mb-3 text-danger"),
            create_diagnosis_card_skeleton()
        ], className="mb-4"),
        
        # 商品健康分析骨架
        html.Div([
            html.H5("📊 商品健康分析", className="mb-3"),
            create_product_health_skeleton()
        ], className="mb-4"),
        
    ], id="today-must-do-skeleton-container")


def create_section_skeleton(title, icon="📊", rows=3):
    """
    创建通用的区块骨架屏
    
    Args:
        title: 区块标题
        icon: 图标
        rows: 骨架行数
    """
    skeleton_rows = []
    for i in range(rows):
        row = html.Div([
            html.Div(className="skeleton-pulse skeleton-text", style={'width': f'{90-i*5}%'})
        ], style={'marginBottom': '12px'})
        skeleton_rows.append(row)
    
    return html.Div([
        html.H5(f"{icon} {title}", className="mb-3"),
        html.Div([
            html.Div(skeleton_rows)
        ], className="skeleton-card")
    ], className="mb-4")


def inject_skeleton_css(app):
    """
    将骨架屏CSS注入到Dash应用
    
    Args:
        app: Dash应用实例
    
    使用方法:
        from components.today_must_do.skeleton_screens import inject_skeleton_css
        inject_skeleton_css(app)
    
    注意：Dash 3.x 不再支持 html.Style()
    建议将 CSS 放入 assets/custom.css 文件中
    """
    # Dash 3.x: 返回空 Div，CSS 应该通过 assets 文件夹注入
    # 或者在 app 初始化时通过 app.index_string 注入
    return html.Div(id='skeleton-css-placeholder', style={'display': 'none'})


# ============ 导出 ============

__all__ = [
    'create_diagnosis_card_skeleton',
    'create_product_health_skeleton',
    'create_loading_spinner',
    'create_today_must_do_skeleton',
    'create_section_skeleton',
    'inject_skeleton_css',
    'SKELETON_CSS'
]
