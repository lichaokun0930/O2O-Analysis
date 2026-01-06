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

from dash import html, dcc, Input, Output, State, callback_context, no_update, ALL, callback, clientside_callback
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import dash_table
try:
    import dash_ag_grid as dag
    AG_GRID_AVAILABLE = True
except ImportError:
    AG_GRID_AVAILABLE = False
    dag = None
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import sys
import os
import json  # V5.1: 用于ECharts图表生成
import time  # 用于防抖处理
import gc  # 用于内存管理

# ECharts 导入
try:
    from dash_echarts import DashECharts
    ECHARTS_AVAILABLE = True
except ImportError:
    ECHARTS_AVAILABLE = False
    DashECharts = None

# 导入V2.0分析模块
from components.today_must_do.product_analysis import (
    analyze_product_fluctuation,
    analyze_slow_moving_products,
    get_product_insight,
    get_product_insight_enhanced,  # V2.0 增强版单品洞察
    get_declining_products,
    identify_slow_moving_products,
    analyze_top_profit_products,
    analyze_traffic_drop_products,
    analyze_new_slow_moving_products,
    analyze_potential_new_products
)
from components.today_must_do.delivery_analysis import (
    analyze_delivery_issues,
    create_delivery_heatmap_data,
    get_delivery_summary_by_distance,
    identify_delivery_issues
)
from components.today_must_do.marketing_analysis import (
    analyze_marketing_loss,
    analyze_activity_overlap,
    create_marketing_delivery_matrix,
    get_discount_analysis_by_range,
    identify_discount_overflow_orders
)

# V8.0 企业级性能优化：骨架屏组件
from components.today_must_do.skeleton_screens import (
    create_today_must_do_skeleton,
    create_diagnosis_card_skeleton,
    create_product_health_skeleton,
    create_loading_spinner,
    SKELETON_CSS
)

# V8.8 前端体验优化：防抖工具
from components.today_must_do.debounce_utils import (
    debounce,
    throttle
)

# V8.8 前端体验优化：增强的加载和错误组件
from components.today_must_do.loading_components import (
    create_enhanced_loading_spinner,
    create_error_alert,
    create_timeout_alert,
    create_no_data_alert,
    LOADING_ANIMATION_CSS
)

# V8.9 数据分页优化：分页工具
from components.today_must_do.pagination_utils import (
    get_pagination_config,
    create_paginated_datatable,
    create_backend_paginated_table,
    get_page_data
)

# 导入V3.0诊断分析模块
from components.today_must_do.diagnosis_analysis import (
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
# 客户流失分析和客单价异常分析使用延迟导入，避免循环依赖
print("🔧 [DEBUG] 准备导入 customer_churn_analyzer 和 aov_anomaly_analyzer")

# 尝试导入客户流失分析模块
try:
    print("  ↳ 导入 customer_churn_analyzer...")
    from components.today_must_do.customer_churn_analyzer import (
        get_customer_churn_warning,
        get_recommended_actions
    )
    print("  ✅ customer_churn_analyzer 导入成功")
except Exception as e:
    print(f"  ❌ customer_churn_analyzer 导入失败: {e}")
    # 定义占位函数
    def get_customer_churn_warning(*args, **kwargs):
        return {'summary': {'total_churn': 0}, 'customers': []}
    def get_recommended_actions(*args, **kwargs):
        return []

# 尝试导入客单价异常分析模块  
try:
    print("  ↳ 导入 aov_anomaly_analyzer...")
    from components.today_must_do.aov_anomaly_analyzer import (
        analyze_customer_downgrade,
        analyze_category_contribution,
        analyze_channel_comparison,
        analyze_product_drag
    )
    print("  ✅ aov_anomaly_analyzer 导入成功")
except Exception as e:
    print(f"  ❌ aov_anomaly_analyzer 导入失败: {e}")
    import traceback
    traceback.print_exc()
    # 定义占位函数
    def analyze_category_contribution(*args, **kwargs):
        return {'category_changes': [], 'top_decline': [], 'top_growth': [], 'summary': {}}
    def analyze_channel_comparison(*args, **kwargs):
        return {'channel_stats': [], 'abnormal_channels': [], 'summary': {}}
    def analyze_customer_downgrade(*args, **kwargs):
        return {'summary': {'total_downgrade': 0}}
    def analyze_product_drag(*args, **kwargs):
        return {'summary': {'total_drag_products': 0}}

print("🔧 [DEBUG] 模块导入阶段完成\n")

# 🎨 导入美化UI组件
try:
    import dash_mantine_components as dmc
    from dash_iconify import DashIconify
    MANTINE_AVAILABLE = True
    print("✅ [UI] Dash Mantine Components 已加载")
except ImportError:
    MANTINE_AVAILABLE = False
    print("⚠️ [UI] Dash Mantine Components 未安装，使用默认样式")


# ==================== 时段下钻分析（简化版）====================
def get_hourly_trend_data(order_agg, date=None):
    """
    获取指定日期的小时维度客单价数据
    
    Args:
        order_agg: 订单聚合数据（需要包含'日期'和'下单时间'字段）
        date: 指定日期（格式：'2025-11-23'）
        
    Returns:
        dict: {
            'hours': [...],      # 小时列表
            'aov_values': [...], # 客单价
            'order_counts': [...] # 订单数
        }
    """
    try:
        if order_agg is None or order_agg.empty:
            return {'error': '订单数据为空'}
        
        # 如果没有日期字段，返回错误
        if '日期' not in order_agg.columns:
            return {'error': '订单数据缺少日期字段'}
        
        # 确保日期格式
        order_agg['日期'] = pd.to_datetime(order_agg['日期'], errors='coerce')
        
        if date:
            target_date = pd.to_datetime(date)
        else:
            target_date = order_agg['日期'].max()
        
        # 筛选当日数据（需要copy因为后续会添加'小时'列）
        date_mask = order_agg['日期'].dt.date == target_date.date()
        daily_orders = order_agg[date_mask].copy()  # 必须copy因为要添加新列
        
        if daily_orders.empty:
            return {'error': f'日期 {date} 无数据'}
        
        # 提取小时信息（修改数据，所以上面的copy是必要的）
        if '下单时间' in daily_orders.columns:
            daily_orders['小时'] = pd.to_datetime(daily_orders['下单时间'], errors='coerce').dt.hour
        elif '日期' in daily_orders.columns:
            daily_orders['小时'] = pd.to_datetime(daily_orders['日期'], errors='coerce').dt.hour
        else:
            return {'error': '缺少时间字段'}
        
        # 按小时聚合
        hourly_stats = daily_orders.groupby('小时').agg({
            '实收价格': ['sum', 'count']
        }).reset_index()
        hourly_stats.columns = ['小时', '总销售额', '订单数']
        hourly_stats['客单价'] = hourly_stats['总销售额'] / hourly_stats['订单数']
        
        # 填充0-23小时
        all_hours = pd.DataFrame({'小时': range(24)})
        hourly_stats = all_hours.merge(hourly_stats, on='小时', how='left').fillna(0)
        
        return {
            'hours': [f"{h:02d}:00" for h in hourly_stats['小时'].tolist()],
            'aov_values': hourly_stats['客单价'].round(2).tolist(),
            'order_counts': hourly_stats['订单数'].astype(int).tolist()
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'error': f'小时分析失败: {str(e)}'}


# ==================== 内存优化工具函数 ====================
def apply_filters_view(df, selected_stores=None, selected_channel=None):
    """
    应用筛选条件，返回视图而非复制（内存优化）
    
    Args:
        df: 原始DataFrame
        selected_stores: 门店筛选（可以是字符串、列表或None）
        selected_channel: 渠道筛选（可以是字符串、列表或None）
        
    Returns:
        DataFrame视图（不复制数据）
    """
    view = df
    
    # V6.1：标准化selected_stores为列表
    if selected_stores:
        if isinstance(selected_stores, str):
            if selected_stores == 'ALL':
                selected_stores = []
            else:
                selected_stores = [selected_stores]
        # 过滤空值
        selected_stores = [s for s in selected_stores if s]
    else:
        selected_stores = []
    
    # V6.1：标准化selected_channel为列表
    if selected_channel:
        if isinstance(selected_channel, str):
            if selected_channel == 'ALL':
                selected_channel = []
            else:
                selected_channel = [selected_channel]
        # 过滤空值
        selected_channel = [c for c in selected_channel if c]
    else:
        selected_channel = []
    
    # 门店筛选（兼容多种列名）
    if selected_stores and len(selected_stores) > 0:
        store_col = None
        for col in ['门店名称', '门店', 'store']:
            if col in view.columns:
                store_col = col
                break
        if store_col:
            view = view[view[store_col].isin(selected_stores)]
    
    # 渠道筛选（兼容多种列名）
    if selected_channel and len(selected_channel) > 0:
        channel_col = None
        for col in ['渠道', '平台', 'channel']:
            if col in view.columns:
                channel_col = col
                break
        if channel_col:
            view = view[view[channel_col].isin(selected_channel)]
    
    return view


def safe_copy_if_needed(df, need_modify=False, columns=None):
    """
    仅在必要时复制DataFrame（内存优化）
    
    Args:
        df: 原始DataFrame
        need_modify: 是否需要修改数据（True时才复制）
        columns: 需要的列（传入时仅选择需要的列，减少内存）
        
    Returns:
        DataFrame（视图或复制）
    """
    # 选择需要的列
    if columns:
        df = df[columns]
    
    # 仅在需要修改时复制
    if need_modify:
        return df.copy()
    else:
        return df


def cleanup_memory(obj=None):
    """
    清理内存并触发垃圾回收
    
    Args:
        obj: 需要删除的对象（可选）
    """
    if obj is not None:
        del obj
    gc.collect()


# 缓存装饰器（用于缓存计算结果）
from functools import lru_cache

def cache_by_data_hash(func):
    """
    基于数据内容哈希的缓存装饰器
    用于缓存DataFrame相关计算结果
    """
    cache = {}
    
    def wrapper(df, *args, **kwargs):
        # 生成数据哈希key
        data_hash = hash((id(df), len(df), tuple(df.columns)))
        cache_key = (data_hash, args, tuple(sorted(kwargs.items())))
        
        if cache_key in cache:
            return cache[cache_key]
        
        result = func(df, *args, **kwargs)
        cache[cache_key] = result
        
        # 限制缓存大小
        if len(cache) > 100:
            cache.clear()
        
        return result
    
    return wrapper


# ==================== 全局防抖变量 ====================
_last_click_time = {'time': 0, 'cell': ''}  # 用于防止快速重复点击


# ==================== 辅助函数：获取全局数据 ====================
def get_real_global_data():
    """获取真实的全局数据(GLOBAL_DATA)，受顶部日期筛选影响"""
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


def get_real_global_full_data():
    """获取全量数据(GLOBAL_FULL_DATA)，不受顶部日期筛选影响"""
    if '__main__' in sys.modules:
        main_module = sys.modules['__main__']
        if hasattr(main_module, 'GLOBAL_FULL_DATA'):
            return main_module.GLOBAL_FULL_DATA
            
    try:
        from 智能门店看板_Dash版 import GLOBAL_FULL_DATA
        return GLOBAL_FULL_DATA
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
    button_text: str = "查看详情",
    trend_info: dict = None  # 新增：趋势信息 {'icon': '↑', 'label': '恶化', 'color': 'red', 'description': '...'}
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
        trend_info: 趋势信息字典 {'icon': '↑', 'label': '恶化', 'color': 'red', 'description': '较3日均(5)↑100%'}
    """
    if not MANTINE_AVAILABLE:
        # 回退到基础样式
        bs_color = {'red': 'danger', 'orange': 'warning', 'green': 'success', 
                    'blue': 'info', 'indigo': 'primary', 'violet': 'secondary'}.get(color, color)
        trend_text = ""
        if trend_info and trend_info.get('description'):
            trend_text = f" | 📈 {trend_info.get('description', '')}"
        return html.Div([
            html.Div(f"{title}", className=f"fw-bold text-{bs_color} mb-2"),
            html.Div([main_value, " ", main_label]),
            html.Div(f"{sub_info or ''}{trend_text}", className="small text-muted") if sub_info or trend_text else None,
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
    
    # 🆕 趋势标签 - 显示在主数值下方
    if trend_info and trend_info.get('description'):
        trend_color_map = {'red': 'red', 'green': 'green', 'gray': 'dimmed', 'orange': 'orange'}
        trend_mantine_color = trend_color_map.get(trend_info.get('color', 'gray'), 'dimmed')
        trend_icon_map = {'up': 'tabler:trending-up', 'down': 'tabler:trending-down', 'stable': 'tabler:minus'}
        trend_icon_name = trend_icon_map.get(trend_info.get('trend', 'stable'), 'tabler:minus')
        
        children.append(
            dmc.Group([
                DashIconify(icon=trend_icon_name, width=16, color=f"var(--mantine-color-{trend_mantine_color}-6)" if trend_mantine_color != 'dimmed' else '#868e96'),
                dmc.Text(
                    f"{trend_info.get('icon', '')} {trend_info.get('label', '')}：{trend_info.get('description', '')}",
                    size="xs",
                    c=trend_mantine_color,
                    fw=600,
                    style={"fontSize": "12px"}
                )
            ], gap=4, mt=6)
        )
    
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
    
    # V8.10.3: 注册性能监控面板回调（TOP 5展示）
    try:
        from components.performance_panel import register_performance_panel_callbacks
        register_performance_panel_callbacks(app, panel_id='today-must-do-performance-panel', top_n=5)
        print("✅ 性能监控面板回调已注册（TOP 5模式）")
    except Exception as e:
        print(f"⚠️ 性能监控面板回调注册失败: {e}")
    
    @app.callback(
        Output('today-must-do-content', 'children'),
        [Input('main-tabs', 'value'),
         Input('data-update-trigger', 'data')],
        [State('db-store-filter', 'value')],
        prevent_initial_call=False  # 允许首次加载
    )
    @debounce(wait_ms=300)  # V8.8: 添加300ms防抖，避免快速切换Tab时的重复请求
    def update_today_must_do_content(active_tab, data_trigger, selected_stores):
        """主内容渲染回调 - 响应TAB切换和数据更新"""
        ctx = callback_context
        print(f"\n{'='*80}")
        print(f"[DEBUG] 今日必做主回调被调用!")
        print(f"  - active_tab: {active_tab}")
        print(f"  - data_trigger: {data_trigger}")
        print(f"  - triggered_id: {ctx.triggered_id}")
        print(f"  - triggered: {ctx.triggered}")
        print(f"  - selected_stores: {selected_stores}")
        
        # 如果active_tab为None或不是今日必做Tab，返回空内容
        if not active_tab or active_tab != 'tab-today-must-do':
            print(f"[DEBUG] 非今日必做Tab, 返回空内容. active_tab={active_tab}")
            print(f"{'='*80}\n")
            return html.Div()  # 返回空div而不是PreventUpdate
        
        print(f"[DEBUG] 开始获取 GLOBAL_DATA...")
        GLOBAL_DATA = get_real_global_data()
        
        print(f"[DEBUG] get_real_global_data() 返回类型: {type(GLOBAL_DATA)}")
        print(f"[DEBUG] GLOBAL_DATA is None: {GLOBAL_DATA is None}")
        
        if GLOBAL_DATA is None:
            print("[ERROR] GLOBAL_DATA 为 None!")
            print(f"[DEBUG] 尝试检查主模块...")
            if '__main__' in sys.modules:
                main_module = sys.modules['__main__']
                print(f"[DEBUG] 主模块存在: {main_module}")
                print(f"[DEBUG] hasattr get_global_data: {hasattr(main_module, 'get_global_data')}")
                print(f"[DEBUG] hasattr GLOBAL_DATA: {hasattr(main_module, 'GLOBAL_DATA')}")
                if hasattr(main_module, 'GLOBAL_DATA'):
                    gd = getattr(main_module, 'GLOBAL_DATA')
                    print(f"[DEBUG] main_module.GLOBAL_DATA 类型: {type(gd)}")
                    print(f"[DEBUG] main_module.GLOBAL_DATA is None: {gd is None}")
                    if gd is not None:
                        print(f"[DEBUG] main_module.GLOBAL_DATA shape: {gd.shape if hasattr(gd, 'shape') else 'N/A'}")
            print(f"{'='*80}\n")
            return create_no_data_message()
        
        if GLOBAL_DATA.empty:
            print("[ERROR] GLOBAL_DATA 为空 DataFrame!")
            print(f"{'='*80}\n")
            return create_no_data_message()
            
        print(f"[DEBUG] ✅ GLOBAL_DATA shape: {GLOBAL_DATA.shape}")
        print(f"[DEBUG] GLOBAL_DATA columns: {list(GLOBAL_DATA.columns[:10])}...")  # 显示前10个列名
        
        try:
            print(f"[DEBUG] 开始调用 create_today_must_do_layout...")
            layout = create_today_must_do_layout(GLOBAL_DATA, selected_stores)
            print(f"[DEBUG] ✅ create_today_must_do_layout 成功!")
            print(f"{'='*80}\n")
            return layout
        except Exception as e:
            print(f"[ERROR] ❌ create_today_must_do_layout 失败!")
            print(f"  错误信息: {str(e)}")
            import traceback
            traceback.print_exc()
            print(f"{'='*80}\n")
            return create_error_message(f"渲染失败: {str(e)}")

    # V7.5性能优化：异步加载经营诊断卡片
    @app.callback(
        [Output('today-must-do-diagnosis-container', 'children'),
         Output('today-must-do-performance-panel-data', 'data')],  # V8.10.3: 输出性能数据
        Input('today-must-do-content', 'children'),  # 等待主布局渲染完成
        State('db-store-filter', 'value'),
        prevent_initial_call=True
    )
    def load_diagnosis_async(layout_children, selected_stores):
        """
        异步加载经营诊断卡片
        
        V8.1性能优化：
        - 优先从Redis缓存读取（<1秒）
        - 缓存未命中时实时计算（70秒）
        - 后台任务每5分钟更新缓存
        
        V8.10.3性能监控：
        - 返回性能数据供前端显示
        - 监控数据加载耗时
        - 重置监控器以开始新的监控周期
        """
        print(f"\n{'='*80}")
        print(f"[异步加载] 开始加载经营诊断...")
        
        import time
        start_time = time.time()
        
        try:
            # V8.10.3: 获取性能监控器并重置（开始新的监控周期）
            from components.today_must_do.performance_monitor import get_global_monitor
            monitor = get_global_monitor()
            monitor.reset()  # 重置监控器，清除之前的数据
            print("[DEBUG] 性能监控器已重置")
            
            # V8.3: 智能缓存 - 基于门店筛选
            from redis_cache_manager import REDIS_CACHE_MANAGER
            
            # 缓存未命中，实时计算
            print(f"[异步加载] ⚠️ 缓存未命中，开始实时计算...")
            
            # V8.10.3: 监控数据获取
            with monitor.measure('0.数据获取', print_result=True):
                GLOBAL_DATA = get_real_global_data()
            
            if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                print("[异步加载] GLOBAL_DATA为空，返回提示")
                return dbc.Alert("暂无数据", color="warning", className="mb-4"), None
            
            # V8.10.3: 监控数据筛选
            with monitor.measure('0.数据筛选', print_result=True):
                # 应用门店筛选
                filtered_df = GLOBAL_DATA
                if selected_stores and len(selected_stores) > 0:
                    if isinstance(selected_stores, str):
                        selected_stores = [selected_stores]
                    if '门店名称' in filtered_df.columns:
                        filtered_df = filtered_df[filtered_df['门店名称'].isin(selected_stores)]
            
            print(f"[异步加载] 筛选后数据行数: {len(filtered_df)}")
            
            # V8.10.3: 获取诊断结果（包含性能数据）
            from components.today_must_do.diagnosis_analysis import get_diagnosis_summary
            diagnosis = get_diagnosis_summary(filtered_df)
            
            # 提取性能数据（合并数据加载的性能）
            performance_data = diagnosis.get('performance', None)
            
            # V8.10.3: 监控卡片创建
            with monitor.measure('6.卡片创建', print_result=True):
                result = create_business_diagnosis_card(filtered_df)
            load_time = time.time() - start_time
            
            print(f"[异步加载] ✅ 经营诊断加载完成，耗时: {load_time:.2f}秒")
            print(f"{'='*80}\n")
            
            # V8.10.3: 获取完整的性能报告（包含数据加载）
            performance_data = monitor.get_report()
            
            return result, performance_data
            
        except Exception as e:
            print(f"[异步加载] ❌ 加载失败: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*80}\n")
            
            return dbc.Alert([
                html.H5("加载失败", className="alert-heading"),
                html.P(f"错误信息: {str(e)}")
            ], color="danger", className="mb-4"), None

    # V7.5性能优化：异步加载商品健康分析（在诊断卡片加载完成后）
    @app.callback(
        [Output('product-scoring-section-container', 'children', allow_duplicate=True),
         Output('today-must-do-performance-panel-data', 'data', allow_duplicate=True)],  # V8.10.3: 更新性能数据
        Input('today-must-do-diagnosis-container', 'children'),  # 等待诊断卡片加载完成
        [State('db-store-filter', 'value'),
         State('today-must-do-performance-panel-data', 'data')],  # V8.10.3: 获取之前的性能数据
        prevent_initial_call=True
    )
    def load_product_scoring_async(diagnosis_content, selected_stores, previous_performance_data):
        """
        异步加载商品健康分析
        
        V8.6.3性能优化：
        - 在主布局渲染完成后才开始加载
        - 显示详细的加载进度
        - 优先使用Redis缓存
        - 用户可以先看到诊断卡片和调价计算器
        
        V8.10.3性能监控：
        - 添加商品健康分析的性能监控
        - 累积之前的性能数据（不覆盖）
        - 更新性能面板数据
        """
        print(f"\n{'='*80}")
        print(f"[V8.6.3异步加载] 开始加载商品健康分析...")
        print(f"[DEBUG] 之前的性能数据: {previous_performance_data is not None}")
        
        import time
        total_start = time.time()
        
        try:
            # V8.10.3: 获取性能监控器（继续使用同一个实例，不重置）
            from components.today_must_do.performance_monitor import get_global_monitor
            monitor = get_global_monitor()
            
            GLOBAL_DATA = get_real_global_data()
            
            if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                print("[异步加载] GLOBAL_DATA为空，返回提示")
                # 返回之前的性能数据，不覆盖
                return dbc.Alert("暂无数据", color="warning", className="mb-4"), previous_performance_data
            
            # 应用门店筛选
            filtered_df = GLOBAL_DATA
            if selected_stores and len(selected_stores) > 0:
                if isinstance(selected_stores, str):
                    selected_stores = [selected_stores]
                if '门店名称' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['门店名称'].isin(selected_stores)]
            
            print(f"[异步加载] 筛选后数据: {len(filtered_df)}行")
            
            # V8.6.3: 显示数据规模和预估时间
            estimated_time = len(filtered_df) / 1000  # 粗略估算：每1000行约1秒
            if estimated_time > 30:
                print(f"⚠️ [异步加载] 数据量较大，预计需要 {estimated_time:.0f}秒")
            
            # V8.10.3: 监控商品健康分析
            with monitor.measure('5.商品健康分析', print_result=True):
                result = create_product_scoring_section(filtered_df)
            
            total_time = time.time() - total_start
            print(f"[异步加载] ✅ 商品健康分析加载完成")
            print(f"   总耗时: {total_time:.2f}秒")
            print(f"   数据行数: {len(filtered_df)}")
            print(f"   性能: {len(filtered_df)/total_time:.0f} 行/秒")
            print(f"{'='*80}\n")
            
            # V8.10.3: 获取累积的性能报告（包含之前的"0.数据获取"等）
            performance_data = monitor.get_report()
            print(f"[DEBUG] 累积的性能数据包含 {len(performance_data.get('measurements', {}))} 个模块")
            
            return result, performance_data
            
        except Exception as e:
            print(f"[异步加载] ❌ 加载失败: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*80}\n")
            
            # 返回之前的性能数据，不覆盖
            return dbc.Alert([
                html.H5("加载失败", className="alert-heading"),
                html.P(f"错误信息: {str(e)}")
            ], color="danger", className="mb-4"), previous_performance_data

    @app.callback(
        [Output("product-detail-modal", "is_open"),
         Output("product-detail-modal-body", "children"),
         Output("product-detail-modal-header", "children")],
        [Input({'type': 'product-analysis-table', 'index': ALL}, "active_cell"),
         Input("product-detail-modal-close", "n_clicks")],
        [State({'type': 'product-analysis-table', 'index': ALL}, "derived_viewport_data"),
         State("product-detail-modal", "is_open")],
        prevent_initial_call=True
    )
    def toggle_product_detail_modal(active_cells, n_close, viewport_datas, is_open):
        """
        处理商品详情弹窗
        
        🔧 修复逻辑：
        1. 只有点击「商品名称」列才触发弹窗
        2. 过滤首次渲染触发
        3. 支持重复点击同一商品
        """
        global _last_click_time  # 声明使用全局变量
        
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update
        
        trigger_prop_id = ctx.triggered[0]['prop_id']
        trigger_value = ctx.triggered[0]['value']
        
        # 🔧 关闭按钮点击
        if 'product-detail-modal-close' in trigger_prop_id:
            return False, no_update, no_update
        
        # 🔧 如果trigger_value是None或空字典，说明不是真正的点击
        if not trigger_value:
            return no_update, no_update, no_update
            
        # Check if it's one of our tables
        if 'product-analysis-table' in trigger_prop_id:
            # Find the active cell that is not None
            active_cell = None
            viewport_data = None
            table_idx = None
            
            for i, (ac, vd) in enumerate(zip(active_cells, viewport_datas)):
                if ac and vd:
                    active_cell = ac
                    viewport_data = vd
                    table_idx = i
                    break
            
            if active_cell and viewport_data:
                # 🔧 修复：只有点击「商品名称」列才触发
                if active_cell.get('column_id') != '商品名称':
                    return no_update, no_update, no_update
                
                row_idx = active_cell['row']
                col_idx = active_cell.get('column', 0)
                
                # 🔧 使用时间戳判断：同一单元格在500ms内不重复触发
                current_time = time.time()
                cell_key = f"{table_idx}_{row_idx}_{col_idx}"
                
                # 首次渲染检测：如果程序刚启动（时间差<2秒）且没有真正点击，跳过
                if _last_click_time['time'] == 0:
                    # 首次调用，记录但不触发
                    _last_click_time = {'time': current_time, 'cell': cell_key}
                    print(f"[DEBUG] 首次渲染，跳过: {cell_key}")
                    return no_update, no_update, no_update
                
                # 正常点击处理
                _last_click_time = {'time': current_time, 'cell': cell_key}
                
                if row_idx < len(viewport_data):
                    product_name = viewport_data[row_idx].get('商品名称')
                    print(f"[DEBUG] Clicked product: {product_name}")
                    
                    if product_name:
                        GLOBAL_DATA = get_real_global_data()
                        if GLOBAL_DATA is None:
                            return True, "数据未加载", "错误"
                            
                        # Generate detail content
                        content = create_product_detail_content(GLOBAL_DATA, product_name)
                        return True, content, dbc.ModalTitle(f"📊 {product_name}")
            
        return no_update, no_update, no_update

    # ==================== 诊断详情弹窗回调 ====================
    @app.callback(
        Output('diagnosis-detail-modal', 'is_open'),
        Output('diagnosis-detail-modal-title', 'children'),
        Output('diagnosis-detail-modal-body', 'children'),
        Output('diagnosis-detail-type-store', 'data'),
        Input('btn-diagnosis-overflow', 'n_clicks'),
        Input('btn-diagnosis-delivery', 'n_clicks'),
        Input('btn-diagnosis-stockout', 'n_clicks'),
        Input('btn-diagnosis-churn', 'n_clicks'),  # 客户流失预警
        Input('btn-diagnosis-aov', 'n_clicks'),  # 🆕 客单价异常诊断
        Input('btn-diagnosis-traffic', 'n_clicks'),
        Input('btn-diagnosis-slow', 'n_clicks'),
        Input('btn-diagnosis-newproduct', 'n_clicks'),
        Input('btn-diagnosis-price-abnormal', 'n_clicks'),
        Input('btn-diagnosis-profit-drop', 'n_clicks'),
        Input('btn-diagnosis-hot-products', 'n_clicks'),
        Input('btn-diagnosis-high-profit', 'n_clicks'),
        Input('btn-diagnosis-price-elasticity', 'n_clicks'),  # 价格弹性分析
        Input('diagnosis-detail-modal-close', 'n_clicks'),
        State('diagnosis-detail-modal', 'is_open'),
        State('db-store-filter', 'value'),
        prevent_initial_call=True
    )
    def toggle_diagnosis_detail_modal(
        n_overflow, n_delivery, n_stockout, n_churn, n_aov, n_traffic, n_slow, n_newproduct, 
        n_price_abnormal, n_profit_drop, n_hot_products, n_high_profit, n_price_elasticity, n_close,
        is_open, selected_stores
    ):
        """处理诊断详情弹窗的打开/关闭"""
        ctx = callback_context
        if not ctx.triggered:
            return is_open, no_update, no_update, no_update
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        trigger_value = ctx.triggered[0]['value']
        
        # V7.5.2 BUG修复：防止异步加载时自动打开弹窗
        # 只有当n_clicks > 0时才打开（排除初始化和异步加载的情况）
        if trigger_id != 'diagnosis-detail-modal-close' and (trigger_value is None or trigger_value == 0):
            print(f"[诊断弹窗] 忽略触发: {trigger_id}, n_clicks={trigger_value}")
            return is_open, no_update, no_update, no_update
        
        # 关闭按钮
        if trigger_id == 'diagnosis-detail-modal-close':
            return False, no_update, no_update, None
        
        # 获取数据
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return True, "数据错误", dbc.Alert("数据未加载", color="warning"), None
        
        # 内存优化：使用视图而非复制
        df = apply_filters_view(
            GLOBAL_DATA,
            selected_stores=selected_stores if selected_stores and len(selected_stores) > 0 else None
        )
        
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
            elif trigger_id == 'btn-diagnosis-churn':
                title = "👥 客户流失预警详情"
                content = create_churn_detail_table(df)
            elif trigger_id == 'btn-diagnosis-aov':
                title = "💰 客单价异常诊断"
                content = create_aov_anomaly_detail(df)
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
        
        # 内存优化：使用视图而非复制
        df = apply_filters_view(
            GLOBAL_DATA,
            selected_stores=selected_stores if selected_stores and len(selected_stores) > 0 else None
        )
        
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
            elif detail_type == 'btn-diagnosis-churn':
                export_df = get_churn_export_data(df)
                filename = "客户流失预警清单.xlsx"
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

    # ==================== 客单价异常诊断回调 ====================
    @app.callback(
        Output('aov-tab-content', 'children'),
        Input('aov-tabs', 'active_tab'),
        Input('aov-period-selector', 'value'),
        Input('aov-channel-filter', 'value'),
        State('db-store-filter', 'value'),
        prevent_initial_call=False
    )
    def update_aov_tab_content(active_tab, period_days, selected_channel, selected_stores):
        """根据Tab、周期和渠道更新客单价异常诊断内容"""
        try:
            GLOBAL_DATA = get_real_global_data()
            if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                return dbc.Alert("数据未加载", color="warning")
            
            # 内存优化：先用视图筛选，再复制筛选后的结果（大幅减少内存占用）
            df_view = apply_filters_view(
                GLOBAL_DATA, 
                selected_stores=selected_stores if selected_stores and len(selected_stores) > 0 else None,
                selected_channel=[selected_channel] if selected_channel and selected_channel != 'all' else None
            )
            # 复制筛选后的数据（通常只是全量的一部分，内存占用小）
            df = df_view.copy()
            print(f"✅ [DEBUG] 渠道筛选: {selected_channel}, 筛选后数据量: {len(df)}")
            
            # 生成order_agg
            calculate_order_metrics = get_calculate_order_metrics()
            order_agg = calculate_order_metrics(df, calc_mode='all_with_fallback')
            
            # ✅ 商品维度分析需要日期字段，从df中合并
            if '日期' not in order_agg.columns and '日期' in df.columns and '订单ID' in df.columns:
                # 提取订单ID-日期映射（每个订单取第一个商品的日期）
                date_mapping = df[['订单ID', '日期']].drop_duplicates('订单ID')
                order_agg = order_agg.merge(date_mapping, on='订单ID', how='left')
                print(f"✅ [DEBUG] 已为order_agg添加日期字段: {order_agg['日期'].notna().sum()}/{len(order_agg)} 条有日期")
            
            if active_tab == 'order-tab' or active_tab == 'customer-tab':
                # 订单维度分析（兼容旧的customer-tab）
                print(f"🔍 [DEBUG] 执行 analyze_customer_downgrade, 周期={period_days}天")
                try:
                    result = analyze_customer_downgrade(df, order_agg, period_days=period_days)
                    print(f"✅ [DEBUG] analyze_customer_downgrade 执行成功")
                    print(f"  📊 result keys: {list(result.keys())}")
                    print(f"  📊 result['summary'] keys: {list(result.get('summary', {}).keys())}")
                except Exception as e:
                    print(f"❌ [DEBUG] analyze_customer_downgrade 执行失败: {e}")
                    import traceback
                    traceback.print_exc()
                    return dbc.Alert(f"分析失败: {str(e)}", color="danger")
                
                # 如果是全部渠道，额外计算渠道对比
                channel_comparison = None
                if selected_channel == 'all':
                    print(f"🔍 [DEBUG] 执行 analyze_channel_comparison, 周期={period_days}天")
                    channel_comparison = analyze_channel_comparison(df, order_agg, period_days=period_days)
                    print(f"✅ [DEBUG] analyze_channel_comparison 执行成功")
                
                return _create_customer_downgrade_view(result, period_days, channel_comparison)
            
            elif active_tab == 'category-tab':
                # 分类维度分析
                print(f"🔍 [DEBUG] 执行 analyze_category_contribution, 周期={period_days}天")
                result = analyze_category_contribution(df, order_agg, period_days=period_days)
                print(f"✅ [DEBUG] analyze_category_contribution 执行成功")
                return _create_category_contribution_view(result, period_days)
            
            else:
                # 商品维度分析
                print(f"🔍 [DEBUG] 执行 analyze_product_drag, 周期={period_days}天")
                print(f"  📊 df.shape = {df.shape}")
                print(f"  📋 df关键字段: {[c for c in df.columns if c in ['日期', '商品名称', '订单ID', '实收价格', '商品实售价', '一级分类']]}")
                print(f"  📊 order_agg.shape = {order_agg.shape}")
                print(f"  📋 order_agg关键字段: {[c for c in order_agg.columns if c in ['日期', '订单ID', '实收价格']]}")
                result = analyze_product_drag(df, order_agg, period_days=period_days)
                print(f"✅ [DEBUG] analyze_product_drag 执行成功")
                
                # 输出四层分析结果
                product_analysis = result.get('product_analysis', {})
                print(f"  🔴 核心拖累: {len(product_analysis.get('core_drag', []))} 个")
                print(f"  🟡 异常变化: {len(product_analysis.get('abnormal', []))} 个")
                print(f"  🆕 新增低价: {len(product_analysis.get('new_low', []))} 个")
                high_price = product_analysis.get('high_price', {})
                print(f"  🚀 高价带: 爆品{len(high_price.get('star', []))} 稳定{len(high_price.get('stable', []))} 滞销{len(high_price.get('decline', []))}")
                
                return _create_product_drag_view(result, period_days)
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return dbc.Alert(f"加载失败: {str(e)}", color="danger")

    # ==================== 单品洞察弹窗回调 ====================
    @app.callback(
        Output('product-insight-modal', 'is_open'),
        Output('product-insight-modal-title', 'children'),
        Output('product-insight-modal-body', 'children'),
        Output('product-insight-name-store', 'data'),
        Input({'type': 'product-insight-link', 'index': ALL}, 'n_clicks'),
        Input('product-insight-modal-close', 'n_clicks'),
        State('db-store-filter', 'value'),
        State('product-insight-modal', 'is_open'),
        prevent_initial_call=True
    )
    def toggle_product_insight_modal(link_clicks, close_clicks, selected_stores, is_open):
        """
        单品洞察弹窗回调
        
        触发条件:
        1. 点击诊断详情表格中的商品名称链接
        2. 点击关闭按钮
        """
        ctx = callback_context
        if not ctx.triggered:
            return is_open, no_update, no_update, no_update
        
        trigger_id = ctx.triggered[0]['prop_id']
        trigger_value = ctx.triggered[0]['value']
        
        print(f"[单品洞察] 触发: {trigger_id}, value: {trigger_value}")
        
        # 关闭弹窗
        if 'product-insight-modal-close' in trigger_id:
            return False, no_update, no_update, None
        
        # 🔧 修复：只有真正点击（n_clicks >= 1）才触发
        # 当按钮首次渲染时 n_clicks=0 或 None，不应触发
        if trigger_value is None or trigger_value == 0:
            print(f"[单品洞察] 跳过：trigger_value={trigger_value}")
            return no_update, no_update, no_update, no_update
        
        # 点击商品链接
        if 'product-insight-link' in trigger_id:
            try:
                # 解析触发的组件ID
                import json
                trigger_info = json.loads(trigger_id.replace('.n_clicks', ''))
                product_name = trigger_info.get('index', '')
                
                if not product_name:
                    return is_open, no_update, no_update, no_update
                
                print(f"[单品洞察] 打开商品: {product_name}")
                
                # 获取数据
                GLOBAL_DATA = get_real_global_data()
                if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                    return True, f"🔍 {product_name}", dbc.Alert("暂无数据", color="warning"), product_name
                
                # 内存优化：使用视图而非复制
                df = apply_filters_view(
                    GLOBAL_DATA,
                    selected_stores=selected_stores if selected_stores and len(selected_stores) > 0 else None
                )
                
                # 渲染单品洞察
                content = render_product_insight_echarts(df, product_name)
                
                return True, f"🔍 单品洞察: {product_name}", content, product_name
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                return True, "错误", dbc.Alert(f"加载失败: {str(e)}", color="danger"), None
        
        return is_open, no_update, no_update, no_update

    # ==================== 订单商品明细弹窗回调 ====================
    @app.callback(
        Output('order-products-modal', 'is_open'),
        Output('order-products-modal-title', 'children'),
        Output('order-products-modal-body', 'children'),
        Output('selected-order-id-store', 'data'),
        Input('overflow-order-table', 'active_cell'),
        Input('order-products-modal-close', 'n_clicks'),
        State('overflow-order-table', 'data'),
        State('db-store-filter', 'value'),
        State('order-products-modal', 'is_open'),
        prevent_initial_call=True
    )
    def toggle_order_products_modal(active_cell, close_clicks, table_data, selected_stores, is_open):
        """
        订单商品明细弹窗回调
        
        触发条件:
        1. 点击订单视图表格中的任意单元格
        2. 点击关闭按钮
        
        功能:
        - 显示该订单中所有商品的亏损情况
        - 按商品毛利排序（亏损最严重的在前）
        """
        ctx = callback_context
        if not ctx.triggered:
            return is_open, no_update, no_update, no_update
        
        trigger_id = ctx.triggered[0]['prop_id']
        
        # 关闭弹窗
        if 'order-products-modal-close' in trigger_id:
            return False, no_update, no_update, None
        
        # 点击订单表格
        if 'overflow-order-table' in trigger_id and active_cell:
            try:
                # active_cell 是一个字典，包含 row, column, column_id 等
                if not isinstance(active_cell, dict):
                    return no_update, no_update, no_update, no_update
                
                row_idx = active_cell.get('row')
                if row_idx is None or not table_data or row_idx >= len(table_data):
                    return no_update, no_update, no_update, no_update
                
                row_data = table_data[row_idx]
                order_id = row_data.get('订单ID', '')
                
                if not order_id:
                    return no_update, no_update, no_update, no_update
                
                print(f"[订单商品明细] 打开订单: {order_id}")
                
                # 获取数据
                GLOBAL_DATA = get_real_global_data()
                if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                    return True, f"📦 订单商品明细", dbc.Alert("暂无数据", color="warning"), order_id
                
                # 内存优化：使用视图而非复制
                df = apply_filters_view(
                    GLOBAL_DATA,
                    selected_stores=selected_stores if selected_stores and len(selected_stores) > 0 else None
                )
                
                # 筛选该订单的商品
                order_id_col = '订单ID' if '订单ID' in df.columns else None
                if not order_id_col:
                    return True, f"📦 订单商品明细", dbc.Alert("数据中缺少订单ID字段", color="warning"), order_id
                
                order_items = df[df[order_id_col] == order_id].copy()
                
                if order_items.empty:
                    return True, f"📦 订单: {order_id}", dbc.Alert("未找到该订单的商品数据", color="warning"), order_id
                
                # 计算每个商品的毛利
                sales_field = '月售' if '月售' in order_items.columns else '销量'
                cost_col = '商品采购成本' if '商品采购成本' in order_items.columns else '成本'
                
                # 实收价格
                if '实收价格' in order_items.columns:
                    order_items['商品销售额'] = order_items['实收价格'].fillna(0) * order_items[sales_field].fillna(1)
                elif '商品实售价' in order_items.columns:
                    order_items['商品销售额'] = order_items['商品实售价'].fillna(0)
                else:
                    order_items['商品销售额'] = 0
                
                # 商品成本
                if cost_col in order_items.columns:
                    order_items['商品成本'] = order_items[cost_col].fillna(0)
                else:
                    order_items['商品成本'] = 0
                
                # 商品毛利
                order_items['商品毛利'] = order_items['商品销售额'] - order_items['商品成本']
                
                # 单品成本
                order_items['单品成本'] = order_items['商品成本'] / order_items[sales_field].replace(0, 1).fillna(1)
                
                # 选择展示列
                display_cols = ['商品名称', sales_field, '商品原价', '实收价格', '单品成本', '商品毛利']
                if '一级分类名' in order_items.columns:
                    display_cols.insert(0, '一级分类名')
                elif '一级分类' in order_items.columns:
                    display_cols.insert(0, '一级分类')
                
                display_cols = [c for c in display_cols if c in order_items.columns]
                
                # 按商品毛利排序（亏损最严重的在前）
                order_items = order_items.sort_values('商品毛利', ascending=True)
                
                # 计算订单汇总 - 确保数值类型
                order_profit_raw = row_data.get('订单实际利润', 0)
                try:
                    order_profit = float(order_profit_raw) if order_profit_raw else 0
                except (ValueError, TypeError):
                    order_profit = 0
                
                # 获取订单编号（用于展示，如果没有则显示订单ID）
                order_number = row_data.get('订单编号', '') or str(order_id)
                    
                total_items = len(order_items)
                loss_items = len(order_items[order_items['商品毛利'] < 0])
                
                # 构建弹窗内容
                content = html.Div([
                    # 订单信息汇总
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Small("订单编号", className="text-muted d-block"),
                                html.Span(f"{order_number}", className="fw-bold", style={'fontSize': '12px'})
                            ], className="text-center p-2 bg-light rounded")
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.Small("订单利润", className="text-muted d-block"),
                                html.Span(f"¥{order_profit:.2f}", className="fw-bold text-danger" if order_profit < 0 else "fw-bold text-success")
                            ], className="text-center p-2 bg-light rounded")
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.Small("商品数", className="text-muted d-block"),
                                html.Span(f"{total_items}个", className="fw-bold")
                            ], className="text-center p-2 bg-light rounded")
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.Small("亏损商品", className="text-muted d-block"),
                                html.Span(f"{loss_items}个", className="fw-bold text-danger" if loss_items > 0 else "fw-bold")
                            ], className="text-center p-2 bg-light rounded")
                        ], width=3),
                    ], className="mb-3"),
                    
                    # 商品明细表格
                    html.H6("📦 商品亏损明细（按毛利排序）", className="mb-2"),
                    dash_table.DataTable(
                        data=order_items[display_cols].round(2).to_dict('records'),
                        columns=[
                            {'name': c, 'id': c, 'type': 'numeric', 'format': {'specifier': ',.2f'}} 
                            if c in ['商品原价', '实收价格', '单品成本', '商品毛利'] 
                            else {'name': c, 'id': c}
                            for c in display_cols
                        ],
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
                        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                        style_data_conditional=[
                            {'if': {'column_id': '商品毛利', 'filter_query': '{商品毛利} < 0'}, 
                             'color': 'red', 'fontWeight': 'bold', 'backgroundColor': '#fff5f5'},
                        ],
                        page_size=20,
                    ),
                    
                    # 说明
                    html.Div([
                        html.Small([
                            html.Strong("📌 说明："),
                            "商品毛利 = 实收价格 × 销量 - 商品采购成本；负值表示该商品在此订单中亏损"
                        ], className="text-muted")
                    ], className="mt-2 p-2 bg-light rounded")
                ])
                
                # order_id 可能是整数或字符串，转为字符串后截取
                order_id_str = str(order_id)
                # 标题使用订单编号
                title_display = order_number if order_number else order_id_str
                title_display = title_display[:30] + "..." if len(title_display) > 30 else title_display
                return True, f"📦 订单商品明细: {title_display}", content, order_id
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                return True, "错误", dbc.Alert(f"加载失败: {str(e)}", color="danger"), None
        
        return is_open, no_update, no_update, no_update

    # ==================== 诊断表格商品点击回调 ====================
    # 🔧 使用时间戳避免首次渲染触发
    _diagnosis_last_click = {'time': 0}
    
    @app.callback(
        Output('product-insight-modal', 'is_open', allow_duplicate=True),
        Output('product-insight-modal-title', 'children', allow_duplicate=True),
        Output('product-insight-modal-body', 'children', allow_duplicate=True),
        Output('product-insight-name-store', 'data', allow_duplicate=True),
        Input({'type': 'diagnosis-product-table', 'index': ALL}, 'active_cell'),
        State({'type': 'diagnosis-product-table', 'index': ALL}, 'data'),
        State('db-store-filter', 'value'),
        prevent_initial_call=True
    )
    def handle_diagnosis_table_click(active_cells, table_datas, selected_stores):
        """
        处理诊断详情表格中商品名称的点击
        
        当用户点击商品名称列时，打开单品洞察弹窗
        """
        import time
        nonlocal _diagnosis_last_click
        
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update
        
        trigger_value = ctx.triggered[0]['value']
        
        # 🔧 如果trigger_value为空，跳过
        if not trigger_value:
            return no_update, no_update, no_update, no_update
        
        # 查找被点击的单元格
        active_cell = None
        data = None
        for ac, d in zip(active_cells, table_datas):
            if ac:
                active_cell = ac
                data = d
                break
        
        if not active_cell or not data:
            return no_update, no_update, no_update, no_update
        
        # 检查是否点击的是商品名称列
        if active_cell.get('column_id') != '商品名称':
            return no_update, no_update, no_update, no_update
        
        # 🔧 首次渲染检测
        current_time = time.time()
        if _diagnosis_last_click['time'] == 0:
            _diagnosis_last_click['time'] = current_time
            print(f"[诊断表格] 首次渲染，跳过")
            return no_update, no_update, no_update, no_update
        
        _diagnosis_last_click['time'] = current_time
        
        row_idx = active_cell.get('row', 0)
        if row_idx >= len(data):
            return no_update, no_update, no_update, no_update
        
        product_name = data[row_idx].get('商品名称', '')
        if not product_name:
            return no_update, no_update, no_update, no_update
        
        print(f"[诊断表格] 点击商品: {product_name}")
        
        try:
            # 获取数据
            GLOBAL_DATA = get_real_global_data()
            if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                return True, f"🔍 {product_name}", dbc.Alert("暂无数据", color="warning"), product_name
            
            # 内存优化：使用视图而非复制
            df = apply_filters_view(
                GLOBAL_DATA,
                selected_stores=selected_stores if selected_stores and len(selected_stores) > 0 else None
            )
            
            # 渲染单品洞察
            content = render_product_insight_echarts(df, product_name)
            
            return True, f"🔍 单品洞察: {product_name}", content, product_name
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return True, "错误", dbc.Alert(f"加载失败: {str(e)}", color="danger"), None

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
        [State('db-store-filter', 'value'),
         State('product-health-channel-store', 'data'),  # V5.2: 添加渠道筛选状态
         State('product-health-date-range-store', 'data')],  # V7.2: 添加日期范围状态
        prevent_initial_call=True
    )
    def export_product_scoring_report(n_clicks, selected_stores, current_channel, current_days):
        """
        导出商品综合评分报告
        
        V5.2更新：支持按渠道筛选导出
        V7.2修复：导出数据与看板显示保持一致，使用相同的日期范围和计算逻辑
        """
        if not n_clicks:
            return no_update
        
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return no_update
        
        # 内存优化：使用视图而非复制（先筛选门店）
        df = apply_filters_view(
            GLOBAL_DATA,
            selected_stores=selected_stores if selected_stores and len(selected_stores) > 0 else None
        )
        
        # V5.2: 应用渠道筛选
        channel_suffix = ""
        if current_channel and current_channel != 'ALL' and '渠道' in df.columns:
            df = df[df['渠道'] == current_channel]  # 使用视图，如果后续需要修改再copy
            channel_suffix = f"_{current_channel}"
            print(f"[导出] 按渠道筛选: {current_channel}, 数据量: {len(df)} 行")
        
        # V7.2修复：获取当前日期范围（注意：0表示全部数据，不能用if判断）
        days_range = current_days if current_days is not None else 15  # 默认15天
        print(f"\n[导出调试] ===== 开始导出 =====")
        print(f"[导出调试] current_days参数: {current_days}")
        print(f"[导出调试] 使用日期范围: {days_range}天 {'(全部数据)' if days_range == 0 else ''}")
        print(f"[导出调试] 选中门店: {selected_stores}")
        print(f"[导出调试] 当前渠道: {current_channel}")
        print(f"[导出调试] 原始数据行数: {len(df)}")
        
        try:
            # V7.2修复：使用与看板显示相同的计算逻辑
            export_df = get_product_scoring_export_data(df, days_range=days_range)
            if export_df is not None and not export_df.empty:
                from io import BytesIO
                output = BytesIO()
                export_df.to_excel(output, index=False, engine='openpyxl')
                output.seek(0)
                # V7.2: 文件名包含渠道和日期范围信息
                date_range_label = "全部数据" if days_range == 0 else f"{days_range}天"
                filename = f"商品综合评分报告{channel_suffix}_{date_range_label}.xlsx"
                print(f"[导出调试] 导出文件名: {filename}")
                print(f"[导出调试] ===== 导出完成 =====\n")
                return dcc.send_bytes(output.getvalue(), filename)
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
         Output('current-category-filter-label', 'children'),
         Output('product-health-tabs', 'active_tab'),
         Output('product-health-date-range-store', 'data')],
        [Input({'type': 'octant-filter-btn', 'index': ALL}, 'n_clicks'),
         Input({'type': 'quadrant-filter-btn', 'index': ALL}, 'n_clicks'),  # V5.0新增：四象限筛选
         Input({'type': 'category-filter-btn', 'index': ALL}, 'n_clicks'),
         Input({'type': 'score-level-filter-btn', 'index': ALL}, 'n_clicks'),
         Input('btn-clear-scoring-filter', 'n_clicks'),
         Input({'type': 'health-date-btn', 'days': ALL}, 'n_clicks')],  # 修改：日期按钮组
        [State('db-store-filter', 'value'),
         State('product-health-channel-store', 'data'),  # V6.1新增：渠道筛选状态
         State('product-health-tabs', 'active_tab'),
         State('current-category-filter-label', 'children'),
         State('product-health-date-range-store', 'data')],  # 新增：当前日期范围
        prevent_initial_call=True
    )
    def filter_scoring_table(octant_clicks, quadrant_clicks, category_clicks, score_level_clicks, clear_clicks, date_btn_clicks, selected_stores, selected_channel, current_active_tab, current_category_label, current_days):
        """
        点击象限/品类按钮筛选表格数据 + 联动更新Tab内容
        
        V5.0更新：
        - 简化为四象限分类（明星/潜力/引流/问题）
        - 点击四象限按钮 → 按象限筛选表格 + 自动展开表格
        - 点击品类按钮 → 按品类筛选表格 + 联动更新评分概览/象限分布Tab
        - 点击清除按钮 → 显示全部数据 + 恢复Tab内容
        
        V5.2修复：保持当前Tab状态，切换分类时不跳转Tab
        V5.3修复：四象限筛选时保持当前分类筛选状态
        V6.0新增：独立日期选择器，支持7/15/30/60/90天分析周期
        V6.1修复：应用渠道筛选，避免显示全部渠道混合数据
        V7.4更新：删除评分等级筛选功能（评分体系已删除）
        """
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        triggered_id = ctx.triggered[0]['prop_id']
        
        # V7.2修复：解析日期选择（注意：0表示全部数据，不能用if判断）
        selected_days = current_days if current_days is not None else 15  # 默认15天
        if 'health-date-btn' in triggered_id:
            try:
                import json
                button_id = json.loads(triggered_id.split('.')[0])
                selected_days = button_id.get('days', 15)
                print(f"[商品健康分析] 日期按钮点击: {selected_days}天")
            except:
                selected_days = 15
        
        days_range = selected_days
        print(f"[商品健康分析] 当前日期范围: {days_range}天, 触发: {triggered_id}")
        
        # V6.1修复：不再初始化active_tab，避免触发页面跳转
        # 所有分支都会显式设置active_tab为no_update
        
        # 获取数据
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return html.Div("暂无数据"), "无数据", True, no_update, no_update, no_update, no_update
        
        # 内存优化：使用视图而非复制
        df = apply_filters_view(
            GLOBAL_DATA,
            selected_stores=selected_stores if selected_stores and len(selected_stores) > 0 else None
        )
        
        # V6.1新增：应用渠道筛选
        if selected_channel and selected_channel != 'ALL' and '渠道' in df.columns:
            df = df[df['渠道'] == selected_channel]
            print(f"[商品健康分析-调试] 应用渠道筛选: {selected_channel}, 剩余数据: {len(df)} 行")
        
        if df.empty:
            return html.Div(f"渠道 '{selected_channel}' 暂无数据"), "无数据", True, no_update, no_update, no_update, no_update
        
        # V5.3: 解析当前的分类筛选状态（用于四象限/评分等级筛选时保持分类）
        existing_category_filter = None
        if current_category_label and current_category_label != "全部商品":
            # 从 "分类名 (N个商品)" 提取分类名
            if '(' in str(current_category_label):
                existing_category_filter = str(current_category_label).split('(')[0].strip()
            else:
                existing_category_filter = current_category_label
        
        # V6.0: 计算商品评分（带趋势，days=0表示全部数据不对比）
        if days_range == 0:
            # 全部数据，不参与对比
            print(f"[商品健康分析-调试] ✅ 使用全部数据模式，不进行趋势对比")
            product_scores = calculate_enhanced_product_scores(df)
            print(f"[商品健康分析-调试] 计算完成，结果行数: {len(product_scores)}")
            if product_scores.empty:
                print(f"[商品健康分析-调试] ⚠️ 全部数据计算结果为空，数据行数: {len(df)}")
            else:
                print(f"[商品健康分析-调试] 结果列: {list(product_scores.columns)}")
        else:
            # 指定天数，参与对比
            print(f"[商品健康分析-调试] 使用近{days_range}天数据进行趋势对比")
            product_scores = calculate_enhanced_product_scores_with_trend(df, days=days_range)
            print(f"[商品健康分析-调试] 计算完成，结果行数: {len(product_scores)}")
        
        if product_scores.empty:
            return html.Div("暂无商品数据"), "无数据", True, no_update, no_update, no_update, days_range
        
        # 确定使用的象限字段名（兼容新旧版本）
        quadrant_col = '四象限分类' if '四象限分类' in product_scores.columns else '八象限分类'
        category_col_name = '一级分类名' if '一级分类名' in product_scores.columns else None
        
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
        elif 'quadrant-filter-btn' in triggered_id or 'octant-filter-btn' in triggered_id:
            # V5.0四象限筛选（兼容旧版八象限）
            # V5.3修复：保持当前分类筛选状态
            try:
                import json
                prop_id_json = triggered_id.split('.')[0]
                id_dict = json.loads(prop_id_json)
                filter_value = id_dict.get('index')
                if filter_value:
                    filter_type = 'quadrant'
                    # V5.3: 如果有分类筛选，先按分类过滤再统计象限数量
                    scores_for_count = product_scores.copy()
                    if existing_category_filter and category_col_name:
                        scores_for_count = scores_for_count[scores_for_count[category_col_name] == existing_category_filter]
                    count = len(scores_for_count[scores_for_count[quadrant_col] == filter_value])
                    filter_label = f"{filter_value} ({count}个)"
                    # 保持当前品类筛选状态
                    category_filter = existing_category_filter
                    category_label = current_category_label if current_category_label else "全部商品"
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
            # V7.4：评分等级筛选已删除（评分体系已删除）
            # 如果用户点击了旧的评分等级按钮（不应该存在），忽略
            print("⚠️ 评分等级筛选已删除，忽略此操作")
            pass
        
        # V5.3: 创建筛选后的表格，传入分类筛选参数
        # V6.1新增: 传递当前渠道用于表格列显示和提示信息
        table = create_product_scoring_table_v4(product_scores, filter_type, filter_value, category_filter=category_filter, current_channel=selected_channel)
        
        # 创建联动的Tab内容（品类筛选、清除、日期变化时更新）
        if 'category-filter-btn' in triggered_id or 'btn-clear-scoring-filter' in triggered_id or 'health-date-btn' in triggered_id:
            # V5.3: 传入raw_df用于趋势分析，同时按分类筛选
            print(f"[商品健康分析-调试] 🔄 需要更新Tab内容")
            raw_df_filtered = df  # 直接引用
            if category_filter and category_filter != '__all__':
                category_col = '一级分类名' if '一级分类名' in df.columns else None
                if category_col:
                    raw_df_filtered = df[df[category_col] == category_filter]  # 移除.copy()
            tab_content = create_product_health_content(product_scores, category_filter, category_filter, raw_df=raw_df_filtered, days_range=days_range)
            print(f"[商品健康分析-调试] Tab内容已更新")
            # V6.1修复：即使更新Tab内容，也保持当前Tab位置，不跳转
            active_tab = no_update
        else:
            # 象限/评分等级筛选时不更新Tab内容，也不改变Tab状态
            print(f"[商品健康分析-调试] ⏭️ 跳过Tab内容更新")
            tab_content = no_update
            active_tab = no_update
        
        print(f"[商品健康分析-调试] 📤 返回days_range值: {days_range}")
        print(f"[商品健康分析-调试] ===== 回调结束 =====\n")
        return table, filter_label, should_open_table, tab_content, category_label, active_tab, days_range

    # ==================== 日期按钮样式更新回调 ====================
    @app.callback(
        [Output({'type': 'health-date-btn', 'days': 0}, 'outline'),
         Output({'type': 'health-date-btn', 'days': 7}, 'outline'),
         Output({'type': 'health-date-btn', 'days': 15}, 'outline'),
         Output({'type': 'health-date-btn', 'days': 30}, 'outline'),
         Output({'type': 'health-date-btn', 'days': 60}, 'outline'),
         Output({'type': 'health-date-btn', 'days': 90}, 'outline')],
        Input('product-health-date-range-store', 'data'),
        prevent_initial_call=False
    )
    def update_date_button_styles(selected_days):
        """更新日期按钮的选中状态（outline=True为未选中，False为选中）"""
        selected = selected_days if selected_days is not None else 15
        print(f"[按钮样式更新] selected_days: {selected_days}, 最终selected: {selected}")
        result = (
            selected != 0,   # 全部
            selected != 7,   # 7天
            selected != 15,  # 15天
            selected != 30,  # 30天
            selected != 60,  # 60天
            selected != 90   # 90天
        )
        print(f"[按钮样式更新] 返回outline状态: 全部={result[0]}, 7天={result[1]}, 15天={result[2]}, 30天={result[3]}, 60天={result[4]}, 90天={result[5]}")
        return result

    # ==================== V5.2 渠道筛选回调（修复选项丢失问题）====================
    @app.callback(
        [Output('product-scoring-section-container', 'children'),
         Output('product-health-channel-store', 'data')],
        Input('product-health-channel-filter', 'value'),
        [State('db-store-filter', 'value')],
        prevent_initial_call=True
    )
    def filter_product_health_by_channel(channel, selected_stores):
        """
        渠道筛选回调 - 重新计算商品健康分析
        
        V5.2修复：
        - 渠道下拉框选项始终基于全量数据（门店筛选后），不再因渠道筛选而减少
        - 选择渠道后，只有评分/象限/表格基于筛选后数据计算
        """
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return html.Div("暂无数据"), 'ALL'
        
        # 应用门店筛选（使用视图，延迟copy）
        df_full = GLOBAL_DATA
        if selected_stores:
            if isinstance(selected_stores, str):
                selected_stores = [selected_stores]
            if len(selected_stores) > 0 and '门店名称' in df_full.columns:
                df_full = df_full[df_full['门店名称'].isin(selected_stores)]
        
        # V5.2: 从门店筛选后的全量数据生成渠道选项（不受渠道筛选影响）
        all_channel_options = [{'label': '📊 全部渠道', 'value': 'ALL'}]
        if '渠道' in df_full.columns:
            channels = sorted(df_full['渠道'].dropna().unique())
            all_channel_options += [{'label': ch, 'value': ch} for ch in channels]
        
        # 应用渠道筛选（用于计算的数据）
        df = df_full.copy()
        if channel and channel != 'ALL' and '渠道' in df.columns:
            df = df[df['渠道'] == channel]  # 已经copy过了，这里不需要再copy
            print(f"[商品健康分析] 渠道筛选: {channel}, 剩余数据: {len(df)} 行")
        
        if df.empty:
            return dbc.Alert(f"渠道 '{channel}' 暂无数据", color="warning"), channel
        
        # V5.2: 传入全量渠道选项和当前选中值
        section = create_product_scoring_section(df, all_channel_options=all_channel_options, current_channel=channel)
        
        return section, channel

    # ==================== V5.3 趋势分析范围切换回调 ====================
    @app.callback(
        Output('trend-tab-content-container', 'children'),
        [Input({'type': 'trend-range-btn', 'days': ALL}, 'n_clicks')],
        [State('db-store-filter', 'value'),
         State('product-health-channel-store', 'data'),
         State('current-category-filter-label', 'children')],
        prevent_initial_call=True
    )
    def switch_trend_range(n_clicks_list, selected_stores, channel, category_label):
        """
        V5.3：切换趋势分析对比范围（15天/30天）
        只更新趋势Tab内容，不影响整个商品健康分析容器
        """
        ctx = callback_context
        if not ctx.triggered or not any(n_clicks_list):
            return no_update
        
        # 解析触发的按钮
        triggered = ctx.triggered[0]
        prop_id = triggered['prop_id']
        
        try:
            button_id = json.loads(prop_id.rsplit('.', 1)[0])
            days_range = button_id.get('days', 15)  # 默认15天
        except:
            days_range = 15
        
        print(f"[趋势分析V5.3] 切换对比范围: {days_range}天")
        
        # 获取数据
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return no_update
        
        # 内存优化：先用视图筛选门店
        df = apply_filters_view(
            GLOBAL_DATA,
            selected_stores=selected_stores if selected_stores and len(selected_stores) > 0 else None
        )
        
        # 应用渠道筛选（视图模式，无需copy）
        if channel and channel != 'ALL' and '渠道' in df.columns:
            df = df[df['渠道'] == channel]  # 筛选不修改原数据，使用视图即可
        
        # 解析分类筛选
        category_filter = None
        if category_label and category_label != "全部商品":
            # 从 "分类名 (N个商品)" 提取分类名
            if '(' in category_label:
                category_filter = category_label.split('(')[0].strip()
            else:
                category_filter = category_label
        
        # 返回趋势Tab内容（V5.3版本）
        return create_trend_tab_content(df, category_filter, days_range)

    # ==================== V5.3 迁移详情按钮点击回调 ====================
    @app.callback(
        Output('migration-detail-container', 'children'),
        [Input({'type': 'migration-detail-btn', 'from': ALL, 'to': ALL}, 'n_clicks')],
        [State('db-store-filter', 'value'),
         State('product-health-channel-store', 'data'),
         State('current-category-filter-label', 'children'),
         State('quadrant-trend-range-store', 'data')],
        prevent_initial_call=True
    )
    def show_migration_detail(n_clicks_list, selected_stores, channel, category_label, current_range):
        """
        V5.3：点击迁移统计表格的详情按钮，显示详细商品列表（含店内码）
        """
        ctx = callback_context
        if not ctx.triggered or not any(n_clicks_list):
            return no_update
        
        # 获取点击的按钮信息
        triggered = ctx.triggered[0]
        prop_id = triggered['prop_id']
        
        try:
            button_id = json.loads(prop_id.rsplit('.', 1)[0])
            from_quadrant = button_id.get('from', '')
            to_quadrant = button_id.get('to', '')
        except:
            return html.Div("解析参数失败", className="text-muted")
        
        print(f"[迁移详情V5.3] 查看: {from_quadrant} → {to_quadrant}")
        
        # 获取数据
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return html.Div("暂无数据", className="text-muted")
        
        # 内存优化：先用视图筛选门店
        df = apply_filters_view(
            GLOBAL_DATA,
            selected_stores=selected_stores if selected_stores and len(selected_stores) > 0 else None
        )
        
        if channel and channel != 'ALL' and '渠道' in df.columns:
            df = df[df['渠道'] == channel]  # 使用视图，减少内存
        
        # 解析分类筛选
        category_filter = None
        if category_label and category_label != "全部商品":
            if '(' in category_label:
                category_filter = category_label.split('(')[0].strip()
            else:
                category_filter = category_label
        
        if category_filter:
            category_col = '一级分类名' if '一级分类名' in df.columns else None
            if category_col:
                df = df[df[category_col] == category_filter]  # 使用视图
        
        # V5.3: 使用前后对半分计算趋势数据
        days_range = current_range if current_range else 15
        trend_data = calculate_period_comparison_quadrants(df, days_range=days_range)
        
        if not trend_data:
            return html.Div("暂无趋势数据", className="text-muted")
        
        # V5.3: 从product_details获取迁移信息
        product_details = trend_data.get('product_details', {})
        
        # 找出符合条件的商品
        matching_products = []
        for product, details in product_details.items():
            first_q = details.get('期初象限', '')
            last_q = details.get('期末象限', '')
            if first_q == from_quadrant and last_q == to_quadrant:
                matching_products.append(product)
        
        if not matching_products:
            return html.Div("未找到符合条件的商品", className="text-muted p-3")
        
        # V5.3: 创建详情表格（含店内码）
        return create_migration_detail_table_v3(df, matching_products, from_quadrant, to_quadrant, trend_data)

    # ==================== 日期筛选按钮回调 ====================
    @app.callback(
        Output('diagnosis-detail-modal-body', 'children', allow_duplicate=True),
        Input({'type': 'date-filter-btn', 'card': ALL, 'days': ALL}, 'n_clicks'),
        State('diagnosis-detail-type-store', 'data'),
        State('db-store-filter', 'value'),
        prevent_initial_call=True
    )
    def handle_date_filter_click(n_clicks_list, detail_type, selected_stores):
        """处理日期筛选按钮点击，更新表格数据"""
        ctx = callback_context
        if not ctx.triggered:
            return no_update
        
        # 检查是否有按钮被点击
        if not any(n_clicks_list):
            return no_update
        
        # 获取触发的按钮信息
        trigger = ctx.triggered[0]
        prop_id = trigger['prop_id']
        
        try:
            # 解析按钮ID
            import json
            button_id = json.loads(prop_id.rsplit('.', 1)[0])
            card_type = button_id.get('card')
            days = button_id.get('days')
            
            print(f"[日期筛选] 卡片类型: {card_type}, 天数: {days}")
            
            # 获取数据
            GLOBAL_DATA = get_real_global_data()
            if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                return dbc.Alert("数据未加载", color="warning")
            
            # 内存优化：使用视图而非复制
            df = apply_filters_view(
                GLOBAL_DATA,
                selected_stores=selected_stores if selected_stores and len(selected_stores) > 0 else None
            )
            
            # 根据卡片类型生成对应内容
            if card_type == 'overflow':
                return create_overflow_detail_table(df, days=days)
            elif card_type == 'delivery':
                return create_delivery_detail_table(df, days=days)
            elif card_type == 'price_abnormal':
                return create_price_abnormal_detail_table(df, days=days)
            elif card_type == 'profit_drop':
                return create_profit_drop_detail_table(df, days=days)
            elif card_type == 'traffic':
                return create_traffic_drop_detail_table(df, days=days)
            elif card_type == 'hot_products':
                return create_hot_products_detail_table(df, days=days)
            elif card_type == 'high_profit':
                return create_high_profit_detail_table(df, days=days)
            else:
                return no_update
                
        except Exception as e:
            print(f"[日期筛选错误] {e}")
            import traceback
            traceback.print_exc()
            return no_update

    # 🔄 场景自动切换推荐日期范围
    @app.callback(
        Output('calculator-date-range', 'value'),
        Input('quick-scene-store', 'data'),
        prevent_initial_call=True
    )
    def auto_switch_date_range(scene):
        """根据快捷场景自动切换推荐的数据周期"""
        if not scene:
            return no_update
        
        scene_date_map = {
            'profit_drop': 7,      # 利润率下滑 → 7天
            'profit_amount_drop': 7,  # 利润额下滑 → 7天
            'sales_drop': 7,       # 销量下滑 → 7天
            'stagnant': 30,        # 滞销清仓 → 30天（需要长周期判断）
            'price_opportunity': 7,   # 提价机会 → 7天
        }
        
        recommended_days = scene_date_map.get(scene, 7)
        print(f"[场景切换] {scene} → 推荐数据范围: {recommended_days}天")
        return recommended_days
    
    # 📊 显示当前数据范围信息
    @app.callback(
        Output('calculator-date-info', 'children'),
        [Input('calculator-date-range', 'value'),
         Input('quick-scene-store', 'data')]
    )
    def update_date_info(selected_days, scene):
        """更新数据范围提示信息"""
        GLOBAL_FULL_DATA = get_real_global_full_data()
        if GLOBAL_FULL_DATA is None or GLOBAL_FULL_DATA.empty:
            return ""
        
        try:
            date_col = '日期' if '日期' in GLOBAL_FULL_DATA.columns else '下单时间'
            if date_col not in GLOBAL_FULL_DATA.columns:
                return ""
            
            df_with_date = GLOBAL_FULL_DATA  # 直接引用
            df_with_date[date_col] = pd.to_datetime(df_with_date[date_col])
            max_date = df_with_date[date_col].max()
            min_date = df_with_date[date_col].min()
            
            if selected_days and selected_days > 0:
                actual_query_days = selected_days * 2 + 1  # 用于对比分析
                start_date = max_date - timedelta(days=actual_query_days - 1)
                start_date = max(start_date, min_date)  # 不超过数据最小日期
                
                scene_tips = {
                    'profit_drop': '（对比前后期利润率变化）',
                    'profit_amount_drop': '（对比前后期利润额变化）',
                    'sales_drop': '（对比前后期销量变化）',
                    'stagnant': '（滞销判断需要长周期数据）',
                    'price_opportunity': '（分析提价安全性）',
                }
                tip = scene_tips.get(scene, '')
                
                # 滞销场景特殊高亮提示
                if scene == 'stagnant':
                    return html.Div([
                        html.Span([
                            f"📅 实际查询范围: ",
                            html.Strong(f"{start_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}", className="text-primary"),
                            f" (共{actual_query_days}天)"
                        ]),
                        html.Br(),
                        html.Span([
                            html.I(className="fas fa-info-circle text-info me-1"),
                            html.Strong("滞销分析自动使用30天数据", className="text-info"),
                            "，准确判断商品最后销售日期"
                        ], className="small")
                    ])
                
                return html.Span([
                    f"📅 实际查询范围: ",
                    html.Strong(f"{start_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"),
                    f" (共{actual_query_days}天，用于{selected_days}天数据的对比分析{tip})"
                ])
            else:
                total_days = (max_date - min_date).days + 1
                return html.Span([
                    f"📅 数据范围: ",
                    html.Strong(f"{min_date.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')}"),
                    f" (共{total_days}天)"
                ])
        except Exception as e:
            return f"数据范围信息获取失败: {str(e)}"

    # ==================== 客单价趋势图下钻回调 ====================
    @app.callback(
        [Output('aov-hourly-drill-down', 'children'),
         Output('aov-hourly-drill-down', 'style')],
        Input('aov-trend-chart', 'click_data'),
        prevent_initial_call=True
    )
    def update_aov_hourly_drill_down(click_data):
        """点击日维度趋势图，下钻到小时维度"""
        try:
            # 如果没有点击数据，隐藏下钻视图
            if not click_data:
                return html.Div(), {'display': 'none'}
            
            print(f"[DEBUG] 接收到 click_data: {click_data}")
            print(f"[DEBUG] click_data 类型: {type(click_data)}")
            
            # 获取点击的日期（DashECharts的数据结构）
            clicked_date_short = None
            if isinstance(click_data, dict):
                # 尝试多种可能的键名
                clicked_date_short = (
                    click_data.get('name') or 
                    click_data.get('axisValue') or 
                    click_data.get('value') or
                    (click_data.get('data', {}).get('name') if isinstance(click_data.get('data'), dict) else None)
                )
                
                print(f"[DEBUG] 提取的日期: {clicked_date_short}")
                
                if not clicked_date_short:
                    # 打印完整数据结构以便调试
                    return html.Div([
                        html.I(className="fas fa-info-circle text-warning me-2"), 
                        "无法解析日期数据",
                        html.Pre(str(click_data), className="mt-2 small text-muted")
                    ], className="text-warning text-center py-3"), {'display': 'block'}
            else:
                return html.Div([
                    html.I(className="fas fa-exclamation-triangle text-danger me-2"),
                    f"点击数据格式错误: {type(click_data)}",
                    html.Pre(str(click_data), className="mt-2 small text-muted")
                ], className="text-danger text-center py-3"), {'display': 'block'}
            
            # 获取全局数据
            GLOBAL_DATA = get_real_global_data()
            if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                return html.Div([
                    html.I(className="fas fa-exclamation-circle text-warning me-2"),
                    "全局数据未加载"
                ], className="text-warning text-center py-3"), {'display': 'block'}
            
            # 注：这里必须copy因为后续有merge操作会修改order_agg
            # 但我们可以延迟copy，先用视图判断
            df = GLOBAL_DATA
            
            # 转换日期格式：'11-23' -> '2025-11-23'
            # 从df中推断年份
            if '日期' in df.columns:
                year = pd.to_datetime(df['日期']).dt.year.mode()[0]
                clicked_date = f"{year}-{clicked_date_short}"
            else:
                clicked_date = f"2025-{clicked_date_short}"
            
            print(f"[DEBUG] 点击日期: {clicked_date}")
            print(f"[DEBUG] df.shape: {df.shape}")
            
            # 生成order_agg（需要带日期字段）
            calculate_order_metrics = get_calculate_order_metrics()
            order_agg = calculate_order_metrics(df, calc_mode='all_with_fallback')
            
            # 为 order_agg 添加日期字段（从 df 中提取）
            if '日期' in df.columns and '订单ID' in df.columns and '订单ID' in order_agg.columns:
                # 从 df 中获取每个订单的日期（drop_duplicates已返回新df，无需copy）
                order_dates = df[['订单ID', '日期']].drop_duplicates('订单ID')
                order_dates['订单ID'] = order_dates['订单ID'].astype(str)
                order_agg['订单ID'] = order_agg['订单ID'].astype(str)
                order_agg = order_agg.merge(order_dates, on='订单ID', how='left')
                print(f"[DEBUG] order_agg添加日期后: {order_agg.shape}, 有日期: {order_agg['日期'].notna().sum()}")
            
            print(f"[DEBUG] order_agg.shape: {order_agg.shape}")
            print(f"[DEBUG] order_agg.columns: {list(order_agg.columns)}")
            
            # 调用小时分析函数
            print(f"[DEBUG] 调用 get_hourly_trend_data, date={clicked_date}")
            hourly_data = get_hourly_trend_data(order_agg, date=clicked_date)
            print(f"[DEBUG] hourly_data 类型: {type(hourly_data)}")
            
            if not hourly_data:
                return html.Div([
                    html.I(className="fas fa-exclamation-triangle text-danger me-2"),
                    "分析函数返回空数据"
                ], className="text-danger text-center py-3"), {'display': 'block'}
            
            if not isinstance(hourly_data, dict):
                return html.Div([
                    html.I(className="fas fa-exclamation-triangle text-danger me-2"),
                    f"返回数据类型错误: {type(hourly_data)}"
                ], className="text-danger text-center py-3"), {'display': 'block'}
            
            print(f"[DEBUG] hourly_data keys: {list(hourly_data.keys())}")
            
            if 'error' in hourly_data:
                return html.Div([
                    html.I(className="fas fa-exclamation-triangle text-danger me-2"),
                    hourly_data['error']
                ], className="text-danger text-center py-3"), {'display': 'block'}
            
            hours = hourly_data.get('hours', [])
            aov_by_hour = hourly_data.get('aov_values', [])
            
            print(f"[DEBUG] hours length: {len(hours)}")
            print(f"[DEBUG] aov_by_hour length: {len(aov_by_hour)}")
            print(f"[DEBUG] hours sample: {hours[:5] if len(hours) > 5 else hours}")
            print(f"[DEBUG] aov_by_hour sample: {aov_by_hour[:5] if len(aov_by_hour) > 5 else aov_by_hour}")
            
            if not hours:
                return html.Div([
                    html.I(className="fas fa-info-circle text-muted me-2"),
                    f"{clicked_date} 无数据"
                ], className="text-muted text-center py-3"), {'display': 'block'}
            
            # 创建小时维度ECharts图表（仅显示当日客单价）
            # 过滤掉0值，避免图表显示问题
            valid_data = [(h, v) for h, v in zip(hours, aov_by_hour) if v > 0]
            if not valid_data:
                return html.Div([
                    html.I(className="fas fa-info-circle text-muted me-2"),
                    f"{clicked_date} 无有效数据（客单价均为0）"
                ], className="text-muted text-center py-3"), {'display': 'block'}
            
            filtered_hours = [item[0] for item in valid_data]
            filtered_aov = [item[1] for item in valid_data]
            
            print(f"[DEBUG] 过滤后数据点数量: {len(filtered_hours)}")
            print(f"[DEBUG] Y轴范围: {min(filtered_aov):.2f} - {max(filtered_aov):.2f}")
            
            hourly_option = {
                'title': {
                    'text': f'📈 {clicked_date} 时段客单价趋势',
                    'left': 'center',
                    'textStyle': {'fontSize': 16, 'fontWeight': 'bold'}
                },
                'tooltip': {
                    'trigger': 'axis',
                    'axisPointer': {'type': 'cross'},
                    'formatter': '{b}<br/>客单价: ¥{c}'
                },
                'grid': {'left': '10%', 'right': '5%', 'top': '20%', 'bottom': '15%', 'containLabel': True},
                'xAxis': {
                    'type': 'category',
                    'data': filtered_hours,
                    'axisLabel': {'fontSize': 11, 'rotate': 45},
                    'boundaryGap': False
                },
                'yAxis': {
                    'type': 'value',
                    'name': '客单价(¥)',
                    'axisLabel': {'formatter': '¥{value}'},
                    'scale': True
                },
                'series': [{
                    'name': '客单价',
                    'type': 'line',
                    'data': filtered_aov,
                    'smooth': True,
                    'symbol': 'circle',
                    'symbolSize': 6,
                    'lineStyle': {'width': 2, 'color': '#4CAF50'},
                    'itemStyle': {
                        'color': '#4CAF50',
                        'borderWidth': 2,
                        'borderColor': '#fff'
                    },
                    'areaStyle': {
                        'color': {
                            'type': 'linear',
                            'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                            'colorStops': [
                                {'offset': 0, 'color': 'rgba(76, 175, 80, 0.3)'},
                                {'offset': 1, 'color': 'rgba(76, 175, 80, 0.05)'}
                            ]
                        }
                    },
                    'markLine': {
                        'data': [{'type': 'average', 'name': '平均值'}],
                        'label': {'formatter': '平均: ¥{c}'},
                        'lineStyle': {'type': 'dashed', 'color': '#999'}
                    }
                }]
            }
            
            # 生成日期选项（最近30天）
            from datetime import datetime, timedelta
            
            clicked_dt = datetime.strptime(clicked_date, '%Y-%m-%d')
            date_options = []
            # 中文星期映射
            weekday_map = {0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'}
            
            for i in range(1, 31):  # 从1开始，排除当前日期
                date = clicked_dt - timedelta(days=i)
                weekday = weekday_map[date.weekday()]
                date_options.append({
                    'label': f"{date.strftime('%m月%d日')} ({weekday})",
                    'value': date.strftime('%Y-%m-%d')
                })
            
            return html.Div([
                # 顶部操作栏
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Button([
                                html.I(className="fas fa-arrow-left me-2"),
                                "返回日维度"
                            ], id='btn-back-to-daily', className="btn btn-sm btn-outline-secondary")
                        ], width=3),
                        dbc.Col([
                            html.Div([
                                html.Span(f"📅 {clicked_date}", className="fw-bold me-3"),
                                html.Button([
                                    html.I(className="fas fa-plus-circle me-2"),
                                    "添加对比日期"
                                ], id='btn-toggle-compare', n_clicks=0, className="btn btn-sm btn-outline-primary")
                            ], className="d-flex align-items-center")
                        ], width=6, className="text-center"),
                        dbc.Col(width=3)
                    ], className="align-items-center")
                ], className="mb-3 pb-3 border-bottom"),
                
                # 对比日期选择器（默认隐藏）
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.Label("对比日期:", className="small text-muted me-2"),
                            dcc.Dropdown(
                                id='compare-date-selector',
                                options=date_options,
                                placeholder="选择日期进行对比...",
                                clearable=True,
                                className="d-inline-block",
                                style={'width': '200px'}
                            )
                        ], className="d-flex align-items-center")
                    ])
                ], id='compare-date-container', style={'display': 'none'}, className="mb-3"),
                
                # 24小时趋势图
                html.Div(id='hourly-trend-chart-container', children=[
                    DashECharts(
                        option=hourly_option,
                        style={'height': '350px', 'width': '100%'}
                    )
                ]),
                
                # 时段对比容器（选择对比日期后显示）
                html.Div(id='period-compare-container', children=[], className="mt-3"),
                
                # 存储当前选中的日期（用于对比功能）
                dcc.Store(id='current-drill-down-date', data=clicked_date)
                
            ], className="p-3 border rounded bg-white"), {'display': 'block'}
            
        except Exception as e:
            return html.Div([
                html.I(className="fas fa-exclamation-triangle text-danger me-2"),
                f"下钻分析出错: {str(e)}"
            ], className="text-danger text-center py-3"), {'display': 'block'}

    # 返回日维度视图（隐藏下钻内容）
    @app.callback(
        Output('aov-hourly-drill-down', 'style', allow_duplicate=True),
        Input('btn-back-to-daily', 'n_clicks'),
        prevent_initial_call=True
    )
    def back_to_daily_view(n_clicks):
        if n_clicks:
            return {'display': 'none'}
    
    # ==================== 对比模式回调 ====================
    
    # 切换对比日期选择器的显示/隐藏
    @app.callback(
        Output('compare-date-container', 'style'),
        Input('btn-toggle-compare', 'n_clicks'),
        State('compare-date-container', 'style'),
        prevent_initial_call=True
    )
    def toggle_compare_date_selector(n_clicks, current_style):
        """点击'添加对比日期'按钮，切换选择器显示状态"""
        if n_clicks:
            if current_style and current_style.get('display') == 'none':
                return {'display': 'block'}
            else:
                return {'display': 'none'}
        return current_style or {'display': 'none'}
    
    # 对比模式：更新趋势图显示两条线
    @app.callback(
        Output('hourly-trend-chart-container', 'children'),
        Input('compare-date-selector', 'value'),
        State('current-drill-down-date', 'data'),
        prevent_initial_call=True
    )
    def update_comparison_chart(compare_date, base_date):
        """当选择对比日期时，更新图表显示两条趋势线"""
        try:
            if not base_date:
                return []
            
            # 获取全局数据（使用视图，避免复制）
            GLOBAL_DATA = get_real_global_data()
            if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                return html.Div("全局数据未加载", className="text-center text-danger py-3")
            
            # 注：使用视图而非复制，仅在需要添加字段时才复制必要的列
            df = GLOBAL_DATA
            
            # 生成order_agg
            calculate_order_metrics = get_calculate_order_metrics()
            order_agg = calculate_order_metrics(df, calc_mode='all_with_fallback')
            
            # 添加日期字段
            if '日期' in df.columns and '订单ID' in df.columns and '订单ID' in order_agg.columns:
                order_dates = df[['订单ID', '日期']].drop_duplicates('订单ID').copy()
                order_dates['订单ID'] = order_dates['订单ID'].astype(str)
                order_agg['订单ID'] = order_agg['订单ID'].astype(str)
                order_agg = order_agg.merge(order_dates, on='订单ID', how='left')
            
            # 获取基准日期数据
            base_hourly_data = get_hourly_trend_data(order_agg, date=base_date)
            if 'error' in base_hourly_data:
                return html.Div(base_hourly_data['error'], className="text-center text-danger py-3")
            
            hours = base_hourly_data.get('hours', [])
            base_aov = base_hourly_data.get('aov_values', [])
            
            # 过滤0值
            valid_base = [(h, v) for h, v in zip(hours, base_aov) if v > 0]
            if not valid_base:
                return html.Div(f"{base_date} 无有效数据", className="text-center text-muted py-3")
            
            filtered_hours = [item[0] for item in valid_base]
            filtered_base_aov = [item[1] for item in valid_base]
            
            # 构建series
            series = [{
                'name': f'{base_date}',
                'type': 'line',
                'data': filtered_base_aov,
                'smooth': True,
                'symbol': 'circle',
                'symbolSize': 6,
                'lineStyle': {'width': 2, 'color': '#4CAF50'},
                'itemStyle': {'color': '#4CAF50'},
                'areaStyle': {
                    'color': {
                        'type': 'linear',
                        'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                        'colorStops': [
                            {'offset': 0, 'color': 'rgba(76, 175, 80, 0.3)'},
                            {'offset': 1, 'color': 'rgba(76, 175, 80, 0.05)'}
                        ]
                    }
                }
            }]
            
            title_text = f'📈 {base_date} 时段客单价趋势'
            
            # 如果选择了对比日期，添加第二条线
            if compare_date:
                compare_hourly_data = get_hourly_trend_data(order_agg, date=compare_date)
                if 'error' not in compare_hourly_data:
                    compare_aov = compare_hourly_data.get('aov_values', [])
                    valid_compare = [(h, v) for h, v in zip(hours, compare_aov) if v > 0]
                    
                    if valid_compare:
                        filtered_compare_aov = [item[1] for item in valid_compare]
                        
                        series.append({
                            'name': f'{compare_date}',
                            'type': 'line',
                            'data': filtered_compare_aov,
                            'smooth': True,
                            'symbol': 'circle',
                            'symbolSize': 6,
                            'lineStyle': {'width': 2, 'color': '#FF9800'},
                            'itemStyle': {'color': '#FF9800'},
                            'areaStyle': {
                                'color': {
                                    'type': 'linear',
                                    'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                                    'colorStops': [
                                        {'offset': 0, 'color': 'rgba(255, 152, 0, 0.3)'},
                                        {'offset': 1, 'color': 'rgba(255, 152, 0, 0.05)'}
                                    ]
                                }
                            }
                        })
                        
                        title_text = f'📈 {base_date} vs {compare_date} 时段客单价对比'
            
            # 构建图表配置
            chart_option = {
                'title': {
                    'text': title_text,
                    'left': 'center',
                    'textStyle': {'fontSize': 16, 'fontWeight': 'bold'}
                },
                'tooltip': {
                    'trigger': 'axis',
                    'axisPointer': {'type': 'cross'}
                },
                'legend': {
                    'data': [s['name'] for s in series],
                    'top': '35px',
                    'left': 'center'
                },
                'grid': {'left': '10%', 'right': '5%', 'top': '25%', 'bottom': '15%', 'containLabel': True},
                'xAxis': {
                    'type': 'category',
                    'data': filtered_hours,
                    'axisLabel': {'fontSize': 11, 'rotate': 45},
                    'boundaryGap': False
                },
                'yAxis': {
                    'type': 'value',
                    'name': '客单价(¥)',
                    'axisLabel': {'formatter': '¥{value}'},
                    'scale': True
                },
                'series': series
            }
            
            return DashECharts(
                option=chart_option,
                style={'height': '350px', 'width': '100%'}
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return html.Div(f"图表更新失败: {str(e)}", className="text-center text-danger py-3")
    
    # 对比模式：更新时段对比统计
    @app.callback(
        Output('period-compare-container', 'children'),
        Input('compare-date-selector', 'value'),
        State('current-drill-down-date', 'data'),
        prevent_initial_call=True
    )
    def update_period_comparison(compare_date, base_date):
        """当选择对比日期时,显示时段对比统计"""
        from datetime import datetime
        try:
            if not compare_date:
                return []  # 清空对比容器
            
            if not base_date:
                print(f"[DEBUG] base_date为空,返回错误")
                return html.Div("基准日期丢失", className="text-center text-danger py-3")
            
            # 获取全局数据（使用视图）
            GLOBAL_DATA = get_real_global_data()
            if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                return html.Div("全局数据未加载", className="text-center text-danger py-3")
            
            # 准备数据（使用视图，仅在筛选时复制）
            df = GLOBAL_DATA
            
            # 确定日期字段（兼容'日期'和'下单时间'）
            date_col = '日期' if '日期' in df.columns else '下单时间'
            if date_col not in df.columns:
                return html.Div("数据缺少日期字段", className="text-center text-danger py-3")
            
            # 确保日期字段是datetime格式，并提取小时
            df['日期_date'] = pd.to_datetime(df[date_col]).dt.date
            df['小时'] = pd.to_datetime(df[date_col]).dt.hour
            
            # 将日期字符串转换为date对象
            base_date_obj = datetime.strptime(base_date, '%Y-%m-%d').date()
            compare_date_obj = datetime.strptime(compare_date, '%Y-%m-%d').date()
            
            # 过滤两个日期的数据（使用视图，减少内存）
            df_base = df[df['日期_date'] == base_date_obj]
            df_compare = df[df['日期_date'] == compare_date_obj]
            
            if df_base.empty:
                return html.Div(f"{base_date} 无数据", className="text-center text-warning py-3")
            
            if df_compare.empty:
                return html.Div(f"{compare_date} 无数据,无法对比", className="text-center text-warning py-3")
            
            # 计算基准日期的小时统计
            base_hourly_stats = df_base.groupby('小时').agg({
                '订单ID': 'nunique',
                '实收价格': 'sum'
            }).reset_index()
            base_hourly_stats.columns = ['小时', '订单数', '销售额']
            base_hourly_stats['客单价'] = base_hourly_stats['销售额'] / base_hourly_stats['订单数']
            
            # 计算对比日期的小时统计
            compare_hourly_stats = df_compare.groupby('小时').agg({
                '订单ID': 'nunique',
                '实收价格': 'sum'
            }).reset_index()
            compare_hourly_stats.columns = ['小时', '订单数', '销售额']
            compare_hourly_stats['客单价'] = compare_hourly_stats['销售额'] / compare_hourly_stats['订单数']
            
            # 定义时段
            time_periods = [
                {'name': '早餐', 'range': '6-9时', 'hours': [6, 7, 8, 9], 'icon': 'sun'},
                {'name': '午餐', 'range': '11-14时', 'hours': [11, 12, 13, 14], 'icon': 'utensils'},
                {'name': '下午', 'range': '14-18时', 'hours': [14, 15, 16, 17, 18], 'icon': 'coffee'},
                {'name': '晚餐', 'range': '18-21时', 'hours': [18, 19, 20, 21], 'icon': 'moon'},
                {'name': '夜宵', 'range': '21-24时', 'hours': [21, 22, 23], 'icon': 'star'}
            ]
            
            period_comparisons = []
            for period in time_periods:
                # 基准日期时段统计
                base_period_data = base_hourly_stats[base_hourly_stats['小时'].isin(period['hours'])]
                if not base_period_data.empty:
                    base_aov = base_period_data['销售额'].sum() / base_period_data['订单数'].sum()
                    base_orders = base_period_data['订单数'].sum()
                else:
                    base_aov = 0
                    base_orders = 0
                
                # 对比日期时段统计
                compare_period_data = compare_hourly_stats[compare_hourly_stats['小时'].isin(period['hours'])]
                if not compare_period_data.empty:
                    compare_aov = compare_period_data['销售额'].sum() / compare_period_data['订单数'].sum()
                    compare_orders = compare_period_data['订单数'].sum()
                else:
                    compare_aov = 0
                    compare_orders = 0
                
                # 计算变化率
                aov_change = ((base_aov - compare_aov) / compare_aov * 100) if compare_aov > 0 else 0
                orders_change = ((base_orders - compare_orders) / compare_orders * 100) if compare_orders > 0 else 0
                
                period_comparisons.append({
                    'name': period['name'],
                    'range': period['range'],
                    'icon': period['icon'],
                    'base_aov': base_aov,
                    'base_orders': base_orders,
                    'compare_aov': compare_aov,
                    'compare_orders': compare_orders,
                    'aov_change': aov_change,
                    'orders_change': orders_change
                })
            
            # 生成对比显示
            return html.Div([
                html.H6([
                    html.I(className="fas fa-clock me-2"),
                    "时段统计对比"
                ], className="mt-3 mb-3"),
                html.Div([
                    html.Div([
                        html.I(className=f"fas fa-{stat['icon']} me-2 text-primary"),
                        html.Strong(f"{stat['name']} ", className="me-2"),
                        html.Span(f"({stat['range']})", className="text-muted small me-3"),
                        html.Br(),
                        html.Div([
                            html.Span(f"{base_date}: ¥{stat['base_aov']:.2f} ({int(stat['base_orders'])}单)", 
                                     className="badge bg-success me-2"),
                            html.Span(f"{compare_date}: ¥{stat['compare_aov']:.2f} ({int(stat['compare_orders'])}单)", 
                                     className="badge bg-warning me-2"),
                            html.Span(
                                f"{'↑' if stat['aov_change'] > 0 else '↓'} {abs(stat['aov_change']):.1f}%",
                                className=f"badge {'bg-danger' if stat['aov_change'] < 0 else 'bg-info'}"
                            )
                        ], className="mt-1")
                    ], className="mb-3")
                    for stat in period_comparisons
                ])
            ], className="p-3 bg-light rounded")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return html.Div(f"时段对比失败: {str(e)}", className="text-center text-danger py-3")
    
    # 对比模式：更新时段统计(删除这个旧函数)
    @app.callback(
        Output('period-stats-container', 'children', allow_duplicate=True) if 'period-stats-container' in app.callback_map else Output('dummy-output-for-old-callback', 'children'),
        Input('compare-date-selector', 'value'),
        State('current-drill-down-date', 'data'),
        prevent_initial_call=True
    )
    def update_hourly_trend_with_comparison_old(compare_date, base_date):
        """当选择对比日期时，更新趋势图为双折线"""
        from datetime import datetime, timedelta
        try:
            if not compare_date or not base_date:
                raise PreventUpdate
            
            # 获取全局数据
            GLOBAL_DATA = get_real_global_data()
            if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                return html.Div("数据未加载", className="text-center text-muted py-3")
            
            df = GLOBAL_DATA  # 直接引用，不复制
            
            # 确保有下单时间列
            if '下单时间' not in df.columns:
                return html.Div("缺少下单时间列", className="text-center text-danger py-3")
            
            # 转换下单时间为datetime并提取日期和小时
            df['\u4e0b\u5355\u65f6\u95f4'] = pd.to_datetime(df['下单时间'])
            df['日期'] = df['下单时间'].dt.date
            df['小时'] = df['下单时间'].dt.hour
            
            # 转换日期字符串为date对象
            try:
                base_date_obj = datetime.strptime(base_date, '%Y-%m-%d').date()
                compare_date_obj = datetime.strptime(compare_date, '%Y-%m-%d').date()
            except Exception as e:
                return html.Div(f"日期格式错误: {str(e)}", className="text-center text-danger py-3")
            
            # 过滤两个日期的数据
            df_base = df[df['日期'] == base_date_obj]  # 移除.copy()
            df_compare = df[df['日期'] == compare_date_obj]  # 移除.copy()
            
            if df_base.empty:
                return html.Div(f"{base_date} 无数据", className="text-center text-warning py-3")
            
            if df_compare.empty:
                return html.Div(f"{compare_date} 无数据，无法对比", className="text-center text-warning py-3")
            
            # 计算基准日期的小时客单价
            base_hourly_stats = df_base.groupby('小时').agg({
                '订单ID': 'nunique',
                '实收价格': 'sum'
            }).reset_index()
            base_hourly_stats.columns = ['小时', '订单数', '销售额']
            base_hourly_stats['客单价'] = base_hourly_stats['销售额'] / base_hourly_stats['订单数']
            
            # 计算对比日期的小时客单价
            compare_hourly_stats = df_compare.groupby('小时').agg({
                '订单ID': 'nunique',
                '实收价格': 'sum'
            }).reset_index()
            compare_hourly_stats.columns = ['小时', '订单数', '销售额']
            compare_hourly_stats['客单价'] = compare_hourly_stats['销售额'] / compare_hourly_stats['订单数']
            
            # 生成24小时的完整数据
            hours = list(range(24))
            base_aov_by_hour = []
            compare_aov_by_hour = []
            
            for h in hours:
                base_val = base_hourly_stats[base_hourly_stats['小时'] == h]['客单价'].values
                base_aov_by_hour.append(round(float(base_val[0]), 2) if len(base_val) > 0 else 0)
                
                compare_val = compare_hourly_stats[compare_hourly_stats['小时'] == h]['客单价'].values
                compare_aov_by_hour.append(round(float(compare_val[0]), 2) if len(compare_val) > 0 else 0)
            
            # 生成对比图表配置
            compare_option = {
                'title': {
                    'text': f'24小时客单价对比',
                    'left': 'center',
                    'top': 10,
                    'textStyle': {'fontSize': 16, 'fontWeight': 'bold'}
                },
                'tooltip': {
                    'trigger': 'axis',
                    'axisPointer': {'type': 'cross'}
                },
                'legend': {
                    'data': [base_date, compare_date],
                    'top': 45,
                    'left': 'center',
                    'itemGap': 20,
                    'textStyle': {'fontSize': 12}
                },
                'grid': {'left': '8%', 'right': '8%', 'top': '22%', 'bottom': '15%'},
                'xAxis': {
                    'type': 'category',
                    'data': [f'{h}时' for h in hours],
                    'axisLabel': {'fontSize': 11, 'rotate': 0}
                },
                'yAxis': {
                    'type': 'value',
                    'name': '客单价(¥)',
                    'axisLabel': {'formatter': '{value}'}
                },
                'series': [
                    {
                        'name': base_date,
                        'type': 'line',
                        'data': base_aov_by_hour,
                        'smooth': True,
                        'symbol': 'circle',
                        'symbolSize': 6,
                        'lineStyle': {'width': 2.5, 'color': '#4CAF50'},
                        'itemStyle': {'color': '#4CAF50'},
                        'areaStyle': {
                            'color': {
                                'type': 'linear',
                                'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                                'colorStops': [
                                    {'offset': 0, 'color': 'rgba(76, 175, 80, 0.2)'},
                                    {'offset': 1, 'color': 'rgba(76, 175, 80, 0.02)'}
                                ]
                            }
                        },
                        'z': 1  # 层级，确保在下层
                    },
                    {
                        'name': compare_date,
                        'type': 'line',
                        'data': compare_aov_by_hour,
                        'smooth': True,
                        'symbol': 'diamond',
                        'symbolSize': 7,
                        'lineStyle': {'width': 2.5, 'color': '#FF9800', 'type': 'dashed'},
                        'itemStyle': {'color': '#FF9800', 'borderWidth': 2, 'borderColor': '#fff'},
                        'z': 2  # 层级，确保在上层，避免被基准线的填充遮挡
                    }
                ]
            }
            
            return DashECharts(
                option=compare_option,
                style={'height': '350px', 'width': '100%'}
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return html.Div(f"对比图表生成失败: {str(e)}", className="text-center text-danger py-3")
    
    # 对比模式：更新时段统计（显示变化百分比）
    @app.callback(
        Output('period-stats-container', 'children'),
        Input('compare-date-selector', 'value'),
        State('current-drill-down-date', 'data'),
        prevent_initial_call=True
    )
    def update_period_stats_with_comparison(compare_date, base_date):
        """当选择对比日期时，更新时段统计显示变化百分比"""
        from datetime import datetime, timedelta
        try:
            if not compare_date or not base_date:
                raise PreventUpdate
            
            # 获取全局数据
            GLOBAL_DATA = get_real_global_data()
            if GLOBAL_DATA is None or GLOBAL_DATA.empty:
                return html.Div("数据未加载", className="text-center text-muted py-3")
            
            df = GLOBAL_DATA  # 直接引用
            
            # 确保有下单时间列
            if '下单时间' not in df.columns:
                return html.Div("缺少下单时间列", className="text-center text-danger py-3")
            
            # 转换下单时间为datetime并提取日期和小时
            df['下单时间'] = pd.to_datetime(df['下单时间'])
            df['日期'] = df['下单时间'].dt.date
            df['小时'] = df['下单时间'].dt.hour
            
            # 转换日期字符串为date对象
            try:
                base_date_obj = datetime.strptime(base_date, '%Y-%m-%d').date()
                compare_date_obj = datetime.strptime(compare_date, '%Y-%m-%d').date()
            except Exception as e:
                return html.Div(f"日期格式错误: {str(e)}", className="text-center text-danger py-3")
            
            # 过滤两个日期的数据（筛选不需要copy，groupby会创建新对象）
            df_base = df[df['日期'] == base_date_obj]
            df_compare = df[df['日期'] == compare_date_obj]
            
            if df_base.empty:
                return html.Div(f"{base_date} 无数据", className="text-center text-warning py-3")
            
            if df_compare.empty:
                return html.Div(f"{compare_date} 无数据，无法对比", className="text-center text-warning py-3")
            
            # 计算基准日期的小时统计（groupby会返回新DataFrame，无需copy）
            base_hourly_stats = df_base.groupby('小时').agg({
                '订单ID': 'nunique',
                '实收价格': 'sum'
            }).reset_index()
            base_hourly_stats.columns = ['小时', '订单数', '销售额']
            base_hourly_stats['客单价'] = base_hourly_stats['销售额'] / base_hourly_stats['订单数']
            
            # 计算对比日期的小时统计
            compare_hourly_stats = df_compare.groupby('小时').agg({
                '订单ID': 'nunique',
                '实收价格': 'sum'
            }).reset_index()
            compare_hourly_stats.columns = ['小时', '订单数', '销售额']
            compare_hourly_stats['客单价'] = compare_hourly_stats['销售额'] / compare_hourly_stats['订单数']
            
            # 定义时段
            time_periods = [
                {'name': '早餐', 'range': '6-9时', 'hours': [6, 7, 8, 9], 'icon': 'sun'},
                {'name': '午餐', 'range': '11-14时', 'hours': [11, 12, 13, 14], 'icon': 'utensils'},
                {'name': '下午', 'range': '14-18时', 'hours': [14, 15, 16, 17, 18], 'icon': 'coffee'},
                {'name': '晚餐', 'range': '18-21时', 'hours': [18, 19, 20, 21], 'icon': 'moon'},
                {'name': '夜宵', 'range': '21-24时', 'hours': [21, 22, 23], 'icon': 'star'}
            ]
            
            period_comparisons = []
            for period in time_periods:
                # 基准日期时段统计
                base_period_data = base_hourly_stats[base_hourly_stats['小时'].isin(period['hours'])]
                if not base_period_data.empty:
                    base_aov = base_period_data['销售额'].sum() / base_period_data['订单数'].sum()
                    base_orders = base_period_data['订单数'].sum()
                else:
                    base_aov = 0
                    base_orders = 0
                
                # 对比日期时段统计
                compare_period_data = compare_hourly_stats[compare_hourly_stats['小时'].isin(period['hours'])]
                if not compare_period_data.empty:
                    compare_aov = compare_period_data['销售额'].sum() / compare_period_data['订单数'].sum()
                    compare_orders = compare_period_data['订单数'].sum()
                else:
                    compare_aov = 0
                    compare_orders = 0
                
                # 计算变化率
                aov_change = ((base_aov - compare_aov) / compare_aov * 100) if compare_aov > 0 else 0
                orders_change = ((base_orders - compare_orders) / compare_orders * 100) if compare_orders > 0 else 0
                
                period_comparisons.append({
                    'name': period['name'],
                    'range': period['range'],
                    'icon': period['icon'],
                    'base_aov': base_aov,
                    'base_orders': base_orders,
                    'compare_aov': compare_aov,
                    'compare_orders': compare_orders,
                    'aov_change': aov_change,
                    'orders_change': orders_change
                })
            
            # 生成对比显示
            return html.Div([
                html.H6([
                    html.I(className="fas fa-clock me-2"),
                    "时段统计对比"
                ], className="mt-4 mb-3"),
                html.Div([
                    html.Div([
                        html.I(className=f"fas fa-{stat['icon']} me-2 text-primary"),
                        html.Strong(f"{stat['name']} ", className="me-2"),
                        html.Span(f"({stat['range']})", className="text-muted small me-3"),
                        html.Br(),
                        html.Div([
                            html.Span(f"{base_date}: ¥{stat['base_aov']:.2f} ({int(stat['base_orders'])}单)", 
                                     className="badge bg-success me-2"),
                            html.Span(f"{compare_date}: ¥{stat['compare_aov']:.2f} ({int(stat['compare_orders'])}单)", 
                                     className="badge bg-warning me-2"),
                            html.Span(
                                f"{'↑' if stat['aov_change'] > 0 else '↓'} {abs(stat['aov_change']):.1f}%",
                                className=f"badge {'bg-danger' if stat['aov_change'] < 0 else 'bg-info'}"
                            )
                        ], className="mt-1")
                    ], className="mb-3")
                    for stat in period_comparisons
                ])
            ], className="p-3 bg-light rounded")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return html.Div(f"时段统计对比失败: {str(e)}", className="text-center text-danger py-3")
        return no_update

    print("✅ 今日必做回调函数已注册")


# ==================== 诊断详情表格UI函数 ====================


def create_date_filter_buttons(card_type: str, default_days: int = 1) -> html.Div:
    """
    创建日期筛选按钮组
    
    参数:
        card_type: 卡片类型（如 'overflow', 'delivery' 等）
        default_days: 默认选中的天数
    
    返回:
        包含按钮组的 html.Div
    """
    button_configs = [
        {'label': '全部', 'value': 0},
        {'label': '昨日', 'value': 1},
        {'label': '3日', 'value': 3},
        {'label': '7日', 'value': 7},
        {'label': '15日', 'value': 15},
    ]
    
    buttons = []
    for config in button_configs:
        is_active = config['value'] == default_days
        buttons.append(
            dbc.Button(
                config['label'],
                id={'type': 'date-filter-btn', 'card': card_type, 'days': config['value']},
                color="primary" if is_active else "outline-secondary",
                size="sm",
                className="me-1",
                n_clicks=0
            )
        )
    
    return html.Div([
        html.Span("📅 日期范围: ", className="me-2 small fw-bold"),
        html.Div(buttons, className="d-inline-flex")
    ], className="mb-3 d-flex align-items-center")


def create_trend_comparison_section(
    df: pd.DataFrame, 
    metric_type: str,
    title: str = "📈 趋势分析"
) -> html.Div:
    """
    创建趋势对比区组件 - 用于弹窗详情顶部
    
    V6.1 优化版：
    1. 展示全部日期数据（30天），不仅仅7天
    2. 添加金额维度：穿底亏损金额、配送费总额等
    3. 使用ECharts双Y轴，同时展示数量和金额
    
    Args:
        df: 原始数据
        metric_type: 'overflow'(穿底) | 'delivery'(高配送费) | 'price_abnormal'(价格异常) | 'high_profit'(高利润)
        title: 标题
    """
    if df is None or df.empty:
        return html.Div()
    
    try:
        # 确保日期列存在
        if '日期' not in df.columns:
            return html.Div()
        
        # 内存优化：不复制整个df，仅在需要修改时copy特定列
        # df = df.copy()  # 删除不必要的整体复制
        df['日期'] = pd.to_datetime(df['日期'])  # 直接修改，因为调用者传入的已经是视图或副本
        
        # 获取数据中所有唯一日期，按时间顺序排列
        all_dates = sorted(df['日期'].dt.date.unique())
        latest_date = all_dates[-1] if all_dates else None
        
        if not latest_date:
            return html.Div()
        
        # 根据指标类型计算每日数值和金额
        daily_counts = {}  # 数量
        daily_amounts = {}  # 金额
        
        for d in all_dates:
            day_df = df[df['日期'].dt.date == d]
            
            if metric_type == 'overflow':
                # 穿底：计算订单实际利润为负的订单数和亏损金额
                if '订单ID' in day_df.columns:
                    order_agg = day_df.groupby('订单ID').agg({
                        '利润额': 'sum',
                        '平台服务费': 'sum',
                        '物流配送费': 'first',
                        '企客后返': 'sum' if '企客后返' in day_df.columns else lambda x: 0
                    }).reset_index()
                    
                    if '企客后返' not in order_agg.columns:
                        order_agg['企客后返'] = 0
                    
                    order_agg['订单实际利润'] = (
                        order_agg['利润额'] 
                        - order_agg['平台服务费'] 
                        - order_agg['物流配送费'] 
                        + order_agg['企客后返'].fillna(0)
                    )
                    overflow_orders = order_agg[order_agg['订单实际利润'] < 0]
                    daily_counts[d] = len(overflow_orders)
                    daily_amounts[d] = abs(overflow_orders['订单实际利润'].sum())  # 亏损金额（正数）
                else:
                    daily_counts[d] = 0
                    daily_amounts[d] = 0
                    
            elif metric_type == 'delivery':
                # 高配送费：配送净成本 > 6元的订单数和配送费总额
                if '订单ID' in day_df.columns and '物流配送费' in day_df.columns:
                    order_df = day_df.groupby('订单ID').agg({
                        '物流配送费': 'first',
                        '用户支付配送费': 'first' if '用户支付配送费' in day_df.columns else lambda x: 0,
                        '配送费减免金额': 'first' if '配送费减免金额' in day_df.columns else lambda x: 0
                    }).reset_index()
                    
                    user_pay = order_df['用户支付配送费'].fillna(0) if '用户支付配送费' in order_df.columns else 0
                    delivery_discount = order_df['配送费减免金额'].fillna(0) if '配送费减免金额' in order_df.columns else 0
                    order_df['配送净成本'] = order_df['物流配送费'] - user_pay - delivery_discount
                    high_delivery = order_df[order_df['配送净成本'] > 6]
                    daily_counts[d] = len(high_delivery)
                    daily_amounts[d] = high_delivery['配送净成本'].sum()  # 配送费总额
                else:
                    daily_counts[d] = 0
                    daily_amounts[d] = 0
            
            elif metric_type == 'price_abnormal':
                # 价格异常：售价低于成本的商品数和损失金额
                if '实收价格' in day_df.columns and '商品采购成本' in day_df.columns:
                    sales_col = '月售' if '月售' in day_df.columns else '销量'
                    if sales_col in day_df.columns:
                        day_df = day_df.copy()
                        day_df['_单品成本'] = day_df['商品采购成本'] / day_df[sales_col].replace(0, 1)
                        day_df['_损失'] = (day_df['_单品成本'] - day_df['实收价格']).clip(lower=0) * day_df[sales_col]
                        abnormal = day_df[day_df['实收价格'] < day_df['_单品成本']]
                        daily_counts[d] = len(abnormal['商品名称'].unique()) if '商品名称' in abnormal.columns else len(abnormal)
                        daily_amounts[d] = abnormal['_损失'].sum()
                    else:
                        daily_counts[d] = 0
                        daily_amounts[d] = 0
                else:
                    daily_counts[d] = 0
                    daily_amounts[d] = 0
            
            elif metric_type == 'high_profit':
                # 高利润商品：利润额和商品数（使用店内码分组）
                if '利润额' in day_df.columns and '商品名称' in day_df.columns:
                    group_cols = get_product_group_columns(day_df, include_category=False)
                    product_profit = day_df.groupby(group_cols)['利润额'].sum()
                    high_profit = product_profit[product_profit > 0]
                    daily_counts[d] = len(high_profit)
                    daily_amounts[d] = high_profit.sum()  # 利润总额
                else:
                    daily_counts[d] = 0
                    daily_amounts[d] = 0
            
            else:
                # 其他类型默认处理
                daily_counts[d] = 0
                daily_amounts[d] = 0
        
        # 准备图表数据（使用全部日期）
        chart_dates = [d.strftime('%m-%d') for d in all_dates]
        chart_counts = [daily_counts.get(d, 0) for d in all_dates]
        chart_amounts = [round(daily_amounts.get(d, 0), 2) for d in all_dates]
        
        # 指标配置
        metric_config = {
            'overflow': {
                'count_label': '穿底单数',
                'amount_label': '亏损利润',
                'count_color': '#ef4444',
                'amount_color': '#f97316',
                'trend_bad': 'up'  # 上升是坏趋势
            },
            'delivery': {
                'count_label': '高配送费单数',
                'amount_label': '配送费总额',
                'count_color': '#f59e0b',
                'amount_color': '#eab308',
                'trend_bad': 'up'
            },
            'price_abnormal': {
                'count_label': '价格异常商品数',
                'amount_label': '预计损失',
                'count_color': '#8b5cf6',
                'amount_color': '#a855f7',
                'trend_bad': 'up'
            },
            'high_profit': {
                'count_label': '高利润商品数',
                'amount_label': '利润总额',
                'count_color': '#10b981',
                'amount_color': '#22c55e',
                'trend_bad': 'down'  # 下降是坏趋势
            }
        }
        
        config = metric_config.get(metric_type, metric_config['overflow'])
        
        # 计算趋势（昨日 vs 前日）- 注意：数据最新日期是"昨日"
        if len(chart_counts) >= 2:
            yesterday_count = chart_counts[-1]  # 最新日期是昨日
            day_before_count = chart_counts[-2]  # 前日
            yesterday_amount = chart_amounts[-1]
            day_before_amount = chart_amounts[-2]
            
            count_change = yesterday_count - day_before_count
            amount_change = yesterday_amount - day_before_amount
            
            # 判断趋势好坏
            if config['trend_bad'] == 'up':
                is_bad_trend = count_change > 0
            else:
                is_bad_trend = count_change < 0
        else:
            yesterday_count = chart_counts[-1] if chart_counts else 0
            yesterday_amount = chart_amounts[-1] if chart_amounts else 0
            count_change = 0
            amount_change = 0
            is_bad_trend = False
        
        # 趋势文字（较前日）
        if count_change > 0:
            trend_text = f"较前日 +{count_change}"
            trend_icon = "📈"
        elif count_change < 0:
            trend_text = f"较前日 {count_change}"
            trend_icon = "📉"
        else:
            trend_text = "较前日持平"
            trend_icon = "➡️"
        
        trend_color = "danger" if is_bad_trend else "success"
        
        # 计算统计数据
        total_days = len(all_dates)
        total_count = sum(chart_counts)
        total_amount = sum(chart_amounts)
        avg_count = total_count / total_days if total_days else 0
        avg_amount = total_amount / total_days if total_days else 0
        
        # ECharts双Y轴配置（默认展示全部日期）
        chart_option = {
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {'type': 'cross'}
            },
            'legend': {
                'data': [config['count_label'], config['amount_label']],
                'top': 5,
                'textStyle': {'fontSize': 12}
            },
            'grid': {'left': '10%', 'right': '10%', 'top': '18%', 'bottom': '20%'},
            'xAxis': {
                'type': 'category',
                'data': chart_dates,
                'axisLabel': {'fontSize': 10, 'rotate': 45, 'interval': 0}
            },
            'yAxis': [
                {
                    'type': 'value',
                    'name': config['count_label'],
                    'position': 'left',
                    'minInterval': 1,
                    'axisLabel': {'fontSize': 10},
                    'nameTextStyle': {'fontSize': 10}
                },
                {
                    'type': 'value',
                    'name': config['amount_label'],
                    'position': 'right',
                    'axisLabel': {'fontSize': 10, 'formatter': '¥{value}'},
                    'nameTextStyle': {'fontSize': 10}
                }
            ],
            'series': [
                {
                    'name': config['count_label'],
                    'type': 'bar',
                    'yAxisIndex': 0,
                    'data': chart_counts,
                    'itemStyle': {'color': config['count_color'], 'borderRadius': [2, 2, 0, 0]},
                    'barMaxWidth': 20
                },
                {
                    'name': config['amount_label'],
                    'type': 'line',
                    'yAxisIndex': 1,
                    'data': chart_amounts,
                    'smooth': True,
                    'symbol': 'circle',
                    'symbolSize': 6,
                    'lineStyle': {'color': config['amount_color'], 'width': 2},
                    'itemStyle': {'color': config['amount_color']}
                }
            ]
        }
        
        return html.Div([
            # 趋势判断（昨日数据）
            dbc.Alert([
                html.Span(f"{trend_icon} 昨日{config['count_label']}: ", className="fw-bold"),
                html.Span(f"{yesterday_count}个", className="fw-bold text-danger me-2"),
                html.Span(f"({trend_text})", className="small"),
                html.Span(" | ", className="mx-2"),
                html.Span(f"昨日{config['amount_label']}: ", className="fw-bold"),
                html.Span(f"¥{yesterday_amount:,.2f}", className="fw-bold", style={'color': config['amount_color']}),
            ], color=trend_color, className="mb-2 py-2"),
            
            # 趋势图（支持拖拽缩放查看全部30天）
            html.Div([
                DashECharts(option=chart_option, style={'height': '280px', 'width': '100%'})
            ], className="mb-2"),
            
            # 汇总统计
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Small(f"{total_days}日累计{config['count_label']}", className="text-muted d-block"),
                        html.Span(f"{total_count}个", className="fw-bold"),
                    ], className="text-center")
                ], width=3),
                dbc.Col([
                    html.Div([
                        html.Small(f"日均{config['count_label']}", className="text-muted d-block"),
                        html.Span(f"{avg_count:.1f}个", className="fw-bold"),
                    ], className="text-center")
                ], width=3),
                dbc.Col([
                    html.Div([
                        html.Small(f"{total_days}日累计{config['amount_label']}", className="text-muted d-block"),
                        html.Span(f"¥{total_amount:,.2f}", className="fw-bold", style={'color': config['amount_color']}),
                    ], className="text-center")
                ], width=3),
                dbc.Col([
                    html.Div([
                        html.Small(f"日均{config['amount_label']}", className="text-muted d-block"),
                        html.Span(f"¥{avg_amount:,.2f}", className="fw-bold"),
                    ], className="text-center")
                ], width=3),
            ], className="py-2 bg-light rounded"),
        ], className="mb-3 p-3 bg-white rounded border")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div(f"趋势分析加载失败: {str(e)}", className="text-muted small")


def create_simple_trend_section(
    df: pd.DataFrame, 
    metric_type: str
) -> html.Div:
    """
    创建简化趋势区组件 - 用于流量下滑、利润率下滑、爆款商品等
    
    仅展示每日商品数和总金额趋势
    
    Args:
        df: 原始数据
        metric_type: 'traffic'(流量下滑) | 'profit_drop'(利润率下滑) | 'hot'(爆款商品)
    """
    if df is None or df.empty:
        return html.Div()
    
    try:
        if '日期' not in df.columns:
            return html.Div()
        
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        
        # 获取数据中所有唯一日期，按时间顺序排列
        all_dates = sorted(df['日期'].dt.date.unique())
        
        if not all_dates:
            return html.Div()
        
        daily_counts = {}
        daily_amounts = {}
        
        for d in all_dates:
            day_df = df[df['日期'].dt.date == d]
            
            if metric_type == 'traffic':
                # 流量下滑：统计日销量和日销售额
                if '商品名称' in day_df.columns:
                    sales_col = '销量' if '销量' in day_df.columns else '月售'
                    if sales_col in day_df.columns:
                        daily_counts[d] = day_df[sales_col].sum()
                        # 计算销售额：优先使用已有的销售额字段，否则用 实收价格*销量
                        if '销售额' in day_df.columns and day_df['销售额'].sum() > 0:
                            daily_amounts[d] = day_df['销售额'].sum()
                        elif '实收价格' in day_df.columns:
                            daily_amounts[d] = (day_df['实收价格'].fillna(0) * day_df[sales_col].fillna(0)).sum()
                        elif '商品实售价' in day_df.columns:
                            daily_amounts[d] = (day_df['商品实售价'].fillna(0) * day_df[sales_col].fillna(0)).sum()
                        else:
                            daily_amounts[d] = 0
                        # 计算利润额
                        if '利润额' in day_df.columns:
                            if 'daily_profits' not in dir():
                                daily_profits = {}
                            daily_profits[d] = day_df['利润额'].sum()
                    else:
                        daily_counts[d] = 0
                        daily_amounts[d] = 0
                else:
                    daily_counts[d] = 0
                    daily_amounts[d] = 0
                    
            elif metric_type == 'profit_drop':
                # 利润率下滑：统计日利润额
                if '利润额' in day_df.columns:
                    daily_counts[d] = len(day_df['商品名称'].unique()) if '商品名称' in day_df.columns else len(day_df)
                    daily_amounts[d] = day_df['利润额'].sum()
                else:
                    daily_counts[d] = 0
                    daily_amounts[d] = 0
                    
            elif metric_type == 'hot':
                # 爆款商品：统计日销量和销售额（需要计算销售额）
                sales_col = '销量' if '销量' in day_df.columns else '月售'
                if sales_col in day_df.columns:
                    daily_counts[d] = day_df[sales_col].sum()
                    
                    # 计算销售额：优先使用已有的销售额字段，否则用 实收价格*销量
                    if '销售额' in day_df.columns:
                        daily_amounts[d] = day_df['销售额'].sum()
                    elif '实收价格' in day_df.columns:
                        daily_amounts[d] = (day_df['实收价格'].fillna(0) * day_df[sales_col].fillna(0)).sum()
                    elif '商品实售价' in day_df.columns:
                        daily_amounts[d] = day_df['商品实售价'].sum()
                    else:
                        daily_amounts[d] = 0
                    
                    # 计算利润额
                    if '利润额' in day_df.columns:
                        if 'daily_profits' not in dir():
                            daily_profits = {}
                        daily_profits[d] = day_df['利润额'].sum()
                else:
                    daily_counts[d] = 0
                    daily_amounts[d] = 0
        
        # 准备图表数据
        chart_dates = [d.strftime('%m-%d') for d in all_dates]
        chart_counts = [daily_counts.get(d, 0) for d in all_dates]
        chart_amounts = [round(daily_amounts.get(d, 0), 2) for d in all_dates]
        
        # 流量下滑和爆款商品都需要利润额曲线
        chart_profits = []
        if metric_type in ['hot', 'traffic']:
            try:
                # 重新计算每日利润额
                for d in all_dates:
                    day_df = df[df['日期'].dt.date == d]
                    if '利润额' in day_df.columns:
                        chart_profits.append(round(day_df['利润额'].sum(), 2))
                    else:
                        chart_profits.append(0)
            except:
                chart_profits = [0] * len(all_dates)
        
        total_days = len(all_dates)
        
        # 指标配置
        metric_config = {
            'traffic': {
                'count_label': '日销量',
                'amount_label': '日销售额',
                'count_color': '#3b82f6',
                'amount_color': '#06b6d4',
                'trend_bad': 'down'  # 下降是坏趋势
            },
            'profit_drop': {
                'count_label': '商品数',
                'amount_label': '日利润额',
                'count_color': '#f59e0b',
                'amount_color': '#22c55e',
                'trend_bad': 'down'
            },
            'hot': {
                'count_label': '日销量',
                'amount_label': '日销售额',
                'count_color': '#ef4444',
                'amount_color': '#f97316',
                'trend_bad': 'down'
            }
        }
        
        config = metric_config.get(metric_type, metric_config['traffic'])
        
        # 计算趋势（昨日 vs 前日）
        if len(chart_counts) >= 2:
            yesterday_count = chart_counts[-1]  # 最新日期是昨日
            day_before_count = chart_counts[-2]
            count_change = yesterday_count - day_before_count
            
            if config['trend_bad'] == 'down':
                is_bad_trend = count_change < 0
            else:
                is_bad_trend = count_change > 0
        else:
            yesterday_count = chart_counts[-1] if chart_counts else 0
            count_change = 0
            is_bad_trend = False
        
        yesterday_amount = chart_amounts[-1] if chart_amounts else 0
        
        # 趋势文字（较前日）
        if count_change > 0:
            trend_text = f"+{count_change:,.0f}"
            trend_icon = "📈"
        elif count_change < 0:
            trend_text = f"{count_change:,.0f}"
            trend_icon = "📉"
        else:
            trend_text = "持平"
            trend_icon = "➡️"
        
        trend_color = "danger" if is_bad_trend else "success"
        
        # ECharts图表配置
        # 爆款商品和流量下滑：增加利润额曲线
        if metric_type in ['hot', 'traffic'] and chart_profits:
            legend_data = [config['count_label'], config['amount_label'], '日利润额']
            chart_option = {
                'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'cross'}},
                'legend': {'data': legend_data, 'top': 5, 'textStyle': {'fontSize': 11}},
                'grid': {'left': '12%', 'right': '12%', 'top': '18%', 'bottom': '20%'},
                'xAxis': {'type': 'category', 'data': chart_dates, 'axisLabel': {'fontSize': 9, 'rotate': 45, 'interval': 0}},
                'yAxis': [
                    {'type': 'value', 'name': config['count_label'], 'position': 'left', 'axisLabel': {'fontSize': 9}, 'nameTextStyle': {'fontSize': 9}},
                    {'type': 'value', 'name': '金额', 'position': 'right', 'axisLabel': {'fontSize': 9}, 'nameTextStyle': {'fontSize': 9}}
                ],
                'series': [
                    {'name': config['count_label'], 'type': 'bar', 'yAxisIndex': 0, 'data': chart_counts,
                     'itemStyle': {'color': config['count_color'], 'borderRadius': [2, 2, 0, 0]}, 'barMaxWidth': 18},
                    {'name': config['amount_label'], 'type': 'line', 'yAxisIndex': 1, 'data': chart_amounts,
                     'smooth': True, 'symbol': 'circle', 'symbolSize': 5,
                     'lineStyle': {'color': config['amount_color'], 'width': 2}, 'itemStyle': {'color': config['amount_color']}},
                    {'name': '日利润额', 'type': 'line', 'yAxisIndex': 1, 'data': chart_profits,
                     'smooth': True, 'symbol': 'diamond', 'symbolSize': 6,
                     'lineStyle': {'color': '#22c55e', 'width': 2, 'type': 'dashed'}, 'itemStyle': {'color': '#22c55e'}}
                ]
            }
            # 昨日利润额
            yesterday_profit = chart_profits[-1] if chart_profits else 0
        else:
            # 默认配置（非爆款）
            chart_option = {
                'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'cross'}},
                'legend': {'data': [config['count_label'], config['amount_label']], 'top': 5, 'textStyle': {'fontSize': 11}},
                'grid': {'left': '10%', 'right': '10%', 'top': '16%', 'bottom': '20%'},
                'xAxis': {'type': 'category', 'data': chart_dates, 'axisLabel': {'fontSize': 9, 'rotate': 45, 'interval': 0}},
                'yAxis': [
                    {'type': 'value', 'name': config['count_label'], 'position': 'left', 'axisLabel': {'fontSize': 9}, 'nameTextStyle': {'fontSize': 9}},
                    {'type': 'value', 'name': config['amount_label'], 'position': 'right', 'axisLabel': {'fontSize': 9}, 'nameTextStyle': {'fontSize': 9}}
                ],
                'series': [
                    {'name': config['count_label'], 'type': 'bar', 'yAxisIndex': 0, 'data': chart_counts,
                     'itemStyle': {'color': config['count_color'], 'borderRadius': [2, 2, 0, 0]}, 'barMaxWidth': 18},
                    {'name': config['amount_label'], 'type': 'line', 'yAxisIndex': 1, 'data': chart_amounts,
                     'smooth': True, 'symbol': 'circle', 'symbolSize': 5,
                     'lineStyle': {'color': config['amount_color'], 'width': 2}, 'itemStyle': {'color': config['amount_color']}}
                ]
            }
            yesterday_profit = 0
        
        # 构建趋势提示
        if metric_type in ['hot', 'traffic'] and chart_profits:
            yesterday_profit = chart_profits[-1] if chart_profits else 0
            trend_alert = dbc.Alert([
                html.Span(f"{trend_icon} 昨日{config['count_label']}: ", className="small fw-bold"),
                html.Span(f"{yesterday_count:,.0f}", className="fw-bold", style={'color': config['count_color']}),
                html.Span(f" (较前日{trend_text})", className="small"),
                html.Span(" | ", className="mx-2"),
                html.Span(f"昨日销售额: ", className="small fw-bold"),
                html.Span(f"¥{yesterday_amount:,.2f}", className="fw-bold", style={'color': config['amount_color']}),
                html.Span(" | ", className="mx-2"),
                html.Span(f"昨日利润额: ", className="small fw-bold"),
                html.Span(f"¥{yesterday_profit:,.2f}", className="fw-bold", style={'color': '#22c55e'}),
            ], color=trend_color, className="mb-2 py-2")
        else:
            trend_alert = dbc.Alert([
                html.Span(f"{trend_icon} 昨日{config['count_label']}: ", className="small fw-bold"),
                html.Span(f"{yesterday_count:,.0f}", className="fw-bold", style={'color': config['count_color']}),
                html.Span(f" (较前日{trend_text})", className="small"),
                html.Span(" | ", className="mx-2"),
                html.Span(f"昨日{config['amount_label']}: ", className="small fw-bold"),
                html.Span(f"¥{yesterday_amount:,.2f}", className="fw-bold", style={'color': config['amount_color']}),
            ], color=trend_color, className="mb-2 py-2")
        
        return html.Div([
            trend_alert,
            html.Div([
                DashECharts(option=chart_option, style={'height': '280px', 'width': '100%'})
            ]),
        ], className="mb-3 p-2 bg-white rounded border")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return html.Div()


def create_overflow_detail_table(df: pd.DataFrame, days: int = 1) -> html.Div:
    """
    创建亏损订单详情表格（订单视图 + 商品视图）
    
    设计理念：
    - 订单视图：定位哪些订单穿底，用于财务分析
    - 商品视图：定位哪些商品导致穿底，用于业务动作
    
    参数：
        df: 原始数据
        days: 日期范围（1=昨日，3=近3天，7=近7天，15=近15天，0=全部）
    """
    order_data = get_overflow_orders(df, days=days)
    product_data = get_overflow_products(df, days=days)
    
    if order_data.empty and product_data.empty:
        return dbc.Alert("暂无穿底数据", color="info")
    
    # 计算穿底损失（负利润的绝对值之和）
    total_loss = abs(order_data['订单实际利润'].sum()) if not order_data.empty and '订单实际利润' in order_data.columns else 0
    order_count = len(order_data) if not order_data.empty else 0
    product_count = len(product_data) if not product_data.empty else 0
    
    # 日期范围描述
    days_label = {0: '全部', 1: '昨日', 3: '近3天', 7: '近7天', 15: '近15天'}.get(days, f'近{days}天')
    
    # 订单视图表格 - 添加点击下钻提示
    order_table = html.Div([
        # 下钻提示
        html.Div([
            html.Span("👆 ", style={'fontSize': '18px'}),
            html.Span("点击表格中任意一行，可查看该订单的", className="small"),
            html.Span(" 商品亏损明细 ", className="fw-bold text-primary", style={'textDecoration': 'underline'}),
        ], className="mb-2 p-2 bg-info bg-opacity-25 rounded d-flex align-items-center border border-info"),
        dash_table.DataTable(
            id='overflow-order-table',
            data=order_data.head(100).to_dict('records') if not order_data.empty else [],
            columns=[{'name': c, 'id': c, 'type': 'numeric', 'format': {'specifier': ',.2f'}} 
                     if c in ['销售额', '成本', '物流配送费', '平台服务费', '活动成本', '利润额', '订单实际利润'] 
                     else {'name': c, 'id': c} 
                     for c in order_data.columns] if not order_data.empty else [],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px', 'cursor': 'pointer'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'column_id': '订单实际利润'}, 'color': 'red', 'fontWeight': 'bold'},
                # 鼠标悬停效果
                {'if': {'state': 'active'}, 'backgroundColor': '#e3f2fd', 'border': '1px solid #2196F3'},
            ],
            page_size=15,
            sort_action='native',
            row_selectable=False,  # 不用多选，用active_cell
            cell_selectable=True,  # 允许选中单元格
        ),
        html.Div([
            html.Small([
                html.Strong("📌 定义提示："),
                f"穿底 = 卖一单亏一单（订单实际利润为负）；数据范围：{days_label}"
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
    
    # 商品视图表格 - 添加单品洞察提示
    product_table = html.Div([
        # 单品洞察提示
        html.Div([
            html.Span("👆 ", style={'fontSize': '18px'}),
            html.Span("点击表格中", className="small"),
            html.Span(" 商品名称 ", className="fw-bold text-primary", style={'textDecoration': 'underline'}),
            html.Span("可打开", className="small"),
            html.Span(" 单品洞察 ", className="fw-bold text-success"),
            html.Span("详情分析", className="small")
        ], className="mb-2 p-2 bg-warning bg-opacity-25 rounded d-flex align-items-center border border-warning"),
        dash_table.DataTable(
            id={'type': 'product-analysis-table', 'index': 'overflow-product'},
            data=product_data.head(50).to_dict('records') if not product_data.empty else [],
            columns=[
                {'name': c, 'id': c, 'type': 'numeric', 'format': {'specifier': ',.2f'}} 
                if c in ['商品原价', '商品实售价', '实收价格', '单品成本', '穿底贡献'] 
                else {'name': c, 'id': c, 'type': 'numeric', 'format': {'specifier': '.1f'}} 
                if c in ['定价毛利率', '实收毛利率']
                else {'name': c, 'id': c} 
                for c in product_data.columns if c != '订单ID'  # 隐藏订单ID列，太长影响展示
            ] if not product_data.empty else [],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'column_id': '穿底贡献', 'filter_query': '{穿底贡献} < 0'}, 'color': 'red', 'fontWeight': 'bold'},
                {'if': {'column_id': '实收毛利率', 'filter_query': '{实收毛利率} < 15'}, 'color': '#fd7e14'},
                # 商品名称列 - 可点击样式
                {'if': {'column_id': '商品名称'}, 'color': '#667eea', 'fontWeight': 'bold', 'cursor': 'pointer', 'textDecoration': 'underline'},
            ],
            cell_selectable=True,
            page_size=15,
            sort_action='native',
            tooltip_data=[
                {
                    '穿底订单数': {'value': f"订单ID: {row.get('订单ID', '')}", 'type': 'markdown'}
                } for row in product_data.head(50).to_dict('records')
            ] if not product_data.empty and '订单ID' in product_data.columns else None,
            tooltip_duration=None,
            tooltip_delay=0
        ),
        html.Div([
            html.Small("💡 处理建议：关注临期商品、爆品、神价品、重量加价配置", className="text-muted"),
        ], className="mt-2 p-2 bg-light rounded")
    ]) if not product_data.empty else dbc.Alert("暂无商品数据", color="secondary")
    
    # 生成趋势对比区
    trend_section = create_trend_comparison_section(df, 'overflow')
    
    return html.Div([
        # ========== 趋势对比区（顶部） ==========
        trend_section,
        
        # ========== 日期筛选按钮 ==========
        create_date_filter_buttons('overflow', default_days=days),
        
        # 顶部汇总
        html.Div([
            html.Span([
                html.I(className="bi bi-exclamation-triangle-fill me-2 text-danger"),
                f"{days_label}穿底：",
                html.Span(f"{order_count}单", className="fw-bold text-danger mx-1"),
                f"涉及 ",
                html.Span(f"{product_count}款商品", className="fw-bold text-danger mx-1"),
                f"，累计损失 ",
                html.Span(f"¥{total_loss:,.2f}", className="fw-bold text-danger")
            ])
        ], className="mb-3 p-2 bg-danger bg-opacity-10 rounded"),
        
        # 表格容器（用于日期筛选回调更新）
        html.Div(id='overflow-tables-container', children=[
            # Tab切换
            dbc.Tabs([
                dbc.Tab(product_table, label=f"📦 商品视图 ({product_count})", tab_id="product-view",
                       label_style={"fontWeight": "bold"}),
                dbc.Tab(order_table, label=f"📋 订单视图 ({order_count})", tab_id="order-view"),
            ], active_tab="product-view", className="mb-2"),
        ]),
        
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
        
        # ===== 图表1：亏损原因分布（饼图）=====
        # 分类逻辑更直观：
        # - 营销活动亏损：定价毛利率>=15%但实收毛利率<5%（促销折扣太大导致亏损）
        # - 商品定价过低：定价毛利率<15%（商品售价本身就接近或低于成本）
        # - 采购成本偏高：定价毛利率>=15%且实收毛利率>=5%（成本高导致利润不足）
        if not product_data.empty:
            # 分析亏损原因
            reasons = {'营销活动亏损': 0, '商品定价过低': 0, '采购成本偏高': 0}
            
            for _, row in product_data.iterrows():
                pricing_margin = row.get('定价毛利率', 0) or 0
                actual_margin = row.get('实收毛利率', 0) or 0
                loss = abs(row.get('穿底贡献', 0) or 0)
                
                if pricing_margin < 15:  # 定价毛利率低于15%，说明商品定价本身就低
                    reasons['商品定价过低'] += loss
                elif actual_margin < 5:  # 定价合理但实收毛利率很低，说明是活动折扣导致
                    reasons['营销活动亏损'] += loss
                else:  # 定价合理、折扣也不大，但还是亏损，说明成本偏高
                    reasons['采购成本偏高'] += loss
            
            pie_data = [{'name': k, 'value': round(v, 2)} for k, v in reasons.items() if v > 0]
            
            if pie_data:
                option1 = {
                    'title': {'text': '🔍 亏损原因分布', 'left': 'center', 'top': 5, 
                              'textStyle': {'fontSize': 14, 'fontWeight': 'bold'}},
                    'tooltip': {'trigger': 'item', 'formatter': '{b}: ¥{c} ({d}%)'},
                    'legend': {'orient': 'vertical', 'left': 10, 'top': 'middle', 
                               'textStyle': {'fontSize': 11}},
                    'series': [{
                        'type': 'pie',
                        'radius': ['35%', '65%'],
                        'center': ['60%', '55%'],
                        'data': pie_data,
                        'itemStyle': {'borderRadius': 8, 'borderColor': '#fff', 'borderWidth': 2},
                        'label': {'formatter': '{b}\n¥{c}', 'fontSize': 11},
                        'emphasis': {'itemStyle': {'shadowBlur': 10, 'shadowColor': 'rgba(0,0,0,0.3)'}},
                        # 颜色：营销活动=橙色，定价过低=红色，成本偏高=蓝色
                        'color': ['#FF9F43', '#EE5A5A', '#54A0FF']
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
                    # 渠道数据保留2位小数
                    channel_values = [round(v, 2) for v in channel_loss.values.tolist()[::-1]]
                    channel_names = channel_loss.index.tolist()[::-1]
                    option2 = {
                        'title': {'text': '📊 各渠道亏损金额', 'left': 'center', 'top': 5,
                                  'textStyle': {'fontSize': 14, 'fontWeight': 'bold'}},
                        'tooltip': {
                            'trigger': 'axis',
                            'axisPointer': {'type': 'shadow'},
                            'formatter': None  # 使用默认格式
                        },
                        'grid': {'left': '20%', 'right': '18%', 'top': '20%', 'bottom': '15%'},
                        'xAxis': {
                            'type': 'value', 
                            'axisLabel': {
                                'fontSize': 10,
                                'formatter': None  # 使用默认数字格式
                            }
                        },
                        'yAxis': {'type': 'category', 'data': channel_names,
                                  'axisLabel': {'fontSize': 11}},
                        'series': [{
                            'type': 'bar',
                            'data': channel_values,
                            'barWidth': '50%',
                            'itemStyle': {
                                'color': {'type': 'linear', 'x': 0, 'y': 0, 'x2': 1, 'y2': 0,
                                          'colorStops': [{'offset': 0, 'color': '#FF6B6B'},
                                                         {'offset': 1, 'color': '#EE5A5A'}]},
                                'borderRadius': [0, 6, 6, 0]
                            },
                            'label': {
                                'show': True, 
                                'position': 'right', 
                                'fontSize': 11,
                                'formatter': None  # 使用默认格式，显示数值
                            }
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
        
        # ===== 按渠道+商品聚合（使用店内码）=====
        group_cols = get_product_group_columns(overflow_items, include_category=False)
        if channel_col and channel_col in overflow_items.columns:
            group_cols = [channel_col] + group_cols  # 渠道放在最前面
        
        category_col = '一级分类名' if '一级分类名' in overflow_items.columns else '一级分类'
        category3_col = '三级分类名' if '三级分类名' in overflow_items.columns else '三级分类'
        
        agg_dict = {
            '穿底订单数': pd.NamedAgg(column=order_id_col, aggfunc='nunique'),
            '订单ID': pd.NamedAgg(column=order_id_col, aggfunc=lambda x: '\n'.join(x.astype(str).unique())),
            '穿底销量': pd.NamedAgg(column=sales_field, aggfunc='sum'),
            '商品原价': pd.NamedAgg(column='_商品原价', aggfunc='max'),      # 单价，取最大
            # 商品实售价和实收价格改为聚合后计算加权平均
            '_商品销售额': pd.NamedAgg(column='_商品实售价', aggfunc=lambda x: (x * overflow_items.loc[x.index, sales_field]).sum()),  # 销售额
            '_单品成本总额': pd.NamedAgg(column='单品成本', aggfunc='sum'),   # 总成本，需除以销量
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
        
        # 计算商品实售价和实收价格（加权平均）
        product_agg['商品实售价'] = np.where(
            product_agg['穿底销量'] > 0,
            product_agg['_商品销售额'] / product_agg['穿底销量'],
            0
        )
        product_agg['实收价格'] = product_agg['商品实售价']  # 在成本穿底分析中两者相同
        
        # 单品成本 = 总成本 / 销量
        product_agg['单品成本'] = np.where(
            product_agg['穿底销量'] > 0,
            product_agg['_单品成本总额'] / product_agg['穿底销量'],
            0
        )
        
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


def create_delivery_detail_table(df: pd.DataFrame, days: int = 1) -> html.Div:
    """创建高配送费订单详情表格（优化版）- 支持日期筛选"""
    data = get_high_delivery_orders(df, days=days)
    if data.empty:
        return dbc.Alert("暂无高配送费订单数据", color="info")
    
    # 计算配送溢价总额
    total_extra = data['配送溢价'].sum() if '配送溢价' in data.columns else 0
    
    # 生成趋势对比区
    trend_section = create_trend_comparison_section(df, 'delivery')
    
    # 日期范围描述
    days_label = {0: '全部', 1: '昨日', 3: '近3天', 7: '近7天', 15: '近15天'}.get(days, f'近{days}天')
    
    return html.Div([
        # ========== 趋势对比区（顶部） ==========
        trend_section,
        
        # ========== 日期筛选按钮 ==========
        create_date_filter_buttons('delivery', default_days=days),
        
        # 表格容器（用于日期筛选回调更新）
        html.Div(id='delivery-tables-container', children=[
            html.Div([
                html.Span([
                    html.I(className="bi bi-truck me-2 text-warning"),
                    f"{days_label}共 ",
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
        ]),
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
    """创建热销缺货商品详情表格 - 增加持续缺货分级"""
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
    
    # ========== 计算缺货分级（基于建议补货数量） ==========
    # 根据建议补货数量判断紧急程度
    urgent_products = []  # 紧急补货（建议补货数量大）
    normal_products = []  # 正常缺货
    
    try:
        if '商品名称' in data.columns:
            for _, row in data.iterrows():
                product_name = row.get('商品名称', '')
                suggest_qty = row.get('建议补货', 0) or 0
                
                # 根据建议补货数量判断紧急程度
                if suggest_qty >= 5:  # 建议补货>=5件，紧急
                    urgent_products.append(product_name)
                else:
                    normal_products.append(product_name)
    except Exception as e:
        print(f"[DEBUG] 缺货分级分析失败: {e}")
    
    # ========== 构建缺货分级区域（显示具体商品） ==========
    stockout_level_section = html.Div()
    total_stockout = len(data)
    
    # 始终显示分级区域
    if total_stockout > 0:
        level_sections = []
        
        # 紧急补货区域 - 显示具体商品
        if urgent_products:
            urgent_badges = [
                html.Span(f"{name[:8]}{'...' if len(name)>8 else ''}", 
                         className="badge bg-danger me-1 mb-1",
                         style={'fontSize': '12px'}) 
                for name in urgent_products[:10]  # 最多显示10个
            ]
            if len(urgent_products) > 10:
                urgent_badges.append(html.Span(f"等{len(urgent_products)}个", className="text-muted small"))
            
            level_sections.append(
                html.Div([
                    html.Div([
                        html.Span("🔴 ", style={'fontSize': '18px'}),
                        html.Span("紧急补货: ", className="fw-bold text-danger"),
                        html.Span(f"{len(urgent_products)}个", className="badge bg-danger me-2"),
                        html.Small("（建议补货≥5件）", className="text-muted")
                    ], className="mb-2"),
                    html.Div(urgent_badges, className="d-flex flex-wrap")
                ], className="mb-3")
            )
        
        # 正常缺货区域 - 显示具体商品
        if normal_products:
            normal_badges = [
                html.Span(f"{name[:8]}{'...' if len(name)>8 else ''}", 
                         className="badge bg-warning text-dark me-1 mb-1",
                         style={'fontSize': '12px'}) 
                for name in normal_products[:10]  # 最多显示10个
            ]
            if len(normal_products) > 10:
                normal_badges.append(html.Span(f"等{len(normal_products)}个", className="text-muted small"))
            
            level_sections.append(
                html.Div([
                    html.Div([
                        html.Span("🟡 ", style={'fontSize': '18px'}),
                        html.Span("正常缺货: ", className="fw-bold text-warning"),
                        html.Span(f"{len(normal_products)}个", className="badge bg-warning text-dark me-2"),
                        html.Small("（建议补货<5件）", className="text-muted")
                    ], className="mb-2"),
                    html.Div(normal_badges, className="d-flex flex-wrap")
                ], className="mb-2")
            )
        
        # 如果没有分级，给出总数提示
        if not level_sections:
            level_sections.append(
                html.Div([
                    html.Span("📦 ", style={'fontSize': '18px'}),
                    html.Span(f"共 {total_stockout} 个热销商品缺货", className="fw-bold text-danger"),
                ], className="mb-2")
            )
        
        stockout_level_section = html.Div([
            html.H6("📊 缺货分级诊断", className="mb-3"),
            html.Div(level_sections),
            html.Hr(className="my-2"),
            html.Small([
                "🔴 紧急补货：建议补货量大(≥5件)，需优先处理；",
                "🟡 正常缺货：建议补货量小(<5件)，正常补货即可"
            ], className="text-muted d-block")
        ], className="mb-3 p-3 bg-danger bg-opacity-10 rounded border border-danger")
    
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
    
    # 添加商品名称列的可点击样式
    style_data_conditional.append({
        'if': {'column_id': '商品名称'},
        'color': '#667eea',
        'fontWeight': 'bold',
        'cursor': 'pointer',
        'textDecoration': 'underline'
    })
    
    return html.Div([
        # ========== 缺货分级区域（顶部） ==========
        stockout_level_section,
        
        description,
        # 单品洞察提示
        html.Div([
            html.Span("👆 ", style={'fontSize': '18px'}),
            html.Span("点击表格中", className="small"),
            html.Span(" 商品名称 ", className="fw-bold text-primary", style={'textDecoration': 'underline'}),
            html.Span("可打开", className="small"),
            html.Span(" 单品洞察 ", className="fw-bold text-success"),
            html.Span("详情分析", className="small")
        ], className="mb-2 p-2 bg-warning bg-opacity-25 rounded d-flex align-items-center border border-warning"),
        dash_table.DataTable(
            id={'type': 'product-analysis-table', 'index': 'stockout'},
            data=data.head(50).to_dict('records'),
            columns=columns,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=style_data_conditional,
            cell_selectable=True,
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


def create_churn_detail_table(df: pd.DataFrame) -> html.Div:
    """创建客户流失预警详情表格 - 显示流失客户及原因分析"""
    try:
        # 获取商品主数据（需要JOIN库存信息）
        from database.connection import engine
        
        # 确保事务干净
        try:
            with engine.connect() as conn:
                products_df = pd.read_sql("SELECT product_name, stock FROM products", conn)
        except Exception as db_error:
            # 如果查询失败，尝试回滚并重试
            try:
                engine.dispose()
                with engine.connect() as conn:
                    products_df = pd.read_sql("SELECT product_name, stock FROM products", conn)
            except:
                raise db_error
        
        # 调用客户流失分析
        churn_result = get_customer_churn_warning(
            df, 
            products_df, 
            today=pd.Timestamp.now(),
            lookback_days=30,
            min_orders=2,
            no_order_days=7
        )
        
        if churn_result['summary']['total_churn'] == 0:
            return dbc.Alert("✅ 暂无流失客户，客户留存良好！", color="success")
        
        summary = churn_result['summary']
        details = churn_result['details']
        data_date = summary.get('data_date', '未知')
        
        # ========== 数据时点说明 ==========
        data_info = dbc.Alert([
            html.Div([
                html.H6([
                    html.I(className="fas fa-info-circle me-2"),
                    f"📅 数据时点: {data_date}"
                ], className="mb-2"),
                html.Div([
                    html.Strong("🔍 分析逻辑说明:"),
                    html.Ul([
                        html.Li([
                            html.Strong("缺货影响: "),
                            f"客户历史购买的商品在{data_date}的库存=0,推测客户可能因商品缺货而流失"
                        ]),
                        html.Li([
                            html.Strong("涨价影响: "),
                            "采用",
                            html.Strong("「同期对比」"),
                            "逻辑 - 对比客户购买期与近7天的价格差异(更科学),涨幅>10%判定为涨价影响"
                        ]),
                        html.Li([
                            html.Strong("下架影响: "),
                            "客户历史购买的商品已从商品库中移除(不再销售)"
                        ]),
                        html.Li([
                            html.Strong("成本分析: "),
                            "显示商品成本、毛利率和可让利空间,辅助制定精准召回策略"
                        ]),
                    ], className="mb-2", style={"fontSize": "13px"}),
                    html.Small([
                        html.I(className="fas fa-lightbulb me-1"),
                        "流失原因为推测性关联,用于制定精准召回策略"
                    ], className="text-muted fst-italic")
                ])
            ])
        ], color="info", className="mb-3")
        
        # ========== 流失原因汇总区域 ==========
        reason_section = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("🚫 缺货影响", className="text-danger mb-2"),
                        html.H3(f"{summary['out_of_stock']}", className="text-danger"),
                        html.Small("个客户购买的商品现已缺货", className="text-muted")
                    ])
                ], className="text-center border-danger")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("💰 涨价影响", className="text-warning mb-2"),
                        html.H3(f"{summary['price_increased']}", className="text-warning"),
                        html.Small("个客户购买的商品涨价>10%", className="text-muted")
                    ])
                ], className="text-center border-warning")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("❌ 下架影响", className="text-secondary mb-2"),
                        html.H3(f"{summary['delisted']}", className="text-secondary"),
                        html.Small("个客户购买的商品已下架", className="text-muted")
                    ])
                ], className="text-center border-secondary")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("❓ 其他原因", className="text-info mb-2"),
                        html.H3(f"{summary['unknown']}", className="text-info"),
                        html.Small("需进一步分析流失原因", className="text-muted")
                    ])
                ], className="text-center border-info")
            ], width=3),
        ], className="mb-4")
        
        # ========== AG Grid 使用指南 ==========
        filter_buttons = html.Div([
            dbc.Alert([
                html.H6([
                    html.I(className="fas fa-lightbulb me-2"),
                    "✨ 新功能: 智能表格升级 + 涨价分析可视化"
                ], className="alert-heading mb-2"),
                html.Div([
                    html.Strong("🎯 支持的新功能:"),
                    html.Ul([
                        html.Li([
                            html.I(className="fas fa-arrows-alt-h me-1"),
                            "拖动列边缘可调整列宽 - 自定义您的视图"
                        ]),
                        html.Li([
                            html.I(className="fas fa-thumbtack me-1"),
                            "\"客户地址\"列已固定在左侧 - 横向滚动时保持可见"
                        ]),
                        html.Li([
                            html.I(className="fas fa-chart-line me-1"),
                            html.Strong("涨价分析分列展示: "),
                            "客户期价 → 近期价 → 涨幅 → 成本 → 可让利 (一目了然)"
                        ]),
                        html.Li([
                            html.I(className="fas fa-filter me-1"),
                            "每列下方有筛选框 - 即时搜索,无需回车"
                        ]),
                    ], className="mb-2", style={"fontSize": "13px"}),
                    html.Small([
                        html.I(className="fas fa-info-circle me-1"),
                        "涨价分析列说明: 客户期价=客户购买期前7天均价, 近期价=近7天均价, 可让利=近期价-成本"
                    ], className="text-muted fst-italic")
                ])
            ], color="info", className="mb-3")
        ], className="mb-3")
        
        # ========== 建议行动区域 ==========
        actions = get_recommended_actions(churn_result)
        action_section = dbc.Alert([
            html.H6("💡 建议行动", className="alert-heading mb-3"),
            html.Ul([html.Li(action) for action in actions])
        ], color="light", className="mb-4")
        
        # ========== 流失客户明细表格 ==========
        # 表格顶部说明
        table_header = html.Div([
            html.H6([
                html.I(className="fas fa-table me-2"),
                f"📋 流失客户明细 (共{len(details)}个,显示前30个)"
            ], className="mb-2"),
            html.Small("💡 提示: 点击列标题排序,使用表格内筛选框快速查找", className="text-muted")
        ], className="mb-3")
        
        # 构建表格数据
        table_data = []
        for detail in details[:30]:  # 最多显示30个客户
            # 流失原因映射
            reason_map = {
                'out_of_stock': '🚫 缺货',
                'price_increased': '💰 涨价',
                'delisted': '❌ 下架',
                'unknown': '❓ 其他'
            }
            
            # 获取问题商品列表和涨价详情
            problem_products = []
            has_price_issue = False
            price_detail = {
                'customer_price': None,
                'recent_price': None,
                'price_change_pct': None,
                'cost': None,
                'max_discount': None
            }
            
            for issue in detail.get('product_issues', [])[:3]:  # 最多显示3个问题商品
                product_name = issue['product_name'][:10]  # 截取商品名
                if issue['issue_type'] == 'out_of_stock':
                    problem_products.append(f"{product_name}(缺货)")
                elif issue['issue_type'] == 'price_increased':
                    # 记录第一个涨价商品的详细信息
                    if not has_price_issue:
                        has_price_issue = True
                        price_detail['customer_price'] = issue.get('customer_period_price', issue.get('last_price', 0))
                        price_detail['recent_price'] = issue.get('recent_price', issue.get('current_price', 0))
                        price_detail['price_change_pct'] = issue.get('price_change_pct', 0)
                        price_detail['cost'] = issue.get('cost')
                        price_detail['max_discount'] = issue.get('max_discount')
                    problem_products.append(f"{product_name}")
                elif issue['issue_type'] == 'delisted':
                    problem_products.append(f"{product_name}(下架)")
            
            problem_text = "、".join(problem_products) if problem_products else "--"
            
            # 构建表格行数据
            row_data = {
                '客户地址': detail['customer_id'][:30] + ('...' if len(detail['customer_id']) > 30 else ''),
                '最后下单': detail['last_order_date'].strftime('%Y-%m-%d'),
                '未下单天数': detail['days_since_last'],
                '历史LTV': f"¥{detail['ltv']:.0f}",
                '平均客单价': f"¥{detail['avg_order_value']:.0f}",
                '流失原因': reason_map.get(detail['primary_reason'], '未知'),
                '问题商品': problem_text,
            }
            
            # 如果是涨价影响,添加价格对比列
            if has_price_issue:
                row_data['客户期价'] = f"¥{price_detail['customer_price']:.1f}" if price_detail['customer_price'] else '--'
                row_data['近期价'] = f"¥{price_detail['recent_price']:.1f}" if price_detail['recent_price'] else '--'
                row_data['涨幅'] = f"+{price_detail['price_change_pct']:.0f}%" if price_detail['price_change_pct'] else '--'
                row_data['成本'] = f"¥{price_detail['cost']:.1f}" if price_detail['cost'] and price_detail['cost'] > 0 else '--'
                row_data['可让利'] = f"¥{price_detail['max_discount']:.1f}" if price_detail['max_discount'] and price_detail['max_discount'] > 0 else '--'
            else:
                row_data['客户期价'] = '--'
                row_data['近期价'] = '--'
                row_data['涨幅'] = '--'
                row_data['成本'] = '--'
                row_data['可让利'] = '--'
            
            table_data.append(row_data)
        
        # ========== 使用 AG Grid 表格 (支持列宽拖动、固定列等高级功能) ==========
        table = dag.AgGrid(
            rowData=table_data,
            columnDefs=[
                {
                    "field": "客户地址",
                    "headerName": "客户地址",
                    "pinned": "left",  # 固定左侧列
                    "width": 180,
                    "resizable": True,
                    "filter": "agTextColumnFilter",
                    "cellStyle": {"fontWeight": "500", "color": "#2c3e50"}
                },
                {
                    "field": "最后下单",
                    "headerName": "最后下单",
                    "width": 110,
                    "resizable": True,
                    "filter": "agDateColumnFilter",
                    "cellStyle": {"textAlign": "center"}
                },
                {
                    "field": "未下单天数",
                    "headerName": "未下单天数",
                    "width": 110,
                    "resizable": True,
                    "filter": "agNumberColumnFilter",
                    "cellStyle": {"textAlign": "center"},
                    "cellClassRules": {
                        "ag-cell-danger": "params.value >= 15"  # 高危客户标红
                    }
                },
                {
                    "field": "历史LTV",
                    "headerName": "历史LTV",
                    "width": 100,
                    "resizable": True,
                    "filter": "agTextColumnFilter",
                    "cellStyle": {"textAlign": "right", "fontWeight": "500"},
                    "cellClassRules": {
                        "ag-cell-warning": "params.value.includes('¥') && parseInt(params.value.replace(/[^0-9]/g, '')) >= 200"  # 高价值客户
                    }
                },
                {
                    "field": "平均客单价",
                    "headerName": "平均客单价",
                    "width": 110,
                    "resizable": True,
                    "filter": "agTextColumnFilter",
                    "cellStyle": {"textAlign": "right"}
                },
                {
                    "field": "流失原因",
                    "headerName": "流失原因",
                    "width": 120,
                    "resizable": True,
                    "filter": "agTextColumnFilter",
                    "cellStyle": {"textAlign": "center", "fontWeight": "500"}
                },
                {
                    "field": "问题商品",
                    "headerName": "问题商品",
                    "width": 150,
                    "resizable": True,
                    "filter": "agTextColumnFilter",
                    "wrapText": True,
                    "autoHeight": True
                },
                # ========== 涨价分析列 ==========
                {
                    "field": "客户期价",
                    "headerName": "客户期价",
                    "width": 100,
                    "resizable": True,
                    "filter": "agTextColumnFilter",
                    "cellStyle": {"textAlign": "right", "color": "#1890ff"},
                    "headerTooltip": "客户购买期(前7天)的平均价格"
                },
                {
                    "field": "近期价",
                    "headerName": "近期价",
                    "width": 100,
                    "resizable": True,
                    "filter": "agTextColumnFilter",
                    "cellStyle": {"textAlign": "right", "color": "#52c41a"},
                    "headerTooltip": "近7天的平均价格"
                },
                {
                    "field": "涨幅",
                    "headerName": "涨幅",
                    "width": 90,
                    "resizable": True,
                    "filter": "agTextColumnFilter",
                    "cellStyle": {"textAlign": "center", "color": "#ff4d4f", "fontWeight": "bold"},
                    "headerTooltip": "价格涨幅百分比"
                },
                {
                    "field": "成本",
                    "headerName": "成本",
                    "width": 90,
                    "resizable": True,
                    "filter": "agTextColumnFilter",
                    "cellStyle": {"textAlign": "right", "color": "#8c8c8c"},
                    "headerTooltip": "商品采购成本"
                },
                {
                    "field": "可让利",
                    "headerName": "可让利",
                    "width": 90,
                    "resizable": True,
                    "filter": "agTextColumnFilter",
                    "cellStyle": {"textAlign": "right", "color": "#722ed1", "fontWeight": "500"},
                    "headerTooltip": "最大可让利空间(近期价-成本)"
                },
            ],
            defaultColDef={
                "resizable": True,
                "sortable": True,
                "filter": True,
                "floatingFilter": True,  # 显示浮动筛选框
                "suppressMenu": False,  # 保留菜单
            },
            dashGridOptions={
                "pagination": True,
                "paginationPageSize": 15,
                "suppressRowHoverHighlight": False,
                "enableCellTextSelection": True,  # 可以选中文本复制
                "rowSelection": "multiple",  # 支持多选(未来可用于批量操作)
                "animateRows": True,
                "domLayout": "normal",  # 正常布局
            },
            className="ag-theme-alpine",
            style={"height": "650px", "width": "100%"}
        )
        
        return html.Div([
            data_info,
            reason_section,
            filter_buttons,  # 新增筛选按钮
            action_section,
            table_header,
            table
        ])
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"加载客户流失预警详情失败: {str(e)}", color="danger")


def get_churn_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取客户流失预警导出数据"""
    try:
        # 获取商品主数据
        from database.connection import engine
        
        # 确保事务干净
        try:
            with engine.connect() as conn:
                products_df = pd.read_sql("SELECT product_name, stock FROM products", conn)
        except Exception as db_error:
            try:
                engine.dispose()
                with engine.connect() as conn:
                    products_df = pd.read_sql("SELECT product_name, stock FROM products", conn)
            except:
                raise db_error
        
        # 调用客户流失分析
        churn_result = get_customer_churn_warning(
            df, 
            products_df, 
            today=pd.Timestamp.now(),
            lookback_days=30,
            min_orders=2,
            no_order_days=7
        )
        
        if churn_result['summary']['total_churn'] == 0:
            return pd.DataFrame()
        
        # 构建导出数据
        export_data = []
        reason_map = {
            'out_of_stock': '缺货',
            'price_increased': '涨价',
            'delisted': '下架',
            'unknown': '其他'
        }
        
        for detail in churn_result['details']:
            # 获取问题商品列表
            problem_products = []
            for issue in detail.get('product_issues', []):
                product_name = issue['product_name']
                if issue['issue_type'] == 'out_of_stock':
                    problem_products.append(f"{product_name}(缺货)")
                elif issue['issue_type'] == 'price_increased':
                    pct = issue.get('price_change_pct', 0)
                    last_price = issue.get('last_price', 0)
                    current_price = issue.get('current_price', 0)
                    problem_products.append(
                        f"{product_name}(涨价: ¥{last_price:.1f}→¥{current_price:.1f}, +{pct:.1f}%)"
                    )
                elif issue['issue_type'] == 'delisted':
                    problem_products.append(f"{product_name}(已下架)")
            
            export_data.append({
                '客户地址': detail['customer_id'],
                '最后下单日期': detail['last_order_date'].strftime('%Y-%m-%d'),
                '未下单天数': detail['days_since_last'],
                '历史LTV': detail['ltv'],
                '平均客单价': detail['avg_order_value'],
                '流失原因': reason_map.get(detail['primary_reason'], '未知'),
                '问题商品': '; '.join(problem_products) if problem_products else '--'
            })
        
        return pd.DataFrame(export_data)
    except Exception as e:
        print(f"导出客户流失数据失败: {str(e)}")
        return pd.DataFrame()


def create_aov_anomaly_detail(df: pd.DataFrame) -> html.Div:
    """创建客单价异常诊断详情 - 三Tab展示(订单维度+分类维度+商品维度)"""
    try:
        # 生成order_agg
        calculate_order_metrics = get_calculate_order_metrics()
        order_agg = calculate_order_metrics(df, calc_mode='all_with_fallback')
        
        # 创建双Tab布局
        return html.Div([
            # 筛选器行
            dbc.Row([
                # 渠道筛选
                dbc.Col([
                    html.Label("渠道筛选:", className="fw-bold me-2"),
                    dcc.Dropdown(
                        id='aov-channel-filter',
                        options=[
                            {'label': '全部渠道', 'value': 'all'},
                            {'label': '美团共橙', 'value': '美团共橙'},
                            {'label': '饿了么', 'value': '饿了么'},
                            {'label': '收银机订单', 'value': '收银机订单'},
                            {'label': '京东到家', 'value': '京东到家'},
                            {'label': '闪购小程序', 'value': '闪购小程序'}
                        ],
                        value='all',
                        clearable=False,
                        className="mb-3"
                    )
                ], width=3),
                # 周期选择器
                dbc.Col([
                    html.Label("分析周期:", className="fw-bold me-2"),
                    dbc.RadioItems(
                        id='aov-period-selector',
                        options=[
                            {'label': '近7天', 'value': 7},
                            {'label': '近15天', 'value': 15},
                            {'label': '近30天', 'value': 30}
                        ],
                        value=30,
                        inline=True,
                        className="mb-3"
                    )
                ], width=9)
            ]),
            
            # Tab导航
            dbc.Tabs([
                dbc.Tab(
                    label="📊 订单维度", 
                    tab_id="order-tab",
                    label_style={"fontSize": "16px", "fontWeight": "bold"}
                ),
                dbc.Tab(
                    label="🏷️ 分类维度", 
                    tab_id="category-tab",
                    label_style={"fontSize": "16px", "fontWeight": "bold"}
                ),
                dbc.Tab(
                    label="📦 商品维度", 
                    tab_id="product-tab",
                    label_style={"fontSize": "16px", "fontWeight": "bold"}
                )
            ], id='aov-tabs', active_tab="order-tab", className="mb-3"),
            
            # Tab内容容器
            html.Div(id='aov-tab-content')
        ])
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"加载客单价异常诊断失败: {str(e)}", color="danger")


def create_traffic_drop_detail_table(df: pd.DataFrame, days: int = 1) -> html.Div:
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
        # 🆕 趋势图区域
        create_simple_trend_section(df, 'traffic'),
        description,
        # 单品洞察提示
        html.Div([
            html.Span("👆 ", style={'fontSize': '18px'}),
            html.Span("点击表格中", className="small"),
            html.Span(" 商品名称 ", className="fw-bold text-primary", style={'textDecoration': 'underline'}),
            html.Span("可打开", className="small"),
            html.Span(" 单品洞察 ", className="fw-bold text-success"),
            html.Span("详情分析", className="small")
        ], className="mb-2 p-2 bg-warning bg-opacity-25 rounded d-flex align-items-center border border-warning"),
        dash_table.DataTable(
            id={'type': 'product-analysis-table', 'index': 'traffic-drop'},
            data=data.head(100).to_dict('records'),  # 🚀 优化：限制100行
            columns=columns,
            style_table={'overflowX': 'auto', 'maxHeight': '350px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=style_data_conditional + [
                # 商品名称列 - 可点击样式
                {'if': {'column_id': '商品名称'}, 'color': '#667eea', 'fontWeight': 'bold', 'cursor': 'pointer', 'textDecoration': 'underline'},
            ],
            cell_selectable=True,
            page_size=10,
            page_action='native',  # 🚀 客户端分页
            sort_action='native'  # 🚀 客户端排序
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


# ==================== 带商品名称点击的表格辅助函数 ====================

def create_clickable_product_table(
    data: pd.DataFrame, 
    table_index: str = 'default',
    columns: list = None,
    style_data_conditional: list = None,
    page_size: int = 20,
    max_height: str = '500px'
) -> html.Div:
    """
    创建带有可点击商品名称的表格
    
    点击商品名称可以打开单品洞察弹窗
    
    Args:
        data: 数据DataFrame，必须包含'商品名称'列
        table_index: 表格唯一索引，用于pattern-matching ID
        columns: 列定义，如果为None则自动生成
        style_data_conditional: 条件样式
        page_size: 每页显示行数
        max_height: 表格最大高度
    
    Returns:
        html.Div: 包含表格和商品链接的组件
    """
    if data.empty or '商品名称' not in data.columns:
        return html.Div("暂无数据或缺少商品名称列")
    
    # 生成商品名称可点击链接列表
    product_names = data['商品名称'].unique().tolist()
    
    # 创建隐藏的商品链接按钮（用于触发回调）
    hidden_links = html.Div([
        html.Button(
            name,
            id={'type': 'product-insight-link', 'index': name},
            n_clicks=0,
            style={'display': 'none'}
        ) for name in product_names
    ], id='hidden-product-links')
    
    # 创建表格头部提示 - 更醒目
    tip_section = html.Div([
        html.Span("👆 ", style={'fontSize': '18px'}),
        html.Span("点击表格中", className="small"),
        html.Span(" 商品名称 ", className="fw-bold text-primary", style={'textDecoration': 'underline'}),
        html.Span("可打开", className="small"),
        html.Span(" 单品洞察 ", className="fw-bold text-success"),
        html.Span("详情分析", className="small")
    ], className="mb-3 p-2 bg-warning bg-opacity-25 rounded d-flex align-items-center border border-warning")
    
    # 将商品名称变成链接样式的文本（使用markdown presentation）
    # 但由于DataTable不支持直接渲染HTML，我们改用列点击
    if columns is None:
        columns = [{'name': c, 'id': c} for c in data.columns]
    
    # 为商品名称列添加特殊样式
    style_data_conditional = style_data_conditional or []
    style_data_conditional.append({
        'if': {'column_id': '商品名称'},
        'color': '#667eea',
        'fontWeight': 'bold',
        'cursor': 'pointer',
        'textDecoration': 'underline'
    })
    
    # 创建表格（使用active_cell来捕获点击）
    table = dash_table.DataTable(
        id={'type': 'product-analysis-table', 'index': table_index},
        data=data.to_dict('records'),
        columns=columns,
        style_table={'overflowX': 'auto', 'maxHeight': max_height, 'overflowY': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
        style_data_conditional=style_data_conditional,
        page_size=page_size,
        page_action='native',
        sort_action='native',
        cell_selectable=True,
    )
    
    return html.Div([
        tip_section,
        hidden_links,
        table
    ])


def create_slow_moving_detail_table(df: pd.DataFrame) -> html.Div:
    """创建滞销商品详情表格（支持点击商品名称查看单品洞察）"""
    data = get_slow_moving_products(df)
    if data.empty:
        return dbc.Alert("暂无滞销商品数据", color="info")
    
    # 统计各等级数量
    level_counts = data['滞销等级'].value_counts().to_dict()
    
    # 条件样式
    style_data_conditional = [
        {'if': {'filter_query': '{滞销等级} = "🔴 严重滞销"'}, 'backgroundColor': '#ffebee'},
        {'if': {'filter_query': '{滞销等级} = "⚠️ 持续滞销"'}, 'backgroundColor': '#fff8e1'},
        {'if': {'filter_query': '{滞销等级} = "🆕 新增风险"'}, 'backgroundColor': '#e3f2fd'}
    ]
    
    # 使用可点击表格
    table_component = create_clickable_product_table(
        data=data,
        table_index='slow-moving',
        style_data_conditional=style_data_conditional,
        page_size=20
    )
    
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
        table_component,
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
    """创建昨日首销商品详情表格（支持点击商品名称查看单品洞察）"""
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
    
    # 条件样式
    style_data_conditional = [
        {'if': {'column_id': '首日销量'}, 'color': 'green', 'fontWeight': 'bold'},
        {'if': {'column_id': '首日销售额'}, 'color': 'green', 'fontWeight': 'bold'},
        {'if': {'column_id': '首日利润'}, 'color': '#1976d2', 'fontWeight': 'bold'},
        {'if': {'filter_query': '{沉寂等级} = "🟢 短期沉寂"'}, 'backgroundColor': '#e8f5e9'},
        {'if': {'filter_query': '{沉寂等级} = "🟡 中期沉寂"'}, 'backgroundColor': '#fff8e1'},
        {'if': {'filter_query': '{沉寂等级} = "🔴 长期沉寂"'}, 'backgroundColor': '#ffebee'}
    ]
    
    # 使用可点击表格
    table_component = create_clickable_product_table(
        data=data,
        table_index='new-product',
        style_data_conditional=style_data_conditional,
        page_size=20
    )
    
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
        table_component,
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


def create_price_abnormal_detail_table(df: pd.DataFrame, days: int = 1) -> html.Div:
    """创建价格异常商品详情表格（昨日售价<成本的商品）+ 趋势分析"""
    data = get_price_abnormal_products(df)
    if data.empty:
        return dbc.Alert("暂无价格异常商品（昨日所有商品售价均高于成本）", color="success")
    
    # 生成趋势对比区
    trend_section = create_trend_comparison_section(df, 'price_abnormal')
    
    # 统计各等级数量
    level_counts = data['异常等级'].value_counts().to_dict() if '异常等级' in data.columns else {}
    severe_count = level_counts.get('🔴严重亏损', 0)
    mild_count = level_counts.get('🟠轻度亏损', 0)
    
    # 统计总亏损
    total_loss = data['预估总亏损'].sum() if '预估总亏损' in data.columns else 0
    
    return html.Div([
        # ========== 趋势对比区（顶部） ==========
        trend_section,
        
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
        # 单品洞察提示
        html.Div([
            html.Span("👆 ", style={'fontSize': '18px'}),
            html.Span("点击表格中", className="small"),
            html.Span(" 商品名称 ", className="fw-bold text-primary", style={'textDecoration': 'underline'}),
            html.Span("可打开", className="small"),
            html.Span(" 单品洞察 ", className="fw-bold text-success"),
            html.Span("详情分析", className="small")
        ], className="mb-2 p-2 bg-warning bg-opacity-25 rounded d-flex align-items-center border border-warning"),
        dash_table.DataTable(
            id={'type': 'product-analysis-table', 'index': 'price-abnormal'},
            data=data.head(200).to_dict('records'),  # 🚀 优化：限制200行
            columns=[{'name': c, 'id': c} for c in data.columns],
            style_table={'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'column_id': '单位亏损'}, 'fontWeight': 'bold', 'color': 'red'},
                {'if': {'column_id': '预估总亏损'}, 'fontWeight': 'bold', 'color': 'red'},
                {'if': {'filter_query': '{异常等级} = "🔴严重亏损"'}, 'backgroundColor': '#ffebee'},
                {'if': {'filter_query': '{异常等级} = "🟠轻度亏损"'}, 'backgroundColor': '#fff3e0'},
                # 商品名称列 - 可点击样式
                {'if': {'column_id': '商品名称'}, 'color': '#667eea', 'fontWeight': 'bold', 'cursor': 'pointer', 'textDecoration': 'underline'},
            ],
            cell_selectable=True,
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


def create_profit_drop_detail_table(df: pd.DataFrame, days: int = 1) -> html.Div:
    """创建利润率下滑商品详情表格（近7天vs前7天，下滑>5%）+ 可视化图表"""
    data = get_profit_rate_drop_products(df)
    if data.empty:
        return dbc.Alert("暂无利润率下滑商品（近7天利润率下滑均<5个百分点）", color="success")
    
    # 统计各等级数量（优化后的4档）
    level_counts = data['下滑等级'].value_counts().to_dict() if '下滑等级' in data.columns else {}
    severe_count = level_counts.get('🔴严重下滑', 0)
    major_count = level_counts.get('🟠大幅下滑', 0)
    medium_count = level_counts.get('🟡中度下滑', 0)
    light_count = level_counts.get('🟢轻微下滑', 0)
    
    # ========== 可视化图表 (ECharts) ==========
    charts_section = html.Div()
    if ECHARTS_AVAILABLE:
        try:
            charts = []
            
            # ===== 图表1：利润率下滑原因分析（按分类统计）=====
            category_col = '一级分类' if '一级分类' in data.columns else None
            if category_col:
                # 按分类统计下滑商品数
                category_stats = data.groupby(category_col).agg({
                    '商品名称': 'count'
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
                {'name': '🔴 严重(>20%)', 'value': severe_count},
                {'name': '🟠 大幅(15-20%)', 'value': major_count},
                {'name': '🟡 中度(10-15%)', 'value': medium_count},
                {'name': '🟢 轻微(5-10%)', 'value': light_count}
            ]
            # 过滤掉0值
            pie_data = [p for p in pie_data if p['value'] > 0]
            
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
                    'color': ['#F44336', '#FF9800', '#FFC107', '#4CAF50']
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
        # 🆕 趋势图区域
        create_simple_trend_section(df, 'profit_drop'),
        html.P([
            f"发现 ",
            html.Span(f"{len(data)}", className="fw-bold text-warning"),
            f" 个利润率下滑商品（近7天vs前7天，下滑>5个百分点）"
        ], className="mb-2"),
        html.Div([
            html.Span(f"🔴 严重(>20%): {severe_count}", className="me-3 text-danger"),
            html.Span(f"🟠 大幅(15-20%): {major_count}", className="me-3", style={'color': '#FF9800'}),
            html.Span(f"🟡 中度(10-15%): {medium_count}", className="me-3", style={'color': '#FFC107'}),
            html.Span(f"🟢 轻微(5-10%): {light_count}", style={'color': '#4CAF50'})
        ], className="mb-3 small"),
        # 单品洞察提示
        html.Div([
            html.Span("👆 ", style={'fontSize': '18px'}),
            html.Span("点击表格中", className="small"),
            html.Span(" 商品名称 ", className="fw-bold text-primary", style={'textDecoration': 'underline'}),
            html.Span("可打开", className="small"),
            html.Span(" 单品洞察 ", className="fw-bold text-success"),
            html.Span("详情分析", className="small")
        ], className="mb-2 p-2 bg-warning bg-opacity-25 rounded d-flex align-items-center border border-warning"),
        dash_table.DataTable(
            id={'type': 'product-analysis-table', 'index': 'profit-drop'},
            data=data.head(150).to_dict('records'),  # 🚀 优化：限制150行
            columns=[{'name': c, 'id': c} for c in data.columns],
            style_table={'overflowX': 'auto', 'maxHeight': '350px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'column_id': '下滑幅度'}, 'fontWeight': 'bold', 'color': 'red'},
                {'if': {'column_id': '前7天利润率'}, 'color': '#4CAF50'},
                {'if': {'column_id': '近7天利润率'}, 'color': '#FF9800'},
                {'if': {'filter_query': '{下滑等级} = "🔴严重下滑"'}, 'backgroundColor': '#ffebee'},
                {'if': {'filter_query': '{下滑等级} = "🟠大幅下滑"'}, 'backgroundColor': '#fff3e0'},
                {'if': {'filter_query': '{下滑等级} = "🟡中度下滑"'}, 'backgroundColor': '#fffde7'},
                {'if': {'filter_query': '{下滑等级} = "🟢轻微下滑"'}, 'backgroundColor': '#e8f5e9'},
                # 商品名称列 - 可点击样式
                {'if': {'column_id': '商品名称'}, 'color': '#667eea', 'fontWeight': 'bold', 'cursor': 'pointer', 'textDecoration': 'underline'},
            ],
            cell_selectable=True,
            page_size=15,
            page_action='native',
            sort_action='native'
        ),
        # 可视化图表区
        charts_section,
        html.Div([
            html.Small([
                html.Strong("📌 利润率计算："),
                "利润率 = 利润额 ÷ 销售额 × 100%（限制在-100%~100%范围）"
            ], className="text-muted d-block"),
            html.Small([
                html.Strong("📝 下滑等级："),
                "🔴严重(>20%) | 🟠大幅(15-20%) | 🟡中度(10-15%) | 🟢轻微(5-10%)"
            ], className="text-muted d-block mt-1"),
        ], className="mt-2 p-2 bg-light rounded")
    ])


def get_profit_drop_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取利润率下滑商品导出数据"""
    return get_profit_rate_drop_products(df)


def create_hot_products_detail_table(df: pd.DataFrame, days: int = 1) -> html.Div:
    """创建爆款商品详情表格 - 增加连续增长天数分析"""
    data = get_hot_products(df)
    if data.empty:
        return dbc.Alert("暂无爆款商品（昨日无销量环比增长>50%且销量>=10的商品）", color="info")
    
    # 统计各等级数量
    level_counts = data['爆款等级'].value_counts().to_dict() if '爆款等级' in data.columns else {}
    super_hot = level_counts.get('超级爆款', 0)
    very_hot = level_counts.get('热销', 0)
    hot = level_counts.get('增长', 0)
    
    # 统计总销量和销售额
    total_qty = data['昨日销量'].sum() if '昨日销量' in data.columns else 0
    total_sales = data['昨日销售额'].sum() if '昨日销售额' in data.columns else 0
    
    # ========== 计算连续增长天数（简化版：基于爆款等级判断） ==========
    sustained_hot_products = []  # 真爆款
    
    try:
        # 简化逻辑：超级爆款和热销都算真爆款
        if '爆款等级' in data.columns and '商品名称' in data.columns:
            print(f"[DEBUG] 爆款等级列数据样例: {data['爆款等级'].head().tolist()}")
            
            for _, row in data.iterrows():
                level = str(row.get('爆款等级', '')).strip()
                name = str(row.get('商品名称', ''))
                
                # 获取增长率，处理各种格式
                growth_raw = row.get('增长率', 0)
                if isinstance(growth_raw, str):
                    growth_raw = growth_raw.replace('%', '').replace('+', '')
                    try:
                        growth = float(growth_raw)
                    except:
                        growth = 0
                else:
                    growth = float(growth_raw) if growth_raw else 0
                
                # 判断爆款等级（使用中文描述）
                if level == '超级爆款':
                    sustained_hot_products.append({'name': name, 'growth': growth, 'level': '超级爆款'})
                elif level == '热销':
                    sustained_hot_products.append({'name': name, 'growth': growth, 'level': '热销'})
        
        print(f"[DEBUG] 找到 {len(sustained_hot_products)} 个真爆款: {[p['name'][:6] for p in sustained_hot_products[:5]]}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[DEBUG] 爆款分析失败: {e}")
    
    # ========== 构建真爆款区域（始终显示） ==========
    if sustained_hot_products:
        # 按增长率排序
        sustained_hot_products.sort(key=lambda x: x['growth'], reverse=True)
        
        product_badges = []
        for p in sustained_hot_products[:8]:
            growth_display = f"+{p['growth']:.0f}%" if p['growth'] > 0 else "热卖"
            product_badges.append(
                html.Div([
                    html.Span(f"🔥 {p['name'][:10]}", className="fw-bold text-success"),
                    html.Span(f" {growth_display}", className="badge bg-success ms-1"),
                    html.Small(f" [{p['level']}]", className="text-muted ms-1")
                ], className="me-3 mb-2 d-inline-block")
            )
        
        sustained_section = html.Div([
            html.H6([
                "🏆 真爆款TOP ",
                html.Span(f"({len(sustained_hot_products)}个)", className="text-success")
            ], className="mb-3"),
            html.Div(product_badges, className="d-flex flex-wrap"),
            html.Hr(className="my-2"),
            html.Small([
                "✅ 真爆款标准：增长率>100%的超级爆款或热销商品，说明是持续的市场需求。",
                "建议：加大曝光、确保库存、考虑提价空间"
            ], className="text-muted d-block")
        ], className="mb-3 p-3 bg-success bg-opacity-10 rounded border border-success")
    else:
        # 没有超级爆款时，显示简单提示
        sustained_section = html.Div([
            html.Div([
                html.Span("📊 ", style={'fontSize': '18px'}),
                html.Span("爆款分析：", className="fw-bold"),
                html.Span(f"共发现 {len(data)} 个增长商品", className="text-muted ms-2"),
                html.Small("（超级爆款🔥🔥🔥更值得关注）", className="text-muted ms-2")
            ])
        ], className="mb-3 p-2 bg-light rounded")
    
    # 条件样式
    style_data_conditional = [
        {'if': {'column_id': '昨日销量'}, 'fontWeight': 'bold', 'color': 'green'},
        {'if': {'column_id': '增长率'}, 'fontWeight': 'bold', 'color': '#28a745'},
        {'if': {'column_id': '昨日利润'}, 'fontWeight': 'bold', 'color': '#1976d2'},
        {'if': {'filter_query': '{爆款等级} = "超级爆款"'}, 'backgroundColor': '#fff3e0'},
        {'if': {'filter_query': '{爆款等级} = "热销"'}, 'backgroundColor': '#fffde7'},
        # 商品名称可点击样式
        {'if': {'column_id': '商品名称'}, 'color': '#667eea', 'fontWeight': 'bold', 
         'cursor': 'pointer', 'textDecoration': 'underline'},
    ]
    
    # 使用普通DataTable，避免自动弹窗问题
    table_component = html.Div([
        # 单品洞察提示
        html.Div([
            html.Span("👆 ", style={'fontSize': '18px'}),
            html.Span("点击表格中", className="small"),
            html.Span(" 商品名称 ", className="fw-bold text-primary", style={'textDecoration': 'underline'}),
            html.Span("可打开", className="small"),
            html.Span(" 单品洞察 ", className="fw-bold text-success"),
            html.Span("详情分析", className="small")
        ], className="mb-2 p-2 bg-warning bg-opacity-25 rounded d-flex align-items-center border border-warning"),
        dash_table.DataTable(
            id={'type': 'product-analysis-table', 'index': 'hot-products'},
            data=data.head(100).to_dict('records'),  # 🚀 优化：增加到100行
            columns=[{'name': c, 'id': c} for c in data.columns],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px', 'fontSize': '13px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=style_data_conditional,
            cell_selectable=True,
            page_size=15,
            page_action='native',  # 🚀 客户端分页
            sort_action='native'  # 🚀 客户端排序
        )
    ])
    
    return html.Div([
        # 🆕 趋势图区域
        create_simple_trend_section(df, 'hot'),
        # ========== 真爆款识别区域（顶部） ==========
        sustained_section,
        
        html.P([
            f"昨日发现 ",
            html.Span(f"{len(data)}", className="fw-bold text-success"),
            f" 个爆款商品，共销售 ",
            html.Span(f"{total_qty}", className="fw-bold text-success"),
            f" 件，贡献销售额 ",
            html.Span(f"¥{total_sales:,.2f}", className="fw-bold text-success")
        ], className="mb-2"),
        html.Div([
            html.Span(f"超级爆款(+200%): {super_hot}个", className="me-3 text-danger fw-bold"),
            html.Span(f"热销(+100%): {very_hot}个", className="me-3 text-warning"),
            html.Span(f"增长(+50%): {hot}个", className="me-3")
        ], className="mb-3 small"),
        table_component,
        html.Div([
            html.Small([
                html.Strong("📌 定义提示："),
                "爆款 = 昨日销量环比增长>50% 且 昨日销量>=10；数据范围：昨日vs前日"
            ], className="text-muted d-block"),
            html.Small([
                html.Strong("📝 爆款等级："),
                "超级爆款: 增长>200%；",
                "热销: 增长>100%；",
                "增长: 增长>50%"
            ], className="text-muted d-block mt-1"),
        ], className="mt-2 p-2 bg-light rounded")
    ])


def get_hot_products_export_data(df: pd.DataFrame) -> pd.DataFrame:
    """获取爆款商品导出数据"""
    return get_hot_products(df)


def create_high_profit_detail_table(df: pd.DataFrame, days: int = 1) -> html.Div:
    """创建高利润商品详情表格（支持点击商品名称查看单品洞察）+ 趋势分析 + 日期筛选"""
    data = get_high_profit_products(df, days=days)
    if data.empty:
        return html.Div([
            # 日期筛选按钮（即使无数据也显示，方便切换）
            create_date_filter_buttons('high_profit', default_days=days),
            dbc.Alert("暂无符合条件的高利润商品（毛利率≥25%且利润额≥10元且销量≥3）", color="info", className="mt-3")
        ])
    
    # 根据days确定列名前缀
    if days == 0:
        period_prefix = '累计'
        period_label = '累计'
    elif days == 1:
        period_prefix = '当天'
        period_label = '当天'
    else:
        period_prefix = f'{days}天'
        period_label = f'近{days}天'
    
    # 生成趋势对比区
    trend_section = create_trend_comparison_section(df, 'high_profit')
    
    # 统计 - 根据实际列名
    profit_col = f'{period_prefix}利润'
    sales_col = f'{period_prefix}销售额'
    total_profit = data[profit_col].sum() if profit_col in data.columns else 0
    total_sales = data[sales_col].sum() if sales_col in data.columns else 0
    avg_rate = (total_profit / total_sales * 100) if total_sales > 0 else 0
    
    # 条件样式 - 根据实际列名
    style_data_conditional = [
        {'if': {'column_id': profit_col}, 'fontWeight': 'bold', 'color': '#1976d2'},
        {'if': {'column_id': '利润率'}, 'fontWeight': 'bold', 'color': '#28a745'},
        {'if': {'column_id': '排名'}, 'fontWeight': 'bold'},
        {'if': {'filter_query': '{排名} contains "🥇"'}, 'backgroundColor': '#fff8e1'},
        {'if': {'filter_query': '{排名} contains "🥈"'}, 'backgroundColor': '#f5f5f5'},
        {'if': {'filter_query': '{排名} contains "🥉"'}, 'backgroundColor': '#fff3e0'},
    ]
    
    # 使用可点击表格
    table_component = create_clickable_product_table(
        data=data,
        style_data_conditional=style_data_conditional,
        page_size=20,
        table_index='high-profit'  # 高利润商品
    )
    
    return html.Div([
        # ========== 趋势对比区（顶部） ==========
        trend_section,
        
        # ========== 日期筛选按钮 ==========
        create_date_filter_buttons('high_profit', default_days=days),
        
        # 顶部汇总
        html.Div([
            html.Span([
                html.I(className="bi bi-gem me-2 text-primary"),
                f"{period_label}高利润TOP ",
                html.Span(f"{len(data)}", className="fw-bold text-primary"),
                f" 商品，贡献利润 ",
                html.Span(f"¥{total_profit:,.2f}", className="fw-bold text-primary"),
                f"，平均利润率 ",
                html.Span(f"{avg_rate:.1f}%", className="fw-bold text-success")
            ])
        ], className="mb-3 p-2 bg-primary bg-opacity-10 rounded"),
        
        # 表格容器
        html.Div(id='high-profit-tables-container', children=[
            table_component
        ]),
        
        html.Div([
            html.Small([
                html.Strong("📌 高利润定义："),
                "毛利率≥25% + 利润额≥10元 + 销量≥3；按利润额排序取TOP30"
            ], className="text-muted d-block"),
            html.Small([
                html.Strong("📊 核心公式："),
                "利润率 = 利润额 ÷ 销售额 × 100%；",
                "单品成本 = 商品采购成本 ÷ 销量"
            ], className="text-muted d-block mt-1"),
        ], className="mt-2 p-2 bg-light rounded")
    ])


def get_high_profit_export_data(df: pd.DataFrame, days: int = 1) -> pd.DataFrame:
    """获取高利润商品导出数据"""
    return get_high_profit_products(df, days=days)


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
                    data=basic_data.head(200).to_dict('records'),  # 🚀 优化：限制200行
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
                    data=revenue_data.head(200).to_dict('records') if not revenue_data.empty else [],  # 🚀 优化
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
                    data=profit_data.head(200).to_dict('records') if not profit_data.empty else [],  # 🚀 优化
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


# ==================== 单品洞察 ECharts 组件 (V2.0) ====================

def render_product_insight_echarts(df: pd.DataFrame, product_name: str) -> html.Div:
    """
    使用 ECharts 渲染增强版单品洞察
    
    包含四个核心图表:
    1. 📊 单品日记 - 购买角色按日拆解（堆叠柱状图）
    2. 🤝 最佳拍档 - Top 10 连带商品（水平条形图）
    3. ⏰ 时段画像 - 24小时销量+利润率（双轴图）
    4. 📈 价格敏感度 - 按日销量+单价+利润率（多轴图）
    """
    if not ECHARTS_AVAILABLE:
        return dbc.Alert("ECharts 组件未安装，请安装 dash-echarts", color="warning")
    
    try:
        # 获取增强版单品洞察数据
        insight = get_product_insight_enhanced(df, product_name)
        
        if insight.get('error'):
            return dbc.Alert(f"获取数据失败: {insight['error']}", color="danger")
        
        summary = insight['summary']
        daily_trend = insight['daily_trend']
        hourly_trend = insight['hourly_trend']
        partners = insight['partners']
        role_daily = insight['role_daily']
        sensitivity = insight['price_sensitivity']
        recommendations = insight['recommendations']
        
        # ========== 顶部指标卡片 ==========
        def create_metric_card(title, value, sub_text, icon, color):
            color_map = {
                'primary': '#667eea', 'success': '#10b981', 'warning': '#f59e0b',
                'danger': '#ef4444', 'info': '#06b6d4'
            }
            bg_color = color_map.get(color, '#667eea')
            return dbc.Col([
                html.Div([
                    html.Div([
                        html.Span(icon, style={'fontSize': '24px'}),
                        html.Span(title, className="ms-2 fw-bold", style={'fontSize': '14px'})
                    ], className="d-flex align-items-center mb-2"),
                    html.Div(value, className="fw-bold", style={'fontSize': '28px', 'color': bg_color}),
                    html.Small(sub_text, className="text-muted")
                ], className="p-3 bg-light rounded h-100", style={'borderLeft': f'4px solid {bg_color}'})
            ], width=3, className="mb-3")
        
        metric_cards = dbc.Row([
            create_metric_card("销量", f"{summary['total_quantity']}单", "累计订单数", "📦", "primary"),
            create_metric_card("销售额", f"¥{summary['total_sales']:,.0f}", "累计销售额", "💰", "warning"),
            create_metric_card("平均单价", f"¥{summary['avg_price']:.1f}", "实收/销量", "🏷️", "info"),
            create_metric_card("毛利率", f"{summary['avg_margin']:.1f}%", "利润/销售额", "📈", 
                             "danger" if summary['avg_margin'] < 15 else "success"),
        ])
        
        # ========== 图表1: 单品日记（购买角色堆叠柱状图） ==========
        chart1_option = {'title': {'text': '📊 单品日记 (暂无数据)', 'left': 'center'}}
        if not role_daily.empty:
            # 透视数据
            role_pivot = role_daily.pivot(index='日期', columns='角色', values='销量').fillna(0)
            dates = [d.strftime('%m-%d') for d in role_pivot.index]
            
            role_colors = {'核心需求': '#10b981', '凑单配角': '#3b82f6', '亏损引流': '#ef4444'}
            series = []
            for role in ['核心需求', '凑单配角', '亏损引流']:
                if role in role_pivot.columns:
                    series.append({
                        'name': role,
                        'type': 'bar',
                        'stack': 'total',
                        'data': role_pivot[role].tolist(),
                        'itemStyle': {'color': role_colors.get(role, '#999')},
                        'emphasis': {'focus': 'series'}
                    })
            
            chart1_option = {
                'title': {'text': '📊 单品日记 (购买角色拆解)', 'left': 'center', 'textStyle': {'fontSize': 14}},
                'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
                'legend': {'data': ['核心需求', '凑单配角', '亏损引流'], 'top': 30},
                'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'top': 80, 'containLabel': True},
                'xAxis': {'type': 'category', 'data': dates, 'axisLabel': {'rotate': 30, 'fontSize': 11}},
                'yAxis': {'type': 'value', 'name': '销量'},
                'series': series
            }
        
        # ========== 图表2: 最佳拍档（水平条形图） ==========
        chart2_option = {'title': {'text': '🤝 最佳拍档 (暂无数据)', 'left': 'center'}}
        if not partners.empty:
            # 取 Top 10
            top_partners = partners.head(10).sort_values('频次', ascending=True)
            
            chart2_option = {
                'title': {'text': '🤝 最佳拍档 (Top 10 连带商品)', 'left': 'center', 'textStyle': {'fontSize': 14}},
                'tooltip': {
                    'trigger': 'axis', 
                    'axisPointer': {'type': 'shadow'},
                    'formatter': '''function(params) {
                        var name = params[0].name;
                        var value = params[0].value;
                        return name + '<br/>频次: ' + value + '次';
                    }'''
                },
                'grid': {'left': '3%', 'right': '10%', 'bottom': '3%', 'top': 50, 'containLabel': True},
                'xAxis': {'type': 'value', 'name': '连带频次'},
                'yAxis': {'type': 'category', 'data': top_partners['商品名称'].tolist(),
                         'axisLabel': {'fontSize': 11, 'width': 120, 'overflow': 'truncate'}},
                'series': [{
                    'name': '频次',
                    'type': 'bar',
                    'data': top_partners['频次'].tolist(),
                    'itemStyle': {
                        'color': {
                            'type': 'linear', 'x': 0, 'y': 0, 'x2': 1, 'y2': 0,
                            'colorStops': [
                                {'offset': 0, 'color': '#667eea'},
                                {'offset': 1, 'color': '#764ba2'}
                            ]
                        },
                        'borderRadius': [0, 4, 4, 0]
                    },
                    'label': {'show': True, 'position': 'right', 'formatter': '{c}次'}
                }]
            }
        
        # ========== 图表3: 时段画像（24小时双轴图） ==========
        chart3_option = {'title': {'text': '⏰ 时段画像 (暂无数据)', 'left': 'center'}}
        if not hourly_trend.empty:
            hours = hourly_trend['小时'].tolist()
            sales_data = hourly_trend['销量'].tolist()
            profit_rate_data = hourly_trend['实收利润率'].tolist()
            revenue_data = hourly_trend['销售额'].tolist()
            
            chart3_option = {
                'title': {'text': '⏰ 时段画像 (24小时销量与利润率)', 'left': 'center', 'textStyle': {'fontSize': 14}},
                'tooltip': {
                    'trigger': 'axis',
                    'axisPointer': {'type': 'cross'},
                    'formatter': '''function(params) {
                        var hour = params[0].axisValue;
                        var result = hour + '点<br/>';
                        params.forEach(function(p) {
                            if (p.seriesName === '销量') {
                                result += p.marker + p.seriesName + ': ' + p.value + '单<br/>';
                            } else if (p.seriesName === '利润率') {
                                result += p.marker + p.seriesName + ': ' + p.value + '%<br/>';
                            } else {
                                result += p.marker + p.seriesName + ': ¥' + p.value + '<br/>';
                            }
                        });
                        return result;
                    }'''
                },
                'legend': {'data': ['销量', '销售额', '利润率'], 'top': 30},
                'grid': {'left': '3%', 'right': '10%', 'bottom': '3%', 'top': 80, 'containLabel': True},
                'xAxis': {'type': 'category', 'data': hours, 'name': '小时',
                         'axisLabel': {'formatter': '{value}点'}},
                'yAxis': [
                    {'type': 'value', 'name': '销量/销售额', 'position': 'left'},
                    {'type': 'value', 'name': '利润率(%)', 'position': 'right', 'min': 0, 'max': 100,
                     'axisLabel': {'formatter': '{value}%'}}
                ],
                'series': [
                    {
                        'name': '销量',
                        'type': 'bar',
                        'data': sales_data,
                        'itemStyle': {'color': 'rgba(102, 126, 234, 0.7)', 'borderRadius': [4, 4, 0, 0]}
                    },
                    {
                        'name': '销售额',
                        'type': 'bar',
                        'data': revenue_data,
                        'itemStyle': {'color': 'rgba(245, 158, 11, 0.7)', 'borderRadius': [4, 4, 0, 0]}
                    },
                    {
                        'name': '利润率',
                        'type': 'line',
                        'yAxisIndex': 1,
                        'data': profit_rate_data,
                        'smooth': True,
                        'symbol': 'circle',
                        'symbolSize': 6,
                        'lineStyle': {'color': '#10b981', 'width': 2},
                        'itemStyle': {'color': '#10b981'},
                        'areaStyle': {'color': 'rgba(16, 185, 129, 0.1)'}
                    }
                ]
            }
        
        # ========== 图表4: 价格敏感度趋势（多轴图） ==========
        chart4_option = {'title': {'text': '📈 价格敏感度 (暂无数据)', 'left': 'center'}}
        if not daily_trend.empty:
            dates = [d.strftime('%m-%d') for d in daily_trend['日期']]
            sales_data = daily_trend['销量'].tolist()
            price_data = daily_trend['平均单价'].tolist()
            profit_rate_data = daily_trend['实收利润率'].tolist()
            pricing_rate_data = daily_trend['定价利润率'].tolist()
            profit_data = daily_trend['利润额'].tolist()
            
            chart4_option = {
                'title': {'text': '📈 价格敏感度趋势 (销量vs单价vs利润率)', 'left': 'center', 'textStyle': {'fontSize': 14}},
                'tooltip': {
                    'trigger': 'axis',
                    'axisPointer': {'type': 'cross'},
                    'formatter': '''function(params) {
                        var date = params[0].axisValue;
                        var result = date + '<br/>';
                        params.forEach(function(p) {
                            if (p.seriesName === '销量') {
                                result += p.marker + p.seriesName + ': ' + p.value + '单<br/>';
                            } else if (p.seriesName.indexOf('利润率') >= 0) {
                                result += p.marker + p.seriesName + ': ' + p.value + '%<br/>';
                            } else if (p.seriesName === '利润额') {
                                result += p.marker + p.seriesName + ': ¥' + p.value + '<br/>';
                            } else {
                                result += p.marker + p.seriesName + ': ¥' + p.value + '<br/>';
                            }
                        });
                        return result;
                    }'''
                },
                'legend': {'data': ['销量', '平均单价', '实收利润率', '定价利润率', '利润额'], 'top': 30, 
                          'selected': {'销量': True, '平均单价': True, '实收利润率': True, '定价利润率': False, '利润额': False}},
                'grid': {'left': '3%', 'right': '15%', 'bottom': '3%', 'top': 80, 'containLabel': True},
                'xAxis': {'type': 'category', 'data': dates, 'axisLabel': {'rotate': 30, 'fontSize': 11}},
                'yAxis': [
                    {'type': 'value', 'name': '销量', 'position': 'left'},
                    {'type': 'value', 'name': '单价(¥)', 'position': 'right', 'offset': 0},
                    {'type': 'value', 'name': '利润率(%)', 'position': 'right', 'offset': 60, 
                     'min': 0, 'axisLabel': {'formatter': '{value}%'}}
                ],
                'series': [
                    {
                        'name': '销量',
                        'type': 'bar',
                        'data': sales_data,
                        'itemStyle': {'color': 'rgba(102, 126, 234, 0.6)', 'borderRadius': [4, 4, 0, 0]}
                    },
                    {
                        'name': '平均单价',
                        'type': 'line',
                        'yAxisIndex': 1,
                        'data': price_data,
                        'smooth': True,
                        'symbol': 'circle',
                        'symbolSize': 6,
                        'lineStyle': {'color': '#f59e0b', 'width': 2},
                        'itemStyle': {'color': '#f59e0b'}
                    },
                    {
                        'name': '实收利润率',
                        'type': 'line',
                        'yAxisIndex': 2,
                        'data': profit_rate_data,
                        'smooth': True,
                        'symbol': 'diamond',
                        'symbolSize': 6,
                        'lineStyle': {'color': '#10b981', 'width': 2},
                        'itemStyle': {'color': '#10b981'}
                    },
                    {
                        'name': '定价利润率',
                        'type': 'line',
                        'yAxisIndex': 2,
                        'data': pricing_rate_data,
                        'smooth': True,
                        'symbol': 'triangle',
                        'symbolSize': 6,
                        'lineStyle': {'color': '#8b5cf6', 'width': 2, 'type': 'dashed'},
                        'itemStyle': {'color': '#8b5cf6'}
                    },
                    {
                        'name': '利润额',
                        'type': 'bar',
                        'yAxisIndex': 1,
                        'data': profit_data,
                        'itemStyle': {'color': 'rgba(16, 185, 129, 0.4)', 'borderRadius': [4, 4, 0, 0]}
                    }
                ]
            }
        
        # ========== 智能洞察卡片 ==========
        sensitivity_colors = {'red': 'danger', 'orange': 'warning', 'green': 'success', 'blue': 'info', 'gray': 'secondary'}
        sensitivity_badge_color = sensitivity_colors.get(sensitivity['color'], 'secondary')
        
        insight_card = dbc.Card([
            dbc.CardHeader([
                html.Span("💡 ", style={'fontSize': '18px'}),
                html.Span("智能洞察", className="fw-bold")
            ]),
            dbc.CardBody([
                # 价格敏感度
                html.Div([
                    html.Span("价格敏感度: ", className="fw-bold"),
                    dbc.Badge(sensitivity['level'], color=sensitivity_badge_color, className="ms-2"),
                    html.Small(f" (相关系数: {sensitivity['correlation']:.2f})", className="text-muted ms-2")
                ], className="mb-3"),
                # 核心指标提示
                html.Div([
                    html.Small([
                        html.Strong("平均订单利润: "),
                        html.Span(f"¥{summary['avg_profit_per_order']:.2f}", 
                                 className="text-success" if summary['avg_profit_per_order'] > 0 else "text-danger")
                    ])
                ], className="mb-2"),
                html.Hr(),
                # 推荐行动
                html.Div([
                    dbc.Alert([
                        html.H6(rec['title'], className="alert-heading mb-1"),
                        html.P(rec['desc'], className="mb-0 small")
                    ], color=rec['type'], className="mb-2 py-2") for rec in recommendations
                ])
            ])
        ], className="h-100")
        
        # ========== 组装布局 ==========
        return html.Div([
            # 顶部指标卡片
            metric_cards,
            
            # 第一行: 单品日记 + 最佳拍档
            dbc.Row([
                dbc.Col([
                    DashECharts(option=chart1_option, style={'height': '320px', 'width': '100%'})
                ], width=6),
                dbc.Col([
                    DashECharts(option=chart2_option, style={'height': '320px', 'width': '100%'})
                ], width=6),
            ], className="mb-4"),
            
            # 第二行: 时段画像 + 价格敏感度
            dbc.Row([
                dbc.Col([
                    DashECharts(option=chart3_option, style={'height': '320px', 'width': '100%'})
                ], width=6),
                dbc.Col([
                    DashECharts(option=chart4_option, style={'height': '320px', 'width': '100%'})
                ], width=6),
            ], className="mb-4"),
            
            # 第三行: 智能洞察
            dbc.Row([
                dbc.Col(insight_card, width=12)
            ])
        ], className="p-3")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"渲染单品洞察失败: {str(e)}", color="danger")


def create_business_diagnosis_card(df: pd.DataFrame) -> html.Div:
    """
    创建昨日经营诊断卡片 - V3.0 按紧急度分层
    
    两层架构:
    🔴 紧急处理（今日必须完成）
    🟡 关注观察（本周内处理）
    
    功能：
    - 点击按钮可查看详细列表
    - 支持导出Excel
    
    性能优化:
    - Redis缓存诊断数据（TTL=5分钟）
    """
    if df is None or df.empty:
        return None
    
    try:
        print(f"[DEBUG] create_business_diagnosis_card 开始执行, df.shape={df.shape}")
        
        # 🚀 V8.3性能优化：智能缓存键 - 基于门店而非数据形状
        diagnosis = None
        
        # 生成智能缓存键
        def generate_smart_cache_key(df):
            """
            生成智能缓存键
            
            策略：基于门店名称而非数据形状
            - 相同门店组合 → 相同缓存键
            - 不同门店组合 → 不同缓存键
            """
            if '门店名称' in df.columns:
                stores = sorted(df['门店名称'].unique().tolist())
                store_key = '_'.join(stores) if stores else 'all'
            else:
                store_key = 'all'
            
            # 添加日期范围（确保数据更新后缓存失效）
            if '日期' in df.columns:
                date_col = '日期'
            elif '下单时间' in df.columns:
                date_col = '下单时间'
            else:
                date_col = None
            
            if date_col:
                dates = pd.to_datetime(df[date_col])
                date_range = f"{dates.min().strftime('%Y%m%d')}_{dates.max().strftime('%Y%m%d')}"
            else:
                date_range = 'unknown'
            
            return f"diagnosis_v3:{store_key}:{date_range}"
        
        try:
            from redis_cache_manager import REDIS_CACHE_MANAGER
            if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
                cache_key = generate_smart_cache_key(df)
                diagnosis = REDIS_CACHE_MANAGER.get(cache_key)
                if diagnosis is not None:
                    print(f"✅ [缓存命中] 诊断卡片数据")
                    print(f"   缓存键: {cache_key}")
        except Exception as e:
            print(f"⚠️ Redis缓存读取失败: {e}")
        
        # 如果缓存未命中，重新计算
        if diagnosis is None:
            import time
            calc_start = time.time()
            
            diagnosis = get_diagnosis_summary(df)
            
            calc_time = time.time() - calc_start
            print(f"[DEBUG] get_diagnosis_summary 完成: date={diagnosis.get('date')}, 耗时: {calc_time:.2f}秒")
            
            # 保存到Redis缓存
            try:
                from redis_cache_manager import REDIS_CACHE_MANAGER
                if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
                    cache_key = generate_smart_cache_key(df)
                    REDIS_CACHE_MANAGER.set(cache_key, diagnosis, ttl=3600)  # 60分钟缓存
                    print(f"✅ [已缓存] 诊断卡片数据，60分钟有效")
                    print(f"   缓存键: {cache_key}")
            except Exception as e:
                print(f"⚠️ Redis缓存保存失败: {e}")
        
        urgent = diagnosis['urgent']
        watch = diagnosis['watch']
        
        print(f"\n{'='*80}")
        print(f"[DEBUG] 诊断卡片数据:")
        print(f"{'='*80}")
        print(f"[DEBUG] urgent 问题数:")
        print(f"  - overflow(穿底): {urgent['overflow']['count']}")
        print(f"  - delivery(高配送费): {urgent['delivery']['count']}")
        print(f"  - stockout(热销缺货): {urgent['stockout']['count']}")
        print(f"  - price_abnormal(价格异常): {urgent.get('price_abnormal', {}).get('count', 0)}")
        print(f"[DEBUG] watch 问题数:")
        print(f"  - traffic_drop: {watch['traffic_drop']['count']}")
        print(f"  - new_slow: {watch['new_slow']['count']}")
        print(f"  - new_products: {watch['new_products']['count']}")
        print(f"{'='*80}\n")
        
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
            
            # V7.6：获取趋势信息并格式化展示
            overflow_trend = urgent['overflow'].get('trend', {})
            avg_3d = urgent['overflow'].get('avg_3d', 0)
            trend_text = ""
            if overflow_trend and avg_3d > 0:
                trend_icon = overflow_trend.get('icon', '')
                trend_label = overflow_trend.get('label', '')
                trend_text = f"{trend_icon} {trend_label} (前3天均{avg_3d:.0f}单)"
            
            if MANTINE_AVAILABLE:
                urgent_cards.append(
                    dbc.Col([
                        create_mantine_diagnosis_card(
                            title="亏损订单",
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
                # 回退到原始样式（V7.6：添加趋势展示）
                urgent_cards.append(
                    dbc.Col([
                        html.Div([
                            html.Div("💸 亏损订单", className="fw-bold text-danger mb-2"),
                            html.Div([
                                "昨日 ",
                                html.Span(f"{urgent['overflow']['count']}", className="fw-bold text-danger fs-5"),
                                " 单亏损"
                            ], className="mb-1"),
                            html.Div([
                                "累计损失 ",
                                html.Span(f"¥{urgent['overflow']['loss']:,.0f}", className="fw-bold text-danger")
                            ], className="small text-muted mb-1"),
                            # V7.6：添加趋势信息
                            html.Div([
                                html.Small(trend_text, className="text-muted")
                            ], className="mb-1") if trend_text else html.Div(),
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
            
            # V7.6：获取趋势信息并格式化展示
            delivery_trend = urgent['delivery'].get('trend', {})
            avg_3d_delivery = urgent['delivery'].get('avg_3d', 0)
            delivery_trend_text = ""
            if delivery_trend and avg_3d_delivery > 0:
                trend_icon = delivery_trend.get('icon', '')
                trend_label = delivery_trend.get('label', '')
                delivery_trend_text = f"{trend_icon} {trend_label} (前3天均{avg_3d_delivery:.0f}单)"
            
            if MANTINE_AVAILABLE:
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
            else:
                # 回退到原始样式（V7.6：添加趋势展示）
                urgent_cards.append(
                    dbc.Col([
                        html.Div([
                            html.Div("🚚 高配送费预警", className="fw-bold text-warning mb-2"),
                            html.Div([
                                "昨日 ",
                                html.Span(f"{urgent['delivery']['count']}", className="fw-bold text-warning fs-5"),
                                " 单配送净成本>6元"
                            ], className="mb-1"),
                            html.Div([
                                "配送溢价 ",
                                html.Span(f"¥{urgent['delivery']['extra_cost']:,.0f}", className="fw-bold text-warning"),
                                f" | 均¥{avg_extra:.1f}"
                            ], className="small text-muted mb-1"),
                            # V7.6：添加趋势信息
                            html.Div([
                                html.Small(delivery_trend_text, className="text-muted")
                            ], className="mb-1") if delivery_trend_text else html.Div(),
                            html.Div([
                                html.Small(distance_info, className="text-muted")
                            ], className="mb-1") if distance_info else html.Div(),
                            create_channel_badges(urgent['delivery'].get('channels', {})),
                            html.Div([
                                dbc.Button("查看详情 →", id="btn-diagnosis-delivery", color="link", size="sm", className="p-0 text-warning", n_clicks=0)
                            ], className="mt-2")
                        ], className="p-3 bg-warning bg-opacity-10 rounded h-100 border-start border-4 border-warning")
                    ], width=4)
                )
        
        # 3. 热销缺货 - 使用红色(red)表示严重
        # V8.10.1修复：始终创建按钮，避免回调函数找不到ID
        if urgent['stockout']['count'] > 0:
            # 有缺货数据 - 显示警告状态
            # 构建缺货分级徽章（持续缺货 vs 新增缺货）
            persistent_count = urgent['stockout'].get('persistent_count', 0)
            new_count = urgent['stockout'].get('new_count', urgent['stockout']['count'])
            
            stockout_badges = []
            if persistent_count > 0:
                stockout_badges.append({"text": f"持续≥3天 {persistent_count}个", "color": "red"})
            if new_count > 0 and new_count != urgent['stockout']['count']:
                stockout_badges.append({"text": f"新增 {new_count}个", "color": "orange"})
            
            # 如果没有分级信息，使用渠道徽章
            if not stockout_badges:
                stockout_badges = [{"text": f"{ch[:4]} {cnt}", "color": "red"} 
                                  for ch, cnt in list(urgent['stockout']['channels'].items())[:3]]
            
            # 计算平均损失
            avg_loss = urgent['stockout']['loss'] / urgent['stockout']['count'] if urgent['stockout']['count'] > 0 else 0
            
            # 构建extra_info：显示持续缺货警告
            extra_info_text = f"单品均损 ¥{avg_loss:.0f}/天"
            if persistent_count > 0:
                extra_info_text = f"🔴 {persistent_count}个持续缺货≥3天，需优先补货"
            
            urgent_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="热销缺货",
                        icon="tabler:package-off",
                        color="red",
                        main_value=f"{urgent['stockout']['count']}",
                        main_label="个热销品库存为0",
                        sub_info=f"日均损失 ¥{urgent['stockout']['loss']:,.0f}",
                        extra_info=extra_info_text,
                        extra_badges=stockout_badges,
                        button_id="btn-diagnosis-stockout",
                        button_text="生成补货单"
                    )
                ], width=4, className="mb-3")
            )
        else:
            # 没有缺货数据 - 显示良好状态
            urgent_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="热销缺货",
                        icon="tabler:package-check",
                        color="green",
                        main_value="0",
                        main_label="个商品缺货",
                        sub_info="✅ 库存充足",
                        extra_info="所有热销商品库存正常",
                        button_id="btn-diagnosis-stockout",
                        button_text="查看库存"
                    )
                ], width=4, className="mb-3")
            )
        
        # 4. 客户流失预警 - 新增功能 🆕
        churn_card_added = False
        try:
            # 获取商品主数据（需要JOIN库存信息）
            from database.connection import engine
            
            # 确保事务干净
            try:
                with engine.connect() as conn:
                    products_df = pd.read_sql("SELECT product_name, stock FROM products", conn)
            except Exception as db_error:
                print(f"[WARNING] 首次查询失败，尝试重连: {db_error}")
                try:
                    engine.dispose()
                    with engine.connect() as conn:
                        products_df = pd.read_sql("SELECT product_name, stock FROM products", conn)
                except:
                    raise db_error
            
            print(f"[DEBUG] 客户流失分析：products_df.shape={products_df.shape}")
            print(f"[DEBUG] 客户流失分析：df.columns={list(df.columns)[:10]}")  # 打印前10个字段名
            print(f"[DEBUG] 客户流失分析：df.shape={df.shape}")
            
            # 调用客户流失分析
            churn_result = get_customer_churn_warning(
                df, 
                products_df, 
                today=pd.Timestamp.now(),
                lookback_days=30,
                min_orders=2,
                no_order_days=7
            )
            
            print(f"[DEBUG] 客户流失分析：total_churn={churn_result['summary']['total_churn']}")
            
            summary = churn_result['summary']
            data_date = summary.get('data_date', '未知')
            
            # 即使没有流失客户，也显示卡片（显示0）
            if summary['total_churn'] > 0:
                # 有流失客户，显示详细信息
                # 构建原因分析徽章（包含数据时点）
                churn_badges = [
                    {"text": f"📅 {data_date}", "color": "gray"}  # 数据时点
                ]
                if summary['out_of_stock'] > 0:
                    churn_badges.append({"text": f"🚫缺货 {summary['out_of_stock']}", "color": "red"})
                if summary['price_increased'] > 0:
                    churn_badges.append({"text": f"💰涨价 {summary['price_increased']}", "color": "orange"})
                if summary['delisted'] > 0:
                    churn_badges.append({"text": f"❌下架 {summary['delisted']}", "color": "gray"})
                if summary['unknown'] > 0:
                    churn_badges.append({"text": f"❓其他 {summary['unknown']}", "color": "blue"})
                
                # 构建extra_info：显示高价值客户信息
                extra_info_churn = None
                if summary.get('high_value_count', 0) > 0:
                    extra_info_churn = (
                        f"⭐ {summary['high_value_count']}个高价值客户 "
                        f"(总LTV ¥{summary['high_value_ltv']:,.0f})"
                    )
                
                # 获取建议行动（显示第一条）
                actions = get_recommended_actions(churn_result)
                first_action = actions[0] if actions else "发放召回优惠券"
                
                urgent_cards.append(
                    dbc.Col([
                        create_mantine_diagnosis_card(
                            title="客户流失预警",
                            icon="tabler:user-exclamation",
                            color="violet",
                            main_value=f"{summary['total_churn']}",
                            main_label="个老客超7天未下单",
                            sub_info="流失原因分析↓",
                            extra_info=extra_info_churn,
                            extra_badges=churn_badges if churn_badges else None,
                            button_id="btn-diagnosis-churn",
                            button_text="查看详情"
                        )
                    ], width=4, className="mb-3")
                )
                churn_card_added = True
            else:
                # 没有流失客户，显示良好状态
                urgent_cards.append(
                    dbc.Col([
                        create_mantine_diagnosis_card(
                            title="客户流失预警",
                            icon="tabler:user-check",
                            color="green",
                            main_value="0",
                            main_label="个老客流失",
                            sub_info="✅ 客户留存良好",
                            extra_info="所有客户7天内均有下单",
                            button_id="btn-diagnosis-churn",
                            button_text="查看详情"
                        )
                    ], width=4, className="mb-3")
                )
                churn_card_added = True
                
        except Exception as e:
            print(f"[ERROR] 客户流失预警卡片生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 出错也显示卡片，提示异常
            urgent_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="客户流失预警",
                        icon="tabler:alert-circle",
                        color="gray",
                        main_value="--",
                        main_label="数据加载失败",
                        sub_info=f"错误: {str(e)[:30]}",
                        extra_info="请检查数据库连接",
                        button_id="btn-diagnosis-churn",
                        button_text="重试"
                    )
                ], width=4, className="mb-3")
            )
            churn_card_added = True
        
        # 5. 客单价异常诊断 - 双维度分析(客户+商品) 🆕
        try:
            # 先检查是否有order_agg数据
            if 'order_agg' not in locals() and 'order_agg' not in globals():
                # 如果没有order_agg,先生成
                print("🔍 [DEBUG] 卡片生成: 生成 order_agg")
                calculate_order_metrics = get_calculate_order_metrics()
                order_agg = calculate_order_metrics(df, calc_mode='all_with_fallback')
                print(f"🔍 [DEBUG] 卡片生成: order_agg.shape = {order_agg.shape}")
            
            # 默认30天周期
            print("🔍 [DEBUG] 卡片生成: 执行 analyze_customer_downgrade")
            aov_result = analyze_customer_downgrade(df, order_agg, period_days=30)
            print(f"✅ [DEBUG] 卡片生成: analyze_customer_downgrade 执行成功")
            
            summary_aov = aov_result['summary']
            
            # 🎯 新逻辑：展示订单金额分布异常（价格带维度）
            if summary_aov['total_downgrade'] > 0:
                # 有下滑价格带 - 显示警告状态
                aov_badges = []
                if summary_aov['severe_count'] > 0:
                    aov_badges.append({"text": f"🔴重度 {summary_aov['severe_count']}", "color": "red"})
                if summary_aov['moderate_count'] > 0:
                    aov_badges.append({"text": f"🟡中度 {summary_aov['moderate_count']}", "color": "orange"})
                if summary_aov['mild_count'] > 0:
                    aov_badges.append({"text": f"🟢轻度 {summary_aov['mild_count']}", "color": "yellow"})
                
                # 显示客单价变化
                aov_change = summary_aov.get('aov_change_amount', 0)
                extra_info_aov = f"客单价变化: ¥{aov_change:+.1f}"
                
                urgent_cards.append(
                    dbc.Col([
                        create_mantine_diagnosis_card(
                            title="客单价异常诊断",
                            icon="tabler:trending-down",
                            color="pink",
                            main_value=f"{summary_aov['total_downgrade']}",
                            main_label="个价格带订单下滑",
                            sub_info="订单分布分析↓",
                            extra_info=extra_info_aov,
                            extra_badges=aov_badges,
                            button_id="btn-diagnosis-aov",
                            button_text="查看详情"
                        )
                    ], width=4, className="mb-3")
                )
            else:
                # 没有下滑价格带 - 显示良好状态
                urgent_cards.append(
                    dbc.Col([
                        create_mantine_diagnosis_card(
                            title="客单价异常诊断",
                            icon="tabler:chart-line",
                            color="green",
                            main_value="0",
                            main_label="个价格带异常",
                            sub_info="✅ 订单分布稳定",
                            extra_info=f"当前客单价 ¥{summary_aov.get('avg_aov', 0):.2f}",
                            button_id="btn-diagnosis-aov",
                            button_text="查看详情"
                        )
                    ], width=4, className="mb-3")
                )
            
        except Exception as e:
            print(f"[ERROR] 客单价异常诊断卡片生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # 出错也显示卡片
            urgent_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="客单价异常诊断",
                        icon="tabler:alert-circle",
                        color="gray",
                        main_value="--",
                        main_label="数据加载失败",
                        sub_info=f"错误: {str(e)[:30]}",
                        extra_info="请检查数据",
                        button_id="btn-diagnosis-aov",
                        button_text="重试"
                    )
                ], width=4, className="mb-3")
            )
        
        # 6. 价格异常预警 - 使用橙色(orange)区分
        # V8.10.1修复：始终创建按钮
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
        else:
            # 没有价格异常 - 显示良好状态
            urgent_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="价格异常",
                        icon="tabler:check-circle",
                        color="green",
                        main_value="0",
                        main_label="个商品价格异常",
                        sub_info="✅ 价格正常",
                        extra_info="所有商品定价合理",
                        button_id="btn-diagnosis-price-abnormal",
                        button_text="查看详情"
                    )
                ], width=4, className="mb-3")
            )
        
        # 6. 销量下滑 - 使用蓝色(blue)区分
        # V8.10.1修复：始终创建按钮
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
        else:
            # 没有销量下滑 - 显示良好状态
            urgent_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="销量下滑",
                        icon="tabler:trending-up",
                        color="green",
                        main_value="0",
                        main_label="个商品销量下滑",
                        sub_info="✅ 销量稳定",
                        extra_info="热销商品表现良好",
                        button_id="btn-diagnosis-traffic",
                        button_text="查看详情"
                    )
                ], width=4, className="mb-3")
            )
        
        # 7. 利润率下滑 - 使用葡萄紫(grape)区分
        # V8.10.1修复：始终创建按钮
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
        else:
            # 没有利润率下滑 - 显示良好状态
            urgent_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="利润率下滑",
                        icon="tabler:arrow-up-right-circle",
                        color="green",
                        main_value="0",
                        main_label="个商品利润率下滑",
                        sub_info="✅ 利润率稳定",
                        extra_info="商品盈利能力良好",
                        button_id="btn-diagnosis-profit-drop",
                        button_text="查看详情"
                    )
                ], width=4, className="mb-3")
            )
        
        # ================== 关注观察层 ==================
        watch_cards = []
        
        # 1. 滞销预警（合并显示）- 使用蓝绿色(cyan)
        # V8.10.1修复：始终创建按钮
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
        else:
            # 没有滞销 - 显示良好状态
            watch_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="滞销积压",
                        icon="tabler:check-circle",
                        color="green",
                        main_value="0",
                        main_label="个SKU滞销",
                        sub_info="✅ 库存周转良好",
                        extra_info="商品动销正常",
                        button_id="btn-diagnosis-slow",
                        button_text="查看详情"
                    )
                ], width=4, className="mb-3")
            )
        
        # 2. 新品表现 - 使用绿色(green)
        # V8.10.1修复：始终创建按钮
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
        else:
            # 没有新品 - 显示提示状态
            watch_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="新品表现",
                        icon="tabler:package",
                        color="gray",
                        main_value="0",
                        main_label="个新品上架",
                        sub_info="暂无新品数据",
                        extra_info="可考虑引入新品",
                        button_id="btn-diagnosis-newproduct",
                        button_text="查看详情"
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
        # V8.10.1修复：始终创建按钮
        hot_products = highlights.get('hot_products', {})
        if hot_products.get('count', 0) > 0:
            top_hot = hot_products.get('top_products', [])[:2]
            # 显示连续增长天数
            hot_badges = []
            for p in top_hot:
                consecutive_days = p.get('consecutive_days', 1)
                if consecutive_days >= 3:
                    hot_badges.append({"text": f"{p['name'][:6]} 🔥连涨{consecutive_days}天", "color": "pink"})
                else:
                    hot_badges.append({"text": f"{p['name'][:6]}+{p['growth']:.0f}%", "color": "pink"})
            
            # 构建extra_info：显示持续爆款数量
            sustained_count = hot_products.get('sustained_count', 0)
            extra_info_hot = f"共销售 {hot_products.get('total_qty', 0)} 件"
            if sustained_count > 0:
                extra_info_hot = f"🔥 {sustained_count}个连续增长≥3天，真爆款！"
            
            highlight_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="爆款商品",
                        icon="tabler:flame",
                        color="pink",
                        main_value=f"{hot_products['count']}",
                        main_label="个商品销量突增",
                        sub_info=f"共销售 {hot_products.get('total_qty', 0)} 件",
                        extra_info=extra_info_hot if sustained_count > 0 else None,
                        extra_badges=hot_badges if hot_badges else None,
                        button_id="btn-diagnosis-hot-products",
                        button_text="查看详情"
                    )
                ], width=4, className="mb-3")
            )
        else:
            # 没有爆款 - 显示提示状态
            highlight_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="爆款商品",
                        icon="tabler:star",
                        color="gray",
                        main_value="0",
                        main_label="个爆款商品",
                        sub_info="暂无突增商品",
                        extra_info="持续关注销量变化",
                        button_id="btn-diagnosis-hot-products",
                        button_text="查看详情"
                    )
                ], width=4, className="mb-3")
            )
        
        # 2. 高利润商品 - 使用靛蓝色(indigo)表示盈利亮点
        # V8.10.1修复：始终创建按钮
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
        else:
            # 没有高利润商品数据 - 显示提示状态
            highlight_cards.append(
                dbc.Col([
                    create_mantine_diagnosis_card(
                        title="高利润商品",
                        icon="tabler:coin",
                        color="gray",
                        main_value="—",
                        main_label="暂无数据",
                        sub_info="持续关注利润贡献",
                        extra_info="优化商品结构",
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
    filtered_df = df if df is not None else None
    if filtered_df is not None and selected_stores and len(selected_stores) > 0:
        if isinstance(selected_stores, str):
            selected_stores = [selected_stores]
        if len(selected_stores) > 0 and '门店名称' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['门店名称'].isin(selected_stores)]
    
    # V8.0 企业级性能优化：使用骨架屏替代简单的加载动画
    diagnosis_section = html.Div([
        html.H5("🔴 紧急处理", className="mb-3 text-danger"),
        create_loading_spinner("正在分析昨日经营数据..."),
        create_diagnosis_card_skeleton()
    ])
    
    # V8.10.3: 创建性能监控面板
    try:
        from components.performance_panel import create_performance_panel
        performance_panel = create_performance_panel(panel_id='today-must-do-performance-panel')
    except Exception as e:
        print(f"⚠️ 性能监控面板创建失败: {e}")
        performance_panel = html.Div()
    
    return html.Div([
        # V8.10.3: 性能监控面板（固定在右上角）
        performance_panel,
        
        # 顶部工具栏
        dbc.Row([
            dbc.Col([
                html.H4("✅ 今日必做 - 智能运营提醒", className="mb-0"),
                html.Small("基于昨日数据自动识别需要关注的运营问题", className="text-muted")
            ], width=12)
        ], className="mb-4 align-items-center"),
        
        dcc.Store(id='selected-product-store'),
        
        # 商品详情弹窗（单品洞察 - 全屏模式）
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("📊 商品详情分析"), id='product-detail-modal-header', className="px-5"),
            dbc.ModalBody(id='product-detail-modal-body', className="px-5"),
            dbc.ModalFooter(
                dbc.Button("关闭", id="product-detail-modal-close", className="ms-auto", n_clicks=0),
                className="px-5"
            ),
        ], id="product-detail-modal", fullscreen=True, is_open=False, scrollable=True),
        
        # 诊断详情弹窗 - 用于查看各类问题的详细列表（全屏模式）
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id='diagnosis-detail-modal-title'), className="px-5"),
            dbc.ModalBody(id='diagnosis-detail-modal-body', className="px-5"),
            dbc.ModalFooter([
                dbc.Button("导出Excel", id="diagnosis-detail-export-btn", color="success", className="me-2", n_clicks=0),
                dbc.Button("关闭", id="diagnosis-detail-modal-close", className="ms-auto", n_clicks=0)
            ], className="px-5"),
        ], id="diagnosis-detail-modal", fullscreen=True, is_open=False, scrollable=True),
        
        # 🆕 单品洞察弹窗 - 用于展示单个商品的深度分析
        dbc.Modal([
            dbc.ModalHeader([
                dbc.ModalTitle(id='product-insight-modal-title'),
                dbc.Button("×", id="product-insight-modal-close", className="btn-close", n_clicks=0)
            ]),
            dbc.ModalBody(id='product-insight-modal-body', className="p-4", style={'backgroundColor': '#f8f9fa'}),
        ], id="product-insight-modal", fullscreen=True, is_open=False, scrollable=True),
        
        # 🆕 订单商品明细弹窗 - 用于查看单个订单中的商品亏损情况
        dbc.Modal([
            dbc.ModalHeader([
                dbc.ModalTitle(id='order-products-modal-title'),
                dbc.Button("×", id="order-products-modal-close", className="btn-close", n_clicks=0)
            ]),
            dbc.ModalBody(id='order-products-modal-body', className="p-4"),
        ], id="order-products-modal", size="xl", is_open=False, scrollable=True),
        
        # 存储当前选中的订单ID（用于订单商品明细）
        dcc.Store(id='selected-order-id-store', data=None),
        
        # 存储当前选中的商品名称（用于单品洞察）
        dcc.Store(id='product-insight-name-store', data=None),
        
        # 存储当前诊断类型
        dcc.Store(id='diagnosis-detail-type-store', data=None),
        dcc.Download(id='diagnosis-download'),
        
        # 经营诊断卡片
        html.Div(id='today-must-do-diagnosis-container', children=diagnosis_section),
        
        # ========== 商品综合分析 ==========
        # V8.0 企业级性能优化：使用骨架屏替代简单的加载动画
        html.Div(id='product-scoring-section-container', 
                 children=html.Div([
                     html.H5("📊 商品健康分析", className="mb-3"),
                     create_loading_spinner("正在加载商品健康数据..."),
                     create_product_health_skeleton()
                 ])),
        
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
                # ==================== 两个Tab模式（删除智能调价Tab） ====================
                dbc.Tabs([
                    # ========== Tab 1: 自由调价（V3.0：六象限联动） ==========
                    dbc.Tab([
                        html.Div([
                            # V3.1：来源信息显示（从六象限跳转时显示）
                            html.Div(id='pricing-source-info', className="mb-3"),
                            
                            # 面包屑导航（来源信息）- V3.0新增（保留兼容）
                            html.Div(id='pricing-source-breadcrumb', className="mb-3", style={'display': 'none'}),
                            
                            # 智能建议 - V3.0新增（保留兼容）
                            html.Div(id='pricing-smart-suggestion', className="mb-3", style={'display': 'none'}),
                            
                            # 六象限商品选择器（方案B：补充功能）- V3.0新增
                            dbc.Card([
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.Span("📊 六象限商品", className="fw-bold me-2"),
                                            html.Small("从六象限分析中选择商品", className="text-muted")
                                        ], width=3),
                                        dbc.Col([
                                            dbc.Button([
                                                html.I(className="fas fa-th me-1"),
                                                "选择象限"
                                            ],
                                            id='pricing-role-quadrant',
                                            color='info',
                                            size="sm",
                                            outline=True
                                            )
                                        ], width=2),
                                        dbc.Col([
                                            html.Div([
                                                dcc.Dropdown(
                                                    id='pricing-quadrant-dropdown',
                                                    options=[],
                                                    placeholder='选择象限...',
                                                    clearable=True,
                                                    style={'fontSize': '13px', 'zIndex': 9999}  # 修复：提高z-index避免被遮挡
                                                )
                                            ], id='pricing-quadrant-selector-container', style={'display': 'none', 'position': 'relative', 'zIndex': 9999})  # 修复：提高z-index
                                        ], width=7),
                                    ], align="center")
                                ], className="py-2")
                            ], className="mb-3 border-info", style={'borderWidth': '1px', 'position': 'relative', 'zIndex': 100}),  # 修复：提高卡片z-index
                            
                            # 📅 独立日期选择器（不受顶部日期影响）
                            dbc.Card([
                                dbc.CardBody([
                                    dbc.Row([
                                        dbc.Col([
                                            html.Div([
                                                html.Span("📅 数据时间范围", className="fw-bold me-3"),
                                                html.Small("独立于顶部日期筛选，用于精准分析", className="text-muted"),
                                            ]),
                                        ], width=4),
                                        dbc.Col([
                                            dbc.RadioItems(
                                                id='calculator-date-range',
                                                options=[
                                                    {'label': '近7天', 'value': 7},
                                                    {'label': '近15天', 'value': 15},
                                                    {'label': '近30天', 'value': 30},
                                                    {'label': '全部数据', 'value': 0},
                                                ],
                                                value=7,
                                                inline=True,
                                                className="d-flex gap-3"
                                            ),
                                        ], width=8, className="text-end"),
                                    ], align="center"),
                                    # 数据范围提示
                                    html.Div(id='calculator-date-info', className="mt-2 small text-muted"),
                                ], className="py-2")
                            ], className="mb-3 border-info", style={'borderWidth': '1px'}),
                            
                            # 🎯 快捷场景入口（新增）
                            dbc.Card([
                                dbc.CardBody([
                                    html.Div([
                                        html.Span("🎯 快捷场景", className="fw-bold me-3"),
                                        html.Small("点击场景按钮直接加载对应商品", className="text-muted"),
                                    ], className="mb-2"),
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Button([
                                                html.Div("📉 利润下滑", className="fw-bold"),
                                                html.Small("利润率降>5%", className="text-muted d-block", style={'fontSize': '10px'}),
                                            ], id='quick-scene-profit-drop', color="danger", outline=True, className="w-100 py-2", size="sm"),
                                        ], width=3),
                                        # 隐藏的利润额下滑按钮（保持回调兼容）
                                        dbc.Button(id='quick-scene-profit-amount-drop', style={'display': 'none'}),
                                        dbc.Col([
                                            dbc.Button([
                                                html.Div("🔻 销量下滑", className="fw-bold"),
                                                html.Small("销量降>20%", className="text-muted d-block", style={'fontSize': '10px'}),
                                            ], id='quick-scene-sales-drop', color="warning", outline=True, className="w-100 py-2", size="sm"),
                                        ], width=2),
                                        dbc.Col([
                                            dbc.Button([
                                                html.Div("🐌 滞销清仓", className="fw-bold"),
                                                html.Small("自动30天 | 最后售卖≥7天前", className="text-muted d-block", style={'fontSize': '10px'}),
                                            ], id='quick-scene-stagnant', color="secondary", outline=True, className="w-100 py-2", size="sm"),
                                        ], width=2),
                                        dbc.Col([
                                            dbc.Button([
                                                html.Div("💡 提价机会", className="fw-bold"),
                                                html.Small("销量稳定+有利润空间", className="text-muted d-block", style={'fontSize': '10px'}),
                                            ], id='quick-scene-price-opportunity', color="success", outline=True, className="w-100 py-2", size="sm"),
                                        ], width=2),
                                        dbc.Col([
                                            dbc.Button([
                                                html.Div("❌ 清除场景", className="fw-bold text-muted"),
                                                html.Small("显示全部商品", className="text-muted d-block", style={'fontSize': '10px'}),
                                            ], id='quick-scene-clear', color="light", outline=False, className="w-100 py-2 border", size="sm"),
                                        ], width=2),
                                    ], className="g-2"),
                                    # 场景统计信息
                                    html.Div(id='quick-scene-stats', className="mt-2 small"),
                                ], className="py-2")
                            ], id='quick-scene-card', className="mb-3 border-primary", style={'borderWidth': '2px'}),
                            # 当前场景提示
                            html.Div(id='quick-scene-alert', className="mb-2"),
                            # 存储当前快捷场景
                            dcc.Store(id='quick-scene-store', data=None),
                            # 多条件筛选区（简化版）
                            dbc.Row([
                                dbc.Col([
                                    html.Label("一级分类:", className="fw-bold mb-1"),
                                    dcc.Dropdown(id='free-pricing-category', options=[], value=None, placeholder="全部分类", clearable=True, style={'fontSize': '12px'})
                                ], width=2),
                                dbc.Col([
                                    html.Label("价格区间:", className="fw-bold mb-1"),
                                    dbc.Row([
                                        dbc.Col(dbc.Input(id='free-pricing-price-min', type="number", placeholder="最低¥", size="sm"), width=6),
                                        dbc.Col(dbc.Input(id='free-pricing-price-max', type="number", placeholder="最高¥", size="sm"), width=6),
                                    ], className="g-1")
                                ], width=2),
                                dbc.Col([
                                    html.Label("调整方式:", className="fw-bold mb-1"),
                                    dbc.Select(id='free-pricing-adjust-type', options=[
                                        {'label': '按百分比涨/降', 'value': 'percent'},
                                        {'label': '按固定金额涨/降', 'value': 'fixed'},
                                        {'label': '设置目标利润率', 'value': 'target_margin'},
                                    ], value='percent', size="sm")
                                ], width=2),
                                dbc.Col([
                                    html.Label("调整值:", className="fw-bold mb-1"),
                                    dbc.InputGroup([
                                        dbc.Input(id='free-pricing-adjust-value', type="number", value=5, step=0.1, size="sm"),
                                        dbc.InputGroupText(id='free-pricing-adjust-unit', children="%", className="bg-light"),
                                    ], size="sm")
                                ], width=2),
                                dbc.Col([
                                    html.Label("商品搜索:", className="fw-bold mb-1"),
                                    dbc.Input(id='free-pricing-search', type="text", placeholder="商品名称或店内码...", size="sm")
                                ], width=2),
                                dbc.Col([
                                    html.Label("渠道:", className="fw-bold mb-1"),
                                    dcc.Dropdown(id='free-pricing-channel', options=[{'label': '全部渠道', 'value': 'all'}], value='all', clearable=False, style={'fontSize': '12px'})
                                ], width=2),
                            ], className="mb-2"),
                            # 隐藏的输入框（保持回调兼容性）
                            html.Div([
                                dbc.Input(id='free-pricing-profit-min', type="hidden", value=None),
                                dbc.Input(id='free-pricing-profit-max', type="hidden", value=None),
                                dbc.Input(id='free-pricing-sales-min', type="hidden", value=None),
                                dbc.Input(id='free-pricing-sales-max', type="hidden", value=None),
                            ], style={'display': 'none'}),
                            dbc.Row([
                                dbc.Col([
                                    html.Label("　", className="d-block mb-1"),
                                    dbc.ButtonGroup([
                                        dbc.Button([html.I(className="fas fa-search me-1"), "🔍 筛选商品"], id='free-pricing-filter-btn', color="primary", size="sm", className="px-4"),
                                        dbc.Button([html.I(className="fas fa-calculator me-1"), "批量计算"], id='free-pricing-calc-btn', color="success", outline=True, size="sm"),
                                    ]),
                                    # 静态提示：显示当前设置
                                    html.Div(id='free-pricing-current-settings', className="text-muted small mt-1"),
                                    # 隐藏的全选按钮（保持回调兼容）
                                    dbc.Button(id='free-pricing-select-all-btn', style={'display': 'none'}),
                                ], width=12, className="text-end"),
                            ], className="mb-3"),
                            # 计算完成提示
                            html.Div(id='free-pricing-calc-alert', className="mb-2"),
                            # 统计信息
                            html.Div(id='free-pricing-stats', className="mb-2"),
                            # 结果表格
                            dcc.Loading(id='loading-free-pricing', type='circle', children=[html.Div(id='free-pricing-table-container')]),
                            # 存储
                            dcc.Store(id='free-pricing-data-store', data=None),
                            
                            # 隐藏的占位组件（防止回调报错）- V3.0新增
                            html.Div([
                                dcc.Store(id='pricing-role-store', data='loss'),
                                dcc.Dropdown(id='pricing-source-dropdown', options=[{'label': '全部', 'value': 'all'}], value='all', style={'display': 'none'}),
                                dbc.Button(id='pricing-role-promo', style={'display': 'none'}),
                                dbc.Button(id='pricing-role-lowfreq', style={'display': 'none'}),
                                dbc.Button(id='pricing-role-star', style={'display': 'none'}),
                                dbc.Button(id='pricing-role-cash', style={'display': 'none'}),
                                dbc.Button(id='pricing-role-potential', style={'display': 'none'}),
                                dbc.Button(id='pricing-role-all', style={'display': 'none'}),
                                dbc.Button(id='pricing-role-loss', style={'display': 'none'}),
                                dbc.Button(id='pricing-role-volume', style={'display': 'none'}),
                                dbc.Button(id='pricing-role-slow', style={'display': 'none'}),
                                dbc.Button(id='pricing-role-traffic', style={'display': 'none'}),
                                dbc.Button(id='pricing-direction-up', style={'display': 'none'}),
                                dbc.Button(id='pricing-direction-down', style={'display': 'none'}),
                                dcc.Store(id='pricing-direction-store', data='down'),
                                html.Div(id='pricing-direction-hint', style={'display': 'none'}),
                                dcc.Dropdown(id='pricing-channel-filter', options=[{'label': '全部渠道', 'value': 'all'}], value='all', style={'display': 'none'}),
                                dbc.Input(id='pricing-target-margin-v2', type="hidden", value=15),
                                dbc.Button(id='pricing-calculate-btn', style={'display': 'none'}),
                                html.Div(id='pricing-batch-status', style={'display': 'none'}),
                                dcc.Store(id='pricing-v2-data-store', data=None),
                                html.Div(id='pricing-floor-alert-container', style={'display': 'none'}),
                                html.Div(id='pricing-summary-container', style={'display': 'none'}),
                                html.Div(id='pricing-table-container', style={'display': 'none'}),
                            ], style={'display': 'none'}),
                        ], className="pt-3"),
                    ], label="🎯 自由调价", tab_id="tab-free", className="py-2"),
                    
                    # ========== Tab 3: 目标导向（暂时禁用，优化中） ==========
                    dbc.Tab([
                        html.Div([
                            dbc.Alert([
                                html.H4([html.I(className="fas fa-tools me-2"), "功能优化中"], className="alert-heading"),
                                html.Hr(),
                                html.P([
                                    "🚀 目标导向调价功能正在重新设计优化，敬请期待！",
                                ], className="mb-2"),
                                html.P([
                                    html.Strong("预计功能："),
                                    html.Ul([
                                        html.Li("输入利润目标，系统自动反推最优调价方案"),
                                        html.Li("支持多种优化目标：日利润提升、目标利润率等"),
                                        html.Li("智能优先级：按利润贡献、销量、弹性系数等排序"),
                                        html.Li("约束条件：最大涨降幅、排除特定分类/角色"),
                                    ], className="mb-0 small")
                                ]),
                            ], color="info", className="text-center"),
                            # 隐藏的占位组件（防止回调报错，保留后端代码可用）
                            html.Div([
                                dcc.Store(id='goal-pricing-data-store', data=None),
                                html.Div(id='goal-pricing-current-status', style={'display': 'none'}),
                                html.Div(id='goal-pricing-result-container', style={'display': 'none'}),
                                dbc.Input(id='goal-pricing-target-type', type="hidden", value='profit_increase'),
                                dbc.Input(id='goal-pricing-target-value', type="hidden", value=500),
                                dbc.Input(id='goal-pricing-target-unit', type="hidden"),
                                dbc.Input(id='goal-pricing-max-up', type="hidden", value=20),
                                dbc.Input(id='goal-pricing-max-down', type="hidden", value=15),
                                dcc.Dropdown(id='goal-pricing-exclude-category', options=[], value=[], style={'display': 'none'}),
                                dcc.Dropdown(id='goal-pricing-exclude-role', options=[], value=[], style={'display': 'none'}),
                                dbc.Select(id='goal-pricing-priority', options=[], value='profit_contribution', style={'display': 'none'}),
                                dbc.Button(id='goal-pricing-calc-btn', style={'display': 'none'}),
                            ], style={'display': 'none'}),
                        ], className="pt-3"),
                    ], label="🚀 目标导向", tab_id="tab-goal", className="py-2", disabled=False),
                ], id="pricing-tabs", active_tab="tab-free", className="nav-fill"),
                
                # 使用说明（根据Tab切换）
                dbc.Card([
                    dbc.CardBody([
                        html.H6("📋 使用说明", className="text-muted mb-2"),
                        html.Div(id='pricing-tab-help', children=[
                            html.P([
                                html.Strong("🎯 自由调价："), "多条件筛选，自定义涨降幅度，支持快捷场景一键筛选",
                            ], className="mb-1 small"),
                            html.P([
                                html.Strong("⚠️ 保本底线："), "任何调价不会低于成本价"
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
                ),
                
                # 保留旧版隐藏组件（兼容性）
                html.Div([
                    dbc.RadioItems(id='pricing-adjust-direction', options=[{'label': '提价', 'value': 'up'}], value='up', style={'display': 'none'}),
                    dbc.RadioItems(id='pricing-adjust-mode', options=[{'label': '智能', 'value': 'smart'}], value='smart', style={'display': 'none'}),
                    dbc.Input(id='pricing-target-margin', type="hidden", value=15),
                    dbc.Input(id='pricing-adjust-value', type="hidden", value=10),
                    dbc.Button(id='pricing-batch-1', style={'display': 'none'}),
                    dbc.Button(id='pricing-batch-3', style={'display': 'none'}),
                    dbc.Button(id='pricing-batch-5', style={'display': 'none'}),
                    dbc.Button(id='pricing-batch-10', style={'display': 'none'}),
                    dbc.Button(id='pricing-batch-target', style={'display': 'none'}),
                    dbc.Button(id='pricing-level-light', style={'display': 'none'}),
                    dbc.Button(id='pricing-level-medium', style={'display': 'none'}),
                    dbc.Button(id='pricing-level-heavy', style={'display': 'none'}),
                    dcc.Store(id='pricing-smart-level-store', data='medium'),
                    html.Div(id='pricing-smart-level-container', style={'display': 'none'}),
                    html.Div(id='pricing-manual-input-container', style={'display': 'none'}),
                    html.Div(id='pricing-level-hint', style={'display': 'none'}),
                    html.Div(id='pricing-quick-buttons-container', style={'display': 'none'}),
                    html.Div(id='pricing-floor-warning', style={'display': 'none'}),
                ], style={'display': 'none'})
            ])
        ], id='pricing-calculator-card', className="mb-4 shadow-sm border-0"),  # 添加id用于滚动定位
        
        # 调价方案导出下载
        dcc.Download(id='pricing-download'),
        # 存储调价数据
        dcc.Store(id='pricing-data-store', data=None),
        dcc.Store(id='pricing-selected-product', data=None),
        
        # V3.1：联动功能所需的虚拟Store组件
        dcc.Store(id='pricing-scroll-trigger', data=None),
        dcc.Store(id='pricing-back-trigger', data=None),
        dcc.Store(id='pricing-quadrant-filter', data=None),
        dcc.Store(id='pricing-source-context', data=None),
        
        # ========== 隐藏的按钮占位符 ==========
        # 这些按钮可能不会在诊断卡片中显示（取决于数据），但回调需要它们存在
        html.Div([
            dbc.Button(id="btn-diagnosis-traffic", n_clicks=0, style={'display': 'none'}),
            dbc.Button(id="btn-diagnosis-slow", n_clicks=0, style={'display': 'none'}),
        ], style={'display': 'none'})
    ], className="p-3")


def create_product_detail_content(df: pd.DataFrame, product_name: str) -> html.Div:
    """
    创建商品详情弹窗内容 - 增强版 (与渠道表现对比的单品洞察保持一致)
    
    包含:
    - 6个核心指标卡片（总销量、总销售额、平均单价、毛利率、总利润、订单均利润）
    - 单品日记（购买角色拆解）
    - 最佳拍档（Top 5 连带 + 分类信息）
    - 时段画像（24h热度 + 利润率）
    - 价格敏感度趋势（销量 vs 单价 + 利润率曲线）
    - 智能洞察与建议
    """
    # 使用增强版单品洞察数据
    insight_data = get_product_insight_enhanced(df, product_name)
    
    if insight_data.get('error'):
        return dbc.Alert(insight_data['error'], color="danger")
    
    summary = insight_data['summary']
    daily_trend = insight_data['daily_trend']
    hourly_trend = insight_data['hourly_trend']
    partners = insight_data['partners']
    role_daily = insight_data['role_daily']
    price_sensitivity = insight_data['price_sensitivity']
    recommendations = insight_data['recommendations']
    
    # ========== 1. 顶部核心指标卡片 (6个) ==========
    def create_stat_card(title, value, subtitle, icon, color):
        """创建统计卡片"""
        color_map = {
            'primary': '#0d6efd', 'success': '#198754', 'warning': '#ffc107',
            'danger': '#dc3545', 'info': '#0dcaf0', 'secondary': '#6c757d',
            'purple': '#6f42c1'
        }
        bg_color = color_map.get(color, '#0d6efd')
        return dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Span(icon, style={'fontSize': '20px'}),
                    html.H5(value, className="mb-0 ms-2 d-inline", style={'fontSize': '16px'})
                ], className="d-flex align-items-center justify-content-center"),
                html.P(title, className="text-muted small mb-0 mt-1 text-center", style={'fontSize': '12px'}),
                html.Small(subtitle, className="text-muted", style={'fontSize': '10px'})
            ], className="text-center py-2")
        ], style={'borderTop': f'3px solid {bg_color}'}, className="h-100")
    
    # 判断利润颜色
    profit_color = "danger" if summary['total_profit'] < 0 else "success"
    avg_profit_color = "danger" if summary['avg_profit_per_order'] < 0 else "info"
    
    metrics_row = dbc.Row([
        dbc.Col(create_stat_card(
            "总销量", f"{summary['total_quantity']}单", 
            "累计订单数", "📦", "primary"
        ), width=2),
        dbc.Col(create_stat_card(
            "总销售额", f"¥{summary['total_sales']:,.0f}", 
            "累计销售", "💰", "warning"
        ), width=2),
        dbc.Col(create_stat_card(
            "总利润", f"¥{summary['total_profit']:,.0f}", 
            "累计利润", "💵", profit_color
        ), width=2),
        dbc.Col(create_stat_card(
            "平均单价", f"¥{summary['avg_price']:.1f}", 
            "实收/销量", "🏷️", "info"
        ), width=2),
        dbc.Col(create_stat_card(
            "毛利率", f"{summary['avg_margin']:.1f}%", 
            "利润/销售额", "📈", 
            "danger" if summary['avg_margin'] < 15 else "success"
        ), width=2),
        dbc.Col(create_stat_card(
            "订单均利润", f"¥{summary['avg_profit_per_order']:.1f}", 
            "单均利润", "📊", avg_profit_color
        ), width=2),
    ], className="mb-4")
    
    # ========== 2. 图表区域 (ECharts) ==========
    charts_row1 = html.Div()
    charts_row2 = html.Div()
    
    if ECHARTS_AVAILABLE:
        # ===== 图表A: 单品日记（购买角色拆解）=====
        fig_journal = html.Div("暂无角色数据", className="text-muted text-center p-5")
        if not role_daily.empty:
            # 转换为ECharts堆叠柱状图格式
            dates = sorted(role_daily['日期'].unique())
            roles = ['核心需求', '凑单配角', '亏损引流']
            role_colors = {'核心需求': '#2ecc71', '凑单配角': '#3498db', '亏损引流': '#e74c3c'}
            
            series_data = []
            for role in roles:
                role_df = role_daily[role_daily['角色'] == role]
                values = []
                for d in dates:
                    v = role_df[role_df['日期'] == d]['销量'].sum()
                    values.append(int(v))
                series_data.append({
                    'name': role,
                    'type': 'bar',
                    'stack': 'total',
                    'data': values,
                    'itemStyle': {'color': role_colors.get(role, '#999')},
                    'emphasis': {'focus': 'series'}
                })
            
            # 计算核心需求占比
            core_count = role_daily[role_daily['角色'] == '核心需求']['销量'].sum()
            total_count = role_daily['销量'].sum()
            core_ratio = (core_count / total_count * 100) if total_count > 0 else 0
            
            # 格式化日期为 MM-DD 格式
            dates_str = [pd.to_datetime(d).strftime('%m-%d') for d in dates]
            
            journal_option = {
                'title': {'text': f'📊 单品日记 (核心需求占比: {core_ratio:.1f}%)', 'left': 'center', 'top': 5,
                          'textStyle': {'fontSize': 14, 'fontWeight': 'bold'}},
                'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'},
                           'formatter': '{b}<br/>{a0}: {c0}单<br/>{a1}: {c1}单<br/>{a2}: {c2}单'},
                'legend': {'data': roles, 'bottom': 5},
                'grid': {'left': '3%', 'right': '4%', 'bottom': '18%', 'top': '18%', 'containLabel': True},
                'xAxis': {'type': 'category', 'data': dates_str, 
                          'axisLabel': {'rotate': 45, 'fontSize': 10}},
                'yAxis': {'type': 'value', 'name': '销量'},
                'series': series_data
            }
            fig_journal = DashECharts(option=journal_option, style={'height': '320px', 'width': '100%'})
        
        # ===== 图表B: 最佳拍档（Top 5 连带 + 分类信息）=====
        fig_partner = html.Div("暂无连带数据", className="text-muted text-center p-5")
        if not partners.empty:
            top5 = partners.head(5)
            # 构建带分类的标签
            labels = []
            for _, row in top5.iterrows():
                category = row.get('一级分类', '-')
                if category and category != '-':
                    labels.append(f"{row['商品名称'][:10]}({category})")
                else:
                    labels.append(row['商品名称'][:12])
            
            partner_option = {
                'title': {'text': '🤝 最佳拍档 (Top 5 连带)', 'left': 'center', 'top': 5,
                          'textStyle': {'fontSize': 14, 'fontWeight': 'bold'}},
                'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
                'grid': {'left': '3%', 'right': '12%', 'bottom': '3%', 'top': '15%', 'containLabel': True},
                'xAxis': {'type': 'value', 'name': '连带频次'},
                'yAxis': {'type': 'category', 'data': labels[::-1],
                          'axisLabel': {'fontSize': 10, 'width': 120, 'overflow': 'truncate'}},
                'series': [{
                    'type': 'bar',
                    'data': top5['频次'].tolist()[::-1],
                    'itemStyle': {'color': '#667eea'},
                    'label': {'show': True, 'position': 'right', 'fontSize': 11, 'formatter': '{c}次'}
                }]
            }
            fig_partner = DashECharts(option=partner_option, style={'height': '320px', 'width': '100%'})
        
        # ===== 图表C: 时段画像（24h热度 + 利润率）=====
        fig_hourly = html.Div("暂无时段数据", className="text-muted text-center p-5")
        if not hourly_trend.empty:
            # 找出销量高峰时段
            peak_hour = hourly_trend.loc[hourly_trend['销量'].idxmax(), '小时'] if hourly_trend['销量'].sum() > 0 else 0
            
            # 确保hourly_trend按小时排序，并填充缺失时段
            hourly_trend_sorted = hourly_trend.sort_values('小时').reset_index(drop=True)
            
            hourly_option = {
                'title': {'text': f'⏰ 时段画像 (高峰: {int(peak_hour)}时)', 'left': 'center', 'top': 5,
                          'textStyle': {'fontSize': 14, 'fontWeight': 'bold'}},
                'tooltip': {'trigger': 'axis',
                           'formatter': '{b}<br/>销量: {c0}单<br/>利润率: {c1}%'},
                'legend': {'data': ['销量', '实收利润率'], 'bottom': 5},
                'grid': {'left': '3%', 'right': '4%', 'bottom': '18%', 'top': '18%', 'containLabel': True},
                'xAxis': {'type': 'category', 'data': [f'{h}时' for h in range(24)],
                          'axisLabel': {'fontSize': 10, 'interval': 0}},  # interval: 0 强制显示所有标签
                'yAxis': [
                    {'type': 'value', 'name': '销量', 'position': 'left'},
                    {'type': 'value', 'name': '利润率%', 'position': 'right',
                     'axisLabel': {'formatter': '{value}%'}}
                ],
                'series': [
                    {'name': '销量', 'type': 'bar',
                     'data': [int(x) for x in hourly_trend_sorted['销量'].tolist()],
                     'itemStyle': {'color': 'rgba(102, 126, 234, 0.7)'}},
                    {'name': '实收利润率', 'type': 'line', 'yAxisIndex': 1,
                     'data': hourly_trend_sorted['实收利润率'].tolist(),
                     'smooth': True,
                     'lineStyle': {'color': '#e74c3c', 'width': 2},
                     'itemStyle': {'color': '#e74c3c'}}
                ]
            }
            fig_hourly = DashECharts(option=hourly_option, style={'height': '320px', 'width': '100%'})
        
        # ===== 图表D: 价格敏感度趋势（销量 vs 单价 + 利润率）=====
        fig_price = html.Div("暂无趋势数据", className="text-muted text-center p-5")
        if not daily_trend.empty:
            # 格式化日期为 MM-DD 格式
            dates_str = [pd.to_datetime(d).strftime('%m-%d') for d in daily_trend['日期'].tolist()]
            
            # 计算最近趋势
            if len(daily_trend) >= 7:
                recent_margin = daily_trend['实收利润率'].tail(3).mean()
                early_margin = daily_trend['实收利润率'].head(3).mean()
                margin_trend = "↑" if recent_margin > early_margin else "↓"
                margin_diff = recent_margin - early_margin
            else:
                margin_trend = ""
                margin_diff = 0
            
            price_option = {
                'title': {'text': f'🏷️ 价格敏感度趋势 (利润率{margin_trend}{abs(margin_diff):.1f}%)', 
                          'left': 'center', 'top': 5,
                          'textStyle': {'fontSize': 14, 'fontWeight': 'bold'}},
                'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'cross'},
                           'formatter': '{b}<br/>销量: {c0}单<br/>均价: ¥{c1}<br/>实收利润率: {c2}%<br/>定价利润率: {c3}%'},
                'legend': {'data': ['销量', '平均单价', '实收利润率', '定价利润率'], 'bottom': 5, 'itemWidth': 15},
                'grid': {'left': '3%', 'right': '8%', 'bottom': '18%', 'top': '18%', 'containLabel': True},
                'xAxis': {'type': 'category', 'data': dates_str, 
                          'axisLabel': {'rotate': 45, 'fontSize': 10}},
                'yAxis': [
                    {'type': 'value', 'name': '销量', 'position': 'left', 'min': 0},
                    {'type': 'value', 'name': '单价/利润率', 'position': 'right'}
                ],
                'series': [
                    {'name': '销量', 'type': 'bar', 
                     'data': [int(x) for x in daily_trend['销量'].tolist()],
                     'itemStyle': {'color': 'rgba(102, 126, 234, 0.6)'}},
                    {'name': '平均单价', 'type': 'line', 'yAxisIndex': 1,
                     'data': daily_trend['平均单价'].tolist(),
                     'lineStyle': {'color': '#ff9900', 'width': 2},
                     'itemStyle': {'color': '#ff9900'}},
                    {'name': '实收利润率', 'type': 'line', 'yAxisIndex': 1,
                     'data': daily_trend['实收利润率'].tolist(),
                     'lineStyle': {'color': '#2ecc71', 'width': 2, 'type': 'solid'},
                     'itemStyle': {'color': '#2ecc71'}},
                    {'name': '定价利润率', 'type': 'line', 'yAxisIndex': 1,
                     'data': daily_trend['定价利润率'].tolist(),
                     'lineStyle': {'color': '#9b59b6', 'width': 2, 'type': 'dashed'},
                     'itemStyle': {'color': '#9b59b6'}}
                ]
            }
            fig_price = DashECharts(option=price_option, style={'height': '320px', 'width': '100%'})
        
        # 组合图表行
        charts_row1 = dbc.Row([
            dbc.Col(fig_journal, width=6),
            dbc.Col(fig_partner, width=6),
        ], className="mb-3")
        
        charts_row2 = dbc.Row([
            dbc.Col(fig_hourly, width=6),
            dbc.Col(fig_price, width=6),
        ], className="mb-3")
    
    # ========== 3. 智能洞察与建议 ==========
    # 价格敏感度洞察 (增强版)
    sensitivity_badge_color = {
        'red': 'danger', 'orange': 'warning', 'green': 'success', 
        'blue': 'info', 'gray': 'secondary'
    }
    
    # 计算额外洞察
    role_insight = ""
    if not role_daily.empty:
        core_count = role_daily[role_daily['角色'] == '核心需求']['销量'].sum()
        sidekick_count = role_daily[role_daily['角色'] == '凑单配角']['销量'].sum()
        loss_count = role_daily[role_daily['角色'] == '亏损引流']['销量'].sum()
        total_count = role_daily['销量'].sum()
        if total_count > 0:
            core_pct = core_count / total_count * 100
            if core_pct > 70:
                role_insight = f"🎯 核心商品 (主买占比{core_pct:.0f}%)"
            elif loss_count / total_count > 0.3:
                role_insight = f"⚠️ 引流商品 (亏损占比{loss_count/total_count*100:.0f}%)"
            elif sidekick_count / total_count > 0.4:
                role_insight = f"🛒 凑单商品 (配角占比{sidekick_count/total_count*100:.0f}%)"
    
    sensitivity_card = dbc.Card([
        dbc.CardHeader("💡 价格敏感度洞察", className="fw-bold"),
        dbc.CardBody([
            html.Div([
                html.Span("敏感度评级: ", className="fw-bold"),
                dbc.Badge(
                    price_sensitivity.get('level', '数据不足'), 
                    color=sensitivity_badge_color.get(price_sensitivity.get('color', 'gray'), 'secondary'),
                    className="ms-2"
                )
            ], className="mb-2"),
            html.P(f"价格-销量相关系数: {price_sensitivity.get('correlation', 0):.2f}", 
                   className="text-muted small mb-1"),
            html.Small("(系数越接近-1表示越敏感，降价能带来销量提升)", className="text-muted d-block mb-2"),
            html.Hr(className="my-2") if role_insight else None,
            html.Div([
                html.Span("商品角色: ", className="fw-bold small"),
                html.Span(role_insight, className="small")
            ]) if role_insight else None
        ])
    ])
    
    # 推荐行动方案
    recommendation_alerts = []
    for rec in recommendations:
        recommendation_alerts.append(
            dbc.Alert([
                html.H6(rec['title'], className="alert-heading mb-1"),
                html.P(rec['desc'], className="mb-0 small")
            ], color=rec['type'], className="mb-2 py-2")
        )
    
    recommendation_card = dbc.Card([
        dbc.CardHeader("🎯 推荐行动方案", className="fw-bold"),
        dbc.CardBody(recommendation_alerts if recommendation_alerts else [
            html.P("暂无特别建议", className="text-muted")
        ])
    ])
    
    insights_row = dbc.Row([
        dbc.Col(sensitivity_card, width=6),
        dbc.Col(recommendation_card, width=6),
    ])
    
    # ========== 毛利/净利说明提示 ==========
    profit_note = dbc.Alert([
        html.Div([
            html.Span("📌 利润说明：", className="fw-bold"),
            html.Span("本页展示的是", className="ms-1"),
            html.Strong("商品毛利", className="text-success"),
            html.Span("（= 实收金额 - 商品采购成本），反映单品本身的盈利能力。", className="ms-1"),
        ]),
        html.Div([
            html.Small([
                "区别于",
                html.Strong("订单净利润", className="text-primary mx-1"),
                "（= 商品毛利 - 平台服务费 - 物流配送费 + 企客后返），净利润在「订单数据概览」Tab中体现。"
            ], className="text-muted")
        ], className="mt-1")
    ], color="light", className="mb-0 py-2 border-start border-4 border-info")
    
    # ========== 组装完整布局 ==========
    return html.Div([
        metrics_row,
        charts_row1,
        charts_row2,
        insights_row,
        html.Hr(className="my-3"),
        profit_note
    ])


# ==================== 智能调价计算器 V2.0 ====================
# 独立数据处理，不依赖诊断卡片

def identify_product_role(
    discount_rate: float,
    profit_rate: float,
    marketing_ratio: float,
    sales_percentile: float,
    daily_sales: float
) -> tuple:
    """
    识别商品角色（10种）
    
    注意：此角色分类基于【销售数据】，与"滞销品"（基于滞销天数+库存）是不同概念
    
    判断优先级（从高到低）：
    1. 引流款 - 折扣率<30% 或 (营销占比>15% 且 利润率<5%)
    2. 特价款 - 30%≤折扣率<50%
    3. 亏损款 - 利润率<0
    4. 低频款 - 销量排名后10%（动销极差）
    5. 明星款 - 高盈利(>20%) + 高动销(前30%) + 低营销(<10%)
    6. 现金牛 - 高盈利 + 高动销 + 高营销
    7. 走量款 - 低盈利(5-20%) + 高动销
    8. 潜力款 - 高盈利 + 中低动销（非前30%）
    9. 低动销款 - 低盈利(<20%) + 低动销(后30%) - 注意与"滞销品"不同
    10. 正常款 - 其他
    
    Args:
        discount_rate: 折扣率（0-1），如0.3表示3折
        profit_rate: 利润率（%），如15表示15%
        marketing_ratio: 营销占比（%），如10表示10%
        sales_percentile: 销量排名百分位（0-1），如0.9表示前10%
        daily_sales: 日均销量
    
    Returns:
        (角色名称, 角色图标, 调价建议, 是否允许调价, 建议方向)
        建议方向: 'up'=提价, 'down'=降价, 'none'=不建议, 'optional'=可选
    """
    # ========== 策略性低价商品优先判断（不应强制提价） ==========
    
    # 1. 引流款（折扣极低 < 30%，或高营销投入）- 策略性低价，仍允许调价
    if discount_rate < 0.30:
        if profit_rate < 0:
            return ('引流款', '🚀', '引流商品(亏损引流)', True, 'optional')
        else:
            return ('引流款', '🚀', '引流商品', True, 'optional')
    
    # 2. 特价款（折扣 30%-50%）- 促销商品，仍允许调价
    if 0.30 <= discount_rate < 0.50:
        if profit_rate < 0:
            return ('特价款', '🏷️', '特价商品(微亏促销)', True, 'optional')
        else:
            return ('特价款', '🏷️', '促销商品', True, 'optional')
    
    # 3. 高营销投入的引流款（营销占比>15% 且 利润率<5%）- 仍允许调价
    if marketing_ratio > 15 and profit_rate < 5:
        return ('引流款', '🚀', '营销引流商品', True, 'optional')
    
    # ========== 非策略性亏损商品（需要提价止损） ==========
    
    # 4. 亏损款（利润率<0，但不是引流/特价款）- 必须提价
    if profit_rate < 0:
        return ('亏损款', '🔴', '非策略性亏损，必须提价止损', True, 'up')
    
    # ========== 其他正常分类 ==========
    
    # 5. 低频款 - 销量排名后10%，仍允许调价
    if sales_percentile < 0.10:
        return ('低频款', '📦', '销量较低，可调价促销', True, 'optional')
    
    # 定义高/低阈值
    high_profit = profit_rate > 20
    high_sales = sales_percentile >= 0.7  # 前30%
    low_sales = sales_percentile < 0.3    # 后30%
    high_marketing = marketing_ratio > 10
    
    # 6. 明星款
    if high_profit and high_sales and not high_marketing:
        return ('明星款', '🌟', '核心商品，可小幅提价', True, 'optional')
    
    # 7. 现金牛
    if high_profit and high_sales and high_marketing:
        return ('现金牛', '💰', '高利润，可试探提价', True, 'optional')
    
    # 8. 走量款
    if not high_profit and profit_rate >= 5 and high_sales:
        return ('走量款', '⚡', '薄利多销，建议提价', True, 'up')
    
    # 9. 潜力款
    if high_profit and not high_sales:
        return ('潜力款', '💎', '利润好销量低，可提价', True, 'optional')
    
    # 10. 低动销款（基于销量排名，与滞销品不同）
    if not high_profit and low_sales:
        return ('低动销款', '📉', '动销差利润低，可降价促销', True, 'down')
    
    # 11. 正常款
    return ('正常款', '⚪', '根据目标利润率调整', True, 'optional')


def prepare_pricing_data_v2(df: pd.DataFrame, channel: str = None) -> pd.DataFrame:
    """
    准备调价计算器数据 V2.0（独立计算，不依赖诊断模块）
    
    Args:
        df: 原始订单数据
        channel: 渠道筛选（可选）
    
    Returns:
        处理后的商品级DataFrame，包含所有调价所需字段
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    # 直接引用不复制，后面会创建新的聚合数据框
    df_filtered = df
    
    # ===== 渠道筛选 =====
    if channel and channel != 'all':
        channel_col = next((c for c in ['渠道', '平台', 'channel'] if c in df_filtered.columns), None)
        if channel_col:
            df_filtered = df_filtered[df_filtered[channel_col] == channel]
    
    if df_filtered.empty:
        return pd.DataFrame()
    
    # ===== 剔除耗材分类 =====
    category_col = '一级分类名' if '一级分类名' in df_filtered.columns else ('一级分类' if '一级分类' in df_filtered.columns else None)
    if category_col:
        df_filtered = df_filtered[df_filtered[category_col] != '耗材']
    
    if df_filtered.empty:
        return pd.DataFrame()
    
    # ===== 字段映射 =====
    sales_col = '月售' if '月售' in df_filtered.columns else ('销量' if '销量' in df_filtered.columns else None)
    cost_col = '商品采购成本' if '商品采购成本' in df_filtered.columns else ('成本' if '成本' in df_filtered.columns else None)
    # ⭐ 优先使用商品实售价（商家可调整的定价），而非实收价格（受平台活动影响）
    price_col = '商品实售价' if '商品实售价' in df_filtered.columns else ('实收价格' if '实收价格' in df_filtered.columns else None)
    original_price_col = '商品原价' if '商品原价' in df_filtered.columns else None
    
    if not sales_col or not price_col:
        print("[调价V2] 缺少必要字段：销量或价格")
        return pd.DataFrame()
    
    print(f"[调价V2] 使用价格字段: {price_col}")
    
    # ===== 计算销售额 =====
    df_filtered['_销量'] = pd.to_numeric(df_filtered[sales_col], errors='coerce').fillna(0)
    df_filtered['_实售价格'] = pd.to_numeric(df_filtered[price_col], errors='coerce').fillna(0)
    
    # ⭐ 商品实售价是单价，销售额 = 单价 × 销量
    df_filtered['_销售额'] = df_filtered['_实售价格'] * df_filtered['_销量']
    
    # 商品原价
    if original_price_col:
        df_filtered['_商品原价'] = pd.to_numeric(df_filtered[original_price_col], errors='coerce').fillna(0)
    else:
        df_filtered['_商品原价'] = df_filtered['_实售价格']  # 无原价时用实售价格代替
    
    # 成本
    if cost_col:
        df_filtered['_成本'] = pd.to_numeric(df_filtered[cost_col], errors='coerce').fillna(0)
    else:
        df_filtered['_成本'] = 0
    
    # ===== 计算营销成本（订单级分摊）=====
    marketing_cols = ['满减金额', '新客减免金额', '配送费减免金额', '商家代金券', 
                     '商家承担部分券', '满赠金额', '商家其他优惠', '商品减免金额']
    available_marketing_cols = [col for col in marketing_cols if col in df_filtered.columns]
    
    if available_marketing_cols:
        df_filtered['_行营销成本'] = df_filtered[available_marketing_cols].fillna(0).sum(axis=1)
        # 按订单分摊
        if '订单ID' in df_filtered.columns:
            df_filtered['_订单销售额占比'] = df_filtered.groupby('订单ID')['_销售额'].transform(
                lambda x: x / x.sum() if x.sum() > 0 else 1/len(x)
            )
            df_filtered['_订单营销总成本'] = df_filtered.groupby('订单ID')['_行营销成本'].transform('max')
            df_filtered['_商品营销成本'] = df_filtered['_订单营销总成本'] * df_filtered['_订单销售额占比']
        else:
            df_filtered['_商品营销成本'] = df_filtered['_行营销成本']
    else:
        df_filtered['_商品营销成本'] = 0
    
    # ===== 动态计算数据周期（在聚合前计算，确保使用完整数据）=====
    date_col = '日期' if '日期' in df_filtered.columns else ('下单时间' if '下单时间' in df_filtered.columns else None)
    if date_col:
        try:
            df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors='coerce')
            valid_dates = df_filtered[date_col].dropna()
            if len(valid_dates) > 0:
                date_range = (valid_dates.max() - valid_dates.min()).days + 1
                DATA_DAYS = max(1, min(date_range, 30))  # 最少1天，最多30天
            else:
                DATA_DAYS = 30
            print(f"[调价V2] 数据周期: {DATA_DAYS} 天")
        except Exception as e:
            print(f"[调价V2] 日期解析异常: {e}")
            DATA_DAYS = 30
    else:
        DATA_DAYS = 30
    
    # ===== 聚合到商品级别 =====
    # ⚠️ 重要：使用店内码（而非商品名称）区分商品，避免同名不同规格/价格混淆
    # 业务逻辑说明（根据权威文档）：
    # - 商品原价：单价，用 max
    # - 实收价格：用加权平均 = 总销售额 / 总销量
    # - 商品采购成本：总成本（单品成本×数量），用 sum 后除以销量得到单品成本
    agg_dict = {
        '_销售额': 'sum',           # 总销售额 = 实收价格 × 销量
        '_销量': 'sum',             # 总销量
        '_商品原价': 'max',         # 单价，取最大
        '_成本': 'sum',             # 总成本，需要除以销量得到单品成本
        '_商品营销成本': 'sum',
        '商品名称': 'first',        # 保留商品名称
    }
    
    # 添加可选字段
    if '订单ID' in df_filtered.columns:
        agg_dict['订单ID'] = 'nunique'
    if category_col:
        agg_dict[category_col] = 'first'
    if '利润额' in df_filtered.columns:
        agg_dict['利润额'] = 'sum'
    
    # 分组聚合 - 优先使用店内码，其次使用商品名称
    group_key = '店内码' if '店内码' in df_filtered.columns else '商品名称'
    if group_key == '店内码':
        # 过滤掉没有店内码的数据
        df_filtered = df_filtered[df_filtered['店内码'].notna() & (df_filtered['店内码'] != '')]
    product_data = df_filtered.groupby(group_key).agg(agg_dict).reset_index()
    
    # ===== 计算核心指标 =====
    # ⭐ 商品实售价 = 总销售额 / 总销量（加权平均，考虑不同订单销量权重）
    product_data['_实售价格'] = np.where(
        product_data['_销量'] > 0,
        product_data['_销售额'] / product_data['_销量'],
        0
    )
    
    # 单品成本 = 总成本 / 销量（成本是总额，需要除以销量）
    product_data['单品成本'] = np.where(
        product_data['_销量'] > 0,
        product_data['_成本'] / product_data['_销量'],
        0
    )
    
    # 日均销量（使用实际数据周期）
    product_data['日均销量'] = product_data['_销量'] / DATA_DAYS
    print(f"[调价V2] 日均销量范围: {product_data['日均销量'].min():.2f} ~ {product_data['日均销量'].max():.2f}")
    
    # 定价利润率 = (商品实售价 - 单品成本) / 商品实售价 × 100
    # 基于商品定价计算，反映定价策略的合理性
    product_data['利润率'] = np.where(
        product_data['_实售价格'] > 0,
        ((product_data['_实售价格'] - product_data['单品成本']) / product_data['_实售价格'] * 100),
        0
    )
    
    # 折扣率 = 商品实售价 / 商品原价
    product_data['折扣率'] = np.where(
        product_data['_商品原价'] > 0,
        product_data['_实售价格'] / product_data['_商品原价'],
        1
    )
    
    # 营销占比 = 营销成本 / 销售额 × 100（仅用于参考，不计入保本价）
    product_data['营销占比'] = np.where(
        product_data['_销售额'] > 0,
        (product_data['_商品营销成本'] / product_data['_销售额'] * 100),
        0
    )
    
    # ===== V3.0 核心计算：真实保本价 =====
    # 公式：真实保本价 = 单品成本 / (1 - 平台费率)
    # 说明：营销费用是变动成本（可选的促销投入），不应计入保本价
    #       保本价只考虑固定费用：商品成本 + 平台抽成
    PLATFORM_FEE_RATE = 0.08  # 平台抽成8%
    
    # 商品营销费率（仅供参考显示，不计入保本价）
    product_data['商品营销费率'] = (product_data['营销占比'] / 100).clip(upper=0.50)
    
    # 真实保本价 = 单品成本 / (1 - 8%)
    # 即：真实保本价 = 成本 / 0.92 ≈ 成本 × 1.087
    product_data['真实保本价'] = np.where(
        product_data['单品成本'] > 0,
        product_data['单品成本'] / (1 - PLATFORM_FEE_RATE),
        0
    )
    
    # 是否亏损 = 商品实售价 < 真实保本价
    product_data['是否亏损'] = product_data['_实售价格'] < product_data['真实保本价']
    
    # ===== V3.0 核心计算：高光利润率 =====
    # 需要从原始订单数据中计算每个商品的历史最高利润率
    # 这里简化处理：高光利润率 = 当前利润率的1.5倍，最低15%，最高50%
    # TODO: 后续可以从历史数据中计算真实的高光利润率
    product_data['高光利润率'] = (product_data['利润率'] * 1.5).clip(lower=15, upper=50)
    
    # 是否可修复 = 当前利润率 < 高光利润率 且 不亏损
    product_data['是否可修复'] = (product_data['利润率'] < product_data['高光利润率']) & (~product_data['是否亏损'])
    
    # ===== 计算销量排名百分位 =====
    product_data['销量排名'] = product_data['_销量'].rank(pct=True, method='average')
    
    # ===== ABC分类 =====
    product_data = product_data.sort_values('_销售额', ascending=False).reset_index(drop=True)
    total_sales = product_data['_销售额'].sum()
    if total_sales > 0:
        product_data['销售额占比'] = product_data['_销售额'] / total_sales * 100
        product_data['累计占比'] = product_data['销售额占比'].cumsum()
        product_data['ABC分类'] = product_data['累计占比'].apply(
            lambda x: 'A' if x <= 80 else ('B' if x <= 95 else 'C')
        )
    else:
        product_data['ABC分类'] = 'C'
    
    # ===== 识别商品角色 =====
    def apply_role(row):
        role_name, role_icon, suggestion, allow_adjust, direction = identify_product_role(
            discount_rate=row['折扣率'],
            profit_rate=row['利润率'],
            marketing_ratio=row['营销占比'],
            sales_percentile=row['销量排名'],
            daily_sales=row['日均销量']
        )
        return pd.Series({
            '商品角色': role_name,
            '角色图标': role_icon,
            '调价建议': suggestion,
            '允许调价': allow_adjust,
            '建议方向': direction
        })
    
    role_info = product_data.apply(apply_role, axis=1)
    product_data = pd.concat([product_data, role_info], axis=1)
    
    # ===== 整理输出列 =====
    output_cols = [
        '商品名称',
        '店内码' if '店内码' in product_data.columns else None,
        category_col if category_col and category_col in product_data.columns else None,
        '商品角色', '角色图标', 'ABC分类',
        '折扣率', '_商品原价', '_实售价格', '单品成本',
        '利润率', '日均销量', '_销量', '_销售额',
        '营销占比', '销量排名',
        '调价建议', '允许调价', '建议方向',
        # V3.0 新增字段
        '真实保本价', '商品营销费率', '高光利润率', '是否亏损', '是否可修复'
    ]
    output_cols = [c for c in output_cols if c is not None and c in product_data.columns]
    
    # 重命名列
    result = product_data[output_cols].copy()
    result = result.rename(columns={
        '_商品原价': '商品原价',
        '_实售价格': '实收价格',  # ⭐ 输出仍然叫“实收价格”，但实际来源是商品实售价
        '_销量': '总销量',
        '_销售额': '总销售额'
    })
    
    # 圆整数值
    for col in ['商品原价', '实收价格', '单品成本', '利润率', '日均销量', '营销占比', '折扣率', '真实保本价', '商品营销费率', '高光利润率']:
        if col in result.columns:
            result[col] = result[col].round(2)
    
    print(f"[调价V2] 准备数据完成：{len(result)} 个商品")
    print(f"[调价V3] 亏损商品: {result['是否亏损'].sum()} 个, 可修复商品: {result['是否可修复'].sum()} 个")
    return result


def calculate_pricing_suggestion(
    current_price: float,
    cost: float,
    original_price: float,
    daily_sales: float,
    elasticity: float,
    target_margin: float,
    product_role: str,
    allow_adjust: bool,
    direction: str,
    real_breakeven_price: float = None  # V3.0: 真实保本价（含平台费+营销费）
) -> dict:
    """
    计算调价建议 (V3.0升级：使用真实保本价)
    
    Args:
        current_price: 当前售价
        cost: 单品成本
        original_price: 商品原价
        daily_sales: 日均销量
        elasticity: 弹性系数（负数）
        target_margin: 目标利润率（%）
        product_role: 商品角色
        allow_adjust: 是否允许调价
        direction: 建议方向 ('up'/'down'/'none'/'optional')
        real_breakeven_price: V3.0真实保本价 = 单品成本 / (1 - 平台费率 - 商品营销费率)
    
    Returns:
        {
            'suggested_price': 建议价格,
            'floor_price': 真实保本价,
            'ceiling_price': 最高价,
            'suggestion_text': 建议说明,
            'estimated_qty_change': 预估销量变化(%),
            'estimated_profit_change': 预估利润变化(%)
        }
    """
    # 安全检查：价格必须为正数
    if current_price <= 0:
        current_price = 1
    if original_price <= 0:
        original_price = current_price
    if cost < 0:
        cost = 0
    
    # V3.0: 使用真实保本价作为floor_price（包含平台费+营销费）
    # 如果没有传入真实保本价，则使用单品成本/0.92（简化计算，假设8%平台费）
    if real_breakeven_price is None or real_breakeven_price <= 0:
        real_breakeven_price = cost / 0.92 if cost > 0 else 0.01
    
    result = {
        'suggested_price': current_price,
        'floor_price': real_breakeven_price,  # V3.0: 使用真实保本价
        'ceiling_price': original_price if original_price > current_price else current_price,
        'suggestion_text': '--',
        'estimated_qty_change': 0,
        'estimated_profit_change': 0
    }
    
    # 不允许调价的商品
    if not allow_adjust or direction == 'none':
        result['suggestion_text'] = '不建议调价'
        return result
    
    # V3.0: 保本价使用真实保本价（含平台费+营销费），最高价为原价
    floor_price = real_breakeven_price
    ceiling_price = original_price if original_price > current_price else current_price * 1.5
    
    result['floor_price'] = round(floor_price, 2)
    result['ceiling_price'] = round(ceiling_price, 2)
    
    # 目标利润率边界保护（防止除以零或负数）
    safe_margin = min(max(target_margin, 1), 98)  # 限制在1-98%，避免除以零
    
    # 计算目标价格：目标价格 = 成本 / (1 - 目标利润率)
    if cost > 0:
        divisor = 1 - safe_margin / 100
        if divisor > 0.01:  # 确保分母有效
            target_price = cost / divisor
            # 合理性检查：目标价格不应超过当前价格的3倍
            if target_price > current_price * 3:
                target_price = current_price * 3
        else:
            target_price = current_price * 3  # 极端情况默认涨到3倍
    else:
        target_price = current_price
    
    # 根据方向调整
    if direction == 'up':
        # 涨价模式：建议价格 = max(目标价格, 当前价格)，但不超过最高价（原价）
        suggested_price = min(max(target_price, current_price), ceiling_price)
        if suggested_price > current_price:
            change_pct = (suggested_price - current_price) / current_price * 100
            result['suggestion_text'] = f'建议涨{change_pct:.1f}%'
        else:
            result['suggestion_text'] = '已达上限'
    
    elif direction == 'down':
        # 降价模式：根据目标利润率计算，不低于保本价
        # 如果目标价格低于当前价格，使用目标价格；否则维持或小幅降价
        if target_price < current_price:
            suggested_price = max(target_price, floor_price)
        else:
            # 当前利润率已低于目标，考虑小幅降价促销（5%）
            suggested_price = max(current_price * 0.95, floor_price)
        
        if suggested_price < current_price:
            change_pct = (current_price - suggested_price) / current_price * 100
            result['suggestion_text'] = f'建议降{change_pct:.1f}%'
        else:
            result['suggestion_text'] = '已达下限'
    
    else:  # optional - 自动判断
        # 根据目标利润率自动判断涨降
        if target_price > current_price * 1.01:
            # 需要涨价
            suggested_price = min(target_price, ceiling_price)
            if suggested_price > current_price:
                change_pct = (suggested_price - current_price) / current_price * 100
                result['suggestion_text'] = f'可涨{change_pct:.1f}%'
            else:
                result['suggestion_text'] = '价格合理'
        elif target_price < current_price * 0.99:
            # 可以降价
            suggested_price = max(target_price, floor_price)
            if suggested_price < current_price:
                change_pct = (current_price - suggested_price) / current_price * 100
                result['suggestion_text'] = f'可降{change_pct:.1f}%'
            else:
                result['suggestion_text'] = '已达下限'
        else:
            suggested_price = current_price
            result['suggestion_text'] = '价格合理'
    
    result['suggested_price'] = round(suggested_price, 2)
    
    # 预估销量和利润变化
    if current_price > 0 and suggested_price != current_price:
        price_change_rate = (suggested_price - current_price) / current_price
        qty_change_rate = price_change_rate * elasticity  # 弹性系数为负
        
        result['estimated_qty_change'] = round(qty_change_rate * 100, 1)
        
        # 利润变化
        old_profit = (current_price - cost) * daily_sales
        new_qty = daily_sales * (1 + qty_change_rate)
        new_profit = (suggested_price - cost) * new_qty
        
        if old_profit != 0:
            profit_change_rate = (new_profit - old_profit) / abs(old_profit) * 100
            result['estimated_profit_change'] = round(profit_change_rate, 1)
    
    return result


def get_elasticity_label(elasticity: float) -> tuple:
    """
    获取弹性敏感度标签
    
    Args:
        elasticity: 弹性系数（负数）
    
    Returns:
        (标签, 图标, 颜色)
    """
    abs_e = abs(elasticity)
    if abs_e > 1.5:
        return ('高敏', '🔴', 'danger')
    elif abs_e > 1.0:
        return ('中敏', '🟡', 'warning')
    elif abs_e > 0.5:
        return ('低敏', '🟢', 'success')
    else:
        return ('不敏感', '⚪', 'secondary')


# ==================== 帮助弹窗回调 ====================

@callback(
    Output("product-help-modal", "is_open"),
    Input("product-help-btn", "n_clicks"),
    State("product-help-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_help_modal(n_clicks, is_open):
    """切换帮助弹窗的显示状态"""
    if n_clicks:
        return not is_open
    return is_open


# ==================== 智能调价计算器回调函数 ====================

# 调价方向自动切换回调 - 根据商品来源自动设置提价/降价
@callback(
    Output("pricing-adjust-direction", "value"),
    Input("pricing-source-dropdown", "value"),
    prevent_initial_call=True
)
def auto_switch_adjust_direction(source):
    """根据商品来源自动切换调价方向 - 旧版兼容"""
    from .pricing_engine import get_source_direction
    
    if not source or source.startswith('_header_'):
        raise PreventUpdate
    
    return get_source_direction(source)


# ==================== V2.0 调价方向筛选回调 ====================

@callback(
    [Output('pricing-role-store', 'data'),
     Output('pricing-role-loss', 'outline'),
     Output('pricing-role-volume', 'outline'),
     Output('pricing-role-slow', 'outline'),
     Output('pricing-role-traffic', 'outline'),
     Output('pricing-role-promo', 'outline'),
     Output('pricing-role-lowfreq', 'outline'),
     Output('pricing-role-star', 'outline'),
     Output('pricing-role-cash', 'outline'),
     Output('pricing-role-potential', 'outline'),
     Output('pricing-role-all', 'outline')],
    [Input('pricing-role-loss', 'n_clicks'),
     Input('pricing-role-volume', 'n_clicks'),
     Input('pricing-role-slow', 'n_clicks'),
     Input('pricing-role-traffic', 'n_clicks'),
     Input('pricing-role-promo', 'n_clicks'),
     Input('pricing-role-lowfreq', 'n_clicks'),
     Input('pricing-role-star', 'n_clicks'),
     Input('pricing-role-cash', 'n_clicks'),
     Input('pricing-role-potential', 'n_clicks'),
     Input('pricing-role-all', 'n_clicks')],
    prevent_initial_call=True
)
def update_role_selection(*args):
    """更新调价方向筛选状态（V3.0：按调价场景筛选）"""
    from dash import ctx
    triggered_id = ctx.triggered_id
    
    # 调价方向ID到值的映射（V3.0：四个调价场景）
    # loss: 亏损止血（实收价 < 真实保本价）
    # profit: 利润修复（当前利润率 < 高光利润率）
    # slow: 滞销清仓（连续N天无销量且有库存）
    # promo: 促销引流（全部商品，用户自选）
    role_map = {
        'pricing-role-loss': 'loss',      # 🩸 亏损止血
        'pricing-role-volume': 'profit',  # 📈 利润修复
        'pricing-role-slow': 'slow',      # 📦 滞销清仓
        'pricing-role-traffic': 'promo',  # 🎯 促销引流
        # 以下为兼容性保留（隐藏按钮）
        'pricing-role-promo': 'promo',
        'pricing-role-lowfreq': 'promo',
        'pricing-role-star': 'promo',
        'pricing-role-cash': 'promo',
        'pricing-role-potential': 'promo',
        'pricing-role-all': 'promo'
    }
    
    # 默认全部为outline（未选中），只有前4个按钮可见
    outlines = [True] * 10
    role = 'loss'  # 默认亏损止血
    
    if triggered_id in role_map:
        role = role_map[triggered_id]
        # 找到被点击按钮的索引（只处理前4个可见按钮）
        visible_buttons = ['pricing-role-loss', 'pricing-role-volume', 'pricing-role-slow', 'pricing-role-traffic']
        if triggered_id in visible_buttons:
            idx = visible_buttons.index(triggered_id)
            outlines[idx] = False  # 选中状态
        else:
            outlines[0] = False  # 隐藏按钮点击默认选中第一个
    else:
        # 默认选中"亏损止血"
        outlines[0] = False
    
    return [role] + outlines


# ==================== V2.0 根据调价方向自动切换涨价/降价 ====================
@callback(
    [Output('pricing-direction-store', 'data', allow_duplicate=True),
     Output('pricing-direction-up', 'outline', allow_duplicate=True),
     Output('pricing-direction-down', 'outline', allow_duplicate=True),
     Output('pricing-direction-hint', 'children', allow_duplicate=True)],
    Input('pricing-role-store', 'data'),
    prevent_initial_call=True
)
def auto_switch_direction_by_role(role):
    """根据调价方向自动切换涨价/降价（V3.0：基于调价场景）"""
    # 场景说明映射
    scene_hints = {
        'loss': ('up', "🩸 亏损止血：涨价至真实保本价以上"),
        'profit': ('up', "📈 利润修复：涨价恢复至高光利润率"),
        'slow': ('down', "📦 滞销清仓：降价促进销售"),
        'promo': ('down', "🎯 促销引流：降价吸引流量"),
    }
    
    if role in scene_hints:
        direction, hint = scene_hints[role]
        if direction == 'up':
            return 'up', False, True, hint
        else:
            return 'down', True, False, hint
    
    # 默认降价模式
    return 'down', True, False, "降价：建议价格 ≤ 实售价"


# ==================== V2.0 涨价/降价方向切换回调 ====================
@callback(
    [Output('pricing-direction-store', 'data'),
     Output('pricing-direction-up', 'outline'),
     Output('pricing-direction-down', 'outline'),
     Output('pricing-direction-hint', 'children')],
    [Input('pricing-direction-up', 'n_clicks'),
     Input('pricing-direction-down', 'n_clicks')],
    prevent_initial_call=True
)
def update_pricing_direction(n_up, n_down):
    """切换涨价/降价方向"""
    from dash import ctx
    triggered_id = ctx.triggered_id
    
    if triggered_id == 'pricing-direction-up':
        return 'up', False, True, "涨价：建议价格 ≥ 实售价"
    else:
        return 'down', True, False, "降价：建议价格 ≤ 实售价"


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
        
    # 内存优化：使用视图而非复制
    df = apply_filters_view(
        GLOBAL_DATA,
        selected_stores=selected_stores if selected_stores and len(selected_stores) > 0 else None
    )
    
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


# ==================== V2.0 智能调价计算器主回调 ====================
@callback(
    [Output("pricing-table-container", "children"),
     Output("pricing-data-store", "data"),
     Output("pricing-batch-status", "children")],
    [Input("pricing-calculate-btn", "n_clicks"),
     Input("pricing-role-store", "data")],         # 角色选择也触发（加载商品列表）
    [State("pricing-direction-store", "data"),     # 方向作为State
     State("pricing-target-margin-v2", "value"),   # 目标利润率作为State
     State("db-store-filter", "value"),
     State("pricing-channel-filter", "value")],
    prevent_initial_call=True
)
def update_pricing_table_v2(n_clicks, role_filter, direction, target_margin, store, channel):
    """V2.0 智能调价计算器主回调 - 独立数据处理，基于商品角色"""
    from dash import dash_table, ctx
    from .pricing_engine import get_product_elasticity, predict_profit_change, get_stagnant_products
    
    triggered_id = ctx.triggered_id
    
    # 详细调试：显示原始接收到的参数类型和值
    print(f"[调价V2] 回调触发: triggered={triggered_id}")
    print(f"[调价V2] 参数详情: role={role_filter}({type(role_filter).__name__}), direction={direction}({type(direction).__name__})")
    print(f"[调价V2] 目标利润率原始值: target_margin={repr(target_margin)}, type={type(target_margin).__name__}")
    
    # ========== 判断触发来源 ==========
    is_role_trigger = triggered_id == 'pricing-role-store'  # 角色选择触发
    is_calc_trigger = triggered_id == 'pricing-calculate-btn'  # 计算按钮触发
    
    # ========== 第一步：解析目标利润率 ==========
    # 如果是角色选择触发，不需要目标利润率（只加载商品列表）
    # 如果是计算按钮触发，必须有目标利润率
    if target_margin is None or target_margin == '' or target_margin == 'None':
        if is_calc_trigger:
            # 计算按钮触发但没有输入目标利润率，提示用户
            return html.Div([
                dbc.Alert([
                    html.I(className="fas fa-exclamation-circle me-2"),
                    "请先输入目标利润率再点击计算"
                ], color="warning", className="text-center")
            ], className="py-3"), [], "⚠️ 请输入目标利润率"
        else:
            # 角色选择触发，使用None表示只加载列表不计算
            margin_value = None
            print(f"[调价V2] 角色选择触发，只加载商品列表，不计算调价")
    else:
        try:
            margin_value = float(target_margin)
            print(f"[调价V2] target_margin成功转换为: {margin_value}")
        except (ValueError, TypeError) as e:
            if is_calc_trigger:
                return html.Div([
                    dbc.Alert([
                        html.I(className="fas fa-exclamation-circle me-2"),
                        "目标利润率格式错误，请输入数字"
                    ], color="danger", className="text-center")
                ], className="py-3"), [], "❌ 格式错误"
            margin_value = None
    
    # 基础检查：不能为负数
    if margin_value is not None and margin_value < 1:
        margin_value = 1
    
    target_margin = margin_value
    print(f"[调价V2] 最终使用 target_margin = {target_margin}%")
    
    # 获取全局数据
    GLOBAL_DATA = get_real_global_data()
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return html.Div("请先加载数据", className="text-muted text-center py-4"), [], ""
    
    # 如果是角色选择触发，但角色为空则跳过
    if triggered_id == 'pricing-role-store' and not role_filter:
        raise PreventUpdate
    
    try:
        # 内存优化：使用视图筛选门店
        if store:
            store_list = store if isinstance(store, list) else [store]
            df = apply_filters_view(GLOBAL_DATA, selected_stores=store_list)
            store_name = store_list[0] if store_list else None
        else:
            df = GLOBAL_DATA  # 不筛选，直接用原数据（视图）
            store_name = None
        print(f"[调价V2] 原始数据: {len(GLOBAL_DATA)} 行, 筛选后: {len(df)} 行")
        
        if df.empty:
            return html.Div("筛选后无数据", className="text-muted text-center py-4"), [], ""
        
        # ========== 特殊处理：滞销品 ==========
        # 如果选择的是滞销品，使用专门的滞销品函数（基于滞销天数+库存）
        if role_filter == '_stagnant':
            print("[调价V2] 使用滞销品专用函数")
            
            # 检查数据天数
            if '日期' in df.columns:
                date_range = (df['日期'].max() - df['日期'].min()).days + 1
                print(f"[调价V2] 数据天数: {date_range}天")
                if date_range < 7:
                    return html.Div([
                        dbc.Alert([
                            html.I(className="bi bi-exclamation-triangle me-2"),
                            f"数据天数不足（当前{date_range}天），滞销天数无法准确计算。建议选择至少7天的数据。"
                        ], color="warning")
                    ], className="text-center py-4"), [], ""
            
            products_df = get_stagnant_products(df, store_name, 'all')
            
            if products_df.empty:
                return html.Div("暂无滞销品（需要库存>0且连续7天+无销量）", className="text-muted text-center py-4"), [], ""
            
            print(f"[调价V2] 滞销品数量: {len(products_df)}")
            
            # 为滞销品添加角色标记（包含滞销天数和等级）
            products_df['商品角色'] = products_df.apply(
                lambda r: f"滞销{r.get('滞销天数', 0)}天", axis=1
            )
            products_df['角色图标'] = products_df['滞销等级'].apply(
                lambda x: x.split(' ')[0] if isinstance(x, str) and ' ' in x else '🐌'
            )
            products_df['允许调价'] = True
            products_df['建议方向'] = 'down'
            products_df['调价建议'] = '建议降价清仓'
            
            # 统一字段名
            if '实收价格' not in products_df.columns and '商品实售价' in products_df.columns:
                products_df['实收价格'] = products_df['商品实售价']
            if '单品成本' not in products_df.columns:
                if '商品采购成本' in products_df.columns:
                    qty_col = '月售' if '月售' in products_df.columns else ('销量' if '销量' in products_df.columns else None)
                    if qty_col:
                        products_df['_qty'] = pd.to_numeric(products_df[qty_col], errors='coerce').fillna(1).replace(0, 1)
                        products_df['单品成本'] = products_df['商品采购成本'] / products_df['_qty']
                    else:
                        products_df['单品成本'] = products_df['商品采购成本']
                else:
                    products_df['单品成本'] = 0
            if '日均销量' not in products_df.columns:
                qty_col = '月售' if '月售' in products_df.columns else ('销量' if '销量' in products_df.columns else None)
                if qty_col:
                    products_df['日均销量'] = pd.to_numeric(products_df[qty_col], errors='coerce').fillna(0) / 30
                else:
                    products_df['日均销量'] = 0
            if '利润率' not in products_df.columns:
                if '实收价格' in products_df.columns and '单品成本' in products_df.columns:
                    products_df['利润率'] = np.where(
                        products_df['实收价格'] > 0,
                        (products_df['实收价格'] - products_df['单品成本']) / products_df['实收价格'] * 100,
                        0
                    )
                else:
                    products_df['利润率'] = 0
            # 滞销品没有原价，用实收价格代替
            if '商品原价' not in products_df.columns:
                products_df['商品原价'] = products_df['实收价格'] if '实收价格' in products_df.columns else 0
            
            # 确保数值字段安全（防止除以零）
            products_df['实收价格'] = pd.to_numeric(products_df.get('实收价格', 0), errors='coerce').fillna(0)
            products_df['单品成本'] = pd.to_numeric(products_df.get('单品成本', 0), errors='coerce').fillna(0)
            products_df['商品原价'] = pd.to_numeric(products_df.get('商品原价', 0), errors='coerce').fillna(0)
            # V3.0: 滞销品添加真实保本价（简化计算）
            products_df['真实保本价'] = products_df['单品成本'] / 0.92  # 假设8%平台费
            products_df['是否亏损'] = products_df['实收价格'] < products_df['真实保本价']
            products_df['高光利润率'] = 15.0  # 滞销品默认15%
            products_df['是否可修复'] = False
        else:
            # ========== 常规处理：使用V2数据处理函数 ==========
            products_df = prepare_pricing_data_v2(df, channel)
            
            if products_df.empty:
                return html.Div("无法准备商品数据", className="text-muted text-center py-4"), [], ""
            
            print(f"[调价V2] 准备数据: {len(products_df)} 个商品")
            print(f"[调价V2] 角色分布: {products_df['商品角色'].value_counts().to_dict()}")
            
            # ========== V3.0 调价方向筛选 ==========
            # role_filter 现在是调价场景：loss/profit/slow/promo
            scene_names = {
                'loss': '亏损止血',
                'profit': '利润修复', 
                'slow': '滞销清仓',
                'promo': '促销引流'
            }
            
            if role_filter == 'loss':
                # 🩸 亏损止血：实收价格 < 真实保本价
                products_df = products_df[products_df['是否亏损'] == True]
                print(f"[调价V3] 亏损止血筛选后: {len(products_df)} 个商品")
            elif role_filter == 'profit':
                # 📈 利润修复：当前利润率 < 高光利润率（且不亏损）
                products_df = products_df[products_df['是否可修复'] == True]
                print(f"[调价V3] 利润修复筛选后: {len(products_df)} 个商品")
            elif role_filter == 'slow':
                # 📦 滞销清仓：使用滞销品函数
                products_df = get_stagnant_products(df, store_name, 'all')
                if not products_df.empty:
                    # 补充必要字段
                    if '实收价格' not in products_df.columns and '商品实售价' in products_df.columns:
                        products_df['实收价格'] = products_df['商品实售价']
                    if '单品成本' not in products_df.columns:
                        products_df['单品成本'] = 0
                    products_df['商品角色'] = '滞销品'
                    products_df['角色图标'] = '📦'
                print(f"[调价V3] 滞销清仓筛选后: {len(products_df)} 个商品")
            elif role_filter == 'promo':
                # 🎯 促销引流：全部商品，用户自选
                print(f"[调价V3] 促销引流：展示全部 {len(products_df)} 个商品")
            else:
                # 兼容旧版：按角色筛选（如果传入的是旧角色值）
                if role_filter and role_filter not in ['all', 'loss', 'profit', 'slow', 'promo']:
                    products_df = products_df[products_df['商品角色'] == role_filter]
                    print(f"[调价V2] 兼容模式-角色筛选后: {len(products_df)} 个商品")
            
            scene_name = scene_names.get(role_filter, role_filter)
            if products_df.empty:
                return html.Div(f"暂无【{scene_name}】商品", className="text-muted text-center py-4"), [], ""
        
        # ========== 如果没有目标利润率（方向选择触发），只显示商品列表 ==========
        if target_margin is None:
            # 构建简单的商品列表展示
            from dash import dash_table
            
            # V3.0: 根据场景调整展示列
            scene_labels = {
                'loss': '🩸 亏损止血',
                'profit': '📈 利润修复',
                'slow': '📦 滞销清仓',
                'promo': '🎯 促销引流'
            }
            
            # 准备展示数据
            preview_data = []
            for _, row in products_df.head(100).iterrows():
                item = {
                    '店内码': str(row.get('店内码', ''))[:10] or '--',
                    '商品名称': str(row.get('商品名称', ''))[:15] or '--',
                    '实收价格': f"¥{float(row.get('实收价格', 0)):.2f}",
                    '成本': f"¥{float(row.get('单品成本', 0)):.2f}",
                    '利润率': f"{float(row.get('利润率', 0)):.1f}%",
                }
                # V3.0: 根据场景添加特殊列
                if role_filter == 'loss':
                    item['真实保本价'] = f"¥{float(row.get('真实保本价', 0)):.2f}"
                    item['亏损额'] = f"¥{float(row.get('真实保本价', 0) - row.get('实收价格', 0)):.2f}"
                elif role_filter == 'profit':
                    item['高光利润率'] = f"{float(row.get('高光利润率', 0)):.1f}%"
                    item['差距'] = f"{float(row.get('高光利润率', 0) - row.get('利润率', 0)):.1f}%"
                elif role_filter == 'slow':
                    item['滞销天数'] = str(row.get('滞销天数', '--'))
                    item['库存'] = str(row.get('库存', '--'))
                else:
                    item['日均销量'] = f"{float(row.get('日均销量', 0)):.1f}"
                preview_data.append(item)
            
            # 根据场景构建列
            base_cols = [
                {'name': '店内码', 'id': '店内码'},
                {'name': '商品名称', 'id': '商品名称'},
                {'name': '实收价格', 'id': '实收价格'},
                {'name': '成本', 'id': '成本'},
                {'name': '利润率', 'id': '利润率'},
            ]
            if role_filter == 'loss':
                base_cols.extend([
                    {'name': '真实保本价', 'id': '真实保本价'},
                    {'name': '亏损额', 'id': '亏损额'},
                ])
            elif role_filter == 'profit':
                base_cols.extend([
                    {'name': '高光利润率', 'id': '高光利润率'},
                    {'name': '差距', 'id': '差距'},
                ])
            elif role_filter == 'slow':
                base_cols.extend([
                    {'name': '滞销天数', 'id': '滞销天数'},
                    {'name': '库存', 'id': '库存'},
                ])
            else:
                base_cols.append({'name': '日均销量', 'id': '日均销量'})
            
            preview_table = dash_table.DataTable(
                columns=base_cols,
                data=preview_data,
                page_size=20,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'center', 'padding': '6px', 'fontSize': '12px'},
                style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                style_data_conditional=[
                    # 亏损商品红色高亮
                    {'if': {'filter_query': '{利润率} contains "-"'}, 'backgroundColor': '#ffe6e6'},
                ]
            )
            
            scene_label = scene_labels.get(role_filter, role_filter)
            
            content = html.Div([
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    f"已加载 【{scene_label}】商品 {len(products_df)} 个",
                    html.Span("，请输入目标利润率后点击「计算调价」", className="ms-1")
                ], color="info", className="mb-3"),
                preview_table
            ])
            
            return content, [], f"✅ 已加载{len(products_df)}个商品"
        
        # ========== 动态边界计算（与老版本一致） ==========
        # 遍历所有商品，计算可达到的利润率边界
        max_achievable_margin = 0  # 涨价能达到的最高利润率（价格=原价时）
        min_achievable_margin = 0  # 降价能达到的最低利润率（价格=保本价时=0%）
        valid_items_count = 0
        
        for _, row in products_df.iterrows():
            try:
                current_price = float(row['实收价格']) if pd.notna(row.get('实收价格')) else 0
                cost = float(row['单品成本']) if pd.notna(row.get('单品成本')) else 0
                original_price = float(row['商品原价']) if pd.notna(row.get('商品原价')) else current_price
            except (ValueError, TypeError, KeyError):
                continue
            
            if current_price <= 0 or cost <= 0:
                continue
            
            valid_items_count += 1
            
            # 原价如果无效，使用实售价
            if original_price <= 0:
                original_price = current_price
            
            # 涨价上限：价格=原价时的利润率
            if original_price > cost:
                margin_at_ceiling = (original_price - cost) / original_price * 100  # 转为百分比
                max_achievable_margin = max(max_achievable_margin, margin_at_ceiling)
        
        # 如果没有有效商品，使用默认边界
        if valid_items_count == 0:
            max_achievable_margin = 99
        
        print(f"[调价V2] 边界计算: 最大可达利润率={max_achievable_margin:.1f}%, 商品数={valid_items_count}")
        
        # ========== 前置边界校验（与老版本一致） ==========
        boundary_exceeded = False
        boundary_msg = ""
        
        if direction == 'up':  # 涨价模式
            if target_margin > max_achievable_margin:
                boundary_exceeded = True
                boundary_msg = f"涨价目标利润率 {target_margin:.0f}% 超过最大可达 {max_achievable_margin:.1f}%"
        else:  # 降价模式
            if target_margin <= 0:
                boundary_exceeded = True
                boundary_msg = f"降价目标利润率 {target_margin:.0f}% 低于保本价下限 1%"
            elif target_margin > max_achievable_margin:
                boundary_exceeded = True
                boundary_msg = f"降价目标利润率 {target_margin:.0f}% 超过当前可达范围"
        
        if boundary_exceeded:
            print(f"[调价V2] ★★★ 动态边界超限: {boundary_msg}")
            
            # 构建详细的边界提示
            direction_text = "涨价" if direction == 'up' else "降价"
            
            error_content = html.Div([
                dbc.Alert([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    html.Strong(f"{direction_text}目标超出可达范围！"),
                ], color="warning", className="mb-3"),
                html.Div([
                    html.Div([
                        html.Span("您输入的目标利润率：", className="text-muted"),
                        html.Strong(f"{target_margin:.0f}%", className="text-danger fs-4 ms-2")
                    ], className="mb-2"),
                    html.Div([
                        html.Span(f"当前商品最大可达利润率：", className="text-muted"),
                        html.Strong(f"{max_achievable_margin:.1f}%", className="text-success fs-4 ms-2")
                    ], className="mb-3"),
                    html.Hr(),
                    html.P([
                        html.I(className="fas fa-info-circle me-2"),
                        f"这是根据当前筛选的 ",
                        html.Strong(f"{valid_items_count} 个商品"),
                        " 计算出的边界（所有商品涨至原价时的利润率）"
                    ], className="small text-muted mb-2"),
                    html.P([
                        "请输入 ",
                        html.Strong(f"1% ~ {max_achievable_margin:.0f}%", className="text-primary"),
                        " 之间的值"
                    ], className="mb-0")
                ], className="text-center py-3")
            ])
            
            status = html.Span([
                f"❌ 超限 (最大{max_achievable_margin:.0f}%)"
            ], className="text-danger small")
            
            return error_content, [], status
        
        # 获取渠道
        channel_name = channel if channel and channel != 'all' else '美团'
        
        # 构建表格数据
        table_data = []
        
        for _, row in products_df.iterrows():
            # 获取弹性系数（优先使用学习得到的弹性系数）
            code = str(row.get('店内码', '') or '')
            category = str(row.get('一级分类名', '') or row.get('一级分类', '') or '')
            elasticity, elasticity_source = get_product_elasticity(code, channel_name, category, None)
            
            # 当前数据（安全获取，防止空值）
            try:
                current_price = float(row.get('实收价格', 0) or 0)
                cost = float(row.get('单品成本', 0) or 0)
                original_price = float(row.get('商品原价', 0) or 0)
                if original_price <= 0:
                    original_price = current_price if current_price > 0 else 1
                daily_sales = float(row.get('日均销量', 0) or 0)
                profit_rate = float(row.get('利润率', 0) or 0)
                # V3.0: 获取真实保本价、商品营销费率、高光利润率
                real_breakeven = float(row.get('真实保本价', 0) or 0)
                marketing_rate = float(row.get('商品营销费率', 0) or 0)
                highlight_margin = float(row.get('高光利润率', 0) or 0)
                is_loss = bool(row.get('是否亏损', False))
                # 滞销天数（滞销品专用）
                stagnant_days = int(row.get('滞销天数', 0) or 0)
                is_repairable = bool(row.get('是否可修复', False))
            except (ValueError, TypeError):
                # 数据转换失败，跳过该商品
                continue
            
            # 跳过价格为0的无效商品
            if current_price <= 0:
                continue
            
            # 商品角色信息
            role_name = row.get('商品角色', '正常款')
            role_icon = row.get('角色图标', '⚪')
            allow_adjust = row.get('允许调价', True)
            product_direction = row.get('建议方向', 'optional')
            suggestion = row.get('调价建议', '')
            
            # 使用用户选择的全局方向（优先级高于商品自身建议）
            # 但对于不允许调价的商品，保持原方向
            effective_direction = direction if allow_adjust else product_direction
            
            # 计算调价建议（V3.0: 传入真实保本价）
            pricing_result = calculate_pricing_suggestion(
                current_price=current_price,
                cost=cost,
                original_price=original_price,
                daily_sales=daily_sales,
                elasticity=elasticity,
                target_margin=target_margin,
                product_role=role_name,
                allow_adjust=allow_adjust,
                direction=effective_direction,
                real_breakeven_price=real_breakeven  # V3.0: 真实保本价
            )
            
            suggested_price = pricing_result['suggested_price']
            floor_price = pricing_result['floor_price']
            ceiling_price = pricing_result['ceiling_price']
            
            # 预估变化
            est_qty_change = pricing_result['estimated_qty_change']
            est_profit_change = pricing_result['estimated_profit_change']
            
            # 弹性敏感度
            sens_label, sens_icon, _ = get_elasticity_label(elasticity)
            
            # 计算价格变化幅度
            price_change = suggested_price - current_price
            price_change_pct = (price_change / current_price * 100) if current_price > 0 else 0
            
            # ============ 老版本边界判断逻辑（移植自 batch_adjust_prices_smart） ============
            # 计算目标价格（未受边界约束的理论价格）
            if cost > 0:
                divisor = 1 - target_margin / 100
                if divisor > 0.01:
                    target_price_raw = cost / divisor
                else:
                    target_price_raw = current_price * 3  # 极端情况
            else:
                target_price_raw = current_price
            
            # 理论变化百分比（如果没有边界约束，需要变化多少）
            theoretical_change_pct = ((target_price_raw - current_price) / current_price * 100) if current_price > 0 else 0
            
            # 边界判断
            hit_ceiling = suggested_price >= original_price * 0.99  # 触及原价上限
            hit_floor = suggested_price <= floor_price * 1.01  # 触及保本价下限
            already_at_ceiling = current_price >= original_price * 0.99  # 当前已是原价
            already_at_floor = cost > 0 and current_price <= floor_price * 1.01  # 当前已是保本价
            
            # 调整说明（根据是否允许调价）- 参照老版本逻辑
            if not allow_adjust:
                adjust_text = "⛔ 不建议"
                suggested_price = current_price  # 不允许调价时，建议价格=当前价格
            elif direction == 'up':  # 涨价模式
                if already_at_ceiling:
                    # 当前已经是原价，无法再涨
                    if theoretical_change_pct > 0.5:
                        adjust_text = f"⚠️ 已达原价上限(需涨{theoretical_change_pct:.1f}%)"
                    else:
                        adjust_text = "✓ 已达原价上限"
                elif hit_ceiling:
                    # 涨到原价就停了
                    actual_pct = (original_price - current_price) / current_price * 100 if current_price > 0 else 0
                    adjust_text = f"↑ +{actual_pct:.1f}%(达原价上限)"
                elif abs(price_change_pct) < 0.5:
                    adjust_text = "→ 维持(已达目标)"
                else:
                    adjust_text = f"↑ +{price_change_pct:.1f}%"
            elif direction == 'down':  # 降价模式
                if already_at_floor:
                    # 当前已经是保本价，无法再降
                    if theoretical_change_pct < -0.5:
                        adjust_text = f"⚠️ 已达保本下限(需降{abs(theoretical_change_pct):.1f}%)"
                    else:
                        adjust_text = "✓ 已达保本下限"
                elif hit_floor:
                    # 降到保本价就停了
                    actual_pct = (current_price - floor_price) / current_price * 100 if current_price > 0 else 0
                    adjust_text = f"↓ -{actual_pct:.1f}%(达保本下限)"
                elif abs(price_change_pct) < 0.5:
                    adjust_text = "→ 维持(已达目标)"
                else:
                    adjust_text = f"↓ {price_change_pct:.1f}%"
            else:  # optional - 自动判断
                if abs(price_change_pct) < 0.5:
                    adjust_text = "→ 维持"
                elif price_change > 0:
                    if hit_ceiling:
                        actual_pct = (original_price - current_price) / current_price * 100 if current_price > 0 else 0
                        adjust_text = f"↑ +{actual_pct:.1f}%(达原价)"
                    else:
                        adjust_text = f"↑ +{price_change_pct:.1f}%"
                else:
                    if hit_floor:
                        actual_pct = (current_price - floor_price) / current_price * 100 if current_price > 0 else 0
                        adjust_text = f"↓ -{actual_pct:.1f}%(达保本)"
                    else:
                        adjust_text = f"↓ {price_change_pct:.1f}%"
            
            # 计算调整后的利润率（防止除以零）
            if suggested_price > 0 and cost >= 0:
                new_profit_rate = (suggested_price - cost) / suggested_price * 100
            else:
                new_profit_rate = 0
            
            # V3.0: 亏损/可修复状态显示
            loss_status = '🩸亏损' if is_loss else '✓'
            repair_status = '📈可修' if is_repairable else '--'
            
            # 滞销天数显示（仅滞销品有值）
            stagnant_display = f"{stagnant_days}天" if stagnant_days > 0 else '--'
            
            # 弹性来源简化显示（用于表格）
            if '学习' in elasticity_source:
                elasticity_display = f"🎓{elasticity:.2f}"
            elif '历史' in elasticity_source:
                elasticity_display = f"📊{elasticity:.2f}"
            elif '默认' in elasticity_source or '品类' in elasticity_source:
                elasticity_display = f"⚠️{elasticity:.2f}"
            else:
                elasticity_display = f"{elasticity:.2f}"
            
            table_data.append({
                '店内码': str(row.get('店内码', ''))[:10] or '--',
                '商品名称': str(row.get('商品名称', ''))[:15] or '--',
                '角色': f"{role_icon} {role_name}",
                '实售价': round(current_price, 2),
                '原价': round(original_price, 2),
                '成本': round(cost, 2),
                # V3.0: 真实保本价替代原来的保本价
                '真实保本价': round(floor_price, 2),
                '当前利润率': f"{profit_rate:.1f}%",
                '高光利润率': f"{highlight_margin:.1f}%",
                '亏损状态': loss_status,
                '滞销天数': stagnant_display,  # 新增滞销天数
                '日均销量': round(daily_sales, 1),
                '调整价格': round(suggested_price, 2),  # 可编辑的调整价格
                '调整后利润率': f"{new_profit_rate:.1f}%",
                '调整说明': adjust_text,
                '预估销量': f"{est_qty_change:+.1f}%" if abs(est_qty_change) > 0.1 else '--',
                '预估利润': f"{est_profit_change:+.1f}%" if abs(est_profit_change) > 0.1 else '--',
                '弹性系数': elasticity_display,  # V3.0: 显示弹性系数和来源
                # 隐藏字段
                '_allow_adjust': allow_adjust,
                '_direction': effective_direction,
                '_price_change': price_change_pct,
                '_cost': cost,
                '_elasticity': elasticity,  # 保存弹性系数用于学习
                '_elasticity_source': elasticity_source,  # 弹性来源
            })
        
        # 统计状态
        total = len(table_data)
        adjustable = sum(1 for t in table_data if t['_allow_adjust'])
        price_up_count = sum(1 for t in table_data if t.get('_price_change', 0) > 0.5)
        price_down_count = sum(1 for t in table_data if t.get('_price_change', 0) < -0.5)
        unchanged_count = total - price_up_count - price_down_count
        
        # 统计弹性来源分布
        learned_count = sum(1 for t in table_data if '🎓' in str(t.get('弹性系数', '')))
        history_count = sum(1 for t in table_data if '📊' in str(t.get('弹性系数', '')))
        default_count = sum(1 for t in table_data if '⚠️' in str(t.get('弹性系数', '')))
        
        # 方向提示
        direction_icon = "📈" if direction == 'up' else "📉"
        direction_text = "涨价" if direction == 'up' else "降价"
        role_text = role_filter if role_filter and role_filter != 'all' and role_filter != '_stagnant' else "全部"
        if role_filter == '_stagnant':
            role_text = "滞销品"
        
        # 计算实际调价方向（与用户选择可能不同）
        actual_up = price_up_count
        actual_down = price_down_count
        
        # 构建状态内容
        status_items = [
            html.Strong(f"{direction_icon} {direction_text}模式", className="me-2"),
            html.Span(f"| 目标: {target_margin:.0f}%", className="me-2"),
            html.Span(f"| 共{total}个", className="me-2"),
        ]
        
        if actual_up > 0:
            status_items.append(html.Span(f"↑{actual_up}", className="text-success me-1"))
        if actual_down > 0:
            status_items.append(html.Span(f"↓{actual_down}", className="text-primary me-1"))
        if unchanged_count > 0:
            status_items.append(html.Span(f"→{unchanged_count}", className="text-muted"))
        
        # 添加弹性来源统计提示
        if learned_count > 0 or history_count > 0:
            status_items.append(html.Span(" | ", className="text-muted mx-1"))
            status_items.append(html.Span("弹性:", className="text-muted"))
            if learned_count > 0:
                status_items.append(html.Span(f"🎓{learned_count}", className="text-success ms-1", title="从历史调价效果学习"))
            if history_count > 0:
                status_items.append(html.Span(f"📊{history_count}", className="text-info ms-1", title="历史数据"))
            if default_count > 0:
                status_items.append(html.Span(f"⚠️{default_count}", className="text-warning ms-1", title="品类默认值"))
        
        status_content = html.Span(status_items, className="small")
        
        # 创建DataTable - V3.0升级版（添加真实保本价、高光利润率等列）
        data_table = dash_table.DataTable(
            id='pricing-data-table',
            columns=[
                {'name': '店内码', 'id': '店内码', 'editable': False},
                {'name': '商品名称', 'id': '商品名称', 'editable': False},
                {'name': '角色', 'id': '角色', 'editable': False},
                {'name': '实售价', 'id': '实售价', 'type': 'numeric', 'editable': False},
                {'name': '原价', 'id': '原价', 'type': 'numeric', 'editable': False},
                {'name': '成本', 'id': '成本', 'type': 'numeric', 'editable': False},
                # V3.0: 真实保本价（含平台费）
                {'name': '真实保本价', 'id': '真实保本价', 'type': 'numeric', 'editable': False},
                {'name': '当前利润率', 'id': '当前利润率', 'editable': False},
                {'name': '高光利润率', 'id': '高光利润率', 'editable': False},
                {'name': '亏损状态', 'id': '亏损状态', 'editable': False},
                {'name': '滞销天数', 'id': '滞销天数', 'editable': False},  # 新增
                {'name': '日均销量', 'id': '日均销量', 'type': 'numeric', 'editable': False},
                {'name': '调整价格', 'id': '调整价格', 'type': 'numeric', 'editable': True},
                {'name': '调整后利润率', 'id': '调整后利润率', 'editable': False},
                {'name': '调整说明', 'id': '调整说明', 'editable': False},
                {'name': '预估销量', 'id': '预估销量', 'editable': False},
                {'name': '预估利润', 'id': '预估利润', 'editable': False},
                {'name': '弹性', 'id': '弹性系数', 'editable': False},  # V3.0: 弹性系数列
            ],
            data=table_data,
            editable=True,
            row_selectable='multi',
            selected_rows=[],
            page_size=20,
            page_action='native',
            style_table={'overflowX': 'auto', 'maxHeight': '500px', 'overflowY': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '6px 8px',
                'fontSize': '12px',
                'minWidth': '55px',
                'maxWidth': '90px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'border': '1px solid #dee2e6',
                'fontSize': '11px'
            },
            style_data_conditional=[
                # 角色列 - 左对齐
                {'if': {'column_id': '角色'}, 'textAlign': 'left', 'fontWeight': 'bold', 'fontSize': '11px'},
                # 商品名称 - 左对齐
                {'if': {'column_id': '商品名称'}, 'textAlign': 'left'},
                # 原价列 - 价格上限（蓝色底）
                {'if': {'column_id': '原价'}, 'backgroundColor': '#e3f2fd', 'color': '#1565c0'},
                # V3.0: 真实保本价列 - 价格下限（橙色底）
                {'if': {'column_id': '真实保本价'}, 'backgroundColor': '#fff3e0', 'color': '#e65100', 'fontWeight': 'bold'},
                # 调整价格列 - 可编辑（黄色底，加粗）
                {'if': {'column_id': '调整价格'}, 'backgroundColor': '#fff3cd', 'fontWeight': 'bold', 'fontSize': '13px'},
                # 当前利润率负值 - 红色
                {'if': {'filter_query': '{当前利润率} contains "-"', 'column_id': '当前利润率'}, 
                 'color': '#dc3545', 'fontWeight': 'bold', 'backgroundColor': '#ffeef0'},
                # 调整后利润率负值 - 红色
                {'if': {'filter_query': '{调整后利润率} contains "-"', 'column_id': '调整后利润率'}, 
                 'color': '#dc3545', 'fontWeight': 'bold'},
                # V3.0: 亏损状态显示红色
                {'if': {'filter_query': '{亏损状态} contains "亏损"', 'column_id': '亏损状态'}, 
                 'color': '#dc3545', 'fontWeight': 'bold', 'backgroundColor': '#ffeef0'},
                # 滞销天数 - 橙色高亮
                {'if': {'filter_query': '{滞销天数} ne "--"', 'column_id': '滞销天数'}, 
                 'color': '#e65100', 'fontWeight': 'bold', 'backgroundColor': '#fff3e0'},
                # 调整说明 - 涨价绿色
                {'if': {'filter_query': '{调整说明} contains "↑"', 'column_id': '调整说明'}, 
                 'color': '#198754', 'fontWeight': 'bold', 'backgroundColor': '#d4edda'},
                # 调整说明 - 降价蓝色
                {'if': {'filter_query': '{调整说明} contains "↓"', 'column_id': '调整说明'}, 
                 'color': '#0d6efd', 'fontWeight': 'bold', 'backgroundColor': '#cfe2ff'},
                # 调整说明 - 不建议红色
                {'if': {'filter_query': '{调整说明} contains "⛔"', 'column_id': '调整说明'}, 
                 'color': '#dc3545', 'backgroundColor': '#ffeef0'},
                # 预估利润正值 - 绿色
                {'if': {'filter_query': '{预估利润} contains "+"', 'column_id': '预估利润'}, 
                 'color': '#198754', 'fontWeight': 'bold'},
                # 预估利润负值 - 红色
                {'if': {'filter_query': '{预估利润} contains "-"', 'column_id': '预估利润'}, 
                 'color': '#dc3545'},
            ],
            # 列宽设置
            style_cell_conditional=[
                {'if': {'column_id': '店内码'}, 'width': '65px'},
                {'if': {'column_id': '商品名称'}, 'width': '100px'},
                {'if': {'column_id': '角色'}, 'width': '75px'},
                {'if': {'column_id': '实售价'}, 'width': '55px'},
                {'if': {'column_id': '原价'}, 'width': '55px'},
                {'if': {'column_id': '成本'}, 'width': '50px'},
                {'if': {'column_id': '真实保本价'}, 'width': '70px'},
                {'if': {'column_id': '当前利润率'}, 'width': '65px'},
                {'if': {'column_id': '高光利润率'}, 'width': '70px'},
                {'if': {'column_id': '亏损状态'}, 'width': '55px'},
                {'if': {'column_id': '滞销天数'}, 'width': '55px'},
                {'if': {'column_id': '日均销量'}, 'width': '55px'},
                {'if': {'column_id': '调整价格'}, 'width': '60px'},
                {'if': {'column_id': '调整后利润率'}, 'width': '75px'},
                {'if': {'column_id': '调整说明'}, 'width': '90px'},
                {'if': {'column_id': '预估销量'}, 'width': '60px'},
                {'if': {'column_id': '预估利润'}, 'width': '60px'},
                {'if': {'column_id': '弹性系数'}, 'width': '55px'},
            ],
            tooltip_header={
                '原价': '商品标价（价格上限）',
                '真实保本价': '含平台费8%的保本价（价格下限）',
                '高光利润率': '目标利润率参考值',
                '亏损状态': '实收价格 < 真实保本价',
                '滞销天数': '连续无销量的天数',
                '调整价格': '调整后的售价（可手动修改）',
                '预估销量': '基于弹性系数预测（仅供参考）',
                '预估利润': '基于弹性系数预测（仅供参考）',
                '弹性系数': '🎓=学习数据(从历史调价效果反推)  📊=历史数据  ⚠️=品类默认值',
            },
            tooltip_delay=300,
            tooltip_duration=3000,
        )
        
        return data_table, table_data, status_content
        
    except Exception as e:
        print(f"[调价V2] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"加载失败: {str(e)}", className="text-danger text-center py-4"), [], ""


# ==================== 旧版回调代码已删除 ====================
# 旧版 update_pricing_table 已由 update_pricing_table_v2 替代


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
        # 过滤掉 None 元素
        pricing_data = [p for p in pricing_data if p is not None]
        if not pricing_data:
            return html.Div("数据为空", className="text-muted text-center py-3")
        
        # 统计汇总
        total_products = len(pricing_data)
        adjusted_products = sum(1 for p in pricing_data if p and p.get('调整价格') != p.get('实售价'))
        
        total_current_profit = 0
        total_new_profit = 0
        
        for p in pricing_data:
            if not p:
                continue
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
     State("free-pricing-data-store", "data"),
     State("db-store-filter", "value"),
     State("pricing-channel-filter", "value"),
     State("free-pricing-channel", "value")],
    prevent_initial_call=True
)
def export_pricing_plan(n_clicks, pricing_data, free_pricing_data, store, channel, free_channel):
    """导出调价方案Excel - 支持智能调价和自由调价"""
    if not n_clicks:
        raise PreventUpdate
    
    # 优先使用有数据的store
    export_data = None
    export_channel = None
    if free_pricing_data and len(free_pricing_data) > 0:
        export_data = free_pricing_data
        export_channel = free_channel
    elif pricing_data and len(pricing_data) > 0:
        export_data = pricing_data
        export_channel = channel
    
    if not export_data:
        raise PreventUpdate
    
    try:
        import io
        from datetime import datetime
        
        # 创建DataFrame
        export_df = pd.DataFrame(export_data)
        
        # 选择导出列
        export_columns = [
            '店内码', '商品名称', '分类', '实售价', '成本', '利润率',
            '日均销量', '弹性系数', '调整价格', '预估销量变化', '预估利润变化'
        ]
        export_df = export_df[[c for c in export_columns if c in export_df.columns]]
        
        # 统计汇总
        total_products = len(export_data)
        adjusted_products = sum(1 for p in export_data if p.get('调整价格') != p.get('实售价'))
        
        # 计算总利润变化
        total_current_profit = 0
        total_new_profit = 0
        for p in export_data:
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
                    export_channel if export_channel and export_channel != 'all' else '全部渠道',
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
    [Input("pricing-data-store", "data"),
     Input("free-pricing-data-store", "data")],
    prevent_initial_call=True
)
def toggle_export_button(pricing_data, free_pricing_data):
    """启用/禁用导出按钮 - 智能调价或自由调价有数据时启用"""
    has_smart_data = pricing_data and len(pricing_data) > 0
    has_free_data = free_pricing_data and len(free_pricing_data) > 0
    return not (has_smart_data or has_free_data)


# ==================== Tab 2: 自由调价回调 ====================

# ==================== 快捷场景回调 ====================

@callback(
    [Output("quick-scene-stats", "children"),
     Output("quick-scene-store", "data"),
     Output("quick-scene-alert", "children"),
     Output("free-pricing-profit-min", "value"),
     Output("free-pricing-profit-max", "value"),
     Output("free-pricing-sales-min", "value"),
     Output("free-pricing-sales-max", "value"),
     Output("free-pricing-adjust-type", "value"),
     Output("free-pricing-adjust-value", "value"),
     # 场景按钮样式 - 选中状态
     Output("quick-scene-profit-drop", "outline"),
     Output("quick-scene-profit-drop", "color"),
     Output("quick-scene-profit-amount-drop", "outline"),
     Output("quick-scene-profit-amount-drop", "color"),
     Output("quick-scene-sales-drop", "outline"),
     Output("quick-scene-sales-drop", "color"),
     Output("quick-scene-stagnant", "outline"),
     Output("quick-scene-stagnant", "color"),
     Output("quick-scene-price-opportunity", "outline"),
     Output("quick-scene-price-opportunity", "color")],
    [Input("quick-scene-profit-drop", "n_clicks"),
     Input("quick-scene-profit-amount-drop", "n_clicks"),
     Input("quick-scene-sales-drop", "n_clicks"),
     Input("quick-scene-stagnant", "n_clicks"),
     Input("quick-scene-price-opportunity", "n_clicks"),
     Input("quick-scene-clear", "n_clicks"),
     Input("pricing-tabs", "active_tab")],
    [State("db-store-filter", "value"),
     State("free-pricing-channel", "value")],
    prevent_initial_call=True
)
def handle_quick_scene(n_profit, n_profit_amount, n_sales, n_stagnant, n_opportunity, n_clear, active_tab, store, channel):
    """处理快捷场景按钮点击"""
    from dash import ctx, no_update
    from .diagnosis_analysis import get_profit_rate_drop_products, get_traffic_drop_products
    from .pricing_engine import get_stagnant_products
    from .price_opportunity_analyzer import get_price_increase_opportunity_products
    
    triggered_id = ctx.triggered_id
    
    # 默认值
    empty_stats = ""
    empty_alert = ""
    # 默认按钮样式 - 全部outline
    default_styles = (True, "danger", True, "danger", True, "warning", True, "secondary", True, "success")
    
    # 清除场景
    if triggered_id == "quick-scene-clear":
        return empty_stats, None, "", None, None, None, None, "percent", 5, *default_styles
    
    # 如果是Tab切换到自由调价，显示场景统计
    if triggered_id == "pricing-tabs" and active_tab == "tab-free":
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            return empty_stats, None, empty_alert, no_update, no_update, no_update, no_update, no_update, no_update, *default_styles
        
        try:
            # 内存优化：使用视图筛选门店
            if store:
                store_list = store if isinstance(store, list) else [store]
                df = apply_filters_view(GLOBAL_DATA, selected_stores=store_list)
            else:
                df = GLOBAL_DATA  # 不筛选，直接用原数据（视图）
            
            # 统计各场景商品数
            profit_drop_count = 0
            profit_amount_drop_count = 0
            sales_drop_count = 0
            stagnant_count = 0
            
            try:
                profit_drop_df = get_profit_rate_drop_products(df)
                profit_drop_count = len(profit_drop_df) if profit_drop_df is not None else 0
                # 利润额下滑：从利润率下滑商品中筛选利润额也下滑的
                if profit_drop_df is not None and not profit_drop_df.empty:
                    if '近7天利润额' in profit_drop_df.columns and '前7天利润额' in profit_drop_df.columns:
                        profit_amount_drop_df = profit_drop_df[profit_drop_df['近7天利润额'] < profit_drop_df['前7天利润额']]
                        profit_amount_drop_count = len(profit_amount_drop_df)
            except:
                pass
            
            try:
                sales_drop_df = get_traffic_drop_products(df)
                sales_drop_count = len(sales_drop_df) if sales_drop_df is not None else 0
            except:
                pass
            
            try:
                stagnant_df = get_stagnant_products(df, store=store if isinstance(store, str) else None, level='all')
                stagnant_count = len(stagnant_df) if stagnant_df is not None else 0
            except:
                pass
            
            try:
                opportunity_df = get_price_increase_opportunity_products(df, selected_days=7)
                opportunity_count = len(opportunity_df) if opportunity_df is not None else 0
            except:
                pass
            
            stats = html.Div([
                dbc.Badge(f"📉 利润率下滑 {profit_drop_count}个", color="danger" if profit_drop_count > 0 else "secondary"),
                html.Span(" · ", className="text-muted mx-1"),
                dbc.Badge(f"💰 利润额下滑 {profit_amount_drop_count}个", color="warning" if profit_amount_drop_count > 0 else "secondary"),
                html.Span(" · ", className="text-muted mx-1"),
                dbc.Badge(f"🔻 销量下滑 {sales_drop_count}个", color="danger" if sales_drop_count > 0 else "secondary"),
                html.Span(" · ", className="text-muted mx-1"),
                dbc.Badge(f"🐌 滞销清仓 {stagnant_count}个", color="warning" if stagnant_count > 0 else "secondary"),
                html.Span(" · ", className="text-muted mx-1"),
                dbc.Badge(f"💡 提价机会 {opportunity_count}个", color="success" if opportunity_count > 0 else "secondary"),
            ])
            return stats, None, empty_alert, no_update, no_update, no_update, no_update, no_update, no_update, *default_styles
        except Exception as e:
            print(f"[快捷场景] 统计失败: {e}")
            return empty_stats, None, empty_alert, no_update, no_update, no_update, no_update, no_update, no_update, *default_styles
    
    # 处理场景按钮点击 - 选中的按钮 outline=False，其他保持 outline=True
    if triggered_id == "quick-scene-profit-drop":
        # 利润率下滑 → 筛选利润率下滑商品，建议提价5%
        alert = dbc.Alert([
            html.Strong("📉 利润率下滑场景"), 
            " 已选中，建议提价5%，请确认后点击「批量计算」",
        ], color="danger", dismissable=True, className="py-2")
        # 选中样式：profit_drop不是outline（10个值：5个场景×2个属性）
        styles = (False, "danger", True, "danger", True, "warning", True, "secondary", True, "success")
        return no_update, "profit_drop", alert, None, None, None, None, "percent", 5, *styles
    
    elif triggered_id == "quick-scene-profit-amount-drop":
        # 利润额下滑 → 筛选利润额减少的商品，建议提价5%
        alert = dbc.Alert([
            html.Strong("💰 利润额下滑场景"), 
            " 已选中，建议提价5%，请确认后点击「批量计算」",
        ], color="danger", dismissable=True, className="py-2")
        # 选中样式：profit_amount_drop不是outline
        styles = (True, "danger", False, "danger", True, "warning", True, "secondary", True, "success")
        return no_update, "profit_amount_drop", alert, None, None, None, None, "percent", 5, *styles
    
    elif triggered_id == "quick-scene-sales-drop":
        # 销量下滑 → 筛选销量下滑商品，建议降价8%
        alert = dbc.Alert([
            html.Strong("🔻 销量下滑场景"), 
            " 已选中，建议降价10%，请确认后点击「批量计算」",
        ], color="warning", dismissable=True, className="py-2")
        # 选中样式：sales_drop不是outline
        styles = (True, "danger", True, "danger", False, "warning", True, "secondary", True, "success")
        return no_update, "sales_drop", alert, None, None, None, None, "percent", -10, *styles
    
    elif triggered_id == "quick-scene-stagnant":
        # 滞销清仓 → 筛选滞销品，建议降价15%
        alert = dbc.Alert([
            html.Strong("🐌 滞销清仓场景"), 
            " 已选中，建议降价15%，请确认后点击「批量计算」",
        ], color="secondary", dismissable=True, className="py-2")
        # 选中样式：stagnant不是outline
        styles = (True, "danger", True, "danger", True, "warning", False, "secondary", True, "success")
        return no_update, "stagnant", alert, None, None, None, None, "percent", -15, *styles
    
    elif triggered_id == "quick-scene-price-opportunity":
        # 提价机会 → 筛选可安全提价的商品，建议提价5%
        alert = dbc.Alert([
            html.Strong("💡 提价机会场景"), 
            " 已选中，智能提价建议3-8%，请确认后点击「批量计算」",
        ], color="success", dismissable=True, className="py-2")
        # 选中样式：price_opportunity不是outline
        styles = (True, "danger", True, "danger", True, "warning", True, "secondary", False, "success")
        return no_update, "price_opportunity", alert, None, None, None, None, "percent", 5, *styles
    
    return empty_stats, None, empty_alert, no_update, no_update, no_update, no_update, no_update, no_update, *default_styles


@callback(
    Output("free-pricing-adjust-unit", "children"),
    Input("free-pricing-adjust-type", "value"),
    prevent_initial_call=True
)
def update_adjust_unit(adjust_type):
    """更新调整值单位"""
    if adjust_type == 'percent':
        return "%"
    elif adjust_type == 'fixed':
        return "元"
    else:  # target_margin
        return "%"


@callback(
    Output("free-pricing-current-settings", "children"),
    [Input("free-pricing-adjust-type", "value"),
     Input("free-pricing-adjust-value", "value"),
     Input("free-pricing-data-store", "data")],
    prevent_initial_call=True
)
def update_current_settings(adjust_type, adjust_value, data_store):
    """实时显示当前调价参数设置"""
    if adjust_value is None or data_store is None:
        return ""
    
    # 解析调整方式
    type_map = {
        'percent': '百分比',
        'fixed': '固定金额',
        'target_margin': '目标利润率'
    }
    type_text = type_map.get(adjust_type, '百分比')
    
    # 格式化调整值
    if adjust_type == 'percent':
        if adjust_value > 0:
            adjust_text = f"提价{adjust_value}%"
        elif adjust_value < 0:
            adjust_text = f"降价{abs(adjust_value)}%"
        else:
            adjust_text = "不调整"
    elif adjust_type == 'fixed':
        if adjust_value > 0:
            adjust_text = f"提价{adjust_value}元"
        elif adjust_value < 0:
            adjust_text = f"降价{abs(adjust_value)}元"
        else:
            adjust_text = "不调整"
    else:  # target_margin
        adjust_text = f"目标利润率{adjust_value}%"
    
    # 获取商品数量
    product_count = len(data_store) if data_store else 0
    
    return html.Span([
        "当前设置: ",
        html.Strong(adjust_text, className="text-primary"),
        f" ({type_text}) | 预计影响: ",
        html.Strong(f"{product_count}个商品", className="text-success")
    ])


@callback(
    Output("free-pricing-category", "options"),
    [Input("pricing-tabs", "active_tab"),
     Input("quick-scene-store", "data")],
    State("db-store-filter", "value"),
    prevent_initial_call=True
)
def update_free_category_options(active_tab, quick_scene, store):
    """更新自由调价的分类选项"""
    if active_tab != 'tab-free':
        raise PreventUpdate
    
    GLOBAL_DATA = get_real_global_data()
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return []
    
    # 内存优化：使用视图筛选门店
    if store:
        store_list = store if isinstance(store, list) else [store]
        df = apply_filters_view(GLOBAL_DATA, selected_stores=store_list)
    else:
        df = GLOBAL_DATA
    
    # 获取分类
    cat_col = '一级分类名' if '一级分类名' in df.columns else ('一级分类' if '一级分类' in df.columns else None)
    if cat_col:
        categories = df[cat_col].dropna().unique().tolist()
        # 排除耗材
        categories = [c for c in categories if c != '耗材']
        return [{'label': c, 'value': c} for c in sorted(categories)]
    
    return []


@callback(
    Output("free-pricing-channel", "options"),
    Input("pricing-tabs", "active_tab"),
    State("db-store-filter", "value"),
    prevent_initial_call=True
)
def update_free_channel_options(active_tab, store):
    """更新自由调价的渠道选项"""
    if active_tab != 'tab-free':
        raise PreventUpdate
    
    GLOBAL_DATA = get_real_global_data()
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return [{'label': '全部渠道', 'value': 'all'}]
    
    # 内存优化：使用视图筛选门店
    if store:
        store_list = store if isinstance(store, list) else [store]
        df = apply_filters_view(GLOBAL_DATA, selected_stores=store_list)
    else:
        df = GLOBAL_DATA
    
    channel_col = next((c for c in ['渠道', '平台', 'channel'] if c in df.columns), None)
    if channel_col:
        channels = df[channel_col].dropna().unique().tolist()
        options = [{'label': '全部渠道', 'value': 'all'}]
        for ch in sorted(channels):
            options.append({'label': str(ch), 'value': str(ch)})
        return options
    
    return [{'label': '全部渠道', 'value': 'all'}]


@callback(
    [Output("free-pricing-table-container", "children"),
     Output("free-pricing-data-store", "data"),
     Output("free-pricing-stats", "children"),
     Output("free-pricing-calc-alert", "children")],
    [Input("free-pricing-filter-btn", "n_clicks"),
     Input("free-pricing-calc-btn", "n_clicks"),
     Input("quick-scene-store", "data"),  # 快捷场景变化时也触发（包括象限场景）
     Input("calculator-date-range", "value")],  # V3.1：监听时间范围变化
    [State("pricing-quadrant-filter", "data"),  # V3.1：读取象限筛选数据
     State("free-pricing-category", "value"),
     State("free-pricing-profit-min", "value"),
     State("free-pricing-profit-max", "value"),
     State("free-pricing-sales-min", "value"),
     State("free-pricing-sales-max", "value"),
     State("free-pricing-price-min", "value"),
     State("free-pricing-price-max", "value"),
     State("free-pricing-search", "value"),
     State("free-pricing-channel", "value"),
     State("free-pricing-adjust-type", "value"),
     State("free-pricing-adjust-value", "value"),
     State("db-store-filter", "value"),
     State("free-pricing-data-store", "data")],
    prevent_initial_call=True
)
def update_free_pricing_table(n_filter, n_calc, quick_scene, selected_days,
                               quadrant_filter, category, profit_min, profit_max, 
                               sales_min, sales_max, price_min, price_max,
                               search_text, channel, adjust_type, adjust_value,
                               store, existing_data):
    """自由调价表格更新 - 支持快捷场景和独立日期选择"""
    from dash import dash_table, ctx
    from .pricing_engine import get_product_elasticity, predict_profit_change, get_stagnant_products
    from .diagnosis_analysis import get_profit_rate_drop_products, get_traffic_drop_products
    from .price_opportunity_analyzer import get_price_increase_opportunity_products
    
    triggered_id = ctx.triggered_id
    
    # 如果是清除场景，显示提示
    if triggered_id == "quick-scene-store" and quick_scene is None:
        return html.Div("请选择快捷场景或点击「筛选商品」", className="text-muted text-center py-4"), [], "", None
    
    # 🔄 使用全量数据（不受顶部日期影响）
    GLOBAL_FULL_DATA = get_real_global_full_data()
    
    # 回退机制：如果GLOBAL_FULL_DATA不可用，使用GLOBAL_DATA
    if GLOBAL_FULL_DATA is None or GLOBAL_FULL_DATA.empty:
        print("[计算器] GLOBAL_FULL_DATA不可用，回退到GLOBAL_DATA")
        GLOBAL_FULL_DATA = get_real_global_data()
        if GLOBAL_FULL_DATA is None or GLOBAL_FULL_DATA.empty:
            return html.Div("请先加载数据", className="text-muted text-center py-4"), [], "", None
    
    try:
        # 📅 根据独立日期选择器切片数据
        max_date = None
        recent_start = None
        compare_start = None
        compare_end = None
        
        if selected_days and selected_days > 0:
            date_col = '日期' if '日期' in GLOBAL_FULL_DATA.columns else '下单时间'
            if date_col in GLOBAL_FULL_DATA.columns:
                full_df_with_date = GLOBAL_FULL_DATA  # 直接引用
                full_df_with_date[date_col] = pd.to_datetime(full_df_with_date[date_col])
                max_date = full_df_with_date[date_col].max()
                
                # 为了支持对比分析，实际查询 2x+1 天数据
                actual_query_days = selected_days * 2 + 1
                start_date = max_date - timedelta(days=actual_query_days - 1)
                df = full_df_with_date[full_df_with_date[date_col] >= start_date]  # 移除.copy()
                
                # 计算对比时间范围（用于列标题显示）
                recent_start = max_date - timedelta(days=selected_days - 1)
                compare_end = recent_start - timedelta(days=1)
                compare_start = compare_end - timedelta(days=selected_days - 1)
                
                print(f"[计算器日期] 用户选择{selected_days}天")
                print(f"  近{selected_days}天: {recent_start.strftime('%m-%d')} ~ {max_date.strftime('%m-%d')}")
                print(f"  前{selected_days}天: {compare_start.strftime('%m-%d')} ~ {compare_end.strftime('%m-%d')}")
                print(f"  实际查询: {actual_query_days}天用于对比分析")
            else:
                df = GLOBAL_FULL_DATA  # 直接引用
        else:
            # 全部数据
            df = GLOBAL_FULL_DATA  # 直接引用
            print(f"[计算器日期] 使用全部数据: {len(df)}条")
        
        # 门店筛选
        if df is None or df.empty:
            return html.Div("数据为空", className="text-muted text-center py-4"), [], ""
        
        # 注：这里的df.copy()是必要的，因为后面需要修改数据
        df = df.copy()
        store_col = next((c for c in ['门店名称', '门店', 'store'] if c in df.columns), None)
        if store and store_col:
            if isinstance(store, list):
                df = df[df[store_col].isin(store)]
            else:
                df = df[df[store_col] == store]
        
        # ===== 快捷场景处理 =====
        scene_product_codes = None  # 场景筛选的商品店内码列表
        scene_name = ""
        scene_comparison_data = {}  # 存储场景的对比数据
        
        if quick_scene:
            try:
                # V3.1：处理象限场景（从六象限跳转）
                if isinstance(quick_scene, dict) and quick_scene.get('type') == 'quadrant':
                    quadrant_name = quick_scene.get('quadrant', '')
                    scene_name = f"📊 {quadrant_name}"
                    
                    # 从quadrant_filter中获取商品列表
                    if quadrant_filter and 'products' in quadrant_filter:
                        products_list = quadrant_filter['products']
                        if products_list:
                            # 提取店内码列表
                            scene_product_codes = [str(p.get('店内码', '')) for p in products_list if p.get('店内码')]
                            print(f"[象限联动] 筛选到 {len(scene_product_codes)} 个{quadrant_name}商品")
                    
                elif quick_scene == "profit_drop":
                    # 利润率下滑场景 - 获取利润率下滑商品
                    scene_df = get_profit_rate_drop_products(df)
                    if scene_df is not None and not scene_df.empty:
                        scene_product_codes = scene_df['店内码'].dropna().astype(str).tolist()
                        scene_name = "📉 利润率下滑"
                        # 保存对比数据（需要解析字符串格式）
                        for _, row in scene_df.iterrows():
                            code = str(row.get('店内码', ''))
                            if code:
                                # 解析字符串格式的利润率（去掉%号）
                                try:
                                    recent_rate = float(str(row.get('近7天利润率', '0')).replace('%', ''))
                                    prev_rate = float(str(row.get('前7天利润率', '0')).replace('%', ''))
                                    change = float(str(row.get('下滑幅度', '0')).replace('%', ''))
                                except (ValueError, AttributeError):
                                    recent_rate = 0
                                    prev_rate = 0
                                    change = 0
                                
                                scene_comparison_data[code] = {
                                    '近7天利润率': recent_rate,
                                    '前7天利润率': prev_rate,
                                    '利润率变化': change,
                                }
                
                elif quick_scene == "profit_amount_drop":
                    # 利润额下滑场景 - 获取利润额减少的商品
                    scene_df = get_profit_rate_drop_products(df)
                    if scene_df is not None and not scene_df.empty:
                        # 进一步筛选：利润额也下滑
                        if '近7天利润额' in scene_df.columns and '前7天利润额' in scene_df.columns:
                            scene_df = scene_df[scene_df['近7天利润额'] < scene_df['前7天利润额']]
                        scene_product_codes = scene_df['店内码'].dropna().astype(str).tolist()
                        scene_name = "💰 利润额下滑"
                        # 保存对比数据
                        for _, row in scene_df.iterrows():
                            code = str(row.get('店内码', ''))
                            if code:
                                scene_comparison_data[code] = {
                                    '近7天利润额': row.get('近7天利润额', 0),
                                    '前7天利润额': row.get('前7天利润额', 0),
                                }
                
                elif quick_scene == "sales_drop":
                    # 销量下滑场景 - 获取销量下滑商品
                    scene_df = get_traffic_drop_products(df)
                    if scene_df is not None and not scene_df.empty:
                        if '店内码' in scene_df.columns:
                            scene_product_codes = scene_df['店内码'].dropna().astype(str).tolist()
                        elif '商品名称' in scene_df.columns:
                            # 通过商品名称匹配
                            scene_product_codes = scene_df['商品名称'].dropna().tolist()
                        scene_name = "🔻 销量下滑"
                        # 保存对比数据（使用总销量而非日均）
                        for _, row in scene_df.iterrows():
                            code = str(row.get('店内码', '')) if '店内码' in scene_df.columns else str(row.get('商品名称', ''))
                            if code:
                                scene_comparison_data[code] = {
                                    '近7天总销量': row.get('近7天销量', 0),
                                    '前7天总销量': row.get('前7天销量', 0),
                                    '销量变化': row.get('跌幅', 0),
                                }
                
                elif quick_scene == "stagnant":
                    # 滞销清仓场景 - 获取滞销商品
                    scene_df = get_stagnant_products(df, store=store if isinstance(store, str) else None, level='all')
                    if scene_df is not None and not scene_df.empty:
                        if '店内码' in scene_df.columns:
                            scene_product_codes = scene_df['店内码'].dropna().astype(str).tolist()
                            # 保存滞销天数映射，用于后续显示
                            stagnant_days_map = dict(zip(
                                scene_df['店内码'].astype(str), 
                                scene_df.get('滞销天数', pd.Series([0]*len(scene_df)))
                            ))
                        elif '商品名称' in scene_df.columns:
                            scene_product_codes = scene_df['商品名称'].dropna().tolist()
                            stagnant_days_map = dict(zip(
                                scene_df['商品名称'], 
                                scene_df.get('滞销天数', pd.Series([0]*len(scene_df)))
                            ))
                        else:
                            stagnant_days_map = {}
                        scene_name = "🐌 滞销清仓"
                
                elif quick_scene == "price_opportunity":
                    # 提价机会场景
                    scene_df = get_price_increase_opportunity_products(df, selected_days=selected_days if selected_days else 7)
                    if scene_df is not None and not scene_df.empty:
                        if '店内码' in scene_df.columns:
                            scene_product_codes = scene_df['店内码'].dropna().astype(str).tolist()
                        elif '商品名称' in scene_df.columns:
                            scene_product_codes = scene_df['商品名称'].dropna().tolist()
                        scene_name = "💡 提价机会"
                        # 调试：打印第一个商品的数据
                        if not scene_df.empty:
                            print(f"[提价机会调试] scene_df列名: {scene_df.columns.tolist()}")
                            first_row = scene_df.iloc[0]
                            print(f"[提价机会调试] 第一行数据: {first_row.to_dict()}")
                            days = selected_days if selected_days else 7
                            print(f"[提价机会调试] selected_days: {selected_days}, 使用days: {days}")
                        
                        # 保存对比数据
                        for _, row in scene_df.iterrows():
                            code = str(row.get('店内码', '')) if '店内码' in scene_df.columns else str(row.get('商品名称', ''))
                            if code:
                                days = selected_days if selected_days else 7
                                scene_comparison_data[code] = {
                                    f'近{days}天总销量': row.get(f'近{days}天销量', 0),  # 注意：scene_df中是"销量"，这里统一为"总销量"
                                    f'前{days}天总销量': row.get(f'前{days}天销量', 0),
                                    '销量变化': row.get('销量变化', 0),
                                    '建议提价幅度': row.get('建议提价幅度', 5),
                                }
                
            except Exception as e:
                print(f"[快捷场景] 获取商品失败: {e}")
        
        # 准备调价数据
        products_df = prepare_pricing_data_v2(df, channel)
        if products_df.empty:
            return html.Div("无可调价商品", className="text-muted text-center py-4"), [], "", None
        
        # ===== 应用快捷场景筛选 =====
        stagnant_days_map = locals().get('stagnant_days_map', {})  # 获取滞销天数映射
        
        # V3.1：支持象限场景筛选
        is_quadrant_scene = isinstance(quick_scene, dict) and quick_scene.get('type') == 'quadrant'
        
        if scene_product_codes and (quick_scene in ["profit_drop", "profit_amount_drop", "sales_drop", "stagnant", "price_opportunity"] or is_quadrant_scene):
            # 优先按店内码匹配
            if '店内码' in products_df.columns:
                code_mask = products_df['店内码'].astype(str).isin(scene_product_codes)
                if code_mask.sum() > 0:
                    products_df = products_df[code_mask]
                    print(f"[场景筛选] 按店内码筛选到 {len(products_df)} 个商品")
                else:
                    # 尝试按商品名称匹配
                    name_mask = products_df['商品名称'].isin(scene_product_codes)
                    if name_mask.sum() > 0:
                        products_df = products_df[name_mask]
                        print(f"[场景筛选] 按商品名称筛选到 {len(products_df)} 个商品")
            elif '商品名称' in products_df.columns:
                name_mask = products_df['商品名称'].isin(scene_product_codes)
                products_df = products_df[name_mask]
                print(f"[场景筛选] 按商品名称筛选到 {len(products_df)} 个商品")
        
        # ===== 应用常规筛选条件 =====
        
        # 分类筛选
        if category:
            cat_col = '一级分类名' if '一级分类名' in products_df.columns else ('一级分类' if '一级分类' in products_df.columns else None)
            if cat_col:
                products_df = products_df[products_df[cat_col] == category]
        
        # 利润率筛选
        if profit_min is not None:
            products_df = products_df[products_df['利润率'] >= profit_min]
        if profit_max is not None:
            products_df = products_df[products_df['利润率'] <= profit_max]
        
        # 销量筛选
        if sales_min is not None:
            products_df = products_df[products_df['日均销量'] >= sales_min]
        if sales_max is not None:
            products_df = products_df[products_df['日均销量'] <= sales_max]
        
        # 价格筛选
        if price_min is not None:
            products_df = products_df[products_df['实收价格'] >= price_min]
        if price_max is not None:
            products_df = products_df[products_df['实收价格'] <= price_max]
        
        # 搜索筛选
        if search_text:
            search_text = str(search_text).strip().lower()
            name_mask = products_df['商品名称'].astype(str).str.lower().str.contains(search_text, na=False)
            code_mask = products_df['店内码'].astype(str).str.lower().str.contains(search_text, na=False)
            products_df = products_df[name_mask | code_mask]
        
        if products_df.empty:
            return html.Div("筛选后无商品", className="text-muted text-center py-4"), [], "", None
        
        # 不再限制数量，展示全部商品（已有Redis缓存和分页支持）
        # products_df = products_df.head(500)  # 已移除限制
        
        # 构建表格数据
        table_data = []
        channel_name = channel if channel and channel != 'all' else '美团'
        
        # 是否计算调价
        is_calc = triggered_id == 'free-pricing-calc-btn' and adjust_value is not None
        
        # ===== 快捷场景的预设调整策略（已去除自动计算） =====
        # 快捷场景只提供建议值，用户需手动点击"批量计算"才执行
        
        for _, row in products_df.iterrows():
            code = str(row.get('店内码', '') or '')
            category_name = str(row.get('一级分类名', '') or row.get('一级分类', '') or '')
            elasticity, elasticity_source = get_product_elasticity(code, channel_name, category_name, None)
            
            try:
                current_price = float(row.get('实收价格', 0) or 0)
                cost = float(row.get('单品成本', 0) or 0)
                original_price = float(row.get('商品原价', 0) or 0)
                if original_price <= 0:
                    original_price = current_price
                daily_sales = float(row.get('日均销量', 0) or 0)
                total_sales = float(row.get('总销量', 0) or 0)  # 30天总销量
                profit_rate = float(row.get('利润率', 0) or 0)
                # V3.0: 获取真实保本价
                real_breakeven = float(row.get('真实保本价', 0) or 0)
                is_loss = bool(row.get('是否亏损', False))
                allow_adjust = bool(row.get('允许调价', True))
                role_name = str(row.get('商品角色', '正常款') or '正常款')
            except (ValueError, TypeError):
                continue
            
            if current_price <= 0:
                continue
            
            # V3.0: 使用真实保本价（成本/0.92），而非单纯成本
            # 真实保本价 = 成本 / (1 - 平台费率8%) = 成本 × 1.087
            if real_breakeven > 0:
                floor_price = real_breakeven
            elif cost > 0:
                floor_price = cost / 0.92  # 计算真实保本价
            else:
                floor_price = 0.01
            ceiling_price = original_price
            
            # 计算调整后价格
            new_price = current_price
            adjust_text = "--"
            
            if is_calc:
                adjust_val = float(adjust_value or 0)
                
                if adjust_type == 'percent':
                    # 百分比调整（正数涨，负数降）
                    new_price = current_price * (1 + adjust_val / 100)
                elif adjust_type == 'fixed':
                    # 固定金额调整
                    new_price = current_price + adjust_val
                elif adjust_type == 'target_margin':
                    # 目标利润率（基于真实保本价计算）
                    if floor_price > 0 and adjust_val < 100:
                        # 目标价格 = 保本价 / (1 - 目标利润率)
                        new_price = floor_price / (1 - adjust_val / 100)
                    else:
                        new_price = current_price
                
                # ===== V3.0 边界约束 =====
                # 1. 不允许调价的商品保持原价
                if not allow_adjust:
                    new_price = current_price
                    adjust_text = "⛔ 不建议调整"
                else:
                    # 2. 应用边界：不低于保本价，不高于原价
                    new_price = max(floor_price, min(ceiling_price, new_price))
                    new_price = round(new_price, 2)
                    
                    # 3. 边界判断
                    hit_ceiling = new_price >= ceiling_price * 0.99
                    hit_floor = new_price <= floor_price * 1.01
                    already_at_ceiling = current_price >= ceiling_price * 0.99
                    already_at_floor = current_price <= floor_price * 1.01
                    
                    # 4. 调整说明（参照智能调价的完整逻辑）
                    price_change_pct = (new_price - current_price) / current_price * 100 if current_price > 0 else 0
                    
                    if already_at_ceiling and adjust_val > 0:
                        adjust_text = "🚫 已达原价上限"
                    elif already_at_floor and adjust_val < 0:
                        adjust_text = "🚫 已达保本下限"
                    elif abs(price_change_pct) < 0.5:
                        adjust_text = "→ 无变化"
                    elif hit_ceiling:
                        actual_pct = (ceiling_price - current_price) / current_price * 100 if current_price > 0 else 0
                        adjust_text = f"⚠️ +{actual_pct:.1f}%(达原价)"
                    elif hit_floor:
                        actual_pct = (current_price - floor_price) / current_price * 100 if current_price > 0 else 0
                        adjust_text = f"⚠️ -{actual_pct:.1f}%(达保本)"
                    elif price_change_pct > 0:
                        adjust_text = f"↑ +{price_change_pct:.1f}%"
                    else:
                        adjust_text = f"↓ {price_change_pct:.1f}%"
            
            # 计算调整后利润率（基于真实保本价的成本）
            new_profit_rate = (new_price - cost) / new_price * 100 if new_price > 0 else 0
            
            # 预估变化
            est_qty = "--"
            est_profit = "--"
            if is_calc and new_price != current_price and allow_adjust:
                prediction = predict_profit_change(current_price, new_price, cost, daily_sales, elasticity, channel_name)
                if prediction:
                    est_qty = f"{prediction.get('qty_change_rate', 0):+.1f}%"
                    est_profit = f"{prediction.get('profit_change_rate', 0):+.1f}%"
            
            # 滞销天数（仅滞销清仓场景有值）
            stagnant_days = stagnant_days_map.get(code, stagnant_days_map.get(str(row.get('商品名称', '')), '--'))
            if stagnant_days != '--':
                stagnant_days = f"{int(stagnant_days)}天"
            
            # 对比数据（仅在对应场景显示）
            comparison_info = scene_comparison_data.get(code, {})
            # 使用动态天数读取字段
            days_label = selected_days if selected_days else 7
            recent_profit_rate = comparison_info.get(f'近{days_label}天利润率', comparison_info.get('近7天利润率', '--'))
            prev_profit_rate = comparison_info.get(f'前{days_label}天利润率', comparison_info.get('前7天利润率', '--'))
            profit_change = comparison_info.get('利润率变化', '--')
            # 销量字段：销量下滑场景显示总销量，其他场景为空
            recent_sales = comparison_info.get(f'近{days_label}天总销量', comparison_info.get('近7天总销量', '--'))
            prev_sales = comparison_info.get(f'前{days_label}天总销量', comparison_info.get('前7天总销量', '--'))
            sales_change = comparison_info.get('销量变化', '--')
            
            # 格式化对比数据（数值型才需要格式化）
            if recent_profit_rate != '--' and isinstance(recent_profit_rate, (int, float)):
                try:
                    recent_profit_rate = f"{float(recent_profit_rate):.1f}%"
                    prev_profit_rate = f"{float(prev_profit_rate):.1f}%"
                    if profit_change != '--' and isinstance(profit_change, (int, float)):
                        profit_change = f"{float(profit_change):+.1f}%"
                except (ValueError, TypeError):
                    recent_profit_rate = '--'
                    prev_profit_rate = '--'
                    profit_change = '--'
            
            if recent_sales != '--' and isinstance(recent_sales, (int, float)):
                try:
                    # 销量下滑和提价机会场景显示整数（总销量），其他场景显示小数（日均）
                    if quick_scene in ['sales_drop', 'price_opportunity']:
                        recent_sales_val = int(recent_sales)
                        prev_sales_val = int(prev_sales)
                        recent_sales = f"{recent_sales_val}"
                        prev_sales = f"{prev_sales_val}"
                        # 销量变化使用绝对值：近7天 - 前7天（负数表示下滑）
                        if sales_change != '--' and isinstance(sales_change, (int, float)):
                            sales_diff = recent_sales_val - prev_sales_val
                            sales_change = f"{sales_diff:+d}"
                    else:
                        recent_sales = f"{float(recent_sales):.1f}"
                        prev_sales = f"{float(prev_sales):.1f}"
                        if sales_change != '--' and isinstance(sales_change, (int, float)):
                            sales_change = f"{float(sales_change):+.1f}%"
                except (ValueError, TypeError):
                    recent_sales = '--'
                    prev_sales = '--'
                    sales_change = '--'
            
            table_data.append({
                '店内码': code[:10] or '--',
                '商品名称': str(row.get('商品名称', ''))[:20] or '--',
                '分类': category_name[:8] or '--',
                '实售价': round(current_price, 2),
                '原价': round(original_price, 2),
                '成本': round(cost, 2),
                '利润率': f"{profit_rate:.1f}%",
                '总销量': int(round(total_sales)),  # 30天总销量，更直观
                # 对比字段（字段名稍后根据日期范围动态调整）
                '近期利润率': recent_profit_rate,
                '对比期利润率': prev_profit_rate,
                '利润率变化': profit_change,
                '近期销量': recent_sales,
                '对比期销量': prev_sales,
                '销量变化': sales_change,
                '滞销天数': stagnant_days,  # 滞销清仓场景显示
                '弹性系数': round(elasticity, 2),  # 显示弹性系数
                '保本价': round(floor_price, 2),
                '调整价格': round(new_price, 2),
                '调整后利润率': f"{new_profit_rate:.1f}%",
                '调整说明': adjust_text,
                '预估销量': est_qty,
                '预估利润': est_profit,
                '_cost': cost,
                '_elasticity': elasticity,  # 存储弹性系数用于调试
                '_daily_sales': daily_sales,  # 保留日均销量用于计算
            })
        
        # 统计信息
        total = len(table_data)
        price_up = sum(1 for t in table_data if t['调整价格'] > t['实售价'] + 0.01)
        price_down = sum(1 for t in table_data if t['调整价格'] < t['实售价'] - 0.01)
        hit_limit = sum(1 for t in table_data if '⚠️' in t.get('调整说明', '') or '达' in t.get('调整说明', ''))
        
        # 场景标识和策略提示
        scene_badge = ""
        scene_tip = ""
        if scene_name:
            scene_color = {
                "📉 利润率下滑": "danger",
                "💰 利润额下滑": "warning",
                "🔻 销量下滑": "danger", 
                "🐌 滞销清仓": "secondary",
                "💡 提价机会": "success"
            }.get(scene_name, "secondary")
            scene_badge = dbc.Badge(f"{scene_name}场景", color=scene_color, className="me-2")
        
        stats_content = html.Div([
            scene_badge,
            scene_tip,
            dbc.Badge(f"共 {total} 个商品", color="primary", className="me-2"),
            dbc.Badge(f"↑ 涨价 {price_up}", color="success", className="me-2") if price_up > 0 else "",
            dbc.Badge(f"↓ 降价 {price_down}", color="info", className="me-2") if price_down > 0 else "",
            dbc.Badge(f"⚠️ 达边界 {hit_limit}", color="warning", className="me-2") if hit_limit > 0 else "",
        ])
        
        # 创建表格 - 根据场景动态显示不同的列
        show_stagnant_col = quick_scene == "stagnant"
        show_profit_compare = quick_scene in ["profit_drop", "profit_amount_drop"]
        show_sales_compare = quick_scene in ["sales_drop", "price_opportunity"]
        
        # 生成列标题（包含日期范围）
        if recent_start and compare_start:
            recent_label = f"近{selected_days}天({recent_start.strftime('%m-%d')}~{max_date.strftime('%m-%d')})"
            compare_label = f"前{selected_days}天({compare_start.strftime('%m-%d')}~{compare_end.strftime('%m-%d')})"
        else:
            recent_label = "近期"
            compare_label = "对比期"
        
        columns = [
            {'name': '店内码', 'id': '店内码', 'editable': False},
            {'name': '商品名称', 'id': '商品名称', 'editable': False},
            {'name': '分类', 'id': '分类', 'editable': False},
            {'name': '实售价', 'id': '实售价', 'type': 'numeric', 'editable': False},
            {'name': '原价', 'id': '原价', 'type': 'numeric', 'editable': False},
            {'name': '成本', 'id': '成本', 'type': 'numeric', 'editable': False},
            {'name': '利润率', 'id': '利润率', 'editable': False},
            {'name': '总销量', 'id': '总销量', 'type': 'numeric', 'editable': False},
        ]
        
        # 添加对比列（仅在对应场景显示，并显示具体日期）
        if show_profit_compare:
            columns.extend([
                {'name': f'{recent_label}利润率', 'id': '近期利润率', 'editable': False},
                {'name': f'{compare_label}利润率', 'id': '对比期利润率', 'editable': False},
                {'name': '变化', 'id': '利润率变化', 'editable': False},
            ])
        
        if show_sales_compare:
            # 销量下滑和提价机会场景显示总销量
            sales_unit = '总销量' if quick_scene in ['sales_drop', 'price_opportunity'] else '日均'
            columns.extend([
                {'name': f'{recent_label}{sales_unit}', 'id': '近期销量', 'editable': False},
                {'name': f'{compare_label}{sales_unit}', 'id': '对比期销量', 'editable': False},
                {'name': '变化', 'id': '销量变化', 'editable': False},
            ])
        
        if show_stagnant_col:
            columns.append({'name': '滞销天数', 'id': '滞销天数', 'editable': False})
        
        columns.extend([
            {'name': '弹性系数', 'id': '弹性系数', 'type': 'numeric', 'editable': False},
            {'name': '保本价', 'id': '保本价', 'type': 'numeric', 'editable': False},
            {'name': '调整价格', 'id': '调整价格', 'type': 'numeric', 'editable': True},
            {'name': '调整后利润率', 'id': '调整后利润率', 'editable': False},
            {'name': '调整说明', 'id': '调整说明', 'editable': False},
            {'name': '预估销量', 'id': '预估销量', 'editable': False},
            {'name': '预估利润', 'id': '预估利润', 'editable': False},
        ])
        
        data_table = dash_table.DataTable(
            id='free-pricing-data-table',
            columns=columns,
            data=table_data[:500],  # 🚀 优化：限制500行
            editable=True,
            row_selectable='multi',
            selected_rows=[],
            page_size=20,
            page_action='native',
            sort_action='native',  # 🚀 客户端排序
            style_table={'overflowX': 'auto', 'maxHeight': '450px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'center', 'padding': '5px', 'fontSize': '12px', 'minWidth': '80px', 'width': '120px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                # 近期数据列 - 浅蓝色背景高亮
                {'if': {'column_id': '近期利润率'}, 'backgroundColor': '#e3f2fd', 'fontWeight': '500'},
                {'if': {'column_id': '近期销量'}, 'backgroundColor': '#e3f2fd', 'fontWeight': '500'},
                # 对比期数据列 - 浅灰色背景
                {'if': {'column_id': '对比期利润率'}, 'backgroundColor': '#f5f5f5'},
                {'if': {'column_id': '对比期销量'}, 'backgroundColor': '#f5f5f5'},
                # 变化列 - 根据正负显示颜色
                {'if': {'column_id': '利润率变化', 'filter_query': '{利润率变化} contains "-"'}, 'color': '#d32f2f', 'fontWeight': 'bold'},
                {'if': {'column_id': '利润率变化', 'filter_query': '{利润率变化} contains "+"'}, 'color': '#388e3c', 'fontWeight': 'bold'},
                {'if': {'column_id': '销量变化', 'filter_query': '{销量变化} contains "-"'}, 'color': '#d32f2f', 'fontWeight': 'bold'},
                {'if': {'column_id': '销量变化', 'filter_query': '{销量变化} contains "+"'}, 'color': '#388e3c', 'fontWeight': 'bold'},
                # 调整价格列 - 绿色高亮
                {'if': {'column_id': '调整价格'}, 'backgroundColor': '#e8f5e9', 'fontWeight': 'bold'},
                # 调整说明 - 根据符号显示颜色
                {'if': {'filter_query': '{调整说明} contains "↑"', 'column_id': '调整说明'}, 'color': '#28a745'},
                {'if': {'filter_query': '{调整说明} contains "↓"', 'column_id': '调整说明'}, 'color': '#007bff'},
                # 达边界的警告样式 - 更醒目
                {'if': {'filter_query': '{调整说明} contains "🚫"', 'column_id': '调整说明'}, 'color': '#dc3545', 'fontWeight': 'bold', 'backgroundColor': '#ffebee'},
                {'if': {'filter_query': '{调整说明} contains "⚠️"', 'column_id': '调整说明'}, 'color': '#e65100', 'fontWeight': 'bold', 'backgroundColor': '#fff3e0'},
                # 滞销天数 - 橙色高亮
                {'if': {'filter_query': '{滞销天数} ne "--"', 'column_id': '滞销天数'}, 'color': '#e65100', 'fontWeight': 'bold'},
            ],
            # 支持列宽拖动调整
            style_cell_conditional=[{'if': {'column_id': c['id']}, 'width': '100px'} for c in columns],
            css=[{'selector': '.dash-spreadsheet-container', 'rule': 'overflow-x: auto;'}]
        )
        
        # 生成计算完成提示
        calc_alert = None
        if is_calc and adjust_value is not None:
            # 格式化调整说明
            if adjust_type == 'percent':
                if adjust_value > 0:
                    adjust_desc = f"提价{adjust_value}%"
                elif adjust_value < 0:
                    adjust_desc = f"降价{abs(adjust_value)}%"
                else:
                    adjust_desc = "不调整"
            elif adjust_type == 'fixed':
                if adjust_value > 0:
                    adjust_desc = f"提价{adjust_value}元"
                elif adjust_value < 0:
                    adjust_desc = f"降价{abs(adjust_value)}元"
                else:
                    adjust_desc = "不调整"
            else:  # target_margin
                adjust_desc = f"设置目标利润率{adjust_value}%"
            
            calc_alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                html.Strong("✅ 计算完成！"),
                f" 使用 {adjust_desc}(", 
                {'percent': '百分比', 'fixed': '固定金额', 'target_margin': '目标利润率'}.get(adjust_type, '百分比'),
                f"), 共调整{len(table_data)}个商品"
            ], color="success", dismissable=True, className="py-2 mb-0")
        
        return data_table, table_data, stats_content, calc_alert
        
    except Exception as e:
        print(f"[自由调价] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"加载失败: {str(e)}", className="text-danger text-center py-4"), [], "", None


# ==================== Tab 3: 目标导向调价回调 ====================

@callback(
    Output("goal-pricing-target-unit", "children"),
    Input("goal-pricing-target-type", "value"),
    prevent_initial_call=True
)
def update_goal_unit(target_type):
    """更新目标值单位"""
    if target_type == 'margin_target':
        return "%"
    return "元"


@callback(
    Output("goal-pricing-exclude-category", "options"),
    Input("pricing-tabs", "active_tab"),
    State("db-store-filter", "value"),
    prevent_initial_call=True
)
def update_goal_category_options(active_tab, store):
    """更新目标导向的排除分类选项"""
    if active_tab != 'tab-goal':
        raise PreventUpdate
    
    GLOBAL_DATA = get_real_global_data()
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return []
    
    # 内存优化：使用视图筛选门店
    if store:
        store_list = store if isinstance(store, list) else [store]
        df = apply_filters_view(GLOBAL_DATA, selected_stores=store_list)
    else:
        df = GLOBAL_DATA
    
    cat_col = '一级分类名' if '一级分类名' in df.columns else ('一级分类' if '一级分类' in df.columns else None)
    if cat_col:
        categories = df[cat_col].dropna().unique().tolist()
        categories = [c for c in categories if c != '耗材']
        return [{'label': c, 'value': c} for c in sorted(categories)]
    
    return []


@callback(
    [Output("goal-pricing-current-status", "children"),
     Output("goal-pricing-result-container", "children"),
     Output("goal-pricing-data-store", "data")],
    Input("goal-pricing-calc-btn", "n_clicks"),
    [State("goal-pricing-target-type", "value"),
     State("goal-pricing-target-value", "value"),
     State("goal-pricing-max-up", "value"),
     State("goal-pricing-max-down", "value"),
     State("goal-pricing-exclude-category", "value"),
     State("goal-pricing-exclude-role", "value"),
     State("goal-pricing-priority", "value"),
     State("db-store-filter", "value"),
     State("pricing-channel-filter", "value")],
    prevent_initial_call=True
)
def calculate_goal_pricing(n_clicks, target_type, target_value, max_up, max_down,
                           exclude_categories, exclude_roles, priority, store, channel):
    """
    目标导向调价计算 - 使用scipy.optimize实现精确优化
    
    优化模型：
    - 目标函数：最大化总利润（或最小化与目标的差距）
    - 决策变量：每个商品的价格变化率 r_i ∈ [-max_down, max_up]
    - 约束条件：
      1. 价格边界：floor_price ≤ new_price ≤ ceiling_price
      2. 利润目标：sum(new_profit_i) ≥ target_profit
    - 利润计算：profit_i = (price_i * (1+r_i) - cost_i) * qty_i * (1 + r_i * elasticity_i)
    """
    from dash import dash_table
    from .pricing_engine import get_product_elasticity
    from scipy.optimize import minimize, differential_evolution
    import numpy as np
    
    print(f"[目标导向] ★★★ 回调被触发！n_clicks={n_clicks}, target_value={target_value}")
    
    if not n_clicks:
        print("[目标导向] n_clicks为空，跳过")
        raise PreventUpdate
    
    if not target_value:
        print("[目标导向] target_value为空，跳过")
        raise PreventUpdate
    
    GLOBAL_DATA = get_real_global_data()
    print(f"[目标导向] GLOBAL_DATA: {len(GLOBAL_DATA) if GLOBAL_DATA is not None else 'None'} 行")
    
    if GLOBAL_DATA is None or GLOBAL_DATA.empty:
        return html.Div("请先加载数据", className="text-warning text-center py-4"), html.Div(), []
    
    try:
        target_value = float(target_value)
        max_up_pct = float(max_up or 20) / 100
        max_down_pct = float(max_down or 15) / 100
        
        print(f"[目标导向] 开始优化: 目标类型={target_type}, 目标值={target_value}, 涨幅上限={max_up_pct*100}%, 降幅上限={max_down_pct*100}%")
        print(f"[目标导向] 门店={store}, 渠道={channel}, 排除分类={exclude_categories}, 排除角色={exclude_roles}")
        
        # 准备数据
        products_df = prepare_pricing_data_v2(GLOBAL_DATA, channel)
        print(f"[目标导向] prepare_pricing_data_v2返回: {len(products_df) if products_df is not None else 'None'} 行")
        
        if products_df is None or products_df.empty:
            return html.Div("无可调价商品（prepare_pricing_data_v2返回空）", className="text-warning text-center py-4"), html.Div(), []
        
        print(f"[目标导向] 数据列: {list(products_df.columns)}")
        
        # 门店筛选
        store_col = next((c for c in ['门店名称', '门店', 'store'] if c in products_df.columns), None)
        if store and store_col:
            if isinstance(store, list):
                products_df = products_df[products_df[store_col].isin(store)]
            else:
                products_df = products_df[products_df[store_col] == store]
            print(f"[目标导向] 门店筛选后: {len(products_df)} 行")
        
        # 排除分类
        if exclude_categories:
            cat_col = '一级分类名' if '一级分类名' in products_df.columns else ('一级分类' if '一级分类' in products_df.columns else None)
            if cat_col:
                products_df = products_df[~products_df[cat_col].isin(exclude_categories)]
                print(f"[目标导向] 排除分类后: {len(products_df)} 行")
        
        # 排除角色
        if exclude_roles and '商品角色' in products_df.columns:
            products_df = products_df[~products_df['商品角色'].isin(exclude_roles)]
            print(f"[目标导向] 排除角色后: {len(products_df)} 行")
        
        # 只保留允许调价的商品
        if '允许调价' in products_df.columns:
            products_df = products_df[products_df['允许调价'] == True]
            print(f"[目标导向] 允许调价筛选后: {len(products_df)} 行")
        else:
            print(f"[目标导向] 警告：数据中没有'允许调价'列")
        
        if products_df.empty:
            return html.Div("筛选后无可调价商品", className="text-warning text-center py-4"), html.Div(), []
        
        # 构建优化数据
        channel_name = channel if channel and channel != 'all' else '美团'
        
        products_list = []
        total_current_profit = 0
        
        for _, row in products_df.iterrows():
            code = str(row.get('店内码', '') or '')
            category_name = str(row.get('一级分类名', '') or row.get('一级分类', '') or '')
            elasticity, _ = get_product_elasticity(code, channel_name, category_name, None)
            
            try:
                current_price = float(row.get('实收价格', 0) or 0)
                cost = float(row.get('单品成本', 0) or 0)
                original_price = float(row.get('商品原价', 0) or 0)
                if original_price <= 0:
                    original_price = current_price
                daily_sales = float(row.get('日均销量', 0) or 0)
                profit_rate = float(row.get('利润率', 0) or 0)
            except:
                continue
            
            if current_price <= 0 or daily_sales <= 0:
                continue
            
            current_profit = (current_price - cost) * daily_sales
            total_current_profit += current_profit
            
            # 价格边界
            floor_price = cost if cost > 0 else 0.01
            ceiling_price = max(original_price, current_price)  # 确保上限至少是当前价格
            
            # 变化率边界（考虑绝对边界）
            # 涨价上限：不超过原价，也不超过用户设置的最大涨幅
            if current_price > 0 and ceiling_price > current_price:
                max_rate_up = min(max_up_pct, (ceiling_price - current_price) / current_price)
            elif current_price > 0 and ceiling_price <= current_price:
                max_rate_up = 0  # 已经在原价或高于原价，不能涨价
            else:
                max_rate_up = max_up_pct  # 异常情况，使用用户设置的上限
            
            # 降价下限：不低于保本价，也不超过用户设置的最大降幅
            if current_price > 0 and current_price > floor_price:
                max_rate_down = min(max_down_pct, (current_price - floor_price) / current_price)
            else:
                max_rate_down = 0  # 如果当前价格已经低于保本价，不能再降
            
            # 确保边界有效（下界 <= 上界）- 双重保险
            max_rate_up = max(0, max_rate_up)  # 涨幅不能为负
            max_rate_down = max(0, max_rate_down)  # 降幅不能为负
            
            # 跳过无法调价的商品（涨降幅都为0的）
            if max_rate_up < 0.001 and max_rate_down < 0.001:
                continue  # 无调价空间，跳过
            
            products_list.append({
                '店内码': code,
                '商品名称': str(row.get('商品名称', ''))[:20],
                '分类': category_name,
                '角色': row.get('商品角色', ''),
                'price': current_price,
                'cost': cost,
                'original_price': original_price,
                'qty': daily_sales,
                'elasticity': elasticity,
                'current_profit': current_profit,
                'profit_rate': profit_rate,
                'max_rate_up': max_rate_up,
                'max_rate_down': max_rate_down,
            })
        
        if not products_list:
            return html.Div("无有效商品"), html.Div(), []
        
        n_products = len(products_list)
        print(f"[目标导向] 可调商品数量: {n_products}")
        
        # 计算目标利润
        if target_type == 'profit_increase':
            target_total_profit = total_current_profit + target_value
        elif target_type == 'profit_target':
            target_total_profit = target_value
        else:  # margin_target
            target_total_profit = total_current_profit * (1 + target_value / 100)
        
        profit_gap = target_total_profit - total_current_profit
        
        print(f"[目标导向] 当前利润: {total_current_profit:.0f}, 目标利润: {target_total_profit:.0f}, 缺口: {profit_gap:.0f}")
        
        # 当前状态展示
        current_status = dbc.Alert([
            dbc.Row([
                dbc.Col([
                    html.Div("当前日利润", className="text-muted small"),
                    html.H4(f"¥{total_current_profit:.0f}", className="mb-0")
                ], width=3, className="text-center"),
                dbc.Col([
                    html.Div("目标日利润", className="text-muted small"),
                    html.H4(f"¥{target_total_profit:.0f}", className="mb-0 text-primary")
                ], width=3, className="text-center"),
                dbc.Col([
                    html.Div("需要提升", className="text-muted small"),
                    html.H4([
                        f"¥{profit_gap:.0f}",
                        html.Small(f" ({profit_gap/total_current_profit*100:+.1f}%)" if total_current_profit > 0 else "", className="text-muted")
                    ], className=f"mb-0 text-{'success' if profit_gap > 0 else 'danger'}")
                ], width=3, className="text-center"),
                dbc.Col([
                    html.Div("可调商品", className="text-muted small"),
                    html.H4(f"{n_products}个", className="mb-0")
                ], width=3, className="text-center"),
            ])
        ], color="info" if profit_gap > 0 else "warning", className="mb-3")
        
        # ==================== 精确优化算法 ====================
        
        # 提取数组（加速计算）
        prices = np.array([p['price'] for p in products_list])
        costs = np.array([p['cost'] for p in products_list])
        quantities = np.array([p['qty'] for p in products_list])
        elasticities = np.array([p['elasticity'] for p in products_list])
        max_rates_up = np.array([p['max_rate_up'] for p in products_list])
        max_rates_down = np.array([p['max_rate_down'] for p in products_list])
        
        def calculate_total_profit(rate_changes):
            """计算给定价格变化率下的总利润"""
            new_prices = prices * (1 + rate_changes)
            # 销量变化：价格变化率 * 弹性系数（弹性为负数，涨价会降销量）
            qty_changes = rate_changes * elasticities
            new_quantities = quantities * (1 + qty_changes)
            # 确保销量不为负
            new_quantities = np.maximum(new_quantities, 0)
            # 利润 = (价格 - 成本) * 销量
            profits = (new_prices - costs) * new_quantities
            return np.sum(profits)
        
        def objective(rate_changes):
            """
            目标函数：最小化（目标利润 - 实际利润）的平方 + 变化惩罚项
            
            惩罚项的作用：在多个可行解中选择变化最小的
            """
            total_profit = calculate_total_profit(rate_changes)
            profit_shortfall = max(0, target_total_profit - total_profit)
            
            # 变化惩罚：鼓励尽量少的商品调价，且调价幅度尽量小
            change_penalty = np.sum(rate_changes ** 2) * 0.1
            
            return profit_shortfall ** 2 + change_penalty
        
        # 变量边界 - 验证并构建
        bounds = []
        for i, p in enumerate(products_list):
            lb = -p['max_rate_down']
            ub = p['max_rate_up']
            # 确保lb <= ub (在极端情况下修正)
            if lb > ub:
                print(f"[目标导向] 警告: 商品{i}({p['商品名称']})边界异常 lb={lb:.4f} > ub={ub:.4f}, 修正为[0,0]")
                lb, ub = 0, 0
            bounds.append((lb, ub))
        
        print(f"[目标导向] 边界范围: 下界[{min(b[0] for b in bounds):.4f}, {max(b[0] for b in bounds):.4f}], 上界[{min(b[1] for b in bounds):.4f}, {max(b[1] for b in bounds):.4f}]")
        
        # 初始猜测：根据优先级策略
        x0 = np.zeros(n_products)
        
        if profit_gap > 0:
            # 需要增加利润，优先涨价利润贡献大/弹性低的商品
            if priority == 'profit_contribution':
                priority_scores = np.array([p['current_profit'] for p in products_list])
            elif priority == 'sales_volume':
                priority_scores = quantities.copy()
            elif priority == 'low_elasticity':
                priority_scores = -np.abs(elasticities)  # 弹性绝对值越小越优先
            elif priority == 'low_margin':
                priority_scores = -np.array([p['profit_rate'] for p in products_list])
            else:
                priority_scores = np.ones(n_products)
            
            # 归一化优先级
            if priority_scores.max() > priority_scores.min():
                priority_scores = (priority_scores - priority_scores.min()) / (priority_scores.max() - priority_scores.min())
            else:
                priority_scores = np.ones(n_products) / n_products
            
            # 初始猜测：按优先级分配涨幅
            x0 = priority_scores * max_rates_up * 0.5  # 初始设为最大涨幅的50%
        
        print(f"[目标导向] 开始SLSQP优化...")
        
        # 使用SLSQP优化
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            options={'maxiter': 500, 'ftol': 1e-6, 'disp': False}
        )
        
        optimal_rates = result.x
        final_profit = calculate_total_profit(optimal_rates)
        
        print(f"[目标导向] SLSQP完成: success={result.success}, 最终利润={final_profit:.0f}")
        
        # 如果SLSQP效果不好，尝试差分进化（全局优化）
        if final_profit < target_total_profit * 0.9 and n_products <= 100:
            print(f"[目标导向] SLSQP未达目标，尝试差分进化...")
            
            def neg_profit(rate_changes):
                """负利润（用于最大化）"""
                return -calculate_total_profit(rate_changes)
            
            try:
                de_result = differential_evolution(
                    neg_profit,
                    bounds,
                    maxiter=100,
                    seed=42,
                    workers=1,
                    updating='deferred'
                )
                
                de_profit = calculate_total_profit(de_result.x)
                print(f"[目标导向] 差分进化完成: 利润={de_profit:.0f}")
                
                if de_profit > final_profit:
                    optimal_rates = de_result.x
                    final_profit = de_profit
                    print(f"[目标导向] 采用差分进化结果")
            except Exception as e:
                print(f"[目标导向] 差分进化失败: {e}")
        
        # ==================== 构建结果 ====================
        
        adjusted_count = 0
        total_new_profit = 0
        result_data = []
        
        for i, p in enumerate(products_list):
            rate = optimal_rates[i]
            current_price = p['price']
            cost = p['cost']
            qty = p['qty']
            elasticity = p['elasticity']
            
            # 计算新价格和新利润
            new_price = current_price * (1 + rate)
            new_qty = qty * (1 + rate * elasticity)
            new_qty = max(new_qty, 0)
            new_profit = (new_price - cost) * new_qty
            old_profit = p['current_profit']
            profit_change = new_profit - old_profit
            
            total_new_profit += new_profit
            
            if abs(rate) > 0.005:  # 变化超过0.5%才算调整
                adjusted_count += 1
            
            change_pct = rate * 100
            
            result_data.append({
                '店内码': p['店内码'],
                '商品名称': p['商品名称'],
                '分类': p['分类'],
                '角色': p['角色'],
                '实售价': round(current_price, 2),
                '成本': round(cost, 2),
                '日均销量': round(qty, 1),
                '弹性': round(elasticity, 2),
                '调整价格': round(new_price, 2),
                '涨降幅': f"{change_pct:+.1f}%" if abs(change_pct) > 0.5 else "--",
                '预估利润变化': f"¥{profit_change:+.0f}" if abs(profit_change) > 0.5 else "--",
                '_rate': rate,
                '_profit_change': profit_change,
            })
        
        # 按利润变化排序（变化大的在前）
        result_data.sort(key=lambda x: abs(x['_profit_change']), reverse=True)
        
        # 结果汇总
        achieved_gap = total_new_profit - total_current_profit
        achievement_rate = (achieved_gap / profit_gap * 100) if profit_gap > 0 else 100
        
        print(f"[目标导向] 最终结果: 调整商品={adjusted_count}, 新利润={total_new_profit:.0f}, 达成率={achievement_rate:.1f}%")
        
        # 优化效果说明
        if achievement_rate >= 100:
            effect_text = "✅ 完全达成目标"
            effect_color = "success"
        elif achievement_rate >= 80:
            effect_text = "🔶 基本达成目标"
            effect_color = "success"
        elif achievement_rate >= 50:
            effect_text = "⚠️ 部分达成目标"
            effect_color = "warning"
        else:
            effect_text = "❌ 目标可能过高"
            effect_color = "danger"
        
        # 结果表格
        result_table = dash_table.DataTable(
            id='goal-pricing-result-table',
            columns=[
                {'name': '店内码', 'id': '店内码'},
                {'name': '商品名称', 'id': '商品名称'},
                {'name': '分类', 'id': '分类'},
                {'name': '角色', 'id': '角色'},
                {'name': '实售价', 'id': '实售价', 'type': 'numeric'},
                {'name': '弹性', 'id': '弹性', 'type': 'numeric'},
                {'name': '调整价格', 'id': '调整价格', 'type': 'numeric'},
                {'name': '涨降幅', 'id': '涨降幅'},
                {'name': '预估利润变化', 'id': '预估利润变化'},
            ],
            data=[{k: v for k, v in d.items() if not k.startswith('_')} for d in result_data],
            page_size=15,
            style_table={'overflowX': 'auto', 'maxHeight': '400px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'center', 'padding': '5px', 'fontSize': '12px'},
            style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'filter_query': '{涨降幅} contains "+"'}, 'backgroundColor': '#e8f5e9'},
                {'if': {'filter_query': '{涨降幅} contains "-"'}, 'backgroundColor': '#e3f2fd'},
                {'if': {'column_id': '调整价格'}, 'fontWeight': 'bold'},
            ]
        )
        
        result_content = html.Div([
            dbc.Alert([
                html.H5([
                    f"📊 优化方案结果 - {effect_text}",
                    dbc.Badge(f"达成率 {achievement_rate:.0f}%", color=effect_color, className="ms-2")
                ], className="mb-2"),
                dbc.Row([
                    dbc.Col([
                        html.Span("调整商品: ", className="text-muted"),
                        html.Strong(f"{adjusted_count}个 / {n_products}个")
                    ], width=3),
                    dbc.Col([
                        html.Span("预估新利润: ", className="text-muted"),
                        html.Strong(f"¥{total_new_profit:.0f}")
                    ], width=3),
                    dbc.Col([
                        html.Span("利润提升: ", className="text-muted"),
                        html.Strong(f"¥{achieved_gap:.0f}", className=f"text-{effect_color}")
                    ], width=3),
                    dbc.Col([
                        html.Span("vs目标: ", className="text-muted"),
                        html.Strong(
                            f"{'达成' if achieved_gap >= profit_gap else '差' + str(int(profit_gap - achieved_gap)) + '元'}", 
                            className=f"text-{effect_color}"
                        )
                    ], width=3),
                ]),
                html.Hr(className="my-2"),
                html.Small([
                    html.I(className="fas fa-info-circle me-1"),
                    f"使用scipy.optimize求解，算法: SLSQP + 差分进化。弹性系数影响销量预估。"
                ], className="text-muted")
            ], color=effect_color),
            result_table
        ])
        
        return current_status, result_content, result_data
        
    except Exception as e:
        print(f"[目标导向] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"计算失败: {str(e)}", className="text-danger"), html.Div(), []


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
     Output("pricing-batch-status", "children", allow_duplicate=True),
     Output("pricing-floor-alert-container", "children", allow_duplicate=True)],
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


# ==================== 📊 商品分组辅助函数 ====================

def get_product_group_columns(df: pd.DataFrame, include_category: bool = False) -> list:
    """
    获取商品分组字段（统一逻辑：优先使用店内码）
    
    Args:
        df: 数据DataFrame
        include_category: 是否包含一级分类字段
    
    Returns:
        分组字段列表，例如：['店内码', '商品名称'] 或 ['商品名称']
    
    说明：
        店内码能唯一标识商品规格，避免同名不同规格商品被混淆
        例如："可乐 330ml" (店内码: A001) vs "可乐 500ml" (店内码: A002)
    """
    group_cols = []
    
    # 优先使用店内码
    if '店内码' in df.columns:
        valid_ratio = df['店内码'].notna().sum() / len(df) if len(df) > 0 else 0
        if valid_ratio > 0.5:  # 有效率>50%
            group_cols.append('店内码')
    
    # 始终包含商品名称（用于展示）
    if '商品名称' in df.columns:
        group_cols.append('商品名称')
    
    # 可选：包含一级分类
    if include_category:
        for col in ['一级分类名', '一级分类', '分类']:
            if col in df.columns:
                group_cols.append(col)
                break
    
    return group_cols if group_cols else ['商品名称']  # 降级保护


# ==================== 📊 商品综合分析模块 (V7.0 - 六象限分类体系) ====================
# 核心改进：
# 1. 去掉2.99折判定，增加极端引流品判断（亏损引流、低价引流、赠品）
# 2. 明星商品增加单品价值门槛（防止低价品虚高）
# 3. 新增畅销商品象限（低价高销刚需品）
# 4. 使用动态阈值（自适应不同门店）

def calculate_enhanced_product_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    商品健康评分计算 V7.0（六象限分类体系）
    
    核心设计：
    1. 优先级1：极端策略引流品识别（最高优先级）
       - 秒杀/满赠：实售价 ≤ 0.01元 + 销量≥中位数（动态）
       - 亏损引流：利润率 < -50% + 销量≥中位数（动态）
       - 低价引流：实售价≤2元 且 不到成本一半 + 销量≥中位数（动态）
       - 赠品：实售价=0 但有销量
       → 直接归类为 🎯 策略引流
    
    2. 优先级2：明星商品（高利润+高动销+高单品价值）
       - 利润率 > 品类中位数
       - 动销指数 > 全局中位数
       - 单品利润额≥0.5元 OR 总利润贡献≥50元（动态阈值）
       → 🌟 明星商品（防止低价品因利润率高被误判）
    
    3. 优先级3：畅销商品（低价+高销+正利润）
       - 实售价 < 全局价格中位数
       - 销量 ≥ 70分位数
       - 利润率 ≥ 品类中位数
       → 🔥 畅销商品（刚需基础品，如包子、矿泉水）
    
    4. 优先级4：潜力商品（高利润+低动销）
       → 💎 潜力商品（待推广的利润品）
    
    5. 优先级5：自然引流（低利润+高动销+销量门槛）
       - 利润率 ≤ 品类中位数
       - 动销指数 > 全局中位数
       - 销量≥20 + 订单≥5
       → ⚡ 自然引流（市场验证的引流品）
    
    6. 优先级6：低效商品（其他所有情况）
       → 🐌 低效商品（待优化或淘汰）
    
    业务意义（V7.0核心优化）：
    - 避免低价高利润率商品被误判为明星（增加绝对价值门槛）
    - 区分畅销刚需品和策略引流品（前者有正常利润）
    - 使用动态阈值，自适应不同门店的商品结构
    - 六象限体系更精准，决策价值更高
    
    Returns:
        包含象限分类、利润率、动销指数等的商品DataFrame
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    df_copy = df.copy()
    
    # ===== V6.2：剔除异常数据 =====
    # 1. 剔除非销售商品（仅剔除"耗材"分类）
    category_col = '一级分类名' if '一级分类名' in df_copy.columns else None
    if category_col:
        exclude_categories = ['耗材']
        original_count = len(df_copy)
        df_copy = df_copy[~df_copy[category_col].isin(exclude_categories)]
        excluded_count = original_count - len(df_copy)
        if excluded_count > 0:
            print(f"📦 商品健康分析V6.2：已剔除 {excluded_count} 条耗材数据")
    
    # 2. 剔除销量≤0的退款和异常数据
    sales_col_check = '月售' if '月售' in df_copy.columns else '销量'
    if sales_col_check in df_copy.columns:
        original_count = len(df_copy)
        df_copy = df_copy[df_copy[sales_col_check].fillna(0) > 0]
        excluded_count = original_count - len(df_copy)
        if excluded_count > 0:
            print(f"🧹 已剔除 {excluded_count} 条销量≤0的退款/异常数据")
    
    if df_copy.empty:
        return pd.DataFrame()
    
    # ===== 字段映射 =====
    sales_col = '月售' if '月售' in df_copy.columns else '销量'
    cost_col = '商品采购成本' if '商品采购成本' in df_copy.columns else '成本'
    
    # 计算销售额（实收价格 × 销量）
    # 注意：实收价格是单价，需要×销量；利润额是原始字段，已经是总毛利
    if '实收价格' in df_copy.columns and sales_col in df_copy.columns:
        df_copy['商品销售额'] = df_copy['实收价格'].fillna(0) * df_copy[sales_col].fillna(1)
    else:
        df_copy['商品销售额'] = df_copy.get('商品实售价', 0)
    
    # ===== 聚合到商品级别（V6.1：商品维度只关注毛利，不扣营销成本） =====
    # 说明：
    # - 原始数据中的"利润额"字段 = (实收价格 × 销量) - 成本（总毛利）
    # - 商品健康分析关注商品本身盈利能力，不扣除营销成本
    # - 营销成本应在订单维度分析时考虑
    agg_dict = {
        '商品销售额': 'sum',  # 实收价格×销量的总和
        '利润额': 'sum',      # 毛利润（只扣商品成本）
        sales_col: 'sum',
        '订单ID': 'nunique'
    }
    
    if cost_col in df_copy.columns:
        agg_dict[cost_col] = 'sum'
    if '库存' in df_copy.columns or '剩余库存' in df_copy.columns:
        stock_field = '库存' if '库存' in df_copy.columns else '剩余库存'
        agg_dict[stock_field] = 'last'
    # 店内码处理：如果用于分组则不需要在agg_dict中，否则保留第一个值
    # （店内码字段将在后面根据是否用于分组来决定是否添加到agg_dict）
    
    # 新增：三级分类
    category3_col = '三级分类名' if '三级分类名' in df_copy.columns else ('三级分类' if '三级分类' in df_copy.columns else None)
    if category3_col:
        agg_dict[category3_col] = 'first'
    
    # 价格字段（用于计算单品利润率）
    # 商品原价：单价，用max；实收价格和商品实售价：聚合后用加权平均（销售额÷销量）计算
    if '商品原价' in df_copy.columns:
        agg_dict['商品原价'] = 'max'   # 单价，取最大
    # 商品实售价和实收价格改为加权平均，不在这里聚合
    
    # ===== 分组字段（关键修复：优先使用店内码+渠道）=====
    # 店内码能唯一标识商品规格，避免同名不同规格商品被混淆
    # 例如："可乐 330ml" vs "可乐 500ml" - 同名但店内码不同
    # V6.1修复：增加渠道维度，避免同一商品在不同渠道的价格混淆
    # 例如：店内码52183在美团原价12.8元，饿了么原价9.8元
    group_cols = ['商品名称']
    use_store_code = False  # 标记是否使用店内码分组
    use_channel = False  # 标记是否使用渠道分组
    
    # 优先使用店内码分组（如果存在且有效）
    if '店内码' in df_copy.columns:
        # 检查店内码是否有效（非空值占比>50%）
        valid_store_code_ratio = df_copy['店内码'].notna().sum() / len(df_copy)
        if valid_store_code_ratio > 0.5:
            group_cols = ['店内码', '商品名称']  # 优先用店内码，保留商品名称便于展示
            use_store_code = True
            print(f"✅ 使用店内码分组（有效率{valid_store_code_ratio:.1%}），避免同名不同规格商品混淆")
        else:
            print(f"⚠️ 店内码数据不足（有效率{valid_store_code_ratio:.1%}），降级为商品名称分组")
            # 店内码不用于分组时，保留第一个值作为参考
            agg_dict['店内码'] = 'first'
    else:
        print("ℹ️ 无店内码字段，使用商品名称分组")
    
    # V6.1新增：检查是否需要按渠道分组
    if '渠道' in df_copy.columns:
        # 检查同一商品在不同渠道是否有价格差异
        unique_channels = df_copy['渠道'].nunique()
        if unique_channels > 1:
            # 抽样检查：是否存在同一商品在不同渠道价格不同的情况
            if use_store_code:
                # 使用店内码检查
                sample_check = df_copy.groupby(['店内码', '渠道'])['商品原价'].mean().reset_index()
                price_variance = sample_check.groupby('店内码')['商品原价'].std().fillna(0)
                has_price_diff = (price_variance > 0.1).any()  # 价格标准差>0.1元视为有差异
            else:
                # 使用商品名称检查
                sample_check = df_copy.groupby(['商品名称', '渠道'])['商品原价'].mean().reset_index()
                price_variance = sample_check.groupby('商品名称')['商品原价'].std().fillna(0)
                has_price_diff = (price_variance > 0.1).any()
            
            if has_price_diff:
                group_cols.append('渠道')
                use_channel = True
                print(f"✅ 检测到跨渠道价格差异，增加渠道维度分组（共{unique_channels}个渠道）")
            else:
                # 保留渠道字段用于展示
                agg_dict['渠道'] = 'first'
                print(f"ℹ️ 检测到{unique_channels}个渠道，但价格差异不明显，不分渠道聚合")
        else:
            # 只有一个渠道，保留字段用于展示
            agg_dict['渠道'] = 'first'
            print(f"ℹ️ 数据仅包含单一渠道，不需要渠道分组")
    
    # 添加一级分类到分组字段
    if category_col and category_col in df_copy.columns:
        group_cols.append(category_col)
    
    product_data = df_copy.groupby(group_cols).agg(agg_dict).reset_index()
    
    # 重命名列
    product_data = product_data.rename(columns={
        '商品销售额': '销售额',
        sales_col: '销量',
        '订单ID': '订单数'
    })
    if cost_col in product_data.columns:
        product_data = product_data.rename(columns={cost_col: '成本'})
    
    # 统一库存字段名
    if '剩余库存' in product_data.columns:
        product_data = product_data.rename(columns={'剩余库存': '库存'})
    
    # 统一三级分类字段名
    if category3_col and category3_col in product_data.columns and category3_col != '三级分类名':
        product_data = product_data.rename(columns={category3_col: '三级分类名'})
    
    # ===== 计算价格字段（加权平均）=====
    # 商品实售价 = 销售额 / 销量（加权平均，反映真实成交价）
    if '商品实售价' not in product_data.columns:
        product_data['商品实售价'] = np.where(
            product_data['销量'] > 0,
            product_data['销售额'] / product_data['销量'],
            0
        )
    
    # 实收价格 = 销售额 / 销量（加权平均）
    if '实收价格' not in product_data.columns:
        product_data['实收价格'] = np.where(
            product_data['销量'] > 0,
            product_data['销售额'] / product_data['销量'],
            0
        )
    
    # ===== 计算基础指标 =====
    # 单品成本 = 总成本 / 销量（成本是总额，需要除以销量）
    product_data['单品成本'] = np.where(
        product_data['销量'] > 0,
        product_data['成本'] / product_data['销量'],
        0
    )
    
    # V6.1：综合利润率（毛利率）= 利润额 / 销售额
    # 说明：
    # - 利润额是原始字段的毛利润（只扣商品成本）
    # - 销售额 = 实收价格 × 销量
    # - 此利润率反映商品本身的盈利能力，不包含营销成本
    product_data['综合利润率'] = np.where(
        product_data['销售额'] > 0,
        (product_data['利润额'] / product_data['销售额'] * 100),
        0
    )
    
    # V7.0新增：单品利润额和总利润贡献（用于明星商品判定）
    product_data['单品利润额'] = np.where(
        product_data['销量'] > 0,
        product_data['利润额'] / product_data['销量'],
        0
    )
    product_data['总利润贡献'] = product_data['利润额']
    
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
    
    # V6.1：删除营销ROI和营销占比计算
    # 说明：商品维度只关注毛利，营销成本应在订单维度分析
    # 保留字段用于兼容性，设为默认值
    product_data['营销ROI'] = 10  # 默认高ROI
    product_data['营销占比'] = 0   # 默认0%
    
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
    
    # ===== V7.1：动销指数（优化版 - 移除周转率）=====
    # 动销指数 = 0.6×标准化销量 + 0.4×标准化订单数
    # 说明：
    # - 移除周转率：订单数据无法准确计算库存周转率（库存快照不连续）
    # - 销量（60%）：反映商品总体销售规模
    # - 订单数（40%）：反映购买频次，防止单笔大单误判
    # - 使用Min-Max标准化
    
    min_sales = product_data['销量'].min()
    max_sales = product_data['销量'].max()
    sales_range = max_sales - min_sales if max_sales > min_sales else 1
    product_data['标准化销量'] = (product_data['销量'] - min_sales) / sales_range
    
    min_orders = product_data['订单数'].min()
    max_orders = product_data['订单数'].max()
    orders_range = max_orders - min_orders if max_orders > min_orders else 1
    product_data['标准化订单数'] = (product_data['订单数'] - min_orders) / orders_range
    
    # 综合动销指数（V7.1优化）
    product_data['动销指数'] = (
        0.6 * product_data['标准化销量'] + 
        0.4 * product_data['标准化订单数']
    )
    
    # ===== V5.2：分品类动态阈值（科学模型）=====
    # 利润率阈值：每个品类的利润率中位数（让品类内部竞争）
    # 动销指数阈值：全局中位数（相对排序）
    
    # 确定分类字段
    category_field = None
    for field in ['一级分类名', '一级分类', '分类']:
        if field in product_data.columns:
            category_field = field
            break
    
    # 计算每个品类的利润率中位数
    if category_field:
        category_profit_median = product_data.groupby(category_field)['综合利润率'].median()
        product_data['品类利润率阈值'] = product_data[category_field].map(category_profit_median)
        # 如果某品类只有1个商品，使用全局中位数作为阈值
        global_profit_median = product_data['综合利润率'].median()
        product_data['品类利润率阈值'] = product_data['品类利润率阈值'].fillna(global_profit_median)
        print(f"📊 V5.2分品类阈值模式: 全局利润率中位数={global_profit_median:.1f}%")
        print(f"   各品类阈值: {category_profit_median.to_dict()}")
    else:
        # 无分类字段时，使用全局中位数
        global_profit_median = product_data['综合利润率'].median()
        product_data['品类利润率阈值'] = global_profit_median
        print(f"📊 V5.2全局阈值模式: 利润率中位数={global_profit_median:.1f}%")
    
    # 动销指数阈值：全局中位数（相对排序）
    sales_threshold = product_data['动销指数'].median()
    print(f"   动销指数中位数={sales_threshold:.3f}")
    
    # ===== V7.0：六象限分类体系（策略引流 + 明星 + 畅销 + 潜力 + 自然引流 + 低效）=====
    
    # 极端引流品识别阈值
    EXTREME_PRICE_THRESHOLD = 0.01  # 秒杀：实售价≤0.01元
    LOSS_ATTRACTION_THRESHOLD = -50  # 亏损引流：利润率<-50%
    LOW_PRICE_THRESHOLD = 2.0  # 低价引流：实售价≤2元
    LOW_PRICE_COST_RATIO = 0.5  # 低价引流：实售价<成本×0.5
    
    # ===== V7.2：动态门槛（自适应门店规模）=====
    
    # 1. 高动销门槛（用于明星、潜力、自然引流、低效）
    # 使用70分位数作为门槛，确保约30%的商品有机会成为"高动销"
    # 优点：自适应不同门店规模，小门店不会因为绝对销量低而没有明星商品
    HIGH_SALES_MIN_QUANTITY = max(
        product_data['销量'].quantile(0.7) if len(product_data) > 0 else 10,
        5  # 保底5件，避免门槛过低
    )
    HIGH_SALES_MIN_ORDERS = max(
        product_data['订单数'].quantile(0.7) if len(product_data) > 0 else 3,
        2  # 保底2单，避免门槛过低
    )
    
    # 2. 策略引流门槛（用于识别有效的引流活动）
    # 使用50分位数（中位数），门槛相对较低，确保能识别到引流活动
    # 原因：引流活动的目的是带动流量，不需要太高的销量门槛
    STRATEGY_MIN_QUANTITY = max(
        product_data['销量'].quantile(0.5) if len(product_data) > 0 else 5,
        3  # 保底3件，避免测试活动被误判
    )
    
    print(f"📊 V7.2动态门槛:")
    print(f"   高动销门槛: 销量≥{HIGH_SALES_MIN_QUANTITY:.0f}件, 订单≥{HIGH_SALES_MIN_ORDERS:.0f}单 (70分位数)")
    print(f"   策略引流门槛: 销量≥{STRATEGY_MIN_QUANTITY:.0f}件 (50分位数，确保识别有效引流)")
    
    # V7.0新增：明星商品价值门槛（动态计算）
    # 单品利润额阈值：0.5元保底 + 全局30分位数
    STAR_MIN_UNIT_PROFIT = max(0.5, product_data['单品利润额'].quantile(0.3) if len(product_data) > 0 else 0.5)
    # 总利润贡献阈值：50元保底 + 全局30分位数
    STAR_MIN_TOTAL_PROFIT = max(50, product_data['总利润贡献'].quantile(0.3) if len(product_data) > 0 else 50)
    
    # V7.3优化：畅销商品价格阈值（低价高销刚需品）
    # 价格阈值：从中位数改为30分位数（更宽松，识别更多刚需品）
    BESTSELLER_PRICE_THRESHOLD = product_data['商品实售价'].quantile(0.3) if len(product_data) > 0 else 10
    # 销量阈值：从70分位数改为80分位数（更严格，确保是真正的畅销品）
    BESTSELLER_SALES_THRESHOLD = product_data['销量'].quantile(0.8) if len(product_data) > 0 else 20
    
    # V7.3优化：潜力商品阈值
    # 低动销上限：销量中位数（明确的上限）
    POTENTIAL_SALES_THRESHOLD = product_data['销量'].quantile(0.5) if len(product_data) > 0 else 10
    # 价值门槛：单品利润额≥0.3元
    POTENTIAL_MIN_UNIT_PROFIT = 0.3
    
    # V7.4优化：打印阈值信息（删除评分相关输出）
    print(f"📊 V7.4动态阈值设置:")
    print(f"   明星-单品利润额门槛: ≥{STAR_MIN_UNIT_PROFIT:.2f}元")
    print(f"   明星-总利润贡献门槛: ≥{STAR_MIN_TOTAL_PROFIT:.2f}元")
    print(f"   畅销-价格阈值: <{BESTSELLER_PRICE_THRESHOLD:.2f}元 (30分位数)")
    print(f"   畅销-销量阈值: ≥{BESTSELLER_SALES_THRESHOLD:.0f}件 (80分位数)")
    print(f"   潜力-销量上限: <{POTENTIAL_SALES_THRESHOLD:.0f}件 (50分位数)")
    print(f"   潜力-单品利润门槛: ≥{POTENTIAL_MIN_UNIT_PROFIT:.2f}元")
    
    def is_high_sales(sales_index, sales_qty, order_count):
        """
        V7.2 统一的高动销判定标准（动态门槛）
        
        判定条件（需同时满足）：
        1. 动销指数 > 全店中位数（相对排名前50%）
        2. 销量 ≥ 全店销量70分位数（动态，约前30%）
        3. 订单数 ≥ 全店订单数70分位数（动态，约前30%）
        
        V7.2优化说明：
        - 从固定门槛（20件+5单）改为动态门槛（70分位数）
        - 自适应不同门店规模：大门店门槛高，小门店门槛低
        - 确保约30%的商品有机会成为"高动销"
        - 保底门槛：销量≥5件，订单≥2单（避免过低）
        """
        return (sales_index > sales_threshold and 
                sales_qty >= HIGH_SALES_MIN_QUANTITY and 
                order_count >= HIGH_SALES_MIN_ORDERS)
    
    def classify_quadrant_v7(row):
        """
        V7.2 六象限分类体系（动态门槛+统一判定标准）
        
        六个象限：
        1. 🎯 策略引流 - 极端价格引流品（秒杀/亏损引流/低价引流/赠品）
        2. 🌟 明星商品 - 高利润率+高动销+高单品价值
        3. 🔥 畅销商品 - 低价+高销+正利润（刚需基础品）
        4. 💎 潜力商品 - 高利润率+低动销（待推广）
        5. ⚡ 自然引流 - 低利润率+高动销
        6. 🐌 低效商品 - 低利润率+低动销（明确定义）
        
        V7.2核心优化：
        - 动态门槛：销量/订单数门槛使用70分位数（自适应门店规模）
        - 统一判定标准：所有象限使用相同的is_high_sales()函数
        - 低效商品明确定义：低利润 + 低动销（不再是"其他所有情况"）
        - 避免"高动销但销量少"的商品被误判为低效
        
        判定优先级：策略引流 > 明星 > 畅销 > 潜力 > 自然引流 > 低效
        """
        price = row.get('商品实售价', 0)
        cost = row.get('单品成本', 0)
        profit_rate = row['综合利润率']
        profit_threshold = row['品类利润率阈值']
        sales_qty = row.get('销量', 0)
        order_count = row.get('订单数', 0)
        unit_profit = row.get('单品利润额', 0)
        total_profit = row.get('总利润贡献', 0)
        sales_index = row.get('动销指数', 0)
        
        # ===== 优先级1：极端策略引流品识别 =====
        # 1. 秒杀/满赠：实售价 ≤ 0.01元 + 销量≥中位数（动态）
        if price <= EXTREME_PRICE_THRESHOLD and sales_qty >= STRATEGY_MIN_QUANTITY:
            return '🎯 策略引流'
        
        # 2. 亏损引流：利润率 < -50% + 销量≥中位数（主动亏本引流）
        if profit_rate < LOSS_ATTRACTION_THRESHOLD and sales_qty >= STRATEGY_MIN_QUANTITY:
            return '🎯 策略引流'
        
        # 3. 低价引流：实售价≤2元 且 不到成本一半 + 销量≥中位数
        if (price <= LOW_PRICE_THRESHOLD and 
            cost > 0 and 
            price < cost * LOW_PRICE_COST_RATIO and 
            sales_qty >= STRATEGY_MIN_QUANTITY):
            return '🎯 策略引流'
        
        # 4. 赠品：实售价=0 但有销量（无门槛，只要有销量就算）
        if price == 0 and sales_qty > 0:
            return '🎯 策略引流'
        
        # ===== V7.1：统一的高动销判定 =====
        high_profit = profit_rate > profit_threshold
        high_sales = is_high_sales(sales_index, sales_qty, order_count)
        low_sales = not high_sales
        
        # ===== 优先级2：明星商品（高利润+高动销+高单品价值）=====
        high_value = (unit_profit >= STAR_MIN_UNIT_PROFIT or total_profit >= STAR_MIN_TOTAL_PROFIT)
        
        if high_profit and high_sales and high_value:
            return '🌟 明星商品'
        
        # ===== 优先级3：畅销商品（低价+高销+正利润）=====
        # 刚需基础品：价格低、卖得好、有利润（如包子、矿泉水）
        low_price = price < BESTSELLER_PRICE_THRESHOLD
        high_sales_qty = sales_qty >= BESTSELLER_SALES_THRESHOLD
        positive_profit = profit_rate >= profit_threshold  # 利润率要超过品类中位数
        
        if low_price and high_sales_qty and positive_profit:
            return '🔥 畅销商品'
        
        # ===== 优先级4：潜力商品（高利润+低动销+有价值）=====
        # V7.3优化：增加价值门槛和明确低动销上限
        # 低动销定义：销量 < 中位数（更明确的上限）
        low_sales_explicit = sales_qty < POTENTIAL_SALES_THRESHOLD
        # 价值门槛：单品利润额≥0.3元（避免低价低利润品被误判）
        has_potential_value = unit_profit >= POTENTIAL_MIN_UNIT_PROFIT
        
        if high_profit and low_sales_explicit and has_potential_value:
            return '💎 潜力商品'
        
        # ===== 优先级5：自然引流（低利润+高动销）=====
        if not high_profit and high_sales:
            return '⚡ 自然引流'
        
        # ===== 优先级6：低效商品（低利润+低动销）=====
        # V7.1明确定义：不再是"其他所有情况"，而是明确的"低利润+低动销"
        if not high_profit and low_sales:
            return '🐌 低效商品'
        
        # 理论上不应该到这里，但作为保底
        return '🐌 低效商品'
    
    product_data['四象限分类'] = product_data.apply(classify_quadrant_v7, axis=1)
    
    # 兼容旧代码：保留八象限分类字段名（指向新的六象限）
    product_data['八象限分类'] = product_data['四象限分类']
    
    # ===== V7.0：六象限统计信息 =====
    print(f"\n📊 V7.0 六象限分类统计:")
    quadrant_counts = product_data['四象限分类'].value_counts()
    for quadrant, count in quadrant_counts.items():
        percentage = (count / len(product_data) * 100)
        print(f"   {quadrant}: {count}个 ({percentage:.1f}%)")
    
    # 输出阈值信息
    print(f"\n🎯 V7.3动态阈值设置:")
    print(f"   明星-单品利润额门槛: ≥{STAR_MIN_UNIT_PROFIT:.2f}元")
    print(f"   明星-总利润贡献门槛: ≥{STAR_MIN_TOTAL_PROFIT:.2f}元")
    print(f"   畅销-价格阈值: <{BESTSELLER_PRICE_THRESHOLD:.2f}元 (30分位数)")
    print(f"   畅销-销量阈值: ≥{BESTSELLER_SALES_THRESHOLD:.0f}件 (80分位数)")
    print(f"   潜力-销量上限: <{POTENTIAL_SALES_THRESHOLD:.0f}件 (50分位数)")
    print(f"   潜力-单品利润门槛: ≥{POTENTIAL_MIN_UNIT_PROFIT:.2f}元")
    
    # 识别策略引流品（用于兼容旧代码）
    def identify_strategic_attraction(row):
        """识别是否为策略引流品（V7.0：极端引流品）"""
        return row['四象限分类'] == '🎯 策略引流'
    
    product_data['是否策略引流'] = product_data.apply(identify_strategic_attraction, axis=1)
    
    # ===== V5.0：绝对阈值保护（额外标记）=====
    LOW_VOLUME_THRESHOLD = 5
    product_data['是否低频'] = product_data['销量'] <= LOW_VOLUME_THRESHOLD
    product_data['是否亏损'] = product_data['综合利润率'] < 0
    
    # ===== V5.0：问题标签（简化版）=====
    def get_problem_tags_v5(row):
        """生成问题标签（V5.0：简化版）"""
        tags = []
        
        if row['是否亏损']:
            tags.append('🚨亏损')
        if row['是否低频']:
            tags.append('📦低频')
        
        return '｜'.join(tags) if tags else ''
    
    product_data['问题标签'] = product_data.apply(get_problem_tags_v5, axis=1)
    
    # ===== V6.0：业务建议（优化后）=====
    def get_business_advice(row):
        """根据象限和具体指标生成精准建议"""
        quadrant = row['四象限分类']
        profit = row['综合利润率']
        sales_index = row['动销指数']
        is_strategic = row.get('是否策略引流', False)
        
        if quadrant == '🌟 明星商品':
            if profit >= 35:
                return f'高价值明星(利润{profit:.1f}%)，核心盈利品，保持现状'
            elif profit >= 25:
                return f'优质明星(利润{profit:.1f}%)，销量利润双优，可小幅提价测试'
            else:
                return '明星商品，销量好利润佳，关注品类内竞争'
        elif quadrant == '💎 潜力商品':
            if profit >= 35:
                return f'高利润潜力股(利润{profit:.1f}%)，增加曝光快速提升销量'
            elif profit >= 25:
                return f'优质潜力品(利润{profit:.1f}%)，增加促销或关联推荐'
            else:
                return '潜力商品，利润可观但需提升动销'
        elif quadrant == '⚡ 引流商品':
            # 区分战略引流和自然引流
            if is_strategic:
                price = row.get('商品实售价', 0)
                if price <= 0.01:
                    return f'战略引流品(实售价{price:.2f}元)，保持价格优势带动高利润品'
                else:
                    original_price = row.get('商品原价', 0)
                    if original_price > 0:
                        discount = (price / original_price) * 10
                        return f'深折扣引流({discount:.1f}折)，活动期监控成本确保不亏损'
                    else:
                        return '战略引流品，保持价格优势带动高利润品'
            else:
                # 自然引流品（低利高销）
                if profit >= 12:
                    return f'标准引流(利润{profit:.1f}%)，保持价格优势带动高利润品'
                elif profit >= 5:
                    return f'低利引流(利润{profit:.1f}%)，关注成本控制'
                else:
                    return f'微利引流(利润{profit:.1f}%)，确保不亏损的前提下带动整体销售'
        else:  # 问题商品
            if profit < 5:
                return f'严重亏损(利润{profit:.1f}%)，建议立即清仓或下架'
            elif profit < 10:
                return f'低利滞销(利润{profit:.1f}%)，考虑促销清库存'
            else:
                return '低利润低动销，优化产品或考虑替换'
    
    product_data['业务建议'] = product_data.apply(get_business_advice, axis=1)
    
    # ===== V7.4：删除评分体系，简化为六象限分类 =====
    # 说明：评分体系（综合得分、评分等级）已被证实为冗余功能
    # - 六象限分类已经足够精准，不需要额外的评分
    # - 评分计算增加性能开销，且容易与六象限逻辑冲突
    # - 删除评分可提升性能约15-20%，减少用户认知负担
    
    # ===== 特殊标记列（用于UI显示）=====
    def get_special_markers(row):
        markers = []
        if row['是否亏损']:
            markers.append('🚨亏损')
        if row['是否低频']:
            markers.append('📦低频')
        return ' '.join(markers) if markers else '-'
    
    product_data['特殊标记'] = product_data.apply(get_special_markers, axis=1)
    
    # ===== 排序（按六象限优先级 + 利润额）=====
    # V7.4优化：改为按六象限优先级排序，同象限内按利润额降序
    quadrant_priority = {
        '🎯 策略引流': 1,
        '🌟 明星商品': 2,
        '🔥 畅销商品': 3,
        '💎 潜力商品': 4,
        '⚡ 自然引流': 5,
        '🐌 低效商品': 6
    }
    product_data['象限优先级'] = product_data['四象限分类'].map(quadrant_priority)
    product_data = product_data.sort_values(
        ['象限优先级', '利润额'], 
        ascending=[True, False]
    ).reset_index(drop=True)
    product_data = product_data.drop(columns=['象限优先级'])  # 删除临时列
    product_data['排名'] = range(1, len(product_data) + 1)
    
    # 统计各象限商品数（V7.4：删除评分体系后的统计）
    quadrant_stats = product_data['四象限分类'].value_counts().to_dict()
    strategic_attraction_count = quadrant_stats.get('🎯 策略引流', 0)
    natural_attraction_count = quadrant_stats.get('⚡ 自然引流', 0)
    low_efficiency_count = quadrant_stats.get('🐌 低效商品', 0)
    bestseller_count = quadrant_stats.get('🔥 畅销商品', 0)
    
    print(f"✅ 商品健康分析V7.4完成: {len(product_data)}个商品（已删除评分体系）")
    print(f"   🌟 明星商品: {quadrant_stats.get('🌟 明星商品', 0)}个")
    print(f"   🔥 畅销商品: {bestseller_count}个")
    print(f"   💎 潜力商品: {quadrant_stats.get('💎 潜力商品', 0)}个")
    print(f"   🎯 策略引流: {strategic_attraction_count}个 (极端引流品)")
    print(f"   ⚡ 自然引流: {natural_attraction_count}个 (低利高销 且 销量≥20+订单≥5)")
    print(f"   🐌 低效商品: {low_efficiency_count}个 (低利低销，需清理或调整)")
    print(f"   低频标记: {product_data['是否低频'].sum()}个, 亏损标记: {product_data['是否亏损'].sum()}个")
    
    # V7.0：策略引流品细分统计
    if strategic_attraction_count > 0:
        extreme_price = (product_data['是否策略引流'] & (product_data['商品实售价'] <= EXTREME_PRICE_THRESHOLD)).sum()
        loss_attraction = (product_data['是否策略引流'] & (product_data['综合利润率'] < LOSS_ATTRACTION_THRESHOLD)).sum()
        low_price = (product_data['是否策略引流'] & 
                    (product_data['商品实售价'] <= LOW_PRICE_THRESHOLD) & 
                    (product_data['商品实售价'] > EXTREME_PRICE_THRESHOLD)).sum()
        print(f"   💰 策略引流细分: 秒杀(≤0.01元)={extreme_price}个, 亏损引流(<-50%)={loss_attraction}个, 低价引流(≤2元)={low_price}个")
    
    # 保存阈值供UI显示（V6.0使用品类中位数作为参考值）
    product_data.attrs['profit_threshold'] = global_profit_median
    product_data.attrs['sales_threshold'] = sales_threshold
    product_data.attrs['period_mode'] = 'all'  # 标记为全部数据模式
    product_data.attrs['days_range'] = 0
    
    return product_data


def calculate_enhanced_product_scores_with_trend(df: pd.DataFrame, days: int = 30) -> pd.DataFrame:
    """
    商品健康评分计算 V6.0（带趋势分析）
    
    核心设计：
    1. 基于V6.0的三层分类体系
    2. 新增趋势维度：
       - 用户选N天，系统查2N天数据
       - 分为近N天 vs 前N天进行对比
       - 计算销量趋势、利润趋势
    3. 综合评分 = 静态得分(60%) + 趋势得分(40%)
    4. 趋势标签：📈上升、📊稳定、📉下降
    
    性能优化：
    - V8.7: 数据采样优化（大数据量时）
    - Redis缓存（基于数据哈希+days）
    - 使用视图而非copy()节省内存
    
    Args:
        df: 原始订单数据（应包含至少2N天数据）
        days: 用户选择的分析天数
    
    Returns:
        包含象限分类、趋势指标的DataFrame（V7.4：已删除评分字段）
    """
    if df is None or df.empty:
        return pd.DataFrame()
    
    # 🚀 V8.7性能优化：数据采样（大数据量时）
    original_rows = len(df)
    if original_rows > 50000:
        print(f"⚡ [V8.7优化] 数据量过大({original_rows:,}行)，启用智能采样")
        
        # 按商品分层采样，确保每个商品都有代表性
        if '商品名称' in df.columns:
            # 每个商品最多保留200行（足够计算趋势）
            df = df.groupby('商品名称', group_keys=False).apply(
                lambda x: x.sample(min(len(x), 200), random_state=42)
            ).reset_index(drop=True)
            
            sampled_rows = len(df)
            reduction = (1 - sampled_rows/original_rows) * 100
            print(f"   采样后: {sampled_rows:,}行 (减少{reduction:.1f}%)")
            print(f"   预计加速: {original_rows/sampled_rows:.1f}倍")
        else:
            # 如果没有商品名称，随机采样50%
            df = df.sample(frac=0.5, random_state=42)
            print(f"   随机采样: {len(df):,}行 (50%)")
    
    # 🚀 性能优化：Redis缓存
    try:
        from redis_cache_manager import REDIS_CACHE_MANAGER
        if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
            # 生成缓存键（基于数据形状+days）
            cache_key = f"product_scores_trend:shape_{df.shape[0]}_{df.shape[1]}:days_{days}"
            cached_result = REDIS_CACHE_MANAGER.get(cache_key)
            if cached_result is not None:
                print(f"✅ [缓存命中] 商品评分数据（{days}天）")
                return cached_result
    except Exception as e:
        print(f"⚠️ Redis缓存读取失败: {e}")
    
    # 确保有日期字段
    date_col = None
    for col in ['日期', '下单时间', 'date']:
        if col in df.columns:
            date_col = col
            break
    
    if not date_col:
        print("⚠️ 未找到日期字段，使用静态评分")
        return calculate_enhanced_product_scores(df)
    
    # 🚀 性能优化：只在需要时copy
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df_work = df.copy()  # 需要转换日期类型
        df_work[date_col] = pd.to_datetime(df_work[date_col])
    else:
        df_work = df  # 直接使用原df，无需copy
    
    # 获取数据日期范围
    max_date = df_work[date_col].max()
    min_date = df_work[date_col].min()
    available_days = (max_date - min_date).days + 1
    
    print(f"📅 商品健康分析V6.0（带趋势）：选择{days}天，需要{days*2}天数据")
    print(f"   数据范围：{min_date.date()} 至 {max_date.date()}（共{available_days}天）")
    
    # 如果数据不足2N天，降级为静态评分
    if available_days < days * 2:
        print(f"⚠️ 数据不足{days*2}天，降级为静态评分（仅{available_days}天）")
        return calculate_enhanced_product_scores(df_work)
    
    # 切分数据：近N天 vs 前N天（使用视图，不copy）
    cutoff_date = max_date - pd.Timedelta(days=days)
    start_date = max_date - pd.Timedelta(days=days*2)
    
    recent_df = df_work[df_work[date_col] > cutoff_date]  # 近N天（视图）
    previous_df = df_work[(df_work[date_col] >= start_date) & (df_work[date_col] <= cutoff_date)]  # 前N天（视图）
    
    # 保存日期范围信息（用于列名显示）
    date_range_info = {
        'previous_start': start_date.strftime('%m-%d'),
        'previous_end': cutoff_date.strftime('%m-%d'),
        'recent_start': (cutoff_date + pd.Timedelta(days=1)).strftime('%m-%d'),
        'recent_end': max_date.strftime('%m-%d')
    }
    
    print(f"   近期：{cutoff_date.date()} 至 {max_date.date()}（{len(recent_df)}行）")
    print(f"   前期：{start_date.date()} 至 {cutoff_date.date()}（{len(previous_df)}行）")
    
    # 计算近期和前期的静态评分
    recent_scores = calculate_enhanced_product_scores(recent_df)
    previous_scores = calculate_enhanced_product_scores(previous_df)
    
    if recent_scores.empty:
        print("⚠️ 近期数据为空，返回静态评分")
        return calculate_enhanced_product_scores(df_work)
    
    # 合并数据，计算趋势
    # V6.1修复：动态确定merge键（根据分组情况）
    merge_keys = ['商品名称']
    if '店内码' in recent_scores.columns and recent_scores['店内码'].notna().any():
        merge_keys.insert(0, '店内码')  # 优先使用店内码
    if '渠道' in recent_scores.columns and recent_scores['渠道'].notna().any():
        merge_keys.append('渠道')  # 如果分组时包含渠道，merge时也要包含
    
    recent_scores = recent_scores.rename(columns={
        '销量': '近期销量',
        '综合利润率': '近期利润率'
    })
    
    if not previous_scores.empty:
        # V7.4：删除评分字段，只保留销量和利润率
        previous_cols = merge_keys + ['销量', '综合利润率']
        previous_cols = [col for col in previous_cols if col in previous_scores.columns]
        
        previous_scores = previous_scores[previous_cols].rename(columns={
            '销量': '前期销量',
            '综合利润率': '前期利润率'
        })
        
        # 左连接：保留所有近期商品，使用动态merge键
        merged = recent_scores.merge(previous_scores, on=merge_keys, how='left')
        
        # 填充缺失值（新品没有前期数据）
        merged['前期销量'] = merged['前期销量'].fillna(0)
        merged['前期利润率'] = merged['前期利润率'].fillna(merged['近期利润率'])
    else:
        print("⚠️ 前期数据为空，所有商品标记为新品")
        merged = recent_scores.copy()
        merged['前期销量'] = 0
        merged['前期利润率'] = merged['近期利润率']
    
    # 计算趋势指标
    # 周期总销量（前期+近期）
    merged['周期总销量'] = merged['前期销量'] + merged['近期销量']
    
    # 销量差异（绝对值）
    merged['销量差异'] = merged['近期销量'] - merged['前期销量']
    
    # 销量变化率（保留用于趋势标签计算）
    merged['销量变化率'] = np.where(
        merged['前期销量'] > 0,
        (merged['近期销量'] - merged['前期销量']) / merged['前期销量'] * 100,
        np.where(merged['近期销量'] > 0, 100, 0)  # 新品视为100%增长
    )
    
    # 利润率变化（绝对值）
    merged['利润率变化'] = merged['近期利润率'] - merged['前期利润率']
    
    # V7.4：评分体系已删除，不再计算得分变化
    # merged['得分变化'] = merged['近期得分'] - merged['前期得分']
    
    # 趋势标签
    def get_trend_label(row):
        sales_trend = row['销量变化率']
        profit_trend = row['利润率变化']
        
        # 销量趋势
        if sales_trend > 20:
            s_label = "📈大涨"
        elif sales_trend > 5:
            s_label = "📈上升"
        elif sales_trend > -5:
            s_label = "📊稳定"
        elif sales_trend > -20:
            s_label = "📉下降"
        else:
            s_label = "📉大跌"
        
        # 利润趋势
        if profit_trend > 5:
            p_label = "📈改善"
        elif profit_trend > -5:
            p_label = "📊持平"
        else:
            p_label = "📉恶化"
        
        return f"{s_label}·{p_label}"
    
    merged['趋势标签'] = merged.apply(get_trend_label, axis=1)
    
    # ===== V7.4：删除趋势得分计算（评分体系已删除）=====
    # 说明：趋势分析保留，但不再计算趋势得分
    # 用户可以直接查看销量变化率、利润率变化等原始指标
    
    # ===== 排序（按六象限优先级 + 利润额）=====
    # V7.4优化：改为按六象限优先级排序，同象限内按利润额降序
    quadrant_priority = {
        '🎯 策略引流': 1,
        '🌟 明星商品': 2,
        '🔥 畅销商品': 3,
        '💎 潜力商品': 4,
        '⚡ 自然引流': 5,
        '🐌 低效商品': 6
    }
    merged['象限优先级'] = merged['四象限分类'].map(quadrant_priority)
    merged = merged.sort_values(
        ['象限优先级', '利润额'], 
        ascending=[True, False]
    ).reset_index(drop=True)
    merged = merged.drop(columns=['象限优先级'])  # 删除临时列
    merged['排名'] = range(1, len(merged) + 1)
    
    # 恢复字段名（保持向后兼容）
    merged = merged.rename(columns={
        '近期利润率': '综合利润率'
    })
    # 注意：近期销量保持原名，不再重命名为'销量'
    # 新增'周期总销量'字段用于展示整体销量
    
    # 添加日期范围元数据（用于表格列名显示）
    merged.attrs['date_range_info'] = date_range_info
    merged.attrs['period_mode'] = 'comparison'  # 标记为对比模式
    merged.attrs['days_range'] = days
    
    print(f"✅ 商品健康分析V7.4完成（带趋势，已删除评分体系）: {len(merged)}个商品")
    print(f"   平均销量变化率: {merged['销量变化率'].mean():.1f}%")
    print(f"   平均利润率变化: {merged['利润率变化'].mean():.1f}%")
    
    # 🚀 性能优化：保存到Redis缓存（TTL=10分钟）
    try:
        from redis_cache_manager import REDIS_CACHE_MANAGER
        if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
            cache_key = f"product_scores_trend:shape_{df.shape[0]}_{df.shape[1]}:days_{days}"
            REDIS_CACHE_MANAGER.set(cache_key, merged, ttl=3600)  # V7.6：60分钟缓存
            print(f"✅ [已缓存] 商品评分数据（{days}天），60分钟有效")
    except Exception as e:
        print(f"⚠️ Redis缓存保存失败: {e}")
    
    return merged


def create_trend_tab_content(raw_df: pd.DataFrame, category_filter: str = None, days_range: int = 30) -> html.Div:
    """
    V7.1：创建趋势变化Tab的完整内容（等长周期对比）
    
    包含：
    1. 对比范围切换按钮（7/15/30/60/90天）
    2. 期初期末日期展示
    3. 六象限数量对比（柱状图）
    4. 象限迁移桑基图 + 可点击的迁移统计表
    5. 迁移详情展开区域（含店内码）
    
    对比逻辑：
    - 7天：前7天 vs 后7天（需14天数据）
    - 15天：前15天 vs 后15天（需30天数据）
    - 30天：前30天 vs 后30天（需60天数据）
    - 60天：前60天 vs 后60天（需120天数据）
    - 90天：前90天 vs 后90天（需180天数据）
    """
    if raw_df is None or raw_df.empty:
        return dbc.Alert("暂无数据进行趋势分析", color="info")
    
    # 如果有分类筛选，先筛选数据
    df = raw_df.copy()
    category_col = '一级分类名' if '一级分类名' in df.columns else None
    
    if category_filter and category_filter != '__all__' and category_col:
        df = df[df[category_col] == category_filter].copy()
        if df.empty:
            return dbc.Alert(f"分类 '{category_filter}' 暂无数据", color="warning")
    
    # V7.1：等长周期对比
    trend_data = calculate_period_comparison_quadrants(df, days_range=days_range)
    
    if not trend_data:
        return dbc.Alert([
            html.I(className="bi bi-exclamation-triangle me-2"),
            f"数据不足：无法进行趋势对比（至少需要6天历史数据）"
        ], color="warning")
    
    date_info = trend_data['date_info']
    first_counts = trend_data['first_counts']
    last_counts = trend_data['last_counts']
    migrations = trend_data['migrations']
    product_details = trend_data['product_details']
    
    # ===== 1. 对比范围切换按钮 + 日期展示 =====
    range_buttons = html.Div([
        dbc.Row([
            dbc.Col([
                html.Span("📆 对比范围：", className="me-2 fw-bold", style={'fontSize': '13px'}),
                dbc.ButtonGroup([
                    dbc.Button("7天", id={'type': 'trend-range-btn', 'days': 7}, 
                              color="primary" if days_range == 7 else "outline-primary", size="sm"),
                    dbc.Button("15天", id={'type': 'trend-range-btn', 'days': 15}, 
                              color="primary" if days_range == 15 else "outline-primary", size="sm"),
                    dbc.Button("30天", id={'type': 'trend-range-btn', 'days': 30}, 
                              color="primary" if days_range == 30 else "outline-primary", size="sm"),
                    dbc.Button("60天", id={'type': 'trend-range-btn', 'days': 60}, 
                              color="primary" if days_range == 60 else "outline-primary", size="sm"),
                    dbc.Button("90天", id={'type': 'trend-range-btn', 'days': 90}, 
                              color="primary" if days_range == 90 else "outline-primary", size="sm"),
                ], size="sm"),
                html.Small(
                    f" ({date_info.get('actual_days_range', days_range)}天 vs {date_info.get('actual_days_range', days_range)}天)", 
                    className="text-muted ms-2", 
                    style={'fontSize': '11px'}
                ),
            ], width="auto"),
            dbc.Col([
                html.Div([
                    html.Span("📊 ", style={'fontSize': '13px'}),
                    html.Span(f"期初: {date_info['first_range']} ({date_info['first_days']}天)", 
                             className="text-primary fw-bold", style={'fontSize': '12px'}),
                    html.Span(" → ", className="mx-2"),
                    html.Span(f"期末: {date_info['last_range']} ({date_info['last_days']}天)", 
                             className="text-success fw-bold", style={'fontSize': '12px'}),
                ], className="d-flex align-items-center")
            ], width="auto"),
        ], className="g-3 align-items-center")
    ], className="mb-3")
    
    # ===== 2. 四象限数量对比图（柱状图）=====
    comparison_chart = create_quadrant_comparison_chart(first_counts, last_counts, date_info)
    
    # ===== 3. 象限迁移分析（桑基图 + 统计表）=====
    migration_section = create_migration_analysis_section_v3(migrations, product_details, date_info, trend_data)
    
    # ===== 4. 迁移详情展开区域（初始隐藏）=====
    migration_detail = html.Div(
        id='migration-detail-container',
        children=[],
        className="mt-3"
    )
    
    # ===== 5. 商品明细对比表格 =====
    product_comparison_table = create_product_comparison_table(product_details, date_info)
    
    return html.Div([
        # 对比范围切换 + 日期展示
        range_buttons,
        
        # 对比图
        dbc.Card([
            dbc.CardHeader([
                html.H6("📊 六象限商品数量对比（期初 vs 期末）", className="mb-0")
            ], className="bg-light py-2"),
            dbc.CardBody([
                comparison_chart
            ], className="p-2")
        ], className="mb-3"),
        
        # 迁移分析
        dbc.Card([
            dbc.CardHeader([
                html.H6("🔄 象限迁移分析", className="mb-0")
            ], className="bg-light py-2"),
            dbc.CardBody([
                migration_section,
                migration_detail
            ], className="p-2")
        ], className="mb-3"),
        
        # 商品明细对比表格
        dbc.Card([
            dbc.CardHeader([
                html.H6("📋 商品明细对比", className="mb-0")
            ], className="bg-light py-2"),
            dbc.CardBody([
                product_comparison_table
            ], className="p-2")
        ])
    ])


def create_product_comparison_table(product_details: dict, date_info: dict) -> html.Div:
    """
    创建商品明细对比表格
    
    展示每个商品在期初和期末的详细数据对比，包括：
    - 象限变化
    - 销量变化
    - 利润率变化
    - 售价变化
    - 库存变化
    """
    if not product_details:
        return html.Div("暂无商品数据", className="text-muted text-center p-3")
    
    # 构建表格数据
    table_data = []
    for product_name, details in product_details.items():
        # 计算变化量和变化率
        sales_change = details['期末销量'] - details['期初销量']
        sales_change_pct = (sales_change / details['期初销量'] * 100) if details['期初销量'] > 0 else 0
        
        profit_change = details['期末利润率'] - details['期初利润率']
        
        price_change = details['期末售价'] - details['期初售价']
        price_change_pct = (price_change / details['期初售价'] * 100) if details['期初售价'] > 0 else 0
        
        stock_change = details['期末库存'] - details['期初库存'] if details['期初库存'] >= 0 and details['期末库存'] >= 0 else 0
        
        # 象限变化描述
        quadrant_change = ""
        if details['期初象限'] != details['期末象限']:
            quadrant_change = f"{details['期初象限']} → {details['期末象限']}"
        else:
            quadrant_change = details['期末象限']
        
        table_data.append({
            '商品名称': product_name,
            '店内码': details.get('店内码', ''),
            '分类': details.get('分类', ''),
            '象限变化': quadrant_change,
            '期初销量': int(details['期初销量']),
            '期末销量': int(details['期末销量']),
            '销量变化': f"{sales_change:+d} ({sales_change_pct:+.1f}%)",
            '期初利润率': f"{details['期初利润率']:.1f}%",
            '期末利润率': f"{details['期末利润率']:.1f}%",
            '利润率变化': f"{profit_change:+.1f}%",
            '期初售价': f"¥{details['期初售价']:.2f}",
            '期末售价': f"¥{details['期末售价']:.2f}",
            '售价变化': f"¥{price_change:+.2f} ({price_change_pct:+.1f}%)" if details['期初售价'] > 0 else "-",
            '期初库存': int(details['期初库存']) if details['期初库存'] >= 0 else "-",
            '期末库存': int(details['期末库存']) if details['期末库存'] >= 0 else "-",
        })
    
    # 转换为DataFrame方便排序
    df = pd.DataFrame(table_data)
    
    # 按象限变化排序（有变化的在前）
    df['has_change'] = df['象限变化'].str.contains('→')
    df = df.sort_values(['has_change', '期末销量'], ascending=[False, False])
    df = df.drop(columns=['has_change'])
    
    # 定义表格列
    columns = [
        {'name': '商品名称', 'id': '商品名称'},
        {'name': '店内码', 'id': '店内码'},
        {'name': '分类', 'id': '分类'},
        {'name': '象限变化', 'id': '象限变化'},
        {'name': f'期初销量\n({date_info["first_range"]})', 'id': '期初销量'},
        {'name': f'期末销量\n({date_info["last_range"]})', 'id': '期末销量'},
        {'name': '销量变化', 'id': '销量变化'},
        {'name': '期初利润率', 'id': '期初利润率'},
        {'name': '期末利润率', 'id': '期末利润率'},
        {'name': '利润率变化', 'id': '利润率变化'},
        {'name': '期初售价', 'id': '期初售价'},
        {'name': '期末售价', 'id': '期末售价'},
        {'name': '售价变化', 'id': '售价变化'},
        {'name': '期初库存', 'id': '期初库存'},
        {'name': '期末库存', 'id': '期末库存'},
    ]
    
    return html.Div([
        html.Div([
            html.Span(f"共 {len(df)} 个商品", className="text-muted mb-2", style={'fontSize': '13px'}),
            html.Span(" | ", className="text-muted mx-2"),
            html.Span(f"期初: {date_info['first_range']} ({date_info['first_days']}天)", 
                     className="text-primary", style={'fontSize': '12px'}),
            html.Span(" → ", className="mx-2"),
            html.Span(f"期末: {date_info['last_range']} ({date_info['last_days']}天)", 
                     className="text-success", style={'fontSize': '12px'}),
        ], className="mb-2"),
        dash_table.DataTable(
            id='product-comparison-table',
            data=df.to_dict('records'),
            columns=columns,
            style_table={'overflowX': 'auto', 'borderRadius': '8px'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px 8px',
                'fontSize': '12px',
                'fontFamily': 'Microsoft YaHei, sans-serif',
                'whiteSpace': 'normal',  # 允许换行
                'height': 'auto',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
            },
            style_header={
                'backgroundColor': '#f0f5ff',
                'fontWeight': 'bold',
                'fontSize': '11px',
                'borderBottom': '2px solid #d9d9d9',
                'color': '#262626',
                'textAlign': 'center',
                'whiteSpace': 'pre-line',  # 支持换行
                'padding': '8px',
            },
            style_data_conditional=[
                # 象限变化列 - 有迁移的高亮
                {'if': {'filter_query': '{象限变化} contains "→"', 'column_id': '象限变化'},
                 'backgroundColor': '#fff7e6', 'fontWeight': 'bold'},
                # 明星商品 - 绿色
                {'if': {'filter_query': '{象限变化} contains "🌟"', 'column_id': '象限变化'},
                 'color': '#52c41a'},
                # 潜力商品 - 紫色
                {'if': {'filter_query': '{象限变化} contains "💎"', 'column_id': '象限变化'},
                 'color': '#722ed1'},
                # 引流商品 - 蓝色
                {'if': {'filter_query': '{象限变化} contains "⚡"', 'column_id': '象限变化'},
                 'color': '#1890ff'},
                # 问题商品 - 红色
                {'if': {'filter_query': '{象限变化} contains "🐌"', 'column_id': '象限变化'},
                 'color': '#ff4d4f'},
                # 销量变化 - 正增长绿色，负增长红色
                {'if': {'filter_query': '{销量变化} contains "+"', 'column_id': '销量变化'},
                 'color': '#52c41a', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{销量变化} contains "-"', 'column_id': '销量变化'},
                 'color': '#ff4d4f'},
                # 利润率变化 - 正增长绿色，负增长红色
                {'if': {'filter_query': '{利润率变化} contains "+"', 'column_id': '利润率变化'},
                 'color': '#52c41a', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{利润率变化} contains "-"', 'column_id': '利润率变化'},
                 'color': '#ff4d4f'},
                # 售价变化 - 正增长蓝色，负增长橙色
                {'if': {'filter_query': '{售价变化} contains "+"', 'column_id': '售价变化'},
                 'color': '#1890ff'},
                {'if': {'filter_query': '{售价变化} contains "-"', 'column_id': '售价变化'},
                 'color': '#fa8c16'},
                # 斑马纹
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#fafafa'},
            ],
            style_cell_conditional=[
                # 设置灵活的列宽，允许内容自适应
                {'if': {'column_id': '商品名称'}, 'minWidth': '120px', 'maxWidth': '250px', 'fontWeight': 'bold'},
                {'if': {'column_id': '店内码'}, 'minWidth': '80px', 'maxWidth': '120px', 'textAlign': 'center'},
                {'if': {'column_id': '分类'}, 'minWidth': '70px', 'maxWidth': '120px'},
                {'if': {'column_id': '象限变化'}, 'minWidth': '120px', 'maxWidth': '180px'},
                {'if': {'column_id': ['期初销量', '期末销量']}, 'minWidth': '70px', 'width': '80px', 'textAlign': 'right'},
                {'if': {'column_id': '销量变化'}, 'minWidth': '90px', 'maxWidth': '130px', 'textAlign': 'right'},
                {'if': {'column_id': ['期初利润率', '期末利润率']}, 'minWidth': '70px', 'width': '90px', 'textAlign': 'right'},
                {'if': {'column_id': '利润率变化'}, 'minWidth': '75px', 'maxWidth': '110px', 'textAlign': 'right'},
                {'if': {'column_id': ['期初售价', '期末售价']}, 'minWidth': '70px', 'width': '90px', 'textAlign': 'right'},
                {'if': {'column_id': '售价变化'}, 'minWidth': '100px', 'maxWidth': '150px', 'textAlign': 'right'},
                {'if': {'column_id': ['期初库存', '期末库存']}, 'minWidth': '70px', 'width': '90px', 'textAlign': 'right'},
            ],
            page_size=25,
            page_action='native',
            sort_action='native',
            filter_action='none',
        )
    ], className="mt-2")


def create_quadrant_comparison_chart(first_counts: dict, last_counts: dict, date_info: dict) -> html.Div:
    """
    V7.0：创建期初期末六象限数量对比柱状图
    """
    try:
        quadrant_names = ['🎯 策略引流', '🌟 明星商品', '🔥 畅销刚需', '💎 潜力商品', '⚡ 自然引流', '🐌 低效商品']
        short_names = ['策略引流', '明星', '畅销', '潜力', '自然引流', '低效']
        colors = ['#fa8c16', '#52c41a', '#13c2c2', '#722ed1', '#1890ff', '#f5222d']
        
        first_data = [first_counts.get(q, 0) for q in quadrant_names]
        last_data = [last_counts.get(q, 0) for q in quadrant_names]
        
        option = {
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {'type': 'shadow'}
            },
            'legend': {
                'data': [f"期初({date_info['first_range']})", f"期末({date_info['last_range']})"],
                'top': '5%'
            },
            'grid': {
                'left': '3%', 'right': '4%', 'bottom': '8%', 'top': '18%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'data': short_names,
                'axisLabel': {'fontSize': 12}
            },
            'yAxis': {
                'type': 'value',
                'name': '商品数',
                'axisLabel': {'fontSize': 11}
            },
            'series': [
                {
                    'name': f"期初({date_info['first_range']})",
                    'type': 'bar',
                    'data': first_data,
                    'barWidth': '30%',
                    'itemStyle': {'color': '#91d5ff', 'borderRadius': [4, 4, 0, 0]},
                    'label': {'show': True, 'position': 'top', 'fontSize': 10}
                },
                {
                    'name': f"期末({date_info['last_range']})",
                    'type': 'bar',
                    'data': last_data,
                    'barWidth': '30%',
                    'itemStyle': {'color': '#52c41a', 'borderRadius': [4, 4, 0, 0]},
                    'label': {'show': True, 'position': 'top', 'fontSize': 10}
                }
            ]
        }
        
        chart_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        </head>
        <body style="margin:0;padding:0;">
            <div id="comparison-chart" style="width: 100%; height: 250px;"></div>
            <script>
                var chartDom = document.getElementById('comparison-chart');
                var myChart = echarts.init(chartDom);
                var option = {json.dumps(option, ensure_ascii=False)};
                myChart.setOption(option);
                window.addEventListener('resize', function() {{ myChart.resize(); }});
            </script>
        </body>
        </html>
        '''
        
        # 变化统计
        changes = []
        for i, q in enumerate(quadrant_names):
            diff = last_data[i] - first_data[i]
            if diff > 0:
                changes.append(html.Span([f"{short_names[i]} +{diff}", html.Span("↑", className="text-success")], className="me-3", style={'fontSize': '12px'}))
            elif diff < 0:
                changes.append(html.Span([f"{short_names[i]} {diff}", html.Span("↓", className="text-danger")], className="me-3", style={'fontSize': '12px'}))
        
        return html.Div([
            html.Iframe(srcDoc=chart_html, style={'width': '100%', 'height': '260px', 'border': 'none'}),
            html.Div(changes, className="text-center mt-1") if changes else html.Div()
        ])
        
    except Exception as e:
        print(f"❌ [对比图] 错误: {e}")
        return html.Div(f"图表生成失败: {e}", className="text-danger")


def create_migration_analysis_section_v3(migrations: dict, product_details: dict, date_info: dict, trend_data: dict) -> html.Div:
    """
    V5.3：创建象限迁移分析区域（桑基图 + 可点击统计表）
    """
    try:
        if not migrations:
            return html.Div("暂无迁移数据", className="text-muted text-center p-3")
        
        # 统计迁移数量
        migration_counts = {k: len(v) for k, v in migrations.items()}
        total_products = trend_data.get('total_products', sum(migration_counts.values()))
        changed_count = sum(count for (f, t), count in migration_counts.items() if f != t)
        
        # ===== 桑基图 =====
        sankey_chart = create_migration_sankey_v3(migrations, date_info)
        
        # ===== 可点击的迁移统计表 =====
        migration_rows = []
        for (from_q, to_q), products in sorted(migrations.items(), key=lambda x: -len(x[1])):
            count = len(products)
            # 判断趋势类型
            quadrant_priority = {'🌟 明星商品': 1, '💎 潜力商品': 2, '⚡ 引流商品': 3, '🐌 问题商品': 4}
            from_p = quadrant_priority.get(from_q, 5)
            to_p = quadrant_priority.get(to_q, 5)
            
            if from_q == to_q:
                trend = "➡️ 稳定"
                trend_color = "secondary"
            elif from_p < to_p:
                trend = "📉 恶化"
                trend_color = "danger"
            else:
                trend = "📈 改善"
                trend_color = "success"
            
            pct = count / total_products * 100 if total_products > 0 else 0
            
            migration_rows.append({
                'from': from_q,
                'to': to_q,
                'trend': trend,
                'trend_color': trend_color,
                'count': count,
                'pct': pct,
                'key': f"{from_q}→{to_q}"
            })
        
        # 构建统计表
        stats_table_rows = []
        for row in migration_rows:
            stats_table_rows.append(
                html.Tr([
                    html.Td(row['from'][:6], style={'fontSize': '12px'}),
                    html.Td("→", className="text-center"),
                    html.Td(row['to'][:6], style={'fontSize': '12px'}),
                    html.Td(dbc.Badge(row['trend'], color=row['trend_color'], className=""), style={'fontSize': '11px'}),
                    html.Td(f"{row['count']}个", style={'fontSize': '12px', 'fontWeight': 'bold'}),
                    html.Td(f"({row['pct']:.0f}%)", style={'fontSize': '11px'}, className="text-muted"),
                    html.Td(
                        dbc.Button("详情", 
                                  id={'type': 'migration-detail-btn', 'from': row['from'], 'to': row['to']},
                                  color="link", size="sm", className="p-0", style={'fontSize': '11px'})
                    )
                ], style={'cursor': 'pointer'})
            )
        
        stats_table = html.Table([
            html.Thead([
                html.Tr([
                    html.Th("期初", style={'fontSize': '11px', 'width': '18%'}),
                    html.Th("", style={'width': '5%'}),
                    html.Th("期末", style={'fontSize': '11px', 'width': '18%'}),
                    html.Th("趋势", style={'fontSize': '11px', 'width': '15%'}),
                    html.Th("数量", style={'fontSize': '11px', 'width': '15%'}),
                    html.Th("占比", style={'fontSize': '11px', 'width': '12%'}),
                    html.Th("", style={'width': '12%'})
                ], className="table-light")
            ]),
            html.Tbody(stats_table_rows)
        ], className="table table-sm table-hover mb-0", style={'fontSize': '12px'})
        
        return html.Div([
            dbc.Row([
                # 左侧：桑基图
                dbc.Col([
                    html.Div([
                        sankey_chart
                    ], style={'height': '320px'})
                ], md=6, className="pe-2"),
                # 右侧：统计表
                dbc.Col([
                    html.Div([
                        html.H6([
                            "📊 迁移统计 ",
                            dbc.Badge(f"{changed_count}个变化", color="warning", className="ms-1")
                        ], className="mb-2"),
                        html.Small(f"共{total_products}个商品参与分析", className="text-muted d-block mb-2"),
                        html.Div([
                            stats_table
                        ], style={'maxHeight': '280px', 'overflowY': 'auto'})
                    ])
                ], md=6, className="ps-2")
            ], className="g-0")
        ])
        
    except Exception as e:
        print(f"❌ [V5.3迁移分析] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"生成失败: {e}", className="text-danger")


def create_migration_sankey_v3(migrations: dict, date_info: dict) -> html.Div:
    """
    V5.3：创建象限迁移桑基图
    """
    try:
        migration_counts = {k: len(v) for k, v in migrations.items()}
        
        if not migration_counts:
            return html.Div("暂无迁移数据", className="text-muted text-center p-4")
        
        # 构建桑基图数据
        nodes = []
        links = []
        node_set = set()
        
        quadrant_map = {
            '🌟 明星商品': {'short': '明星', 'color': '#52c41a'},
            '💎 潜力商品': {'short': '潜力', 'color': '#722ed1'},
            '⚡ 引流商品': {'short': '引流', 'color': '#1890ff'},
            '🐌 问题商品': {'short': '问题', 'color': '#f5222d'}
        }
        
        for (from_q, to_q), count in migration_counts.items():
            if count > 0:
                from_info = quadrant_map.get(from_q, {'short': from_q[:2], 'color': '#999'})
                to_info = quadrant_map.get(to_q, {'short': to_q[:2], 'color': '#999'})
                
                source_node = f"期初({date_info['first_range'][:5]})\n{from_info['short']}"
                target_node = f"期末({date_info['last_range'][:5]})\n{to_info['short']}"
                
                if source_node not in node_set:
                    nodes.append({'name': source_node, 'itemStyle': {'color': from_info['color']}})
                    node_set.add(source_node)
                
                if target_node not in node_set:
                    nodes.append({'name': target_node, 'itemStyle': {'color': to_info['color']}})
                    node_set.add(target_node)
                
                links.append({
                    'source': source_node,
                    'target': target_node,
                    'value': count,
                    'lineStyle': {'color': from_info['color'], 'opacity': 0.4}
                })
        
        option = {
            'tooltip': {'trigger': 'item'},
            'series': [{
                'type': 'sankey',
                'data': nodes,
                'links': links,
                'nodeWidth': 25,
                'nodeGap': 12,
                'orient': 'horizontal',
                'label': {'fontSize': 10, 'color': '#333'},
                'lineStyle': {'color': 'source', 'curveness': 0.5},
                'emphasis': {'focus': 'adjacency'}
            }]
        }
        
        chart_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        </head>
        <body style="margin:0;padding:0;">
            <div id="sankey-chart" style="width: 100%; height: 300px;"></div>
            <script>
                var chartDom = document.getElementById('sankey-chart');
                var myChart = echarts.init(chartDom);
                var option = {json.dumps(option, ensure_ascii=False)};
                myChart.setOption(option);
                window.addEventListener('resize', function() {{ myChart.resize(); }});
            </script>
        </body>
        </html>
        '''
        
        return html.Iframe(srcDoc=chart_html, style={'width': '100%', 'height': '310px', 'border': 'none'})
        
    except Exception as e:
        print(f"❌ [V5.3桑基图] 错误: {e}")
        return html.Div(f"图表生成失败: {e}", className="text-danger")


def create_quadrant_trend_line_chart(trend_data: dict, quadrant_data: dict = None) -> html.Div:
    """
    创建四象限商品数量变化趋势的多折线图
    
    Parameters:
    -----------
    trend_data : dict - 趋势数据（从calculate_time_period_quadrants_v2返回）
    quadrant_data : dict - {商品名: [周期1象限, 周期2象限, ...]} 格式的数据
    """
    try:
        periods = trend_data['periods']
        period_label = trend_data['period_label']
        
        # 如果没有传入quadrant_data，尝试从trend_data构建
        if quadrant_data is None:
            period_product_data = trend_data.get('period_product_data', {})
            all_products = set()
            for p_data in period_product_data.values():
                all_products.update(p_data.keys())
            
            quadrant_data = {}
            for product in all_products:
                quadrant_list = []
                for p in periods:
                    p_products = period_product_data.get(p, {})
                    if product in p_products:
                        quadrant_list.append(p_products[product].get('象限', '无数据'))
                    else:
                        quadrant_list.append('无数据')
                quadrant_data[product] = quadrant_list
        
        if len(periods) < 2:
            return html.Div("需要至少2个周期的数据", className="text-muted text-center p-3")
        
        # 统计每个周期各象限的商品数量
        quadrant_names = ['🌟 明星商品', '💎 潜力商品', '⚡ 引流商品', '🐌 问题商品']
        period_counts = {q: [] for q in quadrant_names}
        
        for i, period in enumerate(periods):
            # 统计该周期各象限商品数
            counts = {q: 0 for q in quadrant_names}
            for product, quadrant_list in quadrant_data.items():
                if i < len(quadrant_list) and quadrant_list[i] in counts:
                    counts[quadrant_list[i]] += 1
            
            for q in quadrant_names:
                period_counts[q].append(counts[q])
        
        # 格式化X轴标签
        x_labels = []
        for p in periods:
            if period_label == '日':
                try:
                    x_labels.append(pd.to_datetime(p).strftime('%m-%d'))
                except:
                    x_labels.append(str(p)[-5:])
            elif period_label == '周':
                x_labels.append(f"第{len(x_labels)+1}周")
            else:
                x_labels.append(str(p)[-5:])
        
        # ECharts配置
        option = {
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {'type': 'cross'}
            },
            'legend': {
                'data': ['明星', '潜力', '引流', '问题'],
                'top': '5%',
                'textStyle': {'fontSize': 11}
            },
            'grid': {
                'left': '3%', 'right': '4%', 'bottom': '10%', 'top': '18%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'data': x_labels,
                'axisLabel': {'fontSize': 10, 'rotate': 30 if len(x_labels) > 7 else 0}
            },
            'yAxis': {
                'type': 'value',
                'name': '商品数',
                'axisLabel': {'fontSize': 10}
            },
            'series': [
                {
                    'name': '明星',
                    'type': 'line',
                    'data': period_counts['🌟 明星商品'],
                    'itemStyle': {'color': '#52c41a'},
                    'lineStyle': {'width': 2},
                    'symbol': 'circle',
                    'symbolSize': 6
                },
                {
                    'name': '潜力',
                    'type': 'line',
                    'data': period_counts['💎 潜力商品'],
                    'itemStyle': {'color': '#722ed1'},
                    'lineStyle': {'width': 2},
                    'symbol': 'diamond',
                    'symbolSize': 6
                },
                {
                    'name': '引流',
                    'type': 'line',
                    'data': period_counts['⚡ 引流商品'],
                    'itemStyle': {'color': '#1890ff'},
                    'lineStyle': {'width': 2},
                    'symbol': 'triangle',
                    'symbolSize': 6
                },
                {
                    'name': '问题',
                    'type': 'line',
                    'data': period_counts['🐌 问题商品'],
                    'itemStyle': {'color': '#f5222d'},
                    'lineStyle': {'width': 2, 'type': 'dashed'},
                    'symbol': 'rect',
                    'symbolSize': 6
                }
            ]
        }
        
        chart_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        </head>
        <body style="margin:0;padding:0;">
            <div id="trend-chart" style="width: 100%; height: 280px;"></div>
            <script>
                var chartDom = document.getElementById('trend-chart');
                var myChart = echarts.init(chartDom);
                var option = {json.dumps(option, ensure_ascii=False)};
                myChart.setOption(option);
                window.addEventListener('resize', function() {{ myChart.resize(); }});
            </script>
        </body>
        </html>
        '''
        
        return html.Iframe(srcDoc=chart_html, style={'width': '100%', 'height': '300px', 'border': 'none'})
        
    except Exception as e:
        print(f"❌ [趋势折线图] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"图表生成失败: {e}", className="text-danger")


def create_migration_analysis_section(quadrant_data: dict, periods: list, period_label: str, trend_data: dict) -> html.Div:
    """
    创建象限迁移分析区域（桑基图 + 可点击统计表）
    """
    try:
        if len(periods) < 2:
            return html.Div("需要至少2个周期的数据", className="text-muted text-center p-3")
        
        # 统计迁移路径
        migrations = {}
        migration_products = {}  # 存储每个迁移路径的商品列表
        
        for product, quadrant_list in quadrant_data.items():
            valid_quadrants = [q for q in quadrant_list if q != '无数据']
            if len(valid_quadrants) >= 2:
                from_q = valid_quadrants[0]
                to_q = valid_quadrants[-1]
                key = (from_q, to_q)
                migrations[key] = migrations.get(key, 0) + 1
                
                if key not in migration_products:
                    migration_products[key] = []
                migration_products[key].append(product)
        
        if not migrations:
            return html.Div("暂无足够数据生成迁移分析", className="text-muted text-center p-3")
        
        total_products = sum(migrations.values())
        changed_count = sum(count for (f, t), count in migrations.items() if f != t)
        
        # ===== 桑基图（使用V5.2版本）=====
        # 构建migrations字典格式 {(from_q, to_q): [商品列表]}
        migrations_with_products = migration_products
        sankey_chart = create_quadrant_migration_sankey_v2(migrations_with_products, periods, period_label)
        
        # ===== 可点击的迁移统计表 =====
        migration_rows = []
        for (from_q, to_q), count in sorted(migrations.items(), key=lambda x: -x[1]):
            # 判断趋势类型
            quadrant_priority = {'🌟 明星商品': 1, '💎 潜力商品': 2, '⚡ 引流商品': 3, '🐌 问题商品': 4}
            from_p = quadrant_priority.get(from_q, 5)
            to_p = quadrant_priority.get(to_q, 5)
            
            if from_q == to_q:
                trend = "➡️ 稳定"
                trend_color = "secondary"
            elif from_p < to_p:
                trend = "📉 恶化"
                trend_color = "danger"
            else:
                trend = "📈 改善"
                trend_color = "success"
            
            pct = count / total_products * 100 if total_products > 0 else 0
            
            migration_rows.append({
                'from': from_q,
                'to': to_q,
                'trend': trend,
                'trend_color': trend_color,
                'count': count,
                'pct': pct,
                'key': f"{from_q}→{to_q}"
            })
        
        # 构建可点击的统计表
        stats_table_rows = []
        for row in migration_rows:
            stats_table_rows.append(
                html.Tr([
                    html.Td(row['from'][:6], style={'fontSize': '12px'}),
                    html.Td("→", className="text-center"),
                    html.Td(row['to'][:6], style={'fontSize': '12px'}),
                    html.Td(dbc.Badge(row['trend'], color=row['trend_color'], className=""), style={'fontSize': '11px'}),
                    html.Td(f"{row['count']}个", style={'fontSize': '12px', 'fontWeight': 'bold'}),
                    html.Td(f"({row['pct']:.0f}%)", style={'fontSize': '11px'}, className="text-muted"),
                    html.Td(
                        dbc.Button("详情", 
                                  id={'type': 'migration-detail-btn', 'from': row['from'], 'to': row['to']},
                                  color="link", size="sm", className="p-0", style={'fontSize': '11px'})
                    )
                ], id={'type': 'migration-row', 'key': row['key']}, 
                   className="migration-row",
                   style={'cursor': 'pointer'})
            )
        
        stats_table = html.Table([
            html.Thead([
                html.Tr([
                    html.Th("起始", style={'fontSize': '11px', 'width': '18%'}),
                    html.Th("", style={'width': '5%'}),
                    html.Th("当前", style={'fontSize': '11px', 'width': '18%'}),
                    html.Th("趋势", style={'fontSize': '11px', 'width': '15%'}),
                    html.Th("数量", style={'fontSize': '11px', 'width': '15%'}),
                    html.Th("占比", style={'fontSize': '11px', 'width': '12%'}),
                    html.Th("", style={'width': '12%'})
                ], className="table-light")
            ]),
            html.Tbody(stats_table_rows)
        ], className="table table-sm table-hover mb-0", style={'fontSize': '12px'})
        
        return html.Div([
            dbc.Row([
                # 左侧：桑基图
                dbc.Col([
                    html.Div([
                        sankey_chart
                    ], style={'height': '320px'})
                ], md=6, className="pe-2"),
                # 右侧：统计表
                dbc.Col([
                    html.Div([
                        html.H6([
                            "📊 迁移统计 ",
                            dbc.Badge(f"{changed_count}个变化", color="warning", className="ms-1")
                        ], className="mb-2"),
                        html.Small(f"共{total_products}个商品参与分析", className="text-muted d-block mb-2"),
                        html.Div([
                            stats_table
                        ], style={'maxHeight': '280px', 'overflowY': 'auto'})
                    ])
                ], md=6, className="ps-2")
            ], className="g-0")
        ])
        
    except Exception as e:
        print(f"❌ [迁移分析区域] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"生成失败: {e}", className="text-danger")


def create_migration_detail_table_v2(df: pd.DataFrame, products: list, from_quadrant: str, to_quadrant: str, trend_data: dict) -> html.Div:
    """
    创建迁移详情表格 V5.2
    
    显示从某象限迁移到另一象限的商品详情，包括智能原因诊断
    """
    try:
        if not products:
            return html.Div("无数据", className="text-muted")
        
        periods = trend_data['periods']
        
        # 为每个商品计算详情
        detail_rows = []
        
        for product in products[:50]:  # 限制最多显示50个
            # 获取商品基本信息
            product_df = df[df['商品名称'] == product]
            if product_df.empty:
                continue
            
            # 获取分类
            category = product_df['一级分类名'].iloc[0] if '一级分类名' in product_df.columns else '-'
            
            # 计算期初和期末的指标
            # 期初数据（第一个周期）
            first_period = periods[0]
            last_period = periods[-1]
            
            # 根据周期类型获取数据
            df_temp = df.copy()
            df_temp['日期'] = pd.to_datetime(df_temp['日期'], errors='coerce')
            
            if '周' in trend_data['period_label']:
                df_temp['周期'] = df_temp['日期'].dt.to_period('W-MON').astype(str)
            elif '日' in trend_data['period_label']:
                df_temp['周期'] = df_temp['日期'].dt.strftime('%Y-%m-%d')
            else:
                df_temp['周期'] = df_temp['日期'].dt.to_period('M').astype(str)
            
            product_first = df_temp[(df_temp['商品名称'] == product) & (df_temp['周期'] == first_period)]
            product_last = df_temp[(df_temp['商品名称'] == product) & (df_temp['周期'] == last_period)]
            
            # 计算期初期末指标
            def calc_metrics(period_df):
                if period_df.empty:
                    return {'销量': 0, '销售额': 0, '利润额': 0, '利润率': 0, '售价': 0, '库存': 0}
                
                sales_col = '月售' if '月售' in period_df.columns else '销量'
                sales = period_df[sales_col].sum() if sales_col in period_df.columns else 0
                
                revenue_col = '预计订单收入' if '预计订单收入' in period_df.columns else '销售额'
                revenue = period_df[revenue_col].sum() if revenue_col in period_df.columns else 0
                
                profit = period_df['利润额'].sum() if '利润额' in period_df.columns else 0
                profit_rate = (profit / revenue * 100) if revenue > 0 else 0
                
                price = period_df['实收价格'].mean() if '实收价格' in period_df.columns else 0
                
                stock_col = '库存' if '库存' in period_df.columns else '剩余库存'
                stock = period_df[stock_col].iloc[-1] if stock_col in period_df.columns else 0
                
                return {'销量': sales, '销售额': revenue, '利润额': profit, '利润率': profit_rate, '售价': price, '库存': stock}
            
            first_metrics = calc_metrics(product_first)
            last_metrics = calc_metrics(product_last)
            
            # 智能诊断变化原因
            reasons = diagnose_migration_reason_v2(first_metrics, last_metrics, from_quadrant, to_quadrant)
            
            detail_rows.append({
                '商品名称': product[:20] + '...' if len(product) > 20 else product,
                '分类': category[:6] if len(str(category)) > 6 else category,
                '期初象限': from_quadrant[:4],
                '期末象限': to_quadrant[:4],
                '期初利润率': f"{first_metrics['利润率']:.1f}%",
                '期末利润率': f"{last_metrics['利润率']:.1f}%",
                '期初销量': int(first_metrics['销量']),
                '期末销量': int(last_metrics['销量']),
                '变化原因': reasons
            })
        
        if not detail_rows:
            return html.Div("无详细数据", className="text-muted")
        
        detail_df = pd.DataFrame(detail_rows)
        
        return html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        dbc.Badge(f"{from_quadrant} → {to_quadrant}", color="primary", className="me-2"),
                        html.Small(f"共 {len(products)} 个商品", className="text-muted")
                    ])
                ], className="py-2 bg-light"),
                dbc.CardBody([
                    dash_table.DataTable(
                        data=detail_df.to_dict('records'),
                        columns=[{'name': c, 'id': c} for c in detail_df.columns],
                        page_size=10,
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'fontSize': '12px', 'padding': '6px 8px'},
                        style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa', 'fontSize': '11px'},
                        style_data_conditional=[
                            {'if': {'filter_query': '{变化原因} contains "售罄"'}, 'backgroundColor': '#fff1f0'},
                            {'if': {'filter_query': '{变化原因} contains "降价"'}, 'backgroundColor': '#fffbe6'},
                            {'if': {'filter_query': '{变化原因} contains "滞销"'}, 'backgroundColor': '#f6ffed'},
                            {'if': {'filter_query': '{变化原因} contains "改善"'}, 'backgroundColor': '#e6f7ff'},
                        ]
                    )
                ], className="p-2")
            ])
        ])
        
    except Exception as e:
        print(f"❌ [迁移详情表格] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"生成失败: {e}", className="text-danger")


def create_migration_detail_table_v3(df: pd.DataFrame, products: list, from_quadrant: str, to_quadrant: str, trend_data: dict) -> html.Div:
    """
    创建迁移详情表格 V5.3 - 含店内码
    
    V5.3更新：
    - 使用前后对半分对比数据
    - 新增店内码列
    - 展示期初期末日期范围
    - 智能诊断变化原因
    """
    try:
        if not products:
            return html.Div("无数据", className="text-muted")
        
        product_details = trend_data.get('product_details', {})
        date_info = trend_data.get('date_info', {})
        
        # 为每个商品构建详情行
        detail_rows = []
        
        for product in products[:50]:  # 限制最多显示50个
            details = product_details.get(product, {})
            if not details:
                continue
            
            # 获取店内码
            store_code = details.get('店内码', '-')
            if not store_code or pd.isna(store_code):
                store_code = '-'
            
            # 获取分类
            category = details.get('分类', '-')
            if len(str(category)) > 6:
                category = str(category)[:6]
            
            # 获取期初期末指标
            first_metrics = {
                '利润率': details.get('期初利润率', 0),
                '销量': details.get('期初销量', 0),
                '销售额': details.get('期初销额', 0),
                '售价': 0,
                '库存': 0
            }
            last_metrics = {
                '利润率': details.get('期末利润率', 0),
                '销量': details.get('期末销量', 0),
                '销售额': details.get('期末销额', 0),
                '售价': 0,
                '库存': 0
            }
            
            # 智能诊断变化原因
            reasons = diagnose_migration_reason_v2(first_metrics, last_metrics, from_quadrant, to_quadrant)
            
            detail_rows.append({
                '店内码': str(store_code)[:12] if len(str(store_code)) > 12 else str(store_code),
                '商品名称': product[:18] + '...' if len(product) > 18 else product,
                '分类': category,
                '期初象限': from_quadrant[:4],
                '期末象限': to_quadrant[:4],
                '期初利润率': f"{first_metrics['利润率']:.1f}%",
                '期末利润率': f"{last_metrics['利润率']:.1f}%",
                '期初销量': int(first_metrics['销量']),
                '期末销量': int(last_metrics['销量']),
                '变化原因': reasons
            })
        
        if not detail_rows:
            return html.Div("无详细数据", className="text-muted")
        
        detail_df = pd.DataFrame(detail_rows)
        
        # 构建表头日期信息
        first_start = date_info.get('first_start', '')
        first_end = date_info.get('first_end', '')
        last_start = date_info.get('last_start', '')
        last_end = date_info.get('last_end', '')
        
        return html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        dbc.Badge(f"{from_quadrant} → {to_quadrant}", color="primary", className="me-2"),
                        html.Small(f"共 {len(products)} 个商品", className="text-muted me-2"),
                        html.Small(f"| 期初: {first_start}~{first_end} → 期末: {last_start}~{last_end}", 
                                  className="text-info", style={'fontSize': '11px'})
                    ])
                ], className="py-2 bg-light"),
                dbc.CardBody([
                    dash_table.DataTable(
                        data=detail_df.to_dict('records'),
                        columns=[{'name': c, 'id': c} for c in detail_df.columns],
                        page_size=10,
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'fontSize': '11px', 'padding': '5px 6px'},
                        style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa', 'fontSize': '10px'},
                        style_cell_conditional=[
                            {'if': {'column_id': '店内码'}, 'width': '80px', 'fontFamily': 'monospace'},
                            {'if': {'column_id': '商品名称'}, 'width': '130px'},
                            {'if': {'column_id': '分类'}, 'width': '60px'},
                            {'if': {'column_id': '期初象限'}, 'width': '55px'},
                            {'if': {'column_id': '期末象限'}, 'width': '55px'},
                        ],
                        style_data_conditional=[
                            {'if': {'filter_query': '{变化原因} contains "售罄"'}, 'backgroundColor': '#fff1f0'},
                            {'if': {'filter_query': '{变化原因} contains "降价"'}, 'backgroundColor': '#fffbe6'},
                            {'if': {'filter_query': '{变化原因} contains "滞销"'}, 'backgroundColor': '#f6ffed'},
                            {'if': {'filter_query': '{变化原因} contains "改善"'}, 'backgroundColor': '#e6f7ff'},
                        ]
                    )
                ], className="p-2")
            ])
        ])
        
    except Exception as e:
        print(f"❌ [迁移详情表格V3] 错误: {e}")
        import traceback
        traceback.print_exc()
        return html.Div(f"生成失败: {e}", className="text-danger")


def diagnose_migration_reason_v2(first_metrics: dict, last_metrics: dict, from_q: str, to_q: str) -> str:
    """
    智能诊断商品象限迁移原因 V5.2
    
    根据期初期末指标变化，判断迁移原因
    阈值：利润率±5%，动销变化根据销量判断
    """
    reasons = []
    
    # 利润率变化
    profit_change = last_metrics['利润率'] - first_metrics['利润率']
    
    # 销量变化
    first_sales = first_metrics['销量']
    last_sales = last_metrics['销量']
    
    # 库存状态
    last_stock = last_metrics['库存']
    
    # 售价变化
    price_change = last_metrics['售价'] - first_metrics['售价'] if first_metrics['售价'] > 0 else 0
    price_change_pct = (price_change / first_metrics['售价'] * 100) if first_metrics['售价'] > 0 else 0
    
    # 1. 判断利润率变化原因
    if profit_change < -5:  # 利润率下降超过5%
        if price_change_pct < -5:
            reasons.append("📉降价促销")
        else:
            reasons.append("📉利润下降")
    elif profit_change > 5:  # 利润率上升超过5%
        if price_change_pct > 5:
            reasons.append("📈提价成功")
        else:
            reasons.append("📈利润改善")
    
    # 2. 判断销量变化原因
    if first_sales > 0:
        sales_change_pct = (last_sales - first_sales) / first_sales * 100
    else:
        sales_change_pct = 100 if last_sales > 0 else 0
    
    if sales_change_pct < -50:  # 销量下降超过50%
        if last_stock == 0:
            reasons.append("🚨售罄缺货")
        elif last_sales < 5:
            reasons.append("📦滞销")
        else:
            reasons.append("📉销量下滑")
    elif sales_change_pct > 50:  # 销量上升超过50%
        reasons.append("🔥销量增长")
    
    # 3. 综合判断
    if not reasons:
        # 根据象限变化给出默认原因
        quadrant_priority = {'🌟 明星商品': 1, '💎 潜力商品': 2, '⚡ 引流商品': 3, '🐌 问题商品': 4}
        from_p = quadrant_priority.get(from_q, 5)
        to_p = quadrant_priority.get(to_q, 5)
        
        if from_p < to_p:
            reasons.append("➡️正常波动(恶化)")
        elif from_p > to_p:
            reasons.append("✅正常波动(改善)")
        else:
            reasons.append("➡️稳定")
    
    return " + ".join(reasons[:2])  # 最多显示2个原因


def create_product_health_content(product_scores: pd.DataFrame, category_filter: str = None, selected_category: str = None, raw_df: pd.DataFrame = None, days_range: int = 15) -> html.Div:
    """
    创建商品健康分析的动态内容 V5.3 - 四象限版本（含趋势分析）
    
    V5.3更新：
    - 趋势分析改为15天/30天对比范围（前后对半分对比）
    - 增加days_range参数用于对比范围切换
    - 去掉日/周/月周期概念，改为更简洁的对比范围
    
    Args:
        product_scores: 全量商品评分数据
        category_filter: 当前选中的品类（用于筛选数据）
        selected_category: 当前选中的品类名称
        raw_df: 原始订单数据（用于趋势分析）
        days_range: 对比范围天数 (15或30)
    
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
    
    # V7.4：删除评分等级统计（评分体系已删除）
    
    # V5.0: 四象限统计（改用新字段名）
    quadrant_col = '四象限分类' if '四象限分类' in filtered_scores.columns else '八象限分类'
    quadrant_counts = filtered_scores[quadrant_col].value_counts().to_dict()
    
    # ===== V7.4：删除评分等级UI（评分体系已删除）=====
    # 说明：评分等级按钮已删除，用户直接使用六象限分类筛选
    score_level_items = []  # 保留空列表，避免UI报错
    
    # ===== V7.4：删除品类平均分图（评分体系已删除）=====
    # 说明：品类平均分图已删除，暂时不显示任何图表
    # TODO: 后续可以改为显示各品类的明星商品数量排行
    category_bar_option = None
    
    # ===== V6.2 四象限+策略引流进度条列表 =====
    quadrant_colors = {
        '🌟 明星商品': '#52c41a',   # 高利润+高动销+高单品价值 - 绿色
        '🔥 畅销商品': '#ff9800',   # 低价+高销+正利润(刚需基础品) - 橙黄色
        '💎 潜力商品': '#722ed1',   # 高利润+低动销 - 紫色
        '🎯 策略引流': '#fa8c16',   # 极端引流品 - 橙色
        '⚡ 自然引流': '#1890ff',   # 低利润+高动销 - 蓝色
        '🐌 低效商品': '#ff4d4f',   # 低利润+低动销 - 红色
    }
    
    # V7.0 六象限描述（策略引流+明星+畅销+潜力+自然引流+低效）
    quadrant_descriptions = [
        ('🌟 明星商品', '高利润+高动销+单品价值≥0.5元', 'success', '核心盈利品，重点维护'),
        ('🔥 畅销商品', '低价+高销+正利润', 'warning', '刚需基础品，保证供应'),
        ('💎 潜力商品', '高利润+低动销', 'primary', '提高曝光，营销推广'),
        ('🎯 策略引流', '0.01元秒杀/亏损50%以上/低价不到成本一半', 'dark', '主动策略，监控效果'),
        ('⚡ 自然引流', '低利润+高动销(动销指数>中位数+≥70分位数)', 'info', '市场验证，可适当提价'),
        ('🐌 低效商品', '低利润+低动销(动态门槛)', 'danger', '优化或淘汰'),
    ]
    
    total_count = sum(quadrant_counts.values()) if quadrant_counts else 1
    quadrant_progress_items = []
    for name, desc, btn_color, tip in quadrant_descriptions:
        count = quadrant_counts.get(name, 0)
        pct = count / total_count * 100 if total_count > 0 else 0
        color = quadrant_colors.get(name, '#8c8c8c')
        
        # V3.0联动：为每个象限添加"调价优化"按钮
        quadrant_progress_items.append(
            html.Div([
                dbc.Button([
                    dbc.Row([
                        dbc.Col([
                            html.Span(name, className="fw-bold", style={'fontSize': '13px'}),
                            html.Br(),
                            html.Small(desc, className="text-muted", style={'fontSize': '10px'})
                        ], width=4),
                        dbc.Col([
                            html.Div([
                                html.Div(style={
                                    'width': f'{pct}%', 
                                    'height': '18px', 
                                    'backgroundColor': color, 
                                    'borderRadius': '4px',
                                    'transition': 'width 0.3s'
                                })
                            ], style={
                                'height': '18px', 
                                'backgroundColor': '#f0f0f0', 
                                'borderRadius': '4px',
                                'flex': '1'
                            })
                        ], width=3, className="d-flex align-items-center"),
                        dbc.Col([
                            html.Span(f"{count}个", className="fw-bold", style={'fontSize': '14px'}),
                            html.Small(f" ({pct:.0f}%)", className="text-muted", style={'fontSize': '11px'})
                        ], width=2, className="text-end"),
                        dbc.Col([
                            html.Small(tip, className="text-muted fst-italic", style={'fontSize': '10px'})
                        ], width=2),
                        dbc.Col([
                            dbc.Button([
                                html.I(className="fas fa-calculator me-1"),
                                "调价"
                            ],
                            id={'type': 'quadrant-to-pricing', 'quadrant': name},
                            color='primary',
                            size="sm",
                            outline=True,
                            disabled=(count == 0),  # 无商品时禁用
                            style={'fontSize': '11px', 'padding': '2px 8px'}
                            ) if count > 0 else html.Span()
                        ], width=1, className="text-end"),
                    ], className="w-100 align-items-center", style={'minHeight': '32px'})
                ],
                id={'type': 'quadrant-filter-btn', 'index': name},
                color='light',
                size="sm",
                className="mb-2 w-100 text-start border",
                style={'borderLeftWidth': '5px', 'borderLeftColor': color}
                )
            ], className="mb-2")
        )
    
    # ===== 特殊标记统计（亏损/低频）=====
    loss_count = quadrant_counts.get('🚨 亏损', 0)  # 统计亏损标记数
    low_freq_count = quadrant_counts.get('📦 低频', 0)  # 统计低频标记数
    
    # 从scores中统计特殊标记
    if '特殊标记' in filtered_scores.columns:
        loss_count = len(filtered_scores[filtered_scores['特殊标记'].str.contains('🚨', na=False)])
        low_freq_count = len(filtered_scores[filtered_scores['特殊标记'].str.contains('📦', na=False)])
    
    # ===== 构建Tab内容 =====
    filter_hint = f"品类: {category_filter}" if category_filter else "全部商品"
    
    # ===== 帮助弹窗内容 =====
    help_modal = dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("📖 门店诊断操作指南"),
        ], close_button=True),
        dbc.ModalBody([
            # 使用Accordion折叠面板
            dbc.Accordion([
                # 第零部分：今日必做整体说明
                dbc.AccordionItem([
                    html.Div([
                        html.P("「今日必做」帮助运营快速诊断门店，发现问题并指导优化。", className="mb-3 fw-bold"),
                        html.Table([
                            html.Thead(html.Tr([
                                html.Th("模块", style={'width': '140px'}),
                                html.Th("解决什么问题"),
                                html.Th("使用场景"),
                            ])),
                            html.Tbody([
                                html.Tr([
                                    html.Td("📊 昨日经营诊断", className="fw-bold"),
                                    html.Td("快速定位门店异常问题，并快速处理"),
                                    html.Td("运营核心，每日对所有异常门店进行诊断，降低门店异常经营情况"),
                                ]),
                                html.Tr([
                                    html.Td("🎯 商品六象限", className="fw-bold"),
                                    html.Td("商品结构健不健康？哪些该优化？"),
                                    html.Td("每周分析，优化商品结构"),
                                ]),
                                html.Tr([
                                    html.Td("🔧 智能调价计算器", className="fw-bold"),
                                    html.Td("这个商品该卖多少钱？"),
                                    html.Td("调价前用它算一下，避免亏损"),
                                ]),
                            ])
                        ], className="table table-bordered table-sm"),
                    ])
                ], title="📌 今日必做是干嘛的？", item_id="help-0"),
                
                # 第一部分：昨日经营诊断
                dbc.AccordionItem([
                    html.Div([
                        html.P("分析昨日订单数据，自动发现经营问题，按紧急程度分层提醒。", className="mb-3"),
                        
                        html.H6("🔴 紧急处理（今日必须完成）", className="text-danger mb-2"),
                        html.Table([
                            html.Thead(html.Tr([
                                html.Th("问题类型", style={'width': '100px'}),
                                html.Th("说明"),
                                html.Th("处理方式"),
                            ])),
                            html.Tbody([
                                html.Tr([
                                    html.Td("💸 溢出订单"),
                                    html.Td("利润率<0%的订单，卖一单亏一单"),
                                    html.Td("检查定价、成本，考虑调价或下架"),
                                ]),
                                html.Tr([
                                    html.Td("🚚 配送超时"),
                                    html.Td("配送时间过长，影响用户体验"),
                                    html.Td("定位溢价收货地址，分时段分距离调整起送，剔除异常地址重新画圈"),
                                ]),
                                html.Tr([
                                    html.Td("📦 缺货商品"),
                                    html.Td("有订单但库存不足"),
                                    html.Td("联系商品采购进行补货"),
                                ]),
                            ])
                        ], className="table table-bordered table-sm mb-3"),
                        
                        html.H6("🟡 关注观察（本周内处理）", className="text-warning mb-2"),
                        html.Table([
                            html.Thead(html.Tr([
                                html.Th("问题类型", style={'width': '100px'}),
                                html.Th("说明"),
                                html.Th("处理方式"),
                            ])),
                            html.Tbody([
                                html.Tr([
                                    html.Td("📉 流量下降"),
                                    html.Td("订单量/销售额同比下降"),
                                    html.Td("分品类分商品对标商圈竞对，关注应季品、畅销品的核心竞争力，提高供给能力"),
                                ]),
                                html.Tr([
                                    html.Td("🐢 新品动销慢"),
                                    html.Td("新上架商品销量不达预期"),
                                    html.Td("关注商品是否与当前场景、季节有关，关注新增动销品库存，与商圈竞对比价提高曝光"),
                                ]),
                            ])
                        ], className="table table-bordered table-sm"),
                    ])
                ], title="📊 昨日经营诊断", item_id="help-1"),
                
                # 第二部分：专业术语解释（新手必读）
                dbc.AccordionItem([
                    html.Div([
                        html.P("看不懂六象限中的专业指标？这里有详细解释！", className="mb-3 fw-bold text-primary"),
                        
                        # 指标速查表
                        html.Div([
                            html.H6("📊 指标速查表 - 这些指标用在哪？", className="text-primary mb-2"),
                            html.Table([
                                html.Thead(html.Tr([
                                    html.Th("指标名称", style={'width': '140px'}),
                                    html.Th("用在哪些象限判定中"),
                                ])),
                                html.Tbody([
                                    html.Tr([
                                        html.Td("动销指数", className="fw-bold"),
                                        html.Td("🌟明星 💎潜力 ⚡自然引流 🐌低效"),
                                    ]),
                                    html.Tr([
                                        html.Td("利润率阈值", className="fw-bold"),
                                        html.Td("🌟明星 💎潜力 🔥畅销 ⚡自然引流"),
                                    ]),
                                    html.Tr([
                                        html.Td("高动销门槛", className="fw-bold"),
                                        html.Td("🎯策略引流 ⚡自然引流"),
                                    ]),
                                    html.Tr([
                                        html.Td("-50%阈值", className="fw-bold"),
                                        html.Td("🎯策略引流"),
                                    ]),
                                    html.Tr([
                                        html.Td("单品价值门槛", className="fw-bold"),
                                        html.Td("🌟明星商品"),
                                    ]),
                                    html.Tr([
                                        html.Td("价格阈值", className="fw-bold"),
                                        html.Td("🔥畅销商品"),
                                    ]),
                                    html.Tr([
                                        html.Td("标准化", className="fw-bold"),
                                        html.Td("动销指数的计算方法"),
                                    ]),
                                ])
                            ], className="table table-bordered table-sm mb-3"),
                        ], className="alert alert-light py-2 mb-3"),
                        
                        # 详细解释（嵌套折叠面板）
                        html.H6("📖 详细解释", className="text-primary mb-2"),
                        dbc.Accordion([
                            # 核心判定指标
                            dbc.AccordionItem([
                                html.Div([
                                    # 1. 动销指数
                                    html.Div([
                                        html.H6("1️⃣ 动销指数 - 商品到底卖得好不好？", className="text-primary mb-2"),
                                        html.Div([
                                            html.Strong("📍 用在哪些象限："),
                                            html.Span(" 🌟明星 💎潜力 ⚡自然引流 🐌低效", className="ms-2"),
                                        ], className="alert alert-info py-1 mb-2 small"),
                                        
                                        html.P([
                                            html.Strong("什么是动销指数？"),
                                            html.Br(),
                                            "一个0-1之间的数字，越接近1说明商品越畅销，综合考虑'卖了多少'、'多少人买'"
                                        ], className="mb-2"),
                                        
                                        html.Div([
                                            html.Strong("怎么算出来的？"),
                                            html.Pre(
                                                "动销指数 = 标准化销量×60% + 标准化订单数×40%",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("🔍 关键问题：这个'占比'是品类内比，还是全店比？"),
                                            html.Pre(
                                                "答案：全店比较！\n\n"
                                                "计算范围：\n"
                                                "- 你的商品销量 vs 全店所有商品销量\n"
                                                "- 你的商品订单数 vs 全店所有商品订单数\n\n"
                                                "→ 不是品类内比较，是全店横向PK",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("为什么要全店比较？"),
                                            html.Pre(
                                                "目的：找出全店最畅销的商品\n\n"
                                                "如果品类内比较：\n"
                                                "- 饮料品类：可乐是第1名\n"
                                                "- 生鲜品类：白菜是第1名\n"
                                                "- 零食品类：薯片是第1名\n"
                                                "→ 但无法知道可乐、白菜、薯片谁更畅销\n\n"
                                                "全店比较：\n"
                                                "- 可乐：动销指数0.85（全店第1）\n"
                                                "- 白菜：动销指数0.62（全店第8）\n"
                                                "- 薯片：动销指数0.45（全店第15）\n"
                                                "→ 一目了然：可乐最畅销",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("为什么不直接看销量？"),
                                            html.Pre(
                                                "❌ 只看销量的问题：\n"
                                                "商品A：销量100件，但只有1个客户买（团购）\n"
                                                "商品B：销量50件，有20个客户买（日常复购）\n"
                                                "→ 如果只看销量，A比B好，但实际B更受欢迎\n\n"
                                                "✅ 用动销指数：\n"
                                                "商品A：销量高但订单少 → 动销指数可能只有0.6\n"
                                                "商品B：销量和订单都不错 → 动销指数可能有0.8\n"
                                                "→ 更准确反映商品受欢迎程度",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                    ], className="mb-4"),
                                    
                                    # 2. 利润率阈值
                                    html.Div([
                                        html.H6("2️⃣ 利润率阈值 - 为什么不同品类标准不同？", className="text-primary mb-2"),
                                        html.Div([
                                            html.Strong("📍 用在哪些象限："),
                                            html.Span(" 🌟明星 💎潜力 🔥畅销 ⚡自然引流", className="ms-2"),
                                        ], className="alert alert-info py-1 mb-2 small"),
                                        
                                        html.Div([
                                            html.Strong("🔍 关键区别：动销指数全店比，利润率品类比"),
                                            html.Pre(
                                                "动销指数：全店比较\n"
                                                "→ 目的：找出全店最畅销的商品\n"
                                                "→ 可乐 vs 红酒 vs 白菜，谁卖得最好？\n\n"
                                                "利润率阈值：品类内比较\n"
                                                "→ 目的：评估商品在同类中是否赚钱\n"
                                                "→ 可乐 vs 雪碧 vs 矿泉水，谁更赚钱？",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("一个不公平的故事："),
                                            html.Pre(
                                                "假设全店统一标准：利润率30%才算'高利润'\n\n"
                                                "饮料老板：我的可乐利润率35%，是高利润✅\n"
                                                "生鲜老板：我的蔬菜利润率15%，是低利润❌\n\n"
                                                "生鲜老板不服：\n"
                                                "'蔬菜损耗大、周转快，行业利润率就是10-20%！\n"
                                                " 我15%已经很不错了，为什么算低利润？'\n\n"
                                                "→ 确实不公平！应该'品类内比较'",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("品类内比较："),
                                            html.Pre(
                                                "饮料品类（10个商品）：\n"
                                                "利润率：25%, 28%, 30%, 32%, 35%, 38%, 40%, 42%, 45%, 50%\n"
                                                "中位数：36.5%\n"
                                                "→ 可乐35% < 36.5% → 在饮料品类中算'低利润'\n\n"
                                                "生鲜品类（8个商品）：\n"
                                                "利润率：8%, 10%, 12%, 14%, 15%, 18%, 20%, 25%\n"
                                                "中位数：14.5%\n"
                                                "→ 蔬菜15% > 14.5% → 在生鲜品类中算'高利润'✅\n\n"
                                                "→ 公平了！",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                    ], className="mb-4"),
                                    
                                    # 3. 高动销门槛（V7.2动态门槛）
                                    html.Div([
                                        html.H6("3️⃣ 高动销门槛：动态自适应 - 三重标准", className="text-primary mb-2"),
                                        html.Div([
                                            html.Strong("📍 用在哪些象限："),
                                            html.Span(" 🌟明星商品 💎潜力商品 ⚡自然引流 🐌低效商品", className="ms-2"),
                                            html.Br(),
                                            html.Small("V7.2优化：动态门槛，自适应门店规模", className="text-muted"),
                                        ], className="alert alert-info py-1 mb-2 small"),
                                        
                                        html.Div([
                                            html.Strong("高动销的三重标准（需同时满足）："),
                                            html.Pre(
                                                "1️⃣ 动销指数 > 全店中位数（相对排名前50%）\n"
                                                "2️⃣ 销量 ≥ 全店销量70分位数（动态，约前30%）\n"
                                                "3️⃣ 订单数 ≥ 全店订单数70分位数（动态，约前30%）\n\n"
                                                "→ 既看相对排名，又看绝对销量\n"
                                                "→ 动态门槛自适应门店规模\n"
                                                "→ 保底门槛：销量≥5件，订单≥2单",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("为什么要动态门槛？"),
                                            html.Pre(
                                                "问题：固定门槛（20件+5单）不适合所有门店\n\n"
                                                "大门店（日均1000单）：\n"
                                                "→ 20件太低，80%的商品都满足\n"
                                                "→ 明星商品太多，失去筛选意义\n\n"
                                                "小门店（日均50单）：\n"
                                                "→ 20件太高，只有3.7%的商品满足\n"
                                                "→ 明星商品太少，打击运营信心\n\n"
                                                "动态门槛（70分位数）：\n"
                                                "→ 大门店：门槛自动提高（如30件+8单）\n"
                                                "→ 小门店：门槛自动降低（如4件+3单）\n"
                                                "→ 确保约30%的商品有机会成为'高动销'",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("三重标准的作用："),
                                            html.Pre(
                                                "场景1：只看动销指数的问题\n"
                                                "商品A：销量3件，订单2单，动销指数0.65（排名前50%）\n"
                                                "→ 动销指数高，但实际销量太少\n"
                                                "→ 不应该算'高动销'❌\n\n"
                                                "场景2：只看销量的问题\n"
                                                "商品B：销量50件，订单1单\n"
                                                "→ 某公司一次性团购50件\n"
                                                "→ 不算高动销❌（只是偶然大单）\n\n"
                                                "场景3：真正的高动销\n"
                                                "商品C：销量8件，订单5单，动销指数0.68\n"
                                                "→ 动销指数高（排名前50%）✅\n"
                                                "→ 销量≥70分位数（如4件）✅\n"
                                                "→ 订单≥70分位数（如3单）✅\n"
                                                "→ 这才是真正的高动销！",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("V7.2优化说明："),
                                            html.Pre(
                                                "V7.1问题：\n"
                                                "- 固定门槛（20件+5单）不适合所有门店\n"
                                                "- 小门店明星商品太少（只有3.7%满足）\n\n"
                                                "V7.2优化：\n"
                                                "- 动态门槛：使用70分位数自适应\n"
                                                "- 确保约30%的商品有机会成为'高动销'\n"
                                                "- 保底门槛：销量≥5件，订单≥2单\n"
                                                "→ 既科学又灵活，适合不同规模门店",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                    ], className="mb-4"),
                                    
                                    # 4. 单品价值门槛
                                    html.Div([
                                        html.H6("4️⃣ 单品价值门槛：0.5元/50元 - 防止低价商品虚高", className="text-primary mb-2"),
                                        html.Div([
                                            html.Strong("📍 用在哪些象限："),
                                            html.Span(" 🌟明星商品", className="ms-2"),
                                        ], className="alert alert-info py-1 mb-2 small"),
                                        
                                        html.Div([
                                            html.Strong("一个尴尬的案例："),
                                            html.Pre(
                                                "商品：口香糖\n"
                                                "售价：1元\n"
                                                "成本：0.5元\n"
                                                "利润率：50%（很高！）\n"
                                                "动销指数：0.8（很高！）\n"
                                                "销量：100件\n\n"
                                                "如果只看利润率和动销：\n"
                                                "→ 应该是'明星商品'✅\n\n"
                                                "但实际：\n"
                                                "→ 单品只赚0.5元\n"
                                                "→ 总共才赚50元\n"
                                                "→ 算明星商品？有点勉强...",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("加上价值门槛："),
                                            html.Pre(
                                                "明星商品三重标准：\n"
                                                "1. 利润率 > 品类中位数（效率高）\n"
                                                "2. 动销指数 > 全店中位数（卖得好）\n"
                                                "3. 单品利润≥0.5元 或 总利润≥50元（价值高）\n\n"
                                                "口香糖：\n"
                                                "→ 单品利润0.5元（刚好达标）\n"
                                                "→ 总利润50元（刚好达标）\n"
                                                "→ 勉强算明星商品\n\n"
                                                "红酒礼盒：\n"
                                                "→ 单品利润21.9元（远超标准）\n"
                                                "→ 总利润1752元（远超标准）\n"
                                                "→ 妥妥的明星商品✅",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                    ], className="mb-4"),
                                    
                                    # 5. 畅销商品门槛
                                    html.Div([
                                        html.H6("5️⃣ 畅销商品门槛 - 低价刚需品的标准", className="text-primary mb-2"),
                                        html.Div([
                                            html.Strong("📍 用在哪些象限："),
                                            html.Span(" 🔥畅销刚需", className="ms-2"),
                                        ], className="alert alert-info py-1 mb-2 small"),
                                        
                                        html.Div([
                                            html.Strong("判定条件（需同时满足）："),
                                            html.Pre(
                                                "1️⃣ 低价：实售价 < 全店商品价格中位数\n"
                                                "2️⃣ 高销：销量 ≥ 全店销量70分位数\n"
                                                "3️⃣ 正利润：利润率 ≥ 品类中位数",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("为什么要单独设置畅销商品？"),
                                            html.Pre(
                                                "问题：包子、矿泉水这类商品怎么分类？\n\n"
                                                "包子：\n"
                                                "- 价格：3.5元（低价）\n"
                                                "- 销量：200件/月（很高）\n"
                                                "- 利润率：48%（高于品类中位数）\n\n"
                                                "如果没有畅销商品象限：\n"
                                                "→ 可能被分到'自然引流'（但利润率其实不低）\n"
                                                "→ 或者'明星商品'（但价格太低，不够'明星'）\n\n"
                                                "有了畅销商品象限：\n"
                                                "→ 明确定位：低价刚需基础品\n"
                                                "→ 运营策略：保持稳定供应，维持价格竞争力",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("与其他象限的区别："),
                                            html.Pre(
                                                "🔥 畅销刚需 vs 🌟 明星商品：\n"
                                                "- 畅销：低价+高销+正利润\n"
                                                "- 明星：高利润+高动销+高价值\n"
                                                "→ 畅销更注重'量'，明星更注重'质'\n\n"
                                                "🔥 畅销刚需 vs ⚡ 自然引流：\n"
                                                "- 畅销：利润率 ≥ 品类中位数（有利润）\n"
                                                "- 自然引流：利润率 ≤ 品类中位数（低利润）\n"
                                                "→ 畅销是'赚钱的引流'，自然引流是'不太赚钱的引流'",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                    ], className="mb-4"),
                                    
                                    # 6. 策略引流门槛
                                    html.Div([
                                        html.H6("6️⃣ 策略引流门槛 - 极端价格的识别", className="text-primary mb-2"),
                                        html.Div([
                                            html.Strong("📍 用在哪些象限："),
                                            html.Span(" 🎯策略引流", className="ms-2"),
                                        ], className="alert alert-info py-1 mb-2 small"),
                                        
                                        html.Div([
                                            html.Strong("判定条件（满足任一即可）："),
                                            html.Pre(
                                                "1️⃣ 秒杀/满赠：实售价 ≤ 0.01元 + 销量≥中位数（动态）\n"
                                                "2️⃣ 亏损引流：利润率 < -50% + 销量≥中位数（动态）\n"
                                                "3️⃣ 低价引流：实售价≤2元 且 不到成本一半 + 销量≥中位数（动态）\n"
                                                "4️⃣ 赠品：实售价=0 但有销量（无门槛）\n\n"
                                                "V7.2优化：使用50分位数（中位数）作为销量门槛\n"
                                                "→ 门槛相对较低，确保能识别到有效的引流活动",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("为什么要识别策略引流？"),
                                            html.Pre(
                                                "目的：区分'主动策略'和'自然低价'\n\n"
                                                "策略引流（主动）：\n"
                                                "- 0.01元秒杀可乐（平台活动）\n"
                                                "- 亏损60%卖红酒（清库存）\n"
                                                "→ 这是运营主动决策，需要监控ROI\n\n"
                                                "自然引流（被动）：\n"
                                                "- 2.5元卖矿泉水（市场价）\n"
                                                "- 利润率28%（行业正常水平）\n"
                                                "→ 这是市场竞争结果，不是主动策略\n\n"
                                                "→ 分开管理，策略更清晰",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("为什么要加销量门槛？"),
                                            html.Pre(
                                                "问题：如果不加销量门槛会怎样？\n\n"
                                                "商品A：0.01元秒杀，但只卖了2件\n"
                                                "→ 可能是测试活动，或者活动失败\n"
                                                "→ 不应该算'策略引流'（没有引流效果）\n\n"
                                                "商品B：0.01元秒杀，卖了8件（≥中位数）\n"
                                                "→ 真正的引流活动，有实际效果\n"
                                                "→ 应该算'策略引流'✅\n\n"
                                                "V7.2动态门槛：\n"
                                                "→ 使用50分位数（中位数）作为门槛\n"
                                                "→ 大门店门槛高（如20件），小门店门槛低（如3件）\n"
                                                "→ 自适应门店规模，确保识别有效引流",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                    ]),
                                ])
                            ], title="🎯 核心判定指标", item_id="terms-core"),
                            
                            # 基础概念
                            dbc.AccordionItem([
                                html.Div([
                                    # 5. 中位数 vs 平均数
                                    html.Div([
                                        html.H6("5️⃣ 中位数 vs 平均数 - 为什么不用平均数？", className="text-primary mb-2"),
                                        
                                        html.Div([
                                            html.Strong("一个故事说明白："),
                                            html.Pre(
                                                "5个人的工资：\n"
                                                "张三：3000元\n"
                                                "李四：3500元\n"
                                                "王五：4000元\n"
                                                "赵六：4500元\n"
                                                "马云：1000000元\n\n"
                                                "平均工资 = (3000+3500+4000+4500+1000000)/5 = 203000元\n"
                                                "→ 老板说：'我们公司平均工资20万！'\n"
                                                "→ 员工：？？？我怎么只有3000？\n\n"
                                                "中位数 = 4000元（排序后中间那个）\n"
                                                "→ 更能代表大多数人的真实情况",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("在商品分析中："),
                                            html.Pre(
                                                "10个商品的利润率：\n"
                                                "5%, 8%, 10%, 12%, 15%, 18%, 20%, 25%, 30%, 500%（爆款）\n\n"
                                                "平均数 = 64.3%（被爆款拉高，不真实）\n"
                                                "中位数 = 16.5%（代表大多数商品的水平）\n\n"
                                                "→ 系统用中位数做标准，更公平",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("系统中的应用："),
                                            html.Ul([
                                                html.Li("利润率阈值：品类中位数（P50）→ 一半商品高于它，一半低于它"),
                                                html.Li("动销指数阈值：全店中位数（P50）→ 一半商品高动销，一半低动销"),
                                                html.Li("畅销商品销量门槛：全店70分位数（P70）→ 只有前30%的商品才算'高销'"),
                                                html.Li("明星商品价值门槛：全店30分位数（P30）→ 前70%的商品才有资格当明星"),
                                            ], className="small"),
                                        ]),
                                    ], className="mb-4"),
                                    
                                    # 6. 利润率 vs 利润额
                                    html.Div([
                                        html.H6("6️⃣ 利润率 vs 利润额 - 哪个更重要？", className="text-primary mb-2"),
                                        
                                        html.Div([
                                            html.Strong("两个老板的对话："),
                                            html.Pre(
                                                "老板A（卖包子）：\n"
                                                "'我的利润率50%，很赚钱！'\n"
                                                "→ 售价2元，成本1元，赚1元\n"
                                                "→ 卖100个，赚100元\n\n"
                                                "老板B（卖红酒）：\n"
                                                "'我的利润率只有20%，不赚钱...'\n"
                                                "→ 售价100元，成本80元，赚20元\n"
                                                "→ 卖10瓶，赚200元\n\n"
                                                "结论：A利润率高但赚得少，B利润率低但赚得多",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("明星商品为什么要看两个指标？"),
                                            html.Pre(
                                                "只看利润率：\n"
                                                "→ 1元的口香糖，赚0.5元，利润率50%\n"
                                                "→ 算明星商品？不合理！单品只赚5毛钱\n\n"
                                                "只看利润额：\n"
                                                "→ 100元的商品，赚5元，利润率只有5%\n"
                                                "→ 算明星商品？不合理！效率太低\n\n"
                                                "同时看：\n"
                                                "→ 利润率要高（效率高）\n"
                                                "→ 单品利润要≥0.5元 或 总利润≥50元（价值高）\n"
                                                "→ 这才是真正的明星！",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                    ], className="mb-4"),
                                    
                                    # 7. 标准化
                                    html.Div([
                                        html.H6("7️⃣ 标准化 - 为什么要把数据转换成0-1？", className="text-primary mb-2"),
                                        
                                        html.Div([
                                            html.Strong("问题：为什么不直接用销量，要'标准化'？"),
                                            html.Pre(
                                                "原因：不同指标的单位不同，无法直接相加\n\n"
                                                "例子：\n"
                                                "- 销量：100件\n"
                                                "- 订单数：20单\n\n"
                                                "如果直接相加：100 + 20 = 120\n"
                                                "→ 这个120是什么意思？没有意义！",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("标准化的作用：把所有指标转换成0-1的分数"),
                                            html.Pre(
                                                "标准化公式：\n"
                                                "(实际值 - 最小值) / (最大值 - 最小值)\n\n"
                                                "例子：\n"
                                                "门店有5个商品的销量：20, 30, 50, 80, 100\n\n"
                                                "商品A（销量100）：\n"
                                                "标准化销量 = (100-20)/(100-20) = 80/80 = 1.0（满分）\n\n"
                                                "商品C（销量50）：\n"
                                                "标准化销量 = (50-20)/(100-20) = 30/80 = 0.375（中等）\n\n"
                                                "商品E（销量20）：\n"
                                                "标准化销量 = (20-20)/(100-20) = 0/80 = 0（最低）\n\n"
                                                "→ 现在所有商品的销量都变成了0-1之间的分数\n"
                                                "→ 可以和其他指标（订单数）一起计算了",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                    ], className="mb-4"),
                                    
                                    # 8. 分位数
                                    html.Div([
                                        html.H6("8️⃣ 分位数（P30/P50/P70）- 什么意思？", className="text-primary mb-2"),
                                        
                                        html.Div([
                                            html.Strong("分位数是什么？"),
                                            html.Pre(
                                                "分位数 = 把数据排序后，某个位置的值\n\n"
                                                "例子：10个学生的考试成绩（已排序）\n"
                                                "60, 65, 70, 75, 80, 85, 90, 92, 95, 100\n\n"
                                                "P30（30分位数）= 70分\n"
                                                "→ 30%的学生低于70分，70%的学生高于70分\n\n"
                                                "P50（50分位数/中位数）= 82.5分\n"
                                                "→ 50%的学生低于82.5分，50%的学生高于82.5分\n\n"
                                                "P70（70分位数）= 90分\n"
                                                "→ 70%的学生低于90分，30%的学生高于90分",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("系统中的应用："),
                                            html.Ul([
                                                html.Li("P30（30分位数）：明星商品价值门槛 → 前70%的商品才有资格"),
                                                html.Li("P50（50分位数/中位数）：利润率、动销指数阈值 → 一半一半"),
                                                html.Li("P70（70分位数）：高动销门槛 → 前30%的商品才算高动销"),
                                            ], className="small"),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("为什么用P70作为高动销门槛？"),
                                            html.Pre(
                                                "目标：让约30%的商品有机会成为'高动销'\n\n"
                                                "如果用P50（中位数）：\n"
                                                "→ 50%的商品都是高动销\n"
                                                "→ 太多了，失去筛选意义\n\n"
                                                "如果用P90（90分位数）：\n"
                                                "→ 只有10%的商品是高动销\n"
                                                "→ 太少了，打击运营信心\n\n"
                                                "用P70（70分位数）：\n"
                                                "→ 30%的商品是高动销\n"
                                                "→ 刚刚好，既有筛选性又不会太少",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                    ], className="mb-4"),
                                    
                                    # 9. 动态门槛 vs 固定门槛
                                    html.Div([
                                        html.H6("9️⃣ 动态门槛 vs 固定门槛 - 为什么要动态？", className="text-primary mb-2"),
                                        
                                        html.Div([
                                            html.Strong("固定门槛的问题："),
                                            html.Pre(
                                                "固定门槛：销量≥20件，订单≥5单\n\n"
                                                "大门店（日均1000单）：\n"
                                                "- 销量中位数：50件\n"
                                                "- 20件太低，80%的商品都满足\n"
                                                "→ 明星商品太多，失去筛选意义\n\n"
                                                "小门店（日均50单）：\n"
                                                "- 销量中位数：2件\n"
                                                "- 20件太高，只有3.7%的商品满足\n"
                                                "→ 明星商品太少，打击运营信心\n\n"
                                                "→ 一刀切不合理！",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("动态门槛的优势："),
                                            html.Pre(
                                                "动态门槛：销量≥P70，订单≥P70\n\n"
                                                "大门店（日均1000单）：\n"
                                                "- P70 = 30件（自动提高）\n"
                                                "- 约30%的商品满足\n"
                                                "→ 筛选性强，明星商品含金量高\n\n"
                                                "小门店（日均50单）：\n"
                                                "- P70 = 4件（自动降低）\n"
                                                "- 约30%的商品满足\n"
                                                "→ 门槛合理，明星商品数量适中\n\n"
                                                "→ 自适应门店规模，更科学！",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("保底门槛的作用："),
                                            html.Pre(
                                                "问题：如果门店太小怎么办？\n\n"
                                                "极小门店（日均10单）：\n"
                                                "- P70可能只有1件\n"
                                                "- 1件就算高动销？太低了！\n\n"
                                                "解决：设置保底门槛\n"
                                                "- 销量≥max(P70, 5件)\n"
                                                "- 订单≥max(P70, 2单)\n"
                                                "→ 既动态又有底线",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                    ], className="mb-4"),
                                    
                                    # 10. 品类内比较 vs 全店比较
                                    html.Div([
                                        html.H6("🔟 品类内比较 vs 全店比较 - 什么时候用哪个？", className="text-primary mb-2"),
                                        
                                        html.Div([
                                            html.Strong("核心原则："),
                                            html.Pre(
                                                "利润率 → 品类内比较（公平竞争）\n"
                                                "动销指数 → 全店比较（找出最畅销）",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("为什么利润率要品类内比较？"),
                                            html.Pre(
                                                "原因：不同品类的利润率差异巨大\n\n"
                                                "饮料品类：利润率30-50%（高）\n"
                                                "生鲜品类：利润率10-20%（低）\n"
                                                "电子产品：利润率5-15%（很低）\n\n"
                                                "如果全店比较：\n"
                                                "→ 所有生鲜、电子产品都是'低利润'\n"
                                                "→ 不公平！应该在同类中比较\n\n"
                                                "品类内比较：\n"
                                                "→ 可乐在饮料中算低利润（35% < 40%中位数）\n"
                                                "→ 白菜在生鲜中算高利润（15% > 12%中位数）\n"
                                                "→ 公平了！",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                        
                                        html.Div([
                                            html.Strong("为什么动销指数要全店比较？"),
                                            html.Pre(
                                                "原因：需要找出全店最畅销的商品\n\n"
                                                "如果品类内比较：\n"
                                                "- 饮料第1名：可乐（动销指数0.85）\n"
                                                "- 生鲜第1名：白菜（动销指数0.62）\n"
                                                "- 零食第1名：薯片（动销指数0.45）\n"
                                                "→ 无法知道可乐、白菜、薯片谁更畅销\n\n"
                                                "全店比较：\n"
                                                "- 可乐：动销指数0.85（全店第1）\n"
                                                "- 白菜：动销指数0.62（全店第8）\n"
                                                "- 薯片：动销指数0.45（全店第15）\n"
                                                "→ 一目了然：可乐最畅销！",
                                                className="bg-light p-2 rounded small mb-2"
                                            ),
                                        ]),
                                    ]),
                                ])
                            ], title="🔧 基础概念", item_id="terms-basic"),
                        ], start_collapsed=True, className="mb-0"),
                    ])
                ], title="📚 专业术语解释（新手必读）", item_id="help-1-5"),
                
                # 第三部分：六象限分析（V7.0全新升级）
                dbc.AccordionItem([
                    html.Div([
                        html.P("门店商品结构健不健康？哪些商品该优化？", className="mb-2 fw-bold"),
                        
                        # 适用场景
                        html.Div([
                            html.Strong("💡 适用场景："),
                            html.Div([
                                html.Div("🐌 清理滞销 → 筛选低效商品，决定促销/下架", className="mb-1"),
                                html.Div("💎 活动选品 → 筛选潜力商品，优化营销提曝光", className="mb-1"),
                                html.Div("⚡ 涨价测试 → 筛选引流商品，评估提价空间", className="mb-1"),
                                html.Div("🎯 ROI监控 → 评估策略引流品的投入产出", className="mb-1"),
                            ], className="mt-2 small"),
                        ], className="alert alert-light py-2 mb-3"),
                        
                        # V7.0 六象限全景图
                        html.Div([
                            html.H6("📊 V7.0 六象限全景图", className="text-primary mb-2"),
                            html.Table([
                                html.Tbody([
                                    html.Tr([
                                        html.Td([
                                            html.Div("💎 潜力商品", className="fw-bold text-primary"),
                                            html.Small("高利润+低动销", className="text-muted d-block"),
                                            html.Small("待推广", className="badge bg-primary mt-1"),
                                        ], className="text-center p-3 border", style={'backgroundColor': '#e3f2fd'}),
                                        html.Td([
                                            html.Div("🌟 明星商品", className="fw-bold text-success"),
                                            html.Small("高利润+高动销+高价值", className="text-muted d-block"),
                                            html.Small("核心盈利", className="badge bg-success mt-1"),
                                        ], className="text-center p-3 border", style={'backgroundColor': '#e8f5e9'}),
                                    ]),
                                    html.Tr([
                                        html.Td([
                                            html.Div("🐌 低效商品", className="fw-bold text-danger"),
                                            html.Small("低利润+低动销", className="text-muted d-block"),
                                            html.Small("待优化", className="badge bg-danger mt-1"),
                                        ], className="text-center p-3 border", style={'backgroundColor': '#ffebee'}),
                                        html.Td([
                                            html.Div("� 畅力销刚需", className="fw-bold text-warning"),
                                            html.Small("低价+高销+正利润", className="text-muted d-block"),
                                            html.Small("基础流量", className="badge bg-warning mt-1"),
                                        ], className="text-center p-3 border", style={'backgroundColor': '#fff3e0'}),
                                    ]),
                                    html.Tr([
                                        html.Td([
                                            html.Div("🎯 策略引流", className="fw-bold", style={'color': '#fa8c16'}),
                                            html.Small("极端价格引流", className="text-muted d-block"),
                                            html.Small("主动策略", className="badge mt-1", style={'backgroundColor': '#fa8c16'}),
                                        ], className="text-center p-3 border", style={'backgroundColor': '#fff7e6'}),
                                        html.Td([
                                            html.Div("⚡ 自然引流", className="fw-bold text-info"),
                                            html.Small("低利润+高动销", className="text-muted d-block"),
                                            html.Small("流量担当", className="badge bg-info mt-1"),
                                        ], className="text-center p-3 border", style={'backgroundColor': '#e0f7fa'}),
                                    ]),
                                ])
                            ], className="table table-bordered mb-2", style={'tableLayout': 'fixed'}),
                            html.Div([
                                html.Small("← 低利润", className="text-muted me-3"),
                                html.Small("高利润 →", className="text-muted"),
                                html.Span(" | ", className="mx-2 text-muted"),
                                html.Small("↑ 高动销", className="text-muted me-3"),
                                html.Small("低动销 ↓", className="text-muted"),
                            ], className="text-center small"),
                        ], className="mb-3"),
                        
                        # 判定标准总览
                        html.Div([
                            html.H6("📐 判定标准总览（V7.2动态门槛）", className="text-primary mb-2"),
                            html.Table([
                                html.Tbody([
                                    html.Tr([
                                        html.Td("利润率阈值", className="fw-bold", style={'width': '120px'}),
                                        html.Td("品类中位数（动态，不同品类不同标准）"),
                                    ]),
                                    html.Tr([
                                        html.Td("动销指数阈值", className="fw-bold"),
                                        html.Td("全店中位数（综合销量60% + 订单数40%）"),
                                    ]),
                                    html.Tr([
                                        html.Td("高动销门槛", className="fw-bold"),
                                        html.Td("销量≥70分位数 且 订单≥70分位数（动态，自适应门店规模）"),
                                    ]),
                                ])
                            ], className="table table-sm table-bordered mb-2"),
                            html.Div([
                                html.I(className="bi bi-lightbulb me-1"),
                                html.Strong("V7.2动态门槛优势："),
                                html.Br(),
                                html.Small("使用70分位数作为门槛，自适应不同门店规模。大门店门槛自动提高，小门店门槛自动降低，确保约30%的商品有机会成为'高动销'。保底门槛：销量≥5件，订单≥2单。", 
                                          className="text-muted"),
                            ], className="small"),
                        ], className="alert alert-light py-2 mb-3"),
                        
                        # 六象限详细说明
                        html.H6("🎯 六象限详解", className="text-primary mb-3"),
                        
                        # 由于内容较长，使用折叠面板
                        dbc.Accordion([
                            # 象限1：策略引流
                            dbc.AccordionItem([
                                html.Div([
                                    html.Div([
                                        html.Strong("定义："), html.Span(" 主动亏损或极低价引流的商品", className="ms-1"),
                                    ], className="mb-2"),
                                    html.Div([
                                        html.Strong("判定条件（满足任一即可）："),
                                        html.Ul([
                                            html.Li("秒杀/满赠：实售价 ≤ 0.01元 + 销量≥中位数（动态）"),
                                            html.Li("亏损引流：利润率 < -50% + 销量≥中位数（动态）"),
                                            html.Li("低价引流：实售价≤2元 且 不到成本一半 + 销量≥中位数（动态）"),
                                            html.Li("赠品：实售价=0 但有销量（无门槛）"),
                                        ], className="mb-1 small"),
                                        html.Div([
                                            html.I(className="bi bi-info-circle me-1"),
                                            html.Small("V7.2优化：使用50分位数（中位数）作为销量门槛，自适应门店规模。大门店门槛高，小门店门槛低。", className="text-muted"),
                                        ], className="small mb-2"),
                                    ]),
                                    html.Div([
                                        html.Strong("典型案例："),
                                        html.Pre(
                                            "商品：可乐500ml\n实售价：0.01元（秒杀活动）\n成本：2.5元\n利润率：-24900%\n销量：150件\n→ 判定：🎯 策略引流\n→ 分析：平台秒杀活动，亏本引流，需监控ROI",
                                            className="bg-light p-2 rounded small mb-2", style={'fontSize': '11px'}
                                        ),
                                    ]),
                                    html.Div([
                                        html.Strong("运营策略："),
                                        html.Ul([
                                            html.Li([html.Span("✅", className="me-1"), "监控活动ROI（引流成本 vs 带动销售）"]),
                                            html.Li([html.Span("✅", className="me-1"), "控制活动频率和数量"]),
                                            html.Li([html.Span("⚠️", className="me-1"), "避免常态化（会损害品牌价值）"]),
                                        ], className="mb-0 small"),
                                    ]),
                                ])
                            ], title="🎯 策略引流（极端引流品）"),
                            
                            # 象限2：明星商品
                            dbc.AccordionItem([
                                html.Div([
                                    html.Div([
                                        html.Strong("定义："), html.Span(" 又赚钱又好卖的核心商品", className="ms-1"),
                                    ], className="mb-2"),
                                    html.Div([
                                        html.Strong("判定条件（需同时满足）："),
                                        html.Ul([
                                            html.Li("高利润：利润率 > 品类中位数"),
                                            html.Li("高动销：动销指数 > 全店中位数"),
                                            html.Li("高价值：单品利润≥0.5元 或 总利润贡献≥50元"),
                                        ], className="mb-1 small"),
                                        html.Div([
                                            html.I(className="bi bi-lightbulb me-1"),
                                            html.Small("为什么要加'高价值'门槛？防止低价商品虚高。例如：1元商品利润率50%，但单品只赚0.5元，不应算明星。", className="text-muted"),
                                        ], className="small mb-2"),
                                    ]),
                                    html.Div([
                                        html.Strong("典型案例："),
                                        html.Pre(
                                            "商品：网红零食礼盒\n实售价：39.9元\n成本：18元\n利润率：55%\n销量：80件/月\n单品利润：21.9元\n总利润：1752元\n→ 判定：🌟 明星商品\n→ 分析：高利润+高销量+高价值，门店核心盈利品",
                                            className="bg-light p-2 rounded small mb-2", style={'fontSize': '11px'}
                                        ),
                                    ]),
                                    html.Div([
                                        html.Strong("运营策略："),
                                        html.Ul([
                                            html.Li([html.Span("✅", className="me-1"), "保持充足库存（避免缺货）"]),
                                            html.Li([html.Span("✅", className="me-1"), "测试小幅提价（评估价格弹性）"]),
                                            html.Li([html.Span("✅", className="me-1"), "关联推荐（带动其他商品）"]),
                                            html.Li([html.Span("⚠️", className="me-1"), "关注竞对价格（防止流失）"]),
                                        ], className="mb-0 small"),
                                    ]),
                                ])
                            ], title="🌟 明星商品（核心盈利品）"),
                            
                            # 象限3：畅销刚需
                            dbc.AccordionItem([
                                html.Div([
                                    html.Div([
                                        html.Strong("定义："), html.Span(" 低价、高销、有利润的刚需基础品", className="ms-1"),
                                    ], className="mb-2"),
                                    html.Div([
                                        html.Strong("判定条件（需同时满足）："),
                                        html.Ul([
                                            html.Li([
                                                "低价：实售价 < 全店商品价格30分位数",
                                                html.Span(" (V7.3优化：从中位数改为30分位数，更宽松)", className="badge bg-success ms-2", style={'fontSize': '10px'})
                                            ]),
                                            html.Li([
                                                "高销：销量 ≥ 全店销量80分位数",
                                                html.Span(" (V7.3优化：从70分位数改为80分位数，更严格)", className="badge bg-success ms-2", style={'fontSize': '10px'})
                                            ]),
                                            html.Li("正利润：利润率 ≥ 品类中位数"),
                                        ], className="mb-1 small"),
                                        html.Div([
                                            html.I(className="bi bi-lightbulb me-1"),
                                            html.Small("V7.3优化说明：降低价格阈值（识别更多刚需品），提高销量门槛（确保是真正的畅销品），避免与明星商品重叠。", className="text-muted"),
                                        ], className="small mb-2"),
                                        html.Div([
                                            html.I(className="bi bi-info-circle me-1"),
                                            html.Small("与'自然引流'的区别：畅销刚需有利润（利润率≥品类中位数），自然引流低利润或亏损。", className="text-muted"),
                                        ], className="small mb-2"),
                                    ]),
                                    html.Div([
                                        html.Strong("典型案例："),
                                        html.Pre(
                                            "商品：包子（猪肉大葱）\n实售价：3.5元\n成本：1.8元\n利润率：48.6%\n销量：200件/月\n→ 判定：🔥 畅销刚需\n→ 分析：低价刚需品，卖得好且有利润，是门店基础",
                                            className="bg-light p-2 rounded small mb-2", style={'fontSize': '11px'}
                                        ),
                                    ]),
                                    html.Div([
                                        html.Strong("运营策略："),
                                        html.Ul([
                                            html.Li([html.Span("✅", className="me-1"), "保持稳定供应（刚需品不能断货）"]),
                                            html.Li([html.Span("✅", className="me-1"), "维持价格竞争力（对标商圈）"]),
                                            html.Li([html.Span("⚠️", className="me-1"), "谨慎提价（可能影响客流）"]),
                                        ], className="mb-0 small"),
                                    ]),
                                ])
                            ], title="🔥 畅销刚需（基础流量品）"),
                            
                            # 象限4：潜力商品
                            dbc.AccordionItem([
                                html.Div([
                                    html.Div([
                                        html.Strong("定义："), html.Span(" 利润好但销量低，有推广价值的商品", className="ms-1"),
                                    ], className="mb-2"),
                                    html.Div([
                                        html.Strong("判定条件（需同时满足）："),
                                        html.Ul([
                                            html.Li("高利润：利润率 > 品类中位数"),
                                            html.Li([
                                                "低动销：销量 < 全店销量中位数",
                                                html.Span(" (V7.3优化：明确低动销上限)", className="badge bg-success ms-2", style={'fontSize': '10px'})
                                            ]),
                                            html.Li([
                                                "有价值：单品利润额 ≥ 0.3元",
                                                html.Span(" (V7.3新增：避免低价低利润品被误判)", className="badge bg-success ms-2", style={'fontSize': '10px'})
                                            ]),
                                        ], className="mb-1 small"),
                                        html.Div([
                                            html.I(className="bi bi-lightbulb me-1"),
                                            html.Small("V7.3优化说明：增加单品利润额门槛（≥0.3元），过滤掉虽然利润率高但单品利润很低的商品（如1元商品利润率50%但只赚0.5元）。", className="text-muted"),
                                        ], className="small mb-2"),
                                    ]),
                                    html.Div([
                                        html.Strong("典型案例："),
                                        html.Pre(
                                            "商品：进口红酒\n实售价：128元\n成本：45元\n利润率：64.8%\n销量：5件/月\n→ 判定：💎 潜力商品\n→ 分析：利润率高但销量低，需要增加曝光",
                                            className="bg-light p-2 rounded small mb-2", style={'fontSize': '11px'}
                                        ),
                                    ]),
                                    html.Div([
                                        html.Strong("运营策略："),
                                        html.Ul([
                                            html.Li([html.Span("✅", className="me-1"), "上平台活动（提高曝光）"]),
                                            html.Li([html.Span("✅", className="me-1"), "关联推荐（搭配明星商品）"]),
                                            html.Li([html.Span("✅", className="me-1"), "优化商品详情页（提高转化）"]),
                                            html.Li([html.Span("✅", className="me-1"), "测试降价促销（评估价格敏感度）"]),
                                        ], className="mb-0 small"),
                                    ]),
                                ])
                            ], title="💎 潜力商品（待推广）"),
                            
                            # 象限5：自然引流
                            dbc.AccordionItem([
                                html.Div([
                                    html.Div([
                                        html.Strong("定义："), html.Span(" 低利润但高销量的引流品（非主动策略）", className="ms-1"),
                                    ], className="mb-2"),
                                    html.Div([
                                        html.Strong("判定条件（需同时满足）："),
                                        html.Ul([
                                            html.Li("低利润：利润率 ≤ 品类中位数"),
                                            html.Li("高动销：动销指数 > 全店中位数"),
                                            html.Li("销量门槛：销量≥70分位数 且 订单≥70分位数（动态）"),
                                        ], className="mb-1 small"),
                                        html.Div([
                                            html.I(className="bi bi-info-circle me-1"),
                                            html.Small("与'策略引流'的区别：策略引流是极端价格（0.01元、亏损50%+），自然引流是正常定价但利润率低。V7.2使用动态门槛自适应门店规模。", className="text-muted"),
                                        ], className="small mb-2"),
                                    ]),
                                    html.Div([
                                        html.Strong("典型案例："),
                                        html.Pre(
                                            "商品：农夫山泉550ml\n实售价：2.5元\n成本：1.8元\n利润率：28%（低于饮料品类中位数35%）\n销量：180件/月\n→ 判定：⚡ 自然引流\n→ 分析：刚需品，卖得好但利润低，带动客流",
                                            className="bg-light p-2 rounded small mb-2", style={'fontSize': '11px'}
                                        ),
                                    ]),
                                    html.Div([
                                        html.Strong("运营策略："),
                                        html.Ul([
                                            html.Li([html.Span("✅", className="me-1"), "测试小幅提价（评估价格弹性）"]),
                                            html.Li([html.Span("✅", className="me-1"), "关联推荐高毛利品（提升客单价）"]),
                                            html.Li([html.Span("⚠️", className="me-1"), "监控竞对价格（避免失去竞争力）"]),
                                            html.Li([html.Span("⚠️", className="me-1"), "评估是否值得保留（占库位成本）"]),
                                        ], className="mb-0 small"),
                                    ]),
                                ])
                            ], title="⚡ 自然引流（流量担当）"),
                            
                            # 象限6：低效商品（V7.2动态门槛）
                            dbc.AccordionItem([
                                html.Div([
                                    html.Div([
                                        html.Strong("定义："), html.Span(" 既不赚钱也不好卖的商品", className="ms-1"),
                                    ], className="mb-2"),
                                    html.Div([
                                        html.Strong("判定条件（V7.2动态门槛）："),
                                        html.Ul([
                                            html.Li("低利润：利润率 ≤ 品类中位数"),
                                            html.Li("低动销：动销指数 ≤ 全店中位数 或 销量<70分位数 或 订单<70分位数"),
                                        ], className="mb-1 small"),
                                        html.Div([
                                            html.I(className="bi bi-info-circle me-1"),
                                            html.Small("V7.2优化：使用动态门槛（70分位数）自适应门店规模。不再是'其他所有情况'，而是明确的'低利润+低动销'。", className="text-muted"),
                                        ], className="small mb-2"),
                                    ]),
                                    html.Div([
                                        html.Strong("典型案例："),
                                        html.Pre(
                                            "商品：某品牌薯片（小众口味）\n实售价：8.9元\n成本：5.2元\n利润率：41.6%（高于品类中位数35%）\n销量：2件/月（< 70分位数4件）\n订单数：1单（< 70分位数3单）\n动销指数：0.15（低于全店中位数0.5）\n→ 判定：🐌 低效商品\n→ 分析：虽然利润率不错，但销量太少，占库位",
                                            className="bg-light p-2 rounded small mb-2", style={'fontSize': '11px'}
                                        ),
                                    ]),
                                    html.Div([
                                        html.Strong("运营策略："),
                                        html.Ul([
                                            html.Li([html.Span("✅", className="me-1"), "促销清货（降价、满减）"]),
                                            html.Li([html.Span("✅", className="me-1"), "评估下架（释放库位）"]),
                                            html.Li([html.Span("✅", className="me-1"), "分析原因（价格？口味？包装？）"]),
                                            html.Li([html.Span("⚠️", className="me-1"), "避免盲目进货（控制库存）"]),
                                        ], className="mb-0 small"),
                                    ]),
                                ])
                            ], title="🐌 低效商品（待优化）"),
                        ], start_collapsed=True, className="mb-3"),
                        
                        # 优化路径图
                        html.Div([
                            html.H6("🎯 优化路径图", className="text-primary mb-2"),
                            html.Pre(
                                "🐌 低效商品\n  ↓ 增加曝光（活动、推荐）\n⚡ 自然引流 / 💎 潜力商品\n  ↓ 优化定价 / 提高销量\n🔥 畅销刚需 / 🌟 明星商品",
                                className="bg-light p-3 rounded text-center mb-2", style={'fontSize': '12px', 'lineHeight': '1.8'}
                            ),
                            html.Strong("具体路径："),
                            html.Ul([
                                html.Li("🐌→💎：优化定价，提高利润率"),
                                html.Li("🐌→⚡：增加曝光，提高销量（但利润低）"),
                                html.Li("⚡→🌟：小幅提价，提高利润率"),
                                html.Li("💎→🌟：上活动，增加曝光和销量"),
                                html.Li("🔥→🌟：测试提价，提高利润率"),
                            ], className="mb-0 small"),
                        ], className="alert alert-success py-2 mb-3"),
                        
                        # 特殊标记
                        html.Div([
                            html.Strong("🚨 特殊标记："),
                            html.Span(" 🚨亏损=利润率<0% ", className="badge bg-danger me-2"),
                            html.Span(" 📦低频=销量≤5件 ", className="badge bg-secondary"),
                            html.Br(),
                            html.Small("这些商品需要优先处理，不受六象限分类影响", className="text-muted"),
                        ], className="alert alert-warning py-2 mb-0")
                    ])
                ], title="🎯 商品六象限分析（V7.0全新升级）", item_id="help-2"),
                
                # 第三部分：智能调价计算器
                dbc.AccordionItem([
                    html.Div([
                        html.P("这个商品该卖多少钱？调价后会怎样？", className="mb-2 fw-bold"),
                        
                        # 适用场景
                        html.Div([
                            html.Strong("适用场景："),
                            html.Ul([
                                html.Li(["🚨 ", html.Strong("亏损商品"), " → 算出止血价，调到不亏"]),
                                html.Li(["🐌 ", html.Strong("滞销商品"), " → 测算降价促销效果"]),
                                html.Li(["🏷️ ", html.Strong("竞对比价"), " → 评估降价到竞对价位的利润影响"]),
                                html.Li(["📈 ", html.Strong("利润优化"), " → 测试涨价对销量和利润的影响"]),
                            ], className="mb-0 small"),
                        ], className="alert alert-light py-2 mb-3"),
                        
                        # 1. 价格弹性系数
                        html.Div([
                            html.H6("📊 价格弹性系数", className="text-primary mb-2"),
                            html.P("衡量「价格变化对销量的影响程度」", className="mb-2 small"),
                            html.Pre(
                                "弹性系数 = 销量变化% ÷ 价格变化%\n\n"
                                "举例：\n"
                                "价格从10元涨到11元（涨10%），销量从100件降到85件（降15%）\n"
                                "弹性系数 = -15% ÷ 10% = -1.5",
                                className="bg-light p-2 rounded",
                                style={'fontSize': '11px', 'whiteSpace': 'pre-wrap'}
                            ),
                            html.Table([
                                html.Thead(html.Tr([
                                    html.Th("弹性系数", style={'width': '100px'}),
                                    html.Th("类型"),
                                    html.Th("含义"),
                                ])),
                                html.Tbody([
                                    html.Tr([
                                        html.Td("< -1", className="text-danger"),
                                        html.Td("敏感型"),
                                        html.Td("涨价1%，销量降>1%（慎重涨价）"),
                                    ]),
                                    html.Tr([
                                        html.Td("= -1"),
                                        html.Td("中性"),
                                        html.Td("涨价1%，销量降1%"),
                                    ]),
                                    html.Tr([
                                        html.Td("> -1", className="text-success"),
                                        html.Td("不敏感型"),
                                        html.Td("涨价1%，销量降<1%（可以涨价）"),
                                    ]),
                                ])
                            ], className="table table-bordered table-sm mb-2"),
                            html.Div([
                                html.Strong("🤖 自动学习："),
                                html.Span("系统分析历史调价记录，自动计算每个商品的弹性系数", className="small"),
                            ], className="alert alert-info py-1 mb-0 small"),
                        ], className="mb-3"),
                        
                        # 2. 预估销量公式
                        html.Div([
                            html.H6("📈 预估销量", className="text-primary mb-2"),
                            html.Pre(
                                "预估销量 = 当前销量 × (1 + 弹性系数 × 价格变化率)\n\n"
                                "举例：\n"
                                "当前销量100件，弹性系数-1.5，价格涨10%\n"
                                "预估销量 = 100 × (1 + (-1.5) × 10%)\n"
                                "        = 100 × (1 - 0.15)\n"
                                "        = 100 × 0.85 = 85件",
                                className="bg-light p-2 rounded",
                                style={'fontSize': '11px', 'whiteSpace': 'pre-wrap'}
                            ),
                        ], className="mb-3"),
                        
                        # 3. 预估利润公式
                        html.Div([
                            html.H6("💰 预估利润", className="text-primary mb-2"),
                            html.P("通过对比调价前后的「总利润」，判断调价是否值得", className="mb-2 small text-muted"),
                            
                            # 公式说明
                            html.Div([
                                html.Strong("公式：", className="d-block mb-1"),
                                html.Pre(
                                    "单件利润 = 售价 - 成本\n"
                                    "总利润 = 销量 × 单件利润",
                                    className="bg-white border p-2 rounded mb-0",
                                    style={'fontSize': '12px', 'whiteSpace': 'pre-wrap'}
                                ),
                                html.Small("💡 注意：此处为毛利润，未扣除平台扣点（平台费用在其他报表中体现）", className="text-muted"),
                            ], className="mb-2"),
                            
                            # 完整举例
                            html.Div([
                                html.Strong("完整举例：", className="d-block mb-2"),
                                
                                # 调价前
                                html.Div([
                                    html.Span("📍 调价前：", className="fw-bold text-secondary"),
                                    html.Span("售价10元，成本6元，日销100件", className="small"),
                                ], className="mb-1"),
                                html.Pre(
                                    "单件利润 = 10 - 6 = 4元\n"
                                    "日总利润 = 100件 × 4元 = 400元",
                                    className="bg-light p-2 rounded mb-2",
                                    style={'fontSize': '11px', 'whiteSpace': 'pre-wrap'}
                                ),
                                
                                # 调价后
                                html.Div([
                                    html.Span("📍 涨价10%后：", className="fw-bold text-primary"),
                                    html.Span("新售价11元，预估销量85件（弹性系数-1.5）", className="small"),
                                ], className="mb-1"),
                                html.Pre(
                                    "单件利润 = 11 - 6 = 5元\n"
                                    "日总利润 = 85件 × 5元 = 425元",
                                    className="bg-light p-2 rounded mb-2",
                                    style={'fontSize': '11px', 'whiteSpace': 'pre-wrap'}
                                ),
                                
                                # 结论
                                html.Div([
                                    html.Strong("📊 对比结论："),
                                    html.Span("涨价10%后，虽然销量降15%（少卖15件），但日利润多赚25元（+6.25%）", className="small"),
                                ], className="alert alert-success py-1 mb-0 small"),
                            ], className="border rounded p-2 bg-light"),
                        ], className="mb-3"),
                        
                        # 4. 保本价公式
                        html.Div([
                            html.H6("🎯 保本价（亏损判定标准）", className="text-primary mb-2"),
                            html.P("系统用「保本价」判断商品是否亏损：售价 < 保本价 = 亏损商品", className="mb-2 small text-muted"),
                            html.Pre(
                                "保本价 = 成本 ÷ (1 - 平台费率)\n\n"
                                "举例：成本6元，平台费率8%\n"
                                "保本价 = 6 ÷ (1-0.08) = 6.52元\n"
                                "→ 售价低于6.52元就会亏损",
                                className="bg-light p-2 rounded",
                                style={'fontSize': '11px', 'whiteSpace': 'pre-wrap'}
                            ),
                        ], className="mb-3"),
                        
                        # 5. 两种利润口径说明
                        html.Div([
                            html.H6("📝 两种利润口径", className="text-info mb-2"),
                            html.Table([
                                html.Thead(html.Tr([
                                    html.Th("场景", style={'width': '120px'}),
                                    html.Th("公式"),
                                    html.Th("用途"),
                                ])),
                                html.Tbody([
                                    html.Tr([
                                        html.Td("亏损判定"),
                                        html.Td("保本价 = 成本/(1-8%)"),
                                        html.Td("判断商品是否亏本销售"),
                                    ]),
                                    html.Tr([
                                        html.Td("调价预估"),
                                        html.Td("利润 = 售价 - 成本"),
                                        html.Td("对比调价前后的毛利变化"),
                                    ]),
                                ])
                            ], className="table table-bordered table-sm mb-2"),
                            html.Small("💡 调价预估用毛利简化计算，便于快速对比；实际净利润需扣除平台费用", className="text-muted"),
                        ], className="mb-3"),
                        
                        # 6. 注意事项
                        html.Div([
                            html.H6("⚠️ 注意事项", className="text-warning mb-2"),
                            html.Ul([
                                html.Li("弹性系数需要足够的历史数据才准确，新品建议小幅调价测试"),
                                html.Li("平台费率默认设定为8%，实际费率请根据各渠道合同调整"),
                                html.Li("计算器需要结合实际情况使用，所有预估值仅供参考"),
                            ], className="mb-0 small"),
                        ], className="alert alert-warning py-2 mb-0"),
                    ])
                ], title="🔧 智能调价计算器", item_id="help-3"),
                
                # 第四部分：如何使用六象限分析
                dbc.AccordionItem([
                    html.Div([
                        html.P("掌握这4步，轻松用好六象限分析！", className="mb-3 fw-bold text-primary"),
                        
                        # 第1步
                        html.Div([
                            html.H6("第1步：看分布（整体诊断）", className="text-primary mb-2"),
                            html.Ul([
                                html.Li("打开「商品健康分析」→「六象限分布」Tab"),
                                html.Li("看饼图：各象限占比是否健康？"),
                                html.Li("看趋势：哪些象限在增长/下降？"),
                            ], className="mb-3 small"),
                        ]),
                        
                        # 第2步
                        html.Div([
                            html.H6("第2步：找问题（重点商品）", className="text-primary mb-2"),
                            html.Ul([
                                html.Li([html.Span("🐌低效商品 > 20%？", className="fw-bold"), " → 需要清理"]),
                                html.Li([html.Span("🌟明星商品 < 20%？", className="fw-bold"), " → 盈利能力不足"]),
                                html.Li([html.Span("🎯策略引流 > 10%？", className="fw-bold"), " → 引流成本过高"]),
                            ], className="mb-3 small"),
                        ]),
                        
                        # 第3步
                        html.Div([
                            html.H6("第3步：定策略（分类处理）", className="text-primary mb-2"),
                            html.Table([
                                html.Thead(html.Tr([
                                    html.Th("象限", style={'width': '120px'}),
                                    html.Th("处理策略"),
                                ])),
                                html.Tbody([
                                    html.Tr([
                                        html.Td("🐌 低效商品", className="fw-bold"),
                                        html.Td("促销清货 or 下架"),
                                    ]),
                                    html.Tr([
                                        html.Td("💎 潜力商品", className="fw-bold"),
                                        html.Td("上活动、关联推荐、优化详情页"),
                                    ]),
                                    html.Tr([
                                        html.Td("⚡ 自然引流", className="fw-bold"),
                                        html.Td("测试小幅提价、关联高毛利品"),
                                    ]),
                                    html.Tr([
                                        html.Td("🎯 策略引流", className="fw-bold"),
                                        html.Td("监控ROI、控制频率和数量"),
                                    ]),
                                    html.Tr([
                                        html.Td("🌟 明星商品", className="fw-bold"),
                                        html.Td("保持库存、测试提价、关联推荐"),
                                    ]),
                                    html.Tr([
                                        html.Td("🔥 畅销刚需", className="fw-bold"),
                                        html.Td("稳定供应、对标竞对、谨慎提价"),
                                    ]),
                                ])
                            ], className="table table-sm table-bordered mb-3"),
                        ]),
                        
                        # 第4步
                        html.Div([
                            html.H6("第4步：看变化（趋势监控）", className="text-primary mb-2"),
                            html.Ul([
                                html.Li("打开「趋势变化」Tab，查看象限变化"),
                                html.Li([
                                    html.Span("关注恶化趋势：", className="fw-bold text-danger"),
                                    html.Br(),
                                    html.Small("• 明星→潜力（销量下降，需要增加曝光）", className="text-muted"),
                                    html.Br(),
                                    html.Small("• 潜力→低效（持续低迷，考虑下架）", className="text-muted"),
                                ]),
                                html.Li([
                                    html.Span("关注改善趋势：", className="fw-bold text-success"),
                                    html.Br(),
                                    html.Small("• 低效→潜力（利润率提升，继续优化）", className="text-muted"),
                                    html.Br(),
                                    html.Small("• 潜力→明星（销量提升，加大推广）", className="text-muted"),
                                ]),
                            ], className="mb-3 small"),
                        ]),
                        
                        # 提示
                        html.Div([
                            html.I(className="bi bi-lightbulb me-2"),
                            html.Strong("💡 小提示："),
                            html.Br(),
                            html.Small("看不懂专业术语？点击上面的「📚 专业术语解释」查看详细说明！", className="text-muted"),
                        ], className="alert alert-info py-2 mb-0"),
                    ])
                ], title="🔍 如何使用六象限分析", item_id="help-4"),
                
                # 第五部分：每日/每周SOP
                dbc.AccordionItem([
                    html.Div([
                        html.H6("⏰ 每天早上（5分钟）", className="text-danger mb-2"),
                        html.Ol([
                            html.Li("打开「昨日经营诊断」"),
                            html.Li("有🔴红色警报？→ 立即处理"),
                            html.Li("有🟡黄色提醒？→ 记录待办"),
                        ], className="mb-3"),
                        
                        html.H6("📅 每周一次（15-20分钟）", className="text-primary mb-2"),
                        html.Ol([
                            html.Li("打开「商品健康分析」→「六象限分布」Tab"),
                            html.Li("查看六象限分布图，了解整体结构"),
                            html.Li([
                                "点击「🐌低效商品」，导出清单",
                                html.Br(),
                                html.Small("→ 决定：促销清货/下架/调价", className="text-muted ms-3"),
                            ]),
                            html.Li([
                                "点击「💎潜力商品」，挑3-5个报活动",
                                html.Br(),
                                html.Small("→ 增加曝光，提升销量", className="text-muted ms-3"),
                            ]),
                            html.Li([
                                "点击「🎯策略引流」，评估ROI效果",
                                html.Br(),
                                html.Small("→ 计算引流成本 vs 带动销售", className="text-muted ms-3"),
                            ]),
                            html.Li([
                                "查看「趋势变化」Tab，关注象限变化",
                                html.Br(),
                                html.Small("→ 重点关注：明星→潜力（销量下降）、潜力→低效（持续低迷）", className="text-muted ms-3"),
                            ]),
                            html.Li([
                                "查看「商品评分」Tab，找出高分低销的商品",
                                html.Br(),
                                html.Small("→ 这些商品有潜力，需要增加推广", className="text-muted ms-3"),
                            ]),
                        ], className="mb-3"),
                        
                        html.Div([
                            html.Strong("🎯 健康门店标准（V7.0）："),
                            html.Div([
                                html.Strong("六象限分布：", className="d-block mt-2 mb-1"),
                                html.Ul([
                                    html.Li("🌟 明星商品：≥ 25%（核心盈利）"),
                                    html.Li("💎 潜力商品：10-15%（待推广）"),
                                    html.Li("🔥 畅销刚需：15-20%（基础流量）"),
                                    html.Li("⚡ 自然引流：10-15%（流量担当）"),
                                    html.Li("🎯 策略引流：< 5%（控制成本）"),
                                    html.Li("🐌 低效商品：< 20%（需要优化）"),
                                ], className="mb-2 small"),
                                html.Strong("异常指标：", className="d-block mb-1"),
                                html.Ul([
                                    html.Li("🔴 紧急问题：= 0个"),
                                    html.Li("🚨 亏损商品（非策略）：< 3%"),
                                    html.Li("📦 低频商品（销量≤5件）：< 15%"),
                                ], className="mb-0 small"),
                            ])
                        ], className="alert alert-success py-2")
                    ])
                ], title="📋 每日/每周SOP", item_id="help-5"),
            ], start_collapsed=True, always_open=True),
        ], style={'maxHeight': '70vh', 'overflowY': 'auto'}),
    ], id="product-help-modal", size="lg", is_open=False, scrollable=True)
    
    return html.Div([
        # 帮助按钮 + 弹窗
        html.Div([
            dbc.Button(
                [html.I(className="bi bi-question-circle me-1"), "操作指南"],
                id="product-help-btn",
                color="outline-secondary",
                size="sm",
                className="float-end"
            ),
            help_modal,
        ], className="mb-2"),
        
        # Tab切换
        dbc.Tabs([
            # Tab1: 六象限分布
            dbc.Tab([
                html.Div([
                    # 筛选提示
                    html.Div([
                        html.Small(f"🎯 当前显示: {filter_hint} ({total_products}个商品)", 
                                  className="text-primary fw-bold")
                    ], className="mb-2") if category_filter else html.Div(),
                    
                    # V7.3说明（六象限分类体系 - 保守优化）
                    dbc.Alert([
                        html.Strong("📊 V7.3 六象限分类体系（保守优化）："),
                        html.Br(),
                        html.Small([
                            "🌟 明星商品：高利润率+高动销+高单品价值(≥0.5元或总利润≥50元) → 核心盈利品",
                            html.Br(),
                            "🔥 畅销商品：低价(30分位数)+高销(80分位数)+正利润 → 刚需基础品 ",
                            html.Span("(V7.3优化)", className="badge bg-success ms-1", style={'fontSize': '9px'}),
                            html.Br(),
                            "💎 潜力商品：高利润率+低动销(中位数)+单品利润≥0.3元 → 有价值的待推广品 ",
                            html.Span("(V7.3优化)", className="badge bg-success ms-1", style={'fontSize': '9px'}),
                            html.Br(),
                            "🎯 策略引流：极端引流品（0.01元秒杀/亏损50%以上/2元以下不到成本一半/赠品）",
                            html.Br(),
                            "⚡ 自然引流：低利润率+高动销（动销指数>中位数+销量≥70分位数+订单≥70分位数） → 市场验证的引流品",
                            html.Br(),
                            "🐌 低效商品：低利润率+低动销（动态门槛） → 待优化或淘汰",
                        ], className="text-muted")
                    ], color="light", className="mb-3 py-2 border"),
                    
                    # 四象限进度条列表
                    html.Div([
                        html.Div(quadrant_progress_items, className="px-2")
                    ], style={'maxHeight': '280px', 'overflowY': 'auto'}),
                    
                    # 特殊标记统计
                    html.Div([
                        html.Hr(className="my-2"),
                        html.Small("📌 特殊标记商品：", className="text-muted fw-bold"),
                        html.Span([
                            html.Span(f"🚨 亏损商品 {loss_count}个", className="badge bg-danger me-2"),
                            html.Span(f"📦 低频商品 {low_freq_count}个", className="badge bg-secondary"),
                        ], className="ms-2")
                    ], className="mb-3") if (loss_count > 0 or low_freq_count > 0) else html.Div(),
                    
                    # V7.0汇总统计(六象限)
                    html.Hr(className="my-3"),
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Span("🌟 明星商品", className="d-block text-muted", style={'fontSize': '12px'}),
                                html.Span(f"{quadrant_counts.get('🌟 明星商品', 0)}个", 
                                         className="badge bg-success", style={'fontSize': '14px'})
                            ], className="text-center")
                        ], width=2),
                        dbc.Col([
                            html.Div([
                                html.Span("🔥 畅销商品", className="d-block text-muted", style={'fontSize': '12px'}),
                                html.Span(f"{quadrant_counts.get('🔥 畅销商品', 0)}个", 
                                         className="badge", style={'fontSize': '14px', 'backgroundColor': '#ff9800', 'color': 'white'})
                            ], className="text-center")
                        ], width=2),
                        dbc.Col([
                            html.Div([
                                html.Span("💎 潜力商品", className="d-block text-muted", style={'fontSize': '12px'}),
                                html.Span(f"{quadrant_counts.get('💎 潜力商品', 0)}个", 
                                         className="badge bg-primary", style={'fontSize': '14px'})
                            ], className="text-center")
                        ], width=2),
                        dbc.Col([
                            html.Div([
                                html.Span("🎯 策略引流", className="d-block text-muted", style={'fontSize': '12px'}),
                                html.Span(f"{quadrant_counts.get('🎯 策略引流', 0)}个", 
                                         className="badge bg-warning text-dark", style={'fontSize': '14px'})
                            ], className="text-center")
                        ], width=2),
                        dbc.Col([
                            html.Div([
                                html.Span("⚡ 自然引流", className="d-block text-muted", style={'fontSize': '12px'}),
                                html.Span(f"{quadrant_counts.get('⚡ 自然引流', 0)}个", 
                                         className="badge bg-info", style={'fontSize': '14px'})
                            ], className="text-center")
                        ], width=2),
                        dbc.Col([
                            html.Div([
                                html.Span("🐌 低效商品", className="d-block text-muted", style={'fontSize': '12px'}),
                                html.Span(f"{quadrant_counts.get('🐌 低效商品', 0)}个", 
                                         className="badge bg-danger", style={'fontSize': '14px'})
                            ], className="text-center")
                        ], width=2),
                    ])
                ], className="pt-3")
            ], label=f"🎯 六象限分布 ({'全部数据' if days_range == 0 else f'{days_range}天'})", tab_id="tab-quadrant"),
            
            # Tab3: 趋势分析（V5.3：前后对半分对比）
            dbc.Tab([
                html.Div([
                    # 趋势分析内容容器（有独立ID，用于范围切换时局部更新）
                    html.Div(
                        (dbc.Alert([
                            html.I(className="bi bi-info-circle me-2"),
                            "全部数据模式不支持趋势对比，请选择具体天数（7/15/30/60/90天）"
                        ], color="info") if days_range == 0 else 
                        create_trend_tab_content(raw_df, category_filter, days_range)) if raw_df is not None and not raw_df.empty else dbc.Alert([
                            html.I(className="bi bi-info-circle me-2"),
                            "需要原始订单数据才能进行趋势分析"
                        ], color="info"),
                        id='trend-tab-content-container'
                    )
                ], className="pt-3")
            ], label=f"📈 趋势变化 ({'不可用' if days_range == 0 else f'{days_range}天对比{days_range}天'})", tab_id="tab-trend", disabled=(days_range == 0)),
        ], id="product-health-tabs", active_tab="tab-score", className="mb-3"),
    ])


def create_product_scoring_section(df: pd.DataFrame, all_channel_options: list = None, current_channel: str = 'ALL') -> html.Div:
    """
    创建商品健康分析区域 V5.0
    
    V5.0重大更新：
    1. 八象限简化为四象限（明星/潜力/引流/问题）
    2. 全局阈值（利润率中位数 + 动销指数中位数）
    3. 动销指数 = 0.5×销量 + 0.3×周转率 + 0.2×订单数
    4. 特殊标记：🚨亏损 📦低频
    5. 保留：品类筛选、渠道筛选、评分概览Tab
    
    参数：
    - df: 用于计算的数据（可能已经过渠道筛选）
    - all_channel_options: 渠道下拉框选项（基于全量数据），不传则从df生成
    - current_channel: 当前选中的渠道值，用于回显
    """
    if df is None or df.empty:
        return html.Div()
    
    # 获取渠道列表 - V5.2: 优先使用传入的全量选项
    if all_channel_options is not None:
        channel_options = all_channel_options
    else:
        # 兼容旧调用方式：从df生成（首次加载时使用）
        channel_options = [{'label': '📊 全部渠道', 'value': 'ALL'}]
        if '渠道' in df.columns:
            channels = sorted(df['渠道'].dropna().unique())
            channel_options += [{'label': ch, 'value': ch} for ch in channels]
    
    # 🚀 V8.6.2性能优化：智能缓存键生成
    def generate_smart_cache_key_for_products(df):
        """生成智能缓存键（商品健康分析专用）"""
        # 门店维度
        if '门店名称' in df.columns:
            stores = sorted(df['门店名称'].unique().tolist())
            if len(stores) <= 3:
                store_key = '_'.join(stores)
            else:
                # 超过3个门店，使用首个+数量
                store_key = f"{stores[0]}_plus{len(stores)-1}"
        else:
            store_key = 'all'
        
        # 日期范围维度
        date_col = '日期' if '日期' in df.columns else '下单时间'
        if date_col in df.columns:
            dates = pd.to_datetime(df[date_col])
            date_range = f"{dates.min().strftime('%Y%m%d')}_{dates.max().strftime('%Y%m%d')}"
        else:
            date_range = 'unknown'
        
        # 数据规模维度（用于检测数据变化）
        row_count = len(df)
        
        return f"product_scores_v2:{store_key}:{date_range}:rows_{row_count}:days_30"
    
    # 尝试从Redis缓存读取商品评分数据
    product_scores = None
    cache_key = None
    try:
        from redis_cache_manager import REDIS_CACHE_MANAGER
        if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
            cache_key = generate_smart_cache_key_for_products(df)
            product_scores = REDIS_CACHE_MANAGER.get(cache_key)
            if product_scores is not None:
                print(f"✅ [V8.6.2缓存命中] 商品评分数据")
                print(f"   缓存键: {cache_key}")
    except Exception as e:
        print(f"⚠️ Redis缓存读取失败: {e}")
    
    # 如果缓存未命中，重新计算
    if product_scores is None:
        print(f"[商品健康分析初始化] 原始数据行数: {len(df)}")
        import time
        start_time = time.time()
        product_scores = calculate_enhanced_product_scores_with_trend(df, days=30)
        calc_time = time.time() - start_time
        print(f"[商品健康分析初始化] 评分数据行数: {len(product_scores)}, 计算耗时: {calc_time:.2f}秒")
        print(f"[商品健康分析初始化] 评分数据列: {list(product_scores.columns) if not product_scores.empty else '空'}")
        
        # 保存到Redis缓存（V8.6.2：60分钟缓存）
        if cache_key:
            try:
                from redis_cache_manager import REDIS_CACHE_MANAGER
                if REDIS_CACHE_MANAGER and REDIS_CACHE_MANAGER.enabled:
                    REDIS_CACHE_MANAGER.set(cache_key, product_scores, ttl=3600)
                    print(f"✅ [V8.6.2已缓存] 商品评分数据，60分钟有效")
                    print(f"   缓存键: {cache_key}")
            except Exception as e:
                print(f"⚠️ Redis缓存保存失败: {e}")
    
    if product_scores.empty:
        print("[商品健康分析初始化] ⚠️ 评分数据为空！")
        return dbc.Alert("暂无商品数据", color="warning")
    
    # 获取品类列表用于筛选按钮
    category_col = '一级分类名' if '一级分类名' in product_scores.columns else None
    category_buttons = []
    
    if category_col:
        # V7.4：改为按明星商品数量排序（评分体系已删除）
        category_stats = product_scores.groupby(category_col).agg({
            '商品名称': 'count'
        }).reset_index()
        category_stats.columns = [category_col, '商品数']
        
        # 计算每个品类的明星商品数量
        star_counts = product_scores[product_scores['四象限分类'] == '🌟 明星商品'].groupby(category_col).size()
        category_stats['明星商品数'] = category_stats[category_col].map(star_counts).fillna(0).astype(int)
        
        # 按明星商品数量降序排序
        category_stats = category_stats.sort_values('明星商品数', ascending=False)
        
        total_categories = len(category_stats)
        for idx, (_, row) in enumerate(category_stats.iterrows()):
            cat_name = row[category_col]
            cat_count = row['商品数']
            star_count = row['明星商品数']
            
            # V7.4：按明星商品数量选择颜色
            if star_count >= 10:
                btn_color = 'success'
                star_badge_class = 'bg-success text-white'
            elif star_count >= 5:
                btn_color = 'info'
                star_badge_class = 'bg-info text-white'
            elif star_count >= 3:
                btn_color = 'primary'
                star_badge_class = 'bg-primary text-white'
            elif star_count >= 1:
                btn_color = 'warning'
                star_badge_class = 'bg-warning text-dark'
            else:
                btn_color = 'secondary'
                star_badge_class = 'bg-secondary text-white'
            
            category_buttons.append(
                dbc.Button([
                    html.Span(f"{cat_name}", className="me-1 fw-bold"),
                    html.Span(f"⭐{star_count}", className=f"badge {star_badge_class} me-1", style={'fontSize': '11px', 'fontWeight': 'bold'}),
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
                ], width=3),
                # 独立日期选择器（优化样式）
                dbc.Col([
                    html.Div([
                        html.Span("🔄 对比周期：", className="text-muted me-2", style={'fontSize': '13px', 'fontWeight': '500'}),
                        dbc.ButtonGroup([
                            dbc.Button("全部数据", id={'type': 'health-date-btn', 'days': 0}, 
                                      color="info", size="sm", outline=True, className="px-3"),
                            dbc.Button("7天", id={'type': 'health-date-btn', 'days': 7}, 
                                      color="primary", size="sm", outline=True, className="px-3"),
                            dbc.Button("15天", id={'type': 'health-date-btn', 'days': 15}, 
                                      color="primary", size="sm", outline=False, className="px-3"),  # 默认选中
                            dbc.Button("30天", id={'type': 'health-date-btn', 'days': 30}, 
                                      color="primary", size="sm", outline=True, className="px-3"),
                            dbc.Button("60天", id={'type': 'health-date-btn', 'days': 60}, 
                                      color="primary", size="sm", outline=True, className="px-3"),
                            dbc.Button("90天", id={'type': 'health-date-btn', 'days': 90}, 
                                      color="primary", size="sm", outline=True, className="px-3"),
                        ], size="sm"),
                        html.Small("（N天=近N天vs前N天）", className="text-muted ms-2", style={'fontSize': '11px'})
                    ], className="d-flex align-items-center justify-content-start")
                ], width=7),
                # 渠道筛选下拉框
                dbc.Col([
                    dbc.InputGroup([
                        dbc.InputGroupText("📡 渠道", style={'fontSize': '12px', 'padding': '4px 8px'}),
                        dbc.Select(
                            id='product-health-channel-filter',
                            options=channel_options,
                            value=current_channel,  # V5.2: 使用传入的当前选中值
                            style={'fontSize': '12px', 'padding': '4px 8px', 'maxWidth': '150px'}
                        )
                    ], size="sm")
                ], width=2, className="d-flex align-items-center justify-content-center"),
                dbc.Col([
                    dbc.Button([
                        html.I(className="bi bi-download me-1"),
                        "导出报告"
                    ], id='btn-export-product-scoring', color="primary", size="sm", outline=True)
                ], width=2, className="text-end")
            ], align="center")
        ], className="bg-white border-bottom py-2"),
        
        # 存储当前渠道筛选值和日期范围
        dcc.Store(id='product-health-channel-store', data='ALL'),
        dcc.Store(id='product-health-date-range-store', data=30),
        
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
            
            # ===== 动态内容容器（评分概览Tab + 象限分布Tab + 趋势分析Tab）=====
            html.Div(
                id='product-health-content-container',
                children=create_product_health_content(product_scores, None, None, raw_df=df, days_range=30)
            ),
            
            # 存储当前对比范围天数 (V5.3)
            dcc.Store(id='quadrant-trend-range-store', data=15),
            
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
                    children=(lambda: (
                        print(f"[表格容器初始化] 准备创建表格，评分数据行数: {len(product_scores)}"),
                        create_product_scoring_table_v4(product_scores, current_channel=None)  # 初始化时无渠道上下文
                    )[1])()
                )
            ], id='collapse-scoring-detail', is_open=False)
        ])
    ], id='product-health-card', className="mb-4 shadow-sm border-0")  # 添加id用于返回滚动


# ===== 以下函数已废弃（V5.0改用Tab+进度条列表）=====
# def create_octant_section(octant_pie_option, octant_buttons, octant_counts):
#     """创建八象限分布区域（初始静态版本）- 已废弃"""
#     pass

# def create_octant_section_dynamic(product_scores, category_filter=None):
#     """动态创建八象限分布区域 - 已废弃"""
#     pass


# ===== 以下为真正的表格函数 =====


def create_product_scoring_table_v4(product_scores: pd.DataFrame, filter_type: str = None, filter_value: str = None, category_filter: str = None, current_channel: str = None) -> html.Div:
    """
    创建商品评分详细数据表 V7.2 (六象限版本)
    
    V5.0更新：
    1. 八象限简化为四象限（明星/潜力/引流/问题）
    2. 新增：动销指数、特殊标记（亏损/低频）
    3. 支持按四象限/品类/评分等级筛选
    
    V5.3更新：
    4. 新增category_filter参数，支持在象限/评分等级筛选时保持分类过滤
    
    V6.1更新：
    5. 新增current_channel参数，在提示信息中显示当前渠道
    6. 在表格中添加"渠道"列
    
    V7.2更新：
    7. 字段名从"四象限分类"更新为"六象限分类"（实际已是六象限体系）
    8. 添加调试信息，确保表格显示与导出数据一致
    """
    if product_scores.empty:
        return html.Div("暂无数据", className="text-center text-muted p-4")
    
    # V7.2修复：确定使用的象限字段名（兼容新旧版本）
    # 内部字段名仍为'四象限分类'，但显示时重命名为'六象限分类'
    quadrant_col = '四象限分类' if '四象限分类' in product_scores.columns else '八象限分类'
    category_col = '一级分类名' if '一级分类名' in product_scores.columns else None
    
    # V7.2调试：打印象限分布
    if quadrant_col in product_scores.columns:
        table_quadrant_counts = product_scores[quadrant_col].value_counts()
        print(f"\n[表格显示调试] 原始数据六象限分布:")
        for quadrant, count in table_quadrant_counts.items():
            print(f"  {quadrant}: {count}个")
    
    # 应用筛选
    filtered_df = product_scores.copy()
    
    # V5.3: 首先应用分类筛选（如果有）
    if category_filter and category_filter != '__all__' and category_col:
        filtered_df = filtered_df[filtered_df[category_col] == category_filter]
    
    # 然后应用其他筛选
    if filter_type == 'quadrant' and filter_value:
        # 新版四象限筛选
        filtered_df = filtered_df[filtered_df[quadrant_col] == filter_value]
    elif filter_type == 'octant' and filter_value:
        # 兼容旧版八象限筛选
        filtered_df = filtered_df[filtered_df[quadrant_col] == filter_value]
    elif filter_type == 'category' and filter_value and filter_value != '__all__':
        # 品类筛选（如果还没应用category_filter）
        if category_col and not category_filter:
            filtered_df = filtered_df[filtered_df[category_col] == filter_value]
    elif filter_type == 'score_level' and filter_value:
        # V7.4：评分等级筛选已删除（评分体系已删除）
        print("⚠️ 评分等级筛选已删除，忽略此筛选条件")
        pass
    
    if filtered_df.empty:
        return html.Div("筛选结果为空", className="text-center text-muted p-4")
    
    # 获取模式信息，决定显示哪些列
    period_mode = getattr(filtered_df, 'attrs', {}).get('period_mode', 'comparison')
    
    # 选择显示的列（根据模式动态调整）
    if period_mode == 'all':
        # 全部数据模式：显示原始销量字段
        display_cols = [
            '排名', '渠道', '店内码', '商品名称', '一级分类名', '三级分类名',
            '商品原价', '商品实售价', '单品成本', '综合利润率', '定价利润率',
            '销量', '订单数', '动销指数', '销售额', '利润额',  # 原始字段
            # V7.4：删除评分字段（综合得分、评分等级）
            # V8.10.3：删除重复和低价值字段（实收价格、特殊标记、营销占比、售罄率、库存周转天数）
            quadrant_col, '问题标签', '业务建议'
        ]
    else:
        # 趋势对比模式：显示周期和对比字段
        display_cols = [
            '排名', '渠道', 'ABC描述', '店内码', '商品名称', '一级分类名', '三级分类名',
            '商品原价', '商品实售价', '单品成本', '综合利润率', '定价利润率',
            '周期总销量', '动销指数', '销售额', '销售额占比', 
            '趋势标签', '前期销量', '近期销量', '销量差异', '利润率变化',  # V6.0：前后对比
            # V7.4：删除评分字段（综合得分、评分等级、趋势得分）
            # V8.10.3：删除重复和低价值字段（实收价格、特殊标记、营销占比、售罄率、库存周转天数）
            quadrant_col, '问题标签', '业务建议'
        ]
    
    available_cols = [c for c in display_cols if c in filtered_df.columns]
    display_df = filtered_df[available_cols].copy()
    
    # 格式化数值
    # V8.10.3：删除售罄率、营销占比的格式化
    for col in ['综合利润率', '定价利润率']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    
    # 全部数据模式：格式化销量和订单数
    if '销量' in display_df.columns:
        display_df['销量'] = display_df['销量'].apply(lambda x: f"{int(x)}件" if pd.notna(x) else "-")
    
    if '订单数' in display_df.columns:
        display_df['订单数'] = display_df['订单数'].apply(lambda x: f"{int(x)}单" if pd.notna(x) else "-")
    
    # V6.0: 趋势字段格式化
    # 周期总销量
    if '周期总销量' in display_df.columns:
        display_df['周期总销量'] = display_df['周期总销量'].apply(lambda x: f"{int(x)}件" if pd.notna(x) else "-")
    
    # 前期销量和近期销量
    if '前期销量' in display_df.columns:
        display_df['前期销量'] = display_df['前期销量'].apply(lambda x: f"{int(x)}件" if pd.notna(x) else "-")
    
    if '近期销量' in display_df.columns:
        display_df['近期销量'] = display_df['近期销量'].apply(lambda x: f"{int(x)}件" if pd.notna(x) else "-")
    
    # 销量差异（只显示绝对值）
    if '销量差异' in display_df.columns:
        display_df['销量差异'] = filtered_df['销量差异'].apply(
            lambda x: f"{int(x):+d}件" if pd.notna(x) and x != 0 else "持平" if x == 0 else "-"
        )
    
    if '利润率变化' in display_df.columns:
        display_df['利润率变化'] = display_df['利润率变化'].apply(
            lambda x: f"{x:+.1f}%" if pd.notna(x) else "-"
        )
    
    # V7.4：删除评分字段格式化（评分体系已删除）
    # V8.10.3：删除库存周转天数格式化
    
    # V5.0: 动销指数格式化（0-1范围，显示2位小数）
    if '动销指数' in display_df.columns:
        display_df['动销指数'] = display_df['动销指数'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
    
    # 价格和成本字段格式化
    for col in ['商品原价', '商品实售价', '单品成本']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"¥{x:.2f}" if pd.notna(x) and x > 0 else "-")
    
    if '销售额' in display_df.columns:
        display_df['销售额'] = display_df['销售额'].apply(lambda x: f"¥{x:,.0f}")
    
    if '利润额' in display_df.columns:
        display_df['利润额'] = display_df['利润额'].apply(lambda x: f"¥{x:,.0f}" if pd.notna(x) else "-")
    
    # V4.0新增：销售额占比格式化
    if '销售额占比' in display_df.columns:
        display_df['销售额占比'] = display_df['销售额占比'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
    
    # 调试：打印数据信息
    print(f"[商品评分表格] 数据行数: {len(display_df)}")
    print(f"[商品评分表格] 列数: {len(display_df.columns)}")
    print(f"[商品评分表格] 列名: {list(display_df.columns)[:10]}")  # 打印前10个列名
    if len(display_df) > 0:
        print(f"[商品评分表格] 第一行数据示例: {display_df.iloc[0].to_dict()}")
    
    # 获取日期范围信息（用于列名显示和提示）
    date_range_info = getattr(filtered_df, 'attrs', {}).get('date_range_info', {})
    period_mode = getattr(filtered_df, 'attrs', {}).get('period_mode', 'comparison')  # 'all' 或 'comparison'
    days_range = getattr(filtered_df, 'attrs', {}).get('days_range', 15)
    
    # 创建周期说明提示
    # V6.1：添加渠道提示
    channel_hint = ""
    if current_channel and current_channel != 'ALL':
        channel_hint = f" | 渠道：{current_channel}"
    elif '渠道' in filtered_df.columns:
        unique_channels = filtered_df['渠道'].unique()
        if len(unique_channels) == 1:
            channel_hint = f" | 渠道：{unique_channels[0]}"
        elif len(unique_channels) > 1:
            channel_hint = f" | 渠道：全部（{len(unique_channels)}个）"
    
    if period_mode == 'all':
        period_hint = html.Div([
            html.I(className="bi bi-info-circle me-1", style={'color': '#1890ff'}),
            html.Span("当前显示：", className="text-muted", style={'fontSize': '12px'}),
            html.Span("全部历史数据", style={'fontSize': '12px', 'fontWeight': 'bold', 'color': '#1890ff', 'marginLeft': '4px'}),
            html.Span("（不进行趋势对比）", className="text-muted ms-1", style={'fontSize': '11px'}),
            html.Span(channel_hint, style={'fontSize': '12px', 'fontWeight': 'bold', 'color': '#fa8c16', 'marginLeft': '8px'}) if channel_hint else None
        ], className="mb-2 p-2", style={'backgroundColor': '#e6f7ff', 'borderRadius': '4px', 'border': '1px solid #91d5ff'})
    else:
        # 对比模式，显示日期范围
        if date_range_info:
            period_hint = html.Div([
                html.I(className="bi bi-clock-history me-1", style={'color': '#52c41a'}),
                html.Span("对比周期：", className="text-muted", style={'fontSize': '12px'}),
                html.Span(f"近{days_range}天 vs 前{days_range}天", 
                         style={'fontSize': '12px', 'fontWeight': 'bold', 'color': '#52c41a', 'marginLeft': '4px'}),
                html.Span(f"（{date_range_info.get('recent_start', '')}~{date_range_info.get('recent_end', '')} vs {date_range_info.get('previous_start', '')}~{date_range_info.get('previous_end', '')}）", 
                         className="text-muted ms-1", style={'fontSize': '11px'}),
                html.Span(channel_hint, style={'fontSize': '12px', 'fontWeight': 'bold', 'color': '#fa8c16', 'marginLeft': '8px'}) if channel_hint else None
            ], className="mb-2 p-2", style={'backgroundColor': '#f6ffed', 'borderRadius': '4px', 'border': '1px solid #b7eb8f'})
        else:
            period_hint = html.Div([
                html.I(className="bi bi-clock-history me-1", style={'color': '#52c41a'}),
                html.Span(f"对比周期：近{days_range}天 vs 前{days_range}天", 
                         style={'fontSize': '12px', 'fontWeight': 'bold', 'color': '#52c41a'}),
                html.Span(channel_hint, style={'fontSize': '12px', 'fontWeight': 'bold', 'color': '#fa8c16', 'marginLeft': '8px'}) if channel_hint else None
            ], className="mb-2 p-2", style={'backgroundColor': '#f6ffed', 'borderRadius': '4px', 'border': '1px solid #b7eb8f'})
    
    # V7.2修复：创建列定义，并为趋势列添加日期范围，同时将"四象限分类"重命名为"六象限分类"
    columns_def = []
    for col in display_df.columns:
        if col == '前期销量' and date_range_info:
            col_name = f"前期销量\n({date_range_info.get('previous_start', '')}~{date_range_info.get('previous_end', '')})"
        elif col == '近期销量' and date_range_info:
            col_name = f"近期销量\n({date_range_info.get('recent_start', '')}~{date_range_info.get('recent_end', '')})"
        elif col == '四象限分类':
            col_name = '六象限分类'  # V7.2：显示名称更新为六象限
        elif col == '八象限分类':
            col_name = '六象限分类'  # V7.2：兼容旧版，统一显示为六象限
        else:
            col_name = col
        columns_def.append({'name': col_name, 'id': col})
    
    # V8.9: 使用智能分页表格
    print(f"[V8.9分页] 准备创建分页表格，数据量: {len(display_df)}行")
    
    # V8.10.1修复：定义样式配置
    style_data_conditional = [
        # V4.0新增：ABC分类颜色
        {'if': {'filter_query': '{ABC描述} contains "核心"', 'column_id': 'ABC描述'}, 
         'color': '#fa541c', 'fontWeight': 'bold'},
        {'if': {'filter_query': '{ABC描述} contains "常规"', 'column_id': 'ABC描述'}, 
         'color': '#1890ff', 'fontWeight': 'bold'},
        {'if': {'filter_query': '{ABC描述} contains "长尾"', 'column_id': 'ABC描述'}, 
         'color': '#8c8c8c'},
        # V7.0: 六象限分类列颜色
        {'if': {'filter_query': '{四象限分类} contains "🌟 明星商品"', 'column_id': '四象限分类'}, 
         'color': '#52c41a', 'fontWeight': 'bold'},
        {'if': {'filter_query': '{四象限分类} contains "🔥 畅销商品"', 'column_id': '四象限分类'}, 
         'color': '#ff9800', 'fontWeight': 'bold'},
        {'if': {'filter_query': '{四象限分类} contains "💎 潜力商品"', 'column_id': '四象限分类'}, 
         'color': '#722ed1', 'fontWeight': 'bold'},
        {'if': {'filter_query': '{四象限分类} contains "🎯 策略引流"', 'column_id': '四象限分类'}, 
         'color': '#fa8c16', 'fontWeight': 'bold'},
        {'if': {'filter_query': '{四象限分类} contains "⚡ 自然引流"', 'column_id': '四象限分类'}, 
         'color': '#1890ff', 'fontWeight': 'bold'},
        {'if': {'filter_query': '{四象限分类} contains "🐌 低效商品"', 'column_id': '四象限分类'}, 
         'color': '#ff4d4f', 'fontWeight': 'bold'},
        # V5.0: 特殊标记列颜色
        {'if': {'filter_query': '{特殊标记} contains "🚨"', 'column_id': '特殊标记'}, 
         'color': '#cf1322', 'fontWeight': 'bold'},
        {'if': {'filter_query': '{特殊标记} contains "📦"', 'column_id': '特殊标记'}, 
         'color': '#fa8c16'},
        # 问题标签列 - 有问题的红色警示
        {'if': {'filter_query': '{问题标签} contains "亏损"', 'column_id': '问题标签'}, 
         'color': '#cf1322', 'fontWeight': 'bold'},
        {'if': {'filter_query': '{问题标签} contains "低频"', 'column_id': '问题标签'}, 
         'color': '#fa8c16'},
        {'if': {'filter_query': '{问题标签} contains "低盈利"', 'column_id': '问题标签'}, 
         'color': '#fa8c16'},
        {'if': {'filter_query': '{问题标签} contains "高营销"', 'column_id': '问题标签'}, 
         'color': '#ff4d4f'},
        {'if': {'filter_query': '{问题标签} contains "低动销"', 'column_id': '问题标签'}, 
         'color': '#8c8c8c'},
        # V6.0: 销量差异列颜色（正值绿色，负值红色）
        {'if': {'filter_query': '{销量差异} contains "+"', 'column_id': '销量差异'}, 
         'color': '#52c41a', 'fontWeight': 'bold'},
        {'if': {'filter_query': '{销量差异} contains "-"', 'column_id': '销量差异'}, 
         'color': '#ff4d4f', 'fontWeight': 'bold'},
        {'if': {'filter_query': '{销量差异} = "持平"', 'column_id': '销量差异'}, 
         'color': '#8c8c8c'},
        # 斑马纹
        {'if': {'row_index': 'odd'}, 'backgroundColor': '#fafafa'},
    ]
    
    style_cell_conditional = [
        {'if': {'column_id': '排名'}, 'minWidth': '50px', 'width': '60px', 'maxWidth': '70px', 'textAlign': 'center'},
        {'if': {'column_id': '渠道'}, 'minWidth': '70px', 'width': '90px', 'maxWidth': '120px', 'textAlign': 'center'},
        {'if': {'column_id': '商品名称'}, 'minWidth': '120px', 'maxWidth': '250px'},
        {'if': {'column_id': '一级分类名'}, 'minWidth': '70px', 'maxWidth': '120px'},
        {'if': {'column_id': '四象限分类'}, 'minWidth': '90px', 'maxWidth': '130px'},
        # V8.10.3：删除特殊标记列宽设置
        {'if': {'column_id': '动销指数'}, 'minWidth': '70px', 'width': '80px', 'textAlign': 'center'},
        {'if': {'column_id': '问题标签'}, 'minWidth': '80px', 'maxWidth': '150px'},
        {'if': {'column_id': '业务建议'}, 'minWidth': '120px', 'maxWidth': '200px'},
        {'if': {'column_id': '综合利润率'}, 'minWidth': '70px', 'width': '90px', 'textAlign': 'right'},
        # V8.10.3：删除售罄率、营销占比、库存周转天数列宽设置
        {'if': {'column_id': '销量'}, 'minWidth': '60px', 'width': '75px', 'textAlign': 'right'},
        {'if': {'column_id': '销售额'}, 'minWidth': '80px', 'width': '100px', 'textAlign': 'right'},
        # V6.0: 趋势对比列宽设置
        {'if': {'column_id': '周期总销量'}, 'minWidth': '70px', 'width': '85px', 'textAlign': 'right'},
        {'if': {'column_id': '前期销量'}, 'minWidth': '90px', 'width': '110px', 'textAlign': 'right'},
        {'if': {'column_id': '近期销量'}, 'minWidth': '90px', 'width': '110px', 'textAlign': 'right'},
        {'if': {'column_id': '销量差异'}, 'minWidth': '70px', 'width': '85px', 'textAlign': 'center'},
        {'if': {'column_id': '趋势标签'}, 'minWidth': '90px', 'width': '110px', 'textAlign': 'center'},
    ]
    
    # V8.10.1修复：传递自定义列定义和样式配置
    print(f"[V8.10.1调试] 准备调用create_paginated_datatable")
    print(f"[V8.10.1调试] display_df.shape = {display_df.shape}")
    print(f"[V8.10.1调试] columns_def数量 = {len(columns_def)}")
    print(f"[V8.10.1调试] 前3个columns_def = {columns_def[:3]}")
    
    # 创建分页表格（自动根据数据量选择分页策略）
    paginated_table = create_paginated_datatable(
        df=display_df,
        table_id='scoring-detail-table',
        page_size=100,  # 每页100行
        max_height='600px',
        enable_sort=True,
        enable_filter=False,  # 禁用内置筛选，避免英文显示
        columns=columns_def,  # V8.10.1：传递自定义列定义
        style_data_conditional=style_data_conditional,  # V8.10.1：传递样式配置
        style_cell_conditional=style_cell_conditional  # V8.10.1：传递单元格样式
    )
    
    print(f"[V8.10.1调试] create_paginated_datatable 返回成功")
    
    # V8.10.1紧急修复：暂时使用备份DataTable来测试
    print(f"[V8.10.1紧急修复] 使用备份DataTable进行测试")
    
    return html.Div([
        period_hint,  # 周期说明提示
        html.Div([
            html.Span(f"共 {len(display_df)} 个商品", className="text-muted fw-bold", style={'fontSize': '14px'}),
        ], className="mb-2"),
        
        # V8.10.1紧急修复：暂时禁用paginated_table，使用备份DataTable
        # paginated_table,
        
        # 注意：样式已通过 DataTable 的 style_cell、style_header、style_data_conditional 属性应用
        # Dash 3.x 不再支持 html.Style()，所有样式通过组件属性或 assets/custom.css 文件应用
        
        # 原有的DataTable配置（作为备份，如果分页组件失败）
        html.Div(id='scoring-detail-table-backup', style={'display': 'block'}, children=[
            dash_table.DataTable(
                id='scoring-detail-table-original',
                data=display_df.head(500).to_dict('records'),  # 限制500行
                columns=columns_def,
                style_table={'overflowX': 'auto', 'borderRadius': '8px'},
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
                # V4.0新增：ABC分类颜色
                {'if': {'filter_query': '{ABC描述} contains "核心"', 'column_id': 'ABC描述'}, 
                 'color': '#fa541c', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{ABC描述} contains "常规"', 'column_id': 'ABC描述'}, 
                 'color': '#1890ff', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{ABC描述} contains "长尾"', 'column_id': 'ABC描述'}, 
                 'color': '#8c8c8c'},
                # V7.0: 六象限分类列颜色
                {'if': {'filter_query': '{四象限分类} contains "🌟 明星商品"', 'column_id': '四象限分类'}, 
                 'color': '#52c41a', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{四象限分类} contains "🔥 畅销商品"', 'column_id': '四象限分类'}, 
                 'color': '#ff9800', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{四象限分类} contains "💎 潜力商品"', 'column_id': '四象限分类'}, 
                 'color': '#722ed1', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{四象限分类} contains "🎯 策略引流"', 'column_id': '四象限分类'}, 
                 'color': '#fa8c16', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{四象限分类} contains "⚡ 自然引流"', 'column_id': '四象限分类'}, 
                 'color': '#1890ff', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{四象限分类} contains "🐌 低效商品"', 'column_id': '四象限分类'}, 
                 'color': '#ff4d4f', 'fontWeight': 'bold'},
                # 兼容旧版八象限分类列颜色
                {'if': {'filter_query': '{八象限分类} contains "🌟 明星商品"', 'column_id': '八象限分类'}, 
                 'color': '#52c41a', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{八象限分类} contains "🔥 畅销商品"', 'column_id': '八象限分类'}, 
                 'color': '#ff9800', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{八象限分类} contains "💎 潜力商品"', 'column_id': '八象限分类'}, 
                 'color': '#722ed1', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{八象限分类} contains "🎯 策略引流"', 'column_id': '八象限分类'}, 
                 'color': '#fa8c16', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{八象限分类} contains "⚡ 自然引流"', 'column_id': '八象限分类'}, 
                 'color': '#1890ff', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{八象限分类} contains "🐌 低效商品"', 'column_id': '八象限分类'}, 
                 'color': '#ff4d4f', 'fontWeight': 'bold'},
                # V5.0: 特殊标记列颜色
                {'if': {'filter_query': '{特殊标记} contains "🚨"', 'column_id': '特殊标记'}, 
                 'color': '#cf1322', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{特殊标记} contains "📦"', 'column_id': '特殊标记'}, 
                 'color': '#fa8c16'},
                # 问题标签列 - 有问题的红色警示
                {'if': {'filter_query': '{问题标签} contains "亏损"', 'column_id': '问题标签'}, 
                 'color': '#cf1322', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{问题标签} contains "低频"', 'column_id': '问题标签'}, 
                 'color': '#fa8c16'},
                {'if': {'filter_query': '{问题标签} contains "低盈利"', 'column_id': '问题标签'}, 
                 'color': '#fa8c16'},
                {'if': {'filter_query': '{问题标签} contains "高营销"', 'column_id': '问题标签'}, 
                 'color': '#ff4d4f'},
                {'if': {'filter_query': '{问题标签} contains "低动销"', 'column_id': '问题标签'}, 
                 'color': '#8c8c8c'},
                # V7.4：删除评分等级列颜色（评分体系已删除）
                # V6.0: 销量差异列颜色（正值绿色，负值红色）
                {'if': {'filter_query': '{销量差异} contains "+"', 'column_id': '销量差异'}, 
                 'color': '#52c41a', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{销量差异} contains "-"', 'column_id': '销量差异'}, 
                 'color': '#ff4d4f', 'fontWeight': 'bold'},
                {'if': {'filter_query': '{销量差异} = "持平"', 'column_id': '销量差异'}, 
                 'color': '#8c8c8c'},
                # 斑马纹
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#fafafa'},
            ],
            page_size=15,
            page_action='native',
            sort_action='native',
            # 移除原生筛选，避免英文显示
            filter_action='none',
            # 优化列宽：使用minWidth和maxWidth而不是固定width
            style_cell_conditional=[
                {'if': {'column_id': '排名'}, 'minWidth': '50px', 'width': '60px', 'maxWidth': '70px', 'textAlign': 'center'},
                {'if': {'column_id': '渠道'}, 'minWidth': '70px', 'width': '90px', 'maxWidth': '120px', 'textAlign': 'center'},
                {'if': {'column_id': '商品名称'}, 'minWidth': '120px', 'maxWidth': '250px'},
                {'if': {'column_id': '一级分类名'}, 'minWidth': '70px', 'maxWidth': '120px'},
                # V7.4：删除评分字段的列宽配置
                {'if': {'column_id': '四象限分类'}, 'minWidth': '90px', 'maxWidth': '130px'},
                {'if': {'column_id': '八象限分类'}, 'minWidth': '90px', 'maxWidth': '130px'},  # 兼容旧版
                # V8.10.3：删除特殊标记列宽设置
                {'if': {'column_id': '动销指数'}, 'minWidth': '70px', 'width': '80px', 'textAlign': 'center'},
                {'if': {'column_id': '问题标签'}, 'minWidth': '80px', 'maxWidth': '150px'},
                {'if': {'column_id': '业务建议'}, 'minWidth': '120px', 'maxWidth': '200px'},
                {'if': {'column_id': '综合利润率'}, 'minWidth': '70px', 'width': '90px', 'textAlign': 'right'},
                # V8.10.3：删除售罄率、营销占比、库存周转天数列宽设置
                {'if': {'column_id': '销量'}, 'minWidth': '60px', 'width': '75px', 'textAlign': 'right'},
                {'if': {'column_id': '销售额'}, 'minWidth': '80px', 'width': '100px', 'textAlign': 'right'},
                # V6.0: 趋势对比列宽设置
                {'if': {'column_id': '周期总销量'}, 'minWidth': '70px', 'width': '85px', 'textAlign': 'right'},
                {'if': {'column_id': '前期销量'}, 'minWidth': '90px', 'width': '110px', 'textAlign': 'right'},
                {'if': {'column_id': '近期销量'}, 'minWidth': '90px', 'width': '110px', 'textAlign': 'right'},
                {'if': {'column_id': '销量差异'}, 'minWidth': '70px', 'width': '85px', 'textAlign': 'center'},
                    {'if': {'column_id': '趋势标签'}, 'minWidth': '90px', 'width': '110px', 'textAlign': 'center'},
                ],
            )
        ])
    ], className="mt-2")


def get_product_scoring_export_data(df: pd.DataFrame, days_range: int = 0) -> pd.DataFrame:
    """获取商品评分导出数据（V7.2 修复版本）
    
    确保导出数据与看板表格展示完全一致，包括：
    - 相同的字段顺序
    - 相同的字段名称
    - 相同的日期范围和计算逻辑
    - V5.0新增：四象限分类、动销指数、特殊标记
    - V7.2修复：支持日期范围参数，与看板显示保持一致
    
    Parameters:
    -----------
    df : DataFrame - 原始数据
    days_range : int - 日期范围（0=全部数据，7/15/30/60/90=指定天数）
    """
    # V7.2修复：使用与看板显示相同的计算逻辑
    if days_range == 0:
        # 全部数据，不参与对比
        product_scores = calculate_enhanced_product_scores(df)
    else:
        # 指定天数，参与对比（与看板显示一致）
        product_scores = calculate_enhanced_product_scores_with_trend(df, days=days_range)
    
    if product_scores.empty:
        return pd.DataFrame()
    
    # V7.2修复：添加调试信息，确保导出数据与看板一致
    print(f"\n[导出数据调试] days_range={days_range}, 数据行数={len(product_scores)}")
    if '四象限分类' in product_scores.columns:
        export_quadrant_counts = product_scores['四象限分类'].value_counts()
        print(f"[导出数据调试] 六象限分布:")
        for quadrant, count in export_quadrant_counts.items():
            print(f"  {quadrant}: {count}个")
    
    # 导出列 - V7.4更新：删除评分字段
    # V8.10.3：删除重复和低价值字段（实收价格、特殊标记、营销占比、售罄率、库存周转天数）
    export_cols = [
        # 基础信息
        '排名', 'ABC分类', 'ABC描述', '店内码', '商品名称', '一级分类名', '三级分类名',
        # 价格与成本
        '商品原价', '商品实售价', '单品成本', 
        # 利润率
        '综合利润率', '定价利润率',
        # 销售数据
        '销量', '动销指数', '销售额', '销售额占比', '累计销售额占比', '利润额', '营销成本', '订单数',
        # V7.4：六象限分类与诊断（删除评分字段）
        # V8.10.3：删除重复和低价值字段（特殊标记、营销占比、售罄率、库存周转天数）
        '六象限分类', '问题标签', '业务建议',
        # 详细指标
        '库存',
        # V5.0：特殊标记
        '是否低频', '是否亏损'
    ]
    
    # 兼容旧字段名：如果没有新字段，尝试使用旧字段
    if '综合利润率' not in product_scores.columns and '毛利率' in product_scores.columns:
        product_scores['综合利润率'] = product_scores['毛利率']
    
    # V7.2修复：将"四象限分类"重命名为"六象限分类"（用于导出）
    if '四象限分类' in product_scores.columns:
        product_scores = product_scores.copy()  # 避免修改原数据
        product_scores['六象限分类'] = product_scores['四象限分类']
    # 兼容旧版：如果没有四象限分类，使用八象限分类
    elif '八象限分类' in product_scores.columns:
        product_scores = product_scores.copy()
        product_scores['六象限分类'] = product_scores['八象限分类']
    
    available_cols = [c for c in export_cols if c in product_scores.columns]
    return product_scores[available_cols]


# ==================== V5.3：四象限趋势分析功能（简化版 - 前后对半分对比）====================
# 功能：对比范围切换(15天/30天) + 前后对半分对比 + 期初期末日期展示 + 店内码支持

# 阈值常量
PROFIT_CHANGE_THRESHOLD = 5.0   # 利润率变化阈值：±5%
SALES_CHANGE_THRESHOLD = 0.15   # 动销变化阈值：±0.15（0-1范围）


def calculate_period_comparison_quadrants(df, days_range=30, profit_threshold=30.0):
    """
    V7.1：计算等长周期的六象限对比（与评分概览逻辑一致）
    
    核心逻辑（等长对比，更公平）：
    - 7天模式：前7天（期初） vs 后7天（期末），共需14天数据
    - 15天模式：前15天（期初） vs 后15天（期末），共需30天数据
    - 30天模式：前30天（期初） vs 后30天（期末），共需60天数据
    - 60天模式：前60天（期初） vs 后60天（期末），共需120天数据
    - 90天模式：前90天（期初） vs 后90天（期末），共需180天数据
    
    Parameters:
    -----------
    df : DataFrame - 原始数据
    days_range : int - 单个周期天数（7/15/30/60/90天）
    profit_threshold : float - 利润率阈值（默认30%）
        
    Returns:
    --------
    dict : 包含期初期末数据、商品详情、迁移统计等
    """
    try:
        # 确保日期字段存在
        if '日期' not in df.columns:
            return None
        
        df = df.copy()
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        df = df.dropna(subset=['日期'])
        
        if len(df) == 0:
            return None
        
        # V7.2：智能等长周期对比（根据实际数据量自动调整）
        max_date = df['日期'].max()
        actual_min = df['日期'].min()
        actual_days = (max_date - actual_min).days + 1
        
        print(f"📊 [趋势对比] 实际数据范围: {actual_min.strftime('%Y-%m-%d')} ~ {max_date.strftime('%Y-%m-%d')} ({actual_days}天)")
        
        # 智能调整：如果数据不足，自动使用实际数据量的一半作为对比周期
        if actual_days < days_range * 2:
            # 数据不足，使用实际数据的一半
            adjusted_days = actual_days // 2
            if adjusted_days < 3:  # 至少需要3天数据才能对比
                print(f"⚠️ [趋势对比] 数据太少：只有{actual_days}天，无法进行对比（至少需要6天）")
                return None
            print(f"⚠️ [趋势对比] 数据不足：期望{days_range * 2}天，实际{actual_days}天")
            print(f"✅ [趋势对比] 自动调整为 {adjusted_days}天 vs {adjusted_days}天")
            days_range = adjusted_days
        
        # 等长对比：前 days_range 天 vs 后 days_range 天
        # 从最新日期往前推算
        last_end = max_date
        last_start = last_end - pd.Timedelta(days=days_range - 1)
        first_end = last_start - pd.Timedelta(days=1)
        first_start = first_end - pd.Timedelta(days=days_range - 1)
        
        # 确保不超出数据范围
        if first_start < actual_min:
            first_start = actual_min
            first_end = first_start + pd.Timedelta(days=days_range - 1)
            last_start = first_end + pd.Timedelta(days=1)
            last_end = last_start + pd.Timedelta(days=days_range - 1)
        
        df_first = df[(df['日期'] >= first_start) & (df['日期'] <= first_end)].copy()  # 期初
        df_last = df[(df['日期'] >= last_start) & (df['日期'] <= last_end)].copy()  # 期末
        
        if df_first.empty or df_last.empty:
            return None
        
        # 期初期末日期范围（格式化显示）
        first_start_str = df_first['日期'].min().strftime('%m-%d')
        first_end_str = df_first['日期'].max().strftime('%m-%d')
        last_start_str = df_last['日期'].min().strftime('%m-%d')
        last_end_str = df_last['日期'].max().strftime('%m-%d')
        first_days = (df_first['日期'].max() - df_first['日期'].min()).days + 1
        last_days = (df_last['日期'].max() - df_last['日期'].min()).days + 1
        
        date_info = {
            'first_range': f"{first_start_str}~{first_end_str}",
            'last_range': f"{last_start_str}~{last_end_str}",
            'first_days': first_days,
            'last_days': last_days,
            'total_days': actual_days,
            'actual_days_range': days_range  # 实际使用的对比天数
        }
        
        print(f"✅ [趋势对比] 期初: {date_info['first_range']} ({first_days}天) vs 期末: {date_info['last_range']} ({last_days}天)")
        
        # 获取库存字段
        stock_col = None
        for col in ['库存', '剩余库存', 'stock']:
            if col in df.columns:
                stock_col = col
                break
        
        def aggregate_period_data(period_df):
            """聚合周期数据到商品级别"""
            # 获取商品聚合的key字段（优先店内码）
            from components.today_must_do.diagnosis_analysis import get_product_group_key
            group_key = get_product_group_key(period_df)
            
            agg_dict = {'订单ID': 'nunique'}
            
            if '预计订单收入' in period_df.columns:
                agg_dict['预计订单收入'] = 'sum'
            elif '销售额' in period_df.columns:
                agg_dict['销售额'] = 'sum'
            
            if '利润额' in period_df.columns:
                agg_dict['利润额'] = 'sum'
            
            sales_col = '月售' if '月售' in period_df.columns else '销量'
            if sales_col in period_df.columns:
                agg_dict[sales_col] = 'sum'
            
            if '实收价格' in period_df.columns:
                agg_dict['实收价格'] = 'mean'
            
            if stock_col and stock_col in period_df.columns:
                agg_dict[stock_col] = 'last'
            
            # 保留商品名称字段（如果用店内码作为key）
            if group_key != '商品名称' and '商品名称' in period_df.columns:
                agg_dict['商品名称'] = 'first'
            
            # 保留店内码字段（如果用商品名称作为key）
            if group_key != '店内码' and '店内码' in period_df.columns:
                agg_dict['店内码'] = 'first'
            
            if '一级分类名' in period_df.columns:
                agg_dict['一级分类名'] = 'first'
            
            product_agg = period_df.groupby(group_key).agg(agg_dict).reset_index()
            
            # 统一字段名
            rename_map = {
                '订单ID': '订单数',
                '预计订单收入': '销售额',
                '月售': '销量',
                '实收价格': '售价'
            }
            if stock_col:
                rename_map[stock_col] = '库存'
            product_agg.rename(columns=rename_map, inplace=True)
            
            # 确保必要字段
            for col, default in [('销量', 0), ('订单数', 1), ('利润额', 0), ('销售额', 0), ('库存', -1), ('售价', 0)]:
                if col not in product_agg.columns:
                    product_agg[col] = default
            
            # 计算利润率
            product_agg['利润率'] = np.where(
                product_agg['销售额'] > 0,
                product_agg['利润额'] / product_agg['销售额'] * 100,
                0
            )
            
            # 计算动销指数（标准化）
            min_sales = product_agg['销量'].min()
            max_sales = product_agg['销量'].max()
            sales_range = max_sales - min_sales if max_sales > min_sales else 1
            
            min_orders = product_agg['订单数'].min()
            max_orders = product_agg['订单数'].max()
            orders_range = max_orders - min_orders if max_orders > min_orders else 1
            
            product_agg['动销指数'] = (
                0.6 * (product_agg['销量'] - min_sales) / sales_range + 
                0.4 * (product_agg['订单数'] - min_orders) / orders_range
            )
            
            # V7.0 六象限判定（与评分概览逻辑一致）
            sales_threshold = product_agg['动销指数'].median()
            profit_median = product_agg['利润率'].median()
            
            # 极端引流品识别阈值
            extreme_low_price = 0.01  # 实售价≤0.01元
            extreme_low_margin = -50   # 利润率≤-50%
            min_sales_for_attraction = 20  # 最低销量要求
            
            def classify_quadrant_v7(row):
                """V7.0 六象限分类（与评分概览一致）"""
                profit = row['利润率']
                sales_idx = row['动销指数']
                sales_qty = row['销量']
                price = row['售价']
                
                # 1. 策略引流品（极端引流）
                is_extreme_low_price = (price <= extreme_low_price and sales_qty >= min_sales_for_attraction)
                is_extreme_low_margin = (profit <= extreme_low_margin and sales_qty >= min_sales_for_attraction)
                if is_extreme_low_price or is_extreme_low_margin:
                    return '🎯 策略引流'
                
                # 2. 明星商品（高利润+高动销+单品价值高）
                single_value = row['利润额'] / sales_qty if sales_qty > 0 else 0
                if profit > profit_median and sales_idx > sales_threshold and single_value >= 0.5:
                    return '🌟 明星商品'
                
                # 3. 畅销刚需（高动销+正常利润）
                if sales_idx > sales_threshold and profit > 0 and profit <= profit_median:
                    return '🔥 畅销刚需'
                
                # 4. 潜力商品（高利润+低动销）
                if profit > profit_median and sales_idx <= sales_threshold:
                    return '💎 潜力商品'
                
                # 5. 自然引流（低利润+高动销，但不是极端引流）
                if sales_idx > sales_threshold and profit <= 0:
                    return '⚡ 自然引流'
                
                # 6. 低效商品（低利润+低动销）
                return '🐌 低效商品'
            
            product_agg['象限'] = product_agg.apply(classify_quadrant_v7, axis=1)
            
            # 检查并处理重复的商品名称
            if product_agg['商品名称'].duplicated().any():
                print(f"⚠️ [六象限分析] 发现 {product_agg['商品名称'].duplicated().sum()} 个重复商品名称，已按销量去重")
                # 按销量降序排序后去重，保留销量最大的
                product_agg = product_agg.sort_values('销量', ascending=False).drop_duplicates('商品名称', keep='first')
            
            return product_agg.set_index('商品名称').to_dict('index')
        
        # 分别聚合期初和期末数据
        first_product_data = aggregate_period_data(df_first)
        last_product_data = aggregate_period_data(df_last)
        
        # 所有商品
        all_products = set(first_product_data.keys()) | set(last_product_data.keys())
        
        # 构建商品详情（包含期初期末对比）
        product_details = {}
        for product in all_products:
            first_data = first_product_data.get(product, None)
            last_data = last_product_data.get(product, None)
            
            if first_data and last_data:
                product_details[product] = {
                    '店内码': last_data.get('店内码', first_data.get('店内码', '')),
                    '分类': last_data.get('一级分类名', first_data.get('一级分类名', '')),
                    '期初象限': first_data.get('象限', '无数据'),
                    '期末象限': last_data.get('象限', '无数据'),
                    '期初利润率': first_data.get('利润率', 0),
                    '期末利润率': last_data.get('利润率', 0),
                    '期初动销': first_data.get('动销指数', 0),
                    '期末动销': last_data.get('动销指数', 0),
                    '期初售价': first_data.get('售价', 0),
                    '期末售价': last_data.get('售价', 0),
                    '期初销量': first_data.get('销量', 0),
                    '期末销量': last_data.get('销量', 0),
                    '期初库存': first_data.get('库存', -1),
                    '期末库存': last_data.get('库存', -1),
                }
        
        # V7.0 统计期初期末各象限商品数（六象限）
        first_counts = {
            '🎯 策略引流': 0, '🌟 明星商品': 0, '🔥 畅销刚需': 0,
            '💎 潜力商品': 0, '⚡ 自然引流': 0, '🐌 低效商品': 0
        }
        last_counts = {
            '🎯 策略引流': 0, '🌟 明星商品': 0, '🔥 畅销刚需': 0,
            '💎 潜力商品': 0, '⚡ 自然引流': 0, '🐌 低效商品': 0
        }
        
        for data in first_product_data.values():
            q = data.get('象限', '无数据')
            if q in first_counts:
                first_counts[q] += 1
        
        for data in last_product_data.values():
            q = data.get('象限', '无数据')
            if q in last_counts:
                last_counts[q] += 1
        
        # 统计迁移路径
        migrations = {}
        for product, details in product_details.items():
            from_q = details['期初象限']
            to_q = details['期末象限']
            key = (from_q, to_q)
            if key not in migrations:
                migrations[key] = []
            migrations[key].append(product)
        
        return {
            'date_info': date_info,
            'days_range': days_range,
            'first_product_data': first_product_data,
            'last_product_data': last_product_data,
            'product_details': product_details,
            'first_counts': first_counts,
            'last_counts': last_counts,
            'migrations': migrations,
            'total_products': len(all_products)
        }
        
    except Exception as e:
        print(f"❌ [V5.3对比分析] 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def calculate_time_period_quadrants_v2(df, period='week', profit_threshold=30.0):
    """
    V5.2：计算不同时间周期的四象限分类（全新重构）
    
    新增功能：
    1. 保存期初/期末的详细指标（用于诊断原因）
    2. 支持智能周期选择
    3. 返回更丰富的统计数据
    
    Parameters:
    -----------
    df : DataFrame - 原始数据
    period : str - 'day'(日) / 'week'(周) / 'month'(月)
    profit_threshold : float - 利润率阈值（默认30%）
        
    Returns:
    --------
    dict : 包含周期数据、商品详情、迁移统计等
    """
    try:
        # 确保日期字段存在
        if '日期' not in df.columns:
            return None
        
        df = df.copy()
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        df = df.dropna(subset=['日期'])
        
        if len(df) == 0:
            return None
        
        # 按周期分组
        if period == 'day':
            df['周期'] = df['日期'].dt.strftime('%Y-%m-%d')
            period_label = '日'
        elif period == 'week':
            df['周期'] = df['日期'].dt.to_period('W-MON').astype(str)
            period_label = '周'
        elif period == 'month':
            df['周期'] = df['日期'].dt.to_period('M').astype(str)
            period_label = '月'
        else:
            return None
        
        periods = sorted(df['周期'].unique())
        if len(periods) < 2:
            return None
        
        # 为每个周期计算商品指标
        period_product_data = {}  # {周期: {商品: {指标字典}}}
        
        # 获取库存字段
        stock_col = None
        for col in ['库存', '剩余库存', 'stock']:
            if col in df.columns:
                stock_col = col
                break
        
        # 获取商品聚合的key字段（优先店内码）
        from components.today_must_do.diagnosis_analysis import get_product_group_key
        group_key = get_product_group_key(df)
        
        for p in periods:
            period_df = df[df['周期'] == p].copy()
            
            # 构建聚合字典
            agg_dict = {'订单ID': 'nunique'}
            
            # 销售额字段
            if '预计订单收入' in period_df.columns:
                agg_dict['预计订单收入'] = 'sum'
            elif '销售额' in period_df.columns:
                agg_dict['销售额'] = 'sum'
            
            # 利润额
            if '利润额' in period_df.columns:
                agg_dict['利润额'] = 'sum'
            
            # 销量
            if '月售' in period_df.columns:
                agg_dict['月售'] = 'sum'
            elif '销量' in period_df.columns:
                agg_dict['销量'] = 'sum'
            
            # 售价（改为sum销售额用于后续计算加权平均）
            if '实收价格' in period_df.columns:
                agg_dict['_销售额'] = lambda x: (period_df.loc[x.index, '实收价格'] * x).sum()
            elif '商品实售价' in period_df.columns:
                agg_dict['_销售额'] = lambda x: (period_df.loc[x.index, '商品实售价'] * x).sum()
            
            # 库存
            if stock_col:
                agg_dict[stock_col] = 'last'
            
            # 保留商品名称字段（如果用店内码作为key）
            if group_key != '商品名称' and '商品名称' in period_df.columns:
                agg_dict['商品名称'] = 'first'
            
            # 保留店内码字段（如果用商品名称作为key）
            if group_key != '店内码' and '店内码' in period_df.columns:
                agg_dict['店内码'] = 'first'
            
            product_agg = period_df.groupby(group_key).agg(agg_dict).reset_index()
            
            # 统一字段名
            rename_map = {
                '订单ID': '订单数',
                '预计订单收入': '销售额',
                '月售': '销量'
            }
            if stock_col:
                rename_map[stock_col] = '库存'
            product_agg.rename(columns=rename_map, inplace=True)
            
            # 计算售价（加权平均）
            if '_销售额' in product_agg.columns and '销量' in product_agg.columns:
                product_agg['售价'] = np.where(
                    product_agg['销量'] > 0,
                    product_agg['_销售额'] / product_agg['销量'],
                    0
                )
            
            # 确保必要字段
            if '销量' not in product_agg.columns:
                product_agg['销量'] = 0
            if '订单数' not in product_agg.columns:
                product_agg['订单数'] = 1
            if '利润额' not in product_agg.columns:
                product_agg['利润额'] = 0
            if '销售额' not in product_agg.columns:
                product_agg['销售额'] = 0
            if '库存' not in product_agg.columns:
                product_agg['库存'] = -1  # -1表示无库存数据
            if '售价' not in product_agg.columns:
                product_agg['售价'] = 0
            
            # 计算利润率
            product_agg['利润率'] = np.where(
                product_agg['销售额'] > 0,
                product_agg['利润额'] / product_agg['销售额'] * 100,
                0
            )
            
            # 计算动销指数（标准化）
            min_sales = product_agg['销量'].min()
            max_sales = product_agg['销量'].max()
            sales_range = max_sales - min_sales if max_sales > min_sales else 1
            
            min_orders = product_agg['订单数'].min()
            max_orders = product_agg['订单数'].max()
            orders_range = max_orders - min_orders if max_orders > min_orders else 1
            
            product_agg['动销指数'] = (
                0.6 * (product_agg['销量'] - min_sales) / sales_range + 
                0.4 * (product_agg['订单数'] - min_orders) / orders_range
            )
            
            # 四象限判定
            sales_threshold = product_agg['动销指数'].median()
            
            def classify_quadrant(row):
                high_profit = row['利润率'] > profit_threshold
                high_sales = row['动销指数'] > sales_threshold
                if high_profit and high_sales:
                    return '🌟 明星商品'
                elif high_profit and not high_sales:
                    return '💎 潜力商品'
                elif not high_profit and high_sales:
                    return '⚡ 引流商品'
                else:
                    return '🐌 问题商品'
            
            product_agg['象限'] = product_agg.apply(classify_quadrant, axis=1)
            
            # 保存到字典
            period_product_data[p] = product_agg.set_index('商品名称').to_dict('index')
        
        # 构建商品迁移数据
        all_products = set()
        for p_data in period_product_data.values():
            all_products.update(p_data.keys())
        
        # 商品详情（包含期初期末对比）
        product_details = {}
        first_period = periods[0]
        last_period = periods[-1]
        
        for product in all_products:
            first_data = period_product_data.get(first_period, {}).get(product, None)
            last_data = period_product_data.get(last_period, {}).get(product, None)
            
            if first_data and last_data:
                product_details[product] = {
                    '期初象限': first_data.get('象限', '无数据'),
                    '期末象限': last_data.get('象限', '无数据'),
                    '期初利润率': first_data.get('利润率', 0),
                    '期末利润率': last_data.get('利润率', 0),
                    '期初动销': first_data.get('动销指数', 0),
                    '期末动销': last_data.get('动销指数', 0),
                    '期初售价': first_data.get('售价', 0),
                    '期末售价': last_data.get('售价', 0),
                    '期初销量': first_data.get('销量', 0),
                    '期末销量': last_data.get('销量', 0),
                    '期初库存': first_data.get('库存', -1),
                    '期末库存': last_data.get('库存', -1),
                }
        
        # 统计各周期各象限商品数（用于趋势图）
        quadrant_counts_by_period = {}
        for p in periods:
            counts = {'🌟 明星商品': 0, '💎 潜力商品': 0, '⚡ 引流商品': 0, '🐌 问题商品': 0}
            for product_data in period_product_data.get(p, {}).values():
                q = product_data.get('象限', '无数据')
                if q in counts:
                    counts[q] += 1
            quadrant_counts_by_period[p] = counts
        
        # 统计迁移路径
        migrations = {}
        for product, details in product_details.items():
            from_q = details['期初象限']
            to_q = details['期末象限']
            key = (from_q, to_q)
            if key not in migrations:
                migrations[key] = []
            migrations[key].append(product)
        
        return {
            'periods': periods,
            'period_label': period_label,
            'first_period': first_period,
            'last_period': last_period,
            'product_details': product_details,
            'quadrant_counts_by_period': quadrant_counts_by_period,
            'migrations': migrations,
            'period_product_data': period_product_data
        }
        
    except Exception as e:
        print(f"❌ [V5.2时间维度四象限计算] 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def diagnose_migration_reason(product_detail):
    """
    V5.2：智能诊断商品象限迁移原因
    
    基于期初期末对比，分析迁移原因
    """
    reasons = []
    
    from_q = product_detail.get('期初象限', '')
    to_q = product_detail.get('期末象限', '')
    
    profit_change = product_detail.get('期末利润率', 0) - product_detail.get('期初利润率', 0)
    sales_change = product_detail.get('期末动销', 0) - product_detail.get('期初动销', 0)
    price_change = product_detail.get('期末售价', 0) - product_detail.get('期初售价', 0)
    quantity_change = product_detail.get('期末销量', 0) - product_detail.get('期初销量', 0)
    
    start_stock = product_detail.get('期初库存', -1)
    end_stock = product_detail.get('期末库存', -1)
    
    # 1. 利润率变化诊断
    if profit_change < -PROFIT_CHANGE_THRESHOLD:
        if price_change < 0:
            reasons.append("📉 降价促销")
        else:
            reasons.append("📉 利润率下降")
    elif profit_change > PROFIT_CHANGE_THRESHOLD:
        if price_change > 0:
            reasons.append("📈 提价成功")
        else:
            reasons.append("📈 成本优化")
    
    # 2. 动销变化诊断
    if sales_change < -SALES_CHANGE_THRESHOLD:
        if end_stock == 0 and start_stock > 0:
            reasons.append("🚨 售罄缺货")
        elif quantity_change < -5:
            reasons.append("📦 销量下滑")
        else:
            reasons.append("📉 动销下降")
    elif sales_change > SALES_CHANGE_THRESHOLD:
        if start_stock == 0 and end_stock > 0:
            reasons.append("✅ 补货恢复")
        elif quantity_change > 10:
            reasons.append("🔥 销量增长")
        else:
            reasons.append("📈 动销提升")
    
    # 3. 特殊情况
    if end_stock == 0:
        if "售罄" not in str(reasons):
            reasons.append("⚠️ 当前售罄")
    
    if product_detail.get('期末销量', 0) < 3:
        reasons.append("📦 低频滞销")
    
    # 综合判断
    if not reasons:
        if from_q == to_q:
            reasons.append("➡️ 保持稳定")
        else:
            reasons.append("🔄 正常波动")
    
    return " | ".join(reasons[:3])  # 最多显示3个原因


def _create_quadrant_trend_line_chart_by_counts(quadrant_counts_by_period, periods, period_label):
    """
    V5.2内部函数：根据已统计好的象限计数创建趋势折线图
    
    与create_quadrant_trend_line_chart的区别：
    - 本函数直接接收已统计好的quadrant_counts_by_period字典
    - 而create_quadrant_trend_line_chart需要从trend_data和quadrant_data计算
    """
    try:
        # 准备数据
        x_data = []
        for p in periods:
            if period_label == '日':
                # 格式化为 MM-DD
                try:
                    x_data.append(pd.to_datetime(p).strftime('%m-%d'))
                except:
                    x_data.append(p[-5:])
            elif period_label == '周':
                x_data.append(f"第{periods.index(p)+1}周")
            else:
                x_data.append(p)
        
        # 各象限数据
        star_data = [quadrant_counts_by_period.get(p, {}).get('🌟 明星商品', 0) for p in periods]
        potential_data = [quadrant_counts_by_period.get(p, {}).get('💎 潜力商品', 0) for p in periods]
        traffic_data = [quadrant_counts_by_period.get(p, {}).get('⚡ 引流商品', 0) for p in periods]
        problem_data = [quadrant_counts_by_period.get(p, {}).get('🐌 问题商品', 0) for p in periods]
        
        option = {
            'tooltip': {
                'trigger': 'axis',
                'axisPointer': {'type': 'cross'}
            },
            'legend': {
                'data': ['🌟 明星', '💎 潜力', '⚡ 引流', '🐌 问题'],
                'top': '5%'
            },
            'grid': {
                'left': '3%', 'right': '4%', 'bottom': '3%', 'top': '18%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'boundaryGap': False,
                'data': x_data,
                'axisLabel': {'fontSize': 11}
            },
            'yAxis': {
                'type': 'value',
                'name': '商品数',
                'axisLabel': {'fontSize': 11}
            },
            'series': [
                {
                    'name': '🌟 明星',
                    'type': 'line',
                    'data': star_data,
                    'smooth': True,
                    'symbol': 'circle',
                    'symbolSize': 8,
                    'lineStyle': {'width': 3, 'color': '#52c41a'},
                    'itemStyle': {'color': '#52c41a'}
                },
                {
                    'name': '💎 潜力',
                    'type': 'line',
                    'data': potential_data,
                    'smooth': True,
                    'symbol': 'diamond',
                    'symbolSize': 8,
                    'lineStyle': {'width': 3, 'color': '#722ed1'},
                    'itemStyle': {'color': '#722ed1'}
                },
                {
                    'name': '⚡ 引流',
                    'type': 'line',
                    'data': traffic_data,
                    'smooth': True,
                    'symbol': 'triangle',
                    'symbolSize': 8,
                    'lineStyle': {'width': 3, 'color': '#1890ff'},
                    'itemStyle': {'color': '#1890ff'}
                },
                {
                    'name': '🐌 问题',
                    'type': 'line',
                    'data': problem_data,
                    'smooth': True,
                    'symbol': 'rect',
                    'symbolSize': 8,
                    'lineStyle': {'width': 3, 'color': '#f5222d'},
                    'itemStyle': {'color': '#f5222d'}
                }
            ]
        }
        
        chart_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        </head>
        <body>
            <div id="trend-chart" style="width: 100%; height: 280px;"></div>
            <script>
                var chartDom = document.getElementById('trend-chart');
                var myChart = echarts.init(chartDom);
                var option = {json.dumps(option, ensure_ascii=False)};
                myChart.setOption(option);
                window.addEventListener('resize', function() {{ myChart.resize(); }});
            </script>
        </body>
        </html>
        '''
        
        return html.Iframe(srcDoc=chart_html, style={'width': '100%', 'height': '300px', 'border': 'none'})
        
    except Exception as e:
        print(f"❌ [趋势折线图] 错误: {e}")
        return html.Div(f"图表生成失败: {e}", className="text-danger")


def create_migration_stats_table(migrations, product_details):
    """
    V5.2：创建可点击的迁移统计表格
    """
    migration_stats = []
    
    for (from_q, to_q), products in sorted(migrations.items(), key=lambda x: -len(x[1])):
        # 判断趋势
        quadrant_priority = {'🌟 明星商品': 1, '💎 潜力商品': 2, '⚡ 引流商品': 3, '🐌 问题商品': 4}
        from_p = quadrant_priority.get(from_q, 5)
        to_p = quadrant_priority.get(to_q, 5)
        
        if from_q == to_q:
            trend = "➡️ 稳定"
            trend_color = "secondary"
        elif from_p < to_p:
            trend = "📉 恶化"
            trend_color = "danger"
        else:
            trend = "📈 改善"
            trend_color = "success"
        
        migration_stats.append({
            'from_quadrant': from_q,
            'to_quadrant': to_q,
            'trend': trend,
            'trend_color': trend_color,
            'count': len(products),
            'products': products
        })
    
    return migration_stats


def create_migration_detail_table(products, product_details):
    """
    V5.2：创建迁移详情表格（包含智能原因诊断）
    """
    if not products:
        return html.Div("暂无数据", className="text-muted text-center p-3")
    
    rows = []
    for product in products[:50]:  # 限制显示50个
        detail = product_details.get(product, {})
        reason = diagnose_migration_reason(detail)
        
        rows.append({
            '商品名称': product[:20] + ('...' if len(product) > 20 else ''),
            '期初象限': detail.get('期初象限', '-'),
            '期末象限': detail.get('期末象限', '-'),
            '利润率变化': f"{detail.get('期初利润率', 0):.1f}% → {detail.get('期末利润率', 0):.1f}%",
            '动销变化': f"{detail.get('期初动销', 0):.2f} → {detail.get('期末动销', 0):.2f}",
            '销量变化': f"{int(detail.get('期初销量', 0))} → {int(detail.get('期末销量', 0))}",
            '变化原因': reason
        })
    
    if not rows:
        return html.Div("暂无数据", className="text-muted text-center p-3")
    
    df = pd.DataFrame(rows)
    
    return dash_table.DataTable(
        data=df.head(200).to_dict('records'),  # 🚀 优化：限制200行
        columns=[{'name': c, 'id': c} for c in df.columns],
        page_size=10,
        page_action='native',  # 🚀 客户端分页
        sort_action='native',  # 🚀 客户端排序
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'fontSize': '12px', 'padding': '8px', 'whiteSpace': 'normal'},
        style_header={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'},
        style_data_conditional=[
            {'if': {'filter_query': '{变化原因} contains "售罄"'}, 'backgroundColor': '#fff1f0'},
            {'if': {'filter_query': '{变化原因} contains "降价"'}, 'backgroundColor': '#fff7e6'},
            {'if': {'filter_query': '{变化原因} contains "提价"'}, 'backgroundColor': '#f6ffed'},
            {'if': {'filter_query': '{变化原因} contains "增长"'}, 'backgroundColor': '#e6fffb'},
        ]
    )


def create_quadrant_trend_section_v2(df: pd.DataFrame, period: str = 'week') -> html.Div:
    """
    V5.2：创建四象限趋势分析区域（全新版本）
    
    包含：
    1. 周期切换按钮（日/周/月）
    2. 四象限数量变化趋势图（多折线图）
    3. 象限迁移桑基图
    4. 可点击的迁移统计表格
    5. 迁移详情表格（带智能原因诊断）
    """
    if df is None or df.empty:
        return html.Div()
    
    try:
        # 计算趋势数据
        trend_data = calculate_time_period_quadrants_v2(df, period=period)
        
        if not trend_data:
            return dbc.Alert([
                html.I(className="bi bi-info-circle me-2"),
                "暂无足够数据进行趋势分析（需要至少2个周期的数据）"
            ], color="info")
        
        periods = trend_data['periods']
        period_label = trend_data['period_label']
        product_details = trend_data['product_details']
        quadrant_counts_by_period = trend_data['quadrant_counts_by_period']
        migrations = trend_data['migrations']
        
        # 1. 趋势折线图
        trend_chart = _create_quadrant_trend_line_chart_by_counts(quadrant_counts_by_period, periods, period_label)
        
        # 2. 桑基图
        sankey_chart = create_quadrant_migration_sankey_v2(migrations, periods, period_label)
        
        # 3. 迁移统计表
        migration_stats = create_migration_stats_table(migrations, product_details)
        
        # 构建迁移统计按钮列表
        migration_buttons = []
        for i, stat in enumerate(migration_stats[:12]):  # 最多显示12个
            btn_color = stat['trend_color']
            migration_buttons.append(
                dbc.Button([
                    html.Span(f"{stat['from_quadrant'][:4]} → {stat['to_quadrant'][:4]}", style={'fontSize': '11px'}),
                    html.Br(),
                    html.Span(f"{stat['count']}个", className="badge bg-light text-dark ms-1")
                ],
                id={'type': 'migration-stat-btn', 'index': i},
                color=btn_color,
                outline=True,
                size="sm",
                className="me-1 mb-1",
                style={'minWidth': '100px'}
                )
            )
        
        # 默认显示第一个迁移路径的详情
        default_detail = html.Div()
        if migration_stats:
            first_stat = migration_stats[0]
            default_detail = create_migration_detail_table(first_stat['products'], product_details)
        
        return dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H5([
                            html.I(className="bi bi-graph-up-arrow me-2"),
                            "📈 四象限趋势分析"
                        ], className="mb-0 text-primary")
                    ], width=6),
                    dbc.Col([
                        # 周期切换按钮
                        dbc.ButtonGroup([
                            dbc.Button("按日", id='trend-period-day', color="primary" if period == 'day' else "outline-secondary", size="sm"),
                            dbc.Button("按周", id='trend-period-week', color="primary" if period == 'week' else "outline-secondary", size="sm"),
                            dbc.Button("按月", id='trend-period-month', color="primary" if period == 'month' else "outline-secondary", size="sm"),
                        ], size="sm")
                    ], width=6, className="text-end")
                ], align="center")
            ], className="bg-white"),
            dbc.CardBody([
                # 周期信息
                html.Div([
                    dbc.Badge(f"分析周期：{periods[0]} ~ {periods[-1]}（共{len(periods)}个{period_label}）", color="info"),
                    dbc.Badge(f"共{len(product_details)}个商品", color="secondary", className="ms-2")
                ], className="mb-3"),
                
                # 1. 趋势折线图
                html.Div([
                    html.H6("📊 各象限商品数量变化趋势", className="mb-2"),
                    trend_chart
                ], className="mb-4"),
                
                html.Hr(),
                
                # 2. 象限迁移分析
                html.Div([
                    html.H6("🔄 象限迁移分析", className="mb-3"),
                    dbc.Row([
                        # 左侧：桑基图
                        dbc.Col([
                            sankey_chart
                        ], md=7),
                        # 右侧：迁移统计按钮
                        dbc.Col([
                            html.Small("点击查看详情：", className="text-muted d-block mb-2"),
                            html.Div(migration_buttons, className="d-flex flex-wrap")
                        ], md=5)
                    ])
                ], className="mb-4"),
                
                html.Hr(),
                
                # 3. 迁移详情表格
                html.Div([
                    html.H6([
                        "📋 迁移商品详情",
                        html.Small("（含智能原因诊断）", className="text-muted ms-2")
                    ], className="mb-2"),
                    html.Div(
                        id='migration-detail-container',
                        children=default_detail
                    )
                ])
            ])
        ], className="mb-4 shadow-sm")
        
    except Exception as e:
        print(f"❌ [V5.2趋势分析区域] 错误: {e}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"趋势分析生成失败: {e}", color="danger")


def create_quadrant_migration_sankey_v2(migrations, periods, period_label):
    """
    V5.2：创建象限迁移桑基图
    """
    try:
        if len(periods) < 2:
            return html.Div("需要至少2个周期的数据", className="text-muted text-center p-4")
        
        # 统计迁移数量
        migration_counts = {k: len(v) for k, v in migrations.items()}
        
        if not migration_counts:
            return html.Div("暂无迁移数据", className="text-muted text-center p-4")
        
        # 判断是按日还是按周
        is_daily = period_label == '日'
        
        # 构建桑基图数据
        nodes = []
        links = []
        node_set = set()
        
        quadrant_map = {
            '🌟 明星商品': {'short': '明星', 'color': '#52c41a'},
            '💎 潜力商品': {'short': '潜力', 'color': '#722ed1'},
            '⚡ 引流商品': {'short': '引流', 'color': '#1890ff'},
            '🐌 问题商品': {'short': '问题', 'color': '#f5222d'}
        }
        
        for (from_q, to_q), count in migration_counts.items():
            if count > 0:
                from_info = quadrant_map.get(from_q, {'short': from_q[:2], 'color': '#999'})
                to_info = quadrant_map.get(to_q, {'short': to_q[:2], 'color': '#999'})
                
                if is_daily:
                    try:
                        first_date = pd.to_datetime(periods[0]).strftime("%m-%d")
                        last_date = pd.to_datetime(periods[-1]).strftime("%m-%d")
                    except:
                        first_date = periods[0][-5:]
                        last_date = periods[-1][-5:]
                    source_node = f'期初({first_date})\n{from_info["short"]}'
                    target_node = f'期末({last_date})\n{to_info["short"]}'
                else:
                    source_node = f'期初\n{from_info["short"]}'
                    target_node = f'期末\n{to_info["short"]}'
                
                if source_node not in node_set:
                    nodes.append({'name': source_node, 'itemStyle': {'color': from_info['color']}})
                    node_set.add(source_node)
                
                if target_node not in node_set:
                    nodes.append({'name': target_node, 'itemStyle': {'color': to_info['color']}})
                    node_set.add(target_node)
                
                links.append({
                    'source': source_node,
                    'target': target_node,
                    'value': count,
                    'lineStyle': {'color': from_info['color'], 'opacity': 0.4}
                })
        
        option = {
            'tooltip': {'trigger': 'item'},
            'series': [{
                'type': 'sankey',
                'data': nodes,
                'links': links,
                'nodeWidth': 25,
                'nodeGap': 12,
                'orient': 'horizontal',
                'label': {'fontSize': 10, 'color': '#333'},
                'lineStyle': {'color': 'source', 'curveness': 0.5},
                'emphasis': {'focus': 'adjacency'}
            }]
        }
        
        chart_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        </head>
        <body style="margin:0;padding:0;">
            <div id="sankey-chart" style="width: 100%; height: 300px;"></div>
            <script>
                var chartDom = document.getElementById('sankey-chart');
                var myChart = echarts.init(chartDom);
                var option = {json.dumps(option, ensure_ascii=False)};
                myChart.setOption(option);
                window.addEventListener('resize', function() {{ myChart.resize(); }});
            </script>
        </body>
        </html>
        '''
        
        return html.Iframe(srcDoc=chart_html, style={'width': '100%', 'height': '310px', 'border': 'none'})
        
    except Exception as e:
        print(f"❌ [V5.2桑基图] 错误: {e}")
        return html.Div(f"图表生成失败: {e}", className="text-danger")


# 保留旧版函数兼容性
def calculate_time_period_quadrants(df, period='week', profit_threshold=30.0, start_date=None, end_date=None):
    """兼容旧版调用"""
    return calculate_time_period_quadrants_v2(df, period, profit_threshold)


def analyze_quadrant_trends(quadrant_data, periods):
    """兼容旧版 - 已废弃，返回空列表"""
    return []


def create_quadrant_migration_sankey(quadrant_data, periods, period_label):
    """兼容旧版调用"""
    return html.Div("请使用新版趋势分析", className="text-muted")


def create_quadrant_trend_section(df: pd.DataFrame, period: str = 'week') -> html.Div:
    """兼容旧版调用，重定向到V5.2"""
    return create_quadrant_trend_section_v2(df, period)


# ==================== 客单价异常诊断视图生成函数 ====================

def _create_aov_distribution_view(result: Dict, period_days: int) -> html.Div:
    """创建订单金额分布分析视图（新版：展示绝对数量变化）"""
    # 防御性检查
    if not result or 'summary' not in result or 'trend' not in result:
        print(f"❌ [DEBUG] _create_aov_distribution_view 收到无效result: {result}")
        return dbc.Alert("数据格式错误", color="danger")
    
    summary = result['summary']
    trend = result['trend']
    distribution = summary['distribution']
    
    # 汇总卡片
    summary_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-cash-coin text-primary", style={'fontSize': '2rem'}),
                        html.Div([
                            html.H3(f"¥{summary['avg_aov']:.1f}", className="mb-0 text-primary"),
                            html.Small("当前客单价", className="text-muted")
                        ], className="ms-3")
                    ], className="d-flex align-items-center")
                ])
            ])
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-arrow-up-down text-info", style={'fontSize': '2rem'}),
                        html.Div([
                            html.H3(f"{summary['aov_change_amount']:+.2f}", className="mb-0 " + 
                                   ("text-success" if summary['aov_change_amount'] >= 0 else "text-danger")),
                            html.Small("较前期变化", className="text-muted")
                        ], className="ms-3")
                    ], className="d-flex align-items-center")
                ])
            ])
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-arrow-down-circle text-danger", style={'fontSize': '2rem'}),
                        html.Div([
                            html.H3(f"{summary['max_decline_bracket']}", className="mb-0 text-danger"),
                            html.Small(f"{summary['max_decline_count']:+d}单", className="text-muted")
                        ], className="ms-3")
                    ], className="d-flex align-items-center")
                ])
            ])
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-arrow-up-circle text-success", style={'fontSize': '2rem'}),
                        html.Div([
                            html.H3(f"{summary['max_growth_bracket']}", className="mb-0 text-success"),
                            html.Small(f"{summary['max_growth_count']:+d}单", className="text-muted")
                        ], className="ms-3")
                    ], className="d-flex align-items-center")
                ])
            ])
        ], width=3)
    ], className="mb-4")
    
    # 📊 价格带分布表格
    table_data = []
    for item in distribution:
        arrow = "⬆️" if item['变化数量'] > 0 else "⬇️" if item['变化数量'] < 0 else "➡️"
        table_data.append({
            '价格带': item['价格带'],
            '历史订单数': item['历史订单数'],
            '近期订单数': item['近期订单数'],
            '变化数量': f"{item['变化数量']:+d} {arrow}",
            '历史占比': f"{item['历史占比']:.1f}%",
            '近期占比': f"{item['近期占比']:.1f}%"
        })
    
    distribution_table = html.Div([
        html.H5("📊 订单金额分布变化", className="mb-3"),
        dbc.Table.from_dataframe(
            pd.DataFrame(table_data),
            striped=True,
            bordered=True,
            hover=True,
            className="text-center"
        )
    ], className="mb-4")
    
    # 📈 趋势图（如果有ECharts）
    trend_chart = html.Div()
    if ECHARTS_AVAILABLE:
        try:
            option = {
                'title': {'text': f'近{period_days}天订单金额分布趋势', 'left': 'center'},
                'tooltip': {'trigger': 'axis'},
                'legend': {'data': ['<20元', '20-50元', '50-100元', '>100元'], 'top': 30},
                'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'containLabel': True},
                'xAxis': {'type': 'category', 'data': trend['dates']},
                'yAxis': {'type': 'value', 'name': '订单数'},
                'series': [
                    {'name': '<20元', 'type': 'line', 'stack': 'total', 'data': trend['low_price_orders'], 
                     'itemStyle': {'color': '#FF6B6B'}},
                    {'name': '20-50元', 'type': 'line', 'stack': 'total', 'data': trend['mainstream_orders'],
                     'itemStyle': {'color': '#4ECDC4'}},
                    {'name': '50-100元', 'type': 'line', 'stack': 'total', 'data': trend['mid_price_orders'],
                     'itemStyle': {'color': '#45B7D1'}},
                    {'name': '>100元', 'type': 'line', 'stack': 'total', 'data': trend['high_price_orders'],
                     'itemStyle': {'color': '#96CEB4'}}
                ]
            }
            from dash_echarts import DashECharts
            trend_chart = html.Div([
                html.H5("📈 每日订单金额分布趋势", className="mb-3"),
                DashECharts(option=option, style={'height': '400px', 'width': '100%'})
            ], className="mb-4")
        except Exception as e:
            print(f"趋势图生成失败: {str(e)}")
    
    # 💡 分析建议
    suggestions = []
    for item in distribution:
        if item['变化数量'] < -10:  # 下降超过10单
            suggestions.append(
                dbc.Alert([
                    html.Strong(f"⚠️ {item['价格带']} 订单减少 {abs(item['变化数量'])} 单"),
                    html.Br(),
                    f"建议：检查该价格带商品的库存、活动力度、竞品对比"
                ], color="warning", className="mb-2")
            )
        elif item['变化数量'] > 10:  # 增长超过10单
            suggestions.append(
                dbc.Alert([
                    html.Strong(f"✅ {item['价格带']} 订单增加 {item['变化数量']} 单"),
                    html.Br(),
                    f"建议：保持该价格带商品的供应和推广力度"
                ], color="success", className="mb-2")
            )
    
    suggestions_section = html.Div([
        html.H5("💡 分析建议", className="mb-3"),
        html.Div(suggestions if suggestions else dbc.Alert("订单结构稳定，暂无特别建议", color="info"))
    ]) if suggestions else html.Div()
    
    return html.Div([
        # 汇总卡片
        summary_cards,
        
        # 分布表格
        distribution_table,
        
        # 趋势图
        trend_chart,
        
        # 分析建议
        suggestions_section
    ])


def _create_customer_downgrade_view(result: Dict, period_days: int, channel_comparison: Dict = None) -> html.Div:
    """创建订单分布分析视图（订单维度：分析订单金额分布变化）"""
    # 防御性检查
    if not result or 'summary' not in result or 'trend' not in result:
        print(f"❌ [DEBUG] _create_customer_downgrade_view 收到无效result: {result}")
        return dbc.Alert("数据格式错误", color="danger")
    
    summary = result['summary']
    trend = result['trend']
    distribution = summary.get('distribution', [])
    
    # 渠道对比卡片（仅当有渠道对比数据时显示）
    channel_card = None
    if channel_comparison and channel_comparison.get('channel_stats'):
        channel_card = _create_channel_comparison_card(channel_comparison)
    
    if summary['total_downgrade'] == 0:
        return dbc.Alert([
            html.H5("✅ 订单金额分布稳定", className="mb-2"),
            html.P([
                f"当前平均客单价: ¥{summary['avg_aov']:.2f}，",
                f"较上期 ¥{summary.get('last_period_avg_aov', summary.get('history_avg_aov', 0)):.2f} 变化 ",
                html.Span(f"{summary['aov_change_rate']:+.1f}%", 
                         className="fw-bold text-success" if summary['aov_change_rate'] >= 0 else "fw-bold text-danger")
            ], className="mb-0")
        ], color="success")
    
    # 汇总信息（包含数据不足警告）
    header_content = [
        html.H5(f"📊 分析周期: 近{period_days}天", className="mb-2"),
        html.Div([
            html.Span("📅 上期: ", className="text-muted"),
            html.Span(f"{summary.get('last_period_start', 'N/A')} ~ {summary.get('last_period_end', 'N/A')}", 
                     className="fw-bold me-2"),
            html.Span(" vs ", className="text-muted mx-2"),
            html.Span("本期: ", className="text-muted"),
            html.Span(f"{summary.get('current_period_start', 'N/A')} ~ {summary.get('current_period_end', 'N/A')}", 
                     className="fw-bold")
        ], className="mb-2 small")
    ]
    
    # 数据不足警告
    if summary.get('data_warning'):
        header_content.append(
            dbc.Alert([
                html.I(className="bi bi-exclamation-triangle me-2"),
                html.Strong(summary['data_warning'])
            ], color="info", className="py-2 mb-2")
        )
    
    header_content.extend([
        html.P([
            f"本期平均客单价: ¥{summary['avg_aov']:.2f}，",
            f"较上期 ¥{summary.get('last_period_avg_aov', summary.get('history_avg_aov', 0)):.2f} ",
            html.Span(f"下降 ¥{abs(summary['aov_change_amount']):.2f} ({abs(summary['aov_change_rate']):.1f}%)", 
                     className="fw-bold text-danger")
        ], className="mb-2"),
        html.P([
            f"共有 {summary['total_downgrade']} 个价格带订单数下降，",
            f"其中重度下滑 {summary['severe_count']} 个，中度下滑 {summary['moderate_count']} 个"
        ], className="mb-0")
    ])
    
    header = dbc.Alert(header_content, color="warning", className="mb-3")
    
    # 订单金额分布对比表
    if distribution:
        distribution_table = dbc.Table([
            html.Thead(html.Tr([
                html.Th("价格带", style={'width': '15%'}),
                html.Th("历史期订单数", style={'width': '15%'}),
                html.Th("近期订单数", style={'width': '15%'}),
                html.Th("变化数量", style={'width': '15%'}),
                html.Th("变化率", style={'width': '15%'}),
                html.Th("历史占比", style={'width': '12.5%'}),
                html.Th("近期占比", style={'width': '12.5%'})
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(seg['价格带'], className="fw-bold"),
                    html.Td(f"{seg.get('上期订单数', seg.get('历史期订单数', 0)):,}"),
                    html.Td(f"{seg.get('本期订单数', seg.get('近期订单数', 0)):,}"),
                    html.Td(
                        f"{seg['变化数量']:+,}", 
                        className="fw-bold text-danger" if seg['变化数量'] < 0 else "fw-bold text-success"
                    ),
                    html.Td(
                        f"{seg['变化率']:+.1f}%",
                        className="fw-bold text-danger" if seg['变化率'] < 0 else "fw-bold text-success"
                    ),
                    html.Td(f"{seg.get('上期占比', seg.get('历史期占比', 0)):.1f}%"),
                    html.Td(f"{seg.get('本期占比', seg.get('近期占比', 0)):.1f}%")
                ], style={'backgroundColor': '#fff3cd'} if seg['变化率'] < -30 
                   else {'backgroundColor': '#ffe9cc'} if seg['变化率'] < -15 
                   else {})
                for seg in distribution
            ])
        ], bordered=True, hover=True, striped=True, className="mb-4")
    else:
        distribution_table = html.Div("暂无分布数据", className="text-muted")
    
    # 诊断建议
    suggestions = summary.get('suggestions', [])
    suggestions_section = None
    if suggestions:
        suggestions_section = html.Div([
            html.H5("💡 诊断建议", className="mb-3"),
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.H6(sug['问题'], className="mb-2 text-danger"),
                    html.P(sug['具体'], className="mb-2 text-muted small"),
                    html.P([html.I(className="bi bi-lightbulb me-2"), sug['建议']], className="mb-0 text-primary")
                ]) for sug in suggestions
            ], className="mb-4")
        ])
    
    # 分级卡片
    severity_cards = dbc.Row([
        # 重度下滑
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5([html.I(className="bi bi-exclamation-triangle-fill text-danger me-2"), "重度下滑"], className="mb-2"),
                    html.H3(f"{summary['severe_count']}", className="text-danger mb-2"),
                    html.Small("订单数下降>30%", className="text-muted"),
                    html.Hr(),
                    html.Div(_render_distribution_list(result['severe'], '重度'))
                ])
            ], className="border-danger")
        ], width=4),
        
        # 中度下滑
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5([html.I(className="bi bi-exclamation-circle-fill text-warning me-2"), "中度下滑"], className="mb-2"),
                    html.H3(f"{summary['moderate_count']}", className="text-warning mb-2"),
                    html.Small("订单数下降15-30%", className="text-muted"),
                    html.Hr(),
                    html.Div(_render_distribution_list(result['moderate'], '中度'))
                ])
            ], className="border-warning")
        ], width=4),
        
        # 轻度下滑
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5([html.I(className="bi bi-info-circle-fill text-info me-2"), "轻度下滑"], className="mb-2"),
                    html.H3(f"{summary['mild_count']}", className="text-info mb-2"),
                    html.Small("订单数下降<15%", className="text-muted"),
                    html.Hr(),
                    html.Div(_render_distribution_list(result['mild'], '轻度'))
                ])
            ], className="border-info")
        ], width=4)
    ], className="mb-4")
    
    # 趋势图（客单价、订单数、单均件数）
    trend_charts = _create_aov_trend_charts(trend)
    
    return html.Div([
        header,
        channel_card if channel_card else html.Div(),  # 渠道对比卡片
        trend_charts,  # 客单价趋势图（自动适应数据天数，支持点击下钻）
        html.H5("📊 订单金额分布对比（本期 vs 上期）", className="mb-3 mt-4"),
        distribution_table,
        suggestions_section if suggestions_section else html.Div(),
        html.H5("📉 问题价格带详情", className="mb-3 mt-4"),
        severity_cards
    ])


def _render_distribution_list(segments: List[Dict], severity: str) -> html.Div:
    """渲染价格带列表"""
    if not segments:
        return html.P("暂无数据", className="text-muted small")
    
    items = []
    for seg in segments[:5]:  # 最多显示5个
        items.append(html.Div([
            html.Div([
                html.Span(seg['价格带'], className="fw-bold me-2"),
                html.Span(f"{seg['变化率']:+.1f}%", 
                         className="badge bg-danger" if seg['变化率'] < -30 
                         else "badge bg-warning" if seg['变化率'] < -15 
                         else "badge bg-secondary")
            ], className="d-flex justify-content-between align-items-center mb-1"),
            html.Small([
                f"订单数: {seg.get('上期订单数', seg.get('历史期订单数', 0))} → {seg.get('本期订单数', seg.get('近期订单数', 0))} ",
                f"({seg['变化数量']:+,})"
            ], className="text-muted")
        ], className="mb-2"))
    
    return html.Div(items)


def _create_channel_comparison_card(channel_comparison: Dict) -> html.Div:
    """创建渠道对比卡片"""
    channel_stats = channel_comparison.get('channel_stats', [])
    abnormal_channels = channel_comparison.get('abnormal_channels', [])
    
    if not channel_stats:
        return html.Div()
    
    # 构建表格
    table_rows = []
    for ch in channel_stats:
        # 判断是否异常
        is_abnormal = abs(ch['变化率']) > 10
        row_style = {'backgroundColor': '#fff3cd'} if is_abnormal else {}
        
        table_rows.append(
            html.Tr([
                html.Td([
                    ch['渠道'],
                    html.Span(" ⚠️", className="text-warning") if is_abnormal else ""
                ], className="fw-bold"),
                html.Td(f"{int(ch['订单数_近期']):,}"),
                html.Td(f"¥{ch['客单价_历史']:.2f}"),
                html.Td(f"¥{ch['客单价_近期']:.2f}"),
                html.Td(
                    f"¥{ch['客单价变化']:+.2f}",
                    className="fw-bold text-danger" if ch['客单价变化'] < 0 else "fw-bold text-success"
                ),
                html.Td(
                    f"{ch['变化率']:+.1f}%",
                    className="fw-bold text-danger" if ch['变化率'] < -10
                           else "fw-bold text-warning" if abs(ch['变化率']) > 10
                           else "text-success"
                )
            ], style=row_style)
        )
    
    channel_table = dbc.Table([
        html.Thead(html.Tr([
            html.Th("渠道", style={'width': '20%'}),
            html.Th("订单数", style={'width': '15%'}),
            html.Th("历史期客单价", style={'width': '16%'}),
            html.Th("近期客单价", style={'width': '16%'}),
            html.Th("变化金额", style={'width': '16%'}),
            html.Th("变化率", style={'width': '17%'})
        ])),
        html.Tbody(table_rows)
    ], bordered=True, hover=True, striped=True, className="mb-3")
    
    # 异常提示
    alert = None
    if abnormal_channels:
        alert = dbc.Alert([
            html.Strong(f"⚠️ 发现 {len(abnormal_channels)} 个异常渠道（变化率>10%）"),
            html.Ul([
                html.Li(f"{ch['渠道']}: 客单价{ch['客单价变化']:+.2f} ({ch['变化率']:+.1f}%)")
                for ch in abnormal_channels
            ], className="mb-0 mt-2")
        ], color="warning", className="mb-3")
    
    return html.Div([
        html.H5("📱 渠道客单价对比", className="mb-3"),
        alert if alert else html.Div(),
        channel_table
    ], className="mb-4")


def _create_aov_trend_charts(trend: Dict) -> html.Div:
    """创建客单价趋势图（只显示客单价，自动适应数据天数）"""
    
    dates = trend.get('dates', [])
    aov_values = trend.get('aov_values', [])
    trend_days = trend.get('trend_days', len(dates))  # 获取实际趋势天数
    
    if not dates or not ECHARTS_AVAILABLE:
        return html.Div()
    
    # 客单价趋势图（ECharts，支持点击下钻）
    aov_option = {
        'title': {
            'text': f'📈 客单价趋势（近{trend_days}天）',
            'left': 'center',
            'textStyle': {'fontSize': 16, 'fontWeight': 'bold'}
        },
        'tooltip': {
            'trigger': 'axis',  # 轴触发，悬停显示tooltip和辅助线
            'axisPointer': {
                'type': 'cross',
                'label': {'backgroundColor': '#6a7985'}
            },
            'formatter': '{b}<br/>客单价: ¥{c}<br/><small style="color:#999">💡 点击数据点查看24小时分布</small>'
        },
        'grid': {'left': '8%', 'right': '8%', 'top': '15%', 'bottom': '12%'},
        'xAxis': {
            'type': 'category',
            'data': dates,
            'axisLabel': {'rotate': 30, 'fontSize': 11}
        },
        'yAxis': {
            'type': 'value',
            'name': '客单价(¥)',
            'axisLabel': {'formatter': '¥{value}'}
        },
        'series': [{
            'name': '客单价',
            'type': 'line',
            'data': aov_values,
            'smooth': True,
            'symbol': 'circle',
            'symbolSize': 20,  # 大幅增大点击区域，覆盖更多X轴空间
            'lineStyle': {'width': 3, 'color': '#FF6B6B'},
            'itemStyle': {
                'color': '#FF6B6B', 
                'borderWidth': 2, 
                'borderColor': '#fff'
            },
            'areaStyle': {
                'color': {
                    'type': 'linear',
                    'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                    'colorStops': [
                        {'offset': 0, 'color': 'rgba(255, 107, 107, 0.3)'},
                        {'offset': 1, 'color': 'rgba(255, 107, 107, 0.05)'}
                    ]
                }
            },
            'emphasis': {
                'scale': True,  # 鼠标悬停时放大
                'focus': 'series',
                'itemStyle': {
                    'shadowBlur': 10,
                    'shadowOffsetX': 0,
                    'shadowColor': 'rgba(255, 107, 107, 0.5)',
                    'borderWidth': 3
                }
            }
        }]
    }
    
    return html.Div([
        html.Div([
            html.Span("💡 提示：点击趋势图中的任意日期可查看当日24小时时段分析", 
                     className="text-muted small ms-2")
        ], className="mb-2"),
        DashECharts(
            option=aov_option,
            id='aov-trend-chart',
            style={'height': '350px', 'width': '100%'}
        ),
        # 小时维度下钻视图（默认隐藏）
        html.Div(
            id='aov-hourly-drill-down',
            style={'display': 'none'},
            className="mt-3"
        )
    ], className="mb-4")


# 已删除：_create_time_period_comparison_section 函数（功能已合并到下钻页面）


def _create_category_contribution_view(result: Dict, period_days: int) -> html.Div:
    """创建分类贡献度分析视图"""
    summary = result['summary']
    top_decline = result.get('top_decline', [])
    top_growth = result.get('top_growth', [])
    category_changes = result.get('category_changes', [])
    
    if summary.get('total_categories', 0) == 0:
        return dbc.Alert("暂无分类数据", color="warning")
    
    # 标题信息（包含数据警告）
    header_content = [
        html.H5(f"🏷️ 分类贡献度分析 - 近{period_days}天", className="mb-2"),
        html.Div([
            html.Span("📅 对比周期: ", className="text-muted"),
            html.Span(f"{summary.get('history_start', 'N/A')} ~ {summary.get('history_end', 'N/A')}", 
                     className="fw-bold me-2"),
            html.Span(" vs ", className="text-muted mx-2"),
            html.Span(f"{summary.get('recent_start', 'N/A')} ~ {summary.get('recent_end', 'N/A')}", 
                     className="fw-bold")
        ], className="mb-2 small")
    ]
    
    # 数据警告
    if summary.get('data_warning'):
        header_content.append(
            dbc.Alert([
                html.I(className="bi bi-exclamation-triangle me-2"),
                html.Strong(summary['data_warning'])
            ], color="info", className="py-2 mb-2")
        )
    
    header_content.append(
        html.P([
            f"共有 {summary['total_categories']} 个分类，",
            f"其中 {summary['decline_categories']} 个分类贡献度下降，",
            f"累计影响客单价 ",
            html.Span(f"¥{abs(summary['total_decline_contribution']):.2f}", 
                     className="fw-bold text-danger")
        ], className="mb-0")
    )
    
    header = dbc.Alert(header_content, color="info", className="mb-3")
    
    # TOP5榜单
    top_section = dbc.Row([
        # TOP5贡献度下降
        dbc.Col([
            html.H5("📉 TOP5贡献度下降分类", className="mb-3 text-danger"),
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Div([
                        html.Span(f"#{i+1} {cat['分类']}", className="fw-bold"),
                        html.Span(f"{cat['贡献度变化']:+.2f}", 
                                 className="badge bg-danger float-end")
                    ], className="mb-2"),
                    html.Small([
                        f"销量占比: {cat['销量占比_历史']:.1f}% → {cat['销量占比_近期']:.1f}% ",
                        f"({cat['销量占比变化']:+.1f}%)"
                    ], className="text-muted d-block"),
                    html.Small([
                        f"平均单价: ¥{cat['平均单价_历史']:.2f} → ¥{cat['平均单价_近期']:.2f} ",
                        f"({cat['平均单价变化']:+.2f})"
                    ], className="text-muted d-block")
                ]) for i, cat in enumerate(top_decline)
            ], className="mb-4")
        ], width=6),
        
        # TOP5贡献度增长
        dbc.Col([
            html.H5("📈 TOP5贡献度增长分类", className="mb-3 text-success"),
            dbc.ListGroup([
                dbc.ListGroupItem([
                    html.Div([
                        html.Span(f"#{i+1} {cat['分类']}", className="fw-bold"),
                        html.Span(f"{cat['贡献度变化']:+.2f}", 
                                 className="badge bg-success float-end")
                    ], className="mb-2"),
                    html.Small([
                        f"销量占比: {cat['销量占比_历史']:.1f}% → {cat['销量占比_近期']:.1f}% ",
                        f"({cat['销量占比变化']:+.1f}%)"
                    ], className="text-muted d-block"),
                    html.Small([
                        f"平均单价: ¥{cat['平均单价_历史']:.2f} → ¥{cat['平均单价_近期']:.2f} ",
                        f"({cat['平均单价变化']:+.2f})"
                    ], className="text-muted d-block")
                ]) for i, cat in enumerate(top_growth)
            ], className="mb-4")
        ], width=6)
    ], className="mb-4")
    
    # 完整分类对比表
    if category_changes:
        category_table = dbc.Table([
            html.Thead(html.Tr([
                html.Th("分类", style={'width': '15%'}),
                html.Th("上期销量占比", style={'width': '12%'}),
                html.Th("本期销量占比", style={'width': '12%'}),
                html.Th("上期平均单价", style={'width': '12%'}),
                html.Th("本期平均单价", style={'width': '12%'}),
                html.Th("上期贡献度", style={'width': '12%'}),
                html.Th("本期贡献度", style={'width': '12%'}),
                html.Th("贡献度变化", style={'width': '13%'})
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(cat['分类'], className="fw-bold"),
                    html.Td(f"{cat['销量占比_历史']:.1f}%"),
                    html.Td(f"{cat['销量占比_近期']:.1f}%"),
                    html.Td(f"¥{cat['平均单价_历史']:.2f}"),
                    html.Td(f"¥{cat['平均单价_近期']:.2f}"),
                    html.Td(f"¥{cat['贡献度_历史']:.2f}"),
                    html.Td(f"¥{cat['贡献度_近期']:.2f}"),
                    html.Td(
                        f"¥{cat['贡献度变化']:+.2f}",
                        className="fw-bold text-danger" if cat['贡献度变化'] < 0 else "fw-bold text-success"
                    )
                ], style={'backgroundColor': '#fff3cd'} if cat['贡献度变化'] < -0.5
                   else {'backgroundColor': '#d1ecf1'} if cat['贡献度变化'] > 0.5
                   else {})
                for cat in category_changes
            ])
        ], bordered=True, hover=True, striped=True, className="mb-4")
    else:
        category_table = html.Div("暂无数据", className="text-muted")
    
    return html.Div([
        header,
        top_section,
        html.H5("📊 完整分类对比表", className="mb-3"),
        category_table
    ])


def _create_product_drag_view(result: Dict, period_days: int) -> html.Div:
    """创建商品拖累视图（四层分析）"""
    summary = result.get('summary', {})
    product_analysis = result.get('product_analysis', {})
    
    # 提取summary数据（全部使用.get()防御）
    avg_aov = summary.get('avg_aov', 0)
    low_price_ratio = summary.get('low_price_ratio', 0)
    drag_product_count = summary.get('drag_product_count', 0)
    high_price_star_count = summary.get('high_price_star_count', 0)
    
    # 四层商品分析
    core_drag_view = _render_core_drag(product_analysis.get('core_drag', []))
    abnormal_view = _render_abnormal_products(product_analysis.get('abnormal', []))
    new_low_view = _render_new_low_products(product_analysis.get('new_low', []))
    high_price_view = _render_high_price_opportunity(product_analysis.get('high_price', {}), avg_aov)
    
    return html.Div([
        # 汇总信息
        dbc.Alert([
            html.H5(f"📊 分析周期: 近{period_days}天", className="mb-2"),
            html.P([
                f"平均客单价 ¥{avg_aov:.2f}，",
                f"低价商品占比 {low_price_ratio:.1f}%，",
                f"核心拖累 {drag_product_count} 个，",
                f"高价爆品 {high_price_star_count} 个"
            ], className="mb-0")
        ], color="info", className="mb-3"),
        
        # ============ 四层商品分析 ============
        html.H4("🔍 四维度商品分析", className="mb-3 mt-4"),
        
        # 第一层：核心拖累
        html.H5("🔴 第一层：核心拖累TOP10（按拉低金额排序）", className="mb-3 text-danger"),
        dbc.Alert("价格低于均价85%，对客单价影响最大的商品", color="danger", className="mb-2", style={'fontSize': '12px'}),
        core_drag_view,
        
        html.Hr(className="my-4"),
        
        # 第二层：异常变化
        html.H5("🟡 第二层：异常变化TOP10（销量大幅波动）", className="mb-3 text-warning"),
        dbc.Alert("上期≥5单，销量变化>100%或<-30%的商品", color="warning", className="mb-2", style={'fontSize': '12px'}),
        abnormal_view,
        
        html.Hr(className="my-4"),
        
        # 第三层：新增低价
        html.H5("🆕 第三层：新增低价TOP5（近期新出现）", className="mb-3 text-info"),
        dbc.Alert(f"上期无销量，本期出现且价格<¥{avg_aov * 0.3:.2f}的商品", color="info", className="mb-2", style={'fontSize': '12px'}),
        new_low_view,
        
        html.Hr(className="my-4"),
        
        # 第四层：高价带机会
        html.H5("🚀 第四层：高价带机会（价格>¥30）", className="mb-3 text-success"),
        dbc.Alert("单价30元以上的商品表现分析，挖掘提升机会", color="success", className="mb-2", style={'fontSize': '12px'}),
        high_price_view
    ])


def _render_customer_list(customers: List[Dict], severity: str) -> html.Div:
    """渲染客户列表"""
    if not customers:
        return html.Small("暂无数据", className="text-muted")
    
    items = []
    for customer in customers[:5]:  # 显示前5个
        customer_name = customer.get('客户', customer.get('customer', '未知客户'))
        history_aov = customer.get('历史客单价', customer.get('old_aov', 0))
        recent_aov = customer.get('近期客单价', customer.get('new_aov', 0))
        change_amount = customer.get('变化金额', customer.get('decline_rate', 0))
        
        items.append(
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Strong(customer_name[:15] + '...' if len(customer_name) > 15 else customer_name),
                        html.Span(f" {change_amount:+.1f}元", className="text-danger ms-2")
                    ], className="mb-1"),
                    html.Small(f"¥{history_aov:.2f} → ¥{recent_aov:.2f}", className="text-muted d-block mb-1"),
                    html.Small([
                        html.I(className="bi bi-tag me-1"),
                        customer.get('原因', customer.get('reason', '客单价下降'))
                    ], className="text-info d-block")
                ], className="p-2")
            ], className="mb-2", style={'fontSize': '12px'})
        )
    
    return html.Div(items)


def _render_drag_products(products: List[Dict]) -> html.Div:
    """渲染拖累商品列表（带诊断标签）"""
    if not products:
        return dbc.Alert("暂无拖累商品", color="success")
    
    # 创建卡片列表
    cards = []
    for idx, p in enumerate(products, 1):
        # 获取诊断信息
        label = p.get('diagnosis_label', '💰 低价拖累')
        reason = p.get('diagnosis_reason', f'价格¥{p["avg_price"]:.2f}低于整体均价')
        suggestion = p.get('suggestion', '建议：优化商品组合')
        
        # 根据标签设置卡片颜色
        if '赠品' in label:
            card_color = 'secondary'
        elif '促销' in label:
            card_color = 'warning'
        elif '降价' in label:
            card_color = 'info'
        elif '售罄' in label:
            card_color = 'danger'
        elif '滞销' in label:
            card_color = 'dark'
        else:
            card_color = 'light'
        
        card = dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.Span(f"#{idx}", className="badge bg-dark me-2"),
                    html.Strong(p['product'][:20] + '...' if len(p['product']) > 20 else p['product']),
                    html.Span(label, className="badge bg-primary ms-auto")
                ], className="d-flex align-items-center")
            ], className="py-2"),
            
            dbc.CardBody([
                # 数据行
                html.Div([
                    html.Div([
                        html.Small("平均价格", className="text-muted d-block"),
                        html.Strong(f"¥{p['avg_price']:.2f}", className="text-primary")
                    ], className="text-center", style={'flex': '1'}),
                    
                    html.Div([
                        html.Small("订单占比", className="text-muted d-block"),
                        html.Strong(f"{p['order_ratio']:.1f}%", className="text-info")
                    ], className="text-center", style={'flex': '1'}),
                    
                    html.Div([
                        html.Small("拉低金额", className="text-muted d-block"),
                        html.Strong(f"¥{p['drag_amount']:.2f}", className="text-danger")
                    ], className="text-center", style={'flex': '1'})
                ], className="d-flex justify-content-around mb-3"),
                
                # 诊断信息
                html.Hr(className="my-2"),
                html.Div([
                    html.I(className="bi bi-exclamation-circle me-2"),
                    html.Small(reason, className="text-muted")
                ], className="mb-2"),
                
                html.Div([
                    html.I(className="bi bi-lightbulb me-2"),
                    html.Small(suggestion, className="text-success")
                ])
            ], className="p-3")
        ], className="mb-3", outline=True, color=card_color, style={'fontSize': '13px'})
        
        cards.append(card)
    
    return html.Div(cards)


def _create_customer_trend_chart(trend: Dict, period_days: int):
    """创建客户降级趋势图"""
    option = {
        'tooltip': {'trigger': 'axis'},
        'legend': {'data': ['重度降级', '中度降级', '轻度降级', '总计']},
        'xAxis': {'type': 'category', 'data': trend['dates']},
        'yAxis': {'type': 'value', 'name': '客户数'},
        'series': [
            {'name': '重度降级', 'type': 'line', 'data': trend['severe_count'], 'itemStyle': {'color': '#ff4d4f'}},
            {'name': '中度降级', 'type': 'line', 'data': trend['moderate_count'], 'itemStyle': {'color': '#faad14'}},
            {'name': '轻度降级', 'type': 'line', 'data': trend['mild_count'], 'itemStyle': {'color': '#1890ff'}},
            {'name': '总计', 'type': 'line', 'data': trend['total_count'], 'itemStyle': {'color': '#722ed1'}, 'lineStyle': {'width': 3}}
        ]
    }
    
    chart_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    </head>
    <body style="margin:0;padding:0;">
        <div id="chart" style="width: 100%; height: 400px;"></div>
        <script>
            var myChart = echarts.init(document.getElementById('chart'));
            myChart.setOption({json.dumps(option, ensure_ascii=False)});
            window.addEventListener('resize', function() {{ myChart.resize(); }});
        </script>
    </body>
    </html>
    '''
    
    return html.Iframe(srcDoc=chart_html, style={'width': '100%', 'height': '420px', 'border': 'none'})


def _create_low_price_trend_chart(data: Dict, period_days: int):
    """创建低价商品占比趋势图"""
    option = {
        'tooltip': {'trigger': 'axis', 'formatter': '{b}<br/>{a}: {c}%'},
        'xAxis': {'type': 'category', 'data': data['dates']},
        'yAxis': {'type': 'value', 'name': '占比(%)', 'max': 100},
        'series': [{
            'name': '低价商品占比',
            'type': 'line',
            'data': data['ratios'],
            'itemStyle': {'color': '#ff4d4f'},
            'areaStyle': {'color': 'rgba(255, 77, 79, 0.2)'},
            'markLine': {
                'data': [{'yAxis': 25, 'name': '警戒线'}],
                'lineStyle': {'color': '#faad14', 'type': 'dashed'}
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
    <body style="margin:0;padding:0;">
        <div id="chart" style="width: 100%; height: 350px;"></div>
        <script>
            var myChart = echarts.init(document.getElementById('chart'));
            myChart.setOption({json.dumps(option, ensure_ascii=False)});
            window.addEventListener('resize', function() {{ myChart.resize(); }});
        </script>
    </body>
    </html>
    '''
    
    return html.Div([
        html.Iframe(srcDoc=chart_html, style={'width': '100%', 'height': '370px', 'border': 'none'}),
        dbc.Alert([
            html.Strong(f"当前: {data['current_ratio']:.1f}%"),
            f" | 平均: {data['avg_ratio']:.1f}%",
            f" | 峰值: {data['peak_ratio']:.1f}% ({data['peak_date']})",
            html.Span(
                " ⚠️ 超过警戒线!" if data['current_ratio'] > 25 else " ✅ 控制良好",
                className="text-danger fw-bold" if data['current_ratio'] > 25 else "text-success fw-bold"
            )
        ], color="warning" if data['current_ratio'] > 25 else "success", className="mt-2")
    ])


def _create_structure_change_chart(data: Dict, period_days: int):
    """创建客单价结构变化图"""
    option = {
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
        'legend': {'data': ['<25元', '25-50元', '>50元']},
        'xAxis': {'type': 'category', 'data': data['dates']},
        'yAxis': {'type': 'value', 'name': '占比(%)', 'max': 100},
        'series': [
            {'name': '<25元', 'type': 'bar', 'stack': 'total', 'data': data['low'], 'itemStyle': {'color': '#ff4d4f'}},
            {'name': '25-50元', 'type': 'bar', 'stack': 'total', 'data': data['mid'], 'itemStyle': {'color': '#faad14'}},
            {'name': '>50元', 'type': 'bar', 'stack': 'total', 'data': data['high'], 'itemStyle': {'color': '#52c41a'}}
        ]
    }
    
    chart_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    </head>
    <body style="margin:0;padding:0;">
        <div id="chart" style="width: 100%; height: 350px;"></div>
        <script>
            var myChart = echarts.init(document.getElementById('chart'));
            myChart.setOption({json.dumps(option, ensure_ascii=False)});
            window.addEventListener('resize', function() {{ myChart.resize(); }});
        </script>
    </body>
    </html>
    '''
    
    current = data['current']
    change = data['change']
    
    return html.Div([
        html.Iframe(srcDoc=chart_html, style={'width': '100%', 'height': '370px', 'border': 'none'}),
        dbc.Row([
            dbc.Col([
                dbc.Alert([
                    html.Strong("<25元: "),
                    f"{current['low']:.1f}% ",
                    html.Span(f"({'↑' if change['low'] > 0 else '↓'}{abs(change['low']):.1f}%)", 
                             className="text-danger" if change['low'] > 0 else "text-success")
                ], color="light", className="mb-0 py-2")
            ], width=4),
            dbc.Col([
                dbc.Alert([
                    html.Strong("25-50元: "),
                    f"{current['mid']:.1f}% ",
                    html.Span(f"({'↑' if change['mid'] > 0 else '↓'}{abs(change['mid']):.1f}%)", 
                             className="text-success" if change['mid'] > 0 else "text-danger")
                ], color="light", className="mb-0 py-2")
            ], width=4),
            dbc.Col([
                dbc.Alert([
                    html.Strong(">50元: "),
                    f"{current['high']:.1f}% ",
                    html.Span(f"({'↑' if change['high'] > 0 else '↓'}{abs(change['high']):.1f}%)", 
                             className="text-success" if change['high'] > 0 else "text-danger")
                ], color="light", className="mb-0 py-2")
            ], width=4)
        ], className="mt-2")
    ])


def _create_opportunity_chart(products: List[Dict]):
    """创建机会商品销量趋势图"""
    if not products:
        return dbc.Alert("暂无机会商品", color="info")
    
    names = [p['product'][:10] for p in products]
    sales_change = [p['sales_change'] for p in products]
    avg_prices = [p['avg_price'] for p in products]
    
    option = {
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
        'legend': {'data': ['销量变化率', '平均价格']},
        'xAxis': {'type': 'category', 'data': names, 'axisLabel': {'rotate': 30}},
        'yAxis': [
            {'type': 'value', 'name': '变化率(%)', 'position': 'left'},
            {'type': 'value', 'name': '价格(元)', 'position': 'right'}
        ],
        'series': [
            {'name': '销量变化率', 'type': 'bar', 'data': sales_change, 'itemStyle': {'color': '#ff4d4f'}},
            {'name': '平均价格', 'type': 'line', 'yAxisIndex': 1, 'data': avg_prices, 'itemStyle': {'color': '#1890ff'}}
        ]
    }
    
    chart_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    </head>
    <body style="margin:0;padding:0;">
        <div id="chart" style="width: 100%; height: 350px;"></div>
        <script>
            var myChart = echarts.init(document.getElementById('chart'));
            myChart.setOption({json.dumps(option, ensure_ascii=False)});
            window.addEventListener('resize', function() {{ myChart.resize(); }});
        </script>
    </body>
    </html>
    '''
    
    return html.Iframe(srcDoc=chart_html, style={'width': '100%', 'height': '370px', 'border': 'none'})


# ============ 四层商品分析渲染函数 ============

def _render_core_drag(products: List[Dict]) -> html.Div:
    """渲染核心拖累商品（卡片式）"""
    if not products:
        return dbc.Alert("✅ 暂无核心拖累商品", color="success")
    
    cards = []
    for idx, p in enumerate(products, 1):
        label = p.get('diagnosis_label', '💰 低价拖累')
        reason = p.get('diagnosis_reason', '')
        suggestion = p.get('suggestion', '')
        
        # 根据标签设置颜色
        if '促销' in label:
            border_color = '#faad14'
        elif '降价' in label:
            border_color = '#1890ff'
        elif '缺货' in label:
            border_color = '#ff4d4f'
        elif '滞销' in label:
            border_color = '#722ed1'
        else:
            border_color = '#d9d9d9'
        
        card = dbc.Card([
            dbc.CardBody([
                # 标题行
                html.Div([
                    html.Span(f"#{idx}", className="badge bg-danger me-2"),
                    html.Strong(p['product'][:25] + '...' if len(p['product']) > 25 else p['product'], style={'fontSize': '14px'}),
                    html.Span(label, className="badge bg-primary ms-auto", style={'fontSize': '12px'})
                ], className="d-flex align-items-center mb-3"),
                
                # 数据行
                dbc.Row([
                    dbc.Col([
                        html.Small("平均价格", className="text-muted d-block"),
                        html.Strong(f"¥{p['avg_price']:.2f}", className="text-primary", style={'fontSize': '16px'})
                    ], width=3, className="text-center"),
                    dbc.Col([
                        html.Small("订单数", className="text-muted d-block"),
                        html.Strong(f"{p['order_count']}单", className="text-info", style={'fontSize': '16px'})
                    ], width=3, className="text-center"),
                    dbc.Col([
                        html.Small("占比", className="text-muted d-block"),
                        html.Strong(f"{p['order_ratio']:.1f}%", className="text-warning", style={'fontSize': '16px'})
                    ], width=3, className="text-center"),
                    dbc.Col([
                        html.Small("拉低金额", className="text-muted d-block"),
                        html.Strong(f"¥{p['drag_amount']:.2f}", className="text-danger", style={'fontSize': '16px'})
                    ], width=3, className="text-center")
                ], className="mb-3"),
                
                html.Hr(className="my-2"),
                
                # 诊断信息
                html.Div([
                    html.I(className="bi bi-exclamation-triangle me-2 text-warning"),
                    html.Small(reason, className="text-muted")
                ], className="mb-2"),
                
                html.Div([
                    html.I(className="bi bi-lightbulb me-2 text-success"),
                    html.Small(suggestion, style={'color': '#52c41a'})
                ])
            ], className="p-3")
        ], className="mb-3", style={'border': f'2px solid {border_color}', 'fontSize': '13px'})
        
        cards.append(card)
    
    return html.Div(cards)


def _render_abnormal_products(products: List[Dict]) -> html.Div:
    """渲染异常变化商品（表格式）"""
    if not products:
        return dbc.Alert("暂无异常变化商品", color="info")
    
    table_header = [
        html.Thead(html.Tr([
            html.Th("商品名称", style={'width': '30%'}),
            html.Th("价格", className="text-end"),
            html.Th("历史订单", className="text-end"),
            html.Th("近期订单", className="text-end"),
            html.Th("销量变化", className="text-end"),
            html.Th("价格变化", className="text-end")
        ]))
    ]
    
    rows = []
    for p in products:
        change_color = 'success' if p['sales_change'] > 0 else 'danger'
        price_change_color = 'success' if p['price_change'] < 0 else 'danger'
        
        rows.append(html.Tr([
            html.Td(p['product'][:30] + '...' if len(p['product']) > 30 else p['product']),
            html.Td(f"¥{p['avg_price']:.2f}", className="text-end"),
            html.Td(f"{p['history_orders']}单", className="text-end"),
            html.Td(f"{p['recent_orders']}单", className="text-end"),
            html.Td(
                html.Span(f"{p['sales_change']:+.1f}%", className=f"badge bg-{change_color}"),
                className="text-end"
            ),
            html.Td(
                html.Span(f"{p['price_change']:+.1f}%", className=f"badge bg-{price_change_color}") if abs(p['price_change']) > 1 else html.Span("--", className="text-muted"),
                className="text-end"
            )
        ]))
    
    table = dbc.Table(table_header + [html.Tbody(rows)], bordered=True, hover=True, size="sm", style={'fontSize': '13px'})
    
    return html.Div([
        table,
        html.Small(f"共 {len(products)} 个商品", className="text-muted")
    ])


def _render_new_low_products(products: List[Dict]) -> html.Div:
    """渲染新增低价商品（列表式）"""
    if not products:
        return dbc.Alert("✅ 暂无新增低价商品", color="success")
    
    items = []
    for idx, p in enumerate(products, 1):
        items.append(
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Span(f"#{idx}", className="badge bg-info me-2"),
                        html.Strong(p['product'][:35] + '...' if len(p['product']) > 35 else p['product']),
                        html.Span(f"¥{p['avg_price']:.2f}", className="badge bg-warning ms-auto")
                    ], className="d-flex align-items-center mb-2"),
                    
                    html.Small([
                        html.I(className="bi bi-cart-check me-1"),
                        f"{p['order_count']}单 | 占比{p['order_ratio']:.1f}% | ",
                        html.Span("🎯 新品引流", className="text-primary")
                    ], className="text-muted")
                ], className="p-2")
            ], className="mb-2", color="light", outline=True, style={'fontSize': '13px'})
        )
    
    return html.Div(items)


def _render_high_price_opportunity(high_price_data: Dict, avg_aov: float) -> html.Div:
    """渲染高价带机会（分三类展示）"""
    star = high_price_data.get('star', [])
    stable = high_price_data.get('stable', [])
    decline = high_price_data.get('decline', [])
    
    if not star and not stable and not decline:
        return dbc.Alert("暂无高价商品数据（价格>¥30）", color="info")
    
    return html.Div([
        # 高价爆品
        html.Div([
            html.H6("🌟 高价爆品（销量暴增>50%）", className="mb-3 text-success"),
            _render_star_products(star) if star else html.Small("暂无", className="text-muted")
        ], className="mb-4"),
        
        # 高价稳定
        html.Div([
            html.H6("🔸 高价稳定（销量变化-20%~50%）", className="mb-3"),
            _render_stable_products(stable) if stable else html.Small("暂无", className="text-muted")
        ], className="mb-4"),
        
        # 高价滞销
        html.Div([
            html.H6("⚠️ 高价滞销（销量下降>20%）", className="mb-3 text-danger"),
            _render_decline_products(decline) if decline else html.Small("暂无", className="text-muted")
        ])
    ])


def _render_star_products(products: List[Dict]) -> html.Div:
    """渲染高价爆品"""
    cards = []
    for idx, p in enumerate(products, 1):
        card = dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Span(f"#{idx}", className="badge bg-success me-2"),
                    html.Strong(p['product'][:30] + '...' if len(p['product']) > 30 else p['product']),
                    html.Span(f"¥{p['avg_price']:.2f}", className="badge bg-warning ms-auto")
                ], className="d-flex align-items-center mb-2"),
                
                dbc.Row([
                    dbc.Col([
                        html.Small("历史", className="text-muted d-block"),
                        html.Strong(f"{p['history_orders']}单", style={'fontSize': '14px'})
                    ], width=3),
                    dbc.Col([
                        html.Small("近期", className="text-muted d-block"),
                        html.Strong(f"{p['recent_orders']}单", style={'fontSize': '14px'})
                    ], width=3),
                    dbc.Col([
                        html.Small("变化", className="text-muted d-block"),
                        html.Strong(f"+{p['sales_change']:.0f}%", className="text-success", style={'fontSize': '14px'})
                    ], width=3),
                    dbc.Col([
                        html.Small("拉升潜力", className="text-muted d-block"),
                        html.Strong(f"¥{p['lift_potential']:.2f}", className="text-primary", style={'fontSize': '14px'})
                    ], width=3)
                ]),
                
                html.Hr(className="my-2"),
                html.Small("💡 建议：加大推广力度，设为主推商品", className="text-success")
            ], className="p-3")
        ], className="mb-3", color="success", outline=True, style={'fontSize': '13px'})
        cards.append(card)
    
    return html.Div(cards)


def _render_stable_products(products: List[Dict]) -> html.Div:
    """渲染高价稳定商品（表格）"""
    table_header = [
        html.Thead(html.Tr([
            html.Th("商品名称", style={'width': '40%'}),
            html.Th("价格", className="text-end"),
            html.Th("近期订单", className="text-end"),
            html.Th("变化", className="text-end"),
            html.Th("拉升潜力", className="text-end")
        ]))
    ]
    
    rows = []
    for p in products:
        rows.append(html.Tr([
            html.Td(p['product'][:35] + '...' if len(p['product']) > 35 else p['product']),
            html.Td(f"¥{p['avg_price']:.2f}", className="text-end"),
            html.Td(f"{p['recent_orders']}单", className="text-end"),
            html.Td(
                html.Span(f"{p['sales_change']:+.0f}%", className="text-muted"),
                className="text-end"
            ),
            html.Td(f"¥{p['lift_potential']:.2f}", className="text-end text-primary")
        ]))
    
    return dbc.Table(table_header + [html.Tbody(rows)], bordered=True, hover=True, size="sm", style={'fontSize': '12px'})


def _create_hourly_analysis_card(hourly_result: Dict) -> html.Div:
    """
    创建时段分析展示卡片（占位函数）
    
    TODO: 完整实现需要：
    1. 日期选择器组件
    2. 时段对比表格/图表
    3. 回调函数处理日期选择和数据更新
    
    参数：
        hourly_result: analyze_hourly_aov函数的返回结果
    """
    if not hourly_result or 'date1' not in hourly_result:
        return html.Div("暂无数据", className="text-muted")
    
    date1_data = hourly_result['date1']
    period_data = date1_data.get('period_data', [])
    
    if not period_data:
        return html.Div("暂无时段数据", className="text-muted")
    
    # 时段对比表格
    period_rows = []
    for p in period_data:
        diff_color = 'text-success' if p['diff_rate'] > 0 else 'text-danger' if p['diff_rate'] < 0 else 'text-secondary'
        period_rows.append(html.Tr([
            html.Td(p['label']),
            html.Td(f"¥{p['aov']:.2f}"),
            html.Td(f"{p['orders']}单"),
            html.Td(f"{p['diff_rate']:+.1f}%", className=diff_color)
        ]))
    
    return html.Div([
        dbc.Table([
            html.Thead(html.Tr([
                html.Th("时段"),
                html.Th("客单价"),
                html.Th("订单数"),
                html.Th("vs全天")
            ])),
            html.Tbody(period_rows)
        ], bordered=True, hover=True, size="sm")
    ])


def _render_decline_products(products: List[Dict]) -> html.Div:
    """渲染高价滞销商品"""
    items = []
    for p in products:
        items.append(
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Strong(p['product'][:35] + '...' if len(p['product']) > 35 else p['product']),
                        html.Span(f"¥{p['avg_price']:.2f}", className="badge bg-danger ms-2")
                    ], className="mb-2"),
                    
                    html.Small([
                        f"{p['history_orders']}单 → {p['recent_orders']}单 ",
                        html.Span(f"({p['sales_change']:.0f}%)", className="text-danger"),
                        " | 💡 检查价格竞争力"
                    ], className="text-muted")
                ], className="p-2")
            ], className="mb-2", color="danger", outline=True, style={'fontSize': '13px'})
        )
    
    return html.Div(items)



# ==================== 六象限与调价计算器联动回调（V3.1：滚动+数据传递） ====================

# Clientside callback：实现页面滚动到智能调价计算器
clientside_callback(
    """
    function(n_clicks) {
        // 检查是否有按钮被点击
        const triggered = dash_clientside.callback_context.triggered;
        if (!triggered || triggered.length === 0) {
            return window.dash_clientside.no_update;
        }
        
        // 等待一小段时间确保DOM更新
        setTimeout(function() {
            // 滚动到智能调价计算器
            const element = document.getElementById('pricing-calculator-card');
            if (element) {
                // 平滑滚动
                element.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start',
                    inline: 'nearest'
                });
                
                // 高亮显示2秒
                element.style.transition = 'box-shadow 0.3s';
                element.style.boxShadow = '0 0 30px rgba(255, 193, 7, 0.8)';
                setTimeout(function() {
                    element.style.boxShadow = '';
                }, 2000);
            }
        }, 100);
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('pricing-scroll-trigger', 'data'),  # 虚拟输出
    Input({'type': 'quadrant-to-pricing', 'quadrant': ALL}, 'n_clicks'),
    prevent_initial_call=True
)

@callback(
    [Output('pricing-quadrant-filter', 'data'),
     Output('pricing-source-context', 'data'),
     Output('quick-scene-store', 'data', allow_duplicate=True)],  # 利用现有的快捷场景Store，允许重复输出
    Input({'type': 'quadrant-to-pricing', 'quadrant': ALL}, 'n_clicks'),
    [State('db-store-filter', 'value'),
     State('product-health-channel-filter', 'value')],
    prevent_initial_call=True
)
def pass_quadrant_data_to_pricing(n_clicks, selected_stores, channel):
    """
    从六象限传递数据到调价计算器（V3.1：滚动+数据传递）
    
    功能：
    1. 传递象限筛选数据
    2. 传递来源上下文信息
    3. 设置快捷场景为"六象限"（利用现有机制）
    4. 配合clientside callback实现页面滚动
    
    Args:
        n_clicks: 各象限"调价"按钮的点击次数
        selected_stores: 当前选择的门店
        channel: 当前选择的渠道
    
    Returns:
        (quadrant_filter, source_context, quick_scene)
    """
    from dash import ctx
    from datetime import datetime
    
    # 检查是否有按钮被点击
    if not any(n_clicks) or not ctx.triggered:
        raise PreventUpdate
    
    # 获取点击的象限
    triggered = ctx.triggered_id
    if not triggered or 'quadrant' not in triggered:
        raise PreventUpdate
    
    quadrant = triggered['quadrant']  # 如 "💎 潜力商品"
    
    print(f"[联动] 传递象限数据到调价计算器: {quadrant}")
    
    # 重新计算商品评分数据（确保数据最新）
    try:
        GLOBAL_DATA = get_real_global_data()
        if GLOBAL_DATA is None or GLOBAL_DATA.empty:
            print("[联动] 无全局数据")
            raise PreventUpdate
        
        # 应用门店筛选
        from .diagnosis_analysis import apply_filters_view
        store_list = selected_stores if isinstance(selected_stores, list) else [selected_stores] if selected_stores else []
        df = apply_filters_view(GLOBAL_DATA, selected_stores=store_list)
        
        if df is None or df.empty:
            print("[联动] 筛选后无数据")
            raise PreventUpdate
        
        # 应用渠道筛选
        if channel and channel != 'all':
            channel_col = next((c for c in ['渠道', '平台', 'channel'] if c in df.columns), None)
            if channel_col:
                df = df[df[channel_col] == channel]
        
        # 计算商品评分
        from .diagnosis_analysis import calculate_product_scores
        product_scores = calculate_product_scores(df, days_range=0)  # 使用全部数据
        
        if product_scores is None or product_scores.empty:
            print("[联动] 无商品评分数据")
            raise PreventUpdate
        
        # 筛选该象限的商品
        quadrant_col = '四象限分类' if '四象限分类' in product_scores.columns else '象限分类'
        if quadrant_col not in product_scores.columns:
            print(f"[联动] 缺少象限分类列: {quadrant_col}")
            raise PreventUpdate
        
        quadrant_products = product_scores[product_scores[quadrant_col] == quadrant]
        
        print(f"[联动] 筛选到 {len(quadrant_products)} 个{quadrant}商品")
        
        # 转换为字典列表（便于存储和传递）
        quadrant_products_dict = quadrant_products.to_dict('records')
        
        # 构建象限筛选数据
        quadrant_filter = {
            'quadrant': quadrant,
            'products': quadrant_products_dict,
            'count': len(quadrant_products),
            'timestamp': datetime.now().isoformat()
        }
        
        # 构建来源上下文信息
        source_context = {
            'from': '商品健康分析',
            'quadrant': quadrant,
            'stores': store_list,
            'channel': channel,
            'timestamp': datetime.now().isoformat()
        }
        
        # 设置快捷场景为"六象限"（利用现有的快捷场景机制）
        quick_scene = {
            'type': 'quadrant',
            'quadrant': quadrant,
            'count': len(quadrant_products),
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"[联动] 数据传递成功: {len(quadrant_products_dict)}个商品")
        
        return quadrant_filter, source_context, quick_scene
        
    except Exception as e:
        print(f"[联动] 数据传递失败: {e}")
        import traceback
        traceback.print_exc()
        raise PreventUpdate


@callback(
    Output('pricing-source-info', 'children'),
    Input('pricing-source-context', 'data'),
    prevent_initial_call=True
)
def show_pricing_source_info(context):
    """
    显示来源信息（V3.1：简化版）
    
    功能：
    1. 显示来源信息和象限
    2. 显示"返回"按钮
    
    Args:
        context: 来源上下文信息
    
    Returns:
        来源信息组件
    """
    if not context or 'quadrant' not in context:
        return html.Div()
    
    quadrant = context.get('quadrant', '')
    count = context.get('count', 0)
    
    print(f"[联动] 显示来源信息: {quadrant}")
    
    return dbc.Alert([
        html.Div([
            html.I(className="fas fa-link me-2"),
            html.Strong(f"已自动筛选：{quadrant}", className="me-2"),
            html.Small(f"(来自商品健康分析，共{count}个商品)", className="text-muted"),
        ], className="d-inline-block"),
        dbc.Button([
            html.I(className="fas fa-arrow-up me-1"),
            "返回六象限"
        ], 
        id="pricing-back-to-source", 
        size="sm", 
        color="link", 
        className="float-end",
        style={'textDecoration': 'none'})
    ], color="success", className="py-2 mb-3")



# Clientside callback：返回到六象限分布（滚动）
clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks) {
            // 滚动到商品健康分析卡片
            const element = document.getElementById('product-health-card');
            if (element) {
                element.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start',
                    inline: 'nearest'
                });
            }
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('pricing-back-trigger', 'data'),  # 虚拟输出
    Input('pricing-back-to-source', 'n_clicks'),
    prevent_initial_call=True
)


# ==================== 调价计算器中添加"六象限商品"选项（方案B：补充功能） ====================

@callback(
    Output('pricing-quadrant-selector-container', 'style'),
    Input('pricing-role-quadrant', 'n_clicks'),
    State('pricing-quadrant-selector-container', 'style'),
    prevent_initial_call=True
)
def toggle_quadrant_selector(n_clicks, current_style):
    """
    切换六象限选择器的显示/隐藏
    
    功能：点击"六象限商品"按钮后，显示/隐藏象限下拉框
    """
    if n_clicks:
        # 切换显示状态
        if current_style and current_style.get('display') == 'block':
            return {'display': 'none'}
        else:
            return {'display': 'block'}
    raise PreventUpdate


@callback(
    [Output('pricing-quadrant-dropdown', 'options'),
     Output('pricing-quadrant-dropdown', 'value')],
    Input('product-scores-store', 'data'),
    prevent_initial_call=True
)
def update_quadrant_dropdown_options(product_scores):
    """
    更新六象限下拉框的选项
    
    功能：根据当前的商品评分数据，动态生成象限选项（显示商品数量）
    """
    if not product_scores:
        # 默认选项
        default_options = [
            {'label': '🌟 明星商品', 'value': '🌟 明星商品'},
            {'label': '💎 潜力商品', 'value': '💎 潜力商品'},
            {'label': '⚡ 自然引流', 'value': '⚡ 自然引流'},
            {'label': '🐌 低效商品', 'value': '🐌 低效商品'},
            {'label': '🔥 畅销商品', 'value': '🔥 畅销商品'},
            {'label': '🎯 策略引流', 'value': '🎯 策略引流'},
        ]
        return default_options, None
    
    # 统计各象限商品数量
    import pandas as pd
    df = pd.DataFrame(product_scores)
    
    quadrant_col = '四象限分类' if '四象限分类' in df.columns else '象限分类'
    if quadrant_col not in df.columns:
        return [], None
    
    quadrant_counts = df[quadrant_col].value_counts().to_dict()
    
    # 生成选项（按固定顺序）
    quadrant_order = [
        '🌟 明星商品',
        '💎 潜力商品',
        '⚡ 自然引流',
        '🐌 低效商品',
        '🔥 畅销商品',
        '🎯 策略引流',
    ]
    
    options = []
    for quadrant in quadrant_order:
        count = quadrant_counts.get(quadrant, 0)
        if count > 0:  # 只显示有商品的象限
            options.append({
                'label': f"{quadrant} ({count}个)",
                'value': quadrant
            })
    
    return options, None


@callback(
    [Output('pricing-quadrant-filter', 'data', allow_duplicate=True),
     Output('pricing-smart-suggestion', 'children', allow_duplicate=True),
     Output('pricing-role-store', 'data', allow_duplicate=True),
     Output('pricing-target-margin-v2', 'value', allow_duplicate=True)],
    Input('pricing-quadrant-dropdown', 'value'),
    State('product-scores-store', 'data'),
    prevent_initial_call=True
)
def filter_by_quadrant_dropdown(quadrant, product_scores):
    """
    根据下拉框选择的象限筛选商品（方案B：在调价计算器中选择象限）
    
    功能：
    1. 筛选该象限的商品
    2. 提供智能建议
    3. 自动选择调价场景
    4. 自动填充目标利润率
    """
    if not quadrant or not product_scores:
        raise PreventUpdate
    
    print(f"[联动] 从下拉框选择象限: {quadrant}")
    
    # 筛选该象限的商品
    import pandas as pd
    df = pd.DataFrame(product_scores)
    
    quadrant_col = '四象限分类' if '四象限分类' in df.columns else '象限分类'
    if quadrant_col not in df.columns:
        raise PreventUpdate
    
    quadrant_products = df[df[quadrant_col] == quadrant]
    quadrant_products_dict = quadrant_products.to_dict('records')
    
    # 构建象限筛选数据
    from datetime import datetime
    quadrant_filter = {
        'quadrant': quadrant,
        'products': quadrant_products_dict,
        'count': len(quadrant_products),
        'timestamp': datetime.now().isoformat()
    }
    
    # 智能建议（复用上面的逻辑）
    quadrant_strategies = {
        '🌟 明星商品': ('profit', '测试性提价', '明星商品又赚钱又好卖，可以小幅提价测试价格弹性上限。建议提价幅度：3-8%', 25),
        '💎 潜力商品': ('promo', '降价促销', '潜力商品利润好但销量低，建议降价促销提升销量。建议降价幅度：5-15%，目标利润率：15%', 15),
        '⚡ 自然引流': ('profit', '小幅提价', '自然引流商品有提价空间，建议小幅提价提升利润率。建议提价幅度：3-8%', 20),
        '🐌 低效商品': ('slow', '清仓降价', '低效商品既不赚钱也不好卖，建议清仓降价快速出清。建议降价幅度：15-30%', 8),
        '🔥 畅销商品': ('profit', '谨慎提价', '畅销商品是刚需品，提价需谨慎，建议小幅提价。建议提价幅度：1-3%', 18),
        '🎯 策略引流': ('loss', '监控效果', '策略引流是主动亏损引流，不建议调价。建议监控引流效果和ROI，控制引流成本', 5),
    }
    
    strategy = quadrant_strategies.get(quadrant, ('promo', '根据目标调整', '请根据商品特点和业务目标，选择合适的调价方向和目标利润率', 15))
    scene, action_title, action_desc, target_margin = strategy
    
    suggestion_colors = {
        'profit': 'success',
        'promo': 'warning',
        'slow': 'danger',
        'loss': 'secondary'
    }
    
    suggestion_color = suggestion_colors.get(scene, 'info')
    
    suggestion = dbc.Alert([
        html.H6([
            html.I(className="fas fa-lightbulb me-2"),
            f"智能建议：{action_title}"
        ], className="mb-2"),
        html.P(action_desc, className="mb-0", style={'fontSize': '14px'})
    ], color=suggestion_color, className="mb-3")
    
    print(f"[联动] 下拉框筛选成功: {len(quadrant_products_dict)}个商品, 场景: {scene}")
    
    return quadrant_filter, suggestion, scene, target_margin
