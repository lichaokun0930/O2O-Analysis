"""
加载和错误组件模块 - V8.8前端体验优化

提供增强的加载状态和错误处理组件
更友好的用户体验

作者: GitHub Copilot
版本: V8.8
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import Optional


def create_enhanced_loading_spinner(
    message: str = "正在加载数据...",
    submessage: Optional[str] = None,
    show_progress: bool = True
) -> dbc.Card:
    """
    创建增强的加载动画
    
    参数：
        message: 主要提示信息
        submessage: 次要提示信息
        show_progress: 是否显示进度条
    
    返回：
        加载动画组件
    """
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                # 旋转加载器
                dbc.Spinner(
                    color="primary",
                    size="lg",
                    spinner_style={
                        "width": "3rem",
                        "height": "3rem"
                    }
                ),
                
                # 主要提示
                html.H5(
                    message,
                    className="mt-3 mb-2 text-primary fw-bold"
                ),
                
                # 次要提示
                html.P(
                    submessage or "请稍候，这可能需要几秒钟",
                    className="text-muted small mb-3"
                ),
                
                # 进度条
                dbc.Progress(
                    value=100,
                    animated=True,
                    striped=True,
                    color="primary",
                    className="mt-3",
                    style={"height": "8px"}
                ) if show_progress else None,
                
                # 提示文字
                html.Small([
                    html.I(className="bi bi-info-circle me-1"),
                    "首次加载可能需要更长时间"
                ], className="text-muted mt-2 d-block")
                
            ], className="text-center py-5")
        ])
    ], className="shadow-sm border-0 animate__animated animate__fadeIn")


def create_skeleton_card(
    title: str = "加载中...",
    num_lines: int = 3
) -> dbc.Card:
    """
    创建骨架屏卡片
    
    参数：
        title: 卡片标题
        num_lines: 骨架行数
    
    返回：
        骨架屏组件
    """
    skeleton_lines = []
    for i in range(num_lines):
        width = "100%" if i < num_lines - 1 else "60%"
        skeleton_lines.append(
            html.Div(
                className="skeleton-line mb-2",
                style={
                    "height": "20px",
                    "width": width,
                    "backgroundColor": "#e0e0e0",
                    "borderRadius": "4px",
                    "animation": "skeleton-loading 1.5s infinite"
                }
            )
        )
    
    return dbc.Card([
        dbc.CardHeader([
            html.H6(title, className="mb-0 text-muted")
        ]),
        dbc.CardBody(skeleton_lines)
    ], className="mb-3 animate__animated animate__fadeIn")


def create_error_alert(
    error_msg: str,
    error_type: str = "加载失败",
    show_retry: bool = True,
    retry_button_id: Optional[str] = None,
    show_details: bool = False
) -> dbc.Alert:
    """
    创建友好的错误提示
    
    参数：
        error_msg: 错误信息
        error_type: 错误类型标题
        show_retry: 是否显示重试按钮
        retry_button_id: 重试按钮ID
        show_details: 是否显示详细错误信息
    
    返回：
        错误提示组件
    """
    return dbc.Alert([
        html.Div([
            # 错误图标
            html.Div([
                html.I(
                    className="bi bi-exclamation-triangle-fill",
                    style={"fontSize": "32px", "color": "#dc3545"}
                )
            ], className="mb-3"),
            
            # 错误标题
            html.H5(error_type, className="alert-heading mb-3"),
            
            # 错误信息
            html.P(
                error_msg,
                className="mb-3",
                style={"fontSize": "14px"}
            ),
            
            # 详细信息（可折叠）
            dbc.Collapse([
                html.Hr(),
                html.Pre(
                    error_msg,
                    className="bg-light p-3 rounded",
                    style={
                        "fontSize": "12px",
                        "maxHeight": "200px",
                        "overflow": "auto"
                    }
                )
            ], id=f"{retry_button_id}-details-collapse" if retry_button_id else "error-details-collapse",
               is_open=False) if show_details else None,
            
            # 操作按钮
            html.Div([
                dbc.Button([
                    html.I(className="bi bi-arrow-clockwise me-2"),
                    "重试"
                ], id=retry_button_id or "retry-load-btn",
                   color="danger",
                   size="sm",
                   className="me-2") if show_retry else None,
                
                dbc.Button([
                    html.I(className="bi bi-info-circle me-2"),
                    "查看详情"
                ], id=f"{retry_button_id}-details-btn" if retry_button_id else "error-details-btn",
                   color="light",
                   size="sm",
                   outline=True) if show_details else None
            ], className="mt-3")
        ], className="text-center")
    ], color="danger", className="animate__animated animate__shakeX")


def create_timeout_alert(
    timeout_seconds: int = 30,
    retry_button_id: Optional[str] = None
) -> dbc.Alert:
    """
    创建超时提示
    
    参数：
        timeout_seconds: 超时秒数
        retry_button_id: 重试按钮ID
    
    返回：
        超时提示组件
    """
    return dbc.Alert([
        html.Div([
            html.I(className="bi bi-clock-history me-2", style={"fontSize": "24px"}),
            html.Div([
                html.H5("请求超时", className="alert-heading mb-2"),
                html.P(
                    f"操作超过 {timeout_seconds} 秒未完成，可能是数据量过大或网络问题",
                    className="mb-3"
                ),
                html.Div([
                    html.Strong("建议："),
                    html.Ul([
                        html.Li("缩小数据范围（选择更短的时间段）"),
                        html.Li("减少筛选条件"),
                        html.Li("检查网络连接"),
                        html.Li("稍后重试")
                    ], className="mb-3 text-start")
                ]),
                dbc.Button([
                    html.I(className="bi bi-arrow-clockwise me-2"),
                    "重新加载"
                ], id=retry_button_id or "retry-timeout-btn",
                   color="warning",
                   size="sm")
            ])
        ], className="d-flex align-items-start text-start")
    ], color="warning", className="animate__animated animate__fadeIn")


def create_no_data_alert(
    message: str = "暂无数据",
    suggestion: Optional[str] = None
) -> dbc.Alert:
    """
    创建无数据提示
    
    参数：
        message: 提示信息
        suggestion: 建议操作
    
    返回：
        无数据提示组件
    """
    return dbc.Alert([
        html.Div([
            html.I(className="bi bi-inbox me-2", style={"fontSize": "32px"}),
            html.Div([
                html.H5(message, className="mb-2"),
                html.P(
                    suggestion or "请尝试调整筛选条件或导入数据",
                    className="text-muted mb-0"
                )
            ])
        ], className="d-flex align-items-center justify-content-center")
    ], color="info", className="text-center animate__animated animate__fadeIn")


def create_success_toast(
    message: str,
    duration: int = 3000
) -> dbc.Toast:
    """
    创建成功提示Toast
    
    参数：
        message: 提示信息
        duration: 显示时长（毫秒）
    
    返回：
        Toast组件
    """
    return dbc.Toast(
        [
            html.Div([
                html.I(className="bi bi-check-circle-fill me-2 text-success"),
                html.Span(message)
            ])
        ],
        header="操作成功",
        icon="success",
        duration=duration,
        is_open=True,
        dismissable=True,
        style={
            "position": "fixed",
            "top": 20,
            "right": 20,
            "zIndex": 9999,
            "minWidth": "300px"
        },
        className="animate__animated animate__fadeInRight"
    )


def create_loading_overlay(
    is_loading: bool = True,
    message: str = "处理中..."
) -> html.Div:
    """
    创建全屏加载遮罩
    
    参数：
        is_loading: 是否显示
        message: 提示信息
    
    返回：
        遮罩组件
    """
    if not is_loading:
        return html.Div(style={"display": "none"})
    
    return html.Div([
        html.Div([
            dbc.Spinner(color="light", size="lg"),
            html.H5(message, className="mt-3 text-white")
        ], className="text-center")
    ], style={
        "position": "fixed",
        "top": 0,
        "left": 0,
        "right": 0,
        "bottom": 0,
        "backgroundColor": "rgba(0, 0, 0, 0.7)",
        "zIndex": 9999,
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "center"
    }, className="animate__animated animate__fadeIn")


# CSS动画样式
LOADING_ANIMATION_CSS = """
@keyframes skeleton-loading {
    0% {
        opacity: 0.6;
    }
    50% {
        opacity: 1;
    }
    100% {
        opacity: 0.6;
    }
}

.animate__animated {
    animation-duration: 0.5s;
}

.animate__fadeIn {
    animation-name: fadeIn;
}

.animate__fadeInRight {
    animation-name: fadeInRight;
}

.animate__shakeX {
    animation-name: shakeX;
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }
    to {
        opacity: 1;
    }
}

@keyframes fadeInRight {
    from {
        opacity: 0;
        transform: translateX(20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes shakeX {
    0%, 100% {
        transform: translateX(0);
    }
    10%, 30%, 50%, 70%, 90% {
        transform: translateX(-5px);
    }
    20%, 40%, 60%, 80% {
        transform: translateX(5px);
    }
}
"""


# 导出
__all__ = [
    'create_enhanced_loading_spinner',
    'create_skeleton_card',
    'create_error_alert',
    'create_timeout_alert',
    'create_no_data_alert',
    'create_success_toast',
    'create_loading_overlay',
    'LOADING_ANIMATION_CSS'
]
