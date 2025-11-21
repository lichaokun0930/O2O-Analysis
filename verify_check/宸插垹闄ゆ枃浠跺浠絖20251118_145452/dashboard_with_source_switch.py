"""
P2增强版：智能门店看板 - 支持数据源切换
可以选择从Excel或数据库加载数据
"""

import sys
from pathlib import Path
import pandas as pd
from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.data_source_manager import DataSourceManager
from 真实数据处理器 import RealDataProcessor


class SmartDashboardWithSourceSwitch:
    """带数据源切换的智能看板"""
    
    def __init__(self):
        self.app = Dash(__name__, suppress_callback_exceptions=True)
        self.data_manager = DataSourceManager()
        self.processor = RealDataProcessor()
        
        # 默认Excel路径
        self.default_excel_path = r"门店数据\比价看板模块\订单数据-本店.xlsx"
        
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        """设置页面布局"""
        self.app.layout = html.Div([
            # 标题
            html.Div([
                html.H1("🏪 智能门店经营看板 (数据源可切换)", 
                       style={'color': '#1890ff', 'margin': '0'}),
                html.P("支持Excel和数据库双数据源", 
                      style={'color': '#666', 'margin': '5px 0'}),
            ], style={
                'padding': '20px',
                'backgroundColor': '#f0f2f5',
                'borderBottom': '2px solid #1890ff'
            }),
            
            # 数据源选择面板
            html.Div([
                html.Div([
                    html.Label("📁 数据源:", style={'fontWeight': 'bold', 'marginRight': '15px'}),
                    
                    dcc.RadioItems(
                        id='data-source-selector',
                        options=[
                            {'label': ' Excel文件', 'value': 'excel'},
                            {'label': ' 数据库', 'value': 'database'},
                        ],
                        value='excel',
                        inline=True,
                        style={'marginRight': '20px'}
                    ),
                    
                    html.Button('🔄 加载数据', id='load-data-btn', n_clicks=0,
                               style={
                                   'padding': '8px 20px',
                                   'backgroundColor': '#1890ff',
                                   'color': 'white',
                                   'border': 'none',
                                   'borderRadius': '4px',
                                   'cursor': 'pointer',
                                   'marginLeft': '15px'
                               }),
                    
                    html.Span(id='load-status', style={'marginLeft': '15px', 'color': '#52c41a'}),
                ], style={
                    'display': 'flex',
                    'alignItems': 'center',
                    'padding': '15px',
                    'backgroundColor': 'white',
                    'borderRadius': '4px',
                }),
                
                # Excel路径输入（条件显示）
                html.Div(id='excel-path-input', children=[
                    html.Label("Excel路径:", style={'marginRight': '10px'}),
                    dcc.Input(
                        id='excel-path',
                        type='text',
                        value=r'门店数据\比价看板模块\订单数据-本店.xlsx',
                        style={'width': '500px', 'padding': '5px'}
                    ),
                ], style={'marginTop': '10px', 'display': 'none'}),
                
                # 数据库过滤器（条件显示）
                html.Div(id='database-filters', children=[
                    html.Div([
                        html.Label("门店:", style={'marginRight': '10px'}),
                        dcc.Dropdown(
                            id='store-filter',
                            options=[],
                            placeholder='选择门店（可选）',
                            style={'width': '200px', 'display': 'inline-block'}
                        ),
                        
                        html.Label("起始日期:", style={'marginLeft': '20px', 'marginRight': '10px'}),
                        dcc.DatePickerSingle(
                            id='start-date',
                            placeholder='起始日期（可选）',
                            display_format='YYYY-MM-DD'
                        ),
                        
                        html.Label("结束日期:", style={'marginLeft': '20px', 'marginRight': '10px'}),
                        dcc.DatePickerSingle(
                            id='end-date',
                            placeholder='结束日期（可选）',
                            display_format='YYYY-MM-DD'
                        ),
                    ], style={'marginTop': '10px'})
                ], style={'display': 'none'}),
                
            ], style={'padding': '15px', 'backgroundColor': 'white', 'margin': '15px'}),
            
            # 数据统计卡片
            html.Div(id='stats-cards', style={'padding': '0 15px'}),
            
            # 主内容区 - 标签页
            html.Div([
                dcc.Tabs(id='main-tabs', value='tab-overview', children=[
                    dcc.Tab(label='📊 订单概览', value='tab-overview'),
                    dcc.Tab(label='📦 商品分析', value='tab-products'),
                    dcc.Tab(label='💰 收入分析', value='tab-revenue'),
                    dcc.Tab(label='🎯 场景分析', value='tab-scenes'),
                ]),
                
                html.Div(id='tab-content', style={'padding': '20px'}),
            ], style={'margin': '15px', 'backgroundColor': 'white'}),
            
            # 数据存储
            dcc.Store(id='data-store'),
            dcc.Store(id='current-source'),
        ])
    
    def setup_callbacks(self):
        """设置回调函数"""
        
        # 1. 切换数据源时显示/隐藏相应控件
        @self.app.callback(
            [Output('excel-path-input', 'style'),
             Output('database-filters', 'style')],
            [Input('data-source-selector', 'value')]
        )
        def toggle_source_controls(source):
            if source == 'excel':
                return {'marginTop': '10px', 'display': 'block'}, {'display': 'none'}
            else:
                return {'display': 'none'}, {'marginTop': '10px', 'display': 'block'}
        
        # 2. 初始化数据库选项
        @self.app.callback(
            Output('store-filter', 'options'),
            [Input('data-source-selector', 'value')]
        )
        def update_store_options(source):
            if source == 'database':
                stores = self.data_manager.get_available_stores()
                return [{'label': s, 'value': s} for s in stores]
            return []
        
        # 3. 加载数据
        @self.app.callback(
            [Output('data-store', 'data'),
             Output('current-source', 'data'),
             Output('load-status', 'children')],
            [Input('load-data-btn', 'n_clicks')],
            [State('data-source-selector', 'value'),
             State('excel-path', 'value'),
             State('store-filter', 'value'),
             State('start-date', 'date'),
             State('end-date', 'date')]
        )
        def load_data(n_clicks, source, excel_path, store, start_date, end_date):
            if n_clicks == 0:
                # 初始加载Excel数据
                df = self.data_manager.load_from_excel(self.default_excel_path)
                return (
                    df.to_dict('records'),
                    'excel',
                    f"✅ 已加载 {len(df):,} 条数据 (Excel)"
                )
            
            # 用户点击加载按钮
            if source == 'excel':
                df = self.data_manager.load_from_excel(excel_path)
                status = f"✅ 已加载 {len(df):,} 条数据 (Excel)"
            else:
                # 数据库
                kwargs = {}
                if store:
                    kwargs['store_name'] = store
                if start_date:
                    kwargs['start_date'] = pd.to_datetime(start_date)
                if end_date:
                    kwargs['end_date'] = pd.to_datetime(end_date)
                
                df = self.data_manager.load_from_database(**kwargs)
                status = f"✅ 已加载 {len(df):,} 条数据 (数据库)"
            
            return df.to_dict('records'), source, status
        
        # 4. 更新统计卡片
        @self.app.callback(
            Output('stats-cards', 'children'),
            [Input('data-store', 'data')]
        )
        def update_stats(data):
            if not data:
                return html.Div("无数据", style={'textAlign': 'center', 'padding': '50px'})
            
            df = pd.DataFrame(data)
            
            # 计算统计指标
            total_orders = len(df)
            total_amount = df['实收金额'].sum() if '实收金额' in df.columns else 0
            unique_products = df['商品名称'].nunique() if '商品名称' in df.columns else 0
            avg_order_value = total_amount / total_orders if total_orders > 0 else 0
            
            # 卡片样式
            card_style = {
                'backgroundColor': 'white',
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                'textAlign': 'center'
            }
            
            return html.Div([
                html.Div([
                    html.H4("订单总数", style={'color': '#666', 'margin': '0 0 10px 0'}),
                    html.H2(f"{total_orders:,}", style={'color': '#1890ff', 'margin': '0'}),
                ], style=card_style),
                
                html.Div([
                    html.H4("销售总额", style={'color': '#666', 'margin': '0 0 10px 0'}),
                    html.H2(f"¥{total_amount:,.2f}", style={'color': '#52c41a', 'margin': '0'}),
                ], style=card_style),
                
                html.Div([
                    html.H4("商品种类", style={'color': '#666', 'margin': '0 0 10px 0'}),
                    html.H2(f"{unique_products:,}", style={'color': '#fa8c16', 'margin': '0'}),
                ], style=card_style),
                
                html.Div([
                    html.H4("客单价", style={'color': '#666', 'margin': '0 0 10px 0'}),
                    html.H2(f"¥{avg_order_value:.2f}", style={'color': '#722ed1', 'margin': '0'}),
                ], style=card_style),
            ], style={
                'display': 'grid',
                'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))',
                'gap': '15px'
            })
        
        # 5. 渲染标签页内容
        @self.app.callback(
            Output('tab-content', 'children'),
            [Input('main-tabs', 'value'),
             Input('data-store', 'data')]
        )
        def render_tab(tab, data):
            if not data:
                return html.Div("请加载数据", style={'textAlign': 'center', 'padding': '50px'})
            
            df = pd.DataFrame(data)
            
            if tab == 'tab-overview':
                return self.render_overview_tab(df)
            elif tab == 'tab-products':
                return self.render_products_tab(df)
            elif tab == 'tab-revenue':
                return self.render_revenue_tab(df)
            elif tab == 'tab-scenes':
                return self.render_scenes_tab(df)
            
            return html.Div("未知标签页")
    
    def render_overview_tab(self, df):
        """订单概览标签页"""
        # 日期趋势
        if '日期' in df.columns:
            df['日期'] = pd.to_datetime(df['日期'])
            daily = df.groupby(df['日期'].dt.date).size().reset_index()
            daily.columns = ['日期', '订单数']
            
            fig_trend = px.line(daily, x='日期', y='订单数', 
                              title='📈 每日订单趋势',
                              markers=True)
        else:
            fig_trend = go.Figure()
        
        # 渠道分布
        if '渠道' in df.columns:
            channel = df['渠道'].value_counts().reset_index()
            channel.columns = ['渠道', '订单数']
            
            fig_channel = px.pie(channel, names='渠道', values='订单数',
                                title='📱 渠道分布')
        else:
            fig_channel = go.Figure()
        
        return html.Div([
            dcc.Graph(figure=fig_trend),
            dcc.Graph(figure=fig_channel),
        ])
    
    def render_products_tab(self, df):
        """商品分析标签页"""
        # Top商品
        if '商品名称' in df.columns and '销售数量' in df.columns:
            top_products = df.groupby('商品名称')['销售数量'].sum().sort_values(ascending=False).head(20)
            
            fig = px.bar(x=top_products.index, y=top_products.values,
                        title='📦 TOP20热销商品',
                        labels={'x': '商品', 'y': '销售数量'})
        else:
            fig = go.Figure()
        
        # 分类分布
        if '一级分类名' in df.columns:
            category = df['一级分类名'].value_counts().reset_index()
            category.columns = ['分类', '数量']
            
            fig_cat = px.treemap(category, path=['分类'], values='数量',
                                title='🏷️ 商品分类分布')
        else:
            fig_cat = go.Figure()
        
        return html.Div([
            dcc.Graph(figure=fig),
            dcc.Graph(figure=fig_cat),
        ])
    
    def render_revenue_tab(self, df):
        """收入分析标签页"""
        if '日期' in df.columns and '实收金额' in df.columns:
            df['日期'] = pd.to_datetime(df['日期'])
            daily_revenue = df.groupby(df['日期'].dt.date)['实收金额'].sum().reset_index()
            daily_revenue.columns = ['日期', '销售额']
            
            fig = px.area(daily_revenue, x='日期', y='销售额',
                         title='💰 每日销售额趋势')
        else:
            fig = go.Figure()
        
        return html.Div([
            dcc.Graph(figure=fig),
        ])
    
    def render_scenes_tab(self, df):
        """场景分析标签页"""
        if '场景' in df.columns:
            scene_stats = df['场景'].value_counts().reset_index()
            scene_stats.columns = ['场景', '订单数']
            
            fig = px.bar(scene_stats, x='场景', y='订单数',
                        title='🎯 消费场景分布')
        else:
            fig = go.Figure()
            fig.add_annotation(
                text="暂无场景数据<br>请确保订单数据包含场景字段",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color='#999')
            )
        
        return html.Div([
            dcc.Graph(figure=fig),
        ])
    
    def run(self, debug=True, port=8050):
        """运行看板"""
        print("\n" + "="*60)
        print("P2任务：智能门店看板（数据源可切换）")
        print("="*60)
        print(f"功能: ✅ Excel文件 | ✅ PostgreSQL数据库")
        print(f"地址: http://localhost:{port}")
        print("="*60 + "\n")
        
        # 测试数据库连接
        stats = self.data_manager.get_database_stats()
        print(f"数据库统计:")
        print(f"  商品: {stats.get('products', 0):,}")
        print(f"  订单: {stats.get('orders', 0):,}")
        print(f"  门店: {stats.get('stores', 0):,}")
        
        if stats.get('start_date'):
            print(f"  日期范围: {stats['start_date']} ~ {stats['end_date']}")
        
        print(f"\n启动看板...\n")
        self.app.run(debug=debug, port=port, host='0.0.0.0')


if __name__ == "__main__":
    dashboard = SmartDashboardWithSourceSwitch()
    dashboard.run(debug=True, port=8050)
