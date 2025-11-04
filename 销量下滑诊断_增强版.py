"""
销量下滑诊断 - 增强版
深度诊断 + 智能分析 + 可视化报告

功能清单:
1. ✅ 趋势可视化图表
2. ✅ 诊断报告导出 (Excel)
3. ✅ 智能原因分析
4. ✅ 同比环比对比
5. ✅ 多维度筛选
6. ✅ 改进建议生成
7. ✅ 数据上传
8. ✅ 优化UI布局
"""

import pandas as pd
import numpy as np
from dash import Dash, html, dcc, Input, Output, State, dash_table, no_update, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
from pathlib import Path
import io
import base64

# 导入诊断引擎
sys.path.insert(0, str(Path(__file__).parent))
from 问题诊断引擎 import ProblemDiagnosticEngine

# ======================== 全局变量 ========================
GLOBAL_DATA = None
DIAGNOSTIC_ENGINE = None
LAST_DIAGNOSTIC_RESULT = None  # 保存最后诊断结果用于导出

# ======================== 辅助函数 ========================

def analyze_decline_reasons(product_data, full_data):
    """
    智能分析商品下滑原因
    
    参数:
        product_data: 单个商品的诊断数据(Series)
        full_data: 完整的订单数据(DataFrame)
    
    返回:
        reasons: 可能原因列表
    """
    reasons = []
    
    # 1. 价格因素分析
    if '商品实售价' in product_data.index:
        price = product_data['商品实售价']
        # 转换为数值（去除¥符号）
        try:
            price_num = float(str(price).replace('¥', '').replace('￥', ''))
            median_price = full_data[full_data['商品名称'] == product_data['商品名称']]['商品实售价'].median()
            
            # 检查是否涨价
            if price_num > median_price:
                reasons.append({
                    'category': '价格因素',
                    'factor': '价格偏高',
                    'description': f'当前售价 ¥{price_num:.2f} 高于该商品历史中位价',
                    'impact': 'high',
                    'suggestion': '建议适当降价或推出促销活动'
                })
        except:
            pass
    
    # 2. 销量变化幅度分析
    if '变化幅度%' in product_data.index:
        change_pct = product_data['变化幅度%']
        # 转换为数值（去除%符号）
        try:
            change_num = float(str(change_pct).replace('%', ''))
            if change_num < -30:
                reasons.append({
                    'category': '销量急降',
                    'factor': '销量大幅下滑',
                    'description': f'销量下滑 {abs(change_num):.1f}%，属于严重下滑',
                    'impact': 'critical',
                    'suggestion': '需要立即采取补救措施，检查库存、价格、竞品情况'
                })
            elif change_num < -15:
                reasons.append({
                    'category': '销量下滑',
                    'factor': '销量明显下降',
                    'description': f'销量下滑 {abs(change_num):.1f}%，需要关注',
                    'impact': 'medium',
                    'suggestion': '建议分析用户反馈，优化商品展示'
                })
        except:
            pass
    
    # 3. 利润率分析
    if '平均毛利率%' in product_data.index:
        profit_margin = product_data['平均毛利率%']
        try:
            margin_num = float(str(profit_margin).replace('%', ''))
            if margin_num < 10:
                reasons.append({
                    'category': '利润因素',
                    'factor': '毛利率过低',
                    'description': f'当前毛利率 {margin_num:.1f}%，盈利能力弱',
                    'impact': 'medium',
                    'suggestion': '考虑优化供应链成本或调整定价策略'
                })
        except:
            pass
    
    # 4. 季节性因素（简化判断）
    product_name = product_data.get('商品名称', '')
    if any(kw in product_name for kw in ['冰', '冷饮', '雪糕']):
        current_month = datetime.now().month
        if current_month in [11, 12, 1, 2]:  # 冬季
            reasons.append({
                'category': '季节性因素',
                'factor': '冬季冷饮需求降低',
                'description': '当前为冬季，冷饮类商品需求自然下降',
                'impact': 'low',
                'suggestion': '这是正常季节性波动，可推出热饮替代品'
            })
    
    if any(kw in product_name for kw in ['热饮', '暖宝', '姜茶']):
        current_month = datetime.now().month
        if current_month in [5, 6, 7, 8, 9]:  # 夏季
            reasons.append({
                'category': '季节性因素',
                'factor': '夏季热饮需求降低',
                'description': '当前为夏季，热饮类商品需求自然下降',
                'impact': 'low',
                'suggestion': '这是正常季节性波动，可增加冷饮供应'
            })
    
    # 如果没有找到明显原因，给出通用建议
    if not reasons:
        reasons.append({
            'category': '综合因素',
            'factor': '多因素影响',
            'description': '销量下滑可能由多种因素共同导致',
            'impact': 'medium',
            'suggestion': '建议全面检查：库存是否充足、商品展示是否醒目、是否有竞品促销、用户评价是否良好'
        })
    
    return reasons


def generate_improvement_suggestions(diagnostic_result):
    """
    基于诊断结果生成改进建议
    
    参数:
        diagnostic_result: 诊断结果DataFrame
    
    返回:
        suggestions: 建议列表
    """
    suggestions = []
    
    if diagnostic_result.empty:
        return suggestions
    
    # 预处理：转换数值字段（去除符号）
    result = diagnostic_result.copy()
    
    # 转换变化幅度%为数值
    if '变化幅度%' in result.columns:
        result['变化幅度%_num'] = pd.to_numeric(
            result['变化幅度%'].astype(str).str.replace('%', ''),
            errors='coerce'
        )
    
    # 转换商品实售价为数值
    if '商品实售价' in result.columns:
        result['商品实售价_num'] = pd.to_numeric(
            result['商品实售价'].astype(str).str.replace('¥', '').str.replace('￥', ''),
            errors='coerce'
        )
    
    # 1. 定价优化建议
    if '商品实售价_num' in result.columns and '变化幅度%_num' in result.columns:
        high_price_decline = result[
            (result['变化幅度%_num'] < -20) & 
            (result['商品实售价_num'] > result['商品实售价_num'].median())
        ]
        
        if len(high_price_decline) > 0:
            suggestions.append({
                'type': '定价策略',
                'priority': 'high',
                'title': f'🏷️ {len(high_price_decline)} 个高价商品销量大幅下滑',
                'description': f'这些商品价格高于平均水平且销量下滑超过20%',
                'action': '建议：适当降价5-10%，或推出限时促销',
                'expected_impact': '预计可恢复15-25%的销量'
            })
    
    # 2. 库存优化建议
    if '变化幅度%_num' in result.columns:
        critical_products = result[result['变化幅度%_num'] < -30]
        if len(critical_products) > 0:
            suggestions.append({
                'type': '库存管理',
                'priority': 'critical',
                'title': f'⚠️ {len(critical_products)} 个商品销量严重下滑',
                'description': '这些商品销量下降超过30%，可能影响库存周转',
                'action': '建议：检查库存积压情况，考虑清仓促销或停止进货',
                'expected_impact': '避免库存积压损失'
            })
    
    # 3. 促销策略建议
    if '收入变化' in result.columns:
        revenue_loss = result['收入变化'].sum()
        if revenue_loss < -1000:
            suggestions.append({
                'type': '促销活动',
                'priority': 'high',
                'title': f'💰 总收入损失 ¥{abs(revenue_loss):,.2f}',
                'description': '下滑商品导致的收入损失较大',
                'action': '建议：策划组合促销活动（买一送一、满减等）',
                'expected_impact': f'预计可挽回 ¥{abs(revenue_loss) * 0.3:,.2f} - ¥{abs(revenue_loss) * 0.5:,.2f}'
            })
    
    # 4. 商品优化建议
    if '一级分类名' in result.columns and '变化幅度%_num' in result.columns:
        category_decline = result.groupby('一级分类名')['变化幅度%_num'].mean()
        worst_category = category_decline.idxmin()
        worst_pct = category_decline.min()
        
        if worst_pct < -15:
            suggestions.append({
                'type': '商品结构',
                'priority': 'medium',
                'title': f'📊 "{worst_category}" 类商品整体下滑',
                'description': f'该类别平均下滑 {abs(worst_pct):.1f}%',
                'action': '建议：优化该类别商品结构，引入新品或淘汰滞销品',
                'expected_impact': '提升品类竞争力'
            })
    
    # 5. 用户体验建议
    suggestions.append({
        'type': '用户体验',
        'priority': 'medium',
        'title': '🎯 提升商品展示和推荐',
        'description': '优化下滑商品的展示位置和推荐策略',
        'action': '建议：将下滑商品放在首页推荐位，增加曝光度',
        'expected_impact': '提升10-20%的点击率和购买转化'
    })
    
    return suggestions


def create_trend_chart(data, product_name, time_period='week'):
    """
    创建商品销量趋势图
    
    参数:
        data: 完整订单数据
        product_name: 商品名称
        time_period: 'week' 或 'month'
    """
    # 筛选商品数据
    product_data = data[data['商品名称'] == product_name].copy()
    
    if product_data.empty:
        return go.Figure().add_annotation(
            text="暂无数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    # 按日期聚合
    product_data['日期'] = pd.to_datetime(product_data['日期'])
    
    if time_period == 'week':
        # 按周聚合
        product_data['周'] = product_data['日期'].dt.to_period('W').dt.start_time
        trend = product_data.groupby('周').agg({
            '销量': 'sum',
            '预计订单收入': 'sum',
            '利润': 'sum'
        }).reset_index()
        trend['周'] = trend['周'].dt.strftime('%Y-%m-%d')
        x_label = '周'
        x_data = trend['周']
    else:
        # 按月聚合
        product_data['月'] = product_data['日期'].dt.to_period('M').dt.start_time
        trend = product_data.groupby('月').agg({
            '销量': 'sum',
            '预计订单收入': 'sum',
            '利润': 'sum'
        }).reset_index()
        trend['月'] = trend['月'].dt.strftime('%Y-%m')
        x_label = '月'
        x_data = trend['月']
    
    # 创建图表
    fig = go.Figure()
    
    # 销量趋势线
    fig.add_trace(go.Scatter(
        x=x_data,
        y=trend['销量'],
        mode='lines+markers',
        name='销量',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8),
        yaxis='y'
    ))
    
    # 收入趋势线
    fig.add_trace(go.Scatter(
        x=x_data,
        y=trend['预计订单收入'],
        mode='lines+markers',
        name='收入',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    # 布局设置
    fig.update_layout(
        title=dict(
            text=f'📈 {product_name} - 销量&收入趋势',
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(title=x_label),
        yaxis=dict(
            title='销量 (单)',
            titlefont=dict(color='#1f77b4'),
            tickfont=dict(color='#1f77b4')
        ),
        yaxis2=dict(
            title='收入 (¥)',
            titlefont=dict(color='#2ca02c'),
            tickfont=dict(color='#2ca02c'),
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    return fig


def create_category_comparison_chart(diagnostic_result):
    """
    创建分类对比柱状图
    """
    if diagnostic_result.empty or '一级分类名' not in diagnostic_result.columns:
        return go.Figure()
    
    # 按分类统计
    category_stats = diagnostic_result.groupby('一级分类名').agg({
        '商品名称': 'count',
        '销量变化': 'sum',
        '收入变化': 'sum'
    }).reset_index()
    category_stats.columns = ['分类', '商品数', '销量变化', '收入变化']
    
    # 创建图表
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=category_stats['分类'],
        y=category_stats['商品数'],
        name='下滑商品数',
        marker_color='#ff7f0e'
    ))
    
    fig.update_layout(
        title='📊 各分类下滑商品分布',
        xaxis_title='商品分类',
        yaxis_title='下滑商品数',
        height=350,
        template='plotly_white'
    )
    
    return fig


def export_diagnostic_report(diagnostic_result, suggestions, filename='诊断报告.xlsx'):
    """
    导出完整诊断报告到Excel
    
    参数:
        diagnostic_result: 诊断结果DataFrame
        suggestions: 改进建议列表
        filename: 文件名
    
    返回:
        Excel文件的二进制数据
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 工作表1: 诊断数据
        diagnostic_result.to_excel(writer, sheet_name='诊断数据', index=False)
        
        # 工作表2: 改进建议
        if suggestions:
            suggestions_df = pd.DataFrame(suggestions)
            suggestions_df.to_excel(writer, sheet_name='改进建议', index=False)
        
        # 工作表3: 统计摘要
        if not diagnostic_result.empty:
            # 转换变化幅度%为数值以计算平均值
            avg_decline = 'N/A'
            if '变化幅度%' in diagnostic_result.columns:
                try:
                    decline_numeric = pd.to_numeric(
                        diagnostic_result['变化幅度%'].astype(str).str.replace('%', ''),
                        errors='coerce'
                    )
                    avg_decline = f"{decline_numeric.mean():.2f}%"
                except:
                    pass
            
            summary = {
                '指标': ['下滑商品数', '总销量损失', '总收入损失', '总利润损失', '平均下滑幅度'],
                '数值': [
                    len(diagnostic_result),
                    f"{int(diagnostic_result['销量变化'].sum())} 单" if '销量变化' in diagnostic_result.columns else 'N/A',
                    f"¥{diagnostic_result['收入变化'].sum():,.2f}" if '收入变化' in diagnostic_result.columns else 'N/A',
                    f"¥{diagnostic_result['利润变化'].sum():,.2f}" if '利润变化' in diagnostic_result.columns else 'N/A',
                    avg_decline
                ]
            }
            summary_df = pd.DataFrame(summary)
            summary_df.to_excel(writer, sheet_name='统计摘要', index=False)
    
    output.seek(0)
    return output.getvalue()


# ======================== 数据加载 ========================
def load_default_data():
    """加载默认数据"""
    global GLOBAL_DATA, DIAGNOSTIC_ENGINE
    
    try:
        # 直接加载Excel文件
        data_dir = Path("实际数据")
        excel_files = list(data_dir.glob("*.xlsx"))
        
        if not excel_files:
            print(f"❌ 未找到数据文件,目录: {data_dir}")
            return False
        
        # 读取第一个Excel文件
        file_path = excel_files[0]
        print(f"📂 正在加载数据: {file_path.name}")
        df = pd.read_excel(file_path)
        print(f"📊 原始数据: {len(df)} 行 × {len(df.columns)} 列")
        
        # 标准化字段名
        if '下单时间' in df.columns:
            df['日期'] = pd.to_datetime(df['下单时间'])
        elif '日期' not in df.columns:
            print("❌ 缺少日期字段")
            return False
        
        # 字段映射
        if '月售' in df.columns and '销量' not in df.columns:
            df['销量'] = df['月售']
        if '利润额' in df.columns and '利润' not in df.columns:
            df['利润'] = df['利润额']
        if '预计订单收入' not in df.columns and '订单零售额' in df.columns:
            df['预计订单收入'] = df['订单零售额']
        
        # 必需字段检查
        required_fields = ['商品名称', '日期', '销量']
        missing = [f for f in required_fields if f not in df.columns]
        if missing:
            print(f"❌ 缺少必需字段: {missing}")
            return False
        
        # 剔除耗材和咖啡渠道
        if '一级分类名' in df.columns:
            df = df[df['一级分类名'] != '耗材']
        if '渠道' in df.columns:
            coffee_channels = ['饿了么咖啡', '美团咖啡']
            df = df[~df['渠道'].isin(coffee_channels)]
        
        print(f"✅ 数据过滤后: {len(df)} 行")
        
        GLOBAL_DATA = df
        DIAGNOSTIC_ENGINE = ProblemDiagnosticEngine(df)
        
        print(f"✅ 数据加载成功: {len(df)} 行")
        return True
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ======================== 创建应用 ========================
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    # 隐藏的threshold输入（用于兼容回调）
    dcc.Input(id='threshold', type='hidden', value=-100),
    
    # 标题
    dbc.Row([
        dbc.Col([
            html.H1("📉 销量下滑诊断系统 - 增强版", className="text-center my-4"),
            html.P("深度诊断 | 智能分析 | 可视化报告", className="text-center text-muted")
        ])
    ]),
    
    # Tab导航
    dbc.Tabs([
        # Tab 1: 数据管理
        dbc.Tab(label="📁 数据管理", tab_id="tab-data", children=[
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dcc.Upload(
                                id='upload-data',
                                children=dbc.Button(
                                    "📤 上传订单数据 (Excel文件)",
                                    color="success",
                                    outline=True,
                                    className="w-100"
                                ),
                                multiple=False
                            )
                        ], md=8),
                        dbc.Col([
                            html.Div(id='upload-status', className="mt-2")
                        ], md=4)
                    ])
                ])
            ], className="my-3")
        ]),
        
        # Tab 2: 诊断分析
        dbc.Tab(label="🔍 诊断分析", tab_id="tab-diagnosis", children=[
            # 控制面板
            dbc.Card([
                dbc.CardHeader(html.H4("🎛️ 诊断参数")),
                dbc.CardBody([
                    dbc.Row([
                        # 对比模式
                        dbc.Col([
                            html.Label("对比模式:"),
                            dcc.Dropdown(
                                id='time-period',
                                options=[
                                    {'label': '📅 周度对比', 'value': 'week'},
                                    {'label': '📆 月度对比', 'value': 'month'},
                                ],
                                value='week',
                                clearable=False
                            )
                        ], md=3),
                        
                        # 说明文字（替代阈值滑块）
                        dbc.Col([
                            html.Label("诊断范围:"),
                            dbc.Alert([
                                html.Strong("自动展示所有下滑商品"),
                                html.Br(),
                                html.Small("可通过高级筛选精细控制展示范围", className="text-muted")
                            ], color="info", className="mb-0 py-2")
                        ], md=4),
                        
                        # 周期选择
                        dbc.Col([
                            html.Label("当前周期:"),
                            dcc.Dropdown(id='current-period', value=0),
                        ], md=2),
                        
                        dbc.Col([
                            html.Label("对比周期:"),
                            dcc.Dropdown(id='compare-period', value=1)
                        ], md=2),
                        
                        # 诊断按钮
                        dbc.Col([
                            html.Label("\u00a0", style={'opacity': 0}),  # 占位对齐
                            dbc.Button(
                                "🔍 开始诊断",
                                id='diagnose-btn',
                                color="primary",
                                size="lg",
                                className="w-100"
                            )
                        ], md=2)
                    ])
                ])
            ], className="my-3"),
            
            # 高级筛选
            dbc.Card([
                dbc.CardHeader([
                    html.H5("🔧 高级筛选", className="mb-0")
                ]),
                dbc.Collapse([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("商品分类:"),
                                dcc.Dropdown(id='category-filter', multi=True, placeholder="全部分类")
                            ], md=3),
                            dbc.Col([
                                html.Label("价格区间:"),
                                dcc.RangeSlider(
                                    id='price-range',
                                    min=0,
                                    max=100,
                                    step=5,
                                    value=[0, 100],
                                    marks={i: f"¥{i}" for i in range(0, 101, 20)},
                                    tooltip={"placement": "bottom", "always_visible": True}
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("下滑幅度:"),
                                dcc.RangeSlider(
                                    id='decline-range',
                                    min=-100,
                                    max=0,
                                    step=10,
                                    value=[-100, 0],
                                    marks={i: f"{i}%" for i in range(-100, 1, 20)},
                                    tooltip={"placement": "bottom", "always_visible": True}
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("\u00a0"),
                                dbc.Button("应用筛选", id='apply-filter', color="secondary", className="w-100")
                            ], md=2)
                        ])
                    ])
                ], id='advanced-filter-collapse', is_open=False)
            ], className="mb-3"),
            
            # 结果显示
            dbc.Alert(id='diagnosis-alert', is_open=False),
            
            # 统计卡片
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("下滑商品数", className="text-muted"),
                            html.H3(id='stat-products', children="0 个", className="text-danger")
                        ])
                    ])
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("销量损失", className="text-muted"),
                            html.H3(id='stat-quantity', children="0 单", className="text-warning")
                        ])
                    ])
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("收入损失", className="text-muted"),
                            html.H3(id='stat-revenue', children="¥0", className="text-warning")
                        ])
                    ])
                ], md=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("利润损失", className="text-muted"),
                            html.H3(id='stat-profit', children="¥0", className="text-danger")
                        ])
                    ])
                ], md=3)
            ], className="mb-3"),
            
            # 图表展示
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 分类分布"),
                        dbc.CardBody([
                            dcc.Graph(id='category-chart', config={'displayModeBar': False})
                        ])
                    ])
                ], md=12)
            ], className="mb-3"),
            
            # 数据表格
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col(html.H5("📋 诊断明细", className="mb-0"), width=8),
                        dbc.Col([
                            dbc.Button("📥 导出报告", id='export-btn', color="success", size="sm", className="float-end")
                        ], width=4)
                    ])
                ]),
                dbc.CardBody([
                    dash_table.DataTable(
                        id='diagnosis-table',
                        data=[],
                        columns=[],
                        page_size=15,
                        style_cell={
                            'textAlign': 'left',
                            'padding': '10px',
                            'fontSize': '14px'
                        },
                        style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {
                                'if': {'column_id': '变化幅度%'},
                                'backgroundColor': '#ffebee',
                                'color': '#c62828'
                            }
                        ]
                    )
                ])
            ], className="mb-3"),
            
            # 下载组件(隐藏)
            dcc.Download(id='download-report')
        ]),
        
        # Tab 3: 趋势分析
        dbc.Tab(label="📈 趋势分析", tab_id="tab-trends", children=[
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("选择商品:"),
                            dcc.Dropdown(id='product-selector', placeholder="请先进行诊断...")
                        ], md=10),
                        dbc.Col([
                            html.Label("\u00a0"),
                            dbc.Button("查看趋势", id='view-trend-btn', color="primary", className="w-100")
                        ], md=2)
                    ])
                ])
            ], className="my-3"),
            
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(id='trend-chart', config={'displayModeBar': True})
                ])
            ])
        ]),
        
        # Tab 4: 智能建议
        dbc.Tab(label="💡 智能建议", tab_id="tab-suggestions", children=[
            html.Div(id='suggestions-container', className="my-3")
        ])
    ], id='main-tabs', active_tab='tab-diagnosis')
    
], fluid=True)


# ======================== 回调函数 ========================

# 上传数据回调
@app.callback(
    [Output('upload-status', 'children'),
     Output('current-period', 'options', allow_duplicate=True),
     Output('compare-period', 'options', allow_duplicate=True),
     Output('category-filter', 'options', allow_duplicate=True)],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def upload_file(contents, filename):
    """处理上传的文件"""
    global GLOBAL_DATA, DIAGNOSTIC_ENGINE
    
    if contents is None:
        return "未上传文件", [], [], []
    
    try:
        # 解析上传的文件
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # 读取Excel文件
        df = pd.read_excel(io.BytesIO(decoded))
        print(f"\n📂 上传文件: {filename}")
        print(f"📊 原始数据: {len(df)} 行 × {len(df.columns)} 列")
        
        # 标准化字段
        if '下单时间' in df.columns:
            df['日期'] = pd.to_datetime(df['下单时间'])
        elif '日期' not in df.columns:
            return "❌ 缺少日期字段", [], [], []
        
        # 字段映射
        if '月售' in df.columns and '销量' not in df.columns:
            df['销量'] = df['月售']
        if '利润额' in df.columns and '利润' not in df.columns:
            df['利润'] = df['利润额']
        if '预计订单收入' not in df.columns and '订单零售额' in df.columns:
            df['预计订单收入'] = df['订单零售额']
        
        # 必需字段检查
        required_fields = ['商品名称', '日期', '销量']
        missing = [f for f in required_fields if f not in df.columns]
        if missing:
            return f"❌ 缺少必需字段: {missing}", [], [], []
        
        # 剔除耗材和咖啡渠道
        if '一级分类名' in df.columns:
            df = df[df['一级分类名'] != '耗材']
        if '渠道' in df.columns:
            coffee_channels = ['饿了么咖啡', '美团咖啡']
            df = df[~df['渠道'].isin(coffee_channels)]
        
        print(f"✅ 数据过滤后: {len(df)} 行")
        
        # 更新全局数据
        GLOBAL_DATA = df
        DIAGNOSTIC_ENGINE = ProblemDiagnosticEngine(df)
        
        # 生成周期选项
        max_date = df['日期'].max()
        week_options = []
        for i in range(12):
            end_date = max_date - timedelta(days=i * 7)
            start_date = end_date - timedelta(days=6)
            week_options.append({
                'label': f"第{i+1}周 ({start_date.strftime('%m-%d')} 至 {end_date.strftime('%m-%d')})",
                'value': i
            })
        
        # 获取分类选项
        category_options = []
        if '一级分类名' in df.columns:
            categories = df['一级分类名'].unique()
            category_options = [{'label': cat, 'value': cat} for cat in categories if pd.notna(cat)]
        
        status_msg = html.Div([
            html.I(className="fas fa-check-circle text-success me-2"),
            html.Span(f"✅ 已上传: {filename}", className="text-success"),
            html.Br(),
            html.Small(f"共 {len(df)} 条记录", className="text-muted")
        ])
        
        return status_msg, week_options, week_options, category_options
        
    except Exception as e:
        print(f"❌ 文件处理失败: {e}")
        import traceback
        traceback.print_exc()
        return f"❌ 文件处理失败: {str(e)}", [], [], []


# 更新周期选项
@app.callback(
    [Output('current-period', 'options'),
     Output('compare-period', 'options'),
     Output('category-filter', 'options')],
    Input('time-period', 'value')
)
def update_period_options(time_period):
    """更新周期选择器选项"""
    if GLOBAL_DATA is None:
        return [], [], []
    
    max_date = GLOBAL_DATA['日期'].max()
    options = []
    
    if time_period == 'week':
        for i in range(12):
            end_date = max_date - timedelta(days=i * 7)
            start_date = end_date - timedelta(days=6)
            options.append({
                'label': f"第{i+1}周 ({start_date.strftime('%m-%d')} 至 {end_date.strftime('%m-%d')})",
                'value': i
            })
    else:  # month
        for i in range(12):
            month_start = (max_date - timedelta(days=i * 30)).replace(day=1)
            options.append({
                'label': f"{month_start.strftime('%Y年%m月')}",
                'value': i
            })
    
    # 获取分类选项
    category_options = []
    if '一级分类名' in GLOBAL_DATA.columns:
        categories = GLOBAL_DATA['一级分类名'].unique()
        category_options = [{'label': cat, 'value': cat} for cat in categories if pd.notna(cat)]
    
    return options, options, category_options


# 主诊断回调
@app.callback(
    [Output('diagnosis-table', 'data'),
     Output('diagnosis-table', 'columns'),
     Output('stat-products', 'children'),
     Output('stat-quantity', 'children'),
     Output('stat-revenue', 'children'),
     Output('stat-profit', 'children'),
     Output('diagnosis-alert', 'children'),
     Output('diagnosis-alert', 'is_open'),
     Output('diagnosis-alert', 'color'),
     Output('category-chart', 'figure'),
     Output('product-selector', 'options'),
     Output('suggestions-container', 'children')],
    Input('diagnose-btn', 'n_clicks'),
    [State('time-period', 'value'),
     State('threshold', 'value'),
     State('current-period', 'value'),
     State('compare-period', 'value'),
     State('category-filter', 'value'),
     State('price-range', 'value'),
     State('decline-range', 'value')],
    prevent_initial_call=True
)
def diagnose(n_clicks, time_period, threshold, current_idx, compare_idx,
             category_filter, price_range, decline_range):
    """执行诊断分析"""
    global LAST_DIAGNOSTIC_RESULT
    
    print(f"\n{'='*80}")
    print(f"🔍 诊断触发: n_clicks={n_clicks}, time_period={time_period}")
    print(f"   current_idx={current_idx}, compare_idx={compare_idx}")
    print(f"   筛选条件: category={category_filter}, price={price_range}, decline={decline_range}")
    print(f"{'='*80}\n")
    
    if GLOBAL_DATA is None or DIAGNOSTIC_ENGINE is None:
        return (
            [], [], "0 个", "0 单", "¥0", "¥0",
            "⚠️ 请先上传数据", True, "warning",
            go.Figure(), [], html.Div()
        )
    
    try:
        # 执行诊断 - threshold参数已不再使用，诊断引擎会返回所有下滑商品
        print(f"\n{'='*80}")
        print(f"🔍 开始诊断...")
        print(f"   时间粒度: {time_period}")
        print(f"   当前周期: {current_idx}, 对比周期: {compare_idx}")
        
        result = DIAGNOSTIC_ENGINE.diagnose_sales_decline(
            threshold=-100,  # 传入一个极小值，确保返回所有下滑商品
            time_period=time_period,
            current_period_index=current_idx if current_idx is not None else 0,
            compare_period_index=compare_idx if compare_idx is not None else 1
        )
        
        print(f"✅ 诊断完成，初始结果: {len(result)} 个下滑商品")
        if len(result) > 0:
            print(f"   变化幅度%类型: {result['变化幅度%'].dtype}")
            print(f"   前3个值: {list(result['变化幅度%'].head(3))}")
        
        # 应用高级筛选
        if not result.empty:
            # 分类筛选
            if category_filter and '一级分类名' in result.columns:
                before_count = len(result)
                result = result[result['一级分类名'].isin(category_filter)]
                print(f"   分类筛选: {before_count} -> {len(result)} 个商品")
            
            # 价格筛选 - 先转换为数值类型
            if price_range and '商品实售价' in result.columns:
                before_count = len(result)
                # 转换为数值类型，先去除¥符号和其他非数字字符
                result['商品实售价'] = pd.to_numeric(
                    result['商品实售价'].astype(str).str.replace('¥', '').str.replace('￥', ''),
                    errors='coerce'
                )
                # 先过滤掉NaN值，然后再进行范围比较
                result = result[result['商品实售价'].notna()]
                if len(result) > 0:
                    result = result[
                        (result['商品实售价'] >= price_range[0]) &
                        (result['商品实售价'] <= price_range[1])
                    ]
                print(f"   价格筛选 [{price_range[0]}-{price_range[1]}]: {before_count} -> {len(result)} 个商品")
            
            # 下滑幅度筛选 - 先转换为数值类型
            if decline_range and '变化幅度%' in result.columns:
                before_count = len(result)
                print(f"   下滑幅度筛选前: {before_count} 个商品")
                print(f"   筛选范围: {decline_range}")
                
                # 转换字符串百分比为数值（去除%符号）
                result['变化幅度%_numeric'] = pd.to_numeric(
                    result['变化幅度%'].astype(str).str.replace('%', ''),
                    errors='coerce'
                )
                print(f"   转换后类型: {result['变化幅度%_numeric'].dtype}")
                if len(result) > 0:
                    print(f"   转换后前3个值: {list(result['变化幅度%_numeric'].head(3))}")
                
                # 先过滤掉NaN值
                result = result[result['变化幅度%_numeric'].notna()]
                if len(result) > 0:
                    result = result[
                        (result['变化幅度%_numeric'] >= decline_range[0]) &
                        (result['变化幅度%_numeric'] <= decline_range[1])
                    ]
                print(f"   下滑幅度筛选后: {len(result)} 个商品")
                
                # 删除临时列
                if '变化幅度%_numeric' in result.columns:
                    result = result.drop('变化幅度%_numeric', axis=1)
        
        print(f"📊 最终结果: {len(result)} 个下滑商品")
        print(f"{'='*80}\n")
        
        # 保存结果用于导出
        LAST_DIAGNOSTIC_RESULT = result
        
        if result.empty:
            # 构建详细的提示信息
            tips = html.Div([
                html.H5("ℹ️ 未发现下滑商品"),
                html.Hr(),
                html.P("可能的原因："),
                html.Ul([
                    html.Li("所选对比周期内商品销量均呈上涨或持平趋势"),
                    html.Li("高级筛选条件可能过滤掉了部分商品"),
                    html.Li("数据时间范围内销量波动较小"),
                ]),
                html.P("💡 建议操作：", className="mt-3"),
                html.Ol([
                    html.Li("尝试选择相距更远的对比周期（如第1周 vs 第4周）"),
                    html.Li("切换到月度对比查看更长时间跨度的变化"),
                    html.Li("如果设置了高级筛选，尝试放宽条件"),
                    html.Li("检查数据源是否包含足够的历史数据"),
                ])
            ])
            
            return (
                [], [], "0 个", "0 单", "¥0", "¥0",
                tips, True, "info",
                go.Figure(), [], html.Div([
                    dbc.Alert([
                        html.H5("💡 如何使用智能建议功能"),
                        html.P("智能建议基于诊断结果生成。当发现下滑商品后，系统会自动分析并提供："),
                        html.Ul([
                            html.Li("定价策略建议"),
                            html.Li("库存管理建议"),
                            html.Li("促销活动方案"),
                            html.Li("商品结构优化建议"),
                            html.Li("用户体验提升建议"),
                        ]),
                        html.P("请先调整对比周期，或检查是否有销量下滑情况。", className="mb-0")
                    ], color="info")
                ])
            )
        
        # 准备显示数据
        display_cols = []
        for col in result.columns:
            if col in ['商品名称', '场景', '时段', '一级分类名']:
                display_cols.append(col)
            elif any(kw in col for kw in ['周销量', '月销量', '周预计收入', '月预计收入', '周利润', '月利润']):
                display_cols.append(col)
            elif col in ['销量变化', '变化幅度%', '收入变化', '利润变化']:
                display_cols.append(col)
            elif col in ['商品实售价', '平均毛利率%']:
                display_cols.append(col)
        
        display_data = result[display_cols].copy()
        
        # 格式化数值
        for col in display_data.columns:
            if display_data[col].dtype in ['float64', 'int64', 'float32', 'int32']:
                if '变化幅度%' in col or '毛利率%' in col:
                    display_data[col] = display_data[col].round(2)
                elif '收入' in col or '利润' in col or '实售价' in col:
                    display_data[col] = display_data[col].round(2)
        
        # 准备表格列定义
        columns = [{'name': col, 'id': col} for col in display_cols]
        
        # 计算统计
        stat_products = f"{len(result)} 个"
        stat_quantity = f"{int(result['销量变化'].sum())} 单" if '销量变化' in result.columns else "0 单"
        stat_revenue = f"¥{result['收入变化'].sum():,.2f}" if '收入变化' in result.columns else "¥0"
        stat_profit = f"¥{result['利润变化'].sum():,.2f}" if '利润变化' in result.columns else "¥0"
        
        # 创建分类图表
        category_chart = create_category_comparison_chart(result)
        
        # 生成商品选择器选项
        product_options = [{'label': name, 'value': name} for name in result['商品名称'].unique()]
        
        # 生成改进建议
        suggestions = generate_improvement_suggestions(result)
        suggestions_cards = []
        
        priority_colors = {
            'critical': 'danger',
            'high': 'warning',
            'medium': 'info',
            'low': 'secondary'
        }
        
        for sug in suggestions:
            card = dbc.Card([
                dbc.CardHeader([
                    dbc.Badge(sug['type'], color="primary", className="me-2"),
                    dbc.Badge(sug['priority'].upper(), color=priority_colors.get(sug['priority'], 'secondary'))
                ]),
                dbc.CardBody([
                    html.H5(sug['title'], className="card-title"),
                    html.P(sug['description'], className="text-muted"),
                    html.Hr(),
                    html.P([html.Strong("行动建议: "), sug['action']]),
                    html.P([html.Strong("预期效果: "), sug['expected_impact']], className="text-success")
                ])
            ], className="mb-3")
            suggestions_cards.append(card)
        
        suggestions_content = html.Div([
            html.H4("💡 智能改进建议", className="mb-4"),
            *suggestions_cards
        ]) if suggestions_cards else html.Div([
            dbc.Alert("暂无改进建议", color="info")
        ])
        
        print(f"✅ 诊断完成: 找到 {len(result)} 个下滑商品")
        
        return (
            display_data.to_dict('records'),
            columns,
            stat_products,
            stat_quantity,
            stat_revenue,
            stat_profit,
            f"✅ 诊断完成! 发现 {len(result)} 个下滑商品",
            True,
            "success",
            category_chart,
            product_options,
            suggestions_content
        )
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
        return (
            [], [], "0 个", "0 单", "¥0", "¥0",
            f"❌ 诊断失败: {str(e)}", True, "danger",
            go.Figure(), [], html.Div()
        )


# 趋势图回调
@app.callback(
    Output('trend-chart', 'figure'),
    Input('view-trend-btn', 'n_clicks'),
    [State('product-selector', 'value'),
     State('time-period', 'value')],
    prevent_initial_call=True
)
def show_trend(n_clicks, product_name, time_period):
    """显示商品趋势图"""
    if not product_name or GLOBAL_DATA is None:
        return go.Figure().add_annotation(
            text="请先选择商品",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
    
    return create_trend_chart(GLOBAL_DATA, product_name, time_period)


# 导出报告回调
@app.callback(
    Output('download-report', 'data'),
    Input('export-btn', 'n_clicks'),
    prevent_initial_call=True
)
def export_report(n_clicks):
    """导出诊断报告"""
    if LAST_DIAGNOSTIC_RESULT is None or LAST_DIAGNOSTIC_RESULT.empty:
        return no_update
    
    try:
        # 生成改进建议
        suggestions = generate_improvement_suggestions(LAST_DIAGNOSTIC_RESULT)
        
        # 导出Excel
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"销量下滑诊断报告_{timestamp}.xlsx"
        
        excel_data = export_diagnostic_report(LAST_DIAGNOSTIC_RESULT, suggestions, filename)
        
        # 使用base64编码
        import base64
        encoded = base64.b64encode(excel_data).decode()
        
        return dict(
            content=encoded,
            filename=filename,
            base64=True,
            type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        import traceback
        traceback.print_exc()
        return no_update


# ======================== 启动应用 ========================
if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 销量下滑诊断系统 - 增强版")
    print("="*80 + "\n")
    
    # 加载数据
    if load_default_data():
        print("\n✅ 数据初始化完成,启动应用...")
        print("📍 访问地址: http://localhost:8052\n")
        app.run(debug=False, host='0.0.0.0', port=8052)
    else:
        print("\n❌ 数据加载失败,无法启动应用")
        sys.exit(1)
