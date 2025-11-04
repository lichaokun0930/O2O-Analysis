#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试：验证日历选择器切换功能
"""

from dash import Dash, html, dcc, Input, Output, no_update
import dash_bootstrap_components as dbc

# 创建应用
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# 布局
app.layout = dbc.Container([
    html.H1("日历选择器测试", className="mt-4 mb-4"),
    
    dbc.Row([
        dbc.Col([
            html.Label("📊 对比模式"),
            dcc.Dropdown(
                id='time-period-test',
                options=[
                    {'label': '📅 日度对比', 'value': 'day'},
                    {'label': '📆 周度对比', 'value': 'week'}
                ],
                value='week'
            )
        ], md=4),
        
        dbc.Col([
            html.Div(id='period-container-test', children=[
                html.P("初始内容（占位符）")
            ])
        ], md=8)
    ])
], fluid=True)

# 回调
@app.callback(
    Output('period-container-test', 'children'),
    Input('time-period-test', 'value'),
    prevent_initial_call=False
)
def update_selector(time_period):
    print(f"🔄 回调触发！time_period = {time_period}")
    
    if time_period == 'day':
        print("   → 返回日历选择器")
        return html.Div([
            html.H4("📅 日期范围选择"),
            dcc.DatePickerRange(
                id='date-range-test',
                display_format='YYYY-MM-DD',
                start_date_placeholder_text="开始日期",
                end_date_placeholder_text="结束日期"
            )
        ])
    else:
        print("   → 返回下拉框")
        return html.Div([
            html.H4("📆 周期选择"),
            dcc.Dropdown(
                id='dropdown-test',
                options=[
                    {'label': '第1周', 'value': 0},
                    {'label': '第2周', 'value': 1}
                ],
                value=0
            )
        ])

if __name__ == '__main__':
    print("="*60)
    print("🧪 启动测试应用")
    print("📍 访问: http://127.0.0.1:8051")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=8051)
