# -*- coding: utf-8 -*-
"""
系统监控面板组件

显示内容:
1. Redis状态
2. 缓存命中率
3. 内存使用情况
4. 系统负载
5. 在线用户数（估算）

作者: AI Assistant
版本: V1.0
日期: 2025-12-11
"""

from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import psutil
from datetime import datetime


def create_monitor_panel():
    """创建监控面板布局"""
    
    return html.Div([
        # 定时刷新组件（每5秒刷新一次）
        dcc.Interval(
            id='monitor-interval-component',
            interval=5000,  # 5秒
            n_intervals=0
        ),
        
        dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-heartbeat me-2"),
                "系统监控",
                dbc.Badge(
                    "实时",
                    color="success",
                    className="ms-2",
                    pill=True
                )
            ]),
            dbc.CardBody([
            dbc.Row([
                # Redis状态
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-database fa-2x text-primary mb-2"),
                            html.H6("Redis缓存", className="mb-1"),
                        ], className="text-center"),
                        html.Div(id='monitor-redis-status', className="text-center mt-2"),
                        html.Small(id='monitor-redis-detail', className="text-muted d-block text-center mt-1")
                    ], className="p-3 border rounded")
                ], width=3),
                
                # 缓存命中率
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-bullseye fa-2x text-success mb-2"),
                            html.H6("缓存命中率", className="mb-1"),
                        ], className="text-center"),
                        html.Div(id='monitor-cache-hitrate', className="text-center mt-2"),
                        html.Small(id='monitor-cache-detail', className="text-muted d-block text-center mt-1")
                    ], className="p-3 border rounded")
                ], width=3),
                
                # 内存使用
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-memory fa-2x text-warning mb-2"),
                            html.H6("内存使用", className="mb-1"),
                        ], className="text-center"),
                        html.Div(id='monitor-memory-usage', className="text-center mt-2"),
                        html.Small(id='monitor-memory-detail', className="text-muted d-block text-center mt-1")
                    ], className="p-3 border rounded")
                ], width=3),
                
                # 系统负载
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-tachometer-alt fa-2x text-info mb-2"),
                            html.H6("系统负载", className="mb-1"),
                        ], className="text-center"),
                        html.Div(id='monitor-system-load', className="text-center mt-2"),
                        html.Small(id='monitor-system-detail', className="text-muted d-block text-center mt-1")
                    ], className="p-3 border rounded")
                ], width=3),
            ]),
            
            # 详细信息（可折叠）
            html.Hr(className="my-3"),
            dbc.Collapse([
                dbc.Row([
                    dbc.Col([
                        html.H6("Redis详细信息", className="mb-2"),
                        html.Div(id='monitor-redis-details-full')
                    ], width=6),
                    dbc.Col([
                        html.H6("系统详细信息", className="mb-2"),
                        html.Div(id='monitor-system-details-full')
                    ], width=6),
                ])
            ], id='monitor-details-collapse', is_open=False),
            
            dbc.Button(
                [html.I(className="fas fa-chevron-down me-2"), "显示详细信息"],
                id='monitor-toggle-details',
                color="link",
                size="sm",
                className="mt-2"
            )
        ])
        ], className="mb-3")
    ])


def register_monitor_callbacks(app, redis_monitor, redis_cache_manager):
    """
    注册监控面板回调
    
    Args:
        app: Dash应用实例
        redis_monitor: Redis健康监控器
        redis_cache_manager: Redis缓存管理器
    """
    
    # 定时更新监控数据
    @app.callback(
        [
            Output('monitor-redis-status', 'children'),
            Output('monitor-redis-detail', 'children'),
            Output('monitor-cache-hitrate', 'children'),
            Output('monitor-cache-detail', 'children'),
            Output('monitor-memory-usage', 'children'),
            Output('monitor-memory-detail', 'children'),
            Output('monitor-system-load', 'children'),
            Output('monitor-system-detail', 'children'),
        ],
        [Input('monitor-interval-component', 'n_intervals')]
    )
    def update_monitor_data(n):
        """更新监控数据"""
        
        # 1. Redis状态
        if redis_monitor and redis_monitor.is_healthy:
            redis_status = html.Div([
                html.I(className="fas fa-check-circle fa-2x text-success"),
                html.Div("在线", className="fw-bold text-success mt-1")
            ])
            
            status = redis_monitor.get_status()
            redis_detail = f"成功率: {status['metrics']['success_rate']}%"
        else:
            redis_status = html.Div([
                html.I(className="fas fa-times-circle fa-2x text-danger"),
                html.Div("离线", className="fw-bold text-danger mt-1")
            ])
            redis_detail = "缓存不可用"
        
        # 2. 缓存命中率
        if redis_cache_manager and redis_cache_manager.enabled:
            try:
                stats = redis_cache_manager.get_stats()
                hit_rate = stats.get('hit_rate', 0)
                
                if hit_rate >= 90:
                    color = "success"
                    icon = "fa-smile"
                elif hit_rate >= 70:
                    color = "warning"
                    icon = "fa-meh"
                else:
                    color = "danger"
                    icon = "fa-frown"
                
                cache_hitrate = html.Div([
                    html.I(className=f"fas {icon} fa-2x text-{color}"),
                    html.Div(f"{hit_rate:.1f}%", className=f"fw-bold text-{color} mt-1")
                ])
                
                cache_detail = f"命中: {stats.get('hits', 0)} / 总计: {stats.get('hits', 0) + stats.get('misses', 0)}"
            except:
                cache_hitrate = html.Div([
                    html.I(className="fas fa-question-circle fa-2x text-secondary"),
                    html.Div("N/A", className="fw-bold text-secondary mt-1")
                ])
                cache_detail = "数据不可用"
        else:
            cache_hitrate = html.Div([
                html.I(className="fas fa-ban fa-2x text-secondary"),
                html.Div("未启用", className="fw-bold text-secondary mt-1")
            ])
            cache_detail = "缓存未启用"
        
        # 3. 内存使用
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            if memory_percent < 70:
                color = "success"
            elif memory_percent < 85:
                color = "warning"
            else:
                color = "danger"
            
            memory_usage = html.Div([
                html.I(className=f"fas fa-chart-pie fa-2x text-{color}"),
                html.Div(f"{memory_percent:.1f}%", className=f"fw-bold text-{color} mt-1")
            ])
            
            memory_detail = f"{memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB"
        except:
            memory_usage = html.Div([
                html.I(className="fas fa-question-circle fa-2x text-secondary"),
                html.Div("N/A", className="fw-bold text-secondary mt-1")
            ])
            memory_detail = "数据不可用"
        
        # 4. 系统负载
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            if cpu_percent < 60:
                color = "success"
                status_text = "正常"
            elif cpu_percent < 80:
                color = "warning"
                status_text = "繁忙"
            else:
                color = "danger"
                status_text = "高负载"
            
            system_load = html.Div([
                html.I(className=f"fas fa-server fa-2x text-{color}"),
                html.Div(f"{cpu_percent:.1f}%", className=f"fw-bold text-{color} mt-1")
            ])
            
            system_detail = f"CPU: {status_text}"
        except:
            system_load = html.Div([
                html.I(className="fas fa-question-circle fa-2x text-secondary"),
                html.Div("N/A", className="fw-bold text-secondary mt-1")
            ])
            system_detail = "数据不可用"
        
        return (
            redis_status, redis_detail,
            cache_hitrate, cache_detail,
            memory_usage, memory_detail,
            system_load, system_detail
        )
    
    # 详细信息展开/收起
    @app.callback(
        [
            Output('monitor-details-collapse', 'is_open'),
            Output('monitor-toggle-details', 'children')
        ],
        [Input('monitor-toggle-details', 'n_clicks')],
        [State('monitor-details-collapse', 'is_open')]
    )
    def toggle_details(n, is_open):
        """切换详细信息显示"""
        if n:
            is_open = not is_open
        
        if is_open:
            button_text = [html.I(className="fas fa-chevron-up me-2"), "隐藏详细信息"]
        else:
            button_text = [html.I(className="fas fa-chevron-down me-2"), "显示详细信息"]
        
        return is_open, button_text
    
    # 更新详细信息
    @app.callback(
        [
            Output('monitor-redis-details-full', 'children'),
            Output('monitor-system-details-full', 'children'),
        ],
        [Input('monitor-interval-component', 'n_intervals')]
    )
    def update_details(n):
        """更新详细信息"""
        
        # Redis详细信息
        redis_details = []
        if redis_monitor:
            status = redis_monitor.get_status()
            redis_details = [
                html.Small([
                    html.Strong("主机: "), status['host']
                ], className="d-block mb-1"),
                html.Small([
                    html.Strong("最后检查: "), status['last_check'] or "未检查"
                ], className="d-block mb-1"),
                html.Small([
                    html.Strong("总检查次数: "), f"{status['metrics']['total_checks']}"
                ], className="d-block mb-1"),
                html.Small([
                    html.Strong("成功次数: "), f"{status['metrics']['successful_checks']}"
                ], className="d-block mb-1"),
                html.Small([
                    html.Strong("失败次数: "), f"{status['metrics']['failed_checks']}"
                ], className="d-block mb-1"),
                html.Small([
                    html.Strong("重连次数: "), f"{status['metrics']['reconnect_attempts']}"
                ], className="d-block mb-1"),
                html.Small([
                    html.Strong("运行时间: "), f"{status['metrics']['uptime_hours']:.2f}小时"
                ], className="d-block mb-1"),
            ]
            
            if status['last_error']:
                redis_details.append(
                    html.Small([
                        html.Strong("最后错误: "),
                        html.Span(status['last_error'], className="text-danger")
                    ], className="d-block mb-1")
                )
        else:
            redis_details = [html.Small("监控器未初始化", className="text-muted")]
        
        # 系统详细信息
        system_details = []
        try:
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            disk = psutil.disk_usage('/')
            
            system_details = [
                html.Small([
                    html.Strong("CPU核心: "), f"{cpu_count}核"
                ], className="d-block mb-1"),
                html.Small([
                    html.Strong("CPU频率: "), f"{cpu_freq.current:.0f}MHz" if cpu_freq else "N/A"
                ], className="d-block mb-1"),
                html.Small([
                    html.Strong("磁盘使用: "), f"{disk.percent}% ({disk.used / 1024**3:.1f}GB / {disk.total / 1024**3:.1f}GB)"
                ], className="d-block mb-1"),
                html.Small([
                    html.Strong("启动时间: "), datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
                ], className="d-block mb-1"),
            ]
        except:
            system_details = [html.Small("系统信息不可用", className="text-muted")]
        
        return html.Div(redis_details), html.Div(system_details)


# 导出
__all__ = [
    'create_monitor_panel',
    'register_monitor_callbacks'
]
