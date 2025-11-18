"""
阶段8示例: WebWorker后台计算 (Dash实现)

适用场景:
- 大数据量统计分析 (10万+订单聚合)
- 复杂矩阵运算 (商品相似度计算)
- 图表数据预处理 (千万级数据点降采样)
"""

from dash import Dash, html, dcc, Input, Output, ClientsideFunction
import dash_bootstrap_components as dbc

app = Dash(__name__, external_scripts=[
    "https://cdn.jsdelivr.net/npm/lodash@4.17.21/lodash.min.js"
])

app.layout = html.Div([
    html.H3("WebWorker后台计算示例"),
    
    # 触发按钮
    dbc.Button("开始复杂计算 (3秒)", id="compute-btn", color="primary"),
    
    # 进度提示
    dbc.Spinner(html.Div(id="loading-indicator")),
    
    # 结果展示
    html.Div(id="result-output"),
    
    # 存储数据
    dcc.Store(id="worker-result")
])

# ====== 方式1: 使用Clientside Callback ======
app.clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='runWorkerComputation'
    ),
    Output('worker-result', 'data'),
    Input('compute-btn', 'n_clicks'),
    prevent_initial_call=True
)

# ====== 方式2: 普通Callback更新UI ======
@app.callback(
    Output('result-output', 'children'),
    Input('worker-result', 'data')
)
def update_result(data):
    if not data:
        return "等待计算..."
    
    return dbc.Alert([
        html.H5("✅ 计算完成!"),
        html.P(f"处理数据量: {data.get('count', 0):,} 条"),
        html.P(f"计算时长: {data.get('duration', 0):.2f} 秒"),
        html.P(f"UI保持流畅: ✅ 无卡顿")
    ], color="success")


if __name__ == '__main__':
    print("""
    =====================================================
    WebWorker后台计算示例
    =====================================================
    
    演示功能:
    1. 点击按钮触发3秒复杂计算
    2. 计算在Worker线程进行
    3. UI保持响应,可以继续操作
    4. 计算完成后自动更新结果
    
    对比传统方式:
    - ❌ 传统: UI卡死3秒,无法操作
    - ✅ WebWorker: UI流畅,后台计算
    
    打开浏览器访问: http://localhost:8050
    =====================================================
    """)
    
    app.run_server(debug=True)
