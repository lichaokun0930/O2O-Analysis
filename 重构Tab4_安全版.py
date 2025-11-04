# -*- coding: utf-8 -*-
"""
Tab 4 重构脚本 - 安全版本
一次性完成：删除旧UI + 插入新UI
"""

file_path = r"d:\Python1\O2O_Analysis\O2O数据分析\测算模型\智能门店看板_Dash版.py"

print("=" * 60)
print("Tab 4 重构脚本 - 开始执行")
print("=" * 60)

# 读取文件
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"\n1. 原始文件: {len(lines)} 行")

# 找到关键位置
tab4_start = None
tab4_old_content_start = None
tab5_start = None

for i, line in enumerate(lines):
    if "# ========== Tab 4: 问题诊断 ==========" in line:
        tab4_start = i
    elif "# 问题诊断的子Tabs" in line and tab4_start is not None:
        tab4_old_content_start = i
    elif "# ========== Tab 5: 时段场景分析 ==========" in line:
        tab5_start = i
        break

print(f"2. 找到关键位置:")
print(f"   Tab 4 开始: 第 {tab4_start + 1} 行")
print(f"   旧内容开始: 第 {tab4_old_content_start + 1} 行")
print(f"   Tab 5 开始: 第 {tab5_start + 1} 行")
print(f"   需要删除: {tab5_start - tab4_old_content_start} 行旧代码")

# 新的 Tab 4 UI代码
new_tab4_ui = '''                        # 页面标题
                        html.Div([
                            html.H3("🚨 经营预警中心", className="mb-2"),
                            html.P("智能识别经营异常，自动生成预警与诊断建议", className="text-muted")
                        ], className="mb-4"),
                        
                        # 第一部分：实时经营健康度
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5("📊 实时经营健康度", className="mb-0 d-inline"),
                                html.Small(" Real-time Business Health", className="text-muted ms-2")
                            ]),
                            dbc.CardBody([
                                dbc.Row([
                                    # KPI 1: 今日销量
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.Div([
                                                    html.I(className="bi bi-graph-up", style={'fontSize': '2rem', 'color': '#667eea'}),
                                                    html.Div([
                                                        html.H4(id='today-sales', children="--", className="mb-0"),
                                                        html.P("今日销量", className="text-muted small mb-0")
                                                    ], className="ms-3")
                                                ], className="d-flex align-items-center")
                                            ])
                                        ], className="border-0 shadow-sm")
                                    ], md=3),
                                    
                                    # KPI 2: 利润率
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.Div([
                                                    html.I(className="bi bi-percent", style={'fontSize': '2rem', 'color': '#f093fb'}),
                                                    html.Div([
                                                        html.H4(id='profit-rate', children="--", className="mb-0"),
                                                        html.P("毛利率", className="text-muted small mb-0")
                                                    ], className="ms-3")
                                                ], className="d-flex align-items-center")
                                            ])
                                        ], className="border-0 shadow-sm")
                                    ], md=3),
                                    
                                    # KPI 3: 库存状态
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.Div([
                                                    html.I(className="bi bi-box-seam", style={'fontSize': '2rem', 'color': '#4facfe'}),
                                                    html.Div([
                                                        html.H4(id='stock-rate', children="--", className="mb-0"),
                                                        html.P("库存健康度", className="text-muted small mb-0")
                                                    ], className="ms-3")
                                                ], className="d-flex align-items-center")
                                            ])
                                        ], className="border-0 shadow-sm")
                                    ], md=3),
                                    
                                    # KPI 4: 盈利订单占比
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.Div([
                                                    html.I(className="bi bi-cash-coin", style={'fontSize': '2rem', 'color': '#43e97b'}),
                                                    html.Div([
                                                        html.H4(id='profitable-rate', children="--", className="mb-0"),
                                                        html.P("盈利订单占比", className="text-muted small mb-0")
                                                    ], className="ms-3")
                                                ], className="d-flex align-items-center")
                                            ])
                                        ], className="border-0 shadow-sm")
                                    ], md=3)
                                ], className="g-3")
                            ])
                        ], className="mb-4"),
                        
                        # 第二部分：智能预警卡片
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5("⚠️ 智能预警", className="mb-0 d-inline"),
                                html.Small(" Smart Alerts", className="text-muted ms-2"),
                                dbc.Badge("自动识别", color="success", className="ms-2")
                            ]),
                            dbc.CardBody([
                                html.Div(id='warning-cards-container', children=[
                                    dbc.Alert([
                                        html.I(className="bi bi-info-circle me-2"),
                                        "系统将自动分析数据并生成预警..."
                                    ], color="info")
                                ])
                            ])
                        ], className="mb-4"),
                        
                        # 第三部分：问题详情分析（折叠面板）
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5("🔍 问题详情分析", className="mb-0 d-inline"),
                                html.Small(" Detailed Analysis", className="text-muted ms-2")
                            ]),
                            dbc.CardBody([
                                dbc.Collapse([
                                    dbc.Tabs([
                                        # 时段分析
                                        dbc.Tab([
                                            html.Div(id='detail-slot-analysis', className="p-3")
                                        ], label="⏰ 时段分析"),
                                        
                                        # 场景分析
                                        dbc.Tab([
                                            html.Div(id='detail-scene-analysis', className="p-3")
                                        ], label="🎭 场景分析"),
                                        
                                        # 商品分析
                                        dbc.Tab([
                                            html.Div(id='detail-product-analysis', className="p-3")
                                        ], label="📦 商品分析"),
                                        
                                        # 趋势分析
                                        dbc.Tab([
                                            html.Div(id='detail-trend-analysis', className="p-3")
                                        ], label="📈 趋势分析")
                                    ])
                                ], id='detail-collapse', is_open=False)
                            ])
                        ], className="mb-4"),
                        
                        # 第四部分：AI 诊断建议
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5("🤖 AI 诊断建议", className="mb-0 d-inline"),
                                html.Small(" Powered by GLM-4.6", className="text-muted ms-2")
                            ]),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Button(
                                            [html.I(className="bi bi-robot me-2"), "生成 AI 诊断报告"],
                                            id='ai-diagnose-btn',
                                            color="primary",
                                            size="lg",
                                            className="w-100"
                                        )
                                    ], md=12)
                                ]),
                                html.Div(id='ai-diagnose-result', className="mt-3")
                            ])
                        ], className="mb-4"),
                        
                        # 第五部分：数据导出
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5("📥 数据导出", className="mb-0")
                            ]),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Button(
                                            [html.I(className="bi bi-file-earmark-excel me-2"), "导出诊断报告 (Excel)"],
                                            id='export-report-btn',
                                            color="success",
                                            outline=True,
                                            className="w-100"
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        dbc.Button(
                                            [html.I(className="bi bi-file-earmark-text me-2"), "导出预警列表 (CSV)"],
                                            id='export-warnings-btn',
                                            color="warning",
                                            outline=True,
                                            className="w-100"
                                        )
                                    ], md=4),
                                    dbc.Col([
                                        dbc.Button(
                                            [html.I(className="bi bi-file-earmark-pdf me-2"), "导出完整报告 (PDF)"],
                                            id='export-pdf-btn',
                                            color="danger",
                                            outline=True,
                                            className="w-100",
                                            disabled=True
                                        )
                                    ], md=4)
                                ])
                            ])
                        ]),
                        
                        # 下载组件
                        dcc.Download(id='download-report'),
                        dcc.Download(id='download-warnings')
'''

# 构建新文件内容
new_lines = []
new_lines.extend(lines[:tab4_old_content_start])  # 保留Tab 4开头到旧内容之前
new_lines.append(new_tab4_ui)  # 插入新UI
new_lines.extend(lines[tab5_start:])  # 保留Tab 5及以后的所有内容

print(f"3. 构建新文件: {len(new_lines)} 行")
print(f"   删除了: {len(lines) - len(new_lines)} 行")

# 写入文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n4. ✓ 重构完成！")
print(f"   原文件: {len(lines)} 行")
print(f"   新文件: {len(new_lines)} 行")
print(f"   净减少: {len(lines) - len(new_lines)} 行")
print("=" * 60)
