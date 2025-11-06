#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小化测试：只测试日历选择器功能
直接访问 http://127.0.0.1:8052 查看效果
"""

from dash import Dash, html, dcc, Input, Output, no_update
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H2("🧪 日历选择器最小测试", className="my-4"),
    
    dbc.Alert("如果看到日期范围选择器（两个日期输入框），说明功能正常！", color="info"),
    
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("📊 对比模式"),
                    dcc.Dropdown(
                        id='mode',
                        options=[
                            {'label': '📅 日度对比', 'value': 'day'},
                            {'label': '📆 周度对比', 'value': 'week'}
                        ],
                        value='day',  # 默认日度
                        clearable=False
                    )
                ], width=4),
                
                dbc.Col([
                    html.Div(id='container', children=[
                        html.P("初始占位符", className="text-muted")
                    ])
                ], width=8)
            ])
        ])
    ], className="mb-4"),
    
    html.Div(id='log', className="mt-4")
], fluid=True)

@app.callback(
    [Output('container', 'children'),
     Output('log', 'children')],
    Input('mode', 'value'),
    prevent_initial_call=False
)
def update(mode):
    import datetime
    log_time = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"[{log_time}] 🔄 回调触发！mode={mode}")
    
    if mode == 'day':
        print(f"[{log_time}]    → 返回日历选择器")
        content = html.Div([
            html.H5("📅 日期范围选择", className="mb-3"),
            dcc.DatePickerRange(
                id='date-range',
                display_format='YYYY-MM-DD',
                start_date_placeholder_text="开始日期",
                end_date_placeholder_text="结束日期",
                className="mb-2"
            ),
            dbc.Alert("✅ 成功！这就是日历选择器", color="success", className="mt-3")
        ])
    else:
        print(f"[{log_time}]    → 返回下拉框")
        content = html.Div([
            html.H5("📆 周期选择", className="mb-3"),
            dcc.Dropdown(
                id='period',
                options=[{'label': f'第{i}周', 'value': i} for i in range(1, 6)],
                value=0
            ),
            dbc.Alert("这是下拉框模式", color="warning", className="mt-3")
        ])
    
    log = dbc.Alert(f"[{log_time}] 回调执行完成 - 模式: {mode}", color="info")
    
    return content, log

if __name__ == '__main__':
    print("="*70)
    print("🧪 最小化测试应用启动")
    print("📍 访问地址: http://127.0.0.1:8052")
    print("="*70)
    print("\n如果看到日历选择器，说明代码逻辑正常！")
    print("如果看不到，说明是 Dash 版本或配置问题。\n")
    app.run(debug=False, host='0.0.0.0', port=8052)
