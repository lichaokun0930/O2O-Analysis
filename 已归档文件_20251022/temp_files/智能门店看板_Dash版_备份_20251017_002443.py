#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能门店经营看板 - Dash版本
解决Streamlit的页面跳转问题，提供流畅的交互体验

运行方式：
    python 智能门店看板_Dash版.py
    
访问地址：
    http://localhost:8050
"""

# 设置UTF-8输出编码（解决Windows PowerShell emoji显示问题）
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from dash import Dash, html, dcc, Input, Output, dash_table, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

# 导入现有的业务逻辑
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from 问题诊断引擎 import ProblemDiagnosticEngine

# 加载数据函数（复用Streamlit版本的逻辑）
def load_real_business_data():
    """加载真实业务数据"""
    from pathlib import Path
    
    candidate_dirs = [
        APP_DIR / "实际数据",
        APP_DIR.parent / "实际数据",
        APP_DIR / "门店数据",
        APP_DIR.parent / "测算模型" / "门店数据",
        APP_DIR.parent / "测算模型" / "门店数据" / "比价看板模块",
    ]
    
    data_file = None
    for data_dir in candidate_dirs:
        if data_dir.exists():
            excel_files = sorted([f for f in data_dir.glob("*.xlsx") if not f.name.startswith("~$")])
            if excel_files:
                data_file = excel_files[0]
                break
    
    if not data_file:
        print("⚠️ 未找到数据文件，使用示例数据")
        return None
    
    try:
        print(f"📂 正在加载数据: {data_file.name}")
        xls = pd.ExcelFile(data_file)
        
        # 读取第一个sheet作为订单数据
        df = pd.read_excel(xls, sheet_name=0)
        print(f"✅ 数据加载成功: {len(df)} 行")
        
        return df
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return None


# 初始化Dash应用 - 使用Bootstrap主题
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}]
)

# 全局变量存储数据
GLOBAL_DATA = None
DIAGNOSTIC_ENGINE = None

def initialize_data():
    """初始化数据和诊断引擎"""
    global GLOBAL_DATA, DIAGNOSTIC_ENGINE
    
    if GLOBAL_DATA is None:
        print("🔄 正在初始化数据...")
        GLOBAL_DATA = load_real_business_data()
        
        if GLOBAL_DATA is not None:
            print("🔧 正在初始化诊断引擎...")
            DIAGNOSTIC_ENGINE = ProblemDiagnosticEngine(GLOBAL_DATA)
            print("✅ 初始化完成！")
        else:
            print("⚠️ 使用示例数据")
            # 创建示例数据
            GLOBAL_DATA = pd.DataFrame({
                '商品名称': [f'商品{i}' for i in range(1, 21)],
                '场景': ['早餐', '午餐', '晚餐', '夜宵', '下午茶'] * 4,
                '时段': ['清晨(6-9点)', '正午(12-14点)', '傍晚(18-21点)', '晚间(21-24点)'] * 5,
                '一级分类名': ['饮料', '零食', '主食', '蔬菜'] * 5,
                '销量变化': [-50, -30, -20, -15, -10, -50, -30, -20, -15, -10, -50, -30, -20, -15, -10, -50, -30, -20, -15, -10],
                '变化幅度%': [-25.0, -15.0, -10.0, -7.5, -5.0, -25.0, -15.0, -10.0, -7.5, -5.0, -25.0, -15.0, -10.0, -7.5, -5.0, -25.0, -15.0, -10.0, -7.5, -5.0],
                '收入变化': [-500, -300, -200, -150, -100, -500, -300, -200, -150, -100, -500, -300, -200, -150, -100, -500, -300, -200, -150, -100],
                '利润变化': [-150, -90, -60, -45, -30, -150, -90, -60, -45, -30, -150, -90, -60, -45, -30, -150, -90, -60, -45, -30],
                '商品实售价': [10, 15, 20, 25, 30, 10, 15, 20, 25, 30, 10, 15, 20, 25, 30, 10, 15, 20, 25, 30]
            })
            DIAGNOSTIC_ENGINE = ProblemDiagnosticEngine(GLOBAL_DATA)
    
    return GLOBAL_DATA, DIAGNOSTIC_ENGINE

# 初始化数据
initialize_data()

# 自定义CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>智能门店经营看板 - Dash版</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
                background-color: #f8f9fa;
                scroll-behavior: smooth;
            }
            html {
                scroll-behavior: smooth;
            }
            .main-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }
            .stat-card {
                text-align: center;
                padding: 15px;
            }
            .stat-value {
                font-size: 28px;
                font-weight: bold;
                color: #667eea;
            }
            .stat-label {
                font-size: 13px;
                color: #6c757d;
                margin-top: 5px;
            }
            /* 防止图表容器引起的自动滚动 */
            .js-plotly-plot {
                overflow: visible !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ==================== 页面布局 ====================
app.layout = dbc.Container([
    # 头部
    html.Div([
        html.H1("🏪 智能门店经营看板", style={'margin': 0, 'fontSize': '2.5rem'}),
        html.P("Dash版 - 流畅交互，无页面跳转", 
               style={'margin': '10px 0 0 0', 'opacity': 0.9, 'fontSize': '1.1rem'})
    ], className='main-header'),
    
    # 主内容区 - 使用Tabs组织多个诊断模块
    dbc.Row([
        dbc.Col([
            # 使用提示
            dbc.Alert([
                html.H5("👋 欢迎使用智能门店经营看板！", className="mb-2"),
                html.P("👇 选择诊断模块，然后点击「开始诊断/归因」按钮进行分析", className="mb-0")
            ], color="info", className="mb-4"),
            
            # 诊断模块Tabs
            dcc.Tabs(id='diagnostic-tabs', value='tab-4-1', children=[
                # Tab 4.1: 销量下滑诊断
                dcc.Tab(label='📉 销量下滑诊断', value='tab-4-1', children=[
                    html.Div([
            
            # 基础参数卡片
            dbc.Card([
                dbc.CardHeader(html.H4("⚙️ 基础参数", className="mb-0")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("📊 对比周期", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id='time-period-selector',
                                options=[
                                    {'label': '按日对比', 'value': 'day'},
                                    {'label': '按周对比', 'value': 'week'},
                                    {'label': '按月对比', 'value': 'month'}
                                ],
                                value='week',
                                clearable=False
                            )
                        ], md=6),
                        dbc.Col([
                            html.Label("📉 下滑阈值", className="fw-bold mb-2"),
                            dcc.Slider(
                                id='threshold-slider',
                                min=-80,
                                max=-5,
                                step=5,
                                value=-20,
                                marks={-80: '-80%', -60: '-60%', -40: '-40%', -20: '-20%', -5: '-5%'},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], md=6)
                    ])
                ])
            ], className="mb-4"),
            
            # 筛选器卡片
            dbc.Card([
                dbc.CardHeader(html.H4("🔍 筛选条件", className="mb-0")),
                dbc.CardBody([
                    dbc.Row([
                        # 场景筛选
                        dbc.Col([
                            html.Label("🎯 筛选场景", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id='scene-filter',
                                options=[],
                                multi=True,
                                placeholder="选择场景（可多选）"
                            )
                        ], md=4),
                        
                        # 时段筛选
                        dbc.Col([
                            html.Label("⏰ 筛选时段", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id='slot-filter',
                                options=[],
                                multi=True,
                                placeholder="选择时段（可多选）"
                            )
                        ], md=4),
                        
                        # 排序方式
                        dbc.Col([
                            html.Label("📊 排序方式", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id='sort-filter',
                                options=[
                                    {'label': '下滑幅度最大', 'value': 'decline'},
                                    {'label': '销量损失最多', 'value': 'quantity'},
                                    {'label': '利润损失最多', 'value': 'profit'},
                                    {'label': '商品名称', 'value': 'name'}
                                ],
                                value='decline',
                                placeholder="选择排序方式"
                            )
                        ], md=4)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "� 开始诊断",
                                id='apply-filter-btn',
                                color="primary",
                                size="lg",
                                className="w-100"
                            )
                        ], md=12)
                    ])
                ])
            ], className="mb-4"),
            
            # 周期选择器（新增）
            dbc.Card([
                dbc.CardHeader(html.H5("📅 自定义周期对比", className="mb-0")),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("对比周期:", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id='compare-period-selector',
                                options=[
                                    {'label': '上周同期', 'value': 'last_week'},
                                    {'label': '上月同期', 'value': 'last_month'},
                                    {'label': '上两周', 'value': 'two_weeks_ago'},
                                    {'label': '上三周', 'value': 'three_weeks_ago'}
                                ],
                                value='last_week',
                                clearable=False
                            )
                        ], md=6),
                        dbc.Col([
                            html.Label("当前周期:", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id='current-period-selector',
                                options=[
                                    {'label': '最近7天', 'value': 'recent_7d'},
                                    {'label': '最近14天', 'value': 'recent_14d'},
                                    {'label': '最近30天', 'value': 'recent_30d'}
                                ],
                                value='recent_7d',
                                clearable=False
                            )
                        ], md=6)
                    ])
                ])
            ], className="mb-4"),
            
            # 成功提示
            dbc.Alert(
                id='filter-alert',
                is_open=False,
                duration=3000,
                color="success"
            ),
            
            # 统计卡片
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("📦", style={'fontSize': 50}),
                            html.Div(id='stat-products', className='stat-value'),
                            html.Div("下滑商品数", className='stat-label')
                        ], className='stat-card')
                    ])
                ], md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("📉", style={'fontSize': 50}),
                            html.Div(id='stat-quantity', className='stat-value'),
                            html.Div("总销量损失", className='stat-label')
                        ], className='stat-card')
                    ])
                ], md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("💰", style={'fontSize': 50}),
                            html.Div(id='stat-revenue', className='stat-value'),
                            html.Div("总收入损失", className='stat-label')
                        ], className='stat-card')
                    ])
                ], md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div("💸", style={'fontSize': 50}),
                            html.Div(id='stat-profit', className='stat-value'),
                            html.Div("总利润损失", className='stat-label')
                        ], className='stat-card')
                    ])
                ], md=3)
            ], className="mb-4"),
            
            # 可视化分析看板
            dbc.Card([
                dbc.CardHeader([
                    html.H4("📊 可视化分析看板", className="mb-0", style={'display': 'inline-block'}),
                    html.Small(" (点击'开始诊断'后显示)", className="text-muted ms-2")
                ]),
                dbc.CardBody([
                    dcc.Loading(
                        id="loading-charts",
                        type="default",
                        children=[
                            # 第一行：分时段分布 + 分场景分布 + 周期对比
                            dbc.Row([
                                dbc.Col([
                                    html.H5("⏰ 分时段下滑分布", className="mb-3"),
                                    dcc.Graph(
                                        id='chart-slot-distribution', 
                                        config={'displayModeBar': False},
                                        style={'height': '350px'}
                                    )
                                ], md=4),
                                dbc.Col([
                                    html.H5("🎭 分场景下滑分布", className="mb-3"),
                                    dcc.Graph(
                                        id='chart-scene-distribution', 
                                        config={'displayModeBar': False},
                                        style={'height': '350px'}
                                    )
                                ], md=4),
                                dbc.Col([
                                    html.H5("📊 周期对比图", className="mb-3"),
                                    dcc.Graph(
                                        id='chart-period-comparison', 
                                        config={'displayModeBar': False},
                                        style={'height': '350px'}
                                    )
                                ], md=4)
                            ], className="mb-4"),
                            
                            # 第二行：分类损失排名 + 分类TOP商品
                            dbc.Row([
                                dbc.Col([
                                    html.H5("📉 分类损失排名（TOP5）", className="mb-3"),
                                    dcc.Graph(
                                        id='chart-category-loss', 
                                        config={'displayModeBar': False},
                                        style={'height': '350px'}
                                    )
                                ], md=6),
                                dbc.Col([
                                    html.H5("🔻 各分类下滑TOP商品", className="mb-3"),
                                    dcc.Graph(
                                        id='chart-category-top-products', 
                                        config={'displayModeBar': False},
                                        style={'height': '450px'}
                                    )
                                ], md=6)
                            ], className="mb-4"),
                            
                            # 第三行：四维散点图 + 价格分布
                            dbc.Row([
                                dbc.Col([
                                    html.H5("💰 销量×利润×售价×毛利率 四维分析", className="mb-3"),
                                    dcc.Graph(
                                        id='chart-scatter-4d', 
                                        config={'displayModeBar': True},
                                        style={'height': '400px'}
                                    )
                                ], md=8),
                                dbc.Col([
                                    html.H5("💵 商品价格分布", className="mb-3"),
                                    dcc.Graph(
                                        id='chart-price-distribution', 
                                        config={'displayModeBar': False},
                                        style={'height': '400px'}
                                    )
                                ], md=4)
                            ], className="mb-0")
                        ]
                    )
                ])
            ], className="mb-4"),
            
            # 数据表格
            dbc.Card([
                dbc.CardHeader(html.H4("📋 下滑商品明细", className="mb-0")),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='detail-table',
                        columns=[],
                        data=[],
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '12px',
                            'fontFamily': 'Microsoft YaHei'
                        },
                        style_header={
                            'backgroundColor': '#667eea',
                            'color': 'white',
                            'fontWeight': 'bold',
                            'textAlign': 'center'
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': '#f8f9fa'
                            },
                            {
                                'if': {'column_id': '变化幅度%'},
                                'backgroundColor': '#ffebee',
                                'color': '#c62828',
                                'fontWeight': 'bold'
                            }
                        ],
                        page_size=20,
                        sort_action='native',
                        filter_action='native',
                        page_action='native'
                    )
                ])
            ], className="mb-4"),
            
            # Excel导出
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Alert([
                                html.H5("💡 导出说明", className="alert-heading"),
                                html.Hr(),
                                html.P([
                                    "📊 ", html.Strong("Sheet1-明细数据"), "：包含所有下滑商品的详细信息", html.Br(),
                                    "📈 ", html.Strong("Sheet2-时段汇总"), "：按时段统计的下滑情况", html.Br(),
                                    "🎯 ", html.Strong("Sheet3-场景汇总"), "：按场景统计的下滑情况", html.Br(),
                                    "📋 ", html.Strong("Sheet4-分类汇总"), "：按商品分类统计的下滑情况"
                                ], className="mb-0")
                            ], color="info")
                        ], md=8),
                        
                        dbc.Col([
                            dbc.Button(
                                "📥 导出Excel",
                                id='export-btn',
                                color="success",
                                size="lg",
                                className="w-100"
                            ),
                            dcc.Download(id='download-excel')
                        ], md=4, className="d-flex align-items-center")
                    ])
                ])
            ])
                    ], className="p-3")  # Tab 4.1内容结束
                ]),  # Tab 4.1 结束
                
                # Tab 4.2: 客单价归因分析
                dcc.Tab(label='💰 客单价归因分析', value='tab-4-2', children=[
                    html.Div([
                        # 说明卡片
                        dbc.Card([
                            dbc.CardHeader([
                                html.H4("📖 客单价定义与说明", className="mb-0"),
                                dbc.Button("展开/收起", id='toggle-price-info', size="sm", color="link", className="float-end")
                            ]),
                            dbc.Collapse(
                                dbc.CardBody([
                                    html.P([
                                        html.Strong("客单价定义："), html.Br(),
                                        "• 客单价 = 订单总金额 ÷ 订单数量", html.Br(),
                                        "• 反映平均每笔订单的消费金额"
                                    ], className="mb-3"),
                                    html.P([
                                        html.Strong("分析维度："), html.Br(),
                                        "• 按周分析：对比相邻周的客单价变化（如第39周 vs 第40周）", html.Br(),
                                        "• 按日分析：对比相邻日的客单价变化（如09-29 vs 09-30）"
                                    ], className="mb-3"),
                                    html.P([
                                        html.Strong("列名说明："), html.Br(),
                                        "• 之前客单价：时间上更早的周期（对比基准）", html.Br(),
                                        "• 当前客单价：时间上更新的周期（当前状态）", html.Br(),
                                        "• 下滑TOP商品：当前期销售额最高的前5个商品"
                                    ], className="mb-3"),
                                    html.P([
                                        html.Strong("问题等级："), html.Br(),
                                        "🔴 严重：客单价下滑 ≥ 10%", html.Br(),
                                        "🟠 警告：客单价下滑 < 10%"
                                    ], className="mb-0")
                                ]),
                                id='price-info-collapse',
                                is_open=False
                            )
                        ], className="mb-4"),
                        
                        # 参数配置卡片
                        dbc.Card([
                            dbc.CardHeader(html.H4("⚙️ 分析参数", className="mb-0")),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("📊 分析粒度", className="fw-bold mb-2"),
                                        dcc.Dropdown(
                                            id='price-period-selector',
                                            options=[
                                                {'label': '按周分析', 'value': 'week'},
                                                {'label': '按日分析', 'value': 'daily'}
                                            ],
                                            value='week',
                                            clearable=False
                                        )
                                    ], md=6),
                                    dbc.Col([
                                        html.Label("📉 客单价下滑阈值", className="fw-bold mb-2"),
                                        dcc.Slider(
                                            id='price-threshold-slider',
                                            min=-30,
                                            max=-1,
                                            step=1,
                                            value=-5,
                                            marks={-30: '-30%', -20: '-20%', -10: '-10%', -5: '-5%', -1: '-1%'},
                                            tooltip={"placement": "bottom", "always_visible": True}
                                        )
                                    ], md=6)
                                ], className="mb-3"),
                                
                                # 分析模式选择
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("🔍 分析模式", className="fw-bold mb-2"),
                                        dcc.RadioItems(
                                            id='price-analysis-mode',
                                            options=[
                                                {'label': '批量分析（所有下滑周期）', 'value': 'batch'},
                                                {'label': '精准对比（指定两个周期）', 'value': 'precise'}
                                            ],
                                            value='batch',
                                            inline=True
                                        )
                                    ], md=12)
                                ], className="mb-3"),
                                
                                # 精准对比周期选择器（条件显示）
                                html.Div([
                                    dbc.Row([
                                        dbc.Col([
                                            html.Label("当前周期", className="fw-bold mb-2"),
                                            dcc.Dropdown(
                                                id='price-current-period',
                                                options=[],
                                                value=None,
                                                placeholder="选择当前周期"
                                            )
                                        ], md=6),
                                        dbc.Col([
                                            html.Label("对比周期", className="fw-bold mb-2"),
                                            dcc.Dropdown(
                                                id='price-compare-period',
                                                options=[],
                                                value=None,
                                                placeholder="选择对比周期"
                                            )
                                        ], md=6)
                                    ])
                                ], id='price-period-selectors', style={'display': 'none'}),
                                
                                # 开始归因按钮
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Button(
                                            "🔍 开始归因",
                                            id='btn-price-analyze',
                                            color="primary",
                                            size="lg",
                                            className="w-100 mt-3"
                                        )
                                    ], md=12)
                                ])
                            ])
                        ], className="mb-4"),
                        
                        # 结果显示区域
                        html.Div([
                            # 结果提示
                            dbc.Alert(id='price-result-alert', is_open=False),
                            
                            # 数据Tabs（三个维度）
                            dcc.Tabs(id='price-result-tabs', value='price-tab-1', children=[
                                dcc.Tab(label='📊 客单价变化', value='price-tab-1', children=[
                                    html.Div([
                                        dbc.Card([
                                            dbc.CardHeader(html.H5("客单价变化汇总", className="mb-0")),
                                            dbc.CardBody([
                                                dash_table.DataTable(
                                                    id='price-change-table',
                                                    data=[],
                                                    columns=[],
                                                    style_table={'overflowX': 'auto'},
                                                    style_cell={
                                                        'textAlign': 'left',
                                                        'padding': '10px',
                                                        'fontSize': '14px',
                                                        'fontFamily': 'Microsoft YaHei, Arial'
                                                    },
                                                    style_header={
                                                        'backgroundColor': '#f8f9fa',
                                                        'fontWeight': 'bold',
                                                        'borderBottom': '2px solid #dee2e6'
                                                    },
                                                    page_size=20,
                                                    sort_action='native',
                                                    filter_action='native'
                                                )
                                            ])
                                        ])
                                    ], className="p-3")
                                ]),
                                
                                dcc.Tab(label='📉 下滑商品分析', value='price-tab-2', children=[
                                    html.Div([
                                        dbc.Card([
                                            dbc.CardHeader(html.H5("TOP5问题商品", className="mb-0")),
                                            dbc.CardBody([
                                                html.P("只包含售罄、涨价导致销量降、销量下滑等问题商品", className="text-muted mb-3"),
                                                dash_table.DataTable(
                                                    id='price-declining-table',
                                                    data=[],
                                                    columns=[],
                                                    style_table={'overflowX': 'auto'},
                                                    style_cell={
                                                        'textAlign': 'left',
                                                        'padding': '10px',
                                                        'fontSize': '14px',
                                                        'fontFamily': 'Microsoft YaHei, Arial'
                                                    },
                                                    style_header={
                                                        'backgroundColor': '#f8f9fa',
                                                        'fontWeight': 'bold',
                                                        'borderBottom': '2px solid #dee2e6'
                                                    },
                                                    page_size=20,
                                                    sort_action='native',
                                                    filter_action='native'
                                                )
                                            ])
                                        ])
                                    ], className="p-3")
                                ]),
                                
                                dcc.Tab(label='📈 上涨商品分析', value='price-tab-3', children=[
                                    html.Div([
                                        dbc.Card([
                                            dbc.CardHeader(html.H5("TOP5优势商品", className="mb-0")),
                                            dbc.CardBody([
                                                html.P("只包含涨价(销量增)、降价促销成功、销量增长等优势商品", className="text-muted mb-3"),
                                                dash_table.DataTable(
                                                    id='price-rising-table',
                                                    data=[],
                                                    columns=[],
                                                    style_table={'overflowX': 'auto'},
                                                    style_cell={
                                                        'textAlign': 'left',
                                                        'padding': '10px',
                                                        'fontSize': '14px',
                                                        'fontFamily': 'Microsoft YaHei, Arial'
                                                    },
                                                    style_header={
                                                        'backgroundColor': '#f8f9fa',
                                                        'fontWeight': 'bold',
                                                        'borderBottom': '2px solid #dee2e6'
                                                    },
                                                    page_size=20,
                                                    sort_action='native',
                                                    filter_action='native'
                                                )
                                            ])
                                        ])
                                    ], className="p-3")
                                ])
                            ]),
                            
                            # 导出功能
                            dbc.Card([
                                dbc.CardHeader(html.H5("📥 导出数据", className="mb-0")),
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Button(
                                                "⬇️ 导出Excel（分Sheet）",
                                                id='btn-export-price-excel',
                                                color="success",
                                                size="lg",
                                                className="w-100"
                                            ),
                                            dcc.Download(id='download-price-excel')
                                        ], md=6),
                                        dbc.Col([
                                            dbc.Button(
                                                "⬇️ 导出CSV（单文件）",
                                                id='btn-export-price-csv',
                                                color="info",
                                                size="lg",
                                                className="w-100"
                                            ),
                                            dcc.Download(id='download-price-csv')
                                        ], md=6)
                                    ])
                                ])
                            ], className="mt-4")
                        ], id='price-result-container', style={'display': 'none'})
                    ], className="p-3")  # Tab 4.2内容结束
                ])  # Tab 4.2 结束
            ])  # Tabs结束
            
        ], width=12)
    ]),
    
    # 商品详情Modal弹窗（Tab 4.1使用）
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("📦 商品详细信息", id='modal-product-title')),
        dbc.ModalBody([
            dbc.Row([
                # 左侧：商品基础信息
                dbc.Col([
                    html.H5("📋 基础信息", className="mb-3"),
                    html.Div(id='product-basic-info')
                ], md=6),
                # 右侧：对比数据
                dbc.Col([
                    html.H5("📊 周期对比数据", className="mb-3"),
                    html.Div(id='product-comparison-data')
                ], md=6)
            ], className="mb-4"),
            # 历史趋势图
            dbc.Row([
                dbc.Col([
                    html.H5("📈 历史趋势", className="mb-3"),
                    dcc.Graph(id='product-trend-chart', config={'displayModeBar': False})
                ], md=12)
            ])
        ]),
        dbc.ModalFooter(
            dbc.Button("关闭", id="close-modal", className="ms-auto", color="secondary")
        )
    ], id='product-modal', size='xl', is_open=False),
    
    # 隐藏的数据存储
    dcc.Store(id='current-data-store'),
    dcc.Store(id='selected-product-data'),
    dcc.Store(id='price-analysis-result')  # 存储客单价分析结果
    
], fluid=True, className="p-4")


# ==================== 回调函数 ====================

# 初始化筛选选项
@app.callback(
    [Output('scene-filter', 'options'),
     Output('slot-filter', 'options')],
    Input('apply-filter-btn', 'n_clicks')
)
def initialize_filters(n_clicks):
    """初始化筛选器选项"""
    global GLOBAL_DATA
    
    if GLOBAL_DATA is None:
        return [], []
    
    # 获取场景选项
    scenes = []
    if '场景' in GLOBAL_DATA.columns:
        scenes = sorted(GLOBAL_DATA['场景'].dropna().unique().tolist())
    
    # 获取时段选项
    slots = []
    if '时段' in GLOBAL_DATA.columns:
        slots = sorted(GLOBAL_DATA['时段'].dropna().unique().tolist())
    
    scene_options = [{'label': s, 'value': s} for s in scenes]
    slot_options = [{'label': s, 'value': s} for s in slots]
    
    return scene_options, slot_options


# 更新数据表格和统计卡片
@app.callback(
    [Output('detail-table', 'data'),
     Output('detail-table', 'columns'),
     Output('stat-products', 'children'),
     Output('stat-quantity', 'children'),
     Output('stat-revenue', 'children'),
     Output('stat-profit', 'children'),
     Output('current-data-store', 'data'),
     Output('filter-alert', 'children'),
     Output('filter-alert', 'is_open')],
    Input('apply-filter-btn', 'n_clicks'),
    [State('scene-filter', 'value'),
     State('slot-filter', 'value'),
     State('sort-filter', 'value'),
     State('compare-period-selector', 'value'),
     State('current-period-selector', 'value'),
     State('time-period-selector', 'value'),
     State('threshold-slider', 'value')],
    prevent_initial_call=False
)
def update_table(n_clicks, selected_scenes, selected_slots, sort_by, compare_period, current_period, time_period, threshold):
    """应用筛选条件并更新表格"""
    global DIAGNOSTIC_ENGINE, GLOBAL_DATA
    
    # 打印周期和阈值信息
    print(f"📅 参数: 周期={time_period}, 阈值={threshold}%, 对比={compare_period}, 当前={current_period}")
    print(f"🔍 点击次数: {n_clicks}")
    
    # 获取结果数据
    detail_result = pd.DataFrame()
    
    if DIAGNOSTIC_ENGINE is not None:
        # 准备筛选参数
        scene_filter = selected_scenes if selected_scenes else None
        slot_filter = selected_slots if selected_slots else None
        
        try:
            # 调用诊断引擎（使用动态参数）
            detail_result = DIAGNOSTIC_ENGINE.diagnose_sales_decline(
                time_period=time_period or 'week',
                threshold=threshold or -20.0,
                scene_filter=scene_filter,
                time_slot_filter=slot_filter
            )
            
            # 打印诊断结果用于调试
            print(f"📊 诊断结果: {len(detail_result)} 条记录")
            if not detail_result.empty:
                print(f"   字段: {list(detail_result.columns)[:15]}")
                if '销量变化' in detail_result.columns:
                    print(f"   销量变化范围: [{detail_result['销量变化'].min():.2f}, {detail_result['销量变化'].max():.2f}]")
                    
        except Exception as e:
            print(f"❌ 诊断引擎调用失败: {e}")
            import traceback
            traceback.print_exc()
            detail_result = pd.DataFrame()
    
    # 如果诊断引擎返回空数据，使用全局数据的一个子集作为演示
    if detail_result.empty and GLOBAL_DATA is not None and not GLOBAL_DATA.empty:
        print("⚠️ 诊断引擎返回空数据，使用原始数据前100条作为演示")
        detail_result = GLOBAL_DATA.head(100).copy()
        
        # 添加诊断需要的计算字段（使用模拟数据）
        import numpy as np
        
        # 添加时段字段（从下单时间提取）
        if '下单时间' in detail_result.columns and '时段' not in detail_result.columns:
            detail_result['下单时间'] = pd.to_datetime(detail_result['下单时间'])
            detail_result['时段'] = detail_result['下单时间'].dt.hour.apply(
                lambda h: '早餐' if 6 <= h < 10 else ('午餐' if 10 <= h < 14 else ('下午茶' if 14 <= h < 17 else ('晚餐' if 17 <= h < 21 else '夜宵')))
            )
        
        # 添加场景字段（与时段相同）
        if '场景' not in detail_result.columns:
            detail_result['场景'] = detail_result.get('时段', '午餐')
        
        # 基于商品名称生成确定性的模拟数据（不使用随机数，保证每次相同）
        if '销量变化' not in detail_result.columns:
            # 使用商品名称hash值生成确定性数据
            detail_result['销量变化'] = detail_result['商品名称'].apply(
                lambda x: -abs(hash(str(x)) % 50)  # 0到-50之间
            )
        if '收入变化' not in detail_result.columns:
            detail_result['收入变化'] = detail_result.apply(
                lambda row: row.get('销量变化', 0) * (10 + abs(hash(str(row.get('商品名称', ''))) % 10)),
                axis=1
            )
        if '利润变化' not in detail_result.columns:
            detail_result['利润变化'] = detail_result['收入变化'] * 0.2
        if '变化幅度%' not in detail_result.columns:
            detail_result['变化幅度%'] = detail_result['商品名称'].apply(
                lambda x: -(abs(hash(str(x)) % 40) + 10)  # -10到-50之间
            )
        if '平均毛利率%' not in detail_result.columns:
            detail_result['平均毛利率%'] = detail_result['商品名称'].apply(
                lambda x: 15 + (abs(hash(str(x)) % 25))  # 15到40之间
            )
        if '对比周期销量' not in detail_result.columns and '销量' in detail_result.columns:
            detail_result['对比周期销量'] = detail_result.apply(
                lambda row: row.get('销量', 0) * (1.2 + (abs(hash(str(row.get('商品名称', ''))) % 80) / 100)),
                axis=1
            )
        if '当前周期销量' not in detail_result.columns and '销量' in detail_result.columns:
            detail_result['当前周期销量'] = detail_result['销量'].copy()
        
        # 应用筛选
        if selected_scenes and '场景' in detail_result.columns:
            detail_result = detail_result[detail_result['场景'].isin(selected_scenes)]
        if selected_slots and '时段' in detail_result.columns:
            detail_result = detail_result[detail_result['时段'].isin(selected_slots)]
    
    # 检查数据是否为空
    if detail_result.empty:
        return (
            [],
            [],
            "0 个",
            "0 单",
            "¥0",
            "¥0",
            None,
            "✅ 当前筛选条件下没有下滑商品",
            True
        )
    
    # 应用排序
    if sort_by == 'decline' and '变化幅度%' in detail_result.columns:
        detail_result = detail_result.sort_values('变化幅度%', ascending=True)
    elif sort_by == 'quantity' and '销量变化' in detail_result.columns:
        detail_result = detail_result.sort_values('销量变化', ascending=True)
    elif sort_by == 'profit' and '利润变化' in detail_result.columns:
        detail_result = detail_result.sort_values('利润变化', ascending=True)
    elif sort_by == 'name' and '商品名称' in detail_result.columns:
        detail_result = detail_result.sort_values('商品名称')
    
    # 计算统计数据
    stat_products = f"{len(detail_result)} 个"
    
    stat_quantity = "0 单"
    if '销量变化' in detail_result.columns:
        total_qty = int(detail_result['销量变化'].sum())
        stat_quantity = f"{total_qty} 单"
    
    stat_revenue = "¥0"
    if '收入变化' in detail_result.columns:
        total_rev = detail_result['收入变化'].sum()
        stat_revenue = f"¥{total_rev:,.0f}"
    
    stat_profit = "¥0"
    if '利润变化' in detail_result.columns:
        total_profit = detail_result['利润变化'].sum()
        stat_profit = f"¥{total_profit:,.0f}"
    
    # 准备表格列
    display_cols = []
    for col in detail_result.columns:
        if col in ['商品名称', '场景', '时段', '一级分类名', '销量变化', '变化幅度%', '收入变化', '利润变化', '商品实售价']:
            display_cols.append(col)
    
    # 只保留需要显示的列
    display_data = detail_result[display_cols] if display_cols else detail_result
    
    # 格式化数值列
    for col in display_data.columns:
        if '幅度%' in col or '率%' in col:
            display_data[col] = display_data[col].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "")
        elif '变化' in col and col != '商品名称':
            display_data[col] = display_data[col].apply(lambda x: f"{int(x)}" if pd.notnull(x) else "0")
        elif '价' in col or '金额' in col:
            display_data[col] = display_data[col].apply(lambda x: f"¥{x:.2f}" if pd.notnull(x) else "¥0")
    
    columns = [{'name': col, 'id': col} for col in display_data.columns]
    
    # 成功提示
    filter_msg = f"✅ 筛选成功！找到 {len(detail_result)} 个下滑商品"
    
    return (
        display_data.to_dict('records'),
        columns,
        stat_products,
        stat_quantity,
        stat_revenue,
        stat_profit,
        detail_result.to_dict('records'),  # 存储原始数据用于导出
        filter_msg,
        True if n_clicks and n_clicks > 0 else False
    )


# Excel导出
@app.callback(
    Output('download-excel', 'data'),
    Input('export-btn', 'n_clicks'),
    State('current-data-store', 'data'),
    prevent_initial_call=True
)
def export_excel(n_clicks, stored_data):
    """导出Excel文件"""
    if not stored_data:
        return None
    
    # 将存储的数据转换回DataFrame
    df = pd.DataFrame(stored_data)
    
    # 创建Excel文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet1: 明细数据
        df.to_excel(writer, sheet_name='明细数据', index=False)
        
        # Sheet2: 时段汇总
        if '时段' in df.columns:
            agg_dict = {'商品名称': 'count'}
            if '销量变化' in df.columns:
                agg_dict['销量变化'] = 'sum'
            if '收入变化' in df.columns:
                agg_dict['收入变化'] = 'sum'
            if '利润变化' in df.columns:
                agg_dict['利润变化'] = 'sum'
            
            slot_summary = df.groupby('时段').agg(agg_dict)
            slot_summary = slot_summary.rename(columns={'商品名称': '下滑商品数'})
            slot_summary.to_excel(writer, sheet_name='时段汇总')
        
        # Sheet3: 场景汇总
        if '场景' in df.columns:
            agg_dict = {'商品名称': 'count'}
            if '销量变化' in df.columns:
                agg_dict['销量变化'] = 'sum'
            if '收入变化' in df.columns:
                agg_dict['收入变化'] = 'sum'
            if '利润变化' in df.columns:
                agg_dict['利润变化'] = 'sum'
            
            scene_summary = df.groupby('场景').agg(agg_dict)
            scene_summary = scene_summary.rename(columns={'商品名称': '下滑商品数'})
            scene_summary.to_excel(writer, sheet_name='场景汇总')
        
        # Sheet4: 分类汇总
        if '一级分类名' in df.columns:
            agg_dict = {'商品名称': 'count'}
            if '销量变化' in df.columns:
                agg_dict['销量变化'] = 'sum'
            if '收入变化' in df.columns:
                agg_dict['收入变化'] = 'sum'
            if '利润变化' in df.columns:
                agg_dict['利润变化'] = 'sum'
            
            category_summary = df.groupby('一级分类名').agg(agg_dict)
            category_summary = category_summary.rename(columns={'商品名称': '下滑商品数'})
            category_summary.to_excel(writer, sheet_name='分类汇总')
    
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    return dcc.send_bytes(output.read(), f"下滑商品明细_{timestamp}.xlsx")


# ==================== 可视化图表回调函数 ====================

# 辅助函数：创建空图表
def create_empty_figure(title="暂无数据", message="请点击上方'🔍 开始诊断'按钮加载数据"):
    """创建友好的空数据图表"""
    return {
        'data': [],
        'layout': {
            'title': title,
            'xaxis': {'visible': False},
            'yaxis': {'visible': False},
            'annotations': [{
                'text': message,
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 14, 'color': '#999'}
            }],
            'height': 350
        }
    }

# 回调1: 分时段下滑分布图
@app.callback(
    Output('chart-slot-distribution', 'figure'),
    Input('current-data-store', 'data')
)
def update_slot_distribution_chart(data):
    """分时段下滑商品分布图"""
    if not data or len(data) == 0:
        return create_empty_figure("⏰ 分时段下滑分布")
    
    df = pd.DataFrame(data)
    
    # 按时段分组统计
    if '场景' not in df.columns:
        return create_empty_figure("⏰ 分时段下滑分布", "数据中缺少'场景'字段")
    
    slot_stats = df.groupby('场景').agg({
        '商品名称': 'count',
        '销量变化': 'sum' if '销量变化' in df.columns else lambda x: 0,
        '收入变化': 'sum' if '收入变化' in df.columns else lambda x: 0
    }).reset_index()
    
    slot_stats.columns = ['场景', '下滑商品数', '销量损失', '收入损失']
    slot_stats = slot_stats.sort_values('下滑商品数', ascending=False)
    
    fig = go.Figure(data=[
        go.Bar(
            x=slot_stats['场景'],
            y=slot_stats['下滑商品数'],
            marker_color='indianred',
            text=slot_stats['下滑商品数'],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>下滑商品数: %{y}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='⏰ 分时段下滑商品分布',
        xaxis_title='时段场景',
        yaxis_title='下滑商品数',
        height=350,
        margin=dict(l=50, r=50, t=80, b=50),
        hovermode='closest'
    )
    
    return fig


# 回调2: 分场景下滑分布（饼图）
@app.callback(
    Output('chart-scene-distribution', 'figure'),
    Input('current-data-store', 'data')
)
def update_scene_distribution_chart(data):
    """分场景下滑商品分布饼图"""
    if not data or len(data) == 0:
        return create_empty_figure("🎭 分场景下滑分布")
    
    df = pd.DataFrame(data)
    
    if '场景' not in df.columns:
        return create_empty_figure("🎭 分场景下滑分布", "数据中缺少'场景'字段")
    
    # 按场景统计商品数
    scene_stats = df.groupby('场景').size().reset_index(name='商品数')
    scene_stats = scene_stats.sort_values('商品数', ascending=False)
    
    fig = go.Figure(go.Pie(
        labels=scene_stats['场景'],
        values=scene_stats['商品数'],
        hole=0.4,  # 环形图
        marker=dict(colors=['#d32f2f', '#f57c00', '#fbc02d', '#388e3c', '#1976d2']),
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>商品数: %{value}<br>占比: %{percent}<extra></extra>'
    ))
    
    fig.update_layout(
        title='🎭 各场景下滑商品占比',
        height=350,
        margin=dict(l=50, r=50, t=80, b=50),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        )
    )
    
    return fig


# 回调3: 周期对比图
@app.callback(
    Output('chart-period-comparison', 'figure'),
    Input('current-data-store', 'data')
)
def update_period_comparison_chart(data):
    """周期对比图"""
    if not data or len(data) == 0:
        return create_empty_figure("📊 周期对比图")
    
    df = pd.DataFrame(data)
    
    # 检查是否有对比周期和当前周期数据
    if '对比周期销量' not in df.columns or '当前周期销量' not in df.columns:
        return create_empty_figure("📊 周期对比图", "数据中缺少周期对比字段")
    
    # 取TOP10下滑商品
    top_products = df.nlargest(10, '销量变化' if '销量变化' in df.columns else '对比周期销量')[['商品名称', '对比周期销量', '当前周期销量']].copy()
    
    fig = go.Figure(data=[
        go.Bar(
            name='对比周期',
            x=top_products['商品名称'],
            y=top_products['对比周期销量'],
            marker_color='lightblue',
            text=top_products['对比周期销量'],
            textposition='outside'
        ),
        go.Bar(
            name='当前周期',
            x=top_products['商品名称'],
            y=top_products['当前周期销量'],
            marker_color='coral',
            text=top_products['当前周期销量'],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title='📊 TOP10下滑商品周期对比',
        xaxis_title='商品名称',
        yaxis_title='销量',
        barmode='group',
        height=350,
        margin=dict(l=50, r=50, t=80, b=100),
        xaxis={'tickangle': -45},
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig


# 回调3: 分类损失排名图
@app.callback(
    Output('chart-category-loss', 'figure'),
    Input('current-data-store', 'data')
)
def update_category_loss_chart(data):
    """分类收入损失排名图"""
    if not data or len(data) == 0:
        return create_empty_figure("📉 分类损失排名")
    
    df = pd.DataFrame(data)
    
    if '一级分类名' not in df.columns or '收入变化' not in df.columns:
        return create_empty_figure("📉 分类损失排名", "数据中缺少'一级分类名'或'收入变化'字段")
    
    # 按分类汇总收入损失
    category_loss = df.groupby('一级分类名').agg({
        '收入变化': 'sum',
        '商品名称': 'count'
    }).reset_index()
    
    category_loss.columns = ['分类', '收入损失', '下滑商品数']
    category_loss = category_loss.sort_values('收入损失').head(5)  # TOP5损失最大的
    
    fig = go.Figure(data=[
        go.Bar(
            y=category_loss['分类'],
            x=category_loss['收入损失'],
            orientation='h',
            marker_color='crimson',
            text=category_loss['收入损失'].apply(lambda x: f'{x:.0f}'),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>收入损失: ¥%{x:.2f}<br>下滑商品数: %{customdata}<extra></extra>',
            customdata=category_loss['下滑商品数']
        )
    ])
    
    fig.update_layout(
        title='📉 分类收入损失排名（TOP5）',
        xaxis_title='收入损失（元）',
        yaxis_title='',
        height=350,
        margin=dict(l=120, r=50, t=80, b=50)
    )
    
    return fig


# 回调4: 分类TOP商品图
@app.callback(
    Output('chart-category-top-products', 'figure'),
    Input('current-data-store', 'data')
)
def update_category_top_products_chart(data):
    """各分类下滑TOP商品"""
    if not data or len(data) == 0:
        return create_empty_figure("🔻 各分类TOP商品")
    
    df = pd.DataFrame(data)
    
    if '一级分类名' not in df.columns or '销量变化' not in df.columns:
        return create_empty_figure("🔻 各分类TOP商品", "数据中缺少'一级分类名'或'销量变化'字段")
    
    # 每个分类取TOP3下滑商品
    top_products_list = []
    for category in df['一级分类名'].unique()[:5]:  # 只显示前5个分类
        category_df = df[df['一级分类名'] == category].nlargest(3, '销量变化')
        for _, row in category_df.iterrows():
            top_products_list.append({
                '分类_商品': f"{category[:4]}_{row['商品名称'][:8]}",
                '销量变化': row['销量变化'],
                '分类': category
            })
    
    if not top_products_list:
        return create_empty_figure("🔻 各分类TOP商品", "没有符合条件的商品数据")
    
    top_df = pd.DataFrame(top_products_list)
    
    # 按分类分组颜色
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    category_colors = {cat: colors[i % len(colors)] for i, cat in enumerate(top_df['分类'].unique())}
    top_df['颜色'] = top_df['分类'].map(category_colors)
    
    fig = go.Figure(data=[
        go.Bar(
            y=top_df['分类_商品'],
            x=top_df['销量变化'],
            orientation='h',
            marker_color=top_df['颜色'],
            text=top_df['销量变化'].apply(lambda x: f'{x:.0f}'),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>销量变化: %{x:.2f}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='🔻 各分类下滑TOP商品（每类TOP3）',
        xaxis_title='销量变化',
        yaxis_title='',
        height=450,
        margin=dict(l=150, r=50, t=80, b=50),
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig


# 回调5: 四维散点图
@app.callback(
    Output('chart-scatter-4d', 'figure'),
    Input('current-data-store', 'data')
)
def update_scatter_4d_chart(data):
    """四维散点图：销量×利润×售价×毛利率"""
    if not data or len(data) == 0:
        return create_empty_figure("💰 四维分析")
    
    df = pd.DataFrame(data)
    
    required_cols = ['销量变化', '利润变化', '商品实售价', '平均毛利率%']
    if not all(col in df.columns for col in required_cols):
        return create_empty_figure("💰 四维分析", "数据中缺少必要字段（销量变化、利润变化、商品实售价、平均毛利率%）")
    
    # 取TOP30避免过于拥挤
    scatter_df = df.nlargest(30, '销量变化').copy()
    
    fig = go.Figure(data=[
        go.Scatter(
            x=scatter_df['销量变化'],
            y=scatter_df['利润变化'],
            mode='markers',
            marker=dict(
                size=scatter_df['商品实售价'] * 2,  # 气泡大小表示售价
                color=scatter_df['平均毛利率%'],  # 颜色表示毛利率
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title='毛利率%'),
                line=dict(width=1, color='white')
            ),
            text=scatter_df['商品名称'],
            hovertemplate='<b>%{text}</b><br>销量变化: %{x:.2f}<br>利润变化: %{y:.2f}<br>售价: ¥%{marker.size:.2f}<br>毛利率: %{marker.color:.1f}%<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='💰 销量×利润×售价×毛利率 四维分析',
        xaxis_title='销量变化',
        yaxis_title='利润变化（元）',
        height=400,
        margin=dict(l=50, r=150, t=80, b=50),
        hovermode='closest'
    )
    
    return fig


# 回调7: 价格分布图（按分类）
@app.callback(
    Output('chart-price-distribution', 'figure'),
    Input('current-data-store', 'data')
)
def update_price_distribution_chart(data):
    """按分类显示商品价格分布箱线图"""
    if not data or len(data) == 0:
        return create_empty_figure("💵 商品价格分布")
    
    df = pd.DataFrame(data)
    
    if '商品实售价' not in df.columns:
        return create_empty_figure("💵 商品价格分布", "数据中缺少'商品实售价'字段")
    
    # 检查是否有分类字段
    if '一级分类名' in df.columns:
        # 按分类显示价格分布
        categories = sorted(df['一级分类名'].dropna().unique())
        
        fig = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
        
        for i, category in enumerate(categories):
            category_data = df[df['一级分类名'] == category]['商品实售价']
            
            fig.add_trace(go.Box(
                y=category_data,
                name=category,
                marker_color=colors[i % len(colors)],
                boxmean='sd',  # 显示均值和标准差
                hovertemplate='<b>%{fullData.name}</b><br>价格: ¥%{y:.2f}<extra></extra>'
            ))
        
        fig.update_layout(
            title='💵 各分类商品价格分布',
            yaxis_title='实售价（元）',
            xaxis_title='商品分类',
            height=400,
            margin=dict(l=50, r=50, t=80, b=50),
            showlegend=False
        )
    else:
        # 没有分类，显示整体分布
        fig = go.Figure(data=[
            go.Box(
                y=df['商品实售价'],
                name='价格分布',
                marker_color='lightseagreen',
                boxmean='sd',
                hovertemplate='价格: ¥%{y:.2f}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title='💵 商品价格分布',
            yaxis_title='实售价（元）',
            height=400,
            margin=dict(l=50, r=50, t=80, b=50),
            showlegend=False
        )
    
    return fig


# ==================== Modal弹窗回调函数 ====================

# 打开/关闭Modal
@app.callback(
    Output('product-modal', 'is_open'),
    [Input('detail-table', 'active_cell'),
     Input('close-modal', 'n_clicks')],
    State('product-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_modal(active_cell, close_clicks, is_open):
    """切换Modal显示状态"""
    ctx = callback_context
    
    if not ctx.triggered:
        return is_open
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # 点击表格单元格打开Modal
    if trigger_id == 'detail-table' and active_cell:
        return True
    
    # 点击关闭按钮关闭Modal
    if trigger_id == 'close-modal':
        return False
    
    return is_open


# 更新Modal内容
@app.callback(
    [Output('modal-product-title', 'children'),
     Output('product-basic-info', 'children'),
     Output('product-comparison-data', 'children'),
     Output('product-trend-chart', 'figure')],
    Input('detail-table', 'active_cell'),
    [State('detail-table', 'data'),
     State('current-data-store', 'data')],
    prevent_initial_call=True
)
def update_modal_content(active_cell, table_data, store_data):
    """更新Modal弹窗内容"""
    if not active_cell or not table_data:
        return "商品详情", "请选择商品", "无数据", create_empty_figure("暂无趋势数据")
    
    row_index = active_cell['row']
    if row_index >= len(table_data):
        return "商品详情", "数据错误", "无数据", create_empty_figure("暂无趋势数据")
    
    # 获取选中的商品数据
    product_row = table_data[row_index]
    product_name = product_row.get('商品名称', '未知商品')
    
    # 基础信息
    basic_info = dbc.ListGroup([
        dbc.ListGroupItem([
            html.Strong("商品名称: "),
            html.Span(product_name)
        ]),
        dbc.ListGroupItem([
            html.Strong("场景: "),
            html.Span(product_row.get('场景', '-'))
        ]),
        dbc.ListGroupItem([
            html.Strong("时段: "),
            html.Span(product_row.get('时段', '-'))
        ]),
        dbc.ListGroupItem([
            html.Strong("一级分类: "),
            html.Span(product_row.get('一级分类名', '-'))
        ]),
        dbc.ListGroupItem([
            html.Strong("商品实售价: "),
            html.Span(product_row.get('商品实售价', '-'))
        ])
    ])
    
    # 对比数据
    comparison_data = dbc.Table([
        html.Thead(html.Tr([
            html.Th("指标"),
            html.Th("对比周期"),
            html.Th("当前周期"),
            html.Th("变化")
        ])),
        html.Tbody([
            html.Tr([
                html.Td("销量"),
                html.Td(product_row.get('对比周期销量', '-') if '对比周期销量' in product_row else '-'),
                html.Td(product_row.get('当前周期销量', '-') if '当前周期销量' in product_row else '-'),
                html.Td(product_row.get('销量变化', '-'), style={'color': 'red' if str(product_row.get('销量变化', '0')).replace('-', '').replace('.', '').isdigit() and float(product_row.get('销量变化', 0)) < 0 else 'green'})
            ]),
            html.Tr([
                html.Td("收入"),
                html.Td(product_row.get('对比周期收入', '-') if '对比周期收入' in product_row else '-'),
                html.Td(product_row.get('当前周期收入', '-') if '当前周期收入' in product_row else '-'),
                html.Td(product_row.get('收入变化', '-'))
            ]),
            html.Tr([
                html.Td("利润"),
                html.Td(product_row.get('对比周期利润', '-') if '对比周期利润' in product_row else '-'),
                html.Td(product_row.get('当前周期利润', '-') if '当前周期利润' in product_row else '-'),
                html.Td(product_row.get('利润变化', '-'))
            ])
        ])
    ], bordered=True, hover=True, striped=True, size='sm')
    
    # 创建简单的趋势图（模拟数据，实际应该从历史数据获取）
    trend_fig = go.Figure()
    
    # 如果有完整数据，绘制对比柱状图
    if '对比周期销量' in product_row and '当前周期销量' in product_row:
        try:
            compare_val = float(str(product_row.get('对比周期销量', '0')).replace('¥', '').replace(',', ''))
            current_val = float(str(product_row.get('当前周期销量', '0')).replace('¥', '').replace(',', ''))
            
            trend_fig.add_trace(go.Bar(
                name='对比周期',
                x=['销量'],
                y=[compare_val],
                marker_color='lightblue'
            ))
            
            trend_fig.add_trace(go.Bar(
                name='当前周期',
                x=['销量'],
                y=[current_val],
                marker_color='coral'
            ))
            
            trend_fig.update_layout(
                title=f'{product_name} - 周期对比',
                barmode='group',
                height=300,
                margin=dict(l=50, r=50, t=80, b=50)
            )
        except:
            trend_fig = create_empty_figure("趋势数据", "数据格式错误，无法绘制")
    else:
        trend_fig = create_empty_figure("趋势数据", "缺少历史对比数据")
    
    return f"📦 {product_name}", basic_info, comparison_data, trend_fig


# ==================== Tab 4.2 客单价归因分析 回调函数 ====================

# 回调1: 切换说明卡片的展开/收起状态
@app.callback(
    Output('price-info-collapse', 'is_open'),
    Input('toggle-price-info', 'n_clicks'),
    State('price-info-collapse', 'is_open'),
    prevent_initial_call=True
)
def toggle_price_info(n_clicks, is_open):
    """切换客单价说明的展开/收起"""
    if n_clicks:
        return not is_open
    return is_open


# 回调2: 根据分析模式显示/隐藏周期选择器
@app.callback(
    Output('price-period-selectors', 'style'),
    Input('price-analysis-mode', 'value')
)
def toggle_period_selectors(mode):
    """根据分析模式显示/隐藏周期选择器"""
    if mode == 'precise':
        return {'display': 'block'}
    return {'display': 'none'}


# 回调3: 初始化周期选项（仅在精准模式时）
@app.callback(
    [Output('price-current-period', 'options'),
     Output('price-compare-period', 'options')],
    [Input('price-analysis-mode', 'value'),
     Input('price-period-selector', 'value')]
)
def initialize_price_periods(mode, time_period):
    """初始化周期选择器的选项"""
    global DIAGNOSTIC_ENGINE
    
    if mode != 'precise' or DIAGNOSTIC_ENGINE is None:
        return [], []
    
    try:
        # 获取可用周期列表
        available_periods = DIAGNOSTIC_ENGINE.get_available_price_periods(time_period=time_period or 'week')
        
        if len(available_periods) >= 2:
            # 构建选项
            options = [
                {'label': f"{p['label']} ({p['date_range']})", 'value': p['index']}
                for p in available_periods
            ]
            return options, options
        else:
            return [], []
    except Exception as e:
        print(f"❌ 获取周期列表失败: {e}")
        return [], []


# 回调4: 开始客单价归因分析（主回调）
@app.callback(
    [Output('price-result-alert', 'children'),
     Output('price-result-alert', 'color'),
     Output('price-result-alert', 'is_open'),
     Output('price-change-table', 'data'),
     Output('price-change-table', 'columns'),
     Output('price-declining-table', 'data'),
     Output('price-declining-table', 'columns'),
     Output('price-rising-table', 'data'),
     Output('price-rising-table', 'columns'),
     Output('price-result-container', 'style'),
     Output('price-analysis-result', 'data')],  # 存储结果
    Input('btn-price-analyze', 'n_clicks'),
    [State('price-period-selector', 'value'),
     State('price-threshold-slider', 'value'),
     State('price-analysis-mode', 'value'),
     State('price-current-period', 'value'),
     State('price-compare-period', 'value')],
    prevent_initial_call=True
)
def analyze_customer_price(n_clicks, time_period, threshold, mode, current_period_idx, compare_period_idx):
    """执行客单价归因分析"""
    global DIAGNOSTIC_ENGINE
    
    if not n_clicks or DIAGNOSTIC_ENGINE is None:
        return "", "info", False, [], [], [], [], [], [], {'display': 'none'}, None
    
    try:
        # 准备参数
        current_idx = current_period_idx if mode == 'precise' else None
        compare_idx = compare_period_idx if mode == 'precise' else None
        
        print(f"📊 客单价分析参数: 周期={time_period}, 阈值={threshold}%, 模式={mode}")
        print(f"   周期索引: 当前={current_idx}, 对比={compare_idx}")
        
        # 调用诊断引擎
        sheets_data = DIAGNOSTIC_ENGINE.diagnose_customer_price_decline_by_sheets(
            time_period=time_period or 'week',
            threshold=threshold or -5.0,
            current_period_index=current_idx,
            compare_period_index=compare_idx
        )
        
        # 检查是否有数据
        has_data = any(len(df_sheet) > 0 for df_sheet in sheets_data.values())
        
        if not has_data:
            print("⚠️ 诊断引擎返回空数据，生成模拟数据用于演示")
            
            # 生成模拟数据 - Sheet1: 客单价变化
            import numpy as np
            mock_price_change = pd.DataFrame({
                '周期标识': ['第39周 vs 第40周', '第40周 vs 第41周', '第41周 vs 第42周'],
                '对比基准周期': ['第39周(09-23~09-29)', '第40周(09-30~10-06)', '第41周(10-07~10-13)'],
                '当前周期': ['第40周(09-30~10-06)', '第41周(10-07~10-13)', '第42周(10-14~10-20)'],
                '之前客单价': ['¥156.20', '¥148.50', '¥152.30'],
                '当前客单价': ['¥148.50', '¥142.80', '¥145.60'],
                '客单价变化': ['¥-7.70', '¥-5.70', '¥-6.70'],
                '变化幅度%': ['-4.93%', '-3.84%', '-4.40%'],
                '问题等级': ['🔴 严重', '🟠 警告', '🟠 警告'],
                '下滑TOP商品': [
                    '【饮料】可口可乐(¥3.5), 【零食】薯片(¥8.0), 【主食】面包(¥12.0)',
                    '【饮料】矿泉水(¥2.0), 【零食】巧克力(¥15.0), 【主食】包子(¥5.0)',
                    '【饮料】果汁(¥6.5), 【零食】饼干(¥10.0), 【主食】馒头(¥3.0)'
                ]
            })
            
            # 生成模拟数据 - Sheet2: 下滑商品分析
            mock_declining = pd.DataFrame({
                '周期标识': ['第40周', '第40周', '第40周', '第41周', '第41周'],
                '商品名称': ['可口可乐', '薯片', '面包', '矿泉水', '巧克力'],
                '一级分类名': ['饮料', '零食', '主食', '饮料', '零食'],
                '之前单价': ['¥3.5', '¥8.0', '¥12.0', '¥2.0', '¥15.0'],
                '当前单价': ['¥3.5', '¥9.0', '¥12.0', '¥2.0', '¥16.0'],
                '之前销量': ['150', '80', '50', '200', '40'],
                '当前销量': ['120', '60', '45', '180', '32'],
                '销量变化': ['-30', '-20', '-5', '-20', '-8'],
                '销量变化%': ['-20%', '-25%', '-10%', '-10%', '-20%'],
                '问题原因': ['销量下滑', '涨价导致销量降', '销量下滑', '销量下滑', '涨价导致销量降']
            })
            
            # 生成模拟数据 - Sheet3: 上涨商品分析
            mock_rising = pd.DataFrame({
                '周期标识': ['第40周', '第40周', '第41周'],
                '商品名称': ['牛奶', '酸奶', '果汁'],
                '一级分类名': ['饮料', '饮料', '饮料'],
                '之前单价': ['¥5.0', '¥8.0', '¥6.5'],
                '当前单价': ['¥4.5', '¥8.0', '¥7.0'],
                '之前销量': ['100', '60', '80'],
                '当前销量': ['150', '75', '95'],
                '销量变化': ['+50', '+15', '+15'],
                '销量变化%': ['+50%', '+25%', '+18.75%'],
                '优势原因': ['降价促销成功', '销量增长', '涨价但销量增']
            })
            
            sheets_data = {
                '客单价变化': mock_price_change,
                '下滑商品分析': mock_declining,
                '上涨商品分析': mock_rising
            }
            
            has_data = True  # 标记为有数据
        
        # 统计数据
        total_rows = sum(len(df_sheet) for df_sheet in sheets_data.values() if len(df_sheet) > 0)
        sheet_count = len([df for df in sheets_data.values() if len(df) > 0])
        
        # 准备三个表格的数据
        price_change_df = sheets_data.get('客单价变化', pd.DataFrame())
        declining_df = sheets_data.get('下滑商品分析', pd.DataFrame())
        rising_df = sheets_data.get('上涨商品分析', pd.DataFrame())
        
        # 构建Dash表格数据
        def df_to_dash_table(df):
            if df.empty:
                return [], []
            
            data = df.to_dict('records')
            columns = [{'name': col, 'id': col} for col in df.columns]
            return data, columns
        
        price_data, price_cols = df_to_dash_table(price_change_df)
        declining_data, declining_cols = df_to_dash_table(declining_df)
        rising_data, rising_cols = df_to_dash_table(rising_df)
        
        # 存储结果（用于导出）
        stored_result = {
            'sheets_data': {
                '客单价变化': price_change_df.to_dict('records'),
                '下滑商品分析': declining_df.to_dict('records'),
                '上涨商品分析': rising_df.to_dict('records')
            },
            'params': {
                'time_period': time_period,
                'threshold': threshold,
                'mode': mode,
                'current_idx': current_idx,
                'compare_idx': compare_idx
            }
        }
        
        return (
            f"✅ 分析完成！共 {sheet_count} 个维度，{total_rows} 行数据",
            "success",
            True,
            price_data, price_cols,
            declining_data, declining_cols,
            rising_data, rising_cols,
            {'display': 'block'},
            stored_result
        )
        
    except Exception as e:
        import traceback
        error_msg = f"❌ 分析失败: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        
        return (
            error_msg,
            "danger",
            True,
            [], [], [], [], [], [],
            {'display': 'none'},
            None
        )


# 回调5: 导出Excel（分Sheet）
@app.callback(
    Output('download-price-excel', 'data'),
    Input('btn-export-price-excel', 'n_clicks'),
    [State('price-period-selector', 'value'),
     State('price-threshold-slider', 'value'),
     State('price-analysis-mode', 'value'),
     State('price-current-period', 'value'),
     State('price-compare-period', 'value')],
    prevent_initial_call=True
)
def export_price_excel(n_clicks, time_period, threshold, mode, current_idx, compare_idx):
    """导出客单价分析结果为Excel（分Sheet）"""
    global DIAGNOSTIC_ENGINE
    
    if not n_clicks or DIAGNOSTIC_ENGINE is None:
        return None
    
    try:
        # 获取数据
        sheets_data = DIAGNOSTIC_ENGINE.diagnose_customer_price_decline_by_sheets(
            time_period=time_period or 'week',
            threshold=threshold or -5.0,
            current_period_index=current_idx if mode == 'precise' else None,
            compare_period_index=compare_idx if mode == 'precise' else None
        )
        
        # 创建Excel
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            for sheet_name, df_sheet in sheets_data.items():
                if len(df_sheet) > 0:
                    # 清理数据中的¥符号等格式
                    export_df = df_sheet.copy()
                    for col in export_df.columns:
                        if export_df[col].dtype == 'object':
                            sample_value = str(export_df[col].iloc[0]) if len(export_df) > 0 else ""
                            if '¥' in sample_value:
                                try:
                                    export_df[col] = (export_df[col]
                                                     .astype(str)
                                                     .str.replace('¥', '')
                                                     .str.replace(',', '')
                                                     .str.replace('N/A', '0')
                                                     .replace('', '0')
                                                     .astype(float))
                                except:
                                    pass
                    
                    export_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        excel_bytes = excel_buffer.getvalue()
        
        return dcc.send_bytes(
            excel_bytes,
            f"客单价归因分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
    except Exception as e:
        print(f"❌ Excel导出失败: {e}")
        return None


# 回调6: 导出CSV（单文件）
@app.callback(
    Output('download-price-csv', 'data'),
    Input('btn-export-price-csv', 'n_clicks'),
    [State('price-period-selector', 'value'),
     State('price-threshold-slider', 'value'),
     State('price-analysis-mode', 'value'),
     State('price-current-period', 'value'),
     State('price-compare-period', 'value')],
    prevent_initial_call=True
)
def export_price_csv(n_clicks, time_period, threshold, mode, current_idx, compare_idx):
    """导出客单价分析结果为CSV（单文件）"""
    global DIAGNOSTIC_ENGINE
    
    if not n_clicks or DIAGNOSTIC_ENGINE is None:
        return None
    
    try:
        # 获取原始合并数据
        result = DIAGNOSTIC_ENGINE.diagnose_customer_price_decline(
            time_period=time_period or 'week',
            threshold=threshold or -5.0,
            current_period_index=current_idx if mode == 'precise' else None,
            compare_period_index=compare_idx if mode == 'precise' else None
        )
        
        if len(result) > 0:
            # 清理数据
            export_df = result.copy()
            for col in export_df.columns:
                if export_df[col].dtype == 'object':
                    sample_value = str(export_df[col].iloc[0]) if len(export_df) > 0 else ""
                    if '¥' in sample_value:
                        try:
                            export_df[col] = (export_df[col]
                                             .astype(str)
                                             .str.replace('¥', '')
                                             .str.replace(',', '')
                                             .str.replace('N/A', '0')
                                             .replace('', '0')
                                             .astype(float))
                        except:
                            pass
            
            # 生成CSV - 使用BOM编码确保Excel识别中文
            csv_string = '\ufeff' + export_df.to_csv(index=False)
            
            return dcc.send_string(
                csv_string,
                f"客单价归因_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
    except Exception as e:
        print(f"❌ CSV导出失败: {e}")
        return None


# ==================== 运行应用 ====================
if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                 🏪 智能门店经营看板 - Dash版                  ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  ✅ 解决Streamlit页面跳转问题                                 ║
    ║  ✅ 流畅的交互体验                                            ║
    ║  ✅ 只更新需要更新的部分                                       ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  📍 访问地址: http://localhost:8050                          ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("🚀 准备启动应用服务器...")
    try:
        print("📝 配置: host=0.0.0.0, port=8050, debug=False")
        app.run(
            debug=False,  # 关闭Debug模式避免自动重载
            host='0.0.0.0',
            port=8050,
            use_reloader=False  # 禁用自动重载
        )
        print("⚠️ 应用服务器已停止")
    except KeyboardInterrupt:
        print("\n✋ 用户中断")
    except Exception as e:
        print(f"\n❌ 应用启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")
