#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
门店诊断看板(订单数据)
启动命令: python "智能门店看板_Dash版.py"
访问地址: http://localhost:8050
"""
import base64
import io
import json
import os
import re
import sys
import warnings
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

# ⚡ 解决 Windows PowerShell 下 emoji 输出乱码问题 - 必须在任何print之前设置
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Input, Output, State, dash_table, callback_context, no_update
from dash.dependencies import ALL, MATCH
from dash.exceptions import PreventUpdate

# 尝试导入 dash_echarts，如果失败则使用 Plotly 作为后备方案
try:
    from dash_echarts import DashECharts
    ECHARTS_AVAILABLE = True
    print("✅ ECharts 可用，将使用 ECharts 图表")
    
    # dash-echarts 0.0.12.x 版本直接支持字符串形式的 JS 函数
    # 不需要 JsCode 包装，创建一个兼容类以保持代码一致性
    class JsCode:
        """兼容包装类，dash-echarts 直接支持字符串JS代码"""
        def __init__(self, code):
            self.js_code = code
            
except ImportError:
    ECHARTS_AVAILABLE = False
    # 定义一个兼容的 JsCode 类
    class JsCode:
        def __init__(self, code):
            self.js_code = code
    print("⚠️ dash-echarts 未安装，将使用 Plotly 图表作为后备方案")
    print("   提示：运行 'pip install dash-echarts' 以获得更好的图表效果")

# 🎨 导入 Mantine UI 组件库
try:
    import dash_mantine_components as dmc
    from dash_iconify import DashIconify
    MANTINE_AVAILABLE = True
    print("✅ Mantine UI 可用，将使用现代化卡片组件")
except ImportError:
    MANTINE_AVAILABLE = False
    print("⚠️ dash-mantine-components 未安装，将使用Bootstrap卡片")
    print("   提示：运行 'pip install dash-mantine-components dash-iconify' 以获得更好的UI效果")

# 🎨 导入ECharts统一配置（仅当ECharts可用时）
if ECHARTS_AVAILABLE:
    try:
        from echarts_factory import (
            COMMON_COLORS, COMMON_ANIMATION, COMMON_TOOLTIP, COMMON_LEGEND,
            COMMON_GRID, COMMON_TITLE, COMMON_AXIS_LABEL, COMMON_SPLIT_LINE,
            format_number,
            create_metric_bar_card, create_gauge_card  # 🎨 卡片工厂函数
        )
        print("✅ ECharts统一配置已加载（8种配色×5级梯度）")
        print("✅ ECharts卡片工厂函数已加载")
    except ImportError as e:
        print(f"⚠️ ECharts配置导入失败: {e}")
        # 如果导入失败，定义空字典避免报错
        COMMON_COLORS = COMMON_ANIMATION = COMMON_TOOLTIP = COMMON_LEGEND = {}
        COMMON_GRID = COMMON_TITLE = COMMON_AXIS_LABEL = COMMON_SPLIT_LINE = {}
        format_number = lambda x: x
        create_metric_bar_card = create_gauge_card = None

warnings.filterwarnings('ignore')

# 应用目录及模块导入路径
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

# 🎨 导入统一组件样式库
try:
    from component_styles import (
        create_card, create_stat_card, create_alert, create_badge,
        create_metric_row, create_info_card, create_comparison_badge,
        create_data_info_header, create_loading_card, create_error_card,
        create_success_card, create_warning_card
    )
    COMPONENT_STYLES_AVAILABLE = True
    print("✅ 统一组件样式库已加载")
except ImportError as e:
    COMPONENT_STYLES_AVAILABLE = False
    print(f"⚠️ 组件样式库加载失败: {e}")
    print("   将使用原始dbc组件")

# 导入商品场景智能打标引擎
try:
    from 商品场景智能打标引擎 import ProductSceneTagger
    SMART_TAGGING_AVAILABLE = True
    print("✅ 商品场景智能打标引擎已加载")
except ImportError as e:
    SMART_TAGGING_AVAILABLE = False
    print(f"⚠️ 商品场景智能打标引擎未找到: {e}")
    print("   部分高级场景分析功能将不可用")

# 导入Tab 5扩展渲染函数
try:
    from tab5_extended_renders import (
        render_heatmap_profit_matrix,
        render_trend_price_analysis,
        render_product_scene_network,
        render_product_scene_profile
    )
    TAB5_EXTENDED_RENDERS_AVAILABLE = True
    print("✅ Tab 5扩展渲染模块已加载")
except ImportError as e:
    TAB5_EXTENDED_RENDERS_AVAILABLE = False
    print(f"⚠️ Tab 5扩展渲染模块未找到: {e}")
    print("   热力图、利润矩阵等高级功能将不可用")

# 业务模块导入
# from 问题诊断引擎 import ProblemDiagnosticEngine  # 已删除，功能已集成
ProblemDiagnosticEngine = None  # 占位，避免引用错误
from 真实数据处理器 import RealDataProcessor

# ✨ 导入Tab 7专用分析器（提前导入避免延迟导入问题）
try:
    from 科学八象限分析器 import ScientificQuadrantAnalyzer
    from 评分模型分析器 import ScoringModelAnalyzer
    TAB7_ANALYZERS_AVAILABLE = True
    print("✅ Tab 7 八象限分析器已加载")
except ImportError as e:
    TAB7_ANALYZERS_AVAILABLE = False
    ScientificQuadrantAnalyzer = None
    ScoringModelAnalyzer = None
    print(f"⚠️ Tab 7 分析器模块未找到: {e}")
    print("   营销成本八象限分析功能将不可用")

# ✨ 导入数据源管理器（支持Excel/数据库双数据源）
try:
    # ⚠️ 在导入任何数据库模块前，先确保 platform_service_fee 字段存在
    try:
        from database.add_platform_service_fee_field import ensure_platform_service_fee_column
        ensure_platform_service_fee_column()
    except Exception as field_check_err:
        print(f"⚠️ 自动检查 platform_service_fee 字段失败: {field_check_err}")
    
    from database.data_source_manager import DataSourceManager
    DATABASE_AVAILABLE = True
    print("✅ 数据库数据源已启用")
    
    # 初始化时获取门店列表
    def get_initial_store_options():
        """获取初始门店列表用于下拉框"""
        try:
            from database.connection import engine
            from sqlalchemy import text
            
            with engine.connect() as conn:
                query = text("SELECT DISTINCT store_name FROM orders ORDER BY store_name")
                results = conn.execute(query).fetchall()
            
            options = [{'label': r[0], 'value': r[0]} for r in results if r[0]]
            print(f"✅ 已预加载 {len(options)} 个门店选项")
            for i, opt in enumerate(options, 1):
                print(f"   {i}. {opt['label']}")
            return options
        except Exception as e:
            print(f"⚠️ 预加载门店列表失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    INITIAL_STORE_OPTIONS = get_initial_store_options()
    
except ImportError as e:
    DATABASE_AVAILABLE = False
    DataSourceManager = None
    INITIAL_STORE_OPTIONS = []
    print(f"⚠️ 数据库模块未找到: {e}")
    print("   仅支持Excel数据源")

# ✨ 导入AI分析器模块（专注于数据洞察和策略建议）
from ai_analyzer import get_ai_analyzer

# ✨ 导入AI业务上下文模块（标准化业务逻辑 + 阶段1优化）
try:
    from ai_business_context import (
        get_health_warnings,
        BUSINESS_CONTEXT,
        get_analysis_prompt,
        FEW_SHOT_EXAMPLES,
        COT_TEMPLATE,
        DATA_VALIDATION_RULES
    )
    BUSINESS_CONTEXT_AVAILABLE = True
    print("✅ 业务上下文模块已加载 - GLM-4.6 阶段1优化启用")
    print("   ✓ Few-Shot示例库 (3个典型案例)")
    print("   ✓ CoT思维链 (6步分析流程)")
    print("   ✓ 数据验证规则 (刻在基因中)")
except ImportError:
    BUSINESS_CONTEXT_AVAILABLE = False
    print("⚠️ 业务上下文模块未找到,将使用基础AI分析")

# ✨ 导入场景推断工具模块（统一场景推断逻辑）
from scene_inference import (
    add_scene_and_timeslot_fields,
    get_available_scenes,
    get_available_timeslots,
    infer_scene,
    classify_timeslot
)

# ✨ 导入缓存工具模块（优化哈希计算）
from cache_utils import (
    calculate_data_hash_fast,
    save_dataframe_compressed,
    load_dataframe_compressed,
    get_cache_metadata,
    cleanup_old_caches
)

# ✨ 导入Redis缓存管理器（多用户缓存共享）
# 🔴 默认禁用以提升启动速度,如需启用请修改下方ENABLE_REDIS=True
ENABLE_REDIS = True  

REDIS_CACHE_AVAILABLE = False
REDIS_CACHE_MANAGER = None

if ENABLE_REDIS:
    try:
        from redis_cache_manager import (
            RedisCacheManager,
            get_cache_manager,
            cache_dataframe,
            get_cached_dataframe,
            clear_store_cache
        )
        REDIS_CACHE_AVAILABLE = True
        print("✅ Redis缓存模块已加载")
    except Exception as e:
        REDIS_CACHE_AVAILABLE = False
        print(f"⚠️  Redis缓存模块加载失败（将使用本地缓存）: {e}")
else:
    print("ℹ️  Redis已禁用,使用本地文件缓存")

# ✨ 导入响应式工具函数
from echarts_responsive_utils import (
    calculate_chart_height,
    calculate_dynamic_grid,
    get_responsive_font_size,
    create_responsive_echarts_config
)

# ✨ 导入 PandasAI 智能分析模块（GLM-4.6 阶段2）
try:
    from ai_pandasai_integration import (
        SmartDataAnalyzer,
        QUERY_TEMPLATES,
        get_template_query
    )
    PANDAS_AI_MODULE_AVAILABLE = True
    print("✅ PandasAI 智能分析模块已加载 - 阶段2启用")
except ImportError as e:
    PANDAS_AI_MODULE_AVAILABLE = False
    print(f"⚠️ PandasAI 模块未找到: {e}")
    print("   自然语言数据洞察功能暂不可用")

# ✨ 导入 RAG 向量知识库模块（GLM-4.6 阶段3）- 暂时禁用避免下载模型
RAG_MODULE_AVAILABLE = False
VectorKnowledgeBase = None
RAGAnalyzer = None
init_default_knowledge_base = None
print("ℹ️ RAG 向量知识库模块已暂时禁用（避免下载模型）")

# 原始导入代码（需要时取消注释）
# try:
#     from ai_rag_knowledge_base import (
#         VectorKnowledgeBase,
#         RAGAnalyzer,
#         init_default_knowledge_base
#     )
#     RAG_MODULE_AVAILABLE = True
#     print("✅ RAG 向量知识库模块已加载 - 阶段3启用")
# except ImportError as e:
#     RAG_MODULE_AVAILABLE = False
#     print(f"⚠️ RAG 知识库模块未找到: {e}")
#     print("   历史案例检索与RAG增强分析暂不可用")
# except OSError as e:
#     # Torch DLL 加载失败时优雅降级
#     RAG_MODULE_AVAILABLE = False
#     if "DLL" in str(e) or "1114" in str(e):
#         print("⚠️ RAG 模块依赖的 Torch DLL 加载失败")
#         print("   解决方案: 安装 Visual C++ Redistributable")
#         print("   下载: https://aka.ms/vs/17/release/vc_redist.x64.exe")
#         print("   或执行: pip uninstall torch -y && pip install torch --index-url https://download.pytorch.org/whl/cpu")
#     else:
#         print(f"⚠️ RAG 模块加载失败: {e}")
#     print("   阶段3功能暂不可用，阶段1/2功能不受影响")

# ⭐ 关键业务规则：需要剔除的渠道（咖啡业务非O2O零售核心，与Streamlit保持一致）
CHANNELS_TO_REMOVE = ['饿了么咖啡', '美团咖啡']

# 统一利润/配送计算口径配置
CALCULATION_MODES = {
    'service_fee_positive': {
        'label': '仅平台服务费>0',
        'description': '仅统计平台服务费>0的订单（剔除平台服务费=0的订单）'
    },
    'all_no_fallback': {
        'label': '全量（仅平台服务费）',
        'description': '仅使用平台服务费字段，剔除平台服务费=0的订单'
    },
    'all_with_fallback': {
        'label': '全量（服务费+佣金兜底）（默认）',
        'description': '平台服务费<=0时使用平台佣金兜底，但最终必须>0才计入'
    }
}

DEFAULT_CALCULATION_MODE = 'all_with_fallback'  # ✅ 全量模式(兜底逻辑): 平台服务费<=0时使用平台佣金,但最终必须>0才计入


def normalize_calc_mode(mode: Optional[str]) -> str:
    """将外部传入的计算口径值规范化为受支持的枚举。"""
    if not mode:
        return DEFAULT_CALCULATION_MODE
    return mode if mode in CALCULATION_MODES else DEFAULT_CALCULATION_MODE


def serialize_order_agg_cache(df: pd.DataFrame, calc_mode: str) -> Dict[str, Any]:
    """序列化订单聚合数据并附带计算口径，便于缓存复用。"""
    return {
        'mode': normalize_calc_mode(calc_mode),
        'data': df.to_dict('records')
    }


def deserialize_order_agg_cache(payload: Any) -> (Optional[pd.DataFrame], Optional[str]):
    """从缓存结构中还原DataFrame与计算口径。兼容旧版本列表结构。"""
    if not payload:
        return None, None
    if isinstance(payload, dict) and 'data' in payload:
        return pd.DataFrame(payload['data']), payload.get('mode')
    if isinstance(payload, list):
        return pd.DataFrame(payload), None
    return None, None


def build_calc_mode_selector() -> dbc.Card:
    """构建全局计算口径选择器组件。"""
    options = [
        {'label': info['label'], 'value': mode_key}
        for mode_key, info in CALCULATION_MODES.items()
    ]
    descriptions = html.Ul([
        html.Li(f"{info['label']}：{info['description']}")
        for info in CALCULATION_MODES.values()
    ], className="text-muted small mb-0")

    return dbc.Card([
        dbc.CardHeader([
            html.Span("📐 计算口径", className="fw-bold me-2"),
            html.Small("影响利润额与配送净成本的统计范围")
        ]),
        dbc.CardBody([
            dcc.Dropdown(
                id='calc-mode-dropdown',
                options=options,
                value=DEFAULT_CALCULATION_MODE,
                clearable=False,
                persistence=True,
                style={'width': '100%'}
            ),
            html.Div(descriptions, className="mt-3")
        ])
    ], className="mb-3 shadow-sm")


def build_data_source_card() -> dbc.Card:
    """构建数据库/文件数据源选择组件，供不同布局复用。"""

    database_tab = (html.Div([
        dbc.Alert([
            html.I(className="bi bi-database me-2"),
            "从PostgreSQL数据库加载订单数据"
        ], color="primary", className="mb-3 mt-3"),

        dbc.Row([
            dbc.Col([
                html.Label("🏪 选择门店:"),
                dcc.Dropdown(
                    id='db-store-filter',
                    placeholder='全部门店',
                    clearable=True
                )
            ], md=4),
            dbc.Col([
                html.Label("📅 统计日期:"),
                dcc.DatePickerRange(
                    id='db-date-range',
                    display_format='YYYY-MM-DD',
                    start_date_placeholder_text='开始日期',
                    end_date_placeholder_text='结束日期',
                    clearable=True,
                    with_portal=True,
                    number_of_months_shown=1,
                    first_day_of_week=1,
                    month_format='YYYY年MM月',
                    show_outside_days=True,
                    minimum_nights=0,
                    style={'width': '100%', 'fontSize': '14px'}
                )
            ], md=5),
            dbc.Col([
                html.Label(html.Br()),
                dbc.Button(
                    [html.I(className="bi bi-download me-1"), "加载数据"],
                    id='load-from-database-btn',
                    color="primary",
                    className="w-100"
                )
            ], md=2),
            dbc.Col([
                html.Label(html.Br()),
                dbc.Button(
                    "🔄",
                    id='refresh-cache-btn',
                    color="secondary",
                    outline=True,
                    title="刷新数据范围缓存",
                    className="w-100",
                    style={'fontSize': '18px'}
                )
            ], md=1)
        ], className="mb-3"),

        html.Div(id='cache-status-alert', className="mb-3"),

        dbc.Row([
            dbc.Col([
                html.Label("📆 快捷选择:", className="me-2"),
                dbc.ButtonGroup([
                    dbc.Button("昨日", id='quick-date-yesterday', size="sm", outline=True, color="secondary"),
                    dbc.Button("今日", id='quick-date-today', size="sm", outline=True, color="secondary"),
                    dbc.Button("上周", id='quick-date-last-week', size="sm", outline=True, color="secondary"),
                    dbc.Button("本周", id='quick-date-this-week', size="sm", outline=True, color="secondary"),
                    dbc.Button("上月", id='quick-date-last-month', size="sm", outline=True, color="secondary"),
                    dbc.Button("本月", id='quick-date-this-month', size="sm", outline=True, color="secondary"),
                    dbc.Button("过去7天", id='quick-date-last-7days', size="sm", outline=True, color="secondary"),
                    dbc.Button("过去30天", id='quick-date-last-30days', size="sm", outline=True, color="secondary"),
                ], size="sm")
            ], md=12)
        ], className="mb-3"),

        html.Div(id='database-stats'),

        dcc.Loading(
            id="loading-database-data",
            type="circle",
            color="#667eea",
            children=[html.Div(id='database-load-status', className="mt-3")],
            fullscreen=False,
            style={'marginTop': '20px'}
        )
    ], className="p-3") if DATABASE_AVAILABLE else html.Div([
        dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            "数据库功能未启用。请安装必要的依赖： pip install psycopg2-binary sqlalchemy"
        ], color="warning", className="mt-3")
    ]))

    upload_tab = html.Div([
        dbc.Alert([
            html.I(className="bi bi-info-circle me-2"),
            html.Div([
                html.Strong("💾 数据将自动保存到数据库"),
                html.Br(),
                html.Small([
                    "上传的数据会自动导入PostgreSQL数据库，",
                    "支持多人共享访问，下次可直接从数据库加载。",
                    html.Br(),
                    html.Span("⚠️ 如果门店已存在数据，将自动覆盖。", className="text-warning fw-bold")
                ])
            ])
        ], color="primary", className="mb-3" if DATABASE_AVAILABLE else "d-none"),

        dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            html.Div([
                html.Strong("⚠️ 数据库功能未启用"),
                html.Br(),
                html.Small("上传的数据仅供临时分析，不会保存到数据库。如需持久化存储，请安装数据库依赖。")
            ])
        ], color="warning", className="mb-3" if not DATABASE_AVAILABLE else "d-none"),

        dcc.Upload(
            id='upload-data',
            children=html.Div([
                html.I(className="bi bi-cloud-upload", style={'fontSize': '3rem', 'color': '#667eea'}),
                html.Br(),
                html.B('拖拽文件到这里 或 点击选择文件', style={'fontSize': '1.1rem', 'marginTop': '10px'}),
                html.Br(),
                html.Span('支持 .xlsx / .xls 格式，可同时上传多个文件',
                         style={'fontSize': '0.9rem', 'color': '#666', 'marginTop': '5px'}),
                html.Br(),
                html.Span('💾 数据将自动保存到数据库，支持多人共享访问',
                         style={'fontSize': '0.85rem', 'color': '#667eea', 'marginTop': '5px', 'fontWeight': 'bold'}) if DATABASE_AVAILABLE else ""
            ]),
            style={
                'width': '100%',
                'height': '150px',
                'lineHeight': '150px',
                'borderWidth': '2px',
                'borderStyle': 'dashed',
                'borderRadius': '10px',
                'borderColor': '#667eea',
                'textAlign': 'center',
                'background': '#f8f9ff',
                'cursor': 'pointer',
                'transition': 'all 0.3s'
            },
            multiple=True
        ),
        
        # 上传状态显示（带加载动画）
        dcc.Loading(
            id="upload-loading",
            type="circle",  # circle 动画效果
            color="#667eea",
            children=[
                html.Div(id='upload-status', className="mt-3")
            ],
            className="mt-3"
        ),
        html.Div(id='upload-debug-info', className="text-muted small mt-2"),

        dbc.Accordion([
            dbc.AccordionItem([
                html.Div([
                    html.H6("📋 必需字段：", className="mb-2"),
                    html.Ul([
                        html.Li("订单ID: 订单唯一标识"),
                        html.Li("商品名称: 商品名称"),
                        html.Li("商品实售价: 商品售价"),
                        html.Li("销量: 商品数量"),
                        html.Li("下单时间: 订单时间"),
                        html.Li("门店名称: 门店标识"),
                        html.Li("渠道: 销售渠道（如美团、饿了么）"),
                    ]),
                    html.H6("✨ 推荐字段（用于完整分析）：", className="mb-2 mt-3"),
                    html.Ul([
                        html.Li("物流配送费、平台佣金、配送距离"),
                        html.Li("美团一级分类、美团三级分类"),
                        html.Li("收货地址、配送费减免、满减、商品减免、代金券"),
                        html.Li("用户支付配送费、订单零售额、打包费"),
                    ])
                ])
            ], title="📋 订单数据格式要求")
        ], start_collapsed=True, className="mt-3")
    ], className="p-3")

    data_manage_tab = (html.Div([
        dbc.Alert([
            html.I(className="bi bi-info-circle me-2"),
            html.Div([
                html.Strong("📊 数据库空间管理"),
                html.Br(),
                html.Small("定期清理历史数据，释放数据库空间，优化看板性能")
            ])
        ], color="info", className="mb-3 mt-3"),

        html.Div(id='db-management-stats', className="mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="bi bi-shop me-2"),
                        html.Strong("按门店清理")
                    ]),
                    dbc.CardBody([
                        html.Label("选择要清理的门店:", className="fw-bold mb-2"),
                        dbc.Select(
                            id='cleanup-store-select',
                            placeholder='选择门店',
                            options=[{'label': opt['label'], 'value': opt['value']} for opt in (INITIAL_STORE_OPTIONS if DATABASE_AVAILABLE else [])],
                            className="mb-3"
                        ),
                        dbc.Button([
                            html.I(className="bi bi-info-circle me-1"), "查看门店数据"
                        ], id='preview-store-data-btn', color="info", className="w-100 mb-2"),
                        dbc.Button([
                            html.I(className="bi bi-trash3 me-1"), "删除门店数据"
                        ], id='delete-store-btn', color="danger", className="w-100")
                    ])
                ], className="mb-3")
            ], md=12),
        ]),

        html.Div(id='cleanup-result', className="mt-3"),

        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6([
                            html.I(className="bi bi-speedometer2 me-2"),
                            "数据库优化"
                        ], className="mb-0"),
                        html.Small("清理空间碎片，重建索引，提升性能", className="text-muted")
                    ], md=8),
                    dbc.Col([
                        dbc.Button([
                            html.I(className="bi bi-gear me-1"), "优化数据库"
                        ], id='optimize-database-btn', color="success", className="w-100")
                    ], md=4)
                ])
            ])
        ], className="mt-3")
    ], className="p-3") if DATABASE_AVAILABLE else html.Div([
        dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            "数据库功能未启用"
        ], color="warning", className="mt-3")
    ]))

    tabs_children = [
        dcc.Tab(label='🗄️ 数据库数据', value='database-data', children=[database_tab]),
        dcc.Tab(label='📤 上传新数据', value='upload-data', children=[upload_tab]),
        dcc.Tab(label='🗂️ 数据管理', value='data-management', children=[data_manage_tab])
    ]

    return dbc.Card([
        dbc.CardHeader([
            html.H4("📂 数据源选择", className="mb-0 d-inline-block"),
            html.Span(" | 当前数据: ", className="ms-3 text-muted small"),
            html.Span(id='current-data-label', children="数据库数据", className="text-primary small fw-bold")
        ]),
        dbc.CardBody([
            dcc.Tabs(id='data-source-tabs', value='database-data', children=tabs_children)
        ])
    ], className="mb-4")

# 缓存目录
CACHE_DIR = APP_DIR / "学习数据仓库" / "uploaded_data"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Dash 应用初始化
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'}]
)
app.title = "门店诊断看板(订单数据)"
server = app.server
server.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB 上传限制

# ============================================================================
# 注意：app.index_string的定义在line 2039（唯一定义）
# 包含完整的.modern-card CSS样式，确保悬停动画正常工作
# ============================================================================
# 全局数据容器
GLOBAL_DATA = None  # 当前筛选后的数据
GLOBAL_FULL_DATA = None  # 数据库完整数据(用于环比计算)
DIAGNOSTIC_ENGINE = None
UPLOADED_DATA_CACHE = None
DATA_SOURCE_MANAGER = None  # 数据源管理器实例

# ✅ Redis缓存管理器实例（多用户共享）
REDIS_CACHE_MANAGER = None
if REDIS_CACHE_AVAILABLE:
    try:
        REDIS_CACHE_MANAGER = get_cache_manager(
            host='localhost',
            port=6379,
            db=0,
            default_ttl=1800  # 默认30分钟
        )
        if REDIS_CACHE_MANAGER.enabled:
            print("✅ Redis缓存已启用 - 支持多用户数据共享")
            print(f"📊 缓存配置: TTL=30分钟, 自动过期")
        else:
            print("⚠️  Redis连接失败，将使用本地缓存")
            REDIS_CACHE_MANAGER = None
    except Exception as e:
        print(f"⚠️  Redis初始化失败: {e}")
        REDIS_CACHE_MANAGER = None

# ✅ 新增：存储用户查询的日期范围（优化缓存机制）
QUERY_DATE_RANGE = {
    'start_date': None,
    'end_date': None,
    'db_min_date': None,  # 数据库完整日期范围的最小值
    'db_max_date': None,   # 数据库完整日期范围的最大值
    'cache_timestamp': None,  # 缓存时间戳
    'cache_store': None  # 缓存的门店名称
}

# 阶段2/阶段3 AI 智能助手全局实例
PANDAS_AI_ANALYZER = None
PANDAS_AI_TEMPLATES: Dict[str, str] = {}
VECTOR_KB_INSTANCE = None
RAG_ANALYZER_INSTANCE = None

PANDAS_TEMPLATE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "高利润商品": {"threshold": 20, "top_n": 10},
    "低客单价订单": {"threshold": 25},
    "滞销商品": {"days": 30},
    "时段销量分析": {},
    "场景营销效果": {},
    "商品角色分布": {},
    "成本结构分析": {},
    "营销ROI排名": {"top_n": 10}
}


def load_real_business_data():
    """加载真实业务数据（使用标准化处理器）"""
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
        print(f"📊 原始数据加载: {len(df)} 行 × {len(df.columns)} 列")
        print(f"📋 原始字段: {list(df.columns)[:10]}...")

        # ⭐ 使用真实数据处理器标准化（关键步骤）
        processor = RealDataProcessor()
        df_standardized = processor.standardize_sales_data(df)

        print(f"✅ 数据标准化完成: {len(df_standardized)} 行")
        print(f"📊 标准化字段: {list(df_standardized.columns)[:10]}...")

        # 检查关键字段
        required_fields = ['商品名称', '商品实售价', '日期']
        missing_fields = [f for f in required_fields if f not in df_standardized.columns]

        if missing_fields:
            print(f"⚠️ 缺失关键字段: {missing_fields}")
        else:
            print(f"✅ 关键字段验证通过")

        # 🆕 使用统一的场景推断模块
        df_standardized = add_scene_and_timeslot_fields(df_standardized)

        scenes = get_available_scenes(df_standardized)
        timeslots = get_available_timeslots(df_standardized)

        print(f"✅ 已生成场景和时段字段")
        print(f"   场景选项: {scenes}")
        print(f"   时段选项: {timeslots}")

        return df_standardized

    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return None


def _sanitize_filename(file_name: str) -> str:
    if not file_name:
        return "uploaded_data"
    stem = Path(file_name).stem if file_name else "uploaded_data"
    sanitized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fa5]+", "_", stem).strip("_")
    return sanitized or "uploaded_data"


def save_data_to_cache(df: pd.DataFrame, original_file: str) -> str:
    """保存DataFrame到缓存目录，自动去重并写入元数据"""
    try:
        if df is None or df.empty:
            return "跳过保存：数据为空"

        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        data_hash = calculate_data_hash_fast(df)
        existing = load_cached_data_list()
        for cache_info in existing:
            if cache_info.get('data_hash') == data_hash:
                return f"跳过保存：已存在相同数据 ({cache_info.get('file_name', '未知文件')})"

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = _sanitize_filename(original_file)
        cache_file = CACHE_DIR / f"{safe_name}_{timestamp}_{data_hash[:8]}.pkl.gz"

        metadata = {
            'original_file': original_file,
            'upload_time': datetime.now().isoformat(),
            'rows': int(len(df)),
            'columns': list(df.columns),
            'data_hash': data_hash,
            'file_name': cache_file.name
        }

        payload: Dict[str, Any] = {
            'data': df,
            'metadata': metadata
        }

        size_bytes = save_dataframe_compressed(payload, cache_file)
        metadata['size_mb'] = round(size_bytes / 1024 / 1024, 2) if size_bytes else 0

        # 清理过期缓存，保留最近的12个，最长保留14天
        try:
            cleanup_old_caches(CACHE_DIR, max_age_hours=24 * 14, keep_latest=12)
        except Exception as cleanup_err:
            print(f"⚠️ 清理缓存失败: {cleanup_err}")

        return str(cache_file)

    except Exception as e:
        print(f"❌ 保存缓存失败: {e}")
        return f"保存失败: {e}"


def load_data_from_cache(file_path: str) -> Optional[pd.DataFrame]:
    """从缓存文件加载DataFrame"""
    try:
        path = Path(file_path)
        if not path.exists():
            print(f"⚠️ 缓存文件不存在: {file_path}")
            return None

        payload = load_dataframe_compressed(path)

        if isinstance(payload, dict):
            df = payload.get('data')
            if isinstance(df, pd.DataFrame):
                return df
            if df is not None:
                return pd.DataFrame(df)
        elif isinstance(payload, pd.DataFrame):
            return payload

        print(f"⚠️ 缓存文件格式未知: {file_path}")
        return None

    except Exception as e:
        print(f"❌ 加载缓存失败: {e}")
        return None


def load_cached_data_list() -> List[Dict[str, Any]]:
    """列出缓存目录中的所有历史数据"""
    if not CACHE_DIR.exists():
        return []

    cached_files: List[Dict[str, Any]] = []

    for file_path in sorted(CACHE_DIR.glob("*.pkl.gz"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            payload = load_dataframe_compressed(file_path)
            metadata: Dict[str, Any] = {}
            df: Optional[pd.DataFrame] = None

            if isinstance(payload, dict):
                metadata = payload.get('metadata', {}) or {}
                df_obj = payload.get('data')
                if isinstance(df_obj, pd.DataFrame):
                    df = df_obj
            elif isinstance(payload, pd.DataFrame):
                df = payload

            rows = metadata.get('rows')
            if rows is None and isinstance(df, pd.DataFrame):
                rows = len(df)

            cached_files.append({
                'file_path': str(file_path),
                'file_name': file_path.name,
                'original_file': metadata.get('original_file', file_path.stem),
                'upload_time': metadata.get('upload_time', 'Unknown'),
                'rows': int(rows) if rows is not None else 0,
                'size_mb': round(file_path.stat().st_size / 1024 / 1024, 2),
                'data_hash': metadata.get('data_hash', ''),
            })

        except Exception as e:
            print(f"⚠️ 读取缓存文件失败: {file_path.name} - {e}")
            continue

    return cached_files


def process_uploaded_excel(contents, filename):
    """
    处理上传的Excel文件
    
    Args:
        contents: base64编码的文件内容
        filename: 文件名
        
    Returns:
        处理后的DataFrame或None
    """
    import base64
    
    import base64

    try:
        # 解码base64内容
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        file_suffix = Path(filename).suffix.lower()
        buffer = BytesIO(decoded)

        if file_suffix in {'.xlsx', '.xls', '.xlsm', '.xlsb'}:
            df = pd.read_excel(buffer)
        elif file_suffix == '.csv':
            # 尝试常见编码读取CSV
            for encoding in ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']:
                buffer.seek(0)
                try:
                    df = pd.read_csv(buffer, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("CSV 文件无法解码（尝试编码: utf-8-sig / utf-8 / gbk / gb2312）")
        else:
            raise ValueError(f"不支持的文件类型: {file_suffix or '（无后缀）'}")

        print(f"📖 成功读取文件: {filename} ({len(df):,}行 × {len(df.columns)}列)")

        # 保存到缓存
        save_data_to_cache(df, filename)

        return df

    except Exception as e:
        print(f"❌ 读取文件 {filename} 失败: {str(e)}")
        return None


def initialize_data():
    """初始化数据和诊断引擎"""
    global GLOBAL_DATA, DIAGNOSTIC_ENGINE, DATA_SOURCE_MANAGER
    
    # 初始化数据源管理器
    if DATABASE_AVAILABLE and DATA_SOURCE_MANAGER is None:
        try:
            DATA_SOURCE_MANAGER = DataSourceManager()
            print("✅ 数据源管理器已初始化", flush=True)
        except Exception as e:
            print(f"⚠️ 数据源管理器初始化失败: {e}", flush=True)
            DATA_SOURCE_MANAGER = None
    
    if GLOBAL_DATA is None:
        print("\n" + "="*80, flush=True)
        print("🔄 正在初始化数据...", flush=True)
        print("="*80, flush=True)
        
        GLOBAL_DATA = load_real_business_data()
        
        if GLOBAL_DATA is not None:
            # ========== 🔍 调试日志：初始加载数据检查 ==========
            print("\n" + "="*80, flush=True)
            print("🔍 [调试] GLOBAL_DATA 初始加载完成", flush=True)
            print(f"📊 数据量: {len(GLOBAL_DATA)} 行", flush=True)
            print(f"📋 字段数量: {len(GLOBAL_DATA.columns)} 列", flush=True)
            
            if '商品采购成本' in GLOBAL_DATA.columns:
                print(f"\n✅ '商品采购成本' 字段存在", flush=True)
                print(f"   数据类型: {GLOBAL_DATA['商品采购成本'].dtype}", flush=True)
                print(f"   总和: ¥{GLOBAL_DATA['商品采购成本'].sum():,.2f}", flush=True)
                print(f"   非零数量: {(GLOBAL_DATA['商品采购成本'] > 0).sum()} / {len(GLOBAL_DATA)}", flush=True)
                print(f"   NaN数量: {GLOBAL_DATA['商品采购成本'].isna().sum()}", flush=True)
            else:
                print(f"\n❌ '商品采购成本' 字段不存在！", flush=True)
            print("="*80 + "\n", flush=True)
            
            # ⭐ 关键业务规则1：剔除耗材数据（购物袋等）
            # 识别标准：一级分类名 == '耗材'
            # 参考：订单数据业务逻辑确认.md、业务逻辑最终确认.md
            original_rows = len(GLOBAL_DATA)
            category_col = None
            for col_name in ['一级分类名', '美团一级分类', '一级分类']:
                if col_name in GLOBAL_DATA.columns:
                    category_col = col_name
                    break
            
            if category_col:
                GLOBAL_DATA = GLOBAL_DATA[GLOBAL_DATA[category_col] != '耗材'].copy()
                removed_consumables = original_rows - len(GLOBAL_DATA)
                if removed_consumables > 0:
                    print(f"🔴 已剔除耗材数据: {removed_consumables:,} 行 (购物袋等，一级分类='耗材')", flush=True)
                    print(f"📊 剔除耗材后数据量: {len(GLOBAL_DATA):,} 行", flush=True)
            else:
                print(f"⚠️ 未找到一级分类列，无法剔除耗材数据", flush=True)
            
            # ⭐ 关键业务规则2：标记咖啡渠道数据（仅在渠道对比中隐藏）
            if '渠道' in GLOBAL_DATA.columns:
                coffee_rows = GLOBAL_DATA['渠道'].isin(CHANNELS_TO_REMOVE).sum()
                if coffee_rows > 0:
                    print(
                        f"☕ 监测到咖啡渠道数据: {coffee_rows:,} 行 (将在渠道表现对比中隐藏: {CHANNELS_TO_REMOVE})",
                        flush=True
                    )
            
            # ⭐ 使用统一的场景推断模块（替代重复代码）
            GLOBAL_DATA = add_scene_and_timeslot_fields(GLOBAL_DATA)
            
            scenes = get_available_scenes(GLOBAL_DATA)
            timeslots = get_available_timeslots(GLOBAL_DATA)
            
            print(f"✅ 已智能生成场景和时段字段")
            print(f"   场景选项: {scenes}")
            print(f"   时段选项: {timeslots}")
            
            # ========== 🎯 商品场景智能打标 (在剔除耗材和咖啡后执行) ==========
            if SMART_TAGGING_AVAILABLE:
                print("\n" + "="*80, flush=True)
                print("🎯 执行商品场景智能打标...", flush=True)
                print("="*80, flush=True)
                try:
                    tagger = ProductSceneTagger()
                    GLOBAL_DATA = tagger.tag_product_scenes(GLOBAL_DATA)
                    print(f"   ✅ 打标完成! 添加了扩展场景维度标签", flush=True)
                    print(f"      - 基础场景: {GLOBAL_DATA['场景'].nunique()} 种", flush=True)
                    if '季节场景' in GLOBAL_DATA.columns:
                        print(f"      - 季节场景: {GLOBAL_DATA['季节场景'].nunique()} 种", flush=True)
                    if '节假日场景' in GLOBAL_DATA.columns:
                        print(f"      - 节假日场景: {GLOBAL_DATA['节假日场景'].nunique()} 种", flush=True)
                    if '购买驱动' in GLOBAL_DATA.columns:
                        print(f"      - 购买驱动: {GLOBAL_DATA['购买驱动'].nunique()} 种", flush=True)
                    print("="*80 + "\n", flush=True)
                except Exception as e:
                    print(f"   ⚠️ 智能打标失败: {e}", flush=True)
                    print("   将继续使用基础场景功能", flush=True)
                    print("="*80 + "\n", flush=True)
            
            # ========== 🔍 调试日志：剔除耗材并标记咖啡渠道后的数据检查 ==========
            print("\n" + "="*80)
            print("🔍 [调试] 数据剔除完成")
            print(f"📊 最终数据量: {len(GLOBAL_DATA)} 行")
            
            if '商品采购成本' in GLOBAL_DATA.columns:
                print(f"\n✅ '商品采购成本' 字段仍然存在")
                print(f"   总和: ¥{GLOBAL_DATA['商品采购成本'].sum():,.2f}")
                print(f"   非零数量: {(GLOBAL_DATA['商品采购成本'] > 0).sum()} / {len(GLOBAL_DATA)}")
            else:
                print(f"\n❌ '商品采购成本' 字段丢失！")
            print("="*80 + "\n")
            
            # ========== ✅ 初始化日期范围（修复日期显示问题） ==========
            if '日期' in GLOBAL_DATA.columns:
                GLOBAL_DATA['日期'] = pd.to_datetime(GLOBAL_DATA['日期'], errors='coerce')
                min_date = GLOBAL_DATA['日期'].min()
                max_date = GLOBAL_DATA['日期'].max()
                
                global QUERY_DATE_RANGE
                QUERY_DATE_RANGE['db_min_date'] = min_date
                QUERY_DATE_RANGE['db_max_date'] = max_date
                QUERY_DATE_RANGE['start_date'] = min_date
                QUERY_DATE_RANGE['end_date'] = max_date
                QUERY_DATE_RANGE['cache_timestamp'] = datetime.now()
                
                print(f"📅 数据日期范围: {min_date.strftime('%Y-%m-%d')} 至 {max_date.strftime('%Y-%m-%d')}")
                print(f"   总天数: {(max_date - min_date).days + 1} 天")
                print(f"   唯一日期数: {GLOBAL_DATA['日期'].dt.date.nunique()} 天")
            
            # 诊断引擎已移除
            # print("🔧 正在初始化诊断引擎...")
            # DIAGNOSTIC_ENGINE = ProblemDiagnosticEngine(GLOBAL_DATA)
            # print("✅ 初始化完成！")
            DIAGNOSTIC_ENGINE = None
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
            DIAGNOSTIC_ENGINE = None
    
    return GLOBAL_DATA, DIAGNOSTIC_ENGINE


def initialize_ai_tools():
    """初始化 PandasAI（阶段2）与 RAG 知识库（阶段3）"""
    global PANDAS_AI_ANALYZER, PANDAS_AI_TEMPLATES, VECTOR_KB_INSTANCE, RAG_ANALYZER_INSTANCE

    if PANDAS_AI_MODULE_AVAILABLE and PANDAS_AI_ANALYZER is None:
        try:
            PANDAS_AI_ANALYZER = SmartDataAnalyzer()
            PANDAS_AI_TEMPLATES = dict(QUERY_TEMPLATES)
            print("✅ PandasAI 智能分析器已就绪")
        except Exception as exc:
            PANDAS_AI_ANALYZER = None
            print(f"⚠️ PandasAI 初始化失败: {exc}")
    elif not PANDAS_AI_MODULE_AVAILABLE:
        print("ℹ️ PandasAI 模块不可用，跳过阶段2初始化")

    # 暂时跳过 RAG 模块初始化（避免下载模型）
    if False and RAG_MODULE_AVAILABLE and RAG_ANALYZER_INSTANCE is None:
        try:
            knowledge_dir = APP_DIR / "知识库" / "向量案例库"
            knowledge_dir.mkdir(parents=True, exist_ok=True)
            VECTOR_KB_INSTANCE = VectorKnowledgeBase(str(knowledge_dir))
            stats = VECTOR_KB_INSTANCE.get_stats()
            if stats.get('total_cases', 0) == 0:
                print("ℹ️ 知识库当前为空，自动预填充典型案例…")
                init_default_knowledge_base(VECTOR_KB_INSTANCE)
            api_key = os.getenv('ZHIPU_API_KEY')
            RAG_ANALYZER_INSTANCE = RAGAnalyzer(api_key=api_key, knowledge_base=VECTOR_KB_INSTANCE)
            print("✅ RAG 增强分析器已就绪")
        except Exception as exc:
            RAG_ANALYZER_INSTANCE = None
            print(f"⚠️ RAG 分析器初始化失败: {exc}")
    else:
        print("ℹ️ RAG 模块已跳过，后续可启用")


def get_active_dataframe(data_scope: str, diagnostic_records: Optional[List[Dict[str, Any]]]) -> Optional[pd.DataFrame]:
    """根据用户选择返回副本数据，用于AI分析"""
    if data_scope == 'diagnostic' and diagnostic_records:
        try:
            df = pd.DataFrame(diagnostic_records)
            if not df.empty:
                return df.copy()
        except Exception as exc:
            print(f"⚠️ 将诊断记录转换为DataFrame失败: {exc}")

    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return None
    return GLOBAL_DATA.copy()


def build_business_summary(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """生成业务数据摘要，供RAG分析使用"""
    summary: Dict[str, Any] = {}
    if df is None or df.empty:
        return summary

    revenue_candidates = ['预计订单收入', '订单零售额', '订单实收金额', '实收价格']
    revenue_col = next((col for col in revenue_candidates if col in df.columns), None)
    order_col = next((col for col in ['订单ID', '订单编号', '订单号'] if col in df.columns), None)

    total_sales = 0.0
    order_count = 0
    if revenue_col and order_col:
        order_sales = df.groupby(order_col)[revenue_col].sum()
        total_sales = float(order_sales.sum())
        order_count = int(order_sales.shape[0])
    elif revenue_col:
        total_sales = float(df[revenue_col].sum())
        order_count = int(df[revenue_col].notna().sum())

    if total_sales:
        summary['GMV(¥)'] = total_sales
    if order_count:
        summary['订单数'] = order_count
        if total_sales:
            summary['客单价(¥)'] = total_sales / max(order_count, 1)

    profit_col = next((col for col in ['实际利润', '利润额', '毛利润'] if col in df.columns), None)
    if profit_col:
        summary['利润总额(¥)'] = float(df[profit_col].sum())
    else:
        cost_cols = [col for col in ['商品采购成本', '物流配送费', '平台佣金', '平台服务费', '营销成本', '优惠减免'] if col in df.columns]
        if cost_cols and revenue_col:
            total_cost = float(df[cost_cols].sum(axis=1).sum()) if len(cost_cols) > 1 else float(df[cost_cols[0]].sum())
            summary['成本合计(¥)'] = total_cost
            summary['估算利润(¥)'] = total_sales - total_cost

    if '商品名称' in df.columns:
        summary['SKU数量'] = int(df['商品名称'].nunique())
    if '场景' in df.columns:
        summary['场景数'] = int(df['场景'].nunique())
    if '时段' in df.columns:
        summary['时段数'] = int(df['时段'].nunique())

    if '日期' in df.columns:
        try:
            dates = pd.to_datetime(df['日期'])
            if not dates.isna().all():
                summary['时间范围'] = f"{dates.min():%Y-%m-%d} ~ {dates.max():%Y-%m-%d}"
        except Exception as exc:
            print(f"⚠️ 日期字段解析失败: {exc}")

    return summary


def format_summary_text(summary: Dict[str, Any]) -> str:
    """将摘要字典转为 Markdown 文本"""
    if not summary:
        return ""
    lines: List[str] = []
    for key, value in summary.items():
        if isinstance(value, (int, float)):
            if isinstance(value, int):
                lines.append(f"- {key}: {value:,}")
            else:
                lines.append(f"- {key}: {value:,.2f}")
        else:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines)


# ==================== 环比计算功能 ====================
def calculate_period_comparison(df: pd.DataFrame, start_date: datetime = None, end_date: datetime = None, 
                                store_name: str = None) -> Dict[str, Dict]:
    """
    计算环比数据（支持自动从数据中获取日期范围）
    
    Args:
        df: 完整数据集（需包含当前周期和历史数据）
        start_date: 当前周期开始日期（可选，不传则使用数据中的最小日期）
        end_date: 当前周期结束日期（可选，不传则使用数据中的最大日期）
        store_name: 门店名称（可选）
    
    Returns:
        环比数据字典，包含各指标的环比信息
    """
    try:
        if df is None or len(df) == 0:
            return {}
        
        # 确保日期字段存在且为datetime类型
        date_col = '日期' if '日期' in df.columns else '下单时间'
        if date_col not in df.columns:
            return {}
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 如果没有传入日期范围，使用数据中的日期范围
        if start_date is None:
            start_date = df[date_col].min()
        if end_date is None:
            end_date = df[date_col].max()
        
        # 确保 start_date 和 end_date 是 datetime 对象
        if not isinstance(start_date, datetime):
            start_date = pd.to_datetime(start_date)
        if not isinstance(end_date, datetime):
            end_date = pd.to_datetime(end_date)
        
        # 计算周期长度（天数）
        period_days = (end_date - start_date).days + 1  # +1包含结束日期当天
        
        # 计算上一周期的日期范围
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=period_days - 1)
        
        # 筛选当前周期数据
        current_data = df[
            (df[date_col].dt.date >= start_date.date()) & 
            (df[date_col].dt.date <= end_date.date())
        ].copy()
        
        # 筛选上一周期数据
        prev_data = df[
            (df[date_col].dt.date >= prev_start_date.date()) & 
            (df[date_col].dt.date <= prev_end_date.date())
        ].copy()
        
        # 如果上一周期无数据，返回空字典
        if len(prev_data) == 0:
            print(f"⚠️ 上一周期({prev_start_date.date()}~{prev_end_date.date()})无数据，无法计算环比")
            return {}
        
        print(f"✅ 环比计算: 当前周期({start_date.date()}~{end_date.date()}, {len(current_data)}条)")
        print(f"            上一周期({prev_start_date.date()}~{prev_end_date.date()}, {len(prev_data)}条)")
        
        # 计算关键指标
        def calc_metrics(data):
            """计算指标"""
            if len(data) == 0:
                return {
                    'order_count': 0,
                    'total_sales': 0,
                    'total_profit': 0,
                    'expected_revenue': 0,
                    'avg_order_value': 0,
                    'profit_rate': 0,  # 总利润率
                    'product_count': 0
                }
            
            # ✅ 使用统一的订单聚合函数
            try:
                order_metrics = calculate_order_metrics(data)
            except Exception as e:
                print(f"⚠️ 聚合数据失败: {e}")
                # ✅ 修复:简化版本需要重新计算订单实际利润(使用新公式)
                agg_dict = {
                    '实收价格': 'sum',
                    '利润额': 'sum',  # 商品级字段
                    '物流配送费': 'first',  # 订单级字段
                    '平台佣金': 'first',
                    '平台服务费': 'first',
                }
                
                if '预计订单收入' in data.columns:
                    agg_dict['预计订单收入'] = 'sum'  # 商品级字段
                if '新客减免金额' in data.columns:
                    agg_dict['新客减免金额'] = 'first'  # 订单级字段
                if '企客后返' in data.columns:
                    agg_dict['企客后返'] = 'sum'  # 商品级字段
                    
                # ✅ 使用统一的订单指标计算函数(与全局保持一致)
                # 🔧 环比计算：使用all_with_fallback模式，保留所有订单（包括闪购小程序）
                order_metrics = calculate_order_metrics(data, calc_mode='all_with_fallback')
            
            order_count = len(order_metrics)
            
            # 统一使用实收价格
            total_actual_sales = order_metrics['实收价格'].sum()
            avg_order_value = total_actual_sales / order_count if order_count > 0 else 0
            
            total_profit = order_metrics['订单实际利润'].sum() if '订单实际利润' in order_metrics.columns else 0
            expected_revenue = order_metrics['预计订单收入'].sum() if '预计订单收入' in order_metrics.columns else total_actual_sales
            
            # ✅ 总利润率 = 订单实际利润 / 实收价格（订单实际利润已正确剔除平台服务费=0的订单）
            profit_rate = (total_profit / total_actual_sales * 100) if total_actual_sales > 0 else 0
            
            # 动销商品数
            if '商品名称' in data.columns and '月售' in data.columns:
                product_count = data[data['月售'] > 0]['商品名称'].nunique()
            elif '商品名称' in data.columns:
                product_count = data['商品名称'].nunique()
            else:
                product_count = 0
            
            return {
                'order_count': order_count,
                'actual_sales': total_actual_sales,  # ✅ 修改: 改为实收价格
                'total_profit': total_profit,
                'expected_revenue': expected_revenue,
                'avg_order_value': avg_order_value,
                'profit_rate': profit_rate,  # 总利润率
                'product_count': product_count
            }
        
        current_metrics = calc_metrics(current_data)
        prev_metrics = calc_metrics(prev_data)
        
        # 计算环比变化率
        def calc_change_rate(current, prev):
            """计算变化率"""
            if prev == 0:
                return 999.9 if current > 0 else 0
            return ((current - prev) / prev) * 100
        
        # 为每个指标生成环比数据
        comparison_results = {
            '订单数': {
                'current': current_metrics['order_count'],
                'previous': prev_metrics['order_count'],
                'change_rate': calc_change_rate(current_metrics['order_count'], prev_metrics['order_count']),
                'metric_type': 'positive'
            },
            '商品实收额': {  # ✅ 修改: 预计零售额 → 商品实收额
                'current': current_metrics['actual_sales'],
                'previous': prev_metrics['actual_sales'],
                'change_rate': calc_change_rate(current_metrics['actual_sales'], prev_metrics['actual_sales']),
                'metric_type': 'positive'
            },
            '总利润': {
                'current': current_metrics['total_profit'],
                'previous': prev_metrics['total_profit'],
                'change_rate': calc_change_rate(current_metrics['total_profit'], prev_metrics['total_profit']),
                'metric_type': 'positive'
            },
            '客单价': {
                'current': current_metrics['avg_order_value'],
                'previous': prev_metrics['avg_order_value'],
                'change_rate': calc_change_rate(current_metrics['avg_order_value'], prev_metrics['avg_order_value']),
                'metric_type': 'positive'
            },
            '总利润率': {
                'current': current_metrics['profit_rate'],
                'previous': prev_metrics['profit_rate'],
                'change_rate': current_metrics['profit_rate'] - prev_metrics['profit_rate'],  # 利润率用差值
                'metric_type': 'positive'
            },
            '动销商品数': {
                'current': current_metrics['product_count'],
                'previous': prev_metrics['product_count'],
                'change_rate': calc_change_rate(current_metrics['product_count'], prev_metrics['product_count']),
                'metric_type': 'positive'
            }
        }
        
        return comparison_results
        
    except Exception as e:
        print(f"❌ 环比计算失败: {e}")
        import traceback
        traceback.print_exc()
        return {}


def create_comparison_badge(comparison_data: Dict) -> html.Div:
    """
    创建环比变化徽章（增强版：支持详细提示、重大变化高亮）
    
    Args:
        comparison_data: 环比数据字典，包含:
            - change_rate: 变化率(%)
            - current: 当前值
            - previous: 上期值
            - metric_type: 指标类型('positive'/'negative')
    
    Returns:
        环比显示组件
    """
    if not comparison_data:
        return html.Small(
            html.Span("环比: 无数据", className="text-muted", style={'fontSize': '0.75rem'}),
            className="d-block mt-1",
            title="上一周期无数据,无法计算环比"
        )
    
    if 'change_rate' not in comparison_data:
        return html.Div()
    
    change_value = comparison_data.get('change_rate', 0)
    current_value = comparison_data.get('current', 0)
    previous_value = comparison_data.get('previous', 0)
    metric_type = comparison_data.get('metric_type', 'positive')
    
    if change_value is None or pd.isna(change_value):
        return html.Div()
    
    # 判断是上升还是下降
    is_up = change_value > 0
    
    # 根据指标类型确定颜色
    if metric_type == 'positive':
        color = 'success' if is_up else 'danger'
        icon = '↑' if is_up else '↓'
    else:
        color = 'danger' if is_up else 'success'
        icon = '↑' if is_up else '↓'
    
    # 格式化显示
    if abs(change_value) >= 999:
        change_text = f"{icon} >999%"
    else:
        sign = '+' if is_up else ''
        change_text = f"{icon} {sign}{change_value:.1f}%"
    
    # ✅ 新增:构建详细的Tooltip提示信息
    if current_value != 0 or previous_value != 0:
        # 计算绝对变化值
        abs_change = current_value - previous_value
        abs_change_sign = '+' if abs_change >= 0 else ''
        
        # 格式化数值(根据大小选择格式)
        if abs(current_value) >= 1000:
            current_fmt = f"{current_value:,.0f}"
            previous_fmt = f"{previous_value:,.0f}"
            abs_change_fmt = f"{abs_change_sign}{abs_change:,.0f}"
        else:
            current_fmt = f"{current_value:.2f}"
            previous_fmt = f"{previous_value:.2f}"
            abs_change_fmt = f"{abs_change_sign}{abs_change:.2f}"
        
        tooltip_text = f"当前: {current_fmt} | 上期: {previous_fmt} | 变化: {abs_change_fmt}"
    else:
        tooltip_text = "环比数据"
    
    # ✅ 新增:重大变化高亮(变化率>15%添加脉冲动画)
    is_significant = abs(change_value) > 15
    badge_class = "ms-1"
    if is_significant:
        badge_class += " border border-2"
        # 添加醒目边框
        badge_style = {
            'animation': 'pulse 2s ease-in-out infinite',
            'boxShadow': '0 0 8px rgba(255,193,7,0.6)' if color == 'warning' else 
                         '0 0 8px rgba(220,53,69,0.6)' if color == 'danger' else
                         '0 0 8px rgba(25,135,84,0.6)'
        }
    else:
        badge_style = {}
    
    return html.Small(
        dbc.Badge(
            change_text, 
            color=color, 
            pill=True, 
            className=badge_class,
            style=badge_style,
            title=tooltip_text  # 鼠标悬停显示详细信息
        ),
        className="d-block mt-1"
    )


def calculate_channel_comparison(df: pd.DataFrame, order_agg: pd.DataFrame, 
                                 start_date: datetime = None, end_date: datetime = None) -> Dict[str, Dict]:
    """
    计算各渠道的环比数据
    
    Args:
        df: 原始订单数据(完整数据集,用于查找历史周期)
        order_agg: 当前周期的订单聚合数据(已应用所有业务规则)
        start_date: 当前周期开始日期
        end_date: 当前周期结束日期
    
    Returns:
        {渠道名称: {订单数环比, 销售额环比, 利润环比, 客单价环比}}
    """
    try:
        if df is None or len(df) == 0 or '渠道' not in df.columns:
            return {}
        
        # 确保日期字段
        date_col = '日期' if '日期' in df.columns else '下单时间'
        if date_col not in df.columns:
            return {}
        
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        
        # 自动获取日期范围
        if start_date is None:
            start_date = df[date_col].min()
        if end_date is None:
            end_date = df[date_col].max()
        
        if not isinstance(start_date, datetime):
            start_date = pd.to_datetime(start_date)
        if not isinstance(end_date, datetime):
            end_date = pd.to_datetime(end_date)
        
        # 计算周期长度
        period_days = (end_date - start_date).days + 1
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=period_days - 1)
        
        # 🔍 调试: 输出周期计算信息
        print(f"📅 [渠道环比] 周期计算:")
        print(f"   当前周期: {start_date.date()} ~ {end_date.date()} ({period_days}天)")
        print(f"   上一周期: {prev_start_date.date()} ~ {prev_end_date.date()} ({period_days}天)")
        print(f"   完整数据集行数: {len(df)}")
        
        # ✅ 关键修复: 直接使用传入的order_agg作为当前周期数据(已应用所有过滤规则)
        # 确保order_agg包含渠道信息
        if '渠道' not in order_agg.columns:
            # 从原始数据中获取订单对应的渠道
            from_current_data = df[
                (df[date_col].dt.date >= start_date.date()) & 
                (df[date_col].dt.date <= end_date.date())
            ]
            # 🔴 统一订单ID类型为字符串
            from_current_data['订单ID'] = from_current_data['订单ID'].astype(str)
            order_agg['订单ID'] = order_agg['订单ID'].astype(str)
            
            order_channel = from_current_data.groupby('订单ID')['渠道'].first().reset_index()
            current_order_agg = order_agg.merge(order_channel, on='订单ID', how='left')
        else:
            current_order_agg = order_agg.copy()
        
        # ✅ 使用当前订单聚合数据计算当前周期渠道指标(与卡片显示一致)
        # 🔧 修复：不再硬编码排除闪购小程序和收银机订单，只排除咖啡渠道
        excluded_channels = CHANNELS_TO_REMOVE  # 只排除咖啡渠道
        current_filtered = current_order_agg[~current_order_agg['渠道'].isin(excluded_channels)]
        
        # ✅ 修改：使用'实收价格'替代'商品实售价'
        current_metrics = current_filtered.groupby('渠道').agg({
            '订单ID': 'count',
            '实收价格': 'sum',
            '订单实际利润': 'sum'
        }).reset_index()
        current_metrics.columns = ['渠道', '订单数', '销售额', '总利润']
        current_metrics['客单价'] = current_metrics['销售额'] / current_metrics['订单数']
        # ✅ 利润率 = 订单实际利润 / 销售额（订单实际利润已正确剔除平台服务费=0的订单）
        current_metrics['利润率'] = (current_metrics['总利润'] / current_metrics['销售额'] * 100).fillna(0)
        
        print(f"   📊 当前周期渠道指标(基于order_agg,与卡片一致):", flush=True)
        for _, row in current_metrics.iterrows():
            print(f"      {row['渠道']}: 订单{int(row['订单数'])}单, 销售额¥{row['销售额']:.0f}, 利润¥{row['总利润']:.2f}", flush=True)
        
        # 计算上一周期数据(从完整数据集)
        prev_data = df[
            (df[date_col].dt.date >= prev_start_date.date()) & 
            (df[date_col].dt.date <= prev_end_date.date())
        ].copy()
        
        print(f"   🔍 上一周期筛选结果: {len(prev_data)}行")
        if len(prev_data) > 0 and '渠道' in prev_data.columns:
            print(f"      渠道分布: {prev_data['渠道'].value_counts().to_dict()}")
        
        if len(prev_data) == 0:
            print(f"⚠️ [渠道环比] 上一周期({prev_start_date.date()}~{prev_end_date.date()})无数据")
            print(f"   提示: 完整数据集日期范围 {df[date_col].min().date()} ~ {df[date_col].max().date()}")
            return {}
        
        # 过滤掉不需要的渠道
        prev_data = prev_data[~prev_data['渠道'].isin(excluded_channels)]
        
        # 计算上一周期渠道指标
        def calc_prev_channel_metrics(data):
            """按渠道聚合计算上期指标（✅ 使用统一函数）"""
            if len(data) == 0:
                return None
            
            # ✅ 使用统一的订单聚合函数
            try:
                # 🔧 修复: 使用all_with_fallback模式,确保包含所有订单(包括闪购小程序)
                order_metrics = calculate_order_metrics(data, calc_mode='all_with_fallback')
            except Exception as e:
                print(f"⚠️ 上期数据聚合失败: {e}")
                return None
            
            # 添加渠道信息
            if '渠道' not in data.columns:
                print(f"⚠️ 上期数据缺少'渠道'字段")
                return None
            
            # 🔧 修复: 检查order_metrics是否已包含渠道字段
            if '渠道' not in order_metrics.columns:
                # 🔴 统一订单ID类型
                data['订单ID'] = data['订单ID'].astype(str)
                order_metrics['订单ID'] = order_metrics['订单ID'].astype(str)
                
                # 从原始数据中提取订单-渠道映射
                order_channel = data.groupby('订单ID')['渠道'].first().reset_index()
                order_metrics = order_metrics.merge(order_channel, on='订单ID', how='left')
                
                # 验证合并是否成功
                if '渠道' not in order_metrics.columns:
                    print(f"⚠️ 合并后缺少'渠道'字段")
                    print(f"   order_metrics列: {order_metrics.columns.tolist()}")
                    print(f"   order_channel列: {order_channel.columns.tolist()}")
                    return None
            else:
                print(f"✅ order_metrics已包含'渠道'字段,跳过merge")
            
            # 按渠道聚合 (✅ 修改：使用'实收价格'替代'商品实售价')
            channel_metrics = order_metrics.groupby('渠道').agg({
                '订单ID': 'count',
                '实收价格': 'sum',
                '订单实际利润': 'sum'
            }).reset_index()
            
            channel_metrics.columns = ['渠道', '订单数', '销售额', '总利润']
            channel_metrics['客单价'] = channel_metrics['销售额'] / channel_metrics['订单数']
            # ✅ 利润率 = 订单实际利润 / 销售额（订单实际利润已正确剔除平台服务费=0的订单）
            channel_metrics['利润率'] = (channel_metrics['总利润'] / channel_metrics['销售额'] * 100).fillna(0)
            
            return channel_metrics
        
        prev_metrics = calc_prev_channel_metrics(prev_data)
        
        if prev_metrics is None or len(prev_metrics) == 0:
            return {}
        
        # ✅ 调试日志: 显示上期指标
        print(f"   📊 上一周期渠道指标(使用利润额字段):", flush=True)
        for _, row in prev_metrics.iterrows():
            print(f"      {row['渠道']}: 订单{int(row['订单数'])}单, 销售额¥{row['销售额']:.0f}, 利润¥{row['总利润']:.2f}", flush=True)
        
        # 计算环比
        comparison_results = {}
        
        for _, current_row in current_metrics.iterrows():
            channel_name = current_row['渠道']
            prev_row = prev_metrics[prev_metrics['渠道'] == channel_name]
            
            if len(prev_row) == 0:
                # 上期没有该渠道数据
                continue
            
            prev_row = prev_row.iloc[0]
            
            def calc_rate(curr, prev):
                if prev == 0:
                    return 999.9 if curr > 0 else 0
                return ((curr - prev) / prev) * 100
            
            comparison_results[channel_name] = {
                '订单数': {
                    'current': current_row['订单数'],
                    'previous': prev_row['订单数'],
                    'change_rate': calc_rate(current_row['订单数'], prev_row['订单数']),
                    'metric_type': 'positive'
                },
                '销售额': {
                    'current': current_row['销售额'],
                    'previous': prev_row['销售额'],
                    'change_rate': calc_rate(current_row['销售额'], prev_row['销售额']),
                    'metric_type': 'positive'
                },
                '总利润': {
                    'current': current_row['总利润'],
                    'previous': prev_row['总利润'],
                    'change_rate': calc_rate(current_row['总利润'], prev_row['总利润']),
                    'metric_type': 'positive'
                },
                '客单价': {
                    'current': current_row['客单价'],
                    'previous': prev_row['客单价'],
                    'change_rate': calc_rate(current_row['客单价'], prev_row['客单价']),
                    'metric_type': 'positive'
                },
                '利润率': {
                    'current': current_row['利润率'],
                    'previous': prev_row['利润率'],
                    'change_rate': current_row['利润率'] - prev_row['利润率'],  # 利润率用差值
                    'metric_type': 'positive'
                }
            }
        
        print(f"✅ [渠道环比] 计算完成,共{len(comparison_results)}个渠道", flush=True)
        return comparison_results
        
    except Exception as e:
        print(f"❌ [渠道环比] 计算失败: {e}")
        import traceback
        traceback.print_exc()
        return {}


# ==================== Mantine UI 卡片工厂函数 ====================

def create_mantine_metric_card(title, value, badge_text=None, badge_color="blue"):
    """
    创建Mantine风格的指标卡片 - 完全模仿Bootstrap风格，只添加微妙增强
    
    设计理念：
    - ✅ 居中对齐（与Bootstrap一致）
    - ✅ 相同的文字层级（H6标题 + H4数值 + Badge）
    - ✅ 相同的间距（mb-1, mb-2）
    - ✅ 微妙增强：更平滑的阴影、更精细的圆角、悬停效果
    
    参数:
        title (str): 卡片标题（如"¥0-20"）
        value (str): 主要数值（如"727单"）
        badge_text (str, optional): 徽章文字（如"8.9% | 利润率 38.7%"）
        badge_color (str): 颜色主题 (blue/gray/red/green/teal等)
    
    返回:
        dmc.Card: Mantine卡片组件
    """
    if not MANTINE_AVAILABLE:
        # 降级为Bootstrap卡片
        return dbc.Card([
            dbc.CardBody([
                html.H6(title, className="text-muted mb-2"),
                html.H4(value, className=f"text-{badge_color} mb-2"),
                dbc.Badge(badge_text, color="secondary", className="mt-1") if badge_text else None
            ])
        ], className="modern-card text-center shadow-sm h-100")  # 🎨 添加modern-card悬停效果
    
    # 🎨 Mantine卡片 - 完全模仿Bootstrap布局
    children = []
    
    # 标题（对应 Bootstrap 的 H6）
    children.append(
        dmc.Text(
            title,
            size="sm",           # 对应 H6 大小
            c="dimmed",          # 对应 text-muted
            ta="center",         # ✅ 居中对齐
            mb="sm"              # 对应 mb-2
        )
    )
    
    # 主要数值（对应 Bootstrap 的 H4）
    children.append(
        dmc.Text(
            str(value),
            size="xl",           # 对应 H4 大小
            fw=700,              # 加粗
            c=badge_color,       # 颜色主题
            ta="center",         # ✅ 居中对齐
            mb="sm"              # 对应 mb-2
        )
    )
    
    # 徽章（完全复刻 Bootstrap 的双 Span 结构）
    if badge_text:
        # 解析徽章文字："8.9% | 利润率 38.7%"
        parts = badge_text.split('|')
        if len(parts) == 2:
            percentage = parts[0].strip()      # "8.9%"
            profit_text = parts[1].strip()     # "利润率 38.7%"
            
            children.append(
                dmc.Group([
                    # 第一个Span：百分比徽章（对应 badge bg-secondary）
                    dmc.Badge(
                        percentage,
                        variant="filled",       # 实心填充
                        color="gray",           # 灰色（对应 bg-secondary）
                        size="sm",
                        radius="sm",
                        style={'marginRight': '8px'}  # me-2
                    ),
                    # 第二个Span：利润率文字（对应 small text-muted）
                    dmc.Text(
                        profit_text,
                        size="xs",              # small
                        c="dimmed"              # text-muted
                    )
                ], gap="xs", justify="center")
            )
        else:
            # 如果格式不对，直接显示
            children.append(
                dmc.Text(badge_text, size="xs", c="dimmed", ta="center")
            )
    
    # 返回Mantine卡片 - 完全模仿Bootstrap样式
    return dmc.Card(
        dmc.Stack(children, gap="xs", align="center"),  # ✅ 居中对齐
        shadow="sm",                    # 对应 Bootstrap shadow-sm
        padding="md",                   # 对应 Bootstrap CardBody padding
        radius="md",                    # 8px圆角（Bootstrap默认）
        withBorder=True,                # 细边框
        style={
            'height': '100%',           # 对应 h-100
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center'  # ✅ 垂直居中
        }
    )


def create_mantine_progress_card(title, value, percentage, icon=None, color="blue", gradient=None):
    """
    创建带进度条的Mantine卡片
    
    参数:
        title (str): 卡片标题
        value (str/float): 数值
        percentage (float): 进度百分比 (0-100)
        icon (str, optional): Iconify图标名称
        color (str): 颜色主题
        gradient (dict, optional): 渐变配置
    
    返回:
        dmc.Card: Mantine卡片组件
    """
    if not MANTINE_AVAILABLE:
        # 降级为Bootstrap卡片
        return dbc.Card([
            dbc.CardBody([
                html.H5(title, className="card-title text-muted"),
                html.H3(value, className=f"text-{color}"),
                dbc.Progress(value=percentage, color=color, className="mt-2"),
                dbc.Badge(f"{percentage:.1f}%", color=color, className="mt-1")
            ])
        ], className="modern-card text-center shadow-sm h-100")  # 🎨 添加modern-card悬停效果
    
    # Mantine卡片组件
    return dmc.Card([
        dmc.Stack([
            # 图标+标题
            dmc.Group([
                dmc.ThemeIcon(
                    DashIconify(icon=icon, width=24) if icon else None,
                    size="xl",
                    radius="md",
                    variant="gradient" if gradient else "filled",
                    gradient=gradient if gradient else None,
                    color=color
                ) if icon else dmc.Text(title, size="sm", c="dimmed", fw=500),
                dmc.Text(title, size="sm", c="dimmed", fw=500) if icon else None
            ], justify="space-between"),
            
            # 数值
            dmc.Text(str(value), size="xl", fw=700, c=color),
            
            # 进度条
            dmc.Progress(
                value=percentage,
                size="lg",
                radius="xl",
                color=color,
                striped=True,
                animated=True
            ),
            
            # 百分比徽章
            dmc.Badge(
                f"{percentage:.1f}% 占比",
                variant="gradient" if gradient else "filled",
                gradient=gradient if gradient else None,
                color=color,
                size="lg"
            )
        ], gap="sm")
    ], shadow="sm", padding="lg", radius="md", withBorder=True, 
       style={'textAlign': 'center', 'height': '100%'})


# ==================== 性能优化工具函数 ====================

def create_skeleton_placeholder(height="200px", count=1):
    """
    ✨ 创建Skeleton占位符(企业级加载体验)
    
    参数:
        height: 占位符高度
        count: 占位符数量
    
    返回:
        Dash组件列表
    """
    skeletons = []
    for i in range(count):
        skeletons.append(
            html.Div([
                html.Div(className="skeleton-box", style={
                    'height': height,
                    'background': 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
                    'backgroundSize': '200% 100%',
                    'animation': 'skeleton-loading 1.5s ease-in-out infinite',
                    'borderRadius': '8px',
                    'marginBottom': '16px'
                })
            ])
        )
    return html.Div(skeletons)


def create_metric_cards_skeleton():
    """创建指标卡片的Skeleton占位符"""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div(style={
                        'height': '24px', 
                        'width': '80%', 
                        'background': '#e0e0e0',
                        'borderRadius': '4px',
                        'marginBottom': '12px',
                        'animation': 'skeleton-loading 1.5s ease-in-out infinite'
                    }),
                    html.Div(style={
                        'height': '48px', 
                        'width': '60%', 
                        'background': '#e0e0e0',
                        'borderRadius': '4px',
                        'marginBottom': '8px',
                        'animation': 'skeleton-loading 1.5s ease-in-out infinite'
                    })
                ])
            ], className="modern-card text-center shadow-sm")  # 🎨 添加modern-card
        ], md=2) for _ in range(6)
    ], className="mb-4")


def downsample_data_for_chart(df, max_points=1000, sort_column=None, keep_extremes=True):
    """
    ✨ 智能数据采样优化函数(用于图表展示) - 阶段6增强版
    
    策略:
    1. 数据量<=max_points: 不采样,返回全部数据
    2. 数据量>max_points: 智能采样,保证趋势和关键点
       - 保留首尾数据点
       - 保留极值点(最大值/最小值)
       - 等间隔采样中间数据
    
    Args:
        df: 原始数据DataFrame
        max_points: 最大展示点数(默认1000)
        sort_column: 排序列名(如'日期'),确保时序正确
        keep_extremes: 是否保留极值点(默认True)
        
    Returns:
        tuple: (采样后的DataFrame, 采样信息dict)
        
    示例:
        >>> sampled_df, info = downsample_data_for_chart(df, max_points=500, sort_column='日期')
        >>> print(info['message'])  # "⚡ 数据采样: 5000行 → 500点"
        
    注意: 此函数仅用于优化图表展示,不改变原始数据
    """
    original_count = len(df)
    
    if original_count <= max_points:
        # 数据量小,不需要采样
        return df, {
            'sampled': False,
            'original_count': original_count,
            'sampled_count': original_count,
            'message': f"✅ 数据量适中 ({original_count}行),无需采样"
        }
    
    # 数据量大,需要采样
    print(f"   ⚡ [性能优化] 数据采样: {original_count}行 → {max_points}点 (保证趋势)", flush=True)
    
    # 如果指定了排序列,先排序
    if sort_column and sort_column in df.columns:
        df = df.sort_values(sort_column).reset_index(drop=True)
    
    # 保留的关键索引
    key_indices = set()
    
    # 1. 始终保留首尾点
    key_indices.add(0)
    key_indices.add(original_count - 1)
    
    # 2. 保留极值点(如果有数值列)
    if keep_extremes:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            # 对主要数值列找极值
            for col in numeric_cols[:3]:  # 限制只检查前3个数值列,避免过多极值
                try:
                    max_idx = df[col].idxmax()
                    min_idx = df[col].idxmin()
                    if pd.notna(max_idx):
                        key_indices.add(max_idx)
                    if pd.notna(min_idx):
                        key_indices.add(min_idx)
                except:
                    pass
    
    # 3. 等间隔采样
    step = max(1, original_count // max_points)
    interval_indices = set(range(0, original_count, step))
    
    # 合并所有索引
    all_indices = sorted(key_indices | interval_indices)
    
    # 限制总数不超过max_points
    if len(all_indices) > max_points:
        # 优先保留关键点
        step = max(1, len(all_indices) // max_points)
        key_indices_list = sorted(key_indices)
        interval_subset = [idx for idx in all_indices if idx not in key_indices][::step]
        all_indices = sorted(set(key_indices_list + interval_subset))
    
    # 采样
    sampled_df = df.iloc[all_indices].copy()
    sampled_count = len(sampled_df)
    
    return sampled_df, {
        'sampled': True,
        'original_count': original_count,
        'sampled_count': sampled_count,
        'reduction_rate': (1 - sampled_count / original_count) * 100,
        'message': f"⚡ 数据采样: {original_count}行 → {sampled_count}点 (减少{(1 - sampled_count / original_count) * 100:.1f}%)"
    }


def create_data_info_badge(sampling_info):
    """
    创建数据量信息徽章(显示是否采样)
    
    Args:
        sampling_info: downsample_data_for_chart返回的信息dict
        
    Returns:
        dbc.Badge组件
    """
    if not sampling_info['sampled']:
        return dbc.Badge(
            f"📊 {sampling_info['original_count']}条数据",
            color="info",
            className="ms-2"
        )
    else:
        return dbc.Badge([
            html.I(className="fas fa-chart-line me-1"),
            f"采样展示: {sampling_info['sampled_count']}/{sampling_info['original_count']}条 (优化{sampling_info['reduction_rate']:.0f}%)"
        ], color="warning", className="ms-2", pill=True)


# ==================== 订单指标计算（统一函数）====================


# 初始化数据
initialize_data()
initialize_ai_tools()

# 🔍 调试: 打印DATABASE_AVAILABLE状态
print(f"\n{'='*80}")
print(f"🔍 [UI渲染前检查] DATABASE_AVAILABLE = {DATABASE_AVAILABLE}")
print(f"🔍 [UI渲染前检查] DATA_SOURCE_MANAGER = {DATA_SOURCE_MANAGER}")
print(f"🔍 [UI渲染前检查] Tab将被{'启用' if DATABASE_AVAILABLE else '禁用(灰色)'}")
if DATABASE_AVAILABLE:
    print(f"🔍 [UI渲染前检查] INITIAL_STORE_OPTIONS 数量 = {len(INITIAL_STORE_OPTIONS)}")
    for i, opt in enumerate(INITIAL_STORE_OPTIONS, 1):
        print(f"   {i}. {opt['label']}")
print(f"{'='*80}\n")

PANDAS_STATUS_TEXT = "可用" if PANDAS_AI_ANALYZER else ("待安装" if PANDAS_AI_MODULE_AVAILABLE else "未安装")
PANDAS_STATUS_COLOR = "success" if PANDAS_AI_ANALYZER else ("warning" if PANDAS_AI_MODULE_AVAILABLE else "secondary")
RAG_STATUS_TEXT = "可用" if RAG_ANALYZER_INSTANCE else ("待安装" if RAG_MODULE_AVAILABLE else "未安装")
RAG_STATUS_COLOR = "success" if RAG_ANALYZER_INSTANCE else ("warning" if RAG_MODULE_AVAILABLE else "secondary")
KB_STATS_TEXT = ""
if VECTOR_KB_INSTANCE:
    try:
        _kb_stats = VECTOR_KB_INSTANCE.get_stats()
        KB_STATS_TEXT = f"案例数: {_kb_stats.get('total_cases', 0)} | 标签数: {len(_kb_stats.get('tag_distribution', {}))}"
    except Exception as exc:
        KB_STATS_TEXT = f"知识库统计读取失败: {exc}"
else:
    KB_STATS_TEXT = "知识库未初始化"

# 自定义CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>门店诊断看板(订单数据)</title>
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
            
            /* 日历选择器中文星期显示 */
            .DateInput_input {
                font-size: 14px;
                padding: 8px 12px;
            }
            
            /* 自定义星期标题为中文 */
            .CalendarMonth_caption {
                font-size: 16px;
                font-weight: bold;
                padding-bottom: 10px;
            }
            
            /* 🔧 修复: 星期标题样式优化，避免和日期重叠 */
            .DayPicker_weekHeader {
                position: relative;
                top: 0;
                padding-bottom: 15px !important;  /* 进一步增加底部间距 */
                margin-bottom: 10px !important;   /* 进一步增加下边距 */
            }
            
            .DayPicker_weekHeader_ul {
                margin-bottom: 15px !important;  /* 进一步增加列表底部间距 */
                padding-bottom: 5px !important;  /* 额外内边距 */
            }
            
            .DayPicker_weekHeader_li {
                padding: 10px 0 !important;  /* 进一步增加上下内边距 */
                margin-bottom: 5px !important;  /* 额外底部边距 */
            }
            
            /* 隐藏原始英文星期文本 */
            .DayPicker_weekHeader small {
                font-size: 0 !important;  /* 隐藏原始英文文本 */
                visibility: hidden;
                display: inline-block;
                height: 20px;  /* 固定高度 */
            }
            
            /* 使用CSS伪元素添加中文星期（周一开始） */
            .DayPicker_weekHeader_li:nth-child(1) small:before { 
                font-size: 15px;
                font-weight: 600;
                content: "一"; 
                visibility: visible;
                display: inline-block;
                color: #333;
            }
            
            .DayPicker_weekHeader_li:nth-child(2) small:before { 
                font-size: 15px;
                font-weight: 600;
                content: "二"; 
                visibility: visible;
                display: inline-block;
                color: #333;
            }
            
            .DayPicker_weekHeader_li:nth-child(3) small:before { 
                font-size: 15px;
                font-weight: 600;
                content: "三"; 
                visibility: visible;
                display: inline-block;
                color: #333;
            }
            
            .DayPicker_weekHeader_li:nth-child(4) small:before { 
                font-size: 14px;
                font-weight: 600;
                content: "四"; 
                visibility: visible;
                display: inline-block;
                color: #333;
            }
            
            .DayPicker_weekHeader_li:nth-child(5) small:before { 
                font-size: 14px;
                font-weight: 600;
                content: "五"; 
                visibility: visible;
                display: inline-block;
                color: #333;
            }
            
            .DayPicker_weekHeader_li:nth-child(6) small:before { 
                font-size: 14px;
                font-weight: 600;
                content: "六"; 
                visibility: visible;
                display: inline-block;
                color: #333;
            }
            
            .DayPicker_weekHeader_li:nth-child(7) small:before { 
                font-size: 14px;
                font-weight: 600;
                content: "日"; 
                visibility: visible;
                display: inline-block;
                color: #d32f2f;  /* 周日用红色 */
            }
            
            /* 🔧 增加日历日期单元格的间距 */
            .CalendarDay {
                padding: 8px 0 !important;  /* 增加日期单元格内边距 */
                line-height: 1.5 !important;
            }
            
            /* 🔧 优化日历整体布局 */
            .DayPicker {
                padding-top: 12px !important;  /* 增加顶部内边距 */
            }
            
            .DayPicker_weekHeaders {
                margin-bottom: 20px !important;  /* 进一步增加星期标题和日期之间的间距 */
            }
            
            /* 🔧 日历日期容器额外间距 */
            .DayPicker_transitionContainer {
                padding-top: 10px !important;
            }
            
            /* 🆕 单日选择模式：完全隐藏结束日期输入框和箭头 */
            .single-day-picker .DateInput:last-child,
            .single-day-picker .DateRangePickerInput_arrow {
                display: none !important;  /* 完全隐藏结束日期和箭头 */
            }
            
            /* 🆕 单日选择模式：优化开始日期输入框样式 */
            .single-day-picker .DateInput:first-child {
                width: 100% !important;
                max-width: 100% !important;
            }
            
            /* 🎨 CSS定制：现代化卡片样式（超级增强版 - 最高优先级） */
            .modern-card {
                /* 关键修复：确保transform生效 */
                position: relative !important;
                display: block !important;
                transform: translateY(0) scale(1) !important;
                
                /* 视觉样式 */
                background: linear-gradient(145deg, #ffffff 0%, #f5f7fa 100%) !important;
                border: 2px solid #e3e8ef !important;
                border-radius: 18px !important;
                box-shadow: 
                    0 4px 6px rgba(0,0,0,0.05),
                    0 10px 20px rgba(0,0,0,0.03) !important;
                
                /* 动画设置 */
                transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
                will-change: transform, box-shadow !important;
                backface-visibility: hidden !important;
                
                /* 布局 */
                overflow: hidden !important;  /* 🔧 改为hidden，裁剪彩色条防止溢出 */
                cursor: pointer !important;
                min-height: 100% !important;
                height: auto !important;
            }
            
            /* ✨ 关键修复：卡片内所有元素都不阻止父级悬停 */
            .modern-card * {
                pointer-events: none !important;
            }
            
            /* 恢复卡片本身的交互 */
            .modern-card {
                pointer-events: auto !important;
            }
            
            /* 顶部彩色渐变条（常驻加粗，更醒目） */
            .modern-card::before {
                content: '';
                position: absolute;
                top: 0;  /* 🎯 贴合顶部 */
                left: 0;
                right: 0;
                height: 5px;
                background: linear-gradient(90deg, 
                    #0d6efd 0%, 
                    #6610f2 25%,
                    #d63384 50%, 
                    #fd7e14 75%,
                    #ffc107 100%);
                opacity: 0.8;
                transition: all 0.35s ease;
                border-radius: 16px 16px 0 0 !important;  /* 🔧 圆角与卡片一致 */
            }
            
            /* 悬停效果（更夸张的变化） */
            .modern-card:hover {
                transform: translateY(-12px) scale(1.03) !important;
                box-shadow: 
                    0 12px 24px rgba(13,110,253,0.2),
                    0 24px 48px rgba(13,110,253,0.15) !important;
                border-color: #0d6efd !important;
                background: linear-gradient(145deg, #ffffff 0%, #f0f4ff 100%) !important;
            }
            
            .modern-card:hover::before {
                height: 6px !important;
                opacity: 1 !important;
                box-shadow: 0 3px 12px rgba(13,110,253,0.5) !important;
            }
            
            /* 卡片内容动画 */
            .modern-card-content {
                padding: 1.5rem;
                text-align: center;
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: center;
                position: relative;
                z-index: 1;
            }
            
            /* ✨ 数值放大动画（增强优先级和效果） */
            .modern-value {
                transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
                display: inline-block !important;
            }
            
            .modern-card:hover .modern-value {
                transform: scale(1.15) !important;
                color: #0d6efd !important;
                text-shadow: 0 4px 12px rgba(13,110,253,0.4) !important;
            }
            
            /* ✨ 徽章悬停效果（增强动画） */
            .modern-card .badge {
                transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
                display: inline-block !important;
            }
            
            .modern-card:hover .badge {
                transform: scale(1.15) translateY(-3px) !important;
                box-shadow: 0 6px 16px rgba(0,0,0,0.2) !important;
            }
            
            .single-day-picker .DateInput:first-child .DateInput_input {
                width: 100% !important;
                text-align: center;  /* 居中显示日期 */
                font-weight: 500;
            }
            
            /* 优化日期选择器的整体布局 */
            .DateRangePickerInput {
                display: flex;
                align-items: center;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 0.375rem 0.75rem;
            }
            
            .DateRangePickerInput_arrow {
                padding: 0 8px;
                color: #6c757d;
            }
            
            /* 🎨 上传动画美化 */
            #upload-loading ._dash-loading {
                display: flex !important;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100px;
            }
            
            #upload-loading ._dash-loading::after {
                content: "正在处理上传文件...";
                margin-top: 15px;
                font-size: 0.95rem;
                color: #667eea;
                font-weight: 500;
                animation: uploadPulse 1.5s ease-in-out infinite;
            }
            
            @keyframes uploadPulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            /* 上传区域悬停效果增强 */
            #upload-data:hover {
                border-color: #667eea !important;
                background: linear-gradient(135deg, #f8f9ff 0%, #e8ebff 100%) !important;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
            }
            
            #upload-data {
                transition: all 0.3s ease !important;
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
        <script>
            // 开发模式控制（生产环境设为false）
            window.DEBUG_MODE = false;
            
            // 强制触发周期选择器回调
            window.addEventListener('load', function() {
                if (window.DEBUG_MODE) console.log('🔄 页面加载完成，准备触发回调...');
                setTimeout(function() {
                    // 找到对比模式选择器
                    var selector = document.querySelector('#time-period-selector');
                    if (selector) {
                        if (window.DEBUG_MODE) console.log('✅ 找到选择器，当前值:', selector.value);
                        // 强制触发change事件
                        var event = new Event('change', { bubbles: true });
                        selector.dispatchEvent(event);
                        if (window.DEBUG_MODE) console.log('🚀 已触发change事件');
                    }
                    // 已移除不必要的警告日志
                }, 2000); // 等待2秒确保Dash初始化完成
                
                // 🆕 单日选择模式：自动同步开始和结束日期
                // 监听日期选择器的变化
                setTimeout(function() {
                    if (window.DEBUG_MODE) console.log('📅 初始化单日选择模式监听器...');
                    
                    // 获取所有日期选择器输入框
                    var dateInputs = document.querySelectorAll('input[id*="date-range"]');
                    
                    dateInputs.forEach(function(input) {
                        // 监听日期变化
                        input.addEventListener('change', function(e) {
                            var inputId = e.target.id;
                            
                            // 检查是否是开始日期输入框
                            if (inputId && inputId.includes('start')) {
                                if (window.DEBUG_MODE) console.log('📅 开始日期被选择:', e.target.value);
                                
                                // 找到对应的结束日期输入框
                                var endInputId = inputId.replace('start', 'end');
                                var endInput = document.getElementById(endInputId);
                                
                                if (endInput && e.target.value) {
                                    // 自动将结束日期设置为开始日期
                                    endInput.value = e.target.value;
                                    if (window.DEBUG_MODE) console.log('✅ 已自动同步结束日期:', e.target.value);
                                    
                                    // 触发change事件，通知Dash
                                    var changeEvent = new Event('change', { bubbles: true });
                                    endInput.dispatchEvent(changeEvent);
                                }
                            }
                        });
                    });
                    
                    if (window.DEBUG_MODE) console.log('✅ 单日选择模式已启用');
                }, 2500);
                
                // CSS已经优化了布局，移除其他JavaScript操作以提升性能
            });
        </script>
    </body>
</html>
'''

# ==================== 全局数据信息组件 ====================
def create_data_info_card():
    """创建全局数据信息卡片（显示在所有Tab顶部）- 使用统一样式"""
    # 如果样式库可用，使用预设函数；否则使用原始方式
    if COMPONENT_STYLES_AVAILABLE:
        # 注意：这里只是返回占位结构，实际内容由回调更新
        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # 数据状态指示器
                    dbc.Col([
                        html.Div([
                            html.I(className="bi bi-database-check me-2", 
                                   style={'fontSize': '1.2rem', 'color': '#28a745'}),
                            html.Span("数据已加载", id='data-status-text', 
                                     className="fw-bold", style={'color': '#28a745'})
                        ], className="d-flex align-items-center")
                    ], width=2),
                    
                    # 数据文件名
                    dbc.Col([
                        html.Small("📁 数据文件:", className="text-muted me-2"),
                        html.Span(id='data-filename', children="加载中...", className="fw-bold")
                    ], width=3),
                    
                    # 数据时间范围
                    dbc.Col([
                        html.Small("📅 时间范围:", className="text-muted me-2"),
                        html.Span(id='data-date-range', children="计算中...", className="fw-bold")
                    ], width=3),
                    
                    # 数据量统计
                    dbc.Col([
                        html.Small("📊 数据量:", className="text-muted me-2"),
                        html.Span(id='data-record-count', children="统计中...", className="fw-bold")
                    ], width=2),
                    
                    # 最后更新时间
                    dbc.Col([
                        html.Small("🕐 更新时间:", className="text-muted me-2"),
                        html.Span(id='data-update-time', children="--", className="text-muted small")
                    ], width=2)
                ], align="center")
            ])
        ], className="mb-3 shadow-sm", style={
            'borderLeft': '4px solid #28a745',
            'borderRadius': '8px'
        })
    else:
        # 原始方式（保持兼容）
        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # 数据状态指示器
                    dbc.Col([
                        html.Div([
                            html.I(className="bi bi-database-check me-2", 
                                   style={'fontSize': '1.2rem', 'color': '#28a745'}),
                            html.Span("数据已加载", id='data-status-text', 
                                     className="fw-bold", style={'color': '#28a745'})
                        ], className="d-flex align-items-center")
                    ], width=2),
                    
                    # 数据文件名
                    dbc.Col([
                        html.Small("📁 数据文件:", className="text-muted me-2"),
                        html.Span(id='data-filename', children="加载中...", className="fw-bold")
                    ], width=3),
                    
                    # 数据时间范围
                    dbc.Col([
                        html.Small("📅 时间范围:", className="text-muted me-2"),
                        html.Span(id='data-date-range', children="计算中...", className="fw-bold")
                    ], width=3),
                    
                    # 数据量统计
                    dbc.Col([
                        html.Small("📊 数据量:", className="text-muted me-2"),
                        html.Span(id='data-record-count', children="统计中...", className="fw-bold")
                    ], width=2),
                    
                    # 最后更新时间
                    dbc.Col([
                        html.Small("🕐 更新时间:", className="text-muted me-2"),
                        html.Span(id='data-update-time', children="--", className="text-muted small")
                    ], width=2)
                ], align="center")
            ])
        ], className="mb-3", style={
            'borderLeft': '4px solid #28a745',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
        })


# ==================== 渠道表现对比组件 ====================
def _create_channel_comparison_cards(df: pd.DataFrame, order_agg: pd.DataFrame, 
                                    channel_comparison: Dict[str, Dict] = None) -> html.Div:
    """
    创建渠道表现对比卡片（美团、饿了么、京东）- 增强版支持环比
    
    Args:
        df: 原始订单数据
        order_agg: 订单聚合数据
        channel_comparison: 渠道环比数据字典(可选)
        
    Returns:
        渠道对比组件
    """
    if '渠道' not in df.columns:
        return html.Div()
    
    try:
        # 🔴 统一订单ID类型
        df['订单ID'] = df['订单ID'].astype(str)
        order_agg['订单ID'] = order_agg['订单ID'].astype(str)
        
        # 确保订单聚合数据包含渠道信息
        if '渠道' not in order_agg.columns:
            # 从原始数据中获取订单对应的渠道
            order_channel = df.groupby('订单ID')['渠道'].first().reset_index()
            order_channel['订单ID'] = order_channel['订单ID'].astype(str)  # 🔴 确保order_channel的订单ID也是str
            order_agg = order_agg.merge(order_channel, on='订单ID', how='left')
        
        # ✅ 确保订单聚合数据包含"实收价格"字段
        if '实收价格' not in order_agg.columns and '实收价格' in df.columns:
            # ⚠️ 关键修复: 实收价格是单价，需要先乘以销量再聚合
            if '月售' in df.columns:
                df_temp = df.copy()
                df_temp['订单总收入'] = df_temp['实收价格'] * df_temp['月售']
                order_actual_price = df_temp.groupby('订单ID')['订单总收入'].sum().reset_index()
                order_actual_price.columns = ['订单ID', '实收价格']
                print(f"🔧 [渠道对比] 实收价格修复: 使用(实收价格×月售)聚合")
            else:
                # 兜底方案: 如果没有月售字段，直接sum（可能不准确）
                order_actual_price = df.groupby('订单ID')['实收价格'].sum().reset_index()
                print(f"⚠️ [渠道对比] 实收价格兜底: 直接sum（缺少月售字段）")
            order_agg = order_agg.merge(order_actual_price, on='订单ID', how='left')
        
        # ✅ 过滤掉不参与对比的渠道（含咖啡渠道）
        excluded_channels = ['收银机订单', '闪购小程序'] + CHANNELS_TO_REMOVE
        order_agg_filtered = order_agg[~order_agg['渠道'].isin(excluded_channels)].copy()
        
        # ✅ 按渠道聚合统计 (销售额使用"实收价格")
        channel_stats = order_agg_filtered.groupby('渠道').agg({
            '订单ID': 'count',
            '实收价格': 'sum',  # ✅ 修改：使用"实收价格"作为销售额
            '订单实际利润': 'sum',
            '商家活动成本': 'sum',
            '平台佣金': 'sum',
            '配送净成本': 'sum'  # ✅ 修改：使用"配送净成本"而不是"物流配送费"
        }).reset_index()
        
        channel_stats.columns = ['渠道', '订单数', '销售额', '总利润', '营销成本', '平台佣金', '配送成本']

        if '平台服务费' in order_agg_filtered.columns:
            platform_fee_stats = order_agg_filtered.groupby('渠道')['平台服务费'].sum().reset_index()
            channel_stats = channel_stats.merge(platform_fee_stats, on='渠道', how='left')
            channel_stats['平台服务费'] = channel_stats['平台服务费'].fillna(0)
        else:
            channel_stats['平台服务费'] = channel_stats['平台佣金']
        
        # 计算核心指标
        channel_stats['客单价'] = channel_stats['销售额'] / channel_stats['订单数']
        channel_stats['利润率'] = (channel_stats['总利润'] / channel_stats['销售额'] * 100).fillna(0)
        channel_stats['营销成本率'] = (channel_stats['营销成本'] / channel_stats['销售额'] * 100).fillna(0)
        channel_stats['佣金率'] = (channel_stats['平台服务费'] / channel_stats['销售额'] * 100).fillna(0)
        channel_stats['配送成本率'] = (channel_stats['配送成本'] / channel_stats['销售额'] * 100).fillna(0)
        channel_stats['销售额占比'] = (channel_stats['销售额'] / channel_stats['销售额'].sum() * 100).fillna(0)
        
        # ✅ 新增：单均成本指标
        channel_stats['单均营销费用'] = channel_stats['营销成本'] / channel_stats['订单数']
        channel_stats['单均配送费支出'] = channel_stats['配送成本'] / channel_stats['订单数']
        
        # ✅ 新增：单均利润指标
        channel_stats['单均利润'] = channel_stats['总利润'] / channel_stats['订单数']
        
        # 按销售额排序
        channel_stats = channel_stats.sort_values('销售额', ascending=False)
        
        # 渠道图标映射
        channel_icons = {
            '美团': '🟡',
            '饿了么': '🔵',
            '京东': '🔴',
            '美团外卖': '🟡',
            '饿了么外卖': '🔵'
        }
        
        # 渠道颜色映射
        channel_colors = {
            '美团': 'warning',
            '饿了么': 'info',
            '京东': 'danger',
            '美团外卖': 'warning',
            '饿了么外卖': 'info'
        }
        
        # 创建渠道卡片
        channel_cards = []
        
        for idx, row in channel_stats.iterrows():
            channel_name = row['渠道']
            icon = channel_icons.get(channel_name, '📱')
            card_color = channel_colors.get(channel_name, 'secondary')
            
            # ✅ 获取该渠道的环比数据
            channel_comp = channel_comparison.get(channel_name, {}) if channel_comparison else {}
            
            # 健康度评分（基于利润率）
            profit_rate = row['利润率']
            if profit_rate >= 12:
                health_badge = dbc.Badge("优秀", color="success", className="ms-2")
            elif profit_rate >= 8:
                health_badge = dbc.Badge("良好", color="primary", className="ms-2")
            elif profit_rate >= 5:
                health_badge = dbc.Badge("一般", color="warning", className="ms-2")
            else:
                health_badge = dbc.Badge("待优化", color="danger", className="ms-2")
            
            card = dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            icon, f" {channel_name}",
                            health_badge
                        ], className="mb-0")
                    ], className=f"bg-{card_color} text-white"),
                    dbc.CardBody([
                        # 核心指标 - 第一行（带环比）
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Small("订单数", className="text-muted d-block"),
                                    html.H5(f"{int(row['订单数']):,}单", className="mb-0"),
                                    create_comparison_badge(channel_comp.get('订单数', {}))
                                ])
                            ], width=4),
                            dbc.Col([
                                html.Div([
                                    html.Small("销售额", className="text-muted d-block"),
                                    html.H5(f"¥{row['销售额']:,.0f}", className="mb-0 text-primary"),
                                    create_comparison_badge(channel_comp.get('销售额', {}))
                                ])
                            ], width=4),
                            dbc.Col([
                                html.Div([
                                    html.Small("占比", className="text-muted d-block"),
                                    html.H5(f"{row['销售额占比']:.1f}%", className="mb-0 text-secondary")
                                ])
                            ], width=4)
                        ], className="mb-3"),
                        
                        # 核心指标 - 第二行 (带环比)
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Small("利润额", className="text-muted d-block"),
                                    html.H6(f"¥{row['总利润']:,.0f}", className="mb-0 text-success fw-bold"),
                                    create_comparison_badge(channel_comp.get('总利润', {}))
                                ])
                            ], width=4),
                            dbc.Col([
                                html.Div([
                                    html.Small("客单价", className="text-muted d-block"),
                                    html.H6(f"¥{row['客单价']:.2f}", className="mb-0"),
                                    create_comparison_badge(channel_comp.get('客单价', {}))
                                ])
                            ], width=4),
                            dbc.Col([
                                html.Div([
                                    html.Small("利润率", className="text-muted d-block"),
                                    html.H6(
                                        f"{row['利润率']:.1f}%",
                                        className="mb-0 " + (
                                            "text-success" if row['利润率'] >= 10 else
                                            "text-warning" if row['利润率'] >= 5 else
                                            "text-danger"
                                        )
                                    ),
                                    create_comparison_badge(channel_comp.get('利润率', {}))
                                ])
                            ], width=4)
                        ], className="mb-3"),
                        
                        # ✅ 新增：单均指标 - 第三行
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Small("单均利润", className="text-muted d-block"),
                                    html.H6(f"¥{row['单均利润']:.2f}", className="mb-0 text-success fw-bold")
                                ])
                            ], width=4),
                            dbc.Col([
                                html.Div([
                                    html.Small("单均营销费用", className="text-muted d-block"),
                                    html.H6(f"¥{row['单均营销费用']:.2f}", className="mb-0 text-warning fw-bold")
                                ])
                            ], width=4),
                            dbc.Col([
                                html.Div([
                                    html.Small("单均配送费支出", className="text-muted d-block"),
                                    html.H6(f"¥{row['单均配送费支出']:.2f}", className="mb-0 text-secondary fw-bold")
                                ])
                            ], width=4)
                        ], className="mb-3"),
                        
                        # 成本结构 - 优化为可视化进度条
                        html.Hr(),
                        html.Small("成本结构分析：", className="text-muted fw-bold d-block mb-2"),
                        
                        # 营销成本
                        html.Div([
                            html.Div([
                                html.Span("💰 营销", className="small me-2"),
                                html.Span(f"{row['营销成本率']:.1f}%", className="small fw-bold text-warning")
                            ], className="d-flex justify-content-between mb-1"),
                            dbc.Progress(
                                value=row['营销成本率'],
                                max=30,  # 设置最大值为30%
                                color="warning",
                                style={'height': '8px'},
                                className="mb-2"
                            )
                        ]),
                        
                        # 平台佣金
                        html.Div([
                            html.Div([
                                html.Span("📱 佣金", className="small me-2"),
                                html.Span(f"{row['佣金率']:.1f}%", className="small fw-bold text-info")
                            ], className="d-flex justify-content-between mb-1"),
                            dbc.Progress(
                                value=row['佣金率'],
                                max=30,
                                color="info",
                                style={'height': '8px'},
                                className="mb-2"
                            )
                        ]),
                        
                        # 配送成本
                        html.Div([
                            html.Div([
                                html.Span("🚚 配送", className="small me-2"),
                                html.Span(f"{row['配送成本率']:.1f}%", className="small fw-bold text-secondary")
                            ], className="d-flex justify-content-between mb-1"),
                            dbc.Progress(
                                value=row['配送成本率'],
                                max=30,
                                color="secondary",
                                style={'height': '8px'},
                                className="mb-1"
                            )
                        ]),
                        
                        # 总成本率
                        html.Hr(className="my-2"),
                        html.Div([
                            html.Span("📊 总成本率", className="small fw-bold"),
                            html.Span(
                                f"{row['营销成本率'] + row['佣金率'] + row['配送成本率']:.1f}%",
                                className="small fw-bold " + (
                                    "text-success" if (row['营销成本率'] + row['佣金率'] + row['配送成本率']) < 25 else
                                    "text-warning" if (row['营销成本率'] + row['佣金率'] + row['配送成本率']) < 35 else
                                    "text-danger"
                                )
                            )
                        ], className="d-flex justify-content-between")
                    ])
                ], className="h-100 shadow-sm")
            ], md=4, className="mb-3")
            
            channel_cards.append(card)
        
        # 渠道对比分析建议
        if len(channel_stats) == 0:
            # 没有渠道数据时返回空布局
            return dbc.Row([
                dbc.Col([
                    dbc.Alert("暂无渠道数据", color="info", className="text-center")
                ], width=12)
            ])
        
        best_channel = channel_stats.iloc[0]
        worst_channel = channel_stats.iloc[-1] if len(channel_stats) > 1 else best_channel
        
        insights = []
        
        # 洞察1: 最优渠道
        insights.append(
            dbc.Alert([
                html.I(className="bi bi-trophy-fill me-2"),
                html.Strong(f"🏆 最优渠道: {best_channel['渠道']}"),
                html.Br(),
                html.Small(
                    f"利润率 {best_channel['利润率']:.1f}%，销售额占比 {best_channel['销售额占比']:.1f}%，"
                    f"建议加大资源投入",
                    className="text-muted"
                )
            ], color="success", className="mb-2")
        )
        
        # 洞察2: 待优化渠道
        if len(channel_stats) > 1 and worst_channel['利润率'] < 8:
            insights.append(
                dbc.Alert([
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    html.Strong(f"⚠️ 待优化渠道: {worst_channel['渠道']}"),
                    html.Br(),
                    html.Small(
                        f"利润率仅 {worst_channel['利润率']:.1f}%，"
                        f"建议优化营销成本({worst_channel['营销成本率']:.1f}%)和配送策略({worst_channel['配送成本率']:.1f}%)",
                        className="text-muted"
                    )
                ], color="warning", className="mb-2")
            )
        
        # 洞察3: 营销成本对比
        avg_marketing_rate = channel_stats['营销成本率'].mean()
        high_marketing_channels = channel_stats[channel_stats['营销成本率'] > avg_marketing_rate * 1.2]
        if len(high_marketing_channels) > 0:
            insights.append(
                dbc.Alert([
                    html.I(className="bi bi-piggy-bank-fill me-2"),
                    html.Strong(f"💰 营销成本提示"),
                    html.Br(),
                    html.Small(
                        f"{', '.join(high_marketing_channels['渠道'].tolist())} 的营销成本率偏高，"
                        f"建议评估活动ROI并优化促销策略",
                        className="text-muted"
                    )
                ], color="info", className="mb-2")
            )
        
        # 组装最终组件
        return html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.H4([
                        html.I(className="bi bi-shop me-2"),
                        "📱 渠道表现对比分析"
                    ], className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.Row(channel_cards),
                    
                    # 智能洞察
                    html.Div([
                        html.H5([
                            html.I(className="bi bi-lightbulb-fill me-2"),
                            "💡 智能洞察"
                        ], className="mt-3 mb-3"),
                        html.Div(insights)
                    ])
                ])
            ], className="mb-4")
        ])
        
    except Exception as e:
        print(f"❌ 渠道对比分析失败: {e}")
        import traceback
        traceback.print_exc()
        return html.Div()


# ==================== 客单价深度分析组件 ====================
def _create_aov_analysis(df: pd.DataFrame, order_agg: pd.DataFrame, selected_channel: str = 'all') -> html.Div:
    """
    创建客单价深度分析组件
    
    Args:
        df: 原始订单数据
        order_agg: 订单聚合数据
        selected_channel: 选中的渠道 ('all'表示全部渠道)
    
    Returns:
        客单价分析组件
    """
    try:
        if df is None or len(df) == 0 or order_agg is None or len(order_agg) == 0:
            return html.Div()
        
        # 🔧 剔除咖啡渠道（不再排除闪购小程序和收银机订单）
        exclude_channels = CHANNELS_TO_REMOVE
        
        # 🔴 统一订单ID类型
        df['订单ID'] = df['订单ID'].astype(str)
        order_agg['订单ID'] = order_agg['订单ID'].astype(str)
        
        # 从df或order_agg中获取渠道信息
        if '渠道' in order_agg.columns:
            # 如果order_agg已经有渠道字段,直接使用
            pass
        elif '渠道' in df.columns:
            # 否则从df中提取渠道信息
            order_channel = df.groupby('订单ID')['渠道'].first().reset_index()
            order_channel['订单ID'] = order_channel['订单ID'].astype(str)
            order_agg = order_agg.merge(order_channel, on='订单ID', how='left')
        
        # 🆕 渠道筛选逻辑：支持按渠道筛选或排除咖啡渠道
        if '渠道' in order_agg.columns:
            original_count = len(order_agg)
            
            # 先排除咖啡渠道
            order_agg = order_agg[~order_agg['渠道'].isin(exclude_channels)].copy()
            
            # 如果选择了特定渠道,进行筛选
            if selected_channel != 'all':
                order_agg = order_agg[order_agg['渠道'] == selected_channel].copy()
                print(f"📊 [客单价分析-渠道筛选] 渠道='{selected_channel}': {original_count} -> {len(order_agg)} 订单")
            else:
                filtered_count = original_count - len(order_agg)
                if filtered_count > 0:
                    print(f"📊 [客单价分析] 已剔除{exclude_channels}渠道订单 {filtered_count} 单，剩余 {len(order_agg)} 单")
        
        if len(order_agg) == 0:
            available_channels = []
            if '渠道' in df.columns:
                available_channels = sorted([ch for ch in df['渠道'].dropna().unique() if ch not in exclude_channels])
            msg = f"⚠️ 渠道 '{selected_channel}' 暂无数据" if selected_channel != 'all' else "剔除特定渠道后无可用数据"
            if available_channels and selected_channel != 'all':
                msg += f"\n\n可用渠道: {', '.join(available_channels)}"
            return html.Div([
                dbc.Alert(msg, color="warning", style={'whiteSpace': 'pre-wrap'})
            ])
        
        # ========== 📈 计算周环比数据（新增） ==========
        # 合并日期信息到order_agg
        date_col = '日期' if '日期' in df.columns else '下单时间'
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col])
            order_date_map = df.groupby('订单ID')[date_col].first().reset_index()
            order_agg = order_agg.merge(order_date_map, on='订单ID', how='left')
            
            # 按周分组
            order_agg['周'] = order_agg[date_col].dt.to_period('W')
            
            # 获取最近两周的数据
            weeks = order_agg['周'].unique()
            if len(weeks) >= 2:
                weeks_sorted = sorted(weeks, reverse=True)
                current_week = weeks_sorted[0]
                previous_week = weeks_sorted[1]
                
                current_data = order_agg[order_agg['周'] == current_week]
                previous_data = order_agg[order_agg['周'] == previous_week]
                
                # 计算4个关键指标的环比
                # 1. 主流区订单数 (20-50元)
                def count_mainstream(data):
                    if '客单价' in data.columns:
                        return ((data['客单价'] >= 20) & (data['客单价'] < 50)).sum()
                    return 0
                
                current_mainstream = count_mainstream(current_data)
                previous_mainstream = count_mainstream(previous_data)
                mainstream_change = ((current_mainstream - previous_mainstream) / previous_mainstream * 100) if previous_mainstream > 0 else 0
                
                # 2. 平均客单价 (✅ 使用实收价格)
                current_avg_aov = current_data['实收价格'].mean() if len(current_data) > 0 else 0
                previous_avg_aov = previous_data['实收价格'].mean() if len(previous_data) > 0 else 0
                aov_change = ((current_avg_aov - previous_avg_aov) / previous_avg_aov * 100) if previous_avg_aov > 0 else 0
                
                # 3. 购物篮深度（需要后面计算SKU数）
                week_on_week_data = {
                    'mainstream_change': mainstream_change,
                    'aov_change': aov_change,
                    'has_data': True,
                    'current_week': current_week,  # 保存周信息
                    'previous_week': previous_week
                }
            else:
                week_on_week_data = {'has_data': False}
        else:
            week_on_week_data = {'has_data': False}
        
        # 🔧 【CRITICAL】确保订单总收入字段存在（必须在所有分析之前）
        # 因为后续很多分析都依赖这个字段，包括利润率、成本率、销售额占比等
        if '订单总收入' not in order_agg.columns:
            if '预计订单收入' in order_agg.columns:
                order_agg['订单总收入'] = order_agg['预计订单收入']
            else:
                # Fallback: 使用实收价格 + 其他可能的费用
                order_agg['订单总收入'] = order_agg['实收价格']
                    
                if '打包袋金额' in order_agg.columns:
                    order_agg['订单总收入'] += order_agg['打包袋金额']
                if '用户支付配送费' in order_agg.columns:
                    order_agg['订单总收入'] += order_agg['用户支付配送费']
        
        # ✅ 确保实收价格字段存在（客单价计算需要）
        if '实收价格' not in order_agg.columns:
            # Fallback: 使用预计订单收入或订单总收入
            if '预计订单收入' in order_agg.columns:
                order_agg['实收价格'] = order_agg['预计订单收入']
            else:
                order_agg['实收价格'] = order_agg['订单总收入']
        
        # ✅ 计算每个订单的客单价（使用实收价格）
        order_agg['客单价'] = order_agg['实收价格']
        
        # ========== 1. 客单价分布分析 ==========
        # 定义客单价区间（完整版：从0开始,包含所有订单）
        bins = [0, 10, 20, 30, 40, 50, 100, 200, float('inf')]
        labels = ['¥0-10', '¥10-20', '¥20-30', '¥30-40', '¥40-50', '¥50-100', '¥100-200', '¥200+']
        order_agg['客单价区间'] = pd.cut(order_agg['客单价'], bins=bins, labels=labels)
        
        # 统计各区间订单数和占比
        aov_dist = order_agg['客单价区间'].value_counts().sort_index()
        aov_dist_pct = (aov_dist / len(order_agg) * 100).round(1)
        
        # 🔧 修正：净利率应该用订单总收入作为分母（而非商品实售价）
        # 公式：净利率 = 订单实际利润 ÷ 订单总收入 × 100%
        # 原因：订单总收入包含打包费、配送费，是真实营收
        aov_profit_rate = order_agg.groupby('客单价区间').apply(
            lambda x: (x['订单实际利润'].sum() / x['订单总收入'].sum() * 100) if x['订单总收入'].sum() > 0 else 0
        )
        
        # 🔧 修正：成本率也应该用订单总收入作为分母
        # 兼容'商品采购成本'和'成本'两种字段名
        cost_field = '商品采购成本' if '商品采购成本' in order_agg.columns else '成本'
        aov_cost_rate = order_agg.groupby('客单价区间').apply(
            lambda x: (x[cost_field].sum() / x['订单总收入'].sum() * 100) if cost_field in x.columns and x['订单总收入'].sum() > 0 else 0
        )
        
        # ✅ 各区间亏损订单占比（识别异常）
        aov_loss_order_pct = order_agg.groupby('客单价区间').apply(
            lambda x: (x['订单实际利润'] < 0).sum() / len(x) * 100 if len(x) > 0 else 0
        )
        
        # ✅ 各区间平均利润额
        aov_avg_profit = order_agg.groupby('客单价区间')['订单实际利润'].mean()
        
        # 🔧 修正：销售额占比应该用订单总收入计算（而非商品实售价）
        print(f"🔍 [调试] 准备计算销售额占比, order_agg字段: {order_agg.columns.tolist()}", flush=True)
        print(f"🔍 [调试] '订单总收入' in columns: {'订单总收入' in order_agg.columns}", flush=True)
        
        if '订单总收入' not in order_agg.columns:
            print(f"⚠️⚠️⚠️ 致命错误: order_agg中没有'订单总收入'字段!", flush=True)
            raise ValueError("order_agg中缺少'订单总收入'字段")
        
        total_sales = order_agg['订单总收入'].sum()
        aov_sales_by_range = order_agg.groupby('客单价区间')['订单总收入'].sum()
        aov_sales_pct = (aov_sales_by_range / total_sales * 100).round(1)
        
        # ========== 2. 影响因素分析 ==========
        # 合并订单级数据和商品明细
        df_with_order = df.merge(
            order_agg[['订单ID', '客单价', '客单价区间']], 
            on='订单ID', 
            how='left'
        )
        
        # 计算每个订单的SKU数
        order_sku_count = df.groupby('订单ID')['商品名称'].nunique().reset_index()
        order_sku_count.columns = ['订单ID', 'SKU数']
        order_agg = order_agg.merge(order_sku_count, on='订单ID', how='left')
        
        # 📈 补充周环比数据：购物篮深度和单SKU订单占比
        if week_on_week_data.get('has_data', False):
            # 重新获取本周和上周数据（现在包含SKU数）
            current_week = week_on_week_data['current_week']
            previous_week = week_on_week_data['previous_week']
            current_data_with_sku = order_agg[order_agg['周'] == current_week]
            previous_data_with_sku = order_agg[order_agg['周'] == previous_week]
            
            # 3. 购物篮深度环比
            current_basket = current_data_with_sku['SKU数'].mean() if len(current_data_with_sku) > 0 else 0
            previous_basket = previous_data_with_sku['SKU数'].mean() if len(previous_data_with_sku) > 0 else 0
            basket_change = ((current_basket - previous_basket) / previous_basket * 100) if previous_basket > 0 else 0
            
            # 4. 单SKU订单占比环比
            current_single_sku = (current_data_with_sku['SKU数'] == 1).sum() / len(current_data_with_sku) * 100 if len(current_data_with_sku) > 0 else 0
            previous_single_sku = (previous_data_with_sku['SKU数'] == 1).sum() / len(previous_data_with_sku) * 100 if len(previous_data_with_sku) > 0 else 0
            single_sku_change = current_single_sku - previous_single_sku
            
            week_on_week_data['basket_change'] = basket_change
            week_on_week_data['single_sku_change'] = single_sku_change
        
        # ✅ 新增：各区间平均SKU单价
        order_agg['SKU单价'] = order_agg['客单价'] / order_agg['SKU数'].replace(0, 1)  # 避免除以0
        aov_avg_sku_price = order_agg.groupby('客单价区间')['SKU单价'].mean()
        
        # ✅ 新增：各区间热门时段（需要时段字段）
        if '时段' in df.columns:
            # 为订单添加时段信息（取订单中第一个商品的时段）
            order_period = df.groupby('订单ID')['时段'].first().reset_index()
            order_agg = order_agg.merge(order_period, on='订单ID', how='left')
            
            # 计算各区间的热门时段
            aov_hot_period = {}
            for label in labels:
                range_orders = order_agg[order_agg['客单价区间'] == label]
                if len(range_orders) > 0 and '时段' in range_orders.columns:
                    hot_period = range_orders['时段'].mode()
                    aov_hot_period[label] = hot_period[0] if len(hot_period) > 0 else "未知"
                else:
                    aov_hot_period[label] = "未知"
        else:
            aov_hot_period = {label: "未知" for label in labels}
        
        # ✅ 新增：各区间复购率（需要用户ID或手机号字段）
        user_field = None
        for field in ['用户ID', '手机号', '收货人电话', '用户手机']:
            if field in df.columns:
                user_field = field
                break
        
        if user_field:
            # 为订单添加用户信息
            order_user = df.groupby('订单ID')[user_field].first().reset_index()
            order_agg = order_agg.merge(order_user, on='订单ID', how='left')
            
            # 计算各区间复购率
            aov_repurchase_rate = {}
            for label in labels:
                range_orders = order_agg[order_agg['客单价区间'] == label]
                if len(range_orders) > 0 and user_field in range_orders.columns:
                    user_order_counts = range_orders.groupby(user_field)['订单ID'].count()
                    repurchase_users = (user_order_counts > 1).sum()
                    total_users = user_order_counts.count()
                    aov_repurchase_rate[label] = (repurchase_users / total_users * 100) if total_users > 0 else 0
                else:
                    aov_repurchase_rate[label] = 0
        else:
            aov_repurchase_rate = {label: 0 for label in labels}
        
        # 分高低客单价组分析
        high_aov_orders = order_agg[order_agg['客单价'] >= 40]  # 高客单价
        low_aov_orders = order_agg[order_agg['客单价'] < 40]   # 低客单价
        
        # 计算影响因素
        high_avg_sku = high_aov_orders['SKU数'].mean() if len(high_aov_orders) > 0 else 0
        low_avg_sku = low_aov_orders['SKU数'].mean() if len(low_aov_orders) > 0 else 0
        
        # 计算营销参与率 (有商家活动成本的订单)
        high_marketing_rate = (high_aov_orders['商家活动成本'] > 0).mean() * 100 if len(high_aov_orders) > 0 else 0
        low_marketing_rate = (low_aov_orders['商家活动成本'] > 0).mean() * 100 if len(low_aov_orders) > 0 else 0
        
        # 计算配送费占比 (✅ 使用实收价格作为分母)
        high_delivery_rate = (high_aov_orders['配送净成本'].sum() / high_aov_orders['实收价格'].sum() * 100) if len(high_aov_orders) > 0 and high_aov_orders['实收价格'].sum() > 0 else 0
        low_delivery_rate = (low_aov_orders['配送净成本'].sum() / low_aov_orders['实收价格'].sum() * 100) if len(low_aov_orders) > 0 and low_aov_orders['实收价格'].sum() > 0 else 0
        
        # ========== 3. 数据健康度检测 ==========
        # 计算数据覆盖天数
        if '日期' in df.columns:
            date_range = pd.to_datetime(df['日期'])
            min_date = date_range.min()
            max_date = date_range.max()
            total_days = (max_date - min_date).days + 1
            unique_days = date_range.dt.date.nunique()
            missing_days = total_days - unique_days
        else:
            total_days = 0
            unique_days = 0
            missing_days = 0
        
        # 检查关键字段完整性
        field_completeness = {}
        critical_fields = ['商品名称', '商品实售价', '订单ID', '销量']
        for field in critical_fields:
            if field in df.columns:
                non_null_count = df[field].notna().sum()
                field_completeness[field] = (non_null_count / len(df) * 100) if len(df) > 0 else 0
            else:
                field_completeness[field] = 0
        
        avg_completeness = sum(field_completeness.values()) / len(field_completeness) if field_completeness else 0
        
        # 检测数据异常
        anomaly_count = 0
        anomaly_details = []
        
        # 1. 价格异常(实售价 > 原价)
        if '实收价格' in df.columns and '商品原价' in df.columns:
            price_anomaly = df[df['实收价格'] > df['商品原价']]
            if len(price_anomaly) > 0:
                anomaly_count += len(price_anomaly)
                anomaly_details.append(f"价格异常: {len(price_anomaly)}条(实售价>原价)")
        
        # 2. 负利润订单
        if '净利润' in order_agg.columns:
            negative_profit = order_agg[order_agg['净利润'] < 0]
            if len(negative_profit) > 0:
                anomaly_count += len(negative_profit)
                anomaly_details.append(f"负利润订单: {len(negative_profit)}单")
        
        # 3. 超高客单价(>500)
        ultra_high_aov = order_agg[order_agg['客单价'] > 500]
        if len(ultra_high_aov) > 0:
            anomaly_count += len(ultra_high_aov)
            anomaly_details.append(f"超高客单价: {len(ultra_high_aov)}单(>¥500)")
        
        # 4. 零销量异常
        if '销量' in df.columns:
            zero_sales = df[(df['销量'] == 0) | (df['销量'].isna())]
            if len(zero_sales) > 0:
                anomaly_count += len(zero_sales)
                anomaly_details.append(f"零销量记录: {len(zero_sales)}条")
        
        # 环比可用性检查
        can_calculate_wow = week_on_week_data.get('has_data', False)
        
        # 数据健康度评分
        health_score = 0
        if avg_completeness >= 95:
            health_score += 40
        elif avg_completeness >= 80:
            health_score += 25
        
        if missing_days == 0:
            health_score += 30
        elif missing_days <= 3:
            health_score += 15
        
        if anomaly_count == 0:
            health_score += 30
        elif anomaly_count <= 10:
            health_score += 15
        
        if health_score >= 85:
            health_level = "优秀"
            health_color = "success"
        elif health_score >= 70:
            health_level = "良好"
            health_color = "info"
        elif health_score >= 50:
            health_level = "一般"
            health_color = "warning"
        else:
            health_level = "需改进"
            health_color = "danger"
        
        # ========== 4. 准备7天趋势数据 ==========
        trend_data = []
        if '日期' in df.columns and len(df) > 0:
            # 获取最近7天的数据
            df_with_date = df.copy()
            df_with_date['日期'] = pd.to_datetime(df_with_date['日期'])
            last_date = df_with_date['日期'].max()
            first_date = last_date - pd.Timedelta(days=6)
            recent_7days = df_with_date[df_with_date['日期'] >= first_date].copy()
            
            # 计算每天的指标
            for single_date in pd.date_range(first_date, last_date, freq='D'):
                day_data = recent_7days[recent_7days['日期'].dt.date == single_date.date()]
                if len(day_data) > 0:
                    # 聚合订单（使用实收价格计算客单价）
                    agg_dict = {'商品名称': 'nunique', '实收价格': 'sum'}
                    day_orders = day_data.groupby('订单ID').agg(agg_dict).reset_index()
                    day_orders.rename(columns={'实收价格': '客单价', '商品名称': 'SKU数'}, inplace=True)
                    
                    # 统计当天所有订单(不限价格区间)
                    total_orders = len(day_orders)
                    avg_aov = day_orders['客单价'].mean()
                    avg_basket = day_orders['SKU数'].mean()
                    
                    trend_data.append({
                        '日期': single_date.strftime('%m月%d日'),
                        '总订单': total_orders,
                        '平均客单价': round(avg_aov, 2),
                        '连带率': round(avg_basket, 2)
                    })
        
        # ========== 5. 准备价格带分布数据(用于环形图) ==========
        # 调试: 打印客单价统计信息
        print("\n" + "="*60)
        print("🔍 客单价区间分布详情 (启东门店):")
        print("="*60)
        print(f"📊 客单价统计:")
        print(f"   - 最小值: ¥{order_agg['客单价'].min():.2f}")
        print(f"   - 最大值: ¥{order_agg['客单价'].max():.2f}")
        print(f"   - 平均值: ¥{order_agg['客单价'].mean():.2f}")
        print(f"   - 中位数: ¥{order_agg['客单价'].median():.2f}")
        print(f"\n📈 各区间订单分布:")
        for idx, count in aov_dist.items():
            pct = count / len(order_agg) * 100
            print(f"   {idx}: {count}单 ({pct:.1f}%)")
        
        price_ring_data = []
        # 内环: 调整为4大价格组 (更精细的划分)
        low_price_count = len(order_agg[order_agg['客单价'] < 15])  # 0-15元 (流量区)
        medium_count = len(order_agg[(order_agg['客单价'] >= 15) & (order_agg['客单价'] < 30)])  # 15-30元 (主流区)
        mainstream_count = len(order_agg[(order_agg['客单价'] >= 30) & (order_agg['客单价'] < 50)])  # 30-50元 (利润区)
        high_price_count = len(order_agg[order_agg['客单价'] >= 50])  # 50+元 (高价区)
        
        print(f"\n💡 四大价格组业务化划分:")
        print(f"   🎯 流量区 <¥15: {low_price_count}单 ({low_price_count/len(order_agg)*100:.1f}%) - 引流低价商品")
        print(f"   🌟 主流区 ¥15-30: {medium_count}单 ({medium_count/len(order_agg)*100:.1f}%) - 日常高频商品")
        print(f"   💰 利润区 ¥30-50: {mainstream_count}单 ({mainstream_count/len(order_agg)*100:.1f}%) - 毛利贡献主力")
        print(f"   💎 高价区 ≥¥50: {high_price_count}单 ({high_price_count/len(order_agg)*100:.1f}%) - 高端/大单")
        print("="*60 + "\n")
        
        # 计算GMV
        low_gmv = order_agg[order_agg['客单价'] < 15]['客单价'].sum()
        medium_gmv = order_agg[(order_agg['客单价'] >= 15) & (order_agg['客单价'] < 30)]['客单价'].sum()
        mainstream_gmv = order_agg[(order_agg['客单价'] >= 30) & (order_agg['客单价'] < 50)]['客单价'].sum()
        high_gmv = order_agg[order_agg['客单价'] >= 50]['客单价'].sum()
        
        # ========== 5.5. 用户行为预测引擎 ==========
        # ⚡ 性能优化: 已完全删除"精准触达策略"、"分层路径挖掘"和"个性化推荐清单"模块
        # 这些模块计算复杂,影响页面加载速度,已全部移除
        
        # ========== 6. 构建UI组件 ==========
        return html.Div([
            # 数据健康度卡片 - 重新设计
            dbc.Card([
                dbc.CardBody([
                    # 标题行
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.I(className="bi bi-clipboard-data-fill me-2", style={'fontSize': '1.5rem', 'color': '#667eea'}),
                                html.H5("数据健康度", className="d-inline mb-0", style={'fontWeight': '600'})
                            ], className="mb-3")
                        ], md=12)
                    ]),
                    # 指标行
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.Div([
                                        html.P("健康评级", className="text-muted mb-1", style={'fontSize': '0.85rem'}),
                                        html.H4(health_level, className=f"text-{health_color} mb-1", style={'fontWeight': '700'}),
                                        html.Small(f"{health_score}分", className="text-muted")
                                    ], className="text-center")
                                ], className="p-2")
                            ], className="border-0 shadow-sm", style={'background': '#f8f9fa'})
                        ], md=2),
                        dbc.Col([
                            html.Div([
                                html.P("数据覆盖", className="text-muted mb-1", style={'fontSize': '0.85rem'}),
                                html.H5(f"{unique_days}/{total_days}天", className="mb-1", style={'fontWeight': '600'}),
                                html.Small(f"缺失{missing_days}天" if missing_days > 0 else "✓ 完整", 
                                         className=f"badge bg-{'warning' if missing_days > 0 else 'success'}")
                            ])
                        ], md=2),
                        dbc.Col([
                            html.Div([
                                html.P("字段完整率", className="text-muted mb-1", style={'fontSize': '0.85rem'}),
                                html.H5(f"{avg_completeness:.1f}%", className="mb-1", style={'fontWeight': '600'}),
                                html.Small(f"{'✓ 优秀' if avg_completeness >= 95 else '⚠ 需关注' if avg_completeness >= 80 else '✗ 较差'}", 
                                         className=f"badge bg-{'success' if avg_completeness >= 95 else 'warning' if avg_completeness >= 80 else 'danger'}")
                            ])
                        ], md=2),
                        dbc.Col([
                            html.Div([
                                html.P("数据异常", className="text-muted mb-1", style={'fontSize': '0.85rem'}),
                                html.H5(f"{anomaly_count}项", className="mb-1", style={'fontWeight': '600'}),
                                html.Small(f"{'✓ 无异常' if anomaly_count == 0 else '⚠ 需检查'}", 
                                         className=f"badge bg-{'success' if anomaly_count == 0 else 'warning'}")
                            ])
                        ], md=2),
                        dbc.Col([
                            html.Div([
                                html.P("环比计算", className="text-muted mb-1", style={'fontSize': '0.85rem'}),
                                html.H5(f"{'可用' if can_calculate_wow else '不可用'}", className="mb-1", style={'fontWeight': '600'}),
                                html.Small(f"{'✓ 数据充足' if can_calculate_wow else '需≥14天'}", 
                                         className=f"badge bg-{'success' if can_calculate_wow else 'secondary'}")
                            ])
                        ], md=2),
                        dbc.Col([
                            html.Div([
                                html.P("异常明细", className="text-muted mb-1", style={'fontSize': '0.85rem'}),
                                html.Div([
                                    html.Small(detail, className="d-block", style={'fontSize': '0.75rem'})
                                    for detail in anomaly_details[:2]
                                ]) if anomaly_details else html.Small("✓ 无异常", className="text-success")
                            ])
                        ], md=2)
                    ], className="g-3")
                ], className="p-4")
            ], className="shadow-sm mb-4", style={'border': '1px solid #e0e0e0', 'borderRadius': '8px'}),
            
            # 标题和导出按钮
            dbc.Row([
                dbc.Col([
                    html.H4("💰 客单价深度分析", className="mb-0")
                ], width=3),
                dbc.Col([
                    # 🆕 渠道筛选下拉菜单
                    dcc.Dropdown(
                        id='aov-analysis-channel-filter',
                        options=[{'label': '全部渠道', 'value': 'all'}],  # 设置初始选项
                        value='all',  # 明确默认值
                        placeholder='选择渠道',
                        clearable=False,
                        className="dash-bootstrap"
                    )
                ], width=3),
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button(
                            [html.I(className="fas fa-download me-1"), "基础分析"],
                            id="export-aov-analysis-btn",
                            color="success",
                            size="sm",
                            outline=False
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-chart-line me-1"), "趋势分析"],
                            id="export-aov-trend-btn",
                            color="primary",
                            size="sm",
                            outline=True
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-project-diagram me-1"), "关联分析"],
                            id="export-aov-association-btn",
                            color="info",
                            size="sm",
                            outline=True
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-users me-1"), "用户分层"],
                            id="export-aov-segment-btn",
                            color="warning",
                            size="sm",
                            outline=True
                        ),
                    ], size="sm", className="float-end")
                ], width=6, className="text-end")
            ], className="mb-3"),
            
            # 业务目的说明
            dbc.Alert([
                html.Div([
                    html.I(className="bi bi-lightbulb-fill me-2"),
                    html.Strong("📌 分析目的：", className="me-2"),
                    html.Span("客单价不是终点，而是提升GMV的关键路径。", className="me-2"),
                ], className="mb-2"),
                html.Ul([
                    html.Li([
                        html.Strong("发现增长机会：", className="text-primary me-1"),
                        "找出各价格区间的畅销商品与潜力商品，设计组合套餐和凑单策略"
                    ], className="small mb-1"),
                    html.Li([
                        html.Strong("诊断动销异常：", className="text-warning me-1"),
                        "对比不同渠道和时间段，识别商品动销下滑原因，及时调整运营策略"
                    ], className="small mb-1"),
                    html.Li([
                        html.Strong("优化用户体验：", className="text-success me-1"),
                        "通过购物篮分析，推荐合适的第N件商品，帮助用户完成购物，提升满意度"
                    ], className="small mb-0"),
                ], className="mb-0", style={'paddingLeft': '20px', 'marginBottom': '0'})
            ], color="info", className="mb-3", style={'fontSize': '0.9rem'}),
            
            # 📊 关键指标环比趋势（新增）
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Small("主流区订单", className="text-muted d-block", style={'fontSize': '0.75rem'}),
                                html.H5([
                                    f"{int(aov_dist.get('¥10-20', 0) + aov_dist.get('¥20-30', 0))}单",
                                ], className="mb-1", style={'fontWeight': '700'}),
                                html.Small("(¥15-30元)", className="text-muted d-block", style={'fontSize': '0.65rem'}),
                                (html.Span(
                                    f"{'📈' if week_on_week_data.get('mainstream_change', 0) > 0 else '📉'} 周环比{week_on_week_data.get('mainstream_change', 0):.1f}%",
                                    className=f"badge {'bg-success' if week_on_week_data.get('mainstream_change', 0) > 0 else 'bg-danger'}",
                                    style={'fontSize': '0.7rem'}
                                ) if week_on_week_data.get('has_data', False) else html.Span("数据不足", className="badge bg-secondary", style={'fontSize': '0.7rem'}))
                            ])
                        ], className="p-3")
                    ], className="shadow-sm")
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Small("平均客单价", className="text-muted d-block", style={'fontSize': '0.75rem'}),
                                html.H5([
                                    f"¥{order_agg['客单价'].mean():.2f}",
                                ], className="mb-1", style={'fontWeight': '700'}),
                                (html.Span(
                                    f"{'📈' if week_on_week_data.get('aov_change', 0) > 0 else '📉'} 周环比{week_on_week_data.get('aov_change', 0):.1f}%",
                                    className=f"badge {'bg-success' if week_on_week_data.get('aov_change', 0) > 0 else 'bg-danger'}",
                                    style={'fontSize': '0.7rem'}
                                ) if week_on_week_data.get('has_data', False) else html.Span("数据不足", className="badge bg-secondary", style={'fontSize': '0.7rem'}))
                            ])
                        ], className="p-3")
                    ], className="shadow-sm")
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Small("购物篮深度", className="text-muted d-block", style={'fontSize': '0.75rem'}),
                                html.H5([
                                    f"{order_agg['SKU数'].mean():.1f}件",
                                ], className="mb-1", style={'fontWeight': '700'}),
                                (html.Span(
                                    f"{'📈' if week_on_week_data.get('basket_change', 0) > 0 else '📉'} 周环比{week_on_week_data.get('basket_change', 0):.1f}%",
                                    className=f"badge {'bg-success' if week_on_week_data.get('basket_change', 0) > 0 else 'bg-danger'}",
                                    style={'fontSize': '0.7rem'}
                                ) if week_on_week_data.get('has_data', False) else html.Span("数据不足", className="badge bg-secondary", style={'fontSize': '0.7rem'}))
                            ])
                        ], className="p-3")
                    ], className="shadow-sm")
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Small("单SKU订单", className="text-muted d-block", style={'fontSize': '0.75rem'}),
                                html.H5([
                                    f"{((order_agg['SKU数'] == 1).sum() / len(order_agg) * 100):.1f}%",
                                ], className="mb-1", style={'fontWeight': '700'}),
                                (html.Span(
                                    f"{'⬆️' if week_on_week_data.get('single_sku_change', 0) > 0 else '⬇️'}{abs(week_on_week_data.get('single_sku_change', 0)):.1f}pp",
                                    className=f"badge {'bg-warning text-dark' if week_on_week_data.get('single_sku_change', 0) > 0 else 'bg-success'}",
                                    style={'fontSize': '0.7rem'}
                                ) if week_on_week_data.get('has_data', False) else 
                                (html.Span("⚠️ 凑单机会", className="badge bg-warning text-dark", style={'fontSize': '0.7rem'}) if (order_agg['SKU数'] == 1).sum() / len(order_agg) > 0.25 else html.Span("✅ 健康", className="badge bg-success", style={'fontSize': '0.7rem'})))
                            ])
                        ], className="p-3")
                    ], className="shadow-sm")
                ], md=3),
            ], className="mb-3"),
            
            # 🚨 异常预警（根据数据动态显示）
            html.Div([
                dbc.Alert([
                    html.Div([
                        html.I(className="bi bi-exclamation-triangle-fill me-2"),
                        html.Strong("异常预警"),
                    ], className="mb-2"),
                    html.Ul([
                        html.Li([
                            f"单SKU订单占比 {((order_agg['SKU数'] == 1).sum() / len(order_agg) * 100):.1f}%，建议推荐凑单商品提升客单价"
                        ], className="small") if (order_agg['SKU数'] == 1).sum() / len(order_agg) > 0.3 else None,
                        html.Li([
                            f"低价区（0-20元）订单占比 {(aov_dist.get('¥10-20', 0) / len(order_agg) * 100):.1f}%，关注用户消费升级机会"
                        ], className="small") if (aov_dist.get('¥10-20', 0) / len(order_agg)) > 0.25 else None,
                    ], className="mb-0", style={'paddingLeft': '20px'})
                ], color="warning", className="mb-3")
            ]) if ((order_agg['SKU数'] == 1).sum() / len(order_agg) > 0.3) or ((aov_dist.get('¥10-20', 0) / len(order_agg)) > 0.25) else html.Div(),
            
            # 客单价分布 - 使用inline样式的现代化卡片
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 客单价分布", className="bg-light"),
                        dbc.CardBody([
                            dbc.Row(
                                # 🔥 使用inline样式 + JavaScript实现悬停效果
                                [dbc.Col([
                                    html.Div([
                                        html.Div([
                                            html.H6(
                                                label, 
                                                className="text-muted mb-2", 
                                                style={'fontSize': '0.95rem', 'fontWeight': '500'}
                                            ),
                                            html.H4(
                                                f"{int(aov_dist.get(label, 0))}单", 
                                                className="text-primary mb-2 card-value",
                                                style={
                                                    'fontSize': '1.85rem', 
                                                    'fontWeight': '700',
                                                    'letterSpacing': '-0.5px',
                                                    'transition': 'all 0.3s ease'
                                                }
                                            ),
                                            html.P([
                                                html.Span(
                                                    f"{aov_dist_pct.get(label, 0):.1f}%", 
                                                    className="badge bg-secondary me-2 card-badge",
                                                    style={'fontSize': '0.8rem', 'transition': 'all 0.3s ease'}
                                                ),
                                                # ✅ 优化：显示净利率，添加成本率和异常提示
                                                html.Span([
                                                    f"净利率 {aov_profit_rate.get(label, 0):.1f}%",
                                                    # 如果净利率异常高（>50%）或成本率异常低（<30%），添加提示
                                                    html.Span(" ⚠️", className="text-warning", title=f"成本率{aov_cost_rate.get(label, 0):.1f}% 请核实数据准确性") 
                                                    if (aov_profit_rate.get(label, 0) > 50 or aov_cost_rate.get(label, 0) < 30) and aov_cost_rate.get(label, 0) > 0
                                                    else None
                                                ], 
                                                    className="small text-muted card-profit",
                                                    style={'fontSize': '0.85rem', 'transition': 'all 0.3s ease'},
                                                    title=f"净利润÷营收。成本率{aov_cost_rate.get(label, 0):.1f}%，亏损订单{aov_loss_order_pct.get(label, 0):.0f}%"
                                                )
                                            ], className="mb-2"),
                                            # ✅ 优化：每个指标前添加清晰定义，左对齐展示
                                            html.Div([
                                                # 单均利润
                                                html.Div([
                                                    html.Small("单均利润：", className="text-muted me-1", style={'fontSize': '0.75rem'}),
                                                    html.Small([
                                                        "💰 ",
                                                        html.Span(f"¥{aov_avg_profit.get(label, 0):.2f}", className="fw-bold text-success"),
                                                        "/单"
                                                    ], style={'fontSize': '0.85rem'})
                                                ], className="mb-1", style={'textAlign': 'left'}),
                                                
                                                # 销售额占比（改名）
                                                html.Div([
                                                    html.Small("销售额占比：", className="text-muted me-1", style={'fontSize': '0.75rem'}),
                                                    html.Small([
                                                        "📊 ",
                                                        html.Span(f"{aov_sales_pct.get(label, 0):.1f}%", className="fw-bold text-primary")
                                                    ], style={'fontSize': '0.85rem'})
                                                ], className="mb-1", style={'textAlign': 'left'}),
                                                
                                                # 购物篮
                                                html.Div([
                                                    html.Small("购物篮：", className="text-muted me-1", style={'fontSize': '0.75rem'}),
                                                    html.Small([
                                                        "🛒 平均",
                                                        html.Span(f"{order_agg[order_agg['客单价区间']==label]['SKU数'].mean():.1f}", className="fw-bold text-info") if len(order_agg[order_agg['客单价区间']==label]) > 0 else html.Span("0", className="fw-bold text-info"),
                                                        "件/单"
                                                    ], style={'fontSize': '0.85rem'})
                                                ], className="mb-1", style={'textAlign': 'left'}),
                                                
                                                # 复购率（如果有数据）
                                                html.Div([
                                                    html.Small("复购率：", className="text-muted me-1", style={'fontSize': '0.75rem'}),
                                                    html.Small([
                                                        "🔄 ",
                                                        html.Span(f"{aov_repurchase_rate.get(label, 0):.0f}%", className="fw-bold text-warning")
                                                    ], style={'fontSize': '0.85rem'})
                                                ], className="mb-1", style={'textAlign': 'left'}) if aov_repurchase_rate.get(label, 0) > 0 else None,
                                                
                                                # 高峰时段（如果有数据）
                                                html.Div([
                                                    html.Small("高峰时段：", className="text-muted me-1", style={'fontSize': '0.75rem'}),
                                                    html.Small([
                                                        "⏰ ",
                                                        html.Span(f"{aov_hot_period.get(label, '未知')}", className="fw-bold text-secondary")
                                                    ], style={'fontSize': '0.85rem'})
                                                ], style={'textAlign': 'left'}) if aov_hot_period.get(label, '未知') != '未知' else None
                                            ], style={'paddingLeft': '1rem', 'paddingRight': '1rem'})
                                        ], style={
                                            'padding': '1.5rem',
                                            'textAlign': 'center',
                                            'height': '100%',
                                            'display': 'flex',
                                            'flexDirection': 'column',
                                            'justifyContent': 'center'
                                        })
                                    ], 
                                    className="modern-card text-center shadow-sm"  # 🎨 改用modern-card，享受悬停动画
                                )
                                ], md=3, lg=3, xl=3)
                                for label in labels],
                                className="g-3"
                            )
                        ])
                    ], className="shadow-sm mb-3")
                ], md=12)
            ]),
            
            # 影响因素分析 - 单独一行
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🔍 影响因素分析", className="bg-light"),
                        dbc.CardBody([
                            html.Table([
                                html.Thead([
                                    html.Tr([
                                        html.Th("因素", className="text-muted small"),
                                        html.Th("高客单价(≥¥40)", className="text-muted small"),
                                        html.Th("低客单价(<¥40)", className="text-muted small"),
                                        html.Th("差异", className="text-muted small")
                                    ])
                                ]),
                                html.Tbody([
                                    html.Tr([
                                        html.Td("平均SKU数", className="small"),
                                        html.Td(f"{high_avg_sku:.1f}个", className="small fw-bold"),
                                        html.Td(f"{low_avg_sku:.1f}个", className="small"),
                                        html.Td([
                                            html.Span(
                                                f"+{((high_avg_sku - low_avg_sku) / low_avg_sku * 100):.0f}%" if low_avg_sku > 0 else "N/A",
                                                className="badge bg-success small"
                                            )
                                        ])
                                    ]),
                                    html.Tr([
                                        html.Td("配送费占比", className="small"),
                                        html.Td(f"{high_delivery_rate:.1f}%", className="small fw-bold"),
                                        html.Td(f"{low_delivery_rate:.1f}%", className="small"),
                                        html.Td([
                                            html.Span(
                                                f"{(high_delivery_rate - low_delivery_rate):.1f}%",
                                                className=f"badge bg-{'success' if high_delivery_rate < low_delivery_rate else 'warning'} small"
                                            )
                                        ])
                                    ]),
                                    html.Tr([
                                        html.Td("营销活动参与率", className="small"),
                                        html.Td(f"{high_marketing_rate:.1f}%", className="small fw-bold"),
                                        html.Td(f"{low_marketing_rate:.1f}%", className="small"),
                                        html.Td([
                                            html.Span(
                                                f"{(high_marketing_rate - low_marketing_rate):.1f}%",
                                                className=f"badge bg-{'warning' if high_marketing_rate > low_marketing_rate else 'info'} small"
                                            )
                                        ])
                                    ])
                                ])
                            ], className="table table-sm table-borderless mb-0")
                        ])
                    ], className="shadow-sm mb-3")
                ], md=12)  # ✅ 修改：从md=6改为md=12，占满整行
            ]),
            
            # 💡 快速洞察卡片（新增）
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-stars me-2"),
                            "快速洞察"
                        ], className="bg-gradient", style={'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 'color': 'white'}),
                        dbc.CardBody([
                            dbc.Row([
                                # 洞察1: 凑单机会
                                dbc.Col([
                                    html.Div([
                                        html.H6("🎯 凑单机会", className="text-primary mb-2"),
                                        html.P([
                                            f"{((order_agg['SKU数'] == 1).sum() / len(order_agg) * 100):.1f}% 的订单只买1件商品",
                                            html.Br(),
                                            html.Small(f"推荐凑单预计可增收约 {((order_agg['SKU数'] == 1).sum() * order_agg['客单价'].mean() * 0.15):.0f}元", className="text-muted")
                                        ], className="small mb-0")
                                    ])
                                ], md=4, className="border-end"),
                                # 洞察2: 渠道冠军
                                dbc.Col([
                                    html.Div([
                                        html.H6("🏆 渠道表现", className="text-success mb-2"),
                                        (lambda: (
                                            html.P([
                                                f"{channel_avg.idxmax()} 平均客单价¥{channel_avg.max():.2f}",
                                                html.Br(),
                                                html.Small("最高客单价渠道", className="text-muted")
                                            ], className="small mb-0")
                                            if '渠道' in order_agg.columns and len(channel_avg := order_agg.groupby('渠道')['客单价'].mean()) > 0
                                            else html.P("渠道数据不可用", className="small text-muted")
                                        ))()
                                    ])
                                ], md=4, className="border-end"),
                                # 洞察3: 高价值商品
                                dbc.Col([
                                    html.Div([
                                        html.H6("💎 价值洼地", className="text-warning mb-2"),
                                        html.P([
                                            f"主流区（¥15-30）占比 {((aov_dist.get('¥10-20', 0) + aov_dist.get('¥20-30', 0)) / len(order_agg) * 100 if len(order_agg) > 0 else 0):.1f}%",
                                            html.Br(),
                                            html.Small("提升主流区占比可增加GMV", className="text-muted")
                                        ], className="small mb-0")
                                    ])
                                ], md=4),
                            ])
                        ])
                    ], className="shadow-sm mb-3")
                ], md=12)
            ]),
            
            # 📊 7天趋势图 & 价格带分布环形图（使用ECharts）
            dbc.Row([
                # 左侧: 7天趋势折线图
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📈 7天关键指标趋势", className="bg-light"),
                        dbc.CardBody([
                            DashECharts(
                                option={
                                    'title': {'text': '', 'left': 'center'},
                                    'tooltip': {
                                        'trigger': 'axis',
                                        'backgroundColor': 'rgba(255, 255, 255, 0.96)',
                                        'borderColor': '#e0e0e0',
                                        'borderWidth': 1,
                                        'padding': [10, 15],
                                        'textStyle': {'color': '#333', 'fontSize': 13}
                                    },
                                    'legend': {'data': ['订单数', '平均客单价(¥)', '连带率(件)'], 'top': '5%'},
                                    'grid': {'left': '8%', 'right': '8%', 'top': '18%', 'bottom': '12%', 'containLabel': True},
                                    'xAxis': {
                                        'type': 'category',
                                        'data': [item['日期'] for item in trend_data],
                                        'axisLabel': {'fontSize': 11, 'color': '#666'}
                                    },
                                    'yAxis': [
                                        {'type': 'value', 'name': '订单数', 'position': 'left', 'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.08)'}}, 'axisLabel': {'fontSize': 11, 'color': '#666'}},
                                        {'type': 'value', 'name': '客单价/连带率', 'position': 'right', 'splitLine': {'show': False}, 'axisLabel': {'fontSize': 11, 'color': '#666'}}
                                    ],
                                    'series': [
                                        {
                                            'name': '订单数',
                                            'type': 'line',
                                            'data': [item['总订单'] for item in trend_data],
                                            'smooth': True,
                                            'symbol': 'circle',
                                            'symbolSize': 8,
                                            'lineStyle': {'width': 3, 'color': '#667eea'},
                                            'itemStyle': {'color': '#667eea', 'borderWidth': 2, 'borderColor': '#fff'},
                                            'areaStyle': {'color': {'type': 'linear', 'x': 0, 'y': 0, 'x2': 0, 'y2': 1, 'colorStops': [{'offset': 0, 'color': 'rgba(102, 126, 234, 0.3)'}, {'offset': 1, 'color': 'rgba(102, 126, 234, 0.05)'}]}}
                                        },
                                        {
                                            'name': '平均客单价(¥)',
                                            'type': 'line',
                                            'yAxisIndex': 1,
                                            'data': [item['平均客单价'] for item in trend_data],
                                            'smooth': True,
                                            'symbol': 'diamond',
                                            'symbolSize': 8,
                                            'lineStyle': {'width': 3, 'color': '#f093fb', 'type': 'dotted'},
                                            'itemStyle': {'color': '#f093fb', 'borderWidth': 2, 'borderColor': '#fff'}
                                        },
                                        {
                                            'name': '连带率(件)',
                                            'type': 'line',
                                            'yAxisIndex': 1,
                                            'data': [item['连带率'] for item in trend_data],
                                            'smooth': True,
                                            'symbol': 'triangle',
                                            'symbolSize': 8,
                                            'lineStyle': {'width': 3, 'color': '#4facfe', 'type': 'dashed'},
                                            'itemStyle': {'color': '#4facfe', 'borderWidth': 2, 'borderColor': '#fff'}
                                        }
                                    ],
                                    'animationEasing': 'cubicOut',
                                    'animationDuration': 1200
                                } if len(trend_data) > 0 else {
                                    'title': {'text': '需要至少7天数据', 'left': 'center', 'top': 'center', 'textStyle': {'color': '#999', 'fontSize': 14}}
                                },
                                style={'height': '350px', 'width': '100%'}
                            ) if len(trend_data) > 0 else html.Div([
                                html.I(className="bi bi-info-circle me-2"),
                                "需要至少7天数据才能显示趋势"
                            ], className="text-muted text-center p-5")
                        ], className="p-2")
                    ], className="shadow-sm")
                ], md=7),
                
                # 右侧: 价格带分布环形图
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🍩 价格带分布", className="bg-light"),
                        dbc.CardBody([
                            DashECharts(
                                option={
                                    'tooltip': {'trigger': 'item', 'formatter': '{b}: {c}单 ({d}%)', 'backgroundColor': 'rgba(255, 255, 255, 0.96)', 'borderColor': '#e0e0e0', 'borderWidth': 1},
                                    'legend': {'orient': 'horizontal', 'bottom': '5%', 'left': 'center'},
                                    'series': [{
                                        'name': '订单分布',
                                        'type': 'pie',
                                        'radius': ['40%', '70%'],
                                        'center': ['50%', '45%'],
                                        'data': [
                                            {'name': '流量区<¥15', 'value': low_price_count, 'itemStyle': {'color': '#fbc2eb'}},
                                            {'name': '主流区¥15-30', 'value': medium_count, 'itemStyle': {'color': '#a8edea'}},
                                            {'name': '利润区¥30-50', 'value': mainstream_count, 'itemStyle': {'color': '#667eea'}},
                                            {'name': '高价区≥¥50', 'value': high_price_count, 'itemStyle': {'color': '#f093fb'}}
                                        ],
                                        'itemStyle': {'borderRadius': 10, 'borderColor': '#fff', 'borderWidth': 2},
                                        'label': {'show': True, 'formatter': '{b}\\n{d}%', 'fontSize': 11, 'fontWeight': 'bold'},
                                        'emphasis': {'itemStyle': {'shadowBlur': 20, 'shadowColor': 'rgba(0, 0, 0, 0.5)'}, 'label': {'show': True, 'fontSize': 14}},
                                        'animationType': 'scale',
                                        'animationEasing': 'cubicOut'
                                    }],
                                    'graphic': [{
                                        'type': 'text',
                                        'left': 'center',
                                        'top': '42%',
                                        'style': {'text': f'{len(order_agg)}单', 'fontSize': 20, 'fontWeight': 'bold', 'fill': '#667eea', 'textAlign': 'center'}
                                    }, {
                                        'type': 'text',
                                        'left': 'center',
                                        'top': '52%',
                                        'style': {'text': '总订单', 'fontSize': 12, 'fill': '#999', 'textAlign': 'center'}
                                    }]
                                },
                                style={'height': '350px', 'width': '100%'}
                            )
                        ], className="p-2")
                    ], className="shadow-sm")
                ], md=5)
            ], className="mb-4"),
            
            # ⚡ 性能优化: 已完全删除"用户行为预测引擎"模块(包括精准触达策略和ROI预测)
            # 原因: 该模块计算复杂,包含商品共现分析、推荐策略生成等,严重影响页面加载速度

            
            # 业务洞察和建议
            dbc.Row([
                dbc.Col([
                    dbc.Alert([
                        html.I(className="bi bi-lightbulb-fill me-2"),
                        html.Strong("💡 智能经营建议："),
                        html.Ul([
                            html.Li([
                                "🎯 套餐组合策略：高客单价订单平均包含 ",
                                html.Strong(f"{high_avg_sku:.1f}个SKU", className="text-primary"),
                                f"，比低客单价订单多 {((high_avg_sku - low_avg_sku) / low_avg_sku * 100):.0f}%" if low_avg_sku > 0 else "",
                                "，建议推出套餐优惠"
                            ], className="small mb-2"),
                            html.Li([
                                f"📦 配送费优化：低客单价订单配送费占比高达 {low_delivery_rate:.1f}%，"
                                f"建议设置起送价或配送费梯度"
                            ], className="small mb-2") if low_delivery_rate > 10 else None,
                            html.Li([
                                f"🎁 营销精准化：避免过度促销，当前低客单价订单营销参与率 {low_marketing_rate:.1f}%，"
                                f"可能吸引了价格敏感用户"
                            ], className="small mb-2") if low_marketing_rate > high_marketing_rate else None,
                            # 🔄 基于时序分析的推荐
                            # ⚡ 性能优化: 已删除复购提醒策略和智能推送时机建议
                            # 原因: 依赖的sequential_patterns和repurchase_intervals变量已删除
                        ], className="mb-0", style={'paddingLeft': '20px'})
                    ], color="info", className="mb-0")
                ], md=12)
            ]),
        
            # Download组件
            dcc.Download(id="download-aov-analysis"),
            dcc.Download(id="download-aov-trend"),
            dcc.Download(id="download-aov-association"),
            dcc.Download(id="download-aov-segment")
        ])
        
    except Exception as e:
        print(f"❌ 客单价分析失败: {e}")
        import traceback
        traceback.print_exc()
        return html.Div()


# ==================== 健康度预警组件(基于业务逻辑) ====================
def _create_health_warnings(total_sales: float, total_profit: float, order_agg: pd.DataFrame) -> list:
    """
    创建健康度预警组件
    
    Args:
        total_sales: 总销售额
        total_profit: 总利润
        order_agg: 订单聚合数据
    
    Returns:
        健康度预警组件列表
    """
    if not BUSINESS_CONTEXT_AVAILABLE:
        return []
    
    # 计算核心指标
    profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
    
    # 计算成本占比
    product_cost = order_agg['商品采购成本'].sum() if '商品采购成本' in order_agg.columns else 0
    logistics_cost = order_agg['配送净成本'].sum() if '配送净成本' in order_agg.columns else 0  # ✅ 使用配送净成本
    if '平台服务费' in order_agg.columns:
        platform_cost = order_agg['平台服务费'].sum()
    else:
        platform_cost = order_agg['平台佣金'].sum() if '平台佣金' in order_agg.columns else 0
    marketing_cost = order_agg['商家活动成本'].sum() if '商家活动成本' in order_agg.columns else 0
    
    product_cost_rate = (product_cost / total_sales * 100) if total_sales > 0 else 0
    logistics_cost_rate = (logistics_cost / total_sales * 100) if total_sales > 0 else 0
    platform_cost_rate = (platform_cost / total_sales * 100) if total_sales > 0 else 0
    marketing_cost_rate = (marketing_cost / total_sales * 100) if total_sales > 0 else 0
    
    # ✨ 新增: 计算商品角色占比(基于毛利率的简单分类)
    # 从GLOBAL_DATA获取商品级数据来分类
    try:
        if GLOBAL_DATA is not None and '商品名称' in GLOBAL_DATA.columns:
            df = GLOBAL_DATA.copy()
            
            # ✅ 修复：检查价格和成本字段
            price_col = None
            if '实收价格' in df.columns:
                price_col = '实收价格'
            else:
                price_col = '实收价格'  # 必须存在
            
            cost_col = '商品采购成本' if '商品采购成本' in df.columns else None
            
            # 计算每个商品的毛利率
            if price_col and cost_col:
                # 按商品聚合
                agg_dict = {
                    price_col: 'sum',
                    cost_col: 'sum'
                }
                if '月售' in df.columns:
                    agg_dict['月售'] = 'sum'
                    
                product_stats = df.groupby('商品名称').agg(agg_dict).reset_index()
                
                # 计算毛利率
                product_stats['毛利率'] = (
                    (product_stats[price_col] - product_stats[cost_col]) / 
                    product_stats[price_col] * 100
                ).fillna(0)
                
                # 商品角色分类(基于业务规则)
                # 流量品: 毛利率<15%
                # 利润品: 毛利率>30%
                # 形象品: 15% <= 毛利率 <= 30%
                total_products = len(product_stats)
                流量品数 = len(product_stats[product_stats['毛利率'] < 15])
                利润品数 = len(product_stats[product_stats['毛利率'] > 30])
                形象品数 = len(product_stats[(product_stats['毛利率'] >= 15) & (product_stats['毛利率'] <= 30)])
                
                流量品占比 = (流量品数 / total_products * 100) if total_products > 0 else 0
                利润品占比 = (利润品数 / total_products * 100) if total_products > 0 else 0
                形象品占比 = (形象品数 / total_products * 100) if total_products > 0 else 0
                
                # 🔍 调试日志
                print(f"\n{'='*80}")
                print(f"📊 商品角色分类统计")
                print(f"{'='*80}")
                print(f"总商品数: {total_products}")
                print(f"流量品: {流量品数} 个 ({流量品占比:.1f}%) - 毛利率<15%")
                print(f"利润品: {利润品数} 个 ({利润品占比:.1f}%) - 毛利率>30%")
                print(f"形象品: {形象品数} 个 ({形象品占比:.1f}%) - 毛利率15-30%")
                print(f"{'='*80}\n")
            else:
                流量品占比 = 0
                利润品占比 = 0
                形象品占比 = 0
        else:
            流量品占比 = 0
            利润品占比 = 0
            形象品占比 = 0
    except Exception as e:
        print(f"⚠️ 商品角色分类计算失败: {e}")
        流量品占比 = 0
        利润品占比 = 0
        形象品占比 = 0
    
    # 构建指标字典(包含商品角色占比)
    metrics = {
        '利润率': profit_rate,
        '商品成本占比': product_cost_rate,
        '履约成本占比': logistics_cost_rate,
        '平台成本占比': platform_cost_rate,
        '营销成本占比': marketing_cost_rate,
        '流量品占比': 流量品占比,
        '利润品占比': 利润品占比,
        '形象品占比': 形象品占比
    }
    
    # 调用业务上下文模块获取预警
    try:
        warnings = get_health_warnings(metrics)
    except Exception as e:
        print(f"⚠️ 健康度预警计算失败: {e}")
        warnings = []
    
    # 如果无预警,返回健康状态卡片
    if not warnings:
        return [dbc.Alert([
            html.I(className="bi bi-check-circle-fill me-2", style={'fontSize': '1.2rem'}),
            html.Strong("✅ 经营健康度良好"),
            html.Br(),
            html.Small(f"利润率 {profit_rate:.1f}% 处于健康范围 (8-15%)", className="text-muted")
        ], color="success", className="mb-4")]
    
    # 有预警时,生成预警卡片
    warning_cards = []
    
    # 预警标题
    warning_cards.append(dbc.Alert([
        html.I(className="bi bi-exclamation-triangle-fill me-2", style={'fontSize': '1.3rem'}),
        html.Strong(f"⚠️ 发现 {len(warnings)} 项经营风险", style={'fontSize': '1.1rem'}),
        html.Br(),
        html.Small("请立即关注以下指标异常,采取措施恢复健康状态", className="mt-2")
    ], color="warning", className="mb-3"))
    
    # 预警详情
    for idx, warning in enumerate(warnings, 1):
        # ✨ 修复: 使用正确的键名映射(来自ai_business_context.py)
        severity = warning.get('级别', '警告')
        indicator = warning.get('指标', '未知指标')
        current_value = warning.get('当前值', 'N/A')
        threshold = warning.get('阈值', 'N/A')
        problem = warning.get('问题', '未知问题')
        suggestion = warning.get('建议', '请咨询运营专家')
        
        severity_color = {
            '严重': 'danger',
            '警告': 'warning',
            '提示': 'info'
        }.get(severity, 'warning')
        
        severity_icon = {
            '严重': 'bi-x-circle-fill',
            '警告': 'bi-exclamation-triangle-fill',
            '提示': 'bi-info-circle-fill'
        }.get(severity, 'bi-exclamation-triangle-fill')
        
        warning_cards.append(dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className=f"bi {severity_icon} me-2", style={'fontSize': '1.1rem'}),
                    html.Strong(f"{idx}. {indicator}", style={'fontSize': '1rem'})
                ], className="mb-2"),
                html.Div([
                    html.Span("当前: ", className="text-muted small me-1"),
                    html.Span(current_value, className="text-danger fw-bold small me-3"),
                    html.Span("基准: ", className="text-muted small me-1"),
                    html.Span(threshold, className="text-success small")
                ], className="mb-2"),
                html.P(problem, className="mb-2 text-muted small"),
                html.Div([
                    html.Strong("💡 建议: ", className="me-1"),
                    html.Span(suggestion, className="small")
                ])
            ])
        ], color=severity_color, outline=True, className="mb-2"))
    
    return warning_cards


# ==================== 成本优化分析核心函数 ====================
def analyze_cost_optimization(df_raw: pd.DataFrame, order_agg: pd.DataFrame) -> Dict[str, Any]:
    """
    成本优化分析：针对3项成本预警提供深度分析
    
    Args:
        df_raw: 原始订单数据（包含商品名称等字段）
        order_agg: 订单聚合数据（用于计算总体指标）
        
    Returns:
        包含成本分析结果的字典
    """
    if df_raw is None or len(df_raw) == 0:
        return {
            'product_cost_analysis': None,
            'logistics_cost_analysis': None,
            'marketing_cost_analysis': None
        }
    
    df = df_raw.copy()
    
    # ========== 1. 商品成本分析 ==========
    product_cost_analysis = {}
    
    # 统一使用实收价格
    price_col = '实收价格'
    cost_col = '商品采购成本'
    
    if price_col not in df.columns or cost_col not in df.columns:
        return {
            'product_cost_analysis': None,
            'logistics_cost_analysis': None,
            'marketing_cost_analysis': None
        }
    
    # 按商品聚合
    agg_dict = {
        price_col: 'sum',
        cost_col: 'sum'
    }
    if '月售' in df.columns:
        agg_dict['月售'] = 'sum'
        
    product_stats = df.groupby('商品名称').agg(agg_dict).reset_index()
    
    # 计算毛利率和成本占比
    product_stats['毛利率'] = (
        (product_stats[price_col] - product_stats[cost_col]) / 
        product_stats[price_col] * 100
    )
    product_stats['成本占比'] = (
        product_stats[cost_col] / product_stats[price_col] * 100
    )
    
    # 识别高成本低毛利商品（成本占比>70%且销量较高）
    if '月售' in product_stats.columns:
        high_cost_products = product_stats[
            (product_stats['成本占比'] > 70) & 
            (product_stats['月售'] > product_stats['月售'].quantile(0.5))
        ].sort_values(price_col, ascending=False).head(20)
    else:
        high_cost_products = product_stats[
            product_stats['成本占比'] > 70
        ].sort_values(price_col, ascending=False).head(20)
    
    product_cost_analysis['high_cost_products'] = high_cost_products
    product_cost_analysis['avg_cost_rate'] = product_stats['成本占比'].mean()
    product_cost_analysis['total_products'] = len(product_stats)
    product_cost_analysis['problem_products'] = len(high_cost_products)
    
    # ========== 2. 履约成本分析 ==========
    logistics_cost_analysis = {}
    
    # 计算履约成本相关指标
    total_sales = df[price_col].sum()
    
    # 🔄 计算履约净成本: 实际物流配送费 - 配送费减免 + 用户支付配送费
    # 注意: 需要先根据配送平台调整物流配送费
    has_full_data = all(field in df.columns for field in ['用户支付配送费', '配送费减免金额', '物流配送费'])
    
    if has_full_data:
        # 🔄 根据配送平台调整物流配送费
        平台扣减列表 = ['eleck', '美团跑腿-平台扣减', '京东平台配送-平台扣减']
        if '配送平台' in df.columns:
            df['实际物流配送费'] = df.apply(
                lambda row: 0 if row.get('配送平台', '') in 平台扣减列表 else row['物流配送费'],
                axis=1
            )
        else:
            df['实际物流配送费'] = df['物流配送费']
        
        # 完整公式: 配送净成本 = 实际物流配送费 - 配送费减免金额 + 用户支付配送费
        total_logistics = (
            df['实际物流配送费'].sum() - 
            df['配送费减免金额'].sum() + 
            df['用户支付配送费'].sum()
        )
        logistics_cost_field = '实际物流配送费'  # 用于后续分组分析
    else:
        # 降级: 仅使用物流配送费
        logistics_cost_field = None
        for field in ['物流配送费', '配送成本', '物流成本']:
            if field in df.columns:
                logistics_cost_field = field
                break
        total_logistics = df[logistics_cost_field].sum() if logistics_cost_field else 0
    
    # 按配送距离分析
    if '配送距离' in df.columns and logistics_cost_field:
        df['距离分组'] = pd.cut(
            df['配送距离'], 
            bins=[0, 1, 3, 5, 10, 100],
            labels=['<1km', '1-3km', '3-5km', '5-10km', '>10km']
        )
        
        # 计算每个距离段的配送净成本
        if has_full_data:
            # 使用完整公式
            agg_dict = {
                '用户支付配送费': 'sum',
                '配送费减免金额': 'sum',
                '实际物流配送费': 'sum',  # 🔄 使用实际物流配送费
                price_col: 'sum',
                '订单ID': 'count'
            }
            distance_stats = df.groupby('距离分组').agg(agg_dict).reset_index()
            # 计算净成本 (修正公式)
            distance_stats['配送成本'] = (
                distance_stats['实际物流配送费'] - 
                distance_stats['配送费减免金额'] + 
                distance_stats['用户支付配送费']
            )
            distance_stats['销售额'] = distance_stats[price_col]
            distance_stats['订单数'] = distance_stats['订单ID']
        else:
            # 降级: 仅使用物流配送费
            distance_stats = df.groupby('距离分组').agg({
                logistics_cost_field: 'sum',
                price_col: 'sum',
                '订单ID': 'count'
            }).reset_index()
            distance_stats.columns = ['距离分组', '配送成本', '销售额', '订单数']
        
        distance_stats['成本占比'] = (
            distance_stats['配送成本'] / distance_stats['销售额'] * 100
        )
        distance_stats['平均客单价'] = distance_stats['销售额'] / distance_stats['订单数']
        
        logistics_cost_analysis['distance_stats'] = distance_stats[
            ['距离分组', '配送成本', '销售额', '订单数', '成本占比', '平均客单价']
        ]
    else:
        logistics_cost_analysis['distance_stats'] = None
    
    logistics_cost_analysis['total_logistics_cost'] = total_logistics
    logistics_cost_analysis['logistics_cost_rate'] = (total_logistics / total_sales * 100) if total_sales > 0 else 0
    logistics_cost_analysis['has_logistics_data'] = logistics_cost_field is not None
    logistics_cost_analysis['use_full_formula'] = has_full_data  # 标识是否使用完整公式
    
    # ========== 3. 营销成本分析 ==========
    marketing_cost_analysis = {}
    
    # 计算各类营销成本
    total_marketing = 0
    marketing_breakdown = {}
    
    if '满减' in df.columns:
        manjian = df['满减'].sum()
        total_marketing += manjian
        marketing_breakdown['满减'] = manjian
    
    if '商品减免' in df.columns:
        goods_discount = df['商品减免'].sum()
        total_marketing += goods_discount
        marketing_breakdown['商品减免'] = goods_discount
    
    if '代金券' in df.columns:
        voucher = df['代金券'].sum()
        total_marketing += voucher
        marketing_breakdown['代金券'] = voucher
    
    if '配送费减免' in df.columns:
        delivery_discount = df['配送费减免'].sum()
        total_marketing += delivery_discount
        marketing_breakdown['配送费减免'] = delivery_discount
    
    # 计算营销ROI（销售额 / 营销成本）
    marketing_roi = (total_sales / total_marketing) if total_marketing > 0 else 0
    
    marketing_cost_analysis['total_marketing_cost'] = total_marketing
    marketing_cost_analysis['marketing_cost_rate'] = (total_marketing / total_sales * 100) if total_sales > 0 else 0
    marketing_cost_analysis['marketing_roi'] = marketing_roi
    marketing_cost_analysis['marketing_breakdown'] = marketing_breakdown
    
    # 按渠道分析营销效率
    if '渠道' in df.columns:
        # 构建聚合字典,只包含存在的字段
        agg_dict = {price_col: 'sum', '订单ID': 'count'}
        
        # 添加存在的营销字段
        marketing_fields = []
        if '满减' in df.columns:
            agg_dict['满减'] = 'sum'
            marketing_fields.append('满减')
        if '商品减免' in df.columns:
            agg_dict['商品减免'] = 'sum'
            marketing_fields.append('商品减免')
        if '代金券' in df.columns:
            agg_dict['代金券'] = 'sum'
            marketing_fields.append('代金券')
        
        if marketing_fields:  # 只有有营销字段时才分析
            channel_stats = df.groupby('渠道').agg(agg_dict).reset_index()
            
            # 计算营销成本总和
            channel_stats['营销成本'] = channel_stats[marketing_fields].sum(axis=1)
            channel_stats['营销成本占比'] = (
                channel_stats['营销成本'] / channel_stats[price_col] * 100
            )
            channel_stats['营销ROI'] = (
                channel_stats[price_col] / channel_stats['营销成本']
            ).replace([np.inf, -np.inf], 0)
            
            marketing_cost_analysis['channel_stats'] = channel_stats
        else:
            marketing_cost_analysis['channel_stats'] = None
    else:
        marketing_cost_analysis['channel_stats'] = None
    
    return {
        'product_cost_analysis': product_cost_analysis,
        'logistics_cost_analysis': logistics_cost_analysis,
        'marketing_cost_analysis': marketing_cost_analysis
    }


# ==================== 页面布局 ====================
# 🎨 Mantine布局包裹器
if MANTINE_AVAILABLE:
    app.layout = dmc.MantineProvider([
        dbc.Container([
            # URL 路由组件（用于页面加载检测）
            dcc.Location(id='url', refresh=False),
            
            # 隐藏的数据更新触发器
            dcc.Store(id='data-update-trigger', data=0),
    dcc.Store(id='data-metadata', data={}),  # 存储数据元信息
    dcc.Store(id='page-init-trigger', data={'loaded': False}),  # 页面初始化触发器
    dcc.Store(id='pandasai-history-store', data=[]),
    dcc.Store(id='rag-auto-summary-store', data={}),
    
    # ========== 门店切换支持 ==========
    dcc.Store(id='current-store-id', data=None),  # 当前选中的门店ID
    dcc.Store(id='store-data', data=[]),  # 当前门店的数据
    
    # ========== 性能优化: 前端数据缓存 (阶段3) ==========
    dcc.Store(id='cached-order-agg', data=None),  # 缓存订单聚合数据
    dcc.Store(id='cached-comparison-data', data=None),  # 缓存环比计算数据
    dcc.Store(id='cache-version', data=0),  # 缓存版本号,用于判断缓存是否有效
    
    # ========== 性能优化: 异步加载控制 (阶段4) ==========
    dcc.Store(id='tab1-core-ready', data=False),  # Tab1核心指标是否就绪
    dcc.Store(id='tab2-core-ready', data=False),  # Tab2核心内容是否就绪
    dcc.Store(id='tab3-core-ready', data=False),  # Tab3核心内容是否就绪
    dcc.Interval(id='progressive-render-interval', interval=100, max_intervals=0, disabled=True),  # 渐进式渲染定时器
    
    # ========== 性能优化: WebWorker后台计算 (阶段8) ==========
    dcc.Store(id='raw-orders-store', storage_type='memory'),  # 原始订单数据
    dcc.Store(id='worker-aggregated-data', storage_type='memory'),  # Worker聚合结果
    
    # 头部
    html.Div([
        html.H1("🏪 门店诊断看板(订单数据)", style={'margin': 0, 'fontSize': '2.5rem'})
    ], className='main-header'),
    
    # 全局数据信息卡片
    html.Div(id='global-data-info-card'),

    # 计算口径选择
    build_calc_mode_selector(),
    
    # ========== 数据源选择区域 ==========
    build_data_source_card(),
    
    # 主内容区 - 使用顶层Tabs组织所有功能模块
    dbc.Row([
        dbc.Col([
            # 使用提示
            dbc.Alert([
                html.H5("👋 欢迎使用门店诊断看板！", className="mb-2"),
                html.P("👇 选择功能模块开始数据分析", className="mb-0")
            ], color="info", className="mb-4"),
            
            # 顶层功能Tabs
            dcc.Tabs(id='main-tabs', value='tab-1', children=[
                
                # ========== Tab 1: 订单数据概览 ==========
                dcc.Tab(label='📊 订单数据概览', value='tab-1', children=[
                    dcc.Loading(
                        id="loading-tab1",
                        type="default",  # default, circle, dot, cube
                        children=[html.Div(id='tab-1-content', className="p-3")]
                    )
                ]),
                
                # ========== Tab 7: 营销成本分析 ==========
                dcc.Tab(label='💰 营销分析', value='tab-7', children=[
                    dcc.Loading(
                        id="loading-tab7",
                        type="default",
                        children=[html.Div(id='tab-7-content', className="p-3")]
                    )
                ]),
                
                # ========== Tab 2: 商品分析 ==========
                dcc.Tab(label='📦 商品分析(开发中)', value='tab-2', children=[
                    dcc.Loading(
                        id="loading-tab2",
                        type="default",
                        children=[html.Div(id='tab-2-content', className="p-3")]
                    )
                ]),
                
                # ========== Tab 5: 时段场景分析 ==========
                dcc.Tab(label='⏰ 时段场景(开发中)', value='tab-5', children=[
                    html.Div(id='tab-5-content', className="p-3")
                ]),
                
            ])  # main-tabs结束（顶层Tabs）
            
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
                    html.H5("📈 销量趋势", className="mb-3"),
                    dcc.Loading(dcc.Graph(id='product-trend-chart'))
                ], md=12)
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("关闭", id='close-product-modal', className="ms-auto")
        ])
    ], id='product-detail-modal', size='xl', is_open=False),
    
    # 数据存储组件
    dcc.Store(id='current-data-store', data=[]),  # 存储当前诊断结果
    dcc.Store(id='uploaded-data-metadata', data=None),  # 上传数据的元信息
    dcc.Store(id='upload-timestamp', data=None),  # 上传时间戳
    dcc.Store(id='global-data-info', data={}),  # 全局数据统计信息
    
    # 调试输出（可选）
    html.Div(id='debug-output', style={'display': 'none'})
        ], fluid=True, className="p-4")
    ])  # 关闭 MantineProvider
else:
    # 如果Mantine不可用，使用原始Bootstrap布局
    app.layout = dbc.Container([
        # URL 路由组件（用于页面加载检测）
        dcc.Location(id='url', refresh=False),
        
        # 隐藏的数据更新触发器
        dcc.Store(id='data-update-trigger', data=0),
        dcc.Store(id='data-metadata', data={}),  # 存储数据元信息
        dcc.Store(id='page-init-trigger', data={'loaded': False}),  # 页面初始化触发器
        dcc.Store(id='pandasai-history-store', data=[]),
        dcc.Store(id='rag-auto-summary-store', data={}),

        # ========== 门店切换支持 ==========
        dcc.Store(id='current-store-id', data=None),  # 当前选中的门店ID
        dcc.Store(id='store-data', data=[]),  # 当前门店的数据
        
        # ========== 性能优化: 前端数据缓存 (阶段3) ==========
        dcc.Store(id='cached-order-agg', data=None),  # 缓存订单聚合数据
        dcc.Store(id='cached-comparison-data', data=None),  # 缓存环比计算数据
        dcc.Store(id='cache-version', data=0),  # 缓存版本号,用于判断缓存是否有效
        
        # ========== 性能优化: 异步加载控制 (阶段4) ==========
        dcc.Store(id='tab1-core-ready', data=False),  # Tab1核心指标是否就绪
        dcc.Store(id='tab2-core-ready', data=False),  # Tab2核心内容是否就绪
        dcc.Store(id='tab3-core-ready', data=False),  # Tab3核心内容是否就绪
        dcc.Interval(id='progressive-render-interval', interval=100, max_intervals=0, disabled=True),  # 渐进式渲染定时器
        
        # ========== 性能优化: WebWorker后台计算 (阶段8) ==========
        dcc.Store(id='raw-orders-store', storage_type='memory'),  # 原始订单数据
        dcc.Store(id='worker-aggregated-data', storage_type='memory'),  # Worker聚合结果
        
        # 头部
        html.Div([
            html.H1("🏪 门店诊断看板(订单数据)", style={'margin': 0, 'fontSize': '2.5rem'})
        ], className='main-header'),
        
        # 全局数据信息卡片
        html.Div(id='global-data-info-card'),
        build_calc_mode_selector(),
        
        # ========== 数据源选择区域 ==========
        build_data_source_card(),

        # 主内容区 - 使用顶层Tabs组织所有功能模块
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H5("👋 欢迎使用门店诊断看板！", className="mb-2"),
                    html.P("👇 选择功能模块开始数据分析", className="mb-0")
                ], color="info", className="mb-4"),

                dcc.Tabs(id='main-tabs', value='tab-1', children=[
                    dcc.Tab(label='📊 订单数据概览', value='tab-1', children=[
                        dcc.Loading(
                            id="loading-tab1",
                            type="default",
                            children=[html.Div(id='tab-1-content', className="p-3")]
                        )
                    ]),
                    dcc.Tab(label='💰 营销分析', value='tab-7', children=[
                        dcc.Loading(
                            id="loading-tab7",
                            type="default",
                            children=[html.Div(id='tab-7-content', className="p-3")]
                        )
                    ]),
                    dcc.Tab(label='📦 商品分析(开发中)', value='tab-2', children=[
                        dcc.Loading(
                            id="loading-tab2",
                            type="default",
                            children=[html.Div(id='tab-2-content', className="p-3")]
                        )
                    ]),
                    dcc.Tab(label='⏰ 时段场景(开发中)', value='tab-5', children=[
                        html.Div(id='tab-5-content', className="p-3")
                    ])
                ])
            ], width=12)
        ], className="mb-3"),
        
        # ⚠️ 注意: main-tabs 已在前面定义,这里不需要重复定义
        # 主体内容Tabs 已在上面完整定义
        
        # 上传数据存储
        dcc.Store(id='uploaded-data-store', storage_type='memory'),
        dcc.Store(id='uploaded-data-metadata', data=None),
        dcc.Store(id='upload-timestamp', data=None),
        dcc.Store(id='global-data-info', data={}),
        
        # 调试输出
        html.Div(id='debug-output', style={'display': 'none'})
    ], fluid=True, className="p-4")


# ==================== 辅助函数 ====================

def get_available_months(df):
    """提取数据中所有的月份，用于月度选择器"""
    if df is None or '日期' not in df.columns:
        return []
    try:
        df_temp = df.copy()
        df_temp['日期'] = pd.to_datetime(df_temp['日期'], errors='coerce')
        min_date = df_temp['日期'].min()
        max_date = df_temp['日期'].max()
        return min_date, max_date
    except Exception as e:
        print(f"❌ 获取日期范围失败: {e}")
        return None, None


# 📊 动态周期选择器回调

# ============================================================================
# 旧Tab 4的动态周期选择器回调已删除（引用已删除的UI组件）
# 新Tab 4采用智能驱动模式，不需要手动选择周期
# ============================================================================

# ==================== 数据库数据源回调函数 ====================

@app.callback(
    [Output('db-store-filter', 'options'),
     Output('database-stats', 'children')],
    Input('data-source-tabs', 'value')
)
def update_database_info(tab_value):
    """当切换到数据库Tab时，加载门店列表和统计信息"""
    if tab_value != 'database-data' or not DATABASE_AVAILABLE or DATA_SOURCE_MANAGER is None:
        return [], html.Div()
    
    try:
        # 获取门店列表
        stores = DATA_SOURCE_MANAGER.get_available_stores()
        store_options = [{'label': store, 'value': store} for store in stores]
        
        # 获取数据库统计
        stats = DATA_SOURCE_MANAGER.get_database_stats()
        
        stats_card = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H3(f"{stats.get('orders', 0):,}", className="mb-0 text-primary"),
                            html.Small("订单数量", className="text-muted")
                        ])
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.H3(f"{stats.get('products', 0):,}", className="mb-0 text-success"),
                            html.Small("商品种类", className="text-muted")
                        ])
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.H3(f"{stats.get('stores', 0):,}", className="mb-0 text-info"),
                            html.Small("门店数量", className="text-muted")
                        ])
                    ], md=3),
                    dbc.Col([
                        html.Div([
                            html.H3(stats.get('start_date', '--') + " ~ " + stats.get('end_date', '--'), 
                                   className="mb-0 text-secondary small"),
                            html.Small("数据时间范围", className="text-muted")
                        ])
                    ], md=3)
                ])
            ])
        ], className="mb-3")
        
        return store_options, stats_card
        
    except Exception as e:
        error_msg = dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            f"数据库连接失败: {str(e)}"
        ], color="danger")
        return [], error_msg


# ==================== 快捷日期选择回调 ====================
@app.callback(
    [Output('db-date-range', 'start_date'),
     Output('db-date-range', 'end_date')],
    [Input('quick-date-yesterday', 'n_clicks'),
     Input('quick-date-today', 'n_clicks'),
     Input('quick-date-last-week', 'n_clicks'),
     Input('quick-date-this-week', 'n_clicks'),
     Input('quick-date-last-month', 'n_clicks'),
     Input('quick-date-this-month', 'n_clicks'),
     Input('quick-date-last-7days', 'n_clicks'),
     Input('quick-date-last-30days', 'n_clicks')],
    prevent_initial_call=True
)
def update_date_range_from_quick_buttons(yesterday, today, last_week, this_week, 
                                         last_month, this_month, last_7days, last_30days):
    """根据快捷按钮更新日期范围（✅ 限制在数据库实际范围内）"""
    global QUERY_DATE_RANGE
    
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    today_date = datetime.now()
    
    # ✅ 获取数据库实际日期范围
    db_max_date = QUERY_DATE_RANGE.get('db_max_date')
    db_min_date = QUERY_DATE_RANGE.get('db_min_date')
    
    # 如果数据库有最大日期,使用它作为"今天"的上限
    if db_max_date:
        # 使用数据库最大日期和系统当前日期中的较小值
        effective_today = min(today_date, db_max_date)
    else:
        effective_today = today_date
    
    # 根据按钮ID计算日期范围
    if button_id == 'quick-date-yesterday':
        # 昨日
        target_date = effective_today - timedelta(days=1)
        start_date = target_date.date()
        end_date = target_date.date()
    
    elif button_id == 'quick-date-today':
        # 今日
        start_date = effective_today.date()
        end_date = effective_today.date()
    
    elif button_id == 'quick-date-last-week':
        # 上周 (上周一到上周日)
        days_since_monday = effective_today.weekday()
        last_monday = effective_today - timedelta(days=days_since_monday + 7)
        last_sunday = last_monday + timedelta(days=6)
        start_date = last_monday.date()
        end_date = last_sunday.date()
    
    elif button_id == 'quick-date-this-week':
        # 本周 (本周一到今天)
        days_since_monday = effective_today.weekday()
        this_monday = effective_today - timedelta(days=days_since_monday)
        start_date = this_monday.date()
        end_date = effective_today.date()
    
    elif button_id == 'quick-date-last-month':
        # 上月 (上月1日到上月最后一天)
        first_day_this_month = effective_today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        start_date = first_day_last_month.date()
        end_date = last_day_last_month.date()
    
    elif button_id == 'quick-date-this-month':
        # 本月 (本月1日到今天)
        start_date = effective_today.replace(day=1).date()
        end_date = effective_today.date()
    
    elif button_id == 'quick-date-last-7days':
        # 过去7天
        start_date = (effective_today - timedelta(days=6)).date()
        end_date = effective_today.date()
    
    elif button_id == 'quick-date-last-30days':
        # 过去30天
        start_date = (effective_today - timedelta(days=29)).date()
        end_date = effective_today.date()
    
    else:
        return no_update, no_update
    
    # ✅ 进一步限制在数据库范围内
    if db_min_date:
        start_date = max(start_date, db_min_date.date())
    if db_max_date:
        end_date = min(end_date, db_max_date.date())
    
    return start_date, end_date


def _generate_load_success_response(df, start_date, end_date, cache_source="Database"):
    """
    生成数据加载成功的响应信息
    
    Args:
        df: 加载的DataFrame
        start_date: 起始日期
        end_date: 结束日期
        cache_source: 缓存来源（Redis/Database/Local）
    
    Returns:
        tuple: (data_label, trigger, status, stats_card)
    """
    # 计算实际加载数据的统计信息
    actual_start = df['日期'].min().strftime('%Y-%m-%d') if '日期' in df.columns else '--'
    actual_end = df['日期'].max().strftime('%Y-%m-%d') if '日期' in df.columns else '--'
    unique_products = df['商品名称'].nunique() if '商品名称' in df.columns else 0
    unique_stores = df['门店名称'].nunique() if '门店名称' in df.columns else 0
    
    # 缓存来源图标
    cache_icon = {
        "Redis": "🎯",
        "Database": "📊",
        "Local": "💾"
    }.get(cache_source, "📦")
    
    # 生成更新后的统计卡片
    stats_card = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H3(f"{len(df):,}", className="mb-0 text-primary"),
                        html.Small("订单数量", className="text-muted")
                    ])
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.H3(f"{unique_products:,}", className="mb-0 text-success"),
                        html.Small("商品种类", className="text-muted")
                    ])
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.H3(f"{unique_stores:,}", className="mb-0 text-info"),
                        html.Small("门店数量", className="text-muted")
                    ])
                ], md=3),
                dbc.Col([
                    html.Div([
                        html.H3(f"{actual_start} ~ {actual_end}", 
                               className="mb-0 text-secondary small"),
                        html.Small("数据时间范围", className="text-muted")
                    ])
                ], md=3)
            ])
        ])
    ], className="shadow-sm mb-3")
    
    # 成功消息
    success_message = dbc.Alert([
        html.I(className="bi bi-check-circle me-2"),
        html.Span([
            f"{cache_icon} 数据加载成功 ",
            html.Small(f"(来源: {cache_source})", className="text-muted")
        ])
    ], color="success", dismissable=True, duration=4000)
    
    return (
        f"数据库数据 ({actual_start} ~ {actual_end})",
        datetime.now().isoformat(),
        success_message,
        stats_card
    )


@app.callback(
    [Output('current-data-label', 'children', allow_duplicate=True),
     Output('data-update-trigger', 'data', allow_duplicate=True),
     Output('database-load-status', 'children'),
     Output('database-stats', 'children', allow_duplicate=True)],  # 添加统计卡片更新
    Input('load-from-database-btn', 'n_clicks'),
    [State('db-store-filter', 'value'),
     State('db-date-range', 'start_date'),
     State('db-date-range', 'end_date')],
    prevent_initial_call=True
)
def load_from_database(n_clicks, store_name, start_date, end_date):
    """从数据库加载数据"""
    if not n_clicks or not DATABASE_AVAILABLE or DATA_SOURCE_MANAGER is None:
        return no_update, no_update, "", no_update
    
    global GLOBAL_DATA, GLOBAL_FULL_DATA, QUERY_DATE_RANGE
    
    # 🔍 调试日志:打印接收到的参数
    print("\n" + "="*80)
    print("🔍 [DEBUG] load_from_database 被调用")
    print(f"   门店名称: '{store_name}' (类型: {type(store_name)})")
    print(f"   起始日期: '{start_date}' (类型: {type(start_date)})")
    print(f"   结束日期: '{end_date}' (类型: {type(end_date)})")
    if store_name:
        print(f"   门店名称长度: {len(store_name)}")
        print(f"   门店名称repr: {repr(store_name)}")
    print("="*80 + "\n")
    
    try:
        # 转换日期
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # ✅ 第1层：Redis缓存（多用户共享，跨会话）
        redis_cache_key = None
        if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
            # 生成Redis缓存键
            redis_cache_key = f"store_data:{store_name}:{start_date}:{end_date}"
            
            # 尝试从Redis读取
            cached_df = get_cached_dataframe(redis_cache_key, REDIS_CACHE_MANAGER)
            if cached_df is not None:
                print(f"🎯 [Redis缓存命中] 门店: {store_name}, 日期: {start_date} ~ {end_date}")
                print(f"   数据行数: {len(cached_df):,}, 缓存命中率提升！")
                
                # 更新全局数据
                GLOBAL_DATA = cached_df
                
                # 更新完整数据缓存
                if GLOBAL_FULL_DATA is None or QUERY_DATE_RANGE.get('cache_store') != store_name:
                    full_redis_key = f"store_full_data:{store_name}"
                    full_cached_df = get_cached_dataframe(full_redis_key, REDIS_CACHE_MANAGER)
                    if full_cached_df is not None:
                        GLOBAL_FULL_DATA = full_cached_df
                        print(f"✅ 完整数据也从Redis缓存加载")
                
                # 生成统计信息并返回
                return _generate_load_success_response(cached_df, start_date, end_date, cache_source="Redis")
        
        # ✅ 第2层：本地内存缓存（5分钟，单会话）
        cache_valid = (
            QUERY_DATE_RANGE.get('cache_store') == store_name and
            QUERY_DATE_RANGE.get('cache_timestamp') is not None and
            QUERY_DATE_RANGE.get('db_min_date') is not None and
            QUERY_DATE_RANGE.get('db_max_date') is not None and
            # 缓存有效期：5分钟
            (datetime.now() - QUERY_DATE_RANGE.get('cache_timestamp')).total_seconds() < 300
        )
        
        if not cache_valid:
            # 缓存无效或过期，重新加载数据库完整范围
            print("🔄 本地缓存无效或过期，从数据库加载完整数据...")
            
            # 先尝试从Redis加载完整数据
            full_df = None
            if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
                full_redis_key = f"store_full_data:{store_name}"
                full_df = get_cached_dataframe(full_redis_key, REDIS_CACHE_MANAGER)
                if full_df is not None:
                    print(f"✅ 完整数据从Redis缓存加载 ({len(full_df):,}行)")
            
            # Redis未命中，从数据库加载
            if full_df is None:
                print("📊 从数据库加载完整数据...")
                full_df = DATA_SOURCE_MANAGER.load_from_database(store_name=store_name)
                full_df = add_scene_and_timeslot_fields(full_df)
                
                # 保存到Redis缓存
                if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled and not full_df.empty:
                    full_redis_key = f"store_full_data:{store_name}"
                    cache_dataframe(full_redis_key, full_df, ttl=1800, cache_manager=REDIS_CACHE_MANAGER)
                    print(f"💾 完整数据已保存到Redis缓存 (TTL=30分钟)")
            
            GLOBAL_FULL_DATA = full_df
            
            if not full_df.empty and '日期' in full_df.columns:
                date_col = pd.to_datetime(full_df['日期'], errors='coerce')
                QUERY_DATE_RANGE['db_min_date'] = date_col.min()
                QUERY_DATE_RANGE['db_max_date'] = date_col.max()
                QUERY_DATE_RANGE['cache_timestamp'] = datetime.now()
                QUERY_DATE_RANGE['cache_store'] = store_name
                print(f"✅ 数据库完整范围已缓存: {QUERY_DATE_RANGE['db_min_date'].strftime('%Y-%m-%d')} ~ {QUERY_DATE_RANGE['db_max_date'].strftime('%Y-%m-%d')}")
                print(f"📦 本地缓存将在 5 分钟后过期")
        else:
            print(f"✅ 使用本地缓存的数据库范围: {QUERY_DATE_RANGE['db_min_date'].strftime('%Y-%m-%d')} ~ {QUERY_DATE_RANGE['db_max_date'].strftime('%Y-%m-%d')}")
            print(f"📦 本地缓存剩余时间: {int(300 - (datetime.now() - QUERY_DATE_RANGE['cache_timestamp']).total_seconds())} 秒")
        
        # 从数据库加载(带日期过滤)
        print(f"📊 从数据库查询指定日期范围数据: {start_date} ~ {end_date}")
        df = DATA_SOURCE_MANAGER.load_from_database(
            store_name=store_name,
            start_date=start_dt,
            end_date=end_dt
        )
        
        # ✅ 修复: 如果用户未指定日期,使用实际加载的数据范围
        if df is not None and not df.empty and '日期' in df.columns:
            df_date_col = pd.to_datetime(df['日期'], errors='coerce')
            actual_min_date = df_date_col.min()
            actual_max_date = df_date_col.max()
            
            # 如果用户未指定日期范围,使用实际数据范围
            if start_dt is None:
                start_dt = actual_min_date
            if end_dt is None:
                end_dt = actual_max_date
            
            # 保存用户查询的日期范围(或实际数据范围)
            QUERY_DATE_RANGE['start_date'] = start_dt
            QUERY_DATE_RANGE['end_date'] = end_dt
            print(f"✅ 查询日期范围已保存: {start_dt.strftime('%Y-%m-%d')} ~ {end_dt.strftime('%Y-%m-%d')}")
        else:
            # 保存用户查询的日期范围
            QUERY_DATE_RANGE['start_date'] = start_dt
            QUERY_DATE_RANGE['end_date'] = end_dt
        
        if df.empty:
            return no_update, no_update, dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                "未找到符合条件的数据"
            ], color="warning"), no_update
        
        # ✨ 应用场景和时段字段(智能打标)
        print(f"🎯 开始场景打标处理({len(df)}行数据)...")
        df = add_scene_and_timeslot_fields(df)
        print(f"✅ 场景打标完成")
        
        # 更新全局数据(筛选后的)
        GLOBAL_DATA = df
        # ⚠️ 修复:GLOBAL_FULL_DATA不应该被日期筛选后的数据覆盖
        # 它应该保持完整数据,用于环比计算时查找历史周期
        # GLOBAL_FULL_DATA = df  # ❌ 错误:这会导致环比无法找到上期数据
        
        # ✅ 保存到Redis缓存（供其他用户共享）
        if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled and redis_cache_key:
            cache_dataframe(redis_cache_key, df, ttl=1800, cache_manager=REDIS_CACHE_MANAGER)
            print(f"💾 查询结果已保存到Redis缓存 (TTL=30分钟)")
        
        # 生成成功响应
        return _generate_load_success_response(df, start_date, end_date, cache_source="Database")
        
    except Exception as e:
        # ✨ 增强错误消息,帮助用户排查问题
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ 数据加载失败: {error_detail}")
        
        error_msg = dbc.Alert([
            html.Div([
                html.I(className="bi bi-exclamation-triangle me-2"),
                html.Strong("加载失败", className="me-2"),
                html.Br(),
                html.Small([
                    html.Span(f"错误信息: {str(e)}", className="text-danger"),
                    html.Br(),
                    html.Span("请检查: 1)门店名称是否正确 2)网络连接是否正常 3)数据库是否可访问", className="text-muted mt-2")
                ])
            ])
        ], color="danger", dismissable=True)
        return no_update, no_update, error_msg, no_update


# ========== 新增: 门店切换时更新store-data ==========
@app.callback(
    [Output('current-store-id', 'data'),
     Output('store-data', 'data')],
    Input('data-update-trigger', 'data'),
    State('db-store-filter', 'value'),
    prevent_initial_call=True
)
def update_store_data(trigger, store_name):
    """门店切换或数据更新时,同步更新store-data"""
    if GLOBAL_DATA is not None and len(GLOBAL_DATA) > 0:
        return store_name, GLOBAL_DATA.to_dict('records')
    return store_name, []


# ✨ 新增：刷新数据范围缓存的回调
@app.callback(
    Output('cache-status-alert', 'children'),
    [Input('refresh-cache-btn', 'n_clicks'),
     Input('load-from-database-btn', 'n_clicks')],
    State('db-store-filter', 'value'),
    prevent_initial_call=True
)
def refresh_or_show_cache_status(refresh_clicks, load_clicks, store_name):
    """刷新缓存或显示缓存状态（包含Redis缓存）"""
    if not DATABASE_AVAILABLE or DATA_SOURCE_MANAGER is None:
        return no_update
    
    global QUERY_DATE_RANGE
    
    # 判断触发源
    ctx = callback_context
    if not ctx.triggered:
        return no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'refresh-cache-btn' and refresh_clicks:
        # 手动刷新缓存
        try:
            print("🔄 手动刷新数据范围缓存...")
            
            # ✅ 清除Redis缓存
            redis_cleared = 0
            if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled and store_name:
                redis_cleared = clear_store_cache(store_name, REDIS_CACHE_MANAGER)
                if redis_cleared > 0:
                    print(f"🗑️  已清除 {redis_cleared} 个Redis缓存项")
            
            # 重新加载数据
            full_df = DATA_SOURCE_MANAGER.load_from_database(store_name=store_name)
            
            if not full_df.empty and '日期' in full_df.columns:
                full_df = add_scene_and_timeslot_fields(full_df)
                date_col = pd.to_datetime(full_df['日期'], errors='coerce')
                QUERY_DATE_RANGE['db_min_date'] = date_col.min()
                QUERY_DATE_RANGE['db_max_date'] = date_col.max()
                QUERY_DATE_RANGE['cache_timestamp'] = datetime.now()
                QUERY_DATE_RANGE['cache_store'] = store_name
                
                # ✅ 保存到Redis缓存
                if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
                    full_redis_key = f"store_full_data:{store_name}"
                    cache_dataframe(full_redis_key, full_df, ttl=1800, cache_manager=REDIS_CACHE_MANAGER)
                    print(f"💾 完整数据已更新到Redis缓存")
                
                cache_info = f"本地+Redis" if redis_cleared > 0 else "本地"
                return dbc.Alert([
                    html.I(className="bi bi-check-circle me-2"),
                    f"✅ {cache_info}缓存已刷新！数据范围: {QUERY_DATE_RANGE['db_min_date'].strftime('%Y-%m-%d')} ~ {QUERY_DATE_RANGE['db_max_date'].strftime('%Y-%m-%d')}"
                ], color="success", dismissable=True, duration=4000)
            else:
                return dbc.Alert([
                    html.I(className="bi bi-exclamation-triangle me-2"),
                    "⚠️ 无法刷新缓存：数据库无数据"
                ], color="warning", dismissable=True, duration=4000)
        except Exception as e:
            print(f"❌ 刷新缓存失败: {e}")
            return dbc.Alert([
                html.I(className="bi bi-x-circle me-2"),
                f"❌ 刷新失败: {str(e)}"
            ], color="danger", dismissable=True, duration=4000)
    
    # 加载数据后显示缓存状态
    if QUERY_DATE_RANGE.get('cache_timestamp'):
        cache_age = (datetime.now() - QUERY_DATE_RANGE['cache_timestamp']).total_seconds()
        remaining = max(0, 300 - cache_age)  # 5分钟本地缓存
        
        # 检查Redis缓存状态
        redis_info = ""
        if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
            try:
                stats = REDIS_CACHE_MANAGER.get_stats()
                if stats.get('enabled'):
                    redis_info = f" | Redis: {stats.get('total_keys', 0)}键, 命中率{stats.get('hit_rate', 0):.1f}%"
            except:
                pass
        
        if remaining > 0:
            return dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                html.Small(f"📦 使用缓存数据 | 本地缓存剩余: {int(remaining)}秒{redis_info} | 范围: {QUERY_DATE_RANGE['db_min_date'].strftime('%Y-%m-%d')} ~ {QUERY_DATE_RANGE['db_max_date'].strftime('%Y-%m-%d')}")
            ], color="info", className="mb-0", style={'padding': '8px 12px'})
    
    return no_update


# ==================== 上传新数据到数据库回调函数 ====================
@app.callback(
    [Output('current-data-label', 'children', allow_duplicate=True),
     Output('data-update-trigger', 'data', allow_duplicate=True),
     Output('upload-status', 'children'),
     Output('upload-debug-info', 'children')],
    Input('upload-data', 'contents'),
    [State('upload-data', 'filename'),
     State('upload-data', 'last_modified')],
    prevent_initial_call=True
)
def upload_data_to_database(list_of_contents, list_of_names, list_of_dates):
    """上传数据文件并导入到数据库"""
    global GLOBAL_DATA, GLOBAL_FULL_DATA, QUERY_DATE_RANGE, DATA_SOURCE_MANAGER
    
    print(f"\n{'='*70}")
    print(f"🔍 [上传回调] 被触发")
    print(f"   list_of_contents: {list_of_contents is not None}")
    print(f"   list_of_names: {list_of_names}")
    print(f"   DATABASE_AVAILABLE: {DATABASE_AVAILABLE}")
    print(f"   DATA_SOURCE_MANAGER: {DATA_SOURCE_MANAGER}")
    print(f"{'='*70}")
    
    if not list_of_contents:
        print("⚠️ list_of_contents 为空，返回 no_update")
        return no_update, no_update, "", ""
    
    # 如果数据库不可用，给出详细提示
    if not DATABASE_AVAILABLE:
        print("❌ DATABASE_AVAILABLE = False，数据库功能未启用")
        return no_update, no_update, dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            html.Div([
                html.Strong("数据库功能未启用"),
                html.Br(),
                html.Small("请安装数据库依赖: pip install psycopg2-binary sqlalchemy"),
                html.Br(),
                html.Small("或检查数据库连接配置是否正确", className="text-muted")
            ])
        ], color="warning"), ""
    
    # 尝试初始化数据源管理器（如果还未初始化）
    if DATA_SOURCE_MANAGER is None:
        try:
            DATA_SOURCE_MANAGER = DataSourceManager()
            print("✅ 数据源管理器已初始化（延迟加载）", flush=True)
        except Exception as init_error:
            print(f"❌ 数据源管理器初始化失败: {init_error}", flush=True)
            import traceback
            traceback.print_exc()
            return no_update, no_update, dbc.Alert([
                html.I(className="bi bi-x-circle me-2"),
                html.Div([
                    html.Strong("数据源管理器初始化失败"),
                    html.Br(),
                    html.Small(f"错误: {str(init_error)}"),
                    html.Br(),
                    html.Small("请检查数据库连接配置", className="text-muted")
                ])
            ], color="danger"), ""
    
    try:
        import base64
        import io
        from database.models import Order
        from database.connection import SessionLocal
        
        session = SessionLocal()
        all_results = []
        total_success = 0
        total_failed = 0
        uploaded_stores = []
        
        # 处理每个上传的文件
        for content, filename, date in zip(list_of_contents, list_of_names, list_of_dates):
            try:
                # 解析文件内容
                content_type, content_string = content.split(',')
                decoded = base64.b64decode(content_string)
                
                # 读取Excel
                print(f"\n{'='*70}")
                print(f"📥 处理文件: {filename}")
                print(f"{'='*70}")
                
                df = pd.read_excel(io.BytesIO(decoded))
                print(f"✅ 读取成功: {len(df):,} 行")
                
                # ===== 1. 验证数据结构 =====
                required_fields = ['订单ID', '门店名称', '商品名称', '商品实售价', '销量', '下单时间']
                missing_fields = [f for f in required_fields if f not in df.columns]
                
                if missing_fields:
                    all_results.append({
                        'filename': filename,
                        'status': 'error',
                        'message': f"缺少必需字段: {', '.join(missing_fields)}"
                    })
                    continue
                
                print("✅ 数据结构验证通过")
                
                # ===== 2. 过滤耗材 =====
                if '一级分类名' in df.columns:
                    original_len = len(df)
                    df = df[~df['一级分类名'].isin(['耗材'])]
                    filtered_count = original_len - len(df)
                    if filtered_count > 0:
                        print(f"🗑️  过滤耗材: 移除 {filtered_count:,} 条")
                
                # ===== 3. 检查门店是否已存在 =====
                store_name = df['门店名称'].iloc[0] if '门店名称' in df.columns else "未知门店"
                uploaded_stores.append(store_name)
                
                existing_count = session.query(Order).filter(
                    Order.store_name == store_name
                ).count()
                
                if existing_count > 0:
                    print(f"⚠️  门店 '{store_name}' 已存在 {existing_count:,} 条数据")
                    # 删除旧数据
                    print("🗑️  删除旧数据...")
                    session.query(Order).filter(Order.store_name == store_name).delete()
                    session.commit()
                    print("✅ 旧数据已删除")
                
                # ===== 4. 批量导入数据 =====
                print(f"📊 开始导入数据...")
                batch_size = 5000
                batch_orders = []
                success_count = 0
                error_count = 0
                
                from datetime import datetime as dt
                start_time = dt.now()
                
                for idx, row in df.iterrows():
                    try:
                        commission_raw = row.get('平台佣金', None)
                        service_fee_raw = row.get('平台服务费', commission_raw)
                        if pd.isna(commission_raw) and not pd.isna(service_fee_raw):
                            commission_value = service_fee_raw
                        else:
                            commission_value = commission_raw
                        platform_service_fee_value = service_fee_raw

                        order_data = {
                            'order_id': str(row.get('订单ID', '')),
                            'date': pd.to_datetime(row.get('下单时间')) if pd.notna(row.get('下单时间')) else None,
                            'store_name': str(row.get('门店名称', '')),
                            'product_name': str(row.get('商品名称', '')),
                            'price': float(row.get('商品实售价', 0)),
                            'original_price': float(row.get('商品原价', 0)),
                            'quantity': int(row.get('销量', 0)),
                            'cost': float(row.get('成本', 0)) if pd.notna(row.get('成本')) else 0.0,
                            # ✅ 修复:从Excel读取利润额(优先使用'利润额',备选'实际利润')
                            'profit': float(row.get('利润额', row.get('实际利润', 0))) if pd.notna(row.get('利润额', row.get('实际利润', 0))) else 0.0,
                            'category_level1': str(row.get('一级分类名', '')),
                            'category_level3': str(row.get('三级分类名', '')),
                            'barcode': str(row.get('条码', '')),
                            'delivery_fee': float(row.get('物流配送费', 0)) if pd.notna(row.get('物流配送费')) else 0.0,
                            'commission': float(commission_value) if pd.notna(commission_value) else 0.0,
                            'platform_service_fee': float(platform_service_fee_value) if pd.notna(platform_service_fee_value) else 0.0,
                            'user_paid_delivery_fee': float(row.get('用户支付配送费', 0)) if pd.notna(row.get('用户支付配送费')) else 0.0,
                            'delivery_discount': float(row.get('配送费减免金额', 0)) if pd.notna(row.get('配送费减免金额')) else 0.0,
                            'full_reduction': float(row.get('满减金额', 0)) if pd.notna(row.get('满减金额')) else 0.0,
                            'product_discount': float(row.get('商品减免金额', 0)) if pd.notna(row.get('商品减免金额')) else 0.0,
                            'merchant_voucher': float(row.get('商家代金券', 0)) if pd.notna(row.get('商家代金券')) else 0.0,
                            'merchant_share': float(row.get('商家承担部分券', 0)) if pd.notna(row.get('商家承担部分券')) else 0.0,
                            'packaging_fee': float(row.get('打包袋金额', 0)) if pd.notna(row.get('打包袋金额')) else 0.0,
                            # ✅ 新增营销维度字段
                            'gift_amount': float(row.get('满赠金额', 0)) if pd.notna(row.get('满赠金额')) else 0.0,
                            'other_merchant_discount': float(row.get('商家其他优惠', 0)) if pd.notna(row.get('商家其他优惠')) else 0.0,
                            'new_customer_discount': float(row.get('新客减免金额', 0)) if pd.notna(row.get('新客减免金额')) else 0.0,
                            # ✅ 新增利润维度字段
                            'corporate_rebate': float(row.get('企客后返', 0)) if pd.notna(row.get('企客后返')) else 0.0,
                            # ✅ 新增配送平台字段
                            'delivery_platform': str(row.get('配送平台', '')) if pd.notna(row.get('配送平台')) else '',
                            # 其他字段
                            'address': str(row.get('收货地址', '')),
                            'channel': str(row.get('渠道', '')),
                            'actual_price': float(row.get('实收价格', 0)) if pd.notna(row.get('实收价格')) else 0.0,
                            # ✅ 修复:添加备选值'订单零售额',与其他导入脚本保持一致
                            'amount': float(row.get('预计订单收入', row.get('订单零售额', 0))) if pd.notna(row.get('预计订单收入', row.get('订单零售额', 0))) else 0.0,
                        }
                        batch_orders.append(order_data)
                        success_count += 1
                        
                        # 批量插入
                        if len(batch_orders) >= batch_size:
                            session.bulk_insert_mappings(Order, batch_orders)
                            session.commit()
                            batch_orders = []
                            
                            elapsed = (dt.now() - start_time).total_seconds()
                            speed = success_count / elapsed if elapsed > 0 else 0
                            print(f"   进度: {success_count:,}/{len(df):,} ({success_count/len(df)*100:.1f}%) | 速度: {speed:.0f}行/秒", end='\r')
                    
                    except Exception as e:
                        error_count += 1
                        if error_count <= 3:
                            print(f"\n⚠️  第{idx+1}行失败: {e}")
                
                # 插入剩余数据
                if batch_orders:
                    session.bulk_insert_mappings(Order, batch_orders)
                    session.commit()
                
                total_time = (dt.now() - start_time).total_seconds()
                print(f"\n✅ 导入完成: {success_count:,}/{len(df):,} ({success_count/len(df)*100:.1f}%)")
                print(f"⏱️  耗时: {total_time:.1f}秒 | 速度: {success_count/total_time:.0f}行/秒")
                
                # ===== 4.5 更新Product表（同步库存信息） =====
                print(f"\n📦 同步商品库存信息到Product表...")
                try:
                    from database.models import Product
                    
                    # 获取Excel中的库存字段（兼容不同字段名）
                    stock_field = None
                    if '库存' in df.columns:
                        stock_field = '库存'
                    elif '剩余库存' in df.columns:
                        stock_field = '剩余库存'
                    
                    if stock_field and '条码' in df.columns:
                        # 获取每个商品的最新库存（取最后一行的库存数据）
                        product_stock = df.groupby('条码').agg({
                            stock_field: 'last',  # 取最后一次出现的库存值
                            '店内码': 'first',  # 取第一次出现的店内码
                            '商品名称': 'first'
                        }).reset_index()
                        
                        product_stock = product_stock[product_stock['条码'].notna()]
                        
                        updated_count = 0
                        created_count = 0
                        
                        for _, row in product_stock.iterrows():
                            barcode = str(row['条码'])
                            stock = int(row[stock_field]) if pd.notna(row[stock_field]) else 0
                            store_code = str(row['店内码']) if pd.notna(row['店内码']) else None
                            product_name = str(row['商品名称'])
                            
                            # 查找或创建Product记录
                            product = session.query(Product).filter(Product.barcode == barcode).first()
                            
                            if product:
                                # 更新现有商品
                                product.stock = stock
                                if store_code:
                                    product.store_code = store_code
                                updated_count += 1
                            else:
                                # 创建新商品
                                new_product = Product(
                                    barcode=barcode,
                                    store_code=store_code,
                                    stock=stock,
                                    product_name=product_name
                                )
                                session.add(new_product)
                                created_count += 1
                        
                        session.commit()
                        print(f"✅ Product表同步完成: 更新 {updated_count} 个商品, 新增 {created_count} 个商品")
                    else:
                        print(f"⚠️  Excel中缺少'库存'或'条码'字段，跳过Product表同步")
                        
                except Exception as e:
                    print(f"⚠️  Product表同步失败: {e}")
                    import traceback
                    traceback.print_exc()
                    # 不影响主流程，继续执行
                
                total_success += success_count
                total_failed += error_count
                
                all_results.append({
                    'filename': filename,
                    'status': 'success',
                    'rows': len(df),
                    'success': success_count,
                    'failed': error_count,
                    'store': store_name
                })
                
            except Exception as e:
                import traceback
                print(f"❌ 文件 {filename} 处理失败: {e}")
                traceback.print_exc()
                all_results.append({
                    'filename': filename,
                    'status': 'error',
                    'message': str(e)
                })
        
        session.close()
        
        # ===== 5. 清除缓存 =====
        print("\n🗑️  清除缓存...")
        for store in set(uploaded_stores):
            QUERY_DATE_RANGE.pop('cache_store', None)
            QUERY_DATE_RANGE.pop('cache_timestamp', None)
            
            if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
                clear_store_cache(store, REDIS_CACHE_MANAGER)
        
        print("✅ 缓存已清除")
        
        # ===== 6. 自动加载第一个上传的门店数据 =====
        if uploaded_stores and all_results[0]['status'] == 'success':
            first_store = uploaded_stores[0]
            print(f"\n📊 自动加载门店 '{first_store}' 的数据...")
            
            df_loaded = DATA_SOURCE_MANAGER.load_from_database(store_name=first_store)
            df_loaded = add_scene_and_timeslot_fields(df_loaded)
            GLOBAL_DATA = df_loaded
            GLOBAL_FULL_DATA = df_loaded
            
            if not df_loaded.empty and '日期' in df_loaded.columns:
                date_col = pd.to_datetime(df_loaded['日期'], errors='coerce')
                QUERY_DATE_RANGE['db_min_date'] = date_col.min()
                QUERY_DATE_RANGE['db_max_date'] = date_col.max()
                print(f"✅ 数据已加载到看板: {len(df_loaded):,} 行")
        
        # ===== 7. 生成结果信息 =====
        success_files = [r for r in all_results if r['status'] == 'success']
        error_files = [r for r in all_results if r['status'] == 'error']
        
        # 状态信息
        if success_files:
            status_alert = dbc.Alert([
                html.Div([
                    html.I(className="bi bi-check-circle me-2"),
                    html.Strong(f"✅ 上传成功!", className="me-2"),
                    html.Br(),
                    html.Div([
                        html.Small([
                            html.Div([
                                html.Span(f"📁 文件: {len(success_files)}/{len(all_results)}", className="me-3"),
                                html.Span(f"📊 总行数: {sum(r['rows'] for r in success_files):,}", className="me-3"),
                                html.Span(f"✅ 成功: {total_success:,}", className="me-3"),
                                html.Span(f"❌ 失败: {total_failed}", className="text-danger") if total_failed > 0 else ""
                            ], className="mb-2"),
                            html.Div([
                                html.Strong("📦 已导入门店:", className="me-2"),
                                html.Br(),
                                *[html.Div([
                                    html.Span(f"  • {r['store']}: ", className="text-muted"),
                                    html.Span(f"{r['success']:,} 条数据", className="text-success")
                                ]) for r in success_files]
                            ])
                        ])
                    ], className="mt-2")
                ])
            ], color="success", dismissable=True)
        else:
            status_alert = dbc.Alert([
                html.I(className="bi bi-x-circle me-2"),
                "❌ 所有文件导入失败，请检查文件格式"
            ], color="danger", dismissable=True)
        
        # 调试信息
        debug_info = html.Div([
            html.Details([
                html.Summary("📋 详细导入记录", className="text-muted small cursor-pointer"),
                html.Div([
                    *[html.Div([
                        html.Span(f"✅ {r['filename']}: ", className="text-success" if r['status'] == 'success' else "text-danger"),
                        html.Span(f"{r.get('success', 0):,}/{r.get('rows', 0):,} 行" if r['status'] == 'success' else r.get('message', '未知错误'))
                    ], className="mb-1") for r in all_results]
                ], className="mt-2 p-2 bg-light rounded")
            ], open=False)
        ])
        
        # 更新数据标签
        if uploaded_stores:
            data_label = f"数据库: {uploaded_stores[0]}"
        else:
            data_label = no_update
        
        return data_label, datetime.now().timestamp(), status_alert, debug_info
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ 上传处理失败: {error_detail}")
        
        return no_update, no_update, dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            html.Div([
                html.Strong("上传失败"),
                html.Br(),
                html.Small(str(e))
            ])
        ], color="danger", dismissable=True), ""


# ==================== 数据管理回调函数 ====================
if DATABASE_AVAILABLE:
    from database.data_lifecycle_manager import DataLifecycleManager

    @app.callback(
        Output('db-management-stats', 'children'),
        [Input('data-source-tabs', 'value'),
         Input('cleanup-result', 'children')]
    )
    def update_database_stats(tab_value, cleanup_trigger):
        """更新数据库统计信息"""
        if tab_value != 'data-management':
            return no_update
        
        try:
            manager = DataLifecycleManager()
            stats = manager.get_database_stats()
            manager.close()
            
            # 格式化数据库大小
            db_size = stats.get('db_size', 'N/A')
            min_date = stats.get('min_date', 'N/A')
            max_date = stats.get('max_date', 'N/A')
            date_range = f"{min_date} ~ {max_date}" if min_date != 'N/A' else 'N/A'
            
            return dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3(f"{stats['total_orders']:,}", className="text-primary mb-0"),
                            html.P("总订单数", className="text-muted mb-0 mt-1", style={'fontSize': '0.9rem'})
                        ], className="text-center py-3")
                    ], className="shadow-sm")
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3(f"{stats['store_count']}", className="text-success mb-0"),
                            html.P("门店数量", className="text-muted mb-0 mt-1", style={'fontSize': '0.9rem'})
                        ], className="text-center py-3")
                    ], className="shadow-sm")
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3(db_size, className="text-info mb-0", style={'fontSize': '1.8rem'}),
                            html.P("数据库大小", className="text-muted mb-0 mt-1", style={'fontSize': '0.9rem'})
                        ], className="text-center py-3")
                    ], className="shadow-sm")
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div(date_range, className="text-warning mb-0", style={'fontSize': '0.95rem', 'fontWeight': '500'}),
                            html.P("数据日期范围", className="text-muted mb-0 mt-1", style={'fontSize': '0.9rem'})
                        ], className="text-center py-3")
                    ], className="shadow-sm")
                ], md=3),
            ], className="mb-4")
            
        except Exception as e:
            print(f"❌ 获取数据库统计失败: {str(e)}")
            return dbc.Alert(f"获取统计信息失败: {str(e)}", color="danger")

    @app.callback(
        Output('cleanup-result', 'children', allow_duplicate=True),
        Input('preview-store-data-btn', 'n_clicks'),
        State('cleanup-store-select', 'value'),
        prevent_initial_call=True
    )
    def preview_store_data(n_clicks, store_name):
        """预览门店数据"""
        if not n_clicks or not store_name:
            return no_update
        
        try:
            manager = DataLifecycleManager()
            
            query = """
            SELECT 
                COUNT(*) as total_rows,
                MIN(date) as min_date,
                MAX(date) as max_date
            FROM orders
            WHERE store_name = :store_name
            """
            result = manager.session.execute(text(query), {'store_name': store_name}).first()
            
            manager.close()
            
            if result.total_rows == 0:
                return dbc.Alert(f"门店 [{store_name}] 没有数据", color="info", dismissable=True)
            
            return dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                html.Div([
                    html.Strong(f"门店数据预览: {store_name}"),
                    html.Br(),
                    html.Div([
                        f"• 订单数量: {result.total_rows:,} 条",
                        html.Br(),
                        f"• 数据范围: {result.min_date} 至 {result.max_date}",
                    ], className="mt-2")
                ])
            ], color="info", dismissable=True)
            
        except Exception as e:
            print(f"❌ 预览门店数据失败: {str(e)}")
            return dbc.Alert(f"预览失败: {str(e)}", color="danger", dismissable=True)

    @app.callback(
        Output('cleanup-result', 'children', allow_duplicate=True),
        Input('delete-store-btn', 'n_clicks'),
        State('cleanup-store-select', 'value'),
        prevent_initial_call=True
    )
    def delete_store_data(n_clicks, store_name):
        """删除门店数据"""
        print(f"\n{'='*70}")
        print(f"🔍 [删除回调] 被触发")
        print(f"   n_clicks: {n_clicks}")
        print(f"   store_name: {store_name}")
        print(f"{'='*70}")
        
        if not n_clicks:
            print("⚠️ n_clicks 为空，返回 no_update")
            return no_update
        
        if not store_name:
            print("⚠️ store_name 为空，返回提示")
            return dbc.Alert("请先选择要删除的门店", color="warning", dismissable=True)
        
        try:
            print(f"📊 开始删除门店: {store_name}")
            manager = DataLifecycleManager()
            
            # ✅ 使用 auto_confirm=True 跳过命令行交互式确认
            result = manager.clean_store_data(store_name=store_name, dry_run=False, auto_confirm=True)
            
            manager.close()
            
            # ✅ 修复：使用正确的键名 'deleted'
            deleted_count = result.get('deleted', 0)
            print(f"✅ 删除完成，删除行数: {deleted_count}")
            
            # 检查是否有错误
            if 'error' in result:
                return dbc.Alert(f"删除失败: {result['error']}", color="danger", dismissable=True)
            
            # 检查是否被取消
            if result.get('cancelled'):
                return dbc.Alert("操作已取消", color="info", dismissable=True)
            
            if deleted_count == 0:
                return dbc.Alert(f"门店 [{store_name}] 没有数据", color="info", dismissable=True)
            
            return dbc.Alert([
                html.I(className="bi bi-check-circle me-2"),
                html.Div([
                    html.Strong(f"✅ 已删除门店: {store_name}"),
                    html.Br(),
                    html.Div([
                        f"• 删除订单数: {deleted_count:,} 条",
                        html.Br(),
                        f"• 数据库已优化",
                        html.Br(),
                        html.Strong("• 请刷新页面查看最新统计", className="text-primary mt-2")
                    ], className="mt-2")
                ])
            ], color="success", dismissable=True, duration=10000)
            
        except Exception as e:
            print(f"❌ 删除门店数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return dbc.Alert(f"删除失败: {str(e)}", color="danger", dismissable=True)

    @app.callback(
        Output('cleanup-result', 'children', allow_duplicate=True),
        Input('optimize-database-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def optimize_database(n_clicks):
        """优化数据库"""
        if not n_clicks:
            return no_update
        
        try:
            manager = DataLifecycleManager()
            
            manager.optimize_database()
            
            manager.close()
            
            return dbc.Alert([
                html.I(className="bi bi-check-circle me-2"),
                html.Div([
                    html.Strong("✅ 数据库优化成功！"),
                    html.Br(),
                    html.Div([
                        "• VACUUM FULL - 已回收磁盘空间",
                        html.Br(),
                        "• REINDEX - 索引重建完成",
                        html.Br(),
                        "• ANALYZE - 统计信息更新完成",
                        html.Br(),
                        html.Small("💡 建议刷新页面查看最新门店列表", className="text-muted")
                    ], className="mt-2")
                ])
            ], color="success", dismissable=True, duration=10000)
            
        except Exception as e:
            print(f"❌ 优化数据库失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return dbc.Alert(f"优化失败: {str(e)}", color="danger", dismissable=True)

    # 动态刷新门店列表 - 页面加载和操作后自动更新下拉列表
    @app.callback(
        Output('cleanup-store-select', 'options'),
        [Input('delete-store-btn', 'n_clicks'),
         Input('optimize-database-btn', 'n_clicks'),
         Input('data-source-tabs', 'value')],  # ✅ 添加：切换到删除tab时加载
        prevent_initial_call=False  # ✅ 修改：允许初始加载
    )
    def refresh_store_dropdown(delete_clicks, optimize_clicks, tab_value):
        '''删除门店或优化数据库后刷新下拉列表，或切换到删除tab时加载'''
        try:
            # 如果数据库不可用，返回空列表
            if not DATABASE_AVAILABLE:
                return []
            
            from database.data_lifecycle_manager import DataLifecycleManager
            from sqlalchemy import text
            
            manager = DataLifecycleManager()
            
            query = '''
            SELECT DISTINCT store_name
            FROM orders
            ORDER BY store_name
            '''
            results = manager.session.execute(text(query)).fetchall()
            
            manager.close()
            
            options = [{'label': r[0], 'value': r[0]} for r in results]
            
            print(f"🔄 已刷新门店列表: {len(options)} 个门店")
            for opt in options:
                print(f"   - {opt['label']}")
            
            return options
            
        except Exception as e:
            print(f"❌ 刷新门店列表失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 失败时返回初始列表
            return INITIAL_STORE_OPTIONS


# ============================================================================

@app.callback(
    Output('debug-output', 'children'),
    Input('current-data-store', 'data')
)
def debug_stored_data(data):
    """调试回调：检查存储的数据"""
    if not data:
        print("⚠️ current-data-store 中没有数据")
        return ""
    
    df = pd.DataFrame(data)
    print(f"✅ current-data-store 数据加载成功")
    print(f"   - 数据行数: {len(df)}")
    print(f"   - 字段列表: {list(df.columns)}")
    
    # 检查关键字段
    if '场景' in df.columns:
        print(f"   ✓ 包含'场景'字段，唯一值: {df['场景'].unique()[:5]}")
    else:
        print(f"   ✗ 缺少'场景'字段")
    
    if '时段' in df.columns:
        print(f"   ✓ 包含'时段'字段，唯一值: {df['时段'].unique()[:5]}")
    else:
        print(f"   ✗ 缺少'时段'字段")
    
    return ""


# ==================== 可视化图表回调函数 ====================

# 辅助函数：创建空图表
def wrap_chart_component(component, height='450px'):
    """
    统一包装图表组件，确保ECharts/Plotly/空态提示都有一致的容器
    
    参数:
        component: DashECharts / go.Figure / html.Div
        height: 固定高度，避免布局抖动
    
    返回:
        html.Div - 统一的容器组件
    """
    # 如果是 Plotly Figure 对象，转换为 dcc.Graph
    if isinstance(component, go.Figure):
        component = dcc.Graph(
            figure=component,
            config={'displayModeBar': False},
            style={'height': '100%', 'width': '100%'}
        )
    
    # 统一包装在固定高度容器中
    return html.Div(
        component,
        style={
            'height': height,
            'width': '100%',
            'minHeight': height,  # 防止塌陷
            'overflow': 'hidden'   # 防止内容溢出
        }
    )


def create_empty_figure(title="暂无数据", message="请点击上方'🔍 开始诊断'按钮加载数据"):
    """创建友好的空数据图表（返回HTML div用于ECharts容器）"""
    return html.Div([
        html.Div(title, style={
            'textAlign': 'center',
            'fontSize': '18px',
            'fontWeight': 'bold',
            'color': '#666',
            'paddingTop': '80px'
        }),
        html.Div(message, style={
            'textAlign': 'center',
            'fontSize': '14px',
            'color': '#999',
            'paddingTop': '20px'
        })
    ], style={'height': '100%', 'width': '100%'})


def create_empty_plotly_figure(title="暂无数据", message="请点击上方'🔍 开始诊断'按钮加载数据"):
    """创建空态 Plotly Figure（用于 Output(..., 'figure') 的回调）
    
    返回一个带有友好提示的空白 go.Figure 对象，避免类型警告
    """
    fig = go.Figure()
    
    # 添加文本注释显示提示信息
    fig.add_annotation(
        text=f"<b>{title}</b><br><br>{message}",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=16, color="#999"),
        align="center"
    )
    
    # 配置布局
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=400
    )
    
    return fig

# 回调1: 分时段下滑分布图
@app.callback(
    Output('chart-slot-distribution', 'children'),
    Input('current-data-store', 'data')
)
def update_slot_distribution_chart(data):
    """分时段销量对比图（ECharts分组柱状图）- 显示当前周期 vs 对比周期"""
    # 🔧 文件日志
    import datetime
    # [DEBUG模式已禁用] 原文件日志已替换为标准logging
    # log_callback('update_slot_distribution_chart', ...)
    print(f"\n🎨 [分时段图表] 回调触发", flush=True)
    print(f"   数据类型: {type(data)}", flush=True)
    print(f"   数据长度: {len(data) if data else 0}", flush=True)
    
    if not data or len(data) == 0:
        print("   ⚠️ 数据为空，返回提示信息", flush=True)
        return html.Div([
            html.Div([
                html.I(className="bi bi-search", style={'fontSize': '48px', 'color': '#667eea', 'marginBottom': '15px'}),
                html.H5("⏰ 分时段销量对比", className="mb-3", style={'color': '#667eea'}),
                html.P("请点击上方🔍 开始诊断按钮加载数据", className="text-muted", style={'fontSize': '14px'})
            ], style={
                'textAlign': 'center',
                'padding': '60px 20px',
                'height': '400px',
                'display': 'flex',
                'flexDirection': 'column',
                'alignItems': 'center',
                'justifyContent': 'center'
            })
        ])
    
    df = pd.DataFrame(data)
    print(f"   DataFrame形状: {df.shape}", flush=True)
    print(f"   字段列表: {list(df.columns)}", flush=True)
    
    # 🔧 详细日志：检查关键字段
    # [DEBUG模式已禁用] 原文件日志已替换为标准logging
    # log_callback('update_slot_distribution_chart', ...)
    # 检查必需字段
    if '时段' not in df.columns:
        print("   ❌ 缺少'时段'字段", flush=True)
        return html.Div([
            dbc.Alert([
                html.I(className="bi bi-exclamation-triangle me-2"),
                "数据中缺少'时段'字段，请检查数据源"
            ], color="warning")
        ])
    
    # 检查销量字段（支持多种命名）
    # 查找模式：第X周销量、第X期销量、当前周期销量等
    current_qty_col = None
    compare_qty_col = None
    qty_cols = [col for col in df.columns if '销量' in col]
    
    # 🔧 添加详细日志：检查所有销量字段
    # [DEBUG模式已禁用] 原文件日志已替换为标准logging
    # log_callback('unknown', ...)
    print(f"   🔍 包含'销量'的列: {qty_cols}", flush=True)
    
    if len(qty_cols) >= 2:
        # 假设前两个销量列分别是当前周期和对比周期
        current_qty_col = qty_cols[0]
        compare_qty_col = qty_cols[1]
        print(f"   ✅ 找到销量字段: {current_qty_col}, {compare_qty_col}", flush=True)
        use_fallback = False
    else:
        print(f"   ⚠️ 缺少销量对比字段（需要至少2列），尝试降级方案", flush=True)
        use_fallback = True
    
    # 🔧 清洗时段数据：提取纯时段（去除场景混合）
    # 示例：'下午(14-18点)休闲零食' → '下午(14-18点)'
    #       '晚间(21-24点), 深夜(0-3点)' → '晚间(21-24点)'
    df['纯时段'] = df['时段'].apply(lambda x: str(x).split(',')[0].strip() if pd.notnull(x) else x)
    # 进一步提取：如果有中文后跟时间段，只保留时间段部分
    import re
    df['纯时段'] = df['纯时段'].apply(lambda x: re.search(r'[^a-zA-Z]*\([0-9-]+点\)', str(x)).group() if re.search(r'\([0-9-]+点\)', str(x)) else x)
    
    # 🎯 **新逻辑：分组柱状图对比（当前周期 vs 对比周期）**
    if not use_fallback:
        # 方案A：有销量数据 → 显示销量对比
        slot_stats = df.groupby('纯时段').agg({
            current_qty_col: 'sum',
            compare_qty_col: 'sum'
        }).reset_index()
        
        slot_stats.columns = ['时段', '当前周期销量', '对比周期销量']
        slot_stats = slot_stats.sort_values('当前周期销量', ascending=False)
        
        # 提取周期标签（从列名中提取，如"第40周销量" → "第40周"）
        current_label = current_qty_col.replace('销量', '').replace('(', '').replace(')', '') if '(' in current_qty_col else "当前周期"
        compare_label = compare_qty_col.replace('销量', '').replace('(', '').replace(')', '') if '(' in compare_qty_col else "对比周期"
        
        print(f"   📊 对比模式: {current_label} vs {compare_label}", flush=True)
        print(f"   统计结果: {len(slot_stats)} 个时段", flush=True)
        print(f"   时段数据预览:\n{slot_stats.head()}", flush=True)
        
        if len(slot_stats) == 0:
            return create_empty_figure("⏰ 分时段销量对比", "没有时段数据")
        
        # 🎨 使用 ECharts 分组柱状图
        if ECHARTS_AVAILABLE:
            # 📏 响应式高度计算
            num_slots = len(slot_stats)
            if num_slots <= 5:
                chart_height = 400
                font_size = 11
            elif num_slots <= 8:
                chart_height = 500
                font_size = 11
            else:
                chart_height = 550
                font_size = 10
            
            print(f"   📏 响应式配置: {num_slots}个时段 → 高度{chart_height}px, 字体{font_size}px", flush=True)
            
            option = {
                'title': {
                    'text': f'⏰ 分时段销量对比（{current_label} vs {compare_label}）',
                    'left': 'center',
                    'textStyle': {'fontSize': 16, 'fontWeight': 'bold'}
                },
                'tooltip': {
                    'trigger': 'axis',
                    'axisPointer': {'type': 'shadow'}
                },
                'legend': {
                    'data': [current_label, compare_label],
                    'top': 35,
                    'textStyle': {'fontSize': 12}
                },
                'grid': {
                    'left': '3%',
                    'right': '4%',
                    'bottom': '10%',
                    'top': '80px',
                    'containLabel': True
                },
                'xAxis': {
                    'type': 'category',
                    'data': slot_stats['时段'].tolist(),
                    'axisLabel': {'interval': 0, 'rotate': 30, 'fontSize': font_size}
                },
                'yAxis': {
                    'type': 'value',
                    'name': '销量',
                    'axisLabel': {'fontSize': 11}
                },
                'series': [
                    {
                        'name': current_label,
                        'type': 'bar',
                        'data': slot_stats['当前周期销量'].tolist(),
                        'itemStyle': {'color': '#ef5350'},  # 红色
                        'label': {
                            'show': True,
                            'position': 'top',
                            'fontSize': 10
                        }
                    },
                    {
                        'name': compare_label,
                        'type': 'bar',
                        'data': slot_stats['对比周期销量'].tolist(),
                        'itemStyle': {'color': '#42a5f5'},  # 蓝色
                        'label': {
                            'show': True,
                            'position': 'top',
                            'fontSize': 10
                        }
                    }
                ]
            }
            
            print(f"   ✅ ECharts图表配置生成成功", flush=True)
            
            return DashECharts(
                option=option,
                id='echarts-slot-distribution',
                style={'height': f'{chart_height}px', 'width': '100%'}
            )
    
    # 降级方案：统计下滑商品数
    slot_stats = df.groupby('纯时段').size().reset_index(name='下滑商品数')
    slot_stats.columns = ['时段', '下滑商品数']
    slot_stats = slot_stats.sort_values('下滑商品数', ascending=False)
    
    print(f"   ⚠️ 使用降级方案：统计下滑商品数", flush=True)
    print(f"   统计结果: {len(slot_stats)} 个时段", flush=True)
    
    if len(slot_stats) == 0:
        return create_empty_figure("⏰ 分时段下滑分布", "没有时段数据")
    
    # Plotly柱状图（降级方案）
    fig = go.Figure(data=[
        go.Bar(
            x=slot_stats['时段'],
            y=slot_stats['下滑商品数'],
            marker_color='indianred',
            text=slot_stats['下滑商品数'],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title='⏰ 分时段下滑商品分布',
        xaxis_title='时段',
        yaxis_title='下滑商品数',
        height=450,
        margin=dict(l=60, r=60, t=80, b=80)
    )
    
    # ✅ 使用统一包装函数，确保返回 dcc.Graph 而非裸 Figure
    return wrap_chart_component(fig, height='450px')


# 回调2: 分场景下滑分布（饼图）
@app.callback(
    Output('chart-scene-distribution', 'children'),
    Input('current-data-store', 'data')
)
def update_scene_distribution_chart(data):
    """分场景销量对比图（ECharts分组柱状图）- 显示当前周期 vs 对比周期"""
    # 🔧 文件日志
    import datetime
    # [DEBUG模式已禁用] 原文件日志已替换为标准logging
    # log_callback('update_scene_distribution_chart', ...)
    if not data or len(data) == 0:
        return html.Div([
            html.Div([
                html.I(className="bi bi-search", style={'fontSize': '48px', 'color': '#667eea', 'marginBottom': '15px'}),
                html.H5("🎭 分场景销量对比", className="mb-3", style={'color': '#667eea'}),
                html.P("请点击上方🔍 开始诊断按钮加载数据", className="text-muted", style={'fontSize': '14px'})
            ], style={
                'textAlign': 'center',
                'padding': '60px 20px',
                'height': '400px',
                'display': 'flex',
                'flexDirection': 'column',
                'alignItems': 'center',
                'justifyContent': 'center'
            })
        ])
    
    df = pd.DataFrame(data)
    print(f"\n🎨 [分场景图表] 数据字段: {list(df.columns)}", flush=True)
    
    # 检查必需字段
    if '场景' not in df.columns:
        return html.Div([
            dbc.Alert([
                html.I(className="bi bi-exclamation-triangle me-2"),
                "数据中缺少'场景'字段，请检查数据源"
            ], color="warning")
        ])
    
    # 🔧 清洗场景数据：提取第一个场景（去除组合场景）
    # 示例：'休闲零食, 早餐' → '休闲零食'
    #       '社交娱乐, 夜间社交' → '社交娱乐'
    df['纯场景'] = df['场景'].apply(lambda x: str(x).split(',')[0].strip() if pd.notnull(x) else x)
    
    # 检查销量字段（支持多种命名）
    # 查找模式：第X周销量、第X期销量、当前周期销量等
    current_qty_col = None
    compare_qty_col = None
    qty_cols = [col for col in df.columns if '销量' in col]
    
    print(f"   🔍 包含'销量'的列: {qty_cols}", flush=True)
    
    if len(qty_cols) >= 2:
        # 假设前两个销量列分别是当前周期和对比周期
        current_qty_col = qty_cols[0]
        compare_qty_col = qty_cols[1]
        print(f"   ✅ 找到销量字段: {current_qty_col}, {compare_qty_col}", flush=True)
        use_fallback = False
    else:
        print(f"   ⚠️ 缺少销量对比字段（需要至少2列），使用降级方案", flush=True)
        use_fallback = True
    
    # 🎯 **新逻辑：分组柱状图对比（当前周期 vs 对比周期）**
    if not use_fallback:
        # 方案A：有销量数据 → 显示销量对比
        scene_stats = df.groupby('纯场景').agg({
            current_qty_col: 'sum',
            compare_qty_col: 'sum'
        }).reset_index()
        
        scene_stats.columns = ['场景', '当前周期销量', '对比周期销量']
        scene_stats = scene_stats.sort_values('当前周期销量', ascending=False)
        
        # 提取周期标签
        current_label = current_qty_col.replace('销量', '').replace('(', '').replace(')', '') if '(' in current_qty_col else "当前周期"
        compare_label = compare_qty_col.replace('销量', '').replace('(', '').replace(')', '') if '(' in compare_qty_col else "对比周期"
        
        print(f"   📊 对比模式: {current_label} vs {compare_label}", flush=True)
        print(f"   统计结果: {len(scene_stats)} 个场景", flush=True)
        print(f"   场景数据预览:\n{scene_stats.head()}", flush=True)
        
        if len(scene_stats) == 0:
            return create_empty_figure("🎭 分场景销量对比", "没有场景数据")
        
        # 🎨 使用 ECharts 分组柱状图
        if ECHARTS_AVAILABLE:
            # 📏 响应式高度计算
            num_scenes = len(scene_stats)
            if num_scenes <= 5:
                chart_height = 400
                font_size = 11
            elif num_scenes <= 8:
                chart_height = 500
                font_size = 11
            else:
                chart_height = 600
                font_size = 10
            
            print(f"   📏 响应式配置: {num_scenes}个场景 → 高度{chart_height}px, 字体{font_size}px", flush=True)
            
            option = {
                'title': {
                    'text': f'🎭 分场景销量对比（{current_label} vs {compare_label}）',
                    'left': 'center',
                    'textStyle': {'fontSize': 16, 'fontWeight': 'bold'}
                },
                'tooltip': {
                    'trigger': 'axis',
                    'axisPointer': {'type': 'shadow'}
                },
                'legend': {
                    'data': [current_label, compare_label],
                    'top': 35,
                    'textStyle': {'fontSize': 12}
                },
                'grid': {
                    'left': '3%',
                    'right': '4%',
                    'bottom': '10%',
                    'top': '80px',
                    'containLabel': True
                },
                'xAxis': {
                    'type': 'category',
                    'data': scene_stats['场景'].tolist(),
                    'axisLabel': {'interval': 0, 'rotate': 30, 'fontSize': font_size}
                },
                'yAxis': {
                    'type': 'value',
                    'name': '销量',
                    'axisLabel': {'fontSize': 11}
                },
                'series': [
                    {
                        'name': current_label,
                        'type': 'bar',
                        'data': scene_stats['当前周期销量'].tolist(),
                        'itemStyle': {'color': '#ef5350'},  # 红色
                        'label': {
                            'show': True,
                            'position': 'top',
                            'fontSize': 10
                        }
                    },
                    {
                        'name': compare_label,
                        'type': 'bar',
                        'data': scene_stats['对比周期销量'].tolist(),
                        'itemStyle': {'color': '#42a5f5'},  # 蓝色
                        'label': {
                            'show': True,
                            'position': 'top',
                            'fontSize': 10
                        }
                    }
                ]
            }
            
            print(f"   ✅ ECharts图表配置生成成功", flush=True)
            
            return DashECharts(
                option=option,
                id='echarts-scene-distribution',
                style={'height': f'{chart_height}px', 'width': '100%'}
            )
    
    # 降级方案：统计下滑商品数
    scene_stats = df.groupby('纯场景').size().reset_index(name='下滑商品数')
    scene_stats.columns = ['场景', '下滑商品数']
    scene_stats = scene_stats.sort_values('下滑商品数', ascending=False)
    
    print(f"   ⚠️ 使用降级方案：统计下滑商品数", flush=True)
    print(f"   场景统计: {len(scene_stats)} 个场景", flush=True)
    
    if len(scene_stats) == 0:
        return create_empty_figure("🎭 分场景下滑分布", "没有场景数据")
    
    # Plotly饼图（降级方案）
    fig = go.Figure(go.Pie(
        labels=scene_stats['场景'],
        values=scene_stats['下滑商品数'],
        hole=0.4,
        marker=dict(colors=['#d32f2f', '#f57c00', '#fbc02d', '#388e3c', '#1976d2']),
        textinfo='label+percent'
    ))
    
    fig.update_layout(
        title='🎭 各场景下滑商品占比',
        height=450,
        margin=dict(l=60, r=60, t=80, b=80)
    )
    
    # ✅ 使用统一包装函数，确保返回 dcc.Graph 而非裸 Figure
    return wrap_chart_component(fig, height='450px')


# 回调3: 周期对比图（ECharts版本）
@app.callback(
    Output('chart-period-comparison', 'children'),
    Input('current-data-store', 'data')
)
def update_period_comparison_chart(data):
    """周期对比图（支持动态周期字段）- ECharts版本
    
    ✨ 新增功能：
    - 动态高度计算：根据商品数量自动调整图表高度
    - 响应式布局：配合 echarts_responsive.js 实现自适应
    """
    print(f"\n📊 [周期对比图-ECharts] 回调触发", flush=True)
    
    if not data or len(data) == 0:
        print("   ⚠️ 数据为空", flush=True)
        return html.Div([
            dbc.Alert([
                html.H6("暂无数据", className="mb-1"),
                html.P("请先点击「开始诊断」按钮生成诊断数据", className="mb-0")
            ], color="info", className="mt-3")
        ])
    
    df = pd.DataFrame(data)
    print(f"   数据行数: {len(df)}", flush=True)
    print(f"   字段列表: {list(df.columns)}", flush=True)
    
    # 🔧 动态查找周期字段（支持"第X周销量"、"第X天销量"等格式）
    sales_cols = [col for col in df.columns if '销量' in col and ('周' in col or '天' in col or '月' in col)]
    print(f"   找到销量字段: {sales_cols}", flush=True)
    
    if len(sales_cols) < 2:
        print("   ❌ 销量字段数量不足", flush=True)
        return html.Div([
            dbc.Alert("数据中缺少周期对比字段", color="warning", className="mt-3")
        ])
    
    # 假设第一个是当前周期，第二个是对比周期
    current_col = sales_cols[0]
    compare_col = sales_cols[1]
    
    print(f"   当前周期: {current_col}", flush=True)
    print(f"   对比周期: {compare_col}", flush=True)
    
    # 检查必需字段
    if '商品名称' not in df.columns:
        print("   ❌ 缺少商品名称字段", flush=True)
        return html.Div([
            dbc.Alert("数据中缺少'商品名称'字段", color="warning", className="mt-3")
        ])
    
    # 🔧 过滤掉当前周期销量为0的商品（已停售商品对对比图意义不大）
    df_filtered = df[df[current_col] > 0].copy()
    print(f"   过滤前商品数: {len(df)}, 过滤后: {len(df_filtered)}", flush=True)
    
    if len(df_filtered) == 0:
        print("   ⚠️ 所有商品当前周期销量为0", flush=True)
        return html.Div([
            dbc.Alert([
                html.H6("暂无可对比商品", className="mb-1"),
                html.P("所有下滑商品当前周期销量为0（可能已停售）", className="mb-0")
            ], color="warning", className="mt-3")
        ])
    
    # 取TOP10下滑商品（按变化幅度排序，只选仍在销售的商品）
    if '变化幅度%' in df_filtered.columns and '_变化幅度_数值' in df_filtered.columns:
        top_products = df_filtered.nsmallest(10, '_变化幅度_数值')[['商品名称', current_col, compare_col]].copy()
    elif '销量变化' in df_filtered.columns:
        top_products = df_filtered.nsmallest(10, '销量变化')[['商品名称', current_col, compare_col]].copy()
    else:
        top_products = df_filtered.head(10)[['商品名称', current_col, compare_col]].copy()
    
    print(f"   TOP10商品数: {len(top_products)}", flush=True)
    
    if len(top_products) == 0:
        return html.Div([
            dbc.Alert("没有符合条件的商品", color="info", className="mt-3")
        ])
    
    # 🔧 确保销量列是数值类型
    top_products[current_col] = pd.to_numeric(top_products[current_col], errors='coerce').fillna(0)
    top_products[compare_col] = pd.to_numeric(top_products[compare_col], errors='coerce').fillna(0)
    
    print(f"   销量数据样本:\n{top_products.head(3)}", flush=True)
    print(f"   {current_col} 数据类型: {top_products[current_col].dtype}", flush=True)
    print(f"   {current_col} 样本值: {top_products[current_col].tolist()[:3]}", flush=True)
    print(f"   {compare_col} 样本值: {top_products[compare_col].tolist()[:3]}", flush=True)
    
    # 提取周期标签（去掉"销量"两字）
    current_label = current_col.replace('销量', '').strip()
    compare_label = compare_col.replace('销量', '').strip()
    
    # 准备ECharts数据 - 确保转换为Python原生类型
    products = [str(name) for name in top_products['商品名称'].tolist()]
    current_values = [int(v) if pd.notna(v) else 0 for v in top_products[current_col].tolist()]
    compare_values = [int(v) if pd.notna(v) else 0 for v in top_products[compare_col].tolist()]
    
    print(f"   产品列表: {products[:3]}", flush=True)
    print(f"   {current_label} 值: {current_values[:3]}", flush=True)
    print(f"   {compare_label} 值: {compare_values[:3]}", flush=True)
    
    # 🎨 创建ECharts配置
    option = {
        'title': {
            'text': 'TOP10下滑商品周期对比',
            'left': 'center',
            'top': 5,
            'textStyle': {
                'fontSize': 14,
                'fontWeight': '600',
                'color': '#333'
            }
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {
                'type': 'shadow'
            }
        },
        'legend': {
            'data': [compare_label, current_label],
            'top': 35,
            'left': 'center',
            'itemGap': 20,
            'textStyle': {'fontSize': 12}
        },
        'grid': {
            'left': '3%',
            'right': '4%',
            'bottom': '20%',
            'top': '80px',
            'containLabel': True
        },
        'xAxis': {
            'type': 'category',
            'data': products,
            'axisLabel': {
                'rotate': 45,
                'fontSize': 10,
                'interval': 0,
                'overflow': 'truncate',
                'width': 60
            },
            'axisLine': {'lineStyle': {'color': '#ccc'}},
            'axisTick': {'alignWithLabel': True}
        },
        'yAxis': {
            'type': 'value',
            'name': '销量',
            'nameTextStyle': {'fontSize': 11},
            'axisLine': {'lineStyle': {'color': '#ccc'}},
            'splitLine': {'lineStyle': {'type': 'dashed', 'color': '#eee'}}
        },
        'series': [
            {
                'name': compare_label,
                'type': 'bar',
                'data': compare_values,
                'itemStyle': {
                    'color': '#1976d2',
                    'borderRadius': [4, 4, 0, 0]
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'fontSize': 10
                },
                'barMaxWidth': 30
            },
            {
                'name': current_label,
                'type': 'bar',
                'data': current_values,
                'itemStyle': {
                    'color': '#d32f2f',
                    'borderRadius': [4, 4, 0, 0]
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'fontSize': 10
                },
                'barMaxWidth': 30
            }
        ]
    }
    
    print(f"   ✅ ECharts图表配置生成成功", flush=True)
    
    # 📏 使用工具函数动态计算高度和配置
    num_products = len(top_products)
    responsive_config = create_responsive_echarts_config(
        data_count=num_products,
        chart_type='bar',
        include_height=True,
        include_grid=True,
        include_font=True
    )
    
    dynamic_height = responsive_config['height']
    print(f"   📏 响应式配置: {num_products}个商品 → 高度{dynamic_height}px, 字体{responsive_config['fontSize']}px", flush=True)
    
    # 更新grid配置（如果数据量大，调整底部空间）
    if num_products > 10:
        option['grid'] = responsive_config['grid']
        print(f"   🎯 已应用动态grid配置: bottom={option['grid']['bottom']}", flush=True)
    
    # 返回ECharts组件 - 使用动态计算的高度
    return DashECharts(
        option=option,
        id='echarts-period-comparison',
        style={'height': f'{dynamic_height}px', 'width': '100%'}  # 动态高度
    )


# 回调4: 分类损失排名图
@app.callback(
    Output('chart-category-loss', 'figure'),
    Input('current-data-store', 'data')
)
def update_category_loss_chart(data):
    """分类收入损失排名图"""
    print(f"\n📉 [分类损失图] 回调触发", flush=True)
    
    if not data or len(data) == 0:
        print("   ⚠️ 数据为空", flush=True)
        return create_empty_plotly_figure("📉 分类损失排名", "请先点击「开始诊断」按钮")
    
    df = pd.DataFrame(data)
    print(f"   数据行数: {len(df)}", flush=True)
    print(f"   字段列表: {list(df.columns)[:15]}...", flush=True)
    
    # 检查必需字段
    if '一级分类名' not in df.columns:
        print("   ❌ 缺少'一级分类名'字段", flush=True)
        return create_empty_plotly_figure("📉 分类损失排名", "数据中缺少'一级分类名'字段")
    
    if '商品名称' not in df.columns:
        print("   ❌ 缺少'商品名称'字段", flush=True)
        return create_empty_plotly_figure("📉 分类损失排名", "数据中缺少'商品名称'字段")
    
    # 检查收入变化字段
    if '收入变化' not in df.columns:
        print("   ❌ 缺少'收入变化'字段", flush=True)
        return create_empty_plotly_figure("📉 分类损失排名", "数据中缺少'收入变化'字段")
    
    # 确保收入变化是数值类型
    df['收入变化'] = pd.to_numeric(df['收入变化'], errors='coerce').fillna(0)
    
    # 按分类汇总收入损失
    try:
        category_loss = df.groupby('一级分类名').agg({
            '收入变化': 'sum',
            '商品名称': 'count'
        }).reset_index()
        
        category_loss.columns = ['分类', '收入损失', '下滑商品数']
        category_loss['收入损失'] = -category_loss['收入损失']  # 转换为正数（损失）
        category_loss = category_loss.sort_values('收入损失', ascending=False).head(5)  # TOP5损失最大的
        
        print(f"   统计结果: {len(category_loss)} 个分类", flush=True)
        print(f"   TOP分类:\n{category_loss}", flush=True)
        
    except Exception as e:
        print(f"   ❌ 聚合失败: {e}", flush=True)
        return create_empty_plotly_figure("📉 分类损失排名", f"数据聚合失败: {str(e)}")
    
    if len(category_loss) == 0:
        return create_empty_plotly_figure("📉 分类损失排名", "没有分类数据")
    
    # 创建Plotly横向柱状图
    fig = go.Figure(data=[
        go.Bar(
            y=category_loss['分类'],
            x=category_loss['收入损失'],
            orientation='h',
            marker_color='#d32f2f',
            text=category_loss['收入损失'].apply(lambda x: f'¥{x:,.0f}'),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>收入损失: ¥%{x:,.0f}<br>下滑商品数: %{customdata}<extra></extra>',
            customdata=category_loss['下滑商品数']
        )
    ])
    
    fig.update_layout(
        title='📉 分类收入损失排名（TOP5）',
        xaxis_title='收入损失（元）',
        yaxis_title='',
        height=320,
        margin=dict(l=100, r=50, t=60, b=50),
        font=dict(family='Microsoft YaHei', size=11),
        template='plotly_white'
    )
    
    print(f"   ✅ 图表生成成功", flush=True)
    return fig  # 直接返回Figure对象，不要包装


# 回调4: 分类TOP商品图
@app.callback(
    Output('chart-category-top-products', 'figure'),
    Input('current-data-store', 'data')
)
def update_category_top_products_chart(data):
    """各分类下滑TOP商品"""
    if not data or len(data) == 0:
        return create_empty_plotly_figure("🔻 各分类TOP商品")
    
    df = pd.DataFrame(data)
    
    if '一级分类名' not in df.columns or '销量变化' not in df.columns:
        return create_empty_plotly_figure("🔻 各分类TOP商品", "数据中缺少'一级分类名'或'销量变化'字段")
    
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
        return create_empty_plotly_figure("🔻 各分类TOP商品", "没有符合条件的商品数据")
    
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
    
    return fig  # 直接返回Figure对象，不要包装


# 回调5: 四维散点图
@app.callback(
    Output('chart-scatter-4d', 'figure'),
    Input('current-data-store', 'data')
)
def update_scatter_4d_chart(data):
    """四维散点图：销量×利润×售价×毛利率"""
    if not data or len(data) == 0:
        return create_empty_plotly_figure("💰 四维分析")
    
    df = pd.DataFrame(data)
    
    required_cols = ['销量变化', '利润变化', '商品实售价', '平均毛利率%']
    if not all(col in df.columns for col in required_cols):
        return create_empty_plotly_figure("💰 四维分析", "数据中缺少必要字段（销量变化、利润变化、商品实售价、平均毛利率%）")
    
    # 🔧 将百分比字符串转换为数值
    def parse_percentage(val):
        """将 '44.5%' 转换为 44.5"""
        if isinstance(val, str) and val.endswith('%'):
            try:
                return float(val.replace('%', ''))
            except:
                return 0
        return float(val) if val else 0
    
    # 🔧 将价格字符串转换为数值
    def parse_price(val):
        """将 '¥23.5' 或 '¥23.5¥23.5' 转换为 23.5"""
        if isinstance(val, str):
            # 移除所有 ¥ 符号和空格
            cleaned = val.replace('¥', '').replace(' ', '')
            # 如果重复了（如 "23.523.5"），取第一个数字
            try:
                # 尝试直接转换
                return float(cleaned)
            except:
                # 如果失败，可能是重复格式，提取第一个数字
                import re
                match = re.search(r'(\d+\.?\d*)', cleaned)
                if match:
                    return float(match.group(1))
                return 10.0  # 默认值
        return float(val) if val else 10.0
    
    # 取TOP30避免过于拥挤
    scatter_df = df.nlargest(30, '销量变化').copy()
    scatter_df['毛利率_数值'] = scatter_df['平均毛利率%'].apply(parse_percentage)
    scatter_df['售价_数值'] = scatter_df['实收价格'].apply(parse_price)  # 🔧 解析价格
    
    fig = go.Figure(data=[
        go.Scatter(
            x=scatter_df['销量变化'],
            y=scatter_df['利润变化'],
            mode='markers',
            marker=dict(
                size=scatter_df['售价_数值'] * 2,  # 🔧 使用数值版本的售价
                color=scatter_df['毛利率_数值'],  # 🔧 使用数值版本的毛利率
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title='毛利率%'),
                line=dict(width=1, color='white')
            ),
            text=scatter_df['商品名称'],
            customdata=scatter_df['售价_数值'],  # 🔧 传递数值版本的售价用于悬停
            hovertemplate='<b>%{text}</b><br>销量变化: %{x:.2f}<br>利润变化: %{y:.2f}<br>售价: ¥%{customdata:.2f}<br>毛利率: %{marker.color:.1f}%<extra></extra>'
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
    
    return fig  # 直接返回Figure对象，不要包装


# 回调7: 价格分布图（按分类）
@app.callback(
    Output('chart-price-distribution', 'figure'),
    Input('current-data-store', 'data')
)
def update_price_distribution_chart(data):
    """按分类显示商品价格分布箱线图"""
    if not data or len(data) == 0:
        return create_empty_plotly_figure("💵 商品价格分布")
    
    df = pd.DataFrame(data)
    
    if '商品实售价' not in df.columns:
        return create_empty_plotly_figure("💵 商品价格分布", "数据中缺少'商品实售价'字段")
    
    # 检查是否有分类字段
    if '一级分类名' in df.columns:
        # 按分类显示价格分布
        categories = sorted(df['一级分类名'].dropna().unique())
        
        fig = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
        
        for i, category in enumerate(categories):
            category_data = df[df['一级分类名'] == category]['实收价格']
            
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
                y=df['实收价格'],
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
    
    return fig  # 直接返回Figure对象，不要包装


# 回调8: 收入损失TOP10（瀑布图）
@app.callback(
    Output('chart-revenue-top10', 'children'),
    Input('current-data-store', 'data')
)
def update_revenue_top10_chart(data):
    """收入对比TOP10商品（ECharts分组柱状图）- 显示当前周期 vs 对比周期"""
    # 🔧 文件日志
    import datetime
    # [DEBUG模式已禁用] 原文件日志已替换为标准logging
    # log_callback('update_revenue_top10_chart', ...)
    if not data or len(data) == 0:
        print("⚠️ [收入TOP10] 没有数据", flush=True)
        return html.Div([
            html.Div([
                html.I(className="bi bi-search", style={'fontSize': '48px', 'color': '#667eea', 'marginBottom': '15px'}),
                html.H5("💸 收入对比TOP10", className="mb-3", style={'color': '#667eea'}),
                html.P("请点击上方🔍 开始诊断按钮加载数据", className="text-muted", style={'fontSize': '14px'})
            ], style={
                'textAlign': 'center',
                'padding': '60px 20px',
                'height': '400px',
                'display': 'flex',
                'flexDirection': 'column',
                'alignItems': 'center',
                'justifyContent': 'center'
            })
        ])
    
    df = pd.DataFrame(data)
    print(f"\n🔍 [收入TOP10] 数据字段: {list(df.columns)}", flush=True)
    print(f"   数据行数: {len(df)}", flush=True)
    
    # 检查必需字段
    if '商品名称' not in df.columns:
        return create_empty_plotly_figure("💸 收入对比TOP10", "数据中缺少'商品名称'字段")
    
    # 查找当前周期和对比周期的收入字段
    # 查找模式：第X周预计收入、第X周收入、当前周期收入等
    current_revenue_col = None
    compare_revenue_col = None
    revenue_cols = [col for col in df.columns if '收入' in col and '变化' not in col and '损失' not in col]
    
    print(f"   🔍 包含'收入'的列: {revenue_cols}", flush=True)
    
    if len(revenue_cols) >= 2:
        # 假设前两个收入列分别是当前周期和对比周期
        current_revenue_col = revenue_cols[0]
        compare_revenue_col = revenue_cols[1]
        print(f"   ✅ 找到收入字段: {current_revenue_col}, {compare_revenue_col}", flush=True)
        use_fallback = False
    else:
        print(f"   ⚠️ 缺少收入对比字段（需要至少2列），尝试降级方案", flush=True)
        use_fallback = True
    
    if use_fallback:
        # 降级方案：使用收入变化
        if '收入变化' not in df.columns:
            return create_empty_plotly_figure("💸 收入对比TOP10", "数据中缺少收入相关字段")
        
        # 计算收入损失并使用瀑布图
        df['收入损失'] = -df['收入变化']
        top10_revenue = df.nlargest(10, '收入损失')[['商品名称', '收入变化']].copy()
        
        # Plotly瀑布图（降级方案）
        fig = go.Figure(go.Waterfall(
            orientation="v",
            measure=["relative"] * len(top10_revenue),
            x=top10_revenue['商品名称'].tolist(),
            y=top10_revenue['收入损失'].tolist(),
            decreasing={"marker": {"color": "#d32f2f"}},
            text=[f"¥{abs(val):,.0f}" for val in top10_revenue['收入变化'].tolist()],
            textposition="outside"
        ))
        
        fig.update_layout(
            title='💸 收入损失TOP10商品',
            yaxis_title='收入损失（元）',
            height=450,
            margin=dict(l=70, r=60, t=80, b=120),
            xaxis={'tickangle': -45}
        )
        
        # ✅ 使用统一包装函数，确保返回 dcc.Graph 而非裸 Figure
        
        return wrap_chart_component(fig, height='450px')
    
    # 🎯 **新逻辑：分组柱状图对比（当前周期 vs 对比周期）**
    print(f"   ✅ 找到收入字段: {current_revenue_col}, {compare_revenue_col}", flush=True)
    
    # 确保数值型
    df[current_revenue_col] = pd.to_numeric(df[current_revenue_col], errors='coerce').fillna(0)
    df[compare_revenue_col] = pd.to_numeric(df[compare_revenue_col], errors='coerce').fillna(0)
    
    # 计算收入变化，按损失排序
    df['收入变化'] = df[current_revenue_col] - df[compare_revenue_col]
    df['收入损失'] = -df['收入变化']
    
    # 获取TOP10损失最大的商品
    top10_revenue = df.nlargest(10, '收入损失')[['商品名称', current_revenue_col, compare_revenue_col]].copy()
    top10_revenue.columns = ['商品名称', '当前周期收入', '对比周期收入']
    top10_revenue = top10_revenue.sort_values('对比周期收入', ascending=False)  # 按对比周期降序排列
    
    # 提取周期标签
    current_label = current_revenue_col.replace('收入', '').replace('(', '').replace(')', '') if '(' in current_revenue_col else "当前周期"
    compare_label = compare_revenue_col.replace('收入', '').replace('(', '').replace(')', '') if '(' in compare_revenue_col else "对比周期"
    
    print(f"   📊 对比模式: {current_label} vs {compare_label}", flush=True)
    print(f"   TOP10数据预览:\n{top10_revenue.head()}", flush=True)
    
    if len(top10_revenue) == 0:
        return create_empty_plotly_figure("💸 收入对比TOP10", "没有收入数据")
    
    # 🎨 使用 ECharts 分组柱状图
    if ECHARTS_AVAILABLE:
        # 📏 响应式高度计算
        num_products = len(top10_revenue)
        if num_products <= 5:
            chart_height = 400
            font_size = 11
        elif num_products <= 8:
            chart_height = 550
            font_size = 10
        else:
            chart_height = 650
            font_size = 10
        
        print(f"   📏 响应式配置: {num_products}个商品 → 高度{chart_height}px, 字体{font_size}px", flush=True)
        
        option = {
            'title': {
                'text': f'💸 收入对比TOP10（{current_label} vs {compare_label}）',
                'left': 'center',
                'textStyle': {'fontSize': 16, 'fontWeight': 'bold'}
            },
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {'type': 'shadow'}
            },
            'legend': {
                'data': [current_label, compare_label],
                'top': 35,
                'textStyle': {'fontSize': 12}
            },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '25%',
                'top': '80px',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'data': top10_revenue['商品名称'].tolist(),
                'axisLabel': {'interval': 0, 'rotate': 45, 'fontSize': font_size}
            },
            'yAxis': {
                'type': 'value',
                'name': '收入（元）',
                'axisLabel': {'fontSize': 11, 'formatter': '¥{value}'}
            },
            'series': [
                {
                    'name': current_label,
                    'type': 'bar',
                    'data': top10_revenue['当前周期收入'].tolist(),
                    'itemStyle': {'color': '#ef5350'},  # 红色
                    'label': {
                        'show': True,
                        'position': 'top',
                        'fontSize': 9,
                        'formatter': '¥{c}'
                    }
                },
                {
                    'name': compare_label,
                    'type': 'bar',
                    'data': top10_revenue['对比周期收入'].tolist(),
                    'itemStyle': {'color': '#42a5f5'},  # 蓝色
                    'label': {
                        'show': True,
                        'position': 'top',
                        'fontSize': 9,
                        'formatter': '¥{c}'
                    }
                }
            ]
        }
        
        print(f"   ✅ ECharts图表配置生成成功", flush=True)
        
        return DashECharts(
            option=option,
            id='echarts-revenue-top10',
            style={'height': f'{chart_height}px', 'width': '100%'}
        )
    
    # 降级方案：Plotly分组柱状图
    fig = go.Figure(data=[
        go.Bar(
            name=current_label,
            x=top10_revenue['商品名称'],
            y=top10_revenue['当前周期收入'],
            marker_color='#ef5350',
            text=[f"¥{val:,.0f}" for val in top10_revenue['当前周期收入']],
            textposition='outside'
        ),
        go.Bar(
            name=compare_label,
            x=top10_revenue['商品名称'],
            y=top10_revenue['对比周期收入'],
            marker_color='#42a5f5',
            text=[f"¥{val:,.0f}" for val in top10_revenue['对比周期收入']],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title=f'💸 收入对比TOP10（{current_label} vs {compare_label}）',
        xaxis_title='',
        yaxis_title='收入（元）',
        barmode='group',
        height=450,
        margin=dict(l=70, r=60, t=80, b=120),
        xaxis={'tickangle': -45},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
    
    # ✅ 使用统一包装函数，确保返回 dcc.Graph 而非裸 Figure
    
    return wrap_chart_component(fig, height='450px')


# 回调9: 分类树状图
@app.callback(
    Output('chart-category-treemap', 'figure'),
    Input('current-data-store', 'data')
)
def update_category_treemap_chart(data):
    """显示三级分类收入损失树状图"""
    if not data or len(data) == 0:
        return create_empty_plotly_figure("🌳 分类树状图")
    
    df = pd.DataFrame(data)
    
    # 检查必需字段
    required_cols = ['一级分类名', '三级分类名', '商品名称', '收入变化']
    if not all(col in df.columns for col in required_cols):
        return create_empty_plotly_figure("🌳 分类树状图", "数据中缺少必需字段")
    
    # 计算收入损失和变化幅度
    treemap_df = df.copy()
    treemap_df['收入损失绝对值'] = treemap_df['收入变化'].abs()
    
    # 计算变化幅度%
    if '变化幅度%' not in treemap_df.columns:
        if '本期销量' in treemap_df.columns and '上期销量' in treemap_df.columns:
            treemap_df['变化幅度%'] = ((treemap_df['本期销量'] - treemap_df['上期销量']) / treemap_df['上期销量'] * 100).fillna(0)
        else:
            treemap_df['变化幅度%'] = -50  # 默认值
    
    # 填充缺失值
    treemap_df['一级分类名'] = treemap_df['一级分类名'].fillna('未分类')
    treemap_df['三级分类名'] = treemap_df['三级分类名'].fillna('其他')
    
    # 创建树状图
    fig = px.treemap(
        treemap_df,
        path=['一级分类名', '三级分类名', '商品名称'],
        values='收入损失绝对值',
        color='变化幅度%',
        color_continuous_scale='Reds',
        color_continuous_midpoint=0,
        hover_data={
            '收入损失绝对值': ':,.0f',
            '变化幅度%': ':.1f'
        },
        labels={
            '收入损失绝对值': '收入损失（元）',
            '变化幅度%': '变化幅度（%）'
        }
    )
    
    fig.update_traces(
        textposition="middle center",
        textfont_size=12,
        hovertemplate='<b>%{label}</b><br>收入损失: ¥%{value:,.0f}<br>变化幅度: %{color:.1f}%<extra></extra>'
    )
    
    fig.update_layout(
        title='🌳 三级分类收入损失树状图',
        height=500,
        margin=dict(l=10, r=10, t=60, b=10)
    )
    
    return fig  # 直接返回Figure对象，不要包装


# 回调10: 时段×场景热力图
@app.callback(
    Output('chart-slot-scene-heatmap', 'figure'),
    Input('current-data-store', 'data')
)
def update_slot_scene_heatmap_chart(data):
    """显示时段×场景下滑商品数热力图"""
    if not data or len(data) == 0:
        return create_empty_plotly_figure("🔥 时段×场景热力图")
    
    df = pd.DataFrame(data)
    
    # 检查必需字段（注意：字段名是"时段"和"场景"，不是"诊断时段"和"诊断场景"）
    if '时段' not in df.columns or '场景' not in df.columns:
        return create_empty_plotly_figure("🔥 时段×场景热力图", "数据中缺少时段或场景字段")
    
    # 创建交叉透视表：统计每个(时段, 场景)组合的下滑商品数
    heatmap_df = df.groupby(['场景', '时段']).size().reset_index(name='下滑商品数')
    
    # 转换为矩阵格式
    heatmap_matrix = heatmap_df.pivot(index='场景', columns='时段', values='下滑商品数').fillna(0)
    
    if heatmap_matrix.empty:
        return create_empty_plotly_figure("🔥 时段×场景热力图", "没有足够的数据生成热力图")
    
    # 创建热力图
    fig = px.imshow(
        heatmap_matrix,
        labels=dict(x="时段", y="场景", color="下滑商品数"),
        x=heatmap_matrix.columns.tolist(),
        y=heatmap_matrix.index.tolist(),
        color_continuous_scale='Reds',
        aspect="auto",
        text_auto=True
    )
    
    fig.update_traces(
        hovertemplate='<b>场景:</b> %{y}<br><b>时段:</b> %{x}<br><b>下滑商品数:</b> %{z}<extra></extra>',
        textfont={"size": 14}
    )
    
    fig.update_layout(
        title='🔥 时段×场景下滑商品数热力图',
        height=500,
        margin=dict(l=100, r=50, t=80, b=80),
        xaxis_title='诊断时段',
        yaxis_title='诊断场景'
    )
    
    # 调整坐标轴
    fig.update_xaxes(side="bottom")
    fig.update_yaxes(side="left")
    
    return fig  # 直接返回Figure对象，不要包装


# 回调11: 热力图详细数据表格
@app.callback(
    [Output('heatmap-detail-table', 'columns'),
     Output('heatmap-detail-table', 'data')],
    Input('current-data-store', 'data')
)
def update_heatmap_detail_table(data):
    """生成时段×场景交叉分析的详细数据表格"""
    if not data or len(data) == 0:
        return [], []
    
    df = pd.DataFrame(data)
    
    # 检查必需字段（注意：字段名是"时段"和"场景"）
    if '时段' not in df.columns or '场景' not in df.columns:
        return [], []
    
    # 创建交叉分析表
    # 方式1：统计每个(场景, 时段)组合的下滑商品数
    agg_dict = {
        '商品名称': 'count',  # 下滑商品数
    }
    
    # 动态添加存在的字段
    if '销量变化' in df.columns:
        agg_dict['销量变化'] = 'sum'  # 总销量损失
    if '收入变化' in df.columns:
        agg_dict['收入变化'] = 'sum'  # 总收入损失
    if '_变化幅度_数值' in df.columns:
        agg_dict['_变化幅度_数值'] = 'mean'  # 平均下滑幅度
    
    cross_df = df.groupby(['场景', '时段']).agg(agg_dict).reset_index()
    
    # 重命名列（根据实际存在的列）
    column_mapping = {
        '场景': '场景',
        '时段': '时段',
        '商品名称': '下滑商品数'
    }
    
    if '销量变化' in cross_df.columns:
        column_mapping['销量变化'] = '总销量损失'
    if '收入变化' in cross_df.columns:
        column_mapping['收入变化'] = '总收入损失'
    if '_变化幅度_数值' in cross_df.columns:
        column_mapping['_变化幅度_数值'] = '平均下滑幅度%'
    
    cross_df = cross_df.rename(columns=column_mapping)
    
    # 格式化数值（只格式化存在的列）
    if '总销量损失' in cross_df.columns:
        cross_df['总销量损失'] = cross_df['总销量损失'].apply(lambda x: int(x))
    if '总收入损失' in cross_df.columns:
        cross_df['总收入损失'] = cross_df['总收入损失'].apply(lambda x: f"¥{x:,.0f}")
    if '平均下滑幅度%' in cross_df.columns:
        cross_df['平均下滑幅度%'] = cross_df['平均下滑幅度%'].apply(lambda x: f"{x:.1f}%")
    
    # 按下滑商品数降序排列
    cross_df = cross_df.sort_values('下滑商品数', ascending=False)
    
    # 定义表格列（根据实际存在的列动态生成）
    columns = [
        {'name': '场景', 'id': '场景'},
        {'name': '时段', 'id': '时段'},
        {'name': '下滑商品数', 'id': '下滑商品数', 'type': 'numeric'}
    ]
    
    # 添加存在的列
    if '总销量损失' in cross_df.columns:
        columns.append({'name': '总销量损失', 'id': '总销量损失', 'type': 'numeric'})
    if '总收入损失' in cross_df.columns:
        columns.append({'name': '总收入损失', 'id': '总收入损失'})
    if '平均下滑幅度%' in cross_df.columns:
        columns.append({'name': '平均下滑幅度', 'id': '平均下滑幅度%'})
    
    return columns, cross_df.to_dict('records')


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
        return "商品详情", "请选择商品", "无数据", create_empty_plotly_figure("暂无趋势数据")
    
    row_index = active_cell['row']
    if row_index >= len(table_data):
        return "商品详情", "数据错误", "无数据", create_empty_plotly_figure("暂无趋势数据")
    
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



# ==================== 辅助函数：图表生成 ====================

def create_category_cost_chart_echarts(df):
    """创建商品成本分类分析图表 - ECharts版本"""
    if '一级分类名' not in df.columns or '商品采购成本' not in df.columns:
        return html.Div("⚠️ 缺少必要字段", className="text-center text-muted p-5")
    
    # 按一级分类统计商品成本
    category_cost = df.groupby('一级分类名').agg({
        '商品采购成本': 'sum',
        '商品名称': 'count'
    }).reset_index()
    category_cost.columns = ['分类', '总成本', '商品数量']
    category_cost = category_cost.sort_values('总成本', ascending=False).head(10)
    
    # 格式化数据
    formatted_costs = [format_number(v) for v in category_cost['总成本'].tolist()]
    formatted_counts = [format_number(v) for v in category_cost['商品数量'].tolist()]
    
    # 预处理标签数据（用于显示）
    cost_labels = [f'¥{x/1000:.1f}k' if x >= 1000 else f'¥{x:.0f}' for x in category_cost['总成本']]
    
    # 📏 响应式高度计算
    num_categories = len(category_cost)
    if num_categories <= 5:
        chart_height = 380
        font_size = 11
    elif num_categories <= 8:
        chart_height = 420
        font_size = 11
    else:
        chart_height = 480
        font_size = 10
    
    # ECharts 配置
    option = {
        'title': dict(COMMON_TITLE, text='🏆 TOP 10 分类成本排行'),
        'tooltip': dict(COMMON_TOOLTIP, 
                       axisPointer={'type': 'cross'},
                       formatter='{b}<br/>💰 总成本: ¥{c0}<br/>📦 商品数量: {c1}'),
        'legend': dict(COMMON_LEGEND, data=['总成本', '商品数量']),
        'grid': COMMON_GRID,
        'xAxis': {
            'type': 'category',
            'data': category_cost['分类'].tolist(),
            'axisLabel': dict(COMMON_AXIS_LABEL, rotate=35, fontSize=font_size, interval=0),
            'axisLine': {'lineStyle': {'color': 'rgba(0,0,0,0.1)'}},
            'axisTick': {'show': False}
        },
        'yAxis': [
            {
                'type': 'value',
                'name': '💰 总成本 (¥)',
                'nameTextStyle': {'color': COMMON_COLORS['blue'][2], 'fontSize': 12, 'fontWeight': 'bold'},
                'axisLabel': COMMON_AXIS_LABEL,
                'splitLine': COMMON_SPLIT_LINE
            },
            {
                'type': 'value',
                'name': '📦 商品数量',
                'nameTextStyle': {'color': COMMON_COLORS['red'][0], 'fontSize': 12, 'fontWeight': 'bold'},
                'axisLabel': COMMON_AXIS_LABEL,
                'splitLine': {'show': False}
            }
        ],
        'series': [
            {
                'name': '总成本',
                'type': 'bar',
                'data': [{'value': v, 'label': l} for v, l in zip(formatted_costs, cost_labels)],
                'yAxisIndex': 0,
                'barWidth': '50%',
                'itemStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': COMMON_COLORS['blue'][0]},
                            {'offset': 0.5, 'color': COMMON_COLORS['blue'][2]},
                            {'offset': 1, 'color': COMMON_COLORS['blue'][4]}
                        ]
                    },
                    'borderRadius': [8, 8, 0, 0],
                    'shadowColor': 'rgba(0,0,0,0.2)',
                    'shadowBlur': 10
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': '{@label}',
                    'fontSize': 11,
                    'fontWeight': 'bold',
                    'color': '#2c3e50'
                },
                'emphasis': {
                    'itemStyle': {
                        'shadowColor': 'rgba(0,0,0,0.5)',
                        'shadowBlur': 20
                    }
                },
                'animationDelay': '{dataIndex} * 50'
            },
            {
                'name': '商品数量',
                'type': 'line',
                'data': formatted_counts,
                'yAxisIndex': 1,
                'smooth': True,
                'symbol': 'circle',
                'symbolSize': 10,
                'lineStyle': {'width': 4, 'color': COMMON_COLORS['red'][0]},
                'itemStyle': {'color': COMMON_COLORS['red'][0], 'borderWidth': 3, 'borderColor': '#fff'},
                'areaStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': 'rgba(255,107,107,0.3)'},
                            {'offset': 1, 'color': 'rgba(255,107,107,0.05)'}
                        ]
                    }
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'fontSize': 11,
                    'fontWeight': 'bold',
                    'color': COMMON_COLORS['red'][0]
                }
            }
        ],
        **COMMON_ANIMATION
    }
    
    return DashECharts(
        option=option,
        id='category-cost-chart-echarts',
        style={'height': f'{chart_height}px', 'width': '100%'}
    )


def create_category_cost_chart(df):
    """创建商品成本分类分析图表 - 智能选择版本"""
    if ECHARTS_AVAILABLE:
        return create_category_cost_chart_echarts(df)
    
    # Plotly 备份方案（保持原有代码）
    if '一级分类名' not in df.columns or '商品采购成本' not in df.columns:
        return go.Figure().update_layout(
            title="⚠️ 缺少必要字段",
            annotations=[dict(text="数据中缺少'一级分类名'或'商品采购成本'字段", 
                            showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)]
        )
    
    # 按一级分类统计商品成本
    category_cost = df.groupby('一级分类名').agg({
        '商品采购成本': 'sum',
        '商品名称': 'count'  # 统计商品数量
    }).reset_index()
    category_cost.columns = ['分类', '总成本', '商品数量']
    category_cost = category_cost.sort_values('总成本', ascending=False).head(10)
    
    # 创建双轴柱状图 - 优化版
    fig = go.Figure()
    
    # 主轴：成本（柱状图 - 渐变色效果）
    fig.add_trace(go.Bar(
        name='总成本',
        x=category_cost['分类'],
        y=category_cost['总成本'],
        yaxis='y',
        marker=dict(
            color=category_cost['总成本'],  # 使用数值映射颜色
            colorscale=[
                [0, '#4A90E2'],      # 浅蓝
                [0.5, '#2E5C8A'],    # 中蓝
                [1, '#1A3A5C']       # 深蓝
            ],
            showscale=False,
            line=dict(color='rgba(255,255,255,0.3)', width=1.5),
            # 添加圆角效果（通过调整bar的corner radius）
        ),
        text=category_cost['总成本'].apply(lambda x: f'¥{x/1000:.1f}k' if x >= 1000 else f'¥{x:.0f}'),
        textposition='outside',  # 改为外部显示，避免遮挡
        textfont=dict(color='#2c3e50', size=11, family='Arial'),
        hovertemplate='<b>%{x}</b><br>💰 总成本: ¥%{y:,.2f}<extra></extra>',
        width=0.65,
        opacity=0.9  # 添加透明度
    ))
    
    # 次轴：商品数量（折线图 - 优化样式）
    fig.add_trace(go.Scatter(
        name='商品数量',
        x=category_cost['分类'],
        y=category_cost['商品数量'],
        yaxis='y2',
        mode='lines+markers+text',
        marker=dict(
            color='#FF6B6B',
            size=12,
            symbol='circle',
            line=dict(color='white', width=3),
            gradient=dict(type='radial', color=['#FF6B6B', '#FF8E8E'])
        ),
        line=dict(color='#FF6B6B', width=4, shape='spline'),  # 平滑曲线
        text=category_cost['商品数量'],
        textposition='top center',
        textfont=dict(size=11, color='#FF6B6B', family='Arial', weight='bold'),
        hovertemplate='<b>%{x}</b><br>📦 商品数量: %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text='🏆 TOP 10 分类成本排行',
            font=dict(size=16, color='#1a1a1a', family='Arial, sans-serif', weight='bold'),
            x=0.5,
            xanchor='center',
            y=0.98,
            yanchor='top'
        ),
        xaxis=dict(
            title='',
            tickangle=-35,
            tickfont=dict(size=11, color='#2c3e50', family='Arial'),
            showline=True,
            linewidth=2,
            linecolor='rgba(0,0,0,0.1)',
            mirror=False
        ),
        yaxis=dict(
            title=dict(
                text='💰 总成本 (¥)',
                font=dict(size=12, color='#2E5C8A', family='Arial', weight='bold')
            ),
            side='left',
            tickfont=dict(size=10, color='#2c3e50'),
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(0,0,0,0.05)',
            zeroline=False
        ),
        yaxis2=dict(
            title=dict(
                text='📦 商品数量',
                font=dict(size=12, color='#FF6B6B', family='Arial', weight='bold')
            ),
            side='right',
            overlaying='y',
            tickfont=dict(size=10, color='#2c3e50'),
            showgrid=False
        ),
        height=380,  # 增加高度以容纳外部文本
        margin=dict(l=70, r=70, t=70, b=80),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.25,
            xanchor='center',
            x=0.5,
            font=dict(size=11, family='Arial'),
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        ),
        bargap=0.3,
        plot_bgcolor='rgba(248,250,252,0.8)',  # 更柔和的背景
        paper_bgcolor='white',
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='rgba(255,255,255,0.95)',
            font=dict(size=12, family='Arial'),
            bordercolor='rgba(0,0,0,0.1)'
        ),
        # 添加动画效果
        transition=dict(duration=500, easing='cubic-in-out')
    )
    
    # ✅ 使用统一包装函数，确保返回 dcc.Graph 而非裸 Figure
    
    return wrap_chart_component(fig, height='450px')


def create_marketing_activity_chart_echarts(order_agg):
    """创建商家活动补贴分析图表 - ECharts版本"""
    required_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券']
    
    # 检查必要字段
    missing_fields = [f for f in required_fields if f not in order_agg.columns]
    if missing_fields:
        return html.Div(f"⚠️ 缺少必要字段: {', '.join(missing_fields)}", className="text-center text-muted p-5")
    
    # 统计各类补贴
    subsidy_data = {
        '满减优惠': {
            '总金额': order_agg['满减金额'].sum(),
            '参与订单数': (order_agg['满减金额'] > 0).sum()
        },
        '商品折扣': {
            '总金额': order_agg['商品减免金额'].sum(),
            '参与订单数': (order_agg['商品减免金额'] > 0).sum()
        },
        '代金券': {
            '总金额': order_agg['商家代金券'].sum(),
            '参与订单数': (order_agg['商家代金券'] > 0).sum()
        },
        '商家承担券': {
            '总金额': order_agg['商家承担部分券'].sum(),
            '参与订单数': (order_agg['商家承担部分券'] > 0).sum()
        }
    }
    
    activities = list(subsidy_data.keys())
    amounts = [subsidy_data[k]['总金额'] for k in activities]
    orders = [subsidy_data[k]['参与订单数'] for k in activities]
    
    # 格式化数据
    formatted_amounts = [format_number(v) for v in amounts]
    formatted_orders = [format_number(v) for v in orders]
    
    # 预处理标签数据（用于显示）
    amount_labels = [f'¥{x/1000:.1f}k' if x >= 1000 else f'¥{x:.0f}' for x in amounts]
    
    # ECharts 配置
    option = {
        'title': dict(COMMON_TITLE, text='🎁 各类补贴活动力度与参与度'),
        'tooltip': dict(COMMON_TOOLTIP, axisPointer={'type': 'cross'}),
        'legend': dict(COMMON_LEGEND, data=['补贴总金额', '参与订单数']),
        'grid': dict(COMMON_GRID, bottom='12%'),
        'xAxis': {
            'type': 'category',
            'data': activities,
            'axisLabel': dict(COMMON_AXIS_LABEL, fontSize=12, interval=0),
            'axisLine': {'lineStyle': {'color': 'rgba(0,0,0,0.1)'}},
            'axisTick': {'show': False}
        },
        'yAxis': [
            {
                'type': 'value',
                'name': '💳 补贴金额 (¥)',
                'nameTextStyle': {'color': COMMON_COLORS['red'][2], 'fontSize': 12, 'fontWeight': 'bold'},
                'axisLabel': COMMON_AXIS_LABEL,
                'splitLine': COMMON_SPLIT_LINE
            },
            {
                'type': 'value',
                'name': '📋 参与订单数',
                'nameTextStyle': {'color': COMMON_COLORS['green'][0], 'fontSize': 12, 'fontWeight': 'bold'},
                'axisLabel': COMMON_AXIS_LABEL,
                'splitLine': {'show': False}
            }
        ],
        'series': [
            {
                'name': '补贴总金额',
                'type': 'bar',
                'data': [{'value': v, 'label': l} for v, l in zip(formatted_amounts, amount_labels)],
                'yAxisIndex': 0,
                'barWidth': '45%',
                'itemStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': COMMON_COLORS['red'][0]},
                            {'offset': 0.5, 'color': COMMON_COLORS['red'][2]},
                            {'offset': 1, 'color': COMMON_COLORS['red'][4]}
                        ]
                    },
                    'borderRadius': [8, 8, 0, 0],
                    'shadowColor': 'rgba(231,76,60,0.3)',
                    'shadowBlur': 10
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': '{@label}',
                    'fontSize': 11,
                    'fontWeight': 'bold',
                    'color': '#2c3e50'
                },
                'emphasis': {
                    'itemStyle': {
                        'shadowColor': 'rgba(231,76,60,0.6)',
                        'shadowBlur': 20,
                        'scale': True
                    }
                },
                'animationDelay': '{dataIndex} * 100'
            },
            {
                'name': '参与订单数',
                'type': 'line',
                'data': formatted_orders,
                'yAxisIndex': 1,
                'smooth': True,
                'symbol': 'diamond',
                'symbolSize': 12,
                'lineStyle': {'width': 4, 'color': COMMON_COLORS['green'][0]},
                'itemStyle': {
                    'color': COMMON_COLORS['green'][0],
                    'borderWidth': 3,
                    'borderColor': '#fff'
                },
                'areaStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': 'rgba(46,204,113,0.4)'},
                            {'offset': 1, 'color': 'rgba(46,204,113,0.05)'}
                        ]
                    }
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'fontSize': 11,
                    'fontWeight': 'bold',
                    'color': COMMON_COLORS['green'][0]
                },
                'emphasis': {
                    'scale': True,
                    'focus': 'series'
                }
            }
        ],
        **COMMON_ANIMATION
    }
    
    return DashECharts(
        option=option,
        id='marketing-activity-chart-echarts',
        style={'height': '420px', 'width': '100%'}
    )


def create_marketing_activity_chart(order_agg):
    """创建商家活动补贴分析图表 - 智能选择版本"""
    if ECHARTS_AVAILABLE:
        return create_marketing_activity_chart_echarts(order_agg)
    
    # Plotly 备份方案（保持原有代码）
    """创建商家活动补贴分析图表"""
    required_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券']
    
    # 检查必要字段
    missing_fields = [f for f in required_fields if f not in order_agg.columns]
    if missing_fields:
        return go.Figure().update_layout(
            title="⚠️ 缺少必要字段",
            annotations=[dict(text=f"数据中缺少字段: {', '.join(missing_fields)}", 
                            showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)]
        )
    
    # 统计各类补贴
    subsidy_data = {
        '满减优惠': {
            '总金额': order_agg['满减金额'].sum(),
            '参与订单数': (order_agg['满减金额'] > 0).sum()
        },
        '商品折扣': {
            '总金额': order_agg['商品减免金额'].sum(),
            '参与订单数': (order_agg['商品减免金额'] > 0).sum()
        },
        '代金券': {
            '总金额': order_agg['商家代金券'].sum(),
            '参与订单数': (order_agg['商家代金券'] > 0).sum()
        },
        '商家承担券': {
            '总金额': order_agg['商家承担部分券'].sum(),
            '参与订单数': (order_agg['商家承担部分券'] > 0).sum()
        }
    }
    
    # 构造数据
    activities = list(subsidy_data.keys())
    amounts = [subsidy_data[k]['总金额'] for k in activities]
    orders = [subsidy_data[k]['参与订单数'] for k in activities]
    
    # 创建双轴柱状图 - 优化版
    fig = go.Figure()
    
    # 主轴：补贴金额（柱状图 - 渐变红色）
    fig.add_trace(go.Bar(
        name='补贴总金额',
        x=activities,
        y=amounts,
        yaxis='y',
        marker=dict(
            color=amounts,  # 使用数值映射颜色
            colorscale=[
                [0, '#FF6B6B'],      # 浅红
                [0.5, '#E74C3C'],    # 中红
                [1, '#C0392B']       # 深红
            ],
            showscale=False,
            line=dict(color='rgba(255,255,255,0.4)', width=2),
        ),
        text=[f'¥{x/1000:.1f}k' if x >= 1000 else f'¥{x:.0f}' for x in amounts],
        textposition='outside',  # 改为外部显示
        textfont=dict(color='#2c3e50', size=11, family='Arial'),
        width=0.5,
        hovertemplate='<b>%{x}</b><br>💳 补贴金额: ¥%{y:,.2f}<extra></extra>',
        opacity=0.9
    ))
    
    # 次轴：参与订单数（折线图 - 优化样式）
    fig.add_trace(go.Scatter(
        name='参与订单数',
        x=activities,
        y=orders,
        yaxis='y2',
        mode='lines+markers+text',
        marker=dict(
            color='#2ECC71',
            size=14,
            symbol='diamond',
            line=dict(color='white', width=3)
        ),
        line=dict(color='#2ECC71', width=4, shape='spline'),  # 平滑曲线
        text=[f'{int(x)}' for x in orders],
        textposition='top center',
        textfont=dict(size=11, color='#2ECC71', family='Arial'),
        hovertemplate='<b>%{x}</b><br>📋 参与订单: %{y:,}单<extra></extra>',
        fill='tonexty',
        fillcolor='rgba(46,204,113,0.1)'  # 添加区域填充
    ))
    
    fig.update_layout(
        title=dict(
            text='🎁 各类补贴活动力度与参与度',
            font=dict(size=16, color='#1a1a1a', family='Arial, sans-serif', weight='bold'),
            x=0.5,
            xanchor='center',
            y=0.98,
            yanchor='top'
        ),
        xaxis=dict(
            title='',
            tickfont=dict(size=11, color='#2c3e50', family='Arial'),
            showline=True,
            linewidth=2,
            linecolor='rgba(0,0,0,0.1)',
            mirror=False
        ),
        yaxis=dict(
            title=dict(
                text='💳 补贴金额 (¥)',
                font=dict(size=12, color='#E74C3C', family='Arial', weight='bold')
            ),
            side='left',
            tickfont=dict(size=10, color='#2c3e50'),
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(0,0,0,0.05)',
            range=[0, max(amounts) * 1.2] if amounts else [0, 1000],
            zeroline=False
        ),
        yaxis2=dict(
            title=dict(
                text='📋 参与订单数',
                font=dict(size=12, color='#2ECC71', family='Arial', weight='bold')
            ),
            side='right',
            overlaying='y',
            tickfont=dict(size=10, color='#2c3e50'),
            showgrid=False,
            range=[0, max(orders) * 1.25] if orders else [0, 100]
        ),
        height=380,  # 增加高度
        margin=dict(l=70, r=70, t=70, b=80),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.22,
            xanchor='center',
            x=0.5,
            font=dict(size=11, family='Arial'),
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='rgba(0,0,0,0.1)',
            borderwidth=1
        ),
        bargap=0.4,  # 调整间距
        plot_bgcolor='rgba(248,250,252,0.8)',
        paper_bgcolor='white',
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='rgba(255,255,255,0.95)',
            font=dict(size=12, family='Arial'),
            bordercolor='rgba(0,0,0,0.1)'
        ),
        # 添加动画效果
        transition=dict(duration=500, easing='cubic-in-out')
    )
    
    # ✅ 使用统一包装函数，确保返回 dcc.Graph 而非裸 Figure
    
    return wrap_chart_component(fig, height='450px')


# ==================== 数值格式化工具函数 ====================

def format_number(value):
    """
    智能数值格式化：整数显示整数，有小数则保留一位
    
    Args:
        value: 数值
    
    Returns:
        格式化后的数值（整数或保留一位小数）
    """
    if value == int(value):
        return int(value)
    else:
        return round(value, 1)


# ==================== 更多 ECharts 图表函数 ====================

def calculate_daily_sales_with_channel(df, order_agg, selected_channel='all'):
    """
    按渠道筛选后计算日度销售数据(含利润率)
    
    Args:
        df: 原始数据DataFrame
        order_agg: 订单级聚合数据(来自calculate_order_metrics)
        selected_channel: 选中的渠道 ('all'表示全部渠道)
    
    Returns:
        daily_sales: 包含利润率的日度数据
        channel_available: 是否有渠道字段
    """
    # 检查是否有渠道字段
    channel_available = '渠道' in df.columns
    
    # 🔍 调试日志
    print(f"\n🔍 [calculate_daily_sales_with_channel] 调用")
    print(f"   selected_channel = '{selected_channel}'")
    print(f"   channel_available = {channel_available}")
    print(f"   df行数 = {len(df)}")
    print(f"   order_agg行数 = {len(order_agg)}")
    
    # 🔴 关键修复: 统一订单ID类型为字符串
    df = df.copy()  # 避免修改原始数据
    df['订单ID'] = df['订单ID'].astype(str)
    order_agg = order_agg.copy()
    order_agg['订单ID'] = order_agg['订单ID'].astype(str)
    
    # 提取日期信息(从原始数据)
    if '日期' in df.columns:
        # 🔍 检查order_agg中渠道分布(merge前)
        if channel_available and '渠道' in order_agg.columns:
            channel_dist_before = order_agg['渠道'].value_counts()
            print(f"   📊 [Merge前] order_agg渠道分布:")
            for ch, cnt in channel_dist_before.items():
                print(f"      {ch}: {cnt} 订单")
            print(f"   📊 [Merge前] order_agg总行数: {len(order_agg)}")
        
        # 只提取日期(渠道已经在order_agg中)
        date_map = df[['订单ID', '日期']].drop_duplicates('订单ID')
        date_map['日期'] = date_map['日期'].dt.date
        
        print(f"   📊 date_map行数: {len(date_map)}")
        print(f"   📊 date_map订单ID类型: {date_map['订单ID'].dtype}")
        print(f"   📊 order_agg订单ID类型: {order_agg['订单ID'].dtype}")
        
        # 合并到order_agg
        order_agg_with_info = order_agg.merge(date_map, on='订单ID', how='left')
        
        print(f"   📊 [Merge后] order_agg_with_info总行数: {len(order_agg_with_info)}")
        
        # 🔍 检查渠道分布(merge后)
        if channel_available and '渠道' in order_agg_with_info.columns:
            channel_dist = order_agg_with_info['渠道'].value_counts()
            print(f"   📊 [Merge后] 渠道分布:")
            for ch, cnt in channel_dist.items():
                print(f"      {ch}: {cnt} 订单")
        
        # 如果选择了特定渠道,进行筛选
        if selected_channel != 'all' and channel_available:
            # 🔍 筛选前统计
            before_filter = len(order_agg_with_info)
            
            # 🔍 检查精确匹配
            print(f"   🔍 筛选条件: 渠道 == '{selected_channel}'")
            print(f"   🔍 order_agg_with_info中'渠道'列的唯一值: {sorted(order_agg_with_info['渠道'].dropna().unique())}")
            
            order_agg_with_info = order_agg_with_info[
                order_agg_with_info['渠道'] == selected_channel
            ].copy()
            
            # 🔍 筛选后统计
            after_filter = len(order_agg_with_info)
            print(f"   渠道筛选: {before_filter} -> {after_filter} 订单 (渠道='{selected_channel}')")
            
            if after_filter == 0:
                print(f"   ⚠️ 警告: 筛选后没有数据!")
                # 显示df中实际有哪些渠道
                actual_channels_df = df['渠道'].dropna().unique()
                print(f"   df中实际渠道列表: {sorted(actual_channels_df)}")
                # 显示order_agg中有哪些渠道
                if '渠道' in order_agg.columns:
                    actual_channels_agg = order_agg['渠道'].dropna().unique()
                    print(f"   order_agg中渠道列表: {sorted(actual_channels_agg)}")
                # 显示合并信息
                print(f"   order_agg原始行数: {len(order_agg)}")
                print(f"   date_map行数: {len(date_map)}")
                print(f"   合并后行数: {before_filter}")
        
        # 按日期聚合
        agg_dict = {
            '订单实际利润': 'sum',
            '订单ID': 'nunique'
        }
        
        # 优先使用实收价格
        if '实收价格' in order_agg_with_info.columns:
            agg_dict['实收价格'] = 'sum'
        elif '预计订单收入' in order_agg_with_info.columns:
            agg_dict['预计订单收入'] = 'sum'
        else:
            agg_dict['实收价格'] = 'sum'
        
        daily_sales = order_agg_with_info.groupby('日期').agg(agg_dict).reset_index()
        
        # 重命名列
        col_mapping = {'订单ID': '订单数', '订单实际利润': '总利润'}
        if '实收价格' in daily_sales.columns:
            col_mapping['实收价格'] = '销售额'
        elif '预计订单收入' in daily_sales.columns:
            col_mapping['预计订单收入'] = '销售额'
        else:
            col_mapping['实收价格'] = '销售额'
        
        daily_sales.rename(columns=col_mapping, inplace=True)
        
        # 计算利润率
        daily_sales['利润率'] = (
            daily_sales['总利润'] / daily_sales['销售额'].replace(0, np.nan) * 100
        ).fillna(0).round(2)
        
        return daily_sales, channel_available
    else:
        # 如果没有日期字段,返回空DataFrame
        return pd.DataFrame(), channel_available


def analyze_channel_health_warnings(df, order_agg):
    """
    分析各渠道健康度,识别利润率异常渠道
    
    Args:
        df: 原始数据
        order_agg: 订单聚合数据(已包含渠道字段)
    
    Returns:
        warnings: 警示信息列表
    """
    warnings = []
    
    # 检查是否有渠道和日期字段
    if '渠道' not in order_agg.columns or '日期' not in df.columns:
        return warnings
    
    # 🔴 统一订单ID类型
    df = df.copy()
    df['订单ID'] = df['订单ID'].astype(str)
    order_agg = order_agg.copy()
    order_agg['订单ID'] = order_agg['订单ID'].astype(str)
    
    # 只提取日期信息(渠道已经在order_agg中)
    date_map = df[['订单ID', '日期']].drop_duplicates('订单ID')
    date_map['日期'] = date_map['日期'].dt.date
    
    # 合并到order_agg
    order_agg_with_info = order_agg.merge(date_map, on='订单ID', how='left')
    
    # 按渠道+日期聚合
    channel_daily = order_agg_with_info.groupby(['渠道', '日期']).agg({
        '实收价格': 'sum',
        '订单实际利润': 'sum'
    }).reset_index()
    
    # 计算每日利润率
    channel_daily['利润率'] = (
        channel_daily['订单实际利润'] / channel_daily['实收价格'].replace(0, np.nan) * 100
    ).fillna(0)
    
    # 按渠道分析
    for channel in channel_daily['渠道'].unique():
        channel_data = channel_daily[channel_daily['渠道'] == channel].sort_values('日期')
        
        if len(channel_data) < 3:
            continue  # 数据太少,无法分析
        
        # 计算利润率统计指标
        profit_rates = channel_data['利润率'].values
        mean_rate = np.mean(profit_rates)
        std_rate = np.std(profit_rates)
        
        # 获取最近3天数据
        recent_3_days = channel_data.tail(3)
        if len(recent_3_days) == 3:
            first_rate = recent_3_days.iloc[0]['利润率']
            last_rate = recent_3_days.iloc[-1]['利润率']
            
            # 计算近3天跌幅
            if first_rate > 0:
                decline_pct = ((last_rate - first_rate) / first_rate) * 100
            else:
                decline_pct = 0
            
            # 判断是否需要警示
            # 条件1: 利润率波动大 (标准差 > 10%)
            # 条件2: 近3天下跌超过10%
            issue_found = False
            warning_text = []
            severity = 'low'
            
            if std_rate > 10:
                issue_found = True
                warning_text.append(f"利润率波动大(σ={std_rate:.1f}%)")
                severity = 'medium'
            
            if decline_pct < -10:
                issue_found = True
                warning_text.append(f"近3天下跌{abs(decline_pct):.0f}%")
                severity = 'high'
            
            if issue_found:
                warnings.append({
                    'channel': channel,
                    'issue': ' | '.join(warning_text),
                    'mean_rate': mean_rate,
                    'std_rate': std_rate,
                    'recent_decline': decline_pct,
                    'severity': severity
                })
    
    # 按严重程度排序
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    warnings.sort(key=lambda x: severity_order[x['severity']])
    
    return warnings


def create_sales_trend_chart_echarts(daily_sales):
    """创建销售趋势分析图表 - ECharts版本 (支持利润率和异常标注)"""
    
    # 格式化数据
    formatted_sales = [format_number(v) for v in daily_sales['销售额'].tolist()]
    formatted_profit = [format_number(v) for v in daily_sales['总利润'].tolist()]
    formatted_orders = [format_number(v) for v in daily_sales['订单数'].tolist()]
    
    # 🆕 检查是否有利润率字段
    has_profit_rate = '利润率' in daily_sales.columns
    if has_profit_rate:
        formatted_profit_rate = [format_number(v) for v in daily_sales['利润率'].tolist()]
        profit_rates = daily_sales['利润率'].values
        
        # 🆕 识别异常点 (利润率 < 均值 - 1σ)
        mean_rate = np.mean(profit_rates)
        std_rate = np.std(profit_rates)
        anomaly_threshold = mean_rate - std_rate
        
        # 找出异常点的索引和数据
        anomaly_points = []
        for idx, (date, rate) in enumerate(zip(daily_sales['日期'].tolist(), profit_rates)):
            if rate < anomaly_threshold and rate > 0:  # 避免0值
                anomaly_points.append({
                    'coord': [idx, rate],
                    'value': f'{rate:.1f}%',
                    'itemStyle': {'color': '#e74c3c'}
                })
    
    # 计算订单数的范围,用于优化右Y轴显示
    order_min = daily_sales['订单数'].min()
    order_max = daily_sales['订单数'].max()
    
    # 处理 NaN 或空数据的情况
    if pd.isna(order_min) or pd.isna(order_max):
        order_axis_min = 0
        order_axis_max = 100
    else:
        # 给订单数轴留出20%的上下空间,让曲线更饱满
        order_range = order_max - order_min
        order_axis_min = max(0, order_min - order_range * 0.2)
        order_axis_max = order_max + order_range * 0.2
    
    # 🆕 构建图例数据 (动态添加利润率)
    legend_data = ['销售额', '总利润']
    if has_profit_rate:
        legend_data.append('利润率')
    legend_data.append('订单数')
    
    # 🆕 构建Y轴配置 (支持三Y轴)
    yAxis_config = [
        # Y轴1: 金额 (左侧)
        {
            'type': 'value',
            'name': '金额 (¥)',
            'position': 'left',
            'nameTextStyle': {'color': '#333', 'fontSize': 12, 'fontWeight': 'bold'},
            'axisLabel': COMMON_AXIS_LABEL,
            'splitLine': COMMON_SPLIT_LINE
        },
        # Y轴2: 利润率 (右侧) 🆕
        {
            'type': 'value',
            'name': '利润率 (%)',
            'position': 'right',
            'offset': 0,
            'min': 0,
            'max': 100,
            'nameTextStyle': {'color': COMMON_COLORS['orange'][0], 'fontSize': 12, 'fontWeight': 'bold'},
            'axisLabel': {
                'color': '#666',
                'fontSize': 11,
                'formatter': '{value}%'
            },
            'splitLine': {'show': False}
        },
        # Y轴3: 订单数 (右侧,偏移)
        {
            'type': 'value',
            'name': '订单数',
            'position': 'right',
            'offset': 80,  # 🆕 向右偏移,避免与利润率轴重叠
            'min': int(order_axis_min),
            'max': int(order_axis_max),
            'nameTextStyle': {'color': COMMON_COLORS['purple'][0], 'fontSize': 12, 'fontWeight': 'bold'},
            'axisLabel': COMMON_AXIS_LABEL,
            'splitLine': {'show': False}
        }
    ]
    
    # 🆕 构建系列数据
    series_config = [
        # 销售额曲线
        {
            'name': '销售额',
            'type': 'line',
            'data': formatted_sales,
            'yAxisIndex': 0,
            'smooth': True,
            'symbol': 'circle',
            'symbolSize': 8,
            'lineStyle': {'width': 3, 'color': COMMON_COLORS['blue'][0]},
            'itemStyle': {'color': COMMON_COLORS['blue'][0], 'borderWidth': 2, 'borderColor': '#fff'},
            'areaStyle': {
                'color': {
                    'type': 'linear',
                    'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                    'colorStops': [
                        {'offset': 0, 'color': f'rgba(74,144,226,0.3)'},
                        {'offset': 1, 'color': f'rgba(74,144,226,0.05)'}
                    ]
                }
            }
        },
        # 总利润曲线
        {
            'name': '总利润',
            'type': 'line',
            'data': formatted_profit,
            'yAxisIndex': 0,
            'smooth': True,
            'symbol': 'triangle',
            'symbolSize': 8,
            'lineStyle': {'width': 3, 'color': COMMON_COLORS['green'][0]},
            'itemStyle': {'color': COMMON_COLORS['green'][0], 'borderWidth': 2, 'borderColor': '#fff'}
        }
    ]
    
    # 🆕 添加利润率曲线 (如果有数据)
    if has_profit_rate:
        profit_rate_series = {
            'name': '利润率',
            'type': 'line',
            'data': formatted_profit_rate,
            'yAxisIndex': 1,  # 🆕 使用Y轴2
            'smooth': True,
            'symbol': 'circle',
            'symbolSize': 6,
            'lineStyle': {
                'width': 2.5,
                'color': COMMON_COLORS['orange'][0],
                'type': 'dashed'  # 🆕 虚线样式,区别于其他曲线
            },
            'itemStyle': {'color': COMMON_COLORS['orange'][0], 'borderWidth': 2, 'borderColor': '#fff'}
        }
        
        # 🆕 添加异常点标注
        if anomaly_points:
            profit_rate_series['markPoint'] = {
                'data': anomaly_points,
                'symbol': 'pin',
                'symbolSize': 50,
                'label': {
                    'show': True,
                    'formatter': '{c}',
                    'fontSize': 10,
                    'color': '#fff'
                }
            }
        
        series_config.append(profit_rate_series)
    
    # 订单数曲线
    series_config.append({
        'name': '订单数',
        'type': 'line',
        'data': formatted_orders,
        'yAxisIndex': 2,  # 🆕 使用Y轴3
        'smooth': True,
        'symbol': 'diamond',
        'symbolSize': 8,
        'lineStyle': {'width': 3, 'color': COMMON_COLORS['purple'][0]},
        'itemStyle': {'color': COMMON_COLORS['purple'][0], 'borderWidth': 2, 'borderColor': '#fff'}
    })
    
    option = {
        'title': dict(COMMON_TITLE, text='📈 销售趋势分析 (含利润率) [优化版✨]'),
        'tooltip': dict(COMMON_TOOLTIP, axisPointer={'type': 'cross'}),
        'legend': dict(COMMON_LEGEND, data=legend_data, top='8%'),
        'grid': dict(COMMON_GRID, right='15%'),  # 🆕 右侧留更多空间给第三Y轴
        'xAxis': {
            'type': 'category',
            'data': [str(d) for d in daily_sales['日期'].tolist()],
            'axisLabel': dict(COMMON_AXIS_LABEL, rotate=30)
        },
        'yAxis': yAxis_config,
        'series': series_config,
        **COMMON_ANIMATION
    }
    
    return DashECharts(
        option=option,
        id='sales-trend-chart-echarts',  # 🆕 添加ID,用于callback更新
        style={'height': '450px', 'width': '100%'}  # 🆕 稍微增加高度
    )


def analyze_daily_anomalies(df, daily_sales):
    """智能异常分析：识别销售趋势中的异常点并深度分析原因"""
    
    # 计算利润率
    daily_sales['利润率'] = (daily_sales['总利润'] / daily_sales['销售额'] * 100).round(2)
    daily_sales['单均销售额'] = (daily_sales['销售额'] / daily_sales['订单数']).round(2)
    daily_sales['单均利润'] = (daily_sales['总利润'] / daily_sales['订单数']).round(2)
    
    # 计算历史平均值（用于异常检测）
    avg_profit_rate = daily_sales['利润率'].mean()
    std_profit_rate = daily_sales['利润率'].std()
    
    # 识别异常点：利润率低于平均值-1个标准差
    daily_sales['异常标记'] = daily_sales['利润率'] < (avg_profit_rate - std_profit_rate)
    
    # 找出最佳日和最差日（添加空值检查）
    if len(daily_sales) > 0 and not daily_sales['利润率'].isna().all():
        best_day = daily_sales.loc[daily_sales['利润率'].idxmax()]
        worst_day = daily_sales.loc[daily_sales['利润率'].idxmin()]
    else:
        # 如果数据为空，创建默认值
        best_day = worst_day = pd.Series({
            '日期': pd.Timestamp.now().date(),
            '订单数': 0,
            '销售额': 0,
            '成本': 0,
            '利润': 0,
            '利润率': 0
        })
    
    # 识别所有异常日期
    anomaly_days = daily_sales[daily_sales['异常标记']].copy()
    
    # 分析每个异常日期的详细原因
    anomaly_details = []
    
    for idx, day_data in anomaly_days.iterrows():
        date = day_data['日期']
        
        # 获取该日期的订单数据
        day_df = df[df['日期'].dt.date == date].copy()
        
        # 按订单聚合
        agg_dict = {
            '利润额': 'sum',
            '物流配送费': 'first',
            '配送平台': 'first',
            '用户支付配送费': 'first',
            '配送费减免金额': 'first',
            '平台佣金': 'first',
            '平台服务费': 'first',
            '满减金额': 'first',
            '商品减免金额': 'first',
            '商家代金券': 'first',
            '商家承担部分券': 'first',
            '实收价格': 'sum'
        }
        
        # ✅ 动态添加新字段
        if '新客减免金额' in day_df.columns:
            agg_dict['新客减免金额'] = 'first'
        if '企客后返' in day_df.columns:
            agg_dict['企客后返'] = 'sum'
        
        day_orders = day_df.groupby('订单ID').agg(agg_dict).reset_index()

        if '平台服务费' not in day_orders.columns:
            day_orders['平台服务费'] = day_orders.get('平台佣金', 0)
        if '企客后返' not in day_orders.columns:
            day_orders['企客后返'] = 0
        
        # 计算成本结构
        day_orders['活动成本'] = (
            day_orders['满减金额'] + 
            day_orders['商品减免金额'] + 
            day_orders['商家代金券'] + 
            day_orders['商家承担部分券']
        )
        
        # ✅ 使用全局统一的利润计算公式
        day_orders['订单实际利润'] = _calculate_profit_formula(day_orders)
        
        # 成本占比分析 - 使用实收价格作为分母
        total_sales = day_orders['实收价格'].sum()
        
        # ✅ 配送成本 = 物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返
        total_delivery = (
            day_orders['物流配送费'] -
            (day_orders['用户支付配送费'] - day_orders['配送费减免金额']) -
            day_orders['企客后返']
        ).sum()
        platform_fee_col = '平台服务费' if '平台服务费' in day_orders.columns else '平台佣金'
        total_commission = day_orders[platform_fee_col].sum()
        total_activity = day_orders['活动成本'].sum()
        
        delivery_rate = (total_delivery / total_sales * 100) if total_sales > 0 else 0
        commission_rate = (total_commission / total_sales * 100) if total_sales > 0 else 0
        activity_rate = (total_activity / total_sales * 100) if total_sales > 0 else 0
        
        # 商品级别分析：找出拉低利润的商品
        product_agg_dict = {
            '利润额': 'sum',
            '月售': 'sum',
            '实收价格': 'sum'
        }
        
        product_analysis = day_df.groupby('商品名称').agg(product_agg_dict).reset_index()
        
        # 计算商品利润率
        product_analysis['商品利润率'] = (
            product_analysis['利润额'] / product_analysis['实收价格'] * 100
        ).round(2)
        product_analysis = product_analysis.sort_values('实收价格', ascending=False)
        
        # 找出销售额Top5但利润率低的商品
        top_products = product_analysis.head(5)
        low_margin_products = top_products[top_products['商品利润率'] < avg_profit_rate]
        
        # 统一使用实收价格
        problem_products_cols = ['商品名称', '商品利润率', '实收价格']
        
        anomaly_details.append({
            '日期': str(date),
            '销售额': day_data['销售额'],
            '总利润': day_data['总利润'],
            '利润率': day_data['利润率'],
            '订单数': day_data['订单数'],
            '配送成本率': delivery_rate,
            '佣金率': commission_rate,
            '活动成本率': activity_rate,
            '问题商品数': len(low_margin_products),
            '问题商品': low_margin_products[problem_products_cols].to_dict('records') if len(low_margin_products) > 0 else []
        })
    
    return {
        'summary': {
            '平均利润率': avg_profit_rate,
            '利润率标准差': std_profit_rate,
            '异常天数': len(anomaly_days),
            '总天数': len(daily_sales)
        },
        'best_day': {
            '日期': str(best_day['日期']),
            '销售额': best_day['销售额'],
            '利润率': best_day['利润率'],
            '订单数': best_day['订单数']
        },
        'worst_day': {
            '日期': str(worst_day['日期']),
            '销售额': worst_day['销售额'],
            '利润率': worst_day['利润率'],
            '订单数': worst_day['订单数']
        },
        'anomaly_details': anomaly_details
    }


def create_category_pie_chart_echarts(category_sales):
    """创建分类销售占比饼图 - ECharts版本"""
    
    # 格式化数据
    formatted_data = [
        {'name': k, 'value': format_number(v)} 
        for k, v in zip(category_sales.index, category_sales.values)
    ]
    
    option = {
        'title': dict(COMMON_TITLE, text='🏷️ 商品分类销售占比 [统一配置✅]'),
        'tooltip': dict(COMMON_TOOLTIP, trigger='item', formatter='{b}: ¥{c} ({d}%)'),
        'legend': dict(COMMON_LEGEND, orient='vertical', left='5%', top='15%'),
        'series': [
            {
                'name': '销售额',
                'type': 'pie',
                'radius': ['40%', '70%'],
                'center': ['60%', '55%'],
                'data': formatted_data,
                'itemStyle': {
                    'borderRadius': 10,
                    'borderColor': '#fff',
                    'borderWidth': 2
                },
                'label': {
                    'show': True,
                    'formatter': '{b}\n{d}%',
                    'fontSize': 11,
                    'fontWeight': 'bold'
                },
                'emphasis': {
                    'itemStyle': {
                        'shadowBlur': 20,
                        'shadowOffsetX': 0,
                        'shadowColor': 'rgba(0, 0, 0, 0.5)'
                    },
                    'label': {
                        'show': True,
                        'fontSize': 14,
                        'fontWeight': 'bold'
                    }
                },
                'animationType': 'scale',
                'animationEasing': COMMON_ANIMATION['animationEasing'],
                'animationDelay': '{dataIndex} * 80'
            }
        ]
    }
    
    return DashECharts(
        option=option,
        style={'height': '400px', 'width': '100%'}
    )


# ==================== Tab7 营销分析专用ECharts图表 ====================

def create_scientific_quadrant_pie_echarts(scientific_data):
    """创建科学方法8象限分布环形图 - ECharts版本"""
    if not scientific_data or len(scientific_data) == 0:
        return html.Div("⚠️ 暂无数据", className="text-center text-muted p-5")
    
    df = pd.DataFrame(scientific_data)
    
    # 统计各象限商品数量
    if '象限名称' not in df.columns:
        return html.Div("⚠️ 数据缺少象限名称字段", className="text-center text-muted p-5")
    
    quadrant_count = df['象限名称'].value_counts().to_dict()
    
    # 象限颜色映射（8个象限 - 匹配科学八象限分析器的输出）
    quadrant_colors = {
        '🌟 明星商品': '#52c41a',        # 绿色 - 高营销+高利润+高动销
        '💰 高利润商品': '#73d13d',      # 浅绿 - 高营销+高利润+低动销
        '📈 高频低利': '#40a9ff',        # 浅蓝 - 高营销+低利润+高动销
        '⚠️ 营销低效': '#faad14',       # 橙色 - 高营销+低利润+低动销
        '💎 潜力商品': '#1890ff',        # 蓝色 - 低营销+高利润+高动销
        '🔍 利润潜力': '#13c2c2',        # 青色 - 低营销+高利润+低动销
        '⏰ 待优化': '#ffc53d',          # 浅橙 - 低营销+低利润+高动销
        '❌ 淘汰候选': '#ff4d4f'         # 红色 - 低营销+低利润+低动销
    }
    
    # 格式化数据
    formatted_data = [
        {
            'name': name,
            'value': count,
            'itemStyle': {'color': quadrant_colors.get(name, '#8c8c8c')}
        }
        for name, count in quadrant_count.items()
    ]
    
    option = {
        'title': dict(COMMON_TITLE, text='📊 象限分布分析', left='center'),
        'tooltip': dict(COMMON_TOOLTIP, 
                       trigger='item', 
                       formatter='{b}: {c}个商品 ({d}%)'),
        'legend': dict(COMMON_LEGEND, 
                      orient='vertical', 
                      left='5%', 
                      top='15%',
                      textStyle={'fontSize': 11}),
        'series': [
            {
                'name': '象限分布',
                'type': 'pie',
                'radius': ['45%', '75%'],  # 环形图
                'center': ['58%', '55%'],
                'data': formatted_data,
                'itemStyle': {
                    'borderRadius': 8,
                    'borderColor': '#fff',
                    'borderWidth': 2
                },
                'label': {
                    'show': True,
                    'formatter': '{b}\n{c}个\n({d}%)',
                    'fontSize': 10,
                    'fontWeight': 'bold'
                },
                'emphasis': {
                    'itemStyle': {
                        'shadowBlur': 15,
                        'shadowOffsetX': 0,
                        'shadowColor': 'rgba(0, 0, 0, 0.4)'
                    },
                    'label': {
                        'show': True,
                        'fontSize': 12,
                        'fontWeight': 'bold'
                    }
                },
                'animationType': 'scale',
                'animationEasing': COMMON_ANIMATION['animationEasing']
            }
        ]
    }
    
    return DashECharts(
        option=option,
        style={'height': '400px', 'width': '100%'}
    )


def create_scientific_confidence_bar_echarts(scientific_data):
    """创建科学方法置信度分布柱状图 - ECharts版本"""
    if not scientific_data or len(scientific_data) == 0:
        return html.Div("⚠️ 暂无数据", className="text-center text-muted p-5")
    
    df = pd.DataFrame(scientific_data)
    
    # 🔍 调试：打印数据信息
    print(f"\n🔍 [置信度分布图] 数据量: {len(df)}条")
    print(f"🔍 [置信度分布图] 字段: {df.columns.tolist()}")
    if '分类置信度' in df.columns:
        print(f"🔍 [置信度分布图] 分类置信度范围: {df['分类置信度'].min():.3f} - {df['分类置信度'].max():.3f}")
        print(f"🔍 [置信度分布图] 前5条分类置信度: {df['分类置信度'].head().tolist()}")
    
    # 统计各置信度级别商品数量
    if '分类置信度' not in df.columns:
        return html.Div("⚠️ 数据缺少分类置信度字段", className="text-center text-muted p-5")
    
    # 定义置信度级别（分类置信度是0-1之间的小数）
    def get_confidence_level(confidence):
        if confidence >= 0.7:
            return '高置信度'
        elif confidence >= 0.4:
            return '中置信度'
        else:
            return '低置信度'
    
    df['置信度级别'] = df['分类置信度'].apply(get_confidence_level)
    confidence_count = df['置信度级别'].value_counts()
    
    # 🔍 调试：打印统计结果
    print(f"🔍 [置信度分布图] 统计结果:")
    for level in ['高置信度', '中置信度', '低置信度']:
        count = confidence_count.get(level, 0)
        print(f"  {level}: {count}个")
    
    # 确保三个级别都存在（即使为0）
    levels = ['高置信度', '中置信度', '低置信度']
    counts = [int(confidence_count.get(level, 0)) for level in levels]  # 转换为Python原生int
    colors = ['#52c41a', '#faad14', '#ff4d4f']  # 绿、橙、红
    
    # 🔍 调试：打印最终数据
    print(f"🔍 [置信度分布图] 最终counts数组: {counts}")
    print(f"🔍 [置信度分布图] counts类型: {[type(c).__name__ for c in counts]}")
    print(f"🔍 [置信度分布图] Y轴最大值: {max(counts) * 1.2 if max(counts) > 0 else 10}")
    
    option = {
        'title': dict(COMMON_TITLE, text='📈 置信度分布分析', left='center'),
        'tooltip': dict(COMMON_TOOLTIP, 
                       trigger='axis',
                       axisPointer={'type': 'shadow'},
                       formatter='{b}: {c}个商品'),
        'grid': {
            'left': '5%',
            'right': '5%',
            'top': '20%',
            'bottom': '10%',
            'containLabel': True
        },
        'xAxis': {
            'type': 'category',
            'data': levels,
            'axisLabel': dict(COMMON_AXIS_LABEL, fontSize=12, fontWeight='bold'),
            'axisLine': {'lineStyle': {'color': 'rgba(0,0,0,0.1)'}},
            'axisTick': {'show': False}
        },
        'yAxis': {
            'type': 'value',
            'name': '商品数量',
            'nameTextStyle': {'fontSize': 12, 'fontWeight': 'bold'},
            'axisLabel': COMMON_AXIS_LABEL,
            'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}}
        },
        'series': [
            {
                'name': '商品数量',
                'type': 'bar',
                'data': [
                    {'value': counts[0], 'itemStyle': {'color': colors[0], 'borderRadius': [8, 8, 0, 0]}},
                    {'value': counts[1], 'itemStyle': {'color': colors[1], 'borderRadius': [8, 8, 0, 0]}},
                    {'value': counts[2], 'itemStyle': {'color': colors[2], 'borderRadius': [8, 8, 0, 0]}}
                ],
                'barWidth': '50%',
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': '{c}个',
                    'fontSize': 12,
                    'fontWeight': 'bold'
                },
                'emphasis': {
                    'itemStyle': {
                        'shadowBlur': 10,
                        'shadowColor': 'rgba(0, 0, 0, 0.3)'
                    }
                }
            }
        ]
    }
    
    return DashECharts(
        option=option,
        style={'height': '350px', 'width': '100%'}
    )


def create_scoring_distribution_bar_echarts(scoring_data):
    """创建评分模型评分分布直方图 - ECharts版本"""
    if not scoring_data or len(scoring_data) == 0:
        return html.Div("⚠️ 暂无数据", className="text-center text-muted p-5")
    
    df = pd.DataFrame(scoring_data)
    
    # 🔍 调试：打印数据信息
    print(f"\n🔍 [评分分布图] 数据量: {len(df)}条")
    print(f"🔍 [评分分布图] 字段: {df.columns.tolist()}")
    if '综合得分' in df.columns:
        print(f"🔍 [评分分布图] 得分范围: {df['综合得分'].min():.2f} - {df['综合得分'].max():.2f}")
        print(f"🔍 [评分分布图] 前5条得分: {df['综合得分'].head().tolist()}")
    
    # 统计各分数段商品数量
    if '综合得分' not in df.columns:
        return html.Div("⚠️ 数据缺少综合得分字段", className="text-center text-muted p-5")
    
    # 定义分数段
    bins = [0, 20, 40, 60, 80, 100]
    labels = ['0-20分', '20-40分', '40-60分', '60-80分', '80-100分']
    df['分数段'] = pd.cut(df['综合得分'], bins=bins, labels=labels, include_lowest=True)
    
    score_count = df['分数段'].value_counts().reindex(labels, fill_value=0)
    
    # 🔍 调试：打印统计结果
    print(f"🔍 [评分分布图] 统计结果:")
    for label in labels:
        count = score_count[label]
        print(f"  {label}: {count}个")
    
    # ⚠️ 数据质量检查
    total_count = len(df)
    low_score_count = score_count['0-20分'] + score_count['20-40分']
    if low_score_count / total_count > 0.8:
        print(f"⚠️ [评分分布图] 警告: {low_score_count}/{total_count} ({low_score_count/total_count*100:.1f}%) 商品得分低于40分")
        print(f"   可能原因: 营销ROI低、毛利率低、售罄率低或销量低")
        print(f"   建议检查: 营销成本是否过高、商品定价是否合理、库存是否积压")
    
    # 渐变色（从红到绿）
    colors = ['#ff4d4f', '#ff7a45', '#faad14', '#73d13d', '#52c41a']
    
    option = {
        'title': dict(COMMON_TITLE, text='📊 评分分布分析', left='center'),
        'tooltip': dict(COMMON_TOOLTIP, 
                       trigger='axis',
                       axisPointer={'type': 'shadow'},
                       formatter='{b}: {c}个商品'),
        'grid': {
            'left': '5%',
            'right': '5%',
            'top': '20%',
            'bottom': '15%',
            'containLabel': True
        },
        'xAxis': {
            'type': 'category',
            'data': labels,
            'axisLabel': dict(COMMON_AXIS_LABEL, fontSize=11, rotate=20),
            'axisLine': {'lineStyle': {'color': 'rgba(0,0,0,0.1)'}},
            'axisTick': {'show': False}
        },
        'yAxis': {
            'type': 'value',
            'name': '商品数量',
            'nameTextStyle': {'fontSize': 12, 'fontWeight': 'bold'},
            'axisLabel': COMMON_AXIS_LABEL,
            'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}}
        },
        'series': [
            {
                'name': '商品数量',
                'type': 'bar',
                'data': [
                    {'value': int(score_count[labels[0]]), 'itemStyle': {'color': colors[0], 'borderRadius': [6, 6, 0, 0]}},
                    {'value': int(score_count[labels[1]]), 'itemStyle': {'color': colors[1], 'borderRadius': [6, 6, 0, 0]}},
                    {'value': int(score_count[labels[2]]), 'itemStyle': {'color': colors[2], 'borderRadius': [6, 6, 0, 0]}},
                    {'value': int(score_count[labels[3]]), 'itemStyle': {'color': colors[3], 'borderRadius': [6, 6, 0, 0]}},
                    {'value': int(score_count[labels[4]]), 'itemStyle': {'color': colors[4], 'borderRadius': [6, 6, 0, 0]}}
                ],
                'barWidth': '60%',
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': '{c}个',
                    'fontSize': 11,
                    'fontWeight': 'bold'
                },
                'emphasis': {
                    'itemStyle': {
                        'shadowBlur': 10,
                        'shadowColor': 'rgba(0, 0, 0, 0.3)'
                    }
                }
            }
        ]
    }
    
    return DashECharts(
        option=option,
        style={'height': '350px', 'width': '100%'}
    )


def create_category_trend_chart_echarts(df, order_agg, selected_channel='all'):
    """创建一级分类销售趋势组合图表 - ECharts版本 (增强版)
    
    功能说明:
    - 柱状图: 显示TOP20分类的销售额
    - 折线图1: 显示利润额趋势(左Y轴,绿色,单位:元)
    - 折线图2: 显示利润率(%)趋势(右Y轴,橙色)
    - 预警标记: 售罄品⚠️、滞销品🐌
    - 数据表格: 包含所有指标的详细明细
    - 智能检测: 自动检测数据字段,缺少关键字段时显示友好提示
    - 🆕 渠道筛选: 支持按渠道筛选数据
    
    参数:
    - df: 原始数据DataFrame (需包含:商品名称、一级分类名、库存、日期等)
    - order_agg: 订单聚合数据 (需包含:订单实际利润)
    - selected_channel: 选中的渠道 ('all'表示全部渠道)
    
    返回:
    - html.Div 包含图表和数据表格
    """
    
    # ==================== 0. 字段检查 ====================
    required_fields = {
        '一级分类名': False,
        '日期': False,
        '库存': False,
        '月售': False
    }
    
    for field in required_fields.keys():
        if field in df.columns:
            required_fields[field] = True
        elif field == '日期' and '下单时间' in df.columns:
            required_fields[field] = True
        elif field == '库存' and '剩余库存' in df.columns:
            # 兼容不同的库存字段名
            required_fields[field] = True
    
    # 如果缺少一级分类名,无法生成分类分析
    if not required_fields['一级分类名']:
        return html.Div([
            dbc.Alert([
                html.H5("⚠️ 数据字段不足", className="alert-heading"),
                html.P("当前数据缺少【一级分类名】字段,无法进行分类销售分析。"),
                html.Hr(),
                html.P("请上传包含完整订单数据的Excel文件,需包含以下字段:", className="mb-1"),
                html.Ul([
                    html.Li("一级分类名 (必需)"),
                    html.Li("日期 或 下单时间 (必需)"),
                    html.Li("商品实售价 (必需)"),
                    html.Li("库存 (可选,用于计算库存周转和滞销品)"),
                    html.Li("月售 (可选,用于计算滞销品)")
                ])
            ], color="warning")
        ])
    
    # ==================== 1. 准备订单级数据并添加分类信息 ====================
    # 🔧 修复：从原始df按订单ID聚合，确保每个订单的分类、销售额、利润正确关联
    # 先获取每个订单的一级分类（一个订单可能有多个商品，取第一个分类）
    order_category_map = df.groupby('订单ID')['一级分类名'].first().reset_index()
    order_category_map.columns = ['订单ID', '一级分类名']
    
    # 将分类信息合并到订单聚合数据
    order_agg_with_category = order_agg.merge(order_category_map, on='订单ID', how='left')
    
    # 🔍 调试：查看order_agg中的关键字段
    print(f"\n🔍 [一级分类] order_agg可用字段: {order_agg.columns.tolist()}")
    print(f"🔍 [一级分类] order_agg样本数据 (前3行):")
    sample_cols = ['订单ID', '订单实际利润']
    if '实收价格' in order_agg.columns:
        sample_cols.append('实收价格')
    if '订单总收入' in order_agg.columns:
        sample_cols.append('订单总收入')
    if '预计订单收入' in order_agg.columns:
        sample_cols.append('预计订单收入')
    print(order_agg[sample_cols].head(3).to_string())
    
    # 🆕 渠道筛选逻辑
    channel_available = '渠道' in order_agg_with_category.columns
    if selected_channel != 'all' and channel_available:
        before_filter = len(order_agg_with_category)
        order_agg_with_category = order_agg_with_category[
            order_agg_with_category['渠道'] == selected_channel
        ].copy()
        after_filter = len(order_agg_with_category)
        print(f"\n🔍 [一级分类-渠道筛选] 渠道='{selected_channel}': {before_filter} -> {after_filter} 订单")
        
        # 如果筛选后没有数据,返回提示
        if after_filter == 0:
            available_channels = sorted(order_agg['渠道'].dropna().unique()) if '渠道' in order_agg.columns else []
            msg = f"⚠️ 渠道 '{selected_channel}' 暂无分类数据"
            if available_channels:
                msg += f"\n\n可用渠道: {', '.join(available_channels)}"
            return html.Div([
                dbc.Alert(msg, color="info", style={'whiteSpace': 'pre-wrap'})
            ])
    elif selected_channel != 'all':
        print(f"\n⚠️ [一级分类-渠道筛选] 数据中没有'渠道'字段,无法筛选")
    
    # ==================== 2. 按分类聚合统计 ====================
    # 🔧 使用订单级数据按分类聚合，确保不重复计算
    agg_dict = {
        '订单ID': 'count',           # 订单数
        '订单实际利润': 'sum'        # ✅ 总利润 (已扣除所有成本)
    }
    
    # ✅ 销售额字段选择（按优先级）
    if '实收价格' in order_agg_with_category.columns:
        sales_field = '实收价格'
        agg_dict['实收价格'] = 'sum'
    elif '订单总收入' in order_agg_with_category.columns:
        sales_field = '订单总收入'
        agg_dict['订单总收入'] = 'sum'
    elif '预计订单收入' in order_agg_with_category.columns:
        sales_field = '预计订单收入'
        agg_dict['预计订单收入'] = 'sum'
    else:
        # 如果都没有，从df按订单聚合实收价格
        # ⚠️ 关键修复：实收价格是单价，需要先乘以销量再聚合
        sales_field = '实收价格'
        sales_col = '月售' if '月售' in df.columns else '销量'
        if sales_col in df.columns:
            df_temp = df.copy()
            df_temp['订单总收入'] = df_temp['实收价格'] * df_temp[sales_col]
            order_sales = df_temp.groupby('订单ID')['订单总收入'].sum().reset_index()
            order_sales.columns = ['订单ID', '实收价格']
            print(f"🔧 [一级分类聚合] 实收价格修复: 使用(实收价格×{sales_col})聚合")
        else:
            order_sales = df.groupby('订单ID')['实收价格'].sum().reset_index()
            print(f"⚠️ [一级分类聚合] 实收价格兜底: 直接sum（缺少销量字段）")
        order_agg_with_category = order_agg_with_category.merge(order_sales, on='订单ID', how='left')
        agg_dict['实收价格'] = 'sum'
    
    # 按分类聚合
    category_stats = order_agg_with_category.groupby('一级分类名').agg(agg_dict).reset_index()
    
    # 🔍 调试：查看聚合后的数据
    print(f"\n🔍 [一级分类聚合] 聚合后数据 (前5行):")
    print(f"   列名: {category_stats.columns.tolist()}")
    if len(category_stats) > 0:
        print(category_stats.head().to_string())
    
    # ✅ 重命名列 - 使用rename而不是直接赋值列名,避免列顺序错位
    col_mapping = {
        '订单ID': '订单数',
        '订单实际利润': '利润额',  # 改为利润额，更清晰
        sales_field: '销售额',
        '一级分类名': '分类'
    }
    category_stats.rename(columns=col_mapping, inplace=True)
    
    # 🔍 调试：查看重命名后的数据
    print(f"\n🔍 [一级分类聚合] 重命名后数据 (前5行):")
    print(f"   列名: {category_stats.columns.tolist()}")
    if len(category_stats) > 0:
        print(category_stats.head().to_string())
    
    # 🔧 修复：利润率计算 = 利润额 / 销售额 * 100
    category_stats['利润率'] = (category_stats['利润额'] / category_stats['销售额'].replace(0, np.nan) * 100).fillna(0).round(2)
    
    # 🔍 调试：查看利润率计算结果
    print(f"\n🔍 [一级分类聚合] 利润率计算 (前5行):")
    if len(category_stats) > 0:
        print(category_stats[['分类', '销售额', '利润额', '利润率']].head().to_string())
    
    # ==================== 3. 获取数据最后日期和商品最新库存状态 ====================
    if required_fields['日期']:
        last_date = df['日期'].max() if '日期' in df.columns else df['下单时间'].max()
    else:
        # 如果没有日期字段,设为当前日期
        last_date = pd.Timestamp.now()
    
    # 统一库存字段名（兼容'库存'和'剩余库存'）
    stock_col = '库存' if '库存' in df.columns else '剩余库存' if '剩余库存' in df.columns else None
    
    # ==================== 4. 获取商品最新库存状态 (🔴 双重判断逻辑) ====================
    if stock_col:
        # 步骤1: 获取源数据的最后一天
        max_date = df['日期'].max() if '日期' in df.columns else df['下单时间'].max()
        
        # 步骤2: 获取每个商品在最后一天的库存(如果存在)
        last_day_data = df[df['日期'] == max_date] if '日期' in df.columns else df[df['下单时间'] == max_date]
        if len(last_day_data) > 0:
            last_day_stock_map = last_day_data.groupby('商品名称')[stock_col].last().to_dict()
        else:
            last_day_stock_map = {}
        
        # 步骤3: 获取每个商品最后一次售卖记录的库存
        last_sale_stock = df.sort_values('日期' if '日期' in df.columns else '下单时间').groupby('商品名称').agg({
            stock_col: 'last',
            '日期' if '日期' in df.columns else '下单时间': 'last'
        })
        
        # 步骤4: 双重判断,优先使用最后一天的库存
        def get_final_stock(product_name):
            # 优先使用最后一天的库存
            if product_name in last_day_stock_map:
                return last_day_stock_map[product_name]
            # 否则使用最后售卖时的库存
            elif product_name in last_sale_stock.index:
                return last_sale_stock.loc[product_name, stock_col]
            else:
                return 0
        
        # 构建最终库存DataFrame
        all_products = df['商品名称'].unique()
        last_stock = pd.DataFrame({
            '商品名称': all_products,
            stock_col: [get_final_stock(p) for p in all_products]
        })
        
        # 添加分类信息
        product_category_map = df.groupby('商品名称')['一级分类名'].first().to_dict()
        last_stock['一级分类名'] = last_stock['商品名称'].map(product_category_map)
    else:
        # 如果没有库存字段,创建空DataFrame
        last_stock = pd.DataFrame(columns=['商品名称', '一级分类名'])
    
    # ==================== 5. 售罄品统计 (库存=0且近7天有销量) ====================
    # 只有当同时有日期和库存字段时才计算
    if required_fields['日期'] and required_fields['库存'] and stock_col:
        # 计算7天前的日期
        seven_days_ago = last_date - timedelta(days=7)
        
        # 筛选近7天有销量的数据
        recent_sales = df[df['日期'] >= seven_days_ago] if '日期' in df.columns else df[df['下单时间'] >= seven_days_ago]
        
        # 获取近7天有销量的商品
        recent_products = set(recent_sales['商品名称'].unique())
        
        # 获取当前库存=0的商品（使用统一的库存字段名）
        zero_stock_products = set(last_stock[last_stock[stock_col] == 0]['商品名称'].unique())
        
        # 售罄品 = 库存0 且 近7天有销量
        sellout_products = zero_stock_products & recent_products
        
        # 按分类统计售罄品数量
        if len(sellout_products) > 0:
            sellout_df = df[df['商品名称'].isin(sellout_products)][['一级分类名', '商品名称']].drop_duplicates()
            sellout_count = sellout_df.groupby('一级分类名').size().reset_index()
            sellout_count.columns = ['分类', '售罄品数']
            category_stats = category_stats.merge(sellout_count, on='分类', how='left')
        else:
            category_stats['售罄品数'] = 0
    else:
        # 缺少必需字段,无法计算售罄品
        category_stats['售罄品数'] = 0
    
    category_stats['售罄品数'] = category_stats['售罄品数'].fillna(0).astype(int)
    
    # ==================== 6. 滞销品四级分级统计 ====================
    # 只有当同时有日期和库存字段时才计算
    if required_fields['日期'] and required_fields['库存'] and stock_col:
        # 计算每个商品的最后销售日期
        product_last_sale = df.groupby('商品名称')['日期'].max().reset_index() if '日期' in df.columns else df.groupby('商品名称')['下单时间'].max().reset_index()
        product_last_sale.columns = ['商品名称', '最后销售日期']
        
        # 计算滞销天数
        product_last_sale['滞销天数'] = (last_date - product_last_sale['最后销售日期']).dt.days
        
        # 获取商品的分类和库存信息
        product_info = df[['商品名称', '一级分类名']].drop_duplicates()
        product_stock = last_stock[['商品名称', stock_col]]
        product_stock.columns = ['商品名称', '库存']  # 统一列名为'库存'
        product_info = product_info.merge(product_stock, on='商品名称', how='left')
        product_info['库存'] = product_info['库存'].fillna(0)
        
        product_stagnant = product_last_sale.merge(product_info, on='商品名称', how='left')
        
        # 滞销品分级 (库存>0 且 无销量天数达到标准)
        product_stagnant['轻度滞销'] = ((product_stagnant['滞销天数'] == 7) & (product_stagnant['库存'] > 0)).astype(int)
        product_stagnant['中度滞销'] = ((product_stagnant['滞销天数'] >= 8) & (product_stagnant['滞销天数'] <= 15) & (product_stagnant['库存'] > 0)).astype(int)
        product_stagnant['重度滞销'] = ((product_stagnant['滞销天数'] >= 16) & (product_stagnant['滞销天数'] <= 30) & (product_stagnant['库存'] > 0)).astype(int)
        product_stagnant['超重度滞销'] = ((product_stagnant['滞销天数'] > 30) & (product_stagnant['库存'] > 0)).astype(int)
        
        # 按分类汇总滞销品数量
        stagnant_stats = product_stagnant.groupby('一级分类名').agg({
            '轻度滞销': 'sum',
            '中度滞销': 'sum',
            '重度滞销': 'sum',
            '超重度滞销': 'sum'
        }).reset_index()
        stagnant_stats.columns = ['分类', '轻度滞销', '中度滞销', '重度滞销', '超重度滞销']
        stagnant_stats['滞销品总数'] = stagnant_stats[['轻度滞销', '中度滞销', '重度滞销', '超重度滞销']].sum(axis=1)
        
        category_stats = category_stats.merge(stagnant_stats, on='分类', how='left')
        for col in ['轻度滞销', '中度滞销', '重度滞销', '超重度滞销', '滞销品总数']:
            category_stats[col] = category_stats[col].fillna(0).astype(int)
    else:
        # 缺少必需字段,无法计算滞销品
        for col in ['轻度滞销', '中度滞销', '重度滞销', '超重度滞销', '滞销品总数']:
            category_stats[col] = 0
    
    # ==================== 7. 库存周转天数计算 ====================
    # 只有当同时有日期、库存和月售字段时才计算
    if required_fields['日期'] and required_fields['库存'] and required_fields['月售'] and stock_col:
        # 计算日均销量
        date_range_days = (df['日期'].max() - df['日期'].min()).days + 1 if '日期' in df.columns else (df['下单时间'].max() - df['下单时间'].min()).days + 1
        
        # 按分类统计总销量
        category_quantity = df.groupby('一级分类名')['月售'].sum().reset_index()
        category_quantity.columns = ['分类', '总销量']
        category_stats = category_stats.merge(category_quantity, on='分类', how='left')
        category_stats['总销量'] = category_stats['总销量'].fillna(0)
        
        # 按分类统计当前库存（使用统一的库存字段名）
        category_stock = last_stock.groupby('一级分类名')[stock_col].sum().reset_index()
        category_stock.columns = ['分类', '当前库存']
        category_stats = category_stats.merge(category_stock, on='分类', how='left')
        category_stats['当前库存'] = category_stats['当前库存'].fillna(0)
        
        # 计算日均销量和库存周转天数
        category_stats['日均销量'] = (category_stats['总销量'] / date_range_days).round(2)
        category_stats['库存周转天数'] = (category_stats['当前库存'] / category_stats['日均销量'].replace(0, np.nan)).fillna(0).replace([np.inf, -np.inf], 0).round(1)
    else:
        # 缺少必需字段,无法计算库存周转
        if '月售' in df.columns:
            category_quantity = df.groupby('一级分类名')['月售'].sum().reset_index()
            category_quantity.columns = ['分类', '总销量']
            category_stats = category_stats.merge(category_quantity, on='分类', how='left')
            category_stats['总销量'] = category_stats['总销量'].fillna(0)
        else:
            category_stats['总销量'] = 0
        
        category_stats['当前库存'] = 0
        category_stats['日均销量'] = 0
        category_stats['库存周转天数'] = 0
    
    # ==================== 8. 按销售额排序,只取TOP20 ====================
    category_stats = category_stats.sort_values('销售额', ascending=False).head(20)
    
    # ==================== 9. 准备图表数据 ====================
    categories = category_stats['分类'].tolist()
    sales_data = category_stats['销售额'].round(2).tolist()  # ✅ 销售额
    profit_data = category_stats['利润额'].round(2).tolist()  # ✅ 利润额（已修复字段名）
    profit_rate_data = category_stats['利润率'].round(2).tolist()  # ✅ 利润率
    
    # 🔍 [调试] 打印传递给ECharts的最终数据
    print(f"\n🔍 [ECharts数据] 传递给图表的数据 (前5个分类):")
    for i in range(min(5, len(categories))):
        print(f"   {categories[i]}: 销售额={sales_data[i]}, 利润额={profit_data[i]}, 利润率={profit_rate_data[i]}%")
    
    # ==================== 10. ECharts图表配置 ====================
    option = {
        'title': dict(COMMON_TITLE, text='🏷️ 一级分类销售分析 TOP20'),
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'cross'},
            'backgroundColor': 'rgba(255, 255, 255, 0.95)',
            'borderColor': '#e5e7eb',
            'borderWidth': 1,
            'padding': [10, 15],
            'textStyle': {'color': '#333', 'fontSize': 13}
        },
        'legend': dict(COMMON_LEGEND,
            data=['销售额', '利润额', '利润率'],  # 🆕 新增利润额图例
            top='8%',
            right='5%'
        ),
        'grid': dict(COMMON_GRID, top='20%', bottom='20%', left='5%', right='8%'),
        'xAxis': {
            'type': 'category',
            'data': categories,
            'axisLabel': dict(COMMON_AXIS_LABEL, 
                rotate=45,
                interval=0,
                fontSize=11,
                margin=10
            )
        },
        'yAxis': [
            {
                'type': 'value',
                'name': '金额 (¥)',
                'nameTextStyle': {'color': '#333', 'fontSize': 12, 'fontWeight': 'bold'},
                'axisLabel': {
                    'color': '#666',
                    'fontSize': 11
                },
                'splitLine': COMMON_SPLIT_LINE
            },
            {
                'type': 'value',
                'name': '百分比 (%)',
                'nameTextStyle': {'color': '#f59e0b', 'fontSize': 12, 'fontWeight': 'bold'},
                'axisLabel': {
                    'color': '#666',
                    'fontSize': 11,
                    'formatter': '{value}%'
                },
                'splitLine': {'show': False}
            }
        ],
        'series': [
            {
                'name': '销售额',
                'type': 'bar',
                'data': sales_data,
                'yAxisIndex': 0,
                'barWidth': '35%',
                'itemStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': COMMON_COLORS['purple'][0]},
                            {'offset': 1, 'color': COMMON_COLORS['purple'][2]}
                        ]
                    },
                    'borderRadius': [4, 4, 0, 0]
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': '{c}',
                    'fontSize': 9,
                    'fontWeight': 'bold',
                    'color': '#666'
                }
            },
            {  # 🆕 新增利润额折线
                'name': '利润额',
                'type': 'line',
                'data': profit_data,
                'yAxisIndex': 0,  # 使用左侧Y轴(金额)
                'smooth': True,
                'symbol': 'circle',
                'symbolSize': 8,
                'lineStyle': {'width': 3, 'color': COMMON_COLORS['green'][0]},
                'itemStyle': {'color': COMMON_COLORS['green'][0], 'borderWidth': 2, 'borderColor': '#fff'},
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': '{c}',
                    'fontSize': 9,
                    'fontWeight': 'bold',
                    'color': COMMON_COLORS['green'][0]
                }
            },
            {
                'name': '利润率',
                'type': 'line',
                'data': profit_rate_data,
                'yAxisIndex': 1,
                'smooth': True,
                'symbol': 'diamond',
                'symbolSize': 10,
                'lineStyle': {'width': 3, 'color': COMMON_COLORS['orange'][0]},
                'itemStyle': {'color': COMMON_COLORS['orange'][0], 'borderWidth': 2, 'borderColor': '#fff'},
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': '{c}%',
                    'fontSize': 9,
                    'fontWeight': 'bold',
                    'color': COMMON_COLORS['orange'][0]
                }
            }
        ],
        **COMMON_ANIMATION
    }
    
    # 创建图表
    chart = DashECharts(
        option=option,
        style={'height': '500px', 'width': '100%'}
    )
    
    # ==================== 11. 创建数据表格 ====================
    # 准备表格数据
    table_data = category_stats[[
        '分类', '销售额', '利润额', '总销量', '利润率', '售罄品数', 
        '轻度滞销', '中度滞销', '重度滞销', '超重度滞销', '滞销品总数',
        '库存周转天数'
    ]].copy()
    
    # 保存原值用于条件判断(在格式化之前)
    table_data['库存周转天数_原值'] = table_data['库存周转天数'].copy()
    
    # 格式化数值
    table_data['销售额'] = table_data['销售额'].apply(lambda x: f"¥{x:,.0f}")
    table_data['利润额'] = table_data['利润额'].apply(lambda x: f"¥{x:,.0f}")
    table_data['总销量'] = table_data['总销量'].apply(lambda x: f"{int(x):,}件")
    table_data['利润率'] = table_data['利润率'].apply(lambda x: f"{x:.1f}%")
    table_data['库存周转天数'] = table_data['库存周转天数_原值'].apply(lambda x: f"{x:.1f}天" if x > 0 else "-")
    
    # 创建表格行
    table_rows = []
    for idx, row in table_data.iterrows():
        # 售罄品单元格
        sellout_cell = html.Td(
            html.Span(
                f"⚠️ {row['售罄品数']}个",
                className="badge bg-danger" if row['售罄品数'] > 0 else "text-muted",
                style={'fontSize': '12px'}
            ) if row['售罄品数'] > 0 else "-"
        )
        
        # 滞销品单元格 - 添加文字说明
        stagnant_badges = []
        if row['轻度滞销'] > 0:
            stagnant_badges.append(html.Span(f"🟡轻度{row['轻度滞销']}", className="badge bg-warning text-dark me-1", style={'fontSize': '11px'}, title="7天无销量"))
        if row['中度滞销'] > 0:
            stagnant_badges.append(html.Span(f"🟠中度{row['中度滞销']}", className="badge bg-orange me-1", style={'fontSize': '11px', 'background': '#f97316', 'color': 'white'}, title="8-15天无销量"))
        if row['重度滞销'] > 0:
            stagnant_badges.append(html.Span(f"🔴重度{row['重度滞销']}", className="badge bg-danger me-1", style={'fontSize': '11px'}, title="16-30天无销量"))
        if row['超重度滞销'] > 0:
            stagnant_badges.append(html.Span(f"⚫超重度{row['超重度滞销']}", className="badge bg-dark me-1", style={'fontSize': '11px'}, title=">30天无销量"))
        
        stagnant_cell = html.Td(
            html.Div([
                html.Div(stagnant_badges if stagnant_badges else "-"),
                html.Small(f"共{row['滞销品总数']}个", className="text-muted") if row['滞销品总数'] > 0 else None
            ])
        )
        table_rows.append(
            html.Tr([
                html.Td(html.Strong(row['分类'])),
                html.Td(row['销售额']),
                html.Td(row['利润额']),
                html.Td(row['总销量'], style={'textAlign': 'center'}),
                html.Td(row['利润率']),
                sellout_cell,
                stagnant_cell,
                html.Td(row['库存周转天数'], style={'color': '#d97706' if row['库存周转天数_原值'] > 30 else '#333'})
            ])
        )
    
    # 创建表格
    data_table = dbc.Table(
        [
            html.Thead([
                html.Tr([
                    html.Th("分类", style={'minWidth': '100px'}),
                    html.Th("销售额", style={'minWidth': '100px'}),
                    html.Th("利润额", style={'minWidth': '100px'}),
                    html.Th("销售量", style={'minWidth': '90px'}),
                    html.Th("利润率", style={'minWidth': '80px'}),
                    html.Th("售罄品", style={'minWidth': '80px'}),
                    html.Th("滞销品统计", style={'minWidth': '200px'}),
                    html.Th("库存周转", style={'minWidth': '90px'})
                ])
            ]),
            html.Tbody(table_rows)
        ],
        bordered=True,
        hover=True,
        responsive=True,
        striped=True,
        className="mt-3"
    )
    
    # ==================== 12. 返回组合组件和数据 ====================
    result_div = html.Div([
        # 图表
        chart,
        
        # 表格标题
        html.H5(
            "📊 详细数据明细",
            className="mt-4 mb-3",
            style={'fontWeight': '600'}
        ),
        
        # 数据表格
        data_table,
        
        # 说明文字
        dbc.Alert([
            html.Strong("📝 指标说明:"),
            html.Hr(className="my-2"),
            html.Div([
                html.Div("• 利润额: 订单实际利润总和 (与销售额共用左侧Y轴,绿色折线)", className="mb-1"),
                html.Div("• 利润率: 利润额 / 销售额 × 100% (右侧Y轴,橙色折线)", className="mb-1"),
                html.Div("• 售罄品: 库存=0 且 近7天有销量 (需紧急补货) ⚠️需要库存和日期字段", className="mb-1"),
                html.Div("• 滞销品: 🟡轻度7天 🟠中度8-15天 🔴重度16-30天 ⚫超重度>30天 (库存>0且无销量) ⚠️需要库存和日期字段", className="mb-1"),
                html.Div("• 库存周转: 当前库存 / 日均销量 (天数) ⚠️需要库存、日期和月售字段", className="mb-1"),
                html.Div("💡 提示: 如果某些指标显示为0或'-',请检查上传的数据是否包含必要字段", className="mb-1 text-muted", style={'fontSize': '12px', 'fontStyle': 'italic'})
            ], style={'fontSize': '13px'})
        ], color="light", className="mt-3"),
        
        # 隐藏的Store组件,存储数据用于导出
        dcc.Store(id='category-trend-data-store', data=category_stats.to_dict('records'))
    ])
    
    return result_div


# ==================== 新增：利润分布直方图 (ECharts) ====================
def create_profit_histogram_chart(order_agg):
    """创建订单利润分布直方图 - ECharts 版本"""
    import numpy as np
    
    profit_values = order_agg['订单实际利润'].values
    hist_counts, hist_bins = np.histogram(profit_values, bins=50)
    
    # 格式化数据
    formatted_counts = [format_number(v) for v in hist_counts.tolist()]
    
    # 生成 bin 标签
    bin_labels = [f'{hist_bins[i]:.0f}' for i in range(len(hist_counts))]
    
    option = {
        'title': dict(COMMON_TITLE, text='📊 订单利润分布', textStyle={'fontSize': 16}),
        'tooltip': dict(COMMON_TOOLTIP, axisPointer={'type': 'shadow'}),
        'grid': dict(COMMON_GRID, left='10%', right='10%'),
        'xAxis': {
            'type': 'category',
            'data': bin_labels,
            'name': '订单实际利润 (¥)',
            'axisLabel': dict(COMMON_AXIS_LABEL, rotate=45, fontSize=9)
        },
        'yAxis': {
            'type': 'value',
            'name': '订单数量',
            'splitLine': COMMON_SPLIT_LINE,
            'axisLabel': COMMON_AXIS_LABEL
        },
        'series': [{
            'name': '订单数量',
            'type': 'bar',
            'data': formatted_counts,
            'barWidth': '90%',
            'itemStyle': {
                'color': {
                    'type': 'linear',
                    'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                    'colorStops': [
                        {'offset': 0, 'color': COMMON_COLORS['green'][0]},
                        {'offset': 1, 'color': COMMON_COLORS['green'][2]}
                    ]
                },
                'borderRadius': [4, 4, 0, 0]
            },
            'emphasis': {'itemStyle': {'shadowBlur': 10, 'shadowColor': 'rgba(46,204,113,0.5)'}},
            'animationDelay': '{dataIndex} * 20'
        }],
        **COMMON_ANIMATION
    }
    
    return DashECharts(option=option, style={'height': '100%', 'width': '100%'})


# ==================== 新增：利润区间分布图 (ECharts) ====================
def create_profit_range_chart(order_agg):
    """创建利润区间分布柱状图 - 更直观的分析"""
    import numpy as np
    
    profit_values = order_agg['订单实际利润'].values
    
    # 定义利润区间
    bins = [-np.inf, -100, -50, -20, 0, 20, 50, 100, np.inf]
    labels = ['重度亏损\n(<-100)', '中度亏损\n(-100~-50)', '轻度亏损\n(-50~-20)', 
              '微亏损\n(-20~0)', '微盈利\n(0~20)', '良好盈利\n(20~50)', 
              '优秀盈利\n(50~100)', '超级盈利\n(>100)']
    
    # 统计各区间订单数
    counts, _ = np.histogram(profit_values, bins=bins)
    formatted_counts = [format_number(v) for v in counts.tolist()]
    
    # 根据盈亏设置颜色
    colors = ['#C0392B', '#E74C3C', '#FF6B6B', '#FFA07A',  # 亏损区间：深红到浅红
              '#98FB98', '#2ECC71', '#27AE60', '#229954']  # 盈利区间：浅绿到深绿
    
    # ========== ECharts 版本（统一配置）==========
    if ECHARTS_AVAILABLE:
        option = {
        'title': dict(COMMON_TITLE, 
            text='💰 订单利润区间分布分析 [统一配置✅]',
            subtext=f'总订单: {len(profit_values)} 笔'
        ),
        'tooltip': dict(COMMON_TOOLTIP,
            trigger='axis',
            axisPointer={'type': 'shadow'},
            formatter='{b}<br/>订单数: {c} 笔'
        ),
        'grid': COMMON_GRID,
        'xAxis': {
            'type': 'category',
            'data': labels,
            'axisLabel': dict(COMMON_AXIS_LABEL, interval=0, rotate=0),
            'axisTick': {'show': False},
            'axisLine': {'lineStyle': {'color': '#e0e0e0'}}
        },
        'yAxis': {
            'type': 'value',
            'name': '订单数量',
            'axisLabel': COMMON_AXIS_LABEL,
            'splitLine': COMMON_SPLIT_LINE
        },
        'series': [{
            'name': '订单数量',
            'type': 'bar',
            'data': [{'value': v, 'itemStyle': {'color': c}} for v, c in zip(formatted_counts, colors)],
            'barWidth': '70%',
            'label': {
                'show': True,
                'position': 'top',
                'formatter': '{c}',
                'fontSize': 11,
                'fontWeight': 'bold',
                'color': '#333'
            },
            'itemStyle': {
                'borderRadius': [6, 6, 0, 0],
                'shadowColor': 'rgba(0,0,0,0.1)',
                'shadowBlur': 5
            },
            'emphasis': {
                'itemStyle': {
                    'shadowBlur': 15,
                    'shadowColor': 'rgba(0,0,0,0.3)'
                }
            }
        }],
        **COMMON_ANIMATION
    }
    
        return DashECharts(option=option, style={'height': '500px', 'width': '100%'})
    
    # ========== Plotly 后备方案 ==========
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=labels,
        y=counts.tolist(),
        marker=dict(color=colors),
        text=formatted_counts,
        textposition='outside',
        textfont=dict(size=11, color='#333'),
        hovertemplate='<b>%{x}</b><br>订单数: %{y} 笔<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text=f'💰 订单利润区间分布分析<br><sub>总订单: {len(profit_values)} 笔</sub>',
            font=dict(size=18, color='#2c3e50'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            tickangle=0,
            tickfont=dict(size=10, color='#2c3e50')
        ),
        yaxis=dict(
            title='订单数量',
            tickfont=dict(size=11),
            showgrid=True,
            gridcolor='rgba(224,224,224,0.5)'
        ),
        height=380,
        margin=dict(l=60, r=40, t=80, b=80),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x'
    )
    
    return wrap_chart_component(fig, height='450px')


# ==================== 新增：通用横向排行榜 (ECharts) ====================
def create_horizontal_ranking_chart(data_df, name_field, value_field, title='排行榜', color_scheme='blue', limit=20):
    """
    创建通用横向柱状图排行榜 - ECharts 版本
    
    Args:
        data_df: DataFrame 数据
        name_field: 名称字段
        value_field: 数值字段
        title: 图表标题
        color_scheme: 颜色方案 (blue/green/red/orange/purple)
        limit: 显示前N名
    """
    # 取前N名
    top_data = data_df.nlargest(limit, value_field)
    
    # 颜色方案
    colors = {
        'blue': ['#4A90E2', '#2E5C8A'],
        'green': ['#2ECC71', '#27AE60'],
        'red': ['#FF6B6B', '#E74C3C'],
        'orange': ['#FF7F0E', '#E67E22'],
        'purple': ['#9B59B6', '#8E44AD']
    }
    color_pair = colors.get(color_scheme, colors['blue'])
    
    option = {
        'title': {'text': title, 'left': 'center', 'textStyle': {'fontSize': 16, 'fontWeight': 'bold', 'color': '#2c3e50'}},
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'shadow'},
            'backgroundColor': 'rgba(255,255,255,0.95)',
            'borderColor': '#ccc',
            'textStyle': {'color': '#333'}
        },
        'grid': {'left': '25%', 'right': '10%', 'top': '12%', 'bottom': '8%', 'containLabel': False},
        'xAxis': {
            'type': 'value',
            'splitLine': {'lineStyle': {'type': 'dashed', 'color': 'rgba(0,0,0,0.1)'}},
            'axisLabel': {'fontSize': 10}
        },
        'yAxis': {
            'type': 'category',
            'data': top_data[name_field].tolist()[::-1],
            'axisLabel': {'fontSize': 10, 'interval': 0}
        },
        'series': [{
            'name': value_field,
            'type': 'bar',
            'data': top_data[value_field].tolist()[::-1],
            'barWidth': '60%',
            'itemStyle': {
                'color': {
                    'type': 'linear',
                    'x': 0, 'y': 0, 'x2': 1, 'y2': 0,
                    'colorStops': [
                        {'offset': 0, 'color': color_pair[0]},
                        {'offset': 1, 'color': color_pair[1]}
                    ]
                },
                'borderRadius': [0, 8, 8, 0],
                'shadowColor': f'rgba({int(color_pair[0][1:3], 16)},{int(color_pair[0][3:5], 16)},{int(color_pair[0][5:7], 16)},0.3)',
                'shadowBlur': 10
            },
            'label': {
                'show': True,
                'position': 'right',
                'formatter': '{c}',
                'fontSize': 10,
                'fontWeight': 'bold',
                'color': '#2c3e50'
            },
            'emphasis': {'itemStyle': {'shadowBlur': 20}},
            'animationDelay': '{dataIndex} * 50'
        }],
        'animationEasing': 'elasticOut',
        'animationDuration': 1200
    }
    
    return DashECharts(option=option, style={'height': f'{max(400, limit * 25)}px', 'width': '100%'})


# ==================== 公共计算函数 ====================

def get_actual_date_range(df):
    """
    从数据中获取实际的日期范围
    
    Args:
        df: DataFrame，包含日期相关字段
        
    Returns:
        (start_date, end_date): 开始和结束日期的tuple，如果无法获取则返回(None, None)
    """
    try:
        # 尝试找到日期字段
        date_col = None
        for col in ['日期', '下单时间', 'date']:
            if col in df.columns:
                date_col = col
                break
        
        if date_col is None:
            return None, None
        
        # 转换为datetime并获取范围
        dates = pd.to_datetime(df[date_col], errors='coerce')
        dates = dates.dropna()
        
        if len(dates) == 0:
            return None, None
            
        return dates.min(), dates.max()
        
    except Exception as e:
        print(f"⚠️ 获取日期范围失败: {e}")
        return None, None


def calculate_order_metrics(df, calc_mode: Optional[str] = None):
    """
    统一的订单指标计算函数（Tab 1和Tab 2共用）
    
    核心计算逻辑:
    1. 空值处理：配送相关字段空值填充为0
    2. 订单级聚合（订单级字段用first，商品级字段用sum）
    3. 计算利润额（新公式）= 预计订单收入 - 成本 - 平台佣金 - 物流配送费 - 配送费减免金额 + 用户支付配送费
    4. 计算商家活动成本
    5. 计算订单总收入
    6. 计算订单实际利润 = 利润额 - 新客减免金额 + 企客后返
    
    Args:
        df: 原始数据DataFrame（必须包含订单ID字段）
        
    Returns:
        order_agg: 订单级聚合数据（包含利润额、订单实际利润等计算字段）
    """
    if '订单ID' not in df.columns:
        raise ValueError("数据缺少订单ID字段")
    
    calc_mode = normalize_calc_mode(calc_mode)
    
    # 🔍 调试: 检查输入数据
    print(f"🔍 [calculate_order_metrics] 输入数据: {len(df)} 行")
    print(f"   订单ID样本 (前5个): {df['订单ID'].head().tolist()}")
    print(f"   订单ID类型: {df['订单ID'].dtype}")
    print(f"   订单ID唯一值数量: {df['订单ID'].nunique()}")
    print(f"   订单ID是否有NaN: {df['订单ID'].isna().sum()}/{len(df)}")
    
    # 🔴 统一订单ID类型为字符串
    df['订单ID'] = df['订单ID'].astype(str)
    
    # 🔍 检查转换后是否产生了'nan'字符串
    nan_str_count = (df['订单ID'] == 'nan').sum()
    none_str_count = (df['订单ID'] == 'None').sum()
    print(f"   转换后订单ID样本: {df['订单ID'].head().tolist()}")
    print(f"   转换后订单ID类型: {df['订单ID'].dtype}")
    print(f"   转换后'nan'字符串数量: {nan_str_count}")
    print(f"   转换后'None'字符串数量: {none_str_count}")
    
    # 🔧 兼容不同成本字段名（'商品采购成本' 或 '成本'）
    cost_field = '商品采购成本' if '商品采购成本' in df.columns else '成本'
    
    # 🔧 兼容不同销量字段名（'月售' 或 '销量'）
    sales_field = '月售' if '月售' in df.columns else '销量'
    
    # ===== 前置处理：空值填充 =====
    # 配送相关字段空值填充为0，避免计算错误
    df['物流配送费'] = df['物流配送费'].fillna(0)
    df['配送费减免金额'] = df['配送费减免金额'].fillna(0)
    df['用户支付配送费'] = df['用户支付配送费'].fillna(0)
    
    # ⚠️ 关键修复：实收价格是单价，需要先乘以销量，再聚合
    if '实收价格' in df.columns and sales_field in df.columns:
        df['订单总收入'] = df['实收价格'] * df[sales_field]
        print(f"🔧 [实收价格修复] 计算订单总收入 = 实收价格 × {sales_field}")
    elif '实收价格' in df.columns:
        print(f"⚠️ [实收价格修复] 缺少'{sales_field}'字段，无法计算订单总收入")
    
    # ===== Step 1: 订单级聚合 =====
    agg_dict = {
        '商品实售价': 'sum',              # 商品销售额(商品级,sum)
        '预计订单收入': 'sum',            # ✅ 商品级字段: 每个商品有不同的预计订单收入,需要sum
        '用户支付配送费': 'first',        # 订单级字段
        '配送费减免金额': 'first',
        '物流配送费': 'first',
        '平台佣金': 'first',
    }

    # ⚠️ 商品级字段：月售、平台服务费、订单总收入需要sum
    if sales_field in df.columns:
        agg_dict[sales_field] = 'sum'
    if '平台服务费' in df.columns:
        agg_dict['平台服务费'] = 'sum'
    # ⚠️ 关键修复：使用订单总收入（已乘以销量）而不是直接sum实收价格
    if '订单总收入' in df.columns:
        agg_dict['订单总收入'] = 'sum'  # 已经乘以销量，直接sum

    # ✅ 动态添加订单级可选字段（避免字段不存在的错误）
    optional_fields_first = ['满减金额', '商品减免金额', '商家代金券',
                            '商家承担部分券', '打包袋金额', '配送平台', '渠道']

    for field in optional_fields_first:
        if field in df.columns:
            agg_dict[field] = 'first'
    
    # ✅ 添加利润额字段（如果存在，商品级需要sum）
    if '利润额' in df.columns:
        agg_dict['利润额'] = 'sum'  # 商品级字段，按订单汇总
    
    # ✅ 动态添加新增营销维度字段
    # 订单级字段:满赠金额、商家其他优惠、新客减免金额、配送平台 -> first()
    for field in ['满赠金额', '商家其他优惠', '新客减免金额', '配送平台']:
        if field in df.columns:
            agg_dict[field] = 'first'
    
    # ⚠️ 商品级字段:企客后返(每个商品单独返现) -> sum()
    if '企客后返' in df.columns:
        agg_dict['企客后返'] = 'sum'
    
    # 动态添加成本字段
    if cost_field in df.columns:
        agg_dict[cost_field] = 'sum'
    
    print(f"🔍 [calculate_order_metrics] 准备groupby,聚合字典包含 {len(agg_dict)} 个字段")
    
    order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    
    # ⚠️ 关键修复：将订单总收入重命名为实收价格（现在是总额）
    if '订单总收入' in order_agg.columns:
        order_agg['实收价格'] = order_agg['订单总收入']
        print(f"✅ [实收价格修复] 重命名: 订单总收入 → 实收价格（现为订单级总额）")
    
    print(f"✅ [calculate_order_metrics] groupby完成: {len(order_agg)} 个订单")
    if len(order_agg) > 0:
        print(f"   订单ID样本: {order_agg['订单ID'].head().tolist()}")
        # 🔍 检查渠道字段
        if '渠道' in order_agg.columns:
            channel_dist = order_agg['渠道'].value_counts()
            print(f"   渠道分布:")
            for ch, cnt in channel_dist.items():
                print(f"     {ch}: {cnt} 订单")
        else:
            print(f"   ⚠️ 警告: order_agg中没有'渠道'字段!")
    else:
        print(f"   ❌ groupby后数据为空!")
    
    # 🔧 统一成本字段名为'商品采购成本'
    if cost_field == '成本':
        order_agg['商品采购成本'] = order_agg['成本']

    # 🔧 关键字段兜底
    if '平台服务费' not in order_agg.columns:
        order_agg['平台服务费'] = 0
    order_agg['平台服务费'] = order_agg['平台服务费'].fillna(0)

    if '企客后返' not in order_agg.columns:
        order_agg['企客后返'] = 0
    else:
        order_agg['企客后返'] = order_agg['企客后返'].fillna(0)

    # 兼容旧数据：若缺少平台佣金字段，使用平台服务费
    if '平台佣金' not in order_agg.columns:
        order_agg['平台佣金'] = order_agg['平台服务费']
    else:
        order_agg['平台佣金'] = order_agg['平台佣金'].fillna(0)
    
    # ===== Step 2: 计算配送净成本 =====
    # 公式: 配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返
    # ⚠️ 注意: 体现平台真实承担的配送支出
    order_agg['配送净成本'] = (
        order_agg['物流配送费'] - 
        (order_agg['用户支付配送费'] - order_agg['配送费减免金额']) - 
        order_agg['企客后返']
    )
    
    # ===== Step 2.2: 利润额处理 =====
    # 📊 两套公式说明:
    # 
    # 【第一套公式】(当前使用) - 基于Excel利润额:
    #   订单实际利润 = 利润额 - 物流配送费 - 平台佣金 - 新客减免金额 + 企客后返
    #   ⚠️ 物流配送费使用原始值,不剔除任何配送平台
    # 
    # 【第二套公式】(备用) - 从零计算:
    #   订单实际利润 = 预计订单收入 - 成本 - 平台佣金 - 实际物流配送费 
    #                 - 配送费减免金额 + 用户支付配送费 + 企客后返
    #   ⚠️ 实际物流配送费需剔除: eleck、美团跑腿-平台扣减、京东平台配送-平台扣减
    # 
    # ✅ 优先使用Excel中的"利润额"字段(已包含所有成本扣减)
    # ✅ 如果没有利润额字段,使用第二套公式计算(需要剔除特定配送平台)
    
    if '利润额' not in order_agg.columns:
        # 兼容旧数据: 使用第二套公式计算
        # 步骤1: 根据配送平台调整物流配送费
        平台扣减列表 = ['eleck', '美团跑腿-平台扣减', '京东平台配送-平台扣减']
        if '配送平台' in order_agg.columns:
            order_agg['实际物流配送费_临时'] = order_agg.apply(
                lambda row: 0 if row.get('配送平台', '') in 平台扣减列表 else row['物流配送费'],
                axis=1
            )
        else:
            order_agg['实际物流配送费_临时'] = order_agg['物流配送费']
        
        # 步骤2: 计算利润额
        order_agg['利润额'] = (
            order_agg['预计订单收入'] - 
            order_agg['商品采购成本'] - 
            order_agg['平台佣金'] - 
            order_agg['实际物流配送费_临时'] - 
            order_agg['配送费减免金额'] + 
            order_agg['用户支付配送费'] +
            order_agg.get('企客后返', 0)
        )
    # else: 直接使用已聚合的Excel利润额字段（已在groupby中sum）
    
    # ===== Step 3: 计算商家活动成本 =====
    # 公式: 商家活动成本 = 满减金额 + 商品减免金额 + 商家代金券 + 商家承担部分券 + 满赠金额 + 商家其他优惠
    order_agg['商家活动成本'] = (
        order_agg.get('满减金额', 0) + 
        order_agg.get('商品减免金额', 0) + 
        order_agg.get('商家代金券', 0) +
        order_agg.get('商家承担部分券', 0) +  # 包含商家承担部分券
        order_agg.get('满赠金额', 0) +  # ✅ 新增：满赠金额
        order_agg.get('商家其他优惠', 0)  # ✅ 新增：商家其他优惠
    )
    
    # ===== Step 4: 订单总收入（直接使用原始数据字段"预计订单收入"）=====
    # 注：原始数据中"预计订单收入"已包含商品售价、打包费、配送费等
    if '预计订单收入' not in order_agg.columns:
        # 兼容旧数据：如果没有"预计订单收入"字段，则计算
        order_agg['订单总收入'] = (
            order_agg['实收价格'] + 
            order_agg['打包袋金额'] + 
            order_agg['用户支付配送费']
        )
    else:
        order_agg['订单总收入'] = order_agg['预计订单收入']
    
    # ===== Step 5: 计算订单实际利润（核心公式）=====
    # 📊 公式: 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
    # 
    # ⚠️ 关键说明:
    #   - 利润额: 直接使用Excel中的值(已包含所有成本扣减)
    #   - 物流配送费: 使用原始值,不剔除任何配送平台
    #   - 平台服务费: 订单级字段（新增）
    #   - 企客后返: 商品级补偿项(已sum聚合)
    # 
    # 💡 为什么不剔除配送平台?
    #   因为Excel的利润额已经扣除了所有平台的配送费
    #   这里再次扣除物流配送费,是为了避免Excel利润额计算不完整的情况
    # 
    # 🎯 如需修改利润公式,只需修改 _calculate_profit_formula() 函数,全局生效!
    
    order_agg['订单实际利润'] = _calculate_profit_formula(order_agg, calc_mode)
    
    # ⚠️ 关键修复: 统一剔除平台服务费=0的订单
    # 业务规则: 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
    # 只有平台服务费>0的订单才是真实的平台订单,需要计入利润
    if calc_mode == 'service_fee_positive':
        # 兼容逻辑: 平台服务费>0 或 平台佣金>0
        # 原因: 历史数据导入时,Excel的'平台服务费'列未正确映射到platform_service_fee字段
        # 而是映射到了commission字段,因此需要同时检查两个字段
        filtered = order_agg[
            (order_agg['平台服务费'] > 0) | (order_agg['平台佣金'] > 0)
        ].copy()
    elif calc_mode == 'all_with_fallback':
        # ✅ 修复: all_with_fallback模式也需要剔除平台服务费=0的订单
        # 逻辑: 先使用平台服务费,如果<=0则使用平台佣金兜底,但最终必须>0
        service_fee_col = order_agg.get('平台服务费', pd.Series(0, index=order_agg.index))
        commission_col = order_agg.get('平台佣金', pd.Series(0, index=order_agg.index))
        # 计算有效的服务费(使用兜底后的值)
        effective_fee = service_fee_col.copy()
        fallback_mask = (effective_fee <= 0)
        effective_fee = effective_fee.mask(fallback_mask, commission_col)
        # 只保留有效服务费>0的订单
        filtered = order_agg[effective_fee > 0].copy()
    else:
        # all_no_fallback: 只使用平台服务费,必须>0
        filtered = order_agg[order_agg.get('平台服务费', 0) > 0].copy()
    
    filtered['计算口径'] = calc_mode
    
    # 🔍 [调试] 打印order_agg聚合后的字段和样本数据
    print(f"\n🔍 [calculate_order_metrics] 聚合后order_agg:")
    print(f"   订单数: {len(filtered)}")
    print(f"   字段列表: {filtered.columns.tolist()}")
    
    # 打印销售和利润相关字段的样本数据
    sample_cols = ['订单ID', '订单实际利润', '利润额', '订单总收入']
    if '实收价格' in filtered.columns:
        sample_cols.append('实收价格')
    if '商品实售价' in filtered.columns:
        sample_cols.append('商品实售价')
    if '预计订单收入' in filtered.columns:
        sample_cols.append('预计订单收入')
    
    available_cols = [col for col in sample_cols if col in filtered.columns]
    print(f"   样本数据 (前3行):")
    print(filtered[available_cols].head(3).to_string(index=False))
    
    # 打印销售额和利润额的汇总统计
    if '实收价格' in filtered.columns and '利润额' in filtered.columns:
        total_sales = filtered['实收价格'].sum()
        total_profit = filtered['利润额'].sum()
        profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
        print(f"\n   汇总统计:")
        print(f"   - 总销售额(实收价格): ¥{total_sales:,.2f}")
        print(f"   - 总利润额: ¥{total_profit:,.2f}")
        print(f"   - 利润率: {profit_rate:.2f}%")
    
    return filtered


def _calculate_profit_formula(order_agg, calc_mode: Optional[str] = None):
    """
    🔧 利润公式计算辅助函数 - 全局唯一利润计算逻辑
    
    ⚠️ 重要: 这是全局唯一的利润计算公式!
    所有TAB页的利润计算都调用这个函数,确保公式一致性
    
    如需修改利润公式,只需修改这个函数,所有TAB页自动生效:
    - Tab1 订单数据概览
    - Tab1 环比计算
    - Tab1 每日趋势分析
    - Tab1 异常诊断
    - Tab2 渠道分析
    - Tab3+ 其他所有使用订单实际利润的地方
    
    当前使用: 新公式(基于Excel利润额 + 平台服务费)
    公式: 订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返
    
    参数:
        order_agg: 订单级聚合数据(DataFrame,必须包含以下字段)
            - 利润额: 商品级sum
            - 物流配送费: 订单级first
            - 平台佣金: 订单级first
            - 新客减免金额(可选): 订单级first
            - 企客后返(可选): 商品级sum
        calc_mode: 计算口径, 控制平台服务费与兜底逻辑
            - service_fee_positive/all_no_fallback: 仅使用平台服务费
            - all_with_fallback: 平台服务费<=0时使用平台佣金兜底
    
    返回:
        Series: 订单实际利润
    """
    mode = normalize_calc_mode(calc_mode)

    service_fee = order_agg.get('平台服务费')
    if service_fee is None:
        service_fee = pd.Series(0, index=order_agg.index, dtype=float)
    else:
        service_fee = service_fee.fillna(0)

    if mode == 'all_with_fallback':
        commission = order_agg.get('平台佣金', 0)
        if not isinstance(commission, pd.Series):
            commission = pd.Series(commission, index=order_agg.index, dtype=float)
        else:
            commission = commission.fillna(0)
        fallback_mask = (service_fee <= 0)
        service_fee = service_fee.mask(fallback_mask, commission)

    return (
        order_agg['利润额'] -
        service_fee -
        order_agg['物流配送费'] +
        order_agg.get('企客后返', 0)
    )


# ==================== 性能优化: 缓存管理回调 (阶段3) ====================

@app.callback(
    Output('cache-version', 'data'),
    Input('data-update-trigger', 'data'),
    prevent_initial_call=True
)
def invalidate_cache(trigger):
    """
    数据更新时清空缓存
    - data-update-trigger变化 → cache-version自增 → 缓存失效
    """
    print(f"🔄 [缓存管理] data-update-trigger={trigger}, 缓存失效", flush=True)
    return trigger  # 直接使用trigger作为版本号


# ==================== Tab 1-7 内容回调 ====================

# Tab 1: 订单数据概览
@app.callback(
    [Output('tab-1-content', 'children'),
     Output('cached-order-agg', 'data'),  # ⚡ 缓存订单聚合数据
     Output('cached-comparison-data', 'data')],  # ⚡ 缓存环比数据
    [Input('main-tabs', 'value'),
     Input('data-update-trigger', 'data')],
    [State('cached-order-agg', 'data'),  # ⚡ 读取缓存
     State('cached-comparison-data', 'data'),
     State('cache-version', 'data')]
)
def render_tab1_content(active_tab, trigger, cached_agg, cached_comparison, cache_version):
    """渲染Tab 1：订单数据概览（✅ 使用统一计算函数 + ⚡ 缓存优化）"""
    global GLOBAL_DATA, GLOBAL_FULL_DATA
    
    if active_tab != 'tab-1':
        raise PreventUpdate
    
    # 添加数据信息卡片（通过全局回调更新）
    data_info_placeholder = html.Div(id='tab1-data-info')
    
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return dbc.Container([
            data_info_placeholder,
            dbc.Alert("⚠️ 未找到数据，请检查数据文件", color="warning")
        ]), None, None  # ⚡ 返回3个值(包括缓存)
    
    df = GLOBAL_DATA.copy()
    
    # ========== ⚡ 性能优化: 检查缓存有效性 ==========
    cache_valid = (
        cached_agg is not None 
        and cached_comparison is not None 
        and cache_version == trigger  # 缓存版本匹配
    )
    
    if cache_valid:
        print(f"⚡ [性能优化] 使用缓存数据,跳过订单聚合和环比计算", flush=True)
        order_agg = pd.DataFrame(cached_agg)
        print(f"   🔍 缓存的order_agg行数: {len(order_agg)}", flush=True)
        # ⚠️ 检查缓存是否包含新字段,如果没有则重新计算
        if '配送净成本' not in order_agg.columns:
            print(f"⚠️ 缓存数据缺少'配送净成本'字段,重新计算...", flush=True)
            cache_valid = False
        elif len(order_agg) == 0:
            print(f"⚠️ 缓存的order_agg为空,重新计算...", flush=True)
            cache_valid = False
        else:
            comparison_metrics = cached_comparison.get('comparison_metrics', {})
            channel_comparison = cached_comparison.get('channel_comparison', {})
            # ⚠️ 新增检查:如果环比数据为空,则强制重新计算
            if not comparison_metrics or (not channel_comparison and '渠道' in df.columns):
                print(f"⚠️ 缓存中环比数据为空,强制重新计算...", flush=True)
                cache_valid = False
                # ⚠️ 关键:清空环比变量,让后续if not cache_valid块重新计算
                comparison_metrics = None
                channel_comparison = None
    
    if not cache_valid:
        print(f"🔄 [缓存失效] 重新计算订单聚合和环比数据", flush=True)
        
        # 🔍 在调用calculate_order_metrics之前检查df
        print(f"\n🔍 [调用前检查] df数据状态:", flush=True)
        print(f"   行数: {len(df)}", flush=True)
        print(f"   字段: {list(df.columns)}", flush=True)
        if '订单ID' in df.columns:
            print(f"   订单ID字段存在: ✅", flush=True)
            print(f"   订单ID样本 (前5): {df['订单ID'].head().tolist()}", flush=True)
            print(f"   订单ID类型: {df['订单ID'].dtype}", flush=True)
            print(f"   订单ID唯一数: {df['订单ID'].nunique()}", flush=True)
            print(f"   订单ID NaN数: {df['订单ID'].isna().sum()}", flush=True)
        else:
            print(f"   订单ID字段: ❌ 不存在!", flush=True)
    
    # ========== 步骤1：使用统一计算函数(仅在缓存失效时) ==========
    if not cache_valid:
        try:
            # 🔧 Tab1订单数据概览：使用all_with_fallback模式，保留所有订单（包括闪购小程序）
            order_agg = calculate_order_metrics(df, calc_mode='all_with_fallback')  # ✅ 调用公共函数
        except ValueError as e:
            return dbc.Container([
                data_info_placeholder,
                dbc.Alert(f"❌ {str(e)}", color="danger")
            ]), None, None
    
    # ========== 步骤2：计算汇总指标 ==========
    print(f"📊 [汇总指标计算] order_agg状态: {len(order_agg)} 行", flush=True)
    total_orders = len(order_agg)
    
    # ✅ 修改: 使用实收价格计算商品实收额和客单价
    if '实收价格' in order_agg.columns:
        total_actual_sales = order_agg['实收价格'].sum()  # 商品实收额
        avg_order_value = total_actual_sales / total_orders if total_orders > 0 else 0  # 客单价
        print(f"   ✅ 使用'实收价格'字段: 商品实收额=¥{total_actual_sales:,.2f}", flush=True)
    else:
        # 兼容旧数据: 如果没有实收价格,使用商品实售价
        total_actual_sales = order_agg['实收价格'].sum()
        avg_order_value = total_actual_sales / total_orders if total_orders > 0 else 0
        print(f"   ⚠️ 缺少'实收价格'字段,使用'商品实售价': ¥{total_actual_sales:,.2f}", flush=True)
    
    total_revenue = order_agg['订单总收入'].sum()
    total_profit = order_agg['订单实际利润'].sum()
    
    # ✅ 总利润率 = 订单实际利润 / 实收价格（订单实际利润已正确剔除平台服务费=0的订单）
    profit_rate = (total_profit / total_actual_sales * 100) if total_actual_sales > 0 else 0
    
    # 🔍 调试: 打印卡片指标
    print(f"\n{'='*60}", flush=True)
    print(f"🔍 [Tab1卡片指标] 基于当前数据计算:", flush=True)
    print(f"   订单数: {total_orders}", flush=True)
    print(f"   总利润: ¥{total_profit:,.2f}", flush=True)
    print(f"   数据量: {len(df)} 行", flush=True)
    print(f"{'='*60}\n", flush=True)
    
    # ✅ 修正: 预计零售额从order_agg获取(已在calculate_order_metrics中正确聚合)
    if '订单总收入' in order_agg.columns:
        total_expected_revenue = order_agg['订单总收入'].sum()
        print(f"   预计零售额: ¥{total_expected_revenue:,.2f} (从order_agg.订单总收入)", flush=True)
    else:
        total_expected_revenue = total_revenue
        print(f"   预计零售额: ¥{total_expected_revenue:,.2f} (备选方案)", flush=True)
    
    # ✅ 修正：动销商品数 = 有销量的商品（月售>0）
    if '商品名称' in df.columns and '月售' in df.columns:
        total_products = df[df['月售'] > 0]['商品名称'].nunique()
    else:
        total_products = df['商品名称'].nunique() if '商品名称' in df.columns else 0
    
    # ========== 步骤3：计算环比数据(仅在缓存失效时) ==========
    if not cache_valid:
        # ✅ 修复: 环比计算应该基于完整数据集,但返回值应该与卡片显示的数据一致
        # 重要: 卡片显示的是当前筛选数据的指标,环比也应该对比相同口径的数据
        comparison_metrics = {}
        channel_comparison = {}  # 渠道环比数据
        
        if '日期' in df.columns and GLOBAL_FULL_DATA is not None:
            try:
                print(f"\n{'='*60}")
                print(f"🔍 开始计算环比数据...")
                print(f"   当前查询数据量: {len(df)} 行")
                print(f"   完整数据量: {len(GLOBAL_FULL_DATA)} 行")
                df_dates = pd.to_datetime(df['日期'])
                actual_start = df_dates.min()
                actual_end = df_dates.max()
                print(f"   查询日期范围: {actual_start.date()} ~ {actual_end.date()}")
                
                # ✅ 关键修复: 直接使用已经过滤好的df数据(包含所有业务规则:剔除耗材、渠道过滤等)
                # 这样才能确保环比计算的当前值与卡片显示完全一致
                print(f"   ✅ 使用当前已过滤数据计算指标(确保与卡片一致)", flush=True)
                print(f"      当前查询数据: {len(df)} 行", flush=True)
                
                # 直接使用卡片显示的指标值(这些值已经基于过滤后的df计算)
                current_total_orders = total_orders
                current_actual_sales = total_actual_sales  # ✅ 修改: 使用实收价格
                current_total_profit = total_profit
                current_avg_order_value = avg_order_value
                current_profit_rate = profit_rate
                current_products = total_products
                
                print(f"      ✅ 当前周期指标(与卡片显示一致):", flush=True)
                print(f"         订单数: {current_total_orders}", flush=True)
                print(f"         总利润: ¥{current_total_profit:,.0f}", flush=True)
                print(f"         商品实收额: ¥{current_actual_sales:,.0f}", flush=True)
                print(f"         客单价: ¥{current_avg_order_value:.2f}", flush=True)
                print(f"         总利润率: {current_profit_rate:.1f}%", flush=True)
                print(f"         动销商品数: {current_products}", flush=True)
                
                # ✅ 使用完整数据集计算环比(包含上一周期数据)
                comparison_metrics = calculate_period_comparison(
                    GLOBAL_FULL_DATA,  # 使用完整数据(包含历史数据)
                    start_date=actual_start, 
                    end_date=actual_end
                )
                
                # ✅ 关键修复: 用卡片显示的真实值覆盖环比计算的当前值
                print(f"   🔧 开始覆盖环比数据的current值...", flush=True)
                if comparison_metrics:
                    if '订单数' in comparison_metrics:
                        old_val = comparison_metrics['订单数']['current']
                        comparison_metrics['订单数']['current'] = current_total_orders
                        print(f"      订单数: {old_val} → {current_total_orders}", flush=True)
                    # ✅ 修改: 预计零售额 → 商品实收额
                    if '预计零售额' in comparison_metrics:
                        comparison_metrics['商品实收额'] = comparison_metrics.pop('预计零售额')
                    if '商品实收额' in comparison_metrics:
                        old_val = comparison_metrics['商品实收额']['current']
                        comparison_metrics['商品实收额']['current'] = current_actual_sales
                        print(f"      商品实收额: {old_val} → {current_actual_sales}", flush=True)
                    if '总利润' in comparison_metrics:
                        old_val = comparison_metrics['总利润']['current']
                        comparison_metrics['总利润']['current'] = current_total_profit
                        print(f"      总利润: {old_val:.2f} → {current_total_profit:.2f} ⭐", flush=True)
                    if '客单价' in comparison_metrics:
                        old_val = comparison_metrics['客单价']['current']
                        comparison_metrics['客单价']['current'] = current_avg_order_value
                        print(f"      客单价: {old_val} → {current_avg_order_value}", flush=True)
                    if '总利润率' in comparison_metrics:
                        old_val = comparison_metrics['总利润率']['current']
                        comparison_metrics['总利润率']['current'] = current_profit_rate
                        print(f"      总利润率: {old_val} → {current_profit_rate}", flush=True)
                    if '动销商品数' in comparison_metrics:
                        old_val = comparison_metrics['动销商品数']['current']
                        comparison_metrics['动销商品数']['current'] = current_products
                        print(f"      动销商品数: {old_val} → {current_products}", flush=True)
                
                # ✅ 新增:计算渠道环比数据
                if '渠道' in df.columns:
                    channel_comparison = calculate_channel_comparison(
                        GLOBAL_FULL_DATA,  # 使用完整数据
                        order_agg,
                        start_date=actual_start,
                        end_date=actual_end
                    )
                
                print(f"✅ 环比计算完成,返回 {len(comparison_metrics)} 个指标")
                if comparison_metrics:
                    for key, value in comparison_metrics.items():
                        print(f"   - {key}: 当前值={value.get('current', 0):.1f}, 上期值={value.get('previous', 0):.1f}, 变化率={value.get('change_rate', 0):.1f}%")
                else:
                    print(f"⚠️ 环比数据为空")
                print(f"{'='*60}\n")
            except Exception as e:
                print(f"❌ 环比计算异常: {e}")
                import traceback
                traceback.print_exc()
                comparison_metrics = {}
                channel_comparison = {}
        else:
            if '日期' not in df.columns:
                print(f"⚠️ 数据中缺少'日期'字段,无法计算环比")
            elif GLOBAL_FULL_DATA is None:
                print(f"⚠️ 完整数据集未加载,无法计算环比")
    else:
        # ⚠️ 修复:如果使用缓存,需要确保环比变量有值
        if comparison_metrics is None:
            comparison_metrics = {}
        if channel_comparison is None:
            channel_comparison = {}
    
    # ========== 步骤4: 构建UI内容 ==========
    content = dbc.Container([
        # 数据信息占位符（由全局回调更新）
        data_info_placeholder,
        
        # 标题和导出按钮
        dbc.Row([
            dbc.Col([
                html.H3("📊 订单数据概览", className="mb-0")
            ], width=8),
            dbc.Col([
                dbc.Button([
                    html.I(className="bi bi-download me-2"),
                    "导出经营分析报告"
                ], id="export-tab1-order-report-btn", color="success", size="lg", className="w-100"),
                dcc.Download(id="download-tab1-order-report")
            ], width=4)
        ], className="mb-4"),
        
        # 关键指标卡片
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📦 订单总数", className="card-title"),
                        html.H2(f"{total_orders:,}", className="text-primary"),
                        html.P("笔", className="text-muted"),
                        create_comparison_badge(comparison_metrics.get('订单数', {}))
                    ])
                ], className="modern-card text-center shadow-sm")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("💰 商品实收额", className="card-title"),
                        html.H2(f"¥{total_actual_sales:,.0f}", className="text-success"),
                        html.P("实收价格", className="text-muted small"),
                        create_comparison_badge(comparison_metrics.get('商品实收额', {}))
                    ])
                ], className="modern-card text-center shadow-sm")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("💎 总利润", className="card-title"),
                        html.H2(f"¥{total_profit:,.0f}", className="text-warning"),
                        html.P("元", className="text-muted"),
                        create_comparison_badge(comparison_metrics.get('总利润', {}))
                    ])
                ], className="modern-card text-center shadow-sm")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("🛒 平均客单价", className="card-title"),
                        html.H2(f"¥{avg_order_value:.2f}", className="text-danger"),
                        html.P("实收价格/订单数", className="text-muted small"),
                        create_comparison_badge(comparison_metrics.get('客单价', {}))
                    ])
                ], className="modern-card text-center shadow-sm")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📈 总利润率", className="card-title"),
                        html.H2(f"{profit_rate:.1f}%", className="text-success"),
                        html.P("利润/实收价格", className="text-muted small"),
                        create_comparison_badge(comparison_metrics.get('总利润率', {}))
                    ])
                ], className="modern-card text-center shadow-sm")
            ], md=2),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("🏷️ 动销商品数", className="card-title"),
                        html.H2(f"{total_products:,}", className="text-secondary"),
                        html.P("有销量的SKU", className="text-muted small"),
                        create_comparison_badge(comparison_metrics.get('动销商品数', {}))
                    ])
                ], className="modern-card text-center shadow-sm")
            ], md=2)
        ], className="mb-4"),
        
        # ========== ⚡ 阶段4: 渐进式加载区域 ==========
        # 渠道表现对比(异步加载,显示占位符)
        html.Div(id='tab1-channel-section', children=[
            html.H4("📡 渠道表现对比", className="mb-3"),
            create_skeleton_placeholder(height="150px", count=1)
        ]),
        
        # 客单价深度分析(异步加载,显示占位符)
        html.Div(id='tab1-aov-section', children=[
            html.H4("🛒 客单价深度分析", className="mb-3"),
            create_skeleton_placeholder(height="250px", count=1)
        ]),
        
        dbc.Button(
            "📊 查看详细分析",
            id="btn-show-detail-analysis",
            color="primary",
            size="lg",
            className="w-100 mb-4"
        ),
        
        html.Div(id='tab1-detail-content', style={'display': 'none'})
    ])
    
    # ========== ⚡ 性能优化: 存储计算结果到缓存 ==========
    # 🔍 调试:检查要缓存的数据
    if not cache_valid:
        print(f"💾 [缓存保存] 准备保存新计算的order_agg:", flush=True)
        print(f"   行数: {len(order_agg)}", flush=True)
        cached_agg_data = order_agg.to_dict('records')
        print(f"   转换为dict后记录数: {len(cached_agg_data)}", flush=True)
    else:
        print(f"💾 [缓存保存] 使用原有缓存数据", flush=True)
        cached_agg_data = cached_agg
    
    # ⚠️ 确保环比数据不为None
    if comparison_metrics is None:
        comparison_metrics = {}
    if channel_comparison is None:
        channel_comparison = {}
    
    # ⚠️ 强制日志:显示最终环比数据状态
    print(f"\n{'='*60}", flush=True)
    print(f"📊 [Tab1返回] 最终环比数据状态:", flush=True)
    print(f"   comparison_metrics: {len(comparison_metrics)} 个指标", flush=True)
    if comparison_metrics:
        for key in comparison_metrics.keys():
            print(f"      - {key}", flush=True)
    print(f"   channel_comparison: {len(channel_comparison)} 个渠道", flush=True)
    if channel_comparison:
        for key in channel_comparison.keys():
            print(f"      - {key}", flush=True)
    print(f"{'='*60}\n", flush=True)
    
    cached_comp_data = {
        'comparison_metrics': comparison_metrics,
        'channel_comparison': channel_comparison
    } if not cache_valid else cached_comparison
    
    return content, cached_agg_data, cached_comp_data


# ========== ⚡ 阶段4: 异步加载Tab1渠道和客单价分析 ==========
@app.callback(
    Output('tab1-channel-section', 'children'),
    [Input('tab-1-content', 'children'),
     Input('data-update-trigger', 'data')],
    [State('cached-order-agg', 'data'),
     State('cached-comparison-data', 'data'),
     State('cache-version', 'data')],  # 🔧 新增:监听缓存版本
    prevent_initial_call=True
)
def async_load_tab1_channel_section(tab_content, trigger, cached_agg, cached_comparison, cache_version):
    """
    ✨ 异步加载Tab1渠道表现对比卡片(企业级体验)
    - 在核心指标卡片显示后延迟加载
    - 提升首屏渲染速度
    - 🔧 修复:门店切换后缓存失效问题
    """
    print(f"🎨 [异步加载] 开始渲染Tab1渠道表现对比卡片", flush=True)
    print(f"   🔍 trigger={trigger}, cache_version={cache_version}", flush=True)
    
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return html.Div()
    
    df = GLOBAL_DATA.copy()
    
    # 🔧 修复:检查缓存版本是否匹配
    cache_valid = (
        cached_agg is not None 
        and cached_comparison is not None
        and cache_version == trigger  # 缓存版本必须匹配
    )
    
    # 从缓存读取数据
    if cache_valid:
        order_agg = pd.DataFrame(cached_agg)
        print(f"✅ [缓存命中] 使用缓存的order_agg和comparison数据", flush=True)
        # ⚠️ 检查缓存是否包含新字段,如果没有则重新计算
        if '配送净成本' not in order_agg.columns:
            print(f"⚠️ 缓存数据缺少'配送净成本'字段,重新计算...", flush=True)
            cache_valid = False
    
    if not cache_valid:
        print(f"🔄 [缓存失效] 重新计算订单聚合和渠道环比数据", flush=True)
        # 缓存未命中或失效,重新计算
        # 🔧 Tab1渠道分析：使用all_with_fallback模式，保留所有订单（包括闪购小程序）
        order_agg = calculate_order_metrics(df, calc_mode='all_with_fallback')
        # ⚠️ 重新计算渠道环比
        channel_comparison = {}
        if '渠道' in df.columns and GLOBAL_FULL_DATA is not None:
            actual_start, actual_end = get_actual_date_range(df)
            if actual_start and actual_end:
                channel_comparison = calculate_channel_comparison(
                    GLOBAL_FULL_DATA,
                    order_agg,
                    start_date=actual_start,
                    end_date=actual_end
                )
    else:
        # 使用缓存数据
        channel_comparison = cached_comparison.get('channel_comparison', {})
        # ⚠️ 新增检查:如果缓存的渠道环比为空,也重新计算
        if not channel_comparison and '渠道' in df.columns and GLOBAL_FULL_DATA is not None:
            print(f"⚠️ 缓存中渠道环比为空,重新计算...", flush=True)
            actual_start, actual_end = get_actual_date_range(df)
            if actual_start and actual_end:
                channel_comparison = calculate_channel_comparison(
                    GLOBAL_FULL_DATA,
                    order_agg,
                    start_date=actual_start,
                    end_date=actual_end
                )
    
    # 渲染渠道卡片
    channel_cards = _create_channel_comparison_cards(df, order_agg, channel_comparison) if '渠道' in df.columns else html.Div()
    
    # 🔍 调试: 输出渠道环比数据
    if channel_comparison:
        print(f"✅ [异步加载] 渠道环比数据包含 {len(channel_comparison)} 个渠道:")
        for ch, data in channel_comparison.items():
            print(f"   - {ch}: {list(data.keys())}")
    else:
        print(f"⚠️ [异步加载] 渠道环比数据为空!")
        print(f"   GLOBAL_FULL_DATA是否存在: {GLOBAL_FULL_DATA is not None}")
        if GLOBAL_FULL_DATA is not None:
            print(f"   GLOBAL_FULL_DATA行数: {len(GLOBAL_FULL_DATA)}")
    
    print(f"✅ [异步加载] Tab1渠道卡片渲染完成", flush=True)
    return channel_cards


@app.callback(
    Output('tab1-aov-section', 'children'),
    [Input('tab1-channel-section', 'children'),  # 等待渠道卡片加载完成
     Input('data-update-trigger', 'data')],
    [State('cached-order-agg', 'data'),
     State('cache-version', 'data')],  # 🔧 新增:监听缓存版本
    prevent_initial_call=True
)
def async_load_tab1_aov_section(channel_content, trigger, cached_agg, cache_version):
    """
    ✨ 异步加载Tab1客单价深度分析(企业级体验)
    - 在渠道卡片加载后延迟加载
    - 进一步优化渲染性能
    - 🔧 修复:门店切换后缓存失效问题
    """
    print(f"🎨 [异步加载] 开始渲染Tab1客单价深度分析", flush=True)
    print(f"   🔍 trigger={trigger}, cache_version={cache_version}", flush=True)
    
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return html.Div()
    
    df = GLOBAL_DATA.copy()
    
    # 🔧 修复:检查缓存版本是否匹配,不匹配则强制重新计算
    cache_valid = (
        cached_agg is not None 
        and cache_version == trigger  # 缓存版本必须匹配
    )
    
    # 从缓存读取订单聚合数据
    if cache_valid:
        order_agg = pd.DataFrame(cached_agg)
        print(f"🔍 [调试] 从缓存读取order_agg (cache_version匹配), 字段: {order_agg.columns.tolist()}", flush=True)
        # ⚠️ 检查缓存是否包含新字段,如果没有则重新计算
        if '配送净成本' not in order_agg.columns or '订单总收入' not in order_agg.columns:
            print(f"⚠️ 缓存数据缺少关键字段,重新计算...", flush=True)
            print(f"   缺少字段: {[f for f in ['配送净成本', '订单总收入'] if f not in order_agg.columns]}", flush=True)
            # 🔧 Tab1客单价分析：使用all_with_fallback模式，保留所有订单（包括闪购小程序）
            order_agg = calculate_order_metrics(df, calc_mode='all_with_fallback')
            print(f"✅ 重新计算后order_agg字段: {order_agg.columns.tolist()}", flush=True)
    else:
        print(f"🔍 [调试] 缓存失效或为空 (cache_valid={cache_valid}),调用calculate_order_metrics", flush=True)
        # 🔧 Tab1客单价分析：使用all_with_fallback模式，保留所有订单（包括闪购小程序）
        order_agg = calculate_order_metrics(df, calc_mode='all_with_fallback')
        print(f"✅ calculate_order_metrics返回字段: {order_agg.columns.tolist()}", flush=True)
    
    # 🔧 【CRITICAL】最后的防御: 确保订单总收入字段存在
    if '订单总收入' not in order_agg.columns:
        print(f"⚠️⚠️⚠️ order_agg中仍然缺少'订单总收入'字段,尝试创建...", flush=True)
        if '预计订单收入' in order_agg.columns:
            order_agg['订单总收入'] = order_agg['预计订单收入']
            print(f"✅ 已从'预计订单收入'创建'订单总收入'", flush=True)
        else:
            print(f"❌ '预计订单收入'也不存在! 字段列表: {order_agg.columns.tolist()}", flush=True)
    
    # 渲染客单价分析 (初始为全部渠道)
    aov_analysis = _create_aov_analysis(df, order_agg, selected_channel='all')
    
    # 🆕 获取渠道列表用于下拉菜单
    channel_options = [{'label': '全部渠道', 'value': 'all'}]
    if '渠道' in df.columns:
        unique_channels = sorted([ch for ch in df['渠道'].dropna().unique() if ch])
        channel_options.extend([{'label': ch, 'value': ch} for ch in unique_channels])
    
    # 🆕 将内容包装在容器中,并添加Store存储channel_options
    result = html.Div([
        dcc.Store(id='aov-channel-options-store', data=channel_options),
        html.Div(id='aov-analysis-content-container', children=[aov_analysis])
    ])
    
    print(f"✅ [异步加载] Tab1客单价分析渲染完成", flush=True)
    return result


# Tab 1 详细分析
@app.callback(
    [Output('tab1-detail-content', 'children'),
     Output('tab1-detail-content', 'style')],
    Input('btn-show-detail-analysis', 'n_clicks'),
    prevent_initial_call=True
)
def show_tab1_detail_analysis(n_clicks):
    """显示Tab 1详细分析"""
    if not n_clicks:
        raise PreventUpdate
    
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return dbc.Alert("⚠️ 数据不可用", color="warning"), {'display': 'block'}
    
    df = GLOBAL_DATA.copy()
    charts = []
    
    # ========== 🔍 调试日志：检查原始数据 ==========
    print("\n" + "="*80)
    print("🔍 [调试] show_tab1_detail_analysis 函数调用")
    print(f"📊 GLOBAL_DATA 数据量: {len(df)} 行")
    print(f"📋 GLOBAL_DATA 字段: {df.columns.tolist()}")
    
    if '商品采购成本' in df.columns:
        print(f"✅ '商品采购成本' 字段存在")
        print(f"   数据类型: {df['商品采购成本'].dtype}")
        print(f"   总和: ¥{df['商品采购成本'].sum():,.2f}")
        print(f"   非零数量: {(df['商品采购成本'] > 0).sum()} / {len(df)}")
        print(f"   NaN数量: {df['商品采购成本'].isna().sum()}")
        print(f"   样本数据（前5行）:")
        print(df[['商品名称', '商品采购成本', '商品实售价']].head(5).to_string())
    else:
        print(f"❌ '商品采购成本' 字段不存在！")
    
    # ========== 🔍 调试：检查营销活动字段 ==========
    print("\n🔍 [调试] 营销活动字段检查（聚合前）:")
    marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券']
    for field in marketing_fields:
        if field in df.columns:
            field_sum = df[field].fillna(0).sum()
            non_zero_count = (df[field].fillna(0) > 0).sum()
            print(f"   ✅ {field}: 总和=¥{field_sum:,.2f}, 非零行数={non_zero_count}/{len(df)}")
        else:
            print(f"   ❌ {field}: 字段不存在！")
    print("="*80 + "\n")
    
    # ========== 使用统一的订单聚合函数 ==========
    try:
        order_agg = calculate_order_metrics(df)
        print(f"✅ 使用 calculate_order_metrics() 函数聚合订单数据")
        print(f"   订单数: {len(order_agg)}")
        print(f"   包含字段: {order_agg.columns.tolist()}")
    except Exception as e:
        print(f"❌ calculate_order_metrics() 失败: {e}")
        return dbc.Alert(f"数据处理失败: {str(e)}", color="danger"), {'display': 'block'}
    
    # 计算汇总指标
    total_orders = len(order_agg)
    total_sales = order_agg['实收价格'].sum()
    total_revenue = order_agg['订单总收入'].sum()
    total_profit = order_agg['订单实际利润'].sum()
    profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
    profitable_orders = (order_agg['订单实际利润'] > 0).sum()
    profitable_rate = (profitable_orders / total_orders * 100) if total_orders > 0 else 0
    
    # ========== 🔍 调试日志：订单聚合后的数据 ==========
    print("\n" + "="*80)
    print("🔍 [调试] 订单聚合完成")
    print(f"📊 订单数: {total_orders}")
    print(f"💰 商品销售额: ¥{total_sales:,.2f}")
    print(f"💵 订单总收入: ¥{total_revenue:,.2f}")
    print(f"💎 总利润: ¥{total_profit:,.2f}")
    print(f"📈 利润率: {profit_rate:.2f}%")
    print(f"\n🔍 order_agg 字段: {order_agg.columns.tolist()}")
    
    if '商品采购成本' in order_agg.columns:
        product_cost_sum = order_agg['商品采购成本'].sum()
        print(f"\n✅ order_agg 中'商品采购成本'字段存在")
        print(f"   总和: ¥{product_cost_sum:,.2f}")
        print(f"   非零订单数: {(order_agg['商品采购成本'] > 0).sum()}")
        print(f"   样本数据（前5个订单）:")
        print(order_agg[['订单ID', '商品采购成本', '商品实售价', '订单实际利润']].head(5).to_string())
    else:
        print(f"\n❌ order_agg 中'商品采购成本'字段不存在！")
    print("="*80 + "\n")
    
    # 1. 日期趋势图
    if '日期' in df.columns:
        # ✅ 直接使用已经计算好的order_agg(包含新字段的完整利润计算)
        # 先提取日期信息(从原始数据)
        date_order_map = df[['订单ID', '日期']].drop_duplicates('订单ID')
        date_order_map['日期'] = date_order_map['日期'].dt.date
        
        # 合并日期到order_agg
        order_agg_with_date = order_agg.merge(date_order_map, on='订单ID', how='left')
        
        # ✅ 按日期聚合(使用实收价格)
        agg_dict = {
            '订单实际利润': 'sum',  # ✅ 包含新客减免金额和企客后返
            '订单ID': 'nunique'
        }
        
        # ✅ 优先使用实收价格，fallback到预计订单收入
        if '实收价格' in order_agg_with_date.columns:
            agg_dict['实收价格'] = 'sum'
        elif '预计订单收入' in order_agg_with_date.columns:
            agg_dict['预计订单收入'] = 'sum'
        else:
            agg_dict['实收价格'] = 'sum'
        
        daily_sales = order_agg_with_date.groupby('日期').agg(agg_dict).reset_index()
        
        # ✅ 重命名列，确保使用'销售额'名称
        col_mapping = {'订单ID': '订单数', '订单实际利润': '总利润'}
        if '实收价格' in daily_sales.columns:
            col_mapping['实收价格'] = '销售额'
        elif '预计订单收入' in daily_sales.columns:
            col_mapping['预计订单收入'] = '销售额'
        else:
            col_mapping['实收价格'] = '销售额'
        
        daily_sales.rename(columns=col_mapping, inplace=True)
        
        # ========== ⚡ 阶段6: 图表数据采样优化 ==========
        sampled_daily_sales, sampling_info = downsample_data_for_chart(
            daily_sales, 
            max_points=500,  # 趋势图最多500个点
            sort_column='日期',
            keep_extremes=True  # 保留最高/最低点
        )
        print(f"   {sampling_info['message']}", flush=True)
        
        if ECHARTS_AVAILABLE:
            # 使用 ECharts (传入采样后的数据)
            chart_component = create_sales_trend_chart_echarts(sampled_daily_sales)
        else:
            # Plotly 备份 (使用采样数据)
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=sampled_daily_sales['日期'],
                y=sampled_daily_sales['销售额'],
                mode='lines+markers',
                name='销售额',
                line=dict(color='#1f77b4', width=2),
                fill='tozeroy',
                fillcolor='rgba(31,119,180,0.2)',
                yaxis='y1'
            ))
            fig_trend.add_trace(go.Scatter(
                x=sampled_daily_sales['日期'],
                y=sampled_daily_sales['总利润'],
                mode='lines+markers',
                name='总利润',
                line=dict(color='#2ca02c', width=2),
                yaxis='y1'
            ))
            fig_trend.add_trace(go.Scatter(
                x=sampled_daily_sales['日期'],
                y=sampled_daily_sales['订单数'],
                mode='lines+markers',
                name='订单数',
                line=dict(color='#ff7f0e', width=2),
                yaxis='y2'
            ))
            
            # 计算订单数的范围，优化右Y轴显示
            order_min = sampled_daily_sales['订单数'].min()
            order_max = sampled_daily_sales['订单数'].max()
            order_range = order_max - order_min
            order_axis_min = max(0, order_min - order_range * 0.2)
            order_axis_max = order_max + order_range * 0.2
            
            fig_trend.update_layout(
                title={
                    'text': f"📈 销售趋势分析 {create_data_info_badge(sampling_info).children if sampling_info['sampled'] else ''}",
                    'x': 0.5,
                    'xanchor': 'center'
                },
                xaxis_title='日期',
                yaxis=dict(title='金额 (¥)', side='left'),
                yaxis2=dict(
                    title='订单数', 
                    side='right', 
                    overlaying='y',
                    range=[order_axis_min, order_axis_max]  # 动态设置范围
                ),
                hovermode='x unified',
                height=400
            )
            chart_component = dcc.Graph(figure=fig_trend, config={'displayModeBar': False})
        
        # ========== 添加智能异常分析面板 ==========
        anomaly_analysis = analyze_daily_anomalies(df, daily_sales)
        
        # 调试输出
        print(f"🔍 异常分析结果: 异常天数={len(anomaly_analysis['anomaly_details'])}, 详情数量={len(anomaly_analysis.get('anomaly_details', []))}")
        if anomaly_analysis['anomaly_details']:
            print(f"   第一个异常日期: {anomaly_analysis['anomaly_details'][0]['日期']}")
        
        # 创建异常分析卡片
        anomaly_cards = []
        
        # 1. 概览卡片
        summary = anomaly_analysis['summary']
        best = anomaly_analysis['best_day']
        worst = anomaly_analysis['worst_day']
        
        anomaly_cards.append(
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("📊 利润率概览", className="card-title mb-3"),
                            html.Div([
                                html.P([
                                    html.Strong("平均利润率: "),
                                    html.Span(f"{summary['平均利润率']:.2f}%", className="text-primary")
                                ], className="mb-2"),
                                html.P([
                                    html.Strong("利润率波动: "),
                                    html.Span(f"±{summary['利润率标准差']:.2f}%", className="text-muted")
                                ], className="mb-2"),
                                html.P([
                                    html.Strong("异常天数: "),
                                    html.Span(
                                        f"{summary['异常天数']}/{summary['总天数']} 天", 
                                        className="text-danger" if summary['异常天数'] > summary['总天数'] * 0.3 else "text-warning"
                                    )
                                ], className="mb-0")
                            ])
                        ])
                    ], className="h-100")
                ], md=4),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("🏆 最佳表现日", className="card-title mb-3 text-success"),
                            html.Div([
                                html.P([
                                    html.Strong("日期: "),
                                    html.Span(best['日期'])
                                ], className="mb-2"),
                                html.P([
                                    html.Strong("利润率: "),
                                    html.Span(f"{best['利润率']:.2f}%", className="text-success fs-5")
                                ], className="mb-2"),
                                html.P([
                                    html.Strong("销售额: "),
                                    f"¥{best['销售额']:,.0f} ({best['订单数']:.0f}单)"
                                ], className="mb-0 small text-muted")
                            ])
                        ])
                    ], className="h-100 border-success")
                ], md=4),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("⚠️ 最差表现日", className="card-title mb-3 text-danger"),
                            html.Div([
                                html.P([
                                    html.Strong("日期: "),
                                    html.Span(worst['日期'])
                                ], className="mb-2"),
                                html.P([
                                    html.Strong("利润率: "),
                                    html.Span(f"{worst['利润率']:.2f}%", className="text-danger fs-5")
                                ], className="mb-2"),
                                html.P([
                                    html.Strong("销售额: "),
                                    f"¥{worst['销售额']:,.0f} ({worst['订单数']:.0f}单)"
                                ], className="mb-0 small text-muted")
                            ])
                        ])
                    ], className="h-100 border-danger")
                ], md=4)
            ], className="mb-4")
        )
        
        # 2. 异常日期详细分析
        if anomaly_analysis['anomaly_details']:
            print(f"📊 准备渲染 {len(anomaly_analysis['anomaly_details'])} 个异常日期的折叠面板...")
            anomaly_cards.append(
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("🔍 异常日期深度分析", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P("以下日期的利润率明显低于平均水平，需要重点关注：", className="text-muted mb-3"),
                        
                        # 为每个异常日期创建折叠面板
                        dbc.Accordion([
                            dbc.AccordionItem([
                                html.Div([
                                    # 基本指标
                                    dbc.Row([
                                        dbc.Col([
                                            html.Strong("📈 业绩指标:"),
                                            html.Ul([
                                                html.Li(f"销售额: ¥{detail['销售额']:,.0f}"),
                                                html.Li(f"总利润: ¥{detail['总利润']:,.0f}"),
                                                html.Li([
                                                    f"利润率: ",
                                                    html.Span(f"{detail['利润率']:.2f}%", className="text-danger fw-bold"),
                                                    f" (平均: {summary['平均利润率']:.2f}%)"
                                                ]),
                                                html.Li(f"订单数: {detail['订单数']:.0f}单")
                                            ])
                                        ], md=6),
                                        
                                        dbc.Col([
                                            html.Strong("💰 成本结构分析:"),
                                            html.Ul([
                                                html.Li([
                                                    f"配送成本率: ",
                                                    html.Span(
                                                        f"{detail['配送成本率']:.2f}%",
                                                        className="text-warning" if detail['配送成本率'] > 5 else "text-muted"
                                                    )
                                                ]),
                                                html.Li([
                                                    f"平台佣金率: ",
                                                    html.Span(f"{detail['佣金率']:.2f}%", className="text-muted")
                                                ]),
                                                html.Li([
                                                    f"活动成本率: ",
                                                    html.Span(
                                                        f"{detail['活动成本率']:.2f}%",
                                                        className="text-danger" if detail['活动成本率'] > 10 else "text-warning" if detail['活动成本率'] > 5 else "text-muted"
                                                    )
                                                ])
                                            ])
                                        ], md=6)
                                    ], className="mb-3"),
                                    
                                    # 问题商品分析
                                    html.Div([
                                        html.Strong("🎯 问题商品定位:"),
                                        html.Div([
                                            dbc.Alert([
                                                html.Strong(f"发现 {detail['问题商品数']} 个低利润率商品"),
                                                html.Br(),
                                                html.Small("这些商品销售额高但利润率低，拉低了整体盈利水平", className="text-muted")
                                            ], color="warning", className="mb-2") if detail['问题商品数'] > 0 else 
                                            dbc.Alert("未发现明显的问题商品", color="info", className="mb-2"),
                                            
                                            # 显示问题商品列表
                                            html.Div([
                                                dbc.Table([
                                                    html.Thead([
                                                        html.Tr([
                                                            html.Th("商品名称"),
                                                            html.Th("商品利润率"),
                                                            html.Th("销售额")
                                                        ])
                                                    ]),
                                                    html.Tbody([
                                                        html.Tr([
                                                            html.Td(prod['商品名称'][:30] + '...' if len(prod['商品名称']) > 30 else prod['商品名称']),
                                                            html.Td(f"{prod['商品利润率']:.2f}%", className="text-danger"),
                                                            html.Td(f"¥{prod['实收价格']:,.0f}")
                                                        ]) for prod in detail['问题商品'][:5]  # 只显示前5个
                                                    ])
                                                ], bordered=True, hover=True, size="sm")
                                            ]) if detail['问题商品'] else None
                                        ])
                                    ], className="mt-3"),
                                    
                                    # 诊断建议
                                    html.Div([
                                        html.Strong("💡 诊断建议:"),
                                        html.Ul([
                                            item for item in [
                                                html.Li("活动成本过高，建议优化促销策略") if detail['活动成本率'] > 10 else None,
                                                html.Li("配送成本偏高，考虑优化配送策略或调整起送价") if detail['配送成本率'] > 5 else None,
                                                html.Li(f"有{detail['问题商品数']}个商品利润率低，建议调整定价或减少促销") if detail['问题商品数'] > 0 else None,
                                                html.Li("整体成本结构合理，可能是偶发性波动") if detail['活动成本率'] < 10 and detail['配送成本率'] < 5 and detail['问题商品数'] == 0 else None
                                            ] if item is not None
                                        ])
                                    ], className="mt-3")
                                ])
                            ], title=f"📅 {detail['日期']} - 利润率 {detail['利润率']:.2f}% ({'低' if detail['利润率'] < summary['平均利润率'] - summary['利润率标准差'] else '偏低'})")
                            for detail in anomaly_analysis['anomaly_details'][:10]  # 最多显示10个异常日期
                        ], start_collapsed=True, always_open=False)
                    ])
                ], className="mb-4")
            )
        else:
            anomaly_cards.append(
                dbc.Alert([
                    html.H5("✅ 利润率表现稳定", className="alert-heading"),
                    html.P("未检测到明显的利润率异常，整体经营状况良好！")
                ], color="success", className="mb-4")
            )
        
        # 🆕 获取渠道列表(用于下拉菜单)
        channel_options = [{'label': '全部渠道', 'value': 'all'}]
        if '渠道' in df.columns:
            unique_channels = sorted([ch for ch in df['渠道'].dropna().unique() if ch])
            channel_options.extend([{'label': ch, 'value': ch} for ch in unique_channels])
        
        # 🆕 分析渠道健康度警示
        channel_warnings = analyze_channel_health_warnings(df, order_agg)
        
        # 🆕 创建带渠道筛选和警示的趋势图卡片
        charts.append(dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H4("📈 销售趋势分析", className="mb-0")
                    ], width=6),
                    dbc.Col([
                        # 🆕 渠道筛选下拉菜单
                        dcc.Dropdown(
                            id='sales-trend-channel-filter',
                            options=channel_options,
                            value='all',
                            placeholder='选择渠道',
                            clearable=False,
                            className="dash-bootstrap"
                        )
                    ], width=6)
                ], align="center")
            ]),
            dbc.CardBody([
                # 图表容器 (将通过callback动态更新)
                html.Div(id='sales-trend-chart-container', children=[chart_component]),
                
                # 🆕 渠道健康度警示卡片
                html.Div([
                    html.Hr(className="my-4"),
                    html.H5("⚠️ 渠道健康度警示", className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Alert([
                                html.Div([
                                    html.Strong([
                                        html.I(className="fas fa-exclamation-triangle me-2"),
                                        f"{warning['channel']}"
                                    ]),
                                    html.Br(),
                                    html.Small(warning['issue'], className="text-muted"),
                                    html.Br(),
                                    html.Small([
                                        f"均值: {warning['mean_rate']:.1f}% | ",
                                        f"波动: ±{warning['std_rate']:.1f}%"
                                    ], className="text-muted")
                                ])
                            ], color='danger' if warning['severity'] == 'high' else 'warning', className="mb-2")
                        ], md=6)
                        for warning in channel_warnings[:4]  # 最多显示4个警示
                    ]) if channel_warnings else dbc.Alert([
                        html.I(className="fas fa-check-circle me-2"),
                        "所有渠道利润率表现良好，未发现异常"
                    ], color="success")
                ]) if '渠道' in df.columns else None
            ])
        ], className="mb-4"))
        
        # 添加异常分析卡片
        charts.extend(anomaly_cards)
    
    # 2. 分类销售占比与趋势
    if '一级分类名' in df.columns:
        if ECHARTS_AVAILABLE:
            # 使用新的趋势图(柱状图+折线图组合)
            chart_component = create_category_trend_chart_echarts(df, order_agg)
        else:
            # Plotly 备份 - 保留原饼图 (✅ 使用实收价格)
            sales_field = '实收价格'
            category_sales = df.groupby('一级分类名')[sales_field].sum().sort_values(ascending=False)
            fig_category = go.Figure(data=[go.Pie(
                labels=category_sales.index,
                values=category_sales.values,
                hole=0.4,
                textinfo='label+percent',
                textposition='outside'
            )])
            fig_category.update_layout(
                title='🏷️ 商品分类销售占比',
                height=400
            )
            chart_component = dcc.Graph(figure=fig_category, config={'displayModeBar': False})
        
        charts.append(dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H5("🏷️ 一级分类销售趋势", className="mb-0")
                    ], width=4),
                    dbc.Col([
                        # 🆕 渠道筛选下拉菜单
                        dcc.Dropdown(
                            id='category-trend-channel-filter',
                            options=channel_options,
                            value='all',
                            placeholder='选择渠道',
                            clearable=False,
                            className="dash-bootstrap"
                        )
                    ], width=4),
                    dbc.Col([
                        dbc.Button(
                            "📥 导出数据",
                            id="export-category-trend-btn",
                            color="success",
                            size="sm",
                            className="float-end"
                        )
                    ], width=4)
                ], align="center")
            ]),
            dbc.CardBody([
                # 🆕 图表容器 (将通过callback动态更新)
                html.Div(id='category-trend-chart-container', children=[chart_component])
            ]),
            dcc.Download(id="download-category-trend-data")
        ], className="mb-4 shadow-sm"))
    
    # ==================== 4. 成本结构分析（使用订单级聚合，业务逻辑公式）====================
    
    # ✅ 计算总销售额（用于利润率）
    if '实收价格' in order_agg.columns:
        total_sales_for_rate = order_agg['实收价格'].sum()
    elif '订单总收入' in order_agg.columns:
        total_sales_for_rate = order_agg['订单总收入'].sum()
    else:
        total_sales_for_rate = order_agg['实收价格'].sum()
    
    # 使用订单聚合数据计算成本（避免重复）
    product_cost = order_agg['商品采购成本'].sum()
    delivery_cost = order_agg['配送净成本'].sum()
    marketing_cost = order_agg['商家活动成本'].sum()
    platform_service_fee_total = 0
    if '平台服务费' in order_agg.columns:
        platform_service_fee_total = order_agg['平台服务费'].sum()
    elif '平台佣金' in order_agg.columns:
        platform_service_fee_total = order_agg['平台佣金'].sum()
    
    # ========== 🔍 调试日志：成本结构计算 ==========
    print("\n" + "="*80)
    print("🔍 [调试] 成本结构分析")
    print(f"💰 商品成本: ¥{product_cost:,.2f}")
    print(f"🚚 配送净成本: ¥{delivery_cost:,.2f}")
    print(f"🎁 活动营销成本: ¥{marketing_cost:,.2f}")
    print(f"💳 平台服务费: ¥{platform_service_fee_total:,.2f}")
    print(f"\n🔍 成本详细检查:")
    print(f"   order_agg['商品采购成本'].fillna(0).sum() = ¥{order_agg['商品采购成本'].fillna(0).sum():,.2f}")
    print(f"   order_agg['配送净成本'].fillna(0).sum() = ¥{order_agg['配送净成本'].fillna(0).sum():,.2f}")
    print(f"   order_agg['商家活动成本'].fillna(0).sum() = ¥{order_agg['商家活动成本'].fillna(0).sum():,.2f}")
    platform_fee_column = '平台服务费' if '平台服务费' in order_agg.columns else '平台佣金'
    print(f"   order_agg['{platform_fee_column}'].fillna(0).sum() = ¥{order_agg[platform_fee_column].fillna(0).sum():,.2f}")
    print("="*80 + "\n")
    
    # 计算总成本用于仪表盘百分比
    total_cost = product_cost + delivery_cost + marketing_cost + platform_service_fee_total
    
    # 成本结构卡片 - 使用简洁HTML卡片
    cost_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("📦 商品成本", className="card-title text-muted"),
                    html.H3(f"¥{product_cost:,.2f}", className="text-primary"),
                    html.P("采购成本总额", className="text-muted small"),
                    dbc.Badge(f"{(product_cost/total_cost*100):.1f}%", color="primary", className="mt-1")
                ])
            ], className="modern-card text-center shadow-sm h-100")  # 🎨 添加modern-card
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("🚚 配送净成本", className="card-title text-muted"),
                    html.H3(f"¥{delivery_cost:,.2f}", className="text-warning"),
                    html.P("扣除用户支付后的净成本", className="text-muted small"),
                    dbc.Badge(f"{(delivery_cost/total_cost*100):.1f}%", color="warning", className="mt-1")
                ])
            ], className="modern-card text-center shadow-sm h-100")  # 🎨 添加modern-card
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("🎁 商家活动", className="card-title text-muted"),
                    html.H3(f"¥{marketing_cost:,.2f}", className="text-danger"),
                    html.P("促销活动支出", className="text-muted small"),
                    dbc.Badge(f"{(marketing_cost/total_cost*100):.1f}%", color="danger", className="mt-1")
                ])
            ], className="modern-card text-center shadow-sm h-100")  # 🎨 添加modern-card
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("💼 平台服务费", className="card-title text-muted"),
                    html.H3(f"¥{platform_service_fee_total:,.2f}", className="text-info"),
                    html.P("平台扣点/服务费", className="text-muted small"),
                    dbc.Badge(f"{(platform_service_fee_total/total_cost*100):.1f}%", color="info", className="mt-1")
                ])
            ], className="modern-card text-center shadow-sm h-100")  # 🎨 添加modern-card
        ], md=3)
    ], className="mb-4")
    
    # 成本结构饼图 - 统一使用 ECharts
    if ECHARTS_AVAILABLE:
        cost_structure_chart = DashECharts(
            option={
                'title': dict(COMMON_TITLE, text='💸 成本构成占比 [统一配置✅]'),
                'tooltip': dict(COMMON_TOOLTIP, trigger='item', formatter='{b}<br/>金额: ¥{c}<br/>占比: {d}%'),
                'legend': dict(COMMON_LEGEND, top='15%'),
                'series': [{
                    'name': '成本结构',
                    'type': 'pie',
                    'radius': ['40%', '70%'],
                    'center': ['50%', '60%'],
                    'data': [
                        {'value': round(product_cost, 2), 'name': '商品成本', 'itemStyle': {'color': COMMON_COLORS['blue'][2]}},
                        {'value': round(delivery_cost, 2), 'name': '配送净成本', 'itemStyle': {'color': COMMON_COLORS['orange'][2]}},
                        {'value': round(marketing_cost, 2), 'name': '商家活动', 'itemStyle': {'color': COMMON_COLORS['red'][2]}},
                        {'value': round(platform_service_fee_total, 2), 'name': '平台服务费', 'itemStyle': {'color': COMMON_COLORS['green'][2]}}
                    ],
                    'label': {
                        'show': True,
                        'formatter': '{b}\n¥{c}\n({d}%)',
                        'fontSize': 12,
                        'fontWeight': 'bold'
                    },
                    'labelLine': {'show': True, 'length': 15, 'length2': 10},
                    'emphasis': {
                        'itemStyle': {
                            'shadowBlur': 20,
                            'shadowColor': 'rgba(0, 0, 0, 0.3)'
                        }
                    },
                    **COMMON_ANIMATION
                }]
            },
            style={'height': '450px', 'width': '100%'}
        )
    else:
        # Plotly 后备方案
        cost_structure_chart = dcc.Graph(
            figure=go.Figure(data=[go.Pie(
                labels=['商品成本', '配送净成本', '商家活动', '平台服务费'],
                values=[product_cost, delivery_cost, marketing_cost, platform_service_fee_total],
                hole=0.4,
                textinfo='label+percent+value',
                texttemplate='%{label}<br>¥%{value:,.0f}<br>(%{percent})',
                marker=dict(colors=['#1f77b4', '#ff7f0e', '#d62728', '#2ca02c'])
            )]).update_layout(
                title='成本构成占比',
                height=450,
                showlegend=True
            ),
            config={'displayModeBar': False}
        )
    
    charts.append(dbc.Card([
        dbc.CardHeader(html.H4("💸 成本结构分析 (标准业务逻辑)", className="mb-0")),
        dbc.CardBody([
            cost_cards,
            # 成本占比饼图
            cost_structure_chart,
            
            # ========== 新增:商品成本分类分析 和 商家活动补贴分析 ==========
            html.Hr(className="my-4"),
            html.H5("📊 成本细分分析", className="mb-4 text-center", style={'color': '#2c3e50', 'fontWeight': 'bold', 'fontSize': '1.3rem'}),
            dbc.Row([
                # 左侧：商品成本分类分析
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H6("📦 商品成本分类排行", className="mb-0", style={'color': '#2E5C8A', 'fontWeight': 'bold'})
                        ], style={'background': 'linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%)', 'border': 'none', 'borderRadius': '12px 12px 0 0'}),
                        dbc.CardBody([
                            # 智能选择：ECharts 或 Plotly（函数内部已处理返回完整组件）
                            create_category_cost_chart(df)
                        ], style={'padding': '1.5rem', 'background': 'white'})
                    ], className="shadow-lg h-100", style={
                        'border': 'none',
                        'borderRadius': '12px',
                        'overflow': 'hidden',
                        'transition': 'transform 0.3s ease, box-shadow 0.3s ease'
                    })
                ], md=6, className="mb-4"),
                # 右侧：商家活动补贴分析
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H6("🎁 商家活动补贴分析", className="mb-0", style={'color': '#E74C3C', 'fontWeight': 'bold'})
                        ], style={'background': 'linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%)', 'border': 'none', 'borderRadius': '12px 12px 0 0'}),
                        dbc.CardBody([
                            # 智能选择：ECharts 或 Plotly（函数内部已处理返回完整组件）
                            create_marketing_activity_chart(order_agg)
                        ], style={'padding': '1.5rem', 'background': 'white'})
                    ], className="shadow-lg h-100", style={
                        'border': 'none',
                        'borderRadius': '12px',
                        'overflow': 'hidden',
                        'transition': 'transform 0.3s ease, box-shadow 0.3s ease'
                    })
                ], md=6, className="mb-4")
            ], className="g-4")  # 增大栅格间距
        ])
    ], className="mb-4"))
    
    # ==================== 5. 利润率详细分析（使用订单聚合数据）====================
    
    # ✅ 计算利润率（使用实收价格作为分母）
    if '实收价格' in order_agg.columns:
        profit_rate = (total_profit / order_agg['实收价格'].sum() * 100) if order_agg['实收价格'].sum() > 0 else 0
    else:
        profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
    
    # 使用订单聚合数据
    profit_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("💎 总利润额", className="card-title text-muted"),
                    html.H3(f"¥{total_profit:,.2f}", className="text-success"),
                    html.P("订单实际利润总和", className="text-muted small")
                ])
            ], className="modern-card text-center shadow-sm")  # 🎨 添加modern-card
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("📊 利润率", className="card-title text-muted"),
                    html.H3(f"{profit_rate:.2f}%", className="text-warning"),
                    html.P("利润/销售额", className="text-muted small")
                ])
            ], className="modern-card text-center shadow-sm")  # 🎨 添加modern-card
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("📈 盈利订单数", className="card-title text-muted"),
                    html.H3(f"{profitable_orders:,}", className="text-info"),
                    html.P(f"占比 {profitable_rate:.1f}%", className="text-muted small")
                ])
            ], className="modern-card text-center shadow-sm")  # 🎨 添加modern-card
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("💰 平均订单利润", className="card-title text-muted"),
                    html.H3(f"¥{total_profit/total_orders:.2f}", className="text-primary"),
                    html.P("总利润/订单数", className="text-muted small")
                ])
            ], className="modern-card text-center shadow-sm")  # 🎨 添加modern-card
        ], md=3)
    ], className="mb-4")
    
    charts.append(dbc.Card([
        dbc.CardHeader(html.H4("💰 利润率详细分析 (标准业务逻辑)", className="mb-0")),
        dbc.CardBody([
            profit_cards,
            # 利润区间分布图 - 智能选择（函数内部已处理 ECharts/Plotly 切换）
            create_profit_range_chart(order_agg) if order_agg is not None and len(order_agg) > 0 else html.Div(
                dbc.Alert("暂无订单利润数据", color="info"),
                style={'padding': '2rem', 'textAlign': 'center'}
            )
        ])
    ], className="mb-4"))
    
    # ==================== 6. 业务逻辑说明（基于实际代码逻辑）====================
    business_logic_explanation = dbc.Card([
        dbc.CardHeader(html.H5("📄 Tab1 核心业务逻辑说明", className="mb-0")),
        dbc.CardBody([
            html.H6("📐 计算口径配置", className="text-primary mb-2"),
            html.P([
                "系统支持三种计算口径，影响利润额与配送净成本的统计范围：",
                html.Br(),
                html.Small([
                    html.Strong("• 仅平台服务费>0（默认）："), 
                    "只统计已上报平台服务费的订单，会过滤闪购小程序等",
                    html.Br(),
                    html.Strong("• 全量（仅平台服务费）："), 
                    "保留所有订单，但不使用佣金兜底",
                    html.Br(),
                    html.Strong("• 全量（服务费+佣金兜底）："), 
                    "保留所有订单，服务费≤0时用佣金替代（环比计算使用）"
                ], className="text-muted")
            ], className="mb-3"),
            
            html.Hr(),
            html.H6("💰 核心计算公式 (全局唯一)", className="text-primary mb-2"),
            html.Ol([
                html.Li([
                    html.Strong("订单实际利润 = "),
                    "利润额 - 平台服务费 - 物流配送费 + 企客后返",
                    html.Br(),
                    html.Small([
                        "• 利润额：来自Excel数据，已包含商品成本扣减",
                        html.Br(),
                        "• 平台服务费：根据计算口径可能用佣金兜底",
                        html.Br(),
                        "• 物流配送费：订单级原始值，不剔除任何配送平台"
                    ], className="text-muted")
                ], className="mb-2"),
                html.Li([
                    html.Strong("配送净成本 = "),
                    "物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返",
                    html.Br(),
                    html.Small("体现平台真实承担的配送支出", className="text-muted")
                ], className="mb-2"),
                html.Li([
                    html.Strong("客单价 = "),
                    "实收价格 / 订单数",
                    html.Br(),
                    html.Small("使用用户实际支付金额，不是商品原价", className="text-muted")
                ], className="mb-2"),
                html.Li([
                    html.Strong("利润率 = "),
                    "订单实际利润 / 实收价格 × 100%",
                    html.Br(),
                    html.Small([
                        "• 实收价格：订单总收入（已修复：实收价格×销量后聚合）",
                        html.Br(),
                        "• 订单实际利润：扣除所有成本后的净利润"
                    ], className="text-muted")
                ], className="mb-2"),
                html.Li([
                    html.Strong("商家活动成本 = "),
                    "满减金额 + 商品减免金额 + 商家代金券 + 商家承担部分券 + 满赠金额 + 商家其他优惠"
                ], className="mb-2")
            ], className="mb-3"),
            
            html.Hr(),
            html.H6("📊 订单聚合规则", className="text-primary mb-2"),
            html.P([
                html.Strong("订单级字段（使用first）："),
                html.Br(),
                html.Small("用户支付配送费、配送费减免金额、物流配送费、平台佣金、满减金额、渠道等", className="text-muted"),
                html.Br(),
                html.Strong("商品级字段（使用sum）："),
                html.Br(),
                html.Small("商品实售价、预计订单收入、实收价格、利润额、企客后返、商品采购成本等", className="text-muted")
            ], className="mb-3"),
            
            html.Hr(),
            html.H6("🔄 环比计算逻辑", className="text-primary mb-2"),
            html.P([
                "• 单日查询：对比前一天数据",
                html.Br(),
                "• 多日查询：对比相同天数的前一周期",
                html.Br(),
                "• ",
                html.Strong("强制使用全量（服务费+佣金兜底）模式", className="text-danger"),
                "，确保包含闪购小程序等所有订单",
                html.Br(),
                html.Small("环比指标：订单数、销售额、总利润、客单价、利润率（百分点差值）", className="text-muted")
            ], className="mb-3"),
            
            html.Hr(),
            html.H6("🏪 渠道处理规则", className="text-primary mb-2"),
            html.P([
                html.Strong("自动排除渠道："),
                " 饿了么咖啡、美团咖啡",
                html.Br(),
                html.Strong("包含渠道："),
                " 美团闪购、饿了么、京东到家、闪购小程序",
                html.Br(),
                html.Small("注：闪购小程序平台服务费=0，需使用全量模式才能包含", className="text-muted")
            ], className="mb-3"),
            
            html.Hr(),
            html.Small([
                "📌 提示：所有利润计算使用",
                html.Strong(" 全局唯一公式 "),
                "（_calculate_profit_formula函数），修改时需谨慎。详细说明请参阅",
                html.Code(" Tab1业务逻辑说明文档.md")
            ], className="text-muted")
        ])
    ], className="mb-4")
    
    charts.append(business_logic_explanation)
    
    return html.Div(charts), {'display': 'block'}


# 🆕 Tab 1: 销售趋势渠道筛选callback
@app.callback(
    Output('sales-trend-chart-container', 'children'),
    Input('sales-trend-channel-filter', 'value'),
    prevent_initial_call=False
)
def update_sales_trend_by_channel(selected_channel):
    """根据渠道筛选更新销售趋势图"""
    try:
        # 🔧 处理None值
        if selected_channel is None:
            selected_channel = 'all'
        
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return dbc.Alert("⚠️ 数据不可用", color="warning")
        
        df = GLOBAL_DATA.copy()
        
        # 使用统一的订单聚合函数
        # 🔧 销售趋势分析：使用all_with_fallback模式，保留所有订单（包括平台费用为0的订单，如闪购小程序）
        order_agg = calculate_order_metrics(df, calc_mode='all_with_fallback')
        
        # 🆕 使用新函数计算带利润率的日度数据
        daily_sales, channel_available = calculate_daily_sales_with_channel(
            df, order_agg, selected_channel
        )
        
        # 🔍 调试日志
        print(f"\n🔍 [销售趋势-渠道筛选] 渠道='{selected_channel}', 数据行数={len(daily_sales)}")
        if not daily_sales.empty:
            print(f"   订单数: {daily_sales['订单数'].sum()}")
            print(f"   日期范围: {daily_sales['日期'].min()} ~ {daily_sales['日期'].max()}")
        
        if daily_sales.empty:
            # 🆕 优化提示信息,显示可用渠道
            available_channels = []
            if '渠道' in df.columns:
                available_channels = sorted(df['渠道'].dropna().unique())
            
            msg = f"⚠️ 渠道 '{selected_channel}' 暂无数据"
            if available_channels:
                msg += f"\n\n可用渠道: {', '.join(available_channels)}"
            
            return dbc.Alert(msg, color="info", style={'whiteSpace': 'pre-wrap'})
        
        # 数据采样优化
        sampled_daily_sales, sampling_info = downsample_data_for_chart(
            daily_sales,
            max_points=500,
            sort_column='日期',
            keep_extremes=True
        )
        
        # 生成图表
        if ECHARTS_AVAILABLE:
            return create_sales_trend_chart_echarts(sampled_daily_sales)
        else:
            # Plotly备份
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=sampled_daily_sales['日期'],
                y=sampled_daily_sales['销售额'],
                mode='lines+markers',
                name='销售额',
                line=dict(color='#1f77b4', width=2),
                fill='tozeroy',
                fillcolor='rgba(31,119,180,0.2)'
            ))
            fig_trend.add_trace(go.Scatter(
                x=sampled_daily_sales['日期'],
                y=sampled_daily_sales['总利润'],
                mode='lines+markers',
                name='总利润',
                line=dict(color='#2ca02c', width=2)
            ))
            
            # 🆕 添加利润率曲线
            if '利润率' in sampled_daily_sales.columns:
                fig_trend.add_trace(go.Scatter(
                    x=sampled_daily_sales['日期'],
                    y=sampled_daily_sales['利润率'],
                    mode='lines+markers',
                    name='利润率',
                    line=dict(color='#ff7f0e', width=2, dash='dash'),
                    yaxis='y2'
                ))
            
            fig_trend.update_layout(
                title=f"📈 销售趋势分析 - {selected_channel if selected_channel != 'all' else '全部渠道'}",
                xaxis_title='日期',
                yaxis=dict(title='金额 (¥)', side='left'),
                yaxis2=dict(title='利润率 (%)', side='right', overlaying='y', range=[0, 100]),
                hovermode='x unified',
                height=450
            )
            return dcc.Graph(figure=fig_trend, config={'displayModeBar': False})
    
    except Exception as e:
        print(f"❌ [update_sales_trend_by_channel] 错误: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"图表更新失败: {str(e)}", color="danger")


# 🆕 Tab 1: 分类趋势渠道筛选callback
@app.callback(
    Output('category-trend-chart-container', 'children'),
    Input('category-trend-channel-filter', 'value'),
    prevent_initial_call=False
)
def update_category_trend_by_channel(selected_channel):
    """根据渠道筛选更新一级分类销售趋势图"""
    try:
        # 🔧 处理None值
        if selected_channel is None:
            selected_channel = 'all'
        
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return dbc.Alert("⚠️ 数据不可用", color="warning")
        
        df = GLOBAL_DATA.copy()
        
        # 检查是否有一级分类字段
        if '一级分类名' not in df.columns:
            return dbc.Alert("⚠️ 数据中缺少【一级分类名】字段", color="warning")
        
        # 🔧 使用all_with_fallback模式,保留所有订单(包括闪购小程序)
        order_agg = calculate_order_metrics(df, calc_mode='all_with_fallback')
        
        # 🔍 调试日志
        print(f"\n🔍 [分类趋势-渠道筛选] 渠道='{selected_channel}', 订单数={len(order_agg)}")
        if '渠道' in order_agg.columns:
            print(f"   渠道分布: {order_agg['渠道'].value_counts().to_dict()}")
        
        # 调用修改后的图表生成函数,传入selected_channel参数
        if ECHARTS_AVAILABLE:
            return create_category_trend_chart_echarts(df, order_agg, selected_channel)
        else:
            # Plotly备份 - 简单饼图
            # 先筛选渠道
            if selected_channel != 'all' and '渠道' in df.columns:
                df_filtered = df[df['渠道'] == selected_channel].copy()
                if len(df_filtered) == 0:
                    available_channels = sorted(df['渠道'].dropna().unique())
                    msg = f"⚠️ 渠道 '{selected_channel}' 暂无数据\n\n可用渠道: {', '.join(available_channels)}"
                    return dbc.Alert(msg, color="info", style={'whiteSpace': 'pre-wrap'})
            else:
                df_filtered = df
            
            # 按分类聚合销售额
            # ⚠️ 关键修复：实收价格是单价，需要先乘以销量
            sales_col = '月售' if '月售' in df_filtered.columns else '销量'
            if sales_col in df_filtered.columns:
                df_filtered_temp = df_filtered.copy()
                df_filtered_temp['订单总收入'] = df_filtered_temp['实收价格'] * df_filtered_temp[sales_col]
                category_sales = df_filtered_temp.groupby('一级分类名')['订单总收入'].sum().sort_values(ascending=False)
                print(f"🔧 [分类销售占比] 实收价格修复: 使用(实收价格×{sales_col})聚合")
            else:
                category_sales = df_filtered.groupby('一级分类名')['实收价格'].sum().sort_values(ascending=False)
                print(f"⚠️ [分类销售占比] 实收价格兜底: 直接sum（缺少销量字段）")
            
            fig_category = go.Figure(data=[go.Pie(
                labels=category_sales.index,
                values=category_sales.values,
                hole=0.4,
                textinfo='label+percent',
                textposition='outside'
            )])
            fig_category.update_layout(
                title=f'🏷️ 商品分类销售占比 - {selected_channel if selected_channel != "all" else "全部渠道"}',
                height=400
            )
            return dcc.Graph(figure=fig_category, config={'displayModeBar': False})
    
    except Exception as e:
        print(f"❌ [update_category_trend_by_channel] 错误: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"图表更新失败: {str(e)}", color="danger")


# 🆕 Tab 1: 客单价分析渠道下拉框选项初始化
@app.callback(
    Output('aov-analysis-channel-filter', 'options'),
    Input('aov-channel-options-store', 'data'),
    prevent_initial_call=False
)
def update_aov_channel_options(channel_options):
    """从Store初始化客单价分析的渠道下拉框选项"""
    if channel_options:
        return channel_options
    return [{'label': '全部渠道', 'value': 'all'}]


# 🆕 Tab 1: 客单价分析渠道筛选callback
@app.callback(
    Output('aov-analysis-content-container', 'children'),
    Input('aov-analysis-channel-filter', 'value'),
    [State('cached-order-agg', 'data'),
     State('cache-version', 'data')],
    prevent_initial_call=False  # 🔧 允许初始调用
)
def update_aov_analysis_by_channel(selected_channel, cached_agg, cache_version):
    """根据渠道筛选更新客单价分析"""
    try:
        # 🔧 处理None值
        if selected_channel is None:
            selected_channel = 'all'
        
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return dbc.Alert("⚠️ 数据不可用", color="warning")
        
        df = GLOBAL_DATA.copy()
        
        # 从缓存或重新计算订单聚合数据
        # 🔧 使用all_with_fallback模式,保留所有订单(包括闪购小程序)
        if cached_agg is not None:
            order_agg = pd.DataFrame(cached_agg)
            # 检查缓存是否包含必要字段
            if '配送净成本' not in order_agg.columns or '订单总收入' not in order_agg.columns:
                print(f"⚠️ [客单价-渠道筛选] 缓存数据缺少关键字段,重新计算...")
                order_agg = calculate_order_metrics(df, calc_mode='all_with_fallback')
        else:
            order_agg = calculate_order_metrics(df, calc_mode='all_with_fallback')
        
        # 🔍 调试日志
        print(f"\n🔍 [客单价-渠道筛选] 渠道='{selected_channel}', 订单数={len(order_agg)}")
        if '渠道' in order_agg.columns:
            print(f"   渠道分布: {order_agg['渠道'].value_counts().to_dict()}")
        
        # 调用修改后的分析函数,传入selected_channel参数
        return _create_aov_analysis(df, order_agg, selected_channel)
    
    except Exception as e:
        print(f"❌ [update_aov_analysis_by_channel] 错误: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"客单价分析更新失败: {str(e)}", color="danger")


# ==================== Tab 2: 商品分析（完整功能）====================

def generate_quadrant_scatter_chart(product_agg, profit_threshold, sales_threshold):
    """生成四象限散点图"""
    try:
        print("\n🎨 [生成四象限散点图] 开始...")
        print(f"   商品总数: {len(product_agg)}")
        print(f"   利润率范围: {product_agg['利润率'].min():.2f} ~ {product_agg['利润率'].max():.2f}")
        print(f"   动销指数范围: {product_agg['动销指数'].min():.3f} ~ {product_agg['动销指数'].max():.3f}")
        print(f"   销售额范围: {product_agg['销售额'].min():.0f} ~ {product_agg['销售额'].max():.0f}")
        
        # 按象限分组准备数据
        quadrant_colors = {
            '🌟 高利润高动销': '#28a745',
            '⚠️ 高利润低动销': '#ffc107',
            '🚀 低利润高动销': '#17a2b8',
            '❌ 低利润低动销': '#dc3545'
        }
        
        # 为每个象限创建一个系列
        series_list = []
        for quadrant, color in quadrant_colors.items():
            df_quadrant = product_agg[product_agg['象限分类'] == quadrant]
            if len(df_quadrant) > 0:
                scatter_data = []
                for _, row in df_quadrant.iterrows():
                    # ✅ 跳过无效数据和极端值
                    # 1. 检查是否为有限数值
                    # 2. 销售额必须>0
                    # 3. 利润率在合理范围内（-100% ~ 200%）
                    if (
                        np.isfinite(row['动销指数']) and 
                        np.isfinite(row['利润率']) and 
                        np.isfinite(row['销售额']) and
                        row['销售额'] > 0 and
                        -100 <= row['利润率'] <= 200  # ✅ 过滤极端利润率
                    ):
                        # ✅ 构建包含健康度信息的数据点
                        health_status = row.get('盈利健康度', '未知')
                        profit_order_ratio = row.get('盈利订单占比', 0)
                        
                        scatter_data.append({
                            'name': f"{row['商品名称']}\n{health_status} ({profit_order_ratio:.0f}%订单盈利)",
                            'value': [
                                round(float(row['动销指数']), 3),
                                round(float(row['利润率']), 2),
                                round(float(row['销售额']), 0),
                                round(float(profit_order_ratio), 1)  # 第4个值：盈利订单占比
                            ],
                            'itemStyle': {
                                'borderWidth': 2 if health_status == '🔴 依赖大单' else 0,
                                'borderColor': '#ff0000' if health_status == '🔴 依赖大单' else None
                            }
                        })
                
                print(f"   {quadrant}: {len(scatter_data)} 个有效商品 (原始: {len(df_quadrant)}个)")
                if len(scatter_data) > 0:
                    print(f"      样例数据: {scatter_data[0]}")
                
                # ✅ 只有当有数据时才添加series
                if len(scatter_data) > 0:
                    series_list.append({
                        'name': quadrant,
                        'type': 'scatter',
                        'data': scatter_data,
                        'symbolSize': 15,  # ✅ 临时使用固定大小测试
                        'itemStyle': {'color': color},
                        'emphasis': {
                            'focus': 'series',
                            'label': {
                                'show': True,
                                'formatter': '{b}',
                                'position': 'top'
                            }
                        }
                    })
        
        if not ECHARTS_AVAILABLE or len(series_list) == 0:
            print(f"   ⚠️ 无法生成图表: ECHARTS_AVAILABLE={ECHARTS_AVAILABLE}, series数量={len(series_list)}")
            return html.Div("暂无数据或ECharts不可用")
        
        print(f"   ✅ 成功生成 {len(series_list)} 个系列")
        print(f"   📊 每个系列的数据点数量: {[len(s['data']) for s in series_list]}")
        if len(series_list) > 0 and len(series_list[0]['data']) > 0:
            print(f"   🔍 第一个系列的前3个数据点:")
            for i, point in enumerate(series_list[0]['data'][:3]):
                print(f"      [{i}] {point}")
        
        # 添加阈值线到第一个系列
        if len(series_list) > 0:
            series_list[0]['markLine'] = {
                'silent': True,
                'lineStyle': {
                    'color': '#999',
                    'type': 'solid',
                    'width': 2
                },
                'data': [
                    {'xAxis': sales_threshold, 'label': {'formatter': '动销阈值', 'position': 'end'}},
                    {'yAxis': profit_threshold, 'label': {'formatter': '利润阈值', 'position': 'end'}}
                ]
            }
        
        option = {
            'title': {
                'text': '商品四象限分布图',
                'subtext': f'利润率阈值: {profit_threshold}% | 动销指数阈值: {sales_threshold:.3f}',
                'left': 'center'
            },
            'legend': {
                'data': list(quadrant_colors.keys()),
                'top': '8%',
                'left': 'center'
            },
            'tooltip': {
                'trigger': 'item',
                'backgroundColor': 'rgba(255,255,255,0.95)',
                'borderColor': '#ccc',
                'textStyle': {'color': '#333'},
                'confine': True,
                'formatter': "{b}<br/>动销指数: {c0}<br/>利润率: {c1}%<br/>销售额: ¥{c2}"
            },
            'grid': {
                'left': '10%',
                'right': '10%',
                'top': '18%',
                'bottom': '10%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'value',
                'name': '动销指数',
                'nameLocation': 'middle',
                'nameGap': 30,
                'splitLine': {'show': True, 'lineStyle': {'type': 'dashed'}},
                'axisLine': {'onZero': False}
            },
            'yAxis': {
                'type': 'value',
                'name': '利润率 (%)',
                'nameLocation': 'middle',
                'nameGap': 50,
                'splitLine': {'show': True, 'lineStyle': {'type': 'dashed'}},
                'axisLine': {'onZero': False}
            },
            'series': series_list
        }
        
        return html.Div([
            html.H5('四象限可视化分布', className="text-center mb-3"),
            DashECharts(
                id='quadrant-scatter-echart',  # ✅ 添加ID便于调试
                option=option,
                style={'height': '500px', 'width': '100%'}
            )
        ])
        
    except Exception as e:
        print(f"❌ [生成四象限散点图] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"图表生成错误: {e}")


def calculate_time_period_quadrants(df, period='week', profit_threshold=30.0, start_date=None, end_date=None):
    """
    计算不同时间周期的四象限分类
    
    Parameters:
    -----------
    df : DataFrame
        原始数据,需包含日期、商品名称等字段
    period : str
        时间周期: 'day'(日) / 'week'(自然周) / 'month'(月)
    profit_threshold : float
        利润率阈值
    start_date : str or datetime, optional
        开始日期,用于筛选数据范围
    end_date : str or datetime, optional
        结束日期,用于筛选数据范围
        
    Returns:
    --------
    dict : {
        'periods': [周期列表],
        'period_label': '周期单位',
        'quadrant_data': {商品名称: [各周期的象限分类]},
        'trend_alerts': [预警商品列表]
    }
    """
    try:
        # 确保日期字段存在
        if '日期' not in df.columns:
            return None
        
        # 转换日期格式
        df = df.copy()
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        
        # 日期范围筛选
        if start_date is not None:
            start_date = pd.to_datetime(start_date)
            df = df[df['日期'] >= start_date]
        if end_date is not None:
            end_date = pd.to_datetime(end_date)
            df = df[df['日期'] <= end_date]
        
        if len(df) == 0:
            return None
        
        # 按周期分组
        if period == 'day':
            # 按日统计 - 直接使用日期作为周期
            df['周期'] = df['日期'].dt.strftime('%Y-%m-%d')
            period_label = '日'
        elif period == 'week':
            # 按自然周统计 - 计算从周一开始的自然周
            df['周期'] = df['日期'].dt.to_period('W-MON').astype(str)
            period_label = '周'
        elif period == 'month':
            df['周期'] = df['日期'].dt.to_period('M').astype(str)
            period_label = '月'
        else:
            return None
        
        periods = sorted(df['周期'].unique())
        
        # 为每个周期计算四象限
        period_quadrants = {}
        
        for p in periods:
            period_df = df[df['周期'] == p].copy()
            
            # 商品聚合(简化版,只计算关键指标)
            product_agg = period_df.groupby('商品名称').agg({
                '预计订单收入': 'sum',
                '实收价格': 'sum' if '实收价格' in period_df.columns else lambda x: period_df['预计订单收入'].sum(),
                '利润额': 'sum',
                '月售': 'sum',
                '库存': 'last',
                '订单ID': 'nunique'
            }).reset_index()
            
            product_agg.columns = ['商品名称', '销售额', '实收价格_sum', '实际利润', '总销量', '库存', '订单数']
            
            # 计算利润率
            if '实收价格' in period_df.columns:
                product_agg['利润率'] = (product_agg['实际利润'] / product_agg['实收价格_sum'].replace(0, np.nan) * 100).fillna(0).replace([np.inf, -np.inf], 0)
            else:
                product_agg['利润率'] = (product_agg['实际利润'] / product_agg['销售额'].replace(0, np.nan) * 100).fillna(0).replace([np.inf, -np.inf], 0)
            
            # 计算周转率
            product_agg['库存周转率'] = (product_agg['总销量'] / product_agg['库存'].replace(0, np.nan)).fillna(0).replace([np.inf, -np.inf], 0)
            
            # 标准化动销指数
            min_sales = product_agg['总销量'].min()
            max_sales = product_agg['总销量'].max()
            min_turnover = product_agg['库存周转率'].min()
            max_turnover = product_agg['库存周转率'].max()
            min_orders = product_agg['订单数'].min()
            max_orders = product_agg['订单数'].max()
            
            sales_range = max_sales - min_sales if max_sales > min_sales else 1
            turnover_range = max_turnover - min_turnover if max_turnover > min_turnover else 1
            orders_range = max_orders - min_orders if max_orders > min_orders else 1
            
            product_agg['标准化销量'] = (product_agg['总销量'] - min_sales) / sales_range
            product_agg['标准化周转率'] = (product_agg['库存周转率'] - min_turnover) / turnover_range
            product_agg['标准化订单数'] = (product_agg['订单数'] - min_orders) / orders_range
            
            product_agg['动销指数'] = (
                0.5 * product_agg['标准化销量'] + 
                0.3 * product_agg['标准化周转率'] + 
                0.2 * product_agg['标准化订单数']
            )
            
            # 四象限判定
            sales_threshold = product_agg['动销指数'].median()
            
            def classify_quadrant(row):
                high_profit = row['利润率'] > profit_threshold
                high_sales = row['动销指数'] > sales_threshold
                
                if high_profit and high_sales:
                    return '🌟 高利润高动销'
                elif high_profit and not high_sales:
                    return '⚠️ 高利润低动销'
                elif not high_profit and high_sales:
                    return '🚀 低利润高动销'
                else:
                    return '❌ 低利润低动销'
            
            product_agg['象限'] = product_agg.apply(classify_quadrant, axis=1)
            
            # 保存到字典
            period_quadrants[p] = product_agg[['商品名称', '象限', '销售额', '实际利润', '利润率', '动销指数']].set_index('商品名称')['象限'].to_dict()
        
        # 重构数据: 商品 -> [各周期象限]
        all_products = set()
        for p_data in period_quadrants.values():
            all_products.update(p_data.keys())
        
        quadrant_data = {}
        for product in all_products:
            quadrant_data[product] = [period_quadrants[p].get(product, '无数据') for p in periods]
        
        # 分析趋势预警
        trend_alerts = analyze_quadrant_trends(quadrant_data, periods)
        
        return {
            'periods': periods,
            'period_label': period_label,
            'quadrant_data': quadrant_data,
            'trend_alerts': trend_alerts
        }
        
    except Exception as e:
        print(f"❌ [时间维度四象限计算] 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_quadrant_trends(quadrant_data, periods):
    """
    分析商品的象限迁移趋势，识别需要预警的商品
    
    Returns:
    --------
    list of dict: [
        {
            'product': 商品名称,
            'trend': 趋势描述,
            'alert_level': 'critical'/'warning'/'info',
            'from_quadrant': 起始象限,
            'to_quadrant': 当前象限,
            'recommendation': 建议
        }
    ]
    """
    alerts = []
    
    # 象限优先级(越小越好)
    quadrant_priority = {
        '🌟 高利润高动销': 1,
        '⚠️ 高利润低动销': 2,
        '🚀 低利润高动销': 3,
        '❌ 低利润低动销': 4,
        '无数据': 5
    }
    
    for product, quadrant_list in quadrant_data.items():
        if len(quadrant_list) < 2:
            continue
        
        # 过滤无数据
        valid_quadrants = [q for q in quadrant_list if q != '无数据']
        if len(valid_quadrants) < 2:
            continue
        
        first_quadrant = valid_quadrants[0]
        last_quadrant = valid_quadrants[-1]
        
        # 计算趋势
        first_priority = quadrant_priority.get(first_quadrant, 5)
        last_priority = quadrant_priority.get(last_quadrant, 5)
        
        if first_priority < last_priority:
            # 恶化趋势
            trend_desc = f"{first_quadrant} → {last_quadrant}"
            
            if first_priority == 1 and last_priority == 4:
                # 明星 → 淘汰 (最严重)
                alert_level = 'critical'
                recommendation = "🚨 紧急处理: 曾是明星产品,现已沦为淘汰品,需立即调查原因!"
            elif first_priority == 1:
                # 明星下滑
                alert_level = 'critical'
                recommendation = "⚠️ 重点关注: 明星产品表现下滑,建议检查库存、定价、竞品"
            elif last_priority == 4:
                # 滑向淘汰
                alert_level = 'warning'
                recommendation = "📉 考虑清仓: 产品持续恶化,可能需要下架或促销清仓"
            else:
                alert_level = 'warning'
                recommendation = "💡 需要优化: 产品表现下滑,建议调整策略"
            
            alerts.append({
                'product': product,
                'trend': trend_desc,
                'alert_level': alert_level,
                'from_quadrant': first_quadrant,
                'to_quadrant': last_quadrant,
                'recommendation': recommendation
            })
        
        elif first_priority > last_priority and last_priority <= 2:
            # 改善趋势(且当前表现不错)
            trend_desc = f"{first_quadrant} → {last_quadrant}"
            alert_level = 'info'
            recommendation = "✅ 持续优化: 产品表现改善,保持当前策略"
            
            alerts.append({
                'product': product,
                'trend': trend_desc,
                'alert_level': alert_level,
                'from_quadrant': first_quadrant,
                'to_quadrant': last_quadrant,
                'recommendation': recommendation
            })
    
    # 按严重程度排序
    alert_priority = {'critical': 1, 'warning': 2, 'info': 3}
    alerts.sort(key=lambda x: alert_priority.get(x['alert_level'], 99))
    
    return alerts


def create_category_trend_chart(df, periods, period_label, quadrant_data, view_mode='all'):
    """创建一级分类趋势图 - 支持切换查看不同象限
    
    Args:
        view_mode: 'all'(全部堆叠) / 'star'(明星) / 'problem'(问题) / 'traffic'(引流) / 'eliminate'(淘汰)
    """
    try:
        print(f"\n📈 [分类趋势图] 开始生成... (视图模式: {view_mode})")
        
        # 判断是按日还是按周
        is_daily = '日' in period_label or 'Day' in period_label
        
        # 获取商品的分类信息
        product_category = df[['商品名称', '一级分类名']].drop_duplicates().set_index('商品名称')['一级分类名'].to_dict()
        
        # 按分类统计每个周期的象限分布
        category_trends = {}
        
        for product, quadrants in quadrant_data.items():
            category = product_category.get(product, '未分类')
            if category not in category_trends:
                category_trends[category] = {
                    '🌟 高利润高动销': [0] * len(periods),
                    '⚠️ 高利润低动销': [0] * len(periods),
                    '🚀 低利润高动销': [0] * len(periods),
                    '❌ 低利润低动销': [0] * len(periods)
                }
            
            for i, q in enumerate(quadrants):
                if q and q != '无数据':
                    category_trends[category][q][i] += 1
        
        # 选择TOP 5分类(按商品总数)
        top_categories = sorted(
            category_trends.items(),
            key=lambda x: sum(sum(counts) for counts in x[1].values()),
            reverse=True
        )[:5]
        
        print(f"   📊 TOP5分类: {[cat[0] for cat in top_categories]}")
        
        # 生成折线图 (ECharts)
        if not ECHARTS_AVAILABLE:
            return html.Div()
        
        # X轴标签：按日显示日期，按周/月显示序号
        if is_daily:
            # periods已经是字符串格式 '2025-09-01',转换显示为 '09-01'
            x_labels = [pd.to_datetime(p).strftime('%m-%d') if isinstance(p, str) else p.strftime('%m-%d') for p in periods]
        else:
            x_labels = [f'第{i+1}{period_label}' for i in range(len(periods))]  # 例如: 第1周, 第2周
        
        # 准备数据 - 根据视图模式生成不同的系列
        series_data = []
        
        # 象限配置
        quadrant_config = {
            'star': ('🌟 高利润高动销', '#52c41a', '明星商品'),
            'problem': ('⚠️ 高利润低动销', '#faad14', '问题商品'),
            'traffic': ('🚀 低利润高动销', '#1890ff', '引流商品'),
            'eliminate': ('❌ 低利润低动销', '#f5222d', '淘汰商品')
        }
        
        if view_mode == 'all':
            # 全部堆叠模式
            quadrant_info = [
                ('🌟 高利润高动销', '#52c41a', '明星'),
                ('⚠️ 高利润低动销', '#faad14', '问题'),
                ('🚀 低利润高动销', '#1890ff', '引流'),
                ('❌ 低利润低动销', '#f5222d', '淘汰')
            ]
            
            for quadrant_full, color, quadrant_short in quadrant_info:
                for category, quadrants_dict in top_categories:
                    series_data.append({
                        'name': f'{category}-{quadrant_short}',
                        'type': 'line',
                        'stack': category,
                        'areaStyle': {'opacity': 0.7},
                        'emphasis': {'focus': 'series'},
                        'lineStyle': {'width': 0},
                        'data': quadrants_dict[quadrant_full],
                        'itemStyle': {'color': color}
                    })
            
            title_text = '一级分类 - 四象限商品结构趋势'
            subtitle_text = '堆叠面积图展示每个分类的商品结构变化(颜色表示象限)'
            y_axis_name = '商品数量'
            show_legend = True  # 显示图例说明象限颜色
            legend_type = 'quadrant'  # 图例类型:象限
            
        else:
            # 单象限折线模式
            quadrant_full, color, quadrant_name = quadrant_config[view_mode]
            
            for category, quadrants_dict in top_categories:
                series_data.append({
                    'name': category,
                    'type': 'line',
                    'smooth': True,
                    'data': quadrants_dict[quadrant_full],
                    'lineStyle': {'width': 3},
                    'emphasis': {'focus': 'series'}
                })
            
            title_text = f'一级分类 - {quadrant_name}数量趋势'
            subtitle_text = f'折线图展示TOP5分类的{quadrant_name}变化'
            y_axis_name = f'{quadrant_name}数量'
            show_legend = True
            legend_type = 'category'  # 图例类型:分类
        
        # ECharts配置
        option = {
            'title': {
                'text': title_text,
                'subtext': subtitle_text,
                'left': 'center',
                'textStyle': {'fontSize': 16}
            },
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {'type': 'cross'}
            },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '3%',
                'top': '18%' if legend_type == 'quadrant' else '22%',  # 堆叠模式图例较小,需要的空间少一些
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'boundaryGap': False,
                'data': x_labels
            },
            'yAxis': {
                'type': 'value',
                'name': y_axis_name
            },
            'series': series_data
        }
        
        # 配置图例
        if show_legend:
            if legend_type == 'quadrant':
                # 堆叠模式:显示象限图例
                option['legend'] = {
                    'top': '12%',
                    'left': 'center',
                    'orient': 'horizontal',
                    'data': [
                        {'name': '明星', 'icon': 'rect', 'itemStyle': {'color': '#52c41a'}},
                        {'name': '问题', 'icon': 'rect', 'itemStyle': {'color': '#faad14'}},
                        {'name': '引流', 'icon': 'rect', 'itemStyle': {'color': '#1890ff'}},
                        {'name': '淘汰', 'icon': 'rect', 'itemStyle': {'color': '#f5222d'}}
                    ],
                    'textStyle': {'fontSize': 13},
                    'itemWidth': 30,
                    'itemHeight': 14
                }
            else:
                # 单象限模式:显示分类图例
                option['legend'] = {
                    'top': '15%',
                    'left': 'center',
                    'orient': 'horizontal',
                    'data': [cat[0] for cat in top_categories]
                }
        
        chart_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        </head>
        <body>
            <div id="category-trend-chart" style="width: 100%; height: 400px;"></div>
            <script>
                var chartDom = document.getElementById('category-trend-chart');
                var myChart = echarts.init(chartDom);
                var option = {json.dumps(option, ensure_ascii=False)};
                myChart.setOption(option);
                window.addEventListener('resize', function() {{
                    myChart.resize();
                }});
            </script>
        </body>
        </html>
        '''
        
        period_desc = "每日" if is_daily else "每周"
        view_desc = {
            'all': '堆叠面积图展示TOP5分类的四象限商品结构',
            'star': '🟢明星商品（高利润高动销），重点维护对象',
            'problem': '🟡问题商品（高利润低动销），警惕库存积压',
            'traffic': '🔵引流商品（低利润高动销），关联销售机会',
            'eliminate': '🔴淘汰商品（低利润低动销），考虑清仓下架'
        }
        
        return html.Div([
            html.H6("📈 分类趋势分析", className="mb-2"),
            dcc.Markdown(f"💡 **说明**: {view_desc[view_mode]}，{period_desc}变化趋势", className="text-muted small mb-3"),
            html.Div(
                html.Iframe(
                    srcDoc=chart_html,
                    style={'width': '100%', 'height': '450px', 'border': 'none'}
                )
            )
        ], className="mb-4")
        
    except Exception as e:
        print(f"❌ [分类趋势图] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div()


def create_quadrant_migration_sankey_enhanced(quadrant_data, periods, period_label):
    """创建增强版象限迁移桑基图 - 显示所有迁移路径,线条粗细表示商品数量"""
    try:
        if not ECHARTS_AVAILABLE or len(periods) < 2:
            return html.Div()
        
        print(f"\n📊 [增强桑基图] 开始生成...")
        
        # 判断是按日还是按周
        is_daily = '日' in period_label or 'Day' in period_label
        
        # 统计所有迁移路径
        migrations = {}
        migration_details = []
        
        for product, quadrant_list in quadrant_data.items():
            valid_quadrants = [q for q in quadrant_list if q != '无数据']
            if len(valid_quadrants) >= 2:
                from_q = valid_quadrants[0]
                to_q = valid_quadrants[-1]
                key = (from_q, to_q)
                migrations[key] = migrations.get(key, 0) + 1
                migration_details.append({
                    'product': product,
                    'from': from_q,
                    'to': to_q,
                    'changed': from_q != to_q
                })
        
        # 打印统计信息
        print(f"   📊 总商品数: {len(migration_details)}")
        print(f"   🔄 迁移路径数: {len(migrations)}")
        total_changed = sum(1 for d in migration_details if d['changed'])
        print(f"   ✨ 发生变化: {total_changed}个商品")
        
        # 构建桑基图数据
        nodes = []
        links = []
        node_set = set()
        
        # 添加节点和连接
        for (from_q, to_q), count in migrations.items():
            if count > 0:
                # 象限名称映射(带emoji和详细说明)
                quadrant_map = {
                    '🌟 高利润高动销': {'short': '明星', 'emoji': '🌟', 'desc': '高利润高动销'},
                    '⚠️ 高利润低动销': {'short': '金牛', 'emoji': '⚠️', 'desc': '高利润低动销'},
                    '🚀 低利润高动销': {'short': '引流', 'emoji': '🚀', 'desc': '低利润高动销'},
                    '❌ 低利润低动销': {'short': '淘汰', 'emoji': '❌', 'desc': '低利润低动销'}
                }
                
                from_info = quadrant_map.get(from_q, {'short': from_q, 'emoji': '', 'desc': from_q})
                to_info = quadrant_map.get(to_q, {'short': to_q, 'emoji': '', 'desc': to_q})
                
                # 象限颜色映射(鲜明配色)
                color_map = {
                    '明星': '#52c41a',  # 绿色 - 明星商品
                    '金牛': '#faad14',  # 黄色 - 金牛商品
                    '引流': '#1890ff',  # 蓝色 - 引流商品
                    '淘汰': '#f5222d'   # 红色 - 淘汰商品
                }
                
                # 节点标签：增强标识(期初/期末 + emoji + 象限名 + 时间)
                if is_daily:
                    # periods是字符串列表,需要转换
                    first_date = pd.to_datetime(periods[0]).strftime("%m-%d") if isinstance(periods[0], str) else periods[0].strftime("%m-%d")
                    last_date = pd.to_datetime(periods[-1]).strftime("%m-%d") if isinstance(periods[-1], str) else periods[-1].strftime("%m-%d")
                    source_node = f'【期初】{from_info["emoji"]} {from_info["short"]}\n{first_date}'
                    target_node = f'【期末】{to_info["emoji"]} {to_info["short"]}\n{last_date}'
                else:
                    source_node = f'【期初】{from_info["emoji"]} {from_info["short"]}\n第1{period_label}'
                    target_node = f'【期末】{to_info["emoji"]} {to_info["short"]}\n第{len(periods)}{period_label}'
                
                if source_node not in node_set:
                    nodes.append({
                        'name': source_node,
                        'itemStyle': {'color': color_map.get(from_info['short'], '#999')}
                    })
                    node_set.add(source_node)
                
                if target_node not in node_set:
                    nodes.append({
                        'name': target_node,
                        'itemStyle': {'color': color_map.get(to_info['short'], '#999')}
                    })
                    node_set.add(target_node)
                
                # 添加连接(线条粗细由value决定，附带详细信息)
                links.append({
                    'source': source_node,
                    'target': target_node,
                    'value': count,
                    'lineStyle': {
                        'color': color_map.get(from_info['short'], '#999'),
                        'opacity': 0.3
                    }
                })
                
                print(f"   {from_info['short']} → {to_info['short']}: {count}个商品")
        
        # 桑基图标题：按日显示日期范围，按周显示周数范围
        if is_daily:
            first_date = pd.to_datetime(periods[0]).strftime("%m-%d") if isinstance(periods[0], str) else periods[0].strftime("%m-%d")
            last_date = pd.to_datetime(periods[-1]).strftime("%m-%d") if isinstance(periods[-1], str) else periods[-1].strftime("%m-%d")
            title_text = f'象限迁移可视化 (所有商品)'
            subtitle_text = f'分析周期: {first_date} → {last_date}, 线条粗细表示商品数量'
        else:
            title_text = f'象限迁移可视化 (所有商品)'
            subtitle_text = f'分析周期: 第1{period_label} → 第{len(periods)}{period_label}, 线条粗细表示商品数量'
        
        # 生成ECharts桑基图
        option = {
            'title': {
                'text': title_text,
                'subtext': subtitle_text,
                'left': 'center',
                'top': '2%'
            },
            'legend': {
                'data': [
                    {'name': '🌟 明星商品 (高利润高动销)', 'icon': 'circle', 'itemStyle': {'color': '#52c41a'}},
                    {'name': '⚠️ 金牛商品 (高利润低动销)', 'icon': 'circle', 'itemStyle': {'color': '#faad14'}},
                    {'name': '🚀 引流商品 (低利润高动销)', 'icon': 'circle', 'itemStyle': {'color': '#1890ff'}},
                    {'name': '❌ 淘汰商品 (低利润低动销)', 'icon': 'circle', 'itemStyle': {'color': '#f5222d'}}
                ],
                'top': '8%',
                'left': 'center',
                'orient': 'horizontal',
                'textStyle': {'fontSize': 12}
            },
            'tooltip': {
                'trigger': 'item',
                'triggerOn': 'mousemove',
                'confine': True
            },
            'grid': {
                'top': '18%'
            },
            'series': [{
                'type': 'sankey',
                'data': nodes,
                'links': links,
                'top': '18%',
                'bottom': '5%',
                'left': '5%',
                'right': '15%',
                'nodeWidth': 30,
                'nodeGap': 15,
                'layoutIterations': 32,
                'orient': 'horizontal',
                'draggable': False,
                'label': {
                    'fontSize': 11,
                    'fontWeight': 'bold',
                    'color': '#333'
                },
                'lineStyle': {
                    'color': 'source',
                    'curveness': 0.5
                },
                'emphasis': {
                    'focus': 'adjacency',
                    'lineStyle': {
                        'opacity': 0.6
                    }
                }
            }]
        }
        
        chart_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        </head>
        <body>
            <div id="sankey-chart" style="width: 100%; height: 550px;"></div>
            <script>
                var chartDom = document.getElementById('sankey-chart');
                var myChart = echarts.init(chartDom);
                var option = {json.dumps(option, ensure_ascii=False)};
                
                // 自定义tooltip formatter
                option.tooltip.formatter = function(params) {{
                    if (params.dataType === 'edge') {{
                        var source = params.data.source.split('\\n')[0];
                        var target = params.data.target.split('\\n')[0];
                        return source + ' → ' + target + '<br/>迁移商品数: ' + params.value + '个';
                    }} else {{
                        return params.name.replace('\\n', '<br/>') + '<br/>商品数: ' + params.value + '个';
                    }}
                }};
                
                myChart.setOption(option);
                window.addEventListener('resize', function() {{
                    myChart.resize();
                }});
            </script>
        </body>
        </html>
        '''
        
        # 迁移统计表
        migration_stats = []
        for (from_q, to_q), count in sorted(migrations.items(), key=lambda x: -x[1]):
            trend = ("📉 恶化" if from_q=='🌟 高利润高动销' and to_q=='❌ 低利润低动销'
                     else "📈 改善" if to_q=='🌟 高利润高动销' and from_q!='🌟 高利润高动销'
                     else "🔄 变化" if from_q!=to_q
                     else "➡️ 稳定")
            migration_stats.append({
                '起始象限': from_q,
                '当前象限': to_q,
                '趋势': trend,
                '商品数': count,
                '占比': f"{count/len(migration_details)*100:.1f}%"
            })
        
        stats_df = pd.DataFrame(migration_stats)
        
        return html.Div([
            html.H6("📊 象限迁移可视化", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Div(
                        html.Iframe(
                            srcDoc=chart_html,
                            style={'width': '100%', 'height': '550px', 'border': 'none'}
                        )
                    )
                ], md=8),
                dbc.Col([
                    html.H6("迁移统计", className="mb-2"),
                    html.Small(f"💡 共{len(migration_details)}个商品, {total_changed}个发生迁移", className="text-muted d-block mb-3"),
                    dash_table.DataTable(
                        data=stats_df.to_dict('records'),
                        columns=[{'name': c, 'id': c} for c in stats_df.columns],
                        # ✨ 性能优化: 启用分页和固定高度
                        page_action='native',
                        page_size=10,
                        style_table={'height': '350px', 'overflowY': 'auto'},
                        style_cell={'textAlign': 'left', 'fontSize': '12px', 'padding': '8px'},
                        style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
                        style_data_conditional=[
                            {
                                'if': {'filter_query': '{趋势} contains "恶化"'},
                                'backgroundColor': '#ffe6e6'
                            },
                            {
                                'if': {'filter_query': '{趋势} contains "改善"'},
                                'backgroundColor': '#e6ffe6'
                            }
                        ]
                    )
                ], md=4)
            ])
        ], className="mb-4")
        
    except Exception as e:
        print(f"❌ [增强桑基图] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div()


def generate_trend_analysis_content(df, period='week', alert_level='warning', view_mode='all', start_date=None, end_date=None):
    """生成趋势分析内容（用于Tab 2直接渲染）
    
    Args:
        period: 'day'(按日) / 'week'(按自然周) / 'month'(按月)
        view_mode: 'all'(全部堆叠) / 'star'(明星) / 'problem'(问题) / 'traffic'(引流) / 'eliminate'(淘汰)
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        print(f"\n📊 [生成趋势分析] 周期:{period}, 级别:{alert_level}, 视图:{view_mode}, 日期:{start_date} ~ {end_date}")
        
        # 计算时间维度四象限
        trend_data = calculate_time_period_quadrants(df, period=period, start_date=start_date, end_date=end_date)
        
        if not trend_data:
            return dbc.Alert("暂无足够数据进行趋势分析", color="info", className="mb-4")
        
        periods = trend_data['periods']
        period_label = trend_data['period_label']
        quadrant_data = trend_data['quadrant_data']
        alerts = trend_data['trend_alerts']
        
        print(f"   📊 总预警数: {len(alerts)}")
        
        # 筛选预警级别
        if alert_level == 'critical':
            filtered_alerts = [a for a in alerts if a['alert_level'] == 'critical']
            alert_level_text = '🔴 紧急预警'
        elif alert_level == 'warning':
            filtered_alerts = [a for a in alerts if a['alert_level'] in ['critical', 'warning']]
            alert_level_text = '🟡 重点关注'
        else:
            filtered_alerts = alerts
            alert_level_text = '🟢 全部趋势'
        
        print(f"   🎯 过滤后预警数: {len(filtered_alerts)} ({alert_level_text})")
        
        # ===== 1. 一级分类趋势图 (支持象限选择) =====
        category_trend_chart = create_category_trend_chart(df, periods, period_label, quadrant_data, view_mode)
        
        # ===== 2. 趋势预警卡片 =====
        alert_cards = []
        display_alerts = filtered_alerts[:20]  # 最多显示20个
        
        for alert in display_alerts:
            if alert['alert_level'] == 'critical':
                color = 'danger'
                icon = '🚨'
            elif alert['alert_level'] == 'warning':
                color = 'warning'
                icon = '⚠️'
            else:
                color = 'success'
                icon = '✅'
            
            alert_cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6([icon, f" {alert['product']}"], className="card-title"),
                            html.P(alert['trend'], className="mb-1", style={'fontSize': '0.9rem'}),
                            html.Small(alert['recommendation'], className="text-muted")
                        ])
                    ], color=color, outline=True)
                ], md=6, className="mb-3")
            )
        
        # 标题
        total_count = len(filtered_alerts)
        display_count = len(display_alerts)
        title = f"📢 商品趋势预警 ({alert_level_text} · 共{total_count}个"
        if total_count > display_count:
            title += f", 显示前{display_count}个)"
        else:
            title += ")"
        
        alert_section = html.Div([
            html.H6(title, className="mb-3"),
            dbc.Row(alert_cards) if alert_cards else dbc.Alert(f"暂无{alert_level_text}商品", color="success")
        ], className="mb-4")
        
        # ===== 3. 象限迁移可视化 (优化:显示所有迁移路径,线条粗细表示商品数量) =====
        migration_chart = create_quadrant_migration_sankey_enhanced(quadrant_data, periods, period_label)
        
        return html.Div([
            category_trend_chart,  # 新增:分类趋势图
            alert_section,
            migration_chart
        ])
        
    except Exception as e:
        print(f"❌ [生成趋势分析] 错误: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"趋势分析生成错误: {e}", color="danger", className="mb-4")


@app.callback(
    Output('tab-2-content', 'children'),
    Input('main-tabs', 'value')
)
def render_tab2_content(active_tab):
    """Tab 2: 商品分析 - 商品销售排行、分类分析、库存周转、滞销预警
    
    ✅ 使用统一计算标准（与Tab 1一致）
    """
    if active_tab != 'tab-2':
        raise PreventUpdate
    
    if GLOBAL_DATA is None:
        return dbc.Alert("⚠️ 未加载数据，请重启应用", color="warning", className="text-center")
    
    df = GLOBAL_DATA.copy()
    
    # ==================== 📐 标准计算流程（✅ 使用统一函数）====================
    try:
        print("\n" + "="*80)
        print("🔍 [Tab 2] 开始计算，使用统一标准")
        print("="*80)
        
        # ===== Step 0: 识别并剔除异常订单 =====
        # 异常订单定义：0销量 AND 0利润额 AND 0成本（同时满足三个条件）
        original_count = len(df)
        
        # 识别异常订单（需要同时满足三个条件）
        abnormal_mask = (
            (df['月售'] == 0) & 
            (df['利润额'] == 0) & 
            (df['商品采购成本'] == 0)
        )
        
        abnormal_count = abnormal_mask.sum()
        
        if abnormal_count > 0:
            # 剔除异常订单
            df = df[~abnormal_mask].copy()
            print(f"⚠️  [数据清洗] 识别到 {abnormal_count} 条异常订单（0销量&0利润&0成本），已自动剔除")
            print(f"   原始数据: {original_count} 行 → 清洗后: {len(df)} 行")
        else:
            print(f"✅ [数据清洗] 未发现异常订单，数据质量良好（{original_count} 行）")
        
        # ===== Step 1: 调用统一订单计算函数 =====
        order_agg = calculate_order_metrics(df)  # ✅ 使用公共函数，与Tab 1保持一致
        
        print("✅ 订单级聚合完成（使用统一函数）")
        print(f"   订单数: {len(order_agg)}")
        print(f"   订单总利润: ¥{order_agg['订单实际利润'].sum():,.2f}")
        
        # ===== Step 2: 商品维度数据准备 =====
        # 保留商品信息到订单聚合数据（用于后续商品聚合）
        order_product_map = df.groupby('订单ID').agg({
            '商品名称': lambda x: ','.join(str(i) for i in x.unique()),  # ✅ 转换为字符串避免类型错误
            '一级分类名': lambda x: ','.join(str(i) for i in x.unique()) if '一级分类名' in df.columns else ''
        }).reset_index()
        
        # 合并商品信息
        order_agg = order_agg.merge(order_product_map, on='订单ID', how='left')
        
        # ===== Step 4: 将订单利润分配到商品 =====
        # 为每个商品明细行添加订单实际利润
        df_with_profit = df.merge(
            order_agg[['订单ID', '订单实际利润']],
            on='订单ID',
            how='left'
        )
        
        # 计算每个订单的商品总销售额（用于分配利润）
        # ⚠️ 关键修复：实收价格是单价，需要先乘以销量
        sales_col = '月售' if '月售' in df.columns else '销量'
        if sales_col in df.columns:
            df_temp = df.copy()
            df_temp['订单总收入'] = df_temp['实收价格'] * df_temp[sales_col]
            order_sales_sum = df_temp.groupby('订单ID')['订单总收入'].sum().reset_index()
            order_sales_sum.columns = ['订单ID', '订单商品总额']
            print(f"🔧 [四象限分析] 实收价格修复: 使用(实收价格×{sales_col})计算订单商品总额")
            # 同时计算单个商品的总收入
            df_with_profit['商品总收入'] = df_with_profit['实收价格'] * df_with_profit[sales_col]
        else:
            order_sales_sum = df.groupby('订单ID')['实收价格'].sum().reset_index()
            order_sales_sum.columns = ['订单ID', '订单商品总额']
            df_with_profit['商品总收入'] = df_with_profit['实收价格']
            print(f"⚠️ [四象限分析] 实收价格兜底: 直接sum（缺少销量字段）")
        
        df_with_profit = df_with_profit.merge(order_sales_sum, on='订单ID', how='left')
        
        # 按商品销售额比例分配订单利润
        df_with_profit['商品分配利润'] = (
            df_with_profit['订单实际利润'] * 
            df_with_profit['商品总收入'] / 
            df_with_profit['订单商品总额']
        ).fillna(0)
        
        # ===== Step 5: 商品维度聚合 =====
        # 检查是否存在实收价格字段
        has_actual_price = '实收价格' in df.columns
        if not has_actual_price:
            print("⚠️ [四象限分析] 未找到'实收价格'字段，将使用'预计订单收入'计算利润率")
        else:
            print("✅ [四象限分析] 检测到'实收价格'字段，将用于计算实收利润率")
        
        agg_dict = {
            '预计订单收入': 'sum',         # ✅ 销售额（使用Y列预计订单收入，更真实）
            '商品采购成本': 'sum',         # 成本
            '利润额': 'sum',               # ✅ 实际利润（直接使用N列利润额，商品级已计算好）
            '月售': 'sum',                 # 销量（整个周期累计）
            '库存': 'last',                # ✅ 库存（取最后一天的库存，反映当前状态）
            '订单ID': 'nunique',            # 订单数
            '店内码': 'first',              # ✅ 新增：店内码
            '一级分类名': 'first',          # ✅ 新增：一级分类
            '三级分类名': 'first'           # ✅ 新增：三级分类
        }
        
        # 如果存在实收价格字段，添加到聚合中
        if has_actual_price:
            agg_dict['实收价格'] = 'sum'   # ✅ W列实收价格（排除补贴/折扣，更真实）
        
        product_agg = df.groupby('商品名称').agg(agg_dict).reset_index()
        
        # 设置列名
        if has_actual_price:
            product_agg.columns = ['商品名称', '销售额', '成本', '实际利润', '总销量', '库存', '订单数', '店内码', '一级分类名', '三级分类名', '实收价格']
        else:
            product_agg.columns = ['商品名称', '销售额', '成本', '实际利润', '总销量', '库存', '订单数', '店内码', '一级分类名', '三级分类名']
        
        # 计算衍生指标
        product_agg['平均售价'] = (product_agg['销售额'] / product_agg['总销量']).fillna(0)
        product_agg['平均成本'] = (product_agg['成本'] / product_agg['总销量']).fillna(0)
        
        # ✅ 修复利润率计算：优先使用实收价格（W列），避免除以0产生inf
        if has_actual_price:
            # 使用实收价格计算实收利润率（排除补贴/折扣影响）
            product_agg['利润率'] = (
                product_agg['实际利润'] / product_agg['实收价格'].replace(0, np.nan) * 100
            ).fillna(0).replace([np.inf, -np.inf], 0)
            print(f"✅ [利润率计算] 使用'实收价格'计算，平均实收利润率: {product_agg['利润率'].mean():.2f}%")
        else:
            # 回退方案：使用预计订单收入
            product_agg['利润率'] = (
                product_agg['实际利润'] / product_agg['销售额'].replace(0, np.nan) * 100
            ).fillna(0).replace([np.inf, -np.inf], 0)
            print(f"✅ [利润率计算] 使用'预计订单收入'计算，平均利润率: {product_agg['利润率'].mean():.2f}%")
        
        # ✅ 优化库存周转率计算：智能处理0库存情况
        def calculate_smart_turnover(row):
            """智能计算库存周转率，区分售罄和滞销"""
            sales = row['总销量']
            stock = row['库存']
            
            if stock == 0:
                if sales > 0:
                    # 情况1：0库存但有销量 = 售罄商品（动销很好）
                    # 使用销量作为估算周转率（假设平均库存为1）
                    return float(sales)  # 高周转率
                else:
                    # 情况2：0库存0销量 = 已下架商品
                    return 0.0
            else:
                # 正常计算
                return float(sales / stock)
        
        product_agg['库存周转率'] = product_agg.apply(calculate_smart_turnover, axis=1)
        product_agg['库存周转率'] = product_agg['库存周转率'].replace([np.inf, -np.inf], 0)
        
        # 统计0库存商品情况
        zero_stock_with_sales = ((product_agg['库存'] == 0) & (product_agg['总销量'] > 0)).sum()
        zero_stock_no_sales = ((product_agg['库存'] == 0) & (product_agg['总销量'] == 0)).sum()
        print(f"📦 [库存分析] 0库存商品: {zero_stock_with_sales}个售罄, {zero_stock_no_sales}个无销量")
        
        # ===== Step 6: 四象限分析 =====
        # 计算动销指数（综合指标：销量+周转率+订单数）
        # 先进行标准化处理（Min-Max标准化到0-1区间）
        min_sales = product_agg['总销量'].min()
        max_sales = product_agg['总销量'].max()
        min_turnover = product_agg['库存周转率'].min()
        max_turnover = product_agg['库存周转率'].max()
        min_orders = product_agg['订单数'].min()
        max_orders = product_agg['订单数'].max()
        
        # 避免除以0
        sales_range = max_sales - min_sales if max_sales > min_sales else 1
        turnover_range = max_turnover - min_turnover if max_turnover > min_turnover else 1
        orders_range = max_orders - min_orders if max_orders > min_orders else 1
        
        product_agg['标准化销量'] = (product_agg['总销量'] - min_sales) / sales_range
        product_agg['标准化周转率'] = (product_agg['库存周转率'] - min_turnover) / turnover_range
        product_agg['标准化订单数'] = (product_agg['订单数'] - min_orders) / orders_range
        
        # 动销指数 = 0.5×销量 + 0.3×周转率 + 0.2×订单数
        product_agg['动销指数'] = (
            0.5 * product_agg['标准化销量'] + 
            0.3 * product_agg['标准化周转率'] + 
            0.2 * product_agg['标准化订单数']
        )
        
        # 计算阈值（默认值）
        profit_threshold = 30.0  # 利润率阈值：30%
        sales_threshold = product_agg['动销指数'].median()  # 动销指数阈值：中位数
        
        # 四象限判定
        def classify_quadrant(row):
            high_profit = row['利润率'] > profit_threshold
            high_sales = row['动销指数'] > sales_threshold
            
            if high_profit and high_sales:
                return '🌟 高利润高动销'
            elif high_profit and not high_sales:
                return '⚠️ 高利润低动销'
            elif not high_profit and high_sales:
                return '🚀 低利润高动销'
            else:
                return '❌ 低利润低动销'
        
        product_agg['象限分类'] = product_agg.apply(classify_quadrant, axis=1)
        
        # ===== Step 6.5: 订单级盈利健康度分析 ✅ 新增 =====
        print("🔍 [订单级盈利分析] 开始计算...")
        
        # 准备订单级利润数据（每个商品的每个订单的利润）
        order_profit_detail = df_with_profit.groupby(['商品名称', '订单ID']).agg({
            '订单实际利润': 'first'  # 每个订单的实际利润
        }).reset_index()
        
        # 计算每个商品的盈利订单统计
        profit_health = order_profit_detail.groupby('商品名称').agg(
            总订单数=('订单ID', 'count'),
            盈利订单数=('订单实际利润', lambda x: (x > 0).sum()),
            亏损订单数=('订单实际利润', lambda x: (x <= 0).sum()),
            订单平均利润=('订单实际利润', 'mean'),
            订单利润标准差=('订单实际利润', 'std')
        ).reset_index()
        
        # 计算盈利订单占比
        profit_health['盈利订单占比'] = (
            profit_health['盈利订单数'] / profit_health['总订单数'] * 100
        ).fillna(0)
        
        # 判定健康度
        def get_health_status(ratio):
            if ratio >= 70:
                return '🟢 稳定盈利'
            elif ratio >= 40:
                return '🟡 波动盈利'
            elif ratio > 0:
                return '🔴 依赖大单'
            else:
                return '⚫ 全部亏损'
        
        profit_health['盈利健康度'] = profit_health['盈利订单占比'].apply(get_health_status)
        
        # 合并到商品聚合数据
        product_agg = product_agg.merge(
            profit_health[['商品名称', '盈利订单数', '亏损订单数', '盈利订单占比', '订单平均利润', '盈利健康度']], 
            on='商品名称', 
            how='left'
        )
        
        print(f"✅ [订单级盈利分析] 完成")
        print(f"   盈利健康度分布:")
        print(f"   {product_agg['盈利健康度'].value_counts().to_dict()}")
        
        # 智能经营建议（增强版，考虑盈利健康度）
        # 智能经营建议（增强版，考虑盈利健康度）
        def get_recommendation(row):
            quadrant = row['象限分类']
            stock = row['库存']
            turnover = row['库存周转率']
            health = row['盈利健康度']
            profit_ratio = row['盈利订单占比']
            
            # 基础建议
            base_rec = ""
            if quadrant == '🌟 高利润高动销':
                if turnover > 5:
                    base_rec = "明星商品，建议增加库存确保不断货"
                else:
                    base_rec = "优质商品，保持现有策略"
            elif quadrant == '⚠️ 高利润低动销':
                if stock > 10:
                    base_rec = "库存过高，建议促销或减少采购"
                else:
                    base_rec = "观察需求，谨慎补货"
            elif quadrant == '🚀 低利润高动销':
                base_rec = "流量商品，可适当提价或配合高利润品销售"
            else:
                base_rec = "建议清仓或下架"
            
            # 根据盈利健康度补充建议
            health_rec = ""
            if health == '🔴 依赖大单' and quadrant in ['🌟 高利润高动销', '⚠️ 高利润低动销']:
                health_rec = f" | ⚠️ 注意：{profit_ratio:.0f}%订单盈利，建议设置起购量或调整小单定价"
            elif health == '🟡 波动盈利':
                health_rec = f" | 💡 {profit_ratio:.0f}%订单盈利，盈利稳定性一般"
            elif health == '⚫ 全部亏损':
                health_rec = " | 🚨 所有订单都亏损，立即优化或下架"
            
            return base_rec + health_rec
        
        product_agg['经营建议'] = product_agg.apply(get_recommendation, axis=1)
        
        # 统计各象限商品数量
        quadrant_stats = product_agg['象限分类'].value_counts().to_dict()
        
        print(f"✅ 四象限分析完成")
        print(f"   利润率阈值: {profit_threshold}%")
        print(f"   动销指数阈值: {sales_threshold:.3f}")
        print(f"   🌟 高利润高动销: {quadrant_stats.get('🌟 高利润高动销', 0)} 个")
        print(f"   ⚠️ 高利润低动销: {quadrant_stats.get('⚠️ 高利润低动销', 0)} 个")
        print(f"   🚀 低利润高动销: {quadrant_stats.get('🚀 低利润高动销', 0)} 个")
        print(f"   ❌ 低利润低动销: {quadrant_stats.get('❌ 低利润低动销', 0)} 个")
        
        # ===== Step 8: 分类分析（如果有分类字段）=====
        if '一级分类名' in df.columns:
            # ✅ 直接基于源数据聚合（与商品聚合保持一致）
            category_sales = df.groupby('一级分类名').agg({
                '预计订单收入': 'sum',      # ✅ Y列：销售额
                '月售': 'sum',              # 销量
                '利润额': 'sum',            # ✅ N列：实际利润
                '订单ID': 'nunique'         # 订单数
            }).reset_index()
            
            category_sales.columns = ['分类', '销售额', '销量', '实际利润', '订单数']
            category_sales['利润率'] = (
                (category_sales['实际利润'] / category_sales['销售额'] * 100).fillna(0)
            )
            category_sales = category_sales.sort_values('销售额', ascending=False)
            
            print(f"✅ 分类分析完成: {len(category_sales)} 个分类")
        else:
            category_sales = None
            
    except Exception as e:
        print(f"[ERROR] Tab2 指标计算失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"❌ 数据处理失败: {e}", color="danger")
    
    # ==================== 页面布局 ====================
    # 构建content列表
    content = [
        # 标题
        html.H2("📦 商品分析", className="mb-4"),
        
        # ========== 1. 四象限智能分析 ==========
        html.Hr(),
        dbc.Row([
            dbc.Col([
                html.H4("🎯 商品四象限智能分析", className="mb-0")
            ], md=8),
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-download me-2"), "📥 导出分析数据"],
                    id='btn-export-quadrant',
                    color='primary',
                    size='sm',
                    className='float-end'
                )
            ], md=4)
        ], className="mb-3"),
        
        # 象限统计卡片
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("🌟 高利润高动销", className="card-title text-success"),
                        html.H3(f"{quadrant_stats.get('🌟 高利润高动销', 0)}", className="text-success mb-0"),
                        html.Small("明星产品", className="text-muted")
                    ])
                ], className="modern-card text-center shadow-sm border-success")  # 🎨 添加modern-card
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("⚠️ 高利润低动销", className="card-title text-warning"),
                        html.H3(f"{quadrant_stats.get('⚠️ 高利润低动销', 0)}", className="text-warning mb-0"),
                        html.Small("问题产品", className="text-muted")
                    ])
                ], className="modern-card text-center shadow-sm border-warning")  # 🎨 添加modern-card
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("🚀 低利润高动销", className="card-title text-info"),
                        html.H3(f"{quadrant_stats.get('🚀 低利润高动销', 0)}", className="text-info mb-0"),
                        html.Small("引流产品", className="text-muted")
                    ])
                ], className="modern-card text-center shadow-sm border-info")  # 🎨 添加modern-card
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("❌ 低利润低动销", className="card-title text-danger"),
                        html.H3(f"{quadrant_stats.get('❌ 低利润低动销', 0)}", className="text-danger mb-0"),
                        html.Small("淘汰产品", className="text-muted")
                    ])
                ], className="modern-card text-center shadow-sm border-danger")  # 🎨 添加modern-card
            ], md=3),
        ], className="mb-4"),
        
        # ========== 📈 时间维度趋势分析 ==========
        html.Hr(),
        
        # 标题行
        dbc.Row([
            dbc.Col([
                html.H5("📈 四象限趋势分析", className="mb-0")
            ], md=12),
        ], className="mb-3"),
        
        # 控制面板:日期范围 + 象限选择 + 粒度选择
        dbc.Row([
            # 日期范围选择
            dbc.Col([
                html.Label("📅 日期范围", className="fw-bold mb-2", style={'fontSize': '14px'}),
                dcc.DatePickerRange(
                    id='trend-date-range',
                    start_date=None,  # 将在callback中设置
                    end_date=None,
                    display_format='YYYY-MM-DD',
                    style={'fontSize': '13px'}
                ),
                html.Div([
                    dbc.Button("全部", id='btn-date-all', size='sm', color='link', className='p-0 me-2'),
                    dbc.Button("最近7天", id='btn-date-7d', size='sm', color='link', className='p-0 me-2'),
                    dbc.Button("最近14天", id='btn-date-14d', size='sm', color='link', className='p-0')
                ], className="mt-1")
            ], md=4),
            
            # 象限选择
            dbc.Col([
                html.Label("🎯 象限选择", className="fw-bold mb-2", style={'fontSize': '14px'}),
                dcc.Dropdown(
                    id='quadrant-view-selector',
                    options=[
                        {'label': '📊 全部象限（堆叠）', 'value': 'all'},
                        {'label': '🟢 明星商品', 'value': 'star'},
                        {'label': '🟡 问题商品', 'value': 'problem'},
                        {'label': '🔵 引流商品', 'value': 'traffic'},
                        {'label': '🔴 淘汰商品', 'value': 'eliminate'}
                    ],
                    value='all',
                    clearable=False,
                    style={'fontSize': '14px'}
                )
            ], md=4),
            
            # 粒度选择
            dbc.Col([
                html.Label("📊 时间粒度", className="fw-bold mb-2", style={'fontSize': '14px'}),
                dbc.ButtonGroup([
                    dbc.Button("按日", id='btn-trend-day', color='primary', size='sm', outline=True),
                    dbc.Button("按自然周", id='btn-trend-week', color='primary', size='sm', active=True),
                    dbc.Button("按月", id='btn-trend-month', color='primary', size='sm', outline=True)
                ], size='sm', className='d-flex')
            ], md=4)
        ], className="mb-4"),
        
        # 趋势分析内容容器 (动态更新)
        html.Div(id='trend-analysis-container'),
        
        html.Hr(),
        html.H5("📊 当前四象限分布", className="mb-3"),
        
        # ✅ 四象限定义说明标签
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H6("📊 四象限分析定义说明", className="alert-heading mb-3"),
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.Strong("📐 分析维度："),
                                html.Ul([
                                    html.Li([html.Strong("实收利润率"), f" = 实际利润 ÷ 实收价格 × 100%（阈值：{profit_threshold}%，实收价格=客户实付，排除补贴/折扣）"]),
                                    html.Li([
                                        html.Strong("动销指数"), 
                                        f" = 0.5×标准化销量 + 0.3×标准化周转率 + 0.2×标准化订单数（阈值：{sales_threshold:.3f}，取中位数）"
                                    ]),
                                    html.Li([
                                        html.Strong("库存周转率"), 
                                        " = 总销量 ÷ 库存（",
                                        html.Span("特殊处理", style={'color': '#ff6b00', 'fontWeight': 'bold'}),
                                        "：0库存有销量=售罄商品，周转率=销量；0库存0销量=下架商品，周转率=0）"
                                    ]),
                                    html.Li([
                                        html.Span("⚠️ 异常订单剔除", style={'color': '#dc3545', 'fontWeight': 'bold'}),
                                        "：自动识别并剔除",
                                        html.Strong(" 0销量 & 0利润 & 0成本 "),
                                        "的异常订单（数据源问题，不参与分析）"
                                    ]),
                                ], className="mb-2"),
                            ], md=6),
                            dbc.Col([
                                html.Strong("🎯 象限定义："),
                                html.Ul([
                                    html.Li([html.Span("🌟 高利润高动销", className="text-success"), "：利润率>30% 且 动销指数>中位数 → ", html.Strong("明星产品，重点维护")]),
                                    html.Li([html.Span("⚠️ 高利润低动销", className="text-warning"), "：利润率>30% 但 动销指数≤中位数 → ", html.Strong("优化库存或促销")]),
                                    html.Li([html.Span("🚀 低利润高动销", className="text-info"), "：利润率≤30% 但 动销指数>中位数 → ", html.Strong("引流品，关联销售")]),
                                    html.Li([html.Span("❌ 低利润低动销", className="text-danger"), "：利润率≤30% 且 动销指数≤中位数 → ", html.Strong("考虑清仓下架")]),
                                ], className="mb-2"),
                            ], md=6),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                html.Strong("💡 盈利健康度分析（订单级）："),
                                html.Ul([
                                    html.Li([html.Span("🟢 稳定盈利", className="text-success"), "：≥70%订单盈利"]),
                                    html.Li([html.Span("🟡 波动盈利", className="text-warning"), "：40-70%订单盈利"]),
                                    html.Li([html.Span("🔴 依赖大单", className="text-danger"), "：<40%订单盈利但总体盈利（需关注定价策略）"]),
                                    html.Li([html.Span("⚫ 全部亏损", className="text-dark"), "：0%订单盈利（立即处理）"]),
                                ], className="mb-2"),
                                html.Div([
                                    html.Strong("📌 大单/小单定义说明：", style={'color': '#0066cc'}),
                                    html.Ul([
                                        html.Li([
                                            html.Strong("大单"), 
                                            "：指该商品的",
                                            html.Span("盈利订单", style={'color': '#28a745', 'fontWeight': 'bold'}),
                                            "（多为购买数量多或金额高的订单）"
                                        ]),
                                        html.Li([
                                            html.Strong("小单"), 
                                            "：指该商品的",
                                            html.Span("亏损订单", style={'color': '#dc3545', 'fontWeight': 'bold'}),
                                            "（多为购买数量少或金额低的订单，配送成本>利润）"
                                        ]),
                                        html.Li([
                                            "⚠️ ",
                                            html.Strong("依赖大单"), 
                                            "的商品：虽然总体盈利，但",
                                            html.Span(">60%订单亏损", style={'color': '#dc3545'}),
                                            "，盈利完全靠少数大单支撑 → 建议设置起购量或调整小单定价"
                                        ]),
                                    ], className="mb-0", style={'fontSize': '0.85rem', 'color': '#555'}),
                                ], style={'backgroundColor': '#f8f9fa', 'padding': '10px', 'borderRadius': '5px', 'marginTop': '8px'}),
                            ], md=12),
                        ]),
                    ], style={'fontSize': '0.9rem'})
                ], color="info", className="mb-3", style={'backgroundColor': '#e7f3ff'})
            ], md=12)
        ]),
        
        # 四象限散点图 - 直接在渲染时生成
        dbc.Row([
            dbc.Col([
                generate_quadrant_scatter_chart(product_agg, profit_threshold, sales_threshold)
            ], md=12)
        ], className="mb-4"),
        
        # 象限筛选和表格
        dbc.Row([
            dbc.Col([
                html.Label("筛选象限:"),
                dcc.Dropdown(
                    id='quadrant-filter',
                    options=[
                        {'label': '📊 全部商品', 'value': 'all'},
                        {'label': '🌟 高利润高动销（明星产品）', 'value': '🌟 高利润高动销'},
                        {'label': '⚠️ 高利润低动销（问题产品）', 'value': '⚠️ 高利润低动销'},
                        {'label': '🚀 低利润高动销（引流产品）', 'value': '🚀 低利润高动销'},
                        {'label': '❌ 低利润低动销（淘汰产品）', 'value': '❌ 低利润低动销'}
                    ],
                    value='all',
                    clearable=False,
                    className="mb-3"
                )
            ], md=4)
        ]),
        
        html.Div(id='quadrant-product-table', className="mt-3"),
        
        # 下载组件
        dcc.Download(id='download-quadrant-data'),
        
        # ========== 3. 商品销售排行 ==========
        html.Hr(),
        html.H4("🏆 商品销售排行", className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Label("排序维度:"),
                dcc.Dropdown(
                    id='product-rank-dimension',
                    options=[
                        {'label': '💰 销售额', 'value': '销售额'},
                        {'label': '💵 实际利润', 'value': '实际利润'},
                        {'label': '📈 利润率', 'value': '利润率'},
                        {'label': '📦 销量', 'value': '总销量'},
                        {'label': '📊 订单数', 'value': '订单数'}
                    ],
                    value='销售额',
                    clearable=False,
                    className="mb-3"
                )
            ], md=3),
            
            dbc.Col([
                html.Label("显示数量:"),
                dcc.Dropdown(
                    id='product-rank-limit',
                    options=[
                        {'label': 'TOP 10', 'value': 10},
                        {'label': 'TOP 20', 'value': 20},
                        {'label': 'TOP 30', 'value': 30},
                        {'label': 'TOP 50', 'value': 50}
                    ],
                    value=20,
                    clearable=False,
                    className="mb-3"
                )
            ], md=3)
        ]),
        
        html.Div(id='product-ranking-chart'),
        
        html.Div(id='product-ranking-table', className="mt-3"),
        
        # ========== 4. 分类分析 ==========
        html.Hr(),
        html.H4("📂 分类分析", className="mb-3"),
        
        # 销售分布 - 独占一行
        dbc.Row([
            dbc.Col([
                html.Div(id='category-sales-chart')
            ], md=12)
        ], className="mb-4"),
        
        # 利润分析 - 独占一行
        dbc.Row([
            dbc.Col([
                html.Div(id='category-profit-chart')
            ], md=12)
        ]),
        
        # ========== 5. 商品结构分析 ==========
        html.Hr(),
        html.H4("🔍 商品结构分析", className="mb-3"),
        
        dbc.Row([
            dbc.Col([
                html.Div(id='price-range-chart')
            ], md=6),
            
            dbc.Col([
                html.Div(id='abc-analysis-chart')
            ], md=6)
        ]),
        
        # ========== 6. 库存预警 ==========
        html.Hr(),
        dbc.Row([
            dbc.Col([
                html.H4("⚠️ 库存与滞销预警", className="mb-0")
            ], md=8),
            dbc.Col([
                dbc.Button(
                    [html.I(className="bi bi-download me-2"), "📥 导出预警数据"],
                    id='btn-export-inventory-warnings',
                    color='success',
                    size='sm',
                    className='float-end'
                )
            ], md=4)
        ], className="mb-3"),
        
        html.Div(id='inventory-warning-section'),
        
        # ========== 🤖 AI智能分析工作流 ==========
        html.Hr(),
        dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.I(className="bi bi-robot me-2"),
                    html.H4("🤖 AI智能商品分析工作流", className="d-inline mb-0"),
                    html.Small(" - 全面分析7大板块数据", className="text-muted ms-2")
                ], className="d-flex align-items-center")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        # 分析模式选择
                        html.H6("📋 选择分析范围:", className="mb-2"),
                        dbc.RadioItems(
                            id='ai-analysis-mode',
                            options=[
                                {'label': ' 🎯 快速分析 (仅四象限)', 'value': 'quick'},
                                {'label': ' 🔍 标准分析 (四象限+趋势+排行)', 'value': 'standard'},
                                {'label': ' 📊 全面分析 (所有7大板块+综合报告)', 'value': 'comprehensive'}
                            ],
                            value='quick',
                            className="mb-3"
                        ),
                        
                        dbc.Alert([
                            html.I(className="bi bi-info-circle-fill me-2"),
                            html.Div(id='ai-mode-description')
                        ], color="info", className="mb-3"),
                        
                        dbc.Button(
                            [
                                html.I(className="bi bi-stars me-2"),
                                "🚀 开始AI智能分析"
                            ],
                            id='ai-tab2-analyze-btn',
                            color="primary",
                            size="lg",
                            className="w-100 mb-3"
                        ),
                        
                        # 分析进度显示
                        html.Div(id='ai-analysis-progress', className="mb-3"),
                        
                        # AI分析结果显示区域
                        dcc.Loading(
                            id="loading-ai-tab2-analysis",
                            type="default",
                            children=[
                                html.Div(id='ai-tab2-analysis-result', className="mt-3")
                            ]
                        )
                    ], md=12)
                ])
            ])
        ], className="mb-4"),
        
        # 下载组件
        dcc.Download(id='download-inventory-warnings'),
        
        # 隐藏数据存储 - 增强版,支持多板块分析
        dcc.Store(id='product-agg-data', data=product_agg.to_dict('records')),
        dcc.Store(id='category-sales-data', data=category_sales.to_dict('records') if category_sales is not None else None),
        # 新增:存储趋势分析和其他板块数据
        dcc.Store(id='tab2-all-data', data={
            'product_agg': product_agg.to_dict('records'),
            'category_agg': category_sales.to_dict('records') if category_sales is not None else None,
            'quadrant_stats': quadrant_stats,
            'profit_threshold': profit_threshold,
            'sales_threshold': sales_threshold
        })
    ]
    
    return html.Div(content)


# ==================== Tab 2 新增回调: AI分析模式描述 ====================
@app.callback(
    Output('ai-mode-description', 'children'),
    Input('ai-analysis-mode', 'value')
)
def update_ai_mode_description(mode):
    """更新AI分析模式描述"""
    descriptions = {
        'quick': [
            html.Strong("快速分析模式："),
            html.Br(),
            "• 分析范围: 四象限数据",
            html.Br(),
            "• 耗时约: 5-8秒",
            html.Br(),
            "• 适用场景: 快速查看商品组合优化建议"
        ],
        'standard': [
            html.Strong("标准分析模式："),
            html.Br(),
            "• 分析范围: 四象限 + 趋势分析 + 商品排行",
            html.Br(),
            "• 耗时约: 15-20秒",
            html.Br(),
            "• 适用场景: 全面了解商品表现和趋势变化"
        ],
        'comprehensive': [
            html.Strong("全面分析模式："),
            html.Br(),
            "• 分析范围: 7大板块(四象限/趋势/排行/分类/结构/库存) + 综合报告",
            html.Br(),
            "• 耗时约: 30-40秒",
            html.Br(),
            "• 适用场景: 制定完整的商品运营策略和执行计划",
            html.Br(),
            "• 输出: 分板块分析 + 整合性策略建议"
        ]
    }
    return descriptions.get(mode, [])


# ==================== Tab 2 子回调: 四象限散点图（已废弃 - 改为直接渲染）====================
# @app.callback(
#     Output('quadrant-scatter-chart', 'children'),
#     Input('product-agg-data', 'data')
# )
# def update_quadrant_scatter(product_data):
#     """更新四象限散点图（✅ ECharts版）"""
#     # 此回调已废弃，四象限图现在在render_tab2_content中直接生成
#     pass


# ==================== Tab 2 子回调: 趋势分析周期切换 ====================
@app.callback(
    [Output('trend-analysis-container', 'children'),
     Output('btn-trend-day', 'active'),
     Output('btn-trend-week', 'active'),
     Output('btn-trend-month', 'active'),
     Output('trend-date-range', 'start_date'),
     Output('trend-date-range', 'end_date')],
    [Input('btn-trend-day', 'n_clicks'),
     Input('btn-trend-week', 'n_clicks'),
     Input('btn-trend-month', 'n_clicks'),
     Input('quadrant-view-selector', 'value'),
     Input('trend-date-range', 'start_date'),
     Input('trend-date-range', 'end_date'),
     Input('btn-date-all', 'n_clicks'),
     Input('btn-date-7d', 'n_clicks'),
     Input('btn-date-14d', 'n_clicks')],
    [State('btn-trend-day', 'active'),
     State('btn-trend-week', 'active'),
     State('btn-trend-month', 'active')],
    prevent_initial_call=False
)
def update_trend_analysis(day_clicks, week_clicks, month_clicks, view_mode, 
                         start_date, end_date, all_clicks, d7_clicks, d14_clicks,
                         day_active, week_active, month_active):
    """切换趋势分析周期（按日/按自然周/按月）、象限视图和日期范围"""
    try:
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return dbc.Alert("请先上传数据", color="warning"), False, True, False, None, None
        
        # 获取数据的日期范围
        data_dates = pd.to_datetime(GLOBAL_DATA['日期'], errors='coerce')
        data_min_date = data_dates.min().date()
        data_max_date = data_dates.max().date()
        
        # 判断触发源
        ctx = callback_context
        if not ctx.triggered:
            # 初始加载，默认按周，全部日期
            period = 'week'
            day_active = False
            week_active = True
            month_active = False
            view_mode = view_mode or 'all'
            start_date = data_min_date
            end_date = data_max_date
        else:
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            
            # 处理粒度切换
            if trigger_id == 'btn-trend-day':
                period = 'day'
                day_active, week_active, month_active = True, False, False
            elif trigger_id == 'btn-trend-week':
                period = 'week'
                day_active, week_active, month_active = False, True, False
            elif trigger_id == 'btn-trend-month':
                period = 'month'
                day_active, week_active, month_active = False, False, True
            # 处理日期快捷按钮
            elif trigger_id == 'btn-date-all':
                start_date = data_min_date
                end_date = data_max_date
                # 全部数据时,保持当前粒度
                if day_active:
                    period = 'day'
                elif month_active:
                    period = 'month'
                else:
                    period = 'week'
            elif trigger_id == 'btn-date-7d':
                start_date = data_max_date - pd.Timedelta(days=6)  # 最近7天
                end_date = data_max_date
                # 最近7天自动切换到按日模式
                period = 'day'
                day_active, week_active, month_active = True, False, False
            elif trigger_id == 'btn-date-14d':
                start_date = data_max_date - pd.Timedelta(days=13)  # 最近14天
                end_date = data_max_date
                # 最近14天自动切换到按日模式
                period = 'day'
                day_active, week_active, month_active = True, False, False
            else:
                # 日期选择器或象限选择器触发，保持当前粒度
                if day_active:
                    period = 'day'
                elif month_active:
                    period = 'month'
                else:
                    period = 'week'
                
                # 如果日期为None,使用全部数据
                if start_date is None:
                    start_date = data_min_date
                if end_date is None:
                    end_date = data_max_date
        
        print(f"\n🔄 [趋势分析] period={period}, view={view_mode}, 日期:{start_date} ~ {end_date}")
        
        # 生成趋势分析内容
        content = generate_trend_analysis_content(
            GLOBAL_DATA, 
            period=period, 
            alert_level='warning', 
            view_mode=view_mode,
            start_date=start_date,
            end_date=end_date
        )
        
        return content, day_active, week_active, month_active, start_date, end_date
        
    except Exception as e:
        print(f"❌ [趋势分析回调] 错误: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"趋势分析加载失败: {str(e)}", color="danger"), False, True, False, None, None


def create_quadrant_migration_sankey(top_products, periods, period_label):
    """创建象限迁移桑基图"""
    try:
        if not ECHARTS_AVAILABLE or len(periods) < 2:
            return html.Div()
        
        # 简化: 只看首周期 -> 末周期
        first_period = periods[0]
        last_period = periods[-1]
        
        # 统计迁移流量
        migrations = {}
        migration_details = []  # 记录迁移详情
        
        for product, quadrant_list in top_products:
            valid_quadrants = [q for q in quadrant_list if q != '无数据']
            if len(valid_quadrants) >= 2:
                from_q = valid_quadrants[0]
                to_q = valid_quadrants[-1]
                key = (from_q, to_q)
                migrations[key] = migrations.get(key, 0) + 1
                migration_details.append({
                    'product': product,
                    'from': from_q,
                    'to': to_q,
                    'changed': from_q != to_q
                })
        
        # 打印调试信息
        print(f"\n📊 [桑基图] 迁移统计:")
        print(f"   总商品数: {len(migration_details)}")
        print(f"   迁移类型数: {len(migrations)}")
        for (from_q, to_q), count in sorted(migrations.items(), key=lambda x: -x[1]):
            status = "→" if from_q != to_q else "="
            print(f"   {from_q} {status} {to_q}: {count}个")
        
        # 构建桑基图节点和链接
        nodes = []
        links = []
        node_set = set()  # 用于去重
        
        # 只添加实际出现的节点
        for (from_q, to_q), count in migrations.items():
            if count > 0:
                source_node = f'{from_q}\n(第1{period_label})'
                target_node = f'{to_q}\n(第{len(periods)}{period_label})'
                
                if source_node not in node_set:
                    nodes.append({'name': source_node})
                    node_set.add(source_node)
                
                if target_node not in node_set:
                    nodes.append({'name': target_node})
                    node_set.add(target_node)
                
                links.append({
                    'source': source_node,
                    'target': target_node,
                    'value': count
                })
        
        if not links:
            return dbc.Alert("暂无商品象限迁移数据", color="info", className="mb-3")
        
        # 创建迁移统计表格
        migration_stats = []
        for (from_q, to_q), count in sorted(migrations.items(), key=lambda x: -x[1]):
            if from_q != to_q:
                trend = "📉 恶化" if from_q.startswith('🌟') and to_q.startswith('❌') else "📈 改善" if to_q.startswith('🌟') else "🔄 变化"
            else:
                trend = "➡️ 稳定"
            
            migration_stats.append({
                '起始象限': from_q,
                '当前象限': to_q,
                '趋势': trend,
                '商品数': count
            })
        
        stats_df = pd.DataFrame(migration_stats)
        
        option = {
            'tooltip': {
                'trigger': 'item',
                'triggerOn': 'mousemove'
            },
            'series': [{
                'type': 'sankey',
                'emphasis': {
                    'focus': 'adjacency'
                },
                'nodeWidth': 20,
                'nodeGap': 15,
                'layoutIterations': 32,
                'orient': 'horizontal',
                'draggable': False,
                'data': nodes,
                'links': links,
                'lineStyle': {
                    'color': 'gradient',
                    'curveness': 0.5
                },
                'label': {
                    'fontSize': 11,
                    'color': '#000'
                }
            }]
        }
        
        return html.Div([
            html.H6(f"📊 象限迁移可视化 (TOP 20商品)", className="mb-3"),
            html.Small(f"分析周期: 第1{period_label} → 第{len(periods)}{period_label}，线条粗细表示迁移商品数量", className="text-muted d-block mb-2"),
            
            dbc.Row([
                dbc.Col([
                    DashECharts(
                        option=option,
                        style={'height': '500px', 'width': '100%'}
                    )
                ], md=8),
                
                dbc.Col([
                    html.H6("迁移统计", className="mb-2"),
                    dbc.Table.from_dataframe(
                        stats_df,
                        striped=True,
                        bordered=True,
                        hover=True,
                        size='sm'
                    )
                ], md=4)
            ]),
            
            html.Small(f"💡 提示: 稳定在同一象限的商品说明表现一致，跨象限迁移的商品需要重点关注", className="text-muted d-block mt-2")
        ])
        
    except Exception as e:
        print(f"❌ [桑基图生成] 错误: {e}")
        return html.Div()


# ==================== Tab 2 子回调: 四象限商品表格 ====================
@app.callback(
    Output('quadrant-product-table', 'children'),
    [Input('quadrant-filter', 'value'),
     Input('product-agg-data', 'data')]
)
def update_quadrant_table(quadrant_filter, product_data):
    """更新四象限商品列表"""
    if not product_data:
        return html.Div("暂无数据")
    
    try:
        df = pd.DataFrame(product_data)
        
        # 筛选
        if quadrant_filter != 'all':
            df_filtered = df[df['象限分类'] == quadrant_filter].copy()
        else:
            df_filtered = df.copy()
        
        # 按销售额排序
        df_filtered = df_filtered.sort_values('销售额', ascending=False).head(50)
        
        # 准备表格数据（✅ 增加盈利健康度字段）
        table_df = df_filtered[[
            '商品名称', '象限分类', '盈利健康度', '盈利订单占比', '利润率', '动销指数', 
            '销售额', '实际利润', '总销量', '库存', '经营建议'
        ]].copy()
        
        # 格式化
        table_df['盈利订单占比'] = table_df['盈利订单占比'].apply(lambda x: f'{x:.0f}%')
        table_df['利润率'] = table_df['利润率'].apply(lambda x: f'{x:.1f}%')
        table_df['动销指数'] = table_df['动销指数'].apply(lambda x: f'{x:.3f}')
        table_df['销售额'] = table_df['销售额'].apply(lambda x: f'¥{x:,.0f}')
        table_df['实际利润'] = table_df['实际利润'].apply(lambda x: f'¥{x:,.0f}')
        table_df['总销量'] = table_df['总销量'].apply(lambda x: f'{int(x)}件')
        table_df['库存'] = table_df['库存'].apply(lambda x: f'{int(x)}件')
        
        # 重命名列
        table_df.columns = ['商品名称', '象限', '盈利健康度', '盈利订单%', '利润率', '动销指数', 
                           '销售额', '实际利润', '销量', '库存', '💡 经营建议']
        
        table = dbc.Table.from_dataframe(
            table_df,
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            size='sm'
        )
        
        return html.Div([
            html.H5(f'商品列表（共 {len(df_filtered)} 个商品）', className="mb-3"),
            table
        ])
        
    except Exception as e:
        print(f"❌ [四象限表格] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"数据处理错误: {e}")


# ==================== Tab 2 子回调: 导出四象限数据 ====================
@app.callback(
    Output('download-quadrant-data', 'data'),
    Input('btn-export-quadrant', 'n_clicks'),
    State('product-agg-data', 'data'),
    prevent_initial_call=True
)
def export_quadrant_data(n_clicks, product_data):
    """导出四象限分析数据到Excel"""
    if not n_clicks or not product_data:
        return None
    
    try:
        df = pd.DataFrame(product_data)
        
        # 创建Excel写入器
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # Sheet 1: 全部数据
            full_data = df[[
                '商品名称', '店内码', '一级分类名', '三级分类名', '象限分类',
                '利润率', '动销指数', '销售额', '实际利润', '总销量', 
                '库存', '库存周转率', '订单数', '经营建议'
            ]].copy()
            full_data.columns = [
                '商品名称', '店内码', '一级分类', '三级分类', '象限分类',
                '利润率(%)', '动销指数', '销售额(元)', '实际利润(元)', '总销量', 
                '库存', '库存周转率', '订单数', '经营建议'
            ]
            full_data.to_excel(writer, sheet_name='全部商品', index=False)
            
            # Sheet 2-5: 各象限数据
            quadrants = [
                ('🌟 高利润高动销', '明星产品'),
                ('⚠️ 高利润低动销', '问题产品'),
                ('🚀 低利润高动销', '引流产品'),
                ('❌ 低利润低动销', '淘汰产品')
            ]
            
            for quadrant, sheet_name in quadrants:
                quad_data = df[df['象限分类'] == quadrant][[
                    '商品名称', '店内码', '一级分类名', '三级分类名',
                    '利润率', '动销指数', '销售额', '实际利润', '总销量', 
                    '库存', '库存周转率', '经营建议'
                ]].copy()
                
                if len(quad_data) > 0:
                    quad_data.columns = [
                        '商品名称', '店内码', '一级分类', '三级分类',
                        '利润率(%)', '动销指数', '销售额(元)', '实际利润(元)', '总销量', 
                        '库存', '库存周转率', '经营建议'
                    ]
                    quad_data = quad_data.sort_values('销售额(元)', ascending=False)
                    quad_data.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"✅ {sheet_name}: {len(quad_data)} 个商品")
        
        output.seek(0)
        
        return dcc.send_bytes(
            output.getvalue(),
            f"商品四象限分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
    except Exception as e:
        print(f"❌ 四象限数据导出失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# ==================== Tab 2 子回调: 商品排行图表 ====================
@app.callback(
    [Output('product-ranking-chart', 'children'),
     Output('product-ranking-table', 'children')],
    [Input('product-rank-dimension', 'value'),
     Input('product-rank-limit', 'value'),
     Input('product-agg-data', 'data')]
)
def update_product_ranking(dimension, limit, product_data):
    """更新商品排行图表和表格（✅ ECharts升级版）"""
    if not product_data:
        return html.Div("暂无数据"), html.Div()
    
    try:
        df = pd.DataFrame(product_data)
        
        # 调试信息
        print(f"\n🔍 [商品排行] 数据检查:")
        print(f"   DataFrame行数: {len(df)}")
        print(f"   DataFrame列: {df.columns.tolist()}")
        print(f"   选择维度: {dimension}")
        print(f"   显示数量: {limit}")
        
        # 检查维度是否存在
        if dimension not in df.columns:
            available_cols = df.columns.tolist()
            return html.Div([
                html.H5("⚠️ 数据字段错误", className="text-warning"),
                html.P(f"未找到字段: {dimension}"),
                html.P(f"可用字段: {', '.join(available_cols)}")
            ]), html.Div()
        
        # 检查是否有数据
        if len(df) == 0:
            return html.Div("暂无商品数据"), html.Div()
        
        # 排序并取前N名
        top_products = df.nlargest(min(limit, len(df)), dimension)
        print(f"   排序后商品数: {len(top_products)}")
        
    except Exception as e:
        print(f"❌ [商品排行] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"数据处理错误: {e}"), html.Div()
    
    # 准备数据（保留1位小数）
    product_names = top_products['商品名称'].tolist()[::-1]  # 倒序显示，最高在上
    values = [round(float(x), 1) for x in top_products[dimension].tolist()[::-1]]
    
    # 截断过长的商品名称
    product_names_display = [name[:30] + '...' if len(name) > 30 else name for name in product_names]
    
    # 维度配置
    dimension_config = {
        '销售额': {'unit': '¥', 'color': ['#4A90E2', '#7BA7D6'], 'suffix': ''},
        '实际利润': {'unit': '¥', 'color': ['#2ECC71', '#5FD68A'], 'suffix': ''},
        '利润率': {'unit': '', 'color': ['#F39C12', '#F5B041'], 'suffix': '%'},
        '总销量': {'unit': '', 'color': ['#9B59B6', '#BB8FCE'], 'suffix': '件'},
        '订单数': {'unit': '', 'color': ['#E74C3C', '#EC7063'], 'suffix': '单'}
    }
    
    config = dimension_config.get(dimension, {'unit': '', 'color': ['#4A90E2', '#7BA7D6'], 'suffix': ''})
    
    # 创建 ECharts 图表
    if ECHARTS_AVAILABLE:
        option = {
            'grid': {
                'left': '5%',
                'right': '15%',
                'top': '3%',
                'bottom': '3%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'value',
                'axisLabel': {
                    'formatter': f'{config["unit"]}{{value}}{config["suffix"]}',
                    'fontSize': 11
                },
                'splitLine': {
                    'lineStyle': {
                        'type': 'dashed',
                        'color': '#e0e0e0'
                    }
                }
            },
            'yAxis': {
                'type': 'category',
                'data': product_names_display,
                'axisLabel': {
                    'fontSize': 10,
                    'interval': 0
                },
                'axisTick': {'show': False},
                'axisLine': {'show': False}
            },
            'series': [{
                'type': 'bar',
                'data': values,
                'barWidth': '70%',
                'itemStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 1, 'y2': 0,
                        'colorStops': [
                            {'offset': 0, 'color': config['color'][0]},
                            {'offset': 1, 'color': config['color'][1]}
                        ]
                    },
                    'borderRadius': [0, 4, 4, 0]
                },
                'label': {
                    'show': True,
                    'position': 'right',
                    'formatter': f'{config["unit"]}{{c}}{config["suffix"]}',
                    'fontSize': 10,
                    'color': '#333'
                },
                'emphasis': {
                    'itemStyle': {
                        'shadowBlur': 15,
                        'shadowColor': 'rgba(0,0,0,0.3)'
                    }
                }
            }],
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {'type': 'shadow'},
                'formatter': '{b}<br/>{a0}: ' + f'{config["unit"]}{{c}}{config["suffix"]}'
            },
            'animationEasing': 'elasticOut',
            'animationDuration': 1000
        }
        
        # 用 html.Div 包装 ECharts
        # 动态计算高度：每个商品35px + 上下边距80px，但最大不超过800px
        chart_height = min(len(top_products) * 35 + 80, 800)
        
        fig = html.Div([
            html.H5(f'TOP {limit} 商品 - 按{dimension}排序', className="text-center mb-3"),
            html.Div([
                DashECharts(
                    option=option,
                    style={'height': f'{chart_height}px', 'width': '100%'}
                )
            ], style={
                'maxHeight': '800px',
                'overflowY': 'auto' if len(top_products) > 20 else 'visible'
            })
        ])
    else:
        # Plotly 备份
        plotly_fig = go.Figure()
        
        plotly_fig.add_trace(go.Bar(
            y=product_names_display,
            x=values,
            orientation='h',
            marker=dict(
                color=values,
                colorscale='Blues',
                showscale=False
            ),
            text=[f"{config['unit']}{v:.2f}{config['suffix']}" for v in values],
            textposition='outside'
        ))
        
        plotly_fig.update_layout(
            title=f'TOP {limit} 商品 - 按{dimension}排序',
            xaxis_title=f'{dimension} ({config["unit"]}{config["suffix"]})',
            yaxis_title='',
            height=max(400, limit * 25),
            margin=dict(l=200, r=50, t=50, b=50),
            hovermode='closest'
        )
        
        fig = dcc.Graph(figure=plotly_fig)
    
    # 创建详细数据表
    table_df = top_products[[
        '商品名称', '总销量', '销售额', '实际利润', '利润率', 
        '平均售价', '库存', '库存周转率', '订单数'
    ]].copy()
    
    # 格式化数值（统一保留1位小数）
    table_df['销售额'] = table_df['销售额'].apply(lambda x: f'¥{x:,.1f}')
    table_df['实际利润'] = table_df['实际利润'].apply(lambda x: f'¥{x:,.1f}')
    table_df['利润率'] = table_df['利润率'].apply(lambda x: f'{x:.1f}%')
    table_df['平均售价'] = table_df['平均售价'].apply(lambda x: f'¥{x:.1f}')
    table_df['库存周转率'] = table_df['库存周转率'].apply(lambda x: f'{x:.1f}')
    table_df['总销量'] = table_df['总销量'].apply(lambda x: f'{int(x)}件')
    table_df['订单数'] = table_df['订单数'].apply(lambda x: f'{int(x)}单')
    table_df['库存'] = table_df['库存'].apply(lambda x: f'{int(x)}件')
    
    # 重命名列
    table_df.columns = ['商品名称', '销量', '销售额', '实际利润', '利润率', 
                        '平均售价', '库存', '库存周转率', '订单数']
    
    table = dbc.Table.from_dataframe(
        table_df,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True,
        size='sm',
        className="mt-3"
    )
    
    return fig, table


# ==================== Tab 2 子回调: 分类分析图表 ====================
@app.callback(
    [Output('category-sales-chart', 'children'),
     Output('category-profit-chart', 'children')],
    Input('category-sales-data', 'data')
)
def update_category_charts(category_data):
    """更新分类分析图表（✅ ECharts升级版）"""
    if not category_data:
        # 无分类数据时显示空提示
        empty_div = html.Div([
            html.P("暂无分类数据", className="text-center text-muted", style={'padding': '50px'})
        ])
        return empty_div, empty_div
    
    df = pd.DataFrame(category_data)
    
    # ===== 1. 销售额分布饼图 =====
    if ECHARTS_AVAILABLE:
        # 准备数据（保留1位小数）
        pie_data = [
            {'value': round(float(row['销售额']), 1), 'name': row['分类']} 
            for _, row in df.iterrows()
        ]
        
        option_sales = {
            'tooltip': {
                'trigger': 'item',
                'formatter': '{b}<br/>销售额: ¥{c}<br/>占比: {d}%'
            },
            'legend': {
                'orient': 'vertical',
                'left': 'left',
                'top': 'middle',
                'textStyle': {'fontSize': 11},
                'itemGap': 8,
                'itemWidth': 20,
                'itemHeight': 14
            },
            'series': [{
                'name': '销售额',
                'type': 'pie',
                'radius': ['45%', '75%'],
                'center': ['60%', '50%'],
                'avoidLabelOverlap': True,
                'itemStyle': {
                    'borderRadius': 8,
                    'borderColor': '#fff',
                    'borderWidth': 3
                },
                'label': {
                    'show': True,
                    'position': 'outside',
                    'formatter': '{d}%',
                    'fontSize': 12,
                    'fontWeight': 'bold',
                    'color': '#333'
                },
                'labelLine': {
                    'show': True,
                    'length': 15,
                    'length2': 10,
                    'smooth': True
                },
                'emphasis': {
                    'label': {
                        'show': True,
                        'fontSize': 16,
                        'fontWeight': 'bold'
                    },
                    'itemStyle': {
                        'shadowBlur': 20,
                        'shadowOffsetX': 0,
                        'shadowColor': 'rgba(0,0,0,0.5)'
                    }
                },
                'data': pie_data
            }],
            'color': ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc']
        }
        
        fig_sales = html.Div([
            html.H5('分类销售额分布', className="text-center mb-3"),
            DashECharts(option=option_sales, style={'height': '550px', 'width': '100%'})
        ])
    else:
        # Plotly 备份
        plotly_fig = go.Figure(data=[go.Pie(
            labels=df['分类'],
            values=df['销售额'],
            hole=0.3,
            marker=dict(colors=px.colors.qualitative.Set3),
            textinfo='label+percent'
        )])
        plotly_fig.update_layout(title='分类销售额分布', height=400)
        fig_sales = dcc.Graph(figure=plotly_fig)
    
    # ===== 2. 实际利润对比柱状图 =====
    if ECHARTS_AVAILABLE:
        categories = df['分类'].tolist()
        # 保留1位小数
        profits = [round(float(x), 1) for x in df['实际利润'].tolist()]
        profit_rates = [round(float(x), 1) for x in df['利润率'].tolist()]
        
        option_profit = {
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {'type': 'shadow'},
                'formatter': '{b0}<br/>实际利润: ¥{c0}<br/>利润率: {c1}%'
            },
            'legend': {
                'data': ['实际利润', '利润率'],
                'top': '5%'
            },
            'grid': {
                'left': '3%',
                'right': '8%',
                'bottom': '3%',
                'top': '15%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'data': categories,
                'axisLabel': {
                    'rotate': 30,
                    'fontSize': 11
                }
            },
            'yAxis': [
                {
                    'type': 'value',
                    'name': '实际利润 (¥)',
                    'position': 'left',
                    'axisLabel': {'formatter': '¥{value}'}
                },
                {
                    'type': 'value',
                    'name': '利润率 (%)',
                    'position': 'right',
                    'axisLabel': {'formatter': '{value}%'}
                }
            ],
            'series': [
                {
                    'name': '实际利润',
                    'type': 'bar',
                    'data': profits,
                    'barWidth': '60%',
                    'itemStyle': {
                        'color': {
                            'type': 'linear',
                            'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                            'colorStops': [
                                {'offset': 0, 'color': '#2ECC71'},
                                {'offset': 1, 'color': '#5FD68A'}
                            ]
                        },
                        'borderRadius': [4, 4, 0, 0]
                    },
                    'label': {
                        'show': True,
                        'position': 'top',
                        'formatter': '¥{c}',
                        'fontSize': 10
                    }
                },
                {
                    'name': '利润率',
                    'type': 'line',
                    'yAxisIndex': 1,
                    'data': profit_rates,
                    'itemStyle': {'color': '#E74C3C'},
                    'lineStyle': {'width': 2},
                    'symbol': 'circle',
                    'symbolSize': 8,
                    'label': {
                        'show': True,
                        'position': 'top',
                        'formatter': '{c}%',
                        'fontSize': 10
                    }
                }
            ]
        }
        
        fig_profit = html.Div([
            html.H5('分类利润分析', className="text-center mb-3"),
            DashECharts(option=option_profit, style={'height': '500px', 'width': '100%'})
        ])
    else:
        # Plotly 备份
        plotly_fig_profit = go.Figure(data=[go.Bar(
            x=df['分类'],
            y=df['实际利润'],
            marker=dict(color=df['实际利润'], colorscale='Greens'),
            text=df['实际利润'].round(2),
            textposition='outside'
        )])
        plotly_fig_profit.update_layout(
            title='分类实际利润对比',
            xaxis_title='商品分类',
            yaxis_title='实际利润 (元)',
            height=400
        )
        fig_profit = dcc.Graph(figure=plotly_fig_profit)
    
    return fig_sales, fig_profit


# ==================== Tab 2 子回调: 商品结构分析 ====================
@app.callback(
    [Output('price-range-chart', 'children'),
     Output('abc-analysis-chart', 'children')],
    Input('product-agg-data', 'data')
)
def update_structure_charts(product_data):
    """更新商品结构分析图表（✅ ECharts升级版）"""
    if not product_data:
        empty_div = html.Div("暂无数据")
        return empty_div, empty_div
    
    df = pd.DataFrame(product_data)
    
    # ===== 1. 价格区间分析 =====
    price_bins = [0, 5, 10, 20, 50, 100, 500, float('inf')]
    price_labels = ['0-5元', '5-10元', '10-20元', '20-50元', '50-100元', '100-500元', '500元以上']
    
    df['价格区间'] = pd.cut(df['平均售价'], bins=price_bins, labels=price_labels, include_lowest=True)
    price_dist = df['价格区间'].value_counts().sort_index()
    
    if ECHARTS_AVAILABLE:
        option_price = {
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {'type': 'shadow'},
                'formatter': '{b}<br/>商品数量: {c}个'
            },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '10%',
                'top': '10%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'data': price_dist.index.astype(str).tolist(),
                'axisLabel': {
                    'rotate': 30,
                    'fontSize': 11
                }
            },
            'yAxis': {
                'type': 'value',
                'name': '商品数量',
                'axisLabel': {'formatter': '{value}个'}
            },
            'series': [{
                'type': 'bar',
                'data': price_dist.values.tolist(),
                'barWidth': '60%',
                'itemStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': '#4A90E2'},
                            {'offset': 1, 'color': '#A8D5FF'}
                        ]
                    },
                    'borderRadius': [4, 4, 0, 0]
                },
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': '{c}',
                    'fontSize': 11
                }
            }]
        }
        
        fig_price = html.Div([
            html.H5('商品价格区间分布', className="text-center mb-3"),
            DashECharts(option=option_price, style={'height': '400px', 'width': '100%'})
        ])
    else:
        # Plotly 备份
        plotly_fig_price = go.Figure(data=[go.Bar(
            x=price_dist.index.astype(str),
            y=price_dist.values,
            marker=dict(color='lightblue'),
            text=price_dist.values,
            textposition='outside'
        )])
        plotly_fig_price.update_layout(
            title='商品价格区间分布',
            xaxis_title='价格区间',
            yaxis_title='商品数量',
            height=400
        )
        fig_price = dcc.Graph(figure=plotly_fig_price)
    
    # ===== 2. ABC分类（帕累托分析） =====
    # 按销售额排序
    df_sorted = df.sort_values('销售额', ascending=False).reset_index(drop=True)
    df_sorted['累计销售额'] = df_sorted['销售额'].cumsum()
    df_sorted['累计占比'] = df_sorted['累计销售额'] / df_sorted['销售额'].sum() * 100
    
    # ABC分类
    df_sorted['ABC分类'] = 'C'
    df_sorted.loc[df_sorted['累计占比'] <= 80, 'ABC分类'] = 'A'
    df_sorted.loc[(df_sorted['累计占比'] > 80) & (df_sorted['累计占比'] <= 95), 'ABC分类'] = 'B'
    
    abc_counts = df_sorted['ABC分类'].value_counts()
    
    if ECHARTS_AVAILABLE:
        # 准备ABC数据
        abc_data = []
        for label in ['A', 'B', 'C']:
            if label in abc_counts.index:
                abc_data.append({
                    'value': int(abc_counts[label]),
                    'name': f'{label}类商品'
                })
        
        option_abc = {
            'tooltip': {
                'trigger': 'item',
                'formatter': '{b}<br/>数量: {c}<br/>占比: {d}%'
            },
            'legend': {
                'orient': 'vertical',
                'right': '5%',
                'top': 'center',
                'textStyle': {'fontSize': 12}
            },
            'series': [{
                'name': 'ABC分类',
                'type': 'pie',
                'radius': ['40%', '70%'],
                'center': ['40%', '50%'],
                'avoidLabelOverlap': True,
                'itemStyle': {
                    'borderRadius': 8,
                    'borderColor': '#fff',
                    'borderWidth': 2
                },
                'label': {
                    'show': True,
                    'formatter': '{b}\n{c}个\n({d}%)',
                    'fontSize': 11
                },
                'emphasis': {
                    'label': {
                        'show': True,
                        'fontSize': 14,
                        'fontWeight': 'bold'
                    },
                    'itemStyle': {
                        'scale': 1.1,
                        'shadowBlur': 15,
                        'shadowColor': 'rgba(0,0,0,0.3)'
                    }
                },
                'data': abc_data
            }],
            'color': ['#2ECC71', '#F39C12', '#E74C3C']  # A绿色, B橙色, C红色
        }
        
        fig_abc = html.Div([
            html.H5('ABC分类法（帕累托分析）', className="text-center mb-3"),
            html.P('A类: 80%销售额 | B类: 80-95%销售额 | C类: 95-100%销售额', 
                   className="text-center text-muted small mb-3"),
            DashECharts(option=option_abc, style={'height': '400px', 'width': '100%'})
        ])
    else:
        # Plotly 备份
        plotly_fig_abc = go.Figure(data=[go.Pie(
            labels=[f'{label}类商品' for label in abc_counts.index],
            values=abc_counts.values,
            hole=0.3,
            marker=dict(colors=['#2ECC71', '#F39C12', '#E74C3C']),
            textinfo='label+value+percent'
        )])
        plotly_fig_abc.update_layout(
            title='ABC分类法（帕累托分析）',
            height=400
        )
        fig_abc = dcc.Graph(figure=plotly_fig_abc)
    
    return fig_price, fig_abc


# ==================== Tab 2 子回调: 库存预警 ====================
@app.callback(
    Output('inventory-warning-section', 'children'),
    Input('product-agg-data', 'data')
)
def update_inventory_warnings(product_data):
    """更新库存与滞销预警"""
    if not product_data:
        return html.Div()
    
    df = pd.DataFrame(product_data)
    
    warnings = []
    
    # 1. 缺货预警
    out_of_stock = df[df['库存'] <= 0]
    if len(out_of_stock) > 0:
        warnings.append(
            dbc.Alert([
                html.H5("🔴 缺货预警", className="alert-heading"),
                html.P(f"发现 {len(out_of_stock)} 个商品缺货，可能影响销售"),
                html.Hr(),
                html.P("缺货商品列表:", className="mb-2"),
                html.Ul([html.Li(f"{row['商品名称']} (历史销量: {row['总销量']}件)") 
                        for _, row in out_of_stock.nlargest(10, '总销量').iterrows()])
            ], color="danger")
        )
    
    # 2. 滞销预警（库存高但销量低）
    df['滞销指数'] = df['库存'] / (df['总销量'] + 1)  # 避免除零
    slow_moving = df[(df['库存'] > 10) & (df['滞销指数'] > 5)].nlargest(10, '滞销指数')
    
    if len(slow_moving) > 0:
        warnings.append(
            dbc.Alert([
                html.H5("⚠️ 滞销预警", className="alert-heading"),
                html.P(f"发现 {len(slow_moving)} 个商品存在滞销风险（库存高、销量低）"),
                html.Hr(),
                html.P("滞销商品列表:", className="mb-2"),
                html.Ul([html.Li(f"{row['商品名称']} - 库存:{int(row['库存'])} / 销量:{int(row['总销量'])} (滞销指数:{row['滞销指数']:.1f})") 
                        for _, row in slow_moving.iterrows()])
            ], color="warning")
        )
    
    # 3. 低周转率预警
    low_turnover = df[(df['库存'] > 0) & (df['库存周转率'] < 0.5) & (df['库存周转率'] > 0)]
    if len(low_turnover) > 0:
        warnings.append(
            dbc.Alert([
                html.H5("📊 低周转率预警", className="alert-heading"),
                html.P(f"发现 {len(low_turnover)} 个商品周转率过低（<0.5）"),
                html.Hr(),
                html.P("建议: 考虑促销或优化库存策略", className="text-muted")
            ], color="info")
        )
    
    # 4. 畅销但库存不足
    hot_low_stock = df[(df['总销量'] > df['总销量'].quantile(0.75)) & (df['库存'] < df['库存'].quantile(0.25))]
    if len(hot_low_stock) > 0:
        warnings.append(
            dbc.Alert([
                html.H5("🔥 畅销品库存不足", className="alert-heading"),
                html.P(f"发现 {len(hot_low_stock)} 个畅销商品库存不足，建议及时补货"),
                html.Hr(),
                html.Ul([html.Li(f"{row['商品名称']} - 销量:{int(row['总销量'])} / 库存:{int(row['库存'])}") 
                        for _, row in hot_low_stock.iterrows()])
            ], color="success")
        )
    
    if not warnings:
        warnings.append(
            dbc.Alert("✅ 库存状态良好，未发现明显异常", color="success")
        )
    
    return html.Div(warnings)


# ==================== Tab 2 子回调: 导出库存预警数据 ====================
@app.callback(
    Output('download-inventory-warnings', 'data'),
    Input('btn-export-inventory-warnings', 'n_clicks'),
    State('product-agg-data', 'data'),
    prevent_initial_call=True
)
def export_inventory_warnings(n_clicks, product_data):
    """导出库存与滞销预警数据到Excel（分Sheet）"""
    if not n_clicks or not product_data:
        return None
    
    try:
        df = pd.DataFrame(product_data)
        
        # 创建Excel写入器
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # ===== Sheet 1: 缺货预警 =====
            out_of_stock = df[df['库存'] <= 0].copy()
            if len(out_of_stock) > 0:
                out_of_stock_export = out_of_stock[[
                    '商品名称', '店内码', '一级分类名', '三级分类名',
                    '总销量', '库存', '销售额', '实际利润', 
                    '利润率', '订单数', '平均售价'
                ]].sort_values('总销量', ascending=False)
                out_of_stock_export.columns = [
                    '商品名称', '店内码', '一级分类', '三级分类',
                    '历史销量', '当前库存', '销售额(元)', '实际利润(元)',
                    '利润率(%)', '订单数', '平均售价(元)'
                ]
                out_of_stock_export.to_excel(writer, sheet_name='缺货预警', index=False)
                print(f"✅ 缺货预警: {len(out_of_stock)} 个商品")
            
            # ===== Sheet 2: 滞销预警 =====
            df['滞销指数'] = df['库存'] / (df['总销量'] + 1)
            slow_moving = df[(df['库存'] > 10) & (df['滞销指数'] > 5)].copy()
            if len(slow_moving) > 0:
                slow_moving_export = slow_moving[[
                    '商品名称', '店内码', '一级分类名', '三级分类名',
                    '库存', '总销量', '滞销指数', '销售额', 
                    '实际利润', '利润率', '库存周转率'
                ]].sort_values('滞销指数', ascending=False)
                slow_moving_export.columns = [
                    '商品名称', '店内码', '一级分类', '三级分类',
                    '当前库存', '累计销量', '滞销指数', '销售额(元)',
                    '实际利润(元)', '利润率(%)', '库存周转率'
                ]
                slow_moving_export.to_excel(writer, sheet_name='滞销预警', index=False)
                print(f"✅ 滞销预警: {len(slow_moving)} 个商品")
            
            # ===== Sheet 3: 低周转率预警 =====
            low_turnover = df[(df['库存'] > 0) & (df['库存周转率'] < 0.5) & (df['库存周转率'] > 0)].copy()
            if len(low_turnover) > 0:
                low_turnover_export = low_turnover[[
                    '商品名称', '店内码', '一级分类名', '三级分类名',
                    '库存周转率', '库存', '总销量', '销售额',
                    '实际利润', '利润率'
                ]].sort_values('库存周转率')
                low_turnover_export.columns = [
                    '商品名称', '店内码', '一级分类', '三级分类',
                    '库存周转率', '当前库存', '累计销量', '销售额(元)',
                    '实际利润(元)', '利润率(%)'
                ]
                low_turnover_export.to_excel(writer, sheet_name='低周转率预警', index=False)
                print(f"✅ 低周转率预警: {len(low_turnover)} 个商品")
            
            # ===== Sheet 4: 畅销缺货预警 =====
            hot_low_stock = df[
                (df['总销量'] > df['总销量'].quantile(0.75)) & 
                (df['库存'] < df['库存'].quantile(0.25))
            ].copy()
            if len(hot_low_stock) > 0:
                hot_low_stock_export = hot_low_stock[[
                    '商品名称', '店内码', '一级分类名', '三级分类名',
                    '总销量', '库存', '库存周转率', '销售额',
                    '实际利润', '利润率', '订单数'
                ]].sort_values('总销量', ascending=False)
                hot_low_stock_export.columns = [
                    '商品名称', '店内码', '一级分类', '三级分类',
                    '累计销量', '当前库存', '库存周转率', '销售额(元)',
                    '实际利润(元)', '利润率(%)', '订单数'
                ]
                hot_low_stock_export.to_excel(writer, sheet_name='畅销缺货预警', index=False)
                print(f"✅ 畅销缺货预警: {len(hot_low_stock)} 个商品")
            
            # ===== Sheet 5: 完整商品库存数据 =====
            full_inventory = df[[
                '商品名称', '店内码', '一级分类名', '三级分类名',
                '库存', '总销量', '库存周转率', '滞销指数',
                '销售额', '成本', '实际利润', '利润率', '订单数', '平均售价', '平均成本'
            ]].copy()
            full_inventory.columns = [
                '商品名称', '店内码', '一级分类', '三级分类',
                '当前库存', '累计销量', '库存周转率', '滞销指数',
                '销售额(元)', '成本(元)', '实际利润(元)', '利润率(%)', 
                '订单数', '平均售价(元)', '平均成本(元)'
            ]
            full_inventory = full_inventory.sort_values('库存周转率', ascending=False)
            full_inventory.to_excel(writer, sheet_name='完整库存数据', index=False)
            print(f"✅ 完整库存数据: {len(full_inventory)} 个商品")
        
        output.seek(0)
        
        return dcc.send_bytes(
            output.getvalue(),
            f"库存与滞销预警_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        
    except Exception as e:
        print(f"❌ 库存预警导出失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# ==================== Tab 5: 时段场景分析 辅助函数 ====================

def extract_time_features_for_scenario(df: pd.DataFrame) -> pd.DataFrame:
    """
    提取时间特征用于场景分析
    ✅ 使用统一的scene_inference模块（与Tab 4保持一致）
    """
    df = df.copy()
    
    # ✅ 调用统一的场景推断模块（与Tab 4、数据加载时保持完全一致）
    if '时段' not in df.columns or '场景' not in df.columns:
        df = add_scene_and_timeslot_fields(df)
    
    return df


def calculate_period_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """计算时段指标（与Tab 1/Tab 2保持一致的计算逻辑）"""
    period_order = ['清晨(6-9点)', '上午(9-12点)', '正午(12-14点)', '下午(14-18点)',
                   '傍晚(18-21点)', '晚间(21-24点)', '深夜(0-3点)', '凌晨(3-6点)']
    metrics = []
    for period in period_order:
        period_df = df[df['时段'] == period]
        if len(period_df) == 0:
            continue
        
        order_count = period_df['订单ID'].nunique()
        item_count = len(period_df)
        
        # 🔧 修复: 按订单ID分组汇总,避免多商品订单重复计算
        # 销售额: 按订单汇总后再求和
        # ⚠️ 关键修复：实收价格是单价，需要先乘以销量再聚合
        sales_col = '月售' if '月售' in period_df.columns else '销量'
        if sales_col in period_df.columns:
            period_df_temp = period_df.copy()
            period_df_temp['订单总收入'] = period_df_temp['实收价格'] * period_df_temp[sales_col]
            order_sales = period_df_temp.groupby('订单ID')['订单总收入'].sum()
        else:
            order_sales = period_df.groupby('订单ID')['实收价格'].sum()
        total_sales = order_sales.sum()
        avg_order_value = order_sales.mean() if len(order_sales) > 0 else 0
        
        # 利润额: 按订单汇总
        if '实际利润' in period_df.columns:
            total_profit = period_df.groupby('订单ID')['实际利润'].sum().sum()
        elif '利润额' in period_df.columns:
            total_profit = period_df.groupby('订单ID')['利润额'].sum().sum()
        else:
            total_profit = 0
        
        # 利润率计算
        profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
        
        metrics.append({
            '时段': period,
            '订单量': order_count,
            '商品数': item_count,
            '销售额': total_sales,
            '平均客单价': avg_order_value,
            '利润额': total_profit,
            '利润率': profit_rate
        })
    
    return pd.DataFrame(metrics)


def calculate_scenario_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """计算场景指标(🔧 修复:按订单ID分组避免重复计算)"""
    
    metrics = []
    for scenario in df['场景'].unique():
        scenario_df = df[df['场景'] == scenario]
        
        order_count = scenario_df['订单ID'].nunique()
        product_count = scenario_df['商品名称'].nunique()
        item_count = len(scenario_df)
        
        # 🔧 修复: 按订单ID分组汇总销售额
        # ⚠️ 关键修复：实收价格是单价，需要先乘以销量再聚合
        sales_col = '月售' if '月售' in scenario_df.columns else '销量'
        if sales_col in scenario_df.columns:
            scenario_df_temp = scenario_df.copy()
            scenario_df_temp['订单总收入'] = scenario_df_temp['实收价格'] * scenario_df_temp[sales_col]
            order_sales = scenario_df_temp.groupby('订单ID')['订单总收入'].sum()
        else:
            order_sales = scenario_df.groupby('订单ID')['实收价格'].sum()
        total_sales = order_sales.sum()
        avg_order_value = order_sales.mean() if len(order_sales) > 0 else 0
        
        # 🔧 修复: 按订单ID分组汇总利润额
        if '实际利润' in scenario_df.columns:
            total_profit = scenario_df.groupby('订单ID')['实际利润'].sum().sum()
        elif '利润额' in scenario_df.columns:
            total_profit = scenario_df.groupby('订单ID')['利润额'].sum().sum()
        else:
            total_profit = 0
        
        # 利润率计算
        profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
        
        metrics.append({
            '场景': scenario,
            '订单量': order_count,
            '商品数': item_count,
            '销售额': total_sales,
            '平均客单价': avg_order_value,
            '利润额': total_profit,
            '利润率': profit_rate
        })
    
    scenario_metrics = pd.DataFrame(metrics)
    
    return scenario_metrics.sort_values('销售额', ascending=False)


# ==================== Tab 3-7 占位符 ====================


@app.callback(
    Output('tab-3-content', 'children'),
    Input('main-tabs', 'value')
)
def render_tab3_content(active_tab):
    if active_tab != 'tab-3':
        raise PreventUpdate
    return dbc.Alert("💰 价格对比分析功能开发中...", color="info", className="text-center")


# Tab 3.5: 成本优化分析
@app.callback(
    Output('tab-cost-content', 'children'),
    [Input('main-tabs', 'value'),
     Input('data-update-trigger', 'data')]
)
def render_cost_optimization_tab(active_tab, trigger):
    """渲染成本优化分析Tab"""
    if active_tab != 'tab-cost-optimization':
        raise PreventUpdate
    
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return dbc.Container([
            dbc.Alert("⚠️ 未找到数据，请检查数据文件", color="warning")
        ])
    
    df = GLOBAL_DATA.copy()
    
    # 计算订单指标
    try:
        order_agg = calculate_order_metrics(df)
    except ValueError as e:
        return dbc.Container([
            dbc.Alert(f"❌ {str(e)}", color="danger")
        ])
    
    # 执行成本优化分析
    cost_analysis = analyze_cost_optimization(df, order_agg)
    
    # 计算总体成本占比
    total_sales = order_agg['实收价格'].sum()
    total_profit = order_agg['订单实际利润'].sum()
    profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
    
    product_cost_rate = cost_analysis['product_cost_analysis']['avg_cost_rate']
    logistics_cost_rate = cost_analysis['logistics_cost_analysis']['logistics_cost_rate']
    marketing_cost_rate = cost_analysis['marketing_cost_analysis']['marketing_cost_rate']
    
    return html.Div([
        html.H3("💡 成本优化分析", className="mb-4"),
        html.P("深度分析成本结构,识别优化机会,提升盈利能力", className="text-muted mb-4"),
        
        # 成本结构概览
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📊 综合利润率", className="card-title"),
                        html.H3(f"{profit_rate:.2f}%", className="text-primary mb-2"),
                        html.P("利润 / 商品销售额", className="text-muted small")
                    ])
                ], className="modern-card text-center shadow-sm")  # 🎨 添加modern-card
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📦 商品成本占比", className="card-title"),
                        html.H3(f"{product_cost_rate:.2f}%", 
                               className="text-danger" if product_cost_rate > 70 else "text-success"),
                        html.P(f"基准: ≤70%", className="text-muted small")
                    ])
                ], className="modern-card text-center shadow-sm")  # 🎨 添加modern-card
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("🚚 履约成本占比", className="card-title"),
                        html.H3(f"{logistics_cost_rate:.2f}%", 
                               className="text-danger" if logistics_cost_rate > 15 else "text-success"),
                        html.P(f"基准: ≤15%", className="text-muted small")
                    ])
                ], className="modern-card text-center shadow-sm")  # 🎨 添加modern-card
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📢 营销成本占比", className="card-title"),
                        html.H3(f"{marketing_cost_rate:.2f}%", 
                               className="text-danger" if marketing_cost_rate > 10 else "text-success"),
                        html.P(f"基准: ≤10%", className="text-muted small")
                    ])
                ], className="modern-card text-center shadow-sm")  # 🎨 添加modern-card
            ], md=3),
        ], className="mb-4"),
        
        # 三个优化分析子模块
        dbc.Tabs([
            # 1. 商品成本优化
            dbc.Tab(label="📦 商品成本优化", children=[
                html.Div([
                    render_product_cost_optimization(cost_analysis['product_cost_analysis'])
                ], className="p-3")
            ]),
            
            # 2. 履约成本优化
            dbc.Tab(label="🚚 履约成本优化", children=[
                html.Div([
                    render_logistics_cost_optimization(cost_analysis['logistics_cost_analysis'])
                ], className="p-3")
            ]),
            
            # 3. 营销成本优化
            dbc.Tab(label="📢 营销成本优化", children=[
                html.Div([
                    render_marketing_cost_optimization(cost_analysis['marketing_cost_analysis'])
                ], className="p-3")
            ]),
        ])
    ])


def render_product_cost_optimization(analysis: Dict):
    """渲染商品成本优化分析"""
    if analysis is None:
        return dbc.Alert("暂无商品成本数据", color="info")
    
    high_cost_products = analysis['high_cost_products']
    avg_cost_rate = analysis['avg_cost_rate']
    problem_products = analysis['problem_products']
    
    return html.Div([
        html.H5("📦 商品成本优化分析", className="mb-3"),
        
        # 问题概述
        dbc.Alert([
            html.H6("🎯 优化目标", className="alert-heading"),
            html.Hr(),
            html.P(f"平均商品成本占比: {avg_cost_rate:.2f}%", className="mb-1"),
            html.P(f"发现 {problem_products} 个高成本商品（成本占比>70%且销量较高）", className="mb-1"),
            html.P("建议: 优化采购价格、调整售价或替换供应商", className="mb-0 fw-bold text-danger")
        ], color="warning" if avg_cost_rate > 70 else "success"),
        
        # 高成本商品列表
        html.H6("🔍 高成本商品明细（Top 20）", className="mt-4 mb-3"),
        
        dbc.Table.from_dataframe(
            high_cost_products[[
                '商品名称', '商品实售价', '商品采购成本', '成本占比', '毛利率', '月售'
            ]].round(2),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            size='sm'
        ) if not high_cost_products.empty else dbc.Alert("✅ 暂无高成本商品", color="success"),
        
        # 优化建议
        dbc.Card([
            dbc.CardHeader("💡 优化建议"),
            dbc.CardBody([
                html.Ul([
                    html.Li("优先优化销量高、成本占比高的商品"),
                    html.Li("与供应商协商批量采购折扣"),
                    html.Li("考虑提高售价（基于竞品定价）"),
                    html.Li("寻找替代供应商或商品"),
                    html.Li("适当减少高成本低毛利商品的备货")
                ])
            ])
        ], className="mt-3")
    ])


def render_logistics_cost_optimization(analysis: Dict):
    """渲染履约成本优化分析"""
    if analysis is None:
        return dbc.Alert("暂无履约成本数据", color="info")
    
    # 检查是否有履约数据
    if not analysis.get('has_logistics_data', False):
        return dbc.Alert([
            html.H6("📊 履约成本数据缺失", className="alert-heading"),
            html.Hr(),
            html.P("当前数据中未找到履约成本相关字段（配送费成本/物流配送费等）", className="mb-0"),
            html.P("建议: 上传包含完整配送费用数据的订单明细", className="mb-0 mt-2")
        ], color="warning")
    
    logistics_cost_rate = analysis['logistics_cost_rate']
    total_logistics_cost = analysis['total_logistics_cost']
    distance_stats = analysis['distance_stats']
    use_full_formula = analysis.get('use_full_formula', False)
    
    return html.Div([
        html.H5("🚚 履约成本优化分析", className="mb-3"),
        
        # 成本概况
        dbc.Alert([
            html.H6("📊 履约成本概况", className="alert-heading"),
            html.Hr(),
            html.P(f"履约净成本: ¥{total_logistics_cost:,.2f}", className="mb-1"),
            html.P(f"履约成本占比: {logistics_cost_rate:.2f}%", className="mb-1"),
            html.P(f"健康基准: ≤15%", className="mb-1"),
            html.Hr(),
            html.Small([
                "📐 计算公式: ",
                html.Code("用户支付配送费 - 配送费减免 - 物流配送费" if use_full_formula else "物流配送费"),
                html.Br(),
                html.I("(反映商家在配送环节的实际收支)" if use_full_formula else "(仅统计配送支出,未扣除用户支付)")
            ], className="text-muted"),
            html.P("建议: 提高起送金额、优化配送范围、减少低客单价订单", 
                  className="mb-0 fw-bold text-danger mt-2") if logistics_cost_rate > 15 else None
        ], color="warning" if logistics_cost_rate > 15 else "success"),
        
        # 配送距离分析
        html.H6("📍 按配送距离分析", className="mt-4 mb-3"),
        
        dbc.Table.from_dataframe(
            distance_stats[[
                '距离分组', '订单数', '销售额', '配送成本', '成本占比', '平均客单价'
            ]].round(2),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            size='sm'
        ) if distance_stats is not None and not distance_stats.empty else dbc.Alert("暂无配送距离数据", color="info"),
        
        # 优化建议
        dbc.Card([
            dbc.CardHeader("💡 优化建议"),
            dbc.CardBody([
                html.Ul([
                    html.Li("提高起送金额（建议≥30元），减少低客单价订单"),
                    html.Li("优化配送范围，限制远距离低客单价订单"),
                    html.Li("设置配送费阶梯（距离越远配送费越高）"),
                    html.Li("引导用户自提或合并订单"),
                    html.Li("与第三方配送平台协商降低配送费")
                ])
            ])
        ], className="mt-3")
    ])


def render_marketing_cost_optimization(analysis: Dict):
    """渲染营销成本优化分析"""
    if analysis is None:
        return dbc.Alert("暂无营销成本数据", color="info")
    
    marketing_cost_rate = analysis['marketing_cost_rate']
    marketing_roi = analysis['marketing_roi']
    marketing_breakdown = analysis['marketing_breakdown']
    channel_stats = analysis['channel_stats']
    
    return html.Div([
        html.H5("📢 营销成本优化分析", className="mb-3"),
        
        # 营销成本概况
        dbc.Alert([
            html.H6("📊 营销成本概况", className="alert-heading"),
            html.Hr(),
            html.P(f"营销成本占比: {marketing_cost_rate:.2f}%", className="mb-1"),
            html.P(f"营销ROI: {marketing_roi:.2f}x (每投入1元产生{marketing_roi:.2f}元销售额)", className="mb-1"),
            html.P(f"健康基准: ≤10%, ROI≥10x", className="mb-0"),
            html.P("建议: 停止低ROI活动、提高活动门槛、精准投放", 
                  className="mb-0 fw-bold text-danger mt-2") if marketing_cost_rate > 10 or marketing_roi < 10 else None
        ], color="warning" if marketing_cost_rate > 10 else "success"),
        
        # 营销成本构成
        html.H6("💰 营销成本构成", className="mt-4 mb-3"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6(key, className="card-title"),
                        html.H4(f"¥{value:,.2f}", className="text-primary")
                    ])
                ], className="modern-card text-center shadow-sm mb-2")  # 🎨 添加modern-card
            ], md=3) for key, value in marketing_breakdown.items()
        ]),
        
        # 按渠道分析
        html.H6("📱 按渠道营销效率分析", className="mt-4 mb-3"),
        
        dbc.Table.from_dataframe(
            channel_stats[[
                '渠道', '销售额', '营销成本', '营销成本占比', '营销ROI', '订单数'
            ]].round(2),
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            size='sm'
        ) if channel_stats is not None and not channel_stats.empty else dbc.Alert("暂无渠道数据", color="info"),
        
        # 优化建议
        dbc.Card([
            dbc.CardHeader("💡 优化建议"),
            dbc.CardBody([
                html.Ul([
                    html.Li("立即停止ROI<10的营销活动"),
                    html.Li("提高满减门槛（建议满50减5，而非满30减5）"),
                    html.Li("减少商品折扣，改为赠品或积分"),
                    html.Li("代金券设置使用门槛（如满80可用）"),
                    html.Li("精准投放：针对高价值客户发券"),
                    html.Li("A/B测试不同营销策略的效果")
                ])
            ])
        ], className="mt-3")
    ])


@app.callback(
    Output('tab-5-content', 'children'),
    Input('main-tabs', 'value')
)
def render_tab5_content(active_tab):
    """Tab 5: 时段场景分析"""
    if active_tab != 'tab-5':
        raise PreventUpdate
    
    try:
        df = GLOBAL_DATA.copy()
        
        if df is None or len(df) == 0:
            return dbc.Alert("📊 暂无数据，请先上传数据", color="warning", className="text-center")
        
        # 提取时间特征
        df = extract_time_features_for_scenario(df)
        
        # 创建布局
        layout = html.Div([
            # 页面标题
            dbc.Row([
                dbc.Col([
                    html.H3([
                        html.I(className="bi bi-clock-history me-2"),
                        "时段场景营销分析"
                    ], className="text-primary mb-4"),
                    html.P("通过时段、场景、客单价等多维度分析,发现黄金销售时段,优化营销策略", 
                          className="text-muted")
                ])
            ], className="mb-4"),
            
            # Tab导航
            dbc.Tabs([
                # 1. 时段分析
                dbc.Tab(label="⏰ 时段订单分析", tab_id="period-analysis", children=[
                    html.Div(id='period-analysis-content', className="p-3")
                ]),
                
                # 2. 场景分析
                dbc.Tab(label="🎯 消费场景分析", tab_id="scenario-analysis", children=[
                    html.Div(id='scenario-analysis-content', className="p-3")
                ]),
                
                
                # 4. AI智能建议
                dbc.Tab(label="🤖 AI营销建议", tab_id="ai-suggestions", children=[
                    html.Div(id='ai-suggestions-content', className="p-3")
                ]),
                
                # ========== 新增扩展子Tab ==========
                # 4. 场景利润矩阵 (时段热力图 + 四象限分析)
                dbc.Tab(label="🔥 场景利润矩阵", tab_id="heatmap-profit", children=[
                    html.Div(id='heatmap-profit-content', className="p-3")
                ]),
                
                # 5. 时段销量趋势 + 客单价探索
                dbc.Tab(label="📈 趋势&客单价", tab_id="trend-price", children=[
                    html.Div(id='trend-price-content', className="p-3")
                ]),
                
                # 6. 商品场景关联网络
                dbc.Tab(label="🕸️ 商品场景关联", tab_id="product-network", children=[
                    html.Div(id='product-network-content', className="p-3")
                ]),
                
                # 7. 商品场景画像
                dbc.Tab(label="🏷️ 商品场景画像", tab_id="product-profile", children=[
                    html.Div(id='product-profile-content', className="p-3")
                ])
            ], id='tab5-subtabs', active_tab='period-analysis'),
            
            # 子Tab内容容器
            html.Div(id='tab5-subtab-content')
        ])
        
        return layout
        
    except Exception as e:
        print(f"❌ Tab 5渲染失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"渲染失败: {str(e)}", color="danger")


# ==================== Tab 5 子Tab回调 ====================

@app.callback(
    Output('tab5-subtab-content', 'children'),
    Input('tab5-subtabs', 'active_tab'),
    Input('main-tabs', 'value')
)
def render_tab5_subtab_content(active_subtab, main_tab):
    """渲染Tab 5的子Tab内容"""
    if main_tab != 'tab-5':
        raise PreventUpdate
    
    try:
        df = GLOBAL_DATA.copy()
        if df is None or len(df) == 0:
            return dbc.Alert("暂无数据", color="warning")
        
        print(f"🔍 Tab5 渲染: active_subtab={active_subtab}, 数据行数={len(df)}")
        
        df = extract_time_features_for_scenario(df)
        print(f"   时间特征提取后: 数据行数={len(df)}, 字段={list(df.columns)}")
        
        # 原有4个基础子Tab
        if active_subtab == 'period-analysis':
            print("   → 进入 period-analysis 分支")
            result = render_period_analysis(df)
            print(f"   ← period-analysis 返回: {type(result)}")
            return result
        elif active_subtab == 'scenario-analysis':
            print("   → 进入 scenario-analysis 分支")
            result = render_scenario_analysis(df)
            print(f"   ← scenario-analysis 返回: {type(result)}")
            return result
        elif active_subtab == 'ai-suggestions':
            return render_ai_marketing_suggestions(df)
        
        # 新增4个扩展子Tab (需要Tab 5扩展渲染模块)
        elif active_subtab == 'heatmap-profit':
            if TAB5_EXTENDED_RENDERS_AVAILABLE:
                return render_heatmap_profit_matrix(df)
            else:
                return dbc.Alert([
                    html.H5("⚠️ 功能不可用", className="alert-heading"),
                    html.P("热力图和利润矩阵功能需要 Tab 5 扩展渲染模块。"),
                    html.Hr(),
                    html.Small("请确保 'tab5_extended_renders.py' 文件存在。")
                ], color="warning")
        
        elif active_subtab == 'trend-price':
            if TAB5_EXTENDED_RENDERS_AVAILABLE:
                return render_trend_price_analysis(df)
            else:
                return dbc.Alert([
                    html.H5("⚠️ 功能不可用", className="alert-heading"),
                    html.P("趋势和客单价分析功能需要 Tab 5 扩展渲染模块。"),
                    html.Hr(),
                    html.Small("请确保 'tab5_extended_renders.py' 文件存在。")
                ], color="warning")
        
        elif active_subtab == 'product-network':
            if TAB5_EXTENDED_RENDERS_AVAILABLE:
                return render_product_scene_network(df)
            else:
                return dbc.Alert([
                    html.H5("⚠️ 功能不可用", className="alert-heading"),
                    html.P("商品场景关联网络功能需要 Tab 5 扩展渲染模块。"),
                    html.Hr(),
                    html.Small("请确保 'tab5_extended_renders.py' 文件存在。")
                ], color="warning")
        
        elif active_subtab == 'product-profile':
            if TAB5_EXTENDED_RENDERS_AVAILABLE:
                return render_product_scene_profile(df)
            else:
                return dbc.Alert([
                    html.H5("⚠️ 功能不可用", className="alert-heading"),
                    html.P("商品场景画像功能需要 Tab 5 扩展渲染模块。"),
                    html.Hr(),
                    html.Small("请确保 'tab5_extended_renders.py' 文件存在。")
                ], color="warning")
        
        return html.Div()
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        
        print("=" * 80)
        print(f"❌ Tab 5子Tab渲染失败: {type(e).__name__}: {e}")
        print("=" * 80)
        print(error_trace)
        print("=" * 80)
        
        return dbc.Alert([
            html.H4("⚠️ Tab 5 渲染失败", className="alert-heading"),
            html.P([
                html.Strong("错误类型: "), f"{type(e).__name__}"
            ]),
            html.P([
                html.Strong("错误信息: "), str(e)
            ]),
            html.P([
                html.Strong("当前子Tab: "), active_subtab
            ]),
            html.Hr(),
            html.Details([
                html.Summary("📋 点击查看完整错误堆栈", style={'cursor': 'pointer', 'color': '#721c24'}),
                html.Pre(error_trace, style={
                    'fontSize': '11px',
                    'maxHeight': '400px',
                    'overflow': 'auto',
                    'backgroundColor': '#f8f9fa',
                    'padding': '10px',
                    'marginTop': '10px'
                })
            ])
        ], color="danger")


def render_period_analysis(df: pd.DataFrame):
    """1. 时段订单分析"""
    print(f"  🕒 render_period_analysis 开始: df.shape={df.shape}")
    
    try:
        period_metrics = calculate_period_metrics(df)
        print(f"     period_metrics 计算成功: {len(period_metrics)} 行")
    except Exception as e:
        print(f"     ❌ period_metrics 计算失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"时段指标计算失败: {str(e)}", color="danger")
    
    # 时段顺序
    period_order = ['清晨(6-9点)', '上午(9-12点)', '正午(12-14点)', '下午(14-18点)',
                   '傍晚(18-21点)', '晚间(21-24点)', '深夜(0-3点)', '凌晨(3-6点)']
    
    # 按时段订单量排序
    order_by_period = df.groupby('时段')['订单ID'].nunique().reindex(period_order, fill_value=0)
    
    # 按时段客单价
    period_avg_price = period_metrics.set_index('时段')['平均客单价'].reindex(period_order, fill_value=0)
    
    # 找出峰谷（添加空值检查）
    if len(order_by_period) > 0:
        peak_period = order_by_period.idxmax()
        peak_orders = order_by_period.max()
        low_period = order_by_period.idxmin()
        low_orders = order_by_period.min()
    else:
        peak_period = low_period = '未知'
        peak_orders = low_orders = 0
    
    if len(period_avg_price) > 0 and period_avg_price.max() > 0:
        high_value_period = period_avg_price.idxmax()
        high_value = period_avg_price.max()
    else:
        high_value_period = '未知'
        high_value = 0
    
    layout = html.Div([
        # 关键指标卡片
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("🔥 高峰时段", className="text-primary mb-2"),
                        html.H4(peak_period, className="mb-1"),
                        html.P(f"{peak_orders:,} 订单", className="text-muted mb-0")
                    ])
                ], className="modern-card shadow-sm border-primary")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📉 低谷时段", className="text-warning mb-2"),
                        html.H4(low_period, className="mb-1"),
                        html.P(f"{low_orders:,} 订单", className="text-muted mb-0")
                    ])
                ], className="modern-card shadow-sm border-warning")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("💰 高价值时段", className="text-success mb-2"),
                        html.H4(high_value_period, className="mb-1"),
                        html.P(f"¥{high_value:.2f} 客单价", className="text-muted mb-0")
                    ])
                ], className="modern-card shadow-sm border-success")
            ], md=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📊 峰谷差异", className="text-info mb-2"),
                        html.H4(f"{(peak_orders/low_orders - 1)*100:.0f}%", className="mb-1"),
                        html.P(f"相差 {peak_orders - low_orders:,} 单", className="text-muted mb-0")
                    ])
                ], className="modern-card shadow-sm border-info")
            ], md=3)
        ], className="mb-4"),
        
        # 图表行
        dbc.Row([
            # 左侧: 订单量分布
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📊 分时段订单量分布"),
                    dbc.CardBody([
                        render_period_orders_chart(order_by_period) if ECHARTS_AVAILABLE
                        else render_period_orders_chart_plotly(order_by_period)
                    ])
                ], className="shadow-sm")
            ], md=6),
            
            # 右侧: 客单价趋势
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("💰 分时段平均客单价趋势"),
                    dbc.CardBody([
                        render_period_price_chart(period_avg_price) if ECHARTS_AVAILABLE
                        else render_period_price_chart_plotly(period_avg_price)
                    ])
                ], className="shadow-sm")
            ], md=6)
        ], className="mb-4"),
        
        # 详细数据表
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📋 分时段营销指标详情"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            data=period_metrics.to_dict('records'),
                            columns=[
                                {'name': '时段', 'id': '时段'},
                                {'name': '订单量', 'id': '订单量', 'type': 'numeric', 'format': {'specifier': ','}},
                                {'name': '商品数', 'id': '商品数', 'type': 'numeric', 'format': {'specifier': ','}},
                                {'name': '销售额', 'id': '销售额', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                                {'name': '平均客单价', 'id': '平均客单价', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                                {'name': '利润率', 'id': '利润率', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                            ],
                            # ✨ 性能优化: 启用虚拟化和分页
                            virtualization=True,
                            page_action='native',
                            page_current=0,
                            page_size=20,
                            style_table={'height': '400px', 'overflowY': 'auto'},
                            style_data_conditional=[
                                {
                                    'if': {'filter_query': '{订单量} = ' + str(int(period_metrics['订单量'].max()))},
                                    'backgroundColor': '#d4edda',
                                    'fontWeight': 'bold'
                                }
                            ],
                            style_cell={'textAlign': 'center'},
                            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'}
                        )
                    ])
                ], className="shadow-sm")
            ])
        ], className="mb-4"),
        
        # 营销建议
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H5([html.I(className="bi bi-lightbulb me-2"), "🎯 营销建议"], className="mb-3"),
                    html.Ul([
                        html.Li([html.Strong("低峰时段促销: "), f"在 {low_period} 加大折扣力度，推出'限时特惠'吸引订单"]),
                        html.Li([html.Strong("高峰时段提价: "), f"在 {peak_period} 减少促销，提升利润率，可推出高价值套餐"]),
                        html.Li([html.Strong("高价值时段: "), f"在 {high_value_period} 推荐高利润商品，提升客单价"]),
                        html.Li([html.Strong("定时推送: "), "提前30分钟推送下一时段优惠券，引导提前下单"])
                    ])
                ], color="info", className="shadow-sm")
            ])
        ])
    ])
    
    return layout


def render_scenario_analysis(df: pd.DataFrame):
    """2. 消费场景分析"""
    print(f"  🎯 render_scenario_analysis 开始: df.shape={df.shape}")
    
    try:
        scenario_metrics = calculate_scenario_metrics(df)
        print(f"     scenario_metrics 计算成功: {len(scenario_metrics)} 行")
    except Exception as e:
        print(f"     ❌ scenario_metrics 计算失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"场景指标计算失败: {str(e)}", color="danger")
    
    # 场景订单分布
    scenario_orders = df.groupby('场景')['订单ID'].nunique().sort_values(ascending=False)
    
    # 找出主要场景（添加空值检查）
    if len(scenario_orders) > 0:
        top_scenario = scenario_orders.idxmax()
        top_scenario_orders = scenario_orders.max()
        top_scenario_ratio = (top_scenario_orders / scenario_orders.sum() * 100)
    else:
        top_scenario = '未知'
        top_scenario_orders = 0
        top_scenario_ratio = 0
    
    layout = html.Div([
        # 场景定义说明
        dbc.Alert([
            html.H5([html.I(className="bi bi-info-circle me-2"), "📖 消费场景定义说明"], className="mb-3"),
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Strong("🍳 早餐: "),
                        html.Span("豆浆、油条、包子、粥、煎饼、鸡蛋、面包、牛奶、燕麦等", className="text-muted")
                    ], md=6),
                    dbc.Col([
                        html.Strong("🍱 午餐: "),
                        html.Span("便当、盒饭、套餐、炒饭、炒面、拉面、米饭等", className="text-muted")
                    ], md=6)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([
                        html.Strong("🍽️ 晚餐: "),
                        html.Span("晚饭、炒菜、烧烤等", className="text-muted")
                    ], md=6),
                    dbc.Col([
                        html.Strong("🌙 夜宵: "),
                        html.Span("宵夜、烧烤、串串、小龙虾、啤酒等", className="text-muted")
                    ], md=6)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([
                        html.Strong("☕ 下午茶: "),
                        html.Span("咖啡、奶茶、蛋糕、甜品、冰淇淋、饮料等", className="text-muted")
                    ], md=6),
                    dbc.Col([
                        html.Strong("🍿 休闲零食: "),
                        html.Span("薯片、饼干、糖果、巧克力、坚果、果冻、瓜子等", className="text-muted")
                    ], md=6)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([
                        html.Strong("🧻 日用补充: "),
                        html.Span("纸巾、洗衣液、洗洁精、牙膏、香皂、洗发水等", className="text-muted")
                    ], md=6),
                    dbc.Col([
                        html.Strong("🆘 应急购买: "),
                        html.Span("电池、充电器、雨伞、口罩、创可贴等", className="text-muted")
                    ], md=6)
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([
                        html.Strong("💊 营养补充: "),
                        html.Span("维生素、蛋白粉、钙片、保健品等", className="text-muted")
                    ], md=6),
                    dbc.Col([
                        html.Strong("🛒 日常购物: "),
                        html.Span("未匹配上述关键词的通用商品", className="text-muted")
                    ], md=6)
                ])
            ]),
            html.Hr(),
            html.Small([
                html.I(className="bi bi-lightbulb me-1"),
                "场景识别优先级: 商品名称关键词 > 商品分类映射 > 默认分类"
            ], className="text-muted")
        ], color="info", className="mb-4"),
        
        # 关键指标
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("🎯 主要场景", className="text-primary mb-2"),
                        html.H4(top_scenario, className="mb-1"),
                        html.P(f"{top_scenario_ratio:.1f}% 订单占比", className="text-muted mb-0")
                    ])
                ], className="modern-card shadow-sm border-primary")
            ], md=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📊 场景数量", className="text-info mb-2"),
                        html.H4(f"{len(scenario_orders)}", className="mb-1"),
                        html.P("个消费场景", className="text-muted mb-0")
                    ])
                ], className="modern-card shadow-sm border-info")
            ], md=4),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("💰 场景客单价", className="text-success mb-2"),
                        html.H4(f"¥{scenario_metrics['平均客单价'].mean():.2f}", className="mb-1"),
                        html.P("平均值", className="text-muted mb-0")
                    ])
                ], className="modern-card shadow-sm border-success")
            ], md=4)
        ], className="mb-4"),
        
        # 图表
        dbc.Row([
            # 场景订单分布
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🎯 消费场景订单分布"),
                    dbc.CardBody([
                        render_scenario_orders_chart(scenario_orders) if ECHARTS_AVAILABLE
                        else render_scenario_orders_chart_plotly(scenario_orders)
                    ])
                ], className="shadow-sm")
            ], md=6),
            
            # 场景销售额对比
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("💰 各场景销售额对比"),
                    dbc.CardBody([
                        render_scenario_sales_chart(scenario_metrics) if ECHARTS_AVAILABLE
                        else render_scenario_sales_chart_plotly(scenario_metrics)
                    ])
                ], className="shadow-sm")
            ], md=6)
        ], className="mb-4"),
        
        # 详细数据表
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📋 消费场景详细指标"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            data=scenario_metrics.to_dict('records'),
                            columns=[
                                {'name': '场景', 'id': '场景'},
                                {'name': '订单量', 'id': '订单量', 'type': 'numeric', 'format': {'specifier': ','}},
                                {'name': '商品数', 'id': '商品数', 'type': 'numeric', 'format': {'specifier': ','}},
                                {'name': '销售额', 'id': '销售额', 'type': 'numeric', 'format': {'specifier': ',.1f'}},
                                {'name': '平均客单价', 'id': '平均客单价', 'type': 'numeric', 'format': {'specifier': ',.1f'}},
                                {'name': '利润率', 'id': '利润率', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                            ],
                            # ✨ 性能优化: 启用虚拟化和分页
                            virtualization=True,
                            page_action='native',
                            page_current=0,
                            page_size=15,
                            style_table={'height': '400px', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'center'},
                            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                            style_data_conditional=[
                                {
                                    'if': {'column_id': '利润率', 'filter_query': '{利润率} >= 30'},
                                    'backgroundColor': '#d4edda',
                                    'color': '#155724'
                                },
                                {
                                    'if': {'column_id': '利润率', 'filter_query': '{利润率} < 20'},
                                    'backgroundColor': '#f8d7da',
                                    'color': '#721c24'
                                }
                            ]
                        )
                    ])
                ], className="shadow-sm")
            ])
        ])
    ])
    
    return layout


def render_cross_analysis(df: pd.DataFrame):
    """3. 时段×场景交叉分析"""
    # 创建交叉透视表
    cross_orders = pd.pivot_table(
        df,
        values='订单ID',
        index='时段',
        columns='场景',
        aggfunc='nunique',
        fill_value=0
    )
    
    # 时段顺序
    period_order = ['清晨(6-9点)', '上午(9-12点)', '正午(12-14点)', '下午(14-18点)',
                   '傍晚(18-21点)', '晚间(21-24点)', '深夜(0-3点)', '凌晨(3-6点)']
    cross_orders = cross_orders.reindex(period_order, fill_value=0)
    
    # 找出最热组合（添加空值检查）
    stacked = cross_orders.stack()
    if len(stacked) > 0 and stacked.max() > 0:
        max_combo = stacked.idxmax()
        max_combo_orders = stacked.max()
    else:
        max_combo = ('未知', '未知')
        max_combo_orders = 0
    
    layout = html.Div([
        # 关键洞察
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H5([html.I(className="bi bi-star me-2"), "🔥 黄金组合"], className="mb-3"),
                    html.H4(f"{max_combo[0]} × {max_combo[1]}", className="text-primary"),
                    html.P(f"{int(max_combo_orders):,} 订单", className="text-muted mb-0")
                ], color="warning", className="shadow-sm")
            ], md=12)
        ], className="mb-4"),
        
        # 热力图
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🔥 时段×场景交叉热力图"),
                    dbc.CardBody([
                        render_cross_heatmap(cross_orders) if ECHARTS_AVAILABLE
                        else render_cross_heatmap_plotly(cross_orders)
                    ])
                ], className="shadow-sm")
            ])
        ])
    ])
    
    return layout


def render_ai_marketing_suggestions(df: pd.DataFrame):
    """4. AI智能营销建议"""
    layout = html.Div([
        dbc.Row([
            dbc.Col([
                html.H4([html.I(className="bi bi-robot me-2"), "AI智能营销建议"], className="text-primary mb-4")
            ])
        ]),
        
        # AI分析按钮
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.P("基于时段场景分析数据，AI将为您生成精准营销策略建议", className="mb-3"),
                        dbc.Button([
                            html.I(className="bi bi-stars me-2"),
                            "🚀 开始AI智能分析"
                        ], id='ai-scenario-analyze-btn', color="primary", size="lg", className="w-100")
                    ])
                ], className="shadow-sm")
            ], md=12)
        ], className="mb-4"),
        
        # AI分析结果
        dbc.Row([
            dbc.Col([
                html.Div(id='ai-scenario-analysis-result')
            ])
        ])
    ])
    
    return layout


@app.callback(
    Output('ai-scenario-analysis-result', 'children'),
    Input('ai-scenario-analyze-btn', 'n_clicks'),
    prevent_initial_call=True
)
def run_ai_scenario_analysis(n_clicks):
    """运行AI场景营销分析"""
    if n_clicks is None:
        raise PreventUpdate
    
    try:
        df = GLOBAL_DATA.copy()
        if df is None or len(df) == 0:
            return dbc.Alert("暂无数据", color="warning")
        
        df = extract_time_features_for_scenario(df)
        period_metrics = calculate_period_metrics(df)
        scenario_metrics = calculate_scenario_metrics(df)
        
        # 构建分析上下文
        analysis_context = {
            'period_metrics': period_metrics.to_dict('records'),
            'scenario_metrics': scenario_metrics.to_dict('records'),
            'total_orders': df['订单ID'].nunique(),
            'total_sales': df['实收价格'].sum()
        }
        
        # 构建prompt
        prompt = f"""
你是一位资深零售运营顾问,专注于O2O场景营销分析。请基于以下真实数据提供精准营销建议:

📊 **时段分析数据**:
{chr(10).join([f"- {m['时段']}: {int(m['订单量'])}单, 客单价¥{m['平均客单价']:.2f}, 利润率{m['利润率']:.1f}%" for m in analysis_context['period_metrics']])}

🎯 **场景分析数据**:
{chr(10).join([f"- {m['场景']}: {int(m['订单量'])}单, 销售额¥{m['销售额']:,.0f}, 利润率{m['利润率']:.1f}%" for m in analysis_context['scenario_metrics']])}

📈 **总体概况**:
- 总订单数: {analysis_context['total_orders']:,}单
- 总销售额: ¥{analysis_context['total_sales']:,.2f}

请提供以下分析:

## 🔍 核心洞察
[3-5个关键发现，基于时段和场景数据]

## 🎯 精准营销策略
### 1. 时段营销
- 低峰时段促销: [具体时段和策略]
- 高峰时段优化: [具体建议]

### 2. 场景营销
- 主力场景深耕: [针对top场景的策略]
- 潜力场景培育: [挖掘低频场景]

### 3. 商品推荐
- 时段商品匹配: [不同时段推荐不同商品]
- 场景套餐设计: [组合营销建议]

## 📅 执行计划
1. 本周: [具体行动]
2. 本月: [目标KPI]

## ⚠️ 风险提示
[可能的风险和应对措施]
"""
        
        # 调用AI
        from ai_analyzer import get_ai_analyzer
        scenario_analyzer = get_ai_analyzer(model_type='glm')
        
        if scenario_analyzer is None or not scenario_analyzer.is_ready():
            return dbc.Alert("AI分析器未就绪，请检查API配置", color="warning")
        
        print(f"\n{'='*60}")
        print(f"🤖 Tab 5 AI场景营销分析开始...")
        
        analysis_result = scenario_analyzer._generate_content(prompt)
        
        print(f"   ✅ AI分析完成")
        print(f"{'='*60}\n")
        
        if not analysis_result:
            return dbc.Alert("AI分析返回空结果，请稍后重试", color="warning")
        
        # 格式化结果
        return dbc.Card([
            dbc.CardHeader([
                html.I(className="bi bi-stars me-2"),
                html.H5("AI场景营销智能分析报告", className="d-inline mb-0")
            ]),
            dbc.CardBody([
                dcc.Markdown(
                    analysis_result,
                    className="ai-analysis-content",
                    style={
                        'fontFamily': 'Microsoft YaHei',
                        'fontSize': '14px',
                        'lineHeight': '1.6'
                    }
                ),
                html.Hr(),
                dbc.Alert([
                    html.I(className="bi bi-info-circle me-2"),
                    html.Small([
                        "此分析基于时段场景数据。",
                        "AI分析仅供参考，请结合实际情况执行。"
                    ])
                ], color="info", className="mb-0")
            ])
        ], className="shadow-sm", style={'border': '2px solid #667eea'})
        
    except Exception as e:
        print(f"❌ AI场景分析失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"分析失败: {str(e)}", color="danger")


# ==================== Tab 6: 成本利润分析辅助函数 ====================

def calculate_cost_profit_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """计算成本利润指标"""
    metrics = {}
    
    # 基础指标
    metrics['total_orders'] = df['订单ID'].nunique() if '订单ID' in df.columns else len(df)
    metrics['total_sales'] = df['实收价格'].sum() if '实收价格' in df.columns else 0
    
    # 成本计算
    cost_fields = []
    if '商品成本' in df.columns:
        cost_fields.append('商品成本')
    if '配送费成本' in df.columns:
        cost_fields.append('配送费成本')
    if '营销费用' in df.columns:
        cost_fields.append('营销费用')
    
    if cost_fields:
        metrics['total_cost'] = df[cost_fields].sum().sum()
    else:
        # 如果没有成本字段,估算为销售额的60%
        metrics['total_cost'] = metrics['total_sales'] * 0.6
    
    # 利润计算
    if '利润额' in df.columns:
        metrics['total_profit'] = df['利润额'].sum()
    else:
        metrics['total_profit'] = metrics['total_sales'] - metrics['total_cost']
    
    # 比率计算
    if metrics['total_sales'] > 0:
        metrics['cost_rate'] = (metrics['total_cost'] / metrics['total_sales']) * 100
        metrics['profit_rate'] = (metrics['total_profit'] / metrics['total_sales']) * 100
    else:
        metrics['cost_rate'] = 0
        metrics['profit_rate'] = 0
    
    # 平均值
    if metrics['total_orders'] > 0:
        metrics['avg_order_value'] = metrics['total_sales'] / metrics['total_orders']
        metrics['avg_profit_per_order'] = metrics['total_profit'] / metrics['total_orders']
    else:
        metrics['avg_order_value'] = 0
        metrics['avg_profit_per_order'] = 0
    
    # 成本结构
    cost_breakdown = {}
    if '商品成本' in df.columns:
        cost_breakdown['商品成本'] = df['商品成本'].sum()
    if '配送费成本' in df.columns:
        cost_breakdown['配送费成本'] = df['配送费成本'].sum()
    if '营销费用' in df.columns:
        cost_breakdown['营销费用'] = df['营销费用'].sum()
    
    # 如果没有详细成本,创建估算
    if not cost_breakdown:
        cost_breakdown = {
            '商品成本': metrics['total_cost'] * 0.7,
            '配送费成本': metrics['total_cost'] * 0.2,
            '营销费用': metrics['total_cost'] * 0.1
        }
    
    metrics['cost_breakdown'] = cost_breakdown
    
    return metrics


def render_cost_structure_chart(metrics: Dict[str, Any]):
    """渲染成本结构饼图 - ECharts版本"""
    cost_breakdown = metrics['cost_breakdown']
    
    option = {
        'title': {
            'text': '成本结构',
            'left': 'center',
            'top': 10,
            'textStyle': {'fontSize': 14, 'fontWeight': 'normal'}
        },
        'tooltip': {
            'trigger': 'item',
            'formatter': '{b}: ¥{c}<br/>占比: {d}%'
        },
        'legend': {
            'orient': 'vertical',
            'left': 'left',
            'top': 'middle'
        },
        'series': [{
            'name': '成本结构',
            'type': 'pie',
            'radius': ['40%', '70%'],
            'center': ['60%', '55%'],
            'avoidLabelOverlap': True,
            'itemStyle': {
                'borderRadius': 10,
                'borderColor': '#fff',
                'borderWidth': 2
            },
            'label': {
                'show': True,
                'formatter': '{b}\n¥{c}\n{d}%'
            },
            'emphasis': {
                'label': {'show': True, 'fontSize': 16, 'fontWeight': 'bold'}
            },
            'data': [
                {'value': v, 'name': k, 'itemStyle': {'color': color}}
                for (k, v), color in zip(cost_breakdown.items(), 
                                        ['#FF6B6B', '#4ECDC4', '#FFE66D'])
            ]
        }]
    }
    
    return DashECharts(
        option=option,
        id='cost-structure-chart',
        style={'height': '400px'}
    )


def render_cost_structure_chart_plotly(metrics: Dict[str, Any]):
    """渲染成本结构饼图 - Plotly版本(后备)"""
    cost_breakdown = metrics['cost_breakdown']
    
    fig = go.Figure(data=[go.Pie(
        labels=list(cost_breakdown.keys()),
        values=list(cost_breakdown.values()),
        hole=0.4,
        marker_colors=['#FF6B6B', '#4ECDC4', '#FFE66D'],
        textinfo='label+value+percent',
        hovertemplate='<b>%{label}</b><br>金额: ¥%{value:,.2f}<br>占比: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        height=400,
        showlegend=True,
        margin=dict(t=30, b=30, l=30, r=30)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def render_profit_source_chart(metrics: Dict[str, Any]):
    """渲染利润来源柱状图 - ECharts版本"""
    total_sales = metrics['total_sales']
    total_cost = metrics['total_cost']
    total_profit = metrics['total_profit']
    
    option = {
        'title': {
            'text': '销售额与成本利润对比',
            'left': 'center',
            'top': 10,
            'textStyle': {'fontSize': 14, 'fontWeight': 'normal'}
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'shadow'}
        },
        'legend': {
            'data': ['销售额', '成本', '利润'],
            'top': 40
        },
        'grid': {
            'left': '3%',
            'right': '4%',
            'bottom': '3%',
            'top': 80,
            'containLabel': True
        },
        'xAxis': {
            'type': 'category',
            'data': ['总体']
        },
        'yAxis': {
            'type': 'value',
            'name': '金额(元)',
            'axisLabel': {'formatter': '¥{value}'}
        },
        'series': [
            {
                'name': '销售额',
                'type': 'bar',
                'data': [total_sales],
                'itemStyle': {'color': '#5470C6'},
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': f'¥{total_sales:,.0f}'
                }
            },
            {
                'name': '成本',
                'type': 'bar',
                'data': [total_cost],
                'itemStyle': {'color': '#EE6666'},
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': f'¥{total_cost:,.0f}'
                }
            },
            {
                'name': '利润',
                'type': 'bar',
                'data': [total_profit],
                'itemStyle': {'color': '#91CC75'},
                'label': {
                    'show': True,
                    'position': 'top',
                    'formatter': f'¥{total_profit:,.0f}'
                }
            }
        ]
    }
    
    return DashECharts(
        option=option,
        id='profit-source-chart',
        style={'height': '400px'}
    )


def render_profit_source_chart_plotly(metrics: Dict[str, Any]):
    """渲染利润来源柱状图 - Plotly版本(后备)"""
    total_sales = metrics['total_sales']
    total_cost = metrics['total_cost']
    total_profit = metrics['total_profit']
    
    fig = go.Figure(data=[
        go.Bar(name='销售额', x=['总体'], y=[total_sales], marker_color='#5470C6',
               text=[f'¥{total_sales:,.0f}'], textposition='auto'),
        go.Bar(name='成本', x=['总体'], y=[total_cost], marker_color='#EE6666',
               text=[f'¥{total_cost:,.0f}'], textposition='auto'),
        go.Bar(name='利润', x=['总体'], y=[total_profit], marker_color='#91CC75',
               text=[f'¥{total_profit:,.0f}'], textposition='auto')
    ])
    
    fig.update_layout(
        height=400,
        barmode='group',
        yaxis_title='金额(元)',
        showlegend=True,
        margin=dict(t=30, b=30, l=50, r=30)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def render_product_profit_chart(df: pd.DataFrame):
    """渲染商品利润率分析 - ECharts版本"""
    # 按商品汇总
    product_metrics = df.groupby('商品名称').agg({
        '商品实售价': 'sum',
        '利润额': 'sum' if '利润额' in df.columns else lambda x: 0
    }).reset_index()
    
    # 如果没有利润额,估算
    if '利润额' not in df.columns:
        product_metrics['利润额'] = product_metrics['实收价格'] * 0.3
    
    # 计算利润率
    product_metrics['利润率'] = (product_metrics['利润额'] / product_metrics['实收价格'] * 100).round(1)
    
    # 取Top 20
    product_metrics = product_metrics.nlargest(20, '实收价格')
    product_metrics = product_metrics.sort_values('利润率')
    
    # 颜色映射
    colors = ['#91CC75' if r >= 30 else '#FAC858' if r >= 20 else '#EE6666' 
              for r in product_metrics['利润率']]
    
    option = {
        'title': {
            'text': 'Top 20 商品利润率',
            'left': 'center',
            'top': 10,
            'textStyle': {'fontSize': 14, 'fontWeight': 'normal'}
        },
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'shadow'}
        },
        'grid': {
            'left': '3%',
            'right': '10%',
            'bottom': '3%',
            'top': 50,
            'containLabel': True
        },
        'xAxis': {
            'type': 'value',
            'name': '销售额(元)'
        },
        'yAxis': {
            'type': 'category',
            'data': product_metrics['商品名称'].tolist(),
            'axisLabel': {
                'interval': 0,
                'fontSize': 11
            }
        },
        'series': [
            {
                'name': '销售额',
                'type': 'bar',
                'data': [
                    {'value': row['实收价格'], 'itemStyle': {'color': color}}
                    for (_, row), color in zip(product_metrics.iterrows(), colors)
                ],
                'label': {
                    'show': True,
                    'position': 'right',
                    'formatter': '{c}%'
                }
            }
        ]
    }
    
    return DashECharts(
        option=option,
        id='product-profit-chart',
        style={'height': '600px'}
    )


def render_product_profit_chart_plotly(df: pd.DataFrame):
    """渲染商品利润率分析 - Plotly版本(后备)"""
    # 按商品汇总
    product_metrics = df.groupby('商品名称').agg({
        '商品实售价': 'sum',
        '利润额': 'sum' if '利润额' in df.columns else lambda x: 0
    }).reset_index()
    
    # 如果没有利润额,估算
    # 如果没有利润额,估算 (Plotly版本)
    if '利润额' not in df.columns:
        product_metrics['利润额'] = product_metrics['实收价格'] * 0.3
    
    # 计算利润率
    product_metrics['利润率'] = (product_metrics['利润额'] / product_metrics['实收价格'] * 100).round(1)
    
    # 取Top 20
    product_metrics = product_metrics.nlargest(20, '实收价格')
    product_metrics = product_metrics.sort_values('利润率')
    
    # 颜色映射
    colors = ['#91CC75' if r >= 30 else '#FAC858' if r >= 20 else '#EE6666' 
              for r in product_metrics['利润率']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=product_metrics['实收价格'],
            y=product_metrics['商品名称'],
            orientation='h',
            marker_color=colors,
            text=[f"{r:.1f}%" for r in product_metrics['利润率']],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>销售额: ¥%{x:,.2f}<br>利润率: %{text}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        height=600,
        xaxis_title='销售额(元)',
        showlegend=False,
        margin=dict(t=30, b=30, l=150, r=80)
    )
    
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def render_cost_optimization_suggestions(metrics: Dict[str, Any]):
    """渲染成本优化建议"""
    suggestions = []
    
    # 基于利润率给建议
    profit_rate = metrics['profit_rate']
    
    if profit_rate < 20:
        suggestions.append({
            'icon': 'exclamation-triangle',
            'color': 'danger',
            'title': '⚠️ 利润率偏低',
            'content': f"当前利润率仅 {profit_rate:.1f}%，低于行业平均水平(25-35%)。建议优化成本结构或提升定价策略。"
        })
    elif profit_rate < 30:
        suggestions.append({
            'icon': 'info-circle',
            'color': 'warning',
            'title': '💡 利润率一般',
            'content': f"当前利润率 {profit_rate:.1f}%，处于中等水平。可通过优化商品组合和控制履约成本进一步提升。"
        })
    else:
        suggestions.append({
            'icon': 'check-circle',
            'color': 'success',
            'title': '✅ 利润率健康',
            'content': f"当前利润率 {profit_rate:.1f}%，处于良好水平。继续保持成本控制和定价策略。"
        })
    
    # 成本结构建议
    cost_breakdown = metrics['cost_breakdown']
    total_cost = metrics['total_cost']
    
    for cost_type, cost_value in cost_breakdown.items():
        cost_pct = (cost_value / total_cost * 100) if total_cost > 0 else 0
        
        if cost_type == '商品成本' and cost_pct > 70:
            suggestions.append({
                'icon': 'box',
                'color': 'info',
                'title': '📦 商品成本优化',
                'content': f"商品成本占比 {cost_pct:.1f}%，建议优化供应链、批量采购降低单位成本，或调整商品结构增加高毛利品。"
            })
        
        if cost_type == '配送费成本' and cost_pct > 25:
            suggestions.append({
                'icon': 'truck',
                'color': 'info',
                'title': '🚚 履约成本优化',
                'content': f"配送费成本占比 {cost_pct:.1f}%，建议提升订单客单价、优化配送路线或调整配送策略。"
            })
        
        if cost_type == '营销费用' and cost_pct > 15:
            suggestions.append({
                'icon': 'megaphone',
                'color': 'info',
                'title': '📢 营销成本优化',
                'content': f"营销费用占比 {cost_pct:.1f}%，建议优化营销ROI、精准投放或提升自然流量。"
            })
    
    # 渲染建议卡片
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="bi bi-lightbulb me-2"),
            "💡 成本优化建议"
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Alert([
                        html.H6([
                            html.I(className=f"bi bi-{sug['icon']} me-2"),
                            sug['title']
                        ], className="mb-2"),
                        html.P(sug['content'], className="mb-0")
                    ], color=sug['color'], className="mb-3")
                ], md=6)
                for sug in suggestions
            ])
        ])
    ], className="shadow-sm")


# ==================== Tab 6回调 ====================

@app.callback(
    Output('tab-6-content', 'children'),
    Input('main-tabs', 'value')
)
def render_tab6_content(active_tab):
    """Tab 6: 成本利润分析 - 使用ECharts可视化"""
    if active_tab != 'tab-6':
        raise PreventUpdate
    
    global GLOBAL_DATA
    
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            "暂无数据，请从数据库加载或上传数据文件"
        ], color="warning", className="text-center")
    
    try:
        df = GLOBAL_DATA.copy()
        
        # 计算成本利润指标
        cost_profit_metrics = calculate_cost_profit_metrics(df)
        
        # 创建布局
        layout = html.Div([
            # 标题
            html.H3([
                html.I(className="bi bi-currency-dollar me-2"),
                "💵 成本利润分析"
            ], className="mb-4"),
            
            # 关键指标卡片
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("💰 总销售额", className="text-primary mb-2"),
                            html.H4(f"¥{cost_profit_metrics['total_sales']:,.2f}", className="mb-1"),
                            html.P(f"订单数: {cost_profit_metrics['total_orders']:,}", 
                                   className="text-muted mb-0 small")
                        ])
                    ], className="modern-card shadow-sm border-primary h-100")
                ], md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("📦 总成本", className="text-danger mb-2"),
                            html.H4(f"¥{cost_profit_metrics['total_cost']:,.2f}", className="mb-1"),
                            html.P(f"成本率: {cost_profit_metrics['cost_rate']:.1f}%", 
                                   className="text-muted mb-0 small")
                        ])
                    ], className="modern-card shadow-sm border-danger h-100")
                ], md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("💎 总利润", className="text-success mb-2"),
                            html.H4(f"¥{cost_profit_metrics['total_profit']:,.2f}", className="mb-1"),
                            html.P(f"利润率: {cost_profit_metrics['profit_rate']:.1f}%", 
                                   className="text-muted mb-0 small")
                        ])
                    ], className="modern-card shadow-sm border-success h-100")
                ], md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("📊 平均客单价", className="text-info mb-2"),
                            html.H4(f"¥{cost_profit_metrics['avg_order_value']:.2f}", className="mb-1"),
                            html.P(f"单利润: ¥{cost_profit_metrics['avg_profit_per_order']:.2f}", 
                                   className="text-muted mb-0 small")
                        ])
                    ], className="modern-card shadow-sm border-info h-100")
                ], md=3)
            ], className="mb-4"),
            
            # 成本结构分析 (使用ECharts)
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-pie-chart me-2"),
                            "📊 成本结构分析"
                        ]),
                        dbc.CardBody([
                            render_cost_structure_chart(cost_profit_metrics) if ECHARTS_AVAILABLE
                            else render_cost_structure_chart_plotly(cost_profit_metrics)
                        ])
                    ], className="shadow-sm")
                ], md=6),
                
                # 利润来源分析 (使用ECharts)
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-bar-chart me-2"),
                            "💎 利润来源分析"
                        ]),
                        dbc.CardBody([
                            render_profit_source_chart(cost_profit_metrics) if ECHARTS_AVAILABLE
                            else render_profit_source_chart_plotly(cost_profit_metrics)
                        ])
                    ], className="shadow-sm")
                ], md=6)
            ], className="mb-4"),
            
            # 商品级成本利润分析 (使用ECharts)
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-graph-up me-2"),
                            "🏷️ 商品利润率分析 (Top 20)"
                        ]),
                        dbc.CardBody([
                            render_product_profit_chart(df) if ECHARTS_AVAILABLE
                            else render_product_profit_chart_plotly(df)
                        ])
                    ], className="shadow-sm")
                ])
            ], className="mb-4"),
            
            # 成本优化建议
            dbc.Row([
                dbc.Col([
                    render_cost_optimization_suggestions(cost_profit_metrics)
                ])
            ])
        ])
        
        return layout
        
    except Exception as e:
        print(f"❌ Tab 6渲染失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"渲染失败: {str(e)}", color="danger")


# ==================== Tab 7回调已在后面定义 (营销成本分析) ====================
# 占位回调已删除,避免重复定义


# ==================== 全局数据信息更新回调 ====================
@app.callback(
    [Output('global-data-info-card', 'children'),
     Output('data-metadata', 'data')],
    [Input('data-update-trigger', 'data'),
     Input('main-tabs', 'value')],
    prevent_initial_call=False
)
def update_global_data_info(trigger, active_tab):
    """更新全局数据信息卡片"""
    global GLOBAL_DATA, QUERY_DATE_RANGE
    
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            "⚠️ 未加载数据，请从数据库加载或上传数据文件"
        ], color="warning", className="mb-3"), {}
    
    try:
        from datetime import datetime
        
        # 计算数据统计信息
        total_records = len(GLOBAL_DATA)
        
        # ✅ 计算当前查询的时间范围
        if '日期' in GLOBAL_DATA.columns:
            date_col = pd.to_datetime(GLOBAL_DATA['日期'], errors='coerce')
            query_min_date = date_col.min()
            query_max_date = date_col.max()
            
            # 检查是否为有效日期
            if pd.isna(query_min_date) or pd.isna(query_max_date):
                query_date_range_text = "日期数据异常"
            else:
                # ✅ 修复: 始终显示实际加载的数据范围,而不是用户输入的查询范围
                # 原因: 用户可能通过快捷按钮选择了今天,但实际数据可能不包含今天
                query_date_range_text = f"{query_min_date.strftime('%Y-%m-%d')} 至 {query_max_date.strftime('%Y-%m-%d')}"
        else:
            query_date_range_text = "无日期字段"
        
        # ✅ 获取数据库完整时间范围(固定)
        if QUERY_DATE_RANGE.get('db_min_date') and QUERY_DATE_RANGE.get('db_max_date'):
            db_date_range_text = f"{QUERY_DATE_RANGE['db_min_date'].strftime('%Y-%m-%d')} 至 {QUERY_DATE_RANGE['db_max_date'].strftime('%Y-%m-%d')}"
        else:
            # 如果没有保存过,使用当前数据的范围
            db_date_range_text = query_date_range_text
        
        # 获取数据文件名（从全局变量或默认值）
        data_filename = "数据库加载"  # 数据库来源
        
        # 订单数量
        order_count = 0
        if '订单ID' in GLOBAL_DATA.columns:
            order_count = GLOBAL_DATA['订单ID'].nunique()
        
        # 商品数量
        product_count = 0
        if '商品名称' in GLOBAL_DATA.columns:
            product_count = GLOBAL_DATA['商品名称'].nunique()
        
        # 获取当前时间
        update_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建元数据
        metadata = {
            'total_records': total_records,
            'query_date_range': query_date_range_text,
            'db_date_range': db_date_range_text,
            'order_count': order_count,
            'product_count': product_count,
            'update_time': update_time,
            'filename': data_filename
        }
        
        # 创建信息卡片
        info_card = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # 数据状态指示器
                    dbc.Col([
                        html.Div([
                            html.I(className="bi bi-database-check me-2", 
                                   style={'fontSize': '1.2rem', 'color': '#28a745'}),
                            html.Span("数据已加载", className="fw-bold", 
                                     style={'color': '#28a745'})
                        ], className="d-flex align-items-center")
                    ], width=2),
                    
                    # 数据文件名
                    dbc.Col([
                        html.Small("📁 数据文件:", className="text-muted me-2"),
                        html.Span(data_filename, className="fw-bold", 
                                 style={'fontSize': '0.9rem'})
                    ], width=3),
                    
                    # ✅ 双重时间范围显示
                    dbc.Col([
                        # 当前查询的日期范围(动态)
                        html.Div([
                            html.Small("📅 当前查询范围:", className="text-muted me-1"),
                            html.Span(query_date_range_text, className="fw-bold text-info",
                                     style={'fontSize': '0.85rem'})
                        ], className="mb-1"),
                        # 数据库完整日期范围(固定)
                        html.Div([
                            html.Small("📚 数据库总范围:", className="text-muted me-1"),
                            html.Span(db_date_range_text, className="fw-bold text-secondary",
                                     style={'fontSize': '0.85rem'})
                        ])
                    ], width=3),
                    
                    # 数据量统计
                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.Small("📊 订单数:", className="text-muted me-1"),
                                html.Span(f"{order_count:,}", className="fw-bold text-primary",
                                         style={'fontSize': '0.9rem'})
                            ]),
                            html.Div([
                                html.Small("🏷️ 商品数:", className="text-muted me-1"),
                                html.Span(f"{product_count:,}", className="fw-bold text-success",
                                         style={'fontSize': '0.9rem'})
                            ])
                        ])
                    ], width=2),
                    
                    # 最后更新时间
                    dbc.Col([
                        html.Small("🕐 更新时间:", className="text-muted me-2"),
                        html.Span(update_time, className="text-muted small")
                    ], width=2)
                ], align="center")
            ])
        ], className="mb-3", style={
            'borderLeft': '4px solid #28a745',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.05)',
            'background': '#f8fff9'
        })
        
        return info_card, metadata
        
    except Exception as e:
        print(f"❌ 更新数据信息失败: {e}")
        import traceback
        traceback.print_exc()
        
        return dbc.Alert([
            html.I(className="bi bi-exclamation-circle me-2"),
            f"❌ 数据信息更新失败: {str(e)}"
        ], color="danger", className="mb-3"), {}


# 为各个Tab更新数据信息
@app.callback(
    Output('tab4-data-info', 'children'),
    [Input('data-metadata', 'data'),
     Input('main-tabs', 'value')],
    prevent_initial_call=False
)
def update_tab_data_info(metadata, active_tab):
    """为Tab-4更新数据信息提示"""
    if not metadata:
        return html.Div()
    
    # 创建简化的数据信息条
    info_bar = dbc.Alert([
        html.I(className="bi bi-info-circle me-2"),
        html.Span("当前分析数据: ", className="fw-bold"),
        html.Span(f"{metadata.get('date_range', '未知')} | ", className="me-2"),
        html.Span(f"订单数: {metadata.get('order_count', 0):,} | ", className="me-2"),
        html.Span(f"商品数: {metadata.get('product_count', 0):,}", className="me-2"),
        html.Span(f" (更新于 {metadata.get('update_time', '--')})", className="text-muted small")
    ], color="info", className="mb-3", style={'padding': '0.75rem'})
    
    return info_bar



# ==================== AI分析回调 ====================
# 初始化AI分析器（全局单例）
AI_ANALYZER = None

def init_ai_analyzer():
    """初始化AI分析器 - 支持多种AI模型"""
    global AI_ANALYZER
    if AI_ANALYZER is None:
        # 从环境变量获取模型类型和API密钥
        model_type = os.getenv('AI_MODEL_TYPE', 'glm')  # 默认使用智谱GLM
        
        # 根据模型类型获取对应的API密钥
        if model_type == 'glm':
            api_key = os.getenv('ZHIPU_API_KEY')
            key_name = 'ZHIPU_API_KEY'
        elif model_type == 'qwen':
            api_key = os.getenv('DASHSCOPE_API_KEY')
            key_name = 'DASHSCOPE_API_KEY'
        else:  # gemini
            api_key = os.getenv('GEMINI_API_KEY')
            key_name = 'GEMINI_API_KEY'
        
        AI_ANALYZER = get_ai_analyzer(api_key, model_type)
        if AI_ANALYZER:
            model_names = {'glm': '智谱GLM-4.6', 'qwen': '通义千问', 'gemini': 'Gemini'}
            print(f"✅ AI分析器初始化成功 (使用{model_names.get(model_type, model_type)})")
        else:
            print(f"⚠️ AI分析器初始化失败,请设置{key_name}环境变量")
    return AI_ANALYZER


# ==================== Tab 2 AI分析回调 - 增强版多板块工作流 ====================
@app.callback(
    [Output('ai-tab2-analysis-result', 'children'),
     Output('ai-analysis-progress', 'children')],
    Input('ai-tab2-analyze-btn', 'n_clicks'),
    [State('ai-analysis-mode', 'value'),
     State('tab2-all-data', 'data')],
    prevent_initial_call=True
)
def run_tab2_ai_analysis_workflow(n_clicks, analysis_mode, all_data):
    """Tab 2 - AI智能分析工作流 (支持快速/标准/全面三种模式)"""
    if not n_clicks or n_clicks == 0:
        return html.Div(), html.Div()
    
    if not all_data or 'product_agg' not in all_data:
        return dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            "请先查看商品分析数据后再进行AI分析"
        ], color="warning"), html.Div()
    
    # 初始化AI分析器
    analyzer = init_ai_analyzer()
    if not analyzer:
        model_type = os.getenv('AI_MODEL_TYPE', 'glm')
        key_names = {'glm': 'ZHIPU_API_KEY', 'qwen': 'DASHSCOPE_API_KEY', 'gemini': 'GEMINI_API_KEY'}
        key_name = key_names.get(model_type, 'ZHIPU_API_KEY')
        
        return dbc.Alert([
            html.I(className="bi bi-x-circle me-2"),
            html.Div([
                html.Strong("AI分析器未就绪"),
                html.Br(),
                html.Small(f"请在.env文件中设置 {key_name}")
            ])
        ], color="danger"), html.Div()
    
    try:
        # 转换数据
        df = pd.DataFrame(all_data['product_agg'])
        
        if len(df) == 0:
            return dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                "商品数据为空,无法进行AI分析"
            ], color="info"), html.Div()
        
        print(f"\n{'='*60}")
        print(f"🤖 Tab 2 AI智能分析工作流启动...")
        print(f"   分析模式: {analysis_mode}")
        print(f"   商品总数: {len(df)}")
        
        # 根据模式执行不同的分析流程
        if analysis_mode == 'quick':
            # 快速模式: 仅四象限分析
            result = run_quick_analysis(df, all_data, analyzer)
            progress = create_progress_indicator(['四象限分析'], [True])
            
        elif analysis_mode == 'standard':
            # 标准模式: 四象限 + 趋势 + 排行
            result = run_standard_analysis(df, all_data, analyzer)
            progress = create_progress_indicator(['四象限分析', '趋势分析', '商品排行'], [True, True, True])
            
        else:  # comprehensive
            # 全面模式: 所有板块 + 综合报告
            result = run_comprehensive_analysis(df, all_data, analyzer)
            progress = create_progress_indicator(
                ['四象限', '趋势', '排行', '分类', '结构', '库存', '综合报告'],
                [True] * 7
            )
        
        return result, progress
        
    except Exception as e:
        print(f"❌ AI分析失败: {e}")
        import traceback
        traceback.print_exc()
        
        return dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            html.Div([
                html.Strong("AI分析出错"),
                html.Br(),
                html.Small(f"错误信息: {str(e)}")
            ])
        ], color="danger"), html.Div()


def create_progress_indicator(steps: List[str], completed: List[bool]) -> html.Div:
    """创建分析进度指示器"""
    items = []
    for i, (step, done) in enumerate(zip(steps, completed)):
        icon = "✅" if done else "⏳"
        color = "success" if done else "secondary"
        items.append(
            dbc.Badge(f"{icon} {step}", color=color, className="me-2 mb-2")
        )
    
    return html.Div([
        html.Small("分析进度:", className="text-muted me-2"),
        html.Div(items, className="d-inline-flex flex-wrap")
    ])


def run_quick_analysis(df: pd.DataFrame, all_data: Dict, analyzer) -> html.Div:
    """快速分析模式 - 仅四象限"""
    print("   📊 执行快速分析 (四象限)...")
    
    # 准备四象限数据
    quadrant_stats = all_data.get('quadrant_stats', {})
    high_profit = df[df['象限分类'].isin(['🌟 高利润高动销', '⚠️ 高利润低动销'])].nlargest(3, '实际利润')
    low_profit = df[df['象限分类'] == '❌ 低利润低动销'].nlargest(3, '销售额')
    
    analysis_context = {
        'total_products': len(df),
        'total_sales': df['销售额'].sum(),
        'total_profit': df['实际利润'].sum(),
        'avg_profit_rate': df['利润率'].mean(),
        'quadrant_stats': quadrant_stats,
        'top_profit_products': high_profit[['商品名称', '销售额', '实际利润', '利润率', '总销量', '平均售价', '象限分类']].to_dict('records') if len(high_profit) > 0 else [],
        'problem_products': low_profit[['商品名称', '销售额', '实际利润', '利润率', '总销量', '平均售价', '象限分类']].to_dict('records') if len(low_profit) > 0 else []
    }
    
    # 构建AI提示词
    prompt = f"""
你是一位资深零售运营顾问。**请严格基于以下真实数据和看板计算逻辑进行分析**:

📋 **看板核心计算逻辑** (AI分析必须遵循):

1. **利润率计算**:
   - 利润率 = (实收价格 - 成本) / 实收价格 × 100%
   - 使用实收价格(排除补贴/折扣后的真实收入)

2. **四象限划分标准**:
   - 利润率阈值: 30% (高于30%为高利润)
   - 动销指数阈值: {df['动销指数'].median():.3f} (高于中位数为高动销)
   - 🌟 高利润高动销: 利润率>30% 且 动销指数>阈值
   - ⚠️ 高利润低动销: 利润率>30% 但 动销指数≤阈值
   - 🚀 低利润高动销: 利润率≤30% 但 动销指数>阈值
   - ❌ 低利润低动销: 利润率≤30% 且 动销指数≤阈值

3. **动销指数计算**:
   - 动销指数 = 0.5×标准化销量 + 0.3×标准化周转率 + 0.2×标准化订单数
   - 综合评价商品的销售活跃度

4. **盈利健康度判定**:
   - 🟢 稳定盈利: ≥70%订单盈利
   - 🟡 波动盈利: 40%-70%订单盈利
   - 🔴 依赖大单: <40%订单盈利但有盈利
   - ⚫ 全部亏损: 0%订单盈利

5. **数据字段说明**:
   - 销售额 = 单价 × 销量 (累计值)
   - 利润 = 销售额 - 成本 (累计值)
   - 平均售价 = 销售额 / 销量 (单价)

---

📊 **总体数据**(统计周期内汇总):
- 商品总数: {analysis_context['total_products']}个
- 总销售额: ¥{analysis_context['total_sales']:,.2f} (所有商品累计销售额)
- 总利润: ¥{analysis_context['total_profit']:,.2f} (所有商品累计利润)
- 平均利润率: {analysis_context['avg_profit_rate']:.1f}%

🎯 **四象限分布**:
{chr(10).join([f"- {k}: {v}个 ({v/analysis_context['total_products']*100:.1f}%)" for k, v in analysis_context['quadrant_stats'].items()])}

🌟 **高利润商品TOP3** (必须在分析中引用):
**注意:销售额是累计值,平均售价是单价**
"""
    # 修复 f-string 反斜杠问题：提取到变量
    newline = '\n'
    top_products_text = chr(10).join([
        f"{i+1}. **{p['商品名称']}**{newline}"
        f"   - 累计销售额: ¥{p['销售额']:,.2f}{newline}"
        f"   - 累计利润: ¥{p['实际利润']:,.2f}{newline}"
        f"   - 利润率: {p['利润率']:.1f}%{newline}"
        f"   - 销量: {p['总销量']}件{newline}"
        f"   - 单价: ¥{p['平均售价']:.2f}/件"
        for i, p in enumerate(analysis_context['top_profit_products'])
    ])
    
    problem_products_text = chr(10).join([
        f"{i+1}. **{p['商品名称']}**{newline}"
        f"   - 累计销售额: ¥{p['销售额']:,.2f}{newline}"
        f"   - 累计利润: ¥{p['实际利润']:,.2f}{newline}"
        f"   - 利润率: {p['利润率']:.1f}%{newline}"
        f"   - 销量: {p['总销量']}件{newline}"
        f"   - 单价: ¥{p['平均售价']:.2f}/件"
        for i, p in enumerate(analysis_context['problem_products'])
    ])
    
    user_prompt = f"""
你是专业的新零售数据分析师,正在分析门店O2O业务数据。

📋 **字段含义**:
   - 销售额 = 单价 × 销量 (累计值)
   - 利润 = 销售额 - 成本 (累计值)
   - 平均售价 = 销售额 / 销量 (单价)

---

📊 **总体数据**(统计周期内汇总):
- 商品总数: {analysis_context['total_products']}个
- 总销售额: ¥{analysis_context['total_sales']:,.2f} (所有商品累计销售额)
- 总利润: ¥{analysis_context['total_profit']:,.2f} (所有商品累计利润)
- 平均利润率: {analysis_context['avg_profit_rate']:.1f}%

🎯 **四象限分布**:
{chr(10).join([f"- {k}: {v}个 ({v/analysis_context['total_products']*100:.1f}%)" for k, v in analysis_context['quadrant_stats'].items()])}

🌟 **高利润商品TOP3** (必须在分析中引用):
**注意:销售额是累计值,平均售价是单价**
{top_products_text}

⚠️ **问题商品TOP3** (必须在分析中引用):
**注意:销售额是累计值,平均售价是单价**
{problem_products_text}

---

**分析要求**:
1. 必须使用上述真实商品名称和数据,不要编造
2. 调价建议基于"平均售价",调幅5%-15%为宜
3. 基于四象限逻辑给建议(如:高利润低动销→加强推广)
4. 所有预期效果需基于真实数据计算

请提供结构化分析报告:

## 📊 核心洞察
[基于四象限分布和盈利健康度的3-5个关键发现]

## 💡 优化策略
### 1. 商品组合优化
- 重点推广: [从高利润TOP3选择,说明当前单价¥X和销量]
- 优化调整: [从问题商品选择,基于象限分类给建议]
- 预期效果: [基于当前数据估算收益]

### 2. 定价策略  
- 调价商品: [商品名,当前¥X→建议¥Y,调幅Z%]
- 调价依据: [基于利润率和市场定位]
- 预期收益: [销量变化×利润变化]

### 3. 库存优化
- 补货优先级: [基于销量和象限分类]
- 清仓方案: [针对低利润低动销商品]

## 📈 执行计划
1. 本周: [具体商品的具体操作]
2. 本月: [目标和KPI]
3. 季度: [长期策略]

## ⚠️ 风险提示
[基于数据的潜在风险]
"""
    
    # 调用AI (阶段1优化: Few-Shot + CoT + 数据验证)
    model_names = {'glm': '智谱GLM-4', 'qwen': '通义千问', 'gemini': 'Gemini'}
    model_name = model_names.get(analyzer.model_type, 'AI')
    print(f"\n   调用{model_name} API...")
    
    if BUSINESS_CONTEXT_AVAILABLE:
        print(f"   ✅ 启用GLM-4.6阶段1优化")
        print(f"   ✓ Few-Shot示例库自动匹配")
        print(f"   ✓ CoT思维链6步引导")
        print(f"   ✓ 数据验证规则注入")
        
        # 构建数据摘要
        data_summary = {
            '商品总数': analysis_context['total_products'],
            '总销售额': f"¥{analysis_context['total_sales']:,.2f}",
            '总利润': f"¥{analysis_context['total_profit']:,.2f}",
            '平均利润率': f"{analysis_context['avg_profit_rate']:.1f}%",
            '四象限分布': analysis_context['quadrant_stats'],
            '高利润商品': [p['商品名称'] for p in analysis_context['top_profit_products']],
            '问题商品': [p['商品名称'] for p in analysis_context['problem_products']]
        }
        
        # 生成增强Prompt
        enhanced_prompt = get_analysis_prompt(
            task_name="商品四象限分析",
            data_summary=data_summary,
            specific_question=prompt,
            use_cot=True,
            use_examples=True
        )
        
        print(f"   📋 增强Prompt前500字: {enhanced_prompt[:500]}...")
        analysis_result = analyzer._generate_content(enhanced_prompt)
    else:
        print(f"   ⚠️ 使用基础分析 (未启用阶段1优化)")
        print(f"   📋 Prompt前500字: {prompt[:500]}...")
        analysis_result = analyzer._generate_content(prompt)
    
    print(f"   ✅ AI分析完成")
    print(f"   📝 结果长度: {len(analysis_result) if analysis_result else 0} 字符")
    if analysis_result:
        print(f"   📝 前200字: {analysis_result[:200]}...")
    
    # 检查结果是否为空
    if not analysis_result or len(analysis_result.strip()) == 0:
        return dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            html.Div([
                html.Strong("AI分析返回空结果"),
                html.Br(),
                html.Small("请稍后重试或联系技术支持")
            ])
        ], color="warning")
    
    # 格式化结果
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="bi bi-stars me-2"),
            html.H5("🎯 四象限智能分析报告", className="d-inline mb-0"),
            html.Small(f" - 基于{analysis_context['total_products']}个商品", className="text-muted ms-2")
        ]),
        dbc.CardBody([
            dcc.Markdown(
                analysis_result,
                className="ai-analysis-content",
                style={
                    'fontFamily': 'Microsoft YaHei',
                    'fontSize': '14px',
                    'lineHeight': '1.6'
                }
            ),
            html.Hr(),
            dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                html.Small([
                    "此分析基于商品四象限数据。",
                    "AI分析仅供参考,请结合实际情况执行。",
                    f"使用模型: {model_name}"
                ])
            ], color="info", className="mb-0")
        ])
    ], className="shadow-sm", style={'border': '2px solid #667eea'})


# ==================== Tab 2 AI分析辅助函数 (多板块工作流) ====================

def run_standard_analysis(df: pd.DataFrame, all_data: Dict, analyzer) -> html.Div:
    """标准分析模式 - 四象限 + 趋势 + 排行"""
    print("   📊 执行标准分析 (四象限 + 趋势 + 排行)...")
    
    results = []
    
    # 1. 四象限分析
    quadrant_result = analyze_quadrant_module(df, all_data, analyzer)
    results.append(quadrant_result)
    
    # 2. 趋势分析 (简化版)
    trend_result = analyze_trend_module(df, analyzer)
    results.append(trend_result)
    
    # 3. 商品排行分析
    ranking_result = analyze_ranking_module(df, analyzer)
    results.append(ranking_result)
    
    # 返回组合结果
    return html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.I(className="bi bi-stars me-2"),
                html.H5("AI标准分析报告", className="d-inline mb-0"),
                html.Small(f" - 基于{len(df)}个商品的多维度分析", className="text-muted ms-2")
            ]),
            dbc.CardBody(results)
        ])
    ])


def run_comprehensive_analysis(df: pd.DataFrame, all_data: Dict, analyzer) -> html.Div:
    """全面分析模式 - 所有7大板块 + 综合报告"""
    print("   📊 执行全面分析 (7大板块 + 综合报告)...")
    
    results = []
    
    try:
        # 7. 综合报告 (优先生成,最重要)
        print("   ✅ 生成综合报告...")
        summary = generate_summary_report(df, all_data, analyzer)
        if summary:
            results.append(summary)
            print("   ✅ 综合报告完成")
        
        # 1-6. 各板块分析(如果前面成功才继续)
        modules = [
            ("🎯 四象限分析", analyze_quadrant_module),
            ("📈 趋势分析", analyze_trend_module),
            ("📊 商品排行", analyze_ranking_module),
            ("📂 分类分析", analyze_category_module),
            ("🔄 结构分析", analyze_structure_module),
            ("⚠️ 库存预警", analyze_inventory_module)
        ]
        
        for title, func in modules:
            try:
                print(f"   ✅ 生成{title}...")
                if title == "🎯 四象限分析":
                    content = func(df, all_data, analyzer)
                else:
                    content = func(df, analyzer)
                
                if content:
                    results.append(
                        dbc.Accordion([
                            dbc.AccordionItem([content], title=title)
                        ], start_collapsed=True, className="mb-3")
                    )
                    print(f"   ✅ {title}完成")
            except Exception as e:
                print(f"   ⚠️ {title}失败: {e}")
                results.append(
                    dbc.Alert(f"{title} 生成失败: {str(e)}", color="warning", className="mb-3")
                )
        
        if not results:
            return dbc.Alert("AI分析未返回结果,请稍后重试", color="warning")
        
        return html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="bi bi-stars me-2"),
                    html.H5("AI全面分析报告", className="d-inline mb-0"),
                    html.Small(f" - 基于{len(df)}个商品的深度洞察", className="text-muted ms-2")
                ]),
                dbc.CardBody(results)
            ])
        ])
        
    except Exception as e:
        print(f"   ❌ 全面分析失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"AI分析失败: {str(e)}", color="danger")


def analyze_quadrant_module(df: pd.DataFrame, all_data: Dict, analyzer) -> html.Div:
    """四象限板块分析"""
    quadrant_stats = all_data.get('quadrant_stats', {})
    high_profit = df[df['象限分类'].isin(['🌟 高利润高动销', '⚠️ 高利润低动销'])].nlargest(3, '实际利润')
    low_profit = df[df['象限分类'] == '❌ 低利润低动销'].nlargest(3, '销售额')
    
    prompt = f"""
基于商品四象限分析,提供深度洞察(限500字):

**数据**: 商品{len(df)}个, 平均利润率{df['利润率'].mean():.1f}%
**分布**: {quadrant_stats}
**TOP3高利润**: {[p['商品名称'] for p in high_profit.to_dict('records')]}
**TOP3问题**: {[p['商品名称'] for p in low_profit.to_dict('records')]}

分析: 1)四象限分布健康度 2)高利润低动销激活策略 3)具体商品优化建议
"""
    
    if BUSINESS_CONTEXT_AVAILABLE:
        data_summary = {'商品数': len(df), '四象限': quadrant_stats}
        enhanced_prompt = get_analysis_prompt("商品四象限分析", data_summary, prompt, use_cot=True, use_examples=True)
        result = analyzer._generate_content(enhanced_prompt)
    else:
        result = analyzer._generate_content(prompt)
    return dcc.Markdown(result, className="ai-analysis-content")


def analyze_trend_module(df: pd.DataFrame, analyzer) -> html.Div:
    """趋势分析板块"""
    prompt = f"""
基于商品数据,分析趋势(限300字):

**商品总数**: {len(df)}
**平均利润率**: {df['利润率'].mean():.1f}%
**高动销占比**: {(df['动销指数'] > df['动销指数'].median()).sum() / len(df) * 100:.1f}%

分析: 1)主要趋势 2)预警商品 3)拐点识别
"""
    
    if BUSINESS_CONTEXT_AVAILABLE:
        data_summary = {'商品数': len(df), '平均利润率': f"{df['利润率'].mean():.1f}%"}
        enhanced_prompt = get_analysis_prompt("商品趋势分析", data_summary, prompt, use_cot=True, use_examples=False)
        result = analyzer._generate_content(enhanced_prompt)
    else:
        result = analyzer._generate_content(prompt)
    return dcc.Markdown(result, className="ai-analysis-content")


def analyze_ranking_module(df: pd.DataFrame, analyzer) -> html.Div:
    """商品排行板块分析"""
    top5 = df.nlargest(5, '销售额')[['商品名称', '销售额', '利润率']].to_dict('records')
    bottom5 = df.nsmallest(5, '销售额')[['商品名称', '销售额', '利润率']].to_dict('records')
    
    prompt = f"""
基于商品排行,识别明星/淘汰商品(限300字):

**TOP5**: {[p['商品名称'] for p in top5]}
**BOTTOM5**: {[p['商品名称'] for p in bottom5]}

分析: 1)明星商品成功因素 2)淘汰商品改进方向
"""
    
    if BUSINESS_CONTEXT_AVAILABLE:
        data_summary = {'TOP5': [p['商品名称'] for p in top5], 'BOTTOM5': [p['商品名称'] for p in bottom5]}
        enhanced_prompt = get_analysis_prompt("商品排行分析", data_summary, prompt, use_cot=True, use_examples=False)
        result = analyzer._generate_content(enhanced_prompt)
    else:
        result = analyzer._generate_content(prompt)
    return dcc.Markdown(result, className="ai-analysis-content")


def analyze_category_module(df: pd.DataFrame, analyzer) -> html.Div:
    """分类分析板块"""
    if '一级分类名' in df.columns:
        category_sales = df.groupby('一级分类名')['销售额'].sum().nlargest(5).to_dict()
        prompt = f"""
基于分类数据,优化品类结构(限300字):

**TOP5分类销售额**: {category_sales}

分析: 1)品类结构合理性 2)加强/削弱建议 3)跨品类组合
"""
        if BUSINESS_CONTEXT_AVAILABLE:
            data_summary = {'TOP5分类': category_sales}
            enhanced_prompt = get_analysis_prompt("商品分类分析", data_summary, prompt, use_cot=True, use_examples=False)
            result = analyzer._generate_content(enhanced_prompt)
        else:
            result = analyzer._generate_content(prompt)
    else:
        prompt = "分类数据不足,无法分析。"
        result = analyzer._generate_content(prompt)
    return dcc.Markdown(result, className="ai-analysis-content")


def analyze_structure_module(df: pd.DataFrame, analyzer) -> html.Div:
    """结构分析板块"""
    prompt = f"""
基于商品结构,分析生命周期(限300字):

**四象限分布**: {df['象限分类'].value_counts().to_dict()}

分析: 1)商品生命周期阶段 2)迁移干预建议
"""
    
    if BUSINESS_CONTEXT_AVAILABLE:
        data_summary = {'四象限分布': df['象限分类'].value_counts().to_dict()}
        enhanced_prompt = get_analysis_prompt("商品结构分析", data_summary, prompt, use_cot=True, use_examples=False)
        result = analyzer._generate_content(enhanced_prompt)
    else:
        result = analyzer._generate_content(prompt)
    return dcc.Markdown(result, className="ai-analysis-content")


def analyze_inventory_module(df: pd.DataFrame, analyzer) -> html.Div:
    """库存预警板块"""
    zero_stock = df[df['库存'] == 0]
    low_stock = df[(df['库存'] > 0) & (df['库存'] < df['总销量'] * 0.1)]
    
    prompt = f"""
基于库存数据,制定补货/清仓策略(限300字):

**0库存商品**: {len(zero_stock)}个
**低库存商品**: {len(low_stock)}个

分析: 1)补货优先级 2)清仓方案 3)周转优化
"""
    
    if BUSINESS_CONTEXT_AVAILABLE:
        data_summary = {'0库存': len(zero_stock), '低库存': len(low_stock)}
        enhanced_prompt = get_analysis_prompt("库存预警分析", data_summary, prompt, use_cot=True, use_examples=False)
        result = analyzer._generate_content(enhanced_prompt)
    else:
        result = analyzer._generate_content(prompt)
    return dcc.Markdown(result, className="ai-analysis-content")


def generate_summary_report(df: pd.DataFrame, all_data: Dict, analyzer) -> html.Div:
    """生成综合报告"""
    prompt = f"""
基于7大板块分析,生成综合执行计划(限800字):

**总览**: {len(df)}个商品, 总销售额¥{df['销售额'].sum():,.2f}, 总利润¥{df['实际利润'].sum():,.2f}
**四象限**: {all_data.get('quadrant_stats', {})}

请整合给出:
## 📊 核心发现 (3-5条)
## 💡 优先级策略 (本周/本月/本季度)
## 📈 预期效果 (数据化目标)
## ⚠️ 风险提示
"""
    
    if BUSINESS_CONTEXT_AVAILABLE:
        data_summary = {
            '商品数': len(df),
            '销售额': f"¥{df['销售额'].sum():,.2f}",
            '利润': f"¥{df['实际利润'].sum():,.2f}",
            '四象限': all_data.get('quadrant_stats', {})
        }
        enhanced_prompt = get_analysis_prompt("综合商品分析报告", data_summary, prompt, use_cot=True, use_examples=True)
        result = analyzer._generate_content(enhanced_prompt)
    else:
        result = analyzer._generate_content(prompt)
    
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="bi bi-file-text me-2"),
            html.H5("📋 综合执行报告", className="d-inline mb-0")
        ], style={'background-color': '#f8f9fa'}),
        dbc.CardBody([
            dcc.Markdown(result, className="ai-analysis-content"),
            html.Hr(),
            dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                html.Small([
                    "此报告整合了四象限、趋势、排行、分类、结构、库存等7大板块分析。",
                    html.Br(),
                    "建议结合实际情况执行,定期复盘效果。使用模型: 智谱GLM-4.6"
                ])
            ], color="info")
        ])
    ], className="mb-3", style={'border': '2px solid #0d6efd'})


# ==================== 运行应用 ====================
# ==================== Tab 5 场景营销 - ECharts图表渲染函数 ====================

def render_period_orders_chart(order_by_period):
    """时段订单量柱状图 - ECharts版本"""
    option = {
        'title': {'text': '分时段订单量', 'left': 'center', 'top': 10},
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
        'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'top': 50, 'containLabel': True},
        'xAxis': {'type': 'category', 'data': order_by_period.index.tolist(), 'axisLabel': {'rotate': 45, 'interval': 0}},
        'yAxis': {'type': 'value', 'name': '订单量'},
        'series': [{
            'name': '订单量',
            'type': 'bar',
            'data': order_by_period.values.tolist(),
            'itemStyle': {'color': '#5470C6'},
            'label': {'show': True, 'position': 'top'}
        }]
    }
    return DashECharts(option=option, id='period-orders-chart', style={'height': '400px'})


def render_period_orders_chart_plotly(order_by_period):
    """时段订单量柱状图 - Plotly版本(后备)"""
    fig = go.Figure(data=[go.Bar(
        x=order_by_period.index,
        y=order_by_period.values,
        marker_color='lightblue',
        text=order_by_period.values,
        textposition='auto'
    )])
    fig.update_layout(xaxis_title='时段', yaxis_title='订单量', height=400)
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def render_period_price_chart(period_avg_price):
    """时段客单价折线图 - ECharts版本"""
    option = {
        'title': {'text': '分时段客单价趋势', 'left': 'center', 'top': 10},
        'tooltip': {'trigger': 'axis'},
        'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'top': 50, 'containLabel': True},
        'xAxis': {'type': 'category', 'data': period_avg_price.index.tolist(), 'axisLabel': {'rotate': 45, 'interval': 0}},
        'yAxis': {'type': 'value', 'name': '客单价(元)', 'axisLabel': {'formatter': '¥{value}'}},
        'series': [{
            'name': '平均客单价',
            'type': 'line',
            'data': [round(v, 1) for v in period_avg_price.values.tolist()],
            'smooth': True,
            'itemStyle': {'color': '#EE6666'},
            'lineStyle': {'width': 3},
            'areaStyle': {'opacity': 0.3},
            'label': {'show': True, 'formatter': '¥{c}'}
        }]
    }
    return DashECharts(option=option, id='period-price-chart', style={'height': '400px'})


def render_period_price_chart_plotly(period_avg_price):
    """时段客单价折线图 - Plotly版本(后备)"""
    fig = go.Figure(data=[go.Scatter(
        x=period_avg_price.index,
        y=period_avg_price.values,
        mode='lines+markers',
        line=dict(color='orange', width=3),
        marker=dict(size=10)
    )])
    fig.update_layout(xaxis_title='时段', yaxis_title='平均客单价(元)', height=400)
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def render_scenario_orders_chart(scenario_orders):
    """场景订单分布饼图 - ECharts版本"""
    option = {
        'title': {'text': '消费场景订单分布', 'left': 'center', 'top': 10},
        'tooltip': {'trigger': 'item', 'formatter': '{b}: {c} ({d}%)'},
        'legend': {'orient': 'vertical', 'left': 'left', 'top': 'middle'},
        'series': [{
            'name': '订单量',
            'type': 'pie',
            'radius': ['40%', '70%'],
            'center': ['60%', '55%'],
            'data': [{'value': v, 'name': k} for k, v in scenario_orders.items()],
            'emphasis': {'itemStyle': {'shadowBlur': 10, 'shadowOffsetX': 0, 'shadowColor': 'rgba(0, 0, 0, 0.5)'}},
            'label': {'formatter': '{b}\n{c}\n({d}%)'}
        }]
    }
    return DashECharts(option=option, id='scenario-orders-chart', style={'height': '400px'})


def render_scenario_orders_chart_plotly(scenario_orders):
    """场景订单分布饼图 - Plotly版本(后备)"""
    fig = go.Figure(data=[go.Pie(
        labels=scenario_orders.index,
        values=scenario_orders.values,
        hole=0.4,
        textinfo='label+percent'
    )])
    fig.update_layout(height=400)
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def render_scenario_sales_chart(scenario_metrics):
    """场景销售额柱状图 - ECharts版本"""
    option = {
        'title': {'text': '各场景销售额对比', 'left': 'center', 'top': 10},
        'tooltip': {
            'trigger': 'axis',
            'axisPointer': {'type': 'shadow'},
            'formatter': "{b}<br/>销售额: ¥{c}"
        },
        'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'top': 50, 'containLabel': True},
        'xAxis': {'type': 'category', 'data': scenario_metrics['场景'].tolist()},
        'yAxis': {'type': 'value', 'name': '销售额(元)', 'axisLabel': {'formatter': '¥{value}'}},
        'series': [{
            'name': '销售额',
            'type': 'bar',
            'data': [round(v, 1) for v in scenario_metrics['销售额'].tolist()],
            'itemStyle': {'color': '#91CC75'},
            'label': {
                'show': True,
                'position': 'top',
                'formatter': '¥{c}'
            }
        }]
    }
    return DashECharts(option=option, id='scenario-sales-chart', style={'height': '400px'})


def render_scenario_sales_chart_plotly(scenario_metrics):
    """场景销售额柱状图 - Plotly版本(后备)"""
    fig = go.Figure(data=[go.Bar(
        x=scenario_metrics['场景'],
        y=scenario_metrics['销售额'],
        marker_color='lightgreen',
        text=[f'¥{v:,.0f}' for v in scenario_metrics['销售额']],
        textposition='auto'
    )])
    fig.update_layout(xaxis_title='消费场景', yaxis_title='销售额(元)', height=400)
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


def render_cross_heatmap(cross_orders):
    """时段×场景交叉热力图 - ECharts版本"""
    # 准备热力图数据 [[x, y, value], ...]
    heatmap_data = []
    for i, period in enumerate(cross_orders.index):
        for j, scenario in enumerate(cross_orders.columns):
            heatmap_data.append([j, i, float(cross_orders.iloc[i, j])])
    
    option = {
        'title': {'text': '时段×场景交叉热力图', 'left': 'center', 'top': 10},
        'tooltip': {'position': 'top'},
        'grid': {'height': '70%', 'top': '15%'},
        'xAxis': {
            'type': 'category',
            'data': cross_orders.columns.tolist(),
            'splitArea': {'show': True}
        },
        'yAxis': {
            'type': 'category',
            'data': cross_orders.index.tolist(),
            'splitArea': {'show': True}
        },
        'visualMap': {
            'min': 0,
            'max': float(cross_orders.values.max()),
            'calculable': True,
            'orient': 'horizontal',
            'left': 'center',
            'bottom': '5%',
            'inRange': {'color': ['#FFFFCC', '#FFEDA0', '#FED976', '#FEB24C', '#FD8D3C', '#FC4E2A', '#E31A1C', '#BD0026']}
        },
        'series': [{
            'name': '订单量',
            'type': 'heatmap',
            'data': heatmap_data,
            'label': {'show': True},
            'emphasis': {'itemStyle': {'shadowBlur': 10, 'shadowColor': 'rgba(0, 0, 0, 0.5)'}}
        }]
    }
    return DashECharts(option=option, id='cross-heatmap-chart', style={'height': '500px'})


def render_cross_heatmap_plotly(cross_orders):
    """时段×场景交叉热力图 - Plotly版本(后备)"""
    fig = go.Figure(data=[go.Heatmap(
        z=cross_orders.values,
        x=cross_orders.columns.tolist(),
        y=cross_orders.index.tolist(),
        colorscale='YlOrRd',
        text=cross_orders.values,
        texttemplate='%{z}'
    )])
    fig.update_layout(xaxis_title='消费场景', yaxis_title='时段', height=500)
    return dcc.Graph(figure=fig, config={'displayModeBar': False})


# ==================== 性能优化: WebWorker后台计算 (阶段8) ====================

# Callback 1: 加载原始订单数据到Store
@app.callback(
    Output('raw-orders-store', 'data'),
    Input('data-update-trigger', 'data'),
    prevent_initial_call=False
)
def load_raw_orders_to_store(trigger):
    """
    将当前订单数据加载到Store,供WebWorker使用
    阶段8: WebWorker后台计算 - 数据准备
    """
    global GLOBAL_DATA
    
    if GLOBAL_DATA is None or len(GLOBAL_DATA) == 0:
        return []
    
    # 转换为JSON友好格式
    orders = GLOBAL_DATA.head(10000).to_dict('records')  # 限制最多1万条避免过大
    
    # 日期转字符串
    for order in orders:
        if pd.notna(order.get('date')):
            order['date'] = str(order['date'])
        if pd.notna(order.get('日期')):
            order['日期'] = str(order['日期'])
    
    return orders


# Callback 2: Clientside Callback - Worker聚合计算
app.clientside_callback(
    """
    function(orders) {
        // 如果没有数据或Worker不可用,返回空
        if (!orders || orders.length === 0) {
            return null;
        }
        
        // 检查Worker是否可用
        if (typeof(Worker) === 'undefined') {
            console.warn('⚠️ 浏览器不支持WebWorker,跳过后台聚合');
            return null;
        }
        
        if (window.DEBUG_MODE) console.log('🚀 [WebWorker] 启动订单聚合,数据量:', orders.length);
        
        return new Promise((resolve, reject) => {
            const worker = new Worker('/assets/workers/order_aggregator.js');
            
            const startTime = performance.now();
            
            worker.onmessage = function(e) {
                const duration = Math.round(performance.now() - startTime);
                
                if (e.data.success) {
                    if (window.DEBUG_MODE) {
                        console.log('✅ [WebWorker] 聚合完成,耗时:', duration, 'ms');
                        console.log('   - 商品数:', e.data.data.byProduct?.length || 0);
                        console.log('   - 日期数:', e.data.data.byDate?.length || 0);
                        console.log('   - 场景数:', e.data.data.byScene?.length || 0);
                    }
                    worker.terminate();
                    resolve(e.data);
                } else {
                    console.error('❌ [WebWorker] 聚合失败:', e.data.error);
                    worker.terminate();
                    reject(e.data.error);
                }
            };
            
            worker.onerror = function(error) {
                console.error('❌ [WebWorker] Worker错误:', error);
                worker.terminate();
                // 降级:返回null,让服务器端处理
                resolve(null);
            };
            
            // 发送聚合任务
            worker.postMessage({
                orders: orders,
                groupBy: ['product', 'date', 'scene', 'time_period'],
                options: { 
                    topN: 100,  // 最多返回前100
                    sortBy: 'sales' 
                }
            });
        });
    }
    """,
    Output('worker-aggregated-data', 'data'),
    Input('raw-orders-store', 'data'),
    prevent_initial_call=True
)


# ==================== Tab 7: 营销成本分析 ====================

@app.callback(
    Output('tab-7-content', 'children'),
    [Input('main-tabs', 'value'),
     Input('data-update-trigger', 'data')],  # 🔴 监听数据更新
    State('current-store-id', 'data'),
    State('store-data', 'data')
)
def render_tab7_marketing_content(active_tab, data_trigger, store_id, store_data):
    """Tab 7: 营销成本异常分析"""
    if active_tab != 'tab-7':
        raise PreventUpdate
    
    print(f"[Tab7渲染] 门店ID: {store_id}, 数据触发: {data_trigger}, 数据量: {len(store_data) if store_data else 0}")
    
    try:
        # 检查分析器是否可用
        if not TAB7_ANALYZERS_AVAILABLE:
            return dbc.Alert([
                html.H4("⚠️ 功能不可用", className="alert-heading"),
                html.P("营销成本八象限分析功能需要安装相关分析器模块。"),
                html.Hr(),
                html.P("请确保以下文件存在：", className="mb-0"),
                html.Ul([
                    html.Li("科学八象限分析器.py"),
                    html.Li("评分模型分析器.py")
                ])
            ], color="warning", className="m-3")
        
        # 🔴 使用门店数据而非全局数据
        if store_data and len(store_data) > 0:
            df = pd.DataFrame(store_data)
        else:
            df = GLOBAL_DATA.copy()
        
        if df is None or len(df) == 0:
            return dbc.Alert("📊 暂无数据，请先加载数据", color="warning", className="text-center")
        
        # 🔴 剔除耗材数据(购物袋等)
        if '一级分类名' in df.columns:
            original_len = len(df)
            df = df[df['一级分类名'] != '耗材'].copy()
            removed = original_len - len(df)
            if removed > 0:
                print(f"[Tab7] 已剔除耗材数据: {removed} 行", flush=True)
        
        # 🔴 按渠道筛选(只排除咖啡渠道)
        if '渠道' in df.columns:
            excluded_channels = CHANNELS_TO_REMOVE  # 只排除咖啡渠道
            if excluded_channels:  # 只有在有需要排除的渠道时才过滤
                original_len = len(df)
                df = df[~df['渠道'].isin(excluded_channels)].copy()
                removed = original_len - len(df)
                if removed > 0:
                    print(f"[Tab7] 已剔除渠道数据: {removed} 行 ({', '.join(excluded_channels)})", flush=True)
        
        # ✅ 检查必需字段
        required_fields = ['商品名称', '实收价格', '利润额', '订单ID', '月售']
        missing_fields = [f for f in required_fields if f not in df.columns]
        if missing_fields:
            return dbc.Alert(f"❌ 缺失必需字段: {', '.join(missing_fields)}", color="danger", className="text-center")
        
        # 初始化科学方法分析器
        scientific_analyzer = ScientificQuadrantAnalyzer(df, use_category_threshold=True)
        scientific_result = scientific_analyzer.analyze_with_confidence()
        
        # 初始化评分模型分析器
        scoring_analyzer = ScoringModelAnalyzer(df)
        scoring_result = scoring_analyzer.analyze_with_scoring({
            '营销效率': 0.25,
            '盈利能力': 0.45,
            '动销健康': 0.3
        })
        
        # ==================== 创建双维度分析布局 ====================
        layout = html.Div([
            # 页面标题
            dbc.Row([
                dbc.Col([
                    html.H3([
                        html.I(className="bi bi-grid-3x3-gap me-2"),
                        "营销分析看板 - 双维度智能诊断"
                    ], className="text-primary mb-2"),
                    html.P("基于品类动态阈值和综合评分模型的科学分析", 
                          className="text-muted")
                ], md=6),
                dbc.Col([
                    html.Label("筛选条件:", className="fw-bold"),
                    dcc.Dropdown(
                        id='tab7-channel-filter',
                        options=[{'label': '📊 全部渠道', 'value': 'ALL'}] + 
                                ([{'label': ch, 'value': ch} for ch in sorted(df['渠道'].dropna().unique())] if '渠道' in df.columns else []),
                        value='ALL',
                        placeholder="选择渠道",
                        clearable=False,
                        className="mb-2"
                    ),
                    dcc.Dropdown(
                        id='tab7-category-filter',
                        options=[{'label': '📦 全部品类', 'value': 'ALL'}] + 
                                ([{'label': cat, 'value': cat} for cat in sorted(df['一级分类名'].dropna().unique())] if '一级分类名' in df.columns else []),
                        value='ALL',
                        placeholder="选择品类",
                        clearable=False
                    )
                ], md=3),
                dbc.Col([
                    dbc.Button([
                        html.I(className="bi bi-search me-2"),
                        "查看差异对比"
                    ], id="btn-show-difference", color="info", size="lg", className="w-100 mb-1"),
                    dbc.Modal([
                        dbc.ModalHeader("🔍 双方法分类差异对比"),
                        dbc.ModalBody(id='difference-comparison-content'),
                        dbc.ModalFooter(
                            dbc.Button("关闭", id="close-difference-modal", className="ms-auto")
                        )
                    ], id="difference-comparison-modal", size="xl", scrollable=True)
                ], md=3)
            ], className="mb-4"),
            
            
            # 双维度对比区 - 左右分栏
            dbc.Row([
                # 左侧: 科学方法(品类动态阈值)
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-diagram-3 me-2"),
                            html.Strong("🔬 科学方法(品类动态阈值)")
                        ], className="bg-primary text-white"),
                        dbc.CardBody([
                            html.P("特点: 品类自适应、风险控制、置信度评估", className="text-muted small mb-3"),
                            
                            # 关键指标
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.H6("黄金商品", className="mb-1"),
                                        html.H4(id='scientific-golden-count', className="text-success mb-0")
                                    ], className="text-center p-2 border rounded")
                                ], md=4),
                                dbc.Col([
                                    html.Div([
                                        html.H6("淘汰区", className="mb-1"),
                                        html.H4(id='scientific-eliminate-count', className="text-danger mb-0")
                                    ], className="text-center p-2 border rounded")
                                ], md=4),
                                dbc.Col([
                                    html.Div([
                                        html.H6("低置信商品", className="mb-1"),
                                        html.H4(id='scientific-low-confidence-count', className="text-warning mb-0")
                                    ], className="text-center p-2 border rounded")
                                ], md=4)
                            ], className="mb-3"),
                            
                            # 象限分布饼图
                            html.Div([
                                create_scientific_quadrant_pie_echarts(scientific_result.to_dict('records'))
                            ], className="mb-3"),
                            
                            # 置信度分布图
                            html.Div([
                                create_scientific_confidence_bar_echarts(scientific_result.to_dict('records'))
                            ], className="mb-3"),
                            
                            # 品类阈值信息(筛选品类时显示)
                            html.Div(id='scientific-category-threshold-info'),
                            
                            # 导出按钮
                            html.Div([
                                dbc.Button([
                                    html.I(className="bi bi-file-earmark-excel me-2"),
                                    "导出科学分析报告"
                                ], id="export-scientific-btn", color="primary", className="w-100"),
                                dcc.Download(id="download-scientific-data")
                            ])
                        ])
                    ], className="shadow-sm h-100")
                ], md=6),
                
                # 右侧: 评分模型
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-star-fill me-2"),
                            html.Strong("📝 评分模型(综合评估)")
                        ], className="bg-success text-white"),
                        dbc.CardBody([
                            html.P("特点: 快速排名、KPI友好、连续评分", className="text-muted small mb-3"),
                            
                            # 关键指标
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.H6("平均分", className="mb-1"),
                                        html.H4(id='scoring-avg-score', className="text-info mb-0")
                                    ], className="text-center p-2 border rounded")
                                ], md=4),
                                dbc.Col([
                                    html.Div([
                                        html.H6("优秀商品", className="mb-1"),
                                        html.H4(id='scoring-excellent-count', className="text-success mb-0")
                                    ], className="text-center p-2 border rounded")
                                ], md=4),
                                dbc.Col([
                                    html.Div([
                                        html.H6("需优化", className="mb-1"),
                                        html.H4(id='scoring-poor-count', className="text-danger mb-0")
                                    ], className="text-center p-2 border rounded")
                                ], md=4)
                            ], className="mb-3"),
                            
                            # 评分分布柱状图
                            html.Div([
                                create_scoring_distribution_bar_echarts(scoring_result.to_dict('records'))
                            ], className="mb-3"),
                            
                            # 品类平均分(筛选品类时显示)
                            html.Div(id='scoring-category-avg-info'),
                            
                            # 导出按钮
                            html.Div([
                                dbc.Button([
                                    html.I(className="bi bi-file-earmark-excel me-2"),
                                    "导出评分排名报告"
                                ], id="export-scoring-btn", color="success", className="w-100"),
                                dcc.Download(id="download-scoring-data")
                            ])
                        ])
                    ], className="shadow-sm h-100")
                ], md=6)
            ], className="mb-4"),
            
            # 底部: 两种分析模型的定义说明
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="bi bi-book me-2"),
                    html.Strong("📚 两种分析模型说明")
                ], className="bg-info text-white"),
                dbc.CardBody([
                    # 科学方法说明
                    html.Div([
                        html.H5([
                            html.I(className="bi bi-diagram-3 me-2 text-primary"),
                            "🔬 科学方法（品类动态阈值）"
                        ], className="mb-3"),
                        html.P([
                            html.Strong("核心思想："),
                            "不同品类的商品特性不同，不应该用统一标准来评判。"
                        ], className="mb-2"),
                        html.P([
                            html.Strong("工作原理："),
                            html.Br(),
                            "• 根据每个品类的历史数据，自动计算该品类的合理利润率和售罄率",
                            html.Br(),
                            "• 用这个品类专属的标准来判断商品好坏",
                            html.Br(),
                            "• 给出置信度评分，告诉你这个判断有多可靠"
                        ], className="mb-3"),
                        html.Div([
                            html.Small([
                                html.Strong("📌 关于售罄率：", className="text-info"),
                                "订单数据本身已经是卖出的商品，售罄率 = 销量 ÷ (销量 + 剩余库存)，反映商品的销售进度"
                            ], className="d-block mb-2 p-2 bg-info bg-opacity-10 rounded")
                        ]),
                        html.Div([
                            html.Strong("💡 举个例子：", className="text-primary"),
                            html.Div([
                                html.P("饮料类商品：平均利润率20%，售罄率60%", className="mb-1 ms-3"),
                                html.P("生鲜类商品：平均利润率10%，售罄率80%", className="mb-1 ms-3"),
                                html.Br(),
                                html.P("如果一瓶饮料利润率25%、售罄率65% → ", className="mb-1 ms-3", style={'display': 'inline'}),
                                html.Strong("判定为优质商品", className="text-success"),
                                html.Br(),
                                html.P("如果一份生鲜利润率25%、售罄率65% → ", className="mb-1 ms-3", style={'display': 'inline'}),
                                html.Strong("利润好但售罄一般", className="text-warning"),
                                html.Br(),
                                html.P("→ 同样25%利润率，在不同品类中的评价不同！", className="mb-1 ms-3 fst-italic text-muted")
                            ], className="p-3 bg-light rounded mb-3")
                        ]),
                        html.P([
                            html.Strong("适用场景："),
                            "品类多样、需要精细化管理、关注风险控制"
                        ], className="mb-1 text-muted small")
                    ], className="mb-4"),
                    
                    html.Hr(),
                    
                    # 评分模型说明
                    html.Div([
                        html.H5([
                            html.I(className="bi bi-star-fill me-2 text-success"),
                            "📝 评分模型（综合评估）"
                        ], className="mb-3"),
                        html.P([
                            html.Strong("核心思想："),
                            "用一个综合分数快速排名，找出表现最好和最差的商品。"
                        ], className="mb-2"),
                        html.P([
                            html.Strong("工作原理："),
                            html.Br(),
                            "• 把利润率、动销率、销售额等指标都转换成0-100分",
                            html.Br(),
                            "• 按照权重加权平均（盈利能力45%、动销健康30%、销售规模25%）",
                            html.Br(),
                            "• 得出每个商品的综合得分，直接排名"
                        ], className="mb-3"),
                        html.Div([
                            html.Strong("💡 举个例子：", className="text-success"),
                            html.Div([
                                html.P("可口可乐：", className="mb-1 ms-3"),
                                html.P("  • 盈利能力得分：75分（利润率中等）", className="mb-1 ms-4"),
                                html.P("  • 动销健康得分：90分（卖得很好）", className="mb-1 ms-4"),
                                html.P("  • 销售规模得分：95分（销量大）", className="mb-1 ms-4"),
                                html.P("  → 综合得分 = 75×0.45 + 90×0.30 + 95×0.25 = ", className="mb-1 ms-3", style={'display': 'inline'}),
                                html.Strong("84.5分", className="text-success"),
                                html.Br(),
                                html.Br(),
                                html.P("小众饮料：", className="mb-1 ms-3"),
                                html.P("  • 盈利能力得分：85分（利润率高）", className="mb-1 ms-4"),
                                html.P("  • 动销健康得分：40分（动销慢）", className="mb-1 ms-4"),
                                html.P("  • 销售规模得分：30分（销量小）", className="mb-1 ms-4"),
                                html.P("  → 综合得分 = 85×0.45 + 40×0.30 + 30×0.25 = ", className="mb-1 ms-3", style={'display': 'inline'}),
                                html.Strong("58.8分", className="text-warning"),
                                html.Br(),
                                html.P("→ 虽然利润率高，但综合表现一般", className="mb-1 ms-3 fst-italic text-muted")
                            ], className="p-3 bg-light rounded mb-3")
                        ]),
                        html.P([
                            html.Strong("适用场景："),
                            "快速决策、商品表现评比、排名对比、整体分析"
                        ], className="mb-1 text-muted small")
                    ]),
                    
                    html.Hr(className="my-4"),
                    
                    # 两种方法对比
                    html.Div([
                        html.H6("🔄 如何选择？", className="text-center mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Strong("选科学方法", className="text-primary d-block mb-2"),
                                    html.Ul([
                                        html.Li("品类差异大"),
                                        html.Li("需要精细化分析"),
                                        html.Li("关注判断的可靠性")
                                    ], className="small")
                                ], className="p-3 border border-primary rounded")
                            ], md=6),
                            dbc.Col([
                                html.Div([
                                    html.Strong("选评分模型", className="text-success d-block mb-2"),
                                    html.Ul([
                                        html.Li("需要快速排名"),
                                        html.Li("评比商品表现"),
                                        html.Li("找出TOP/底部商品")
                                    ], className="small")
                                ], className="p-3 border border-success rounded")
                            ], md=6)
                        ])
                    ])
                ])
            ], className="shadow-sm mb-4"),
            
            # 隐藏的存储组件
            dcc.Store(id='tab7-scientific-data', data=scientific_result.to_dict('records')),
            dcc.Store(id='tab7-scoring-data', data=scoring_result.to_dict('records')),
            dcc.Store(id='tab7-raw-data', data=df.to_dict('records')),
            dcc.Store(id='tab7-analyzer-data', data=None)  # 用于存储渠道筛选后的分析数据
        ])
        
        return layout
        
    except Exception as e:
        print(f"❌ Tab 7渲染失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"渲染失败: {str(e)}", color="danger")


# Tab 7 子组件回调

@app.callback(
    Output('tab7-analyzer-data', 'data'),
    [Input('tab7-channel-filter', 'value')],
    State('tab7-raw-data', 'data'),
    prevent_initial_call=True
)
def update_tab7_by_channel(channel, raw_data):
    """根据渠道筛选更新营销分析数据"""
    if not raw_data:
        raise PreventUpdate
    
    try:
        from 营销异常分析器 import MarketingAnomalyAnalyzer
        
        df = pd.DataFrame(raw_data)
        
        # 🔴 应用渠道筛选
        if channel != 'ALL' and '渠道' in df.columns:
            df = df[df['渠道'] == channel].copy()
            print(f"[Tab7] 渠道筛选: {channel}, 剩余数据: {len(df)} 行", flush=True)
        
        if len(df) == 0:
            return {
                'anomalies': [],
                'activities': [],
                'top_products': [],
                'quadrants': []
            }
        
        # 重新分析
        analyzer = MarketingAnomalyAnalyzer(df)
        anomalies = analyzer.identify_anomalies(ratio_threshold=0.5, roi_threshold=1.0)
        activities = analyzer.analyze_marketing_activities()
        top_products = analyzer.get_top_marketing_products(n=20)
        quadrant_df = analyzer.analyze_eight_quadrants(
            marketing_threshold=0.5,
            margin_threshold=0.3,
            turnover_method='ratio'
        )
        
        return {
            'anomalies': anomalies.to_dict('records') if len(anomalies) > 0 else [],
            'activities': activities.to_dict('records'),
            'top_products': top_products.to_dict('records'),
            'quadrants': quadrant_df.to_dict('records')
        }
        
    except Exception as e:
        print(f"❌ Tab7渠道筛选失败: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise PreventUpdate

@app.callback(
    Output('anomaly-products-table', 'children'),
    Input('tab7-analyzer-data', 'data'),
    Input('anomaly-level-filter', 'value'),
    Input('ratio-threshold-slider', 'value')
)
def update_anomaly_table(analyzer_data, level_filter, ratio_threshold):
    """更新异常商品表格"""
    if not analyzer_data or not analyzer_data.get('anomalies'):
        return dbc.Alert("未发现异常商品", color="success")
    
    anomalies_df = pd.DataFrame(analyzer_data['anomalies'])
    
    # 应用筛选: 同时使用异常级别和营销占比阈值
    filtered = anomalies_df[
        (anomalies_df['异常级别'] >= level_filter) & 
        (anomalies_df['营销占比'] >= ratio_threshold)
    ].copy()
    
    # 格式化显示
    display_cols = ['商品名称', '月售', '实收价格', '利润额', '营销总成本', 
                    '营销占比', '营销ROI', '异常类型', '异常级别']
    
    if len(filtered) == 0:
        return dbc.Alert(
            f"未发现符合条件的异常商品(级别≥{level_filter}, 营销占比≥{ratio_threshold*100:.0f}%)", 
            color="info"
        )
    
    # 格式化数值
    filtered_display = filtered[display_cols].copy()
    filtered_display['实收价格'] = filtered_display['实收价格'].apply(lambda x: f"¥{x:,.2f}")
    filtered_display['利润额'] = filtered_display['利润额'].apply(lambda x: f"¥{x:,.2f}")
    filtered_display['营销总成本'] = filtered_display['营销总成本'].apply(lambda x: f"¥{x:,.2f}")
    filtered_display['营销占比'] = filtered_display['营销占比'].apply(lambda x: f"{x*100:.1f}%")
    filtered_display['营销ROI'] = filtered_display['营销ROI'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    
    return html.Div([
        dbc.Alert(
            f"发现 {len(filtered)} 个异常商品 (级别≥{level_filter}, 营销占比≥{ratio_threshold*100:.0f}%)", 
            color="warning", 
            className="mb-3"
        ),
        dbc.Table.from_dataframe(
            filtered_display.head(20),
            striped=True,
            bordered=True,
            hover=True,
            size='sm',
            className='table-responsive'
        )
    ])


@app.callback(
    [Output('marketing-activity-pie', 'children'),
     Output('marketing-roi-bar', 'children'),
     Output('activity-details-table', 'children')],
    Input('tab7-analyzer-data', 'data')
)
def update_activity_analysis(analyzer_data):
    """更新营销活动分析图表"""
    if not analyzer_data or not analyzer_data.get('activities'):
        return [dbc.Alert("无活动数据", color="warning")] * 3
    
    activities_df = pd.DataFrame(analyzer_data['activities'])
    
    # 1. 饼图:活动成本分布
    pie_fig = go.Figure(data=[go.Pie(
        labels=activities_df['活动类型'],
        values=activities_df['总成本'],
        hole=0.3,
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>成本: ¥%{value:,.2f}<br>占比: %{percent}<extra></extra>'
    )])
    pie_fig.update_layout(
        title='营销活动成本分布',
        height=350,
        showlegend=True
    )
    pie_chart = dcc.Graph(figure=pie_fig, config={'displayModeBar': False})
    
    # 2. 柱状图:活动ROI对比
    bar_fig = go.Figure(data=[go.Bar(
        x=activities_df['活动类型'],
        y=activities_df['平均ROI'],
        marker_color=activities_df['平均ROI'].apply(lambda x: '#28a745' if x >= 1 else '#dc3545'),
        text=[f"{x:.2f}" for x in activities_df['平均ROI']],
        textposition='outside'
    )])
    bar_fig.add_hline(y=1.0, line_dash="dash", line_color="red",
                     annotation_text="盈亏平衡线 (ROI=1.0)")
    bar_fig.update_layout(
        title='各活动平均ROI',
        xaxis_title='活动类型',
        yaxis_title='ROI',
        height=350
    )
    roi_chart = dcc.Graph(figure=bar_fig, config={'displayModeBar': False})
    
    # 3. 活动详细表格
    table = dbc.Table.from_dataframe(
        activities_df,
        striped=True,
        bordered=True,
        hover=True,
        size='sm'
    )
    
    return pie_chart, roi_chart, table


@app.callback(
    [Output('marketing-bubble-chart', 'children'),
     Output('top-marketing-products-table', 'children')],
    Input('tab7-analyzer-data', 'data')
)
def update_top_products(analyzer_data):
    """更新TOP商品营销分析"""
    if not analyzer_data or not analyzer_data.get('top_products'):
        return [dbc.Alert("无商品数据", color="warning")] * 2
    
    top_df = pd.DataFrame(analyzer_data['top_products'])
    
    # 1. 气泡图
    bubble_fig = go.Figure(data=[go.Scatter(
        x=top_df['月售'],
        y=top_df['营销占比'] * 100,  # 转换为百分比
        mode='markers',
        marker=dict(
            size=top_df['营销总成本'] / 10,  # 气泡大小
            color=top_df['营销ROI'],  # 颜色表示ROI
            colorscale='RdYlGn',  # 红-黄-绿色阶
            showscale=True,
            colorbar=dict(title="ROI"),
            line=dict(width=1, color='white')
        ),
        text=top_df['商品名称'],
        hovertemplate='<b>%{text}</b><br>' +
                     '销量: %{x}<br>' +
                     '营销占比: %{y:.1f}%<br>' +
                     '营销成本: ¥%{marker.size:.2f}<br>' +
                     '<extra></extra>'
    )])
    bubble_fig.add_hline(y=50, line_dash="dash", line_color="red",
                        annotation_text="异常阈值 (50%)")
    bubble_fig.update_layout(
        title='营销效率气泡图 (气泡越大=成本越高,越绿=ROI越高)',
        xaxis_title='销量',
        yaxis_title='营销占比 (%)',
        height=500,
        hovermode='closest'
    )
    bubble_chart = dcc.Graph(figure=bubble_fig, config={'displayModeBar': False})
    
    # 2. TOP商品表格
    display_cols = ['商品名称', '月售', '实收价格', '利润额', '营销总成本', 
                    '营销占比', '营销ROI', '主要营销方式']
    top_display = top_df[display_cols].copy()
    
    # 格式化
    top_display['实收价格'] = top_display['实收价格'].apply(lambda x: f"¥{x:,.2f}")
    top_display['利润额'] = top_display['利润额'].apply(lambda x: f"¥{x:,.2f}")
    top_display['营销总成本'] = top_display['营销总成本'].apply(lambda x: f"¥{x:,.2f}")
    top_display['营销占比'] = top_display['营销占比'].apply(lambda x: f"{x*100:.1f}%")
    top_display['营销ROI'] = top_display['营销ROI'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    
    table = dbc.Table.from_dataframe(
        top_display,
        striped=True,
        bordered=True,
        hover=True,
        size='sm',
        className='table-responsive'
    )
    
    return bubble_chart, table


@app.callback(
    Output('marketing-suggestions', 'children'),
    Input('tab7-analyzer-data', 'data')
)
def generate_marketing_suggestions(analyzer_data):
    """生成营销优化建议"""
    if not analyzer_data:
        return dbc.Alert("数据加载中...", color="info")
    
    anomalies_df = pd.DataFrame(analyzer_data.get('anomalies', []))
    activities_df = pd.DataFrame(analyzer_data.get('activities', []))
    
    suggestions = []
    
    # 建议1:针对异常商品
    if len(anomalies_df) > 0:
        high_ratio_count = len(anomalies_df[anomalies_df['营销占比'] > 0.5])
        suggestions.append(
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="bi bi-exclamation-triangle-fill me-2 text-warning"),
                    f"发现 {high_ratio_count} 个高营销占比商品"
                ], className="bg-light"),
                dbc.CardBody([
                    html.P("这些商品的营销成本超过销售额的50%，建议:"),
                    html.Ul([
                        html.Li("降低配送补贴力度，或设置免配送费门槛"),
                        html.Li("减少商品折扣，改为满减或赠品策略"),
                        html.Li("评估是否为引流商品，若是则控制总量"),
                        html.Li("对比竞品定价，适当提高售价")
                    ])
                ])
            ], className="mb-3")
        )
    
    # 建议2:针对低ROI活动
    if len(activities_df) > 0:
        low_roi_activities = activities_df[activities_df['平均ROI'] < 1.0]
        if len(low_roi_activities) > 0:
            suggestions.append(
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="bi bi-graph-down me-2 text-danger"),
                        f"{len(low_roi_activities)} 类营销活动ROI<1.0"
                    ], className="bg-light"),
                    dbc.CardBody([
                        html.P("以下活动投入产出比不佳:"),
                        html.Ul([html.Li(f"{row['活动类型']}: ROI={row['平均ROI']:.2f}") 
                                for _, row in low_roi_activities.iterrows()]),
                        html.P("优化建议:", className="mt-3 fw-bold"),
                        html.Ul([
                            html.Li("设置使用门槛(如满减改为满80减10)"),
                            html.Li("精准投放给高价值客户"),
                            html.Li("A/B测试不同优惠力度"),
                            html.Li("限制单个用户使用次数")
                        ])
                    ])
                ], className="mb-3")
            )
    
    # 建议3:配送补贴优化(通常是最大成本项)
    if len(activities_df) > 0:
        delivery_activity = activities_df[activities_df['活动类型'] == '配送补贴']
        if len(delivery_activity) > 0:
            delivery_cost_ratio = delivery_activity.iloc[0]['成本占比']
            suggestions.append(
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="bi bi-truck me-2 text-info"),
                        f"配送补贴占营销成本的{delivery_cost_ratio}"
                    ], className="bg-light"),
                    dbc.CardBody([
                        html.P("配送补贴是最大营销成本项，建议:"),
                        html.Ul([
                            html.Li("设置免配送费门槛(如满39元免配送费)"),
                            html.Li("对近距离订单(如<1km)降低补贴"),
                            html.Li("高峰时段适当降低配送补贴"),
                            html.Li("引导用户自提或到店消费")
                        ])
                    ])
                ], className="mb-3")
            )
    
    # 总结建议
    suggestions.append(
        dbc.Card([
            dbc.CardHeader([
                html.I(className="bi bi-lightbulb-fill me-2 text-success"),
                "数据驱动的营销策略"
            ], className="bg-light"),
            dbc.CardBody([
                html.P("基于当前数据分析，优先级排序:"),
                html.Ol([
                    html.Li([html.Strong("高优先级: "), "优化配送补贴策略(成本占比最高)"]),
                    html.Li([html.Strong("中优先级: "), "调整低ROI活动的使用规则"]),
                    html.Li([html.Strong("持续监控: "), "异常商品的营销成本变化"]),
                    html.Li([html.Strong("长期目标: "), "提升整体营销ROI至1.5以上"])
                ]),
                dbc.Alert([
                    html.I(className="bi bi-info-circle me-2"),
                    "建议每周复查一次营销数据,及时调整策略"
                ], color="info", className="mt-3 mb-0")
            ])
        ])
    )
    
    return html.Div(suggestions)


# 八象限分析回调

@app.callback(
    [Output('quadrant-summary-cards', 'children'),
     Output('quadrant-products-table', 'children')],
    [Input('tab7-analyzer-data', 'data'),
     Input('quadrant-filter', 'value')]
)
def update_quadrant_analysis(analyzer_data, selected_quadrant):
    """更新八象限分析"""
    if not analyzer_data or not analyzer_data.get('quadrants'):
        return dbc.Alert("数据加载中...", color="info"), None
    
    quadrant_df = pd.DataFrame(analyzer_data['quadrants'])
    
    # 筛选数据
    if selected_quadrant != 'ALL':
        filtered_df = quadrant_df[quadrant_df['象限编号'] == selected_quadrant].copy()
    else:
        filtered_df = quadrant_df.copy()
    
    # 生成统计卡片
    summary_cards = []
    
    # 按象限统计
    quadrant_stats = quadrant_df.groupby(['象限编号', '象限名称', '优先级']).agg({
        '商品名称': 'count',
        '营销总成本': 'sum',
        '实收价格': 'sum',
        '利润额': 'sum'
    }).reset_index()
    quadrant_stats.columns = ['象限编号', '象限名称', '优先级', '商品数', '营销总成本', '销售额', '利润额']
    
    # 只显示筛选的象限或全部
    if selected_quadrant != 'ALL':
        display_stats = quadrant_stats[quadrant_stats['象限编号'] == selected_quadrant]
    else:
        # 按优先级排序显示
        priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4, 'OK': 5}
        quadrant_stats['排序'] = quadrant_stats['优先级'].map(priority_order)
        display_stats = quadrant_stats.sort_values('排序').drop(columns=['排序'])
    
    for _, row in display_stats.iterrows():
        color = 'danger' if row['优先级'] == 'P0' else ('warning' if row['优先级'] in ['P1','P2'] else 'success')
        card = dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6(row['象限名称'], className="mb-2"),
                    html.P([
                        html.Small(f"商品数: {row['商品数']}", className="d-block"),
                        html.Small(f"营销成本: ¥{row['营销总成本']:,.0f}", className="d-block"),
                        html.Small(f"营销占比: {row['营销总成本']/row['销售额']*100:.1f}%", className="d-block")
                    ], className="mb-0")
                ])
            ], color=color, outline=True)
        ], md=3, className="mb-2")
        summary_cards.append(card)
    
    # 生成商品列表
    if len(filtered_df) == 0:
        table = dbc.Alert(f"未找到{selected_quadrant}象限的商品", color="info")
    else:
        # 准备显示数据 - 包含用户要求的字段
        display_cols = ['商品名称', '象限名称', '优先级', '优化建议',
                       '实收价格', '利润额', '月售', '营销总成本', 
                       '营销占比', '毛利率', '营销ROI']
        
        display_df = filtered_df[display_cols].copy()
        
        # 格式化数值
        display_df['实收价格'] = display_df['实收价格'].apply(lambda x: f"¥{x:,.2f}")
        display_df['利润额'] = display_df['利润额'].apply(lambda x: f"¥{x:,.2f}")
        display_df['营销总成本'] = display_df['营销总成本'].apply(lambda x: f"¥{x:,.2f}")
        display_df['营销占比'] = display_df['营销占比'].apply(lambda x: f"{x*100:.1f}%")
        display_df['毛利率'] = display_df['毛利率'].apply(lambda x: f"{x*100:.1f}%")
        display_df['营销ROI'] = display_df['营销ROI'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
        display_df['月售'] = display_df['月售'].apply(lambda x: f"{x:.0f}")
        
        # 限制显示前50条
        table = html.Div([
            dbc.Alert(f"共 {len(filtered_df)} 个商品，显示前50条", color="info", className="mb-2"),
            dbc.Table.from_dataframe(
                display_df.head(50),
                striped=True,
                bordered=True,
                hover=True,
                size='sm',
                className='table-responsive'
            )
        ])
    
    return dbc.Row(summary_cards), table


@app.callback(
    Output('download-category-trend-data', 'data'),
    Input('export-category-trend-btn', 'n_clicks'),
    State('category-trend-data-store', 'data'),
    State('store-data', 'data'),
    State('current-store-id', 'data'),
    prevent_initial_call=True
)
def export_category_trend_data(n_clicks, category_data, store_data, store_id):
    """导出一级分类销售趋势数据 - 按业务动作分组导出
    
    业务逻辑:
    - Sheet1: 售罄商品明细 (需补货) - 库存=0且近7天有销量
    - Sheet2: 滞销商品明细 (需清仓/下架) - 按滞销程度分级
    - Sheet3: 正常在售商品 (监控) - 库存>0且有销量
    - Sheet4: 分类汇总数据 (管理层视角)
    
    导出字段:
    - 门店名称、商品名称、一级分类名、三级分类名、商品原价、商品实售价、店内码、月售
    - 剩余库存、库存周转天数、日均销量、最后售卖日期、销售额、利润额、利润率
    """
    if not category_data or not store_data:
        return None
    
    import io
    from datetime import datetime, timedelta
    
    # 获取原始数据
    df = pd.DataFrame(store_data)
    
    if len(df) == 0:
        return None
    
    # 获取门店名称
    store_name = df['门店名称'].iloc[0] if '门店名称' in df.columns else "未知门店"
    
    # ==================== 准备商品级别数据 ====================
    
    # 检测库存字段
    stock_col = None
    for col in ['剩余库存', '库存', '期末库存']:
        if col in df.columns:
            stock_col = col
            break
    
    # 检测日期字段
    date_col = '日期' if '日期' in df.columns else '下单时间'
    
    if date_col not in df.columns:
        return None
    
    # 确保日期格式正确
    df[date_col] = pd.to_datetime(df[date_col])
    last_date = df[date_col].max()
    seven_days_ago = last_date - timedelta(days=7)
    
    # 按商品聚合数据
    product_agg = df.groupby('商品名称').agg({
        '门店名称': 'first',
        '一级分类名': 'first',
        '三级分类名': 'first' if '三级分类名' in df.columns else lambda x: '',
        '商品原价': 'first' if '商品原价' in df.columns else lambda x: 0,
        '实收价格': 'first',
        '店内码': 'first' if '店内码' in df.columns else lambda x: '',
        '月售': 'sum',
        '实收价格': 'sum',  # 销售额
        '利润额': 'sum' if '利润额' in df.columns else lambda x: 0,
        date_col: 'max'  # 最后售卖日期
    }).reset_index()
    
    # 重命名列
    product_agg.rename(columns={
        '实收价格': '销售额',
        date_col: '最后售卖日期'
    }, inplace=True)
    
    # 计算利润率
    product_agg['利润率'] = (product_agg['利润额'] / product_agg['销售额'] * 100).fillna(0).round(2)
    
    # ==================== 添加库存信息（双重判断逻辑） ====================
    
    if stock_col:
        # 步骤1: 获取源数据最后一天
        max_date = df[date_col].max()
        
        # 步骤2: 获取商品在最后一天的库存
        last_day_data = df[df[date_col] == max_date]
        last_day_stock_map = last_day_data.groupby('商品名称')[stock_col].last().to_dict()
        
        # 步骤3: 获取商品最后售卖时的库存
        last_sale_stock = df.sort_values(date_col).groupby('商品名称')[stock_col].last()
        
        # 步骤4: 双重判断，优先使用最后一天库存
        def get_final_stock(product_name):
            if product_name in last_day_stock_map:
                return last_day_stock_map[product_name]
            elif product_name in last_sale_stock.index:
                return last_sale_stock.loc[product_name]
            else:
                return 0
        
        product_agg['剩余库存'] = product_agg['商品名称'].apply(get_final_stock)
    else:
        product_agg['剩余库存'] = 0
    
    # ==================== 计算日均销量和库存周转天数 ====================
    
    date_range_days = (df[date_col].max() - df[date_col].min()).days + 1
    product_agg['日均销量'] = (product_agg['月售'] / date_range_days).round(2)
    product_agg['库存周转天数'] = (product_agg['剩余库存'] / product_agg['日均销量'].replace(0, np.nan)).fillna(0).replace([np.inf, -np.inf], 999).round(1)
    
    # ==================== 计算滞销天数 ====================
    
    product_agg['滞销天数'] = (last_date - product_agg['最后售卖日期']).dt.days
    
    # ==================== 按业务动作分类 ====================
    
    # 近7天有销量的商品
    recent_products = set(df[df[date_col] >= seven_days_ago]['商品名称'].unique())
    
    # Sheet1: 售罄商品 (库存=0 且 近7天有销量)
    sellout_df = product_agg[
        (product_agg['剩余库存'] == 0) & 
        (product_agg['商品名称'].isin(recent_products))
    ].copy()
    sellout_df = sellout_df.sort_values('月售', ascending=False)  # 按月售降序
    sellout_df['业务动作'] = '立即补货'
    
    # Sheet2: 滞销商品 (库存>0 且 滞销)
    stagnant_df = product_agg[product_agg['剩余库存'] > 0].copy()
    
    # 滞销分级
    stagnant_df['滞销等级'] = ''
    stagnant_df.loc[stagnant_df['滞销天数'] == 7, '滞销等级'] = '轻度滞销'
    stagnant_df.loc[(stagnant_df['滞销天数'] >= 8) & (stagnant_df['滞销天数'] <= 15), '滞销等级'] = '中度滞销'
    stagnant_df.loc[(stagnant_df['滞销天数'] >= 16) & (stagnant_df['滞销天数'] <= 30), '滞销等级'] = '重度滞销'
    stagnant_df.loc[stagnant_df['滞销天数'] > 30, '滞销等级'] = '超重度滞销'
    
    # 只保留有滞销等级的商品
    stagnant_df = stagnant_df[stagnant_df['滞销等级'] != ''].copy()
    stagnant_df = stagnant_df.sort_values('库存周转天数', ascending=False)  # 按库存周转天数降序
    stagnant_df['业务动作'] = '制定清仓方案或下架'
    
    # Sheet3: 正常在售商品 (库存>0 且 非滞销)
    normal_df = product_agg[
        (product_agg['剩余库存'] > 0) & 
        (~product_agg['商品名称'].isin(stagnant_df['商品名称']))
    ].copy()
    normal_df = normal_df.sort_values('销售额', ascending=False)  # 按销售额降序
    normal_df['业务动作'] = '持续监控'
    
    # Sheet4: 分类汇总数据
    category_summary = pd.DataFrame(category_data)
    
    # ==================== 定义导出字段 ====================
    
    export_fields = [
        '门店名称', '商品名称', '一级分类名', '三级分类名',
        '商品原价', '商品实售价', '店内码', '月售',
        '剩余库存', '库存周转天数', '日均销量', '最后售卖日期',
        '销售额', '利润额', '利润率', '业务动作'
    ]
    
    # 为滞销商品添加额外字段
    stagnant_export_fields = export_fields + ['滞销等级', '滞销天数']
    
    # ==================== 创建Excel文件 ====================
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet1: 售罄商品
        if len(sellout_df) > 0:
            sellout_export = sellout_df[[col for col in export_fields if col in sellout_df.columns]].copy()
            sellout_export.to_excel(writer, sheet_name='售罄商品明细_需补货', index=False)
        
        # Sheet2: 滞销商品
        if len(stagnant_df) > 0:
            stagnant_export = stagnant_df[[col for col in stagnant_export_fields if col in stagnant_df.columns]].copy()
            stagnant_export.to_excel(writer, sheet_name='滞销商品明细_需清仓', index=False)
        
        # Sheet3: 正常在售商品
        if len(normal_df) > 0:
            normal_export = normal_df[[col for col in export_fields if col in normal_df.columns]].copy()
            normal_export.to_excel(writer, sheet_name='正常在售商品_监控', index=False)
        
        # Sheet4: 分类汇总
        if len(category_summary) > 0:
            category_export_cols = [
                '分类', '销售额', '总利润', '利润率',
                '总销量', '当前库存', '日均销量', '库存周转天数',
                '售罄品数', 
                '轻度滞销', '中度滞销', '重度滞销', '超重度滞销', '滞销品总数'
            ]
            category_export_cols = [col for col in category_export_cols if col in category_summary.columns]
            category_export = category_summary[category_export_cols].copy()
            category_export.to_excel(writer, sheet_name='分类汇总_管理层视角', index=False)
    
    output.seek(0)
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{store_name}_一级分类销售分析_{timestamp}.xlsx"
    
    return dcc.send_bytes(output.getvalue(), filename)


@app.callback(
    Output('download-quadrant-data-tab7', 'data'),
    Input('export-quadrant-btn', 'n_clicks'),
    State('tab7-analyzer-data', 'data'),
    State('quadrant-filter', 'value'),
    State('tab7-channel-filter', 'value'),  # 🔴 添加渠道参数
    prevent_initial_call=True
)
def export_quadrant_data_tab7(n_clicks, analyzer_data, selected_quadrant, channel):
    """导出八象限分析数据（支持渠道区分）"""
    if not analyzer_data or not analyzer_data.get('quadrants'):
        return None
    
    quadrant_df = pd.DataFrame(analyzer_data['quadrants'])
    
    # 筛选数据
    if selected_quadrant != 'ALL':
        export_df = quadrant_df[quadrant_df['象限编号'] == selected_quadrant].copy()
    else:
        export_df = quadrant_df.copy()
    
    # 选择导出字段 - 包含用户要求的所有字段
    export_cols = [
        '商品名称', '象限编号', '象限名称', '优先级', '优化建议',
        '营销等级', '毛利等级', '动销等级',
        '商品原价', '实收价格', '利润额', '毛利率',
        '月售', '剩余库存', '营销总成本', '营销占比', '营销ROI'
    ]
    
    # 只保留存在的列
    export_cols = [col for col in export_cols if col in export_df.columns]
    export_df = export_df[export_cols]
    
    # 生成文件名（包含渠道信息）
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 🔴 文件名中包含渠道信息
    channel_suffix = "全部渠道" if channel == 'ALL' else channel
    quadrant_suffix = selected_quadrant if selected_quadrant != 'ALL' else '全部象限'
    filename = f"营销分析_{channel_suffix}_{quadrant_suffix}_{timestamp}.xlsx"
    
    return dcc.send_data_frame(export_df.to_excel, filename, index=False, sheet_name='八象限分析')


@app.callback(
    Output('download-scientific-data', 'data'),
    Input('export-scientific-btn', 'n_clicks'),
    State('tab7-scientific-data', 'data'),
    State('tab7-channel-filter', 'value'),
    prevent_initial_call=True
)
def export_scientific_analysis(n_clicks, scientific_data, channel):
    """导出科学分析报告（品类动态阈值方法）- 既要完整数据又要多维度分析"""
    print(f"[导出科学分析] 点击次数: {n_clicks}, 数据量: {len(scientific_data) if scientific_data else 0}")
    
    if not scientific_data:
        print("[导出科学分析] ❌ 无数据")
        return None
    
    import io
    from datetime import datetime
    
    quadrant_df = pd.DataFrame(scientific_data)
    print(f"[导出科学分析] ✅ 准备导出 {len(quadrant_df)} 条数据，共 {len(quadrant_df.columns)} 个字段")
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    channel_suffix = "全部渠道" if channel == 'ALL' else channel
    filename = f"科学分析报告_{channel_suffix}_{timestamp}.xlsx"
    
    # 准备导出数据 - 既要完整数据又要多维度分析
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet1: 完整的29字段数据（总表）
        quadrant_df.to_excel(writer, sheet_name='科学分析报告', index=False)
        
        # Sheet2: 八象限分布汇总
        if '象限编号' in quadrant_df.columns and '象限名称' in quadrant_df.columns:
            quadrant_summary = quadrant_df.groupby(['象限编号', '象限名称']).agg({
                '商品名称': 'count',
                '利润额': 'sum',
                '月售': 'sum',
                '营销总成本': 'sum'
            }).reset_index()
            quadrant_summary.columns = ['象限编号', '象限名称', '商品数', '总利润', '总销量', '总营销成本']
            quadrant_summary['平均利润'] = quadrant_summary['总利润'] / quadrant_summary['商品数']
            quadrant_summary['营销ROI'] = quadrant_summary['总利润'] / quadrant_summary['总营销成本']
            quadrant_summary = quadrant_summary.sort_values('象限编号')
            quadrant_summary.to_excel(writer, sheet_name='象限分布汇总', index=False)
        
        # Sheet3-6: 四维置信度分析
        confidence_dims = [
            ('营销置信度', '营销维度分析'),
            ('毛利置信度', '毛利维度分析'),
            ('动销置信度', '动销维度分析'),
            ('分类置信度', '分类维度分析')
        ]
        
        for conf_col, sheet_name in confidence_dims:
            if conf_col in quadrant_df.columns:
                # 动态选择存在的字段
                base_cols = ['商品名称', conf_col, '象限名称', '优先级',
                            '商品原价', '实收价格', '利润额', '月售', '营销总成本']
                available_cols = [col for col in base_cols if col in quadrant_df.columns]
                
                # 按置信度降序排序
                conf_df = quadrant_df[available_cols].copy()
                conf_df = conf_df.sort_values(conf_col, ascending=False)
                conf_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Sheet7: 优先级分组统计
        if '优先级' in quadrant_df.columns:
            priority_stats = quadrant_df.groupby('优先级').agg({
                '商品名称': 'count',
                '利润额': 'sum',
                '月售': 'sum',
                '营销总成本': 'sum'
            }).reset_index()
            priority_stats.columns = ['优先级', '商品数', '总利润', '总销量', '总营销成本']
            priority_stats['平均利润'] = priority_stats['总利润'] / priority_stats['商品数']
            priority_stats.to_excel(writer, sheet_name='优先级统计', index=False)
    
    output.seek(0)
    return dcc.send_bytes(output.getvalue(), filename)


@app.callback(
    Output('download-scoring-data', 'data'),
    Input('export-scoring-btn', 'n_clicks'),
    State('tab7-scoring-data', 'data'),
    State('tab7-channel-filter', 'value'),
    prevent_initial_call=True
)
def export_scoring_analysis(n_clicks, scoring_data, channel):
    """导出评分排名报告（通用阈值评分方法）- 既要完整数据又要多维度分析"""
    print(f"[导出评分排名] 点击次数: {n_clicks}, 数据量: {len(scoring_data) if scoring_data else 0}")
    
    if not scoring_data:
        print("[导出评分排名] ❌ 无数据")
        return None
    
    import io
    from datetime import datetime
    
    quadrant_df = pd.DataFrame(scoring_data)
    print(f"[导出评分排名] ✅ 准备导出 {len(quadrant_df)} 条数据，共 {len(quadrant_df.columns)} 个字段")
    
    # 按综合得分排序（如果有综合得分字段）
    if '综合得分' in quadrant_df.columns:
        quadrant_df = quadrant_df.sort_values('综合得分', ascending=False)
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    channel_suffix = "全部渠道" if channel == 'ALL' else channel
    filename = f"评分排名报告_{channel_suffix}_{timestamp}.xlsx"
    
    # 准备导出数据 - 既要完整数据又要多维度分析
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet1: 完整的28字段数据（总表）
        quadrant_df.to_excel(writer, sheet_name='评分排名报告', index=False)
        
        # Sheet2: 综合排名TOP100
        if '综合得分' in quadrant_df.columns:
            # 动态选择存在的字段
            base_cols = ['商品名称', '综合得分', '营销效率分', '盈利能力分', '动销健康分',
                        '象限名称', '优先级', '利润额', '月售', '营销总成本']
            available_cols = [col for col in base_cols if col in quadrant_df.columns]
            
            top_products = quadrant_df.head(100)[available_cols].copy()
            top_products['排名'] = range(1, len(top_products) + 1)
            cols = ['排名'] + [col for col in top_products.columns if col != '排名']
            top_products[cols].to_excel(writer, sheet_name='综合排名TOP100', index=False)
        
        # Sheet3-5: 三维评分分析
        score_dims = [
            ('营销效率分', '营销效率维度'),
            ('盈利能力分', '盈利能力维度'),
            ('动销健康分', '动销健康维度')
        ]
        
        for score_col, sheet_name in score_dims:
            if score_col in quadrant_df.columns:
                # 动态选择存在的字段
                base_cols = ['商品名称', score_col, '综合得分', '象限名称', '优先级',
                            '商品原价', '实收价格', '利润额', '月售', '营销总成本']
                available_cols = [col for col in base_cols if col in quadrant_df.columns]
                
                # 按该维度评分降序排序
                score_df = quadrant_df[available_cols].copy()
                score_df = score_df.sort_values(score_col, ascending=False)
                score_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Sheet6: 按象限分组
        if '象限编号' in quadrant_df.columns and '象限名称' in quadrant_df.columns:
            quadrant_stats = quadrant_df.groupby(['象限编号', '象限名称']).agg({
                '商品名称': 'count',
                '综合得分': 'mean',
                '利润额': 'sum',
                '月售': 'sum',
                '营销总成本': 'sum'
            }).reset_index()
            quadrant_stats.columns = ['象限编号', '象限名称', '商品数', '平均综合得分', '总利润', '总销量', '总营销成本']
            quadrant_stats = quadrant_stats.sort_values('象限编号')
            quadrant_stats.to_excel(writer, sheet_name='象限分组统计', index=False)
        
        # Sheet7: 评级分布统计
        if '综合得分' in quadrant_df.columns:
            # 按综合得分分段统计
            def get_grade(score):
                if score >= 80:
                    return '⭐优秀(80-100)'
                elif score >= 60:
                    return '✅良好(60-80)'
                elif score >= 40:
                    return '📊中等(40-60)'
                elif score >= 20:
                    return '⚠️待改进(20-40)'
                else:
                    return '❌需优化(0-20)'
            
            quadrant_df['评级'] = quadrant_df['综合得分'].apply(get_grade)
            grade_stats = quadrant_df.groupby('评级').agg({
                '商品名称': 'count',
                '综合得分': 'mean',
                '利润额': 'sum',
                '月售': 'sum'
            }).reset_index()
            grade_stats.columns = ['评级', '商品数', '平均得分', '总利润', '总销量']
            # 按评级排序
            grade_order = ['⭐优秀(80-100)', '✅良好(60-80)', '📊中等(40-60)', '⚠️待改进(20-40)', '❌需优化(0-20)']
            grade_stats['排序'] = grade_stats['评级'].apply(lambda x: grade_order.index(x) if x in grade_order else 99)
            grade_stats = grade_stats.sort_values('排序').drop('排序', axis=1)
            grade_stats.to_excel(writer, sheet_name='评级分布统计', index=False)
    
    output.seek(0)
    return dcc.send_bytes(output.getvalue(), filename)


@app.callback(
    Output('download-tab7-full-report', 'data'),
    Input('export-tab7-full-report-btn', 'n_clicks'),
    State('tab7-analyzer-data', 'data'),
    State('tab7-channel-filter', 'value'),
    State('tab7-raw-data', 'data'),
    State('current-store-id', 'data'),
    prevent_initial_call=True
)
def export_tab7_full_report(n_clicks, analyzer_data, channel, raw_data, store_id):
    """导出完整营销分析报告 - 按业务动作分组的多Sheet导出
    
    业务逻辑:
    - Sheet1: 异常商品明细_需优化 (按优先级分组)
    - Sheet2: 营销活动效率分析 (各活动ROI对比)
    - Sheet3: TOP营销成本商品 (按营销总成本降序)
    - Sheet4: 八象限分析 (按象限和优先级分组)
    - Sheet5: 营销策略建议汇总
    """
    if not analyzer_data or not raw_data:
        return None
    
    import io
    from datetime import datetime
    
    # 获取原始数据
    df = pd.DataFrame(raw_data)
    
    if len(df) == 0:
        return None
    
    # 获取门店名称和日期范围
    store_name = df['门店名称'].iloc[0] if '门店名称' in df.columns else "未知门店"
    
    date_col = '日期' if '日期' in df.columns else '下单时间'
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
        date_start = df[date_col].min().strftime('%Y%m%d')
        date_end = df[date_col].max().strftime('%Y%m%d')
        date_range_str = f"{date_start}-{date_end}"
    else:
        date_range_str = "未知日期"
    
    # 应用渠道筛选（与界面一致）
    if channel != 'ALL' and '渠道' in df.columns:
        df = df[df['渠道'] == channel].copy()
    
    # ==================== Sheet1: 异常商品明细_需优化 ====================
    
    anomalies_df = pd.DataFrame(analyzer_data.get('anomalies', []))
    
    if len(anomalies_df) > 0:
        # 按优先级分组
        anomalies_df['优先级排序'] = anomalies_df['异常级别'].map({
            10: 'P0-高危', 7: 'P1-严重', 5: 'P2-中等', 3: 'P3-轻微'
        })
        anomalies_df = anomalies_df.sort_values(['异常级别', '营销占比'], ascending=[False, False])
        
        anomalies_export_cols = [
            '商品名称', '异常级别', '优先级排序', '异常类型',
            '营销占比', '营销ROI', '月售', '商品原价', '商品实售价', '实收价格', '利润额',
            '营销总成本', '优化建议'
        ]
        
        # 添加渠道列（如果有）
        if '渠道' in df.columns:
            product_channel = df.groupby('商品名称')['渠道'].first().to_dict()
            anomalies_df['渠道'] = anomalies_df['商品名称'].map(product_channel)
            anomalies_export_cols.insert(1, '渠道')
        
        # 添加店内码列（如果有）
        if '店内码' in df.columns:
            product_code = df.groupby('商品名称')['店内码'].first().to_dict()
            anomalies_df['店内码'] = anomalies_df['商品名称'].map(product_code)
            anomalies_export_cols.insert(1, '店内码')
        
        # 添加商品原价和商品实售价（从原始数据映射）
        if '商品原价' in df.columns:
            product_original_price = df.groupby('商品名称')['商品原价'].first().to_dict()
            anomalies_df['商品原价'] = anomalies_df['商品名称'].map(product_original_price)
        
        if '商品实售价' in df.columns:
            product_sale_price = df.groupby('商品名称')['商品实售价'].first().to_dict()
            anomalies_df['商品实售价'] = anomalies_df['商品名称'].map(product_sale_price)
        
        anomalies_export_cols = [col for col in anomalies_export_cols if col in anomalies_df.columns]
        anomalies_export = anomalies_df[anomalies_export_cols].copy()
        
        # 添加业务动作列
        anomalies_export['业务动作'] = '立即优化营销策略'
    else:
        anomalies_export = pd.DataFrame()
    
    # ==================== Sheet2: 营销活动效率分析 ====================
    
    activities_df = pd.DataFrame(analyzer_data.get('activities', []))
    
    if len(activities_df) > 0:
        activities_export_cols = [
            '活动类型', '使用次数', '使用率', '总成本', '成本占比',
            '带来销售额', '带来利润', '平均ROI', '平均单次成本', '最高单次成本'
        ]
        activities_export_cols = [col for col in activities_export_cols if col in activities_df.columns]
        activities_export = activities_df[activities_export_cols].copy()
        
        # 添加建议列
        activities_export['优化建议'] = activities_export.apply(
            lambda row: f"ROI={row['平均ROI']:.2f}, {'建议加大投入' if row['平均ROI'] > 2 else '建议优化成本'}" if pd.notna(row.get('平均ROI')) else '',
            axis=1
        )
    else:
        activities_export = pd.DataFrame()
    
    # ==================== Sheet3: TOP营销成本商品 ====================
    
    top_products_df = pd.DataFrame(analyzer_data.get('top_products', []))
    
    if len(top_products_df) > 0:
        top_products_export_cols = [
            '商品名称', '营销总成本', '营销占比', '营销ROI',
            '月售', '商品原价', '商品实售价', '实收价格', '利润额', '主要营销方式', '订单ID'
        ]
        
        # 添加渠道列（如果有）
        if '渠道' in df.columns:
            product_channel = df.groupby('商品名称')['渠道'].first().to_dict()
            top_products_df['渠道'] = top_products_df['商品名称'].map(product_channel)
            top_products_export_cols.insert(1, '渠道')
        
        # 添加店内码列（如果有）
        if '店内码' in df.columns:
            product_code = df.groupby('商品名称')['店内码'].first().to_dict()
            top_products_df['店内码'] = top_products_df['商品名称'].map(product_code)
            top_products_export_cols.insert(1, '店内码')
        
        # 添加商品原价和商品实售价（从原始数据映射）
        if '商品原价' in df.columns:
            product_original_price = df.groupby('商品名称')['商品原价'].first().to_dict()
            top_products_df['商品原价'] = top_products_df['商品名称'].map(product_original_price)
        
        if '商品实售价' in df.columns:
            product_sale_price = df.groupby('商品名称')['商品实售价'].first().to_dict()
            top_products_df['商品实售价'] = top_products_df['商品名称'].map(product_sale_price)
        
        top_products_export_cols = [col for col in top_products_export_cols if col in top_products_df.columns]
        top_products_export = top_products_df[top_products_export_cols].copy()
        
        # 重命名订单ID列
        if '订单ID' in top_products_export.columns:
            top_products_export.rename(columns={'订单ID': '订单数'}, inplace=True)
    else:
        top_products_export = pd.DataFrame()
    
    # ==================== Sheet4: 八象限分析 ====================
    
    quadrants_df = pd.DataFrame(analyzer_data.get('quadrants', []))
    
    if len(quadrants_df) > 0:
        quadrants_export_cols = [
            '商品名称', '象限编号', '象限名称', '优先级', '优化建议',
            '营销等级', '毛利等级', '动销等级',
            '商品原价', '商品实售价', '实收价格', '利润额', '毛利率',
            '月售', '剩余库存', '营销总成本', '营销占比', '营销ROI'
        ]
        
        # 添加渠道列（如果有）
        if '渠道' in df.columns:
            product_channel = df.groupby('商品名称')['渠道'].first().to_dict()
            quadrants_df['渠道'] = quadrants_df['商品名称'].map(product_channel)
            quadrants_export_cols.insert(1, '渠道')
        
        # 添加店内码列（如果有）
        if '店内码' in df.columns:
            product_code = df.groupby('商品名称')['店内码'].first().to_dict()
            quadrants_df['店内码'] = quadrants_df['商品名称'].map(product_code)
            quadrants_export_cols.insert(1, '店内码')
        
        # 添加商品实售价（从原始数据映射，商品原价在quadrants分析时已包含）
        if '商品实售价' in df.columns:
            product_sale_price = df.groupby('商品名称')['商品实售价'].first().to_dict()
            quadrants_df['商品实售价'] = quadrants_df['商品名称'].map(product_sale_price)
        
        quadrants_export_cols = [col for col in quadrants_export_cols if col in quadrants_df.columns]
        quadrants_export = quadrants_df[quadrants_export_cols].copy()
        
        # 按优先级和营销占比排序
        priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4, 'OK': 5}
        quadrants_export['排序'] = quadrants_export['优先级'].map(priority_order)
        quadrants_export = quadrants_export.sort_values(['排序', '营销占比'], ascending=[True, False])
        quadrants_export = quadrants_export.drop(columns=['排序'])
    else:
        quadrants_export = pd.DataFrame()
    
    # ==================== Sheet5: 营销策略建议汇总 ====================
    
    suggestions = []
    
    # 1. 异常商品建议
    if len(anomalies_df) > 0:
        p0_count = len(anomalies_df[anomalies_df['异常级别'] >= 10])
        p1_count = len(anomalies_df[anomalies_df['异常级别'] >= 7])
        suggestions.append({
            '类别': '异常商品',
            '数量': len(anomalies_df),
            '重点关注': f"P0高危{p0_count}个, P1严重{p1_count}个",
            '建议': '立即优化营销策略，降低营销占比或提升利润率'
        })
    
    # 2. 营销活动建议
    if len(activities_df) > 0:
        best_activity = activities_df.iloc[0] if '平均ROI' in activities_df.columns else None
        if best_activity is not None and pd.notna(best_activity.get('平均ROI')):
            suggestions.append({
                '类别': '营销活动',
                '数量': len(activities_df),
                '重点关注': f"最优活动: {best_activity['活动类型']} (ROI={best_activity['平均ROI']:.2f})",
                '建议': f"建议加大{best_activity['活动类型']}投入，总成本¥{activities_df['总成本'].sum():,.2f}"
            })
    
    # 3. 八象限建议
    if len(quadrants_df) > 0:
        p0_quadrants = quadrants_df[quadrants_df['优先级'] == 'P0']
        if len(p0_quadrants) > 0:
            suggestions.append({
                '类别': '八象限分析',
                '数量': len(quadrants_df),
                '重点关注': f"P0优先级{len(p0_quadrants)}个商品需立即处理",
                '建议': f"重点优化{p0_quadrants.iloc[0]['象限名称']}象限商品"
            })
    
    # 4. 整体ROI建议
    if len(df) > 0:
        total_marketing = df['营销总成本'].sum() if '营销总成本' in df.columns else 0
        total_profit = df['利润额'].sum() if '利润额' in df.columns else 0
        overall_roi = total_profit / total_marketing if total_marketing > 0 else 0
        
        suggestions.append({
            '类别': '整体营销ROI',
            '数量': f"{overall_roi:.2f}",
            '重点关注': f"营销总成本¥{total_marketing:,.2f}, 带来利润¥{total_profit:,.2f}",
            '建议': f"{'营销效率良好，建议维持' if overall_roi > 1 else '营销成本过高，建议优化'}"
        })
    
    suggestions_export = pd.DataFrame(suggestions)
    
    # ==================== 创建Excel文件 ====================
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet1: 异常商品
        if len(anomalies_export) > 0:
            anomalies_export.to_excel(writer, sheet_name='异常商品明细_需优化', index=False)
        
        # Sheet2: 营销活动
        if len(activities_export) > 0:
            activities_export.to_excel(writer, sheet_name='营销活动效率分析', index=False)
        
        # Sheet3: TOP商品
        if len(top_products_export) > 0:
            top_products_export.to_excel(writer, sheet_name='TOP营销成本商品', index=False)
        
        # Sheet4: 八象限
        if len(quadrants_export) > 0:
            quadrants_export.to_excel(writer, sheet_name='八象限分析', index=False)
        
        # Sheet5: 策略建议
        if len(suggestions_export) > 0:
            suggestions_export.to_excel(writer, sheet_name='营销策略建议汇总', index=False)
    
    output.seek(0)
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    channel_suffix = "全部渠道" if channel == 'ALL' else channel
    filename = f"{store_name}_营销分析报告_{channel_suffix}_{date_range_str}_{timestamp}.xlsx"
    
    return dcc.send_bytes(output.getvalue(), filename)


@app.callback(
    Output('download-aov-analysis', 'data'),
    Input('export-aov-analysis-btn', 'n_clicks'),
    State('store-data', 'data'),
    State('cached-order-agg', 'data'),
    State('current-store-id', 'data'),
    prevent_initial_call=True
)
def export_aov_analysis(n_clicks, store_data, cached_agg, store_id):
    """导出客单价深度分析报告
    
    业务逻辑（增强版）:
    - Sheet1: 客单价分析_汇总（整体价格区间分布）
    - Sheet2: 渠道客单价对比（各渠道在不同价格区间的表现）
    - Sheet3: 购物篮深度分析（各价格区间的SKU购买情况）
    - Sheet4.1~4.8: 各价格区间商品明细（含渠道、利润率、智能建议）
    
    核心洞察：
    1. 发现不同渠道的客单价特征，优化渠道运营策略
    2. 分析购物篮深度，识别凑单机会
    3. 商品级别的智能建议，指导采购和促销决策
    """
    if not store_data:
        return None
    
    import io
    from datetime import datetime
    
    df = pd.DataFrame(store_data)
    
    if len(df) == 0:
        return None
    
    # 获取门店名称和日期范围
    store_name = df['门店名称'].iloc[0] if '门店名称' in df.columns else "未知门店"
    
    date_col = '日期' if '日期' in df.columns else '下单时间'
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
        date_start = df[date_col].min().strftime('%Y%m%d')
        date_end = df[date_col].max().strftime('%Y%m%d')
        date_range_str = f"{date_start}-{date_end}"
    else:
        date_range_str = "未知日期"
    
    # 🔧 从缓存读取order_agg数据（如果有）
    if cached_agg:
        order_agg = pd.DataFrame(cached_agg)
    else:
        # 如果缓存为空，现场聚合 (✅ 包含实收价格)
        agg_dict = {
            '商品实售价': 'sum',
            '订单实际利润': 'first',
            '营销成本': 'sum'
        }
        if '实收价格' in df.columns:
            agg_dict['实收价格'] = 'sum'
        if '预计订单收入' in df.columns:
            agg_dict['预计订单收入'] = 'first'
        if '订单总收入' in df.columns:
            agg_dict['订单总收入'] = 'first'
        
        order_agg = df.groupby('订单ID').agg(agg_dict).reset_index()
    
    # 🔧 剔除咖啡渠道（不再排除闪购小程序和收银机订单）
    exclude_channels = CHANNELS_TO_REMOVE
    
    # 统一订单ID类型
    df['订单ID'] = df['订单ID'].astype(str)
    order_agg['订单ID'] = order_agg['订单ID'].astype(str)
    
    # 从df中获取每个订单的渠道信息
    if '渠道' in df.columns:
        order_channel = df.groupby('订单ID')['渠道'].first().reset_index()
        order_channel['订单ID'] = order_channel['订单ID'].astype(str)
        order_agg = order_agg.merge(order_channel, on='订单ID', how='left')
        
        # 过滤掉排除的渠道
        order_agg = order_agg[~order_agg['渠道'].isin(exclude_channels)].copy()
    
    if len(order_agg) == 0:
        return None
    
    # ✅ 计算客单价（使用实收价格）
    if '实收价格' in order_agg.columns:
        order_agg['客单价'] = order_agg['实收价格']
    elif '预计订单收入' in order_agg.columns:
        order_agg['客单价'] = order_agg['预计订单收入']
    else:
        order_agg['客单价'] = order_agg['实收价格']
    
    # ========== 客单价分区间分析 ==========
    # 定义客单价区间
    bins = [0, 10, 20, 30, 40, 50, 100, 200, float('inf')]
    labels = ['0-10元', '10-20元', '20-30元', '30-40元', '40-50元', '50-100元', '100-200元', '200元以上']
    
    order_agg['客单价区间'] = pd.cut(order_agg['客单价'], bins=bins, labels=labels)
    
    # 将客单价区间合并回原始df，用于后续商品级别分析
    df_with_zone = df.merge(
        order_agg[['订单ID', '客单价区间']], 
        on='订单ID', 
        how='left'
    )
    
    # 统计各区间订单数和占比
    aov_dist = order_agg['客单价区间'].value_counts().sort_index()
    aov_dist_pct = (aov_dist / len(order_agg) * 100).round(1)
    
    # 各区间平均利润
    aov_avg_profit = order_agg.groupby('客单价区间')['订单实际利润'].mean()
    
    # 各区间销售额占比 (✅ 使用实收价格)
    sales_field = '实收价格'
    aov_sales = order_agg.groupby('客单价区间')[sales_field].sum()
    aov_sales_pct = (aov_sales / order_agg[sales_field].sum() * 100).round(1)
    
    # 价格分组（低价区、主流区、高价区）
    def get_price_group(zone):
        if zone in ['0-10元', '10-20元']:
            return '低价区'
        elif zone in ['20-30元', '30-40元', '40-50元']:
            return '主流区'
        else:
            return '高价区'
    
    # Sheet1: 客单价分析汇总
    aov_stats = pd.DataFrame({
        '客单价区间': labels,
        '价格分组': [get_price_group(z) for z in labels],
        '订单数': [int(aov_dist.get(label, 0)) for label in labels],
        '订单占比(%)': [aov_dist_pct.get(label, 0) for label in labels],
        '平均利润(元)': [aov_avg_profit.get(label, 0) for label in labels],
        '销售额占比(%)': [aov_sales_pct.get(label, 0) for label in labels]
    })
    
    aov_export = aov_stats[[
        '客单价区间', '价格分组', '订单数', '订单占比(%)', 
        '平均利润(元)', '销售额占比(%)'
    ]].copy()
    
    # ========== 新增Sheet: 渠道×客单价交叉分析 ==========
    channel_aov_analysis = []
    
    if '渠道' in order_agg.columns:
        for channel in order_agg['渠道'].unique():
            if pd.isna(channel):
                continue
            
            channel_orders = order_agg[order_agg['渠道'] == channel]
            
            for zone in labels:
                zone_orders = channel_orders[channel_orders['客单价区间'] == zone]
                zone_count = len(zone_orders)
                
                if zone_count > 0:
                    channel_aov_analysis.append({
                        '渠道': channel,
                        '客单价区间': zone,
                        '价格分组': get_price_group(zone),
                        '订单数': zone_count,
                        '渠道内占比(%)': round(zone_count / len(channel_orders) * 100, 1),
                        '平均客单价(元)': round(zone_orders['客单价'].mean(), 2),
                        '平均利润(元)': round(zone_orders['订单实际利润'].mean(), 2) if '订单实际利润' in zone_orders.columns else 0
                    })
    
    channel_aov_export = pd.DataFrame(channel_aov_analysis) if channel_aov_analysis else pd.DataFrame()
    
    # ========== 新增Sheet: 购物篮深度分析 ==========
    basket_analysis = []
    
    # 为每个订单计算SKU数量
    if '订单ID' in df.columns and '商品名称' in df.columns:
        order_sku_count = df.groupby('订单ID')['商品名称'].nunique().reset_index()
        order_sku_count.columns = ['订单ID', 'SKU数']
        order_sku_count['订单ID'] = order_sku_count['订单ID'].astype(str)
        
        # 合并到order_agg
        order_agg_with_sku = order_agg.merge(order_sku_count, on='订单ID', how='left')
        
        # 按客单价区间分析购物篮
        for zone in labels:
            zone_orders = order_agg_with_sku[order_agg_with_sku['客单价区间'] == zone]
            
            if len(zone_orders) > 0 and 'SKU数' in zone_orders.columns:
                basket_analysis.append({
                    '客单价区间': zone,
                    '价格分组': get_price_group(zone),
                    '订单数': len(zone_orders),
                    '平均SKU数': round(zone_orders['SKU数'].mean(), 1),
                    'SKU中位数': zone_orders['SKU数'].median(),
                    '最大SKU数': int(zone_orders['SKU数'].max()),
                    '单SKU订单占比(%)': round((zone_orders['SKU数'] == 1).sum() / len(zone_orders) * 100, 1),
                    '3SKU以上占比(%)': round((zone_orders['SKU数'] >= 3).sum() / len(zone_orders) * 100, 1),
                    '购物篮建议': '建议推荐凑单商品' if zone_orders['SKU数'].mean() < 2.5 else '购物篮较丰富，可推荐套餐'
                })
    
    basket_export = pd.DataFrame(basket_analysis) if basket_analysis else pd.DataFrame()
    
    # ========== Sheet2.X: 各价格区间商品明细 ==========
    aov_detail_sheets = {}
    
    for zone in labels:
        # 筛选该价格区间的订单
        zone_df = df_with_zone[df_with_zone['客单价区间'] == zone].copy()
        
        if len(zone_df) == 0:
            continue
        
        # 该区间总订单数
        zone_total_orders = order_agg[order_agg['客单价区间'] == zone]['订单ID'].nunique()
        
        # 按商品聚合
        zone_products = zone_df.groupby('商品名称').agg({
            '商品实售价': 'sum',
            '销量': 'sum',
            '利润额': 'sum',
            '订单ID': 'nunique'  # 该商品出现在多少个订单中
        }).reset_index()
        
        zone_products.columns = ['商品名称', '商品实售价', '销量', '利润额', '出现订单数']
        
        # 添加店内码和分类信息
        if '店内码' in zone_df.columns:
            product_code = zone_df.groupby('商品名称')['店内码'].first().to_dict()
            zone_products['店内码'] = zone_products['商品名称'].map(product_code)
        
        if '分类' in zone_df.columns:
            product_category = zone_df.groupby('商品名称')['分类'].first().to_dict()
            zone_products['分类'] = zone_products['商品名称'].map(product_category)
        
        # 添加渠道维度分析
        if '渠道' in zone_df.columns:
            # 统计该商品在各渠道的出现情况
            product_channels = zone_df.groupby('商品名称')['渠道'].apply(
                lambda x: ','.join(x.value_counts().head(2).index.tolist())
            ).to_dict()
            zone_products['主要渠道'] = zone_products['商品名称'].map(product_channels)
        
        # 计算关键指标
        zone_products['订单覆盖率(%)'] = (zone_products['出现订单数'] / zone_total_orders * 100).round(1)
        zone_products['平均每单贡献(元)'] = (zone_products['实收价格'] / zone_products['出现订单数']).round(2)
        zone_products['单品利润率(%)'] = ((zone_products['利润额'] / zone_products['实收价格']) * 100).round(1) if '利润额' in zone_products.columns else 0
        
        # 增强版经营建议
        def get_zone_suggestion_enhanced(row):
            zone_group = get_price_group(zone)
            coverage = row['订单覆盖率(%)']
            order_count = row['出现订单数']
            contribution = row['平均每单贡献(元)']
            profit_rate = row.get('单品利润率(%)', 0)
            
            suggestions = []
            
            if zone_group == '低价区':
                if coverage > 50:
                    suggestions.append("高频商品")
                    if contribution < 5:
                        suggestions.append("可作为引流品")
                    suggestions.append("建议：设计组合套餐提升客单价")
                elif coverage > 20:
                    suggestions.append("中频商品，建议：关联推荐高价值商品")
                else:
                    suggestions.append("低频商品，建议：搭配销售或清库存")
                    
            elif zone_group == '主流区':
                if coverage > 30:
                    suggestions.append("主流畅销品，建议：保证库存稳定供应")
                    if profit_rate > 20:
                        suggestions.append("高利润商品，可加大推广")
                else:
                    suggestions.append("普通商品，建议：优化定价或促销")
                    
            else:  # 高价区
                if order_count > 10:
                    if profit_rate > 25:
                        suggestions.append("高价值高利润，建议：重点推广")
                    else:
                        suggestions.append("高价值商品，建议：评估降价空间")
                else:
                    suggestions.append("低频高价，建议：分析用户需求或调整定位")
            
            return " | ".join(suggestions) if suggestions else "持续观察"
        
        zone_products['智能建议'] = zone_products.apply(get_zone_suggestion_enhanced, axis=1)
        
        # 按销售额降序
        zone_products = zone_products.sort_values('商品实售价', ascending=False)
        
        # 选择导出列
        export_cols = ['商品名称']
        if '店内码' in zone_products.columns:
            export_cols.append('店内码')
        if '分类' in zone_products.columns:
            export_cols.append('分类')
        if '主要渠道' in zone_products.columns:
            export_cols.append('主要渠道')
        export_cols.extend([
            '商品实售价', '销量', '利润额', 
            '出现订单数', '订单覆盖率(%)', '平均每单贡献(元)'
        ])
        if '单品利润率(%)' in zone_products.columns:
            export_cols.append('单品利润率(%)')
        export_cols.append('智能建议')
        
        zone_products_export = zone_products[export_cols].copy()
        aov_detail_sheets[zone] = zone_products_export
    
    # ========== 导出Excel ==========
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet1: 汇总
        aov_export.to_excel(writer, sheet_name='1_客单价分析_汇总', index=False)
        
        # 新增Sheet2: 渠道×客单价交叉分析
        if len(channel_aov_export) > 0:
            channel_aov_export.to_excel(writer, sheet_name='2_渠道客单价对比', index=False)
        
        # 新增Sheet3: 购物篮深度分析
        if len(basket_export) > 0:
            basket_export.to_excel(writer, sheet_name='3_购物篮深度分析', index=False)
        
        # Sheet4.X: 各价格区间明细（原Sheet2.X）
        zone_order = ['0-10元', '10-20元', '20-30元', '30-40元', '40-50元', '50-100元', '100-200元', '200元以上']
        for idx, zone in enumerate(zone_order):
            if zone in aov_detail_sheets:
                zone_group = get_price_group(zone)
                sheet_name = f"4.{idx+1}_{zone_group}_{zone}"
                
                # Excel sheet名称长度限制为31字符
                if len(sheet_name) > 31:
                    sheet_name = sheet_name[:31]
                
                aov_detail_sheets[zone].to_excel(writer, sheet_name=sheet_name, index=False)
        
        # 自动调整列宽
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{store_name}_客单价深度分析_{date_range_str}_{timestamp}.xlsx"
    
    return dcc.send_bytes(output.getvalue(), filename)


@app.callback(
    Output('download-aov-trend', 'data'),
    Input('export-aov-trend-btn', 'n_clicks'),
    State('store-data', 'data'),
    State('cached-order-agg', 'data'),
    State('current-store-id', 'data'),
    prevent_initial_call=True
)
def export_aov_trend(n_clicks, store_data, cached_agg, store_id):
    """导出客单价趋势分析报告（Phase 2）
    
    业务逻辑：
    - Sheet1: 本周vs上周客单价对比（4周数据，滚动对比）
    - Sheet2: 近7天价格区间趋势（每日各价格区间订单数）
    - Sheet3: 商品动销变化TOP20（销量增长/下降商品）
    - Sheet4: 渠道客单价趋势（各渠道每日客单价）
    - Sheet5: 价格区间订单数趋势（8个价格区间每日订单数）
    - Sheet6: 异常预警清单（客单价突降、订单数骤减等）
    """
    if not store_data:
        return None
    
    import io
    from datetime import datetime, timedelta
    import pandas as pd
    import numpy as np
    
    df = pd.DataFrame(store_data)
    
    if len(df) == 0:
        return None
    
    # 获取门店名称
    store_name = df['门店名称'].iloc[0] if '门店名称' in df.columns else "未知门店"
    
    # 确保日期字段
    date_col = '日期' if '日期' in df.columns else '下单时间'
    if date_col not in df.columns:
        return None
    
    df[date_col] = pd.to_datetime(df[date_col])
    
    # 从缓存读取order_agg
    if cached_agg:
        order_agg = pd.DataFrame(cached_agg)
        # 确保有客单价字段（可能是预计订单收入）
        if '客单价' not in order_agg.columns:
            if '预计订单收入' in order_agg.columns:
                order_agg['客单价'] = order_agg['预计订单收入']
            elif '实收价格' in order_agg.columns:
                order_agg['客单价'] = order_agg['实收价格']
            else:
                # 从原始数据重新聚合
                order_agg = df.groupby('订单ID').agg({
                    '实收价格': 'sum'
                }).reset_index()
                order_agg.rename(columns={'实收价格': '客单价'}, inplace=True)
    else:
        order_agg = df.groupby('订单ID').agg({
            '实收价格': 'sum'
        }).reset_index()
        order_agg.rename(columns={'实收价格': '客单价'}, inplace=True)
    
    # 合并日期信息
    order_date_map = df.groupby('订单ID')[date_col].first().reset_index()
    order_agg = order_agg.merge(order_date_map, on='订单ID', how='left')
    
    # 定义价格分组函数
    def categorize_aov(price):
        if price < 10: return '¥0-10'
        elif price < 20: return '¥10-20'
        elif price < 30: return '¥20-30'
        elif price < 40: return '¥30-40'
        elif price < 50: return '¥40-50'
        elif price < 100: return '¥50-100'
        elif price < 200: return '¥100-200'
        else: return '¥200以上'
    
    order_agg['价格区间'] = order_agg['客单价'].apply(categorize_aov)
    
    # ========== Sheet1: 本周vs上周对比 ==========
    # 按周分组（最近4周）
    order_agg['周'] = order_agg[date_col].dt.to_period('W')
    weekly_stats = order_agg.groupby('周').agg({
        '订单ID': 'count',
        '客单价': 'mean'
    }).reset_index()
    weekly_stats.columns = ['周', '订单数', '平均客单价']
    weekly_stats['周'] = weekly_stats['周'].astype(str)
    
    # 计算环比
    weekly_stats['订单数环比(%)'] = weekly_stats['订单数'].pct_change() * 100
    weekly_stats['客单价环比(%)'] = weekly_stats['平均客单价'].pct_change() * 100
    
    # ========== Sheet2: 近7天价格区间趋势 ==========
    max_date = order_agg[date_col].max()
    min_date = max_date - timedelta(days=6)
    recent_7d = order_agg[order_agg[date_col] >= min_date].copy()
    
    daily_zone_dist = recent_7d.groupby([recent_7d[date_col].dt.date, '价格区间']).size().unstack(fill_value=0)
    daily_zone_dist.index = pd.to_datetime(daily_zone_dist.index)
    daily_zone_dist = daily_zone_dist.reset_index()
    daily_zone_dist.rename(columns={date_col: '日期'}, inplace=True)
    
    # ========== Sheet3: 商品动销变化TOP20 ==========
    # 对比最近7天vs之前7天
    mid_date = max_date - timedelta(days=6)
    previous_7d_start = mid_date - timedelta(days=7)
    
    # 检查销量字段（可能是'销量'或'月售'）
    sales_field = None
    for field in ['销量', '月售', '数量']:
        if field in df.columns:
            sales_field = field
            break
    
    if sales_field:
        recent_sales = df[df[date_col] >= mid_date].groupby('商品名称').agg({
            sales_field: 'sum'
        }).reset_index()
        recent_sales.columns = ['商品名称', '最近7天销量']
        
        previous_sales = df[(df[date_col] >= previous_7d_start) & (df[date_col] < mid_date)].groupby('商品名称').agg({
            sales_field: 'sum'
        }).reset_index()
        previous_sales.columns = ['商品名称', '之前7天销量']
        
        sales_comparison = recent_sales.merge(previous_sales, on='商品名称', how='outer').fillna(0)
        sales_comparison['销量变化'] = sales_comparison['最近7天销量'] - sales_comparison['之前7天销量']
        sales_comparison['变化率(%)'] = ((sales_comparison['最近7天销量'] - sales_comparison['之前7天销量']) / 
                                         (sales_comparison['之前7天销量'].replace(0, 1))) * 100
        
        # TOP20（按绝对变化量）
        sales_top20 = sales_comparison.nlargest(20, '销量变化')
    else:
        # 无销量字段，使用订单数作为替代
        recent_sales = df[df[date_col] >= mid_date].groupby('商品名称').size().reset_index(name='最近7天订单数')
        previous_sales = df[(df[date_col] >= previous_7d_start) & (df[date_col] < mid_date)].groupby('商品名称').size().reset_index(name='之前7天订单数')
        
        sales_comparison = recent_sales.merge(previous_sales, on='商品名称', how='outer').fillna(0)
        sales_comparison.columns = ['商品名称', '最近7天销量', '之前7天销量']
        sales_comparison['销量变化'] = sales_comparison['最近7天销量'] - sales_comparison['之前7天销量']
        sales_comparison['变化率(%)'] = ((sales_comparison['最近7天销量'] - sales_comparison['之前7天销量']) / 
                                         (sales_comparison['之前7天销量'].replace(0, 1))) * 100
        
        sales_top20 = sales_comparison.nlargest(20, '销量变化')
    
    # ========== Sheet4: 渠道客单价趋势 ==========
    if '渠道' in df.columns:
        # 合并渠道信息到order_agg
        order_channel_map = df.groupby('订单ID')['渠道'].first().reset_index()
        order_with_channel = order_agg.merge(order_channel_map, on='订单ID', how='left')
        
        channel_daily_aov = order_with_channel.groupby([order_with_channel[date_col].dt.date, '渠道'])['客单价'].mean().unstack(fill_value=0)
        channel_daily_aov.index = pd.to_datetime(channel_daily_aov.index)
        channel_daily_aov = channel_daily_aov.reset_index()
        channel_daily_aov.rename(columns={date_col: '日期'}, inplace=True)
    else:
        channel_daily_aov = pd.DataFrame({'说明': ['渠道字段不存在']})
    
    # ========== Sheet5: 价格区间订单数趋势 ==========
    zone_order_trend = order_agg.groupby([order_agg[date_col].dt.date, '价格区间']).size().unstack(fill_value=0)
    zone_order_trend.index = pd.to_datetime(zone_order_trend.index)
    zone_order_trend = zone_order_trend.reset_index()
    zone_order_trend.rename(columns={date_col: '日期'}, inplace=True)
    
    # ========== Sheet6: 异常预警清单 ==========
    alerts = []
    
    # 每日客单价计算
    daily_aov = order_agg.groupby(order_agg[date_col].dt.date)['客单价'].mean()
    daily_aov_std = daily_aov.std()
    daily_aov_mean = daily_aov.mean()
    
    # 检测异常低客单价日期
    for date, aov in daily_aov.items():
        if aov < daily_aov_mean - 1.5 * daily_aov_std:
            alerts.append({
                '日期': date,
                '异常类型': '客单价异常低',
                '数值': f'¥{aov:.2f}',
                '正常范围': f'¥{daily_aov_mean:.2f}±{1.5*daily_aov_std:.2f}',
                '建议': '检查是否有大量低价商品促销，或高价商品缺货'
            })
    
    # 检测订单数骤减
    daily_orders = order_agg.groupby(order_agg[date_col].dt.date).size()
    for i in range(1, len(daily_orders)):
        if daily_orders.iloc[i] < daily_orders.iloc[i-1] * 0.5:
            alerts.append({
                '日期': daily_orders.index[i],
                '异常类型': '订单数骤减',
                '数值': f'{daily_orders.iloc[i]}单',
                '前一日': f'{daily_orders.iloc[i-1]}单',
                '建议': '检查系统是否正常，或是否有突发事件影响'
            })
    
    alerts_df = pd.DataFrame(alerts) if alerts else pd.DataFrame({'说明': ['未发现异常']})
    
    # ========== 导出Excel ==========
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        weekly_stats.to_excel(writer, sheet_name='1_本周vs上周对比', index=False)
        daily_zone_dist.to_excel(writer, sheet_name='2_近7天价格区间趋势', index=False)
        sales_top20.to_excel(writer, sheet_name='3_商品动销变化TOP20', index=False)
        channel_daily_aov.to_excel(writer, sheet_name='4_渠道客单价趋势', index=False)
        zone_order_trend.to_excel(writer, sheet_name='5_价格区间订单数趋势', index=False)
        alerts_df.to_excel(writer, sheet_name='6_异常预警清单', index=False)
        
        # 自动调整列宽
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{store_name}_客单价趋势分析_{timestamp}.xlsx"
    return dcc.send_bytes(output.getvalue(), filename)


@app.callback(
    Output('download-aov-association', 'data'),
    Input('export-aov-association-btn', 'n_clicks'),
    State('store-data', 'data'),
    State('cached-order-agg', 'data'),
    State('current-store-id', 'data'),
    prevent_initial_call=True
)
def export_aov_association(n_clicks, store_data, cached_agg, store_id):
    """导出商品关联分析报告（Phase 3）
    
    业务逻辑：
    - Sheet1: 商品关联矩阵（哪些商品经常一起购买）
    - Sheet2: 凑单推荐方案（基于关联规则，置信度>0.6）
    - Sheet3: 套餐组合建议（利润最大化组合，2-3个商品）
    - Sheet4: 交叉销售机会（商品A的买家还买了什么，TOP10）
    - Sheet5: 关联分析预测收益（基于推荐的预期增收）
    """
    if not store_data:
        return None
    
    import io
    from datetime import datetime
    import pandas as pd
    import numpy as np
    from itertools import combinations
    from collections import Counter, defaultdict
    
    df = pd.DataFrame(store_data)
    
    if len(df) == 0:
        return None
    
    # 获取门店名称
    store_name = df['门店名称'].iloc[0] if '门店名称' in df.columns else "未知门店"
    
    # ========== 数据准备 ==========
    # 构建订单-商品矩阵（每个订单包含哪些商品）
    order_products = df.groupby('订单ID')['商品名称'].apply(list).reset_index()
    
    # 过滤只有1个商品的订单（无关联可挖）
    order_products = order_products[order_products['商品名称'].apply(len) > 1]
    
    if len(order_products) == 0:
        # 没有多商品订单，返回提示
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame({'说明': ['数据中没有包含多个商品的订单，无法进行关联分析']}).to_excel(writer, sheet_name='说明', index=False)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"商品关联分析_无数据_{timestamp}.xlsx"
        return dcc.send_bytes(output.getvalue(), filename)
    
    # ========== Sheet1: 商品关联矩阵 ==========
    # 计算商品对的共现次数
    product_pairs = []
    for products in order_products['商品名称']:
        # 生成所有2商品组合
        for pair in combinations(sorted(set(products)), 2):
            product_pairs.append(pair)
    
    pair_counts = Counter(product_pairs)
    
    # 计算每个商品的出现次数
    all_products = []
    for products in order_products['商品名称']:
        all_products.extend(products)
    product_counts = Counter(all_products)
    
    # 构建关联矩阵
    association_data = []
    for (prod_a, prod_b), count in pair_counts.most_common(100):  # TOP100商品对
        support_a = product_counts[prod_a]
        support_b = product_counts[prod_b]
        
        # 置信度: P(B|A) = count(A,B) / count(A)
        confidence_a_b = count / support_a if support_a > 0 else 0
        confidence_b_a = count / support_b if support_b > 0 else 0
        
        # 提升度: lift = P(A,B) / (P(A) * P(B))
        total_orders = len(order_products)
        lift = (count / total_orders) / ((support_a / total_orders) * (support_b / total_orders)) if support_a > 0 and support_b > 0 else 0
        
        association_data.append({
            '商品A': prod_a,
            '商品B': prod_b,
            '共现次数': count,
            'A出现次数': support_a,
            'B出现次数': support_b,
            '置信度A→B(%)': round(confidence_a_b * 100, 2),
            '置信度B→A(%)': round(confidence_b_a * 100, 2),
            '提升度': round(lift, 2),
            '关联强度': '强' if lift > 1.5 and confidence_a_b > 0.3 else ('中' if lift > 1.2 else '弱')
        })
    
    association_matrix = pd.DataFrame(association_data)
    
    # ========== Sheet2: 凑单推荐方案 ==========
    # 筛选高置信度关联规则（置信度>0.4, 提升度>1.2）
    bundle_recommendations = association_matrix[
        (association_matrix['置信度A→B(%)'] > 40) & 
        (association_matrix['提升度'] > 1.2)
    ].copy()
    
    # 添加推荐场景
    bundle_recommendations['推荐场景'] = bundle_recommendations.apply(
        lambda x: f"购买'{x['商品A']}'的用户，有{x['置信度A→B(%)']}%的概率也会买'{x['商品B']}'",
        axis=1
    )
    
    # 预估增收（假设推荐成功率30%）
    if '商品实售价' in df.columns:
        product_avg_price = df.groupby('商品名称')['实收价格'].mean().to_dict()
        bundle_recommendations['商品B平均价格'] = bundle_recommendations['商品B'].map(product_avg_price)
        bundle_recommendations['预期增收(元)'] = (
            bundle_recommendations['A出现次数'] * 
            (bundle_recommendations['置信度A→B(%)'] / 100) * 
            0.3 *  # 推荐成功率
            bundle_recommendations['商品B平均价格']
        ).round(2)
    else:
        bundle_recommendations['预期增收(元)'] = 0
    
    bundle_recommendations = bundle_recommendations.sort_values('预期增收(元)', ascending=False).head(30)
    
    # ========== Sheet3: 套餐组合建议 ==========
    # 基于利润率挖掘最优组合
    combo_data = []
    
    if '实收价格' in df.columns and '商品采购成本' in df.columns:
        # 计算每个商品的平均利润率
        product_profit = df.groupby('商品名称').agg({
            '实收价格': 'mean',
            '商品采购成本': 'mean'
        }).reset_index()
        product_profit['利润率(%)'] = ((product_profit['实收价格'] - product_profit['商品采购成本']) / 
                                       product_profit['实收价格'] * 100).round(2)
        product_profit['单品利润'] = (product_profit['实收价格'] - product_profit['商品采购成本']).round(2)
        
        # 从高置信度关联中选择利润率高的组合
        for idx, row in association_matrix.head(50).iterrows():
            prod_a_info = product_profit[product_profit['商品名称'] == row['商品A']]
            prod_b_info = product_profit[product_profit['商品名称'] == row['商品B']]
            
            if len(prod_a_info) > 0 and len(prod_b_info) > 0:
                combo_price = prod_a_info['实收价格'].values[0] + prod_b_info['实收价格'].values[0]
                combo_profit = prod_a_info['单品利润'].values[0] + prod_b_info['单品利润'].values[0]
                combo_profit_rate = (combo_profit / combo_price * 100) if combo_price > 0 else 0
                
                combo_data.append({
                    '套餐名称': f"{row['商品A']} + {row['商品B']}",
                    '商品1': row['商品A'],
                    '商品2': row['商品B'],
                    '套餐原价(元)': round(combo_price, 2),
                    '套餐利润(元)': round(combo_profit, 2),
                    '利润率(%)': round(combo_profit_rate, 2),
                    '历史共现次数': row['共现次数'],
                    '提升度': row['提升度'],
                    '建议定价(元)': round(combo_price * 0.95, 2),  # 95折
                    '折扣后利润(元)': round(combo_profit - combo_price * 0.05, 2)
                })
    
    combo_recommendations = pd.DataFrame(combo_data).sort_values('折扣后利润(元)', ascending=False).head(20) if combo_data else pd.DataFrame({'说明': ['需要价格和成本数据']})
    
    # ========== Sheet4: 交叉销售机会 ==========
    # 找出每个热销商品的TOP10关联商品
    cross_sell_data = []
    
    top_products = product_counts.most_common(20)  # 前20个热销商品
    
    for prod, count in top_products:
        # 找出与该商品关联的其他商品
        related = []
        for (prod_a, prod_b), pair_count in pair_counts.items():
            if prod_a == prod:
                related.append((prod_b, pair_count))
            elif prod_b == prod:
                related.append((prod_a, pair_count))
        
        # 按共现次数排序
        related.sort(key=lambda x: x[1], reverse=True)
        
        for rank, (related_prod, co_count) in enumerate(related[:10], 1):
            cross_sell_data.append({
                '主商品': prod,
                '主商品销量': count,
                '关联商品': related_prod,
                '关联排名': rank,
                '共同购买次数': co_count,
                '关联率(%)': round(co_count / count * 100, 2) if count > 0 else 0
            })
    
    cross_sell_opportunities = pd.DataFrame(cross_sell_data)
    
    # ========== Sheet5: 预测收益 ==========
    # 汇总各类推荐的预期收益
    revenue_summary = pd.DataFrame({
        '推荐类型': ['凑单推荐', '套餐组合', '交叉销售'],
        '推荐数量': [
            len(bundle_recommendations),
            len(combo_recommendations) if isinstance(combo_recommendations, pd.DataFrame) and '套餐名称' in combo_recommendations.columns else 0,
            len(cross_sell_opportunities)
        ],
        '预期总增收(元)': [
            bundle_recommendations['预期增收(元)'].sum() if '预期增收(元)' in bundle_recommendations.columns else 0,
            combo_recommendations['折扣后利润(元)'].sum() if isinstance(combo_recommendations, pd.DataFrame) and '折扣后利润(元)' in combo_recommendations.columns else 0,
            0  # 交叉销售收益需要更复杂的计算
        ]
    })
    
    revenue_summary['实施优先级'] = revenue_summary['预期总增收(元)'].rank(ascending=False).astype(int)
    
    # ========== 导出Excel ==========
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        association_matrix.to_excel(writer, sheet_name='1_商品关联矩阵', index=False)
        bundle_recommendations.to_excel(writer, sheet_name='2_凑单推荐方案', index=False)
        combo_recommendations.to_excel(writer, sheet_name='3_套餐组合建议', index=False)
        cross_sell_opportunities.to_excel(writer, sheet_name='4_交叉销售机会', index=False)
        revenue_summary.to_excel(writer, sheet_name='5_预测收益汇总', index=False)
        
        # 自动调整列宽
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 60)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{store_name}_商品关联分析_{timestamp}.xlsx"
    return dcc.send_bytes(output.getvalue(), filename)


@app.callback(
    Output('download-aov-segment', 'data'),
    Input('export-aov-segment-btn', 'n_clicks'),
    State('store-data', 'data'),
    State('cached-order-agg', 'data'),
    State('current-store-id', 'data'),
    prevent_initial_call=True
)
def export_aov_segment(n_clicks, store_data, cached_agg, store_id):
    """导出用户分层分析报告（Phase 4）
    
    业务逻辑：
    - Sheet1: 新客vs老客分析（首购vs复购用户行为对比）
    - Sheet2: 用户成长路径（客单价区间迁移分析）
    - Sheet3: 复购分析（不同客单价区间用户的复购行为）
    - Sheet4: 高价值用户画像（TOP100用户识别与特征）
    - Sheet5: 流失预警（近期客单价下降或订单减少的用户）
    
    用户识别策略：优先使用用户ID，其次使用收货地址
    """
    if not store_data:
        return None
    
    import io
    from datetime import datetime, timedelta
    import pandas as pd
    import numpy as np
    
    df = pd.DataFrame(store_data)
    
    if len(df) == 0:
        return None
    
    # 获取门店名称
    store_name = df['门店名称'].iloc[0] if '门店名称' in df.columns else "未知门店"
    
    # ========== 用户识别 ==========
    # 优先级：用户ID > 收货地址
    user_id_field = None
    for field in ['用户ID', '会员ID', '用户手机', '手机号']:
        if field in df.columns and df[field].notna().sum() > len(df) * 0.3:  # 至少30%有值
            user_id_field = field
            break
    
    if user_id_field:
        # 使用用户ID
        df['用户标识'] = df[user_id_field].fillna('未知')
        identification_method = f"使用{user_id_field}字段"
    elif '收货地址' in df.columns:
        # 使用收货地址作为fallback
        df['用户标识'] = 'A_' + df['收货地址'].astype(str)
        identification_method = "使用收货地址"
    else:
        # 无法识别用户
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame({'说明': ['数据中没有用户ID或收货地址字段，无法进行用户分层分析']}).to_excel(writer, sheet_name='说明', index=False)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"用户分层分析_无数据_{timestamp}.xlsx"
        return dcc.send_bytes(output.getvalue(), filename)
    
    # 准备日期字段
    date_col = '日期' if '日期' in df.columns else '下单时间'
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
    else:
        # 无日期字段
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame({'说明': ['数据中没有日期字段，无法进行时间序列分析']}).to_excel(writer, sheet_name='说明', index=False)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"用户分层分析_无日期_{timestamp}.xlsx"
        return dcc.send_bytes(output.getvalue(), filename)
    
    # ========== 用户订单聚合 ==========
    user_orders = df.groupby(['用户标识', '订单ID']).agg({
        '商品实售价': 'sum',
        date_col: 'first'
    }).reset_index()
    user_orders.rename(columns={'商品实售价': '订单金额'}, inplace=True)
    
    # ========== Sheet1: 新客vs老客分析 ==========
    user_stats = user_orders.groupby('用户标识').agg({
        '订单ID': 'count',
        '订单金额': ['sum', 'mean'],
        date_col: ['min', 'max']
    }).reset_index()
    
    user_stats.columns = ['用户标识', '订单数', '总消费金额', '平均客单价', '首次购买日期', '最后购买日期']
    
    # 区分新老客（订单数=1为新客）
    user_stats['用户类型'] = user_stats['订单数'].apply(lambda x: '新客' if x == 1 else '老客')
    
    new_vs_old = user_stats.groupby('用户类型').agg({
        '用户标识': 'count',
        '订单数': 'sum',
        '总消费金额': 'sum',
        '平均客单价': 'mean'
    }).reset_index()
    new_vs_old.columns = ['用户类型', '用户数', '总订单数', '总消费金额(元)', '平均客单价(元)']
    new_vs_old['人均订单数'] = (new_vs_old['总订单数'] / new_vs_old['用户数']).round(2)
    new_vs_old['人均消费(元)'] = (new_vs_old['总消费金额(元)'] / new_vs_old['用户数']).round(2)
    
    # ========== Sheet2: 用户成长路径 ==========
    # 定义客单价区间
    def categorize_aov(price):
        if price < 20: return '低价区(<20)'
        elif price < 50: return '主流区(20-50)'
        else: return '高价区(50+)'
    
    user_orders['价格区间'] = user_orders['订单金额'].apply(categorize_aov)
    
    # 分析用户的首单和末单价格区间
    user_first_last = user_orders.sort_values(date_col).groupby('用户标识').agg({
        '价格区间': ['first', 'last'],
        '订单金额': ['first', 'last']
    }).reset_index()
    user_first_last.columns = ['用户标识', '首单价格区间', '末单价格区间', '首单金额', '末单金额']
    
    # 成长路径分析
    growth_path = user_first_last.groupby(['首单价格区间', '末单价格区间']).size().reset_index(name='用户数')
    growth_path['成长类型'] = growth_path.apply(
        lambda x: '保持' if x['首单价格区间'] == x['末单价格区间']
        else ('升级' if (x['首单价格区间'] == '低价区(<20)' and x['末单价格区间'] != '低价区(<20)') or 
                      (x['首单价格区间'] == '主流区(20-50)' and x['末单价格区间'] == '高价区(50+)')
              else '降级'),
        axis=1
    )
    
    # ========== Sheet3: 复购分析 ==========
    repurchase_analysis = user_stats[user_stats['订单数'] > 1].copy()  # 仅分析复购用户
    repurchase_analysis['平均复购间隔(天)'] = (
        (repurchase_analysis['最后购买日期'] - repurchase_analysis['首次购买日期']).dt.days / 
        (repurchase_analysis['订单数'] - 1)
    ).round(1)
    
    # 按客单价分段分析复购率
    repurchase_analysis['客单价区间'] = repurchase_analysis['平均客单价'].apply(categorize_aov)
    
    repurchase_by_aov = repurchase_analysis.groupby('客单价区间').agg({
        '用户标识': 'count',
        '订单数': 'mean',
        '平均复购间隔(天)': 'mean',
        '总消费金额': 'mean'
    }).reset_index()
    repurchase_by_aov.columns = ['客单价区间', '复购用户数', '平均订单数', '平均复购间隔(天)', '人均消费(元)']
    
    # 计算复购率（复购用户数 / 总用户数）
    total_users_by_aov = user_stats.groupby(
        user_stats['平均客单价'].apply(categorize_aov)
    ).size().reset_index(name='总用户数')
    total_users_by_aov.columns = ['客单价区间', '总用户数']
    
    repurchase_by_aov = repurchase_by_aov.merge(total_users_by_aov, on='客单价区间', how='left')
    repurchase_by_aov['复购率(%)'] = (repurchase_by_aov['复购用户数'] / repurchase_by_aov['总用户数'] * 100).round(2)
    
    # ========== Sheet4: 高价值用户画像 ==========
    high_value_users = user_stats.nlargest(100, '总消费金额').copy()
    
    # 添加更多用户特征
    for idx, user in high_value_users.iterrows():
        user_id = user['用户标识']
        user_detail_orders = user_orders[user_orders['用户标识'] == user_id]
        
        # 计算价格区间分布
        zone_dist = user_detail_orders['价格区间'].value_counts().to_dict()
        high_value_users.at[idx, '低价区订单数'] = zone_dist.get('低价区(<20)', 0)
        high_value_users.at[idx, '主流区订单数'] = zone_dist.get('主流区(20-50)', 0)
        high_value_users.at[idx, '高价区订单数'] = zone_dist.get('高价区(50+)', 0)
    
    high_value_users['价值等级'] = pd.cut(
        high_value_users['总消费金额'],
        bins=3,
        labels=['银牌', '金牌', '钻石']
    )
    
    # ========== Sheet5: 流失预警 ==========
    max_date = df[date_col].max()
    churn_threshold = max_date - timedelta(days=14)  # 14天未下单视为可能流失
    
    churn_risk_users = user_stats[user_stats['最后购买日期'] < churn_threshold].copy()
    churn_risk_users['距离最后购买(天)'] = (max_date - churn_risk_users['最后购买日期']).dt.days
    
    # 计算客单价趋势（最后3单vs前面订单）
    churn_details = []
    for idx, user in churn_risk_users.head(100).iterrows():  # TOP100流失风险用户
        user_id = user['用户标识']
        user_detail_orders = user_orders[user_orders['用户标识'] == user_id].sort_values(date_col)
        
        if len(user_detail_orders) >= 3:
            last_3_avg = user_detail_orders.tail(3)['订单金额'].mean()
            previous_avg = user_detail_orders.head(-3)['订单金额'].mean() if len(user_detail_orders) > 3 else last_3_avg
            
            aov_change = ((last_3_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
            
            churn_details.append({
                '用户标识': user_id,
                '历史订单数': user['订单数'],
                '历史总消费(元)': user['总消费金额'],
                '平均客单价(元)': user['平均客单价'],
                '最后购买日期': user['最后购买日期'],
                '距今天数': user['距离最后购买(天)'],
                '近期客单价变化(%)': round(aov_change, 2),
                '流失风险': '高' if user['距离最后购买(天)'] > 21 else '中',
                '召回建议': '发送优惠券' if aov_change < -10 else '推送新品信息'
            })
    
    churn_warning = pd.DataFrame(churn_details)
    
    # ========== 导出Excel ==========
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 添加说明Sheet
        info_df = pd.DataFrame({
            '说明': [f'用户识别方法: {identification_method}', 
                    f'分析期间: {df[date_col].min()} ~ {df[date_col].max()}',
                    f'总用户数: {len(user_stats)}',
                    f'新客数: {len(user_stats[user_stats["用户类型"]=="新客"])}',
                    f'老客数: {len(user_stats[user_stats["用户类型"]=="老客"])}']
        })
        info_df.to_excel(writer, sheet_name='0_分析说明', index=False)
        
        new_vs_old.to_excel(writer, sheet_name='1_新客vs老客分析', index=False)
        growth_path.to_excel(writer, sheet_name='2_用户成长路径', index=False)
        repurchase_by_aov.to_excel(writer, sheet_name='3_复购分析', index=False)
        high_value_users.to_excel(writer, sheet_name='4_高价值用户画像', index=False)
        if len(churn_warning) > 0:
            churn_warning.to_excel(writer, sheet_name='5_流失预警', index=False)
        else:
            pd.DataFrame({'说明': ['暂无流失风险用户']}).to_excel(writer, sheet_name='5_流失预警', index=False)
        
        # 自动调整列宽
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 60)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{store_name}_用户分层分析_{timestamp}.xlsx"
    return dcc.send_bytes(output.getvalue(), filename)


@app.callback(
    Output('download-tab1-order-report', 'data'),
    Input('export-tab1-order-report-btn', 'n_clicks'),
    State('store-data', 'data'),
    State('cached-order-agg', 'data'),
    State('cached-comparison-data', 'data'),
    State('current-store-id', 'data'),
    prevent_initial_call=True
)
def export_tab1_order_report(n_clicks, store_data, cached_agg, cached_comparison, store_id):
    """导出Tab1订单层面经营分析报告
    
    业务逻辑:
    - Sheet1: 关键指标汇总（订单总数、销售额、利润等核心指标）
    - Sheet2: 渠道表现对比（各渠道订单表现和环比）
    - Sheet3: 利润表现分析（每日订单利润趋势和异常识别）
    - Sheet4: 时段分析（不同时段订单分布）
    - Sheet5: 经营优化建议（智能生成的优化建议）
    
    注意：客单价深度分析已移至单独的导出按钮
    """
    if not store_data:
        return None
    
    import io
    from datetime import datetime, timedelta
    
    df = pd.DataFrame(store_data)
    
    if len(df) == 0:
        return None
    
    # 获取门店名称和日期范围
    store_name = df['门店名称'].iloc[0] if '门店名称' in df.columns else "未知门店"
    
    date_col = '日期' if '日期' in df.columns else '下单时间'
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col])
        date_start = df[date_col].min().strftime('%Y%m%d')
        date_end = df[date_col].max().strftime('%Y%m%d')
        date_range_str = f"{date_start}-{date_end}"
    else:
        date_range_str = "未知日期"
    
    # 获取订单聚合数据
    if cached_agg:
        order_agg = pd.DataFrame(cached_agg)
    else:
        order_agg = calculate_order_metrics(df)
    
    # 获取环比数据
    comparison_metrics = {}
    channel_comparison = {}
    if cached_comparison:
        comparison_metrics = cached_comparison.get('comparison_metrics', {})
        channel_comparison = cached_comparison.get('channel_comparison', {})
    
    # ==================== Sheet1: 关键指标汇总 ====================
    
    total_orders = len(order_agg)
    # 使用正确的字段名：预计订单收入（而非预计零售额）
    total_expected_revenue = order_agg['预计订单收入'].sum() if '预计订单收入' in order_agg.columns else 0
    total_profit = order_agg['利润额'].sum() if '利润额' in order_agg.columns else 0
    total_sales = order_agg['实收价格'].sum() if '实收价格' in order_agg.columns else 0
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0
    profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
    total_products = df['商品名称'].nunique() if '商品名称' in df.columns else 0
    
    indicators = []
    for key, label in [
        ('订单数', '订单总数'),
        ('预计零售额', '预计零售额'),
        ('总利润', '总利润'),
        ('客单价', '平均客单价'),
        ('总利润率', '总利润率'),
        ('动销商品数', '动销商品数')
    ]:
        comp = comparison_metrics.get(key, {})
        indicators.append({
            '指标名称': label,
            '当期值': {
                '订单数': total_orders,
                '预计零售额': total_expected_revenue,
                '总利润': total_profit,
                '客单价': avg_order_value,
                '总利润率': profit_rate,
                '动销商品数': total_products
            }.get(key, 0),
            '上期值': comp.get('previous', ''),
            '变化率': f"{comp.get('change_rate', 0):.1f}%" if comp.get('change_rate') else '',
            '变化方向': comp.get('direction', '')
        })
    
    indicators_export = pd.DataFrame(indicators)
    
    # ==================== Sheet2: 渠道表现对比 ====================
    
    channel_stats_list = []
    
    if '渠道' in order_agg.columns:
        # 构建聚合字典，只包含存在的字段
        agg_dict = {}
        if '预计订单收入' in order_agg.columns:
            agg_dict['预计订单收入'] = 'sum'
        if '利润额' in order_agg.columns:
            agg_dict['利润额'] = 'sum'
        if '商品实售价' in order_agg.columns:
            agg_dict['实收价格'] = 'sum'
        if '配送净成本' in order_agg.columns:
            agg_dict['配送净成本'] = 'sum'
        if '营销成本' in order_agg.columns:
            agg_dict['营销成本'] = 'sum'
        
        if not agg_dict:
            channel_export = pd.DataFrame()
        else:
            channel_stats = order_agg.groupby('渠道').agg(agg_dict).reset_index()
            
            # 计算订单数
            channel_orders = order_agg.groupby('渠道').size().reset_index(name='订单数')
            channel_stats = channel_stats.merge(channel_orders, on='渠道')
            
            # 计算衍生指标
            sales_col = '实收价格'
            channel_stats['利润率'] = (channel_stats['利润额'] / channel_stats[sales_col] * 100).fillna(0) if '利润额' in channel_stats.columns else 0
            channel_stats['平均客单价'] = (channel_stats[sales_col] / channel_stats['订单数']).fillna(0)
            if '配送净成本' in channel_stats.columns:
                channel_stats['配送成本率'] = (channel_stats['配送净成本'] / channel_stats[sales_col] * 100).fillna(0)
            else:
                channel_stats['配送成本率'] = 0
            if '营销成本' in channel_stats.columns:
                channel_stats['营销成本率'] = (channel_stats['营销成本'] / channel_stats[sales_col] * 100).fillna(0)
            else:
                channel_stats['营销成本率'] = 0
            
            # 添加环比数据
            for idx, row in channel_stats.iterrows():
                channel = row['渠道']
                comp = channel_comparison.get(channel, {})
                
                channel_stats_list.append({
                    '渠道名称': channel,
                    '订单数': row['订单数'],
                    '销售额': row.get('商品实售价', 0),
                    '利润额': row.get('利润额', 0),
                    '利润率': f"{row['利润率']:.2f}%",
                    '平均客单价': row['平均客单价'],
                    '配送成本': row.get('配送净成本', 0),
                    '配送成本率': f"{row['配送成本率']:.2f}%",
                    '营销成本': row.get('营销成本', 0),
                    '营销成本率': f"{row['营销成本率']:.2f}%",
                    '销售额环比': f"{comp.get('销售额_变化率', 0):.1f}%" if comp.get('销售额_变化率') else '',
                    '利润率环比': f"{comp.get('利润率_变化率', 0):.1f}%" if comp.get('利润率_变化率') else '',
                    '订单数环比': f"{comp.get('订单数_变化率', 0):.1f}%" if comp.get('订单数_变化率') else ''
                })
    
            channel_export = pd.DataFrame(channel_stats_list) if channel_stats_list else pd.DataFrame()
    else:
        channel_export = pd.DataFrame()
    
    # ==================== 客单价深度分析已移除 ====================
    # 客单价分析已移至单独的导出按钮，此处不再包含
    
    # aov_analysis_list = []
    
    # 客单价分析代码已移除，请使用客单价看板的单独导出功能
    # bins = [0, 10, 20, 30, 40, 50, 100, 200, float('inf')]
    # labels = ['0-10元', '10-20元', '20-30元', '30-40元', '40-50元', '50-100元', '100-200元', '200元以上']
    
    # ==================== Sheet3: 利润表现分析 ====================
    # 注意：原Sheet4调整为Sheet3，因客单价分析已移除
    
    # 从原始df获取订单ID和日期的映射关系
    if date_col in df.columns and '订单ID' in df.columns:
        # 获取每个订单的日期（去重，每个订单只保留一个日期）
        order_dates = df.groupby('订单ID')[date_col].first().reset_index()
        order_dates.columns = ['订单ID', '日期']
        
        # 将日期合并到order_agg
        order_agg_with_date = order_agg.merge(order_dates, on='订单ID', how='left')
        
        # 使用正确的销售额字段
        sales_col_daily = '实收价格' if '实收价格' in order_agg_with_date.columns else '商品销售额'
        
        # 按日期聚合
        agg_dict_daily = {}
        if sales_col_daily in order_agg_with_date.columns:
            agg_dict_daily[sales_col_daily] = 'sum'
        if '利润额' in order_agg_with_date.columns:
            agg_dict_daily['利润额'] = 'sum'
        agg_dict_daily['订单ID'] = 'count'
        
        daily_sales = order_agg_with_date.groupby('日期').agg(agg_dict_daily).reset_index()
        
        # 重命名列
        col_mapping = {'订单ID': '订单数'}
        if sales_col_daily in daily_sales.columns:
            col_mapping[sales_col_daily] = '销售额'
        if '利润额' in daily_sales.columns:
            col_mapping['利润额'] = '总利润'
        daily_sales = daily_sales.rename(columns=col_mapping)
        
        # 计算利润率
        if '总利润' in daily_sales.columns and '销售额' in daily_sales.columns:
            daily_sales['利润率'] = (daily_sales['总利润'] / daily_sales['销售额'] * 100).fillna(0)
        else:
            daily_sales['利润率'] = 0
    else:
        daily_sales = pd.DataFrame()
    
    # 异常检测（仅在有数据时执行）
    if len(daily_sales) > 0 and '利润率' in daily_sales.columns:
        avg_profit_rate = daily_sales['利润率'].mean()
        std_profit_rate = daily_sales['利润率'].std()
        
        daily_sales['异常标识'] = daily_sales['利润率'].apply(
            lambda x: '异常' if abs(x - avg_profit_rate) > std_profit_rate else '正常'
        )
        daily_sales['偏离度'] = ((daily_sales['利润率'] - avg_profit_rate) / std_profit_rate).round(2)
        
        # 异常原因分析
        daily_sales['异常原因'] = daily_sales.apply(
            lambda row: f"利润率{'过低' if row['利润率'] < avg_profit_rate else '过高'}，偏离{abs(row['偏离度']):.1f}个标准差" 
            if row['异常标识'] == '异常' else '',
            axis=1
        )
        
        profit_export = daily_sales.copy()
        profit_export['日期'] = profit_export['日期'].dt.strftime('%Y-%m-%d')
    else:
        profit_export = pd.DataFrame()
        avg_profit_rate = 0
        std_profit_rate = 0
    
    # ==================== Sheet5: 时段分析 ====================
    
    time_analysis_list = []
    
    if '下单时间' in df.columns:
        df['下单时间_dt'] = pd.to_datetime(df['下单时间'], errors='coerce')
        df['时段'] = df['下单时间_dt'].dt.hour.apply(
            lambda x: f"{x:02d}:00-{x+1:02d}:00" if pd.notna(x) else '未知'
        )
        
        # 构建聚合字典
        time_agg_dict = {'订单ID': 'nunique'}
        
        # 使用实际存在的字段
        if '实收价格' in df.columns:
            time_agg_dict['实收价格'] = 'sum'
            sales_field = '实收价格'
        elif '实收价格' in df.columns:
            time_agg_dict['实收价格'] = 'sum'
            sales_field = '实收价格'
        else:
            sales_field = None
            
        if '利润额' in df.columns:
            time_agg_dict['利润额'] = 'sum'
        
        if sales_field:
            time_stats = df.groupby('时段').agg(time_agg_dict).reset_index()
            
            # 重命名列
            col_rename = {'订单ID': '订单数'}
            if sales_field in time_stats.columns:
                col_rename[sales_field] = '销售额'
            time_stats = time_stats.rename(columns=col_rename)
            
            total_time_orders = time_stats['订单数'].sum()
            
            if '销售额' in time_stats.columns:
                total_time_sales = time_stats['销售额'].sum()
                time_stats['平均客单价'] = (time_stats['销售额'] / time_stats['订单数']).round(2)
                time_stats['销售占比'] = (time_stats['销售额'] / total_time_sales * 100).round(2) if total_time_sales > 0 else 0
            
            if '利润额' in time_stats.columns and '销售额' in time_stats.columns:
                time_stats['利润率'] = (time_stats['利润额'] / time_stats['销售额'] * 100).fillna(0).round(2)
            
            time_stats['订单占比'] = (time_stats['订单数'] / total_time_orders * 100).round(2) if total_time_orders > 0 else 0
            
            time_export = time_stats.sort_values('时段')
        else:
            time_export = pd.DataFrame()
    else:
        time_export = pd.DataFrame()
    
    # ==================== Sheet6: 经营优化建议 ====================
    
    suggestions = []
    
    # 1. 渠道优化建议
    if len(channel_export) > 0:
        # 按利润率排序（需要去除%符号后排序）
        if '利润率' in channel_export.columns:
            try:
                # 尝试提取数值
                channel_export_sorted = channel_export.copy()
                if channel_export_sorted['利润率'].dtype == 'object':
                    channel_export_sorted['利润率_num'] = channel_export_sorted['利润率'].str.replace('%', '').astype(float)
                    best_channel = channel_export_sorted.nlargest(1, '利润率_num').iloc[0]
                else:
                    best_channel = channel_export_sorted.nlargest(1, '利润率').iloc[0]
            except:
                best_channel = channel_export.iloc[0]
        else:
            best_channel = channel_export.iloc[0]
        
        suggestions.append({
            '类别': '渠道优化',
            '发现': f"最优渠道：{best_channel['渠道名称']}",
            '数据': f"利润率{best_channel['利润率']}，销售额¥{best_channel['销售额']:,.0f}",
            '建议': f"建议加大{best_channel['渠道名称']}资源投入，优化其他渠道配送和营销成本"
        })
    
    # 2. 客单价优化建议（基于订单数据的简单分析）
    if avg_order_value > 0:
        suggestions.append({
            '类别': '客单价优化',
            '发现': f"当前平均客单价为¥{avg_order_value:.2f}",
            '数据': f"总订单数{total_orders}笔，总销售额¥{total_sales:,.2f}",
            '建议': "建议：1)设计满减活动提升客单价 2)推荐凑单商品增加购物篮 3)使用【客单价深度分析】按钮查看详细报告"
        })
    
    # 3. 利润优化建议
    if len(profit_export) > 0:
        anomaly_days = profit_export[profit_export['异常标识'] == '异常']
        if len(anomaly_days) > 0:
            suggestions.append({
                '类别': '利润优化',
                '发现': f"发现{len(anomaly_days)}个异常利润日",
                '数据': f"平均利润率{avg_profit_rate:.2f}%，波动±{std_profit_rate:.2f}%",
                '建议': "建议分析异常日期的营销活动和配送成本，优化成本控制"
            })
    
    # 4. 时段优化建议
    if len(time_export) > 0:
        peak_time = time_export.nlargest(1, '订单数').iloc[0]
        suggestions.append({
            '类别': '时段优化',
            '发现': f"订单高峰时段：{peak_time['时段']}",
            '数据': f"订单数{peak_time['订单数']:.0f}，占比{peak_time['订单占比']:.1f}%",
            '建议': "建议在高峰时段加强人员配备，确保配送时效和服务质量"
        })
    
    suggestions_export = pd.DataFrame(suggestions)
    
    # ==================== 创建Excel文件 ====================
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet1: 关键指标
        if len(indicators_export) > 0:
            indicators_export.to_excel(writer, sheet_name='1_关键指标汇总', index=False)
        
        # Sheet2: 渠道对比
        if len(channel_export) > 0:
            channel_export.to_excel(writer, sheet_name='2_渠道表现对比', index=False)
        
        # 客单价分析已移除，请使用客单价看板的单独导出功能
        
        # Sheet3: 利润表现（原Sheet4）
        if len(profit_export) > 0:
            profit_export.to_excel(writer, sheet_name='3_利润表现分析', index=False)
        
        # Sheet4: 时段分析（原Sheet5）
        if len(time_export) > 0:
            time_export.to_excel(writer, sheet_name='4_时段分析', index=False)
        
        # Sheet5: 优化建议（原Sheet6）
        if len(suggestions_export) > 0:
            suggestions_export.to_excel(writer, sheet_name='5_经营优化建议', index=False)
    
    output.seek(0)
    
    # 生成文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{store_name}_经营分析报告_订单维度_{date_range_str}_{timestamp}.xlsx"
    
    return dcc.send_bytes(output.getvalue(), filename)


# ==================== 主程序入口 ====================

# ==================== Clientside Callback: 场景化组合切换 ====================
app.clientside_callback(
    """
    function(selected_scene) {
        // 控制5个场景的显示/隐藏
        const scenes = ['早餐', '午餐', '晚餐', '夜宵', '下午茶'];
        const styles = scenes.map(scene => 
            scene === selected_scene ? {} : {display: 'none'}
        );
        
        return styles;
    }
    """,
    [
        Output({'type': 'scene-combo-早餐', 'index': MATCH}, 'style'),
        Output({'type': 'scene-combo-午餐', 'index': MATCH}, 'style'),
        Output({'type': 'scene-combo-晚餐', 'index': MATCH}, 'style'),
        Output({'type': 'scene-combo-夜宵', 'index': MATCH}, 'style'),
        Output({'type': 'scene-combo-下午茶', 'index': MATCH}, 'style')
    ],
    [Input({'type': 'scene-selector', 'index': MATCH}, 'value')]
)

# ==================== 导入并注册Tab7回调 ====================
# 注释：Tab7所有回调已在主文件中直接定义，无需单独导入
# try:
#     from tab7_callbacks import register_tab7_callbacks
#     register_tab7_callbacks(app)
#     print("✅ Tab7双维度分析回调已注册")
# except Exception as e:
#     print(f"⚠️ Tab7回调注册失败: {e}")
print("✅ Tab7营销分析回调已加载（主文件内置）")

# ==================== 主程序入口 ====================
if __name__ == '__main__':
    import sys
    
    # 强制刷新输出，确保日志实时显示
    sys.stdout.flush()
    sys.stderr.flush()
    
    # 获取本机局域网IP
    import socket
    try:
        # 获取本机IP地址
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        # 如果是127.0.0.1，尝试另一种方法
        if local_ip.startswith('127.'):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
    except:
        local_ip = "本机IP"
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                 🏪 门店诊断看板(订单数据)                     ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  ✅ 流畅的交互体验                                            ║
    ║  ✅ 支持局域网多人同时访问                                     ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  📍 本机访问: http://localhost:8050                          ║
    ║  🌐 局域网访问: http://{local_ip}:8050                   ║
    ║  👥 其他设备通过局域网IP访问即可共享看板                       ║
    ╚══════════════════════════════════════════════════════════════╝
    """, flush=True)
    
    # 🆕 测试AI功能
    print("🤖 检查AI分析功能...", flush=True)
    try:
        from ai_analyzer import get_ai_analyzer
        test_analyzer = get_ai_analyzer(model_type='glm')
        if test_analyzer and test_analyzer.is_ready():
            print(f"   ✅ AI分析器就绪 (智谱GLM-4.6)", flush=True)
        else:
            print(f"   ⚠️ AI分析器未就绪,AI功能将不可用", flush=True)
    except Exception as e:
        print(f"   ⚠️ AI初始化异常: {e}", flush=True)
    
    print("🚀 准备启动应用服务器...", flush=True)
    print(f"📊 数据状态: {len(GLOBAL_DATA) if GLOBAL_DATA is not None else 0} 行数据已加载", flush=True)
    print(f"⚙️ 配置: host=0.0.0.0, port=8050, debug=False", flush=True)
    print("", flush=True)
    
    try:
        # 使用debug=True临时查看详细错误
        app.run(
            debug=True,  # 暂时启用Debug查看错误
            host='0.0.0.0',
            port=8050,
            use_reloader=False  # 禁用自动重载
        )
        print("⚠️ 应用服务器已停止", flush=True)
    except KeyboardInterrupt:
        print("\n✋ 用户中断 (Ctrl+C)", flush=True)
    except Exception as e:
        print(f"\n❌ 应用启动失败: {e}", flush=True)
        import traceback
        traceback.print_exc()
        input("按回车键退出...")

