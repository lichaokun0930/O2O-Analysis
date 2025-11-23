import dash_bootstrap_components as dbc
from dash import html
import pandas as pd

def create_super_table_demo(channel_stats, channel_icons):
    """
    超级表格 (Super Table) Demo 代码备份
    
    此代码展示了如何使用 dbc.Table 和 dbc.Progress 创建一个信息密度高、
    包含堆叠条形图的渠道表现对比表格。
    """
    
    # 定义列定义 (如果使用 AG Grid)
    # column_defs = [ ... ] (省略，因为实际使用的是 HTML Table)
    
    # 由于没有注入自定义JS组件，我们先用简单的HTML表格模拟"超级表格"的效果
    # 这样不需要依赖复杂的AG Grid JS注入
    
    table_header = html.Thead(html.Tr([
        html.Th("渠道", style={'width': '15%'}),
        html.Th("核心指标", style={'width': '25%'}),
        html.Th("利润率", style={'width': '10%'}),
        html.Th("成本结构 (堆叠条)", style={'width': '50%'})
    ]))
    
    table_rows = []
    for _, row in channel_stats.iterrows():
        channel_name = row['渠道']
        icon = channel_icons.get(channel_name, '📱')
        
        # 利润率背景色
        profit_bg = "#d1e7dd" if row['利润率'] >= 15 else "#fff3cd" if row['利润率'] >= 5 else "#f8d7da"
        profit_color = "#0f5132" if row['利润率'] >= 15 else "#664d03" if row['利润率'] >= 5 else "#842029"
        
        # 成本条
        # 注意：dbc.Progress 在 dash-bootstrap-components >= 2.0 中移除了 multi 参数
        # 直接将多个 dbc.Progress(bar=True) 放入父容器即可
        cost_bar = dbc.Progress([
            dbc.Progress(value=row['商品成本率'], color="primary", bar=True, label=f"{row['商品成本率']:.0f}%", className="small-text"),
            dbc.Progress(value=row['耗材成本率'], color="dark", bar=True),
            dbc.Progress(value=row['商品减免率'], color="warning", bar=True),
            dbc.Progress(value=row['活动补贴率'], color="danger", bar=True),
            dbc.Progress(value=row['配送成本率'], color="info", bar=True, label=f"{row['配送成本率']:.0f}%", className="small-text"),
            dbc.Progress(value=row['佣金率'], color="success", bar=True)
        ], style={'height': '24px', 'fontSize': '10px'})
        
        # 核心指标微型布局
        metrics_mini = html.Div([
            html.Div([html.Span("订单: ", className="text-muted small"), html.Span(f"{int(row['订单数'])}")]),
            html.Div([html.Span("销售: ", className="text-muted small"), html.Span(f"¥{row['销售额']:,.0f}", className="fw-bold")]),
            html.Div([html.Span("利润: ", className="text-muted small"), html.Span(f"¥{row['总利润']:,.0f}", className="text-success fw-bold")])
        ], className="d-flex justify-content-between align-items-center")

        tr = html.Tr([
            html.Td([html.H5([icon, " ", channel_name], className="mb-0 fs-6")]),
            html.Td(metrics_mini),
            html.Td(
                html.Div(f"{row['利润率']:.1f}%", 
                        style={'backgroundColor': profit_bg, 'color': profit_color, 'padding': '4px 8px', 'borderRadius': '4px', 'textAlign': 'center', 'fontWeight': 'bold'})
            ),
            html.Td([
                cost_bar,
                html.Div([
                    html.Span("🟦商品 ⬛耗材 🟨减免 🟥补贴 🟦配送 🟩佣金", className="text-muted", style={'fontSize': '10px'})
                ], className="mt-1 text-end")
            ])
        ])
        table_rows.append(tr)
    
    return dbc.Card([
        dbc.CardHeader([
            html.H5([html.I(className="bi bi-table me-2"), "渠道表现超级表格"], className="mb-0")
        ]),
        dbc.Table(
            [table_header, html.Tbody(table_rows)],
            bordered=True,
            hover=True,
            responsive=True,
            className="align-middle mb-0"
        )
    ], className="shadow-sm mb-4")
