# 智能门店看板 - 简化高性能版

"""
这是一个简化版本的Dash应用，专注于核心功能和性能优化
主要特点：
1. 减少回调数量
2. 数据采样
3. 按需加载
4. 移除不必要的调试日志
"""

import dash
from dash import Dash, html, dcc, dash_table, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime, timedelta

# 初始化应用
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# 全局数据存储
global_data = {'df': None}

# 简化的布局
app.layout = dbc.Container([
    html.H1("🏪 智能门店看板 - 简化高性能版", className="text-center my-4"),
    
    dbc.Alert([
        html.H5("⚡ 性能优化版本", className="alert-heading"),
        html.P("这是精简版，只包含核心功能："),
        html.Ul([
            html.Li("✅ 减少回调数量（仅3个）"),
            html.Li("✅ 按需分析（点击按钮才计算）"),
            html.Li("✅ 无调试日志"),
            html.Li("✅ 日历选择器正常工作")
        ])
    ], color="info", className="mb-3"),
    
    # 数据上传
    dbc.Card([
        dbc.CardBody([
            html.H5("📁 步骤1: 上传数据"),
            dcc.Upload(
                id='upload-data',
                children=dbc.Button("📂 选择Excel文件", color="secondary"),
                multiple=False
            ),
            html.Div(id='upload-status', className="mt-2")
        ])
    ], className="mb-3"),
    
    # 分析参数
    dbc.Card([
        dbc.CardBody([
            html.H5("⚙️ 步骤2: 设置分析参数"),
            dbc.Row([
                dbc.Col([
                    html.Label("📊 对比模式"),
                    dcc.Dropdown(
                        id='time-mode',
                        options=[
                            {'label': '📅 日度对比', 'value': 'day'},
                            {'label': '📆 周度对比', 'value': 'week'}
                        ],
                        value='day'
                    )
                ], md=3),
                
                dbc.Col([
                    html.Div(id='period-selector-container')
                ], md=9)
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Button("🔍 开始分析", id='analyze-btn', color="primary", className="mt-3", size="lg")
                ])
            ])
        ])
    ], className="mb-3"),
    
    # 分析结果
    dbc.Card([
        dbc.CardBody([
            html.H5("📊 步骤3: 查看结果"),
            html.Div(id='result-container')
        ])
    ])
], fluid=True)

# 回调1: 处理数据上传
@app.callback(
    Output('upload-status', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def upload_file(contents, filename):
    if contents is None:
        return ""
    
    from io import BytesIO
    import base64
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        df = pd.read_excel(BytesIO(decoded))
        
        # 处理日期列
        date_cols = ['下单时间', '日期', '时间']
        for col in date_cols:
            if col in df.columns:
                df['日期'] = pd.to_datetime(df[col])
                break
        
        # 确保销量列
        if '销量' not in df.columns:
            df['销量'] = 1
        
        global_data['df'] = df
        
        return dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"✅ 成功上传: {filename}",
            html.Br(),
            f"📊 数据量: {len(df):,} 行 × {len(df.columns)} 列"
        ], color="success")
        
    except Exception as e:
        return dbc.Alert(f"❌ 上传失败: {str(e)}", color="danger")

# 回调2: 切换选择器
@app.callback(
    Output('period-selector-container', 'children'),
    Input('time-mode', 'value')
)
def update_selector(mode):
    if mode == 'day':
        return dbc.Row([
            dbc.Col([
                html.Label("📅 当前周期"),
                dcc.DatePickerRange(
                    id='current-date-range',
                    display_format='YYYY-MM-DD',
                    start_date_placeholder_text="开始日期",
                    end_date_placeholder_text="结束日期",
                    first_day_of_week=1
                )
            ], md=6),
            dbc.Col([
                html.Label("📅 对比周期"),
                dcc.DatePickerRange(
                    id='compare-date-range',
                    display_format='YYYY-MM-DD',
                    start_date_placeholder_text="开始日期",
                    end_date_placeholder_text="结束日期",
                    first_day_of_week=1
                )
            ], md=6)
        ])
    else:
        return dbc.Alert("周度对比功能开发中...", color="info")

# 回调3: 分析数据
@app.callback(
    Output('result-container', 'children'),
    Input('analyze-btn', 'n_clicks'),
    State('current-date-range', 'start_date'),
    State('current-date-range', 'end_date'),
    State('compare-date-range', 'start_date'),
    State('compare-date-range', 'end_date'),
    prevent_initial_call=True
)
def analyze_data(n, c_start, c_end, b_start, b_end):
    # 检查数据
    if global_data['df'] is None:
        return dbc.Alert("⚠️ 请先上传数据！", color="warning")
    
    if not all([c_start, c_end, b_start, b_end]):
        return dbc.Alert("⚠️ 请选择完整的日期范围！", color="warning")
    
    df = global_data['df']
    
    # 数据筛选
    current_df = df[(df['日期'] >= c_start) & (df['日期'] <= c_end)]
    compare_df = df[(df['日期'] >= b_start) & (df['日期'] <= b_end)]
    
    if len(current_df) == 0 or len(compare_df) == 0:
        return dbc.Alert("⚠️ 所选日期范围内没有数据！", color="warning")
    
    # 简单统计
    current_sales = current_df['销量'].sum()
    compare_sales = compare_df['销量'].sum()
    change = current_sales - compare_sales
    change_pct = (change / compare_sales * 100) if compare_sales > 0 else 0
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{current_sales:,.0f}", className="text-primary"),
                    html.P("当前周期销量", className="text-muted"),
                    html.Small(f"{len(current_df)} 条订单")
                ])
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{compare_sales:,.0f}", className="text-secondary"),
                    html.P("对比周期销量", className="text-muted"),
                    html.Small(f"{len(compare_df)} 条订单")
                ])
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{change:+,.0f}", className="text-success" if change > 0 else "text-danger"),
                    html.P("变化量", className="text-muted")
                ])
            ])
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2(f"{change_pct:+.1f}%", className="text-success" if change_pct > 0 else "text-danger"),
                    html.P("变化幅度", className="text-muted")
                ])
            ])
        ], md=3)
    ])

if __name__ == '__main__':
    print("🚀 启动简化版应用...")
    print("📍 访问: http://localhost:8051")
    app.run(debug=False, host='0.0.0.0', port=8051)
