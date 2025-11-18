"""
📦 统一组件样式库
解决看板中Card、Alert、Badge等组件样式不一致的问题
提供工厂函数快速创建标准化组件
"""

import dash_bootstrap_components as dbc
from dash import html

# ==================== 样式配置常量 ====================

# 卡片标准样式
CARD_STYLES = {
    'default': {
        'className': 'shadow-sm mb-3',
        'style': {
            'borderRadius': '8px',
            'transition': 'transform 0.2s ease, box-shadow 0.3s ease'
        }
    },
    'highlight': {
        'className': 'shadow mb-3',
        'style': {
            'borderRadius': '10px',
            'transition': 'transform 0.2s ease, box-shadow 0.3s ease',
            'border': '2px solid #667eea'
        }
    },
    'simple': {
        'className': 'mb-3',
        'style': {
            'borderRadius': '6px',
            'border': '1px solid #dee2e6'
        }
    },
    'stat': {
        'className': 'text-center shadow-sm',
        'style': {
            'borderRadius': '8px',
            'transition': 'transform 0.2s ease, box-shadow 0.3s ease'
        }
    }
}

# CardHeader标准样式
CARD_HEADER_STYLES = {
    'primary': {
        'className': 'bg-primary text-white',
        'style': {'fontWeight': 'bold', 'borderRadius': '8px 8px 0 0'}
    },
    'info': {
        'className': 'bg-info text-white',
        'style': {'fontWeight': 'bold', 'borderRadius': '8px 8px 0 0'}
    },
    'success': {
        'className': 'bg-success text-white',
        'style': {'fontWeight': 'bold', 'borderRadius': '8px 8px 0 0'}
    },
    'warning': {
        'className': 'bg-warning text-white',
        'style': {'fontWeight': 'bold', 'borderRadius': '8px 8px 0 0'}
    },
    'danger': {
        'className': 'bg-danger text-white',
        'style': {'fontWeight': 'bold', 'borderRadius': '8px 8px 0 0'}
    },
    'light': {
        'className': 'bg-light',
        'style': {'fontWeight': 'bold', 'borderRadius': '8px 8px 0 0'}
    },
    'default': {
        'className': '',
        'style': {'fontWeight': 'bold', 'borderRadius': '8px 8px 0 0', 'backgroundColor': '#f8f9fa'}
    }
}

# Alert标准样式
ALERT_STYLES = {
    'success': {
        'color': 'success',
        'className': 'mb-3',
        'dismissable': True
    },
    'info': {
        'color': 'info',
        'className': 'mb-3',
        'dismissable': True
    },
    'warning': {
        'color': 'warning',
        'className': 'mb-3',
        'dismissable': True
    },
    'danger': {
        'color': 'danger',
        'className': 'mb-3',
        'dismissable': True
    }
}

# Badge样式配置
BADGE_COLORS = {
    'excellent': 'success',    # 优秀
    'good': 'primary',         # 良好
    'normal': 'warning',       # 一般
    'poor': 'danger',          # 待优化
    'info': 'info',           # 信息
    'default': 'secondary'    # 默认
}

# 统计数值颜色配置
STAT_VALUE_COLORS = {
    'primary': '#667eea',
    'success': '#28a745',
    'warning': '#ffc107',
    'danger': '#dc3545',
    'info': '#17a2b8',
    'secondary': '#6c757d'
}


# ==================== 工厂函数：创建标准化组件 ====================

def create_card(
    children,
    header=None,
    header_style='default',
    card_style='default',
    custom_className=None,
    custom_style=None
):
    """
    创建标准化的Card组件
    
    参数:
        children: 卡片主体内容
        header: CardHeader内容（可选）
        header_style: Header样式类型 ('primary', 'info', 'success', 'warning', 'danger', 'light', 'default')
        card_style: Card样式类型 ('default', 'highlight', 'simple', 'stat')
        custom_className: 自定义className（会追加到标准className）
        custom_style: 自定义style（会合并到标准style）
    
    返回:
        dbc.Card组件
    """
    # 获取标准样式
    style_config = CARD_STYLES.get(card_style, CARD_STYLES['default'])
    className = style_config['className']
    style = style_config['style'].copy()
    
    # 合并自定义样式
    if custom_className:
        className = f"{className} {custom_className}"
    if custom_style:
        style.update(custom_style)
    
    # 构建Card
    card_children = []
    
    if header:
        header_config = CARD_HEADER_STYLES.get(header_style, CARD_HEADER_STYLES['default'])
        card_children.append(
            dbc.CardHeader(
                header,
                className=header_config['className'],
                style=header_config['style']
            )
        )
    
    card_children.append(dbc.CardBody(children))
    
    return dbc.Card(card_children, className=className, style=style)


def create_stat_card(
    title,
    value,
    subtitle=None,
    icon=None,
    value_color='primary',
    card_style='stat',
    badge=None
):
    """
    创建标准化的统计卡片
    
    参数:
        title: 统计标题
        value: 统计数值
        subtitle: 副标题（可选）
        icon: 图标emoji或className（可选）
        value_color: 数值颜色 ('primary', 'success', 'warning', 'danger', 'info', 'secondary')
        card_style: Card样式类型
        badge: 徽章内容（可选）
    
    返回:
        dbc.Card组件
    """
    color = STAT_VALUE_COLORS.get(value_color, STAT_VALUE_COLORS['primary'])
    
    content = []
    
    # 图标
    if icon:
        if 'bi-' in str(icon) or 'fa-' in str(icon):
            content.append(html.I(className=f"{icon} mb-2", style={'fontSize': '2rem', 'color': color}))
        else:
            content.append(html.Div(icon, style={'fontSize': '2.5rem', 'marginBottom': '10px'}))
    
    # 标题
    title_content = [html.H6(title, className="card-title text-muted mb-2")]
    if badge:
        title_content.append(badge)
    content.append(html.Div(title_content))
    
    # 数值
    content.append(html.H3(value, className="mb-0", style={'color': color, 'fontWeight': 'bold'}))
    
    # 副标题
    if subtitle:
        content.append(html.P(subtitle, className="text-muted small mt-2 mb-0"))
    
    return create_card(
        children=content,
        card_style=card_style
    )


def create_alert(
    message,
    alert_type='info',
    icon=None,
    dismissable=True,
    custom_className=None
):
    """
    创建标准化的Alert组件
    
    参数:
        message: 提示消息内容
        alert_type: Alert类型 ('success', 'info', 'warning', 'danger')
        icon: 图标（可选）
        dismissable: 是否可关闭
        custom_className: 自定义className
    
    返回:
        dbc.Alert组件
    """
    style_config = ALERT_STYLES.get(alert_type, ALERT_STYLES['info'])
    
    content = []
    if icon:
        if isinstance(icon, str) and ('bi-' in icon or 'fa-' in icon):
            content.append(html.I(className=f"{icon} me-2"))
        else:
            content.append(html.Span(f"{icon} ", style={'marginRight': '8px'}))
    
    content.append(message)
    
    className = style_config['className']
    if custom_className:
        className = f"{className} {custom_className}"
    
    return dbc.Alert(
        content,
        color=style_config['color'],
        dismissable=dismissable if dismissable is not None else style_config['dismissable'],
        className=className
    )


def create_badge(
    text,
    badge_type='default',
    custom_color=None,
    pill=False,
    className=None
):
    """
    创建标准化的Badge组件
    
    参数:
        text: 徽章文本
        badge_type: 徽章类型 ('excellent', 'good', 'normal', 'poor', 'info', 'default')
        custom_color: 自定义颜色（会覆盖badge_type）
        pill: 是否为圆角徽章
        className: 自定义className
    
    返回:
        dbc.Badge组件
    """
    color = custom_color if custom_color else BADGE_COLORS.get(badge_type, BADGE_COLORS['default'])
    
    return dbc.Badge(
        text,
        color=color,
        pill=pill,
        className=className if className else "ms-2"
    )


def create_metric_row(metrics, col_width=3):
    """
    创建一行指标卡片
    
    参数:
        metrics: 指标列表，每个指标为字典 {'label': '标签', 'value': '数值', 'color': '颜色类型'}
        col_width: 每列宽度（默认3，即4列）
    
    返回:
        dbc.Row组件
    """
    cols = []
    
    for metric in metrics:
        label = metric.get('label', '')
        value = metric.get('value', '-')
        color = metric.get('color', 'primary')
        icon = metric.get('icon', None)
        subtitle = metric.get('subtitle', None)
        
        col = dbc.Col([
            create_stat_card(
                title=label,
                value=value,
                subtitle=subtitle,
                icon=icon,
                value_color=color
            )
        ], md=col_width, className="mb-3")
        
        cols.append(col)
    
    return dbc.Row(cols)


def create_info_card(
    title,
    content,
    header_style='light',
    icon=None
):
    """
    创建信息展示卡片
    
    参数:
        title: 卡片标题
        content: 卡片内容
        header_style: Header样式
        icon: 标题图标
    
    返回:
        dbc.Card组件
    """
    header_content = []
    if icon:
        if isinstance(icon, str) and ('bi-' in icon or 'fa-' in icon):
            header_content.append(html.I(className=f"{icon} me-2"))
        else:
            header_content.append(html.Span(f"{icon} ", style={'marginRight': '8px'}))
    
    header_content.append(html.H5(title, className="mb-0 d-inline-block"))
    
    return create_card(
        children=content,
        header=header_content,
        header_style=header_style
    )


def create_comparison_badge(comparison_data):
    """
    创建环比对比徽章
    
    参数:
        comparison_data: 字典 {'change': 变化值, 'direction': 'up'/'down'}
    
    返回:
        html组件或None
    """
    if not comparison_data or 'change' not in comparison_data:
        return None
    
    change = comparison_data.get('change', 0)
    direction = comparison_data.get('direction', 'up' if change > 0 else 'down')
    
    if abs(change) < 0.1:  # 变化太小不显示
        return None
    
    icon = "↑" if direction == 'up' else "↓"
    color = 'success' if direction == 'up' else 'danger'
    
    return dbc.Badge(
        f"{icon} {abs(change):.1f}%",
        color=color,
        className="ms-2 small",
        pill=True
    )


# ==================== 预设组件模板 ====================

def create_data_info_header(
    filename="加载中...",
    date_range="计算中...",
    record_count="统计中...",
    update_time="--"
):
    """
    创建全局数据信息头部卡片
    """
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                # 数据状态
                dbc.Col([
                    html.Div([
                        html.I(className="bi bi-database-check me-2", 
                               style={'fontSize': '1.2rem', 'color': '#28a745'}),
                        html.Span("数据已加载", className="fw-bold", 
                                 style={'color': '#28a745'})
                    ], className="d-flex align-items-center")
                ], width=2),
                
                # 文件名
                dbc.Col([
                    html.Small("📁 数据文件:", className="text-muted me-2"),
                    html.Span(filename, className="fw-bold")
                ], width=3),
                
                # 时间范围
                dbc.Col([
                    html.Small("📅 时间范围:", className="text-muted me-2"),
                    html.Span(date_range, className="fw-bold")
                ], width=3),
                
                # 数据量
                dbc.Col([
                    html.Small("📊 数据量:", className="text-muted me-2"),
                    html.Span(record_count, className="fw-bold")
                ], width=2),
                
                # 更新时间
                dbc.Col([
                    html.Small("🕐 更新时间:", className="text-muted me-2"),
                    html.Span(update_time, className="text-muted small")
                ], width=2)
            ], align="center")
        ])
    ], className="mb-3", style={
        'borderLeft': '4px solid #28a745',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.05)',
        'borderRadius': '8px'
    })


def create_loading_card(message="数据加载中..."):
    """创建加载中提示卡片"""
    return create_alert(
        message=message,
        alert_type='info',
        icon='bi-hourglass-split',
        dismissable=False
    )


def create_error_card(error_message):
    """创建错误提示卡片"""
    return create_alert(
        message=error_message,
        alert_type='danger',
        icon='bi-exclamation-triangle-fill',
        dismissable=True
    )


def create_success_card(success_message):
    """创建成功提示卡片"""
    return create_alert(
        message=success_message,
        alert_type='success',
        icon='bi-check-circle-fill',
        dismissable=True
    )


def create_warning_card(warning_message):
    """创建警告提示卡片"""
    return create_alert(
        message=warning_message,
        alert_type='warning',
        icon='bi-exclamation-circle-fill',
        dismissable=True
    )


# ==================== 使用示例（测试代码） ====================

if __name__ == "__main__":
    print("✅ 统一组件样式库加载成功！")
    print("\n📦 可用的样式类型：")
    print(f"  - Card样式: {list(CARD_STYLES.keys())}")
    print(f"  - Header样式: {list(CARD_HEADER_STYLES.keys())}")
    print(f"  - Alert样式: {list(ALERT_STYLES.keys())}")
    print(f"  - Badge类型: {list(BADGE_COLORS.keys())}")
    print(f"  - 数值颜色: {list(STAT_VALUE_COLORS.keys())}")
    
    print("\n🛠️ 可用的工厂函数：")
    print("  - create_card()")
    print("  - create_stat_card()")
    print("  - create_alert()")
    print("  - create_badge()")
    print("  - create_metric_row()")
    print("  - create_info_card()")
    print("  - create_comparison_badge()")
    print("  - create_data_info_header()")
    print("  - create_loading_card()")
    print("  - create_error_card()")
    print("  - create_success_card()")
    print("  - create_warning_card()")
    
    print("\n💡 使用示例：")
    print("""
    from component_styles import create_card, create_stat_card, create_alert
    
    # 创建统计卡片
    card = create_stat_card(
        title="订单总数",
        value="1,234单",
        subtitle="本月累计",
        icon="📦",
        value_color='primary'
    )
    
    # 创建带Header的Card
    card = create_card(
        children=[html.P("这是卡片内容")],
        header=html.H5("卡片标题"),
        header_style='primary',
        card_style='default'
    )
    
    # 创建Alert
    alert = create_alert(
        message="数据加载成功！",
        alert_type='success',
        icon='bi-check-circle-fill'
    )
    """)
