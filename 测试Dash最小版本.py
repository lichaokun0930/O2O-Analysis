#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小测试版本 - 测试Dash应用是否能正常运行
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dash import Dash, html
import dash_bootstrap_components as dbc

# 创建应用
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# 简单布局
app.layout = dbc.Container([
    html.H1("测试页面"),
    html.P("如果您看到这个页面，说明Dash应用可以正常运行！")
])

if __name__ == '__main__':
    print("=" * 60)
    print("启动测试应用...")
    print("访问: http://localhost:8050")
    print("=" * 60)
    
    try:
        app.run(
            debug=False,
            host='0.0.0.0',
            port=8050
        )
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
