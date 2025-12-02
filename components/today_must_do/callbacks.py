"""
今日必做功能 - 主回调模块 (V3.0 按紧急度分层重构)

设计理念:
- 问题导向：只展示有问题的，没问题的不占位置
- 可执行：看到问题后知道怎么行动
- 优先级清晰：最严重的问题最醒目

两层架构:
🔴 紧急处理（今日必须完成）
🟡 关注观察（本周内处理）

作者: GitHub Copilot
版本: V3.0
"""

print("🚀 [DEBUG] components.today_must_do.callbacks 模块正在加载...")

from dash import html, dcc, Input, Output, State, callback_context, no_update, ALL, callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import dash_table
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import sys
import os

# ECharts 导入
try:
    from dash_echarts import DashECharts
    ECHARTS_AVAILABLE = True
except ImportError:
    ECHARTS_AVAILABLE = False
    DashECharts = None

# 导入V2.0分析模块
from .product_analysis import (
    analyze_product_fluctuation,
    analyze_slow_moving_products,
    get_product_insight,
    get_declining_products,
    identify_slow_moving_products,
    analyze_top_profit_products,
    analyze_traffic_drop_products,
    analyze_new_slow_moving_products,
    analyze_potential_new_products
)
from .delivery_analysis import (
    analyze_delivery_issues,
    create_delivery_heatmap_data,
    get_delivery_summary_by_distance,
    identify_delivery_issues
)
from .marketing_analysis import (
    analyze_marketing_loss,
    analyze_activity_overlap,
    create_marketing_delivery_matrix,
    get_discount_analysis_by_range,
    identify_discount_overflow_orders
)
# 导入V3.0诊断分析模块
from .diagnosis_analysis import (
    analyze_urgent_issues,
    analyze_watch_issues,
    analyze_highlights,
    get_diagnosis_summary,
    get_overflow_orders,
    get_overflow_products,  # 新增：商品级穿底分析
    get_high_delivery_orders,
    get_stockout_products,
    get_traffic_drop_products,
    get_slow_moving_products,
    get_new_products,
    get_price_abnormal_products,
    get_profit_rate_drop_products,
    get_hot_products,
    get_high_profit_products,
    # 新增：价格变动检测与弹性分析
    detect_price_changes_from_orders,
    calculate_price_elasticity,
    get_product_price_history,
    get_price_elasticity_summary
)

# 🎨 导入美化UI组件
try:
    import dash_mantine_components as dmc
    from dash_iconify import DashIconify
    MANTINE_AVAILABLE = True
    print("✅ [UI] Dash Mantine Components 已加载")
except ImportError:
    MANTINE_AVAILABLE = False
    print("⚠️ [UI] Dash Mantine Components 未安装，使用默认样式")


# ==================== 辅助函数：获取全局数据 ====================
def get_real_global_data():
    """获取真实的全局数据(GLOBAL_DATA)"""
    if '__main__' in sys.modules:
        main_module = sys.modules['__main__']
        if hasattr(main_module, 'get_global_data'):
            return main_module.get_global_data()
        if hasattr(main_module, 'GLOBAL_DATA'):
            return main_module.GLOBAL_DATA
            
    try:
        from 智能门店看板_Dash版 import get_global_data
        return get_global_data()
    except ImportError:
        pass
    
    try:
        from 智能门店看板_Dash版 import GLOBAL_DATA
        return GLOBAL_DATA
    except ImportError:
        pass
        
    return None


# ==================== 🎨 美化UI组件工厂 ====================

def create_mantine_diagnosis_card(
    title: str,
    icon: str,
    color: str,
    main_value: str,
    main_label: str,
    sub_info: str = None,
    extra_info: str = None,
    extra_badges: list = None,
    button_id: str = None,
    button_text: str = "查看详情"
) -> html.Div:
    """
    创建紧凑型 Mantine 风格诊断卡片
    
    Args:
        title: 卡片标题
        icon: Iconify 图标名称（如 "tabler:alert-triangle"）
        color: 主题颜色（red, orange, yellow, green, blue, violet, indigo）
        main_value: 主数值
        main_label: 数值说明
        sub_info: 次要信息（如累计损失）
        extra_info: 额外信息行（如距离分布）
        extra_badges: 额外的徽章列表 [{"text": "xxx", "color": "red"}, ...]
        button_id: 按钮ID
        button_text: 按钮文字
    """
    if not MANTINE_AVAILABLE:
        # 回退到基础样式
        bs_color = {'red': 'danger', 'orange': 'warning', 'green': 'success', 
                    'blue': 'info', 'indigo': 'primary', 'violet': 'secondary'}.get(color, color)
        return html.Div([
            html.Div(f"{title}", className=f"fw-bold text-{bs_color} mb-2"),
            html.Div([main_value, " ", main_label]),
            html.Div(sub_info, className="small text-muted") if sub_info else None,
        ], className=f"p-3 bg-{bs_color} bg-opacity-10 rounded h-100 border-start border-4 border-{bs_color}")
    
    # 颜色映射（Bootstrap → Mantine）
    color_map = {
        'danger': 'red', 'warning': 'orange', 'success': 'green',
        'info': 'blue', 'primary': 'indigo', 'secondary': 'gray',
    }
    mantine_color = color_map.get(color, color)
    
    # 构建徽章组 - 优化为更醒目的样式
    badge_group = []
    if extra_badges:
        for badge in extra_badges:
            badge_color = color_map.get(badge.get('color', 'gray'), badge.get('color', 'gray'))
            badge_group.append(
                dmc.Badge(
                    badge.get('text', ''),
                    color=badge_color,
                    variant="filled",  # 实心徽章更醒目
                    size="md",  # 加大尺寸
                    radius="sm",
                    styles={
                        "root": {
                            "fontWeight": 600,
                            "fontSize": "12px",
                            "padding": "4px 10px",
                            "textTransform": "none",  # 保持原样不转大写
                        }
                    }
                )
            )
    
    # 构建内容
    children = [
        # 标题行：图标 + 标题
        dmc.Group([
            dmc.ThemeIcon(
                DashIconify(icon=icon, width=24),  # 图标加大
                color=mantine_color,
                variant="light",
                radius="md",
                size="xl"  # 图标容器更大
            ),
            dmc.Text(title, fw=700, size="lg", c=mantine_color),  # 标题更大
        ], gap="sm"),
        
        # 主数值行 - 数值更突出
        dmc.Group([
            dmc.Text(
                main_value, 
                fw=900, 
                c=mantine_color, 
                style={"fontSize": "2.2rem", "lineHeight": 1, "letterSpacing": "-1px"}  # 数值更大更醒目
            ),
            dmc.Text(main_label, size="md", c="dark", fw=500),  # 标签更清晰
        ], gap="sm", mt="md", align="baseline"),
    ]
    
    # 次要信息 - 增强对比度
    if sub_info:
        children.append(
            dmc.Text(sub_info, size="sm", c=mantine_color, mt=8, fw=600, 
                    style={"opacity": 0.85})
        )
    
    # 额外信息
    if extra_info:
        children.append(
            dmc.Text(extra_info, size="sm", c="dimmed", mt=4, fw=500)
        )
    
    # 徽章组 - 间距调整
    if badge_group:
        children.append(
            dmc.Group(badge_group, gap="sm", mt="md", wrap="wrap")
        )
    
    # 操作按钮 - 使用实心按钮更醒目
    if button_id:
        children.append(
            html.Div([
                dmc.Divider(mt="md", mb="sm", color="gray", opacity=0.2),  # 分割线
                dmc.Button(
                    [
                        DashIconify(icon="tabler:eye", width=18, style={"marginRight": "8px"}),
                        button_text,
                        DashIconify(icon="tabler:chevron-right", width=18, style={"marginLeft": "6px"})
                    ],
                    id=button_id,
                    variant="filled",  # 实心按钮更醒目
                    color=mantine_color,
                    size="md",  # 按钮更大
                    radius="md",
                    fullWidth=True,
                    n_clicks=0,
                    styles={
                        "root": {
                            "fontWeight": 600,
                            "fontSize": "15px",
                            "height": "40px",  # 固定高度
                            "boxShadow": "0 2px 4px rgba(0,0,0,0.15)",
                            "transition": "all 0.2s ease",
                        },
                        "label": {
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                        }
                    }
                )
            ])
        )
    
    return dmc.Paper(
        children=children,
        p="lg",  # 增加内边距
        radius="lg",  # 圆角加大
        withBorder=True,
        shadow="sm",  # 添加阴影
        style={
            "height": "100%",
            "borderLeft": f"5px solid var(--mantine-color-{mantine_color}-6)",  # 左边框加粗
            "backgroundColor": f"var(--mantine-color-{mantine_color}-0)",  # 更浅的背景色
            "transition": "transform 0.2s ease, box-shadow 0.2s ease",
            "cursor": "default",
        }
    )


def get_calculate_order_metrics():
    """获取calculate_order_metrics函数"""
    if '__main__' in sys.modules:
        main_module = sys.modules['__main__']
        if hasattr(main_module, 'calculate_order_metrics'):
            return main_module.calculate_order_metrics
            
    try:
        from 智能门店看板_Dash版 import calculate_order_metrics
        return calculate_order_metrics
    except ImportError:
        pass
        
    return None


def apply_filters(df: pd.DataFrame, selected_stores=None, selected_channel=None) -> pd.DataFrame:
    """应用门店和渠道筛选"""
    result = df.copy()
    
    # 门店筛选
    if selected_stores:
        if isinstance(selected_stores, str):
            selected_stores = [selected_stores]
        
        if len(selected_stores) > 0 and '门店名称' in result.columns:
            result = result[result['门店名称'].isin(selected_stores)]
            
    # 渠道筛选
    if selected_channel and selected_channel != 'all':
        # 尝试匹配渠道字段
        channel_col = next((c for c in ['平台', '渠道', 'platform'] if c in result.columns), None)
        if channel_col:
            # 模糊匹配或精确匹配
            # 考虑到数据中可能是 "美团外卖" 而筛选值是 "美团"
            if selected_channel in ['美团', '饿了么']:
                result = result[result[channel_col].astype(str).str.contains(selected_channel, na=False)]
            else:
                result = result[result[channel_col] == selected_channel]
    
    return result


def get_base_dates(df: pd.DataFrame) -> Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
    """获取昨日和前日日期"""
    date_col = '日期' if '日期' in df.columns else '下单时间'
    if date_col not in df.columns:
        return None, None
    
    df_copy = df.copy()
    df_copy[date_col] = pd.to_datetime(df_copy[date_col])
    
    yesterday = df_copy[date_col].max().normalize()
    day_before = yesterday - timedelta(days=1)
    
    return yesterday, day_before


def register_today_must_do_callbacks(app):
    """注册今日必做功能的所有回调函数"""
    print("[DEBUG] 开始注册今日必做回调函数...")
    
    @app.callback(
        Output('today-must-do-content', 'children'),
        [Input('main-tabs', 'value'),
         Input('data-update-trigger', 'data')],
        [State('db-store-filter', 'value')]
    )
    def update_today_must_do_content(active_tab, data_trigger, selected_stores):
        """主内容渲染回调"""
        print(f"[DEBUG] 今日必做主回调被调用! active_tab={active_tab}")
        
        if active_tab != 'tab-today-must-do':
            print(f"[DEBUG] 非今日必做Tab, 忽略. active_tab={active_tab}")
            return no_update
        
        print(f"[DEBUG] 今日必做主回调触发: active_tab={active_tab}, stores={selected_stores}")
        
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            print("[DEBUG] GLOBAL_DATA 为空")
            return create_no_data_message()
            
        print(f"[DEBUG] GLOBAL_DATA shape: {GLOBAL_DATA.shape}")
        try:
            layout = create_today_must_do_layout(GLOBAL_DATA, selected_stores)
            print("[DEBUG] create_today_must_do_layout 成功")
            return layout
        except Exception as e:
            print(f"[ERROR] create_today_must_do_layout 失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return create_error_message(f"渲染失败: {str(e)}")

    @app.callback(
        [Output("product-detail-modal", "is_open"),
         Output("product-detail-modal-body", "children"),
         Output("product-detail-modal-header", "children")],
        [Input({'type': 'product-analysis-table', 'index': ALL}, "active_cell"),
         Input("product-detail-modal-close", "n_clicks")],
        [State({'type': 'product-analysis-table', 'index': ALL}, "data"),
         State("product-detail-modal", "is_open")]
    )
    def toggle_product_detail_modal(active_cells, n_close, datas, is_open):
        ctx = callback_context
        if not ctx.triggered:
            return is_open, no_update, no_update
            
        trigger_prop_id = ctx.triggered[0]['prop_id']
        print(f"[DEBUG] Modal trigger: {trigger_prop_id}")
        
        if 'product-detail-modal-close' in trigger_prop_id:
            return False, no_update, no_update
            
        # Check if it's one of our tables
        if 'product-analysis-table' in trigger_prop_id:
            # Since only one table is rendered at a time, active_cells and datas 
            # will typically contain only one element (the visible table)
            
            # Find the active cell that is not None
            active_cell = None
            data = None
            
            for ac, d in zip(active_cells, datas):
                if ac:
                    active_cell = ac
                    data = d
                    break
            
            if active_cell and data:
                row_idx = active_cell['row']
                if row_idx < len(data):
                    product_name = data[row_idx].get('商品名称')
                    print(f"[DEBUG] Clicked product: {product_name}")
                    
                    if product_name:
                        GLOBAL_DATA = get_real_global_data()
                        if GLOBAL_DATA is None:
                            return True, "数据未加载", "错误"
                            
                        # Generate detail content
                        content = create_product_detail_content(GLOBAL_DATA, product_name)
                        return True, content, dbc.ModalTitle(f"📊 {product_name}")
            
        return is_open, no_update, no_update

    # ==================== 诊断详情弹窗回调 ====================
    @app.callback(
        Output('diagnosis-detail-modal', 'is_open'),
        Output('diagnosis-detail-modal-title', 'children'),
        Output('diagnosis-detail-modal-body', 'children'),
        Output('diagnosis-detail-type-store', 'data'),
        Input('btn-diagnosis-overflow', 'n_clicks'),
        Input('btn-diagnosis-delivery', 'n_clicks'),
        Input('btn-diagnosis-stockout', 'n_clicks'),
        Input('btn-diagnosis-traffic', 'n_clicks'),
        Input('btn-diagnosis-slow', 'n_clicks'),
        Input('btn-diagnosis-newproduct', 'n_clicks'),
        Input('btn-diagnosis-price-abnormal', 'n_clicks'),
        Input('btn-diagnosis-profit-drop', 'n_clicks'),
        Input('btn-diagnosis-hot-products', 'n_clicks'),
        Input('btn-diagnosis-high-profit', 'n_clicks'),
        Input('btn-diagnosis-price-elasticity', 'n_clicks'),  # 新增：价格弹性分析
        Input('diagnosis-detail-modal-close', 'n_clicks'),
        State('diagnosis-detail-modal', 'is_open'),
        State('db-store-filter', 'value'),
        prevent_initial_call=True
    )
    def toggle_diagnosis_detail_modal(
        n_overflow, n_delivery, n_stockout, n_traffic, n_slow, n_newproduct, 
        n_price_abnormal, n_profit_drop, n_hot_products, n_high_profit, n_price_elasticity, n_close,
        is_open, selected_stores
    ):
        """处理诊断详情弹窗的打开/关闭"""
        ctx = callback_context
        if not ctx.triggered:
            return is_open, no_update, no_update, no_update
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        # 关闭按钮
        if trigger_id == 'diagnosis-detail-modal-close':
            return False, no_update, no_update, None
        
        # 获取数据
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return True, "数据错误", dbc.Alert("数据未加载", color="warning"), None
        
        df = GLOBAL_DATA.copy()
        
        # 应用门店筛选
        if selected_stores:
            if isinstance(selected_stores, str):
                selected_stores = [selected_stores]
            if len(selected_stores) > 0 and '门店名称' in df.columns:
                df = df[df['门店名称'].isin(selected_stores)]
        
        # 注意：不应用渠道筛选，保持与卡片数据一致
        # 渠道筛选只用于其他分析模块，诊断卡片始终显示全渠道数据
        
        # 根据触发的按钮生成不同内容
        title = ""
        content = html.Div("加载中...")
        detail_type = trigger_id
        
        try:
            if trigger_id == 'btn-diagnosis-overflow':
                title = "💸 穿底订单详情"
                content = create_overflow_detail_table(df)
            elif trigger_id == 'btn-diagnosis-delivery':
                title = "🚨 高配送费订单详情"
                content = create_delivery_detail_table(df)
            elif trigger_id == 'btn-diagnosis-stockout':
                title = "📦 热销缺货商品清单"
                content = create_stockout_detail_table(df)
            elif trigger_id == 'btn-diagnosis-traffic':
                title = "📉 流量异常商品清单"
                content = create_traffic_drop_detail_table(df)
            elif trigger_id == 'btn-diagnosis-slow':
                title = "🐌 滞销商品清单"
                content = create_slow_moving_detail_table(df)
            elif trigger_id == 'btn-diagnosis-newproduct':
                title = "🚀 新品表现详情"
                content = create_new_product_detail_table(df)
            elif trigger_id == 'btn-diagnosis-price-abnormal':
                title = "⚠️ 价格异常商品清单"
                content = create_price_abnormal_detail_table(df)
            elif trigger_id == 'btn-diagnosis-profit-drop':
                title = "📉 利润率下滑商品清单"
                content = create_profit_drop_detail_table(df)
            elif trigger_id == 'btn-diagnosis-hot-products':
                title = "🔥 爆款商品清单"
                content = create_hot_products_detail_table(df)
            elif trigger_id == 'btn-diagnosis-high-profit':
                title = "💰 高利润商品清单"
                content = create_high_profit_detail_table(df)
            elif trigger_id == 'btn-diagnosis-price-elasticity':
                title = "📊 价格弹性分析"
                content = create_price_elasticity_detail_table(df)
        except Exception as e:
            content = dbc.Alert(f"加载详情失败: {str(e)}", color="danger")
        
        return True, title, content, detail_type

    @app.callback(
        Output('diagnosis-download', 'data'),
        Input('diagnosis-detail-export-btn', 'n_clicks'),
        State('diagnosis-detail-type-store', 'data'),
        State('db-store-filter', 'value'),
        prevent_initial_call=True
    )
    def export_diagnosis_detail(n_clicks, detail_type, selected_stores):
        """导出诊断详情到Excel"""
        if not n_clicks or not detail_type:
            return no_update
        
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return no_update
        
        df = GLOBAL_DATA.copy()
        
        # 应用门店筛选
        if selected_stores:
            if isinstance(selected_stores, str):
                selected_stores = [selected_stores]
            if len(selected_stores) > 0 and '门店名称' in df.columns:
                df = df[df['门店名称'].isin(selected_stores)]
        
        # 根据类型生成导出数据
        export_df = None
        filename = "诊断详情.xlsx"
        
        try:
            if detail_type == 'btn-diagnosis-overflow':
                # 穿底数据使用多sheet导出
                export_data = get_overflow_export_data(df)
                filename = "穿底商品清单.xlsx"
                
                if export_data is not None and len(export_data) > 0:
                    from io import BytesIO
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        for sheet_name, sheet_df in export_data.items():
                            # Excel sheet名称最长31字符，且不能包含特殊字符
                            safe_name = str(sheet_name)[:31].replace('/', '_').replace('\\', '_').replace('*', '_')
                            sheet_df.to_excel(writer, sheet_name=safe_name, index=False)
                    output.seek(0)
                    return dcc.send_bytes(output.getvalue(), filename)
                return no_update
                
            elif detail_type == 'btn-diagnosis-delivery':
                # 高配送费订单使用多sheet导出
                export_data = get_delivery_export_data(df)
                filename = "高配送费订单清单.xlsx"
                
                if export_data is not None and len(export_data) > 0:
                    from io import BytesIO
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        for sheet_name, sheet_df in export_data.items():
                            safe_name = str(sheet_name)[:31].replace('/', '_').replace('\\', '_').replace('*', '_')
                            sheet_df.to_excel(writer, sheet_name=safe_name, index=False)
                    output.seek(0)
                    return dcc.send_bytes(output.getvalue(), filename)
                return no_update
                
            elif detail_type == 'btn-diagnosis-stockout':
                export_df = get_stockout_export_data(df)
                filename = "热销缺货商品清单.xlsx"
            elif detail_type == 'btn-diagnosis-traffic':
                export_df = get_traffic_drop_export_data(df)
                filename = "流量异常商品清单.xlsx"
            elif detail_type == 'btn-diagnosis-slow':
                export_df = get_slow_moving_export_data(df)
                filename = "滞销商品清单.xlsx"
            elif detail_type == 'btn-diagnosis-newproduct':
                export_df = get_new_product_export_data(df)
                filename = "新品表现清单.xlsx"
            elif detail_type == 'btn-diagnosis-price-abnormal':
                export_df = get_price_abnormal_export_data(df)
                filename = "价格异常商品清单.xlsx"
            elif detail_type == 'btn-diagnosis-profit-drop':
                export_df = get_profit_drop_export_data(df)
                filename = "利润率下滑商品清单.xlsx"
            elif detail_type == 'btn-diagnosis-hot-products':
                export_df = get_hot_products_export_data(df)
                filename = "爆款商品清单.xlsx"
            elif detail_type == 'btn-diagnosis-high-profit':
                export_df = get_high_profit_export_data(df)
                filename = "高利润商品清单.xlsx"
            elif detail_type == 'btn-diagnosis-price-elasticity':
                export_df = get_price_elasticity_export_data(df)
                filename = "价格弹性分析.xlsx"
            
            if export_df is not None and not export_df.empty:
                from io import BytesIO
                output = BytesIO()
                export_df.to_excel(output, index=False, engine='openpyxl')
                output.seek(0)
                return dcc.send_bytes(output.getvalue(), filename)
        except Exception as e:
            print(f"导出失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return no_update

    # ==================== 商品综合分析回调 ====================
    @app.callback(
        Output('collapse-scoring-detail', 'is_open'),
        Input('btn-toggle-scoring-detail', 'n_clicks'),
        State('collapse-scoring-detail', 'is_open'),
        prevent_initial_call=True
    )
    def toggle_scoring_detail_collapse(n_clicks, is_open):
        """切换商品评分详细数据表的展开/折叠"""
        if n_clicks:
            return not is_open
        return is_open
    
    # 注：原八象限折叠回调已移除，改用Tab切换
    
    @app.callback(
        Output('product-scoring-export-download', 'data'),
        Input('btn-export-product-scoring', 'n_clicks'),
        State('db-store-filter', 'value'),
        prevent_initial_call=True
    )
    def export_product_scoring_report(n_clicks, selected_stores):
        """导出商品综合评分报告"""
        if not n_clicks:
            return no_update
        
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return no_update
        
        df = GLOBAL_DATA.copy()
        
        # 应用门店筛选
        if selected_stores:
            if isinstance(selected_stores, str):
                selected_stores = [selected_stores]
            if len(selected_stores) > 0 and '门店名称' in df.columns:
                df = df[df['门店名称'].isin(selected_stores)]
        
        try:
            export_df = get_product_scoring_export_data(df)
            if export_df is not None and not export_df.empty:
                from io import BytesIO
                output = BytesIO()
                export_df.to_excel(output, index=False, engine='openpyxl')
                output.seek(0)
                return dcc.send_bytes(output.getvalue(), "商品综合评分报告.xlsx")
        except Exception as e:
            print(f"导出商品评分报告失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return no_update

    # ==================== V5.0 商品筛选回调（点击象限/品类/评分等级筛选表格 + 联动Tab内容）====================
    @app.callback(
        [Output('scoring-table-container', 'children'),
         Output('scoring-table-filter-label', 'children'),
         Output('collapse-scoring-detail', 'is_open', allow_duplicate=True),
         Output('product-health-content-container', 'children'),
         Output('current-category-filter-label', 'children')],
        [Input({'type': 'octant-filter-btn', 'index': ALL}, 'n_clicks'),
         Input({'type': 'category-filter-btn', 'index': ALL}, 'n_clicks'),
         Input({'type': 'score-level-filter-btn', 'index': ALL}, 'n_clicks'),
         Input('btn-clear-scoring-filter', 'n_clicks')],
        [State('db-store-filter', 'value')],
        prevent_initial_call=True
    )
    def filter_scoring_table(octant_clicks, category_clicks, score_level_clicks, clear_clicks, selected_stores):
        """
        点击象限/品类/评分等级按钮筛选表格数据 + 联动更新Tab内容
        
        V5.0更新：
        - 统一计算模型（基于品类内排名百分位）
        - 点击八象限按钮 → 按象限筛选表格 + 自动展开表格
        - 点击品类按钮 → 按品类筛选表格 + 联动更新评分概览/象限分布Tab
        - 点击评分等级按钮 → 按评分等级筛选表格 + 自动展开表格
        - 点击清除按钮 → 显示全部数据 + 恢复Tab内容
        """
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update, no_update
        
        triggered_id = ctx.triggered[0]['prop_id']
        
        # 获取数据
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return html.Div("暂无数据"), "无数据", True, no_update, no_update
        
        df = GLOBAL_DATA.copy()
        
        # 应用门店筛选
        if selected_stores:
            if isinstance(selected_stores, str):
                selected_stores = [selected_stores]
            if len(selected_stores) > 0 and '门店名称' in df.columns:
                df = df[df['门店名称'].isin(selected_stores)]
        
        # 计算商品评分（全量）
        product_scores = calculate_enhanced_product_scores(df)
        if product_scores.empty:
            return html.Div("暂无商品数据"), "无数据", True, no_update, no_update
        
        # 判断触发来源
        filter_type = None
        filter_value = None
        filter_label = "全部商品"
        category_filter = None  # 用于Tab内容联动
        category_label = "全部商品"  # 用于品类筛选提示
        should_open_table = True
        
        if 'btn-clear-scoring-filter' in triggered_id:
            # 清除筛选
            filter_type = None
            filter_value = None
            filter_label = "全部商品"
            category_filter = None
            category_label = "全部商品"
        elif 'octant-filter-btn' in triggered_id:
            # 八象限筛选 - 只筛选表格，不影响Tab内容
            try:
                import json
                prop_id_json = triggered_id.split('.')[0]
                id_dict = json.loads(prop_id_json)
                filter_value = id_dict.get('index')
                if filter_value:
                    filter_type = 'octant'
                    count = len(product_scores[product_scores['八象限分类'] == filter_value])
                    filter_label = f"{filter_value} ({count}个)"
                    # 八象限筛选不改变品类选择，保持当前品类
            except Exception as e:
                print(f"解析象限筛选ID失败: {e}")
        elif 'category-filter-btn' in triggered_id:
            # 品类筛选 - 联动更新Tab内容和表格
            try:
                import json
                prop_id_json = triggered_id.split('.')[0]
                id_dict = json.loads(prop_id_json)
                filter_value = id_dict.get('index')
                if filter_value and filter_value != '__all__':
                    filter_type = 'category'
                    category_filter = filter_value  # 用于Tab内容联动
                    category_col = '一级分类名' if '一级分类名' in product_scores.columns else None
                    if category_col:
                        count = len(product_scores[product_scores[category_col] == filter_value])
                        filter_label = f"品类: {filter_value} ({count}个)"
                        category_label = f"{filter_value} ({count}个商品)"
                else:
                    filter_label = "全部商品"
                    category_filter = None
                    category_label = "全部商品"
            except Exception as e:
                print(f"解析品类筛选ID失败: {e}")
        elif 'score-level-filter-btn' in triggered_id:
            # 评分等级筛选 - 只筛选表格，不影响Tab内容
            try:
                import json
                prop_id_json = triggered_id.split('.')[0]
                id_dict = json.loads(prop_id_json)
                filter_value = id_dict.get('index')
                if filter_value:
                    filter_type = 'score_level'
                    count = len(product_scores[product_scores['评分等级'] == filter_value])
                    filter_label = f"{filter_value} ({count}个)"
            except Exception as e:
                print(f"解析评分等级筛选ID失败: {e}")
        
        # 创建筛选后的表格
        table = create_product_scoring_table_v4(product_scores, filter_type, filter_value)
        
        # 创建联动的Tab内容（仅品类筛选时更新）
        if 'category-filter-btn' in triggered_id or 'btn-clear-scoring-filter' in triggered_id:
            tab_content = create_product_health_content(product_scores, category_filter, category_filter)
        else:
            # 八象限筛选时不更新Tab内容
            tab_content = no_update
        
        return table, filter_label, should_open_table, tab_content, category_label

    print("✅ 今日必做回调函数已注册")


# ==================== 诊断详情表格UI函数 ====================

def create_overflow_detail_table(df: pd.DataFrame) -> html.Div:
    """
    创建穿底止血详情表格（订单视图 + 商品视图）
    
    设计理念：
    - 订单视图：定位哪些订单穿底，用于财务分析
    - 商品视图：定位哪些商品导致穿底，用于业务动作
    """
    order_data = get_overflow_orders(df)
    product_data = get_overflow_products(df)
    
    if order_data.empty and product_data.empty:
        return dbc.Alert("暂无穿底数据", color="info")
    
    # 计算穿底损失（负利润的绝对值之和）
    total_loss = abs(order_data['订单实际利润'].sum()) if not order_data.empty and '订单实际利润' in order_data.columns else 0
    order_count = len(order_data) if not order_data.empty else 0
    product_count = len(product_data) if not product_data.empty else 0
    
    # 订单视图表格
    order_table = html.Div([
        dash_table.DataTable(
            data=order_data.head(50).to_dict('records') if not order_data.empty else [],
            columns=[{'name': c, 'id': c, 'type': 'numeric', 'format': {'specifier': ',.2f'}} 
                     if c in ['销售额', '成本', '物流配送费', '平台服务费', '活动成本', '利润额', '订单实际利润'] 
                     else {'name': c, 'id': c} 
                     for c in order_data.columns] if not order_data.empty else [],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'column_id': '订单实际利润'}, 'color': 'red', 'fontWeight': 'bold'}
            ],
            page_size=10
        ),
        html.Div([
            html.Small([
                html.Strong("📌 定义提示："),
                "穿底 = 卖一单亏一单（订单实际利润为负）；数据范围：昨日订单"
            ], className="text-muted d-block"),
            html.Small([
                html.Strong("📝 判断标准："),
                "订单实际利润 < 0 即为穿底订单"
            ], className="text-muted d-block mt-1"),
            html.Small([
                html.Strong("📊 核心公式："),
                "订单实际利润 = 利润额 - 平台服务费 - 物流配送费 + 企客后返；",
                "单品成本 = 商品采购成本 ÷ 销量；",
                "穿底贡献 = 商品毛利 = 实收价格 × 销量 - 商品采购成本；",
                "定价毛利率 = (商品原价 - 单品成本) ÷ 商品原价 × 100%；",
                "实收毛利率 = (实收价格 - 单品成本) ÷ 实收价格 × 100%"
            ], className="text-muted d-block mt-1"),
        ], className="mt-2 p-2 bg-light rounded")
    ]) if not order_data.empty else dbc.Alert("暂无订单数据", color="secondary")
    
    # 商品视图表格
    product_table = html.Div([
        dash_table.DataTable(
            data=product_data.head(30).to_dict('records') if not product_data.empty else [],
            columns=[
                {'name': c, 'id': c, 'type': 'numeric', 'format': {'specifier': ',.2f'}} 
                if c in ['商品原价', '商品实售价', '实收价格', '单品成本', '穿底贡献'] 
                else {'name': c, 'id': c, 'type': 'numeric', 'format': {'specifier': '.1f'}} 
                if c in ['定价毛利率', '实收毛利率']
                else {'name': c, 'id': c} 
                for c in product_data.columns
            ] if not product_data.empty else [],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_cell_conditional=[
                {'if': {'column_id': '订单ID'}, 'whiteSpace': 'pre-line', 'minWidth': '120px'}
            ],
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'column_id': '穿底贡献', 'filter_query': '{穿底贡献} < 0'}, 'color': 'red', 'fontWeight': 'bold'},
                {'if': {'column_id': '实收毛利率', 'filter_query': '{实收毛利率} < 15'}, 'color': '#fd7e14'},
            ],
            page_size=10
        ),
        html.Div([
            html.Small("💡 处理建议：关注临期商品、爆品、神价品、重量加价配置", className="text-muted"),
        ], className="mt-2 p-2 bg-light rounded")
    ]) if not product_data.empty else dbc.Alert("暂无商品数据", color="secondary")
    
    return html.Div([
        # 顶部汇总
        html.Div([
            html.Span([
                html.I(className="bi bi-exclamation-triangle-fill me-2 text-danger"),
                f"昨日穿底：",
                html.Span(f"{order_count}单", className="fw-bold text-danger mx-1"),
                f"涉及 ",
                html.Span(f"{product_count}款商品", className="fw-bold text-danger mx-1"),
                f"，累计损失 ",
                html.Span(f"¥{total_loss:,.2f}", className="fw-bold text-danger")
            ])
        ], className="mb-3 p-2 bg-danger bg-opacity-10 rounded"),
        
        # Tab切换
        dbc.Tabs([
            dbc.Tab(product_table, label=f"📦 商品视图 ({product_count})", tab_id="product-view",
                   label_style={"fontWeight": "bold"}),
            dbc.Tab(order_table, label=f"📋 订单视图 ({order_count})", tab_id="order-view"),
        ], active_tab="product-view", className="mb-2"),
        
        # ========== 可视化图表区 ==========
        create_overflow_charts(product_data, order_data),
        
        html.Small([
            "💡 ",
            html.Strong("业务动作建议："),
            "优先处理「商品视图」中标红的商品，调整活动力度或退出活动"
        ], className="text-muted")
    ])


def create_overflow_charts(product_data: pd.DataFrame, order_data: pd.DataFrame) -> html.Div:
    """
    创建穿底分析可视化图表 (ECharts版)
    
    有价值的分析：
    1. 穿底原因分布 - 找到根因（定价问题/活动亏损/成本异常）
    2. 渠道穿底对比 - 哪个渠道问题最大
    """
    if not ECHARTS_AVAILABLE:
        return html.Div("ECharts 不可用", className="text-muted small")
    
    try:
        charts = []
        
        # ===== 图表1：穿底原因分布（饼图）=====
        if not product_data.empty:
            # 分析穿底原因
            reasons = {'定价问题': 0, '活动亏损': 0, '成本异常': 0}
            
            for _, row in product_data.iterrows():
                pricing_margin = row.get('定价毛利率', 0) or 0
                actual_margin = row.get('实收毛利率', 0) or 0
                loss = abs(row.get('穿底贡献', 0) or 0)
                
                if pricing_margin < 5:  # 定价本身就低
                    reasons['定价问题'] += loss
                elif pricing_margin - actual_margin > 15:  # 活动折扣太大
                    reasons['活动亏损'] += loss
                else:
                    reasons['成本异常'] += loss
            
            pie_data = [{'name': k, 'value': round(v, 0)} for k, v in reasons.items() if v > 0]
            
            if pie_data:
                option1 = {
                    'title': {'text': '🔍 穿底原因分布', 'left': 'center', 'top': 5, 
                              'textStyle': {'fontSize': 14, 'fontWeight': 'bold'}},
                    'tooltip': {'trigger': 'item', 'formatter': '{b}: ¥{c} ({d}%)'},
                    'legend': {'orient': 'vertical', 'left': 10, 'top': 'middle'},
                    'series': [{
                        'type': 'pie',
                        'radius': ['35%', '65%'],
                        'center': ['60%', '55%'],
                        'data': pie_data,
                        'itemStyle': {'borderRadius': 8, 'borderColor': '#fff', 'borderWidth': 2},
                        'label': {'formatter': '{b}\n¥{c}', 'fontSize': 11},
                        'emphasis': {'itemStyle': {'shadowBlur': 10, 'shadowColor': 'rgba(0,0,0,0.3)'}},
                        'color': ['#FF6B6B', '#FFE66D', '#4ECDC4']
                    }]
                }
                charts.append(dbc.Col(
                    DashECharts(option=option1, style={'height': '280px', 'width': '100%'}),
                    width=6
                ))
        
        # ===== 图表2：各渠道穿底金额对比（柱状图）=====
        if not order_data.empty:
            channel_col = next((c for c in ['渠道', '平台', 'channel'] if c in order_data.columns), None)
            if channel_col and '订单实际利润' in order_data.columns:
                # 按渠道汇总穿底金额
                channel_loss = order_data.groupby(channel_col)['订单实际利润'].apply(
                    lambda x: abs(x[x < 0].sum())
                ).sort_values(ascending=False).head(5)
                
                if not channel_loss.empty:
                    option2 = {
                        'title': {'text': '📊 各渠道穿底金额', 'left': 'center', 'top': 5,
                                  'textStyle': {'fontSize': 14, 'fontWeight': 'bold'}},
                        'tooltip': {'trigger': 'axis', 'formatter': '{b}: ¥{c}'},
                        'grid': {'left': '15%', 'right': '10%', 'top': '20%', 'bottom': '15%'},
                        'xAxis': {'type': 'value', 'axisLabel': {'formatter': '¥{value}'}},
                        'yAxis': {'type': 'category', 'data': channel_loss.index.tolist()[::-1],
                                  'axisLabel': {'fontSize': 11}},
                        'series': [{
                            'type': 'bar',
                            'data': channel_loss.values.tolist()[::-1],
                            'barWidth': '50%',
                            'itemStyle': {
                                'color': {'type': 'linear', 'x': 0, 'y': 0, 'x2': 1, 'y2': 0,
                                          'colorStops': [{'offset': 0, 'color': '#FF6B6B'},
                                                         {'offset': 1, 'color': '#EE5A5A'}]},
                                'borderRadius': [0, 6, 6, 0]
                            },
                            'label': {'show': True, 'position': 'right', 
                                      'formatter': '¥{c}', 'fontSize': 11}
                        }]
                    }
                    charts.append(dbc.Col(
                        DashECharts(option=option2, style={'height': '280px', 'width': '100%'}),
                        width=6
                    ))
        
        if charts:
            return dbc.Row(charts, className="mt-3")
        return html.Div()
    except Exception as e:
        return html.Div(f"图表生成失败: {str(e)}", className="text-muted small mt-2")


def get_overflow_export_data(df: pd.DataFrame) -> dict:
    """
    获取穿底数据导出（多sheet格式）
    
    返回格式: dict，key为sheet名称，value为DataFrame
    - 汇总: 穿底商品汇总
    - 美团/饿了么/抖音等: 按渠道分sheet的商品明细
    - 订单明细: 穿底订单列表
    """
    from io import BytesIO
    
    result = {}
    
    # 获取商品视图数据（完整数据，包含渠道信息）
    product_data = get_overflow_products_with_channel(df)
    order_data = get_overflow_orders(df)
    
    if product_data.empty and order_data.empty:
        return None
    
    # Sheet1: 商品汇总（不分渠道）
    if not product_data.empty:
        # 汇总视图（去掉渠道列）
        summary_cols = [c for c in product_data.columns if c != '渠道']
        result['商品汇总'] = product_data[summary_cols].drop_duplicates(subset=['商品名称'])
        
        # 按渠道分sheet
        if '渠道' in product_data.columns:
            for channel in product_data['渠道'].dropna().unique():
                channel_data = product_data[product_data['渠道'] == channel].copy()
                if not channel_data.empty:
                    # 渠道sheet去掉渠道列
                    channel_cols = [c for c in channel_data.columns if c != '渠道']
                    result[f'{channel}'] = channel_data[channel_cols]
    
    # 最后一个sheet: 订单明细
    if not order_data.empty:
        result['订单明细'] = order_data
    
    return result


def get_overflow_products_with_channel(df: pd.DataFrame) -> pd.DataFrame:
    """
    获取穿底商品分析（带渠道信息，用于导出）
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    try:
        import numpy as np
        
        date_col = '日期' if '日期' in df.columns else '下单时间'
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        yesterday = df[date_col].max().normalize()
        yesterday_df = df[df[date_col].dt.normalize() == yesterday]
        
        if yesterday_df.empty:
            return pd.DataFrame()
        
        order_id_col = '订单ID' if '订单ID' in yesterday_df.columns else None
        channel_col = next((c for c in ['平台', '渠道', 'platform'] if c in yesterday_df.columns), None)
        
        if not order_id_col or '商品名称' not in yesterday_df.columns:
            return pd.DataFrame()
        
        # 计算订单实际利润
        from .diagnosis_analysis import calculate_order_profit
        
        order_agg_dict = {}
        if '利润额' in yesterday_df.columns:
            order_agg_dict['利润额'] = pd.NamedAgg(column='利润额', aggfunc='sum')
        if '平台服务费' in yesterday_df.columns:
            order_agg_dict['平台服务费'] = pd.NamedAgg(column='平台服务费', aggfunc='sum')
        if '企客后返' in yesterday_df.columns:
            order_agg_dict['企客后返'] = pd.NamedAgg(column='企客后返', aggfunc='sum')
        if '物流配送费' in yesterday_df.columns:
            order_agg_dict['物流配送费'] = pd.NamedAgg(column='物流配送费', aggfunc='first')
        
        if not order_agg_dict:
            return pd.DataFrame()
        
        order_data = yesterday_df.groupby(order_id_col).agg(**order_agg_dict).reset_index()
        order_data['订单实际利润'] = calculate_order_profit(order_data)
        
        # 筛选穿底订单
        overflow_mask = (order_data['订单实际利润'] < 0)
        if '利润额' in order_data.columns:
            overflow_mask = overflow_mask & (order_data['利润额'] != 0)
        overflow_order_ids = order_data[overflow_mask][order_id_col].tolist()
        
        if not overflow_order_ids:
            return pd.DataFrame()
        
        # 获取穿底订单商品明细
        overflow_items = yesterday_df[yesterday_df[order_id_col].isin(overflow_order_ids)].copy()
        
        sales_field = '月售' if '月售' in overflow_items.columns else '销量'
        if sales_field not in overflow_items.columns:
            overflow_items[sales_field] = 1
        
        # 准备聚合字段
        if '商品原价' in overflow_items.columns:
            overflow_items['_商品原价'] = overflow_items['商品原价'].fillna(0)
        else:
            overflow_items['_商品原价'] = 0
        
        if '商品实售价' in overflow_items.columns:
            overflow_items['_商品实售价'] = overflow_items['商品实售价'].fillna(0)
        else:
            overflow_items['_商品实售价'] = 0
        
        if '实收价格' in overflow_items.columns:
            overflow_items['_实收价格'] = overflow_items['实收价格'].fillna(0)
        else:
            overflow_items['_实收价格'] = 0
        
        cost_col = '商品采购成本' if '商品采购成本' in overflow_items.columns else '成本'
        if cost_col in overflow_items.columns:
            overflow_items['单品成本'] = overflow_items[cost_col].fillna(0)
            overflow_items['商品成本'] = overflow_items[cost_col].fillna(0) * overflow_items[sales_field].fillna(1)
        else:
            overflow_items['单品成本'] = 0
            overflow_items['商品成本'] = 0
        
        overflow_items['商品销售额'] = overflow_items['_实收价格'] * overflow_items[sales_field].fillna(1)
        overflow_items['商品毛利'] = overflow_items['商品销售额'] - overflow_items['商品成本']
        
        # 按渠道+商品聚合
        group_cols = ['商品名称']
        if channel_col:
            group_cols = [channel_col, '商品名称']
        
        category_col = '一级分类名' if '一级分类名' in overflow_items.columns else '一级分类'
        category3_col = '三级分类名' if '三级分类名' in overflow_items.columns else '三级分类'
        
        agg_dict = {
            '穿底订单数': pd.NamedAgg(column=order_id_col, aggfunc='nunique'),
            '订单ID': pd.NamedAgg(column=order_id_col, aggfunc=lambda x: '\n'.join(x.astype(str).unique())),
            '穿底销量': pd.NamedAgg(column=sales_field, aggfunc='sum'),
            '商品原价': pd.NamedAgg(column='_商品原价', aggfunc='max'),
            '商品实售价': pd.NamedAgg(column='_商品实售价', aggfunc='mean'),
            '实收价格': pd.NamedAgg(column='_实收价格', aggfunc='mean'),
            '单品成本': pd.NamedAgg(column='单品成本', aggfunc='first'),
            '商品毛利': pd.NamedAgg(column='商品毛利', aggfunc='sum'),
        }
        
        if category_col in overflow_items.columns:
            agg_dict['一级分类'] = pd.NamedAgg(column=category_col, aggfunc='first')
        if category3_col in overflow_items.columns:
            agg_dict['三级分类'] = pd.NamedAgg(column=category3_col, aggfunc='first')
        
        # 店内码
        if '店内码' in overflow_items.columns:
            agg_dict['店内码'] = pd.NamedAgg(column='店内码', aggfunc='first')
        
        product_agg = overflow_items.groupby(group_cols).agg(**agg_dict).reset_index()
        
        # 重命名渠道列
        if channel_col and channel_col in product_agg.columns:
            product_agg = product_agg.rename(columns={channel_col: '渠道'})
        
        # 计算毛利率
        product_agg['定价毛利率'] = np.where(
            product_agg['商品原价'] > 0,
            ((product_agg['商品原价'] - product_agg['单品成本']) / product_agg['商品原价'] * 100).round(1),
            0
        )
        product_agg['实收毛利率'] = np.where(
            product_agg['实收价格'] > 0,
            ((product_agg['实收价格'] - product_agg['单品成本']) / product_agg['实收价格'] * 100).round(1),
            0
        )
        product_agg['穿底贡献'] = product_agg['商品毛利']
        
        # 过滤耗材
        if '一级分类' in product_agg.columns:
            product_agg = product_agg[product_agg['一级分类'] != '耗材'].copy()
        
        # 排序
        product_agg = product_agg.sort_values('穿底贡献', ascending=True)
        
        # 选择展示列
        display_cols = ['渠道', '一级分类', '三级分类', '店内码', '商品名称', '穿底订单数', '订单ID', '穿底销量',
                        '商品原价', '商品实售价', '实收价格', '单品成本', '定价毛利率', '实收毛利率', '穿底贡献']
        display_cols = [c for c in display_cols if c in product_agg.columns]
        
        return product_agg[display_cols]
        
    except Exception as e:
        print(f"get_overflow_products_with_channel 错误: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def get_overflow_products_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取穿底商品导出数据"""
    return get_overflow_products(df)


def create_delivery_detail_table(df: pd.DataFrame) -> html.Div:
    """创建高配送费订单详情表格（优化版）"""
    data = get_high_delivery_orders(df)
    if data.empty:
        return dbc.Alert("暂无高配送费订单数据", color="info")
    
    # 计算配送溢价总额
    total_extra = data['配送溢价'].sum() if '配送溢价' in data.columns else 0
    
    return html.Div([
        html.Div([
            html.Span([
                html.I(className="bi bi-truck me-2 text-warning"),
                f"共 ",
                html.Span(f"{len(data)}笔", className="fw-bold text-warning"),
                f" 配送净成本>6元订单，配送溢价合计 ",
                html.Span(f"¥{total_extra:,.2f}", className="fw-bold text-warning")
            ])
        ], className="mb-3 p-2 bg-warning bg-opacity-10 rounded"),
        dash_table.DataTable(
            data=data.head(50).to_dict('records'),
            columns=[
                {'name': c, 'id': c, 'type': 'numeric', 'format': {'specifier': ',.2f'}} 
                if c in ['销售额', '成本', '配送净成本', '订单实际利润', '配送溢价'] 
                else {'name': c, 'id': c} 
                for c in data.columns
            ],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_cell_conditional=[
                {'if': {'column_id': '风险提示'}, 'whiteSpace': 'pre-line', 'minWidth': '200px', 'maxWidth': '300px'}
            ],
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'column_id': '配送净成本'}, 'color': '#fd7e14', 'fontWeight': 'bold'},
                {'if': {'column_id': '配送溢价'}, 'color': '#dc3545', 'fontWeight': 'bold'},
                {'if': {'column_id': '风险提示'}, 'color': '#6c757d', 'fontSize': '12px'},
            ],
            page_size=10
        ),
        html.Div([
            html.Small([
                html.Strong("📌 定义提示："),
                "配送净成本 = 物流配送费 - (用户支付配送费 - 配送费减免) - 企客后返；",
                "配送溢价 = 配送净成本 - 6元（超过6元的部分）"
            ], className="text-muted d-block"),
            html.Small([
                html.Strong("📝 判断标准："),
                "配送净成本 > 6元 且 订单实际利润 < 配送净成本（高配送费吃掉利润）"
            ], className="text-muted d-block mt-1"),
        ], className="mt-2 p-2 bg-light rounded")
    ])


def get_delivery_export_data(df: pd.DataFrame) -> dict:
    """
    获取高配送费订单导出数据（多sheet格式，按渠道分sheet）
    
    返回格式: dict，key为sheet名称，value为DataFrame
    """
    data = get_high_delivery_orders(df)
    
    if data.empty:
        return None
    
    result = {}
    
    # Sheet1: 汇总数据
    result['高配送费订单汇总'] = data.copy()
    
    # 按渠道分sheet
    if '渠道' in data.columns:
        for channel in data['渠道'].dropna().unique():
            channel_data = data[data['渠道'] == channel].copy()
            if not channel_data.empty:
                safe_name = str(channel)[:31].replace('/', '_').replace('\\', '_')
                result[safe_name] = channel_data
    
    return result


def create_stockout_detail_table(df: pd.DataFrame) -> html.Div:
    """创建热销缺货商品详情表格"""
    data = get_stockout_products(df)
    if data.empty:
        return dbc.Alert("暂无热销缺货商品数据（需要至少2天数据）", color="info")
    
    # 移除日均销量列
    if '日均销量' in data.columns:
        data = data.drop(columns=['日均销量'])
    
    # 判断使用的是库存逻辑还是销量逻辑
    use_stock_logic = '昨日库存' in data.columns
    
    # 检测统计天数（从列名推断）
    stat_days = 7  # 默认
    for col in data.columns:
        if '天销量' in col and col != '7天销量':
            try:
                stat_days = int(col.replace('天销量', ''))
            except:
                pass
            break
    
    if use_stock_logic:
        description = html.Div([
            html.Span([
                html.I(className="bi bi-box-seam me-2 text-danger"),
                f"共 ",
                html.Span(f"{len(data)}", className="fw-bold text-danger"),
                f" 个热销商品昨日库存为0"
            ])
        ], className="mb-3 p-2 bg-danger bg-opacity-10 rounded")
        tip_text = f"💡 判断标准：近{stat_days}天有销量 且 昨日剩余库存=0"
    else:
        description = html.Div([
            html.Span([
                html.I(className="bi bi-box-seam me-2 text-danger"),
                f"共 ",
                html.Span(f"{len(data)}", className="fw-bold text-danger"),
                f" 个热销商品昨日零销量"
            ])
        ], className="mb-3 p-2 bg-danger bg-opacity-10 rounded")
        tip_text = "💡 判断标准：前日销量≥3 且 昨日销量=0（无库存字段，使用销量逻辑）"
    
    # 动态设置列样式
    style_data_conditional = [
        {'if': {'column_id': '昨日库存'}, 'color': 'red', 'fontWeight': 'bold'},
        {'if': {'column_id': '昨日销量'}, 'color': 'red', 'fontWeight': 'bold'},
        {'if': {'column_id': '总利润额'}, 'color': '#28a745', 'fontWeight': 'bold'},
        {'if': {'column_id': '总利润率'}, 'color': '#17a2b8', 'fontWeight': 'bold'},
        {'if': {'column_id': '建议补货'}, 'color': '#fd7e14', 'fontWeight': 'bold'},
        {'if': {'column_id': '主渠道'}, 'color': '#6f42c1', 'fontWeight': 'bold'},
    ]
    # 动态添加销量列高亮
    for col in data.columns:
        if '天销量' in col:
            style_data_conditional.append({'if': {'column_id': col}, 'color': 'green', 'fontWeight': 'bold'})
    
    # 格式化数值列
    columns = []
    for c in data.columns:
        if c == '总利润额':
            columns.append({'name': c, 'id': c, 'type': 'numeric', 'format': {'specifier': ',.2f'}})
        elif '天销量' in c:
            # 销量显示为整数，不要小数点
            columns.append({'name': c, 'id': c, 'type': 'numeric', 'format': {'specifier': ',.0f'}})
        elif c == '建议补货':
            columns.append({'name': c, 'id': c, 'type': 'numeric', 'format': {'specifier': ',.0f'}})
        else:
            columns.append({'name': c, 'id': c})
    
    return html.Div([
        description,
        dash_table.DataTable(
            data=data.head(50).to_dict('records'),
            columns=columns,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=style_data_conditional,
            page_size=10
        ),
        html.Div([
            html.Small(tip_text, className="text-muted d-block"),
            html.Small("📦 建议补货 = (N天销量÷N) × 3天安全库存，至少补1个", className="text-muted d-block mt-1")
        ], className="mt-2 p-2 bg-light rounded")
    ])

def get_stockout_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取热销缺货商品导出数据"""
    return get_stockout_products(df)


def create_traffic_drop_detail_table(df: pd.DataFrame) -> html.Div:
    """创建流量异常商品详情表格（7日 vs 7日对比）+ 可视化图表"""
    data = get_traffic_drop_products(df)
    if data.empty:
        return dbc.Alert("暂无流量异常商品数据（需要至少14天数据）", color="info")
    
    # 只移除日均列，保留销量列
    drop_cols = ['前7天日均', '近7天日均']
    data = data.drop(columns=[c for c in drop_cols if c in data.columns], errors='ignore')
    
    # 描述区域
    description = html.Div([
        html.Span([
            html.I(className="bi bi-graph-down me-2 text-warning"),
            f"共 ",
            html.Span(f"{len(data)}", className="fw-bold text-warning"),
            f" 个热销商品销量持续下滑"
        ])
    ], className="mb-3 p-2 bg-warning bg-opacity-10 rounded")
    
    # 动态设置列样式
    style_data_conditional = [
        {'if': {'column_id': '跌幅'}, 'color': 'red', 'fontWeight': 'bold'},
        {'if': {'column_id': '前7天销量'}, 'color': 'green', 'fontWeight': 'bold'},
        {'if': {'column_id': '近7天销量'}, 'color': '#fd7e14', 'fontWeight': 'bold'},
        {'if': {'column_id': '总利润额'}, 'color': '#28a745', 'fontWeight': 'bold'},
        {'if': {'column_id': '总利润率'}, 'color': '#17a2b8', 'fontWeight': 'bold'},
        {'if': {'column_id': '主渠道'}, 'color': '#6f42c1', 'fontWeight': 'bold'},
    ]
    
    # 格式化数值列
    columns = []
    for c in data.columns:
        if c in ['总利润额', '前7天销量', '近7天销量']:
            columns.append({'name': c, 'id': c, 'type': 'numeric', 'format': {'specifier': ',.0f'}})
        elif c == '跌幅':
            columns.append({'name': c + '%', 'id': c, 'type': 'numeric', 'format': {'specifier': ',.1f'}})
        else:
            columns.append({'name': c, 'id': c})
    
    # ========== 可视化图表 (ECharts) ==========
    charts_section = html.Div()
    if ECHARTS_AVAILABLE:
        try:
            charts = []
            
            # ===== 图表1：按分类统计下滑商品数（找出问题分类）=====
            category_col = '一级分类名' if '一级分类名' in data.columns else None
            if category_col:
                category_counts = data[category_col].value_counts().head(8)
                if not category_counts.empty:
                    option1 = {
                        'title': {'text': '🔍 哪些分类下滑最多', 'left': 'center', 'top': 5,
                                  'textStyle': {'fontSize': 14, 'fontWeight': 'bold'}},
                        'tooltip': {'trigger': 'axis'},
                        'grid': {'left': '20%', 'right': '10%', 'top': '18%', 'bottom': '10%'},
                        'xAxis': {'type': 'value'},
                        'yAxis': {'type': 'category', 'data': category_counts.index.tolist()[::-1],
                                  'axisLabel': {'fontSize': 11, 'width': 80, 'overflow': 'truncate'}},
                        'series': [{
                            'type': 'bar',
                            'data': category_counts.values.tolist()[::-1],
                            'barWidth': '50%',
                            'itemStyle': {
                                'color': {'type': 'linear', 'x': 0, 'y': 0, 'x2': 1, 'y2': 0,
                                          'colorStops': [{'offset': 0, 'color': '#FF9800'},
                                                         {'offset': 1, 'color': '#FF6B6B'}]},
                                'borderRadius': [0, 6, 6, 0]
                            },
                            'label': {'show': True, 'position': 'right', 'fontSize': 12}
                        }]
                    }
                    charts.append(dbc.Col(
                        DashECharts(option=option1, style={'height': '280px', 'width': '100%'}),
                        width=6
                    ))
            
            # ===== 图表2：跌幅严重度分布（环形图）=====
            if '跌幅' in data.columns:
                # 按跌幅分级
                severe = len(data[data['跌幅'].abs() > 60])
                medium = len(data[(data['跌幅'].abs() > 40) & (data['跌幅'].abs() <= 60)])
                light = len(data[data['跌幅'].abs() <= 40])
                
                pie_data = [
                    {'name': '严重(>60%)', 'value': severe},
                    {'name': '中度(40-60%)', 'value': medium},
                    {'name': '轻度(<40%)', 'value': light}
                ]
                
                option2 = {
                    'title': {'text': '⚠️ 下滑严重度分布', 'left': 'center', 'top': 5,
                              'textStyle': {'fontSize': 14, 'fontWeight': 'bold'}},
                    'tooltip': {'trigger': 'item', 'formatter': '{b}: {c}个 ({d}%)'},
                    'legend': {'orient': 'vertical', 'left': 10, 'top': 'middle'},
                    'series': [{
                        'type': 'pie',
                        'radius': ['35%', '65%'],
                        'center': ['60%', '55%'],
                        'data': pie_data,
                        'itemStyle': {'borderRadius': 8, 'borderColor': '#fff', 'borderWidth': 2},
                        'label': {'formatter': '{b}\n{c}个', 'fontSize': 11},
                        'color': ['#F44336', '#FF9800', '#FFC107']
                    }]
                }
                charts.append(dbc.Col(
                    DashECharts(option=option2, style={'height': '280px', 'width': '100%'}),
                    width=6
                ))
            
            if charts:
                charts_section = dbc.Row(charts, className="mt-3")
        except Exception as e:
            charts_section = html.Div(f"图表生成失败: {str(e)}", className="text-muted small")
    
    return html.Div([
        description,
        dash_table.DataTable(
            data=data.head(50).to_dict('records'),
            columns=columns,
            style_table={'overflowX': 'auto', 'maxHeight': '350px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=style_data_conditional,
            page_size=10
        ),
        # 可视化图表区
        charts_section,
        html.Div([
            html.Small("💡 判断标准：前7天日均≥2 且 跌幅>30%", className="text-muted d-block"),
            html.Small("📋 建议检查：库存/下架/竞品/活动变化", className="text-muted d-block mt-1")
        ], className="mt-2 p-2 bg-light rounded")
    ])

def get_traffic_drop_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取流量异常商品导出数据"""
    return get_traffic_drop_products(df)


def create_slow_moving_detail_table(df: pd.DataFrame) -> html.Div:
    """创建滞销商品详情表格"""
    data = get_slow_moving_products(df)
    if data.empty:
        return dbc.Alert("暂无滞销商品数据", color="info")
    
    # 统计各等级数量
    level_counts = data['滞销等级'].value_counts().to_dict()
    
    return html.Div([
        html.P([
            f"共 ",
            html.Span(f"{len(data)}", className="fw-bold text-warning"),
            f" 个滞销商品需关注"
        ], className="mb-2"),
        html.Div([
            html.Span(f"🆕 新增风险: {level_counts.get('🆕 新增风险', 0)}", className="me-3"),
            html.Span(f"⚠️ 持续滞销: {level_counts.get('⚠️ 持续滞销', 0)}", className="me-3"),
            html.Span(f"🔴 严重滞销: {level_counts.get('🔴 严重滞销', 0)}", className="text-danger")
        ], className="mb-3 small"),
        dash_table.DataTable(
            data=data.to_dict('records'),
            columns=[{'name': c, 'id': c} for c in data.columns],
            style_table={'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'filter_query': '{滞销等级} = "🔴 严重滞销"'}, 'backgroundColor': '#ffebee'},
                {'if': {'filter_query': '{滞销等级} = "⚠️ 持续滞销"'}, 'backgroundColor': '#fff8e1'},
                {'if': {'filter_query': '{滞销等级} = "🆕 新增风险"'}, 'backgroundColor': '#e3f2fd'}
            ],
            page_size=20,
            page_action='native',
            sort_action='native'
        ),
        html.Div([
            html.Small([
                html.Strong("📌 定义提示："),
                "滞销天数 = 当前日期 - 最后销售日期；",
                "只统计库存>0的商品（库存=0可能是缺货/下架，不算滞销）"
            ], className="text-muted d-block"),
            html.Small([
                html.Strong("📝 判断标准："),
                "🆕新增风险: 刚满3天无销量；",
                "⚠️持续滞销: 刚满7天无销量；",
                "🔴严重滞销: 刚满15天无销量（只显示状态变化当天的商品，避免重复提醒）"
            ], className="text-muted d-block mt-1"),
        ], className="mt-2 p-2 bg-light rounded")
    ])

def get_slow_moving_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取滞销商品导出数据"""
    return get_slow_moving_products(df)


def create_new_product_detail_table(df: pd.DataFrame) -> html.Div:
    """创建昨日首销商品详情表格"""
    data = get_new_products(df)
    if data.empty:
        return dbc.Alert("暂无昨日首销商品数据", color="info")
    
    total_sales = data['首日销售额'].sum() if '首日销售额' in data.columns else 0
    total_qty = data['首日销量'].sum() if '首日销量' in data.columns else 0
    total_profit = data['首日利润'].sum() if '首日利润' in data.columns else 0
    
    # 统计各沉寂等级数量
    level_counts = data['沉寂等级'].value_counts().to_dict() if '沉寂等级' in data.columns else {}
    short_count = level_counts.get('🟢 短期沉寂', 0)
    mid_count = level_counts.get('🟡 中期沉寂', 0)
    long_count = level_counts.get('🔴 长期沉寂', 0)
    
    return html.Div([
        html.P([
            f"昨日首销 ",
            html.Span(f"{len(data)}", className="fw-bold text-success"),
            f" 个商品，共销售 ",
            html.Span(f"{total_qty}", className="fw-bold text-success"),
            f" 件，贡献销售额 ",
            html.Span(f"¥{total_sales:,.2f}", className="fw-bold text-success"),
            f"，贡献利润 ",
            html.Span(f"¥{total_profit:,.2f}", className="fw-bold text-primary")
        ], className="mb-2"),
        html.Div([
            html.Span(f"🟢 短期沉寂(7-14天): {short_count}", className="me-3"),
            html.Span(f"🟡 中期沉寂(15-30天): {mid_count}", className="me-3"),
            html.Span(f"🔴 长期沉寂(30天+): {long_count}", className="text-danger")
        ], className="mb-3 small"),
        dash_table.DataTable(
            data=data.to_dict('records'),
            columns=[{'name': c, 'id': c} for c in data.columns],
            style_table={'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'column_id': '首日销量'}, 'color': 'green', 'fontWeight': 'bold'},
                {'if': {'column_id': '首日销售额'}, 'color': 'green', 'fontWeight': 'bold'},
                {'if': {'column_id': '首日利润'}, 'color': '#1976d2', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{沉寂等级} = "🟢 短期沉寂"'}, 'backgroundColor': '#e8f5e9'},
                {'if': {'filter_query': '{沉寂等级} = "🟡 中期沉寂"'}, 'backgroundColor': '#fff8e1'},
                {'if': {'filter_query': '{沉寂等级} = "🔴 长期沉寂"'}, 'backgroundColor': '#ffebee'}
            ],
            page_size=20,
            page_action='native',
            sort_action='native'
        ),
        html.Div([
            html.Small([
                html.Strong("📌 定义提示："),
                "首日销售额 = 实收价格 × 销量；",
                "首日利润 = 利润额（原始数据）；",
                "沉寂天数 = 上次销售日到昨日的间隔"
            ], className="text-muted d-block"),
            html.Small([
                html.Strong("📝 判断标准："),
                "过去7天无销量 + 昨日有销量（首次动销）；",
                "🟢短期沉寂: 7-14天；🟡中期沉寂: 15-30天；🔴长期沉寂: 30天+"
            ], className="text-muted d-block mt-1"),
        ], className="mt-2 p-2 bg-light rounded")
    ])

def get_new_product_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取新品表现导出数据"""
    return get_new_products(df)


def create_price_abnormal_detail_table(df: pd.DataFrame) -> html.Div:
    """创建价格异常商品详情表格（昨日售价<成本的商品）"""
    data = get_price_abnormal_products(df)
    if data.empty:
        return dbc.Alert("暂无价格异常商品（昨日所有商品售价均高于成本）", color="success")
    
    # 统计各等级数量
    level_counts = data['异常等级'].value_counts().to_dict() if '异常等级' in data.columns else {}
    severe_count = level_counts.get('🔴严重亏损', 0)
    mild_count = level_counts.get('🟠轻度亏损', 0)
    
    # 统计总亏损
    total_loss = data['预估总亏损'].sum() if '预估总亏损' in data.columns else 0
    
    return html.Div([
        html.P([
            f"昨日发现 ",
            html.Span(f"{len(data)}", className="fw-bold text-danger"),
            f" 个价格异常商品（售价低于成本）",
            f"，预估总亏损 ",
            html.Span(f"¥{total_loss:,.2f}", className="fw-bold text-danger")
        ], className="mb-2"),
        html.Div([
            html.Span(f"🔴 严重亏损(售价<成本80%): {severe_count}", className="me-3 text-danger"),
            html.Span(f"🟠 轻度亏损(80%≤售价<成本): {mild_count}", className="me-3")
        ], className="mb-3 small"),
        dash_table.DataTable(
            data=data.to_dict('records'),
            columns=[{'name': c, 'id': c} for c in data.columns],
            style_table={'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'column_id': '单位亏损'}, 'fontWeight': 'bold', 'color': 'red'},
                {'if': {'column_id': '预估总亏损'}, 'fontWeight': 'bold', 'color': 'red'},
                {'if': {'filter_query': '{异常等级} = "🔴严重亏损"'}, 'backgroundColor': '#ffebee'},
                {'if': {'filter_query': '{异常等级} = "🟠轻度亏损"'}, 'backgroundColor': '#fff3e0'}
            ],
            page_size=20,
            page_action='native',
            sort_action='native'
        ),
        html.Div([
            html.Small([
                html.Strong("📌 定义提示："),
                "价格异常 = 售价低于成本；数据范围：昨日订单"
            ], className="text-muted d-block"),
            html.Small([
                html.Strong("📝 判断标准："),
                "实收价格 < 单品成本（卖一单亏一单）；",
                "🔴严重亏损: 实收价格 < 单品成本×0.8；",
                "🟠轻度亏损: 单品成本×0.8 ≤ 实收价格 < 单品成本"
            ], className="text-muted d-block mt-1"),
            html.Small([
                html.Strong("📊 核心公式："),
                "单品成本 = 商品采购成本 ÷ 销量；",
                "单位亏损 = 单品成本 - 实收价格；",
                "预估总亏损 = 单位亏损 × 销量；",
                "定价毛利率 = (商品原价 - 单品成本) ÷ 商品原价 × 100%；",
                "实收毛利率 = (实收价格 - 单品成本) ÷ 实收价格 × 100%"
            ], className="text-muted d-block mt-1"),
        ], className="mt-2 p-2 bg-light rounded")
    ])


def get_price_abnormal_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取价格异常商品导出数据"""
    return get_price_abnormal_products(df)


def create_profit_drop_detail_table(df: pd.DataFrame) -> html.Div:
    """创建利润率下滑商品详情表格（近7天vs前7天，下滑>10%）+ 可视化图表"""
    data = get_profit_rate_drop_products(df)
    if data.empty:
        return dbc.Alert("暂无利润率下滑商品（近7天利润率下滑均<10个百分点）", color="success")
    
    # 统计各等级数量
    level_counts = data['下滑等级'].value_counts().to_dict() if '下滑等级' in data.columns else {}
    crash_count = level_counts.get('🔴暴跌', 0)
    major_count = level_counts.get('🟠大幅下滑', 0)
    
    # ========== 可视化图表 (ECharts) ==========
    charts_section = html.Div()
    if ECHARTS_AVAILABLE:
        try:
            charts = []
            
            # ===== 图表1：利润率下滑原因分析（按分类统计）=====
            category_col = '一级分类名' if '一级分类名' in data.columns else None
            if category_col:
                # 按分类统计下滑商品数和平均下滑幅度
                category_stats = data.groupby(category_col).agg({
                    '商品名称': 'count',
                    '利润率变化': lambda x: x.apply(lambda v: float(str(v).replace('%', '').replace('pp', '')) if pd.notna(v) else 0).mean()
                }).rename(columns={'商品名称': '下滑商品数'}).sort_values('下滑商品数', ascending=False).head(6)
                
                if not category_stats.empty:
                    option1 = {
                        'title': {'text': '🔍 各分类利润下滑情况', 'left': 'center', 'top': 5,
                                  'textStyle': {'fontSize': 14, 'fontWeight': 'bold'}},
                        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
                        'grid': {'left': '20%', 'right': '10%', 'top': '18%', 'bottom': '10%'},
                        'xAxis': {'type': 'value', 'name': '下滑商品数'},
                        'yAxis': {'type': 'category', 'data': category_stats.index.tolist()[::-1],
                                  'axisLabel': {'fontSize': 11, 'width': 80, 'overflow': 'truncate'}},
                        'series': [{
                            'type': 'bar',
                            'data': category_stats['下滑商品数'].values.tolist()[::-1],
                            'barWidth': '50%',
                            'itemStyle': {
                                'color': {'type': 'linear', 'x': 0, 'y': 0, 'x2': 1, 'y2': 0,
                                          'colorStops': [{'offset': 0, 'color': '#FF9800'},
                                                         {'offset': 1, 'color': '#F44336'}]},
                                'borderRadius': [0, 6, 6, 0]
                            },
                            'label': {'show': True, 'position': 'right', 'fontSize': 12}
                        }]
                    }
                    charts.append(dbc.Col(
                        DashECharts(option=option1, style={'height': '280px', 'width': '100%'}),
                        width=6
                    ))
            
            # ===== 图表2：下滑等级分布（环形图）=====
            pie_data = [
                {'name': '🔴 暴跌(>20%)', 'value': crash_count},
                {'name': '🟠 大幅下滑(10-20%)', 'value': major_count}
            ]
            
            option2 = {
                'title': {'text': '⚠️ 下滑严重度分布', 'left': 'center', 'top': 5,
                          'textStyle': {'fontSize': 14, 'fontWeight': 'bold'}},
                'tooltip': {'trigger': 'item', 'formatter': '{b}: {c}个 ({d}%)'},
                'legend': {'orient': 'vertical', 'left': 10, 'top': 'middle'},
                'series': [{
                    'type': 'pie',
                    'radius': ['35%', '65%'],
                    'center': ['60%', '55%'],
                    'data': pie_data,
                    'itemStyle': {'borderRadius': 8, 'borderColor': '#fff', 'borderWidth': 2},
                    'label': {'formatter': '{b}\n{c}个', 'fontSize': 11},
                    'color': ['#F44336', '#FF9800']
                }]
            }
            charts.append(dbc.Col(
                DashECharts(option=option2, style={'height': '280px', 'width': '100%'}),
                width=6
            ))
            
            if charts:
                charts_section = dbc.Row(charts, className="mt-3")
        except Exception as e:
            charts_section = html.Div(f"图表生成失败: {str(e)}", className="text-muted small")
    
    return html.Div([
        html.P([
            f"发现 ",
            html.Span(f"{len(data)}", className="fw-bold text-warning"),
            f" 个利润率下滑商品（近7天vs前7天，下滑>10个百分点）"
        ], className="mb-2"),
        html.Div([
            html.Span(f"🔴 暴跌(下滑>20%): {crash_count}", className="me-3 text-danger"),
            html.Span(f"🟠 大幅下滑(10-20%): {major_count}", className="me-3")
        ], className="mb-3 small"),
        dash_table.DataTable(
            data=data.to_dict('records'),
            columns=[{'name': c, 'id': c} for c in data.columns],
            style_table={'overflowX': 'auto', 'maxHeight': '350px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'column_id': '利润率变化'}, 'fontWeight': 'bold', 'color': 'red'},
                {'if': {'filter_query': '{下滑等级} = "🔴暴跌"'}, 'backgroundColor': '#ffebee'},
                {'if': {'filter_query': '{下滑等级} = "🟠大幅下滑"'}, 'backgroundColor': '#fff3e0'}
            ],
            page_size=15,
            page_action='native',
            sort_action='native'
        ),
        # 可视化图表区
        charts_section,
        html.Div([
            html.Small([
                html.Strong("📌 定义提示："),
                "利润率下滑 = 近7天利润率比前7天下降超过10个百分点"
            ], className="text-muted d-block"),
            html.Small([
                html.Strong("📝 判断标准："),
                "近7天利润率 - 前7天利润率 < -10%（下滑超过10个百分点）；",
                "🔴暴跌: 下滑>20%；",
                "🟠大幅下滑: 下滑10-20%"
            ], className="text-muted d-block mt-1"),
        ], className="mt-2 p-2 bg-light rounded")
    ])


def get_profit_drop_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取利润率下滑商品导出数据"""
    return get_profit_rate_drop_products(df)


def create_hot_products_detail_table(df: pd.DataFrame) -> html.Div:
    """创建爆款商品详情表格（昨日销量突增的商品）"""
    data = get_hot_products(df)
    if data.empty:
        return dbc.Alert("暂无爆款商品（昨日无销量环比增长>50%且销量>=10的商品）", color="info")
    
    # 统计各等级数量
    level_counts = data['爆款等级'].value_counts().to_dict() if '爆款等级' in data.columns else {}
    super_hot = level_counts.get('🔥🔥🔥', 0)
    very_hot = level_counts.get('🔥🔥', 0)
    hot = level_counts.get('🔥', 0)
    
    # 统计总销量和销售额
    total_qty = data['昨日销量'].sum() if '昨日销量' in data.columns else 0
    total_sales = data['昨日销售额'].sum() if '昨日销售额' in data.columns else 0
    
    return html.Div([
        html.P([
            f"昨日发现 ",
            html.Span(f"{len(data)}", className="fw-bold text-success"),
            f" 个爆款商品，共销售 ",
            html.Span(f"{total_qty}", className="fw-bold text-success"),
            f" 件，贡献销售额 ",
            html.Span(f"¥{total_sales:,.2f}", className="fw-bold text-success")
        ], className="mb-2"),
        html.Div([
            html.Span(f"🔥🔥🔥 超级爆款(+200%): {super_hot}", className="me-3 text-danger fw-bold"),
            html.Span(f"🔥🔥 热销(+100%): {very_hot}", className="me-3 text-warning"),
            html.Span(f"🔥 增长(+50%): {hot}", className="me-3")
        ], className="mb-3 small"),
        dash_table.DataTable(
            data=data.to_dict('records'),
            columns=[{'name': c, 'id': c} for c in data.columns],
            style_table={'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'column_id': '昨日销量'}, 'fontWeight': 'bold', 'color': 'green'},
                {'if': {'column_id': '增长率'}, 'fontWeight': 'bold', 'color': '#28a745'},
                {'if': {'column_id': '昨日利润'}, 'fontWeight': 'bold', 'color': '#1976d2'},
                {'if': {'filter_query': '{爆款等级} = "🔥🔥🔥"'}, 'backgroundColor': '#fff3e0'},
                {'if': {'filter_query': '{爆款等级} = "🔥🔥"'}, 'backgroundColor': '#fffde7'},
            ],
            page_size=20,
            page_action='native',
            sort_action='native'
        ),
        html.Div([
            html.Small([
                html.Strong("📌 定义提示："),
                "爆款 = 昨日销量环比增长>50% 且 昨日销量>=10；数据范围：昨日vs前日"
            ], className="text-muted d-block"),
            html.Small([
                html.Strong("📝 爆款等级："),
                "🔥🔥🔥超级爆款: 增长>200%；",
                "🔥🔥热销: 增长>100%；",
                "🔥增长: 增长>50%"
            ], className="text-muted d-block mt-1"),
        ], className="mt-2 p-2 bg-light rounded")
    ])


def get_hot_products_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取爆款商品导出数据"""
    return get_hot_products(df)


def create_high_profit_detail_table(df: pd.DataFrame) -> html.Div:
    """创建高利润商品详情表格（昨日利润贡献TOP商品）"""
    data = get_high_profit_products(df)
    if data.empty:
        return dbc.Alert("暂无高利润商品数据", color="info")
    
    # 统计
    total_profit = data['昨日利润'].sum() if '昨日利润' in data.columns else 0
    total_sales = data['昨日销售额'].sum() if '昨日销售额' in data.columns else 0
    avg_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
    
    return html.Div([
        html.P([
            f"昨日利润TOP ",
            html.Span(f"{len(data)}", className="fw-bold text-primary"),
            f" 商品，贡献利润 ",
            html.Span(f"¥{total_profit:,.2f}", className="fw-bold text-primary"),
            f"，平均利润率 ",
            html.Span(f"{avg_rate:.1f}%", className="fw-bold text-success")
        ], className="mb-3"),
        dash_table.DataTable(
            data=data.to_dict('records'),
            columns=[{'name': c, 'id': c} for c in data.columns],
            style_table={'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'column_id': '昨日利润'}, 'fontWeight': 'bold', 'color': '#1976d2'},
                {'if': {'column_id': '利润率'}, 'fontWeight': 'bold', 'color': '#28a745'},
                {'if': {'column_id': '排名'}, 'fontWeight': 'bold'},
                {'if': {'filter_query': '{排名} contains "🥇"'}, 'backgroundColor': '#fff8e1'},
                {'if': {'filter_query': '{排名} contains "🥈"'}, 'backgroundColor': '#f5f5f5'},
                {'if': {'filter_query': '{排名} contains "🥉"'}, 'backgroundColor': '#fff3e0'},
            ],
            page_size=20,
            page_action='native',
            sort_action='native'
        ),
        html.Div([
            html.Small([
                html.Strong("📌 定义提示："),
                "高利润商品 = 昨日利润额>0 且 销量>=3；按利润额排序取TOP30"
            ], className="text-muted d-block"),
            html.Small([
                html.Strong("📊 核心公式："),
                "利润率 = 利润额 ÷ 销售额 × 100%；",
                "单品成本 = 商品采购成本 ÷ 销量"
            ], className="text-muted d-block mt-1"),
        ], className="mt-2 p-2 bg-light rounded")
    ])


def get_high_profit_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取高利润商品导出数据"""
    return get_high_profit_products(df)


def create_price_elasticity_detail_table(df: pd.DataFrame, sensitivity_filter: str = 'all') -> html.Div:
    """
    创建价格弹性分析详情表格（精简版）
    
    功能：
    1. 自动检测历史价格变动（原价+售价交叉判断）
    2. 计算每次调价的销量弹性
    3. 给出简短建议
    """
    # 检测价格变动
    price_changes = detect_price_changes_from_orders(df)
    
    if price_changes.empty:
        elasticity_summary = get_price_elasticity_summary(df)
        error_msg = elasticity_summary.get('error', '未检测到显著的价格变动记录')
        
        return html.Div([
            dbc.Alert([
                html.H5("📊 暂无价格变动记录", className="mb-2"),
                html.P(error_msg, className="mb-2"),
                html.Hr(),
                html.P("💡 检测条件：原价或售价变动超过5%，且前后各有至少3天数据", className="small text-muted mb-1"),
                html.P("📝 建议导入至少14天订单数据", className="small text-muted"),
            ], color="info")
        ])
    
    # 统计数据
    total_changes = len(price_changes)
    high_count = len(price_changes[price_changes['敏感度'].str.contains('高敏感', na=False)])
    mid_count = len(price_changes[price_changes['敏感度'].str.contains('中敏感', na=False)])
    low_count = len(price_changes[price_changes['敏感度'].str.contains('低敏感', na=False)])
    abnormal_count = len(price_changes[price_changes['敏感度'].str.contains('异常', na=False)])
    
    # 统计调价类型
    type_counts = price_changes['调价类型'].value_counts().to_dict() if '调价类型' in price_changes.columns else {}
    
    # 统计调价效果
    effect_counts = price_changes['调价效果'].value_counts().to_dict() if '调价效果' in price_changes.columns else {}
    success_count = sum(1 for k in effect_counts if '成功' in str(k))
    fail_count = sum(1 for k in effect_counts if '失败' in str(k))
    neutral_count = sum(1 for k in effect_counts if '中性' in str(k))
    
    # 统计售罄商品数
    stockout_count = len(price_changes[price_changes['是否售罄'] == True]) if '是否售罄' in price_changes.columns else 0
    
    # 统计渠道分布
    channel_counts = price_changes['渠道'].value_counts().to_dict() if '渠道' in price_changes.columns else {}
    
    # ===== 准备不同视图的表格数据 =====
    
    # 视图1：基础信息（价格+销量+弹性+库存）- 加入渠道
    basic_cols = ['一级分类', '店内码', '商品名称', '渠道', '变动日期', '调价类型', '原价变动', '售价变动', 
                  '价格变化率', '调价前7日均销量', '调价后7日均销量', '销量变化率', '当前库存', '弹性', '敏感度', '调价效果', '建议']
    
    # 视图2：销售额分析 - 加入渠道
    revenue_cols = ['商品名称', '渠道', '变动日期', '调价类型', '价格变化率', '调价前7日销售额', '调价后7日销售额', '销售额变化率', '当前库存', '调价效果']
    
    # 视图3：利润分析 - 加入渠道
    profit_cols = ['商品名称', '渠道', '变动日期', '调价类型', '价格变化率', '调价前7日利润额', '调价后7日利润额', '利润额变化率', 
                   '调价前毛利率', '调价后毛利率', '毛利率变化', '当前库存', '调价效果']
    
    # 准备基础视图数据
    basic_available = [c for c in basic_cols if c in price_changes.columns]
    basic_data = price_changes[basic_available].copy()
    
    # 准备销售额视图数据
    revenue_available = [c for c in revenue_cols if c in price_changes.columns]
    revenue_data = price_changes[revenue_available].copy() if len(revenue_available) > 3 else pd.DataFrame()
    
    # 准备利润视图数据
    profit_available = [c for c in profit_cols if c in price_changes.columns]
    profit_data = price_changes[profit_available].copy() if len(profit_available) > 3 else pd.DataFrame()
    
    # 格式化日期
    for df_view in [basic_data, revenue_data, profit_data]:
        if not df_view.empty and '变动日期' in df_view.columns:
            df_view['变动日期'] = df_view['变动日期'].astype(str).str[:10]
    
    # 格式化百分比
    pct_cols = ['价格变化率', '销量变化率', '销售额变化率', '利润额变化率']
    for df_view in [basic_data, revenue_data, profit_data]:
        if not df_view.empty:
            for col in pct_cols:
                if col in df_view.columns:
                    df_view[col] = df_view[col].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "-")
    
    # 格式化毛利率
    for df_view in [profit_data]:
        if not df_view.empty:
            for col in ['调价前毛利率', '调价后毛利率']:
                if col in df_view.columns:
                    df_view[col] = df_view[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
            if '毛利率变化' in df_view.columns:
                df_view['毛利率变化'] = df_view['毛利率变化'].apply(lambda x: f"{x:+.1f}pp" if pd.notna(x) else "-")
    
    # 格式化金额
    for df_view in [revenue_data, profit_data]:
        if not df_view.empty:
            for col in ['调价前7日销售额', '调价后7日销售额', '调价前7日利润额', '调价后7日利润额']:
                if col in df_view.columns:
                    df_view[col] = df_view[col].apply(lambda x: f"¥{x:.0f}" if pd.notna(x) else "-")
    
    if '弹性' in basic_data.columns:
        basic_data['弹性'] = basic_data['弹性'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
    
    # 通用表格样式
    common_style_data_conditional = [
        # 敏感度颜色
        {'if': {'filter_query': '{敏感度} contains "高敏感"'}, 'backgroundColor': '#ffebee'},
        {'if': {'filter_query': '{敏感度} contains "中敏感"'}, 'backgroundColor': '#fff8e1'},
        {'if': {'filter_query': '{敏感度} contains "低敏感"'}, 'backgroundColor': '#e8f5e9'},
        {'if': {'filter_query': '{敏感度} contains "异常"'}, 'backgroundColor': '#f3e5f5'},
        # 调价效果颜色
        {'if': {'filter_query': '{调价效果} contains "成功"'}, 'backgroundColor': '#e8f5e9'},
        {'if': {'filter_query': '{调价效果} contains "失败"'}, 'backgroundColor': '#ffebee'},
        {'if': {'filter_query': '{调价效果} contains "中性"'}, 'backgroundColor': '#fff8e1'},
        # 调价类型颜色
        {'if': {'filter_query': '{调价类型} = "主动调价"'}, 'color': '#1565c0'},
        {'if': {'filter_query': '{调价类型} = "促销/活动"'}, 'color': '#f57c00'},
    ]
    
    return html.Div([
        # 汇总统计卡片
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Span(f"📊 {total_changes}", className="fw-bold text-primary"),
                    html.Span(" 次调价", className="small text-muted")
                ], className="p-2 bg-light rounded text-center")
            ], width=2),
            dbc.Col([
                html.Div([
                    html.Span(f"🔴 {high_count}", className="fw-bold text-danger"),
                    html.Span(" 高敏感", className="small text-muted")
                ], className="p-2 bg-danger bg-opacity-10 rounded text-center")
            ], width=2),
            dbc.Col([
                html.Div([
                    html.Span(f"🟡 {mid_count}", className="fw-bold text-warning"),
                    html.Span(" 中敏感", className="small text-muted")
                ], className="p-2 bg-warning bg-opacity-10 rounded text-center")
            ], width=2),
            dbc.Col([
                html.Div([
                    html.Span(f"🟢 {low_count}", className="fw-bold text-success"),
                    html.Span(" 低敏感", className="small text-muted")
                ], className="p-2 bg-success bg-opacity-10 rounded text-center")
            ], width=2),
            dbc.Col([
                html.Div([
                    html.Span(f"🟣 {abnormal_count}", className="fw-bold text-secondary"),
                    html.Span(" 异常", className="small text-muted")
                ], className="p-2 bg-secondary bg-opacity-10 rounded text-center")
            ], width=2),
            dbc.Col([
                html.Div([
                    html.Span(f"⚠️ {stockout_count}", className="fw-bold text-info"),
                    html.Span(" 售罄", className="small text-muted")
                ], className="p-2 bg-info bg-opacity-10 rounded text-center")
            ], width=2),
        ], className="mb-2 g-1"),
        
        # 调价类型和效果统计
        html.Div([
            html.Small([
                html.Strong("📋 调价类型："),
                f"主动调价 {type_counts.get('主动调价', 0)} 次 | ",
                f"促销/活动 {type_counts.get('促销/活动', 0)} 次",
                html.Span(" ｜ ", className="mx-2"),
                html.Strong("📈 调价效果："),
                html.Span(f"✅成功 {effect_counts.get('✅ 调价成功', 0)} ", className="text-success"),
                html.Span(f"⚠️中性 {effect_counts.get('⚠️ 调价中性', 0)} ", className="text-warning"),
                html.Span(f"❌失败 {effect_counts.get('❌ 调价失败', 0)}", className="text-danger"),
            ])
        ], className="mb-3"),
        
        # Tab切换不同视图
        dbc.Tabs([
            # Tab1: 基础视图（价格+销量+弹性）
            dbc.Tab(label="📊 价格弹性分析", tab_id="tab-basic", children=[
                dash_table.DataTable(
                    data=basic_data.to_dict('records'),
                    columns=[{'name': c, 'id': c} for c in basic_data.columns],
                    style_table={'overflowX': 'auto', 'maxHeight': '400px', 'overflowY': 'auto'},
                    style_cell={
                        'textAlign': 'center', 
                        'padding': '6px 8px', 
                        'fontSize': '12px',
                        'whiteSpace': 'normal',  # 允许换行
                        'height': 'auto',
                    },
                    style_header={
                        'backgroundColor': '#f8f9fa', 
                        'fontWeight': 'bold', 
                        'textAlign': 'center', 
                        'padding': '8px',
                        'whiteSpace': 'normal',
                        'height': 'auto',
                    },
                    style_cell_conditional=[
                        {'if': {'column_id': '一级分类'}, 'width': '80px'},
                        {'if': {'column_id': '店内码'}, 'width': '70px'},
                        {'if': {'column_id': '商品名称'}, 'width': '180px', 'textAlign': 'left'},
                        {'if': {'column_id': '变动日期'}, 'width': '90px'},
                        {'if': {'column_id': '调价类型'}, 'width': '80px'},
                        {'if': {'column_id': '原价变动'}, 'width': '90px'},
                        {'if': {'column_id': '售价变动'}, 'width': '90px'},
                        {'if': {'column_id': '价格变化率'}, 'width': '80px'},
                        {'if': {'column_id': '调价前7日均销量'}, 'width': '100px'},
                        {'if': {'column_id': '调价后7日均销量'}, 'width': '100px'},
                        {'if': {'column_id': '销量变化率'}, 'width': '80px'},
                        {'if': {'column_id': '弹性'}, 'width': '55px'},
                        {'if': {'column_id': '敏感度'}, 'width': '80px'},
                        {'if': {'column_id': '调价效果'}, 'width': '90px'},
                        {'if': {'column_id': '建议'}, 'width': '220px', 'textAlign': 'left'},
                    ],
                    style_data_conditional=common_style_data_conditional,
                    page_size=15,
                    page_action='native',
                    sort_action='native',
                    sort_by=[{'column_id': '变动日期', 'direction': 'desc'}],
                )
            ]),
            
            # Tab2: 销售额视图
            dbc.Tab(label="💰 销售额变化", tab_id="tab-revenue", children=[
                dash_table.DataTable(
                    data=revenue_data.to_dict('records') if not revenue_data.empty else [],
                    columns=[{'name': c, 'id': c} for c in revenue_data.columns] if not revenue_data.empty else [],
                    style_table={'overflowX': 'auto', 'maxHeight': '400px', 'overflowY': 'auto'},
                    style_cell={
                        'textAlign': 'center', 
                        'padding': '8px 10px', 
                        'fontSize': '12px',
                        'whiteSpace': 'normal',
                    },
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold', 'textAlign': 'center', 'padding': '10px'},
                    style_cell_conditional=[
                        {'if': {'column_id': '商品名称'}, 'width': '200px', 'textAlign': 'left'},
                        {'if': {'column_id': '变动日期'}, 'width': '100px'},
                        {'if': {'column_id': '调价类型'}, 'width': '90px'},
                        {'if': {'column_id': '价格变化率'}, 'width': '90px'},
                        {'if': {'column_id': '调价前7日销售额'}, 'width': '120px'},
                        {'if': {'column_id': '调价后7日销售额'}, 'width': '120px'},
                        {'if': {'column_id': '销售额变化率'}, 'width': '100px'},
                        {'if': {'column_id': '调价效果'}, 'width': '100px'},
                    ],
                    style_data_conditional=[
                        {'if': {'filter_query': '{调价效果} contains "成功"'}, 'backgroundColor': '#e8f5e9'},
                        {'if': {'filter_query': '{调价效果} contains "失败"'}, 'backgroundColor': '#ffebee'},
                        {'if': {'filter_query': '{调价效果} contains "中性"'}, 'backgroundColor': '#fff8e1'},
                    ],
                    page_size=15,
                    page_action='native',
                    sort_action='native',
                    sort_by=[{'column_id': '变动日期', 'direction': 'desc'}],
                ) if not revenue_data.empty else html.Div([
                    dbc.Alert("暂无销售额数据，请确保数据中包含'实收价格'字段", color="info")
                ])
            ]),
            
            # Tab3: 利润视图
            dbc.Tab(label="📈 利润分析", tab_id="tab-profit", children=[
                dash_table.DataTable(
                    data=profit_data.to_dict('records') if not profit_data.empty else [],
                    columns=[{'name': c, 'id': c} for c in profit_data.columns] if not profit_data.empty else [],
                    style_table={'overflowX': 'auto', 'maxHeight': '400px', 'overflowY': 'auto'},
                    style_cell={
                        'textAlign': 'center', 
                        'padding': '8px 10px', 
                        'fontSize': '12px',
                        'whiteSpace': 'normal',
                    },
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold', 'textAlign': 'center', 'padding': '10px'},
                    style_cell_conditional=[
                        {'if': {'column_id': '商品名称'}, 'width': '200px', 'textAlign': 'left'},
                        {'if': {'column_id': '变动日期'}, 'width': '100px'},
                        {'if': {'column_id': '调价类型'}, 'width': '90px'},
                        {'if': {'column_id': '价格变化率'}, 'width': '90px'},
                        {'if': {'column_id': '调价前7日利润额'}, 'width': '120px'},
                        {'if': {'column_id': '调价后7日利润额'}, 'width': '120px'},
                        {'if': {'column_id': '利润额变化率'}, 'width': '100px'},
                        {'if': {'column_id': '调价前毛利率'}, 'width': '100px'},
                        {'if': {'column_id': '调价后毛利率'}, 'width': '100px'},
                        {'if': {'column_id': '毛利率变化'}, 'width': '90px'},
                        {'if': {'column_id': '调价效果'}, 'width': '100px'},
                    ],
                    style_data_conditional=[
                        {'if': {'filter_query': '{调价效果} contains "成功"'}, 'backgroundColor': '#e8f5e9'},
                        {'if': {'filter_query': '{调价效果} contains "失败"'}, 'backgroundColor': '#ffebee'},
                        {'if': {'filter_query': '{调价效果} contains "中性"'}, 'backgroundColor': '#fff8e1'},
                        # 毛利率变化颜色
                        {'if': {'column_id': '毛利率变化', 'filter_query': '{毛利率变化} contains "+"'}, 'color': '#388e3c', 'fontWeight': 'bold'},
                        {'if': {'column_id': '毛利率变化', 'filter_query': '{毛利率变化} contains "-"'}, 'color': '#d32f2f', 'fontWeight': 'bold'},
                    ],
                    page_size=15,
                    page_action='native',
                    sort_action='native',
                    sort_by=[{'column_id': '变动日期', 'direction': 'desc'}],
                ) if not profit_data.empty else html.Div([
                    dbc.Alert("暂无利润数据，请确保数据中包含'利润额'字段", color="info")
                ])
            ]),
        ], id="price-elasticity-tabs", active_tab="tab-basic", className="mb-2"),
        
        # ========== 可视化图表区 ==========
        create_price_elasticity_charts(price_changes, high_count, mid_count, low_count, abnormal_count),
        
        # 说明区域
        html.Div([
            html.Div([
                html.Small([
                    html.Strong("📐 弹性公式："),
                    "价格弹性系数 = 销量变化率 ÷ 价格变化率"
                ], className="text-muted d-block"),
                html.Small([
                    html.Strong("📊 敏感度解读："),
                    "🔴高敏感(|E|>1.5)价格变动对销量影响大 | ",
                    "🟡中敏感(0.5~1.5)影响适中 | ",
                    "🟢低敏感(<0.5)销量稳定 | ",
                    "🟣异常(涨价反涨量或降价反降量)"
                ], className="text-muted d-block mt-1"),
                html.Small([
                    html.Strong("📈 调价效果评估："),
                    "综合利润额、销售额、毛利率变化进行评估 | ",
                    "✅成功=利润↑或(利润持平且销售额↑) | ",
                    "⚠️中性=影响有限 | ",
                    "❌失败=利润↓且销售额↓"
                ], className="text-muted d-block mt-1"),
                html.Small([
                    html.Strong("💡 毛利率公式："),
                    "毛利率 = 利润额 ÷ 销售额 × 100%（与业务手册一致）"
                ], className="text-muted d-block mt-1"),
            ], className="p-2 bg-light rounded")
        ], className="mt-2")
    ])


def get_price_elasticity_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取价格弹性分析导出数据（完整版，包含所有维度）"""
    price_changes = detect_price_changes_from_orders(df)
    if price_changes.empty:
        return pd.DataFrame()
    
    # 选择导出列（完整版，包含销售额和利润数据）
    export_cols = [
        '一级分类', '店内码', '商品名称', '变动日期', '调价类型', 
        '原价变动', '售价变动', '价格变化率',
        '调价前7日均销量', '调价后7日均销量', '销量变化率',
        '调价前7日销售额', '调价后7日销售额', '销售额变化率',
        '调价前7日利润额', '调价后7日利润额', '利润额变化率',
        '调价前毛利率', '调价后毛利率', '毛利率变化',
        '弹性', '敏感度', '调价效果', '建议'
    ]
    available = [c for c in export_cols if c in price_changes.columns]
    return price_changes[available]


def create_price_elasticity_charts(price_changes: pd.DataFrame, high_count: int, mid_count: int, low_count: int, abnormal_count: int) -> html.Div:
    """创建价格弹性可视化图表 - ECharts版本"""
    try:
        if not ECHARTS_AVAILABLE:
            return html.Div("ECharts 未安装", className="text-muted small")
        
        charts = []
        
        # 图表1：调价效果按分类统计（柱状图）
        if not price_changes.empty and '一级分类' in price_changes.columns and '调价效果' in price_changes.columns:
            # 统计各分类的调价效果
            effect_stats = price_changes.groupby(['一级分类', '调价效果']).size().unstack(fill_value=0)
            
            # 准备数据
            categories = effect_stats.index.tolist()[:10]  # 最多显示10个分类
            success_data = []
            neutral_data = []
            fail_data = []
            
            for cat in categories:
                row = effect_stats.loc[cat] if cat in effect_stats.index else {}
                success = 0
                neutral = 0
                fail = 0
                for col, val in row.items():
                    if '成功' in str(col):
                        success += val
                    elif '失败' in str(col):
                        fail += val
                    else:
                        neutral += val
                success_data.append(int(success))
                neutral_data.append(int(neutral))
                fail_data.append(int(fail))
            
            # 计算成功率
            total = sum(success_data) + sum(neutral_data) + sum(fail_data)
            success_rate = round(sum(success_data) / total * 100, 1) if total > 0 else 0
            
            chart1_option = {
                'title': {'text': f'📊 调价效果分析（成功率{success_rate}%）', 'left': 'center', 'textStyle': {'fontSize': 14}},
                'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
                'legend': {'data': ['✅ 成功', '⚠️ 中性', '❌ 失败'], 'top': 30},
                'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'top': 80, 'containLabel': True},
                'xAxis': {'type': 'category', 'data': categories, 'axisLabel': {'rotate': 30, 'fontSize': 11}},
                'yAxis': {'type': 'value', 'name': '商品数'},
                'series': [
                    {'name': '✅ 成功', 'type': 'bar', 'stack': 'total', 'data': success_data, 
                     'itemStyle': {'color': '#4CAF50'}, 'emphasis': {'focus': 'series'}},
                    {'name': '⚠️ 中性', 'type': 'bar', 'stack': 'total', 'data': neutral_data, 
                     'itemStyle': {'color': '#FFC107'}, 'emphasis': {'focus': 'series'}},
                    {'name': '❌ 失败', 'type': 'bar', 'stack': 'total', 'data': fail_data, 
                     'itemStyle': {'color': '#F44336'}, 'emphasis': {'focus': 'series'}}
                ]
            }
            charts.append(dbc.Col([
                DashECharts(option=chart1_option, style={'height': '280px', 'width': '100%'})
            ], width=7))
        
        # 图表2：敏感度分布环形图
        sensitivity_data = [
            {'value': high_count, 'name': '🔴 高敏感', 'itemStyle': {'color': '#F44336'}},
            {'value': mid_count, 'name': '🟡 中敏感', 'itemStyle': {'color': '#FFC107'}},
            {'value': low_count, 'name': '🟢 低敏感', 'itemStyle': {'color': '#4CAF50'}},
            {'value': abnormal_count, 'name': '🟣 异常', 'itemStyle': {'color': '#9C27B0'}}
        ]
        # 过滤掉值为0的项
        sensitivity_data = [d for d in sensitivity_data if d['value'] > 0]
        
        chart2_option = {
            'title': {'text': '📈 价格敏感度分布', 'left': 'center', 'textStyle': {'fontSize': 14}},
            'tooltip': {'trigger': 'item', 'formatter': '{b}: {c}个 ({d}%)'},
            'legend': {'orient': 'vertical', 'right': 10, 'top': 'center'},
            'series': [{
                'name': '敏感度',
                'type': 'pie',
                'radius': ['40%', '70%'],
                'center': ['40%', '55%'],
                'avoidLabelOverlap': True,
                'itemStyle': {'borderRadius': 8, 'borderColor': '#fff', 'borderWidth': 2},
                'label': {'show': True, 'formatter': '{b}\n{d}%'},
                'emphasis': {'label': {'show': True, 'fontSize': 14, 'fontWeight': 'bold'}},
                'data': sensitivity_data
            }]
        }
        charts.append(dbc.Col([
            DashECharts(option=chart2_option, style={'height': '280px', 'width': '100%'})
        ], width=5))
        
        if charts:
            return dbc.Row(charts, className="mt-3")
        return html.Div()
    except Exception as e:
        return html.Div(f"图表生成失败: {str(e)}", className="text-muted small mt-2")


# ==================== 通用UI组件 ====================

def create_no_data_message(message: str = "暂无数据，请先上传数据文件") -> html.Div:
    """创建无数据提示"""
    return html.Div([
        dbc.Alert([
            html.H4("📊 暂无数据", className="alert-heading"),
            html.P(message)
        ], color="warning", className="text-center")
    ], className="p-4")


def create_error_message(message: str) -> html.Div:
    """创建错误提示"""
    return html.Div([
        dbc.Alert([
            html.H4("❌ 发生错误", className="alert-heading"),
            html.P(message)
        ], color="danger", className="text-center")
    ], className="p-4")


def create_business_diagnosis_card(df: pd.DataFrame) -> html.Div:
    """
    创建昨日经营诊断卡片 - V3.0 按紧急度分层
    
    两层架构:
    🔴 紧急处理（今日必须完成）
    🟡 关注观察（本周内处理）
    
    功能：
    - 点击按钮可查看详细列表
    - 支持导出Excel
    """
    if df is None or df.empty:
        return None
    
    try:
        print(f"[DEBUG] create_business_diagnosis_card 开始执行, df.shape={df.shape}")
        
        # 获取完整诊断数据
        diagnosis = get_diagnosis_summary(df)
        print(f"[DEBUG] get_diagnosis_summary 完成: date={diagnosis.get('date')}")
        
        urgent = diagnosis['urgent']
        watch = diagnosis['watch']
        
        print(f"[DEBUG] urgent 问题数: overflow={urgent['overflow']['count']}, delivery={urgent['delivery']['count']}, stockout={urgent['stockout']['count']}")
        print(f"[DEBUG] watch 问题数: traffic_drop={watch['traffic_drop']['count']}, new_slow={watch['new_slow']['count']}, new_products={watch['new_products']['count']}")
        
        # 渠道标签生成函数
        def create_channel_badges(channels: Dict[str, int], max_show: int = 3) -> html.Span:
            if not channels:
                return html.Span()
            
            badges = []
            channel_colors = {
                '美团': '🟠', '美团闪购': '🟠', 
                '饿了么': '🔵', 
                '闪购小程序': '🟢', '小程序': '🟢'
            }
            
            sorted_channels = sorted(channels.items(), key=lambda x: x[1], reverse=True)[:max_show]
            for channel, count in sorted_channels:
                emoji = channel_colors.get(channel, '⚪')
                badges.append(html.Span(f"{emoji}{channel[:4]}{count}", className="me-2 small"))
            
            return html.Div(badges, className="mt-2 text-muted")
        
        # 距离分布生成函数
        def create_distance_info(dist_dict: Dict[str, int]) -> str:
            if not dist_dict:
                return ""
            total = sum(dist_dict.values())
            if total == 0:
                return ""
            sorted_dist = sorted(dist_dict.items(), key=lambda x: x[1], reverse=True)
            top_dist, top_count = sorted_dist[0]
            return f"主要分布: {top_dist}"
        
        # ================== 紧急处理层 ==================
        urgent_cards = []
        
        # 1. 穿底止血 - 使用美化版卡片
        if urgent['overflow']['count'] > 0:
            # 构建渠道徽章
            channel_badges = []
            for channel, count in list(urgent['overflow']['channels'].items())[:3]:
                channel_badges.append({"text": f"{channel[:4]} {count}单", "color": "red"})
            
            # 计算平均亏损
            avg_loss = urgent['overflow']['loss'] / urgent['overflow']['count'] if urgent['overflow']['count'] > 0 else 0
            
            if MANTINE_AVAILABLE:
                urgent_cards.append(
                    dbc.Col([
                        create_mantine_diagnosis_card(
                            title="穿底止血",
                            icon="tabler:alert-octagon",
                            color="red",
                            main_value=f"{urgent['overflow']['count']}",
                            main_label="单昨日亏损",
                            sub_info=f"累计损失 ¥{urgent['overflow']['loss']:,.0f}",
                            extra_info=f"单均亏损 ¥{avg_loss:.1f}",
                            extra_badges=channel_badges,
                            button_id="btn-diagnosis-overflow",
                            button_text="立即处理"
                        )
                    ], width=4, className="mb-3")
                )
            else:
                # 回退到原始样式
                urgent_cards.append(
                    dbc.Col([
                        html.Div([
                            html.Div("💸 穿底止血", className="fw-bold text-danger mb-2"),
                            html.Div([
                                "昨日 ",
                                html.Span(f"{urgent['overflow']['count']}", className="fw-bold text-danger fs-5"),
                                " 单亏损"
                            ], className="mb-1"),
                            html.Div([
                                "累计损失 ",
                                html.Span(f"¥{urgent['overflow']['loss']:,.0f}", className="fw-bold text-danger")
                            ], className="small text-muted mb-1"),
                            create_channel_badges(urgent['overflow']['channels']),
                            html.Div([
                                dbc.Button("查看详情 →", id="btn-diagnosis-overflow", color="link", size="sm", className="p-0 text-danger", n_clicks=0)
                            ], className="mt-2")
                        ], className="p-3 bg-danger bg-opacity-10 rounded h-100 border-start border-4 border-danger")
                    ], width=4)
                )
        
        # 2. 高配送费预警 - 使用黄色(yellow)区分
        if urgent['delivery']['count'] > 0:
            distance_info = create_distance_info(urgent['delivery']['distance_distribution'])
            delivery_badges = [{"text": f"{ch[:4]} {cnt}", "color": "yellow"} 
                              for ch, cnt in list(urgent['delivery'].get('channels', {}).items())[:3]]
            
            # 计算平均溢价
            avg_extra = urgent['delivery']['extra_cost'] / urgent['delivery']['count'] if urgent['delivery']['count'] > 0 else 0
            
            urgent_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="高配送费预警",
                        icon="tabler:truck-delivery",
                        color="yellow",
                        main_value=f"{urgent['delivery']['count']}",
                        main_label="单配送净成本>6元",
                        sub_info=f"配送溢价 ¥{urgent['delivery']['extra_cost']:,.0f} | 均¥{avg_extra:.1f}",
                        extra_info=distance_info if distance_info else None,
                        extra_badges=delivery_badges,
                        button_id="btn-diagnosis-delivery",
                        button_text="查看订单"
                    )
                ], width=4, className="mb-3")
            )
        
        # 3. 热销缺货 - 使用红色(red)表示严重
        if urgent['stockout']['count'] > 0:
            stockout_badges = [{"text": f"{ch[:4]} {cnt}", "color": "red"} 
                              for ch, cnt in list(urgent['stockout']['channels'].items())[:3]]
            
            # 计算平均损失
            avg_loss = urgent['stockout']['loss'] / urgent['stockout']['count'] if urgent['stockout']['count'] > 0 else 0
            
            urgent_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="热销缺货",
                        icon="tabler:package-off",
                        color="red",
                        main_value=f"{urgent['stockout']['count']}",
                        main_label="个热销品库存为0",
                        sub_info=f"日均损失 ¥{urgent['stockout']['loss']:,.0f}",
                        extra_info=f"单品均损 ¥{avg_loss:.0f}/天",
                        extra_badges=stockout_badges,
                        button_id="btn-diagnosis-stockout",
                        button_text="生成补货单"
                    )
                ], width=4, className="mb-3")
            )
        
        # 4. 价格异常预警 - 使用橙色(orange)区分
        if urgent.get('price_abnormal', {}).get('count', 0) > 0:
            price_data = urgent['price_abnormal']
            price_badges = [
                {"text": f"严重 {price_data.get('severe_count', 0)}", "color": "red"},
                {"text": f"轻度 {price_data.get('mild_count', 0)}", "color": "yellow"}
            ]
            
            # 计算平均损失
            avg_loss = abs(price_data.get('total_loss', 0)) / price_data['count'] if price_data['count'] > 0 else 0
            
            urgent_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="价格异常",
                        icon="tabler:alert-triangle",
                        color="orange",
                        main_value=f"{price_data['count']}",
                        main_label="个商品售价异常",
                        sub_info=f"预估损失 ¥{abs(price_data.get('total_loss', 0)):,.0f}",
                        extra_info=f"单品均亏 ¥{avg_loss:.1f}",
                        extra_badges=price_badges,
                        button_id="btn-diagnosis-price-abnormal",
                        button_text="立即处理"
                    )
                ], width=4, className="mb-3")
            )
        
        # 5. 销量下滑 - 使用蓝色(blue)区分
        if watch['traffic_drop']['count'] > 0:
            traffic_badges = [{"text": f"{ch[:4]} {cnt}", "color": "blue"} 
                             for ch, cnt in list(watch['traffic_drop']['channels'].items())[:3]]
            urgent_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="销量下滑",
                        icon="tabler:trending-down",
                        color="blue",
                        main_value=f"{watch['traffic_drop']['count']}",
                        main_label="个热销品持续下滑",
                        sub_info="7日vs7日跌幅>30%",
                        extra_badges=traffic_badges,
                        button_id="btn-diagnosis-traffic",
                        button_text="立即处理"
                    )
                ], width=4, className="mb-3")
            )
        
        # 6. 利润率下滑 - 使用葡萄紫(grape)区分
        if watch.get('profit_rate_drop', {}).get('count', 0) > 0:
            profit_drop_data = watch['profit_rate_drop']
            # 新的四档分级徽章
            profit_badges = []
            if profit_drop_data.get('drop_20', 0) > 0:
                profit_badges.append({"text": f">20% {profit_drop_data['drop_20']}", "color": "red"})
            if profit_drop_data.get('drop_15', 0) > 0:
                profit_badges.append({"text": f"15-20% {profit_drop_data['drop_15']}", "color": "orange"})
            if profit_drop_data.get('drop_10', 0) > 0:
                profit_badges.append({"text": f"10-15% {profit_drop_data['drop_10']}", "color": "yellow"})
            if profit_drop_data.get('drop_5', 0) > 0:
                profit_badges.append({"text": f"5-10% {profit_drop_data['drop_5']}", "color": "blue"})
            
            # 显示预估损失
            loss_info = f"预估损失 ¥{profit_drop_data.get('loss', 0):,.0f}" if profit_drop_data.get('loss', 0) > 0 else "近7天vs前7天对比"
            
            urgent_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="利润率下滑",
                        icon="tabler:arrow-down-right-circle",
                        color="grape",
                        main_value=f"{profit_drop_data['count']}",
                        main_label="个商品利润率下滑",
                        sub_info=loss_info,
                        extra_info="7日周期对比分析",
                        extra_badges=profit_badges if profit_badges else None,
                        button_id="btn-diagnosis-profit-drop",
                        button_text="立即处理"
                    )
                ], width=4, className="mb-3")
            )
        
        # ================== 关注观察层 ==================
        watch_cards = []
        
        # 1. 滞销预警（合并显示）- 使用蓝绿色(cyan)
        total_slow = watch['new_slow']['count'] + watch['ongoing_slow']['count'] + watch['severe_slow']['count']
        total_slow_cost = watch['new_slow']['cost'] + watch['ongoing_slow']['cost'] + watch['severe_slow']['cost']
        
        if total_slow > 0:
            slow_badges = []
            if watch['new_slow']['count'] > 0:
                slow_badges.append({"text": f"新增 {watch['new_slow']['count']}", "color": "cyan"})
            if watch['ongoing_slow']['count'] > 0:
                slow_badges.append({"text": f"持续 {watch['ongoing_slow']['count']}", "color": "cyan"})
            if watch['severe_slow']['count'] > 0:
                slow_badges.append({"text": f"严重 {watch['severe_slow']['count']}", "color": "red"})
            
            watch_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="滞销积压",
                        icon="tabler:clock-pause",
                        color="cyan",
                        main_value=f"{total_slow}",
                        main_label="个SKU需关注",
                        sub_info=f"积压成本 ¥{total_slow_cost:,.0f}",
                        extra_badges=slow_badges,
                        button_id="btn-diagnosis-slow",
                        button_text="导出清单"
                    )
                ], width=4, className="mb-3")
            )
        
        # 2. 新品表现 - 使用绿色(green)
        if watch['new_products']['count'] > 0:
            new_badges = []
            if watch['new_products'].get('top_profit_category'):
                new_badges.append({"text": f"TOP:{watch['new_products']['top_profit_category'][:6]}", "color": "green"})
            
            watch_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="新品表现",
                        icon="tabler:rocket",
                        color="green",
                        main_value=f"{watch['new_products']['count']}",
                        main_label="个商品昨日首销",
                        sub_info=f"贡献销售额 ¥{watch['new_products']['sales']:,.0f}",
                        extra_badges=new_badges if new_badges else None,
                        button_id="btn-diagnosis-newproduct",
                        button_text="查看明细"
                    )
                ], width=4, className="mb-3")
            )
        
        # 3. 价格弹性分析 - 使用紫色(violet)表示分析型卡片
        elasticity_summary = get_price_elasticity_summary(df)
        change_count = elasticity_summary.get('调价事件数', 0)
        elasticity_badges = []
        if change_count > 0:
            elasticity_badges = [
                {"text": f"高敏感 {elasticity_summary.get('高敏感商品数', 0)}", "color": "red"},
                {"text": f"中敏感 {elasticity_summary.get('中敏感商品数', 0)}", "color": "orange"},
                {"text": f"低敏感 {elasticity_summary.get('低敏感商品数', 0)}", "color": "green"},
            ]
        
        watch_cards.append(
            dbc.Col([
                create_mantine_diagnosis_card(
                    title="价格弹性分析",
                    icon="tabler:chart-dots",
                    color="violet",
                    main_value=f"{change_count}" if change_count > 0 else "—",
                    main_label="次调价记录" if change_count > 0 else "分析历史调价效果",
                    sub_info="基于历史数据评估定价风险" if change_count == 0 else None,
                    extra_badges=elasticity_badges if elasticity_badges else None,
                    button_id="btn-diagnosis-price-elasticity",
                    button_text="查看分析"
                )
            ], width=4, className="mb-3")
        )
        
        # ================== 正向激励层（今日亮点）==================
        highlights = diagnosis.get('highlights', {})
        highlight_cards = []
        
        # 1. 爆款商品 - 使用粉色(pink)表示热销亮点
        hot_products = highlights.get('hot_products', {})
        if hot_products.get('count', 0) > 0:
            top_hot = hot_products.get('top_products', [])[:2]
            hot_badges = [{"text": f"{p['name'][:6]}+{p['growth']:.0f}%", "color": "pink"} for p in top_hot]
            
            highlight_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="爆款商品",
                        icon="tabler:flame",
                        color="pink",
                        main_value=f"{hot_products['count']}",
                        main_label="个商品销量突增",
                        sub_info=f"共销售 {hot_products.get('total_qty', 0)} 件",
                        extra_badges=hot_badges if hot_badges else None,
                        button_id="btn-diagnosis-hot-products",
                        button_text="查看详情"
                    )
                ], width=4, className="mb-3")
            )
        
        # 2. 高利润商品 - 使用靛蓝色(indigo)表示盈利亮点
        high_profit = highlights.get('high_profit_products', {})
        if high_profit.get('count', 0) > 0:
            top_profit = high_profit.get('top_products', [])[:2]
            profit_badges = [{"text": f"{p['name'][:6]} ¥{p['profit']:.0f}", "color": "teal"} for p in top_profit]
            
            highlight_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="高利润商品",
                        icon="tabler:coin",
                        color="teal",
                        main_value=f"TOP {high_profit['count']}",
                        main_label="贡献利润",
                        sub_info=f"合计 ¥{high_profit.get('total_profit', 0):,.0f}",
                        extra_badges=profit_badges if profit_badges else None,
                        button_id="btn-diagnosis-high-profit",
                        button_text="查看详情"
                    )
                ], width=4, className="mb-3")
            )
        
        # ================== 组装卡片 ==================
        content = []
        
        # 紧急处理层（日期放在标题栏右侧）
        if urgent_cards:
            content.append(
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.Span("🔴", className="me-2"),
                            html.Span("紧急处理", className="fw-bold text-danger"),
                            html.Small("（今日必须完成）", className="text-muted ms-2")
                        ], className="d-inline"),
                        html.Small(f"数据截止: {diagnosis['date']}", className="text-muted float-end") if diagnosis['date'] else None
                    ], className="bg-danger bg-opacity-10 border-0 py-2"),
                    dbc.CardBody([
                        dbc.Row(urgent_cards)
                    ], className="py-3")
                ], className="mb-3 border-danger border-opacity-25")
            )
        
        # 关注观察层
        if watch_cards:
            content.append(
                dbc.Card([
                    dbc.CardHeader([
                        html.Span("🟡", className="me-2"),
                        html.Span("关注观察", className="fw-bold text-warning"),
                        html.Small("（本周内处理）", className="text-muted ms-2")
                    ], className="bg-warning bg-opacity-10 border-0 py-2"),
                    dbc.CardBody([
                        dbc.Row(watch_cards)
                    ], className="py-3")
                ], className="mb-3 border-warning border-opacity-25")
            )
        
        # 正向激励层（今日亮点）
        if highlight_cards:
            content.append(
                dbc.Card([
                    dbc.CardHeader([
                        html.Span("🟢", className="me-2"),
                        html.Span("今日亮点", className="fw-bold text-success"),
                        html.Small("（正向激励）", className="text-muted ms-2")
                    ], className="bg-success bg-opacity-10 border-0 py-2"),
                    dbc.CardBody([
                        dbc.Row(highlight_cards)
                    ], className="py-3")
                ], className="mb-3 border-success border-opacity-25")
            )
        
        # 如果没有任何问题
        if not urgent_cards and not watch_cards:
            content.append(
                dbc.Alert([
                    html.H5("✅ 昨日经营状况良好", className="alert-heading"),
                    html.P("未发现需要紧急处理的问题，继续保持！", className="mb-0")
                ], color="success", className="text-center")
            )
        
        print("[DEBUG] create_business_diagnosis_card 完成")
        return dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-stethoscope me-2"),
                    "昨日经营诊断"
                ], className="mb-0 text-dark")
            ], className="bg-light border-bottom-0 pt-3 ps-3"),
            dbc.CardBody(content)
        ], className="mb-4 shadow-sm border-0")
    
    except Exception as e:
        import traceback
        print(f"[ERROR] create_business_diagnosis_card 失败: {str(e)}")
        traceback.print_exc()
        return dbc.Alert([
            html.H5("⚠️ 诊断分析出错", className="alert-heading"),
            html.P(f"错误信息: {str(e)}", className="mb-0")
        ], color="warning")


def create_today_must_do_layout(df: pd.DataFrame = None, selected_stores=None) -> html.Div:
    """创建今日必做主布局 - V2.1 垂直布局优化"""
    
    # 先应用门店筛选（确保诊断卡片和下钻数据一致）
    filtered_df = df.copy() if df is not None else None
    if filtered_df is not None and selected_stores:
        if isinstance(selected_stores, str):
            selected_stores = [selected_stores]
        if len(selected_stores) > 0 and '门店名称' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['门店名称'].isin(selected_stores)]
    
    diagnosis_section = create_business_diagnosis_card(filtered_df) if filtered_df is not None else None
    
    return html.Div([
        # 顶部工具栏
        dbc.Row([
            dbc.Col([
                html.H4("✅ 今日必做 - 智能运营提醒", className="mb-0"),
                html.Small("基于昨日数据自动识别需要关注的运营问题", className="text-muted")
            ], width=12)
        ], className="mb-4 align-items-center"),
        
        dcc.Store(id='selected-product-store'),
        
        # 商品详情弹窗
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("📊 商品详情分析"), id='product-detail-modal-header'),
            dbc.ModalBody(id='product-detail-modal-body'),
            dbc.ModalFooter(
                dbc.Button("关闭", id="product-detail-modal-close", className="ms-auto", n_clicks=0)
            ),
        ], id="product-detail-modal", size="lg", is_open=False),
        
        # 诊断详情弹窗 - 用于查看各类问题的详细列表（全屏模式）
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id='diagnosis-detail-modal-title'), className="px-5"),
            dbc.ModalBody(id='diagnosis-detail-modal-body', className="px-5"),
            dbc.ModalFooter([
                dbc.Button("导出Excel", id="diagnosis-detail-export-btn", color="success", className="me-2", n_clicks=0),
                dbc.Button("关闭", id="diagnosis-detail-modal-close", className="ms-auto", n_clicks=0)
            ], className="px-5"),
        ], id="diagnosis-detail-modal", fullscreen=True, is_open=False, scrollable=True),
        
        # 存储当前诊断类型
        dcc.Store(id='diagnosis-detail-type-store', data=None),
        dcc.Download(id='diagnosis-download'),
        
        # 经营诊断卡片
        html.Div(id='today-must-do-diagnosis-container', children=diagnosis_section),
        
        # ========== 商品综合分析 ==========
        # 整合评分模型 + 品类动态阈值，提供科学的商品分析视图
        html.Div(id='product-scoring-section-container', 
                 children=create_product_scoring_section(filtered_df) if filtered_df is not None else html.Div()),
        
        # 商品评分导出下载
        dcc.Download(id='product-scoring-export-download'),
        
        # ========== 智能调价计算器 ==========
        dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H5([
                            html.I(className="fas fa-calculator me-2"),
                            "🔧 智能调价计算器"
                        ], className="mb-0 text-warning")
                    ], width=6),
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-file-excel me-1"),
                                "导出方案"
                            ], id='pricing-export-btn', color="success", size="sm", disabled=True),
                            dbc.Button([
                                html.I(className="fas fa-undo me-1"),
                                "重置"
                            ], id='pricing-reset-btn', color="outline-secondary", size="sm"),
                        ], className="float-end")
                    ], width=6, className="text-end")
                ], align="center")
            ], className="bg-white border-bottom-0 pt-3 px-3"),
            dbc.CardBody([
                # 第一行：商品来源、渠道筛选、加载数据
                dbc.Row([
                    dbc.Col([
                        html.Label("商品来源:", className="fw-bold mb-1"),
                        dcc.Dropdown(
                            id='pricing-source-dropdown',
                            options=[
                                # 今日必做问题商品（提价）
                                {'label': '═══ 📋 今日必做问题商品 ═══', 'value': '_header_must_do', 'disabled': True},
                                {'label': '🔴 穿底止血', 'value': 'overflow'},
                                {'label': '⚠️ 价格异常', 'value': 'price_abnormal'},
                                {'label': '📉 销量下滑', 'value': 'sales_decline'},
                                {'label': '📊 利润率下滑', 'value': 'profit_decline'},
                                # 滞销品清仓（降价）
                                {'label': '═══ 🐌 滞销品清仓 ═══', 'value': '_header_stagnant', 'disabled': True},
                                {'label': '🟡 轻度滞销 (7天)', 'value': 'stagnant_light'},
                                {'label': '🟠 中度滞销 (8-15天)', 'value': 'stagnant_medium'},
                                {'label': '🔴 重度滞销 (16-30天)', 'value': 'stagnant_heavy'},
                                {'label': '⚫ 超重度滞销 (>30天)', 'value': 'stagnant_severe'},
                                {'label': '🐌 全部滞销品', 'value': 'stagnant_all'},
                                # 全量数据
                                {'label': '═══ 📦 其他筛选 ═══', 'value': '_header_all', 'disabled': True},
                                {'label': '💰 低利润商品(<10%)', 'value': 'low_profit'},
                            ],
                            value=None,
                            placeholder="请选择商品来源...",
                            clearable=False,
                            style={'fontSize': '13px'}
                        )
                    ], width=4),
                    dbc.Col([
                        html.Label("渠道筛选:", className="fw-bold mb-1"),
                        dcc.Dropdown(
                            id='pricing-channel-filter',
                            options=[{'label': '全部渠道', 'value': 'all'}],
                            value='all',
                            clearable=False,
                            style={'fontSize': '13px'}
                        )
                    ], width=3),
                    dbc.Col([
                        html.Label("　", className="d-block mb-1"),
                        dbc.Button([
                            html.I(className="fas fa-sync-alt me-1"),
                            "加载数据"
                        ], id='pricing-calculate-btn', color="primary", size="sm", className="w-100")
                    ], width=2),
                    dbc.Col([
                        html.Label("　", className="d-block mb-1"),
                        html.Div(id='pricing-batch-status', className="small text-center")
                    ], width=3),
                ], className="mb-3"),
                
                # 第二行：调价方向、调价模式、力度/目标利润率、计算调价
                dbc.Row([
                    dbc.Col([
                        html.Label([
                            "调价方向",
                            html.I(className="fas fa-question-circle ms-1 text-muted", 
                                   id="adjust-direction-help", style={'cursor': 'pointer'})
                        ], className="fw-bold mb-1"),
                        dbc.Tooltip(
                            "提价：用于穿底/价格异常/利润下滑商品；降价：用于滞销品/销量下滑商品",
                            target="adjust-direction-help",
                            placement="top"
                        ),
                        dbc.RadioItems(
                            id='pricing-adjust-direction',
                            options=[
                                {'label': '⬆️ 提价', 'value': 'up'},
                                {'label': '⬇️ 降价', 'value': 'down'},
                            ],
                            value='up',
                            inline=True,
                            className="small"
                        )
                    ], width=2),
                    dbc.Col([
                        html.Label([
                            "调价模式",
                            html.I(className="fas fa-question-circle ms-1 text-muted", 
                                   id="adjust-mode-help", style={'cursor': 'pointer'})
                        ], className="fw-bold mb-1"),
                        dbc.Tooltip(
                            "智能梯度：根据每个商品利润率自动计算最优调价；手动输入：统一设定目标利润率",
                            target="adjust-mode-help",
                            placement="top"
                        ),
                        dbc.RadioItems(
                            id='pricing-adjust-mode',
                            options=[
                                {'label': '🤖 智能梯度', 'value': 'smart'},
                                {'label': '✏️ 手动输入', 'value': 'manual'},
                            ],
                            value='smart',
                            inline=True,
                            className="small"
                        )
                    ], width=2),
                    # 智能梯度档位选择（智能模式显示）
                    dbc.Col(id='pricing-smart-level-container', children=[
                        html.Label("调价力度", className="fw-bold mb-1"),
                        dbc.ButtonGroup([
                            dbc.Button("💚 轻度", id='pricing-level-light', color="success", outline=True, size="sm",
                                      style={'padding': '4px 8px', 'fontSize': '11px'}),
                            dbc.Button("🟡 中度", id='pricing-level-medium', color="warning", outline=False, size="sm",
                                      style={'padding': '4px 8px', 'fontSize': '11px'}),
                            dbc.Button("🔴 重度", id='pricing-level-heavy', color="danger", outline=True, size="sm",
                                      style={'padding': '4px 8px', 'fontSize': '11px'}),
                        ], size="sm", className="d-block"),
                        # 隐藏的档位值存储
                        dcc.Store(id='pricing-smart-level-store', data='medium'),
                        html.Div(id='pricing-level-hint', className="small text-muted mt-1",
                                children="目标利润率: 8%")
                    ], width=3),
                    # 手动输入目标利润率（手动模式显示）
                    dbc.Col(id='pricing-manual-input-container', children=[
                        html.Label("目标利润率 (%)", className="fw-bold mb-1"),
                        dbc.InputGroup([
                            dbc.Input(
                                id='pricing-target-margin', 
                                type="number", 
                                value=15, 
                                min=0, 
                                step=1, 
                                size="sm",
                                style={'width': '80px'}
                            ),
                            dbc.InputGroupText("%", className="bg-light"),
                        ], size="sm"),
                        html.Div(className="small text-muted mt-1",
                                children="所有商品统一调至该利润率")
                    ], width=3, style={'visibility': 'hidden', 'position': 'absolute', 'left': '-9999px'}),
                    dbc.Col([
                        html.Label("　", className="d-block mb-1"),
                        dbc.Button([
                            html.I(className="fas fa-calculator me-1"),
                            "计算调价"
                        ], id='pricing-batch-target', color="success", size="sm", className="w-100")
                    ], width=2),
                    # 隐藏的兼容性组件（保持旧回调不报错）
                    html.Div([
                        dbc.Input(id='pricing-adjust-value', type="hidden", value=10),
                        dbc.Button(id='pricing-batch-1', style={'display': 'none'}),
                        dbc.Button(id='pricing-batch-3', style={'display': 'none'}),
                        dbc.Button(id='pricing-batch-5', style={'display': 'none'}),
                        dbc.Button(id='pricing-batch-10', style={'display': 'none'}),
                        html.Div(id='pricing-quick-buttons-container', style={'display': 'none'}),
                        html.Div(id='pricing-floor-warning', style={'display': 'none'}),
                    ], style={'display': 'none'})
                ], className="mb-3"),
                
                # 🎯 调价结果提示容器
                html.Div(id='pricing-floor-alert-container', className="mb-2"),
                
                # 调价效果汇总
                html.Div(id='pricing-summary-container', className="mb-3"),
                
                # 调价列表
                dcc.Loading(
                    id='loading-pricing-table',
                    type='circle',
                    children=[html.Div(id='pricing-table-container')]
                ),
                
                # 使用说明
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📋 使用说明", className="text-muted mb-2"),
                        html.Div([
                            html.P([
                                html.Strong("📊 商品来源分组："),
                                html.Br(),
                                "• 今日必做：穿底止血/价格异常/销量下滑/利润率下滑 → ⬆️提价",
                                html.Br(),
                                "• 滞销清仓：轻度/中度/重度/超重度滞销 → ⬇️降价",
                                html.Br(),
                                "• 全量数据：全部商品 → 自定义调价"
                            ], className="mb-1 small"),

                            html.P([
                                html.Strong("🔢 调价方式："),
                                html.Br(),
                                "• 按价格调整：直接调整售价X%",
                                html.Br(),
                                "• 按利润率：提价提升利润率/降价保证利润率不低于X%"
                            ], className="mb-1 small"),
                            html.P([
                                html.Strong("⚠️ 保本底线："),
                                "滞销品/销量下滑商品降价不会低于成本价，手动突破需确认"
                            ], className="mb-0 small text-warning"),
                        ])
                    ], className="py-2")
                ], className="mt-3 bg-light border-0"),
                
                # 商品详情面板
                dbc.Collapse(
                    dbc.Card([
                        dbc.CardHeader("📊 商品调价详情", className="py-2"),
                        dbc.CardBody(id='pricing-detail-panel')
                    ], className="mt-3 border-info"),
                    id='pricing-detail-collapse',
                    is_open=False
                )
            ])
        ], className="mb-4 shadow-sm border-0"),
        
        # 调价方案导出下载
        dcc.Download(id='pricing-download'),
        # 存储调价数据
        dcc.Store(id='pricing-data-store', data=None),
        dcc.Store(id='pricing-selected-product', data=None),
        
        # ========== 隐藏的按钮占位符 ==========
        # 这些按钮可能不会在诊断卡片中显示（取决于数据），但回调需要它们存在
        html.Div([
            dbc.Button(id="btn-diagnosis-traffic", style={'display': 'none'}),
            dbc.Button(id="btn-diagnosis-slow", style={'display': 'none'}),
        ], style={'display': 'none'})
    ], className="p-3")


def create_product_detail_content(df: pd.DataFrame, product_name: str) -> html.Div:
    """创建商品详情弹窗内容 - ECharts版本"""
    insight_data = get_product_insight(df, product_name)
    
    if insight_data['error']:
        return dbc.Alert(insight_data['error'], color="danger")
        
    trend_df = insight_data['trend_data']
    price_change = insight_data['price_change']
    activity_change = insight_data['activity_change']
    insight_text = insight_data['insight']
    
    # 趋势图 - ECharts版本
    chart_element = html.Div()
    if ECHARTS_AVAILABLE and not trend_df.empty:
        dates = trend_df['日期'].astype(str).tolist()
        sales = trend_df['销量'].tolist()
        
        # 计算均价
        prices = []
        if '商品实售价' in trend_df.columns:
            trend_df_calc = trend_df.copy()
            trend_df_calc['均价'] = (trend_df_calc['商品实售价'] / trend_df_calc['销量']).replace([np.inf, -np.inf], 0).fillna(0)
            prices = [round(p, 2) for p in trend_df_calc['均价'].tolist()]
        
        chart_option = {
            'title': {'text': '近30天销量与价格趋势', 'left': 'center', 'textStyle': {'fontSize': 14}},
            'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'cross'}},
            'legend': {'data': ['销量', '实收均价'], 'top': 30},
            'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'top': 80, 'containLabel': True},
            'xAxis': {'type': 'category', 'data': dates, 'axisLabel': {'rotate': 45, 'fontSize': 10}},
            'yAxis': [
                {'type': 'value', 'name': '销量', 'position': 'left'},
                {'type': 'value', 'name': '均价', 'position': 'right', 'axisLabel': {'formatter': '¥{value}'}}
            ],
            'series': [
                {'name': '销量', 'type': 'bar', 'data': sales, 'itemStyle': {'color': '#0d6efd', 'opacity': 0.7}},
            ]
        }
        
        if prices:
            chart_option['series'].append({
                'name': '实收均价', 'type': 'line', 'yAxisIndex': 1, 'data': prices,
                'lineStyle': {'color': '#dc3545', 'width': 2},
                'itemStyle': {'color': '#dc3545'}
            })
        
        chart_element = DashECharts(option=chart_option, style={'height': '350px', 'width': '100%'})
    
    # 关键指标卡片
    metrics_row = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div("昨日均价", className="text-muted small"),
                    html.H5(f"¥{price_change.get('昨日均价', 0)}", className="mb-0"),
                    html.Small(
                        f"{price_change.get('变化率', 0):+.1f}%", 
                        className=f"text-{'success' if price_change.get('变化率', 0) > 0 else 'danger'}"
                    )
                ])
            ], className="text-center h-100")
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div("满减占比", className="text-muted small"),
                    html.H5(f"{activity_change.get('昨日满减占比', 0)}%", className="mb-0"),
                    html.Small(
                        f"{activity_change.get('变化', 0):+.1f}%", 
                        className=f"text-{'danger' if activity_change.get('变化', 0) > 0 else 'success'}"
                    )
                ])
            ], className="text-center h-100")
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div("智能诊断", className="text-muted small"),
                    html.P(insight_text, className="mb-0 small fw-bold text-primary")
                ])
            ], className="text-center h-100 bg-light")
        ], width=4),
    ], className="mb-3")
    
    return html.Div([
        metrics_row,
        chart_element
    ])


# ==================== 智能调价计算器回调函数 ====================

# 调价方向自动切换回调 - 根据商品来源自动设置提价/降价
@callback(
    Output("pricing-adjust-direction", "value"),
    Input("pricing-source-dropdown", "value"),
    prevent_initial_call=True
)
def auto_switch_adjust_direction(source):
    """根据商品来源自动切换调价方向"""
    from .pricing_engine import get_source_direction
    
    if not source or source.startswith('_header_'):
        raise PreventUpdate
    
    return get_source_direction(source)


# ==================== 智能梯度调价模式回调 ====================

@callback(
    [Output("pricing-smart-level-container", "style"),
     Output("pricing-manual-input-container", "style")],
    Input("pricing-adjust-mode", "value"),
    prevent_initial_call=True
)
def toggle_pricing_mode_display(mode):
    """切换智能梯度/手动输入模式的显示
    
    注意：使用 visibility 而不是 display:none，确保 Dash 能读取隐藏元素的值
    """
    if mode == 'smart':
        # 智能模式：显示智能梯度，隐藏手动输入
        return {'display': 'block'}, {'visibility': 'hidden', 'position': 'absolute', 'left': '-9999px'}
    else:
        # 手动模式：隐藏智能梯度，显示手动输入
        return {'visibility': 'hidden', 'position': 'absolute', 'left': '-9999px'}, {'display': 'block', 'visibility': 'visible', 'position': 'relative', 'left': 'auto'}


@callback(
    [Output("pricing-level-light", "outline"),
     Output("pricing-level-medium", "outline"),
     Output("pricing-level-heavy", "outline"),
     Output("pricing-smart-level-store", "data"),
     Output("pricing-level-hint", "children")],
    [Input("pricing-level-light", "n_clicks"),
     Input("pricing-level-medium", "n_clicks"),
     Input("pricing-level-heavy", "n_clicks")],
    [State("pricing-adjust-direction", "value")],
    prevent_initial_call=True
)
def update_smart_level_selection(n_light, n_medium, n_heavy, direction):
    """更新智能梯度档位选择状态和提示"""
    from dash import ctx
    triggered_id = ctx.triggered_id
    
    # 默认值
    light_outline, medium_outline, heavy_outline = True, True, True
    level = 'medium'
    
    if triggered_id == 'pricing-level-light':
        light_outline = False
        level = 'light'
    elif triggered_id == 'pricing-level-medium':
        medium_outline = False
        level = 'medium'
    elif triggered_id == 'pricing-level-heavy':
        heavy_outline = False
        level = 'heavy'
    else:
        medium_outline = False  # 默认中度
    
    # 根据调价方向和档位生成提示
    if direction == 'down':  # 降价
        target_margins = {'light': 15, 'medium': 8, 'heavy': 3}
        hint = f"降至 {target_margins[level]}% 利润率"
    else:  # 提价
        target_margins = {'light': 20, 'medium': 25, 'heavy': 30}
        hint = f"提至 {target_margins[level]}% 利润率"
    
    return light_outline, medium_outline, heavy_outline, level, hint


@callback(
    Output("pricing-level-hint", "children", allow_duplicate=True),
    Input("pricing-adjust-direction", "value"),
    State("pricing-smart-level-store", "data"),
    prevent_initial_call=True
)
def update_level_hint_on_direction_change(direction, level):
    """调价方向改变时更新提示"""
    level = level or 'medium'
    if direction == 'down':
        target_margins = {'light': 15, 'medium': 8, 'heavy': 3}
        return f"降至 {target_margins[level]}% 利润率"
    else:
        target_margins = {'light': 20, 'medium': 25, 'heavy': 30}
        return f"提至 {target_margins[level]}% 利润率"


# 快捷按钮动态更新回调 - 根据调价方向显示不同按钮（保留兼容性）
@callback(
    [Output("pricing-quick-buttons-container", "children"),
     Output("pricing-floor-warning", "children")],
    Input("pricing-adjust-direction", "value"),
    prevent_initial_call=True
)
def update_quick_buttons_and_warning(direction):
    """根据调价方向动态更新快捷按钮和保本底线提示"""
    import dash_bootstrap_components as dbc
    
    if direction == 'down':
        # 降价按钮
        buttons = dbc.ButtonGroup([
            dbc.Button("-5%", id='pricing-batch-1', color="outline-warning", size="sm", 
                      style={'padding': '2px 6px', 'fontSize': '10px'}),
            dbc.Button("-10%", id='pricing-batch-3', color="outline-warning", size="sm",
                      style={'padding': '2px 6px', 'fontSize': '10px'}),
            dbc.Button("-15%", id='pricing-batch-5', color="outline-danger", size="sm",
                      style={'padding': '2px 6px', 'fontSize': '10px'}),
            dbc.Button("-20%", id='pricing-batch-10', color="outline-danger", size="sm",
                      style={'padding': '2px 6px', 'fontSize': '10px'}),
        ], size="sm", className="mt-1")
        
        # 保本底线提示
        warning = html.Span([
            html.I(className="fas fa-shield-alt me-1"),
            "系统自动保本，不会亏本定价"
        ], className="text-success")
    else:
        # 提价按钮
        buttons = dbc.ButtonGroup([
            dbc.Button("+1%", id='pricing-batch-1', color="outline-secondary", size="sm", 
                      style={'padding': '2px 6px', 'fontSize': '10px'}),
            dbc.Button("+3%", id='pricing-batch-3', color="outline-secondary", size="sm",
                      style={'padding': '2px 6px', 'fontSize': '10px'}),
            dbc.Button("+5%", id='pricing-batch-5', color="outline-secondary", size="sm",
                      style={'padding': '2px 6px', 'fontSize': '10px'}),
            dbc.Button("+10%", id='pricing-batch-10', color="outline-secondary", size="sm",
                      style={'padding': '2px 6px', 'fontSize': '10px'}),
        ], size="sm", className="mt-1")
        
        # 无警告
        warning = ""
    
    return buttons, warning


# ========== 渠道选项更新回调（针对调价计算器） ==========
@callback(
    Output('pricing-channel-filter', 'options'),
    [Input('db-store-filter', 'value'),
     Input('pricing-source-dropdown', 'value')],
    prevent_initial_call=False
)
def update_pricing_channel_options(selected_stores, source):
    """根据选择的门店更新调价计算器的渠道选项"""
    GLOBAL_DATA = get_real_global_data()
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return [{'label': '全部渠道', 'value': 'all'}]
        
    df = GLOBAL_DATA.copy()
    
    # 门店筛选
    if selected_stores:
        if isinstance(selected_stores, str):
            selected_stores = [selected_stores]
        if len(selected_stores) > 0 and '门店名称' in df.columns:
            df = df[df['门店名称'].isin(selected_stores)]
    
    # 获取渠道列表
    channel_col = next((c for c in ['平台', '渠道', 'platform'] if c in df.columns), None)
    if not channel_col:
        return [{'label': '全部渠道', 'value': 'all'}]
        
    channels = sorted(df[channel_col].dropna().unique().tolist())
    
    options = [{'label': '📊 全部渠道', 'value': 'all'}]
    
    # 渠道emoji映射
    channel_emojis = {
        '美团': '🟡',
        '饿了么': '🔵', 
        '抖音': '🎵',
        '京东': '🔴',
        '拼多多': '🟠'
    }
    
    for channel in channels:
        emoji = channel_emojis.get(channel, '⚪')
        options.append({'label': f'{emoji} {channel}', 'value': str(channel)})
        
    return options


@callback(
    [Output("pricing-table-container", "children"),
     Output("pricing-data-store", "data", allow_duplicate=True)],
    [Input("pricing-source-dropdown", "value"),
     Input("pricing-calculate-btn", "n_clicks")],
    [State("db-store-filter", "value"),
     State("pricing-channel-filter", "value")],
    prevent_initial_call=True
)
def update_pricing_table(source, n_clicks, store, channel):
    """更新调价商品表格 - 复用诊断模块的数据获取逻辑"""
    from dash import ctx, dash_table
    from .pricing_engine import (
        get_product_elasticity, predict_profit_change, get_pricing_decision,
        get_stagnant_products, get_markdown_price_decision, get_source_direction
    )
    from .diagnosis_analysis import (
        get_overflow_products, get_price_abnormal_products, 
        get_product_group_key, ITEM_LEVEL_FIELDS
    )
    
    print(f"[调价计算器] 回调触发: source={source}, n_clicks={n_clicks}, store={store}, channel={channel}")
    
    # 直接从全局数据获取
    GLOBAL_DATA = get_real_global_data()
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        print("[调价计算器] GLOBAL_DATA 为空")
        return html.Div("请先加载数据", className="text-muted text-center py-4"), []
    
    if not source:
        print("[调价计算器] source 为空")
        return html.Div("请选择商品来源", className="text-muted text-center py-4"), []
    
    # 跳过分组标题
    if source.startswith('_header_'):
        print(f"[调价计算器] 跳过标题: {source}")
        raise PreventUpdate
    
    try:
        df = GLOBAL_DATA.copy()
        print(f"[调价计算器] 原始数据: {len(df)} 行, 列: {df.columns.tolist()[:8]}...")
        
        # 使用诊断模块的标准字段检测方式
        channel_col = next((c for c in ['渠道', '平台', 'channel'] if c in df.columns), None)
        store_col = next((c for c in ['门店名称', '门店', 'store'] if c in df.columns), None)
        product_key = get_product_group_key(df)  # 复用诊断模块的函数
        
        # 销量字段（与诊断模块一致）
        qty_col = '月售' if '月售' in df.columns else ('销量' if '销量' in df.columns else None)
        price_col = next((c for c in ['商品实售价', '实收价格'] if c in df.columns), None)
        cost_col = next((c for c in ['商品采购成本', '成本'] if c in df.columns), None)
        category_col = next((c for c in ['一级分类名', '一级分类', '分类'] if c in df.columns), None)
        name_col = '商品名称' if '商品名称' in df.columns else None
        
        print(f"[调价计算器] 字段映射: key={product_key}, 销量={qty_col}, 价格={price_col}, 成本={cost_col}")
        
        # 筛选门店和渠道
        if store and store_col:
            df = df[df[store_col] == store]
            print(f"[调价计算器] 门店筛选后: {len(df)} 行")
        
        # 渠道筛选（重要！支持分渠道定价）
        if channel and channel != 'all' and channel_col:
            df = df[df[channel_col] == channel]
            print(f"[调价计算器] 渠道筛选后: {len(df)} 行, 渠道={channel}")
        
        if df.empty:
            return html.Div("筛选后无数据", className="text-muted text-center py-4"), []
        
        # 根据商品来源获取数据 - 复用诊断模块的分析函数
        products_df = pd.DataFrame()
        
        if source == 'overflow':
            # 穿底商品 - 复用诊断模块的函数
            products_df = get_overflow_products(df)
            if products_df.empty:
                return html.Div("暂无穿底商品（利润>0的商品不在此列表）", className="text-muted text-center py-4"), []
        
        elif source == 'price_abnormal':
            # 价格异常商品 - 复用诊断模块的函数
            products_df = get_price_abnormal_products(df, store)
            if products_df.empty:
                return html.Div("暂无价格异常商品", className="text-muted text-center py-4"), []
        
        elif source == 'low_profit':
            # 低利润商品 - 自行计算
            if price_col and cost_col and qty_col:
                # 🔧 先计算单品成本（关键！原始数据中 商品采购成本 = 单品成本 × 销量）
                df['_销量'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(1).replace(0, 1)
                df['_单品成本'] = df[cost_col].fillna(0) / df['_销量']
                df['_profit_rate'] = ((df[price_col] - df['_单品成本']) / df[price_col].replace(0, np.nan) * 100).fillna(0)
                low_profit_df = df[df['_profit_rate'] < 10].copy()
                if low_profit_df.empty:
                    return html.Div("暂无低利润商品（利润率均>10%）", className="text-muted text-center py-4"), []
                
                # 聚合 - 使用单品成本
                agg_dict = {name_col: 'first'} if name_col else {}
                if category_col:
                    agg_dict[category_col] = 'first'
                if price_col:
                    agg_dict[price_col] = 'mean'
                agg_dict['_单品成本'] = 'mean'  # 使用计算后的单品成本
                if qty_col:
                    agg_dict[qty_col] = 'sum'
                
                products_df = low_profit_df.groupby(product_key).agg(agg_dict).reset_index()
                # 重命名单品成本列
                products_df = products_df.rename(columns={'_单品成本': '单品成本'})
            else:
                return html.Div("缺少价格、成本或销量字段", className="text-muted text-center py-4"), []
        
        elif source == 'sales_decline':
            # 销量下滑商品 - 近7天销量比历史均值下降超30%
            if qty_col:
                # 🔧 先计算单品成本
                if cost_col:
                    df['_销量'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(1).replace(0, 1)
                    df['_单品成本'] = df[cost_col].fillna(0) / df['_销量']
                
                agg_dict = {name_col: 'first'} if name_col else {}
                if category_col:
                    agg_dict[category_col] = 'first'
                if price_col:
                    agg_dict[price_col] = 'mean'
                if cost_col:
                    agg_dict['_单品成本'] = 'mean'  # 使用计算后的单品成本
                if qty_col:
                    agg_dict[qty_col] = 'sum'
                
                # 按商品聚合后筛选销量低于平均的
                products_agg = df.groupby(product_key).agg(agg_dict).reset_index()
                # 重命名单品成本列
                if '_单品成本' in products_agg.columns:
                    products_agg = products_agg.rename(columns={'_单品成本': '单品成本'})
                avg_sales = products_agg[qty_col].mean() if qty_col in products_agg.columns else 0
                if avg_sales > 0:
                    products_df = products_agg[products_agg[qty_col] < avg_sales * 0.7].copy()
                else:
                    products_df = pd.DataFrame()
                
                if products_df.empty:
                    return html.Div("暂无销量下滑商品", className="text-muted text-center py-4"), []
            else:
                return html.Div("缺少销量字段", className="text-muted text-center py-4"), []
        
        elif source == 'profit_decline':
            # 利润率下滑商品 - 利润率低于分类平均
            if price_col and cost_col and qty_col:
                # 🔧 先计算单品成本（关键！原始数据中 商品采购成本 = 单品成本 × 销量）
                df['_销量'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(1).replace(0, 1)
                df['_单品成本'] = df[cost_col].fillna(0) / df['_销量']
                df['_profit_rate'] = ((df[price_col] - df['_单品成本']) / df[price_col].replace(0, np.nan) * 100).fillna(0)
                
                agg_dict = {name_col: 'first'} if name_col else {}
                if category_col:
                    agg_dict[category_col] = 'first'
                if price_col:
                    agg_dict[price_col] = 'mean'
                agg_dict['_单品成本'] = 'mean'  # 使用计算后的单品成本
                if qty_col:
                    agg_dict[qty_col] = 'sum'
                agg_dict['_profit_rate'] = 'mean'
                
                products_agg = df.groupby(product_key).agg(agg_dict).reset_index()
                # 重命名单品成本列
                products_agg = products_agg.rename(columns={'_单品成本': '单品成本'})
                avg_rate = products_agg['_profit_rate'].mean()
                products_df = products_agg[products_agg['_profit_rate'] < avg_rate].copy()
                
                if products_df.empty:
                    return html.Div("暂无利润率下滑商品", className="text-muted text-center py-4"), []
            else:
                return html.Div("缺少价格、成本或销量字段", className="text-muted text-center py-4"), []
        
        elif source.startswith('stagnant_'):
            # 滞销品处理 - 使用 pricing_engine 的函数
            stagnant_level = source.replace('stagnant_', '')  # light, medium, heavy, severe, all
            products_df = get_stagnant_products(df, store, stagnant_level)
            
            if products_df.empty:
                level_names = {
                    'light': '轻度滞销（=7天）',
                    'medium': '中度滞销（8-15天）',
                    'heavy': '重度滞销（16-30天）',
                    'severe': '超重度滞销（>30天）',
                    'all': '滞销'
                }
                level_name = level_names.get(stagnant_level, '滞销')
                return html.Div(f"暂无{level_name}商品（库存>0且有连续无销量记录）", className="text-muted text-center py-4"), []
        
        # 注意：已移除 'all'（全部商品）选项，避免提价/降价逻辑冲突
        
        if products_df.empty:
            return html.Div("该分类暂无商品数据", className="text-muted text-center py-4"), []
        
        total_products = len(products_df)
        print(f"[调价计算器] 获取到 {total_products} 个商品")
        print(f"[调价计算器] 返回列名: {products_df.columns.tolist()[:10]}")
        
        # 不再限制数量，通过分页展示全部数据
        
        # 🔧 构建商品原价映射表（从原始数据获取每个商品的最大原价）
        # 这是为了解决聚合数据中原价可能不准确的问题
        product_original_price_map = {}
        if '商品原价' in df.columns and '商品名称' in df.columns:
            # 按商品名称分组，取原价的最大值
            price_agg = df.groupby('商品名称')['商品原价'].max()
            product_original_price_map = price_agg.to_dict()
            print(f"[调价计算器] 已构建商品原价映射表，共 {len(product_original_price_map)} 个商品")
        
        # 构建表格数据 - 根据诊断模块返回的实际列名映射
        table_data = []
        
        for _, row in products_df.iterrows():
            # 商品编码 - 店内码
            code = str(row.get('店内码', '') or row.get(product_key, '') or '')
            
            # 商品名称
            product_name = str(row.get('商品名称', '') or '')[:20]
            full_product_name = str(row.get('商品名称', '') or '')  # 完整名称用于查找原价
            
            # 分类 - 诊断模块返回的是"一级分类"，不是"一级分类名"
            category = str(row.get('一级分类', '') or row.get('一级分类名', '') or row.get(category_col, '') or '')[:10]
            
            # 价格 - 优先使用实收价格（诊断模块的标准）
            current_price = float(row.get('实收价格', 0) or row.get('商品实售价', 0) or row.get(price_col, 0) or 0)
            
            # 原价 - 商品原价（价格上限）
            # 🔧 优先从原始数据映射表获取原价（更准确）
            original_price = product_original_price_map.get(full_product_name, 0)
            if original_price <= 0:
                # 回退到聚合数据中的原价
                original_price = float(row.get('商品原价', 0) or row.get('原价', 0) or 0)
            # 如果原价仍然为0或小于实售价，使用实售价作为原价
            if original_price <= 0 or original_price < current_price:
                original_price = current_price
            
            # 成本 - 优先使用已计算的单品成本，避免使用总成本
            # 注意：商品采购成本是总成本(=单品成本×销量)，需要除以销量
            cost = float(row.get('单品成本', 0) or 0)
            if cost == 0:
                # 尝试从原始成本计算单品成本
                raw_cost = float(row.get('商品采购成本', 0) or row.get(cost_col, 0) or 0)
                raw_qty = float(row.get('月售', 0) or row.get('销量', 0) or row.get(qty_col, 0) or 1)
                if raw_qty == 0:
                    raw_qty = 1
                cost = raw_cost / raw_qty if raw_cost > 0 else 0
            
            # 销量 - 诊断模块返回的是"昨日总销量"
            daily_sales = float(row.get('昨日总销量', 0) or row.get('销量', 0) or row.get('昨日销量', 0) or row.get('月售', 0) or row.get(qty_col, 0) or 0)
            
            # 获取弹性系数
            elasticity, source_desc = get_product_elasticity(code, channel or '美团', category, None)
            
            # 计算当前利润率
            current_margin = ((current_price - cost) / current_price * 100) if current_price > 0 else 0
            
            # 获取商品来源对应的调价方向
            adjust_direction = get_source_direction(source)
            
            # 🌟 智能定价决策 - 根据调价方向选择不同策略
            smart_suggestion = ""
            recommended_price = current_price  # 默认用当前价格
            urgency_icon = ""
            
            if adjust_direction == 'down' or source.startswith('stagnant_'):
                # 🐌 降价场景 - 使用降价决策函数（保本底线）
                stagnant_days = int(row.get('滞销天数', 0) or 7)
                markdown_decision = get_markdown_price_decision(
                    current_price, cost, stagnant_days, daily_sales, category
                )
                
                if markdown_decision:
                    urgency_icon = markdown_decision.get('urgency_icon', '🐌')
                    recommended_price = markdown_decision.get('suggested_price', current_price)
                    discount_rate = markdown_decision.get('discount_rate', 0)
                    floor_price = markdown_decision.get('floor_price', cost)
                    is_at_floor = markdown_decision.get('at_floor', False)
                    
                    # 构建智能建议文本
                    if is_at_floor:
                        smart_suggestion = f"建议{discount_rate:+.0f}%(保本¥{floor_price:.2f})"
                    else:
                        smart_suggestion = f"建议{discount_rate:+.0f}%"
            else:
                # 📈 提价场景 - 使用原有提价决策
                decision = get_pricing_decision(
                    current_price, cost, daily_sales, elasticity, channel or '美团', category
                )
                
                if decision:
                    urgency_icon = decision.get('urgency_icon', '')
                    recommendations = decision.get('recommendations', [])
                    
                    # 找到推荐方案（optimal级别）
                    for rec in recommendations:
                        if rec.get('level') == 'optimal':
                            recommended_price = rec.get('price', current_price)
                            increase_pct = rec.get('increase', 0)
                            profit_change = rec.get('profit_change', 0)
                            smart_suggestion = f"建议+{increase_pct:.1f}%"
                            break
                    
                    # 如果没有optimal，用conservative
                    if not smart_suggestion:
                        for rec in recommendations:
                            if rec.get('level') == 'conservative':
                                recommended_price = rec.get('price', current_price)
                                increase_pct = rec.get('increase', 0)
                                smart_suggestion = f"可涨+{increase_pct:.1f}%"
                                break
                    
                    # 添加警告阈值
                    if decision.get('warning'):
                        threshold = decision.get('optimal_analysis', {}).get('warning_threshold')
                        if threshold and not smart_suggestion:
                            smart_suggestion = f"最高+{threshold:.0f}%"
            
            # 初始调整价格设为推荐价格
            target_price = recommended_price
            
            # 计算保本价和最大降幅
            floor_price = cost if cost > 0 else current_price
            max_discount = ((current_price - floor_price) / current_price * 100) if current_price > 0 and current_price > floor_price else 0
            # 计算最大涨幅（到原价的空间）
            max_increase = ((original_price - current_price) / current_price * 100) if current_price > 0 and original_price > current_price else 0
            
            table_data.append({
                '店内码': code,
                '商品名称': product_name if product_name else '--',
                '分类': category if category else '--',
                '原价': round(original_price, 2),  # 新增原价
                '实售价': round(current_price, 2),
                '成本': round(cost, 2),
                '保本价': f"¥{floor_price:.2f}",
                '最大降幅': f"{max_discount:.1f}%" if max_discount > 0 else "0%",
                '最大涨幅': f"{max_increase:.1f}%" if max_increase > 0 else "0%",  # 新增最大涨幅
                '当前利润率': f"{current_margin:.1f}%",
                '日均销量': round(daily_sales, 1),
                '弹性系数': round(elasticity, 2),
                '调整价格': round(target_price, 2),
                '调整说明': "--",  # 初始为空，批量调价时更新
                '预估销量变化': "--",
                '预估利润变化': "--"
            })
        
        # 计算预估变化
        for item in table_data:
            try:
                current_price = item['实售价']
                new_price = item['调整价格']
                cost = item['成本']
                daily_sales = item['日均销量']
                elasticity = item['弹性系数']
                
                if new_price != current_price and current_price > 0:
                    prediction = predict_profit_change(
                        current_price, new_price, cost, daily_sales, elasticity, channel or '美团'
                    )
                    item['预估销量变化'] = f"{prediction['qty_change_rate']:+.1f}%"
                    item['预估利润变化'] = f"{prediction['profit_change_rate']:+.1f}%"
            except Exception:
                pass
        
        # 创建DataTable
        data_table = dash_table.DataTable(
            id='pricing-data-table',
            columns=[
                {'name': '店内码', 'id': '店内码', 'editable': False},
                {'name': '商品名称', 'id': '商品名称', 'editable': False},
                {'name': '分类', 'id': '分类', 'editable': False},
                {'name': '原价', 'id': '原价', 'type': 'numeric', 'editable': False},  # 新增原价列
                {'name': '实售价', 'id': '实售价', 'type': 'numeric', 'editable': False},
                {'name': '成本', 'id': '成本', 'type': 'numeric', 'editable': False},
                {'name': '保本价', 'id': '保本价', 'editable': False},
                {'name': '最大降幅', 'id': '最大降幅', 'editable': False},
                {'name': '最大涨幅', 'id': '最大涨幅', 'editable': False},  # 新增最大涨幅列
                {'name': '当前利润率', 'id': '当前利润率', 'editable': False},
                {'name': '日均销量', 'id': '日均销量', 'type': 'numeric', 'editable': False},
                {'name': '弹性系数', 'id': '弹性系数', 'type': 'numeric', 'editable': False},
                {'name': '调整价格', 'id': '调整价格', 'type': 'numeric', 'editable': True},
                {'name': '调整说明', 'id': '调整说明', 'editable': False},  # 新增调整说明列
                {'name': '预估销量变化', 'id': '预估销量变化', 'editable': False},
                {'name': '预估利润变化', 'id': '预估利润变化', 'editable': False},
            ],
            data=table_data,
            editable=True,
            row_selectable='multi',
            selected_rows=[],
            page_size=20,
            page_action='native',  # 启用原生分页
            style_table={'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '8px',
                'fontSize': '13px',
                'minWidth': '60px',
                'maxWidth': '150px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'border': '1px solid #dee2e6'
            },
            style_data_conditional=[
                # 保本价列 - 突出显示
                {
                    'if': {'column_id': '保本价'},
                    'backgroundColor': '#fff3e0',
                    'color': '#e65100',
                    'fontWeight': 'bold'
                },
                # 最大降幅列 - 突出显示
                {
                    'if': {'column_id': '最大降幅'},
                    'backgroundColor': '#fce4ec',
                    'color': '#c2185b',
                    'fontWeight': 'bold'
                },

                # 调整价格列
                {
                    'if': {'column_id': '调整价格'},
                    'backgroundColor': '#fff3cd',
                    'fontWeight': 'bold'
                },
                {
                    'if': {
                        'filter_query': '{预估利润变化} contains "+"',
                        'column_id': '预估利润变化'
                    },
                    'color': '#198754',
                    'fontWeight': 'bold'
                },
                {
                    'if': {
                        'filter_query': '{预估利润变化} contains "-"',
                        'column_id': '预估利润变化'
                    },
                    'color': '#dc3545',
                    'fontWeight': 'bold'
                }
            ]
        )
        
        return data_table, table_data
        
    except Exception as e:
        print(f"调价表格数据加载错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"加载失败: {str(e)}", className="text-danger text-center py-4"), []


@callback(
    Output("pricing-summary-container", "children"),
    Input("pricing-data-store", "data"),
    prevent_initial_call=True
)
def update_pricing_effect_panel(pricing_data):
    """更新调价效果预估面板"""
    if not pricing_data:
        return html.Div("请先选择商品来源加载数据", className="text-muted text-center py-3")
    
    try:
        # 统计汇总
        total_products = len(pricing_data)
        adjusted_products = sum(1 for p in pricing_data if p.get('调整价格') != p.get('实售价'))
        
        total_current_profit = 0
        total_new_profit = 0
        
        for p in pricing_data:
            current_price = float(p.get('实售价', 0) or 0)
            new_price = float(p.get('调整价格', current_price) or current_price)
            cost = float(p.get('成本', 0) or 0)
            daily_sales = float(p.get('日均销量', 0) or 0)
            elasticity = float(p.get('弹性系数', -1.0) or -1.0)
            
            # 当前利润
            current_profit = (current_price - cost) * daily_sales
            total_current_profit += current_profit
            
            # 预估新利润
            if new_price != current_price and new_price > 0:
                price_change_rate = (new_price - current_price) / current_price
                qty_change_rate = price_change_rate * elasticity
                new_qty = daily_sales * (1 + qty_change_rate)
                new_profit = (new_price - cost) * new_qty
                total_new_profit += new_profit
            else:
                total_new_profit += current_profit
        
        profit_change = total_new_profit - total_current_profit
        profit_change_rate = (profit_change / total_current_profit * 100) if total_current_profit > 0 else 0
        
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.Div("商品数量", className="text-muted small"),
                    html.H5(f"{total_products}个", className="mb-0 text-primary")
                ], width=3, className="text-center"),
                dbc.Col([
                    html.Div("已调整", className="text-muted small"),
                    html.H5(f"{adjusted_products}个", className="mb-0 text-info")
                ], width=3, className="text-center"),
                dbc.Col([
                    html.Div("当前日利润", className="text-muted small"),
                    html.H5(f"¥{total_current_profit:.0f}", className="mb-0")
                ], width=3, className="text-center"),
                dbc.Col([
                    html.Div("预估日利润", className="text-muted small"),
                    html.H5([
                        f"¥{total_new_profit:.0f}",
                        html.Small(
                            f" ({profit_change_rate:+.1f}%)",
                            className=f"text-{'success' if profit_change_rate > 0 else 'danger'}"
                        )
                    ], className="mb-0")
                ], width=3, className="text-center"),
            ], className="mb-2"),
            html.Hr(className="my-2"),
            html.Div([
                html.Small("💡 提示：在表格中修改「调整价格」列可实时预览效果", className="text-muted")
            ], className="text-center")
        ])
        
    except Exception as e:
        return html.Div(f"计算错误: {str(e)}", className="text-danger text-center py-3")


@callback(
    Output("pricing-download", "data"),
    Input("pricing-export-btn", "n_clicks"),
    [State("pricing-data-store", "data"),
     State("db-store-filter", "value"),
     State("pricing-channel-filter", "value")],
    prevent_initial_call=True
)
def export_pricing_plan(n_clicks, pricing_data, store, channel):
    """导出调价方案Excel"""
    if not n_clicks or not pricing_data:
        raise PreventUpdate
    
    try:
        import io
        from datetime import datetime
        
        # 创建DataFrame
        export_df = pd.DataFrame(pricing_data)
        
        # 选择导出列
        export_columns = [
            '店内码', '商品名称', '分类', '实售价', '成本', '当前利润率',
            '日均销量', '弹性系数', '调整价格', '预估销量变化', '预估利润变化'
        ]
        export_df = export_df[[c for c in export_columns if c in export_df.columns]]
        
        # 统计汇总
        total_products = len(pricing_data)
        adjusted_products = sum(1 for p in pricing_data if p.get('调整价格') != p.get('实售价'))
        
        # 计算总利润变化
        total_current_profit = 0
        total_new_profit = 0
        for p in pricing_data:
            current_price = float(p.get('实售价', 0) or 0)
            new_price = float(p.get('调整价格', current_price) or current_price)
            cost = float(p.get('成本', 0) or 0)
            daily_sales = float(p.get('日均销量', 0) or 0)
            elasticity = float(p.get('弹性系数', -1.0) or -1.0)
            
            current_profit = (current_price - cost) * daily_sales
            total_current_profit += current_profit
            
            if new_price != current_price and new_price > 0 and current_price > 0:
                price_change_rate = (new_price - current_price) / current_price
                qty_change_rate = price_change_rate * elasticity
                new_qty = daily_sales * (1 + qty_change_rate)
                new_profit = (new_price - cost) * new_qty
                total_new_profit += new_profit
            else:
                total_new_profit += current_profit
        
        # 创建Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 调价明细
            export_df.to_excel(writer, sheet_name='调价明细', index=False)
            
            # 汇总信息
            summary_df = pd.DataFrame({
                '项目': ['门店', '渠道', '商品总数', '调价商品数', '当前日利润(元)', 
                        '预估日利润(元)', '利润变化率', '导出时间'],
                '值': [
                    store or '全部', 
                    channel if channel and channel != 'all' else '全部渠道',
                    total_products, 
                    adjusted_products,
                    f"{total_current_profit:.2f}",
                    f"{total_new_profit:.2f}",
                    f"{((total_new_profit - total_current_profit) / total_current_profit * 100) if total_current_profit > 0 else 0:+.1f}%",
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            })
            summary_df.to_excel(writer, sheet_name='汇总信息', index=False)
        
        output.seek(0)
        
        filename = f"调价方案_{store or '全部'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return dcc.send_bytes(output.getvalue(), filename)
        
    except Exception as e:
        print(f"导出调价方案失败: {e}")
        raise PreventUpdate


@callback(
    Output("pricing-export-btn", "disabled"),
    Input("pricing-data-store", "data"),
    prevent_initial_call=True
)
def toggle_export_button(pricing_data):
    """启用/禁用导出按钮"""
    return not (pricing_data and len(pricing_data) > 0)


@callback(
    Output("pricing-adjust-value", "value"),
    [Input("pricing-batch-1", "n_clicks"),
     Input("pricing-batch-3", "n_clicks"),
     Input("pricing-batch-5", "n_clicks"),
     Input("pricing-batch-10", "n_clicks")],
    [State("pricing-adjust-direction", "value")],
    prevent_initial_call=True
)
def update_adjust_value_from_quick_btn(n1, n3, n5, n10, direction):
    """快捷按钮更新调整幅度值 - 根据调价方向返回对应值"""
    from dash import ctx
    triggered_id = ctx.triggered_id
    
    # 降价模式的按钮值：-5%, -10%, -15%, -20%
    # 提价模式的按钮值：+1%, +3%, +5%, +10%
    if direction == 'down':
        if triggered_id == "pricing-batch-1":
            return 5  # 对应-5%
        elif triggered_id == "pricing-batch-3":
            return 10  # 对应-10%
        elif triggered_id == "pricing-batch-5":
            return 15  # 对应-15%
        elif triggered_id == "pricing-batch-10":
            return 20  # 对应-20%
    else:  # up 提价
        if triggered_id == "pricing-batch-1":
            return 1  # 对应+1%
        elif triggered_id == "pricing-batch-3":
            return 3  # 对应+3%
        elif triggered_id == "pricing-batch-5":
            return 5  # 对应+5%
        elif triggered_id == "pricing-batch-10":
            return 10  # 对应+10%
    return 3  # 默认值


@callback(
    [Output("pricing-table-container", "children", allow_duplicate=True),
     Output("pricing-data-store", "data", allow_duplicate=True),
     Output("pricing-summary-container", "children", allow_duplicate=True),
     Output("pricing-batch-status", "children"),
     Output("pricing-floor-alert-container", "children")],
    [Input("pricing-batch-target", "n_clicks"),
     Input("pricing-reset-btn", "n_clicks")],
    [State("pricing-data-store", "data"),
     State("pricing-adjust-mode", "value"),
     State("pricing-smart-level-store", "data"),
     State("pricing-target-margin", "value"),
     State("pricing-adjust-direction", "value"),
     State("pricing-channel-filter", "value")],
    prevent_initial_call=True
)
def batch_adjust_prices_smart(n_target, n_reset, pricing_data, adjust_mode, smart_level, target_margin_input, adjust_direction, channel):
    """
    批量调整价格 - 智能梯度模式
    
    核心逻辑：根据目标利润率计算每个商品的调整价格
    - 智能模式：根据档位确定目标利润率
    - 手动模式：使用用户输入的目标利润率
    """
    from dash import ctx, dash_table, no_update
    from .pricing_engine import predict_profit_change
    
    print(f"[调价计算] ★★★ batch_adjust_prices_smart 被调用!")
    print(f"[调价计算] n_target={n_target}, n_reset={n_reset}, adjust_mode={adjust_mode}")
    print(f"[调价计算] target_margin_input={target_margin_input}, adjust_direction={adjust_direction}")
    print(f"[调价计算] pricing_data 长度: {len(pricing_data) if pricing_data else 0}")
    
    if not pricing_data:
        status_msg = html.Span([
            html.I(className="fas fa-exclamation-triangle me-1"),
            "请先加载商品数据"
        ], className="text-warning small")
        return no_update, no_update, no_update, status_msg, ""
    
    triggered_id = ctx.triggered_id
    if not triggered_id:
        raise PreventUpdate
    
    # 判断是提价还是降价
    is_markdown = (adjust_direction == 'down')
    
    # ========== 先计算边界，再确定目标利润率 ==========
    # 遍历所有商品，计算可达到的利润率边界
    max_achievable_margin = 0  # 涨价能达到的最高利润率（价格=原价时）
    avg_current_margin = 0     # 当前平均利润率
    max_current_margin = 0     # 当前最高利润率
    min_current_margin = 1     # 当前最低利润率
    valid_items_count = 0
    total_margin = 0
    
    for item in pricing_data:
        current_price = float(item.get('实售价', 0) or 0)
        cost = float(item.get('成本', 0) or 0)
        original_price = float(item.get('原价', 0) or 0)
        
        if current_price <= 0 or cost <= 0:
            continue
        
        valid_items_count += 1
        
        # 原价如果无效，使用实售价
        if original_price <= 0:
            original_price = current_price
        
        # 涨价上限：价格=原价时的利润率
        if original_price > cost:
            margin_at_ceiling = (original_price - cost) / original_price
            max_achievable_margin = max(max_achievable_margin, margin_at_ceiling)
        
        # 当前利润率
        current_margin = (current_price - cost) / current_price
        total_margin += current_margin
        max_current_margin = max(max_current_margin, current_margin)
        min_current_margin = min(min_current_margin, current_margin)
    
    # 如果没有有效商品，使用默认边界
    if valid_items_count == 0:
        max_achievable_margin = 0.99
        avg_current_margin = 0.15
        max_current_margin = 0.30
        min_current_margin = 0.05
    else:
        avg_current_margin = total_margin / valid_items_count
    
    # 降价下限固定为0%（保本价）
    min_achievable_margin = 0.01  # 最低1%
    
    # ========== 确定目标利润率 ==========
    if adjust_mode == 'smart':
        # 智能梯度模式 - 根据档位确定目标利润率
        level = smart_level or 'medium'
        if is_markdown:  # 降价
            target_margins_map = {'light': 0.15, 'medium': 0.08, 'heavy': 0.03}
        else:  # 提价
            target_margins_map = {'light': 0.20, 'medium': 0.25, 'heavy': 0.30}
        target_margin = target_margins_map.get(level, 0.08 if is_markdown else 0.25)
        level_names = {'light': '轻度', 'medium': '中度', 'heavy': '重度'}
        mode_desc = f"智能{level_names.get(level, '中度')}"
    else:
        # 手动输入模式
        # 处理 None 值：如果输入为空，提示用户输入
        if target_margin_input is None or target_margin_input == '':
            print(f"[DEBUG] target_margin_input 为空，提示用户输入")
            status_msg = html.Span([
                html.I(className="fas fa-exclamation-triangle me-1"),
                "请输入目标利润率"
            ], className="text-warning")
            return no_update, no_update, no_update, status_msg, ""
        else:
            target_margin = float(target_margin_input) / 100
        mode_desc = "手动"
    
    print(f"[DEBUG] 目标利润率: {target_margin*100:.1f}%, 最大可达: {max_achievable_margin*100:.1f}%, 最小可达: {min_achievable_margin*100:.1f}%")
    print(f"[DEBUG] triggered_id={triggered_id}, is_markdown={is_markdown}, adjust_direction={adjust_direction}")
    
    # ========== 前置边界校验（强制阻止超限计算） ==========
    # 无论哪个按钮触发，都要进行边界校验
    boundary_exceeded = False
    boundary_msg = ""
    
    if not is_markdown:
        # 涨价模式：目标不能超过最大可达利润率
        if target_margin > max_achievable_margin:
            boundary_exceeded = True
            boundary_msg = f"涨价目标利润率 {target_margin*100:.0f}% 超过最大可达 {max_achievable_margin*100:.1f}%"
            print(f"[DEBUG] 涨价边界检查: target={target_margin}, max={max_achievable_margin}, exceeded={boundary_exceeded}")
    else:
        # 降价模式：目标不能低于保本价（0%），也不能超过最大可达
        if target_margin <= 0:
            boundary_exceeded = True
            boundary_msg = f"降价目标利润率 {target_margin*100:.0f}% 低于保本价下限 0%"
        elif target_margin > max_achievable_margin:
            boundary_exceeded = True
            boundary_msg = f"降价目标利润率 {target_margin*100:.0f}% 超过最大可达 {max_achievable_margin*100:.1f}%"
        print(f"[DEBUG] 降价边界检查: target={target_margin}, max={max_achievable_margin}, exceeded={boundary_exceeded}")
    
    if boundary_exceeded and triggered_id == "pricing-batch-target":
        print(f"[DEBUG] ★★★ 边界超限！阻止计算！{boundary_msg}")
        status_msg = html.Span([
            html.I(className="fas fa-exclamation-circle me-1"),
            f"⚠️ {boundary_msg}，已达边界上限"
        ], className="text-danger fw-bold")
        
        if not is_markdown:
            alert_content = f"根据当前商品数据，涨价最高可达利润率为 {max_achievable_margin*100:.1f}%（所有商品涨至原价时）。请输入 0% ~ {max_achievable_margin*100:.0f}% 之间的值。"
        else:
            alert_content = f"降价目标利润率范围：1% ~ {max_achievable_margin*100:.0f}%。输入的值超出此范围。"
        
        boundary_alert = dbc.Alert([
            html.I(className="fas fa-ban me-2"),
            html.Strong("边界提醒："),
            f" {alert_content}"
        ], color="danger", className="mb-2 py-2")
        
        print(f"[DEBUG] ★★★ 返回 no_update，阻止表格更新")
        return no_update, no_update, no_update, status_msg, boundary_alert
    
    # 确定调整操作和描述
    operation_desc = ""
    status_color = "success"
    
    if triggered_id == "pricing-reset-btn":
        operation_desc = "🔄 已重置为原价"
        status_color = "info"
    elif triggered_id == "pricing-batch-target":
        operation_desc = f"✅ 已调整至 {target_margin*100:.0f}% 利润率"
    
    # 更新数据并统计
    updated_data = []
    adjusted_count = 0  # 实际调整的商品数
    price_up_count = 0
    price_down_count = 0
    
    for item in pricing_data:
        new_item = item.copy()
        current_price = float(item.get('实售价', 0) or 0)
        cost = float(item.get('成本', 0) or 0)
        daily_sales = float(item.get('日均销量', 0) or 0)
        elasticity = float(item.get('弹性系数', -1.0) or -1.0)
        
        # 获取原价（商品标价）- 作为价格上限
        original_price = float(item.get('原价', 0) or 0)
        if original_price <= 0:
            original_price = current_price  # 如果没有原价数据，使用当前实售价
        
        # 计算保本价和最大可降幅
        floor_price = cost if cost > 0 else current_price
        max_discount = ((current_price - floor_price) / current_price * 100) if current_price > 0 and current_price > floor_price else 0
        
        # 计算最大涨幅（涨到原价）
        max_increase = ((original_price - current_price) / current_price * 100) if current_price > 0 and original_price > current_price else 0
        
        new_item['原价'] = round(original_price, 2)
        new_item['保本价'] = f"¥{floor_price:.2f}"
        new_item['最大降幅'] = f"{max_discount:.1f}%" if max_discount > 0 else "0%"
        new_item['最大涨幅'] = f"{max_increase:.1f}%" if max_increase > 0 else "0%"
        
        if triggered_id == "pricing-reset-btn":
            # 重置为实售价
            new_price = current_price
            new_item['调整说明'] = "已重置"
        else:
            # 计算当前利润率
            current_margin = (current_price - cost) / current_price if current_price > 0 else 0
            
            # 统一计算目标价格: 售价 = 成本 / (1 - 目标利润率)
            # 当目标利润率 >= 100% 时，理论上需要无限高价格，设为极大值以触发上限
            if target_margin >= 1.0:
                # 100%及以上利润率，理论价格无穷大
                calculated_price = float('inf')
            elif cost > 0:
                calculated_price = round(cost / (1 - target_margin), 2)
            else:
                calculated_price = current_price
            
            # 应用价格边界约束
            hit_ceiling = False  # 是否触及原价上限
            hit_floor = False    # 是否触及保本价下限
            already_at_ceiling = False  # 当前价格是否已经在原价上限
            already_at_floor = False    # 当前价格是否已经在保本下限
            
            # 判断当前价格是否已经在边界
            if current_price >= original_price:
                already_at_ceiling = True
            if current_price <= floor_price:
                already_at_floor = True
            
            # 判断是否触及边界（在应用限制之前判断）
            if calculated_price > original_price:
                hit_ceiling = True
            elif calculated_price < floor_price:
                hit_floor = True
            
            # 应用价格边界限制
            if hit_ceiling:
                # 触及原价上限，限制为原价
                new_price = round(original_price, 2)
            elif hit_floor:
                # 触及保本价下限，限制为保本价
                new_price = round(floor_price, 2)
            else:
                new_price = calculated_price
            
            # 计算实际价格变化（相对于当前实售价）
            if current_price > 0:
                price_change_pct = (new_price - current_price) / current_price * 100
            else:
                price_change_pct = 0
            
            # 计算理论价格变化（如果不受限制）
            if current_price > 0 and calculated_price != float('inf'):
                theoretical_change_pct = (calculated_price - current_price) / current_price * 100
            elif calculated_price == float('inf'):
                theoretical_change_pct = float('inf')  # 标记为无穷大
            else:
                theoretical_change_pct = 0
            
            # 生成调整说明
            # 优先判断：当前价格是否已在边界且需要超越边界
            if already_at_floor and theoretical_change_pct < -0.1:
                # 当前已是保本价，但目标需要降价
                if target_margin <= 0:
                    new_item['调整说明'] = f"已达保本下限(目标≤0%,无法再降)"
                else:
                    new_item['调整说明'] = f"已达保本下限(需降{abs(theoretical_change_pct):.1f}%,无法再降)"
                adjusted_count += 1
            elif already_at_ceiling and theoretical_change_pct > 0.1:
                # 当前已是原价，但目标需要涨价
                if theoretical_change_pct == float('inf'):
                    new_item['调整说明'] = f"已达原价上限(目标≥100%,无法再涨)"
                else:
                    new_item['调整说明'] = f"已达原价上限(需涨{theoretical_change_pct:.1f}%,无法再涨)"
                adjusted_count += 1
            elif hit_ceiling:
                # 触及原价上限
                if abs(price_change_pct) < 0.1:
                    # 已经是原价，无法再涨
                    if theoretical_change_pct == float('inf'):
                        new_item['调整说明'] = f"已达原价上限(目标≥100%)"
                    else:
                        new_item['调整说明'] = f"已达原价上限(需涨{theoretical_change_pct:.1f}%)"
                else:
                    if theoretical_change_pct == float('inf'):
                        new_item['调整说明'] = f"涨{price_change_pct:.1f}%(达原价上限,目标≥100%)"
                    else:
                        new_item['调整说明'] = f"涨{price_change_pct:.1f}%(达原价上限)"
                adjusted_count += 1
            elif hit_floor:
                # 触及保本价下限
                # 计算理论需要降多少才能达到目标利润率
                if target_margin <= 0:
                    # 目标利润率≤0%，显示特殊提示
                    if abs(price_change_pct) < 0.1:
                        new_item['调整说明'] = f"已达保本下限(目标≤0%)"
                    else:
                        new_item['调整说明'] = f"降{abs(price_change_pct):.1f}%(达保本下限,目标≤0%)"
                else:
                    if abs(price_change_pct) < 0.1:
                        # 已经是保本价，无法再降
                        new_item['调整说明'] = f"已达保本下限(需降{abs(theoretical_change_pct):.1f}%)"
                    else:
                        new_item['调整说明'] = f"降{abs(price_change_pct):.1f}%(达保本下限)"
                adjusted_count += 1
            elif abs(price_change_pct) < 0.1:
                # 价格几乎不变
                new_item['调整说明'] = f"无需调整(目标={target_margin*100:.0f}%)"
            elif price_change_pct > 0:
                # 涨价：目标利润率 > 当前利润率
                new_item['调整说明'] = f"涨{price_change_pct:.1f}%(目标{target_margin*100:.0f}%)"
                adjusted_count += 1
            else:
                # 降价：目标利润率 < 当前利润率
                # 说明当前商品利润率已经高于目标，需要降价才能达到目标
                new_item['调整说明'] = f"降{abs(price_change_pct):.1f}%(目标{target_margin*100:.0f}%<当前{current_margin*100:.0f}%)"
                adjusted_count += 1
        
        new_item['调整价格'] = round(new_price, 2)
        
        # 统计涨跌
        if new_price > current_price:
            price_up_count += 1
        elif new_price < current_price:
            price_down_count += 1
        
        # 计算预估变化
        if new_price != current_price and current_price > 0:
            prediction = predict_profit_change(
                current_price, new_price, cost, daily_sales, elasticity, channel or '美团'
            )
            if prediction:
                new_item['预估销量变化'] = f"{prediction.get('qty_change_rate', 0):+.1f}%"
                new_item['预估利润变化'] = f"{prediction.get('profit_change_rate', 0):+.1f}%"
            else:
                new_item['预估销量变化'] = "--"
                new_item['预估利润变化'] = "--"
        else:
            new_item['预估销量变化'] = "--"
            new_item['预估利润变化'] = "--"
        
        updated_data.append(new_item)
    
    # 创建更新后的表格
    data_table = dash_table.DataTable(
        id='pricing-data-table',
        columns=[
            {'name': '店内码', 'id': '店内码', 'editable': False},
            {'name': '商品名称', 'id': '商品名称', 'editable': False},
            {'name': '分类', 'id': '分类', 'editable': False},
            {'name': '实售价', 'id': '实售价', 'type': 'numeric', 'editable': False},
            {'name': '原价', 'id': '原价', 'type': 'numeric', 'editable': False},
            {'name': '成本', 'id': '成本', 'type': 'numeric', 'editable': False},
            {'name': '保本价', 'id': '保本价', 'editable': False},
            {'name': '最大降幅', 'id': '最大降幅', 'editable': False},
            {'name': '最大涨幅', 'id': '最大涨幅', 'editable': False},
            {'name': '当前利润率', 'id': '当前利润率', 'editable': False},
            {'name': '日均销量', 'id': '日均销量', 'type': 'numeric', 'editable': False},
            {'name': '弹性系数', 'id': '弹性系数', 'type': 'numeric', 'editable': False},
            {'name': '调整价格', 'id': '调整价格', 'type': 'numeric', 'editable': True},
            {'name': '调整说明', 'id': '调整说明', 'editable': False},
            {'name': '预估销量变化', 'id': '预估销量变化', 'editable': False},
            {'name': '预估利润变化', 'id': '预估利润变化', 'editable': False},
        ],
        data=updated_data,
        editable=True,
        row_selectable='multi',
        selected_rows=[],
        page_size=20,
        page_action='native',
        style_table={'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'},
        style_cell={
            'textAlign': 'center',
            'padding': '8px',
            'fontSize': '13px',
            'minWidth': '60px',
            'maxWidth': '150px',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'border': '1px solid #dee2e6'
        },
        style_data_conditional=[
            # 原价列 - 突出显示（标价上限）
            {
                'if': {'column_id': '原价'},
                'backgroundColor': '#e3f2fd',
                'color': '#1565c0',
                'fontWeight': 'bold'
            },
            # 保本价列 - 突出显示
            {
                'if': {'column_id': '保本价'},
                'backgroundColor': '#fff3e0',
                'color': '#e65100',
                'fontWeight': 'bold'
            },
            # 最大降幅列 - 突出显示
            {
                'if': {'column_id': '最大降幅'},
                'backgroundColor': '#fce4ec',
                'color': '#c2185b',
                'fontWeight': 'bold'
            },
            # 最大涨幅列 - 突出显示
            {
                'if': {'column_id': '最大涨幅'},
                'backgroundColor': '#e8f5e9',
                'color': '#2e7d32',
                'fontWeight': 'bold'
            },
            # 调整说明列
            {
                'if': {'column_id': '调整说明'},
                'fontWeight': 'bold',
                'fontSize': '12px'
            },
            {
                'if': {
                    'filter_query': '{调整说明} contains "降"',
                    'column_id': '调整说明'
                },
                'backgroundColor': '#e3f2fd',
                'color': '#1565c0'
            },
            {
                'if': {
                    'filter_query': '{调整说明} contains "涨"',
                    'column_id': '调整说明'
                },
                'backgroundColor': '#e8f5e9',
                'color': '#2e7d32'
            },
            {
                'if': {
                    'filter_query': '{调整说明} contains "上限" or {调整说明} contains "下限"',
                    'column_id': '调整说明'
                },
                'backgroundColor': '#fff8e1',
                'color': '#f57c00'
            },
            # 调整价格列
            {
                'if': {'column_id': '调整价格'},
                'backgroundColor': '#fff3cd',
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'filter_query': '{预估利润变化} contains "+"',
                    'column_id': '预估利润变化'
                },
                'color': '#198754',
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'filter_query': '{预估利润变化} contains "-"',
                    'column_id': '预估利润变化'
                },
                'color': '#dc3545',
                'fontWeight': 'bold'
            }
        ]
    )
    
    # 更新汇总面板
    total_products = len(updated_data)
    adjusted_products = sum(1 for p in updated_data if p.get('调整价格') != p.get('实售价'))
    
    total_current_profit = 0
    total_new_profit = 0
    
    for p in updated_data:
        current_price = float(p.get('实售价', 0) or 0)
        new_price = float(p.get('调整价格', current_price) or current_price)
        cost = float(p.get('成本', 0) or 0)
        daily_sales = float(p.get('日均销量', 0) or 0)
        elasticity = float(p.get('弹性系数', -1.0) or -1.0)
        
        current_profit = (current_price - cost) * daily_sales
        total_current_profit += current_profit
        
        if new_price != current_price and new_price > 0 and current_price > 0:
            price_change_rate = (new_price - current_price) / current_price
            qty_change_rate = price_change_rate * elasticity
            new_qty = daily_sales * (1 + qty_change_rate)
            new_profit = (new_price - cost) * new_qty
            total_new_profit += new_profit
        else:
            total_new_profit += current_profit
    
    profit_change_rate = ((total_new_profit - total_current_profit) / total_current_profit * 100) if total_current_profit > 0 else 0
    
    summary_panel = html.Div([
        dbc.Row([
            dbc.Col([
                html.Div("商品总数", className="text-muted small"),
                html.H5(f"{total_products}个", className="mb-0")
            ], width=2, className="text-center"),
            dbc.Col([
                html.Div("涨价", className="text-muted small"),
                html.H5(f"{price_up_count}个", className="mb-0 text-danger")
            ], width=2, className="text-center"),
            dbc.Col([
                html.Div("降价", className="text-muted small"),
                html.H5(f"{price_down_count}个", className="mb-0 text-success")
            ], width=2, className="text-center"),
            dbc.Col([
                html.Div("当前日利润", className="text-muted small"),
                html.H5(f"¥{total_current_profit:.0f}", className="mb-0")
            ], width=3, className="text-center"),
            dbc.Col([
                html.Div("预估日利润", className="text-muted small"),
                html.H5([
                    f"¥{total_new_profit:.0f}",
                    html.Small(
                        f" ({profit_change_rate:+.1f}%)",
                        className=f"text-{'success' if profit_change_rate > 0 else 'danger'}"
                    )
                ], className="mb-0")
            ], width=3, className="text-center"),
        ], className="mb-2"),
        html.Hr(className="my-2"),
        html.Div([
            html.Small(f"💡 目标利润率: {target_margin*100:.0f}% | 涨价{price_up_count}个 / 降价{price_down_count}个 / 不变{total_products - price_up_count - price_down_count}个", className="text-muted")
        ], className="text-center")
    ])
    
    # 生成状态消息
    if triggered_id == "pricing-batch-target":
        status_msg = html.Span([
            html.I(className="fas fa-check-circle me-1 text-success"),
            f"✅ 已计算完成：涨价{price_up_count}个，降价{price_down_count}个，不变{total_products - price_up_count - price_down_count}个"
        ], className="text-success small")
        floor_alert = ""
    else:
        status_msg = html.Span([
            html.I(className=f"fas fa-check-circle me-1 text-{status_color}"),
            f"{operation_desc}（{len(updated_data)}个商品）"
        ], className=f"text-{status_color} small")
        floor_alert = ""
    
    return data_table, updated_data, summary_panel, status_msg, floor_alert


# ==================== 📊 商品综合分析模块 (V3.0 - 科学统一模型) ====================
# 核心改进：基于品类内排名百分位的统一计算模型
# 评分和象限使用同一套逻辑，确保一致性

def calculate_enhanced_product_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    商品健康评分计算 V3.0（科学统一模型）
    
    核心设计：
    1. 先计算四维度原始得分（0-100）
    2. 再计算品类内排名百分位（0-1）
    3. 综合评分 = 品类内排名加权求和 × 100
    4. 象限分类 = 基于品类内排名（≥50% = 高，<50% = 低）
    5. 问题标签 = 基于品类内排名后50%的维度
    
    一致性保证：
    - 评分高 → 品类内排名靠前 → 不可能是问题商品
    - 评分低 → 品类内排名靠后 → 必然有问题标签
    
    V3.1更新：剔除"耗材"等非销售商品分类
    
    Returns:
        包含评分、等级、象限、问题标签的商品DataFrame
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    df_copy = df.copy()
    
    # ===== 剔除非销售商品（仅剔除"耗材"分类）=====
    category_col = '一级分类名' if '一级分类名' in df_copy.columns else None
    if category_col:
        # 仅剔除"耗材"分类（门店运营用品，非销售商品）
        exclude_categories = ['耗材']
        original_count = len(df_copy)
        df_copy = df_copy[~df_copy[category_col].isin(exclude_categories)]
        excluded_count = original_count - len(df_copy)
        if excluded_count > 0:
            print(f"📦 商品健康分析：已剔除 {excluded_count} 条耗材数据")
    
    if df_copy.empty:
        return pd.DataFrame()
    
    # ===== 字段映射 =====
    sales_col = '月售' if '月售' in df_copy.columns else '销量'
    cost_col = '商品采购成本' if '商品采购成本' in df_copy.columns else '成本'
    
    # 计算订单总收入（实收价格 × 销量）
    if '实收价格' in df_copy.columns and sales_col in df_copy.columns:
        df_copy['订单总收入'] = df_copy['实收价格'].fillna(0) * df_copy[sales_col].fillna(1)
    else:
        df_copy['订单总收入'] = df_copy.get('商品实售价', 0)
    
    # ===== 计算真实营销成本（订单级分摊到商品） =====
    # 营销活动字段（商家承担的优惠成本）
    marketing_cols = ['满减金额', '新客减免金额', '配送费减免金额', '商家代金券', 
                     '商家承担部分券', '满赠金额', '商家其他优惠', '商品减免金额']
    available_marketing_cols = [col for col in marketing_cols if col in df_copy.columns]
    
    if available_marketing_cols:
        # 计算每行的营销成本总和
        df_copy['行营销成本'] = df_copy[available_marketing_cols].fillna(0).sum(axis=1)
        # 按订单分摊：每个订单的营销成本按商品销售额占比分配
        df_copy['订单销售额占比'] = df_copy.groupby('订单ID')['订单总收入'].transform(
            lambda x: x / x.sum() if x.sum() > 0 else 1/len(x)
        )
        # 订单营销成本（每个订单所有行中取最大值，因为订单级字段在每行重复）
        df_copy['订单营销总成本'] = df_copy.groupby('订单ID')['行营销成本'].transform('max')
        # 分摊到商品
        df_copy['商品分摊营销成本'] = df_copy['订单营销总成本'] * df_copy['订单销售额占比']
    elif '平台服务费' in df_copy.columns:
        # 降级方案：使用平台服务费
        df_copy['商品分摊营销成本'] = df_copy['平台服务费'].fillna(0)
    elif '平台佣金' in df_copy.columns:
        df_copy['商品分摊营销成本'] = df_copy['平台佣金'].fillna(0)
    else:
        df_copy['商品分摊营销成本'] = 0
    
    # ===== 聚合到商品级别 =====
    agg_dict = {
        '订单总收入': 'sum',
        '利润额': 'sum',
        sales_col: 'sum',
        '订单ID': 'nunique',
        '商品分摊营销成本': 'sum'
    }
    
    if cost_col in df_copy.columns:
        agg_dict[cost_col] = 'sum'
    if '库存' in df_copy.columns or '剩余库存' in df_copy.columns:
        stock_field = '库存' if '库存' in df_copy.columns else '剩余库存'
        agg_dict[stock_field] = 'last'
    if '店内码' in df_copy.columns:
        agg_dict['店内码'] = 'first'
    
    # 新增：三级分类
    category3_col = '三级分类名' if '三级分类名' in df_copy.columns else ('三级分类' if '三级分类' in df_copy.columns else None)
    if category3_col:
        agg_dict[category3_col] = 'first'
    
    # 新增：价格字段（用于计算单品利润率）
    if '商品原价' in df_copy.columns:
        agg_dict['商品原价'] = 'mean'  # 取平均（同商品可能有不同活动价）
    if '商品实售价' in df_copy.columns:
        agg_dict['商品实售价'] = 'mean'
    if '实收价格' in df_copy.columns:
        agg_dict['实收价格'] = 'mean'
    
    # 分组字段
    group_cols = ['商品名称']
    if category_col and category_col in df_copy.columns:
        group_cols.append(category_col)
    
    product_data = df_copy.groupby(group_cols).agg(agg_dict).reset_index()
    
    # 重命名列
    product_data = product_data.rename(columns={
        '订单总收入': '销售额',
        sales_col: '销量',
        '订单ID': '订单数',
        '商品分摊营销成本': '营销成本'
    })
    if cost_col in product_data.columns:
        product_data = product_data.rename(columns={cost_col: '成本'})
    
    # 统一库存字段名
    if '剩余库存' in product_data.columns:
        product_data = product_data.rename(columns={'剩余库存': '库存'})
    
    # 统一三级分类字段名
    if category3_col and category3_col in product_data.columns and category3_col != '三级分类名':
        product_data = product_data.rename(columns={category3_col: '三级分类名'})
    
    # ===== 计算基础指标 =====
    # 单品成本 = 总成本 / 销量
    product_data['单品成本'] = np.where(
        product_data['销量'] > 0,
        product_data['成本'] / product_data['销量'],
        0
    )
    
    # 综合利润率（汇总口径）= 利润额 / 销售额
    product_data['综合利润率'] = np.where(
        product_data['销售额'] > 0,
        (product_data['利润额'] / product_data['销售额'] * 100),
        0
    )
    
    # 定价利润率 = (商品原价 - 单品成本) / 商品原价
    if '商品原价' in product_data.columns:
        product_data['定价利润率'] = np.where(
            product_data['商品原价'] > 0,
            ((product_data['商品原价'] - product_data['单品成本']) / product_data['商品原价'] * 100),
            0
        )
    else:
        product_data['定价利润率'] = 0
    
    # 售罄率 = 销量 / (销量 + 库存)
    if '库存' in product_data.columns:
        product_data['售罄率'] = np.where(
            (product_data['销量'] + product_data['库存']) > 0,
            (product_data['销量'] / (product_data['销量'] + product_data['库存']) * 100),
            50
        )
    else:
        product_data['售罄率'] = 50  # 默认值
    
    # 营销ROI = (销售额 - 营销成本) / 营销成本
    product_data['营销ROI'] = np.where(
        product_data['营销成本'] > 0,
        (product_data['销售额'] - product_data['营销成本']) / product_data['营销成本'],
        10  # 无营销成本时给予高ROI
    )
    
    # 营销占比 = 营销成本 / 销售额
    product_data['营销占比'] = np.where(
        product_data['销售额'] > 0,
        (product_data['营销成本'] / product_data['销售额'] * 100),
        0
    )
    
    # 库存周转天数 = 库存 / 日均销量 × 30（假设数据周期30天）
    days_in_data = 30  # 数据周期
    product_data['日均销量'] = product_data['销量'] / days_in_data
    if '库存' in product_data.columns:
        product_data['库存周转天数'] = np.where(
            product_data['日均销量'] > 0,
            product_data['库存'] / product_data['日均销量'],
            999  # 无销量时设为999天
        )
    else:
        product_data['库存周转天数'] = 30  # 默认值
    
    # ===== 计算品类动态阈值（60分位数）=====
    # 注：保留这些阈值用于参考，但不再用于象限判断
    if category_col and category_col in product_data.columns:
        product_data['品类利润率阈值'] = product_data.groupby(category_col)['综合利润率'].transform(
            lambda x: x.quantile(0.6) if len(x) >= 5 else x.median()
        )
        product_data['品类销量阈值'] = product_data.groupby(category_col)['销量'].transform(
            lambda x: x.quantile(0.6) if len(x) >= 5 else x.median()
        )
        product_data['品类营销阈值'] = product_data.groupby(category_col)['营销占比'].transform(
            lambda x: x.quantile(0.4) if len(x) >= 5 else x.median()
        )
    else:
        product_data['品类利润率阈值'] = product_data['综合利润率'].quantile(0.6)
        product_data['品类销量阈值'] = product_data['销量'].quantile(0.6)
        product_data['品类营销阈值'] = product_data['营销占比'].quantile(0.4)
    
    # ===== 四大维度原始得分（0-100分）=====
    
    # 1. 盈利能力分 (权重40%)
    profit_90 = max(product_data['利润额'].quantile(0.9), 1)
    product_data['利润率得分'] = (product_data['综合利润率'].clip(0, 50) / 50 * 60).fillna(0)
    product_data['利润额得分'] = (product_data['利润额'].clip(0, profit_90) / profit_90 * 40).fillna(0)
    product_data['盈利能力分'] = (product_data['利润率得分'] + product_data['利润额得分']).clip(0, 100)
    
    # 2. 动销健康分 (权重30%)
    volume_90 = max(product_data['销量'].quantile(0.9), 1)
    product_data['售罄率得分'] = (product_data['售罄率'].clip(0, 100) / 100 * 50).fillna(0)
    product_data['销量得分'] = (product_data['销量'].clip(0, volume_90) / volume_90 * 50).fillna(0)
    product_data['动销健康分'] = (product_data['售罄率得分'] + product_data['销量得分']).clip(0, 100)
    
    # 3. 营销效率分 (权重15%)
    roi_90 = max(product_data['营销ROI'].clip(-10, 100).quantile(0.9), 1)
    product_data['ROI得分'] = (product_data['营销ROI'].clip(0, roi_90) / roi_90 * 60).fillna(30)
    product_data['营销占比得分'] = ((100 - product_data['营销占比'].clip(0, 100)) / 100 * 40).fillna(20)
    product_data['营销效率分'] = (product_data['ROI得分'] + product_data['营销占比得分']).clip(0, 100)
    
    # 4. 库存压力分 (权重15%)
    def calc_stock_score(days):
        if days <= 7:
            return 100
        elif days <= 30:
            return 100 - (days - 7) * (40 / 23)
        elif days <= 90:
            return 60 - (days - 30) * (40 / 60)
        else:
            return max(0, 20 - (days - 90) * 0.2)
    
    product_data['库存压力分'] = product_data['库存周转天数'].apply(calc_stock_score).clip(0, 100)
    
    # ===== 🔬 核心改进：品类内排名百分位（科学统一模型）=====
    # 统一计算逻辑：评分和象限都基于品类内排名
    
    def calc_percentile_rank(series):
        """计算百分位排名（0-1），越高越好"""
        return series.rank(pct=True, method='average')
    
    if category_col and category_col in product_data.columns:
        # 按品类计算各维度的排名百分位
        product_data['盈利排名'] = product_data.groupby(category_col)['盈利能力分'].transform(calc_percentile_rank)
        product_data['动销排名'] = product_data.groupby(category_col)['动销健康分'].transform(calc_percentile_rank)
        product_data['营销排名'] = product_data.groupby(category_col)['营销效率分'].transform(calc_percentile_rank)
        product_data['库存排名'] = product_data.groupby(category_col)['库存压力分'].transform(calc_percentile_rank)
    else:
        # 全局排名
        product_data['盈利排名'] = calc_percentile_rank(product_data['盈利能力分'])
        product_data['动销排名'] = calc_percentile_rank(product_data['动销健康分'])
        product_data['营销排名'] = calc_percentile_rank(product_data['营销效率分'])
        product_data['库存排名'] = calc_percentile_rank(product_data['库存压力分'])
    
    # ===== 综合评分（品类内排名加权求和）=====
    product_data['综合得分'] = (
        product_data['盈利排名'] * 0.40 +
        product_data['动销排名'] * 0.30 +
        product_data['营销排名'] * 0.15 +
        product_data['库存排名'] * 0.15
    ) * 100  # 转换为0-100分
    product_data['综合得分'] = product_data['综合得分'].round(1)
    
    # ===== 等级判定（基于百分位，自然分布）=====
    def get_score_level(score):
        if score >= 75:  # 前25%
            return '⭐ 优秀'
        elif score >= 50:  # 前50%
            return '✅ 良好'
        elif score >= 25:  # 前75%
            return '📊 一般'
        else:  # 后25%
            return '⚠️ 待优化'
    
    product_data['评分等级'] = product_data['综合得分'].apply(get_score_level)
    
    # ===== 三维度标签（基于品类内排名，与评分一致）=====
    # 核心改进：使用排名百分位判断，而非原始指标
    product_data['毛利维度'] = np.where(
        product_data['盈利排名'] >= 0.5, '高盈利', '低盈利'  # 品类内前50%
    )
    product_data['动销维度'] = np.where(
        product_data['动销排名'] >= 0.5, '高动销', '低动销'  # 品类内前50%
    )
    product_data['营销维度'] = np.where(
        product_data['营销排名'] >= 0.5, '高效率', '低效率'  # 品类内前50%（效率高=营销成本低）
    )
    
    # ===== 八象限分类（基于品类内排名，与评分一致）=====
    def classify_octant(row):
        """三维度八象限分类（基于品类内排名）"""
        high_profit = row['毛利维度'] == '高盈利'
        high_sales = row['动销维度'] == '高动销'
        high_efficiency = row['营销维度'] == '高效率'  # 高效率 = 营销成本低
        
        if high_profit and high_sales and high_efficiency:
            return '🌟 明星商品'      # 高盈利+高动销+高效率 = 完美
        elif high_profit and high_sales and not high_efficiency:
            return '💰 现金牛'        # 高盈利+高动销+低效率 = 赚钱但成本高
        elif high_profit and not high_sales and high_efficiency:
            return '💎 潜力商品'      # 高盈利+低动销+高效率 = 等待爆发
        elif high_profit and not high_sales and not high_efficiency:
            return '📉 待观察'        # 高盈利+低动销+低效率 = 投入大回报小
        elif not high_profit and high_sales and high_efficiency:
            return '🚀 引流商品'      # 低盈利+高动销+高效率 = 薄利多销
        elif not high_profit and high_sales and not high_efficiency:
            return '⚠️ 高成本引流'    # 低盈利+高动销+低效率 = 亏本赚吆喝
        elif not high_profit and not high_sales and high_efficiency:
            return '🐌 滞销品'        # 低盈利+低动销+高效率 = 无人问津
        else:
            return '🚨 问题商品'      # 低盈利+低动销+低效率 = 立即止损
    
    product_data['八象限分类'] = product_data.apply(classify_octant, axis=1)
    
    # ===== 问题标签（基于品类内排名后50%）=====
    def get_problem_tags(row):
        """生成问题标签（基于品类内排名）"""
        tags = []
        if row['盈利排名'] < 0.5:
            tags.append('低盈利')
        if row['动销排名'] < 0.5:
            tags.append('低动销')
        if row['营销排名'] < 0.5:
            tags.append('高营销成本')
        if row['库存排名'] < 0.5:
            tags.append('库存积压')
        return '｜'.join(tags) if tags else '健康'
    
    product_data['问题标签'] = product_data.apply(get_problem_tags, axis=1)
    
    # ===== 业务建议 =====
    octant_advice = {
        '🌟 明星商品': '保持现状，可适当提价测试',
        '💰 现金牛': '优化营销，降低推广成本',
        '💎 潜力商品': '增加曝光，提升动销',
        '📉 待观察': '减少营销投入，等待自然动销',
        '🚀 引流商品': '考虑提价，或定位为引流款',
        '⚠️ 高成本引流': '降低营销投入或提价',
        '🐌 滞销品': '清仓促销或下架',
        '🚨 问题商品': '立即止损，停止营销投入'
    }
    product_data['业务建议'] = product_data['八象限分类'].map(octant_advice)
    
    # 排序
    product_data = product_data.sort_values('综合得分', ascending=False).reset_index(drop=True)
    product_data['排名'] = range(1, len(product_data) + 1)
    
    return product_data


def create_product_health_content(product_scores: pd.DataFrame, category_filter: str = None, selected_category: str = None) -> html.Div:
    """
    创建商品健康分析的动态内容（评分概览Tab + 象限分布Tab）
    
    Args:
        product_scores: 全量商品评分数据
        category_filter: 当前选中的品类（用于筛选数据）
        selected_category: 当前选中的品类名称（用于高亮按钮）
    
    Returns:
        包含Tab内容的html.Div
    """
    if product_scores.empty:
        return html.Div("暂无商品数据", className="text-center text-muted p-4")
    
    # 获取品类列
    category_col = '一级分类名' if '一级分类名' in product_scores.columns else None
    
    # 根据品类筛选数据
    if category_filter and category_filter != '__all__' and category_col:
        filtered_scores = product_scores[product_scores[category_col] == category_filter].copy()
        if filtered_scores.empty:
            return html.Div(f"品类 '{category_filter}' 暂无商品数据", className="text-center text-muted p-4")
    else:
        filtered_scores = product_scores.copy()
        category_filter = None  # 重置为None表示全部
    
    # ===== 统计数据（基于筛选后的数据）=====
    total_products = len(filtered_scores)
    avg_score = filtered_scores['综合得分'].mean()
    
    # 评分等级统计
    excellent_count = len(filtered_scores[filtered_scores['评分等级'] == '⭐ 优秀'])
    good_count = len(filtered_scores[filtered_scores['评分等级'] == '✅ 良好'])
    normal_count = len(filtered_scores[filtered_scores['评分等级'] == '📊 一般'])
    poor_count = len(filtered_scores[filtered_scores['评分等级'] == '⚠️ 待优化'])
    
    # 八象限统计
    octant_counts = filtered_scores['八象限分类'].value_counts().to_dict()
    
    # ===== 评分分布图 =====
    score_dist_option = {
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
        'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'top': '10%', 'containLabel': True},
        'xAxis': {'type': 'category', 'data': ['优秀(75+)', '良好(50-74)', '一般(25-49)', '待优化(<25)'],
                  'axisLabel': {'fontSize': 11}},
        'yAxis': {'type': 'value', 'axisLabel': {'fontSize': 10}},
        'series': [{
            'type': 'bar',
            'data': [
                {'value': excellent_count, 'itemStyle': {'color': '#52c41a'}},
                {'value': good_count, 'itemStyle': {'color': '#1890ff'}},
                {'value': normal_count, 'itemStyle': {'color': '#faad14'}},
                {'value': poor_count, 'itemStyle': {'color': '#ff7875'}}
            ],
            'label': {'show': True, 'position': 'top', 'fontSize': 11, 'formatter': '{c}个'}
        }]
    }
    
    # ===== 评分等级可点击按钮列表 =====
    score_level_items = []
    score_levels = [
        ('⭐ 优秀', '75分以上', excellent_count, '#52c41a', 'success'),
        ('✅ 良好', '50-74分', good_count, '#1890ff', 'primary'),
        ('📊 一般', '25-49分', normal_count, '#faad14', 'warning'),
        ('⚠️ 待优化', '25分以下', poor_count, '#ff7875', 'danger'),
    ]
    
    for level_name, level_desc, count, color, btn_color in score_levels:
        pct = count / total_products * 100 if total_products > 0 else 0
        score_level_items.append(
            dbc.Button([
                dbc.Row([
                    dbc.Col([
                        html.Span(level_name, className="fw-bold", style={'fontSize': '13px'}),
                        html.Small(f" {level_desc}", className="text-muted ms-1", style={'fontSize': '10px'})
                    ], width=5),
                    dbc.Col([
                        html.Div([
                            html.Div(style={
                                'width': f'{pct}%', 
                                'height': '14px', 
                                'backgroundColor': color, 
                                'borderRadius': '4px',
                                'transition': 'width 0.3s'
                            })
                        ], style={
                            'height': '14px', 
                            'backgroundColor': '#f0f0f0', 
                            'borderRadius': '4px',
                            'flex': '1'
                        })
                    ], width=4, className="d-flex align-items-center"),
                    dbc.Col([
                        html.Span(f"{count}个", className="fw-bold", style={'fontSize': '12px'}),
                        html.Small(f" ({pct:.0f}%)", className="text-muted", style={'fontSize': '10px'})
                    ], width=3, className="text-end"),
                ], className="w-100 align-items-center", style={'minHeight': '20px'})
            ],
            id={'type': 'score-level-filter-btn', 'index': level_name},
            color='light',
            size="sm",
            className="mb-1 w-100 text-start border",
            style={'borderLeftWidth': '4px', 'borderLeftColor': color}
            )
        )
    
    # ===== 品类平均分图（如果未筛选品类，显示TOP10；如果已筛选，显示该品类的维度得分）=====
    category_bar_option = None
    if not category_filter and category_col:
        # 未筛选：显示各品类平均分TOP10
        # 过滤掉品类名为空或NaN的数据
        valid_category_data = product_scores[product_scores[category_col].notna() & (product_scores[category_col] != '')]
        category_stats = valid_category_data.groupby(category_col).agg({
            '综合得分': 'mean',
            '商品名称': 'count'
        }).reset_index()
        category_stats.columns = [category_col, '平均分', '商品数']
        category_stats = category_stats.sort_values('平均分', ascending=False)
        
        categories = category_stats[category_col].tolist()[:10]
        scores = category_stats['平均分'].tolist()[:10]
        
        bar_colors = []
        for s in scores:
            if s >= 75:
                bar_colors.append('#52c41a')
            elif s >= 50:
                bar_colors.append('#1890ff')
            elif s >= 25:
                bar_colors.append('#faad14')
            else:
                bar_colors.append('#ff7875')
        
        category_bar_option = {
            'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'},
                       'formatter': '{b}<br/>平均分: {c}分'},
            'grid': {'left': '3%', 'right': '8%', 'bottom': '3%', 'top': '10%', 'containLabel': True},
            'xAxis': {'type': 'value', 'max': 100, 'axisLabel': {'fontSize': 10}},
            'yAxis': {'type': 'category', 'data': categories[::-1], 'axisLabel': {'fontSize': 10}},
            'series': [{
                'type': 'bar',
                'data': [{'value': round(s, 1), 'itemStyle': {'color': c}} 
                        for s, c in zip(scores[::-1], bar_colors[::-1])],
                'label': {'show': True, 'position': 'right', 'fontSize': 10, 'formatter': '{c}分'}
            }]
        }
    
    # ===== 八象限进度条列表 =====
    octant_colors = {
        '🌟 明星商品': '#52c41a',
        '💰 现金牛': '#73d13d',
        '💎 潜力商品': '#722ed1',
        '📉 待观察': '#9254de',
        '🚀 引流商品': '#1890ff',
        '⚠️ 高成本引流': '#faad14',
        '🐌 滞销品': '#8c8c8c',
        '🚨 问题商品': '#ff4d4f'
    }
    
    octant_descriptions = [
        ('🌟 明星商品', '高盈利+高动销+高效率', 'success'),
        ('💰 现金牛', '高盈利+高动销+低效率', 'success'),
        ('💎 潜力商品', '高盈利+低动销+高效率', 'primary'),
        ('📉 待观察', '高盈利+低动销+低效率', 'warning'),
        ('🚀 引流商品', '低盈利+高动销+高效率', 'info'),
        ('⚠️ 高成本引流', '低盈利+高动销+低效率', 'warning'),
        ('🐌 滞销品', '低盈利+低动销+高效率', 'secondary'),
        ('🚨 问题商品', '低盈利+低动销+低效率', 'danger'),
    ]
    
    total_count = sum(octant_counts.values()) if octant_counts else 1
    octant_progress_items = []
    for name, desc, btn_color in octant_descriptions:
        count = octant_counts.get(name, 0)
        pct = count / total_count * 100 if total_count > 0 else 0
        color = octant_colors.get(name, '#8c8c8c')
        
        octant_progress_items.append(
            dbc.Button([
                dbc.Row([
                    dbc.Col([
                        html.Span(name, className="fw-bold", style={'fontSize': '13px'}),
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            html.Div(style={
                                'width': f'{pct}%', 
                                'height': '16px', 
                                'backgroundColor': color, 
                                'borderRadius': '4px',
                                'transition': 'width 0.3s'
                            })
                        ], style={
                            'height': '16px', 
                            'backgroundColor': '#f0f0f0', 
                            'borderRadius': '4px',
                            'flex': '1'
                        })
                    ], width=5, className="d-flex align-items-center"),
                    dbc.Col([
                        html.Span(f"{count}个", className="fw-bold", style={'fontSize': '13px'}),
                        html.Small(f" ({pct:.0f}%)", className="text-muted", style={'fontSize': '11px'})
                    ], width=3, className="text-end"),
                ], className="w-100 align-items-center", style={'minHeight': '24px'})
            ],
            id={'type': 'octant-filter-btn', 'index': name},
            color='light',
            size="sm",
            className="mb-2 w-100 text-start border",
            style={'borderLeftWidth': '4px', 'borderLeftColor': color}
            )
        )
    
    # ===== 构建Tab内容 =====
    filter_hint = f"品类: {category_filter}" if category_filter else "全部商品"
    
    return html.Div([
        # Tab切换
        dbc.Tabs([
            # Tab1: 评分概览
            dbc.Tab([
                html.Div([
                    # 筛选提示
                    html.Div([
                        html.Small(f"📊 当前显示: {filter_hint} ({total_products}个商品)", 
                                  className="text-primary fw-bold")
                    ], className="mb-2") if category_filter else html.Div(),
                    
                    # 统计摘要
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Span("📊 商品总数", className="text-muted d-block", style={'fontSize': '12px'}),
                                html.H4(f"{total_products}", className="mb-0 text-primary")
                            ], className="text-center p-2")
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.Span("📈 平均分", className="text-muted d-block", style={'fontSize': '12px'}),
                                html.H4(f"{avg_score:.1f}", className="mb-0 text-info")
                            ], className="text-center p-2")
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.Span("⭐ 优秀", className="text-muted d-block", style={'fontSize': '12px'}),
                                html.H4(f"{excellent_count}", className="mb-0 text-success")
                            ], className="text-center p-2")
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.Span("⚠️ 待优化", className="text-muted d-block", style={'fontSize': '12px'}),
                                html.H4(f"{poor_count}", className="mb-0 text-danger")
                            ], className="text-center p-2")
                        ], width=3),
                    ], className="mb-3 bg-light rounded"),
                    
                    # 双图改为：左侧可点击评分列表 + 右侧品类柱状图
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Small("📊 评分分布 (点击筛选)", className="text-muted d-block mb-2 text-center fw-bold"),
                                html.Div(score_level_items, className="px-1")
                            ], className="border rounded p-2", style={'minHeight': '200px'})
                        ], width=6),
                        dbc.Col([
                            html.Div([
                                html.Small("各品类平均分 TOP10" if not category_filter else f"{category_filter} 商品分布", 
                                          className="text-muted d-block mb-2 text-center fw-bold"),
                                DashECharts(
                                    option=category_bar_option,
                                    style={'height': '200px', 'width': '100%'}
                                ) if (ECHARTS_AVAILABLE and category_bar_option) else html.Div([
                                    html.Div("已筛选单个品类" if category_filter else "暂无品类数据", 
                                            className="text-muted text-center p-5")
                                ], className="p-3")
                            ], className="border rounded p-2", style={'minHeight': '200px'})
                        ], width=6),
                    ], className="mb-3"),
                ], className="pt-3")
            ], label="📊 评分概览", tab_id="tab-score"),
            
            # Tab2: 象限分布
            dbc.Tab([
                html.Div([
                    # 筛选提示
                    html.Div([
                        html.Small(f"🎯 当前显示: {filter_hint} ({total_products}个商品)", 
                                  className="text-primary fw-bold")
                    ], className="mb-2") if category_filter else html.Div(),
                    
                    # 说明
                    dbc.Alert([
                        html.Strong("🔬 科学分析模型："),
                        " 基于品类内排名百分位，每个商品与同品类商品比较。",
                        html.Br(),
                        html.Small("高盈利/动销/效率 = 品类内排名前50%，低 = 后50%。点击任意行可筛选表格。", className="text-muted")
                    ], color="info", className="mb-3 py-2"),
                    
                    # 象限进度条列表
                    html.Div([
                        html.Div(octant_progress_items, className="px-2")
                    ], style={'maxHeight': '350px', 'overflowY': 'auto'}),
                    
                    # 汇总统计
                    html.Hr(className="my-3"),
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Span("🌟 优质商品", className="d-block text-muted", style={'fontSize': '12px'}),
                                html.Span(f"{octant_counts.get('🌟 明星商品', 0) + octant_counts.get('💰 现金牛', 0)}个", 
                                         className="badge bg-success", style={'fontSize': '14px'})
                            ], className="text-center")
                        ], width=4),
                        dbc.Col([
                            html.Div([
                                html.Span("⚠️ 需关注", className="d-block text-muted", style={'fontSize': '12px'}),
                                html.Span(f"{octant_counts.get('📉 待观察', 0) + octant_counts.get('⚠️ 高成本引流', 0)}个", 
                                         className="badge bg-warning", style={'fontSize': '14px'})
                            ], className="text-center")
                        ], width=4),
                        dbc.Col([
                            html.Div([
                                html.Span("🚨 需处理", className="d-block text-muted", style={'fontSize': '12px'}),
                                html.Span(f"{octant_counts.get('🐌 滞销品', 0) + octant_counts.get('🚨 问题商品', 0)}个", 
                                         className="badge bg-danger", style={'fontSize': '14px'})
                            ], className="text-center")
                        ], width=4),
                    ])
                ], className="pt-3")
            ], label="🎯 象限分布", tab_id="tab-octant"),
        ], id="product-health-tabs", active_tab="tab-score", className="mb-3"),
    ])


def create_product_scoring_section(df: pd.DataFrame) -> html.Div:
    """
    创建商品健康分析区域 V5.0
    
    优化内容：
    1. 品类筛选联动：选品类后评分概览+象限分布都更新
    2. 品类选中标记：选中的品类按钮有明显标记
    3. Tab切换：评分概览 / 象限分布
    4. 进度条列表替代饼图
    """
    if df is None or df.empty:
        return html.Div()
    
    # 计算商品评分
    product_scores = calculate_enhanced_product_scores(df)
    
    if product_scores.empty:
        return dbc.Alert("暂无商品数据", color="warning")
    
    # 获取品类列表用于筛选按钮
    category_col = '一级分类名' if '一级分类名' in product_scores.columns else None
    category_buttons = []
    
    if category_col:
        category_stats = product_scores.groupby(category_col).agg({
            '综合得分': 'mean',
            '商品名称': 'count'
        }).reset_index()
        category_stats.columns = [category_col, '平均分', '商品数']
        category_stats = category_stats.sort_values('平均分', ascending=False)
        
        total_categories = len(category_stats)
        for idx, (_, row) in enumerate(category_stats.iterrows()):
            cat_name = row[category_col]
            cat_score = row['平均分']
            cat_count = row['商品数']
            
            # 按排名百分位选择颜色
            rank_pct = idx / total_categories if total_categories > 0 else 0
            
            if rank_pct <= 0.1:
                btn_color = 'success'
                score_badge_class = 'bg-success text-white'
            elif rank_pct <= 0.3:
                btn_color = 'info'
                score_badge_class = 'bg-info text-white'
            elif rank_pct <= 0.5:
                btn_color = 'primary'
                score_badge_class = 'bg-primary text-white'
            elif rank_pct <= 0.7:
                btn_color = 'secondary'
                score_badge_class = 'bg-secondary text-white'
            elif rank_pct <= 0.9:
                btn_color = 'warning'
                score_badge_class = 'bg-warning text-dark'
            else:
                btn_color = 'danger'
                score_badge_class = 'bg-danger text-white'
            
            category_buttons.append(
                dbc.Button([
                    html.Span(f"{cat_name}", className="me-1 fw-bold"),
                    html.Span(f"{cat_score:.0f}分", className=f"badge {score_badge_class} me-1", style={'fontSize': '11px', 'fontWeight': 'bold'}),
                    html.Span(f"({cat_count})", style={'fontSize': '11px', 'opacity': '0.8'})
                ],
                id={'type': 'category-filter-btn', 'index': cat_name},
                color=btn_color,
                outline=True,  # 默认outline，选中时改为实心
                size="sm",
                className="me-1 mb-1",
                style={'fontSize': '12px', 'fontWeight': '600'}
                )
            )
    
    # ===== 构建布局 =====
    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H5([
                        html.I(className="bi bi-graph-up me-2"),
                        "📊 商品健康分析"
                    ], className="mb-0 text-primary"),
                ], width=8),
                dbc.Col([
                    dbc.Button([
                        html.I(className="bi bi-download me-1"),
                        "导出报告"
                    ], id='btn-export-product-scoring', color="primary", size="sm", outline=True)
                ], width=4, className="text-end")
            ], align="center")
        ], className="bg-white border-bottom"),
        
        dbc.CardBody([
            # ===== 品类快捷筛选按钮（放在最上面）=====
            html.Div([
                html.Div([
                    html.Span("🏷️ 按品类筛选：", className="text-secondary me-2 fw-bold", style={'fontSize': '13px'}),
                    dbc.Button([
                        html.I(className="bi bi-grid-3x3-gap me-1"),
                        "全部商品"
                    ], id={'type': 'category-filter-btn', 'index': '__all__'}, 
                              color="dark", size="sm", className="me-1 mb-1"),  # 默认选中全部
                    *category_buttons
                ], className="d-flex flex-wrap align-items-center"),
                # 当前筛选提示
                html.Div([
                    html.Small("当前: ", className="text-muted"),
                    html.Span(id='current-category-filter-label', children="全部商品", 
                             className="badge bg-primary", style={'fontSize': '12px'})
                ], className="mt-2")
            ], className="mb-3 p-2 bg-light rounded") if category_buttons else html.Div(),
            
            # ===== 动态内容容器（评分概览Tab + 象限分布Tab）=====
            html.Div(
                id='product-health-content-container',
                children=create_product_health_content(product_scores, None, None)
            ),
            
            html.Hr(className="my-3"),
            
            # ===== 数据表格（默认折叠）=====
            html.Div([
                dbc.Button([
                    html.I(className="bi bi-table me-2"),
                    "📋 查看商品详细数据"
                ], id='btn-toggle-scoring-detail', color="outline-secondary", size="sm", className="me-2"),
                html.Span(id='scoring-table-filter-label', className="badge bg-info", children="全部商品"),
                dbc.Button("清除筛选", id='btn-clear-scoring-filter', color="link", size="sm", className="ms-2"),
            ], className="mb-2"),
            
            # 数据表格容器（折叠）
            dbc.Collapse([
                html.Div(
                    id='scoring-table-container',
                    children=create_product_scoring_table_v4(product_scores)
                )
            ], id='collapse-scoring-detail', is_open=False)
        ])
    ], className="mb-4 shadow-sm border-0")


# ===== 以下函数已废弃（V5.0改用Tab+进度条列表）=====
# def create_octant_section(octant_pie_option, octant_buttons, octant_counts):
#     """创建八象限分布区域（初始静态版本）- 已废弃"""
#     pass

# def create_octant_section_dynamic(product_scores, category_filter=None):
#     """动态创建八象限分布区域 - 已废弃"""
#     pass


# ===== 以下为真正的表格函数 =====


def create_product_scoring_table_v4(product_scores: pd.DataFrame, filter_type: str = None, filter_value: str = None) -> html.Div:
    """
    创建商品评分详细数据表 V5.0
    
    优化内容：
    1. 补充字段：店内码、三级分类、商品原价、实收价格、单品成本、定价利润率
    2. 字段命名统一：毛利率→利润率
    3. 字体调大到13px
    4. 颜色柔和（浅绿、浅橙替代刺眼红绿）
    5. 支持按象限/品类/评分等级筛选
    """
    if product_scores.empty:
        return html.Div("暂无数据", className="text-center text-muted p-4")
    
    # 应用筛选
    filtered_df = product_scores.copy()
    if filter_type == 'octant' and filter_value:
        filtered_df = filtered_df[filtered_df['八象限分类'] == filter_value]
    elif filter_type == 'category' and filter_value and filter_value != '__all__':
        category_col = '一级分类名' if '一级分类名' in filtered_df.columns else None
        if category_col:
            filtered_df = filtered_df[filtered_df[category_col] == filter_value]
    elif filter_type == 'score_level' and filter_value:
        # 按评分等级筛选
        filtered_df = filtered_df[filtered_df['评分等级'] == filter_value]
    
    if filtered_df.empty:
        return html.Div("筛选结果为空", className="text-center text-muted p-4")
    
    # 选择显示的列（完整字段列表）
    display_cols = [
        '排名', '店内码', '商品名称', '一级分类名', '三级分类名',
        '商品原价', '实收价格', '单品成本', '综合利润率', '定价利润率',
        '销量', '销售额', '综合得分', '评分等级', '八象限分类', 
        '问题标签', '业务建议', '售罄率', '营销占比', '库存周转天数'
    ]
    
    available_cols = [c for c in display_cols if c in filtered_df.columns]
    display_df = filtered_df[available_cols].copy()
    
    # 格式化数值
    for col in ['综合利润率', '定价利润率', '售罄率', '营销占比']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    
    if '综合得分' in display_df.columns:
        display_df['综合得分'] = display_df['综合得分'].apply(lambda x: f"{x:.1f}")
    
    if '库存周转天数' in display_df.columns:
        display_df['库存周转天数'] = display_df['库存周转天数'].apply(lambda x: f"{x:.0f}天" if pd.notna(x) and x < 999 else "-")
    
    # 价格和成本字段格式化
    for col in ['商品原价', '实收价格', '单品成本']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"¥{x:.2f}" if pd.notna(x) and x > 0 else "-")
    
    if '销售额' in display_df.columns:
        display_df['销售额'] = display_df['销售额'].apply(lambda x: f"¥{x:,.0f}")
    
    if '销量' in display_df.columns:
        display_df['销量'] = display_df['销量'].apply(lambda x: f"{int(x)}")
    
    return html.Div([
        html.Div([
            html.Span(f"共 {len(display_df)} 个商品", className="text-muted", style={'fontSize': '13px'}),
        ], className="mb-2"),
        dash_table.DataTable(
            id='scoring-detail-table',
            data=display_df.to_dict('records'),
            columns=[{'name': c, 'id': c} for c in available_cols],
            style_table={'overflowX': 'auto', 'borderRadius': '8px'},
            # 字体调大到13px，优化单元格样式
            style_cell={
                'textAlign': 'left', 
                'padding': '10px 8px', 
                'fontSize': '12px',
                'fontFamily': 'Microsoft YaHei, sans-serif',
                'whiteSpace': 'normal',
                'height': 'auto',
                'minWidth': '50px',
                'maxWidth': '180px',
            },
            style_header={
                'backgroundColor': '#f0f5ff', 
                'fontWeight': 'bold',
                'fontSize': '12px',
                'borderBottom': '2px solid #d9d9d9',
                'color': '#262626',
                'textAlign': 'center',
            },
            # 简洁样式：用文字颜色标记重要列，无边框
            style_data_conditional=[
                # 八象限分类列 - 根据类型显示不同颜色
                {'if': {'filter_query': '{八象限分类} contains "明星商品"', 'column_id': '八象限分类'}, 
                 'color': '#52c41a', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{八象限分类} contains "现金牛"', 'column_id': '八象限分类'}, 
                 'color': '#52c41a', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{八象限分类} contains "潜力商品"', 'column_id': '八象限分类'}, 
                 'color': '#722ed1', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{八象限分类} contains "引流商品"', 'column_id': '八象限分类'}, 
                 'color': '#1890ff', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{八象限分类} contains "待观察"', 'column_id': '八象限分类'}, 
                 'color': '#faad14', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{八象限分类} contains "高成本引流"', 'column_id': '八象限分类'}, 
                 'color': '#fa8c16', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{八象限分类} contains "滞销品"', 'column_id': '八象限分类'}, 
                 'color': '#8c8c8c', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{八象限分类} contains "问题商品"', 'column_id': '八象限分类'}, 
                 'color': '#ff4d4f', 'fontWeight': 'bold'},
                # 问题标签列 - 有问题的红色警示
                {'if': {'filter_query': '{问题标签} contains "低毛利"', 'column_id': '问题标签'}, 
                 'color': '#fa8c16'},
                {'if': {'filter_query': '{问题标签} contains "高营销"', 'column_id': '问题标签'}, 
                 'color': '#ff4d4f'},
                {'if': {'filter_query': '{问题标签} contains "低动销"', 'column_id': '问题标签'}, 
                 'color': '#8c8c8c'},
                # 评分等级列颜色
                {'if': {'filter_query': '{评分等级} contains "优秀"', 'column_id': '评分等级'}, 
                 'color': '#52c41a'},
                {'if': {'filter_query': '{评分等级} contains "良好"', 'column_id': '评分等级'}, 
                 'color': '#1890ff'},
                {'if': {'filter_query': '{评分等级} contains "一般"', 'column_id': '评分等级'}, 
                 'color': '#faad14'},
                {'if': {'filter_query': '{评分等级} contains "待优化"', 'column_id': '评分等级'}, 
                 'color': '#ff4d4f'},
                # 斑马纹
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#fafafa'},
            ],
            page_size=15,
            page_action='native',
            sort_action='native',
            # 移除原生筛选，避免英文显示
            filter_action='none',
            # 添加固定列宽
            style_cell_conditional=[
                {'if': {'column_id': '排名'}, 'width': '50px', 'textAlign': 'center'},
                {'if': {'column_id': '商品名称'}, 'width': '180px'},
                {'if': {'column_id': '一级分类名'}, 'width': '80px'},
                {'if': {'column_id': '综合得分'}, 'width': '70px', 'textAlign': 'center'},
                {'if': {'column_id': '评分等级'}, 'width': '70px', 'textAlign': 'center'},
                {'if': {'column_id': '八象限分类'}, 'width': '100px'},
                {'if': {'column_id': '问题标签'}, 'width': '90px'},
                {'if': {'column_id': '业务建议'}, 'width': '140px'},
                {'if': {'column_id': '综合利润率'}, 'width': '70px', 'textAlign': 'right'},
                {'if': {'column_id': '售罄率'}, 'width': '65px', 'textAlign': 'right'},
                {'if': {'column_id': '营销占比'}, 'width': '70px', 'textAlign': 'right'},
                {'if': {'column_id': '库存周转天数'}, 'width': '80px', 'textAlign': 'center'},
                {'if': {'column_id': '销量'}, 'width': '60px', 'textAlign': 'right'},
                {'if': {'column_id': '销售额'}, 'width': '80px', 'textAlign': 'right'},
            ],
        )
    ], className="mt-2")


def get_product_scoring_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取商品评分导出数据（V3.0含八象限）"""
    product_scores = calculate_enhanced_product_scores(df)
    
    if product_scores.empty:
        return pd.DataFrame()
    
    # 选择导出列（V3.0新增八象限和问题标签）
    export_cols = ['排名', '商品名称', '综合得分', '评分等级', '八象限分类', '问题标签', '业务建议',
                   '毛利维度', '动销维度', '营销维度',
                   '毛利率', '售罄率', '营销占比', '库存周转天数',
                   '销量', '销售额', '利润额', '营销成本', '订单数',
                   '盈利能力分', '动销健康分', '营销效率分', '库存压力分']
    
    if '一级分类名' in product_scores.columns:
        export_cols.insert(2, '一级分类名')
    if '店内码' in product_scores.columns:
        export_cols.insert(2, '店内码')
    if '库存' in product_scores.columns:
        export_cols.append('库存')
    
    available_cols = [c for c in export_cols if c in product_scores.columns]
    return product_scores[available_cols]
