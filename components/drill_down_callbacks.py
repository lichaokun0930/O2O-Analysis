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
    from echarts_factory import create_line_chart
    from dash_echarts import DashECharts
    from component_styles import create_stat_card
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    print("⚠️ 图表组件导入失败,部分功能受限")
    print("⚠️ 下钻状态管理模块未找到")


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
        
        print(f"🔔 [下钻回调] 回调被触发!")
        print(f"📊 [下钻回调] ctx.triggered: {ctx.triggered}")
        print(f"📊 [下钻回调] n_clicks_list: {n_clicks_list}")
        
        # 检查是否有按钮被点击
        if not ctx.triggered:
            print("⚠️ [下钻回调] ctx.triggered为空,返回no_update")
            return no_update, no_update, no_update, no_update, no_update, no_update
            
        if not any(n_clicks_list):
            print("⚠️ [下钻回调] 所有按钮n_clicks都为None,返回no_update")
            return no_update, no_update, no_update, no_update, no_update, no_update
        
        # 获取触发的按钮ID
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        print(f"🎯 [下钻回调] triggered_id: {triggered_id}")
        
        # 解析按钮ID获取渠道名称
        import json
        button_id = json.loads(triggered_id)
        channel_name = button_id['channel']
        
        print(f"🔍 [下钻回调] 用户点击渠道: {channel_name}")
        
        # 创建状态管理器并执行下钻
        state = DrillDownState()
        state.current_layer = current_layer or 'overview'
        state.current_channel = current_channel
        state.current_product = current_product
        state.filter_type = filter_type
        state.navigation_history = history or []
        
        print(f"📦 [下钻回调] 下钻前状态:")
        print(f"   当前层级: {state.current_layer}")
        print(f"   历史栈: {state.navigation_history}")
        
        # 执行下钻操作
        new_state = state.drill_down_to_channel(channel_name)
        
        print(f"✅ [下钻回调] 下钻成功: {current_layer} → channel")
        print(f"📍 [下钻回调] 当前渠道: {channel_name}")
        print(f"📦 [下钻回调] 下钻后历史栈: {new_state['navigation_history']}")
        print(f"{'='*60}\n")
        
        return (
            new_state['current_layer'],
            new_state['current_channel'],
            new_state['current_product'],
            new_state['filter_type'],
            new_state['navigation_history'],
            new_state
        )
    
    # 回调2: 返回按钮 → 返回上一层
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
            Input('drill-down-back-button', 'n_clicks')
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
    def go_back_callback(n_clicks, history, current_layer, current_channel, 
                        current_product, filter_type):
        """
        返回上一层
        
        Args:
            n_clicks: 返回按钮点击次数
            history: 导航历史栈
            current_layer: 当前层级
            current_channel: 当前渠道
            current_product: 当前商品
            filter_type: 当前筛选类型
            
        Returns:
            tuple: (新层级, 新渠道, 新商品, 新筛选类型, 新历史栈, 完整状态)
        """
        if not n_clicks:
            return no_update, no_update, no_update, no_update, no_update, no_update
        
        print(f"\n{'='*60}")
        print(f"⬅️ [返回回调] 点击返回按钮 (第{n_clicks}次点击)")
        print(f"📊 [返回回调] 接收到的State数据:")
        print(f"   - current_layer: {current_layer}")
        print(f"   - current_channel: {current_channel}")
        print(f"   - history长度: {len(history) if history else 0}")
        print(f"   - history内容: {history}")
        
        # 如果已经在overview层,不执行返回
        if current_layer == 'overview' or current_layer is None:
            print("⚠️ [返回回调] 已在overview层,无法返回")
            print(f"{'='*60}\n")
            return no_update, no_update, no_update, no_update, no_update, no_update
        
        # 检查历史栈是否为空
        if not history or len(history) == 0:
            print("⚠️ [返回回调] 历史栈为空,强制返回overview")
            print(f"{'='*60}\n")
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
        
        print(f"📦 [返回回调] DrillDownState加载完成:")
        print(f"   - state.current_layer: {state.current_layer}")
        print(f"   - state.navigation_history: {state.navigation_history}")
        
        # 执行返回操作
        new_state = state.go_back()
        
        print(f"✅ [返回回调] 返回成功!")
        print(f"📊 [返回回调] 新状态:")
        print(f"   - new_layer: {new_state['current_layer']}")
        print(f"   - new_channel: {new_state['current_channel']}")
        print(f"   - new_history长度: {len(new_state['navigation_history'])}")
        print(f"   - new_history内容: {new_state['navigation_history']}")
        print(f"{'='*60}\n")
        
        return (
            new_state['current_layer'],
            new_state['current_channel'],
            new_state['current_product'],
            new_state['filter_type'],
            new_state['navigation_history'],
            new_state
        )
    
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
        
        print(f"🔗 [面包屑回调] 用户点击面包屑: index={breadcrumb_index}, layer={target_layer}")
        
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
        
        print(f"✅ [面包屑回调] 跳转成功: → {new_state['current_layer']}")
        print(f"📊 [面包屑回调] 新状态:")
        print(f"   - new_layer: {new_state['current_layer']}")
        print(f"   - new_channel: {new_state['current_channel']}")
        print(f"   - new_history长度: {len(new_state['navigation_history'])}")
        print(f"   - history内容: {new_state['navigation_history']}")
        print(f"{'='*60}\n")
        
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
        ],
        [
            Input('drill-down-current-layer', 'data'),
            Input('drill-down-current-channel', 'data'),
            Input('drill-down-current-product', 'data'),
            Input('drill-down-filter-type', 'data'),
            Input('drill-down-navigation-history', 'data')
        ],
        [
            State('db-store-filter', 'value')  # ✅ 新增: 获取当前门店名称
        ],
        prevent_initial_call='initial_duplicate'
    )
    def update_drill_down_container(current_layer, current_channel, current_product,
                                    filter_type, history, store_name):
        """
        根据当前层级渲染对应的内容,同时控制容器显示/隐藏
        
        ⚠️ 重要: 不再控制tab1-channel-section的显示,避免触发其他回调导致页面重新加载
        通过CSS的z-index和position来实现下钻容器覆盖在渠道卡片上方
        
        Args:
            current_layer: 当前层级
            current_channel: 当前渠道
            current_product: 当前商品
            filter_type: 当前筛选类型
            history: 导航历史栈
            store_name: 当前选中的门店名称
            
        Returns:
            tuple: (容器内容, 容器className)
        """
        print(f"\n{'='*60}")
        print(f"🎨 [容器更新] 触发渲染")
        print(f"📊 [容器更新] 接收到的状态:")
        print(f"   - current_layer: {current_layer}")
        print(f"   - current_channel: {current_channel}")
        print(f"   - history长度: {len(history) if history else 0}")
        print(f"   - store_name: {store_name}")
        
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
        
        # 根据层级渲染不同内容
        if current_layer == 'overview' or current_layer is None:
            # 第1层: 总览仪表盘 - 隐藏下钻容器
            print(f"📍 [容器更新] overview层 - 隐藏下钻容器")
            print(f"{'='*60}\n")
            return html.Div(), 'd-none'  # 使用d-none类隐藏
        
        elif current_layer == 'channel':
            # 第2层: 渠道深度分析 - 显示下钻容器(覆盖在渠道卡片上方)
            content = render_channel_detail(current_channel, store_name)
            drill_down_class = 'drill-down-overlay'  # 使用特殊类名实现覆盖效果
            print(f"📍 [容器更新] channel层 - 显示下钻容器")
        
        elif current_layer == 'product_list':
            # 第3层: 商品清单页面
            content = render_product_list(current_channel, filter_type)
            drill_down_class = 'drill-down-overlay'
            print(f"📍 [容器更新] product_list层 - 显示下钻容器")
        
        elif current_layer == 'product_insight':
            # 第4层: 单品深度洞察
            content = render_product_insight(current_channel, current_product)
            drill_down_class = 'drill-down-overlay'
            print(f"📍 [容器更新] product_insight层 - 显示下钻容器")
        
        else:
            content = dbc.Alert(f"未知层级: {current_layer}", color="danger")
            drill_down_class = 'drill-down-overlay'
            print(f"⚠️ [容器更新] 未知层级: {current_layer}")
        
        # 组装最终布局
        final_content = html.Div([
            breadcrumb_ui,
            back_button,
            html.Hr(),
            content
        ])
        
        print(f"✅ [容器更新] 渲染完成")
        print(f"{'='*60}\n")
        
        return final_content, drill_down_class
    
    print("✅ 下钻回调函数已注册 (4个回调)")


# ========== 渲染函数(占位实现,后续完善) ==========

def render_overview_dashboard():
    """渲染第1层:总览仪表盘 - 显示真实的渠道对比卡片"""
    try:
        # 导入全局数据
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from 智能门店看板_Dash版 import GLOBAL_DATA, _create_channel_comparison_cards, calculate_order_metrics
        
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


def render_channel_detail(channel_name, store_name=None):
    """
    渲染第2层:渠道深度分析
    
    包含:
    - 4个总体指标卡片(销售额/订单数/利润额/利润率)
    - 30天利润率趋势图
    - TOP10商品表格(可点击下钻到单品分析)
    
    ⚠️ 关键逻辑: 从主看板的全局order_agg中提取该渠道数据,确保计算一致性
    """
    try:
        # 导入必要模块
        import sys
        import os
        import pandas as pd
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from 智能门店看板_Dash版 import GLOBAL_DATA, calculate_order_metrics, CHANNELS_TO_REMOVE, PLATFORM_FEE_CHANNELS
        from echarts_factory import create_line_chart
        
        print(f"\n{'='*60}")
        print(f"🔍 [render_channel_detail] 开始渲染: {channel_name}")
        print(f"   门店: {store_name}")
        
        # 🔄 尝试从Redis获取最新数据 (解决模块间GLOBAL_DATA不同步问题)
        df = None
        if REDIS_AVAILABLE and store_name:
            try:
                # 尝试获取展示数据
                redis_key = f"store_data:{store_name}:display"
                cached_df = get_cached_dataframe(redis_key)
                if cached_df is not None and not cached_df.empty:
                    df = cached_df
                    print(f"✅ [Redis] 成功加载门店数据: {len(df)} 行")
                else:
                    # 尝试获取完整数据
                    redis_key_full = f"store_full_data:{store_name}"
                    cached_full = get_cached_dataframe(redis_key_full)
                    if cached_full is not None and not cached_full.empty:
                        df = cached_full
                        print(f"✅ [Redis] 成功加载门店完整数据: {len(df)} 行")
            except Exception as e:
                print(f"⚠️ [Redis] 读取失败: {e}")
        
        # 如果Redis未命中，回退到GLOBAL_DATA (可能 stale)
        if df is None:
            print(f"⚠️ [数据源] Redis未命中，回退到模块级GLOBAL_DATA")
            if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                print(f"❌ [render_channel_detail] GLOBAL_DATA为空")
                return dbc.Alert("⚠️ 暂无数据", color="warning")
            df = GLOBAL_DATA.copy()
        
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
            
        except Exception as e:
            print(f"   ❌ Step 5计算失败: {e}", flush=True)
            import traceback
            traceback.print_exc()
            raise
        
        # 6. 计算30天趋势数据(需要从原始df获取日期,然后关联order_agg的利润)
        # 先筛选该渠道的原始数据
        channel_data = df[df['渠道'] == channel_name].copy()
        
        if '日期' not in channel_data.columns and '下单时间' not in channel_data.columns:
            print(f"⚠️ [render_channel_detail] 缺少日期字段,无法生成趋势图")
            trend_chart = dbc.Alert("⚠️ 数据中缺少日期字段,无法显示趋势图", color="warning")
        else:
            # 统一使用日期字段
            if '日期' in channel_data.columns:
                channel_data['日期'] = pd.to_datetime(channel_data['日期'])
            else:
                channel_data['日期'] = pd.to_datetime(channel_data['下单时间'])
            
            # 创建订单ID到日期的映射
            order_date_map = channel_data.groupby('订单ID')['日期'].first()
            
            # 给channel_order_agg添加日期字段
            order_agg_with_date = channel_order_agg.copy()
            order_agg_with_date['订单ID'] = order_agg_with_date['订单ID'].astype(str)
            order_date_map.index = order_date_map.index.astype(str)
            order_agg_with_date['日期'] = order_agg_with_date['订单ID'].map(order_date_map)
            
            # 按日期聚合
            daily_data = order_agg_with_date.groupby(order_agg_with_date['日期'].dt.date).agg({
                '订单实际利润': 'sum',
                '实收价格' if '实收价格' in order_agg_with_date.columns else '商品实售价': 'sum',
                '订单ID': 'count'
            }).reset_index()
            daily_data.columns = ['日期', '利润额', '销售额', '订单数']
            daily_data['利润率'] = (daily_data['利润额'] / daily_data['销售额'] * 100).fillna(0).round(2)
            daily_data = daily_data.tail(30)  # 最近30天
            
            # 生成趋势图
            trend_chart = create_line_chart(
                data=daily_data,
                x_field='日期',
                y_fields=['利润率'],
                title='近30天利润率趋势',
                smooth=True,
                show_area=True
            )
        
        # 7. 计算TOP10商品(基于该渠道的原始数据)
        print(f"📊 [Step 5] 计算TOP10商品...")
        top_products = channel_data.groupby('商品名称').agg({
            '商品实售价': 'sum',
            '商品采购成本': 'sum' if '商品采购成本' in channel_data.columns else lambda x: 0,
            '订单ID': 'nunique'
        }).reset_index()
        top_products['利润额'] = top_products['商品实售价'] - top_products['商品采购成本']
        top_products['毛利率'] = (top_products['利润额'] / top_products['商品实售价'] * 100).fillna(0).round(1)
        top_products = top_products.sort_values('商品实售价', ascending=False).head(10)
        print(f"   ✅ TOP10商品计算完成", flush=True)
        
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
            
            # 30天趋势图
            dbc.Card([
                dbc.CardHeader("📈 近30天利润率趋势"),
                dbc.CardBody([
                    trend_chart if not isinstance(trend_chart, dbc.Alert) else trend_chart
                ])
            ], className="mb-4"),
            
            # TOP10商品表格
            dbc.Card([
                dbc.CardHeader("🏆 TOP10畅销商品"),
                dbc.CardBody([
                    dbc.Table([
                        html.Thead(html.Tr([
                            html.Th("排名"),
                            html.Th("商品名称"),
                            html.Th("销售额", style={'textAlign': 'right'}),
                            html.Th("订单数", style={'textAlign': 'right'}),
                            html.Th("毛利率", style={'textAlign': 'right'}),
                            html.Th("操作", style={'textAlign': 'center'})
                        ])),
                        html.Tbody([
                            html.Tr([
                                html.Td(f"#{i+1}"),
                                html.Td(row['商品名称']),
                                html.Td(f"¥{row['商品实售价']:,.0f}", style={'textAlign': 'right'}),
                                html.Td(f"{row['订单ID']:,}", style={'textAlign': 'right'}),
                                html.Td(
                                    html.Span(
                                        f"{row['毛利率']:.1f}%",
                                        className="text-danger" if row['毛利率'] < 10 else "text-success"
                                    ),
                                    style={'textAlign': 'right'}
                                ),
                                html.Td(
                                    dbc.Button(
                                        "分析",
                                        size="sm",
                                        color="primary",
                                        outline=True,
                                        id={'type': 'product-drill-btn', 'channel': channel_name, 'product': row['商品名称']}
                                    ),
                                    style={'textAlign': 'center'}
                                )
                            ]) for i, row in top_products.iterrows()
                        ])
                    ], bordered=True, hover=True, responsive=True, striped=True)
                ])
            ]),
            
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
    """渲染第3层:商品清单页面"""
    filter_label = get_filter_type_label(filter_type)
    return dbc.Alert([
        html.H4(f"📦 {channel_name} - {filter_label}", className="alert-heading"),
        html.P("显示商品表格、筛选器、批量操作建议"),
        html.Hr(),
        html.P("🚧 待实现: 可交互表格和AI批量建议", className="mb-0")
    ], color="warning")


def render_product_insight(channel_name, product_name):
    """渲染第4层:单品深度洞察"""
    return dbc.Alert([
        html.H4(f"🔬 {product_name} 深度分析", className="alert-heading"),
        html.P(f"渠道: {channel_name}"),
        html.P("显示销售趋势、竞品对比、场景关联、3个推荐方案"),
        html.Hr(),
        html.P("🚧 待实现: AI洞察和可执行方案", className="mb-0")
    ], color="primary")


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
