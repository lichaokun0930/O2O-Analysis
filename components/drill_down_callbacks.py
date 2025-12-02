"""
渠道分析下钻回调函数模块
实现4层金字塔式下钻架构的回调逻辑

回调函数清单:
1. drill_down_to_channel_callback - 总览→渠道详情
2. go_back_callback - 返回上一层
3. breadcrumb_navigation_callback - 面包屑导航跳转
4. update_drill_down_container - 根据当前层级渲染对应内容

作者: GitHub Copilot
日期: 2025-11-24
"""

from dash import html, dcc, Input, Output, State, callback_context, no_update
from dash.dependencies import ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any

# 导入Redis缓存管理器
try:
    from redis_cache_manager import get_cached_dataframe, get_cache_manager
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# 导入状态管理模块
try:
    from components.drill_down_manager import (
        DrillDownState, get_state_manager,
        create_breadcrumb_component, create_back_button,
        analyze_channel_health, get_drill_down_button_text, get_drill_down_button_color,
        get_filter_type_label
    )
    DRILL_DOWN_AVAILABLE = True
except ImportError:
    DRILL_DOWN_AVAILABLE = False

# 导入图表工具
try:
    from echarts_factory import create_line_chart, create_dual_axis_chart
    from dash_echarts import DashECharts
    from component_styles import create_stat_card
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    print("⚠️ 图表组件导入失败,部分功能受限")
    print("⚠️ 下钻状态管理模块未找到")


def _perform_go_back(history, current_layer, current_channel, current_product, filter_type):
    """
    执行返回逻辑的通用函数
    """
    # 如果已经在overview层,不执行返回
    if current_layer == 'overview' or current_layer is None:
        return no_update, no_update, no_update, no_update, no_update, no_update
    
    # 检查历史栈是否为空
    if not history or len(history) == 0:
        return 'overview', None, None, None, [], {
            'current_layer': 'overview',
            'current_channel': None,
            'current_product': None,
            'filter_type': None,
            'navigation_history': []
        }
    
    # 创建状态管理器并加载当前状态
    state = DrillDownState()
    state.current_layer = current_layer
    state.current_channel = current_channel
    state.current_product = current_product
    state.filter_type = filter_type
    state.navigation_history = history.copy() if history else []
    
    # 执行返回操作
    new_state = state.go_back()
    
    return (
        new_state['current_layer'],
        new_state['current_channel'],
        new_state['current_product'],
        new_state['filter_type'],
        new_state['navigation_history'],
        new_state
    )


def register_drill_down_callbacks(app):
    """
    注册所有下钻相关的回调函数
    
    Args:
        app: Dash应用实例
    """
    if not DRILL_DOWN_AVAILABLE:
        print("⚠️ 下钻功能不可用，跳过回调注册")
        return
    
    # 回调1: 渠道卡片点击 → 下钻到渠道详情
    @app.callback(
        [
            Output('drill-down-current-layer', 'data'),
            Output('drill-down-current-channel', 'data'),
            Output('drill-down-current-product', 'data'),
            Output('drill-down-filter-type', 'data'),
            Output('drill-down-navigation-history', 'data'),
            Output('drill-down-full-state', 'data')
        ],
        [
            Input({'type': 'drill-to-channel-btn', 'channel': ALL}, 'n_clicks')
        ],
        [
            State('drill-down-navigation-history', 'data'),
            State('drill-down-current-layer', 'data'),
            State('drill-down-current-channel', 'data'),
            State('drill-down-current-product', 'data'),
            State('drill-down-filter-type', 'data')
        ],
        prevent_initial_call=True
    )
    def drill_down_to_channel_callback(n_clicks_list, history, current_layer, 
                                       current_channel, current_product, filter_type):
        """
        下钻到渠道详情页
        
        Args:
            n_clicks_list: 所有渠道按钮的点击次数列表
            history: 导航历史栈
            current_layer: 当前层级
            current_channel: 当前渠道
            current_product: 当前商品
            filter_type: 当前筛选类型
            
        Returns:
            tuple: (新层级, 新渠道, 新商品, 新筛选类型, 新历史栈, 完整状态)
        """
        ctx = callback_context
        
        # 检查是否有按钮被点击
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update, no_update, no_update
            
        # 恢复旧逻辑: 检查 n_clicks_list 是否有有效点击
        # 这能同时解决 "自动下钻" (全为None/0) 和 "点击无反应" (triggered_value判断可能不准) 的问题
        clean_clicks = [c if c is not None else 0 for c in n_clicks_list]
        if not any(clean_clicks):
            return no_update, no_update, no_update, no_update, no_update, no_update
            
        # 获取触发的按钮ID
        try:
            triggered_prop_id = ctx.triggered[0]['prop_id']
            triggered_id = triggered_prop_id.split('.')[0]
            
            # 解析按钮ID获取渠道名称
            import json
            button_id = json.loads(triggered_id)
            channel_name = button_id['channel']
        except Exception as e:
            print(f"❌ [下钻回调] 解析触发ID失败: {e}")
            return no_update, no_update, no_update, no_update, no_update, no_update
        
        # 创建状态管理器并执行下钻
        state = DrillDownState()
        state.current_layer = current_layer or 'overview'
        state.current_channel = current_channel
        state.current_product = current_product
        state.filter_type = filter_type
        state.navigation_history = history or []
        
        # 执行下钻操作
        new_state = state.drill_down_to_channel(channel_name)
        
        return (
            new_state['current_layer'],
            new_state['current_channel'],
            new_state['current_product'],
            new_state['filter_type'],
            new_state['navigation_history'],
            new_state
        )
    
    # 回调2: 统一处理所有返回按钮 (主返回按钮 + 内部返回按钮)
    @app.callback(
        [
            Output('drill-down-current-layer', 'data', allow_duplicate=True),
            Output('drill-down-current-channel', 'data', allow_duplicate=True),
            Output('drill-down-current-product', 'data', allow_duplicate=True),
            Output('drill-down-filter-type', 'data', allow_duplicate=True),
            Output('drill-down-navigation-history', 'data', allow_duplicate=True),
            Output('drill-down-full-state', 'data', allow_duplicate=True)
        ],
        [
            Input('drill-down-back-button', 'n_clicks'),
            Input({'type': 'inner-back-btn', 'index': ALL}, 'n_clicks')
        ],
        [
            State('drill-down-navigation-history', 'data'),
            State('drill-down-current-layer', 'data'),
            State('drill-down-current-channel', 'data'),
            State('drill-down-current-product', 'data'),
            State('drill-down-filter-type', 'data')
        ],
        prevent_initial_call=True
    )
    def unified_go_back_callback(main_n_clicks, inner_n_clicks_list, history, current_layer, 
                                current_channel, current_product, filter_type):
        """
        统一返回逻辑 (增强版)
        """
        try:
            ctx = callback_context
            if not ctx.triggered:
                return no_update, no_update, no_update, no_update, no_update, no_update
                
            triggered_id = ctx.triggered[0]['prop_id']
            triggered_value = ctx.triggered[0]['value']
            
            # 检查是否有效点击
            if triggered_value is None:
                return no_update, no_update, no_update, no_update, no_update, no_update

            # 如果已经在overview层,不执行返回
            if current_layer == 'overview' or current_layer is None:
                return no_update, no_update, no_update, no_update, no_update, no_update
            
            # 检查历史栈是否为空
            if not history or len(history) == 0:
                return 'overview', None, None, None, [], {
                    'current_layer': 'overview',
                    'current_channel': None,
                    'current_product': None,
                    'filter_type': None,
                    'navigation_history': []
                }
            
            # 创建状态管理器并加载当前状态
            state = DrillDownState()
            state.current_layer = current_layer
            state.current_channel = current_channel
            state.current_product = current_product
            state.filter_type = filter_type
            state.navigation_history = history.copy() if history else []
            
            # 执行返回操作
            new_state = state.go_back()
            
            return (
                new_state['current_layer'],
                new_state['current_channel'],
                new_state['current_product'],
                new_state['filter_type'],
                new_state['navigation_history'],
                new_state
            )
            
        except Exception as e:
            print(f"❌ [返回逻辑] 发生异常: {e}")
            import traceback
            traceback.print_exc()
            return no_update, no_update, no_update, no_update, no_update, no_update
    
    # 回调3: 面包屑导航 → 跳转到指定层级
    @app.callback(
        [
            Output('drill-down-current-layer', 'data', allow_duplicate=True),
            Output('drill-down-current-channel', 'data', allow_duplicate=True),
            Output('drill-down-current-product', 'data', allow_duplicate=True),
            Output('drill-down-filter-type', 'data', allow_duplicate=True),
            Output('drill-down-navigation-history', 'data', allow_duplicate=True),
            Output('drill-down-full-state', 'data', allow_duplicate=True)
        ],
        [
            Input({'type': 'breadcrumb-link', 'index': ALL, 'layer': ALL}, 'n_clicks')
        ],
        [
            State('drill-down-navigation-history', 'data')
        ],
        prevent_initial_call=True
    )
    def breadcrumb_navigation_callback(n_clicks_list, history):
        """
        面包屑导航跳转
        
        Args:
            n_clicks_list: 所有面包屑链接的点击次数列表
            history: 导航历史栈
            
        Returns:
            tuple: (新层级, 新渠道, 新商品, 新筛选类型, 新历史栈, 完整状态)
        """
        ctx = callback_context
        
        # 检查是否有链接被点击
        if not ctx.triggered or not any(n_clicks_list):
            return no_update, no_update, no_update, no_update, no_update, no_update
        
        # 获取触发的链接ID
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # 解析链接ID获取目标层级
        import json
        link_id = json.loads(triggered_id)
        target_layer = link_id['layer']
        breadcrumb_index = link_id['index']
        
        # 根据历史栈恢复到指定层级
        state = DrillDownState()
        
        # 从历史栈中找到对应的状态
        if breadcrumb_index == 0:
            # 返回总览
            state.jump_to_layer('overview')
        elif history and breadcrumb_index <= len(history):
            # 恢复到历史栈中的某一层
            target_state = history[breadcrumb_index - 1]
            state.current_layer = target_state['layer']
            state.current_channel = target_state.get('channel')
            state.current_product = target_state.get('product')
            state.filter_type = target_state.get('filter_type')
            # 截断历史栈
            state.navigation_history = history[:breadcrumb_index - 1]
        
        new_state = state.get_state()
        
        return (
            new_state['current_layer'],
            new_state['current_channel'],
            new_state['current_product'],
            new_state['filter_type'],
            new_state['navigation_history'],
            new_state
        )
    
    # 回调4: 根据当前层级更新下钻容器内容
    @app.callback(
        [
            Output('drill-down-analysis-container', 'children'),
            Output('drill-down-analysis-container', 'className'),
            # ✅ 新增: 控制其他区域的显示/隐藏，解决遮挡问题
            Output('tab1-channel-section', 'style'),
            Output('tab1-aov-section', 'style'),
            Output('btn-show-detail-analysis', 'style'),
        ],
        [
            Input('drill-down-current-layer', 'data'),
            Input('drill-down-current-channel', 'data'),
            Input('drill-down-current-product', 'data'),
            Input('drill-down-filter-type', 'data'),
            Input('drill-down-navigation-history', 'data')
        ],
        [
            State('db-store-filter', 'value'),  # ✅ 新增: 获取当前门店名称
            State('db-date-range', 'start_date'), # ✅ 新增: 获取全局开始日期
            State('db-date-range', 'end_date')    # ✅ 新增: 获取全局结束日期
        ],
        prevent_initial_call='initial_duplicate'
    )
    def update_drill_down_container(current_layer, current_channel, current_product,
                                    filter_type, history, store_name, start_date, end_date):
        """
        根据当前层级渲染对应的内容,同时控制容器显示/隐藏
        """
        # 创建状态管理器
        state = DrillDownState()
        state.current_layer = current_layer or 'overview'
        state.current_channel = current_channel
        state.current_product = current_product
        state.filter_type = filter_type
        state.navigation_history = history or []
        
        # 生成面包屑和返回按钮
        breadcrumb_path = state.get_breadcrumb_path()
        breadcrumb_ui = create_breadcrumb_component(breadcrumb_path)
        back_button = create_back_button(disabled=(current_layer == 'overview'))
        
        # 默认显示样式
        show_style = {'display': 'block'}
        hide_style = {'display': 'none'}
        
        # 根据层级渲染不同内容
        if current_layer == 'overview' or current_layer is None:
            # 第1层: 总览仪表盘 - 隐藏下钻容器, 显示其他内容
            return html.Div(), 'd-none', show_style, show_style, show_style
        
        elif current_layer == 'channel':
            # 第2层: 渠道深度分析 - 显示下钻容器, 隐藏其他内容
            content = render_channel_detail(current_channel, store_name, start_date, end_date)
            drill_down_class = 'drill-down-overlay'
        
        elif current_layer == 'product_list':
            # 第3层: 商品清单页面
            content = render_product_list(current_channel, filter_type)
            drill_down_class = 'drill-down-overlay'
        
        elif current_layer == 'product_insight':
            # 第4层: 单品深度洞察
            content = render_product_insight(current_channel, current_product)
            drill_down_class = 'drill-down-overlay'
        
        else:
            content = dbc.Alert(f"未知层级: {current_layer}", color="danger")
            drill_down_class = 'drill-down-overlay'
        
        # 组装最终布局
        final_content = html.Div([
            breadcrumb_ui,
            back_button,
            html.Hr(),
            content
        ])
        
        # 返回: 容器内容, 容器类名, 渠道卡片样式, 客单价样式, 按钮样式
        # 注意: 当下钻时, 隐藏所有其他区域
        return final_content, drill_down_class, hide_style, hide_style, hide_style
    
    # 回调1.5: 成本结构点击 -> 下钻到商品清单
    @app.callback(
        [
            Output('drill-down-current-layer', 'data', allow_duplicate=True),
            Output('drill-down-current-channel', 'data', allow_duplicate=True),
            Output('drill-down-current-product', 'data', allow_duplicate=True),
            Output('drill-down-filter-type', 'data', allow_duplicate=True),
            Output('drill-down-navigation-history', 'data', allow_duplicate=True),
            Output('drill-down-full-state', 'data', allow_duplicate=True)
        ],
        [
            Input({'type': 'cost-drill-btn', 'channel': ALL, 'filter': ALL}, 'n_clicks')
        ],
        [
            State('drill-down-navigation-history', 'data'),
            State('drill-down-current-layer', 'data'),
            State('drill-down-current-channel', 'data'),
            State('drill-down-current-product', 'data'),
            State('drill-down-filter-type', 'data')
        ],
        prevent_initial_call=True
    )
    def drill_down_to_product_list_callback(n_clicks_list, history, current_layer, 
                                            current_channel, current_product, filter_type):
        """
        下钻到商品清单页
        """
        ctx = callback_context
        
        if not ctx.triggered or not any(n_clicks_list):
            return no_update, no_update, no_update, no_update, no_update, no_update
        
        # 获取触发的按钮ID
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        import json
        button_id = json.loads(triggered_id)
        target_filter = button_id['filter']
        target_channel = button_id.get('channel') # 从按钮ID获取渠道
        
        # 创建状态管理器
        state = DrillDownState()
        state.current_layer = current_layer
        # 优先使用按钮中的渠道信息，如果为空则使用当前状态
        state.current_channel = target_channel if target_channel else current_channel
        state.current_product = current_product
        state.filter_type = filter_type
        state.navigation_history = history or []
        
        # 执行下钻
        new_state = state.drill_down_to_product_list(target_filter)
        
        return (
            new_state['current_layer'],
            new_state['current_channel'],
            new_state['current_product'],
            new_state['filter_type'],
            new_state['navigation_history'],
            new_state
        )

    # 回调1.6: TOP商品点击 -> 下钻到单品洞察
    @app.callback(
        [
            Output('drill-down-current-layer', 'data', allow_duplicate=True),
            Output('drill-down-current-channel', 'data', allow_duplicate=True),
            Output('drill-down-current-product', 'data', allow_duplicate=True),
            Output('drill-down-filter-type', 'data', allow_duplicate=True),
            Output('drill-down-navigation-history', 'data', allow_duplicate=True),
            Output('drill-down-full-state', 'data', allow_duplicate=True)
        ],
        [
            Input({'type': 'product-drill-btn', 'channel': ALL, 'product': ALL}, 'n_clicks')
        ],
        [
            State('drill-down-navigation-history', 'data'),
            State('drill-down-current-layer', 'data'),
            State('drill-down-current-channel', 'data'),
            State('drill-down-current-product', 'data'),
            State('drill-down-filter-type', 'data')
        ],
        prevent_initial_call=True
    )
    def drill_down_to_product_insight_callback(n_clicks_list, history, current_layer, 
                                               current_channel, current_product, filter_type):
        """
        下钻到单品洞察页
        """
        ctx = callback_context
        
        if not ctx.triggered or not any(n_clicks_list):
            return no_update, no_update, no_update, no_update, no_update, no_update
        
        # 获取触发的按钮ID
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        import json
        button_id = json.loads(triggered_id)
        target_product = button_id['product']
        target_channel = button_id.get('channel') # 从按钮ID获取渠道
        
        # 创建状态管理器
        state = DrillDownState()
        state.current_layer = current_layer
        # 优先使用按钮中的渠道信息
        state.current_channel = target_channel if target_channel else current_channel
        state.current_product = current_product
        state.filter_type = filter_type
        state.navigation_history = history or []
        
        # 执行下钻
        new_state = state.drill_down_to_product_insight(target_product)
        
        return (
            new_state['current_layer'],
            new_state['current_channel'],
            new_state['current_product'],
            new_state['filter_type'],
            new_state['navigation_history'],
            new_state
        )
    
    # 回调1.7: 导出改价建议表
    @app.callback(
        Output("download-repricing-list", "data"),
        Input("btn-export-repricing", "n_clicks"),
        [
            State("drill-down-current-channel", "data"),
            State("drill-down-filter-type", "data")
        ],
        prevent_initial_call=True
    )
    def export_repricing_list(n_clicks, channel_name, filter_type):
        """
        导出改价建议表
        """
        if not n_clicks:
            return no_update
            
        if not channel_name:
             return no_update
        
        try:
            # 1. 获取数据
            df_global = get_real_global_data()
            if df_global is None or df_global.empty:
                return no_update
                
            # 2. 筛选数据
            df = df_global[df_global['渠道'] == channel_name].copy()
            if df.empty:
                return no_update

            # 🧹 [展示优化] 剔除耗材
            category_col = None
            for col_name in ['一级分类名', '美团一级分类', '一级分类']:
                if col_name in df.columns:
                    category_col = col_name
                    break
            
            if category_col:
                df = df[df[category_col] != '耗材'].copy()

            # 3. 聚合计算 (对齐营销分析逻辑)
            numeric_cols = ['实收价格', '利润额', '商品采购成本']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # 检查关键字段
            if '利润额' not in df.columns:
                df['利润额'] = df['实收价格'] - df.get('商品采购成本', 0)

            agg_rules = {
                '订单ID': 'nunique', # 销量
                '利润额': 'sum',     # 总利润
                '实收价格': 'sum'    # 销售额
            }
            
            product_agg = df.groupby('商品名称').agg(agg_rules).rename(columns={
                '订单ID': '销量',
                '利润额': '总利润',
                '实收价格': '销售额'
            }).reset_index()
            
            # 计算衍生指标
            product_agg['毛利率'] = (product_agg['总利润'] / product_agg['销售额'] * 100).fillna(0).round(1)
            product_agg['单均利润'] = (product_agg['总利润'] / product_agg['销量']).fillna(0).round(2)
            
            # 补充总成本 (用于导出展示)
            if '商品采购成本' in df.columns:
                cost_agg = df.groupby('商品名称')['商品采购成本'].sum().reset_index().rename(columns={'商品采购成本': '总成本'})
                product_agg = product_agg.merge(cost_agg, on='商品名称', how='left')
            else:
                product_agg['总成本'] = 0
            
            # 4. 应用筛选
            filtered_products = pd.DataFrame()
            if filter_type == 'low-margin':
                filtered_products = product_agg[product_agg['毛利率'] < 15].copy()
            elif filter_type == 'delivery-issues':
                filtered_products = product_agg[(product_agg['单均利润'] < 2) & (product_agg['销量'] > 10)].copy()
            elif filter_type == 'discount-products':
                # 简单处理: 销量高且毛利低的也算
                filtered_products = product_agg[(product_agg['毛利率'] < 20) & (product_agg['销量'] > 5)].copy()
            else:
                filtered_products = product_agg.copy()
            
            if filtered_products.empty:
                return no_update
                
            # 5. 生成导出表格
            export_df = filtered_products[['商品名称', '销量', '销售额', '总成本', '总利润', '毛利率', '单均利润']].copy()
            export_df['建议操作'] = ''
            
            if filter_type == 'low-margin':
                export_df['建议操作'] = '建议涨价或降低成本'
            elif filter_type == 'delivery-issues':
                export_df['建议操作'] = '建议提高起送价'
            elif filter_type == 'discount-products':
                export_df['建议操作'] = '建议减少活动力度'
                
            # 6. 导出
            filename = f"改价建议表_{channel_name}_{filter_type}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx"
            return dcc.send_data_frame(export_df.to_excel, filename, index=False)
            
        except Exception as e:
            print(f"❌ [导出] 失败: {e}")
            import traceback
            traceback.print_exc()
            return no_update
    
    # 回调1.8: 批量波动分析
    @app.callback(
        [Output("modal-batch-analysis", "is_open"),
         Output("modal-batch-analysis-content", "children")],
        [Input("btn-batch-analysis", "n_clicks"),
         Input("btn-close-batch-analysis", "n_clicks")],
        [State("modal-batch-analysis", "is_open"),
         State("drill-down-current-channel", "data"),
         State("drill-down-filter-type", "data")],
        prevent_initial_call=True
    )
    def toggle_batch_analysis_modal(n_open, n_close, is_open, channel_name, filter_type):
        """
        切换批量波动分析弹窗状态
        """
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update
            
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # 关闭弹窗
        if button_id == "btn-close-batch-analysis":
            return False, no_update
            
        # 打开弹窗并生成内容
        if button_id == "btn-batch-analysis" and n_open:
            content = generate_batch_volatility_analysis(channel_name, filter_type)
            return True, content
            
        return is_open, no_update
    
    # 回调1.9: 表格点击 -> 下钻到单品洞察
    @app.callback(
        [
            Output('drill-down-current-layer', 'data', allow_duplicate=True),
            Output('drill-down-current-channel', 'data', allow_duplicate=True),
            Output('drill-down-current-product', 'data', allow_duplicate=True),
            Output('drill-down-filter-type', 'data', allow_duplicate=True),
            Output('drill-down-navigation-history', 'data', allow_duplicate=True),
            Output('drill-down-full-state', 'data', allow_duplicate=True)
        ],
        [
            Input('product-list-table', 'active_cell')
        ],
        [
            State('product-list-table', 'derived_viewport_data'), # ✅ 修复: 使用当前页数据，解决分页索引错位问题
            State('product-list-table', 'data'),
            State('drill-down-navigation-history', 'data'),
            State('drill-down-current-layer', 'data'),
            State('drill-down-current-channel', 'data'),
            State('drill-down-current-product', 'data'),
            State('drill-down-filter-type', 'data')
        ],
        prevent_initial_call=True
    )
    def drill_down_from_table_callback(active_cell, viewport_rows, full_data, history, current_layer, 
                                      current_channel, current_product, filter_type):
        """
        从表格点击下钻到单品洞察
        """
        try:
            # 优先使用当前页数据(viewport_rows), 确保索引对应正确
            current_rows = viewport_rows if viewport_rows is not None else full_data
            
            if not active_cell:
                return no_update, no_update, no_update, no_update, no_update, no_update
                
            if not current_rows:
                return no_update, no_update, no_update, no_update, no_update, no_update
                
            # 检查点击的是否是操作列
            if active_cell['column_id'] != '操作':
                return no_update, no_update, no_update, no_update, no_update, no_update
                
            # 获取点击的行数据
            row_index = active_cell['row']
            if row_index >= len(current_rows):
                return no_update, no_update, no_update, no_update, no_update, no_update
                
            target_product = current_rows[row_index]['商品名称']
            
            # 创建状态管理器
            state = DrillDownState()
            state.current_layer = current_layer
            state.current_channel = current_channel
            state.current_product = current_product
            state.filter_type = filter_type
            state.navigation_history = history or []
            
            # 执行下钻
            new_state = state.drill_down_to_product_insight(target_product)
            
            return (
                new_state['current_layer'],
                new_state['current_channel'],
                new_state['current_product'],
                new_state['filter_type'],
                new_state['navigation_history'],
                new_state
            )
        except Exception as e:
            print(f"❌ [表格下钻] 发生异常: {e}")
            import traceback
            traceback.print_exc()
            return no_update, no_update, no_update, no_update, no_update, no_update
    
    print("✅ 下钻回调函数已注册 (4个回调)")


# ========== 辅助函数: 获取真实的全局数据 ==========
def get_real_global_data():
    """
    获取真实的全局数据(GLOBAL_DATA)
    优先尝试从__main__模块获取,因为应用运行时数据存储在那里
    """
    import sys
    
    # 1. 尝试从__main__获取 (最可靠的方式)
    if '__main__' in sys.modules:
        main_module = sys.modules['__main__']
        if hasattr(main_module, 'get_global_data'):
            return main_module.get_global_data()
        if hasattr(main_module, 'GLOBAL_DATA'):
            return main_module.GLOBAL_DATA
            
    # 2. 尝试从导入的模块获取 (可能为空,如果是循环导入产生的副本)
    try:
        from 智能门店看板_Dash版 import get_global_data
        return get_global_data()
    except ImportError:
        pass
        
    return None

# ========== 渲染函数(占位实现,后续完善) ==========

def render_overview_dashboard():
    """渲染第1层:总览仪表盘 - 显示真实的渠道对比卡片"""
    try:
        # 导入全局数据
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from 智能门店看板_Dash版 import _create_channel_comparison_cards, calculate_order_metrics
        
        # ✅ 使用增强版获取器获取最新数据
        GLOBAL_DATA = get_real_global_data()
        
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return dbc.Alert("⚠️ 暂无数据,请先上传订单数据", color="warning")
        
        df = GLOBAL_DATA.copy()
        
        # 计算订单聚合数据
        order_agg = calculate_order_metrics(df, calc_mode='all_no_fallback')
        
        # 渲染渠道卡片(不传channel_comparison,使用默认)
        channel_cards = _create_channel_comparison_cards(df, order_agg, channel_comparison=None)
        
        return html.Div([
            html.H4("📊 渠道表现总览", className="mb-3"),
            channel_cards
        ])
        
    except Exception as e:
        print(f"❌ [总览仪表盘] 渲染失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 降级显示占位提示
        return dbc.Alert([
            html.H4("📊 总览仪表盘", className="alert-heading"),
            html.P("显示3个渠道卡片,点击卡片下钻到渠道详情"),
            html.Hr(),
            html.P("🚧 待实现: 重构渠道卡片,添加健康度标签和下钻按钮", className="mb-0"),
            html.Hr(),
            html.P(f"⚠️ 加载失败: {str(e)}", className="text-danger small")
        ], color="info")


def render_channel_detail(channel_name, store_name=None, start_date=None, end_date=None):
    """
    渲染第2层:渠道深度分析 (重构版 - 增强趋势分析)
    
    包含:
    - 4个总体指标卡片(销售额/订单数/利润额/利润率)
    - 渠道经营健康度诊断 (双轴图: 销售额 vs 利润率/单均成本)
    - 成本结构分解
    - TOP10商品表格
    
    ⚠️ 关键逻辑: 从主看板的全局order_agg中提取该渠道数据,确保计算一致性
    """
    try:
        # 导入必要模块
        import sys
        import os
        import pandas as pd
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from 智能门店看板_Dash版 import calculate_order_metrics, CHANNELS_TO_REMOVE, PLATFORM_FEE_CHANNELS
        from echarts_factory import create_line_chart, create_dual_axis_chart
        
        # 🔄 尝试从Redis获取最新数据 (解决模块间GLOBAL_DATA不同步问题)
        df = None
        if REDIS_AVAILABLE and store_name:
            try:
                # 尝试获取展示数据
                redis_key = f"store_data:{store_name}:display"
                cached_df = get_cached_dataframe(redis_key)
                if cached_df is not None and not cached_df.empty:
                    df = cached_df
                else:
                    # 尝试获取完整数据
                    redis_key_full = f"store_full_data:{store_name}"
                    cached_full = get_cached_dataframe(redis_key_full)
                    if cached_full is not None and not cached_full.empty:
                        df = cached_full
            except Exception as e:
                pass
        
        # 如果Redis未命中，回退到GLOBAL_DATA (可能 stale)
        if df is None:
            # ✅ 使用增强版获取器获取最新数据
            GLOBAL_DATA = get_real_global_data()
            
            if GLOBAL_DATA is None:
                return dbc.Alert("⚠️ 暂无数据 (GLOBAL_DATA is None)", color="warning")
                
            if GLOBAL_DATA.empty:
                return dbc.Alert("⚠️ 暂无数据 (GLOBAL_DATA is Empty)", color="warning")
                
            df = GLOBAL_DATA.copy()
            print(f"✅ [Fallback] 成功从GLOBAL_DATA加载数据: {len(df)} 行")
            
        # 0. 日期过滤 (新增)
        if start_date and end_date:
            print(f"📅 [render_channel_detail] 应用日期过滤: {start_date} - {end_date}")
            # 统一日期列名
            date_col = '日期' if '日期' in df.columns else '下单时间'
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col])
                mask = (df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))
                df = df.loc[mask]
                print(f"   ✅ 过滤后数据量: {len(df)} 行")
            else:
                print(f"   ⚠️ 无法过滤日期: 缺少日期字段")
        
        # ===== 关键修复: 使用与主看板完全一致的计算流程 =====
        # 1. 先对全局数据进行订单聚合(与主看板Tab1一致)
        print(f"📊 [Step 1] 对全局数据进行订单聚合...", flush=True)
        print(f"   🔍 df行数: {len(df)}, 订单数: {df['订单ID'].nunique()}", flush=True)
        
        try:
            order_agg = calculate_order_metrics(df, calc_mode='all_no_fallback')
            print(f"   ✅ calculate_order_metrics执行成功", flush=True)
            print(f"   ✅ 全局order_agg: {len(order_agg)} 订单", flush=True)
            print(f"   🔍 order_agg类型: {type(order_agg)}", flush=True)
            print(f"   🔍 order_agg.empty: {order_agg.empty if hasattr(order_agg, 'empty') else 'N/A'}", flush=True)
        except Exception as e:
            print(f"   ❌ calculate_order_metrics执行失败: {e}", flush=True)
            import traceback
            traceback.print_exc()
            raise
        
        # 2. 确保order_agg包含渠道字段
        print(f"📊 [Step 2] 检查渠道字段...", flush=True)
        print(f"   🔍 order_agg.columns: {list(order_agg.columns)}", flush=True)
        
        if '渠道' not in order_agg.columns:
            print(f"   ⚠️ order_agg缺少渠道字段,从原始数据合并...", flush=True)
            order_channel = df.groupby('订单ID')['渠道'].first().reset_index()
            order_channel['订单ID'] = order_channel['订单ID'].astype(str)
            order_agg['订单ID'] = order_agg['订单ID'].astype(str)
            order_agg = order_agg.merge(order_channel, on='订单ID', how='left')
            print(f"   ✅ 合并后order_agg: {len(order_agg)} 订单", flush=True)
        else:
            print(f"   ✅ order_agg已包含渠道字段", flush=True)
        
        # 3. 过滤排除的渠道(与主看板_create_channel_comparison_cards一致)
        print(f"📊 [Step 3] 过滤排除渠道...", flush=True)
        excluded_channels = ['收银机订单', '闪购小程序'] + CHANNELS_TO_REMOVE
        print(f"   🔍 excluded_channels: {excluded_channels}", flush=True)
        
        order_agg_filtered = order_agg[~order_agg['渠道'].isin(excluded_channels)].copy()
        print(f"   ✅ 过滤后order_agg: {len(order_agg_filtered)} 订单", flush=True)
        
        # 4. 提取目标渠道的订单数据
        print(f"📊 [Step 4] 提取渠道'{channel_name}'的数据...", flush=True)
        channel_order_agg = order_agg_filtered[order_agg_filtered['渠道'] == channel_name].copy()
        print(f"   ✅ {channel_name}订单数: {len(channel_order_agg)}", flush=True)
        
        # ✅ 关键修复: 应用与主看板一致的收费渠道过滤逻辑
        # 必须剔除"平台服务费=0"的订单(异常订单)
        if channel_name in PLATFORM_FEE_CHANNELS:
            print(f"   🔍 应用收费渠道过滤逻辑 (剔除服务费<=0)...", flush=True)
            original_count = len(channel_order_agg)
            channel_order_agg = channel_order_agg[channel_order_agg.get('平台服务费', 0) > 0].copy()
            filtered_count = len(channel_order_agg)
            print(f"   ✅ 过滤完成: {original_count} → {filtered_count} (剔除 {original_count - filtered_count} 单)", flush=True)
        
        if channel_order_agg.empty:
            print(f"⚠️ [render_channel_detail] {channel_name} 无订单数据", flush=True)
            return dbc.Alert(f"⚠️ {channel_name} 暂无数据", color="warning")
        
        # 5. 计算总体指标(基于channel_order_agg)
        print(f"📊 [Step 5] 计算总体指标...", flush=True)
        
        try:
            total_orders = len(channel_order_agg)
            print(f"   🔍 Step 5.1: total_orders = {total_orders}", flush=True)
            
            # 🔍 调试: 打印channel_order_agg的关键字段
            print(f"   🔍 Step 5.2: 检查字段...", flush=True)
            print(f"   🔍 channel_order_agg字段: {list(channel_order_agg.columns)}", flush=True)
            
            if '订单实际利润' in channel_order_agg.columns:
                print(f"   🔍 订单实际利润字段存在: ✅", flush=True)
                print(f"   🔍 订单实际利润前5行: {channel_order_agg['订单实际利润'].head().tolist()}", flush=True)
                print(f"   🔍 订单实际利润sum: {channel_order_agg['订单实际利润'].sum()}", flush=True)
            else:
                print(f"   ❌ 订单实际利润字段不存在!", flush=True)
                raise ValueError("订单实际利润字段不存在")
            
            # 使用实收价格(如果有)或商品实售价
            print(f"   🔍 Step 5.3: 计算销售额...", flush=True)
            if '实收价格' in channel_order_agg.columns:
                total_sales = channel_order_agg['实收价格'].sum()
                print(f"   🔍 使用'实收价格'字段: {total_sales}", flush=True)
            else:
                total_sales = channel_order_agg['商品实售价'].sum()
                print(f"   🔍 使用'商品实售价'字段: {total_sales}", flush=True)
            
            print(f"   🔍 Step 5.4: 计算利润额...", flush=True)
            total_profit = channel_order_agg['订单实际利润'].sum()
            print(f"   🔍 total_profit = {total_profit}", flush=True)
            
            print(f"   🔍 Step 5.5: 计算利润率...", flush=True)
            profit_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
            avg_order_value = total_sales / total_orders if total_orders > 0 else 0
            
            print(f"   ✅ 订单数: {total_orders:,}", flush=True)
            print(f"   ✅ 销售额: ¥{total_sales:,.2f}", flush=True)
            print(f"   ✅ 利润额(total_profit变量): ¥{total_profit:,.2f}", flush=True)
            print(f"   ✅ 利润率: {profit_rate:.2f}%", flush=True)
            print(f"   🔍 验证: total_profit类型={type(total_profit)}, 值={total_profit}", flush=True)
            print(f"{'='*60}\n", flush=True)
            
            # 5.5 计算成本结构 (新增: Phase 1.3)
            print(f"📊 [Step 5.5] 计算成本结构...", flush=True)
            
            # (1) 商品成本
            cost_field = '商品采购成本' if '商品采购成本' in channel_order_agg.columns else '成本'
            total_product_cost = channel_order_agg[cost_field].sum() if cost_field in channel_order_agg.columns else 0
            
            # (2) 配送成本 (配送净成本)
            # 权威公式: 配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返
            delivery_fee = channel_order_agg['物流配送费'].sum() if '物流配送费' in channel_order_agg.columns else 0
            user_paid_delivery = channel_order_agg['用户支付配送费'].sum() if '用户支付配送费' in channel_order_agg.columns else 0
            delivery_discount = channel_order_agg['配送费减免金额'].sum() if '配送费减免金额' in channel_order_agg.columns else 0
            rebate = channel_order_agg['企客后返'].sum() if '企客后返' in channel_order_agg.columns else 0
            
            total_delivery_cost = delivery_fee - (user_paid_delivery - delivery_discount) - rebate
            
            # (3) 营销成本 (各项补贴之和)
            marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', 
                               '满赠金额', '商家其他优惠', '新客减免金额']
            total_marketing_cost = 0
            for field in marketing_fields:
                if field in channel_order_agg.columns:
                    total_marketing_cost += channel_order_agg[field].sum()
            
            # (4) 平台成本 (佣金+服务费)
            total_platform_cost = 0
            if '平台佣金' in channel_order_agg.columns:
                total_platform_cost += channel_order_agg['平台佣金'].sum()
            if '平台服务费' in channel_order_agg.columns:
                total_platform_cost += channel_order_agg['平台服务费'].sum()
                
            # 计算占比 (分母为销售额)
            base_sales = total_sales if total_sales > 0 else 1  # 避免除以0
            
            product_cost_rate = (total_product_cost / base_sales) * 100
            delivery_cost_rate = (total_delivery_cost / base_sales) * 100
            marketing_cost_rate = (total_marketing_cost / base_sales) * 100
            platform_cost_rate = (total_platform_cost / base_sales) * 100
            
            print(f"   📦 商品成本: ¥{total_product_cost:,.0f} ({product_cost_rate:.1f}%)")
            print(f"   🚚 配送成本: ¥{total_delivery_cost:,.0f} ({delivery_cost_rate:.1f}%)")
            print(f"   🎁 营销成本: ¥{total_marketing_cost:,.0f} ({marketing_cost_rate:.1f}%)")
            print(f"   💼 平台成本: ¥{total_platform_cost:,.0f} ({platform_cost_rate:.1f}%)")
            
        except Exception as e:
            print(f"   ❌ Step 5计算失败: {e}", flush=True)
            import traceback
            traceback.print_exc()
            raise
        
        # 6. 计算趋势数据 (重构: 多指标叠加)
        print(f"📊 [Step 6] 计算趋势数据 (多指标)...")
        
        # 先筛选该渠道的原始数据用于获取日期
        channel_data = df[df['渠道'] == channel_name].copy()
        
        if '日期' not in channel_data.columns and '下单时间' not in channel_data.columns:
            trend_chart = dbc.Alert("⚠️ 数据中缺少日期字段,无法显示趋势图", color="warning")
        else:
            # 统一使用日期字段
            date_col = '日期' if '日期' in channel_data.columns else '下单时间'
            channel_data['日期'] = pd.to_datetime(channel_data[date_col])
            
            # 创建订单ID到日期的映射
            order_date_map = channel_data.groupby('订单ID')['日期'].first()
            
            # 给channel_order_agg添加日期字段
            order_agg_with_date = channel_order_agg.copy()
            order_agg_with_date['订单ID'] = order_agg_with_date['订单ID'].astype(str)
            order_date_map.index = order_date_map.index.astype(str)
            order_agg_with_date['日期'] = order_agg_with_date['订单ID'].map(order_date_map)
            
            # 准备聚合字典
            agg_dict = {
                '订单实际利润': 'sum',
                '实收价格' if '实收价格' in order_agg_with_date.columns else '商品实售价': 'sum',
                '订单ID': 'count',
                '物流配送费': 'sum',
                '用户支付配送费': 'sum',
                '配送费减免金额': 'sum',
                '企客后返': 'sum'
            }
            # 添加营销字段
            for field in marketing_fields:
                if field in order_agg_with_date.columns:
                    agg_dict[field] = 'sum'
            
            # 按日期聚合
            daily_data = order_agg_with_date.groupby(order_agg_with_date['日期'].dt.date).agg(agg_dict).reset_index()
            daily_data.rename(columns={
                '订单实际利润': '利润额',
                '实收价格' if '实收价格' in order_agg_with_date.columns else '商品实售价': '销售额',
                '订单ID': '订单数'
            }, inplace=True)
            
            # 计算衍生指标
            daily_data['总营销'] = 0
            for field in marketing_fields:
                if field in daily_data.columns:
                    daily_data['总营销'] += daily_data[field]
            
            # 权威公式: 配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返
            daily_data['配送净成本'] = daily_data['物流配送费'] - (daily_data['用户支付配送费'] - daily_data['配送费减免金额']) - daily_data['企客后返']
            
            daily_data['利润率'] = (daily_data['利润额'] / daily_data['销售额'] * 100).fillna(0).round(2)
            daily_data['单均营销'] = (daily_data['总营销'] / daily_data['订单数']).fillna(0).round(2)
            daily_data['单均配送'] = (daily_data['配送净成本'] / daily_data['订单数']).fillna(0).round(2)
            daily_data['客单价'] = (daily_data['销售额'] / daily_data['订单数']).fillna(0).round(2)
            
            # 生成双轴图
            trend_chart = create_dual_axis_chart(
                data=daily_data,
                x_field='日期',
                bar_fields=['销售额'],
                line_fields=['利润率', '单均营销', '单均配送'],
                title='渠道经营健康度诊断 (销售额 vs 利润/成本)',
                bar_names=['销售额'],
                line_names=['利润率(%)', '单均营销(¥)', '单均配送(¥)']
            )
        
        # 7. 计算红黑榜 (Top 5 盈利 vs Top 5 亏损)
        print(f"📊 [Step 7] 计算红黑榜商品...")
        
        # 🧹 [展示优化] 剔除耗材 (仅在展示列表中剔除,不影响上层计算)
        top_products_data = channel_data.copy()
        category_col = None
        for col_name in ['一级分类名', '美团一级分类', '一级分类']:
            if col_name in top_products_data.columns:
                category_col = col_name
                break
        
        if category_col:
            top_products_data = top_products_data[top_products_data[category_col] != '耗材']

        # 聚合计算
        product_ranks = top_products_data.groupby('商品名称').agg({
            '商品实售价': 'sum',
            '商品采购成本': 'sum' if '商品采购成本' in top_products_data.columns else lambda x: 0,
            '订单ID': 'nunique'
        }).reset_index()
        
        product_ranks['利润额'] = product_ranks['商品实售价'] - product_ranks['商品采购成本']
        product_ranks['毛利率'] = (product_ranks['利润额'] / product_ranks['商品实售价'] * 100).fillna(0).round(1)
        
        # 红榜: 利润最高的5个
        red_list = product_ranks.sort_values('利润额', ascending=False).head(5)
        
        # 黑榜: 利润最低的5个 (优先展示亏损的)
        black_list = product_ranks.sort_values('利润额', ascending=True).head(5)
        
        print(f"   ✅ 红黑榜计算完成", flush=True)
        
        # 7.5 构建成本结构卡片 (新增: Phase 1.3)
        print(f"📊 [Step 5.5] 构建成本结构UI...")
        
        def create_cost_row(label, value, rate, icon, color, filter_type=None):
            """创建单行成本进度条"""
            return html.Div([
                html.Div([
                    html.Span([html.Span(icon, className="me-2"), label]),
                    html.Span([
                        f"¥{value:,.0f}",
                        html.Span(f" ({rate:.1f}%)", className="ms-2 text-muted")
                    ], className="float-end")
                ], className="mb-1 d-flex justify-content-between align-items-center"),
                
                dbc.Progress(value=rate, color=color, style={'height': '12px'}, className="mb-2"),
                
                # 下钻链接 (如果有filter_type)
                html.Div([
                    dbc.Button(
                        "点击查看详情 →", 
                        id={'type': 'cost-drill-btn', 'channel': channel_name, 'filter': filter_type},
                        color="link", 
                        size="sm",
                        className="p-0 text-decoration-none",
                        style={'fontSize': '0.85rem'}
                    )
                ], className="text-end mb-3") if filter_type else html.Div(className="mb-3")
            ])

        cost_structure_card = dbc.Card([
            dbc.CardHeader("💰 成本结构分解"),
            dbc.CardBody([
                create_cost_row("商品成本", total_product_cost, product_cost_rate, "📦", "danger", "low-margin"),
                create_cost_row("配送成本", total_delivery_cost, delivery_cost_rate, "🚚", "warning", "delivery-issues"),
                create_cost_row("营销成本", total_marketing_cost, marketing_cost_rate, "🎁", "info", "discount-products"),
                # 平台成本已移除 (不可控成本)
            ])
        ], className="mb-4")
        
        # 8. 构建UI
        print(f"📊 [Step 6] 构建UI...", flush=True)
        print(f"   🔍 准备渲染,total_profit={total_profit}", flush=True)
        
        ui_content = html.Div([
            # 页面标题
            html.H4(f"🔍 {channel_name} - 深度分析", className="mb-3"),
            
            # 总体指标卡片
            dbc.Row([
                dbc.Col([
                    create_stat_card(
                        title="销售额",
                        value=f"¥{total_sales:,.0f}",
                        subtitle="实收价格",
                        icon="💰",
                        value_color="primary"
                    )
                ], width=3),
                dbc.Col([
                    create_stat_card(
                        title="订单数",
                        value=f"{total_orders:,}",
                        subtitle="笔",
                        icon="📦",
                        value_color="success"
                    )
                ], width=3),
                dbc.Col([
                    create_stat_card(
                        title="利润额",
                        value=f"¥{total_profit:,.0f}",
                        subtitle="订单实际利润",
                        icon="💵",
                        value_color="info"
                    )
                ], width=3),
                dbc.Col([
                    create_stat_card(
                        title="利润率",
                        value=f"{profit_rate:.1f}%",
                        subtitle="利润/销售额",
                        icon="📊",
                        value_color="warning"
                    )
                ], width=3),
            ], className="mb-4"),
            
            # 趋势图 (重构)
            dbc.Card([
                dbc.CardHeader([
                    html.Span("📈 渠道经营健康度诊断"),
                    html.Span(" (销售额 vs 利润/成本)", className="text-muted small ms-2")
                ]),
                dbc.CardBody([
                    trend_chart if not isinstance(trend_chart, dbc.Alert) else trend_chart
                ])
            ], className="mb-4"),
            
            # 成本结构分解 (新增)
            cost_structure_card,
            
            # 红黑榜区域 (替代原TOP10)
            dbc.Row([
                # 红榜
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🏆 红榜: 利润贡献 Top 5", className="text-success fw-bold"),
                        dbc.CardBody([
                            dbc.Table([
                                html.Thead(html.Tr([
                                    html.Th("商品"),
                                    html.Th("利润", style={'textAlign': 'right'}),
                                    html.Th("操作", style={'textAlign': 'center'})
                                ])),
                                html.Tbody([
                                    html.Tr([
                                        html.Td([
                                            html.Div(row['商品名称'], className="text-truncate", style={'maxWidth': '150px'}, title=row['商品名称']),
                                            html.Small(f"销量: {row['订单ID']}", className="text-muted")
                                        ]),
                                        html.Td(f"¥{row['利润额']:,.0f}", style={'textAlign': 'right', 'color': '#28a745', 'fontWeight': 'bold'}),
                                        html.Td(
                                            dbc.Button("分析", size="sm", color="success", outline=True, 
                                                     id={'type': 'product-drill-btn', 'channel': channel_name, 'product': row['商品名称']}),
                                            style={'textAlign': 'center'}
                                        )
                                    ]) for _, row in red_list.iterrows()
                                ])
                            ], size="sm", borderless=True, hover=True)
                        ])
                    ], className="h-100 border-success shadow-sm")
                ], width=6),
                
                # 黑榜
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("⚠️ 黑榜: 亏损严重 Top 5", className="text-danger fw-bold"),
                        dbc.CardBody([
                            dbc.Table([
                                html.Thead(html.Tr([
                                    html.Th("商品"),
                                    html.Th("亏损", style={'textAlign': 'right'}),
                                    html.Th("操作", style={'textAlign': 'center'})
                                ])),
                                html.Tbody([
                                    html.Tr([
                                        html.Td([
                                            html.Div(row['商品名称'], className="text-truncate", style={'maxWidth': '150px'}, title=row['商品名称']),
                                            html.Small(f"销量: {row['订单ID']}", className="text-muted")
                                        ]),
                                        html.Td(f"¥{row['利润额']:,.0f}", style={'textAlign': 'right', 'color': '#dc3545', 'fontWeight': 'bold'}),
                                        html.Td(
                                            dbc.Button("分析", size="sm", color="danger", outline=True,
                                                     id={'type': 'product-drill-btn', 'channel': channel_name, 'product': row['商品名称']}),
                                            style={'textAlign': 'center'}
                                        )
                                    ]) for _, row in black_list.iterrows()
                                ])
                            ], size="sm", borderless=True, hover=True)
                        ])
                    ], className="h-100 border-danger shadow-sm")
                ], width=6)
            ], className="mb-4"),
            
            # 说明文字
            html.Div([
                html.Hr(className="my-4"),
                html.P([
                    html.Strong("💡 数据说明: "),
                    "所有指标使用与主看板Tab1完全一致的计算逻辑,包括渠道过滤和订单实际利润计算公式。"
                ], className="text-muted small")
            ])
        ])
        
        print(f"   ✅ UI构建完成", flush=True)
        print(f"   🔍 返回ui_content", flush=True)
        return ui_content
        
    except Exception as e:
        print(f"❌ [渠道详情] 渲染失败: {e}", flush=True)
        import traceback
        traceback.print_exc()
        
        return dbc.Alert([
            html.H4(f"🔍 {channel_name} - 深度分析", className="alert-heading"),
            html.Hr(),
            html.P(f"⚠️ 加载失败: {str(e)}", className="text-danger small"),
            html.Hr(),
            html.Pre(traceback.format_exc(), className="small")
        ], color="danger")


def render_product_list(channel_name, filter_type):
    """
    渲染第3层: 专项分析页面 (重构版 - 场景化视图)
    
    根据 filter_type 展示不同的分析视图:
    1. low-margin: 低毛利分析 (关注 成本 vs 售价)
    2. discount-products: 营销成本分析 (关注 营销构成 vs 效率)
    3. delivery-issues: 配送成本分析 (关注 距离 vs 成本 vs 利润)
    """
    try:
        import pandas as pd
        import numpy as np
        from dash import dash_table
        import plotly.express as px
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        from dash import dcc
        
        print(f"\n{'='*60}")
        print(f"🔍 [render_product_list] 开始渲染专项分析")
        print(f"   渠道: {channel_name}")
        print(f"   分析主题: {filter_type}")
        
        # 1. 获取数据
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return dbc.Alert("⚠️ 暂无数据", color="warning")
            
        # 2. 数据预处理
        if not channel_name:
             return dbc.Alert("⚠️ 错误: 渠道信息丢失", color="danger")

        df = GLOBAL_DATA[GLOBAL_DATA['渠道'] == channel_name].copy()
        if df.empty:
            return dbc.Alert(f"⚠️ {channel_name} 无数据", color="warning")

        # 🧹 [展示优化] 剔除耗材
        category_col = None
        for col_name in ['一级分类名', '美团一级分类', '一级分类']:
            if col_name in df.columns:
                category_col = col_name
                break
        
        if category_col:
            df = df[df[category_col] != '耗材'].copy()
            
        # 预处理数值列
        numeric_cols = ['实收价格', '利润额', '商品采购成本', '商品原价', '物流配送费', '配送距离', '用户支付配送费', '企客后返']
        marketing_fields = ['满减金额', '商品减免金额', '商家代金券', '商家承担部分券', 
                           '满赠金额', '商家其他优惠', '新客减免金额', '配送费减免金额']
        
        all_cols = numeric_cols + marketing_fields
        for col in all_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0.0 # 缺失字段补0
            
        # 检查关键字段
        if '利润额' not in df.columns:
            df['利润额'] = df['实收价格'] - df.get('商品采购成本', 0)

        # 4. 根据场景构建视图
        print(f"📊 [Step 2] 构建场景视图: {filter_type}")
        
        view_title = "专项分析"
        view_desc = ""
        chart_component = None
        table_component = None
        time_chart_component = None  # ✅ 初始化变量，防止UnboundLocalError
        
        if filter_type == 'low-margin':
            # === 场景1: 商品成本分析 (重构: 销量-毛利矩阵) ===
            view_title = "📉 商品成本与角色分析"
            view_desc = "基于'销量-毛利'矩阵，识别商品的引流能力与盈利能力，辅助淘汰与选品决策。"
            
            # 聚合
            agg_rules = {
                '订单ID': 'nunique',
                '利润额': 'sum',
                '实收价格': 'sum',
                '商品采购成本': 'sum' if '商品采购成本' in df.columns else lambda x: 0
            }
            product_agg = df.groupby('商品名称').agg(agg_rules).reset_index()
            product_agg = product_agg.rename(columns={'订单ID': '销量', '利润额': '总利润', '实收价格': '销售额', '商品采购成本': '总成本'})
            product_agg['毛利率'] = (product_agg['总利润'] / product_agg['销售额'] * 100).fillna(0).round(1)
            
            # 计算中位数作为动态阈值
            median_sales = product_agg['销量'].median()
            if median_sales < 5: median_sales = 5 # 设定最低门槛
            
            # 定义象限角色
            def get_quadrant(row):
                if row['毛利率'] >= 15:
                    return '⭐️ 明星商品' if row['销量'] >= median_sales else '💎 潜力商品'
                else:
                    return '🔥 引流商品' if row['销量'] >= median_sales else '🗑️ 滞销亏损'

            product_agg['角色'] = product_agg.apply(get_quadrant, axis=1)
            
            # 图表: 销量-毛利矩阵 (散点图)
            fig = px.scatter(
                product_agg, 
                x='销量', 
                y='毛利率', 
                size='销售额',
                color='角色',
                hover_name='商品名称',
                hover_data=['销售额', '总利润'],
                color_discrete_map={
                    '⭐️ 明星商品': '#2ecc71', # Green
                    '🔥 引流商品': '#f1c40f', # Yellow
                    '💎 潜力商品': '#3498db', # Blue
                    '🗑️ 滞销亏损': '#e74c3c'  # Red
                },
                title=f'商品角色矩阵 (销量中位数: {median_sales})'
            )
            
            # 添加辅助线
            fig.add_hline(y=15, line_dash="dash", line_color="gray", annotation_text="毛利及格线 (15%)")
            fig.add_vline(x=median_sales, line_dash="dash", line_color="gray", annotation_text="销量中位数")
            
            chart_component = dcc.Graph(figure=fig)
            
            # 表格: 增加建议列
            def get_suggestion(role):
                if role == '⭐️ 明星商品': return '✅ 维持现状, 确保存货'
                if role == '🔥 引流商品': return '⚠️ 监控连带率, 适当提价'
                if role == '💎 潜力商品': return '🚀 增加曝光, 参与活动'
                return '❌ 建议下架或清仓'

            product_agg['建议策略'] = product_agg['角色'].apply(get_suggestion)
            
            # 排序: 优先展示滞销亏损
            product_agg['sort_key'] = product_agg['角色'].map({'🗑️ 滞销亏损': 0, '🔥 引流商品': 1, '💎 潜力商品': 2, '⭐️ 明星商品': 3})
            product_agg = product_agg.sort_values('sort_key')
            
            # 添加操作列
            product_agg['操作'] = '🔍 详情'
            
            table_component = dash_table.DataTable(
                id='product-list-table',
                data=product_agg.to_dict('records'),
                columns=[
                    {'name': '商品名称', 'id': '商品名称'},
                    {'name': '角色', 'id': '角色'},
                    {'name': '建议策略', 'id': '建议策略'},
                    {'name': '销量', 'id': '销量'},
                    {'name': '销售额', 'id': '销售额', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                    {'name': '毛利率(%)', 'id': '毛利率', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                    {'name': '操作', 'id': '操作'},
                ],
                style_data_conditional=[
                    {'if': {'filter_query': '{角色} = "🗑️ 滞销亏损"'}, 'backgroundColor': '#ffebee', 'color': '#c0392b'},
                    {'if': {'filter_query': '{角色} = "⭐️ 明星商品"'}, 'backgroundColor': '#e8f8f5', 'color': '#27ae60'},
                    {'if': {'column_id': '操作'}, 'cursor': 'pointer', 'color': '#3498db', 'fontWeight': 'bold'}
                ],
                sort_action='native',
                page_size=15,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '10px'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            )
            
        elif filter_type == 'discount-products':
            # === 场景2: 营销成本分析 (重构: 效率与门槛分析) ===
            view_title = "🎁 营销效率与门槛分析"
            view_desc = "分析营销活动的投入产出比(ROI)，识别无效补贴与门槛设置问题。"
            
            # 1. 预先聚合为订单级数据
            order_agg_rules = {
                '满减金额': 'first',
                '新客减免金额': 'first',
                '配送费减免金额': 'first',
                '商家代金券': 'first',
                '商家承担部分券': 'first',
                '满赠金额': 'first',
                '商家其他优惠': 'first',
                '商品减免金额': 'first',
                '实收价格': 'sum',
                '利润额': 'sum',
                '商品采购成本': 'sum'
            }
            
            # 确保所有字段存在
            for field in order_agg_rules.keys():
                if field not in df.columns:
                    df[field] = 0
            
            order_df = df.groupby('订单ID').agg(order_agg_rules).reset_index()
            
            # 计算总营销成本
            marketing_cols = ['满减金额', '新客减免金额', '配送费减免金额', '商家代金券', 
                             '商家承担部分券', '满赠金额', '商家其他优惠', '商品减免金额']
            order_df['总营销成本'] = order_df[marketing_cols].sum(axis=1)
            
            # 2. 图表: 订单利润分布 (散点图)
            # 识别"负毛利订单" (羊毛党)
            order_df['订单类型'] = order_df.apply(lambda x: '🔴 亏损订单' if x['利润额'] < 0 else ('🟡 低利订单' if x['利润额'] < 5 else '🟢 正常订单'), axis=1)
            
            fig = px.scatter(
                order_df,
                x='实收价格',
                y='利润额',
                color='订单类型',
                size='总营销成本',
                hover_data=['总营销成本'],
                color_discrete_map={'🔴 亏损订单': '#e74c3c', '🟡 低利订单': '#f1c40f', '🟢 正常订单': '#2ecc71'},
                title='订单利润分布 (气泡大小=营销成本)'
            )
            fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="盈亏平衡线")
            
            chart_component = dcc.Graph(figure=fig)
            
            # 3. 表格: 营销活动ROI分析
            # 汇总各项活动的 支出、带来GMV(估算)、带来利润
            roi_data = []
            total_gmv = order_df['实收价格'].sum()
            total_profit = order_df['利润额'].sum()
            
            for m_type in marketing_cols:
                # 筛选出参与了该活动的订单
                active_orders = order_df[order_df[m_type] > 0]
                if not active_orders.empty:
                    cost = active_orders[m_type].sum()
                    gmv = active_orders['实收价格'].sum()
                    profit = active_orders['利润额'].sum()
                    roi = gmv / cost if cost > 0 else 0
                    
                    roi_data.append({
                        '营销活动': m_type,
                        '涉及订单数': len(active_orders),
                        '总支出': cost,
                        '关联GMV': gmv,
                        '关联利润': profit,
                        'ROI (GMV/支出)': roi
                    })
            
            roi_df = pd.DataFrame(roi_data).sort_values('总支出', ascending=False)
            
            # 添加操作列
            roi_df['操作'] = '🔍 详情'
            
            if not roi_df.empty:
                table_component = dash_table.DataTable(
                    id='product-list-table', # ✅ 修复: 添加ID以支持点击事件
                    data=roi_df.to_dict('records'),
                    columns=[
                        {'name': '营销活动', 'id': '营销活动'},
                        {'name': '涉及订单数', 'id': '涉及订单数'},
                        {'name': '总支出', 'id': '总支出', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                        {'name': '关联GMV', 'id': '关联GMV', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                        {'name': '关联利润', 'id': '关联利润', 'type': 'numeric', 'format': {'specifier': ',.0f'}},
                        {'name': 'ROI', 'id': 'ROI (GMV/支出)', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                        {'name': '操作', 'id': '操作'}, # ✅ 新增: 操作列
                    ],
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                    style_data_conditional=[
                        {'if': {'filter_query': '{关联利润} < 0', 'column_id': '关联利润'}, 'color': 'red', 'fontWeight': 'bold'},
                        {'if': {'column_id': '操作'}, 'cursor': 'pointer', 'color': '#3498db', 'fontWeight': 'bold'}
                    ],
                    sort_action='native', # ✅ 新增: 支持排序
                    page_size=15 # ✅ 新增: 支持分页
                )
            else:
                table_component = dbc.Alert("本期无营销活动支出", color="info")
            
        elif filter_type == 'delivery-issues':
            # === 场景3: 配送成本分析 (重构: 距离分段分析) ===
            view_title = "🚚 配送成本与距离分析"
            view_desc = "按配送距离分段分析订单的盈利能力，识别运费倒挂的距离区间。"
            
            # 1. 检查距离字段
            if '配送距离' not in df.columns:
                return dbc.Alert([
                    html.H5("⚠️ 缺少配送距离数据", className="alert-heading"),
                    html.P("当前数据源中未包含'配送距离'字段，无法进行距离分段分析。"),
                ], color="danger")
            
            # 允许距离为0的情况(可能是数据缺失或确实很近),但给出提示
            warning_component = None
            if df['配送距离'].sum() == 0:
                warning_component = dbc.Alert("⚠️ 警告: 所有订单的配送距离均为0，分析结果可能不准确 (请检查数据源是否包含有效距离信息)", color="warning")
            
            # 1.5 智能单位转换 (米 -> 公里)
            # 如果平均距离 > 100, 很有可能是米为单位
            if df['配送距离'].mean() > 100:
                print("⚠️ 检测到配送距离单位可能是米，自动转换为公里")
                df['配送距离'] = df['配送距离'] / 1000
            
            # 2. 距离分箱
            bins = [0, 1, 2, 3, 4, 5, 100]
            labels = ['0-1km', '1-2km', '2-3km', '3-4km', '4-5km', '5km+']
            df['距离分段'] = pd.cut(df['配送距离'], bins=bins, labels=labels, right=False)
            
            # 1.8 预先聚合为订单级数据 (关键修复: 避免多商品订单导致运费重复计算)
            # 必须先按订单聚合，再按维度(距离/时段)聚合
            
            # 确保有小时字段
            date_col = next((col for col in ['下单时间', '日期', 'time'] if col in df.columns), None)
            if date_col:
                df['hour'] = pd.to_datetime(df[date_col]).dt.hour
            else:
                df['hour'] = 0

            # 定义聚合规则
            order_agg_rules = {
                '物流配送费': 'first',
                '用户支付配送费': 'first',
                '配送费减免金额': 'first',
                '配送距离': 'first',
                '距离分段': 'first',
                'hour': 'first',
                '利润额': 'sum',
                '企客后返': 'sum',
                '实收价格': 'sum'
            }
            
            # 执行订单级聚合
            order_df = df.groupby('订单ID').agg(order_agg_rules).reset_index()
            
            # 3. 聚合计算 (基于订单级数据)
            dist_agg_rules = {
                '订单ID': 'count',
                '实收价格': 'sum',
                '利润额': 'sum',
                '物流配送费': 'sum',
                '用户支付配送费': 'sum',
                '配送费减免金额': 'sum',
                '企客后返': 'sum',
                '配送距离': 'mean'
            }
            dist_agg = order_df.groupby('距离分段').agg(dist_agg_rules).reset_index()
            
            # 4. 计算衍生指标
            # 权威公式: 配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返
            dist_agg['配送净成本'] = dist_agg['物流配送费'] - (dist_agg['用户支付配送费'] - dist_agg['配送费减免金额']) - dist_agg['企客后返']
            
            dist_agg = dist_agg.rename(columns={'订单ID': '订单数', '实收价格': '销售额', '利润额': '总利润', '配送距离': '平均距离'})
            dist_agg['客单价'] = (dist_agg['销售额'] / dist_agg['订单数']).fillna(0).round(1)
            dist_agg['单均利润'] = (dist_agg['总利润'] / dist_agg['订单数']).fillna(0).round(2)
            dist_agg['单均配送'] = (dist_agg['配送净成本'] / dist_agg['订单数']).fillna(0).round(2)
            dist_agg['利润率'] = (dist_agg['总利润'] / dist_agg['销售额'] * 100).fillna(0).round(1)
            
            # 过滤无数据分段 (如果全是0, 0-1km会有数据)
            dist_agg = dist_agg[dist_agg['订单数'] > 0].copy()
            
            # 5. 图表: 双轴组合图 (柱状图=订单量, 折线图=成本/利润)
            # 相比气泡图，双轴图能更清晰地展示"量"与"利"的背离关系
            fig = go.Figure()
            
            # 左轴: 订单量 (柱状图)
            fig.add_trace(go.Bar(
                x=dist_agg['距离分段'],
                y=dist_agg['订单数'],
                name='订单量',
                marker_color='rgba(55, 83, 109, 0.5)',
                yaxis='y'
            ))
            
            # 右轴: 单均配送成本 (折线图)
            fig.add_trace(go.Scatter(
                x=dist_agg['距离分段'],
                y=dist_agg['单均配送'],
                name='单均配送成本',
                mode='lines+markers',
                line=dict(color='#d62728', width=3), # 红色示警
                yaxis='y2'
            ))
            
            # 右轴: 单均利润 (折线图)
            fig.add_trace(go.Scatter(
                x=dist_agg['距离分段'],
                y=dist_agg['单均利润'],
                name='单均利润',
                mode='lines+markers',
                line=dict(color='#2ca02c', width=3), # 绿色代表利润
                yaxis='y2'
            ))
            
            # 布局设置
            fig.update_layout(
                title='配送距离分析: 订单量 vs 成本 vs 利润',
                xaxis=dict(title='配送距离分段'),
                yaxis=dict(
                    title='订单量', 
                    side='left', 
                    showgrid=False
                ),
                yaxis2=dict(
                    title='金额 (元)', 
                    side='right', 
                    overlaying='y', 
                    showgrid=True,
                    zeroline=True,
                    zerolinecolor='rgba(0,0,0,0.2)'
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                hovermode='x unified',
                margin=dict(l=50, r=50, t=80, b=50)
            )
            
            # 添加盈亏平衡线 (0元线)
            fig.add_hline(y=0, line_dash="dash", line_color="gray", yref="y2")
            
            chart_component = html.Div([
                warning_component if warning_component else None,
                dcc.Graph(figure=fig)
            ])
            
            # === 新增: 时段分析 (Time Analysis) ===
            # 1. 提取小时
            time_chart_component = None
            
            if date_col:
                try:
                    # 2. 聚合计算 (基于订单级数据)
                    time_agg = order_df.groupby('hour').agg({
                        '订单ID': 'count',
                        '物流配送费': 'sum',
                        '利润额': 'sum',
                        '用户支付配送费': 'sum',
                        '配送费减免金额': 'sum',
                        '企客后返': 'sum'
                    }).reset_index()
                    
                    # 权威公式: 配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免金额) - 企客后返
                    time_agg['配送净成本'] = time_agg['物流配送费'] - (time_agg['用户支付配送费'] - time_agg['配送费减免金额']) - time_agg['企客后返']
                    
                    time_agg['单均配送'] = (time_agg['配送净成本'] / time_agg['订单ID']).round(2)
                    time_agg['单均利润'] = (time_agg['利润额'] / time_agg['订单ID']).round(2)
                    
                    # 3. 补全24小时数据 (确保X轴完整)
                    full_hours = pd.DataFrame({'hour': range(24)})
                    time_agg = pd.merge(full_hours, time_agg, on='hour', how='left').fillna(0)
                    
                    # 4. 绘制时段分析图
                    fig_time = go.Figure()
                    
                    # 柱状图: 订单量
                    fig_time.add_trace(go.Bar(
                        x=time_agg['hour'],
                        y=time_agg['订单ID'],
                        name='订单量',
                        marker_color='rgba(55, 83, 109, 0.5)',
                        yaxis='y'
                    ))
                    
                    # 折线图: 单均配送
                    fig_time.add_trace(go.Scatter(
                        x=time_agg['hour'],
                        y=time_agg['单均配送'],
                        name='单均配送成本',
                        mode='lines+markers',
                        line=dict(color='#d62728', width=2),
                        yaxis='y2'
                    ))
                    
                    # 折线图: 单均利润
                    fig_time.add_trace(go.Scatter(
                        x=time_agg['hour'],
                        y=time_agg['单均利润'],
                        name='单均利润',
                        mode='lines+markers',
                        line=dict(color='#2ca02c', width=2),
                        yaxis='y2'
                    ))
                    
                    fig_time.update_layout(
                        title='时段分析: 配送成本与利润随时间变化',
                        xaxis=dict(title='小时 (0-23)', tickmode='linear', tick0=0, dtick=1),
                        yaxis=dict(title='订单量', side='left', showgrid=False),
                        yaxis2=dict(title='金额 (元)', side='right', overlaying='y', showgrid=True, zeroline=True),
                        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
                        hovermode='x unified',
                        margin=dict(l=50, r=50, t=80, b=50)
                    )
                    
                    fig_time.add_hline(y=0, line_dash="dash", line_color="gray", yref="y2")
                    
                    time_chart_component = dbc.Card([
                        dbc.CardHeader("🕒 时段配送分析"),
                        dbc.CardBody(dcc.Graph(figure=fig_time))
                    ], className="mb-4")
                    
                except Exception as e:
                    print(f"⚠️ 时段分析计算失败: {e}")
            
            # 6. 表格
            table_component = dash_table.DataTable(
                data=dist_agg.to_dict('records'),
                columns=[
                    {'name': '距离分段', 'id': '距离分段'},
                    {'name': '订单数', 'id': '订单数'},
                    {'name': '客单价', 'id': '客单价', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                    {'name': '单均配送', 'id': '单均配送', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                    {'name': '单均利润', 'id': '单均利润', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                    {'name': '利润率(%)', 'id': '利润率', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                ],
                style_cell={'textAlign': 'left', 'padding': '10px'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{单均利润} < 0', 'column_id': '单均利润'},
                        'color': 'red', 'fontWeight': 'bold'
                    }
                ]
            )
            
        else:
            return dbc.Alert("未知的分析类型", color="danger")

        # 5. 构建UI
        print(f"   📊 准备构建UI: view_title={view_title}, filter_type={filter_type}", flush=True)
        print(f"   📊 组件状态: chart_component={chart_component is not None}, table_component={table_component is not None}", flush=True)
        
        # 手动构建子元素列表，避免 None 值导致的渲染问题
        content_children = []
        
        # 1. 标题栏
        header = dbc.Row([
            dbc.Col([
                html.H4(view_title, className="mb-1"),
                html.P(view_desc, className="text-muted small mb-0")
            ], width=8),
            dbc.Col([
                dbc.Button("📥 导出数据", id="btn-export-repricing", color="success", size="sm", className="me-2"),
                dcc.Download(id="download-repricing-list")
            ], width=4, className="text-end align-self-center")
        ], className="mb-4")
        content_children.append(header)
        
        # 2. 图表区域 (使用 html.Div 替代 dbc.Card 进行调试)
        chart_added = "No"
        if chart_component is not None:
            print("   👉 Adding Chart Container", flush=True)
            chart_added = "Yes"
            # 给组件添加ID，防止React渲染问题
            if hasattr(chart_component, 'id') and not chart_component.id:
                chart_component.id = f"chart-{filter_type}"
                
            chart_card = html.Div([
                html.Div("📊 图表区域", className="card-header bg-light fw-bold"),
                html.Div(chart_component, className="card-body", style={'minHeight': '300px'})
            ], className="card mb-4 shadow-sm", style={'border': '1px solid #dee2e6'})
            content_children.append(chart_card)
        else:
            print("   👉 Chart Component is None", flush=True)
            
        # 3. 时段图表 (仅配送分析)
        if filter_type == 'delivery-issues' and time_chart_component:
            content_children.append(time_chart_component)
            
        # 4. 数据表格 (使用 html.Div 替代 dbc.Card 进行调试)
        table_added = "No"
        if table_component is not None:
            print("   👉 Adding Table Container", flush=True)
            table_added = "Yes"
            table_card = html.Div([
                html.Div("📋 详细数据", className="card-header bg-light fw-bold"),
                html.Div(table_component, className="card-body")
            ], className="card mb-4 shadow-sm", style={'border': '1px solid #dee2e6'})
            content_children.append(table_card)
            
        # 🔧 调试信息 (移动到最后以获取准确的列表长度)
        debug_section = html.Div([
            html.Hr(),
            html.H6("🔧 调试信息 (Debug Info)", className="text-muted"),
            html.Div([
                html.Span(f"Filter: {filter_type} | ", className="me-2"),
                html.Span(f"Rows: {len(df)} | ", className="me-2"),
                html.Span(f"Chart: {type(chart_component).__name__} | ", className="me-2"),
                html.Span(f"Chart Added: {chart_added} | ", className="me-2"),
                html.Span(f"Table: {type(table_component).__name__} | ", className="me-2"),
                html.Span(f"Table Added: {table_added} | ", className="me-2"),
                html.Span(f"Children Count: {len(content_children)}", className="me-2"),
            ], className="small text-monospace text-muted")
        ], className="mt-4 p-3 bg-light rounded")
        
        # 5. 调试信息
        content_children.append(debug_section)
        
        ui_content = html.Div(content_children)
        
        print(f"   ✅ UI构建完成，准备返回 ui_content", flush=True)
        return ui_content
            
    except Exception as e:
        print(f"❌ [专项分析] 渲染失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"⚠️ 加载失败: {str(e)}", color="danger")


def render_product_insight(channel_name, product_name):
    """渲染第4层:单品深度洞察 (4大核心模块)"""
    try:
        import plotly.graph_objects as go
        import plotly.express as px
        from plotly.subplots import make_subplots
        from component_styles import create_stat_card
        
        print(f"\n{'='*60}")
        print(f"🔬 [render_product_insight] 开始渲染单品洞察: {product_name}")

        # 1. 获取基础数据
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return dbc.Alert("⚠️ 暂无数据", color="warning")
            
        # 筛选当前商品数据
        df = GLOBAL_DATA[(GLOBAL_DATA['渠道'] == channel_name) & (GLOBAL_DATA['商品名称'] == product_name)].copy()
        if df.empty:
            return dbc.Alert(f"⚠️ 未找到商品 {product_name} 的数据", color="warning")
            
        # 统一日期字段
        date_col = '日期' if '日期' in df.columns else '下单时间'
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col])
            df['Hour'] = df[date_col].dt.hour
            df['Date'] = df[date_col].dt.date
        
        # 确保数值列存在
        for col in ['实收价格', '利润额', '商品采购成本']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        if '利润额' not in df.columns:
             df['利润额'] = df['实收价格'] - df.get('商品采购成本', 0)

        # 计算核心指标
        total_sales = df['实收价格'].sum()
        total_profit = df['利润额'].sum()
        total_quantity = df['订单ID'].nunique()
        avg_price = total_sales / total_quantity if total_quantity > 0 else 0
        avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0

        # === 模块 D: 价格敏感度趋势 (Price Trend) ===
        # 按日聚合
        # 仅取最近30天数据，避免历史数据干扰趋势分析
        recent_df = df.sort_values('Date').tail(30 * 100) # 预筛选
        if not recent_df.empty:
             max_date = recent_df['Date'].max()
             min_date = max_date - pd.Timedelta(days=30)
             recent_df = recent_df[recent_df['Date'] >= min_date]
        else:
             recent_df = df.copy()

        daily_agg = recent_df.groupby('Date').agg({
            '订单ID': 'nunique',
            '实收价格': 'sum',
            '利润额': 'sum'
        }).reset_index()
        daily_agg['平均实收价'] = daily_agg['实收价格'] / daily_agg['订单ID']
        daily_agg = daily_agg.sort_values('Date')
        
        # ⚠️ 关键修复: 确保日期格式正确，防止Plotly自动缩放异常
        daily_agg['Date'] = pd.to_datetime(daily_agg['Date'])
        
        fig_price = make_subplots(specs=[[{"secondary_y": True}]])
        fig_price.add_trace(
            go.Bar(x=daily_agg['Date'], y=daily_agg['订单ID'], name="销量", marker_color='rgba(102, 126, 234, 0.6)'),
            secondary_y=False
        )
        fig_price.add_trace(
            go.Scatter(x=daily_agg['Date'], y=daily_agg['平均实收价'], name="平均单价", line=dict(color='#ff9900', width=2)),
            secondary_y=True
        )
        fig_price.update_layout(
            title="🏷️ 价格敏感度趋势 (销量 vs 单价)", 
            height=350, 
            margin=dict(l=20, r=20, t=40, b=20), 
            legend=dict(orientation="h", y=1.1),
            hovermode="x unified"
        )
        # 强制设置X轴格式，避免单点数据时显示微秒级刻度
        fig_price.update_xaxes(
            tickformat="%Y-%m-%d",
            dtick="D1"
        )
        fig_price.update_yaxes(title_text="销量", secondary_y=False)
        fig_price.update_yaxes(title_text="单价", secondary_y=True)

        # === 智能洞察分析 (AI Insights) ===
        # 1. 价格敏感度分析
        sensitivity_text = "数据不足，无法分析"
        sensitivity_color = "secondary"
        correlation = 0
        
        if len(daily_agg) > 3:
            # 计算价格与销量的相关性
            correlation = daily_agg['平均实收价'].corr(daily_agg['订单ID'])
            
            if correlation < -0.6:
                sensitivity_text = "高敏感 (价格上涨销量显著下降)"
                sensitivity_color = "danger"
            elif correlation < -0.3:
                sensitivity_text = "中等敏感 (价格对销量有一定影响)"
                sensitivity_color = "warning"
            else:
                sensitivity_text = "低敏感 (销量受价格影响较小)"
        
        # 2. 生成行动建议
        recommendations = []
        
        # 规则1: 负毛利预警
        if avg_margin < 0:
            recommendations.append({
                "title": "🛑 止损建议",
                "desc": "当前商品处于亏损状态，建议立即检查成本配置或提高售价。",
                "type": "danger"
            })
        
        # 规则2: 低毛利 + 低敏感 -> 涨价
        elif avg_margin < 15 and correlation > -0.3:
            recommendations.append({
                "title": "💰 涨价机会",
                "desc": "用户对价格不敏感且当前毛利较低，建议尝试提价 1-2 元以提升利润。",
                "type": "success"
            })
            
        # 规则3: 高毛利 + 高敏感 -> 促销
        elif avg_margin > 40 and correlation < -0.6:
            recommendations.append({
                "title": "📢 以价换量",
                "desc": "用户对价格高度敏感且毛利空间充足，可尝试短期促销活动拉动销量。",
                "type": "info"
            })
            
        if not recommendations:
            recommendations.append({
                "title": "✅ 维持现状",
                "desc": "当前商品表现平稳，建议继续保持当前策略。",
                "type": "secondary"
            })

        recommendation_ui = [
            dbc.Alert([
                html.H6(rec['title'], className="alert-heading"),
                html.P(rec['desc'], className="mb-0 small")
            ], color=rec['type'], className="mb-2") for rec in recommendations
        ]

        # === 模块 A: 单品日记 (Product Daily Journal) ===
        # 需要关联订单总额来判断角色
        # 获取相关订单ID
        order_ids = df['订单ID'].unique()
        # 从全局数据中获取这些订单的完整信息 (为了计算订单总额)
        # 优化: 仅获取必要列
        related_orders = GLOBAL_DATA[GLOBAL_DATA['订单ID'].isin(order_ids)][['订单ID', '实收价格', '商品名称']]
        order_totals = related_orders.groupby('订单ID')['实收价格'].sum().to_dict()
        
        def get_role(row):
            if row['利润额'] < 0: return '亏损引流'
            total = order_totals.get(row['订单ID'], 0)
            if total == 0: return '核心需求' # 默认归为核心需求
            ratio = row['实收价格'] / total
            if ratio > 0.6: return '核心需求' # 主买
            if ratio < 0.3: return '凑单配角' # 顺手买
            return '核心需求' # 其他情况归为核心需求

        df['角色'] = df.apply(get_role, axis=1)
        
        # 按日和角色聚合销量
        role_agg = df.groupby(['Date', '角色'])['订单ID'].nunique().reset_index(name='销量')
        # ⚠️ 关键修复: 确保日期格式正确
        role_agg['Date'] = pd.to_datetime(role_agg['Date'])
        
        fig_journal = px.bar(role_agg, x='Date', y='销量', color='角色', title="📊 单品日记 (购买角色拆解)",
                             color_discrete_map={'核心需求': '#2ecc71', '凑单配角': '#3498db', '亏损引流': '#e74c3c'},
                             height=350)
        fig_journal.update_layout(margin=dict(l=20, r=20, t=40, b=20), legend=dict(orientation="h", y=1.1))
        # 强制设置X轴格式
        fig_journal.update_xaxes(
            tickformat="%Y-%m-%d",
            dtick="D1"
        )

        # === 模块 B: 最佳拍档 (Association Analysis) ===
        # 在 related_orders 中找同单商品
        partners = related_orders[related_orders['商品名称'] != product_name]
        if not partners.empty:
            top_partners = partners['商品名称'].value_counts().head(5).reset_index()
            top_partners.columns = ['商品名称', '频次']
            fig_partner = px.bar(top_partners, x='频次', y='商品名称', orientation='h', title="🤝 最佳拍档 (Top 5 连带)",
                                 text='频次', height=300)
            fig_partner.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=40, b=20))
        else:
            fig_partner = go.Figure()
            fig_partner.add_annotation(text="无连带数据", showarrow=False)

        # === 模块 C: 时段画像 (Hourly Heatmap) ===
        hourly_agg = df.groupby('Hour')['订单ID'].nunique().reset_index(name='销量')
        # 补全24小时
        full_hours = pd.DataFrame({'Hour': range(24)})
        hourly_agg = full_hours.merge(hourly_agg, on='Hour', how='left').fillna(0)
        
        fig_hourly = px.area(hourly_agg, x='Hour', y='销量', title="⏰ 时段画像 (24h热度)",
                             line_shape='spline', height=300)
        fig_hourly.update_xaxes(tickmode='linear', dtick=2)
        fig_hourly.update_layout(margin=dict(l=20, r=20, t=40, b=20))

        # 组装布局
        return html.Div([
            # 顶部: 核心指标卡片
            dbc.Row([
                dbc.Col(create_stat_card("总销量", f"{total_quantity}单", "累计销量", "📦", "primary"), width=3),
                dbc.Col(create_stat_card("总销售额", f"¥{total_sales:,.0f}", "累计销售", "💰", "warning"), width=3),
                dbc.Col(create_stat_card("平均单价", f"¥{avg_price:.1f}", "实收/销量", "🏷️", "info"), width=3),
                dbc.Col(create_stat_card("毛利率", f"{avg_margin:.1f}%", "利润/销售额", "📈", 
                                       "danger" if avg_margin < 15 else "success"), width=3),
            ], className="mb-4"),

            # 第一排: 单品日记(A) + 最佳拍档(B)
            dbc.Row([
                dbc.Col(dcc.Graph(figure=fig_journal, config={'displayModeBar': False}), width=6),
                dbc.Col(dcc.Graph(figure=fig_partner, config={'displayModeBar': False}), width=6),
            ], className="mb-4"),
            
            # 第二排: 时段画像(C) + 价格敏感度(D)
            dbc.Row([
                dbc.Col(dcc.Graph(figure=fig_hourly, config={'displayModeBar': False}), width=6),
                dbc.Col(dcc.Graph(figure=fig_price, config={'displayModeBar': False}), width=6),
            ], className="mb-4"),
            
            # 第三排: 智能洞察与建议 (AI Insights)
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("💡 价格敏感度洞察"),
                        dbc.CardBody([
                            html.Div([
                                html.Span("敏感度评级: ", className="fw-bold"),
                                dbc.Badge(sensitivity_text, color=sensitivity_color, className="ms-2")
                            ], className="mb-3"),
                            html.P(f"价格-销量相关系数: {correlation:.2f}", className="text-muted small mb-0"),
                            html.Small("(系数越接近-1表示越敏感，即降价能显著带来销量提升)", className="text-muted")
                        ])
                    ])
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("🎯 推荐行动方案"),
                        dbc.CardBody(recommendation_ui)
                    ])
                ], width=6)
            ])
        ])

    except Exception as e:
        print(f"❌ [单品洞察] 渲染失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"渲染单品洞察时发生错误: {str(e)}", color="danger")


def generate_batch_volatility_analysis(channel_name, filter_type):
    """
    生成批量波动分析内容 (Top 5 异常商品的价格趋势)
    """
    try:
        import plotly.express as px
        
        # 1. 获取数据
        df_global = get_real_global_data()
        if df_global is None or df_global.empty:
            return dbc.Alert("⚠️ 暂无数据", color="warning")
            
        # 2. 筛选渠道
        df = df_global[df_global['渠道'] == channel_name].copy()
        if df.empty:
            return dbc.Alert(f"⚠️ {channel_name} 无数据", color="warning")

        # 🧹 [展示优化] 剔除耗材
        category_col = None
        for col_name in ['一级分类名', '美团一级分类', '一级分类']:
            if col_name in df.columns:
                category_col = col_name
                break
        
        if category_col:
            df = df[df[category_col] != '耗材'].copy()
            
        # 3. 识别异常商品 (复用筛选逻辑)
        # 预处理
        numeric_cols = ['实收价格', '利润额', '商品采购成本']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        if '利润额' not in df.columns:
            df['利润额'] = df['实收价格'] - df.get('商品采购成本', 0)
            
        # 聚合计算
        agg_rules = {
            '订单ID': 'nunique', # 销量
            '利润额': 'sum',     # 总利润
            '实收价格': 'sum'    # 销售额
        }
        product_agg = df.groupby('商品名称').agg(agg_rules).rename(columns={
            '订单ID': '销量',
            '利润额': '总利润',
            '实收价格': '销售额'
        }).reset_index()
        
        product_agg['毛利率'] = (product_agg['总利润'] / product_agg['销售额'] * 100).fillna(0).round(1)
        product_agg['单均利润'] = (product_agg['总利润'] / product_agg['销量']).fillna(0).round(2)
        
        # 应用筛选
        filtered_products = pd.DataFrame()
        if filter_type == 'low-margin':
            filtered_products = product_agg[product_agg['毛利率'] < 15].copy()
        elif filter_type == 'delivery-issues':
            filtered_products = product_agg[(product_agg['单均利润'] < 2) & (product_agg['销量'] > 10)].copy()
        elif filter_type == 'discount-products':
            filtered_products = product_agg[(product_agg['毛利率'] < 20) & (product_agg['销量'] > 5)].copy()
        else:
            filtered_products = product_agg.copy()
            
        if filtered_products.empty:
            return dbc.Alert("🎉 当前筛选条件下没有发现异常商品，无需分析。", color="success")
            
        # 4. 选取Top 5 重点商品 (按销量排序)
        top_products = filtered_products.sort_values('销量', ascending=False).head(5)['商品名称'].tolist()
        
        # 5. 准备趋势数据
        df_trend = df[df['商品名称'].isin(top_products)].copy()
        
        # 统一日期字段
        date_col = '日期' if '日期' in df_trend.columns else '下单时间'
        df_trend[date_col] = pd.to_datetime(df_trend[date_col])
        
        # 仅取最近30天数据
        max_date = df_trend[date_col].max()
        min_date = max_date - pd.Timedelta(days=30)
        df_trend = df_trend[df_trend[date_col] >= min_date]
        
        # 按日聚合计算平均实收价
        daily_data = df_trend.groupby([df_trend[date_col].dt.date, '商品名称'])['实收价格'].mean().reset_index()
        daily_data.columns = ['日期', '商品名称', '平均实收价']
        
        # 6. 生成图表
        fig = px.line(
            daily_data, 
            x='日期', 
            y='平均实收价', 
            color='商品名称',
            title=f'Top 5 异常商品 - 价格波动趋势 ({filter_type})',
            markers=True,
            template='plotly_white'
        )
        
        fig.update_layout(
            xaxis_title="日期",
            yaxis_title="平均实收价 (元)",
            legend_title="商品名称",
            hovermode="x unified",
            height=450
        )
        
        return html.Div([
            dbc.Alert(f"🔍 已自动选取销量最高的 {len(top_products)} 个异常商品进行分析", color="info", className="mb-3"),
            dcc.Graph(figure=fig),
            html.Hr(),
            html.H5("💡 波动分析建议"),
            html.Ul([
                html.Li("观察曲线是否存在突然的'深V'下探，这通常意味着某天活动设置错误（如满减叠加）。"),
                html.Li("如果曲线持续走低，说明该商品可能陷入了价格战，建议重新评估定价策略。"),
                html.Li("如果曲线平稳但利润仍为负，说明是结构性亏损（成本过高），而非临时活动导致。")
            ], className="text-muted small")
        ])
        
    except Exception as e:
        print(f"❌ [波动分析] 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"⚠️ 分析生成失败: {str(e)}", color="danger")
    

if __name__ == '__main__':
    print("🧪 下钻回调函数模块测试")
    print("=" * 60)
    
    if DRILL_DOWN_AVAILABLE:
        print("✅ 状态管理模块已导入")
        print("✅ 4个回调函数已定义:")
        print("   1. drill_down_to_channel_callback - 总览→渠道")
        print("   2. go_back_callback - 返回上一层")
        print("   3. breadcrumb_navigation_callback - 面包屑跳转")
        print("   4. update_drill_down_container - 容器内容更新")
        print("\n📝 使用方法:")
        print("   from components.drill_down_callbacks import register_drill_down_callbacks")
        print("   register_drill_down_callbacks(app)")
    else:
        print("❌ 状态管理模块未找到")
    
    print("=" * 60)
