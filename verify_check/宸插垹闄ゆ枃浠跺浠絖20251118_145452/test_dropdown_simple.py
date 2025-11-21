#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单测试：Dash下拉列表
"""

from dash import Dash, dcc, html, callback, Output, Input
import dash_bootstrap_components as dbc

# 测试数据
from database.data_lifecycle_manager import DataLifecycleManager
from sqlalchemy import text

def get_stores():
    manager = DataLifecycleManager()
    results = manager.session.execute(
        text("SELECT DISTINCT store_name FROM orders ORDER BY store_name")
    ).fetchall()
    manager.close()
    return [{'label': r[0], 'value': r[0]} for r in results]

STORE_OPTIONS = get_stores()

print("=" * 60)
print(f"加载了 {len(STORE_OPTIONS)} 个门店:")
for i, opt in enumerate(STORE_OPTIONS, 1):
    print(f"{i}. {opt['label']}")
print("=" * 60)

# 创建测试应用
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1("门店下拉列表测试", className="mt-4 mb-4"),
    
    dbc.Card([
        dbc.CardHeader("测试下拉列表"),
        dbc.CardBody([
            html.Label(f"门店选择（共 {len(STORE_OPTIONS)} 个）:"),
            dcc.Dropdown(
                id='test-dropdown',
                options=STORE_OPTIONS,
                placeholder='选择门店',
                clearable=True
            ),
            html.Hr(),
            html.Div(id='output')
        ])
    ])
], className="mt-5")

@callback(
    Output('output', 'children'),
    Input('test-dropdown', 'value')
)
def display_value(value):
    if value:
        return dbc.Alert(f"你选择了: {value}", color="success")
    return dbc.Alert("请选择门店", color="info")

if __name__ == '__main__':
    print("\n🚀 启动测试应用: http://localhost:8051")
    app.run(debug=True, port=8051)
