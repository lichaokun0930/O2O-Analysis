import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("按钮回调测试"),
    dbc.Button("点击我", id='test-btn', color="primary", size="lg"),
    html.Div(id='test-output', className="mt-3")
])

@app.callback(
    Output('test-output', 'children'),
    Input('test-btn', 'n_clicks'),
    prevent_initial_call=False
)
def test_callback(n_clicks):
    print(f"🔍 回调被触发! n_clicks={n_clicks}", flush=True)
    if n_clicks is None or n_clicks == 0:
        return "等待点击..."
    return f"按钮被点击了 {n_clicks} 次！"

if __name__ == '__main__':
    print("✅ 测试应用启动: http://localhost:8051", flush=True)
    app.run(debug=False, host='0.0.0.0', port=8051)
