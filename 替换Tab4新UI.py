"""
替换Tab 4为新的经营预警中心UI
"""

input_file = "智能门店看板_Dash版.py"

# 读取文件
with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"📄 原始文件：{len(lines)} 行")

# 旧Tab 4的范围：line 1577-3023（1447行）
# Python索引：1576-3022
start_line = 1576  # 第1577行
end_line = 3023    # 第3023行

print(f"\n🔍 检查删除范围（第{start_line+1}-{end_line}行）：")
print("开始行：", lines[start_line][:60])
print("结束行：", lines[end_line-1][:60])

# 新Tab 4的UI
new_tab4_ui = '''                # ========== Tab 4: 经营预警中心（智能驱动）==========
                dcc.Tab(label='⚠️ 经营预警', value='tab-4', children=[
                    html.Div([
                        # 数据信息占位符（由全局回调更新）
                        html.Div(id='tab4-data-info', className="mb-3"),
                        
                        # 🆕 实时经营KPI看板
                        dbc.Card([
                            dbc.CardHeader([
                                html.H4("📊 实时经营健康度", className="mb-0 d-inline"),
                                html.Small(" - 自动监控核心指标", className="text-muted ms-2")
                            ]),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.H6("今日销量", className="text-muted mb-2"),
                                                html.H3(id='today-sales', className="text-primary mb-0")
                                            ])
                                        ], className="text-center shadow-sm")
                                    ], md=3),
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.H6("毛利率", className="text-muted mb-2"),
                                                html.H3(id='profit-rate', className="text-success mb-0")
                                            ])
                                        ], className="text-center shadow-sm")
                                    ], md=3),
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.H6("库存健康度", className="text-muted mb-2"),
                                                html.H3(id='stock-rate', className="text-info mb-0")
                                            ])
                                        ], className="text-center shadow-sm")
                                    ], md=3),
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.H6("盈利订单占比", className="text-muted mb-2"),
                                                html.H3(id='profitable-rate', className="text-warning mb-0")
                                            ])
                                        ], className="text-center shadow-sm")
                                    ], md=3)
                                ])
                            ])
                        ], className="mb-3"),
                        
                        # 🆕 智能预警卡片容器
                        html.Div(id='warning-cards-container', className="mb-3"),
                        
                        # 🆕 问题详情与AI诊断
                        dbc.Card([
                            dbc.CardHeader([
                                html.H4("🔍 问题详情与智能诊断", className="mb-0")
                            ]),
                            dbc.CardBody([
                                # 可折叠的详细分析
                                dbc.Collapse([
                                    dbc.Tabs([
                                        dbc.Tab(label="📉 销量预警", tab_id="sales-detail"),
                                        dbc.Tab(label="💰 利润预警", tab_id="profit-detail"),
                                        dbc.Tab(label="📦 库存预警", tab_id="stock-detail"),
                                        dbc.Tab(label="🎯 负毛利预警", tab_id="negative-detail")
                                    ], id='detail-tabs', active_tab='sales-detail'),
                                    html.Div(id='detail-content', className="mt-3")
                                ], id='detail-collapse', is_open=False),
                                
                                # AI诊断按钮与结果
                                html.Hr(),
                                dbc.Button(
                                    [html.I(className="bi bi-robot me-2"), "生成AI诊断报告"],
                                    id='ai-diagnose-btn',
                                    color='info',
                                    className='mb-3'
                                ),
                                dcc.Loading(
                                    html.Div(id='ai-diagnose-result', className="mt-3")
                                )
                            ])
                        ], className="mb-3"),
                        
                        # 🆕 数据导出功能
                        dbc.Card([
                            dbc.CardHeader([
                                html.H4("📥 导出诊断报告", className="mb-0")
                            ]),
                            dbc.CardBody([
                                dbc.Button(
                                    [html.I(className="bi bi-download me-2"), "导出Excel报告"],
                                    id='export-report-btn',
                                    color='success',
                                    className='w-100'
                                ),
                                dcc.Download(id='download-report')
                            ])
                        ]),
                        
                        # 隐藏的数据存储组件
                        dcc.Store(id='warning-data-store'),
                        
                        # ========== 保留：AI智能助手（阶段2/阶段3）==========
                        dbc.Card([
                            dbc.CardHeader([
                                html.H4("🤖 AI智能助手", className="mb-0")
                            ]),
                            dbc.CardBody([
                                dbc.Row([
                                    # 左侧：PandasAI 自然语言分析（阶段2）
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardHeader([
                                                html.H5([
                                                    html.I(className="bi bi-chat-dots me-2"),
                                                    "阶段2: PandasAI 自然语言分析"
                                                ], className="mb-0"),
                                                dbc.Badge(PANDAS_STATUS_TEXT, color=PANDAS_STATUS_COLOR, className="ms-2")
                                            ]),
                                            dbc.CardBody([
                                                # 数据范围选择
                                                html.Div([
                                                    html.Label("📊 数据范围", className="fw-bold mb-2"),
                                                    dcc.RadioItems(
                                                        id='ai-data-scope',
                                                        options=[
                                                            {'label': ' 全部数据', 'value': 'all'},
                                                            {'label': ' 当前诊断结果', 'value': 'diagnostic'}
                                                        ],
                                                        value='all',
                                                        inline=True,
                                                        className="mb-3",
                                                        labelStyle={'margin-right': '20px'}
                                                    )
                                                ]),
                                                
                                                # 模板查询选择
                                                html.Div([
                                                    html.Label("🎯 快速模板", className="fw-bold mb-2"),
                                                    dcc.Dropdown(
                                                        id='pandasai-template-selector',
                                                        options=[],  # 从PANDAS_AI_TEMPLATES动态加载
                                                        placeholder="选择预设查询模板...",
                                                        style={'fontSize': '14px'},
                                                        className="mb-2"
                                                    )
                                                ]),
                                                
                                                # 自定义查询输入
                                                html.Div([
                                                    html.Label("💬 自定义问题", className="fw-bold mb-2"),
                                                    dbc.Textarea(
                                                        id='pandasai-query-input',
                                                        placeholder="用自然语言描述你想了解的数据问题，例如：\\n- 哪些商品的毛利率最高？\\n- 低客单价订单有哪些？\\n- 哪些商品滞销了？",
                                                        style={'minHeight': '100px', 'fontSize': '14px'},
                                                        className="mb-3"
                                                    )
                                                ]),
                                                
                                                # 执行按钮
                                                dbc.Button(
                                                    [html.I(className="bi bi-send-fill me-2"), "执行查询"],
                                                    id='pandasai-run-button',
                                                    color='success',
                                                    disabled=not PANDAS_AI_ANALYZER,
                                                    className='w-100 mb-3'
                                                ),
                                                
                                                # 结果展示
                                                html.Div(id='pandasai-run-status', className="text-muted small mt-2"),
                                                dcc.Loading(html.Div(id='pandasai-result'), className="mt-3")
                                            ])
                                        ], className="h-100")
                                    ], md=6),
                                    
                                    # 右侧：RAG 历史案例检索（阶段3）
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardHeader([
                                                html.H5([
                                                    html.I(className="bi bi-book me-2"),
                                                    "阶段3: RAG 历史案例检索"
                                                ], className="mb-0"),
                                                dbc.Badge(RAG_STATUS_TEXT, color=RAG_STATUS_COLOR, className="ms-2")
                                            ]),
                                            dbc.CardBody([
                                                # 问题描述
                                                html.Div([
                                                    html.Label("🔍 问题描述", className="fw-bold mb-2"),
                                                    dbc.Textarea(
                                                        id='rag-query-input',
                                                        placeholder="描述当前业务问题，系统将检索相似历史案例并给出建议...\\n例如：销量下滑如何应对？",
                                                        style={'minHeight': '120px', 'fontSize': '14px'},
                                                        className="mb-3"
                                                    )
                                                ]),
                                                
                                                # 执行按钮
                                                dbc.Button(
                                                    [html.I(className="bi bi-search me-2"), "搜索案例"],
                                                    id='rag-run-button',
                                                    color='info',
                                                    disabled=not RAG_ANALYZER_INSTANCE,
                                                    className='w-100 mb-3'
                                                ),
                                                
                                                # 结果展示
                                                html.Div(id='rag-run-status', className="text-muted small mt-2"),
                                                dcc.Loading(dcc.Markdown(id='rag-analysis-output'), className="mt-3"),
                                                html.Hr(),
                                                html.Div([
                                                    html.Span("知识库概览：", className="fw-bold"),
                                                    html.Span(KB_STATS_TEXT, className="ms-2 text-muted")
                                                ], className="small")
                                            ])
                                        ], className="h-100")
                                    ], md=6)
                                ], className="gy-4")
                            ])
                        ], className="mt-3")
                    ], className="p-3")
                ]),

'''

# 替换
deleted_lines = end_line - start_line
new_lines = lines[:start_line] + [new_tab4_ui] + lines[end_line:]

print(f"\n✂️ 删除旧UI：{deleted_lines} 行")
print(f"✨ 新增新UI：{new_tab4_ui.count(chr(10))} 行")
print(f"📄 最终文件：{len(new_lines)} 行")

# 写入文件
with open(input_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✅ Tab 4 UI替换完成！")
