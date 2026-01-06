"""
分页工具模块 - V8.9数据分页优化

提供智能分页策略和分页组件
支持10万+行数据的高效展示

作者: GitHub Copilot
版本: V8.9
"""

import pandas as pd
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import dash_table
from typing import Dict, Tuple, Optional


def get_pagination_config(df_size: int) -> Dict:
    """
    根据数据量返回智能分页配置
    
    策略：
    - <5000行：全量加载（性能足够好）
    - 5000-50000行：前端分页（减少渲染压力）
    - >50000行：后端分页（按需加载）
    
    参数：
        df_size: 数据行数
    
    返回：
        {
            'mode': 'none' | 'frontend' | 'backend',
            'page_size': int,
            'message': str
        }
    """
    if df_size < 5000:
        return {
            'mode': 'none',  # 全量加载
            'page_size': df_size,
            'message': f'✅ 数据量适中({df_size:,}行)，全量展示',
            'color': 'success'
        }
    elif df_size < 50000:
        return {
            'mode': 'frontend',  # 前端分页
            'page_size': 100,
            'message': f'📄 共{df_size:,}行，前端分页展示（每页100行）',
            'color': 'info'
        }
    else:
        return {
            'mode': 'backend',  # 后端分页
            'page_size': 100,
            'message': f'⚡ 数据量较大({df_size:,}行)，后端分页加载（每页100行）',
            'color': 'warning'
        }


def create_paginated_datatable(
    df: pd.DataFrame,
    table_id: str,
    page_size: Optional[int] = None,
    max_height: str = '600px',
    enable_sort: bool = True,
    enable_filter: bool = True,
    enable_export: bool = False,
    columns: Optional[list] = None,
    style_data_conditional: Optional[list] = None,
    style_cell_conditional: Optional[list] = None
) -> html.Div:
    """
    创建智能分页表格
    
    参数：
        df: 数据DataFrame
        table_id: 表格ID
        page_size: 每页行数（None则自动判断）
        max_height: 最大高度
        enable_sort: 是否启用排序
        enable_filter: 是否启用筛选
        enable_export: 是否启用导出功能（默认False，V8.10.1修复）
        columns: 自定义列定义（V8.10.1新增，用于支持自定义列名）
        style_data_conditional: 自定义数据样式条件（V8.10.1新增）
        style_cell_conditional: 自定义单元格样式条件（V8.10.1新增）
    
    返回：
        包含分页表格的Div组件
    """
    if df is None or df.empty:
        return html.Div("暂无数据", className="text-muted text-center py-4")
    
    # 获取分页配置
    config = get_pagination_config(len(df))
    
    # 确定分页模式
    if config['mode'] == 'none':
        # 小数据量：全量展示，不分页
        page_action = 'none'
        page_current = 0
        actual_page_size = len(df)
        show_pagination_info = False
    else:
        # 中大数据量：启用分页
        page_action = 'native'  # 前端分页
        page_current = 0
        actual_page_size = page_size or config['page_size']
        show_pagination_info = True
    
    # V8.10.1修复：支持自定义列定义
    if columns is None:
        # 构建默认表格列定义
        columns = []
        for col in df.columns:
            col_def = {"name": col, "id": col}
            
            # 数值列右对齐
            if pd.api.types.is_numeric_dtype(df[col]):
                col_def['type'] = 'numeric'
                col_def['format'] = {'specifier': ',.2f'}
            
            columns.append(col_def)
    
    # V8.10.1调试：打印关键信息
    print(f"[分页表格调试] table_id={table_id}")
    print(f"[分页表格调试] 数据行数={len(df)}, 列数={len(df.columns)}")
    print(f"[分页表格调试] 列定义数量={len(columns)}")
    print(f"[分页表格调试] 前3个列定义: {columns[:3] if len(columns) >= 3 else columns}")
    records = df.to_dict('records')
    print(f"[分页表格调试] Records数量={len(records)}")
    if len(records) > 0:
        print(f"[分页表格调试] 第一条record的keys: {list(records[0].keys())[:5]}...")
    
    # V8.10.1调试：打印返回结构
    print(f"[分页表格调试] 准备返回DataTable组件")
    print(f"[分页表格调试] show_pagination_info = {show_pagination_info}")
    
    return html.Div([
        # 分页提示（仅在启用分页时显示）
        dbc.Alert(
            [
                html.I(className="bi bi-info-circle me-2"),
                config['message']
            ],
            color=config['color'],
            className="mb-2 py-2",
            style={"fontSize": "12px"}
        ) if show_pagination_info else None,
        
        # 表格
        dash_table.DataTable(
            id=table_id,
            data=df.to_dict('records'),
            columns=columns,
            
            # 分页配置
            page_action=page_action,
            page_current=page_current,
            page_size=actual_page_size,
            
            # 样式配置
            style_table={
                'overflowX': 'auto',
                'overflowY': 'auto',
                'maxHeight': max_height
            },
            style_cell={
                'textAlign': 'left',
                'padding': '8px 12px',
                'fontSize': '13px',
                'minWidth': '80px',
                'maxWidth': '300px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'fontSize': '13px',
                'textAlign': 'center',
                'border': '1px solid #dee2e6',
                'position': 'sticky',
                'top': 0,
                'zIndex': 1
            },
            style_data={
                'border': '1px solid #dee2e6',
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            # V8.10.1修复：支持自定义样式条件
            style_data_conditional=style_data_conditional if style_data_conditional is not None else [
                # 斑马纹
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                },
                # 悬停效果
                {
                    'if': {'state': 'active'},
                    'backgroundColor': '#e3f2fd',
                    'border': '1px solid #2196f3'
                }
            ],
            
            # V8.10.1修复：支持自定义单元格样式条件
            style_cell_conditional=style_cell_conditional if style_cell_conditional is not None else None,
            
            # 性能优化
            virtualization=True,  # 虚拟滚动
            
            # 排序和筛选
            sort_action='native' if enable_sort else 'none',
            filter_action='native' if enable_filter else 'none',
            
            # 导出功能（V8.10.1: 默认关闭，避免界面混乱）
            export_format='xlsx' if enable_export else None,
            export_headers='display' if enable_export else None,
            
            # 工具提示
            tooltip_data=[
                {
                    column: {'value': str(value), 'type': 'markdown'}
                    for column, value in row.items()
                } for row in df.to_dict('records')
            ],
            tooltip_duration=None,
            
            # CSS类
            css=[{
                'selector': '.dash-table-tooltip',
                'rule': 'background-color: #333; color: white; font-size: 12px; padding: 8px;'
            }],
        ),
        
        # 分页统计信息（仅在启用分页时显示）
        html.Div([
            html.Small([
                html.I(className="bi bi-table me-1"),
                f"共 {len(df):,} 行数据",
                html.Span(" | ", className="mx-2"),
                f"每页显示 {actual_page_size} 行",
                html.Span(" | ", className="mx-2"),
                f"共 {(len(df) + actual_page_size - 1) // actual_page_size} 页"
            ], className="text-muted")
        ], className="mt-2 text-center") if show_pagination_info else None
    ])


def create_backend_paginated_table(
    df: pd.DataFrame,
    table_id: str,
    current_page: int = 0,
    page_size: int = 100,
    total_rows: Optional[int] = None
) -> Tuple[html.Div, int]:
    """
    创建后端分页表格（用于超大数据量）
    
    参数：
        df: 当前页的数据DataFrame
        table_id: 表格ID
        current_page: 当前页码（从0开始）
        page_size: 每页行数
        total_rows: 总行数（如果None则使用df长度）
    
    返回：
        (表格组件, 总页数)
    """
    if df is None or df.empty:
        return html.Div("暂无数据", className="text-muted text-center py-4"), 0
    
    # 计算分页信息
    total = total_rows or len(df)
    total_pages = (total + page_size - 1) // page_size
    start_idx = current_page * page_size + 1
    end_idx = min((current_page + 1) * page_size, total)
    
    # 构建表格列定义
    columns = []
    for col in df.columns:
        col_def = {"name": col, "id": col}
        if pd.api.types.is_numeric_dtype(df[col]):
            col_def['type'] = 'numeric'
            col_def['format'] = {'specifier': ',.2f'}
        columns.append(col_def)
    
    table_component = html.Div([
        # 分页控制器
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    # 左侧：分页信息
                    dbc.Col([
                        html.Div([
                            html.I(className="bi bi-table me-2"),
                            html.Span(f"显示第 {start_idx:,}-{end_idx:,} 行，", className="fw-bold"),
                            html.Span(f"共 {total:,} 行", className="text-muted")
                        ], className="d-flex align-items-center")
                    ], width=6),
                    
                    # 右侧：分页按钮
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="bi bi-chevron-double-left me-1"),
                                "首页"
                            ], id=f"{table_id}-first-page", size="sm", 
                               color="primary", outline=True,
                               disabled=(current_page == 0)),
                            
                            dbc.Button([
                                html.I(className="bi bi-chevron-left me-1"),
                                "上一页"
                            ], id=f"{table_id}-prev-page", size="sm",
                               color="primary", outline=True,
                               disabled=(current_page == 0)),
                            
                            dbc.Input(
                                id=f"{table_id}-page-input",
                                type="number",
                                min=1,
                                max=total_pages,
                                value=current_page + 1,
                                size="sm",
                                style={"width": "80px", "textAlign": "center"}
                            ),
                            
                            html.Span(f"/ {total_pages}", 
                                     className="d-flex align-items-center px-2 text-muted small"),
                            
                            dbc.Button([
                                "下一页",
                                html.I(className="bi bi-chevron-right ms-1")
                            ], id=f"{table_id}-next-page", size="sm",
                               color="primary", outline=True,
                               disabled=(current_page >= total_pages - 1)),
                            
                            dbc.Button([
                                "末页",
                                html.I(className="bi bi-chevron-double-right ms-1")
                            ], id=f"{table_id}-last-page", size="sm",
                               color="primary", outline=True,
                               disabled=(current_page >= total_pages - 1)),
                        ], size="sm")
                    ], width=6, className="text-end")
                ], align="center")
            ], className="py-2")
        ], className="mb-2"),
        
        # 表格
        dash_table.DataTable(
            id=table_id,
            data=df.to_dict('records'),
            columns=columns,
            
            # 不使用内置分页（由后端控制）
            page_action='none',
            
            # 样式配置
            style_table={
                'overflowX': 'auto',
                'overflowY': 'auto',
                'maxHeight': '600px'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '8px 12px',
                'fontSize': '13px',
                'minWidth': '80px',
                'maxWidth': '300px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'fontSize': '13px',
                'textAlign': 'center',
                'border': '1px solid #dee2e6'
            },
            style_data={
                'border': '1px solid #dee2e6',
                'whiteSpace': 'normal',
                'height': 'auto',
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ],
            
            # 排序和筛选
            sort_action='native',
            filter_action='native',
            
            # 导出功能（V8.10.1: 后端分页表格也默认关闭导出）
            export_format=None,
            export_headers=None,
        )
    ])
    
    return table_component, total_pages


def get_page_data(df: pd.DataFrame, page: int, page_size: int = 100) -> pd.DataFrame:
    """
    获取指定页的数据
    
    参数：
        df: 完整数据DataFrame
        page: 页码（从0开始）
        page_size: 每页行数
    
    返回：
        当前页的数据DataFrame
    """
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, len(df))
    return df.iloc[start_idx:end_idx].copy()


# 导出
__all__ = [
    'get_pagination_config',
    'create_paginated_datatable',
    'create_backend_paginated_table',
    'get_page_data'
]
