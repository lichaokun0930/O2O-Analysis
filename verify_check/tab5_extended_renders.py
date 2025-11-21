#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tab 5扩展渲染函数 - ECharts可视化
包括: 热力图、利润矩阵、趋势图、关联网络、商品画像
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table

# ECharts可用性检查
try:
    from dash_echarts import DashECharts
    ECHARTS_AVAILABLE = True
    print("✅ Tab5扩展: ECharts 可用")
except ImportError:
    ECHARTS_AVAILABLE = False
    print("⚠️ Tab5扩展: ECharts 不可用,将使用 Plotly 后备方案")

try:
    from 商品场景智能打标引擎 import ProductSceneTagger
    SMART_TAGGING_AVAILABLE = True
except:
    SMART_TAGGING_AVAILABLE = False


# ==================== ECharts渲染辅助函数 ====================

def render_heatmap_echarts(cross_pivot):
    """热力图 - ECharts版本"""
    option = {
        'title': {'text': '时段×场景交易热力图', 'left': 'center'},
        'tooltip': {'position': 'top'},
        'grid': {'height': '70%', 'top': '10%'},
        'xAxis': {
            'type': 'category',
            'data': cross_pivot.columns.tolist(),
            'splitArea': {'show': True}
        },
        'yAxis': {
            'type': 'category',
            'data': cross_pivot.index.tolist(),
            'splitArea': {'show': True}
        },
        'visualMap': {
            'min': 0,
            'max': int(cross_pivot.values.max()),
            'calculable': True,
            'orient': 'horizontal',
            'left': 'center',
            'bottom': '5%',
            'inRange': {'color': ['#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c']}
        },
        'series': [{
            'name': '交易数',
            'type': 'heatmap',
            'data': [
                [j, i, int(cross_pivot.values[i][j])]
                for i in range(len(cross_pivot.index))
                for j in range(len(cross_pivot.columns))
            ],
            'label': {'show': True},
            'emphasis': {
                'itemStyle': {'shadowBlur': 10, 'shadowColor': 'rgba(0, 0, 0, 0.5)'}
            }
        }]
    }
    return DashECharts(option=option, id='heatmap-chart', style={'height': '500px'})


def render_heatmap_plotly(cross_pivot):
    """热力图 - Plotly版本(后备)"""
    fig = go.Figure(data=go.Heatmap(
        z=cross_pivot.values,
        x=cross_pivot.columns.tolist(),
        y=cross_pivot.index.tolist(),
        colorscale='YlOrRd',
        text=cross_pivot.values,
        texttemplate='%{z}',
        hovertemplate='<b>%{y} × %{x}</b><br>订单量: %{z}<extra></extra>'
    ))
    fig.update_layout(
        title='时段×场景交易热力图',
        xaxis_title='消费场景',
        yaxis_title='时段',
        height=500,
        font=dict(family="Microsoft YaHei", size=12)
    )
    return dcc.Graph(figure=fig)


def render_quadrant_echarts(scene_stats_df, median_orders, median_profit_rate):
    """场景利润贡献气泡图 - 更直观的ECharts版本"""
    # 按综合得分排序(订单量×利润率)
    scene_stats_df = scene_stats_df.copy()
    scene_stats_df['综合得分'] = scene_stats_df['订单量'] * scene_stats_df['利润率']
    scene_stats_df = scene_stats_df.sort_values('综合得分', ascending=True)
    
    color_map = {
        '明星场景 (高量高利)': '#28a745',
        '流量场景 (高量低利)': '#ffc107',
        '利润场景 (低量高利)': '#17a2b8',
        '问题场景 (低量低利)': '#dc3545'
    }
    
    # 准备数据
    data = []
    for _, row in scene_stats_df.iterrows():
        data.append({
            'name': row['场景'],
            'value': [row['订单量'], row['利润率'], row['销售额']],
            'itemStyle': {'color': color_map.get(row['象限'], '#666')},
            'label': {
                'show': True,
                'position': 'right',
                'formatter': '{b}',
                'fontSize': 12,
                'fontWeight': 'bold'
            }
        })
    
    option = {
        'title': {
            'text': '场景利润贡献气泡图 (订单量 × 利润率)',
            'left': 'center',
            'top': 10,
            'textStyle': {'fontSize': 16}
        },
        'tooltip': {
            'trigger': 'item',
            'formatter': '{b}<br/>订单量: {c[0]}<br/>利润率: {c[1]:.1f}%<br/>销售额: ¥{c[2]:.0f}'
        },
        'legend': {
            'data': list(color_map.keys()),
            'bottom': 10,
            'left': 'center'
        },
        'grid': {
            'left': '15%',
            'right': '15%',
            'bottom': '15%',
            'top': '15%',
            'containLabel': True
        },
        'xAxis': {
            'name': '订单量',
            'nameLocation': 'middle',
            'nameGap': 35,
            'nameTextStyle': {'fontSize': 14, 'fontWeight': 'bold'},
            'splitLine': {'show': True, 'lineStyle': {'type': 'dashed', 'color': '#e0e0e0'}}
        },
        'yAxis': {
            'name': '利润率 (%)',
            'nameLocation': 'middle',
            'nameGap': 50,
            'nameTextStyle': {'fontSize': 14, 'fontWeight': 'bold'},
            'splitLine': {'show': True, 'lineStyle': {'type': 'dashed', 'color': '#e0e0e0'}},
            'axisLabel': {'formatter': '{value}%'}
        },
        'series': [{
            'name': '场景',
            'type': 'scatter',
            'symbolSize': "function (params) { return Math.max(20, Math.sqrt(params.value[2]) / 8); }",
            'data': data,
            'markLine': {
                'silent': True,
                'lineStyle': {'color': '#999', 'type': 'dashed', 'width': 1},
                'label': {'position': 'end', 'formatter': '{b}'},
                'data': [
                    {'xAxis': float(median_orders), 'name': f'订单中位数:{int(median_orders)}'},
                    {'yAxis': float(median_profit_rate), 'name': f'利润率中位数:{median_profit_rate:.1f}%'}
                ]
            },
            'emphasis': {
                'focus': 'self',
                'itemStyle': {'shadowBlur': 10, 'shadowColor': 'rgba(0,0,0,0.5)'}
            }
        }]
    }
    return DashECharts(option=option, id='quadrant-chart', style={'height': '600px'})


def render_scene_radar_chart(scene_stats_df):
    """场景综合表现雷达图 - 显示TOP5场景"""
    # 选择TOP5场景(按综合得分)
    top5_scenes = scene_stats_df.nlargest(5, '综合得分')
    
    # 标准化数据到0-100
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0, 100))
    
    metrics = ['订单量', '销售额', '利润率', '商品数']
    normalized_data = scaler.fit_transform(top5_scenes[metrics])
    
    # 准备雷达图数据
    radar_data = []
    for i, (idx, row) in enumerate(top5_scenes.iterrows()):
        radar_data.append({
            'name': row['场景'],
            'value': normalized_data[i].tolist()
        })
    
    option = {
        'title': {
            'text': 'TOP5场景综合表现',
            'left': 'center',
            'top': 10
        },
        'tooltip': {
            'trigger': 'item'
        },
        'legend': {
            'bottom': 10,
            'left': 'center',
            'data': top5_scenes['场景'].tolist()
        },
        'radar': {
            'indicator': [
                {'name': '订单量', 'max': 100},
                {'name': '销售额', 'max': 100},
                {'name': '利润率', 'max': 100},
                {'name': '商品数', 'max': 100}
            ],
            'shape': 'polygon',
            'splitNumber': 4,
            'axisName': {
                'color': '#333',
                'fontSize': 12,
                'fontWeight': 'bold'
            },
            'splitArea': {
                'areaStyle': {
                    'color': ['rgba(102, 126, 234, 0.05)', 'rgba(102, 126, 234, 0.1)',
                             'rgba(102, 126, 234, 0.15)', 'rgba(102, 126, 234, 0.2)']
                }
            }
        },
        'series': [{
            'name': '场景表现',
            'type': 'radar',
            'data': radar_data,
            'areaStyle': {'opacity': 0.3}
        }]
    }
    return DashECharts(option=option, id='scene-radar-chart', style={'height': '500px'})


def render_quadrant_plotly(scene_stats_df, median_orders, median_profit_rate):
    """四象限散点图 - Plotly版本(后备)"""
    color_map = {
        '明星场景 (高量高利)': '#28a745',
        '流量场景 (高量低利)': '#ffc107',
        '利润场景 (低量高利)': '#17a2b8',
        '问题场景 (低量低利)': '#dc3545'
    }
    
    fig = go.Figure()
    for quadrant in scene_stats_df['象限'].unique():
        quad_data = scene_stats_df[scene_stats_df['象限'] == quadrant]
        fig.add_trace(go.Scatter(
            x=quad_data['订单量'],
            y=quad_data['利润率'],
            mode='markers+text',
            name=quadrant,
            text=quad_data['场景'],
            textposition='top center',
            marker=dict(
                size=quad_data['销售额'] / 100,
                color=color_map.get(quadrant, '#666'),
                line=dict(width=2, color='white')
            ),
            hovertemplate='<b>%{text}</b><br>订单量: %{x}<br>利润率: %{y:.1f}%<extra></extra>'
        ))
    
    fig.add_hline(y=median_profit_rate, line_dash="dash", line_color="gray",
                  annotation_text=f"利润率中位数: {median_profit_rate:.1f}%")
    fig.add_vline(x=median_orders, line_dash="dash", line_color="gray",
                  annotation_text=f"订单量中位数: {int(median_orders)}")
    
    fig.update_layout(
        title='场景利润贡献矩阵 (四象限分析)',
        xaxis_title='订单量',
        yaxis_title='利润率 (%)',
        height=600,
        font=dict(family="Microsoft YaHei", size=12),
        showlegend=True
    )
    return dcc.Graph(figure=fig)


# ==================== 1. 时段场景热力图 + 场景利润矩阵 ====================

def render_heatmap_profit_matrix(df: pd.DataFrame):
    """
    场景利润矩阵 (时段×场景热力图 + 四象限分析)
    整合了时段场景交叉分析,避免重复Tab
    """
    
    # ========== 黄金组合洞察 ==========
    
    # 计算时段×场景交叉订单量 (使用count统计明细数,更准确反映活跃度)
    cross_data = df.groupby(['时段', '场景']).size().reset_index(name='订单明细数')
    cross_pivot = cross_data.pivot(index='时段', columns='场景', values='订单明细数').fillna(0)
    
    # 找出最热组合
    max_combo_value = 0
    max_combo = ('', '')
    for period in cross_pivot.index:
        for scene in cross_pivot.columns:
            value = cross_pivot.loc[period, scene]
            if value > max_combo_value:
                max_combo_value = value
                max_combo = (period, scene)
    
    # ========== 场景利润贡献矩阵 (四象限分析) ==========
    
    # 计算场景指标 (与Tab 1/2逻辑一致)
    scene_stats_list = []
    
    for scene in df['场景'].unique():
        scene_df = df[df['场景'] == scene]
        
        # 订单量
        order_count = scene_df['订单ID'].nunique()
        
        # 🔧 修复: 按订单ID分组汇总销售额
        if '实收价格' in scene_df.columns:
            total_sales = scene_df.groupby('订单ID')['实收价格'].sum().sum()
        else:
            total_sales = scene_df.groupby('订单ID')['商品实售价'].sum().sum()
        
        # 🔧 修复: 按订单ID分组汇总利润额
        if '实际利润' in scene_df.columns:
            total_profit = scene_df.groupby('订单ID')['实际利润'].sum().sum()
        elif '利润额' in scene_df.columns:
            total_profit = scene_df.groupby('订单ID')['利润额'].sum().sum()
        else:
            # 如果没有利润字段,用成本估算
            if '商品采购成本' in scene_df.columns or '成本' in scene_df.columns:
                cost_col = '商品采购成本' if '商品采购成本' in scene_df.columns else '成本'
                total_cost = scene_df.groupby('订单ID')[cost_col].sum().sum()
                total_profit = total_sales - total_cost
            else:
                total_profit = total_sales * 0.2  # 假设20%利润率
        
        # 利润率计算 (与Tab 1/2一致)
        profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
        
        # 商品数
        product_count = scene_df['商品名称'].nunique()
        
        scene_stats_list.append({
            '场景': scene,
            '订单量': order_count,
            '销售额': total_sales,
            '利润额': total_profit,
            '利润率': profit_rate,
            '商品数': product_count
        })
    
    scene_stats_df = pd.DataFrame(scene_stats_list)
    
    # 计算综合得分 (订单量×利润率,标准化后)
    scene_stats_df['综合得分'] = scene_stats_df['订单量'] * scene_stats_df['利润率']
    
    # 计算中位数用于四象限划分
    median_orders = scene_stats_df['订单量'].median()
    median_profit_rate = scene_stats_df['利润率'].median()
    
    # 添加象限标签
    def classify_quadrant(row):
        if row['订单量'] >= median_orders and row['利润率'] >= median_profit_rate:
            return '明星场景 (高量高利)'
        elif row['订单量'] >= median_orders and row['利润率'] < median_profit_rate:
            return '流量场景 (高量低利)'
        elif row['订单量'] < median_orders and row['利润率'] >= median_profit_rate:
            return '利润场景 (低量高利)'
        else:
            return '问题场景 (低量低利)'
    
    scene_stats_df['象限'] = scene_stats_df.apply(classify_quadrant, axis=1)
    
    # ========== 创建时段×场景热力图 ==========
    
    # 计算时段×场景交叉订单量
    cross_data = df.groupby(['时段', '场景'])['订单ID'].nunique().reset_index()
    cross_pivot = cross_data.pivot(index='时段', columns='场景', values='订单ID').fillna(0)
    
    # 时段排序
    period_order = ['清晨(6-9点)', '上午(9-12点)', '正午(12-14点)', '下午(14-18点)',
                   '傍晚(18-21点)', '晚间(21-24点)', '深夜(0-3点)', '凌晨(3-6点)']
    cross_pivot = cross_pivot.reindex([p for p in period_order if p in cross_pivot.index])
    
    # 布局
    layout = html.Div([
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="bi bi-grid-3x3-gap me-2"),
                    "场景利润矩阵 (时段×场景热力图 + 四象限分析)"
                ], className="text-primary mb-4")
            ])
        ]),
        
        # 🔥 黄金组合洞察
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.H5([html.I(className="bi bi-star me-2"), "🔥 黄金组合"], className="mb-3"),
                    html.H4(f"{max_combo[0]} × {max_combo[1]}", className="text-primary"),
                    html.P(f"{int(max_combo_value):,} 笔交易", className="text-muted mb-0")
                ], color="warning", className="shadow-sm")
            ], md=12)
        ], className="mb-4"),
        
        # 时段场景热力图
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🔥 时段×场景交易热力图"),
                    dbc.CardBody([
                        render_heatmap_echarts(cross_pivot) if ECHARTS_AVAILABLE
                        else render_heatmap_plotly(cross_pivot),
                        html.Small([
                            "📊 洞察: 颜色越深代表交易越活跃(订单明细数)。",
                            "快速识别黄金时段×场景组合。"
                        ], className="text-muted")
                    ])
                ], className="shadow-sm mb-4")
            ], width=12)
        ]),
        
        # 场景利润矩阵 (气泡图 + 雷达图组合)
        dbc.Row([
            # 气泡图
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("💎 场景利润贡献气泡图"),
                    dbc.CardBody([
                        render_quadrant_echarts(scene_stats_df, median_orders, median_profit_rate) if ECHARTS_AVAILABLE
                        else render_quadrant_plotly(scene_stats_df, median_orders, median_profit_rate),
                        html.Small([
                            "📊 洞察: 气泡大小=销售额,位置=订单量×利润率。",
                            "右上角的明星场景是核心支柱。"
                        ], className="text-muted")
                    ])
                ], className="shadow-sm mb-4")
            ], md=7),
            
            # 雷达图 - 显示TOP5场景综合表现
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🎯 TOP5场景综合表现雷达图"),
                    dbc.CardBody([
                        render_scene_radar_chart(scene_stats_df) if ECHARTS_AVAILABLE
                        else html.Div("雷达图需要ECharts支持", className="text-muted"),
                        html.Small([
                            "📊 洞察: 多维度评估场景价值。",
                            "面积越大=综合价值越高。"
                        ], className="text-muted")
                    ])
                ], className="shadow-sm mb-4")
            ], md=5)
        ]),
        
        # 四象限说明卡片
        dbc.Row([
            dbc.Col([
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        dbc.Alert([
                            html.H6("🌟 明星场景", className="alert-heading"),
                            html.P("高订单量 + 高利润率 → 核心支柱,重点投入", className="mb-0")
                        ], color="success")
                    ], md=3),
                    dbc.Col([
                        dbc.Alert([
                            html.H6("📈 流量场景", className="alert-heading"),
                            html.P("高订单量 + 低利润率 → 优化定价,提升利润", className="mb-0")
                        ], color="warning")
                    ], md=3),
                    dbc.Col([
                        dbc.Alert([
                            html.H6("💰 利润场景", className="alert-heading"),
                            html.P("低订单量 + 高利润率 → 扩大流量,提升销量", className="mb-0")
                        ], color="info")
                    ], md=3),
                    dbc.Col([
                        dbc.Alert([
                            html.H6("⚠️ 问题场景", className="alert-heading"),
                            html.P("低订单量 + 低利润率 → 优化或放弃", className="mb-0")
                        ], color="danger")
                    ], md=3)
                ])
            ], width=12)
        ])
    ])
    
    return layout


# ==================== 2. 时段销量趋势 + 客单价探索 ====================

def render_trend_price_analysis(df: pd.DataFrame):
    """
    渲染时段销量趋势和客单价探索
    计算逻辑与Tab 1/2完全一致
    """
    
    # ========== 时段销量趋势 ==========
    
    period_order = ['清晨(6-9点)', '上午(9-12点)', '正午(12-14点)', '下午(14-18点)',
                   '傍晚(18-21点)', '晚间(21-24点)', '深夜(0-3点)', '凌晨(3-6点)']
    
    # 按时段聚合 (修复: 先按订单ID分组,避免多商品订单重复计算)
    period_trend = []
    for period in period_order:
        period_df = df[df['时段'] == period]
        if len(period_df) == 0:
            continue
        
        order_count = period_df['订单ID'].nunique()
        item_count = len(period_df)
        
        # 🔧 修复: 按订单ID分组汇总,避免重复计算
        # 销售额: 先按订单汇总,再求和
        if '实收价格' in period_df.columns:
            order_sales = period_df.groupby('订单ID')['实收价格'].sum()
            total_sales = order_sales.sum()
        else:
            order_sales = period_df.groupby('订单ID')['商品实售价'].sum()
            total_sales = order_sales.sum()
        
        # 客单价: 使用订单平均值
        avg_order_value = order_sales.mean() if len(order_sales) > 0 else 0
        
        # 利润额: 按订单汇总
        if '实际利润' in period_df.columns:
            total_profit = period_df.groupby('订单ID')['实际利润'].sum().sum()
        elif '利润额' in period_df.columns:
            total_profit = period_df.groupby('订单ID')['利润额'].sum().sum()
        else:
            total_profit = 0
        
        # 利润率
        profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
        
        period_trend.append({
            '时段': period,
            '订单量': order_count,
            '商品数': item_count,
            '销售额': total_sales,
            '客单价': avg_order_value,
            '利润率': profit_rate
        })
    
    period_trend_df = pd.DataFrame(period_trend)
    
    # 时段销量趋势图
    trend_fig = go.Figure()
    
    trend_fig.add_trace(go.Scatter(
        x=period_trend_df['时段'],
        y=period_trend_df['订单量'],
        mode='lines+markers',
        name='订单量',
        line=dict(color='#667eea', width=3),
        marker=dict(size=10),
        yaxis='y'
    ))
    
    trend_fig.add_trace(go.Scatter(
        x=period_trend_df['时段'],
        y=period_trend_df['销售额'],
        mode='lines+markers',
        name='销售额',
        line=dict(color='#f6993f', width=3, dash='dash'),
        marker=dict(size=10, symbol='diamond'),
        yaxis='y2'
    ))
    
    trend_fig.update_layout(
        title='时段销量与销售额趋势',
        xaxis=dict(title='时段'),
        yaxis=dict(title='订单量', side='left'),
        yaxis2=dict(title='销售额 (¥)', side='right', overlaying='y'),
        height=400,
        font=dict(family="Microsoft YaHei", size=12),
        hovermode='x unified'
    )
    
    # ========== 客单价探索 ==========
    
    # 按场景聚合客单价 (与Tab 1/2一致)
    scene_price_data = []
    
    for scene in df['场景'].unique():
        scene_df = df[df['场景'] == scene]
        
        # 计算每个订单的客单价
        order_prices = []
        for order_id in scene_df['订单ID'].unique():
            order_df = scene_df[scene_df['订单ID'] == order_id]
            
            if '实收价格' in order_df.columns:
                order_total = order_df['实收价格'].sum()
            else:
                order_total = order_df['商品实售价'].sum()
            
            order_prices.append(order_total)
        
        if len(order_prices) > 0:
            scene_price_data.append({
                '场景': scene,
                '订单数': len(order_prices),
                '平均客单价': np.mean(order_prices),
                '中位数': np.median(order_prices),
                'Q1': np.percentile(order_prices, 25),
                'Q3': np.percentile(order_prices, 75),
                '最小值': np.min(order_prices),
                '最大值': np.max(order_prices)
            })
    
    price_df = pd.DataFrame(scene_price_data).sort_values('平均客单价', ascending=False)
    
    # 客单价对比柱状图
    price_bar_fig = go.Figure(data=[
        go.Bar(
            x=price_df['场景'],
            y=price_df['平均客单价'],
            text=price_df['平均客单价'].round(2),
            textposition='auto',
            marker_color='#667eea'
        )
    ])
    
    price_bar_fig.update_layout(
        title='各场景平均客单价对比',
        xaxis_title='场景',
        yaxis_title='平均客单价 (¥)',
        height=400,
        font=dict(family="Microsoft YaHei", size=12)
    )
    
    # 布局
    layout = html.Div([
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="bi bi-graph-up me-2"),
                    "时段销量趋势 & 客单价探索"
                ], className="text-primary mb-4")
            ])
        ]),
        
        # 时段销量趋势
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📈 时段销量与销售额趋势"),
                    dbc.CardBody([
                        dcc.Graph(figure=trend_fig),
                        html.Small([
                            "📊 洞察: 识别销售高峰和低谷时段,优化人员排班和库存。"
                        ], className="text-muted")
                    ])
                ], className="shadow-sm mb-4")
            ], width=12)
        ]),
        
        # 客单价分析
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(" 场景客单价对比"),
                    dbc.CardBody([
                        dcc.Graph(figure=price_bar_fig),
                        html.Small([
                            "💡 策略: 高客单价场景→精准营销,低客单价场景→提升单量。"
                        ], className="text-muted")
                    ])
                ], className="shadow-sm mb-4")
            ], width=12)
        ]),
        
        # 详细数据表
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📋 时段详细数据"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            columns=[
                                {'name': '时段', 'id': '时段'},
                                {'name': '订单量', 'id': '订单量', 'type': 'numeric', 'format': {'specifier': ','}},
                                {'name': '客单价 (¥)', 'id': '客单价', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                                {'name': '销售额 (¥)', 'id': '销售额', 'type': 'numeric', 'format': {'specifier': ',.2f'}},
                                {'name': '利润率 (%)', 'id': '利润率', 'type': 'numeric', 'format': {'specifier': '.1f'}}
                            ],
                            data=period_trend_df.to_dict('records'),
                            style_table={'overflowX': 'auto'},
                            style_cell={
                                'textAlign': 'left',
                                'fontFamily': 'Microsoft YaHei',
                                'fontSize': '13px',
                                'padding': '10px'
                            },
                            style_header={
                                'backgroundColor': '#667eea',
                                'color': 'white',
                                'fontWeight': 'bold'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'column_id': '利润率', 'filter_query': '{利润率} > 20'},
                                    'backgroundColor': '#d4edda',
                                    'color': '#155724'
                                },
                                {
                                    'if': {'column_id': '利润率', 'filter_query': '{利润率} < 10'},
                                    'backgroundColor': '#f8d7da',
                                    'color': '#721c24'
                                }
                            ]
                        )
                    ])
                ], className="shadow-sm")
            ], width=12)
        ])
    ])
    
    return layout


# ==================== 3. 商品场景关联网络 ====================

def render_product_scene_network(df: pd.DataFrame):
    """
    渲染商品场景关联网络图 - 优化版(Top10商品清晰展示)
    """
    
    # 选择Top10商品
    top_products = df.groupby('商品名称')['订单ID'].nunique().nlargest(10)
    
    # 获取所有场景
    all_scenes = sorted(df['场景'].unique())
    
    # 计算Top10商品在各场景的订单分布(确保包含所有场景)
    product_scene_data = []
    
    for product in top_products.index:
        product_df = df[df['商品名称'] == product]
        
        for scene in all_scenes:
            scene_df = product_df[product_df['场景'] == scene]
            order_count = scene_df['订单ID'].nunique()
            
            # 即使订单数为0也要添加,确保图表完整
            product_scene_data.append({
                '商品': product,
                '场景': scene,
                '订单数': order_count
            })
    
    links_df = pd.DataFrame(product_scene_data)
    
    # 创建分组柱状图 - 更清晰的可视化
    if len(links_df) > 0:
        network_fig = go.Figure()
        
        # 为每个场景创建一个柱状图系列
        colors = ['#667eea', '#f6993f', '#38b2ac', '#ed8936', '#9f7aea', '#f56565', '#48bb78', '#4299e1']
        
        for idx, scene in enumerate(all_scenes):
            scene_data = links_df[links_df['场景'] == scene]
            
            network_fig.add_trace(go.Bar(
                name=scene,
                x=scene_data['商品'],
                y=scene_data['订单数'],
                text=scene_data['订单数'].apply(lambda x: str(int(x)) if x > 0 else ''),
                textposition='outside',
                marker_color=colors[idx % len(colors)]
            ))
        
        network_fig.update_layout(
            title='Top 10商品场景关联分析 (分组柱状图)',
            xaxis_title='商品名称',
            yaxis_title='订单数',
            barmode='group',
            height=550,
            font=dict(family="Microsoft YaHei", size=13),
            legend=dict(
                title='消费场景',
                orientation='v',
                yanchor='top',
                y=1,
                xanchor='left',
                x=1.02,
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='#ccc',
                borderwidth=1
            ),
            xaxis=dict(tickangle=-30, tickfont=dict(size=11)),
            margin=dict(b=120)
        )
    else:
        network_fig = go.Figure()
        network_fig.add_annotation(
            text="暂无数据",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
    
    # Top20商品场景分布矩阵 (完全修复版)
    top_products = df.groupby('商品名称')['订单ID'].nunique().nlargest(20)
    all_scenes = sorted(df['场景'].unique())
    
    product_scene_matrix = []
    
    for product in top_products.index:
        product_df = df[df['商品名称'] == product]
        
        # 初始化行数据,默认所有场景订单数为0
        row = {'商品': product}
        
        # 遍历所有场景,计算订单数(没有订单的场景保持为0)
        for scene in all_scenes:
            scene_df = product_df[product_df['场景'] == scene]
            order_count = scene_df['订单ID'].nunique()
            row[scene] = int(order_count)  # 转为int避免浮点数
        
        # 添加总订单数
        row['总订单'] = int(top_products[product])
        
        product_scene_matrix.append(row)
    
    # 创建DataFrame并确保列顺序: 商品 | 场景1 | 场景2 | ... | 总订单
    matrix_df = pd.DataFrame(product_scene_matrix)
    cols_order = ['商品'] + all_scenes + ['总订单']
    matrix_df = matrix_df[cols_order]
    
    # 验证数据完整性
    print(f"✅ 商品场景矩阵: {len(matrix_df)}个商品 × {len(all_scenes)}个场景")
    print(f"   场景列表: {', '.join(all_scenes)}")
    
    # 布局
    layout = html.Div([
        dbc.Row([
            dbc.Col([
                html.H4([
                    html.I(className="bi bi-diagram-3 me-2"),
                    "商品场景关联网络"
                ], className="text-primary mb-4")
            ])
        ]),
        
        # 商品场景关联图
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("� 商品场景关联分析 (Top 10商品)"),
                    dbc.CardBody([
                        dcc.Graph(figure=network_fig),
                        html.Small([
                            "📊 洞察: 柱状图高度代表订单数,快速识别商品的主要销售场景。",
                            html.Br(),
                            "💡 应用: 针对高订单场景优化商品推荐和营销策略。"
                        ], className="text-muted")
                    ])
                ], className="shadow-sm mb-4")
            ], width=12)
        ]),
        
        # 商品场景矩阵表
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📋 Top 20商品场景分布矩阵"),
                    dbc.CardBody([
                        dash_table.DataTable(
                            columns=[{'name': col, 'id': col} for col in matrix_df.columns],
                            data=matrix_df.to_dict('records'),
                            style_table={'overflowX': 'auto'},
                            style_cell={
                                'textAlign': 'center',
                                'fontFamily': 'Microsoft YaHei',
                                'fontSize': '12px',
                                'padding': '8px'
                            },
                            style_header={
                                'backgroundColor': '#667eea',
                                'color': 'white',
                                'fontWeight': 'bold'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'filter_query': '{{{col}}} > 0'.format(col=col), 'column_id': col},
                                    'backgroundColor': '#e3f2fd'
                                } for col in matrix_df.columns if col not in ['商品', '总订单']
                            ],
                            page_size=20
                        ),
                        html.Hr(),
                        html.Small([
                            "💡 应用: 根据商品在各场景的分布,制定精准营销策略。",
                            html.Br(),
                            "例如: 某商品在'下午茶'场景订单多 → 14-16点重点推送。"
                        ], className="text-muted")
                    ])
                ], className="shadow-sm")
            ], width=12)
        ])
    ])
    
    return layout


# ==================== 4. 商品场景画像 + 场景洞察 ====================

def render_scene_insights(df: pd.DataFrame):
    """
    渲染场景深度洞察分析
    包括: 场景商品TOP榜、场景特征、场景营销建议
    """
    if '场景' not in df.columns:
        return dbc.Alert([
            html.H5("⚠️ 场景字段缺失", className="alert-heading"),
            html.P("数据中缺少'场景'字段,无法生成场景洞察。"),
            html.Hr(),
            html.Small("请确保数据已通过场景推断或智能打标添加场景字段。")
        ], color="warning")
    
    # 获取所有场景
    scenes = df['场景'].unique()
    
    # 如果没有场景数据
    if len(scenes) == 0:
        return dbc.Alert("暂无场景数据", color="info")
    
    scene_insights = []
    
    for scene in scenes:
        scene_df = df[df['场景'] == scene]
        
        # 场景订单量
        scene_orders = scene_df['订单ID'].nunique()
        
        # 场景TOP商品
        top_products = scene_df['商品名称'].value_counts().head(5)
        
        # 场景销售额
        if '实收价格' in scene_df.columns:
            scene_sales = scene_df['实收价格'].sum()
        else:
            scene_sales = scene_df['商品实售价'].sum()
        
        # 场景平均客单价
        scene_avg_price = scene_sales / scene_orders if scene_orders > 0 else 0
        
        # 场景卡片
        scene_card = dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="bi bi-star-fill me-2", style={'color': '#ffc107'}),
                    f"{scene}"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Small("订单量", className="text-muted"),
                        html.H4(f"{scene_orders:,}", className="text-primary mb-0")
                    ], md=4),
                    dbc.Col([
                        html.Small("销售额", className="text-muted"),
                        html.H4(f"¥{scene_sales:,.0f}", className="text-success mb-0")
                    ], md=4),
                    dbc.Col([
                        html.Small("客单价", className="text-muted"),
                        html.H4(f"¥{scene_avg_price:.1f}", className="text-info mb-0")
                    ], md=4)
                ]),
                html.Hr(),
                html.H6("🔥 TOP 5 热销商品", className="text-secondary mt-3 mb-2"),
                html.Ol([
                    html.Li(f"{product} ({count}单)") 
                    for product, count in top_products.items()
                ]),
                html.Hr(),
                html.H6("💡 营销建议", className="text-primary mb-2"),
                html.Ul([
                    html.Li(get_scene_marketing_advice(scene, scene_avg_price, scene_orders, df['订单ID'].nunique()))
                ])
            ])
        ], className="shadow-sm mb-3")
        
        scene_insights.append(scene_card)
    
    # 如果没有生成任何场景卡片
    if len(scene_insights) == 0:
        return dbc.Alert("暂无场景洞察数据", color="info")
    
    return html.Div([
        html.H5([
            html.I(className="bi bi-lightbulb me-2"),
            "场景深度洞察"
        ], className="text-primary mb-4"),
        html.P([
            f"📊 基于消费场景的商品销售分析和精准营销建议。识别到 {len(scenes)} 种场景。",
            html.Br(),
            "每个场景展示TOP热销商品和针对性的营销策略。"
        ], className="text-muted mb-4"),
        dbc.Row([
            dbc.Col(card, md=6, lg=4) for card in scene_insights
        ])
    ], style={'marginTop': '2rem'})


def get_scene_marketing_advice(scene: str, avg_price: float, scene_orders: int, total_orders: int) -> str:
    """
    根据场景特征生成营销建议
    """
    scene_ratio = (scene_orders / total_orders * 100) if total_orders > 0 else 0
    
    # 场景特征库
    scene_advice = {
        '早餐': '重点推送时间6-9点,推荐快捷早餐商品,强调配送速度',
        '午餐': '11-13点高峰推送,推荐午餐套餐,可提供满减优惠',
        '晚餐': '17-20点精准推送,推荐家庭装/聚餐商品,提供组合优惠',
        '夜宵': '21-24点推送,推荐零食/速食,强调深夜送达服务',
        '下午茶': '14-16点推送,推荐奶茶/甜点/轻食,可推第二件半价',
        '休闲零食': '全时段推广,推荐组合装,可推满额送',
        '应急购买': '保证库存,快速配送,可适当提价',
        '日用补充': '日常推广,推荐多件优惠,培养复购习惯',
        '营养补充': '推荐高品质商品,强调健康价值,可推会员专享',
        '社交娱乐': '周末/节假日重点推广,推荐聚会装,提供组合套餐'
    }
    
    base_advice = scene_advice.get(scene, '根据场景特点精准推送,优化商品组合')
    
    # 根据数据特征补充建议
    if scene_ratio > 20:
        return f"核心场景({scene_ratio:.1f}%订单)→{base_advice},加大投入"
    elif scene_ratio < 5:
        return f"潜力场景({scene_ratio:.1f}%订单)→{base_advice},挖掘增长空间"
    elif avg_price > 50:
        return f"高价值场景(客单¥{avg_price:.0f})→{base_advice},提升客单量"
    else:
        return base_advice


def render_product_scene_profile(df: pd.DataFrame):
    """
    渲染商品场景画像 + 场景洞察
    需要智能打标引擎
    """
    
    if not SMART_TAGGING_AVAILABLE:
        return dbc.Alert([
            html.H5("⚠️ 商品场景智能打标引擎未加载", className="alert-heading"),
            html.P("此功能需要商品场景智能打标引擎支持。"),
            html.Hr(),
            html.Small("请确保 '商品场景智能打标引擎.py' 文件存在于当前目录。")
        ], color="warning")
    
    # 检查是否已打标
    if '购买驱动' not in df.columns:
        return dbc.Alert([
            html.H5("⚠️ 数据未打标", className="alert-heading"),
            html.P("当前数据未进行智能打标,无法生成商品场景画像。"),
            html.Hr(),
            html.Small("请重新加载数据或等待数据自动打标完成。")
        ], color="warning")
    
    try:
        # 生成商品场景画像
        tagger = ProductSceneTagger()
        product_profiles = tagger.generate_product_scene_profile(df)
        
        # 购买驱动分布
        driver_stats = df['购买驱动'].value_counts()
        
        driver_fig = go.Figure(data=[
            go.Bar(
                x=driver_stats.index,
                y=driver_stats.values,
                text=driver_stats.values,
                textposition='auto',
                marker_color='#667eea'
            )
        ])
        
        driver_fig.update_layout(
            title='购买驱动分布',
            xaxis_title='驱动类型',
            yaxis_title='订单数',
            height=400,
            font=dict(family="Microsoft YaHei", size=12)
        )
        
        # 季节场景分布
        if '季节场景' in df.columns:
            season_stats = df['季节场景'].value_counts()
            
            season_fig = go.Figure(data=[
                go.Pie(
                    labels=season_stats.index,
                    values=season_stats.values,
                    hole=0.4
                )
            ])
            
            season_fig.update_layout(
                title='季节场景分布',
                height=400,
                font=dict(family="Microsoft YaHei", size=12)
            )
        else:
            season_fig = None
        
        # 布局
        # 直接创建包含两部分的完整布局(不使用子Tab切换,避免需要额外回调)
        layout = html.Div([
            dbc.Row([
                dbc.Col([
                    html.H4([
                        html.I(className="bi bi-tags me-2"),
                        "商品场景画像 & 场景洞察"
                    ], className="text-primary mb-4")
                ])
            ]),
            
            # ========== 第一部分: 商品画像总览 ==========
            html.H5([
                html.I(className="bi bi-clipboard-data me-2"),
                "📊 商品画像总览"
            ], className="text-secondary mb-3 mt-4"),
            
            # 关键指标
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("📊 总商品数", className="text-primary mb-2"),
                            html.H3(f"{len(product_profiles):,}", className="mb-0")
                        ])
                    ], className="shadow-sm text-center")
                ], md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("🎯 场景覆盖", className="text-success mb-2"),
                            html.H3(f"{df['场景'].nunique()}", className="mb-0"),
                            html.Small("种基础场景", className="text-muted")
                        ])
                    ], className="shadow-sm text-center")
                ], md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("💡 驱动类型", className="text-info mb-2"),
                            html.H3(f"{df['购买驱动'].nunique()}", className="mb-0"),
                            html.Small("种购买驱动", className="text-muted")
                        ])
                    ], className="shadow-sm text-center")
                ], md=3),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("📈 平均适配度", className="text-warning mb-2"),
                            html.H3(f"{product_profiles['场景适配度'].mean():.1f}%", className="mb-0")
                        ])
                    ], className="shadow-sm text-center")
                ], md=3)
            ], className="mb-4"),
            
            # 购买驱动和季节场景
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("💡 购买驱动分布"),
                        dbc.CardBody([
                            dcc.Graph(figure=driver_fig)
                        ])
                    ], className="shadow-sm")
                ], md=6 if season_fig else 12),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🌸 季节场景分布"),
                        dbc.CardBody([
                            dcc.Graph(figure=season_fig) if season_fig else html.P("暂无季节数据", className="text-center text-muted")
                        ])
                    ], className="shadow-sm")
                ], md=6) if season_fig else None
            ], className="mb-4"),
            
            # 商品场景画像表
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📋 商品场景画像详情 (Top 50)"),
                        dbc.CardBody([
                            dash_table.DataTable(
                                columns=[
                                    {'name': '商品名称', 'id': '商品名称'},
                                    {'name': '总订单量', 'id': '总订单量', 'type': 'numeric', 'format': {'specifier': ','}},
                                    {'name': '场景覆盖数', 'id': '场景覆盖数', 'type': 'numeric'},
                                    {'name': '主要场景', 'id': '主要场景'},
                                    {'name': '主要季节', 'id': '主要季节'},
                                    {'name': '购买驱动', 'id': '购买驱动'},
                                    {'name': '场景适配度', 'id': '场景适配度', 'type': 'numeric', 'format': {'specifier': '.1f'}}
                                ],
                                data=product_profiles.head(50).to_dict('records'),
                                style_table={'overflowX': 'auto'},
                                style_cell={
                                    'textAlign': 'left',
                                    'fontFamily': 'Microsoft YaHei',
                                    'fontSize': '12px',
                                    'padding': '10px',
                                    'whiteSpace': 'normal',
                                    'height': 'auto'
                                },
                                style_header={
                                    'backgroundColor': '#667eea',
                                    'color': 'white',
                                    'fontWeight': 'bold'
                                },
                                style_data_conditional=[
                                    {
                                        'if': {'column_id': '场景适配度', 'filter_query': '{场景适配度} >= 50'},
                                        'backgroundColor': '#d4edda',
                                        'color': '#155724'
                                    },
                                    {
                                        'if': {'column_id': '场景适配度', 'filter_query': '{场景适配度} < 30'},
                                        'backgroundColor': '#fff3cd',
                                        'color': '#856404'
                                    }
                                ],
                                page_size=20,
                                sort_action='native',
                                filter_action='native'
                            ),
                            html.Hr(),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Alert([
                                        html.H6("📖 字段说明", className="alert-heading"),
                                        html.Ul([
                                            html.Li("场景覆盖数: 商品出现在多少个不同场景"),
                                            html.Li("场景适配度: 场景覆盖数/总场景数×100%"),
                                            html.Li("购买驱动: 用户购买该商品的主要驱动因素"),
                                            html.Li("主要场景: 订单量最多的前3个场景")
                                        ], className="mb-0")
                                    ], color="light")
                                ], md=6),
                                
                                dbc.Col([
                                    dbc.Alert([
                                        html.H6("💡 营销建议", className="alert-heading"),
                                        html.Ul([
                                            html.Li("高适配度商品: 多场景营销,扩大覆盖"),
                                            html.Li("低适配度商品: 聚焦核心场景,精准推送"),
                                            html.Li("场景驱动商品: 时段+场景组合推荐"),
                                            html.Li("价格驱动商品: 满减活动,促销优惠")
                                        ], className="mb-0")
                                    ], color="info")
                                ], md=6)
                            ])
                        ])
                    ], className="shadow-sm")
                ], width=12)
            ]),
            
            # ========== 第二部分: 场景深度洞察 ==========
            html.Hr(className="my-5"),
            html.H5([
                html.I(className="bi bi-lightbulb me-2"),
                "💡 场景深度洞察"
            ], className="text-secondary mb-3"),
            
            # 场景洞察内容
            render_scene_insights(df)
        ])
        
        return layout
        
    except Exception as e:
        return dbc.Alert(f"生成商品场景画像失败: {str(e)}", color="danger")
