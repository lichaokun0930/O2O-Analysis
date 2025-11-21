"""
P3任务：前后端集成版智能看板
通过API调用后端，不直接读取Excel或数据库
"""

import sys
from pathlib import Path
import pandas as pd
import requests
from dash import Dash, dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class IntegratedDashboard:
    """集成版看板（前后端分离）"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.app = Dash(__name__, suppress_callback_exceptions=True)
        self.setup_layout()
        self.setup_callbacks()
    
    def call_api(self, endpoint: str, params: dict = None):
        """调用后端API"""
        url = f"{self.api_base_url}/api/{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[API Error] {endpoint}: {str(e)}")
            return None
    
    def get_orders_df(self, limit: int = 1000) -> pd.DataFrame:
        """获取订单数据"""
        data = self.call_api('orders', {'limit': limit})
        if data:
            return pd.DataFrame(data)
        return pd.DataFrame()
    
    def get_products_df(self, limit: int = 500) -> pd.DataFrame:
        """获取商品数据"""
        data = self.call_api('products', {'limit': limit})
        if data:
            return pd.DataFrame(data)
        return pd.DataFrame()
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        data = self.call_api('stats')
        return data if data else {}
    
    def setup_layout(self):
        """设置页面布局"""
        self.app.layout = html.Div([
            # 标题栏
            html.Div([
                html.H1("🏪 智能门店经营看板 (API集成版)", 
                       style={'color': '#1890ff', 'textAlign': 'center'}),
                html.P("数据源：后端API | 实时更新", 
                      style={'textAlign': 'center', 'color': '#666'}),
            ], style={'padding': '20px', 'backgroundColor': '#f0f2f5'}),
            
            # 控制面板
            html.Div([
                html.Div([
                    html.Label("刷新数据："),
                    html.Button("🔄 刷新", id='refresh-btn', n_clicks=0,
                               style={'marginLeft': '10px', 'padding': '5px 15px'}),
                    html.Span(id='last-update', style={'marginLeft': '20px', 'color': '#999'}),
                ], style={'display': 'flex', 'alignItems': 'center'}),
            ], style={'padding': '15px', 'backgroundColor': 'white', 'margin': '10px'}),
            
            # 统计卡片
            html.Div(id='stats-cards', style={'padding': '10px'}),
            
            # 主要内容区
            dcc.Tabs(id='main-tabs', value='tab-orders', children=[
                dcc.Tab(label='📊 订单分析', value='tab-orders'),
                dcc.Tab(label='📦 商品分析', value='tab-products'),
                dcc.Tab(label='📈 趋势分析', value='tab-trends'),
                dcc.Tab(label='⚙️ 系统信息', value='tab-system'),
            ]),
            
            html.Div(id='tab-content', style={'padding': '20px'}),
            
            # 隐藏的数据存储
            dcc.Store(id='orders-store'),
            dcc.Store(id='products-store'),
            dcc.Store(id='stats-store'),
        ])
    
    def setup_callbacks(self):
        """设置回调函数"""
        
        @self.app.callback(
            [Output('orders-store', 'data'),
             Output('products-store', 'data'),
             Output('stats-store', 'data'),
             Output('last-update', 'children')],
            [Input('refresh-btn', 'n_clicks')]
        )
        def refresh_data(n_clicks):
            """刷新数据"""
            # 获取数据
            orders_df = self.get_orders_df()
            products_df = self.get_products_df()
            stats = self.get_stats()
            
            # 更新时间
            update_time = f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            return (
                orders_df.to_dict('records') if not orders_df.empty else [],
                products_df.to_dict('records') if not products_df.empty else [],
                stats,
                update_time
            )
        
        @self.app.callback(
            Output('stats-cards', 'children'),
            [Input('stats-store', 'data'),
             Input('orders-store', 'data')]
        )
        def update_stats_cards(stats, orders_data):
            """更新统计卡片"""
            if not stats:
                return html.Div("加载中...", style={'textAlign': 'center', 'padding': '50px'})
            
            # 计算订单统计
            orders_df = pd.DataFrame(orders_data) if orders_data else pd.DataFrame()
            total_amount = orders_df['amount'].sum() if not orders_df.empty and 'amount' in orders_df else 0
            
            cards = html.Div([
                # 商品数
                html.Div([
                    html.H3("📦 商品总数"),
                    html.H2(f"{stats.get('products', 0):,}"),
                ], className='stat-card'),
                
                # 订单数
                html.Div([
                    html.H3("📋 订单总数"),
                    html.H2(f"{stats.get('orders', 0):,}"),
                ], className='stat-card'),
                
                # 销售总额
                html.Div([
                    html.H3("💰 销售总额"),
                    html.H2(f"¥{total_amount:,.2f}"),
                ], className='stat-card'),
                
                # 场景数
                html.Div([
                    html.H3("🏷️ 场景标签"),
                    html.H2(f"{stats.get('scenes', 0):,}"),
                ], className='stat-card'),
            ], style={
                'display': 'grid',
                'gridTemplateColumns': 'repeat(auto-fit, minmax(250px, 1fr))',
                'gap': '15px',
                'margin': '10px'
            })
            
            return cards
        
        @self.app.callback(
            Output('tab-content', 'children'),
            [Input('main-tabs', 'value'),
             Input('orders-store', 'data'),
             Input('products-store', 'data'),
             Input('stats-store', 'data')]
        )
        def render_tab_content(active_tab, orders_data, products_data, stats):
            """渲染标签页内容"""
            
            if active_tab == 'tab-orders':
                return self.render_orders_tab(orders_data)
            
            elif active_tab == 'tab-products':
                return self.render_products_tab(products_data)
            
            elif active_tab == 'tab-trends':
                return self.render_trends_tab(orders_data)
            
            elif active_tab == 'tab-system':
                return self.render_system_tab(stats)
            
            return html.Div("选择一个标签页")
    
    def render_orders_tab(self, orders_data):
        """订单分析标签页"""
        if not orders_data:
            return html.Div("暂无订单数据", style={'textAlign': 'center', 'padding': '50px'})
        
        df = pd.DataFrame(orders_data)
        
        # 按日期统计
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            daily_stats = df.groupby(df['date'].dt.date).agg({
                'amount': 'sum',
                'order_id': 'count'
            }).reset_index()
            daily_stats.columns = ['日期', '销售额', '订单数']
            
            # 销售额趋势图
            fig_amount = px.line(daily_stats, x='日期', y='销售额', 
                               title='每日销售额趋势',
                               markers=True)
            
            # 订单数趋势图
            fig_orders = px.bar(daily_stats, x='日期', y='订单数',
                              title='每日订单数量')
        else:
            fig_amount = go.Figure()
            fig_orders = go.Figure()
        
        return html.Div([
            html.H2("📊 订单分析"),
            dcc.Graph(figure=fig_amount),
            dcc.Graph(figure=fig_orders),
            
            html.H3("最近订单", style={'marginTop': '30px'}),
            html.Div([
                html.Table([
                    html.Thead(html.Tr([
                        html.Th("订单ID"),
                        html.Th("日期"),
                        html.Th("商品"),
                        html.Th("金额"),
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td(row.get('order_id', '')),
                            html.Td(str(row.get('date', ''))[:10]),
                            html.Td(row.get('product_name', '')),
                            html.Td(f"¥{row.get('amount', 0):.2f}"),
                        ]) for row in df.head(10).to_dict('records')
                    ])
                ], style={'width': '100%', 'borderCollapse': 'collapse'})
            ], style={'overflowX': 'auto'})
        ])
    
    def render_products_tab(self, products_data):
        """商品分析标签页"""
        if not products_data:
            return html.Div("暂无商品数据", style={'textAlign': 'center', 'padding': '50px'})
        
        df = pd.DataFrame(products_data)
        
        # 分类统计
        if 'category_level1' in df.columns:
            category_stats = df['category_level1'].value_counts().reset_index()
            category_stats.columns = ['分类', '数量']
            
            fig = px.pie(category_stats, names='分类', values='数量',
                        title='商品分类分布')
        else:
            fig = go.Figure()
        
        return html.Div([
            html.H2("📦 商品分析"),
            dcc.Graph(figure=fig),
            
            html.H3("商品列表", style={'marginTop': '30px'}),
            html.Div([
                html.Table([
                    html.Thead(html.Tr([
                        html.Th("商品名称"),
                        html.Th("分类"),
                        html.Th("售价"),
                        html.Th("成本"),
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td(row.get('name', '')),
                            html.Td(row.get('category_level1', '')),
                            html.Td(f"¥{row.get('price', 0):.2f}"),
                            html.Td(f"¥{row.get('cost', 0):.2f}" if row.get('cost') else '-'),
                        ]) for row in df.head(20).to_dict('records')
                    ])
                ], style={'width': '100%', 'borderCollapse': 'collapse'})
            ], style={'overflowX': 'auto'})
        ])
    
    def render_trends_tab(self, orders_data):
        """趋势分析标签页"""
        if not orders_data:
            return html.Div("暂无数据", style={'textAlign': 'center', 'padding': '50px'})
        
        df = pd.DataFrame(orders_data)
        
        return html.Div([
            html.H2("📈 趋势分析"),
            html.P("功能开发中...", style={'textAlign': 'center', 'padding': '50px', 'color': '#999'})
        ])
    
    def render_system_tab(self, stats):
        """系统信息标签页"""
        health = self.call_api('health')
        
        return html.Div([
            html.H2("⚙️ 系统信息"),
            
            html.Div([
                html.H3("后端状态"),
                html.P(f"状态: {health.get('status', 'unknown') if health else 'disconnected'}"),
                html.P(f"数据库: {health.get('database', 'unknown') if health else 'unknown'}"),
                html.P(f"API地址: {self.api_base_url}"),
            ], style={'backgroundColor': '#f9f9f9', 'padding': '20px', 'margin': '10px'}),
            
            html.Div([
                html.H3("数据统计"),
                html.P(f"商品总数: {stats.get('products', 0):,}"),
                html.P(f"订单总数: {stats.get('orders', 0):,}"),
                html.P(f"场景标签: {stats.get('scenes', 0):,}"),
                html.P(f"分析缓存: {stats.get('cache', 0):,}"),
            ], style={'backgroundColor': '#f9f9f9', 'padding': '20px', 'margin': '10px'}),
        ])
    
    def run(self, debug=True, port=8051):
        """运行看板"""
        print(f"\n{'='*60}")
        print(f"P3任务：前后端集成版看板")
        print(f"{'='*60}")
        print(f"后端API: {self.api_base_url}")
        print(f"前端地址: http://localhost:{port}")
        print(f"{'='*60}\n")
        
        # 测试API连接
        health = self.call_api('health')
        if health:
            print(f"✅ 后端连接成功")
            print(f"   商品: {health.get('stats', {}).get('products', 0):,}")
            print(f"   订单: {health.get('stats', {}).get('orders', 0):,}")
        else:
            print(f"❌ 后端连接失败，请确保后端服务运行在 {self.api_base_url}")
            print(f"   启动命令: python -m uvicorn backend.main:app --port 8000")
        
        print(f"\n启动看板...")
        self.app.run(debug=debug, port=port)


if __name__ == "__main__":
    dashboard = IntegratedDashboard(api_base_url="http://localhost:8000")
    dashboard.run(debug=True, port=8051)
