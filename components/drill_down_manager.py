"""
渠道分析下钻管理模块
实现4层金字塔式下钻架构的状态管理和导航逻辑

层级结构:
- Layer 1: 总览仪表盘 (overview)
- Layer 2: 渠道深度分析 (channel)
- Layer 3: 商品清单页面 (product_list)
- Layer 4: 单品深度洞察 (product_insight)

作者: GitHub Copilot
日期: 2025-11-24
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import List, Dict, Optional, Tuple
import pandas as pd


class DrillDownState:
    """下钻状态管理类"""
    
    # 层级定义
    LAYER_OVERVIEW = 'overview'
    LAYER_CHANNEL = 'channel'
    LAYER_PRODUCT_LIST = 'product_list'
    LAYER_PRODUCT_INSIGHT = 'product_insight'
    
    # 层级中文名称映射
    LAYER_NAMES = {
        LAYER_OVERVIEW: '总览',
        LAYER_CHANNEL: '渠道分析',
        LAYER_PRODUCT_LIST: '商品清单',
        LAYER_PRODUCT_INSIGHT: '单品洞察'
    }
    
    def __init__(self):
        """初始化状态管理器"""
        self.current_layer = self.LAYER_OVERVIEW
        self.current_channel = None
        self.current_product = None
        self.filter_type = None  # 商品清单筛选类型(low-margin/discount/high-cost等)
        self.navigation_history = []  # 导航历史栈
    
    def drill_down_to_channel(self, channel_name: str) -> Dict:
        """
        下钻到渠道详情页
        
        Args:
            channel_name: 渠道名称(美团外卖/饿了么/京东到家)
            
        Returns:
            dict: 新状态
        """
        self.navigation_history.append({
            'layer': self.current_layer,
            'channel': self.current_channel,
            'product': self.current_product,
            'filter_type': self.filter_type
        })
        
        self.current_layer = self.LAYER_CHANNEL
        self.current_channel = channel_name
        
        return self.get_state()
    
    def drill_down_to_product_list(self, filter_type: str) -> Dict:
        """
        下钻到商品清单页
        
        Args:
            filter_type: 筛选类型
                - 'low-margin': 低毛利商品
                - 'discount': 折扣商品
                - 'high-cost': 高成本商品
                - 'delivery-issue': 配送异常商品
                
        Returns:
            dict: 新状态
        """
        self.navigation_history.append({
            'layer': self.current_layer,
            'channel': self.current_channel,
            'product': self.current_product,
            'filter_type': self.filter_type
        })
        
        self.current_layer = self.LAYER_PRODUCT_LIST
        self.filter_type = filter_type
        
        return self.get_state()
    
    def drill_down_to_product_insight(self, product_name: str) -> Dict:
        """
        下钻到单品洞察页
        
        Args:
            product_name: 商品名称
            
        Returns:
            dict: 新状态
        """
        self.navigation_history.append({
            'layer': self.current_layer,
            'channel': self.current_channel,
            'product': self.current_product,
            'filter_type': self.filter_type
        })
        
        self.current_layer = self.LAYER_PRODUCT_INSIGHT
        self.current_product = product_name
        
        return self.get_state()
    
    def go_back(self) -> Dict:
        """
        返回上一层
        
        Returns:
            dict: 新状态
        """
        if not self.navigation_history:
            return self.get_state()
        
        # 从历史栈弹出上一层状态
        previous_state = self.navigation_history.pop()
        
        self.current_layer = previous_state['layer']
        self.current_channel = previous_state['channel']
        self.current_product = previous_state['product']
        self.filter_type = previous_state['filter_type']
        
        return self.get_state()
    
    def jump_to_layer(self, layer: str, **kwargs) -> Dict:
        """
        直接跳转到指定层级(用于面包屑导航)
        
        Args:
            layer: 目标层级
            **kwargs: 层级参数(channel/product等)
            
        Returns:
            dict: 新状态
        """
        # 清空历史栈
        self.navigation_history = []
        
        self.current_layer = layer
        self.current_channel = kwargs.get('channel')
        self.current_product = kwargs.get('product')
        self.filter_type = kwargs.get('filter_type')
        
        return self.get_state()
    
    def get_state(self) -> Dict:
        """
        获取当前状态
        
        Returns:
            dict: 当前完整状态
        """
        return {
            'current_layer': self.current_layer,
            'current_channel': self.current_channel,
            'current_product': self.current_product,
            'filter_type': self.filter_type,
            'navigation_history': self.navigation_history.copy()
        }
    
    def get_breadcrumb_path(self) -> List[Dict]:
        """
        获取面包屑导航路径
        
        Returns:
            list: 面包屑路径列表
                [
                    {'label': '总览', 'layer': 'overview', 'params': {}},
                    {'label': '美团外卖', 'layer': 'channel', 'params': {'channel': '美团外卖'}},
                    ...
                ]
        """
        path = [{'label': '总览', 'layer': self.LAYER_OVERVIEW, 'params': {}}]
        
        if self.current_channel:
            path.append({
                'label': self.current_channel,
                'layer': self.LAYER_CHANNEL,
                'params': {'channel': self.current_channel}
            })
        
        if self.filter_type:
            filter_labels = {
                'low-margin': '低毛利商品',
                'discount': '折扣商品',
                'high-cost': '高成本商品',
                'delivery-issue': '配送异常商品'
            }
            path.append({
                'label': filter_labels.get(self.filter_type, self.filter_type),
                'layer': self.LAYER_PRODUCT_LIST,
                'params': {
                    'channel': self.current_channel,
                    'filter_type': self.filter_type
                }
            })
        
        if self.current_product:
            path.append({
                'label': self.current_product,
                'layer': self.LAYER_PRODUCT_INSIGHT,
                'params': {
                    'channel': self.current_channel,
                    'product': self.current_product
                }
            })
        
        return path


def create_breadcrumb_component(breadcrumb_path: List[Dict]) -> html.Div:
    """
    创建面包屑导航组件
    
    Args:
        breadcrumb_path: 面包屑路径(由get_breadcrumb_path()生成)
        
    Returns:
        html.Div: 面包屑导航组件
    """
    breadcrumb_items = []
    
    for i, item in enumerate(breadcrumb_path):
        # 添加面包屑项
        if i == len(breadcrumb_path) - 1:
            # 当前页面,不可点击
            breadcrumb_items.append(
                html.Span(
                    item['label'],
                    className="text-muted",
                    style={
                        'fontSize': '14px',
                        'fontWeight': 'bold'
                    }
                )
            )
        else:
            # 可点击的链接
            breadcrumb_items.append(
                html.A(
                    item['label'],
                    id={
                        'type': 'breadcrumb-link',
                        'index': i,
                        'layer': item['layer']
                    },
                    style={
                        'cursor': 'pointer',
                        'color': '#007bff',
                        'textDecoration': 'none',
                        'fontSize': '14px'
                    },
                    n_clicks=0
                )
            )
        
        # 添加分隔符
        if i < len(breadcrumb_path) - 1:
            breadcrumb_items.append(
                html.Span(' / ', className="text-muted mx-2")
            )
    
    return html.Div(
        breadcrumb_items,
        className="mb-3 p-2",
        style={
            'backgroundColor': '#f8f9fa',
            'borderRadius': '4px',
            'display': 'flex',
            'alignItems': 'center'
        }
    )


def create_back_button(disabled: bool = False) -> dbc.Button:
    """
    创建返回按钮
    
    Args:
        disabled: 是否禁用(在总览层禁用)
        
    Returns:
        dbc.Button: 返回按钮组件
    """
    return dbc.Button(
        [
            html.I(className="fas fa-arrow-left me-2"),
            "返回"
        ],
        id='drill-down-back-button',
        color="secondary",
        outline=True,
        size="sm",
        disabled=disabled,
        className="mb-3"
    )


def create_state_stores() -> List[dcc.Store]:
    """
    创建状态存储组件
    
    Returns:
        list: dcc.Store组件列表
    """
    return [
        # 当前层级
        dcc.Store(id='drill-down-current-layer', data='overview'),
        
        # 当前选中渠道
        dcc.Store(id='drill-down-current-channel', data=None),
        
        # 当前选中商品
        dcc.Store(id='drill-down-current-product', data=None),
        
        # 当前筛选类型
        dcc.Store(id='drill-down-filter-type', data=None),
        
        # 导航历史栈
        dcc.Store(id='drill-down-navigation-history', data=[]),
        
        # 完整状态(用于调试)
        dcc.Store(id='drill-down-full-state', data={})
    ]


def get_filter_type_label(filter_type: str) -> str:
    """
    获取筛选类型的中文标签
    
    Args:
        filter_type: 筛选类型
        
    Returns:
        str: 中文标签
    """
    labels = {
        'low-margin': '低毛利商品',
        'discount': '折扣商品',
        'high-cost': '高成本商品',
        'delivery-issue': '配送异常商品',
        'top-products': 'TOP商品',
        'all-products': '全部商品'
    }
    return labels.get(filter_type, filter_type)


def analyze_channel_health(profit_rate: float) -> Tuple[str, str, str]:
    """
    分析渠道健康度
    
    Args:
        profit_rate: 利润率(百分比,如16.8)
        
    Returns:
        tuple: (健康度等级, 徽章文本, 徽章颜色)
            - 健康度等级: 'excellent' / 'warning' / 'good'
            - 徽章文本: '⭐优秀' / '⚠️警戒' / '✅良好'
            - 徽章颜色: 'success' / 'danger' / 'info'
    """
    if profit_rate >= 15:
        return 'excellent', '⭐优秀', 'success'
    elif profit_rate < 10:
        return 'warning', '⚠️警戒', 'danger'
    else:
        return 'good', '✅良好', 'info'


def get_drill_down_button_text(health_level: str) -> str:
    """
    根据健康度等级获取按钮文本
    
    Args:
        health_level: 健康度等级('excellent' / 'warning' / 'good')
        
    Returns:
        str: 按钮文本
    """
    button_texts = {
        'excellent': '深入分析 →',
        'warning': '诊断问题 🔍',
        'good': '深入分析 →'
    }
    return button_texts.get(health_level, '深入分析 →')


def get_drill_down_button_color(health_level: str) -> str:
    """
    根据健康度等级获取按钮颜色
    
    Args:
        health_level: 健康度等级
        
    Returns:
        str: 按钮颜色
    """
    colors = {
        'excellent': 'primary',
        'warning': 'warning',
        'good': 'primary'
    }
    return colors.get(health_level, 'primary')


# 全局状态管理器实例
_global_state_manager = DrillDownState()


def get_state_manager() -> DrillDownState:
    """
    获取全局状态管理器实例
    
    Returns:
        DrillDownState: 状态管理器
    """
    return _global_state_manager


if __name__ == '__main__':
    # 测试代码
    print("=== 下钻状态管理模块测试 ===\n")
    
    state = DrillDownState()
    
    # 测试1: 总览 → 渠道
    print("1. 下钻到美团外卖:")
    state.drill_down_to_channel('美团外卖')
    print(f"   当前层级: {state.current_layer}")
    print(f"   当前渠道: {state.current_channel}")
    print(f"   面包屑: {' > '.join([item['label'] for item in state.get_breadcrumb_path()])}\n")
    
    # 测试2: 渠道 → 商品清单
    print("2. 下钻到低毛利商品:")
    state.drill_down_to_product_list('low-margin')
    print(f"   当前层级: {state.current_layer}")
    print(f"   筛选类型: {state.filter_type}")
    print(f"   面包屑: {' > '.join([item['label'] for item in state.get_breadcrumb_path()])}\n")
    
    # 测试3: 商品清单 → 单品洞察
    print("3. 下钻到可口可乐:")
    state.drill_down_to_product_insight('可口可乐 330ml')
    print(f"   当前层级: {state.current_layer}")
    print(f"   当前商品: {state.current_product}")
    print(f"   面包屑: {' > '.join([item['label'] for item in state.get_breadcrumb_path()])}\n")
    
    # 测试4: 返回
    print("4. 返回上一层:")
    state.go_back()
    print(f"   当前层级: {state.current_layer}")
    print(f"   面包屑: {' > '.join([item['label'] for item in state.get_breadcrumb_path()])}\n")
    
    # 测试5: 健康度分析
    print("5. 健康度分析测试:")
    for rate in [18.5, 12.3, 8.2]:
        level, badge, color = analyze_channel_health(rate)
        print(f"   利润率{rate}% → {badge} (等级:{level}, 颜色:{color})")
    
    print("\n✅ 测试完成!")
